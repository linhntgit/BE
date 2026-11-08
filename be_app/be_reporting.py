"""Independent BE statistical tables and traceable Excel snapshots."""

import io
import json
import math

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from scipy.stats import t

from be_app import __version__
from be_app.review import reviewer_tables

ENDPOINTS = {"Cmax": "cmax", "AUClast": "auc_last", "AUCINF_pred": "auc_inf_pred"}
REVIEW_TABLE_SCHEMA = 2
DISPLAY = {v: f"Ln({k})" for k, v in ENDPOINTS.items()}
DISPLAY["auc_inf"] = "Ln(AUCINF_obs)"
INFERENCE = {
    "estimate": "Estimate",
    "se": "StdError",
    "df": "Denom_DF",
    "t": "T_stat",
    "p": "P_value",
    "confidence": "Conf_Level",
    "critical": "T_critical",
    "lower": "Lower_CI",
    "upper": "Upper_CI",
}


def _infer(row):
    return {INFERENCE.get(k, k): (100 * v if k == "confidence" else v) for k, v in row.items()}


def be_tables(results, *, data=None, design=None):
    average, intervals, criteria, fixed, lsmeans, differences = [], [], [], [], [], []
    partial_tests: list[dict] = []
    sequential_ss: list[dict] = []
    partial_ss: list[dict] = []
    variances: list[dict] = []
    residuals: list[dict] = []
    subjects: list[dict] = []
    howe: list[dict] = []
    missing: list[dict] = []
    diagnostics: list[dict] = []
    intermediate: list[dict] = []
    residual_diagnostics: list[dict] = []
    for value in results:
        r = value.model_dump(mode="json") if hasattr(value, "model_dump") else value
        endpoint, detail = r["endpoint"], r.get("diagnostics", {})
        ids = {
            "Dependent": DISPLAY.get(endpoint, endpoint),
            "Units": "ng/mL" if endpoint == "cmax" else "h*ng/mL",
        }
        lsm_r, lsm_t = detail.get("lsm_r", {}), detail.get("lsm_t", {})
        a = {
            **ids,
            "FormVar": "Treatment",
            "FormRef": "R",
            "RefLSM": r.get("lsmean_log_r"),
            "RefLSM_SE": lsm_r.get("se"),
            "RefGeoLSM": r.get("adjusted_geometric_mean_r"),
            "Test": "T",
            "TestLSM": r.get("lsmean_log_t"),
            "TestLSM_SE": lsm_t.get("se"),
            "TestGeoLSM": r.get("adjusted_geometric_mean_t"),
            "Difference": r.get("estimate"),
            "Diff_SE": r.get("se"),
            "Diff_DF": r.get("df"),
            "Ratio_%Ref_": 100 * r["gmr"] if r.get("gmr") is not None else None,
        }
        for confidence, lo_key, hi_key in (
            (80, "ci80_lower", "ci80_upper"),
            (90, "ci_lower", "ci_upper"),
            (95, "ci95_lower", "ci95_upper"),
        ):
            a[f"CI_{confidence}_Lower"] = 100 * r[lo_key] if r.get(lo_key) is not None else None
            a[f"CI_{confidence}_Upper"] = 100 * r[hi_key] if r.get(hi_key) is not None else None
            intervals.append(
                {
                    **ids,
                    "Confidence_%": confidence,
                    "GMR_%": a["Ratio_%Ref_"],
                    "Lower_%": a[f"CI_{confidence}_Lower"],
                    "Upper_%": a[f"CI_{confidence}_Upper"],
                }
            )
        # Legacy-named TOST columns always refer to conventional 80–125%, including when scaled BE is selected.
        ancillary = detail.get("ancillary", {})
        if r.get("estimate") is not None and r.get("se"):
            t1 = (r["estimate"] - math.log(0.8)) / r["se"]
            t2 = (r["estimate"] - math.log(1.25)) / r["se"]
            p1, p2 = float(t.sf(t1, r["df"])), float(t.cdf(t2, r["df"]))
            a.update(
                t1_TOST=t1, t2_TOST=t2, Prob_80_00=p1, Prob_125_00=p2, MaxProb=max(p1, p2), TotalProb=p1 + p2
            )
        for key in ("Power_TOST", "AHpval", "Power_80_20", "Prob_Eq_Var"):
            a[key] = ancillary.get(key)
        a.update(
            Endpoint_Role=detail.get("endpoint_role", "independent review"),
            Method=r["method"],
            Decision=r["decision"],
            Reason=r.get("reason", ""),
            N_subjects=r.get("n", 0),
            N_observations=r.get("n_observations", 0),
            N_missing=r.get("n_excluded", 0),
            Applicable_Lower_Percent=100 * r.get("lower_limit", 0.8),
            Applicable_Upper_Percent=100 * r.get("upper_limit", 1.25),
        )
        average.append(a)
        for criterion in r.get("criteria", []):
            flattened = {**ids}
            for k, v in criterion.items():
                if isinstance(v, list) and len(v) == 2:
                    flattened[f"{k}_lower"], flattened[f"{k}_upper"] = v
                else:
                    flattened[k] = json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
            criteria.append(flattened)
        for row in detail.get("fixed_parameters", detail.get("ema_method_a", {}).get("fixed_parameters", [])):
            fixed.append({**ids, **_infer(row)})
        for row in detail.get("lsmeans", []):
            lsmeans.append({**ids, **_infer(row), "Geometric_LSM": math.exp(row["estimate"])})
        if detail.get("difference"):
            reverse = dict(detail["difference"])
            reverse.update(
                estimate=-reverse["estimate"],
                t=-reverse["t"],
                lower=-detail["difference"]["upper"],
                upper=-detail["difference"]["lower"],
            )
            differences.append({**ids, "Level_Level": "R - T", **_infer(reverse)})
        for name, output in (
            ("partial_tests", partial_tests),
            ("sequential_ss", sequential_ss),
            ("partial_ss", partial_ss),
        ):
            output.extend({**ids, **row} for row in detail.get(name, []))
        variance = detail.get("variance_parameters", {})
        for name, key in (
            ("Var(Sequence*Subject)", "subject"),
            ("Var(Residual)", "residual"),
            ("Intersubject CV", "cv_between"),
            ("Intrasubject CV", "cv_within"),
        ):
            if key in variance:
                variances.append({**ids, "Parameter": name, "Estimate": variance[key]})
        for name in ("swr", "swt", "cv_wr", "cv_wt"):
            if name in detail:
                variances.append({**ids, "Parameter": name, "Estimate": detail[name]})
        residuals.extend(
            {**ids, **row}
            for row in detail.get("residuals", detail.get("ema_method_a", {}).get("residuals", []))
            if isinstance(row, dict)
        )
        residual_diagnostics.extend(
            {**ids, "Units": "natural-log model scale", "Source_PK_Units": ids["Units"], **row}
            for row in detail.get("residual_diagnostics", [])
        )
        subjects.extend({**ids, **row} for row in detail.get("replicate", {}).get("subjects", []))
        intermediate.extend(
            {**ids, **_infer(row)} for row in detail.get("replicate", {}).get("intermediate_parameters", [])
        )
        if detail.get("howe"):
            howe.append({**ids, **detail["howe"]})
        missing.extend({**ids, **row} for row in detail.get("excluded_observations", []))
        for key, item in detail.get("model_diagnostics", {}).items():
            diagnostics.append(
                {
                    **ids,
                    "Diagnostic": key,
                    "Value": json.dumps(item) if isinstance(item, (dict, list)) else item,
                }
            )
        diagnostics.append({**ids, "Diagnostic": "model", "Value": detail.get("model", r.get("reason", ""))})
    return {
        "Average Bioequivalence": pd.DataFrame(average),
        "Confidence Intervals": pd.DataFrame(intervals),
        "Decision Criteria": pd.DataFrame(criteria),
        "Partial Tests": pd.DataFrame(partial_tests),
        "Sequential SS": pd.DataFrame(sequential_ss),
        "Partial SS": pd.DataFrame(partial_ss),
        "Final Fixed Parameters": pd.DataFrame(fixed),
        "Final Variance Parameters": pd.DataFrame(variances),
        "Least Squares Means": pd.DataFrame(lsmeans),
        "LSM Differences": pd.DataFrame(differences),
        "Residuals": pd.DataFrame(residuals),
        "Residual Diagnostics": pd.DataFrame(residual_diagnostics),
        "Subject Contrasts": pd.DataFrame(subjects),
        "FDA Intermediate Fits": pd.DataFrame(intermediate),
        "Howe Components": pd.DataFrame(howe),
        "Missing Observations": pd.DataFrame(missing),
        "Diagnostics": pd.DataFrame(diagnostics),
        **reviewer_tables(results, data=data, design=design),
    }


