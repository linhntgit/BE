"""Audit two independent saved Phoenix fits; never authorize production inference.

Input transformations are explicit from saved mappings/settings. Fits finish before
expected tables are read. Commercial inputs and generated results stay in output/.
"""

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from be_app.replicate_abe_experimental import MODEL_ID, ReplicateLikelihood, fit_full_replicate_abe

# Declared in FDA_REPLICATE_ABE_METHOD_SPEC.md before fitting the second case.
TOLERANCES = {
    "estimate": (1e-7, 1e-6),
    "covariance": (1e-7, 1e-5),
    "df": (1e-4, 1e-5),
    "hessian": (1e-3, 1e-5),
    "likelihood": (1e-7, 1e-6),
}
NTI_WORKFLOW = "Workflow.Criterion2_ABE_DO NOT MODIFY."
CASES = {
    "nti": ("fda_nti", NTI_WORKFLOW + "Bioequivalence.",
            NTI_WORKFLOW + "Dataset for ABE analysis.Data.csv"),
    "basic": ("basic_replicate", "Workflow.Bioequivalence.",
              "Workflow.Bioequivalence.Main (Data 2x4).csv"),
}


def load_input(root, case):
    folder, _, name = CASES[case]
    data = pd.read_csv(root / folder / name, dtype={"Subject": str})
    data = data.rename(columns={"Subject": "subject_id", "Period": "period"})
    if case == "nti":
        if not (data.Reference_Name.eq("R") & data.Trans_Flag.eq("Y") & data.Design_Flag.eq("F")).all():
            raise ValueError("NTI input flags differ from audited full4/already-Ln mappings.")
        data["sequence"] = data.Sequence.map({1: "TRTR", 2: "RTRT"})
        data["treatment"] = data.Formulation.map({"R": "R", "T": "T"})
        data["parameter"] = np.exp(data.Data)  # Already Ln; invert once for prototype's raw API.
    else:
        data["sequence"] = data.Sequence.map({"CTCT": "RTRT", "TCTC": "TRTR"})
        data["treatment"] = data.Formulation.map({"Capsule": "R", "Tablet": "T"})
        data["parameter"] = data.AUClast  # Raw; settings explicitly request Ln(x).
    return data


def check_settings(root, case):
    folder, prefix, _ = CASES[case]
    settings = (root / folder / (prefix + "Settings.txt")).read_text(encoding="utf-8-sig")
    required = [
        "Model Specification: Sequence+Formulation+Period",
        "Number of Factors: 2", "Type Index: 8", "Type Index: 0",
        "Degrees of Freedom: satterthwaite",
        "Reference Value: " + ("R" if case == "nti" else "Capsule"),
        "Transformation: " + ("Already Ln-transformed" if case == "nti" else "Ln(x)"),
    ]
    for text in required:
        if text not in settings:
            raise ValueError(f"Unreviewed settings for {case}: missing {text!r}")


