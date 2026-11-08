"""Append-only SQLite snapshots and bounded, checksum-verified project archives."""

import base64
import hashlib
import io
import json
import sqlite3
import stat
import zipfile
import zlib
from pathlib import Path, PurePosixPath
from typing import Any
from uuid import uuid4

from pydantic import Field, TypeAdapter

from be_app import __version__
from be_app.domain import BeConfig, NcaConfig, StrictModel, Study, canonical, digest, utc_now
from be_app.imports import apply_corrections, parse_file, validate_data

SCHEMA_VERSION = 2
MAX_ARCHIVE = 30_000_000
MAX_UNCOMPRESSED = 150_000_000


class Project(StrictModel):
    schema_version: int = SCHEMA_VERSION
    project_id: str = Field(default_factory=lambda: str(uuid4()))
    study: Study
    nca_config: NcaConfig = Field(default_factory=NcaConfig)
    be_config: BeConfig = Field(default_factory=BeConfig)
    allocation: list[dict] = Field(default_factory=list)
    allocation_metadata: dict = Field(default_factory=dict)
    raw_file_name: str = ""
    raw_base64: str = ""
    raw_history: list[dict] = Field(default_factory=list)
    column_mapping: dict[str, str] = Field(default_factory=dict)
    allow_unit_conversion: bool = False
    corrections: list[dict] = Field(default_factory=list)
    freeze_hash: str = ""
    runs: list[dict] = Field(default_factory=list)
    snapshot_reviews: list[dict] = Field(default_factory=list)
    events: list[dict] = Field(default_factory=list)
    artifacts: dict[str, str] = Field(default_factory=dict)
    artifact_manifests: dict[str, dict] = Field(default_factory=dict)
    input_revision: int = Field(default=0, ge=0)
    dataset_revision: int = Field(default=0, ge=0)
    config_revision: int = Field(default=0, ge=0)
    nca_config_revision: int = Field(default=0, ge=0)
    be_config_revision: int = Field(default=0, ge=0)
    input_fingerprint: str = ""
    planning_inputs: dict = Field(default_factory=dict)
    preferences: dict = Field(default_factory=dict)
    drafts: dict = Field(default_factory=dict)
    pending_edits: dict[str, dict[str, str]] = Field(default_factory=dict)
    import_provenance: dict = Field(default_factory=dict)

    def record(self, action: str, updates: dict, reason: str, actor: str | None = None):
        if not reason.strip():
            raise ValueError("Thay đổi cần lý do.")
        # Validate only changed fields; immutable existing datasets/runs are shared, never dumped on a light edit.
        validated = {
            key: TypeAdapter(type(self).model_fields[key].annotation or Any).validate_python(value)
            for key, value in updates.items()
        }
        dataset_fields = {
            "allocation",
            "raw_base64",
            "column_mapping",
            "allow_unit_conversion",
            "corrections",
        }
        dataset_changed = bool(dataset_fields & updates.keys())
        config_changed = bool({"study", "nca_config", "be_config"} & updates.keys())
        if self.freeze_hash and (dataset_changed or config_changed) and action != "new_revision":
            raise ValueError("Đã khóa đầu vào; tạo revision mới trước khi thay đổi.")
        revisions = {}
        if dataset_changed or config_changed:
            revisions = dict(
                input_revision=self.input_revision + 1,
                dataset_revision=self.dataset_revision + int(dataset_changed),
                config_revision=self.config_revision + int(config_changed),
                nca_config_revision=self.nca_config_revision + int("nca_config" in updates),
                be_config_revision=self.be_config_revision + int("be_config" in updates),
            )
        before = dict(
            project_id=self.project_id,
            previous=self.events[-1]["hash"] if self.events else "",
            input_revision=self.input_revision,
            input_fingerprint=self.input_fingerprint,
        )
        event = dict(
            timestamp=utc_now(),
            actor=actor or self.study.operator,
            action=action,
            reason=reason,
            before=digest(before),
            changed_fields=sorted(updates),
            after_values_hash=digest(updates),
            previous=self.events[-1]["hash"] if self.events else "",
        )
        event["hash"] = digest(event)
        updated = self.model_copy(update={**validated, **revisions, "events": [*self.events, event]})
        if revisions:
            updated = updated.model_copy(update={"input_fingerprint": updated.input_hash()})
        return updated

    def require_editable(self):
        if self.freeze_hash:
            raise ValueError("Đã khóa dữ liệu/phương pháp; cần tạo revision mới.")

    def with_allocation(self, rows: list[dict], metadata: dict):
        self.require_editable()
        if self.raw_base64:
            raise ValueError("Đã nhập dữ liệu; tạo revision mới trước khi đổi phân nhóm.")
        return self.record(
            "randomize", {"allocation": rows, "allocation_metadata": metadata}, "Lập phân nhóm"
        )

    def import_raw(self, content: bytes, name: str, mapping=None, convert_units=False):
        self.require_editable()
        if self.raw_base64:
            raise ValueError("Raw bất biến; tạo revision riêng để nhập lại.")
        from be_app.import_review import review_import

        review = review_import(
            content, name, json.dumps(mapping or {}, ensure_ascii=False),
            self.study, self.allocation, convert_units,
        )
        if not review.ready:
            details = review.error or "; ".join(
                f"{flag.code} (dòng {flag.row or '-'}, {flag.column})"
                for flag in (review.qc.flags if review.qc else [])
                if flag.severity == "ERROR"
            )
            raise ValueError("File nồng độ chưa đạt kiểm tra trước nhập: " + details[:500])
        return self.record(
            "import",
            {
                "raw_base64": base64.b64encode(content).decode("ascii"),
                "raw_file_name": Path(name).name,
                "column_mapping": mapping or {},
                "allow_unit_conversion": convert_units,
                "import_provenance": dict(
                    source_file=Path(name).name,
                    imported_at=utc_now(),
                    sha256=hashlib.sha256(content).hexdigest(),
                ),
            },
            "Nhập raw bất biến",
        )

    def raw_frame(self):
        if not self.raw_base64:
            raise ValueError("Chưa có dữ liệu raw.")
        return parse_file(
            base64.b64decode(self.raw_base64, validate=True), self.raw_file_name, self.column_mapping
        )

    def clean_frame(self):
        return apply_corrections(self.raw_frame(), self.corrections)

    def qc(self):
        import pandas as pd

        return validate_data(
            self.clean_frame(), self.study, pd.DataFrame(self.allocation), self.allow_unit_conversion
        )

    def corrected(self, change: dict):
        self.require_editable()
        apply_corrections(self.clean_frame(), [change])
        return self.record(
            "correction", {"corrections": [*self.corrections, change]}, change["reason"], change["actor"]
        )

    def input_hash(self):
        return digest(
            dict(
                study=self.study.model_dump(mode="json", exclude={
                    field for field in ("scope_record", "protocol_details") if not getattr(self.study, field)
                }),
                # Preserve pre-override schema-2 fingerprints for an empty new field.
                nca=self.nca_config.model_dump(
                    mode="json",
                    exclude={"terminal_overrides"} if not self.nca_config.terminal_overrides else set(),
                ),
                be=self.be_config.model_dump(mode="json"),
                allocation=self.allocation,
                raw_sha256=hashlib.sha256(base64.b64decode(self.raw_base64)).hexdigest(),
                corrections=self.corrections,
                mapping=self.column_mapping,
                convert_units=self.allow_unit_conversion,
            )
        )

    def freeze(self):
        self.require_editable()
        self.check_freeze_evidence()
        if self.pending_edits:
            raise ValueError("Có chỉnh sửa Chưa áp dụng; áp dụng hoặc hủy có chủ đích trước khi khóa.")
        qc = self.qc()
        if not qc.valid:
            raise ValueError("QC có lỗi chặn; không thể Data Freeze.")
        if self.nca_config.terminal_overrides:
            from be_app.nca import validate_terminal_overrides

            validate_terminal_overrides(self.nca_config, qc.data)
        return self.record(
            "freeze", {"freeze_hash": self.input_hash()}, "Khóa dữ liệu, scope và SAP trước phân tích"
        )

    def check_freeze_evidence(self):
        """Check the workbench's documentation requirements before locking a real study."""
        if self.study.is_demo or self.study.data_purpose != "regulated_study":
            return
        from be_app.regulations import scope_blockers

        missing = scope_blockers(self.study)
        for field, label in (("reference_market", "thị trường đối chứng"),
                             ("guidance", "nguồn và phiên bản hướng dẫn"), ("applicability", "căn cứ áp dụng")):
            if not self.study.scope_record.get(field, "").strip():
                missing.append(label)
        for field, label in (("bioanalysis", "bằng chứng định lượng"), ("statistics", "quần thể và quy tắc SAP"),
                             ("sampling", "kế hoạch lấy mẫu")):
            if not self.study.protocol_details.get(field, "").strip():
                missing.append(label)
        if missing:
            raise ValueError("Trước khi khóa nghiên cứu thật, bổ sung ở chặng 1–2: " + ", ".join(missing))

    def revise(
        self,
        reason: str,
        study: Study | None = None,
        nca_config: NcaConfig | None = None,
        be_config: BeConfig | None = None,
        replace_raw: bool = False,
    ):
        updates: dict = {"freeze_hash": ""}
        for key, value in (("study", study), ("nca_config", nca_config), ("be_config", be_config)):
            if value is not None and value != getattr(self, key):
                updates[key] = value.model_dump(mode="json")
        if study is not None and study.design != self.study.design and self.allocation:
            raise ValueError(
                "Không thể đổi thiết kế khi đã có phân nhóm/dữ liệu; tạo dự án riêng, giữ nguyên dự án này."
            )
        # Validate nested models rather than leaving dicts through model_copy.
        if replace_raw:
            if self.pending_edits:
                raise ValueError(
                    "Còn chỉnh sửa mẫu Chưa áp dụng; áp dụng hoặc hủy có chủ đích trước khi thay raw."
                )
            updates.update(
                raw_file_name="",
                raw_base64="",
                corrections=[],
                raw_history=[
                    *self.raw_history,
                    dict(
                        raw_file_name=self.raw_file_name,
                        raw_base64=self.raw_base64,
                        corrections=self.corrections,
                        column_mapping=self.column_mapping,
                    ),
                ],
            )
        return self.record("new_revision", updates, reason)

    def review_for(self, run):
        if not run:
            return None
        return next((entry for entry in reversed(self.snapshot_reviews)
                     if entry["analysis_run_id"] == run["analysis_run_id"]
                     and entry["snapshot_hash"] == run["snapshot_hash"]), None)

    def for_other_market(self, target_rule, justification):
        from be_app.regulations import RULES
        from be_app.state import pending_config

        target = RULES[target_rule]
        if (target.jurisdiction == RULES[self.study.rule_set_id].jurisdiction
            or self.study.design not in target.designs or self.study.nti != target_rule.endswith("_NTI")):
            raise ValueError("Chọn quy tắc của thị trường thứ hai tương thích với thiết kế.")
        if self.pending_edits or pending_config(self) or not justification.strip():
            raise ValueError("Cần xử lý bản sửa đang chờ và ghi căn cứ dùng chung dữ liệu.")
        study = self.study.model_copy(update={
            "rule_set_id": target_rule, "scope_reviewed": False, "scope_record": {},
            "scope_evidence": "", "sap": "", "protocol_details": {}, "scaled_be_prespecified": False,
            "nti_cmax_narrow": False, "hvd_justification": "",
        })
        origin = {**self.import_provenance, "source_project_id": self.project_id,
                  "source_input_hash": self.input_hash(), "shared_data_rationale": justification.strip()}
        project = Project(study=study)
        return project.record("market_project", {
            "allocation": self.allocation, "allocation_metadata": {
                k: v for k, v in self.allocation_metadata.items() if k != "sample_size_plan"},
            "raw_base64": self.raw_base64, "raw_file_name": self.raw_file_name,
            "column_mapping": self.column_mapping, "allow_unit_conversion": self.allow_unit_conversion,
            "corrections": self.corrections, "import_provenance": origin,
        }, justification)

    def record_review(self, snapshot_hash, reviewer, evidence, outcome):
        from be_app.state import result_status

        run = self.runs[-1] if self.runs else None
        if not run or run["snapshot_hash"] != snapshot_hash or result_status(self, run) != "CURRENT":
            raise ValueError("Cần rà soát bản kết quả hiện hành.")
        reviewer, evidence = reviewer.strip(), evidence.strip()
        if not reviewer or reviewer.casefold() == run["operator"].strip().casefold():
            raise ValueError("Cần định danh người rà soát khác người phân tích.")
        if not evidence or outcome not in ("reviewed", "follow_up"):
            raise ValueError("Cần ghi nhận bằng chứng và kết quả rà soát.")
        entry = dict(analysis_run_id=run["analysis_run_id"], snapshot_hash=snapshot_hash,
                     reviewer=reviewer, evidence=evidence, outcome=outcome, timestamp=utc_now())
        return self.record("snapshot_review", {"snapshot_reviews": [*self.snapshot_reviews, entry]},
                           "Ghi nhận rà soát bản kết quả", reviewer)

    def attach_artifact(self, name: str, content: bytes):
        if not self.runs:
            raise ValueError("Cần analysis snapshot trước khi lưu báo cáo.")
        if name in self.artifacts:
            raise ValueError("Artifact bất biến; dùng tên phiên bản mới.")
        from be_app.state import report_manifest

        manifest = report_manifest(self, self.runs[-1])
        return self.record(
            "report",
            {
                "artifacts": {**self.artifacts, name: base64.b64encode(content).decode()},
                "artifact_manifests": {**self.artifact_manifests, name: manifest},
            },
            "Lưu bản báo cáo dự thảo",
        )


