"""Quick BE runs without project state and fails closed on missing profiles."""

import io

import numpy as np
import pandas as pd
import pytest
from scipy.stats import mannwhitneyu, wilcoxon

from be_app.domain import BeConfig
from be_app.quick_be import quick_be_workbook, run_quick_be
from be_app.statistics import analyze_abe


def pk_table():
    rows = []
    for number, sequence in enumerate(["TR", "TR", "RT", "RT", "TR", "RT"], 1):
        for period, treatment in enumerate(sequence, 1):
            factor = 1.07 if treatment == "T" else 1.0
            value = (18 + number * 1.1 + (period - 1) * 0.3) * factor
            rows.append({"Subject": f"{number:03d}", "Sequence": sequence, "Period": period,
                         "Treatment": treatment, "Cmax": value, "AUClast": value * (2.9 + number * 0.02)})
    return pd.DataFrame(rows)


def concentration_table():
    data = []
    for pk in pk_table().itertuples(index=False):
        for time, fraction in [(0, 0), (1, 0.65), (2, 1), (4, 0.75), (8, 0.35), (12, 0.16), (18, 0.05)]:
            data.append({"Subject": pk.Subject, "Sequence": pk.Sequence, "Period": pk.Period,
                         "Treatment": pk.Treatment, "Time": time, "Cplasma": pk.Cmax * fraction})
    return pd.DataFrame(data)


def encoded(frame):
    return frame.to_csv(index=False).encode("utf-8-sig")


def run(frame, **kwargs):
    return run_quick_be(encoded(frame), "test.csv", **kwargs)


def test_endpoint_be_matches_existing_engine_and_preserves_leading_zero_ids():
    out = run(pk_table(), mode="endpoint")
    assert out.mode == "endpoint" and out.nca.empty
    assert out.endpoints.subject_id.iloc[0] == "001"
    assert len(out.endpoints) == 12
    for result in out.results[:2]:
        reference = analyze_abe(out.endpoints, result.endpoint, "2x2", BeConfig())
        assert result.decision == reference.decision
        assert result.gmr == pytest.approx(reference.gmr)
        assert result.ci_lower == pytest.approx(reference.ci_lower)
    assert len(out.provenance["source_sha256"]) == 64


def test_concentration_flow_runs_nca_then_be_and_exports_evidence():
    out = run(concentration_table())
    assert out.mode == "concentration"
    assert len(out.concentrations) == 84 and len(out.nca) == 12
    assert out.nca.status.eq("EVALUABLE").all()
    assert out.endpoints.cmax.notna().all() and out.endpoints.auc_last.notna().all()
    assert out.endpoints.tmax.eq(2).all()
    assert out.tmax.status == "EVALUABLE"
    assert out.tmax.n_pairs == 6 and out.tmax.p_value == 1.0
    assert all(result.decision in ("PASS", "FAIL") for result in out.results[:2])
    exported = pd.ExcelFile(io.BytesIO(quick_be_workbook(out)))
    assert {"Input PK", "Input Concentrations", "NCA Profiles", "Quick BE Source", "Quick BE Review",
            "Tmax Nonparametric"} <= set(exported.sheet_names)
    tmax_export = pd.read_excel(exported, sheet_name="Tmax Nonparametric")
    assert tmax_export.loc[0, "P_two_sided"] == 1.0


def test_concentration_missing_time_is_rejected_and_no_baseline_is_fabricated():
    with pytest.raises(ValueError, match="Time"):
        run(concentration_table().drop(columns="Time"))
    no_baseline = concentration_table().query("Time != 0")
    out = run(no_baseline)
    assert out.nca.status.eq("NOT EVALUABLE").all()
    assert out.overall_status == "NOT EVALUABLE"
    assert all(r.decision == "NOT EVALUABLE" for r in out.results)
    assert any("baseline" in warning for warning in out.warnings)


