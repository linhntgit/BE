"""Single-dose noncompartmental analysis with explicit failure and terminal diagnostics."""

import math

import numpy as np
import pandas as pd
from scipy.stats import linregress

from be_app import __version__
from be_app.domain import NcaConfig, digest

PROFILE_KEYS = ("subject_id", "sequence", "period", "treatment", "analyte")


def terminal_eligible_times(frame):
    ordered = frame.sort_values("actual_time_h")
    times = ordered.actual_time_h.to_numpy(dtype=float)
    concentrations = ordered.concentration.to_numpy(dtype=float).copy()
    concentrations[ordered.blq_flag.to_numpy(dtype=bool)] = 0
    positive = np.flatnonzero(concentrations > 0)
    if not len(positive):
        return []
    last_peak = np.flatnonzero(concentrations == concentrations.max())[-1]
    zeros = np.flatnonzero(concentrations[: positive[-1] + 1] == 0)
    start = max(last_peak, int(zeros[-1]) if len(zeros) else -1)
    return times[positive[positive > start]].tolist()


def profile_identity(frame):
    return {key: str(frame.iloc[0][key]) for key in PROFILE_KEYS}


def profile_data_hash(frame):
    columns = [k for k in ("sample_id", "actual_time_h", "concentration", "blq_flag", "lloq") if k in frame]
    ordered = frame.sort_values("actual_time_h")[columns]
    return digest(ordered.astype(object).where(pd.notna(ordered), None).to_dict("records"))


def effective_nca_config(config, frame):
    identity = profile_identity(frame)
    override = next(
        (o for o in config.terminal_overrides if all(getattr(o, k) == v for k, v in identity.items())), None
    )
    updates: dict = {"terminal_overrides": ()}
    if override is not None:
        if override.profile_data_hash != profile_data_hash(frame):
            raise ValueError(
                "Dữ liệu profile đã đổi sau lựa chọn terminal; cần rà soát và áp dụng lại lựa chọn."
            )
        updates.update(manual_terminal_times=override.times, manual_reason=override.reason)
    return config.model_copy(update=updates), override


def validate_terminal_overrides(config, data):
    if not config.terminal_overrides:
        return
    matched = 0
    for _, group in data.groupby(list(PROFILE_KEYS), sort=False):
        _, override = effective_nca_config(config, group)
        if override is not None:
            if len(override.times) < config.terminal_min_points or not set(override.times) <= set(
                terminal_eligible_times(group)
            ):
                raise ValueError(
                    "Lựa chọn terminal không đủ điểm hợp lệ sau Tmax/BLQ theo cấu hình hiện tại."
                )
            matched += 1
    if matched != len(config.terminal_overrides):
        raise ValueError("Lựa chọn terminal thuộc profile không còn có trong dữ liệu; cần rà soát.")


def integrate_auc(times, concentrations, method: str = "linear_up_log_down") -> float:
    t = np.asarray(times, dtype=float)
    c = np.asarray(concentrations, dtype=float)
    if method not in ("linear", "linear_up_log_down"):
        raise ValueError("Phương pháp AUC không hợp lệ.")
    if len(t) != len(c) or len(t) < 2 or not np.isfinite(t).all() or not np.isfinite(c).all():
        raise ValueError("AUC cần ít nhất hai cặp thời gian–nồng độ hữu hạn.")
    if (np.diff(t) <= 0).any() or (c < 0).any():
        raise ValueError("Thời gian phải tăng nghiêm ngặt và nồng độ không âm.")
    areas = []
    for dt, c1, c2 in zip(np.diff(t), c[:-1], c[1:], strict=False):
        if method == "linear_up_log_down" and c1 > c2 > 0:
            area = dt * (c1 - c2) / math.log1p((c1 - c2) / c2)
        else:
            area = dt * (c1 + c2) / 2
        areas.append(float(area))
    return math.fsum(areas)


