"""Vietnamese UI. Widgets -> durable draft/validated commit -> immutable calculation snapshot."""

import base64
import hashlib
import json
import os
from dataclasses import asdict
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pydantic import ValidationError

from be_app import __version__
from be_app.be_reporting import (
    REVIEW_TABLE_SCHEMA,
    be_tables,
    be_workbook,
)
from be_app.branding import software_attribution
from be_app.compartment_help import render_compartment_model_details
from be_app.context_help import QUICK_TASKS, RESEARCH_TASKS, integrity_terms_for, lesson_for, profile_help
from be_app.field_help import field_help_for, render_table_legend, table_column_config
from be_app.demo_scenarios import (
    ENDPOINT_CASES,
    FULL_RAW_CASES,
    STUDY_CASES,
    endpoint_frame,
    full_concentrations,
    study_values,
)
from be_app.design import randomize, sample_schedule, sample_size, secure_seed, tost_power
from be_app.domain import BeConfig, NcaConfig, Study, TerminalOverride, digest
from be_app.import_review import filtered_concentrations, review_import
from be_app.imports import REQUIRED, csv_bytes, excel_bytes, parse_file
from be_app.nca import (
    PROFILE_KEYS,
    analyze_profile,
    profile_data_hash,
    profile_identity,
    terminal_eligible_times,
)
from be_app.nca_reporting import nca_tables, nca_workbook
from be_app.persistence import Project, ProjectStore, export_archive, import_archive, restore_archive
from be_app.pk_import import PK_ALIASES, PKImportConfig, import_pk, workbook_sheets
from be_app.pk_ui import independent_pk_page
from be_app.presets import export_preset, from_project, import_preset, new_project
from be_app.protocol import PROTOCOL_FIELDS, blank_protocol_template, docx_protocol, pdf_protocol
from be_app.quick_be_ui import quick_be_page
from be_app.regulations import RULES, capability_for, planning_limits, scope_blockers
from be_app.replicate import analyze_regulatory_be
from be_app.reporting import analysis_exports, blank_report_template, docx_report, pdf_report
from be_app.review import criterion_figures, forest_figure, residual_figures, terminal_figure, workflow_table
from be_app.state import EDIT_COLUMNS, ProjectState, initialize_project_state, result_status
from be_app.table_editor import (
    combine_column_mappings,
    prepare_blq_editor,
    render_persistent_editor,
    suggest_column_mapping,
    validate_structure,
)
from be_app.widgets import Widgets, changed, creation_state, editor_changed, stage_upload
from be_app.workflow_project import validate_project_filename
from be_app.workflow_status import STAGE_NAMES, STAGE_PAGES, workflow_progress

ROOT = Path(__file__).resolve().parents[1]
PAGES = [
    "Tổng quan / Quản lý nghiên cứu",
    "Thiết kế và cỡ mẫu BE",
    "Ngẫu nhiên hóa và lịch lấy mẫu",
    "Nhập dữ liệu nồng độ",
    "Kiểm soát chất lượng (QC)",
    "Phân tích NCA",
    "Thống kê BE — EMA / FDA",
    "Đồ thị và chẩn đoán",
    "Báo cáo CTD / Xuất dữ liệu",
    "Nhật ký kiểm toán / Quản trị",
    "Phân tích PK độc lập",
    "BE nhanh — phân tích độc lập",
]
WORKFLOWS = (
    "Phân tích PK độc lập",
    "BE nhanh",
    "BE đầy đủ",
)
TEACHING_FIELDS = (
    ("teaching_school", "Tên trường", "Trường Đại học Dược Hà Nội"),
    ("teaching_faculty", "Tên Khoa", "Bào chế và Công nghệ dược phẩm"),
    ("teaching_instructor", "Tên giảng viên", "Nguyễn Trần Linh"),
    ("teaching_student", "Tên Học viên", ""),
    ("teaching_class", "Tên lớp", ""),
    ("teaching_cohort", "Khoá", ""),
)
DESIGNS = {
    "2x2": "Crossover 2×2",
    "parallel": "Song song",
    "partial3": "Partial replicate 3 kỳ",
    "full4": "Full replicate 4 kỳ",
}
PURPOSES = {
    "regulated_study": "Nghiên cứu thật (yêu cầu provenance và review)",
    "training_qa": "Đào tạo / kiểm thử QA (không kết luận cấp nghiên cứu)",
    "method_development": "Phát triển / đánh giá phương pháp",
    "unknown": "Chưa xác định / dữ liệu lịch sử",
}
DECISIONS = {
    "PASS": "Đạt tiêu chí thống kê",
    "FAIL": "Không đạt tiêu chí thống kê",
    "NOT EVALUABLE": "Không thể kết luận",
}


def capability_notice(rule_id: str, design: str) -> None:
    capability = capability_for(rule_id)
    rule = RULES[rule_id]
    with st.expander(f"Căn cứ đang áp dụng · {rule.jurisdiction}"):
        st.write(rule.guideline)
        st.caption(f"{rule.effective} · mục {rule.section} · phiên bản quy tắc {rule.version}")
        for index, url in enumerate(rule.sources, start=1):
            st.markdown(f"[Nguồn chính thức {index}]({url})")
    endpoint_vi = {
        "available": "khả dụng",
        "pending": "đang chờ",
        "unavailable": "chưa hỗ trợ",
    }.get(capability.endpoint_decision, capability.endpoint_decision)
    st.caption(
        f"{rule_id} · tính thành phần: {'có' if capability.numerical_components else 'không'} · "
        f"kết luận endpoint: {endpoint_vi} · "
        f"planning: {'có' if capability.planning else 'chưa mở'} · "
        f"thẩm định độc lập: {'đã đạt' if capability.independently_qualified else 'chưa đạt'}"
    )
    if design not in RULES[rule_id].designs:
        st.warning("Thiết kế đã chọn nằm ngoài phạm vi của profile này.")
    if capability.endpoint_decision != "available" or not capability.planning:
        st.info(capability.limitation)


def scope_record_inputs(w, existing=None):
    existing = existing or {}
    with st.expander("Phiếu căn cứ theo sản phẩm và thị trường"):
        fields = (
            ("reference_market", "Thị trường và căn cứ chọn thuốc đối chứng"),
            ("guidance", "Tên, phiên bản, tình trạng draft/final và nguồn hướng dẫn theo sản phẩm"),
            ("applicability", "Lý do áp dụng cho hàm lượng, điều kiện ăn và endpoint"),
            ("deviations", "Sai lệch, căn cứ giải trình và người phụ trách"),
        )
        return {k: v for k, label in fields if (v := w.area("scope_" + k, label, existing.get(k, "")).strip())}


def store():
    return ProjectStore(os.environ.get("BE_PROJECT_DATABASE", str(ROOT / "data" / "projects.sqlite")))


def database():
    if "project_store" not in st.session_state:
        st.session_state.project_store = store()
    return st.session_state.project_store


def controller() -> ProjectState:
    return st.session_state.active_project_state


def activate(project, revision, working_revision=0):
    state = ProjectState(project, database(), revision, working_revision)
    st.session_state.setdefault("project_states", {})[project.project_id] = state
    st.session_state.active_project_state = state
    st.session_state.project = state.project  # Compatibility alias; never a second writable source.
    st.session_state.db_revision = revision
    st.session_state["resume_be_page"] = database().last_page(project.project_id) or PAGES[0]


def open_saved_project(widget_key):
    try:
        project_id = st.session_state[widget_key]
        loaded, revision, working_revision = database().checkout(project_id)
        activate(loaded, revision, working_revision)
    except (ValueError, TypeError, OSError) as exc:
        st.session_state["callback_error"] = str(exc)


def full_project_sidebar_controls(save_slot, upload_slot):
    """Place full-BE project ZIP controls directly below workflow selection."""
    state = st.session_state.get("active_project_state") or creation_state(database())
    with save_slot:
        active = st.session_state.get("active_project_state")
        if active is None:
            st.button("Lưu project BE đầy đủ (.bewf.zip)", disabled=True,
                      help="Hãy tạo hoặc mở một nghiên cứu trước khi lưu project.",
                      key="full_project_save_unavailable", width="stretch")
        else:
            project = active.project
            st.download_button(
                "Lưu project BE đầy đủ (.bewf.zip)",
                data=lambda project=project: export_archive(project),
                file_name=f"{project.study.study_id}.bewf.zip",
                mime="application/zip", on_click="ignore",
                key="full_project_download", width="stretch",
            )
    with upload_slot:
        st.caption("Upload project BE đầy đủ (.bewf.zip)")
        upload_key = f"archive::{state.project.project_id}::{state.mount_id}"
        st.file_uploader(
            "Chọn project BE đầy đủ", type=["zip"], key=upload_key,
            on_change=stage_upload, args=(state, "archive", upload_key),
        )
        staged = state.draft("archive", "file")
        if staged:
            st.caption(f"Đã chọn: {staged['name']}")
            if st.button("Kiểm tra và mở project", key="full_project_open"):
                try:
                    validate_project_filename(staged["name"], "full_be")
                    archive_bytes = base64.b64decode(staged["base64"], validate=True)
                    import_archive(archive_bytes)
                    loaded, revision = restore_archive(database(), archive_bytes)
                except (ValueError, TypeError, OSError) as exc:
                    st.error(f"Project ZIP không hợp lệ: {exc}")
                else:
                    if loaded.import_provenance.get("restored_from_project_id"):
                        st.info("Archive trùng mã dự án được mở thành bản sao mới; bản hiện hành được giữ nguyên.")
                    activate(loaded, revision)
                    st.rerun()


def save_project(project, checkpoint=True):
    current = st.session_state.get("active_project_state")
    if current is not None and current.project.project_id == project.project_id:
        current.commit(project)
        if checkpoint:
            current.checkpoint()
        st.session_state.project = current.project
        st.session_state.db_revision = current.db_revision
    else:
        revision = database().save(project)
        activate(project, revision)
    st.rerun()  # Explicit button mutation only; never inside field callbacks.


def draft_notice():
    st.caption(
        "Bản nháp được giữ khi đổi trang và trong bản lưu dự án. Chỉ nút Áp dụng mới đổi đầu vào phân tích."
    )


def study_metadata_inputs(w: Widgets, existing: Study | None = None) -> dict[str, str]:
    """Collect source-document metadata for both new studies and audited revisions."""
    def previous(name: str) -> str:
        return getattr(existing, name) if existing is not None else ""

    with st.container(border=True):
        st.markdown("#### Điều kiện dùng thuốc và đơn vị thực hiện")
        fed_state = w.select(
            "fed_state", "Trạng thái khi dùng thuốc", ["fasted", "fed"],
            existing.fed_state if existing else "fasted",
            format_func=lambda value: "Đói (nhịn ăn)" if value == "fasted" else "No (sau ăn)",
        )
        sponsor = w.text("sponsor", "Nhà tài trợ nghiên cứu", previous("sponsor"))
        study_site = w.text("study_site", "Cơ sở / địa điểm thực hiện nghiên cứu", previous("study_site"))
        principal_investigator = w.text(
            "principal_investigator", "Nghiên cứu viên chính", previous("principal_investigator")
        )

    products: dict[str, str] = {}
    with st.container(border=True):
        st.markdown("#### Thông tin thuốc thử (T) và thuốc đối chứng (R)")
        st.caption(
            "Hàm lượng (ví dụ: 500 mg/viên) khác với nồng độ (ví dụ: 10 mg/mL). "
            "Chỉ nhập thông số phù hợp với dạng bào chế và đúng nhãn/hồ sơ lô."
        )
        for prefix, label, input_label in (
            ("test", "Thuốc thử T", "Tên thuốc thử T"),
            ("reference", "Thuốc thử R (Thuốc đối chứng)", "Tên thuốc thử R"),
        ):
            with st.container(border=True):
                st.markdown(f"**{label}**")
                products[f"{prefix}_product"] = w.text(
                    f"{prefix}_product", input_label,
                    previous(f"{prefix}_product") if existing else "",
                )
                a, b = st.columns(2)
                with a:
                    products[f"{prefix}_strength"] = w.text(
                        f"{prefix}_strength", "Hàm lượng (kèm đơn vị)", previous(f"{prefix}_strength"),
                        placeholder="Ví dụ: 500 mg/viên",
                    )
                    products[f"{prefix}_dosage_form"] = w.text(
                        f"{prefix}_dosage_form", "Dạng bào chế", previous(f"{prefix}_dosage_form"),
                        placeholder="Ví dụ: viên nén bao phim",
                    )
                    products[f"{prefix}_batch"] = w.text(
                        f"{prefix}_batch", "Số lô sản xuất", previous(f"{prefix}_batch")
                    )
                with b:
                    products[f"{prefix}_concentration"] = w.text(
                        f"{prefix}_concentration", "Nồng độ (nếu áp dụng)",
                        previous(f"{prefix}_concentration"), placeholder="Ví dụ: 10 mg/mL",
                    )
                    products[f"{prefix}_manufacturer"] = w.text(
                        f"{prefix}_manufacturer", "Nhà sản xuất", previous(f"{prefix}_manufacturer")
                    )
                    products[f"{prefix}_expiry_date"] = w.text(
                        f"{prefix}_expiry_date", "Hạn dùng (YYYY-MM-DD)",
                        previous(f"{prefix}_expiry_date"), placeholder="2027-12-31",
                    )

    dates: dict[str, str] = {}
    with st.container(border=True):
        st.markdown("#### Thời gian thực hiện nghiên cứu tương đương sinh học")
        st.caption("Nhập ngày theo dạng YYYY-MM-DD; để trống khi chưa có hồ sơ xác nhận.")
        for start, end, label_start, label_end in (
            ("study_start_date", "study_end_date", "Bắt đầu nghiên cứu", "Kết thúc nghiên cứu"),
            ("clinical_start_date", "clinical_end_date", "Bắt đầu giai đoạn lâm sàng", "Kết thúc giai đoạn lâm sàng"),
            ("bioanalytical_start_date", "bioanalytical_end_date", "Bắt đầu phân tích mẫu sinh học", "Kết thúc phân tích mẫu sinh học"),
        ):
            left, right = st.columns(2)
            with left:
                dates[start] = w.text(start, label_start, previous(start), placeholder="YYYY-MM-DD")
            with right:
                dates[end] = w.text(end, label_end, previous(end), placeholder="YYYY-MM-DD")
        dates["data_lock_date"] = w.text(
            "data_lock_date", "Ngày khóa dữ liệu (Data Lock)", previous("data_lock_date"),
            placeholder="YYYY-MM-DD",
        )
    return {"fed_state": fed_state, "sponsor": sponsor, "study_site": study_site,
            "principal_investigator": principal_investigator, **products, **dates}


def result_banner(state, run=None):
    project = state.project
    status = result_status(project, run)
    if status == "EMPTY":
        st.info("Chưa có analysis snapshot.")
        return None
    run = run if run is not None else project.runs[-1]
    if status != "CURRENT":
        st.warning(
            "Kết quả từ phiên bản dữ liệu hoặc engine trước — STALE/LEGACY. Chỉ xem tham khảo; cần áp dụng chỉnh sửa và tính lại."
        )
    else:
        st.success("✅ Kết quả hiện hành của đầu vào đã xác nhận (CURRENT).")
    fp = run.get("input_fingerprint", run["input_hash"])
    short_fp = fp[:16] + "..." if len(fp) > 16 else fp
    with st.container(border=True):
        col_meta1, col_meta2 = st.columns([2.5, 1.5])
        with col_meta1:
            st.caption(
                f"Input r{run.get('input_revision', 'legacy')} · dữ liệu r{run.get('dataset_revision', 'legacy')} · "
                f"cấu hình r{run.get('config_revision', 'legacy')} · {run['timestamp']} · {run['rule_set_id']}"
            )
        with col_meta2:
            st.caption(f"Fingerprint: `{short_fp}`")
    with st.expander("Xem bảng đầu vào thực sự dùng để phân tích"):
        st.caption(f"Mã băm đầy đủ (SHA-256): `{fp}`")
        show = Widgets(state, "snapshot_view", "preferences").check(
            "show_input", "Hiện bảng đầu vào snapshot"
        )
        if show:
            key = ("snapshot_data", run["analysis_run_id"])
            if key not in state.render_cache:
                state.render_cache[key] = pd.DataFrame(run["validated_data"])
            st.dataframe(state.render_cache[key], hide_index=True)
            st.json(
                {"NCA": run["nca_config"], "BE": run["be_config"], "rule": run["rule_snapshot"]},
                expanded=False,
            )
    return run


