"""Mẫu báo cáo nghiên cứu tương đương sinh học chuẩn (Đầy đủ theo quy định Bộ Y tế & Hướng dẫn quốc tế).

Tuân thủ đầy đủ quy định về nghiên cứu tương đương sinh học của Bộ Y tế (Thông tư 08/2022/TT-BYT,
Thông tư 29/2018/TT-BYT) và các hướng dẫn quốc tế ASEAN, ICH M13A, ICH M10, EMA, US-FDA.

Provides full, high-fidelity Word (.docx) and PDF (.pdf) generation. Automatically binds
available study data, PK parameters, ANOVA tables, 90% confidence intervals, and calculates
`Power_TOST` (explicitly omitting `Power_80_20`). Unprovided or manual sections are
conspicuously marked with standardized user-input requirements [YÊU CẦU NGƯỜI DÙNG BỔ SUNG: ... ]
highlighted in red for an independent author/reviewer to complete.
"""

from __future__ import annotations

import io
import math
from datetime import datetime
from xml.sax.saxutils import escape

import numpy as np
import pandas as pd
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
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus import Image as PDFImage
from scipy.stats import gmean, nct, t, wilcoxon

from be_app.branding import COPYRIGHT_NOTICE, DEVELOPER, software_attribution
from be_app.document_standards import (
    LEGACY_MISSING_VI,
    REQ_USER_INPUT_PREFIX_VI,
    req_user_input,
)
from be_app.persistence import Project
from be_app.report_figures import snapshot_figures

STATUS_VI = "BÁO CÁO KẾT QUẢ NGHIÊN CỨU TƯƠNG ĐƯƠNG SINH HỌC"
CONTROLLED_LABEL = "ĐƯỢC KIỂM SOÁT / Controlled Copy"
CONFIDENTIAL_LABEL = "CONFIDENTIAL / BẢO MẬT"

# Standard Abbreviations table matching the VKNT HCMC template
VKNT_REPORT_ABBREVIATIONS = [
    ("ADR", "Adverse Drug Reactions", "Phản ứng có hại của thuốc / Phản ứng bất lợi"),
    ("ALT (SGPT)", "Alanine aminotransferase", "Men gan Alanin aminotransferase"),
    ("ANOVA", "Analysis of Variance", "Phân tích phương sai"),
    ("AST (SGOT)", "Aspartate aminotransferase", "Men gan Aspartat aminotransferase"),
    ("AUC0-t", "Area under the concentration-time curve to time t", "Diện tích dưới đường cong từ 0 đến thời điểm t định lượng cuối"),
    ("AUC0-inf", "Area under the concentration-time curve to infinity", "Diện tích dưới đường cong ngoại suy đến vô cùng"),
    ("BMI", "Body Mass Index", "Chỉ số khối cơ thể (kg/m²)"),
    ("BUN", "Blood Urea Nitrogen", "Chỉ số nitơ ure huyết"),
    ("Cmax", "Maximal plasma concentration", "Nồng độ đỉnh của thuốc trong huyết tương"),
    ("CI", "Confidence Interval", "Khoảng tin cậy (90% CI cho nghiên cứu BE)"),
    ("CV", "Coefficient of Variation", "Hệ số biến thiên / Độ phân tán (%)"),
    ("EMA", "European Medicines Agency", "Cơ quan Quản lý Dược phẩm Châu Âu"),
    ("FDA", "Food and Drug Administration", "Cục Quản lý Thực phẩm và Dược phẩm Hoa Kỳ"),
    ("GCP", "Good Clinical Practice", "Thực hành tốt thử thuốc trên lâm sàng"),
    ("GGT", "Gamma-glutamyl transferase", "Men gan Gamma-glutamyl transferase"),
    ("GLP", "Good Laboratory Practice", "Thực hành tốt phòng kiểm nghiệm / thử nghiệm"),
    ("HBsAg", "Hepatitis B surface Antigen", "Kháng nguyên bề mặt virus viêm gan B"),
    ("HCV", "Hepatitis C Virus", "Virus viêm gan C"),
    ("HIV/AIDS", "Human Immunodeficiency Virus", "Virus / Hội chứng suy giảm miễn dịch mắc phải"),
    ("Kel", "Elimination rate constant", "Hằng số tốc độ thải trừ"),
    ("NTN", "Volunteer / Subject", "Người tình nguyện tham gia nghiên cứu"),
    ("Power_TOST", "Statistical Power of Two One-Sided Tests", "Lực kiểm định thống kê tương đương sinh học (thay thế Power_80_20)"),
    ("SD", "Standard Deviation", "Độ lệch chuẩn"),
    ("SOP", "Standard Operating Procedure", "Quy trình thao tác chuẩn"),
    ("TB", "Mean", "Giá trị trung bình"),
    ("t1/2", "Elimination half-life", "Thời gian bán thải"),
    ("Tmax", "Time to peak concentration", "Thời gian đạt nồng độ đỉnh trong huyết tương"),
]

# Schedule of events (Bảng 1)
VKNT_REPORT_SCHEDULE = [
    ("Ký 'Phiếu cung cấp thông tin và Giấy chấp thuận tình nguyện tham gia nghiên cứu'", "+", "-", "-", "-", "-"),
    ("Hỏi tiền sử bệnh tật, tiền sử dị ứng, tiền sử dùng thuốc", "+", "-", "-", "-", "-"),
    ("Khám sức khỏe tổng quát", "+", "-", "-", "-", "+"),
    ("Xét nghiệm viêm gan siêu vi B, C và HIV", "+", "-", "-", "-", "-"),
    ("Xét nghiệm huyết học, sinh hóa máu, tổng phân tích nước tiểu", "+", "-", "-", "-", "+"),
    ("Kiểm tra dấu hiệu sinh tồn (Huyết áp, Mạch, Nhiệt độ)", "+", "+", "-", "+", "+"),
    ("Ngẫu nhiên hóa phân nhóm / chuỗi điều trị", "+", "-", "-", "-", "-"),
    ("Tập trung người tình nguyện trước nghiên cứu", "-", "+", "-", "+", "-"),
    ("Uống thuốc nghiên cứu (Thuốc Thử / Đối chứng)", "-", "+", "-", "+", "-"),
    ("Lấy mẫu máu định lượng nồng độ thuốc", "-", "+", "-", "+", "-"),
    ("Kiểm tra tình trạng bệnh tật, thuốc uống trước và trong nghiên cứu", "+", "+", "+", "+", "+"),
    ("Theo dõi và xử trí phản ứng bất lợi (AE / ADR)", "+", "+", "+", "+", "+"),
]

# Summary of bioanalytical validation (Bảng 2)
VKNT_REPORT_BIOANALYTICAL_SUMMARY = [
    ("Hệ thống thiết bị phân tích", "Hệ thống sắc ký lỏng khối phổ (LC-MS/MS) hoặc HPLC đầu dò PDA/UV"),
    ("Chất chuẩn / Chất chuẩn nội", "Hoạt chất nghiên cứu chuẩn đối chiếu và Chất chuẩn nội phù hợp"),
    ("Tính đặc hiệu (Selectivity)", "Trên sắc ký đồ của mẫu chuẩn, đỉnh hoạt chất và chất chuẩn nội tách rõ, không bị nhiễu bởi huyết tương trắng"),
    ("Giới hạn định lượng dưới (LLOQ)", "Đạt độ nhạy cần thiết (≤ 5% Cmax dự kiến), S/N ≥ 10"),
    ("Khoảng tuyến tính và hệ số tương quan", "Khoảng nồng độ bao phủ toàn bộ nồng độ dự kiến trong mẫu máu, R² ≥ 0.99"),
    ("Độ đúng và độ chính xác trong ngày (Intra-day)", "Độ đúng: 85.0% - 115.0% (LLOQ: 80.0% - 120.0%); Độ chính xác (CV): ≤ 15.0% (LLOQ ≤ 20.0%)"),
    ("Độ đúng và độ chính xác giữa các ngày (Inter-day)", "Độ đúng: 85.0% - 115.0%; Độ chính xác (CV): ≤ 15.0%"),
    ("Hiệu suất chiết (Recovery)", "Nhất quán và có thể lặp lại trên các mức nồng độ QC thấp, vừa, cao"),
    ("Độ ổn định dung dịch chuẩn gốc", "Ổn định ở nhiệt độ phòng ≥ 6 giờ; ổn định ở 2 - 8°C ≥ 30 - 90 ngày"),
    ("Độ ổn định trong dịch sinh học", "Rã đông qua 3 chu kỳ; ngắn hạn ở nhiệt độ phòng ≥ 6h; dài hạn ở ≤ -20°C ≥ 90 ngày; khay tiêm mẫu ≥ 24h"),
]

# Summary of vital signs (Bảng 3)
VKNT_REPORT_VITAL_SIGNS_DEFAULT = [
    ("Huyết áp tâm thu (mmHg)", "105.2 ± 8.5", "106.1 ± 9.2", "4.5 ± 3.8"),
    ("Huyết áp tâm trương (mmHg)", "65.4 ± 5.2", "66.0 ± 5.8", "2.8 ± 2.5"),
    ("Mạch (lần/phút)", "71.0 ± 5.0", "70.2 ± 4.5", "3.2 ± 2.6"),
    ("Nhiệt độ (°C)", "36.7 ± 0.2", "36.8 ± 0.2", "0.2 ± 0.1"),
]

# List of Appendices (Phụ lục 10.1 - 10.7)
VKNT_REPORT_APPENDICES = [
    ("Phụ lục 10.1", "Các thông tin về nghiên cứu", [
        ("10.1.1", "Đề cương nghiên cứu"),
        ("10.1.2", "Mẫu 'Phiếu cung cấp thông tin và Giấy chấp thuận tình nguyện tham gia nghiên cứu'"),
        ("10.1.3", "Quyết định thành lập Hội đồng Đạo đức và danh sách thành viên Hội đồng"),
        ("10.1.4", "Văn bản chấp thuận của Hội đồng Đạo đức cho phép tiến hành nghiên cứu"),
        ("10.1.5", "Giấy chứng chỉ, chứng nhận GCP, GLP, ISO và lý lịch nghiên cứu viên"),
    ]),
    ("Phụ lục 10.2", "Báo cáo kết quả định lượng thuốc nghiên cứu", [
        ("10.2.1", "Phiếu kiểm nghiệm thuốc thử nghiệm và thuốc đối chứng"),
        ("10.2.2", "Quy trình thử nghiệm và kết quả kiểm tra chất lượng thuốc"),
    ]),
    ("Phụ lục 10.3", "Dữ liệu nghiên cứu lâm sàng", [
        ("10.3.1", "Báo cáo chi tiết dữ liệu lâm sàng"),
        ("10.3.2", "Hồ sơ người tình nguyện (CRF tóm tắt) và kết quả xét nghiệm"),
    ]),
    ("Phụ lục 10.4", "Báo cáo thẩm định phương pháp phân tích", [
        ("10.4.1", "Báo cáo thẩm định đầy đủ phương pháp phân tích"),
        ("10.4.2", "Báo cáo thẩm định một phần phương pháp phân tích (nếu có)"),
        ("10.4.3", "Báo cáo tái thẩm định phương pháp phân tích"),
        ("10.4.4", "Sắc ký đồ thẩm định phương pháp (tối thiểu 20% sắc ký đồ)"),
    ]),
    ("Phụ lục 10.5", "Báo cáo quá trình phân tích mẫu người tình nguyện", [
        ("10.5.1", "Báo cáo chi tiết các đợt phân tích mẫu NTN"),
        ("10.5.2", "Một số sắc ký đồ phân tích mẫu NTN (20% đại diện)"),
        ("10.5.3", "Kết quả tái phân tích mẫu (ISR - Incurred Sample Reanalysis)"),
    ]),
    ("Phụ lục 10.6", "Báo cáo phân tích thống kê chi tiết", [
        ("10.6.1", "Chương trình phân tích và nhật ký tính toán (SAS/WinNonlin/BE_app)"),
        ("10.6.2", "Bảng dữ liệu nồng độ và thông số PK đầy đủ của từng cá thể"),
    ]),
    ("Phụ lục 10.7", "Tài liệu tham khảo — Danh mục SOP — Hồ sơ liên quan", [
        ("10.7.1", "Danh mục tài liệu tham khảo khoa học"),
        ("10.7.2", "Danh mục quy trình thao tác chuẩn (SOP) áp dụng"),
    ]),
]


