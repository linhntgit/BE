"""Editable table behavior without relying on Streamlit's private widget internals."""

from contextlib import nullcontext
from io import BytesIO

import pandas as pd
import pytest

from be_app.import_review import review_import
from be_app.imports import parse_file
from be_app.table_editor import (
    combine_column_mappings,
    prepare_blq_editor,
    render_persistent_editor,
    suggest_column_mapping,
    validate_structure,
)


def test_blq_checkbox_default_for_inserted_rows_keeps_existing_flags():
    frame = pd.DataFrame({"id": ["A", "B"], "BLQ": ["true", "false"],
                          "blq_flag": [True, False]})
    prepared, config = prepare_blq_editor(frame)
    assert prepared["BLQ"].tolist() == [True, False]
    assert prepared["blq_flag"].tolist() == [True, False]
    assert all(str(prepared[key].dtype) == "bool" for key in ("BLQ", "blq_flag"))
    assert config["BLQ"]["default"] is False
    assert config["blq_flag"]["default"] is False
    assert frame["BLQ"].tolist() == ["true", "false"]


def test_invalid_blq_values_remain_visible_for_qc():
    frame = pd.DataFrame({"BLQ": ["false", "unknown"]})
    prepared, config = prepare_blq_editor(frame)
    assert prepared.equals(frame)
    assert "BLQ" not in config


def test_empty_or_new_blq_cells_default_to_false_checkbox():
    # Empty manual template or added row with empty string / None / NaN
    frame = pd.DataFrame({"BLQ": ["", None, "true", False]})
    prepared, config = prepare_blq_editor(frame)
    assert prepared["BLQ"].tolist() == [False, False, True, False]
    assert str(prepared["BLQ"].dtype) == "bool"
    assert config["BLQ"]["default"] is False
    assert config["BLQ"]["required"] is True

    # Empty frame with BLQ column
    empty_frame = pd.DataFrame(columns=["Subject", "BLQ"])
    prepared_empty, config_empty = prepare_blq_editor(empty_frame)
    assert str(prepared_empty["BLQ"].dtype) == "bool"
    assert config_empty["BLQ"]["default"] is False


def test_header_matching_is_order_independent_and_casefolded():
    assert suggest_column_mapping(
        [" COncentration ", "subject_id", "PERIOD", "Column X"],
        ["period", "subject_id", "concentration"],
    ) == {" COncentration ": "concentration", "PERIOD": "period"}


@pytest.mark.parametrize("names", [["SUBJECT", "subject"], [" x", "X "], ["A", "A"]])
def test_ambiguous_headers_are_rejected(names):
    with pytest.raises(ValueError, match="trùng"):
        suggest_column_mapping(names, ["subject", "treatment"])


def test_manual_mapping_overrides_saved_json_and_can_keep_source_header():
    automatic = {" SUBJECT ": "subject_id", "PERIOD": "period"}
    legacy = {" SUBJECT ": "sample_id", "dose": "dose_datetime"}
    manual = {" SUBJECT ": "subject_id", "PERIOD": None, "dose": None}
    assert combine_column_mappings(automatic, legacy, manual) == {
        " SUBJECT ": "subject_id",
    }


def test_excel_and_bom_csv_preserve_identifiers_when_mapped():
    frame = pd.DataFrame({"  SUBJECT ": ["001", "002"], "CPLASMA": ["1.5", "2.5"]})
    csv = frame.to_csv(index=False).encode("utf-8-sig")
    excel = BytesIO()
    frame.to_excel(excel, index=False)
    for content, name in ((csv, "upload.csv"), (excel.getvalue(), "upload.xlsx")):
        parsed = parse_file(content, name)
        mapping = suggest_column_mapping(parsed.columns, ("subject", "cplasma"))
        mapped = parsed.rename(columns=mapping)
        assert list(mapped.columns) == ["subject", "cplasma"]
        assert mapped.subject.tolist() == ["001", "002"]


