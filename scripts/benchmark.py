"""Offline golden comparison; emit machine-readable evidence and fail on any mismatch."""

import argparse
import csv
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from be_app.design import tost_power
from be_app.domain import NcaConfig
from be_app.nca import analyze_profile
from be_app.statistics import analyze_abe


def benchmark() -> list[dict]:
    fixtures = Path(__file__).resolve().parents[1] / "tests" / "fixtures"
    gold = json.loads((fixtures / "golden.json").read_text(encoding="utf-8"))
    rows = []

    def record(fixture, design, endpoint, expected, actual, tolerance, source):
        difference = abs(actual - expected)
        rows.append(
            dict(
                fixture=fixture,
                design=design,
                jurisdiction="EMA/FDA ABE",
                endpoint=endpoint,
                expected=expected,
                actual=actual,
                absolute_difference=difference,
                relative_difference=difference / abs(expected) if expected else 0,
                tolerance=tolerance,
                source=source,
                passed=difference <= tolerance,
            )
        )

    for item in gold["power"]:
        actual = tost_power(item["cv"], item["gmr"], item["n1"], item["n2"], item["design"])
        record(
            f"PowerTOST_n{item['n1'] + item['n2']}",
            item["design"],
            "power",
            item["expected"],
            actual,
            item["tolerance"],
            gold["power_source"],
        )
    data = pd.read_csv(fixtures / "BE_NCAResult4BE.csv").rename(
        columns={
            "SUBJ": "subject_id",
            "GRP": "sequence",
            "PRD": "period",
            "TRT": "treatment",
            "AUClast": "auc_last",
            "Cmax": "cmax",
        }
    )
    for item in gold["abe"]:
        result = analyze_abe(data, item["endpoint"], "2x2")
        for metric in ("gmr", "ci_lower", "ci_upper"):
            record(
                "BE_R_NCAResult4BE",
                "2x2 unbalanced 16/17",
                f"{item['endpoint']}.{metric}",
                item[metric],
                getattr(result, metric),
                gold["abe_tolerance"],
                gold["abe_source"],
            )
        record(
            "BE_R_NCAResult4BE",
            "2x2 unbalanced 16/17",
            f"{item['endpoint']}.MSE",
            item["mse"],
            result.diagnostics["mse"],
            5e-9,
            gold["abe_source"],
        )
    item = gold["pknca"]
    result = analyze_profile(
        pd.DataFrame(
            dict(
                actual_time_h=item["times"],
                concentration=item["concentrations"],
                blq_flag=[x == 0 for x in item["concentrations"]],
            )
        )
    )
    for metric in ("auc_last", "cmax", "tmax", "clast", "tlast"):
        record(
            "PKNCA_vignette",
            "single dose",
            metric,
            item[metric],
            result[metric],
            item["tolerance"],
            item["source"],
        )
    compatible = analyze_profile(
        pd.DataFrame(
            dict(
                actual_time_h=item["times"],
                concentration=item["concentrations"],
                blq_flag=[x == 0 for x in item["concentrations"]],
            )
        ),
        NcaConfig(terminal_min_adj_r2=0, terminal_min_span_half_lives=0),
    )
    for metric in ("lambda_z", "half_life", "auc_inf"):
        record(
            "PKNCA_vignette_matching_terminal_policy",
            "single dose",
            metric,
            item[metric],
            compatible[metric],
            item["tolerance"],
            item["source"],
        )
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="docs/benchmark_results.csv")
    args = parser.parse_args()
    rows = benchmark()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    passed = sum(row["passed"] for row in rows)
    print(f"Golden benchmark: {passed}/{len(rows)} passed. Evidence: {output}")
    sys.exit(0 if passed == len(rows) else 1)
