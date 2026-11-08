"""Compact reviewer tables shared by Word and PDF report writers."""

import json
import math

from be_app.review import pk_descriptive, reviewer_tables


def formatted(value):
    if isinstance(value, (list, tuple)):
        return " to ".join(formatted(v) for v in value)
    if value is None or isinstance(value, float) and not math.isfinite(value):
        return "—"
    return f"{value:.6g}" if isinstance(value, float) else str(value)


def criterion_value(value):
    if isinstance(value, str) and value.startswith("["):
        return formatted(json.loads(value))
    return formatted(value)


def report_tables(run, language):
    vi = language == "vi"
    decisions_vi = {"PASS": "Đạt", "FAIL": "Không đạt", "NOT EVALUABLE": "Không thể kết luận"}
    cell_status_vi = {
        "Missing period": "Thiếu kỳ",
        "Duplicate period": "Trùng kỳ",
        "Invalid design/identity": "Sai thiết kế hoặc định danh",
        "Missing/nonpositive/nonfinite PK": "Thiếu PK hoặc giá trị PK không hợp lệ",
        "Available": "Có dữ liệu hợp lệ",
    }

    def decision(value):
        return decisions_vi.get(value, value) if vi else value

    tables = reviewer_tables(run["be"], data=run["nca"], design=run["study"]["design"])
    criteria = tables["Reviewer Criteria"]
    counts = tables["Population Counts"]
    matrix = tables["Population Matrix"]
    endpoints = [*run["study"]["primary_endpoints"], *run["study"].get("secondary_endpoints", []), "tmax"]
    stats = pk_descriptive(run["nca"], endpoints)
    tmax = run.get("tmax_comparison")
    if tmax is None:
        tmax_rows = [["—"] * 7]
        tmax_note = (
            "Snapshot lịch sử chưa thực hiện so sánh Tmax phi tham số; không suy diễn kết quả từ dữ liệu khi xuất báo cáo."
            if vi else "Historical snapshot has no nonparametric Tmax comparison; the report does not recompute it."
        )
    else:
        tmax_rows = [
            [arm, tmax.get(f"n_{suffix}"), tmax.get(f"median_{suffix}"),
             tmax.get(f"min_{suffix}"), tmax.get(f"max_{suffix}"),
             tmax.get("method") or "—", tmax.get("p_value")]
            for arm, suffix in (("T", "t"), ("R", "r"))
        ]
        if tmax.get("status") == "EVALUABLE":
            pairs = (
                f"; số cặp={tmax['n_pairs']}, trung vị (T−R)={formatted(tmax['median_paired_difference'])} giờ"
                if vi else
                f"; pairs={tmax['n_pairs']}, median (T−R)={formatted(tmax['median_paired_difference'])} h"
            ) if tmax.get("n_pairs") is not None else ""
            tmax_note = (
                f"Kiểm định hai phía; thống kê={formatted(tmax.get('statistic'))}{pairs}. "
                if vi else f"Two-sided test; statistic={formatted(tmax.get('statistic'))}{pairs}. "
            )
        else:
            tmax_note = f"NOT EVALUABLE: {tmax.get('reason', '')}. "
        tmax_note += (
            "Tmax gốc (giờ), phân tích hỗ trợ, không tham gia quyết định BE hay giới hạn 80–125%. "
            "Wilcoxon ghép cặp không hiệu chỉnh kỳ/trình tự; replicate cần phương pháp định trước trong SAP."
            if vi else
            "Original-hour Tmax, supportive only; not part of BE decision or 80–125% limits. "
            "Paired Wilcoxon is not period/sequence adjusted; replicate designs require a prespecified SAP method."
        )
    specs = [
        (
            "Rà soát từng tiêu chí BE" if vi else "Review of individual BE criteria",
            (["Chỉ số PK", "Tiêu chí", "Giá trị", "Giới hạn", "Kết quả tiêu chí", "Kết quả chỉ số"]
             if vi else ["Endpoint", "Criterion", "Value", "Limits", "Criterion result", "Endpoint result"]),
            [2.4, 3.8, 2.6, 2.0, 2.6, 3.0],
            [
                [
                    r.Endpoint,
                    r.Criterion,
                    criterion_value(r.Value),
                    f"{formatted(r.Lower)} – {formatted(r.Upper)}",
                    decision(r.Criterion_result),
                    decision(r.Endpoint_result),
                ]
                for r in criteria.itertuples()
            ],
            "Giá trị/ngưỡng là tỷ lệ, không phải %. Howe dùng thang log. Kết quả tiêu chí không thay thế điều kiện áp dụng và kết luận endpoint."
            if vi
            else "Values and limits are ratios, not %. Howe uses the log criterion. Criterion results do not replace scope or endpoint decision gates.",
        ),
        (
            "Population dùng trong phân tích" if vi else "Populations used in the analysis",
            ([
                "Chỉ số PK", "Người có dữ liệu", "Hoàn tất", "Người trong mô hình",
                "Quan sát mô hình", "Người tính biến thiên R", "Người tính biến thiên T",
            ] if vi else [
                "Endpoint", "Input subjects", "Complete", "Model subjects", "Model obs",
                "R variance subjects", "T variance subjects",
            ]),
            [2.0, 2.3, 1.8, 2.6, 2.1, 2.8, 2.8],
            [
                [
                    r.Endpoint,
                    r.Input_subjects,
                    r.Complete_subjects,
                    r.Model_subjects,
                    r.Model_observations,
                    r.R_variance_subjects,
                    r.T_variance_subjects,
                ]
                for r in counts.itertuples()
            ],
            "Complete mô tả dữ liệu; Model cho biết phép tính thực sự đã thực hiện. Không tự loại người thiếu kỳ. CV gộp 2×2 không phải sWR."
            if vi
            else "Complete describes available data; Model counts describe calculations actually performed. Missing periods are not silently excluded. Pooled 2x2 CV is not sWR.",
        ),
        (
            "Đại lượng scaling và biến thiên" if vi else "Scaling and variability estimates",
            (["Chỉ số PK", "sWR", "sWT", "Howe UCB95", "Cận dưới CI90 tỷ số SD", "Cận trên CI90 tỷ số SD"]
             if vi else ["Endpoint", "sWR", "sWT", "Howe UCB95", "SD ratio CI90 lower", "SD ratio CI90 upper"]),
            [2.2, 2.0, 2.0, 3.0, 3.6, 3.6],
            [
                [
                    r["endpoint"],
                    *[
                        r.get(k)
                        for k in ("swr", "swt", "scaled_ucb", "sd_ratio_ci_lower", "sd_ratio_ci_upper")
                    ],
                ]
                for r in run["be"]
            ],
            "Dấu — là không áp dụng/chưa ước tính; không đổi thành zero."
            if vi
            else "A dash indicates not applicable or not estimated; it does not mean zero.",
        ),
        (
            "Thống kê PK mô tả" if vi else "Descriptive PK statistics",
            (["Chỉ số PK", "T/R", "Số quan sát", "Số người", "TB (SD)", "CV %", "Trung vị", "Nhỏ nhất – lớn nhất"]
             if vi else ["Endpoint", "T/R", "N obs", "N subjects", "Mean (SD)", "CV %", "Median", "Min to max"]),
            [2.2, 1.0, 1.3, 1.8, 3.4, 1.8, 2.0, 2.9],
            [
                [
                    r.Endpoint,
                    r.Treatment,
                    r.N_observations,
                    r.N_subjects,
                    f"{formatted(r.Mean)} ({formatted(r.SD)})",
                    r.CV_percent,
                    r.Median,
                    f"{formatted(r.Minimum)} – {formatted(r.Maximum)}",
                ]
                for r in stats.itertuples()
            ],
            "N obs đếm lần dùng thuốc; replicate không phải các người độc lập. Cmax ng/mL, AUC h·ng/mL, Tmax h. Đây là PK quan sát, không phải adjusted LS means."
            if vi
            else "N obs counts administrations; replicates are not independent subjects. Units: Cmax ng/mL, AUC h·ng/mL, Tmax h. These describe observed PK, not adjusted LS means.",
        ),
        (
            "So sánh Tmax phi tham số (hỗ trợ)" if vi else "Supportive nonparametric Tmax comparison",
            (["Nhóm", "N", "Trung vị (h)", "Nhỏ nhất (h)", "Lớn nhất (h)", "Kiểm định", "p hai phía"]
             if vi else ["Arm", "N", "Median (h)", "Min (h)", "Max (h)", "Test", "Two-sided p"]),
            [1.4, 1.0, 2.3, 2.3, 2.3, 5.5, 2.3],
            tmax_rows,
            tmax_note,
        ),
        (
            "Trung bình nhân và biến thiên PK" if vi else "Geometric PK summaries",
            (["Chỉ số PK", "T/R", "Trung bình nhân", "CV nhân %", "Thiếu hoặc không hữu hạn", "Không dương"]
             if vi else ["Endpoint", "T/R", "Geometric mean", "Geometric CV %", "Missing or nonfinite", "Nonpositive"]),
            [2.6, 1.1, 3.7, 3.3, 3.0, 2.7],
            [
                [
                    r.Endpoint,
                    r.Treatment,
                    r.Geometric_mean,
                    r.Geometric_CV_percent,
                    r.N_missing_or_nonfinite,
                    r.N_nonpositive,
                ]
                for r in stats.itertuples()
            ],
            "Không tính geometric mean/CV cho Tmax hoặc tập dữ liệu có giá trị không dương."
            if vi
            else "Geometric mean/CV is not calculated for Tmax or data containing nonpositive values.",
        ),
        (
            "Danh sách dữ liệu theo endpoint và kỳ" if vi else "Endpoint and period data listing",
            (["Chỉ số PK", "Mã người tham gia", "Trình tự", "Kỳ", "T/R thực tế", "Trạng thái dữ liệu", "Trong mô hình"]
             if vi else ["Endpoint", "Subject", "Sequence", "Period", "Observed T/R", "Cell status", "Model used"]),
            [2.2, 1.8, 1.8, 1.3, 2.3, 5.2, 1.8],
            [
                [
                    r.Endpoint,
                    r.Subject,
                    r.Sequence,
                    r.Period,
                    r.Observed_treatment,
                    cell_status_vi.get(r.Cell_status, r.Cell_status) if vi else r.Cell_status,
                    ("Có" if r.Model_used else "Không") if vi else ("Yes" if r.Model_used else "No"),
                ]
                for r in matrix.itertuples()
            ],
            "Các kỳ dự kiến bị thiếu được giữ trong danh sách; rà soát population không thay đổi dữ liệu gốc."
            if vi
            else "Missing expected periods remain in the listing; population review does not alter the original data.",
        ),
    ]
    return [
        dict(
            title=title,
            headers=headers,
            widths=widths,
            rows=[[formatted(v) for v in row] for row in rows],
            note=note,
        )
        for title, headers, widths, rows, note in specs
    ]