def verify_project(project: Project):
    if project.schema_version != SCHEMA_VERSION:
        raise ValueError("Schema chưa hỗ trợ; cần migration có kiểm soát.")
    previous = ""
    for event in project.events:
        unsigned = {k: v for k, v in event.items() if k != "hash"}
        if event.get("previous") != previous or event.get("hash") != digest(unsigned):
            raise ValueError("Chuỗi audit bị thay đổi hoặc thiếu sự kiện.")
        previous = event["hash"]
    if project.freeze_hash and project.freeze_hash != project.input_hash():
        raise ValueError("Input đã thay đổi sau Data Freeze.")
    if project.input_fingerprint and project.input_fingerprint != project.input_hash():
        raise ValueError("Fingerprint đầu vào không khớp domain state.")
    for run in project.runs:
        if run.get("snapshot_hash") != digest({k: v for k, v in run.items() if k != "snapshot_hash"}):
            raise ValueError("Analysis snapshot sai hash.")


def load_project_payload(payload: bytes | str) -> Project:
    data = json.loads(payload)
    if data.get("schema_version") == 1:
        data["schema_version"] = SCHEMA_VERSION
        project = Project.model_validate(data)
        project = project.model_copy(update={"input_fingerprint": project.input_hash()})
        # Legacy results remain unchanged and are explicitly not treated as revision-tagged results.
    else:
        project = Project.model_validate(data)
    verify_project(project)
    return project


