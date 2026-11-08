"""Explicitly synthetic learning profiles; no study-level PASS guarantee."""

from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from be_app.design import randomize
from be_app.domain import Design, Study
from be_app.persistence import Project


def demo_project(design: Design = "2x2", n: int = 24, seed: int = 241029) -> Project:
    study = Study(
        study_id="DEMO_BE001",
        title="Dữ liệu giả lập phục vụ học thử BE",
        design=design,
        protocol="DEMO-PROT v1",
        sap="DEMO-SAP v1",
        active_ingredient="SYNTHETIC_API",
        fed_state="fasted",
        dose=1,
        test_product="THUỐC GIẢ LẬP T",
        reference_product="THUỐC GIẢ LẬP R",
        test_strength="1 mg/viên (giả lập)",
        reference_strength="1 mg/viên (giả lập)",
        test_dosage_form="Viên nén giả lập",
        reference_dosage_form="Viên nén giả lập",
        test_batch="SYNTH-T-001",
        reference_batch="SYNTH-R-001",
        test_manufacturer="NHÀ SẢN XUẤT GIẢ LẬP T",
        reference_manufacturer="NHÀ SẢN XUẤT GIẢ LẬP R",
        test_expiry_date="2027-12-31",
        reference_expiry_date="2027-12-31",
        sponsor="NHÀ TÀI TRỢ GIẢ LẬP",
        study_site="TRUNG TÂM GIẢ LẬP - KHÔNG CÓ NGƯỜI THẬT",
        principal_investigator="NGHIÊN CỨU VIÊN GIẢ LẬP",
        study_start_date="2026-08-01",
        study_end_date="2026-10-31",
        clinical_start_date="2026-09-01",
        clinical_end_date="2026-09-30",
        bioanalytical_start_date="2026-09-23",
        bioanalytical_end_date="2026-10-10",
        data_lock_date="2026-10-15",
        is_demo=True,
        data_purpose="training_qa",
        data_provenance=f"Synthetic concentration-time profiles generated locally; seed={seed}; no human subjects.",
        scope_reviewed=True,
        scope_evidence="Synthetic IR single-dose learning example; không phải nghiên cứu thật.",
    )
    allocation, metadata = randomize(design, n, seed)
    rng = np.random.default_rng(seed)
    times = [0, 0.25, 0.5, 1, 1.5, 2, 3, 4, 6, 8, 12, 16, 24, 36]
    rows = []
    for record in allocation.to_dict("records"):
        dose_time = datetime(2026, 9, 1, 8, tzinfo=timezone(timedelta(hours=8))) + timedelta(
            days=7 * (record["period"] - 1)
        )
        scale = float(rng.lognormal(0, 0.25))
        if record["treatment"] == "T":
            scale *= 0.91
        for nominal in times:
            actual = nominal if nominal == 0 else nominal + float(rng.uniform(-0.01, 0.01))
            sample = dose_time + timedelta(hours=actual)
            actual = (sample - dose_time).total_seconds() / 3600
            concentration = 140 * scale * (np.exp(-0.14 * actual) - np.exp(-1.5 * actual))
            concentration *= rng.lognormal(0, 0.06)
            blq = bool(concentration < 0.2)
            rows.append(
                dict(
                    study_id=study.study_id,
                    subject_id=record["subject_id"],
                    sequence=record["sequence"],
                    period=record["period"],
                    treatment=record["treatment"],
                    dose_datetime=dose_time.isoformat(),
                    sample_datetime=sample.isoformat(),
                    nominal_time_h=nominal,
                    actual_time_h=actual,
                    concentration=0 if blq else float(concentration),
                    concentration_unit="ng/mL",
                    blq_flag=blq,
                    lloq=0.2,
                    sample_id=f"{record['subject_id']}_P{record['period']}_T{nominal}",
                    analyte="parent",
                    source_batch="SYNTHETIC_BATCH",
                    sample_status="BLQ" if blq else "VALID",
                )
            )
    project = Project(study=study).with_allocation(allocation.to_dict("records"), metadata)
    return project.import_raw(
        pd.DataFrame(rows).to_csv(index=False).encode("utf-8-sig"), "SYNTHETIC_demo.csv"
    )


def statistical_demo(design: str, nti: bool = False):
    """Synthetic endpoint-only data for inspecting model output, never real study evidence."""
    from be_app.design import SEQUENCES

    rng = np.random.default_rng(20261030)
    rows = []
    sigma = 0.10 if nti else 0.45
    for i in range(36):
        sequence = SEQUENCES[design][i % len(SEQUENCES[design])]
        subject_effect = float(rng.normal(0, 0.15))
        for period, treatment in enumerate(sequence, 1):
            log_pk = (
                7
                + subject_effect
                + 0.015 * period
                + (0.02 if treatment == "T" else 0)
                + float(rng.normal(0, sigma))
            )
            rows.append(
                dict(
                    subject_id=f"DEMO{i + 1:03d}",
                    sequence=sequence,
                    period=period,
                    treatment=treatment,
                    cmax=float(np.exp(log_pk)),
                    auc_last=float(np.exp(log_pk + 0.7)),
                )
            )
    return pd.DataFrame(rows)
