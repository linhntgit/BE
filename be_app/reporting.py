"""Conservative bilingual CSR/CTD drafts generated only from stored analysis snapshots."""

import io
import json
from pathlib import Path
from xml.sax.saxutils import escape

import pandas as pd
from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import CondPageBreak, LongTable, Paragraph, SimpleDocTemplate, Spacer, TableStyle
from reportlab.platypus import Image as PDFImage

from be_app.be_reporting import be_workbook
from be_app.branding import software_attribution
from be_app.domain import digest
from be_app.imports import csv_bytes
from be_app.persistence import Project, verify_project
from be_app.nca_reporting import nca_workbook
from be_app.report_figures import illustrative_figures, snapshot_figures
from be_app.report_tables import report_tables
from be_app.report_template import build_report_outline
from be_app.state import report_manifest

STATUS = "DRAFT / NOT REGULATORY-READY"


def _display_status(language: str) -> str:
    """Translate the document label without changing the canonical snapshot status."""
    return (
        "BẢN DỰ THẢO — CHƯA ĐỦ ĐIỀU KIỆN NỘP CƠ QUAN QUẢN LÝ"
        if language == "vi" else STATUS
    )
CTD_MAPPING = {
    "CSR": "ICH E3 selected sections (draft scaffold)",
    "2.7.1": "Biopharmaceutic Studies and Associated Analytical Methods (draft summary)",
    "5.3.1.2": "Comparative BA and BE study reports (draft)",
    "SAR": "Statistical analysis and intermediate diagnostics",
}

# Canonical blockers are stored in Vietnamese in immutable analysis snapshots.
# Translate only when rendering; changing stored text would invalidate snapshot hashes.
ENGLISH_BLOCKERS = {
    "Bộ quy tắc không tồn tại.": "The regulatory rule set is unknown.",
    "Phương pháp chưa có triển khai tính toán trong bản này.": "This method has no calculation implementation in this release.",
    "Thiết kế nằm ngoài phạm vi bộ quy tắc.": "The study design is outside the scope of the selected rule.",
    "Bản hiện tại chỉ hỗ trợ IR đường uống, đơn liều.": "This release supports only immediate-release, oral, single-dose studies.",
    "Cờ NTI phải phù hợp profile EMA_NTI/FDA_NTI; không dùng quy tắc HVD cho NTI.": "The NTI flag must match an EMA_NTI/FDA_NTI profile; HVD rules do not apply to NTI.",
    "Trường hợp đặc biệt ngoài IR đơn liều cần profile sản phẩm riêng.": "Special cases outside single-dose IR require a product-specific profile.",
    "Cần xác nhận phương pháp scaling đã định trước trong protocol/SAP.": "The scaling method must be prespecified in the protocol/SAP.",
    "Cần căn cứ HVD, rà soát độ tin cậy CVwR/outlier và ý nghĩa lâm sàng của scaling.": "HVD rationale, CVwR/outlier reliability, and the clinical relevance of scaling must be reviewed.",
    "Chưa ghi nhận rà soát phạm vi guideline/PSG và bằng chứng áp dụng.": "Guideline/PSG applicability review and supporting evidence are missing.",
    "Thiếu mã và phiên bản protocol/SAP.": "Protocol/SAP identifiers and versions are missing.",
    "Thiếu tên hoạt chất để xác định phạm vi sản phẩm.": "The active ingredient is missing for product-scope assessment.",
    "Profile phát hành chỉ cho phép alpha=0.05 và giới hạn 0.8–1.25; custom chưa hỗ trợ.": "This release supports only alpha=0.05 and limits of 0.8–1.25; custom limits are unsupported.",
    "Crossover dưới 12 người có dữ liệu đánh giá theo M13A.": "Fewer than 12 evaluable subjects in the crossover study under M13A.",
    "Parallel cần ít nhất 12 người đánh giá mỗi nhánh theo M13A.": "Parallel studies require at least 12 evaluable subjects per arm under M13A.",
    "Dữ liệu đào tạo/QA hoặc giả lập; không có kết luận BE cấp nghiên cứu thật.": "Training/QA or synthetic data cannot support a real-study BE conclusion.",
    "Chưa xác nhận mục đích nghiên cứu thật; không kết luận BE cấp nghiên cứu.": "Real-study data purpose is unconfirmed; no study-level BE conclusion is permitted.",
    "Chưa khai báo nguồn gốc dữ liệu; không kết luận BE cấp nghiên cứu.": "Data provenance is missing; no study-level BE conclusion is permitted.",
}


def _render_blockers(blockers: list[str], vi: bool) -> str:
    if vi:
        return "; ".join(blockers)
    # Preserve unfamiliar reasons verbatim for traceability rather than silently omitting them.
    return "; ".join(ENGLISH_BLOCKERS.get(reason, reason) for reason in blockers)


