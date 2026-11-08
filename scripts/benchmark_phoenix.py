"""Recompute measured profiles and export a traceable Phoenix comparison snapshot."""

import argparse
import json
from pathlib import Path

from tests.legacy_benchmarks.phoenix_nca import analyze_reference, nca_workbook, read_phoenix_reference


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("NCA_Fasted.xlsx"))
    parser.add_argument("--output-dir", type=Path, default=Path("output/phoenix_nca"))
    args = parser.parse_args()
    reference = read_phoenix_reference(args.source.read_bytes(), args.source.name)
    results, comparison = analyze_reference(reference)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    path = args.output_dir / "NCA_Fasted_App_vs_Phoenix.xlsx"
    path.write_bytes(nca_workbook(results, metadata=reference.provenance, comparison=comparison))
    summary = dict(
        **reference.provenance,
        profiles=len(results),
        samples=sum(r["n_samples"] for r in results),
        parameters_per_profile=41,
        comparisons=len(comparison),
        matched=int(comparison.Match.sum()),
        both_missing=int(comparison["Both missing"].sum()),
        terminal_estimated=sum(r["lambda_z"] is not None for r in results),
        max_absolute_difference=float(comparison["Abs difference"].max()),
        relative_tolerance=1e-9,
        absolute_tolerance=1e-8,
    )
    (args.output_dir / "comparison_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if not comparison.Match.all():
        raise SystemExit("Phoenix comparison contains differences. See workbook.")


if __name__ == "__main__":
    main()
