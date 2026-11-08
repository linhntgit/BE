"""Regression against user-supplied Phoenix estimates, not values from our engine."""

import io
import json
import math
from dataclasses import replace
from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from tests.conftest import open_be_page
from be_app.domain import NcaConfig
from be_app.nca import analyze_profile, cumulative_areas
from be_app.nca_reporting import nca_workbook as independent_nca_workbook
from tests.legacy_benchmarks.phoenix_nca import PhoenixReference, analyze_reference, nca_workbook, phoenix_config, read_phoenix_reference
from be_app.snapshots import InputSnapshot, run_nca
from be_app.state import result_status
from tests.conftest import FIXTURES


@pytest.fixture(scope="module")
def phoenix_reference():
    fixture = json.loads((FIXTURES / "phoenix_nca_fasted.json").read_text(encoding="utf-8"))
    tables = fixture["tables"]
    data = pd.DataFrame(tables["Summary Table"][2:], columns=tables["Summary Table"][0])
    expected = pd.DataFrame(tables["Final Parameters"][1:], columns=tables["Final Parameters"][0])
    dosing = tables["Dosing Used"]
    doses = {(r[0], r[1]): float(r[3]) for r in dosing[2:]}
    return PhoenixReference(
        data, expected, doses, "mg", phoenix_config(), {"source_sha256": fixture["sha256"]}
    )


def test_all_1968_phoenix_parameters(phoenix_reference):
    results, comparison = analyze_reference(phoenix_reference)
    assert len(results) == 48
    assert len(comparison) == 1968
    assert comparison.Match.all(), comparison[~comparison.Match].to_string()
    assert comparison["Both missing"].sum() == 468
    assert sum(r["lambda_z"] is None for r in results) == 18
    assert sum(r["n_samples"] for r in results) == 720
    assert comparison["Abs difference"].max() < 4e-10


def test_all_sample_diagnostics_against_phoenix(phoenix_reference):
    results, _ = analyze_reference(phoenix_reference)
    for result in results:
        source = phoenix_reference.data
        profile = source[(source.Subject == result["subject_id"]) & (source.Treatment == result["treatment"])]
        for actual, expected in zip(result["profile_points"], profile.to_dict("records"), strict=True):
            assert actual["terminal"] == (expected["lambda_z_Incl"] == "*")
            for key, column in (
                ("auc", "AUC"),
                ("aumc", "AUMC"),
                ("predicted", "Predicted"),
                ("residual", "Residual"),
            ):
                if pd.isna(expected[column]):
                    assert actual[key] is None
                else:
                    assert actual[key] == pytest.approx(expected[column], rel=1e-9, abs=1e-8)


def test_estimates_cannot_feed_calculations_and_missing_rows_fail(phoenix_reference):
    original, _ = analyze_reference(phoenix_reference)
    changed = phoenix_reference.expected.copy()
    changed["Estimate"] = 99999.0
    recomputed, comparison = analyze_reference(replace(phoenix_reference, expected=changed))
    assert recomputed == original
    assert not comparison.Match.any()
    _, omitted = analyze_reference(replace(phoenix_reference, expected=phoenix_reference.expected.iloc[1:]))
    assert len(omitted) == 1968 and omitted.Match.sum() == 1967


def test_linear_and_log_first_moment():
    assert cumulative_areas([0, 1, 2], [0, 4, 2], "linear") == ([0, 2, 5], [0, 2, 6])
    # C(t)=exp(-k*t), integral t*C(t) has a closed form.
    for k in (0.5, 1e-6, 1e-10):
        times = np.array([0.0, 1.0, 2.0])
        _, moment = cumulative_areas(times, np.exp(-k * times))
        expected = sum((-k) ** j * 2 ** (j + 2) / (math.factorial(j) * (j + 2)) for j in range(30))
        assert moment[-1] == pytest.approx(expected, rel=1e-10)


def test_mass_units_and_terminal_failure(exponential_profile):
    mg = analyze_profile(exponential_profile, dose=50)
    ug = analyze_profile(exponential_profile, dose=50000, dose_unit="ug")
    assert mg["cl_f"] == ug["cl_f"] == pytest.approx(50e6 / mg["auc_inf"])
    assert mg["vz_f"] == pytest.approx(mg["cl_f"] / mg["lambda_z"])
    missing = analyze_profile(exponential_profile.iloc[:4], dose=50)
    assert missing["auc_all"] is not None
    assert missing["clast_pred"] is missing["auc_inf_pred"] is missing["cl_f"] is None
    unknown_unit = analyze_profile(exponential_profile, dose=50, dose_unit="tablet")
    assert unknown_unit["cl_f"] is None
    assert unknown_unit["warnings"]


