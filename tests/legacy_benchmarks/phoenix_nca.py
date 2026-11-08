"""Optional legacy benchmark adapter; never imported by the application."""

import hashlib
import io
import json
import math
import zipfile
from dataclasses import dataclass

import pandas as pd
from be_app.domain import NcaConfig
from be_app.nca import analyze_profile
from be_app.nca_reporting import KEYS, PARAM_COLUMNS, PARAMETERS, nca_tables, nca_workbook as _app_nca_workbook


def phoenix_config() -> NcaConfig:
    """Legacy benchmark configuration for the historical reference dataset."""
    return NcaConfig(integration="linear", terminal_min_adj_r2=0, terminal_min_span_half_lives=0)


def nca_workbook(results: list[dict], *, metadata: dict | None = None, comparison=None) -> bytes:
    """Legacy fixture export with an optional comparison sheet."""
    encoded = _app_nca_workbook(results, metadata=metadata)
    if comparison is None:
        return encoded
    output = io.BytesIO(encoded)
    with pd.ExcelWriter(output, engine="openpyxl", mode="a") as writer:
        comparison.to_excel(writer, sheet_name="Phoenix Comparison", index=False)
    return output.getvalue()


@dataclass
class PhoenixReference:
    data: pd.DataFrame
    expected: pd.DataFrame
    doses: dict
    dose_unit: str
    config: NcaConfig
    provenance: dict


def read_phoenix_reference(content: bytes, name="Phoenix.xlsx") -> PhoenixReference:
    if len(content) > 25_000_000:
        raise ValueError("File vượt giới hạn 25 MB.")
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        if len(archive.infolist()) > 2000 or sum(i.file_size for i in archive.infolist()) > 100_000_000:
            raise ValueError("Excel vượt giới hạn giải nén.")
    book = pd.ExcelFile(io.BytesIO(content), engine="openpyxl")
    needed = {"Summary Table", "Final Parameters", "Dosing Used", "Settings"}
    if not needed <= set(book.sheet_names):
        raise ValueError("Cần workbook Phoenix có Summary Table, Final Parameters, Dosing Used và Settings.")
    settings = "\n".join(str(v) for v in pd.read_excel(book, "Settings", header=None).iloc[:, 0].dropna())
    if (
        "Calculation Method = Linear Trapezoidal Linear Interpolation" not in settings
        or "Dose Type = Extravascular" not in settings
        or "Sparse = False" not in settings
        or "Uniform Weighting; 0" not in settings
    ):
        raise ValueError(
            "Đối chiếu hiện hỗ trợ extravascular đơn liều, linear trapezoidal, uniform weighting như NCA_Fasted."
        )
    raw = pd.read_excel(book, "Summary Table", dtype=object)
    if len(raw) < 3:
        raise ValueError("Summary Table cần dòng đơn vị và ít nhất hai mẫu.")
    if not set([*KEYS, "Time", "Concentration"]) <= set(raw.columns):
        raise ValueError("Summary Table thiếu cột định danh, Time hoặc Concentration.")
    if raw.iloc[0]["Time"] != "h" or raw.iloc[0]["Concentration"] != "ng/mL":
        raise ValueError("Đối chiếu cần đơn vị h và ng/mL; không tự đoán quy đổi.")
    raw = raw.iloc[1:].copy()
    if raw[KEYS].isna().any().any():
        raise ValueError("Summary Table thiếu định danh profile.")
    for key in KEYS:
        raw[key] = raw[key].map(str)
    raw["Time"] = pd.to_numeric(raw["Time"], errors="raise")
    raw["Concentration"] = pd.to_numeric(raw["Concentration"], errors="raise")
    expected = pd.read_excel(book, "Final Parameters", dtype=object)
    if expected.empty:
        raise ValueError("Final Parameters không có kết quả đối chiếu.")
    if not set(PARAM_COLUMNS) <= set(expected.columns) or expected[[*KEYS, "Parameter"]].isna().any().any():
        raise ValueError("Final Parameters thiếu cột hoặc khóa đối chiếu.")
    for key in KEYS:
        expected[key] = expected[key].map(str)
    if expected.duplicated([*KEYS, "Parameter"]).any():
        raise ValueError("Final Parameters có khóa đối chiếu trùng.")
    expected["Estimate"] = pd.to_numeric(expected["Estimate"], errors="raise")
    dosing = pd.read_excel(book, "Dosing Used", dtype=object)
    if len(dosing) < 2:
        raise ValueError("Dosing Used thiếu dòng đơn vị hoặc liều.")
    if not {"Subject", "Treatment", "Time", "Dose"} <= set(dosing.columns):
        raise ValueError("Dosing Used thiếu cột liều.")
    dose_unit = str(dosing.iloc[0]["Dose"])
    if dose_unit not in ("mg", "ug", "µg", "μg", "ng", "g"):
        raise ValueError("Đơn vị liều chưa hỗ trợ.")
    doses = {}
    for row in dosing.iloc[1:].to_dict("records"):
        dose_key = (str(row["Subject"]), str(row["Treatment"]))
        dose, time = float(row["Dose"]), float(row["Time"])
        if dose_key in doses or time != 0 or not math.isfinite(dose) or dose <= 0:
            raise ValueError("Chỉ hỗ trợ một liều dương tại time=0 cho mỗi subject/treatment.")
        doses[dose_key] = dose
    return PhoenixReference(
        raw,
        expected,
        doses,
        dose_unit,
        phoenix_config(),
        {
            "source_file": name,
            "source_sha256": hashlib.sha256(content).hexdigest(),
            "time_basis": "Time exported by Phoenix; actual/nominal not independently verified",
            "zero_policy": "Exported zero retained; original BLQ/LLOQ metadata unavailable",
            "purpose": "NCA numerical comparison only; no study BE decision",
        },
    )


