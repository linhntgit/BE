"""Tests for the Vietnamese Bioequivalence Protocol Template (MOH / VKNT TP.HCM - Phụ lục 10.1.1).

Verifies full-fidelity Word and PDF generation using synthetic demo project data.
"""

import io

import pymupdf
import pytest
from docx import Document

from be_app.document_standards import LEGACY_MISSING_VI, REQ_USER_INPUT_PREFIX_VI
from be_app.domain import Study
from be_app.persistence import Project
from be_app.protocol import (
    blank_protocol_template,
    docx_protocol,
    pdf_protocol,
)
from be_app.protocol_vknt_template import (
    VKNT_ABBREVIATIONS,
    VKNT_MEAL_STANDARDIZED,
    VKNT_PROTOCOL_SECTIONS,
    VKNT_SCHEDULE_OF_EVENTS,
    build_vknt_protocol_content,
    docx_protocol_vknt,
    pdf_protocol_vknt,
)


@pytest.fixture
def synthetic_protocol_project():
    study = Study(
        study_id="BE-DEMO-01",
        title="Đánh giá tương đương sinh học viên nén bao phim Fexofenadin 180 (fexofenadin HCl 180 mg) do Cơ sở A sản xuất",
        active_ingredient="Fexofenadin HCl",
        analyte="fexofenadin",
        dose=180.0,
        dose_unit="mg",
        test_product="Fexofenadin 180",
        test_strength="180 mg",
        test_dosage_form="Viên nén bao phim",
        test_manufacturer="Cơ sở sản xuất Dược phẩm A",
        test_batch="B123456",
        reference_product="Thuốc đối chứng B",
        reference_strength="180 mg",
        reference_dosage_form="Viên nén bao phim",
        reference_manufacturer="Cơ sở sản xuất Dược phẩm B",
        reference_batch="R654321",
        sponsor="Đơn vị tài trợ nghiên cứu A",
        study_site="Trung tâm Nghiên cứu Đánh giá TĐSH Lâm sàng Mẫu",
        principal_investigator="PGS. TS. Nghiên cứu viên Mẫu",
        fed_state="fasted",
        design="2x2",
        single_dose=True,
        rule_set_id="EMA_IR_NONREPLICATE_M13A",
    )
    return Project(study=study)


def test_build_vknt_protocol_content(synthetic_protocol_project):
    details = {
        "washout": "07 ngày (ít nhất 5 lần t1/2)",
        "sampling": "0; 0.5; 1; 1.5; 2; 2.5; 3; 3.5; 4; 6; 8; 11; 15; 24; 36; 48 giờ",
    }
    content = build_vknt_protocol_content(synthetic_protocol_project, details)

    assert content["study_id"] == "BE-DEMO-01"
    assert "Fexofenadin 180" in content["test_prod"]
    assert "Thuốc đối chứng B" in content["ref_prod"]
    assert content["is_fexo"] is True
    assert content["washout_val"] == "07 ngày (ít nhất 5 lần t1/2)"
    assert len(content["contacts_table"]) == 14
    assert len(VKNT_PROTOCOL_SECTIONS) == 15
    assert len(VKNT_ABBREVIATIONS) == 25
    assert len(VKNT_MEAL_STANDARDIZED) == 5
    assert len(VKNT_SCHEDULE_OF_EVENTS) == 14


