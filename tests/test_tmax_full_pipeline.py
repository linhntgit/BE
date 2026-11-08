"""The supportive Tmax result must be traceable without changing BE decisions."""

import io
from dataclasses import asdict

import pandas as pd
import pytest

import be_app.pipeline as pipeline
from be_app.domain import digest
from be_app.examples import demo_project
from be_app.quick_be import TmaxComparison, compare_tmax
from be_app.report_tables import report_tables
from be_app.reporting import analysis_exports


@pytest.mark.parametrize("design", ["2x2", "parallel"])
def test_full_be_tmax_snapshot_and_export(design):
    project = pipeline.run_analysis(demo_project(design=design, n=24).freeze())
    run = project.runs[-1]
    tmax = run["tmax_comparison"]

    assert tmax == asdict(compare_tmax(pd.DataFrame(run["nca"]), design))
    assert tmax["status"] == "EVALUABLE"
    assert 0 <= tmax["p_value"] <= 1
    assert tmax["method"].startswith("Wilcoxon" if design == "2x2" else "Mann")
    if design == "2x2":
        assert tmax["n_pairs"] == 24
    else:
        assert tmax["n_pairs"] is None
    assert run["snapshot_hash"] == digest({k: v for k, v in run.items() if k != "snapshot_hash"})
    assert run["study_decision"] == "NOT EVALUABLE"  # synthetic QA never study PASS

    workbook = pd.ExcelFile(io.BytesIO(analysis_exports(project)["be.xlsx"]))
    assert "Tmax Nonparametric" in workbook.sheet_names
    row = pd.read_excel(workbook, sheet_name="Tmax Nonparametric").iloc[0]
    assert row["Status"] == tmax["status"]
    assert row["P_two_sided"] == pytest.approx(tmax["p_value"])
    assert row["Median_T_h"] == pytest.approx(tmax["median_t"])

    for language in ("vi", "en"):
        specs = report_tables(run, language)
        matching = [s for s in specs if "Tmax" in s["title"]]
        assert len(matching) == 1
        assert len(matching[0]["rows"]) == 2
        assert "80–125%" in matching[0]["note"]


def test_tmax_statistic_cannot_change_abe_or_study_decision(monkeypatch):
    frozen = demo_project(n=24).freeze()
    baseline = pipeline.run_analysis(frozen).runs[-1]
    monkeypatch.setattr(
        pipeline, "compare_tmax",
        lambda *args: TmaxComparison(status="NOT EVALUABLE", reason="SAP missing"),
    )
    changed = pipeline.run_analysis(frozen).runs[-1]

    assert changed["tmax_comparison"]["status"] == "NOT EVALUABLE"
    assert changed["be"] == baseline["be"]
    assert changed["study_decision"] == baseline["study_decision"]


def test_non_evaluable_nca_profile_blocks_tmax_instead_of_silent_exclusion(monkeypatch):
    real_run_nca = pipeline.run_nca

    def one_invalid_profile(snapshot, cache):
        rows, computation = real_run_nca(snapshot, cache)
        rows = [dict(row) for row in rows]
        rows[0]["status"] = "NOT EVALUABLE"
        return rows, computation

    monkeypatch.setattr(pipeline, "run_nca", one_invalid_profile)
    run = pipeline.run_analysis(demo_project(n=12).freeze()).runs[-1]
    tmax = run["tmax_comparison"]

    assert tmax["status"] == "NOT EVALUABLE"
    assert "không tự loại" in tmax["reason"]
    assert tmax["p_value"] is None


def test_legacy_snapshot_report_does_not_recalculate_tmax():
    run = pipeline.run_analysis(demo_project(n=12).freeze()).runs[-1]
    legacy_run = {k: v for k, v in run.items() if k != "tmax_comparison"}
    table = next(spec for spec in report_tables(legacy_run, "en") if "Tmax" in spec["title"])
    assert "does not recompute" in table["note"]
    assert table["rows"] == [["—"] * 7]


@pytest.mark.parametrize("invalid_column, invalid_value", [
    ("treatment", "UNKNOWN"),
    ("subject_id", None),
])
def test_tmax_rejects_invalid_subject_or_treatment_without_excluding_rows(
    invalid_column, invalid_value,
):
    rows = pipeline.run_analysis(demo_project(n=12).freeze()).runs[-1]["nca"]
    endpoints = pd.DataFrame(rows)
    endpoints.loc[0, invalid_column] = invalid_value

    tmax = compare_tmax(endpoints, "2x2")

    assert tmax.status == "NOT EVALUABLE"
    assert tmax.p_value is None
    assert tmax.reason
