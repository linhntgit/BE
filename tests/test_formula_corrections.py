"""Independent numerical and entry-point regressions for the formula audit."""

import io
import math

import numpy as np
import pandas as pd
import pytest
from scipy.stats import t

from be_app.domain import BeConfig, Study
from be_app.examples import demo_project
from be_app.pipeline import run_analysis
from be_app.pk_analysis import PKSettings, analyze_nca
from be_app.pk_models import fit_compartment, predict
from be_app.pk_multiple import PKRegimen, analyze_interval_nca
from be_app.quick_be import quick_be_workbook, run_quick_be
from be_app.replicate import analyze_regulatory_be
from be_app.statistics import _result, ci_within_limits
from tests.test_pk_standalone import profile
from tests.test_quick_be import pk_table, run


def endpoint_data(design, n_t, n_r=0):
    rows = []
    for i in range(n_t + n_r if design == "parallel" else n_t):
        sequence = ("T" if i < n_t else "R") if design == "parallel" else ("TR" if i % 2 else "RT")
        for period, treatment in enumerate(sequence, 1):
            subject_effect = i % n_t if design == "parallel" else i
            value = (20 + subject_effect) * math.exp((.04 if treatment == "T" else 0) + .01 * period * (i % 3))
            rows.append(dict(subject_id=str(i), sequence=sequence, period=period,
                             treatment=treatment, cmax=value, auc_last=value * 3))
    return pd.DataFrame(rows)


@pytest.mark.parametrize("design,n_t,n_r,eligible", [
    ("2x2", 6, 0, False), ("2x2", 11, 0, False), ("2x2", 12, 0, True),
    ("parallel", 11, 13, False), ("parallel", 12, 12, True),
])
def test_regulatory_and_quick_entry_points_agree(design, n_t, n_r, eligible):
    data = endpoint_data(design, n_t, n_r)
    study = Study(study_id="AUDIT", title="Audit", design=design)
    direct = analyze_regulatory_be(data, "cmax", study)
    quick = run_quick_be(data.to_csv(index=False).encode(), "audit.csv", design=design)
    actual = next(r for r in quick.results if r.endpoint == "cmax")
    assert actual.decision == direct.decision
    assert (actual.decision != "NOT EVALUABLE") == eligible
    assert actual.reason == direct.reason
    assert actual.ci_lower == pytest.approx(direct.ci_lower)
    if not eligible:
        assert "12" in actual.reason


def test_six_subjects_export_keeps_ci_and_ineligibility():
    out = run(pk_table())
    assert out.overall_status == "NOT EVALUABLE"
    assert all(r.gmr is not None and r.ci_lower is not None for r in out.results)
    workbook = pd.read_excel(io.BytesIO(quick_be_workbook(out)), sheet_name=None)
    text = " ".join(frame.to_string() for frame in workbook.values())
    assert "NOT EVALUABLE" in text and "crossover có 6" in text


@pytest.mark.parametrize("n", [6, 12])
def test_project_and_quick_concentration_results_agree(n):
    project = demo_project(n=n)
    analyzed = run_analysis(project.freeze())
    data = project.clean_frame()
    quick = run_quick_be(data.to_csv(index=False).encode(), "project.csv", mode="concentration")
    stored = analyzed.runs[-1]["be"]
    for expected in stored:
        result = next(r for r in quick.results if r.endpoint == expected["endpoint"])
        assert result.decision == expected["decision"]
        assert result.reason == expected["reason"]
        assert result.ci_lower == pytest.approx(expected["ci_lower"])


def test_missing_primary_endpoint_blocks_quick_assessment():
    data = endpoint_data("2x2", 12)
    data.loc[0, "auc_last"] = np.nan
    out = run_quick_be(data.to_csv(index=False).encode(), "missing.csv")
    assert out.overall_status == "NOT EVALUABLE"
    assert next(r for r in out.results if r.endpoint == "auc_last").decision == "NOT EVALUABLE"


