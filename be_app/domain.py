"""Strict, serializable study and analysis contracts."""

import hashlib
import json
from datetime import date, datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Design = Literal["2x2", "parallel", "partial3", "full4"]
Decision = Literal["PASS", "FAIL", "NOT EVALUABLE"]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical(value) -> bytes:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":")
    ).encode("utf-8")


def digest(value) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, frozen=True)


class Study(StrictModel):
    study_id: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")
    title: str = Field(min_length=1, max_length=300)
    design: Design = "2x2"
    rule_set_id: str = "EMA_IR_NONREPLICATE_M13A"
    protocol: str = ""
    sap: str = ""
    analyte: str = "parent"
    active_ingredient: str = ""
    formulation: Literal["IR", "MR"] = "IR"
    route: str = "oral"
    single_dose: bool = True
    nti: bool = False
    special_case: bool = False
    scaled_be_prespecified: bool = False
    hvd_justification: str = ""
    nti_cmax_narrow: bool = False
    fed_state: Literal["fasted", "fed"] = "fasted"
    dose: float = Field(default=1, gt=0)
    dose_unit: str = "mg"
    sponsor: str = ""
    study_site: str = ""
    principal_investigator: str = ""
    study_start_date: str = ""
    study_end_date: str = ""
    clinical_start_date: str = ""
    clinical_end_date: str = ""
    bioanalytical_start_date: str = ""
    bioanalytical_end_date: str = ""
    data_lock_date: str = ""
    test_product: str = "Test"
    reference_product: str = "Reference"
    test_batch: str = ""
    reference_batch: str = ""
    test_strength: str = ""
    reference_strength: str = ""
    test_concentration: str = ""
    reference_concentration: str = ""
    test_dosage_form: str = ""
    reference_dosage_form: str = ""
    test_manufacturer: str = ""
    reference_manufacturer: str = ""
    test_expiry_date: str = ""
    reference_expiry_date: str = ""
    primary_endpoints: tuple[str, ...] = ("auc_last", "cmax")
    secondary_endpoints: tuple[str, ...] = ("auc_inf_pred",)
    is_demo: bool = False
    data_purpose: Literal["unknown", "regulated_study", "training_qa", "method_development"] = "unknown"
    data_provenance: str = ""
    scope_reviewed: bool = False
    scope_evidence: str = ""
    scope_record: dict[str, str] = Field(default_factory=dict)
    protocol_details: dict[str, str] = Field(default_factory=dict)
    operator: str = "local-operator"

    @model_validator(mode="after")
    def endpoints_valid(self):
        if not self.primary_endpoints or len(set(self.primary_endpoints)) != len(self.primary_endpoints):
            raise ValueError("Endpoint bắt buộc phải có và không trùng.")
        allowed = {"auc_last", "cmax", "auc_inf", "auc_inf_pred"}
        if not set(self.primary_endpoints) <= allowed or not set(self.secondary_endpoints) <= allowed:
            raise ValueError("Endpoint chưa hỗ trợ.")
        if set(self.primary_endpoints) & set(self.secondary_endpoints) or len(
            set(self.secondary_endpoints)
        ) != len(self.secondary_endpoints):
            raise ValueError("Endpoint chính và bổ sung không được trùng.")
        date_labels = {
            "study_start_date": "Ngày bắt đầu nghiên cứu",
            "study_end_date": "Ngày kết thúc nghiên cứu",
            "clinical_start_date": "Ngày bắt đầu lâm sàng",
            "clinical_end_date": "Ngày kết thúc lâm sàng",
            "bioanalytical_start_date": "Ngày bắt đầu phân tích mẫu sinh học",
            "bioanalytical_end_date": "Ngày kết thúc phân tích mẫu sinh học",
            "data_lock_date": "Ngày khóa dữ liệu",
            "test_expiry_date": "Hạn dùng thuốc thử",
            "reference_expiry_date": "Hạn dùng thuốc đối chứng",
        }
        parsed = {}
        for key, label in date_labels.items():
            value = getattr(self, key)
            if value:
                try:
                    parsed[key] = date.fromisoformat(value)
                except ValueError as exc:
                    raise ValueError(f"{label}: nhập ngày hợp lệ theo định dạng YYYY-MM-DD.") from exc
                if parsed[key].isoformat() != value:
                    raise ValueError(f"{label}: ngày phải có dạng YYYY-MM-DD.")
        for start, end in (
            ("study_start_date", "study_end_date"),
            ("clinical_start_date", "clinical_end_date"),
            ("bioanalytical_start_date", "bioanalytical_end_date"),
        ):
            if start in parsed and end in parsed and parsed[start] > parsed[end]:
                raise ValueError(f"{date_labels[start]} không được sau {date_labels[end]}.")
        return self


