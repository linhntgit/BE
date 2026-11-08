import pandas as pd
from streamlit.testing.v1 import AppTest

from be_app.review import terminal_figure


def test_terminal_plot_marks_actual_selection_and_excludes_zero_on_log_axis():
    group = pd.DataFrame({"actual_time_h": [0, 1, 2, 3], "concentration": [0, 8, 4, 2]})
    result = {
        "terminal_selected": {
            "times": [1, 2, 3],
            "intercept": 2.772588722239781,
            "slope": -0.6931471805599453,
        }
    }
    figure = terminal_figure(group, result, {})
    assert list(figure.data[0].x) == [1, 2, 3]
    assert list(figure.data[1].x) == [1, 2, 3]
    assert figure.data[1].name == "Automatic selected points"
    assert figure.layout.yaxis.type == "log"


def test_terminal_ui_applies_review_without_mutating_raw_or_running_study():
    app = AppTest.from_string(
        """
import streamlit as st
from be_app.examples import demo_project
from be_app.state import ProjectState
from be_app.ui import terminal_review_panel
if "active_project_state" not in st.session_state:
    st.session_state.active_project_state = ProjectState(demo_project(n=4))
st.session_state.project = st.session_state.active_project_state.project
terminal_review_panel(st.session_state.active_project_state)
""",
        default_timeout=30,
    ).run()
    app.checkbox[0].check().run()
    raw = app.session_state.project.raw_base64
    next(s for s in app.selectbox if s.label == "Cách chọn pha cuối").set_value("manual").run()
    times = app.multiselect[0].options[-3:]
    app.multiselect[0].set_value([float(x) for x in times])
    app.text_area[0].set_value("Reviewed terminal selection")
    app.text_input[0].set_value("PK reviewer").run()
    next(b for b in app.button if b.label == "Xem trước tự động và lựa chọn terminal").click().run()
    assert not app.exception
    next(b for b in app.button if b.label == "Áp dụng lựa chọn terminal").click().run()
    assert not app.exception
    state = app.session_state.active_project_state
    assert len(state.project.nca_config.terminal_overrides) == 1
    assert state.project.nca_config.terminal_overrides[0].reviewer == "PK reviewer"
    assert state.project.raw_base64 == raw and not state.project.runs
    assert state.metrics["analyses"] == 0
    assert not any(key.startswith("terminal:") for key in state.project.drafts)
