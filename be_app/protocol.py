"""Editable, pre-analysis BE study protocol drafts in Vietnamese Word and PDF.

Protocol content is sourced from the current study plus explicit planning notes.
It presents prospective plans, hypotheses, and acceptance criteria; it never asserts
that a study has been conducted, data collected, or a protocol approved.
"""

from __future__ import annotations

import io
from xml.sax.saxutils import escape

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from be_app.branding import software_attribution
from be_app.design import SEQUENCES
from be_app.document_standards import (
    REQ_USER_INPUT_PREFIX_VI,
    req_user_input,
)
from be_app.persistence import Project
from be_app.protocol_vknt_template import (
    blank_protocol_vknt,
    docx_protocol_vknt,
    pdf_protocol_vknt,
)
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

FIELD_GUIDANCE: dict[str, tuple[str, str]] = {
    "rationale": (
        "Cơ sở khoa học và lý do chọn thiết kế",
        "Nêu rõ cơ sở dược lý, đặc điểm PK, căn cứ chọn liều, đường dùng, thiết kế crossover/parallel/replicate và điều kiện đói/no theo hướng dẫn FDA/EMA/ICH M13A",
    ),
    "population": (
        "Quần thể tuyển chọn, tiêu chuẩn nhận và loại trừ",
        "Xác định tiêu chuẩn nhận (tình nguyện viên khỏe mạnh 18-55 tuổi, BMI 18.5-30 kg/m2, xét nghiệm lâm sàng bình thường) và loại trừ (dị ứng, bệnh lý tiêu hóa/gan/thận/tim mạch, thuốc đồng thời, phụ nữ mang thai)",
    ),
    "sample_size": (
        "Căn cứ cỡ mẫu khi chưa có kết quả tính hợp lệ",
        "Cung cấp giả định CV trong cá thể (CVw), tỷ số T/R dự kiến (GMR), mức ý nghĩa alpha=0.05, sức mạnh thống kê >= 80% hoặc 90%, dự kiến tỷ lệ bỏ cuộc 10-20% và số lượng đối tượng cần tuyển",
    ),
    "washout": (
        "Thời gian washout và căn cứ lựa chọn",
        "Xác định thời gian washout tối thiểu >= 5-7 lần thời gian bán thải t1/2 để nồng độ trước liều kỳ sau < 5% Cmax hoặc BLQ",
    ),
    "sampling": (
        "Lịch lấy mẫu nồng độ theo thời điểm dự kiến",
        "Quy định cụ thể các thời điểm: trước liều (0h), hấp thu (2-3 điểm trước Cmax), xung quanh Cmax (3-4 điểm), và thải trừ kéo dài ít nhất 72h hoặc 3-5 lần t1/2; kèm thể tích máu mỗi lần lấy và tổng thể tích máu",
    ),
    "administration": (
        "Cách dùng thuốc, kiểm soát ăn uống và lịch khám",
        "Chi tiết về thời gian nhịn ăn >= 10h, lượng nước uống (240 mL), bữa ăn tiêu chuẩn (sau 4h và 10h), hạn chế vận động và tư thế ngồi ít nhất 2-4h sau dùng thuốc",
    ),
    "bioanalysis": (
        "Phương pháp định lượng và thẩm định bioanalytical",
        "Mô tả phương pháp phân tích (LC-MS/MS), chất phân tích (thuốc mẹ/chất chuyển hóa), khoảng tuyến tính, LLOQ, yêu cầu thẩm định đầy đủ theo ICH M10: tính chọn lọc, độ đúng, độ chính xác, matrix effect, độ ổn định và kế hoạch ISR",
    ),
    "safety": (
        "Theo dõi an toàn và xử trí AE/SAE",
        "Quy trình theo dõi dấu hiệu sinh tồn, khám lâm sàng, phân loại và đánh giá mối liên quan của biến cố bất lợi (AE/SAE), quy trình báo cáo khẩn cấp cho IRB/cơ quan quản lý và phương án cấp cứu/xử trí",
    ),
    "ethics": (
        "Hội đồng đạo đức, đồng thuận và bảo mật",
        "Thông tin về Hội đồng Đạo đức trong nghiên cứu y sinh học (IRB/IEC), quy trình lấy phiếu chấp thuận tham gia nghiên cứu (Informed Consent Form - ICF) theo ICH E6(R3)/Tuyên ngôn Helsinki, đăng ký thử nghiệm lâm sàng và bảo mật dữ liệu",
    ),
    "statistics": (
        "Chi tiết SAP, quần thể phân tích và dữ liệu thiếu",
        "Mô hình thống kê (ANOVA/Linear Mixed Model), phép biến đổi logarit tự nhiên, phương pháp ước lượng GMR và khoảng tin cậy 90% (TOST), quy tắc xử lý dữ liệu thiếu, BLQ, outlier và các phân tích độ nhạy",
    ),
    "operations": (
        "Phân công, lưu trữ, QC và kế hoạch vận hành",
        "Phân công trách nhiệm nghiên cứu viên (Delegation of Authority Log), lưu trữ tài liệu nghiên cứu (TMF/ISF ít nhất 5-15 năm), kiểm soát chất lượng (QC/QA), kiểm tra tính toàn vẹn dữ liệu theo nguyên tắc ALCOA+ và quy trình khóa cơ sở dữ liệu",
    ),
}


