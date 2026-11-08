"""Repeated fixed-dose PK: observed dosing-interval NCA and linear superposition.

The dose regimen is shared across profiles; input times are hours since the
first administration, or hours since the final administration if selected.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

from be_app.nca import cumulative_areas
from be_app.pk_analysis import CONCENTRATION_FACTORS, DOSE_FACTORS, PKSettings, validate_profiles
from be_app.pk_models import predict


@dataclass(frozen=True)
class PKRegimen:
    mode: Literal["multiple", "steady_state"] = "multiple"
    tau_h: float = 12.0
    number_doses: int = 5
    time_basis: Literal["first_dose", "last_dose"] = "last_dose"
    steady_state_confirmed: bool = False

    def validate(self, settings: PKSettings) -> None:
        settings.validate()
        if self.mode not in ("multiple", "steady_state"):
            raise ValueError("Chế độ đa liều không hợp lệ.")
        if not math.isfinite(self.tau_h) or self.tau_h <= 0:
            raise ValueError("Khoảng cách liều τ phải dương và hữu hạn.")
        if isinstance(self.number_doses, bool) or not isinstance(self.number_doses, int) or not 2 <= self.number_doses <= 1000:
            raise ValueError("Số liều cần là số nguyên từ 2 đến 1000.")
        if self.time_basis not in ("first_dose", "last_dose"):
            raise ValueError("Gốc thời gian không hợp lệ.")
        if self.steady_state_confirmed and self.mode != "steady_state":
            raise ValueError("Chỉ xác nhận steady-state ở chế độ trạng thái ổn định.")
        if settings.infusion_duration_h is not None and settings.route == "iv_infusion" and settings.infusion_duration_h > self.tau_h:
            raise ValueError("Thời gian truyền IV không được dài hơn τ trong lịch liều đều.")

    @property
    def last_dose_h(self) -> float:
        return (self.number_doses - 1) * self.tau_h

    def absolute_times(self, t: np.ndarray | list[float]) -> np.ndarray:
        times = np.asarray(t, dtype=float)
        if not np.isfinite(times).all() or (times < 0).any():
            raise ValueError("Thời gian lấy mẫu phải không âm và hữu hạn.")
        end = self.tau_h if self.time_basis == "last_dose" else self.number_doses * self.tau_h
        if (times > end + 1e-8).any():
            raise ValueError("Thời gian mẫu nằm ngoài lịch liều được khai báo.")
        return times + (self.last_dose_h if self.time_basis == "last_dose" else 0.0)


def predict_multiple(t: np.ndarray | list[float], parameters: dict[str, float],
                     settings: PKSettings, compartments: int, regimen: PKRegimen) -> np.ndarray:
    """Concentrations after finite repeated identical doses, at absolute sample times.

    Exactly at dose instants, an IV bolus prediction is post-dose. At the final
    interval endpoint there is no extra (n+1)th dose, hence the value is trough.
    """
    regimen.validate(settings)
    if settings.dose is None:
        raise ValueError("Dự đoán nhiều liều cần biết liều mỗi lần.")
    times = np.asarray(t, dtype=float)
    if not np.isfinite(times).all() or (times < 0).any() or (times > regimen.number_doses * regimen.tau_h + 1e-8).any():
        raise ValueError("Thời gian dự đoán nằm ngoài lịch liều.")
    flat = times.reshape(-1)
    dose_times = np.arange(regimen.number_doses, dtype=float) * regimen.tau_h
    elapsed = flat[:, None] - dose_times[None, :]
    active = elapsed >= -1e-10
    if not active.any():
        return np.zeros_like(times, dtype=float)
    single_dose = predict(np.maximum(elapsed[active], 0), parameters, settings, compartments)
    rows = np.nonzero(active)[0]
    return np.bincount(rows, weights=single_dose, minlength=len(flat)).reshape(times.shape)


def _cycle_auc(t: np.ndarray, c: np.ndarray, blq: np.ndarray, start: float,
               tau: float, integration: str, *, exclude_second_bolus: bool = False) -> float | None:
    """Return a measured full-interval AUC; no invented boundary concentrations."""
    end = start + tau
    selected = (t >= start - 1e-8) & (t <= end + 1e-8)
    ts, cs, bs = t[selected], c[selected], blq[selected]
    if len(ts) < 2 or not np.isclose(ts[0], start, atol=1e-8) or not np.isclose(ts[-1], end, atol=1e-8) or bs.any():
        return None
    if exclude_second_bolus:
        return None  # At the next dose, C(tau+) is not C(tau-).
    auc, _ = cumulative_areas(ts - start, cs, integration)
    return float(auc[-1])


def analyze_interval_nca(frame: pd.DataFrame, settings: PKSettings, regimen: PKRegimen) -> dict:
    """Calculate last-interval observed NCA without claiming SS from sampling alone."""
    regimen.validate(settings)
    data = validate_profiles(frame)
    if data.profile_id.nunique() != 1:
        raise ValueError("NCA đa liều cần đúng một hồ sơ mỗi lượt.")
    t = regimen.absolute_times(data.time_h.to_numpy(dtype=float))
    c = data.concentration.to_numpy(dtype=float) * CONCENTRATION_FACTORS[settings.concentration_unit]
    blq = data.blq.to_numpy(dtype=bool)
    start, end = regimen.last_dose_h, regimen.last_dose_h + regimen.tau_h
    within = (t >= start - 1e-8) & (t <= end + 1e-8)
    ts, cs, bs = t[within], c[within], blq[within]
    if len(ts) == 0 or not (~bs).any():
        raise ValueError("Không có mẫu định lượng trong khoảng liều cuối [0, τ].")
    measured = cs[~bs]
    valid_ts = ts[~bs]
    peak = int(np.argmax(measured))
    warnings = ["Cmax/Cmin là cực trị tại các thời điểm được lấy mẫu; có thể bỏ sót đỉnh hoặc đáy thực."]
    if regimen.mode == "steady_state" and not regimen.steady_state_confirmed:
        warnings.append("Chưa xác nhận steady-state; không tính CLss hoặc CL/Fss.")
    if regimen.mode == "steady_state" and regimen.steady_state_confirmed:
        warnings.append("Steady-state do người dùng xác nhận từ bằng chứng ngoài dữ liệu chu kỳ này; phần mềm không tự xác minh.")
    complete = (len(ts) >= 2 and np.isclose(ts[0], start, atol=1e-8)
                and np.isclose(ts[-1], end, atol=1e-8) and not bs.any())
    if (settings.route == "iv_bolus" and len(ts) >= 2 and np.isclose(ts[0], start, atol=1e-8)
            and (bs[0] or cs[0] <= 0 or cs[1] > cs[0] * 1.05)):
        complete = False
        warnings.append("C(0+) của IV bolus không phù hợp với mẫu ngay sau tiêm; "
                        "cần phân biệt mẫu predose và postdose, không tính AUCτ.")
    if not complete:
        warnings.append("Thiếu mẫu đúng biên liều cuối (0 hoặc τ), hoặc có BLQ: không tính AUCτ, Cavg, fluctuation và CLss.")
    auc = (_cycle_auc(t, c, blq, start, regimen.tau_h, settings.integration)
           if complete else None)
    if auc is not None and auc <= 0:
        auc = None
        warnings.append("AUCτ không dương; không thể tính các thông số phụ thuộc AUC.")
    ratio = None
    if auc is not None and regimen.mode == "steady_state" and regimen.steady_state_confirmed and regimen.time_basis == "first_dose":
        first_auc = _cycle_auc(t, c, blq, 0.0, regimen.tau_h, settings.integration,
                               exclude_second_bolus=settings.route == "iv_bolus")
        if first_auc is not None and first_auc > 0:
            ratio = auc / first_auc
    if settings.route == "iv_bolus":
        warnings.append("Ở thời điểm tiêm IV bolus, C(0) là mẫu ngay SAU liều cuối; C(τ) là trough trước liều kế tiếp.")
    cl = None
    if (auc is not None and regimen.mode == "steady_state" and regimen.steady_state_confirmed
            and settings.dose is not None):
        cl = settings.dose * DOSE_FACTORS[settings.dose_unit] / auc / 1000
    return {
        "profile_id": str(data.profile_id.iloc[0]), "route": settings.route,
        "mode": regimen.mode, "status": "Đủ chu kỳ" if auc is not None else "NCA một phần — thiếu biên/BLQ",
        "steady_state_confirmed": regimen.steady_state_confirmed,
        "n": len(ts), "tau_h": regimen.tau_h, "last_dose_h": start,
        "cmax_tau_ng_ml": float(measured[peak]), "tmax_tau_h": float(valid_ts[peak] - start),
        "cmin_tau_ng_ml": float(measured.min()),
        "ctrough_ng_ml": float(cs[-1]) if len(ts) and np.isclose(ts[-1], end, atol=1e-8) and not bs[-1] else None,
        "auc_tau_ng_h_ml": auc, "cavg_tau_ng_ml": auc / regimen.tau_h if auc is not None else None,
        "fluctuation_pct": (100 * (measured.max() - measured.min()) / (auc / regimen.tau_h)
                            if auc is not None else None),
        "cl_ss_l_h": cl if settings.route != "oral" else None,
        "cl_over_f_ss_l_h": cl if settings.route == "oral" else None,
        "accumulation_ratio_auc": ratio, "warnings": warnings,
    }
