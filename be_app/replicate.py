"""EMA Method A and FDA Appendix F/G for complete supported replicate designs."""

import math

import numpy as np
import pandas as pd
from scipy.stats import chi2, f, t

from be_app.domain import BeConfig, BeResult, Study
from be_app.mixed import ols, ols_test
from be_app.statistics import _result, analyze_abe, ema_abel_limits

SEQUENCES = {"partial3": ("TRR", "RTR", "RRT"), "full4": ("TRTR", "RTRT")}


def prepare_replicate(data, endpoint, design):
    if design not in SEQUENCES:
        raise ValueError("Cần partial3 TRR/RTR/RRT hoặc full4 TRTR/RTRT.")
    keys = ["subject_id", "sequence", "period", "treatment"]
    if not set([*keys, endpoint]) <= set(data.columns) or data.empty:
        raise ValueError("Thiếu cột PK hoặc định danh replicate.")
    d = data.copy().reset_index(drop=True)
    if d[keys].isna().any().any() or d.duplicated(["subject_id", "period"]).any():
        raise ValueError("Thiếu định danh hoặc trùng kỳ trong subject.")
    values = pd.to_numeric(d[endpoint], errors="coerce")
    if not np.isfinite(values).all() or (values <= 0).any():
        raise ValueError("Replicate cần endpoint dương và hữu hạn ở mọi kỳ; không tự loại missing.")
    d[endpoint] = values
    expected_sequences = set(SEQUENCES[design])
    if set(d.sequence) != expected_sequences:
        raise ValueError("Thiếu sequence hoặc sequence ngoài thiết kế hỗ trợ.")
    periods = len(SEQUENCES[design][0])
    if set(d.period) != set(range(1, periods + 1)) or d.groupby("subject_id").size().ne(periods).any():
        raise ValueError("Hiện cần profile replicate đủ kỳ; không suy luận bằng mô hình 2×2.")
    if d.groupby("subject_id").sequence.nunique().gt(1).any():
        raise ValueError("Một subject có nhiều sequence.")
    if any(row.treatment != row.sequence[int(row.period) - 1] for row in d.itertuples()):
        raise ValueError("Treatment không khớp sequence/kỳ.")
    if d.groupby("sequence").subject_id.nunique().min() < 2:
        raise ValueError("Mỗi sequence cần ít nhất hai subject.")
    return d