def analyze_reference(reference: PhoenixReference) -> tuple[list[dict], pd.DataFrame]:
    if reference.data.empty or reference.expected.empty:
        raise ValueError("Không có profile hoặc thông số để đối chiếu.")
    results = []
    for ids, group in reference.data.groupby(KEYS, sort=False, dropna=False):
        subject, treatment, sequence, period = ids
        dose_key = (subject, treatment)
        if dose_key not in reference.doses:
            raise ValueError(f"Thiếu liều cho {dose_key}.")
        profile = pd.DataFrame(
            {
                "actual_time_h": group["Time"],
                "concentration": group["Concentration"],
                "blq_flag": group["Concentration"].eq(0),
            }
        )
        result = analyze_profile(
            profile, reference.config, dose=reference.doses[dose_key], dose_unit=reference.dose_unit
        )
        result.update(
            subject_id=subject, treatment=treatment, sequence=sequence, period=period, analyte="parent"
        )
        results.append(result)
    actual = nca_tables(results)["Final Parameters"]
    expected = reference.expected[reference.expected.Parameter.isin([p[0] for p in PARAMETERS])]
    merged = expected.merge(
        actual,
        on=[*KEYS, "Parameter"],
        suffixes=("_Phoenix", "_App"),
        how="outer",
        indicator=True,
        validate="one_to_one",
    )
    comparisons = []
    for row in merged.to_dict("records"):
        expected_value, actual_value = row["Estimate_Phoenix"], row["Estimate_App"]
        both_missing = pd.isna(expected_value) and pd.isna(actual_value)
        both_finite = (
            pd.notna(expected_value)
            and pd.notna(actual_value)
            and math.isfinite(expected_value)
            and math.isfinite(actual_value)
        )
        same_unit = str(row["Units_Phoenix"] if pd.notna(row["Units_Phoenix"]) else "") == str(
            row["Units_App"] if pd.notna(row["Units_App"]) else ""
        )
        match = (
            row["_merge"] == "both"
            and same_unit
            and (
                both_missing
                or (both_finite and math.isclose(expected_value, actual_value, rel_tol=1e-9, abs_tol=1e-8))
            )
        )
        comparisons.append(
            {
                **{k: row[k] for k in [*KEYS, "Parameter"]},
                "Units": row["Units_App"],
                "Phoenix": None if pd.isna(expected_value) else expected_value,
                "App": None if pd.isna(actual_value) else actual_value,
                "Abs difference": abs(actual_value - expected_value) if both_finite else None,
                "Match": bool(match),
                "Both missing": bool(both_missing),
            }
        )
    return results, pd.DataFrame(comparisons)
