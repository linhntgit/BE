"""Portable method presets contain configuration, never study data or approvals."""

import json
from typing import Literal

from pydantic import Field, model_validator

from be_app import __version__
from be_app.domain import BeConfig, Design, NcaConfig, StrictModel, Study, canonical, digest
from be_app.persistence import Project
from be_app.pk_import import PKImportConfig
from be_app.regulations import RULES


class WorkflowPreset(StrictModel):
    schema_version: Literal[1] = 1
    name: str = Field(min_length=1, max_length=120)
    engine_version: str = __version__
    design: Design
    rule_set_id: str
    primary_endpoints: tuple[str, ...] = ("auc_last", "cmax")
    secondary_endpoints: tuple[str, ...] = ("auc_inf_pred",)
    nca_config: NcaConfig = Field(default_factory=NcaConfig)
    be_config: BeConfig = Field(default_factory=BeConfig)
    concentration_mapping: dict[str, str] = Field(default_factory=dict)
    pk_import: PKImportConfig = Field(default_factory=PKImportConfig)
    outputs: tuple[Literal["NCA", "BE", "Reviewer"], ...] = ("NCA", "BE", "Reviewer")

    @model_validator(mode="after")
    def no_study_decisions(self):
        rule = RULES.get(self.rule_set_id)
        if rule is None or self.design not in rule.designs:
            raise ValueError("Preset có rule/design không được hỗ trợ.")
        if (
            self.nca_config.manual_terminal_times
            or self.nca_config.terminal_overrides
            or self.nca_config.manual_reason
        ):
            raise ValueError("Preset không được mang lựa chọn terminal của nghiên cứu nguồn.")
        if self.be_config.missing_policy != "block" or self.be_config.missing_data_reason:
            raise ValueError("Preset không được mang phê duyệt xử lý missing từ nghiên cứu nguồn.")
        Study(
            study_id="PRESET",
            title=self.name,
            primary_endpoints=self.primary_endpoints,
            secondary_endpoints=self.secondary_endpoints,
        )
        return self


def from_project(project, name):
    nca = project.nca_config.model_copy(
        update={"manual_terminal_times": (), "manual_reason": "", "terminal_overrides": ()}
    )
    be = project.be_config.model_copy(update={"missing_policy": "block", "missing_data_reason": ""})
    draft = project.drafts.get("pk_import", {})
    default = PKImportConfig()
    mapping = PKImportConfig(
        sheet=draft.get("sheet", default.sheet),
        scale=draft.get("scale", default.scale),
        column_mapping=json.loads(draft["columns"]) if "columns" in draft else default.column_mapping,
        treatment_mapping=json.loads(draft["treatments"])
        if "treatments" in draft
        else default.treatment_mapping,
        sequence_mapping=json.loads(draft["sequences"]) if "sequences" in draft else default.sequence_mapping,
    )
    return WorkflowPreset(
        name=name,
        design=project.study.design,
        rule_set_id=project.study.rule_set_id,
        primary_endpoints=project.study.primary_endpoints,
        secondary_endpoints=project.study.secondary_endpoints,
        nca_config=nca,
        be_config=be,
        concentration_mapping=project.column_mapping,
        pk_import=mapping,
        outputs=project.preferences.get("preset_outputs", ("NCA", "BE", "Reviewer")),
    )


def export_preset(preset):
    payload = preset.model_dump(mode="json")
    return canonical({"preset": payload, "sha256": digest(payload)})


def import_preset(content):
    if len(content) > 200_000:
        raise ValueError("Preset vượt giới hạn 200 KB.")
    payload = json.loads(content)
    if (
        not isinstance(payload, dict)
        or set(payload) != {"preset", "sha256"}
        or digest(payload["preset"]) != payload["sha256"]
    ):
        raise ValueError("Checksum hoặc cấu trúc preset không hợp lệ.")
    return WorkflowPreset.model_validate(payload["preset"])


def new_project(preset, study_id, title, operator="local-operator"):
    study = Study(
        study_id=study_id,
        title=title,
        design=preset.design,
        rule_set_id=preset.rule_set_id,
        nti=preset.rule_set_id in {"EMA_NTI", "FDA_NTI"},
        primary_endpoints=preset.primary_endpoints,
        secondary_endpoints=preset.secondary_endpoints,
        operator=operator,
    )
    mapping = preset.pk_import
    drafts = {
        "pk_import": {
            "sheet": mapping.sheet,
            "columns": json.dumps(mapping.column_mapping, ensure_ascii=False),
            "treatments": json.dumps(mapping.treatment_mapping, ensure_ascii=False),
            "sequences": json.dumps(mapping.sequence_mapping, ensure_ascii=False),
            "scale": mapping.scale,
            "units_confirmed": False,
        },
        "pk_review": {"rule": preset.rule_set_id, "design": preset.design},
    }
    project = Project(
        study=study,
        nca_config=preset.nca_config,
        be_config=preset.be_config,
        column_mapping=preset.concentration_mapping,
        drafts=drafts,
        preferences={
            "preset_name": preset.name,
            "preset_hash": digest(preset.model_dump(mode="json")),
            "preset_outputs": list(preset.outputs),
        },
    )
    return project.record(
        "create_from_preset", {}, f"Tạo mới từ preset {preset.name}; scope/protocol/SAP cần xác nhận riêng"
    )
