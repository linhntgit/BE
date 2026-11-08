from pathlib import Path

import pandas as pd
import pytest

from be_app.examples import demo_project


def open_be_page(app, page):
    from be_app.ui import PAGES, STAGE_NAMES, STAGE_PAGES
    index = PAGES.index(page)
    stage = next(i for i, pages in enumerate(STAGE_PAGES) if index in pages)
    if app.sidebar.radio[1].value != STAGE_NAMES[stage]:
        app.sidebar.radio[1].set_value(STAGE_NAMES[stage]).run()
    if len(STAGE_PAGES[stage]) > 1:
        app.sidebar.radio[2].set_value(page).run()
    assert not app.exception
    return app


def create_demo_study(app, scenario="2x2"):
    """Exercise the public study form; loading a scenario alone never creates a study."""
    app.selectbox(key="study_demo_case").set_value(scenario).run()
    next(b for b in app.button if b.label == "Điền dữ liệu mẫu vào biểu mẫu nghiên cứu").click().run()
    assert not app.exception
    assert not app.session_state.get("active_project_state")
    next(b for b in app.button if b.label == "Tạo nghiên cứu").click().run()
    assert not app.exception
    assert app.session_state.project.study.is_demo
    return app

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def reference_pk():
    return pd.read_csv(FIXTURES / "BE_NCAResult4BE.csv").rename(
        columns={
            "SUBJ": "subject_id",
            "GRP": "sequence",
            "PRD": "period",
            "TRT": "treatment",
            "AUClast": "auc_last",
            "Cmax": "cmax",
        }
    )


@pytest.fixture(scope="session")
def demo():
    return demo_project(n=12)


@pytest.fixture
def small_demo():
    return demo_project(n=4)


@pytest.fixture
def exponential_profile():
    # Exact exponential after absorption peak at t=1; lambda=ln(2).
    return pd.DataFrame(
        dict(
            actual_time_h=[0, 1, 2, 3, 4, 5],
            concentration=[0, 16, 8, 4, 2, 1],
            blq_flag=[True, False, False, False, False, False],
        )
    )