class TerminalOverride(StrictModel):
    subject_id: str = Field(min_length=1)
    sequence: str = Field(min_length=1)
    period: str = Field(min_length=1)
    treatment: Literal["T", "R"]
    analyte: str = "parent"
    times: tuple[float, ...] = Field(min_length=3)
    reason: str = Field(min_length=5)
    reviewer: str = Field(min_length=1)
    profile_data_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def times_valid(self):
        if any(t < 0 for t in self.times) or tuple(sorted(set(self.times))) != self.times:
            raise ValueError("Thời gian terminal phải không âm, tăng và không trùng.")
        if len(self.reason.strip()) < 5 or not self.reviewer.strip():
            raise ValueError("Chọn terminal cần lý do và người rà soát.")
        return self


class NcaConfig(StrictModel):
    integration: Literal["linear", "linear_up_log_down"] = "linear_up_log_down"
    blq_policy: Literal["zero_m13a"] = "zero_m13a"
    tmax_tie: Literal["first", "last"] = "first"
    terminal_min_points: int = Field(default=3, ge=3, le=20)
    terminal_min_adj_r2: float = Field(default=0.8, ge=0, le=1)
    terminal_min_span_half_lives: float = Field(default=1, ge=0)
    extrapolation_warning_pct: float = Field(default=20, gt=0, lt=100)
    manual_terminal_times: tuple[float, ...] = ()
    manual_reason: str = ""
    terminal_overrides: tuple[TerminalOverride, ...] = ()

    @model_validator(mode="after")
    def reason_required(self):
        if self.manual_terminal_times and len(self.manual_reason.strip()) < 5:
            raise ValueError("Chọn pha cuối thủ công cần lý do tối thiểu 5 ký tự.")
        keys = [
            tuple(getattr(o, k) for k in ("subject_id", "sequence", "period", "treatment", "analyte"))
            for o in self.terminal_overrides
        ]
        if len(set(keys)) != len(keys):
            raise ValueError("Mỗi profile chỉ được có một lựa chọn terminal.")
        return self


class BeConfig(StrictModel):
    alpha: float = Field(default=0.05, gt=0, lt=0.5)
    lower: float = Field(default=0.8, gt=0, lt=1)
    upper: float = Field(default=1.25, gt=1)
    parallel_variance: Literal["pooled", "welch"] = "pooled"
    missing_policy: Literal["block", "available_observations"] = "block"
    missing_data_reason: str = ""

    @model_validator(mode="after")
    def missing_reason_required(self):
        if self.missing_policy != "block" and len(self.missing_data_reason.strip()) < 10:
            raise ValueError(
                "Phân tích quan sát sẵn có cần căn cứ xử lý missing trong SAP (tối thiểu 10 ký tự)."
            )
        return self


class BeResult(StrictModel):
    endpoint: str
    method: str = "ABE/TOST"
    decision: Decision = "NOT EVALUABLE"
    reason: str = ""
    n: int = 0
    estimate: float | None = None
    se: float | None = None
    df: float | None = None
    gmr: float | None = None
    ci_lower: float | None = None
    ci_upper: float | None = None
    p_lower: float | None = None
    p_upper: float | None = None
    cv_within: float | None = None
    geometric_mean_t: float | None = None
    geometric_mean_r: float | None = None
    n_observations: int = 0
    n_excluded: int = 0
    ci80_lower: float | None = None
    ci80_upper: float | None = None
    ci95_lower: float | None = None
    ci95_upper: float | None = None
    lsmean_log_t: float | None = None
    lsmean_log_r: float | None = None
    adjusted_geometric_mean_t: float | None = None
    adjusted_geometric_mean_r: float | None = None
    cv_between: float | None = None
    lower_limit: float = 0.8
    upper_limit: float = 1.25
    swr: float | None = None
    swt: float | None = None
    scaled_ucb: float | None = None
    sd_ratio_ci_lower: float | None = None
    sd_ratio_ci_upper: float | None = None
    criteria: list[dict] = Field(default_factory=list)
    diagnostics: dict = Field(default_factory=dict)
