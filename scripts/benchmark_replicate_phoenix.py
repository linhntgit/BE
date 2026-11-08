"""Audit local Phoenix dependency exports; comparisons do not qualify or change methods.

Export Workflow > Dependencies for the three surveyed projects first. Saved Phoenix
outputs are references, not a re-execution of the templates in the installed build.
Commercial source data stay in the ignored output directory.
"""

import argparse
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chi2

from be_app.domain import Study
from be_app.mixed import ols, ols_test
from be_app.replicate import analyze_replicate, ema_method_a, ema_reference_variance, howe_bound
from be_app.statistics import ema_abel_limits

SEQUENCE_MAPPING = {"ABAB": "TRTR", "BABA": "RTRT", "TRTR": "TRTR", "RTRT": "RTRT"}


def read(root, name):
    return pd.read_csv(root / name)


def wide_to_long(data):
    """Invert declared natural logs once; never infer a scale from numerical values."""
    if data.Subject.isna().any() or data.Subject.duplicated().any():
        raise ValueError("Missing or duplicate subjects in wide Phoenix input")
    if not set(data.Sequence) <= set(SEQUENCE_MAPPING):
        raise ValueError("Unknown Phoenix sequence mapping")
    rows = []
    for row in data.to_dict("records"):
        sequence = SEQUENCE_MAPPING[row["Sequence"]]
        repeat = {"R": 0, "T": 0}
        for period, treatment in enumerate(sequence, 1):
            repeat[treatment] += 1
            value = row[f"LOG_DATA_{treatment}{repeat[treatment]}"]
            rows.append(
                dict(
                    subject_id=str(row["Subject"]),
                    sequence=sequence,
                    period=period,
                    treatment=treatment,
                    parameter=math.exp(value) if pd.notna(value) else np.nan,
                )
            )
    return pd.DataFrame(rows)


def sequence_fit(data, response):
    sequences = sorted(data.Sequence.unique())
    matrix = np.column_stack([data.Sequence.eq(s).to_numpy(float) for s in sequences])
    fit = ols(response, matrix)
    contrast = ols_test(fit, np.ones(len(sequences)) / len(sequences))
    return fit, contrast


