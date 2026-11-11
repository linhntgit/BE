"""Versioned, append-only standalone PK run records and Vietnamese exports."""

from __future__ import annotations

import hashlib
import io
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

NCA_VI_COLUMNS = {
    "profile_id": "Mã hồ sơ", "route": "Đường dùng", "status": "Trạng thái",
    "n": "Số mẫu", "cmax_ng_ml": "Cmax (ng/mL)", "tmax_h": "Tmax (giờ)",
    "t_first_h": "Thời điểm đầu (giờ)", "tlast_h": "Tlast (giờ)",
    "clast_ng_ml": "Clast (ng/mL)", "auc_first_last": "AUC đầu–cuối (ng·giờ/mL)",
    "aumc_first_last": "AUMC đầu–cuối (ng·giờ²/mL)",
    "auc_0_last": "AUC0–last (ng·giờ/mL)",
    "aumc_0_last": "AUMC0–last (ng·giờ²/mL)",
    "c0_estimated_ng_ml": "C0 ngoại suy (ng/mL)",
    "lambda_z_h_inv": "Lambda-z (1/giờ)", "half_life_h": "t½ (giờ)",
    "auc_0_inf": "AUC0–∞ (ng·giờ/mL)", "auc_extrap_pct": "AUC ngoại suy (%)",
    "aumc_0_inf": "AUMC0–∞ (ng·giờ²/mL)",
    "mrt_inf_h": "MRT quan sát (giờ)", "mrt_iv_h": "MRT IV hiệu chỉnh (giờ)",
    "cl_l_h": "CL (L/giờ)", "cl_over_f_l_h": "CL/F (L/giờ)",
    "vz_l": "Vz (L)", "vz_over_f_l": "Vz/F (L)", "vss_l": "Vss (L)",
    "terminal_adj_r2": "R² hiệu chỉnh pha cuối", "terminal_times": "Điểm pha cuối (giờ)",
    "mode": "Chế độ liều", "tau_h": "Khoảng liều τ (giờ)",
    "last_dose_h": "Thời điểm liều cuối (giờ)",
    "steady_state_confirmed": "Đã xác nhận trạng thái ổn định",
    "cmax_tau_ng_ml": "Cmax,τ (ng/mL)", "tmax_tau_h": "Tmax,τ (giờ sau liều cuối)",
    "cmin_tau_ng_ml": "Cmin,τ quan sát (ng/mL)",
    "ctrough_ng_ml": "Ctrough tại τ (ng/mL)",
    "auc_tau_ng_h_ml": "AUCτ (ng·giờ/mL)",
    "cavg_tau_ng_ml": "Cavg,τ (ng/mL)", "fluctuation_pct": "Dao động đỉnh–đáy (%)",
    "cl_ss_l_h": "CLss (L/giờ)", "cl_over_f_ss_l_h": "CL/Fss (L/giờ)",
    "accumulation_ratio_auc": "Tỷ số tích lũy AUCτ cuối/đầu",
    "warnings": "Cảnh báo",
}
SETTINGS_VI_COLUMNS = {
    "route": "Đường dùng", "dose": "Liều dùng", "dose_unit": "Đơn vị liều",
    "concentration_unit": "Đơn vị Cplasma", "infusion_duration_h": "Thời gian truyền (giờ)",
    "integration": "Phương pháp tính AUC", "zero_policy": "Xử lý thời điểm 0",
    "terminal_min_points": "Số điểm pha cuối tối thiểu",
    "terminal_min_adj_r2": "Adjusted R² tối thiểu pha cuối",
    "mode": "Chế độ đa liều", "tau_h": "Khoảng liều τ (giờ)",
    "number_doses": "Số liều đã dùng", "time_basis": "Gốc thời gian",
    "steady_state_confirmed": "Đã xác nhận steady-state",
}
SETTINGS_VI_VALUES = {
    "oral": "Uống", "iv_bolus": "Tiêm IV nhanh", "iv_infusion": "Truyền IV",
    "linear": "Hình thang tuyến tính", "linear_up_log_down": "Tuyến tính tăng – log giảm",
    "measured_only": "Chỉ dùng C0 đo được", "assume_zero": "Giả định C0 bằng 0",
    "extrapolate_iv": "Ngoại suy C0 từ 3 mẫu sớm",
    "multiple": "Đa liều", "steady_state": "Trạng thái ổn định",
    "first_dose": "Từ liều đầu", "last_dose": "Từ liều cuối",
}


