"""Tests for Bioequivalence Protocol and Report standardization according to FDA/EMA/ICH."""

import io
from docx import Document

from be_app.document_standards import (
    DOCUMENT_FIELD_MAPPING,
    REGULATORY_COMPARISON_MATRIX,
    REQ_USER_INPUT_PREFIX_EN,
    REQ_USER_INPUT_PREFIX_VI,
    req_user_input,
)
from be_app.domain import Study
from be_app.examples import demo_project
from be_app.persistence import Project
from be_app.pipeline import run_analysis
from be_app.protocol import docx_protocol, pdf_protocol, protocol_content
from be_app.report_template import build_report_outline
from be_app.reporting import blank_report_template, docx_report, pdf_report


def test_standardized_placeholder_format():
    vi_tag = req_user_input("Số phê duyệt Đạo đức", "Nhập số quyết định của IRB", "vi", context="protocol")
    assert REQ_USER_INPUT_PREFIX_VI in vi_tag
    assert "Số phê duyệt Đạo đức" in vi_tag
    assert "Nhập số quyết định của IRB" in vi_tag
    assert "[CẦN BỔ SUNG" in vi_tag

    en_tag = req_user_input("Ethics Approval Number", "Enter IRB approval decision", "en", context="protocol")
    assert REQ_USER_INPUT_PREFIX_EN in en_tag
    assert "Ethics Approval Number" in en_tag

    report_tag_vi = req_user_input("Hồ sơ lô thuốc thử", "Nhập CoA và quy mô lô", "vi", context="report")
    assert REQ_USER_INPUT_PREFIX_VI in report_tag_vi
    assert "CHƯA CUNG CẤP" in report_tag_vi


def test_protocol_prospective_nature_and_standard_placeholders():
    # Empty study with no notes
    project = Project(study=Study(study_id="BE-TEST-EMPTY", title="Nghiên cứu thử nghiệm"))
    content = protocol_content(project)

    # 15 Sections
    assert len(content["sections"]) == 15

    # Check that manual/unfilled fields contain [YÊU CẦU NGƯỜI DÙNG BỔ SUNG: ...]
    sections_text = " ".join(" ".join(p) for _, _, p in content["sections"])
    assert REQ_USER_INPUT_PREFIX_VI in sections_text
    assert "Quần thể tuyển chọn" in sections_text
    assert "Lịch lấy mẫu nồng độ" in sections_text
    assert "Phương pháp định lượng" in sections_text

    # Protocol must be prospective: no actual study results or BE conclusions
    assert "KẾT QUẢ VÀ BÀN LUẬN" not in sections_text
    assert "ĐẠT tiêu chí thống kê" not in sections_text
    assert "KHÔNG ĐẠT tiêu chí thống kê" not in sections_text

    # Generate documents
    word_bytes = docx_protocol(project)
    pdf_bytes = pdf_protocol(project)
    assert word_bytes.startswith(b"PK")
    assert pdf_bytes.startswith(b"%PDF")

    doc = Document(io.BytesIO(word_bytes))
    all_doc_text = " ".join(p.text for p in doc.paragraphs)
    assert REQ_USER_INPUT_PREFIX_VI in all_doc_text
    assert "DỰ THẢO ĐỀ CƯƠNG — CHƯA ĐƯỢC PHÊ DUYỆT" in all_doc_text


def test_report_standardized_placeholders_and_regulatory_sections():
    demo = demo_project()
    analyzed = run_analysis(demo.freeze())

    # Vietnamese report
    outline_vi = build_report_outline(analyzed.study.model_dump(), analyzed.runs[-1], {}, "vi")
    assert len([s for s in outline_vi if s["level"] == 1]) == 11
    outline_vi_text = " ".join(s["body"] for s in outline_vi)
    assert REQ_USER_INPUT_PREFIX_VI in outline_vi_text
    assert "CHƯA CUNG CẤP" in outline_vi_text

    # English report
    outline_en = build_report_outline(analyzed.study.model_dump(), analyzed.runs[-1], {}, "en")
    assert len([s for s in outline_en if s["level"] == 1]) == 11
    outline_en_text = " ".join(s["body"] for s in outline_en)
    assert REQ_USER_INPUT_PREFIX_EN in outline_en_text
    assert "NOT PROVIDED" in outline_en_text

    # Test blank report template exports
    word_blank_vi = blank_report_template("vi")
    word_blank_en = blank_report_template("en")
    assert word_blank_vi.startswith(b"PK")
    assert word_blank_en.startswith(b"PK")

    # Test full docx and pdf report exports
    docx_bytes = docx_report(analyzed, language="vi")
    pdf_bytes = pdf_report(analyzed, language="vi")
    assert docx_bytes.startswith(b"PK")
    assert pdf_bytes.startswith(b"%PDF")


def test_regulatory_comparison_matrix_and_master_mapping():
    assert len(REGULATORY_COMPARISON_MATRIX) >= 8
    topics = [item["topic"] for item in REGULATORY_COMPARISON_MATRIX]
    assert any("Thiết kế chuẩn" in t for t in topics)
    assert any("thuốc biến thiên cao (HVD)" in t for t in topics)
    assert any("khoảng điều trị hẹp (Narrow Therapeutic Index - NTI)" in t for t in topics)
    assert any("thông số PK chính" in t for t in topics)
    assert any("Phương pháp thống kê trung bình (Average Bioequivalence - ABE)" in t for t in topics)

    assert len(DOCUMENT_FIELD_MAPPING) >= 15
    categories = {m["category"] for m in DOCUMENT_FIELD_MAPPING.values()}
    assert "Hành chính & Quản lý" in categories
    assert "Sản phẩm nghiên cứu" in categories
    assert "Thiết kế & Lâm sàng" in categories
    assert "Dược động học & Thống kê" in categories
    assert "Đạo đức & An toàn" in categories
