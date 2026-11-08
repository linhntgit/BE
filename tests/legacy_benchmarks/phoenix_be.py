"""Optional numerical comparison against archived historical BE workbooks."""

import hashlib
import io
import math
import zipfile

import numpy as np
import pandas as pd
from be_app.be_reporting import ENDPOINTS, be_tables, be_workbook
from be_app.domain import BeConfig
from be_app.statistics import analyze_abe


def read_phoenix_be(content, name="Phoenix_BE.xlsx"):
    if len(content) > 25_000_000:
        raise ValueError("Workbook vượt giới hạn 25 MB.")
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        if len(archive.infolist()) > 2000 or sum(x.file_size for x in archive.infolist()) > 100_000_000:
            raise ValueError("Workbook vượt giới hạn giải nén.")
    book = pd.ExcelFile(io.BytesIO(content), engine="openpyxl")
    if not {"Residuals", "Average Bioequivalence", "Settings"} <= set(book.sheet_names):
        raise ValueError("Cần workbook BE Phoenix có Residuals, Average Bioequivalence và Settings.")
    settings = "\n".join(str(v) for v in pd.read_excel(book, "Settings", header=None).iloc[:, 0].dropna())
    if not all(
        v in settings
        for v in (
            "Study Type: Crossover",
            "Bioequivalence Type: Average",
            "Transformation: Ln(x)",
            "Model Specification: Sequence+Treatment+Period",
            "Subject(Sequence)",
        )
    ):
        raise ValueError("Đối chiếu Phoenix hỗ trợ mô hình mixed 2×2 như Bioequivalence_Fasted.")
    observations = pd.read_excel(book, "Residuals", dtype=object)
    keys = ["Subject", "Sequence", "Period", "Treatment"]
    if not {*keys, "Dependent", "Ln_Observed"} <= set(observations.columns) or observations.empty:
        raise ValueError("Residuals thiếu các quan sát PK gốc.")
    frames = []
    for label, endpoint in ENDPOINTS.items():
        subset = observations.loc[observations.Dependent.eq(f"Ln({label})"), [*keys, "Ln_Observed"]].copy()
        if subset.empty or subset.duplicated(keys).any() or subset[keys].isna().any().any():
            raise ValueError(f"Thiếu hoặc trùng quan sát {label}.")
        text = subset.Ln_Observed.astype(str).str.strip()
        missing = text.isin([".", "", "nan", "None", "-nan(ind)"])
        logs = pd.to_numeric(text.where(~missing), errors="coerce")
        if (logs.isna() & ~missing).any() or (
            (logs.notna()) & ((logs.abs() > 700) | ~np.isfinite(logs))
        ).any():
            raise ValueError("Ln_Observed không hợp lệ; không dùng Predicted làm dữ liệu.")
        subset[endpoint] = np.exp(logs)
        frames.append(subset.drop(columns="Ln_Observed"))
    data = frames[0]
    for frame in frames[1:]:
        data = data.merge(frame, on=keys, how="outer", validate="one_to_one")
    data = data.rename(
        columns={
            "Subject": "subject_id",
            "Sequence": "sequence",
            "Period": "period",
            "Treatment": "treatment",
        }
    )
    data.subject_id = data.subject_id.map(str)
    data.period = pd.to_numeric(data.period, errors="raise").astype(int)
    expected = pd.read_excel(book, "Average Bioequivalence")
    if expected.empty or expected.Dependent.duplicated().any():
        raise ValueError("Average Bioequivalence thiếu kết quả hoặc có endpoint trùng.")
    return (
        data,
        expected,
        dict(
            source_file=name,
            source_sha256=hashlib.sha256(content).hexdigest(),
            input_basis="Only exported Ln_Observed is transformed back to PK; no predicted/model results enter the fit.",
            purpose="Phoenix numerical comparison; not an EMA/FDA population approval",
        ),
    )


def compare_phoenix_be(data, expected):
    config = BeConfig(
        missing_policy="available_observations",
        missing_data_reason="Reproduce Phoenix numerical benchmark; original missing endpoint observations listed explicitly.",
    )
    results = [analyze_abe(data, endpoint, "2x2", config) for endpoint in ENDPOINTS.values()]
    actual = be_tables(results)["Average Bioequivalence"].set_index("Dependent")
    comparisons = []
    for row in expected.to_dict("records"):
        dependent = row["Dependent"]
        if dependent not in actual.index:
            raise ValueError("Phoenix có endpoint không được hỗ trợ.")
        for field, value in row.items():
            if field in ("Dependent", "Units", "FormVar", "FormRef", "Test"):
                continue
            observed = actual.loc[dependent].get(field)
            numeric = pd.notna(value) and isinstance(value, (int, float))
            valid = observed is not None and pd.notna(observed)
            # Legacy Phoenix t-quantile approximations differ at small fractional df.
            # 0.0001 percentage point is <1/100 of the usual 0.01% display precision.
            tolerance = 1e-4 if field.startswith("CI_") else 1e-5
            match = bool(
                numeric
                and valid
                and math.isclose(float(value), float(observed), rel_tol=1e-7, abs_tol=tolerance)
            )
            comparisons.append(
                dict(
                    Dependent=dependent,
                    Statistic=field,
                    Phoenix=float(value) if numeric else None,
                    App=float(observed) if valid else None,
                    **{"Abs difference": abs(float(value) - float(observed)) if numeric and valid else None},
                    Match=match,
                    Absolute_Tolerance=tolerance,
                    Relative_Tolerance=1e-7,
                )
            )
    return results, pd.DataFrame(comparisons)


def be_comparison_workbook(results, *, data=None, metadata=None, comparison=None):
    """Add a comparison sheet to a standalone app export for benchmark review."""
    encoded = be_workbook(results, data=data, metadata=metadata)
    if comparison is None:
        return encoded
    output = io.BytesIO(encoded)
    with pd.ExcelWriter(output, engine="openpyxl", mode="a") as writer:
        comparison.to_excel(writer, sheet_name="Phoenix Comparison", index=False)
    return output.getvalue()
