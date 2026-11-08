import io
import json
import sqlite3
import zipfile

import pytest

from be_app.domain import BeConfig, digest
from be_app.examples import demo_project
from be_app.imports import correction
from be_app.persistence import ProjectStore, export_archive, import_archive, verify_project
from be_app.pipeline import run_analysis


@pytest.fixture(scope="module")
def analyzed(demo):
    return run_analysis(demo.freeze())


def test_pipeline_demo_no_study_pass(analyzed):
    run = analyzed.runs[-1]
    assert len(run["nca"]) == 24 and len(run["be"]) == 3
    assert run["study_decision"] == "NOT EVALUABLE"
    assert run["reviewer"] is None and run["regulatory_status"].startswith("DRAFT")
    assert run["rule_snapshot"]["source_verified_on"] == "2026-10-30"


def test_no_analysis_before_freeze(demo):
    with pytest.raises(ValueError):
        run_analysis(demo)


@pytest.mark.parametrize("design", ["2x2", "parallel"])
@pytest.mark.parametrize("rule", ["EMA_IR_NONREPLICATE_M13A", "FDA_ABE_2026"])
def test_supported_pipeline_designs_and_rules(design, rule):
    # Synthetic fixture exercising production aggregation, not a real-study assertion.
    project = demo_project(design=design, n=24)
    study = project.study.model_copy(update={"is_demo": False, "rule_set_id": rule})
    run = run_analysis(project.revise("Synthetic test of production gate", study=study).freeze()).runs[-1]
    assert len(run["blockers"]) == 1
    assert all(result["decision"] in ("PASS", "FAIL") for result in run["be"])
    # A synthetic fixture remains training/QA even when is_demo is cleared.
    assert run["study"]["data_purpose"] == "training_qa"
    assert run["study_decision"] == "NOT EVALUABLE"
    assert any("đào tạo/QA" in reason for reason in run["blockers"])


@pytest.mark.parametrize("purpose", ["unknown", "method_development"])
def test_nonregulated_data_purpose_never_produces_study_pass(demo, purpose):
    study = demo.study.model_copy(update={"is_demo": False, "data_purpose": purpose})
    project = demo.revise("QA purpose gate", study=study).freeze()
    run = run_analysis(project).runs[-1]
    assert run["study_decision"] == "NOT EVALUABLE"
    assert any("mục đích nghiên cứu thật" in reason for reason in run["blockers"])


def test_scope_unverified_blocks_endpoint(demo):
    study = demo.study.model_copy(update={"scope_reviewed": False})
    project = demo.revise("Scope not yet reviewed", study=study).freeze()
    run = run_analysis(project).runs[-1]
    assert all(r["decision"] == "NOT EVALUABLE" for r in run["be"])


def test_insufficient_n_cannot_pass(small_demo):
    run = run_analysis(small_demo.freeze()).runs[-1]
    assert all(r["decision"] == "NOT EVALUABLE" for r in run["be"])


def test_custom_limits_cannot_masquerade_as_profile(demo):
    project = demo.revise("Custom exploratory limits", be_config=BeConfig(lower=0.7, upper=1.4)).freeze()
    assert run_analysis(project).runs[-1]["study_decision"] == "NOT EVALUABLE"


def test_freeze_immutable_and_revision_preserves_runs(analyzed):
    with pytest.raises(ValueError):
        analyzed.import_raw(b"x", "x.csv")
    change = correction(analyzed.clean_frame(), 1, "source_batch", "NEW", "reason", "DM", "QA", "evidence")
    with pytest.raises(ValueError):
        analyzed.corrected(change)
    revised = analyzed.revise("Independent review requested change")
    assert revised.runs == analyzed.runs and not revised.freeze_hash
    updated = run_analysis(revised.freeze())
    assert len(updated.runs) == 2 and updated.runs[0] == analyzed.runs[0]
    assert updated.runs[0]["dataset_hash"] == updated.runs[1]["dataset_hash"]


def test_replacing_raw_retains_original(analyzed):
    revised = analyzed.revise("New raw file received", replace_raw=True)
    assert revised.raw_history[-1]["raw_base64"] == analyzed.raw_base64
    assert not revised.raw_base64


def test_archive_roundtrip_no_refit(analyzed, monkeypatch):
    import be_app.statistics

    monkeypatch.setattr(be_app.statistics, "analyze_abe", lambda *a, **k: pytest.fail("Refit on reload"))
    content = export_archive(analyzed)
    restored = import_archive(content)
    assert restored == analyzed
    assert export_archive(restored) == content
    assert restored.runs[-1]["snapshot_hash"] == analyzed.runs[-1]["snapshot_hash"]


def test_sqlite_append_only_backup_and_conflict(analyzed, tmp_path):
    store = ProjectStore(tmp_path / "projects.sqlite")
    assert store.save(analyzed, 0) == 1
    assert store.save(analyzed, 1) == 2
    with pytest.raises(ValueError):
        store.save(analyzed, 1)
    assert store.load(analyzed.project_id, 1) == analyzed
    assert store.list_projects()[0]["revision"] == 2
    with store.connect() as db:
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("UPDATE snapshots SET study_id='tamper'")
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("DELETE FROM snapshots")
    store.backup(tmp_path / "backup.sqlite")
    assert ProjectStore(tmp_path / "backup.sqlite").load(analyzed.project_id) == analyzed


def make_zip(items):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in items:
            archive.writestr(name, content)
    return output.getvalue()


@pytest.mark.parametrize("name", ["../project.json", "/project.json", "C:\\project.json", "extra.exe"])
def test_archive_path_traversal_and_extra_files_rejected(name):
    with pytest.raises(ValueError):
        import_archive(make_zip([("manifest.json", "{}"), (name, "{}")]))


def test_checksum_schema_and_audit_tampering_rejected(analyzed):
    content = export_archive(analyzed)
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        manifest = archive.read("manifest.json")
        data = json.loads(archive.read("project.json"))
    data["study"]["title"] = "Tampered"
    with pytest.raises(ValueError):
        import_archive(make_zip([("manifest.json", manifest), ("project.json", json.dumps(data))]))
    data = analyzed.model_copy(deep=True)
    data.events[0]["actor"] = "tamper"
    with pytest.raises(ValueError):
        verify_project(data)
    data = analyzed.model_copy(deep=True)
    data.runs[0]["study_decision"] = "PASS"
    with pytest.raises(ValueError):
        verify_project(data)
    data = analyzed.revise("Future schema").model_copy(update={"schema_version": 999})
    with pytest.raises(ValueError):
        export_archive(data)


def test_freeze_hash_detects_direct_edit(analyzed):
    changed = analyzed.model_copy(update={"be_config": BeConfig(lower=0.7)})
    with pytest.raises(ValueError):
        run_analysis(changed)


def test_snapshot_content_hash(analyzed):
    run = analyzed.runs[-1]
    assert run["snapshot_hash"] == digest({k: v for k, v in run.items() if k != "snapshot_hash"})
