import base64
import io
import json
from dataclasses import replace
from pathlib import Path

import pandas as pd
import pytest
from docx import Document
from streamlit.testing.v1 import AppTest

from tests.conftest import open_be_page
from be_app.domain import BeConfig, NcaConfig, digest
from be_app.examples import demo_project
from be_app.persistence import Project, ProjectStore, export_archive, import_archive
from be_app.pipeline import run_analysis
from be_app.reporting import analysis_exports, docx_report, report_content
from be_app.state import ProjectState, initialize_project_state, result_status


@pytest.fixture
def working_state(tmp_path, small_demo):
    db = ProjectStore(tmp_path / "state.sqlite")
    revision = db.save(small_demo, 0)
    return ProjectState(small_demo, db, revision)


def test_initialize_only_once_and_project_isolation(small_demo):
    session = {}
    first = initialize_project_state(session, small_demo)
    first.set_planning("cv_auc", 24.7)
    first.set_planning("gmr_auc", 0.93)
    assert initialize_project_state(session, small_demo) is first
    other = demo_project(n=4)
    second = initialize_project_state(session, other)
    assert second.project.project_id != first.project.project_id
    assert second.planning()["cv_auc"] == 20
    separate_session = initialize_project_state({}, small_demo)
    assert separate_session.profile_cache is not first.profile_cache
    assert separate_session.planning()["cv_auc"] == 20


def test_lightweight_journal_and_reload_without_checkpoint(working_state, monkeypatch):
    state = working_state
    original = state.project
    monkeypatch.setattr(Project, "input_hash", lambda *_: pytest.fail("Full input hash during a light edit"))
    state.set_planning("cv_auc", 24.7)
    state.set_planning("gmr_auc", 0.93)
    state.set_draft("revision", "reason", "Draft retained")
    assert state.project.raw_base64 is original.raw_base64
    assert state.project.runs is original.runs
    assert state.project.input_revision == original.input_revision
    with state.store.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0] == 1
        payloads = [json.loads(row[0]) for row in db.execute("SELECT payload FROM working_changes")]
        assert len(payloads) == 3 and all(
            "raw_base64" not in patch and "runs" not in patch for patch in payloads
        )
    monkeypatch.undo()
    restored = state.store.load(state.project.project_id)
    assert restored.planning_inputs["cv_auc"] == 24.7 and restored.planning_inputs["gmr_auc"] == 0.93
    assert restored.drafts["revision"]["reason"] == "Draft retained"


def test_conflict_does_not_change_canonical_or_half_save(working_state):
    a = working_state
    b = ProjectState(a.project, a.store, a.db_revision, a.working_revision)
    a.set_planning("cv_auc", 24.7)
    before = b.project
    with pytest.raises(ValueError, match="phiên khác"):
        b.set_planning("gmr_auc", 0.93)
    assert b.project is before
    restored = a.store.load(a.project.project_id)
    assert restored.planning_inputs["cv_auc"] == 24.7
    assert "gmr_auc" in restored.planning_inputs and restored.planning_inputs["gmr_auc"] == 0.95


def sample_binding(state):
    return state.editor_binding("S0001", "2")


def test_three_consecutive_editor_diffs_navigation_checkpoint_archive(working_state):
    state = working_state
    binding = sample_binding(state)
    edits = {}
    for row, value in [(1, "123.7"), (2, "225.4"), (3, "331.9")]:
        edits[row] = {"concentration": value}
        state.editor_diff(binding, {"edited_rows": dict(edits), "added_rows": [], "deleted_rows": []})
    state._bindings.clear()  # Widget removed during navigation.
    restored_binding = sample_binding(state)
    assert restored_binding.baseline.concentration.iloc[1:4].tolist() == ["123.7", "225.4", "331.9"]
    assert len(state.project.pending_edits) == 3
    state.checkpoint()
    saved = state.store.load(state.project.project_id)
    reopened = import_archive(export_archive(saved))
    assert reopened.pending_edits == state.project.pending_edits
    before_revision = state.project.dataset_revision
    state.apply_pending("Correction from assay source", "independent-QA", "LAB-003")
    assert not state.project.pending_edits
    assert state.project.dataset_revision == before_revision + 1
    actual = state.clean_frame().set_index("sample_id")
    for row, value in [(1, "123.7"), (2, "225.4"), (3, "331.9")]:
        assert actual.at[binding.sample_ids[row], "concentration"] == value
    assert base64.b64decode(state.project.raw_base64) == base64.b64decode(saved.raw_base64)


