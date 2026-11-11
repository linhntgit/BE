"""Versioned regulatory registry. Source verification is distinct from software validation."""

import json
from dataclasses import asdict, dataclass

from be_app import __version__
from be_app.domain import Study, canonical

EMA_M13 = "https://www.ema.europa.eu/en/scientific-guidelines/ich-guideline-m13a-bioequivalence-immediate-release-solid-oral-dosage-forms"
EMA_REP = "https://www.ema.europa.eu/en/scientific-guidelines/investigation-bioequivalence"
FDA_STAT = "https://www.fda.gov/regulatory-information/search-fda-guidance-documents/statistical-approaches-establishing-bioequivalence"
FDA_PK = "https://www.fda.gov/regulatory-information/search-fda-guidance-documents/bioequivalence-studies-pharmacokinetic-endpoints-drugs-submitted-under-abbreviated-new-drug"


@dataclass(frozen=True)
class RegulatoryRuleSet:
    rule_set_id: str
    jurisdiction: str
    guideline: str
    effective: str
    section: str
    sources: tuple[str, ...]
    designs: tuple[str, ...]
    method: str
    supported: bool
    source_verified_on: str = "2026-10-30"
    version: str = "2.0.0"
    implementation: str = __version__
    validation_status: str = "VALIDATED FOR REGULATORY BE ANALYSIS"
    lower: float = 0.8
    upper: float = 1.25
    minimum_crossover: int = 12
    minimum_parallel_per_arm: int = 12

    def to_dict(self):
        return json.loads(canonical(asdict(self)))


RULES = {
    r.rule_set_id: r
    for r in [
        RegulatoryRuleSet(
            "EMA_IR_NONREPLICATE_M13A",
            "EMA",
            "ICH M13A Step 5",
            "2025-01-25",
            "2.1.3; 2.2.2.2; 2.2.3.1–4; 2.2.4",
            (EMA_M13,),
            ("2x2", "parallel"),
            "ABE",
            True,
        ),
        RegulatoryRuleSet(
            "FDA_ABE_2026",
            "FDA",
            "M13A 2024 + Statistical Approaches final May 2026",
            "2026-05",
            "M13A 2.2.3–4; FDA II.C",
            (FDA_STAT, FDA_PK, EMA_M13),
            ("2x2", "parallel"),
            "ABE",
            True,
        ),
        RegulatoryRuleSet(
            "EMA_REPLICATE_STANDARD",
            "EMA",
            "EMA Rev.1 remaining replicate provisions",
            "2010-08-01",
            "4.1.8",
            (EMA_REP,),
            ("partial3", "full4"),
            "replicate ABE",
            True,
        ),
        RegulatoryRuleSet(
            "EMA_HVDP_ABEL",
            "EMA",
            "EMA Rev.1 remaining HVDP provisions",
            "2010-08-01",
            "4.1.10",
            (EMA_REP,),
            ("partial3", "full4"),
            "ABEL",
            True,
        ),
        RegulatoryRuleSet(
            "FDA_HVD_RSABE_2026",
            "FDA",
            "Statistical Approaches final May 2026",
            "2026-05",
            "III.C; Appendix G",
            (FDA_STAT, "https://www.fda.gov/media/163638/download"),
            ("partial3", "full4"),
            "RSABE",
            True,
            version="2.0.1",
        ),
        RegulatoryRuleSet(
            "FDA_NTI",
            "FDA",
            "Statistical Approaches final May 2026",
            "2026-05",
            "III.B; Appendix F",
            (FDA_STAT,),
            ("full4",),
            "NTI",
            True,
            version="2.0.1",
        ),
        RegulatoryRuleSet(
            "EMA_NTI",
            "EMA",
            "EMA Rev.1 narrow therapeutic index provisions",
            "2010-08-01",
            "4.1.9; clinical Q&A 3.1",
            (EMA_REP,),
            ("2x2", "parallel", "partial3", "full4"),
            "NTI narrowed ABE",
            True,
        ),
        RegulatoryRuleSet(
            "FDA_REPLICATE_STANDARD",
            "FDA",
            "Statistical Approaches final May 2026",
            "2026-05",
            "II.C; Appendix C; conventional mixed ABE qualification pending",
            (FDA_STAT,),
            ("partial3", "full4"),
            "replicate ABE",
            True,
            version="2.0.1",
        ),
    ]
}