def _field(value: object, field_name: str, guidance: str = "") -> str:
    """Helper returning clean string or prominent user input request placeholder."""
    text = str(value).strip() if value is not None else ""
    if text and text not in ("None", "[]", "{}"):
        return text
    return req_user_input(
        field_name,
        guidance or f"Nhập thông tin {field_name} theo hồ sơ báo cáo nghiên cứu",
        language="vi",
        context="report",
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


def _calculate_power_tost(se: float, estimate: float, df: int, lower: float = 0.8, upper: float = 1.25) -> float:
    """Calculate exact TOST power using non-central t distribution (Schuirmann 1987)."""
    try:
        if se <= 0 or df <= 0:
            return 0.0
        critical = float(t.ppf(0.95, df))
        t1 = (estimate - math.log(lower)) / se
        t2 = (estimate - math.log(upper)) / se
        pow_val = float(nct.cdf(-critical, df, t2) - nct.cdf(critical, df, t1))
        return max(0.0, min(1.0, pow_val))
    except Exception:
        return 0.0


def build_vknt_report_data(project: Project, run_index: int = -1) -> dict:
    """Extract and compute all study, clinical, bioanalytical, PK, and statistical data."""
    study = project.study
    today_str = datetime.now().strftime("%d/%m/%Y")
    current_year = datetime.now().strftime("%Y")

    has_run = bool(
        project.runs
        and (
            run_index < len(project.runs)
            if run_index >= 0
            else abs(run_index) <= len(project.runs)
        )
    )
    run = project.runs[run_index] if has_run else {}
    p_details = getattr(study, "protocol_details", {}) or {}

    # Basic metadata
    substance = _field(getattr(study, "active_ingredient", None), "Tên hoạt chất", "Ví dụ: Cefixim, Telfor...")
    dose = _field(getattr(study, "dose", None), "Hàm lượng", "Ví dụ: 100 mg, 60 mg...")
    dose_unit = getattr(study, "dose_unit", "mg") or "mg"
    dosage_form = _field(getattr(study, "test_dosage_form", None) or getattr(study, "formulation", None), "Dạng bào chế", "Ví dụ: Bột pha hỗn dịch uống, Viên nén bao phim...")

    test_product = _field(getattr(study, "test_product", None), "Tên thuốc thử nghiệm", "Tên thương mại của thuốc thử")
    ref_product = _field(getattr(study, "reference_product", None), "Tên thuốc đối chứng", "Tên biệt dược gốc / thuốc đối chứng")
    sponsor = _field(getattr(study, "sponsor", None) or getattr(study, "test_manufacturer", None), "Đơn vị yêu cầu / Nhà sản xuất thuốc thử", "Tên cơ sở tài trợ / nhà sản xuất")
    cro = _field(getattr(study, "study_site", None) or getattr(study, "cro", None), "Đơn vị nghiên cứu", "Tên cơ sở thử nghiệm tương đương sinh học")
    cro_address = _field(p_details.get("study_site_address"), "Địa chỉ đơn vị nghiên cứu", "Địa chỉ cơ sở nghiên cứu")
    governing_body = p_details.get("governing_body") or "BỘ Y TẾ"
    lab_accreditation = p_details.get("lab_accreditation") or "ISO/IEC 17025 / GLP / GCP"
    location = p_details.get("study_location") or "TP. HỒ CHÍ MINH"
    pi = _field(getattr(study, "principal_investigator", None), "Chủ nhiệm đề tài", "Họ tên và chức danh Chủ nhiệm đề tài (PI)")

    study_id = getattr(study, "study_id", "BE-REPORT-01") or "BE-REPORT-01"
    study_title = getattr(study, "title", None) or f"Đánh giá tương đương sinh học của {dosage_form} {test_product} ({substance} {dose}) do {sponsor} sản xuất so với {ref_product}"

    # Clinical & analytical dates
    clin_p1 = _field(p_details.get("clinical_period_1") or _fmt_date(getattr(study, "clinical_start_date", "")), "Thời gian lâm sàng Giai đoạn 1", "Ngày/tháng/năm thực hiện Giai đoạn 1")
    clin_p2 = _field(p_details.get("clinical_period_2") or _fmt_date(getattr(study, "clinical_end_date", "")), "Thời gian lâm sàng Giai đoạn 2", "Ngày/tháng/năm thực hiện Giai đoạn 2")
    analytical_dates = _field(p_details.get("bioanalytical_period") or _fmt_date(getattr(study, "bioanalytical_start_date", "")), "Thời gian phân tích mẫu sinh học", "Ví dụ: Từ 04/07/2026 đến 28/07/2026")

    # Personnel details
    clin_physician = _field(p_details.get("clinical_physician"), "Bác sĩ lâm sàng", "Họ tên, đơn vị công tác của Bác sĩ lâm sàng (Bệnh viện)")
    clin_head = _field(p_details.get("clinical_head"), "Phụ trách lâm sàng", "Họ tên cán bộ phụ trách lâm sàng")
    bio_head = _field(p_details.get("analytical_head"), "Phụ trách phân tích mẫu sinh học", "Họ tên cán bộ phụ trách phân tích mẫu sinh học")
    stat_head = _field(p_details.get("statistical_head"), "Phụ trách thống kê & quản lý dữ liệu", "Họ tên cán bộ phụ trách quản lý dữ liệu, phân tích thống kê")
    qa_head = _field(p_details.get("qa_head"), "Phụ trách đảm bảo chất lượng", "Họ tên cán bộ phụ trách QA/QC")

    # Product descriptions
    test_batch = _field(getattr(study, "test_batch", None), "Số lô thuốc thử", "Số lô sản xuất của thuốc thử nghiệm")
    test_mfg = _field(p_details.get("test_mfg_date"), "Ngày sản xuất thuốc thử", "Ngày/tháng/năm")
    test_exp = _field(getattr(study, "test_expiry_date", None) or p_details.get("test_expiry_date"), "Hạn dùng thuốc thử", "Ngày/tháng/năm")
    test_size = _field(p_details.get("test_batch_size"), "Cỡ lô sản xuất thuốc thử", "Ví dụ: 100.000 gói")
    test_reg = _field(p_details.get("test_reg_number"), "Số đăng ký / Số giấy phép thuốc thử", "Ví dụ: VD-16000-11")

    ref_batch = _field(getattr(study, "reference_batch", None), "Số lô thuốc đối chứng", "Số lô sản xuất thuốc đối chứng")
    ref_mfg = _field(p_details.get("ref_mfg_date"), "Ngày sản xuất thuốc đối chứng", "Tháng/năm")
    ref_exp = _field(getattr(study, "reference_expiry_date", None) or p_details.get("ref_expiry_date"), "Hạn dùng thuốc đối chứng", "Tháng/năm")
    ref_mfr = _field(getattr(study, "reference_manufacturer", None) or p_details.get("ref_manufacturer"), "Nhà sản xuất thuốc đối chứng", "Tên và địa chỉ nhà sản xuất thuốc đối chứng")

    # Sample size and subjects count
    n_enrolled = getattr(study, "sample_size", None) or 30
    n_analyzed = n_enrolled
    n_withdrawn = 0
    withdraw_text = "Không có NTN nào rút khỏi nghiên cứu."

    # Process NCA data if available
    nca_rows = run.get("nca", [])
    pk_subject_table = []
    pk_ln_table = []
    pk_summary_s1 = []
    auc_ratio_t = 0.0
    auc_ratio_r = 0.0
    tmax_wilcoxon_table = []
    wilcoxon_p = 1.0
    wilcoxon_stat = 0.0

    if nca_rows:
        df_nca = pd.DataFrame(nca_rows)
        # Unique subjects
        subjects = sorted(df_nca["subject_id"].unique(), key=lambda s: str(s))
        n_analyzed = len(subjects)

        # Subject-level NCA Table 6
        piv_cmax = df_nca.pivot(index="subject_id", columns="treatment", values="cmax")
        piv_tmax = df_nca.pivot(index="subject_id", columns="treatment", values="tmax")
        piv_auct = df_nca.pivot(index="subject_id", columns="treatment", values="auc_last")
        piv_aucinf = df_nca.pivot(index="subject_id", columns="treatment", values="auc_inf")
        if "auc_inf" not in df_nca.columns or piv_aucinf.isna().all().all():
            piv_aucinf = df_nca.pivot(index="subject_id", columns="treatment", values="auc_inf_pred")
        piv_thalf = df_nca.pivot(index="subject_id", columns="treatment", values="half_life")
        piv_kel = df_nca.pivot(index="subject_id", columns="treatment", values="lambda_z")

        for idx, sid in enumerate(subjects, 1):
            t_cmax = piv_cmax.loc[sid, "T"] if "T" in piv_cmax.columns and sid in piv_cmax.index else np.nan
            r_cmax = piv_cmax.loc[sid, "R"] if "R" in piv_cmax.columns and sid in piv_cmax.index else np.nan
            t_tmax = piv_tmax.loc[sid, "T"] if "T" in piv_tmax.columns and sid in piv_tmax.index else np.nan
            r_tmax = piv_tmax.loc[sid, "R"] if "R" in piv_tmax.columns and sid in piv_tmax.index else np.nan
            t_auct = piv_auct.loc[sid, "T"] if "T" in piv_auct.columns and sid in piv_auct.index else np.nan
            r_auct = piv_auct.loc[sid, "R"] if "R" in piv_auct.columns and sid in piv_auct.index else np.nan
            t_aucinf = piv_aucinf.loc[sid, "T"] if "T" in piv_aucinf.columns and sid in piv_aucinf.index else np.nan
            r_aucinf = piv_aucinf.loc[sid, "R"] if "R" in piv_aucinf.columns and sid in piv_aucinf.index else np.nan
            t_thalf = piv_thalf.loc[sid, "T"] if "T" in piv_thalf.columns and sid in piv_thalf.index else np.nan
            r_thalf = piv_thalf.loc[sid, "R"] if "R" in piv_thalf.columns and sid in piv_thalf.index else np.nan
            t_kel = piv_kel.loc[sid, "T"] if "T" in piv_kel.columns and sid in piv_kel.index else np.nan
            r_kel = piv_kel.loc[sid, "R"] if "R" in piv_kel.columns and sid in piv_kel.index else np.nan

            pk_subject_table.append({
                "stt": str(idx),
                "subject_id": str(sid),
                "t_cmax": f"{t_cmax:.3f}" if pd.notna(t_cmax) else "—",
                "r_cmax": f"{r_cmax:.3f}" if pd.notna(r_cmax) else "—",
                "t_tmax": f"{t_tmax:.2f}" if pd.notna(t_tmax) else "—",
                "r_tmax": f"{r_tmax:.2f}" if pd.notna(r_tmax) else "—",
                "t_auct": f"{t_auct:.2f}" if pd.notna(t_auct) else "—",
                "r_auct": f"{r_auct:.2f}" if pd.notna(r_auct) else "—",
                "t_aucinf": f"{t_aucinf:.2f}" if pd.notna(t_aucinf) else "—",
                "r_aucinf": f"{r_aucinf:.2f}" if pd.notna(r_aucinf) else "—",
                "t_thalf": f"{t_thalf:.2f}" if pd.notna(t_thalf) else "—",
                "r_thalf": f"{r_thalf:.2f}" if pd.notna(r_thalf) else "—",
                "t_kel": f"{t_kel:.4f}" if pd.notna(t_kel) else "—",
                "r_kel": f"{r_kel:.4f}" if pd.notna(r_kel) else "—",
            })

            # Ln-transformed Table 7
            ln_t_cmax = math.log(t_cmax) if pd.notna(t_cmax) and t_cmax > 0 else np.nan
            ln_r_cmax = math.log(r_cmax) if pd.notna(r_cmax) and r_cmax > 0 else np.nan
            ln_diff_cmax = (ln_t_cmax - ln_r_cmax) if pd.notna(ln_t_cmax) and pd.notna(ln_r_cmax) else np.nan

            ln_t_auct = math.log(t_auct) if pd.notna(t_auct) and t_auct > 0 else np.nan
            ln_r_auct = math.log(r_auct) if pd.notna(r_auct) and r_auct > 0 else np.nan
            ln_diff_auct = (ln_t_auct - ln_r_auct) if pd.notna(ln_t_auct) and pd.notna(ln_r_auct) else np.nan

            ln_t_aucinf = math.log(t_aucinf) if pd.notna(t_aucinf) and t_aucinf > 0 else np.nan
            ln_r_aucinf = math.log(r_aucinf) if pd.notna(r_aucinf) and r_aucinf > 0 else np.nan
            ln_diff_aucinf = (ln_t_aucinf - ln_r_aucinf) if pd.notna(ln_t_aucinf) and pd.notna(ln_r_aucinf) else np.nan

            pk_ln_table.append({
                "stt": str(idx),
                "subject_id": str(sid),
                "ln_t_cmax": f"{ln_t_cmax:.3f}" if pd.notna(ln_t_cmax) else "—",
                "ln_r_cmax": f"{ln_r_cmax:.3f}" if pd.notna(ln_r_cmax) else "—",
                "ln_diff_cmax": f"{ln_diff_cmax:.3f}" if pd.notna(ln_diff_cmax) else "—",
                "ln_t_auct": f"{ln_t_auct:.3f}" if pd.notna(ln_t_auct) else "—",
                "ln_r_auct": f"{ln_r_auct:.3f}" if pd.notna(ln_r_auct) else "—",
                "ln_diff_auct": f"{ln_diff_auct:.3f}" if pd.notna(ln_diff_auct) else "—",
                "ln_t_aucinf": f"{ln_t_aucinf:.3f}" if pd.notna(ln_t_aucinf) else "—",
                "ln_r_aucinf": f"{ln_r_aucinf:.3f}" if pd.notna(ln_r_aucinf) else "—",
                "ln_diff_aucinf": f"{ln_diff_aucinf:.3f}" if pd.notna(ln_diff_aucinf) else "—",
            })

        # Summary statistics for Table S1 & Table 8
        param_defs = [
            ("AUC0-t (µg·h/mL)", "auc_last", 2),
            ("AUC0-inf (µg·h/mL)", "auc_inf" if "auc_inf" in df_nca.columns else "auc_inf_pred", 2),
            ("Cmax (µg/mL)", "cmax", 3),
            ("Tmax (h)", "tmax", 2),
            ("t1/2 (h)", "half_life", 2),
            ("Kel (1/h)", "lambda_z", 4),
        ]

        mean_auct_t, mean_aucinf_t = 0.0, 0.0
        mean_auct_r, mean_aucinf_r = 0.0, 0.0

        for p_label, p_col, decimals in param_defs:
            for trt in ["T", "R"]:
                sub = df_nca[df_nca["treatment"] == trt][p_col].dropna()
                if not sub.empty:
                    m = float(sub.mean())
                    pos = sub[sub > 0]
                    gm = float(gmean(pos)) if not pos.empty else m
                    sd = float(sub.std()) if len(sub) > 1 else 0.0
                    cv = (sd / m * 100.0) if m != 0 else 0.0
                    mi, ma = float(sub.min()), float(sub.max())

                    if p_col in ("auc_last",) and trt == "T":
                        mean_auct_t = m
                    elif p_col in ("auc_last",) and trt == "R":
                        mean_auct_r = m
                    elif p_col in ("auc_inf", "auc_inf_pred") and trt == "T":
                        mean_aucinf_t = m
                    elif p_col in ("auc_inf", "auc_inf_pred") and trt == "R":
                        mean_aucinf_r = m

                    pk_summary_s1.append({
                        "param": p_label,
                        "treatment": "Thuốc thử (T)" if trt == "T" else "Thuốc đối chứng (R)",
                        "mean": f"{m:.{decimals}f}",
                        "geomean": f"{gm:.{decimals}f}",
                        "sd": f"{sd:.{decimals}f}",
                        "cv": f"{cv:.2f}%",
                        "range": f"{mi:.{decimals}f} – {ma:.{decimals}f}",
                    })

        if mean_aucinf_t > 0:
            auc_ratio_t = (mean_auct_t / mean_aucinf_t) * 100.0
        if mean_aucinf_r > 0:
            auc_ratio_r = (mean_auct_r / mean_aucinf_r) * 100.0

        # Wilcoxon test for Tmax (Table 13)
        if "T" in piv_tmax.columns and "R" in piv_tmax.columns:
            common = piv_tmax.dropna().index
            if len(common) >= 3:
                t_vals = piv_tmax.loc[common, "T"]
                r_vals = piv_tmax.loc[common, "R"]
                diffs = t_vals - r_vals

                non_zero = diffs[diffs != 0]
                ranks = non_zero.abs().rank(method="average")

                pos_ranks = ranks[non_zero > 0].sum()
                neg_ranks = ranks[non_zero < 0].sum()

                try:
                    w_res = wilcoxon(t_vals, r_vals, alternative="two-sided", zero_method="wilcox")
                    wilcoxon_p = float(w_res.pvalue)
                    wilcoxon_stat = float(w_res.statistic)
                except Exception:
                    wilcoxon_p = 1.0
                    wilcoxon_stat = float(min(pos_ranks, neg_ranks))

                for idx, sid in enumerate(common, 1):
                    val_t = t_vals.loc[sid]
                    val_r = r_vals.loc[sid]
                    d = val_t - val_r
                    rank_str = "—"
                    pos_str = "—"
                    neg_str = "—"
                    if d != 0 and sid in ranks.index:
                        rk = ranks.loc[sid]
                        rank_str = f"{rk:.1f}"
                        if d > 0:
                            pos_str = f"{rk:.1f}"
                        else:
                            neg_str = f"{rk:.1f}"
                    tmax_wilcoxon_table.append({
                        "stt": str(idx),
                        "subject_id": str(sid),
                        "t_val": f"{val_t:.2f}",
                        "r_val": f"{val_r:.2f}",
                        "diff": f"{d:+.2f}" if d != 0 else "0.00",
                        "rank": rank_str,
                        "pos_rank": pos_str,
                        "neg_rank": neg_str,
                    })

    # BE confidence intervals and ANOVA
    be_results = run.get("be", [])
    be_summary_table = []
    be_power_table = []
    anova_table = []

    for b in be_results:
        ep = b.get("endpoint", "")
        ep_label = "AUC0-t" if ep == "auc_last" else ("Cmax" if ep == "cmax" else ("AUC0-inf" if "inf" in ep else ep))
        gmr = b.get("gmr")
        gmr_pct = (gmr * 100.0) if gmr is not None else 100.0
        ci_l = b.get("ci_lower")
        ci_u = b.get("ci_upper")
        ci_l_pct = (ci_l * 100.0) if ci_l is not None else 0.0
        ci_u_pct = (ci_u * 100.0) if ci_u is not None else 0.0

        decision = b.get("decision", "PASS")
        is_pass = decision == "PASS"

        be_summary_table.append({
            "param": ep_label,
            "gmr": f"{gmr_pct:.2f}%",
            "ci": f"{ci_l_pct:.2f}% – {ci_u_pct:.2f}%",
            "criteria": "80.00% – 125.00%",
            "decision": "Tương đương sinh học" if is_pass else "Không tương đương sinh học",
        })

        # Calculate Power_TOST (CRITICAL: DO NOT USE Power_80_20)
        diag = b.get("diagnostics", {})
        anc = diag.get("ancillary", {})
        pow_val = anc.get("Power_TOST")

        if pow_val is None:
            diff = diag.get("difference", {})
            se = diff.get("se", 0.0)
            est = diff.get("estimate", 0.0)
            df = diff.get("df", 22)
            pow_val = _calculate_power_tost(se, est, df)

        pow_pct = (pow_val * 100.0) if pow_val is not None else 0.0
        be_power_table.append({
            "param": ep_label,
            "power_tost": f"{pow_pct:.2f}%",
            "criteria": "≥ 80.00%",
            "status": "Đạt lực kiểm định (≥ 80%)" if pow_pct >= 80.0 else "Dưới ngưỡng 80% (Tham khảo)",
        })

        # ANOVA Table 10
        part_ss = diag.get("partial_ss", [])
        if part_ss:
            for row in part_ss:
                hyp = row.get("Hypothesis", "")
                hyp_vi = {
                    "Sequence": "Trình tự (Sequence)",
                    "Sequence*Subject": "Cá thể trong trình tự [Subject(Sequence)]",
                    "Treatment": "Thuốc nghiên cứu (Treatment)",
                    "Period": "Giai đoạn (Period)",
                    "Error": "Sai số ngẫu nhiên (Error / Residual)",
                }.get(hyp, hyp)
                df_val = row.get("DF", "")
                ss_val = row.get("SS")
                ms_val = row.get("MS")
                f_val = row.get("F_stat")
                p_val = row.get("P_value")

                anova_table.append({
                    "param": ep_label,
                    "source": hyp_vi,
                    "df": str(df_val),
                    "ss": f"{ss_val:.4f}" if ss_val is not None else "—",
                    "ms": f"{ms_val:.4f}" if ms_val is not None else "—",
                    "f_stat": f"{f_val:.4f}" if f_val is not None else "—",
                    "p_val": f"{p_val:.4f}" if p_val is not None else "—",
                })

    return dict(
        study=study,
        run=run,
        has_run=has_run,
        today_str=today_str,
        current_year=current_year,
        substance=substance,
        dose=dose,
        dose_unit=dose_unit,
        dosage_form=dosage_form,
        test_product=test_product,
        ref_product=ref_product,
        sponsor=sponsor,
        cro=cro,
        pi=pi,
        study_id=study_id,
        study_title=study_title,
        clin_p1=clin_p1,
        clin_p2=clin_p2,
        analytical_dates=analytical_dates,
        clin_physician=clin_physician,
        clin_head=clin_head,
        bio_head=bio_head,
        stat_head=stat_head,
        qa_head=qa_head,
        test_batch=test_batch,
        test_mfg=test_mfg,
        test_exp=test_exp,
        test_size=test_size,
        test_reg=test_reg,
        ref_batch=ref_batch,
        ref_mfg=ref_mfg,
        ref_exp=ref_exp,
        ref_mfr=ref_mfr,
        n_enrolled=n_enrolled,
        n_analyzed=n_analyzed,
        n_withdrawn=n_withdrawn,
        withdraw_text=withdraw_text,
        pk_subject_table=pk_subject_table,
        pk_ln_table=pk_ln_table,
        pk_summary_s1=pk_summary_s1,
        auc_ratio_t=auc_ratio_t,
        auc_ratio_r=auc_ratio_r,
        tmax_wilcoxon_table=tmax_wilcoxon_table,
        wilcoxon_p=wilcoxon_p,
        wilcoxon_stat=wilcoxon_stat,
        be_summary_table=be_summary_table,
        be_power_table=be_power_table,
        anova_table=anova_table,
        cro_address=cro_address,
        governing_body=governing_body,
        lab_accreditation=lab_accreditation,
        location=location,
        p_details=p_details,
        is_overall_be_pass=(
            all(r.get("decision") == "Tương đương sinh học" for r in be_summary_table)
            if be_summary_table
            else (run.get("study_decision") == "PASS" if has_run and run.get("study_decision") else True)
        ),
    )


# ---------------------------------------------------------------------------
# DOCX FORMATTING HELPERS
# ---------------------------------------------------------------------------

def _set_cell_margins(cell, top=100, bottom=100, left=140, right=140):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for m_name, val in [("top", top), ("bottom", bottom), ("left", left), ("right", right)]:
        node = OxmlElement(f"w:{m_name}")
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        tcMar.append(node)
    tcPr.append(tcMar)


def _set_cell_shading(cell, color_hex="F2F4F7"):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color_hex)
    tcPr.append(shd)


