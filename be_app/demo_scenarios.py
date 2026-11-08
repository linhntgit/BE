"""Deterministic synthetic inputs for teaching the *ordinary* application workflows.

None of these functions commits a study, runs an analysis or certifies a result.
The same data-editing, QC, mapping and analysis paths apply to real and demo data.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from be_app.design import SEQUENCES


@dataclass(frozen=True)
class Scenario:
    title: str
    objective: str
    next_step: str


STUDY_CASES = {
    "2x2": Scenario("Crossover 2×2", "Học thiết kế crossover thông thường.", "Kiểm tra thông tin rồi bấm Tạo nghiên cứu."),
    "parallel": Scenario("Song song", "Học hai nhánh độc lập T và R.", "Tạo nghiên cứu rồi lập phân nhóm."),
    "partial3": Scenario("Replicate 3 kỳ", "Học partial replicate với ba sequence.", "Tạo nghiên cứu rồi lập phân nhóm."),
    "full4": Scenario("Replicate 4 kỳ", "Học full replicate với bốn kỳ.", "Tạo nghiên cứu rồi lập phân nhóm."),
    "nti": Scenario("NTI (replicate 4 kỳ)", "Khảo sát độ biến thiên thấp và giới hạn NTI; tự xác nhận scope.", "Kiểm tra rule và các ô xác nhận trước khi tạo."),
    "hvd": Scenario("HVD (replicate 4 kỳ)", "Khảo sát HVD và điều kiện áp dụng scaling, không bảo đảm đủ điều kiện.", "Rà soát SAP và điều kiện scaling trước khi tạo."),
}

FULL_RAW_CASES = {
    "normal": Scenario("Bảng hợp lệ", "Nồng độ giả lập đầy đủ; quan sát preflight và QC.", "Áp dụng bảng → Kiểm tra cấu trúc và QC → Nhập raw."),
    "fail": Scenario("Khác biệt T/R lớn", "Khảo sát trường hợp ước lượng T/R lệch đáng kể; kết quả do engine xác định.", "QC, nhập raw rồi đánh giá BE."),
    "blq": Scenario("Các mẫu BLQ", "BLQ được đánh dấu rõ, nồng độ bằng 0 ở mẫu dưới LLOQ.", "Quan sát quy tắc BLQ trong QC và NCA."),
    "missing_sample": Scenario("Thiếu một mẫu", "Thiếu quan sát tại một thời điểm; không tự điền giá trị.", "Quan sát ảnh hưởng lên dữ liệu và QC."),
    "missing_period": Scenario("Thiếu một kỳ", "Một subject bị thiếu nguyên kỳ; QC cần phát hiện.", "Chạy preflight và đọc báo cáo QC."),
    "duplicate": Scenario("Mẫu trùng", "Mẫu có định danh/thời điểm trùng để luyện sửa lỗi.", "Chạy QC; sửa trong bảng rồi áp dụng và QC lại."),
    "units": Scenario("Đơn vị µg/mL", "Cần xác nhận chuyển sang ng/mL có dấu vết.", "Bật xác nhận chuyển đơn vị rồi chạy QC."),
    "nti": Scenario("NTI: biến thiên thấp", "Chỉ phù hợp nghiên cứu NTI đã khai báo; kết quả phụ thuộc rule.", "Xác nhận rule NTI trước khi phân tích."),
    "hvd": Scenario("Replicate: biến thiên cao", "Tìm hiểu biến thiên trong chủ thể và điều kiện scaling.", "Xác nhận SAP và rà soát CVwR, outlier."),
}

QUICK_CASES = {
    "concentration": Scenario("Nồng độ → NCA → BE (2×2)", "Bảng Time/Cplasma thông thường.", "Áp dụng bảng, xác nhận mapping rồi chạy BE."),
    "endpoint": Scenario("Bảng Cmax/AUClast (2×2)", "Phân tích trực tiếp endpoint có sẵn.", "Xác nhận cột và thang đo rồi chạy BE."),
    "fail": Scenario("Endpoint: khác biệt T/R lớn", "Kịch bản luyện nhận diện BE không đạt.", "Chạy BE và kiểm tra CI/giới hạn."),
    "partial3": Scenario("Endpoint: replicate 3 kỳ", "Học dữ liệu partial replicate.", "Xác nhận thiết kế và rule replicate."),
    "full4": Scenario("Endpoint: replicate 4 kỳ", "Học dữ liệu full replicate.", "Xác nhận thiết kế và rule replicate."),
    "nti": Scenario("Endpoint: NTI", "Thực hành quy tắc giới hạn hẹp.", "Xác nhận rule NTI và căn cứ sản phẩm."),
    "hvd": Scenario("Endpoint: HVD", "Thực hành yêu cầu để áp dụng scaling.", "Kiểm tra SAP định trước và căn cứ HVD."),
    "missing": Scenario("Endpoint: thiếu một giá trị", "Một Cmax bị thiếu; không tự nội suy.", "Kiểm tra cảnh báo và tính đánh giá được."),
    "mapping": Scenario("Tên cột không chuẩn", "Thực hành ghép tên nguồn Peak/Exposure sang Cmax/AUClast.", "Mở mapping và chọn cột nguồn tương ứng."),
}

ENDPOINT_CASES = {
    key: val for key, val in QUICK_CASES.items() if key in {"endpoint", "fail", "partial3", "full4", "nti", "hvd", "missing"}
}

PK_CASES = {
    "oral": Scenario("Đơn liều uống", "Mô hình hấp thu/thải trừ một ngăn với nhiều thời điểm.", "Áp dụng bảng, chọn đường uống rồi chạy PK."),
    "iv": Scenario("Đơn liều IV bolus", "Đường cong thải trừ IV; quan sát C0 và pha cuối.", "Chọn đường IV bolus trước khi chạy."),
    "multiple": Scenario("Đa liều (10 liều, τ=12h)", "Quan sát chu kỳ sau liều cuối.", "Xác nhận chế độ đa liều và thời gian tính từ liều cuối."),
    "steady": Scenario("Steady-state giả định (10 liều)", "Học AUCτ, các điều kiện CLss; chưa có bằng chứng đạt steady-state.", "Tự xác nhận bằng chứng steady-state nếu có."),
    "blq": Scenario("Có nồng độ BLQ", "Quan sát xử lý BLQ rõ ràng.", "Áp dụng bảng và đọc QC/giới hạn NCA."),
    "sparse": Scenario("Thiếu điểm pha cuối", "Khảo sát NCA khi ước lượng terminal không đáng tin.", "Kiểm tra cờ chất lượng pha cuối."),
    "duplicate": Scenario("Trùng thời điểm", "Bảng cố tình trùng Time trong một profile.", "Thử Áp dụng bảng, sửa Time rồi áp dụng lại."),
}


def study_values(case: str) -> dict:
    """Values for the existing create-study widgets; never a ready-made Project."""
    if case not in STUDY_CASES:
        raise ValueError("Kịch bản nghiên cứu không tồn tại.")
    design = {"nti": "full4", "hvd": "full4"}.get(case, case)
    rule = {"partial3": "EMA_REPLICATE_STANDARD", "full4": "EMA_REPLICATE_STANDARD",
            "nti": "EMA_NTI", "hvd": "EMA_HVDP_ABEL"}.get(case, "EMA_IR_NONREPLICATE_M13A")
    return {
        "study_id": "DEMO_" + case.upper(), "title": "Học thử BE: " + STUDY_CASES[case].title,
        "design": design, "rule": rule, "protocol": "SYNTH-PROT v1", "sap": "SYNTH-SAP v1",
        "purpose": "training_qa", "provenance": f"Synthetic data; scenario={case}; seed=241029; no humans.",
        "ingredient": "SYNTHETIC_API", "dose": 100.0, "formulation": "IR", "fed_state": "fasted",
        "sponsor": "NHÀ TÀI TRỢ GIẢ LẬP", "study_site": "TRUNG TÂM GIẢ LẬP",
        "principal_investigator": "NGHIÊN CỨU VIÊN GIẢ LẬP",
        "test_product": "THUỐC GIẢ LẬP T", "reference_product": "THUỐC GIẢ LẬP R",
        "test_strength": "100 mg/viên", "reference_strength": "100 mg/viên",
        "test_dosage_form": "Viên nén", "reference_dosage_form": "Viên nén",
        "test_batch": "SYNTH-T-001", "reference_batch": "SYNTH-R-001",
        "test_manufacturer": "NHÀ SẢN XUẤT GIẢ LẬP T",
        "reference_manufacturer": "NHÀ SẢN XUẤT GIẢ LẬP R",
        "test_expiry_date": "2027-12-31", "reference_expiry_date": "2027-12-31",
        "study_start_date": "2026-08-01", "study_end_date": "2026-10-31",
        "clinical_start_date": "2026-09-01", "clinical_end_date": "2026-09-30",
        "bioanalytical_start_date": "2026-09-23", "bioanalytical_end_date": "2026-10-10",
        "data_lock_date": "2026-10-15", "nti": case == "nti",
        "nti_cmax": False, "scaled": False, "hvd_reason": "",
        "operator": "training-operator", "evidence": "", "reviewed": False,
        "is_demo": True,
    }


def full_concentrations(study, allocation: list[dict], case: str, *, seed: int = 241029) -> pd.DataFrame:
    """Generate raw rows against the *existing* study and exact saved allocation."""
    if case not in FULL_RAW_CASES:
        raise ValueError("Kịch bản raw không tồn tại.")
    if not allocation:
        raise ValueError("Cần tạo phân nhóm trước khi nạp demo nồng độ.")
    rng = np.random.default_rng(seed)
    times = (0, .25, .5, 1, 1.5, 2, 3, 4, 6, 8, 12, 16, 24, 36)
    factor_t = 1.42 if case == "fail" else (1.015 if case == "nti" else .96)
    variability = .34 if case == "hvd" else (.045 if case == "nti" else .14)
    first_subject = str(allocation[0]["subject_id"])
    result = []
    for item in allocation:
        period, subject = int(item["period"]), str(item["subject_id"])
        if case == "missing_period" and subject == first_subject and period == 2:
            continue
        dose_time = datetime(2026, 9, 1, 8, tzinfo=timezone(timedelta(hours=8))) + timedelta(days=7 * (period - 1))
        exposure = float(rng.lognormal(0, variability)) * (factor_t if item["treatment"] == "T" else 1.0)
        for nominal in times:
            if case == "missing_sample" and subject == first_subject and nominal == 12 and period == 1:
                continue
            actual = nominal if nominal == 0 else nominal + float(rng.uniform(-.01, .01))
            sample_time = dose_time + timedelta(hours=actual)
            actual = (sample_time - dose_time).total_seconds() / 3600
            concentration = 140 * exposure * (np.exp(-.14 * actual) - np.exp(-1.5 * actual))
            concentration *= float(rng.lognormal(0, .06))
            blq = concentration < .2 or (case == "blq" and nominal in (.5, 16) and subject == first_subject)
            result.append(dict(study_id=study.study_id, subject_id=subject,
                               sequence=item["sequence"], period=period, treatment=item["treatment"],
                               dose_datetime=dose_time.isoformat(), sample_datetime=sample_time.isoformat(),
                               nominal_time_h=nominal, actual_time_h=actual,
                               concentration=0.0 if blq else float(concentration),
                               concentration_unit="ng/mL", blq_flag=bool(blq), lloq=.2,
                               sample_id=f"{subject}_P{period}_T{nominal}", analyte=study.analyte,
                               source_batch="SYNTHETIC_TRAINING", sample_status="BLQ" if blq else "VALID"))
    data = pd.DataFrame(result)
    if case == "units":
        data["concentration"] /= 1000.0
        data["lloq"] /= 1000.0
        data["concentration_unit"] = "µg/mL"
    if case == "duplicate":
        data = pd.concat([data, data.iloc[[0]]], ignore_index=True)
    return data


def endpoint_frame(design: str, case: str) -> pd.DataFrame:
    if design not in SEQUENCES:
        raise ValueError("Thiết kế chưa hỗ trợ.")
    if case not in {*QUICK_CASES, *ENDPOINT_CASES}:
        raise ValueError("Kịch bản endpoint không tồn tại.")
    seed = 20261103 + sum(ord(ch) for ch in case)
    rng = np.random.default_rng(seed)
    sigma = .33 if case == "hvd" else (.045 if case == "nti" else .07)
    ratio = 1.45 if case == "fail" else 1.035
    rows = []
    for i in range(36):
        seq = SEQUENCES[design][i % len(SEQUENCES[design])]
        person = float(rng.normal(0, .12))
        for period, treatment in enumerate(seq, start=1):
            z = person + float(rng.normal(0, sigma)) + .006 * period
            value = float(80 * np.exp(z) * (ratio if treatment == "T" else 1.0))
            rows.append(dict(Subject=f"DEMO{i + 1:03d}", Sequence=seq, Period=period,
                             Treatment=treatment, Cmax=round(value, 5), AUClast=round(value * 3.2, 5)))
    frame = pd.DataFrame(rows)
    if case == "missing":
        frame["Cmax"] = frame["Cmax"].astype(object)
        frame.loc[0, "Cmax"] = ""
    if case == "mapping":
        frame = frame.rename(columns={"Cmax": "Peak", "AUClast": "Exposure"})
    return frame


def quick_frame(case: str) -> tuple[pd.DataFrame, str, str]:
    if case not in QUICK_CASES:
        raise ValueError("Kịch bản BE nhanh không tồn tại.")
    design = "partial3" if case == "partial3" else "full4" if case in {"full4", "nti", "hvd"} else "2x2"
    rule = {"partial3": "EMA_REPLICATE_STANDARD", "full4": "EMA_REPLICATE_STANDARD",
            "nti": "EMA_NTI", "hvd": "EMA_HVDP_ABEL"}.get(case, "EMA_IR_NONREPLICATE_M13A")
    endpoint = endpoint_frame(design, case)
    if case != "concentration":
        return endpoint, design, rule
    rows = []
    for x in endpoint.itertuples(index=False):
        for time, fraction in ((0, 0), (.5, .35), (1, .7), (2, 1), (4, .8),
                               (8, .43), (12, .22), (18, .09), (24, .04)):
            rows.append(dict(Subject=x.Subject, Sequence=x.Sequence, Period=x.Period,
                             Treatment=x.Treatment, Time=time, Cplasma=round(x.Cmax * fraction, 5),
                             BLQ=False))
    return pd.DataFrame(rows), design, rule


def pk_frame(case: str) -> tuple[pd.DataFrame, dict]:
    if case not in PK_CASES:
        raise ValueError("Kịch bản PK không tồn tại.")
    multiple = case in {"multiple", "steady"}
    times = np.linspace(0, 12, 25) if multiple else np.array([0, .25, .5, 1, 1.5, 2, 3, 4, 6, 8, 12, 16, 24])
    if case == "sparse":
        times = np.array([0, .25, .5, 1, 2, 3, 4])
    if multiple:
        from be_app.pk_analysis import PKSettings
        from be_app.pk_multiple import PKRegimen, predict_multiple
        regimen = PKRegimen(mode="steady_state" if case == "steady" else "multiple",
                            tau_h=12.0, number_doses=10)
        concentrations = predict_multiple(regimen.absolute_times(times),
                                          {"CL/F": 5.0, "V/F": 20.0, "ka": 1.2},
                                          PKSettings(route="oral", dose=100), 1, regimen)
    elif case == "iv":
        concentrations = 90 * np.exp(-.2 * times)
    else:
        concentrations = 125 * 1.2 / (1.2 - .2) * (np.exp(-.2 * times) - np.exp(-1.2 * times))
    frame = pd.DataFrame({"profile_id": ["SYNTH_PK01"] * len(times), "time_h": times,
                          "concentration": np.round(concentrations, 5), "blq": False})
    if case == "blq":
        frame.loc[frame.index[-2:], ["concentration", "blq"]] = [0.0, True]
    if case == "duplicate":
        frame = pd.concat([frame, frame.iloc[[4]]], ignore_index=True)
    settings = {"pk_dose_mode": "steady_state" if case == "steady" else "multiple" if multiple else "single",
                "pk_tau": 12.0, "pk_number_doses": 10, "pk_time_basis": "last_dose"}
    return frame, settings
