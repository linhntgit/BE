"""Vendor-neutral NCA tables and Excel export for computed analysis snapshots."""

import io
import json
import math

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from be_app import __version__


# NCA parameter definitions and export table layout for this independent application.
PARAMETERS = [
    ("N_Samples", "n_samples", ""),
    ("Dose", "dose", "dose"),
    ("Rsq", "r2", ""),
    ("Rsq_adjusted", "adjusted_r2", ""),
    ("Corr_XY", "corr_xy", ""),
    ("No_points_lambda_z", "n", ""),
    ("Lambda_z", "lambda_z", "1/h"),
    ("Lambda_z_intercept", "intercept", ""),
    ("Lambda_z_lower", "lower", "h"),
    ("Lambda_z_upper", "upper", "h"),
    ("HL_Lambda_z", "half_life", "h"),
    ("Span", "span_half_lives", ""),
    ("Tlag", "tlag", "h"),
    ("Tmax", "tmax", "h"),
    ("Cmax", "cmax", "ng/mL"),
    ("Cmax_D", "cmax_d", "ng/mL/dose"),
    ("Tlast", "tlast", "h"),
    ("Clast", "clast", "ng/mL"),
    ("Clast_pred", "clast_pred", "ng/mL"),
    ("AUClast", "auc_last", "h*ng/mL"),
    ("AUClast_D", "auc_last_d", "h*ng/mL/dose"),
    ("AUCall", "auc_all", "h*ng/mL"),
    ("AUCall_D", "auc_all_d", "h*ng/mL/dose"),
    ("AUCINF_obs", "auc_inf", "h*ng/mL"),
    ("AUCINF_D_obs", "auc_inf_d", "h*ng/mL/dose"),
    ("AUC_%Extrap_obs", "auc_extrap_pct", "%"),
    ("Vz_F_obs", "vz_f", "mL"),
    ("Cl_F_obs", "cl_f", "mL/h"),
    ("AUCINF_pred", "auc_inf_pred", "h*ng/mL"),
    ("AUCINF_D_pred", "auc_inf_pred_d", "h*ng/mL/dose"),
    ("AUC_%Extrap_pred", "auc_extrap_pct_pred", "%"),
    ("Vz_F_pred", "vz_f_pred", "mL"),
    ("Cl_F_pred", "cl_f_pred", "mL/h"),
    ("AUMClast", "aumc_last", "h*h*ng/mL"),
    ("AUMCINF_obs", "aumc_inf", "h*h*ng/mL"),
    ("AUMC_%Extrap_obs", "aumc_extrap_pct", "%"),
    ("AUMCINF_pred", "aumc_inf_pred", "h*h*ng/mL"),
    ("AUMC_%Extrap_pred", "aumc_extrap_pct_pred", "%"),
    ("MRTlast", "mrt_last", "h"),
    ("MRTINF_obs", "mrt_inf", "h"),
    ("MRTINF_pred", "mrt_inf_pred", "h"),
]
KEYS = ["Subject", "Treatment", "Sequence", "Period"]
PARAM_COLUMNS = ["Subject", "Treatment", "Parameter", "Units", "Estimate", "Sequence", "Period"]
SUMMARY_COLUMNS = [
    "Time",
    *KEYS,
    "lambda_z_Incl",
    "Concentration",
    "Predicted",
    "Residual",
    "AUC",
    "AUMC",
    "Weighting",
]
METHOD_REFERENCE = "docs/ALGORITHM_SPEC.md"


def parameter_values(result: dict) -> dict:
    terminal = result.get("terminal_selected", {})
    values = dict(result)
    values.update(
        {key: terminal.get(key) for key in ("r2", "adjusted_r2", "corr_xy", "intercept", "span_half_lives")}
    )
    values.update(
        n=terminal.get("n", 0),
        lower=min(terminal["times"]) if terminal else None,
        upper=max(terminal["times"]) if terminal else None,
    )
    for key in ("cmax", "auc_last", "auc_all", "auc_inf", "auc_inf_pred"):
        value, dose = result.get(key), result.get("dose")
        values[key + "_d"] = value / dose if value is not None and dose else None
    return {name: values.get(key) for name, key, _ in PARAMETERS}