def cumulative_areas(times, concentrations, method="linear_up_log_down"):
    """Cumulative AUC and first moment using the selected trapezoidal integration rule."""
    integrate_auc(times, concentrations, method)  # Validate the entire curve first.
    auc, aumc = [0.0], [0.0]
    for t1, t2, c1, c2 in zip(times[:-1], times[1:], concentrations[:-1], concentrations[1:], strict=True):
        dt = t2 - t1
        if method == "linear_up_log_down" and c1 > c2 > 0:
            log_ratio = math.log1p((c1 - c2) / c2)
            area = dt * (c1 - c2) / log_ratio
            # Integral of t*C(t) under exponential interpolation. Use a series near equality.
            if log_ratio < 1e-3:
                moment_fraction = math.fsum(
                    (-log_ratio) ** k / (math.factorial(k) * (k + 2)) for k in range(10)
                )
                moment = t1 * area + c1 * dt**2 * moment_fraction
            else:
                moment = dt * (t1 * c1 - t2 * c2) / log_ratio + dt**2 * (c1 - c2) / log_ratio**2
        else:
            area = dt * (c1 + c2) / 2
            moment = dt * (t1 * c1 + t2 * c2) / 2
        auc.append(math.fsum((auc[-1], float(area))))
        aumc.append(math.fsum((aumc[-1], float(moment))))
    return auc, aumc


