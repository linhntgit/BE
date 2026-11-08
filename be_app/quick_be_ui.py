"""One-page, project-free quick bioequivalence review."""

from __future__ import annotations

import hashlib

import pandas as pd
import plotly.express as px
import streamlit as st

from be_app.demo_scenarios import QUICK_CASES, quick_frame
from be_app.domain import NcaConfig, digest
from be_app.field_help import get_field_description, render_table_legend, table_column_config
from be_app.imports import UNITS, parse_file
from be_app.pk_import import workbook_sheets
from be_app.quick_be import (
    IDENTITY,
    PK_ENDPOINTS,
    auto_column_mapping,
    quick_be_workbook,
    run_quick_be,
)
from be_app.regulations import RULES
from be_app.table_editor import render_persistent_editor, validate_structure
from be_app.workflow_project import export_workflow_project, import_workflow_project, validate_project_filename

LABELS = {
    "subject_id": "Subject", "sequence": "Sequence", "period": "Period",
    "treatment": "Treatment", "actual_time_h": "Time (giờ)",
    "concentration": "Cplasma", "blq_flag": "BLQ (tùy chọn)",
    "cmax": "Cmax", "auc_last": "AUClast", "auc_inf": "AUCinf",
    "auc_inf_pred": "AUCinf predicted", "tmax": "Tmax (giờ)",
}
DESIGNS = {"2x2": "Crossover 2×2", "parallel": "Song song",
           "partial3": "Replicate 3 kỳ", "full4": "Replicate 4 kỳ"}


MANUAL_COLUMNS = {
    "Nồng độ theo thời gian": ("Subject", "Sequence", "Period", "Treatment", "Time", "Cplasma", "BLQ"),
    "Thông số PK": ("Subject", "Sequence", "Period", "Treatment", "Cmax", "AUClast", "AUCinf", "Tmax", "AUCinfPred"),
}
LOADED_TABLE = "Bảng đã nạp"


def _nonblank_quick_rows(frame: pd.DataFrame) -> pd.DataFrame:
    """Discard fully empty spreadsheet rows without dropping partly entered records."""
    non_blq_cols = [c for c in frame.columns if str(c).strip().lower() not in {"blq", "blq_flag"}]
    check_frame = frame[non_blq_cols] if non_blq_cols else frame
    populated = check_frame.apply(lambda col: col.map(lambda value: pd.notna(value) and str(value).strip() != ""))
    return frame.loc[populated.any(axis=1)].reset_index(drop=True)


def _load_quick_table(frame: pd.DataFrame) -> None:
    st.session_state.quick_loaded_table = frame.fillna("").astype(str)
    st.session_state.quick_table_generation = st.session_state.get("quick_table_generation", 0) + 1
    st.session_state.quick_table_layout = LOADED_TABLE


