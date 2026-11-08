import json
import math

import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm
from statsmodels.stats.weightstats import ttost_ind

from be_app.domain import BeConfig, BeResult
from be_app.statistics import aggregate_decision, analyze_abe, ema_abel_limits, fda_hvd_branch
from tests.conftest import FIXTURES


@pytest.mark.parametrize("golden", json.loads((FIXTURES / "golden.json").read_text())["abe"])
def test_abe_against_published_r_result(reference_pk, golden):
    result = analyze_abe(reference_pk, golden["endpoint"], "2x2")
    assert result.decision == "PASS" and result.df == 31
    for key in ("gmr", "ci_lower", "ci_upper"):
        assert getattr(result, key) == pytest.approx(golden[key], abs=0.00000051)
    assert result.diagnostics["mse"] == pytest.approx(golden["mse"], abs=5e-9)
    assert result.cv_within == pytest.approx(golden["cv"], abs=1e-9)


@pytest.mark.parametrize("count", [0, 1, 5, 10])
def test_2x2_against_independent_full_matrix_ols(reference_pk, count):
    data = reference_pk.loc[
        ~reference_pk.subject_id.isin(
            reference_pk.loc[reference_pk.sequence == "RT", "subject_id"].unique()[:count]
        )
    ].copy()
    # Independent direct model with subject fixed effects; sequence is absorbed into subject.
    matrix = pd.get_dummies(data.subject_id.astype(str), drop_first=True, dtype=float)
    matrix["period2"] = (data.period == 2).astype(float)
    matrix["test"] = (data.treatment == "T").astype(float)
    fit = sm.OLS(np.log(data.auc_last), sm.add_constant(matrix)).fit()
    result = analyze_abe(data, "auc_last", "2x2")
    assert result.estimate == pytest.approx(fit.params["test"], abs=2e-13)
    assert result.se == pytest.approx(fit.bse["test"], abs=2e-13)
    assert result.df == fit.df_resid


@pytest.mark.parametrize("variance", ["pooled", "welch"])
def test_parallel_independent_statsmodels(variance):
    rng = np.random.default_rng(120)
    a, b = rng.lognormal(3, 0.2, 29), rng.lognormal(3.04, 0.35, 20)
    data = pd.DataFrame(
        dict(
            subject_id=[f"S{i}" for i in range(49)],
            sequence=["T"] * 29 + ["R"] * 20,
            treatment=["T"] * 29 + ["R"] * 20,
            period=1,
            auc_last=[*a, *b],
        )
    )
    result = analyze_abe(data, "auc_last", "parallel", BeConfig(parallel_variance=variance))
    pvalue, low_test, high_test = ttost_ind(
        np.log(a),
        np.log(b),
        math.log(0.8),
        math.log(1.25),
        usevar="pooled" if variance == "pooled" else "unequal",
    )
    assert result.p_lower == pytest.approx(low_test[1], abs=1e-13)
    assert result.p_upper == pytest.approx(high_test[1], abs=1e-13)
    assert result.df == pytest.approx(low_test[2])
    assert (result.decision == "PASS") == (pvalue <= 0.05)


@pytest.mark.parametrize(
    "failure",
    [
        "missing_period",
        "wrong_treatment",
        "wrong_sequence",
        "duplicate",
        "negative",
        "missing",
        "replicate",
        "zero_variance",
    ],
)
def test_statistics_fail_closed(reference_pk, failure):
    data = reference_pk.copy()
    design = "2x2"
    if failure == "missing_period":
        data = data.iloc[1:]
    elif failure == "wrong_treatment":
        data.loc[0, "treatment"] = "T"
    elif failure == "wrong_sequence":
        data.loc[0, "sequence"] = "TR"
    elif failure == "duplicate":
        data = pd.concat([data, data.iloc[:1]], ignore_index=True)
    elif failure == "negative":
        data.loc[0, "auc_last"] = -1
    elif failure == "missing":
        data.loc[0, "auc_last"] = np.nan
    elif failure == "replicate":
        design = "partial3"
    else:
        data["auc_last"] = np.where(data.treatment == "T", 100, 99)
    assert analyze_abe(data, "auc_last", design).decision == "NOT EVALUABLE"


def test_fail_is_not_p_treatment(reference_pk):
    data = reference_pk.copy()
    data.loc[data.treatment == "T", "auc_last"] *= 1.5
    assert analyze_abe(data, "auc_last", "2x2").decision == "FAIL"


def test_unrounded_ci_controls_decision(reference_pk):
    baseline = analyze_abe(reference_pk, "auc_last", "2x2")
    data = reference_pk.copy()
    data.loc[data.treatment == "T", "auc_last"] *= 0.79999999 / baseline.ci_lower
    result = analyze_abe(data, "auc_last", "2x2")
    assert f"{100 * result.ci_lower:.2f}" == "80.00"
    assert result.decision == "FAIL"


@pytest.mark.parametrize("cv", [0.299, 0.30, 0.35, 0.40, 0.50, 0.75])
def test_ema_scaling_boundaries_and_auc(cv):
    swr = math.sqrt(math.log1p(cv**2))
    lower, upper = ema_abel_limits(swr)
    assert ema_abel_limits(swr, "auc_last") == (0.8, 1.25)
    if cv <= 0.30:
        assert (lower, upper) == (0.8, 1.25)
    else:
        assert upper == pytest.approx(min(1.4319, math.exp(0.760 * min(swr, math.sqrt(math.log1p(0.5**2))))))
    assert lower >= 0.6984 and upper <= 1.4319


@pytest.mark.parametrize("swr,branch", [(0.2939999, "ABE"), (0.294, "RSABE"), (0.2940001, "RSABE")])
def test_fda_branch_never_calls_ema_abel_or_pass(swr, branch):
    result = fda_hvd_branch(swr)
    assert result["branch"] == branch and result["decision"] == "NOT EVALUABLE"
    assert result["theta"] == pytest.approx((math.log(1.25) / 0.25) ** 2)
    with pytest.raises(ValueError):
        fda_hvd_branch(swr, nti=True)


def test_aggregation_fails_closed():
    a = BeResult(endpoint="auc_last", decision="PASS")
    c = BeResult(endpoint="cmax", decision="PASS")
    assert aggregate_decision([a, c], ("auc_last", "cmax")) == "PASS"
    assert aggregate_decision([a], ("auc_last", "cmax")) == "NOT EVALUABLE"
    assert aggregate_decision([a, a], ("auc_last", "cmax")) == "NOT EVALUABLE"
    assert aggregate_decision([a, c], ("auc_last", "cmax"), ["unverified scope"]) == "NOT EVALUABLE"
    assert aggregate_decision([a, c.model_copy(update={"decision": "FAIL"})], ("auc_last", "cmax")) == "FAIL"