def overview():
    state = st.session_state.get("active_project_state") or creation_state(database())
    # A new study has its own form draft, even while a real project is open.
    create_state = creation_state(database())
    w = Widgets(create_state, "create")
    with st.expander("Khởi tạo nghiên cứu", expanded=st.session_state.get("active_project_state") is None):
        draft_notice()
        demo_case = st.selectbox(
            "Học thử · Chọn tình huống tạo nghiên cứu",
            list(STUDY_CASES), format_func=lambda key: STUDY_CASES[key].title,
            key="study_demo_case",
        )
        st.caption(STUDY_CASES[demo_case].objective + " " + STUDY_CASES[demo_case].next_step)
        if st.button("Điền dữ liệu mẫu vào biểu mẫu nghiên cứu", key="study_demo_load"):
            create_state.set_drafts("create", study_values(demo_case))
            create_state.mount_id += "_demo"
            st.rerun()
        if st.button("Làm trống biểu mẫu nghiên cứu", key="study_demo_clear"):
            create_state.clear_drafts("create")
            create_state.mount_id += "_blank"
            st.rerun()
        sid = w.text("study_id", "Mã nghiên cứu", "BE001")
        title = w.text("title", "Tên nghiên cứu", "Nghiên cứu tương đương sinh học")
        design = w.select("design", "Thiết kế nghiên cứu", list(DESIGNS), format_func=lambda x: DESIGNS[x])
        rule = w.select("rule", "Bộ quy tắc pháp lý", list(RULES))
        capability_notice(rule, design)
        protocol = w.text("protocol", "Protocol và phiên bản")
        sap = w.text("sap", "SAP và phiên bản")
        purpose = w.select("purpose", "Mục đích sử dụng dữ liệu", list(PURPOSES), format_func=lambda x: PURPOSES[x])
        provenance = w.area("provenance", "Nguồn gốc dữ liệu và bằng chứng provenance")
        ingredient = w.text("ingredient", "Hoạt chất")
        dose = w.number("dose", "Liều dùng (mg)", 100.0, min_value=0.001)
        formulation = w.select("formulation", "Dạng giải phóng", ["IR", "MR"])
        study_metadata = study_metadata_inputs(w)
        scope_record = scope_record_inputs(w)
        nti = w.check("nti", "Thuốc NTI hoặc nghi ngờ NTI")
        nti_cmax = w.check("nti_cmax", "EMA NTI: cần thu hẹp giới hạn cả Cmax theo yêu cầu sản phẩm")
        scaled = w.check("scaled", "Phương pháp scaling đã được định trước trong protocol/SAP")
        hvd_reason = w.area("hvd_reason", "Căn cứ HVD, rà soát CVwR/outlier và ý nghĩa lâm sàng")
        operator = w.text("operator", "Định danh người thao tác", "local-operator")
        evidence = w.area("evidence", "Bằng chứng rà soát guideline / PSG và phạm vi sản phẩm")
        reviewed = w.check("reviewed", "Đã rà soát phạm vi và yêu cầu riêng của sản phẩm")
        if st.button("Tạo nghiên cứu", type="primary"):
            try:
                study = Study.model_validate(dict(
                    study_id=sid,
                    title=title,
                    design=design,
                    rule_set_id=rule,
                    protocol=protocol,
                    sap=sap,
                    data_purpose=purpose,
                    data_provenance=provenance,
                    active_ingredient=ingredient,
                    dose=dose,
                    formulation=formulation,
                    **study_metadata,
                    nti=nti,
                    nti_cmax_narrow=nti_cmax,
                    scaled_be_prespecified=scaled,
                    hvd_justification=hvd_reason,
                    operator=operator,
                    scope_reviewed=reviewed,
                    scope_evidence=evidence,
                    scope_record=scope_record,
                    is_demo=bool(create_state.draft("create", "is_demo", False)),
                ))
            except ValidationError as exc:
                st.error(f"Thông tin nghiên cứu không hợp lệ: {exc.errors()[0]['msg']}")
            else:
                save_project(Project(study=study).record("create", {}, "Khởi tạo nghiên cứu"))
                create_state.clear_drafts("create")
                create_state.mount_id += "_blank"
                st.rerun()
    with st.expander("Preset phương pháp có phiên bản"):
        st.caption(
            "Preset giữ cấu hình, endpoint và mapping; dự án mới cần khai báo riêng sản phẩm, protocol/SAP và rà soát scope. Không mang dữ liệu, phân nhóm, kết quả, freeze hoặc lựa chọn terminal của dự án nguồn."
        )
        name = Widgets(state, "preset").text("name", "Tên preset", "Phương pháp BE")
        if st.button("Chuẩn bị preset phương pháp"):
            state.render_cache[("method_preset",)] = export_preset(from_project(state.project, name))
        prepared_preset = state.render_cache.get(("method_preset",))
        if isinstance(prepared_preset, bytes):
            st.download_button(
                "Tải preset phương pháp", prepared_preset, "BE_method_preset.json", on_click="ignore"
            )
        preset_key = Widgets(state, "preset").key("file")
        st.file_uploader(
            "Nhập preset phương pháp JSON",
            type=["json"],
            key=preset_key,
            on_change=stage_upload,
            args=(state, "preset", preset_key),
        )
        staged_preset = state.draft("preset", "file")
        if staged_preset:
            preset = import_preset(base64.b64decode(staged_preset["base64"]))
            st.json(preset.model_dump(mode="json"), expanded=False)
            if st.button("Tạo dự án mới từ preset"):
                save_project(new_project(preset, sid, title, operator))
    entries = database().list_projects()
    if entries:
        ids = [x["project_id"] for x in entries]
        open_widgets = Widgets(state, "open")
        open_widgets.select(
            "project",
            "Nghiên cứu đã lưu",
            ids,
            format_func=lambda pid: next(
                f"{x['study_id']} · {x['project_id'][:8]}" for x in entries if x["project_id"] == pid
            ),
        )
        st.button("Mở nghiên cứu đã lưu", on_click=open_saved_project, args=(open_widgets.key("project"),))
    if st.session_state.get("active_project_state") is None:
        st.caption(f"Mã bản nháp khởi tạo để mở lại sau reload: {state.project.project_id}")
        return
    project = controller().project
    st.subheader(project.study.title)
    st.caption(f"Mục đích dữ liệu: {PURPOSES[project.study.data_purpose]} · provenance: {project.study.data_provenance or 'chưa khai báo'}")
    st.write(
        f"Input r{project.input_revision} · dataset r{project.dataset_revision} · config r{project.config_revision}"
    )
    for error in scope_blockers(project.study):
        st.warning(error)
    progress, next_step = workflow_progress(project)
    st.subheader("Tiến độ quy trình nghiên cứu")
    st.dataframe(
        progress,
        hide_index=True,
        alt="Trạng thái và hướng dẫn cho sáu chặng BE đầy đủ",
    )
    st.info(f"Bước tiếp theo: {next_step}")
    with st.expander("Đánh giá cùng nghiên cứu ở thị trường thứ hai"):
        region = RULES[project.study.rule_set_id].jurisdiction
        other = [r.rule_set_id for r in RULES.values() if r.jurisdiction != region
                 and project.study.design in r.designs and project.study.nti == r.rule_set_id.endswith("_NTI")]
        if other:
            target = st.selectbox("Quy tắc cho thị trường thứ hai", other)
            rationale = st.text_area("Căn cứ dùng chung đối chứng, điều kiện nghiên cứu và dữ liệu",
                                     key=f"market_reason_{project.project_id}")
            st.caption("Mở dự án liên kết với dữ liệu nguồn. Rà soát lại phạm vi, SAP và khóa dữ liệu cho thị trường đã chọn.")
            if st.button("Tạo dự án cho thị trường thứ hai"):
                save_project(project.for_other_market(target, rationale))
    if project.import_provenance.get("source_project_id"):
        st.caption(f"Dự án nguồn: {project.import_provenance['source_project_id']} · "
                   f"{project.import_provenance.get('shared_data_rationale', '')}")
    with st.expander(
        "Tạo revision để cập nhật phương pháp / phạm vi",
        expanded=st.session_state.pop("expand_scope_revision", False),
    ):
        w = Widgets(controller(), "revision")
        draft_notice()
        reason = w.text("reason", "Lý do tạo revision")
        protocol = w.text("protocol", "Protocol mới", project.study.protocol)
        sap = w.text("sap", "SAP mới", project.study.sap)
        purpose = w.select("purpose", "Mục đích dữ liệu revision", list(PURPOSES), project.study.data_purpose, format_func=lambda x: PURPOSES[x])
        provenance = w.area("provenance", "Nguồn gốc dữ liệu revision", project.study.data_provenance)
        rule = w.select("rule", "Profile của revision", list(RULES), project.study.rule_set_id)
        design = w.select(
            "design",
            "Thiết kế của revision",
            list(DESIGNS),
            project.study.design,
            format_func=lambda x: DESIGNS[x],
        )
        capability_notice(rule, design)
        scope = w.area("scope", "Bằng chứng phạm vi cập nhật", project.study.scope_evidence)
        scope_record = scope_record_inputs(w, project.study.scope_record)
        reviewed = w.check("reviewed", "Đã rà soát phạm vi revision", project.study.scope_reviewed)
        nti = w.check("nti", "Revision thuộc NTI", project.study.nti)
        nti_cmax = w.check("nti_cmax", "EMA NTI: thu hẹp giới hạn Cmax", project.study.nti_cmax_narrow)
        scaled = w.check(
            "scaled", "Scaling đã định trước trong protocol/SAP", project.study.scaled_be_prespecified
        )
        hvd_reason = w.area("hvd_reason", "Căn cứ HVD và độ tin cậy CVwR", project.study.hvd_justification)
        study_metadata = study_metadata_inputs(w, project.study)
        replace = w.check("replace", "Cho phép nhập raw mới trong revision này")
        if st.button("Tạo revision mới"):
            try:
                study = Study.model_validate({
                    **project.study.model_dump(),
                    "design": design,
                    "protocol": protocol,
                    "sap": sap,
                    "data_purpose": purpose,
                    "data_provenance": provenance,
                    "rule_set_id": rule,
                    "scope_evidence": scope,
                    "scope_record": scope_record,
                    "scope_reviewed": reviewed,
                    "nti": nti,
                    "nti_cmax_narrow": nti_cmax,
                    "scaled_be_prespecified": scaled,
                    "hvd_justification": hvd_reason,
                    **study_metadata,
                })
            except ValidationError as exc:
                st.error(f"Thông tin revision không hợp lệ: {exc.errors()[0]['msg']}")
            else:
                save_project(project.revise(reason, study=study, replace_raw=replace))


@st.cache_data(max_entries=32, show_spinner=False)
def power_plan(inputs_json: str, context_json: str, engine_version: str):
    inputs = json.loads(inputs_json)
    context = json.loads(context_json)
    if not capability_for(context["rule_set_id"]).planning:
        raise ValueError("Profile chưa được phép lập kế hoạch cỡ mẫu.")
    design = context["design"]
    results = [
        dict(
            endpoint=ep,
            lower=lower,
            upper=upper,
            alpha=context["alpha"],
            **asdict(
                sample_size(
                    inputs[cv] / 100,
                    inputs[gmr],
                    inputs["target"] / 100,
                    design,
                    inputs["dropout"] / 100,
                    alpha=context["alpha"],
                    lower=lower,
                    upper=upper,
                )
            ),
        )
        for ep, cv, gmr, (lower, upper) in (
            ("AUC", "cv_auc", "gmr_auc", context["bounds"]["AUC"]),
            ("Cmax", "cv_cmax", "gmr_cmax", context["bounds"]["Cmax"]),
        )
    ]
    controlling = max(results, key=lambda result: result["evaluable"])
    chosen = controlling["evaluable"]
    cv_key, gmr_key = ("cv_auc", "gmr_auc") if controlling["endpoint"] == "AUC" else ("cv_cmax", "gmr_cmax")
    curve = [
        dict(
            n=n,
            Power=tost_power(
                inputs[cv_key] / 100,
                inputs[gmr_key],
                n // 2,
                n // 2,
                design,
                context["alpha"],
                controlling["lower"],
                controlling["upper"],
            ),
        )
        for n in range(max(4, chosen - 12), chosen + 14, 2)
    ]
    return dict(
        results=results,
        curve=curve,
        curve_endpoint=controlling["endpoint"],
        evaluable=chosen,
        recruit=controlling["recruit"],
        inputs=inputs,
        context=context,
        fingerprint=planning_fingerprint(inputs, context, engine_version),
    )


def planning_context(study: Study, be_config: BeConfig) -> dict:
    rule = RULES[study.rule_set_id]
    return dict(
        rule_set_id=rule.rule_set_id,
        rule_version=rule.version,
        design=study.design,
        endpoint_roles={"primary": list(study.primary_endpoints), "secondary": list(study.secondary_endpoints)},
        bounds=planning_limits(study),
        alpha=be_config.alpha,
        nti_cmax_narrow=study.nti_cmax_narrow,
        method="exact_joint_TOST_v1",
    )


def planning_fingerprint(inputs: dict, context: dict, engine_version: str) -> str:
    return digest(dict(inputs=inputs, context=context, engine_version=engine_version))


def design_page(state):
    project = state.project
    st.write(f"Thiết kế: {DESIGNS[project.study.design]}")
    protocol_export_panel(state)
    capability_notice(project.study.rule_set_id, project.study.design)
    capability = capability_for(project.study.rule_set_id)
    context = planning_context(project.study, project.be_config)
    if not capability.planning:
        st.warning("Chưa có cỡ mẫu đủ điều kiện sử dụng cho profile này. Không dùng kết quả planning cũ.")
        return
    if project.study.design not in ("2x2", "parallel"):
        st.warning(
            "Chưa hỗ trợ tính cỡ mẫu cho thiết kế replicate hoặc phương pháp mở rộng giới hạn ABEL/RSABE: "
            "lực thống kê phụ thuộc vào giả định độ lệch chuẩn nội cá thể của thuốc đối chứng ($s_{WR}$ / $CV_{wR}$) "
            "và nhánh chuyển ngưỡng co giãn (US FDA $s_{WR} \\ge 0{,}294$ hoặc EMA $CV_{wR} > 30\\%$), cần mô phỏng Monte Carlo theo SAP."
        )
        return
    if project.study.design not in RULES[project.study.rule_set_id].designs or project.be_config.alpha != 0.05:
        st.warning("Thiết kế hoặc alpha ngoài phạm vi công cụ planning; không hiển thị cỡ mẫu.")
        return
    st.info("2×2 dùng CVw; parallel dùng CV tổng giữa người. Các giả định được tự lưu; chỉ tính khi bấm nút.")
    st.caption(f"Giới hạn AUC: {context['bounds']['AUC']}; Cmax: {context['bounds']['Cmax']}; alpha={context['alpha']}.")
    w = Widgets(state, "planning", "planning")
    w.number("cv_auc", "CV AUC (%)", 20.0, min_value=0.1, max_value=200.0)
    w.number("cv_cmax", "CV Cmax (%)", 30.0, min_value=0.1, max_value=200.0)
    w.number("gmr_auc", "GMR dự kiến AUC (T/R)", 0.95, min_value=0.801, max_value=1.249)
    w.number("gmr_cmax", "GMR dự kiến Cmax (T/R)", 0.95, min_value=0.801, max_value=1.249)
    w.number("target", "Power mục tiêu (%)", 80, min_value=70, max_value=99, step=1)
    w.number("dropout", "Dropout dự kiến (%)", 10, min_value=0, max_value=80, step=1)
    w.text("source", "Nguồn CV và giả định thiết kế")
    if st.button("Tính cỡ mẫu và power"):
        inputs = state.planning()
        if not inputs["source"].strip():
            raise ValueError("Cần ghi nguồn CV và giả định trước khi tính.")
        try:
            plan = power_plan(json.dumps(inputs, sort_keys=True), json.dumps(context, sort_keys=True), __version__)
        except (ValueError, ArithmeticError) as exc:
            st.error(f"Không thể lập kế hoạch: {exc}")
            return
        save_project(
            state.project.record(
                "sample_size_plan",
                {"allocation_metadata": {**state.project.allocation_metadata, "sample_size_plan": plan}},
                "Tính theo giả định đã xác nhận",
            )
        )
    plan = project.allocation_metadata.get("sample_size_plan")
    if plan:
        expected = planning_fingerprint(state.planning(), context, __version__)
        if plan.get("fingerprint") != expected:
            st.warning(
                "STALE: profile, biên, endpoint, alpha hoặc giả định đã thay đổi. Cần tính lại trước khi xem N/power."
            )
            return
        st.success(f"N đánh giá: {plan['evaluable']} · N tuyển: {plan['recruit']} · Endpoint chi phối: {plan['curve_endpoint']}")
        st.caption("Power tính riêng cho từng endpoint, chưa phải xác suất đồng thời tất cả endpoint đạt BE.")
        plan_rows = plan.get("results", [])
        plan_cols = list(plan_rows[0].keys()) if plan_rows else []
        st.dataframe(pd.DataFrame(plan_rows), hide_index=True, column_config=table_column_config(plan_cols))
        render_table_legend(plan_cols, title="ℹ️ Chú thích chỉ tiêu bảng tính cỡ mẫu")
        if "curve" in plan:
            st.plotly_chart(px.line(pd.DataFrame(plan["curve"]), x="n", y="Power", markers=True))


def randomization_page(state):
    project = state.project
    w = Widgets(state, "randomization")
    draft_notice()
    n = w.number("n", "Số người tuyển", 24, min_value=2, max_value=10000, step=2)
    seed = w.text("seed", "Seed lưu trong hồ sơ", "241029")
    block = w.number(
        "block",
        "Kích thước block",
        6 if project.study.design == "partial3" else 4,
        min_value=2,
        max_value=100,
    )
    if st.button("Tạo danh sách phân nhóm", disabled=bool(project.freeze_hash or project.raw_base64)):
        frame, metadata = randomize(project.study.design, int(n), int(seed), int(block))
        save_project(project.with_allocation(frame.to_dict("records"), metadata))
    if st.button("Sinh seed ngẫu nhiên bảo mật"):
        state.set_draft("randomization", "seed", str(secure_seed()))
        # New mount intentionally reconstructs widgets from the confirmed draft.
        state.mount_id += "s"
        st.rerun()
    times = w.text("times", "Lịch lấy mẫu dự kiến (giờ, phân cách dấu phẩy)", "0,0.5,1,2,3,4,6,8,12,24,36")
    if project.allocation:
        alloc_cols = list(project.allocation[0].keys()) if project.allocation else []
        st.dataframe(pd.DataFrame(project.allocation), hide_index=True, column_config=table_column_config(alloc_cols))
        render_table_legend(alloc_cols, title="ℹ️ Chú thích cột bảng phân nhóm ngẫu nhiên")
        if st.button("Chuẩn bị Excel phân nhóm và lịch lấy mẫu"):
            frame = pd.DataFrame(project.allocation)
            schedule = sample_schedule(
                frame.drop(columns=["sequence", "randomization_id", "screening_id"]),
                [float(x.strip()) for x in times.split(",")],
            )
            state.render_cache["schedules"] = (
                excel_bytes(frame),
                excel_bytes(schedule),
                project.dataset_revision,
                times,
            )
        files = state.render_cache.get("schedules")
        if files and files[2:] == (project.dataset_revision, times):
            st.download_button("Tải phân nhóm Excel", files[0], "randomization.xlsx", on_click="ignore")
            st.download_button(
                "Tải lịch lấy mẫu Excel", files[1], "sampling_schedule.xlsx", on_click="ignore"
            )
    st.caption("Actual time để trống; phân nhóm hạn chế truy cập. Bản local chưa có blinding/RBAC.")


def concentration_table(frame: pd.DataFrame, *, key: str, title: str):
    """Read-only complete table with optional filters and a faithful CSV export."""
    st.subheader(title)
    if frame.empty:
        st.info("Bảng chưa có dòng dữ liệu.")
        return
    count = frame.subject_id.astype(str).nunique() if "subject_id" in frame else 0
    st.caption(f"Toàn bộ dữ liệu: {len(frame):,} dòng · {count:,} người tình nguyện. Bảng có thể cuộn để xem hết.")
    subjects = sorted(frame.subject_id.astype(str).unique()) if "subject_id" in frame else []
    periods = sorted(frame.period.astype(str).unique()) if "period" in frame else []
    left, right = st.columns(2)
    with left:
        picked_subjects = st.multiselect(
            "Lọc theo người tình nguyện (để trống = tất cả)", subjects, key=f"{key}::subjects"
        )
    with right:
        picked_periods = st.multiselect(
            "Lọc theo kỳ (để trống = tất cả)", periods, key=f"{key}::periods"
        )
    visible = filtered_concentrations(frame, picked_subjects, picked_periods)
    visible_subjects = visible.subject_id.astype(str).nunique() if "subject_id" in visible else 0
    st.caption(f"Đang hiển thị {len(visible):,}/{len(frame):,} dòng · {visible_subjects:,}/{count:,} người tình nguyện.")
    st.dataframe(visible, hide_index=True, height=420, width="stretch", column_config=table_column_config(visible.columns), alt=title)
    render_table_legend(visible.columns, title="ℹ️ Chú thích các cột dữ liệu nồng độ")
    st.download_button(
        "Tải CSV dữ liệu đang hiển thị",
        csv_bytes(visible),
        f"{key.replace(':', '_')}_filtered.csv",
        mime="text/csv",
        on_click="ignore",
    )


