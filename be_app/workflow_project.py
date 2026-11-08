"""Portable, validated ZIP projects for standalone analysis workflows."""

from __future__ import annotations

import hashlib
import io
import json
import stat
import zipfile
import zlib


MAX_ZIP_BYTES = 30_000_000
MAX_JSON_BYTES = 50_000_000
WORKFLOWS = {"quick_be", "independent_pk"}
PROJECT_SUFFIXES = {
    "independent_pk": ".pk.zip",
    "quick_be": ".be.zip",
    "full_be": ".bewf.zip",
}


def validate_project_filename(filename: str, workflow: str) -> None:
    """Reject files named for another analysis workflow before reading the ZIP."""
    suffix = PROJECT_SUFFIXES.get(workflow)
    if suffix is None:
        raise ValueError("Loại project không được hỗ trợ.")
    if (not isinstance(filename, str) or len(filename) <= len(suffix)
            or not filename.lower().endswith(suffix)
            or "/" in filename or "\\" in filename):
        raise ValueError(f"File project của luồng này phải có đuôi {suffix}.")


def _json_bytes(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      allow_nan=False, separators=(",", ":")).encode("utf-8")


def export_workflow_project(workflow: str, payload: dict) -> bytes:
    if workflow not in WORKFLOWS or not isinstance(payload, dict):
        raise ValueError("Loại project không được hỗ trợ.")
    content = _json_bytes(payload)
    if len(content) > MAX_JSON_BYTES:
        raise ValueError("Dữ liệu project vượt giới hạn 50 MB.")
    manifest = _json_bytes({"format": "be_app_workflow_project", "version": 1,
                            "workflow": workflow, "payload_sha256": hashlib.sha256(content).hexdigest()})
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", manifest)
        # Highly repetitive datasets should remain importable under the zip-bomb guard.
        compression = (zipfile.ZIP_STORED if len(content) > 2_000_000 and
                       len(content) / max(len(zlib.compress(content)), 1) > 500
                       else zipfile.ZIP_DEFLATED)
        archive.writestr("project.json", content, compress_type=compression)
    if buffer.tell() > MAX_ZIP_BYTES:
        raise ValueError("Project ZIP vượt giới hạn 30 MB.")
    return buffer.getvalue()


def import_workflow_project(raw: bytes, expected_workflow: str) -> dict:
    if expected_workflow not in WORKFLOWS:
        raise ValueError("Loại project không được hỗ trợ.")
    if len(raw) > MAX_ZIP_BYTES:
        raise ValueError("Project ZIP vượt giới hạn 30 MB.")
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            infos = archive.infolist()
            if len(infos) != 2 or {item.filename for item in infos} != {"manifest.json", "project.json"}:
                raise ValueError("Project ZIP phải có đúng manifest.json và project.json.")
            if sum(item.file_size for item in infos) > MAX_JSON_BYTES + 4096:
                raise ValueError("Dữ liệu giải nén vượt giới hạn.")
            for item in infos:
                if (item.flag_bits & 1 or item.is_dir() or stat.S_ISLNK(item.external_attr >> 16)
                        or item.file_size > MAX_JSON_BYTES or
                        (item.file_size > 2_000_000 and
                         item.file_size / max(item.compress_size, 1) > 500)):
                    raise ValueError("Project ZIP chứa mục không an toàn.")
            manifest = json.loads(archive.read("manifest.json"))
            content = archive.read("project.json")
            if (not isinstance(manifest, dict) or manifest.get("format") != "be_app_workflow_project"
                    or type(manifest.get("version")) is not int or manifest["version"] != 1
                    or manifest.get("workflow") != expected_workflow):
                raise ValueError("Sai định dạng, phiên bản hoặc luồng phân tích của project.")
            if hashlib.sha256(content).hexdigest() != manifest.get("payload_sha256"):
                raise ValueError("Checksum SHA-256 của project không khớp.")
            payload = json.loads(content)
            if not isinstance(payload, dict):
                raise ValueError("Nội dung project phải là một đối tượng JSON.")
            return payload
    except (zipfile.BadZipFile, UnicodeError, json.JSONDecodeError, EOFError, RuntimeError) as exc:
        raise ValueError("Không đọc được project ZIP hợp lệ.") from exc
