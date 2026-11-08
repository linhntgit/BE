"""Pre-import checks and human-readable file diagnostics for concentration data."""

import csv
import io
import json
import zipfile
from dataclasses import dataclass

import pandas as pd
from openpyxl import load_workbook

from be_app.domain import Study
from be_app.imports import REQUIRED, QCResult, parse_file, validate_data


@dataclass
class ImportReview:
    frame: pd.DataFrame | None = None
    qc: QCResult | None = None
    mapping: dict[str, str] | None = None
    missing: tuple[str, ...] = ()
    extra: tuple[str, ...] = ()
    error: str = ""

    @property
    def ready(self) -> bool:
        return self.frame is not None and self.qc is not None and self.qc.valid and not self.error


def _mapping(mapping_text: str) -> dict[str, str]:
    try:
        mapping = json.loads(mapping_text)
    except (ValueError, TypeError) as exc:
        raise ValueError("Mapping phải là JSON hợp lệ, ví dụ: {\"SUBJ\": \"subject_id\"}.") from exc
    if not isinstance(mapping, dict):
        raise ValueError("Mapping phải là đối tượng JSON dạng {\"tên cột file\": \"tên cột chuẩn\"}.")
    if any(not isinstance(k, str) or not k.strip() or not isinstance(v, str) or not v.strip() for k, v in mapping.items()):
        raise ValueError("Tên cột nguồn và tên cột chuẩn trong mapping phải là chuỗi không rỗng.")
    if any(v not in {*REQUIRED, "sample_status"} for v in mapping.values()):
        raise ValueError("Tên cột đích trong mapping phải thuộc các cột mẫu (hoặc sample_status).")
    return mapping


def _original_headers(content: bytes, name: str) -> list[str]:
    """Read original headers: pandas would silently rename duplicate names with .1."""
    if name.lower().endswith(".csv"):
        raw = next(csv.reader(io.StringIO(content.decode("utf-8-sig"))), [])
    else:
        workbook = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        try:
            raw = next(workbook.active.values, [])
        finally:
            workbook.close()
    return [str(col).strip() if col is not None else "" for col in raw]


def review_import(
    content: bytes,
    name: str,
    mapping_text: str,
    study: Study,
    allocation: list[dict],
    convert_units: bool,
) -> ImportReview:
    """Validate file, schema and scientific QC before any immutable raw write."""
    try:
        mapping = _mapping(mapping_text)
        frame = parse_file(content, name)
        headers = _original_headers(content, name)
        if any(not header for header in headers):
            return ImportReview(error="File có cột chưa đặt tên. Hãy điền tên cột ở hàng tiêu đề.")
        if len(headers) != len({header.casefold() for header in headers}):
            return ImportReview(error="File có tên cột trùng (kể cả khác hoa/thường) ở hàng tiêu đề. Hãy đổi tên trước khi nhập.")
        missing_sources = sorted(set(mapping) - set(frame.columns))
        if missing_sources:
            return ImportReview(error=f"Mapping tham chiếu cột không tồn tại: {', '.join(missing_sources)}.")
        frame = frame.rename(columns=mapping)
        if frame.columns.duplicated().any():
            return ImportReview(error="Mapping làm trùng tên cột; hãy xóa hoặc đổi cột bị trùng.")
        missing = tuple(sorted(set(REQUIRED) - set(frame.columns)))
        extra = tuple(sorted(set(frame.columns) - set(REQUIRED) - {"sample_status"}))
        qc = validate_data(frame, study, pd.DataFrame(allocation), convert_units)
        return ImportReview(frame, qc, mapping, missing, extra)
    except (ValueError, TypeError, KeyError, OSError, UnicodeError, OverflowError, zipfile.BadZipFile, pd.errors.ParserError) as exc:
        return ImportReview(error=f"Không thể kiểm tra file: {exc}")


def filtered_concentrations(
    frame: pd.DataFrame, subjects: list[str], periods: list[str]
) -> pd.DataFrame:
    """Keep all rows by default; filter only on explicit user choices."""
    result = frame
    if subjects and "subject_id" in result:
        result = result.loc[result.subject_id.astype(str).isin(subjects)]
    if periods and "period" in result:
        result = result.loc[result.period.astype(str).isin(periods)]
    return result
