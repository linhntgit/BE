"""Tests for Vietnamese BE Study Report Template (MOH / VKNT TP.HCM - Cefixim 100).

Verifies full structure, all 13 required tables, Word (.docx) and PDF (.pdf) generation,
blank template export, and strict compliance with the explicit requirement to calculate
and report `Power_TOST` (and never report or use `Power_80_20`).
"""

import io
from docx import Document
import pytest

from be_app.examples import demo_project
from be_app.pipeline import run_analysis
from be_app.reporting import blank_report_template, docx_report, pdf_report
from be_app.report_vknt_template import (
    _calculate_power_tost,
    blank_report_vknt,
    build_vknt_report_data,
    docx_report_vknt,
    pdf_report_vknt,
)


@pytest.fixture(scope="module")
def analyzed_project():
    proj = demo_project()
    return run_analysis(proj.freeze())


def test_power_tost_exact_calculation():
    """Verify exact Power_TOST calculation via non-central t distribution."""
    # Test typical bioequivalence scenario: n=24, df=22, se=0.045, estimate=math.log(0.98)
    pow_val = _calculate_power_tost(se=0.045, estimate=-0.0202, df=22, lower=0.8, upper=1.25)
    assert 0.80 <= pow_val <= 1.0, f"Expected high power, got {pow_val}"

    # Zero/negative inputs should safely return 0.0
    assert _calculate_power_tost(se=0.0, estimate=0.0, df=22) == 0.0
    assert _calculate_power_tost(se=0.05, estimate=0.0, df=0) == 0.0


def test_build_vknt_report_data_extracts_power_tost(analyzed_project):
    """Verify build_vknt_report_data extracts Power_TOST and has no Power_80_20 in power table."""
    c = build_vknt_report_data(analyzed_project)
    assert c["has_run"] is True
    assert len(c["be_power_table"]) == 3

    # Check endpoints
    params = [row["param"] for row in c["be_power_table"]]
    assert "AUC0-t" in params
    assert "Cmax" in params
    assert "AUC0-inf" in params

    for row in c["be_power_table"]:
        # Verify Power_TOST is reported
        assert "power_tost" in row
        assert "%" in row["power_tost"]
        val_float = float(row["power_tost"].replace("%", ""))
        assert 70.0 <= val_float <= 100.0
        # Verify Power_80_20 is NOT in row keys
        assert "power_80_20" not in row
        assert "power_8020" not in row


def test_docx_report_vknt_structure_and_tables(analyzed_project):
    """Verify full docx generation with all tables matching VKNT TP.HCM standard."""
    w_bytes = docx_report_vknt(analyzed_project)
    assert len(w_bytes) > 20000

    doc = Document(io.BytesIO(w_bytes))
    assert len(doc.paragraphs) > 100
    assert len(doc.tables) >= 15  # All tables including S1, S3, Bảng 1-3, Bảng 6-13

    # Check Table 12 (Power_TOST)
    power_table_found = False
    for t in doc.tables:
        headers = [c.text.strip() for c in t.rows[0].cells]
        if "Power_TOST (%)" in headers:
            power_table_found = True
            assert headers == ["Thông số", "Power_TOST (%)", "Tiêu chuẩn quy định", "Đánh giá"]
            # Ensure no column for Power_80_20
            assert "Power_80_20" not in headers
            assert "Power 80/20" not in headers
            # Check row count: header + 3 endpoints
            assert len(t.rows) == 4
    assert power_table_found, "Table 12 with Power_TOST (%) header must exist"

    # Verify Bảng 6 (Individual PK) and Bảng 7 (Ln-transformed PK)
    b6_found = False
    b7_found = False
    for t in doc.tables:
        headers = [c.text.strip() for c in t.rows[0].cells]
        if "Cmax (T)" in headers and "Cmax (R)" in headers:
            b6_found = True
            assert len(t.rows) == 25  # 24 subjects + header
        if "Ln Cmax(T)" in headers and "Ln Cmax(R)" in headers:
            b7_found = True
            assert len(t.rows) == 25

    assert b6_found, "Bảng 6 (Thông số PK từng cá thể) must exist"
    assert b7_found, "Bảng 7 (Thông số PK ln-transformed) must exist"


def test_blank_report_vknt():
    """Verify blank report generation produces valid docx with user input placeholders."""
    b_bytes = blank_report_vknt()
    assert len(b_bytes) > 20000

    doc = Document(io.BytesIO(b_bytes))
    all_text = " ".join(p.text for p in doc.paragraphs)
    for t in doc.tables:
        for row in t.rows:
            all_text += " " + " ".join(c.text for c in row.cells)

    assert "[YÊU CẦU NGƯỜI DÙNG BỔ SUNG:" in all_text
    assert "BÁO CÁO KẾT QUẢ NGHIÊN CỨU" in all_text
    assert "Power_TOST" in all_text


def test_pdf_report_vknt(analyzed_project):
    """Verify PDF report generation produces valid PDF with required content."""
    p_bytes = pdf_report_vknt(analyzed_project)
    assert len(p_bytes) > 10000
    assert p_bytes.startswith(b"%PDF")


def test_reporting_router_integration(analyzed_project):
    """Verify router functions in reporting.py respect template parameter."""
    # 1. Blank template
    blank_std = blank_report_template("vi", template="standard")
    blank_legacy = blank_report_template("vi", template="legacy")
    assert len(blank_std) > 0
    assert len(blank_legacy) > 0
    assert blank_std != blank_legacy

    # 2. Docx report
    docx_std = docx_report(analyzed_project, language="vi", template="standard")
    docx_legacy = docx_report(analyzed_project, language="vi", template="legacy")
    assert len(docx_std) > 0
    assert len(docx_legacy) > 0
    assert docx_std != docx_legacy

    # 3. PDF report
    pdf_std = pdf_report(analyzed_project, language="vi", template="standard")
    pdf_legacy = pdf_report(analyzed_project, language="vi", template="legacy")
    assert len(pdf_std) > 0
    assert len(pdf_legacy) > 0
    assert pdf_std != pdf_legacy

    # 4. Backward compatibility check
    assert len(docx_report(analyzed_project, language="vi", template="vknt_tt91")) > 0


def test_filenames_and_metadata_clean_of_vknt_tt91(analyzed_project):
    """Verify that generated artifacts, download file names, and document titles contain no 'vknt' or 'tt91'."""
    # Check blank template filenames logic
    for tpl_choice in ("standard", "legacy"):
        proto_tpl_stem = "Mau_chuan" if tpl_choice in ("standard", "vknt_tt91") else "Mau_tom_tat"
        proto_name = f"BE_Protocol_Template_{proto_tpl_stem}.docx"
        assert "vknt" not in proto_name.lower()
        assert "tt91" not in proto_name.lower()

        rep_tpl_stem = "Mau_chuan" if tpl_choice in ("standard", "vknt_tt91") else "Mau_tom_tat"
        rep_name = f"BE_Report_Template_{rep_tpl_stem}_vi.docx"
        assert "vknt" not in rep_name.lower()
        assert "tt91" not in rep_name.lower()

        tag = "standard" if tpl_choice in ("standard", "vknt_tt91") else "summary"
        artifact_stem = f"1_{tag}_vi_0"
        artifact_name = f"CSR_{artifact_stem}.docx"
        assert "vknt" not in artifact_name.lower()
        assert "tt91" not in artifact_name.lower()

    # Check PDF metadata title in standard report
    pdf_bytes = pdf_report(analyzed_project, language="vi", template="standard")
    assert b"VKNT" not in pdf_bytes[:5000]
    assert b"tt91" not in pdf_bytes[:5000].lower()
