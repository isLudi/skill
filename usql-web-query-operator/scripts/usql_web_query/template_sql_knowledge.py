"""Plan and apply stable canonical Template Query SQL knowledge syncs."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from _shared.domain_adapters import DomainAdapter, load_domain_adapters
from _shared.errors import UsageError

from .template_query import TemplateQuery, canonical_template_sql_text, template_sql_sha256


PLAN_SCHEMA_VERSION = "1.0.0"
TEMPLATE_CANONICAL_FILENAME = re.compile(r"^template_query_[a-z0-9_]+\.sql$")
TEMPLATE_LEGACY_FILENAME = re.compile(r"^template_query_[a-z0-9_]+_20\d{6}\.sql$")
REVERSE_INDEX_FILES = (
    "field_to_metrics.md",
    "metric_to_raw_sql.md",
    "table_to_dashboards.md",
    "join_risk_index.md",
)


@dataclass(frozen=True)
class TemplateSqlLegacyFile:
    path: Path
    sha256: str

    def to_json(self, root: Path) -> dict[str, str]:
        return {"path": _rel_to_root(self.path, root), "sha256": self.sha256}


@dataclass
class TemplateSqlSyncPlan:
    target: DomainAdapter
    run_date: date
    template_id: int
    template_name: str
    template_status: int | None
    source_update_time: str
    canonical_path: Path
    remote_sql: str = field(repr=False)
    remote_sql_sha256: str = ""
    current_sha256: str | None = None
    legacy_files: list[TemplateSqlLegacyFile] = field(default_factory=list)
    changelog_path: Path | None = None
    changelog_before_sha256: str | None = None
    changelog_after_sha256: str | None = None
    changelog_after: bytes | None = field(default=None, repr=False)
    diagnostics: list[dict[str, str]] = field(default_factory=list)

    @property
    def status(self) -> str:
        return "blocked" if any(item.get("severity") == "error" for item in self.diagnostics) else "ready"

    @property
    def changed(self) -> bool:
        return (
            self.current_sha256 != self.remote_sql_sha256
            or bool(self.legacy_files)
            or self.changelog_before_sha256 != self.changelog_after_sha256
        )

    def to_json(self) -> dict[str, Any]:
        return {
            "schema_version": PLAN_SCHEMA_VERSION,
            "target_skill": self.target.target,
            "domain": self.target.domain_id,
            "run_date": self.run_date.isoformat(),
            "status": self.status,
            "template": {
                "id": self.template_id,
                "name": self.template_name,
                "status": self.template_status,
                "source_update_time": self.source_update_time,
            },
            "canonical_sql_file": _rel_to_root(self.canonical_path, self.target.skill_root),
            "remote_sql_sha256": self.remote_sql_sha256,
            "remote_sql_bytes": len(self.remote_sql.encode("utf-8")),
            "remote_sql_lines": len(self.remote_sql.splitlines()),
            "current_sha256": self.current_sha256,
            "legacy_files": [item.to_json(self.target.skill_root) for item in self.legacy_files],
            "changelog_path": (
                _rel_to_root(self.changelog_path, self.target.skill_root)
                if self.changelog_path is not None
                else None
            ),
            "changelog_before_sha256": self.changelog_before_sha256,
            "changelog_after_sha256": self.changelog_after_sha256,
            "policy": {
                "published_template_required": True,
                "stable_canonical_path_required": True,
                "dated_history_files_removed": True,
                "old_sql_text_not_retained": True,
            },
            "diagnostics": self.diagnostics,
        }


@dataclass
class TemplateSqlSyncResult:
    target_skill: str
    template_id: int
    template_name: str
    canonical_sql_file: str
    mode: str
    status: str
    plan_sha256: str
    before_sha256: str | None
    after_sha256: str
    legacy_files_removed: list[str]
    maintenance: list[dict[str, Any]] = field(default_factory=list)
    fully_verified: bool = False

    def to_json(self) -> dict[str, Any]:
        return {
            "target_skill": self.target_skill,
            "template_id": self.template_id,
            "template_name": self.template_name,
            "canonical_sql_file": self.canonical_sql_file,
            "mode": self.mode,
            "status": self.status,
            "plan_sha256": self.plan_sha256,
            "before_sha256": self.before_sha256,
            "after_sha256": self.after_sha256,
            "legacy_files_removed": self.legacy_files_removed,
            "maintenance": self.maintenance,
            "fully_verified": self.fully_verified,
        }


def resolve_template_canonical_path(target: DomainAdapter, value: Path) -> Path:
    """Resolve only a stable template raw SQL path in the registered Skill."""

    path = value.expanduser()
    resolved = path.resolve() if path.is_absolute() else (target.skill_root / path).resolve()
    raw_root = (target.skill_root / "resources" / "raw_sql").resolve()
    if resolved.parent != raw_root:
        raise UsageError(
            "template canonical SQL must be directly under the registered Skill "
            "resources/raw_sql directory"
        )
    if not TEMPLATE_CANONICAL_FILENAME.fullmatch(resolved.name):
        raise UsageError(
            "template canonical SQL must use a stable template_query_<name>.sql filename; "
            "dated filenames are not allowed"
        )
    if re.search(r"_20\d{6}\.sql$", resolved.name):
        raise UsageError("template canonical SQL cannot use a date-suffixed filename")
    if not resolved.name.startswith(f"template_query_{target.target}_"):
        raise UsageError(
            f"template canonical SQL must stay in the {target.target} domain filename namespace"
        )
    return resolved


def plan_template_sql_sync(
    target: DomainAdapter,
    template: TemplateQuery,
    *,
    canonical_file: Path,
    run_date: date,
    update_changelog: bool = True,
) -> TemplateSqlSyncPlan:
    canonical_path = resolve_template_canonical_path(target, canonical_file)
    remote_sql = canonical_template_sql_text(template.sql_detail)
    remote_hash = template_sql_sha256(remote_sql)
    current_hash = _file_sha256(canonical_path)
    legacy_files = [
        TemplateSqlLegacyFile(path=path, sha256=_file_sha256(path) or "")
        for path in sorted(canonical_path.parent.glob(f"{canonical_path.stem}_20??????.sql"))
        if path.is_file() and TEMPLATE_LEGACY_FILENAME.fullmatch(path.name)
    ]
    diagnostics: list[dict[str, str]] = []
    if template.id <= 0:
        diagnostics.append(_diagnostic("INVALID_TEMPLATE_ID", "error", "template id must be positive"))
    if not template.name:
        diagnostics.append(_diagnostic("EMPTY_TEMPLATE_NAME", "error", "template name is empty"))
    if getattr(template, "is_del", 0) not in (None, 0):
        diagnostics.append(
            _diagnostic(
                "TEMPLATE_DELETED",
                "error",
                f"template {template.id} is deleted (isDel={template.is_del}) and must not be synchronized",
            )
        )
    if template.status != 2:
        diagnostics.append(
            _diagnostic(
                "TEMPLATE_NOT_PUBLISHED",
                "error",
                f"template {template.id} must be published (status=2), got {template.status}",
            )
        )
    changelog_path = target.skill_root / "knowledge" / "update_log" / "changelog.md"
    before_text = changelog_path.read_text(encoding="utf-8") if changelog_path.exists() else ""
    before_changelog_hash = _file_sha256(changelog_path)
    after_text = before_text
    if update_changelog:
        after_text = _append_changelog(
            before_text,
            target=target,
            run_date=run_date,
            template=template,
            canonical_path=canonical_path,
            remote_hash=remote_hash,
            legacy_count=len(legacy_files),
        )
    after_changelog = after_text.encode("utf-8") if after_text != before_text else None
    after_changelog_hash = _bytes_sha256(after_changelog) if after_changelog is not None else before_changelog_hash
    return TemplateSqlSyncPlan(
        target=target,
        run_date=run_date,
        template_id=template.id,
        template_name=template.name,
        template_status=template.status,
        source_update_time=template.update_time or template.publish_time,
        canonical_path=canonical_path,
        remote_sql=remote_sql,
        remote_sql_sha256=remote_hash,
        current_sha256=current_hash,
        legacy_files=legacy_files,
        changelog_path=changelog_path,
        changelog_before_sha256=before_changelog_hash,
        changelog_after_sha256=after_changelog_hash,
        changelog_after=after_changelog,
        diagnostics=diagnostics,
    )


def combined_plan_sha256(plans: list[TemplateSqlSyncPlan]) -> str:
    payload = {
        "schema_version": PLAN_SCHEMA_VERSION,
        "plans": [plan.to_json() for plan in plans],
    }
    return _bytes_sha256(_json_bytes(payload))


def dry_run_result(plan: TemplateSqlSyncPlan, plan_sha256: str) -> TemplateSqlSyncResult:
    return TemplateSqlSyncResult(
        target_skill=plan.target.target,
        template_id=plan.template_id,
        template_name=plan.template_name,
        canonical_sql_file=_rel_to_root(plan.canonical_path, plan.target.skill_root),
        mode="dry_run",
        status=plan.status,
        plan_sha256=plan_sha256,
        before_sha256=plan.current_sha256,
        after_sha256=plan.remote_sql_sha256,
        legacy_files_removed=[_rel_to_root(item.path, plan.target.skill_root) for item in plan.legacy_files],
    )


def apply_template_sql_plan(
    plan: TemplateSqlSyncPlan,
    *,
    expected_plan_sha256: str,
) -> TemplateSqlSyncResult:
    actual_plan_sha256 = combined_plan_sha256([plan])
    if expected_plan_sha256 != actual_plan_sha256:
        raise UsageError(
            "Template SQL sync plan hash mismatch; rerun dry-run and review the new plan: "
            f"expected={expected_plan_sha256}, actual={actual_plan_sha256}"
        )
    if plan.status != "ready":
        raise UsageError("Template SQL sync plan is blocked: " + _diagnostic_text(plan.diagnostics))
    if _file_sha256(plan.canonical_path) != plan.current_sha256:
        raise UsageError(f"Template SQL sync precondition drift: {plan.canonical_path}")
    for legacy in plan.legacy_files:
        if _file_sha256(legacy.path) != legacy.sha256:
            raise UsageError(f"Template SQL sync precondition drift: {legacy.path}")
    if plan.changelog_path is not None and _file_sha256(plan.changelog_path) != plan.changelog_before_sha256:
        raise UsageError(f"Template SQL sync precondition drift: {plan.changelog_path}")

    snapshot_paths = {
        plan.canonical_path,
        *(item.path for item in plan.legacy_files),
    }
    if plan.changelog_path is not None:
        snapshot_paths.add(plan.changelog_path)
    snapshot_paths.update(_maintenance_output_paths(plan.target))
    snapshots = {path: path.read_bytes() if path.exists() else None for path in snapshot_paths}
    maintenance: list[dict[str, Any]] = []
    try:
        if plan.current_sha256 != plan.remote_sql_sha256:
            _atomic_write_bytes(plan.canonical_path, plan.remote_sql.encode("utf-8"))
        for legacy in plan.legacy_files:
            legacy.path.unlink(missing_ok=True)
        if plan.changelog_path is not None and plan.changelog_after is not None:
            _atomic_write_bytes(plan.changelog_path, plan.changelog_after)
        maintenance = run_mandatory_maintenance(plan.target)
        if _file_sha256(plan.canonical_path) != plan.remote_sql_sha256:
            raise UsageError("stable template SQL hash did not match the published remote SQL after write")
        remaining_legacy = [
            path.name
            for path in plan.canonical_path.parent.glob(f"{plan.canonical_path.stem}_20??????.sql")
            if path.is_file()
        ]
        if remaining_legacy:
            raise UsageError("dated template SQL files remain after sync: " + ", ".join(sorted(remaining_legacy)))
    except Exception as exc:  # noqa: BLE001
        _restore_snapshots(snapshots)
        raise UsageError(f"Template SQL sync failed and was rolled back: {exc}") from exc

    return TemplateSqlSyncResult(
        target_skill=plan.target.target,
        template_id=plan.template_id,
        template_name=plan.template_name,
        canonical_sql_file=_rel_to_root(plan.canonical_path, plan.target.skill_root),
        mode="write",
        status="applied",
        plan_sha256=actual_plan_sha256,
        before_sha256=plan.current_sha256,
        after_sha256=plan.remote_sql_sha256,
        legacy_files_removed=[_rel_to_root(item.path, plan.target.skill_root) for item in plan.legacy_files],
        maintenance=maintenance,
        fully_verified=True,
    )


def run_mandatory_maintenance(target: DomainAdapter) -> list[dict[str, Any]]:
    skills_root = target.skill_root.parent
    commands: list[tuple[str, list[str], Path]] = [
        (f"reverse_indexes:{target.skill_root.name}", [sys.executable, "scripts/build_reverse_indexes.py"], target.skill_root),
        ("build_text2sql_catalog", [sys.executable, "scripts/build_text2sql_catalog.py"], skills_root),
        ("audit_knowledge_versions", [sys.executable, "scripts/audit_knowledge_versions.py"], skills_root),
        (f"integrity:{target.skill_root.name}", [sys.executable, "scripts/check_skill_integrity.py"], target.skill_root),
        ("validate_text2sql_stack", [sys.executable, "scripts/validate_text2sql_stack.py"], skills_root),
    ]
    results: list[dict[str, Any]] = []
    for name, command, cwd in commands:
        completed = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
            check=False,
        )
        result = {
            "name": name,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
        results.append(result)
        if completed.returncode != 0:
            raise UsageError(f"mandatory maintenance failed: {name}")
    return results


def _append_changelog(
    text: str,
    *,
    target: DomainAdapter,
    run_date: date,
    template: TemplateQuery,
    canonical_path: Path,
    remote_hash: str,
    legacy_count: int,
) -> str:
    heading = f"## {run_date.isoformat()} 模板取数 stable canonical SQL 同步（模板 {template.id}）"
    if heading in text:
        return text
    relative = _rel_to_root(canonical_path, target.skill_root)
    entry = (
        f"\n{heading}\n\n"
        f"- 线上 `published` 模板 `{template.name}`（id `{template.id}`）回读 SQL SHA-256 为 `{remote_hash}`，"
        f"只保留稳定入口 `{relative}`。\n"
        f"- 本次清理日期后缀历史副本 {legacy_count} 个；历史 SQL 文本不进入知识库，也不作为路由入口。\n"
        "- 保存后已重建反向索引、共享 catalog、唯一版本审计、域内 integrity 和完整 Text2SQL 栈。\n"
    )
    return text.rstrip() + "\n" + entry


def _maintenance_output_paths(target: DomainAdapter) -> set[Path]:
    skills_root = target.skill_root.parent
    paths = {target.skill_root / "knowledge" / "reverse_index" / name for name in REVERSE_INDEX_FILES}
    paths.update(
        {
            target.skill_root / "semantic" / "domain_manifest.json",
            target.skill_root / "semantic" / "generated" / "contract_index.json",
            skills_root / "_shared" / "text2sql_core" / "catalog" / "physical_catalog.json",
        }
    )
    try:
        adapters = load_domain_adapters(skills_root=skills_root)
    except UsageError:
        adapters = ()
    for adapter in adapters:
        paths.add(adapter.skill_root / "semantic" / "domain_manifest.json")
        paths.add(adapter.skill_root / "semantic" / "generated" / "contract_index.json")
    return paths


def _diagnostic(code: str, severity: str, message: str) -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def _diagnostic_text(diagnostics: list[dict[str, str]]) -> str:
    return "; ".join(item.get("message", "unknown diagnostic") for item in diagnostics)


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _bytes_sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _file_sha256(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def _atomic_write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)


def _restore_snapshots(snapshots: dict[Path, bytes | None]) -> None:
    for path, content in snapshots.items():
        if content is None:
            path.unlink(missing_ok=True)
        else:
            _atomic_write_bytes(path, content)


def _rel_to_root(path: Path | None, root: Path) -> str:
    if path is None:
        return ""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)
