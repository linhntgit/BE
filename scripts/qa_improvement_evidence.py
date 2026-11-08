"""Create a dated, reviewable evidence index for the 2026-10-31 synthetic QA.

This script does not qualify any statistical method or alter study data. It
checks the existing QA results and renders current bilingual draft reports from
a newly generated deterministic synthetic project.
"""

import argparse
import hashlib
import io
import json
import tomllib
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import pymupdf
from docx import Document

from be_app.examples import demo_project
from be_app.pipeline import run_analysis
from be_app.reporting import docx_report, pdf_report

ROOT = Path(__file__).resolve().parents[1]
QA = ROOT / "output" / "qa_20261031"
REPORT = QA / "improved_report_current"
TEST_XML = QA / "improvement_pytest.xml"
BROWSER_PROOF = ROOT / ".cache" / "browser-cdp-smoke" / "proof.json"
MANIFEST = QA / "improvement_evidence_20261031.json"
VISUAL_REVIEW = QA / "pdf_visual_review_20261031.json"


def record(path: Path) -> dict:
    payload = path.read_bytes()
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def require(condition: bool, description: str) -> None:
    if not condition:
        raise ValueError(f"QA evidence requirement failed: {description}")


def pytest_summary(path: Path) -> dict:
    # This is the XML written locally by the immediately preceding pytest run.
    xml = ET.parse(path).getroot()  # noqa: S314
    suites = [xml] if xml.tag == "testsuite" else list(xml.iter("testsuite"))
    if xml.tag == "testsuites" and xml.attrib.get("tests"):
        suites = [xml]
    return {
        "tests": sum(int(item.attrib.get("tests", 0)) for item in suites),
        "failures": sum(int(item.attrib.get("failures", 0)) for item in suites),
        "errors": sum(int(item.attrib.get("errors", 0)) for item in suites),
        "skipped": sum(int(item.attrib.get("skipped", 0)) for item in suites),
    }


def render_current_reports() -> tuple[list[dict], dict]:
    REPORT.mkdir(parents=True, exist_ok=True)
    project = run_analysis(demo_project(seed=241029).freeze())
    require(project.runs[-1]["study_decision"] == "NOT EVALUABLE", "synthetic study remains gated")
    require(project.study.data_purpose == "training_qa", "explicit synthetic data purpose")
    files = []
    visual = {}
    for language in ("vi", "en"):
        docx_data = docx_report(project, language=language)
        doc = Document(io.BytesIO(docx_data))
        body = " ".join(p.text for p in doc.paragraphs)
        require(len(doc.tables) == 8, f"{language} DOCX reviewer tables")
        require("DRAFT / NOT REGULATORY-READY" in body, f"{language} DOCX draft watermark")
        require("{\"integration\"" not in body, f"{language} DOCX readable methods")
        if language == "en":
            require("Training/QA or synthetic data" in body, "English blocker is localized")
            require("SYNTHETIC LEARNING DATA — FOR TRAINING ONLY" in body, "English demo banner")
            require("TRAINING-QA DATA — NO REAL-STUDY CONCLUSION" in body, "English QA banner")
            require("DỮ LIỆU GIẢ LẬP HỌC THỬ" not in body, "English has no Vietnamese demo banner")
        docx_path = REPORT / f"draft_{language}.docx"
        docx_path.write_bytes(docx_data)
        files.append(record(docx_path))

        pdf_data = pdf_report(project, language=language)
        pdf = pymupdf.open(stream=pdf_data, filetype="pdf")
        pdf_text = " ".join(page.get_text() for page in pdf)
        require("DRAFT / NOT REGULATORY-READY" in pdf_text, f"{language} PDF draft watermark")
        require("{\"integration\"" not in pdf_text, f"{language} PDF readable methods")
        if language == "en":
            require("SYNTHETIC LEARNING DATA — FOR TRAINING ONLY" in pdf_text, "English PDF demo banner")
            require("TRAINING-QA DATA — NO REAL-STUDY CONCLUSION" in pdf_text, "English PDF QA banner")
            require("DỮ LIỆU GIẢ LẬP HỌC THỬ" not in pdf_text, "English PDF banner localization")
        require(len(pdf) >= 1, f"{language} PDF has pages")
        pdf_path = REPORT / f"draft_{language}.pdf"
        pdf_path.write_bytes(pdf_data)
        files.append(record(pdf_path))
        visual[language] = {"pages": len(pdf), "docx_tables": len(doc.tables), "pdf_text_extracted": True}
        pdf.close()
    return files, {
        "synthetic_seed": 241029,
        "study_decision": project.runs[-1]["study_decision"],
        "snapshot_hash": project.runs[-1]["snapshot_hash"],
        "input_fingerprint": project.runs[-1]["input_hash"],
        "programmatic_check": visual,
        "word_visual_layout_review": "pending",
        "pdf_visual_layout_review": "pending",
    }


