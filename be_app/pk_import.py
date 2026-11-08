"""Explicit PK workbook mapping and inverse log transforms with traceable provenance."""

import hashlib
import io
import zipfile
from typing import Literal

import numpy as np
import pandas as pd
from pydantic import Field

from be_app.domain import StrictModel, digest
from be_app.imports import parse_file

PK_ALIASES = {
    "Subject": "subject_id",
    "Sequence": "sequence",
    "Period": "period",
    "Treatment": "treatment",
    "Cmax": "cmax",
    "AUClast": "auc_last",
    "AUCINF_obs": "auc_inf",
    "AUCINF_pred": "auc_inf_pred",
}
PK_ENDPOINTS = ("cmax", "auc_last", "auc_inf", "auc_inf_pred")
DEFAULT_TREATMENTS: dict[str, Literal["T", "R"]] = {"T": "T", "R": "R"}


class PKImportConfig(StrictModel):
    version: Literal[1] = 1
    sheet: str | int = 0
    column_mapping: dict[str, str] = Field(default_factory=lambda: dict(PK_ALIASES))
    treatment_mapping: dict[str, Literal["T", "R"]] = Field(default_factory=lambda: dict(DEFAULT_TREATMENTS))
    sequence_mapping: dict[str, str] = Field(default_factory=dict)
    scale: Literal["raw", "ln", "log10"] = "raw"
    units: Literal["ng/mL; h*ng/mL"] = "ng/mL; h*ng/mL"


def workbook_sheets(content, name):
    if len(content) > 25_000_000:
        raise ValueError("File vượt giới hạn 25 MB.")
    if name.lower().endswith(".csv"):
        return [0]
    if not name.lower().endswith(".xlsx"):
        raise ValueError("Chỉ hỗ trợ CSV và XLSX.")
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        if len(archive.infolist()) > 2000 or sum(i.file_size for i in archive.infolist()) > 100_000_000:
            raise ValueError("Excel vượt giới hạn giải nén.")
    with pd.ExcelFile(io.BytesIO(content), engine="openpyxl") as book:
        return book.sheet_names


def import_pk(content, name, config: PKImportConfig):
    sheets = workbook_sheets(content, name)
    if config.sheet not in sheets and not (config.sheet == 0 and sheets):
        raise ValueError("Sheet đã chọn không còn có trong workbook.")
    data = parse_file(content, name, config.column_mapping, sheet_name=config.sheet)
    keys = ["subject_id", "sequence", "period", "treatment"]
    if not set(keys) <= set(data):
        raise ValueError("Mapping thiếu cột subject_id/sequence/period/treatment.")
    for key in keys:
        data[key] = data[key].map(str).str.strip()
        if data[key].eq("").any():
            raise ValueError("Thiếu định danh bảng PK.")
    original_treatments = sorted(data.treatment.unique())
    if not set(original_treatments) <= set(config.treatment_mapping):
        raise ValueError("Cần mapping rõ mọi nhãn sản phẩm nguồn sang T hoặc R.")
    data["treatment"] = data.treatment.map(config.treatment_mapping)
    data["sequence"] = data.sequence.map(lambda value: config.sequence_mapping.get(value, value))
    if not data.sequence.map(lambda value: bool(value) and set(value) <= {"T", "R"}).all():
        raise ValueError("Cần mapping sequence nguồn sang chuỗi T/R rõ ràng.")
    periods = pd.to_numeric(data.period, errors="raise")
    if not np.isfinite(periods).all() or (periods % 1 != 0).any() or (periods < 1).any():
        raise ValueError("Period phải là số nguyên dương.")
    data["period"] = periods.astype(int)
    if data.duplicated(["subject_id", "period"]).any():
        raise ValueError("Bảng PK có subject/kỳ trùng; không tự gộp hoặc loại.")
    endpoints = [e for e in PK_ENDPOINTS if e in data]
    if not endpoints:
        raise ValueError("Không có endpoint được hỗ trợ sau mapping.")
    for endpoint in endpoints:
        text = data[endpoint].str.strip()
        values = pd.to_numeric(
            text.replace({v: None for v in ("", ".", "NA", "NaN", "nan", "-nan(ind)")}), errors="raise"
        )
        observed = values.notna()
        if not np.isfinite(values[observed]).all():
            raise ValueError("Endpoint có giá trị vô hạn.")
        if config.scale != "raw":
            bound = 700 if config.scale == "ln" else 300
            if values[observed].abs().gt(bound).any():
                raise ValueError("Giá trị log ngoài miền chuyển đổi ổn định.")
            values = np.exp(values) if config.scale == "ln" else np.power(10.0, values)
        if (values[observed] <= 0).any():
            raise ValueError("PK phải dương; không tự coi zero/âm là missing.")
        data[endpoint] = values
    provenance = dict(
        source_file=name,
        source_sha256=hashlib.sha256(content).hexdigest(),
        source_treatment_labels=original_treatments,
        mapping=config.model_dump(mode="json"),
        mapping_sha256=digest(config.model_dump(mode="json")),
        input_sha256=digest(data.astype(object).where(pd.notna(data), None).to_dict("records")),
        transformation="Identity"
        if config.scale == "raw"
        else f"Inverse {config.scale} to raw PK once; BE engine applies Ln(raw PK)",
        purpose="Independent PK review; not a frozen study conclusion",
    )
    return data, provenance
