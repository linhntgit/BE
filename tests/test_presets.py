import json

import pytest

from be_app.domain import BeConfig, canonical, digest
from be_app.nca import PROFILE_KEYS
from be_app.presets import export_preset, from_project, import_preset, new_project
from be_app.regulations import scope_blockers
from tests.test_terminal_review import make_override


def test_preset_creates_isolated_project_without_source_data_or_approvals(demo):
    group = next(iter(demo.qc().data.groupby(list(PROFILE_KEYS))))[1]
    source = demo.record(
        "configure",
        {
            "nca_config": demo.nca_config.model_copy(
                update={"terminal_overrides": (make_override(group),)}
            ).model_dump(mode="json"),
            "be_config": BeConfig(
                missing_policy="available_observations", missing_data_reason="Source SAP justification"
            ).model_dump(mode="json"),
        },
        "Source review",
    )
    preset = from_project(source, "Reusable BE method")
    assert not preset.nca_config.terminal_overrides
    assert preset.be_config.missing_policy == "block"
    restored = import_preset(export_preset(preset))
    created = new_project(restored, "NEW001", "A new study", "new operator")
    assert created.project_id != source.project_id
    assert not created.raw_base64 and not created.allocation and not created.corrections
    assert not created.runs and not created.artifacts and not created.freeze_hash
    assert not created.study.scope_reviewed and not created.study.protocol and not created.study.sap
    assert not created.study.is_demo and not created.study.scaled_be_prespecified
    assert scope_blockers(created.study)
    assert len(created.events) == 1 and created.events[0]["action"] == "create_from_preset"
    assert not created.drafts["pk_import"]["units_confirmed"]


def test_preset_rejects_extra_payload_unknown_schema_and_checksum_changes(demo):
    preset = json.loads(export_preset(from_project(demo, "Example")))
    preset["preset"]["raw_base64"] = "anything"
    preset["sha256"] = digest(preset["preset"])
    with pytest.raises(ValueError):
        import_preset(canonical(preset))
    preset = json.loads(export_preset(from_project(demo, "Example")))
    preset["preset"]["schema_version"] = 999
    preset["sha256"] = digest(preset["preset"])
    with pytest.raises(ValueError):
        import_preset(canonical(preset))
    preset["sha256"] = "bad checksum"
    with pytest.raises(ValueError, match="Checksum"):
        import_preset(canonical(preset))


def test_preset_retains_mapping_and_output_choices_but_not_staged_data(demo):
    source = demo.model_copy(
        update={
            "drafts": {
                "pk_import": {
                    "sheet": "PK summaries",
                    "scale": "ln",
                    "columns": '{"Product": "treatment", "PK": "cmax"}',
                    "treatments": '{"Capsule": "R", "Tablet": "T"}',
                    "sequences": '{"A": "TRTR", "B": "RTRT"}',
                    "file": {"name": "private.xlsx", "base64": "private study content"},
                    "units_confirmed": True,
                },
                "pk_review": {"prespecified": True, "justification": "Source SAP"},
            },
            "preferences": {"preset_outputs": ["BE", "Reviewer"]},
        }
    )
    preset = from_project(source, "Mapped method")
    assert preset.pk_import.sheet == "PK summaries" and preset.pk_import.scale == "ln"
    assert preset.pk_import.treatment_mapping == {"Capsule": "R", "Tablet": "T"}
    assert preset.outputs == ("BE", "Reviewer")
    content = export_preset(preset)
    assert b"private study content" not in content and b"Source SAP" not in content
    project = new_project(import_preset(content), "NEXT", "Next study")
    assert project.drafts["pk_import"]["sheet"] == "PK summaries"
    assert not project.drafts["pk_import"]["units_confirmed"]
    assert "file" not in project.drafts["pk_import"]
    assert "prespecified" not in project.drafts["pk_review"]


def test_preset_refuses_invalid_mapping_draft_instead_of_silently_using_defaults(demo):
    source = demo.model_copy(update={"drafts": {"pk_import": {"treatments": "invalid JSON"}}})
    with pytest.raises(ValueError):
        from_project(source, "Invalid draft")
