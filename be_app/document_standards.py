"""Standardized Regulatory Specifications, Field Mappings, and Placeholders for BE Documents.

This module unifies the regulatory guidance requirements (FDA, EMA, ICH),
data field mappings (auto-filled, calculated, manual input), and standardized
bilingual placeholders across both the Bioequivalence Study Protocol
and Bioequivalence Study Report.
"""

from __future__ import annotations

from typing import Any

# Standard placeholder markers required by regulatory review procedures
REQ_USER_INPUT_PREFIX_VI = "[YÊU CẦU NGƯỜI DÙNG BỔ SUNG:"
REQ_USER_INPUT_PREFIX_EN = "[USER INPUT REQUIRED:"

LEGACY_MISSING_VI = "[CẦN BỔ SUNG / XÁC NHẬN]"
LEGACY_MISSING_EN = "[NOT PROVIDED / TO BE COMPLETED]"

REPORT_BLANK_VI = "CHƯA CUNG CẤP — cần bổ sung hồ sơ gốc và xác minh."
REPORT_BLANK_EN = "NOT PROVIDED — supply and verify the source records."


def req_user_input(
    field_name: str,
    guidance: str,
    language: str = "vi",
    *,
    context: str = "protocol",
) -> str:
    """Return a standardized, prominent placeholder for missing/manual input fields.

    Contains both the user-specified prefix [YÊU CẦU NGƯỜI DÙNG BỔ SUNG: ...]
    and the backward-compatible marker ([CẦN BỔ SUNG] for protocol,
    CHƯA CUNG CẤP for report) to ensure strict auditability and test integrity.
    """
    vi = language == "vi"
    if vi:
        tag = f"{REQ_USER_INPUT_PREFIX_VI} {field_name} – {guidance}]"
        if context == "protocol":
            return f"{tag} {LEGACY_MISSING_VI}"
        return f"{tag} ({REPORT_BLANK_VI})"
    tag = f"{REQ_USER_INPUT_PREFIX_EN} {field_name} – {guidance}]"
    if context == "protocol":
        return f"{tag} {LEGACY_MISSING_EN}"
    return f"{tag} ({REPORT_BLANK_EN})"


