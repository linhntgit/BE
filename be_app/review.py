"""Read-only reviewer views derived from one stored input/result snapshot.

Eligibility is descriptive: it never filters input or makes a BE decision.
"""

import json
import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.stats import norm

PERIODS = {"2x2": 2, "parallel": 1, "partial3": 3, "full4": 4}
SEQUENCES = {"2x2": {"TR", "RT"}, "partial3": {"TRR", "RTR", "RRT"}, "full4": {"TRTR", "RTRT"}}


def result_dicts(results):
    return [r.model_dump(mode="json") if hasattr(r, "model_dump") else r for r in results]


def terminal_figure(group, automatic, draft):
    """Display selected terminal points and the stored fit, without refitting."""
    data = group.loc[group.concentration.gt(0)].sort_values("actual_time_h")
    figure = go.Figure(
        go.Scatter(
            x=data.actual_time_h,
            y=data.concentration,
            mode="lines+markers",
            name="Observed > 0",
            line=dict(color="#555555"),
        )
    )
    for label, result, color, symbol, dash in (
        ("Automatic", automatic, "#0072B2", "circle-open", "dash"),
        ("Draft", draft, "#D55E00", "diamond-open", "dot"),
    ):
        selected = result.get("terminal_selected")
        if not selected:
            continue
        times = selected["times"]
        points = data.loc[data.actual_time_h.isin(times)]
        figure.add_trace(
            go.Scatter(
                x=points.actual_time_h,
                y=points.concentration,
                mode="markers",
                name=label + " selected points",
                marker=dict(color=color, symbol=symbol, size=13, line=dict(width=2)),
            )
        )
        fit_times = np.array([min(times), max(times)])
        figure.add_trace(
            go.Scatter(
                x=fit_times,
                y=np.exp(selected["intercept"] + selected["slope"] * fit_times),
                mode="lines",
                name=label + " terminal fit",
                line=dict(color=color, dash=dash),
            )
        )
    figure.update_layout(
        xaxis_title="Actual sampling time (h)",
        yaxis_title="Concentration (ng/mL)",
        yaxis_type="log",
        legend=dict(orientation="h", y=-0.22),
        margin=dict(b=100),
    )
    return figure


def decision_review(results):
    rows = []
    for r in result_dicts(results):
        detail = r.get("diagnostics", {})
        for criterion in r.get("criteria", []) or [{"criterion": "Model not evaluable"}]:
            limits = criterion.get("limits", [criterion.get("lower"), criterion.get("upper")])
            passed = criterion.get("passed")
            value = criterion.get("value")
            rows.append(
                dict(
                    Endpoint=r["endpoint"],
                    Role=detail.get("endpoint_role", "independent review"),
                    Method=r["method"],
                    Criterion=criterion["criterion"],
                    Value=json.dumps(value) if isinstance(value, (list, dict)) else value,
                    Lower=limits[0],
                    Upper=limits[1],
                    Scale="log criterion" if "Howe" in criterion["criterion"] else "ratio (not %)",
                    Criterion_result="PASS"
                    if passed is True
                    else "FAIL"
                    if passed is False
                    else "NOT EVALUABLE",
                    Endpoint_result=r["decision"],
                    N_subjects=r.get("n", 0),
                    N_observations=r.get("n_observations", 0),
                    Reason=r.get("reason", ""),
                )
            )
    return pd.DataFrame(rows)


