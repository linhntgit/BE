"""FDA/EMA-inspired Vietnamese PK report presentation from immutable snapshots.

The reports only visualize recorded observations and fit outputs.  No figures,
clinical conclusions or unobserved observations are manufactured.
"""

from __future__ import annotations

import io
import math
from collections import defaultdict
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw

from be_app.pk_analysis import CONCENTRATION_FACTORS
from be_app.report_figures import _font

SOURCES = (
    ("ICH E3 - Structure and Content of Clinical Study Reports",
     "https://www.fda.gov/regulatory-information/search-fda-guidance-documents/"
     "e3-structure-and-content-clinical-study-reports"),
    ("ICH E3(R1) - Hỏi đáp về cách điều chỉnh cấu trúc báo cáo",
     "https://www.fda.gov/regulatory-information/search-fda-guidance-documents/"
     "e3-structure-and-content-clinical-study-reports-questions-and-answers-r1"),
    ("FDA - Clinical Pharmacology Review, NDA 208215 (ví dụ PK)",
     "https://www.accessdata.fda.gov/drugsatfda_docs/nda/2016/"
     "208215Orig1s000ClinPharmR.pdf"),
    ("EMA - Apixaban Accord EPAR, public assessment report (ví dụ PK/BE)",
     "https://www.ema.europa.eu/en/documents/assessment-report/"
     "apixaban-accord-epar-public-assessment-report_en.pdf"),
)

NAVY = "#18324C"
BLUE = "#2576A4"
ORANGE = "#C86B3C"
GRAY = "#526477"
LIGHT = "#DFE7ED"


def shown(value: object) -> str:
    """Readable numeric values, including distinguishing missing from zero."""
    if value is None or (isinstance(value, float) and not math.isfinite(value)):
        return "Chưa xác định"
    if isinstance(value, bool):
        return "Có" if value else "Không"
    if isinstance(value, float):
        return f"{value:.6g}"
    if isinstance(value, (list, tuple)):
        return "; ".join(shown(v) for v in value) if value else "Không có"
    if isinstance(value, dict):
        return "; ".join(f"{k}: {shown(v)}" for k, v in value.items())
    return str(value)


def _summary(snapshot: dict) -> list[list[str]]:
    data = snapshot.get("data") or []
    profiles = {str(row.get("profile_id", "")) for row in data}
    regimen = snapshot.get("regimen") or {}
    return [
        ["Số hồ sơ", str(len(profiles))],
        ["Số dòng nồng độ", str(len(data))],
        ["Kết quả NCA", str(len(snapshot.get("nca") or []))],
        ["Mô hình đã khớp", str(len(snapshot.get("models") or []))],
        ["Chế độ", {"steady_state": "Trạng thái ổn định", "multiple": "Đa liều"}.get(
            str(regimen.get("mode")), "Đơn liều")],
        ["Xác nhận steady-state", "Đã xác nhận ngoài ứng dụng" if
         regimen.get("steady_state_confirmed") else "Không có xác nhận"],
        ["Lỗi phân tích", str(len(snapshot.get("errors") or []))],
    ]


def _headings() -> tuple[str, ...]:
    return (
        "1. Tóm tắt phân tích",
        "2. Dữ liệu đầu vào và thiết kế liều",
        "3. Phương pháp phân tích",
        "4. Kết quả phân tích NCA",
        "5. Kết quả mô hình ngăn",
        "6. Hình và đồ thị nồng độ",
        "7. Kiểm soát chất lượng và giới hạn",
        "8. Phụ lục dữ liệu quan sát",
        "9. Tài liệu tham khảo và truy xuất",
    )


