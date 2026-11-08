"""Check QA evidence independently of browser rendering, with explicit expected outcomes."""

import base64
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from be_app.design import randomize
from be_app.domain import Study
from be_app.imports import validate_data
from be_app.persistence import Project, export_archive, import_archive
from be_app.pipeline import run_analysis
from be_app.state import result_status

OUT = Path(__file__).resolve().parents[1] / "output" / "qa_20261031"


def main():
    results = json.loads((OUT / "scenario_results.json").read_text(encoding="utf-8"))
    by_key = {(r["scenario"], r["endpoint"]): r for r in results}
    checks = []

    def check(name, value):
        checks.append({"check": name, "passed": bool(value)})

    for name in (
        "ABE_EMA_pass",
        "ABE_FDA_pass",
        "parallel_EMA",
        "EMA_replicate",
        "EMA_ABEL_full",
        "EMA_ABEL_low_cv",
        "FDA_RSABE_full",
        "FDA_RSABE_partial",
        "EMA_NTI",
    ):
        for ep in ("cmax", "auc_last"):
            check(f"{name}/{ep}: PASS", by_key[name, ep]["decision"] == "PASS")
    for name in ("ABE_EMA_fail", "EMA_ABEL_point_fail", "FDA_RSABE_point_fail"):
        for ep in ("cmax", "auc_last"):
            check(f"{name}/{ep}: FAIL", by_key[name, ep]["decision"] == "FAIL")
    for name in ("FDA_RSABE_low_cv", "FDA_NTI", "FDA_replicate_gate", "wrong_design_RSABE"):
        for ep in ("cmax", "auc_last"):
            check(f"{name}/{ep}: blocked", by_key[name, ep]["decision"] == "NOT EVALUABLE")
    for r in results:
        if r["scenario"].startswith("invalid_") or r["scenario"] in (
            "no_prespec",
            "no_justification",
            "NTI_mismatch",
        ):
            check(r["scenario"], r["decision"] == "NOT EVALUABLE")
    check(
        "EMA partial Cmax passes, AUC fails",
        by_key["EMA_ABEL_partial", "cmax"]["decision"] == "PASS"
        and by_key["EMA_ABEL_partial", "auc_last"]["decision"] == "FAIL",
    )
    check(
        "EMA cap bounds",
        (by_key["EMA_ABEL_cap", "cmax"]["lower_limit"], by_key["EMA_ABEL_cap", "cmax"]["upper_limit"])
        == (0.6984, 1.4319),
    )
    check(
        "EMA AUC never widened",
        (by_key["EMA_ABEL_cap", "auc_last"]["lower_limit"], by_key["EMA_ABEL_cap", "auc_last"]["upper_limit"])
        == (0.8, 1.25),
    )
    check(
        "NTI AUC narrow, Cmax conventional",
        by_key["EMA_NTI_fail", "auc_last"]["decision"] == "FAIL"
        and by_key["EMA_NTI_fail", "cmax"]["decision"] == "PASS",
    )
    check(
        "FDA below threshold gated", by_key["FDA_threshold_0.293999", "cmax"]["decision"] == "NOT EVALUABLE"
    )
    check(
        "FDA exact and above threshold scaled",
        all(
            by_key[n, "cmax"]["scaled_ucb"] is not None
            for n in ("FDA_threshold_0.294", "FDA_threshold_0.294001")
        ),
    )
    for rule in ("EMA_HVDP_ABEL", "FDA_HVD_RSABE_2026"):
        r = by_key[rule + "_isolated_GMR_fail", "cmax"]
        check(
            rule + " independent GMR constraint",
            r["decision"] == "FAIL" and r["gmr"] > 1.25 and r["criteria"][-1]["passed"] is False,
        )

    mapping = {
        "UI_EMA_ABEL.xlsx": "EMA_ABEL_full",
        "UI_EMA_ABEL_partial.xlsx": "EMA_ABEL_partial",
        "UI_FDA_RSABE.xlsx": "FDA_RSABE_full",
        "UI_FDA_RSABE_partial.xlsx": "FDA_RSABE_partial",
        "UI_EMA_NTI.xlsx": "EMA_NTI_fail",
    }
    for name, scenario in mapping.items():
        frame = pd.read_excel(OUT / name, sheet_name="Average Bioequivalence")
        for dep, ep in (("Ln(Cmax)", "cmax"), ("Ln(AUClast)", "auc_last")):
            actual = frame.loc[frame.Dependent.eq(dep)].iloc[0]
            expected = by_key[scenario, ep]
            check(
                f"Browser workbook {name}/{ep} matches engine",
                actual.Decision == expected["decision"]
                and all(
                    math.isclose(float(actual[c]) / 100, expected[k], abs_tol=1e-11)
                    for c, k in (
                        ("Ratio_%Ref_", "gmr"),
                        ("CI_90_Lower", "ci_lower"),
                        ("CI_90_Upper", "ci_upper"),
                    )
                ),
            )
    nti = pd.read_excel(OUT / "UI_EMA_NTI_Cmax_narrow.xlsx", sheet_name="Average Bioequivalence")
    check(
        "Browser Cmax narrowed NTI fails",
        nti.Decision.eq("FAIL").all() and nti.Applicable_Lower_Percent.eq(90).all(),
    )
    fda = pd.read_excel(OUT / "UI_FDA_NTI_high.xlsx", sheet_name="Average Bioequivalence")
    check("Browser FDA NTI gated", fda.Decision.eq("NOT EVALUABLE").all())

    archived = import_archive((OUT / "QA_20261031_ABE.beproject.zip").read_bytes())
    manifest = json.loads((OUT / "project_input_manifest.json").read_text())
    analysis = json.loads((OUT / "project_analysis.json").read_text())
    check(
        "Archive current and retains original run",
        result_status(archived) == "CURRENT"
        and len(archived.runs) == 1
        and analysis["analysis_run_id"] == archived.runs[0]["analysis_run_id"],
    )
    check(
        "Manifest and archive snapshot agree",
        all(
            manifest[k] == archived.runs[0][k]
            for k in ("snapshot_hash", "input_fingerprint", "raw_hash", "analysis_run_id")
        ),
    )
    check(
        "Archive raw bytes unchanged",
        base64.b64decode(archived.raw_base64) == (OUT / "SYNTHETIC_concentrations_ABE.csv").read_bytes(),
    )
    check("Archive contains both report artifacts", len(archived.artifacts) == 2)

    qc_rows = []
    for mutation in ("negative", "duplicate", "bad_time", "wrong_unit", "wrong_treatment", "missing_column"):
        data = pd.read_csv(OUT / "SYNTHETIC_concentrations_ABE.csv", dtype=str, keep_default_na=False)
        if mutation == "negative":
            data.loc[1, "concentration"] = "-3"
        if mutation == "duplicate":
            data = pd.concat([data, data.iloc[:1]], ignore_index=True)
        if mutation == "bad_time":
            data.loc[1, "sample_datetime"] = "2026-10-01T08:15:00"
        if mutation == "wrong_unit":
            data.loc[1, "concentration_unit"] = "banana"
        if mutation == "wrong_treatment":
            data.loc[1, "treatment"] = "T"
        if mutation == "missing_column":
            data = data.drop(columns="sample_id")
        qc = validate_data(data, archived.study, pd.DataFrame(archived.allocation))
        check("Concentration QC rejects " + mutation, not qc.valid)
        qc_rows.append(dict(mutation=mutation, valid=qc.valid, codes=sorted({f.code for f in qc.flags})))

    pipeline = []
    for label, rule, design, sigma, nti in (
        ("EMA_ABEL_full", "EMA_HVDP_ABEL", "full4", 0.45, False),
        ("EMA_ABEL_partial", "EMA_HVDP_ABEL", "partial3", 0.45, False),
        ("FDA_RSABE_full", "FDA_HVD_RSABE_2026", "full4", 0.45, False),
        ("FDA_RSABE_partial", "FDA_HVD_RSABE_2026", "partial3", 0.45, False),
        ("EMA_NTI", "EMA_NTI", "2x2", 0.08, True),
        ("FDA_NTI", "FDA_NTI", "full4", 0.08, True),
    ):
        study = Study(
            study_id="SYN_QA_" + label,
            title="Synthetic pipeline " + label,
            design=design,
            rule_set_id=rule,
            nti=nti,
            scaled_be_prespecified=True,
            hvd_justification="Synthetic QA prespecified reference variability",
            is_demo=True,
            protocol="SYN v1",
            sap="SYN v1",
            scope_reviewed=True,
            scope_evidence="Synthetic QA only",
            active_ingredient="SYNTHETIC",
        )
        allocation, meta = randomize(design, 36, 20261031)
        rng = np.random.default_rng(20261031)
        rows = []
        for a in allocation.to_dict("records"):
            dose = datetime(2026, 10, 1, 8, tzinfo=timezone(timedelta(hours=8))) + timedelta(
                days=7 * (a["period"] - 1)
            )
            amp = 140 * rng.lognormal(0, sigma)
            for h in (0, 0.25, 0.5, 1, 1.5, 2, 3, 4, 6, 8, 12, 16, 24, 36):
                c = amp * (math.exp(-0.14 * h) - math.exp(-1.5 * h))
                rows.append(
                    dict(
                        study_id=study.study_id,
                        subject_id=a["subject_id"],
                        sequence=a["sequence"],
                        period=a["period"],
                        treatment=a["treatment"],
                        dose_datetime=dose.isoformat(),
                        sample_datetime=(dose + timedelta(hours=h)).isoformat(),
                        nominal_time_h=h,
                        actual_time_h=h,
                        concentration=0 if c < 0.2 else c,
                        concentration_unit="ng/mL",
                        blq_flag=c < 0.2,
                        lloq=0.2,
                        sample_id=f"{a['subject_id']}_P{a['period']}_H{h}",
                        analyte="parent",
                        source_batch="SYNTHETIC_QA",
                        sample_status="BLQ" if c < 0.2 else "VALID",
                    )
                )
        content = pd.DataFrame(rows).to_csv(index=False).encode()
        project = (
            Project(study=study)
            .with_allocation(allocation.to_dict("records"), meta)
            .import_raw(content, "SYNTHETIC_" + label + ".csv")
        )
        project = run_analysis(project.freeze())
        run = project.runs[-1]
        check(
            "Pipeline " + label + " current, 36 subjects, demo study gated",
            result_status(project) == "CURRENT"
            and len(run["nca"]) == 36 * len(allocation.sequence.iloc[0])
            and run["study_decision"] == "NOT EVALUABLE",
        )
        (OUT / ("PIPELINE_" + label + ".beproject.zip")).write_bytes(export_archive(project))
        pipeline.append(
            dict(
                case=label,
                design=design,
                profiles=len(run["nca"]),
                study_decision=run["study_decision"],
                endpoint_decisions={r["endpoint"]: r["decision"] for r in run["be"]},
                blockers=run["blockers"],
            )
        )
    evidence = dict(
        checks=checks,
        passed=sum(x["passed"] for x in checks),
        failed=sum(not x["passed"] for x in checks),
        qc_mutations=qc_rows,
        pipeline=pipeline,
    )
    (OUT / "verification.json").write_text(
        json.dumps(evidence, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "passed": evidence["passed"],
                "failed": evidence["failed"],
                "failed_checks": [x for x in checks if not x["passed"]],
                "pipeline": pipeline,
            },
            ensure_ascii=True,
            indent=2,
        )
    )
    if evidence["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
