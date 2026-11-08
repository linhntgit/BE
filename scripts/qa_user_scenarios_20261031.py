"""Reproducible synthetic QA assets; never real study evidence."""

import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from be_app.design import SEQUENCES, randomize
from be_app.domain import Study
from be_app.replicate import analyze_regulatory_be

OUT = Path(__file__).resolve().parents[1] / "output" / "qa_20261031"
OUT.mkdir(parents=True, exist_ok=True)
SEED = 20261031


def endpoints(design, swr=0.15, swt=None, gmr=1.0, n=36):
    rng = np.random.default_rng(SEED)
    rows = []
    for i in range(n):
        seq = SEQUENCES[design][i % len(SEQUENCES[design])]
        subject = rng.normal(0, 0.18)
        for period, trt in enumerate(seq, 1):
            err = rng.normal(0, swr if trt == "R" else (swt if swt is not None else swr))
            level = math.exp(subject + err + (0.01 * period) + (math.log(gmr) if trt == "T" else 0))
            rows.append(
                dict(
                    subject_id=f"SYN{i + 1:03}",
                    sequence=seq,
                    period=period,
                    treatment=trt,
                    cmax=100 * level,
                    auc_last=800 * level,
                    auc_inf_pred=810 * level,
                )
            )
    return pd.DataFrame(rows)