def _nca_method_text(config: dict, vi: bool) -> str:
    integration_key = str(config.get("integration") or "unspecified")
    integration = {
        "linear": "linear trapezoidal",
        "linear_up_log_down": "linear-up/log-down trapezoidal",
    }.get(integration_key, integration_key)
    overrides = len(config.get("terminal_overrides", []))
    if vi:
        return (
            f"NCA đơn liều theo thời gian lấy mẫu thực tế, tích phân {integration}. "
            "BLQ được đặt bằng 0 khi tích phân và loại khỏi hồi quy pha cuối. "
            f"Tmax trùng nhau chọn {config.get('tmax_tie', 'first')}; "
            f"pha cuối ≥ {config.get('terminal_min_points', 3)} điểm, "
            f"adjusted R² ≥ {config.get('terminal_min_adj_r2', 0.8)}, "
            f"khoảng thời gian ≥ {config.get('terminal_min_span_half_lives', 1)} lần t½; "
            f"cảnh báo ngoại suy AUC > {config.get('extrapolation_warning_pct', 20)}%. "
            f"Có {overrides} lựa chọn pha cuối theo profile đã lưu (nếu có)."
        )
    return (
        f"Single-dose NCA uses actual sampling times and {integration} integration. "
        "BLQ is zero for integration and excluded from terminal regression. "
        f"Tmax ties: {config.get('tmax_tie', 'first')}; "
        f"terminal phase: at least {config.get('terminal_min_points', 3)} points, "
        f"adjusted R² ≥ {config.get('terminal_min_adj_r2', 0.8)}, "
        f"span ≥ {config.get('terminal_min_span_half_lives', 1)} half-lives; "
        f"AUC extrapolation warning > {config.get('extrapolation_warning_pct', 20)}%. "
        f"Stored profile-specific terminal overrides: {overrides}."
    )


def _be_method_text(run: dict, vi: bool, review: dict | None = None) -> str:
    config = run["be_config"]
    rule = run.get("rule_snapshot", {})
    methods = ", ".join(sorted({r["method"] for r in run["be"]}))
    tmax = run.get("tmax_comparison")
    tmax_text = ""
    if tmax is not None:
        tmax_text = (
            (f"Tmax trên thang giờ gốc: {tmax.get('method') or 'chưa chọn kiểm định'}, "
             f"p hai phía={_fmt(tmax.get('p_value'))}, trạng thái={tmax['status']}. "
             "Phân tích hỗ trợ, không dùng kết luận BE hoặc giới hạn 80–125%.")
            if vi else
            (f"Original-hour Tmax: {tmax.get('method') or 'no test selected'}, "
             f"two-sided p={_fmt(tmax.get('p_value'))}, status={tmax['status']}. "
             "Supportive only; does not determine BE or use 80–125% limits.")
        )
    review_text = run.get("review_status", "unknown")
    if review:
        review_text = f"{review['outcome']} · {review['reviewer']} · {review['timestamp']} · {review['evidence']}"
    confidence = 100 * (1 - 2 * config.get("alpha", 0.05))
    if vi:
        return (
            f"Mô hình trên log tự nhiên; phương pháp theo endpoint: {methods}. "
            f"Alpha một phía {config['alpha']}; CI hai phía {confidence:.0f}%; "
            f"giới hạn ABE mặc định {config['lower']:.4f}–{config['upper']:.4f}, "
            "với giới hạn theo endpoint/scaling nếu rule yêu cầu. "
            f"Parallel variance: {config['parallel_variance']}; "
            f"xử lý missing: {config['missing_policy']} "
            f"({config.get('missing_data_reason') or 'không có căn cứ bổ sung'}). "
            f"Rule {run['rule_set_id']} phiên bản {rule.get('version', '?')}; "
            f"trạng thái review: {review_text}. "
            "LS means điều chỉnh tách khỏi geometric means mô tả; kết luận dùng endpoint chính "
            "và tất cả tiêu chí đặc thù của method (FDA RSABE cần UCB/scaling, không suy từ CI90 riêng lẻ). "
            + tmax_text
        )
    return (
        f"Natural-log model; endpoint methods: {methods}. "
        f"One-sided alpha {config['alpha']}; two-sided {confidence:.0f}% CI; "
        f"default ABE limits {config['lower']:.4f}–{config['upper']:.4f}, "
        "with endpoint/scaled limits where required. "
        f"Parallel variance: {config['parallel_variance']}; missing policy: {config['missing_policy']} "
        f"({config.get('missing_data_reason') or 'no additional rationale'}). "
        f"Rule {run['rule_set_id']} version {rule.get('version', '?')}; "
        f"review status: {review_text}. "
        "Adjusted LS means differ from descriptive geometric means; primary endpoints and all "
        "method-specific criteria govern decisions (FDA RSABE requires UCB/scaling, not CI alone). "
        + tmax_text
    )


