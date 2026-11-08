import io

import pandas as pd
import pytest
from openpyxl import load_workbook

from be_app.imports import apply_corrections, correction, csv_bytes, excel_bytes, parse_file, validate_data


def qc(project, frame, conversion=False):
    return validate_data(frame, project.study, pd.DataFrame(project.allocation), conversion)


def test_demo_valid_and_actual_not_nominal(small_demo):
    result = small_demo.qc()
    assert result.valid
    assert (result.data.actual_time_h != result.data.nominal_time_h).any()
    assert result.transformations


@pytest.mark.parametrize(
    "column,value,code",
    [
        ("concentration", "-1", "CONCENTRATION"),
        ("concentration", "inf", "CONCENTRATION"),
        ("concentration_unit", "nmol/L", "UNIT"),
        ("blq_flag", "perhaps", "INVALID_BLQ"),
        ("lloq", "0", "LLOQ"),
        ("period", "1.5", "PERIOD"),
        ("subject_id", "ALIEN", "RANDOMIZATION"),
        ("sample_status", "MISSING", "UNRESOLVED_SAMPLE"),
        ("dose_datetime", "2026-09-01 08:00", "TIMESTAMP"),
        ("actual_time_h", "300", "TIME_MISMATCH"),
        ("study_id", "OTHER", "SCOPE"),
        ("source_batch", "", "MISSING_ID"),
    ],
)
def test_qc_boundaries(small_demo, column, value, code):
    raw = small_demo.raw_frame()
    raw.loc[0, column] = value
    result = qc(small_demo, raw)
    assert not result.valid and code in {f.code for f in result.flags}


def test_malformed_actual_time_not_silently_derived(small_demo):
    raw = small_demo.raw_frame()
    raw.loc[0, "actual_time_h"] = "not-a-number"
    assert "INVALID_NUMBER" in {f.code for f in qc(small_demo, raw).flags}


def test_missing_never_imputed(small_demo):
    raw = small_demo.raw_frame()
    raw.loc[1, "concentration"] = ""
    assert not qc(small_demo, raw).valid


def test_duplicate_never_averaged(small_demo):
    raw = small_demo.raw_frame()
    raw = pd.concat([raw, raw.iloc[[1]]], ignore_index=True)
    result = qc(small_demo, raw)
    assert not result.valid and len(result.data) == len(raw)
    assert sum(f.code == "DUPLICATE" for f in result.flags) == 4


def test_unit_conversion_explicit_and_traced(small_demo):
    raw = small_demo.raw_frame()
    raw["concentration_unit"] = "ug/mL"
    raw["concentration"] = pd.to_numeric(raw.concentration) / 1000
    raw["lloq"] = pd.to_numeric(raw.lloq) / 1000
    assert not qc(small_demo, raw).valid
    result = qc(small_demo, raw, True)
    assert result.valid
    assert result.data.concentration.to_numpy() == pytest.approx(
        pd.to_numeric(small_demo.raw_frame().concentration).to_numpy()
    )
    assert any(t["action"] == "convert_unit" and t["factor"] == 1000 for t in result.transformations)


def test_predose_and_missing_period_block(small_demo):
    raw = small_demo.raw_frame()
    raw.loc[0, "concentration"] = "1000"
    raw.loc[0, "blq_flag"] = "false"
    assert "PREDOSE_5PCT" in {f.code for f in qc(small_demo, raw).flags}
    raw = small_demo.raw_frame()
    raw = raw.loc[~((raw.subject_id == raw.subject_id.iloc[0]) & (raw.period == "2"))]
    assert "MISSING_PERIOD" in {f.code for f in qc(small_demo, raw).flags}


def test_correction_preserves_raw(small_demo):
    before = small_demo.raw_frame()
    change = correction(
        before, 1, "source_batch", "CORRECTED", "Lab source correction", "DM", "QA", "LAB-001"
    )
    changed = apply_corrections(before, [change])
    assert before.loc[1, "source_batch"] == "SYNTHETIC_BATCH"
    assert changed.loc[1, "source_batch"] == "CORRECTED"
    with pytest.raises(ValueError):
        apply_corrections(changed, [change])
    with pytest.raises(ValueError):
        correction(before, 1, "source_batch", "X", "reason", "same", "same", "evidence")


def test_excel_csv_preserve_ids_and_block_formulas():
    frame = pd.DataFrame(dict(subject_id=["0001", "0002"], text=["=1+1", "@SUM(1)"]))
    content = excel_bytes(frame)
    book = load_workbook(io.BytesIO(content), data_only=False)
    assert book.active["A2"].value == "0001" and book.active["A2"].number_format == "@"
    assert book.active["B2"].data_type == "s"
    assert parse_file(content, "test.xlsx").subject_id.iloc[0] == "0001"
    assert parse_file(csv_bytes(frame), "test.csv").subject_id.iloc[0] == "0001"
    assert "'=1+1" in csv_bytes(frame).decode("utf-8-sig")
