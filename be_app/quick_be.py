"""Review-only BE analysis from a compact concentration or PK endpoint table.

This module deliberately has no dependency on project state or the project QC
workflow. It keeps the stricter statistical missing-data rules of the BE engine.
"""

from __future__ import annotations

import hashlib
import io
import re
from dataclasses import dataclass
from typing import Literal, cast

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, wilcoxon

from be_app import __version__
from be_app.be_reporting import be_workbook
from be_app.domain import BeConfig, BeResult, Design, NcaConfig, Study, digest
from be_app.imports import UNITS, parse_file
from be_app.nca import analyze_dataset
from be_app.pk_import import PK_ENDPOINTS, PKImportConfig, import_pk
from be_app.regulations import RULES
from be_app.replicate import SEQUENCES, analyze_regulatory_be

FIELDS = {
    "subject": "subject_id", "subjectid": "subject_id", "subject_id": "subject_id",
    "sequence": "sequence", "period": "period", "treatment": "treatment",
    "time": "actual_time_h", "timeh": "actual_time_h", "actualtimeh": "actual_time_h",
    "actual_time_h": "actual_time_h", "cplasma": "concentration",
    "concentration": "concentration", "conc": "concentration",
    "blq": "blq_flag", "blqflag": "blq_flag", "blq_flag": "blq_flag",
    "cmax": "cmax", "auclast": "auc_last", "auc_last": "auc_last",
    "tmax": "tmax",
    "aucinf": "auc_inf", "aucinfobs": "auc_inf", "auc_inf": "auc_inf",
    "aucinfpred": "auc_inf_pred", "auc_inf_pred": "auc_inf_pred",
}
IDENTITY = ("subject_id", "sequence", "period", "treatment")
PROFILE = ("subject_id", "period")


def auto_column_mapping(columns) -> dict[str, str]:
    """Suggest recognized headers; caller must resolve duplicate targets."""
    return {
        str(col): FIELDS[key]
        for col in columns
        if (key := re.sub(r"[^a-z0-9_]", "", str(col).strip().lower())) in FIELDS
    }


def mapped_frame(content: bytes, filename: str, *, sheet=0, column_mapping=None) -> tuple[pd.DataFrame, dict]:
    raw = parse_file(content, filename, sheet_name=sheet)
    mapping = auto_column_mapping(raw.columns) if column_mapping is None else column_mapping
    if any(source not in raw.columns for source in mapping):
        raise ValueError("Mapping chứa tên cột không có trong dữ liệu.")
    if len(set(mapping.values())) != len(mapping):
        raise ValueError("Hai cột đang cùng ánh xạ vào một trường; hãy chọn một cột duy nhất.")
    data = raw.rename(columns=mapping)
    if data.columns.duplicated().any():
        raise ValueError("Mapping tạo tên cột trùng.")
    return data, mapping


def detect_mode(data: pd.DataFrame) -> str:
    if "concentration" in data:
        return "concentration"
    if set(PK_ENDPOINTS) & set(data):
        return "endpoint"
    raise ValueError("Cần Cplasma cho dữ liệu nồng độ hoặc Cmax/AUClast/AUCinf cho bảng endpoint.")


