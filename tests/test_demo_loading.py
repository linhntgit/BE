"""Demo scenarios stage synthetic inputs into the same widgets used for real work."""

from __future__ import annotations

import base64
import io
from pathlib import Path

import pandas as pd
import pytest
from docx import Document
from streamlit.testing.v1 import AppTest

from be_app.demo_scenarios import (
    DEMO_SAMPLING_TIMES,
    ENDPOINT_CASES,
    FULL_RAW_CASES,
    PK_CASES,
    QUICK_CASES,
    STUDY_CASES,
    endpoint_frame,
    full_concentrations,
    pk_frame,
    quick_frame,
    study_values,
)
from be_app.design import randomize
from be_app.domain import Study
from be_app.import_review import review_import
from be_app.imports import REQUIRED, csv_bytes
from be_app.persistence import Project, ProjectStore
from be_app.protocol import PROTOCOL_FIELDS
from be_app.regulations import scope_blockers
from tests.conftest import open_be_page


def _demo_study(case: str) -> Study:
    """Model the values submitted by the ordinary create-study form."""
    values = study_values(case)
    fields = {name: values[name] for name in Study.model_fields if name in values}
    fields.update(
        rule_set_id=values["rule"],
        data_purpose=values["purpose"],
        data_provenance=values["provenance"],
        active_ingredient=values["ingredient"],
        scope_reviewed=values["reviewed"],
        scope_evidence=values["evidence"],
        scaled_be_prespecified=values["scaled"],
        hvd_justification=values["hvd_reason"],
        nti_cmax_narrow=values["nti_cmax"],
        scope_record={
            key: values[f"scope_{key}"]
            for key in ("reference_market", "guidance", "applicability", "deviations")
        },
    )
    return Study.model_validate(fields)


@pytest.mark.parametrize("case", STUDY_CASES)
def test_demo_study_scenarios_fill_descriptions(case):
    values = study_values(case)
    assert values["is_demo"] and values["purpose"] == "training_qa"
    assert values["study_id"].startswith("DEMO_")
    assert values["protocol"] and values["sap"]
    assert values["rule"] and values["design"]
    assert "Synthetic" in values["provenance"]
    study = _demo_study(case)
    assert not scope_blockers(study)
    assert all(study.protocol_details.get(key) for key, _ in PROTOCOL_FIELDS)
    assert set(study.scope_record) == {"reference_market", "guidance", "applicability", "deviations"}
    assert DEMO_SAMPLING_TIMES in study.protocol_details["sampling"]
    assert all(study.protocol_details.get(key) for key in (
        "clinical_period_2", "clinical_physician", "test_mfg_date", "irb_approval_no",
        "pharmacology", "mean_age", "mean_bmi",
    ))


def test_demo_2x2_can_complete_import_qc_freeze_and_analysis_without_manual_values():
    from be_app.pipeline import run_analysis

    study = _demo_study("2x2")
    allocation, metadata = randomize("2x2", 24, 241029)
    project = Project(study=study).with_allocation(allocation.to_dict("records"), metadata)
    frame = full_concentrations(study, project.allocation, "normal")
    assert len(frame) == 24 * 2 * len(DEMO_SAMPLING_TIMES.split(","))

    project = project.import_raw(csv_bytes(frame), "synthetic_normal.csv")
    assert project.qc().valid
    project = project.freeze()
    assert project.freeze_hash
    project = run_analysis(project)
    assert project.runs and project.runs[-1]["nca"]
    assert project.runs[-1]["be"]
    assert project.runs[-1]["snapshot_hash"]


@pytest.mark.parametrize("case", ["parallel", "partial3", "full4", "nti", "hvd"])
def test_demo_all_designs_export_standard_reports_without_manual_values(case):
    from be_app.pipeline import run_analysis
    from be_app.report_vknt_template import build_vknt_report_data
    from be_app.reporting import docx_report, pdf_report

    study = _demo_study(case)
    allocation, metadata = randomize(study.design, 24, 241029)
    project = Project(study=study).with_allocation(allocation.to_dict("records"), metadata)
    raw = full_concentrations(study, project.allocation, "normal")
    project = run_analysis(project.import_raw(csv_bytes(raw), "synthetic_normal.csv").freeze())

    report = build_vknt_report_data(project)
    assert report["is_demo"]
    assert report["n_enrolled"] == 24
    assert report["n_analyzed"] == 24
    assert "GIẢ LẬP" in report["clin_p2"]
    assert "GIẢ LẬP" in report["clin_physician"]
    assert len(report["pk_subject_table"]) == 24
    assert bool(report["pk_replicate_note"]) == (case in {"partial3", "full4", "nti", "hvd"})

    word = docx_report(project, language="vi", template="standard")
    pdf = pdf_report(project, language="vi", template="standard")
    assert pdf.startswith(b"%PDF") and len(pdf) > 10_000
    assert len(word) > 20_000
    doc = Document(io.BytesIO(word))
    assert any("DỮ LIỆU GIẢ LẬP HỌC THỬ" in p.text for p in doc.paragraphs)
    assert any("KẾT LUẬN BÀI THỰC HÀNH" in p.text for p in doc.paragraphs)
    if report["pk_replicate_note"]:
        assert any("trung bình cộng các kỳ" in p.text for p in doc.paragraphs)


