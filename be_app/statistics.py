"""ABE contrasts for complete 2x2 and independent parallel observations."""

import math

import numpy as np
import pandas as pd
from scipy.stats import t

from be_app.be_diagnostics import crossover_tables
from be_app.domain import BeConfig, BeResult


def _result(endpoint, data, estimate, se, df, cfg, diagnostics, cv=None):
    if not all(math.isfinite(x) for x in (estimate, se, df)) or se <= 1e-14 or df <= 0:
        return BeResult(endpoint=endpoint, reason="Phương sai suy biến hoặc không đủ bậc tự do.")
    q = t.ppf(1 - cfg.alpha, df)
    low_log, high_log = estimate - q * se, estimate + q * se
    if max(abs(low_log), abs(high_log)) > 700:
        return BeResult(endpoint=endpoint, reason="Khoảng tin cậy vượt miền tính số ổn định.")
    low, high = math.exp(low_log), math.exp(high_log)
    return BeResult(
        endpoint=endpoint,
        n=int(data.subject_id.nunique()),
        estimate=float(estimate),
        se=float(se),
        df=float(df),
        gmr=math.exp(estimate),
        ci_lower=low,
        ci_upper=high,
        p_lower=float(t.sf((estimate - math.log(cfg.lower)) / se, df)),
        p_upper=float(t.cdf((estimate - math.log(cfg.upper)) / se, df)),
        cv_within=cv,
        geometric_mean_t=float(np.exp(np.log(data.loc[data.treatment == "T", endpoint]).mean())),
        geometric_mean_r=float(np.exp(np.log(data.loc[data.treatment == "R", endpoint]).mean())),
        n_observations=len(data),
        ci80_lower=math.exp(estimate - t.ppf(0.9, df) * se),
        ci80_upper=math.exp(estimate + t.ppf(0.9, df) * se),
        ci95_lower=math.exp(estimate - t.ppf(0.975, df) * se),
        ci95_upper=math.exp(estimate + t.ppf(0.975, df) * se),
        lower_limit=cfg.lower,
        upper_limit=cfg.upper,
        criteria=[
            dict(
                criterion=f"CI {(1 - 2 * cfg.alpha) * 100:g}% within acceptance limits",
                value=[low, high],
                limits=[cfg.lower, cfg.upper],
                passed=bool(low >= cfg.lower and high <= cfg.upper),
            )
        ],
        decision="PASS" if low >= cfg.lower and high <= cfg.upper else "FAIL",
        diagnostics=diagnostics,
    )