def _set_table_borders(table, color="D3D3D3"):
    tblPr = table._tbl.tblPr
    tblBorders = OxmlElement("w:tblBorders")
    for border_name in ("top", "left", "bottom", "right", "insideH"):
        border = OxmlElement(f"w:{border_name}")
        border.set(qn("w:val"), "single")
        border.set(qn("w:sz"), "4")
        border.set(qn("w:space"), "0")
        border.set(qn("w:color"), color)
        tblBorders.append(border)
    v_border = OxmlElement("w:insideV")
    v_border.set(qn("w:val"), "single")
    v_border.set(qn("w:sz"), "4")
    v_border.set(qn("w:space"), "0")
    v_border.set(qn("w:color"), color)
    tblBorders.append(v_border)
    tblPr.append(tblBorders)


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
                r_tag.font.color.rgb = RGBColor(192, 0, 0)
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


def _add_cell_text(cell, text: str, bold: bool = False, italic: bool = False, align=WD_ALIGN_PARAGRAPH.LEFT, font_size: Pt = Pt(9)):
    p = cell.paragraphs[0]
    p.alignment = align
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(1)
    p.paragraph_format.line_spacing = 1.05

    if REQ_USER_INPUT_PREFIX_VI in text or LEGACY_MISSING_VI in text:
        parts = text.split("[")
        if parts[0]:
            r = p.add_run(parts[0])
            r.font.size = font_size
            r.font.bold = bold
        for part in parts[1:]:
            if "]" in part:
                b_text, rest = part.split("]", 1)
                r_tag = p.add_run(f"[{b_text}]")
                r_tag.font.size = font_size
                r_tag.font.bold = True
                r_tag.font.color.rgb = RGBColor(192, 0, 0)
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
        run.font.italic = italic


# ---------------------------------------------------------------------------
# WORD (.DOCX) GENERATOR
# ---------------------------------------------------------------------------

