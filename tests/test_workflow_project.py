"""Project ZIP integrity and workflow isolation regressions."""

import io
import json
import zipfile

import pytest

from be_app.workflow_project import (
    PROJECT_SUFFIXES,
    export_workflow_project,
    import_workflow_project,
    validate_project_filename,
)


@pytest.mark.parametrize("workflow", ["independent_pk", "quick_be", "full_be"])
def test_project_filename_must_match_workflow(workflow):
    suffix = PROJECT_SUFFIXES[workflow]
    assert validate_project_filename(f"study{suffix}", workflow) is None
    assert validate_project_filename(f"STUDY{suffix.upper()}", workflow) is None

    invalid_names = [
        "study.zip", "study.project.zip", suffix, "", None,
        f"folder/study{suffix}", f"folder\\study{suffix}",
        f"study{suffix}.json",
        *(f"study{other}" for key, other in PROJECT_SUFFIXES.items() if key != workflow),
    ]
    for name in invalid_names:
        with pytest.raises(ValueError, match="đuôi"):
            validate_project_filename(name, workflow)


def test_project_filename_rejects_unknown_workflow():
    with pytest.raises(ValueError, match="không được hỗ trợ"):
        validate_project_filename("study.pk.zip", "unknown")


@pytest.mark.parametrize("workflow", ["quick_be", "independent_pk"])
def test_workflow_project_round_trip(workflow):
    payload = {"format_version": 1, "data": [{"profile": "Mẫu 01", "value": 1.5}],
               "widgets": {"choice": "vi"}}
    content = export_workflow_project(workflow, payload)
    assert import_workflow_project(content, workflow) == payload
    with pytest.raises(ValueError, match="luồng"):
        import_workflow_project(content, "independent_pk" if workflow == "quick_be" else "quick_be")


def test_rejects_corruption_and_unexpected_zip_members():
    content = export_workflow_project("quick_be", {"data": [1]})
    with pytest.raises(ValueError):
        import_workflow_project(b"corrupt", "quick_be")
    with zipfile.ZipFile(io.BytesIO(content)) as source:
        manifest = source.read("manifest.json")
        project = source.read("project.json")
    altered = io.BytesIO()
    with zipfile.ZipFile(altered, "w") as dest:
        dest.writestr("manifest.json", manifest)
        dest.writestr("project.json", project.replace(b"1", b"2"))
    with pytest.raises(ValueError, match="Checksum"):
        import_workflow_project(altered.getvalue(), "quick_be")
    with zipfile.ZipFile(altered, "a") as dest:
        dest.writestr("../intruder", "unwanted")
    with pytest.raises(ValueError, match="đúng"):
        import_workflow_project(altered.getvalue(), "quick_be")


def test_rejects_unknown_format_version():
    content = export_workflow_project("quick_be", {})
    with zipfile.ZipFile(io.BytesIO(content)) as source:
        manifest = json.loads(source.read("manifest.json"))
    manifest["version"] = 999
    mutated = io.BytesIO()
    with zipfile.ZipFile(mutated, "w") as dest:
        dest.writestr("manifest.json", json.dumps(manifest))
        dest.writestr("project.json", "{}")
    with pytest.raises(ValueError, match="phiên bản"):
        import_workflow_project(mutated.getvalue(), "quick_be")
