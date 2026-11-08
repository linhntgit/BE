"""Regression cases for the concrete findings in the 2026-11-05 audit.

Fixtures are synthetic and isolated; none of these assertions qualify a PK/BE method.
"""

import hashlib
import io
import sqlite3
from contextlib import nullcontext
from dataclasses import asdict

import openpyxl
import pandas as pd
import pytest

from be_app.domain import BeConfig
from be_app.persistence import ProjectStore, export_archive, import_archive, restore_archive
from be_app.pk_analysis import PKSettings, analyze_nca
from be_app.pk_records import create_snapshot, excel_report
from be_app.pk_ui import _fingerprint, _render_snapshot
from be_app.quick_be import run_quick_be
from be_app.state import ProjectState
from be_app.statistics import analyze_abe
from be_app.ui import _review_table_cache_key


def _endpoint_table():
    rows = []
    for i, sequence in enumerate(("TR", "TR", "RT", "RT", "TR", "RT"), 1):
        for period, treatment in enumerate(sequence, 1):
            cmax = (18 + 1.1 * i + .3 * (period - 1)) * (1.07 if treatment == "T" else 1)
            rows.append({"Subject": f"{i:03d}", "Sequence": sequence, "Period": period,
                         "Treatment": treatment, "Cmax": cmax, "AUClast": cmax * (2.9 + .02 * i)})
    return pd.DataFrame(rows)


def _quick(frame, **options):
    return run_quick_be(frame.to_csv(index=False).encode("utf-8-sig"), "audit.csv",
                        mode=options.pop("mode", "endpoint"), **options)


def _profile(times, values, name="PK01"):
    return pd.DataFrame({"profile_id": [name] * len(times), "time_h": times,
                         "concentration": values, "blq": [False] * len(times)})


def test_a01_review_key_distinguishes_new_dataset_with_identical_decisions():
    first = _quick(_endpoint_table())
    changed = _endpoint_table()
    changed.loc[changed.Treatment.eq("T"), "Cmax"] *= 1.01
    second = _quick(changed)
    assert [r.decision for r in first.results] == [r.decision for r in second.results]
    assert first.provenance["settings_sha256"] == second.provenance["settings_sha256"]
    assert any(a.ci_lower != b.ci_lower for a, b in zip(first.results, second.results, strict=True))
    key1 = _review_table_cache_key([r.model_dump(mode="json") for r in first.results],
                                   first.provenance["settings_sha256"],
                                   first.endpoints, "2x2")
    key2 = _review_table_cache_key([r.model_dump(mode="json") for r in second.results],
                                   second.provenance["settings_sha256"],
                                   second.endpoints, "2x2")
    assert key1 != key2
    assert key1 == _review_table_cache_key([r.model_dump(mode="json") for r in first.results],
                                           first.provenance["settings_sha256"],
                                           first.endpoints.copy(), "2x2")


def test_a01_review_key_accepts_persisted_nca_rows_and_tracks_changed_pk():
    rows = [
        {"subject_id": "001", "sequence": "TR", "period": 1, "treatment": "T", "cmax": 12.123456789012345},
        {"subject_id": "001", "sequence": "TR", "period": 2, "treatment": "R", "cmax": 11.0},
    ]
    values = [{"endpoint": "cmax", "decision": "PASS"}]
    original = _review_table_cache_key(values, "persisted", rows, "2x2")
    assert original == _review_table_cache_key(values, "persisted", pd.DataFrame(rows), "2x2")
    changed = [dict(row) for row in rows]
    changed[0]["cmax"] += 1e-10
    assert original != _review_table_cache_key(values, "persisted", changed, "2x2")


@pytest.mark.parametrize("times,has_terminal", [
    ([0, 1, 2, 3, 4, 5], False),
    ([0, 2, 4, 6, 8, 10, 11, 12], False),
    ([0, 2, 4, 6, 8, 10, 11, 12, 13], True),
])
def test_a02_infusion_requires_three_post_infusion_elimination_samples(times, has_terminal):
    # Deliberately declining concentrations while infusion still runs.
    concentrations = [0] + [10 * .8 ** (t - 1) for t in times[1:]]
    settings = PKSettings(route="iv_infusion", infusion_duration_h=10, dose=100)
    result = analyze_nca(_profile(times, concentrations), settings)
    assert (result["lambda_z_h_inv"] is not None) == has_terminal
    assert (result["auc_0_inf"] is not None) == has_terminal
    assert (result["cl_l_h"] is not None) == has_terminal
    if has_terminal:
        assert min(result["terminal_times"]) > 10
    else:
        assert any("sau khi kết thúc truyền" in message for message in result["warnings"])
        assert result["auc_0_last"] is not None