def population_matrix(data, results, design):
    """Show expected cells including absent periods, without imputing or selecting subjects."""
    columns = [
        "Endpoint",
        "Subject",
        "Sequence",
        "Period",
        "Expected_treatment",
        "Observed_treatment",
        "PK",
        "Cell_status",
        "Contrast_complete",
        "Two_R_complete",
        "Two_T_complete",
        "Model_used",
        "R_variance_used",
        "T_variance_used",
    ]
    if data is None:
        return pd.DataFrame(columns=columns)
    d = pd.DataFrame(data).copy()
    required = {"subject_id", "sequence", "period", "treatment"}
    if d.empty or not required <= set(d.columns):
        return pd.DataFrame(columns=columns)
    if design is None:
        sequences = set(d.sequence.dropna().map(str))
        design = next(
            (name for name, allowed in SEQUENCES.items() if sequences and sequences <= allowed), None
        )
        if sequences and sequences <= {"T", "R"}:
            design = "parallel"
    if design not in PERIODS:
        return pd.DataFrame(columns=columns)
    d["_subject"] = d.subject_id.map(lambda x: str(x) if pd.notna(x) else "<missing subject>")
    d["_period"] = pd.to_numeric(d.period, errors="coerce")
    rows = []
    for r in result_dicts(results):
        endpoint = r["endpoint"]
        for subject, block in d.groupby("_subject", sort=True):
            seqs = block.sequence.dropna().map(str).unique()
            sequence = seqs[0] if len(seqs) == 1 else "<missing/conflicting>"
            sequence_ok = (
                sequence in {"T", "R"} if design == "parallel" else sequence in SEQUENCES[design]
            ) and subject != "<missing subject>"
            subject_rows = []
            expected_periods = set(range(1, PERIODS[design] + 1))
            extra = set(block._period.dropna()) - expected_periods
            periods = [*sorted(expected_periods), *sorted(extra)]
            if block._period.isna().any():
                periods.append(None)
            for period in periods:
                cell = block.loc[block._period.isna() if period is None else block._period.eq(period)]
                in_design = period in expected_periods
                expected = (
                    (sequence if design == "parallel" else sequence[int(period) - 1])
                    if sequence_ok and in_design
                    else ""
                )
                value = (
                    pd.to_numeric(cell[endpoint], errors="coerce")
                    if endpoint in cell
                    else pd.Series(dtype=float)
                )
                numeric = len(value) == 1 and bool(np.isfinite(value.iloc[0])) and value.iloc[0] > 0
                treatment = ", ".join(cell.treatment.fillna("<missing>").map(str))
                if cell.empty:
                    status = "Missing period"
                elif len(cell) > 1:
                    status = "Duplicate period"
                elif not sequence_ok or not in_design or treatment != expected:
                    status = "Invalid design/identity"
                elif not numeric:
                    status = "Missing/nonpositive/nonfinite PK"
                else:
                    status = "Available"
                subject_rows.append(
                    dict(
                        Endpoint=endpoint,
                        Subject=subject,
                        Sequence=sequence,
                        Period=period,
                        Expected_treatment=expected,
                        Observed_treatment=treatment,
                        PK=float(value.iloc[0]) if numeric else None,
                        Cell_status=status,
                    )
                )
            complete = all(x["Cell_status"] == "Available" for x in subject_rows)
            two_r = (
                sum(x["Cell_status"] == "Available" and x["Expected_treatment"] == "R" for x in subject_rows)
                >= 2
            )
            two_t = (
                sum(x["Cell_status"] == "Available" and x["Expected_treatment"] == "T" for x in subject_rows)
                >= 2
            )
            fitted = r.get("estimate") is not None
            available_fit = r.get("diagnostics", {}).get("missing_policy") == "available_observations"
            for row in subject_rows:
                used = fitted and row["Cell_status"] == "Available" and (complete or available_fit)
                row.update(
                    Contrast_complete=complete,
                    Two_R_complete=two_r,
                    Two_T_complete=two_t,
                    Model_used=used,
                    R_variance_used=used and r.get("swr") is not None and row["Expected_treatment"] == "R",
                    T_variance_used=used and r.get("swt") is not None and row["Expected_treatment"] == "T",
                )
            rows.extend(subject_rows)
    return pd.DataFrame(rows, columns=columns)


def population_counts(matrix):
    rows = []
    if matrix.empty:
        return pd.DataFrame()
    for endpoint, block in matrix.groupby("Endpoint", sort=False):
        subjects = block.drop_duplicates("Subject")
        rows.append(
            dict(
                Endpoint=endpoint,
                Input_subjects=block.Subject.nunique(),
                Complete_subjects=int(subjects.Contrast_complete.sum()),
                Subjects_with_two_R=int(subjects.Two_R_complete.sum()),
                Subjects_with_two_T=int(subjects.Two_T_complete.sum()),
                Model_subjects=block.loc[block.Model_used, "Subject"].nunique(),
                Model_observations=int(block.Model_used.sum()),
                R_variance_subjects=block.loc[block.R_variance_used, "Subject"].nunique(),
                R_variance_observations=int(block.R_variance_used.sum()),
                T_variance_subjects=block.loc[block.T_variance_used, "Subject"].nunique(),
                T_variance_observations=int(block.T_variance_used.sum()),
            )
        )
    return pd.DataFrame(rows)