def test_constant_terminal_does_not_serialize_nan(exponential_profile):
    from be_app.domain import canonical

    exponential_profile.loc[2:, "concentration"] = 8
    result = analyze_profile(exponential_profile)
    assert result["lambda_z"] is None
    canonical(result)


def test_old_engine_requires_reanalysis(demo):
    from be_app.pipeline import run_analysis

    analyzed = run_analysis(demo.freeze())
    old = {**analyzed.runs[-1], "engine_version": "0.1.0"}
    assert result_status(analyzed, old) == "LEGACY"


def test_cache_includes_dose(demo):
    data = demo.qc().data.to_json(orient="records").encode()
    snapshot = InputSnapshot(demo.project_id, 0, 0, 0, "test", data, demo.study, NcaConfig(), demo.be_config)
    cache = {}
    first, _ = run_nca(snapshot, cache)
    second, stats = run_nca(
        replace(snapshot, study=demo.study.model_copy(update={"dose": 2 * demo.study.dose})), cache
    )
    assert stats["nca_profiles_reused"] == 0
    assert second[0]["dose"] == 2 * first[0]["dose"]
    assert second[0]["auc_last"] == first[0]["auc_last"]


def test_excel_snapshot_layout_and_numeric_roundtrip(phoenix_reference):
    results, comparison = analyze_reference(phoenix_reference)
    independent_book = openpyxl.load_workbook(io.BytesIO(independent_nca_workbook(results)))
    assert "Final Parameters" in independent_book.sheetnames
    assert "Settings" in independent_book.sheetnames
    assert not any("Phoenix" in name for name in independent_book.sheetnames)
    encoded = nca_workbook(results, comparison=comparison)
    book = openpyxl.load_workbook(io.BytesIO(encoded), data_only=False)
    wide = book["Final Parameters Pivoted"]
    assert wide.max_row == 50 and wide.max_column == 45
    assert wide["D2"].value == "mg" and wide["D3"].value == 50
    assert wide["I3"].value is None  # Missing lambda-z stays blank.
    assert book["Final Parameters"].max_row == 1969
    assert book["Summary Table"].max_row == 722
    assert book["Phoenix Comparison"].max_row == 1969
    assert not any(c.data_type == "f" for sheet in book for row in sheet for c in row)
    actual = pd.read_excel(io.BytesIO(encoded), sheet_name="Final Parameters", keep_default_na=False)
    assert actual.loc[actual.Parameter == "Cmax", "Estimate"].iloc[0] == results[0]["cmax"]


def test_reference_parser_on_supplied_workbook(phoenix_reference):
    source = Path(__file__).resolve().parents[1] / "NCA_Fasted.xlsx"
    if not source.exists():
        pytest.skip("Original workbook is local; portable golden fixture is tested separately.")
    parsed = read_phoenix_reference(source.read_bytes(), source.name)
    assert parsed.provenance["source_sha256"] == phoenix_reference.provenance["source_sha256"]
    assert len(parsed.data) == 720
    _, comparison = analyze_reference(parsed)
    assert comparison.Match.all()


def test_independent_nca_ui_without_vendor_controls(tmp_path, monkeypatch):
    import be_app.ui as ui
    from be_app.persistence import ProjectStore

    monkeypatch.setattr(ui, "store", lambda: ProjectStore(tmp_path / "phoenix-ui.sqlite"))
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=60).run()
    open_be_page(app, ui.PAGES[5])
    assert not any("Phoenix" in b.label for b in app.button)
    assert not any("Phoenix" in e.label for e in app.get("expander"))
    open_be_page(app, ui.PAGES[0])
    from tests.conftest import create_demo_study
    create_demo_study(app)
    open_be_page(app, ui.PAGES[5])
    # Independent NCA thresholds remain editable before Data Freeze.
    next(n for n in app.number_input if n.label == "Adjusted R² tối thiểu terminal theo SAP").set_value(
        0.95
    ).run()
    assert not any("Phoenix" in b.label for b in app.button)
    assert any(n.label == "Adjusted R² tối thiểu terminal theo SAP" and n.value == 0.95
               for n in app.number_input)
    assert not app.exception and not app.error
