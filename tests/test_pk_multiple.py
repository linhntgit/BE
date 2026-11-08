"""Repeated-dose numerical PK benchmarks and persistent Vietnamese reports."""

import io
import math
from dataclasses import asdict

import numpy as np
import pandas as pd
import pytest

from be_app.pk_analysis import PKSettings, read_concentrations
from be_app.pk_models import fit_compartment, predict
from be_app.pk_multiple import PKRegimen, analyze_interval_nca, predict_multiple
from be_app.pk_records import PKRecordStore, create_snapshot, excel_report, pdf_report, word_report


def profile(t, c, blq=None):
    return pd.DataFrame({"profile_id": ["MD01"] * len(t), "time_h": t,
                         "concentration": c,
                         "blq": list(blq) if blq is not None else [False] * len(t)})


def test_steady_state_iv_bolus_one_compartment_exact_benchmarks():
    cfg = PKSettings(route="iv_bolus", dose=100)
    reg = PKRegimen(mode="steady_state", tau_h=12, number_doses=20,
                    steady_state_confirmed=True)
    t = np.arange(0, 12.00001, .05)
    y = predict_multiple(reg.absolute_times(t), {"CL": 5, "Vc": 20}, cfg, 1, reg)
    k = 5 / 20
    peak = 5000 / (1 - math.exp(-k * 12))
    assert y[0] == pytest.approx(peak, rel=1e-12)
    assert y[-1] == pytest.approx(peak * math.exp(-k * 12), rel=1e-12)
    res = analyze_interval_nca(profile(t, y), cfg, reg)
    assert res["auc_tau_ng_h_ml"] == pytest.approx(20_000, rel=1e-12)
    assert res["cl_ss_l_h"] == pytest.approx(5, rel=1e-12)
    assert res["cavg_tau_ng_ml"] == pytest.approx(20_000 / 12, rel=1e-12)
    assert res["cmax_tau_ng_ml"] == pytest.approx(peak, rel=1e-12)
    assert res["ctrough_ng_ml"] == pytest.approx(y[-1])


@pytest.mark.parametrize("route,compartments,params,duration", [
    ("oral", 1, {"CL/F": 5, "V/F": 25, "ka": 1.3}, None),
    ("iv_infusion", 1, {"CL": 5, "Vc": 25}, 2.0),
    ("iv_bolus", 2, {"CL": 5, "Vc": 15, "Q": 6, "Vp": 30}, None),
    ("iv_infusion", 2, {"CL": 5, "Vc": 15, "Q": 6, "Vp": 30}, 2.0),
    ("oral", 2, {"CL/F": 5, "V/F": 15, "Q/F": 6, "Vp/F": 30, "ka": 1.3}, None),
])
def test_superposition_matches_sum_of_single_doses(route, compartments, params, duration):
    cfg = PKSettings(route=route, dose=100, infusion_duration_h=duration)
    reg = PKRegimen(tau_h=8, number_doses=5, time_basis="first_dose")
    times = np.array([0, .1, 7.9, 8, 8.01, 14.0, 32, 40.0])
    expected = np.zeros_like(times)
    for offset in range(5):
        selected = times >= 8 * offset
        expected[selected] += predict(times[selected] - 8 * offset, params, cfg, compartments)
    assert predict_multiple(times, params, cfg, compartments, reg) == pytest.approx(expected)


@pytest.mark.parametrize("route,params,duration", [
    ("oral", {"CL/F": 5, "V/F": 20, "ka": 1.1}, None),
    ("iv_infusion", {"CL": 5, "Vc": 20}, 2.0),
    ("iv_bolus", {"CL": 5, "Vc": 20}, None),
])
def test_repeated_dose_fit_recovers_parameters(route, params, duration):
    cfg = PKSettings(route=route, dose=100, infusion_duration_h=duration)
    reg = PKRegimen(tau_h=12, number_doses=10)
    times = np.linspace(0, 12, 45)
    values = predict_multiple(reg.absolute_times(times), params, cfg, 1, reg)
    result = fit_compartment(profile(times, values), cfg, compartments=1, starts=10, regimen=reg)
    assert result["converged"]
    assert result["rmse_ng_ml"] < 1e-3
    for key, value in params.items():
        assert result["parameters"][key] == pytest.approx(value, rel=.01)
    assert result["time_h"][0] == 0.0


def test_unconfirmed_ss_and_multiple_do_not_calculate_steady_clearance():
    cfg = PKSettings(route="oral", dose=100)
    times = np.linspace(0, 12, 61)
    for mode, confirmed in [("multiple", False), ("steady_state", False), ("steady_state", True)]:
        regimen = PKRegimen(mode=mode, tau_h=12, number_doses=10,
                            steady_state_confirmed=confirmed)
        y = predict_multiple(regimen.absolute_times(times),
                             {"CL/F": 5, "V/F": 20, "ka": 1.2}, cfg, 1, regimen)
        res = analyze_interval_nca(profile(times, y), cfg, regimen)
        assert res["auc_tau_ng_h_ml"] is not None
        assert res["cl_ss_l_h"] is None
        assert (res["cl_over_f_ss_l_h"] is not None) == confirmed