def export_archive(project: Project) -> bytes:
    verify_project(project)
    content = canonical(project.model_dump(mode="json"))
    manifest = dict(
        schema_version=SCHEMA_VERSION,
        engine_version=__version__,
        status="DRAFT / NOT REGULATORY-READY",
        project_id=project.project_id,
        input_revision=project.input_revision,
        dataset_revision=project.dataset_revision,
        config_revision=project.config_revision,
        input_fingerprint=project.input_fingerprint,
        files={"project.json": hashlib.sha256(content).hexdigest()},
    )
    output = io.BytesIO()
    parts = [("manifest.json", canonical(manifest)), ("project.json", content)]
    if sum(len(payload) for _, payload in parts) > MAX_UNCOMPRESSED:
        raise ValueError("Archive vượt giới hạn giải nén.")
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, payload in parts:
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            # Preserve import's zip-bomb guard, even for highly compressible valid drafts.
            high_ratio = len(payload) > 2_000_000 and len(payload) / max(len(zlib.compress(payload)), 1) > 500
            info.compress_type = zipfile.ZIP_STORED if high_ratio else zipfile.ZIP_DEFLATED
            archive.writestr(info, payload)
    if len(output.getvalue()) > MAX_ARCHIVE or len(content) > MAX_UNCOMPRESSED:
        raise ValueError("Dự án vượt giới hạn lưu trữ của bản local.")
    return output.getvalue()


