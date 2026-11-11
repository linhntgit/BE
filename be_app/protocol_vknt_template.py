"""Mẫu đề cương nghiên cứu tương đương sinh học chuẩn (Đầy đủ theo quy định Bộ Y tế & Hướng dẫn quốc tế).

Tuân thủ đầy đủ quy định về đề cương nghiên cứu tương đương sinh học của Bộ Y tế (Thông tư 08/2022/TT-BYT,
Thông tư 29/2018/TT-BYT, Phụ lục 10.1.1) và các hướng dẫn quốc tế ASEAN, ICH M13A, ICH M10, EMA, US-FDA.

Provides full, high-fidelity Word (.docx) and PDF (.pdf) generation. Automatically binds
available study data from `be_app`, and marks missing or unprovided items with standard
placeholders [YÊU CẦU NGƯỜI DÙNG BỔ SUNG: ... ] [CẦN BỔ SUNG / XÁC NHẬN] for the user to complete.
"""

from __future__ import annotations

import io
from datetime import datetime
from xml.sax.saxutils import escape

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from be_app.branding import software_attribution
from be_app.design import SEQUENCES
from be_app.document_standards import (
    LEGACY_MISSING_VI,
    REQ_USER_INPUT_PREFIX_VI,
    req_user_input,
)
from be_app.persistence import Project
from be_app.regulations import RULES, capability_for
from be_app.reporting import _register_pdf_font

STATUS_VI = "DỰ THẢO ĐỀ CƯƠNG — CHƯA ĐƯỢC PHÊ DUYỆT"
CONTROLLED_LABEL = "ĐƯỢC KIỂM SOÁT / Controlled Copy"
CONFIDENTIAL_LABEL = "CONFIDENTIAL / BẢO MẬT"

# Standard Abbreviations table matching the VKNT HCMC template
VKNT_ABBREVIATIONS = [
    ("1", "AE", "Adverse Event", "Biến cố bất lợi"),
    ("2", "ALT (SGPT)", "Alanine aminotransferase", "Men gan Alanin aminotransferase"),
    ("3", "Anti-HCV", "Hepatitis C virus antibody", "Kháng thể kháng virus viêm gan C"),
    ("4", "ANOVA", "Analysis of Variance", "Phân tích phương sai"),
    ("5", "AST (SGOT)", "Aspartate aminotransferase", "Men gan Aspartat aminotransferase"),
    ("6", "AUC", "Area Under the plasma Concentration-time curve", "Diện tích dưới đường cong nồng độ - thời gian"),
    ("7", "BMI", "Body Mass Index", "Chỉ số khối cơ thể"),
    ("8", "BUN", "Blood Urea Nitrogen", "Chỉ số nitơ ure huyết"),
    ("9", "Cmax", "Peak drug concentration", "Nồng độ đỉnh của thuốc trong huyết tương"),
    ("10", "CI", "Confidence Interval", "Khoảng tin cậy (thường dùng CI 90% cho BE)"),
    ("11", "CV", "Coefficient of Variation", "Hệ số biến thiên / Độ phân tán"),
    ("12", "EMA", "European Medicines Agency", "Cơ quan Quản lý Dược phẩm Châu Âu"),
    ("13", "GCP", "Good Clinical Practice", "Thực hành tốt thử thuốc trên lâm sàng"),
    ("14", "GGT", "Gamma-glutamyl transferase", "Men gan Gamma-glutamyl transferase"),
    ("15", "GLP", "Good Laboratory Practice", "Thực hành tốt phòng kiểm nghiệm / thử nghiệm"),
    ("16", "HBsAg", "Hepatitis B surface Antigen", "Kháng nguyên bề mặt virus viêm gan B"),
    ("17", "HIV/AIDS", "Human Immunodeficiency Virus / AIDS", "Virus / Hội chứng suy giảm miễn dịch mắc phải"),
    ("18", "K2EDTA", "Dipotassium ethylenediaminetetraacetate", "Chất chống đông Dikali ethylenediaminetetraacetat"),
    ("19", "Kel (Ke)", "Elimination rate constant", "Hằng số tốc độ thải trừ"),
    ("20", "NTN", "Volunteer / Subject", "Người tình nguyện tham gia nghiên cứu"),
    ("21", "SAE", "Serious Adverse Event", "Biến cố bất lợi nghiêm trọng"),
    ("22", "SOP", "Standard Operating Procedure", "Quy trình thao tác chuẩn"),
    ("23", "t1/2", "Terminal half-life", "Thời gian bán thải"),
    ("24", "Tmax", "Time to peak concentration", "Thời gian đạt nồng độ đỉnh trong huyết tương"),
    ("25", "US-FDA", "United States Food and Drug Administration", "Cơ quan Quản lý Thực phẩm và Dược phẩm Hoa Kỳ"),
]

# Standard Meal Schedule (Table 1: Bữa ăn chuẩn hóa, Table 2: Bữa ăn nhẹ)
VKNT_MEAL_STANDARDIZED = [
    ("1. Cơm trắng", "350 g", "516 kcal"),
    ("2. Canh (rau xanh 100g, thịt 20g, dầu mỡ 5g)", "125 g", "110 kcal"),
    ("3. Món mặn (thịt nạc)", "130 g", "338 kcal"),
    ("4. Món xào (rau xanh 100g, dầu 5g)", "105 g", "60 kcal"),
    ("TỔNG NĂNG LƯỢNG BỮA ĂN CHUẨN", "710 g", "1024 kcal"),
]

VKNT_MEAL_SNACK = [
    ("Bánh ngọt / bánh mì mềm", "100 g", "219 kcal (Protein 6.1g, Lipid 0.5g, Glucid 47.5g)"),
    ("Sữa tươi tiệt trùng", "200 mL", "130 kcal (Protein 6.0g, Lipid 6.6g, Glucid 9.6g)"),
    ("TỔNG NĂNG LƯỢNG BỮA ĂN NHẸ", "300 g / mL", "349 kcal"),
]

# Table 3: Schedule of Events (Kế hoạch thực hiện)
VKNT_SCHEDULE_OF_EVENTS = [
    ("1", "Ký 'Phiếu cung cấp thông tin và chấp thuận tình nguyện tham gia nghiên cứu' (ICF)", "+", "-", "-", "-", "-"),
    ("2", "Hỏi tiền sử bệnh tật, phẫu thuật, tiền sử dị ứng, tiền sử dùng thuốc", "+", "-", "-", "-", "-"),
    ("3", "Hỏi thói quen hút thuốc lá, uống rượu bia, chất gây nghiện", "+", "-", "-", "-", "-"),
    ("4", "Khám sức khỏe tổng quát (toàn thân, các cơ quan chức năng)", "+", "-", "-", "-", "+"),
    ("5", "Kiểm tra dấu hiệu sinh tồn (Huyết áp, Mạch, Thân nhiệt)", "+", "+", "+", "+", "+"),
    ("6", "Xét nghiệm virus miễn dịch: HIV, HBsAg, Anti-HCV", "+", "-", "-", "-", "-"),
    ("7", "Xét nghiệm cận lâm sàng: Huyết học, Sinh hóa (Gan, Thận, Glucose), Tổng phân tích nước tiểu", "+", "-", "-", "-", "+"),
    ("8", "Đo điện tâm đồ (ECG 12 chuyển đạo)", "+", "-", "-", "-", "-"),
    ("9", "Xét nghiệm que thử thai nhanh đối với NTN nữ (trước khi uống thuốc)", "+", "+", "-", "+", "-"),
    ("10", "Ngẫu nhiên hóa mã số đối tượng và xếp nhóm", "+", "-", "-", "-", "-"),
    ("11", "Tập trung tại trung tâm nghiên cứu (lưu trú đêm trước uống thuốc và 24h sau uống)", "-", "+", "-", "+", "-"),
    ("12", "Cho uống thuốc thử / đối chứng theo danh sách ngẫu nhiên hóa", "-", "+", "-", "+", "-"),
    ("13", "Lấy mẫu máu định lượng theo lịch trình quy định", "-", "+", "-", "+", "-"),
    ("14", "Theo dõi và ghi nhận biến cố bất lợi (AE / SAE)", "+", "+", "+", "+", "+"),
]

VKNT_PROTOCOL_SECTIONS = [
    ("1", "ĐẠO ĐỨC TRONG NGHIÊN CỨU"),
    ("2", "TỔNG QUAN VỀ DƯỢC LÝ VÀ DƯỢC ĐỘNG HỌC CỦA THUỐC NGHIÊN CỨU"),
    ("3", "MỤC TIÊU NGHIÊN CỨU"),
    ("4", "THIẾT KẾ NGHIÊN CỨU"),
    ("5", "TUYỂN CHỌN NGƯỜI TÌNH NGUYỆN (NTN)"),
    ("6", "RÚT KHỎI NGHIÊN CỨU"),
    ("7", "QUY TRÌNH CHO UỐNG THUỐC VÀ KIỂM SOÁT ĂN UỐNG"),
    ("8", "KẾ HOẠCH THỰC HIỆN VÀ PHÂN TÍCH"),
    ("9", "QUẢN LÝ VÀ BẢO QUẢN THUỐC NGHIÊN CỨU"),
    ("10", "THEO DÕI VÀ XỬ TRÍ BIẾN CỐ BẤT LỢI (AE / SAE)"),
    ("11", "KẾ HOẠCH PHÂN TÍCH THỐNG KÊ (SAP) VÀ CỠ MẪU"),
    ("12", "QUẢN LÝ VÀ LƯU TRỮ HỒ SƠ NGHIÊN CỨU"),
    ("13", "KIỂM SOÁT CHẤT LƯỢNG VÀ ĐẢM BẢO CHẤT LƯỢNG (QC/QA)"),
    ("14", "ĐÁNH GIÁ TRỰC TIẾP VÀ CHỮ KÝ PHÊ DUYỆT"),
    ("15", "TÀI LIỆU THAM KHẢO"),
]


def _field(value: object, field_name: str, guidance: str = "") -> str:
    """Helper returning clean string or prominent user input request placeholder."""
    text = str(value).strip() if value is not None else ""
    if text:
        return text
    return req_user_input(
        field_name,
        guidance or f"Nhập thông tin {field_name} theo hồ sơ đăng ký",
        language="vi",
        context="protocol",
    )


def _fmt_date(date_str: str) -> str:
    """Format YYYY-MM-DD to DD/MM/YYYY."""
    text = str(date_str).strip() if date_str else ""
    if not text:
        return ""
    try:
        parts = text.split("-")
        if len(parts) == 3:
            return f"{parts[2]}/{parts[1]}/{parts[0]}"
    except Exception:
        pass
    return text