def analyze_profile(
    frame: pd.DataFrame, config: NcaConfig | None = None, *, dose: float | None = None, dose_unit="mg"
) -> dict:
    cfg = config or NcaConfig()
    result: dict = {
        "status": "NOT EVALUABLE",
        "warnings": [],
        "reason": "",
        "engine_version": __version__,
        "config": cfg.model_dump(mode="json"),
        "terminal_candidates": [],
        "cmax": None,
        "tmax": None,
        "auc_last": None,
        "auc_inf": None,
        "lambda_z": None,
        "half_life": None,
        "auc_extrap_pct": None,
        "auc_fraction_observed": None,
        "clast": None,
        "tlast": None,
        "n_samples": len(frame),
        "dose": dose,
        "dose_unit": dose_unit,
        "tlag": None,
        "auc_all": None,
        "aumc_last": None,
        "mrt_last": None,
        "clast_pred": None,
        "auc_inf_pred": None,
        "auc_extrap_pct_pred": None,
        "aumc_inf": None,
        "aumc_inf_pred": None,
        "aumc_extrap_pct": None,
        "aumc_extrap_pct_pred": None,
        "mrt_inf": None,
        "mrt_inf_pred": None,
        "cl_f": None,
        "cl_f_pred": None,
        "vz_f": None,
        "vz_f_pred": None,
        "profile_points": [],
    }
    required = {"actual_time_h", "concentration", "blq_flag"}
    if not required <= set(frame.columns) or len(frame) < 2:
        result["reason"] = "Thiếu cột hoặc thiếu mẫu cho NCA."
        return result
    if "sample_status" in frame and not frame.sample_status.isin(["VALID", "BLQ"]).all():
        result["reason"] = "Mẫu thiếu/từ chối/phân tích lại chưa có quyết định xử lý."
        return result
    try:
        if dose is not None and (not math.isfinite(dose) or dose <= 0):
            raise ValueError("Liều NCA phải hữu hạn và lớn hơn zero.")
        data = frame.sort_values("actual_time_h").copy()
        times = data.actual_time_h.to_numpy(dtype=float)
        conc = data.concentration.to_numpy(dtype=float)
        if not data.blq_flag.map(lambda x: isinstance(x, (bool, np.bool_))).all():
            raise ValueError("BLQ cần cờ boolean đã QC.")
        blq = data.blq_flag.to_numpy(dtype=bool)
        if not np.isfinite(times).all() or (np.diff(times) <= 0).any() or times[0] != 0:
            raise ValueError("Cần baseline actual time=0, thời gian hữu hạn tăng và không trùng.")
        if (conc[~np.isnan(conc)] < 0).any() or not np.isfinite(conc[~blq]).all():
            raise ValueError("Nồng độ âm/thiếu/không hữu hạn không được thay thành zero.")
        if np.isinf(conc).any():
            raise ValueError("Nồng độ vô hạn.")
        conc[blq] = 0.0
        measurable = np.flatnonzero((conc > 0) & ~blq)
        if len(measurable) == 0:
            raise ValueError("Không có nồng độ định lượng dương.")
        last = measurable[-1]
        if last < 1:
            raise ValueError("Không đủ điểm tính AUC sau liều.")
        cmax = float(conc.max())
        peaks = np.flatnonzero(conc == cmax)
        auc, aumc = cumulative_areas(times, conc, cfg.integration)
        result.update(
            cmax=cmax,
            tmax=float(times[peaks[0] if cfg.tmax_tie == "first" else peaks[-1]]),
            clast=float(conc[last]),
            tlast=float(times[last]),
            auc_last=auc[last],
            auc_all=auc[-1],
            aumc_last=aumc[last],
            mrt_last=aumc[last] / auc[last] if auc[last] > 0 else None,
            tlag=float(times[measurable[0] - 1]) if measurable[0] else 0.0,
            status="EVALUABLE",
        )
        result["profile_points"] = [
            dict(
                time=float(t),
                concentration=float(c),
                auc=a,
                aumc=m,
                terminal=False,
                predicted=None,
                residual=None,
                weighting=0,
            )
            for t, c, a, m in zip(times, conc, auc, aumc, strict=True)
        ]
        postdose = np.flatnonzero(times > 0)
        if len(postdose) and conc[postdose[0]] == cmax:
            result["warnings"].append("Cmax ở mẫu đầu sau liều; cần rà soát vùng hấp thu.")
        if conc[0] > 0.05 * cmax:
            result["warnings"].append("Predose >5% Cmax: cần quyết định population theo guideline.")
            result["status"] = "NOT EVALUABLE"
            result["reason"] = "Predose >5% Cmax chưa được giải quyết."

        eligible = measurable[measurable > peaks[-1]]
        # A terminal suffix must not bridge an internal BLQ interval silently.
        if len(eligible):
            zeros = np.flatnonzero(conc[: last + 1] == 0)
            if len(zeros):
                eligible = eligible[eligible > zeros[-1]]
        if cfg.manual_terminal_times:
            requested = np.asarray(cfg.manual_terminal_times)
            selected = np.flatnonzero(np.isin(times, requested))
            if (
                len(set(requested)) != len(requested)
                or len(selected) != len(requested)
                or not np.isin(selected, eligible).all()
            ):
                result["warnings"].append("Điểm terminal thủ công không hợp lệ hoặc chứa Tmax/BLQ.")
                return result
            segments = [selected]
        else:
            segments = [eligible[start:] for start in range(len(eligible) - cfg.terminal_min_points + 1)]
        best = None
        for indices in segments:
            if len(indices) < cfg.terminal_min_points:
                continue
            fit = linregress(times[indices], np.log(conc[indices]))
            if not np.isfinite([fit.slope, fit.intercept, fit.rvalue]).all():
                result["terminal_candidates"].append(
                    dict(
                        times=times[indices].tolist(),
                        n=len(indices),
                        valid=False,
                        reason="Hồi quy không xác định (ví dụ nồng độ hằng).",
                    )
                )
                continue
            adjusted = 1 - (1 - fit.rvalue**2) * (len(indices) - 1) / (len(indices) - 2)
            kel = float(-fit.slope)
            half = math.log(2) / kel if kel > 0 else None
            span = float((times[indices[-1]] - times[indices[0]]) / half) if half else 0.0
            valid = (
                kel > 0 and adjusted >= cfg.terminal_min_adj_r2 and span >= cfg.terminal_min_span_half_lives
            )
            candidate = dict(
                times=times[indices].tolist(),
                n=len(indices),
                slope=float(fit.slope),
                intercept=float(fit.intercept),
                r2=float(fit.rvalue**2),
                corr_xy=float(fit.rvalue),
                adjusted_r2=float(adjusted),
                span_half_lives=span,
                valid=bool(valid),
            )
            result["terminal_candidates"].append(candidate)
            if valid and (best is None or adjusted > best["adjusted_r2"] + 1e-4):
                best = candidate
        if best is None:
            result["warnings"].append("Lambda-z không đủ bằng chứng; không tính AUCinf/t1/2.")
            return result
        kel = -best["slope"]
        auc_inf = result["auc_last"] + result["clast"] / kel
        result.update(
            lambda_z=kel,
            half_life=math.log(2) / kel,
            auc_inf=auc_inf,
            auc_extrap_pct=100 * (auc_inf - result["auc_last"]) / auc_inf,
            auc_fraction_observed=result["auc_last"] / auc_inf,
            terminal_selected=best,
        )
        pred = math.exp(best["intercept"] - kel * result["tlast"])
        result["clast_pred"] = pred
        result["auc_inf_pred"] = result["auc_last"] + pred / kel
        result["auc_extrap_pct_pred"] = 100 * (pred / kel) / result["auc_inf_pred"]
        dose_ng = {"g": 1e9, "mg": 1e6, "ug": 1e3, "µg": 1e3, "μg": 1e3, "ng": 1}.get(dose_unit)
        for suffix, tail_conc, total_auc in (
            ("", result["clast"], auc_inf),
            ("_pred", pred, result["auc_inf_pred"]),
        ):
            tail_moment = tail_conc * (result["tlast"] / kel + 1 / kel**2)
            total_moment = result["aumc_last"] + tail_moment
            result["aumc_inf" + suffix] = total_moment
            result["aumc_extrap_pct" + suffix] = 100 * tail_moment / total_moment
            result["mrt_inf" + suffix] = total_moment / total_auc
            if dose is not None and dose_ng is not None:
                result["cl_f" + suffix] = dose * dose_ng / total_auc
                result["vz_f" + suffix] = result["cl_f" + suffix] / kel
        if dose is not None and dose_ng is None:
            result["warnings"].append("Đơn vị liều chưa hỗ trợ quy đổi khối lượng; không tính CL/F và Vz/F.")
        for point in result["profile_points"]:
            point["terminal"] = point["time"] in best["times"]
            if point["terminal"]:
                point["predicted"] = math.exp(best["intercept"] - kel * point["time"])
                point["residual"] = point["concentration"] - point["predicted"]
                point["weighting"] = 1
        if result["auc_extrap_pct"] > cfg.extrapolation_warning_pct:
            result["warnings"].append("AUC ngoại suy vượt ngưỡng QC theo cấu hình; cần rà soát.")
    except (ValueError, TypeError, ArithmeticError) as exc:
        result["status"] = "NOT EVALUABLE"
        result["reason"] = str(exc)
    return result


def analyze_dataset(data: pd.DataFrame, config: NcaConfig, *, dose=None, dose_unit="mg") -> list[dict]:
    keys = ["study_id", "subject_id", "sequence", "period", "treatment", "analyte"]
    rows = []
    for values, frame in data.groupby(keys, sort=True, dropna=False):
        effective, override = effective_nca_config(config, frame)
        result = analyze_profile(frame, effective, dose=dose, dose_unit=dose_unit)
        if override is not None:
            result["terminal_review"] = override.model_dump(mode="json")
        result.update(
            {
                key: value.item() if isinstance(value, np.generic) else value
                for key, value in zip(keys, values, strict=False)
            }
        )
        result["concentration_unit"] = "ng/mL"
        result["auc_unit"] = "ng*h/mL"
        rows.append(result)
    return rows