def main() -> None:
    verification = json.loads((QA / "verification.json").read_text(encoding="utf-8"))
    proof = json.loads(BROWSER_PROOF.read_text(encoding="utf-8"))
    tests = pytest_summary(TEST_XML)
    require(verification["passed"] == len(verification["checks"]), "scenario check count")
    require(verification["failed"] == 0 and all(item["passed"] for item in verification["checks"]),
            "all scenario checks pass")
    require(proof["passed"] is True and proof["stage"] == "Completed", "browser smoke completed")
    require(tests["tests"] > 0 and tests["failures"] == 0 and tests["errors"] == 0,
            "pytest execution passed")
    require(proof["studyDecision"] == "NOT EVALUABLE (demo/QA)", "browser demo decision gate")

    reports, report_check = render_current_reports()
    version = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    sources = [
        ROOT / "requirements.lock", ROOT / "uv.lock", ROOT / "pyproject.toml",
        QA / "scenario_results.json", QA / "scenario_summary.csv", QA / "verification.json",
        TEST_XML, BROWSER_PROOF,
    ]
    sources += sorted(QA.glob("PIPELINE_*.beproject.zip"))
    sources += sorted((ROOT / ".cache" / "browser-cdp-smoke").glob("*-1440.png"))
    sources += sorted((ROOT / ".cache" / "browser-cdp-smoke").glob("*-714.png"))
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "kind": "synthetic_product_QA_only",
        "engine_version": version,
        "regulatory_validation": False,
        "scenario_seed": 20261031,
        "scenario_verification": {
            "passed": verification["passed"], "failed": verification["failed"],
            "contains_expected_actual": True,
            "independent_regulatory_oracle": False,
        },
        "unit_integration_tests": tests,
        "browser_smoke": {
            "passed": proof["passed"], "checks": len(proof["checks"]),
            "scope": "demo creation, freeze, NCA, BE decision gate, reports, 714px/1440px",
            "full_upload_download_and_manual_page_review": False,
        },
        "current_draft_reports": report_check,
        "review": {
            "technical_reviewer": None, "statistical_reviewer": None,
            "approval_status": "PENDING", "signed_at_utc": None,
        },
        "still_unqualified": [
            "EMA_NTI_sample_size_planning", "FDA_conventional_replicate_ABE",
            "FDA_HVD_low_sWR", "FDA_NTI", "Word_visual_layout", "complete_browser_UAT",
        ],
        "artifacts": [record(p) for p in sources] + reports,
        "historical_evidence_manifest_note": "evidence_manifest.json documents pre-fix observations and is retained unchanged",
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Evidence: {MANIFEST.relative_to(ROOT)}")
    print(f"Tests: {tests}; scenarios: {verification['passed']}; browser checks: {len(proof['checks'])}")


def apply_visual_review() -> None:
    """Attach a layout review only when the reviewed PDFs still match byte-for-byte."""
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    review = json.loads(VISUAL_REVIEW.read_text(encoding="utf-8"))
    require(review["status"] == "VISUALLY_REVIEWED_FOR_LAYOUT", "explicit visual review status")
    indexed = {item["path"]: item for item in manifest["artifacts"]}
    for language in ("vi", "en"):
        path = REPORT / f"draft_{language}.pdf"
        relative = path.relative_to(ROOT).as_posix()
        require(record(path) == indexed[relative], f"{language} manifest PDF still matches on disk")
        require(review["pdf_sha256"][language] == indexed[relative]["sha256"],
                f"{language} review was performed on these exact bytes")
        require(review["pages_reviewed"][language]
                == manifest["current_draft_reports"]["programmatic_check"][language]["pages"],
                f"{language} all pages were reviewed")
    manifest["current_draft_reports"]["pdf_visual_layout_review"] = {
        "status": review["status"],
        "scope": review["scope"],
        "limitations": review["limitations"],
        "review_file": VISUAL_REVIEW.relative_to(ROOT).as_posix(),
    }
    manifest["artifacts"] = [x for x in manifest["artifacts"] if x["path"] != VISUAL_REVIEW.relative_to(ROOT).as_posix()]
    manifest["artifacts"].append(record(VISUAL_REVIEW))
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Visual layout review linked to exact PDF hashes: {MANIFEST.relative_to(ROOT)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply-visual-review", action="store_true", help="Link review for existing PDFs")
    arguments = parser.parse_args()
    apply_visual_review() if arguments.apply_visual_review else main()