def import_archive(content: bytes) -> Project:
    if len(content) > MAX_ARCHIVE:
        raise ValueError("Archive vượt 30 MB.")
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            infos = archive.infolist()
            if len(infos) != 2 or {i.filename for i in infos} != {"manifest.json", "project.json"}:
                raise ValueError("Archive cần đúng manifest.json và project.json; file lạ bị từ chối.")
            if sum(i.file_size for i in infos) > MAX_UNCOMPRESSED:
                raise ValueError("Archive vượt giới hạn giải nén.")
            for info in infos:
                p = PurePosixPath(info.filename)
                if p.is_absolute() or ".." in p.parts or "\\" in info.filename or info.flag_bits & 1:
                    raise ValueError("Archive chứa path/file không an toàn.")
                if stat.S_ISLNK(info.external_attr >> 16):
                    raise ValueError("Không chấp nhận symlink.")
                if info.file_size > 2_000_000 and info.file_size / max(info.compress_size, 1) > 500:
                    raise ValueError("Tỷ lệ nén bất thường.")
            manifest = json.loads(archive.read("manifest.json"))
            payload = archive.read("project.json")
            if manifest.get("schema_version") not in (1, SCHEMA_VERSION):
                raise ValueError("Schema archive chưa hỗ trợ.")
            if manifest.get("files") != {"project.json": hashlib.sha256(payload).hexdigest()}:
                raise ValueError("Checksum archive không khớp.")
            return load_project_payload(payload)
    except (zipfile.BadZipFile, KeyError, json.JSONDecodeError, RecursionError) as exc:
        raise ValueError("Archive không hợp lệ.") from exc


class ProjectStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
                BEGIN IMMEDIATE;
                CREATE TABLE IF NOT EXISTS snapshots (
                    project_id TEXT NOT NULL, revision INTEGER NOT NULL, study_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL, payload BLOB NOT NULL, sha256 TEXT NOT NULL,
                    PRIMARY KEY (project_id, revision));
                CREATE TRIGGER IF NOT EXISTS no_update BEFORE UPDATE ON snapshots
                    BEGIN SELECT RAISE(ABORT, 'immutable snapshot'); END;
                CREATE TRIGGER IF NOT EXISTS no_delete BEFORE DELETE ON snapshots
                    BEGIN SELECT RAISE(ABORT, 'immutable snapshot'); END;
                CREATE TABLE IF NOT EXISTS working_changes (
                    project_id TEXT NOT NULL, base_revision INTEGER NOT NULL,
                    working_revision INTEGER NOT NULL, payload BLOB NOT NULL, sha256 TEXT NOT NULL,
                    PRIMARY KEY (project_id, base_revision, working_revision));
                CREATE TRIGGER IF NOT EXISTS no_update_working_changes BEFORE UPDATE ON working_changes
                    BEGIN SELECT RAISE(ABORT, 'immutable journal'); END;
                CREATE TRIGGER IF NOT EXISTS no_delete_working_changes BEFORE DELETE ON working_changes
                    BEGIN SELECT RAISE(ABORT, 'immutable journal'); END;
                CREATE TABLE IF NOT EXISTS working_heads (
                    project_id TEXT NOT NULL, base_revision INTEGER NOT NULL,
                    working_revision INTEGER NOT NULL,
                    PRIMARY KEY (project_id, base_revision, working_revision));
                CREATE TRIGGER IF NOT EXISTS no_update_working_heads BEFORE UPDATE ON working_heads
                    BEGIN SELECT RAISE(ABORT, 'immutable journal head'); END;
                CREATE TRIGGER IF NOT EXISTS no_delete_working_heads BEFORE DELETE ON working_heads
                    BEGIN SELECT RAISE(ABORT, 'immutable journal head'); END;
                CREATE TABLE IF NOT EXISTS store_migrations (
                    name TEXT PRIMARY KEY);
                CREATE TABLE IF NOT EXISTS navigation (
                    project_id TEXT PRIMARY KEY, page TEXT NOT NULL);
                -- Once migrated, never reconstruct missing heads on a later reopen.
                INSERT OR IGNORE INTO working_heads
                    SELECT project_id, base_revision, working_revision FROM working_changes
                    WHERE NOT EXISTS (
                        SELECT 1 FROM store_migrations WHERE name='working_heads_v1');
                INSERT OR IGNORE INTO store_migrations (name) VALUES ('working_heads_v1');
                COMMIT;
            """)

    def connect(self):
        return sqlite3.connect(self.path, timeout=10)

    def last_page(self, project_id):
        with self.connect() as db:
            row = db.execute("SELECT page FROM navigation WHERE project_id=?", (project_id,)).fetchone()
        return row[0] if row else None

    def remember_page(self, project_id, page):
        with self.connect() as db:
            db.execute("INSERT OR REPLACE INTO navigation VALUES (?,?)", (project_id, page))

    @staticmethod
    def _verified_working_head(db, project_id: str, base_revision: int) -> int:
        """Ensure recorded journal revisions are contiguous, including the persisted heads."""
        def stats(table):
            query = {
                "working_changes": "SELECT COUNT(*), MIN(working_revision), MAX(working_revision) "
                                   "FROM working_changes WHERE project_id=? AND base_revision=?",
                "working_heads": "SELECT COUNT(*), MIN(working_revision), MAX(working_revision) "
                                 "FROM working_heads WHERE project_id=? AND base_revision=?",
            }[table]
            return db.execute(
                query,
                (project_id, base_revision),
            ).fetchone()

        changes_count, changes_first, changes_last = stats("working_changes")
        heads_count, heads_first, heads_last = stats("working_heads")
        changes_last = changes_last or 0
        heads_last = heads_last or 0
        if (
            changes_count != changes_last or (changes_count and changes_first != 1)
            or heads_count != heads_last or (heads_count and heads_first != 1)
            or changes_last != heads_last
        ):
            raise ValueError("Journal thiếu bản ghi so với lịch sử revision.")
        return int(changes_last)

    def save(
        self,
        project: Project,
        expected_revision: int | None = None,
        expected_working_revision: int | None = None,
    ) -> int:
        verify_project(project)
        payload = canonical(project.model_dump(mode="json"))
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            previous = (
                db.execute(
                    "SELECT MAX(revision) FROM snapshots WHERE project_id=?", (project.project_id,)
                ).fetchone()[0]
                or 0
            )
            if expected_revision is not None and previous != expected_revision:
                raise ValueError("Dự án đã có revision mới; tải lại trước khi ghi.")
            head = self._verified_working_head(db, project.project_id, previous)
            if expected_working_revision is not None and head != expected_working_revision:
                raise ValueError("Có sửa đổi từ phiên khác; tải lại trước khi checkpoint.")
            if head and expected_working_revision is None:
                raise ValueError(
                    "Cần checkout revision của journal trước khi checkpoint, không ghi đè sửa đổi chưa đọc."
                )
            revision = previous + 1
            db.execute(
                "INSERT INTO snapshots VALUES (?,?,?,?,?,?)",
                (
                    project.project_id,
                    revision,
                    project.study.study_id,
                    utc_now(),
                    payload,
                    hashlib.sha256(payload).hexdigest(),
                ),
            )
        return revision

    def checkout(self, project_id: str, revision: int | None = None) -> tuple[Project, int, int]:
        with self.connect() as db:
            db.execute("BEGIN")
            row = db.execute(
                "SELECT payload, sha256, revision FROM snapshots WHERE project_id=? AND (? IS NULL OR revision=?) ORDER BY revision DESC LIMIT 1",
                (project_id, revision, revision),
            ).fetchone()
            patches = []
            journal_head = 0
            if row is not None and revision is None:
                patches = db.execute(
                    "SELECT payload, sha256, working_revision FROM working_changes WHERE project_id=? AND base_revision=? ORDER BY working_revision",
                    (project_id, row[2]),
                ).fetchall()
                journal_head = self._verified_working_head(db, project_id, row[2])
        if row is None:
            raise ValueError("Không tìm thấy dự án/revision.")
        if hashlib.sha256(row[0]).hexdigest() != row[1]:
            raise ValueError("Snapshot SQLite không đúng checksum.")
        project = load_project_payload(row[0])
        if revision is None:
            if len(patches) != journal_head:
                raise ValueError("Journal mất bản ghi: số lượng khác revision đã ghi nhận.")
            for expected, (payload, checksum, patch_revision) in enumerate(patches, 1):
                if patch_revision != expected:
                    raise ValueError("Journal mất hoặc sai thứ tự working revision.")
                if hashlib.sha256(payload).hexdigest() != checksum:
                    raise ValueError("Journal không đúng checksum.")
                changes = json.loads(payload)
                validated = {
                    key: TypeAdapter(Project.model_fields[key].annotation or Any).validate_python(value)
                    for key, value in changes.items()
                }
                project = project.model_copy(update=validated)
            verify_project(project)
        return project, int(row[2]), int(patches[-1][2]) if patches else 0

    def load(self, project_id: str, revision: int | None = None) -> Project:
        return self.checkout(project_id, revision)[0]

    def working_revision(self, project_id: str, base_revision: int) -> int:
        with self.connect() as db:
            return (
                db.execute(
                    "SELECT MAX(working_revision) FROM working_changes WHERE project_id=? AND base_revision=?",
                    (project_id, base_revision),
                ).fetchone()[0]
                or 0
            )

    def journal(self, previous: Project, updated: Project, base_revision: int, working_revision: int) -> int:
        """Atomic small patch. No full dataset serialization or snapshot verification on draft edits."""
        if previous.project_id != updated.project_id:
            raise ValueError("Journal không được ghi chéo dự án.")
        changed = {
            key: getattr(updated, key)
            for key in Project.model_fields
            if getattr(previous, key) is not getattr(updated, key)
        }
        payload = canonical(
            {
                key: value.model_dump(mode="json") if isinstance(value, StrictModel) else value
                for key, value in changed.items()
            }
        )
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            base = (
                db.execute(
                    "SELECT MAX(revision) FROM snapshots WHERE project_id=?", (previous.project_id,)
                ).fetchone()[0]
                or 0
            )
            head = self._verified_working_head(db, previous.project_id, base)
            if base != base_revision or head != working_revision:
                raise ValueError(
                    "Dự án đã đổi ở phiên khác; không ghi đè. Hãy tải lại hoặc xuất bản đang giữ."
                )
            next_revision = head + 1
            db.execute(
                "INSERT INTO working_changes VALUES (?,?,?,?,?)",
                (previous.project_id, base, next_revision, payload, hashlib.sha256(payload).hexdigest()),
            )
            db.execute(
                "INSERT INTO working_heads VALUES (?,?,?)", (previous.project_id, base, next_revision)
            )
        return next_revision

    def list_projects(self) -> list[dict]:
        with self.connect() as db:
            return [
                dict(project_id=r[0], study_id=r[1], revision=r[2], timestamp=r[3])
                for r in db.execute(
                    "SELECT project_id, study_id, MAX(revision), MAX(timestamp) FROM snapshots GROUP BY project_id ORDER BY MAX(timestamp) DESC"
                )
            ]

    def backup(self, destination: str | Path):
        with self.connect() as source, sqlite3.connect(destination) as target:
            source.backup(target)


def restore_archive(store: ProjectStore, content: bytes) -> tuple[Project, int]:
    """Restore safely: a colliding archive becomes a traceable, separate project."""
    loaded = import_archive(content)
    with store.connect() as db:
        collision = db.execute(
            "SELECT 1 FROM snapshots WHERE project_id=? LIMIT 1", (loaded.project_id,)
        ).fetchone() is not None
    if collision:
        source_id = loaded.project_id
        loaded = loaded.model_copy(update={
            "project_id": str(uuid4()),
            "import_provenance": {
                **loaded.import_provenance,
                "restored_from_project_id": source_id,
                "restored_at_utc": utc_now(),
                "source_archive_sha256": hashlib.sha256(content).hexdigest(),
            },
        })
    # A new identifier preserves the original audit events, raw data and run hashes.
    verify_project(loaded)
    return loaded, store.save(loaded, 0)