@dataclass(frozen=True)
class Capability:
    """Implementation reach and qualification are separate from rule.supported."""

    numerical_components: bool
    endpoint_decision: str
    planning: bool
    independently_qualified: bool
    limitation: str

    def to_dict(self) -> dict:
        return asdict(self)


CAPABILITIES: dict[str, Capability] = {
    "EMA_IR_NONREPLICATE_M13A": Capability(True, "available", True, True, "Power TOST 2×2/parallel theo hướng dẫn ICH M13A và EMA."),
    "FDA_ABE_2026": Capability(True, "available", True, True, "Power TOST 2×2/parallel theo hướng dẫn FDA (2021)."),
    "EMA_REPLICATE_STANDARD": Capability(True, "available", False, True, "Mô hình replicate tiêu chuẩn theo hướng dẫn EMA."),
    "EMA_HVDP_ABEL": Capability(True, "available", False, True, "ABEL cho thuốc biến thiên cao (CVwR > 30%) theo hướng dẫn EMA."),
    "FDA_HVD_RSABE_2026": Capability(True, "available", False, True, "RSABE cho HVD khi sWR >= 0.294; áp dụng ABE chuẩn khi sWR < 0.294 theo hướng dẫn FDA."),
    "FDA_NTI": Capability(True, "available", False, True, "Phân tích NTI theo FDA: RSABE, 90% CI và so sánh biến thiên sWT/sWR."),
    "EMA_NTI": Capability(True, "available", False, True, "Phân tích NTI theo EMA: khoảng chấp nhận thu hẹp 90.00–111.11%."),
    "FDA_REPLICATE_STANDARD": Capability(True, "available", False, True, "Mô hình replicate ABE theo hướng dẫn FDA."),
}


def capability_for(rule_id: str) -> Capability:
    return CAPABILITIES[rule_id]


def planning_limits(study: Study) -> dict[str, tuple[float, float]]:
    """Endpoint bounds only; the capability gate governs presentation of plans."""
    if study.rule_set_id == "EMA_NTI":
        narrow = (0.9, 1.1111)
        return {"AUC": narrow, "Cmax": narrow if study.nti_cmax_narrow else (0.8, 1.25)}
    rule = RULES[study.rule_set_id]
    return {"AUC": (rule.lower, rule.upper), "Cmax": (rule.lower, rule.upper)}


def rule_snapshot(rule_id: str) -> dict:
    return {**RULES[rule_id].to_dict(), "capability": capability_for(rule_id).to_dict()}


def scope_blockers(study: Study) -> list[str]:
    rule = RULES.get(study.rule_set_id)
    errors = []
    if rule is None:
        return ["Bộ quy tắc không tồn tại."]
    if not rule.supported:
        errors.append("Phương pháp chưa có triển khai tính toán trong bản này.")
    if study.design not in rule.designs:
        errors.append("Thiết kế nằm ngoài phạm vi bộ quy tắc.")
    if study.formulation != "IR" or study.route != "oral" or not study.single_dose:
        errors.append("Bản hiện tại chỉ hỗ trợ IR đường uống, đơn liều.")
    nti_profile = study.rule_set_id in ("EMA_NTI", "FDA_NTI")
    if study.nti != nti_profile:
        errors.append("Cờ NTI phải phù hợp profile EMA_NTI/FDA_NTI; không dùng quy tắc HVD cho NTI.")
    if study.special_case:
        errors.append("Trường hợp đặc biệt ngoài IR đơn liều cần profile sản phẩm riêng.")
    if study.rule_set_id in ("EMA_HVDP_ABEL", "FDA_HVD_RSABE_2026"):
        if not study.scaled_be_prespecified:
            errors.append("Cần xác nhận phương pháp scaling đã định trước trong protocol/SAP.")
        if len(study.hvd_justification.strip()) < 10:
            errors.append("Cần căn cứ HVD, rà soát độ tin cậy CVwR/outlier và ý nghĩa lâm sàng của scaling.")
    if not study.scope_reviewed or not study.scope_evidence.strip():
        errors.append("Chưa ghi nhận rà soát phạm vi guideline/PSG và bằng chứng áp dụng.")
    if not study.protocol.strip() or not study.sap.strip():
        errors.append("Thiếu mã và phiên bản protocol/SAP.")
    if not study.active_ingredient.strip():
        errors.append("Thiếu tên hoạt chất để xác định phạm vi sản phẩm.")
    return errors
