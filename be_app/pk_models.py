"""One-, two-, and three-compartment concentration models and nonlinear fitting.

Oral parameters are apparent (CL/F, V/F, Q/F). All models use ng/mL,
mg-equivalent dose converted to ng, and compartment volumes in litres.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

from be_app.pk_analysis import CONCENTRATION_FACTORS, DOSE_FACTORS, PKSettings, validate_profiles

if TYPE_CHECKING:
    from be_app.pk_multiple import PKRegimen


def parameter_names(route: str, compartments: int) -> tuple[str, ...]:
    if compartments not in (1, 2, 3):
        raise ValueError("Chỉ hỗ trợ mô hình 1, 2 hoặc 3 ngăn.")
    apparent = route == "oral"
    names = ["CL/F", "V/F"] if apparent else ["CL", "Vc"]
    if compartments == 2:
        names += ["Q/F", "Vp/F"] if apparent else ["Q", "Vp"]
    elif compartments == 3:
        names += ["Q2/F", "Vp2/F", "Q3/F", "Vp3/F"] if apparent else ["Q2", "Vp2", "Q3", "Vp3"]
    if apparent:
        names.append("ka")
    return tuple(names)


def _three_compartment_spectrum(cl: float, vc: float, q2: float, vp2: float,
                                q3: float, vp3: float) -> tuple[np.ndarray, np.ndarray]:
    """Positive decay rates and central impulse weights of a mammillary model.

    The amount transfer matrix is similar to a symmetric matrix (volumes
    provide the similarity transform). Its eigenvectors therefore give
    nonnegative central coefficients, even for nearly coincident rates.
    """
    decay = np.array([
        [(cl + q2 + q3) / vc, -q2 / math.sqrt(vc * vp2), -q3 / math.sqrt(vc * vp3)],
        [-q2 / math.sqrt(vc * vp2), q2 / vp2, 0.0],
        [-q3 / math.sqrt(vc * vp3), 0.0, q3 / vp3],
    ])
    rates, vectors = np.linalg.eigh(decay)
    if not np.isfinite(rates).all() or rates[0] <= 0:
        raise ValueError("Các tốc độ suy giảm 3 ngăn không xác định được ổn định.")
    indices = np.argsort(rates)[::-1]  # alpha > beta > gamma
    fractions = np.square(vectors[0, indices])
    fractions /= fractions.sum()
    return rates[indices], fractions


def _three_compartment_derived(parameters: dict[str, float], route: str) -> dict[str, float]:
    """Microconstants, steady-state volume and macro-rate half-lives."""
    apparent = route == "oral"
    names = parameter_names(route, 3)
    cl, vc, q2, vp2, q3, vp3 = (parameters[name] for name in names[:6])
    rates, _ = _three_compartment_spectrum(cl, vc, q2, vp2, q3, vp3)
    derived = {
        "Vss/F (L)" if apparent else "Vss (L)": vc + vp2 + vp3,
        "k10 (1/giờ)": cl / vc,
        "k12 (1/giờ)": q2 / vc,
        "k21 (1/giờ)": q2 / vp2,
        "k13 (1/giờ)": q3 / vc,
        "k31 (1/giờ)": q3 / vp3,
    }
    for label, rate in zip(("α", "β", "γ"), rates, strict=True):
        derived[f"{label} (1/giờ)"] = float(rate)
        derived[f"t½,{label} (giờ)"] = float(math.log(2) / rate)
    return derived


def _kernel(t: np.ndarray, rate: float, route: str, infusion_h: float | None,
            ka: float | None) -> np.ndarray:
    if route == "iv_bolus":
        return np.exp(-rate * t)
    if route == "iv_infusion":
        if infusion_h is None:
            raise ValueError("Thiếu thời gian truyền.")
        duration = float(infusion_h)
        active = np.minimum(t, duration)
        after = np.maximum(t - duration, 0)
        return (-np.expm1(-rate * active)) / (rate * duration) * np.exp(-rate * after)
    if route == "oral":
        if ka is None:
            raise ValueError("Thiếu hằng số hấp thu ka.")
        difference = ka - rate
        if abs(difference) < 1e-7 * max(ka, rate):
            return ka * t * np.exp(-rate * t)
        return ka * (np.exp(-rate * t) - np.exp(-ka * t)) / difference
    raise ValueError("Đường dùng không hợp lệ.")


def predict(t: np.ndarray | list[float], parameters: dict[str, float],
            settings: PKSettings, compartments: int) -> np.ndarray:
    """Return predicted ng/mL for a single administered dose."""
    settings.validate()
    if settings.dose is None:
        raise ValueError("Mô hình ngăn cần biết liều dùng.")
    times = np.asarray(t, dtype=float)
    if not np.isfinite(times).all() or (times < 0).any():
        raise ValueError("Thời điểm dự đoán phải không âm và hữu hạn.")
    names = parameter_names(settings.route, compartments)
    if set(names) != set(parameters) or any(
        not np.isfinite(parameters[name]) or parameters[name] <= 0 for name in names
    ):
        raise ValueError("Thiếu tham số hoặc có tham số ngăn không dương.")
    cl, vc = (parameters[k] for k in names[:2])
    ka = parameters.get("ka")
    if compartments == 1:
        rates, fractions = [cl / vc], [1.0]
    elif compartments == 2:
        q, vp = (parameters[k] for k in names[2:4])
        k10, k12, k21 = cl / vc, q / vc, q / vp
        discriminant = (k10 + k12 + k21) ** 2 - 4 * k10 * k21
        root = math.sqrt(max(discriminant, 0.0))
        alpha = ((k10 + k12 + k21) + root) / 2
        beta = k10 * k21 / alpha  # Stable product of the two positive roots.
        if alpha == beta:
            raise ValueError("Hai hằng số lai không phân biệt được.")
        fraction_a = (alpha - k21) / (alpha - beta)
        rates, fractions = [alpha, beta], [fraction_a, 1 - fraction_a]
    else:
        q2, vp2, q3, vp3 = (parameters[k] for k in names[2:6])
        rates, fractions = _three_compartment_spectrum(cl, vc, q2, vp2, q3, vp3)
    amount_ng = settings.dose * DOSE_FACTORS[settings.dose_unit]
    conc = np.zeros_like(times, dtype=float)
    for rate, fraction in zip(rates, fractions, strict=True):
        conc += fraction * _kernel(times, rate, settings.route, settings.infusion_duration_h, ka)
    return np.maximum(amount_ng / (vc * 1000) * conc, 0.0)


def fit_compartment(frame: pd.DataFrame, settings: PKSettings, *, compartments: int = 1,
                    weighting: str = "equal", starts: int = 8,
                    regimen: PKRegimen | None = None) -> dict:
    """Constrained deterministic multistart least-squares, per independent profile.

    Weighted information criteria are descriptive only (not formal likelihood
    comparisons); compare AICc between models with the same observations/weight.
    """
    settings.validate()
    if regimen is not None:
        regimen.validate(settings)
    if settings.dose is None:
        raise ValueError("Phải khai báo liều để khớp mô hình ngăn.")
    data = validate_profiles(frame)
    if data.profile_id.nunique() != 1:
        raise ValueError("Chỉ khớp mô hình một hồ sơ tại một thời điểm.")
    names = parameter_names(settings.route, compartments)
    if weighting not in ("equal", "1/C", "1/C²"):
        raise ValueError("Trọng số không hợp lệ.")
    input_t = data.time_h.to_numpy(dtype=float)
    t = regimen.absolute_times(input_t) if regimen is not None else input_t.copy()
    y = data.concentration.to_numpy(dtype=float) * CONCENTRATION_FACTORS[settings.concentration_unit]
    if data.blq.any():
        # BLQ is censored, not a measured zero for least-squares fitting.
        kept = ~data.blq.to_numpy(dtype=bool)
        t, y, input_t = t[kept], y[kept], input_t[kept]
    excluded_iv_zero = False
    if settings.route == "iv_bolus" and len(t):
        # Zero at an IV bolus time is predose/invalid as a post-bolus observation.
        if regimen is None:
            invalid = (t == 0) & (y == 0)
        else:
            at_dose = np.isclose(np.mod(t, regimen.tau_h), 0, atol=1e-8)
            invalid = at_dose & (t < regimen.number_doses * regimen.tau_h - 1e-8) & (y == 0)
        if invalid.any():
            t, y, input_t = t[~invalid], y[~invalid], input_t[~invalid]
            excluded_iv_zero = True
    n, p = len(t), len(names)
    if n < p + 3 or (y > 0).sum() < p + 1:
        raise ValueError(f"Mô hình {compartments} ngăn cần ít nhất {p + 3} mẫu định lượng, ≥{p + 1} mẫu dương.")
    if np.ptp(t) <= 0:
        raise ValueError("Các mẫu cần trải trên nhiều thời điểm.")
    floor = float(max(np.min(y[y > 0]) / 2, 1e-8))
    scale = np.maximum(y, floor)
    denominators = {
        "equal": np.ones(n), "1/C": np.sqrt(scale), "1/C²": scale,
    }[weighting]
    # Normalize only overall scale, does not affect optimum or relative criteria.
    denominators /= np.median(denominators)
    dose_ng = settings.dose * DOSE_FACTORS[settings.dose_unit]
    v_guess = np.clip(dose_ng / (1000 * max(float(y.max()), 1e-8)), 1e-5, 1e6)
    guess_t = t if regimen is None else np.mod(t, regimen.tau_h)
    typical_t = max(float(np.median(guess_t[guess_t > 0])), 1e-3) if (guess_t > 0).any() else 1.0
    cl_guess = np.clip(v_guess / typical_t, 1e-7, 1e7)
    start_values = [cl_guess, v_guess]
    if compartments == 2:
        start_values += [cl_guess, v_guess * 2]
    elif compartments == 3:
        start_values += [cl_guess * 2, v_guess * 1.5, cl_guess / 2, v_guess * 4]
    if settings.route == "oral":
        start_values.append(2 / typical_t)
    lower = np.array([1e-10] * p, dtype=float)
    upper = np.array([1e10] * p, dtype=float)
    if settings.route == "oral":
        lower[-1], upper[-1] = 1e-6, 1e4
    low_log, high_log = np.log(lower), np.log(upper)
    base = np.log(np.clip(start_values, lower * 10, upper / 10))

    def errors(log_params: np.ndarray) -> np.ndarray:
        values = dict(zip(names, np.exp(log_params), strict=True))
        try:
            if regimen is None:
                pred = predict(t, values, settings, compartments)
            else:
                from be_app.pk_multiple import predict_multiple
                pred = predict_multiple(t, values, settings, compartments, regimen)
        except (ValueError, OverflowError, FloatingPointError, np.linalg.LinAlgError):
            return np.full(n, 1e30)
        return (pred - y) / denominators

    rng = np.random.default_rng(20261102)
    best = None
    # Three-compartment fitting has additional local minima and equivalent
    # peripheral-label permutations; use more deterministic initializations.
    number_starts = max(starts, 16) if compartments == 3 else starts
    for index in range(max(1, min(number_starts, 25))):
        attempt = base if index == 0 else np.clip(base + rng.normal(0, 1.4, p), low_log + .01, high_log - .01)
        fit = least_squares(errors, attempt, bounds=(low_log, high_log), max_nfev=2500,
                            x_scale="jac", ftol=1e-9, xtol=1e-9, gtol=1e-9)
        if np.isfinite(fit.cost) and (best is None or fit.cost < best.cost):
            best = fit
    if best is None or not best.success:
        raise ValueError("Bộ tối ưu chưa hội tụ; cần kiểm tra dữ liệu và mô hình.")
    params = dict(zip(names, np.exp(best.x).tolist(), strict=True))
    if compartments == 3:
        # The two peripheral compartments are exchangeable. Display the one
        # with faster return (k21) as compartment 2 for reproducible labels.
        suffix = "/F" if settings.route == "oral" else ""
        q2, vp2 = params[f"Q2{suffix}"], params[f"Vp2{suffix}"]
        q3, vp3 = params[f"Q3{suffix}"], params[f"Vp3{suffix}"]
        if q2 / vp2 < q3 / vp3:
            params.update({f"Q2{suffix}": q3, f"Vp2{suffix}": vp3,
                           f"Q3{suffix}": q2, f"Vp3{suffix}": vp2})
    # In a single-compartment Bateman curve, swapping ka and k leaves the
    # concentration profile unchanged after a corresponding V/F adjustment.
    # Use the fast-absorption branch for a stable display, and disclose the
    # equally valid flip-flop branch rather than claiming structural identity.
    flip_flop = settings.route == "oral" and compartments == 1
    if flip_flop and params["ka"] < params["CL/F"] / params["V/F"]:
        elimination_before = params["CL/F"] / params["V/F"]
        params["V/F"] = params["CL/F"] / params["ka"]
        params["ka"] = elimination_before
    if regimen is None:
        predicted = predict(t, params, settings, compartments)
    else:
        from be_app.pk_multiple import predict_multiple
        predicted = predict_multiple(t, params, settings, compartments, regimen)
    residual = y - predicted
    rss = float(np.dot(residual, residual))
    weighted_rss = float(np.dot(best.fun, best.fun))
    rss_for_ic = weighted_rss if weighting != "equal" else rss
    ll_term = n * math.log(max(rss_for_ic / n, 1e-300))
    aic = ll_term + 2 * p
    aicc = aic + 2 * p * (p + 1) / (n - p - 1) if n > p + 1 else None
    jacobian = best.jac
    rank = int(np.linalg.matrix_rank(jacobian))
    singular = np.linalg.svd(jacobian, compute_uv=False)
    condition = float(singular[0] / max(singular[-1], 1e-30))
    warnings: list[str] = []
    if excluded_iv_zero:
        warnings.append("Đã loại mẫu t=0 có nồng độ bằng 0 khi khớp IV bolus "
                        "vì không đại diện C(0+) ngay sau tiêm." if regimen is None else
                        "Đã loại mẫu nồng độ 0 đúng thời điểm tiêm IV bolus "
                        "vì không đại diện C(0+) ngay sau tiêm.")
    if regimen is not None:
        warnings.append("Đã khớp theo chồng chất tuyến tính các liều bằng nhau; mô hình không xét phi tuyến hoặc thay đổi liều.")
    if rank < p or condition > 1e8:
        warnings.append("Tham số có nguy cơ không định danh (Jacobian thiếu hạng hoặc điều kiện kém).")
    if compartments == 3:
        if n < 15:
            warnings.append("Mô hình 3 ngăn có ít hơn 15 mẫu định lượng; cần kiểm tra đủ các pha sớm, giữa và muộn.")
        suffix = "/F" if settings.route == "oral" else ""
        k21 = params[f"Q2{suffix}"] / params[f"Vp2{suffix}"]
        k31 = params[f"Q3{suffix}"] / params[f"Vp3{suffix}"]
        if abs(k21 - k31) / max(k21, k31) < 0.05:
            warnings.append("Hai ngăn ngoại vi có tốc độ quay về gần nhau; khó phân biệt mô hình 3 ngăn với 2 ngăn.")
    if np.any(best.x - low_log < .02) or np.any(high_log - best.x < .02):
        warnings.append("Có tham số chạm gần biên tối ưu; cần rà soát dữ liệu và mô hình.")
    if weighting != "equal":
        warnings.append("AIC/AICc/BIC theo sai số có trọng số chỉ mang tính chẩn đoán; không là likelihood chuẩn hóa.")
    if flip_flop:
        warnings.append("Mô hình uống 1 ngăn có nghiệm hoán đổi ka/k (flip-flop) tương đương; "
                        "hiển thị nhánh ka ≥ k theo quy ước, không chứng minh cơ chế hấp thu.")
    if settings.route == "oral":
        warnings.append("Thông số oral là CL/F, V/F và Q/F biểu kiến; F không suy ra từ một đường uống.")
    return {
        "profile_id": str(data.profile_id.iloc[0]), "route": settings.route,
        "compartments": compartments, "weighting": weighting, "n": n, "p": p,
        "parameters": params,
        "derived_parameters": (_three_compartment_derived(params, settings.route)
                               if compartments == 3 else {}),
        "rmse_ng_ml": math.sqrt(rss / n),
        "rss": rss, "weighted_rss": weighted_rss, "aic": aic,
        "aicc": aicc, "bic": ll_term + p * math.log(n),
        "r2": float(1 - rss / np.sum((y - y.mean()) ** 2)) if np.ptp(y) else None,
        "jacobian_rank": rank, "jacobian_condition": condition,
        "converged": bool(best.success), "warnings": warnings,
        "observed": y.tolist(), "time_h": input_t.tolist(),
        "predicted": predicted.tolist(), "residuals": residual.tolist(),
    }