@pytest.mark.parametrize(
    "diff",
    [
        {"added_rows": [{"concentration": "10"}]},
        {"deleted_rows": [0]},
        {"edited_rows": {999: {"concentration": "12"}}},
        {"edited_rows": {1: {"sample_id": "another"}}},
        {"edited_rows": {1: {"concentration": "100"}, 2: {"concentration": "invalid"}}},
    ],
)
def test_editor_invalid_patch_is_atomic(working_state, diff):
    before = working_state.project
    with pytest.raises((ValueError, TypeError)):
        working_state.editor_diff(sample_binding(working_state), diff)
    assert working_state.project is before


def test_editor_cell_patch_does_not_copy_full_dataframe(working_state, monkeypatch):
    state = working_state
    binding = sample_binding(state)
    state.clean_frame()
    monkeypatch.setattr(
        pd.DataFrame, "copy", lambda *_a, **_k: pytest.fail("Full dataframe copy on editor callback")
    )
    state.editor_diff(binding, {"edited_rows": {3: {"concentration": "333.7"}}})
    assert state.project.pending_edits[binding.sample_ids[3]]["concentration"] == "333.7"


def test_import_preview_draft_and_corrections_survive_restart(working_state):
    state = working_state
    staged = dict(name="assay.csv", base64=state.project.raw_base64)
    state.set_draft("import", "file", staged)
    state.set_draft("import", "mapping", '{"Cplasma":"concentration"}')
    state.editor_diff(sample_binding(state), {"edited_rows": {2: {"concentration": "211"}}})
    loaded, base_revision, working_revision = state.store.checkout(state.project.project_id)
    restarted = ProjectState(loaded, state.store, base_revision, working_revision)
    assert restarted.draft("import", "file") == staged
    assert restarted.project.pending_edits == state.project.pending_edits
    assert restarted.draft("import", "mapping") == '{"Cplasma":"concentration"}'
    with pytest.raises(ValueError, match="Chưa áp dụng"):
        loaded.revise("Another assay file", replace_raw=True)


def test_callback_exception_retains_confirmed_domain(working_state, monkeypatch):
    from be_app import widgets

    state = working_state
    before = state.project
    session = {"cv-widget": -5.0}
    monkeypatch.setattr(widgets.st, "session_state", session)
    widgets.changed(state, "planning", "planning", "cv_auc", "cv-widget")
    assert state.project is before
    assert "callback_error" in session
    assert session["cv-widget"] == 20.0


def test_checkout_conflict_tokens_are_atomic(working_state):
    state = working_state
    state.set_draft("revision", "reason", "First author")
    loaded, base, head = state.store.checkout(state.project.project_id)
    assert head == 1 and loaded.drafts["revision"]["reason"] == "First author"
    rival = ProjectState(loaded, state.store, base, head)
    state.set_draft("revision", "reason", "Newer author")
    with pytest.raises(ValueError, match="phiên khác"):
        rival.set_draft("revision", "reason", "Must not overwrite unseen patch")


def test_planning_draft_values_and_preferences_survive_archive(working_state):
    state = working_state
    state.set_planning("cv_auc", 24.7)
    state.set_planning("gmr_auc", 0.93)
    state.set_draft("nca_config", "integration", "linear")
    state.set_preference("report.language", "en")
    reopened = import_archive(export_archive(state.project))
    assert reopened.planning_inputs == state.project.planning_inputs
    assert reopened.drafts == state.project.drafts
    assert reopened.preferences == state.project.preferences


