"""Power and balanced sample-size planning for complete replicate BE studies.

Conventional ABE is evaluated by the joint TOST integral. Reference-scaled
criteria use seeded parametric Monte Carlo applied to the same contrasts,
reference variance models, and decision gates as replicate.py.
"""

import math
from dataclasses import dataclass

import numpy as np
from scipy.stats import chi2, f, t

from be_app.design import SEQUENCES, _joint_tost_probability

REPLICATE_RULES = {
    "EMA_REPLICATE_STANDARD", "FDA_REPLICATE_STANDARD", "EMA_HVDP_ABEL",
    "FDA_HVD_RSABE_2026", "EMA_NTI", "FDA_NTI",
}


@dataclass(frozen=True)
class ReplicatePower:
    power: float
    mc_se: float
    simulations: int
    method: str


def _validate(cv_wr, cv_wt, gmr, n, design, rule_set_id, alpha, lower, upper, simulations):
    if design not in ("partial3", "full4") or rule_set_id not in REPLICATE_RULES:
        raise ValueError("Thiết kế hoặc quy tắc replicate không được hỗ trợ.")
    if rule_set_id == "FDA_NTI" and design != "full4":
        raise ValueError("FDA NTI yêu cầu full replicate 4 kỳ.")
    values = (cv_wr, cv_wt, gmr, alpha, lower, upper)
    if not all(math.isfinite(x) for x in values):
        raise ValueError("Tham số power phải hữu hạn.")
    if not (0 < cv_wr <= 5 and 0 < cv_wt <= 5 and gmr > 0
            and 0 < alpha < 0.5 and 0 < lower < upper):
        raise ValueError("CV, GMR, alpha hoặc giới hạn BE không hợp lệ.")
    if isinstance(n, bool) or not isinstance(n, int) or n < 2 * len(SEQUENCES[design]) or n % len(SEQUENCES[design]):
        raise ValueError("N phải chia hết cho số sequence, với ít nhất hai người mỗi sequence.")
    if isinstance(simulations, bool) or not isinstance(simulations, int) or simulations < 1000:
        raise ValueError("Cần ít nhất 1.000 lượt mô phỏng.")
    if rule_set_id in {"EMA_HVDP_ABEL", "FDA_HVD_RSABE_2026", "FDA_NTI"}:
        if alpha != 0.05 or lower != 0.8 or upper != 1.25:
            raise ValueError("Profile scaled yêu cầu alpha=0.05 và giới hạn nền 80–125%.")


def _design_matrices(design, per_sequence):
    """Subject-demeaned fixed-period/treatment and reference-period matrices."""
    seqs = SEQUENCES[design]
    periods = len(seqs[0])
    treatment = np.asarray([[c == "T" for c in seq] for seq in seqs])
    period_columns = np.eye(periods)[:, 1:]
    within_x = []
    within_r = []
    for trt in treatment:
        matrix = np.column_stack((period_columns, trt.astype(float)))
        within_x.append(matrix - matrix.mean(axis=0))
        ref_periods = period_columns[~trt]
        within_r.append(ref_periods - ref_periods.mean(axis=0))
    xx = per_sequence * sum((x.T @ x for x in within_x))
    rr = per_sequence * sum((x.T @ x for x in within_r))
    inv_xx = np.linalg.inv(xx)
    pinv_rr = np.linalg.pinv(rr, rcond=1e-12)
    df_ema = per_sequence * len(seqs) * (periods - 1) - periods
    df_r = per_sequence * len(seqs) - np.linalg.matrix_rank(rr)
    return treatment, within_x, within_r, inv_xx, pinv_rr, df_ema, df_r


