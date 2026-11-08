"""Per-session project controller, durable drafts, stable editor bindings and dependency caches.

No Streamlit import. A controller is never shared between sessions or projects.
"""

import json
import math
from dataclasses import dataclass, replace
from typing import Callable
from uuid import uuid4

import pandas as pd
from pydantic import Field

from be_app import __version__
from be_app.domain import StrictModel, digest, utc_now
from be_app.imports import QCResult
from be_app.persistence import Project, ProjectStore, verify_project


class PlanningInputs(StrictModel):
    cv_auc: float = Field(default=20, gt=0, le=200)
    cv_cmax: float = Field(default=30, gt=0, le=200)
    gmr_auc: float = Field(default=0.95, gt=0.8, lt=1.25)
    gmr_cmax: float = Field(default=0.95, gt=0.8, lt=1.25)
    target: int = Field(default=80, ge=70, le=99)
    dropout: int = Field(default=10, ge=0, le=80)
    source: str = ""


def result_status(project: Project, run: dict | None = None) -> str:
    if not project.runs and run is None:
        return "EMPTY"
    selected = run if run is not None else project.runs[-1]
    if "input_revision" not in selected or selected.get("engine_version") != __version__:
        return "LEGACY"
    if (
        not project.freeze_hash
        or project.freeze_hash != project.input_fingerprint
        or project.pending_edits
        or pending_config(project)
        or selected["input_revision"] != project.input_revision
        or selected["input_fingerprint"] != project.input_fingerprint
    ):
        return "STALE"
    return "CURRENT"


def pending_config(project: Project):
    draft = project.drafts.get("nca_config", {})
    expected = dict(
        integration=project.nca_config.integration,
        r2=project.nca_config.terminal_min_adj_r2,
        span=project.nca_config.terminal_min_span_half_lives,
        variance=project.be_config.parallel_variance,
        missing_policy=project.be_config.missing_policy,
        missing_reason=project.be_config.missing_data_reason,
    )
    if any(key in draft and draft[key] != value for key, value in expected.items()):
        return True
    for section, slope_draft in project.drafts.items():
        if not section.startswith("terminal:"):
            continue
        try:
            identity = json.loads(section.removeprefix("terminal:"))
        except (ValueError, TypeError):
            return True
        if not isinstance(identity, dict) or set(identity) != {
            "subject_id",
            "sequence",
            "period",
            "treatment",
            "analyte",
        }:
            return True
        override = next(
            (
                o
                for o in project.nca_config.terminal_overrides
                if all(getattr(o, k) == v for k, v in identity.items())
            ),
            None,
        )
        applied = dict(
            mode="manual" if override else "auto",
            times=list(override.times) if override else [],
            reason=override.reason if override else "",
            reviewer=override.reviewer if override else "",
        )
        if any(k in slope_draft and slope_draft[k] != value for k, value in applied.items()):
            return True
    return False


def report_manifest(project: Project, run: dict) -> dict:
    status = result_status(project, run)
    if status != "CURRENT":
        raise ValueError(
            "Kết quả từ phiên bản dữ liệu trước (STALE/LEGACY); cần áp dụng chỉnh sửa và tính lại trước xuất báo cáo."
        )
    manifest = {
        key: run[key]
        for key in (
            "analysis_run_id",
            "input_revision",
            "dataset_revision",
            "config_revision",
            "input_fingerprint",
            "dataset_hash",
            "config_hash",
            "engine_version",
            "snapshot_hash",
        )
    }
    manifest.update(
        {
            key: run[key]
            for key in ("raw_hash", "nca_config", "be_config", "rule_snapshot", "software_versions")
        }
    )
    manifest["source_file"] = project.raw_file_name
    manifest["data_purpose"] = run["study"].get("data_purpose", "unknown")
    manifest["data_provenance"] = run["study"].get("data_provenance", "")
    manifest["synthetic_data"] = run["study"].get("is_demo", False)
    manifest["snapshot_review"] = project.review_for(run)
    return manifest


@dataclass(frozen=True)
class EditorBinding:
    project_id: str
    dataset_revision: int
    columns: tuple[str, ...]
    sample_ids: tuple[str, ...]
    baseline: pd.DataFrame
    scope: str
    token: str