def test_editor_reordered_schema_and_stale_revision_rejected(working_state):
    binding = sample_binding(working_state)
    moved = replace(binding, baseline=binding.baseline.iloc[::-1])
    with pytest.raises(ValueError, match="Thứ tự"):
        working_state.editor_diff(moved, {"edited_rows": {1: {"concentration": "100"}}})
    with pytest.raises(ValueError, match="phiên bản"):
        working_state.editor_diff(replace(binding, dataset_revision=-1), {})


def test_snapshot_matches_edited_cells_and_report_manifest(demo):
    state = ProjectState(demo)
    binding = sample_binding(state)
    sid = binding.sample_ids[3]
    state.editor_diff(binding, {"edited_rows": {3: {"concentration": "333.12345678901234"}}})
    state.apply_pending("Assay correction", "QA", "LAB-100")
    state.freeze()
    state.analyze()
    run = state.project.runs[-1]
    selected = next(row for row in run["validated_data"] if row["sample_id"] == sid)
    assert selected["concentration"] == float("333.12345678901234")
    assert run["dataset_hash"] == digest(run["validated_data"])
    assert run["input_revision"] == state.project.input_revision
    assert result_status(state.project) == "CURRENT"
    exports = analysis_exports(state.project)
    manifest = json.loads(exports["input_manifest.json"])
    assert manifest["input_fingerprint"] == state.project.input_fingerprint == run["input_hash"]
    csv = pd.read_csv(io.BytesIO(exports["validated.csv"]))
    assert csv.loc[csv.sample_id.eq(sid), "concentration"].iloc[0] == pytest.approx(selected["concentration"])
    assert report_content(state.project)["manifest"] == manifest
    document = Document(io.BytesIO(docx_report(state.project)))
    assert manifest["input_fingerprint"] in " ".join(p.text for p in document.paragraphs)


def test_stale_is_immediate_for_pending_and_committed_and_reports_blocked(demo):
    state = ProjectState(demo)
    state.freeze()
    state.analyze()
    original = state.project.runs[-1]
    state.commit(state.project.revise("Review correction"))
    binding = sample_binding(state)
    state.editor_diff(binding, {"edited_rows": {3: {"concentration": "333.7"}}})
    assert result_status(state.project) == "STALE"
    with pytest.raises(ValueError, match="STALE"):
        report_content(state.project)
    state.apply_pending("Source correction", "QA", "LAB-200")
    assert result_status(state.project) == "STALE" and state.project.runs[-1] == original
    state.freeze()
    state.analyze()
    assert result_status(state.project) == "CURRENT"
    assert result_status(state.project, original) == "STALE"


def test_only_changed_profile_recomputes_and_display_preferences_do_not(demo):
    state = ProjectState(demo)
    state.freeze()
    state.analyze()
    count = len(state.project.runs[-1]["nca"])
    assert state.metrics["nca_profiles_computed"] == count
    state.set_planning("gmr_auc", 0.93)
    state.set_preference("language", "en")
    assert result_status(state.project) == "CURRENT"
    assert state.metrics["analyses"] == 1
    state.commit(state.project.revise("Correction"))
    state.editor_diff(sample_binding(state), {"edited_rows": {3: {"concentration": "250"}}})
    state.apply_pending("Reason", "QA", "Evidence")
    state.freeze()
    state.analyze()
    assert state.project.runs[-1]["computation"] == {
        "nca_profiles_computed": 1,
        "nca_profiles_reused": count - 1,
    }


def test_config_dependency_graph_keeps_nca_for_be_only_changes(demo):
    state = ProjectState(demo)
    state.freeze()
    state.analyze()
    count = len(state.project.runs[-1]["nca"])
    state.commit(
        state.project.revise("Prespecified variance change", be_config=BeConfig(parallel_variance="welch"))
    )
    state.freeze()
    state.analyze()
    assert state.project.runs[-1]["computation"] == {"nca_profiles_computed": 0, "nca_profiles_reused": count}
    state.commit(state.project.revise("NCA integration change", nca_config=NcaConfig(integration="linear")))
    state.freeze()
    state.analyze()
    assert state.project.runs[-1]["computation"] == {"nca_profiles_computed": count, "nca_profiles_reused": 0}