def _simulated_decisions(cv_wr, cv_wt, gmr, n, design, rule_set_id, *,
                         lower, upper, alpha, simulations, seed, endpoint):
    seqs = SEQUENCES[design]
    groups = len(seqs)
    per_seq = n // groups
    periods = len(seqs[0])
    s_r = math.sqrt(math.log1p(cv_wr**2))
    s_t = math.sqrt(math.log1p(cv_wt**2))
    treatment, within_x, within_r, inv_xx, pinv_rr, df_ema, df_r_ema = _design_matrices(design, per_seq)
    fda = rule_set_id.startswith("FDA")
    df_i = n - groups
    critical = float(t.ppf(1 - alpha, df_i if fda else df_ema))
    success = 0
    rng = np.random.default_rng(seed)

    for offset in range(0, simulations, 1000):
        batch = min(1000, simulations - offset)
        # Shape: simulations x sequence x subjects-per-sequence x periods.
        errors = rng.standard_normal((batch, groups, per_seq, periods))
        data = errors * np.where(treatment[None, :, None, :], s_t, s_r)
        data += math.log(gmr) * treatment[None, :, None, :]

        if fda:
            i_means = []
            i_ss = 0.0
            dr_ss = 0.0
            dt_ss = 0.0
            for k in range(groups):
                records = data[:, k]
                trt = treatment[k]
                i_values = records[:, :, trt].mean(axis=-1) - records[:, :, ~trt].mean(axis=-1)
                dr = records[:, :, ~trt][:, :, 0] - records[:, :, ~trt][:, :, 1]
                i_mean = i_values.mean(axis=1)
                i_means.append(i_mean)
                i_ss += np.square(i_values - i_mean[:, None]).sum(axis=1)
                dr_ss += np.square(dr - dr.mean(axis=1, keepdims=True)).sum(axis=1)
                if design == "full4":
                    dt = records[:, :, trt][:, :, 0] - records[:, :, trt][:, :, 1]
                    dt_ss += np.square(dt - dt.mean(axis=1, keepdims=True)).sum(axis=1)
            estimate = np.mean(i_means, axis=0)
            se = np.sqrt((i_ss / df_i) / n)
            swr2 = dr_ss / (2 * df_i)
            swt2 = dt_ss / (2 * df_i) if design == "full4" else None
            df_r = df_i
        else:
            xx_y = np.zeros((batch, periods))
            rr_y = np.zeros((batch, periods - 1))
            yy = np.zeros(batch)
            rr_yy = np.zeros(batch)
            for k in range(groups):
                values = data[:, k]
                centered = values - values.mean(axis=-1, keepdims=True)
                xx_y += np.einsum("bnp,pk->bk", centered, within_x[k])
                yy += np.square(centered).sum(axis=(1, 2))
                ref_values = values[:, :, ~treatment[k]]
                centered_r = ref_values - ref_values.mean(axis=-1, keepdims=True)
                rr_y += np.einsum("bnp,pk->bk", centered_r, within_r[k])
                rr_yy += np.square(centered_r).sum(axis=(1, 2))
            beta = xx_y @ inv_xx
            estimate = beta[:, -1]
            ss = np.maximum(0.0, yy - np.einsum("bi,ij,bj->b", xx_y, inv_xx, xx_y))
            se = np.sqrt(ss / df_ema * inv_xx[-1, -1])
            ss_r = np.maximum(0.0, rr_yy - np.einsum("bi,ij,bj->b", rr_y, pinv_rr, rr_y))
            swr2 = ss_r / df_r_ema
            df_r = df_r_ema

        ci_low, ci_high = estimate - critical * se, estimate + critical * se
        log_lower, log_upper = math.log(lower), math.log(upper)
        passes = (ci_low >= log_lower) & (ci_high <= log_upper)

        if rule_set_id == "EMA_HVDP_ABEL" and endpoint == "Cmax":
            threshold = math.log1p(0.30**2)
            cap = math.log1p(0.50**2)
            widened = swr2 > threshold
            bounds = 0.760 * np.sqrt(np.minimum(swr2, cap))
            lo = np.where(widened, -bounds, math.log(0.8))
            hi = np.where(widened, bounds, math.log(1.25))
            passes = (ci_low >= lo) & (ci_high <= hi) & (np.abs(estimate) <= math.log(1.25))

        if rule_set_id in ("FDA_HVD_RSABE_2026", "FDA_NTI"):
            nti = rule_set_id == "FDA_NTI"
            theta = (math.log(1 / 0.9) / 0.1) ** 2 if nti else (math.log(1.25) / 0.25) ** 2
            x = estimate**2 - se**2
            bound_x = (np.abs(estimate) + float(t.ppf(0.95, df_i)) * se) ** 2
            y = -theta * swr2
            bound_y = y * df_r / float(chi2.ppf(0.95, df_r))
            ucb = x + y + np.hypot(bound_x - x, bound_y - y)
            scaled = (ucb <= 0) & (np.abs(estimate) <= math.log(1.25))
            if nti:
                # Independent T/R repeat-contrast residuals give the F ratio CI.
                ratio_upper = np.sqrt(swt2 / swr2 / float(f.ppf(0.05, df_i, df_r)))
                passes &= scaled & (ratio_upper <= 2.5)
            else:
                passes = np.where(np.sqrt(swr2) >= 0.294, scaled, passes)
        success += int(np.count_nonzero(passes))

    return success / simulations


