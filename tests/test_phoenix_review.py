"""Reviewer output must reflect the actual estimator, population and decision gates."""

import io

import numpy as np
import openpyxl
import pandas as pd
import pytest
import statsmodels.formula.api as smf

from be_app.be_reporting import be_tables, be_workbook
from be_app.domain import BeConfig
from be_app.examples import statistical_demo
from be_app.replicate import analyze_regulatory_be
from be_app.review import (
    criterion_figures,
    decision_review,
    forest_figure,
    population_matrix,
    reviewer_tables,
)
from tests.test_be_extended import full_replicate_case, study_for


def test_forest_uses_endpoint_limits_and_fda_separate_criteria():
    data = statistical_demo("full4")
    study = study_for("EMA_HVDP_ABEL", "full4")
    results = [analyze_regulatory_be(data, name, study) for name in ("cmax", "auc_last")]
    figure = forest_figure(results)
    bands = [shape for shape in figure.layout.shapes if shape.type == "rect"]
    assert bands[0].x0 == pytest.approx(100 * results[0].lower_limit)
    assert bands[0].x0 < 80
    assert (bands[1].x0, bands[1].x1) == (80, 125)
    narrow = analyze_regulatory_be(data, "auc_last", study_for("EMA_NTI", "full4"))
    band = [shape for shape in forest_figure([narrow]).layout.shapes if shape.type == "rect"][0]
    assert (band.x0, band.x1) == pytest.approx((90, 111.11))
    nti = analyze_regulatory_be(full_replicate_case(), "cmax", study_for("FDA_NTI", "full4"))
    assert len(criterion_figures([nti])) == 2
    assert criterion_figures([nti])[1].layout.shapes[0].x0 == 2.5
    diagnostics = be_tables([nti])["Residual Diagnostics"]
    assert diagnostics.Units.eq("natural-log model scale").all()
    assert diagnostics.Source_PK_Units.eq("ng/mL").all()


def test_missing_replicate_shows_expected_cell_and_no_fabricated_used_population():
    d = full_replicate_case().iloc[1:].copy()
    r = analyze_regulatory_be(d, "cmax", study_for("FDA_NTI", "full4"))
    tables = reviewer_tables([r], data=d, design="full4")
    matrix = tables["Population Matrix"]
    assert len(matrix) == 48  # Includes the absent cell.
    assert (matrix.Cell_status == "Missing period").sum() == 1
    assert not matrix.Model_used.any() and not matrix.R_variance_used.any()
    counts = tables["Population Counts"].iloc[0]
    assert counts.Complete_subjects == 11 and counts.Input_subjects == 12
    assert counts.Model_subjects == 0


def test_population_treatment_variance_and_missing_endpoint_are_separate():
    d = full_replicate_case()
    d["auc_last"] = d.cmax
    d.loc[0, "auc_last"] = np.nan
    results = [analyze_regulatory_be(d, e, study_for("FDA_NTI", "full4")) for e in ("cmax", "auc_last")]
    tables = reviewer_tables(results, data=d, design="full4")
    counts = tables["Population Counts"].set_index("Endpoint")
    assert counts.loc["cmax", "Model_observations"] == 48
    assert counts.loc["cmax", "R_variance_observations"] == 24
    assert counts.loc["cmax", "T_variance_observations"] == 24
    assert counts.loc["auc_last", "Model_observations"] == 0
    assert results[1].decision == "NOT EVALUABLE"


def test_available_observation_mixed_population_matches_fitted_observations():
    d = statistical_demo("2x2")
    d.loc[0, "cmax"] = np.nan
    cfg = BeConfig(
        missing_policy="available_observations", missing_data_reason="SAP-defined missing data approach"
    )
    r = analyze_regulatory_be(d, "cmax", study_for("FDA_ABE_2026", "2x2"), cfg)
    matrix = population_matrix(d, [r], "2x2")
    assert r.estimate is not None
    assert matrix.Model_used.sum() == r.n_observations == len(d) - 1
    assert not matrix.R_variance_used.any()  # Pooled 2x2 CV is not sWR.


@pytest.mark.parametrize("design", ["partial3", "full4"])
def test_reference_only_studentization_against_statsmodels(design):
    d = statistical_demo(design)
    d["log_pk"] = np.log(d.cmax)
    oracle = smf.ols("log_pk ~ C(subject_id) + C(period)", d.loc[d.treatment.eq("R")]).fit()
    r = analyze_regulatory_be(d, "cmax", study_for("EMA_HVDP_ABEL", design))
    diagnostics = be_tables([r])["Residual Diagnostics"]
    reference = diagnostics.loc[diagnostics.Model.eq("EMA reference-only (R)")]
    assert reference.treatment.eq("R").all()
    assert reference.Studentized_internal.to_numpy() == pytest.approx(
        oracle.get_influence().resid_studentized_internal, abs=2e-9
    )
    assert reference.Leverage.to_numpy() == pytest.approx(oracle.get_influence().hat_matrix_diag, abs=2e-9)
    assert not reference.Review_flag.any()


def test_criterion_pass_is_not_endpoint_pass_when_scope_blocks():
    study = study_for("EMA_HVDP_ABEL", "full4").model_copy(update={"scaled_be_prespecified": False})
    result = analyze_regulatory_be(full_replicate_case(swr=0.4), "cmax", study)
    table = decision_review([result])
    assert table.Criterion_result.eq("PASS").all()
    assert table.Endpoint_result.eq("NOT EVALUABLE").all()
    assert table.Reason.str.contains("định trước").all()


def test_reviewer_workbook_preserves_ids_population_and_fda_fit_labels():
    d = full_replicate_case()
    result = analyze_regulatory_be(d, "cmax", study_for("FDA_NTI", "full4"))
    tables = be_tables([result], data=d)
    assert set(tables["Residual Diagnostics"].Model) == {
        "FDA I ~ sequence",
        "FDA D_R ~ sequence",
        "FDA D_T ~ sequence",
    }
    assert tables["Residuals"].Model.str.contains("supplementary").all()
    workbook = openpyxl.load_workbook(io.BytesIO(be_workbook([result], data=d)))
    for sheet in (
        "Reviewer Criteria",
        "Population Matrix",
        "Population Counts",
        "PK Descriptive",
        "Residual Diagnostics",
    ):
        assert sheet in workbook.sheetnames and workbook[sheet].max_row > 1
    assert tables["PK Descriptive"].N_subjects.sum() == 24
    assert tables["PK Descriptive"].N_observations.sum() == 48
    assert not any(cell.data_type == "f" for sheet in workbook for row in sheet for cell in row)


def test_invalid_population_duplicate_is_visible_and_not_dropped():
    d = full_replicate_case()
    d = pd.concat([d, d.iloc[:1]], ignore_index=True)
    result = analyze_regulatory_be(d, "cmax", study_for("FDA_NTI", "full4"))
    matrix = population_matrix(d, [result], "full4")
    assert (matrix.Cell_status == "Duplicate period").sum() == 1
    assert not matrix.Model_used.any()