def test_unapplied_config_blocks_old_report_without_touching_old_run(demo):
    state = ProjectState(demo)
    state.freeze()
    state.analyze()
    old = state.project.runs[-1]
    state.set_draft("nca_config", "integration", "linear")
    assert result_status(state.project) == "STALE"
    assert state.project.runs[-1] is old
    with pytest.raises(ValueError, match="STALE"):
        report_content(state.project)


def test_qc_cache_and_no_full_hash_during_navigation(demo, monkeypatch):
    state = ProjectState(demo)
    state.qc()
    monkeypatch.setattr(Project, "qc", lambda *_: pytest.fail("full QC called on navigation"))
    monkeypatch.setattr(Project, "input_hash", lambda *_: pytest.fail("full hash called on navigation"))
    for _ in range(10):
        state.qc()
        state.raw_frame()
        result_status(state.project)
    assert state.metrics["qc_calls"] == 1
    assert state.metrics["analyses"] == 0


def test_analysis_does_not_overwrite_concurrent_preferences(demo, monkeypatch):
    import be_app.pipeline as pipeline

    state = ProjectState(demo)
    state.freeze()
    original = pipeline.run_analysis

    def work(project, **kwargs):
        state.set_preference("report.language", "en")
        return original(project, **kwargs)

    monkeypatch.setattr(pipeline, "run_analysis", work)
    state.analyze()
    assert state.project.preferences["report.language"] == "en"
    assert result_status(state.project) == "CURRENT"


def test_input_change_during_calculation_is_not_published_as_current(demo, monkeypatch):
    import be_app.pipeline as pipeline

    state = ProjectState(demo)
    state.freeze()
    original = pipeline.run_analysis

    def work(project, **kwargs):
        state.commit(
            state.project.revise("Changed during run", be_config=BeConfig(parallel_variance="welch"))
        )
        return original(project, **kwargs)

    monkeypatch.setattr(pipeline, "run_analysis", work)
    with pytest.raises(ValueError, match="đổi khi đang phân tích"):
        state.analyze()
    assert not state.project.runs


def test_revision_design_change_rejected_without_deleting_data(small_demo):
    before = small_demo.model_dump_json()
    with pytest.raises(ValueError, match="thiết kế"):
        small_demo.revise(
            "Change to replicate", study=small_demo.study.model_copy(update={"design": "full4"})
        )
    assert small_demo.model_dump_json() == before


def test_snapshot_qc_mismatch_and_config_draft_are_blocked(demo):
    state = ProjectState(demo)
    state.set_draft("nca_config", "r2", 0.7)
    with pytest.raises(ValueError):
        state.freeze()
    state.commit(
        state.project.record(
            "configure", {"nca_config": NcaConfig(terminal_min_adj_r2=0.7).model_dump(mode="json")}, "Apply"
        )
    )
    state.freeze()
    with pytest.raises(ValueError, match="fingerprint"):
        run_analysis(state.project, qc_result=replace(state.qc(), source_fingerprint="other-dataset"))


def test_schema1_migration_preserves_data_and_legacy_run(demo):
    project = run_analysis(demo.freeze())
    data = project.model_dump(mode="json")
    data["schema_version"] = 1
    for key in (
        "input_revision",
        "dataset_revision",
        "config_revision",
        "nca_config_revision",
        "be_config_revision",
        "input_fingerprint",
    ):
        data.pop(key)
    legacy_run = dict(data["runs"][0])
    legacy_run.pop("input_revision")
    legacy_run["snapshot_hash"] = digest({k: v for k, v in legacy_run.items() if k != "snapshot_hash"})
    data["runs"] = [legacy_run]
    from be_app.persistence import load_project_payload

    restored = load_project_payload(json.dumps(data))
    assert restored.schema_version == 2 and restored.raw_base64 == project.raw_base64
    assert result_status(restored) == "LEGACY"


def app_instance(tmp_path, monkeypatch):
    import be_app.ui as ui

    database = ProjectStore(tmp_path / "state-ui.sqlite")
    saved_demo = demo_project()
    database.save(saved_demo)
    monkeypatch.setattr(ui, "store", lambda: database)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=30).run()
    next(s for s in app.selectbox if s.label == "Nghiên cứu đã lưu").set_value(saved_demo.project_id).run()
    next(b for b in app.button if b.label == "Mở nghiên cứu đã lưu").click().run()
    assert app.session_state.project.raw_base64
    return app


