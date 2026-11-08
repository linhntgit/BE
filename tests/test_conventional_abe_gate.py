"""An I-contrast CI must never be accepted as conventional replicate mixed ABE."""

import io

import openpyxl
import pytest

from be_app.be_reporting import be_tables, be_workbook
from be_app.replicate import analyze_regulatory_be
from be_app.review import decision_review, forest_figure
from be_app.state import result_status
from tests.test_be_extended import full_replicate_case, study_for


@pytest.mark.parametrize("rule", ["FDA_REPLICATE_STANDARD", "FDA_NTI", "FDA_HVD_RSABE_2026"])
def test_conventional_replicate_branches_never_release_i_contrast_abe(rule):
    data = full_replicate_case(swr=0.10)
    result = analyze_regulatory_be(data, "cmax", study_for(rule, "full4"))
    assert result.decision == "NOT EVALUABLE"
    assert "mixed" in result.reason and "I contrasts" in result.reason
    assert result.estimate is not None and result.se is not None and result.df is not None
    assert result.criteria[0]["passed"] is None and result.criteria[0]["value"] is None
    assert result.diagnostics["conventional_abe_ci90"] is None
    assert result.diagnostics["i_contrast_ci90"] == [result.ci_lower, result.ci_upper]
    assert not result.diagnostics["conventional_abe_qualified"]
    review = decision_review([result])
    assert review.iloc[0].Criterion_result == "NOT EVALUABLE"
    assert review.Endpoint_result.eq("NOT EVALUABLE").all()
    figures = forest_figure([result])
    assert figures.layout.shapes[0].fillcolor == "#eeeeee"
    tables = be_tables([result], data=data)
    assert tables["Average Bioequivalence"].iloc[0].Decision == "NOT EVALUABLE"
    workbook = openpyxl.load_workbook(io.BytesIO(be_workbook([result], data=data)))
    assert any("not qualified" in str(c.value) for row in workbook["Reviewer Criteria"] for c in row)


def test_scaled_hvd_and_ema_methods_keep_their_actual_decision_criteria():
    high = analyze_regulatory_be(full_replicate_case(swr=0.4), "cmax", study_for("FDA_HVD_RSABE_2026", "full4"))
    assert high.decision == "PASS"
    assert [c["passed"] for c in high.criteria] == [True, True]
    assert high.scaled_ucb is not None
    assert high.diagnostics["conventional_abe_ci90"] is None
    assert high.diagnostics["i_contrast_ci90"] == [high.ci_lower, high.ci_upper]
    ema = analyze_regulatory_be(full_replicate_case(), "cmax", study_for("EMA_REPLICATE_STANDARD", "full4"))
    assert ema.decision == "PASS" and ema.criteria[0]["passed"]


def test_previous_engine_snapshot_becomes_legacy_without_mutating_it(demo):
    from be_app import __version__
    from be_app.pipeline import run_analysis

    project = run_analysis(demo.freeze())
    current = project.runs[-1]
    assert current["engine_version"] == __version__ == "0.3.1"
    assert result_status(project, current) == "CURRENT"
    previous = {**current, "engine_version": "0.3.0"}
    assert result_status(project, previous) != "CURRENT"
    assert previous["engine_version"] == "0.3.0" and current["engine_version"] == "0.3.1"