def pk_descriptive(data, endpoints):
    rows = []
    if data is None:
        return pd.DataFrame()
    d = pd.DataFrame(data)
    if "treatment" not in d:
        return pd.DataFrame()
    for endpoint in endpoints:
        if endpoint not in d:
            continue
        for treatment, block in d.groupby("treatment", dropna=False, sort=False):
            values = pd.to_numeric(block[endpoint], errors="coerce")
            finite = values[np.isfinite(values)]
            positive = finite[finite > 0]
            n = len(finite)
            mean = float(finite.mean()) if n else None
            sd = float(finite.std(ddof=1)) if n > 1 else None
            log_sd = float(np.log(positive).std(ddof=1)) if len(positive) > 1 else None
            rows.append(
                dict(
                    Endpoint=endpoint,
                    Treatment=treatment,
                    N_observations=n,
                    N_subjects=block.loc[np.isfinite(values), "subject_id"].nunique()
                    if "subject_id" in block
                    else None,
                    N_missing_or_nonfinite=len(block) - n,
                    N_nonpositive=int((finite <= 0).sum()),
                    Mean=mean,
                    SD=sd,
                    CV_percent=100 * sd / mean if sd is not None and mean and mean > 0 else None,
                    Median=float(finite.median()) if n else None,
                    Minimum=float(finite.min()) if n else None,
                    Maximum=float(finite.max()) if n else None,
                    Geometric_mean=float(np.exp(np.log(positive).mean()))
                    if len(positive) == n and n and endpoint != "tmax"
                    else None,
                    Geometric_CV_percent=100 * math.sqrt(math.expm1(log_sd**2))
                    if log_sd is not None and log_sd < 26 and len(positive) == n and endpoint != "tmax"
                    else None,
                    Basis="Observed PK rows; replicated administrations are not independent subjects",
                )
            )
    return pd.DataFrame(rows)


def reviewer_tables(results, *, data=None, design=None):
    values = result_dicts(results)
    matrix = population_matrix(data, values, design)
    return {
        "Reviewer Criteria": decision_review(values),
        "Population Matrix": matrix,
        "Population Counts": population_counts(matrix),
        "PK Descriptive": pk_descriptive(data, [r["endpoint"] for r in values]),
    }


def forest_figure(results):
    """Each endpoint gets its own acceptance band; FDA scaled CI is contextual only."""
    fig = go.Figure()
    labels = []
    for index, r in enumerate(result_dicts(results)):
        role = r.get("diagnostics", {}).get("endpoint_role", "independent")
        labels.append(f"{r['endpoint']} · {role}")
        decisive = any("CI 90% within acceptance" in c["criterion"] for c in r.get("criteria", []))
        lo, hi = 100 * r.get("lower_limit", 0.8), 100 * r.get("upper_limit", 1.25)
        fig.add_shape(
            type="rect",
            x0=lo,
            x1=hi,
            y0=index - 0.25,
            y1=index + 0.25,
            fillcolor="#dce8f2" if decisive else "#eeeeee",
            line_width=0,
            layer="below",
        )
        fig.add_trace(
            go.Scatter(
                x=[lo, hi],
                y=[index, index],
                mode="markers",
                marker=dict(symbol="line-ns", size=18, color="#677c8e"),
                name=f"{r['endpoint']}: {lo:.2f}–{hi:.2f}%" + (" (CI bổ trợ)" if not decisive else ""),
            )
        )
        if all(r.get(k) is not None for k in ("gmr", "ci_lower", "ci_upper")):
            gmr, lower, upper = [100 * r[k] for k in ("gmr", "ci_lower", "ci_upper")]
            fig.add_trace(
                go.Scatter(
                    x=[gmr],
                    y=[index],
                    mode="markers",
                    marker=dict(size=10, color="#235789"),
                    error_x=dict(type="data", symmetric=False, array=[upper - gmr], arrayminus=[gmr - lower]),
                    name=f"{r['endpoint']} · endpoint: {r['decision']}",
                    customdata=[[lower, upper, r["method"]]],
                    hovertemplate="GMR %{x:.4f}%<br>CI90 %{customdata[0]:.4f}–%{customdata[1]:.4f}%<br>%{customdata[2]}<extra></extra>",
                )
            )
    fig.add_vline(x=100, line_dash="dot", line_color="#777777")
    fig.update_layout(
        title="GMR và CI90 theo giới hạn từng endpoint",
        xaxis_title="T/R (%)",
        yaxis=dict(tickmode="array", tickvals=list(range(len(labels))), ticktext=labels),
        height=max(480, 110 * len(labels) + 180),
        margin=dict(b=150),
        legend=dict(orientation="h", y=-0.32, yanchor="top"),
    )
    return fig


