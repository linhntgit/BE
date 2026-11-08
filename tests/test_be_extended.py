"""Phoenix numerical oracles and independent matrix checks for EMA/FDA branches."""

import io
import json
import math
from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd
import pytest
import statsmodels.formula.api as smf
from scipy.stats import chi2, f, t
from streamlit.testing.v1 import AppTest

from tests.conftest import open_be_page
from be_app.be_reporting import be_tables, be_workbook
from tests.legacy_benchmarks.phoenix_be import be_comparison_workbook, compare_phoenix_be, read_phoenix_be
from be_app.domain import BeConfig, Study, canonical
from be_app.examples import statistical_demo
from be_app.regulations import scope_blockers
from be_app.replicate import analyze_regulatory_be
from be_app.statistics import analyze_abe
from tests.conftest import FIXTURES


@pytest.fixture(scope="module")
def phoenix_be():
    fixture = json.loads((FIXTURES / "phoenix_be_fasted.json").read_text(encoding="utf-8"))
    tables = fixture["tables"]
    raw = pd.DataFrame(tables["Residuals"][1:], columns=tables["Residuals"][0])
    data = raw[raw.Dependent.eq("Ln(Cmax)")][["Subject", "Sequence", "Period", "Treatment"]].copy()
    keys = list(data.columns)
    for label, endpoint in (("Cmax", "cmax"), ("AUClast", "auc_last"), ("AUCINF_pred", "auc_inf_pred")):
        block = raw[raw.Dependent.eq(f"Ln({label})")][[*keys, "Ln_Observed"]].copy()
        block[endpoint] = np.exp(pd.to_numeric(block.Ln_Observed, errors="coerce"))
        data = data.merge(block.drop(columns="Ln_Observed"), on=keys, validate="one_to_one")
    data = data.rename(
        columns={
            "Subject": "subject_id",
            "Sequence": "sequence",
            "Period": "period",
            "Treatment": "treatment",
        }
    )
    data.subject_id = data.subject_id.map(str)
    expected = pd.DataFrame(tables["Average Bioequivalence"][1:], columns=tables["Average Bioequivalence"][0])
    return data, expected, tables


def test_78_phoenix_statistics_and_missing_observation_model(phoenix_be):
    data, expected, _ = phoenix_be
    results, checks = compare_phoenix_be(data, expected)
    assert len(checks) == 78 and checks.Match.all(), checks[~checks.Match].to_string()
    assert [r.decision for r in results] == ["FAIL", "PASS", "FAIL"]
    assert [r.n_observations for r in results] == [48, 48, 30]
    assert [r.n_excluded for r in results] == [0, 0, 18]
    assert results[2].n == 20
    assert results[2].df == pytest.approx(11.9728585641244, abs=2e-6)
    assert results[2].adjusted_geometric_mean_t != pytest.approx(results[2].geometric_mean_t, rel=0.001)
    assert checks["Abs difference"].max() < 0.00004
    canonical([r.model_dump(mode="json") for r in results])


def test_phoenix_anova_lsm_variance_and_residuals(phoenix_be):
    data, expected, source = phoenix_be
    results, _ = compare_phoenix_be(data, expected)
    actual = be_tables(results)
    for sheet, keys, columns in (
        ("Final Variance Parameters", ["Dependent", "Parameter"], ["Estimate"]),
        (
            "Least Squares Means",
            ["Dependent", "Level"],
            ["Estimate", "StdError", "Denom_DF", "Lower_CI", "Upper_CI"],
        ),
        (
            "LSM Differences",
            ["Dependent", "Level_Level"],
            ["Estimate", "StdError", "Denom_DF", "Lower_CI", "Upper_CI"],
        ),
        ("Final Fixed Parameters", ["Dependent", "Effect_Level"], ["Estimate", "StdError", "Denom_DF"]),
    ):
        golden = pd.DataFrame(source[sheet][1:], columns=source[sheet][0]).set_index(keys)
        computed = actual[sheet].set_index(keys)
        for key, row in computed.iterrows():
            for column in columns:
                assert row[column] == pytest.approx(float(golden.loc[key, column]), rel=1e-6, abs=5e-6)
    golden_ss = pd.DataFrame(source["Sequential SS"][1:], columns=source["Sequential SS"][0])
    for dependent in ("Ln(Cmax)", "Ln(AUClast)"):
        actual_ss = actual["Sequential SS"]
        a = actual_ss.loc[actual_ss.Dependent.eq(dependent)].set_index("Hypothesis")
        b = golden_ss.loc[golden_ss.Dependent.eq(dependent)].set_index("Hypothesis")
        for term in a.index:
            for col in ("DF", "SS", "MS"):
                assert a.loc[term, col] == pytest.approx(b.loc[term, col], abs=1e-9)
    raw = pd.DataFrame(source["Residuals"][1:], columns=source["Residuals"][0])
    raw.Subject = raw.Subject.map(str)
    for result in results:
        dependent = {"cmax": "Ln(Cmax)", "auc_last": "Ln(AUClast)", "auc_inf_pred": "Ln(AUCINF_pred)"}[
            result.endpoint
        ]
        golden = raw.loc[raw.Dependent.eq(dependent)].set_index(["Subject", "Period"])
        for row in result.diagnostics["residuals"]:
            for col in ("Predicted", "Residual"):
                assert row[col] == pytest.approx(
                    float(golden.loc[(row["subject_id"], row["period"]), col]), abs=1e-7
                )


