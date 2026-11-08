"""Editable, pre-analysis BE study protocol drafts in Vietnamese Word and PDF.

Protocol content is sourced from the current study plus explicit planning notes.
It never asserts that a study has been conducted or a protocol approved.
"""

import io
from xml.sax.saxutils import escape

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from be_app.branding import software_attribution
from be_app.design import SEQUENCES
from be_app.persistence import Project
from be_app.regulations import RULES, capability_for
from be_app.reporting import _register_pdf_font

MISSING = "[CẦN BỔ SUNG / XÁC NHẬN]"
STATUS = "DỰ THẢO ĐỀ CƯƠNG — CHƯA ĐƯỢC PHÊ DUYỆT"

PROTOCOL_FIELDS = (
    ("rationale", "Cơ sở khoa học và lý do chọn thiết kế"),
    ("population", "Quần thể tuyển chọn, tiêu chuẩn nhận và loại trừ"),
    ("sample_size", "Căn cứ cỡ mẫu khi chưa có kết quả tính hợp lệ"),
    ("washout", "Thời gian washout và căn cứ lựa chọn"),
    ("sampling", "Lịch lấy mẫu nồng độ theo thời điểm dự kiến"),
    ("administration", "Cách dùng thuốc, kiểm soát ăn uống và lịch khám"),
    ("bioanalysis", "Phương pháp định lượng và thẩm định bioanalytical"),
    ("safety", "Theo dõi an toàn và xử trí AE/SAE"),
    ("ethics", "Hội đồng đạo đức, đồng thuận và bảo mật"),
    ("statistics", "Chi tiết SAP, quần thể phân tích và dữ liệu thiếu"),
    ("operations", "Phân công, lưu trữ, QC và kế hoạch vận hành"),
)


def _filled(value: object) -> str:
    text = str(value).strip() if value is not None else ""
    return text if text else MISSING


def _row(label: str, value: object) -> tuple[str, str]:
    return label, _filled(value)