def _methods(snapshot: dict) -> list[str]:
    cfg = snapshot.get("settings") or {}
    regimen = snapshot.get("regimen")
    integration = {"linear": "hình thang tuyến tính",
                   "linear_up_log_down": "hình thang tuyến tính tăng - log giảm"}.get(
                        str(cfg.get("integration")), shown(cfg.get("integration")))
    paragraphs = [
        "NCA được tính từ thời điểm lấy mẫu và nồng độ trong bản ghi. "
        f"Phương pháp tích phân: {integration}. Các giá trị thiếu và BLQ phải "
        "được diễn giải theo quy tắc xử lý đã chọn; không xem mẫu BLQ là quan sát định lượng.",
        "Mô hình ngăn (nếu có) sử dụng kết quả khớp và phần dư đã lưu. "
        "RMSE, AICc và BIC là chỉ số chẩn đoán khớp mô hình, không chứng minh "
        "tính phù hợp lâm sàng hoặc định danh tham số.",
    ]
    if regimen:
        paragraphs.append(
            "Với đa liều, AUCτ chỉ được báo cáo khi mẫu định lượng hiện diện ở hai biên "
            "của khoảng liều, không có BLQ trong khoảng phân tích. CLss hoặc CL/Fss chỉ "
            "được tính khi có liều, đủ AUCτ và có xác nhận steady-state từ nguồn bên ngoài. "
            "Dự đoán mô hình dựa trên chồng chất tuyến tính cho lịch liều cách đều."
        )
    else:
        paragraphs.append(
            "Thông số phụ thuộc liều và AUC ngoại suy chỉ được diễn giải khi đủ dữ liệu "
            "đầu vào, điểm biên và tiêu chí ước lượng pha cuối."
        )
    return paragraphs


def _limitations(snapshot: dict) -> list[str]:
    warnings: list[str] = []
    for item in snapshot.get("nca") or []:
        warnings.extend(f"Hồ sơ {item.get('profile_id', '?')} - {text}" for text in
                        item.get("warnings", []) or [])
    for item in snapshot.get("models") or []:
        warnings.extend(f"Mô hình {item.get('profile_id', '?')} - {text}" for text in
                        item.get("warnings", []) or [])
    warnings.extend(snapshot.get("errors") or [])
    unique = list(dict.fromkeys(str(item) for item in warnings))
    return unique or ["Không có cảnh báo ghi nhận trong bản snapshot."]


