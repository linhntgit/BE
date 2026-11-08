"""Self-contained report figures built from either marked examples or locked snapshots.

The figures never change the input project or its analysis hashes. In particular,
mock values in the editable template must not be mistaken for trial results.
"""

import io
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


@dataclass(frozen=True)
class ReportFigure:
    title: str
    note: str
    png: bytes


WIDTH, HEIGHT = 1400, 740
NAVY = "#18324C"
BLUE = "#2878A5"
ORANGE = "#CE6942"
GRID = "#DCE5EA"
INK = "#213244"
MUTED = "#607384"


def _font(size: int, *, bold: bool = False):
    candidates = (
        [Path("C:/Windows/Fonts/arialbd.ttf"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")]
        if bold else
        [Path("C:/Windows/Fonts/arial.ttf"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")]
    )
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def _canvas(title: str, subtitle: str):
    canvas = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((70, 37), title, font=_font(38, bold=True), fill=NAVY)
    draw.text((72, 92), subtitle, font=_font(22), fill=MUTED)
    draw.line([(70, 139), (WIDTH - 70, 139)], fill=GRID, width=3)
    return canvas, draw


def _png(img: Image.Image) -> bytes:
    output = io.BytesIO()
    img.save(output, format="PNG", optimize=True)
    return output.getvalue()


def _s(draw, x: float, y: float, label: str, color=INK, size=21, *, bold=False):
    draw.text((int(x), int(y)), label, fill=color, font=_font(size, bold=bold))


def _design_figure(vi: bool) -> ReportFigure:
    title = "Thiết kế bắt chéo 2 × 2" if vi else "Two-period crossover design"
    subtitle = (
        "Sơ đồ phương pháp từ đề cương NCT03083639 — không thể hiện kết quả nghiên cứu"
        if vi else "Design schematic inspired by NCT03083639 protocol — no study results"
    )
    image, draw = _canvas(title, subtitle)
    x0, x1, x2 = 190, 645, 1110
    _s(draw, x0 - 28, 188, "Trình tự" if vi else "Sequence", size=25, bold=True)
    _s(draw, x1 - 35, 188, "Kỳ 1" if vi else "Period 1", size=25, bold=True)
    _s(draw, x2 - 35, 188, "Kỳ 2" if vi else "Period 2", size=25, bold=True)
    for yy, seq, left, right in [(288, "TR", "T", "R"), (452, "RT", "R", "T")]:
        draw.rounded_rectangle((95, yy, 285, yy + 105), radius=16, fill="#E8F1F6", outline=GRID, width=2)
        _s(draw, 164, yy + 29, seq, size=32, bold=True)
        for xx, letter in [(550, left), (1025, right)]:
            fill = BLUE if letter == "T" else ORANGE
            draw.rounded_rectangle((xx, yy, xx + 182, yy + 105), radius=18, fill=fill)
            _s(draw, xx + 76, yy + 26, letter, "white", 37, bold=True)
        draw.line([(287, yy + 52), (542, yy + 52)], fill=MUTED, width=5)
        draw.polygon([(542, yy + 52), (524, yy + 43), (524, yy + 61)], fill=MUTED)
        draw.line([(734, yy + 52), (1017, yy + 52)], fill=MUTED, width=5)
        draw.polygon([(1017, yy + 52), (999, yy + 43), (999, yy + 61)], fill=MUTED)
    _s(draw, 786, 263, "Washout ≥ 6 ngày" if vi else "Washout ≥ 6 days", color=MUTED, size=22)
    _s(draw, 786, 428, "Washout ≥ 6 ngày" if vi else "Washout ≥ 6 days", color=MUTED, size=22)
    _s(draw, 103, 615, "T: thuốc thử (test)     R: thuốc đối chứng (reference)" if vi else "T: test product     R: reference product", size=24)
    return ReportFigure(title, subtitle, _png(image))


def _teaching_profiles():
    points = []
    for hour in (0, 1 / 3, 2 / 3, 1, 4 / 3, 5 / 3, 2, 7 / 3, 8 / 3, 3, 3.5, 4, 4.5, 5, 6, 7, 8, 9, 10):
        for treatment, factor in (("T", 0.94), ("R", 1.0)):
            concentration = max(0, factor * 155 * (math.exp(-0.32 * hour) - math.exp(-2.0 * hour)))
            points.append({"nominal_time_h": hour, "treatment": treatment, "concentration": concentration})
    return points


def _profiles_figure(records: list[dict], *, vi: bool, log: bool, example: bool) -> ReportFigure | None:
    grouped = defaultdict(list)
    eligible = [row for row in records if row.get("treatment") in ("T", "R")]
    if not example and any(row.get("analyte") == "parent" for row in eligible):
        eligible = [row for row in eligible if row.get("analyte") == "parent"]
    for row in eligible:
        try:
            time = float(row["nominal_time_h"])
            conc = float(row["concentration"])
        except (ValueError, TypeError, KeyError):
            continue
        if math.isfinite(time) and math.isfinite(conc) and time >= 0 and conc >= 0:
            grouped[(row["treatment"], time)].append(conc)
    series = {
        tr: sorted([(t, sum(values) / len(values)) for (trt, t), values in grouped.items() if trt == tr])
        for tr in ("T", "R")
    }
    series = {key: value for key, value in series.items() if len(value) >= 2}
    if not series:
        return None
    scale = "bán log" if log else "tuyến tính"
    title = (f"Nồng độ trung bình theo thời gian — thang {scale}" if vi
             else f"Mean concentration-time profile — {'semilog' if log else 'linear'}")
    provenance = (
        "DỮ LIỆU GIẢ LẬP ĐỂ GIẢNG DẠY — KHÔNG PHẢI KẾT QUẢ NCT03083639"
        if example else "TRÍCH XUẤT TỪ SNAPSHOT PHÂN TÍCH — CẦN ĐỐI CHIẾU DỮ LIỆU GỐC"
    ) if vi else (
        "SYNTHETIC TEACHING EXAMPLE — NOT NCT03083639 RESULTS"
        if example else "LOCKED ANALYSIS SNAPSHOT — VERIFY AGAINST SOURCE RECORDS"
    )
    image, draw = _canvas(title, provenance)
    left, top, right, bottom = 170, 190, 1250, 600
    xs = [t for values in series.values() for t, _ in values]
    ys = [c for values in series.values() for _, c in values if c > 0]
    if not ys:
        return None
    max_x = max(xs) or 1
    if log:
        log_min = min(math.log10(v) for v in ys)
        log_max = max(math.log10(v) for v in ys)
        y0 = math.floor(log_min)
        y1 = math.ceil(log_max) + (1 if math.ceil(log_max) == y0 else 0)
        def project_y(c):
            return bottom - (math.log10(c) - y0) / (y1 - y0) * (bottom - top)

        ticks = [10 ** t for t in range(y0, y1 + 1)]
    else:
        top_y = max(ys) * 1.12

        def project_y(c):
            return bottom - c / top_y * (bottom - top)

        ticks = [top_y * idx / 4 for idx in range(5)]

    def project_x(t):
        return left + t / max_x * (right - left)

    for tick in ticks:
        y = project_y(tick) if tick else bottom
        if top - 2 <= y <= bottom + 2:
            draw.line([(left, y), (right, y)], fill=GRID, width=2)
            label = f"{tick:.3g}" if tick < 1 else f"{tick:g}"
            box = draw.textbbox((0, 0), label, font=_font(20))
            _s(draw, left - 25 - (box[2] - box[0]), y - 13, label, size=20)
    for k in range(6):
        val = max_x * k / 5
        xx = project_x(val)
        draw.line([(xx, bottom), (xx, bottom + 9)], fill=MUTED, width=2)
        _s(draw, xx - 12, bottom + 15, f"{val:.1f}" if val % 1 else f"{val:.0f}", size=19)
    draw.line([(left, top), (left, bottom), (right, bottom)], fill=INK, width=4)
    for tr, color in (("T", BLUE), ("R", ORANGE)):
        points = [(project_x(t), project_y(c)) for t, c in series.get(tr, []) if c > 0 or not log]
        if len(points) > 1:
            draw.line(points, fill=color, width=6, joint="curve")
            for xx, yy in points:
                draw.ellipse((xx - 6, yy - 6, xx + 6, yy + 6), fill="white", outline=color, width=4)
    _s(draw, 480, 675, "Thời gian sau dùng thuốc (giờ)" if vi else "Time after dose (hours)", size=23)
    _s(draw, 170, 160, "Nồng độ (ng/mL)" if vi else "Concentration (ng/mL)", size=21)
    for i, (tr, color) in enumerate((("T", BLUE), ("R", ORANGE))):
        xx = 1025 + i * 122
        draw.line([(xx, 165), (xx + 48, 165)], fill=color, width=6)
        _s(draw, xx + 58, 150, tr, color, size=25, bold=True)
    note = (
        "Trung bình số học theo thuốc và thời điểm danh định; điểm BLQ = 0 không thể biểu diễn trên log. "
        if vi else "Arithmetic means by treatment and nominal time; zero/BLQ points omitted on log scale. "
    ) + provenance
    return ReportFigure(title, note, _png(image))


def _forest_figure(results: list[dict], *, vi: bool, example: bool) -> ReportFigure | None:
    items = []
    for row in results:
        try:
            gmr, low, high = (float(row[key]) for key in ("gmr", "ci_lower", "ci_upper"))
        except (KeyError, TypeError, ValueError):
            continue
        if all(math.isfinite(v) and v > 0 for v in (gmr, low, high)) and low <= high:
            items.append((str(row.get("endpoint", "?")), gmr, low, high))
    if not items:
        return None
    items = items[:8]
    title = "GMR (T/R) và khoảng tin cậy 90%" if vi else "GMR (T/R) and 90% confidence intervals"
    provenance = (
        "GIẢ LẬP ĐỂ MINH HỌA CÁCH ĐỌC BIỂU ĐỒ — KHÔNG PHẢI KẾT QUẢ NGHIÊN CỨU"
        if example else "DỮ LIỆU SNAPSHOT — KHÔNG KẾT LUẬN RSABE/ABEL/NTI CHỈ TỪ CI90"
    ) if vi else (
        "SYNTHETIC TEACHING EXAMPLE — NOT CLINICAL TRIAL RESULTS"
        if example else "SNAPSHOT DATA — CI90 ALONE DOES NOT DECIDE RSABE/ABEL/NTI"
    )
    image, draw = _canvas(title, provenance)
    left, right, top, bottom = 280, 1100, 215, 575
    minimum = min(0.7, min(row[2] for row in items) * .95)
    maximum = max(1.4, max(row[3] for row in items) * 1.05)
    # Linear ratio scale makes the 80%-125% conventional ABE reference band visible.
    def xpos(x):
        return left + (x - minimum) / (maximum - minimum) * (right - left)

    draw.rectangle((xpos(.8), top, xpos(1.25), bottom), fill="#ECF6F0")
    for value, label in ((.8, "80%"), (1, "100%"), (1.25, "125%")):
        x = xpos(value)
        draw.line([(x, top), (x, bottom)], fill=ORANGE if value != 1 else MUTED, width=3)
        _s(draw, x - 28, bottom + 13, label, size=21)
    draw.line([(left, bottom), (right, bottom)], fill=INK, width=3)
    for index, (endpoint, gmr, low, high) in enumerate(items):
        y = top + 40 + index * min(69, 300 / max(len(items), 1))
        _s(draw, 74, y - 19, endpoint, size=24, bold=True)
        draw.line([(xpos(low), y), (xpos(high), y)], fill=BLUE, width=6)
        for x in (xpos(low), xpos(high)):
            draw.line([(x, y - 10), (x, y + 10)], fill=BLUE, width=4)
        xx = xpos(gmr)
        draw.ellipse((xx - 10, y - 10, xx + 10, y + 10), fill=NAVY)
        _s(draw, 1120, y - 17, f"{gmr*100:.1f}%", size=22, bold=True)
    _s(draw, 318, 675, "Vùng màu: giới hạn ABE thông thường; tiêu chí đặc thù phải xét riêng." if vi
       else "Shaded: conventional ABE interval; evaluate method-specific rules separately.", size=23)
    return ReportFigure(title, provenance, _png(image))


def illustrative_figures(language: str = "vi") -> list[ReportFigure]:
    """Educational examples marked as invented; never NCT03083639 observations."""
    vi = language == "vi"
    sample = _teaching_profiles()
    results = [
        {"endpoint": "Cmax", "gmr": .96, "ci_lower": .87, "ci_upper": 1.07},
        {"endpoint": "AUC0–t", "gmr": .98, "ci_lower": .89, "ci_upper": 1.09},
        {"endpoint": "AUC0–∞", "gmr": .99, "ci_lower": .90, "ci_upper": 1.10},
    ]
    figures = [
        _design_figure(vi),
        _profiles_figure(sample, vi=vi, log=False, example=True),
        _profiles_figure(sample, vi=vi, log=True, example=True),
        _forest_figure(results, vi=vi, example=True),
    ]
    return [figure for figure in figures if figure is not None]


def snapshot_figures(run: dict, language: str = "vi") -> list[ReportFigure]:
    """Plots are drawn only from stored source rows and BE results of this run."""
    vi = language == "vi"
    figures = []
    if run.get("study", {}).get("design") == "2x2":
        figures.append(_design_figure(vi))
    for log in (False, True):
        figure = _profiles_figure(run.get("validated_data", []), vi=vi, log=log, example=False)
        if figure:
            figures.append(figure)
    forest = _forest_figure(run.get("be", []), vi=vi, example=False)
    if forest:
        figures.append(forest)
    return figures