def test_docx_protocol_vknt_complete_structure(synthetic_protocol_project):
    details = {
        "washout": "07 ngày",
        "sampling": "0; 0.5; 1; 1.5; 2; 2.5; 3; 3.5; 4; 6; 8; 11; 15; 24; 36; 48 giờ",
    }
    word_bytes = docx_protocol_vknt(synthetic_protocol_project, details)
    assert word_bytes.startswith(b"PK")

    doc = Document(io.BytesIO(word_bytes))
    all_text = "\n".join(p.text for p in doc.paragraphs)

    # 1. Check Cover page & Title page
    assert "PHỤ LỤC 10.1.1" in all_text
    assert "ĐỀ CƯƠNG NGHIÊN CỨU" in all_text
    assert "ĐÁNH GIÁ TƯƠNG ĐƯƠNG SINH HỌC" in all_text
    assert "FEXOFENADIN 180" in all_text.upper()
    assert "FEXOFENADIN" in all_text.upper()

    # 2. Check Tables count & presence
    assert len(doc.tables) == 8
    # Table 1: Contacts
    assert any("Nghiên cứu viên Mẫu" in cell.text for row in doc.tables[0].rows for cell in row.cells)
    # Table 5: Meal standardized (Bảng 1)
    assert any("1024 kcal" in cell.text for row in doc.tables[4].rows for cell in row.cells)
    # Table 7: Schedule of Events (Bảng 3)
    assert any("Ký 'Phiếu cung cấp thông tin" in cell.text for row in doc.tables[6].rows for cell in row.cells)
    # Table 8: Signatures & Approvals
    assert any("NGHIÊN CỨU VIÊN CHÍNH" in cell.text for row in doc.tables[7].rows for cell in row.cells)

    # 3. Check All 14 Main Sections
    assert "1. ĐẠO ĐỨC TRONG NGHIÊN CỨU" in all_text
    assert "2. TỔNG QUAN VỀ FEXOFENADIN" in all_text
    assert "3. MỤC TIÊU NGHIÊN CỨU" in all_text
    assert "4. THIẾT KẾ NGHIÊN CỨU" in all_text
    assert "5. TUYỂN CHỌN NGƯỜI TÌNH NGUYỆN (NTN)" in all_text
    assert "6. RÚT KHỎI NGHIÊN CỨU" in all_text
    assert "7. QUY TRÌNH CHO UỐNG THUỐC VÀ KIỂM SOÁT ĂN UỐNG" in all_text
    assert "8. KẾ HOẠCH THỰC HIỆN VÀ PHÂN TÍCH" in all_text
    assert "9. QUẢN LÝ VÀ BẢO QUẢN THUỐC NGHIÊN CỨU" in all_text
    assert "10. THEO DÕI VÀ XỬ TRÍ BIẾN CỐ BẤT LỢI (AE / SAE)" in all_text
    assert "11. KẾ HOẠCH PHÂN TÍCH THỐNG KÊ (SAP) VÀ CỠ MẪU" in all_text
    assert "12. QUẢN LÝ VÀ LƯU TRỮ HỒ SƠ NGHIÊN CỨU" in all_text
    assert "13. KIỂM SOÁT CHẤT LƯỢNG VÀ ĐẢM BẢO CHẤT LƯỢNG (QC/QA)" in all_text
    assert "14. ĐÁNH GIÁ TRỰC TIẾP VÀ CHỮ KÝ PHÊ DUYỆT" in all_text
    assert "15. TÀI LIỆU THAM KHẢO" in all_text

    # 4. Check that missing information is conspicuously marked with placeholders
    assert REQ_USER_INPUT_PREFIX_VI in all_text
    assert LEGACY_MISSING_VI in all_text


def test_pdf_protocol_vknt(synthetic_protocol_project):
    details = {"washout": "07 ngày", "sampling": "0; 1; 2; 4; 8; 12; 24 giờ"}
    pdf_bytes = pdf_protocol_vknt(synthetic_protocol_project, details)
    assert pdf_bytes.startswith(b"%PDF")

    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as doc:
        assert len(doc) >= 2
        text = "\n".join(page.get_text() for page in doc)
        assert "PHỤ LỤC 10.1.1" in text
        assert "ĐỀ CƯƠNG NGHIÊN CỨU TƯƠNG ĐƯƠNG SINH HỌC" in text
        assert "BE-DEMO-01" in text
        assert "Fexofenadin 180" in text


def test_blank_protocol_template():
    blank_word = blank_protocol_template("standard")
    assert blank_word.startswith(b"PK")
    doc = Document(io.BytesIO(blank_word))
    assert len(doc.tables) == 8
    all_text = "\n".join(p.text for p in doc.paragraphs)
    assert REQ_USER_INPUT_PREFIX_VI in all_text
    assert "ĐỀ CƯƠNG NGHIÊN CỨU" in all_text
    # Backward compatibility
    assert len(blank_protocol_template("vknt_tt91")) == len(blank_word)


def test_template_dispatch_via_docx_and_pdf(synthetic_protocol_project):
    # Default is legacy
    legacy_word = docx_protocol(synthetic_protocol_project)
    assert len(Document(io.BytesIO(legacy_word)).tables) == 3

    # Explicit legacy
    legacy_word2 = docx_protocol(synthetic_protocol_project, template="legacy")
    assert len(Document(io.BytesIO(legacy_word2)).tables) == 3

    # Dispatch to standard and backward-compatible vknt_tt91
    std_word = docx_protocol(synthetic_protocol_project, template="standard")
    assert len(Document(io.BytesIO(std_word)).tables) == 8
    vknt_word = docx_protocol(synthetic_protocol_project, template="vknt_tt91")
    assert len(Document(io.BytesIO(vknt_word)).tables) == 8

    # PDF dispatch
    legacy_pdf = pdf_protocol(synthetic_protocol_project, template="legacy")
    std_pdf = pdf_protocol(synthetic_protocol_project, template="standard")
    assert legacy_pdf.startswith(b"%PDF")
    assert std_pdf.startswith(b"%PDF")

