"""User-facing workflow status must follow the saved snapshot and its revision."""

from be_app.pipeline import run_analysis
import pytest
from be_app.reporting import report_content
from be_app.persistence import export_archive, import_archive
from be_app.workflow_status import workflow_progress


def test_workflow_progress_and_next_action(demo):
    rows, action = workflow_progress(demo)
    assert len(rows) == 6
    assert rows[2]["Trạng thái"] == "Cần rà soát QC"
    assert rows[4]["Trạng thái"] in ("Chưa chạy", "STALE")
    assert "Data Freeze" in action

    frozen = demo.freeze()
    rows, action = workflow_progress(frozen)
    assert rows[2]["Trạng thái"] == "Đã khóa"
    assert rows[3]["Trạng thái"] == "Chưa chạy"
    assert "NCA" in action


def test_review_evidence_bound_to_run_and_market(demo):
    project = run_analysis(demo.freeze())
    run = project.runs[-1]
    reviewed = project.record_review(run["snapshot_hash"], "Reviewer", "QC-12", "reviewed")
    restored = import_archive(export_archive(reviewed))
    assert report_content(restored)["manifest"]["snapshot_review"]["evidence"] == "QC-12"
    revised = restored.revise("Update input")
    with pytest.raises(ValueError):
        revised.record_review(run["snapshot_hash"], "Reviewer", "QC-13", "reviewed")
    target = "FDA_ABE_2026" if project.study.rule_set_id.startswith("EMA") else "EMA_IR_NONREPLICATE_M13A"
    branch = restored.for_other_market(target, "Documented common comparator")
    assert branch.raw_base64 == restored.raw_base64
    assert branch.import_provenance["source_project_id"] == restored.project_id
    assert not branch.runs and not branch.snapshot_reviews and not branch.study.scope_reviewed


def test_workflow_current_report_and_stale(demo):
    analyzed = run_analysis(demo.freeze())
    rows, action = workflow_progress(analyzed)
    assert rows[3]["Trạng thái"] == "Có kết quả NCA"
    assert rows[5]["Trạng thái"] == "Chờ rà soát"
    assert "review" in action

    saved = analyzed.attach_artifact("Draft.pdf", b"draft only")
    rows, _ = workflow_progress(saved)
    assert "Đã lưu dự thảo" in rows[5]["Trạng thái"]

    revised = saved.revise("Changing study input requires new analysis")
    rows, _ = workflow_progress(revised)
    assert rows[4]["Trạng thái"] == "STALE"
    assert "Đã lưu" not in rows[5]["Trạng thái"]


def test_workflow_never_marks_unmatched_freeze_or_empty_review_as_ready(demo):
    analyzed = run_analysis(demo.freeze())
    invalidated = analyzed.model_copy(update={"input_fingerprint": "different"})
    rows, _ = workflow_progress(invalidated)
    assert rows[2]["Trạng thái"] == "Cần rà soát QC"
    assert rows[4]["Trạng thái"] in ("Chưa chạy", "STALE")
    assert rows[4]["Trạng thái"] == "STALE"

    empty_review_run = {**analyzed.runs[-1], "review_status": ""}
    review_missing = analyzed.model_copy(update={"runs": [empty_review_run]})
    rows, action = workflow_progress(review_missing)
    assert rows[5]["Trạng thái"] == "Chờ rà soát"
    assert "review" in action