def _filled(value: object, field_name: str = "", guidance: str = "") -> str:
    text = str(value).strip() if value is not None else ""
    if text:
        return text
    if field_name:
        return req_user_input(field_name, guidance or "Nhập thông tin theo hồ sơ nghiên cứu", language="vi", context="protocol")
    return MISSING


def _row(label: str, value: object, field_name: str = "", guidance: str = "") -> tuple[str, str]:
    return label, _filled(value, field_name, guidance)


def protocol_content(
    project: Project,
    details: dict[str, str] | None = None,
    *,
    valid_plan: dict | None = None,
) -> dict:
    """Return an ordered outline without changing project or accepting stale planning."""
    study = project.study
    rule = RULES[study.rule_set_id]
    capability = capability_for(study.rule_set_id)
    details = details or {}

    def note(key: str) -> str:
        val = details.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
        field_name, guidance = FIELD_GUIDANCE.get(
            key, (key, "Cần cung cấp và đối chiếu hồ sơ nghiên cứu")
        )
        return req_user_input(field_name, guidance, language="vi", context="protocol")

    sample_size = (
        f"Kế hoạch tính từ giả định đã nhập: N đánh giá {valid_plan['evaluable']}; "
        f"N tuyển {valid_plan['recruit']}; endpoint chi phối {valid_plan['curve_endpoint']}. "
        f"Giả định CV/GMR, dropout, nguồn dữ liệu và quần thể phải được đối chiếu với SAP "
        f"trước khi sử dụng."
        if valid_plan is not None else
        (details.get("sample_size").strip() if details.get("sample_size") and details.get("sample_size").strip() else MISSING)
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
        _row("Mã nghiên cứu", study.study_id, "Mã số nghiên cứu", "Nhập mã định danh nghiên cứu duy nhất"),
        _row("Tên nghiên cứu", study.title, "Tên nghiên cứu", "Nhập tên khoa học đầy đủ của nghiên cứu"),
        _row("Mã/phiên bản protocol", study.protocol, "Mã số và phiên bản đề cương", "Nhập mã đề cương và số hiệu phiên bản chính thức"),
        _row("Mã/phiên bản SAP", study.sap, "Mã số và phiên bản SAP", "Nhập mã số và phiên bản kế hoạch phân tích thống kê"),
        _row("Nhà tài trợ", study.sponsor, "Thông tin nhà tài trợ", "Nhập tên cơ quan/tổ chức tài trợ và người đại diện"),
        _row("Cơ sở thực hiện", study.study_site, "Cơ sở nghiên cứu lâm sàng", "Nhập tên bệnh viện/cơ sở thử nghiệm lâm sàng"),
        _row("Nghiên cứu viên chính", study.principal_investigator, "Nghiên cứu viên chính", "Nhập họ tên, học vị và chức danh của PI"),
        _row("Hoạt chất", study.active_ingredient, "Hoạt chất chính", "Nhập tên hoạt chất theo INN hoặc Dược điển"),
        _row("Trạng thái", "No (sau ăn)" if study.fed_state == "fed" else "Đói (nhịn ăn)"),
        _row("Thiết kế", {"2x2": "Crossover 2×2", "parallel": "Song song",
                             "partial3": "Partial replicate 3 kỳ", "full4": "Full replicate 4 kỳ"}[study.design]),
        _row("Quy tắc đánh giá", study.rule_set_id),
    ]
    products = [
        ("Thuốc thử (T)",
         _filled(study.test_product, "Tên thuốc thử", "Nhập tên thương mại và quy cách đóng gói của thuốc thử"),
         _filled(study.test_strength, "Hàm lượng thuốc thử", "Nhập hàm lượng hoạt chất của thuốc thử"),
         _filled(study.test_concentration, "Nồng độ thuốc thử", "Nhập nồng độ nếu dạng lỏng hoặc ghi N/A nếu là dạng rắn"),
         _filled(study.test_dosage_form, "Dạng bào chế thuốc thử", "Nhập dạng bào chế theo Dược điển"),
         _filled(study.test_manufacturer, "Nhà sản xuất thuốc thử", "Nhập tên và địa chỉ cơ sở sản xuất thuốc thử"),
         _filled(study.test_batch, "Số lô sản xuất thuốc thử", "Nhập số lô sản xuất thực tế trên nhãn thuốc thử"),
         _filled(study.test_expiry_date, "Hạn dùng thuốc thử", "Nhập hạn dùng ghi trên nhãn thuốc thử")),
        ("Thuốc đối chứng (R)",
         _filled(study.reference_product, "Tên thuốc đối chứng", "Nhập tên biệt dược gốc / thuốc đối chứng chuẩn"),
         _filled(study.reference_strength, "Hàm lượng thuốc đối chứng", "Nhập hàm lượng hoạt chất của thuốc đối chứng"),
         _filled(study.reference_concentration, "Nồng độ thuốc đối chứng", "Nhập nồng độ nếu dạng lỏng hoặc ghi N/A nếu là dạng rắn"),
         _filled(study.reference_dosage_form, "Dạng bào chế thuốc đối chứng", "Nhập dạng bào chế của thuốc đối chứng"),
         _filled(study.reference_manufacturer, "Nhà sản xuất thuốc đối chứng", "Nhập tên cơ sở sản xuất thuốc đối chứng"),
         _filled(study.reference_batch, "Số lô sản xuất thuốc đối chứng", "Nhập số lô sản xuất trên nhãn thuốc đối chứng"),
         _filled(study.reference_expiry_date, "Hạn dùng thuốc đối chứng", "Nhập hạn dùng ghi trên nhãn thuốc đối chứng")),
    ]
    product_table = [
        ("Thuốc", "Tên thuốc", "Hàm lượng", "Nồng độ", "Dạng bào chế", "Nhà sản xuất", "Số lô", "Hạn dùng"),
        *[tuple(value for value in row) for row in products],
    ]
    sections = [
        ("1", "Tóm tắt đề cương", [
            f"Mục tiêu nghiên cứu: đánh giá tương đương sinh học (Bioequivalence - BE) in vivo giữa thuốc thử "
            f"{_filled(study.test_product, 'Thuốc thử', 'Tên thuốc thử')} và thuốc đối chứng "
            f"{_filled(study.reference_product, 'Thuốc đối chứng', 'Tên thuốc đối chứng')} đối với hoạt chất "
            f"{_filled(study.active_ingredient, 'Hoạt chất', 'Tên hoạt chất')}.",
            f"Thiết kế nghiên cứu: {summary[-2][1]}; các trình tự điều trị dự kiến: {', '.join(SEQUENCES[study.design])}. "
            f"Đường dùng: {_filled(study.route, 'Đường dùng', 'Đường dùng thuốc (oral, v.v.)')}; "
            f"chế độ liều: {'đơn liều (single-dose)' if study.single_dose else 'đa liều (multiple-dose)'}; "
            f"liều dùng dự kiến: {study.dose:g} {_filled(study.dose_unit, 'Đơn vị liều', 'Đơn vị liều (mg, mcg)')}; "
            f"điều kiện dùng thuốc: {summary[-3][1]}.",
            f"Endpoint PK chính đánh giá BE: {', '.join(study.primary_endpoints)}. "
            f"Endpoint PK phụ hỗ trợ: {', '.join(study.secondary_endpoints) if study.secondary_endpoints else MISSING}.",
            f"Tiêu chuẩn chấp thuận dự kiến: Khoảng tin cậy 90% của tỷ số trung bình nhân (GMR T/R) cho các endpoint chính "
            f"phải nằm trong khoảng chấp thuận theo quy định của bộ quy tắc {study.rule_set_id}.",
        ]),
        ("2", "Cơ sở khoa học và mục tiêu", [
            f"Căn cứ lựa chọn sản phẩm, hàm lượng, liều dùng, điều kiện đói/no và thiết kế nghiên cứu: {note('rationale')}",
            f"Đặc tính dược lý và dược động học lâm sàng: Hoạt chất {_filled(study.active_ingredient, 'Hoạt chất', 'Tên hoạt chất')} "
            f"được đánh giá về các đặc tính hấp thu, thời gian bán thải (t1/2), độ biến thiên sinh học, đường thải trừ và khả năng ảnh hưởng của thức ăn.",
            f"Khung hướng dẫn áp dụng: {rule.guideline} ({rule.section}); nghiên cứu được đối chiếu với các hướng dẫn quốc tế ICH M13A "
            f"(Bioequivalence for Immediate-Release Solid Oral Dosage Forms), ICH E6(R3) (GCP), ICH E8(R1), ICH E9, "
            f"hướng dẫn BA/BE của FDA Hoa Kỳ và hướng dẫn BE của Cơ quan Quản lý Dược phẩm Châu Âu (EMA). "
            f"Rà soát Product-Specific Guidance (PSG) và quy chuẩn Dược điển trước khi phê duyệt đề cương.",
        ]),
        ("3", "Sản phẩm nghiên cứu và quản lý thuốc", [
            "Thuốc thử (T) và thuốc đối chứng (R) được thẩm định và đối chiếu chi tiết với nhãn gốc, Giấy chứng nhận phân tích (CoA), "
            "hồ sơ lô sản xuất, điều kiện bảo quản, quy trình cấp phát, tính toán thuốc (accountability) và thu hồi. "
            "Bảng thông tin chi tiết hai sản phẩm được trình bày ở đầu đề cương.",
            "Quy mô lô sản xuất: Thuốc thử phải được sản xuất từ lô có quy mô đại diện thương mại (tối thiểu 100.000 đơn vị phân liều "
            "hoặc 1/10 quy mô thương mại theo quy định của FDA và EMA). Chênh lệch hàm lượng định lượng thực tế giữa T và R không quá 5%.",
            "Quản lý và lưu mẫu: Mô tả chi tiết quy trình ngẫu nhiên hóa mã thuốc, kiểm soát cấp phát thuốc, trách nhiệm của dược sĩ nghiên cứu, "
            "hồ sơ truy xuất chuỗi cung ứng và quy định lưu giữ mẫu lưu độc lập (FDA yêu cầu lưu 5 năm; EMA yêu cầu lưu tối thiểu 1 năm sau hạn dùng).",
        ]),
        ("4", "Thiết kế, ngẫu nhiên hóa và washout", [
            f"Thiết kế đã khai báo: {summary[-2][1]}; sequence dự kiến: {', '.join(SEQUENCES[study.design])}. "
            "Thiết kế nghiên cứu được lựa chọn nhằm tối ưu hóa sức mạnh thống kê và loại trừ tối đa biến thiên giữa các cá thể. "
            "Sơ đồ ngẫu nhiên hóa được thiết lập bằng phần mềm máy tính có kiểm chứng theo khối (block randomization) trước khi nghiên cứu bắt đầu.",
            "Quy trình cấp mã, phân bổ ngẫu nhiên, nguyên tắc che mù đối với phòng phân tích sinh học và quy trình xử lý rút lui/thay thế đối tượng.",
            f"Washout giữa các kỳ và căn cứ bán thải/PK: {note('washout')}",
            f"Điều kiện dùng thuốc và kiểm soát bữa ăn/nước uống: {note('administration')}",
        ]),
        ("5", "Đối tượng và tiêu chuẩn tuyển chọn", [
            f"Quần thể mục tiêu, độ tuổi, sức khỏe, tiêu chuẩn nhận/loại và xét nghiệm sàng lọc: {note('population')}",
            "Tiêu chuẩn nhận vào bao gồm: nam hoặc nữ tình nguyện khỏe mạnh từ 18-55 tuổi; BMI từ 18.5 đến 30.0 kg/m2; "
            "kết quả khám lâm sàng, điện tâm đồ (ECG) và các xét nghiệm huyết học, sinh hóa, nước tiểu trong giới hạn bình thường; "
            "âm tính với các xét nghiệm sàng lọc virus (HIV, HBV, HCV) và chất gây nghiện.",
            "Tiêu chuẩn loại trừ: tiền sử quá mẫn với thuốc thử hoặc tá dược; có bệnh lý tim mạch, gan, thận, tiêu hóa mạn tính; "
            "tiền sử nghiện rượu hoặc thuốc lá; dùng thuốc đồng thời trong vòng 14-28 ngày trước nghiên cứu; phụ nữ mang thai hoặc cho con bú.",
            "Bổ sung quy trình đồng thuận tự nguyện, tiêu chí ngừng tham gia của đối tượng, theo dõi người rút lui "
            "và danh sách phân định quần thể an toàn (Safety population) và quần thể đánh giá BE (PK population) theo SAP.",
        ]),
        ("6", "Cỡ mẫu và giả định thống kê", [
            f"Cỡ mẫu dự kiến: {sample_size}",
            f"Thiết kế {study.design}; profile {study.rule_set_id}. Chức năng tính power trong app: "
            f"{'được hỗ trợ cho profile này' if capability.planning else 'áp dụng công thức tính toán chuyên biệt cho profile này'}. "
            "Cần xác nhận giả định GMR, CV, tỷ lệ rút lui và sức mạnh thống kê cho các endpoint chính.",
            "Yêu cầu cỡ mẫu tối thiểu theo quy định: ICH M13A và EMA quy định số lượng đối tượng có dữ liệu đánh giá được "
            "không được dưới 12 người đối với nghiên cứu crossover và không dưới 12 người mỗi nhánh đối với nghiên cứu parallel. "
            "Cỡ mẫu tuyển chọn thực tế cần tính thêm tỷ lệ dự phòng bỏ cuộc (dropout rate thường 10% - 20%).",
        ]),
        ("7", "Quy trình nghiên cứu và lịch lấy mẫu", [
            f"Liều sử dụng: {study.dose:g} {_filled(study.dose_unit, 'Đơn vị liều', 'Đơn vị liều (mg, mcg)')}; "
            f"đường dùng: {_filled(study.route, 'Đường dùng', 'Đường dùng thuốc')}. "
            f"Chi tiết điều trị/ăn uống: {note('administration')}",
            f"Lịch lấy mẫu: {note('sampling')}",
            "Lịch lấy mẫu máu phải được thiết kế khoa học: gồm mẫu trắng trước liều (0 giờ), giai đoạn hấp thu lấy mẫu dày đặc "
            "(ít nhất 2-3 điểm trước Cmax dự kiến), xung quanh đỉnh Cmax (ít nhất 3-4 điểm), và giai đoạn thải trừ kéo dài ít nhất 72 giờ "
            "hoặc bao phủ 3 đến 5 lần thời gian bán thải t1/2 để diện tích dưới đường cong AUC0-t bao phủ ít nhất 80% của AUC0-inf.",
            "Ghi nhận thời điểm lấy mẫu thực tế chính xác (giờ:phút), quy trình chống đông (K2-EDTA), ly tâm lạnh (4°C), "
            "chia mẫu thành 2 phần (ống chính và ống dự phòng), bảo quản ở nhiệt độ -70°C đến -80°C và giám sát nhiệt độ liên tục (chain of custody).",
        ]),
        ("8", "Phân tích mẫu sinh học và thông số dược động học", [
            f"Chất phân tích: {_filled(study.analyte, 'Chất phân tích', 'Thuốc mẹ hoặc chất chuyển hóa')}. "
            f"Phương pháp định lượng, LLOQ, ổn định mẫu, thẩm định phương pháp và QA: {note('bioanalysis')}",
            "Thẩm định phương pháp phân tích sinh học (Bioanalytical Method Validation) bắt buộc tuân thủ tiêu chuẩn ICH M10: "
            "tính chọn lọc, đường chuẩn, độ đúng và độ chính xác trong ngày và giữa các ngày (<= 15%, riêng LLOQ <= 20%), "
            "hiệu ứng nền (matrix effect), độ thu hồi, độ nhiễm chéo, độ ổn định và phân tích lại mẫu nghiên cứu thực tế (ISR).",
            "Phân tích phi ngăn (NCA) xác định Cmax, Tmax, AUC0-t (hình thang tuyến tính/logarit), AUC0-inf, lambda_z và t1/2. "
            "Pha thải trừ cuối (terminal elimination phase) được xác định hồi quy tối thiểu 3 điểm nồng độ sau Cmax, adjusted R² >= 0.80, "
            "khoảng thời gian >= 1-2 lần t1/2; cảnh báo nếu %AUC ngoại suy > 20%. Quy định xử lý mẫu BLQ, dữ liệu thiếu và ngoại lệ phải nêu rõ trong SAP.",
        ]),
        ("9", "Kế hoạch phân tích thống kê (SAP)", [
            f"Phương pháp dự kiến: {method}",
            f"Scaling/NTI: {scaled} NTI khai báo: {'có' if study.nti else 'không'}. "
            f"Căn cứ HVD: {_filled(study.hvd_justification, 'Căn cứ HVD', 'Nêu rõ cơ sở biến thiên cao CVwR > 30% từ y văn')}.",
            f"Kế hoạch quần thể, mô hình, phương sai, handling dữ liệu thiếu/ngoại lệ: {note('statistics')}",
            "Mô hình thống kê chính: ANOVA hoặc Linear Mixed-Effects Model trên logarit tự nhiên ln(AUC) và ln(Cmax). "
            "Khoảng tin cậy 90% (TOST ở mức alpha = 0.05) của tỷ số trung bình nhân (GMR T/R) được sử dụng để kết luận BE. "
            "Mọi biên chấp nhận, tiêu chí mở rộng (ABEL theo EMA khi CVwR > 30% cho Cmax), tiêu chí chuẩn hóa tham chiếu (RSABE theo FDA), "
            "tiêu chí thu hẹp cho NTI và phân tích Tmax phi tham số phải được định trước trong SAP trước khi mở mù hoặc khóa dữ liệu.",
        ]),
        ("10", "Đánh giá an toàn", [
            f"Theo dõi AE/SAE, dấu hiệu sinh tồn, xét nghiệm, quy trình báo cáo khẩn: {note('safety')}",
            "Quy trình theo dõi an toàn từ lúc đối tượng ký đồng thuận đến khi kết thúc nghiên cứu: đo sinh hiệu, khám lâm sàng định kỳ, "
            "xét nghiệm kiểm tra tại thời điểm kết thúc nghiên cứu.",
            "Phân loại biến cố bất lợi theo CTCAE, đánh giá mức độ nghiêm trọng và mối quan hệ nhân quả với thuốc nghiên cứu. "
            "Quy trình báo cáo khẩn cấp đối với biến cố bất lợi nghiêm trọng (SAE / SUSAR) cho Hội đồng Đạo đức và Cơ quan Quản lý Dược trong vòng 24 giờ. "
            "Xác định rõ tiêu chí dừng nghiên cứu đối với từng cá nhân và tiêu chí tạm dừng toàn bộ nghiên cứu.",
        ]),
        ("11", "Đạo đức, quyền lợi và bảo mật", [
            f"Đánh giá Hội đồng đạo đức, phiếu đồng thuận, đăng ký nghiên cứu và bảo mật: {note('ethics')}",
            "Nghiên cứu được tiến hành hoàn toàn tuân thủ theo Tuyên ngôn Helsinki, Thực hành tốt thử nghiệm lâm sàng ICH E6(R3) "
            "và các quy định pháp luật sở tại về thử nghiệm lâm sàng.",
            "Nghiên cứu chỉ được phép khởi động sau khi có văn bản phê duyệt chính thức từ Hội đồng Đạo đức trong nghiên cứu y sinh học (IRB/IEC). "
            "Đối tượng tham gia tự nguyện ký phiếu chấp thuận tham gia nghiên cứu (ICF). "
            "Bảo mật thông tin cá nhân đối tượng theo quy định; kinh phí và bảo hiểm bồi thường cho đối tượng được cam kết đầy đủ.",
        ]),
        ("12", "Data Integrity, quản lý dữ liệu và QC", [
            f"Phân công, chứng từ nguồn, nhập liệu kép/đối chiếu, quyền truy cập, backup: {note('operations')}",
            "Tuân thủ nguyên tắc ALCOA+ (Attributable, Legible, Contemporaneous, Original, Accurate, Complete, Consistent, Enduring, Available). "
            "Bệnh án nghiên cứu (eCRF/CRF) được nhập liệu kép độc lập và đối chiếu 100% với tài liệu nguồn (SDV).",
            "Hệ thống máy tính và phần mềm phải được thẩm định (CSV) tuân thủ 21 CFR Part 11 / EU Annex 11. "
            "Nhật ký truy vết (audit trail) được kích hoạt liên tục và rà soát định kỳ; quy định rõ quy trình kiểm tra dữ liệu mù, "
            "đóng băng dữ liệu (Data Freeze) và khóa cơ sở dữ liệu (Data Lock) trước khi phân tích thống kê.",
        ]),
        ("13", "Tiến độ dự kiến và trách nhiệm", [
            f"Toàn nghiên cứu: {_filled(study.study_start_date, 'Ngày bắt đầu nghiên cứu', 'Ngày bắt đầu')} đến {_filled(study.study_end_date, 'Ngày kết thúc nghiên cứu', 'Ngày kết thúc')}; "
            f"giai đoạn lâm sàng: {_filled(study.clinical_start_date, 'Ngày bắt đầu lâm sàng', 'Ngày bắt đầu')} đến {_filled(study.clinical_end_date, 'Ngày kết thúc lâm sàng', 'Ngày kết thúc')}.",
            f"Giai đoạn phân tích mẫu sinh học: {_filled(study.bioanalytical_start_date, 'Ngày bắt đầu phân tích', 'Ngày bắt đầu')} đến "
            f"{_filled(study.bioanalytical_end_date, 'Ngày kết thúc phân tích', 'Ngày kết thúc')}; khóa dữ liệu: {_filled(study.data_lock_date, 'Ngày khóa dữ liệu', 'Ngày khóa dữ liệu')}.",
            f"Nhà tài trợ: {_filled(study.sponsor, 'Nhà tài trợ', 'Tên nhà tài trợ')}; "
            f"Nghiên cứu viên chính: {_filled(study.principal_investigator, 'PI', 'Tên nghiên cứu viên chính')}. "
            f"Các bước thực hiện và phân công chi tiết: {note('operations')}",
        ]),
        ("14", "Quản lý sửa đổi đề cương và phê duyệt", [
            f"Mã đề cương: {_filled(study.protocol, 'Mã đề cương', 'Mã số đề cương')}; SAP: {_filled(study.sap, 'Mã SAP', 'Mã số SAP')}. "
            "Mọi thay đổi đối với đề cương sau khi được phê duyệt phải được lập thành văn bản sửa đổi đề cương (Protocol Amendment). "
            "Các sửa đổi trọng yếu phải được Hội đồng Đạo đức và Cơ quan Quản lý Dược phê duyệt trước khi áp dụng.",
            "Ghi nhận đầy đủ nhật ký sai lệch đề cương (Deviation Log), nguyên nhân, biện pháp khắc phục và đánh giá ảnh hưởng đến kết quả nghiên cứu.",
            "Bảng chữ ký phê duyệt chính thức bao gồm Nghiên cứu viên chính, Đại diện Nhà tài trợ, Thống kê viên và Trưởng phòng Phân tích sinh học.",
            "Trạng thái tài liệu hiện tại: DỰ THẢO ĐỀ CƯƠNG — CHƯA ĐƯỢC PHÊ DUYỆT.",
        ]),
        ("15", "Tài liệu tham khảo và phụ lục", [
            f"Hướng dẫn quy định chính: {rule.guideline}; phiên bản quy tắc phần mềm: {rule.version}; "
            f"ngày nguồn được rà soát trong registry: {rule.source_verified_on}.",
            *(f"Nguồn hướng dẫn chính thức {i}: {source}" for i, source in enumerate(rule.sources, 1)),
            "Danh mục tài liệu tham khảo bổ sung: ICH M13A (2024), ICH M10 (2022), ICH E6(R3) (GCP), ICH E8(R1), ICH E9/E9(R1), ICH E3, "
            "FDA Guidance for Industry: Bioequivalence Studies with PK Endpoints (2021), EMA Guideline on the Investigation of Bioequivalence (2010).",
            "Phụ lục cần đính kèm theo hồ sơ: Sơ đồ lịch trình nghiên cứu (Schedule of Events), Phiếu thông tin và Phiếu chấp thuận tham gia nghiên cứu (ICF), "
            "Mẫu bệnh án nghiên cứu (CRF/eCRF), Khoảng tham chiếu cận lâm sàng, Tóm tắt quy trình thẩm định bioanalytical và Sơ đồ phân bổ ngẫu nhiên.",
        ]),
    ]
    return {
        "title": study.title,
        "study_id": study.study_id,
        "summary": summary,
        "product_table": product_table,
        "sections": sections,
        "training": study.is_demo or study.data_purpose == "training_qa",
    }


