import io
import zipfile
from pathlib import Path

import pytest
from docx import Document
from docx.oxml.ns import qn
from streamlit.testing.v1 import AppTest

from tests.conftest import open_be_page
from be_app.branding import COPYRIGHT_NOTICE, DEVELOPER, software_attribution
from be_app.persistence import ProjectStore, export_archive, import_archive
from be_app.pipeline import run_analysis
from be_app.report_template import build_report_outline
from be_app.reporting import analysis_exports, blank_report_template, docx_report, pdf_report, report_content


@pytest.fixture(scope="module")
def report_project(demo):
    return run_analysis(demo.freeze())


@pytest.mark.parametrize("language", ["vi", "en"])
def test_word_draft_and_tables(report_project, language):
    content = docx_report(report_project, language=language)
    doc = Document(io.BytesIO(content))
    footer_text = " ".join(p.text for p in doc.sections[0].footer.paragraphs)
    assert DEVELOPER in footer_text and COPYRIGHT_NOTICE in footer_text
    assert software_attribution(language) in footer_text
    assert len(doc.tables) == 9
    assert len(doc.tables[0].columns) == 6
    assert len(doc.tables[1].rows) == len(report_project.runs[-1]["nca"]) + 1
    assert "Tmax (h)" in [cell.text for cell in doc.tables[1].rows[0].cells]
    expected_headers = (
        ["Chỉ số PK", "Tiêu chí", "Giá trị", "Giới hạn", "Kết quả tiêu chí", "Kết quả chỉ số"]
        if language == "vi" else
        ["Endpoint", "Criterion", "Value", "Limits", "Criterion result", "Endpoint result"]
    )
    assert [cell.text for cell in doc.tables[2].rows[0].cells] == expected_headers
    assert (
        len(doc.tables[-1].rows)
        == len(report_project.runs[-1]["nca"]) * len(report_project.runs[-1]["be"]) + 1
    )
    text = " ".join(p.text for p in doc.paragraphs)
    assert (
        "BẢN DỰ THẢO — CHƯA ĐỦ ĐIỀU KIỆN NỘP CƠ QUAN QUẢN LÝ"
        if language == "vi" else "DRAFT / NOT REGULATORY-READY"
    ) in text
    if language == "vi":
        assert doc.tables[1].rows[0].cells[0].text == "Mã người tham gia"
        assert doc.tables[-1].rows[0].cells[5].text == "Trạng thái dữ liệu"
    else:
        assert doc.tables[1].rows[0].cells[0].text == "Subject"
    assert "SYNTHETIC LEARNING DATA" in text
    assert report_project.runs[-1]["snapshot_hash"] in text
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        assert b"tblHeader" in archive.read("word/document.xml")
    assert doc.paragraphs[0].style.name == "Title"
    for name in ("Normal", "Title", "Heading 1", "Heading 2"):
        style = doc.styles[name]
        assert not style.element.findall(".//" + qn("w:pBdr"))
        fonts = style.element.find(".//" + qn("w:rFonts"))
        assert fonts.get(qn("w:ascii")) == "Arial"
        assert fonts.get(qn("w:hAnsi")) == "Arial"
        assert not any("theme" in attribute.lower() for attribute in fonts.attrib)


def test_pdf_draft_unicode_and_artifact_roundtrip(report_project):
    import fitz

    content = pdf_report(report_project)
    pdf = fitz.open(stream=content, filetype="pdf")
    assert len(pdf) >= 1
    text = " ".join(page.get_text() for page in pdf)
    assert software_attribution("vi") in text
    assert "BẢN DỰ THẢO — CHƯA ĐỦ ĐIỀU KIỆN NỘP CƠ QUAN QUẢN LÝ" in text
    assert "Mã người tham gia" in " ".join(text.split())
    assert "Không thể kết luận" in text
    assert "11.12 Hình và đồ thị minh họa" in text
    assert sum(len(page.get_images()) for page in pdf) >= 3
    updated = report_project.attach_artifact("CSR.pdf", content)
    assert import_archive(export_archive(updated)).artifacts == updated.artifacts


def test_no_report_without_analysis(demo):
    with pytest.raises(ValueError):
        docx_report(demo)


