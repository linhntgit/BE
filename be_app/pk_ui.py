"""Vietnamese Streamlit workbench for independent concentration-time PK data."""

from __future__ import annotations

import hashlib
import io
import json
from dataclasses import asdict
from typing import Literal, cast

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from be_app.field_help import render_table_legend, table_column_config
from be_app.pk_analysis import (
    CONCENTRATION_FACTORS,
    DOSE_FACTORS,
    PKSettings,
    Route,
    analyze_nca,
    read_concentrations,
    validate_profiles,
)
from be_app.pk_import import workbook_sheets
from be_app.pk_models import fit_compartment, predict
from be_app.pk_multiple import PKRegimen, analyze_interval_nca, predict_multiple
from be_app.pk_records import (
    _display_nca,
    create_snapshot,
    excel_report,
    pdf_report,
    record_bytes,
    snapshot_digest,
    word_report,
)
from be_app.table_editor import render_persistent_editor
from be_app.workflow_project import export_workflow_project, import_workflow_project, validate_project_filename


def _read_file(content: bytes, filename: str, sheet: str | int) -> pd.DataFrame:
    if len(content) > 25_000_000:
        raise ValueError("File vượt giới hạn 25 MB.")
    if filename.lower().endswith(".csv"):
        return pd.read_csv(io.BytesIO(content), encoding="utf-8-sig", sep=None, engine="python")
    return pd.read_excel(io.BytesIO(content), sheet_name=sheet, engine="openpyxl")


