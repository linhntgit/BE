"""Demo scenarios stage synthetic inputs into the same widgets used for real work."""

from __future__ import annotations

import base64
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from tests.conftest import open_be_page
from be_app.demo_scenarios import (
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
from be_app.persistence import ProjectStore


@pytest.mark.parametrize("case", STUDY_CASES)
def test_demo_study_scenarios_fill_descriptions(case):
    values = study_values(case)
    assert values["is_demo"] and values["purpose"] == "training_qa"
    assert values["study_id"].startswith("DEMO_")
    assert values["protocol"] and values["sap"]
    assert values["rule"] and values["design"]
    assert "Synthetic" in values["provenance"]


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