def _settings_rows(snapshot: dict) -> list[tuple[str, object]]:
    return [(SETTINGS_VI_COLUMNS.get(key, key), SETTINGS_VI_VALUES.get(value, value)
             if isinstance(value, str) else value)
            for key, value in {**snapshot["settings"], **(snapshot.get("regimen") or {})}.items()]


def _visible(value: object) -> str:
    return "Chưa xác định" if value is None else str(value)


def record_bytes(snapshot: dict) -> bytes:
    return json.dumps(snapshot, ensure_ascii=False, allow_nan=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def snapshot_digest(snapshot: dict) -> str:
    return hashlib.sha256(record_bytes(snapshot)).hexdigest()


def create_snapshot(data: pd.DataFrame, settings: dict, nca: list[dict],
                    models: list[dict], errors: list[str], source: str,
                    regimen: dict | None = None) -> dict:
    snapshot = {
        "schema_version": 2 if regimen is not None else 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source": source, "settings": settings, "data": data.to_dict("records"),
        "nca": nca, "models": models, "errors": errors,
        "scope": "Phân tích Dược động học (PK) độc lập.",
    }
    if regimen is not None:
        snapshot["regimen"] = regimen
    return snapshot


class PKRecordStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS pk_runs (
                run_id TEXT PRIMARY KEY, created_utc TEXT NOT NULL,
                sha256 TEXT NOT NULL, content TEXT NOT NULL)""")

    def _connect(self):
        return sqlite3.connect(self.path, timeout=10)

    def save(self, snapshot: dict) -> str:
        raw = record_bytes(snapshot)
        run_id = uuid.uuid4().hex
        with self._connect() as db:
            db.execute("INSERT INTO pk_runs VALUES (?, ?, ?, ?)",
                       (run_id, snapshot["created_utc"], hashlib.sha256(raw).hexdigest(),
                        raw.decode("utf-8")))
        return run_id

    def list_runs(self, limit: int = 100) -> list[dict]:
        with self._connect() as db:
            rows = db.execute("SELECT run_id,created_utc,sha256 FROM pk_runs "
                              "ORDER BY created_utc DESC,run_id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(run_id=row[0], created_utc=row[1], sha256=row[2]) for row in rows]

    def load(self, run_id: str) -> dict:
        with self._connect() as db:
            row = db.execute("SELECT sha256,content FROM pk_runs WHERE run_id=?", (run_id,)).fetchone()
        if row is None:
            raise ValueError("Không tìm thấy phiên phân tích PK đã lưu.")
        raw = row[1].encode("utf-8")
        if hashlib.sha256(raw).hexdigest() != row[0]:
            raise ValueError("Bản ghi PK không vượt qua kiểm tra toàn vẹn SHA-256.")
        snapshot = json.loads(raw)
        if snapshot.get("schema_version") not in (1, 2):
            raise ValueError("Phiên bản bản ghi PK chưa được hỗ trợ.")
        return snapshot


def _display_nca(snapshot: dict) -> pd.DataFrame:
    frame = pd.DataFrame(snapshot["nca"])
    for column in ("warnings", "terminal_times"):
        if column in frame:
            frame[column] = frame[column].map(lambda value: "; ".join(map(str, value)))
    frame = frame.rename(columns=NCA_VI_COLUMNS)
    if "Đường dùng" in frame:
        frame["Đường dùng"] = frame["Đường dùng"].replace(SETTINGS_VI_VALUES)
    return frame


def _display_models(snapshot: dict) -> pd.DataFrame:
    return pd.DataFrame([
        {"Mã hồ sơ": model["profile_id"], "Số ngăn": model["compartments"],
         "Trọng số": "Không trọng số" if model["weighting"] == "equal" else model["weighting"],
         "RMSE (ng/mL)": model["rmse_ng_ml"],
         "AICc": model["aicc"], "BIC": model["bic"],
         **model["parameters"], **model.get("derived_parameters", {}),
         "Cảnh báo": "; ".join(model["warnings"])}
        for model in snapshot["models"]
    ])


def excel_report(snapshot: dict) -> bytes:
    def safe_text_cells(frame: pd.DataFrame) -> pd.DataFrame:
        """Keep untrusted text as text in openpyxl while preserving numeric cell types."""
        result = frame.copy()
        for column in result.select_dtypes(include=["object", "string"]).columns:
            result[column] = result[column].map(
                lambda value: "'" + value if isinstance(value, str)
                and value.startswith(("=", "+", "-", "@")) else value
            )
        return result

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        safe_text_cells(_display_nca(snapshot)).to_excel(writer, sheet_name="NCA", index=False)
        safe_text_cells(_display_models(snapshot)).to_excel(writer, sheet_name="Mo_hinh", index=False)
        safe_text_cells(pd.DataFrame(snapshot["data"]).rename(columns={
            "profile_id": "Mã hồ sơ", "time_h": "Thời gian (giờ)",
            "concentration": "Nồng độ đầu vào", "blq": "BLQ",
        })).to_excel(writer, sheet_name="Du_lieu", index=False)
        diagnostics = []
        for model in snapshot["models"]:
            diagnostics += [{"profile_id": model["profile_id"], "so_ngan": model["compartments"],
                             "time_h": t, "observed_ng_ml": o, "predicted_ng_ml": p,
                             "residual_ng_ml": r}
                            for t, o, p, r in zip(model["time_h"], model["observed"],
                                                  model["predicted"], model["residuals"], strict=True)]
        safe_text_cells(pd.DataFrame(diagnostics, columns=["profile_id", "so_ngan", "time_h",
                                            "observed_ng_ml", "predicted_ng_ml",
                                            "residual_ng_ml"]).rename(columns={
                                                "profile_id": "Mã hồ sơ", "so_ngan": "Số ngăn",
                                                "time_h": "Thời gian (giờ)",
                                                "observed_ng_ml": "Quan sát (ng/mL)",
                                                "predicted_ng_ml": "Dự đoán (ng/mL)",
                                                "residual_ng_ml": "Phần dư (ng/mL)",
                                            })).to_excel(writer, sheet_name="Chan_doan", index=False)
        safe_text_cells(pd.DataFrame([{"Thuộc tính": k, "Giá trị": _visible(v)}
                      for k, v in _settings_rows(snapshot)] +
                     [{"Thuộc tính": "Nguồn", "Giá trị": snapshot["source"]},
                      {"Thuộc tính": "Thời điểm UTC", "Giá trị": snapshot["created_utc"]},
                      {"Thuộc tính": "SHA-256", "Giá trị": snapshot_digest(snapshot)}]
                     )).to_excel(writer, sheet_name="Cau_hinh", index=False)
        safe_text_cells(pd.DataFrame({"Cảnh báo": snapshot["errors"]})).to_excel(
            writer, sheet_name="Canh_bao", index=False
        )
        for sheet in writer.book:
            sheet.freeze_panes = "A2"
            sheet.auto_filter.ref = sheet.dimensions
            for column in sheet.columns:
                width = min(max(max(len(str(c.value or "")) for c in column[:100]) + 2, 12), 55)
                sheet.column_dimensions[column[0].column_letter].width = width
    return output.getvalue()


def word_report(snapshot: dict) -> bytes:
    """Export the Vietnamese structured PK report with automatic TOC and figures."""
    from be_app.pk_report_design import make_word

    return make_word(snapshot, _settings_rows(snapshot),
                     _display_nca(snapshot).to_dict("records"), snapshot_digest(snapshot))


def pdf_report(snapshot: dict) -> bytes:
    """Export the Vietnamese paginated PK report with TOC and figures."""
    from be_app.pk_report_design import make_pdf

    return make_pdf(snapshot, _settings_rows(snapshot),
                    _display_nca(snapshot).to_dict("records"), snapshot_digest(snapshot))
