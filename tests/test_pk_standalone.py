"""Analytical benchmarks and round-trip checks for independent PK analysis."""

import io
import json
import math
import zipfile
from dataclasses import asdict

import numpy as np
import pandas as pd
import pytest
from scipy.linalg import expm

from be_app.pk_analysis import PKSettings, analyze_nca, read_concentrations
from be_app.pk_models import fit_compartment, predict
from be_app.pk_records import (
    PKRecordStore,
    create_snapshot,
    excel_report,
    pdf_report,
    record_bytes,
    word_report,
)


def profile(t, c, name="PK01"):
    return pd.DataFrame({"profile_id": [name] * len(t), "time_h": t,
                         "concentration": c, "blq": [False] * len(t)})


def test_long_wide_and_explicit_blq():
    long = pd.DataFrame({"id": ["A", "A", "B", "B"], "t": [0, 1, 0, 1],
                         "c": ["BLQ", "2.0", "0", "3.0"]})
    out = read_concentrations(long, layout="long", time_column="t",
                              concentration_column="c", profile_column="id")
    assert out.blq.tolist() == [True, False, False, False]
    assert out.concentration.tolist() == [0, 2, 0, 3]
    wide = pd.DataFrame({"t": [0, 1], "A": [0, 2], "B": [0, 3]})
    out2 = read_concentrations(wide, layout="wide", time_column="t")
    assert out2.profile_id.unique().tolist() == ["A", "B"]
    bad = pd.DataFrame({"t": [0, 0], "c": [1, 2]})
    with pytest.raises(ValueError, match="Trùng"):
        read_concentrations(bad, layout="long", time_column="t", concentration_column="c")
    bad = pd.DataFrame({"t": [0], "c": [3], "blq": [True]})
    with pytest.raises(ValueError, match="BLQ"):
        read_concentrations(bad, layout="long", time_column="t",
                            concentration_column="c", blq_column="blq")
    with pytest.raises(ValueError, match="Nồng độ"):
        read_concentrations(pd.DataFrame({"t": [0], "c": [None]}), layout="long",
                            time_column="t", concentration_column="c")


@pytest.mark.parametrize("route,duration", [("iv_bolus", None), ("iv_infusion", 2.0)])
def test_iv_nca_clearance_volume_mrt_matches_analytic_dense_curve(route, duration):
    settings = PKSettings(route=route, dose=100.0, infusion_duration_h=duration)
    times = np.arange(0, 80.01, 0.05)
    observed = predict(times, {"CL": 5.0, "Vc": 20.0}, settings, 1)
    result = analyze_nca(profile(times, observed), settings)
    assert result["status"] == "Đủ điều kiện NCA"
    assert result["cl_l_h"] == pytest.approx(5.0, rel=.006)
    assert result["vz_l"] == pytest.approx(20.0, rel=.006)
    assert result["mrt_iv_h"] == pytest.approx(4, rel=.006)
    assert result["vss_l"] == pytest.approx(20, rel=.006)
    assert result["half_life_h"] == pytest.approx(math.log(2) * 4, rel=.001)


def test_oral_has_only_apparent_clearance():
    settings = PKSettings(route="oral", dose=100.0)
    times = np.arange(0, 80.01, .05)
    observed = predict(times, {"CL/F": 5.0, "V/F": 20.0, "ka": 1.2}, settings, 1)
    result = analyze_nca(profile(times, observed), settings)
    assert result["cl_l_h"] is None
    assert result["cl_over_f_l_h"] == pytest.approx(5.0, rel=.01)
    assert result["vz_over_f_l"] == pytest.approx(20, rel=.01)
    assert result["mrt_iv_h"] is None


