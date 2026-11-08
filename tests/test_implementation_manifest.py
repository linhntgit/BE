"""Manifest gates must reject incomplete evidence before writing review artifacts."""

import hashlib
import json
import sys

import pytest

from scripts import implementation_manifest as manifest


def invoke(monkeypatch, root, junit, benchmark, *, output=None):
    monkeypatch.setattr(manifest, "ROOT", root)
    dest = output or root / "evidence" / "manifest.json"
    monkeypatch.setattr(sys, "argv", ["manifest", "--junit", str(junit),
                                      "--benchmark", str(benchmark),
                                      "--output", str(dest)])
    manifest.main()
    return dest


def make_evidence(root, junit_text, benchmark_text):
    folder = root / "evidence"
    folder.mkdir()
    junit = folder / "results.xml"
    benchmark = folder / "bench.csv"
    junit.write_text(junit_text, encoding="utf-8")
    benchmark.write_text(benchmark_text, encoding="utf-8")
    return junit, benchmark


def test_manifest_records_source_and_evidence_hashes(monkeypatch, tmp_path):
    source = tmp_path / "be_app" / "example.py"
    source.parent.mkdir()
    source.write_text("VERSION = 1\n", encoding="utf-8")
    junit, benchmark = make_evidence(
        tmp_path,
        '<testsuites><testsuite tests="2" failures="0" errors="0" skipped="1"/></testsuites>',
        "case,passed\nexample,TRUE\nedge,true\n",
    )
    dest = invoke(monkeypatch, tmp_path, junit, benchmark)
    result = json.loads(dest.read_text(encoding="utf-8"))
    assert result["checks"] == {
        "pytest": {"tests": 2, "failures": 0, "errors": 0, "skipped": 1},
        "benchmark": {"passed": 2, "total": 2},
    }
    hashes = {item["path"]: item["sha256"] for item in result["evidence"]}
    assert hashes["evidence/results.xml"] == hashlib.sha256(junit.read_bytes()).hexdigest()
    assert hashes["evidence/bench.csv"] == hashlib.sha256(benchmark.read_bytes()).hexdigest()
    assert result["source_hashes"]["be_app/example.py"] == hashlib.sha256(source.read_bytes()).hexdigest()
    script = tmp_path / "scripts" / "performance_audit.py"
    script.parent.mkdir(exist_ok=True)
    script.write_text("print('synthetic')\n", encoding="utf-8")
    # The source inventory must also cover benchmark and QA scripts.
    assert "scripts/performance_audit.py" in json.loads(
        invoke(monkeypatch, tmp_path, junit, benchmark).read_text(encoding="utf-8")
    )["source_hashes"]


def test_nested_junit_suites_not_double_counted(monkeypatch, tmp_path):
    junit, benchmark = make_evidence(
        tmp_path,
        '<testsuite tests="2" failures="0" errors="0">'
        '<testsuite tests="2" failures="0" errors="0"/></testsuite>',
        "case,passed\nexample,true\n",
    )
    result = json.loads(invoke(monkeypatch, tmp_path, junit, benchmark).read_text())
    assert result["checks"]["pytest"]["tests"] == 2


@pytest.mark.parametrize("junit_text,bench_text,expected", [
    ('<testsuites><testsuite tests="2" failures="1"/></testsuites>',
     "case,passed\nexample,true\n", "JUnit is not a clean"),
    ('<testsuite tests="2" errors="1"/>',
     "case,passed\nexample,true\n", "JUnit is not a clean"),
    ('<testsuite tests="0"/>',
     "case,passed\nexample,true\n", "JUnit is not a clean"),
    ('<testsuites/>',
     "case,passed\nexample,true\n", "JUnit contains no test suites"),
    ('<testsuite tests="2"/>',
     "case,passed\nexample,false\n", "Benchmark not complete"),
    ('<testsuite tests="2"/>',
     "case,passed\nexample,true\nedge,false\n", "Benchmark not complete"),
    ('<testsuite tests="2"/>',
     "case,passed\n", "Benchmark not complete"),
])
def test_manifest_rejects_incomplete_evidence_without_output(
    monkeypatch, tmp_path, junit_text, bench_text, expected
):
    junit, benchmark = make_evidence(tmp_path, junit_text, bench_text)
    dest = tmp_path / "evidence" / "manifest.json"
    with pytest.raises(ValueError, match=expected):
        invoke(monkeypatch, tmp_path, junit, benchmark, output=dest)
    assert not dest.exists()