# ---------------------------------------------------------------------------
# FDA vs EMA vs ICH Regulatory Comparison Matrix
# ---------------------------------------------------------------------------
REGULATORY_COMPARISON_MATRIX = [
    {
        "category": "Khung pháp lý chung & Tiêu chuẩn đạo đức / GCP",
        "topic": "Đạo đức, Bảo vệ đối tượng & Thực hành tốt thử nghiệm lâm sàng (GCP)",
        "fda_requirement": "Bắt buộc tuân thủ 21 CFR 50 (Informed Consent), 21 CFR 56 (IRB), 21 CFR 312/320. Khuyến nghị áp dụng ICH E6(R3) và Tuyên ngôn Helsinki.",
        "ema_requirement": "Bắt buộc tuân thủ EU Clinical Trials Regulation (EU No 536/2014), ICH E6(R3) GCP, Tuyên ngôn Helsinki và phê duyệt của Ethics Committee (IEC).",
        "ich_harmonization": "ICH E6(R3), ICH E8(R1) quy định quản lý chất lượng dựa trên rủi ro (Risk-based Quality Management) và bảo vệ quyền lợi, an toàn đối tượng.",
        "similarity": "Đều bắt buộc có phê duyệt đạo đức trước khi tuyển chọn và văn bản đồng thuận tham gia nghiên cứu (Informed Consent Form - ICF).",
        "difference": "FDA yêu cầu đăng ký IND khi áp dụng (hoặc tuân thủ 21 CFR 320 cho ANDA); EMA quản lý qua hệ thống CTIS (Clinical Trials Information System).",
        "mandatory_status": "Bắt buộc tuyệt đối (Mandatory)",
    },
    {
        "category": "Thiết kế nghiên cứu (Study Design)",
        "topic": "Thiết kế chuẩn cho dạng giải phóng tức thời (IR)",
        "fda_requirement": "Thiết kế crossover 2x2 đơn liều, ngẫu nhiên hóa; thường yêu cầu cả nghiên cứu lúc nhịn đói (Fasting) và sau ăn (Fed) cho hồ sơ ANDA trừ khi PSG có hướng dẫn riêng.",
        "ema_requirement": "Thiết kế crossover 2x2 đơn liều lúc nhịn đói (Fasting) là chuẩn mặc định; nghiên cứu sau ăn (Fed) chỉ bắt buộc nếu SmPC quy định uống cùng thức ăn hoặc có dạng bào chế đặc biệt.",
        "ich_harmonization": "ICH M13A (2024) hài hòa hóa thiết kế crossover 2x2 hoặc parallel; tối thiểu 12 đối tượng đánh giá được cho crossover, 12 đối tượng/nhánh cho parallel.",
        "similarity": "Đều coi thiết kế crossover 2x2, ngẫu nhiên hóa, đơn liều ở người khỏe mạnh là tiêu chuẩn vàng.",
        "difference": "FDA thường yêu cầu cả 2 nghiên cứu Fasting và Fed cho hầu hết thuốc generic đường uống; EMA thường chỉ yêu cầu Fasting đối với thuốc IR thông thường.",
        "mandatory_status": "Bắt buộc (Mandatory per Product Scope)",
    },
    {
        "category": "Thiết kế nghiên cứu (Study Design)",
        "topic": "Nghiên cứu lặp lại (Replicate designs) cho thuốc biến thiên cao (HVD)",
        "fda_requirement": "Khuyến nghị Full replicate 4 kỳ (TRTR/RTRT) hoặc Partial replicate 3 kỳ (TRR/RTR/RRT); áp dụng phân tích RSABE (Reference-Scaled Average Bioequivalence).",
        "ema_requirement": "Cho phép Full replicate 4 kỳ hoặc Partial replicate 3 kỳ; áp dụng phân tích ABEL (Average Bioequivalence with Expanding Limits) mở rộng giới hạn Cmax.",
        "ich_harmonization": "Đang được hài hòa hóa trong ICH M13B; hiện tại áp dụng quy định khu vực tương ứng của FDA hoặc EMA.",
        "similarity": "Đều yêu cầu lặp lại thuốc đối chứng (R) ít nhất 2 lần để ước tính độ biến thiên trong cá thể (sWR / CVwR).",
        "difference": "FDA dùng phương pháp RSABE (Howe's UCB <= 0); EMA dùng phương pháp ABEL (mở rộng biên dựa trên công thức exp(±0.760*sWR)).",
        "mandatory_status": "Áp dụng có điều kiện (Conditional on HVD classification)",
    },
    {
        "category": "Thiết kế nghiên cứu (Study Design)",
        "topic": "Thuốc có khoảng điều trị hẹp (Narrow Therapeutic Index - NTI)",
        "fda_requirement": "Bắt buộc thiết kế Full replicate 4 kỳ (TRTR/RTRT); áp dụng phương pháp RSABE đặc thù cho NTI và kiểm tra tỷ số độ biến thiên trong cá thể sWT/sWR (upper 90% CI <= 2.5).",
        "ema_requirement": "Thiết kế crossover 2x2 thông thường hoặc replicate; thu hẹp khoảng chấp nhận BE của AUC xuống [90.00% - 111.11%]; thu hẹp Cmax nếu có ý nghĩa lâm sàng.",
        "ich_harmonization": "Đang được hài hòa hóa trong ICH M13C; hiện tại tuân thủ nghiêm ngặt theo hướng dẫn riêng của từng khu vực.",
        "similarity": "Đều thắt chặt tiêu chí đánh giá so với giới hạn chuẩn 80.00% - 125.00%.",
        "difference": "FDA yêu cầu thiết kế 4 kỳ và đánh giá cả tỷ số phương sai sWT/sWR; EMA không bắt buộc thiết kế replicate mà tập trung vào khoảng tin cậy thu hẹp 90.00-111.11%.",
        "mandatory_status": "Áp dụng có điều kiện (Conditional on NTI classification)",
    },
    {
        "category": "Thông số Dược động học (PK Endpoints)",
        "topic": "Các thông số PK chính để đánh giá BE",
        "fda_requirement": "Cmax, AUC0-t và AUC0-inf (parent drug). Dưới hướng dẫn ICH M13A mới, Cmax và AUC0-t là thông số chính quyết định.",
        "ema_requirement": "Cmax và AUC0-t là thông số chính; AUC0-inf là thông số hỗ trợ (yêu cầu AUC0-t phải bao phủ ít nhất 80% của AUC0-inf). Cho phép cắt tại 72h (AUC0-72h) cho thuốc bán thải dài.",
        "ich_harmonization": "ICH M13A xác định Cmax và AUC0-t là primary endpoints; AUC0-72h được chấp nhận thay thế cho AUC0-t khi thuốc có t1/2 kéo dài và độ biến thiên thấp.",
        "similarity": "Cmax và AUC0-t (hoặc AUC0-72h) là hai thông số quyết định tương đương sinh học về tốc độ và mức độ hấp thu.",
        "difference": "FDA trước đây bắt buộc AUC0-inf phải đạt BE; EMA và ICH M13A coi AUC0-t là tiêu chí quyết định chính, AUC0-inf mang tính hỗ trợ kiểm tra độ hoàn chỉnh lấy mẫu.",
        "mandatory_status": "Bắt buộc (Mandatory)",
    },
    {
        "category": "Tiêu chuẩn chấp thuận Thống kê (Statistical Criteria)",
        "topic": "Phương pháp thống kê trung bình (Average Bioequivalence - ABE)",
        "fda_requirement": "Mô hình ANOVA / Mixed effects trên log tự nhiên; khoảng tin cậy 90% (TOST alpha=0.05) của GMR (T/R) phải nằm hoàn toàn trong [80.00%, 125.00%].",
        "ema_requirement": "Mô hình ANOVA trên log tự nhiên (Sequence, Period, Treatment, Subject(Sequence)); khoảng tin cậy 90% của GMR nằm hoàn toàn trong [80.00%, 125.00%].",
        "ich_harmonization": "ICH M13A hài hòa hóa tiêu chuẩn ABE: 90% CI cho tỷ số trung bình nhân (GMR) phải nằm trong khoảng 80.00% - 125.00%.",
        "similarity": "Hoàn toàn tương đồng về mô hình thống kê, biến đổi logarit tự nhiên, mức alpha 0.05 và khoảng chấp nhận [80.00%, 125.00%].",
        "difference": "Không có khác biệt đối với nghiên cứu ABE chuẩn 2x2.",
        "mandatory_status": "Bắt buộc (Mandatory for Standard BE)",
    },
    {
        "category": "Tiêu chuẩn chấp thuận Thống kê (Statistical Criteria)",
        "topic": "Mở rộng giới hạn cho thuốc biến thiên cao (HVD)",
        "fda_requirement": "RSABE: Khi sWR >= 0.294 (CVwR >= 30%), tiêu chí chuẩn hóa: (mu_T - mu_R)^2 - theta * sWR^2; Cận trên khoảng tin cậy 95% (Howe's UCB) <= 0 VÀ GMR điểm nằm trong [0.80, 1.25]. Có thể áp dụng cho cả AUC và Cmax.",
        "ema_requirement": "ABEL: Khi CVwR > 30%, chỉ mở rộng khoảng chấp thuận cho Cmax theo công thức [U, L] = exp(±0.760*sWR) đến tối đa [69.84%, 143.19%] (tại CVwR=50%); GMR điểm phải trong [80.00%, 125.00%]. AUC KHÔNG ĐƯỢC PHÉP MỞ RỘNG (giữ nguyên 80.00-125.00%).",
        "ich_harmonization": "Chưa hài hòa; hồ sơ nộp FDA phải dùng RSABE, hồ sơ nộp EMA phải dùng ABEL.",
        "similarity": "Đều yêu cầu chứng minh CVwR >= 30% và yêu cầu GMR điểm (point estimate) phải nằm trong khoảng 80.00% - 125.00%.",
        "difference": "Khác biệt lớn: EMA tuyệt đối không cho phép mở rộng giới hạn cho AUC; FDA cho phép RSABE cho cả AUC nếu thỏa mãn điều kiện sWR.",
        "mandatory_status": "Áp dụng riêng theo từng cơ quan quản lý (Agency-specific)",
    },
    {
        "category": "Phân tích sinh học (Bioanalysis)",
        "topic": "Thẩm định phương pháp & Phân tích mẫu nghiên cứu",
        "fda_requirement": "Tuân thủ ICH M10 (đã ban hành và áp dụng chính thức). LLOQ, tính chọn lọc, độ đúng/chính xác (<=15%, LLOQ <=20%), độ ổn định, hiệu ứng nền, ISR (Incurred Sample Reanalysis).",
        "ema_requirement": "Tuân thủ ICH M10 (thay thế EMA BMV guideline trước đây). Cùng yêu cầu về thẩm định và ISR.",
        "ich_harmonization": "ICH M10 đã hài hòa hóa toàn cầu các yêu cầu về thẩm định phương pháp phân tích mẫu sinh học và phân tích mẫu nghiên cứu lâm sàng.",
        "similarity": "Hoàn toàn thống nhất theo tiêu chuẩn ICH M10.",
        "difference": "Quy định lưu giữ mẫu đối chứng: FDA 21 CFR 320.38/320.63 yêu cầu lưu trữ mẫu lưu (reserve samples) độc lập trong 5 năm; EMA yêu cầu lưu giữ tối thiểu 1 năm sau ngày hết hạn của lô.",
        "mandatory_status": "Bắt buộc tuyệt đối (Mandatory per ICH M10)",
    },
    {
        "category": "Quản lý dữ liệu & Tính toàn vẹn (Data Integrity)",
        "topic": "Nguyên tắc ALCOA+, Dấu vết kiểm toán (Audit Trail) & Xử lý dữ liệu",
        "fda_requirement": "Tuân thủ 21 CFR Part 11 (Electronic Records & Electronic Signatures), hướng dẫn Data Integrity của FDA. Không được tự ý loại trừ dữ liệu (outliers) nếu không có căn cứ kỹ thuật/lâm sàng được xác định trước.",
        "ema_requirement": "Tuân thủ EU GMP Annex 11 (Computerised Systems), GCP guideline. Tất cả dữ liệu của mọi đối tượng được phân liều phải được báo cáo; phân tích độ nhạy nếu có ngoại lệ.",
        "ich_harmonization": "ICH E6(R3) và ICH E9(R1) nhấn mạnh tính minh bạch, lưu vết kiểm toán, xác định trước quần thể phân tích (Estimand framework).",
        "similarity": "Nghiêm cấm làm sai lệch dữ liệu, cấm tự ý xóa bỏ outlier; yêu cầu lưu trữ đầy đủ hồ sơ thô (raw data) và nhật ký audit trail.",
        "difference": "FDA kiểm tra nghiêm ngặt quy định lưu mẫu độc lập (reserve samples) tại cơ sở thử nghiệm lâm sàng.",
        "mandatory_status": "Bắt buộc tuyệt đối (Mandatory)",
    },
]