def test_phoenix_targets_cannot_feed_estimation(phoenix_be):
    data, expected, _ = phoenix_be
    original, _ = compare_phoenix_be(data, expected)
    changed = expected.copy()
    for column in changed.select_dtypes(include="number"):
        changed[column] = 99999.0
    computed, checks = compare_phoenix_be(data, changed)
    assert computed == original
    assert not checks.Match.any()


def test_missing_requires_sap_and_ema_population_guard(phoenix_be):
    data, _, _ = phoenix_be
    assert analyze_abe(data, "auc_inf_pred", "2x2").decision == "NOT EVALUABLE"
    with pytest.raises(ValueError, match="SAP"):
        BeConfig(missing_policy="available_observations")
    cfg = BeConfig(
        missing_policy="available_observations", missing_data_reason="Predefined missing data strategy"
    )
    ema = Study(study_id="E", title="EMA")
    result = analyze_regulatory_be(data, "auc_inf_pred", ema, cfg)
    assert result.estimate is not None and result.decision == "NOT EVALUABLE"
    assert "EMA nonreplicate" in result.reason


def study_for(rule, design):
    return Study(
        study_id="VERIFY",
        title="Numerical verification only",
        rule_set_id=rule,
        design=design,
        nti="NTI" in rule,
        scaled_be_prespecified=True,
        hvd_justification="Synthetic verification; no clinical claim",
    )


@pytest.mark.parametrize("design", ["partial3", "full4"])
def test_ema_method_a_and_reference_variance_independent_statsmodels(design):
    data = statistical_demo(design)
    data["log_pk"] = np.log(data.cmax)
    oracle = smf.ols("log_pk ~ C(subject_id) + C(period) + C(treatment)", data=data).fit()
    result = analyze_regulatory_be(data, "cmax", study_for("EMA_HVDP_ABEL", design))
    assert result.estimate == pytest.approx(oracle.params["C(treatment)[T.T]"], abs=1e-12)
    assert result.se == pytest.approx(oracle.bse["C(treatment)[T.T]"], abs=1e-12)
    assert result.df == oracle.df_resid
    ref = data.loc[data.treatment.eq("R")]
    ref_fit = smf.ols("log_pk ~ C(subject_id) + C(period)", data=ref).fit()
    assert result.swr**2 == pytest.approx(ref_fit.mse_resid, abs=1e-13)
    assert result.diagnostics["replicate"]["df_reference"] == ref_fit.df_resid
    if design == "partial3":
        assert ref_fit.df_resid == data.subject_id.nunique() - 2  # Distinct from FDA D_R~sequence df n-3.
    assert result.lower_limit < 0.8
    auc = analyze_regulatory_be(data, "auc_last", study_for("EMA_HVDP_ABEL", design))
    assert (auc.lower_limit, auc.upper_limit) == (0.8, 1.25)


@pytest.mark.parametrize("design", ["partial3", "full4"])
def test_fda_hvd_ucb_against_independent_formula_models(design):
    data = statistical_demo(design)
    result = analyze_regulatory_be(data, "cmax", study_for("FDA_HVD_RSABE_2026", design))
    subjects = []
    for (sid, sequence), block in data.groupby(["subject_id", "sequence"]):
        ref = np.log(block.loc[block.treatment.eq("R")].sort_values("period").cmax.to_numpy())
        test = np.log(block.loc[block.treatment.eq("T"), "cmax"].to_numpy())
        subjects.append(dict(subject=sid, seq=sequence, i=test.mean() - ref.mean(), d=ref[0] - ref[1]))
    contrasts = pd.DataFrame(subjects)
    model_i = smf.ols("i ~ 0 + C(seq)", contrasts).fit()
    model_d = smf.ols("d ~ C(seq)", contrasts).fit()
    weights = np.ones(len(model_i.params)) / len(model_i.params)
    estimate = float(weights @ model_i.params)
    se = math.sqrt(float(weights @ model_i.cov_params() @ weights))
    s2wr = model_d.mse_resid / 2
    x = estimate**2 - se**2
    bx = (abs(estimate) + t.isf(0.05, model_i.df_resid) * se) ** 2
    y = -((math.log(1.25) / 0.25) ** 2) * s2wr
    by = y * model_d.df_resid / chi2.isf(0.05, model_d.df_resid)
    oracle = x + y + math.sqrt((bx - x) ** 2 + (by - y) ** 2)
    assert result.scaled_ucb == pytest.approx(oracle, abs=1e-13)
    assert result.swr == pytest.approx(math.sqrt(s2wr), abs=1e-13)
    assert len(result.criteria) == 2