def test_structure_rejects_missing_and_oversized_tables():
    frame = pd.DataFrame({"sample_id": ["A", "B"]})
    with pytest.raises(ValueError, match="Thiếu cột"):
        validate_structure(frame, required=["sample_id", "time_h"])
    with pytest.raises(ValueError, match="giới hạn"):
        validate_structure(frame, max_rows=1)


class FakeStreamlit:
    def __init__(self):
        self.session_state = {}
        self.proposed = None
        self.submitted = False
        self.messages = []
        self.keys = []

    def form(self, **kwargs):
        return nullcontext()

    def data_editor(self, frame, **kwargs):
        self.keys.append(kwargs["key"])
        return self.proposed.copy() if self.proposed is not None else frame.copy()

    def form_submit_button(self, label):
        return self.submitted

    def success(self, text):
        self.messages.append(("success", text))

    def error(self, text):
        self.messages.append(("error", text))


def test_form_commits_only_valid_submission_and_preserves_invalid_draft(monkeypatch):
    import be_app.table_editor as module

    fake = FakeStreamlit()
    monkeypatch.setattr(module, "st", fake)
    initial = pd.DataFrame({"id": ["001", "002"], "value": ["1", "2"]})

    def validate(data):
        if data.value.eq("bad").any():
            raise ValueError("invalid numerical value")
        return data

    def render():
        return render_persistent_editor("demo", initial, "source-a", validator=validate)

    # An unsubmitted deletion and pasted edit cannot affect calculations.
    fake.proposed = pd.DataFrame({"id": ["002"], "value": ["5"]})
    assert render().equals(initial)
    fake.submitted = True
    assert render().id.tolist() == ["002"]

    # Invalid multirow paste does not overwrite the last committed values.
    fake.proposed = pd.DataFrame({"id": ["002", "003"], "value": ["5", "bad"]})
    assert render().id.tolist() == ["002"]
    assert fake.session_state["table::demo"]["draft"].id.tolist() == ["002", "003"]
    assert any(level == "error" for level, _ in fake.messages)

    fake.proposed = pd.DataFrame({"id": ["002", "003"], "value": ["5", "6"]})
    assert render().id.tolist() == ["002", "003"]
    assert fake.keys[0] == fake.keys[1]  # Normal rerender keeps edit focus.
    assert len(set(fake.keys[1:])) == 3  # Submission rotates the instance.

    # A new file/sheet intentionally replaces the editor and canonical state.
    fake.submitted = False
    fake.proposed = None
    replaced = render_persistent_editor("demo", initial, "source-b", validator=validate)
    assert replaced.equals(initial)


def test_qc_full_table_row_deletion_archives_original_raw(small_demo):
    original = small_demo.raw_frame()
    replacement = small_demo.clean_frame().iloc[:-1].astype(str)
    csv = replacement.to_csv(index=False).encode("utf-8-sig")
    review = review_import(
        csv, "qc_revised.csv", "{}", small_demo.study,
        small_demo.allocation, small_demo.allow_unit_conversion,
    )
    assert review.ready, review.error or (review.qc.report() if review.qc else None)
    revised = small_demo.revise("Sample withdrawn following independent QC", replace_raw=True)
    revised = revised.import_raw(
        csv, "qc_revised.csv", mapping={},
        convert_units=small_demo.allow_unit_conversion,
    )
    assert len(revised.raw_frame()) == len(original) - 1
    assert len(revised.raw_history) == len(small_demo.raw_history) + 1
    assert revised.raw_history[-1]["raw_base64"] == small_demo.raw_base64
    assert revised.dataset_revision > small_demo.dataset_revision


def test_apply_editor_changes_handles_edits_adds_and_deletions():
    from be_app.table_editor import _apply_editor_changes

    base = pd.DataFrame([
        {"id": "001", "val": 10.0, "blq": False},
        {"id": "002", "val": 20.0, "blq": True},
        {"id": "003", "val": 30.0, "blq": False},
    ])
    delta = {
        "edited_rows": {"0": {"val": 15.0}},
        "deleted_rows": [1],
        "added_rows": [{"id": "004", "val": 40.0}],
    }
    updated = _apply_editor_changes(base, delta)
    assert len(updated) == 3
    assert updated.iloc[0]["val"] == 15.0
    assert updated.iloc[1]["id"] == "003"
    assert updated.iloc[2]["id"] == "004"
    assert bool(updated.iloc[2]["blq"]) is False  # BLQ auto-defaulted to False