def import_page(state):
    project = state.project
    st.subheader("1. Chuẩn bị file nồng độ")
    st.caption(
        "Dùng định dạng long: mỗi dòng là một mẫu nồng độ. CSV mã UTF-8 hoặc Excel XLSX, "
        "tối đa 25 MB; tên cột đúng theo mẫu. File được kiểm tra trước khi lưu raw."
    )
    st.download_button(
        "Tải mẫu CSV (16 cột bắt buộc)",
        csv_bytes(pd.DataFrame(columns=REQUIRED)),
        "concentration_template.csv",
        on_click="ignore",
    )
    with st.expander("Xem tên cột bắt buộc và quy tắc dữ liệu"):
        st.code(", ".join(REQUIRED), language=None)
        st.caption(
            "subject_id, sample_id giữ nguyên định danh (kể cả số 0 đầu); "
            "thời điểm dose/sample có múi giờ; period là số nguyên dương; "
            "blq_flag = true/false hoặc 1/0; concentration và lloq dùng concentration_unit. "
            "Cột sample_status có thể thêm nếu cần."
        )
    case = st.selectbox("Học thử · Tình huống nồng độ", list(FULL_RAW_CASES),
                        format_func=lambda value: FULL_RAW_CASES[value].title,
                        key=f"raw_demo_case::{project.project_id}")
    st.caption(FULL_RAW_CASES[case].objective + " " + FULL_RAW_CASES[case].next_step)
    available = bool(project.study.is_demo and project.allocation)
    if not project.study.is_demo:
        st.caption("Tạo nghiên cứu học thử trước để tránh đưa dữ liệu tổng hợp vào dự án thật.")
    elif not project.allocation:
        st.caption("Hãy lập và lưu phân nhóm tại trang Ngẫu nhiên hóa trước.")
    if st.button("Điền dữ liệu mẫu vào bảng nồng độ", disabled=not available,
                 key=f"raw_demo_load::{project.project_id}"):
        frame = full_concentrations(project.study, project.allocation, case)
        content = csv_bytes(frame)
        state.set_draft("import", "file", dict(
            name=f"synthetic_{case}.csv",
            base64=base64.b64encode(content).decode("ascii"),
            sha256=hashlib.sha256(content).hexdigest(),
        ))
        state.render_cache.pop("import_review", None)
        state.mount_id += "_demo"
        st.rerun()
    key = f"upload::{project.project_id}::{state.mount_id}"
    st.file_uploader(
        "Chọn file CSV hoặc XLSX để kiểm tra",
        type=["csv", "xlsx"],
        key=key,
        on_change=stage_upload,
        args=(state, "import", key),
    )
    if st.button("Tạo bảng trống để nhập thủ công", key=f"import_manual::{project.project_id}"):
        blank = {col: "" for col in REQUIRED}
        blank.update(study_id=project.study.study_id, analyte=project.study.analyte,
                     concentration_unit="ng/mL", blq_flag="false", source_batch="manual")
        content = pd.DataFrame([blank]).to_csv(index=False).encode("utf-8-sig")
        state.set_draft("import", "file", dict(
            name="manual_concentrations.csv",
            base64=base64.b64encode(content).decode("ascii"),
            sha256=hashlib.sha256(content).hexdigest(),
        ))
        st.rerun()
    w = Widgets(state, "import")
    staged = state.draft("import", "file")
    effective_content = base64.b64decode(staged["base64"]) if staged else b""
    effective_name = staged["name"] if staged else ""
    source_columns: list[str] = []
    automatic: dict[str, str] = {}
    if staged:
        try:
            imported = parse_file(effective_content, effective_name)
            source_columns = list(imported.columns)
            automatic = suggest_column_mapping(source_columns, [*REQUIRED, "sample_status"])
            if not imported.empty:
                st.markdown("**Bảng dữ liệu trước khi lưu raw**")
                st.caption("Sửa ô, dán nhiều ô và thêm/xóa dòng, sau đó bấm Áp dụng. "
                           "Bảng đã áp dụng sẽ được kiểm tra QC và lưu thành raw mới.")
                working = render_persistent_editor(
                    f"import::{project.project_id}", imported,
                    staged.get("sha256", hashlib.sha256(effective_content).hexdigest()),
                    validator=lambda frame: validate_structure(frame).fillna("").astype(str),
                    width="stretch",
                )
                if not working.equals(imported):
                    effective_content = working.to_csv(index=False).encode("utf-8-sig")
                    effective_name = "edited_concentrations.csv"
        except (ValueError, TypeError, OSError, KeyError, ImportError,
                pd.errors.ParserError) as exc:
            st.error(f"Không thể mở bảng chỉnh sửa: {exc}")
    with st.expander("Mapping cột (chỉ dùng khi tên cột khác mẫu)"):
        mapping = w.area(
            "mapping",
            "Mapping JSON: tên cột trong file → tên cột mẫu",
            json.dumps(project.column_mapping, ensure_ascii=False),
            help='Ví dụ: {"SUBJ": "subject_id", "CONC": "concentration"}. Để {} nếu file đã đúng mẫu.',
        )
        manual_mapping: dict[str, str | None] = {}
        if source_columns:
            st.caption("Tên cột trùng sau khi bỏ khoảng trắng và phân biệt hoa/thường "
                       "sẽ được tự nhận. Chọn cột đích cho tên khác; mỗi đích chỉ dùng một lần.")
            choices = ["(tự động)", "(giữ tên gốc)", *REQUIRED, "sample_status"]
            for offset in range(0, len(source_columns), 3):
                for col, source_name in zip(st.columns(3), source_columns[offset:offset + 3], strict=False):
                    with col:
                        selected = st.selectbox(
                            f"{source_name} → {automatic.get(source_name, source_name)}",
                            choices, key=f"import_map::{project.project_id}::"
                                         f"{staged.get('sha256') if staged else 'none'}::{offset}::{source_name}",
                        )
                    if selected != "(tự động)":
                        manual_mapping[source_name] = None if selected == "(giữ tên gốc)" else selected
        else:
            manual_mapping = {}
    try:
        existing_mapping = json.loads(mapping)
        if not isinstance(existing_mapping, dict):
            raise ValueError("Mapping JSON phải là object.")
        selected_mapping = combine_column_mappings(automatic, existing_mapping, manual_mapping)
        effective_mapping = json.dumps(selected_mapping, ensure_ascii=False)
    except (ValueError, TypeError):
        # Let the existing preflight show the precise invalid-JSON error.
        effective_mapping = mapping
    convert = w.check("convert", "Xác nhận chuyển đơn vị sang ng/mL và lưu dấu vết")
    review = None
    if staged:
        st.subheader("2. Kiểm tra file trước khi nhập")
        st.caption(f"Đang chờ kiểm tra: {staged['name']}")
        review_key = (
            hashlib.sha256(effective_content).hexdigest(), effective_name, mapping,
            effective_mapping, convert,
            digest(project.study.model_dump(mode="json")), digest(project.allocation),
        )
        if st.button("Kiểm tra cấu trúc và QC", type="primary", width="stretch"):
            review = review_import(
                effective_content, effective_name, effective_mapping,
                project.study, project.allocation, convert,
            )
            state.render_cache["import_review"] = (review_key, review)
        cached = state.render_cache.get("import_review")
        if cached and cached[0] == review_key:
            review = cached[1]
        if review is not None:
            if review.error:
                st.error(review.error)
            elif review.frame is not None and review.qc is not None:
                frame = review.frame
                n_subjects = frame.subject_id.astype(str).nunique() if "subject_id" in frame else 0
                a, b, c = st.columns(3)
                a.metric("Dòng dữ liệu", f"{len(frame):,}")
                b.metric("Người tình nguyện", f"{n_subjects:,}")
                c.metric("Cột bắt buộc hợp lệ", f"{len(set(frame.columns) & set(REQUIRED))}/{len(REQUIRED)}")
                if review.missing:
                    st.error("Thiếu cột bắt buộc: " + ", ".join(review.missing))
                else:
                    st.success("Đã nhận đủ 16 cột bắt buộc.")
                if review.extra:
                    st.info("Cột bổ sung (được giữ trong raw): " + ", ".join(review.extra))
                errors = sum(flag.severity == "ERROR" for flag in review.qc.flags)
                warnings = sum(flag.severity == "WARNING" for flag in review.qc.flags)
                if errors:
                    st.error(f"Có {errors} lỗi cần sửa trong file trước khi nhập; {warnings} cảnh báo.")
                elif warnings:
                    st.warning(f"Không có lỗi chặn; có {warnings} cảnh báo cần đọc và cân nhắc.")
                else:
                    st.success("Kiểm tra đạt: không có lỗi chặn hoặc cảnh báo.")
                if review.qc.flags:
                    st.dataframe(
                        pd.DataFrame(review.qc.report()), hide_index=True, height=260,
                        alt="Chi tiết các lỗi và cảnh báo QC theo dòng, cột",
                    )
                    st.caption("Dòng trong bảng lỗi tính từ dòng 2 của file (sau hàng tiêu đề).")
                concentration_table(
                    frame, key=f"preflight::{project.project_id}::{staged.get('sha256', '')}",
                    title="Xem toàn bộ dữ liệu file đã chọn",
                )
        st.subheader("3. Xác nhận nhập dữ liệu")
        if not project.allocation:
            st.warning("Hãy tạo phân nhóm ở bước 'Ngẫu nhiên hóa và lịch lấy mẫu' trước khi nhập dữ liệu.")
        if project.raw_base64 or project.freeze_hash:
            st.info("Dự án đã lưu raw hoặc đã khóa. Dùng quy trình revision nếu cần thay dữ liệu.")
        if review is None:
            st.info("Bấm 'Kiểm tra cấu trúc và QC' để mở khóa nút nhập. Đổi file, mapping hoặc đơn vị sẽ cần kiểm tra lại.")
        if st.button(
            "Nhập và lưu raw bất biến",
            disabled=bool(project.raw_base64 or project.freeze_hash or not project.allocation or not review or not review.ready),
            width="stretch",
        ):
            updated = project.import_raw(
                effective_content, effective_name,
                review.mapping if review is not None else {}, convert,
            )
            save_project(updated)
    if project.raw_base64:
        st.success("Đã lưu dữ liệu gốc; không import lại khi đổi trang.")
        st.json(project.import_provenance, expanded=False)
        concentration_table(
            state.clean_frame(), key=f"saved::{project.project_id}::{project.dataset_revision}",
            title="Toàn bộ dữ liệu đã lưu (sau correction nếu có)",
        )


def _qc_replacement_source(project, current: pd.DataFrame) -> tuple[pd.DataFrame, str] | None:
    """Prepare a full-table QC replacement from CSV/XLSX with explicit header mapping."""
    upload = st.file_uploader(
        "Hoặc tải bảng thay thế (CSV / XLSX)", type=["csv", "xlsx"],
        key=f"qc_replacement_file::{project.project_id}",
    )
    if upload is None:
        return current.astype(str), f"{project.dataset_revision}:{project.input_fingerprint}"
    content = upload.getvalue()
    try:
        sheets = workbook_sheets(content, upload.name)
        sheet = st.selectbox(
            "Trang tính bảng thay thế", sheets,
            key=f"qc_replacement_sheet::{project.project_id}",
        ) if len(sheets) > 1 else sheets[0]
        imported = parse_file(content, upload.name, sheet_name=sheet)
        auto = suggest_column_mapping(imported.columns, [*REQUIRED, "sample_status"])
    except (ValueError, OSError, KeyError, ImportError, pd.errors.ParserError) as exc:
        st.error(f"Không thể mở bảng thay thế: {exc}")
        return None
    st.caption("Đối chiếu cột nguồn với schema QC. Chọn cột đích nếu tên khác; "
               "giữ '(tự động)' để dùng khớp tên không phân biệt hoa/thường.")
    mapping = dict(auto)
    choices = ["(tự động)", "(giữ tên gốc)", *REQUIRED, "sample_status"]
    for offset in range(0, len(imported.columns), 3):
        for column, source_name in zip(st.columns(3), imported.columns[offset:offset + 3], strict=False):
            with column:
                choice = st.selectbox(
                    f"{source_name} → {auto.get(source_name, source_name)}", choices,
                    key=f"qc_replacement_map::{project.project_id}::"
                        f"{hashlib.sha256(content).hexdigest()[:16]}::{source_name}",
                )
            if choice == "(giữ tên gốc)":
                mapping.pop(source_name, None)
            elif choice != "(tự động)":
                mapping[source_name] = choice
    prepared = imported.rename(columns=mapping)
    if prepared.columns.duplicated().any():
        st.error("Hai cột nguồn đang cùng ánh xạ tới một cột đích. Hãy sửa mapping.")
        return None
    source_id = hashlib.sha256(
        content + str(sheet).encode("utf-8") +
        json.dumps(mapping, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    return prepared, source_id


def qc_freeze_panel(state, qc_result) -> None:
    """Show the actionable route to a valid, traceable analysis snapshot."""
    project = state.project
    with st.container(border=True):
        st.subheader("Khóa dữ liệu để chạy NCA/BE")
        if project.freeze_hash:
            st.success("Đã Data Freeze và khóa SAP cho phiên bản hiện tại.")
            if scope_blockers(project.study):
                st.warning(
                    "Dữ liệu đã khóa nhưng căn cứ phạm vi FDA/EMA vẫn chưa hoàn tất. "
                    "Cần tạo revision và bổ sung rà soát trước khi phân tích."
                )
                st.button(
                    "Đến Tổng quan rà soát phạm vi →", key="qc_frozen_scope_review",
                    on_click=go_to_scope_revision,
                )
            st.button(
                "Đến Phân tích NCA →", key="qc_go_to_nca",
                on_click=go_to_learning_step, args=(PAGES[5],),
            )
            return

        st.markdown(
            "1. Bấm **Kiểm tra / cập nhật QC** và xem lỗi/cảnh báo bên dưới.\n"
            "2. Nếu có lỗi, chọn **Đối tượng/Kỳ** bên dưới để sửa, ghi lý do, "
            "người rà soát và bằng chứng, rồi bấm **Áp dụng các sửa đổi** "
            "(hoặc hủy bản nháp). Chạy QC lại.\n"
            "3. Khi QC hợp lệ, không còn bản nháp và SAP đã chốt, "
            "bấm **Data Freeze và khóa SAP** ngay tại đây."
        )
        blockers = []
        if project.pending_edits:
            blockers.append(
                f"Còn {len(project.pending_edits)} mẫu sửa chưa áp dụng: "
                "áp dụng có giải trình hoặc hủy bản nháp ở phần chỉnh sửa bên dưới."
            )
        if state.pending_config():
            blockers.append("Còn bản nháp NCA/SAP chưa lưu hoặc chọn pha cuối chưa áp dụng.")
            st.button(
                "Đến Phân tích NCA để lưu cấu hình trước khóa →",
                key="qc_go_to_nca_config", on_click=go_to_learning_step, args=(PAGES[5],),
            )
        scope_issues = scope_blockers(project.study)
        if scope_issues:
            blockers.extend(scope_issues)
            st.button(
                "Đến Tổng quan rà soát FDA/EMA trước khi khóa →",
                key="qc_go_to_scope_review", on_click=go_to_scope_revision,
            )
        try:
            project.check_freeze_evidence()
        except ValueError as exc:
            blockers.append(str(exc))
            st.button(
                "Đến Tổng quan bổ sung căn cứ nghiên cứu →",
                key="qc_go_to_overview", on_click=go_to_learning_step, args=(PAGES[0],),
            )

        if qc_result is None:
            st.info("Chưa chạy QC trong phiên làm việc này. Nút Data Freeze cũng sẽ tự kiểm tra QC trước khi khóa.")
        elif qc_result.valid:
            warnings = sum(flag.severity == "WARNING" for flag in qc_result.flags)
            st.success(f"QC đạt: không có lỗi chặn; {warnings} cảnh báo cần xem xét.")
        else:
            errors = sum(flag.severity == "ERROR" for flag in qc_result.flags)
            blockers.append(f"QC còn {errors} lỗi chặn. Xem bảng lỗi và sửa dữ liệu bên dưới.")
        for message in blockers:
            st.warning(message)

        if st.button(
            "Data Freeze và khóa SAP", key="qc_data_freeze", type="primary",
            disabled=bool(blockers),
        ):
            checked = state.qc()
            if not checked.valid:
                st.error("QC còn lỗi chặn. Xem bảng QC bên dưới, sửa dữ liệu rồi kiểm tra lại.")
                if checked.flags:
                    st.dataframe(pd.DataFrame(checked.report()), hide_index=True)
            else:
                state.freeze()
                state.checkpoint()
                st.rerun()


def qc_page(state):
    project = state.project
    learning_mode = bool(st.session_state.get("full_be_learning_mode")) and (
        st.session_state.get("workflow") == "BE đầy đủ"
    )
    if learning_mode and not project.freeze_hash:
        st.info(
            "Trong chế độ học tập, bạn có thể sang bước Phân tích NCA khi QC chưa đạt "
            "hoặc chưa Data Freeze. Chưa thể chạy tính toán NCA/BE cho đến khi dữ liệu hợp lệ."
        )
        st.button(
            "Bỏ qua QC để sang bước Phân tích NCA →",
            key="learning_skip_qc",
            on_click=go_to_learning_step,
            args=(PAGES[5],),
        )
    if not project.raw_base64:
        st.info("Chưa có dữ liệu raw nên chưa thể kiểm tra QC hoặc Data Freeze.")
        st.button(
            "Đến Nhập dữ liệu nồng độ →", key="qc_go_to_import",
            on_click=go_to_learning_step, args=(PAGES[3],),
        )
        return
    if project.freeze_hash:
        st.info("Dữ liệu đã khóa. Tạo revision có chủ đích trước khi sửa mẫu.")
        if st.button("Tạo revision để sửa dữ liệu"):
            save_project(project.revise("Yêu cầu correction sau phân tích"))
    run_qc = st.button("Kiểm tra / cập nhật QC")
    qc = state.qc() if run_qc or state._qc is not None else None
    qc_freeze_panel(state, qc)
    if qc is not None:
        st.success("Hợp lệ: không có lỗi chặn.") if qc.valid else st.error(
            "Có lỗi chặn; chưa được phân tích."
        )
        if qc.flags:
            st.dataframe(pd.DataFrame(qc.report()), hide_index=True)
            flagged = sorted({flag.row - 2 for flag in qc.flags
                              if flag.row is not None and 2 <= flag.row <= len(qc.data) + 1})
            if flagged:
                with st.expander("Xem các mẫu cần xử lý"):
                    columns = ["sample_id", "subject_id", "period", "treatment", "actual_time_h", "concentration"]
                    st.dataframe(qc.data.iloc[flagged].reindex(columns=columns), hide_index=True)
    else:
        st.info("QC chưa chạy cho phiên bản này; bấm Kiểm tra QC. Chỉnh sửa ô không tự chạy lại toàn bộ QC.")
    frame = state.clean_frame()
    subjects = sorted(frame.subject_id.unique())
    w = Widgets(state, "editor", "preferences")
    subject = w.select("subject", "Đối tượng cần sửa", subjects)
    if subject not in subjects:
        return
    periods = sorted(frame.loc[frame.subject_id.eq(subject), "period"].astype(str).unique())
    period = w.select("period", "Kỳ cần sửa", periods)
    if period not in periods:
        st.info("Chọn lại kỳ phù hợp đối tượng.")
        return
    binding = state.editor_binding(subject, period)
    editor_key = f"editor::{project.project_id}::{binding.token}"
    baseline_frame, editor_cfg = prepare_blq_editor(
        binding.baseline,
        {"blq_flag": st.column_config.CheckboxColumn("BLQ", default=False, required=True)}
        if hasattr(st, "column_config") else None
    )
    st.data_editor(
        baseline_frame,
        key=editor_key,
        hide_index=True,
        num_rows="fixed",
        column_config=editor_cfg,
        column_order=[
            "sample_id",
            "concentration",
            "concentration_unit",
            "actual_time_h",
            "lloq",
            "blq_flag",
            "sample_status",
            "nominal_time_h",
            "treatment",
            "period",
            "sequence",
            "dose_datetime",
            "sample_datetime",
            "source_batch",
        ],
        disabled=True if project.freeze_hash else [col for col in binding.columns if col not in EDIT_COLUMNS],
        on_change=editor_changed,
        args=(state, binding, editor_key),
        height=380,
    )
    st.caption(
        "Editor theo sample_id cố định; không thêm/xóa hàng. Sắp xếp hiển thị không đổi định danh mẫu."
    )
    st.caption(
        "Nồng độ/LLOQ dùng đơn vị gốc ở concentration_unit; snapshot QC chuẩn hóa ng/mL khi đã xác nhận."
    )
    if state.project.pending_edits:
        st.warning(
            f"Chưa áp dụng: {len(state.project.pending_edits)} mẫu. Bản nháp đã lưu, NCA/BE hiện hành bị khóa."
        )
        st.json(state.project.pending_edits, expanded=False)
    w = Widgets(state, "correction")
    reason = w.text("reason", "Lý do correction")
    reviewer = w.text("reviewer", "Người rà soát độc lập")
    evidence = w.text("evidence", "Tham chiếu bằng chứng correction")
    if st.button(
        "Áp dụng các sửa đổi", disabled=bool(project.freeze_hash or not state.project.pending_edits)
    ):
        state.apply_pending(reason, reviewer, evidence)
        state.checkpoint()
        st.rerun()
    if st.button("Hủy bản nháp chỉnh sửa", disabled=not bool(state.project.pending_edits)):
        state.commit(
            state.project.record(
                "discard_pending", {"pending_edits": {}}, "Người dùng chủ động hủy chỉnh sửa chưa áp dụng"
            )
        )
        state._bindings.clear()
        st.rerun()
    with st.expander("Chỉnh sửa toàn bộ bảng: dán dữ liệu, thêm hoặc xóa mẫu"):
        st.caption("Thay đổi số dòng/số mẫu sẽ tạo revision raw mới sau khi QC đạt. "
                   "Bản raw trước đó và các correction được giữ trong lịch sử.")
        if project.freeze_hash:
            st.info("Hãy tạo revision bằng nút phía trên trước khi thay bảng đã khóa.")
        else:
            source = _qc_replacement_source(project, frame)
            if source is not None:
                initial_whole, source_id = source
                whole = render_persistent_editor(
                f"qc_full::{project.project_id}", initial_whole,
                source_id,
                validator=lambda candidate: validate_structure(
                    candidate, required=REQUIRED
                ).fillna("").astype(str),
                width="stretch", height=420,
                submit_label="Áp dụng bảng để chuẩn bị revision",
                )
            replace_reason = st.text_input(
                "Lý do thay đổi số dòng hoặc thay thế bảng raw",
                key=f"qc_replace_reason::{project.project_id}",
            )
            if st.button(
                "Kiểm tra QC và lưu revision bảng",
                disabled=bool(project.pending_edits or source is None),
                key=f"qc_replace::{project.project_id}",
            ):
                if not replace_reason.strip():
                    st.error("Cần ghi lý do thay thế raw để phục vụ kiểm toán.")
                elif whole.equals(frame.astype(str).reset_index(drop=True)):
                    st.info("Bảng chưa thay đổi.")
                else:
                    replacement = whole.to_csv(index=False).encode("utf-8-sig")
                    check = review_import(
                        replacement, "qc_revised.csv", "{}", project.study,
                        project.allocation, project.allow_unit_conversion,
                    )
                    if not check.ready:
                        st.error(check.error or "Bảng mới chưa vượt qua QC. Sửa bảng và áp dụng lại.")
                        if check.qc is not None:
                            st.dataframe(pd.DataFrame(check.qc.report()).head(30), hide_index=True)
                    else:
                        updated = project.revise(replace_reason.strip(), replace_raw=True)
                        updated = updated.import_raw(
                            replacement, "qc_revised.csv", mapping={},
                            convert_units=project.allow_unit_conversion,
                        )
                        save_project(updated)
    st.caption("Người review là định danh khai báo; chưa phải chữ ký điện tử.")
def show_nca_results(results, key, state=None):
    tables = nca_tables(results)
    parameters, detail, slopes, warnings = st.tabs(
        ["Thông số NCA", "Từng mẫu và pha cuối", "Khoảng hồi quy", "Cảnh báo NCA"]
    )
    with parameters:
        st.dataframe(
            tables["Final Parameters Pivoted"], hide_index=True, alt="41 thông số NCA theo từng profile"
        )
        st.caption("obs: dùng Clast quan sát; pred: dùng Clast dự đoán từ hồi quy. CL/F: mL/h; Vz/F: mL.")
    with detail:
        profiles = {
            f"{x['subject_id']} / {x['period']} / {x['treatment']} / {x.get('analyte', 'parent')}": x
            for x in results
        }
        if state is not None:
            chosen = Widgets(state, "nca_view", "preferences").select(
                "detailed_profile", "Profile để kiểm tra terminal", list(profiles)
            )
        else:
            chosen = st.selectbox("Profile để kiểm tra terminal", list(profiles), key=f"{key}_profile")
        profile = profiles[chosen]
        points = pd.DataFrame(profile.get("profile_points", []))
        if not points.empty:
            linear, logarithmic = st.columns(2)
            for container, log_scale, label in (
                (linear, False, "Tuyến tính"),
                (logarithmic, True, "Bán log"),
            ):
                with container:
                    plotted = points[points.concentration > 0] if log_scale else points
                    figure = go.Figure()
                    figure.add_scatter(
                        x=plotted.time, y=plotted.concentration, mode="lines+markers", name="Quan sát"
                    )
                    terminal = points[points.terminal]
                    if not terminal.empty:
                        figure.add_scatter(
                            x=terminal.time, y=terminal.predicted, mode="lines+markers", name="Hồi quy λz"
                        )
                    figure.update_layout(
                        title=label,
                        xaxis_title="Thời gian (h)",
                        yaxis_title="Nồng độ (ng/mL)",
                        yaxis_type="log" if log_scale else "linear",
                        height=340,
                    )
                    st.plotly_chart(figure, key=f"{key}_{log_scale}")
            st.dataframe(
                points, hide_index=True, alt="Nồng độ, dự đoán, phần dư và diện tích tích lũy từng mẫu"
            )
        with st.expander("Các khoảng terminal đã đánh giá"):
            st.dataframe(pd.DataFrame(profile.get("terminal_candidates", [])), hide_index=True)
        st.json({k: v for k, v in profile.items() if k != "profile_points"}, expanded=False)
    with slopes:
        st.dataframe(tables["Slopes Settings"], hide_index=True)
    with warnings:
        if tables["Warnings and Errors"].empty:
            st.info("Không có cảnh báo NCA.")
        else:
            st.dataframe(tables["Warnings and Errors"], hide_index=True)


def terminal_review_panel(state):
    project = state.project
    if not project.raw_base64:
        return
    view = Widgets(state, "terminal_view", "preferences")
    if not view.check("open", "Rà soát và chọn pha cuối từng profile"):
        return
    st.caption(
        "Chọn riêng từng profile, lưu lý do và người rà soát. Dữ liệu hoặc thời gian thay đổi sẽ yêu cầu rà soát lại. Dự án đã khóa cần tạo revision trước khi áp dụng."
    )
    qc = state.qc()
    if not qc.valid:
        st.info("Cần xử lý QC trước khi chọn terminal.")
        return
    profiles = {
        json.dumps(profile_identity(group), sort_keys=True): group
        for _, group in qc.data.groupby(list(PROFILE_KEYS), sort=True)
    }
    selected = view.select(
        "profile",
        "Profile chọn pha cuối",
        list(profiles),
        format_func=lambda s: " · ".join(
            f"{label}: {json.loads(s)[key]}"
            for key, label in (
                ("subject_id", "Subject"),
                ("period", "Kỳ"),
                ("treatment", "T/R"),
                ("sequence", "Sequence"),
                ("analyte", "Analyte"),
            )
        ),
    )
    if selected not in profiles:
        return
    group = profiles[selected]
    identity = profile_identity(group)
    existing = next(
        (
            o
            for o in project.nca_config.terminal_overrides
            if all(getattr(o, k) == v for k, v in identity.items())
        ),
        None,
    )
    section = "terminal:" + selected
    w = Widgets(state, section)
    mode = w.select(
        "mode",
        "Cách chọn pha cuối",
        ["auto", "manual"],
        "manual" if existing else "auto",
        format_func=lambda x: "Tự động theo SAP" if x == "auto" else "Chọn điểm thủ công",
    )
    options = terminal_eligible_times(group)
    default_times = list(existing.times) if existing else []
    # Keep an old draft visible when data changed; never silently replace its selection.
    displayed_options = sorted(set(options) | set(state.draft(section, "times", default_times)))
    times = w.input(
        "multiselect",
        "times",
        "Thời gian terminal (h)",
        default_times,
        options=displayed_options,
        disabled=mode == "auto",
    )
    reason = w.area("reason", "Lý do lựa chọn terminal", existing.reason if existing else "")
    reviewer = w.text("reviewer", "Người rà soát terminal", existing.reviewer if existing else "")
    if existing and existing.profile_data_hash != profile_data_hash(group):
        st.warning("Dữ liệu profile đã đổi; lựa chọn đã lưu chưa được xác nhận lại.")
    global_manual = bool(project.nca_config.manual_terminal_times)
    if global_manual and mode == "auto":
        st.warning(
            "Cấu hình chung đang chọn terminal thủ công. Cần bỏ lựa chọn chung trước khi áp dụng chế độ tự động cho profile; bản xem trước vẫn cho phép so sánh tự động."
        )
    if st.button("Xem trước tự động và lựa chọn terminal", key=w.key("preview")):
        base = project.nca_config.model_copy(
            update={"terminal_overrides": (), "manual_terminal_times": (), "manual_reason": ""}
        )
        automatic = analyze_profile(group, base, dose=project.study.dose, dose_unit=project.study.dose_unit)
        manual = (
            analyze_profile(
                group,
                base.model_copy(
                    update={"manual_terminal_times": tuple(sorted(times)), "manual_reason": reason}
                ),
                dose=project.study.dose,
                dose_unit=project.study.dose_unit,
            )
            if mode == "manual" and times
            else automatic
        )
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Selection": name,
                        "Terminal times (h)": ", ".join(
                            f"{t:.6g}" for t in (result.get("terminal_selected") or {}).get("times", [])
                        ),
                        **{k: result.get(k) for k in ("lambda_z", "half_life", "auc_inf", "auc_extrap_pct")},
                        "Warnings": "; ".join(result.get("warnings", [])),
                    }
                    for name, result in (("Automatic", automatic), ("Draft selection", manual))
                ]
            ),
            hide_index=True,
        )
        st.plotly_chart(
            terminal_figure(group, automatic, manual),
            alt="Nồng độ theo thời gian để rà soát pha cuối",
        )
        st.caption(
            "Đồ thị semilog chỉ hiện nồng độ dương; ký hiệu đánh dấu các điểm terminal và đường hồi quy của mỗi lựa chọn. Xem trước không cập nhật kết quả nghiên cứu. Áp dụng, khóa và chạy lại để tạo snapshot mới."
        )
    if st.button(
        "Áp dụng lựa chọn terminal",
        key=w.key("apply"),
        disabled=bool(project.freeze_hash) or (global_manual and mode == "auto"),
    ):
        if len(reason.strip()) < 5 or not reviewer.strip():
            raise ValueError("Áp dụng cần lý do tối thiểu 5 ký tự và người rà soát.")
        overrides = [
            o
            for o in project.nca_config.terminal_overrides
            if not all(getattr(o, k) == v for k, v in identity.items())
        ]
        if mode == "manual":
            if not set(times) <= set(options) or len(times) < project.nca_config.terminal_min_points:
                raise ValueError("Chọn đủ số điểm sau đỉnh cuối cùng, sau BLQ nội khoảng và đang định lượng.")
            overrides.append(
                TerminalOverride(
                    **identity,
                    times=tuple(sorted(times)),
                    reason=reason,
                    reviewer=reviewer,
                    profile_data_hash=profile_data_hash(group),
                )
            )
        cfg = NcaConfig.model_validate({**project.nca_config.model_dump(), "terminal_overrides": overrides})
        drafts = {k: v for k, v in project.drafts.items() if k != section}
        for field in ("mode", "times", "reason", "reviewer"):
            st.session_state.pop(w.key(field), None)
        save_project(
            project.record(
                "terminal_review",
                {"nca_config": cfg.model_dump(mode="json"), "drafts": drafts},
                reason,
                reviewer,
            )
        )
    if st.button("Hủy bản nháp terminal", key=w.key("discard")):
        for field in ("mode", "times", "reason", "reviewer"):
            st.session_state.pop(w.key(field), None)
        save_project(
            project.record(
                "discard_terminal_draft",
                {"drafts": {k: v for k, v in project.drafts.items() if k != section}},
                "Hủy bản nháp chọn pha cuối có chủ đích",
            )
        )


