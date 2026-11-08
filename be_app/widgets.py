"""One-way Streamlit adapters. Callback errors never replace confirmed domain values."""

import base64
import hashlib
import inspect

import streamlit as st

from be_app.domain import Study
from be_app.field_help import get_field_description
from be_app.persistence import Project
from be_app.state import ProjectState


def changed(state: ProjectState, target: str, section: str, field: str, key: str):
    try:
        value = st.session_state[key]
        if target == "planning":
            state.set_planning(field, value)
        elif target == "preferences":
            state.set_preference(f"{section}.{field}", value)
            if section == "editor" and field in {"subject", "period"}:
                state._bindings.clear()
        else:
            state.set_draft(section, field, value)
        st.session_state.project = state.project
    except (ValueError, TypeError, OSError) as exc:
        st.session_state["callback_error"] = str(exc)
        # Assignment is allowed inside the callback, before the widget is rebuilt.
        st.session_state[key] = value_for(state, target, section, field, None)


def value_for(state, target, section, field, default):
    if target == "planning":
        return state.planning()[field]
    if target == "preferences":
        return state.project.preferences.get(f"{section}.{field}", default)
    return state.draft(section, field, default)


class Widgets:
    def __init__(self, state: ProjectState, section: str, target: str = "draft"):
        self.state, self.section, self.target = state, section, target

    def key(self, field):
        return f"_ui::{self.state.project.project_id}::{self.state.mount_id}::{self.section}::{field}"

    def input(self, method: str, field: str, label: str, default=None, **kwargs):
        key = self.key(field)
        if key not in st.session_state:
            st.session_state[key] = value_for(self.state, self.target, self.section, field, default)
        if "help" not in kwargs:
            desc = get_field_description(label) or get_field_description(field)
            if desc:
                target_func = getattr(st, method, None)
                if target_func is not None:
                    try:
                        params = inspect.signature(target_func).parameters
                        if "help" in params or any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values()):
                            kwargs["help"] = desc
                    except (ValueError, TypeError):
                        pass
        return getattr(st, method)(
            label,
            key=key,
            on_change=changed,
            args=(self.state, self.target, self.section, field, key),
            **kwargs,
        )

    def text(self, field, label, default="", **kwargs):
        return self.input("text_input", field, label, default, **kwargs)

    def area(self, field, label, default="", **kwargs):
        return self.input("text_area", field, label, default, **kwargs)

    def number(self, field, label, default, **kwargs):
        return self.input("number_input", field, label, default, **kwargs)

    def select(self, field, label, options, default=None, **kwargs):
        if not options:
            raise ValueError("Không có lựa chọn phù hợp cho " + label)
        key = self.key(field)
        saved = st.session_state.get(
            key,
            value_for(
                self.state, self.target, self.section, field, options[0] if default is None else default
            ),
        )
        if saved not in options:
            st.warning(
                f"{label}: lựa chọn đã lưu không còn tương thích. Hãy chọn lại; không tự thay dữ liệu bằng mặc định."
            )
            st.session_state[key] = None  # Before instantiation, never after widget creation.
        return self.input(
            "selectbox", field, label, options[0] if default is None else default, options=options, **kwargs
        )

    def check(self, field, label, default=False, **kwargs):
        return self.input("checkbox", field, label, default, **kwargs)


def stage_upload(state: ProjectState, section: str, key: str):
    uploaded = st.session_state[key]
    if uploaded is None and state.draft(section, "file") is None:
        return
    try:
        state.set_draft(
            section,
            "file",
            (
                dict(
                    name=uploaded.name,
                    base64=base64.b64encode(uploaded.getvalue()).decode("ascii"),
                    sha256=hashlib.sha256(uploaded.getvalue()).hexdigest(),
                )
                if uploaded is not None
                else None
            ),
        )
        st.session_state.project = state.project
    except (ValueError, TypeError, OSError) as exc:
        st.session_state["callback_error"] = str(exc)


def editor_changed(state: ProjectState, binding, key: str):
    try:
        state.editor_diff(binding, st.session_state[key])
        st.session_state.project = state.project
    except (ValueError, TypeError, KeyError, OSError) as exc:
        st.session_state["callback_error"] = str(exc)
        # Read-only editor key is never assigned/reset. A fresh binding restores confirmed/pending data.
        state._bindings.clear()


def creation_state(store) -> ProjectState:
    if "creation_state" not in st.session_state:
        project = Project(study=Study(study_id="DRAFT", title="Bản nháp khởi tạo"))
        revision = store.save(project, 0)
        st.session_state.creation_state = ProjectState(project, store, revision)
    return st.session_state.creation_state