def test_a03_archive_collision_forks_and_keeps_live_journal(demo, tmp_path):
    store = ProjectStore(tmp_path / "restore.sqlite")
    assert store.save(demo, 0) == 1
    old_archive = export_archive(demo)
    state = ProjectState(demo, store, db_revision=1)
    state.set_draft("study", "title", "Uncheckpointed journal value")
    original, base, working = store.checkout(demo.project_id)
    assert base == 1 and working == 1
    assert original.drafts["study"]["title"] == "Uncheckpointed journal value"

    restored, revision = restore_archive(store, old_archive)
    assert revision == 1 and restored.project_id != demo.project_id
    assert store.load(demo.project_id) == original
    assert store.load(restored.project_id) == restored
    assert restored.import_provenance["restored_from_project_id"] == demo.project_id
    assert restored.import_provenance["source_archive_sha256"] == hashlib.sha256(old_archive).hexdigest()


@pytest.mark.parametrize("options", [
    {"nti": True},
    {"be_config": BeConfig(alpha=.2)},
    {"be_config": BeConfig(lower=.5, upper=2.0)},
])
def test_a04_named_quick_be_rule_rejects_mismatched_scientific_config(options):
    with pytest.raises(ValueError, match="NTI|alpha"):
        _quick(_endpoint_table(), **options)


def test_a04_ci_criterion_reflects_actual_alpha():
    results = _quick(_endpoint_table())
    estimate = analyze_abe(results.endpoints, "cmax", "2x2", BeConfig(alpha=.2))
    assert estimate.criteria[0]["criterion"].startswith("CI 60%")


@pytest.mark.parametrize("tamper_revision", [1, 2])
def test_a05_journal_detects_missing_patch_after_bypassing_guard(demo, tmp_path, tamper_revision):
    store = ProjectStore(tmp_path / "journal.sqlite")
    store.save(demo, 0)
    state = ProjectState(demo, store, db_revision=1)
    state.set_draft("study", "title", "First edit")
    state.set_draft("study", "title", "Second edit")
    with store.connect() as db:
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            db.execute("UPDATE working_changes SET sha256='tamper'")
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            db.execute("DELETE FROM working_changes")
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            db.execute("UPDATE working_heads SET working_revision=99")
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            db.execute("DELETE FROM working_heads")
        # Test a corrupt external DB edit, bypassing only the deliberately local trigger.
        db.execute("DROP TRIGGER no_delete_working_changes")
        db.execute("DELETE FROM working_changes WHERE working_revision=?", (tamper_revision,))
    with pytest.raises(ValueError, match="Journal mất|Journal thiếu"):
        store.checkout(demo.project_id)


@pytest.mark.parametrize("missing_revision", [1, 2])
def test_a05_reopen_does_not_regenerate_missing_journal_heads(demo, tmp_path, missing_revision):
    path = tmp_path / "working-heads.sqlite"
    store = ProjectStore(path)
    store.save(demo, 0)
    state = ProjectState(demo, store, db_revision=1)
    state.set_draft("study", "title", "Edit 1")
    state.set_draft("study", "title", "Edit 2")
    with store.connect() as db:
        db.execute("DROP TRIGGER no_delete_working_heads")
        db.execute("DELETE FROM working_heads WHERE working_revision=?", (missing_revision,))
    reopened = ProjectStore(path)
    with pytest.raises(ValueError, match="Journal thiếu"):
        reopened.checkout(demo.project_id)


def test_a05_existing_legacy_journal_receives_one_time_head_migration(demo, tmp_path):
    path = tmp_path / "legacy.sqlite"
    store = ProjectStore(path)
    store.save(demo, 0)
    state = ProjectState(demo, store, db_revision=1)
    state.set_draft("study", "title", "Legacy edit")
    with store.connect() as db:
        db.execute("DROP TRIGGER no_delete_working_heads")
        db.execute("DELETE FROM working_heads")
        db.execute("DELETE FROM store_migrations WHERE name='working_heads_v1'")
    reopened = ProjectStore(path)
    project, base, working = reopened.checkout(demo.project_id)
    assert (base, working) == (1, 1)
    assert project.drafts["study"]["title"] == "Legacy edit"


@pytest.mark.parametrize("text_id", ["=1+1", "+SUM(1,1)", "-formula", "@custom"])
def test_a06_excel_escapes_untrusted_identifiers_in_all_sheets(text_id):
    frame = _profile([0, 1, 2, 4, 8, 12], [0, 10, 8, 5, 2, 1], text_id)
    cfg = PKSettings(route="oral", dose=100)
    snapshot = create_snapshot(frame, asdict(cfg), [analyze_nca(frame, cfg)], [],
                               [text_id], text_id)
    workbook = openpyxl.load_workbook(io.BytesIO(excel_report(snapshot)), data_only=False)
    for sheet_name, cell in (("Du_lieu", "A2"), ("NCA", "A2"), ("Canh_bao", "A2")):
        actual = workbook[sheet_name][cell]
        assert actual.data_type == "s"
        assert actual.value == "'" + text_id
    assert any(cell.value == "'" + text_id for row in workbook["Cau_hinh"] for cell in row)
    assert workbook["Du_lieu"]["C2"].data_type == "n"