def nca_readiness_panel(state) -> None:
    """Explain every NCA gate and give a route to repair a locked project."""
    project = state.project
    blockers = scope_blockers(project.study)
    pending = state.pending_config()
    if not (project.freeze_hash or blockers or pending):
        return

    with st.container(border=True):
        st.subheader("Điều kiện để bật phân tích NCA/BE")
        if project.freeze_hash:
            st.info(
                "Dự án đã Data Freeze: cấu hình NCA/SAP hiện tại được khóa để bảo toàn "
                "dấu vết phân tích. Vì vậy nút 'Lưu cấu hình trước khóa' bị mờ. "
                "Muốn thay đổi cấu hình, cần tạo revision có lý do rồi khóa lại."
            )
        if blockers:
            for item in blockers:
                st.warning(item)
            st.caption(
                "Vào Tổng quan → 'Tạo revision để cập nhật phương pháp / phạm vi'. "
                "Bổ sung bằng chứng guideline/PSG, xác nhận đã rà soát và lưu revision."
            )
            st.button(
                "Đến nơi rà soát phạm vi FDA/EMA →",
                key="nca_go_to_scope_review",
                on_click=go_to_scope_revision,
            )
        if pending:
            st.warning(
                "Có cấu hình NCA/SAP hoặc lựa chọn terminal đang ở bản nháp. "
                "Bản nháp chưa được áp dụng vào đầu vào phân tích."
            )
            if not project.freeze_hash:
                st.caption(
                    "Mở mục 'Cấu hình NCA và thống kê trước khóa' để lưu cấu hình; "
                    "nếu có bản nháp pha cuối, rà soát và áp dụng/hủy ở phần terminal."
                )
        if project.freeze_hash and (pending or blockers):
            reason = st.text_input(
                "Lý do tạo revision để sửa cấu hình/phạm vi",
                key=f"nca_revision_reason::{project.project_id}",
                placeholder="Ví dụ: Hoàn thiện rà soát PSG và cập nhật SAP",
            )
            if st.button(
                "Tạo revision mới để cập nhật và khóa lại",
                key="nca_create_revision",
                disabled=not reason.strip(),
            ):
                save_project(project.revise(reason.strip()))
        if pending and project.freeze_hash:
            st.caption(
                "Nếu các chỉnh sửa nháp là ngoài ý muốn, có thể bỏ riêng bản nháp "
                "NCA/terminal và giữ nguyên cấu hình đã Data Freeze."
            )
            if st.button("Bỏ bản nháp NCA/terminal, giữ bản đã khóa", key="nca_discard_drafts"):
                drafts = {
                    section: values for section, values in project.drafts.items()
                    if section != "nca_config" and not section.startswith("terminal:")
                }
                state.mount_id += "_nca_restored"
                save_project(project.record(
                    "discard_nca_drafts", {"drafts": drafts},
                    "Hủy bản nháp NCA/terminal; giữ nguyên cấu hình đã Data Freeze",
                ))


def nca_page(state):
    st.button("Rà soát bảng PK từ NCA bên ngoài", on_click=go_to_learning_step, args=(PAGES[6],))
    project = state.project
    learning_mode = bool(st.session_state.get("full_be_learning_mode")) and (
        st.session_state.get("workflow") == "BE đầy đủ"
    )
    nca_readiness_panel(state)
    with st.expander("Cấu hình NCA và thống kê trước khóa"):
        draft_notice()
        if project.freeze_hash:
            st.info("Cấu hình đã khóa. Xem hướng dẫn tạo revision hoặc bỏ bản nháp ở phần trên.")
        st.caption(
            "Chọn cách tích phân và tiêu chí pha terminal theo protocol/SAP của nghiên cứu. "
            "Kiểm tra độ phù hợp, số điểm và lý do loại trừ trước khi khóa cấu hình."
        )
        w = Widgets(state, "nca_config")
        integration = w.select(
            "integration", "Tích phân AUC", ["linear_up_log_down", "linear"],
            project.nca_config.integration, disabled=bool(project.freeze_hash),
        )
        r2 = w.number(
            "r2",
            "Adjusted R² tối thiểu terminal theo SAP",
            project.nca_config.terminal_min_adj_r2,
            min_value=0.0,
            max_value=1.0,
            disabled=bool(project.freeze_hash),
        )
        span = w.number(
            "span",
            "Span terminal tối thiểu theo số t1/2",
            project.nca_config.terminal_min_span_half_lives,
            min_value=0.0,
            max_value=10.0,
            disabled=bool(project.freeze_hash),
        )
        variance = w.select(
            "variance",
            "Phương sai parallel theo SAP",
            ["pooled", "welch"],
            project.be_config.parallel_variance,
            disabled=bool(project.freeze_hash),
        )
        missing_policy = w.select(
            "missing_policy",
            "Xử lý endpoint thiếu theo SAP",
            ["block", "available_observations"],
            project.be_config.missing_policy,
            format_func=lambda x: (
                "Chặn kết luận khi thiếu dữ liệu"
                if x == "block"
                else "REML quan sát sẵn có (2×2, cần căn cứ SAP)"
            ),
            disabled=bool(project.freeze_hash),
        )
        missing_reason = w.area(
            "missing_reason",
            "Căn cứ SAP và giả định cho dữ liệu thiếu",
            project.be_config.missing_data_reason,
            disabled=bool(project.freeze_hash),
        )
        if project.study.design == "parallel":
            st.caption(
                "ℹ️ Ngữ cảnh thiết kế Song song (Parallel): tùy chọn **Phương sai parallel theo SAP** (`pooled`/`welch`) "
                "được áp dụng; tùy chọn **REML 2×2 (`available_observations`)** và hệ số biến thiên nội cá thể $CV_{intra}$ "
                "không áp dụng do mỗi đối tượng chỉ dùng một thuốc."
            )
        elif project.study.design == "2x2":
            st.caption(
                "ℹ️ Ngữ cảnh thiết kế Chéo đôi 2×2: **Phương sai parallel** không áp dụng ở bước phân tích BE; "
                "tùy chọn `available_observations` cho phép chạy REML trên quan sát sẵn có nếu được định trước trong SAP."
            )
        else:
            st.caption(
                f"ℹ️ Ngữ cảnh thiết kế Lặp lại ({project.study.design}): **Phương sai parallel** và REML 2×2 không áp dụng; "
                "ước lượng $s_{WR}$, $s_{WT}$ và co giãn RSABE/ABEL (nếu bật) sẽ chạy ở Bước 6 theo quy chế đã chọn."
            )
        if st.button("Lưu cấu hình trước khóa", disabled=bool(project.freeze_hash)):
            cfg = NcaConfig.model_validate(
                {
                    **project.nca_config.model_dump(),
                    "integration": integration,
                    "terminal_min_adj_r2": r2,
                    "terminal_min_span_half_lives": span,
                }
            )
            be = BeConfig.model_validate(
                {
                    **project.be_config.model_dump(),
                    "parallel_variance": variance,
                    "missing_policy": missing_policy,
                    "missing_data_reason": missing_reason,
                }
            )
            save_project(
                project.record(
                    "configure",
                    {"nca_config": cfg.model_dump(mode="json"), "be_config": be.model_dump(mode="json")},
                    "Áp dụng cấu hình từ bản nháp",
                )
            )
    terminal_review_panel(state)
    blockers = scope_blockers(project.study)
    pending_config = state.pending_config()
    if not project.freeze_hash:
        st.warning(
            "Chưa Data Freeze: mở trang QC, bấm 'Kiểm tra / cập nhật QC', "
            "xử lý lỗi/bản nháp và chọn 'Data Freeze và khóa SAP'."
        )
        st.button(
            "Đến QC để kiểm tra và khóa dữ liệu →", key="nca_go_to_qc",
            on_click=go_to_learning_step, args=(PAGES[4],),
        )
    if learning_mode:
        if blockers or pending_config or not project.freeze_hash:
            st.info(
                "Đang thực hành: bạn có thể chuyển sang bước Thống kê BE dù chưa đủ điều kiện "
                "phân tích NCA. Các điều kiện còn thiếu chỉ ngăn chạy tính toán chính thức."
            )
            with st.expander("Xem điều kiện cần hoàn tất để chạy NCA/BE"):
                if not project.freeze_hash:
                    st.write("• Chưa Data Freeze: dùng nút 'Đến QC' phía trên để xem hướng dẫn và khóa dữ liệu.")
                for blocker in blockers:
                    st.write(f"• {blocker}")
                if pending_config:
                    st.write("• Cấu hình chưa áp dụng: lưu cấu hình hoặc khôi phục bản nháp.")
        st.button(
            "Bỏ qua điều kiện NCA để sang Thống kê BE →",
            key="learning_skip_nca",
            on_click=go_to_learning_step,
            args=(PAGES[6],),
        )
    else:
        for blocker in blockers:
            st.warning(blocker)
    if st.button(
        "Phân tích NCA và BE",
        type="primary",
        disabled=bool(not project.freeze_hash or blockers or project.pending_edits or pending_config),
    ):
        state.analyze()
        state.checkpoint()
        st.rerun()
    if pending_config and not learning_mode:
        st.warning(
            "Cấu hình chưa áp dụng trong dự án đã khóa. Dùng phần 'Điều kiện để bật phân tích NCA/BE' "
            "ở đầu trang để tạo revision hoặc bỏ bản nháp."
            if project.freeze_hash else
            "Cấu hình chưa áp dụng; lưu cấu hình hoặc xử lý bản nháp terminal trước khi Data Freeze."
        )
    if learning_mode and not project.runs:
        st.info("Chưa có kết quả NCA vì chưa chạy phân tích. Bạn vẫn có thể xem các bước tiếp theo.")
        run = None
    else:
        run = result_banner(state)
    if run:
        show_nca_results(run["nca"], "nca_" + run["analysis_run_id"], state)
        stale = result_status(project, run) != "CURRENT"
        if st.button("Chuẩn bị Excel NCA", disabled=stale):
            state.render_cache[("nca_excel", run["snapshot_hash"])] = nca_workbook(
                run["nca"],
                metadata={
                    "analysis_run_id": run["analysis_run_id"],
                    "snapshot_hash": run["snapshot_hash"],
                    "input_fingerprint": run["input_fingerprint"],
                },
            )
        cached = state.render_cache.get(("nca_excel", run["snapshot_hash"]))
        if cached and not stale:
            st.download_button("Tải Excel NCA", cached, "NCA.xlsx", on_click="ignore")


def _review_table_cache_key(values, key, data, design):
    # A rule/settings hash and PASS/FAIL decisions do not identify the CI or ANOVA data.
    if data is not None and not isinstance(data, pd.DataFrame):
        data = pd.DataFrame(data)
    data_fingerprint = hashlib.sha256(
        data.to_csv(index=True, float_format="%.17g").encode("utf-8")
    ).hexdigest() if data is not None else None
    return (REVIEW_TABLE_SCHEMA, key, digest(values), design, data_fingerprint)