def test_observed_interval_nca_without_known_dose():
    modeled = PKSettings(route="oral", dose=100)
    unknown = PKSettings(route="oral", dose=None)
    reg = PKRegimen(mode="steady_state", tau_h=12, number_doses=10,
                    steady_state_confirmed=True)
    t = np.linspace(0, 12, 61)
    y = predict_multiple(reg.absolute_times(t),
                         {"CL/F": 5, "V/F": 20, "ka": 1.2}, modeled, 1, reg)
    res = analyze_interval_nca(profile(t, y), unknown, reg)
    assert res["auc_tau_ng_h_ml"] is not None
    assert res["cavg_tau_ng_ml"] is not None
    assert res["cl_over_f_ss_l_h"] is None
    with pytest.raises(ValueError, match="liều"):
        fit_compartment(profile(t, y), unknown, compartments=1, regimen=reg)


def test_missing_boundary_and_blq_do_not_silently_extrapolate():
    cfg = PKSettings(route="oral", dose=100)
    reg = PKRegimen(mode="steady_state", tau_h=12, number_doses=8,
                    steady_state_confirmed=True)
    t = np.linspace(0, 12, 49)
    y = predict_multiple(reg.absolute_times(t), {"CL/F": 5, "V/F": 20, "ka": 1}, cfg, 1, reg)
    for data in [profile(t[1:], y[1:]), profile(t[:-1], y[:-1])]:
        res = analyze_interval_nca(data, cfg, reg)
        assert res["auc_tau_ng_h_ml"] is None
        assert res["cl_over_f_ss_l_h"] is None
    blq = [False] * len(t)
    blq[8] = True
    y[8] = 0
    res = analyze_interval_nca(profile(t, y, blq), cfg, reg)
    assert res["auc_tau_ng_h_ml"] is None


def test_first_cycle_accumulation_oral_when_both_cycles_are_measured():
    cfg = PKSettings(route="oral", dose=100)
    reg = PKRegimen(mode="steady_state", tau_h=12, number_doses=20,
                    time_basis="first_dose", steady_state_confirmed=True)
    t = np.r_[np.linspace(0, 12, 61), np.linspace(reg.last_dose_h, reg.last_dose_h + 12, 61)]
    y = predict_multiple(t, {"CL/F": 5, "V/F": 20, "ka": 1}, cfg, 1, reg)
    res = analyze_interval_nca(profile(t, y), cfg, reg)
    assert res["accumulation_ratio_auc"] is not None
    assert res["accumulation_ratio_auc"] > 1
    assert res["cl_over_f_ss_l_h"] == pytest.approx(5, rel=.002)


def test_regimen_validation_and_iv_bolus_boundary():
    cfg = PKSettings(route="iv_bolus", dose=100)
    for reg in [PKRegimen(tau_h=0), PKRegimen(number_doses=1),
                PKRegimen(time_basis="invalid"), PKRegimen(mode="multiple", steady_state_confirmed=True)]:
        with pytest.raises(ValueError):
            reg.validate(cfg)
    reg = PKRegimen(tau_h=12, number_doses=3, time_basis="first_dose")
    with pytest.raises(ValueError, match="ngoài lịch"):
        reg.absolute_times([36.01])
    doses = predict_multiple([12 - 1e-5, 12, 36], {"CL": 5, "Vc": 20}, cfg, 1, reg)
    assert doses[1] - doses[0] == pytest.approx(5000, rel=1e-5)
    assert doses[-1] < doses[1]


def test_multiple_snapshot_reports_and_v1_compatibility(tmp_path):
    cfg = PKSettings(route="iv_bolus", dose=100)
    reg = PKRegimen(mode="steady_state", tau_h=12, number_doses=12,
                    steady_state_confirmed=True)
    t = np.linspace(0, 12, 49)
    data = profile(t, predict_multiple(reg.absolute_times(t), {"CL": 5, "Vc": 20}, cfg, 1, reg))
    result = analyze_interval_nca(data, cfg, reg)
    snapshot = create_snapshot(data, asdict(cfg), [result], [], [], "Mô phỏng", asdict(reg))
    assert snapshot["schema_version"] == 2
    store = PKRecordStore(tmp_path / "repeated.sqlite")
    assert store.load(store.save(snapshot)) == snapshot
    report = pd.read_excel(io.BytesIO(excel_report(snapshot)), sheet_name="NCA")
    assert "AUCτ (ng·giờ/mL)" in report.columns
    assert "CLss (L/giờ)" in report.columns
    assert word_report(snapshot).startswith(b"PK")
    assert pdf_report(snapshot).startswith(b"%PDF")
    old = create_snapshot(data, asdict(cfg), [], [], [], "Đơn liều")
    assert old["schema_version"] == 1
    assert store.load(store.save(old)) == old


def test_vietnamese_multiple_dose_example_download_can_be_analyzed():
    from be_app.pk_ui import _demo_multiple_csv

    raw = pd.read_csv(io.BytesIO(_demo_multiple_csv()))
    assert set(raw.columns) == {"profile", "time_h", "Cplasma_ng_mL"}
    data = read_concentrations(raw, layout="long", time_column="time_h",
                               concentration_column="Cplasma_ng_mL", profile_column="profile")
    regimen = PKRegimen(mode="steady_state", tau_h=12, number_doses=10,
                        steady_state_confirmed=True)
    result = analyze_interval_nca(data, PKSettings(route="oral", dose=100), regimen)
    assert result["auc_tau_ng_h_ml"] is not None
    assert result["cl_over_f_ss_l_h"] == pytest.approx(5, rel=.002)
