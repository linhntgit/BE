"""Bilingual, evidence-aware ASEAN/ICH-style bioequivalence report outline.

This is a comprehensive bioequivalence clinical study report template aligned
with ICH E3, ICH M13A, ICH M10, FDA BA/BE guidelines, and EMA BE guidelines.
Only stored snapshot fields are populated automatically; unsupplied source documents
and manual fields are conspicuously marked with standardized user-input requirements
for an independent author/reviewer.
"""

from __future__ import annotations

from typing import Any

from be_app.document_standards import (
    REPORT_BLANK_EN,
    REPORT_BLANK_VI,
    req_user_input,
)


def build_report_outline(
    study: dict, run: dict, manifest: dict, language: str, blockers_text: str = ""
) -> list[dict[str, Any]]:
    """Return numbered, hierarchical sections, preserving their source order."""
    vi = language == "vi"
    blank = REPORT_BLANK_VI if vi else REPORT_BLANK_EN

    def req_field(field_name_vi: str, field_name_en: str, guidance_vi: str, guidance_en: str) -> str:
        return req_user_input(
            field_name_vi if vi else field_name_en,
            guidance_vi if vi else guidance_en,
            language=language,
            context="report",
        )

    def field(key: str, name_vi: str = "", name_en: str = "", guide_vi: str = "", guide_en: str = "") -> str:
        value = study.get(key)
        if value is None or value == "" or value == []:
            if name_vi:
                return req_field(name_vi, name_en, guide_vi, guide_en)
            return blank
        if isinstance(value, (list, tuple)):
            res = ", ".join(str(x) for x in value)
            return res if res else (req_field(name_vi, name_en, guide_vi, guide_en) if name_vi else blank)
        return str(value)

    fed_state_vi = {"fasted": "Đói (nhịn ăn)", "fed": "No (sau ăn)"}.get(
        str(study.get("fed_state") or ""),
        req_field("Tình trạng ăn uống", "Dosing condition", "Ghi rõ điều kiện nhịn đói hoặc sau ăn", "Specify fasted or fed condition"),
    )
    fed_state_en = {"fasted": "Fasted", "fed": "Fed"}.get(
        str(study.get("fed_state") or ""),
        req_field("Tình trạng ăn uống", "Dosing condition", "Ghi rõ điều kiện nhịn đói hoặc sau ăn", "Specify fasted or fed condition"),
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

    # 1. TITLE PAGE AND STUDY GOVERNANCE
    add("1", "TRANG BÌA VÀ THÔNG TIN QUẢN LÝ", "TITLE PAGE AND STUDY GOVERNANCE",
        "Báo cáo nghiên cứu tương đương sinh học — bản dự thảo kỹ thuật; bắt buộc kiểm tra đối chiếu với đề cương, SAP, hồ sơ lâm sàng gốc và báo cáo phân tích sinh học.",
        "Bioequivalence clinical study report draft; must be reconciled with approved protocol, SAP, clinical source records and bioanalytical report.")

    add("1.1", "Tên nghiên cứu, mã số, phiên bản", "Study title, identifier and version",
        f"Tên nghiên cứu: {field('title', 'Tên nghiên cứu', 'Study title', 'Nhập tên khoa học đầy đủ của nghiên cứu', 'Enter full scientific study title')}. "
        f"Mã nghiên cứu: {field('study_id', 'Mã nghiên cứu', 'Study ID', 'Nhập mã số định danh nghiên cứu', 'Enter unique study ID')}. "
        f"Mã đề cương (Protocol): {field('protocol', 'Mã đề cương', 'Protocol ID', 'Nhập mã đề cương chính thức', 'Enter official protocol ID')}; "
        f"Kế hoạch phân tích thống kê (SAP): {field('sap', 'Mã SAP', 'SAP ID', 'Nhập mã số SAP đã phê duyệt', 'Enter approved SAP ID')}. "
        f"Phiên bản báo cáo và ngày lập: {req_field('Phiên bản báo cáo', 'Report version', 'Nhập số hiệu phiên bản báo cáo và ngày hoàn thành', 'Enter report version number and completion date')}.",
        f"Study title: {field('title', 'Tên nghiên cứu', 'Study title', 'Nhập tên khoa học đầy đủ của nghiên cứu', 'Enter full scientific study title')}. "
        f"Study ID: {field('study_id', 'Mã nghiên cứu', 'Study ID', 'Nhập mã số định danh nghiên cứu', 'Enter unique study ID')}. "
        f"Protocol: {field('protocol', 'Mã đề cương', 'Protocol ID', 'Nhập mã đề cương chính thức', 'Enter official protocol ID')}; "
        f"SAP: {field('sap', 'Mã SAP', 'SAP ID', 'Nhập mã số SAP đã phê duyệt', 'Enter approved SAP ID')}. "
        f"Report version and date: {req_field('Phiên bản báo cáo', 'Report version', 'Nhập số hiệu phiên bản báo cáo và ngày hoàn thành', 'Enter report version number and completion date')}.")

    governance_vi = {
        "1.2": (
            f"Nhà tài trợ: {field('sponsor', 'Nhà tài trợ', 'Sponsor', 'Nhập tên đơn vị tài trợ', 'Enter sponsor name')}. "
            f"Địa chỉ, người phụ trách, tài trợ và vai trò: {req_field('Thông tin nhà tài trợ', 'Sponsor details', 'Nhập tên, địa chỉ pháp lý, người đại diện và phân định trách nhiệm', 'Enter sponsor name, address, contact and responsibilities')}"
        ),
        "1.3": (
            f"Địa điểm thực hiện: {field('study_site', 'Cơ sở nghiên cứu', 'Study site', 'Nhập tên cơ sở nghiên cứu lâm sàng', 'Enter study site name')}. "
            f"Hợp đồng, giấy phép và trách nhiệm: {req_field('Cơ sở nghiên cứu lâm sàng', 'Study institutions', 'Nhập thông tin hợp đồng thử nghiệm, quyết định phê duyệt cơ sở và chứng chỉ GCP', 'Enter trial contract, site approval and GCP certification')}"
        ),
        "1.4": (
            f"Nghiên cứu viên chính: {field('principal_investigator', 'Nghiên cứu viên chính', 'Principal investigator', 'Nhập tên PI', 'Enter PI name')}. "
            f"Học vị, cơ quan, trách nhiệm: {req_field('Hồ sơ nghiên cứu viên chính', 'Principal investigator details', 'Nhập học vị, chứng chỉ hành nghề y, đào tạo GCP và văn bản phân công', 'Enter qualifications, medical license, GCP training and delegation')}"
        ),
        "1.10": (
            f"Thời gian toàn nghiên cứu: {field('study_start_date')} đến {field('study_end_date')}; "
            f"lâm sàng: {field('clinical_start_date')} đến {field('clinical_end_date')}; "
            f"phân tích mẫu sinh học: {field('bioanalytical_start_date')} đến {field('bioanalytical_end_date')}; "
            f"khóa dữ liệu: {field('data_lock_date')}. "
            f"Bổ sung ngày phê duyệt, tuyển chọn, lấy mẫu và phê duyệt báo cáo: {req_field('Các mốc thời gian nghiên cứu', 'Study chronology milestones', 'Nhập ngày phê duyệt IRB, ngày tuyển chọn đầu tiên, ngày dùng thuốc, ngày lấy mẫu cuối và ngày phê duyệt báo cáo', 'Enter IRB approval date, first subject screened, dosing dates, last sampling date and final report approval date')}"
        ),
    }
    governance_en = {
        "1.2": (
            f"Sponsor: {field('sponsor', 'Nhà tài trợ', 'Sponsor', 'Nhập tên đơn vị tài trợ', 'Enter sponsor name')}. "
            f"Address, contact, funding and responsibilities: {req_field('Thông tin nhà tài trợ', 'Sponsor details', 'Nhập tên, địa chỉ pháp lý, người đại diện và phân định trách nhiệm', 'Enter sponsor name, address, contact and responsibilities')}"
        ),
        "1.3": (
            f"Study site: {field('study_site', 'Cơ sở nghiên cứu', 'Study site', 'Nhập tên cơ sở nghiên cứu lâm sàng', 'Enter study site name')}. "
            f"Contracts, authorizations and responsibilities: {req_field('Cơ sở nghiên cứu lâm sàng', 'Study institutions', 'Nhập thông tin hợp đồng thử nghiệm, quyết định phê duyệt cơ sở và chứng chỉ GCP', 'Enter trial contract, site approval and GCP certification')}"
        ),
        "1.4": (
            f"Principal investigator: {field('principal_investigator', 'Nghiên cứu viên chính', 'Principal investigator', 'Nhập tên PI', 'Enter PI name')}. "
            f"Qualifications and duties: {req_field('Hồ sơ nghiên cứu viên chính', 'Principal investigator details', 'Nhập học vị, chứng chỉ hành nghề y, đào tạo GCP và văn bản phân công', 'Enter qualifications, medical license, GCP training and delegation')}"
        ),
        "1.10": (
            f"Overall study: {field('study_start_date')} to {field('study_end_date')}; "
            f"clinical: {field('clinical_start_date')} to {field('clinical_end_date')}; "
            f"bioanalysis: {field('bioanalytical_start_date')} to {field('bioanalytical_end_date')}; "
            f"data lock: {field('data_lock_date')}. "
            f"Supply approval, recruitment, sampling and report approval dates: {req_field('Các mốc thời gian nghiên cứu', 'Study chronology milestones', 'Nhập ngày phê duyệt IRB, ngày tuyển chọn đầu tiên, ngày dùng thuốc, ngày lấy mẫu cuối và ngày phê duyệt báo cáo', 'Enter IRB approval date, first subject screened, dosing dates, last sampling date and final report approval date')}"
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
            governance_vi.get(n, f"{prompt_vi}: {req_field(tv, te, prompt_vi, prompt_en)}"),
            governance_en.get(n, f"{prompt_en}: {req_field(tv, te, prompt_vi, prompt_en)}"))

    # 2. STUDY SYNOPSIS
    add("2", "TÓM TẮT NGHIÊN CỨU", "STUDY SYNOPSIS",
        f"Nghiên cứu: {field('title')}; hoạt chất: {field('active_ingredient')}; thiết kế: {field('design')}; "
        f"điều kiện: {fed_state_vi}; liều: {field('dose')} {field('dose_unit')}; "
        f"Thuốc thử (T): {field('test_product')} (lô {field('test_batch')}); "
        f"Thuốc đối chứng (R): {field('reference_product')} (lô {field('reference_batch')}); "
        f"quy tắc đánh giá: {rule}; phương pháp phân tích: {method}; endpoint chính: {field('primary_endpoints')}. "
        f"Kết quả phân tích từ snapshot: {result_label}. "
        f"Tóm tắt an toàn: {req_field('Tóm tắt an toàn', 'Safety summary', 'Nhập tóm tắt số lượng và mức độ biến cố bất lợi (AE/SAE)', 'Enter summary of adverse events and safety findings')}. "
        "Các quyết định cấp nghiên cứu chính thức đòi hỏi đầy đủ hồ sơ nguồn, chữ ký phê duyệt và thẩm định độc lập.",
        f"Recorded study title: {field('title')}; active substance: {field('active_ingredient')}; design: {field('design')}; "
        f"condition: {fed_state_en}; dose: {field('dose')} {field('dose_unit')}; "
        f"Test (T): {field('test_product')} (batch {field('test_batch')}); "
        f"Reference (R): {field('reference_product')} (batch {field('reference_batch')}); "
        f"regulatory rule: {rule}; method: {method}; primary endpoints: {field('primary_endpoints')}. "
        f"Snapshot analysis decision: {result_label}. "
        f"Safety summary: {req_field('Tóm tắt an toàn', 'Safety summary', 'Nhập tóm tắt số lượng và mức độ biến cố bất lợi (AE/SAE)', 'Enter summary of adverse events and safety findings')}. "
        "Formal study-level claims require reconciled source documentation, signatures and independent review.")

    # 3. TABLE OF CONTENTS
    add("3", "MỤC LỤC", "TABLE OF CONTENTS",
        "Danh mục các phần 1–11 và các đề mục cấp hai, cấp ba được trình bày chi tiết bên dưới. "
        "Bảng mục lục số trang thực tế cần được cập nhật sau khi hoàn thiện toàn bộ văn bản báo cáo.",
        "Sections 1–11 and their respective subsections are listed below. "
        "Page numbering must be updated after final compilation of the complete clinical study report.")

    # 4. ABBREVIATIONS AND DEFINITIONS
    add("4", "CHỮ VIẾT TẮT VÀ THUẬT NGỮ", "ABBREVIATIONS AND DEFINITIONS",
        "ABE: tương đương sinh học trung bình (Average Bioequivalence); ABEL: ABE với giới hạn mở rộng (Average BE with Expanding Limits); "
        "ADR: phản ứng có hại của thuốc (Adverse Drug Reaction); AE: biến cố bất lợi (Adverse Event); "
        "ALCOA+: attributable, legible, contemporaneous, original, accurate, complete, consistent, enduring, available; "
        "ANOVA: phân tích phương sai (Analysis of Variance); AUC: diện tích dưới đường cong nồng độ–thời gian (Area Under Curve); "
        "AUC0–t: AUC từ 0 đến thời điểm lấy mẫu có nồng độ đo được cuối cùng; AUC0–∞: AUC từ 0 ngoại suy đến vô cực; "
        "BLQ: dưới giới hạn định lượng (Below Limit of Quantification); CI90: khoảng tin cậy 90% (90% Confidence Interval); "
        "Cmax: nồng độ đỉnh trong huyết tương; CVw: hệ số biến thiên trong cá thể; CVwR: hệ số biến thiên trong cá thể của thuốc đối chứng; "
        "ECG: điện tâm đồ; EMA: Cơ quan Quản lý Dược phẩm Châu Âu; FDA: Cục Quản lý Thực phẩm và Dược phẩm Hoa Kỳ; "
        "GCP: Thực hành tốt thử nghiệm lâm sàng; GLP: Thực hành tốt phòng kiểm nghiệm; GMR: tỷ số trung bình nhân (Geometric Mean Ratio T/R); "
        "HVD/HVDP: thuốc/chế phẩm có độ biến thiên cao (Highly Variable Drug Product, CVw >= 30%); "
        "ICH: Hội đồng quốc tế về hài hòa các yêu cầu kỹ thuật đối với dược phẩm dùng cho người; "
        "IR: giải phóng tức thời (Immediate Release); ISR: phân tích lại mẫu nghiên cứu thực tế (Incurred Sample Reanalysis); "
        "LC-MS/MS: sắc ký lỏng ghép hai lần khối phổ; LLOQ: giới hạn định lượng dưới; LS means: trung bình bình phương tối thiểu; "
        "NCA: phân tích phi ngăn (Noncompartmental Analysis); NTI: khoảng điều trị hẹp (Narrow Therapeutic Index); "
        "PK: dược động học (Pharmacokinetics); PSG: hướng dẫn đặc thù sản phẩm (Product-Specific Guidance); "
        "RSABE: tương đương sinh học chuẩn hóa theo tham chiếu (Reference-Scaled Average Bioequivalence); "
        "SAE: biến cố bất lợi nghiêm trọng (Serious Adverse Event); SAP: kế hoạch phân tích thống kê (Statistical Analysis Plan); "
        "sWR: độ lệch chuẩn trong cá thể của thuốc đối chứng trên thang log; sWT: độ lệch chuẩn trong cá thể của thuốc thử; "
        "t½: thời gian bán thải pha cuối; Tmax: thời gian đạt nồng độ đỉnh; TOST: hai kiểm định một phía (Two One-Sided Tests); "
        "UCB: cận trên khoảng tin cậy (Upper Confidence Bound); λz: hằng số tốc độ thải trừ pha cuối.",
        "ABE: average bioequivalence; ABEL: average BE with expanding limits; ADR: adverse drug reaction; AE: adverse event; "
        "ALCOA+: attributable, legible, contemporaneous, original, accurate, complete, consistent, enduring, available; "
        "ANOVA: analysis of variance; AUC: area under concentration-time curve; AUC0–t: AUC from time 0 to last quantifiable concentration; "
        "AUC0–∞: AUC from time 0 extrapolated to infinity; BLQ: below limit of quantification; CI90: 90% confidence interval; "
        "Cmax: peak plasma concentration; CVw: within-subject coefficient of variation; CVwR: within-subject CV of reference; "
        "ECG: electrocardiogram; EMA: European Medicines Agency; FDA: US Food and Drug Administration; "
        "GCP: Good Clinical Practice; GLP: Good Laboratory Practice; GMR: geometric mean ratio (T/R); "
        "HVD/HVDP: highly variable drug product (CVw >= 30%); ICH: International Council for Harmonisation; "
        "IR: immediate release; ISR: incurred sample reanalysis; LC-MS/MS: liquid chromatography-tandem mass spectrometry; "
        "LLOQ: lower limit of quantification; LS means: least-squares means; NCA: noncompartmental analysis; "
        "NTI: narrow therapeutic index; PK: pharmacokinetics; PSG: product-specific guidance; "
        "RSABE: reference-scaled average bioequivalence; SAE: serious adverse event; SAP: statistical analysis plan; "
        "sWR: within-subject standard deviation of reference on log scale; sWT: within-subject SD of test; "
        "t½: terminal elimination half-life; Tmax: time to peak concentration; TOST: two one-sided tests; "
        "UCB: upper confidence bound; λz: terminal elimination rate constant.")

    # 5. INTRODUCTION AND SCIENTIFIC BACKGROUND
    add("5", "GIỚI THIỆU VÀ CƠ SỞ KHOA HỌC", "INTRODUCTION AND SCIENTIFIC BACKGROUND")
    add("5.1", "Dược lý, cơ chế tác dụng, chỉ định", "Pharmacology, mechanism and indication",
        f"Hoạt chất nghiên cứu: {field('active_ingredient', 'Hoạt chất', 'Active ingredient', 'Nhập tên hoạt chất', 'Enter active ingredient')}. "
        f"Bổ sung cơ chế tác dụng dược lý, nhóm điều trị, chỉ định lâm sàng, liều điều trị khuyến cáo, đường dùng "
        f"và đặc tính hấp thu/chuyển hóa: {req_field('Dược lý và chỉ định', 'Pharmacology and indication', 'Nhập cơ chế tác dụng, chỉ định, đường dùng và tài liệu tham khảo SmPC/USPI', 'Enter mechanism, indication, route and SmPC/USPI references')}",
        f"Investigational substance: {field('active_ingredient', 'Hoạt chất', 'Active ingredient', 'Nhập tên hoạt chất', 'Enter active ingredient')}. "
        f"Supply clinical pharmacology, mechanism of action, therapeutic indication, dose range, route, "
        f"and absorption/disposition properties: {req_field('Dược lý và chỉ định', 'Pharmacology and indication', 'Nhập cơ chế tác dụng, chỉ định, đường dùng và tài liệu tham khảo SmPC/USPI', 'Enter mechanism, indication, route and SmPC/USPI references')}")

    add("5.2", "Dược động học và lựa chọn endpoint", "Pharmacokinetics and endpoint rationale",
        f"Endpoint chính đánh giá BE: {field('primary_endpoints')}; endpoint phụ: {field('secondary_endpoints')}. "
        f"Giải thích tính phù hợp của AUC0-t/Cmax theo hướng dẫn FDA/EMA/ICH M13A, cơ sở lựa chọn thời gian lấy mẫu, "
        f"tính toán λz, tỷ lệ AUC ngoại suy, ảnh hưởng của thức ăn và chiến lược đo lường thuốc mẹ so với chất chuyển hóa: "
        f"{req_field('Cơ sở lựa chọn endpoint PK', 'PK endpoint rationale', 'Giải thích tính phù hợp của AUC/Cmax, thời gian lấy mẫu và chất phân tích', 'Justify AUC/Cmax, sampling duration and target analyte')}",
        f"Primary BE endpoints: {field('primary_endpoints')}; secondary endpoints: {field('secondary_endpoints')}. "
        f"Justify appropriateness of AUC0-t/Cmax under FDA/EMA/ICH M13A, sampling duration, λz estimation, "
        f"extrapolated AUC fraction, food effect and parent vs metabolite measurement strategy: "
        f"{req_field('Cơ sở lựa chọn endpoint PK', 'PK endpoint rationale', 'Giải thích tính phù hợp của AUC/Cmax, thời gian lấy mẫu và chất phân tích', 'Justify AUC/Cmax, sampling duration and target analyte')}")

    add("5.3", "An toàn và phản ứng bất lợi đã biết", "Known safety and adverse reactions",
        f"Đặc điểm an toàn đã biết của hoạt chất, chống chỉ định, cảnh báo đặc biệt, các biến cố bất lợi thường gặp, "
        f"theo dõi an toàn trong quá trình thử nghiệm và kế hoạch cấp cứu/xử trí: "
        f"{req_field('An toàn và phản ứng bất lợi', 'Safety and known ADRs', 'Nhập hồ sơ an toàn, chống chỉ định, theo dõi lâm sàng và thuốc cấp cứu', 'Supply safety profile, contraindications, clinical monitoring and rescue medication')}",
        f"Known safety profile of the substance, contraindications, warnings, anticipated adverse reactions, "
        f"clinical safety monitoring and emergency management plan: "
        f"{req_field('An toàn và phản ứng bất lợi', 'Safety and known ADRs', 'Nhập hồ sơ an toàn, chống chỉ định, theo dõi lâm sàng và thuốc cấp cứu', 'Supply safety profile, contraindications, clinical monitoring and rescue medication')}")

    # 6. OBJECTIVES AND HYPOTHESES
    add("6", "MỤC TIÊU VÀ GIẢ THUYẾT", "OBJECTIVES AND HYPOTHESES",
        f"Mục tiêu chính: Đánh giá tương đương sinh học giữa thuốc thử T ({field('test_product')}) và thuốc đối chứng R ({field('reference_product')}) "
        f"theo phương pháp {method} trong thiết kế {field('design')}. "
        f"Giả thuyết thống kê: Hai kiểm định một phía (TOST) ở mức ý nghĩa alpha = 0.05. "
        f"Tiêu chuẩn chấp thuận dự kiến theo từng endpoint, tính hợp lệ của thiết kế và các phân tích độ nhạy đã xác định trước; "
        f"đối chiếu với SAP chính thức: {field('sap')}.",
        f"Primary objective: Assess bioequivalence of Test product T ({field('test_product')}) versus Reference product R ({field('reference_product')}) "
        f"using {method} methodology under {field('design')} design. "
        f"Statistical hypotheses: Two one-sided tests (TOST) at alpha = 0.05. "
        f"Prespecified acceptance criteria by endpoint, design eligibility, and sensitivity analyses; "
        f"reconciled with official SAP: {field('sap')}.")

    # 7. INVESTIGATIONAL PRODUCT INFORMATION
    add("7", "THÔNG TIN SẢN PHẨM NGHIÊN CỨU", "INVESTIGATIONAL PRODUCT INFORMATION")
    add("7.1", "Thuốc thử T", "Test product T",
        f"Tên thuốc thử: {field('test_product')}; hoạt chất: {field('active_ingredient')}; "
        f"hàm lượng: {field('test_strength')}; nồng độ: {field('test_concentration')}; "
        f"dạng bào chế: {field('test_dosage_form')}; loại giải phóng: {field('formulation')}; "
        f"nhà sản xuất: {field('test_manufacturer')}; số lô sản xuất: {field('test_batch')}; "
        f"hạn dùng: {field('test_expiry_date')}; liều sử dụng: {field('dose')} {field('dose_unit')}. "
        f"Bổ sung cỡ lô sản xuất thực tế, công thức thành phần, tiêu chuẩn chất lượng thành phẩm và phiếu kiểm nghiệm (CoA): "
        f"{req_field('Hồ sơ thuốc thử', 'Test product records', 'Nhập cỡ lô sản xuất, tiêu chuẩn thành phẩm, hàm lượng định lượng thực tế và CoA', 'Supply batch size, release specifications, actual assay potency and CoA')}",
        f"Test product: {field('test_product')}; active ingredient: {field('active_ingredient')}; "
        f"strength: {field('test_strength')}; concentration: {field('test_concentration')}; "
        f"dosage form: {field('test_dosage_form')}; release type: {field('formulation')}; "
        f"manufacturer: {field('test_manufacturer')}; batch number: {field('test_batch')}; "
        f"expiry date: {field('test_expiry_date')}; administered dose: {field('dose')} {field('dose_unit')}. "
        f"Add commercial batch size, composition, release specifications and Certificate of Analysis (CoA): "
        f"{req_field('Hồ sơ thuốc thử', 'Test product records', 'Nhập cỡ lô sản xuất, tiêu chuẩn thành phẩm, hàm lượng định lượng thực tế và CoA', 'Supply batch size, release specifications, actual assay potency and CoA')}")

    add("7.2", "Thuốc đối chứng R", "Reference product R",
        f"Tên thuốc đối chứng: {field('reference_product')}; hoạt chất: {field('active_ingredient')}; "
        f"hàm lượng: {field('reference_strength')}; nồng độ: {field('reference_concentration')}; "
        f"dạng bào chế: {field('reference_dosage_form')}; nhà sản xuất: {field('reference_manufacturer')}; "
        f"số lô sản xuất: {field('reference_batch')}; hạn dùng: {field('reference_expiry_date')}. "
        f"Bổ sung nước xuất xứ, đơn vị sở hữu giấy phép lưu hành, nguồn gốc cung ứng, nhãn gốc và CoA: "
        f"{req_field('Hồ sơ thuốc đối chứng', 'Reference product records', 'Nhập nước xuất xứ, số ĐKLH, nguồn gốc mua thuốc và CoA', 'Supply country of origin, marketing authorization holder, procurement source and CoA')}",
        f"Reference product: {field('reference_product')}; active ingredient: {field('active_ingredient')}; "
        f"strength: {field('reference_strength')}; concentration: {field('reference_concentration')}; "
        f"dosage form: {field('reference_dosage_form')}; manufacturer: {field('reference_manufacturer')}; "
        f"batch number: {field('reference_batch')}; expiry date: {field('reference_expiry_date')}. "
        f"Add country of origin, marketing authorization holder, procurement chain, original packaging label and CoA: "
        f"{req_field('Hồ sơ thuốc đối chứng', 'Reference product records', 'Nhập nước xuất xứ, số ĐKLH, nguồn gốc mua thuốc và CoA', 'Supply country of origin, marketing authorization holder, procurement source and CoA')}")

    add("7.3", "Tương đương dược học và kiểm nghiệm", "Pharmaceutical equivalence and testing",
        f"Đối chiếu định tính, định lượng, độ đồng đều khối lượng/hàm lượng, hàm lượng hoạt chất thực tế đo được (chênh lệch giữa T và R không quá 5% theo FDA/EMA), "
        f"tạp chất liên quan và các tiêu chuẩn kiểm nghiệm giải phóng lô: "
        f"{req_field('Kiểm nghiệm tương đương dược học', 'Pharmaceutical equivalence testing', 'Báo cáo hàm lượng định lượng của T và R, độ chênh lệch <= 5% và kết quả kiểm nghiệm', 'Report assay potency of T and R, potency difference <= 5% and release testing results')}",
        f"Comparison of identification, assay, content uniformity, actual measured potency difference between T and R (must not exceed 5% per FDA/EMA), "
        f"related substances, and release specification compliance: "
        f"{req_field('Kiểm nghiệm tương đương dược học', 'Pharmaceutical equivalence testing', 'Báo cáo hàm lượng định lượng của T và R, độ chênh lệch <= 5% và kết quả kiểm nghiệm', 'Report assay potency of T and R, potency difference <= 5% and release testing results')}")

    add("7.4", "So sánh hòa tan", "Comparative dissolution",
        f"Dữ liệu thử nghiệm hòa tan so sánh in vitro tại các môi trường pH sinh lý (pH 1.2, pH 4.5, pH 6.8 và môi trường kiểm nghiệm chất lượng), "
        f"thiết bị thử, tốc độ khuấy, số thời điểm lấy mẫu, đồ thị giải phóng và tính toán hệ số tương đồng f2 (yêu cầu f2 >= 50): "
        f"{req_field('Hòa tan so sánh in vitro', 'Comparative in vitro dissolution', 'Nhập điều kiện thử, bảng số liệu hòa tan, giá trị f2 và kết luận tương đồng', 'Supply test conditions, dissolution profile data, f2 similarity and conclusions')}",
        f"In vitro comparative dissolution testing across physiological pH media (pH 1.2, pH 4.5, pH 6.8 and QC release medium), "
        f"apparatus, agitation speed, sampling timepoints, dissolution profiles and f2 similarity factor calculation (f2 >= 50): "
        f"{req_field('Hòa tan so sánh in vitro', 'Comparative in vitro dissolution', 'Nhập điều kiện thử, bảng số liệu hòa tan, giá trị f2 và kết luận tương đồng', 'Supply test conditions, dissolution profile data, f2 similarity and conclusions')}")

    add("7.5", "Cam kết của nhà tài trợ", "Sponsor declaration",
        f"Cam kết chính thức của nhà tài trợ về tính đại diện của lô thuốc thử, chứng nhận GMP, điều kiện vận chuyển/bảo quản, "
        f"tính toán thuốc (product accountability), bảo quản mẫu lưu độc lập (FDA 21 CFR 320.38 yêu cầu 5 năm; EMA yêu cầu tối thiểu 1 năm sau hạn dùng) và chữ ký có thẩm quyền: "
        f"{req_field('Cam kết nhà tài trợ', 'Sponsor declaration', 'Bổ sung văn bản cam kết GMP, lưu giữ mẫu lưu độc lập và trách nhiệm sản phẩm', 'Supply GMP declaration, retention sample storage commitment and authorized sign-off')}",
        f"Sponsor declaration regarding representative commercial batch manufacturing, GMP compliance, transport/storage conditions, "
        f"drug accountability, independent reserve sample retention (FDA 21 CFR 320.38 requires 5 years; EMA requires >= 1 year past expiry) and authorized sign-off: "
        f"{req_field('Cam kết nhà tài trợ', 'Sponsor declaration', 'Bổ sung văn bản cam kết GMP, lưu giữ mẫu lưu độc lập và trách nhiệm sản phẩm', 'Supply GMP declaration, retention sample storage commitment and authorized sign-off')}")

    # 8. INVESTIGATIONAL PLAN AND METHODS
    add("8", "KẾ HOẠCH NGHIÊN CỨU VÀ PHƯƠNG PHÁP", "INVESTIGATIONAL PLAN AND METHODS")
    add("8.1", "Thiết kế lâm sàng", "Clinical study design",
        f"Thiết kế: {field('design')}; tình trạng ăn uống: {fed_state_vi}; chế độ liều: {'đơn liều (single-dose)' if study.get('single_dose') else 'đa liều'}; "
        f"đường dùng: {field('route')}. Căn cứ lựa chọn thiết kế crossover/parallel/replicate; tiêu chí chọn vào và loại trừ đối tượng, "
        f"thời gian washout giữa các kỳ (>= 5-7 lần t1/2), điều kiện kiểm soát lâm sàng, thời điểm lấy mẫu và tổng thể tích máu thu thập: "
        f"{req_field('Thiết kế nghiên cứu lâm sàng', 'Clinical study design details', 'Nhập lý giải thiết kế, tiêu chuẩn chọn/loại, thời gian washout và thể tích máu', 'Justify design, eligibility criteria, washout duration and blood volume')}",
        f"Design: {field('design')}; fed state: {fed_state_en}; dosing: {'single-dose' if study.get('single_dose') else 'multiple-dose'}; "
        f"route: {field('route')}. Justification for crossover/parallel/replicate; participant inclusion/exclusion criteria, "
        f"washout duration (>= 5-7 t1/2), controlled clinical conditions, sampling schedule and total blood volume: "
        f"{req_field('Thiết kế nghiên cứu lâm sàng', 'Clinical study design details', 'Nhập lý giải thiết kế, tiêu chuẩn chọn/loại, thời gian washout và thể tích máu', 'Justify design, eligibility criteria, washout duration and blood volume')}")

    add("8.1.1", "Tuyển chọn, phân nhóm và quần thể", "Screening, randomization and populations",
        f"Sơ đồ tuyển chọn đối tượng (participant flow chart), danh sách đối tượng sàng lọc, phân bổ ngẫu nhiên theo trình tự, "
        f"các kỳ đã hoàn tất, các trường hợp rút lui hoặc mất theo dõi, xử lý dữ liệu thiếu và phân định quần thể phân tích "
        f"(Safety Population, PK Population, Evaluated BE Population) theo quy định trong SAP: "
        f"{req_field('Quần thể phân tích và đối tượng', 'Analysis populations and disposition', 'Nhập sơ đồ phân bổ đối tượng, lý do rút lui và phân định quần thể theo SAP', 'Supply subject disposition flowchart, withdrawal reasons and SAP population definitions')}",
        f"Participant screening and disposition flowchart, allocation to sequences, completed periods, "
        f"withdrawals/dropouts, handling of missing observations, and definition of analysis populations "
        f"(Safety Population, PK Population, Evaluated BE Population) according to the SAP: "
        f"{req_field('Quần thể phân tích và đối tượng', 'Analysis populations and disposition', 'Nhập sơ đồ phân bổ đối tượng, lý do rút lui và phân định quần thể theo SAP', 'Supply subject disposition flowchart, withdrawal reasons and SAP population definitions')}")

    add("8.1.2", "Lấy, xử lý và bảo quản mẫu", "Sample collection, handling and storage",
        f"Quy trình thu thập mẫu máu: thời điểm danh định so với thời điểm thực tế, loại chất chống đông (K2-EDTA), ly tâm lạnh (4°C), "
        f"chia mẫu thành 2 ống (chính và dự phòng), nhiệt độ lưu trữ (-70°C đến -80°C), thời gian giữ mẫu, "
        f"nhật ký theo dõi nhiệt độ liên tục trong quá trình lưu trữ và vận chuyển (chain of custody), và các sai lệch lấy mẫu phát sinh: "
        f"{req_field('Quy trình xử lý mẫu sinh học', 'Biological sample handling', 'Nhập quy trình ly tâm, chia mẫu, nhiệt độ bảo quản, nhật ký vận chuyển và sai lệch', 'Supply centrifugation, aliquoting, storage temperatures, shipping logs and deviations')}",
        f"Nominal vs actual sampling timepoints, anticoagulant (K2-EDTA), refrigerated centrifugation (4°C), "
        f"splitting into primary and backup aliquots, storage temperature (-70°C to -80°C), hold times, "
        f"continuous temperature monitoring during storage and transport (chain of custody), and sampling deviations: "
        f"{req_field('Quy trình xử lý mẫu sinh học', 'Biological sample handling', 'Nhập quy trình ly tâm, chia mẫu, nhiệt độ bảo quản, nhật ký vận chuyển và sai lệch', 'Supply centrifugation, aliquoting, storage temperatures, shipping logs and deviations')}")

    add("8.2", "Thuốc dùng và quy trình can thiệp", "Treatments and interventions",
        f"Thuốc thử T: {field('test_product')} (lô {field('test_batch')}); "
        f"Thuốc đối chứng R: {field('reference_product')} (lô {field('reference_batch')}); "
        f"liều dùng: {field('dose')} {field('dose_unit')}; điều kiện dùng thuốc: {fed_state_vi}. "
        f"Quy trình phân liều: bảng ngẫu nhiên hóa, kiểm tra khoang miệng sau uống, uống cùng 240 mL nước ở nhiệt độ phòng, "
        f"kiểm soát bữa ăn (ăn sau 4h và 10h), hạn chế nước uống và tư thế ngồi/đi lại trong 2-4 giờ đầu sau dùng thuốc: "
        f"{req_field('Can thiệp dùng thuốc', 'Dosing interventions', 'Mô tả quy trình phân liều, kiểm tra tuân thủ, lượng nước và kiểm soát ăn uống', 'Describe dosing procedure, compliance checks, water volume and meal control')}",
        f"Test product T: {field('test_product')} (batch {field('test_batch')}); "
        f"Reference product R: {field('reference_product')} (batch {field('reference_batch')}); "
        f"dose: {field('dose')} {field('dose_unit')}; condition: {fed_state_en}. "
        f"Dosing administration: randomization schedule, mouth check, administration with 240 mL ambient water, "
        f"standardized meal schedule (4 h and 10 h post-dose), fluid restriction and sitting posture control for first 2-4 hours: "
        f"{req_field('Can thiệp dùng thuốc', 'Dosing interventions', 'Mô tả quy trình phân liều, kiểm tra tuân thủ, lượng nước và kiểm soát ăn uống', 'Describe dosing procedure, compliance checks, water volume and meal control')}")

    add("8.3", "Theo dõi lâm sàng và an toàn", "Clinical and safety monitoring",
        f"Quy trình theo dõi an toàn: lịch khám thực thể, đo dấu hiệu sinh tồn định kỳ, xét nghiệm huyết học/sinh hóa/nước tiểu, "
        f"điện tâm đồ (ECG); ghi nhận và mã hóa biến cố bất lợi (AE/SAE), đánh giá mức độ nặng theo CTCAE, đánh giá mối quan hệ nhân quả, "
        f"thuốc dùng kèm và biện pháp xử trí: "
        f"{req_field('Theo dõi an toàn lâm sàng', 'Clinical safety monitoring', 'Báo cáo lịch khám lâm sàng, mã hóa AE/SAE, mối liên quan và biện pháp cấp cứu', 'Report examination schedule, AE/SAE coding, causality and emergency procedures')}",
        f"Clinical safety monitoring: physical examinations, routine vital signs, clinical laboratory tests, "
        f"ECG; AE/SAE recording and coding, severity grading per CTCAE, causality assessment, "
        f"concomitant medications and emergency management procedures: "
        f"{req_field('Theo dõi an toàn lâm sàng', 'Clinical safety monitoring', 'Báo cáo lịch khám lâm sàng, mã hóa AE/SAE, mối liên quan và biện pháp cấp cứu', 'Report examination schedule, AE/SAE coding, causality and emergency procedures')}")

    add("8.4", "Phương pháp PK/NCA", "PK/NCA methods",
        "Sử dụng thời gian lấy mẫu thực tế và dữ liệu nồng độ định lượng từ snapshot đã được kiểm chứng. "
        "Đối chiếu cấu hình NCA, phần mềm phân tích và thuật toán tích phân với SAP và hồ sơ phương pháp. "
        "Định nghĩa Cmax/Tmax, AUC0–t (phương pháp hình thang tuyến tính/logarit), AUC0–∞, λz, t½, %AUC ngoại suy và quy tắc xử lý BLQ; "
        "mọi can thiệp lựa chọn pha cuối (terminal phase) đều phải có nhật ký audit trail và căn cứ khoa học rõ ràng.",
        "Use actual sampling times and validated concentration data from the locked snapshot. "
        "Reconcile NCA configuration, analytical software and integration algorithm with the SAP and methods records. "
        "Define Cmax/Tmax, AUC0–t (linear-up / log-down trapezoidal), AUC0–∞, λz, t½, %AUC extrapolated and BLQ handling; "
        "any terminal-phase overrides require audit trail documentation and objective scientific justification.")

    add("8.5", "Kế hoạch phân tích thống kê", "Statistical analysis plan",
        f"Quy tắc đánh giá: {rule}; SAP: {field('sap')}; endpoint chính: {field('primary_endpoints')}. "
        "Phép biến đổi logarit tự nhiên trên các thông số PK dương, mô hình ANOVA hoặc Mixed Model phù hợp với cấu trúc thiết kế, "
        "ước lượng GMR (T/R) và khoảng tin cậy 90% (hai kiểm định một phía TOST ở mức alpha = 0.05), "
        "bậc tự do, phương sai dư và hệ số biến thiên trong cá thể (CVw), xử lý dữ liệu thiếu và phân tích độ nhạy. "
        "Các giới hạn BE được xác định trước theo quy định và profile nghiên cứu trước khi khóa cơ sở dữ liệu.",
        f"Regulatory rule: {rule}; SAP: {field('sap')}; primary endpoints: {field('primary_endpoints')}. "
        "Natural-log transformation of positive PK endpoints, ANOVA or Mixed Model appropriate for the design, "
        "T/R GMR point estimate and 90% confidence interval (two one-sided tests TOST at alpha = 0.05), "
        "degrees of freedom, residual variance and within-subject CV (CVw), missing data handling and sensitivity analyses. "
        "BE acceptance limits must be prespecified according to regulations and profile prior to database lock.")

    add("8.5.1", "ABE tiêu chuẩn và TOST", "Conventional ABE and TOST",
        "Đối với nghiên cứu crossover 2×2 hoặc parallel đủ điều kiện, tiêu chuẩn ABE yêu cầu toàn bộ khoảng tin cậy 90% "
        "của GMR đối với AUC0-t và Cmax phải nằm hoàn toàn trong giới hạn [80.00%, 125.00%] (tương ứng với thang log [-0.2231, +0.2231]). "
        "Mô hình phân tích phương sai (ANOVA) có các yếu tố: Sequence, Period, Treatment và Subject(Sequence) đối với crossover; "
        "hoặc Treatment và Subject đối với parallel; không suy luận tương đương sinh học chỉ dựa trên p-value của kiểm định khác biệt.",
        "For eligible 2×2 crossover or parallel studies, conventional ABE requires that the entire 90% confidence interval "
        "of the T/R GMR for AUC0-t and Cmax fall completely within [80.00%, 125.00%] (log scale [-0.2231, +0.2231]). "
        "The ANOVA model includes Sequence, Period, Treatment and Subject(Sequence) for crossover, "
        "or Treatment and Subject for parallel; never infer bioequivalence from difference-test p-values alone.")

    if rule == "EMA_HVDP_ABEL":
        add("8.5.2", "EMA HVDP: ABEL", "EMA HVDP: ABEL",
            "Chỉ áp dụng mở rộng khoảng chấp nhận cho Cmax khi thiết kế replicate, độ biến thiên trong cá thể của R được ước tính hợp lệ, "
            "CVwR > 30%, phương pháp đã được định trước trong đề cương/SAP và có lý giải lâm sàng. Giới hạn mở rộng dựa trên sWR: "
            "[U, L] = exp(±0.760*sWR), có trần tối đa [69.84%, 143.19%] (tương ứng CVwR = 50%), đồng thời GMR điểm phải nằm trong [80.00%, 125.00%]; "
            "AUC giữ nguyên tiêu chí chấp thuận thông thường [80.00%, 125.00%]. "
            f"Scaling prespecified: {field('scaled_be_prespecified')}; căn cứ HVD: {field('hvd_justification')}. "
            "Rà soát outlier và độ tin cậy của sWR; đánh giá từng tiêu chí trong bảng kết quả chi tiết.",
            "Widening acceptance limits applies to Cmax only under a replicate design when within-subject reference variability is valid, "
            "CVwR > 30%, prespecified in protocol/SAP, and clinically justified. Widened limits use sWR: "
            "[U, L] = exp(±0.760*sWR) capped at [69.84%, 143.19%] (at CVwR = 50%); point estimate GMR must also remain within [80.00%, 125.00%]; "
            "AUC strictly retains conventional limits [80.00%, 125.00%]. "
            f"Prespecified: {field('scaled_be_prespecified')}; HVD justification: {field('hvd_justification')}. "
            "Review outliers and sWR reliability; verify all individual gates in reviewer tables.")
    elif rule == "FDA_HVD_RSABE_2026":
        add("8.5.2", "FDA HVD: RSABE", "FDA HVD: RSABE",
            "Thiết kế replicate cho phép ước tính độ biến thiên trong cá thể của thuốc đối chứng (sWR). Với sWR >= 0.294 (CVwR >= 30%) "
            "và các điều kiện profile phù hợp, tiêu chuẩn RSABE yêu cầu cận trên khoảng tin cậy 95% của thống kê chuẩn hóa Howe (scaled criterion UCB) <= 0, "
            "đồng thời GMR điểm (point estimate) phải nằm trong [0.80, 1.25]; khoảng tin cậy 90% thông thường được trình bày để tham khảo bổ trợ nhưng không thay thế tiêu chí UCB. "
            "Với sWR < 0.294, chuyển sang đánh giá conventional replicate ABE theo khoảng tin cậy 90% [80.00% – 125.00%]. "
            f"Căn cứ HVD: {field('hvd_justification')}. Cần đối chiếu dữ liệu replicate và hồ sơ nguồn.",
            "Replicate design allows estimation of within-subject reference variability (sWR). When sWR >= 0.294 (CVwR >= 30%) "
            "and profile conditions hold, RSABE requires the 95% upper confidence bound of the Howe scaled criterion <= 0, "
            "and point estimate GMR within [0.80, 1.25]; conventional 90% CI is presented as supplementary but does not replace the UCB test. "
            "When sWR < 0.294, conventional replicate ABE is evaluated with 90% CI [80.00% – 125.00%]. "
            f"HVD justification: {field('hvd_justification')}. Reconcile replicate data and source records.")
    elif rule == "EMA_NTI":
        add("8.5.2", "EMA NTI: giới hạn thu hẹp", "EMA NTI: narrowed limits",
            "Với AUC, áp dụng CI90 của GMR trong [0,90; 1,1111]. Cmax có thể dùng [0,80; 1,25] "
            "hoặc thu hẹp xuống [0,90; 1,1111] nếu có cơ sở an toàn/hiệu quả được quy định; "
            "tuyệt đối không áp dụng mở rộng giới hạn cho thuốc NTI. "
            f"Cờ yêu cầu thu hẹp Cmax: {field('nti_cmax_narrow')}. "
            "Căn cứ phân loại NTI, đề cương/SAP và guideline đặc thù sản phẩm phải được lưu giữ đầy đủ trong hồ sơ.",
            "AUC GMR 90% CI must fall in [0.90, 1.1111]. Cmax may use [0.80, 1.25] "
            "or narrower limits if specifically required by clinical/regulatory evidence; never scale NTI bounds wider. "
            f"Cmax narrowing flag: {field('nti_cmax_narrow')}. "
            "NTI justification, protocol/SAP and product-specific guidance must be documented.")
    elif rule == "FDA_NTI":
        add("8.5.2", "FDA NTI: tiêu chí replicate đặc thù", "FDA NTI: replicate criteria",
            "Yêu cầu bắt buộc thiết kế full replicate 4 kỳ (TRTR/RTRT); hồ sơ phải báo cáo GMR, tiêu chí scaled và conventional theo hướng dẫn FDA, "
            "đồng thời so sánh độ biến thiên trong cá thể giữa thử và đối chứng (sWT/sWR) với cận trên khoảng tin cậy 90% của tỷ số độ lệch chuẩn <= 2.5. "
            "Đánh giá tiêu chí conventional replicate ABE dựa trên khoảng tin cậy 90% [80.00% – 125.00%] kết hợp cùng tiêu chí scaled và so sánh biến thiên sWT/sWR để đưa ra kết luận tương đương sinh học.",
            "Mandatory 4-period full replicate design (TRTR/RTRT); report GMR, FDA scaled and conventional criteria, "
            "and within-subject variability comparison between test and reference (sWT/sWR) with upper 90% CI of SD ratio <= 2.5. "
            "Evaluate conventional replicate ABE criteria based on 90% CI [80.00% – 125.00%] combined with scaled criteria and sWT/sWR ratio to reach the bioequivalence decision.")
    elif "REPLICATE" in rule and "NONREPLICATE" not in rule:
        add("8.5.2", "ABE với thiết kế replicate", "Conventional replicate ABE",
            "Phân biệt số người tham gia với số quan sát phân liều; ước lượng hiệu ứng điều trị và các thành phần phương sai theo mô hình phù hợp. "
            "Đối với FDA replicate ABE, đánh giá khoảng tin cậy 90% của tỷ số trung bình nhân GMR theo khoảng chấp thuận 80.00% – 125.00% dựa trên số liệu phân tích thực tế.",
            "Separate participants from dosing observations; estimate treatment effects and variance components using an appropriate model. "
            "For FDA replicate ABE, evaluate 90% confidence interval of GMR against 80.00% – 125.00% acceptance limits based on actual analyzed data.")

    if not study.get("rule_set_id"):
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
        f"Giả định ban đầu về GMR, CVw, tỷ lệ bỏ cuộc, alpha, power mục tiêu và phương pháp ước tính: "
        f"{req_field('Giả định cỡ mẫu', 'Sample size assumptions', 'Nhập giả định CVw, GMR, dropout và phương pháp tính', 'Supply assumed CVw, GMR, dropout and calculation method')}. "
        "Power quan sát được sau nghiên cứu không thay thế cho chứng cứ BE. Phân biệt rõ dữ liệu thiếu thực sự với dữ liệu bị loại theo quy định SAP; "
        "trình bày đầy đủ số người tham gia, số quan sát và phân tích độ nhạy theo từng endpoint.",
        f"Prespecified assumptions for GMR, CVw, dropout rate, alpha, target power, and estimation method: "
        f"{req_field('Giả định cỡ mẫu', 'Sample size assumptions', 'Nhập giả định CVw, GMR, dropout và phương pháp tính', 'Supply assumed CVw, GMR, dropout and calculation method')}. "
        "Observed post-hoc power cannot establish bioequivalence. Clearly distinguish genuine missing data from excluded observations; "
        "document participant/observation counts and endpoint-specific sensitivity analyses.")

    add("8.6", "Phương pháp phân tích mẫu và thẩm định", "Bioanalytical method and validation",
        f"Phương pháp định lượng (LC-MS/MS), chất chuẩn nội, LLOQ, tính chọn lọc, khoảng đường chuẩn, độ đúng và độ chính xác trong ngày và giữa các ngày, "
        f"độ thu hồi, độ nhiễm chéo (carry-over), hiệu ứng nền (matrix effect), độ ổn định (trên bàn, đông-rã đông, dài hạn) và phân tích lại mẫu thực tế (ISR): "
        f"{req_field('Báo cáo thẩm định phương pháp bioanalytical', 'Bioanalytical validation report', 'Nhập chi tiết thẩm định theo ICH M10, SOP phân tích, nhật ký thiết bị, lô hóa chất và chứng nhận QC', 'Enter ICH M10 validation details, analytical SOPs, instrument logs, reagent lots and QC certifications')}. "
        "Bắt buộc truy xuất SOP, số serial thiết bị, lô hóa chất chuẩn và kết quả các mẫu QC trong từng đợt chạy; kết quả tính toán NCA không thay thế cho việc thẩm định phương pháp phân tích.",
        f"Quantification method (LC-MS/MS), internal standard, LLOQ, selectivity, calibration range, within-run and between-run accuracy/precision, "
        f"recovery, carry-over, matrix effect, stability (bench-top, freeze-thaw, long-term) and incurred sample reanalysis (ISR): "
        f"{req_field('Báo cáo thẩm định phương pháp bioanalytical', 'Bioanalytical validation report', 'Nhập chi tiết thẩm định theo ICH M10, SOP phân tích, nhật ký thiết bị, lô hóa chất và chứng nhận QC', 'Enter ICH M10 validation details, analytical SOPs, instrument logs, reagent lots and QC certifications')}. "
        "Traceability of analytical SOPs, instrument serial numbers, reference standards, and QC run acceptance is required; NCA outputs do not substitute for assay validation.")

    add("8.7", "Đảm bảo chất lượng và Data Integrity", "Quality assurance and data integrity",
        f"Nguồn gốc dữ liệu: {field('data_provenance')}; mục đích sử dụng: {field('data_purpose')}; "
        f"input_revision: {manifest.get('input_revision', '—')}; input_fingerprint: {manifest.get('input_fingerprint', '—')}. "
        "Rà soát tuân thủ nguyên tắc ALCOA+, phân quyền truy cập người dùng, lịch sử sửa đổi dữ liệu, đối chiếu phiên bản đề cương/SAP, "
        "nhật ký truy vết kiểm toán (audit trail), đối chiếu 100% dữ liệu gốc (SDV), biên bản khóa dữ liệu (data lock), "
        "sai lệch đề cương, hành động khắc phục/phòng ngừa (CAPA) và quy trình ký duyệt độc lập của bộ phận QA: "
        f"{req_field('Bằng chứng QA và Data Integrity', 'QA and Data Integrity evidence', 'Bổ sung chứng nhận thanh tra QA, thẩm định hệ thống máy tính CSV, kiểm soát phân quyền và chữ ký điện tử', 'Supply QA audit certificate, computerized system validation CSV, access control logs and e-signature records')}",
        f"Data provenance: {field('data_provenance')}; purpose: {field('data_purpose')}; "
        f"input_revision: {manifest.get('input_revision', '—')}; input_fingerprint: {manifest.get('input_fingerprint', '—')}. "
        "Review ALCOA+ compliance, role-based access control, amendment history, protocol/SAP version reconciliation, "
        "audit trail review, 100% source data verification (SDV), formal data lock records, "
        "deviations, CAPA, and independent QA sign-off: "
        f"{req_field('Bằng chứng QA và Data Integrity', 'QA and Data Integrity evidence', 'Bổ sung chứng nhận thanh tra QA, thẩm định hệ thống máy tính CSV, kiểm soát phân quyền và chữ ký điện tử', 'Supply QA audit certificate, computerized system validation CSV, access control logs and e-signature records')}")

    # 9. RESULTS AND DISCUSSION
    add("9", "KẾT QUẢ VÀ BÀN LUẬN", "RESULTS AND DISCUSSION")
    add("9.1", "Đặc điểm người tham gia và kết quả lâm sàng", "Demographics and clinical conduct",
        f"Đặc điểm nhân khẩu học: tuổi, giới tính, BMI, chủng tộc; số đối tượng tuyển chọn, phân bổ ngẫu nhiên, hoàn thành nghiên cứu, "
        f"thời gian dùng thuốc và lấy mẫu thực tế, các sai lệch đề cương phát sinh, thuốc dùng kèm, "
        f"theo dõi an toàn và báo cáo các biến cố bất lợi (AE/SAE): "
        f"{req_field('Kết quả lâm sàng và an toàn thực tế', 'Actual clinical and safety results', 'Nhập bảng đặc điểm nhân khẩu học, danh sách đối tượng hoàn tất/bỏ cuộc, danh sách AE/SAE và sai lệch đề cương thực tế', 'Supply demographic characteristics, subject disposition table, actual AE/SAE listings and deviation reports')}. "
        "Số lượng đối tượng và kỳ phân tích thực tế được trích xuất tự động từ snapshot trong các bảng phụ trợ bên dưới.",
        f"Demographic characteristics: age, sex, BMI, race; number of subjects screened, randomized, completed, "
        f"actual dosing and sampling times, protocol deviations, concomitant medications, "
        f"safety observations and adverse events (AE/SAE): "
        f"{req_field('Kết quả lâm sàng và an toàn thực tế', 'Actual clinical and safety results', 'Nhập bảng đặc điểm nhân khẩu học, danh sách đối tượng hoàn tất/bỏ cuộc, danh sách AE/SAE và sai lệch đề cương thực tế', 'Supply demographic characteristics, subject disposition table, actual AE/SAE listings and deviation reports')}. "
        "Actual analysis population and period counts are extracted from the locked snapshot in the review tables below.")

    add("9.2", "Kết quả định lượng mẫu sinh học", "Bioanalytical results",
        f"Kết quả phân tích mẫu thực tế: tỷ lệ mẫu BLQ, các mẫu phải phân tích lại và lý do, độ chấp nhận của các mẻ phân tích (analytical runs) "
        f"dựa trên mẫu chuẩn và mẫu QC, sai lệch nhiệt độ bảo quản (nếu có), kết quả kiểm tra ISR, "
        f"sắc ký đồ đại diện và quyết định nghiệm thu kết quả phân tích: "
        f"{req_field('Kết quả bioanalytical thực tế', 'Actual bioanalytical results', 'Nhập tỷ lệ BLQ, tóm tắt phân tích lại mẫu, kết quả ISR, tỷ lệ đạt QC và sắc ký đồ đại diện', 'Supply BLQ fraction, repeat analysis summary, ISR results, QC run acceptance and representative chromatograms')}. "
        "Bảng nồng độ gốc đã được thẩm định và nhật ký chạy mẫu cần được đính kèm đầy đủ tại Phụ lục.",
        f"Bioanalytical performance: fraction of BLQ samples, repeat sample analysis and reasons, run acceptance based on calibration "
        f"standards and QC samples, storage temperature deviations if any, ISR reanalysis results, "
        f"representative chromatograms and final analytical batch approval: "
        f"{req_field('Kết quả bioanalytical thực tế', 'Actual bioanalytical results', 'Nhập tỷ lệ BLQ, tóm tắt phân tích lại mẫu, kết quả ISR, tỷ lệ đạt QC và sắc ký đồ đại diện', 'Supply BLQ fraction, repeat analysis summary, ISR results, QC run acceptance and representative chromatograms')}. "
        "Complete validated concentration listings and run logs must be attached in the Appendices.")

    add("9.3", "Kết quả PK cá thể và mô tả", "Individual and descriptive PK results",
        "Trình bày chi tiết các thông số Cmax, Tmax, AUC0–t, AUC0–∞, λz, t½ và %AUC ngoại suy theo từng đối tượng, từng kỳ và từng thuốc điều trị (T/R); "
        "các chỉ số thống kê mô tả: trung bình số học, độ lệch chuẩn (SD), hệ số biến thiên (CV%), trung vị, nhỏ nhất – lớn nhất, "
        "trung bình nhân (Geometric mean) và CV nhân. "
        "Đồ thị nồng độ–thời gian trung bình và từng cá thể được thể hiện ở cả hai thang đo tuyến tính và bán logarit; "
        "nhận xét về các mẫu bất thường và mọi can thiệp điều chỉnh pha cuối hồi quy.",
        "Report individual parameters Cmax, Tmax, AUC0–t, AUC0–∞, λz, t½ and %AUC extrapolated by subject, period and treatment (T/R); "
        "descriptive statistics: arithmetic mean, standard deviation (SD), coefficient of variation (CV%), median, min–max, "
        "geometric mean and geometric CV%. "
        "Mean and individual concentration–time profiles are plotted on both linear and semi-logarithmic scales; "
        "outlier concentrations and all audited terminal-phase adjustments are documented.")

    add("9.4", "Kết quả thống kê tương đương sinh học", "Bioequivalence statistical results",
        f"Phương pháp: {method}; kết luận snapshot: {result_label}. "
        "Các bảng tiếp theo trình bày chi tiết tỷ số trung bình nhân GMR, khoảng tin cậy 90% (CI90), quyết định cho từng endpoint, "
        "tiêu chí scaling/độ biến thiên (sWR, sWT, Howe UCB95), số lượng đối tượng trong mô hình, bảng thống kê PK mô tả và danh sách dữ liệu theo kỳ. "
        "Kết luận tương đương sinh học được xác định dựa trên việc toàn bộ khoảng tin cậy 90% và các tiêu chuẩn quy định có thỏa mãn tiêu chí chấp thuận hay không. "
        "Phân tích độ nhạy và đánh giá tác động của sai lệch đề cương cần được bổ sung khi có hồ sơ lâm sàng hoàn chỉnh.",
        f"Statistical methodology: {method}; snapshot analysis decision: {result_label}. "
        "The following tables present point estimate GMR, 90% confidence intervals, endpoint-specific decisions, "
        "scaling and variability criteria (sWR, sWT, Howe UCB95), model population counts, descriptive PK summaries, and period listings. "
        "The bioequivalence decision is determined based on whether 90% confidence intervals and regulatory criteria fully satisfy the acceptance standards. "
        "Sensitivity analyses and impact of protocol deviations must be added from complete clinical source records.")

    add("9.4.1", "Bảng kết quả từ snapshot đã khóa", "Locked-snapshot result tables",
        "Các bảng kết quả thống kê và dược động học dưới đây được sinh tự động và bất biến từ snapshot đã khóa theo analysis_run_id và mã băm toàn vẹn. "
        "Tiêu đề, đơn vị tính, số lượng người tham gia, số lần phân liều lặp lại và từng tiêu chí độc lập phải được rà soát và xác nhận trước khi phê duyệt.",
        "The following statistical and pharmacokinetic result tables are generated automatically from the locked snapshot by analysis_run_id and hashes. "
        "Headers, units, participant counts, replicate observations, and individual regulatory gates must be reviewed and certified prior to sign-off.")

    add("9.5", "Diễn giải, độ nhạy và giới hạn", "Interpretation, sensitivity and limitations",
        "Phân biệt rõ ràng giữa ý nghĩa thống kê và ý nghĩa lâm sàng của kết quả. Thảo luận chi tiết về mức độ chênh lệch sinh khả dụng giữa T và R, "
        "độ biến thiên trong cá thể quan sát được (CVw) so với y văn, khả năng ngoại suy kết quả, tác động của các mẫu BLQ, giá trị ngoại lệ (outlier), "
        "dữ liệu thiếu, các giả định của mô hình thống kê, độ nhạy đối với việc lựa chọn điểm hồi quy pha cuối và giới hạn khái quát hóa của nghiên cứu. "
        "Tuyệt đối không tự ý loại trừ dữ liệu outlier khỏi phân tích chính nếu không có căn cứ kỹ thuật được ghi nhận trước.",
        "Carefully distinguish statistical significance from clinical relevance. Discuss bioavailability differences between T and R, "
        "observed within-subject variability (CVw) versus literature, extrapolation of findings, impact of BLQ samples, outliers, "
        "missing observations, model assumptions, sensitivity to terminal-phase regression points, and generalizability limitations. "
        "Outliers must never be discarded from the primary analysis without objective, prespecified technical or clinical grounds.")

    # 10. CONCLUSION AND RECOMMENDATIONS
    add("10", "KẾT LUẬN VÀ KHUYẾN NGHỊ", "CONCLUSION AND RECOMMENDATIONS",
        f"Kết luận tương đương sinh học theo snapshot phân tích: {result_label}. Trạng thái rà soát độc lập: {run.get('review_status', 'chưa rà soát' if vi else 'unreviewed')}. "
        "Nghiên cứu sử dụng dữ liệu mô phỏng, dữ liệu đào tạo hoặc thiếu hồ sơ kiểm chứng không thể dùng để khẳng định tương đương sinh học cấp nghiên cứu thực tế. "
        "Bắt buộc có kết luận riêng biệt cho từng endpoint chính (Cmax, AUC0-t) và các điều kiện bắt buộc trước khi kết luận tổng thể; "
        "kết luận chính thức chỉ được xác lập sau khi hoàn tất rà soát độc lập của các chuyên gia QA, Dược động học, Thống kê sinh học và Đăng ký thuốc. "
        "Bản dự thảo này phục vụ rà soát kỹ thuật, chưa phải là chứng nhận CSR/eCTD hoàn chỉnh.",
        f"Bioequivalence conclusion according to analysis snapshot: {result_label}. Independent review status: {run.get('review_status', 'unreviewed')}. "
        "Studies based on synthetic data, training data, or incomplete source records cannot support a real-study bioequivalence claim. "
        "Separate conclusions are mandatory for each primary endpoint (Cmax, AUC0-t) and prerequisite criteria before reaching an overall conclusion; "
        "official conclusion is established only after independent multi-disciplinary sign-off by QA, PK, Biostatistics and Regulatory Affairs. "
        "This draft serves technical review and does not constitute a certified CSR/eCTD submission.")

    add("10.1", "Các điều kiện chặn và công việc còn thiếu", "Blocking conditions and outstanding work",
        (blockers_text or ("Không có blocker kỹ thuật được ghi nhận trong snapshot; vẫn bắt buộc rà soát hồ sơ độc lập." if vi else "No stored blockers in snapshot; independent review still mandatory.")) +
        f" Bằng chứng xác nhận lâm sàng/kiểm nghiệm/QA/chữ ký phê duyệt còn thiếu: {req_field('Hồ sơ xác nhận còn thiếu', 'Outstanding verification items', 'Bổ sung các tài liệu phê duyệt, hồ sơ gốc và chữ ký còn thiếu trước khi nộp', 'Supply missing approvals, source records and signatures before filing')}",
        (blockers_text or ("No stored blockers in snapshot; independent review still mandatory." if not vi else "Không có blocker kỹ thuật được ghi nhận trong snapshot; vẫn bắt buộc rà soát hồ sơ độc lập.")) +
        f" Outstanding clinical/assay/QA/signature confirmations: {req_field('Hồ sơ xác nhận còn thiếu', 'Outstanding verification items', 'Bổ sung các tài liệu phê duyệt, hồ sơ gốc và chữ ký còn thiếu trước khi nộp', 'Supply missing approvals, source records and signatures before filing')}")

    # 11. APPENDICES, TRACEABILITY AND REFERENCES
    add("11", "PHỤ LỤC, TRUY XUẤT VÀ TÀI LIỆU THAM KHẢO", "APPENDICES, TRACEABILITY AND REFERENCES")
    for n, tv, te, bv, be in [
        ("11.1", "Protocol, SAP, phê duyệt và hồ sơ lâm sàng", "Protocol, SAP, approvals and clinical records",
         "Đề cương nghiên cứu và các văn bản sửa đổi đã được phê duyệt, SAP có chữ ký trước khi khóa dữ liệu, văn bản chấp thuận của Hội đồng Đạo đức (IRB/IEC), "
         "phiếu thông tin và mẫu chấp thuận tham gia nghiên cứu (ICF), bệnh án nghiên cứu (CRF/eCRF), sơ đồ ngẫu nhiên hóa, báo cáo theo dõi đối tượng, "
         "nhật ký sai lệch đề cương (deviations), danh sách biến cố bất lợi (AE/SAE), chứng từ cấp phát và thu hồi thuốc nghiên cứu, Giấy chứng nhận phân tích (CoA)",
         "Approved study protocol and formal amendments, signed and dated SAP prior to database lock, Ethics Committee (IRB/IEC) approval letters, "
         "subject information sheet and informed consent form (ICF) templates, CRF/eCRF specimen, randomization schedule, participant disposition logs, "
         "protocol deviation logs, AE/SAE listings, investigational product accountability records, and Certificates of Analysis (CoA)"),
        ("11.2", "Thẩm định bioanalytical và chromatogram", "Bioanalytical validation and chromatograms",
         "Báo cáo thẩm định phương pháp phân tích sinh học đầy đủ theo ICH M10, quy trình thao tác chuẩn (SOP), nhật ký chạy mẫu chuẩn và mẫu QC, "
         "đường chuẩn nồng độ, sắc ký đồ đại diện (tối thiểu 20% đối tượng gồm mẫu trắng, LLOQ, Cmax, mẫu tái phân tích ISR), "
         "báo cáo độ ổn định mẫu và báo cáo kiểm tra tính tái lập trên mẫu thực tế (ISR)",
         "Full bioanalytical method validation report under ICH M10, analytical SOPs, calibration standards and QC run logs, "
         "representative chromatograms (at least 20% of subjects including blank, LLOQ, Cmax, and ISR reanalysis samples), "
         "sample stability reports, and Incurred Sample Reanalysis (ISR) report"),
        ("11.3", "Báo cáo phân tích và dữ liệu gốc", "Analytical report and raw data",
         "Sổ tay phân tích mẫu sinh học, bảng nồng độ đo được kèm thời điểm lấy mẫu thực tế, LLOQ và ghi chú BLQ, báo cáo các lần chạy mẫu bị loại hoặc bất thường, "
         "tập dữ liệu gốc (raw dataset), tập dữ liệu đã thẩm định (validated dataset) và nhật ký audit trail của hệ thống phân tích",
         "Bioanalytical study report, measured concentration listings with actual sampling times, LLOQ and BLQ flags, run failure and exception reports, "
         "raw datasets, validated analysis datasets, and computerized system audit trails"),
        ("11.4", "Chứng nhận cơ sở và kiểm soát chất lượng", "Facility and quality certificates",
         "Chứng chỉ Thực hành tốt thử nghiệm lâm sàng (GCP) của cơ sở nghiên cứu, chứng nhận GLP/ISO 17025 của phòng phân tích sinh học, "
         "hồ sơ năng lực nghiên cứu viên, biên bản hiệu chuẩn và bảo dưỡng thiết bị phân tích, chứng nhận thẩm định hệ thống máy tính (CSV) và báo cáo thanh tra của bộ phận Đảm bảo chất lượng (QA)",
         "Clinical site GCP accreditation, bioanalytical laboratory GLP/ISO 17025 certificates, investigator qualifications, "
         "analytical instrument calibration and maintenance records, Computerised System Validation (CSV) certificates, and QA audit certificates"),
        ("11.5", "Hòa tan và liên quan các hàm lượng", "Dissolution and strength proportionality",
         "Hồ sơ so sánh độ hòa tan in vitro giữa thuốc thử và thuốc đối chứng ở các dải pH sinh lý, công thức thành phần các hàm lượng đăng ký, "
         "tính toán hệ số tương đồng f2 và hồ sơ đề nghị miễn thử tương đương sinh học in vivo cho các hàm lượng khác (biowaiver justification) nếu áp dụng",
         "In vitro comparative dissolution profiles of test vs reference across physiological pH media, formulation composition of registered strengths, "
         "f2 similarity factor calculations, and biowaiver justification documentation for additional strengths where applicable"),
        ("11.6", "Dữ liệu PK, bảng ANOVA và đồ thị", "PK listings, model tables and plots",
         "Bảng liệt kê toàn bộ thông số PK cá thể, bảng thống kê mô tả theo từng nhóm xử lý, đồ thị nồng độ–thời gian ở thang tuyến tính và bán logarit, "
         "kết quả chẩn đoán mô hình thống kê, bảng ANOVA chi tiết (LS means, SE, bậc tự do, MSE, F-test, p-value), khoảng tin cậy 90% và các chỉ số scaling đặc thù",
         "Complete individual PK parameter listings, descriptive statistics tables by treatment, linear and semi-log concentration–time plots, "
         "statistical model diagnostic outputs, detailed ANOVA tables (LS means, SE, degrees of freedom, MSE, F-tests, p-values), 90% CIs, and scaled criterion metrics"),
        ("11.7", "Bảng đối chiếu CTD và kiểm tra nộp hồ sơ", "CTD mapping and submission checks",
         "Bảng đối chiếu cấu trúc báo cáo với hướng dẫn ICH E3, Hồ sơ kỹ thuật chung CTD Module 2.7.1 (Tóm tắt nghiên cứu sinh dược học) và Module 5.3.1.2 (Báo cáo nghiên cứu sinh khả dụng và tương đương sinh học so sánh); "
         "danh mục kiểm tra tính đầy đủ của hồ sơ điện tử eCTD trước khi nộp",
         "Cross-reference mapping to ICH E3, Common Technical Document (CTD) Module 2.7.1 (Biopharmaceutic Studies Summary) and Module 5.3.1.2 (Comparative BA/BE Study Reports); "
         "complete eCTD submission readiness checklist"),
    ]:
        add(n, tv, te,
            f"{bv}: {req_field(tv, te, bv, be)}",
            f"{be}: {req_field(tv, te, bv, be)}")

    add("11.8", "Dấu vết tính toán và phiên bản", "Calculation traceability and versions",
        f"analysis_run_id: {run.get('analysis_run_id', '—')}; dataset_hash: {run.get('dataset_hash', '—')}; "
        f"raw_hash: {run.get('raw_hash', '—')}; config_hash: {run.get('config_hash', '—')}; "
        f"snapshot_hash: {run.get('snapshot_hash', '—')}; engine_version: {run.get('engine_version', '—')}. "
        "Bắt buộc kiểm tra tính toàn vẹn dữ liệu, đối chiếu mã băm (hash) và chứng minh khả năng tái lập kết quả tính toán độc lập ngoài ứng dụng.",
        f"analysis_run_id: {run.get('analysis_run_id', '—')}; dataset_hash: {run.get('dataset_hash', '—')}; "
        f"raw_hash: {run.get('raw_hash', '—')}; config_hash: {run.get('config_hash', '—')}; "
        f"snapshot_hash: {run.get('snapshot_hash', '—')}; engine_version: {run.get('engine_version', '—')}. "
        "Verify data integrity, cryptographic hashes, and independent computational reproducibility against original source records.")

    add("11.9", "Nguồn quy định và phạm vi áp dụng", "Guidance references and applicability",
        "Cấu trúc báo cáo được chuẩn hóa theo ICH E3 và định dạng báo cáo BE quốc tế (ASEAN ACCSQ PPWG / EMA / FDA). "
        f"Bộ quy tắc phân tích đang áp dụng: {rule}; các nguồn hướng dẫn chính thức trong snapshot: " +
        "; ".join(run.get("rule_snapshot", {}).get("sources", [])) +
        ". Danh mục hướng dẫn áp dụng bắt buộc rà soát: ICH M13A (Bioequivalence for IR Solid Oral Forms, 2024), "
        "ICH M10 (Bioanalytical Method Validation, 2022), ICH E6(R3) (GCP), ICH E8(R1), ICH E9/E9(R1), "
        "FDA Guidance for Industry: Bioequivalence Studies with Pharmacokinetic Endpoints for Drugs Submitted Under an ANDA (2021), "
        "FDA Statistical Approaches to Establishing Bioequivalence (2001 / draft update), "
        "EMA Guideline on the Investigation of Bioequivalence (CPMP/EWP/QWP/1401/98 Rev. 1/ Corr **, 2010), "
        "và Product-Specific Guidances (PSG) liên quan.",
        "Reporting structure standardized in accordance with ICH E3 and international BE study report guidelines (ASEAN / EMA / FDA). "
        f"Selected regulatory rule set: {rule}; official references in snapshot: " +
        "; ".join(run.get("rule_snapshot", {}).get("sources", [])) +
        ". Applicable guidelines to verify: ICH M13A (Bioequivalence for IR Solid Oral Forms, 2024), "
        "ICH M10 (Bioanalytical Method Validation, 2022), ICH E6(R3) (GCP), ICH E8(R1), ICH E9/E9(R1), "
        "FDA Guidance for Industry: Bioequivalence Studies with Pharmacokinetic Endpoints for Drugs Submitted Under an ANDA (2021), "
        "FDA Statistical Approaches to Establishing Bioequivalence (2001 / draft update), "
        "EMA Guideline on the Investigation of Bioequivalence (CPMP/EWP/QWP/1401/98 Rev. 1/ Corr **, 2010), "
        "and applicable Product-Specific Guidances (PSGs).")

    # Table of Contents compilation into Section 3
    index = "\n".join(s["title"] for s in sections if s["level"] <= 2 and s["number"] != "3")
    index += "\n" + ("11.10 Phụ lục bảng dữ liệu tính toán" if vi else "11.10 Analysis data tables")
    index += "\n" + ("11.11 Nguồn và truy xuất" if vi else "11.11 References and traceability")
    index += "\n" + ("11.12 Hình và đồ thị minh họa" if vi else "11.12 Figures and visualizations")
    next(s for s in sections if s["number"] == "3")["body"] += "\n" + index
    return sections