def _report_figure(rows: list[dict], models: list[dict], profile_id: str,
                   *, log: bool = False, residual: bool = False,
                   concentration_factor: float = 1.0) -> bytes | None:
    """Draw an actual-snapshot graph using Pillow; report generation needs no browser."""
    points = sorted((r for r in rows if str(r.get("profile_id")) == profile_id),
                    key=lambda r: float(r["time_h"]))
    candidates = [m for m in models if str(m.get("profile_id")) == profile_id]
    if not points or (residual and not candidates):
        return None
    w, h = 1280, 660
    img = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(img)
    d.text((65, 22), f"Hồ sơ {profile_id} - " + (
        "Phần dư mô hình" if residual else "Nồng độ theo thời gian (bán log)" if log
        else "Nồng độ theo thời gian (tuyến tính)"), font=_font(29, bold=True), fill=NAVY)
    left, top, right, bottom = 128, 100, 1170, 500
    t_data = [float(row["time_h"]) for row in points]
    # Observations retain the source unit; model predictions are in ng/mL.
    observed = [(float(row["time_h"]), float(row["concentration"]) * concentration_factor)
                for row in points if not row.get("blq") and row.get("concentration") is not None]
    series: list[tuple[str, str, list[tuple[float, float]], bool]] = []
    if not residual:
        series.append(("Quan sát", BLUE, observed, True))
        for item in candidates[:3]:
            curve = [(float(t), float(c)) for t, c in zip(
                item.get("time_h", []), item.get("predicted", []), strict=False)
                if t is not None and c is not None]
            series.append((f"Dự đoán {item.get('compartments')} ngăn", ORANGE, curve, False))
    else:
        for item in candidates[:3]:
            curve = [(float(t), float(c)) for t, c in zip(
                item.get("time_h", []), item.get("residuals", []), strict=False)
                if t is not None and c is not None]
            series.append((f"Phần dư {item.get('compartments')} ngăn", ORANGE, curve, True))
    all_values = [y for _, _, curve, _ in series for _, y in curve
                  if math.isfinite(y) and (y > 0 if log else True)]
    if not all_values:
        return None
    ymin, ymax = min(all_values), max(all_values)
    if residual:
        extent = max(abs(ymin), abs(ymax), 1e-8) * 1.12
        ymin, ymax = -extent, extent
    elif log:
        ymin, ymax = math.log10(ymin) - .15, math.log10(ymax) + .15
    else:
        ymin, ymax = min(0, ymin), max(ymax * 1.12, 1e-9)
    times = t_data + [t for _, _, curve, _ in series for t, _ in curve]
    tmin, tmax = min(times), max(times)
    if tmax <= tmin:
        tmax = tmin + 1
    def xy(t: float, concentration: float) -> tuple[int, int]:
        yy = math.log10(concentration) if log else concentration
        return (round(left + (t-tmin)/(tmax-tmin)*(right-left)),
                round(bottom - (yy-ymin)/(ymax-ymin)*(bottom-top)))
    for i in range(6):
        y = top + (bottom-top) * i/5
        d.line([(left, y), (right, y)], fill=LIGHT, width=2)
        value = ymax - (ymax-ymin) * i/5
        if abs(value) < 1e-10:
            value = 0.0
        label = f"{10**value:.3g}" if log else f"{value:.3g}"
        d.text((18, y-13), label, font=_font(19), fill=GRAY)
        x = left + (right-left)*i/5
        d.line([(x, top), (x, bottom)], fill="#EDF1F4", width=2)
        d.text((x-27, bottom+10), f"{tmin+(tmax-tmin)*i/5:.3g}", font=_font(19), fill=GRAY)
    if residual and ymin < 0 < ymax:
        d.line([xy(tmin, 0), xy(tmax, 0)], fill=GRAY, width=3)
    for _name, color, curve, marks in series:
        valid = [(t, v) for t, v in curve if math.isfinite(t) and math.isfinite(v)
                 and (v > 0 if log else True)]
        if len(valid) > 1 and not residual:
            d.line([xy(t, v) for t, v in valid], fill=color, width=4)
        if marks:
            for t, v in valid[:500]:
                x, y = xy(t, v)
                d.ellipse((x-4, y-4, x+4, y+4), fill=color)
    blq = [(float(r["time_h"]), float(r.get("concentration") or 0))
           for r in points if r.get("blq")]
    if blq and not residual:
        for t, _ in blq:
            # A BLQ has no quantifiable ordinate, especially on a log axis.
            x = round(left + (t - tmin) / (tmax - tmin) * (right - left))
            d.line([(x-6, bottom-7), (x+6, bottom+5)], fill=GRAY, width=3)
        d.text((735, 65), "BLQ: ký hiệu tại trục thời gian", font=_font(19), fill=GRAY)
    d.text((528, 545), "Thời gian (giờ)", font=_font(23), fill=NAVY)
    d.text((140, 65), "Nồng độ (ng/mL)" if not residual else "Phần dư (ng/mL)",
           font=_font(21), fill=GRAY)
    for idx, (name, color, _, _) in enumerate(series):
        xlegend = 130 + (idx % 2) * 575
        ylegend = 592 + (idx // 2) * 36
        d.line([(xlegend, ylegend), (xlegend+34, ylegend)], fill=color, width=5)
        d.text((xlegend+40, ylegend-13), name, font=_font(17), fill=GRAY)
    output = io.BytesIO()
    img.save(output, format="PNG", optimize=True)
    return output.getvalue()


def report_figures(snapshot: dict, limit: int = 6) -> list[tuple[str, bytes]]:
    rows = snapshot.get("data") or []
    grouped = defaultdict(list)
    for item in rows:
        grouped[str(item.get("profile_id", "?"))].append(item)
    unit = (snapshot.get("settings") or {}).get("concentration_unit", "ng/mL")
    factor = CONCENTRATION_FACTORS.get(unit, 1.0)
    figures = []
    for profile_id in sorted(grouped)[:limit]:
        for log, residual, description in (
            (False, False, "tuyến tính"), (True, False, "bán log"),
            (False, True, "phần dư"),
        ):
            payload = _report_figure(grouped[profile_id], snapshot.get("models") or [],
                                     profile_id, log=log, residual=residual,
                                     concentration_factor=factor)
            if payload:
                figures.append((f"Hồ sơ {profile_id} - {description}", payload))
    return figures


def _representative_rows(snapshot: dict, max_rows: int = 40) -> tuple[list[list[str]], int]:
    original = snapshot.get("data") or []
    unit = (snapshot.get("settings") or {}).get("concentration_unit", "ng/mL")
    table = [["Hồ sơ", "Giờ", f"Cplasma ({unit})", "BLQ"]]
    for item in original[:max_rows]:
        table.append([str(item.get("profile_id", "")), shown(item.get("time_h")),
                      shown(item.get("concentration")), "Có" if item.get("blq") else "Không"])
    return table, max(0, len(original) - max_rows)


def _nca_summary(snapshot: dict) -> list[list[str]]:
    regimen = bool(snapshot.get("regimen"))
    auc = "auc_tau_ng_h_ml" if regimen else "auc_0_inf"
    peak = "cmax_tau_ng_ml" if regimen else "cmax_ng_ml"
    col = "AUCτ" if regimen else "AUC0-inf"
    rows = [["Hồ sơ", "Trạng thái", "Cmax (ng/mL)", f"{col} (ng.h/mL)", "Số mẫu"]]
    for item in snapshot.get("nca") or []:
        rows.append([str(item.get("profile_id", "")), shown(item.get("status")),
                     shown(item.get(peak)), shown(item.get(auc)), shown(item.get("n"))])
    return rows


def _model_summary(snapshot: dict) -> list[list[str]]:
    rows = [["Hồ sơ", "Ngăn", "Trọng số", "RMSE", "AICc", "BIC"]]
    for item in snapshot.get("models") or []:
        rows.append([str(item.get("profile_id", "")), shown(item.get("compartments")),
                     shown(item.get("weighting")), shown(item.get("rmse_ng_ml")),
                     shown(item.get("aicc")), shown(item.get("bic"))])
    return rows


def make_word(snapshot: dict, settings_rows: list[tuple[str, object]],
              nca_rows: list[dict], sha256: str) -> bytes:
    from docx import Document
    from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Cm, Pt, RGBColor

    figures = report_figures(snapshot)
    doc = Document()
    section = doc.sections[0]
    section.page_height, section.page_width = Cm(29.7), Cm(21)
    section.left_margin = section.right_margin = Cm(2)
    section.top_margin = section.bottom_margin = Cm(2.1)
    for name in ("Normal", "Title", "Heading 1", "Heading 2"):
        style = doc.styles[name]
        style.font.name = "Arial"
        style.font.color.rgb = RGBColor.from_string("18324C" if name != "Normal" else "253647")
        for attr in ("eastAsia", "cs"):
            style.element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:" + attr), "Arial")
    doc.styles["Normal"].font.size = Pt(10)
    doc.styles["Normal"].paragraph_format.space_after = Pt(6)
    doc.styles["Title"].font.size = Pt(22)
    doc.styles["Heading 1"].font.size = Pt(14)
    doc.styles["Heading 2"].font.size = Pt(11)
    section.header.paragraphs[0].text = "PHÂN TÍCH DƯỢC ĐỘNG HỌC | BẢN DỰ THẢO"
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run("Báo cáo PK độc lập  |  Trang ")
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    footer._p.append(field)

    def table(rows: list[list[str]], widths: list[float] | None = None) -> None:
        if not rows:
            return
        grid = doc.add_table(rows=1, cols=len(rows[0]))
        grid.autofit = False
        grid.style = "Table Grid"
        for idx, row in enumerate(rows):
            cells = grid.rows[0].cells if idx == 0 else grid.add_row().cells
            for j, (cell, val) in enumerate(zip(cells, row, strict=False)):
                cell.text = str(val)
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                if widths:
                    cell.width = Cm(widths[j])
                for p in cell.paragraphs:
                    p.paragraph_format.space_before = Pt(3)
                    p.paragraph_format.space_after = Pt(3)
                    for run in p.runs:
                        run.font.size = Pt(8.5)
                        if idx == 0:
                            run.bold = True
                if idx == 0 or idx % 2 == 0:
                    shade = OxmlElement("w:shd")
                    shade.set(qn("w:fill"), "DFE7ED" if idx == 0 else "F4F7F9")
                    cell._tc.get_or_add_tcPr().append(shade)
            if idx == 0:
                repeat = OxmlElement("w:tblHeader")
                grid.rows[0]._tr.get_or_add_trPr().append(repeat)
        doc.add_paragraph()

    doc.add_paragraph("BÁO CÁO PHÂN TÍCH DƯỢC ĐỘNG HỌC ĐỘC LẬP", "Title")
    doc.add_paragraph("DỰ THẢO - CHƯA THẨM ĐỊNH ĐỘC LẬP CHO QUYẾT ĐỊNH PHÁP LÝ")
    doc.add_paragraph(f"Ngày UTC: {snapshot.get('created_utc', '')}")
    doc.add_paragraph(f"Nguồn dữ liệu: {snapshot.get('source', '')}")
    doc.add_paragraph("Bố cục tham khảo ICH E3 và ví dụ báo cáo công khai FDA/EMA; "
                      "đây không phải báo cáo do FDA/EMA phát hành hoặc phê duyệt.")
    label = doc.add_paragraph("THÔNG TIN TỔNG QUAN")
    label.runs[0].bold = True
    label.runs[0].font.color.rgb = RGBColor.from_string("2576A4")
    table([["Chỉ tiêu", "Giá trị"], *_summary(snapshot)[:5]], [6.5, 10.5])
    if figures:
        label = doc.add_paragraph("BIỂU ĐỒ NỒNG ĐỘ MINH HOẠ TỪ DỮ LIỆU")
        label.runs[0].bold = True
        label.runs[0].font.color.rgb = RGBColor.from_string("2576A4")
        preview = doc.add_paragraph()
        preview.alignment = WD_ALIGN_PARAGRAPH.CENTER
        preview.add_run().add_picture(io.BytesIO(figures[0][1]), width=Cm(15))
        doc.add_paragraph("Đồ thị đầu tiên từ dữ liệu đã ghi nhận; nội dung chi tiết ở mục 6.")
    doc.add_page_break()
    doc.add_paragraph("MỤC LỤC", "Title")
    doc.add_paragraph("Trong Microsoft Word, nhấn chuột phải vào mục lục và chọn 'Update Field' "
                      "hoặc nhấn Ctrl+A, F9 để cập nhật số trang.")
    p = doc.add_paragraph()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instruction = OxmlElement("w:instrText")
    instruction.set(qn("xml:space"), "preserve")
    instruction.text = ' TOC \\o "1-2" \\h \\z \\u '
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    for part in (begin, instruction, separate, end):
        p.add_run()._r.append(part)
    update = OxmlElement("w:updateFields")
    update.set(qn("w:val"), "true")
    doc.settings.element.append(update)
    doc.add_page_break()

    headings = _headings()
    doc.add_heading(headings[0], 1)
    table([["Chỉ tiêu", "Giá trị"], *_summary(snapshot)], [6.5, 10.5])
    doc.add_paragraph("Bản báo cáo mô tả các thông số PK được tính từ dữ liệu trong phiên "
                      "phân tích; trạng thái ổn định chỉ được ghi nhận khi có xác nhận từ bên ngoài.")
    doc.add_heading(headings[1], 1)
    table([["Thuộc tính", "Giá trị"], *[[str(k), shown(v)] for k, v in settings_rows]], [8, 9])
    doc.add_heading(headings[2], 1)
    for line in _methods(snapshot):
        doc.add_paragraph(line)
    doc.add_heading(headings[3], 1)
    if nca_rows:
        table(_nca_summary(snapshot))
        for idx, item in enumerate(nca_rows, 1):
            doc.add_heading(f"4.{idx} Hồ sơ {item.get('Mã hồ sơ', '?')}", 2)
            table([["Thông số", "Giá trị"], *[[str(k), shown(v)] for k, v in item.items()
                                                if k != "Mã hồ sơ"]], [9.5, 7.5])
    else:
        doc.add_paragraph("Không có kết quả NCA trong phiên phân tích.")
    doc.add_heading(headings[4], 1)
    if snapshot.get("models"):
        table(_model_summary(snapshot))
        for idx, model in enumerate(snapshot["models"], 1):
            doc.add_heading(f"5.{idx} Hồ sơ {model['profile_id']} - {model['compartments']} ngăn", 2)
            table([["Tham số / kiểm định", "Giá trị"],
                   *[[str(k), shown(v)] for k, v in model.get("parameters", {}).items()],
                   ["Hội tụ", shown(model.get("converged"))],
                   ["Điều kiện Jacobian", shown(model.get("jacobian_condition"))]])
    else:
        doc.add_paragraph("Không yêu cầu hoặc chưa khớp mô hình ngăn.")
    doc.add_heading(headings[5], 1)
    if figures:
        for i, (caption, png) in enumerate(figures, 1):
            doc.add_heading(f"6.{i} {caption}", 2)
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.add_run().add_picture(io.BytesIO(png), width=Cm(16.6))
            doc.add_paragraph(f"Hình {i}. Vẽ từ dữ liệu và mô hình trong snapshot; "
                              "BLQ không được nối vào đường quan sát.")
    else:
        doc.add_paragraph("Không có dữ liệu định lượng phù hợp để vẽ đồ thị.")
    if len({str(r.get('profile_id')) for r in snapshot.get('data', [])}) > 6:
        doc.add_paragraph("Chỉ thể hiện hình của 6 hồ sơ đầu; dữ liệu đầy đủ có trong Excel/JSON.")
    doc.add_heading(headings[6], 1)
    for warning_text in _limitations(snapshot):
        doc.add_paragraph(warning_text, style="List Bullet")
    doc.add_paragraph("Không sử dụng bản DỰ THẢO để kết luận tính tương đương sinh học, "
                      "đánh giá hiệu quả hoặc ra quyết định quản lý khi chưa được thẩm định.")
    doc.add_heading(headings[7], 1)
    rows, skipped = _representative_rows(snapshot)
    table(rows)
    if skipped:
        doc.add_paragraph(f"Hiển thị 40 mẫu đầu; còn {skipped} mẫu trong Excel/JSON xuất cùng phiên.")
    doc.add_heading(headings[8], 1)
    doc.add_paragraph(f"SHA-256 bản ghi: {sha256}")
    for title, url in SOURCES:
        doc.add_paragraph(f"{title}: {url}")
    doc.add_paragraph("Các nguồn trên dùng để tham khảo cấu trúc trình bày; không xác nhận "
                      "phương pháp hay kết quả của phần mềm.")
    output = io.BytesIO()
    doc.save(output)
    return output.getvalue()


def make_pdf(snapshot: dict, settings_rows: list[tuple[str, object]],
             nca_rows: list[dict], sha256: str) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (
        BaseDocTemplate,
        Frame,
        KeepTogether,
        LongTable,
        PageBreak,
        PageTemplate,
        Paragraph,
        TableStyle,
    )
    from reportlab.platypus import Image as PDFImage
    from reportlab.platypus.tableofcontents import TableOfContents

    if "PKUnicode" not in pdfmetrics.getRegisteredFontNames():
        paths = (Path("C:/Windows/Fonts/arial.ttf"),
                 Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
        source = next((candidate for candidate in paths if candidate.is_file()), None)
        if source is None:
            raise ValueError("Không tìm thấy font Unicode để xuất PDF tiếng Việt.")
        pdfmetrics.registerFont(TTFont("PKUnicode", str(source)))
    normal = ParagraphStyle("PKBody", fontName="PKUnicode", fontSize=9, leading=14, spaceAfter=8)
    small = ParagraphStyle("PKSmall", parent=normal, fontSize=7.6, leading=11, spaceAfter=3)
    title = ParagraphStyle("PKTitle", parent=normal, fontSize=18, leading=25,
                           textColor=colors.HexColor(NAVY), spaceAfter=16)
    h1 = ParagraphStyle("PKHeading1", parent=normal, fontSize=13, leading=19,
                        textColor=colors.HexColor(NAVY), spaceBefore=15, spaceAfter=10,
                        keepWithNext=True)
    h2 = ParagraphStyle("PKHeading2", parent=normal, fontSize=10.5, leading=15,
                        textColor=colors.HexColor(BLUE), spaceBefore=12,
                        spaceAfter=6, keepWithNext=True)
    cover_label = ParagraphStyle("PKCoverLabel", parent=h2, keepWithNext=True)
    caption = ParagraphStyle("PKCaption", parent=small, alignment=TA_CENTER, spaceAfter=11)
    w, h = A4
    figures = report_figures(snapshot)
    output = io.BytesIO()

    class PKDoc(BaseDocTemplate):
        def __init__(self, buffer):
            super().__init__(buffer, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm,
                             topMargin=2.25*cm, bottomMargin=2.05*cm,
                             title="Báo cáo phân tích dược động học độc lập")
            frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height,
                          leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
            self.addPageTemplates(PageTemplate(id="body", frames=frame, onPage=self.decorate))
            self._heading_key = 0

        def beforeDocument(self):
            # multiBuild reruns the story until page numbers and TOC stabilize.
            # Bookmarks must retain the same keys on every layout pass.
            self._heading_key = 0

        def decorate(self, canvas, document):
            canvas.saveState()
            canvas.setFont("PKUnicode", 8)
            canvas.setFillColor(colors.HexColor(NAVY))
            canvas.drawString(2*cm, h-1.4*cm, "PHÂN TÍCH PK ĐỘC LẬP  |  DỰ THẢO")
            canvas.setStrokeColor(colors.HexColor(LIGHT))
            canvas.line(2*cm, h-1.57*cm, w-2*cm, h-1.57*cm)
            canvas.setFillColor(colors.HexColor(GRAY))
            canvas.drawString(2*cm, 1.35*cm, "PK độc lập - chưa thẩm định pháp lý")
            canvas.drawRightString(w-2*cm, 1.35*cm, f"Trang {document.page}")
            canvas.restoreState()

        def afterFlowable(self, flowable):
            if isinstance(flowable, Paragraph) and flowable.style.name in ("PKHeading1", "PKHeading2"):
                level = 0 if flowable.style.name == "PKHeading1" else 1
                key = f"section_{self._heading_key}"
                self._heading_key += 1
                title_text = flowable.getPlainText()
                self.canv.bookmarkPage(key)
                self.notify("TOCEntry", (level, title_text, self.page, key))

    def para(text: object, style=normal):
        return Paragraph(escape(shown(text)), style)

    def table(rows: list[list[str]], widths: list[float] | None = None):
        if widths is None:
            widths = [17*cm/len(rows[0])] * len(rows[0])
        else:
            widths = [n*cm for n in widths]
        cells = [[para(cell, small) for cell in row] for row in rows]
        grid = LongTable(cells, colWidths=widths, repeatRows=1, hAlign="LEFT")
        grid.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(LIGHT)),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F7F9")]),
            ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#CFD8E0")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        return grid

    story = [para("BÁO CÁO PHÂN TÍCH DƯỢC ĐỘNG HỌC ĐỘC LẬP", title),
             para("DỰ THẢO - CHƯA THẨM ĐỊNH ĐỘC LẬP CHO QUYẾT ĐỊNH PHÁP LÝ"),
             para(f"Ngày UTC: {snapshot.get('created_utc', '')}"),
             para(f"Nguồn dữ liệu: {snapshot.get('source', '')}"),
             para("Cấu trúc tham khảo ICH E3 và báo cáo FDA/EMA; không phải tài liệu "
                  "do cơ quan quản lý phê duyệt."),
             para("THÔNG TIN TỔNG QUAN", cover_label),
             table([["Chỉ tiêu", "Giá trị"], *_summary(snapshot)[:5]], [6.5, 10.5])]
    if figures:
        story.extend([
            para("BIỂU ĐỒ NỒNG ĐỘ MINH HOẠ TỪ DỮ LIỆU", cover_label),
            PDFImage(io.BytesIO(figures[0][1]), width=15*cm, height=7.75*cm),
            para("Đồ thị đầu tiên từ dữ liệu đã ghi nhận; nội dung chi tiết ở mục 6.", caption),
        ])
    story.extend([PageBreak(), para("MỤC LỤC", title)])
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle("PKTOC1", parent=normal, fontSize=9, leading=15, leftIndent=5,
                       firstLineIndent=0, spaceAfter=4),
        ParagraphStyle("PKTOC2", parent=small, leftIndent=20, firstLineIndent=0),
    ]
    story.extend([toc, PageBreak()])
    headings = _headings()
    def section(i: int):
        story.append(para(headings[i], h1))
    section(0)
    story.append(table([["Chỉ tiêu", "Giá trị"], *_summary(snapshot)], [6.5, 10.5]))
    story.append(para("Trạng thái ổn định chỉ được báo cáo khi đã xác nhận ngoài ứng dụng."))
    section(1)
    story.append(table([["Thuộc tính", "Giá trị"], *[[str(k), shown(v)] for k, v in settings_rows]], [8, 9]))
    section(2)
    story.extend(para(item) for item in _methods(snapshot))
    section(3)
    if nca_rows:
        story.append(table(_nca_summary(snapshot), [2.4, 4, 4, 4.4, 2.2]))
        for item in nca_rows:
            story.append(para(f"Hồ sơ {item.get('Mã hồ sơ', '?')}", h2))
            story.append(table([["Thông số", "Giá trị"], *[[str(k), shown(v)] for k, v in item.items()
                                                        if k != "Mã hồ sơ"]], [9.5, 7.5]))
    else:
        story.append(para("Không có kết quả NCA trong phiên phân tích."))
    section(4)
    if snapshot.get("models"):
        story.append(table(_model_summary(snapshot), [3, 1.6, 3.2, 3.1, 3.1, 3]))
        for model in snapshot["models"]:
            story.append(para(f"Hồ sơ {model['profile_id']} - {model['compartments']} ngăn", h2))
            story.append(table([["Tham số / kiểm định", "Giá trị"],
                                *[[str(k), shown(v)] for k, v in model.get("parameters", {}).items()],
                                ["Hội tụ", shown(model.get("converged"))],
                                ["Điều kiện Jacobian", shown(model.get("jacobian_condition"))]], [8, 9]))
    else:
        story.append(para("Không yêu cầu hoặc chưa khớp mô hình ngăn."))
    section(5)
    if figures:
        for i, (label, png) in enumerate(figures, 1):
            graphic = PDFImage(io.BytesIO(png), width=16.5*cm, height=8.5*cm)
            story.append(KeepTogether([
                para(f"Hình {i}. {label}", h2),
                graphic,
                para("Hình dựa trên dữ liệu snapshot; "
                     "BLQ không được nối vào đường quan sát.", caption),
            ]))
    else:
        story.append(para("Không có dữ liệu định lượng phù hợp để vẽ đồ thị."))
    if len({str(r.get('profile_id')) for r in snapshot.get('data', [])}) > 6:
        story.append(para("Chỉ hiển thị hình của 6 hồ sơ đầu; dữ liệu đầy đủ trong Excel/JSON."))
    section(6)
    story.extend(para(f"- {item}") for item in _limitations(snapshot))
    story.append(para("Chưa thẩm định độc lập cho quyết định pháp lý, tương đương sinh học hoặc hiệu quả."))
    section(7)
    raw, skipped = _representative_rows(snapshot)
    story.append(table(raw, [3, 3, 6, 5]))
    if skipped:
        story.append(para(f"Hiển thị 40 mẫu đầu; còn {skipped} mẫu trong Excel/JSON."))
    section(8)
    story.append(para(f"SHA-256: {sha256}"))
    story.extend(para(f"{label}: {url}") for label, url in SOURCES)
    story.append(para("Tài liệu tham khảo chỉ được dùng cho cấu trúc báo cáo, "
                      "không hàm ý FDA/EMA/ICH đã thẩm định phần mềm."))
    PKDoc(output).multiBuild(story, maxPasses=5)
    return output.getvalue()