@pytest.mark.parametrize("language", ["vi", "en"])
def test_blank_editable_template_available_without_analysis(language):
    doc = Document(io.BytesIO(blank_report_template(language)))
    footer_text = " ".join(p.text for p in doc.sections[0].footer.paragraphs)
    assert software_attribution(language) in footer_text
    assert len(doc.tables) == 6
    assert all(len(table.rows) == 2 for table in doc.tables)
    assert all(len(table.columns) >= 5 for table in doc.tables)
    headings = [p.text for p in doc.paragraphs if p.style.name == "Heading 1"]
    assert len(headings) == 11
    assert headings[0].startswith("1 ") and headings[-1].startswith("11 ")
    text = " ".join(p.text for p in doc.paragraphs)
    assert "SAP" in text and "ALCOA+" in text
    assert "11.10" in text and "11.11" in text
    assert "11.12" in text
    assert len(doc.inline_shapes) == 4
    if language == "vi":
        assert "NCT03083639" in text
        assert "GIẢ LẬP" in text
    else:
        assert "SYNTHETIC" in text
    assert ("CHƯA CUNG CẤP" if language == "vi" else "NOT PROVIDED") in doc.tables[0].cell(1, 0).text
    assert ("CHƯA CUNG CẤP" if language == "vi" else "NOT PROVIDED") in text
    case_headings = [
        p.text for p in doc.paragraphs
        if p.style.name == "Heading 3" and p.text.startswith("8.5.")
    ]
    assert [heading.split(" ", 1)[0] for heading in case_headings] == [
        "8.5.1", "8.5.2", "8.5.3", "8.5.4", "8.5.5", "8.5.6", "8.5.7"
    ]
    for method in ("ABEL", "RSABE", "EMA NTI", "FDA NTI", "replicate" if language == "en" else "replicate"):
        assert any(method in heading for heading in case_headings)


def test_qa_only_watermark_and_readable_methods(demo):
    study = demo.study.model_copy(update={"is_demo": False})
    analyzed = run_analysis(demo.revise("Keep training provenance when removing demo flag", study=study).freeze())
    content = report_content(analyzed, language="en")
    assert content["qa"] and not content["demo"]
    assert content["run"]["study_decision"] == "NOT EVALUABLE"
    sections = dict(content["sections"])
    assert "terminal phase" in sections["NCA methods"]
    assert "Rule " in sections["Statistical methods"]
    assert "{\"integration\"" not in sections["NCA methods"]
    text = " ".join(p.text for p in Document(io.BytesIO(docx_report(analyzed, language="en"))).paragraphs)
    assert "TRAINING-QA" in text
    assert "SYNTHETIC LEARNING DATA" not in text


def test_english_blockers_localized_without_mutating_snapshot(report_project):
    before = report_project.runs[-1]["snapshot_hash"]
    assert "Dữ liệu đào tạo/QA" in " ".join(report_project.runs[-1]["blockers"])
    en = dict(report_content(report_project, language="en")["sections"])["Conclusion and limitations"]
    vi = dict(report_content(report_project, language="vi")["sections"])["Kết luận và giới hạn"]
    assert "Training/QA or synthetic data" in en
    assert "Dữ liệu đào tạo/QA" not in en
    assert "Dữ liệu đào tạo/QA" in vi
    assert report_project.runs[-1]["snapshot_hash"] == before


def test_english_report_disclaimers_are_localized_in_word_and_pdf(report_project):
    import fitz

    word = Document(io.BytesIO(docx_report(report_project, language="en")))
    word_text = " ".join(paragraph.text for paragraph in word.paragraphs)
    pdf = fitz.open(stream=pdf_report(report_project, language="en"), filetype="pdf")
    pdf_text = " ".join(page.get_text() for page in pdf)
    pdf.close()
    for text in (word_text, pdf_text):
        assert "SYNTHETIC LEARNING DATA — FOR TRAINING ONLY" in text
        assert "TRAINING-QA DATA — NO REAL-STUDY CONCLUSION" in text
        assert "DỮ LIỆU GIẢ LẬP HỌC THỬ" not in text
        assert "DỮ LIỆU ĐÀO TẠO/QA" not in text
        assert "Recorded study title: " in text
        assert report_project.study.title in text


@pytest.mark.parametrize("language", ["vi", "en"])
def test_full_asean_outline_and_hierarchical_headings(report_project, language):
    content = report_content(report_project, language=language)
    outline = content["outline"]
    assert [section["number"] for section in outline if section["level"] == 1] == [
        str(i) for i in range(1, 12)
    ]
    for number in ("1.11", "5.3", "7.5", "8.1.2", "8.7", "9.4.1", "11.9"):
        assert any(section["number"] == number for section in outline)
    assert "SAP" in next(s["body"] for s in outline if s["number"] == "4")
    assert "ALCOA+" in next(s["body"] for s in outline if s["number"] == "8.7")
    word = Document(io.BytesIO(docx_report(report_project, language=language)))
    headings = {p.text: p.style.name for p in word.paragraphs if p.style.name.startswith("Heading")}
    assert any(title.startswith("8.1.2 ") and style == "Heading 3" for title, style in headings.items())
    assert any(title.startswith("11.10 ") and style == "Heading 2" for title, style in headings.items())
    assert len(word.tables) == 9


