"""Bilingual, evidence-aware ASEAN-style bioequivalence report outline.

This is a report *template*, not a clinical study report certification. Only
stored snapshot fields may be populated automatically; absent source documents
remain conspicuously marked for an independent author/reviewer.
"""

from __future__ import annotations

from typing import Any


def build_report_outline(
    study: dict, run: dict, manifest: dict, language: str, blockers_text: str = ""
) -> list[dict[str, Any]]:
    """Return numbered, hierarchical sections, preserving their source order."""
    vi = language == "vi"
    blank = "CHƯA CUNG CẤP — cần bổ sung hồ sơ gốc và xác minh." if vi else (
        "NOT PROVIDED — supply and verify the source records."
    )

    def field(key: str) -> str:
        value = study.get(key)
        if value is None or value == "" or value == []:
            return blank
        if isinstance(value, (list, tuple)):
            return ", ".join(str(x) for x in value) or blank
        return str(value)

    fed_state_vi = {"fasted": "Đói (nhịn ăn)", "fed": "No (sau ăn)"}.get(
        str(study.get("fed_state") or ""), blank
    )
    fed_state_en = {"fasted": "Fasted", "fed": "Fed"}.get(
        str(study.get("fed_state") or ""), blank
    )

    result_label = {
        "PASS": "ĐẠT tiêu chí thống kê" if vi else "STATISTICAL CRITERIA MET",
        "FAIL": "KHÔNG ĐẠT tiêu chí thống kê" if vi else "STATISTICAL CRITERIA NOT MET",
        "NOT EVALUABLE": "Không thể kết luận" if vi else "NOT EVALUABLE",
    }.get(str(run.get("study_decision")), "Chưa phân tích" if vi else "NOT ANALYZED")
    rule = str(study.get("rule_set_id") or ("Chưa chọn" if vi else "Not selected"))
    method = "Chưa chọn" if not study.get("rule_set_id") and vi else (
        "Not selected" if not study.get("rule_set_id") else "ABE"
    )
    if rule == "EMA_HVDP_ABEL":
        method = "EMA ABEL / HVDP"
    elif rule == "FDA_HVD_RSABE_2026":
        method = "FDA RSABE / HVD"
    elif rule == "EMA_NTI":
        method = "EMA NTI"
    elif rule == "FDA_NTI":
        method = "FDA NTI"
    elif "REPLICATE" in rule and "NONREPLICATE" not in rule:
        method = "Replicate ABE"

    sections: list[dict[str, Any]] = []

    def add(number: str, title_vi: str, title_en: str, body_vi: str = "", body_en: str = "") -> None:
        sections.append(
            {
                "number": number,
                "level": min(number.count(".") + 1, 3),
                "title": f"{number} {title_vi if vi else title_en}",
                "body": body_vi if vi else body_en,
            }
        )

    add("1", "TRANG BÌA VÀ THÔNG TIN QUẢN LÝ", "TITLE PAGE AND STUDY GOVERNANCE",
        "Báo cáo tương đương sinh học — bản dự thảo; cần kiểm tra đối chiếu với protocol, SAP, hồ sơ lâm sàng và phân tích.",
        "Bioequivalence report draft; reconcile with protocol, SAP, clinical and analytical source records.")
    add("1.1", "Tên nghiên cứu, mã số, phiên bản", "Study title, identifier and version",
        f"Tên: {field('title')}. Mã nghiên cứu: {field('study_id')}. Protocol: {field('protocol')}; SAP: {field('sap')}. Phiên bản báo cáo: {blank}.",
        f"Title: {field('title')}. Study ID: {field('study_id')}. Protocol: {field('protocol')}; SAP: {field('sap')}. Report version: {blank}.")
    governance_vi = {
        "1.2": f"Nhà tài trợ: {field('sponsor')}. Địa chỉ, người phụ trách, tài trợ và vai trò: {blank}",
        "1.3": f"Địa điểm thực hiện: {field('study_site')}. Hợp đồng, giấy phép và trách nhiệm: {blank}",
        "1.4": f"Nghiên cứu viên chính: {field('principal_investigator')}. Học vị, cơ quan, trách nhiệm: {blank}",
        "1.10": (
            f"Thời gian toàn nghiên cứu: {field('study_start_date')} đến {field('study_end_date')}; "
            f"lâm sàng: {field('clinical_start_date')} đến {field('clinical_end_date')}; "
            f"phân tích mẫu sinh học: {field('bioanalytical_start_date')} đến {field('bioanalytical_end_date')}; "
            f"khóa dữ liệu: {field('data_lock_date')}. "
            f"Bổ sung ngày phê duyệt, tuyển chọn, lấy mẫu và phê duyệt báo cáo: {blank}"
        ),
    }
    governance_en = {
        "1.2": f"Sponsor: {field('sponsor')}. Address, contact, funding and responsibilities: {blank}",
        "1.3": f"Study site: {field('study_site')}. Contracts, authorizations and responsibilities: {blank}",
        "1.4": f"Principal investigator: {field('principal_investigator')}. Qualifications and duties: {blank}",
        "1.10": (
            f"Overall study: {field('study_start_date')} to {field('study_end_date')}; "
            f"clinical: {field('clinical_start_date')} to {field('clinical_end_date')}; "
            f"bioanalysis: {field('bioanalytical_start_date')} to {field('bioanalytical_end_date')}; "
            f"data lock: {field('data_lock_date')}. "
            f"Supply approval, recruitment, sampling and report approval dates: {blank}"
        ),
    }
    for n, tv, te, prompt_vi, prompt_en in [
        ("1.2", "Nhà tài trợ và đầu mối liên hệ", "Sponsor and contact details", "Tên, địa chỉ, người phụ trách, tài trợ và vai trò", "Name, address, contact, funding and role"),
        ("1.3", "Cơ sở nghiên cứu", "Study institutions", "Địa điểm, đơn vị chủ trì, hợp đồng và giấy phép", "Sites, institutions, contracts and authorizations"),
        ("1.4", "Nghiên cứu viên chính", "Principal investigator", "Tên, học vị, cơ quan, trách nhiệm", "Name, qualifications, affiliation and responsibility"),
        ("1.5", "Nghiên cứu viên lâm sàng", "Clinical/medical investigators", "Danh sách nhân sự, chức năng, phân quyền", "Personnel, roles and delegation log"),
        ("1.6", "Phòng xét nghiệm lâm sàng", "Clinical laboratory", "Cơ sở, phương pháp, chứng nhận", "Facility, procedures and certifications"),
        ("1.7", "Phòng phân tích mẫu sinh học", "Bioanalytical laboratory", "Cơ sở, phương pháp và người phê duyệt", "Facility, method and approver"),
        ("1.8", "Quản lý dữ liệu, PK và thống kê", "Data management, PK and statistics", "Đơn vị, phần mềm, người thực hiện, người rà soát độc lập", "Organization, software, analyst and independent reviewer"),
        ("1.9", "Các đơn vị khác", "Other organizations", "Các bên thứ ba và trách nhiệm", "Third parties and responsibilities"),
        ("1.10", "Các mốc thời gian nghiên cứu", "Study chronology", "Ngày phê duyệt, tuyển chọn, dùng thuốc, lấy mẫu, khóa dữ liệu và báo cáo", "Approval, recruitment, dosing, sampling, lock and reporting dates"),
        ("1.11", "Chữ ký và phê duyệt", "Signatures and approvals", "Chữ ký PI, thống kê, QA, nhà tài trợ và ngày ký", "PI, statistician, QA and sponsor signatures and dates"),
    ]:
        add(n, tv, te,
            governance_vi.get(n, f"{prompt_vi}: {blank}"),
            governance_en.get(n, f"{prompt_en}: {blank}"))

    add("2", "TÓM TẮT NGHIÊN CỨU", "STUDY SYNOPSIS",
        f"Nghiên cứu: {field('title')}; hoạt chất: {field('active_ingredient')}; thiết kế: {field('design')}; "
        f"điều kiện: {fed_state_vi}; liều: {field('dose')} {field('dose_unit')}; "
        f"T: {field('test_product')}; R: {field('reference_product')}; "
        f"quy tắc: {rule}; phân tích: {method}; endpoint chính: {field('primary_endpoints')}. "
        f"Kết quả snapshot: {result_label}. Các quyết định cấp nghiên cứu cần đủ hồ sơ và phê duyệt độc lập.",
        f"Recorded study title: {field('title')}; substance: {field('active_ingredient')}; design: {field('design')}; "
        f"condition: {fed_state_en}; dose: {field('dose')} {field('dose_unit')}; "
        f"T: {field('test_product')}; R: {field('reference_product')}; "
        f"rule: {rule}; method: {method}; primary endpoints: {field('primary_endpoints')}. "
        f"Snapshot result: {result_label}. Study-level claims require supporting records and independent approval.")
    add("3", "MỤC LỤC", "TABLE OF CONTENTS",
        "Danh sách mục 1–11 và các đề mục cấp hai được trình bày bên dưới. Kiểm tra số trang sau khi hoàn thiện báo cáo.",
        "Sections 1–11 and their subsections are listed below. Update page numbering after finalization.")
    add("4", "CHỮ VIẾT TẮT VÀ THUẬT NGỮ", "ABBREVIATIONS AND DEFINITIONS",
        "ABE: tương đương sinh học trung bình; ABEL: ABE với giới hạn mở rộng theo độ biến thiên; RSABE: BE được chuẩn hóa theo độ biến thiên tham chiếu; HVD/HVDP: thuốc có biến thiên trong cá thể cao; NTI: khoảng điều trị hẹp; "
        "AUC: diện tích dưới đường cong; Cmax: nồng độ đỉnh; Tmax: thời gian đạt đỉnh; t½: thời gian bán thải; λz: hằng số thải trừ pha cuối; "
        "GMR: tỷ số trung bình nhân; CI90: khoảng tin cậy 90%; TOST: hai kiểm định một phía; CVwR: biến thiên trong cá thể của tham chiếu; sWR/sWT: độ lệch chuẩn trong cá thể trên thang log; "
        "BLQ: dưới giới hạn định lượng; LLOQ: giới hạn định lượng dưới; PK: dược động học; NCA: phân tích phi ngăn; SAP: kế hoạch phân tích thống kê; "
        "ALCOA+: attributable, legible, contemporaneous, original, accurate, complete, consistent, enduring, available; audit trail: nhật ký truy vết thay đổi.",
        "ABE: average bioequivalence; ABEL: average BE with expanded limits; RSABE: reference-scaled ABE; HVD/HVDP: highly variable drug/product; NTI: narrow therapeutic index; "
        "AUC: area under the curve; Cmax: peak concentration; Tmax: time of peak; t½: elimination half-life; λz: terminal rate constant; "
        "GMR: geometric mean ratio; CI90: 90% confidence interval; TOST: two one-sided tests; CVwR: within-subject reference CV; sWR/sWT: within-subject log SD; "
        "BLQ: below limit of quantification; LLOQ: lower limit of quantification; PK: pharmacokinetics; NCA: noncompartmental analysis; SAP: statistical analysis plan; "
        "ALCOA+: attributable, legible, contemporaneous, original, accurate, complete, consistent, enduring, available; audit trail: change history.")

    add("5", "GIỚI THIỆU VÀ CƠ SỞ KHOA HỌC", "INTRODUCTION AND SCIENTIFIC BACKGROUND")
    add("5.1", "Dược lý, cơ chế tác dụng, chỉ định", "Pharmacology, mechanism and indication",
        f"Hoạt chất: {field('active_ingredient')}. Bổ sung cơ chế tác dụng, chỉ định, đường dùng, đặc điểm hấp thu và tài liệu sản phẩm: {blank}",
        f"Active ingredient: {field('active_ingredient')}. Supply mechanism, indication, route, absorption characteristics and product references: {blank}")
    add("5.2", "Dược động học và lựa chọn endpoint", "Pharmacokinetics and endpoint rationale",
        f"Endpoint chính: {field('primary_endpoints')}; endpoint phụ: {field('secondary_endpoints')}. "
        "Giải thích tính phù hợp của AUC/Cmax, thời gian lấy mẫu, λz, AUC ngoại suy, thức ăn và chất chuyển hóa: " + blank,
        f"Primary: {field('primary_endpoints')}; secondary: {field('secondary_endpoints')}. "
        "Explain AUC/Cmax, sampling interval, λz, extrapolation, food effect and metabolite strategy: " + blank)
    add("5.3", "An toàn và phản ứng bất lợi đã biết", "Known safety and adverse reactions",
        f"Đặc điểm an toàn, chống chỉ định, theo dõi lâm sàng và kế hoạch cứu hộ: {blank}",
        f"Safety profile, contraindications, monitoring and rescue measures: {blank}")

    add("6", "MỤC TIÊU VÀ GIẢ THUYẾT", "OBJECTIVES AND HYPOTHESES",
        f"Đánh giá BE của T so với R theo {method} trong thiết kế {field('design')}. Xác định trước endpoint chính, "
        "mức alpha, tiêu chí chấp nhận theo từng endpoint, tính hợp lệ của thiết kế và các phân tích nhạy cảm; đối chiếu SAP: " + field("sap") + ".",
        f"Assess T versus R under {method} with {field('design')} design. Prespecify primary endpoints, "
        "alpha, endpoint-specific bounds, design eligibility and sensitivity analyses; reconcile with SAP: " + field("sap") + ".")

    add("7", "THÔNG TIN SẢN PHẨM NGHIÊN CỨU", "INVESTIGATIONAL PRODUCT INFORMATION")
    add("7.1", "Thuốc thử T", "Test product T",
        f"Tên thuốc thử: {field('test_product')}; hoạt chất: {field('active_ingredient')}; "
        f"hàm lượng: {field('test_strength')}; nồng độ (nếu áp dụng): {field('test_concentration')}; "
        f"dạng bào chế: {field('test_dosage_form')}; loại giải phóng: {field('formulation')}; "
        f"nhà sản xuất: {field('test_manufacturer')}; số lô sản xuất: {field('test_batch')}; "
        f"hạn dùng: {field('test_expiry_date')}; liều sử dụng: {field('dose')} {field('dose_unit')}. "
        f"Bổ sung cỡ lô, thành phần, tiêu chuẩn thành phẩm và CoA: {blank}",
        f"Test product: {field('test_product')}; active ingredient: {field('active_ingredient')}; "
        f"strength: {field('test_strength')}; concentration (if applicable): {field('test_concentration')}; "
        f"dosage form: {field('test_dosage_form')}; release type: {field('formulation')}; "
        f"manufacturer: {field('test_manufacturer')}; batch number: {field('test_batch')}; "
        f"expiry date: {field('test_expiry_date')}; administered dose: {field('dose')} {field('dose_unit')}. "
        f"Add batch size, composition, specifications and CoA: {blank}")
    add("7.2", "Thuốc đối chứng R", "Reference product R",
        f"Tên thuốc đối chứng: {field('reference_product')}; hoạt chất: {field('active_ingredient')}; "
        f"hàm lượng: {field('reference_strength')}; nồng độ (nếu áp dụng): {field('reference_concentration')}; "
        f"dạng bào chế: {field('reference_dosage_form')}; nhà sản xuất: {field('reference_manufacturer')}; "
        f"số lô sản xuất: {field('reference_batch')}; hạn dùng: {field('reference_expiry_date')}. "
        f"Bổ sung nước xuất xứ, đơn vị đăng ký/nhập khẩu và nhãn gốc: {blank}",
        f"Reference product: {field('reference_product')}; active ingredient: {field('active_ingredient')}; "
        f"strength: {field('reference_strength')}; concentration (if applicable): {field('reference_concentration')}; "
        f"dosage form: {field('reference_dosage_form')}; manufacturer: {field('reference_manufacturer')}; "
        f"batch number: {field('reference_batch')}; expiry date: {field('reference_expiry_date')}. "
        f"Add country of origin, authorization holder/importer and original label: {blank}")
    add("7.3", "Tương đương dược học và kiểm nghiệm", "Pharmaceutical equivalence and testing",
        f"Đối chiếu định tính/định lượng, độ đồng đều hàm lượng, assay, tạp chất và quy chuẩn kiểm nghiệm: {blank}",
        f"Compare identification, content uniformity, assay, impurities and release specifications: {blank}")
    add("7.4", "So sánh hòa tan", "Comparative dissolution",
        f"Điều kiện thử, môi trường, thời gian, profile, thống kê f2/nếu áp dụng và hồ sơ nhiều hàm lượng: {blank}",
        f"Media, apparatus, sampling, profiles, f2 where applicable and strength proportionality: {blank}")
    add("7.5", "Cam kết của nhà tài trợ", "Sponsor declaration",
        f"Xác nhận về lô, hàm lượng, điều kiện bảo quản, truy xuất thuốc và chữ ký có thẩm quyền: {blank}",
        f"Batch, potency, storage, product accountability and authorized signature: {blank}")

    add("8", "KẾ HOẠCH NGHIÊN CỨU VÀ PHƯƠNG PHÁP", "INVESTIGATIONAL PLAN AND METHODS")
    add("8.1", "Thiết kế lâm sàng", "Clinical study design",
        f"Thiết kế: {field('design')}; tình trạng ăn: {fed_state_vi}; đơn liều: {field('single_dose')}; "
        f"đường dùng: {field('route')}. Nêu lý do chọn crossover/parallel/replicate; tiêu chí chọn/loại, "
        f"thời gian washout, điều kiện kiểm soát, thời điểm lấy mẫu, tổng thể tích máu: {blank}",
        f"Design: {field('design')}; fed state: {fed_state_en}; single-dose: {field('single_dose')}; "
        f"route: {field('route')}. Justify crossover/parallel/replicate; eligibility, washout, controlled conditions, "
        f"sampling schedule and total blood volume: {blank}")
    add("8.1.1", "Tuyển chọn, phân nhóm và quần thể", "Screening, randomization and populations",
        f"Trình bày flow tuyển chọn, danh sách người tham gia, sequence, các kỳ đã hoàn tất, mất theo dõi, "
        f"xử lý mẫu thiếu và quần thể phân tích theo SAP: {blank}",
        f"Report participant flow, allocation, sequences, completed periods, dropouts, missing observations "
        f"and prespecified analysis population: {blank}")
    add("8.1.2", "Lấy, xử lý và bảo quản mẫu", "Sample collection, handling and storage",
        f"Thời gian danh định/thực tế, ma trận mẫu, chống đông, phân ly, nhiệt độ, thời gian giữ mẫu, "
        f"chuỗi bàn giao và sai lệch lấy mẫu: {blank}",
        f"Nominal/actual times, sample matrix, anticoagulant, centrifugation, storage temperatures, "
        f"hold times, chain of custody and deviations: {blank}")
    add("8.2", "Thuốc dùng và quy trình can thiệp", "Treatments and interventions",
        f"T: {field('test_product')} ({field('test_batch')}); R: {field('reference_product')} "
        f"({field('reference_batch')}); liều: {field('dose')} {field('dose_unit')}; "
        f"điều kiện: {fed_state_vi}. "
        f"Bảng randomization, số viên, lượng nước, thời điểm dùng, ăn/uống, che mù và washout: {blank}",
        f"T: {field('test_product')} ({field('test_batch')}); R: {field('reference_product')} "
        f"({field('reference_batch')}); dose: {field('dose')} {field('dose_unit')}; "
        f"condition: {fed_state_en}. "
        f"Randomization, units, water volume, timing, meals, blinding and washout: {blank}")
    add("8.3", "Theo dõi lâm sàng và an toàn", "Clinical and safety monitoring",
        f"Lịch khám, sinh hiệu, xét nghiệm, ECG nếu phù hợp; mã hóa và phân loại AE/SAE/ADR, "
        f"quan hệ nhân quả, mức độ nghiêm trọng, thuốc dùng kèm và xử trí: {blank}",
        f"Examinations, vitals, laboratory tests, ECG where applicable; AE/SAE/ADR coding, "
        f"causality, seriousness, concomitant medication and management: {blank}")
    add("8.4", "Phương pháp PK/NCA", "PK/NCA methods",
        "Dùng thời gian lấy mẫu thực tế và dữ liệu nồng độ của snapshot. "
        "Đối chiếu cấu hình NCA, phần mềm và thuật toán với SAP và hồ sơ phương pháp. "
        "Định nghĩa Cmax/Tmax, AUC0–t, AUC0–∞, λz, t½, %AUC ngoại suy và quy tắc BLQ; rà soát thủ công pha cuối cần audit trail.",
        "Use actual sampling times and snapshot concentrations. Reconcile NCA settings, software "
        "and algorithms with the SAP and methods records. "
        "Define Cmax/Tmax, AUC0–t, AUC0–∞, λz, t½, %AUC extrapolated and BLQ handling; audited terminal-phase overrides need review.")
    add("8.5", "Kế hoạch phân tích thống kê", "Statistical analysis plan",
        f"Rule {rule}; SAP: {field('sap')}; endpoint chính: {field('primary_endpoints')}. "
        "Log tự nhiên các PK endpoint dương, mô hình có hiệu ứng thiết kế phù hợp, GMR(T/R), CI90, "
        "alpha một phía 0,05, sai số và bậc tự do, xử lý missing và phân tích độ nhạy. "
        "Giới hạn BE được quyết định theo endpoint và profile, phải thống nhất SAP trước khi khóa dữ liệu.",
        f"Rule {rule}; SAP: {field('sap')}; primary endpoints: {field('primary_endpoints')}. "
        "Natural-log positive PK endpoints, design-appropriate model, T/R GMR, 90% CI, "
        "one-sided alpha 0.05, residual variability/DF, missingness and sensitivity analyses. "
        "Endpoint/profile-specific criteria must be prespecified in the SAP.")
    add("8.5.1", "ABE tiêu chuẩn và TOST", "Conventional ABE and TOST",
        "Với 2×2 hoặc parallel đủ điều kiện, yêu cầu toàn bộ CI90 của GMR cho AUC và Cmax trong [0,80; 1,25] "
        "trừ khi profile hợp lệ quy định khác; biểu diễn bằng tỷ lệ trên thang gốc. "
        "ANOVA/mixed model, sequence, period, treatment và subject(sequence) tùy thiết kế; "
        "không suy luận BE từ riêng p-value khác biệt.",
        "For eligible 2×2/parallel studies, the entire 90% CI of AUC/Cmax GMR must fall within "
        "[0.80, 1.25] unless an applicable rule specifies otherwise. Use ratios on the original scale, "
        "design-appropriate ANOVA/mixed effects and TOST, not difference-test p-values alone.")
    if rule == "EMA_HVDP_ABEL":
        add("8.5.2", "EMA HVDP: ABEL", "EMA HVDP: ABEL",
            "Chỉ áp dụng mở rộng cho Cmax khi thiết kế replicate, độ biến thiên trong cá thể của R được ước tính hợp lệ, "
            "CVwR > 30%, phương pháp đã định trước và có lý giải lâm sàng. Giới hạn mở rộng dựa trên sWR, "
            "có trần 69,84–143,19% cho Cmax, đồng thời GMR nằm trong 80–125%; AUC giữ tiêu chí thông thường. "
            f"Scaling prespecified: {field('scaled_be_prespecified')}; cơ sở HVD: {field('hvd_justification')}. "
            "Rà soát outlier và độ tin cậy sWR; đọc từng tiêu chí trong bảng reviewer.",
            "Expansion applies to Cmax only when replicate reference variability is valid, CVwR >30%, "
            "prespecified and clinically justified. Limits use sWR capped at 69.84–143.19% for Cmax; "
            "GMR must also remain 80–125%, while AUC retains standard limits. "
            f"Prespecified: {field('scaled_be_prespecified')}; justification: {field('hvd_justification')}. "
            "Review outliers, sWR reliability and criterion-level output.")
    elif rule == "FDA_HVD_RSABE_2026":
        add("8.5.2", "FDA HVD: RSABE", "FDA HVD: RSABE",
            "Thiết kế replicate cho phép ước tính sWR. Với sWR ≥ 0,294 và điều kiện profile phù hợp, "
            "quyết định RSABE dùng cận trên khoảng tin cậy 95% cho tiêu chí scaling (Howe) ≤ 0, "
            "và GMR phải trong [0,80;1,25]; CI90 có thể được trình bày để tham khảo nhưng không thay UCB. "
            "Với sWR < 0,294, cần conventional replicate ABE đủ qualification; nhánh này hiện không đủ điều kiện "
            "kết luận, phải ghi NOT EVALUABLE. Cần ghi lại lý do HVD và dữ liệu replicate.",
            "Replicate design estimates sWR. When sWR ≥0.294 and other profile gates hold, RSABE uses "
            "the 95% upper confidence bound of the scaled criterion (Howe) ≤0 and GMR within [0.80,1.25]; "
            "the displayed 90% CI is supplementary, not the decision test. When sWR <0.294, "
            "conventional replicate ABE would be required but is not qualified here, hence NOT EVALUABLE. "
            "Document HVD justification and replicate observations.")
    elif rule == "EMA_NTI":
        add("8.5.2", "EMA NTI: giới hạn thu hẹp", "EMA NTI: narrowed limits",
            "Với AUC, áp dụng CI90 của GMR trong [0,90;1,1111]. Cmax có thể dùng [0,80;1,25] "
            "hoặc thu hẹp nếu có cơ sở an toàn/hiệu quả được quy định; không tự động mở rộng giới hạn cho NTI. "
            f"Cờ yêu cầu thu hẹp Cmax: {field('nti_cmax_narrow')}. "
            "Căn cứ phân loại NTI, protocol/SAP và guideline sản phẩm cần được lưu hồ sơ.",
            "AUC GMR 90% CI must fall in [0.90,1.1111]. Cmax may use [0.80,1.25] "
            "or narrower limits if specifically required by clinical/regulatory evidence; never scale NTI bounds wider. "
            f"Cmax narrowing flag: {field('nti_cmax_narrow')}. "
            "NTI justification, protocol/SAP and product-specific guidance must be documented.")
    elif rule == "FDA_NTI":
        add("8.5.2", "FDA NTI: tiêu chí replicate đặc thù", "FDA NTI: replicate criteria",
            "Thiết kế full replicate; hồ sơ phải báo cáo GMR, giới hạn/tiêu chí scaled và conventional theo "
            "khuyến cáo FDA, so sánh phương sai T/R (sWT/sWR) và khoảng tin cậy tỷ số SD. "
            "Nhánh conventional replicate ABE chưa được đối chiếu độc lập trong ứng dụng: "
            "trạng thái NOT EVALUABLE (không thể kết luận); không được chuyển thành kết luận đạt, "
            "kể cả khi thành phần tính toán khác hiện số liệu. "
            "Báo cáo rõ từng tiêu chí chưa đủ điều kiện và yêu cầu kiểm chứng bên ngoài.",
            "Full replicate design; report GMR, FDA scaled and conventional criteria, T/R within-subject "
            "variation (sWT/sWR) and SD ratio confidence interval. Conventional replicate ABE "
            "has not been independently qualified here; do not release a pass even if other components compute. "
            "Show unresolved gates and required external verification.")
    elif "REPLICATE" in rule and "NONREPLICATE" not in rule:
        add("8.5.2", "ABE với thiết kế replicate", "Conventional replicate ABE",
            "Phân biệt số người với số lần dùng thuốc; ước lượng hiệu ứng điều trị và phương sai theo "
            "mô hình phù hợp. Với FDA replicate ABE, nhánh conventional mixed chưa qualified trong ứng dụng; "
            "phải giữ NOT EVALUABLE. Không dùng CI theo tương phản đơn giản thay CI BE đã xác nhận.",
            "Separate participants from dosing observations; use an appropriate replicate model. "
            "FDA conventional mixed replicate ABE remains unqualified in this app: NOT EVALUABLE. "
            "Do not substitute an unqualified contrast CI for a validated BE CI.")
    if not study.get("rule_set_id"):
        # A standalone, editable template must describe every supported study
        # profile before the author has selected the applicable rule.
        for number, case_rule in enumerate(
            ("EMA_HVDP_ABEL", "FDA_HVD_RSABE_2026", "EMA_NTI", "FDA_NTI", "FDA_REPLICATE_STANDARD"),
            start=2,
        ):
            variant = build_report_outline({**study, "rule_set_id": case_rule}, run, manifest, language)
            case = next(item for item in variant if item["number"] == "8.5.2")
            section_number = f"8.5.{number}"
            sections.append({
                "number": section_number,
                "level": 3,
                "title": f"{section_number} {case['title'].split(' ', 1)[1]}",
                "body": case["body"],
            })
    sample_number = (
        "8.5.7" if not study.get("rule_set_id") else
        "8.5.3" if any(section["number"] == "8.5.2" for section in sections) else "8.5.2"
    )
    add(sample_number,
        "Cỡ mẫu, độ mạnh và dữ liệu thiếu", "Sample size, power and missingness",
        f"Giả định GMR, CV, dropout, alpha, power mục tiêu và phương pháp ước tính: {blank}. "
        "Power quan sát được không thay cho chứng cứ BE. Phân biệt dữ liệu thiếu thật với dữ liệu bị loại theo SAP; "
        "trình bày số người, số quan sát và độ nhạy theo từng endpoint.",
        f"Prespecified GMR, CV, dropout, alpha, target power and method: {blank}. "
        "Observed power cannot establish BE. Distinguish missing from excluded data and document "
        "participant/observation counts and endpoint-wise sensitivity analyses.")
    add("8.6", "Phương pháp phân tích mẫu và thẩm định", "Bioanalytical method and validation",
        f"LLOQ, tính đặc hiệu, đường chuẩn, chính xác, đúng, độ thu hồi, carryover, "
        f"matrix effect, ổn định và incurred sample reanalysis: {blank}. "
        "Truy xuất SOP, thiết bị, lô hóa chất và mẫu QC; kết quả NCA không thay thế thẩm định assay.",
        f"LLOQ, selectivity, calibration, accuracy, precision, recovery, carryover, matrix effect, "
        f"stability and incurred sample reanalysis: {blank}. "
        "Trace SOPs, equipment, reagents and QCs; NCA output does not replace assay validation.")
    add("8.7", "Đảm bảo chất lượng và Data Integrity", "Quality assurance and data integrity",
        f"Nguồn dữ liệu: {field('data_provenance')}; mục đích: {field('data_purpose')}; "
        f"revision: {manifest.get('input_revision', '—')}; fingerprint: {manifest.get('input_fingerprint', '—')}. "
        "Rà soát ALCOA+, quyền truy cập, thay đổi dữ liệu, protocol/SAP version, audit trail, đối chiếu dữ liệu gốc, "
        "freeze/lock, deviations, CAPA và quy trình reviewer sign-off. "
        f"Chứng cứ QA/CSV/phân quyền/chữ ký điện tử: {blank}",
        f"Data source: {field('data_provenance')}; purpose: {field('data_purpose')}; "
        f"revision: {manifest.get('input_revision', '—')}; fingerprint: {manifest.get('input_fingerprint', '—')}. "
        "Review ALCOA+, access, amendments, protocol/SAP versioning, audit trail, raw-data reconciliation, "
        "lock, deviations, CAPA and sign-off. "
        f"QA, computerized-system validation, access control and e-signature evidence: {blank}")

    add("9", "KẾT QUẢ VÀ BÀN LUẬN", "RESULTS AND DISCUSSION")
    add("9.1", "Đặc điểm người tham gia và kết quả lâm sàng", "Demographics and clinical conduct",
        f"Số liệu tuổi, giới, BMI, tuyển chọn, hoàn thành, thời gian dùng thuốc/lấy mẫu thực tế, "
        f"protocol deviations, thuốc dùng kèm, AE/SAE/ADR và an toàn: {blank}. "
        "Số người và kỳ phân tích thực tế xuất từ snapshot trong bảng phụ trợ phía dưới.",
        f"Age, sex, BMI, disposition, dosing/actual sampling times, deviations, concomitant "
        f"medications, AE/SAE/ADR and safety: {blank}. "
        "Actual analysis population counts appear in the snapshot review tables below.")
    add("9.2", "Kết quả định lượng mẫu sinh học", "Bioanalytical results",
        f"Tỷ lệ BLQ, mẫu kiểm tra lại, độ phù hợp QC/đường chuẩn, sai lệch bảo quản, độ ổn định, "
        f"chromatogram minh họa và quyết định chấp nhận batch: {blank}. "
        "Bảng nồng độ gốc/đã xác thực và chứng cứ xử lý cần đính kèm.",
        f"BLQ fraction, repeat samples, QC/calibration acceptance, storage deviations, "
        f"stability, representative chromatograms and run acceptance: {blank}. "
        "Attach raw and validated concentration listings and processing evidence.")
    add("9.3", "Kết quả PK cá thể và mô tả", "Individual and descriptive PK results",
        "Trình bày Cmax, Tmax, AUC0–t, AUC0–∞, λz, t½ và %AUC ngoại suy theo người/kỳ/điều trị; "
        "trung bình, SD, CV, trung vị, min–max, trung bình nhân và CI thích hợp. "
        "Đính kèm đồ thị nồng độ–thời gian trung bình và từng người ở thang thường và log, "
        "nhận xét mẫu bất thường và mọi lần điều chỉnh pha cuối.",
        "Report Cmax, Tmax, AUC0–t, AUC0–∞, λz, t½ and extrapolated AUC by participant/period/treatment; "
        "arithmetic/geometric summaries and suitable CI. Include mean and individual concentration–time "
        "plots (linear and log scales), outlier review and all terminal-slope changes.")
    add("9.4", "Kết quả thống kê tương đương sinh học", "Bioequivalence statistical results",
        f"Phương pháp: {method}; kết luận snapshot: {result_label}. "
        "Bảng tiếp theo gồm GMR, CI90, quyết định theo endpoint, tiêu chí scaling/variability, "
        "population, PK mô tả và từng bản ghi theo kỳ. Khi NOT EVALUABLE, không chuyển phần số học "
        "thành khẳng định BE. Phân tích độ nhạy và sai lệch protocol cần bổ sung khi có hồ sơ.",
        f"Method: {method}; snapshot decision: {result_label}. "
        "The next tables cover GMR, 90% CI, endpoint decisions, scaling/variability criteria, "
        "populations, descriptive PK and period listings. NOT EVALUABLE must not become a BE claim. "
        "Add sensitivity/deviation analyses when source records become available.")
    add("9.4.1", "Bảng kết quả từ snapshot đã khóa", "Locked-snapshot result tables",
        "Các bảng được sinh tự động theo analysis_run_id và hash; tiêu đề, đơn vị, số người, "
        "nhiều kỳ và tiêu chí độc lập phải được kiểm tra trước phê duyệt.",
        "Tables are generated from the analysis_run_id and hashes; verify headers, units, "
        "participants, replicate observations and all individual gates before approval.")
    add("9.5", "Diễn giải, độ nhạy và giới hạn", "Interpretation, sensitivity and limitations",
        "Phân biệt ý nghĩa thống kê với ý nghĩa lâm sàng. Thảo luận khác biệt T/R, biến thiên trong cá thể, "
        "khả năng ngoại suy, mẫu BLQ, outlier, dữ liệu thiếu, assumption của mô hình, "
        "độ nhạy với lựa chọn pha cuối và giới hạn khả năng khái quát hóa. Không tự động loại outlier.",
        "Distinguish statistical and clinical meaning. Discuss T/R difference, within-subject "
        "variability, extrapolation, BLQ, outliers, missingness, model assumptions, terminal-phase "
        "sensitivity and generalizability. Never exclude outliers automatically.")

    add("10", "KẾT LUẬN VÀ KHUYẾN NGHỊ", "CONCLUSION AND RECOMMENDATIONS",
        f"Kết quả theo snapshot: {result_label}. Review status: {run.get('review_status', 'unknown')}. "
        "Nghiên cứu mô phỏng/đào tạo hoặc thiếu hồ sơ không thể dùng để khẳng định BE cấp nghiên cứu; "
        "cần kết luận riêng cho từng endpoint bắt buộc, sau khi hoàn tất QA, PK, thống kê và regulatory review. "
        "Báo cáo này là bản nháp, chưa chứng nhận CSR/eCTD.",
        f"Snapshot result: {result_label}. Review status: {run.get('review_status', 'unknown')}. "
        "Synthetic/training data or incomplete source records cannot establish real-study BE. "
        "Required endpoints need individual decisions after QA, PK, statistical and regulatory review. "
        "This draft is not a qualified CSR/eCTD submission.")
    add("10.1", "Các điều kiện chặn và công việc còn thiếu", "Blocking conditions and outstanding work",
        (blockers_text or "Không có blocker được lưu; vẫn phải rà soát độc lập.") +
        f" Bằng chứng xác nhận clinical/assay/QA/chữ ký: {blank}",
        (blockers_text or "No stored blockers; independent review still required.") +
        f" Clinical/assay/QA/signature confirmation: {blank}")

    add("11", "PHỤ LỤC, TRUY XUẤT VÀ TÀI LIỆU THAM KHẢO", "APPENDICES, TRACEABILITY AND REFERENCES")
    for n, tv, te, bv, be in [
        ("11.1", "Protocol, SAP, phê duyệt và hồ sơ lâm sàng", "Protocol, SAP, approvals and clinical records",
         "Protocol và sửa đổi, SAP ký/khóa, ethics, consent, CRF, tuyển chọn, deviations, AE/SAE, chứng từ cấp phát thuốc, CoA", "Signed protocol/amendments, SAP, ethics, consent, CRF, disposition, deviations, AEs/SAEs, drug accountability and CoA"),
        ("11.2", "Thẩm định bioanalytical và chromatogram", "Bioanalytical validation and chromatograms",
         "Validation report, SOP, mẫu QC, đường chuẩn, chromatogram đại diện, ổn định, ISR", "Validation report, SOPs, QCs, calibration, representative chromatograms, stability and ISR"),
        ("11.3", "Báo cáo phân tích và dữ liệu gốc", "Analytical report and raw data",
         "Sổ tay chạy mẫu, dữ liệu nồng độ có đơn vị/LLOQ/BLQ, bất thường, raw/validated/analysis datasets, audit trail", "Assay batch reports, concentrations and units/LLOQ/BLQ, exceptions, raw/validated/analysis datasets and audit trail"),
        ("11.4", "Chứng nhận cơ sở và kiểm soát chất lượng", "Facility and quality certificates",
         "GCP/GLP/GMP nếu áp dụng, hồ sơ năng lực cơ sở, kiểm định/hiệu chuẩn, QA và CSV", "Applicable GCP/GLP/GMP, facility qualifications, calibration, QA and computerized-system validation"),
        ("11.5", "Hòa tan và liên quan các hàm lượng", "Dissolution and strength proportionality",
         "Hồ sơ nhiều hàm lượng, công thức, phép thử dissolution/f2 và đánh giá biowaiver nếu áp dụng", "Multiple strengths, formulations, dissolution/f2 and biowaiver justification if applicable"),
        ("11.6", "Dữ liệu PK, bảng ANOVA và đồ thị", "PK listings, model tables and plots",
         "Bảng PK cá thể, trung bình theo xử lý, đồ thị tuyến tính/log, diagnostics, LS means, SE, df, kiểm định, CI, scale criteria", "Individual PK, treatment summaries, linear/log plots, diagnostics, LS means, SE, df, tests, CI and scaled criteria"),
        ("11.7", "Bảng đối chiếu CTD và kiểm tra nộp hồ sơ", "CTD mapping and submission checks",
         "CSR/ICH E3, CTD 2.7.1, 5.3.1.2; đối chiếu từng thành phần và kiểm tra eCTD ngoài ứng dụng", "CSR/ICH E3, CTD 2.7.1 and 5.3.1.2; reconcile and validate any eCTD package outside this app"),
    ]:
        add(n, tv, te, bv + ": " + blank, be + ": " + blank)
    add("11.8", "Dấu vết tính toán và phiên bản", "Calculation traceability and versions",
        f"analysis_run_id: {run.get('analysis_run_id', '—')}; dataset_hash: {run.get('dataset_hash', '—')}; "
        f"raw_hash: {run.get('raw_hash', '—')}; config_hash: {run.get('config_hash', '—')}; "
        f"snapshot_hash: {run.get('snapshot_hash', '—')}; engine_version: {run.get('engine_version', '—')}. "
        "Cần kiểm chứng hash và truy xuất dữ liệu ngoài bản nháp.",
        f"analysis_run_id: {run.get('analysis_run_id', '—')}; dataset_hash: {run.get('dataset_hash', '—')}; "
        f"raw_hash: {run.get('raw_hash', '—')}; config_hash: {run.get('config_hash', '—')}; "
        f"snapshot_hash: {run.get('snapshot_hash', '—')}; engine_version: {run.get('engine_version', '—')}. "
        "Verify hash and provenance against original records.")
    add("11.9", "Nguồn quy định và phạm vi áp dụng", "Guidance references and applicability",
        "Mẫu cấu trúc: Bioequivalence Study Reporting Format, ASEAN ACCSQ PPWG (tài liệu được cung cấp; "
        "phiên bản lịch sử). Quy tắc đang chọn: " + rule + "; nguồn trong snapshot: " +
        "; ".join(run.get("rule_snapshot", {}).get("sources", [])) +
        ". Kiểm tra phiên bản hiệu lực, product-specific guidance và phạm vi trước khi sử dụng.",
        "Reporting structure adapted from the supplied historical ASEAN ACCSQ PPWG Bioequivalence Study "
        "Reporting Format. Selected rule: " + rule + "; snapshot references: " +
        "; ".join(run.get("rule_snapshot", {}).get("sources", [])) +
        ". Confirm current applicability and product-specific guidance before use.")

    index = "\n".join(s["title"] for s in sections if s["level"] <= 2 and s["number"] != "3")
    index += "\n" + ("11.10 Phụ lục bảng dữ liệu tính toán" if vi else "11.10 Analysis data tables")
    index += "\n" + ("11.11 Nguồn và truy xuất" if vi else "11.11 References and traceability")
    index += "\n" + ("11.12 Hình và đồ thị minh họa" if vi else "11.12 Figures and visualizations")
    next(s for s in sections if s["number"] == "3")["body"] += "\n" + index
    return sections