def test_missing_time_zero_never_silently_completes_auc_or_cl():
    cfg = PKSettings(route="iv_bolus", dose=100.0)
    times = np.arange(.25, 50, .5)
    c = predict(times, {"CL": 5.0, "Vc": 20.0}, cfg, 1)
    incomplete = analyze_nca(profile(times, c), cfg)
    assert incomplete["auc_0_last"] is None
    assert incomplete["auc_0_inf"] is None
    assert incomplete["cl_l_h"] is None
    explicit = analyze_nca(profile(times, c), PKSettings(route="iv_bolus", dose=100.0,
                                                          zero_policy="extrapolate_iv"))
    assert explicit["cl_l_h"] == pytest.approx(5, rel=.02)
    assert explicit["c0_estimated_ng_ml"] == pytest.approx(5000, rel=.01)
    assert any("ngoại suy" in msg.lower() for msg in explicit["warnings"])


def test_iv_bolus_zero_at_time_zero_does_not_enable_dose_parameters():
    cfg = PKSettings(route="iv_bolus", dose=100)
    times = np.arange(0, 40, .5)
    observed = predict(times, {"CL": 5.0, "Vc": 20.0}, cfg, 1)
    observed[0] = 0.0  # Invalid observation immediately after a bolus.
    partial = analyze_nca(profile(times, observed), cfg)
    assert "một phần" in partial["status"]
    assert partial["auc_0_last"] is None
    assert partial["auc_0_inf"] is None
    assert partial["cl_l_h"] is None
    assert partial["t_first_h"] == .5
    assert any("C0" in warning for warning in partial["warnings"])
    extrapolated = analyze_nca(profile(times, observed), PKSettings(
        route="iv_bolus", dose=100, zero_policy="extrapolate_iv"))
    assert extrapolated["cl_l_h"] == pytest.approx(5, rel=.02)
    fitted = fit_compartment(profile(times, observed), cfg)
    assert fitted["n"] == len(times) - 1
    assert fitted["parameters"]["CL"] == pytest.approx(5, rel=.01)
    assert any("t=0" in warning for warning in fitted["warnings"])


def test_blq_inside_measurable_range_is_not_integrated_as_zero():
    cfg = PKSettings(route="oral", dose=100)
    times = np.arange(0, 20, 1)
    data = profile(times, predict(times, {"CL/F": 5, "V/F": 20, "ka": 1.2}, cfg, 1))
    data.loc[5, "blq"] = True
    data.loc[5, "concentration"] = 0.0
    with pytest.raises(ValueError, match="BLQ nằm giữa"):
        analyze_nca(data, cfg)


@pytest.mark.parametrize("route,compartments,parameters,duration", [
    ("iv_bolus", 1, {"CL": 5.0, "Vc": 20.0}, None),
    ("iv_infusion", 1, {"CL": 5.0, "Vc": 20.0}, 2.0),
    ("oral", 1, {"CL/F": 5.0, "V/F": 20.0, "ka": 1.2}, None),
    ("iv_bolus", 2, {"CL": 5.0, "Vc": 12.0, "Q": 7.0, "Vp": 25.0}, None),
    ("iv_infusion", 2, {"CL": 5.0, "Vc": 12.0, "Q": 7.0, "Vp": 25.0}, 2.0),
    ("oral", 2, {"CL/F": 5.0, "V/F": 12.0, "Q/F": 7.0, "Vp/F": 25.0, "ka": 1.2}, None),
])
def test_fit_recovers_synthetic_models(route, compartments, parameters, duration):
    cfg = PKSettings(route=route, dose=100, infusion_duration_h=duration)
    times = np.r_[0, .1, .2, .4, .7, 1, 1.5, 2, 3, 4, 6, 8, 12, 16, 24, 36, 48]
    values = predict(times, parameters, cfg, compartments)
    fit = fit_compartment(profile(times, values), cfg, compartments=compartments, starts=12)
    assert fit["converged"]
    assert fit["rmse_ng_ml"] < 1e-3 * max(values)
    assert fit["aicc"] is not None
    for name, expected in parameters.items():
        assert fit["parameters"][name] == pytest.approx(expected, rel=.06)