def analyze_abe(data: pd.DataFrame, endpoint: str, design: str, config: BeConfig | None = None) -> BeResult:
    cfg = config or BeConfig()

    def ne(reason):
        return BeResult(endpoint=endpoint, reason=reason)

    if design not in ("2x2", "parallel"):
        return ne("Chưa hỗ trợ mô hình replicate; không dùng mô hình 2×2 cho dữ liệu lặp lại.")
    columns = {"subject_id", "sequence", "period", "treatment", endpoint}
    if not columns <= set(data.columns) or data.empty:
        return ne("Thiếu dữ liệu hoặc cột endpoint/thiết kế.")
    if design == "2x2" and cfg.missing_policy == "available_observations":
        return analyze_mixed_abe(data, endpoint, cfg)
    d = data.copy()
    values = pd.to_numeric(d[endpoint], errors="coerce")
    if (
        d[list(columns - {endpoint})].isna().any().any()
        or not np.isfinite(values).all()
        or (values <= 0).any()
    ):
        return ne("PK phải dương, hữu hạn và đủ định danh; không tự loại giá trị thiếu.")
    d[endpoint] = values
    if not set(d.treatment) <= {"T", "R"} or set(d.treatment) != {"T", "R"}:
        return ne("Cần đúng hai treatment T và R.")
    if d.duplicated(["subject_id", "period"]).any() or d.groupby("subject_id").sequence.nunique().gt(1).any():
        return ne("Trùng kỳ hoặc subject có nhiều sequence.")
    if design == "2x2":
        if set(d.sequence) != {"TR", "RT"} or set(d.period) != {1, 2}:
            return ne("2×2 cần hai sequence TR/RT và kỳ 1/2.")
        if d.groupby("subject_id").size().ne(2).any():
            return ne("Mất kỳ: cần mô hình đã xác nhận riêng; không tự xóa subject.")
        if any(row.treatment != row.sequence[int(row.period) - 1] for row in d.itertuples()):
            return ne("Treatment không khớp sequence/kỳ.")
        table = d.pivot(index=["subject_id", "sequence"], columns="treatment", values=endpoint)
        if table.isna().any().any():
            return ne("Thiếu treatment trong một subject.")
        diffs = np.log(table.T.loc["T"]) - np.log(table.T.loc["R"])
        groups = [diffs.xs(seq, level="sequence") for seq in ("TR", "RT")]
        n1, n2 = (len(g) for g in groups)
        if min(n1, n2) < 2:
            return ne("Mỗi sequence cần ít nhất hai người.")
        means = [float(g.mean()) for g in groups]
        residuals = [float(x - mean) for g, mean in zip(groups, means, strict=False) for x in g]
        variance_d = math.fsum(x * x for x in residuals) / (n1 + n2 - 2)
        delta = sum(means) / 2
        se = math.sqrt(variance_d * 0.25 * (1 / n1 + 1 / n2))
        mse = variance_d / 2
        diagnostics = dict(
            model="subject(sequence) + period + treatment; reduced within-subject contrasts",
            n_TR=n1,
            n_RT=n2,
            sequence_difference_means=means,
            mse=mse,
            residual_ss=mse * (n1 + n2 - 2),
            period_2_minus_1=(means[1] - means[0]) / 2,
            residuals_difference=residuals,
            contrast_covariance=[[variance_d / n1, 0], [0, variance_d / n2]],
            geometric_means="descriptive, unadjusted",
        )
        result = _result(
            endpoint,
            d,
            delta,
            se,
            n1 + n2 - 2,
            cfg,
            diagnostics,
            math.sqrt(math.expm1(mse)) if mse < 700 else None,
        )
        if result.estimate is not None:
            result = attach_crossover_tables(result, d, endpoint, cfg)
        return result
    if d.subject_id.duplicated().any():
        return ne("Parallel chỉ có một endpoint mỗi subject.")
    if set(d.period) != {1} or not (d.sequence == d.treatment).all():
        return ne("Parallel cần period=1 và sequence bằng treatment.")
    groups = [np.log(d.loc[d.treatment == trt, endpoint].to_numpy()) for trt in ("T", "R")]
    a, b = groups
    n1, n2 = len(a), len(b)
    if min(n1, n2) < 2:
        return ne("Mỗi nhánh cần ít nhất hai người.")
    v1, v2 = float(a.var(ddof=1)), float(b.var(ddof=1))
    if cfg.parallel_variance == "pooled":
        variance = ((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2)
        se = math.sqrt(variance * (1 / n1 + 1 / n2))
        df: float = n1 + n2 - 2
    else:
        se = math.sqrt(v1 / n1 + v2 / n2)
        denominator = (v1 / n1) ** 2 / (n1 - 1) + (v2 / n2) ** 2 / (n2 - 1)
        df = se**4 / denominator if denominator > 0 else 0
    return _result(
        endpoint,
        d,
        float(a.mean() - b.mean()),
        se,
        df,
        cfg,
        dict(
            model=f"parallel {cfg.parallel_variance}",
            n_T=n1,
            n_R=n2,
            log_variance_T=v1,
            log_variance_R=v2,
            residuals=[*(a - a.mean()).tolist(), *(b - b.mean()).tolist()],
            geometric_means="descriptive, unadjusted",
        ),
    )


def attach_crossover_tables(result, data, endpoint, cfg, tables=None):
    detailed = tables if tables is not None else crossover_tables(data, endpoint, cfg.lower, cfg.upper)
    r, trt = detailed["lsm_r"], detailed["lsm_t"]
    return result.model_copy(
        update=dict(
            diagnostics={**result.diagnostics, **detailed},
            lsmean_log_r=r["estimate"],
            lsmean_log_t=trt["estimate"],
            adjusted_geometric_mean_r=math.exp(r["estimate"]),
            adjusted_geometric_mean_t=math.exp(trt["estimate"]),
            cv_between=detailed["variance_parameters"]["cv_between"],
        )
    )


def analyze_mixed_abe(data, endpoint, cfg):
    """Explicit SAP-authorized available-observation REML; never silently complete-case."""
    try:
        d = data.copy()
        ids = ["subject_id", "sequence", "period", "treatment"]
        if d[ids].isna().any().any() or d.duplicated(["subject_id", "period"]).any():
            raise ValueError("Thiếu định danh hoặc trùng subject/kỳ.")
        if set(d.sequence) != {"TR", "RT"} or not set(d.period) <= {1, 2}:
            raise ValueError("REML này cần hai sequence TR/RT, period 1/2.")
        if d.groupby("subject_id").sequence.nunique().gt(1).any():
            raise ValueError("Subject có nhiều sequence.")
        if any(r.treatment != r.sequence[int(r.period) - 1] for r in d.itertuples()):
            raise ValueError("Treatment không khớp sequence/kỳ.")
        values = pd.to_numeric(d[endpoint], errors="coerce")
        if ((values.notna()) & ((values <= 0) | ~np.isfinite(values))).any():
            raise ValueError("PK không dương hoặc không hữu hạn.")
        if (d[endpoint].notna() & values.isna()).any():
            raise ValueError("PK không phải số; không được tự coi là missing.")
        excluded = d.loc[values.isna(), ids].to_dict("records")
        d[endpoint] = values
        d = d.loc[values.notna()].copy()
        if set(d.treatment) != {"T", "R"} or d.groupby("sequence").subject_id.nunique().min() < 2:
            raise ValueError("Không đủ subject trong mỗi sequence/treatment.")
        tables = crossover_tables(d, endpoint, cfg.lower, cfg.upper)
        c = tables["difference"]
        tables.update(
            excluded_observations=excluded,
            missing_policy=cfg.missing_policy,
            missing_data_reason=cfg.missing_data_reason,
            missing_assumption="Available-observation likelihood requires a defensible missing-at-random assumption.",
        )
        result = _result(
            endpoint,
            d,
            c["estimate"],
            c["se"],
            c["df"],
            cfg,
            tables,
            tables["variance_parameters"]["cv_within"],
        )
        result = attach_crossover_tables(result, d, endpoint, cfg, tables)
        return result.model_copy(update={"n_excluded": len(excluded), "method": "ABE/REML/Satterthwaite"})
    except (ValueError, ArithmeticError, np.linalg.LinAlgError) as exc:
        return BeResult(endpoint=endpoint, method="ABE/REML/Satterthwaite", reason=str(exc))


def aggregate_decision(
    results: list[BeResult], required: tuple[str, ...], blockers: list[str] | None = None
) -> str:
    if blockers or not required:
        return "NOT EVALUABLE"
    if len(results) != len(required) or len({r.endpoint for r in results}) != len(results):
        return "NOT EVALUABLE"
    index = {r.endpoint: r for r in results}
    if any(e not in index or index[e].decision == "NOT EVALUABLE" for e in required):
        return "NOT EVALUABLE"
    return "PASS" if all(index[e].decision == "PASS" for e in required) else "FAIL"


def ema_abel_limits(swr: float, endpoint: str = "cmax") -> tuple[float, float]:
    """Formula helper only; not a validated replicate statistical test."""
    if not math.isfinite(swr) or swr < 0:
        raise ValueError("sWR phải hữu hạn và không âm.")
    if endpoint != "cmax" or swr <= math.sqrt(math.log1p(0.3**2)):
        return 0.8, 1.25
    scaled = 0.760 * min(swr, math.sqrt(math.log1p(0.5**2)))
    return max(0.6984, math.exp(-scaled)), min(1.4319, math.exp(scaled))


def fda_hvd_branch(swr: float, nti: bool = False) -> dict:
    if nti:
        raise ValueError("FDA NTI chưa hỗ trợ và không được dùng tham số HVD.")
    if not math.isfinite(swr) or swr < 0:
        raise ValueError("sWR không hợp lệ.")
    return dict(
        branch="ABE" if swr < 0.294 else "RSABE",
        theta=(math.log(1.25) / 0.25) ** 2,
        supported=False,
        decision="NOT EVALUABLE",
        reason="Thiếu adapter và benchmark Appendix G.",
    )