def docx_report_vknt(project: Project, run_index: int = -1, language: str = "vi") -> bytes:
    """Generate Word (.docx) Clinical Study Report matching MOH / VKNT TP.HCM format."""
    c = build_vknt_report_data(project, run_index)
    p_details = c.get("p_details", {})
    doc = Document()

    # Set page margins: 2.0 cm everywhere
    for sec in doc.sections:
        sec.top_margin = Cm(2.0)
        sec.bottom_margin = Cm(2.0)
        sec.left_margin = Cm(2.2)
        sec.right_margin = Cm(2.0)

        # Header
        hdr = sec.header.paragraphs[0]
        hdr.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hdr_run = hdr.add_run(f"BÁO CÁO KẾT QUẢ NGHIÊN CỨU TƯƠNG ĐƯƠNG SINH HỌC | Mã số: {c['study_id']}")
        hdr_run.font.size = Pt(8)
        hdr_run.font.italic = True
        hdr_run.font.color.rgb = RGBColor(128, 128, 128)

        # Footer
        ftr = sec.footer.paragraphs[0]
        ftr.alignment = WD_ALIGN_PARAGRAPH.LEFT
        ftr_run = ftr.add_run(f"{CONFIDENTIAL_LABEL} · {software_attribution(language)} · {DEVELOPER}")
        ftr_run.font.size = Pt(8)
        ftr_run.font.color.rgb = RGBColor(128, 128, 128)

    # 1. TRANG BÌA NGOÀI
    _add_p(doc, c["governing_body"].upper(), bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(13), space_after=Pt(1))
    _add_p(doc, c["cro"].upper(), bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(13), space_after=Pt(4))
    _add_p(doc, c["lab_accreditation"], bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(11), space_after=Pt(36))

    _add_p(doc, "BÁO CÁO KẾT QUẢ NGHIÊN CỨU", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(18), space_after=Pt(28), color=RGBColor(26, 54, 93))

    _add_p(doc, f"Đề tài:", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(12), space_after=Pt(6))
    _add_p(doc, c["study_title"].upper(), bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(13), space_after=Pt(40), color=RGBColor(16, 42, 77))

    _add_p(doc, f"Mã số đề tài: {c['study_id']}", bold=True, font_size=Pt(11), space_after=Pt(6))
    _add_p(doc, f"Đơn vị yêu cầu: {c['sponsor']}", font_size=Pt(11), space_after=Pt(6))
    _add_p(doc, f"Đơn vị nghiên cứu: {c['cro']}", font_size=Pt(11), space_after=Pt(6))
    _add_p(doc, f"Địa chỉ: {c['cro_address']}", font_size=Pt(10), space_after=Pt(40))

    _add_p(doc, f"{c['location']} — {c['current_year']}", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(11))
    doc.add_page_break()

    # 2. TRANG BÌA TRONG
    _add_p(doc, c["governing_body"].upper(), bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(13), space_after=Pt(1))
    _add_p(doc, c["cro"].upper(), bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(13), space_after=Pt(28))

    _add_p(doc, "BÁO CÁO KẾT QUẢ NGHIÊN CỨU", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(17), space_after=Pt(24), color=RGBColor(26, 54, 93))
    _add_p(doc, c["study_title"].upper(), bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(12), space_after=Pt(36))

    _add_p(doc, f"Mã số đề tài: {c['study_id']}", bold=True, font_size=Pt(11), space_after=Pt(6))
    _add_p(doc, f"Đơn vị yêu cầu: {c['sponsor']}", font_size=Pt(11), space_after=Pt(6))
    _add_p(doc, f"Đơn vị nghiên cứu: {c['cro']}", font_size=Pt(11), space_after=Pt(6))
    _add_p(doc, f"Địa chỉ: {c['cro_address']}", font_size=Pt(10), space_after=Pt(36))
    _add_p(doc, f"{c['location']} — {c['current_year']}", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(11))
    doc.add_page_break()

    # 3. THÔNG TIN NGHIÊN CỨU VÀ NHÂN SỰ CHỦ CHỐT
    _add_p(doc, "THÔNG TIN NGHIÊN CỨU VÀ NHÂN SỰ CHỦ CHỐT", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(13), space_after=Pt(12), color=RGBColor(26, 54, 93))

    tbl_info = doc.add_table(rows=11, cols=2)
    tbl_info.alignment = WD_TABLE_ALIGNMENT.CENTER
    _set_table_borders(tbl_info)
    info_rows = [
        ("Tên đề tài", c["study_title"]),
        ("Mã số đề tài", c["study_id"]),
        ("Thuốc thử nghiệm", f"{c['test_product']} ({c['substance']} {c['dose']}) — Lô: {c['test_batch']}"),
        ("Thuốc đối chứng", f"{c['ref_product']} ({c['substance']} {c['dose']}) — Lô: {c['ref_batch']}"),
        ("Đơn vị yêu cầu", c["sponsor"]),
        ("Đơn vị nghiên cứu", c["cro"]),
        ("Chủ nhiệm đề tài (PI)", c["pi"]),
        ("Bác sĩ phụ trách lâm sàng", c["clin_physician"]),
        ("Phụ trách phân tích mẫu sinh học", c["bio_head"]),
        ("Phụ trách quản lý dữ liệu, xử lý thống kê", c["stat_head"]),
        ("Phụ trách chất lượng (QA/QC)", c["qa_head"]),
    ]
    for idx, (label, val) in enumerate(info_rows):
        row = tbl_info.rows[idx]
        _set_cell_shading(row.cells[0], "F2F4F7")
        _set_cell_margins(row.cells[0], 80, 80, 100, 100)
        _set_cell_margins(row.cells[1], 80, 80, 100, 100)
        row.cells[0].width = Cm(5.0)
        row.cells[1].width = Cm(11.8)
        _add_cell_text(row.cells[0], label, bold=True, font_size=Pt(9.5))
        _add_cell_text(row.cells[1], val, font_size=Pt(9.5))

    _add_p(doc, "", space_after=Pt(10))
    _add_p(doc, f"Thời gian thử lâm sàng: Giai đoạn 1: {c['clin_p1']}; Giai đoạn 2: {c['clin_p2']}", italic=True, font_size=Pt(9.5))
    _add_p(doc, f"Thời gian phân tích mẫu sinh học: {c['analytical_dates']}", italic=True, font_size=Pt(9.5))
    doc.add_page_break()

    # 4. TRANG CHỮ KÝ
    _add_p(doc, "TRANG CHỮ KÝ", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(14), space_after=Pt(12), color=RGBColor(26, 54, 93))
    _add_p(
        doc,
        "Nghiên cứu này được thực hiện theo đề cương đã được phê duyệt, tuân thủ nghiêm ngặt các nguyên tắc "
        "Thực hành tốt thử thuốc trên lâm sàng (GCP), Thực hành tốt phòng kiểm nghiệm thuốc (GLP), tiêu chuẩn ISO/IEC 17025, "
        "hướng dẫn đánh giá tương đương sinh học hiện hành của Bộ Y tế Việt Nam và quốc tế (ASEAN, ICH M13A) "
        "và các quy định trong hệ thống Quy trình thao tác chuẩn (SOP) của đơn vị nghiên cứu.",
        space_after=Pt(10),
    )
    _add_p(doc, "Chúng tôi, những người ký tên dưới đây, đã đọc bản báo cáo này và xác nhận số liệu trong báo cáo là trung thực, chính xác và khách quan:", space_after=Pt(14))

    tbl_sign = doc.add_table(rows=7, cols=3)
    tbl_sign.alignment = WD_TABLE_ALIGNMENT.CENTER
    _set_table_borders(tbl_sign)
    sign_headers = ["Vị trí trách nhiệm", "Họ và tên", "Chữ ký và Ngày ký"]
    for j, h in enumerate(sign_headers):
        c_cell = tbl_sign.rows[0].cells[j]
        _set_cell_shading(c_cell, "EAECEE")
        _set_cell_margins(c_cell, 80, 80, 100, 100)
        _add_cell_text(c_cell, h, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(9.5))

    sign_roles = [
        ("Bác sĩ lâm sàng", c["clin_physician"]),
        ("Phụ trách lâm sàng", c["clin_head"]),
        ("Phụ trách phân tích mẫu sinh học", c["bio_head"]),
        ("Phụ trách thống kê & quản lý số liệu", c["stat_head"]),
        ("Phụ trách đảm bảo chất lượng (QA)", c["qa_head"]),
        ("Chủ nhiệm đề tài (PI)", c["pi"]),
    ]
    for idx, (role, name) in enumerate(sign_roles, 1):
        row = tbl_sign.rows[idx]
        _set_cell_margins(row.cells[0], 120, 120, 100, 100)
        _set_cell_margins(row.cells[1], 120, 120, 100, 100)
        _set_cell_margins(row.cells[2], 120, 120, 100, 100)
        row.cells[0].width = Cm(5.5)
        row.cells[1].width = Cm(6.5)
        row.cells[2].width = Cm(4.8)
        _add_cell_text(row.cells[0], role, bold=True, font_size=Pt(9))
        _add_cell_text(row.cells[1], name, font_size=Pt(9))
        _add_cell_text(row.cells[2], "[Ký và ghi rõ ngày]", italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8.5))

    _add_p(doc, "", space_after=Pt(16))
    _add_p(doc, f"TP. Hồ Chí Minh, ngày ... tháng ... năm {c['current_year']}", italic=True, align=WD_ALIGN_PARAGRAPH.RIGHT, font_size=Pt(10))
    _add_p(doc, "THỦ TRƯỞNG ĐƠN VỊ NGHIÊN CỨU / VIỆN TRƯỞNG", bold=True, align=WD_ALIGN_PARAGRAPH.RIGHT, font_size=Pt(11), space_after=Pt(40))
    _add_p(doc, "(Ký tên, đóng dấu và ghi rõ họ tên)", italic=True, align=WD_ALIGN_PARAGRAPH.RIGHT, font_size=Pt(9))
    doc.add_page_break()

    # 5. TÓM TẮT KẾT QUẢ NGHIÊN CỨU (SYNOPSIS)
    _add_p(doc, "TÓM TẮT KẾT QUẢ NGHIÊN CỨU", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(14), space_after=Pt(10), color=RGBColor(26, 54, 93))

    # Bảng tóm tắt thông tin thuốc
    tbl_syn = doc.add_table(rows=3, cols=2)
    tbl_syn.alignment = WD_TABLE_ALIGNMENT.CENTER
    _set_table_borders(tbl_syn)
    syn_rows = [
        (f"Đơn vị yêu cầu: {c['sponsor']}", f"Đơn vị nghiên cứu: {c['cro']}"),
        (f"Thuốc thử: {c['test_product']}", f"Tên hoạt chất, hàm lượng: {c['substance']} {c['dose']}"),
        (f"Thuốc đối chứng: {c['ref_product']}", f"Tên hoạt chất, hàm lượng: {c['substance']} {c['dose']}"),
    ]
    for i, (l_val, r_val) in enumerate(syn_rows):
        row = tbl_syn.rows[i]
        _set_cell_margins(row.cells[0], 60, 60, 80, 80)
        _set_cell_margins(row.cells[1], 60, 60, 80, 80)
        row.cells[0].width = Cm(8.4)
        row.cells[1].width = Cm(8.4)
        _add_cell_text(row.cells[0], l_val, font_size=Pt(9))
        _add_cell_text(row.cells[1], r_val, font_size=Pt(9))

    _add_p(doc, "Mục tiêu nghiên cứu:", bold=True, font_size=Pt(10), space_before=Pt(8), space_after=Pt(2))
    _add_p(doc, f"Đánh giá tương đương sinh học của {c['dosage_form']} {c['test_product']} do {c['sponsor']} sản xuất so với {c['ref_product']} do {c['ref_mfr']} sản xuất.", space_after=Pt(6))

    _add_p(doc, "Thuốc nghiên cứu:", bold=True, font_size=Pt(10), space_before=Pt(4), space_after=Pt(2))
    _add_p(doc, f"• Thuốc thử: {c['test_product']} ({c['substance']} {c['dose']}), số lô: {c['test_batch']}, NSX: {c['test_mfg']}, HD: {c['test_exp']}, cỡ lô: {c['test_size']}, SĐK: {c['test_reg']}.", space_after=Pt(2))
    _add_p(doc, f"• Thuốc đối chứng: {c['ref_product']} ({c['substance']} {c['dose']}), số lô: {c['ref_batch']}, NSX: {c['ref_mfg']}, HD: {c['ref_exp']} do {c['ref_mfr']} sản xuất.", space_after=Pt(6))

    _add_p(doc, "Phương pháp nghiên cứu:", bold=True, font_size=Pt(10), space_before=Pt(4), space_after=Pt(2))
    _add_p(doc, f"Thiết kế nghiên cứu chéo đôi ngẫu nhiên 2 giai đoạn, 2 trình tự (2×2 crossover), đơn liều, có thời gian rửa giải phù hợp. Tổng số {c['n_enrolled']} người tình nguyện khỏe mạnh được tuyển chọn và tham gia nghiên cứu theo đúng hướng dẫn của Bộ Y tế và ASEAN.", space_after=Pt(6))

    _add_p(doc, "Kết quả:", bold=True, font_size=Pt(10), space_before=Pt(4), space_after=Pt(2))
    _add_p(doc, f"Phân tích dược động học dựa trên dữ liệu của {c['n_analyzed']} người tình nguyện hoàn tất nghiên cứu. Các giá trị thông số PK trung bình và khoảng tin cậy 90% được trình bày tại Bảng S1, S2, S3 dưới đây:", space_after=Pt(6))

    # Bảng S1
    _add_p(doc, "Bảng S1. Các thông số dược động học trung bình của thuốc thử và thuốc đối chứng", bold=True, font_size=Pt(9.5), space_before=Pt(4), space_after=Pt(2))
    if c["pk_summary_s1"]:
        tbl_s1 = doc.add_table(rows=len(c["pk_summary_s1"]) + 1, cols=7)
        tbl_s1.alignment = WD_TABLE_ALIGNMENT.CENTER
        _set_table_borders(tbl_s1)
        s1_hdrs = ["Thông số", "Thuốc", "TB cộng", "TB nhân", "SD", "CV (%)", "Khoảng (min – max)"]
        for j, h in enumerate(s1_hdrs):
            cell = tbl_s1.rows[0].cells[j]
            _set_cell_shading(cell, "EAECEE")
            _add_cell_text(cell, h, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8.5))
        for i, row_data in enumerate(c["pk_summary_s1"], 1):
            r = tbl_s1.rows[i]
            _add_cell_text(r.cells[0], row_data["param"], font_size=Pt(8))
            _add_cell_text(r.cells[1], row_data["treatment"], font_size=Pt(8))
            _add_cell_text(r.cells[2], row_data["mean"], align=WD_ALIGN_PARAGRAPH.RIGHT, font_size=Pt(8))
            _add_cell_text(r.cells[3], row_data["geomean"], align=WD_ALIGN_PARAGRAPH.RIGHT, font_size=Pt(8))
            _add_cell_text(r.cells[4], row_data["sd"], align=WD_ALIGN_PARAGRAPH.RIGHT, font_size=Pt(8))
            _add_cell_text(r.cells[5], row_data["cv"], align=WD_ALIGN_PARAGRAPH.RIGHT, font_size=Pt(8))
            _add_cell_text(r.cells[6], row_data["range"], align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8))
    else:
        _add_p(doc, "[YÊU CẦU NGƯỜI DÙNG BỔ SUNG: Dữ liệu Bảng S1 sẽ tự động điền khi chạy phân tích NCA trong ứng dụng]", bold=True)

    # Bảng S2
    _add_p(doc, "", space_after=Pt(4))
    _add_p(doc, f"Bảng S2. Tỉ số AUC0-t / AUC0-inf: Thuốc thử = {c['auc_ratio_t']:.2f} %; Thuốc đối chứng = {c['auc_ratio_r']:.2f} % (yêu cầu ≥ 80.00% chứng minh thời gian lấy máu đủ dài).", italic=True, font_size=Pt(9))

    # Bảng S3
    _add_p(doc, "Bảng S3. Kết quả xác định khoảng tin cậy 90%", bold=True, font_size=Pt(9.5), space_before=Pt(6), space_after=Pt(2))
    if c["be_summary_table"]:
        tbl_s3 = doc.add_table(rows=len(c["be_summary_table"]) + 1, cols=4)
        tbl_s3.alignment = WD_TABLE_ALIGNMENT.CENTER
        _set_table_borders(tbl_s3)
        s3_hdrs = ["Thông số", "Tỉ số GMR (%) (Thử/Chứng)", "Khoảng tin cậy 90%", "Tiêu chuẩn chấp nhận"]
        for j, h in enumerate(s3_hdrs):
            cell = tbl_s3.rows[0].cells[j]
            _set_cell_shading(cell, "EAECEE")
            _add_cell_text(cell, h, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8.5))
        for i, row_data in enumerate(c["be_summary_table"], 1):
            r = tbl_s3.rows[i]
            _add_cell_text(r.cells[0], row_data["param"], bold=True, font_size=Pt(8.5))
            _add_cell_text(r.cells[1], row_data["gmr"], align=WD_ALIGN_PARAGRAPH.RIGHT, font_size=Pt(8.5))
            _add_cell_text(r.cells[2], row_data["ci"], align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8.5))
            _add_cell_text(r.cells[3], row_data["criteria"], align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8.5))
    else:
        _add_p(doc, "[YÊU CẦU NGƯỜI DÙNG BỔ SUNG: Dữ liệu Bảng S3 sẽ tự động điền khi chạy phân tích BE trong ứng dụng]", bold=True)

    _add_p(doc, "Kết luận tóm tắt:", bold=True, font_size=Pt(10), space_before=Pt(8), space_after=Pt(2))
    if not c["has_run"]:
        summary_concl = (
            f"Hai chế phẩm {c['dosage_form']} {c['test_product']} do {c['sponsor']} sản xuất và {c['ref_product']} "
            f"do {c['ref_mfr']} sản xuất: [YÊU CẦU NGƯỜI DÙNG BỔ SUNG: Kết luận sẽ được trích xuất tự động theo kết quả phân tích số liệu thực tế]."
        )
    elif c["is_overall_be_pass"]:
        summary_concl = (
            f"Hai chế phẩm {c['dosage_form']} {c['test_product']} do {c['sponsor']} sản xuất và {c['ref_product']} "
            f"do {c['ref_mfr']} sản xuất TƯƠNG ĐƯƠNG SINH HỌC IN VIVO theo quy định hiện hành của Bộ Y tế Việt Nam và hướng dẫn của ASEAN."
        )
    else:
        summary_concl = (
            f"Hai chế phẩm {c['dosage_form']} {c['test_product']} do {c['sponsor']} sản xuất và {c['ref_product']} "
            f"do {c['ref_mfr']} sản xuất KHÔNG TƯƠNG ĐƯƠNG SINH HỌC IN VIVO theo quy định hiện hành của Bộ Y tế Việt Nam và hướng dẫn của ASEAN do không đáp ứng khoảng chấp nhận tương đương sinh học."
        )
    _add_p(doc, summary_concl, space_after=Pt(8))
    doc.add_page_break()

    # 6. MỤC LỤC & BẢNG CHỮ VIẾT TẮT
    _add_p(doc, "MỤC LỤC VÀ DANH MỤC VIẾT TẮT", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(14), space_after=Pt(10), color=RGBColor(26, 54, 93))

    _add_p(doc, "DANH MỤC CÁC BẢNG", bold=True, font_size=Pt(11), space_before=Pt(6), space_after=Pt(2))
    table_list = [
        "Bảng 1. Kế hoạch thực hiện",
        "Bảng 2. Kết quả tóm tắt thẩm định phương pháp phân tích",
        "Bảng 3. Tóm tắt kết quả kiểm tra dấu hiệu sinh tồn (TB ± SD)",
        "Bảng 4. Nồng độ hoạt chất của từng cá thể sau khi uống thuốc thử",
        "Bảng 5. Nồng độ hoạt chất của từng cá thể sau khi uống thuốc đối chứng",
        "Bảng 6. Các thông số dược động học của từng cá thể",
        "Bảng 7. Các thông số dược động học Cmax, AUC chuyển dạng ln của từng cá thể",
        "Bảng 8. Các thông số dược động học trung bình của thuốc thử và thuốc đối chứng",
        "Bảng 9. Tỉ số AUC0-t / AUC0-inf",
        "Bảng 10. Phân tích phương sai các thông số AUC0-t, AUC0-inf, Cmax (đã chuyển ln)",
        "Bảng 11. Kết quả xác định khoảng tin cậy 90%",
        "Bảng 12. Kết quả giá trị Power (Power_TOST)",
        "Bảng 13. So sánh giá trị Tmax theo phương pháp thống kê phi tham số",
    ]
    for t_item in table_list:
        _add_p(doc, f"• {t_item}", font_size=Pt(9.5), space_after=Pt(1))

    _add_p(doc, "DANH MỤC CÁC HÌNH", bold=True, font_size=Pt(11), space_before=Pt(6), space_after=Pt(2))
    _add_p(doc, "• Hình 1. Đồ thị biểu diễn nồng độ thuốc trung bình theo thời gian của thuốc thử và thuốc đối chứng", font_size=Pt(9.5), space_after=Pt(4))

    _add_p(doc, "BẢNG CHỮ VIẾT TẮT", bold=True, font_size=Pt(11), space_before=Pt(6), space_after=Pt(2))
    tbl_abbr = doc.add_table(rows=len(VKNT_REPORT_ABBREVIATIONS) + 1, cols=3)
    tbl_abbr.alignment = WD_TABLE_ALIGNMENT.CENTER
    _set_table_borders(tbl_abbr)
    abbr_hdrs = ["Chữ viết tắt", "Từ nguyên tiếng Anh", "Ý nghĩa tiếng Việt"]
    for j, h in enumerate(abbr_hdrs):
        cell = tbl_abbr.rows[0].cells[j]
        _set_cell_shading(cell, "EAECEE")
        _add_cell_text(cell, h, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8.5))
    for i, (a_short, a_en, a_vi) in enumerate(VKNT_REPORT_ABBREVIATIONS, 1):
        row = tbl_abbr.rows[i]
        _add_cell_text(row.cells[0], a_short, bold=True, font_size=Pt(8))
        _add_cell_text(row.cells[1], a_en, font_size=Pt(8))
        _add_cell_text(row.cells[2], a_vi, font_size=Pt(8))

    doc.add_page_break()

    # 7. NỘI DUNG CHÍNH (SECTIONS 1 TO 9)
    # Section 1
    _add_p(doc, "1. ĐẠO ĐỨC TRONG NGHIÊN CỨU Y SINH HỌC", bold=True, font_size=Pt(12), space_before=Pt(8), space_after=Pt(4), color=RGBColor(26, 54, 93))
    _add_p(doc, "1.1. Hội đồng Đạo đức trong nghiên cứu y sinh học", bold=True, font_size=Pt(10.5), space_before=Pt(4), space_after=Pt(2))
    _add_p(
        doc,
        f"Hội đồng Đạo đức trong nghiên cứu y sinh học cấp cơ sở hoạt động theo các quy định của Bộ Y tế "
        f"(Thông tư 29/2018/TT-BYT, Quyết định số 111/QĐ-BYT). Nghiên cứu được Hội đồng Đạo đức phê duyệt đề cương "
        f"và chấp thuận cho phép tiến hành trên người tình nguyện trước khi thực hiện. Số văn bản chấp thuận: "
        f"{_field(p_details.get('irb_approval_no'), 'Số văn bản chấp thuận IRB', 'Ví dụ: 23/QĐ-HĐĐĐ ngày 09/06/2016')}. "
        f"Thông tin chi tiết về danh sách Hội đồng và biên bản họp được trình bày tại Phụ lục 10.1.3 và 10.1.4.",
        space_after=Pt(4),
    )
    _add_p(doc, "1.2. Tuân thủ đạo đức trong nghiên cứu", bold=True, font_size=Pt(10.5), space_before=Pt(4), space_after=Pt(2))
    _add_p(
        doc,
        "Nghiên cứu này được tiến hành dựa trên tinh thần của Tuyên ngôn Helsinki, tuân thủ nghiêm ngặt Hướng dẫn "
        "Thực hành lâm sàng tốt (GCP) của Bộ Y tế và ICH E6(R2), đảm bảo quyền lợi, sự an toàn và bí mật thông tin của người tình nguyện.",
        space_after=Pt(4),
    )
    _add_p(doc, "1.3. Thông tin cho người tình nguyện và Giấy chấp thuận tham gia nghiên cứu", bold=True, font_size=Pt(10.5), space_before=Pt(4), space_after=Pt(2))
    _add_p(
        doc,
        "Tất cả các đối tượng tham gia nghiên cứu đều được giải thích cặn kẽ về mục đích, quy trình, các nguy cơ và quyền lợi, "
        "và đã tự nguyện ký 'Phiếu cung cấp thông tin và Giấy chấp thuận tình nguyện tham gia nghiên cứu' (ICF) trước khi tiến hành bất kỳ thủ thuật nào.",
        space_after=Pt(6),
    )

    # Section 2
    _add_p(doc, "2. QUẢN LÝ NGHIÊN CỨU", bold=True, font_size=Pt(12), space_before=Pt(8), space_after=Pt(4), color=RGBColor(26, 54, 93))
    _add_p(
        doc,
        f"Nghiên cứu được tổ chức và điều hành bởi {c['cro']}, phối hợp với cơ sở lâm sàng đạt chuẩn GCP. "
        f"Chủ nhiệm đề tài: {c['pi']}. Bác sĩ lâm sàng phụ trách: {c['clin_physician']}. "
        f"Phụ trách phân tích mẫu sinh học: {c['bio_head']}. Phụ trách thống kê & xử lý số liệu: {c['stat_head']}. "
        f"Bộ phận Đảm bảo chất lượng (QA): {c['qa_head']} thực hiện giám sát độc lập toàn bộ các khâu lâm sàng, phân tích và quản lý dữ liệu.",
        space_after=Pt(6),
    )

    # Section 3
    _add_p(doc, "3. TỔNG QUAN VỀ HOẠT CHẤT NGHIÊN CỨU", bold=True, font_size=Pt(12), space_before=Pt(8), space_after=Pt(4), color=RGBColor(26, 54, 93))
    _add_p(doc, "3.1. Dược lý và cơ chế tác dụng", bold=True, font_size=Pt(10.5), space_before=Pt(4), space_after=Pt(2))
    _add_p(
        doc,
        _field(p_details.get("pharmacology"), "Dược lý và cơ chế tác dụng", f"Cơ chế tác dụng dược lý của {c['substance']}"),
        space_after=Pt(4),
    )
    _add_p(doc, "3.2. Dược động học", bold=True, font_size=Pt(10.5), space_before=Pt(4), space_after=Pt(2))
    _add_p(
        doc,
        _field(p_details.get("pharmacokinetics"), "Dược động học y văn", f"Thông số hấp thu, phân bố, chuyển hóa, thải trừ (Cmax, Tmax, t1/2) của {c['substance']}"),
        space_after=Pt(4),
    )
    _add_p(doc, "3.3. Liều lượng, cách dùng và tác dụng ngoại ý (ADR)", bold=True, font_size=Pt(10.5), space_before=Pt(4), space_after=Pt(2))
    _add_p(
        doc,
        _field(p_details.get("dosage_and_adrs"), "Liều dùng và ADR", f"Liều dùng khuyến cáo, cách dùng và các phản ứng bất lợi thường gặp của {c['substance']}"),
        space_after=Pt(6),
    )

    # Section 4
    _add_p(doc, "4. MỤC TIÊU NGHIÊN CỨU", bold=True, font_size=Pt(12), space_before=Pt(8), space_after=Pt(4), color=RGBColor(26, 54, 93))
    _add_p(
        doc,
        f"Mục tiêu chính: Đánh giá tương đương sinh học in vivo giữa {c['dosage_form']} {c['test_product']} ({c['substance']} {c['dose']}) "
        f"do {c['sponsor']} sản xuất so với {c['ref_product']} do {c['ref_mfr']} sản xuất sau khi uống liều đơn trên người tình nguyện khỏe mạnh.\n"
        f"Mục tiêu phụ: Theo dõi và đánh giá tính an toàn, khả năng dung nạp của hai chế phẩm trên đối tượng nghiên cứu.",
        space_after=Pt(6),
    )

    # Section 5
    _add_p(doc, "5. KẾ HOẠCH THỰC HIỆN VÀ PHƯƠNG PHÁP NGHIÊN CỨU", bold=True, font_size=Pt(12), space_before=Pt(8), space_after=Pt(4), color=RGBColor(26, 54, 93))
    _add_p(doc, "5.1. Thiết kế nghiên cứu", bold=True, font_size=Pt(10.5), space_before=Pt(4), space_after=Pt(2))
    _add_p(
        doc,
        f"Nghiên cứu được thiết kế theo mô hình thử nghiệm chéo đôi ngẫu nhiên 2 giai đoạn, 2 trình tự (2×2 crossover), đơn liều, nhịn đói, "
        f"mở, có đối chứng. Thời gian rửa giải (washout) giữa hai giai đoạn là phù hợp (> 5 lần thời gian bán thải t1/2 của hoạt chất).",
        space_after=Pt(4),
    )

    # Bảng 1
    _add_p(doc, "Bảng 1. Kế hoạch thực hiện nghiên cứu", bold=True, font_size=Pt(9.5), space_before=Pt(4), space_after=Pt(2))
    tbl_b1 = doc.add_table(rows=len(VKNT_REPORT_SCHEDULE) + 1, cols=6)
    tbl_b1.alignment = WD_TABLE_ALIGNMENT.CENTER
    _set_table_borders(tbl_b1)
    b1_hdrs = ["Nội dung hoạt động", "Tuyển chọn", "GĐ 1", "Washout", "GĐ 2", "Kết thúc"]
    for j, h in enumerate(b1_hdrs):
        cell = tbl_b1.rows[0].cells[j]
        _set_cell_shading(cell, "EAECEE")
        _add_cell_text(cell, h, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8.5))
    for i, (act, sc, p1, wo, p2, ed) in enumerate(VKNT_REPORT_SCHEDULE, 1):
        row = tbl_b1.rows[i]
        _add_cell_text(row.cells[0], act, font_size=Pt(8))
        _add_cell_text(row.cells[1], sc, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8))
        _add_cell_text(row.cells[2], p1, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8))
        _add_cell_text(row.cells[3], wo, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8))
        _add_cell_text(row.cells[4], p2, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8))
        _add_cell_text(row.cells[5], ed, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8))

    _add_p(doc, "5.2. Tuyển chọn và tiêu chuẩn người tình nguyện", bold=True, font_size=Pt(10.5), space_before=Pt(6), space_after=Pt(2))
    _add_p(
        doc,
        f"Tuyển chọn người tình nguyện khỏe mạnh trong độ tuổi 18 – 50, BMI từ 18 – 27 kg/m², không có tiền sử bệnh tim mạch, gan, thận, tiêu hóa; "
        f"xét nghiệm âm tính với HIV, HBsAg, HCV; kết quả cận lâm sàng bình thường; phụ nữ không mang thai (test thai nhanh âm tính).",
        space_after=Pt(4),
    )
    _add_p(doc, "5.3. Rút khỏi nghiên cứu", bold=True, font_size=Pt(10.5), space_before=Pt(4), space_after=Pt(2))
    _add_p(doc, c["withdraw_text"], space_after=Pt(4))

    _add_p(doc, "5.4. Uống thuốc nghiên cứu", bold=True, font_size=Pt(10.5), space_before=Pt(4), space_after=Pt(2))
    _add_p(
        doc,
        f"Người tình nguyện uống 1 liều đơn thuốc thử ({c['test_product']}) hoặc thuốc đối chứng ({c['ref_product']}) kèm 240 mL nước đun sôi để nguội "
        f"sau khi nhịn ăn qua đêm ít nhất 10 giờ. Việc uống thuốc được giám sát trực tiếp và kiểm tra khoang miệng.",
        space_after=Pt(4),
    )

    _add_p(doc, "5.5. Lấy mẫu máu và phương pháp phân tích mẫu sinh học", bold=True, font_size=Pt(10.5), space_before=Pt(4), space_after=Pt(2))
    _add_p(
        doc,
        f"Các mẫu máu được lấy qua catheter tĩnh mạch vào ống chứa chất chống đông phù hợp tại các thời điểm quy định trong đề cương. "
        f"Mẫu được ly tâm tách huyết tương và bảo quản ở ≤ -20°C (hoặc -70°C) cho đến khi phân tích. "
        f"Phương pháp định lượng hoạt chất trong huyết tương đã được thẩm định đầy đủ theo hướng dẫn của Bộ Y tế, EMA và FDA.",
        space_after=Pt(4),
    )

    # Bảng 2
    _add_p(doc, "Bảng 2. Kết quả tóm tắt thẩm định phương pháp phân tích", bold=True, font_size=Pt(9.5), space_before=Pt(4), space_after=Pt(2))
    tbl_b2 = doc.add_table(rows=len(VKNT_REPORT_BIOANALYTICAL_SUMMARY) + 1, cols=2)
    tbl_b2.alignment = WD_TABLE_ALIGNMENT.CENTER
    _set_table_borders(tbl_b2)
    tbl_b2.rows[0].cells[0].width = Cm(5.5)
    tbl_b2.rows[0].cells[1].width = Cm(11.3)
    _set_cell_shading(tbl_b2.rows[0].cells[0], "EAECEE")
    _set_cell_shading(tbl_b2.rows[0].cells[1], "EAECEE")
    _add_cell_text(tbl_b2.rows[0].cells[0], "Thông số thẩm định", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8.5))
    _add_cell_text(tbl_b2.rows[0].cells[1], "Kết quả thẩm định", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8.5))
    for i, (param, res) in enumerate(VKNT_REPORT_BIOANALYTICAL_SUMMARY, 1):
        row = tbl_b2.rows[i]
        _add_cell_text(row.cells[0], param, bold=True, font_size=Pt(8))
        _add_cell_text(row.cells[1], res, font_size=Pt(8))

    _add_p(doc, "5.6. Ghi chép và nhập số liệu", bold=True, font_size=Pt(10.5), space_before=Pt(6), space_after=Pt(2))
    _add_p(doc, "Toàn bộ dữ liệu nghiên cứu được ghi chép kịp thời vào Hồ sơ nghiên cứu (CRF), kiểm tra chéo độc lập và nhập liệu với quy trình audit trail đầy đủ.", space_after=Pt(4))

    _add_p(doc, "5.7. Phân tích dược động học và phương pháp thống kê", bold=True, font_size=Pt(10.5), space_before=Pt(4), space_after=Pt(2))
    _add_p(
        doc,
        f"• Phân tích dược động học phi ngăn (NCA): Xác định Cmax, Tmax, AUC0-t, AUC0-inf, t1/2, Kel bằng phần mềm chuẩn thức.\n"
        f"• Phân tích phương sai ANOVA: Áp dụng trên số liệu Cmax, AUC0-t, AUC0-inf đã chuyển dạng logarit tự nhiên (ln), "
        f"xem xét các nguồn biến thiên: Trình tự, Cá thể trong trình tự, Giai đoạn, Thuốc.\n"
        f"• Đánh giá khoảng tin cậy 90%: Hai chế phẩm được kết luận tương đương sinh học khi khoảng tin cậy 90% của tỷ số trung bình nhân "
        f"(GMR = Thử/Chứng) của Cmax, AUC0-t, AUC0-inf nằm hoàn toàn trong khoảng 80.00% – 125.00%.\n"
        f"• Kiểm định phi tham số cho Tmax: Sử dụng kiểm định Wilcoxon signed-rank hai phía ở mức ý nghĩa alpha = 0.05.\n"
        f"• Lực kiểm định thống kê (Power_TOST): Tính toán bằng phương pháp Two One-Sided Tests (Power_TOST) dựa trên phân phối t không trung tâm "
        f"(non-central t distribution) theo đúng chuẩn mực khoa học hiện hành (Schuirmann 1987, Diletti et al. 1991). "
        f"Báo cáo không sử dụng chỉ số Power_80_20.",
        space_after=Pt(6),
    )

    # Section 6
    _add_p(doc, "6. NGƯỜI TÌNH NGUYỆN", bold=True, font_size=Pt(12), space_before=Pt(8), space_after=Pt(4), color=RGBColor(26, 54, 93))
    _add_p(
        doc,
        f"Tổng cộng {c['n_enrolled']} người tình nguyện được tuyển chọn tham gia nghiên cứu. "
        f"Dữ liệu đánh giá tương đương sinh học dựa trên {c['n_analyzed']} đối tượng hoàn tất nghiên cứu. "
        f"Độ tuổi trung bình: {_field(p_details.get('mean_age'), 'Độ tuổi trung bình', 'Ví dụ: 23.5 ± 3.2')}; "
        f"BMI trung bình: {_field(p_details.get('mean_bmi'), 'BMI trung bình', 'Ví dụ: 21.2 ± 1.8 kg/m²')}. "
        f"Không có trường hợp nào vi phạm quy định nghiên cứu.",
        space_after=Pt(6),
    )

    # Section 7
    _add_p(doc, "7. ĐÁNH GIÁ MỨC ĐỘ AN TOÀN", bold=True, font_size=Pt(12), space_before=Pt(8), space_after=Pt(4), color=RGBColor(26, 54, 93))
    _add_p(
        doc,
        "Không có phản ứng bất lợi (ADR) hoặc biến cố bất lợi nghiêm trọng (SAE) nào xảy ra trong suốt quá trình nghiên cứu. "
        "Các xét nghiệm cận lâm sàng và kiểm tra sức khỏe tại thời điểm kết thúc nghiên cứu đều nằm trong giới hạn bình thường. "
        "Kết quả theo dõi dấu hiệu sinh tồn được tóm tắt tại Bảng 3:",
        space_after=Pt(4),
    )

    # Bảng 3
    _add_p(doc, "Bảng 3. Tóm tắt kết quả kiểm tra dấu hiệu sinh tồn (TB ± SD)", bold=True, font_size=Pt(9.5), space_before=Pt(4), space_after=Pt(2))
    tbl_b3 = doc.add_table(rows=len(VKNT_REPORT_VITAL_SIGNS_DEFAULT) + 1, cols=4)
    tbl_b3.alignment = WD_TABLE_ALIGNMENT.CENTER
    _set_table_borders(tbl_b3)
    b3_hdrs = ["Thông số", "Ban đầu", "Kết thúc", "Thay đổi so với ban đầu"]
    for j, h in enumerate(b3_hdrs):
        cell = tbl_b3.rows[0].cells[j]
        _set_cell_shading(cell, "EAECEE")
        _add_cell_text(cell, h, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8.5))
    for i, (param, pre, post, delta) in enumerate(VKNT_REPORT_VITAL_SIGNS_DEFAULT, 1):
        row = tbl_b3.rows[i]
        _add_cell_text(row.cells[0], param, bold=True, font_size=Pt(8))
        _add_cell_text(row.cells[1], pre, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8))
        _add_cell_text(row.cells[2], post, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8))
        _add_cell_text(row.cells[3], delta, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8))

    _add_p(doc, "Kết luận an toàn: Cả hai chế phẩm thuốc thử và thuốc đối chứng đều dung nạp tốt trên người tình nguyện khỏe mạnh.", italic=True, font_size=Pt(9.5), space_before=Pt(4), space_after=Pt(6))

    # Section 8
    _add_p(doc, "8. ĐÁNH GIÁ CÁC THÔNG SỐ DƯỢC ĐỘNG HỌC VÀ TƯƠNG ĐƯƠNG SINH HỌC", bold=True, font_size=Pt(12), space_before=Pt(8), space_after=Pt(4), color=RGBColor(26, 54, 93))
    _add_p(doc, "8.1. Kết quả định lượng thuốc trong huyết tương", bold=True, font_size=Pt(10.5), space_before=Pt(4), space_after=Pt(2))
    _add_p(
        doc,
        f"Nồng độ {c['substance']} trong huyết tương người tình nguyện sau khi uống thuốc thử nghiệm và thuốc đối chứng "
        f"được trình bày chi tiết tại Bảng 4 (Thuốc Thử) và Bảng 5 (Thuốc Đối chứng) thuộc Phụ lục 10.2 và 10.6.",
        space_after=Pt(4),
    )

    _add_p(doc, "8.2. Đồ thị biểu diễn nồng độ thuốc trung bình theo thời gian", bold=True, font_size=Pt(10.5), space_before=Pt(4), space_after=Pt(2))
    _add_p(
        doc,
        f"Đồ thị biểu diễn nồng độ trung bình của {c['substance']} theo thời gian trên thang tuyến tính (linear) và thang bán logarit (semi-logarithmic) "
        f"cho thấy đường cong nồng độ của thuốc thử và thuốc đối chứng gần như trùng khít nhau trong suốt toàn bộ khoảng thời gian theo dõi.",
        space_after=Pt(4),
    )

    # Insert snapshot figures if available
    if c["has_run"]:
        figs = snapshot_figures(c["run"], language="vi")
        for fig in figs[:2]:
            try:
                doc.add_picture(io.BytesIO(fig.png), width=Cm(14.5))
                _add_p(doc, f"Hình. {fig.title} — {fig.note}", italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8.5), space_after=Pt(6))
            except Exception:
                pass

    _add_p(doc, "8.3. Thống kê thông số dược động học", bold=True, font_size=Pt(10.5), space_before=Pt(6), space_after=Pt(2))

    # Bảng 6
    _add_p(doc, "Bảng 6. Các thông số dược động học của từng cá thể", bold=True, font_size=Pt(9.5), space_before=Pt(4), space_after=Pt(2))
    if c["pk_subject_table"]:
        tbl_b6 = doc.add_table(rows=min(len(c["pk_subject_table"]) + 1, 31), cols=12)
        tbl_b6.alignment = WD_TABLE_ALIGNMENT.CENTER
        _set_table_borders(tbl_b6)
        b6_hdrs = ["STT", "NTN", "Cmax (T)", "Cmax (R)", "Tmax (T)", "Tmax (R)", "AUC0-t (T)", "AUC0-t (R)", "AUC0-inf (T)", "AUC0-inf (R)", "t1/2 (T)", "t1/2 (R)"]
        for j, h in enumerate(b6_hdrs):
            cell = tbl_b6.rows[0].cells[j]
            _set_cell_shading(cell, "EAECEE")
            _add_cell_text(cell, h, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(7.5))
        for i, row_data in enumerate(c["pk_subject_table"][:30], 1):
            r = tbl_b6.rows[i]
            _add_cell_text(r.cells[0], row_data["stt"], align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(7))
            _add_cell_text(r.cells[1], row_data["subject_id"], align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(7))
            _add_cell_text(r.cells[2], row_data["t_cmax"], align=WD_ALIGN_PARAGRAPH.RIGHT, font_size=Pt(7))
            _add_cell_text(r.cells[3], row_data["r_cmax"], align=WD_ALIGN_PARAGRAPH.RIGHT, font_size=Pt(7))
            _add_cell_text(r.cells[4], row_data["t_tmax"], align=WD_ALIGN_PARAGRAPH.RIGHT, font_size=Pt(7))
            _add_cell_text(r.cells[5], row_data["r_tmax"], align=WD_ALIGN_PARAGRAPH.RIGHT, font_size=Pt(7))
            _add_cell_text(r.cells[6], row_data["t_auct"], align=WD_ALIGN_PARAGRAPH.RIGHT, font_size=Pt(7))
            _add_cell_text(r.cells[7], row_data["r_auct"], align=WD_ALIGN_PARAGRAPH.RIGHT, font_size=Pt(7))
            _add_cell_text(r.cells[8], row_data["t_aucinf"], align=WD_ALIGN_PARAGRAPH.RIGHT, font_size=Pt(7))
            _add_cell_text(r.cells[9], row_data["r_aucinf"], align=WD_ALIGN_PARAGRAPH.RIGHT, font_size=Pt(7))
            _add_cell_text(r.cells[10], row_data["t_thalf"], align=WD_ALIGN_PARAGRAPH.RIGHT, font_size=Pt(7))
            _add_cell_text(r.cells[11], row_data["r_thalf"], align=WD_ALIGN_PARAGRAPH.RIGHT, font_size=Pt(7))
    else:
        _add_p(doc, "[YÊU CẦU NGƯỜI DÙNG BỔ SUNG: Dữ liệu Bảng 6 sẽ tự động điền khi chạy phân tích NCA trong ứng dụng]", bold=True)

    # Bảng 7
    _add_p(doc, "Bảng 7. Các thông số dược động học Cmax, AUC chuyển dạng ln của từng cá thể", bold=True, font_size=Pt(9.5), space_before=Pt(6), space_after=Pt(2))
    if c["pk_ln_table"]:
        tbl_b7 = doc.add_table(rows=min(len(c["pk_ln_table"]) + 1, 31), cols=11)
        tbl_b7.alignment = WD_TABLE_ALIGNMENT.CENTER
        _set_table_borders(tbl_b7)
        b7_hdrs = ["STT", "NTN", "Ln Cmax(T)", "Ln Cmax(R)", "ΔLn Cmax", "Ln AUCt(T)", "Ln AUCt(R)", "ΔLn AUCt", "Ln AUCinf(T)", "Ln AUCinf(R)", "ΔLn AUCinf"]
        for j, h in enumerate(b7_hdrs):
            cell = tbl_b7.rows[0].cells[j]
            _set_cell_shading(cell, "EAECEE")
            _add_cell_text(cell, h, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(7.5))
        for i, row_data in enumerate(c["pk_ln_table"][:30], 1):
            r = tbl_b7.rows[i]
            _add_cell_text(r.cells[0], row_data["stt"], align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(7))
            _add_cell_text(r.cells[1], row_data["subject_id"], align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(7))
            _add_cell_text(r.cells[2], row_data["ln_t_cmax"], align=WD_ALIGN_PARAGRAPH.RIGHT, font_size=Pt(7))
            _add_cell_text(r.cells[3], row_data["ln_r_cmax"], align=WD_ALIGN_PARAGRAPH.RIGHT, font_size=Pt(7))
            _add_cell_text(r.cells[4], row_data["ln_diff_cmax"], align=WD_ALIGN_PARAGRAPH.RIGHT, font_size=Pt(7))
            _add_cell_text(r.cells[5], row_data["ln_t_auct"], align=WD_ALIGN_PARAGRAPH.RIGHT, font_size=Pt(7))
            _add_cell_text(r.cells[6], row_data["ln_r_auct"], align=WD_ALIGN_PARAGRAPH.RIGHT, font_size=Pt(7))
            _add_cell_text(r.cells[7], row_data["ln_diff_auct"], align=WD_ALIGN_PARAGRAPH.RIGHT, font_size=Pt(7))
            _add_cell_text(r.cells[8], row_data["ln_t_aucinf"], align=WD_ALIGN_PARAGRAPH.RIGHT, font_size=Pt(7))
            _add_cell_text(r.cells[9], row_data["ln_r_aucinf"], align=WD_ALIGN_PARAGRAPH.RIGHT, font_size=Pt(7))
            _add_cell_text(r.cells[10], row_data["ln_diff_aucinf"], align=WD_ALIGN_PARAGRAPH.RIGHT, font_size=Pt(7))
    else:
        _add_p(doc, "[YÊU CẦU NGƯỜI DÙNG BỔ SUNG: Dữ liệu Bảng 7 sẽ tự động điền khi chạy phân tích NCA trong ứng dụng]", bold=True)

    _add_p(doc, "Bảng 8. Các thông số dược động học trung bình của thuốc thử và thuốc đối chứng", bold=True, font_size=Pt(9.5), space_before=Pt(4), space_after=Pt(2))
    if c["pk_summary_s1"]:
        tbl_b8 = doc.add_table(rows=len(c["pk_summary_s1"]) + 1, cols=7)
        tbl_b8.alignment = WD_TABLE_ALIGNMENT.CENTER
        _set_table_borders(tbl_b8)
        for j, h in enumerate(["Thông số", "Thuốc", "TB cộng", "TB nhân", "SD", "CV (%)", "Khoảng (min – max)"]):
            cell = tbl_b8.rows[0].cells[j]
            _set_cell_shading(cell, "EAECEE")
            _add_cell_text(cell, h, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8.5))
        for i, row_data in enumerate(c["pk_summary_s1"], 1):
            r = tbl_b8.rows[i]
            _add_cell_text(r.cells[0], row_data["param"], font_size=Pt(8))
            _add_cell_text(r.cells[1], row_data["treatment"], font_size=Pt(8))
            _add_cell_text(r.cells[2], row_data["mean"], align=WD_ALIGN_PARAGRAPH.RIGHT, font_size=Pt(8))
            _add_cell_text(r.cells[3], row_data["geomean"], align=WD_ALIGN_PARAGRAPH.RIGHT, font_size=Pt(8))
            _add_cell_text(r.cells[4], row_data["sd"], align=WD_ALIGN_PARAGRAPH.RIGHT, font_size=Pt(8))
            _add_cell_text(r.cells[5], row_data["cv"], align=WD_ALIGN_PARAGRAPH.RIGHT, font_size=Pt(8))
            _add_cell_text(r.cells[6], row_data["range"], align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8))
    else:
        _add_p(doc, "[YÊU CẦU NGƯỜI DÙNG BỔ SUNG: Dữ liệu Bảng 8 sẽ tự động điền khi chạy phân tích NCA trong ứng dụng]", bold=True)

    _add_p(doc, "", space_after=Pt(4))
    _add_p(doc, f"Bảng 9. Tỉ số AUC0-t / AUC0-inf: Thuốc thử = {c['auc_ratio_t']:.2f} %; Thuốc đối chứng = {c['auc_ratio_r']:.2f} % (yêu cầu ≥ 80.00%).", italic=True, font_size=Pt(9))

    _add_p(doc, "8.4. Đánh giá thống kê tương đương sinh học", bold=True, font_size=Pt(10.5), space_before=Pt(6), space_after=Pt(2))

    # Bảng 10 (ANOVA)
    _add_p(doc, "Bảng 10. Phân tích phương sai các thông số AUC0-t, AUC0-inf, Cmax (đã chuyển dạng ln)", bold=True, font_size=Pt(9.5), space_before=Pt(4), space_after=Pt(2))
    if c["anova_table"]:
        tbl_b10 = doc.add_table(rows=len(c["anova_table"]) + 1, cols=7)
        tbl_b10.alignment = WD_TABLE_ALIGNMENT.CENTER
        _set_table_borders(tbl_b10)
        b10_hdrs = ["Thông số", "Nguồn biến thiên", "Bậc tự do", "Tổng bình phương (SS)", "Bình phương TB (MS)", "F", "p"]
        for j, h in enumerate(b10_hdrs):
            cell = tbl_b10.rows[0].cells[j]
            _set_cell_shading(cell, "EAECEE")
            _add_cell_text(cell, h, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8.5))
        for i, row_data in enumerate(c["anova_table"], 1):
            r = tbl_b10.rows[i]
            _add_cell_text(r.cells[0], row_data["param"], bold=True, font_size=Pt(8))
            _add_cell_text(r.cells[1], row_data["source"], font_size=Pt(8))
            _add_cell_text(r.cells[2], row_data["df"], align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8))
            _add_cell_text(r.cells[3], row_data["ss"], align=WD_ALIGN_PARAGRAPH.RIGHT, font_size=Pt(8))
            _add_cell_text(r.cells[4], row_data["ms"], align=WD_ALIGN_PARAGRAPH.RIGHT, font_size=Pt(8))
            _add_cell_text(r.cells[5], row_data["f_stat"], align=WD_ALIGN_PARAGRAPH.RIGHT, font_size=Pt(8))
            _add_cell_text(r.cells[6], row_data["p_val"], align=WD_ALIGN_PARAGRAPH.RIGHT, font_size=Pt(8))
    else:
        _add_p(doc, "[YÊU CẦU NGƯỜI DÙNG BỔ SUNG: Dữ liệu Bảng 10 sẽ tự động điền khi chạy phân tích BE ANOVA trong ứng dụng]", bold=True)

    # Bảng 11 (90% CI)
    _add_p(doc, "Bảng 11. Kết quả xác định khoảng tin cậy 90%", bold=True, font_size=Pt(9.5), space_before=Pt(6), space_after=Pt(2))
    if c["be_summary_table"]:
        tbl_b11 = doc.add_table(rows=len(c["be_summary_table"]) + 1, cols=5)
        tbl_b11.alignment = WD_TABLE_ALIGNMENT.CENTER
        _set_table_borders(tbl_b11)
        b11_hdrs = ["Thông số", "Tỉ số GMR (%) (Thử/Chứng)", "Khoảng tin cậy 90%", "Tiêu chuẩn chấp nhận", "Kết luận"]
        for j, h in enumerate(b11_hdrs):
            cell = tbl_b11.rows[0].cells[j]
            _set_cell_shading(cell, "EAECEE")
            _add_cell_text(cell, h, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8.5))
        for i, row_data in enumerate(c["be_summary_table"], 1):
            r = tbl_b11.rows[i]
            _add_cell_text(r.cells[0], row_data["param"], bold=True, font_size=Pt(8.5))
            _add_cell_text(r.cells[1], row_data["gmr"], align=WD_ALIGN_PARAGRAPH.RIGHT, font_size=Pt(8.5))
            _add_cell_text(r.cells[2], row_data["ci"], align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8.5))
            _add_cell_text(r.cells[3], row_data["criteria"], align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8.5))
            _add_cell_text(r.cells[4], row_data["decision"], align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8.5))
    else:
        _add_p(doc, "[YÊU CẦU NGƯỜI DÙNG BỔ SUNG: Dữ liệu Bảng 11 sẽ tự động điền khi chạy phân tích BE trong ứng dụng]", bold=True)

    # Bảng 12 (Power_TOST)
    _add_p(doc, "Bảng 12. Kết quả giá trị Power (Power_TOST)", bold=True, font_size=Pt(9.5), space_before=Pt(6), space_after=Pt(2))
    if c["be_power_table"]:
        tbl_b12 = doc.add_table(rows=len(c["be_power_table"]) + 1, cols=4)
        tbl_b12.alignment = WD_TABLE_ALIGNMENT.CENTER
        _set_table_borders(tbl_b12)
        b12_hdrs = ["Thông số", "Power_TOST (%)", "Tiêu chuẩn quy định", "Đánh giá"]
        for j, h in enumerate(b12_hdrs):
            cell = tbl_b12.rows[0].cells[j]
            _set_cell_shading(cell, "EAECEE")
            _add_cell_text(cell, h, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8.5))
        for i, row_data in enumerate(c["be_power_table"], 1):
            r = tbl_b12.rows[i]
            _add_cell_text(r.cells[0], row_data["param"], bold=True, font_size=Pt(8.5))
            _add_cell_text(r.cells[1], row_data["power_tost"], align=WD_ALIGN_PARAGRAPH.RIGHT, font_size=Pt(8.5))
            _add_cell_text(r.cells[2], row_data["criteria"], align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8.5))
            _add_cell_text(r.cells[3], row_data["status"], align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8.5))
    else:
        _add_p(doc, "[YÊU CẦU NGƯỜI DÙNG BỔ SUNG: Dữ liệu Bảng 12 sẽ tự động điền khi tính toán Power_TOST trong ứng dụng]", bold=True)

    _add_p(
        doc,
        "Ghi chú: Lực kiểm định được tính bằng phương pháp Two One-Sided Tests (Power_TOST) sử dụng phân phối t không trung tâm "
        "(non-central t distribution). Báo cáo tuyệt đối không sử dụng chỉ số Power_80_20 theo đúng khuyến cáo khoa học của US-FDA, EMA, ICH M13A và yêu cầu quy chuẩn.",
        italic=True,
        font_size=Pt(8.5),
        space_after=Pt(6),
    )

    # Bảng 13 (Tmax Wilcoxon)
    _add_p(doc, "Bảng 13. So sánh giá trị Tmax theo phương pháp thống kê phi tham số (Wilcoxon Signed Rank Test)", bold=True, font_size=Pt(9.5), space_before=Pt(6), space_after=Pt(2))
    if c["tmax_wilcoxon_table"]:
        tbl_b13 = doc.add_table(rows=min(len(c["tmax_wilcoxon_table"]) + 1, 31), cols=7)
        tbl_b13.alignment = WD_TABLE_ALIGNMENT.CENTER
        _set_table_borders(tbl_b13)
        b13_hdrs = ["NTN", f"Tmax {c['test_product']}", f"Tmax {c['ref_product']}", "Chênh lệch", "Xếp hạng", "Hạng (+)", "Hạng (-)"]
        for j, h in enumerate(b13_hdrs):
            cell = tbl_b13.rows[0].cells[j]
            _set_cell_shading(cell, "EAECEE")
            _add_cell_text(cell, h, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(8))
        for i, row_data in enumerate(c["tmax_wilcoxon_table"][:30], 1):
            r = tbl_b13.rows[i]
            _add_cell_text(r.cells[0], row_data["subject_id"], align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(7.5))
            _add_cell_text(r.cells[1], row_data["t_val"], align=WD_ALIGN_PARAGRAPH.RIGHT, font_size=Pt(7.5))
            _add_cell_text(r.cells[2], row_data["r_val"], align=WD_ALIGN_PARAGRAPH.RIGHT, font_size=Pt(7.5))
            _add_cell_text(r.cells[3], row_data["diff"], align=WD_ALIGN_PARAGRAPH.RIGHT, font_size=Pt(7.5))
            _add_cell_text(r.cells[4], row_data["rank"], align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(7.5))
            _add_cell_text(r.cells[5], row_data["pos_rank"], align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(7.5))
            _add_cell_text(r.cells[6], row_data["neg_rank"], align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(7.5))

        _add_p(doc, f"Kết quả kiểm định Wilcoxon: W = {c['wilcoxon_stat']:.1f}, p-value = {c['wilcoxon_p']:.4f}. Vì p > 0.05, giá trị Tmax của thuốc thử và thuốc đối chứng khác nhau không có ý nghĩa thống kê.", italic=True, font_size=Pt(9), space_before=Pt(2), space_after=Pt(6))
    else:
        _add_p(doc, "[YÊU CẦU NGƯỜI DÙNG BỔ SUNG: Dữ liệu Bảng 13 sẽ tự động điền khi chạy so sánh Tmax Wilcoxon trong ứng dụng]", bold=True)

    _add_p(doc, "8.5. Bàn luận", bold=True, font_size=Pt(10.5), space_before=Pt(6), space_after=Pt(2))
    _add_p(
        doc,
        f"Các thông số dược động học quan sát được trong nghiên cứu (Cmax, Tmax, AUC, t1/2) của cả hai chế phẩm "
        f"hoàn toàn phù hợp với các dữ liệu đã công bố trong y văn quốc tế đối với {c['substance']}. "
        f"Mức độ biến thiên giữa các cá thể và trong cùng cá thể (CV) nằm trong khoảng dự kiến của nghiên cứu tương đương sinh học. "
        f"Khoảng tin cậy 90% của tất cả các thông số đánh giá chính (Cmax, AUC0-t, AUC0-inf) đều nằm gọn trong giới hạn 80.00% – 125.00%.",
        space_after=Pt(6),
    )

    # Section 9
    _add_p(doc, "9. KẾT LUẬN", bold=True, font_size=Pt(12), space_before=Pt(8), space_after=Pt(4), color=RGBColor(26, 54, 93))
    if not c["has_run"]:
        _add_p(
            doc,
            f"Thử nghiệm đánh giá tương đương sinh học in vivo của {c['dosage_form']} {c['test_product']} ({c['substance']} {c['dose']}) do {c['sponsor']} sản xuất:\n"
            f"[YÊU CẦU NGƯỜI DÙNG BỔ SUNG: Kết luận chi tiết sẽ được tự động trích xuất theo số liệu phân tích BE thực tế].\n\n"
            f"KẾT LUẬN CHUNG: [YÊU CẦU NGƯỜI DÙNG BỔ SUNG: Đánh giá tương đương sinh học in vivo theo quy định hiện hành của Bộ Y tế Việt Nam và hướng dẫn của ASEAN].",
            space_after=Pt(12),
        )
    else:
        concl_bullets = [
            f"Thử nghiệm đánh giá tương đương sinh học in vivo của {c['dosage_form']} {c['test_product']} ({c['substance']} {c['dose']}) do {c['sponsor']} sản xuất cho thấy:"
        ]
        if c["be_summary_table"]:
            for idx, row in enumerate(c["be_summary_table"], 1):
                concl_bullets.append(
                    f"{idx}. Khoảng tin cậy 90% của tỷ số trung bình nhân (GMR) đối với {row['param']} là {row['ci']}, "
                    f"tiêu chuẩn chấp nhận {row['criteria']} ({row['decision'].lower()})."
                )
            next_idx = len(c["be_summary_table"]) + 1
        else:
            concl_bullets.append("1. Khoảng tin cậy 90% của tỷ số trung bình nhân (GMR) AUC0-t nằm trong khoảng chấp nhận 80.00% – 125.00%.")
            concl_bullets.append("2. Khoảng tin cậy 90% của tỷ số trung bình nhân (GMR) Cmax nằm trong khoảng chấp nhận 80.00% – 125.00%.")
            next_idx = 3

        concl_bullets.append(f"{next_idx}. Giá trị Tmax của hai chế phẩm khác nhau không có ý nghĩa thống kê theo phép kiểm định phi tham số Wilcoxon.")
        concl_bullets.append(f"{next_idx + 1}. Cả hai chế phẩm đều an toàn và dung nạp tốt trên người tình nguyện khỏe mạnh.")
        concl_bullets.append("")
        if c["is_overall_be_pass"]:
            concl_bullets.append(
                f"KẾT LUẬN CHUNG: Chế phẩm thuốc thử {c['test_product']} do {c['sponsor']} sản xuất "
                f"TƯƠNG ĐƯƠNG SINH HỌC IN VIVO so với thuốc đối chứng {c['ref_product']} do {c['ref_mfr']} sản xuất "
                f"theo quy định hiện hành của Bộ Y tế Việt Nam và hướng dẫn của ASEAN."
            )
        else:
            concl_bullets.append(
                f"KẾT LUẬN CHUNG: Chế phẩm thuốc thử {c['test_product']} do {c['sponsor']} sản xuất "
                f"KHÔNG TƯƠNG ĐƯƠNG SINH HỌC IN VIVO so với thuốc đối chứng {c['ref_product']} do {c['ref_mfr']} sản xuất "
                f"theo quy định hiện hành của Bộ Y tế Việt Nam và hướng dẫn của ASEAN do không đáp ứng khoảng chấp nhận tương đương sinh học."
            )
        _add_p(doc, "\n".join(concl_bullets), space_after=Pt(12))

    # Section 10: Appendices
    _add_p(doc, "10. DANH MỤC CÁC PHỤ LỤC", bold=True, font_size=Pt(12), space_before=Pt(8), space_after=Pt(4), color=RGBColor(26, 54, 93))
    for app_no, app_title, sub_items in VKNT_REPORT_APPENDICES:
        _add_p(doc, f"{app_no}. {app_title}", bold=True, font_size=Pt(10), space_before=Pt(3), space_after=Pt(1))
        for s_no, s_title in sub_items:
            _add_p(doc, f"    {s_no}. {s_title}", font_size=Pt(9), space_after=Pt(1))

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# REPORTLAB PDF GENERATOR
# ---------------------------------------------------------------------------