@pytest.mark.parametrize("route,duration", [
    ("iv_bolus", None), ("iv_infusion", 1.5), ("oral", None),
])
def test_three_compartment_predictions_match_independent_matrix_solution(route, duration):
    """A separate amount-space matrix exponential validates all three routes."""
    params = {"CL": 5.0, "Vc": 12.0, "Q2": 8.0, "Vp2": 17.0,
              "Q3": 2.5, "Vp3": 80.0}
    if route == "oral":
        params = {"CL/F": params["CL"], "V/F": params["Vc"],
                  "Q2/F": params["Q2"], "Vp2/F": params["Vp2"],
                  "Q3/F": params["Q3"], "Vp3/F": params["Vp3"], "ka": 1.3}
    cfg = PKSettings(route=route, dose=100, infusion_duration_h=duration)
    k10, k12, k21, k13, k31 = 5 / 12, 8 / 12, 8 / 17, 2.5 / 12, 2.5 / 80
    amount_matrix = np.array([
        [-(k10 + k12 + k13), k21, k31],
        [k12, -k21, 0],
        [k13, 0, -k31],
    ])
    times = np.array([0, .03, .25, 1, 1.5, 2.7, 8, 30, 100])
    expected = []
    for time in times:
        if route == "iv_bolus":
            central_amount = (expm(amount_matrix * time) @ np.array([100., 0, 0]))[0]
        elif route == "iv_infusion":
            augmented = np.zeros((4, 4))
            augmented[:3, :3] = amount_matrix
            augmented[0, 3] = 100 / duration
            infusion_state = (expm(augmented * min(time, duration))
                              @ np.array([0., 0, 0, 1]))[:3]
            central_amount = (expm(amount_matrix * max(0, time - duration))
                              @ infusion_state)[0]
        else:
            oral_matrix = np.zeros((4, 4))
            oral_matrix[:3, :3] = amount_matrix
            oral_matrix[0, 3] = params["ka"]
            oral_matrix[3, 3] = -params["ka"]
            central_amount = (expm(oral_matrix * time)
                              @ np.array([0., 0, 0, 100.]))[0]
        expected.append(central_amount / 12 * 1000)  # mg/L -> ng/mL
    np.testing.assert_allclose(predict(times, params, cfg, 3), expected,
                               rtol=1e-10, atol=1e-8)


@pytest.mark.parametrize("route,duration", [
    ("iv_bolus", None), ("iv_infusion", 1.5), ("oral", None),
])
def test_three_compartment_fit_recovers_parameters_and_derived_quantities(route, duration):
    iv_params = {"CL": 5., "Vc": 12., "Q2": 8., "Vp2": 17., "Q3": 2.5, "Vp3": 80.}
    params = iv_params if route != "oral" else {
        "CL/F": 5., "V/F": 12., "Q2/F": 8., "Vp2/F": 17.,
        "Q3/F": 2.5, "Vp3/F": 80., "ka": 1.3,
    }
    cfg = PKSettings(route=route, dose=100, infusion_duration_h=duration)
    times = np.geomspace(.05, 150, 30)  # No fictitious t=0 IV concentration.
    values = predict(times, params, cfg, 3)
    fitted = fit_compartment(profile(times, values), cfg, compartments=3, starts=16)
    assert fitted["converged"]
    assert fitted["n"] == 30
    assert fitted["p"] == len(params)
    assert fitted["rmse_ng_ml"] < 1e-3
    assert fitted["aicc"] is not None
    for name, target in params.items():
        assert fitted["parameters"][name] == pytest.approx(target, rel=.04)
    derived = fitted["derived_parameters"]
    assert derived["Vss/F (L)" if route == "oral" else "Vss (L)"] == pytest.approx(109.)
    assert derived["k10 (1/giờ)"] == pytest.approx(5 / 12, rel=.04)
    assert derived["k21 (1/giờ)"] > derived["k31 (1/giờ)"]
    assert derived["α (1/giờ)"] > derived["β (1/giờ)"] > derived["γ (1/giờ)"] > 0
    assert derived["t½,γ (giờ)"] > derived["t½,β (giờ)"] > derived["t½,α (giờ)"]
    if route == "oral":
        assert any("biểu kiến" in warning for warning in fitted["warnings"])


