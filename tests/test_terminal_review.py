"""Per-profile slope changes preserve data identity, stale gates, audit and unaffected cache."""

import json

import pytest

from be_app.domain import NcaConfig, TerminalOverride, canonical
from be_app.nca import (
    PROFILE_KEYS,
    effective_nca_config,
    profile_data_hash,
    profile_identity,
    terminal_eligible_times,
)
from be_app.persistence import export_archive, import_archive, load_project_payload
from be_app.state import ProjectState, pending_config, result_status


def make_override(group, **updates):
    return TerminalOverride(
        **{
            **profile_identity(group),
            "times": tuple(terminal_eligible_times(group)[-3:]),
            "reason": "Reviewed terminal phase",
            "reviewer": "PK reviewer",
            "profile_data_hash": profile_data_hash(group),
            **updates,
        }
    )


def test_one_override_recomputes_only_one_profile_and_survives_archive(small_demo):
    state = ProjectState(small_demo)
    state.freeze()
    state.analyze()
    count = len(state.project.runs[-1]["nca"])
    group = next(iter(state.qc().data.groupby(list(PROFILE_KEYS))))[1]
    override = make_override(group)
    config = NcaConfig.model_validate(
        {**state.project.nca_config.model_dump(), "terminal_overrides": [override]}
    )
    old_run = state.project.runs[-1]
    state.commit(state.project.revise("Reviewed phase selection", nca_config=config))
    assert result_status(state.project) == "STALE"
    state.freeze()
    state.analyze()
    run = state.project.runs[-1]
    assert run["computation"] == {"nca_profiles_computed": 1, "nca_profiles_reused": count - 1}
    selected = [row for row in run["nca"] if row.get("terminal_review")]
    assert len(selected) == 1 and selected[0]["terminal_review"]["reviewer"] == "PK reviewer"
    assert selected[0]["terminal_selected"]["times"] == list(override.times)
    assert state.project.runs[-2] == old_run
    restored = import_archive(export_archive(state.project))
    assert restored.nca_config.terminal_overrides == (override,)
    assert restored.runs[-1] == run


def test_stale_slope_selection_blocks_freeze_and_cannot_silently_follow_changed_data(small_demo):
    state = ProjectState(small_demo)
    group = next(iter(state.qc().data.groupby(list(PROFILE_KEYS))))[1]
    override = make_override(group, profile_data_hash="0" * 64)
    config = NcaConfig.model_validate(
        {**state.project.nca_config.model_dump(), "terminal_overrides": [override]}
    )
    state.commit(
        state.project.record(
            "terminal_review", {"nca_config": config.model_dump(mode="json")}, "Review phase"
        )
    )
    with pytest.raises(ValueError, match="Dữ liệu profile đã đổi"):
        state.freeze()
    with pytest.raises(ValueError, match="Dữ liệu profile đã đổi"):
        state.project.freeze()
    changed = group.copy()
    valid = make_override(group)
    changed.loc[changed.index[-1], "concentration"] *= 1.01
    config = config.model_copy(update={"terminal_overrides": (valid,)})
    with pytest.raises(ValueError, match="Dữ liệu profile đã đổi"):
        effective_nca_config(config, changed)


def test_slope_drafts_survive_archive_and_block_results(small_demo):
    state = ProjectState(small_demo)
    group = next(iter(state.qc().data.groupby(list(PROFILE_KEYS))))[1]
    section = "terminal:" + json.dumps(profile_identity(group), sort_keys=True)
    state.set_draft(section, "mode", "manual")
    state.set_draft(section, "times", terminal_eligible_times(group)[-3:])
    assert state.pending_config()
    restored = import_archive(export_archive(state.project))
    assert pending_config(restored)
    with pytest.raises(ValueError, match="Chưa áp dụng"):
        state.freeze()


def test_schema2_existing_freeze_hash_remains_valid_without_new_field(small_demo):
    frozen = small_demo.freeze()
    payload = frozen.model_dump(mode="json")
    payload["nca_config"].pop("terminal_overrides")
    restored = load_project_payload(canonical(payload))
    assert restored.freeze_hash == frozen.freeze_hash == restored.input_hash()
    assert restored.nca_config.terminal_overrides == ()


def test_override_requires_reviewer_and_valid_unique_profile(small_demo):
    group = next(iter(small_demo.qc().data.groupby(list(PROFILE_KEYS))))[1]
    override = make_override(group)
    for updates in (
        {"reviewer": " "},
        {"reason": " " * 6},
        {"times": (1, 1, 2)},
        {"times": (1, float("nan"), 2)},
    ):
        with pytest.raises(ValueError):
            make_override(group, **updates)
    with pytest.raises(ValueError, match="Mỗi profile"):
        NcaConfig(terminal_overrides=(override, override))
    missing = override.model_copy(update={"subject_id": "absent"})
    configured = small_demo.record(
        "configure",
        {"nca_config": NcaConfig(terminal_overrides=(missing,)).model_dump(mode="json")},
        "Review phase",
    )
    with pytest.raises(ValueError, match="không còn có"):
        configured.freeze()
