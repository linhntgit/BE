"""Preset import through the actual overview must create a clean project."""

import base64
from pathlib import Path

from streamlit.testing.v1 import AppTest

from tests.conftest import open_be_page
from be_app.persistence import ProjectStore
from be_app.presets import export_preset, from_project


def test_overview_imports_preset_without_inheriting_source_data_or_approvals(tmp_path, monkeypatch):
    import be_app.ui as ui

    database = ProjectStore(tmp_path / "preset-ui.sqlite")
    monkeypatch.setattr(ui, "store", lambda: database)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=30).run()
    from tests.conftest import create_demo_study
    create_demo_study(app)
    state = app.session_state.active_project_state
    state.set_draft("pk_import", "sheet", "PK")
    state.set_draft("pk_import", "scale", "ln")
    state.set_draft("pk_import", "treatments", '{"Capsule":"R","Tablet":"T"}')
    state.set_draft("pk_import", "units_confirmed", True)
    state.set_draft("pk_import", "file", {"name": "source.csv", "base64": "cHJpdmF0ZQ=="})
    source = state.project
    preset = export_preset(from_project(source, "Reusable source method"))
    # AppTest cannot upload files; seed the durable upload draft, then press the real UI button.
    state.set_draft("preset", "file", {"name": "method.json", "base64": base64.b64encode(preset).decode()})
    app.session_state.project = state.project
    app.run()
    next(b for b in app.button if b.label == "Tạo dự án mới từ preset").click().run()
    assert not app.exception and not app.error
    created = app.session_state.active_project_state.project
    assert created.project_id != source.project_id
    assert not created.raw_base64 and not created.runs and not created.freeze_hash
    assert not created.study.protocol and not created.study.sap and not created.study.scope_reviewed
    assert not created.nca_config.terminal_overrides
    assert created.drafts["pk_import"]["sheet"] == "PK"
    assert created.drafts["pk_import"]["scale"] == "ln"
    assert not created.drafts["pk_import"]["units_confirmed"]
    assert "file" not in created.drafts["pk_import"]
    assert "preset" not in created.drafts
    assert len(created.events) == 1 and created.events[0]["action"] == "create_from_preset"
    assert database.load(source.project_id).raw_base64 == source.raw_base64
    open_be_page(app, ui.PAGES[6])
    assert not app.exception
    assert app.selectbox(key="pk_be_rule").value == created.study.rule_set_id
    assert not next(c for c in app.checkbox if c.label == "Đã xác nhận đơn vị nguồn Cmax ng/mL và AUC h·ng/mL").value