def test_render_persistent_editor_apptest_editing_and_submission():
    from streamlit.testing.v1 import AppTest

    def app():
        import pandas as pd
        import streamlit as st
        from be_app.table_editor import render_persistent_editor
        initial = pd.DataFrame([{"profile_id": "PK01", "time_h": 0.0, "concentration": 0.0, "blq": False}])
        committed = render_persistent_editor("test_pk", initial, "src_test")
        st.session_state["saved_res"] = committed

    at = AppTest.from_function(app).run()
    assert at.session_state["saved_res"].iloc[0]["time_h"] == 0.0

    # Simulate user entering rows
    editor_key = [k for k in at.session_state.keys() if k.startswith("table_editor::test_pk")][0]
    at.session_state[editor_key] = {
        "edited_rows": {0: {"time_h": 0.0, "concentration": 0.0, "blq": False}},
        "added_rows": [{"profile_id": "PK01", "time_h": 1.0, "concentration": 25.5}],
        "deleted_rows": [],
    }
    submit_btn = at.form_submit_button[0]
    submit_btn.click().run()

    # The table must be committed and have 2 rows, not reverted to 1 row
    saved = at.session_state["saved_res"]
    assert len(saved) == 2
    assert saved.iloc[1]["time_h"] == 1.0
    assert saved.iloc[1]["concentration"] == 25.5
    assert bool(saved.iloc[1]["blq"]) is False


def test_apply_editor_changes_handles_adding_then_deleting_row():
    from be_app.table_editor import _apply_editor_changes

    base = pd.DataFrame([
        {"id": "001", "val": 10.0, "blq": False},
        {"id": "002", "val": 20.0, "blq": True},
    ])
    # User added a 3rd row, then deleted it
    delta = {
        "edited_rows": {},
        "added_rows": [{"id": "003", "val": 30.0, "blq": False}],
        "deleted_rows": [2],
    }
    updated = _apply_editor_changes(base, delta)
    assert len(updated) == 2
    assert updated.iloc[0]["id"] == "001"
    assert updated.iloc[1]["id"] == "002"


def test_render_persistent_editor_drops_blank_rows_with_blq_default():
    from streamlit.testing.v1 import AppTest
    from be_app.pk_analysis import validate_profiles

    def app():
        import pandas as pd
        import streamlit as st
        from be_app.table_editor import render_persistent_editor
        from be_app.pk_analysis import validate_profiles

        initial = pd.DataFrame([
            {"profile_id": "PK01", "time_h": 0.0, "concentration": 0.0, "blq": False},
            {"profile_id": "PK02", "time_h": 1.0, "concentration": 1.0, "blq": False},
        ])
        committed = render_persistent_editor("test_pk_blank", initial, "src_blank", validator=validate_profiles)
        st.session_state["committed_result"] = committed

    at = AppTest.from_function(app).run()

    # User appends an empty row (e.g. via '+', with all fields None and blq False)
    editor_key = [k for k in at.session_state.keys() if k.startswith("table_editor::test_pk_blank")][0]
    at.session_state[editor_key] = {
        "edited_rows": {},
        "added_rows": [{"profile_id": None, "time_h": None, "concentration": None, "blq": False}],
        "deleted_rows": [],
    }
    at.form_submit_button[0].click().run()

    # The blank row must be cleanly dropped without causing "Mã hồ sơ không được trống" error
    assert at.session_state.get("_editor_error::test_pk_blank") is None
    committed = at.session_state["committed_result"]
    assert len(committed) == 2
    assert committed.iloc[0]["profile_id"] == "PK01"
    assert committed.iloc[1]["profile_id"] == "PK02"