def test_three_compartment_derived_parameters_are_exported():
    params = {"CL": 5., "Vc": 12., "Q2": 8., "Vp2": 17., "Q3": 2.5, "Vp3": 80.}
    cfg = PKSettings(route="iv_bolus", dose=100.)
    times = np.geomspace(.05, 150, 30)
    frame = profile(times, predict(times, params, cfg, 3))
    fitted = fit_compartment(frame, cfg, compartments=3)
    snapshot = create_snapshot(frame, asdict(cfg), [], [fitted], [], "Kiểm thử mô hình 3 ngăn")
    cols = pd.read_excel(io.BytesIO(excel_report(snapshot)), sheet_name="Mo_hinh").columns
    assert "Vss (L)" in cols
    assert "k21 (1/giờ)" in cols
    assert "t½,γ (giờ)" in cols
    with zipfile.ZipFile(io.BytesIO(word_report(snapshot))) as archive:
        document_xml = archive.read("word/document.xml").decode("utf-8")
        assert "Vss (L)" in document_xml
    assert pdf_report(snapshot).startswith(b"%PDF")


def test_blq_is_excluded_from_fit_not_treated_as_measured_zero():
    cfg = PKSettings(route="iv_bolus", dose=100)
    t = np.arange(0, 14, 1)
    data = profile(t, predict(t, {"CL": 5, "Vc": 20}, cfg, 1))
    data.loc[data.index[-2:], "blq"] = True
    data.loc[data.index[-2:], "concentration"] = 0.0
    fit = fit_compartment(data, cfg)
    assert fit["n"] == len(t) - 2
    assert fit["parameters"]["CL"] == pytest.approx(5, rel=.001)


def test_save_integrity_and_exports(tmp_path):
    cfg = PKSettings(route="iv_bolus", dose=100)
    t = np.arange(0, 20, 1)
    frame = profile(t, predict(t, {"CL": 5, "Vc": 20}, cfg, 1))
    snapshot = create_snapshot(frame, asdict(cfg), [analyze_nca(frame, cfg)],
                               [fit_compartment(frame, cfg)], [], "Ví dụ kiểm thử & <QC>")
    assert json.loads(record_bytes(snapshot))["schema_version"] == 1
    store = PKRecordStore(tmp_path / "pk.sqlite")
    run_id = store.save(snapshot)
    assert len(store.list_runs()) == 1
    assert store.load(run_id) == snapshot
    xlsx = excel_report(snapshot)
    with zipfile.ZipFile(io.BytesIO(xlsx)) as archive:
        assert "xl/workbook.xml" in archive.namelist()
    nca_columns = pd.read_excel(io.BytesIO(xlsx), sheet_name="NCA").columns
    assert "Mã hồ sơ" in nca_columns
    assert "AUC0–∞ (ng·giờ/mL)" in nca_columns
    with zipfile.ZipFile(io.BytesIO(word_report(snapshot))) as archive:
        assert "word/document.xml" in archive.namelist()
    assert pdf_report(snapshot).startswith(b"%PDF")
    import sqlite3
    with sqlite3.connect(store.path) as con:
        con.execute("UPDATE pk_runs SET content=? WHERE run_id=?", ("{}", run_id))
    with pytest.raises(ValueError, match="SHA-256"):
        store.load(run_id)


def test_pk_ui_tabular_renders_without_missing_helpers():
    from be_app.pk_ui import _tabular

    cfg = PKSettings(route="iv_bolus", dose=100)
    t = np.arange(0, 20, 1)
    frame = profile(t, predict(t, {"CL": 5, "Vc": 20}, cfg, 1))
    snapshot = create_snapshot(frame, asdict(cfg), [analyze_nca(frame, cfg)],
                               [fit_compartment(frame, cfg)], [], "Test snapshot")
    _tabular(snapshot)

