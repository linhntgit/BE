"""Exercise the independent Quick BE workflow in Streamlit without a project."""

from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

from be_app.persistence import ProjectStore
from be_app.quick_be_ui import _nonblank_quick_rows
from be_app.ui import WORKFLOWS


def test_manual_quick_table_ignores_empty_spreadsheet_rows():
    frame = pd.DataFrame({
        "Subject": ["", "001", "", "002"],
        "Cmax": ["", "12.5", "", ""],
    })
    cleaned = _nonblank_quick_rows(frame)
    assert cleaned.Subject.tolist() == ["001", "002"]
    assert cleaned.Cmax.tolist() == ["12.5", ""]


def _pk_csv():
    lines = ["Subject,Sequence,Period,Treatment,Cmax,AUClast"]
    for number, sequence in enumerate(("TR", "RT", "TR", "RT", "TR", "RT"), 1):
        for period, treatment in enumerate(sequence, 1):
            value = (18 + number * 1.1 + (period - 1) * 0.3) * (1.07 if treatment == "T" else 1)
            lines.append(
                f"{number:03d},{sequence},{period},{treatment},{value},{value * (2.9 + number * 0.02)}"
            )
    return "\n".join(lines)


def _concentration_csv():
    rows = ["Subject,Sequence,Period,Treatment,Time,Cplasma"]
    for line in _pk_csv().splitlines()[1:]:
        subject, sequence, period, treatment, cmax, _ = line.split(",")
        for time, fraction in ((0, 0), (1, 0.65), (2, 1), (4, 0.75),
                               (8, 0.35), (12, 0.16), (18, 0.05)):
            rows.append(f"{subject},{sequence},{period},{treatment},{time},{float(cmax) * fraction}")
    return "\n".join(rows)


def _open_quick_page(tmp_path, monkeypatch):
    import be_app.ui as ui

    monkeypatch.setattr(ui, "store", lambda: ProjectStore(tmp_path / "quick_ui.sqlite"))
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=30).run()
    assert not app.exception
    app.sidebar.radio[0].set_value(WORKFLOWS[1]).run()
    assert not app.exception
    return app


def _upload_csv(app, content):
    uploader = next(x for x in app.file_uploader if x.key.startswith("quick_upload::"))
    uploader.set_value(("study.csv", content.encode(), "text/csv")).run()


def test_quick_be_upload_runs_without_creating_a_project_and_invalidates_old_result(tmp_path, monkeypatch):
    app = _open_quick_page(tmp_path, monkeypatch)
    assert app.session_state["project"] is None
    _upload_csv(app, _pk_csv())
    assert not app.exception
    assert next(x for x in app.selectbox if x.label == "Cmax").value == "Cmax"
    next(button for button in app.button if "Chạy phân tích BE nhanh" in button.label).click().run()
    assert not app.exception
    result = app.session_state["quick_be_result"][1]
    assert result.overall_status == "PASS"
    assert len(result.endpoints) == 12
    assert app.session_state["project"] is None
    assert any("PASS" in line.value for line in app.success)

    # Any change to the source must hide the old result until recalculated.
    # A real input change, using an endpoint value that remains valid.
    lines = _pk_csv().splitlines()
    first = lines[1].split(",")
    first[4] = str(float(first[4]) * 1.01)
    lines[1] = ",".join(first)
    updated = "\n".join(lines)
    _upload_csv(app, updated)
    assert any("Chạy lại" in message.value for message in app.warning)
    assert not any("PASS" in message.value for message in app.success)


def test_quick_be_rejects_reusing_the_same_source_column(tmp_path, monkeypatch):
    app = _open_quick_page(tmp_path, monkeypatch)
    _upload_csv(app, _pk_csv())
    next(x for x in app.selectbox if x.label == "AUClast").set_value("Cmax").run()
    assert any("nhiều trường" in message.value for message in app.error)
    assert not any("Chạy phân tích BE nhanh" in button.label for button in app.button)


def test_quick_be_uploaded_concentrations_complete_nca_and_be(tmp_path, monkeypatch):
    app = _open_quick_page(tmp_path, monkeypatch)
    _upload_csv(app, _concentration_csv())
    assert not app.exception
    assert next(r for r in app.radio if r.label == "Kiểu dữ liệu").value == "concentration"
    next(button for button in app.button if "Chạy phân tích BE nhanh" in button.label).click().run()
    assert not app.exception
    result = app.session_state["quick_be_result"][1]
    assert result.mode == "concentration"
    assert len(result.nca) == 12 and result.nca.status.eq("EVALUABLE").all()
    assert result.overall_status == "PASS"
    assert app.session_state["project"] is None


def test_quick_be_endpoint_tmax_is_mapped_and_shown_as_supportive_test(tmp_path, monkeypatch):
    app = _open_quick_page(tmp_path, monkeypatch)
    lines = _pk_csv().splitlines()
    tmax_csv = "\n".join([lines[0] + ",Tmax"] + [
        row + (",3" if row.split(",")[3] == "T" else ",2")
        for row in lines[1:]
    ])
    _upload_csv(app, tmax_csv)
    assert not app.exception
    assert next(s for s in app.selectbox if s.label == "Tmax (giờ)").value == "Tmax"
    next(button for button in app.button if "Chạy phân tích BE nhanh" in button.label).click().run()
    assert not app.exception
    result = app.session_state["quick_be_result"][1]
    assert result.tmax.status == "EVALUABLE"
    assert result.tmax.n_pairs == 6
    assert any("So sánh Tmax phi tham số" in x.value for x in app.markdown)
