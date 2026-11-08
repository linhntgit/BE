"""Read-only study workflow guidance; never recomputes or approves an analysis."""

from be_app.persistence import Project
from be_app.regulations import scope_blockers
from be_app.state import pending_config, result_status


STAGE_NAMES = (
    "Xác định nghiên cứu",
    "Thiết kế và kế hoạch phân tích",
    "Nhập và kiểm tra dữ liệu",
    "Duyệt thông số PK",
    "Đánh giá BE",
    "Rà soát và xuất",
)
STAGE_PAGES = ((0,), (1, 2), (3, 4), (5,), (6, 7), (8, 9))


def workflow_progress(project: Project) -> tuple[list[dict[str, str]], str]:
    """Return six workflow stages and the most useful next action."""
    run = project.runs[-1] if project.runs else None
    current = bool(run and result_status(project, run) == "CURRENT")
    ready_scope = not scope_blockers(project.study)
    raw = bool(project.raw_base64)
    frozen = bool(
        project.freeze_hash
        and project.freeze_hash == project.input_fingerprint
        and not project.pending_edits
        and not pending_config(project)
    )
    reviewed = bool(
        current and run and run.get("review_status") not in (None, "", "Pending independent review")
    )
    review = project.review_for(run) if current else None
    exported = bool(
        current
        and run is not None
        and any(
            manifest.get("analysis_run_id") == run["analysis_run_id"]
            and manifest.get("snapshot_hash") == run["snapshot_hash"]
            and manifest.get("snapshot_review") == review
            for manifest in project.artifact_manifests.values()
        )
    )
    if review:
        reviewed = review["outcome"] == "reviewed"
    review_label = "Đã rà soát" if reviewed else ("Cần xử lý thêm" if review else "Chờ rà soát")
    result_state = result_status(project, run) if run else "Chưa chạy"
    decision = {"PASS": "Đạt", "FAIL": "Không đạt", "NOT EVALUABLE": "Không thể đánh giá"}
    stages = [
        ("Đã rà soát" if ready_scope else "Cần hoàn thiện", "Kiểm tra sản phẩm, thị trường và nguồn áp dụng."),
        ("Đã ghi protocol/SAP" if project.study.protocol and project.study.sap else "Thiếu protocol/SAP",
         "Đối chiếu giả định cỡ mẫu, phân nhóm, lịch lấy mẫu và phiên bản SAP."),
        ("Đã khóa" if frozen else ("Cần rà soát QC" if raw else "Chưa nhập"),
         "Kiểm tra dữ liệu thực tế và giải trình trước khi khóa."),
        ("Có kết quả NCA" if current else result_state, "Rà soát đường cong và từng thông số PK."),
        (decision.get(run.get("study_decision"), "Không thể đánh giá") if current else result_state,
         "Xem tiêu chí và lý do theo từng endpoint của thị trường đang xét."),
        (review_label + (" · Đã lưu dự thảo" if exported else ""),
         "Kiểm tra bằng chứng và kết luận trên cùng phiên bản kết quả."),
    ]
    rows = [{"Bước": label, "Trạng thái": status, "Hướng dẫn": detail}
            for label, (status, detail) in zip(STAGE_NAMES, stages, strict=True)]
    if not ready_scope:
        next_step = "Hoàn thiện phạm vi, protocol/SAP và bằng chứng áp dụng ở Tổng quan."
    elif not raw:
        next_step = "Nhập dữ liệu nồng độ, kèm phân nhóm nếu có, tại Nhập dữ liệu."
    elif project.pending_edits or pending_config(project):
        next_step = "Xử lý các bản nháp/chỉnh sửa chưa áp dụng trước khi Data Freeze."
    elif not frozen:
        next_step = "Kiểm tra QC, xử lý lỗi chặn và Data Freeze."
    elif not current:
        next_step = "Chạy lại NCA và BE trên snapshot đã khóa."
    elif review and not reviewed:
        next_step = "Xử lý vấn đề người rà soát đã ghi ở Rà soát và xuất."
    elif not reviewed:
        next_step = "Gửi snapshot hiện hành tới người review PK/thống kê/QA độc lập."
    elif not exported:
        next_step = "Tạo và lưu báo cáo dự thảo ở Báo cáo CTD / Xuất dữ liệu."
    else:
        next_step = "Kiểm tra dấu vết, tài liệu và giới hạn qualification trước khi sử dụng kết quả."
    return rows, next_step