def subject_contrasts(d, endpoint):
    rows = []
    for (subject, seq), group in d.groupby(["subject_id", "sequence"], sort=True):
        group = group.sort_values("period")
        trt = np.log(group.loc[group.treatment.eq("T"), endpoint].to_numpy())
        ref = np.log(group.loc[group.treatment.eq("R"), endpoint].to_numpy())
        rows.append(
            dict(
                subject_id=str(subject),
                sequence=seq,
                I=float(trt.mean() - ref.mean()),
                D_R=float(ref[0] - ref[1]),
                D_T=float(trt[0] - trt[1]) if len(trt) == 2 else None,
            )
        )
    subjects = pd.DataFrame(rows)
    seqs = sorted(subjects.sequence.unique())
    matrix = np.column_stack([subjects.sequence.eq(seq).to_numpy(dtype=float) for seq in seqs])
    weights = np.ones(len(seqs)) / len(seqs)
    fit_i, fit_r = ols(subjects.I, matrix), ols(subjects.D_R, matrix)
    estimate = ols_test(fit_i, weights)
    intermediate = []
    intermediate_tests = []
    residual_diagnostics: list[dict] = []
    for name, response, fitted in (("I", subjects.I, fit_i), ("D_R", subjects.D_R, fit_r)):
        residual_diagnostics.extend(
            {
                "subject_id": str(record.subject_id),
                "sequence": record.sequence,
                "Model": f"FDA {name} ~ sequence",
                **row,
            }
            for record, row in zip(subjects.itertuples(), fitted["residual_diagnostics"], strict=True)
        )
        for index, sequence in enumerate(seqs):
            mean = float(fitted["beta"][index])
            se = math.sqrt(float(fitted["covariance"][index, index]))
            critical = float(t.ppf(0.95, fitted["df"]))
            intermediate.append(
                dict(
                    model=f"{name} ~ sequence",
                    effect=sequence,
                    estimate=mean,
                    se=se,
                    df=fitted["df"],
                    lower=mean - critical * se,
                    upper=mean + critical * se,
                )
            )
        total_ss = float(np.sum((response - response.mean()) ** 2))
        explained = max(0.0, total_ss - fitted["sse"])
        fvalue = explained / (len(seqs) - 1) / fitted["mse"] if fitted["mse"] > 0 else None
        intermediate_tests.append(
            dict(
                model=f"{name} ~ sequence",
                Hypothesis="Sequence",
                Numer_DF=len(seqs) - 1,
                Denom_DF=fitted["df"],
                SS=explained,
                MS=explained / (len(seqs) - 1),
                F_stat=fvalue,
                P_value=float(f.sf(fvalue, len(seqs) - 1, fitted["df"])) if fvalue is not None else None,
            )
        )
    if fit_r["mse"] <= 1e-16:
        raise ValueError("Phương sai reference bằng zero; không scale hoặc chia tỷ lệ phương sai.")
    swr = math.sqrt(fit_r["mse"] / 2)
    swt, fit_t = None, None
    if subjects.D_T.notna().all():
        fit_t = ols(subjects.D_T, matrix)
        swt = math.sqrt(fit_t["mse"] / 2)
        residual_diagnostics.extend(
            {
                "subject_id": str(record.subject_id),
                "sequence": record.sequence,
                "Model": "FDA D_T ~ sequence",
                **row,
            }
            for record, row in zip(subjects.itertuples(), fit_t["residual_diagnostics"], strict=True)
        )
    return dict(
        subjects=subjects.to_dict("records"),
        estimate=estimate,
        swr=swr,
        swt=swt,
        variance_reference=swr**2,
        df_reference=fit_r["df"],
        variance_test=swt**2 if swt is not None else None,
        df_test=fit_t["df"] if fit_t is not None else None,
        mse_I=fit_i["mse"],
        sequence_counts=subjects.groupby("sequence").size().to_dict(),
        model="I/D contrasts by sequence, equal sequence weights; FDA Appendix F/G; complete subjects",
        intermediate_parameters=intermediate,
        intermediate_tests=intermediate_tests,
        residual_diagnostics=residual_diagnostics,
    )