def build_vknt_protocol_content(
    project: Project,
    details: dict[str, str] | None = None,
    *,
    valid_plan: dict | None = None,
) -> dict:
    """Build complete structured content for the VKNT TP.HCM MOH Bioequivalence Protocol."""
    study = project.study
    rule = RULES[study.rule_set_id]
    capability = capability_for(study.rule_set_id)
    details = details or {}

    today_str = datetime.now().strftime("%d/%m/%Y")
    protocol_date = (
        _fmt_date(study.study_start_date)
        or _fmt_date(study.clinical_start_date)
        or today_str
    )
    protocol_year = protocol_date.split("/")[-1] if "/" in protocol_date else "2026"

    # 1. Basic administrative metadata
    study_id = _field(study.study_id, "Mã số đề tài / nghiên cứu", "Nhập mã số đề tài (ví dụ: 30BE19, BE-2026-01)")
    protocol_code = study.protocol.strip() if study.protocol.strip() else study_id
    version = "01"
    if "v" in protocol_code.lower():
        try:
            version = protocol_code.lower().split("v")[-1].strip()
        except Exception:
            version = "01"

    study_site = study.study_site.strip() if study.study_site.strip() else _field(None, "Đơn vị nghiên cứu", "Tên cơ sở thử nghiệm tương đương sinh học")
    site_address = details.get("study_site_address", "").strip() if details.get("study_site_address", "").strip() else _field(None, "Địa chỉ đơn vị nghiên cứu", "Địa chỉ cơ sở nghiên cứu")
    sponsor = _field(study.sponsor, "Đơn vị yêu cầu (Nhà tài trợ)", "Tên công ty / nhà tài trợ nghiên cứu")
    pi = _field(study.principal_investigator, "Nghiên cứu viên chính (PI)", "Họ tên, học vị của Nghiên cứu viên chính")

    active_ing = _field(study.active_ingredient, "Tên hoạt chất", "Tên hoạt chất chính theo Dược thư Quốc gia")
    test_prod = _field(study.test_product, "Tên thuốc thử (T)", "Tên thương mại của thuốc thử")
    ref_prod = _field(study.reference_product, "Tên thuốc đối chứng (R)", "Tên biệt dược gốc / thuốc đối chứng")
    test_strength = _field(study.test_strength, "Hàm lượng thuốc thử", "Hàm lượng hoạt chất (ví dụ: 180 mg, 60 mg)")
    ref_strength = _field(study.reference_strength, "Hàm lượng thuốc đối chứng", "Hàm lượng hoạt chất của thuốc đối chứng")
    test_form = _field(study.test_dosage_form, "Dạng bào chế thuốc thử", "Ví dụ: Viên nén bao phim, Viên nang cứng")
    ref_form = _field(study.reference_dosage_form, "Dạng bào chế thuốc đối chứng", "Ví dụ: Viên nén bao phim")
    test_mfr = _field(study.test_manufacturer, "Nhà sản xuất thuốc thử", "Tên cơ sở sản xuất thuốc thử")
    ref_mfr = _field(study.reference_manufacturer, "Nhà sản xuất thuốc đối chứng", "Tên cơ sở sản xuất thuốc đối chứng")

    # Full Title
    if study.title.strip():
        full_title = study.title.strip()
    else:
        full_title = (
            f"Đánh giá tương đương sinh học {test_form} {test_prod} ({active_ing} {test_strength}) "
            f"do {test_mfr} sản xuất so với {ref_form} {ref_prod} ({active_ing} {ref_strength}) do {ref_mfr} sản xuất"
        )

    # 2. Key Personnel & Study Sites Table (Trang 3 & 4)
    author = pi
    screening_site = _field("", "Cơ sở khám tuyển chọn NTN", "Nhập tên và địa chỉ phòng khám / trung tâm chẩn đoán khám tuyển chọn sức khỏe NTN")
    clinical_lead = _field("", "Bác sĩ phụ trách lâm sàng", "Nhập họ tên, học vị bác sĩ phụ trách lâm sàng và bệnh viện phối hợp")
    bio_lead = _field("", "Phụ trách phân tích mẫu sinh học", "Nhập họ tên chuyên viên / nghiên cứu viên phụ trách phòng phân tích bioanalytical")
    stats_lead = _field("", "Phụ trách thống kê", "Nhập họ tên chuyên viên phụ trách phân tích thống kê dược động học")
    qa_lead = _field("", "Phụ trách đảm bảo chất lượng (QA)", "Nhập họ tên cán bộ QA giám sát thử nghiệm")

    contacts_table = [
        ("Tên đề tài:", full_title),
        ("Mã số đề tài:", study_id),
        ("Ngày viết đề cương:", protocol_date),
        ("Thuốc thử nghiên cứu:", f"{test_form} {test_prod} ({active_ing} {test_strength})"),
        ("Pha nghiên cứu:", "Đánh giá tương đương sinh học (in vivo)"),
        ("Đơn vị yêu cầu (Nhà tài trợ):", f"{sponsor}\n{_field('', 'Địa chỉ nhà tài trợ', 'Địa chỉ, số điện thoại, fax của nhà tài trợ')}"),
        ("Đơn vị nghiên cứu:", f"{study_site}\nĐịa chỉ: {site_address}\nĐiện thoại: 028 38385637 - 028 38368518 | Fax: 028 38367900"),
        ("Nghiên cứu viên chính:", f"{pi}\n{study_site}"),
        ("Người viết đề cương:", f"{author}\n{study_site}"),
        ("Khám tuyển chọn NTN:", screening_site),
        ("Phụ trách lâm sàng:", clinical_lead),
        ("Phụ trách phân tích mẫu sinh học:", bio_lead),
        ("Phụ trách thống kê:", stats_lead),
        ("Phụ trách chất lượng (QA):", qa_lead),
    ]

    # 3. Synopsis / Tóm tắt nghiên cứu (Trang 5-7)
    design_str = {
        "2x2": "Nghiên cứu chéo 2x2 (2 thuốc, 2 giai đoạn, 2 trình tự)",
        "parallel": "Nghiên cứu song song 2 nhánh",
        "partial3": "Nghiên cứu lặp lại một phần 3 kỳ (Partial replicate)",
        "full4": "Nghiên cứu lặp lại toàn phần 4 kỳ (Full replicate)",
    }.get(study.design, "Nghiên cứu chéo 2x2")

    fed_str = "Uống thuốc sau khi nhịn đói qua đêm ít nhất 10 giờ (điều kiện nhịn đói - Fasted)" if study.fed_state == "fasted" else "Uống thuốc sau bữa ăn chuẩn giàu calo và chất béo (điều kiện sau ăn - Fed)"
    single_dose_str = "đơn liều (single-dose)" if study.single_dose else "đa liều đến trạng thái ổn định (steady-state)"

    washout_val = details.get("washout", "").strip() or _field("", "Thời gian washout", "Nhập thời gian rửa giải giữa các kỳ (ví dụ: 07 ngày, ít nhất 5-7 lần t1/2)")
    sampling_val = details.get("sampling", "").strip() or _field("", "Lịch lấy mẫu máu", "Nhập các thời điểm lấy mẫu (ví dụ: 0; 0.5; 1; 1.5; 2; 2.5; 3; 3.5; 4; 6; 8; 11; 15; 24; 36; 48 giờ)")

    # Sample size logic
    if valid_plan is not None:
        evaluable_n = valid_plan.get("evaluable", 24)
        recruit_n = valid_plan.get("recruit", 28)
        sample_size_str = (
            f"Cỡ mẫu tính toán: {evaluable_n} NTN đánh giá được, tuyển chọn {recruit_n} NTN "
            f"(dự phòng {recruit_n - evaluable_n} NTN rút lui). Sức mạnh thống kê đạt >= 80%."
        )
    elif details.get("sample_size", "").strip():
        sample_size_str = details.get("sample_size").strip()
    else:
        sample_size_str = _field("", "Căn cứ cỡ mẫu", "Dự kiến 24-30 NTN chính thức và 2-4 NTN dự bị để đạt sức mạnh thống kê >= 80%")

    test_batch = _field(study.test_batch, "Số lô sản xuất thuốc thử", "Số lô sản xuất thực tế trên nhãn")
    ref_batch = _field(study.reference_batch, "Số lô sản xuất thuốc đối chứng", "Số lô sản xuất trên nhãn thuốc đối chứng")
    test_exp = _field(_fmt_date(study.test_expiry_date), "Hạn dùng thuốc thử", "Hạn dùng thuốc thử (DD/MM/YYYY)")
    ref_exp = _field(_fmt_date(study.reference_expiry_date), "Hạn dùng thuốc đối chứng", "Hạn dùng thuốc đối chứng (DD/MM/YYYY)")
    test_mfg = _field(_fmt_date(study.clinical_start_date), "Ngày sản xuất thuốc thử", "Ngày sản xuất thuốc thử (DD/MM/YYYY)")
    ref_mfg = _field("", "Ngày sản xuất thuốc đối chứng", "Ngày sản xuất ghi trên nhãn thuốc đối chứng")
    test_size = _field("", "Cỡ lô thuốc thử", "Ví dụ: 100.000 viên hoặc 240.000 viên")
    ref_reg = _field("", "Số đăng ký lưu hành thuốc đối chứng", "Ví dụ: VD-28324-17")

    # Pharmacological details
    is_fexo = "fexofenadin" in active_ing.lower()

    return {
        "study_id": study_id,
        "protocol_code": protocol_code,
        "version": version,
        "protocol_date": protocol_date,
        "protocol_year": protocol_year,
        "full_title": full_title,
        "institution": study_site,
        "institution_address": site_address,
        "sponsor": sponsor,
        "pi": pi,
        "author": author,
        "contacts_table": contacts_table,
        "active_ing": active_ing,
        "test_prod": test_prod,
        "ref_prod": ref_prod,
        "test_strength": test_strength,
        "ref_strength": ref_strength,
        "test_form": test_form,
        "ref_form": ref_form,
        "test_mfr": test_mfr,
        "ref_mfr": ref_mfr,
        "test_batch": test_batch,
        "ref_batch": ref_batch,
        "test_exp": test_exp,
        "ref_exp": ref_exp,
        "test_mfg": test_mfg,
        "ref_mfg": ref_mfg,
        "test_size": test_size,
        "ref_reg": ref_reg,
        "design_str": design_str,
        "fed_str": fed_str,
        "single_dose_str": single_dose_str,
        "dose": study.dose,
        "dose_unit": study.dose_unit,
        "washout_val": washout_val,
        "sampling_val": sampling_val,
        "sample_size_str": sample_size_str,
        "rule_set_id": study.rule_set_id,
        "guideline": rule.guideline,
        "primary_endpoints": [ep.upper().replace("_", "") for ep in study.primary_endpoints],
        "secondary_endpoints": [ep.upper().replace("_", "") for ep in study.secondary_endpoints],
        "is_fexo": is_fexo,
        "training": study.is_demo or study.data_purpose == "training_qa",
        "details": details,
    }