def compare(root):
    rows = []
    findings = []

    def check(case, statistic, observed, expected, *, comparable=True, note=""):
        observed, expected = float(observed), float(expected)
        matched = math.isclose(observed, expected, abs_tol=1e-8, rel_tol=1e-7)
        rows.append(
            dict(
                case=case,
                statistic=statistic,
                app=observed,
                phoenix=expected,
                absolute_difference=abs(observed - expected),
                matched=matched,
                comparable_model_and_population=comparable,
                note=note,
            )
        )

    data = read(root, "Workflow.Prepare Dataset for Analysis.Dataset Ready for Analysis.Result.csv")
    data = data.rename(
        columns={
            "Subject": "subject_id",
            "Period": "period",
            "Data": "parameter",
            "Formulation_Calc": "treatment",
        }
    )
    data["sequence"] = data.Sequence.map(SEQUENCE_MAPPING)
    method = ema_method_a(data, "parameter")
    refkeys = read(root, "Workflow.Analysis.ABEL.Calculation Steps.Complete reference data.Result.csv")
    reference = data.merge(
        refkeys[["Subject", "Period"]].rename(columns={"Subject": "subject_id", "Period": "period"}),
        on=["subject_id", "period"],
        validate="one_to_one",
    )
    variance = ema_reference_variance(reference, "parameter")
    # Expected output is only read after both fits above have been calculated.
    expected = read(
        root, "Workflow.Analysis.Standard Average BE.BE Method A log.Average Bioequivalence.csv"
    ).iloc[0]
    for key, column in (("estimate", "Difference"), ("se", "Diff_SE"), ("df", "Diff_DF")):
        check("EMA Method A component", key, method["contrast"][key], expected[column])
    for key, column in (("estimate", "Ratio_%Ref_"), ("lower", "CI_90_Lower"), ("upper", "CI_90_Upper")):
        check("EMA Method A component", column, 100 * math.exp(method["contrast"][key]), expected[column])
    expected_variance = read(root, "Workflow.Analysis.ABEL.Calculation Steps.Calculate CVwr.Result.csv").iloc[
        0
    ]
    lower, upper = ema_abel_limits(variance["sd"], "cmax")
    for name, value, column in (
        ("R variance", variance["variance"], "Estimate"),
        ("CVwR %", 100 * math.sqrt(math.expm1(variance["variance"])), "CVWR"),
        ("Lower %", 100 * lower, "L"),
        ("Upper %", 100 * upper, "U"),
    ):
        check("EMA reference-only component", name, value, expected_variance[column])
    production = analyze_replicate(
        data,
        "parameter",
        Study(
            study_id="EMA_REFERENCE", title="Internal comparison", design="full4", rule_set_id="EMA_HVDP_ABEL"
        ),
    )
    if production.decision != "NOT EVALUABLE":
        raise ValueError("Missing-replicate release gate unexpectedly opened")
    findings.append(
        dict(
            case="EMA",
            status="scope_blocked",
            observations=len(data),
            subjects=int(data.subject_id.nunique()),
            complete_subjects=int(data.groupby("subject_id").size().eq(4).sum()),
            reference_subjects=int(reference.subject_id.nunique()),
            reference_observations=len(reference),
            reason="Component fits compared only. Production correctly blocks missing replicate; no subject was silently excluded.",
        )
    )

    nti_root = root / "fda_nti"
    wide = read(
        nti_root,
        "Workflow.USER_INPUT_Prepare Dataset for Analysis.Dataset Preparation_DO NOT MODIFY.Dataset ready for analysis_allPeriods.Result.csv",
    )
    nti = analyze_replicate(
        wide_to_long(wide),
        "parameter",
        Study(
            study_id="NTI_REFERENCE",
            title="Internal comparison",
            design="full4",
            rule_set_id="FDA_NTI",
            nti=True,
        ),
    )
    if nti.estimate is None:
        raise ValueError("NTI input could not be fitted")
    intermediate = read(
        nti_root,
        "Workflow.Criterion1_RSABE_DO NOT MODIFY.Prepare Data for RSABE analysis.Pointest x and boundx.Result.csv",
    ).iloc[0]
    for name, observed, column in (
        ("estimate", nti.estimate, "Estimate"),
        ("SE", nti.se, "StdError"),
        ("df", nti.df, "Denom_DF"),
        ("GMR", nti.gmr, "pointest"),
    ):
        check("FDA NTI RSABE", name, observed, intermediate[column])
    final = (
        read(nti_root, "Workflow.Criterion1_RSABE_DO NOT MODIFY.Final RSABE results.Result.csv")
        .dropna(subset=["critbound"])
        .iloc[0]
    )
    check("FDA NTI RSABE", "sWR", nti.swr, final.sWR)
    check(
        "FDA NTI RSABE",
        "UCB95 (exact vs rounded constant)",
        nti.scaled_ucb,
        final.critbound,
        comparable=False,
        note="App uses exact 1/0.9; saved Phoenix formula uses 1.11111. Tolerance is not widened.",
    )
    howe = nti.diagnostics["howe"]
    y = -((math.log(1.11111) / 0.1) ** 2) * nti.swr**2
    bound_y = y * howe["df_R"] / float(chi2.ppf(0.95, howe["df_R"]))
    replay = howe["x"] + y + math.hypot(howe["bound_x"] - howe["x"], bound_y - y)
    check("FDA NTI saved-constant diagnostic replay", "UCB95", replay, final.critbound)
    ratio = read(
        nti_root,
        "Workflow.Criterion3_Upper 90 CI_Limit_DO NOT MODIFY.Calculate Ratio.Criterion 3 Assessment.Result.csv",
    ).iloc[0]
    for name, observed, column in (
        ("sWT", nti.swt, "sWt"),
        ("SD ratio upper CI90", nti.sd_ratio_ci_upper, "Upper90CI"),
    ):
        check("FDA NTI variability", name, observed, ratio[column])
    abe = read(
        nti_root, "Workflow.Criterion2_ABE_DO NOT MODIFY.Bioequivalence.Average Bioequivalence.csv"
    ).iloc[0]
    for name, observed, column in (
        ("SE", nti.se, "Diff_SE"),
        ("df", nti.df, "Diff_DF"),
        ("CI90 lower %", 100 * nti.ci_lower, "CI_90_Lower"),
        ("CI90 upper %", 100 * nti.ci_upper, "CI_90_Upper"),
    ):
        check(
            "FDA NTI conventional ABE",
            name,
            observed,
            abe[column],
            comparable=False,
            note="Phoenix uses formulation-specific repeated variance + random formulation UN; app uses complete-subject I contrast. Method specification/independent validation required before changing the decision model.",
        )
    findings.append(
        dict(
            case="FDA NTI",
            status="abe_model_difference",
            contrast_subjects=len(wide),
            variance_subjects=len(wide),
            reason="I/D fits and variance components agree; UCB difference is explained by exact 1/0.9 vs saved 1.11111 constant. Conventional ABE is not the same estimator/df. No whole-method qualification.",
        )
    )

    hvd_root = root / "fda_hvd"
    complete = read(
        hvd_root, "Workflow.Prepare Dataset for Analysis.Dataset ready for analysis_allPeriods.Result.csv"
    )
    reference = read(
        hvd_root,
        "Workflow.RSABE.Prepare Data for RSABE analysis.Dataset ready for analysis_Rperiods.Data.csv",
    )
    fit_i, contrast = sequence_fit(
        complete,
        (complete.LOG_DATA_T1 + complete.LOG_DATA_T2 - complete.LOG_DATA_R1 - complete.LOG_DATA_R2) / 2,
    )
    fit_r, _ = sequence_fit(reference, reference.LOG_DATA_R1 - reference.LOG_DATA_R2)
    swr = math.sqrt(fit_r["mse"] / 2)
    bound = howe_bound(contrast["estimate"], contrast["se"], contrast["df"], swr, fit_r["df"])
    expected = read(
        hvd_root, "Workflow.RSABE.Prepare Data for RSABE analysis.Pointest x and boundx.Result.csv"
    ).iloc[0]
    for key, column in (("estimate", "Estimate"), ("se", "StdError"), ("df", "Denom_DF")):
        check("FDA HVD template components", key, contrast[key], expected[column])
    final = (
        read(hvd_root, "Workflow.RSABE.Final RSABE results.Result.csv").dropna(subset=["critbound"]).iloc[0]
    )
    check("FDA HVD template components", "sWR", swr, final.sWR)
    check("FDA HVD template components", "UCB95 (not selected branch)", bound["upper_95"], final.critbound)
    findings.append(
        dict(
            case="FDA HVD",
            status="not_a_scaled_branch_fixture",
            contrast_subjects=len(complete),
            reference_subjects=len(reference),
            df_contrast=fit_i["df"],
            df_reference=fit_r["df"],
            swr=swr,
            reason="Saved template chooses unscaled ABE because sWR < 0.294. I and D use different populations. Source maps logData to Data while Trans_Flag=N; saved workflow logs this again. Values are reproduced as stored, not endorsed as the correct PK transform. No complete-case subset used as a substitute for the original study.",
        )
    )
    return pd.DataFrame(rows), findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=Path("output/phoenix_replicate_reference"))
    parser.add_argument("--output-dir", type=Path, default=Path("output/phoenix_replicate_comparison"))
    args = parser.parse_args()
    checks, findings = compare(args.source_dir)
    inventory = json.loads(Path("docs/phoenix_survey/inventory.json").read_text(encoding="utf-8"))
    source_projects = []
    for item in inventory["files"]:
        if item["name"].startswith(("EMA ABEL", "FDA RSABE")):
            source = Path(inventory["source_directory"]) / item["name"]
            current_hash = hashlib.sha256(source.read_bytes()).hexdigest()
            if current_hash != item["sha256"]:
                raise ValueError("Source project changed since survey: " + item["name"])
            source_projects.append(
                {
                    "name": item["name"],
                    "bytes": item["bytes"],
                    "sha256": current_hash,
                    "unchanged_since_survey": True,
                }
            )
    files = [p for p in args.source_dir.rglob("*") if p.is_file()]
    settings = [p for p in files if p.name.endswith("Settings.txt")]
    manifest = dict(
        exported_on="2026-10-31",
        compared_at=datetime.now(timezone.utc).isoformat(),
        export_host_build="8.8.0.20523",
        reexecuted_in_export_host=False,
        saved_output_builds=sorted(
            {
                build
                for p in settings
                for build in re.findall(r"Phoenix Build ([\d.]+)", p.read_text(encoding="utf-8-sig"))
            }
        ),
        source_projects=source_projects,
        exported_files=[
            dict(
                path=str(p.relative_to(args.source_dir)),
                bytes=p.stat().st_size,
                sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
            )
            for p in sorted(files)
        ],
        tolerances=dict(absolute=1e-8, relative=1e-7),
        expected_values_used_in_fits=False,
    )
    summary = dict(
        status="NOT QUALIFIED: population, model and source-transform findings remain",
        comparisons=len(checks),
        matched=int(checks.matched.sum()),
        comparable_matches=int((checks.matched & checks.comparable_model_and_population).sum()),
        findings=findings,
        provenance=manifest,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    checks.to_csv(args.output_dir / "comparisons.csv", index=False)
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in summary.items() if k != "provenance"}, ensure_ascii=True, indent=2))
    if not checks.loc[checks.comparable_model_and_population, "matched"].all():
        raise SystemExit("Unexpected component differences: inspect comparisons.csv")


if __name__ == "__main__":
    main()
