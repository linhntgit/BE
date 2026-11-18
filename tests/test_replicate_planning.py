"""Replicate planning: exact standard ABE and seeded scaled decision probabilities."""

import json
import math

import pytest

from be_app.design import sample_size, tost_power
from be_app.regulations import capability_for
from be_app.replicate_planning import replicate_power, replicate_sample_size


@pytest.mark.parametrize("rule", [
    "EMA_REPLICATE_STANDARD", "FDA_REPLICATE_STANDARD", "EMA_HVDP_ABEL",
    "FDA_HVD_RSABE_2026", "FDA_NTI", "EMA_NTI",
])
def test_replicate_planning_capability(rule):
    assert capability_for(rule).planning


@pytest.mark.parametrize("design,count", [("partial3", 3), ("full4", 2)])
def test_exact_replicate_abe_and_size(design, count):
    n = count * 8
    result = replicate_power(.25, .95, n, design=design)
    assert result.simulations == 0 and result.mc_se == 0
    assert 0 < result.power < 1
    assert tost_power(.25, .95, 8, 8, design=design) == pytest.approx(result.power)
    size = sample_size(.25, design=design, dropout=.2)
    assert size.evaluable % count == 0
    assert size.recruit == count * math.ceil(size.per_group / .8)
    assert size.achieved_power >= .8
    if size.per_group > 6:
        assert replicate_power(.25, .95, count * (size.per_group - 1), design=design).power < .8


@pytest.mark.parametrize("rule,design,n", [
    ("EMA_REPLICATE_STANDARD", "partial3", 30),
    ("EMA_REPLICATE_STANDARD", "full4", 24),
    ("FDA_REPLICATE_STANDARD", "partial3", 30),
    ("FDA_REPLICATE_STANDARD", "full4", 24),
])
def test_replicate_exact_tost_agrees_with_decision_simulation(rule, design, n):
    from be_app.replicate_planning import _simulated_decisions

    exact = replicate_power(.27, .97, n, design=design, rule_set_id=rule).power
    simulated = _simulated_decisions(
        .27, .27, .97, n, design, rule,
        lower=.8, upper=1.25, alpha=.05,
        simulations=20000, seed=61, endpoint="Cmax",
    )
    assert simulated == pytest.approx(exact, abs=.02)


def test_scaled_replicate_seeded_mc_and_branches():
    ema_scaled = replicate_power(.4, .95, 24, rule_set_id="EMA_HVDP_ABEL", simulations=4000)
    assert ema_scaled == replicate_power(.4, .95, 24, rule_set_id="EMA_HVDP_ABEL", simulations=4000)
    assert ema_scaled.simulations == 4000 and 0 < ema_scaled.mc_se < .01
    auc = replicate_power(.4, .95, 24, rule_set_id="EMA_HVDP_ABEL", endpoint="AUC")
    conventional = replicate_power(.4, .95, 24)
    assert auc == conventional
    assert ema_scaled.power > conventional.power

    below = replicate_power(.2, .95, 24, rule_set_id="FDA_HVD_RSABE_2026", simulations=15000)
    unscaled = replicate_power(.2, .95, 24, rule_set_id="FDA_REPLICATE_STANDARD")
    assert below.power == pytest.approx(unscaled.power, abs=.025)


def test_fda_nti_requires_full_replicate_and_both_variances():
    base = replicate_power(.12, .98, 24, design="full4", rule_set_id="FDA_NTI", simulations=6000)
    different = replicate_power(.12, .98, 24, design="full4", rule_set_id="FDA_NTI",
                                cv_wt=.5, simulations=6000)
    assert base.power > different.power
    with pytest.raises(ValueError, match="full"):
        replicate_power(.12, .98, 24, design="partial3", rule_set_id="FDA_NTI")


@pytest.mark.parametrize("rule,design,cv,gmr", [
    ("EMA_HVDP_ABEL", "partial3", .4, .95),
    ("FDA_HVD_RSABE_2026", "full4", .4, .95),
    ("FDA_NTI", "full4", .12, .98),
])
def test_scaled_sample_size_reaches_target(rule, design, cv, gmr):
    result, detail = replicate_sample_size(cv, gmr, target=.8, design=design,
                                           rule_set_id=rule, simulations=1500, seed=41,
                                           max_n=240)
    assert result.achieved_power >= .8
    assert 0 <= detail.mc_se <= .013
    assert result.evaluable % (3 if design == "partial3" else 2) == 0


def test_ema_nti_narrowed_power_and_validation():
    ordinary = replicate_power(.2, .98, 24, design="full4", rule_set_id="EMA_REPLICATE_STANDARD")
    narrow = replicate_power(.2, .98, 24, design="full4", rule_set_id="EMA_NTI",
                             lower=.9, upper=1.1111)
    assert narrow.power < ordinary.power
    with pytest.raises(ValueError):
        replicate_power(float("nan"), .98, 24)
    with pytest.raises(ValueError):
        replicate_power(.2, .98, 25, design="full4")
    with pytest.raises(ValueError):
        replicate_power(.4, .98, 24, rule_set_id="FDA_HVD_RSABE_2026", alpha=.1)


def test_power_plan_replicate_serialization_and_fingerprint():
    from be_app.ui import power_plan

    inputs = dict(cv_auc=20, cv_cmax=40, cv_wt_auc=20, cv_wt_cmax=40,
                  gmr_auc=.95, gmr_cmax=.95, target=80, dropout=10,
                  source="Pilot", simulations=1500, seed=42)
    context = dict(rule_set_id="EMA_HVDP_ABEL", design="partial3", alpha=.05,
                   bounds={"AUC": [.8, 1.25], "Cmax": [.8, 1.25]})
    result = power_plan(json.dumps(inputs), json.dumps(context), "test")
    assert result["evaluable"] % 3 == 0
    assert result["recruit"] >= result["evaluable"]
    assert {r["endpoint"] for r in result["results"]} == {"AUC", "Cmax"}
    assert len(result["curve"]) == 7
    assert all("mc_se" in r for r in result["results"])
