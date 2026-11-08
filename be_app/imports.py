"""Long-format parsing, immutable corrections, and row-level reconciliation."""

import io
import math
import zipfile
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from be_app.domain import Study, digest, utc_now

REQUIRED = [
    "study_id",
    "subject_id",
    "sequence",
    "period",
    "treatment",
    "dose_datetime",
    "sample_datetime",
    "nominal_time_h",
    "actual_time_h",
    "concentration",
    "concentration_unit",
    "blq_flag",
    "lloq",
    "sample_id",
    "analyte",
    "source_batch",
]
UNITS = {
    "ng/mL": 1.0,
    "ug/L": 1.0,
    "µg/L": 1.0,
    "μg/L": 1.0,
    "ug/mL": 1000.0,
    "µg/mL": 1000.0,
    "μg/mL": 1000.0,
    "mg/L": 1000.0,
}


@dataclass(frozen=True)
class QCFlag:
    severity: str
    row: int | None
    column: str
    code: str
    message: str


@dataclass
class QCResult:
    data: pd.DataFrame
    flags: list[QCFlag]
    transformations: list[dict]
    source_fingerprint: str = ""

    @property
    def valid(self) -> bool:
        return not any(f.severity == "ERROR" for f in self.flags)

    def report(self) -> list[dict]:
        return [asdict(f) for f in self.flags]


def parse_file(content: bytes, name: str, mapping: dict[str, str] | None = None, *, sheet_name=0) -> pd.DataFrame:
    if len(content) > 25_000_000:
        raise ValueError("File vượt giới hạn 25 MB.")
    if name.lower().endswith(".csv"):
        frame = pd.read_csv(io.BytesIO(content), dtype=str, keep_default_na=False, encoding="utf-8-sig")
    elif name.lower().endswith(".xlsx"):
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            if len(archive.infolist()) > 2000 or sum(i.file_size for i in archive.infolist()) > 100_000_000:
                raise ValueError("Excel vượt giới hạn giải nén.")
        frame = pd.read_excel(io.BytesIO(content), sheet_name=sheet_name, dtype=str, keep_default_na=False, engine="openpyxl")
    else:
        raise ValueError("Chỉ hỗ trợ CSV UTF-8 và XLSX dạng long; wide chưa hỗ trợ.")
    frame.columns = frame.columns.str.strip()
    if mapping:
        frame = frame.rename(columns=mapping)
    if frame.columns.duplicated().any():
        raise ValueError("Mapping tạo cột trùng.")
    return frame.reset_index(drop=True)


def _timestamp(value):
    try:
        stamp = pd.Timestamp(str(value))
        return stamp.tz_convert("UTC") if stamp.tzinfo is not None and not pd.isna(stamp) else None
    except (ValueError, TypeError):
        return None


def _bool(value):
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    text = str(value).strip().lower()
    return {"true": True, "false": False, "1": True, "0": False}.get(text)