def _normalise_identity(data: pd.DataFrame, design: str, treatment_mapping, sequence_mapping) -> pd.DataFrame:
    if not set(IDENTITY) <= set(data):
        raise ValueError("Thiếu Subject, Sequence, Period hoặc Treatment.")
    d = data.copy()
    for col in IDENTITY:
        d[col] = d[col].astype(str).str.strip()
        if d[col].eq("").any():
            raise ValueError(f"Trường {col} có giá trị trống.")
    unknown_t = sorted(set(d.treatment) - set(treatment_mapping))
    unknown_s = sorted(set(d.sequence) - set(sequence_mapping))
    if unknown_t or unknown_s:
        raise ValueError(f"Cần ánh xạ tường minh Treatment {unknown_t} và Sequence {unknown_s}.")
    d["treatment"] = d.treatment.map(treatment_mapping)
    d["sequence"] = d.sequence.map(sequence_mapping)
    values = pd.to_numeric(d.period, errors="coerce")
    if values.isna().any() or not np.isfinite(values).all() or (values < 1).any() or (values % 1 != 0).any():
        raise ValueError("Period phải là số nguyên dương.")
    d["period"] = values.astype(int)
    sequences = {"2x2": {"TR", "RT"}, "parallel": {"T", "R"},
                 **{k: set(v) for k, v in SEQUENCES.items()}}[design]
    if not set(d.sequence) <= sequences or not set(d.treatment) <= {"T", "R"}:
        raise ValueError("Sequence hoặc Treatment không thuộc thiết kế đã chọn.")
    if d.groupby("subject_id").sequence.nunique().gt(1).any():
        raise ValueError("Một Subject có nhiều Sequence.")
    if d.groupby(list(PROFILE)).treatment.nunique().gt(1).any():
        raise ValueError("Một Subject/Period có nhiều Treatment.")
    for record in d[list(IDENTITY)].drop_duplicates().itertuples(index=False):
        if record.period > len(record.sequence) or record.treatment != record.sequence[record.period - 1]:
            raise ValueError(f"Treatment/Period không khớp Sequence của Subject {record.subject_id}.")
    return d