def _add_styled_cell(
    row,
    index: int,
    text: str,
    width: Cm,
    bold: bool = False,
    shading_hex: str | None = None,
    align=WD_ALIGN_PARAGRAPH.LEFT,
    font_size: Pt = Pt(9.5),
) -> None:
    cell = row.cells[index]
    cell.width = width
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    if shading_hex:
        tcPr = cell._tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), shading_hex)
        tcPr.append(shd)
    p = cell.paragraphs[0]
    p.alignment = align
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.1

    # Check for placeholder markers to color red
    if REQ_USER_INPUT_PREFIX_VI in text or LEGACY_MISSING_VI in text:
        parts = text.split("[")
        if parts[0]:
            r0 = p.add_run(parts[0])
            r0.font.size = font_size
            r0.font.bold = bold
        for part in parts[1:]:
            if "]" in part:
                b_text, rest = part.split("]", 1)
                r_tag = p.add_run(f"[{b_text}]")
                r_tag.font.size = font_size
                r_tag.font.bold = True
                r_tag.font.color.rgb = RGBColor(180, 40, 20)
                if rest:
                    r_rest = p.add_run(rest)
                    r_rest.font.size = font_size
                    r_rest.font.bold = bold
            else:
                r_tail = p.add_run(f"[{part}")
                r_tail.font.size = font_size
                r_tail.font.bold = bold
    else:
        run = p.add_run(text)
        run.font.size = font_size
        run.font.bold = bold


def _add_p(
    doc: Document,
    text: str,
    bold: bool = False,
    italic: bool = False,
    align=WD_ALIGN_PARAGRAPH.LEFT,
    font_size: Pt = Pt(10),
    space_after: Pt = Pt(3),
    space_before: Pt = Pt(0),
    color: RGBColor | None = None,
) -> None:
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = space_before
    p.paragraph_format.space_after = space_after
    p.paragraph_format.line_spacing = 1.15

    if REQ_USER_INPUT_PREFIX_VI in text or LEGACY_MISSING_VI in text:
        parts = text.split("[")
        if parts[0]:
            r = p.add_run(parts[0])
            r.font.size = font_size
            r.font.bold = bold
            r.font.italic = italic
            if color:
                r.font.color.rgb = color
        for part in parts[1:]:
            if "]" in part:
                b_text, rest = part.split("]", 1)
                r_tag = p.add_run(f"[{b_text}]")
                r_tag.font.size = font_size
                r_tag.font.bold = True
                r_tag.font.color.rgb = RGBColor(180, 40, 20)
                if rest:
                    r_rest = p.add_run(rest)
                    r_rest.font.size = font_size
                    r_rest.font.bold = bold
                    r_rest.font.italic = italic
                    if color:
                        r_rest.font.color.rgb = color
            else:
                r_tail = p.add_run(f"[{part}")
                r_tail.font.size = font_size
                r_tail.font.bold = bold
                r_tail.font.italic = italic
                if color:
                    r_tail.font.color.rgb = color
    else:
        r = p.add_run(text)
        r.font.size = font_size
        r.font.bold = bold
        r.font.italic = italic
        if color:
            r.font.color.rgb = color


