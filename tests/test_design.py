import json
import math

import numpy as np
import pytest
from scipy.stats import t

from be_app.design import randomize, sample_schedule, sample_size, tost_power
from be_app.regulations import capability_for, planning_limits
from tests.conftest import FIXTURES


@pytest.mark.parametrize("row", json.loads((FIXTURES / "golden.json").read_text())["power"])
def test_power_public_golden(row):
    actual = tost_power(row["cv"], row["gmr"], row["n1"], row["n2"], row["design"])
    assert abs(actual - row["expected"]) <= row["tolerance"]


@pytest.mark.parametrize(
    "design,n,block", [("2x2", 26, 4), ("parallel", 24, 6), ("partial3", 27, 6), ("full4", 24, 4)]
)
def test_randomization_balanced_reproducible(design, n, block):
    frame, metadata = randomize(design, n, 12345, block)
    same, same_metadata = randomize(design, n, 12345, block)
    assert frame.equals(same) and metadata == same_metadata
    subjects = frame.drop_duplicates("subject_id")
    assert subjects.sequence.value_counts().nunique() == 1
    assert len(subjects) == n and not frame.duplicated(["subject_id", "period"]).any()
    for row in frame.itertuples():
        assert row.treatment == row.sequence[row.period - 1]
    schedule = sample_schedule(frame, [0, 1, 2])
    assert schedule.actual_time_h.eq("").all() and schedule.sample_datetime.eq("").all()


@pytest.mark.parametrize("args", [("2x2", 13, 1, 4), ("partial3", 24, 1, 4), ("unknown", 24, 1, 4)])
def test_bad_randomization(args):
    with pytest.raises(ValueError):
        randomize(*args)


def test_sample_size_public_reference():
    result = sample_size(0.2, dropout=0.2)
    assert result.evaluable == 20 and result.recruit == 26
    assert tost_power(0.2, 0.95, 9, 9) < 0.8


def test_nti_bounds_differ_from_standard_abe_and_planning_is_gated(demo):
    study = demo.study.model_copy(update={"rule_set_id": "EMA_NTI", "nti": True})
    bounds = planning_limits(study)
    assert bounds == {"AUC": (0.9, 1.1111), "Cmax": (0.8, 1.25)}
    assert not capability_for("EMA_NTI").planning
    standard = sample_size(0.2, 0.95, 0.8, dropout=0.1)
    narrower = sample_size(0.2, 0.95, 0.8, dropout=0.1, lower=0.9, upper=1.1111)
    assert narrower.evaluable > standard.evaluable
    with pytest.raises(ValueError, match="GMR"):
        sample_size(0.2, 0.88, 0.8, lower=0.9, upper=1.1111)
    tightened = study.model_copy(update={"nti_cmax_narrow": True})
    assert planning_limits(tightened)["Cmax"] == (0.9, 1.1111)


def test_planning_fingerprint_invalidates_when_rule_or_nti_cmax_changes(demo):
    from be_app.ui import planning_context, planning_fingerprint

    inputs = dict(cv_auc=20, cv_cmax=30, gmr_auc=0.95, gmr_cmax=0.95, target=80, dropout=10)
    base = planning_context(demo.study, demo.be_config)
    fp = planning_fingerprint(inputs, base, "0.3.1")
    alternate = demo.study.model_copy(update={"rule_set_id": "FDA_ABE_2026"})
    assert planning_fingerprint(inputs, planning_context(alternate, demo.be_config), "0.3.1") != fp
    nti = demo.study.model_copy(update={"rule_set_id": "EMA_NTI", "nti": True})
    nti_context = planning_context(nti, demo.be_config)
    assert planning_fingerprint(inputs, nti_context, "0.3.1") != fp
    narrower = nti.model_copy(update={"nti_cmax_narrow": True})
    assert (
        planning_fingerprint(inputs, planning_context(narrower, demo.be_config), "0.3.1")
        != planning_fingerprint(inputs, nti_context, "0.3.1")
    )


def test_parallel_is_not_crossover():
    assert tost_power(0.3, 0.95, 12, 12, "parallel") < tost_power(0.3, 0.95, 12, 12, "2x2")
    result = sample_size(0.2, design="parallel")
    assert result.per_group >= 12


@pytest.mark.parametrize(
    "cv,gmr,n1,n2,design",
    [
        (30, 0.95, 10, 10, "2x2"),
        (0.2, 0, 10, 10, "2x2"),
        (0.2, 0.95, 1, 10, "2x2"),
        (0.2, 0.95, 10, 10, "full4"),
        (float("nan"), 0.95, 10, 10, "2x2"),
        (0.2, 0.95, 10.5, 10, "2x2"),
    ],
)
def test_power_rejects_invalid(cv, gmr, n1, n2, design):
    with pytest.raises(ValueError):
        tost_power(cv, gmr, n1, n2, design)


def test_joint_probability_against_independent_simulation():
    rng = np.random.default_rng(129)
    n1, n2, cv, gmr = 8, 10, 0.3, 0.95
    df = n1 + n2 - 2
    se = math.sqrt(math.log1p(cv**2) * 0.5 * (1 / n1 + 1 / n2))
    delta = rng.normal(math.log(gmr), se, 200_000)
    estimated_se = se * np.sqrt(rng.chisquare(df, len(delta)) / df)
    critical = t.ppf(0.95, df)
    success = (delta - critical * estimated_se >= math.log(0.8)) & (
        delta + critical * estimated_se <= math.log(1.25)
    )
    assert abs(success.mean() - tost_power(cv, gmr, n1, n2)) < 0.004


def test_power_symmetry_monotonicity_and_null_boundary():
    assert tost_power(0.3, 0.95, 15, 15) == pytest.approx(tost_power(0.3, 1 / 0.95, 15, 15), abs=1e-12)
    assert tost_power(0.3, 1, 20, 20) > tost_power(0.3, 1, 10, 10)
    assert tost_power(0.3, 0.8, 20, 20) <= 0.05
    assert tost_power(0.3, 1.25, 20, 20) <= 0.05