def nca_tables(results: list[dict]) -> dict[str, pd.DataFrame]:
    long, pivot, slopes, dosing, summary, warnings = [], [], [], [], [], []
    for result in results:
        ids = dict(
            zip(
                KEYS, [str(result[k]) for k in ("subject_id", "treatment", "sequence", "period")], strict=True
            )
        )
        values = parameter_values(result)
        pivot.append({**ids, **values})
        for name, _, unit in PARAMETERS:
            long.append(
                {
                    **ids,
                    "Parameter": name,
                    "Units": unit.replace("dose", result.get("dose_unit", "mg")),
                    "Estimate": values[name],
                }
            )
        selected = result.get("terminal_selected", {})
        slopes.append(
            {
                **ids,
                "Start Time": values["Lambda_z_lower"],
                "End Time": values["Lambda_z_upper"],
                "Exclusions": "",
                "Fit Method": "TimeRange" if result["config"].get("manual_terminal_times") else "BestFit",
                "Selection": "User" if result["config"].get("manual_terminal_times") else "System",
                "Rsq_adjusted": selected.get("adjusted_r2"),
                "Review Reason": result.get("terminal_review", {}).get(
                    "reason", result["config"].get("manual_reason", "")
                ),
                "Reviewer": result.get("terminal_review", {}).get("reviewer", ""),
                "Profile Data Hash": result.get("terminal_review", {}).get("profile_data_hash", ""),
            }
        )
        dosing.append(
            {**ids, "Time": 0, "Dose": result.get("dose"), "Dose Unit": result.get("dose_unit", "mg")}
        )
        for point in result.get("profile_points", []):
            summary.append(
                {
                    **ids,
                    "Time": point["time"],
                    "lambda_z_Incl": "*" if point["terminal"] else None,
                    "Concentration": point["concentration"],
                    "Predicted": point["predicted"],
                    "Residual": point["residual"],
                    "AUC": point["auc"],
                    "AUMC": point["aumc"],
                    "Weighting": point["weighting"],
                }
            )
        for warning in [result.get("reason", ""), *result.get("warnings", [])]:
            if warning:
                warnings.append({**ids, "Message": warning})
    return {
        "Final Parameters Pivoted": pd.DataFrame(
            pivot, columns=["Subject", "Treatment", *[p[0] for p in PARAMETERS], "Sequence", "Period"]
        ),
        "Final Parameters": pd.DataFrame(long, columns=PARAM_COLUMNS),
        "Dosing Used": pd.DataFrame(dosing),
        "Slopes Settings": pd.DataFrame(slopes),
        "Summary Table": pd.DataFrame(summary, columns=SUMMARY_COLUMNS),
        "Warnings and Errors": pd.DataFrame(warnings, columns=[*KEYS, "Message"]),
    }


def nca_workbook(results: list[dict], *, metadata: dict | None = None) -> bytes:
    """Export a computed snapshot using the Python runtime shipped with this app."""
    tables = nca_tables(results)
    tables["Settings"] = pd.DataFrame(
        [
            {"Setting": "Engine", "Value": __version__},
            {"Setting": "Status", "Value": "DRAFT / single-dose extravascular NCA"},
            {
                "Setting": "Methods",
                "Value": json.dumps(results[0]["config"], ensure_ascii=False) if results else "",
            },
            {"Setting": "Method documentation", "Value": METHOD_REFERENCE},
            *[{"Setting": k, "Value": str(v)} for k, v in (metadata or {}).items()],
        ]
    )
    output = io.BytesIO()
    # Export workbook with the bundled openpyxl dependency.
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for name, frame in tables.items():
            units_row = name in ("Final Parameters Pivoted", "Summary Table")
            frame.to_excel(writer, sheet_name=name, index=False, startrow=1 if units_row else 0)
            sheet = writer.sheets[name]
            if units_row:
                # Include units on a separate row for inspection.
                for column, label in enumerate(frame.columns, 1):
                    sheet.cell(1, column, label)
                    unit = ""
                    if name == "Final Parameters Pivoted":
                        unit = next((u for n, _, u in PARAMETERS if n == label), "")
                        unit = unit.replace("dose", results[0].get("dose_unit", "mg")) if results else unit
                    else:
                        unit = {
                            "Time": "h",
                            "Concentration": "ng/mL",
                            "Predicted": "ng/mL",
                            "Residual": "ng/mL",
                            "AUC": "h*ng/mL",
                            "AUMC": "h*h*ng/mL",
                        }.get(label, "")
                    sheet.cell(2, column).value = unit or None
            sheet.freeze_panes = "C3" if units_row else "C2"
            sheet.auto_filter.ref = f"A1:{get_column_letter(sheet.max_column)}{sheet.max_row}"
            sheet.sheet_view.zoomScale = 90
            for cell in sheet[1]:
                cell.font = Font(name="Calibri", bold=True, color="FFFFFF")
                cell.fill = PatternFill("solid", fgColor="17365D")
                cell.alignment = Alignment(wrap_text=True, vertical="center")
            sheet.row_dimensions[1].height = 32
            for column, label in enumerate(frame.columns, 1):
                width = max(14, min(26, len(str(label)) + 3))
                if label in ("Parameter", "Setting"):
                    width = 28
                if label == "Units":
                    width = 22
                if label in ("Message", "Value"):
                    width = 88
                sheet.column_dimensions[get_column_letter(column)].width = width
            for row in sheet.iter_rows(min_row=2):
                for cell in row:
                    cell.alignment = Alignment(vertical="top", wrap_text=isinstance(cell.value, str))
                    if isinstance(cell.value, float):
                        cell.number_format = (
                            "0.00E+00" if frame.columns[cell.column - 1] == "Abs difference" else "0.000000"
                        )
                    if isinstance(cell.value, str) and cell.value.startswith(("=", "+", "-", "@")):
                        cell.data_type = "s"  # Untrusted labels must never become Excel formulas.
                lines = max(
                    (
                        max(
                            math.ceil(
                                len(line) / max(1, sheet.column_dimensions[cell.column_letter].width - 2)
                            )
                            for line in str(cell.value).split("\n")
                        )
                        if isinstance(cell.value, str)
                        else 1
                    )
                    for cell in row
                )
                sheet.row_dimensions[row[0].row].height = max(16, 16 * lines)
    return output.getvalue()


