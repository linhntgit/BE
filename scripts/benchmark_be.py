"""Recompute Phoenix mixed-model BE from observed PK and export comparison evidence."""

import argparse
import json
from pathlib import Path

from tests.legacy_benchmarks.phoenix_be import be_comparison_workbook, compare_phoenix_be, read_phoenix_be


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("Bioequivalence_Fasted.xlsx"))
    parser.add_argument("--output-dir", type=Path, default=Path("output/phoenix_be"))
    args = parser.parse_args()
    data, expected, provenance = read_phoenix_be(args.source.read_bytes(), args.source.name)
    results, checks = compare_phoenix_be(data, expected)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "BE_Fasted_App_vs_Phoenix.xlsx").write_bytes(
        be_comparison_workbook(results, data=data, metadata=provenance, comparison=checks)
    )
    summary = {
        **provenance,
        "statistics_compared": len(checks),
        "matched": int(checks.Match.sum()),
        "max_absolute_difference": float(checks["Abs difference"].max()),
        "tolerances": "CI percent: abs 1e-4 percentage point; other values abs 1e-5; all values rel 1e-7",
        "endpoints": [
            {
                "endpoint": r.endpoint,
                "n_subjects": r.n,
                "n_observations": r.n_observations,
                "missing_observations": r.n_excluded,
                "gmr": r.gmr,
                "ci90": [r.ci_lower, r.ci_upper],
                "df": r.df,
                "decision": r.decision,
            }
            for r in results
        ],
    }
    (args.output_dir / "comparison_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if not checks.Match.all():
        raise SystemExit("Differences outside declared tolerances. Inspect comparison workbook.")


if __name__ == "__main__":
    main()