def report_content(project: Project, run_index: int = -1, language: str = "vi") -> dict:
    verify_project(project)
    if language not in ("vi", "en"):
        raise ValueError("Ngôn ngữ báo cáo phải là vi hoặc en.")
    if not project.runs:
        raise ValueError("Chưa có analysis snapshot; không tạo kết luận/báo cáo nghiên cứu.")
    run = project.runs[run_index]
    manifest = report_manifest(project, run)
    if run["snapshot_hash"] != digest({k: v for k, v in run.items() if k != "snapshot_hash"}):
        raise ValueError("Snapshot không hợp lệ.")
    vi = language == "vi"
    study = run["study"]
    decision = (
        {
            "PASS": "Đạt tiêu chí thống kê",
            "FAIL": "Không đạt tiêu chí thống kê",
            "NOT EVALUABLE": "Không thể kết luận",
        }
        if vi
        else {x: x for x in ("PASS", "FAIL", "NOT EVALUABLE")}
    )
    rows = []

    def number(result, key):
        value = result.get(key)
        return "—" if value is None else f"{100 * value:.4f}"

    for result in run["be"]:
        rows.append(
            [
                result["endpoint"],
                result["method"],
                str(result["n"]),
                number(result, "gmr"),
                f"{number(result, 'ci_lower')} – {number(result, 'ci_upper')}",
                decision[result["decision"]],
            ]
        )
    sections = [
        (
            "Phiên bản đầu vào thực sự dùng" if vi else "Actual calculation input revision",
            f"input_revision={manifest['input_revision']}; dataset_revision={manifest['dataset_revision']}; "
            f"config_revision={manifest['config_revision']}; input_fingerprint={manifest['input_fingerprint']}",
        ),
        (
            "Mục tiêu và phạm vi" if vi else "Objective and scope",
            (
                "Bản dự thảo phục vụ rà soát nội bộ về tính toán PK và BE. Chưa được thẩm định để nộp cơ quan quản lý."
                if vi
                else "This draft supports independent review of PK and BE computations. It is not qualified for regulatory submission."
            ),
        ),
        (
            "Mục đích và nguồn gốc dữ liệu" if vi else "Data purpose and provenance",
            f"Purpose: {study.get('data_purpose', 'unknown')}; "
            f"provenance: {study.get('data_provenance') or 'not documented'}; "
            f"source: {project.raw_file_name or 'not recorded'}. "
            + ("Dự án cũ mặc định unknown; không suy luận nguồn dữ liệu theo tên file." if vi
               else "Legacy records default to unknown; file names do not establish provenance."),
        ),
        (
            "Thiết kế và sản phẩm" if vi else "Study design and products",
            ("Tên nghiên cứu: " if vi else "Recorded study title: ")
            + f"{study['title']} | {study['design']} | "
            + ({"fasted": "Đói (nhịn ăn)", "fed": "No (sau ăn)"}.get(study['fed_state'], study['fed_state'])
               if vi else {"fasted": "Fasted", "fed": "Fed"}.get(study['fed_state'], study['fed_state']))
            + f" | {study['active_ingredient']} | "
            + ("Thuốc thử: " if vi else "Test: ")
            + f"{study['test_product']} ({study['test_batch']}); "
            + ("Thuốc đối chứng: " if vi else "Reference: ")
            + f"{study['reference_product']} ({study['reference_batch']}). "
            + f"Protocol: {study['protocol']}; SAP: {study['sap']}; "
            + ("liều: " if vi else "dose: ")
            + f"{study['dose']} {study['dose_unit']}.",
        ),
        (
            "Phương pháp NCA" if vi else "NCA methods",
            _nca_method_text(run["nca_config"], vi),
        ),
        (
            "Phương pháp thống kê" if vi else "Statistical methods",
            _be_method_text(run, vi, manifest.get("snapshot_review")),
        ),
        (
            "Kết luận và giới hạn" if vi else "Conclusion and limitations",
            decision[run["study_decision"]]
            + ". "
            + _render_blockers(run["blockers"], vi)
            + " "
            + (
                "Đang chờ rà soát độc lập PK, thống kê, QA và Regulatory Affairs. Chưa có dữ liệu thẩm định assay, "
                "conduct/deviations đầy đủ, chữ ký hoặc chứng nhận eCTD. Không phải CSR E3 hoàn chỉnh."
                if vi
                else "Pending independent PK, statistical, QA and regulatory review. Assay validation, complete conduct and "
                "deviation narratives, signatures and eCTD validation are not supplied. This is not a complete ICH E3 CSR."
            ),
        ),
        (
            "Cấu trúc CTD" if vi else "CTD mapping",
            "; ".join(f"{key}: {value}" for key, value in CTD_MAPPING.items()),
        ),
    ]
    sections.append(
        (
            "Chi tiết thống kê và endpoint" if vi else "Statistical details and endpoints",
            ("Endpoint chính: " if vi else "Primary endpoints: ")
            + ", ".join(study["primary_endpoints"])
            + (". Endpoint bổ sung: " if vi else ". Secondary endpoints: ")
            + (", ".join(study.get("secondary_endpoints", [])) or "—")
            + f". Rule: {study['rule_set_id']}. "
            + (
                "Các bảng dưới đây trình bày từng tiêu chí, scaling, population và thống kê PK của cùng snapshot."
                if vi
                else "The following tables present criteria, scaling, populations and PK statistics from the same snapshot."
            ),
        )
    )
    disclaimers = []
    if study["is_demo"]:
        disclaimers.append(
            "DỮ LIỆU GIẢ LẬP HỌC THỬ / SYNTHETIC LEARNING DATA"
            if vi else "SYNTHETIC LEARNING DATA — FOR TRAINING ONLY"
        )
    if study.get("data_purpose") == "training_qa":
        disclaimers.append(
            "DỮ LIỆU ĐÀO TẠO/QA / TRAINING-QA — NO REAL-STUDY CONCLUSION"
            if vi else "TRAINING-QA DATA — NO REAL-STUDY CONCLUSION"
        )
    outline = build_report_outline(study, run, manifest, language, _render_blockers(run["blockers"], vi))
    for section in outline:
        if section["number"] == "8.4":
            section["body"] += " " + _nca_method_text(run["nca_config"], vi)
        elif section["number"] == "8.5":
            section["body"] += " " + _be_method_text(run, vi, manifest.get("snapshot_review"))
    return dict(
        title=("Báo cáo phân tích tương đương sinh học" if vi else "Bioequivalence analysis report"),
        study_id=study["study_id"],
        demo=study["is_demo"],
        qa=study.get("data_purpose") == "training_qa",
        disclaimers=disclaimers,
        sections=sections,
        outline=outline,
        rows=rows,
        run=run,
        manifest=manifest,
        reviewer_tables=report_tables(run, language),
        headings=(
            ["Endpoint", "Phương pháp", "N", "GMR %", "CI 90%", "Kết quả"]
            if vi
            else ["Endpoint", "Method", "N", "GMR %", "90% CI", "Decision"]
        ),
    )