def docx_protocol(
    project: Project,
    details: dict[str, str] | None = None,
    *,
    valid_plan: dict | None = None,
    template: str = "legacy",
) -> bytes:
    if template in ("standard", "vknt", "vknt_tt91", "vn_moh", "standard_vn"):
        return docx_protocol_vknt(project, details, valid_plan=valid_plan)
    content = protocol_content(project, details, valid_plan=valid_plan)
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.top_margin = sec.bottom_margin = Cm(2)
    sec.left_margin = sec.right_margin = Cm(1.8)

    for name in ("Normal", "Title", "Heading 1", "Heading 2", "Heading 3"):
        style = doc.styles[name]
        style.font.name = "Arial"
        style.font.color.rgb = RGBColor(0, 0, 0)
        fonts = style.element.get_or_add_rPr().find(qn("w:rFonts"))
        for attribute in ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme"):
            fonts.attrib.pop(qn("w:" + attribute), None)
        for attribute in ("eastAsia", "cs"):
            fonts.set(qn("w:" + attribute), "Arial")
        properties = style.element.find(qn("w:pPr"))
        if properties is not None:
            for border in properties.findall(qn("w:pBdr")):
                properties.remove(border)

    doc.styles["Normal"].font.size = Pt(10)
    doc.styles["Normal"].paragraph_format.space_after = Pt(4)
    doc.styles["Heading 1"].font.size = Pt(12)
    doc.styles["Heading 1"].font.bold = True
    doc.styles["Heading 1"].paragraph_format.space_before = Pt(10)
    doc.styles["Heading 1"].paragraph_format.space_after = Pt(4)
    doc.styles["Heading 2"].font.size = Pt(10.5)
    doc.styles["Heading 2"].font.bold = True
    doc.styles["Heading 2"].paragraph_format.space_before = Pt(6)
    doc.styles["Heading 2"].paragraph_format.space_after = Pt(2)

    # Header and Footer
    sec.header.paragraphs[0].text = STATUS
    sec.header.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    sec.header.paragraphs[0].runs[0].font.size = Pt(8)
    sec.header.paragraphs[0].runs[0].font.color.rgb = RGBColor(128, 128, 128)

    footer = sec.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run(software_attribution("vi")).font.size = Pt(8)

    # Document Header
    title_p = doc.add_paragraph("ĐỀ CƯƠNG NGHIÊN CỨU TƯƠNG ĐƯƠNG SINH HỌC", "Title")
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_p = doc.add_paragraph("BIOEQUIVALENCE STUDY PROTOCOL (THEO HƯỚNG DẪN FDA / EMA / ICH M13A)")
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_p.runs[0].font.size = Pt(10)
    sub_p.runs[0].font.bold = True

    status_p = doc.add_paragraph(STATUS)
    status_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    status_p.runs[0].font.size = Pt(9)
    status_p.runs[0].font.bold = True
    status_p.runs[0].font.color.rgb = RGBColor(180, 40, 40)

    if content["training"]:
        train_p = doc.add_paragraph("DỮ LIỆU ĐÀO TẠO/GIẢ LẬP — KHÔNG SỬ DỤNG CHO NGHIÊN CỨU THỰC")
        train_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        train_p.runs[0].font.size = Pt(9)
        train_p.runs[0].font.bold = True

    # Section: Administrative and Design Summary
    doc.add_heading("Thông tin hành chính và thiết kế", level=1)
    table = doc.add_table(rows=0, cols=2)
    table.style = "Table Grid"
    table.autofit = False
    col_widths = [Cm(5.0), Cm(12.4)]
    for column, width in zip(table.columns, col_widths, strict=True):
        column.width = width

    for label, value in content["summary"]:
        row = table.add_row()
        for cell, width in zip(row.cells, col_widths, strict=True):
            cell.width = width
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        row.cells[0].text = label
        row.cells[0].paragraphs[0].runs[0].font.bold = True
        row.cells[0].paragraphs[0].runs[0].font.size = Pt(9)
        row.cells[1].text = value
        for p in row.cells[1].paragraphs:
            for r in p.runs:
                r.font.size = Pt(9)
                if REQ_USER_INPUT_PREFIX_VI in r.text or "[CẦN BỔ SUNG" in r.text:
                    r.font.color.rgb = RGBColor(180, 50, 20)

    # Shading and cantSplit on table
    for row in table.rows:
        prevent_split = OxmlElement("w:cantSplit")
        row._tr.get_or_add_trPr().append(prevent_split)

    # Section: Products Table
    doc.add_heading("Thuốc thử và thuốc đối chứng", level=1)
    for product in content["product_table"][1:]:
        doc.add_heading(product[0], level=2)
        detail_table = doc.add_table(rows=0, cols=2)
        detail_table.style = "Table Grid"
        detail_table.autofit = False
        for column, width in zip(detail_table.columns, col_widths, strict=True):
            column.width = width
        for label, value in zip(content["product_table"][0][1:], product[1:], strict=True):
            row = detail_table.add_row()
            for cell, width in zip(row.cells, col_widths, strict=True):
                cell.width = width
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            row.cells[0].text = label
            row.cells[0].paragraphs[0].runs[0].font.bold = True
            row.cells[0].paragraphs[0].runs[0].font.size = Pt(9)
            row.cells[1].text = value
            for p in row.cells[1].paragraphs:
                for r in p.runs:
                    r.font.size = Pt(9)
                    if REQ_USER_INPUT_PREFIX_VI in r.text or "[CẦN BỔ SUNG" in r.text:
                        r.font.color.rgb = RGBColor(180, 50, 20)
        for row in detail_table.rows:
            prevent_split = OxmlElement("w:cantSplit")
            row._tr.get_or_add_trPr().append(prevent_split)

    # 15 Protocol Sections
    for number, title, paragraphs in content["sections"]:
        doc.add_heading(f"{number}. {title}", level=1)
        for item in paragraphs:
            p = doc.add_paragraph()
            # If text has manual input tags, highlight them
            if REQ_USER_INPUT_PREFIX_VI in item or "[CẦN BỔ SUNG" in item:
                parts = item.split("[")
                if parts[0]:
                    p.add_run(parts[0])
                for part in parts[1:]:
                    if "]" in part:
                        bracket_content, rest = part.split("]", 1)
                        r = p.add_run(f"[{bracket_content}]")
                        r.bold = True
                        r.font.color.rgb = RGBColor(180, 40, 20)
                        if rest:
                            p.add_run(rest)
                    else:
                        p.add_run(f"[{part}")
            else:
                p.add_run(item)

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def pdf_protocol(
    project: Project,
    details: dict[str, str] | None = None,
    *,
    valid_plan: dict | None = None,
    template: str = "legacy",
) -> bytes:
    if template in ("standard", "vknt", "vknt_tt91", "vn_moh", "standard_vn"):
        return pdf_protocol_vknt(project, details, valid_plan=valid_plan)
    content = protocol_content(project, details, valid_plan=valid_plan)
    font = _register_pdf_font()
    styles = getSampleStyleSheet()
    for style_name in ("Title", "Normal", "Heading1", "Heading2"):
        styles[style_name].fontName = font
        styles[style_name].textColor = colors.black
    styles["Normal"].fontSize, styles["Normal"].leading = 9, 13
    styles["Heading1"].fontSize, styles["Heading1"].leading = 11, 15
    styles["Heading2"].fontSize, styles["Heading2"].leading = 10, 13
    styles["Heading1"].keepWithNext = True
    small = ParagraphStyle("ProtocolSmall", fontName=font, fontSize=8, leading=11)

    def para(value: str, style="Normal"):
        return Paragraph(escape(value).replace("\n", "<br/>"), styles[style])

    elements = [
        para("ĐỀ CƯƠNG NGHIÊN CỨU TƯƠNG ĐƯƠNG SINH HỌC", "Title"),
        para(STATUS),
    ]
    if content["training"]:
        elements.append(para("DỮ LIỆU ĐÀO TẠO/GIẢ LẬP — KHÔNG SỬ DỤNG CHO NGHIÊN CỨU THỰC"))
    elements.append(para("Thông tin hành chính và thiết kế", "Heading1"))

    def table(rows):
        result = Table(
            [[Paragraph(escape(str(cell)), small) for cell in row] for row in rows],
            colWidths=[4.9 * cm, 11.5 * cm],
            repeatRows=0,
            hAlign="LEFT",
        )
        result.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.35, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
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
        canvas.drawString(1.6 * cm, 1.1 * cm, software_attribution("vi"))
        canvas.drawRightString(19.2 * cm, 1.1 * cm, f"{content['study_id']} | {document.page}")

    SimpleDocTemplate(
        out,
        pagesize=(21 * cm, 29.7 * cm),
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=f"Đề cương BE - {content['study_id']}",
    ).build(elements, onFirstPage=page, onLaterPages=page)
    return out.getvalue()


def blank_protocol_template(template: str = "legacy") -> bytes:
    """Return a blank protocol Word template with standard placeholders and guidelines."""
    if template in ("standard", "vknt", "vknt_tt91", "vn_moh", "standard_vn"):
        return blank_protocol_vknt()
    from be_app.domain import Study
    return docx_protocol(Project(study=Study(study_id="BLANK-PROTOCOL", title="ĐỀ CƯƠNG NGHIÊN CỨU BE")))

