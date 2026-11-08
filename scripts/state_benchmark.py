"""Measure state/UI boundary work on identical synthetic inputs; no network needed."""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from be_app.examples import demo_project


def measure(operation, repeats=3):
    times = []
    for _ in range(repeats):
        start = time.perf_counter()
        operation()
        times.append(time.perf_counter() - start)
    return dict(samples_s=times, median_s=sorted(times)[len(times) // 2])


def baseline():
    output = {}
    for label, n in [("small", 12), ("large", 240)]:
        project = demo_project(n=n)
        output[label] = dict(
            subjects=n,
            records=len(project.raw_frame()),
            qc_navigation=measure(project.qc),
            input_fingerprint_render=measure(project.input_hash),
            raw_preview=measure(project.raw_frame),
            full_nca_calls_on_navigation=0,
            qc_calls_on_three_reruns=3,
        )
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["before", "after"], default="before")
    args = parser.parse_args()
    if args.phase == "before":
        results = baseline()
    else:
        from be_app.state import benchmark_state

        results = benchmark_state(measure)
        before = json.loads(Path("docs/state_performance_before.json").read_text(encoding="utf-8"))
        for label, result in results.items():
            limit = before[label]["qc_navigation"]["median_s"] * 0.1
            result["acceptance"] = dict(
                warm_qc_limit_s=limit,
                passed=result["qc_navigation"]["median_s"] < limit
                and result["qc_calls_on_three_reruns"] == 0
                and result["full_nca_calls_on_navigation"] == 0,
                basis="Warm data-access path <10% of measured prior full-QC path on this host; excludes browser rendering",
            )
    output = Path(f"docs/state_performance_{args.phase}.json")
    output.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))
    if args.phase == "after" and not all(item["acceptance"]["passed"] for item in results.values()):
        sys.exit(1)