def show_be_results(results, key, *, data=None, design=None):
    values = [r.model_dump(mode="json") if hasattr(r, "model_dump") else r for r in results]
    # Persisted NCA snapshots contain rows of dicts; independent BE panels use DataFrames.
    if data is not None and not isinstance(data, pd.DataFrame):
        data = pd.DataFrame(data)
    cache = st.session_state.setdefault("review_table_cache", {})
    cache_key = _review_table_cache_key(values, key, data, design)
    if cache_key not in cache:
        if len(cache) >= 16:
            cache.pop(next(iter(cache)))
        cache[cache_key] = be_tables(results, data=data, design=design)
    tables = cache[cache_key]
    summary = pd.DataFrame(values)[
        [
            "endpoint",
            "method",
            "n",
            "n_observations",
            "n_excluded",
            "gmr",
            "ci_lower",
            "ci_upper",
            "decision",
            "reason",
        ]
    ]
    st.dataframe(summary, hide_index=True, column_config=table_column_config(summary.columns), alt="GMR, khoảng tin cậy, cỡ mẫu và kết luận từng endpoint")
    render_table_legend(summary.columns, title="ℹ️ Chú thích tiêu đề cột & thuật ngữ bảng tóm tắt BE")
    st.caption(
        "GMR và CI trong bảng tóm tắt là tỷ lệ; các bảng BE chi tiết hiển thị theo phần trăm. "
        "Endpoint bổ sung không quyết định kết luận nghiên cứu nếu SAP không chọn là endpoint chính."
    )
    conclusions, anova, estimates, scaling, residuals = st.tabs(
        ["Tiêu chí & TOST", "ANOVA", "LS means & hệ số", "Phương sai & HVD/NTI", "Phần dư & dữ liệu thiếu"]
    )
    with conclusions:
        st.write("Bảng rà soát từng tiêu chí")
        st.dataframe(
            tables["Reviewer Criteria"].astype({"Value": "string"}),
            hide_index=True,
            alt="Giá trị, ngưỡng và kết luận từng tiêu chí BE",
        )
        st.caption(
            "Kết quả từng tiêu chí có thể đạt trong khi endpoint vẫn NOT EVALUABLE do điều kiện áp dụng hoặc population. Kết luận endpoint ở cột riêng."
        )
        st.dataframe(tables["Decision Criteria"], hide_index=True, column_config=table_column_config(tables["Decision Criteria"].columns))
        st.dataframe(tables["Confidence Intervals"], hide_index=True, column_config=table_column_config(tables["Confidence Intervals"].columns))
        render_table_legend(["Endpoint", "Method", "GMR", "CI 90%", "Lower_%", "Upper_%", "Decision", "Reason", "Power_TOST", "sWR", "CVwR", "MSE"], title="ℹ️ Chú thích tiêu đề cột & thuật ngữ bảng tiêu chí BE")
        with st.expander("Chi tiết thống kê Average Bioequivalence"):
            st.dataframe(tables["Average Bioequivalence"], hide_index=True)
            st.caption(
                "Power_TOST, Power_80_20, Anderson–Hauck và kiểm tra phương sai là chỉ số bổ trợ. "
                "Kết luận tuân theo CI/TOST hoặc từng tiêu chí scaling, không dựa vào power hậu nghiệm."
            )
    with anova:
        st.caption(
            "Partial Tests: kiểm định Wald từ REML với df Satterthwaite cho 2×2. "
            "Sequential/Partial SS là chẩn đoán OLS; khi thiếu quan sát cần đọc cùng giả định mô hình."
        )
        for name in ("Partial Tests", "Sequential SS", "Partial SS"):
            st.write(name)
            if not tables[name].empty:
                st.dataframe(tables[name], hide_index=True)
        # This display column mixes booleans, counts and model descriptions.
        # Keep typed values in the Excel tables; render an Arrow-safe text view.
        st.dataframe(tables["Diagnostics"].astype({"Value": "string"}), hide_index=True)
    with estimates:
        for name in ("Least Squares Means", "LSM Differences", "Final Fixed Parameters"):
            st.write(name)
            st.dataframe(tables[name], hide_index=True)
    with scaling:
        st.dataframe(tables["Final Variance Parameters"], hide_index=True)
        if not tables["Howe Components"].empty:
            st.write("Cận trên 95% theo Howe (FDA)")
            st.dataframe(tables["Howe Components"], hide_index=True)
        scalars = [
            {
                "endpoint": r["endpoint"],
                "sWR": r.get("swr"),
                "sWT": r.get("swt"),
                "UCB_95": r.get("scaled_ucb"),
                "SD_ratio_CI90_lower": r.get("sd_ratio_ci_lower"),
                "SD_ratio_CI90_upper": r.get("sd_ratio_ci_upper"),
                "lower_limit": r.get("lower_limit"),
                "upper_limit": r.get("upper_limit"),
            }
            for r in values
        ]
        st.dataframe(pd.DataFrame(scalars), hide_index=True, column_config=table_column_config(pd.DataFrame(scalars).columns))
        render_table_legend(pd.DataFrame(scalars).columns, title="ℹ️ Chú thích tiêu đề cột bảng phương sai & HVD/NTI")
        if all(r.get("swr") is None for r in values):
            if design == "parallel":
                st.info(
                    "Thiết kế song song (Parallel) mỗi đối tượng chỉ dùng 1 thuốc (T hoặc R) nên không tách được "
                    "sWR/sWT hay CV nội cá thể; phân tích dùng phương sai giữa các cá thể và không áp dụng co giãn HVD/FDA NTI."
                )
            else:
                st.info(
                    "Thiết kế 2×2 không ước tính riêng sWR/sWT. CV nội cá thể gộp không đủ để áp dụng scaling HVD hoặc FDA NTI."
                )
        if not tables["Subject Contrasts"].empty:
            st.dataframe(tables["Subject Contrasts"], hide_index=True)
        if not tables["FDA Intermediate Fits"].empty:
            st.write("Mô hình trung gian I/D theo sequence (FDA)")
            st.dataframe(tables["FDA Intermediate Fits"], hide_index=True)
    with residuals:
        st.write("Population theo endpoint và kỳ")
        if not tables["Population Matrix"].empty:
            st.dataframe(
                tables["Population Counts"],
                hide_index=True,
                alt="Số đối tượng và quan sát dùng trong từng mô hình",
            )
            st.dataframe(
                tables["Population Matrix"],
                hide_index=True,
                alt="Các kỳ thiếu, giá trị PK và đối tượng dùng trong mô hình hoặc phương sai R/T",
            )
            st.caption(
                "Complete/Two R/Two T mô tả dữ liệu sẵn có; các cột Used cho biết mô hình đã thực sự tính. Bảng này không tự loại dữ liệu hoặc mở mô hình missing replicate."
            )
        else:
            st.info("Cần bảng PK đầu vào cùng snapshot để xem population.")
        st.write("PK mô tả theo treatment")
        st.dataframe(
            tables["PK Descriptive"], hide_index=True, alt="Thống kê mô tả theo endpoint và treatment"
        )
        st.caption(
            "N observations đếm lần dùng thuốc; dữ liệu replicate không được coi là các đối tượng độc lập. Thống kê mô tả không phải adjusted LS means."
        )
        st.dataframe(tables["Residuals"], hide_index=True)
        if st.checkbox("Xem đồ thị chẩn đoán phần dư", key=f"{key}_residual_plots"):
            diagnostic = tables["Residual Diagnostics"]
            if diagnostic.empty:
                diagnostic = tables["Residuals"].copy()
                if not diagnostic.empty:
                    diagnostic["Model"] = "Stored model residuals; no OLS studentization applied"
            if not diagnostic.empty:
                options = (
                    diagnostic[["Dependent", "Model"]].drop_duplicates().itertuples(index=False, name=None)
                )
                selected_fit = st.selectbox(
                    "Endpoint và mô hình chẩn đoán",
                    list(options),
                    format_func=lambda pair: f"{pair[0]} · {pair[1]}",
                    key=f"{key}_residual_fit",
                )
                selected_data = diagnostic.loc[
                    diagnostic.Dependent.eq(selected_fit[0]) & diagnostic.Model.eq(selected_fit[1])
                ]
                st.dataframe(
                    selected_data, hide_index=True, alt="Phần dư và chỉ dấu rà soát của mô hình đã chọn"
                )
                st.caption(
                    "Residual dùng thang mô hình log; studentized residual không có đơn vị. Chỉ dấu |studentized residual| >3 là gợi ý rà soát, không tự loại dữ liệu. REML không dùng chuẩn hóa OLS. QQ plot không là kiểm định chuẩn hay điều kiện tự động để đổi mô hình."
                )
                for index, figure in enumerate(residual_figures(selected_data)):
                    st.plotly_chart(
                        figure,
                        key=f"{key}_residual_{index}",
                        alt="Đồ thị phần dư của đúng endpoint và mô hình đang chọn",
                    )
            else:
                st.info("Snapshot chưa có phần dư gắn định danh để vẽ.")
        st.dataframe(tables["Missing Observations"], hide_index=True)
        with st.expander("Toàn bộ kết quả thống kê và giả định"):
            st.json(values, expanded=False)


def endpoint_be_panel():
    with st.expander("Phân tích bảng PK cho replicate, HVD và NTI"):
        st.caption(
            "Dùng bảng PK đã tính để kiểm tra thống kê. Phân tích này có dữ liệu đầu vào và giả định riêng; "
            "kết luận nghiên cứu chính thức vẫn theo dự án đã QC, protocol/SAP và Data Freeze."
        )
        owner = st.session_state.get("active_project_state") or creation_state(database())
        demo_case = st.selectbox("Học thử · Tình huống bảng PK", list(ENDPOINT_CASES),
                                 format_func=lambda key: ENDPOINT_CASES[key].title,
                                 key="pk_be_demo_case")
        st.caption(ENDPOINT_CASES[demo_case].objective + " " + ENDPOINT_CASES[demo_case].next_step)
        if st.button("Điền dữ liệu mẫu vào bảng PK", key="pk_be_demo_load"):
            design_for_case = ("partial3" if demo_case == "partial3" else
                               "full4" if demo_case in {"full4", "nti", "hvd"} else "2x2")
            rule_for_case = ({"partial3": "EMA_REPLICATE_STANDARD",
                              "full4": "EMA_REPLICATE_STANDARD", "nti": "EMA_NTI",
                              "hvd": "EMA_HVDP_ABEL"}.get(demo_case, "EMA_IR_NONREPLICATE_M13A"))
            content = csv_bytes(endpoint_frame(design_for_case, demo_case))
            owner.set_draft("pk_import", "file", dict(
                name=f"synthetic_pk_{demo_case}.csv",
                base64=base64.b64encode(content).decode("ascii"),
                sha256=hashlib.sha256(content).hexdigest(), demo_case=demo_case,
            ))
            owner.set_drafts("pk_review", {"design": design_for_case, "rule": rule_for_case,
                                           "prespecified": False, "justification": "",
                                           "nti_cmax": False})
            owner.set_draft("pk_import", "units_confirmed", False)
            owner.mount_id += "_demo"
            st.session_state.pop("pk_be_result", None)
            st.rerun()
        binding = (owner.project.project_id, owner.mount_id)
        rebind = st.session_state.get("_pk_be_owner") != binding
        st.session_state["_pk_be_owner"] = binding

        def setting(method, field, label, default, **kwargs):
            key = "pk_be_" + field
            if rebind or key not in st.session_state:
                st.session_state[key] = owner.draft("pk_review", field, default)
            return getattr(st, method)(
                label,
                key=key,
                on_change=changed,
                args=(owner, "draft", "pk_review", field, key),
                **kwargs,
            )

        rule = setting(
            "selectbox",
            "rule",
            "Phương pháp cho bảng PK",
            owner.project.study.rule_set_id,
            options=list(RULES),
        )
        design = setting(
            "selectbox",
            "design",
            "Thiết kế bảng PK",
            owner.project.study.design,
            options=list(DESIGNS),
            format_func=lambda x: DESIGNS[x],
        )
        nti_cmax = setting("checkbox", "nti_cmax", "EMA NTI: thu hẹp cả Cmax theo yêu cầu sản phẩm", False)
        prespecified = setting(
            "checkbox", "prespecified", "Scaling đã định trước trong protocol/SAP của nghiên cứu", False
        )
        justification = setting(
            "text_area", "justification", "Căn cứ áp dụng HVD/NTI và độ tin cậy biến thiên", ""
        )
        w = Widgets(owner, "pk_import")
        st.file_uploader(
            "Bảng PK: subject_id, sequence, period, treatment và cmax/auc_last/auc_inf/auc_inf_pred",
            type=["csv", "xlsx"],
            key=w.key("file"),
            on_change=stage_upload,
            args=(owner, "pk_import", w.key("file")),
        )
        staged = owner.draft("pk_import", "file")
        staged_content = base64.b64decode(staged["base64"]) if staged else None
        sheets = workbook_sheets(staged_content, staged["name"]) if staged else [0]
        sheet = w.select("sheet", "Sheet bảng PK", sheets)
        effective_content: bytes = staged_content if staged_content is not None else b""
        effective_name = staged["name"] if staged else ""
        effective_sheet = sheet
        if staged:
            try:
                source_table = parse_file(effective_content, staged["name"], sheet_name=sheet)
                st.markdown("**Bảng nguồn PK trước khi phân tích**")
                st.caption("Sửa ô hoặc dán từ Excel, thêm/xóa dòng rồi bấm Áp dụng chỉnh sửa bảng. "
                           "Mapping và phân tích sẽ dùng chính bảng đã áp dụng.")
                edited_table = render_persistent_editor(
                    f"pk_be_source::{owner.project.project_id}", source_table,
                    f"{staged['sha256']}::{sheet}",
                    validator=lambda frame: validate_structure(frame).fillna("").astype(str),
                    width="stretch",
                )
                if not edited_table.equals(source_table):
                    effective_content = csv_bytes(edited_table)
                    effective_name, effective_sheet = "edited_pk.csv", 0
            except (ValueError, TypeError, OSError, KeyError, ImportError,
                    pd.errors.ParserError) as exc:
                st.error(f"Không thể mở bảng nguồn PK: {exc}")
        scale = w.select(
            "scale",
            "Thang đo PK trong file nguồn",
            ["raw", "ln", "log10"],
            format_func=lambda x: {"raw": "PK gốc", "ln": "Ln(PK)", "log10": "Log10(PK)"}[x],
        )
        columns_text = w.area(
            "columns", "Mapping cột PK JSON (nguồn → schema)", json.dumps(PK_ALIASES, ensure_ascii=False)
        )
        treatment_text = w.area(
            "treatments", "Mapping nhãn sản phẩm JSON (nguồn → T/R)", '{"T": "T", "R": "R"}'
        )
        sequence_text = w.area("sequences", "Mapping sequence JSON (nguồn → chuỗi T/R)", "{}")
        st.caption(
            "Đơn vị nguồn yêu cầu Cmax ng/mL, AUC h·ng/mL. Khai báo log được chuyển về PK gốc một lần trước khi engine tính Ln(PK); không tự đoán thang đo hay reference."
        )
        units_confirmed = w.check("units_confirmed", "Đã xác nhận đơn vị nguồn Cmax ng/mL và AUC h·ng/mL")
        nca_reference = w.text("nca_reference", "Tham chiếu báo cáo NCA bên ngoài và phiên bản")
        needs_reference = owner.project.study.data_purpose == "regulated_study"

        def import_config():
            return PKImportConfig(
                sheet=effective_sheet,
                scale=scale,
                column_mapping=json.loads(columns_text),
                treatment_mapping=json.loads(treatment_text),
                sequence_mapping=json.loads(sequence_text),
            )

        if st.button("Xem trước mapping bảng PK", disabled=not staged):
            if not units_confirmed:
                raise ValueError("Cần xác nhận đơn vị nguồn trước khi nhập.")
            preview, provenance = import_pk(effective_content, effective_name, import_config())
            st.dataframe(preview, hide_index=True, alt="PK sau mapping và chuyển đổi log về giá trị gốc")
            st.json(provenance, expanded=False)
        input_settings = digest(
            dict(
                owner=owner.project.project_id,
                source=(staged.get("sha256") or digest(staged["base64"])) if staged else None,
                edited_source=hashlib.sha256(effective_content).hexdigest() if effective_content else None,
                sheet=sheet,
                scale=scale,
                columns=columns_text,
                treatments=treatment_text,
                sequences=sequence_text,
                units_confirmed=units_confirmed,
                nca_reference=nca_reference,
                rule=rule,
                design=design,
                nti_cmax=nti_cmax,
                prespecified=prespecified,
                justification=justification,
            )
        )
        calculate = st.button("Phân tích bảng PK đã tải", disabled=not staged or not units_confirmed
                              or (needs_reference and not nca_reference.strip()))
        if calculate:
            if not staged or not units_confirmed:
                raise ValueError("Cần tải bảng PK trước khi phân tích.")
            data, provenance = import_pk(effective_content, effective_name, import_config())
            study = Study.model_validate(
                dict(
                    study_id="PK_REVIEW",
                    title="Independent PK statistics",
                    design=design,
                    rule_set_id=rule,
                    nti=rule in ("EMA_NTI", "FDA_NTI"),
                    nti_cmax_narrow=nti_cmax,
                    scaled_be_prespecified=prespecified,
                    hvd_justification=justification,
                    is_demo=bool(staged.get("demo_case")),
                    data_purpose="training_qa" if staged.get("demo_case") else "unknown",
                )
            )
            endpoints = [e for e in ("cmax", "auc_last", "auc_inf", "auc_inf_pred") if e in data]
            if not endpoints:
                raise ValueError("Không có cột endpoint được hỗ trợ.")
            results = [analyze_regulatory_be(data, e, study) for e in endpoints]
            st.session_state["pk_be_result"] = dict(
                owner_project_id=owner.project.project_id,
                input_settings=input_settings,
                provenance=provenance,
                results=results,
                data=data,
                study=study,
                workbook=be_workbook(
                    results,
                    data=data,
                    metadata={
                        "study": study.model_dump(mode="json"),
                        "source": provenance,
                        "external_nca_reference": nca_reference,
                        "purpose": "Independent statistical review; not a frozen project conclusion",
                    },
                ),
            )
        checked = st.session_state.get("pk_be_result")
        if checked and checked.get("owner_project_id") == owner.project.project_id:
            stale = checked.get("input_settings") != input_settings
            if stale:
                st.warning(
                    "STALE — bảng PK, mapping hoặc giả định đã đổi; cần bấm phân tích lại trước khi tải kết quả."
                )
            if checked["study"].is_demo:
                st.warning(
                    "DỮ LIỆU GIẢ LẬP PHỤC VỤ KIỂM TRA THỐNG KÊ — không có kết luận cho nghiên cứu thật."
                )
            st.caption(
                f"Kết quả đã tính: {checked['study'].rule_set_id} · {checked['study'].design}. Đổi lựa chọn cần bấm phân tích lại."
            )
            shown = (
                checked["results"]
                if not stale
                else [
                    {**r.model_dump(mode="json"), "decision": "STALE — tham khảo lịch sử"}
                    for r in checked["results"]
                ]
            )
            show_be_results(
                shown,
                "pk_be_" + checked["input_settings"] + digest(checked["provenance"]),
                data=checked["data"],
                design=checked["study"].design,
            )
            st.download_button(
                "Tải đầy đủ thống kê bảng PK",
                checked["workbook"],
                "BE_PK_statistics.xlsx",
                on_click="ignore",
                disabled=stale,
            )