def criterion_figures(results):
    figures = []
    for field, threshold, title in (
        ("scaled_ucb", 0, "FDA: cận trên 95% theo Howe (≤ 0)"),
        ("sd_ratio_ci_upper", 2.5, "FDA NTI: cận trên CI90 của sWT/sWR (≤ 2.5)"),
    ):
        selected = [r for r in result_dicts(results) if r.get(field) is not None]
        if selected:
            fig = go.Figure(
                go.Scatter(
                    x=[r[field] for r in selected],
                    y=[r["endpoint"] for r in selected],
                    mode="markers",
                    marker=dict(size=10, color="#235789"),
                )
            )
            fig.add_vline(
                x=threshold,
                line_dash="dash",
                annotation_text=f"Ngưỡng {threshold:g}",
                annotation_position="top left",
            )
            minimum, maximum = (
                min(*[r[field] for r in selected], threshold),
                max(*[r[field] for r in selected], threshold),
            )
            padding = max((maximum - minimum) * 0.08, 0.001)
            fig.update_xaxes(range=[minimum - padding, maximum + padding])
            fig.update_layout(
                title=title, xaxis_title="Log criterion" if field == "scaled_ucb" else "Tỷ lệ SD", height=300
            )
            figures.append(fig)
    return figures


def residual_figures(frame):
    """Display diagnostics from one named fit; never pool reference/FDA/EMA models."""
    figures: list[go.Figure] = []
    if frame.empty or not {"Predicted", "Residual"} <= set(frame.columns):
        return figures
    valid = frame.loc[np.isfinite(pd.to_numeric(frame.Residual, errors="coerce"))].copy()
    if valid.empty:
        return figures
    labels = valid.get("subject_id", pd.Series(valid.index, index=valid.index)).map(str)
    fig = go.Figure(go.Scatter(x=valid.Predicted, y=valid.Residual, mode="markers", text=labels))
    fig.add_hline(y=0, line_dash="dot")
    fig.update_layout(
        title="Phần dư theo fitted value", xaxis_title="Fitted (model scale)", yaxis_title="Residual"
    )
    figures.append(fig)
    values = np.sort(valid.Residual.to_numpy(dtype=float))
    theoretical = norm.ppf((np.arange(1, len(values) + 1) - 0.5) / len(values))
    qq = go.Figure(go.Scatter(x=theoretical, y=values, mode="markers"))
    qq.update_layout(
        title="QQ plot phần dư — chẩn đoán mô tả",
        xaxis_title="Normal quantile",
        yaxis_title="Residual quantile",
    )
    figures.append(qq)
    box = go.Figure(go.Box(y=values, boxpoints="all", name="Residuals"))
    box.update_layout(title="Phân bố phần dư", yaxis_title="Residual (model scale)")
    figures.append(box)
    return figures


def workflow_table(run):
    matrix = population_matrix(run.get("nca"), run.get("be", []), run.get("study", {}).get("design"))
    counts = population_counts(matrix)
    return pd.DataFrame(
        [
            {
                "Step": "Input / QC",
                "Rows": len(run.get("validated_data", [])),
                "Basis": "Validated input snapshot",
            },
            {
                "Step": "NCA / PK",
                "Rows": len(run.get("nca", [])),
                "Basis": "One row per subject/period/treatment/analyte",
            },
            {
                "Step": "Population",
                "Rows": len(matrix),
                "Basis": f"{len(counts)} endpoint populations; includes missing expected cells",
            },
            {"Step": "BE models", "Rows": len(run.get("be", [])), "Basis": run.get("rule_set_id", "")},
            {
                "Step": "Decision criteria",
                "Rows": len(decision_review(run.get("be", []))),
                "Basis": run.get("study_decision", ""),
            },
        ]
    ).assign(
        Analysis_run_id=run.get("analysis_run_id"),
        Input_revision=run.get("input_revision"),
        Input_fingerprint=run.get("input_fingerprint"),
    )