def _number(value):
    """Parse decimal text with Python's correctly rounded float conversion, without a 15-digit intermediate."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def validate_data(
    raw: pd.DataFrame, study: Study, allocation: pd.DataFrame, allow_unit_conversion: bool = False
) -> QCResult:
    data = raw.copy(deep=True).reset_index(drop=True)
    flags: list[QCFlag] = []
    transforms: list[dict] = []

    def flag(severity, row, col, code, message):
        flags.append(QCFlag(severity, row, col, code, message))

    missing = sorted(set(REQUIRED) - set(data.columns))
    if missing:
        flag("ERROR", None, ",".join(missing), "MISSING_COLUMNS", "Thiếu cột bắt buộc.")
        return QCResult(data, flags, transforms)
    if data.empty:
        flag("ERROR", None, "", "EMPTY", "Không có dữ liệu.")
        return QCResult(data, flags, transforms)
    if allocation.empty or not {"subject_id", "period", "sequence", "treatment"} <= set(allocation.columns):
        flag("ERROR", None, "", "NO_ALLOCATION", "Cần danh sách phân nhóm để đối soát.")
        return QCResult(data, flags, transforms)
    if allocation.duplicated(["subject_id", "period"]).any():
        flag("ERROR", None, "", "ALLOCATION_DUPLICATE", "Phân nhóm có subject–period trùng.")
        return QCResult(data, flags, transforms)
    assignments = {
        (str(r.subject_id), int(r.period)): (str(r.sequence), str(r.treatment))
        for r in allocation.itertuples()
    }
    for col in ("study_id", "subject_id", "sequence", "treatment", "sample_id", "analyte", "source_batch"):
        data[col] = data[col].astype(str).str.strip()
        for i in data.index[data[col].eq("") | data[col].isin(["nan", "None"])]:
            flag("ERROR", int(i) + 2, col, "MISSING_ID", "Thiếu định danh hoặc provenance.")
    numeric_cols = ["period", "nominal_time_h", "actual_time_h", "concentration", "lloq"]
    for col in numeric_cols:
        original = data[col].astype(str).str.strip()
        data[col] = data[col].map(_number)
        invalid = original.ne("") & data[col].isna()
        for i in data.index[invalid]:
            flag(
                "ERROR",
                int(i) + 2,
                col,
                "INVALID_NUMBER",
                "Giá trị nhập không phải số; không tự coi là missing.",
            )
    data["sample_status"] = (
        data.get("sample_status", pd.Series("VALID", index=data.index)).astype(str).str.upper()
    )
    bools = [_bool(value) for value in data.blq_flag]
    for i in data.index:
        row = int(i) + 2
        blq = bools[i]
        if blq is None:
            flag("ERROR", row, "blq_flag", "INVALID_BLQ", "Cờ BLQ phải là true/false hoặc 1/0.")
        data.at[i, "blq_flag"] = blq
        period = data.at[i, "period"]
        if not math.isfinite(period) or period < 1 or period != int(period):
            flag("ERROR", row, "period", "PERIOD", "Kỳ phải là số nguyên dương.")
        else:
            expected = assignments.get((data.at[i, "subject_id"], int(period)))
            if expected != (data.at[i, "sequence"], data.at[i, "treatment"]):
                flag(
                    "ERROR",
                    row,
                    "treatment",
                    "RANDOMIZATION",
                    "Subject/kỳ/sequence/treatment không khớp phân nhóm.",
                )
        if data.at[i, "study_id"] != study.study_id or data.at[i, "analyte"] != study.analyte:
            flag("ERROR", row, "study_id,analyte", "SCOPE", "Study hoặc analyte không khớp cấu hình.")
        dose = _timestamp(data.at[i, "dose_datetime"])
        sample = _timestamp(data.at[i, "sample_datetime"])
        imported = data.at[i, "actual_time_h"]
        if dose is None or sample is None:
            flag(
                "ERROR",
                row,
                "dose_datetime,sample_datetime",
                "TIMESTAMP",
                "Thiếu/sai actual datetime hoặc thiếu múi giờ UTC offset.",
            )
        else:
            computed = (sample - dose).total_seconds() / 3600
            if pd.notna(imported) and (not math.isfinite(imported) or abs(computed - imported) > 1 / 3600):
                flag(
                    "ERROR",
                    row,
                    "actual_time_h",
                    "TIME_MISMATCH",
                    "Actual time nhập lệch timestamp quá một giây; cần đối soát.",
                )
            data.at[i, "actual_time_h"] = computed
            data.at[i, "dose_datetime"] = dose.isoformat()
            data.at[i, "sample_datetime"] = sample.isoformat()
            transforms.append(
                dict(
                    row=row,
                    action="derive_actual_time",
                    before=None if pd.isna(imported) else float(imported),
                    after=computed,
                    source="actual timezone-aware datetimes",
                )
            )
            if computed < 0:
                flag(
                    "ERROR",
                    row,
                    "actual_time_h",
                    "PREDOSE_TIME",
                    "Mẫu trước liều cần rà soát; bản hiện tại yêu cầu baseline time=0.",
                )
        if not math.isfinite(data.at[i, "nominal_time_h"]) or data.at[i, "nominal_time_h"] < 0:
            flag("ERROR", row, "nominal_time_h", "NOMINAL_TIME", "Nominal time phải hữu hạn và không âm.")
        conc, lloq = data.at[i, "concentration"], data.at[i, "lloq"]
        if not math.isfinite(lloq) or lloq <= 0:
            flag("ERROR", row, "lloq", "LLOQ", "LLOQ phải hữu hạn và dương.")
        if (pd.notna(conc) and (not math.isfinite(conc) or conc < 0)) or (pd.isna(conc) and blq is not True):
            flag(
                "ERROR",
                row,
                "concentration",
                "CONCENTRATION",
                "Nồng độ âm/không hữu hạn/thiếu không phải BLQ.",
            )
        if pd.notna(conc) and conc == 0 and blq is not True:
            flag("ERROR", row, "blq_flag", "ZERO_NOT_BLQ", "Nồng độ zero chưa được xác nhận BLQ.")
        if pd.notna(conc) and conc < lloq and blq is False:
            flag("ERROR", row, "blq_flag", "BELOW_LLOQ", "Nồng độ dưới LLOQ nhưng không gắn BLQ.")
        if pd.notna(conc) and conc >= lloq and blq is True:
            flag("ERROR", row, "blq_flag", "BLQ_CONFLICT", "Cờ BLQ mâu thuẫn với nồng độ ≥LLOQ.")
        status = data.at[i, "sample_status"]
        if status not in ("VALID", "BLQ"):
            flag(
                "ERROR",
                row,
                "sample_status",
                "UNRESOLVED_SAMPLE",
                "MISSING/REJECTED/REASSAY cần quyết định, không tự loại mẫu.",
            )
        if status == "BLQ" and blq is not True:
            flag("ERROR", row, "sample_status", "STATUS_CONFLICT", "Trạng thái BLQ không khớp cờ BLQ.")
        unit = str(data.at[i, "concentration_unit"])
        if unit not in UNITS:
            flag("ERROR", row, "concentration_unit", "UNIT", "Đơn vị chưa hỗ trợ hoặc sai thứ nguyên.")
        elif unit != "ng/mL":
            if not allow_unit_conversion:
                flag(
                    "ERROR",
                    row,
                    "concentration_unit",
                    "UNIT_CONFIRM",
                    "Cần xác nhận chuyển đơn vị sang ng/mL.",
                )
            else:
                factor = UNITS[unit]
                data.at[i, "concentration"] = conc * factor
                data.at[i, "lloq"] = lloq * factor
                data.at[i, "concentration_unit"] = "ng/mL"
                transforms.append(
                    dict(row=row, action="convert_unit", before=unit, after="ng/mL", factor=factor)
                )
    for col, keys in [
        ("sample_id", ["sample_id"]),
        ("actual_time_h", ["subject_id", "period", "analyte", "actual_time_h"]),
    ]:
        for i in data.index[data.duplicated(keys, keep=False)]:
            flag("ERROR", int(i) + 2, col, "DUPLICATE", "Trùng mẫu/thời gian; không tự lấy trung bình.")
    for _, profile in data.groupby(["subject_id", "period", "analyte"], dropna=False):
        if profile.dose_datetime.nunique() != 1:
            flag(
                "ERROR",
                int(profile.index[0]) + 2,
                "dose_datetime",
                "DOSE_CONFLICT",
                "Một kỳ có nhiều thời điểm liều.",
            )
        if not profile.actual_time_h.eq(0).any():
            flag(
                "ERROR",
                int(profile.index[0]) + 2,
                "actual_time_h",
                "NO_BASELINE",
                "Thiếu baseline thực tế tại time=0.",
            )
        valid = profile.loc[profile.blq_flag.eq(False) & profile.concentration.gt(0)]  # noqa: E712
        if len(valid) < 4:
            flag(
                "WARNING",
                int(profile.index[0]) + 2,
                "concentration",
                "TERMINAL_POINTS",
                "Ít mẫu định lượng cho pha cuối.",
            )
        baseline = profile.loc[profile.actual_time_h.eq(0) & profile.blq_flag.eq(False), "concentration"]  # noqa: E712
        if len(baseline) and len(valid) and baseline.max() > 0.05 * valid.concentration.max():
            flag(
                "ERROR",
                int(profile.index[0]) + 2,
                "concentration",
                "PREDOSE_5PCT",
                "Predose >5% Cmax; cần quyết định population có chứng cứ.",
            )
    observed = set(zip(data.subject_id, data.period, strict=False))
    for key in sorted(set(assignments) - observed):
        flag(
            "ERROR",
            None,
            "subject_id,period",
            "MISSING_PERIOD",
            f"Thiếu kỳ theo phân nhóm: {key[0]}, kỳ {key[1]}.",
        )
    return QCResult(data, flags, transforms)


def apply_corrections(raw: pd.DataFrame, corrections: list[dict]) -> pd.DataFrame:
    data = raw.copy(deep=True).reset_index(drop=True)
    for change in corrections:
        row, column = change["row_index"], change["column"]
        if "sample_id" in change:
            matches = data.index[data.sample_id.astype(str).eq(str(change["sample_id"]))]
            if len(matches) != 1:
                raise ValueError("Correction cần sample_id duy nhất; không suy đoán theo hàng.")
            row = int(matches[0])
        if row not in data.index or column not in data:
            raise ValueError("Correction trỏ tới dòng/cột không tồn tại.")
        if str(data.at[row, column]) != str(change["before"]):
            raise ValueError("Correction không khớp giá trị trước; cần tạo revision đúng dữ liệu.")
        data.at[row, column] = change["after"]
    return data


def correction(
    frame, row_index: int, column: str, after, reason: str, actor: str, reviewer: str, evidence: str
) -> dict:
    if not all(str(v).strip() for v in (reason, actor, reviewer, evidence)) or actor == reviewer:
        raise ValueError("Correction cần lý do, bằng chứng và người rà soát độc lập.")
    if row_index not in frame.index or column not in frame:
        raise ValueError("Dòng/cột không tồn tại.")
    return dict(
        row_index=row_index,
        column=column,
        before=str(frame.at[row_index, column]),
        after=str(after),
        reason=reason,
        actor=actor,
        reviewer=reviewer,
        evidence=evidence,
        timestamp=utc_now(),
        source_hash=digest(frame.fillna("").astype(str).to_dict("records")),
    )


def csv_bytes(frame: pd.DataFrame) -> bytes:
    """Neutralize spreadsheet formula injection while preserving numeric columns."""
    safe = frame.copy()
    for column in safe.select_dtypes(include=["object", "string"]).columns:
        safe[column] = safe[column].map(
            lambda x: "'" + x if isinstance(x, str) and x.lstrip().startswith(("=", "+", "-", "@")) else x
        )
    return safe.to_csv(index=False).encode("utf-8-sig")


def excel_bytes(frame: pd.DataFrame) -> bytes:
    safe = frame.copy()
    for column in safe.select_dtypes(include=["object", "string"]).columns:
        safe[column] = safe[column].map(
            lambda x: "'" + x if isinstance(x, str) and x.lstrip().startswith(("=", "+", "-", "@")) else x
        )
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        safe.to_excel(writer, index=False, sheet_name="Du_lieu")
        for col in ("subject_id", "randomization_id", "screening_id", "sample_id"):
            if col in safe.columns:
                index = safe.columns.get_loc(col) + 1
                for row in writer.sheets["Du_lieu"].iter_rows(min_row=2, min_col=index, max_col=index):
                    row[0].number_format = "@"
    return output.getvalue()
