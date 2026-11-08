from streamlit.testing.v1 import AppTest

from be_app.domain import digest


def test_removing_uploaded_pk_clears_staged_source_and_blocks_cached_export():
    app = AppTest.from_string(
        '''
import base64
import streamlit as st
from be_app.examples import demo_project, statistical_demo
from be_app.state import ProjectState
from be_app.ui import endpoint_be_panel
from be_app.widgets import stage_upload
if "active_project_state" not in st.session_state:
    state = ProjectState(demo_project(n=4))
    data = statistical_demo("2x2").to_csv(index=False).encode()
    state.set_draft("pk_import", "file", {"name":"synthetic.csv", "base64":base64.b64encode(data).decode()})
    state.set_draft("pk_import", "units_confirmed", True)
    st.session_state.active_project_state = state
state = st.session_state.active_project_state
st.session_state.project = state.project
# Exercise the exact file-uploader on_change callback with the value sent on removal.
if st.button("Simulate upload removal"):
    st.session_state.removed_upload = None
    stage_upload(state, "pk_import", "removed_upload")
endpoint_be_panel()
''', default_timeout=30,
    ).run()
    state = app.session_state.active_project_state
    raw, fingerprint = state.project.raw_base64, state.project.input_hash()
    next(b for b in app.button if b.label == "Phân tích bảng PK đã tải").click().run()
    assert not app.exception
    assert any(b.label == "Tải đầy đủ thống kê bảng PK" for b in app.get("download_button"))
    cached = app.session_state.pk_be_result
    cached_fingerprint = digest([r.model_dump(mode="json") for r in cached["results"]])
    next(b for b in app.button if b.label == "Simulate upload removal").click().run()
    assert not app.exception
    assert state.draft("pk_import", "file") is None
    assert state.draft("pk_import", "units_confirmed")
    assert any("STALE" in alert.value for alert in app.warning)
    assert next(b for b in app.button if b.label == "Phân tích bảng PK đã tải").disabled
    assert next(b for b in app.get("download_button") if b.label == "Tải đầy đủ thống kê bảng PK").disabled
    assert digest([r.model_dump(mode="json") for r in cached["results"]]) == cached_fingerprint
    assert state.project.raw_base64 == raw and state.project.input_hash() == fingerprint
    assert not state.project.runs


def test_independent_pk_settings_survive_navigation_reload_and_project_switch():
    app = AppTest.from_string(
        """
import streamlit as st
from be_app.examples import demo_project
from be_app.state import ProjectState
from be_app.ui import endpoint_be_panel
if "owners" not in st.session_state:
    st.session_state.owners = [ProjectState(demo_project(n=4)), ProjectState(demo_project(n=4))]
selected = st.selectbox("Owner", [0, 1], key="owner_selection")
owner = st.session_state.owners[selected]
if st.button("Reload controller"):
    owner = ProjectState(owner.project)
    st.session_state.owners[selected] = owner
st.session_state.active_project_state = owner
if st.checkbox("Show panel", value=True, key="show_panel"):
    endpoint_be_panel()
""",
        default_timeout=30,
    ).run()
    app.selectbox(key="pk_be_rule").set_value("FDA_NTI")
    app.selectbox(key="pk_be_design").set_value("full4")
    app.checkbox(key="pk_be_prespecified").check()
    app.text_area(key="pk_be_justification").set_value("Protocol-specific justification").run()
    owner = app.session_state.owners[0]
    assert owner.project.drafts["pk_review"]["rule"] == "FDA_NTI"
    app.checkbox(key="show_panel").uncheck().run()
    app.checkbox(key="show_panel").check().run()
    assert app.selectbox(key="pk_be_design").value == "full4"
    next(b for b in app.button if b.label == "Reload controller").click().run()
    assert app.checkbox(key="pk_be_prespecified").value
    app.selectbox(key="owner_selection").set_value(1).run()
    assert not app.checkbox(key="pk_be_prespecified").value
    assert app.text_area(key="pk_be_justification").value == ""
    app.selectbox(key="owner_selection").set_value(0).run()
    assert app.selectbox(key="pk_be_rule").value == "FDA_NTI"
    assert app.text_area(key="pk_be_justification").value == "Protocol-specific justification"
    assert not app.exception and not app.error