@pytest.mark.parametrize(
    ("rule_id", "number", "keyword"),
    [
        ("EMA_HVDP_ABEL", "8.5.2", "ABEL"),
        ("FDA_HVD_RSABE_2026", "8.5.2", "Howe"),
        ("EMA_NTI", "8.5.2", "0,90"),
        ("FDA_NTI", "8.5.2", "sWT/sWR"),
        ("FDA_REPLICATE_STANDARD", "8.5.2", "replicate"),
        ("EMA_IR_NONREPLICATE_M13A", "8.5.1", "TOST"),
    ],
)
def test_method_specific_template_without_fabricated_evidence(report_project, rule_id, number, keyword):
    run = report_project.runs[-1]
    study = {**run["study"], "rule_set_id": rule_id}
    outline = build_report_outline(study, run, {}, "vi")
    body = next(s["title"] + s["body"] for s in outline if s["number"] == number)
    assert keyword in body
    assert "CHƯA CUNG CẤP" in next(s["body"] for s in outline if s["number"] == "1.11")
    assert "CHƯA CUNG CẤP" in next(s["body"] for s in outline if s["number"] == "8.6")


def test_nonreplicate_rule_does_not_inherit_replicate_method(report_project):
    run = report_project.runs[-1]
    study = {**run["study"], "rule_set_id": "EMA_IR_NONREPLICATE_M13A"}
    outline = build_report_outline(study, run, {}, "vi")
    conventional_follow_up = next(section for section in outline if section["number"] == "8.5.2")
    assert "Cỡ mẫu" in conventional_follow_up["title"]
    assert not any("ABE với thiết kế replicate" in section["title"] for section in outline)
    methods = next(section["body"] for section in outline if section["number"] == "9.4")
    assert "Phương pháp: ABE" in methods


def test_data_exports_and_ctd_mapping(report_project):
    data = analysis_exports(report_project)
    assert {
        "nca.csv",
        "nca.xlsx",
        "be.xlsx",
        "validated.csv",
        "audit.json",
        "analysis.json",
        "ctd_mapping.json",
        "input_manifest.json",
    } == set(data)
    assert b"5.3.1.2" in data["ctd_mapping.json"]
    content = report_content(report_project)
    assert content["run"]["study_decision"] == "NOT EVALUABLE"


def test_snapshot_figures_show_actual_analysis_without_changing_hash(report_project):
    from be_app.report_figures import snapshot_figures

    original_hash = report_project.runs[-1]["snapshot_hash"]
    figures = snapshot_figures(report_project.runs[-1], "vi")
    assert len(figures) == 4
    assert all(f.png.startswith(b"\x89PNG\r\n\x1a\n") for f in figures)
    assert "SNAPSHOT" in figures[1].note
    assert "CI90" in figures[3].note
    word = Document(io.BytesIO(docx_report(report_project, language="vi")))
    assert len(word.inline_shapes) == 4
    assert "11.12 Hình và đồ thị minh họa" in " ".join(p.text for p in word.paragraphs)
    assert report_project.runs[-1]["snapshot_hash"] == original_hash


def test_snapshot_figures_do_not_invent_missing_concentrations_or_be():
    from be_app.report_figures import snapshot_figures

    assert snapshot_figures({"study": {"design": "parallel"}, "validated_data": [], "be": []}) == []


def test_streamlit_all_pages_and_workflow(tmp_path, monkeypatch):
    import be_app.ui as ui
    from be_app.examples import demo_project

    database = ProjectStore(tmp_path / "ui.sqlite")
    saved_demo = demo_project()
    database.save(saved_demo)
    monkeypatch.setattr(ui, "store", lambda: database)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=30).run()
    assert not app.exception
    next(s for s in app.selectbox if s.label == "Nghiên cứu đã lưu").set_value(saved_demo.project_id).run()
    button = next(b for b in app.button if b.label == "Mở nghiên cứu đã lưu")
    button.click().run()
    assert app.session_state.project.study.is_demo
    open_be_page(app, ui.PAGES[5])
    assert any("Chưa Data Freeze" in message.value for message in app.warning)
    next(b for b in app.button if b.label == "Đến QC để kiểm tra và khóa dữ liệu →").click().run()
    assert any(s.value == "Khóa dữ liệu để chạy NCA/BE" for s in app.subheader)
    assert any(b.label == "Kiểm tra / cập nhật QC" for b in app.button)
    next(b for b in app.button if b.label == "Data Freeze và khóa SAP").click().run()
    assert app.session_state.project.freeze_hash
    open_be_page(app, ui.PAGES[5])
    assert any("Dự án đã Data Freeze" in notice.value for notice in app.info)
    assert next(b for b in app.button if b.label == "Lưu cấu hình trước khóa").disabled
    next(b for b in app.button if b.label == "Phân tích NCA và BE").click().run()
    assert app.session_state.project.runs[-1]["study_decision"] == "NOT EVALUABLE"
    for page in ui.PAGES[:10]:
        open_be_page(app, page)
        assert not app.exception, page
        assert not app.error, (page, [e.value for e in app.error])
    for workflow in ui.WORKFLOWS[:2]:
        app.sidebar.radio[0].set_value(workflow).run()
        assert not app.exception, workflow
        assert not app.error, (workflow, [e.value for e in app.error])
