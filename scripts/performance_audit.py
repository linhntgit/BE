"""Profile synthetic BE state boundaries and PK artifact generation (not browser UI)."""

from __future__ import annotations

import argparse
import gc
import io
import json
import math
import sys
import time
import tracemalloc
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from be_app.examples import demo_project
from be_app.pk_analysis import PKSettings, analyze_nca
from be_app.pk_records import create_snapshot, excel_report, pdf_report, word_report
from be_app.state import ProjectState


def timed(fn):
    """Wall time and peak tracked Python allocations for one local operation."""
    gc.collect()
    tracemalloc.start()
    started = time.perf_counter()
    try:
        value = fn()
        elapsed = time.perf_counter() - started
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return {"seconds": round(elapsed, 6), "python_peak_mib": round(peak / (1024**2), 3)}, value


def state_case(n):
    creation, project = timed(lambda: demo_project(n=n))
    creation_state, state = timed(lambda: ProjectState(project))
    cold, _ = timed(state.qc)
    warm = [timed(state.qc)[0] for _ in range(3)]
    preview, frame = timed(state.raw_frame)
    fingerprint, _ = timed(lambda: state.project.input_fingerprint)
    return {
        "subjects": n,
        "raw_rows": len(frame),
        "project_generation": creation,
        "state_initialization": creation_state,
        "qc_first": cold,
        "qc_repeats": warm,
        "raw_frame": preview,
        "input_fingerprint": fingerprint,
        "qc_calls_after_repeats": state.metrics["qc_calls"],
    }


def synthetic_pk_snapshot(n):
    """Construct deterministic mock concentration profiles with no patient information."""
    cfg = PKSettings(route="oral", dose=100.0)
    times = [0.0, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0,
             8.0, 12.0, 16.0, 24.0, 36.0]
    records, nca = [], []
    for index in range(n):
        profile_id = f"MOCK_{index + 1:04d}"
        scale = 1 + 0.02 * (index % 7)
        rows = [{"profile_id": profile_id, "time_h": t,
                 "concentration": round(100 * scale * (math.exp(-0.15*t) - math.exp(-1.5*t)), 8),
                 "blq": t == 0.0} for t in times]
        frame = pd.DataFrame(rows)
        records.extend(rows)
        nca.append(analyze_nca(frame, cfg))
    return create_snapshot(pd.DataFrame(records), asdict(cfg), nca, [], [],
                           "SYNTHETIC PERFORMANCE FIXTURE - NO PATIENT DATA")


def check_artifact(kind, payload, n):
    if kind == "xlsx":
        from openpyxl import load_workbook

        workbook = load_workbook(io.BytesIO(payload), read_only=True)
        try:
            if not {"NCA", "Du_lieu", "Cau_hinh"}.issubset(workbook.sheetnames):
                raise ValueError("Excel artifact is missing required sheets")
            rows = workbook["Du_lieu"].max_row
            if rows != n * 14 + 1:
                raise ValueError(f"Excel row mismatch: expected {n * 14 + 1}, got {rows}")
            return {"rows": rows, "sheets": len(workbook.sheetnames)}
        finally:
            workbook.close()
    if kind == "docx":
        from docx import Document

        document = Document(io.BytesIO(payload))
        body = "\n".join(p.text for p in document.paragraphs)
        if "PHÂN TÍCH DƯỢC ĐỘNG HỌC" not in body or "Tài liệu tham khảo" not in body:
            raise ValueError("Word report is missing the title or references")
        return {"tables": len(document.tables), "paragraphs": len(document.paragraphs)}
    if kind == "pdf":
        import pymupdf

        with pymupdf.open(stream=payload, filetype="pdf") as document:
            text = "\n".join(page.get_text() for page in document)
            if "PHÂN TÍCH" not in text or "Tài liệu tham khảo" not in text:
                raise ValueError("PDF report is missing the Vietnamese title or references")
            if not all(page.rect.width > 500 for page in document):
                raise ValueError("PDF contains unexpected page geometry")
            return {"pages": len(document), "text_characters": len(text)}
    raise ValueError(f"Unknown artifact: {kind}")


def report_case(n, sample_dir: Path | None):
    preparation, snapshot = timed(lambda: synthetic_pk_snapshot(n))
    result = {"profiles": n, "raw_rows": len(snapshot["data"]), "snapshot_preparation": preparation}
    for kind, exporter in (("xlsx", excel_report), ("docx", word_report), ("pdf", pdf_report)):
        performance, data = timed(lambda exporter=exporter: exporter(snapshot))
        validation = check_artifact(kind, data, n)
        result[kind] = {**performance, "bytes": len(data), "validation": validation}
        if sample_dir is not None:
            sample_dir.mkdir(parents=True, exist_ok=True)
            (sample_dir / f"synthetic_pk_{n}.{kind}").write_bytes(data)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", default="12,60,240", help="BE state subjects")
    parser.add_argument("--report-sizes", default="12,60", help="PK synthetic profile counts")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sample-dir", type=Path, help="Save synthetic reports for visual inspection")
    args = parser.parse_args()
    sizes = [int(value) for value in args.sizes.split(",")]
    report_sizes = [int(value) for value in args.report_sizes.split(",")]
    if not sizes or not report_sizes or any(value < 1 or value > 1000 for value in sizes + report_sizes):
        parser.error("Sizes must be between 1 and 1000")
    result = {
        "scope": "Synthetic local Python boundary only; excludes Streamlit first paint, browser rerun, RSS and Word pagination",
        "measurement": "Wall-clock seconds and tracemalloc peak of tracked Python allocations per operation",
        "state": [], "reports": [],
    }
    for n in sizes:
        item = state_case(n)
        result["state"].append(item)
        print(f"State: {n} subjects, first QC {item['qc_first']['seconds']}s")
    for index, n in enumerate(report_sizes):
        item = report_case(n, args.sample_dir if index == 0 else None)
        result["reports"].append(item)
        print(f"Reports: {n} profiles, PDF {item['pdf']['seconds']}s, {item['pdf']['validation']['pages']} pages")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Evidence: {args.output}")


if __name__ == "__main__":
    main()
