"""The sidebar shows three workflows with the full BE steps nested inside one."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from tests.conftest import open_be_page
from be_app.persistence import ProjectStore
from be_app.ui import PAGES, WORKFLOWS


def test_sidebar_workflows_keep_full_be_step_and_project(tmp_path, monkeypatch):
    import be_app.ui as ui

    monkeypatch.setattr(ui, "store", lambda: ProjectStore(tmp_path / "navigation.sqlite"))
    app = AppTest.from_file(
        str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=30
    ).run()

    assert not app.exception
    assert app.title[0].value == "Phân tích dược động học và tương đương sinh học"
    assert len(app.sidebar.radio) == 2
    assert app.sidebar.radio[0].options == list(WORKFLOWS)
    assert app.sidebar.radio[0].value == "BE đầy đủ"
    assert app.sidebar.radio[1].options == list(ui.STAGE_NAMES)
    assert any(b.label == "Lưu project BE đầy đủ (.bewf.zip)" for b in app.sidebar.button)
    assert any(u.label == "Chọn project BE đầy đủ" and u.allowed_type == [".zip"]
               for u in app.sidebar.file_uploader)

    from tests.conftest import create_demo_study
    create_demo_study(app)
    initial_revision = app.session_state.project.input_revision
    assert any(b.label == "Lưu project BE đầy đủ (.bewf.zip)"
               for b in app.sidebar.download_button)
    open_be_page(app, PAGES[6])
    assert app.session_state.last_page == PAGES[6]

    app.sidebar.radio[0].set_value("Phân tích PK độc lập").run()
    assert not app.exception
    assert len(app.sidebar.radio) == 1
    assert any(h.value == PAGES[10] for h in app.header)
    assert app.session_state.project.input_revision == initial_revision
    assert any(b.label == "Lưu project PK độc lập (.pk.zip)"
               for b in [*app.sidebar.button, *app.sidebar.download_button])
    assert any(u.label == "Chọn project PK độc lập" for u in app.sidebar.file_uploader)

    app.sidebar.radio[0].set_value("BE nhanh").run()
    assert not app.exception
    assert len(app.sidebar.radio) == 1
    assert any(h.value == PAGES[11] for h in app.header)
    assert app.session_state.project.input_revision == initial_revision
    assert any(b.label == "Lưu project BE nhanh (.be.zip)"
               for b in [*app.sidebar.button, *app.sidebar.download_button])
    assert any(u.label == "Chọn project BE nhanh" for u in app.sidebar.file_uploader)

    app.sidebar.radio[0].set_value("BE đầy đủ").run()
    assert not app.exception
    assert len(app.sidebar.radio) == 3
    assert app.sidebar.radio[1].options == list(ui.STAGE_NAMES)
    assert app.session_state.last_page == PAGES[6]
    assert app.session_state.project.input_revision == initial_revision


def test_learning_mode_advances_without_qc_or_freeze(tmp_path, monkeypatch):
    import be_app.ui as ui

    monkeypatch.setattr(ui, "store", lambda: ProjectStore(tmp_path / "learning.sqlite"))
    app = AppTest.from_file(
        str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=30
    ).run()
    assert not app.exception
    assert "full_be_learning_mode" not in app.session_state or not app.session_state.full_be_learning_mode
    assert not any(button.label == "Bước tiếp theo →" for button in app.button)

    from tests.conftest import create_demo_study

    create_demo_study(app)
    assert not app.session_state.project.freeze_hash
    app.sidebar.toggle[0].set_value(True).run()
    assert not app.exception
    assert app.session_state.full_be_learning_mode

    next_button = next(button for button in app.button if button.label == "Bước tiếp theo →")
    next_button.click().run()
    assert not app.exception
    assert app.session_state.last_page == PAGES[1]
    assert not app.session_state.project.freeze_hash

    open_be_page(app, PAGES[4])
    assert not app.exception
    skip_qc = next(
        button for button in app.button
        if button.label == "Bỏ qua QC để sang bước Phân tích NCA →"
    )
    skip_qc.click().run()
    assert not app.exception
    assert app.session_state.last_page == PAGES[5]
    assert not app.session_state.project.freeze_hash

    open_be_page(app, PAGES[5])
    assert not app.exception
    assert app.session_state.last_page == PAGES[5]
    assert not app.session_state.project.runs
    assert any(button.label == "Phân tích NCA và BE" and button.disabled for button in app.button)
    skip_nca = next(
        button for button in app.button
        if button.label == "Bỏ qua điều kiện NCA để sang Thống kê BE →"
    )
    skip_nca.click().run()
    assert not app.exception
    assert app.session_state.last_page == PAGES[6]
    assert not app.session_state.project.runs

    app.sidebar.toggle[0].set_value(False).run()
    assert not app.exception
    assert not any(button.label == "Bước tiếp theo →" for button in app.button)