def be_workbook(results, *, data=None, metadata=None, tmax_comparison=None):
    tables = be_tables(results, data=data)
    if data is not None:
        tables["Input PK"] = data
    if tmax_comparison is not None:
        tmax = tmax_comparison.model_dump() if hasattr(tmax_comparison, "model_dump") else (
            vars(tmax_comparison) if not isinstance(tmax_comparison, dict) else tmax_comparison
        )
        tables["Tmax Nonparametric"] = pd.DataFrame([{
            "Status": tmax.get("status"), "Method": tmax.get("method"),
            "N_T": tmax.get("n_t"), "Median_T_h": tmax.get("median_t"),
            "Min_T_h": tmax.get("min_t"), "Max_T_h": tmax.get("max_t"),
            "N_R": tmax.get("n_r"), "Median_R_h": tmax.get("median_r"),
            "Min_R_h": tmax.get("min_r"), "Max_R_h": tmax.get("max_r"),
            "N_pairs": tmax.get("n_pairs"),
            "Median_paired_T_minus_R_h": tmax.get("median_paired_difference"),
            "Statistic": tmax.get("statistic"), "P_two_sided": tmax.get("p_value"),
            "Reason": tmax.get("reason"), "Interpretation": tmax.get("note"),
        }])
    settings = {
        "Engine": __version__,
        "Status": "DRAFT / independent review required",
        "Interpretation": "Decision Criteria controls conclusions. Legacy power, AH and equal-variance tests are ancillary.",
        "CI": "Ratios and CI are percentages in tables; original-scale and log-scale values are explicitly labeled.",
        "SS": "OLS sums of squares are diagnostic. REML Wald tests use Satterthwaite df; do not combine their denominators.",
        "FDA source": "https://www.fda.gov/media/163638/download",
        "EMA source": "https://www.ema.europa.eu/en/scientific-guidelines/investigation-bioequivalence",
        **(metadata or {}),
    }
    tables["Settings"] = pd.DataFrame(
        [
            {
                "Setting": k,
                "Value": json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v),
            }
            for k, v in settings.items()
        ]
    )
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for name, frame in tables.items():
            if frame.empty:
                frame = pd.DataFrame(
                    {"Information": ["Not applicable / not estimable for the selected data and method."]}
                )
            frame.to_excel(writer, sheet_name=name, index=False)
            sheet = writer.sheets[name]
            sheet.freeze_panes = "C2"
            sheet.auto_filter.ref = sheet.dimensions
            sheet.row_dimensions[1].height = 34
            sheet.sheet_view.zoomScale = 90
            for cell in sheet[1]:
                cell.font = Font(name="Calibri", bold=True, color="FFFFFF")
                cell.fill = PatternFill("solid", fgColor="17365D")
                cell.alignment = Alignment(wrap_text=True, vertical="center")
            for i, col in enumerate(frame.columns, 1):
                width = (
                    24
                    if col in ("Dependent", "Parameter", "Effect_Level", "Diagnostic", "criterion", "Setting")
                    else max(16, min(28, len(str(col)) + 3))
                )
                if col in ("Value", "Reason", "Method", "Information", "model", "constant_note"):
                    width = 72
                if col == "criterion":
                    width = 48
                if col == "Endpoint_Role":
                    width = 24
                sheet.column_dimensions[get_column_letter(i)].width = width
            for row in sheet.iter_rows(min_row=2):
                lines = 1
                for cell in row:
                    cell.alignment = Alignment(vertical="top", wrap_text=isinstance(cell.value, str))
                    if isinstance(cell.value, float):
                        cell.number_format = (
                            "0.00E+00"
                            if frame.columns[cell.column - 1]
                            in (
                                "Abs difference",
                                "P_value",
                                "p",
                                "Value",
                                "value",
                                "Relative_Tolerance",
                                "Absolute_Tolerance",
                                "Prob_80_00",
                                "Prob_125_00",
                                "MaxProb",
                                "TotalProb",
                                "AHpval",
                                "Prob_Eq_Var",
                                "Power_TOST",
                                "upper_95",
                                "x",
                                "y",
                                "bound_x",
                                "bound_y",
                            )
                            else "0.000000"
                        )
                    if isinstance(cell.value, str):
                        if cell.value.startswith(("=", "+", "-", "@")):
                            cell.data_type = "s"
                        lines = max(
                            lines,
                            math.ceil(
                                len(cell.value) / (sheet.column_dimensions[cell.column_letter].width - 2)
                            ),
                        )
                sheet.row_dimensions[row[0].row].height = max(16, 16 * lines)
    return output.getvalue()