def _fingerprint(data: pd.DataFrame, config: PKSettings, modes: tuple[int, ...],
                 weighting: str, regimen: PKRegimen | None = None, source: str = "") -> str:
    # Native Python float JSON serialization preserves 17-digit binary64 precision.
    text = json.dumps({"data": data.to_dict(orient="records"), "settings": asdict(config),
                       "modes": modes, "weighting": weighting,
                       "regimen": asdict(regimen) if regimen else None,
                       "source": source}, ensure_ascii=False, sort_keys=True, allow_nan=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _demo_csv() -> bytes:
    times = np.array([0, .25, .5, 1, 1.5, 2, 3, 4, 6, 8, 12, 16, 24])
    ka, k = 1.2, .2
    conc = 100_000_000 / (50 * 1000) * ka / (ka-k) * (np.exp(-k*times) - np.exp(-ka*times))
    return pd.DataFrame({"profile": "MÔ PHỎNG_PK01", "time_h": times,
                         "Cplasma_ng_mL": np.round(conc, 5)}).to_csv(index=False).encode("utf-8-sig")


def _demo_multiple_csv() -> bytes:
    """Synthetic oral concentrations across the final 12-hour interval after 10 doses."""
    settings = PKSettings(route="oral", dose=100.0)
    regimen = PKRegimen(mode="steady_state", tau_h=12.0, number_doses=10)
    times = np.linspace(0, 12, 49)
    values = predict_multiple(regimen.absolute_times(times),
                              {"CL/F": 5.0, "V/F": 20.0, "ka": 1.2}, settings, 1, regimen)
    return pd.DataFrame({"profile": "MÔ PHỎNG_MD01", "time_h": times,
                         "Cplasma_ng_mL": np.round(values, 5)}).to_csv(index=False).encode("utf-8-sig")


def _parse_input() -> tuple[pd.DataFrame, str]:
    upload = st.file_uploader("Bảng nồng độ Cplasma (CSV hoặc XLSX)", type=["csv", "xlsx"],
                              key=f"standalone_pk_file::{st.session_state.get('pk_upload_generation', 0)}")
    if upload is None:
        st.caption("Có thể nhập thủ công trong bảng bên dưới, hoặc tải tệp CSV/XLSX.")
        initial = st.session_state.get("pk_manual_data")
        if initial is None:
            initial = pd.DataFrame([{"profile_id": "PK01", "time_h": 0.0,
                                     "concentration": 0.0, "blq": False}])
        source_id = f"manual::{st.session_state.get('pk_manual_generation', 0)}"
        source = st.session_state.get("pk_restored_source", "Nhập trực tiếp")
    else:
        content = upload.getvalue()
        workbook = workbook_sheets(content, upload.name)
        sheet = st.selectbox("Trang tính Excel", workbook, key="pk_sheet") if len(workbook) > 1 else workbook[0]
        raw = _read_file(content, upload.name, sheet)
        if raw.empty:
            raise ValueError("Tệp không có dữ liệu.")
        cols = list(raw.columns)
        st.dataframe(raw.head(20), hide_index=True)
        layout = st.radio("Cấu trúc dữ liệu", ["long", "wide"], horizontal=True,
                          format_func=lambda x: "Long — mỗi dòng một mẫu" if x == "long"
                          else "Wide — mỗi cột một hồ sơ", key="pk_layout")
        time_col = st.selectbox("Cột thời gian (giờ)", cols, index=next(
            (i for i, c in enumerate(cols) if "time" in str(c).lower() or "giờ" in str(c).lower()), 0))
        if layout == "long":
            conc_col = st.selectbox("Cột nồng độ Cplasma", cols, index=next(
                (i for i, c in enumerate(cols) if "conc" in str(c).lower() or "cplasma" in str(c).lower()),
                min(1, len(cols)-1)))
            profile_col = st.selectbox("Cột mã hồ sơ", ["(một hồ sơ)", *cols], index=next(
                (i+1 for i, c in enumerate(cols) if "profile" in str(c).lower()
                 or "subject" in str(c).lower()), 0))
            blq_options = ["(không có)", *cols]
            blq_col = st.selectbox("Cột cờ BLQ (tùy chọn)", blq_options,
                                   index=next((i + 1 for i, c in enumerate(cols)
                                               if str(c).strip().casefold() in {"blq", "blq_flag"}), 0))
            initial = read_concentrations(raw, layout=layout, time_column=time_col,
                                          concentration_column=conc_col,
                                          profile_column=None if profile_col == "(một hồ sơ)" else profile_col,
                                          blq_column=None if blq_col == "(không có)" else blq_col)
        else:
            initial = read_concentrations(raw, layout=layout, time_column=time_col)
        mapping_hash = hashlib.sha256((hashlib.sha256(content).hexdigest() + str(sheet) + layout + time_col +
                                       str(locals().get("conc_col")) + str(locals().get("profile_col")) +
                                       str(locals().get("blq_col"))).encode()).hexdigest()[:16]
        source_id = "upload_" + mapping_hash
        source = f"{upload.name} · {sheet} · SHA256 {hashlib.sha256(content).hexdigest()}"
    st.caption("BLQ: nhập BLQ, <LLOQ hoặc chọn cờ BLQ. Giá trị trống và thời điểm trùng sẽ bị chặn.")
    st.caption("Nhập hoặc dán nhiều ô, thêm/xóa dòng rồi bấm **Áp dụng chỉnh sửa bảng** trước khi phân tích.")
    def _on_manual_pk_commit(committed_frame: pd.DataFrame) -> None:
        if upload is None:
            st.session_state["pk_manual_data"] = committed_frame.copy(deep=True)

    editor = render_persistent_editor("pk_concentrations", initial, source_id,
                            validator=validate_profiles, width="stretch", column_config={
                                "profile_id": st.column_config.TextColumn("Mã hồ sơ"),
                                "time_h": st.column_config.NumberColumn("Thời gian (giờ)"),
                                "concentration": st.column_config.NumberColumn("Cplasma"),
                                "blq": st.column_config.CheckboxColumn("BLQ", default=False, required=True),
                            },
                            on_commit=_on_manual_pk_commit)
    if upload is None and editor is not None and not editor.empty:
        st.session_state["pk_manual_data"] = editor.copy(deep=True)
    return editor, source


def _settings() -> tuple[PKSettings, tuple[int, ...], str, bool, PKRegimen | None]:
    st.subheader("Thiết lập đường dùng và phân tích")
    dose_mode = st.radio("Chế độ dùng thuốc", ["single", "multiple", "steady_state"],
                         format_func=lambda v: {"single": "Đơn liều", "multiple": "Đa liều",
                                                "steady_state": "Trạng thái ổn định (steady-state)"}[v],
                         horizontal=True, key="pk_dose_mode", help="Chế độ đưa thuốc: Đơn liều, Đa liều hoặc Trạng thái ổn định (steady-state).")
    regimen = None
    if dose_mode != "single":
        st.caption("Lịch dùng liều bằng nhau, cách đều τ; tính từ liều đầu tại t=0. "
                   "Cần khai báo số liều đã thực dùng. Không hỗ trợ thay đổi liều hoặc lịch không đều.")
        r1, r2 = st.columns(2)
        with r1:
            tau = st.number_input("Khoảng cách giữa hai liều τ (giờ)", min_value=0.001,
                                  value=12.0, step=1.0, key="pk_tau", help="Khoảng thời gian dùng thuốc lặp lại (Dosing interval, tau) trong phác đồ đa liều.")
            time_basis = st.radio("Mốc thời gian của bảng Cplasma",
                                  ["last_dose", "first_dose"],
                                  format_func=lambda v: "Giờ sau liều cuối (0 đến τ)" if v == "last_dose"
                                  else "Giờ từ liều đầu (toàn lịch)", key="pk_time_basis")
        with r2:
            number_doses = st.number_input("Tổng số liều đã dùng", min_value=2, max_value=1000,
                                           value=5, step=1, key="pk_number_doses", help="Tổng số lần đưa thuốc thực tế trước thời điểm lấy mẫu đánh giá dược động học.")
            confirmed = st.checkbox("Tôi đã xác nhận đạt trạng thái ổn định bằng bằng chứng phù hợp",
                                    value=False, key="pk_ss_confirm") if dose_mode == "steady_state" else False
        regimen = PKRegimen(mode=cast(Literal["multiple", "steady_state"], dose_mode),
                            tau_h=float(tau), number_doses=int(number_doses),
                            time_basis=cast(Literal["first_dose", "last_dose"], time_basis),
                            steady_state_confirmed=bool(confirmed))
        st.info("NCA sử dụng khoảng liều cuối [0, τ]. AUCτ cần đủ mẫu tại cả hai biên, "
                "không có BLQ trong chu kỳ. CLss chỉ tính khi xác nhận steady-state và biết liều.")
    route_labels = {"oral": "Uống (oral)", "iv_bolus": "Tiêm tĩnh mạch nhanh (IV bolus)",
                    "iv_infusion": "Truyền tĩnh mạch (IV infusion)"}
    route = cast(Route, st.selectbox("Đường dùng", ["oral", "iv_bolus", "iv_infusion"],
                                    format_func=lambda v: route_labels[str(v)], key="pk_route", help="Đường dùng thuốc: Uống (Oral), Tiêm tĩnh mạch nhanh (IV bolus) hoặc Truyền tĩnh mạch (IV infusion)."))
    left, mid, right = st.columns(3)
    with left:
        concentration_unit = st.selectbox("Đơn vị nồng độ đầu vào", list(CONCENTRATION_FACTORS), key="pk_concentration_unit")
    with mid:
        has_dose = st.checkbox("Có thông tin liều mỗi lần" if regimen is not None
                               else "Có thông tin liều dùng", value=regimen is not None, key="pk_has_dose")
        dose = st.number_input("Liều đã dùng", min_value=0.000001, value=100.0,
                               step=1.0, disabled=not has_dose,
                               help="Liều mỗi lần dùng" if regimen is not None else "Liều đơn",
                               key="pk_dose") if has_dose else None
    with right:
        dose_unit = st.selectbox("Đơn vị liều", list(DOSE_FACTORS), index=2, key="pk_dose_unit")
    infusion = st.number_input("Thời gian truyền (giờ)", min_value=0.000001, value=1.0,
                               step=.25, key="pk_infusion") if route == "iv_infusion" else None
    zero_options = ["measured_only"]
    if regimen is None:
        if route == "iv_bolus":
            zero_options.append("extrapolate_iv")
        else:
            zero_options.append("assume_zero")
    zero_labels = {"measured_only": "Giữ nguyên dữ liệu; không ước lượng C0",
                   "extrapolate_iv": "Ngoại suy C0 từ 3 mẫu dương sớm (IV bolus)",
                   "assume_zero": "Giả định C(0)=0 (được ghi rõ trong kết quả)"}
    zero_policy = cast(str, st.selectbox("Xử lý khi không có quan sát t=0", zero_options,
                                         format_func=lambda v: zero_labels[str(v)], key="pk_zero_policy", help="Quy ước xử lý nồng độ tại thời điểm t=0 khi mẫu thực tế không có điểm đo trước liều."))
    integration_labels = {"linear_up_log_down": "Tuyến tính tăng – log giảm",
                          "linear": "Hình thang tuyến tính"}
    integration = cast(str, st.selectbox("Quy tắc tích phân NCA", ["linear_up_log_down", "linear"],
                                          format_func=lambda v: integration_labels[str(v)], key="pk_integration", help="Thuật toán tích phân diện tích dưới đường cong: linear_up_log_down (chuẩn NCA) hoặc linear."))
    c1, c2 = st.columns(2)
    with c1:
        terminal_points = st.number_input("Số điểm tối thiểu pha cuối", min_value=3, max_value=10, value=3,
                                          key="pk_terminal_points", help="Số lượng điểm nồng độ tối thiểu ở pha thải trừ cuối tham gia hồi quy ước tính λz (≥ 3).")
    with c2:
        terminal_r2 = st.slider("Adjusted R² tối thiểu pha cuối", min_value=0.0,
                                max_value=1.0, value=0.8, step=.05, key="pk_terminal_r2", help="Ngưỡng hệ số xác định hiệu chỉnh (Adjusted R²) tối thiểu để chấp nhận pha đào thải cuối λz.")
    modes = st.multiselect("Phương pháp", ["NCA", "1 ngăn", "2 ngăn", "3 ngăn"], default=["NCA", "1 ngăn"],
                           key="pk_methods", help="Phân tích phi ngăn (NCA) hoặc khớp mô hình 1, 2, 3 ngăn. Mô hình 3 ngăn cần mẫu trải đủ ba pha và có thể không định danh được nếu dữ liệu quá thưa.")
    weight_labels = {"equal": "Không trọng số", "1/C": "1/C", "1/C²": "1/C²"}
    weighting = cast(str, st.selectbox("Trọng số khớp mô hình", ["equal", "1/C", "1/C²"],
                                      format_func=lambda v: weight_labels[str(v)], key="pk_weighting", help="Sơ đồ gán trọng số sai số khi khớp phi tuyến: Không trọng số (equal), 1/C hoặc 1/C²."))
    config = PKSettings(route=route, dose=float(dose) if dose is not None else None,
                        dose_unit=dose_unit, concentration_unit=concentration_unit,
                        infusion_duration_h=float(infusion) if infusion is not None else None,
                        integration=cast(Literal["linear", "linear_up_log_down"], integration),
                        zero_policy=cast(Literal["measured_only", "assume_zero", "extrapolate_iv"], zero_policy),
                        terminal_min_points=int(terminal_points), terminal_min_adj_r2=terminal_r2)
    if regimen is not None and dose is None:
        st.info("Chưa khai báo liều: vẫn có thể tính NCA trong khoảng liều, "
                "nhưng không thể tính CLss/CL/Fss hoặc khớp mô hình ngăn.")
    return config, tuple(n for n in (1, 2, 3) if f"{n} ngăn" in modes), weighting, "NCA" in modes, regimen


def _tabular(snapshot: dict) -> None:
    st.subheader("Kết quả NCA")
    if snapshot["nca"]:
        df_nca = _display_nca(snapshot)
        st.dataframe(df_nca, hide_index=True, width="stretch", column_config=table_column_config(df_nca.columns))
        render_table_legend(df_nca.columns, title="ℹ️ Chú thích thông số bảng NCA")
    else:
        st.caption("Không chọn NCA.")
    st.subheader("Thông số mô hình ngăn")
    if snapshot["models"]:
        rows = []
        for model in snapshot["models"]:
            rows.append({"Hồ sơ": model["profile_id"], "Số ngăn": model["compartments"],
                         "Trọng số": "Không trọng số" if model["weighting"] == "equal"
                         else model["weighting"], "RMSE (ng/mL)": model["rmse_ng_ml"],
                         "AICc": model["aicc"], "BIC": model["bic"],
                         "Điều kiện Jacobian": model["jacobian_condition"], **model["parameters"],
                         **model.get("derived_parameters", {})})
        df_models = pd.DataFrame(rows)
        st.dataframe(df_models, hide_index=True, width="stretch", column_config=table_column_config(df_models.columns))
        render_table_legend(df_models.columns, title="ℹ️ Chú thích tiêu đề cột & tiêu chí mô hình PK")
        st.caption("So sánh AICc chỉ trong cùng hồ sơ, tập mẫu và cách trọng số. "
                   "Với trọng số 1/C, 1/C² các tiêu chí thông tin chỉ mang tính gợi ý.")
    else:
        st.caption("Không có mô hình khớp thành công.")
    if snapshot["errors"]:
        for message in snapshot["errors"]:
            st.warning(message)
    for result in snapshot["nca"]:
        for message in result["warnings"]:
            st.caption(f"⚠️ {result['profile_id']}: {message}")
    for model in snapshot["models"]:
        for message in model["warnings"]:
            st.caption(f"⚠️ {model['profile_id']} ({model['compartments']} ngăn): {message}")


def _plot(snapshot: dict, key: str) -> None:
    data = pd.DataFrame(snapshot["data"])
    selected = st.selectbox("Hồ sơ để xem đồ thị", sorted(data.profile_id.unique()), key=f"{key}_profile")
    sub = data.loc[data.profile_id == selected].sort_values("time_h")
    factor = CONCENTRATION_FACTORS[snapshot["settings"]["concentration_unit"]]
    t = sub.time_h.to_numpy(dtype=float)
    c = sub.concentration.to_numpy(dtype=float) * factor
    models = [m for m in snapshot["models"] if m["profile_id"] == selected]
    regimen = PKRegimen(**snapshot["regimen"]) if snapshot.get("regimen") else None
    plot_tabs = st.tabs(["Nồng độ tuyến tính", "Nồng độ bán log", "Phần dư"])
    for index, tab in enumerate(plot_tabs):
        with tab:
            fig = go.Figure()
            if index < 2:
                plotted = c > 0 if index == 1 else np.ones(len(c), dtype=bool)
                fig.add_trace(go.Scatter(x=t[plotted], y=c[plotted], mode="markers+lines",
                                         name="Quan sát", marker={"size": 8}))
                curve_t = np.linspace(0, max(float(t.max()), .001), 240)
                for model in models:
                    settings = PKSettings(**snapshot["settings"])
                    predicted = (predict(curve_t, model["parameters"], settings, model["compartments"])
                                 if regimen is None else predict_multiple(
                                     regimen.absolute_times(curve_t), model["parameters"],
                                     settings, model["compartments"], regimen))
                    valid = predicted > 0 if index == 1 else np.ones(len(predicted), dtype=bool)
                    fig.add_trace(go.Scatter(x=curve_t[valid], y=predicted[valid],
                                             name=f"Dự đoán {model['compartments']} ngăn", mode="lines"))
                fig.update_yaxes(title="Nồng độ (ng/mL)", type="log" if index == 1 else "linear")
                if regimen is not None and regimen.number_doses <= 30:
                    lines = ([float(i) * regimen.tau_h for i in range(regimen.number_doses)]
                             if regimen.time_basis == "first_dose" else [0.0])
                    for point in lines:
                        if point <= float(t.max()):
                            fig.add_vline(x=point, line_dash="dot", line_color="gray", opacity=.4)
            else:
                for model in models:
                    fig.add_trace(go.Scatter(x=model["time_h"], y=model["residuals"], mode="markers",
                                             name=f"Phần dư {model['compartments']} ngăn"))
                fig.add_hline(y=0, line_dash="dash")
                fig.update_yaxes(title="Quan sát − dự đoán (ng/mL)")
                if not models:
                    st.info("Cần khớp mô hình ngăn để xem phần dư.")
            fig.update_layout(xaxis_title="Thời gian (giờ)", legend_title="Chú giải",
                              margin=dict(l=8, r=8, t=12, b=8))
            st.plotly_chart(fig, width="stretch", key=f"{key}_plot_{index}")


@st.cache_data(show_spinner=False, max_entries=12, ttl=3600)
def _export(raw: bytes, kind: str) -> bytes:
    snapshot = json.loads(raw)
    exporters = {"excel": excel_report, "word": word_report, "pdf": pdf_report}
    return exporters[kind](snapshot)


def _render_snapshot(snapshot: dict, key: str) -> None:
    st.caption(f"Nguồn: {snapshot['source']} · UTC: {snapshot['created_utc']}")
    st.caption(f"SHA-256 bản ghi: {snapshot_digest(snapshot)}")
    table_tab, plot_tab, export_tab = st.tabs(["Bảng thông số", "Biểu đồ và chẩn đoán", "Xuất báo cáo"])
    with table_tab:
        _tabular(snapshot)
    with plot_tab:
        _plot(snapshot, key)
    with export_tab:
        raw = record_bytes(snapshot)
        prepared = st.session_state.setdefault("pk_prepared_exports", {})
        snapshot_id = snapshot_digest(snapshot)
        for kind, label, filename in (
            ("excel", "Tải Excel (dữ liệu/NCA/mô hình/chẩn đoán)", "phan_tich_pk.xlsx"),
            ("word", "Tải báo cáo Word tiếng Việt", "bao_cao_pk.docx"),
            ("pdf", "Tải báo cáo PDF tiếng Việt", "bao_cao_pk.pdf"),
        ):
            prepared_key = f"{snapshot_id}:{kind}"
            if st.button(f"Chuẩn bị {kind.upper()} để tải", key=f"{key}_prepare_{kind}"):
                try:
                    if len(prepared) >= 12:
                        prepared.clear()
                    prepared[prepared_key] = _export(raw, kind)
                except (ValueError, OSError, TypeError, ImportError) as exc:
                    if hasattr(st, "warning"):
                        st.warning(f"Không thể tạo báo cáo {kind.upper()}: {exc}")
            if prepared_key in prepared:
                st.download_button(label, prepared[prepared_key], file_name=filename,
                                   key=f"{key}_{kind}")


def independent_pk_page(project_controls=None) -> None:
    st.info("Phân hệ PK độc lập với nghiên cứu BE. Hỗ trợ đơn liều, đa liều cách đều "
            "và đánh giá chu kỳ ở trạng thái ổn định. Kết quả là bản phân tích kỹ thuật, "
            "chưa được thẩm định cho quyết định pháp lý.")
    save_slot, upload_slot = project_controls if project_controls is not None else (st.container(), st.container())
    save_placeholder = save_slot.empty()
    with save_placeholder:
        st.button("Lưu project PK độc lập (.pk.zip)", disabled=True,
                  help="Hãy nhập dữ liệu hợp lệ trước khi lưu project.",
                  key="pk_project_save_unavailable", width="stretch")
    with upload_slot:
        st.caption("Upload project PK độc lập (.pk.zip)")
        upload_project = st.file_uploader("Chọn project PK độc lập", type=["zip"], key="pk_project_upload")
        if upload_project is not None and st.button("Kiểm tra và mở project", key="pk_project_open"):
            try:
                validate_project_filename(upload_project.name, "independent_pk")
                payload = import_workflow_project(upload_project.getvalue(), "independent_pk")
                if payload.get("format_version") != 1:
                    raise ValueError("Phiên bản nội dung project chưa hỗ trợ.")
                snapshot = payload["snapshot"]
                if not isinstance(snapshot, dict) or not all(
                    isinstance(snapshot.get(key), expected) for key, expected in
                    {"data": list, "settings": dict, "nca": list, "models": list,
                     "errors": list, "source": str, "created_utc": str}.items()
                ):
                    raise ValueError("Thiếu trường bắt buộc trong project PK.")
                data = validate_profiles(pd.DataFrame(snapshot["data"]))
                settings = PKSettings(**snapshot["settings"])
                settings.validate()
                if snapshot.get("regimen"):
                    PKRegimen(**snapshot["regimen"]).validate(settings)
                widgets = payload["widgets"]
                allowed = {"pk_dose_mode", "pk_tau", "pk_time_basis", "pk_number_doses",
                           "pk_ss_confirm", "pk_route", "pk_concentration_unit", "pk_has_dose",
                           "pk_dose", "pk_dose_unit", "pk_infusion", "pk_zero_policy",
                           "pk_integration", "pk_terminal_points", "pk_terminal_r2",
                           "pk_methods", "pk_weighting"}
                if (not isinstance(widgets, dict) or set(widgets) - allowed or
                        not all(isinstance(value, (str, int, float, bool, list)) for value in widgets.values())):
                    raise ValueError("Cấu hình điều khiển PK không hợp lệ.")
                if "pk_dose_mode" in widgets and widgets["pk_dose_mode"] not in ("single", "multiple", "steady_state"):
                    raise ValueError("Chế độ liều trong project không hợp lệ.")
                if "pk_route" in widgets and widgets["pk_route"] not in ("oral", "iv_bolus", "iv_infusion"):
                    raise ValueError("Đường dùng trong project không hợp lệ.")
                if "pk_methods" in widgets and (not isinstance(widgets["pk_methods"], list) or
                    any(item not in ("NCA", "1 ngăn", "2 ngăn", "3 ngăn") for item in widgets["pk_methods"])):
                    raise ValueError("Phương pháp phân tích trong project không hợp lệ.")
                choices = payload.get("analysis_choices")
                if choices is not None and (not isinstance(choices, dict) or
                    set(choices) != {"modes", "run_nca", "weighting"} or
                    not isinstance(choices["modes"], list) or
                    any(type(n) is not int or n not in (1, 2, 3) for n in choices["modes"]) or
                    type(choices["run_nca"]) is not bool or
                    choices["weighting"] not in ("equal", "1/C", "1/C²")):
                    raise ValueError("Cấu hình phân tích trong project không hợp lệ.")
                # All integrity and domain checks must pass before applying any changes.
                st.session_state.update(widgets)
                st.session_state["pk_manual_data"] = data
                st.session_state["pk_manual_generation"] = st.session_state.get("pk_manual_generation", 0) + 1
                st.session_state["pk_upload_generation"] = st.session_state.get("pk_upload_generation", 0) + 1
                st.session_state["pk_restored_source"] = snapshot["source"]
                st.session_state["pk_restored_analysis_choices"] = choices
                if payload.get("analyzed") is True:
                    st.session_state["pk_current_snapshot"] = snapshot
                    st.session_state["pk_restore_pending"] = True
                else:
                    st.session_state.pop("pk_current_snapshot", None)
                    st.session_state.pop("pk_current_fingerprint", None)
                    st.session_state.pop("pk_restore_pending", None)
                st.session_state.pop("table::pk_concentrations", None)
                st.rerun()
            except (ValueError, TypeError, KeyError, UnicodeError) as exc:
                st.error(f"Không mở được project: {exc}")

    from be_app.demo_scenarios import PK_CASES, pk_frame

    demo_case = st.selectbox("Học thử · Tình huống PK", list(PK_CASES),
                             format_func=lambda key: PK_CASES[key].title, key="pk_demo_case")
    st.caption(PK_CASES[demo_case].objective + " " + PK_CASES[demo_case].next_step)
    if st.button("Điền dữ liệu mẫu vào bảng PK", key="pk_demo_load"):
        frame, settings = pk_frame(demo_case)
        st.session_state["pk_manual_data"] = frame
        st.session_state["pk_manual_generation"] = st.session_state.get("pk_manual_generation", 0) + 1
        st.session_state["pk_upload_generation"] = st.session_state.get("pk_upload_generation", 0) + 1
        st.session_state.update(settings)
        st.session_state["pk_route"] = "iv_bolus" if demo_case == "iv" else "oral"
        st.session_state["pk_ss_confirm"] = False
        st.session_state.pop("pk_current_snapshot", None)
        st.session_state.pop("pk_current_fingerprint", None)
        st.session_state.pop("pk_restored_source", None)
        st.session_state.pop("pk_restore_pending", None)
        st.session_state.pop("pk_restored_analysis_choices", None)
        st.session_state["pk_demo_active"] = demo_case
        st.rerun()
    if st.session_state.get("pk_demo_active"):
        st.caption("Dữ liệu tổng hợp cho học tập · Áp dụng bảng rồi dùng nút Chạy phân tích PK thông thường.")
    st.subheader("1. Nhập dữ liệu Cplasma")
    try:
        edited, source = _parse_input()
    except (ValueError, TypeError, KeyError, UnicodeError) as exc:
        st.error(f"Không đọc được bảng dữ liệu: {exc}")
        return
    st.subheader("2. Cấu hình phân tích")
    config, modes, weighting, run_nca, regimen = _settings()
    current_data = None
    fingerprint = None
    try:
        config.validate()
        if regimen is not None:
            regimen.validate(config)
        current_data = validate_profiles(edited)
        if regimen is not None:
            for _, frame in current_data.groupby("profile_id"):
                regimen.absolute_times(frame.time_h.to_numpy(dtype=float))
        fingerprint = _fingerprint(current_data, config, modes + ((0,) if run_nca else ()),
                                   weighting, regimen, source)
        if st.session_state.pop("pk_restore_pending", False):
            restored = st.session_state.get("pk_current_snapshot")
            if (restored and restored["settings"] == asdict(config) and
                    restored.get("regimen") == (asdict(regimen) if regimen else None) and
                    validate_profiles(pd.DataFrame(restored["data"])).reset_index(drop=True).equals(
                        current_data.reset_index(drop=True)) and
                    st.session_state.get("pk_restored_analysis_choices") ==
                    {"modes": list(modes), "run_nca": run_nca, "weighting": weighting}):
                st.session_state["pk_current_fingerprint"] = fingerprint
        st.success(f"QC cấu trúc: {len(current_data)} mẫu, {current_data.profile_id.nunique()} hồ sơ; "
                   "không có thời gian trùng, thiếu hoặc nồng độ âm.")
    except (ValueError, TypeError) as exc:
        st.warning(f"QC chưa đạt: {exc}")
    if current_data is not None:
        existing = st.session_state.get("pk_current_snapshot")
        analyzed = bool(existing and st.session_state.get("pk_current_fingerprint") == fingerprint)
        project_snapshot = (existing if analyzed else create_snapshot(
            current_data, asdict(config), [], [], [], source,
            asdict(regimen) if regimen is not None else None))
        widget_keys = {"pk_dose_mode", "pk_tau", "pk_time_basis", "pk_number_doses",
                       "pk_ss_confirm", "pk_route", "pk_concentration_unit", "pk_has_dose",
                       "pk_dose", "pk_dose_unit", "pk_infusion", "pk_zero_policy",
                       "pk_integration", "pk_terminal_points", "pk_terminal_r2",
                       "pk_methods", "pk_weighting"}
        payload = {"format_version": 1, "snapshot": project_snapshot, "analyzed": analyzed,
                   "analysis_choices": {"modes": list(modes), "run_nca": run_nca,
                                        "weighting": weighting},
                   "widgets": {key: st.session_state[key] for key in widget_keys
                               if key in st.session_state}}
        try:
            project_bytes = export_workflow_project("independent_pk", payload)
            with save_placeholder:
                st.download_button("Lưu project PK độc lập (.pk.zip)", project_bytes,
                                   file_name="PK_doc_lap.pk.zip", mime="application/zip",
                                   on_click="ignore", key="pk_project_download", width="stretch")
        except (TypeError, ValueError) as exc:
            st.error(f"Không xuất được project: {exc}")
    if st.button("3. Chạy phân tích PK", type="primary", disabled=current_data is None) and current_data is not None:
        nca_results, fitted, errors = [], [], []
        for profile_id, frame in current_data.groupby("profile_id", sort=True):
            if run_nca:
                try:
                    nca_results.append(analyze_nca(frame, config) if regimen is None
                                       else analyze_interval_nca(frame, config, regimen))
                except (ValueError, TypeError, ArithmeticError) as exc:
                    errors.append(f"{profile_id} · NCA: {exc}")
            for compartments in modes:
                try:
                    fitted.append(fit_compartment(frame, config, compartments=compartments,
                                                  weighting=weighting, regimen=regimen))
                except (ValueError, TypeError, ArithmeticError, OverflowError) as exc:
                    errors.append(f"{profile_id} · {compartments} ngăn: {exc}")
        if not run_nca and not modes:
            errors.append("Cần chọn ít nhất một phương pháp phân tích.")
        snapshot = create_snapshot(current_data, asdict(config), nca_results, fitted, errors, source,
                                   asdict(regimen) if regimen is not None else None)
        st.session_state.pk_current_snapshot = snapshot
        st.session_state.pk_current_fingerprint = fingerprint
        st.session_state.pk_last_saved_id = None
    current_snapshot = st.session_state.get("pk_current_snapshot")
    if current_snapshot is not None:
        if fingerprint != st.session_state.get("pk_current_fingerprint"):
            st.warning("Đầu vào hoặc cấu hình đã thay đổi. Cần chạy lại PK để lưu/xuất kết quả mới.")
        else:
            st.subheader("4. Kết quả phân tích")
            _render_snapshot(current_snapshot, "pk_current")