def be_page(state):
    project = state.project
    endpoint_be_panel()
    st.subheader("Kết quả BE của nghiên cứu đã lưu")
    if not project.runs:
        st.info("Hoàn tất QC và Data Freeze, rồi chạy tại Phân tích NCA.")
        return
    runs = {run["analysis_run_id"]: run for run in project.runs}
    selected = Widgets(state, "be_view", "preferences").select(
        "run",
        "Lịch sử analysis snapshot",
        list(runs),
        project.runs[-1]["analysis_run_id"],
        format_func=lambda rid: runs[rid]["timestamp"],
    )
    if selected not in runs:
        return
    run = result_banner(state, runs[selected])
    current = result_status(project, run) == "CURRENT"
    rule = run.get("rule_snapshot", {})
    st.caption(
        f"Project: {project.project_id} · dataset r{run['dataset_revision']} · "
        f"rule: {run['rule_set_id']} v{rule.get('version', '?')} · "
        f"purpose: {run['study'].get('data_purpose', 'unknown')} · "
        f"run: {run['timestamp']} · fingerprint: {run['input_fingerprint'][:12]}…"
    )
    st.subheader(DECISIONS[run["study_decision"]] if current else "Kết luận hiện hành: cần tính lại")
    shown = run["be"] if current else [{**r, "decision": "STALE — tham khảo lịch sử"} for r in run["be"]]
    def percent(value):
        return "—" if value is None else f"{value * 100:.2f}%"

    with st.container(border=True):
        col_verdict, col_meta = st.columns([2.5, 1.5])
        with col_verdict:
            if not current:
                st.warning("""⚠️ **Kết luận hiện hành: Cần tính lại**
Dữ liệu hoặc cấu hình đã thay đổi. Kết quả dưới đây chỉ để tham khảo lịch sử.""")
            elif run["study_decision"] == "PASS":
                st.success("""### ✅ ĐẠT TIÊU CHUẨN TƯƠNG ĐƯƠNG SINH HỌC (PASS)
Các thông số dược động học chính thỏa mãn tiêu chuẩn theo quy định hiện hành.""")
            elif run["study_decision"] == "FAIL":
                st.error("""### ❌ KHÔNG ĐẠT TƯƠNG ĐƯƠNG SINH HỌC (FAIL)
Ít nhất một thông số chính không thỏa mãn giới hạn tương đương.""")
            else:
                st.info("""### ⚠️ CHƯA THỂ ĐÁNH GIÁ (NOT EVALUABLE)
Dữ liệu không thỏa mãn điều kiện để kết luận tương đương sinh học.""")
        with col_meta:
            st.caption(f"**Quy tắc:** {run['rule_set_id']} (v{rule.get('version', '?')})")
            st.caption(f"**Thiết kế:** {DESIGNS.get(run['study']['design'], run['study']['design'])}")
            st.caption(f"**Mục đích:** {PURPOSES.get(run['study'].get('data_purpose'), 'Chưa xác định')}")

    if shown and current:
        metric_cols = st.columns(min(3, len(shown)))
        for col, r in zip(metric_cols, shown[:3]):
            with col:
                with st.container(border=True):
                    st.metric(
                        label=f"{r['endpoint']} ({r['method']})",
                        value=percent(r["gmr"]),
                        delta=f"90% CI: [{percent(r['ci_lower'])} – {percent(r['ci_upper'])}]",
                        delta_color="off",
                    )
                    st.caption(f"Trạng thái: **{r['decision']}** | Giới hạn: `{percent(r['lower_limit'])} – {percent(r['upper_limit'])}`")

    st.dataframe(
        [
            {
                "Endpoint": r["endpoint"],
                "Vai trò": r.get("diagnostics", {}).get("endpoint_role", "—"),
                "Phương pháp": r["method"],
                "N": r["n"],
                "GMR": percent(r["gmr"]),
                "CI 90% (bổ trợ nếu RSABE)": f"{percent(r['ci_lower'])} – {percent(r['ci_upper'])}",
                "Giới hạn": f"{percent(r['lower_limit'])} – {percent(r['upper_limit'])}",
                "UCB scaling": "—" if r.get("scaled_ucb") is None else f"{r['scaled_ucb']:.5g}",
                "Trạng thái": r["decision"],
                "Lý do": r.get("reason", ""),
            }
            for r in shown
        ],
        hide_index=True,
        alt="Tóm tắt vai trò endpoint, GMR, CI90, giới hạn, UCB và kết luận của snapshot nghiên cứu",
    )
    rule_id_run = run.get("rule_set_id", "")
    if rule_id_run == "FDA_HVD_RSABE_2026":
        st.caption(
            "FDA RSABE: khi sWR ≥ 0,294 đánh giá theo UCB95 ≤ 0 và GMR ∈ [80,00%–125,00%]; "
            "khi sWR < 0,294 chuyển về ABE chuẩn (CI90 chỉ là thông tin bổ trợ khi sWR ≥ 0,294)."
        )
    elif rule_id_run == "EMA_HVDP_ABEL":
        st.caption(
            "EMA ABEL: mở rộng giới hạn tối đa [69,84%–143,19%] chỉ áp dụng cho Cmax khi CVwR > 30% "
            "(kèm GMR ∈ [80,00%–125,00%]); AUC vẫn giữ biên chuẩn [80,00%–125,00%]."
        )
    elif rule_id_run == "FDA_NTI":
        st.caption(
            "FDA NTI (full replicate 4 kỳ): yêu cầu đạt đồng thời ABE chuẩn [80–125%], RSABE thu hẹp (σ_w0 = 0,10) "
            "và cận trên 90% CI của tỷ số sWT/sWR ≤ 2,5."
        )
    elif rule_id_run == "EMA_NTI":
        st.caption("EMA NTI: áp dụng biên thu hẹp [90,00%–111,11%] cho AUC (và Cmax nếu được quy định trong SAP).")
    elif run["study"]["design"] == "parallel":
        st.caption("Thiết kế song song (Parallel): suy luận dựa trên phương sai giữa các cá thể (pooled hoặc Welch); không ước tính CV_intra.")
    else:
        st.caption("ABE chuẩn: khoảng tin cậy 90% của GMR phải nằm trọn trong giới hạn chấp nhận quy định trong SAP.")
    show_be_results(shown, "be_" + run["analysis_run_id"], data=run["nca"], design=run["study"]["design"])
    st.markdown("**So sánh Tmax phi tham số (phân tích hỗ trợ)**")
    tmax = run.get("tmax_comparison")
    if tmax is None:
        st.info("Snapshot cũ chưa có phép kiểm định Tmax; cần chạy phân tích mới nếu muốn sử dụng.")
    else:
        st.dataframe(pd.DataFrame([
            {"Nhóm": "T", "N": tmax["n_t"], "Trung vị (giờ)": tmax["median_t"],
             "Nhỏ nhất (giờ)": tmax["min_t"], "Lớn nhất (giờ)": tmax["max_t"]},
            {"Nhóm": "R", "N": tmax["n_r"], "Trung vị (giờ)": tmax["median_r"],
             "Nhỏ nhất (giờ)": tmax["min_r"], "Lớn nhất (giờ)": tmax["max_r"]},
        ]), hide_index=True, alt="Trung vị và khoảng Tmax gốc theo T và R")
        if tmax["status"] == "EVALUABLE":
            message = (f"{tmax['method']} · thống kê = {tmax['statistic']:.4g} · "
                       f"p hai phía = {tmax['p_value']:.4g}")
            if tmax["n_pairs"] is not None:
                message += (f" · {tmax['n_pairs']} cặp · trung vị (T−R) = "
                            f"{tmax['median_paired_difference']:.4g} giờ")
            st.write(message)
        else:
            st.info(f"Tmax: NOT EVALUABLE — {tmax['reason']}")
        st.caption(tmax["note"])
    with st.expander("Luồng phân tích và truy vết snapshot"):
        st.dataframe(
            workflow_table(run),
            hide_index=True,
            alt="Các bước phân tích cùng run ID, revision và fingerprint",
        )
        st.caption("Chỉ xem các đầu vào và kết quả đã lưu; không chạy lại QC/NCA/BE khi mở bảng này.")
    with st.container(border=True):
        st.markdown("##### 📥 Xuất sổ tính thống kê BE")
        col_prep, col_dl = st.columns([1, 1])
        with col_prep:
            if st.button("Chuẩn bị Excel thống kê BE", disabled=not current, use_container_width=True):
                with st.spinner("Đang kết xuất sổ tính Excel từ snapshot hiện hành..."):
                    state.render_cache[("be_excel", run["snapshot_hash"])] = be_workbook(
                        run["be"],
                        data=pd.DataFrame(run["nca"]),
                        tmax_comparison=run.get("tmax_comparison"),
                        metadata={
                            "analysis_run_id": run["analysis_run_id"],
                            "input_fingerprint": run["input_fingerprint"],
                            "primary_endpoints": run["study"]["primary_endpoints"],
                            "secondary_endpoints": run["study"].get("secondary_endpoints", []),
                        },
                    )
        prepared = state.render_cache.get(("be_excel", run["snapshot_hash"]))
        with col_dl:
            if current and prepared:
                st.download_button("Tải đầy đủ thống kê BE", prepared, "BE_statistics.xlsx", type="primary", use_container_width=True, on_click="ignore")
            elif not current:
                st.caption("Cần có snapshot hiện hành để xuất thống kê.")
            else:
                st.caption("Bấm nút 'Chuẩn bị Excel thống kê BE' để khởi tạo tệp.")
    for blocker in run["blockers"]:
        st.warning(blocker)
    with st.expander("Chẩn đoán và TOST của snapshot đã chọn"):
        st.json(run["be"], expanded=False)


@st.fragment
def plots_page(state):
    run = result_banner(state)
    if not run:
        return
    key = ("plot_data", run["analysis_run_id"])
    if key not in state.render_cache:
        data = pd.DataFrame(run["validated_data"])
        data.loc[data.blq_flag, "concentration"] = 0
        mean = (
            data.groupby(["treatment", "nominal_time_h"])
            .concentration.agg(["mean", "std", "count"])
            .reset_index()
        )
        state.render_cache[key] = (data, mean)
    data, mean = state.render_cache[key]
    w = Widgets(state, "plot_view", "preferences")
    subject = w.select("subject", "Đối tượng", sorted(data.subject_id.unique()))
    if subject not in set(data.subject_id):
        return
    semilog = w.check("semilog", "Thang bán log nồng độ")
    individual = data.loc[data.subject_id == subject]
    if semilog:
        individual = individual.loc[individual.concentration > 0]
    tab_pk, tab_be = st.tabs(["📈 Đường cong Nồng độ – Thời gian", "📊 Đồ thị Tương đương sinh học & Tiêu chí"])
    with tab_pk:
        fig_ind = px.line(
            individual.sort_values("actual_time_h"),
            x="actual_time_h",
            y="concentration",
            color="treatment",
            color_discrete_map={"T": "#1f77b4", "R": "#d62728"},
            line_group="period",
            markers=True,
            log_y=semilog,
            title=f"Đồ thị nồng độ cá thể — Đối tượng {subject}",
            labels={"actual_time_h": "Thời gian (giờ)", "concentration": "Nồng độ Cplasma", "treatment": "Thuốc"},
        )
        fig_ind.update_layout(template="plotly_white", legend_title_text="Thuốc")
        st.plotly_chart(fig_ind, width="stretch")

        fig_mean = px.line(
            mean, x="nominal_time_h", y="mean", error_y="std",
            color="treatment",
            color_discrete_map={"T": "#1f77b4", "R": "#d62728"},
            title="Đồ thị nồng độ trung bình (Mean ± SD)",
            labels={"nominal_time_h": "Thời gian quy định (giờ)", "mean": "Nồng độ trung bình", "treatment": "Thuốc"},
        )
        fig_mean.update_layout(template="plotly_white", legend_title_text="Thuốc")
        st.plotly_chart(fig_mean, width="stretch")

    with tab_be:
        st.plotly_chart(forest_figure(run["be"]), alt="GMR và CI90 với vùng giới hạn riêng của từng endpoint", width="stretch")
        st.caption(
            "Giới hạn và tiêu chí lấy từ snapshot đang xem. Với FDA RSABE, CI90 màu xám là bổ trợ; kết luận cần UCB và các tiêu chí bên dưới."
        )
        for figure in criterion_figures(run["be"]):
            st.plotly_chart(figure, alt="Tiêu chí FDA theo từng endpoint và ngưỡng quyết định tương ứng", width="stretch")


def protocol_export_panel(state: ProjectState) -> None:
    """Export a pre-analysis study protocol from the current project and saved notes."""
    with st.expander("Đề cương nghiên cứu BE · Xuất Word / PDF", expanded=False):
        st.info(
            "Lập đề cương trước khi thu thập dữ liệu hoặc chạy BE. Bản xuất là DỰ THẢO; "
            "các thông tin chưa khai báo sẽ được đánh dấu để bổ sung và phê duyệt."
        )
        st.caption(
            "Thông tin hành chính, thuốc thử/đối chứng và thiết kế được lấy từ Tổng quan. "
            "Các ghi chú bên dưới được lưu cùng dự án và có thể chỉnh sửa khi quay lại."
        )
        fields = Widgets(state, "protocol")
        template_choice = fields.select(
            "protocol_template",
            "Mẫu đề cương nghiên cứu",
            ["standard", "legacy"],
            format_func=lambda x: (
                "Mẫu chuẩn"
                if x in ("standard", "vknt_tt91")
                else "Mẫu tóm tắt quy định ICH M13A / FDA / EMA (15 phần)"
            ),
        )
        proto_tpl_stem = "Mau_chuan" if template_choice in ("standard", "vknt_tt91") else "Mau_tom_tat"
        st.download_button(
            "Tải mẫu đề cương Word trống (chưa cần dữ liệu)",
            blank_protocol_template(template_choice),
            f"BE_Protocol_Template_{proto_tpl_stem}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            on_click="ignore",
        )
        details = {}
        first, second = st.columns(2, gap="medium", wrap=True)
        for index, (field, label) in enumerate(PROTOCOL_FIELDS):
            with (first if index % 2 == 0 else second):
                details[field] = fields.area(field, label, state.project.study.protocol_details.get(field, ""), height=95)

        project = state.project
        proposed = {k: v.strip() for k, v in details.items() if v.strip()}
        if proposed != project.study.protocol_details:
            st.info("Ghi chú đang ở bản nháp. Khi chốt, ứng dụng lưu nội dung vào phiên bản nghiên cứu và đưa các kết quả phụ thuộc về trạng thái cần tính lại.")
            reason = fields.text("revision_reason", "Lý do chốt nội dung đề cương/SAP")
            if st.button("Chốt nội dung vào phiên bản nghiên cứu", disabled=not reason.strip()):
                study = project.study.model_copy(update={"protocol_details": proposed})
                save_project(project.revise(reason, study=study))
        plan = project.allocation_metadata.get("sample_size_plan")
        valid_plan = None
        if plan is not None:
            expected = planning_fingerprint(
                state.planning(), planning_context(project.study, project.be_config), __version__
            )
            if plan.get("fingerprint") == expected:
                valid_plan = plan
                st.caption("Đã liên kết kết quả cỡ mẫu còn hiệu lực từ trang Thiết kế và cỡ mẫu BE.")
            else:
                st.warning(
                    "Kết quả cỡ mẫu đã cũ (STALE): bản xuất chỉ dùng ghi chú cỡ mẫu, "
                    "không đưa kết quả tính trước đó vào đề cương."
                )

        fingerprint = digest({
            "project_id": project.project_id,
            "study": project.study.model_dump(mode="json"),
            "details": details,
            "valid_plan": valid_plan,
            "template": template_choice,
        })
        key = ("protocol_exports", fingerprint)
        if st.button("Tạo đề cương Word và PDF", key="generate_be_protocol"):
            try:
                word = docx_protocol(project, details, valid_plan=valid_plan, template=template_choice)
                pdf = pdf_protocol(project, details, valid_plan=valid_plan, template=template_choice)
            except (ValueError, OSError, RuntimeError) as exc:
                st.error(f"Không thể tạo đề cương: {exc}")
            else:
                state.render_cache[key] = (word, pdf)
                # Discard previous generated drafts so they cannot be downloaded after editing.
                for old_key in list(state.render_cache):
                    if isinstance(old_key, tuple) and old_key[0] == "protocol_exports" and old_key != key:
                        del state.render_cache[old_key]
        prepared = state.render_cache.get(key)
        if isinstance(prepared, tuple) and len(prepared) == 2:
            stem = f"De_cuong_BE_{project.study.study_id}_vi"
            left, right = st.columns(2)
            with left:
                st.download_button(
                    "Tải đề cương MS Word (.docx)", prepared[0], f"{stem}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    on_click="ignore",
                )
            with right:
                st.download_button(
                    "Tải đề cương PDF (.pdf)", prepared[1], f"{stem}.pdf",
                    mime="application/pdf", on_click="ignore",
                )
            st.success("Đã tạo đề cương dự thảo. Rà soát các vị trí [CẦN BỔ SUNG / XÁC NHẬN].")
        else:
            st.caption("Nhấn Tạo đề cương Word và PDF để chuẩn bị hai tệp từ thông tin hiện tại.")


def reports_page(state):
    project = state.project
    protocol_export_panel(state)
    st.subheader("Báo cáo kết quả BE và dữ liệu phân tích")
    st.info("Báo cáo kết quả nghiên cứu tương đương sinh học dựa trên số liệu phân tích thực tế.")
    report_prefs = Widgets(state, "report", "preferences")
    report_template_choice = report_prefs.select(
        "report_template",
        "Mẫu báo cáo kết quả nghiên cứu",
        ["standard", "legacy"],
        format_func=lambda x: (
            "Mẫu chuẩn"
            if x in ("standard", "vknt_tt91")
            else "Mẫu tóm tắt ASEAN / ICH E3 (Bản song ngữ)"
        ),
    )
    language = report_prefs.select(
        "language",
        "Ngôn ngữ báo cáo",
        ["vi", "en"],
        format_func=lambda x: "Tiếng Việt nội bộ" if x == "vi" else "Tiếng Anh hồ sơ dự thảo",
    )
    rep_tpl_stem = "Mau_chuan" if report_template_choice in ("standard", "vknt_tt91") else "Mau_tom_tat"
    st.download_button(
        "Tải mẫu Word đầy đủ (chưa cần phân tích)",
        blank_report_template(language, template=report_template_choice),
        f"BE_Report_Template_{rep_tpl_stem}_{language}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        on_click="ignore",
    )
    if st.button("Chuẩn bị archive dự án"):
        state.checkpoint()
        state.render_cache["archive"] = (state.working_revision, state.db_revision, export_archive(project))
    archive = state.render_cache.get("archive")
    if archive and archive[:2] == (state.working_revision, state.db_revision):
        st.download_button(
            "Tải xuống toàn bộ dự án",
            archive[2],
            f"{project.study.study_id}.bewf.zip",
            on_click="ignore",
        )
    run = result_banner(state)
    if not run:
        return
    stale = result_status(project, run) != "CURRENT"
    export_key = ("exports", run["snapshot_hash"], digest(project.review_for(run)))
    st.write(f"Kết luận nghiên cứu: {DECISIONS[run['study_decision']]}" if not stale
             else "Cần tính lại trước khi rà soát kết luận hiện hành.")
    for blocker in run.get("blockers", []):
        st.warning(blocker)
    prior = project.review_for(run)
    if prior:
        st.write("Rà soát gần nhất", prior)
    if not stale:
        with st.form(f"review_{run['snapshot_hash']}"):
            reviewer = st.text_input("Người rà soát độc lập")
            evidence = st.text_area("Bằng chứng rà soát, sai lệch và người phụ trách xử lý")
            outcome = st.radio("Kết quả rà soát", ("follow_up", "reviewed"),
                               format_func=lambda x: "Cần xử lý thêm" if x == "follow_up" else "Đã rà soát")
            if st.form_submit_button("Ghi nhận rà soát snapshot"):
                save_project(project.record_review(run["snapshot_hash"], reviewer, evidence, outcome))
    if st.button("Tạo Word và PDF dự thảo", disabled=stale):
        word = docx_report(project, language=language, template=report_template_choice)
        pdf = pdf_report(project, language=language, template=report_template_choice)
        tag = "standard" if report_template_choice in ("standard", "vknt_tt91") else "summary"
        stem = f"{len(project.runs)}_{tag}_{language}_{len(project.artifacts)}"
        save_project(
            project.attach_artifact(f"CSR_{stem}.docx", word).attach_artifact(f"CSR_{stem}.pdf", pdf)
        )
    if st.button("Chuẩn bị datasets và manifest", disabled=stale):
        state.render_cache[export_key] = analysis_exports(project)
    if not stale:
        for name, encoded in project.artifacts.items():
            artifact = project.artifact_manifests.get(name, {})
            if (artifact.get("analysis_run_id") == run["analysis_run_id"]
                    and artifact.get("snapshot_hash") == run["snapshot_hash"]
                    and artifact.get("snapshot_review") == project.review_for(run)):
                st.download_button(f"Tải artifact {name}", base64.b64decode(encoded), name, on_click="ignore")
            else:
                st.caption(f"Artifact lịch sử {name}: khác snapshot hiện hành; giữ trong archive.")
        for name, content in state.render_cache.get(export_key, {}).items():
            st.download_button(f"Tải {name}", content, name, on_click="ignore")


def audit_page(state):
    st.info("Local single-user; chưa có authentication/RBAC hoặc chữ ký điện tử.")
    st.dataframe(pd.DataFrame(state.project.events), hide_index=True)
    st.json(state.metrics)
    st.caption(
        f"Checkpoint {state.db_revision}; journal {state.working_revision}. Bản nháp journal được phục hồi khi mở dự án."
    )


def help_rule_for(page: str, state: ProjectState | None) -> str:
    """Reflect the selected study/PK method without changing either workflow."""
    owner = state or st.session_state.get("creation_state")
    rule = owner.project.study.rule_set_id if owner is not None else next(iter(RULES))
    if page == PAGES[0] and owner is not None:
        rule = owner.draft("revision", "rule", owner.draft("create", "rule", rule))
    if page == PAGES[6]:
        rule = st.session_state.get("pk_be_rule", rule)
    return rule if rule in RULES else next(iter(RULES))


def teaching_information() -> None:
    """Session-local classroom information, independent of study calculations."""
    for key, _, default in TEACHING_FIELDS:
        st.session_state.setdefault(key, default)

    with st.expander("Thông tin giảng dạy", expanded=False):
        st.caption("Thông tin dùng trong phiên học hiện tại; không thay đổi đầu vào hoặc kết quả BE.")
        for offset in range(0, len(TEACHING_FIELDS), 2):
            left, right = st.columns(2, gap="small", wrap=True)
            for column, (key, label, _) in zip(
                (left, right), TEACHING_FIELDS[offset : offset + 2], strict=True
            ):
                with column:
                    st.text_input(label, key=key, max_chars=200)


def render_field_help(page: int | str, key_suffix: str = "") -> None:
    """Explain form labels and table headers without changing study data."""
    with st.expander("Giải thích tên ô, cột/hàng bảng"):
        st.caption("Tra cứu tên ô nhập, tiêu đề cột hoặc chỉ tiêu kết quả của bước này.")
        query = st.text_input(
            "Tìm tên hoặc ký hiệu",
            placeholder="Ví dụ: LLOQ, AUClast, GMR, Tmax...",
            key=f"field_help_search_{page}{key_suffix}",
        ).strip().casefold()
        found = False
        for group in field_help_for(page):
            matches = [
                (label, meaning)
                for label, meaning in group.entries
                if not query or query in label.casefold() or query in meaning.casefold()
            ]
            if not matches:
                continue
            found = True
            st.markdown(f"**{group.title}**")
            st.markdown("\n".join(f"- **{label}** — {meaning}" for label, meaning in matches))
        if not found:
            st.info("Không tìm thấy tên phù hợp trong bước này.")


HELP_CHAPTERS: list[tuple[str, str]] = [
    (PAGES[0], "0. Tạo nghiên cứu & Thiết lập đề cương"),
    (PAGES[1], "1. Thiết kế nghiên cứu & Cỡ mẫu (ICH M13A)"),
    (PAGES[2], "2. Lịch lấy mẫu & Thời gian rửa giải (Washout)"),
    (PAGES[3], "3. Nhập dữ liệu & Toàn vẹn QC (ALCOA+)"),
    (PAGES[4], "4. Khóa dữ liệu (Data Freeze) & Xử lý loại trừ"),
    (PAGES[5], "5. Phân tích Dược động học NCA (Linear Up / Log Down)"),
    (PAGES[6], "6. Đánh giá Tương đương sinh học (ABE / ABEL / RSABE)"),
    (PAGES[7], "7. Chẩn đoán mô hình & Phân tích ngoại lai"),
    (PAGES[8], "8. Xuất hiện vật & Báo cáo pháp quy CTD"),
    (PAGES[9], "9. Rà soát kiểm toán (Audit Trail) & Khóa nghiên cứu"),
    (PAGES[10], "Phân tích Dược động học Độc lập (PK Standalone)"),
    (PAGES[11], "BE Nhanh — Phân tích Độc lập (Quick BE)"),
]