def docx_protocol_vknt(
    project: Project,
    details: dict[str, str] | None = None,
    *,
    valid_plan: dict | None = None,
) -> bytes:
    """Generate Word (.docx) Bioequivalence Protocol matching the MOH / VKNT TP.HCM format."""
    study = project.study
    c = build_vknt_protocol_content(project, details, valid_plan=valid_plan)
    doc = Document()

    # Page setup (A4 standard)
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.top_margin = Cm(2.0)
    sec.bottom_margin = Cm(2.0)
    sec.left_margin = Cm(2.5)
    sec.right_margin = Cm(2.0)

    # Base styles
    for style_name in ("Normal", "Title", "Heading 1", "Heading 2", "Heading 3"):
        s = doc.styles[style_name]
        s.font.name = "Arial"
        s.font.color.rgb = RGBColor(0, 0, 0)
        fonts = s.element.get_or_add_rPr().find(qn("w:rFonts"))
        for attr in ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme"):
            fonts.attrib.pop(qn("w:" + attr), None)
        for attr in ("eastAsia", "cs"):
            fonts.set(qn("w:" + attr), "Arial")

    # Header & Footer setup
    header = sec.header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    hrun = header.add_run(f"Đề cương {c['protocol_code']}  |  {CONTROLLED_LABEL}")
    hrun.font.size = Pt(8)
    hrun.font.color.rgb = RGBColor(120, 120, 120)

    footer = sec.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    frun = footer.add_run(f"{software_attribution('vi')}  |  {STATUS_VI}")
    frun.font.size = Pt(8)
    frun.font.color.rgb = RGBColor(120, 120, 120)

    # -----------------------------------------------------------------------
    # 1. TRANG BÌA (Cover Page - Phụ lục 10.1.1)
    # -----------------------------------------------------------------------
    _add_p(doc, "BỘ Y TẾ", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(12), space_after=Pt(2))
    _add_p(doc, c["institution"].upper(), bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(12), space_after=Pt(36))

    _add_p(doc, "PHỤ LỤC 10.1.1", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(15), space_after=Pt(14), color=RGBColor(30, 70, 140))
    _add_p(doc, "ĐỀ CƯƠNG NGHIÊN CỨU", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(18), space_after=Pt(24))

    _add_p(doc, CONTROLLED_LABEL, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(10), color=RGBColor(180, 40, 40), space_after=Pt(4))
    _add_p(doc, CONFIDENTIAL_LABEL, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(9), color=RGBColor(120, 120, 120), space_after=Pt(120))

    if c["training"]:
        _add_p(doc, "DỮ LIỆU ĐÀO TẠO / GIẢ LẬP — KHÔNG SỬ DỤNG CHO NGHIÊN CỨU THỰC TẾ", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(10), color=RGBColor(180, 40, 40))

    doc.add_page_break()

    # -----------------------------------------------------------------------
    # 2. TRANG TIÊU ĐỀ ĐỀ CƯƠNG (Title Page)
    # -----------------------------------------------------------------------
    _add_p(doc, "BỘ Y TẾ", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(12), space_after=Pt(2))
    _add_p(doc, c["institution"].upper(), bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(12), space_after=Pt(30))

    _add_p(doc, "ĐỀ CƯƠNG NGHIÊN CỨU", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(16), space_after=Pt(14), color=RGBColor(20, 50, 110))

    _add_p(doc, "ĐÁNH GIÁ TƯƠNG ĐƯƠNG SINH HỌC", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(13), space_after=Pt(4))
    _add_p(doc, f"{c['test_form'].upper()} {c['test_prod'].upper()}", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(13), space_after=Pt(4), color=RGBColor(160, 30, 30))
    _add_p(doc, f"({c['active_ing'].upper()} {c['test_strength']})", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(12), space_after=Pt(4))
    _add_p(doc, f"DO {c['test_mfr'].upper()} SẢN XUẤT", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(11), space_after=Pt(40))

    # Meta block
    meta_p = doc.add_paragraph()
    meta_p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    meta_p.paragraph_format.left_indent = Cm(3.0)
    meta_p.paragraph_format.line_spacing = 1.3
    meta_p.add_run("Mã số đề tài: ").bold = True
    meta_p.add_run(f"{c['study_id']}\n")
    meta_p.add_run("Phiên bản số: ").bold = True
    meta_p.add_run(f"{c['version']}\n")
    meta_p.add_run("Ngày ban hành: ").bold = True
    meta_p.add_run(f"{c['protocol_date']}\n")
    meta_p.add_run("Đơn vị nghiên cứu: ").bold = True
    meta_p.add_run(f"{c['institution']}\n")
    meta_p.add_run("Địa chỉ: ").bold = True
    meta_p.add_run(f"{c['institution_address']}\n")

    _add_p(doc, f"TP. HỒ CHÍ MINH - {c['protocol_year']}", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(11), space_before=Pt(80))
    _add_p(doc, CONTROLLED_LABEL, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(9), color=RGBColor(180, 40, 40), space_before=Pt(10))

    doc.add_page_break()

    # -----------------------------------------------------------------------
    # 3. BẢNG THÔNG TIN NHÂN SỰ VÀ ĐƠN VỊ THỰC HIỆN
    # -----------------------------------------------------------------------
    _add_p(doc, "ĐỀ CƯƠNG NGHIÊN CỨU — THÔNG TIN CHUNG", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(13), space_after=Pt(10), color=RGBColor(20, 50, 110))

    tbl_contacts = doc.add_table(rows=0, cols=2)
    tbl_contacts.style = "Table Grid"
    tbl_contacts.alignment = WD_TABLE_ALIGNMENT.CENTER
    c_widths = [Cm(5.0), Cm(11.5)]

    for label, val in c["contacts_table"]:
        row = tbl_contacts.add_row()
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        _add_styled_cell(row, 0, label, c_widths[0], bold=True, shading_hex="F8F9FA", font_size=Pt(9))
        _add_styled_cell(row, 1, val, c_widths[1], bold=False, font_size=Pt(9))

    doc.add_page_break()

    # -----------------------------------------------------------------------
    # 4. TÓM TẮT NGHIÊN CỨU (Study Synopsis)
    # -----------------------------------------------------------------------
    _add_p(doc, "TÓM TẮT NGHIÊN CỨU (STUDY SYNOPSIS)", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(13), space_after=Pt(10), color=RGBColor(20, 50, 110))

    tbl_syn = doc.add_table(rows=3, cols=2)
    tbl_syn.style = "Table Grid"
    tbl_syn.alignment = WD_TABLE_ALIGNMENT.CENTER
    for r in tbl_syn.rows:
        r._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))

    _add_styled_cell(tbl_syn.rows[0], 0, f"Đơn vị yêu cầu:\n{c['sponsor']}", c_widths[0], bold=False, font_size=Pt(9))
    _add_styled_cell(tbl_syn.rows[0], 1, f"Đơn vị nghiên cứu:\n{c['institution']}", c_widths[1], bold=False, font_size=Pt(9))
    _add_styled_cell(tbl_syn.rows[1], 0, f"Thuốc thử (T):\n{c['test_prod']}", c_widths[0], bold=False, font_size=Pt(9))
    _add_styled_cell(tbl_syn.rows[1], 1, f"Tên hoạt chất, hàm lượng:\n{c['active_ing']} {c['test_strength']}", c_widths[1], bold=False, font_size=Pt(9))
    _add_styled_cell(tbl_syn.rows[2], 0, f"Thuốc đối chứng (R):\n{c['ref_prod']}", c_widths[0], bold=False, font_size=Pt(9))
    _add_styled_cell(tbl_syn.rows[2], 1, f"Tên hoạt chất, hàm lượng:\n{c['active_ing']} {c['ref_strength']}", c_widths[1], bold=False, font_size=Pt(9))

    _add_p(doc, "Mục tiêu nghiên cứu:", bold=True, font_size=Pt(10.5), space_before=Pt(8), space_after=Pt(2))
    _add_p(doc, f"Đánh giá tương đương sinh học của {c['test_form']} {c['test_prod']} ({c['active_ing']} {c['test_strength']}) do {c['test_mfr']} sản xuất so với {c['ref_form']} {c['ref_prod']} ({c['active_ing']} {c['ref_strength']}) do {c['ref_mfr']} sản xuất trên người tình nguyện khỏe mạnh.")

    _add_p(doc, "Thuốc nghiên cứu:", bold=True, font_size=Pt(10.5), space_before=Pt(6), space_after=Pt(2))
    _add_p(doc, f"• Thuốc thử (T): {c['test_form']} {c['test_prod']} ({c['active_ing']} {c['test_strength']}), số lô: {c['test_batch']}, ngày sản xuất: {c['test_mfg']}, hạn dùng: {c['test_exp']}, cỡ lô: {c['test_size']} do {c['test_mfr']} sản xuất.")
    _add_p(doc, f"• Thuốc đối chứng (R): {c['ref_form']} {c['ref_prod']} ({c['active_ing']} {c['ref_strength']}), số lô: {c['ref_batch']}, ngày sản xuất: {c['ref_mfg']}, hạn dùng: {c['ref_exp']}, số đăng ký lưu hành: {c['ref_reg']} do {c['ref_mfr']} sản xuất.")

    _add_p(doc, "Thiết kế nghiên cứu:", bold=True, font_size=Pt(10.5), space_before=Pt(6), space_after=Pt(2))
    _add_p(doc, f"{c['design_str']}, {c['single_dose_str']}, ngẫu nhiên hóa, {c['fed_str']}. Thời gian thải trừ (washout) giữa các kỳ: {c['washout_val']}.")

    _add_p(doc, "Tiêu chuẩn chọn lựa chính:", bold=True, font_size=Pt(10.5), space_before=Pt(6), space_after=Pt(2))
    _add_p(doc, "Người tình nguyện khỏe mạnh nam hoặc nữ, độ tuổi từ 18 đến 50 (hoặc 18-55); chỉ số BMI từ 18.0 đến 27.0 kg/m²; cân nặng >= 44 kg (nữ) và >= 47 kg (nam); huyết áp tâm thu 100-139 mmHg, tâm trương 60-89 mmHg; nhịp tim 60-90 lần/phút; xét nghiệm HIV, HBsAg, Anti-HCV âm tính; kết quả khám sức khỏe, xét nghiệm huyết học, sinh hóa và nước tiểu trong giới hạn bình thường.")

    _add_p(doc, "Phương pháp phân tích mẫu sinh học:", bold=True, font_size=Pt(10.5), space_before=Pt(6), space_after=Pt(2))
    _add_p(doc, f"Định lượng {c['active_ing']} trong huyết tương người bằng phương pháp sắc ký lỏng ghép nối khối phổ hai lần (LC-MS/MS) với chất chuẩn nội phù hợp, được thẩm định đầy đủ theo hướng dẫn của US-FDA, EMA và ICH M10 (độ chọn lọc, tính tuyến tính, độ đúng, độ chính xác, hiệu suất chiết, độ nhiễm chéo, hiệu ứng nền, độ ổn định).")

    _add_p(doc, "Phương pháp phân tích thống kê:", bold=True, font_size=Pt(10.5), space_before=Pt(6), space_after=Pt(2))
    _add_p(doc, f"Tính toán các thông số dược động học phi ngăn (NCA): Cmax, AUC0-t, AUC0-inf, Tmax, t1/2, Kel, %AUCextrap. Phân tích phương sai ANOVA trên ln(Cmax), ln(AUC0-t), ln(AUC0-inf). Hai chế phẩm được kết luận tương đương sinh học khi khoảng tin cậy 90% (CI 90%) của tỷ số trung bình nhân GMR (T/R) cho Cmax và AUC0-t nằm hoàn toàn trong khoảng [80.00% - 125.00%]. Kiểm định Wilcoxon signed-rank đối với Tmax. Báo cáo giá trị Power (sức mạnh thống kê).")

    doc.add_page_break()

    # -----------------------------------------------------------------------
    # 5. MỤC LỤC & CHÚ GIẢI CHỮ VIẾT TẮT
    # -----------------------------------------------------------------------
    _add_p(doc, "MỤC LỤC ĐỀ CƯƠNG", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(13), space_after=Pt(8), color=RGBColor(20, 50, 110))

    tbl_toc = doc.add_table(rows=0, cols=2)
    tbl_toc.style = "Table Grid"
    tbl_toc.alignment = WD_TABLE_ALIGNMENT.CENTER
    for num, title in VKNT_PROTOCOL_SECTIONS:
        r = tbl_toc.add_row()
        r._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        _add_styled_cell(r, 0, f"Mục {num}", Cm(2.2), bold=True, shading_hex="F8F9FA", align=WD_ALIGN_PARAGRAPH.CENTER)
        _add_styled_cell(r, 1, title, Cm(14.3), bold=True)

    _add_p(doc, "CHÚ GIẢI CHỮ VIẾT TẮT", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(13), space_before=Pt(16), space_after=Pt(8), color=RGBColor(20, 50, 110))

    tbl_abbr = doc.add_table(rows=1, cols=4)
    tbl_abbr.style = "Table Grid"
    tbl_abbr.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = tbl_abbr.rows[0]
    hdr._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
    hdr._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))
    w_abbr = [Cm(1.2), Cm(2.8), Cm(6.5), Cm(6.0)]
    _add_styled_cell(hdr, 0, "STT", w_abbr[0], bold=True, shading_hex="EAECEF", align=WD_ALIGN_PARAGRAPH.CENTER)
    _add_styled_cell(hdr, 1, "Từ viết tắt", w_abbr[1], bold=True, shading_hex="EAECEF")
    _add_styled_cell(hdr, 2, "Từ nguyên (tiếng Anh)", w_abbr[2], bold=True, shading_hex="EAECEF")
    _add_styled_cell(hdr, 3, "Nghĩa tiếng Việt", w_abbr[3], bold=True, shading_hex="EAECEF")

    for stt, abbr, orig, vi_mean in VKNT_ABBREVIATIONS:
        r = tbl_abbr.add_row()
        r._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        _add_styled_cell(r, 0, stt, w_abbr[0], align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8.5))
        _add_styled_cell(r, 1, abbr, w_abbr[1], bold=True, font_size=Pt(8.5))
        _add_styled_cell(r, 2, orig, w_abbr[2], font_size=Pt(8.5))
        _add_styled_cell(r, 3, vi_mean, w_abbr[3], font_size=Pt(8.5))

    doc.add_page_break()

    # -----------------------------------------------------------------------
    # 6. CHI TIẾT 14 MỤC THEO MẪU CHUẨN ĐỀ CƯƠNG NGHIÊN CỨU
    # -----------------------------------------------------------------------

    # MỤC 1
    _add_p(doc, "1. ĐẠO ĐỨC TRONG NGHIÊN CỨU", bold=True, font_size=Pt(12), space_before=Pt(10), space_after=Pt(4), color=RGBColor(20, 50, 110))
    _add_p(doc, f"Nghiên cứu được đệ trình và phê duyệt bởi Hội đồng Đạo đức trong nghiên cứu y sinh học cơ sở ({_field('', 'Quyết định thành lập và mã số IRB', 'Nhập số quyết định thành lập HĐĐĐ và mã số chứng nhận IRB')}) hoạt động theo Thông tư số 45/2017/TT-BYT ngày 16/11/2017 của Bộ Y tế về 'Quy định việc thành lập, chức năng, nhiệm vụ, quyền hạn của Hội đồng đạo đức trong nghiên cứu y sinh học'. Nghiên cứu tuân thủ các nguyên tắc của Thực hành tốt thử thuốc trên lâm sàng theo Thông tư số 29/2018/TT-BYT ngày 29/10/2018 và Thông tư 03/2012/TT-BYT ngày 02/02/2012 của Bộ Y tế.")
    _add_p(doc, f"Nghiên cứu được tiến hành trên tinh thần của Tuyên ngôn Helsinki, hướng dẫn ICH E6(R3) về Thực hành tốt lâm sàng (GCP) và tuân thủ các quy trình thao tác chuẩn (SOP), quy định GLP của {c['institution']}.")
    _add_p(doc, "Nghiên cứu chỉ được phép khởi động sau khi có văn bản chấp thuận chính thức từ Hội đồng Đạo đức. Nghiên cứu viên chính chịu trách nhiệm đệ trình, lưu giữ hồ sơ và các biên bản thẩm định của Hội đồng. Người tình nguyện được cung cấp đầy đủ thông tin về thuốc, quyền lợi, nghĩa vụ, rủi ro tiềm tàng và tự nguyện ký vào bản 'Phiếu cung cấp thông tin và chấp thuận tình nguyện tham gia nghiên cứu' (ICF) theo mẫu đã được Hội đồng Đạo đức phê duyệt.")

    # MỤC 2
    _add_p(doc, f"2. TỔNG QUAN VỀ {c['active_ing'].upper()}", bold=True, font_size=Pt(12), space_before=Pt(10), space_after=Pt(4), color=RGBColor(20, 50, 110))
    if c["is_fexo"]:
        _add_p(doc, "Dược lý và cơ chế tác dụng:", bold=True, font_size=Pt(10), space_before=Pt(3), space_after=Pt(1))
        _add_p(doc, "Fexofenadin là thuốc kháng histamin thế hệ hai, có tác dụng đối kháng đặc hiệu và chọn lọc trên thụ thể H1 ngoại vi. Thuốc là một chất chuyển hóa có hoạt tính của terfenadin, cạnh tranh với histamin tại thụ thể H1 ở đường tiêu hóa, mạch máu và đường hô hấp, nhưng không gây kéo dài khoảng QT và không có độc tính trên tim. Ở liều điều trị, fexofenadin không gây ngủ hay ảnh hưởng đến hệ thần kinh trung ương.")
        _add_p(doc, "Dược động học lâm sàng:", bold=True, font_size=Pt(10), space_before=Pt(3), space_after=Pt(1))
        _add_p(doc, "Fexofenadin hấp thu tốt khi dùng đường uống và bắt đầu phát huy tác dụng sau khoảng 60 phút. Nồng độ đỉnh trong huyết tương (Cmax) đạt được sau 2 - 3 giờ (Tmax). Thức ăn giàu chất béo làm giảm Cmax khoảng 17% và kéo dài Tmax. Tỷ lệ gắn kết protein huyết tương là 60 - 70%. Thuốc rất ít bị chuyển hóa qua gan (khoảng 5%, chủ yếu nhờ vi khuẩn đường ruột và niêm mạc ruột). Thời gian bán thải t1/2 của fexofenadin khoảng 14,4 giờ (dao động 11 - 18 giờ). Thuốc thải trừ chủ yếu qua phân (khoảng 80%) và nước tiểu (11 - 12%) dưới dạng không biến đổi.")
        _add_p(doc, "Chỉ định và liều dùng:", bold=True, font_size=Pt(10), space_before=Pt(3), space_after=Pt(1))
        _add_p(doc, "Điều trị triệu chứng trong viêm mũi dị ứng theo mùa và mề đay tự phát mạn tính ở người lớn và trẻ em từ 12 tuổi trở lên với liều 60 mg x 2 lần/ngày hoặc 180 mg x 1 lần/ngày.")
        _add_p(doc, "Tương tác thuốc và thận trọng:", bold=True, font_size=Pt(10), space_before=Pt(3), space_after=Pt(1))
        _add_p(doc, "Erythromycin và ketoconazol làm tăng nồng độ fexofenadin trong huyết tương nhưng không làm biến đổi khoảng QT. Các thuốc kháng acid chứa nhôm và magnesi làm giảm hấp thu fexofenadin, cần uống cách xa ít nhất 2 giờ. Tránh uống thuốc với nước ép hoa quả (bưởi chùm, cam, táo) do ức chế chất vận chuyển OATP1A2 làm giảm sinh khả dụng.")
    else:
        _add_p(doc, f"Đặc tính dược lý, cơ chế tác dụng, chỉ định và hồ sơ an toàn của {c['active_ing']} được tổng hợp từ Dược thư Quốc gia Việt Nam và tờ Hướng dẫn sử dụng thuốc gốc (SmPC).")
        _add_p(doc, f"Đặc điểm dược động học: {c['active_ing']} được hấp thu qua đường {study.route}, thời gian bán thải t1/2, con đường chuyển hóa và thải trừ chính cần được đối chiếu để xác định thời gian washout tối thiểu >= 5-7 lần t1/2 và lịch lấy mẫu bao phủ ít nhất 80% AUC0-inf.")

    # MỤC 3
    _add_p(doc, "3. MỤC TIÊU NGHIÊN CỨU", bold=True, font_size=Pt(12), space_before=Pt(10), space_after=Pt(4), color=RGBColor(20, 50, 110))
    _add_p(doc, "3.1. Dược động học", bold=True, font_size=Pt(10.5), space_before=Pt(2), space_after=Pt(2))
    _add_p(doc, f"Mục tiêu của nghiên cứu là đánh giá tương đương sinh học in vivo giữa {c['test_form']} {c['test_prod']} ({c['active_ing']} {c['test_strength']}) do {c['test_mfr']} sản xuất và {c['ref_form']} {c['ref_prod']} ({c['active_ing']} {c['ref_strength']}) do {c['ref_mfr']} sản xuất thông qua việc so sánh các thông số dược động học chính ({', '.join(c['primary_endpoints'])}) và phụ ({', '.join(c['secondary_endpoints'])}).")
    _add_p(doc, "3.2. An toàn", bold=True, font_size=Pt(10.5), space_before=Pt(2), space_after=Pt(2))
    _add_p(doc, "Theo dõi, ghi nhận và đánh giá toàn diện tính an toàn, khả năng dung nạp của thuốc trên người tình nguyện trong suốt quá trình thử nghiệm.")

    # MỤC 4
    _add_p(doc, "4. THIẾT KẾ NGHIÊN CỨU", bold=True, font_size=Pt(12), space_before=Pt(10), space_after=Pt(4), color=RGBColor(20, 50, 110))
    _add_p(doc, f"Phương pháp nghiên cứu: {c['design_str']}, {c['single_dose_str']}, ngẫu nhiên hóa, {c['fed_str']}.")
    _add_p(doc, f"Cỡ mẫu nghiên cứu dự kiến: {c['sample_size_str']}. Các đối tượng được phân ngẫu nhiên thành các nhóm trình tự ({', '.join(SEQUENCES.get(study.design, ['TR', 'RT']))}). Giai đoạn 1: nhóm 1 uống thuốc thử (T), nhóm 2 uống thuốc đối chứng (R); Giai đoạn 2: thực hiện ngược lại.")
    _add_p(doc, f"Thời gian thải trừ (washout) giữa 2 giai đoạn: {c['washout_val']} (đảm bảo ít nhất gấp 5-7 lần thời gian bán thải t1/2 để nồng độ trước liều kỳ 2 dưới ngưỡng phát hiện hoặc < 5% Cmax).")
    _add_p(doc, f"NTN có mặt tại cơ sở thử nghiệm lâm sàng vào chiều/tối trước ngày cho uống thuốc (Ngày 1 và Ngày 8). NTN lưu trú tại trung tâm trong suốt 24 giờ sau khi uống thuốc và trở lại lấy mẫu ngoại trú theo đúng lịch trình.")

    # MỤC 5
    _add_p(doc, "5. TUYỂN CHỌN NGƯỜI TÌNH NGUYỆN (NTN)", bold=True, font_size=Pt(12), space_before=Pt(10), space_after=Pt(4), color=RGBColor(20, 50, 110))
    _add_p(doc, "5.1. Tiêu chuẩn chọn lựa (Inclusion Criteria):", bold=True, font_size=Pt(10), space_before=Pt(2), space_after=Pt(1))
    inclusion_items = [
        "Người tình nguyện khỏe mạnh nam hoặc nữ, độ tuổi từ 18 đến 50 (hoặc 18-55).",
        "Chỉ số khối cơ thể BMI từ 18.0 đến 27.0 kg/m².",
        "Cân nặng ít nhất 44 kg đối với nữ và 47 kg đối với nam.",
        "Huyết áp tâm thu trong khoảng 100 - 139 mmHg, huyết áp tâm trương 60 - 89 mmHg; nhịp tim đều 60 - 90 lần/phút.",
        "Không có tiền sử và hiện tại không mắc các bệnh lý mạn tính: tim mạch, gan, thận, hô hấp, tiêu hóa, nội tiết, thần kinh, tâm thần, huyết học.",
        "Không có tiền sử dị ứng với hoạt chất nghiên cứu hoặc các tá dược trong công thức.",
        "Phụ nữ không mang thai, không trong thời kỳ cho con bú; xét nghiệm que thử thai nhanh nước tiểu âm tính trước mỗi kỳ uống thuốc.",
        "Xét nghiệm miễn dịch âm tính với HIV, HBsAg và Anti-HCV.",
        "Kết quả khám lâm sàng, điện tâm đồ (ECG) và các xét nghiệm huyết học, sinh hóa máu, tổng phân tích nước tiểu nằm trong giới hạn bình thường.",
        "Tự nguyện ký Phiếu chấp thuận tham gia nghiên cứu (ICF) và cam kết tuân thủ đầy đủ quy định của đề cương.",
    ]
    for it in inclusion_items:
        _add_p(doc, f"• {it}", space_after=Pt(1))

    _add_p(doc, "5.2. Tiêu chuẩn loại bỏ (Exclusion Criteria):", bold=True, font_size=Pt(10), space_before=Pt(4), space_after=Pt(1))
    exclusion_items = [
        "Kết quả xét nghiệm cận lâm sàng hoặc khám sức khỏe bất thường có ý nghĩa lâm sàng.",
        "Mắc bệnh cấp tính hoặc phẫu thuật lớn trong vòng 8 tuần trước nghiên cứu.",
        "Sử dụng bất kỳ thuốc kê đơn, không kê đơn hoặc thực phẩm chức năng trong vòng 14 ngày (hoặc 28 ngày đối với thuốc gây cảm ứng/ức chế enzym gan) trước khi uống thuốc nghiên cứu.",
        "Tiền sử nghiện rượu, nghiện thuốc lá (hút trên 5 điếu/ngày) hoặc sử dụng chất kích thích, ma túy.",
        "Hiến máu hoặc tham gia một nghiên cứu thử nghiệm lâm sàng/tương đương sinh học khác trong vòng 3 tháng gần nhất.",
        "Khó nuốt thuốc dạng viên nén/viên nang hoặc có rối loạn hấp thu đường tiêu hóa.",
    ]
    for it in exclusion_items:
        _add_p(doc, f"• {it}", space_after=Pt(1))

    # MỤC 6
    _add_p(doc, "6. RÚT KHỎI NGHIÊN CỨU", bold=True, font_size=Pt(12), space_before=Pt(10), space_after=Pt(4), color=RGBColor(20, 50, 110))
    _add_p(doc, "Người tình nguyện có quyền tự nguyện rút khỏi nghiên cứu vào bất kỳ thời điểm nào vì bất kỳ lý do gì mà không bị khiển trách và vẫn được theo dõi kiểm tra sức khỏe chu đáo. Khi đã rút lui, NTN sẽ không được tham gia lại vào nghiên cứu.")
    _add_p(doc, "Nghiên cứu viên chính hoặc bác sĩ lâm sàng có thể quyết định cho NTN ngừng tham gia nghiên cứu trong các trường hợp: xảy ra biến cố bất lợi nặng hoặc nghiêm trọng (SAE); nôn mửa hoặc tiêu chảy trong vòng 6 giờ sau khi uống thuốc; vi phạm nghiêm trọng quy định đề cương; hoặc mất liên lạc.")
    _add_p(doc, "Mọi trường hợp ngừng nghiên cứu sớm phải được ghi nhận rõ lý do, ngày giờ và có chữ ký xác nhận của Nghiên cứu viên trong Hồ sơ NTN.")

    # MỤC 7
    _add_p(doc, "7. QUY TRÌNH CHO UỐNG THUỐC VÀ KIỂM SOÁT ĂN UỐNG", bold=True, font_size=Pt(12), space_before=Pt(10), space_after=Pt(4), color=RGBColor(20, 50, 110))
    _add_p(doc, f"Mỗi NTN uống 1 liều ({c['test_prod']} hoặc {c['ref_prod']}) tương ứng với {c['dose']} {c['dose_unit']} hoạt chất cùng 240 mL nước đun sôi để nguội ở nhiệt độ phòng. Nuốt nguyên viên thuốc, không nhai hoặc bẻ vỡ viên. Nghiên cứu viên tiến hành kiểm tra khoang miệng ngay sau khi uống để đảm bảo NTN đã nuốt thuốc hoàn toàn.")
    _add_p(doc, "Sau khi uống thuốc, NTN phải ngồi ở tư thế lưng thẳng ít nhất 30 phút (hoặc 2 giờ). Không uống nước trong khoảng 1 giờ trước và 1 giờ sau khi uống thuốc, sau đó được uống nước tự do theo nhu cầu.")
    _add_p(doc, "Chế độ kiểm soát ăn uống: NTN chỉ được ăn bữa ăn chuẩn hóa vào khoảng 4 giờ và 11 giờ sau khi uống thuốc, và ăn bữa ăn nhẹ vào 3 giờ sau bữa ăn chuẩn hóa. Toàn bộ NTN được phục vụ cùng một thực đơn.")

    _add_p(doc, "Bảng 1. Bữa ăn chuẩn hóa (khoảng 4 giờ và 11 giờ sau khi uống thuốc):", bold=True, font_size=Pt(9.5), space_before=Pt(4), space_after=Pt(2))
    tbl_m1 = doc.add_table(rows=1, cols=3)
    tbl_m1.style = "Table Grid"
    tbl_m1.alignment = WD_TABLE_ALIGNMENT.CENTER
    m1_hdr = tbl_m1.rows[0]
    m1_hdr._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
    m1_w = [Cm(8.0), Cm(3.5), Cm(5.0)]
    _add_styled_cell(m1_hdr, 0, "Thành phần món ăn", m1_w[0], bold=True, shading_hex="EAECEF")
    _add_styled_cell(m1_hdr, 1, "Khối lượng", m1_w[1], bold=True, shading_hex="EAECEF", align=WD_ALIGN_PARAGRAPH.CENTER)
    _add_styled_cell(m1_hdr, 2, "Năng lượng (kcal)", m1_w[2], bold=True, shading_hex="EAECEF", align=WD_ALIGN_PARAGRAPH.RIGHT)
    for comp, weight, kcal in VKNT_MEAL_STANDARDIZED:
        r = tbl_m1.add_row()
        r._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        is_tot = "TỔNG" in comp
        _add_styled_cell(r, 0, comp, m1_w[0], bold=is_tot, shading_hex="F8F9FA" if is_tot else None)
        _add_styled_cell(r, 1, weight, m1_w[1], bold=is_tot, align=WD_ALIGN_PARAGRAPH.CENTER, shading_hex="F8F9FA" if is_tot else None)
        _add_styled_cell(r, 2, kcal, m1_w[2], bold=is_tot, align=WD_ALIGN_PARAGRAPH.RIGHT, shading_hex="F8F9FA" if is_tot else None)

    _add_p(doc, "Bảng 2. Bữa ăn nhẹ (khoảng 3 giờ sau bữa ăn chuẩn hóa):", bold=True, font_size=Pt(9.5), space_before=Pt(4), space_after=Pt(2))
    tbl_m2 = doc.add_table(rows=1, cols=3)
    tbl_m2.style = "Table Grid"
    tbl_m2.alignment = WD_TABLE_ALIGNMENT.CENTER
    m2_hdr = tbl_m2.rows[0]
    m2_hdr._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
    _add_styled_cell(m2_hdr, 0, "Thành phần món ăn", m1_w[0], bold=True, shading_hex="EAECEF")
    _add_styled_cell(m2_hdr, 1, "Khối lượng / Thể tích", m1_w[1], bold=True, shading_hex="EAECEF", align=WD_ALIGN_PARAGRAPH.CENTER)
    _add_styled_cell(m2_hdr, 2, "Giá trị dinh dưỡng", m1_w[2], bold=True, shading_hex="EAECEF")
    for comp, weight, kcal in VKNT_MEAL_SNACK:
        r = tbl_m2.add_row()
        r._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        is_tot = "TỔNG" in comp
        _add_styled_cell(r, 0, comp, m1_w[0], bold=is_tot, shading_hex="F8F9FA" if is_tot else None)
        _add_styled_cell(r, 1, weight, m1_w[1], bold=is_tot, align=WD_ALIGN_PARAGRAPH.CENTER, shading_hex="F8F9FA" if is_tot else None)
        _add_styled_cell(r, 2, kcal, m1_w[2], bold=is_tot, shading_hex="F8F9FA" if is_tot else None)

    _add_p(doc, "Quy định kiêng cữ:", bold=True, font_size=Pt(10), space_before=Pt(3), space_after=Pt(1))
    _add_p(doc, "Không uống rượu bia, cà phê, trà, nước tăng lực, nước ép bưởi chùm trong vòng 48 giờ trước khi uống thuốc cho đến khi lấy xong mẫu máu cuối cùng của mỗi giai đoạn. Không sử dụng bất kỳ loại thuốc nào khác trong suốt quá trình tham gia nghiên cứu. Không vận động thể lực nặng 48 giờ trước ngày uống thuốc và trong thời gian lưu trú tại trung tâm.")

    # MỤC 8
    _add_p(doc, "8. KẾ HOẠCH THỰC HIỆN VÀ PHÂN TÍCH", bold=True, font_size=Pt(12), space_before=Pt(10), space_after=Pt(4), color=RGBColor(20, 50, 110))
    _add_p(doc, "8.1. Quản lý nghiên cứu và Lịch trình (Schedule of Events):", bold=True, font_size=Pt(10.5), space_before=Pt(2), space_after=Pt(2))

    tbl_soe = doc.add_table(rows=1, cols=7)
    tbl_soe.style = "Table Grid"
    tbl_soe.alignment = WD_TABLE_ALIGNMENT.CENTER
    soe_hdr = tbl_soe.rows[0]
    soe_hdr._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
    soe_hdr._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))
    soe_w = [Cm(0.9), Cm(6.6), Cm(1.8), Cm(1.8), Cm(1.8), Cm(1.8), Cm(1.8)]
    _add_styled_cell(soe_hdr, 0, "STT", soe_w[0], bold=True, shading_hex="EAECEF", align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8.5))
    _add_styled_cell(soe_hdr, 1, "Quy trình thực hiện", soe_w[1], bold=True, shading_hex="EAECEF", font_size=Pt(8.5))
    _add_styled_cell(soe_hdr, 2, "Tuyển chọn", soe_w[2], bold=True, shading_hex="EAECEF", align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8.5))
    _add_styled_cell(soe_hdr, 3, "Giai đoạn 1", soe_w[3], bold=True, shading_hex="EAECEF", align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8.5))
    _add_styled_cell(soe_hdr, 4, "Thải trừ", soe_w[4], bold=True, shading_hex="EAECEF", align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8.5))
    _add_styled_cell(soe_hdr, 5, "Giai đoạn 2", soe_w[5], bold=True, shading_hex="EAECEF", align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8.5))
    _add_styled_cell(soe_hdr, 6, "Kết thúc", soe_w[6], bold=True, shading_hex="EAECEF", align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8.5))

    for stt, act, sc, p1, wo, p2, ed in VKNT_SCHEDULE_OF_EVENTS:
        r = tbl_soe.add_row()
        r._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        _add_styled_cell(r, 0, stt, soe_w[0], align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8.5))
        _add_styled_cell(r, 1, act, soe_w[1], font_size=Pt(8.5))
        _add_styled_cell(r, 2, sc, soe_w[2], align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8.5))
        _add_styled_cell(r, 3, p1, soe_w[3], align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8.5))
        _add_styled_cell(r, 4, wo, soe_w[4], align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8.5))
        _add_styled_cell(r, 5, p2, soe_w[5], align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8.5))
        _add_styled_cell(r, 6, ed, soe_w[6], align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8.5))

    _add_p(doc, "8.2. Đánh giá các thông số dược động học", bold=True, font_size=Pt(10.5), space_before=Pt(6), space_after=Pt(2))
    _add_p(doc, "8.2.1. Lấy mẫu máu:", bold=True, font_size=Pt(10), space_before=Pt(2), space_after=Pt(1))
    _add_p(doc, f"Máu tĩnh mạch được lấy qua kim luồn hoặc tiêm trực tiếp vào ống nghiệm tráng chất chống đông K2EDTA. Lịch lấy mẫu: {c['sampling_val']}. Mỗi lần lấy khoảng 5-6 mL máu. Trong vòng 20 phút sau khi lấy, mẫu được ly tâm lạnh ở tốc độ 4000 vòng/phút trong 5-10 phút để tách huyết tương. Huyết tương được chia đều thành 2 ống cryotube (ống phân tích chính và ống lưu dự phòng), dán nhãn mã hóa và bảo quản trong tủ đông âm sâu dưới -70°C cho đến ngày phân tích.")
    _add_p(doc, "Dung sai thời gian lấy mẫu: Trong 24 giờ đầu, sai lệch quá ± 2 đến 5 phút so với thời gian danh định phải ghi rõ lý do vào Hồ sơ NTN. Sau 24 giờ, sai lệch quá ± 30 phút phải ghi rõ lý do. Thời điểm lấy mẫu thực tế được sử dụng để tính toán thông số dược động học.")

    _add_p(doc, "8.2.2. Phương pháp phân tích mẫu sinh học:", bold=True, font_size=Pt(10), space_before=Pt(2), space_after=Pt(1))
    _add_p(doc, f"Phương pháp phân tích LC-MS/MS định lượng {c['active_ing']} trong huyết tương người được thẩm định đầy đủ theo tiêu chuẩn ICH M10, US-FDA và EMA: tính chọn lọc không bị ảnh hưởng bởi nền mẫu; khoảng tuyến tính phù hợp với nồng độ dự kiến; độ đúng và độ chính xác trong ngày và giữa các ngày <= 15% (riêng LLOQ <= 20%); hiệu ứng nền matrix effect ổn định; độ ổn định mẫu qua các chu kỳ đông-rã, ổn định ngắn hạn và dài hạn.")

    _add_p(doc, "8.2.3. Phân tích dược động học (NCA):", bold=True, font_size=Pt(10), space_before=Pt(2), space_after=Pt(1))
    _add_p(doc, "Các thông số dược động học phi ngăn (NCA) được tính toán bằng phần mềm chuyên dụng (be_app / Phoenix WinNonlin) theo quy tắc hình thang tuyến tính kết hợp logarit (linear-up / log-down): Cmax, Tmax, AUC0-t, AUC0-inf, t1/2, Kel và %AUCextrap.")

    _add_p(doc, "8.2.4. Phân tích lại mẫu (ISR - Incurred Sample Reanalysis):", bold=True, font_size=Pt(10), space_before=Pt(2), space_after=Pt(1))
    _add_p(doc, "Tiến hành phân tích lại mẫu nghiên cứu thực tế theo tiêu chuẩn ICH M10: tối thiểu 10% cho 1000 mẫu đầu tiên và 5% cho các mẫu tiếp theo. Tiêu chuẩn chấp thuận: ít nhất 67% số mẫu phân tích lại có độ sai khác không quá ± 20% so với giá trị ban đầu.")

    _add_p(doc, "8.3. Đánh giá tính an toàn:", bold=True, font_size=Pt(10), space_before=Pt(2), space_after=Pt(1))
    _add_p(doc, "Đo sinh hiệu (huyết áp, mạch, thân nhiệt) trước khi uống thuốc, sau khi uống thuốc 4 giờ, 12 giờ, 24 giờ và trước khi NTN ra về. Bác sĩ lâm sàng khám và theo dõi phát hiện kịp thời mọi biến cố bất lợi.")

    # MỤC 9
    _add_p(doc, "9. QUẢN LÝ VÀ BẢO QUẢN THUỐC NGHIÊN CỨU", bold=True, font_size=Pt(12), space_before=Pt(10), space_after=Pt(4), color=RGBColor(20, 50, 110))
    _add_p(doc, "9.1. Ngẫu nhiên hóa và làm mù:", bold=True, font_size=Pt(10), space_before=Pt(2), space_after=Pt(1))
    _add_p(doc, "Bảng ngẫu nhiên hóa được thiết lập bằng phần mềm máy tính có kiểm chứng theo khối (block randomization). Nghiên cứu là thiết kế nhãn mở đối với nghiên cứu viên lâm sàng nhưng làm mù đối với nhân viên phòng phân tích mẫu sinh học (mẫu huyết tương chỉ ghi mã số đối tượng và thời điểm).")
    _add_p(doc, "9.2. Cung cấp, bảo quản và kiểm soát thuốc:", bold=True, font_size=Pt(10), space_before=Pt(2), space_after=Pt(1))
    _add_p(doc, f"Thuốc thử ({c['test_prod']}) và thuốc đối chứng ({c['ref_prod']}) được bảo quản ở điều kiện nhiệt độ dưới 30°C, tránh ánh sáng và độ ẩm theo đúng nhãn thuốc. Dược sĩ phụ trách nghiên cứu ghi chép đầy đủ Phiếu theo dõi xuất nhập thuốc (Drug Accountability Log) và lưu giữ mẫu lưu theo quy định (ít nhất 5 năm theo FDA hoặc 1 năm sau hạn dùng theo EMA).")

    # MỤC 10
    _add_p(doc, "10. THEO DÕI VÀ XỬ TRÍ BIẾN CỐ BẤT LỢI (AE / SAE)", bold=True, font_size=Pt(12), space_before=Pt(10), space_after=Pt(4), color=RGBColor(20, 50, 110))
    _add_p(doc, "Mọi biến cố bất lợi (AE) xuất hiện từ khi NTN ký ICF đến hết thời gian theo dõi đều phải được ghi nhận vào Bệnh án nghiên cứu (CRF) với đầy đủ thông tin: thời điểm bắt đầu/kết thúc, mức độ (nhẹ, trung bình, nặng), mối liên quan nhân quả với thuốc thử (Không liên quan, Ít khả năng, Có thể, Chắc chắn), biện pháp xử trí và kết cục.")
    _add_p(doc, "Quy trình báo cáo khẩn cấp biến cố bất lợi nghiêm trọng (SAE): Trong trường hợp xảy ra SAE gây tử vong hoặc đe dọa tính mạng, Nghiên cứu viên chính phải thông báo khẩn cấp cho Hội đồng Đạo đức trong nghiên cứu y sinh học và Cơ quan Quản lý Dược có thẩm quyền trong vòng 24 giờ, và gửi báo cáo đầy đủ trong vòng 07 ngày làm việc. Các SAE khác phải báo cáo trong vòng 15 ngày làm việc.")

    # MỤC 11
    _add_p(doc, "11. KẾ HOẠCH PHÂN TÍCH THỐNG KÊ (SAP) VÀ CỠ MẪU", bold=True, font_size=Pt(12), space_before=Pt(10), space_after=Pt(4), color=RGBColor(20, 50, 110))
    _add_p(doc, "11.1. Mô hình phân tích thống kê Dược động học:", bold=True, font_size=Pt(10), space_before=Pt(2), space_after=Pt(1))
    _add_p(doc, "Phân tích phương sai ANOVA hoặc Mô hình hiệu ứng hỗn hợp (Linear Mixed-Effects Model) trên các thông số đã biến đổi logarit tự nhiên ln(Cmax), ln(AUC0-t), ln(AUC0-inf) với các yếu tố cố định: Trình tự (Sequence), Kỳ (Period), Thuốc (Treatment) và yếu tố ngẫu nhiên Đối tượng lồng trong trình tự [Subject(Sequence)].")
    _add_p(doc, "Tiêu chuẩn chấp thuận tương đương sinh học (BE Acceptance Criteria):")
    _add_p(doc, "Khoảng tin cậy 90% (CI 90% theo kiểm định TOST ở mức alpha = 0.05) của tỷ số trung bình nhân GMR (Test / Reference) đối với Cmax và AUC0-t phải nằm hoàn toàn trong khoảng chấp thuận 80.00% - 125.00%.")
    _add_p(doc, "Thông số Tmax được phân tích so sánh bằng phép kiểm định phi tham số Wilcoxon signed-rank test. Báo cáo giá trị sức mạnh thống kê (Power).")
    _add_p(doc, "11.2. Căn cứ tính cỡ mẫu:", bold=True, font_size=Pt(10), space_before=Pt(2), space_after=Pt(1))
    _add_p(doc, f"Căn cứ cỡ mẫu được xác định dựa trên hệ số biến thiên trong cá thể (CVw), mức ý nghĩa alpha = 0.05, sức mạnh thống kê mong muốn 1 - beta >= 80% (hoặc 90%), tỷ số GMR kỳ vọng trong khoảng 0.95 - 1.05. Theo hướng dẫn của ASEAN, EMA và ICH M13A, số lượng đối tượng có dữ liệu đánh giá được tối thiểu không dưới 12 người. Kế hoạch cỡ mẫu: {c['sample_size_str']}.")

    # MỤC 12, 13, 14
    _add_p(doc, "12. QUẢN LÝ VÀ LƯU TRỮ HỒ SƠ NGHIÊN CỨU", bold=True, font_size=Pt(12), space_before=Pt(10), space_after=Pt(4), color=RGBColor(20, 50, 110))
    _add_p(doc, "Tất cả hồ sơ gốc của nghiên cứu (TMF/ISF), bệnh án CRF, dữ liệu sắc ký thô, nhật ký audit trail và tài liệu liên quan được lưu trữ bảo mật tại cơ sở thử nghiệm trong thời gian tối thiểu 5 năm sau khi kết thúc nghiên cứu (hoặc theo quy định hiện hành của Bộ Y tế).")

    _add_p(doc, "13. KIỂM SOÁT CHẤT LƯỢNG VÀ ĐẢM BẢO CHẤT LƯỢNG (QC/QA)", bold=True, font_size=Pt(12), space_before=Pt(10), space_after=Pt(4), color=RGBColor(20, 50, 110))
    _add_p(doc, "Nghiên cứu tuân thủ hệ thống quản lý chất lượng và các SOP nội bộ của đơn vị. Bộ phận Đảm bảo chất lượng (QA) độc lập tiến hành giám sát định kỳ các khâu lâm sàng, phân tích sinh học và thẩm tra số liệu theo nguyên tắc toàn vẹn dữ liệu ALCOA+.")

    _add_p(doc, "14. ĐÁNH GIÁ TRỰC TIẾP VÀ CHỮ KÝ PHÊ DUYỆT", bold=True, font_size=Pt(12), space_before=Pt(10), space_after=Pt(4), color=RGBColor(20, 50, 110))
    _add_p(doc, "Đơn vị nghiên cứu chấp thuận việc thanh tra, kiểm tra trực tiếp từ Đơn vị yêu cầu (Nhà tài trợ), Hội đồng Đạo đức và Cơ quan Quản lý Dược có thẩm quyền trên hồ sơ và dữ liệu gốc.")

    _add_p(doc, f"TP. Hồ Chí Minh, ngày {c['protocol_date'].split('/')[0]} tháng {c['protocol_date'].split('/')[1]} năm {c['protocol_year']}", italic=True, align=WD_ALIGN_PARAGRAPH.RIGHT, space_before=Pt(12), space_after=Pt(8))

    tbl_sig = doc.add_table(rows=2, cols=3)
    tbl_sig.style = "Table Grid"
    tbl_sig.alignment = WD_TABLE_ALIGNMENT.CENTER
    s_widths = [Cm(5.5), Cm(5.5), Cm(5.5)]
    for r in tbl_sig.rows:
        r._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))

    _add_styled_cell(tbl_sig.rows[0], 0, "NGHIÊN CỨU VIÊN CHÍNH\n(Ký và ghi rõ họ tên)", s_widths[0], bold=True, shading_hex="F8F9FA", align=WD_ALIGN_PARAGRAPH.CENTER)
    _add_styled_cell(tbl_sig.rows[0], 1, "ĐƠN VỊ NGHIÊN CỨU\n(Ký tên và đóng dấu)", s_widths[1], bold=True, shading_hex="F8F9FA", align=WD_ALIGN_PARAGRAPH.CENTER)
    _add_styled_cell(tbl_sig.rows[0], 2, "ĐƠN VỊ YÊU CẦU (NHÀ TÀI TRỢ)\n(Ký tên và đóng dấu)", s_widths[2], bold=True, shading_hex="F8F9FA", align=WD_ALIGN_PARAGRAPH.CENTER)

    _add_styled_cell(tbl_sig.rows[1], 0, f"\n\n\n\n{c['pi']}", s_widths[0], bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    _add_styled_cell(tbl_sig.rows[1], 1, f"\n\n\n\n{c['institution']}", s_widths[1], bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    _add_styled_cell(tbl_sig.rows[1], 2, f"\n\n\n\n{c['sponsor']}", s_widths[2], bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)

    # MỤC 15: TÀI LIỆU THAM KHẢO
    _add_p(doc, "15. TÀI LIỆU THAM KHẢO", bold=True, font_size=Pt(12), space_before=Pt(16), space_after=Pt(4), color=RGBColor(20, 50, 110))
    _add_p(doc, "Tiếng Việt:", bold=True, font_size=Pt(10), space_before=Pt(2), space_after=Pt(2))
    refs_vi = [
        "1. Thông tư số 29/2018/TT-BYT ngày 29/10/2018 của Bộ Y tế về 'Quy định về thử thuốc trên lâm sàng'.",
        "2. Thông tư 03/2012/TT-BYT ngày 02/02/2012 của Bộ Y tế 'Hướng dẫn về thử thuốc trên lâm sàng'.",
        "3. Thông tư số 45/2017/TT-BYT ngày 16/11/2017 của Bộ Y tế về 'Quy định thành lập, chức năng, nhiệm vụ của Hội đồng đạo đức trong nghiên cứu y sinh học'.",
        "4. Bộ Y Tế, Dược thư Quốc gia Việt Nam.",
    ]
    for r in refs_vi:
        _add_p(doc, r, space_after=Pt(1))

    _add_p(doc, "Tiếng Anh:", bold=True, font_size=Pt(10), space_before=Pt(4), space_after=Pt(2))
    refs_en = [
        "1. ASEAN (2015), ASEAN Guideline for the Conduct of Bioequivalence Studies, pp. 1 - 43.",
        "2. EMA (2010), Guideline on the Investigation of Bioequivalence, CPMP/EWP/QWP/1401/98 Rev. 1/Corr **.",
        "3. EMA / ICH (2022), ICH Guideline M10 on Bioanalytical Method Validation, EMA/CHMP/ICH/172948/2019.",
        "4. ICH (2024), ICH Harmonised Guideline M13A: Bioequivalence for Immediate-Release Solid Oral Dosage Forms.",
        "5. ICH (2016/2023), Integrated Addendum to ICH E6(R1): Guideline for Good Clinical Practice E6(R2)/(R3).",
        "6. US-FDA (2021), Bioequivalence Studies with Pharmacokinetic Endpoints for Drugs Submitted Under an ANDA Guidance for Industry.",
        "7. US-FDA (2018), Bioanalytical Method Validation Guidance for Industry.",
        "8. WHO (2005), Handbook for Good Clinical Research Practice (GCP): Guidance for Implementation, pp. 1 - 89.",
    ]
    for r in refs_en:
        _add_p(doc, r, space_after=Pt(1))

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def pdf_protocol_vknt(
    project: Project,
    details: dict[str, str] | None = None,
    *,
    valid_plan: dict | None = None,
) -> bytes:
    """Generate PDF Bioequivalence Protocol matching the MOH / VKNT TP.HCM format."""
    c = build_vknt_protocol_content(project, details, valid_plan=valid_plan)
    font = _register_pdf_font()
    styles = getSampleStyleSheet()

    for s_name in ("Title", "Normal", "Heading1", "Heading2"):
        styles[s_name].fontName = font
        styles[s_name].textColor = colors.black

    styles["Normal"].fontSize, styles["Normal"].leading = 8.5, 11.5
    styles["Heading1"].fontSize, styles["Heading1"].leading = 10.5, 14
    styles["Heading2"].fontSize, styles["Heading2"].leading = 9.5, 12.5

    small_style = ParagraphStyle("StdSmall", fontName=font, fontSize=7.5, leading=10)
    bold_small = ParagraphStyle("StdBoldSmall", fontName=font, fontSize=7.5, leading=10, fontBold=True)

    def p_text(val: str, style="Normal"):
        if REQ_USER_INPUT_PREFIX_VI in val or LEGACY_MISSING_VI in val or "[" in val:
            parts = val.split("[")
            formatted = escape(parts[0])
            for part in parts[1:]:
                if "]" in part:
                    b_text, rest = part.split("]", 1)
                    formatted += f"<font color='#B42814'><b>[{escape(b_text)}]</b></font>{escape(rest)}"
                else:
                    formatted += f"[{escape(part)}"
            formatted = formatted.replace("\n", "<br/>")
            return Paragraph(formatted, styles[style])
        return Paragraph(escape(val).replace("\n", "<br/>"), styles[style])

    elements = []

    # Title & Header
    elements.append(Paragraph("BỘ Y TẾ — " + escape(c["institution"].upper()), styles["Heading1"]))
    elements.append(Paragraph(f"<b>PHỤ LỤC 10.1.1 — ĐỀ CƯƠNG NGHIÊN CỨU TƯƠNG ĐƯƠNG SINH HỌC</b>", styles["Heading1"]))
    elements.append(Paragraph(f"<b>{escape(c['full_title'])}</b>", styles["Heading2"]))
    elements.append(Paragraph(f"<font color='#B42814'><b>{STATUS_VI}</b></font>", styles["Normal"]))
    elements.append(Spacer(1, 6))

    # Summary table
    syn_data = [
        [Paragraph(f"<b>Mã đề tài:</b> {escape(c['study_id'])}", small_style), Paragraph(f"<b>Phiên bản:</b> {escape(c['version'])} ({escape(c['protocol_date'])})", small_style)],
        [Paragraph(f"<b>Đơn vị yêu cầu:</b> {escape(c['sponsor'])}", small_style), Paragraph(f"<b>Đơn vị nghiên cứu:</b> {escape(c['institution'])}", small_style)],
        [Paragraph(f"<b>Thuốc thử (T):</b> {escape(c['test_prod'])} ({escape(c['test_strength'])})", small_style), Paragraph(f"<b>Thuốc đối chứng (R):</b> {escape(c['ref_prod'])} ({escape(c['ref_strength'])})", small_style)],
        [Paragraph(f"<b>Thiết kế:</b> {escape(c['design_str'])}", small_style), Paragraph(f"<b>Cỡ mẫu:</b> {escape(c['sample_size_str'])}", small_style)],
    ]
    t_syn = Table(syn_data, colWidths=[8.0 * cm, 8.5 * cm])
    t_syn.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.35, colors.grey),
        ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elements.append(t_syn)
    elements.append(Spacer(1, 8))

    # 14 Sections summary in PDF
    for num, title in VKNT_PROTOCOL_SECTIONS:
        elements.append(KeepTogether([
            Paragraph(f"<b>{num}. {escape(title)}</b>", styles["Heading1"]),
            HRFlowable(width="100%", thickness=0.5, color=colors.navy, spaceBefore=1, spaceAfter=4),
        ]))
        if num == "1":
            elements.append(p_text(f"Nghiên cứu được phê duyệt bởi Hội đồng Đạo đức trong nghiên cứu y sinh học cơ sở tuân thủ Thông tư 45/2017/TT-BYT, Thông tư 29/2018/TT-BYT và Tuyên ngôn Helsinki. Mọi đối tượng tự nguyện ký Phiếu chấp thuận (ICF) trước khi tham gia."))
        elif num == "2":
            elements.append(p_text(f"Tổng quan đặc tính dược lý và dược động học của hoạt chất {c['active_ing']} theo Dược thư Quốc gia Việt Nam, bao gồm hấp thu, Cmax, Tmax, chuyển hóa và thải trừ."))
        elif num == "3":
            elements.append(p_text(f"Mục tiêu: Đánh giá tương đương sinh học in vivo giữa {c['test_prod']} và {c['ref_prod']} qua các thông số {', '.join(c['primary_endpoints'])} và theo dõi an toàn trên NTN."))
        elif num == "4":
            elements.append(p_text(f"Thiết kế: {c['design_str']}, {c['single_dose_str']}, {c['fed_str']}. Thời gian washout: {c['washout_val']}."))
        elif num == "5":
            elements.append(p_text("Tiêu chuẩn chọn lựa: NTN khỏe mạnh 18-50 tuổi, BMI 18-27 kg/m², mạch, huyết áp và các xét nghiệm huyết học, sinh hóa, nước tiểu trong giới hạn bình thường; âm tính HIV, HBsAg, HCV."))
        elif num == "6":
            elements.append(p_text("Quyền tự nguyện rút khỏi nghiên cứu của NTN và tiêu chí ngừng tham gia theo quyết định của Nghiên cứu viên."))
        elif num == "7":
            elements.append(p_text(f"Uống thuốc với 240 mL nước, ngồi thẳng 30 phút. Kiểm soát chặt chẽ chế độ ăn uống chuẩn hóa ({VKNT_MEAL_STANDARDIZED[-1][2]}) và kiêng cữ rượu bia, cà phê, nước bưởi 48 giờ."))
        elif num == "8":
            elements.append(p_text(f"Lấy mẫu máu: {c['sampling_val']}. Định lượng bằng LC-MS/MS theo ICH M10. Phân tích NCA xác định Cmax, AUC0-t, AUC0-inf, Tmax, t1/2, Kel. Kế hoạch ISR."))
        elif num == "9":
            elements.append(p_text("Ngẫu nhiên hóa theo khối; làm mù phòng phân tích; kiểm soát xuất nhập và lưu trữ thuốc theo SOP."))
        elif num == "10":
            elements.append(p_text("Theo dõi và xử trí biến cố bất lợi (AE/SAE); quy trình cấp cứu và báo cáo khẩn cấp cho Hội đồng Đạo đức và Cơ quan Quản lý Dược trong 24 giờ."))
        elif num == "11":
            elements.append(p_text("Kế hoạch phân tích thống kê: ANOVA ln-scale, khoảng tin cậy 90% của GMR (T/R) nằm trong [80.00% - 125.00%], Wilcoxon cho Tmax. Sức mạnh thống kê Power >= 80%."))
        elif num in ("12", "13", "14"):
            elements.append(p_text("Lưu trữ hồ sơ tối thiểu 5 năm theo nguyên tắc ALCOA+; đảm bảo chất lượng QA/QC; cam kết chấp thuận thanh tra trực tiếp trên hồ sơ gốc."))
        elif num == "15":
            elements.append(p_text("Tuân thủ hướng dẫn Thông tư 29/2018/TT-BYT, ASEAN BE Guideline, EMA BE Guideline, ICH M10, ICH M13A và US-FDA."))
        elements.append(Spacer(1, 4))

    out = io.BytesIO()

    def page_drawer(canvas, doc_obj):
        canvas.setFont(font, 7)
        canvas.drawString(1.6 * cm, 28.5 * cm, f"Đề cương {c['protocol_code']}  |  {CONTROLLED_LABEL}")
        canvas.drawString(1.6 * cm, 1.0 * cm, software_attribution("vi"))
        canvas.drawRightString(19.2 * cm, 1.0 * cm, f"{c['study_id']} | Trang {doc_obj.page}")

    SimpleDocTemplate(
        out,
        pagesize=(21 * cm, 29.7 * cm),
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=f"Đề cương BE - {c['study_id']}",
    ).build(elements, onFirstPage=page_drawer, onLaterPages=page_drawer)

    return out.getvalue()


def blank_protocol_vknt() -> bytes:
    """Generate a clean blank Word template based on the VKNT TP.HCM format."""
    from be_app.domain import Study
    mock_study = Study(
        study_id="MA-DE-TAI",
        title="ĐỀ CƯƠNG NGHIÊN CỨU TƯƠNG ĐƯƠNG SINH HỌC",
        active_ingredient="",
        test_product="",
        reference_product="",
        test_strength="",
        reference_strength="",
        test_manufacturer="",
        reference_manufacturer="",
        sponsor="",
        study_site="",
        principal_investigator="",
    )
    return docx_protocol_vknt(Project(study=mock_study))