@pytest.mark.parametrize("case", FULL_RAW_CASES)
def test_demo_raw_cases_provide_preflight_and_a_click_only_recovery(case):
    study = _demo_study(case if case in {"nti", "hvd"} else "2x2")
    allocation, _ = randomize(study.design, 12, 241029)
    rows = allocation.to_dict("records")
    source = csv_bytes(full_concentrations(study, rows, case))
    reviewed = review_import(source, f"synthetic_{case}.csv", "{}", study, rows, case == "units")

    assert reviewed.ready == (case not in {"missing_period", "duplicate"})
    if not reviewed.ready:
        # The recovery button stages the same valid dataset as the normal scenario.
        restored = csv_bytes(full_concentrations(study, rows, "normal"))
        assert review_import(restored, "synthetic_normal.csv", "{}", study, rows, False).ready


@pytest.mark.parametrize("case", FULL_RAW_CASES)
def test_demo_concentration_variants_follow_saved_allocation(case):
    study = Study(study_id="DEMO_TEST", title="Synthetic", is_demo=True, data_purpose="training_qa")
    frame, _ = randomize("2x2", 4, 241029)
    allocation = frame.to_dict("records")
    raw = full_concentrations(study, allocation, case)
    assert set(REQUIRED) <= set(raw.columns)
    assert set(raw.study_id) == {study.study_id}
    assert set(raw.subject_id) <= set(frame.subject_id)
    assert set(raw.treatment) == {"T", "R"}
    if case == "missing_period":
        assert len(raw) < 4 * 2 * 14
    if case == "missing_sample":
        assert len(raw) == len(allocation) * 14 - 1
    if case == "duplicate":
        assert raw.duplicated(["subject_id", "period", "sample_id"]).any()
    if case == "units":
        assert set(raw.concentration_unit) == {"µg/mL"}
    if case == "blq":
        assert raw.blq_flag.any()


@pytest.mark.parametrize("case", STUDY_CASES)
def test_valid_raw_demo_preflight_for_each_study_design(case):
    values = study_values(case)
    study = Study(
        study_id=values["study_id"], title=values["title"],
        design=values["design"], rule_set_id=values["rule"],
        is_demo=True, data_purpose="training_qa",
    )
    allocation, _ = randomize(study.design, 12, 241029)
    raw = full_concentrations(study, allocation.to_dict("records"), "normal")
    review = review_import(csv_bytes(raw), "study_demo.csv", "{}", study,
                           allocation.to_dict("records"), False)
    assert review.ready, review.error or (review.qc.report() if review.qc else "Không có QC")


@pytest.mark.parametrize("case", QUICK_CASES)
def test_demo_quick_case_has_editable_source(case):
    frame, design, rule = quick_frame(case)
    assert len(frame) > 0 and {"Subject", "Sequence", "Period", "Treatment"} <= set(frame)
    assert design and rule
    assert ("Peak" in frame) == (case == "mapping")
    if case == "concentration":
        assert "BLQ" in frame
        assert frame["BLQ"].dtype == bool


@pytest.mark.parametrize("case", ENDPOINT_CASES)
def test_demo_endpoint_case_has_required_identity(case):
    design = "partial3" if case == "partial3" else "full4" if case in {"full4", "nti", "hvd"} else "2x2"
    frame = endpoint_frame(design, case)
    assert len(frame) >= 72
    assert {"Subject", "Sequence", "Period", "Treatment", "Cmax", "AUClast"} <= set(frame)
    assert (frame.Cmax.eq("").any()) == (case == "missing")


@pytest.mark.parametrize("case", PK_CASES)
def test_demo_pk_case_is_staged_source_not_result(case):
    frame, settings = pk_frame(case)
    assert not frame.empty and {"profile_id", "time_h", "concentration", "blq"} <= set(frame)
    assert settings["pk_dose_mode"] in {"single", "multiple", "steady_state"}
    assert (frame.time_h.duplicated().any()) == (case == "duplicate")
    if case == "iv":
        # IV bolus C(0+) is an extrapolated model value, not an observed sample.
        assert frame.time_h.min() == 0.25
        assert not frame.time_h.eq(0).any()
        assert frame.concentration.gt(0).all()