def _fmt(value):
    return "—" if value is None else f"{value:.5g}"


def _append_docx_figures(doc, figures, language: str, *, template: bool) -> None:
    """Append numbered, captioned pictures; keep them separate from evidence tables."""
    doc.add_heading(
        "11.12 Hình và đồ thị minh họa" if language == "vi" else "11.12 Figures and visualizations",
        level=2,
    )
    if template:
        doc.add_paragraph(
            "Ví dụ phương pháp tham khảo: đề cương NCT03083639, Esomeprazole-1001 "
            "(07/03/2017), nghiên cứu pha 1 ngẫu nhiên, nhãn mở, bắt chéo 2 kỳ với trình tự TR/RT; "
            "52 người dự kiến, nhịn ăn ít nhất 10 giờ, washout ít nhất 6 ngày và lấy mẫu đến 10 giờ. "
            "Những con số này là KẾ HOẠCH trong protocol, không phải kết quả hay số liệu đo được. "
            "Tất cả đồ thị bên dưới là ví dụ GIẢ LẬP để giảng dạy và phải thay bằng dữ liệu nghiên cứu đã thẩm định."
            if language == "vi" else
            "Methodological example: NCT03083639, Esomeprazole-1001 protocol dated 07 Mar 2017; "
            "randomized open-label two-period crossover TR/RT; planned 52 subjects, at least 10 h "
            "fasting, at least 6 d washout, samples through 10 h. These are PROTOCOL PLANS, "
            "not observed study results. All figures below are SYNTHETIC teaching illustrations."
        )
    else:
        doc.add_paragraph(
            "Các hình nồng độ và CI được vẽ lại từ dữ liệu/snapshot của run này. "
            "Sơ đồ thiết kế (nếu có) chỉ minh họa trình tự; không phải dữ liệu thực nghiệm. "
            "Các tiêu chí ABEL, RSABE hoặc NTI phải đánh giá riêng ngoài hình CI90."
            if language == "vi" else
            "Concentration plots and confidence intervals are generated from this analysis snapshot. "
            "The design schematic, when present, is illustrative. ABEL, RSABE and NTI rules "
            "must be evaluated separately from the CI90 figure."
        )
    for index, figure in enumerate(figures, start=1):
        doc.add_heading(f"11.12.{index} {figure.title}", level=3)
        picture = doc.add_paragraph()
        picture.alignment = WD_ALIGN_PARAGRAPH.CENTER
        picture.add_run().add_picture(io.BytesIO(figure.png), width=Cm(16.6))
        caption = doc.add_paragraph(f"{'Hình' if language == 'vi' else 'Figure'} {index}. {figure.note}")
        caption.paragraph_format.keep_together = True
        for span in caption.runs:
            span.italic = True
            span.font.size = Pt(8)