# ---------------------------------------------------------------------------
# Master Field Mapping Specification for Protocol and Report
# ---------------------------------------------------------------------------
DOCUMENT_FIELD_MAPPING: dict[str, dict[str, Any]] = {
    # 1. Administrative & Study Governance
    "study_id": {
        "field_name_vi": "Mã số nghiên cứu",
        "field_name_en": "Study Identifier",
        "category": "Hành chính & Quản lý",
        "source_type": "AUTO_POPULATED",
        "protocol_status": "Tự động điền từ Study.study_id",
        "report_status": "Tự động điền từ Study.study_id",
        "guidance": "Mã định danh duy nhất của nghiên cứu, nhất quán giữa đề cương, SAP và báo cáo.",
    },
    "title": {
        "field_name_vi": "Tên nghiên cứu",
        "field_name_en": "Study Title",
        "category": "Hành chính & Quản lý",
        "source_type": "AUTO_POPULATED",
        "protocol_status": "Tự động điền từ Study.title",
        "report_status": "Tự động điền từ Study.title",
        "guidance": "Tên khoa học đầy đủ nêu rõ hoạt chất, dạng bào chế, thiết kế, tình trạng ăn và mục tiêu BE.",
    },
    "protocol": {
        "field_name_vi": "Mã số và phiên bản đề cương",
        "field_name_en": "Protocol Identifier and Version",
        "category": "Hành chính & Quản lý",
        "source_type": "AUTO_POPULATED",
        "protocol_status": "Tự động điền từ Study.protocol; nếu trống: yêu cầu bổ sung",
        "report_status": "Tự động điền từ Study.protocol; đối chiếu với bản phê duyệt",
        "guidance": "Mã số đề cương và số hiệu phiên bản chính thức đã được Hội đồng Đạo đức phê duyệt.",
    },
    "sap": {
        "field_name_vi": "Mã số và phiên bản SAP",
        "field_name_en": "SAP Identifier and Version",
        "category": "Hành chính & Quản lý",
        "source_type": "AUTO_POPULATED",
        "protocol_status": "Tự động điền từ Study.sap; nếu trống: yêu cầu bổ sung",
        "report_status": "Tự động điền từ Study.sap; đối chiếu ngày ký khóa trước unblinding",
        "guidance": "Kế hoạch phân tích thống kê (SAP) phải được phê duyệt trước khi mở mù hoặc khóa cơ sở dữ liệu.",
    },
    "sponsor": {
        "field_name_vi": "Thông tin nhà tài trợ",
        "field_name_en": "Sponsor Information",
        "category": "Hành chính & Quản lý",
        "source_type": "AUTO_POPULATED",
        "protocol_status": "Tự động điền từ Study.sponsor; nếu trống: yêu cầu bổ sung",
        "report_status": "Tự động điền từ Study.sponsor; nếu trống: yêu cầu bổ sung",
        "guidance": "Tên công ty/tổ chức tài trợ, địa chỉ pháp lý, người đại diện liên hệ.",
    },
    "study_site": {
        "field_name_vi": "Cơ sở nghiên cứu lâm sàng",
        "field_name_en": "Clinical Study Site",
        "category": "Hành chính & Quản lý",
        "source_type": "AUTO_POPULATED",
        "protocol_status": "Tự động điền từ Study.study_site; nếu trống: yêu cầu bổ sung",
        "report_status": "Tự động điền từ Study.study_site; nếu trống: yêu cầu bổ sung",
        "guidance": "Tên đơn vị/bệnh viện thực hiện thử nghiệm lâm sàng, chứng nhận GCP của cơ sở.",
    },
    "principal_investigator": {
        "field_name_vi": "Nghiên cứu viên chính (PI)",
        "field_name_en": "Principal Investigator",
        "category": "Hành chính & Quản lý",
        "source_type": "AUTO_POPULATED",
        "protocol_status": "Tự động điền từ Study.principal_investigator; nếu trống: yêu cầu bổ sung",
        "report_status": "Tự động điền từ Study.principal_investigator; nếu trống: yêu cầu bổ sung",
        "guidance": "Họ tên, học vị, chuyên môn y khoa, chứng chỉ GCP và cơ quan công tác của PI.",
    },
    "approvals_signatures": {
        "field_name_vi": "Chữ ký và phê duyệt đề cương / báo cáo",
        "field_name_en": "Signatures and Approvals",
        "category": "Hành chính & Quản lý",
        "source_type": "MANUAL_REQUIRED",
        "protocol_status": "Mục giữ chỗ với chữ ký PI, Thống kê, Bioanalytical, Nhà tài trợ",
        "report_status": "Chữ ký chính thức của PI, Nhà tài trợ, QA Manager, Biostatistician",
        "guidance": "Bắt buộc ký tên và ghi rõ ngày tháng trước khi tiến hành nghiên cứu hoặc nộp hồ sơ.",
    },
    "irb_iec_approval": {
        "field_name_vi": "Số phê duyệt Hội đồng Đạo đức (IRB/IEC)",
        "field_name_en": "Ethics Committee Approval Details",
        "category": "Đạo đức & An toàn",
        "source_type": "MANUAL_REQUIRED",
        "protocol_status": "Yêu cầu người dùng bổ sung số quyết định và ngày họp phê duyệt",
        "report_status": "Bắt buộc bổ sung ngày, số phê duyệt và đính kèm công văn tại Phụ lục",
        "guidance": "Số văn bản chấp thuận của Hội đồng Đạo đức cơ sở hoặc quốc gia.",
    },

    # 2. Investigational Products
    "test_product_info": {
        "field_name_vi": "Thông tin thuốc thử (Test Product)",
        "field_name_en": "Test Product Details",
        "category": "Sản phẩm nghiên cứu",
        "source_type": "AUTO_POPULATED",
        "protocol_status": "Tự động điền: tên, hàm lượng, dạng bào chế, nhà sản xuất, số lô, hạn dùng",
        "report_status": "Tự động điền; người dùng bổ sung CoA, cỡ lô và hàm lượng định lượng thực tế",
        "guidance": "Lô sản xuất thuốc thử phải đại diện cho quy mô thương mại (>= 100.000 đơn vị hoặc 1/10 quy mô thương mại).",
    },
    "reference_product_info": {
        "field_name_vi": "Thông tin thuốc đối chứng (Reference Product)",
        "field_name_en": "Reference Product Details",
        "category": "Sản phẩm nghiên cứu",
        "source_type": "AUTO_POPULATED",
        "protocol_status": "Tự động điền: tên, hàm lượng, dạng bào chế, nhà sản xuất, số lô, hạn dùng",
        "report_status": "Tự động điền; người dùng bổ sung nước xuất xứ, số ĐKLH và CoA",
        "guidance": "Thuốc đối chứng phải là thuốc gốc (innovator/reference) được mua từ thị trường mục tiêu (US hoặc EU).",
    },
    "pharmaceutical_equivalence": {
        "field_name_vi": "Tương đương dược học và kiểm nghiệm so sánh",
        "field_name_en": "Pharmaceutical Equivalence and Potency Comparison",
        "category": "Sản phẩm nghiên cứu",
        "source_type": "MANUAL_REQUIRED",
        "protocol_status": "Nêu tiêu chí chênh lệch hàm lượng định lượng giữa T và R không quá 5%",
        "report_status": "Báo cáo kết quả kiểm nghiệm thực tế của T và R; xác nhận độ chênh lệch <= 5%",
        "guidance": "Hàm lượng hoạt chất đo được giữa T và R không được chênh lệch quá 5% theo khuyến cáo của FDA và EMA.",
    },
    "dissolution_comparison": {
        "field_name_vi": "Hòa tan so sánh in vitro",
        "field_name_en": "Comparative In Vitro Dissolution",
        "category": "Sản phẩm nghiên cứu",
        "source_type": "MANUAL_REQUIRED",
        "protocol_status": "Quy định điều kiện thử ở pH 1.2, 4.5, 6.8 và môi trường QC",
        "report_status": "Trình bày bảng đồ thị profile hòa tan và giá trị f2 (yêu cầu f2 >= 50)",
        "guidance": "Cần thiết để chứng minh tính tương đồng in vitro trước khi tiến hành in vivo.",
    },

    # 3. Clinical Study Conduct
    "study_design_type": {
        "field_name_vi": "Loại thiết kế nghiên cứu",
        "field_name_en": "Study Design Type",
        "category": "Thiết kế & Lâm sàng",
        "source_type": "AUTO_POPULATED",
        "protocol_status": "Tự động điền: 2x2 crossover, parallel, partial3 hoặc full4",
        "report_status": "Tự động điền thiết kế thực tế đã tiến hành",
        "guidance": "Lựa chọn căn cứ vào thời gian bán thải, biến thiên trong cá thể và khuyến cáo FDA/EMA.",
    },
    "fed_state": {
        "field_name_vi": "Điều kiện nghiên cứu (Đói / No)",
        "field_name_en": "Study Condition (Fasted / Fed)",
        "category": "Thiết kế & Lâm sàng",
        "source_type": "AUTO_POPULATED",
        "protocol_status": "Tự động điền: Fasted (nhịn đói) hoặc Fed (sau ăn)",
        "report_status": "Tự động điền; mô tả chi tiết bữa ăn chuẩn đã sử dụng",
        "guidance": "Bữa ăn giàu chất béo và calo theo chuẩn FDA/EMA (800-1000 kcal, ~50% chất béo).",
    },
    "washout_period": {
        "field_name_vi": "Thời gian washout giữa các kỳ",
        "field_name_en": "Washout Period",
        "category": "Thiết kế & Lâm sàng",
        "source_type": "MANUAL_REQUIRED",
        "protocol_status": "Tự động điền từ ghi chú protocol_details['washout']; nếu trống: yêu cầu bổ sung",
        "report_status": "Báo cáo thời gian washout thực tế giữa các kỳ phân liều",
        "guidance": "Tối thiểu >= 5 lần thời gian bán thải t1/2 để đảm bảo nồng độ trước liều kỳ 2 < 5% Cmax hoặc BLQ.",
    },
    "sampling_schedule": {
        "field_name_vi": "Lịch lấy mẫu máu nghiên cứu",
        "field_name_en": "Blood Sampling Schedule",
        "category": "Thiết kế & Lâm sàng",
        "source_type": "MANUAL_REQUIRED",
        "protocol_status": "Tự động điền từ ghi chú protocol_details['sampling']; nếu trống: yêu cầu bổ sung",
        "report_status": "Báo cáo các thời điểm danh định và sai lệch thời gian thực tế",
        "guidance": "Ít nhất 2-3 điểm trước Cmax, 3-4 điểm xung quanh Cmax, kéo dài ít nhất 72h hoặc 3-5 lần t1/2.",
    },
    "adverse_events_actual": {
        "field_name_vi": "Theo dõi an toàn và biến cố bất lợi (AE/SAE)",
        "field_name_en": "Safety and Adverse Events Reporting",
        "category": "Đạo đức & An toàn",
        "source_type": "MANUAL_REQUIRED",
        "protocol_status": "Kế hoạch theo dõi, phân loại CTCAE và quy trình cấp cứu",
        "report_status": "Bắt buộc bổ sung danh sách toàn bộ AE/SAE phát sinh trong nghiên cứu",
        "guidance": "Mô tả biến cố, mức độ, quan hệ nhân quả với thuốc thử/đối chứng, biện pháp xử trí.",
    },
    "protocol_deviations": {
        "field_name_vi": "Sai lệch đề cương nghiên cứu (Protocol Deviations)",
        "field_name_en": "Protocol Deviations and Violations",
        "category": "Đạo đức & An toàn",
        "source_type": "MANUAL_REQUIRED",
        "protocol_status": "Kế hoạch quản lý và phân loại sai lệch (major vs minor)",
        "report_status": "Bắt buộc liệt kê các sai lệch thực tế và đánh giá ảnh hưởng đến PK/BE",
        "guidance": "Phân loại sai lệch ảnh hưởng (major) và không ảnh hưởng (minor) đến phân tích thống kê.",
    },

    # 4. PK and Statistical Analysis
    "nca_parameters_computed": {
        "field_name_vi": "Các thông số Dược động học tính toán (NCA)",
        "field_name_en": "Noncompartmental PK Parameters",
        "category": "Dược động học & Thống kê",
        "source_type": "CALCULATED",
        "protocol_status": "Kế hoạch thuật toán tính Cmax, Tmax, AUC0-t, AUC0-inf, t1/2, lambda_z",
        "report_status": "Tự động xuất bảng số liệu cá thể và bảng thống kê mô tả (Mean, SD, CV, Median)",
        "guidance": "Tính theo phương pháp hình thang tuyến tính/logarit theo thời gian lấy mẫu thực tế.",
    },
    "sample_size_calculation": {
        "field_name_vi": "Tính toán cỡ mẫu và sức mạnh thống kê",
        "field_name_en": "Sample Size and Power Calculation",
        "category": "Dược động học & Thống kê",
        "source_type": "CALCULATED",
        "protocol_status": "Tự động liên kết từ valid_plan nếu có; nếu không có: yêu cầu bổ sung",
        "report_status": "Trình bày giả định ban đầu so với độ biến thiên CVw quan sát được",
        "guidance": "Đảm bảo sức mạnh thống kê (power) >= 80% hoặc 90% ở mức ý nghĩa alpha=0.05.",
    },
    "be_statistical_results": {
        "field_name_vi": "Kết quả phân tích thống kê BE (GMR, CI90, ANOVA)",
        "field_name_en": "Bioequivalence Statistical Results",
        "category": "Dược động học & Thống kê",
        "source_type": "CALCULATED",
        "protocol_status": "Quy định mô hình thống kê, biến đổi log và tiêu chí chấp nhận",
        "report_status": "Tự động xuất bảng kết quả: GMR, CI 90%, MSE, CVw, kết quả từng tiêu chí",
        "guidance": "Kết luận dựa trên việc toàn bộ khoảng tin cậy 90% nằm trong biên quy định.",
    },
    "swr_variability_metrics": {
        "field_name_vi": "Chỉ số biến thiên sWR và tiêu chí mở rộng (HVD/NTI)",
        "field_name_en": "Within-subject Variability and Scaling Metrics",
        "category": "Dược động học & Thống kê",
        "source_type": "CALCULATED",
        "protocol_status": "Xác định trước có áp dụng RSABE/ABEL/NTI hay không",
        "report_status": "Tự động xuất sWR, sWT, Howe UCB95, giới hạn mở rộng ABEL, CI tỷ số SD",
        "guidance": "Chỉ kích hoạt khi nghiên cứu replicate và thỏa mãn các điều kiện quy định.",
    },
    "data_hashes_traceability": {
        "field_name_vi": "Dấu vết tính toán và mã băm toàn vẹn dữ liệu",
        "field_name_en": "Calculation Traceability and Audit Hashes",
        "category": "Data Integrity & QC",
        "source_type": "AUTO_POPULATED",
        "protocol_status": "N/A (đề cương lập trước khi tính toán)",
        "report_status": "Tự động xuất analysis_run_id, dataset_hash, raw_hash, config_hash, snapshot_hash",
        "guidance": "Bảo đảm khả năng tái lập và truy xuất ngược nguồn gốc dữ liệu theo ALCOA+.",
    },
}