def protocol_content(project: Project, details: dict[str, str] | None = None,
                     *, valid_plan: dict | None = None) -> dict:
    """Return an ordered outline without changing project or accepting stale planning."""
    study = project.study
    rule = RULES[study.rule_set_id]
    capability = capability_for(study.rule_set_id)
    details = details or {}

    def note(key: str) -> str:
        return _filled(details.get(key))

    sample_size = (
        f"Kế hoạch tính từ giả định đã nhập: N đánh giá {valid_plan['evaluable']}; "
        f"N tuyển {valid_plan['recruit']}; endpoint chi phối {valid_plan['curve_endpoint']}. "
        f"Giả định CV/GMR, dropout, nguồn dữ liệu và quần thể phải được đối chiếu với SAP "
        f"trước khi sử dụng."
        if valid_plan is not None else note("sample_size")
    )
    if valid_plan is not None:
        sample_size += f"\nGiả định và nguồn tham khảo: {_filled(valid_plan.get('inputs', {}).get('source'))}."
    scaled = (
        "Scaling được đánh dấu đã định trước; phải kiểm tra điều kiện CVwR, giới hạn và "
        "điều kiện bổ sung của profile trước khi áp dụng."
        if study.scaled_be_prespecified else
        "Chưa xác nhận scaling đã định trước; không mặc định sử dụng giới hạn mở rộng."
    )
    if study.rule_set_id == "EMA_HVDP_ABEL":
        method = "EMA ABEL: xem xét mở rộng biên Cmax có điều kiện dựa vào CVwR của R; AUC đánh giá riêng."
    elif study.rule_set_id == "FDA_HVD_RSABE_2026":
        method = "FDA RSABE: kiểm tra tiêu chí scaled/UCB cùng các điều kiện phụ trợ và nhánh fallback khi áp dụng."
    elif study.rule_set_id == "FDA_NTI":
        method = "FDA NTI: mô hình replicate và tiêu chí biến thiên, thử/đối chứng theo hướng dẫn áp dụng."
    elif study.rule_set_id == "EMA_NTI":
        method = "EMA NTI: cân nhắc biên AUC thu hẹp, và Cmax khi có căn cứ lâm sàng."
    elif "REPLICATE" in study.rule_set_id:
        method = "Replicate ABE: sử dụng mô hình có xét cấu trúc chuỗi/kỳ và phương sai phù hợp."
    else:
        method = "ABE: mô hình trên ln(PK), tỷ số trung bình hình học T/R và khoảng tin cậy 90% (TOST)."

    summary = [
        _row("Mã nghiên cứu", study.study_id),
        _row("Tên nghiên cứu", study.title),
        _row("Mã/phiên bản protocol", study.protocol),
        _row("Mã/phiên bản SAP", study.sap),
        _row("Nhà tài trợ", study.sponsor),
        _row("Cơ sở thực hiện", study.study_site),
        _row("Nghiên cứu viên chính", study.principal_investigator),
        _row("Hoạt chất", study.active_ingredient),
        _row("Trạng thái", "No (sau ăn)" if study.fed_state == "fed" else "Đói (nhịn ăn)"),
        _row("Thiết kế", {"2x2": "Crossover 2×2", "parallel": "Song song",
                             "partial3": "Partial replicate 3 kỳ", "full4": "Full replicate 4 kỳ"}[study.design]),
        _row("Quy tắc đánh giá", study.rule_set_id),
    ]
    products = [
        ("Thuốc thử (T)", study.test_product, study.test_strength, study.test_concentration,
         study.test_dosage_form, study.test_manufacturer, study.test_batch, study.test_expiry_date),
        ("Thuốc đối chứng (R)", study.reference_product, study.reference_strength,
         study.reference_concentration, study.reference_dosage_form, study.reference_manufacturer,
         study.reference_batch, study.reference_expiry_date),
    ]
    product_table = [
        ("Thuốc", "Tên thuốc", "Hàm lượng", "Nồng độ", "Dạng bào chế", "Nhà sản xuất", "Số lô", "Hạn dùng"),
        *[tuple(_filled(value) for value in row) for row in products],
    ]
    sections = [
        ("1", "Tóm tắt đề cương", [
            f"Mục tiêu: đánh giá tương đương sinh học của {_filled(study.test_product)} so với "
            f"{_filled(study.reference_product)} đối với hoạt chất {_filled(study.active_ingredient)}.",
            f"Thiết kế: {summary[-2][1]}; trình tự dự kiến: {', '.join(SEQUENCES[study.design])}. "
            f"Đường dùng: {_filled(study.route)}; đơn liều: {'có' if study.single_dose else 'không'}; "
            f"liều dự kiến: {study.dose:g} {_filled(study.dose_unit)}; tình trạng: {summary[-3][1]}.",
            f"Endpoint chính: {', '.join(study.primary_endpoints)}. "
            f"Endpoint phụ: {', '.join(study.secondary_endpoints) or MISSING}.",
        ]),
        ("2", "Cơ sở khoa học và mục tiêu", [
            f"Căn cứ lựa chọn sản phẩm, liều, điều kiện đói/no và thiết kế: {note('rationale')}",
            f"Phạm vi hướng dẫn: {rule.guideline} ({rule.section}); rà soát guidance đặc thù sản phẩm, "
            "dạng bào chế và thị trường trước khi phê duyệt.",
        ]),
        ("3", "Sản phẩm nghiên cứu và quản lý thuốc", [
            "Thuốc thử (T) và thuốc đối chứng (R) được đối chiếu với nhãn, CoA, nguồn cung cấp, "
            "hồ sơ lô, bảo quản, cấp phát và thu hồi. Bảng thông tin chi tiết ở đầu đề cương.",
            "Cần mô tả ngẫu nhiên hóa mã thuốc, kiểm soát cấp phát, trách nhiệm của nhân sự và hồ sơ truy xuất.",
        ]),
        ("4", "Thiết kế, ngẫu nhiên hóa và washout", [
            f"Thiết kế đã khai báo: {summary[-2][1]}; sequence dự kiến: {', '.join(SEQUENCES[study.design])}. "
            "Mô tả quy trình cấp mã, phân bổ, thay thế/rút lui và duy trì tính tái lập theo protocol.",
            f"Washout giữa các kỳ và căn cứ bán thải/PK: {note('washout')}",
            f"Điều kiện dùng thuốc và kiểm soát bữa ăn/nước uống: {note('administration')}",
        ]),
        ("5", "Đối tượng và tiêu chuẩn tuyển chọn", [
            f"Quần thể mục tiêu, độ tuổi, sức khỏe, tiêu chuẩn nhận/loại và xét nghiệm sàng lọc: {note('population')}",
            "Bổ sung quy trình đồng thuận, tuyển chọn, tiêu chí ngừng tham gia, theo dõi người rút lui "
            "và danh sách quần thể an toàn/PK theo SAP.",
        ]),
        ("6", "Cỡ mẫu và giả định thống kê", [
            f"Cỡ mẫu dự kiến: {sample_size}",
            f"Thiết kế {study.design}; profile {study.rule_set_id}. Chức năng tính power trong app: "
            f"{'được hỗ trợ cho profile này' if capability.planning else 'chưa được thẩm định/hỗ trợ cho profile này'}. "
            "Cần xác nhận giả định GMR, CV, tỷ lệ rút lui và sức mạnh thống kê cho các endpoint chính.",
        ]),
        ("7", "Quy trình nghiên cứu và lịch lấy mẫu", [
            f"Liều sử dụng: {study.dose:g} {_filled(study.dose_unit)}; đường dùng: {_filled(study.route)}. "
            f"Chi tiết điều trị/ăn uống: {note('administration')}",
            f"Lịch lấy mẫu: {note('sampling')}",
            "Xác định các điểm trước liều, giai đoạn hấp thu, gần Cmax và pha thải trừ; "
            "ghi thời điểm thực tế, xử lý mẫu, nhiệt độ, lưu mẫu và chain of custody.",
        ]),
        ("8", "Phân tích mẫu sinh học và thông số dược động học", [
            f"Chất phân tích: {_filled(study.analyte)}. Phương pháp định lượng, LLOQ, ổn định mẫu, "
            f"thẩm định phương pháp và QA: {note('bioanalysis')}",
            "NCA xác định Cmax, tmax, AUC0–t, AUC0–∞ khi phù hợp, λz và t1/2; "
            "phải quy định trước BLQ, sai lệch thời gian, pha terminal và ngoại suy trong SAP.",
        ]),
        ("9", "Kế hoạch phân tích thống kê (SAP)", [
            f"Phương pháp dự kiến: {method}",
            f"Scaling/NTI: {scaled} NTI khai báo: {'có' if study.nti else 'không'}. "
            f"Căn cứ HVD: {_filled(study.hvd_justification)}.",
            f"Kế hoạch quần thể, mô hình, phương sai, handling dữ liệu thiếu/ngoại lệ: {note('statistics')}",
            "Mọi biên chấp nhận, tiêu chí phụ, fallback và độ phù hợp của profile cần ghi chính xác "
            "trong protocol/SAP trước khi mở mù hoặc khóa dữ liệu; không suy kết luận từ kết quả giả lập.",
        ]),
        ("10", "Đánh giá an toàn", [
            f"Theo dõi AE/SAE, dấu hiệu sinh tồn, xét nghiệm, quy trình báo cáo khẩn: {note('safety')}",
            "Chỉ định rõ lịch khám, người chịu trách nhiệm, tiêu chí dừng nghiên cứu và quy trình xử trí.",
        ]),
        ("11", "Đạo đức, quyền lợi và bảo mật", [
            f"Đánh giá Hội đồng đạo đức, phiếu đồng thuận, đăng ký nghiên cứu và bảo mật: {note('ethics')}",
            "Chỉ tiến hành nghiên cứu sau khi có phê duyệt phù hợp; bản xuất phần mềm không thay thế phê duyệt.",
        ]),
        ("12", "Data Integrity, quản lý dữ liệu và QC", [
            f"Phân công, chứng từ nguồn, nhập liệu kép/đối chiếu, quyền truy cập, backup: {note('operations')}",
            "Áp dụng ALCOA+; lưu bản gốc, lý do sửa, dấu vết kiểm toán, version protocol/SAP; "
            "định nghĩa vai trò xác nhận dữ liệu, Data Freeze và quản lý deviations trước phân tích.",
        ]),
        ("13", "Tiến độ dự kiến và trách nhiệm", [
            f"Toàn nghiên cứu: {_filled(study.study_start_date)} đến {_filled(study.study_end_date)}; "
            f"lâm sàng: {_filled(study.clinical_start_date)} đến {_filled(study.clinical_end_date)}.",
            f"Bioanalytical: {_filled(study.bioanalytical_start_date)} đến "
            f"{_filled(study.bioanalytical_end_date)}; khóa dữ liệu: {_filled(study.data_lock_date)}.",
            f"Nhà tài trợ: {_filled(study.sponsor)}; nghiên cứu viên chính: {_filled(study.principal_investigator)}. "
            f"Các bước thực hiện: {note('operations')}",
        ]),
        ("14", "Quản lý sửa đổi đề cương và phê duyệt", [
            f"Protocol: {_filled(study.protocol)}; SAP: {_filled(study.sap)}. "
            "Đính kèm lịch sử sửa đổi, lý do, ngày có hiệu lực, chữ ký người soạn, rà soát và phê duyệt.",
            "Trạng thái tài liệu hiện tại: DỰ THẢO, chưa có chữ ký phê duyệt từ hệ thống.",
        ]),
        ("15", "Tài liệu tham khảo và phụ lục", [
            f"Hướng dẫn: {rule.guideline}; phiên bản quy tắc phần mềm: {rule.version}; "
            f"ngày nguồn được rà soát trong registry: {rule.source_verified_on}.",
            *(f"Nguồn chính thức {i}: {source}" for i, source in enumerate(rule.sources, 1)),
            "Phụ lục phải bổ sung: lịch lấy mẫu có đơn vị, sơ đồ nghiên cứu, quy trình ngẫu nhiên hóa, "
            "biểu mẫu CRF, danh mục xét nghiệm, phương pháp bioanalytical và mẫu báo cáo AE/SAE.",
        ]),
    ]
    return {"title": study.title, "study_id": study.study_id, "summary": summary,
            "product_table": product_table, "sections": sections,
            "training": study.is_demo or study.data_purpose == "training_qa"}


