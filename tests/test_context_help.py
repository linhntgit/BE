import re
"""Context help is pedagogical, conditional on page, and read-only for studies."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from tests.conftest import open_be_page
from be_app.context_help import (
    DATA_INTEGRITY_TERMS,
    LESSONS,
    PK_STANDALONE_LESSON,
    PROFILE_LESSONS,
    QUICK_BE_LESSON,
    QUICK_TASKS,
    RESEARCH_TASKS,
    integrity_terms_for,
    lesson_for,
    profile_help,
)
from be_app.persistence import ProjectStore
from be_app.regulations import RULES


def test_every_workflow_step_has_complete_teaching_sections():
    from be_app.ui import PAGES

    # The guided workflow has ten steps; independent analysis pages follow it.
    assert len(LESSONS) == 10
    assert len(RESEARCH_TASKS) == len(LESSONS)
    assert len(PAGES) >= len(LESSONS)
    assert all("Trợ giúp" not in page for page in PAGES)
    for index, page in enumerate(PAGES[:len(LESSONS)]):
        lesson = lesson_for(index)
        assert page
        assert len(lesson.interface) >= 2
        assert len(lesson.actions) >= 2
        assert len(lesson.theory) >= 2
        assert len(lesson.terms) >= 2
        assert len(lesson.exercise) > 20


def test_integrity_glossary_is_complete_and_contextual():
    assert len(DATA_INTEGRITY_TERMS) >= 20
    assert "Statistical Analysis Plan" in DATA_INTEGRITY_TERMS["sap"].name
    assert "Attributable" in DATA_INTEGRITY_TERMS["alcoa"].meaning
    assert "single-user" in DATA_INTEGRITY_TERMS["audit_trail"].app_example
    for index in range(len(LESSONS)):
        terms = integrity_terms_for(index)
        names = [term.name for term in terms]
        assert len(terms) >= 7
        assert len(names) == len(set(names))
        assert all(term.meaning and term.app_example for term in terms)
        assert names[:4] == [
            DATA_INTEGRITY_TERMS[key].name
            for key in ("integrity", "alcoa", "sap", "audit_trail")
        ]
    assert DATA_INTEGRITY_TERMS["raw"] in integrity_terms_for(3)
    assert DATA_INTEGRITY_TERMS["freeze"] in integrity_terms_for(4)
    assert DATA_INTEGRITY_TERMS["reproducibility"] in integrity_terms_for(6)
    assert DATA_INTEGRITY_TERMS["esign"] in integrity_terms_for(9)
    assert DATA_INTEGRITY_TERMS["esign"] not in integrity_terms_for(3)


def test_all_regulatory_profiles_have_theory_current_capability_and_sources():
    assert set(RULES) == set(PROFILE_LESSONS)
    for rule_id, rule in RULES.items():
        explanations, status, urls = profile_help(rule_id)
        assert len(explanations) == 2
        assert "Kết luận endpoint:" in status
        assert "thẩm định độc lập:" in status
        assert urls == rule.sources
        assert all(url.startswith("https://") for url in urls)
    assert "sWT/sWR" in " ".join(profile_help("FDA_NTI")[0])
    assert "sWR < 0,294" in " ".join(profile_help("FDA_HVD_RSABE_2026")[0])


def test_help_pane_toggles_and_tracks_navigation_without_changing_study(tmp_path, monkeypatch):
    import be_app.ui as ui

    monkeypatch.setattr(ui, "store", lambda: ProjectStore(tmp_path / "teaching.sqlite"))
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=30).run()
    assert not app.exception
    assert app.sidebar.radio[0].options == list(ui.WORKFLOWS)
    assert app.sidebar.radio[1].options == list(ui.STAGE_NAMES)
    assert len([s for s in app.subheader if s.value == "Trợ giúp"]) == 1
    assert "Tạo nghiên cứu" in " ".join(m.value for m in app.markdown)
    assert any(exp.label == "Data Integrity · Thuật ngữ và ví dụ" for exp in app.get("expander"))
    assert any("Statistical Analysis Plan" in m.value for m in app.markdown)

    from tests.conftest import create_demo_study
    create_demo_study(app)
    initial_revision = app.session_state.project.input_revision
    open_be_page(app, ui.PAGES[4])
    assert any("Data Freeze" in m.value for m in app.markdown)
    assert any("Data correction" in m.value for m in app.markdown)
    assert not app.exception
    assert app.session_state.project.input_revision == initial_revision

    next(toggle for toggle in app.toggle if toggle.label == "Trợ giúp bên phải").set_value(False).run()
    assert not any(s.value == "Trợ giúp" for s in app.subheader)
    assert not any("Statistical Analysis Plan" in m.value for m in app.markdown)
    open_be_page(app, ui.PAGES[9])
    assert not any(s.value == "Trợ giúp" for s in app.subheader)
    assert app.session_state.project.input_revision == initial_revision

    next(toggle for toggle in app.toggle if toggle.label == "Trợ giúp bên phải").set_value(True).run()
    assert any(s.value == "Trợ giúp" for s in app.subheader)
    assert any("Audit trail" in m.value for m in app.markdown)
    assert any("Role-Based Access Control" in m.value for m in app.markdown)
    assert not app.exception


def test_help_method_selection_does_not_change_study_rule(tmp_path, monkeypatch):
    import be_app.ui as ui

    monkeypatch.setattr(ui, "store", lambda: ProjectStore(tmp_path / "methods.sqlite"))
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=30).run()
    from tests.conftest import create_demo_study
    create_demo_study(app)
    original_rule = app.session_state.project.study.rule_set_id
    selector = next(select for select in app.selectbox if select.label == "Tìm hiểu profile")
    selector.set_value("FDA_HVD_RSABE_2026").run()
    assert not app.exception
    assert app.session_state.project.study.rule_set_id == original_rule
    assert any("sWR < 0,294" in m.value for m in app.markdown)
    assert app.session_state.context_help_method == "FDA_HVD_RSABE_2026"


def test_teaching_information_defaults_and_survives_navigation(tmp_path, monkeypatch):
    import be_app.ui as ui

    monkeypatch.setattr(ui, "store", lambda: ProjectStore(tmp_path / "classroom.sqlite"))
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=30).run()
    assert not app.exception

    expected = {
        "Tên trường": "Trường Đại học Dược Hà Nội",
        "Tên Khoa": "Bào chế và Công nghệ dược phẩm",
        "Tên giảng viên": "Nguyễn Trần Linh",
        "Tên Học viên": "",
        "Tên lớp": "",
        "Khoá": "",
    }
    assert [(item.label, item.value) for item in app.text_input if item.label in expected] == list(
        expected.items()
    )

    next(item for item in app.text_input if item.label == "Tên Học viên").set_value("Học viên A").run()
    next(item for item in app.text_input if item.label == "Tên lớp").set_value("BE-01").run()
    next(item for item in app.text_input if item.label == "Khoá").set_value("2026").run()
    from tests.conftest import create_demo_study
    create_demo_study(app)
    original_revision = app.session_state.project.input_revision
    open_be_page(app, ui.PAGES[6])
    next(item for item in app.toggle if item.label == "Trợ giúp bên phải").set_value(False).run()

    assert not app.exception
    assert app.session_state.teaching_student == "Học viên A"
    assert app.session_state.teaching_class == "BE-01"
    assert app.session_state.teaching_cohort == "2026"
    assert app.session_state.project.input_revision == original_revision
    assert app.session_state.project.preferences == {}
    assert len([item for item in app.text_input if item.label in expected]) == 6


def test_independent_help_tracks_work_in_progress(tmp_path, monkeypatch):
    import be_app.ui as ui

    monkeypatch.setattr(ui, "store", lambda: ProjectStore(tmp_path / "independent.sqlite"))
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=60).run()
    app.sidebar.radio[0].set_value("BE nhanh").run()
    assert QUICK_TASKS["input"] in [item.value for item in app.markdown]
    app.selectbox(key="quick_demo_case").set_value("endpoint")
    app.button(key="quick_demo_load").click().run()
    assert QUICK_TASKS["endpoint"] in [item.value for item in app.markdown]
    app.button(key="quick_run").click().run()
    assert QUICK_TASKS["results"] in [item.value for item in app.markdown]
    app.sidebar.radio[0].set_value("Phân tích PK độc lập").run()
    app.radio(key="pk_dose_mode").set_value("steady_state").run()
    assert any("Ghi bằng chứng đạt trạng thái ổn định" in item.value for item in app.markdown)
    app.radio(key="pk_dose_mode").set_value("single").run()
    assert any("Chọn một hồ sơ đơn liều" in item.value for item in app.markdown)
    assert not any("Ghi bằng chứng đạt trạng thái ổn định" in item.value for item in app.markdown)
    assert not app.exception


def test_all_lessons_have_complete_six_pedagogical_subsections():
    # Verify all 10 workflow lessons
    for index in range(len(LESSONS)):
        lesson = lesson_for(index)
        assert len(lesson.actions) >= 2
        assert len(lesson.theory) >= 2
        assert len(lesson.diagram) > 10
        assert lesson.diagram.strip().startswith("<svg")
        assert len(lesson.regulations) >= 2
        assert len(lesson.equations) >= 1
        for eq, desc in lesson.equations:
            assert eq and desc
            assert not re.search(r'\\n[^\w]|\\n$', desc)
            assert len([line for line in desc.splitlines() if line.strip().startswith('-')]) >= 2
        assert len(lesson.terms) >= 2
        assert len(lesson.exercise) > 20
        assert len(lesson.questions) >= 1
        assert len(lesson.references) >= 2

    # Verify Standalone PK (Lesson 10) and Quick BE (Lesson 11)
    for idx, standalone in ((10, PK_STANDALONE_LESSON), (11, QUICK_BE_LESSON)):
        lesson = lesson_for(idx)
        assert lesson is standalone
        assert len(lesson.actions) >= 2
        assert len(lesson.theory) >= 2
        assert len(lesson.diagram) > 10
        assert lesson.diagram.strip().startswith("<svg")
        assert len(lesson.regulations) >= 1
        assert len(lesson.equations) >= 1
        for eq, desc in lesson.equations:
            assert eq and desc
            assert not re.search(r'\\n[^\w]|\\n$', desc)
            assert len([line for line in desc.splitlines() if line.strip().startswith('-')]) >= 2
        assert len(lesson.terms) >= 2
        assert len(lesson.exercise) > 20
        assert len(lesson.questions) >= 1
        assert len(lesson.references) >= 2


def test_ui_renders_six_subsections_across_modes(tmp_path, monkeypatch):
    import be_app.ui as ui

    monkeypatch.setattr(ui, "store", lambda: ProjectStore(tmp_path / "sections.sqlite"))
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=60).run()
    markdown_vals = [m.value for m in app.markdown]

    # Verify all 6 subsections are rendered in default view
    assert "### 1. Hướng dẫn thao tác" in markdown_vals
    assert len(app.image) >= 1
    assert "### 2. Tóm tắt lý thuyết và tiêu chuẩn pháp quy" in markdown_vals
    assert "### 3. Phương trình toán học và giải thích biến số" in markdown_vals
    assert "### 4. Thuật ngữ" in markdown_vals
    assert "### 5. Câu hỏi gợi ý và chủ đề tự học" in markdown_vals
    assert "### 6. Tài liệu tham khảo" in markdown_vals

    # Check for Quick BE
    app.sidebar.radio[0].set_value("BE nhanh").run()
    quick_md = [m.value for m in app.markdown]
    assert "### 1. Hướng dẫn thao tác" in quick_md
    assert "### 3. Phương trình toán học và giải thích biến số" in quick_md
    assert "### 6. Tài liệu tham khảo" in quick_md

    # Check for PK Standalone
    app.sidebar.radio[0].set_value("Phân tích PK độc lập").run()
    pk_md = [m.value for m in app.markdown]
    assert "### 1. Hướng dẫn thao tác" in pk_md
    assert "### 2. Tóm tắt lý thuyết và tiêu chuẩn pháp quy" in pk_md
    assert "### 3. Phương trình toán học và giải thích biến số" in pk_md

def test_floating_help_dialog_opens_and_renders(tmp_path, monkeypatch):
    import be_app.ui as ui

    monkeypatch.setattr(ui, 'store', lambda: ProjectStore(tmp_path / 'dialog.sqlite'))
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'), default_timeout=60).run()
    assert not app.exception

    # Check that expand button exists on right pane
    expand_btn = app.button(key='btn_expand_floating_help_0')
    assert expand_btn is not None
    assert 'Mở rộng nổi' in expand_btn.label

    # Click expand button to trigger the floating dialog
    expand_btn.click().run()
    assert not app.exception

    # Verify dialog content appears
    assert any('mở rộng toàn diện theo chiều ngang' in info.value for info in app.info)
    assert any('Chế độ toàn cảnh mở rộng nổi' in c.value for c in app.caption)
    assert len(app.image) >= 2
    close_btn = app.button(key='btn_close_floating_help_dialog')
    assert close_btn is not None
    close_btn.click().run()
    assert not app.exception



def test_ivivc_inspired_help_features(tmp_path, monkeypatch):
    import be_app.ui as ui

    monkeypatch.setattr(ui, 'store', lambda: ProjectStore(tmp_path / 'ivivc_test.sqlite'))
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'), default_timeout=60).run()
    assert not app.exception

    # 1. Check Live Workspace Diagnostic Banner
    assert any('Trạng thái Ngữ cảnh Thực hành (Live Workspace Diagnostics)' in m.value for m in app.markdown)

    # 2. Check Dimensional Analysis Expander
    assert any('Bộ Kiểm tra Đồng nhất Thứ nguyên & Đơn vị' in exp.label for exp in app.get('expander'))

    # 3. Check Chapter Browsing Navigation
    nav_select = next(s for s in app.selectbox if s.label == '📚 Xem chủ đề trợ giúp & bài giảng')
    assert nav_select is not None
    assert len(nav_select.options) == 12
    assert any('Tạo nghiên cứu' in opt for opt in nav_select.options)
    assert any('Linear Up / Log Down' in opt for opt in nav_select.options)

    # Switch help chapter to Step 5 (NCA) while staying on Step 0
    nav_select.select_index(5).run()
    assert not app.exception
    # Now help displays Linear Up / Log Down from Step 5
    assert any('Linear Up / Log Down' in m.value for m in app.markdown)

    # Reset button appears to return to active step
    reset_btn = next(b for b in app.button if 'Quay lại bước đang làm' in b.label)
    assert reset_btn is not None
    reset_btn.click().run()
    assert not app.exception


def test_nine_compartmental_models_are_comprehensive_and_valid():
    """Verify all 9 compartmental models (3 routes x 3 compartments) have complete graduate-level documentation."""
    import xml.etree.ElementTree as ET
    from be_app.compartment_help import MODEL_DOCS
    from be_app.diagram_svg import get_diagram_10, get_diagram_compartment
    from be_app.context_equations import EQUATIONS_10

    # 1. Check all 9 models exist in MODEL_DOCS
    assert len(MODEL_DOCS) == 9
    expected_routes = {"iv_bolus", "iv_infusion", "oral"}
    expected_cpts = {1, 2, 3}
    found_combinations = set()

    for title, doc in MODEL_DOCS.items():
        assert doc.route in expected_routes
        assert doc.compartments in expected_cpts
        found_combinations.add((doc.route, doc.compartments))

        # Check required subsections A, C, D, E
        assert len(doc.theory) > 100
        assert "Khái niệm" in doc.theory or "Nguyên lý" in doc.theory
        assert doc.ode_latex and len(doc.ode_latex) > 10
        assert doc.solution_latex and len(doc.solution_latex) > 10
        assert len(doc.parameters) > 50
        assert "mg" in doc.parameters or "L" in doc.parameters or "h" in doc.parameters
        assert len(doc.example) > 50
        assert "mg" in doc.example and "L" in doc.example
        assert len(doc.notes) > 30

    assert found_combinations == {(r, c) for r in expected_routes for c in expected_cpts}

    iv_bolus_three = next(doc for doc in MODEL_DOCS.values()
                          if (doc.route, doc.compartments) == ("iv_bolus", 3))
    iv_infusion_three = next(doc for doc in MODEL_DOCS.values()
                             if (doc.route, doc.compartments) == ("iv_infusion", 3))
    oral_three = next(doc for doc in MODEL_DOCS.values()
                      if (doc.route, doc.compartments) == ("oral", 3))
    assert "ngoại suy" in iv_bolus_three.notes
    assert "không phải điểm đo" in iv_bolus_three.parameters
    assert "\\mathbf{1}" in iv_infusion_three.ode_latex
    assert "\\delta" not in iv_infusion_three.ode_latex
    assert "7 tham số" in oral_three.theory
    assert "thời gian trễ" in oral_three.theory
    assert "3 ngăn" in " ".join(PK_STANDALONE_LESSON.interface)

    # 2. Check all 9 individual SVG diagrams compile to valid XML
    for route, c in found_combinations:
        svg_xml = get_diagram_compartment(route, c)
        assert svg_xml.strip().startswith("<svg")
        tree = ET.fromstring(svg_xml)
        assert tree.tag.endswith("svg")

    # 3. Check master diagram 10 compiles to valid XML
    master_svg = get_diagram_10()
    assert master_svg.strip().startswith("<svg")
    master_tree = ET.fromstring(master_svg)
    assert master_tree.tag.endswith("svg")

    # 4. Check EQUATIONS_10 covers all 9 models + multi-dose + model selection
    assert len(EQUATIONS_10) >= 11
    eq_texts = " ".join(desc for _, desc in EQUATIONS_10)
    assert "IV Bolus" in eq_texts
    assert "IV Infusion" in eq_texts
    assert "Bateman" in eq_texts
    assert "AICc" in eq_texts
    assert "BIC" in eq_texts


def test_pk_standalone_help_model_explorer_ui(tmp_path, monkeypatch):
    """Test interactive selection of 9 compartmental models in PK Standalone help pane."""
    import be_app.ui as ui

    monkeypatch.setattr(ui, "store", lambda: ProjectStore(tmp_path / "model_explorer.sqlite"))
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=60).run()
    assert not app.exception

    # Switch to Standalone PK workflow
    app.sidebar.radio[0].set_value("Phân tích PK độc lập").run()
    assert not app.exception

    # Locate the model explorer selectbox
    model_sel = next((s for s in app.selectbox if s.label == "Chọn mô hình cần tra cứu chuyên sâu"), None)
    assert model_sel is not None
    assert len(model_sel.options) == 10
    assert "Toàn cảnh 9 mô hình (Tổng quan kiến trúc)" in model_sel.options[0]

    # Select 2-Compartment IV Bolus
    model_sel.select_index(2).run()
    assert not app.exception
    assert any("Vancomycin" in m.value for m in app.markdown)
    assert any("bi-exponential" in m.value.lower() or "biexponential" in m.value.lower() or "ngăn 2" in m.value.lower() for m in app.markdown)

    # Select 1-Compartment Oral (Bateman)
    model_sel.select_index(7).run()
    assert not app.exception
    assert any("Paracetamol" in m.value for m in app.markdown)
    assert any("Bateman" in m.value for m in app.markdown)

    # Select 2-Compartment IV Infusion
    model_sel.select_index(5).run()
    assert not app.exception
    assert any("Truyền tĩnh mạch liên tục (IV Infusion) — Mô hình 2 Ngăn" in m.value for m in app.markdown)


def test_contextual_help_scientific_regulatory_and_code_alignment():
    """Verify contextual help, equations, SVGs, and compartment models align with actual algorithms."""
    import xml.etree.ElementTree as ET
    from be_app.compartment_help import MODEL_DOCS
    from be_app.context_equations import EQUATIONS_1, EQUATIONS_6, EQUATIONS_7, EQUATIONS_9, EQUATIONS_11
    from be_app.diagram_svg import DIAGRAM_SVGS
    from be_app.field_help import PAGE_HELP

    # 1. All 12 SVG diagrams parse cleanly as XML and Lesson 0..11 include pedagogical extensions
    assert len(DIAGRAM_SVGS) == 12
    for idx, svg in DIAGRAM_SVGS.items():
        assert ET.fromstring(svg).tag.endswith("svg")
        lesson = lesson_for(idx)
        assert lesson.examples
        assert lesson.interpretation
        assert lesson.self_study
        assert lesson.question_answers

    # 2. Sample size planning aligns with design.py / design.tost_power (no unsupported ASEAN or fake replicate planner)
    assert "design.py" in " ".join(desc for _, desc in EQUATIONS_1)
    assert "design.tost_power" in DIAGRAM_SVGS[1]
    assert "scipy.integrate.quad" in " ".join(desc for _, desc in EQUATIONS_1)
    assert "replicate 3–4 kỳ" in " ".join(desc for _, desc in EQUATIONS_1)
    assert all("ASEAN" not in meaning for groups in PAGE_HELP for g in groups for _, meaning in g.entries)

    # 3. EMA ABEL, FDA RSABE, FDA NTI, and default Adjusted R² >= 0.80 accuracy
    eq6_text = " ".join(desc for _, desc in EQUATIONS_6)
    assert "0.29356" in eq6_text
    assert "0.760" in eq6_text
    assert "C_{\\max}" in eq6_text
    assert "0.294" in eq6_text
    assert "2.5" in eq6_text
    assert "0.80" in " ".join(desc for _, desc in EQUATIONS_7)
    assert "single-user" in " ".join(desc for _, desc in EQUATIONS_9)
    eq11_text = " ".join(desc for _, desc in EQUATIONS_11)
    assert "chưa hỗ trợ kiểm định phi tham số" in eq11_text
    assert "chưa hỗ trợ cho replicate" in " ".join(QUICK_BE_LESSON.interpretation)

    # 4. Compartmental examples match pk_models.py exact forward evaluations
    doc_1 = MODEL_DOCS["1. Tiêm tĩnh mạch nhanh (IV Bolus) — 1 Ngăn"]
    doc_2 = MODEL_DOCS["2. Tiêm tĩnh mạch nhanh (IV Bolus) — 2 Ngăn"]
    doc_5 = MODEL_DOCS["5. Truyền tĩnh mạch liên tục (IV Infusion) — 2 Ngăn"]
    doc_7 = MODEL_DOCS["7. Đường uống (Oral) — 1 Ngăn (Bateman)"]
    doc_9 = MODEL_DOCS["9. Đường uống (Oral) — 3 Ngăn"]
    assert "86" in doc_1.example
    assert "333" in doc_2.example
    assert "52" in doc_5.example and "333" in doc_5.example
    assert "T_{\\text{lag}} = 0" in PK_STANDALONE_LESSON.theory[1] or "Tlag = 0" in " ".join(PK_STANDALONE_LESSON.theory)
    assert "7,10" in doc_7.example or "7.10" in doc_7.example
    assert "12,5" in doc_9.example or "12.5" in doc_9.example


def test_contextual_diagnostics_and_expanders_adapt_to_workflow_options(tmp_path, monkeypatch):
    """Live workspace diagnostics and new expanders render cleanly without nested-expander errors."""
    import be_app.ui as ui

    monkeypatch.setattr(ui, "store", lambda: ProjectStore(tmp_path / "diag_adapt.sqlite"))
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=60).run()
    assert not app.exception

    # Full BE Step 0 renders examples / self-study / answer expanders cleanly without duplicate exercise
    expander_labels = [exp.label for exp in app.get("expander")]
    assert "Ví dụ minh họa & Kết quả kiểm chứng" in expander_labels
    assert "Gợi ý đáp án & Giải thích tự kiểm tra" in expander_labels
    assert "Chủ đề tự học chuyên sâu (Contextual Self-Study)" in expander_labels
    assert "Câu hỏi tự kiểm tra" not in expander_labels

    # Standalone PK reflects Tlag=0 for oral and switches guidance dynamically for IV bolus
    app.sidebar.radio[0].set_value("Phân tích PK độc lập").run()
    assert not app.exception
    captions_oral = " ".join(c.value for c in app.caption)
    assert "T_{\\text{lag}} = 0" in captions_oral
    assert "có $T_{\\text{lag}}$" not in captions_oral

    app.selectbox(key="pk_route").select_index(1).run()  # iv_bolus
    assert not app.exception
    captions_iv = " ".join(c.value for c in app.caption)
    assert "Tiêm TM nhanh ($F=1$)" in captions_iv

