"""The only production entry point for regulated analysis decisions."""

import base64
import hashlib
import json
import sys
import uuid
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path

import pandas as pd

from be_app import __version__
from be_app.domain import BeResult, canonical, digest, utc_now
from be_app.persistence import Project, verify_project
from be_app.quick_be import compare_tmax
from be_app.regulations import RULES, rule_snapshot, scope_blockers
from be_app.snapshots import InputSnapshot, run_abe, run_nca
from be_app.statistics import aggregate_decision


def run_analysis(
    project: Project, *, qc_result=None, profile_cache: dict[str, bytes] | None = None
) -> Project:
    verify_project(project)
    if not project.freeze_hash or project.input_hash() != project.freeze_hash:
        raise ValueError("Cần Data Freeze đúng dữ liệu/phương pháp trước khi phân tích.")
    if project.pending_edits:
        raise ValueError("Có chỉnh sửa Chưa áp dụng; không phân tích từ dữ liệu cũ.")
    if qc_result is not None and qc_result.source_fingerprint != project.input_fingerprint:
        raise ValueError("QC và input snapshot không cùng fingerprint; từ chối tính toán.")
    qc = qc_result if qc_result is not None else project.qc()
    if not qc.valid:
        raise ValueError("QC có lỗi chặn; không chạy NCA/BE.")
    # Lossless JSON float round-trip: the displayed/stored input is exactly what NCA receives.
    dataset = canonical(qc.data.astype(object).where(pd.notna(qc.data), None).to_dict("records"))
    snapshot = InputSnapshot(
        project.project_id,
        project.input_revision,
        project.dataset_revision,
        project.config_revision,
        project.input_fingerprint or project.input_hash(),
        dataset,
        project.study,
        project.nca_config,
        project.be_config,
    )
    nca, computation = run_nca(snapshot, profile_cache)
    endpoints = pd.DataFrame(nca)
    # Do not use Tmax from a profile NCA marked non-evaluable, even when its
    # observed peak time was calculated. Missing values fail the Tmax test closed.
    tmax_endpoints = endpoints.copy()
    if "status" in tmax_endpoints and "tmax" in tmax_endpoints:
        tmax_endpoints.loc[tmax_endpoints["status"].ne("EVALUABLE"), "tmax"] = None
    # Supportive analysis on original-hour Tmax, outside BE pass/fail.
    tmax_comparison = asdict(compare_tmax(tmax_endpoints, project.study.design))
    blockers = scope_blockers(project.study)
    rule = RULES.get(project.study.rule_set_id)
    if project.be_config.alpha != 0.05 or project.be_config.lower != 0.8 or project.be_config.upper != 1.25:
        blockers.append("Profile phát hành chỉ cho phép alpha=0.05 và giới hạn 0.8–1.25; custom chưa hỗ trợ.")
    if rule:
        if project.study.design != "parallel" and endpoints.subject_id.nunique() < rule.minimum_crossover:
            blockers.append("Crossover dưới 12 người có dữ liệu đánh giá theo M13A.")
        if project.study.design == "parallel":
            sizes = endpoints.groupby("treatment").subject_id.nunique()
            if any(sizes.get(arm, 0) < rule.minimum_parallel_per_arm for arm in ("T", "R")):
                blockers.append("Parallel cần ít nhất 12 người đánh giá mỗi nhánh theo M13A.")
    results = []
    for endpoint in (*project.study.primary_endpoints, *project.study.secondary_endpoints):
        if not endpoints.status.eq("EVALUABLE").all():
            result = BeResult(
                endpoint=endpoint, reason="Có profile NCA không đánh giá được; không tự loại subject."
            )
        else:
            result = run_abe(snapshot, nca, endpoint)
        if result.n and project.study.design != "parallel" and result.n < 12:
            result = result.model_copy(
                update={
                    "decision": "NOT EVALUABLE",
                    "reason": "Dưới 12 subject có dữ liệu endpoint để đánh giá.",
                }
            )
        if blockers:
            result = result.model_copy(update={"decision": "NOT EVALUABLE", "reason": "; ".join(blockers)})
        result = result.model_copy(
            update={
                "diagnostics": {
                    **result.diagnostics,
                    "endpoint_role": "primary"
                    if endpoint in project.study.primary_endpoints
                    else "secondary",
                }
            }
        )
        results.append(result)
    study_blockers = [*blockers]
    if project.study.is_demo or project.study.data_purpose == "training_qa":
        study_blockers.append("Dữ liệu đào tạo/QA hoặc giả lập; không có kết luận BE cấp nghiên cứu thật.")
    elif project.study.data_purpose != "regulated_study":
        study_blockers.append("Chưa xác nhận mục đích nghiên cứu thật; không kết luận BE cấp nghiên cứu.")
    if not project.study.data_provenance.strip():
        study_blockers.append("Chưa khai báo nguồn gốc dữ liệu; không kết luận BE cấp nghiên cứu.")
    lock_path = Path(__file__).resolve().parents[1] / "uv.lock"
    dependency_lock = lock_path.read_text(encoding="utf-8") if lock_path.is_file() else ""
    run = dict(
        input_revision=snapshot.input_revision,
        dataset_revision=snapshot.dataset_revision,
        config_revision=snapshot.config_revision,
        input_fingerprint=snapshot.input_fingerprint,
        computation=computation,
        software_versions={
            "python": sys.version.split()[0],
            **{
                p: version(p)
                for p in ("numpy", "pandas", "scipy", "pydantic", "streamlit", "python-docx", "reportlab")
            },
        },
        dependency_lock=dependency_lock,
        dependency_lock_sha256=hashlib.sha256(dependency_lock.encode()).hexdigest(),
        analysis_run_id=str(uuid.uuid4()),
        timestamp=utc_now(),
        operator=project.study.operator,
        reviewer=None,
        review_status="Pending independent review",
        engine_version=__version__,
        dataset_hash=snapshot.dataset_hash,
        validated_data=json.loads(snapshot.dataset),
        raw_hash=hashlib.sha256(base64.b64decode(project.raw_base64)).hexdigest(),
        input_hash=project.input_hash(),
        config_hash=digest(
            dict(nca=project.nca_config.model_dump(mode="json"), be=project.be_config.model_dump(mode="json"))
        ),
        study=project.study.model_dump(mode="json"),
        rule_set_id=project.study.rule_set_id,
        rule_snapshot=rule_snapshot(project.study.rule_set_id) if rule else {},
        nca_config=project.nca_config.model_dump(mode="json"),
        be_config=project.be_config.model_dump(mode="json"),
        qc_flags=qc.report(),
        transformations=qc.transformations,
        nca=nca,
        tmax_comparison=tmax_comparison,
        be=[r.model_dump(mode="json") for r in results],
        blockers=study_blockers,
        study_decision=aggregate_decision(
            [r for r in results if r.endpoint in project.study.primary_endpoints],
            project.study.primary_endpoints,
            study_blockers,
        ),
        regulatory_status="DRAFT / NOT REGULATORY-READY",
    )
    run["snapshot_hash"] = digest(run)
    return project.record(
        "analysis", {"runs": [*project.runs, run]}, "Phân tích snapshot mới, không ghi đè kết quả cũ"
    )