def test_a07_highly_compressible_export_can_be_imported(demo):
    large = demo.record("draft", {"drafts": {"long_note": "A" * 3_000_000}},
                        "Stress test for archive round-trip")
    content = export_archive(large)
    assert import_archive(content) == large


def test_a08_fingerprint_preserves_small_float_changes_and_source_identity():
    cfg = PKSettings(route="oral", dose=100)
    a = _profile([0, 1, 2], [0, 1.00000000001, 1])
    b = a.copy()
    b.loc[1, "concentration"] = 1.00000000002
    one = _fingerprint(a, cfg, (1,), "equal", source="file A · SHA256 aa")
    assert one != _fingerprint(b, cfg, (1,), "equal", source="file A · SHA256 aa")
    assert one != _fingerprint(a, cfg, (1,), "equal", source="file B · SHA256 bb")
    assert one == _fingerprint(a.copy(), cfg, (1,), "equal", source="file A · SHA256 aa")


def test_a10_report_rendering_is_on_demand(monkeypatch):
    import be_app.pk_ui as pk_ui

    class FakeUI:
        session_state = {}
        prepared = None
        downloads = []

        def caption(self, _message):
            pass

        def tabs(self, _names):
            return nullcontext(), nullcontext(), nullcontext()

        def button(self, label, **_kwargs):
            return self.prepared == label

        def download_button(self, label, *_args, **_kwargs):
            self.downloads.append(label)

    ui = FakeUI()
    generated = []

    def export(_raw, kind):
        generated.append(kind)
        return b"fake-report"

    monkeypatch.setattr(pk_ui, "st", ui)
    monkeypatch.setattr(pk_ui, "_tabular", lambda _snapshot: None)
    monkeypatch.setattr(pk_ui, "_plot", lambda _snapshot, _key: None)
    monkeypatch.setattr(pk_ui, "_export", export)
    snapshot = {"source": "QA", "created_utc": "2026-11-05T00:00:00Z", "data": []}
    _render_snapshot(snapshot, "test")
    assert generated == []
    # Reports are prepared on demand; project state is saved via the ZIP control.
    assert ui.downloads == []
    ui.prepared = "Chuẩn bị WORD để tải"
    _render_snapshot(snapshot, "test")
    assert generated == ["word"]
    assert any("Word" in label for label in ui.downloads)


def test_a10_quick_excel_is_on_demand_and_bound_to_source(monkeypatch):
    import be_app.quick_be_ui as quick_ui

    class FakeUI:
        def __init__(self):
            self.session_state = {}
            self.prepare = False
            self.downloads = []

        def button(self, _label, **_kwargs):
            return self.prepare

        def download_button(self, _label, data, **_kwargs):
            self.downloads.append(data)

    ui = FakeUI()
    generated = []

    def export(value):
        generated.append(value)
        return value.encode()

    monkeypatch.setattr(quick_ui, "st", ui)
    monkeypatch.setattr(quick_ui, "quick_be_workbook", export)
    quick_ui._quick_excel_export("first", "hash-1")
    assert generated == ui.downloads == []

    ui.prepare = True
    quick_ui._quick_excel_export("first", "hash-1")
    assert generated == ["first"] and ui.downloads == [b"first"]

    ui.prepare = False
    quick_ui._quick_excel_export("first", "hash-1")
    assert generated == ["first"] and ui.downloads[-1] == b"first"
    ui.downloads.clear()
    quick_ui._quick_excel_export("second", "hash-2")
    assert generated == ["first"] and ui.downloads == []

    ui.prepare = True
    quick_ui._quick_excel_export("second", "hash-2")
    assert generated == ["first", "second"] and ui.downloads == [b"second"]


def test_a11_positive_blq_preserves_source_and_flags_adjustment():
    rows = []
    for pk in _endpoint_table().itertuples(index=False):
        for time, fraction in ((0, 0), (1, .65), (2, 1), (4, .75), (8, .35),
                               (12, .16), (18, .05)):
            rows.append({"Subject": pk.Subject, "Sequence": pk.Sequence,
                         "Period": pk.Period, "Treatment": pk.Treatment,
                         "Time": time, "Cplasma": pk.Cmax * fraction,
                         "BLQ": "true" if pk.Subject == "001" and time == 18 else "false"})
    original = pd.DataFrame(rows)
    result = _quick(original, mode="concentration")
    handling = result.provenance["blq_handling"]
    assert handling["positive_flagged_count"] == 2
    assert handling["raw_values_preserved"] is True
    assert all(sample["concentration"] > 0 for sample in handling["positive_flagged_samples"])
    assert any("BLQ" in warning and "LLOQ" in warning for warning in result.warnings)
    assert result.raw.loc[result.raw.Subject.eq("001") & result.raw.Time.eq(18), "Cplasma"].gt(0).all()