def compare_case(root, case):
    check_settings(root, case)
    data = load_input(root, case)
    fit = fit_full_replicate_abe(data, "parameter")
    # The independent oracle is first read AFTER the estimator has returned.
    folder, prefix, _ = CASES[case]

    def read(suffix):
        return pd.read_csv(root / folder / (prefix + suffix))

    average = read("Average Bioequivalence.csv").iloc[0]
    fixed = read("Final Fixed Parameters.csv").set_index("Effect_Level")
    variance = read("Final Variance Parameters.csv").set_index("Parameter").Estimate
    diagnostics = read("Diagnostics.csv").set_index("Diagnostic").Value
    rows = []

    def check(statistic, actual, expected, kind="estimate", *, comparable=True, note=""):
        actual, expected = float(actual), float(expected)
        absolute, relative = TOLERANCES[kind]
        rows.append(dict(
            case=case, statistic=statistic, prototype=actual, phoenix=expected,
            absolute_difference=abs(actual - expected), absolute_tolerance=absolute,
            relative_tolerance=relative,
            matched=math.isclose(actual, expected, abs_tol=absolute, rel_tol=relative),
            comparable=comparable, note=note,
        ))

    for key, column, kind in (("estimate", "Difference", "estimate"),
                              ("se", "Diff_SE", "estimate"), ("df", "Diff_DF", "df")):
        check(key, fit[key], average[column], kind)
    for statistic, value, column in (
        ("GMR", fit["gmr"], "Ratio_%Ref_"),
        ("CI90 lower", fit["ci90"][0], "CI_90_Lower"),
        ("CI90 upper", fit["ci90"][1], "CI_90_Upper"),
    ):
        check(statistic, value, average[column] / 100)
    factors = [float(variance[name]) for name in
               ("lambda(1,1)_11", "lambda(1,2)_11", "lambda(2,2)_11")]
    a, b, c = factors
    expected_g = np.array([[a * a, a * b], [a * b, b * b + c * c]])
    for i, j in ((0, 0), (0, 1), (1, 1)):
        check(f"G[{i},{j}] R,T", fit["random_covariance"][i][j], expected_g[i, j], "covariance")
    for treatment, suffix in (("r", "21"), ("t", "22")):
        check(f"residual variance {treatment.upper()}", fit[f"residual_variance_{treatment}"],
              variance[f"Var(Period*Formulation*Subject)_{suffix}"], "covariance")

    # Rebase the fixed design to each saved table's reference sequence/treatment.
    # NTI: baseline Sequence:2/T; basic: baseline TCTC/Tablet.
    contrasts = np.eye(6)
    contrasts[0, 5] = 1
    if case == "basic":
        contrasts[0, 1] = 1
        contrasts[1, 1] = -1
    contrasts[5, 5] = -1
    labels = ["int", "Sequence:" + ("1" if case == "nti" else "CTCT"),
              "Period:1", "Period:2", "Period:3",
              "Formulation:" + ("R" if case == "nti" else "Capsule")]
    beta, cov = np.array(fit["fixed_parameters"]), np.array(fit["fixed_covariance"])
    for label, contrast in zip(labels, contrasts, strict=True):
        check("fixed " + label, contrast @ beta, fixed.loc[label, "Estimate"])
        check("fixed SE " + label, math.sqrt(contrast @ cov @ contrast), fixed.loc[label, "StdError"])

    # Phoenix eigenvalues use raw residual variances rather than log variances.
    model = ReplicateLikelihood(data, "parameter")
    state = model.evaluate(fit["fitted_parameters"], information=True)
    rr, rt = fit["residual_variance_r"], fit["residual_variance_t"]
    jacobian = np.diag([1, 1, 1, 1 / rr, 1 / rt])
    raw_hessian = jacobian @ state["hessian"] @ jacobian
    raw_hessian[3, 3] -= state["gradient"][3] / rr**2
    raw_hessian[4, 4] -= state["gradient"][4] / rt**2
    eigenvalues = np.linalg.eigvalsh(raw_hessian)[::-1]
    for index, value in enumerate(eigenvalues, 1):
        check(f"observed Hessian eigenvalue {index}", value,
              diagnostics[f"Hessian eigenvalues #{index}"], "hessian")
    ll = float(diagnostics["REML log(likelihood)"])
    check("REML log-likelihood exact constant", fit["reml_log_likelihood"], ll, "likelihood",
          comparable=False, note="Constant-normalization difference retained; see diagnostic replay.")
    replay = fit["reml_log_likelihood"] - 0.5 * (len(data) - 6) * (1.837878 - math.log(2 * math.pi))
    check("REML rounded-constant diagnostic replay", replay, ll, "likelihood",
          note="Numerical inference only: 1.837878 reproduces saved values; estimator retains exact log(2*pi).")
    check("observations used", fit["n_observations"], diagnostics["Observations Used"])
    fit["sequence_subject_counts"] = data.groupby("sequence").subject_id.nunique().to_dict()
    return rows, fit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=Path("output/phoenix_replicate_reference"))
    parser.add_argument("--output-dir", type=Path, default=Path("output/replicate_abe_experimental"))
    args = parser.parse_args()
    rows, fits = [], {}
    for case in CASES:
        checks, fits[case] = compare_case(args.source_dir, case)
        rows.extend(checks)
    inventory = json.loads(Path("docs/phoenix_survey/inventory.json").read_text(encoding="utf-8"))
    projects = []
    for item in inventory["files"]:
        if item["name"] in ("Bioequivalence_replicated.phxproj", "FDA RSABE NTID Template Project_v1_0.phxproj"):
            path = Path(inventory["source_directory"]) / item["name"]
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != item["sha256"]:
                raise ValueError("Source project changed: " + item["name"])
            projects.append(dict(name=item["name"], sha256=digest, unchanged_since_survey=True))
    files = sorted(p for folder, _, _ in CASES.values()
                   for p in (args.source_dir / folder).rglob("*") if p.is_file())
    provenance = dict(
        compared_at=datetime.now(timezone.utc).isoformat(), model_id=MODEL_ID,
        expected_values_used_in_fits=False, export_host_build="8.8.0.20523",
        saved_output_builds=["8.3.2.116", "8.3.4.295"], reexecuted_in_export_host=False,
        source_projects=projects,
        files=[dict(path=str(p.relative_to(args.source_dir)), bytes=p.stat().st_size,
                    sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files],
        tolerances=TOLERANCES,
    )
    checks = pd.DataFrame(rows)
    summary = dict(
        status="NOT QUALIFIED; diagnostic prototype only", inference_allowed=False,
        production_connected=False, comparisons=len(checks), matched=int(checks.matched.sum()),
        comparable_matches=int((checks.matched & checks.comparable).sum()),
        comparable_checks=int(checks.comparable.sum()),
        remaining=["Both saved Phoenix cases have boundary G and balanced sequences; numerical interior/imbalance oracle is separate in pytest, not a third Phoenix case.",
                   "Boundary release policy and broader qualification remain; no new decisions enabled.",
                   "Missing/partial3 remain outside prototype scope; do not subset saved missing data."],
        provenance=provenance,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    checks.to_csv(args.output_dir / "comparisons.csv", index=False)
    for name, value in {"summary": summary, "fits": fits}.items():
        (args.output_dir / (name + ".json")).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "provenance"}, indent=2))
    if not checks.loc[checks.comparable, "matched"].all():
        raise SystemExit("Unexpected prototype differences; inspect comparisons.csv, do not loosen tolerance.")


if __name__ == "__main__":
    main()