def ema_method_a(d, endpoint):
    subjects = sorted(d.subject_id.unique(), key=str)
    periods = sorted(d.period.unique())
    matrix = np.column_stack(
        [
            np.ones(len(d)),
            *[d.subject_id.eq(s).to_numpy(dtype=float) for s in subjects[1:]],
            *[d.period.eq(p).to_numpy(dtype=float) for p in periods[1:]],
            d.treatment.eq("T").to_numpy(dtype=float),
        ]
    )
    fit = ols(np.log(d[endpoint]), matrix)
    weights = np.zeros(matrix.shape[1])
    weights[-1] = 1
    c = ols_test(fit, weights)
    c.update(t=c["estimate"] / c["se"], confidence=0.9, critical=float(t.ppf(0.95, fit["df"])))
    c.update(lower=c["estimate"] - c["critical"] * c["se"], upper=c["estimate"] + c["critical"] * c["se"])
    # Equal-weight subject and period marginals for adjusted formulation means.
    marginal = np.array(
        [1, *([1 / len(subjects)] * (len(subjects) - 1)), *([1 / len(periods)] * (len(periods) - 1)), 0.0]
    )
    lsmean_r = float(marginal @ fit["beta"])
    lsmean_t = lsmean_r + c["estimate"]
    lsm_rows = []
    for level in ("R", "T"):
        vector = marginal.copy()
        vector[-1] = 1 if level == "T" else 0
        mean = float(vector @ fit["beta"])
        se = math.sqrt(float(vector @ fit["covariance"] @ vector))
        statistic = mean / se
        lsm_rows.append(
            dict(
                Level=level,
                estimate=mean,
                se=se,
                df=fit["df"],
                t=statistic,
                p=float(2 * t.sf(abs(statistic), fit["df"])),
                confidence=0.9,
                critical=c["critical"],
                lower=mean - c["critical"] * se,
                upper=mean + c["critical"] * se,
            )
        )
    tests = []
    for label, indices in (
        ("Subject (Sequence absorbed)", list(range(1, len(subjects)))),
        ("Period", list(range(len(subjects), matrix.shape[1] - 1))),
        ("Treatment", [matrix.shape[1] - 1]),
    ):
        reduced = ols(np.log(d[endpoint]), np.delete(matrix, indices, axis=1))
        ss = max(0.0, reduced["sse"] - fit["sse"])
        fvalue = (ss / len(indices)) / fit["mse"]
        tests.append(
            dict(
                Hypothesis=label,
                Numer_DF=len(indices),
                Denom_DF=fit["df"],
                SS=ss,
                MS=ss / len(indices),
                F_stat=fvalue,
                P_value=float(f.sf(fvalue, len(indices), fit["df"])),
            )
        )
    coefficient_rows = []
    labels = [
        "int",
        *[f"Subject:{s}" for s in subjects[1:]],
        *[f"Period:{p}" for p in periods[1:]],
        "Treatment:T-R",
    ]
    for i, label in enumerate(labels):
        se = math.sqrt(float(fit["covariance"][i, i]))
        value = float(fit["beta"][i])
        coefficient_rows.append(
            dict(
                effect=label,
                estimate=value,
                se=se,
                df=fit["df"],
                p=float(2 * t.sf(abs(value / se), fit["df"])),
            )
        )
    return dict(
        contrast=c,
        mse=fit["mse"],
        residual_ss=fit["sse"],
        residual_df=fit["df"],
        residuals=[
            {
                **{k: record[k] for k in ("subject_id", "sequence", "period", "treatment")},
                "Predicted": pred,
                "Residual": res,
                **fit["residual_diagnostics"][i],
                "Model": "EMA Method A",
            }
            for i, (record, pred, res) in enumerate(
                zip(d.to_dict("records"), fit["predicted"], fit["residuals"], strict=True)
            )
        ],
        fixed_parameters=coefficient_rows,
        lsmean_log_r=lsmean_r,
        lsmean_log_t=lsmean_t,
        model="EMA Method A: fixed subject(sequence), period, formulation; sequence absorbed by subject",
        lsmeans=lsm_rows,
        partial_tests=tests,
    )


def ema_reference_variance(d, endpoint, treatment="R"):
    """Reference-only fixed subject/period ANOVA (EMA Q&A 3.1), distinct from FDA D contrasts."""
    ref = d.loc[d.treatment.eq(treatment)]
    candidates = [
        np.ones(len(ref)),
        *[ref.subject_id.eq(s).to_numpy(dtype=float) for s in sorted(ref.subject_id.unique(), key=str)[1:]],
        *[ref.period.eq(p).to_numpy(dtype=float) for p in sorted(ref.period.unique())[1:]],
    ]
    independent: list[np.ndarray] = []
    rank = 0
    for column in candidates:
        trial = np.column_stack([*independent, column])
        new_rank = int(np.linalg.matrix_rank(trial))
        if new_rank > rank:
            independent.append(column)
            rank = new_rank
    fit = ols(np.log(ref[endpoint]), np.column_stack(independent))
    if fit["mse"] <= 1e-16:
        raise ValueError("Phương sai trong treatment suy biến.")
    return dict(
        variance=fit["mse"],
        sd=math.sqrt(fit["mse"]),
        df=fit["df"],
        ss=fit["sse"],
        n_observations=len(ref),
        model=f"EMA reference-only fixed subject + period ({treatment})",
        residual_diagnostics=[
            {
                **{k: record[k] for k in ("subject_id", "sequence", "period", "treatment")},
                **row,
                "Model": f"EMA reference-only ({treatment})",
            }
            for record, row in zip(ref.to_dict("records"), fit["residual_diagnostics"], strict=True)
        ],
    )