def _complete_profiles(d: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Keep explicit missing-period rows so BE never silently uses completers."""
    absent = []
    for subject, group in d.groupby("subject_id", sort=False):
        seq = group.sequence.iloc[0]
        periods = set(group.period)
        for period, treatment in enumerate(seq, 1):
            if period not in periods:
                absent.append(dict(subject_id=subject, sequence=seq, period=period, treatment=treatment))
    if not absent:
        return d, []
    missing = pd.DataFrame(absent)
    completed = pd.concat([d, missing], ignore_index=True)
    messages = [f"Subject {r['subject_id']}, kỳ {r['period']}: thiếu toàn bộ profile."
                for r in absent]
    return completed, messages


def _concentrations(d: pd.DataFrame, unit: str) -> pd.DataFrame:
    if "actual_time_h" not in d:
        raise ValueError("Cplasma cần cột Time (giờ) để tính AUC bằng NCA.")
    if unit not in UNITS:
        raise ValueError("Đơn vị nồng độ không được hỗ trợ.")
    d = d.copy()
    for col in ("actual_time_h", "concentration"):
        original = d[col].astype(str).str.strip()
        d[col] = pd.to_numeric(original, errors="coerce")
        if original.eq("").any() or not np.isfinite(d[col]).all():
            raise ValueError(f"{col} chứa giá trị trống, chữ hoặc không hữu hạn; cần xử lý rõ trước NCA.")
    if (d.actual_time_h < 0).any() or (d.concentration < 0).any():
        raise ValueError("Time và Cplasma không được âm.")
    if d.duplicated(["subject_id", "period", "actual_time_h"]).any():
        raise ValueError("Trùng Subject/Period/Time; không tự gộp điểm đo.")
    if "blq_flag" not in d:
        d["blq_flag"] = False
    else:
        flags = {"1": True, "true": True, "yes": True, "0": False, "false": False, "no": False}
        d["blq_flag"] = d.blq_flag.astype(str).str.strip().str.lower().map(flags)
        if d.blq_flag.isna().any():
            raise ValueError("BLQ phải là true/false hoặc 1/0; không tự suy đoán BLQ từ nồng độ.")
        d["blq_flag"] = d.blq_flag.astype(bool)
    d["concentration"] = d.concentration * UNITS[unit]
    if not np.isfinite(d.concentration).all():
        raise ValueError("Quy đổi nồng độ vượt giới hạn tính toán.")
    d["study_id"] = "QUICK_BE"
    d["analyte"] = "parent"
    d["concentration_unit"] = "ng/mL"
    return d


@dataclass
class TmaxComparison:
    """Descriptive/exploratory original-hour Tmax analysis, outside the BE decision."""

    status: str = "NOT EVALUABLE"
    method: str = ""
    n_t: int = 0
    n_r: int = 0
    median_t: float | None = None
    median_r: float | None = None
    min_t: float | None = None
    max_t: float | None = None
    min_r: float | None = None
    max_r: float | None = None
    n_pairs: int | None = None
    median_paired_difference: float | None = None
    statistic: float | None = None
    p_value: float | None = None
    reason: str = ""
    note: str = "Phân tích hỗ trợ trên Tmax gốc (giờ); không tham gia quyết định BE, không áp dụng 80–125%."


def compare_tmax(endpoints: pd.DataFrame, design: str) -> TmaxComparison:
    """Compare Tmax without logs; never silently exclude missing/invalid profiles."""
    result = TmaxComparison()
    if "tmax" not in endpoints:
        result.reason = "Không có cột Tmax; cần dữ liệu Tmax theo Subject/Period."
        return result
    if not {"subject_id", "treatment"} <= set(endpoints):
        result.reason = "Thiếu định danh Subject/Treatment cho Tmax."
        return result
    values = pd.to_numeric(endpoints.tmax, errors="coerce")
    valid = np.isfinite(values) & values.ge(0)
    for treatment, suffix in (("T", "t"), ("R", "r")):
        sample = values.loc[valid & endpoints.treatment.eq(treatment)]
        setattr(result, f"n_{suffix}", int(len(sample)))
        if not sample.empty:
            setattr(result, f"median_{suffix}", float(sample.median()))
            setattr(result, f"min_{suffix}", float(sample.min()))
            setattr(result, f"max_{suffix}", float(sample.max()))

    if endpoints["subject_id"].isna().any():
        result.reason = "Có profile Tmax thiếu mã Subject; không tự loại dòng để kiểm định."
        return result
    if not endpoints["treatment"].isin(["T", "R"]).all():
        result.reason = "Tmax chỉ nhận nhãn điều trị T/R; có nhãn thiếu hoặc không hợp lệ."
        return result

    if not valid.all():
        result.reason = (f"Tmax thiếu/không phải số, âm hoặc không hữu hạn ở "
                         f"{int((~valid).sum())} profile; không tự loại dòng để kiểm định.")
        return result
    if design not in {"2x2", "parallel"}:
        result.reason = ("Thiết kế replicate cần phương pháp Tmax được định trước trong SAP; "
                         "chưa hỗ trợ kiểm định phi tham số cho thiết kế này.")
        return result

    if design == "2x2":
        result.method = "Wilcoxon signed-rank, paired two-sided"
        if endpoints.duplicated(["subject_id", "treatment"]).any():
            result.reason = "Tmax 2×2 cần đúng một T và một R cho mỗi Subject."
            return result
        paired = endpoints.assign(tmax=values).pivot(index="subject_id", columns="treatment", values="tmax")
        if not {"T", "R"} <= set(paired) or paired[["T", "R"]].isna().any().any():
            result.reason = "Không đủ cặp Tmax T/R trong mỗi Subject; không loại Subject tự động."
            return result
        differences = paired["T"] - paired["R"]
        result.n_pairs = len(differences)
        if result.n_pairs < 2:
            result.reason = "Cần ít nhất 2 cặp Tmax T/R để so sánh."
            return result
        result.median_paired_difference = float(differences.median())
        if differences.eq(0).all():
            result.statistic, result.p_value = 0.0, 1.0
        else:
            test = wilcoxon(differences.to_numpy(), alternative="two-sided", zero_method="wilcox", method="auto")
            result.statistic, result.p_value = float(test.statistic), float(test.pvalue)
        result.note += " Wilcoxon ghép cặp chưa hiệu chỉnh hiệu ứng kỳ/trình tự."
    else:
        result.method = "Mann–Whitney U, independent two-sided"
        if endpoints.duplicated(["subject_id"]).any():
            result.reason = "Thiết kế song song cần một Tmax trên mỗi Subject."
            return result
        if result.n_t < 2 or result.n_r < 2:
            result.reason = "Cần ít nhất 2 Subject ở mỗi nhóm T/R để so sánh."
            return result
        t_values = values.loc[endpoints.treatment.eq("T")].to_numpy()
        r_values = values.loc[endpoints.treatment.eq("R")].to_numpy()
        test = mannwhitneyu(t_values, r_values, alternative="two-sided", method="auto")
        result.statistic, result.p_value = float(test.statistic), float(test.pvalue)
    result.status = "EVALUABLE"
    return result


@dataclass
class QuickBEResult:
    mode: str
    raw: pd.DataFrame
    concentrations: pd.DataFrame | None
    nca: pd.DataFrame
    endpoints: pd.DataFrame
    results: list[BeResult]
    tmax: TmaxComparison
    overall_status: str
    warnings: list[str]
    provenance: dict


def run_quick_be(
    content: bytes,
    filename: str,
    *,
    sheet=0,
    column_mapping: dict[str, str] | None = None,
    mode: str | None = None,
    design: str = "2x2",
    rule_id: str | None = None,
    treatment_mapping: dict[str, str] | None = None,
    sequence_mapping: dict[str, str] | None = None,
    concentration_unit: str = "ng/mL",
    endpoint_scale: str = "raw",
    primary_endpoints: tuple[str, ...] = ("auc_last", "cmax"),
    nca_config: NcaConfig | None = None,
    be_config: BeConfig | None = None,
    nti: bool = False,
    nti_cmax_narrow: bool = False,
    scaled_be_prespecified: bool = False,
    hvd_justification: str = "",
) -> QuickBEResult:
    """Run one snapshot. Missing NCA and/or PK stay NOT EVALUABLE."""
    d, mapping = mapped_frame(content, filename, sheet=sheet, column_mapping=column_mapping)
    # Preserve the original source labels and values for the downloadable evidence.
    source = d.rename(columns={target: origin for origin, target in mapping.items()}).copy()
    if d.empty:
        raise ValueError("Bảng không có dòng dữ liệu.")
    if design not in ("2x2", "parallel", *SEQUENCES):
        raise ValueError("Thiết kế chưa hỗ trợ.")
    selected_mode = mode or detect_mode(d)
    if selected_mode not in {"concentration", "endpoint"}:
        raise ValueError("Chỉ có hai chế độ nồng độ hoặc endpoint PK.")
    rule_id = rule_id or ("EMA_IR_NONREPLICATE_M13A" if design in {"2x2", "parallel"} else "EMA_REPLICATE_STANDARD")
    if rule_id not in RULES or design not in RULES[rule_id].designs:
        raise ValueError("Bộ quy tắc không áp dụng cho thiết kế đã chọn.")
    if nti != (rule_id in {"EMA_NTI", "FDA_NTI"}):
        raise ValueError("Cờ NTI phải phù hợp bộ quy tắc EMA_NTI/FDA_NTI.")
    selected_be_config = be_config or BeConfig()
    if (selected_be_config.alpha != 0.05 or selected_be_config.lower != 0.8
            or selected_be_config.upper != 1.25):
        raise ValueError("Bộ quy tắc có tên chỉ dùng alpha=0,05 và biên mặc định 0,80–1,25; "
                         "cấu hình tùy chỉnh cần phương pháp phân tích riêng.")
    if not primary_endpoints or not set(primary_endpoints) <= set(PK_ENDPOINTS):
        raise ValueError("Phải chọn endpoint chính hợp lệ.")
    treatment_mapping = treatment_mapping or {"T": "T", "R": "R"}
    sequence_mapping = sequence_mapping or {k: k for k in ({"TR", "RT"} if design == "2x2" else
                                                        ({"T", "R"} if design == "parallel" else SEQUENCES[design]))}
    d = _normalise_identity(d, design, treatment_mapping, sequence_mapping)
    warnings: list[str] = []
    concentrations = None
    nca = pd.DataFrame()
    if selected_mode == "concentration":
        if "concentration" not in d:
            raise ValueError("Chế độ NCA cần Cplasma.")
        concentrations = _concentrations(d, concentration_unit)
        altered_blq = concentrations.loc[
            concentrations.blq_flag & concentrations.concentration.gt(0),
            ["subject_id", "period", "actual_time_h", "concentration"],
        ]
        if len(altered_blq):
            warnings.append(
                f"BLQ: {len(altered_blq)} mẫu có giá trị dương sẽ được quy về 0 theo "
                "zero_m13a khi tính NCA; cần kiểm tra LLOQ và tác động đến Cmax/AUC. "
                "Giá trị gốc được giữ trong bảng nguồn."
            )
        nca_rows = analyze_dataset(concentrations, nca_config or NcaConfig())
        nca = pd.DataFrame(nca_rows)
        if nca.empty:
            raise ValueError("Không tìm thấy hồ sơ nồng độ để tính NCA.")
        for row in nca_rows:
            name = f"Subject {row['subject_id']}, kỳ {row['period']}"
            if row["status"] != "EVALUABLE":
                warnings.append(f"{name}: {row['reason'] or 'NCA chưa đánh giá được' }")
            warnings.extend(f"{name}: {msg}" for msg in row.get("warnings", []))
        endpoint_cols = [k for k in (*PK_ENDPOINTS, "tmax") if k in nca]
        endpoints = nca[list(IDENTITY) + endpoint_cols].copy()
        # A profile blocked by NCA QC cannot contribute even a calculated Cmax.
        endpoints.loc[nca.status.ne("EVALUABLE"), endpoint_cols] = np.nan
    else:
        if not (set(PK_ENDPOINTS) & set(d)):
            raise ValueError("Bảng endpoint cần ít nhất một trong Cmax, AUClast, AUCinf.")
        if endpoint_scale not in {"raw", "ln", "log10"}:
            raise ValueError("Thang đo endpoint không hợp lệ.")
        if not set(treatment_mapping.values()) <= {"T", "R"}:
            raise ValueError("Mapping Treatment chỉ chấp nhận T hoặc R.")
        # Reuse the independently audited importer and its single inverse-log transform.
        cfg = PKImportConfig(
            sheet=sheet, column_mapping=mapping,
            treatment_mapping=cast(dict[str, Literal["T", "R"]], treatment_mapping),
            sequence_mapping=sequence_mapping,
            scale=cast(Literal["raw", "ln", "log10"], endpoint_scale),
        )
        endpoints, _ = import_pk(content, filename, cfg)
    endpoints, missing_messages = _complete_profiles(endpoints)
    warnings.extend(missing_messages)
    tmax_comparison = compare_tmax(endpoints, design)
    for endpoint in primary_endpoints:
        if endpoint not in endpoints:
            endpoints[endpoint] = np.nan
            warnings.append(f"Thiếu endpoint chính {endpoint} trong dữ liệu.")
    study = Study(
        study_id="QUICK_BE", title="Quick BE — independent draft", design=cast(Design, design),
        rule_set_id=rule_id, primary_endpoints=primary_endpoints,
        secondary_endpoints=tuple(e for e in PK_ENDPOINTS if e in endpoints and e not in primary_endpoints),
        nti=nti, nti_cmax_narrow=nti_cmax_narrow,
        scaled_be_prespecified=scaled_be_prespecified, hvd_justification=hvd_justification,
        data_purpose="method_development",
    )
    be_results = []
    for endpoint in (*primary_endpoints, *study.secondary_endpoints):
        # Fail closed when any profile is absent or any parameter is missing.
        values = pd.to_numeric(endpoints[endpoint], errors="coerce")
        if values.isna().any() or not np.isfinite(values).all() or (values <= 0).any():
            reason = f"{endpoint}: thiếu/không hợp lệ ở {int((~np.isfinite(values) | (values <= 0)).sum())} profile; không loại subject tự động."
            result = BeResult(endpoint=endpoint, reason=reason, n_observations=int(values.notna().sum()))
        else:
            try:
                result = analyze_regulatory_be(endpoints, endpoint, study, selected_be_config)
            except (ValueError, TypeError, ArithmeticError, np.linalg.LinAlgError) as exc:
                result = BeResult(endpoint=endpoint, reason=str(exc))
        be_results.append(result)
    primary = [r for r in be_results if r.endpoint in primary_endpoints]
    overall = ("NOT EVALUABLE" if any(r.decision == "NOT EVALUABLE" for r in primary)
               else "FAIL" if any(r.decision == "FAIL" for r in primary) else "PASS")
    settings = {
        "design": design, "rule_id": rule_id, "mode": selected_mode, "sheet": sheet,
        "mapping": mapping, "treatment_mapping": treatment_mapping,
        "sequence_mapping": sequence_mapping, "concentration_unit": concentration_unit,
        "endpoint_scale": endpoint_scale, "primary_endpoints": primary_endpoints,
        "nca_config": (nca_config or NcaConfig()).model_dump(mode="json"),
        "be_config": selected_be_config.model_dump(mode="json"),
        "nti": nti, "nti_cmax_narrow": nti_cmax_narrow,
        "scaled_be_prespecified": scaled_be_prespecified, "hvd_justification": hvd_justification,
    }
    provenance = {
        "source_file": filename, "source_sha256": hashlib.sha256(content).hexdigest(),
        "input_sha256": digest(d.astype(object).where(pd.notna(d), None).to_dict("records")),
        "settings_sha256": digest(settings), "settings": settings,
        "engine_version": __version__, "status": "ANALYZED",
        "blq_handling": {
            "policy": (nca_config or NcaConfig()).blq_policy,
            "positive_flagged_count": len(altered_blq) if selected_mode == "concentration" else 0,
            "positive_flagged_samples": altered_blq.to_dict("records") if selected_mode == "concentration" else [],
            "raw_values_preserved": True,
        },
    }
    return QuickBEResult(selected_mode, source, concentrations, nca, endpoints,
                         be_results, tmax_comparison, overall, warnings, provenance)


def quick_be_workbook(result: QuickBEResult) -> bytes:
    """Extend the standard BE workbook with input and per-profile NCA evidence."""
    def safe(frame):
        out = frame.copy()
        for col in out.select_dtypes(include=["object", "string"]).columns:
            out[col] = out[col].map(lambda v: "'" + v if isinstance(v, str) and v.startswith(("=", "+", "-", "@")) else v)
        return out

    buffer = io.BytesIO(be_workbook(result.results, data=safe(result.endpoints), metadata={
        "Quick BE overall": result.overall_status,
        "Quick BE provenance": result.provenance,
    }))
    with pd.ExcelWriter(buffer, engine="openpyxl", mode="a", if_sheet_exists="error") as writer:
        safe(result.raw).to_excel(writer, sheet_name="Quick BE Source", index=False)
        if result.concentrations is not None:
            safe(result.concentrations).to_excel(writer, sheet_name="Input Concentrations", index=False)
            scalars = result.nca.drop(columns=["profile_points", "terminal_candidates", "config", "terminal_selected", "warnings"], errors="ignore")
            safe(scalars).to_excel(writer, sheet_name="NCA Profiles", index=False)
        tmax = result.tmax
        pd.DataFrame([{
            "Status": tmax.status, "Method": tmax.method,
            "N_T": tmax.n_t, "Median_T_h": tmax.median_t, "Min_T_h": tmax.min_t,
            "Max_T_h": tmax.max_t, "N_R": tmax.n_r, "Median_R_h": tmax.median_r,
            "Min_R_h": tmax.min_r, "Max_R_h": tmax.max_r,
            "N_pairs": tmax.n_pairs, "Median_paired_T_minus_R_h": tmax.median_paired_difference,
            "Statistic": tmax.statistic, "P_two_sided": tmax.p_value,
            "Reason": tmax.reason, "Interpretation": tmax.note,
        }]).to_excel(writer, sheet_name="Tmax Nonparametric", index=False)
        pd.DataFrame({"Warning / review required": result.warnings or ["No additional input warnings"]}).to_excel(
            writer, sheet_name="Quick BE Review", index=False
        )
    return buffer.getvalue()