def boundary_data(swr, gmr=1.0, swt=0.10):
    residual = np.array([-3.0, -2.0, -1.0, 1.0, 2.0, 3.0])
    ref = residual * math.sqrt(10 * swr * swr / float(residual @ residual))
    test = np.roll(residual, 2) * math.sqrt(10 * swt * swt / float(residual @ residual))
    rows = []
    for i in range(12):
        seq = ("TRTR", "RTRT")[i // 6]
        delta = math.log(gmr) + residual[i % 6] * 0.001
        values = {
            "R": [7 + ref[i % 6] / 2, 7 - ref[i % 6] / 2],
            "T": [7 + delta + test[i % 6] / 2, 7 + delta - test[i % 6] / 2],
        }
        used = {"T": 0, "R": 0}
        for period, trt in enumerate(seq, 1):
            value = math.exp(values[trt][used[trt]])
            used[trt] += 1
            rows.append(
                dict(
                    subject_id=f"SYN{i:03}",
                    sequence=seq,
                    period=period,
                    treatment=trt,
                    cmax=value,
                    auc_last=value,
                )
            )
    return pd.DataFrame(rows)


def main():
    allocation, _ = randomize("2x2", 24, 241029, 4)
    rng = np.random.default_rng(SEED)
    rows = []
    for a in allocation.to_dict("records"):
        dose = datetime(2026, 10, 1, 8, tzinfo=timezone(timedelta(hours=8))) + timedelta(
            days=7 * (a["period"] - 1)
        )
        amplitude = 140 * rng.lognormal(0, 0.10) * (1.02 if a["treatment"] == "T" else 1)
        for h in [0, 0.25, 0.5, 1, 1.5, 2, 3, 4, 6, 8, 12, 16, 24, 36]:
            c = amplitude * (math.exp(-0.14 * h) - math.exp(-1.5 * h)) * rng.lognormal(0, 0.02)
            blq = c < 0.2
            rows.append(
                dict(
                    study_id="QA_20261031_ABE",
                    subject_id=a["subject_id"],
                    sequence=a["sequence"],
                    period=a["period"],
                    treatment=a["treatment"],
                    dose_datetime=dose.isoformat(),
                    sample_datetime=(dose + timedelta(hours=h)).isoformat(),
                    nominal_time_h=h,
                    actual_time_h=h,
                    concentration=0 if blq else c,
                    concentration_unit="ng/mL",
                    blq_flag=blq,
                    lloq=0.2,
                    sample_id=f"SYN_{a['subject_id']}_P{a['period']}_H{h}",
                    analyte="parent",
                    source_batch="SYNTHETIC_QA_20261031",
                    sample_status="BLQ" if blq else "VALID",
                )
            )
    pd.DataFrame(rows).to_csv(OUT / "SYNTHETIC_concentrations_ABE.csv", index=False)
    allocation.to_csv(OUT / "expected_allocation.csv", index=False)
    cases = [
        ("ABE_EMA_pass", "EMA_IR_NONREPLICATE_M13A", "2x2", 0.10, 1.0),
        ("ABE_EMA_fail", "EMA_IR_NONREPLICATE_M13A", "2x2", 0.10, 1.45),
        ("ABE_FDA_pass", "FDA_ABE_2026", "2x2", 0.10, 1.0),
        ("parallel_EMA", "EMA_IR_NONREPLICATE_M13A", "parallel", 0.10, 1.0),
        ("EMA_replicate", "EMA_REPLICATE_STANDARD", "full4", 0.15, 1.0),
        ("EMA_ABEL_full", "EMA_HVDP_ABEL", "full4", 0.45, 1.0),
        ("EMA_ABEL_partial", "EMA_HVDP_ABEL", "partial3", 0.45, 1.0),
        ("EMA_ABEL_cap", "EMA_HVDP_ABEL", "full4", 0.75, 1.0),
        ("EMA_ABEL_point_fail", "EMA_HVDP_ABEL", "full4", 0.65, 1.6),
        ("EMA_ABEL_low_cv", "EMA_HVDP_ABEL", "full4", 0.10, 1.0),
        ("FDA_RSABE_full", "FDA_HVD_RSABE_2026", "full4", 0.45, 1.0),
        ("FDA_RSABE_partial", "FDA_HVD_RSABE_2026", "partial3", 0.45, 1.0),
        ("FDA_RSABE_point_fail", "FDA_HVD_RSABE_2026", "full4", 0.65, 1.6),
        ("FDA_RSABE_low_cv", "FDA_HVD_RSABE_2026", "full4", 0.10, 1.0),
        ("EMA_NTI", "EMA_NTI", "2x2", 0.08, 1.0),
        ("EMA_NTI_fail", "EMA_NTI", "2x2", 0.08, 1.16),
        ("FDA_NTI", "FDA_NTI", "full4", 0.08, 1.0),
        ("FDA_replicate_gate", "FDA_REPLICATE_STANDARD", "full4", 0.10, 1.0),
        ("wrong_design_RSABE", "FDA_HVD_RSABE_2026", "2x2", 0.45, 1.0),
    ]
    results = []
    for name, rule, design, sigma, gmr in cases:
        data = endpoints(design, sigma, gmr=gmr)
        data.to_csv(OUT / f"SYNTHETIC_PK_{name}.csv", index=False)
        study = Study(
            study_id="SYN_QA",
            title=name,
            design=design,
            rule_set_id=rule,
            nti="NTI" in rule,
            scaled_be_prespecified=True,
            hvd_justification="Synthetic prespecified QA scenario",
            protocol="SYN v1",
            sap="SYN v1",
            scope_reviewed=True,
            scope_evidence="Synthetic QA only",
            active_ingredient="SYNTHETIC",
            is_demo=True,
        )
        for ep in ("cmax", "auc_last"):
            r = analyze_regulatory_be(data, ep, study)
            results.append(dict(scenario=name, **r.model_dump(mode="json")))
    base = endpoints("full4", 0.45)
    study = Study(
        study_id="SYN_QA",
        title="invalid",
        design="full4",
        rule_set_id="FDA_HVD_RSABE_2026",
        scaled_be_prespecified=True,
        hvd_justification="Synthetic QA only",
    )
    for mutation in (
        "missing_period",
        "duplicate",
        "negative",
        "zero",
        "missing_endpoint",
        "wrong_treatment",
    ):
        data = base.copy()
        if mutation == "missing_period":
            data = data.iloc[1:]
        if mutation == "duplicate":
            data = pd.concat([data, data.iloc[:1]])
        if mutation == "negative":
            data.loc[0, "cmax"] = -1
        if mutation == "zero":
            data.loc[0, "cmax"] = 0
        if mutation == "missing_endpoint":
            data.loc[0, "cmax"] = np.nan
        if mutation == "wrong_treatment":
            data.loc[0, "treatment"] = "X"
        data.to_csv(OUT / f"SYNTHETIC_PK_invalid_{mutation}.csv", index=False)
        r = analyze_regulatory_be(data, "cmax", study)
        results.append(dict(scenario="invalid_" + mutation, **r.model_dump(mode="json")))
    for sigma in (0.293999, 0.294, 0.294001):
        data = boundary_data(sigma)
        r = analyze_regulatory_be(data, "cmax", study)
        results.append(dict(scenario=f"FDA_threshold_{sigma}", **r.model_dump(mode="json")))
    for cv in (0.299999, 0.30, 0.300001, 0.50, 0.75):
        data = boundary_data(math.sqrt(math.log1p(cv * cv)))
        s = study.model_copy(update={"rule_set_id": "EMA_HVDP_ABEL"})
        r = analyze_regulatory_be(data, "cmax", s)
        results.append(dict(scenario=f"EMA_threshold_CV_{cv}", **r.model_dump(mode="json")))
    for label, updates in [
        ("no_prespec", {"scaled_be_prespecified": False}),
        ("no_justification", {"hvd_justification": ""}),
        ("NTI_mismatch", {"nti": True}),
    ]:
        r = analyze_regulatory_be(base, "cmax", study.model_copy(update=updates))
        results.append(dict(scenario=label, **r.model_dump(mode="json")))
    for rule in ("EMA_HVDP_ABEL", "FDA_HVD_RSABE_2026"):
        r = analyze_regulatory_be(
            boundary_data(0.6, gmr=1.27), "cmax", study.model_copy(update={"rule_set_id": rule})
        )
        results.append(dict(scenario=rule + "_isolated_GMR_fail", **r.model_dump(mode="json")))
    (OUT / "scenario_results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8"
    )
    summary = pd.DataFrame(
        [
            {
                k: r.get(k)
                for k in (
                    "scenario",
                    "endpoint",
                    "method",
                    "decision",
                    "gmr",
                    "ci_lower",
                    "ci_upper",
                    "swr",
                    "scaled_ucb",
                    "lower_limit",
                    "upper_limit",
                    "reason",
                )
            }
            for r in results
        ]
    )
    summary.to_csv(OUT / "scenario_summary.csv", index=False)
    print(summary[["scenario", "endpoint", "decision"]].to_string(index=False))


if __name__ == "__main__":
    main()