def howe_bound(estimate, se, df_i, swr, df_r, *, nti=False):
    theta = (math.log(1 / 0.9) / 0.1) ** 2 if nti else (math.log(1.25) / 0.25) ** 2
    critical = float(t.ppf(0.95, df_i))
    x = estimate**2 - se**2
    bound_x = (abs(estimate) + critical * se) ** 2
    y = -theta * swr**2
    bound_y = y * df_r / float(chi2.ppf(0.95, df_r))
    upper = x + y + math.hypot(bound_x - x, bound_y - y)
    return dict(
        theta=theta,
        sigma_w0=0.1 if nti else 0.25,
        x=x,
        bound_x=bound_x,
        y=y,
        bound_y=bound_y,
        upper_95=upper,
        df_I=df_i,
        df_R=df_r,
        constant_note="NTI uses exact 1/0.9; FDA illustrative SAS rounds to 1.11111." if nti else "",
    )


def analyze_replicate(data, endpoint, study: Study, config=None):
    cfg = config or BeConfig()
    try:
        if cfg.alpha != 0.05 or cfg.lower != 0.8 or cfg.upper != 1.25:
            raise ValueError("Replicate profile yêu cầu alpha=0.05 và giới hạn nền 0.8–1.25.")
        d = prepare_replicate(data, endpoint, study.design)
        stats = subject_contrasts(d, endpoint)
        method_a = ema_method_a(d, endpoint)
        fda = study.rule_set_id.startswith("FDA")
        if not fda:
            reference_only = ema_reference_variance(d, endpoint)
            test_only = ema_reference_variance(d, endpoint, "T") if study.design == "full4" else None
            stats.update(
                swr=reference_only["sd"],
                variance_reference=reference_only["variance"],
                df_reference=reference_only["df"],
                reference_only_anova=reference_only,
                swt=test_only["sd"] if test_only else None,
                variance_test=test_only["variance"] if test_only else None,
                df_test=test_only["df"] if test_only else None,
            )
        contrast = stats["estimate"] if fda else method_a["contrast"]
        diagnostics = dict(
            replicate=stats,
            ema_method_a=method_a,
            model=stats["model"] if fda else method_a["model"],
            swr=stats["swr"],
            swt=stats["swt"],
            cv_wr=math.sqrt(math.expm1(stats["swr"] ** 2)),
            cv_wt=math.sqrt(math.expm1(stats["swt"] ** 2)) if stats["swt"] is not None else None,
            missing_policy="complete supported replicate designs only",
            model_diagnostics=dict(
                n_observations=len(d),
                n_subjects=int(d.subject_id.nunique()),
                converged=True,
                df_reference=stats["df_reference"],
            ),
        )
        diagnostics.update(
            partial_tests=stats["intermediate_tests"] if fda else method_a["partial_tests"],
            fixed_parameters=[
                {**row, "Model": "EMA Method A supplementary" if fda else "EMA Method A"}
                for row in method_a["fixed_parameters"]
            ],
        )
        diagnostics["residual_diagnostics"] = (
            stats["residual_diagnostics"]
            if fda
            else [
                *method_a["residuals"],
                *stats["reference_only_anova"]["residual_diagnostics"],
            ]
        )
        if fda:
            for row in method_a["residuals"]:
                row["Model"] = "EMA Method A supplementary; not the FDA decision model"
        if not fda:
            diagnostics.update(
                lsmeans=method_a["lsmeans"],
                difference=method_a["contrast"],
                lsm_r=method_a["lsmeans"][0],
                lsm_t=method_a["lsmeans"][1],
            )
        base_cfg = cfg.model_copy(update={"lower": 0.8, "upper": 1.25})
        if study.rule_set_id == "EMA_NTI":
            narrow = endpoint != "cmax" or study.nti_cmax_narrow
            base_cfg = cfg.model_copy(
                update={"lower": 0.9 if narrow else 0.8, "upper": 1.1111 if narrow else 1.25}
            )
        if study.rule_set_id == "EMA_HVDP_ABEL":
            lo, hi = ema_abel_limits(stats["swr"], endpoint)
            base_cfg = cfg.model_copy(update={"lower": lo, "upper": hi})
        result = _result(
            endpoint,
            d,
            contrast["estimate"],
            contrast["se"],
            contrast["df"],
            base_cfg,
            diagnostics,
            None if fda else math.sqrt(math.expm1(method_a["mse"])),
        )
        if result.estimate is None:
            return result
        method = "replicate ABE / FDA subject contrasts" if fda else "replicate ABE / EMA Method A"
        criteria = list(result.criteria)
        upper_bound = None
        ratio_low, ratio_high = None, None
        if study.rule_set_id == "EMA_HVDP_ABEL":
            method = "EMA ABEL Cmax" if endpoint == "cmax" and base_cfg.lower < 0.8 else "EMA replicate ABE"
            if endpoint == "cmax" and base_cfg.lower < 0.8:
                criteria.append(
                    dict(
                        criterion="GMR 80.00–125.00%",
                        value=result.gmr,
                        limits=[0.8, 1.25],
                        passed=bool(0.8 <= result.gmr <= 1.25),
                    )
                )
            diagnostics.update(
                scaling_threshold_cv=0.30,
                scaling_cap_cv=0.50,
                scaling_k=0.760,
                selected_branch=method,
                scaled_limits=[base_cfg.lower, base_cfg.upper],
            )
        if study.rule_set_id in ("FDA_HVD_RSABE_2026", "FDA_NTI"):
            nti = study.rule_set_id == "FDA_NTI"
            scaling = nti or stats["swr"] >= 0.294
            if scaling:
                bound = howe_bound(
                    result.estimate, result.se, result.df, stats["swr"], stats["df_reference"], nti=nti
                )
                upper_bound = bound["upper_95"]
                diagnostics["howe"] = bound
                scaled_criterion = dict(
                    criterion="Howe 95% UCB ≤ 0", value=upper_bound, upper=0, passed=bool(upper_bound <= 0)
                )
                if nti:
                    if study.design != "full4" or stats["swt"] is None:
                        raise ValueError("FDA NTI cần full4 có cả T và R được dùng lặp lại.")
                    method = "FDA NTI / RSABE + ABE + variance comparison"
                    ratio = stats["swt"] / stats["swr"]
                    ratio_low = ratio / math.sqrt(float(f.ppf(0.95, stats["df_test"], stats["df_reference"])))
                    ratio_high = ratio / math.sqrt(
                        float(f.ppf(0.05, stats["df_test"], stats["df_reference"]))
                    )
                    criteria.extend(
                        [
                            scaled_criterion,
                            dict(
                                criterion="90% upper CI of sWT/sWR ≤ 2.5",
                                value=ratio_high,
                                upper=2.5,
                                passed=bool(ratio_high <= 2.5),
                            ),
                        ]
                    )
                    diagnostics.update(sd_ratio=ratio, sd_ratio_ci90=[ratio_low, ratio_high])
                else:
                    method = "FDA HVD / RSABE"
                    criteria = [
                        scaled_criterion,
                        dict(
                            criterion="GMR 80.00–125.00%",
                            value=result.gmr,
                            limits=[0.8, 1.25],
                            passed=bool(0.8 <= result.gmr <= 1.25),
                        ),
                    ]
            else:
                method = "FDA HVD / unscaled ABE (sWR < 0.294)"
            diagnostics.update(
                selected_branch=method,
                scaling_threshold_swr=0.294,
                i_contrast_ci90=[result.ci_lower, result.ci_upper],
                conventional_abe_ci90=None,
                conventional_abe_qualified=False,
            )
        decision = "PASS" if all(c["passed"] for c in criteria) else "FAIL"
        reason = ""
        requires_conventional_abe = fda and (
            study.rule_set_id in ("FDA_REPLICATE_STANDARD", "FDA_NTI")
            or (study.rule_set_id == "FDA_HVD_RSABE_2026" and stats["swr"] < 0.294)
        )
        if requires_conventional_abe:
            # The I-contrast model qualifies RSABE components, not Appendix C ABE SE/df.
            # Archived independent benchmark outputs demonstrate that these CIs differ.
            reason = (
                "Conventional ABE replicate cần mô hình mixed/covariance/df đã kiểm chứng; "
                "CI từ FDA I contrasts chỉ để chẩn đoán, không thay conventional ABE. "
                "Nhánh mixed mới chưa qualification; chưa cho phép kết luận endpoint."
            )
            diagnostics.update(
                conventional_abe_qualified=False,
                conventional_abe_ci90=None,
                i_contrast_ci90=[result.ci_lower, result.ci_upper],
                conventional_abe_gate_reason=reason,
            )
            criteria[0] = dict(
                criterion="Conventional replicate ABE — model not qualified",
                value=None,
                limits=[0.8, 1.25],
                passed=None,
                reason=reason,
            )
            decision = "NOT EVALUABLE"
            method += " / I-contrast diagnostics; conventional ABE not qualified"
        if not fda:
            result = result.model_copy(
                update=dict(
                    lsmean_log_r=method_a["lsmean_log_r"],
                    lsmean_log_t=method_a["lsmean_log_t"],
                    adjusted_geometric_mean_r=math.exp(method_a["lsmean_log_r"]),
                    adjusted_geometric_mean_t=math.exp(method_a["lsmean_log_t"]),
                )
            )
        return result.model_copy(
            update=dict(
                method=method,
                decision=decision,
                reason=reason,
                swr=stats["swr"],
                swt=stats["swt"],
                scaled_ucb=upper_bound,
                sd_ratio_ci_lower=ratio_low,
                sd_ratio_ci_upper=ratio_high,
                criteria=criteria,
                diagnostics=diagnostics,
            )
        )
    except (ValueError, TypeError, ArithmeticError, np.linalg.LinAlgError) as exc:
        return BeResult(
            endpoint=endpoint,
            method=study.rule_set_id,
            reason=str(exc),
            diagnostics={"n_input_observations": len(data), "requested_design": study.design},
        )


