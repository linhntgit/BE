"""Index reproducible test evidence and source hashes for an implementation review."""

import argparse
import csv
import hashlib
import json
import platform
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def identity(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--junit", type=Path, required=True)
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    junit, benchmark = args.junit.resolve(), args.benchmark.resolve()
    xml_root = ET.parse(junit).getroot()  # noqa: S314 - local pytest-generated evidence
    # Count each suite once: nested suites already contribute to the parent totals.
    suites = [xml_root] if xml_root.tag == "testsuite" else xml_root.findall("testsuite")
    if not suites:
        raise ValueError("JUnit contains no test suites")
    tests = {field: sum(int(item.get(field, 0)) for item in suites)
             for field in ("tests", "failures", "errors", "skipped")}
    if tests["tests"] == 0 or tests["failures"] or tests["errors"]:
        raise ValueError(f"JUnit is not a clean completed run: {tests}")

    with benchmark.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    passed = sum(str(row.get("passed", "")).casefold() == "true" for row in rows)
    if not rows or passed != len(rows):
        raise ValueError(f"Benchmark not complete: {passed}/{len(rows)} passed")

    source_paths = sorted({
        *ROOT.glob("be_app/**/*.py"),
        *ROOT.glob("tests/**/*.py"),
        *ROOT.glob("tests/fixtures/**/*"),
        *ROOT.glob("scripts/**/*.py"),
        *ROOT.glob("scripts/**/*.cjs"),
        *ROOT.glob(".streamlit/**/*.toml"),
        *ROOT.glob(".github/workflows/*.yml"),
        ROOT / "app.py",
        ROOT / "pyproject.toml",
        ROOT / "uv.lock",
        ROOT / "requirements.lock",
        ROOT / "README.md",
        ROOT / "docs" / "CAPABILITY_MATRIX.md",
    })
    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "purpose": "Technical implementation evidence; scientific qualification and visual browser UAT remain separate gates",
        "python": sys.version,
        "platform": platform.platform(),
        "checks": {"pytest": tests, "benchmark": {"passed": passed, "total": len(rows)}},
        "evidence": [identity(junit), identity(benchmark)],
        "source_hashes": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in source_paths if p.is_file()},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Verified {tests['tests']} pytest cases and {passed}/{len(rows)} benchmark cases: {args.output}")


if __name__ == "__main__":
    main()
