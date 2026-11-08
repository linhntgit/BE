"""Import must preserve IDs and provenance while requiring explicit source interpretation."""

import io

import numpy as np
import pandas as pd
import pytest

from be_app.pk_import import PKImportConfig, import_pk, workbook_sheets


def source_table():
    return pd.DataFrame(
        {
            "Subject": ["001", "001", "002", "002"],
            "Sequence": ["TR", "TR", "RT", "RT"],
            "Period": [1, 2, 1, 2],
            "Treatment": ["Tablet", "Capsule", "Capsule", "Tablet"],
            "Cmax": [12.0, 10.0, 14.0, 11.0],
        }
    )


def encoded(frame):
    return frame.to_csv(index=False).encode()


def config(**updates):
    return PKImportConfig(**{"treatment_mapping": {"Tablet": "T", "Capsule": "R"}, **updates})


@pytest.mark.parametrize("scale", ["raw", "ln", "log10"])
def test_import_inverts_only_declared_scale_and_preserves_identifiers(scale):
    original = source_table()
    frame = original.copy()
    if scale != "raw":
        frame["Cmax"] = np.log(frame.Cmax) if scale == "ln" else np.log10(frame.Cmax)
    content = encoded(frame)
    data, provenance = import_pk(content, "source.csv", config(scale=scale))
    assert list(data.subject_id) == ["001", "001", "002", "002"]
    assert data.cmax.to_numpy() == pytest.approx(original.Cmax.to_numpy())
    assert data.treatment.tolist() == ["T", "R", "R", "T"]
    assert provenance["mapping"]["scale"] == scale and len(provenance["input_sha256"]) == 64
    assert provenance["source_treatment_labels"] == ["Capsule", "Tablet"]
    second, manifest = import_pk(content, "source.csv", config(scale=scale))
    assert manifest == provenance
    pd.testing.assert_frame_equal(second, data)


def test_select_nonfirst_workbook_sheet_and_require_explicit_mapping():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame({"notes": ["not PK"]}).to_excel(writer, sheet_name="Readme", index=False)
        source_table().to_excel(writer, sheet_name="PK", index=False)
    content = output.getvalue()
    assert workbook_sheets(content, "study.xlsx") == ["Readme", "PK"]
    with pytest.raises(ValueError, match="Mapping thiếu"):
        import_pk(content, "study.xlsx", config())
    data, provenance = import_pk(content, "study.xlsx", config(sheet="PK"))
    assert len(data) == 4 and provenance["mapping"]["sheet"] == "PK"
    with pytest.raises(ValueError, match="mapping rõ"):
        import_pk(content, "study.xlsx", PKImportConfig(sheet="PK"))


def test_no_silent_sequence_inference_and_no_ambiguous_duplicate_keys():
    data = source_table()
    data["Sequence"] = data.Sequence.map({"TR": "AB", "RT": "BA"})
    with pytest.raises(ValueError, match="mapping sequence"):
        import_pk(encoded(data), "x.csv", config())
    mapped, _ = import_pk(encoded(data), "x.csv", config(sequence_mapping={"AB": "TR", "BA": "RT"}))
    assert set(mapped.sequence) == {"TR", "RT"}
    with pytest.raises(ValueError, match="trùng"):
        import_pk(encoded(pd.concat([source_table(), source_table().iloc[:1]])), "x.csv", config())


@pytest.mark.parametrize(
    "value,scale", [(0, "raw"), (-1, "raw"), (float("inf"), "raw"), (701, "ln"), (301, "log10")]
)
def test_invalid_endpoint_or_unstable_inverse_transform_is_rejected(value, scale):
    data = source_table()
    data.loc[0, "Cmax"] = value
    with pytest.raises(ValueError):
        import_pk(encoded(data), "x.csv", config(scale=scale))


def test_missing_is_retained_instead_of_zero_or_subject_exclusion():
    data = source_table().astype(object)
    data.loc[0, "Cmax"] = "."
    imported, _ = import_pk(encoded(data), "x.csv", config())
    assert len(imported) == 4 and pd.isna(imported.cmax.iloc[0])