def render_live_diagnostic_banner(page: str, state: ProjectState | None, quick_stage: str | None = None) -> None:
    """Live Context-Aware Workspace Diagnostic Banner (inspired by IVIVC app)."""
    with st.container(border=True):
        st.markdown("🎯 **Trạng thái Ngữ cảnh Thực hành (Live Workspace Diagnostics):**")
        if state is not None and state.project is not None:
            project = state.project
            p_idx = PAGES.index(page) if page in PAGES else -1
            t_prod = project.study.test_product or "Chưa đặt"
            r_prod = project.study.reference_product or "Chưa đặt"
            freeze_status = "ĐÃ KHÓA 🔒" if project.freeze_hash else "CHƯA KHÓA 🔓"
            res_stat = result_status(project)
            
            st.markdown(
                f"- **Mã nghiên cứu:** `{project.study.study_id}` (r{project.input_revision}) | "
                f"**Thuốc Thử (T):** `{t_prod}` | **Thuốc Đối chứng (R):** `{r_prod}`\n"
                f"- **Dữ liệu thô:** `{freeze_status}` | **Kết quả phân tích:** `{res_stat}`"
            )
            
            if p_idx == 0:
                st.caption(
                    f"📌 **Bước 0:** Quy chuẩn `{project.study.rule_set_id}` | "
                    f"Hoạt chất: `{project.study.active_ingredient or 'Chưa khai báo'}` | "
                    f"Liều dùng: `{project.study.dose} {project.study.dose_unit}` ({project.study.fed_state}). "
                    "Chênh lệch hàm lượng hai lô khuyến cáo ≤ 5,0% theo ICH M13A (BE_app không tự hiệu chỉnh hàm lượng)."
                )
            elif p_idx == 1:
                if project.study.design == "2x2":
                    design_note = "Dùng $CV_w$ nội cá thể; tính lực TOST bằng tích phân số chuẩn có điều kiện × phân phối $\\chi^2_\\nu$ (`design.tost_power`)."
                elif project.study.design == "parallel":
                    design_note = "Dùng $CV_{\\text{total}}$ giữa cá thể trên hai nhánh độc lập (`design.tost_power`); không tách $CV_w$."
                else:
                    design_note = "Planning cỡ mẫu trong BE_app đang khóa cho thiết kế replicate (cần mô phỏng Monte Carlo theo SAP)."
                st.caption(
                    f"📌 **Bước 1:** Thiết kế `{project.study.design}` | "
                    f"Chỉ tiêu chính: `{', '.join(project.study.primary_endpoints)}`. {design_note}"
                )
            elif p_idx == 2:
                st.caption(
                    "📌 **Bước 2:** Thời gian rửa giải yêu cầu $T_{\\text{washout}} \\ge 5 \\times t_{1/2}$; "
                    "lấy mẫu cần bao phủ $\\ge 80\\%$ $AUC_{0-\\infty}$ ($AUC_{\\%\\text{extrap}} \\le 20\\%$; trừ ngoại lệ lấy mẫu tới 72 h cho thuốc IR $t_{1/2}$ dài theo ICH M13A)."
                )
            elif p_idx == 3:
                raw_info = f"Tệp `{project.raw_file_name}`" if project.raw_file_name else "Chưa tải tệp nồng độ"
                st.caption(
                    f"📌 **Bước 3:** {raw_info} | Sửa đổi đang chờ: `{len(project.pending_edits)} mẫu`. "
                    "Mọi thay đổi dữ liệu đều được gắn mã băm SHA-256 bảo toàn tính toàn vẹn ALCOA+."
                )
            elif p_idx == 4:
                corr_count = len(project.corrections)
                st.caption(
                    f"📌 **Bước 4:** Số bản ghi sửa hợp lệ: `{corr_count}`. "
                    "Nếu $C_{\\text{predose}} > 5\\% C_{\\max}$, `imports.py` chặn Data Freeze (`PREDOSE_5PCT`) để xử lý loại trừ theo SAP trước khi khóa."
                )
            elif p_idx == 5:
                nc = project.nca_config
                st.caption(
                    f"📌 **Bước 5:** Tích phân `{nc.integration}` (`linear_up_log_down` lùi về tuyến tính nếu $C_{{i+1}}=0$); "
                    f"hồi quy OLS $\\lambda_z$ yêu cầu Adjusted $R^2 \\ge {nc.terminal_min_adj_r2:.2f}$, "
                    f"Span $\\ge {nc.terminal_min_span_half_lives:.1f}\\times t_{{1/2}}$ và $\\ge {nc.terminal_min_points}$ điểm pha cuối."
                )
            elif p_idx == 6:
                rule_id = project.study.rule_set_id
                if rule_id == "FDA_HVD_RSABE_2026":
                    rule_note = "$s_{WR} \\ge 0{,}294 \\Rightarrow$ Howe $UCB_{95} \\le 0$ + GMR $\\in [80, 125]\\%$; $s_{WR} < 0{,}294 \\Rightarrow$ ABE chuẩn $[80, 125]\\%$."
                elif rule_id == "EMA_HVDP_ABEL":
                    rule_note = "Chỉ $C_{\\max}$ mở rộng theo $CV_{wR} > 30\\%$ (tối đa $69{,}84\\%–143{,}19\\%$) + GMR $\\in [80, 125]\\%$; $AUC$ giữ $[80, 125]\\%$."
                elif rule_id == "FDA_NTI":
                    rule_note = "Full replicate 4 kỳ: đạt đồng thời ABE $[80, 125]\\%$, RSABE thu hẹp ($\\sigma_{w0}=0{,}10$) và $s_{WT}/s_{WR} \\le 2{,}5$ (CI 90%)."
                elif rule_id == "EMA_NTI":
                    rule_note = "Thu hẹp biên $[90{,}00\\%–111{,}11\\%]$ cho AUC (và Cmax nếu quy định trong SAP)."
                elif project.study.design == "parallel":
                    rule_note = f"Thiết kế song song (`{project.be_config.parallel_variance}`): so sánh trên log với phương sai giữa cá thể, không tách $CV_{{intra}}$."
                else:
                    rule_note = "ABE chuẩn: khoảng tin cậy 90% của GMR nằm trọn trong $[80{,}00\\% – 125{,}00\\%]$ cho $C_{\\max}$ và $AUC$."
                st.caption(f"📌 **Bước 6:** Quy chuẩn `{rule_id}` ({project.study.design}). {rule_note}")
            elif p_idx == 7:
                st.caption(
                    "📌 **Bước 7:** Phần dư chuẩn hóa Studentized $|r_i| > 3{,}0$ là tín hiệu tham khảo nghi ngờ ngoại lai "
                    "(theo thực hành thống kê; chỉ dùng đánh giá độ nhạy, không tự ý loại bỏ đối tượng khỏi tập phân tích)."
                )
            elif p_idx == 8:
                st.caption(
                    "📌 **Bước 8:** Xuất hồ sơ báo cáo & gói truy vết dự án kèm bảng kê SHA-256 Manifest; "
                    "nội dung báo cáo dùng hỗ trợ rà soát chuyên môn trước khi biên tập hồ sơ CTD chính thức."
                )
            elif p_idx == 9:
                st.caption(
                    f"📌 **Bước 9:** Nhật ký kiểm toán nối chuỗi băm SHA-256 trên SQLite gồm `{len(project.events)} sự kiện`. "
                    "Hỗ trợ truy vết cục bộ đơn người dùng (chưa có phân quyền RBAC hay chữ ký điện tử đầy đủ theo 21 CFR Part 11 / EU GMP Annex 11)."
                )
        elif page == PAGES[10]:
            rt = st.session_state.get("pk_route", "oral")
            dm = st.session_state.get("pk_dose_mode", "single")
            wt = st.session_state.get("pk_weighting", "equal")
            methods = ", ".join(st.session_state.get("pk_methods", ["NCA", "1 ngăn"])) or "Chưa chọn"
            st.markdown(
                f"- **Đường dùng:** `{rt}` | **Chế độ liều:** `{dm}` | **Trọng số:** `{wt}`\n"
                f"- **Phương pháp đang chọn:** `{methods}` (chỉ so sánh $AIC_c$ trên cùng hồ sơ, cùng tập mẫu và cùng trọng số)."
            )
            if rt == "oral":
                rt_note = "Hấp thu bậc 1 với $T_{\\text{lag}} = 0$ cố định trong solver; tham số biểu kiến mang `/F` ($CL/F, V/F$); cảnh giác hiện tượng flip-flop ($k_a < k_{el}$)."
            elif rt == "iv_bolus":
                rt_note = "Tiêm TM nhanh ($F=1$): tách trực tiếp $CL$ và $V_c$; không nhập $C(0)=0$ nhân tạo làm điểm đo (nếu cần, bật ngoại suy $C_0$ ở NCA)."
            else:
                rt_note = "Truyền TM tốc độ hằng $R_0 = D/T_{\\text{inf}}$ ($F=1$): $C_{\\max}$ thực ở $t = T_{\\text{inf}}$ và $MRT_{\\text{thực}} = MRT_{\\text{inf}} - T_{\\text{inf}}/2$."
            if dm != "single":
                rt_note += " Đa liều dùng cộng tác dụng tuyến tính cách đều $\\tau$; $CL_{ss}$ chỉ tính khi xác nhận steady-state và có liều."
            st.caption(f"📌 {rt_note}")
        elif page == PAGES[11]:
            q_design = st.session_state.get("quick_design", "2x2")
            q_rule = st.session_state.get("quick_rule", "EMA_IR_NONREPLICATE_M13A")
            q_mode = st.session_state.get("quick_mode", "concentration")
            if q_design == "parallel":
                q_note = "Song song (Pooled/Welch): không ước tính $CV_{\\text{intra}}$; so sánh $T_{\\max}$ bằng Mann-Whitney U."
            elif q_design in ("partial3", "full4"):
                q_note = f"Replicate (`{q_design}`): tách được $s_{{WR}}$/$s_{{WT}}$; phần mềm không tự chạy kiểm định phi tham số $T_{{\\max}}$ (`NOT EVALUABLE`)."
            else:
                q_note = "Chéo đôi $2\\times 2$: ANOVA OLS / REML trên thang log; so sánh $T_{\\max}$ bằng Wilcoxon signed-rank."
            st.markdown(
                f"- **Luồng phân tích:** `BE Nhanh (R&D / Giảng dạy)` | **Giai đoạn:** `{quick_stage or 'Nhập liệu'}`\n"
                f"- **Thiết kế & Quy tắc:** `{q_design}` | `{q_rule}` | **Đầu vào:** `{q_mode}`"
            )
            st.caption(f"📌 {q_note} Lưu ý: Kết quả BE nhanh ở trạng thái DRAFT; hồ sơ đăng ký chính thức cần quy trình BE đầy đủ.")
        else:
            st.caption(
                "⏳ **Chưa mở hoặc tạo dự án:** Hãy nhập thông tin thuốc Thử (T) và thuốc Đối chứng (R) "
                "ở bước Tổng quan (Bước 0) hoặc nạp dữ liệu mẫu để kích hoạt hệ thống chẩn đoán ngữ cảnh thời gian thực."
            )


def render_dimensional_analysis() -> None:
    """Dimensional homogeneity and unit consistency checker (inspired by IVIVC app)."""
    with st.expander("📐 Bộ Kiểm tra Đồng nhất Thứ nguyên & Đơn vị (Dimensional Analysis)", expanded=False):
        st.markdown(
            "- **Nguyên tắc bảo toàn thứ nguyên (*Dimensional Homogeneity*):**\n"
            "  - **Nồng độ huyết tương:** $[C] = \\text{ng/mL} = \\mu\\text{g/L} = \\text{mg/L}$ (tùy đơn vị khai báo).\n"
            "  - **Thời gian lấy mẫu:** $[t] = \\text{h}$ (giờ).\n"
            "  - **Diện tích dưới đường cong:** $[AUC] = [C] \\times [t] = \\text{ng}\\cdot\\text{h/mL}$ hoặc $\\text{mg}\\cdot\\text{h/L}$.\n"
            "  - **Hằng số tốc độ:** $[k_{el}] = [\\lambda_z] = [k_a] = \\text{h}^{-1}$.\n"
            "  - **Thời gian bán thải:** $[t_{1/2}] = \\ln(2) / [\\lambda_z] = \\text{h}$.\n"
            "  - **Độ thanh thải toàn thân:** $[CL] = [\\text{Dose}] / [AUC_{0-\\infty}] = \\text{L/h}$ (sau uống biểu kiến là $CL/F$).\n"
            "  - **Thể tích phân bố:** $[V] = [CL] / [k_{el}] = \\text{L}$ (sau uống biểu kiến là $V/F$).\n"
            "  - **Thời gian lưu trú trung bình:** $[MRT] = [AUMC_{0-\\infty}] / [AUC_{0-\\infty}] = (\\text{ng}\\cdot\\text{h}^2/\\text{mL}) / (\\text{ng}\\cdot\\text{h/mL}) = \\text{h}$."
        )
        st.caption("💡 Mọi phép tính tích phân hình thang NCA và khớp mô hình ngăn đều bảo toàn đơn vị chuẩn trước khi tính toán.")


def _set_help_chapter(chapter: str, key_suffix: str = "") -> None:
    st.session_state[f"_help_browse_chapter{key_suffix}"] = chapter
    st.session_state[f"help_chapter_selector{key_suffix}"] = chapter


def _on_help_chapter_select(key_suffix: str = "") -> None:
    st.session_state[f"_help_browse_chapter{key_suffix}"] = st.session_state[f"help_chapter_selector{key_suffix}"]


def _help_navigation(page: str, is_dialog: bool = False) -> str:
    """Chapter browsing navigation (inspired by IVIVC app)."""
    key_suffix = "_dialog" if is_dialog else "_side"
    browse_key = f"_help_browse_chapter{key_suffix}"
    selector_key = f"help_chapter_selector{key_suffix}"
    last_page_key = f"_help_last_active_page{key_suffix}"
    
    chapter_keys = [p for p, _ in HELP_CHAPTERS]
    current = page if page in chapter_keys else chapter_keys[0]
    
    if st.session_state.get(last_page_key) != current:
        st.session_state[last_page_key] = current
        _set_help_chapter(current, key_suffix)
        
    chosen = st.session_state.get(browse_key, current)
    if chosen not in chapter_keys:
        chosen = current
    if st.session_state.get(selector_key) != chosen:
        _set_help_chapter(chosen, key_suffix)
        
    chapter_dict = dict(HELP_CHAPTERS)
    st.caption(f"📍 Ngữ cảnh làm việc: **{chapter_dict.get(page, page)}**")
    
    selected = st.selectbox(
        "📚 Xem chủ đề trợ giúp & bài giảng",
        chapter_keys,
        index=chapter_keys.index(chosen),
        format_func=lambda p: chapter_dict.get(p, p),
        key=selector_key,
        on_change=_on_help_chapter_select,
        args=(key_suffix,),
        help="Chọn bước bất kỳ để tra cứu bài giảng mà không ảnh hưởng đến màn hình tính toán.",
    )
    st.session_state[browse_key] = selected
    
    if selected != current:
        st.button(
            f"↩ Quay lại bước đang làm ({page})",
            key=f"btn_help_reset_chapter{key_suffix}",
            use_container_width=True,
            on_click=_set_help_chapter,
            args=(current, key_suffix),
        )
            
    return selected


