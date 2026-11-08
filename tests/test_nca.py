import json
import math

import numpy as np
import pandas as pd
import pytest
from hypothesis import given
from hypothesis import strategies as hs

from be_app.domain import NcaConfig
from be_app.nca import analyze_profile, integrate_auc
from tests.conftest import FIXTURES


def test_pknca_independent_public_fixture():
    golden = json.loads((FIXTURES / "golden.json").read_text())["pknca"]
    frame = pd.DataFrame(
        dict(
            actual_time_h=golden["times"],
            concentration=golden["concentrations"],
            blq_flag=[x == 0 for x in golden["concentrations"]],
        )
    )
    result = analyze_profile(frame)
    for key in ("auc_last", "cmax", "tmax", "clast", "tlast"):
        assert result[key] == pytest.approx(golden[key], abs=golden["tolerance"])
    # Deliberately stricter terminal QC than PKNCA example: low fit cannot produce AUCinf.
    assert result["auc_inf"] is None


def test_exponential_closed_form(exponential_profile):
    result = analyze_profile(exponential_profile)
    assert result["lambda_z"] == pytest.approx(math.log(2), abs=1e-14)
    assert result["half_life"] == pytest.approx(1)
    assert result["auc_last"] == pytest.approx(8 + 15 / math.log(2))
    assert result["auc_inf"] == pytest.approx(8 + 16 / math.log(2))
    assert result["terminal_selected"]["n"] == 4


def test_pknca_terminal_and_extrapolation_with_matching_policy():
    golden = json.loads((FIXTURES / "golden.json").read_text())["pknca"]
    frame = pd.DataFrame(
        dict(
            actual_time_h=golden["times"],
            concentration=golden["concentrations"],
            blq_flag=[x == 0 for x in golden["concentrations"]],
        )
    )
    # PKNCA vignette reports a low-fit terminal segment without the stricter release QC.
    # Match that documented policy for comparison; leave production defaults unchanged.
    result = analyze_profile(frame, NcaConfig(terminal_min_adj_r2=0, terminal_min_span_half_lives=0))
    for key in ("lambda_z", "half_life", "auc_inf"):
        assert result[key] == pytest.approx(golden[key], abs=golden["tolerance"])
    assert result["terminal_selected"]["times"] == [3, 4, 5, 8]


def test_linear_hand_calculation():
    assert integrate_auc([0, 1, 2, 4], [0, 4, 2, 0], "linear") == 7
    assert integrate_auc([0, 1, 2], [0, 4, 2]) == pytest.approx(2 + 2 / math.log(2))


@pytest.mark.parametrize(
    "times,conc",
    [([0, 1, 1], [0, 1, 2]), ([0, 2, 1], [0, 1, 2]), ([0, 1], [0, -1]), ([0, 1], [0, float("nan")])],
)
def test_auc_invalid(times, conc):
    with pytest.raises(ValueError):
        integrate_auc(times, conc)


def test_missing_not_zero(exponential_profile):
    exponential_profile.loc[3, "concentration"] = np.nan
    result = analyze_profile(exponential_profile)
    assert result["status"] == "NOT EVALUABLE" and result["auc_last"] is None


def test_blq_terminal_never_logged(exponential_profile):
    exponential_profile.loc[5, "concentration"] = np.nan
    exponential_profile.loc[5, "blq_flag"] = True
    result = analyze_profile(exponential_profile)
    assert result["clast"] == 2 and result["tlast"] == 4
    assert result["lambda_z"] == pytest.approx(math.log(2))


def test_tmax_tie_and_manual_reason(exponential_profile):
    exponential_profile.loc[2, "concentration"] = 16
    assert analyze_profile(exponential_profile)["tmax"] == 1
    assert analyze_profile(exponential_profile, NcaConfig(tmax_tie="last"))["tmax"] == 2
    with pytest.raises(ValueError):
        NcaConfig(manual_terminal_times=(3, 4, 5))
    result = analyze_profile(
        exponential_profile, NcaConfig(manual_terminal_times=(3, 4, 5), manual_reason="SAP review")
    )
    assert result["terminal_selected"]["times"] == [3, 4, 5]


@pytest.mark.parametrize("change", ["no_baseline", "duplicate", "negative", "missing_status", "predose"])
def test_profile_failure_not_pass(exponential_profile, change):
    data = exponential_profile.copy()
    if change == "no_baseline":
        data = data.iloc[1:]
    elif change == "duplicate":
        data.loc[2, "actual_time_h"] = 1
    elif change == "negative":
        data.loc[1, "concentration"] = -1
    elif change == "missing_status":
        data["sample_status"] = "VALID"
        data.loc[1, "sample_status"] = "MISSING"
    else:
        data.loc[0, "concentration"] = 3
        data.loc[0, "blq_flag"] = False
    assert analyze_profile(data)["status"] == "NOT EVALUABLE"


def test_terminal_insufficient_points(exponential_profile):
    result = analyze_profile(exponential_profile.iloc[:4])
    assert result["cmax"] == 16 and result["auc_inf"] is None


@given(hs.floats(min_value=0.01, max_value=1000, allow_nan=False, allow_infinity=False))
def test_auc_concentration_scaling(scale):
    t, c = [0, 1, 2, 3], np.array([0, 5, 3, 1])
    assert integrate_auc(t, c * scale) == pytest.approx(integrate_auc(t, c) * scale, rel=1e-12)