def blank_report_template(language: str = "vi") -> bytes:
    """Editable report structure; contains no results, signatures or invented source evidence."""
    if language not in ("vi", "en"):
        raise ValueError("Ngôn ngữ báo cáo phải là vi hoặc en.")
    outline = build_report_outline({}, {}, {}, language)
    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Cm(21), Cm(29.7)
    section.top_margin = section.bottom_margin = Cm(2)
    section.left_margin = section.right_margin = Cm(1.8)
    for name in ("Normal", "Title", "Heading 1", "Heading 2", "Heading 3"):
        doc.styles[name].font.name = "Arial"
        doc.styles[name].font.color.rgb = RGBColor(0, 0, 0)
    doc.styles["Normal"].font.size = Pt(10)
    template_footer = section.footer.paragraphs[0]
    template_footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    template_footer.add_run(software_attribution(language)).font.size = Pt(8)
    doc.add_paragraph(
        "MẪU BÁO CÁO TƯƠNG ĐƯƠNG SINH HỌC" if language == "vi" else "BIOEQUIVALENCE REPORT TEMPLATE",
        "Title",
    )
    doc.add_paragraph(
        "MẪU — CHƯA CÓ DỮ LIỆU NGHIÊN CỨU; cần điền và kiểm chứng toàn bộ bằng chứng."
        if language == "vi" else "TEMPLATE — NO STUDY DATA; all evidence must be supplied and verified."
    )
    for item in outline:
        doc.add_heading(item["title"], level=item["level"])
        if item["body"]:
            doc.add_paragraph(item["body"])
    appendix = [
        (
            "11.10.1 Kết quả BE theo endpoint" if language == "vi" else "11.10.1 Endpoint-level BE results",
            ["Endpoint", "Thiết kế / rule" if language == "vi" else "Design / rule", "GMR (T/R)", "CI 90%", "Giới hạn" if language == "vi" else "Limits", "Kết luận" if language == "vi" else "Decision"],
        ),
        (
            "11.10.2 Chỉ số PK theo người và kỳ" if language == "vi" else "11.10.2 Individual/period PK parameters",
            ["Mã người tham gia" if language == "vi" else "Subject", "Kỳ" if language == "vi" else "Period", "T/R", "Cmax", "AUC0–t", "AUC0–∞"],
        ),
        (
            "11.10.3 Quyết định theo từng tiêu chí HVD / NTI" if language == "vi" else "11.10.3 HVD / NTI criterion-level decisions",
            ["Tiêu chí" if language == "vi" else "Criterion", "Giá trị" if language == "vi" else "Value", "Ngưỡng" if language == "vi" else "Limit", "Đạt?" if language == "vi" else "Met?", "Cơ sở / nguồn" if language == "vi" else "Basis / source"],
        ),
        (
            "11.10.4 Quần thể phân tích và dữ liệu thiếu" if language == "vi" else "11.10.4 Analysis populations and missingness",
            ["Mã người tham gia" if language == "vi" else "Subject", "Trình tự" if language == "vi" else "Sequence", "Kỳ hoàn tất" if language == "vi" else "Completed periods", "Quần thể" if language == "vi" else "Population", "Lý do loại / thiếu" if language == "vi" else "Exclusion / missing reason"],
        ),
        (
            "11.10.5 Theo dõi AE / SAE" if language == "vi" else "11.10.5 AE / SAE listings",
            ["Mã người tham gia" if language == "vi" else "Subject", "T/R", "Biến cố" if language == "vi" else "Event", "Mức độ" if language == "vi" else "Severity", "SAE?", "Liên quan / xử trí" if language == "vi" else "Relatedness / action"],
        ),
        (
            "11.10.6 Sai lệch và bằng chứng audit" if language == "vi" else "11.10.6 Deviations and audit evidence",
            ["Mã" if language == "vi" else "ID", "Sai lệch" if language == "vi" else "Deviation", "Ảnh hưởng" if language == "vi" else "Impact", "Xử lý" if language == "vi" else "Disposition", "Tham chiếu" if language == "vi" else "Reference"],
        ),
    ]
    doc.add_heading(
        "11.10 Phụ lục bảng dữ liệu tính toán" if language == "vi" else "11.10 Analysis data tables",
        level=2,
    )
    doc.add_paragraph(
        "Bảng khung để điền từ dữ liệu nguồn đã đối chiếu; mỗi dòng cần có đơn vị, quần thể, SAP và phiên bản phù hợp."
        if language == "vi" else
        "Fill these example tables from reconciled records; verify units, populations, SAP and versions."
    )
    placeholder = "CHƯA CUNG CẤP" if language == "vi" else "NOT PROVIDED"
    for title, headers in appendix:
        doc.add_heading(title, level=3)
        table = doc.add_table(rows=2, cols=len(headers))
        table.style = "Table Grid"
        for cell, header in zip(table.rows[0].cells, headers, strict=True):
            cell.text = header
        for cell in table.rows[1].cells:
            cell.text = placeholder
        doc.add_paragraph()
    doc.add_heading(
        "11.11 Nguồn và truy xuất" if language == "vi" else "11.11 References and traceability",
        level=2,
    )
    doc.add_paragraph(
        "Đính kèm phiên bản quy định hiện hành, guidance theo sản phẩm, protocol/SAP đã ký, mã run và hash đối chiếu: "
        if language == "vi" else
        "Attach applicable current guidance, product-specific guidance, signed protocol/SAP, run ID and reconciled hashes: "
    )
    doc.add_paragraph(placeholder)
    _append_docx_figures(doc, illustrative_figures(language), language, template=True)
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def docx_report(project: Project, run_index: int = -1, language: str = "vi") -> bytes:
    content = report_content(project, run_index, language)
    run = content["run"]
    display_status = _display_status(language)
    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Cm(21), Cm(29.7)
    section.top_margin = section.bottom_margin = Cm(2)
    section.left_margin = section.right_margin = Cm(1.8)
    for name in ("Normal", "Title", "Heading 1", "Heading 2", "Heading 3"):
        style = doc.styles[name]
        style.font.name = "Arial"
        style.font.color.rgb = RGBColor(0, 0, 0)
        # Explicit fonts must not be overridden by the default template's theme.
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
    doc.styles["Normal"].paragraph_format.space_after = Pt(6)
    section.header.paragraphs[0].text = display_status
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.text = f"{content['study_id']} | "
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    footer._p.append(field)
    credit = section.footer.add_paragraph()
    credit.alignment = WD_ALIGN_PARAGRAPH.CENTER
    credit.paragraph_format.space_after = Pt(0)
    credit.add_run(software_attribution(language)).font.size = Pt(8)
    doc.add_paragraph(content["title"], "Title")
    doc.add_paragraph(f"{content['study_id']} | {run['timestamp']} | {display_status}")
    for disclaimer in content["disclaimers"]:
        doc.add_paragraph(disclaimer)
    for item in content["outline"]:
        doc.add_heading(item["title"], level=item["level"])
        if item["body"]:
            doc.add_paragraph(item["body"])
    doc.add_heading("11.10 Phụ lục bảng dữ liệu tính toán" if language == "vi" else "11.10 Analysis data tables", level=2)
    doc.add_heading("11.10.1 Kết quả BE" if language == "vi" else "11.10.1 BE results", level=3)

    def table(headers, rows, widths=None):
        tbl = doc.add_table(rows=1, cols=len(headers))
        tbl.style = "Table Grid"
        tbl.autofit = False
        widths = widths or [17.4 / len(headers)] * len(headers)
        for column, width in zip(tbl.columns, widths, strict=True):
            column.width = Cm(width)
        for cell, text in zip(tbl.rows[0].cells, headers, strict=False):
            cell.text = str(text)
            shade = OxmlElement("w:shd")
            shade.set(qn("w:fill"), "DFE8EE")
            cell._tc.get_or_add_tcPr().append(shade)
        repeat = OxmlElement("w:tblHeader")
        tbl.rows[0]._tr.get_or_add_trPr().append(repeat)
        for row in rows:
            for cell, text in zip(tbl.add_row().cells, row, strict=False):
                cell.text = str(text)
                for p in cell.paragraphs:
                    p.paragraph_format.space_after = Pt(3)
                    for item in p.runs:
                        item.font.size = Pt(8)
        for row in tbl.rows:
            prevent_split = OxmlElement("w:cantSplit")
            row._tr.get_or_add_trPr().append(prevent_split)
            for cell, width in zip(row.cells, widths, strict=True):
                cell.width = Cm(width)
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                for p in cell.paragraphs:
                    p.paragraph_format.space_after = Pt(3)
                    p.paragraph_format.space_before = Pt(3)
                    for item in p.runs:
                        item.font.size = Pt(8)
        doc.add_paragraph()

    table(content["headings"], content["rows"])
    doc.add_heading("11.10.2 PK cá thể" if language == "vi" else "11.10.2 Individual PK", level=3)
    table(
        ["Mã người tham gia" if language == "vi" else "Subject",
         "Kỳ" if language == "vi" else "Period", "T/R", "Cmax ng/mL", "Tmax (h)",
         "AUC0–t ng·h/mL" if language == "vi" else "AUC last ng h/mL",
         "AUC0–∞ ng·h/mL" if language == "vi" else "AUCinf ng h/mL"],
        [
            [
                r["subject_id"],
                r["period"],
                r["treatment"],
                _fmt(r["cmax"]), _fmt(r.get("tmax")),
                _fmt(r["auc_last"]),
                _fmt(r["auc_inf"]),
            ]
            for r in run["nca"]
        ],
    )
    for index, specification in enumerate(content["reviewer_tables"], 3):
        doc.add_heading(f"11.10.{index} {specification['title']}", level=3)
        doc.add_paragraph(specification["note"])
        table(specification["headers"], specification["rows"], specification["widths"])
    doc.add_heading("11.11 Nguồn và truy xuất" if language == "vi" else "11.11 References and traceability", level=2)
    for url in run["rule_snapshot"].get("sources", []):
        doc.add_paragraph(url)
    for key in (
        "analysis_run_id",
        "dataset_hash",
        "raw_hash",
        "config_hash",
        "snapshot_hash",
        "engine_version",
    ):
        doc.add_paragraph(f"{key}: {run[key]}")
    _append_docx_figures(doc, snapshot_figures(run, language), language, template=False)
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def _register_pdf_font() -> str:
    if "BEUnicode" in pdfmetrics.getRegisteredFontNames():
        return "BEUnicode"
    candidates = [Path("C:/Windows/Fonts/arial.ttf"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")]
    for path in candidates:
        if path.is_file():
            pdfmetrics.registerFont(TTFont("BEUnicode", str(path)))
            return "BEUnicode"
    raise ValueError("Thiếu font Unicode Arial/DejaVuSans để xuất PDF tiếng Việt.")


def pdf_report(project: Project, run_index: int = -1, language: str = "vi") -> bytes:
    content = report_content(project, run_index, language)
    run = content["run"]
    display_status = _display_status(language)
    font = _register_pdf_font()
    styles = getSampleStyleSheet()
    for name in ("Normal", "Title", "Heading1", "Heading2", "Heading3"):
        styles[name].fontName = font
        styles[name].textColor = colors.black
    styles["Normal"].fontSize, styles["Normal"].leading = 9, 14
    styles["Heading1"].fontSize, styles["Heading1"].leading = 14, 18
    styles["Heading1"].keepWithNext = True
    styles["Heading2"].fontSize, styles["Heading2"].leading = 11, 15
    styles["Heading3"].fontSize, styles["Heading3"].leading = 10, 14
    styles["Heading2"].keepWithNext = True
    styles["Heading3"].keepWithNext = True
    small = ParagraphStyle("small", fontName=font, fontSize=7, leading=10, wordWrap="CJK")
    centered = ParagraphStyle("center", parent=small, alignment=TA_CENTER)
    elements = [
        Paragraph(escape(content["title"]), styles["Title"]),
        Paragraph(f"{escape(content['study_id'])} | {escape(display_status)}", styles["Normal"]),
    ]
    for disclaimer in content["disclaimers"]:
        elements.append(Paragraph(escape(disclaimer), styles["Normal"]))
    for item in content["outline"]:
        elements.extend(
            [
                Paragraph(escape(item["title"]), styles[f"Heading{item['level']}"]),
                Paragraph(escape(item["body"]).replace("\n", "<br/>") or " ", styles["Normal"]),
                Spacer(1, 0.2 * cm),
            ]
        )
    elements.append(Paragraph("11.10 Phụ lục bảng dữ liệu tính toán" if language == "vi" else "11.10 Analysis data tables", styles["Heading2"]))
    elements.append(Paragraph("11.10.1 Kết quả BE" if language == "vi" else "11.10.1 BE results", styles["Heading3"]))
    rows = [
        [Paragraph(escape(str(v)), centered) for v in row] for row in [content["headings"], *content["rows"]]
    ]
    table = LongTable(rows, colWidths=[2 * cm, 2.3 * cm, 0.8 * cm, 1.7 * cm, 3.2 * cm, 6 * cm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DFE8EE")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9D9D9")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    elements.append(table)
    elements.append(Paragraph("11.10.2 PK cá thể" if language == "vi" else "11.10.2 Individual PK", styles["Heading3"]))
    individual_headers = (
        ["Mã người tham gia", "Kỳ", "T/R", "Cmax", "Tmax (h)", "AUC0–t", "AUC0–∞"]
        if language == "vi" else ["Subject", "Period", "T/R", "Cmax", "Tmax (h)", "AUC last", "AUC inf"]
    )
    individual_rows = [
        [r["subject_id"], r["period"], r["treatment"], _fmt(r["cmax"]), _fmt(r.get("tmax")),
         _fmt(r["auc_last"]), _fmt(r["auc_inf"])]
        for r in run["nca"]
    ]
    individual = LongTable(
        [[Paragraph(escape(str(v)), small) for v in row] for row in [individual_headers, *individual_rows]],
        colWidths=[2.5 * cm, 1.4 * cm, 1.1 * cm, 2.9 * cm, 2.3 * cm, 3.6 * cm, 3.6 * cm], repeatRows=1,
    )
    individual.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DFE8EE")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9D9D9")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(individual)
    for index, specification in enumerate(content["reviewer_tables"], 3):
        elements.append(CondPageBreak(130))
        elements.append(Paragraph(escape(f"11.10.{index} {specification['title']}"), styles["Heading3"]))
        note_style = ParagraphStyle("table_note", parent=styles["Normal"], spaceAfter=6)
        elements.append(Paragraph(escape(specification["note"]), note_style))
        values = [specification["headers"], *specification["rows"]]
        rendered = [[Paragraph(escape(str(v)), small) for v in row] for row in values]
        listing = LongTable(
            rendered, colWidths=[width * cm for width in specification["widths"]], repeatRows=1
        )
        listing.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DFE8EE")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9D9D9")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        elements.extend([listing, Spacer(1, 0.3 * cm)])
    elements.append(
        Paragraph(
            "11.11 Nguồn và truy xuất" if language == "vi" else "11.11 References and traceability", styles["Heading2"]
        )
    )
    for text in [
        *content["run"]["rule_snapshot"].get("sources", []),
        f"analysis_run_id: {content['run']['analysis_run_id']}",
        f"snapshot_hash: {content['run']['snapshot_hash']}",
    ]:
        elements.append(Paragraph(escape(text), small))
    elements.append(Paragraph(
        "11.12 Hình và đồ thị minh họa" if language == "vi" else "11.12 Figures and visualizations",
        styles["Heading2"],
    ))
    elements.append(Paragraph(
        "Đồ thị từ dữ liệu trong snapshot; sơ đồ chỉ minh họa. ABEL, RSABE và NTI phải xem đủ các tiêu chí."
        if language == "vi" else
        "Plots from the analysis snapshot; schematic is illustrative. Assess all ABEL, RSABE and NTI criteria.",
        styles["Normal"],
    ))
    for index, figure in enumerate(snapshot_figures(run, language), start=1):
        elements.append(CondPageBreak(330))
        elements.append(Paragraph(escape(f"11.12.{index} {figure.title}"), styles["Heading3"]))
        elements.append(PDFImage(io.BytesIO(figure.png), width=16.5 * cm, height=16.5 * cm * 740 / 1400))
        elements.append(Paragraph(
            escape(f"{'Hình' if language == 'vi' else 'Figure'} {index}. {figure.note}"), small,
        ))
        elements.append(Spacer(1, 0.25 * cm))
    output = io.BytesIO()

    def page(canvas, document):
        canvas.setFont(font, 7)
        canvas.drawString(1.5 * cm, 28.5 * cm, display_status)
        canvas.drawString(1.5 * cm, 1 * cm, software_attribution(language))
        canvas.drawRightString(19.5 * cm, 1 * cm, f"{content['study_id']} | {document.page}")

    SimpleDocTemplate(
        output,
        pagesize=(21 * cm, 29.7 * cm),
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
        title=content["title"],
    ).build(elements, onFirstPage=page, onLaterPages=page)
    return output.getvalue()


def analysis_exports(project: Project, run_index: int = -1) -> dict[str, bytes]:
    content = report_content(project, run_index)
    run = content["run"]
    nca = pd.DataFrame(run["nca"]).drop(
        columns=["config", "terminal_candidates", "terminal_selected", "profile_points"], errors="ignore"
    )
    return {
        "nca.csv": csv_bytes(nca),
        "nca.xlsx": nca_workbook(run["nca"], metadata=content["manifest"]),
        "be.xlsx": be_workbook(
            run["be"],
            tmax_comparison=run.get("tmax_comparison"),
            data=pd.DataFrame(run["nca"]).drop(
                columns=["config", "terminal_candidates", "terminal_selected", "profile_points"],
                errors="ignore",
            ),
            metadata=content["manifest"],
        ),
        "validated.csv": csv_bytes(pd.DataFrame(run["validated_data"])),
        "audit.json": json.dumps(project.events, ensure_ascii=False, indent=2).encode(),
        "analysis.json": json.dumps(run, ensure_ascii=False, indent=2).encode(),
        "ctd_mapping.json": json.dumps(CTD_MAPPING, ensure_ascii=False, indent=2).encode(),
        "input_manifest.json": json.dumps(content["manifest"], ensure_ascii=False, indent=2).encode(),
    }
