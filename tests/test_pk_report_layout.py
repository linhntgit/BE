"""Document structure and real-snapshot figures in standalone PK exports."""

from __future__ import annotations

import io
from zipfile import ZipFile

import fitz
import pandas as pd
import pytest
from docx import Document

from be_app.pk_records import create_snapshot, pdf_report, record_bytes, word_report
from be_app.pk_report_design import _representative_rows, report_figures


@pytest.mark.parametrize("multiple", [False, True], ids=["single-dose", "steady-state"])
def test_pk_reports_have_real_figures_toc_and_unicode(multiple):
    times = [0, 1, 2, 4, 8, 12]
    concentrations = [100, 82, 61, 38, 12, 0]
    observed = pd.DataFrame({
        "profile_id": ["PK01"] * len(times),
        "time_h": times,
        "concentration": concentrations,
        "blq": [False] * 5 + [True],
    })
    nca_result = {
        "profile_id": "PK01", "status": "Đủ điều kiện NCA", "n": len(times),
        "warnings": ["Ví dụ nhắc nhở về BLQ"],
    }
    if multiple:
        nca_result.update(cmax_tau_ng_ml=100, auc_tau_ng_h_ml=320)
        regimen = {
            "mode": "steady_state", "tau_h": 12, "number_doses": 10,
            "steady_state_confirmed": True, "time_basis": "last_dose",
        }
    else:
        nca_result.update(cmax_ng_ml=100, auc_0_inf=340)
        regimen = None
    model = {
        "profile_id": "PK01", "compartments": 1, "weighting": "none",
        "parameters": {"CL": 5.0, "Vc": 20.0}, "converged": True,
        "rmse_ng_ml": 1.5, "aicc": 18, "bic": 20, "jacobian_condition": 22,
        "time_h": times[:-1], "predicted": [99, 80, 60, 39, 13],
        "residuals": [1, 2, 1, -1, -1], "warnings": [],
    }
    snapshot = create_snapshot(
        observed, {"route": "iv_bolus", "dose": 100,
                   "integration": "linear_up_log_down"},
        [nca_result], [model], [], "Kiểm thử tiếng Việt & <PK>", regimen,
    )
    original = record_bytes(snapshot)

    docx_bytes = word_report(snapshot)
    word = Document(io.BytesIO(docx_bytes))
    headings_1 = [p.text for p in word.paragraphs if p.style.name == "Heading 1"]
    headings_2 = [p.text for p in word.paragraphs if p.style.name == "Heading 2"]
    assert len(headings_1) == 9
    assert len(headings_2) >= 3
    assert headings_1[0].startswith("1. Tóm tắt")
    assert any("Dữ liệu đầu vào" in heading for heading in headings_1)
    assert any("Hồ sơ PK01" in heading for heading in headings_2)
    assert len(word.inline_shapes) >= 2  # linear, log, and model residuals
    with ZipFile(io.BytesIO(docx_bytes)) as archive:
        xml = archive.read("word/document.xml").decode("utf-8")
        settings = archive.read("word/settings.xml").decode("utf-8")
        assert 'TOC \\o &quot;1-2&quot;' in xml or 'TOC \\o "1-2"' in xml
        assert "updateFields" in settings
        assert "word/media/image1.png" in archive.namelist()

    pdf = fitz.open(stream=pdf_report(snapshot), filetype="pdf")
    assert pdf.page_count >= 4
    toc_text = pdf[1].get_text()
    full_text = "\n".join(page.get_text() for page in pdf)
    assert "MỤC LỤC" in toc_text
    assert "Tóm tắt phân tích" in toc_text
    assert "Kiểm thử tiếng Việt" in full_text
    assert "SHA-256" in full_text
    assert sum(len(page.get_images(full=True)) for page in pdf) >= 2
    assert ("Đã xác nhận ngoài ứng dụng" in full_text) == multiple
    assert record_bytes(snapshot) == original  # exporting cannot change the source


def test_report_figures_convert_original_concentration_units():
    """Observations and fitted curves must share ng/mL axes in exported charts."""
    data = [
        {"profile_id": "PK02", "time_h": t, "concentration": c, "blq": False}
        for t, c in ((0, 100.0), (1, 50.0), (2, 25.0))
    ]
    fitted = [{"profile_id": "PK02", "compartments": 1,
               "time_h": [0, 1, 2], "predicted": [100, 50, 25],
               "residuals": [0, 0, 0]}]
    base = {"settings": {"concentration_unit": "ng/mL"},
            "data": data, "models": fitted}
    converted = {"settings": {"concentration_unit": "µg/mL"},
                 "data": [{**r, "concentration": r["concentration"] / 1000} for r in data],
                 "models": fitted}

    figures_base = report_figures(base)
    figures_converted = report_figures(converted)
    assert len(figures_base) == len(figures_converted) == 3
    assert figures_base == figures_converted
    assert "µg/mL" in _representative_rows(converted)[0][0][2]
