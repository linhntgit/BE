"""Coverage of user-facing explanations for input and output labels."""

from be_app.field_help import (
    BE_RESULTS,
    INDEPENDENT_HELP,
    NCA_DETAIL_COLUMNS,
    NCA_PARAMETERS,
    PAGE_HELP,
    RAW_COLUMNS,
    TMAX_RESULTS,
    field_help_for,
    get_field_description,
    render_table_legend,
    table_column_config,
)
from be_app.imports import REQUIRED
from be_app.nca_reporting import PARAMETERS


def _labels(entries):
    return {part.strip() for label, _ in entries for part in label.split(" / ")}


def test_required_import_columns_and_nca_report_parameters_are_explained():
    assert set(REQUIRED) <= _labels(RAW_COLUMNS)
    assert {name for name, _, _ in PARAMETERS} <= _labels(NCA_PARAMETERS)
    assert {"Subject", "Treatment", "Sequence", "Period", "Parameter", "Units", "Estimate"} <= _labels(
        NCA_DETAIL_COLUMNS
    )


def test_help_covers_full_be_stages_and_independent_workflows():
    assert len(PAGE_HELP) == 10
    for page in range(10):
        assert field_help_for(page) == PAGE_HELP[page]
    assert set(INDEPENDENT_HELP) == {"pk", "quick"}
    for workflow in INDEPENDENT_HELP:
        assert field_help_for(workflow)
    assert {"GMR", "MSE", "sWR", "CVwR"} <= _labels(BE_RESULTS)
    assert {"Tmax", "p hai phía", "Trung vị (giờ)"} <= _labels(TMAX_RESULTS)


def test_each_help_entry_is_unique_and_contains_a_short_explanation():
    for groups in (*PAGE_HELP, *INDEPENDENT_HELP.values()):
        assert groups
        for group in groups:
            assert group.title.strip()
            labels = [label for label, _ in group.entries]
            assert len(labels) == len(set(labels))
            assert all(label.strip() and meaning.strip() for label, meaning in group.entries)
            assert all(len(meaning) <= 180 for _, meaning in group.entries)


def test_in_table_help_tooltips_and_legends():
    test_terms = ["GMR", "CI90 thấp (%)", "Cmax", "sWR", "CVwR", "MSE", "actual_time_h", "Tmax"]
    for term in test_terms:
        desc = get_field_description(term)
        assert desc and len(desc) > 10

    cfg = table_column_config(test_terms)
    assert len(cfg) == len(test_terms)
    for term in test_terms:
        assert cfg[term]["help"]

    # Legend renders cleanly without throwing exceptions
    render_table_legend(test_terms)
    render_table_legend([])


def test_displayed_workflow_columns_and_unique_dictionary_keys():
    import ast
    from pathlib import Path

    # Verify zero duplicate keys in any dict literal inside field_help.py
    tree = ast.parse(Path(__file__).resolve().parents[1].joinpath("be_app", "field_help.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            keys = [k.value for k in node.keys if isinstance(k, ast.Constant)]
            assert len(keys) == len(set(keys))

    displayed_cols = [
        "Vai trò",
        "Phương pháp",
        "CI 90% (bổ trợ nếu RSABE)",
        "Giới hạn",
        "UCB scaling",
        "Trạng thái",
        "Quyết định",
        "Lý do",
        "SD_ratio_CI90_lower",
        "SD_ratio_CI90_upper",
        "Mã hồ sơ",
        "Hồ sơ",
        "Số ngăn",
        "Trọng số",
        "Lambda-z (1/giờ)",
        "t½ (giờ)",
        "AUC0–∞ (ng·giờ/mL)",
        "Điều kiện Jacobian",
        "CL/F",
        "V/F",
        "Vc",
        "Vp3",
        "Vp3/F",
        "ka",
        "evaluable",
        "recruit",
        "achieved_power",
    ]
    for col in displayed_cols:
        desc = get_field_description(col)
        assert desc and len(desc) > 10, f"Missing tooltip for {col}"


