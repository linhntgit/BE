"""Standalone, single-dose PK analysis; deliberately independent of BE decisions.

Concentration units are converted to ng/mL. No missing time-zero observation is
invented: any optional time-zero estimate is an explicit, reported assumption.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd
from scipy.stats import linregress

from be_app.nca import cumulative_areas

Route = Literal["oral", "iv_bolus", "iv_infusion"]

CONCENTRATION_FACTORS = {"ng/mL": 1.0, "µg/mL": 1000.0, "mg/L": 1000.0, "mg/mL": 1_000_000.0}
DOSE_FACTORS = {"ng": 1.0, "µg": 1000.0, "mg": 1_000_000.0, "g": 1_000_000_000.0}


@dataclass(frozen=True)
class PKSettings:
    route: Route = "oral"
    dose: float | None = None
    dose_unit: str = "mg"
    concentration_unit: str = "ng/mL"
    infusion_duration_h: float | None = None
    integration: Literal["linear", "linear_up_log_down"] = "linear_up_log_down"
    zero_policy: Literal["measured_only", "assume_zero", "extrapolate_iv"] = "measured_only"
    terminal_min_points: int = 3
    terminal_min_adj_r2: float = 0.8

    def validate(self) -> None:
        if self.route not in ("oral", "iv_bolus", "iv_infusion"):
            raise ValueError("Đường dùng không hợp lệ.")
        if self.concentration_unit not in CONCENTRATION_FACTORS or self.dose_unit not in DOSE_FACTORS:
            raise ValueError("Đơn vị nồng độ hoặc liều chưa được hỗ trợ.")
        if self.dose is not None and (not math.isfinite(self.dose) or self.dose <= 0):
            raise ValueError("Liều phải là số hữu hạn dương.")
        if self.route == "iv_infusion" and (
            self.infusion_duration_h is None
            or not math.isfinite(self.infusion_duration_h)
            or self.infusion_duration_h <= 0
        ):
            raise ValueError("Truyền IV phải có thời gian truyền hữu hạn và lớn hơn 0.")
        if self.zero_policy == "extrapolate_iv" and self.route != "iv_bolus":
            raise ValueError("Chỉ dùng ngoại suy C0 cho IV bolus.")
        if self.zero_policy == "assume_zero" and self.route == "iv_bolus":
            raise ValueError("IV bolus không thể giả định C0 = 0.")
        if self.integration not in ("linear", "linear_up_log_down"):
            raise ValueError("Phương pháp tích phân không hợp lệ.")
        if not 3 <= self.terminal_min_points <= 10 or not 0 <= self.terminal_min_adj_r2 <= 1:
            raise ValueError("Cấu hình pha thải trừ không hợp lệ.")


def read_concentrations(raw: pd.DataFrame, *, layout: str, time_column: str,
                        concentration_column: str | None = None,
                        profile_column: str | None = None,
                        blq_column: str | None = None) -> pd.DataFrame:
    """Normalize long/wide input; explicit BLQ text or bool is accepted, missing is rejected."""
    if time_column not in raw or raw.empty:
        raise ValueError("Không tìm thấy cột thời gian hoặc bảng rỗng.")
    if layout == "wide":
        value_columns = [c for c in raw if c != time_column]
        if not value_columns:
            raise ValueError("Dạng wide cần ít nhất một cột hồ sơ nồng độ.")
        data = raw.melt(id_vars=time_column, value_vars=value_columns,
                        var_name="profile_id", value_name="concentration")
    elif layout == "long":
        if not concentration_column or concentration_column not in raw:
            raise ValueError("Chưa chọn cột nồng độ.")
        data = pd.DataFrame({
            "profile_id": raw[profile_column] if profile_column else "PK01",
            time_column: raw[time_column], "concentration": raw[concentration_column],
        })
        if blq_column:
            data["explicit_blq"] = raw[blq_column]
    else:
        raise ValueError("Định dạng dữ liệu không hợp lệ.")
    data = data.rename(columns={time_column: "time_h"})
    data["profile_id"] = data["profile_id"].astype("string").str.strip()
    if data.profile_id.isna().any() or data.profile_id.eq("").any():
        raise ValueError("Thiếu mã hồ sơ PK.")
    data["time_h"] = pd.to_numeric(data.time_h, errors="coerce")
    if data.time_h.isna().any() or not np.isfinite(data.time_h.to_numpy(dtype=float)).all():
        raise ValueError("Thời gian phải là số hữu hạn, không được trống.")
    if (data.time_h < 0).any():
        raise ValueError("Không hỗ trợ thời gian âm trong PK đơn liều.")
    raw_c = data["concentration"].astype("string").str.strip()
    blq_text = raw_c.str.upper().isin(["BLQ", "BQL", "<LLOQ", "<LOQ"])
    if "explicit_blq" in data:
        flags = data["explicit_blq"].astype("string").str.strip().str.lower()
        if not flags.isin(["true", "false", "1", "0", "yes", "no", "có", "không"]).all():
            raise ValueError("Cờ BLQ chỉ nhận True/False, 1/0, yes/no, có/không.")
        flagged = flags.isin(["true", "1", "yes", "có"])
        numeric_observed = pd.to_numeric(raw_c, errors="coerce")
        if (flagged & numeric_observed.gt(0).fillna(False)).any():
            raise ValueError("BLQ không được đi kèm nồng độ định lượng dương.")
        blq_text |= flagged
    raw_c = raw_c.mask(blq_text, "0")
    data["concentration"] = pd.to_numeric(raw_c, errors="coerce")
    if data.concentration.isna().any() or not np.isfinite(data.concentration.to_numpy(dtype=float)).all():
        raise ValueError("Nồng độ thiếu hoặc không phải số; BLQ phải đánh dấu tường minh.")
    if (data.concentration < 0).any():
        raise ValueError("Không chấp nhận nồng độ âm.")
    data["blq"] = blq_text.astype(bool)
    if data.duplicated(["profile_id", "time_h"]).any():
        raise ValueError("Trùng thời điểm trong cùng hồ sơ: cần QC trước khi phân tích.")
    return data[["profile_id", "time_h", "concentration", "blq"]].sort_values(
        ["profile_id", "time_h"]
    ).reset_index(drop=True)


def validate_profiles(data: pd.DataFrame) -> pd.DataFrame:
    required = {"profile_id", "time_h", "concentration", "blq"}
    if not required <= set(data) or data.empty:
        raise ValueError("Thiếu cột profile_id / time_h / concentration / blq.")
    clean = data.copy()
    clean["profile_id"] = clean.profile_id.astype("string").str.strip()
    if clean.profile_id.isna().any() or clean.profile_id.eq("").any():
        raise ValueError("Mã hồ sơ không được trống.")
    for col in ("time_h", "concentration"):
        clean[col] = pd.to_numeric(clean[col], errors="coerce")
        if clean[col].isna().any() or not np.isfinite(clean[col].to_numpy(dtype=float)).all():
            raise ValueError(f"{col} có giá trị thiếu hoặc không hữu hạn.")
    if (clean.time_h < 0).any() or (clean.concentration < 0).any():
        raise ValueError("Không cho phép thời gian/nồng độ âm.")
    if clean.blq.isna().any() or not clean.blq.map(lambda x: isinstance(x, (bool, np.bool_))).all():
        raise ValueError("Cột BLQ cần giá trị boolean đầy đủ.")
    if (clean.blq & (clean.concentration > 0)).any():
        raise ValueError("Dòng BLQ không được chứa nồng độ dương.")
    if clean.duplicated(["profile_id", "time_h"]).any():
        raise ValueError("Có thời gian trùng trong một hồ sơ.")
    return clean.sort_values(["profile_id", "time_h"]).reset_index(drop=True)


def _terminal(t: np.ndarray, c: np.ndarray, settings: PKSettings) -> tuple[dict | None, list[str]]:
    warnings: list[str] = []
    positive = np.flatnonzero(c > 0)
    if not len(positive):
        return None, ["Không có mẫu nồng độ định lượng dương."]
    peak = np.flatnonzero(c == c.max())[-1]
    last = positive[-1]
    candidates = positive[positive > peak]
    zeros = np.flatnonzero(c[:last + 1] == 0)
    if len(zeros):
        candidates = candidates[candidates > zeros[-1]]
    if settings.route == "iv_infusion":
        # A decline during an ongoing infusion cannot establish elimination kinetics.
        candidates = candidates[t[candidates] > settings.infusion_duration_h]
        if len(candidates) < settings.terminal_min_points:
            return None, ["Truyền IV: không đủ điểm pha cuối sau khi kết thúc truyền; "
                          "không tính λz, AUC∞ hoặc CL."]
    best = None
    for start in range(len(candidates) - settings.terminal_min_points + 1):
        idx = candidates[start:]
        fit = linregress(t[idx], np.log(c[idx]))
        if not np.isfinite([fit.slope, fit.intercept, fit.rvalue]).all() or fit.slope >= 0:
            continue
        r2adj = 1 - (1 - fit.rvalue**2) * (len(idx) - 1) / (len(idx) - 2)
        if r2adj < settings.terminal_min_adj_r2:
            continue
        candidate = {"lambda_z": -float(fit.slope), "adj_r2": float(r2adj),
                     "terminal_times": t[idx].tolist(), "n_terminal": len(idx),
                     "intercept": float(fit.intercept)}
        if best is None or candidate["adj_r2"] > best["adj_r2"] + 1e-4:
            best = candidate
    if best is None:
        warnings.append("Không xác định được pha cuối đạt tiêu chí; AUC∞ và t½ để trống.")
    return best, warnings


def analyze_nca(frame: pd.DataFrame, settings: PKSettings) -> dict:
    """Estimate NCA per profile; dose-dependent parameters only if AUC0-inf valid."""
    settings.validate()
    data = validate_profiles(frame)
    if data.profile_id.nunique() != 1:
        raise ValueError("NCA cần đúng một hồ sơ mỗi lần gọi.")
    warnings: list[str] = []
    t = data.time_h.to_numpy(dtype=float)
    c = data.concentration.to_numpy(dtype=float) * CONCENTRATION_FACTORS[settings.concentration_unit]
    censored = data.blq.to_numpy(dtype=bool)
    c[censored] = 0
    if len(t) < 2 or not (c > 0).any():
        raise ValueError("Cần ít nhất hai thời điểm và nồng độ định lượng dương.")
    positives = np.flatnonzero(c > 0)
    if censored[positives[0]:positives[-1] + 1].any():
        raise ValueError("BLQ nằm giữa các mẫu định lượng: cần xử lý dữ liệu trước khi tính NCA; "
                         "không được tự thay BLQ bằng 0 giữa đường cong.")
    if censored.any():
        warnings.append("Các mẫu BLQ ngoài khoảng mẫu định lượng được quy về 0 khi tính NCA.")
    measured_t0 = t[0] == 0
    inferred_c0 = None
    if measured_t0 and settings.route == "iv_bolus" and c[0] <= 0:
        warnings.append("C0 của IV bolus bằng 0 hoặc BLQ, không hợp lệ cho nồng độ ngay sau tiêm; "
                        "bỏ điểm này khỏi tích phân. Chỉ tính AUC0 khi chọn ngoại suy C0.")
        t, c = t[1:], c[1:]
        measured_t0 = False
        if len(t) < 2:
            raise ValueError("IV bolus có C0 không hợp lệ cần thêm ít nhất hai thời điểm sau tiêm.")
    if not measured_t0:
        if settings.zero_policy == "assume_zero":
            inferred_c0 = 0.0
            warnings.append("Đã giả định C(0)=0 theo lựa chọn người dùng; không phải mẫu đo.")
        elif settings.zero_policy == "extrapolate_iv":
            idx = np.flatnonzero(c > 0)[:3]
            if len(idx) < 3:
                raise ValueError("Ngoại suy C0 của IV bolus cần ≥3 mẫu dương đầu tiên.")
            first_fit = linregress(t[idx], np.log(c[idx]))
            if first_fit.slope >= 0 or not np.isfinite(first_fit.intercept):
                raise ValueError("Không thể ngoại suy C0: nồng độ giai đoạn đầu không giảm.")
            inferred_c0 = float(math.exp(first_fit.intercept))
            warnings.append("C0 ngoại suy từ 3 điểm dương sớm theo giả định một hàm mũ; cần rà soát nếu đa ngăn.")
        else:
            warnings.append("Không có mẫu t=0: chỉ báo cáo AUC từ thời điểm đầu; không tính CL/V theo liều.")
    if inferred_c0 is not None:
        t = np.r_[0.0, t]
        c = np.r_[inferred_c0, c]
    last = np.flatnonzero(c > 0)[-1]
    auc, aumc = cumulative_areas(t[:last + 1], c[:last + 1], settings.integration)
    terminal, tail_warnings = _terminal(t, c, settings)
    warnings.extend(tail_warnings)
    full_start = bool(measured_t0 or inferred_c0 is not None)
    if measured_t0 and settings.route in ("oral", "iv_infusion") and c[0] > .05 * c.max():
        warnings.append("Nồng độ trước liều >5% Cmax; không tính AUC0–∞ và CL khi chưa xử lý nền.")
        full_start = False
    result = {
        "profile_id": str(data.profile_id.iloc[0]), "route": settings.route,
        "status": "Đủ điều kiện NCA" if full_start else "NCA một phần — thiếu/không hợp lệ mẫu nền",
        "n": len(data), "cmax_ng_ml": float(c.max()), "tmax_h": float(t[np.flatnonzero(c == c.max())[0]]),
        "t_first_h": float(t[0]), "tlast_h": float(t[last]), "clast_ng_ml": float(c[last]),
        "auc_first_last": float(auc[-1]), "aumc_first_last": float(aumc[-1]),
        "auc_0_last": float(auc[-1]) if full_start else None,
        "aumc_0_last": float(aumc[-1]) if full_start else None,
        "c0_estimated_ng_ml": inferred_c0,
        "lambda_z_h_inv": None, "half_life_h": None,
        "auc_0_inf": None, "auc_extrap_pct": None, "aumc_0_inf": None,
        "mrt_inf_h": None, "mrt_iv_h": None,
        "cl_l_h": None, "cl_over_f_l_h": None, "vz_l": None,
        "vz_over_f_l": None, "vss_l": None,
        "terminal_adj_r2": None, "terminal_times": [], "warnings": warnings,
    }
    if terminal is None:
        return result
    lam = terminal["lambda_z"]
    result.update(lambda_z_h_inv=lam, half_life_h=math.log(2)/lam,
                  terminal_adj_r2=terminal["adj_r2"], terminal_times=terminal["terminal_times"])
    if not full_start:
        return result
    auc_inf = float(auc[-1] + c[last] / lam)
    aumc_inf = float(aumc[-1] + c[last] * (t[last] / lam + 1/lam**2))
    extrap = 100 * (auc_inf - auc[-1]) / auc_inf
    mrt = aumc_inf / auc_inf
    result.update(auc_0_inf=auc_inf, aumc_0_inf=aumc_inf, auc_extrap_pct=extrap,
                  mrt_inf_h=mrt)
    if extrap > 20:
        warnings.append("AUC ngoại suy >20%; độ tin cậy thông số phụ thuộc pha cuối cần xem xét.")
    if settings.route == "iv_infusion":
        if settings.infusion_duration_h is None:
            raise ValueError("Thiếu thời gian truyền IV.")
        mrt_iv = mrt - settings.infusion_duration_h / 2
        result["mrt_iv_h"] = mrt_iv if mrt_iv > 0 else None
        if mrt_iv <= 0:
            warnings.append("MRT hiệu chỉnh thời gian truyền không dương; không tính Vss.")
    elif settings.route == "iv_bolus":
        result["mrt_iv_h"] = mrt
    if settings.dose is not None:
        # (ng / [ng*h/mL]) / 1000 => L/h
        clearance = float(settings.dose) * DOSE_FACTORS[settings.dose_unit] / auc_inf / 1000
        volume = clearance / lam
        if settings.route == "oral":
            result.update(cl_over_f_l_h=clearance, vz_over_f_l=volume)
            warnings.append("CL/F và Vz/F biểu kiến; không xác định sinh khả dụng F từ uống đơn độc.")
        else:
            result.update(cl_l_h=clearance, vz_l=volume)
            mrt_for_vss: float | None = (
                mrt if settings.route == "iv_bolus" else
                mrt - settings.infusion_duration_h / 2
                if settings.infusion_duration_h is not None else None
            )
            if mrt_for_vss is not None and mrt_for_vss > 0:
                result["vss_l"] = clearance * mrt_for_vss
    return result