def test_duplicates_in_long_format_and_wrong_sequence_rejected():
    frame = concentration_table()
    with pytest.raises(ValueError, match="Trùng Subject/Period/Time"):
        run(pd.concat([frame, frame.iloc[[0]]], ignore_index=True))
    frame.loc[frame.Subject.eq("001") & frame.Period.eq(1), "Treatment"] = "R"
    with pytest.raises(ValueError, match="không khớp Sequence"):
        run(frame)


def test_missing_profile_and_missing_endpoint_block_full_assessment():
    missing = pk_table().query("not (Subject == '001' and Period == 2)")
    out = run(missing)
    assert out.overall_status == "NOT EVALUABLE"
    assert len(out.endpoints) == 12 and out.endpoints.cmax.isna().sum() == 1
    assert any("Subject 001" in warning for warning in out.warnings)
    only_cmax = run(pk_table().drop(columns="AUClast"))
    assert only_cmax.overall_status == "NOT EVALUABLE"
    assert next(r for r in only_cmax.results if r.endpoint == "auc_last").decision == "NOT EVALUABLE"


def test_blq_explicit_and_bad_values_not_silently_replaced():
    data = concentration_table()
    data["BLQ"] = "false"
    data.loc[data.Time.eq(0), "BLQ"] = "true"
    out = run(data)
    assert out.concentrations.blq_flag.sum() == 12
    data.loc[0, "Cplasma"] = -1
    with pytest.raises(ValueError, match="không được âm"):
        run(data)
    data.loc[0, "Cplasma"] = 0
    data.loc[0, "BLQ"] = "unknown"
    with pytest.raises(ValueError, match="BLQ"):
        run(data)


def test_parallel_and_replicate_endpoint_paths():
    p = pk_table().query("Period == 1").copy()
    p["Sequence"] = p["Treatment"]
    outcome = run(p, design="parallel")
    assert len(outcome.results) >= 2
    assert all(r.decision in ("PASS", "FAIL") for r in outcome.results[:2])

    rows = []
    for sequence in ("TRR", "RTR", "RRT"):
        for i in range(3):
            subject = f"{sequence}_{i}"
            for period, treatment in enumerate(sequence, 1):
                val = (21 + i * 2 + period * 0.3) * (1.06 if treatment == "T" else 1)
                rows.append(dict(Subject=subject, Sequence=sequence, Period=period,
                                 Treatment=treatment, Cmax=val, AUClast=val * 3))
    replicate = run(pd.DataFrame(rows), design="partial3")
    assert len(replicate.endpoints) == 27
    assert len(replicate.results) >= 2
    assert replicate.provenance["settings"]["rule_id"] == "EMA_REPLICATE_STANDARD"


def test_tmax_2x2_uses_paired_wilcoxon_with_ties_and_preserves_abe_decision():
    frame = pk_table()
    t_values = [1, 2, 3, 4, 2, 5]
    frame["Tmax"] = [t_values[int(row.Subject) - 1] if row.Treatment == "T" else 2
                     for row in frame.itertuples(index=False)]
    out = run(frame, mode="endpoint")
    differences = np.array(t_values, dtype=float) - 2
    expected = wilcoxon(differences, alternative="two-sided", zero_method="wilcox", method="auto")
    assert out.tmax.status == "EVALUABLE"
    assert out.tmax.method.startswith("Wilcoxon")
    assert out.tmax.n_t == out.tmax.n_r == out.tmax.n_pairs == 6
    assert out.tmax.median_t == 2.5 and out.tmax.median_r == 2.0
    assert out.tmax.median_paired_difference == pytest.approx(np.median(differences))
    assert out.tmax.statistic == pytest.approx(expected.statistic)
    assert out.tmax.p_value == pytest.approx(expected.pvalue)
    assert out.overall_status == run(pk_table(), mode="endpoint").overall_status
    xls = pd.read_excel(io.BytesIO(quick_be_workbook(out)), sheet_name="Tmax Nonparametric")
    assert xls.loc[0, "N_pairs"] == 6
    assert xls.loc[0, "P_two_sided"] == pytest.approx(expected.pvalue)