def full_replicate_case(swr=0.10, swt=0.10, gmr=1.0):
    # Hand-constructed contrasts: I varies slightly, while D_R/D_T set independent within-product spread.
    residual = np.array([-3.0, -2.0, -1.0, 1.0, 2.0, 3.0])
    reference = residual * math.sqrt(2 * swr**2 * 10 / (2 * float(residual @ residual)))
    test = np.roll(residual, 2) * math.sqrt(2 * swt**2 * 10 / (2 * float(residual @ residual)))
    records = []
    for i in range(12):
        sequence = ("TRTR", "RTRT")[i // 6]
        delta = math.log(gmr) + residual[i % 6] * 0.001
        levels = {
            "R": [7 + reference[i % 6] / 2, 7 - reference[i % 6] / 2],
            "T": [7 + delta + test[i % 6] / 2, 7 + delta - test[i % 6] / 2],
        }
        used = {"T": 0, "R": 0}
        for period, trt in enumerate(sequence, 1):
            value = math.exp(levels[trt][used[trt]])
            used[trt] += 1
            records.append(
                dict(
                    subject_id=str(i),
                    sequence=sequence,
                    period=period,
                    treatment=trt,
                    cmax=value,
                    auc_last=value,
                )
            )
    return pd.DataFrame(records)


def test_nti_three_criteria_and_sd_ratio_upper_bound():
    study = study_for("FDA_NTI", "full4")
    good = analyze_regulatory_be(full_replicate_case(), "cmax", study)
    assert good.decision == "NOT EVALUABLE" and len(good.criteria) == 3
    assert good.criteria[0]["passed"] is None
    assert good.criteria[1]["passed"] and good.criteria[2]["passed"]
    assert good.diagnostics["conventional_abe_ci90"] is None
    assert good.swr == pytest.approx(0.1)
    assert good.sd_ratio_ci_upper == pytest.approx(1 / math.sqrt(f.ppf(0.05, 10, 10)))
    bad = analyze_regulatory_be(full_replicate_case(swt=0.3), "cmax", study)
    assert bad.criteria[0]["passed"] is None and bad.criteria[1]["passed"]
    assert not bad.criteria[2]["passed"] and bad.decision == "NOT EVALUABLE"
    assert bad.scaled_ucb < 0
    assert bad.sd_ratio_ci_upper > 2.5


def test_fda_threshold_and_point_constraint():
    study = study_for("FDA_HVD_RSABE_2026", "full4")
    low = analyze_regulatory_be(full_replicate_case(swr=0.293999), "cmax", study)
    high = analyze_regulatory_be(full_replicate_case(swr=0.294001), "cmax", study)
    assert low.scaled_ucb is None and "unscaled ABE" in low.method
    assert high.scaled_ucb is not None and "RSABE" in high.method
    outside = analyze_regulatory_be(full_replicate_case(swr=0.6, gmr=1.27), "cmax", study)
    assert outside.scaled_ucb < 0 and outside.decision == "FAIL"
    assert not outside.criteria[1]["passed"]


def test_ema_nti_endpoint_specific_limits_and_scope():
    data = statistical_demo("2x2", nti=True)
    study = study_for("EMA_NTI", "2x2")
    auc = analyze_regulatory_be(data, "auc_last", study)
    cmax = analyze_regulatory_be(data, "cmax", study)
    assert (auc.lower_limit, auc.upper_limit) == (0.9, 1.1111)
    assert (cmax.lower_limit, cmax.upper_limit) == (0.8, 1.25)
    narrowed = analyze_regulatory_be(data, "cmax", study.model_copy(update={"nti_cmax_narrow": True}))
    assert narrowed.lower_limit == 0.9
    mismatch = study.model_copy(update={"rule_set_id": "FDA_HVD_RSABE_2026"})
    assert any("NTI" in r for r in scope_blockers(mismatch))


@pytest.mark.parametrize(
    "change", ["missing_period", "wrong_treatment", "duplicate", "negative", "missing_endpoint"]
)
def test_replicate_rejects_invalid_data(change):
    data = full_replicate_case()
    if change == "missing_period":
        data = data.iloc[1:]
    elif change == "wrong_treatment":
        data.loc[0, "treatment"] = "R"
    elif change == "duplicate":
        data = pd.concat([data, data.iloc[:1]], ignore_index=True)
    elif change == "negative":
        data.loc[0, "cmax"] = -1
    else:
        data.loc[0, "cmax"] = np.nan
    result = analyze_regulatory_be(data, "cmax", study_for("FDA_NTI", "full4"))
    assert result.decision == "NOT EVALUABLE"
    assert result.reason


def test_nonreplicate_hvd_never_scales_pooled_cv(phoenix_be):
    data, _, _ = phoenix_be
    result = analyze_regulatory_be(data, "cmax", study_for("FDA_HVD_RSABE_2026", "2x2"))
    assert result.cv_within > 0.3 and result.swr is None
    assert result.decision == "NOT EVALUABLE" and result.scaled_ucb is None


def test_scaling_requires_prespecified_justification():
    study = study_for("EMA_HVDP_ABEL", "full4").model_copy(update={"scaled_be_prespecified": False})
    result = analyze_regulatory_be(full_replicate_case(swr=0.4), "cmax", study)
    assert result.estimate is not None and result.decision == "NOT EVALUABLE"
    assert "định trước" in result.reason


def test_export_includes_complete_statistics_and_no_formulas(phoenix_be):
    data, expected, _ = phoenix_be
    results, checks = compare_phoenix_be(data, expected)
    independent_book = openpyxl.load_workbook(io.BytesIO(be_workbook(results, data=data)))
    assert "Average Bioequivalence" in independent_book.sheetnames
    assert "Settings" in independent_book.sheetnames
    assert not any("Phoenix" in name for name in independent_book.sheetnames)
    encoded = be_comparison_workbook(results, data=data, comparison=checks)
    book = openpyxl.load_workbook(io.BytesIO(encoded))
    for sheet in (
        "Average Bioequivalence",
        "Decision Criteria",
        "Partial Tests",
        "Final Fixed Parameters",
        "Final Variance Parameters",
        "Least Squares Means",
        "Residuals",
        "Missing Observations",
        "Input PK",
        "Phoenix Comparison",
    ):
        assert sheet in book.sheetnames and book[sheet].max_row > 1
    assert book["Average Bioequivalence"].max_row == 4
    assert book["Missing Observations"].max_row == 19
    assert not any(c.data_type == "f" for sheet in book for row in sheet for c in row)


def test_be_reference_ui_and_hvd_nti_demo(tmp_path, monkeypatch, caplog):
    import be_app.ui as ui
    from be_app.persistence import ProjectStore

    monkeypatch.setattr(ui, "store", lambda: ProjectStore(tmp_path / "be-extended-ui.sqlite"))
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=60).run()
    open_be_page(app, ui.PAGES[6])
    assert not any("Phoenix" in b.label for b in app.button)
    assert not any("Phoenix" in e.label for e in app.get("expander"))
    app.selectbox(key="pk_be_demo_case").set_value("nti").run()
    next(b for b in app.button if b.label == "Điền dữ liệu mẫu vào bảng PK").click().run()
    assert "pk_be_result" not in app.session_state
    owner = app.session_state.get("active_project_state") or app.session_state.creation_state
    editor_key = f"table::pk_be_source::{owner.project.project_id}"
    assert editor_key in app.session_state
    assert {"Subject", "Cmax", "AUClast"} <= set(app.session_state[editor_key]["committed"].columns)
    editor = app.session_state[editor_key]
    new_cmax = round(float(editor["committed"].loc[0, "Cmax"]) * 1.01, 5)
    editor["committed"].loc[0, "Cmax"] = str(new_cmax)
    app.session_state[editor_key] = editor
    app.run()
    assert not app.exception
    app.selectbox(key="pk_be_rule").set_value("FDA_NTI").run()
    next(b for b in app.checkbox if b.label.startswith("Đã xác nhận đơn vị nguồn Cmax")).set_value(True).run()
    next(b for b in app.button if b.label == "Phân tích bảng PK đã tải").click().run()
    assert not app.exception and not app.error
    results = app.session_state.pk_be_result["results"]
    assert all(r.scaled_ucb is not None and r.sd_ratio_ci_upper is not None for r in results)
    assert app.session_state.pk_be_result["provenance"]["source_file"] == "edited_pk.csv"
    assert app.session_state.pk_be_result["data"].loc[0, "cmax"] == new_cmax
    assert "Serialization of dataframe to Arrow table was unsuccessful" not in caplog.text


def test_original_workbook_parser_if_available():
    source = Path(__file__).resolve().parents[1] / "Bioequivalence_Fasted.xlsx"
    if not source.exists():
        pytest.skip("Local user workbook; portable fixture is tested separately")
    data, expected, provenance = read_phoenix_be(source.read_bytes(), source.name)
    assert len(data) == 48 and provenance["source_sha256"]
    _, checks = compare_phoenix_be(data, expected)
    assert checks.Match.all()