def analyze_regulatory_be(data, endpoint, study: Study, config=None):
    cfg = config or BeConfig()
    if study.design in SEQUENCES:
        result = analyze_replicate(data, endpoint, study, cfg)
    else:
        if study.rule_set_id in ("FDA_NTI", "FDA_HVD_RSABE_2026", "EMA_HVDP_ABEL"):
            baseline = analyze_abe(data, endpoint, study.design, cfg)
            return baseline.model_copy(
                update={
                    "method": study.rule_set_id,
                    "decision": "NOT EVALUABLE",
                    "reason": "Cần dữ liệu replicate để ước tính riêng sWR (và sWT cho FDA NTI); CV gộp 2×2 không đủ.",
                    "diagnostics": {**baseline.diagnostics, "unscaled_abe_only": True},
                }
            )
        endpoint_cfg = cfg
        if study.rule_set_id == "EMA_NTI":
            narrow = endpoint != "cmax" or study.nti_cmax_narrow
            endpoint_cfg = cfg.model_copy(
                update=dict(lower=0.9 if narrow else 0.8, upper=1.1111 if narrow else 1.25)
            )
        result = analyze_abe(data, endpoint, study.design, endpoint_cfg)
        if study.rule_set_id == "EMA_NTI":
            result = result.model_copy(update={"method": "EMA NTI / narrowed ABE"})
        if study.rule_set_id.startswith("EMA") and cfg.missing_policy == "available_observations":
            observed = data.loc[pd.to_numeric(data[endpoint], errors="coerce").notna()]
            if study.design == "2x2" and observed.groupby("subject_id").treatment.nunique().ne(2).any():
                result = result.model_copy(
                    update={
                        "decision": "NOT EVALUABLE",
                        "reason": "EMA nonreplicate: có subject không có cả T/R; cần population và xử lý missing định trước. Kết quả REML chỉ để chẩn đoán.",
                    }
                )
    requirements = []
    if study.rule_set_id in ("EMA_HVDP_ABEL", "FDA_HVD_RSABE_2026"):
        if study.nti:
            requirements.append("Không dùng HVD scaling cho NTI.")
        if not study.scaled_be_prespecified or len(study.hvd_justification.strip()) < 10:
            requirements.append("Scaling cần định trước và căn cứ độ tin cậy biến thiên/ý nghĩa lâm sàng.")
    if study.rule_set_id in ("EMA_NTI", "FDA_NTI") and not study.nti:
        requirements.append("Cần xác nhận phân loại NTI dựa trên yêu cầu sản phẩm.")
    from be_app.regulations import RULES

    rule = RULES.get(study.rule_set_id)
    if rule is None or study.design not in rule.designs:
        requirements.append("Thiết kế không phù hợp profile đã chọn.")
    if requirements:
        result = result.model_copy(update={"decision": "NOT EVALUABLE", "reason": "; ".join(requirements)})
    return result