def test_tmax_parallel_uses_two_sided_mann_whitney():
    frame = pk_table().query("Period == 1").copy()
    frame["Sequence"] = frame["Treatment"]
    frame["Tmax"] = [1, 1, 2, 4, 4, 5]
    out = run(frame, mode="endpoint", design="parallel")
    sample_t = frame.loc[frame.Treatment.eq("T"), "Tmax"]
    sample_r = frame.loc[frame.Treatment.eq("R"), "Tmax"]
    expected = mannwhitneyu(sample_t, sample_r, alternative="two-sided", method="auto")
    assert out.tmax.status == "EVALUABLE" and out.tmax.n_pairs is None
    assert out.tmax.method.startswith("Mann")
    assert out.tmax.statistic == pytest.approx(expected.statistic)
    assert out.tmax.p_value == pytest.approx(expected.pvalue)


def test_tmax_missing_invalid_and_partial_pairs_fail_closed_without_affecting_be():
    frame = pk_table()
    absent = run(frame)
    assert absent.tmax.status == "NOT EVALUABLE" and "Không có cột Tmax" in absent.tmax.reason
    assert absent.overall_status == "PASS"

    frame["Tmax"] = "2.0"
    for invalid in ("", "abc", "inf", "-1"):
        bad = frame.copy()
        bad.loc[0, "Tmax"] = invalid
        out = run(bad)
        assert out.tmax.status == "NOT EVALUABLE"
        assert "không tự loại" in out.tmax.reason
        assert out.overall_status == absent.overall_status

    missing = frame.query("not (Subject == '001' and Period == 2)")
    out = run(missing)
    assert out.tmax.status == "NOT EVALUABLE"
    assert out.overall_status == "NOT EVALUABLE"


def test_tmax_replicate_stays_descriptive_and_does_not_claim_unsupported_test():
    rows = []
    for sequence in ("TRR", "RTR", "RRT"):
        for number in range(3):
            for period, treatment in enumerate(sequence, 1):
                rows.append(dict(Subject=f"{sequence}_{number}", Sequence=sequence,
                                 Period=period, Treatment=treatment, Cmax=20 + number + period,
                                 AUClast=65 + number + period, Tmax=period))
    out = run(pd.DataFrame(rows), design="partial3")
    assert out.tmax.status == "NOT EVALUABLE"
    assert "replicate" in out.tmax.reason
    assert out.tmax.p_value is None


def test_explicit_source_mapping_and_log_pk_values():
    frame = pk_table().rename(columns={"Subject": "Participant", "Cmax": "Peak"})
    frame["Peak"] = np.log(frame.Peak)
    mapping = {"Participant": "subject_id", "Sequence": "sequence", "Period": "period",
               "Treatment": "treatment", "Peak": "cmax", "AUClast": "auc_last"}
    # All endpoint columns share one declared scale; both columns are encoded in ln.
    frame["AUClast"] = np.log(frame.AUClast)
    outcome = run(frame, column_mapping=mapping, endpoint_scale="ln", mode="endpoint")
    assert "Participant" in outcome.raw and "Peak" in outcome.raw
    assert "subject_id" not in outcome.raw
    assert float(outcome.raw.Peak.iloc[0]) == pytest.approx(frame.Peak.iloc[0])
    assert outcome.endpoints.cmax.iloc[0] == pytest.approx(pk_table().Cmax.iloc[0])
    assert outcome.endpoints.auc_last.iloc[0] == pytest.approx(pk_table().AUClast.iloc[0])
    workbook = pd.read_excel(io.BytesIO(quick_be_workbook(outcome)), sheet_name="Quick BE Source")
    assert "Participant" in workbook and "Peak" in workbook