def replicate_power(cv_wr: float, gmr: float, n: int, *, design: str = "partial3",
                    rule_set_id: str = "EMA_REPLICATE_STANDARD", cv_wt: float | None = None,
                    endpoint: str = "Cmax", alpha: float = 0.05,
                    lower: float = 0.8, upper: float = 1.25,
                    simulations: int = 20000, seed: int = 20261118) -> ReplicatePower:
    """Return endpoint decision probability for a balanced complete replicate design.

    Monte Carlo standard error is reported for scaled / unequal-CV variants.
    Fixed seed makes repeated computations exactly reproducible.
    """
    if cv_wt is None:
        cv_wt = cv_wr
    _validate(cv_wr, cv_wt, gmr, n, design, rule_set_id, alpha, lower, upper, simulations)
    if endpoint not in {"AUC", "Cmax"}:
        raise ValueError("Endpoint phải là AUC hoặc Cmax.")

    # Normal estimate and independent pooled chi-square error for balanced,
    # homoscedastic conventional ABE under each regulator's analysis model.
    conventional = (rule_set_id in {"EMA_REPLICATE_STANDARD", "FDA_REPLICATE_STANDARD", "EMA_NTI"}
                    or (rule_set_id == "EMA_HVDP_ABEL" and endpoint == "AUC"))
    if conventional and cv_wt == cv_wr:
        groups = len(SEQUENCES[design])
        per_seq = n // groups
        if rule_set_id.startswith("FDA"):
            variance = math.log1p(cv_wr**2) * (1.5 if design == "partial3" else 1) / n
            df = n - groups
        else:
            _, _, _, inverse, _, df, _ = _design_matrices(design, per_seq)
            variance = math.log1p(cv_wr**2) * inverse[-1, -1]
        power = _joint_tost_probability(math.log(gmr), math.sqrt(variance), df, alpha, lower, upper)
        return ReplicatePower(power, 0.0, 0, "exact_joint_TOST_replicate")

    if rule_set_id.startswith("FDA") and alpha != 0.05:
        raise ValueError("Mô phỏng FDA yêu cầu alpha=0.05.")
    power = _simulated_decisions(cv_wr, cv_wt, gmr, n, design, rule_set_id,
                                 lower=lower, upper=upper, alpha=alpha, simulations=simulations,
                                 seed=seed, endpoint=endpoint)
    return ReplicatePower(power, math.sqrt(power * (1 - power) / simulations), simulations,
                          "seeded_parametric_MC_replicate")


def replicate_sample_size(cv_wr: float, gmr: float = 0.95, target: float = 0.8, *,
                          design: str = "partial3", rule_set_id: str = "EMA_REPLICATE_STANDARD",
                          cv_wt: float | None = None, endpoint: str = "Cmax", dropout: float = 0.1,
                          minimum_per_group: int = 6, max_n: int = 10000,
                          alpha: float = 0.05, lower: float = 0.8, upper: float = 1.25,
                          simulations: int = 20000, seed: int = 20261118):
    """Smallest balanced sequence allocation meeting estimated endpoint power."""
    from be_app.design import SampleSize

    if not (0 < target < 1 and 0 <= dropout < 1 and lower < gmr < upper):
        raise ValueError("Power/dropout/GMR ngoài phạm vi giới hạn áp dụng.")
    if (isinstance(minimum_per_group, bool) or not isinstance(minimum_per_group, int)
            or minimum_per_group < 2 or not isinstance(max_n, int)):
        raise ValueError("Giới hạn cỡ mẫu không hợp lệ.")
    groups = len(SEQUENCES.get(design, ()))
    if not groups or max_n < groups * minimum_per_group:
        raise ValueError("Giới hạn N thấp hơn cỡ mẫu tối thiểu cho thiết kế.")
    cache = {}

    def at(per_group):
        if per_group not in cache:
            cache[per_group] = replicate_power(
                cv_wr, gmr, groups * per_group, design=design, rule_set_id=rule_set_id,
                cv_wt=cv_wt, endpoint=endpoint, alpha=alpha, lower=lower, upper=upper,
                simulations=simulations, seed=seed + groups * per_group,
            )
        return cache[per_group]

    floor = minimum_per_group
    ceiling = max_n // groups
    if at(floor).power >= target:
        found = floor
    else:
        below = floor
        above = floor + 1
        while above <= ceiling and at(above).power < target:
            below = above
            above = min(ceiling, above * 2)
            if above == below:
                break
        if above > ceiling or at(above).power < target:
            raise ValueError("Không tìm được N đạt power trong giới hạn tìm kiếm.")
        while above - below > 1:
            mid = (above + below) // 2
            if at(mid).power >= target:
                above = mid
            else:
                below = mid
        found = above
        # Smooth over localized simulation noise near the threshold.
        for candidate in range(max(floor, found - 3), found):
            if at(candidate).power >= target:
                found = candidate
                break

    achieved = at(found)
    return SampleSize(groups * found, groups * math.ceil(found / (1 - dropout)),
                      found, achieved.power, dropout, "CVwR / CVwT"), achieved