def test_full_be_demo_stages_study_and_raw_without_auto_import_or_analysis(tmp_path, monkeypatch):
    import be_app.ui as ui

    monkeypatch.setattr(ui, "store", lambda: ProjectStore(tmp_path / "demo_full.sqlite"))
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=40).run()
    assert not app.session_state.get("active_project_state")

    app.selectbox(key="study_demo_case").set_value("partial3").run()
    next(b for b in app.button if b.label == "Điền dữ liệu mẫu vào biểu mẫu nghiên cứu").click().run()
    assert not app.exception
    assert not app.session_state.get("active_project_state")
    assert next(t for t in app.text_input if t.label == "Mã nghiên cứu").value == "DEMO_PARTIAL3"
    next(t for t in app.text_input if t.label == "Tên nghiên cứu").set_value("Bài tập đã sửa").run()
    next(b for b in app.button if b.label == "Tạo nghiên cứu").click().run()
    project = app.session_state.project
    assert project.study.is_demo and project.study.title == "Bài tập đã sửa"
    assert project.study.design == "partial3" and not project.allocation
    assert not project.raw_base64 and not project.runs

    open_be_page(app, ui.PAGES[2])
    next(b for b in app.button if b.label == "Tạo danh sách phân nhóm").click().run()
    assert app.session_state.project.allocation
    open_be_page(app, ui.PAGES[3])
    next(b for b in app.button if b.label == "Điền dữ liệu mẫu vào bảng nồng độ").click().run()
    assert not app.exception
    assert any({"study_id", "concentration"} <= set(table.value.columns)
               for table in app.dataframe)
    state = app.session_state.active_project_state
    staged = state.draft("import", "file")
    assert len(pd.read_csv(pd.io.common.BytesIO(base64.b64decode(staged["base64"])))) > 0
    assert not state.project.raw_base64 and not state.project.runs
    next(b for b in app.button if b.label == "Kiểm tra cấu trúc và QC").click().run()
    assert not app.exception
    assert any(b.label == "Nhập và lưu raw bất biến" for b in app.button)


def test_demo_buttons_quick_and_independent_pk_fill_existing_editors(tmp_path, monkeypatch):
    import be_app.ui as ui

    monkeypatch.setenv("PK_ANALYSIS_DATABASE", str(tmp_path / "independent_pk.sqlite"))
    monkeypatch.setattr(ui, "store", lambda: ProjectStore(tmp_path / "quick.sqlite"))
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=40).run()
    app.sidebar.radio[0].set_value("BE nhanh").run()
    app.selectbox(key="quick_demo_case").set_value("mapping").run()
    next(b for b in app.button if b.label == "Điền dữ liệu mẫu vào bảng BE nhanh").click().run()
    assert not app.exception
    assert "Peak" in app.session_state.quick_loaded_table.columns
    assert any("Peak" in table.value.columns and len(table.value) > 8
               for table in app.dataframe)
    assert not app.session_state.get("quick_be_result")

    app.sidebar.radio[0].set_value("Phân tích PK độc lập").run()
    app.selectbox(key="pk_demo_case").set_value("iv").run()
    next(b for b in app.button if b.label == "Điền dữ liệu mẫu vào bảng PK").click().run()
    assert not app.exception
    assert app.session_state.pk_route == "iv_bolus"
    assert len(app.session_state.pk_manual_data) > 5
    assert app.session_state.pk_manual_data.time_h.min() == 0.25
    assert not app.session_state.pk_manual_data.time_h.eq(0).any()
    assert any({"time_h", "concentration"} <= set(table.value.columns)
               and len(table.value) > 5 for table in app.dataframe)
    assert not app.session_state.get("pk_current_snapshot")


def test_study_demo_can_be_cleared_for_real_data(tmp_path, monkeypatch):
    import be_app.ui as ui

    monkeypatch.setattr(ui, "store", lambda: ProjectStore(tmp_path / "clear_demo.sqlite"))
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=40).run()
    next(b for b in app.button if b.label == "Điền dữ liệu mẫu vào biểu mẫu nghiên cứu").click().run()
    assert app.session_state.creation_state.draft("create", "is_demo") is True
    next(b for b in app.button if b.label == "Làm trống biểu mẫu nghiên cứu").click().run()
    assert app.session_state.creation_state.draft("create", "is_demo") is None
    assert next(t for t in app.text_input if t.label == "Mã nghiên cứu").value == "BE001"
    next(b for b in app.button if b.label == "Tạo nghiên cứu").click().run()
    assert not app.exception
    assert app.session_state.project.study.is_demo is False
    assert app.session_state.creation_state.draft("create", "is_demo") is None