def test_apptest_cv_ratio_navigation_reload_and_power_inputs(tmp_path, monkeypatch):
    import be_app.ui as ui

    app = app_instance(tmp_path, monkeypatch)
    open_be_page(app, ui.PAGES[1])
    next(w for w in app.number_input if w.label == "CV AUC (%)").set_value(24.7).run()
    next(w for w in app.number_input if w.label == "GMR dự kiến AUC (T/R)").set_value(0.93).run()
    next(w for w in app.text_input if w.label == "Nguồn CV và giả định thiết kế").set_value(
        "Pilot study protocol"
    ).run()
    open_be_page(app, ui.PAGES[5])
    open_be_page(app, ui.PAGES[1])
    assert next(w for w in app.number_input if w.label == "CV AUC (%)").value == 24.7
    assert next(w for w in app.number_input if w.label == "GMR dự kiến AUC (T/R)").value == 0.93
    assert app.session_state.project.planning_inputs["cv_auc"] == 24.7
    next(b for b in app.button if b.label == "Tính cỡ mẫu và power").click().run()
    assert not app.exception and not app.error
    plan = app.session_state.project.allocation_metadata["sample_size_plan"]
    assert plan["inputs"]["cv_auc"] == 24.7 and plan["inputs"]["gmr_auc"] == 0.93
    db = app.session_state.active_project_state.store
    restored = db.load(app.session_state.project.project_id)
    assert restored.planning_inputs == app.session_state.project.planning_inputs


def test_apptest_editor_pending_navigation_and_batch_apply(tmp_path, monkeypatch):
    import be_app.ui as ui

    app = app_instance(tmp_path, monkeypatch)
    open_be_page(app, ui.PAGES[4])
    state = app.session_state.active_project_state
    binding = state.editor_binding("S0001", "2")
    # Streamlit stores a diff, not a DataFrame. Exercise the exact callback contract.
    for row, value in [(1, "123.7"), (2, "225.4"), (3, "331.9")]:
        state.editor_diff(binding, {"edited_rows": {row: {"concentration": value}}})
    open_be_page(app, ui.PAGES[5])
    assert next(b for b in app.button if b.label == "Phân tích NCA và BE").disabled
    open_be_page(app, ui.PAGES[4])
    assert app.session_state.active_project_state.project.pending_edits
    for label, value in [
        ("Lý do correction", "Assay correction"),
        ("Người rà soát độc lập", "QA"),
        ("Tham chiếu bằng chứng correction", "LAB-123"),
    ]:
        next(w for w in app.text_input if w.label == label).set_value(value).run()
    next(b for b in app.button if b.label == "Áp dụng các sửa đổi").click().run()
    assert not app.error and not app.exception
    assert not app.session_state.project.pending_edits
    actual = app.session_state.active_project_state.clean_frame().set_index("sample_id")
    assert actual.at[binding.sample_ids[3], "concentration"] == "331.9"


def test_apptest_no_stale_decision_on_all_result_pages(tmp_path, monkeypatch):
    import be_app.ui as ui

    app = app_instance(tmp_path, monkeypatch)
    state = app.session_state.active_project_state
    state.freeze()
    state.analyze()
    state.commit(state.project.revise("Correction"))
    state.editor_diff(sample_binding(state), {"edited_rows": {3: {"concentration": "333"}}})
    for page in (ui.PAGES[5], ui.PAGES[6], ui.PAGES[7], ui.PAGES[8]):
        open_be_page(app, page)
        assert not app.error and not app.exception
        assert any("STALE" in w.value for w in app.warning)
        assert not any(
            h.value in ("Đạt tiêu chí thống kê", "Không đạt tiêu chí thống kê") for h in app.subheader
        )
        if page == ui.PAGES[8]:
            assert next(b for b in app.button if b.label == "Tạo Word và PDF dự thảo").disabled