def docx_protocol(project: Project, details: dict[str, str] | None = None,
                  *, valid_plan: dict | None = None) -> bytes:
    content = protocol_content(project, details, valid_plan=valid_plan)
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.top_margin = sec.bottom_margin = Cm(2)
    sec.left_margin = sec.right_margin = Cm(1.8)
    for name in ("Normal", "Title", "Heading 1", "Heading 2"):
        style = doc.styles[name]
        style.font.name = "Arial"
        style.font.color.rgb = RGBColor(0, 0, 0)
    doc.styles["Normal"].font.size = Pt(10)
    footer = sec.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run(software_attribution()).font.size = Pt(8)

    doc.add_paragraph("ĐỀ CƯƠNG NGHIÊN CỨU TƯƠNG ĐƯƠNG SINH HỌC", "Title")
    doc.add_paragraph(STATUS)
    if content["training"]:
        doc.add_paragraph("DỮ LIỆU ĐÀO TẠO/GIẢ LẬP — KHÔNG SỬ DỤNG CHO NGHIÊN CỨU THỰC")
    doc.add_heading("Thông tin hành chính và thiết kế", level=1)
    table = doc.add_table(rows=0, cols=2)
    table.style = "Table Grid"
    for label, value in content["summary"]:
        cells = table.add_row().cells
        cells[0].text, cells[1].text = label, value

    doc.add_heading("Thuốc thử và thuốc đối chứng", level=1)
    for product in content["product_table"][1:]:
        doc.add_heading(product[0], level=2)
        detail_table = doc.add_table(rows=0, cols=2)
        detail_table.style = "Table Grid"
        for label, value in zip(content["product_table"][0][1:], product[1:], strict=True):
            cells = detail_table.add_row().cells
            cells[0].text, cells[1].text = label, value
    for number, title, paragraphs in content["sections"]:
        doc.add_heading(f"{number}. {title}", level=1)
        for item in paragraphs:
            doc.add_paragraph(item)
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def pdf_protocol(project: Project, details: dict[str, str] | None = None,
                 *, valid_plan: dict | None = None) -> bytes:
    content = protocol_content(project, details, valid_plan=valid_plan)
    font = _register_pdf_font()
    styles = getSampleStyleSheet()
    for style_name in ("Title", "Normal", "Heading1", "Heading2"):
        styles[style_name].fontName = font
        styles[style_name].textColor = colors.black
    styles["Normal"].fontSize, styles["Normal"].leading = 9, 14
    styles["Heading1"].fontSize, styles["Heading1"].leading = 12, 16
    styles["Heading2"].fontSize, styles["Heading2"].leading = 10, 14
    styles["Heading1"].keepWithNext = True
    small = ParagraphStyle("ProtocolSmall", fontName=font, fontSize=8, leading=12)

    def para(value: str, style="Normal"):
        return Paragraph(escape(value).replace("\n", "<br/>"), styles[style])

    elements = [para("ĐỀ CƯƠNG NGHIÊN CỨU TƯƠNG ĐƯƠNG SINH HỌC", "Title"),
                para(STATUS)]
    if content["training"]:
        elements.append(para("DỮ LIỆU ĐÀO TẠO/GIẢ LẬP — KHÔNG SỬ DỤNG CHO NGHIÊN CỨU THỰC"))
    elements.append(para("Thông tin hành chính và thiết kế", "Heading1"))

    def table(rows):
        result = Table([[Paragraph(escape(str(cell)), small) for cell in row] for row in rows],
                       colWidths=[4.9 * cm, 11.5 * cm], repeatRows=0, hAlign="LEFT")
        result.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.35, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        return result

    elements.append(table(content["summary"]))
    elements.append(Spacer(1, 10))
    elements.append(para("Thuốc thử và thuốc đối chứng", "Heading1"))
    for product in content["product_table"][1:]:
        elements.append(para(product[0], "Heading2"))
        elements.append(table(list(zip(content["product_table"][0][1:], product[1:], strict=True))))
        elements.append(Spacer(1, 8))
    for number, title, paragraphs in content["sections"]:
        elements.append(KeepTogether([para(f"{number}. {title}", "Heading1"), para(paragraphs[0])]))
        for item in paragraphs[1:]:
            elements.append(para(item))
        elements.append(Spacer(1, 5))

    out = io.BytesIO()

    def page(canvas, document):
        canvas.setFont(font, 7)
        canvas.drawString(1.6 * cm, 28.4 * cm, STATUS)
        canvas.drawString(1.6 * cm, 1.1 * cm, software_attribution())
        canvas.drawRightString(19.2 * cm, 1.1 * cm, f"{content['study_id']} | {document.page}")

    SimpleDocTemplate(out, pagesize=(21 * cm, 29.7 * cm), leftMargin=2 * cm,
                      rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
                      title=f"Đề cương BE - {content['study_id']}").build(
                          elements, onFirstPage=page, onLaterPages=page
                      )
    return out.getvalue()