def render_help_body(page: str, state: ProjectState | None, quick_stage: str | None = None, is_dialog: bool = False, viewed_page: str | None = None) -> None:
    """Render the 6 pedagogical subsections for the contextual help pane or floating dialog."""
    active_view_page = viewed_page or page
    page_index = PAGES.index(active_view_page) if active_view_page in PAGES else 0
    lesson = lesson_for(page_index)

    # 0. Live workspace diagnostic banner & Dimensional analysis
    render_live_diagnostic_banner(active_view_page, state, quick_stage)
    render_dimensional_analysis()

    # -------------------------------------------------------------------------
    # 1. HƯỚNG DẪN THAO TÁC
    # -------------------------------------------------------------------------
    st.markdown("### 1. Hướng dẫn thao tác")
    with st.expander("1. Hướng dẫn Thao tác & Quy trình Thực hành (Operational Guide & SOP)", expanded=True):
        if page_index < 10:
            st.markdown("**Thành phần giao diện**")
            st.markdown(
                "- **Thông tin giảng dạy (bên trái):** nhập tên trường, khoa, giảng viên, "
                "học viên, lớp và khoá; có thể thu gọn khi làm bài. Các giá trị chỉ giữ trong phiên học."
            )
        elif page_index == 10:
            st.markdown(
                "**Dữ liệu:** CSV/XLSX dạng long (mỗi dòng một mẫu) "
                "hoặc wide (mỗi cột một hồ sơ). Thời gian tính từ lúc dùng liều, đơn vị giờ."
            )
            st.markdown(
                "**NCA:** Cmax, Tmax, AUC, AUMC, lambda-z, t½, MRT. "
                "CL và thể tích chỉ tính khi có liều, AUC0–∞ hợp lệ. "
                "MRT của truyền IV phải trừ một nửa thời gian truyền."
            )
            if st.session_state.get("pk_route") == "oral":
                st.caption("Sau uống, phân biệt CL/F với CL. Ghi rõ căn cứ nếu dùng giá trị F để diễn giải.")
            elif st.session_state.get("pk_route") == "iv_infusion":
                st.caption("Đối chiếu thời gian truyền với hồ sơ dùng thuốc khi diễn giải MRT.")
        elif page_index == 11:
            st.markdown("**NCA** cần Subject, Sequence, Period, Treatment, Cplasma và Time (giờ).")
            st.markdown("**BE từ PK** cần 4 cột định danh và Cmax hoặc AUClast/AUCinf.")
            st.markdown("Xác nhận mapping và đơn vị; mỗi subject/period có một profile hoặc một hàng PK.")
            st.warning(
                "Không tự tạo mẫu Time=0, thay thế BLQ hoặc loại người tham gia thiếu kỳ. "
                "Kết quả phân tích dựa trên số liệu thực tế của nghiên cứu."
            )

        for item in lesson.interface:
            st.markdown(f"- {item}")

        key_suffix = "_floating" if is_dialog else ""
        if page_index < 10:
            render_field_help(page_index, key_suffix=key_suffix)
        elif page_index == 10:
            render_field_help("pk", key_suffix=key_suffix)
        elif page_index == 11:
            render_field_help("quick", key_suffix=key_suffix)

        st.markdown("**Các thao tác cần làm**")
        for number, item in enumerate(lesson.actions, start=1):
            st.markdown(f"{number}. {item}")

    # -------------------------------------------------------------------------
    # 2. TÓM TẮT LÝ THUYẾT VÀ TIÊU CHUẨN PHÁP QUY
    # -------------------------------------------------------------------------
    st.markdown("### 2. Tóm tắt lý thuyết và tiêu chuẩn pháp quy")
    with st.expander("2. Tóm tắt Lý thuyết (Sơ đồ Minh họa) & Tiêu chuẩn Pháp quy (Theory & Regulatory Standards)", expanded=True):
        st.markdown("**Cơ sở lý thuyết & Sinh dược học:**")
        for item in lesson.theory:
            st.markdown(f"- {item}")

        if lesson.diagram:
            st.markdown("**Sơ đồ minh họa:**")
            if lesson.diagram.strip().startswith("<svg"):
                try:
                    st.image(lesson.diagram, use_container_width=True)
                except TypeError:
                    st.image(lesson.diagram, width="stretch")
            else:
                st.markdown(lesson.diagram)

        if lesson.regulations:
            st.markdown("**Tiêu chuẩn & Văn bản pháp quy áp dụng:**")
            for reg in lesson.regulations:
                st.markdown(f"- {reg}")

        if page_index < 10:
            st.markdown("**Phương pháp / quy định liên quan**")
            context_rule = help_rule_for(active_view_page, state)
            sel_key = "context_help_method" if not is_dialog else "context_help_method_floating"
            chosen_rule = st.selectbox(
                "Tìm hiểu profile",
                ["Theo ngữ cảnh", *RULES],
                key=sel_key,
                help="Chỉ đổi nội dung trợ giúp; không thay đổi thiết kế hay phân tích.",
            )
            rule_id = context_rule if chosen_rule == "Theo ngữ cảnh" else chosen_rule
            rule = RULES[rule_id]
            explanation, status, sources = profile_help(rule_id)
            st.caption(f"{rule.jurisdiction} · {rule.method} · {rule_id}")
            for item in explanation:
                st.markdown(f"- {item}")
            if capability_for(rule_id).endpoint_decision != "available":
                st.warning(status)
            else:
                st.info(status)
        elif page_index == 10:
            st.markdown("---")
            st.markdown("**Tra cứu chuyên sâu theo từng mô hình (Interactive Compartmental Model Explorer):**")
            st.caption("Tổ chức theo cấu trúc chuẩn: Đường dùng thuốc → Số ngăn → Lý thuyết → Sơ đồ → Phương trình → Tham số → Ví dụ minh họa.")
            sel_key = "pk_help_model_sel" if not is_dialog else "pk_help_model_sel_floating"
            model_options = [
                "Toàn cảnh 9 mô hình (Tổng quan kiến trúc)",
                "1. Tiêm tĩnh mạch nhanh (IV Bolus) — 1 Ngăn",
                "2. Tiêm tĩnh mạch nhanh (IV Bolus) — 2 Ngăn",
                "3. Tiêm tĩnh mạch nhanh (IV Bolus) — 3 Ngăn",
                "4. Truyền tĩnh mạch liên tục (IV Infusion) — 1 Ngăn",
                "5. Truyền tĩnh mạch liên tục (IV Infusion) — 2 Ngăn",
                "6. Truyền tĩnh mạch liên tục (IV Infusion) — 3 Ngăn",
                "7. Đường uống (Oral) — 1 Ngăn (Bateman)",
                "8. Đường uống (Oral) — 2 Ngăn",
                "9. Đường uống (Oral) — 3 Ngăn",
            ]
            chosen_model = st.selectbox(
                "Chọn mô hình cần tra cứu chuyên sâu",
                model_options,
                index=0,
                key=sel_key,
                help="Xem sơ đồ vector riêng biệt, phương trình ODE, tham số và ví dụ lâm sàng tính toán cụ thể.",
            )
            if chosen_model != "Toàn cảnh 9 mô hình (Tổng quan kiến trúc)":
                render_compartment_model_details(chosen_model)

        if lesson.interpretation:
            st.markdown("**Điều kiện diễn giải & Phạm vi áp dụng:**")
            for tip in lesson.interpretation:
                st.markdown(f"- {tip}")

    if lesson.examples:
        with st.expander("Ví dụ minh họa & Kết quả kiểm chứng", expanded=is_dialog):
            for ex in lesson.examples:
                st.markdown(f"- {ex}")

    # -------------------------------------------------------------------------
    # 3. PHƯƠNG TRÌNH TOÁN HỌC VÀ GIẢI THÍCH BIẾN SỐ
    # -------------------------------------------------------------------------
    st.markdown("### 3. Phương trình toán học và giải thích biến số")
    with st.expander("3. Phương trình Toán học & Giải thích Biến số (Mathematical Formulations & Parameter Nomenclature)", expanded=True):
        if lesson.equations:
            for eq_latex, eq_desc in lesson.equations:
                st.latex(eq_latex)
                st.markdown(eq_desc.replace(r"\n", "\n"))
        else:
            st.info("Bước này tập trung vào thiết lập quy trình quản trị, không sử dụng công thức tính toán trực tiếp.")

    # -------------------------------------------------------------------------
    # 4. THUẬT NGỮ
    # -------------------------------------------------------------------------
    st.markdown("### 4. Thuật ngữ")
    with st.expander("4. Thuật ngữ Chuyên ngành (UI-Mapped Technical Glossary)", expanded=is_dialog):
        st.markdown("**Thuật ngữ chuyên ngành:**")
        for item in lesson.terms:
            st.markdown(f"- {item}")

    with st.expander("Data Integrity · Thuật ngữ và ví dụ", expanded=is_dialog):
        st.caption("Nguyên tắc chung và thuật ngữ liên quan trực tiếp đến bước đang học.")
        for term in integrity_terms_for(page_index):
            st.markdown(f"**{term.name}** — {term.meaning}")
            st.caption(f"Ví dụ trong app: {term.app_example}")
        st.caption(
            "Tài liệu tham khảo (phân biệt phạm vi GCP và CGMP): "
            "[ICH E6(R3) GCP – EMA]"
            "(https://www.ema.europa.eu/en/scientific-guidelines/ich-e6-good-clinical-practice) · "
            "[FDA Data Integrity – CGMP (2018)]"
            "(https://www.fda.gov/regulatory-information/search-fda-guidance-documents/"
            "data-integrity-and-compliance-drug-cgmp-questions-and-answers)"
        )

    # -------------------------------------------------------------------------
    # 5. CÂU HỎI GỢI Ý VÀ CHỦ ĐỀ TỰ HỌC
    # -------------------------------------------------------------------------
    st.markdown("### 5. Câu hỏi gợi ý và chủ đề tự học")
    with st.expander("5. Câu hỏi Gợi ý & Chủ đề Tự học (Inquiry-Based Questions & Doctoral Self-Study Topics)", expanded=is_dialog):
        st.markdown("**Bài thực hành cho nghiên cứu sinh**")
        if page_index < 10:
            st.write(RESEARCH_TASKS[page_index])
        elif page_index == 10:
            dose_mode = st.session_state.get("pk_dose_mode")
            if dose_mode in ("multiple", "steady_state"):
                st.write(
                    "Dùng khoảng cách liều τ và số liều thực dùng để xác định khoảng liều cuối. "
                    "Kiểm tra mốc thời gian, mẫu ở cả hai biên và BLQ trước khi diễn giải AUCτ."
                )
                if dose_mode == "steady_state":
                    st.write("Ghi bằng chứng đạt trạng thái ổn định trước khi xác nhận. Đối chiếu liều và AUCτ khi diễn giải độ thanh thải.")
            else:
                st.write("Chọn một hồ sơ đơn liều. Đánh dấu Cmax, Tmax và các mẫu pha cuối trên đồ thị bán log. Giải thích cách xử lý khi thiếu mẫu tại t=0.")
            if any(method != "NCA" for method in st.session_state.get("pk_methods", [])):
                st.write("Với mô hình ngăn đang chọn, xem phần dư theo thời gian. Khi so sánh AICc, giữ cùng dữ liệu và trọng số rồi giải thích lựa chọn mô hình.")
        elif page_index == 11:
            st.write(QUICK_TASKS[quick_stage or "input"])

        st.markdown("**Câu hỏi cốt lõi phản biện:**")
        st.write(lesson.exercise)

        if lesson.questions:
            st.markdown("**Chủ đề đào sâu tư duy phản biện & Thảo luận Seminar:**")
            for q in lesson.questions:
                st.markdown(f"- {q}")

    if lesson.question_answers:
        with st.expander("Gợi ý đáp án & Giải thích tự kiểm tra", expanded=is_dialog):
            for q_title, q_ans in lesson.question_answers:
                st.markdown(f"**{q_title}**")
                st.markdown(q_ans)

    if lesson.self_study:
        with st.expander("Chủ đề tự học chuyên sâu (Contextual Self-Study)", expanded=is_dialog):
            for topic_title, topic_body in lesson.self_study:
                st.markdown(f"**{topic_title}**")
                st.markdown(topic_body)

    # -------------------------------------------------------------------------
    # 6. TÀI LIỆU THAM KHẢO
    # -------------------------------------------------------------------------
    st.markdown("### 6. Tài liệu tham khảo")
    with st.expander("6. Tài liệu Tham khảo Học thuật & Pháp quy (Authoritative Academic & Regulatory References)", expanded=is_dialog):
        if page_index < 10:
            st.markdown("**Văn bản quy phạm & Hướng dẫn chính thức:**")
            st.caption(f"{rule.guideline} · mục {rule.section}; nguồn được rà soát: {rule.source_verified_on}.")
            for n, url in enumerate(sources, start=1):
                st.markdown(f"- [Văn bản chính thức {n}]({url})")

        if lesson.references:
            st.markdown("**Tài liệu khoa học & Giáo trình chuẩn:**")
            for ref in lesson.references:
                st.markdown(f"- {ref}")

        st.caption("Tài liệu hướng dẫn trong dự án: docs/ALGORITHM_SPEC.md, docs/REGULATORY_MATRIX.md.")
        st.caption("Hệ thống phân tích và báo cáo tương đương sinh học.")


@st.dialog("📚 Bài giảng chuyên sâu & Trợ giúp theo ngữ cảnh", width="large")
def open_floating_help_dialog(page: str, state: ProjectState | None, quick_stage: str | None = None) -> None:
    """Modal overlay that expands horizontally up to 1280px and floats over the web page."""
    st.markdown(
        """<style>
        [data-testid="stImage"] {
            display: flex;
            justify-content: center;
            width: 100%;
        }
        [data-testid="stImage"] img {
            width: 100% !important;
            max-width: 960px !important;
            height: auto !important;
            border-radius: 8px;
        }
        </style>""",
        unsafe_allow_html=True,
    )
    st.caption(f"📍 Chế độ toàn cảnh mở rộng nổi · {page}")
    st.info(
        "Nội dung trợ giúp được mở rộng toàn diện theo chiều ngang và hiển thị nổi trên trang web "
        "để tối ưu hóa không gian hiển thị cho các công thức toán học, bảng dữ liệu và sơ đồ quy trình."
    )
    viewed_page = _help_navigation(page, is_dialog=True)
    render_help_body(page, state, quick_stage, is_dialog=True, viewed_page=viewed_page)
    st.markdown("---")
    if st.button("✕ Thu gọn / Đóng cửa sổ nổi", key="btn_close_floating_help_dialog", type="primary", use_container_width=True):
        st.rerun()


def contextual_help(page: str, state: ProjectState | None, quick_stage: str | None = None) -> None:
    """Read-only postgraduate teaching pane; updating it never edits a project or re-runs BE."""
    page_index = PAGES.index(page)
    with st.container(border=True):
        col_title, col_expand = st.columns([1.6, 1.4])
        with col_title:
            if page == "Phân tích PK độc lập":
                st.subheader("Trợ giúp phân tích PK")
            elif page == "BE nhanh — phân tích độc lập":
                st.subheader("BE nhanh")
            else:
                st.subheader("Trợ giúp")
            st.caption(f"Theo bước: {page}")
        with col_expand:
            if st.button(
                "⤢ Mở rộng nổi",
                key=f"btn_expand_floating_help_{page_index}",
                help="Mở rộng bài giảng theo chiều ngang và hiển thị nổi trên toàn trang web",
                use_container_width=True,
            ):
                open_floating_help_dialog(page, state, quick_stage)

        viewed_page = _help_navigation(page, is_dialog=False)

        if state is None and page_index < 10 and page_index:
            if page_index in (5, 6):
                st.info("Bạn có thể đối chiếu dữ liệu ngoài tại bước này. Để làm việc với dữ liệu nghiên cứu, mở hoặc tạo dự án ở Tổng quan.")
            else:
                st.info("Mở hoặc tạo dự án ở Tổng quan để thực hành bước này.")
        elif state and page_index == 4:
            _, next_step = workflow_progress(state.project)
            st.info(next_step)
        elif state and page_index in (5, 6, 7, 8):
            status = result_status(state.project)
            if status == "EMPTY" and page_index == 8:
                st.info("Bạn có thể soạn đề cương và tải mẫu Word ngay. Để tạo báo cáo kết quả, cần có lần phân tích hiện hành.")
            elif status == "EMPTY":
                st.info("Dự án chưa có kết quả. Kiểm tra dữ liệu và Data Freeze ở bước QC trước khi chạy phân tích của dự án.")
            elif status != "CURRENT":
                st.info(f"Kết quả gần nhất có trạng thái {status}. Kiểm tra thay đổi đầu vào và chạy lại trước khi diễn giải hoặc xuất kết quả.")

        render_help_body(page, state, quick_stage, is_dialog=False, viewed_page=viewed_page)


def go_to_learning_step(target):
    """Button callback runs before the sidebar navigation widget is created."""
    index = PAGES.index(target)
    stage = next(i for i, indices in enumerate(STAGE_PAGES) if index in indices)
    st.session_state.be_stage = STAGE_NAMES[stage]
    st.session_state[f"be_detail_{stage}"] = target


def go_to_scope_revision():
    st.session_state.expand_scope_revision = True
    go_to_learning_step(PAGES[0])


def full_be_navigation():
    resume = st.session_state.pop("resume_be_page", None)
    if resume in PAGES[:10]:
        go_to_learning_step(resume)
    stage = st.sidebar.radio("Chặng nghiên cứu", STAGE_NAMES, key="be_stage", persist_state="session")
    index = STAGE_NAMES.index(stage)
    details = [PAGES[i] for i in STAGE_PAGES[index]]
    page = details[0]
    if len(details) > 1:
        page = st.sidebar.radio("Công việc trong chặng", details, key=f"be_detail_{index}",
                                persist_state="session")
    state = st.session_state.get("active_project_state")
    if state:
        if st.session_state.get("last_be_location") != (state.project.project_id, page):
            database().remember_page(state.project.project_id, page)
            st.session_state.last_be_location = (state.project.project_id, page)
        st.sidebar.button("Mở nhật ký nghiên cứu", on_click=go_to_learning_step, args=(PAGES[9],))
        rows, _ = workflow_progress(state.project)
        st.sidebar.caption(f"{stage} · {rows[index]['Trạng thái']}")
    return page


def main():
    st.set_page_config(page_title="Phân tích dược động học và tương đương sinh học", page_icon="🧪", layout="wide")
    st.markdown(
        """
        <style>
        .katex { font-size: 0.95em !important; }
        .katex-display { font-size: 0.88rem !important; overflow-x: auto !important; overflow-y: hidden !important; padding: 4px 2px !important; margin: 0.35rem 0 !important; }
        div[data-testid="stMarkdownContainer"] table { display: block !important; width: 100% !important; overflow-x: auto !important; border-collapse: collapse !important; margin: 0.5rem 0 0.8rem 0 !important; border: 1px solid #e2e8f0 !important; border-radius: 6px !important; background-color: #ffffff !important; font-size: 0.82rem !important; }
        div[data-testid="stMarkdownContainer"] th { background-color: #f1f5f9 !important; color: #0f172a !important; font-weight: 600 !important; border: 1px solid #cbd5e1 !important; padding: 6px 9px !important; text-align: left !important; }
        div[data-testid="stMarkdownContainer"] td { border: 1px solid #e2e8f0 !important; padding: 6px 9px !important; font-size: 0.80rem !important; }
        div[data-testid="stExpander"] { border-radius: 8px !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    initialize_project_state(st.session_state)
    st.session_state.setdefault("project", None)
    st.title("Phân tích dược động học và tương đương sinh học")
    st.caption(f"EMA / FDA · Engine {__version__}")
    workflow = st.sidebar.radio("Luồng phân tích", WORKFLOWS, index=2, key="workflow")
    save_slot = st.sidebar.container()
    upload_slot = st.sidebar.container()
    if workflow == "BE đầy đủ":
        full_project_sidebar_controls(save_slot, upload_slot)
        learning_mode = st.sidebar.toggle(
            "Chế độ học tập — bỏ qua khóa chuyển bước",
            value=False,
            key="full_be_learning_mode",
            help="Cho phép chuyển đến mọi bước để học và xem giao diện khi chưa hoàn tất QC/Data Freeze. "
                 "Các yêu cầu kiểm tra trước tính NCA/BE và phát hành báo cáo vẫn được giữ.",
        )
        page = full_be_navigation()
        if learning_mode:
            st.sidebar.caption("Đang học thử: được chuyển bước dù chưa hoàn tất QC hoặc Data Freeze.")
    elif workflow == "BE nhanh":
        page = PAGES[11]
    else:
        page = PAGES[10]
    state = st.session_state.get("active_project_state")
    previous_page = st.session_state.get("last_page")
    if state and previous_page != page:
        state._bindings.clear()  # Rebuild editor from preserved pending cells on remount.
    st.session_state.last_page = page
    st.toggle("Trợ giúp bên phải", value=True, key="context_help_visible")
    show_help = st.session_state.context_help_visible
    if show_help:
        work_column, help_column = st.columns([3.5, 1.25], gap="medium", wrap=True)
    else:
        work_column, help_column = st.container(), None
    with work_column:
        quick_stage = None
        if workflow == "BE đầy đủ" and state is not None:
            active_idx = PAGES.index(page) if page in PAGES[:10] else 0
            curr_stage = next((i for i, indices in enumerate(STAGE_PAGES) if active_idx in indices), 0)
            rows, _ = workflow_progress(state.project)
            with st.container(border=True):
                st.caption("TIẾN TRÌNH 6 CHẶNG NGHIÊN CỨU BE")
                scols = st.columns(6)
                for s_i, (s_name, sc) in enumerate(zip(STAGE_NAMES, scols)):
                    is_active = (s_i == curr_stage)
                    s_target = PAGES[STAGE_PAGES[s_i][0]]
                    s_label = f"📍 {s_name}" if is_active else f"{s_i + 1}. {s_name}"
                    sc.button(
                        s_label,
                        key=f"stepper_stage_{s_i}",
                        type="primary" if is_active else "secondary",
                        use_container_width=True,
                        help=f"Chặng: {s_name} · {rows[s_i]['Trạng thái']}",
                        on_click=go_to_learning_step,
                        args=(s_target,),
                    )
        st.header(page)
        if workflow == "BE đầy đủ" and learning_mode:
            st.info(
                "Chế độ học tập: có thể xem và chuyển giữa các bước trước khi hoàn tất bước trước. "
                "Các dữ liệu thiếu, QC chưa đạt hoặc chưa Data Freeze vẫn cần xử lý trước khi tính NCA/BE."
            )
            step_index = PAGES[:10].index(page)
            back_column, next_column = st.columns(2)
            with back_column:
                st.button(
                    "← Bước trước", disabled=step_index == 0, key="learning_previous",
                    on_click=go_to_learning_step,
                    args=(PAGES[max(0, step_index - 1)],),
                )
            with next_column:
                st.button(
                    "Bước tiếp theo →", disabled=step_index == 9,
                    key="learning_next", type="primary",
                    on_click=go_to_learning_step,
                    args=(PAGES[min(9, step_index + 1)],),
                )
        if page != "BE nhanh — phân tích độc lập":
            teaching_information()
        if "callback_error" in st.session_state:
            st.error(st.session_state.pop("callback_error"))
        if state:
            st.session_state.project = state.project
            project = state.project
            st.sidebar.caption(
                f"{project.study.study_id} · r{project.input_revision} · {'Đã khóa' if project.freeze_hash else 'Chưa khóa'}"
            )
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([1.5, 1.2, 1.5, 1.2])
                with c1:
                    st.markdown(f"**Nghiên cứu:** `{project.study.study_id}` (r{project.input_revision})")
                    st.caption(project.study.title[:45] + "..." if len(project.study.title) > 45 else project.study.title)
                with c2:
                    if project.freeze_hash:
                        st.markdown("🔒 **Dữ liệu:** `Đã khóa (Data Freeze)`")
                    else:
                        st.markdown("🔓 **Dữ liệu:** `Chưa khóa`")
                    st.caption(f"Hash: `{project.input_fingerprint[:8]}...`")
                with c3:
                    if project.study.is_demo:
                        st.markdown("🧪 **Mục đích:** `Học thử / Giả lập`")
                    elif project.study.data_purpose == "regulated_study":
                        st.markdown("📋 **Mục đích:** `Nghiên cứu thật`")
                    else:
                        st.markdown("🔍 **Mục đích:** `Phát triển PP`")
                with c4:
                    if project.pending_edits:
                        st.markdown(f"⚠️ **Bản nháp:** `{len(project.pending_edits)} mẫu`")
                    else:
                        st.markdown("✅ **Bản nháp:** `Đã đồng bộ`")
                    if st.button("Lưu checkpoint", key="btn_save_checkpoint_top", use_container_width=True):
                        try:
                            state.checkpoint()
                            st.success("Đã lưu checkpoint.")
                        except (ValueError, OSError) as exc:
                            st.error(str(exc))
            if project.study.is_demo:
                st.warning("DỮ LIỆU GIẢ LẬP PHỤC VỤ HỌC THỬ — không dùng kết luận nghiên cứu thật.")
            elif project.study.data_purpose != "regulated_study":
                st.warning("Dữ liệu chưa được xác nhận là nghiên cứu thật; chỉ dùng để phát triển, kiểm thử hoặc đối chiếu.")
            if project.pending_edits:
                st.warning("Chưa áp dụng sửa mẫu: bản nháp đã lưu; cần áp dụng trước phân tích/báo cáo.")
            if st.sidebar.button("Lưu checkpoint dự án"):
                try:
                    state.checkpoint()
                    st.success("Đã lưu dữ liệu chính thức và bản nháp.")
                except (ValueError, OSError) as exc:
                    st.error(str(exc))
        try:
            if page == PAGES[0]:
                overview()
            elif page == "Phân tích PK độc lập":
                independent_pk_page((save_slot, upload_slot))
            elif page == "BE nhanh — phân tích độc lập":
                quick_stage = quick_be_page((save_slot, upload_slot))
            elif state is None:
                if page == PAGES[6]:
                    endpoint_be_panel()
                st.info(
                    "Bạn đang xem trước bước này. Khởi tạo hoặc mở dự án tại Tổng quan để thao tác "
                    "với dữ liệu; bản nháp khởi tạo vẫn được giữ."
                    if workflow == "BE đầy đủ" and learning_mode else
                    "Khởi tạo hoặc mở dự án tại Tổng quan; bản nháp khởi tạo vẫn được giữ."
                )
            else:
                [
                    design_page,
                    randomization_page,
                    import_page,
                    qc_page,
                    nca_page,
                    be_page,
                    plots_page,
                    reports_page,
                    audit_page,
                ][PAGES.index(page) - 1](state)
        except (ValueError, TypeError, KeyError, ArithmeticError, OSError) as exc:
            st.error(f"Chưa thể hoàn tất thao tác: {exc}")
        if workflow == "BE đầy đủ" and not learning_mode:
            page_index = PAGES.index(page)
            if page_index < 9:
                target = PAGES[page_index + 1]
                st.button(f"Tiếp tục · {target}", on_click=go_to_learning_step, args=(target,))
    if help_column is not None:
        with help_column:
            contextual_help(page, st.session_state.get("active_project_state"), quick_stage=quick_stage)
    st.sidebar.caption(software_attribution("vi"))
