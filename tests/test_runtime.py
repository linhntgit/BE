import pytest

from be_app.runtime import runtime_issue


@pytest.mark.parametrize(
    "python_version,streamlit_version",
    [
        ((3, 10, 11), "1.58.0"),
        ((3, 12, 14), "1.58.0"),
        ((3, 14, 0), "1.66.1"),
    ],
)
def test_wrong_runtime_has_actionable_reason(python_version, streamlit_version):
    assert runtime_issue(python_version, streamlit_version)


def test_locked_runtime_is_accepted():
    assert runtime_issue((3, 12, 14), "1.66.1") is None


def test_widget_adapter_does_not_require_persist_state(small_demo, monkeypatch):
    from be_app import widgets
    from be_app.state import ProjectState

    session = {}
    monkeypatch.setattr(widgets.st, "session_state", session)
    calls = []

    def legacy_input(label, *, key, on_change, args, min_value, max_value):
        calls.append(key)
        return session[key]

    monkeypatch.setattr(widgets.st, "number_input", legacy_input)
    state = ProjectState(small_demo)
    state.set_planning("cv_auc", 24.7)
    value = widgets.Widgets(state, "planning", "planning").number(
        "cv_auc", "CV AUC (%)", 20.0, min_value=0.1, max_value=200.0
    )
    assert value == 24.7 and len(calls) == 1