@pytest.mark.parametrize("rule_id", ["EMA_IR_NONREPLICATE_M13A", "FDA_ABE_2026"])
def test_ci_near_boundary_passes_through_normal_entry_points(rule_id):
    data = endpoint_data("2x2", 12)
    lo, hi = math.log(.79996), math.log(1.05)
    estimate = (lo + hi) / 2
    se = (hi - lo) / (2 * t.ppf(.95, 10))
    scale = se * math.sqrt(12 / 3.5)
    for i in range(12):
        difference = estimate + scale * (i // 2 - 2.5)
        data.loc[(data.subject_id == str(i)) & data.treatment.eq("T"), ["cmax", "auc_last"]] = math.exp(difference)
        data.loc[(data.subject_id == str(i)) & data.treatment.eq("R"), ["cmax", "auc_last"]] = 1.0
    study = Study(study_id="BOUNDARY", title="Boundary", rule_set_id=rule_id)
    direct = analyze_regulatory_be(data, "cmax", study)
    quick = run_quick_be(data.to_csv(index=False).encode(), "boundary.csv", rule_id=rule_id)
    assert direct.ci_lower == pytest.approx(.79996)
    assert direct.ci_upper == pytest.approx(1.05)
    assert direct.decision == quick.overall_status == "PASS"
    assert all(r.criteria[0]["passed"] for r in quick.results)


@pytest.mark.parametrize("low,high,passed", [
    (.79996, 1.05, True), (.79994, 1.05, False),
    (.9, 1.25004, True), (.9, 1.25006, False),
    (.79995, 1.05, True), (.9, 1.25005, False),
])
def test_ci_rounding_in_percentage_units(low, high, passed):
    assert ci_within_limits(low, high, .8, 1.25, round_percent=True) == passed
    lo, hi = math.log(low), math.log(high)
    result = _result("cmax", endpoint_data("2x2", 12), (lo + hi) / 2,
                     (hi - lo) / (2 * t.ppf(.95, 10)), 10, BeConfig(), {}, round_ci=True)
    # Exact halfway values are tested directly above, avoiding log/exp roundoff.
    if low != .79995 and high != 1.25005:
        assert result.decision == ("PASS" if passed else "FAIL")
    assert result.ci_lower == pytest.approx(low)


@pytest.mark.parametrize("basis", ["first_dose", "last_dose"])
@pytest.mark.parametrize("times,expected", [([.2, 12, 23.8], None), ([0, 12, 24], 240)])
def test_interval_boundaries_do_not_depend_on_dose_count(basis, times, expected):
    regimen = PKRegimen(mode="steady_state", tau_h=24, number_doses=1000,
                        time_basis=basis, steady_state_confirmed=True)
    input_times = np.array(times) + (regimen.last_dose_h if basis == "first_dose" else 0)
    result = analyze_interval_nca(profile(input_times, [10, 10, 10]), PKSettings(dose=1), regimen)
    assert result["auc_tau_ng_h_ml"] == expected
    if expected is None:
        assert result["cavg_tau_ng_ml"] is None
        assert result["cl_over_f_ss_l_h"] is None
        assert result["ctrough_ng_ml"] is None
    else:
        assert result["cavg_tau_ng_ml"] == 10


def test_iv_extrapolation_preserves_observed_peak():
    settings = PKSettings(route="iv_bolus", dose=1, zero_policy="extrapolate_iv")
    result = analyze_nca(profile([1, 2, 3, 4], [8, 4, 2, 1]), settings)
    assert result["cmax_ng_ml"] == 8
    assert result["tmax_h"] == 1
    assert result["c0_estimated_ng_ml"] == pytest.approx(16)
    assert result["auc_0_inf"] == pytest.approx(16 / math.log(2))
    measured = analyze_nca(profile([0, 1, 2, 3, 4], [16, 8, 4, 2, 1]), settings)
    assert measured["cmax_ng_ml"] == 16 and measured["tmax_h"] == 0


@pytest.mark.parametrize("weighting", ["equal", "1/C", "1/C²"])
def test_information_criteria_include_residual_scale(weighting):
    settings = PKSettings(route="iv_bolus", dose=1)
    times = np.arange(10.)
    y = predict(times, {"CL": 5, "Vc": 20}, settings, 1) * np.exp(.03 * np.sin(times))
    fitted = fit_compartment(profile(times, y), settings, starts=2, weighting=weighting)
    rss = fitted["rss"] if weighting == "equal" else fitted["weighted_rss"]
    base = 10 * math.log(rss / 10)
    assert fitted["aic"] == pytest.approx(base + 6)
    assert fitted["aicc"] == pytest.approx(base + 6 + 4)
    assert fitted["bic"] == pytest.approx(base + 3 * math.log(10))


def test_aicc_model_ranking_matches_independent_calculation():
    settings = PKSettings(route="iv_bolus", dose=1)
    times = np.array([0, .2, .5, 1, 2, 3, 5, 8, 12, 18])
    values = predict(times, {"CL": 5, "Vc": 12, "Q": 7, "Vp": 25}, settings, 2)
    data = profile(times, values * np.exp(.02 * np.cos(times)))
    fits = [fit_compartment(data, settings, compartments=c, starts=2) for c in (1, 2)]
    independent = []
    for fit in fits:
        k = len(fit["parameters"]) + 1
        independent.append(10 * math.log(fit["rss"] / 10) + 2 * k + 2 * k * (k + 1) / (10 - k - 1))
    assert [fit["aicc"] for fit in fits] == pytest.approx(independent)
    assert np.argmin([fit["aicc"] for fit in fits]) == np.argmin(independent)
