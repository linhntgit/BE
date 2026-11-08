"""Inspectable statistical tables for nonreplicate mixed-model ABE."""

import math
from collections.abc import Sequence

import numpy as np
import pandas as pd
from scipy.stats import f, nct, t

from be_app.mixed import fit_random_intercept, ols


def crossover_tables(data: pd.DataFrame, endpoint: str, lower=0.8, upper=1.25):
    d = data.copy().reset_index(drop=True)
    y = np.log(d[endpoint].to_numpy(dtype=float))
    x = np.column_stack([np.ones(len(d)), d.sequence.eq("RT"), d.treatment.eq("R"), d.period.eq(1)]).astype(
        float
    )
    fit = fit_random_intercept(y, x, d.subject_id)
    contrast = fit["contrast"]
    difference = contrast([0, 0, -1, 0])
    lsm_r, lsm_t = contrast([1, 0.5, 1, 0.5]), contrast([1, 0.5, 0, 0.5])
    fixed = []
    weights: Sequence[float]
    for label, weights in (
        ("int", [1, 0, 0, 0]),
        ("Sequence:RT", [0, 1, 0, 0]),
        ("Treatment:R", [0, 0, 1, 0]),
        ("Period:1", [0, 0, 0, 1]),
    ):
        fixed.append({"Effect_Level": label, **contrast(weights, 0.95)})
    lsmeans = [{"Level": "R", **lsm_r}, {"Level": "T", **lsm_t}]
    tests = []
    for label, weights in (
        ("int", [1, 0.5, 0.5, 0.5]),
        ("Sequence", [0, 1, 0, 0]),
        ("Treatment", [0, 0, 1, 0]),
        ("Period", [0, 0, 0, 1]),
    ):
        c = contrast(weights)
        tests.append(
            dict(
                Hypothesis=label,
                Numer_DF=1,
                Denom_DF=c["df"],
                F_stat=c["t"] ** 2,
                P_value=float(f.sf(c["t"] ** 2, 1, c["df"])),
            )
        )
    residuals = []
    for record, observed, predicted, residual in zip(
        d.to_dict("records"), y, fit["predicted"], fit["residuals"], strict=True
    ):
        residuals.append(
            {
                **{k: record[k] for k in ("subject_id", "sequence", "period", "treatment")},
                "Ln_Observed": float(observed),
                "Predicted": predicted,
                "Residual": residual,
            }
        )
    # OLS sums of squares are a separate diagnostic from REML/Wald inference.
    base = x[:, :2]
    nested = []
    for _, group in d.groupby("sequence", sort=True):
        for subject in sorted(group.subject_id.unique(), key=str)[1:]:
            nested.append(d.subject_id.eq(subject).to_numpy(dtype=float))
    matrix = np.column_stack([base, *nested, x[:, 2], x[:, 3]])
    full = ols(y, matrix)
    stages = [
        ("Sequence", base),
        ("Sequence*Subject", np.column_stack([base, *nested])),
        ("Treatment", matrix[:, :-1]),
        ("Period", matrix),
    ]
    previous_ss = float(np.sum((y - y.mean()) ** 2))
    previous_rank = 1
    sequential = []
    for label, stage in stages:
        current = ols(y, stage)
        rank = int(np.linalg.matrix_rank(stage))
        df = rank - previous_rank
        ss = max(0.0, previous_ss - current["sse"])
        sequential.append(dict(Hypothesis=label, DF=df, SS=ss, MS=ss / df if df else None))
        previous_ss, previous_rank = current["sse"], rank
    sequence_subject_ms = sequential[1]["MS"]
    for row in sequential:
        denom = sequence_subject_ms if row["Hypothesis"] == "Sequence" else full["mse"]
        denom_df = sequential[1]["DF"] if row["Hypothesis"] == "Sequence" else full["df"]
        value = row["MS"] / denom if denom and row["DF"] else None
        row.update(
            F_stat=value,
            P_value=float(f.sf(value, row["DF"], denom_df)) if value is not None else None,
            Denom_DF=denom_df,
        )
    sequential.append(
        dict(Hypothesis="Error", DF=full["df"], SS=full["sse"], MS=full["mse"], F_stat=None, P_value=None)
    )
    partial = []
    term_columns = [
        ("Sequence", [1]),
        ("Sequence*Subject", list(range(2, matrix.shape[1] - 2))),
        ("Treatment", [matrix.shape[1] - 2]),
        ("Period", [matrix.shape[1] - 1]),
    ]
    for label, indices in term_columns:
        reduced = ols(y, np.delete(matrix, indices, axis=1))
        df = len(indices)
        ss = max(0.0, reduced["sse"] - full["sse"])
        # Sequence tested between subjects; preserve the full-model test rather than coding-dependent SS.
        if label == "Sequence":
            partial.append(sequential[0].copy())
        else:
            value = (ss / df) / full["mse"]
            partial.append(
                dict(
                    Hypothesis=label,
                    DF=df,
                    SS=ss,
                    MS=ss / df,
                    F_stat=value,
                    P_value=float(f.sf(value, df, full["df"])),
                    Denom_DF=full["df"],
                )
            )
    partial.append(sequential[-1].copy())
    se, delta, df = difference["se"], difference["estimate"], difference["df"]
    t1, t2 = (delta - math.log(lower)) / se, (delta - math.log(upper)) / se
    critical = float(t.ppf(0.95, df))
    # Ancillary statistical diagnostics; these are not regulatory BE decision rules.
    power_tost = max(0.0, float(nct.cdf(-critical, df, t2) - nct.cdf(critical, df, t1)))
    ah = abs(float(t.cdf(t1, df) - t.cdf(-t2, df)))
    detect = -math.log(0.8) / se
    power_8020 = float(t.cdf(-critical - detect, df) + t.sf(critical - detect, df))
    variances = dict(
        subject=fit["subject_variance"],
        residual=fit["residual_variance"],
        cv_between=math.sqrt(math.expm1(fit["subject_variance"])),
        cv_within=math.sqrt(math.expm1(fit["residual_variance"])),
    )
    pairs = d.pivot(index="subject_id", columns="treatment", values=endpoint).dropna()
    equal_variance_p = None
    if len(pairs) >= 3 and {"T", "R"} <= set(pairs.columns):
        sums = np.log(pairs["T"]) + np.log(pairs["R"])
        differences = np.log(pairs["T"]) - np.log(pairs["R"])
        if sums.std() > 0 and differences.std() > 0:
            correlation = float(np.corrcoef(sums, differences)[0, 1])
            if abs(correlation) < 1:
                statistic = abs(correlation) * math.sqrt((len(pairs) - 2) / (1 - correlation**2))
                equal_variance_p = float(2 * t.sf(statistic, len(pairs) - 2))
    return dict(
        difference=difference,
        lsm_r=lsm_r,
        lsm_t=lsm_t,
        fixed_parameters=fixed,
        lsmeans=lsmeans,
        partial_tests=tests,
        sequential_ss=sequential,
        partial_ss=partial,
        residuals=residuals,
        variance_parameters=variances,
        mse=fit["residual_variance"],
        model="REML: Sequence + Treatment + Period; random Subject(Sequence); Satterthwaite",
        model_diagnostics=dict(
            converged=fit["converged"],
            variance_boundary=fit["boundary"],
            reml_log_likelihood=float(fit["reml_log_likelihood"]),
            hessian_eigenvalues=fit["hessian_eigenvalues"],
            n_observations=len(d),
            n_subjects=int(d.subject_id.nunique()),
            ols_residual_df=full["df"],
            ols_residual_ss=full["sse"],
        ),
        ancillary=dict(
            t1_TOST=t1,
            t2_TOST=t2,
            Power_TOST=power_tost,
            AHpval=ah,
            Power_80_20=power_8020,
            Prob_Eq_Var=equal_variance_p,
            Pitman_Morgan_n_pairs=len(pairs),
            note="Thống kê bổ trợ; observed power và AH không thay thế 90% CI hoặc TOST để kết luận BE.",
        ),
    )