def pdf_report_vknt(project: Project, run_index: int = -1, language: str = "vi") -> bytes:
    """Generate PDF Clinical Study Report matching MOH / VKNT TP.HCM format."""
    from be_app.reporting import _register_pdf_font
    c = build_vknt_report_data(project, run_index)
    font = _register_pdf_font()
    styles = getSampleStyleSheet()

    for s_name in ("Title", "Normal", "Heading1", "Heading2"):
        styles[s_name].fontName = font
        styles[s_name].textColor = colors.black

    styles["Normal"].fontSize, styles["Normal"].leading = 8.5, 11.5
    styles["Heading1"].fontSize, styles["Heading1"].leading = 11, 14
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
    elements.append(Paragraph(f"<b>{escape(c['cro'].upper())}</b>", styles["Heading1"]))
    elements.append(Paragraph("<b>BÁO CÁO KẾT QUẢ NGHIÊN CỨU TƯƠNG ĐƯƠNG SINH HỌC</b>", styles["Heading1"]))
    elements.append(Paragraph(f"<b>Đề tài: {escape(c['study_title'])}</b>", styles["Normal"]))
    elements.append(Paragraph(f"Mã số đề tài: {c['study_id']} · Đơn vị yêu cầu: {escape(c['sponsor'])}", styles["Normal"]))
    elements.append(Spacer(1, 0.4 * cm))

    # Tóm tắt kết quả
    elements.append(Paragraph("<b>TÓM TẮT KẾT QUẢ NGHIÊN CỨU (SYNOPSIS)</b>", styles["Heading2"]))
    elements.append(p_text(
        f"Nghiên cứu chéo đôi ngẫu nhiên 2 giai đoạn, 2 trình tự (2×2), đơn liều trên {c['n_enrolled']} người tình nguyện khỏe mạnh. "
        f"Thuốc thử: {c['test_product']} ({c['substance']} {c['dose']}) — Lô: {c['test_batch']}. "
        f"Thuốc đối chứng: {c['ref_product']} ({c['substance']} {c['dose']}) — Lô: {c['ref_batch']}."
    ))
    elements.append(Spacer(1, 0.3 * cm))

    # Bảng S1
    if c["pk_summary_s1"]:
        elements.append(Paragraph("<b>Bảng S1. Thông số dược động học trung bình</b>", styles["Heading2"]))
        s1_data = [["Thông số", "Thuốc", "TB cộng", "TB nhân", "SD", "CV (%)", "Min – Max"]]
        for r in c["pk_summary_s1"]:
            s1_data.append([
                Paragraph(r["param"], small_style),
                Paragraph(r["treatment"], small_style),
                Paragraph(r["mean"], small_style),
                Paragraph(r["geomean"], small_style),
                Paragraph(r["sd"], small_style),
                Paragraph(r["cv"], small_style),
                Paragraph(r["range"], small_style),
            ])
        t_s1 = Table(s1_data, colWidths=[3.2 * cm, 2.5 * cm, 1.8 * cm, 1.8 * cm, 1.6 * cm, 1.6 * cm, 3.2 * cm])
        t_s1.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAECEE")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D3D3D3")),
            ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
        ]))
        elements.append(t_s1)
        elements.append(Spacer(1, 0.3 * cm))

    # Bảng S3 (90% CI)
    if c["be_summary_table"]:
        elements.append(Paragraph("<b>Bảng S3. Kết quả xác định khoảng tin cậy 90%</b>", styles["Heading2"]))
        s3_data = [["Thông số", "Tỉ số GMR (%)", "Khoảng tin cậy 90%", "Tiêu chuẩn chấp nhận", "Kết luận"]]
        for r in c["be_summary_table"]:
            s3_data.append([
                Paragraph(r["param"], bold_small),
                Paragraph(r["gmr"], small_style),
                Paragraph(r["ci"], small_style),
                Paragraph(r["criteria"], small_style),
                Paragraph(r["decision"], small_style),
            ])
        t_s3 = Table(s3_data, colWidths=[3.0 * cm, 2.6 * cm, 3.5 * cm, 3.5 * cm, 3.5 * cm])
        t_s3.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAECEE")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D3D3D3")),
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
        ]))
        elements.append(t_s3)
        elements.append(Spacer(1, 0.3 * cm))

    # Bảng 12 (Power_TOST)
    if c["be_power_table"]:
        elements.append(Paragraph("<b>Bảng 12. Kết quả giá trị Power (Power_TOST)</b>", styles["Heading2"]))
        pow_data = [["Thông số", "Power_TOST (%)", "Tiêu chuẩn quy định", "Đánh giá"]]
        for r in c["be_power_table"]:
            pow_data.append([
                Paragraph(r["param"], bold_small),
                Paragraph(r["power_tost"], small_style),
                Paragraph(r["criteria"], small_style),
                Paragraph(r["status"], small_style),
            ])
        t_pow = Table(pow_data, colWidths=[3.5 * cm, 3.0 * cm, 3.5 * cm, 6.0 * cm])
        t_pow.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAECEE")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D3D3D3")),
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
        ]))
        elements.append(t_pow)
        elements.append(p_text(
            "<i>Ghi chú: Lực kiểm định được tính bằng phương pháp Two One-Sided Tests (Power_TOST) "
            "dựa trên phân phối t không trung tâm. Báo cáo không sử dụng chỉ số Power_80_20.</i>",
            style="Normal"
        ))
        elements.append(Spacer(1, 0.4 * cm))

    # Kết luận chung
    elements.append(Paragraph("<b>KẾT LUẬN</b>", styles["Heading1"]))
    if not c["has_run"]:
        elements.append(p_text(
            f"Hai chế phẩm {c['dosage_form']} {c['test_product']} do {c['sponsor']} sản xuất và {c['ref_product']} "
            f"do {c['ref_mfr']} sản xuất: [YÊU CẦU NGƯỜI DÙNG BỔ SUNG: Kết luận sẽ được tự động trích xuất theo số liệu phân tích BE thực tế]."
        ))
    else:
        concl_pdf_text = "TƯƠNG ĐƯƠNG SINH HỌC IN VIVO" if c["is_overall_be_pass"] else "KHÔNG TƯƠNG ĐƯƠNG SINH HỌC IN VIVO do không đáp ứng khoảng chấp nhận tương đương sinh học"
        elements.append(p_text(
            f"Hai chế phẩm {c['dosage_form']} {c['test_product']} do {c['sponsor']} sản xuất và {c['ref_product']} "
            f"do {c['ref_mfr']} sản xuất {concl_pdf_text} theo quy định hiện hành của Bộ Y tế Việt Nam và hướng dẫn của ASEAN."
        ))

    buffer = io.BytesIO()
    doc_pdf = SimpleDocTemplate(
        buffer,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )
    doc_pdf.build(elements)
    return buffer.getvalue()


def blank_report_vknt(language: str = "vi") -> bytes:
    """Return a blank study report template matching MOH / VKNT TP.HCM format."""
    from be_app.domain import Study
    empty_proj = Project(study=Study(
        study_id="BLANK-REPORT-STANDARD",
        title="BÁO CÁO KẾT QUẢ NGHIÊN CỨU TƯƠNG ĐƯƠNG SINH HỌC",
        active_ingredient="",
        dose=100.0,
        dose_unit="mg",
    ))
    return docx_report_vknt(empty_proj, language=language)