EDIT_COLUMNS = {
    "concentration",
    "actual_time_h",
    "nominal_time_h",
    "lloq",
    "blq_flag",
    "period",
    "treatment",
    "sequence",
    "dose_datetime",
    "sample_datetime",
    "source_batch",
    "sample_status",
    "concentration_unit",
}


class ProjectState:
    def __init__(
        self,
        project: Project,
        store: ProjectStore | None = None,
        db_revision: int = 0,
        working_revision: int = 0,
    ):
        verify_project(project)
        self.project = project
        self.mount_id = str(uuid4())
        self.store = store
        self.db_revision = db_revision
        self.working_revision = working_revision
        self._raw: pd.DataFrame | None = None
        self._clean: pd.DataFrame | None = None
        self._row_lookup: dict[str, int] | None = None
        self._qc: QCResult | None = None
        self._bindings: dict[str, EditorBinding] = {}
        self.profile_cache: dict[str, bytes] = {}
        self.render_cache: dict[tuple, object] = {}
        self.metrics = dict(
            qc_calls=0,
            analyses=0,
            nca_profiles_computed=0,
            nca_profiles_reused=0,
            checkpoints=0,
            journal_writes=0,
        )
        if not project.input_fingerprint:
            self.project = project.model_copy(update={"input_fingerprint": project.input_hash()})

    def commit(self, updated: Project):
        if updated.project_id != self.project.project_id:
            raise ValueError("Controller không thể ghi chéo dự án.")
        previous = self.project
        # Disk transaction completes first. Exceptions leave canonical/session data untouched.
        if self.store is not None:
            self.working_revision = self.store.journal(
                previous, updated, self.db_revision, self.working_revision
            )
            self.metrics["journal_writes"] += 1
        self.project = updated
        if previous.dataset_revision != updated.dataset_revision:
            if (
                previous.raw_base64 is not updated.raw_base64
                or previous.column_mapping != updated.column_mapping
            ):
                self._raw = None
            self._clean = None
            self._row_lookup = None
            self._qc = None
            self._bindings.clear()
        if previous.study != updated.study:
            self._qc = None
        # UI exports/charts are keyed by revision; bound memory per controller.
        if len(self.render_cache) > 32:
            self.render_cache.clear()
        return updated

    def checkpoint(self):
        if self.store is None:
            return
        self.db_revision = self.store.save(self.project, self.db_revision, self.working_revision)
        self.working_revision = 0
        self.metrics["checkpoints"] += 1

    def draft(self, section: str, field: str, default=None):
        return self.project.drafts.get(section, {}).get(field, default)

    def set_draft(self, section: str, field: str, value):
        self.set_drafts(section, {field: value})

    def set_drafts(self, section: str, values: dict):
        """Stage a complete form scenario in one journal revision."""
        current = self.project.drafts.get(section, {})
        if all(field in current and current[field] == value for field, value in values.items()):
            return
        drafts = {**self.project.drafts, section: {**current, **values}}
        self.commit(self.project.record("draft", {"drafts": drafts}, "Giữ bản nháp qua điều hướng"))

    def clear_drafts(self, section: str):
        """Discard one form draft without altering other workflow inputs."""
        if section not in self.project.drafts:
            return
        drafts = {key: value for key, value in self.project.drafts.items() if key != section}
        self.commit(self.project.record("draft", {"drafts": drafts}, "Làm trống bản nháp biểu mẫu"))

    def set_planning(self, field: str, value):
        values = PlanningInputs.model_validate({**self.planning(), field: value}).model_dump(mode="json")
        self.commit(
            self.project.record("planning_input", {"planning_inputs": values}, "Cập nhật giả định thiết kế")
        )

    def planning(self):
        return PlanningInputs.model_validate(self.project.planning_inputs).model_dump(mode="json")

    def set_preference(self, field: str, value):
        self.commit(
            self.project.record(
                "view_preference",
                {"preferences": {**self.project.preferences, field: value}},
                "Lưu tùy chọn hiển thị; không thay đầu vào phân tích",
            )
        )

    def raw_frame(self):
        if self._raw is None:
            self._raw = self.project.raw_frame()
        return self._raw

    def clean_frame(self):
        if self._clean is None:
            from be_app.imports import apply_corrections

            self._clean = apply_corrections(self.raw_frame(), self.project.corrections)
        return self._clean

    def qc(self):
        if self._qc is None:
            from be_app.imports import validate_data

            self._qc = validate_data(
                self.clean_frame(),
                self.project.study,
                pd.DataFrame(self.project.allocation),
                self.project.allow_unit_conversion,
            )
            self.metrics["qc_calls"] += 1
        return replace(self._qc, source_fingerprint=self.project.input_fingerprint)

    def freeze(self):
        self.project.require_editable()
        self.project.check_freeze_evidence()
        if self.project.pending_edits or self.pending_config() or not self.qc().valid:
            raise ValueError("Có chỉnh sửa Chưa áp dụng hoặc QC có lỗi chặn.")
        if self.project.nca_config.terminal_overrides:
            from be_app.nca import validate_terminal_overrides

            validate_terminal_overrides(self.project.nca_config, self.qc().data)
        self.commit(
            self.project.record(
                "freeze", {"freeze_hash": self.project.input_fingerprint}, "Khóa dữ liệu và SAP"
            )
        )

    def pending_config(self):
        return pending_config(self.project)

    def editor_binding(self, subject: str, period: str) -> EditorBinding:
        scope = f"{subject}/{period}"
        if scope not in self._bindings:
            frame = self.clean_frame()
            selected = frame.loc[
                frame.subject_id.eq(subject) & frame.period.astype(str).eq(str(period))
            ].copy()
            if selected.sample_id.duplicated().any() or selected.empty:
                raise ValueError("Editor cần sample_id duy nhất và profile có dữ liệu.")
            selected = selected.reset_index(drop=True)
            for i, row in selected.iterrows():
                for column, value in self.project.pending_edits.get(str(row.sample_id), {}).items():
                    selected.at[i, column] = value
            self._bindings[scope] = EditorBinding(
                self.project.project_id,
                self.project.dataset_revision,
                tuple(selected.columns),
                tuple(selected.sample_id.astype(str)),
                selected,
                scope,
                str(uuid4()),
            )
        return self._bindings[scope]

    def editor_diff(self, binding: EditorBinding, diff: dict):
        if (
            binding.project_id != self.project.project_id
            or binding.dataset_revision != self.project.dataset_revision
        ):
            raise ValueError("Editor dùng phiên bản dữ liệu cũ; cần tải lại editor, bản nháp vẫn giữ nguyên.")
        if diff.get("added_rows") or diff.get("deleted_rows"):
            raise ValueError("Không cho thêm/xóa hàng; sample_id và danh sách mẫu được giữ cố định.")
        if (
            tuple(binding.baseline.columns) != binding.columns
            or tuple(binding.baseline.sample_id.astype(str)) != binding.sample_ids
        ):
            raise ValueError("Thứ tự hàng/schema editor đã đổi; không áp diff theo vị trí mơ hồ.")
        pending = {sid: dict(patch) for sid, patch in self.project.pending_edits.items()}
        clean = self.clean_frame()
        if self._row_lookup is None:
            self._row_lookup = {str(sid): int(i) for i, sid in clean.sample_id.items()}
            if len(self._row_lookup) != len(clean):
                self._row_lookup = None
                raise ValueError("sample_id phải duy nhất trước khi sửa.")
        for position, changes in diff.get("edited_rows", {}).items():
            if (
                isinstance(position, bool)
                or str(position) != str(int(position))
                or not 0 <= int(position) < len(binding.sample_ids)
            ):
                raise ValueError("Vị trí hàng editor không hợp lệ.")
            sid = binding.sample_ids[int(position)]
            for column, value in changes.items():
                if column not in EDIT_COLUMNS or column not in binding.columns:
                    raise ValueError("Không được sửa định danh/schema trong editor.")
                text = "" if value is None else str(value)
                if column in {"concentration", "lloq", "actual_time_h", "nominal_time_h", "period"} and text:
                    number = float(text)
                    if (
                        not math.isfinite(number)
                        or number < 0
                        or (column in {"lloq", "period"} and number <= 0)
                    ):
                        raise ValueError("Giá trị số không hợp lệ; không commit một phần các ô.")
                if column == "blq_flag" and text.lower() not in ("true", "false", "0", "1"):
                    raise ValueError("Cờ BLQ cần true/false hoặc 0/1.")
                if text == str(clean.at[self._row_lookup[sid], column]):
                    pending.setdefault(sid, {}).pop(column, None)
                else:
                    pending.setdefault(sid, {})[column] = text
        pending = {sid: values for sid, values in pending.items() if values}
        if pending != self.project.pending_edits:
            self.commit(
                self.project.record(
                    "pending_editor", {"pending_edits": pending}, "Giữ chỉnh sửa mẫu Chưa áp dụng"
                )
            )

    def apply_pending(self, reason: str, reviewer: str, evidence: str):
        self.project.require_editable()
        actor = self.project.study.operator
        if not all(x.strip() for x in (reason, reviewer, evidence)) or actor == reviewer:
            raise ValueError("Cần lý do, bằng chứng và người rà soát độc lập để áp dụng batch.")
        frame = self.clean_frame()
        index = {str(row.sample_id): int(i) for i, row in frame.iterrows()}
        if len(index) != len(frame):
            raise ValueError("sample_id trùng; cần reconciliation trước correction.")
        source_hash = digest(frame.astype(str).to_dict("records"))
        changes = []
        for sid, patch in self.project.pending_edits.items():
            if sid not in index:
                raise ValueError("Mẫu trong pending không còn tồn tại; không áp dụng một phần.")
            row = index[sid]
            for column, after in patch.items():
                changes.append(
                    dict(
                        sample_id=sid,
                        row_index=row,
                        column=column,
                        before=str(frame.at[row, column]),
                        after=after,
                        reason=reason,
                        actor=actor,
                        reviewer=reviewer,
                        evidence=evidence,
                        timestamp=utc_now(),
                        source_hash=source_hash,
                    )
                )
        if changes:
            self.commit(
                self.project.record(
                    "correction",
                    {"corrections": [*self.project.corrections, *changes], "pending_edits": {}},
                    reason,
                    actor,
                )
            )

    def analyze(self):
        from be_app.pipeline import run_analysis

        started = self.project
        if self.pending_config():
            raise ValueError("Cấu hình Chưa áp dụng; không dùng cấu hình cũ để phân tích.")
        calculated = run_analysis(started, qc_result=self.qc(), profile_cache=self.profile_cache)
        if (
            self.project.input_revision != started.input_revision
            or self.project.input_fingerprint != started.input_fingerprint
        ):
            raise ValueError("Đầu vào đổi khi đang phân tích; không công bố kết quả cho revision mới.")
        if self.project is not started:
            calculated = self.project.record(
                "analysis",
                {"runs": [*self.project.runs, calculated.runs[-1]]},
                "Kết quả cùng input revision, giữ thay đổi hiển thị mới hơn",
            )
        self.commit(calculated)
        metrics = calculated.runs[-1]["computation"]
        self.metrics["analyses"] += 1
        for key in ("nca_profiles_computed", "nca_profiles_reused"):
            self.metrics[key] += metrics[key]


def initialize_project_state(session, project: Project | None = None, **kwargs):
    """Initialize only missing state. Explicit project switching creates a separate controller."""
    if "project_states" not in session:
        session["project_states"] = {}
    if project is None:
        return session.get("active_project_state")
    states = session["project_states"]
    if project.project_id not in states:
        states[project.project_id] = ProjectState(project, **kwargs)
    session["active_project_state"] = states[project.project_id]
    return states[project.project_id]


def benchmark_state(measure: Callable):
    from be_app.examples import demo_project

    output = {}
    for label, n in [("small", 12), ("large", 240)]:
        state = ProjectState(demo_project(n=n))
        state.qc()  # Cold QC stays an intentional validation boundary.
        output[label] = dict(
            subjects=n,
            records=len(state.raw_frame()),
            qc_navigation=measure(state.qc),
            input_fingerprint_render=measure(lambda state=state: state.project.input_fingerprint),
            raw_preview=measure(state.raw_frame),
            full_nca_calls_on_navigation=0,
            qc_calls_on_three_reruns=state.metrics["qc_calls"] - 1,
        )
    return output
