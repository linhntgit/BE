"""Study-specific medicinal product and chronology data survive revision and reporting."""

import io

import pytest
from docx import Document

from be_app.domain import Study
from be_app.examples import demo_project
from be_app.persistence import Project, ProjectStore, export_archive, import_archive
from be_app.pipeline import run_analysis
from be_app.report_template import build_report_outline
from be_app.reporting import blank_report_template, docx_report, pdf_report


def populated_study() -> Study:
    return Study(
        study_id="META001", title="Nghiên cứu BE kiểm thử", fed_state="fed",
        active_ingredient="Hoạt chất X", dose=100, dose_unit="mg",
        sponsor="Đơn vị tài trợ XYZ", study_site="Trung tâm PK XYZ",
        principal_investigator="Nghiên cứu viên A",
        test_product="Chế phẩm thử X", reference_product="Chế phẩm đối chứng Y",
        test_strength="100 mg/viên", reference_strength="100 mg/viên",
        test_concentration="", reference_concentration="",
        test_dosage_form="Viên nang cứng", reference_dosage_form="Viên nang cứng",
        test_manufacturer="Công ty sản xuất A", reference_manufacturer="Công ty sản xuất B",
        test_batch="T-2026-01", reference_batch="R-2026-02",
        test_expiry_date="2027-05-01", reference_expiry_date="2027-06-01",
        study_start_date="2026-01-01", study_end_date="2026-06-30",
        clinical_start_date="2026-02-01", clinical_end_date="2026-02-15",
        bioanalytical_start_date="2026-03-01", bioanalytical_end_date="2026-04-15",
        data_lock_date="2026-05-01",
    )


def test_study_metadata_survives_archive_database_and_revision(tmp_path):
    study = populated_study()
    project = Project(study=study)
    assert import_archive(export_archive(project)).study == study
    store = ProjectStore(tmp_path / "studies.sqlite")
    store.save(project, 0)
    loaded, _, _ = store.checkout(project.project_id)
    assert loaded.study == study

    revised_study = study.model_copy(update={"fed_state": "fasted", "reference_batch": "R-NEW"})
    revised = project.revise("Bổ sung thay đổi đã duyệt từ protocol", study=revised_study)
    assert revised.study.fed_state == "fasted"
    assert revised.study.reference_batch == "R-NEW"
    assert revised.study.test_manufacturer == study.test_manufacturer
    assert revised.config_revision == project.config_revision + 1


@pytest.mark.parametrize("overrides", [
    {"test_expiry_date": "2026-02-30"},
    {"reference_expiry_date": "01/12/2027"},
    {"study_start_date": "2026-04-01", "study_end_date": "2026-03-01"},
    {"clinical_start_date": "2026-03-01", "clinical_end_date": "2026-02-01"},
    {"bioanalytical_start_date": "2026-06-01", "bioanalytical_end_date": "2026-05-01"},
])
def test_reject_invalid_study_dates(overrides):
    with pytest.raises(ValueError, match="ngày|Ngày"):
        Study(study_id="BAD-DATE", title="Kiểm tra ngày", **overrides)


@pytest.mark.parametrize("language", ["vi", "en"])
def test_metadata_is_in_outline_and_blank_word_template(language):
    study = populated_study()
    outline = {x["number"]: x["body"] for x in build_report_outline(
        study.model_dump(mode="json"), {}, {}, language
    )}
    assert "2026-02-15" in outline["1.10"]
    assert "2026-04-15" in outline["1.10"]
    assert "Chế phẩm thử X" in outline["7.1"]
    assert "Chế phẩm đối chứng Y" in outline["7.2"]
    assert "T-2026-01" in outline["7.1"]
    assert "R-2026-02" in outline["7.2"]
    assert "2027-05-01" in outline["7.1"]
    assert "100 mg/viên" in outline["7.1"]
    assert ("No (sau ăn)" if language == "vi" else "Fed") in outline["8.1"]
    word = Document(io.BytesIO(blank_report_template(language)))
    text = " ".join(paragraph.text for paragraph in word.paragraphs)
    assert ("hàm lượng" if language == "vi" else "strength") in text.lower()
    assert "7.1" in text and "1.10" in text


def test_generated_word_and_pdf_contain_snapshot_product_details():
    import fitz

    project = run_analysis(demo_project().freeze())
    snapshot = project.runs[-1]["study"]
    assert snapshot["test_batch"] == "SYNTH-T-001"
    assert snapshot["reference_expiry_date"] == "2027-12-31"
    doc = Document(io.BytesIO(docx_report(project, language="vi")))
    word_text = " ".join(p.text for p in doc.paragraphs)
    assert "SYNTH-T-001" in word_text
    assert "SYNTH-R-001" in word_text
    assert "2026-09-30" in word_text
    assert "Đói (nhịn ăn)" in word_text
    pdf = fitz.open(stream=pdf_report(project, language="vi"), filetype="pdf")
    pdf_text = " ".join(page.get_text() for page in pdf)
    pdf.close()
    assert "SYNTH-T-001" in pdf_text
    assert "2027-12-31" in pdf_text