def _quick_excel_export(result, identity: str) -> None:
    """Prepare the workbook only when requested, and bind it to the input snapshot."""
    if st.button("Chuẩn bị Excel kết quả BE nhanh", key="quick_prepare_excel"):
        st.session_state["quick_excel_cached"] = (identity, quick_be_workbook(result))
    cached = st.session_state.get("quick_excel_cached")
    if cached is not None and cached[0] == identity:
        st.download_button("Tải Excel kết quả BE nhanh + NCA + nguồn", data=cached[1],
                           file_name="Quick_BE_Review.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           on_click="ignore", key="quick_download")


def quick_be_page(project_controls=None) -> str | None:
    st.info("Phân tích độc lập 3 bước: nhập bảng → xác nhận mapping & thiết kế → chạy BE. "
            "Kết quả là **DRAFT / REVIEW**, chưa được thẩm định và không ghi vào dự án.")
    save_slot, upload_slot = project_controls if project_controls is not None else (st.container(), st.container())
    save_placeholder = save_slot.empty()
    with save_placeholder:
        st.button("Lưu project BE nhanh (.be.zip)", disabled=True,
                  help="Hãy nhập dữ liệu trước khi lưu project.",
                  key="quick_project_save_unavailable", width="stretch")
    with upload_slot:
        st.caption("Upload project BE nhanh (.be.zip)")
        project_upload = st.file_uploader("Chọn project BE nhanh", type=["zip"], key="quick_project_upload")
        if project_upload is not None and st.button("Kiểm tra và mở project", key="quick_project_open"):
            try:
                validate_project_filename(project_upload.name, "quick_be")
                payload = import_workflow_project(project_upload.getvalue(), "quick_be")
                frame = validate_structure(pd.DataFrame(payload["data"]))
                if len(frame.columns) > 200:
                    raise ValueError("Quá nhiều cột dữ liệu.")
                settings = payload["widgets"]
                allowed_exact = {"quick_design", "quick_rule", "quick_mode", "quick_unit",
                                 "quick_integration", "quick_scale", "quick_primary",
                                 "quick_nti_cmax", "quick_scaling", "quick_justification"}
                allowed_prefixes = ("quick_mapping_", "quick_treatment_", "quick_sequence_")
                if not isinstance(settings, dict) or not all(
                    isinstance(key, str) and (key in allowed_exact or key.startswith(allowed_prefixes))
                    and (isinstance(value, (str, bool)) or
                         (key == "quick_primary" and isinstance(value, list) and
                          all(isinstance(item, str) for item in value)))
                    for key, value in settings.items()
                ):
                    raise ValueError("Cấu hình project không hợp lệ.")
                for key, value in settings.items():
                    if key == "quick_design" and value not in DESIGNS:
                        raise ValueError("Thiết kế BE trong project không hợp lệ.")
                    if key == "quick_rule" and value not in RULES:
                        raise ValueError("Quy tắc BE trong project không hợp lệ.")
                    if key == "quick_mode" and value not in ("concentration", "endpoint"):
                        raise ValueError("Kiểu dữ liệu BE không hợp lệ.")
                    if key == "quick_primary" and any(item not in
                        ("auc_last", "cmax", "auc_inf", "auc_inf_pred") for item in value):
                        raise ValueError("Endpoint trong project không hợp lệ.")
                    if key.startswith("quick_mapping_") and value not in ("(không chọn)", *frame.columns):
                        raise ValueError("Mapping tham chiếu đến cột không tồn tại.")
                # Validate the complete upload before changing any live widget state.
                if payload.get("format_version") != 1:
                    raise ValueError("Phiên bản nội dung project chưa hỗ trợ.")
                for key in list(st.session_state):
                    if isinstance(key, str) and (key.startswith("quick_mapping_") or
                            key.startswith("quick_treatment_") or key.startswith("quick_sequence_")):
                        del st.session_state[key]
                st.session_state.update(settings)
                _load_quick_table(frame)
                st.session_state.pop("quick_demo_active", None)
                st.session_state.pop("quick_be_result", None)
                st.session_state.pop("quick_excel_cached", None)
                st.session_state["quick_project_autorun"] = payload.get("analyzed") is True
                st.success("Project hợp lệ. Đã khôi phục dữ liệu và cấu hình.")
                st.rerun()
            except (ValueError, KeyError, TypeError, UnicodeError) as exc:
                st.error(f"Không mở được project: {exc}")
    demo_case = st.selectbox("Học thử · Tình huống BE nhanh", list(QUICK_CASES),
                             format_func=lambda key: QUICK_CASES[key].title, key="quick_demo_case")
    st.caption(QUICK_CASES[demo_case].objective + " " + QUICK_CASES[demo_case].next_step)
    if st.button("Điền dữ liệu mẫu vào bảng BE nhanh", key="quick_demo_load"):
        frame, design, rule = quick_frame(demo_case)
        # These assignments happen before the respective widgets are instantiated.
        for key in list(st.session_state):
            if isinstance(key, str) and key.startswith(("quick_mapping_", "quick_treatment_", "quick_sequence_")):
                del st.session_state[key]
        st.session_state.update({
            "quick_design": design, "quick_rule": rule,
            "quick_mode": "concentration" if demo_case == "concentration" else "endpoint",
        })
        _load_quick_table(frame)
        st.session_state.pop("quick_be_result", None)
        st.session_state["quick_demo_active"] = demo_case
        st.rerun()
    st.markdown("**1. Nhập dữ liệu BE nhanh**")
    generation = st.session_state.get("quick_table_generation", 0)
    upload = st.file_uploader("Tải bảng CSV hoặc XLSX (tùy chọn)", type=["csv", "xlsx"],
                              key=f"quick_upload::{generation}")
    if upload is not None:
        content, name = upload.getvalue(), upload.name
        try:
            sheets = workbook_sheets(content, name)
            sheet = st.selectbox("Sheet dữ liệu", sheets, key="quick_sheet") if len(sheets) > 1 else sheets[0]
            preview = parse_file(content, name, sheet_name=sheet)
        except (ValueError, OSError, KeyError, pd.errors.ParserError, ImportError) as exc:
            st.error(f"Không đọc được dữ liệu: {exc}")
            return
        source_id = hashlib.sha256(content + str(sheet).encode("utf-8")).hexdigest()
        table_id = "quick_be_upload"
    else:
        layouts = list(MANUAL_COLUMNS)
        if "quick_loaded_table" in st.session_state:
            layouts.insert(0, LOADED_TABLE)
        layout = st.radio("Bảng nhập liệu", layouts, horizontal=True, key="quick_table_layout",
                          persist_state="session")
        table_id = f"quick_be_manual::{layout}"
        if layout == LOADED_TABLE:
            preview = st.session_state.quick_loaded_table
            source_id = f"loaded::{generation}"
            if st.session_state.get("quick_demo_active"):
                st.caption("Dữ liệu tổng hợp cho học tập.")
        else:
            preview = st.session_state.get(f"quick_manual_data::{layout}")
            if preview is None:
                if layout == "Nồng độ theo thời gian":
                    preview = pd.DataFrame([
                        {"Subject": "", "Sequence": "", "Period": "", "Treatment": "",
                         "Time": "", "Cplasma": "", "BLQ": False}
                        for _ in range(4)
                    ])
                else:
                    preview = pd.DataFrame("", index=range(4), columns=MANUAL_COLUMNS[layout], dtype="string")
            source_id = layout
        name, sheet = "quick_be_manual.csv", 0
    st.caption("Nhập trực tiếp vào các ô như Excel, hoặc sao chép một vùng ô từ Excel rồi dán vào bảng. "
               "Có thể thêm/xóa dòng. Bấm **Áp dụng chỉnh sửa bảng** trước khi phân tích.")

    def _on_quick_commit(committed_frame: pd.DataFrame) -> None:
        if upload is None and layout != LOADED_TABLE:
            st.session_state[f"quick_manual_data::{layout}"] = committed_frame.copy(deep=True)

    working = render_persistent_editor(
        table_id, preview, source_id,
        validator=lambda frame: validate_structure(_nonblank_quick_rows(frame)).fillna("").astype(str),
        width="stretch",
        on_commit=_on_quick_commit,
    )
    if upload is None and layout != LOADED_TABLE and not working.empty:
        st.session_state[f"quick_manual_data::{layout}"] = working.copy(deep=True)
    if _nonblank_quick_rows(working).empty:
        st.info("Điền dữ liệu vào bảng và bấm **Áp dụng chỉnh sửa bảng**, hoặc chọn dữ liệu mẫu để bắt đầu.")
        return
    if upload is None or not working.equals(preview):
        # The calculation now consumes exactly the committed editor snapshot.
        content = working.to_csv(index=False).encode("utf-8-sig")
        if upload is not None:
            name, sheet = "quick_be_edited.csv", 0
    preview = working
    # Save the committed input and partial choices before the mapping gates below.
    project_widgets = {key: value for key, value in st.session_state.items()
                       if isinstance(key, str) and (key in {
                           "quick_design", "quick_rule", "quick_mode", "quick_unit",
                           "quick_integration", "quick_scale", "quick_primary",
                           "quick_nti_cmax", "quick_scaling", "quick_justification"}
                           or key.startswith(("quick_mapping_", "quick_treatment_", "quick_sequence_")))
                       and isinstance(value, (str, bool, list))}
    saved_result = st.session_state.get("quick_be_result")
    project_payload = {"format_version": 1, "data": preview.to_dict("records"),
                       "widgets": project_widgets, "analyzed": False}
    try:
        with save_placeholder:
            st.download_button("Lưu project BE nhanh (.be.zip)",
                               export_workflow_project("quick_be", project_payload),
                               file_name="BE_nhanh.be.zip", mime="application/zip",
                               on_click="ignore", key="quick_project_download", width="stretch")
    except (ValueError, TypeError) as exc:
        st.warning(f"Chưa xuất được project: {exc}")
    auto = auto_column_mapping(preview.columns)
    st.markdown("**2. Xác nhận ý nghĩa cột và thiết kế**")
    values = ["(không chọn)", *list(preview.columns)]
    mapping = {}
    used_sources = []
    items = list(LABELS)

    with st.container(border=True):
        st.markdown("##### 📌 Cột định danh bắt buộc")
        st.caption("Cần thiết để phân biệt người tình nguyện (Subject), trình tự (Sequence), kỳ (Period) và thuốc (Treatment).")
        id_cols = st.columns(4)
        for col, target in zip(id_cols, IDENTITY, strict=True):
            suggested = next((name for name, dest in auto.items() if dest == target), None)
            with col:
                selected = st.selectbox(LABELS[target], values, index=values.index(suggested) if suggested else 0,
                                        key=f"quick_mapping_{target}", help=get_field_description(target))
            if selected != "(không chọn)":
                used_sources.append(selected)
                mapping[selected] = target

    other_items = [k for k in items if k not in IDENTITY]
    with st.container(border=True):
        st.markdown("##### 📊 Cột dữ liệu nồng độ & thông số PK")
        st.caption("Ánh xạ cột Cplasma và Time (nếu tính NCA) hoặc các thông số Cmax, AUClast, AUCinf có sẵn.")
        for start in range(0, len(other_items), 4):
            chunk = other_items[start : start + 4]
            columns = st.columns(len(chunk))
            for col, target in zip(columns, chunk, strict=True):
                suggested = next((name for name, dest in auto.items() if dest == target), None)
                with col:
                    selected = st.selectbox(LABELS[target], values, index=values.index(suggested) if suggested else 0,
                                            key=f"quick_mapping_{target}", help=get_field_description(target))
                if selected != "(không chọn)":
                    used_sources.append(selected)
                    mapping[selected] = target
    if len(used_sources) != len(set(used_sources)):
        st.error("Một cột nguồn đang được chọn cho nhiều trường; hãy ánh xạ mỗi cột một lần.")
        return "mapping"
    reverse = {target: src for src, target in mapping.items()}
    if not set(IDENTITY) <= set(reverse):
        st.warning("Cần mapping đủ Subject, Sequence, Period, Treatment.")
        return "mapping"
    if len(set(mapping.values())) != len(mapping):
        st.error("Một đích được chọn từ nhiều cột.")
        return "mapping"
    possible_modes = []
    if "concentration" in reverse:
        possible_modes.append("concentration")
    if set(PK_ENDPOINTS) & set(reverse):
        possible_modes.append("endpoint")
    if not possible_modes:
        st.warning("Cần Cplasma hoặc ít nhất một endpoint PK.")
        return "mapping"
    names = {"concentration": "Nồng độ theo Time → NCA → BE", "endpoint": "Cmax / AUC đã tính → BE"}
    mode = st.radio("Kiểu dữ liệu", possible_modes, format_func=names.get, horizontal=True, key="quick_mode", help="Chọn dạng dữ liệu đầu vào: Nồng độ theo thời gian (để tính NCA rồi BE) hoặc Thông số Cmax/AUC đã tính sẵn.")
    if mode == "concentration" and "actual_time_h" not in reverse:
        st.error("Dữ liệu Cplasma cần cột Time để tính AUClast; không suy diễn từ thứ tự dòng.")
        return "time"
    design = st.selectbox("Thiết kế", list(DESIGNS), format_func=lambda key: DESIGNS[key], key="quick_design", help="Cấu trúc thiết kế thử nghiệm: Crossover 2×2, Song song (Parallel) hoặc Replicate 3/4 kỳ.")
    choices = [key for key, rule in RULES.items() if design in rule.designs and rule.supported]
    rule_id = st.selectbox("Quy tắc BE", choices, key="quick_rule", help="Quy chế pháp lý áp dụng (ICH M13A, US FDA, EMA, ASEAN, NTI, HVD RSABE/ABEL).")
    try:
        original_treatments = sorted(preview[reverse["treatment"]].astype(str).str.strip().unique())
        original_sequences = sorted(preview[reverse["sequence"]].astype(str).str.strip().unique())
    except KeyError as exc:
        st.error(f"Thiếu cột: {exc}")
        return
    sequences = {"2x2": ["TR", "RT"], "parallel": ["T", "R"],
                 "partial3": ["TRR", "RTR", "RRT"], "full4": ["TRTR", "RTRT"]}[design]
    treatment_mapping = {}
    sequence_mapping = {}
    with st.expander("Xác nhận nhãn Treatment / Sequence", expanded=True):
        left, right = st.columns(2)
        with left:
            for label in original_treatments:
                candidates = ["(chọn)", "T", "R"]
                selected = st.selectbox(f"Treatment nguồn: {label}", candidates,
                                        index=candidates.index(label) if label in {"T", "R"} else 0,
                                        key=f"quick_treatment_{label}")
                if selected != "(chọn)":
                    treatment_mapping[label] = selected
        with right:
            for label in original_sequences:
                candidates = ["(chọn)", *sequences]
                selected = st.selectbox(f"Sequence nguồn: {label}", candidates,
                                        index=candidates.index(label) if label in sequences else 0,
                                        key=f"quick_sequence_{label}")
                if selected != "(chọn)":
                    sequence_mapping[label] = selected
    if len(treatment_mapping) != len(original_treatments) or len(sequence_mapping) != len(original_sequences):
        st.warning("Cần xác nhận rõ mọi nhãn Treatment và Sequence trước phân tích.")
        return "labels"
    nca_config = NcaConfig()
    unit, endpoint_scale = "ng/mL", "raw"
    if mode == "concentration":
        unit = st.selectbox("Đơn vị Cplasma (giờ dùng cho Time)", list(UNITS), key="quick_unit", help="Đơn vị nồng độ chuẩn hóa của dữ liệu đầu vào (ví dụ ng/mL).")
        with st.expander("Tùy chọn NCA", expanded=False):
            integration = st.selectbox("Tính diện tích AUC", ["linear_up_log_down", "linear"],
                                       key="quick_integration", help="Thuật toán tích phân diện tích dưới đường cong: linear_up_log_down (chuẩn NCA) hoặc linear.")
            nca_config = NcaConfig.model_validate({"integration": integration})
            st.caption("Giữ nguyên mốc Time=0; BLQ chỉ xử lý khi có cờ BLQ rõ ràng. "
                       "Chất lượng pha cuối được đánh giá theo cấu hình NCA mặc định.")
    else:
        endpoint_scale = st.selectbox("Dữ liệu PK hiện ở thang đo", ["raw", "ln", "log10"],
                                      key="quick_scale", help="Thang đo thực tế của dữ liệu PK nhập vào (cần khai báo đúng để biến đổi log tự nhiên).")
    primary = tuple(st.multiselect("Endpoint chính để đánh giá tổng thể", ["auc_last", "cmax", "auc_inf", "auc_inf_pred"],
                                   default=["auc_last", "cmax"], key="quick_primary", help="Các chỉ tiêu dược động học cốt lõi quyết định kết luận tương đương sinh học chung."))
    nti = rule_id in {"EMA_NTI", "FDA_NTI"}
    nti_cmax_narrow = st.checkbox("Thu hẹp Cmax theo chỉ định NTI (EMA)", key="quick_nti_cmax", help="Áp dụng khoảng hẹp 90,00–111,11% cho cả Cmax theo quy định NTI của EMA.") if rule_id == "EMA_NTI" else False
    scaled = False
    justification = ""
    if rule_id in {"EMA_HVDP_ABEL", "FDA_HVD_RSABE_2026"}:
        scaled = st.checkbox("Scaling đã được định trước trong SAP", key="quick_scaling", help="Xác nhận phương pháp co giãn giới hạn BE (RSABE/ABEL) đã được quy định trước trong đề cương/SAP.")
        justification = st.text_input("Căn cứ biến thiên và ý nghĩa lâm sàng", key="quick_justification", help="Giải trình căn cứ khoa học về độ biến thiên cao (sWR ≥ 0,294) và an toàn lâm sàng.")

    kwargs = dict(sheet=sheet, column_mapping=mapping, mode=mode, design=design, rule_id=rule_id,
                  treatment_mapping=treatment_mapping, sequence_mapping=sequence_mapping,
                  concentration_unit=unit, endpoint_scale=endpoint_scale,
                  primary_endpoints=primary, nca_config=nca_config, nti=nti,
                  nti_cmax_narrow=nti_cmax_narrow, scaled_be_prespecified=scaled,
                  hvd_justification=justification)
    # Source bytes and all calculation choices must match the displayed snapshot.
    identity = digest({"source": hashlib.sha256(content).hexdigest(), "name": name,
                       "kwargs": {key: (value.model_dump(mode="json") if hasattr(value, "model_dump") else value)
                                  for key, value in kwargs.items()}})
    if st.button("3. Chạy phân tích BE nhanh", type="primary", key="quick_run") or st.session_state.pop(
        "quick_project_autorun", False
    ):
        try:
            outcome = run_quick_be(content, name, **kwargs)
            st.session_state["quick_be_result"] = (identity, outcome)
        except (ValueError, TypeError, KeyError, ArithmeticError) as exc:
            st.session_state.pop("quick_be_result", None)
            st.error(f"Không thể phân tích: {exc}")
    saved = st.session_state.get("quick_be_result")
    if not saved:
        return mode
    if saved[0] != identity:
        st.warning("Dữ liệu hoặc cấu hình đã đổi. Chạy lại để cập nhật kết quả và xuất file.")
        return "stale"
    result = saved[1]
    st.subheader("Kết quả BE nhanh · DRAFT / cần rà soát")
    with st.container(border=True):
        col_verdict, col_meta = st.columns([2.5, 1.5])
        with col_verdict:
            if result.overall_status == "NOT EVALUABLE":
                st.error("Đánh giá tổng thể: NOT EVALUABLE — thiếu dữ liệu hoặc điều kiện phân tích.")
            elif result.overall_status == "FAIL":
                st.warning("Đánh giá các endpoint chính: FAIL (kết quả phát triển, cần rà soát).")
            else:
                st.success("Các endpoint chính: PASS theo cấu hình hiện tại (DRAFT, chưa thẩm định).")
        with col_meta:
            st.caption(f"**Quy tắc:** {RULES[rule_id].jurisdiction} ({rule_id})")
            st.caption(f"**Thiết kế:** {DESIGNS[design]}")
            st.caption(f"**Mã băm nguồn:** `{result.provenance['source_sha256'][:12]}...`")

    if result.results:
        m_cols = st.columns(min(3, len(result.results)))
        for col, r in zip(m_cols, result.results[:3]):
            with col:
                with st.container(border=True):
                    gmr_txt = f"{100 * r.gmr:.2f}%" if r.gmr is not None else "—"
                    ci_txt = f"[{100 * r.ci_lower:.2f}% – {100 * r.ci_upper:.2f}%]" if r.ci_lower is not None else "—"
                    cv_txt = f"{100 * r.cv_within:.2f}%" if r.cv_within is not None else "—"
                    st.metric(label=f"Endpoint: {r.endpoint}", value=gmr_txt, delta=f"90% CI: {ci_txt}", delta_color="off")
                    st.caption(f"Quyết định: **{r.decision}** | $CV_{{intra}}$: {cv_txt}")
    rows = [{"Endpoint": r.endpoint, "GMR (%)": 100 * r.gmr if r.gmr is not None else None,
             "CI90 thấp (%)": 100 * r.ci_lower if r.ci_lower is not None else None,
             "CI90 cao (%)": 100 * r.ci_upper if r.ci_upper is not None else None,
             "CV nội (%)": 100 * r.cv_within if r.cv_within is not None else None,
             "N": r.n, "Quyết định": r.decision, "Lý do": r.reason} for r in result.results]
    cols = list(rows[0].keys()) if rows else []
    st.dataframe(pd.DataFrame(rows), hide_index=True, column_config=table_column_config(cols))
    render_table_legend(cols, title="ℹ️ Chú thích tiêu đề cột & thuật ngữ bảng BE nhanh")
    st.markdown("**So sánh Tmax phi tham số (phân tích hỗ trợ)**")
    tmax = result.tmax
    if tmax.n_t or tmax.n_r:
        tmax_cols = ["Nhóm", "N", "Trung vị (giờ)", "Nhỏ nhất (giờ)", "Lớn nhất (giờ)"]
        st.dataframe(pd.DataFrame([
            {"Nhóm": "T", "N": tmax.n_t, "Trung vị (giờ)": tmax.median_t,
             "Nhỏ nhất (giờ)": tmax.min_t, "Lớn nhất (giờ)": tmax.max_t},
            {"Nhóm": "R", "N": tmax.n_r, "Trung vị (giờ)": tmax.median_r,
             "Nhỏ nhất (giờ)": tmax.min_r, "Lớn nhất (giờ)": tmax.max_r},
        ]), hide_index=True, column_config=table_column_config(tmax_cols), alt="Thống kê Tmax theo nhóm T và R")
        render_table_legend(tmax_cols, title="ℹ️ Chú thích tiêu đề cột bảng so sánh Tmax")
    if tmax.status == "EVALUABLE":
        st.write(f"{tmax.method} · thống kê = {tmax.statistic:.4g} · "
                 f"p hai phía = {tmax.p_value:.4g}"
                 + (f" · {tmax.n_pairs} cặp · trung vị (T−R) = "
                    f"{tmax.median_paired_difference:.4g} giờ" if tmax.n_pairs is not None else ""))
    else:
        st.info(f"Tmax: NOT EVALUABLE — {tmax.reason}")
    st.caption(tmax.note)
    if result.warnings:
        with st.expander(f"Cảnh báo / profile cần rà soát ({len(result.warnings)})", expanded=True):
            st.dataframe(pd.DataFrame({"Cảnh báo": result.warnings}), hide_index=True)
    if not result.nca.empty:
        with st.expander("Kết quả NCA theo Subject/Period", expanded=True):
            nca_columns = [c for c in ("subject_id", "sequence", "period", "treatment", "status", "reason",
                                    "cmax", "tmax", "auc_last", "auc_inf", "half_life", "auc_extrap_pct")
                       if c in result.nca]
            st.dataframe(result.nca[nca_columns], hide_index=True, column_config=table_column_config(nca_columns))
            render_table_legend(nca_columns, title="ℹ️ Chú thích thông số bảng NCA")
    if result.concentrations is not None:
        with st.expander("Đường cong nồng độ–thời gian"):
            display = result.concentrations.copy()
            display["Profile"] = display.subject_id + " / kỳ " + display.period.astype(str)
            fig = px.line(display.sort_values("actual_time_h"), x="actual_time_h", y="concentration",
                          color="treatment",
                          color_discrete_map={"T": "#1f77b4", "R": "#d62728"},
                          line_group="Profile", markers=True,
                          hover_data=["subject_id", "period", "sequence"],
                          labels={"actual_time_h": "Thời gian (giờ)", "concentration": f"Cplasma ({unit})", "treatment": "Thuốc"})
            fig.update_layout(template="plotly_white", legend_title_text="Thuốc")
            st.plotly_chart(fig, width="stretch")
    with st.expander("Chi tiết thống kê / ANOVA / đánh giá tiêu chí"):
        from be_app.ui import show_be_results  # Delay UI import to avoid a circular import.

        show_be_results(result.results, key=result.provenance["settings_sha256"],
                        data=result.endpoints, design=design)
    st.caption("SHA256 dữ liệu: " + result.provenance["source_sha256"] +
               " · Quy tắc: " + rule_id + " · Engine phát triển, chưa qualified.")
    _quick_excel_export(result, identity)
    return "results"
