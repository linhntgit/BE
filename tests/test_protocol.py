"""Pre-analysis BE research protocol: content, formats, and Streamlit workflow."""

import io
from pathlib import Path

import pymupdf
import pytest
from docx import Document
from streamlit.testing.v1 import AppTest

from tests.conftest import open_be_page
from be_app.domain import Study
from be_app.persistence import Project, ProjectStore
from be_app.protocol import MISSING, PROTOCOL_FIELDS, docx_protocol, pdf_protocol, protocol_content


def test_protocol_exports_before_any_analysis_and_preserves_project():
    study = Study(
        study_id="BE-TRAIN-2026", title="Đánh giá tương đương sinh học", analyte="esomeprazole",
        active_ingredient="Esomeprazole", sponsor="Trường Đại học Dược Hà Nội",
        test_product="Thuốc thử A", reference_product="Thuốc đối chứng B",
        test_strength="20 mg", reference_strength="20 mg",
        test_batch="TX-42", reference_batch="RX-52",
        test_expiry_date="2027-06-30", reference_expiry_date="2027-07-31",
        protocol="BE-01 v1", fed_state="fed", is_demo=True,
    )
    project = Project(study=study)
    snapshot = project.model_dump(mode="json")
    details = {"washout": "Ít nhất 7 ngày", "sampling": "0; 0,5; 1; 2; 4; 8; 12; 24 giờ"}
    result = protocol_content(project, details)
    sections = result["sections"]
    assert len(sections) == 15
    assert len(PROTOCOL_FIELDS) == 11
    assert "Ít nhất 7 ngày" in " ".join(sections[3][2])
    assert "[CẦN BỔ SUNG" in " ".join(sections[4][2])
    assert result["summary"][8][1] == "No (sau ăn)"

    word = docx_protocol(project, details)
    pdf = pdf_protocol(project, details)
    assert word.startswith(b"PK") and pdf.startswith(b"%PDF")

    doc = Document(io.BytesIO(word))
    headings = [p.text for p in doc.paragraphs if p.style.name == "Heading 1"]
    assert "1. Tóm tắt đề cương" in headings
    assert "9. Kế hoạch phân tích thống kê (SAP)" in headings
    assert "15. Tài liệu tham khảo và phụ lục" in headings
    assert len(doc.tables) == 3
    assert "Thuốc thử A" in " ".join(cell.text for row in doc.tables[1].rows for cell in row.cells)
    assert any("CHƯA ĐƯỢC PHÊ DUYỆT" in p.text for p in doc.paragraphs)
    assert any("ĐÀO TẠO/GIẢ LẬP" in p.text for p in doc.paragraphs)
    assert "Nguyễn Trần Linh" in doc.sections[0].footer.paragraphs[0].text

    with pymupdf.open(stream=pdf, filetype="pdf") as pages:
        text = "\n".join(page.get_text() for page in pages)
        assert len(pages) >= 2
        assert "ĐỀ CƯƠNG NGHIÊN CỨU" in text
        assert "Đánh giá tương đương sinh học" in text
        assert "Esomeprazole" in text
        assert "Nguyễn Trần Linh" in text
        assert "DỮ LIỆU ĐÀO TẠO/GIẢ LẬP" in text
        assert MISSING in text
    assert project.model_dump(mode="json") == snapshot


@pytest.mark.parametrize(
    ("rule_id", "design", "keyword"),
    [
        ("EMA_IR_NONREPLICATE_M13A", "2x2", "ABE:"),
        ("FDA_ABE_2026", "parallel", "ABE:"),
        ("EMA_REPLICATE_STANDARD", "full4", "Replicate ABE:"),
        ("EMA_HVDP_ABEL", "partial3", "EMA ABEL:"),
        ("FDA_HVD_RSABE_2026", "full4", "FDA RSABE:"),
        ("EMA_NTI", "2x2", "EMA NTI:"),
        ("FDA_NTI", "full4", "FDA NTI:"),
        ("FDA_REPLICATE_STANDARD", "full4", "Replicate ABE:"),
    ],
)
def test_method_specific_protocol(rule_id, design, keyword):
    project = Project(study=Study(study_id="METHOD", title="Đề cương", rule_set_id=rule_id,
                                  design=design, nti="NTI" in rule_id,
                                  scaled_be_prespecified="HVD" in rule_id))
    content = protocol_content(project)
    text = " ".join(content["sections"][8][2])
    assert keyword in text
    assert MISSING in text
    assert len(docx_protocol(project)) > 10000
    assert pdf_protocol(project).startswith(b"%PDF")


def test_unverified_sample_size_not_assumed():
    project = Project(study=Study(study_id="SAMPLE", title="Đề cương"))
    assert MISSING in protocol_content(project)["sections"][5][2][0]
    plan = {"evaluable": 24, "recruit": 28, "curve_endpoint": "cmax", "inputs": {"source": "Pilot"}}
    content = protocol_content(project, {"sample_size": "Ghi chú cũ"}, valid_plan=plan)
    description = content["sections"][5][2][0]
    assert "24" in description and "28" in description
    assert "Ghi chú cũ" not in description
    assert "Pilot" in description


def test_streamlit_protocol_export_without_analysis_and_with_persistent_notes(tmp_path, monkeypatch):
    import be_app.ui as ui

    monkeypatch.setattr(ui, "store", lambda: ProjectStore(tmp_path / "protocol_ui.sqlite"))
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=30).run()
    assert not app.exception
    from tests.conftest import create_demo_study
    create_demo_study(app)
    initial_revision = app.session_state.project.input_revision
    assert not app.session_state.project.runs
    open_be_page(app, ui.PAGES[8])
    assert not app.exception
    assert any(e.label == "Đề cương nghiên cứu BE · Xuất Word / PDF" for e in app.get("expander"))
    washout = next(t for t in app.text_area if t.label == "Thời gian washout và căn cứ lựa chọn")
    washout.set_value("7 ngày theo thời gian bán thải").run()
    assert app.session_state.project.drafts["protocol"]["washout"] == "7 ngày theo thời gian bán thải"
    next(b for b in app.button if b.label == "Tạo đề cương Word và PDF").click().run()
    assert not app.exception
    cached = [v for k, v in app.session_state.active_project_state.render_cache.items()
              if isinstance(k, tuple) and k[0] == "protocol_exports"]
    assert len(cached) == 1
    assert cached[0][0].startswith(b"PK") and cached[0][1].startswith(b"%PDF")
    assert app.session_state.project.input_revision == initial_revision
    assert not app.session_state.project.runs

    # Editing a note must hide exports generated from its previous contents.
    next(t for t in app.text_area if t.label == "Thời gian washout và căn cứ lựa chọn").set_value(
        "14 ngày theo thời gian bán thải"
    ).run()
    assert not [
        b for b in app.get("button") if b.label.startswith("Tải đề cương")
    ]
    next(b for b in app.button if b.label == "Tạo đề cương Word và PDF").click().run()
    assert not app.exception
    assert len([
        k for k in app.session_state.active_project_state.render_cache
        if isinstance(k, tuple) and k[0] == "protocol_exports"
    ]) == 1
    open_be_page(app, ui.PAGES[7])
    open_be_page(app, ui.PAGES[8])
    assert next(t for t in app.text_area if t.label == "Thời gian washout và căn cứ lựa chọn").value == "14 ngày theo thời gian bán thải"
    assert not app.exception
