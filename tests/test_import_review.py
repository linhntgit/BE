"""Concentration uploads must pass preflight before immutable import."""

import base64
import hashlib
import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from tests.conftest import open_be_page
from be_app.import_review import filtered_concentrations, review_import
from be_app.imports import csv_bytes
from be_app.persistence import Project, ProjectStore


def check(project, frame, mapping="{}", convert=False):
    return review_import(
        csv_bytes(frame), "concentrations.csv", mapping,
        project.study, project.allocation, convert,
    )


def test_valid_file_passes_with_every_volunteer_and_can_be_imported(small_demo):
    project = Project(study=small_demo.study).with_allocation(
        small_demo.allocation, small_demo.allocation_metadata
    )
    frame = small_demo.raw_frame()
    result = check(project, frame)
    assert result.ready
    assert result.frame is not None and len(result.frame) == len(frame) > 30
    assert set(result.frame.subject_id) == set(frame.subject_id)
    saved = project.import_raw(csv_bytes(frame), "valid.csv")
    assert len(saved.raw_frame()) == len(frame)


def test_missing_columns_block_import(small_demo):
    project = Project(study=small_demo.study).with_allocation(
        small_demo.allocation, small_demo.allocation_metadata
    )
    frame = small_demo.raw_frame().drop(columns=["subject_id", "lloq"])
    result = check(project, frame)
    assert not result.ready
    assert set(result.missing) == {"subject_id", "lloq"}
    assert any(flag.code == "MISSING_COLUMNS" for flag in result.qc.flags)
    with pytest.raises(ValueError, match="chưa đạt kiểm tra"):
        project.import_raw(csv_bytes(frame), "incomplete.csv")


@pytest.mark.parametrize("mapping", ["not json", "[]", '{"A": 123}', '{"X": "typo"}'])
def test_invalid_mapping_shows_actionable_error(small_demo, mapping):
    result = check(small_demo, small_demo.raw_frame(), mapping)
    assert not result.ready and result.error


def test_mapping_missing_source_and_duplicate_columns_block(small_demo):
    frame = small_demo.raw_frame()
    missing = check(small_demo, frame, '{"NOT_EXIST": "subject_id"}')
    duplicated = check(small_demo, frame, '{"sample_id": "subject_id"}')
    assert "không tồn tại" in missing.error
    assert "trùng" in duplicated.error


def test_duplicate_header_in_uploaded_csv_is_not_silently_renamed(small_demo):
    result = review_import(
        b"subject_id,subject_id,period\n001,001,1\n",
        "duplicate.csv", "{}", small_demo.study, small_demo.allocation, False,
    )
    assert not result.ready and "trùng" in result.error


def test_renamed_columns_mapping_success_and_extra_columns_visible(small_demo):
    frame = small_demo.raw_frame().rename(columns={"concentration": "CONC"})
    frame["lab_note"] = "training"
    result = check(small_demo, frame, json.dumps({"CONC": "concentration"}))
    assert result.ready and result.extra == ("lab_note",)


def test_invalid_data_or_unit_conversion_requires_recheck(small_demo):
    frame = small_demo.raw_frame()
    frame.loc[0, "blq_flag"] = "perhaps"
    result = check(small_demo, frame)
    assert not result.ready
    assert any(flag.column == "blq_flag" and flag.row == 2 for flag in result.qc.flags)
    frame = small_demo.raw_frame()
    frame["concentration_unit"] = "ug/L"
    assert not check(small_demo, frame).ready
    assert check(small_demo, frame, convert=True).ready


def test_invalid_file_and_missing_allocation(small_demo):
    malformed = review_import(b"not an xlsx", "broken.xlsx", "{}", small_demo.study, small_demo.allocation, False)
    assert not malformed.ready and malformed.error
    missing_allocation = review_import(
        csv_bytes(small_demo.raw_frame()), "valid.csv", "{}", small_demo.study, [], False
    )
    assert not missing_allocation.ready
    assert any(flag.code == "NO_ALLOCATION" for flag in missing_allocation.qc.flags)


def test_full_table_and_filters_show_tail_volunteers(small_demo):
    frame = small_demo.raw_frame()
    all_rows = filtered_concentrations(frame, [], [])
    assert len(all_rows) == len(frame) > 30
    last_subject = str(frame.subject_id.iloc[-1])
    selected = filtered_concentrations(frame, [last_subject], ["2"])
    assert not selected.empty
    assert set(selected.subject_id.astype(str)) == {last_subject}
    assert set(selected.period.astype(str)) == {"2"}
    assert len(selected) < len(frame)


def test_import_page_full_table_and_preflight_button_state(tmp_path, monkeypatch):
    import be_app.ui as ui
    from be_app.examples import demo_project

    database = ProjectStore(tmp_path / "import-ui.sqlite")
    saved_demo = demo_project()
    database.save(saved_demo)
    monkeypatch.setattr(ui, "store", lambda: database)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=40).run()
    next(s for s in app.selectbox if s.label == "Nghiên cứu đã lưu").set_value(saved_demo.project_id).run()
    next(b for b in app.button if b.label == "Mở nghiên cứu đã lưu").click().run()
    open_be_page(app, ui.PAGES[3])
    assert not app.exception

    # The saved table displays every record, including volunteers after row 30.
    saved = app.session_state.active_project_state.project
    rows = saved.raw_frame()
    matches = [d.value for d in app.dataframe if "subject_id" in d.value.columns]
    assert any(len(d) == len(rows) for d in matches)
    assert str(rows.subject_id.iloc[-1]) in set(matches[-1].subject_id.astype(str))

    # Simulate a fresh raw revision and the uploader's persisted draft.
    state = app.session_state.active_project_state
    content = base64.b64decode(saved.raw_base64)
    state.commit(saved.revise("Re-import teaching sample", replace_raw=True))
    state.set_draft(
        "import", "file",
        dict(name="teaching.csv", base64=base64.b64encode(content).decode("ascii"), sha256=hashlib.sha256(content).hexdigest()),
    )
    app.run()
    def import_button():
        return next(b for b in app.button if b.label == "Nhập và lưu raw bất biến")
    assert import_button().disabled
    next(b for b in app.button if b.label == "Kiểm tra cấu trúc và QC").click().run()
    assert not app.exception
    assert not import_button().disabled

    # Changing mapping invalidates the previous success even if the bytes are unchanged.
    next(t for t in app.text_area if t.label.startswith("Mapping JSON")).set_value("{ }").run()
    assert import_button().disabled
    next(b for b in app.button if b.label == "Kiểm tra cấu trúc và QC").click().run()
    assert not app.exception and not import_button().disabled
