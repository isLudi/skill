"""Plan and atomically apply Data Center canonical SQL updates."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from _shared.config import DATA_CENTER_DATASET_URL
from _shared.errors import UsageError

from .data_center import DataCenterDatasetSql


PLAN_SCHEMA_VERSION = "1.0.0"
REGISTRY_SCHEMA_VERSION = "1.0.0"
REGISTRY_RELATIVE_PATH = Path("semantic/current_model_bindings.json")
REVERSE_INDEX_FILES = (
    "field_to_metrics.md",
    "metric_to_raw_sql.md",
    "table_to_dashboards.md",
    "join_risk_index.md",
)


@dataclass(frozen=True)
class DataCenterSkillTarget:
    name: str
    root: Path
    dataset_prefix: str
    doc_filename: str
    title: str
    scope_note: str

    @property
    def domain(self) -> str:
        return "market_consultant" if self.name == "market" else "qingcheng"


@dataclass
class DataCenterDatasetWriteResult:
    dataset_name: str
    dataset_id: str
    model_id: str
    raw_sql_file: str
    action: str
    before_sha256: str | None
    after_sha256: str
    sql_lines: int
    sql_bytes: int
    legacy_files_removed: list[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return self.action != "unchanged" or bool(self.legacy_files_removed)

    def to_json(self) -> dict[str, Any]:
        data = self.__dict__.copy()
        data["changed"] = self.changed
        return data


@dataclass
class FileMutation:
    path: Path
    root: Path
    action: str
    before_sha256: str | None
    after_sha256: str | None
    content: bytes | None = field(default=None, repr=False)

    def to_json(self) -> dict[str, Any]:
        return {
            "path": _rel_to_root(self.path, self.root),
            "action": self.action,
            "before_sha256": self.before_sha256,
            "after_sha256": self.after_sha256,
        }


@dataclass
class DataCenterSkillSyncPlan:
    target: DataCenterSkillTarget
    run_date: date
    scope_complete: bool
    datasets: list[DataCenterDatasetWriteResult]
    registry_before_sha256: str | None
    registry_after_sha256: str
    registry_payload: dict[str, Any] = field(repr=False)
    mutations: list[FileMutation] = field(default_factory=list, repr=False)
    diagnostics: list[dict[str, str]] = field(default_factory=list)

    @property
    def status(self) -> str:
        return "blocked" if any(item.get("severity") == "error" for item in self.diagnostics) else "ready"

    def to_json(self) -> dict[str, Any]:
        return {
            "schema_version": PLAN_SCHEMA_VERSION,
            "skill": self.target.name,
            "domain": self.target.domain,
            "run_date": self.run_date.isoformat(),
            "scope_complete": self.scope_complete,
            "status": self.status,
            "registry_before_sha256": self.registry_before_sha256,
            "registry_after_sha256": self.registry_after_sha256,
            "datasets": [item.to_json() for item in self.datasets],
            "mutations": [item.to_json() for item in self.mutations],
            "diagnostics": self.diagnostics,
        }


@dataclass
class DataCenterSkillSyncResult:
    skill: str
    root: str
    mode: str
    run_date: str
    plan_sha256: str
    status: str
    datasets_seen: int
    raw_sql_changed: int
    changed_files: list[str]
    maintenance: list[dict[str, Any]] = field(default_factory=list)
    rolled_back: bool = False

    def to_json(self) -> dict[str, Any]:
        return self.__dict__.copy()


def plan_data_center_sync(
    target: DataCenterSkillTarget,
    dataset_sqls: list[DataCenterDatasetSql],
    *,
    run_date: date,
    scope_complete: bool,
    update_changelog: bool,
    retire_model_ids: set[str] | None = None,
    slot_bindings: dict[str, str] | None = None,
) -> DataCenterSkillSyncPlan:
    if not target.root.exists():
        raise UsageError(f"Target skill root does not exist: {target.root}")

    registry_path = target.root / REGISTRY_RELATIVE_PATH
    registry_before_sha256 = _file_sha256(registry_path)
    registry = _load_registry(target, registry_path)
    models_by_id = {str(item["model_id"]): dict(item) for item in registry.get("models", [])}
    retire_model_ids = set(retire_model_ids or set())
    slot_bindings = dict(slot_bindings or {})
    records: list[DataCenterDatasetWriteResult] = []
    mutations: list[FileMutation] = []
    diagnostics: list[dict[str, str]] = []
    observed_ids: set[str] = set()

    for ordinal, item in enumerate(dataset_sqls, start=1):
        model_id = _stable_model_id(item)
        if model_id in observed_ids:
            diagnostics.append(_diagnostic("DUPLICATE_MODEL_IN_FETCH", "error", f"model_id {model_id} appeared more than once"))
            continue
        observed_ids.add(model_id)
        raw_path = target.root / "resources" / "raw_sql" / _raw_sql_filename(target, model_id)
        content = (item.execute_sql.rstrip() + "\n").encode("utf-8")
        before_sha = _file_sha256(raw_path)
        after_sha = _bytes_sha256(content)
        action = "unchanged" if before_sha == after_sha else ("replace" if before_sha else "create")
        if action != "unchanged":
            mutations.append(_write_mutation(raw_path, target.root, content))

        legacy_paths = sorted(
            path
            for path in raw_path.parent.glob(f"data_center_{target.dataset_prefix}_{model_id}_20??????.sql")
            if path != raw_path
        )
        for legacy_path in legacy_paths:
            mutations.append(_delete_mutation(legacy_path, target.root))

        previous = models_by_id.get(model_id)
        model = {
            "model_id": model_id,
            "dataset_id": item.dataset.id,
            "dataset_name": item.dataset.name,
            "file_value": item.dataset.file_value,
            "subject_id": item.dataset.subject_id,
            "data_source_id": item.data_source_id,
            "path": item.dataset.path_text,
            "canonical_sql": _rel_to_root(raw_path, target.root),
            "sql_sha256": after_sha,
            "sql_lines": len(item.execute_sql.splitlines()),
            "sql_bytes": len(item.execute_sql.encode("utf-8")),
            "ordinal": ordinal if scope_complete else int((previous or {}).get("ordinal") or 100000 + ordinal),
        }
        comparison_keys = tuple(model)
        if previous and all(previous.get(key) == model.get(key) for key in comparison_keys):
            model["source_observed_on"] = previous.get("source_observed_on", run_date.isoformat())
        else:
            model["source_observed_on"] = run_date.isoformat()
        models_by_id[model_id] = model

        records.append(
            DataCenterDatasetWriteResult(
                dataset_name=item.dataset.name,
                dataset_id=item.dataset.id,
                model_id=model_id,
                raw_sql_file=_rel_to_root(raw_path, target.root),
                action=action,
                before_sha256=before_sha,
                after_sha256=after_sha,
                sql_lines=model["sql_lines"],
                sql_bytes=model["sql_bytes"],
                legacy_files_removed=[_rel_to_root(path, target.root) for path in legacy_paths],
            )
        )

    unknown_retirements = sorted(retire_model_ids - set(models_by_id))
    if unknown_retirements:
        diagnostics.append(
            _diagnostic(
                "RETIRE_MODEL_NOT_CURRENT",
                "error",
                "requested retirement is not current: " + ", ".join(unknown_retirements),
            )
        )
    for model_id in sorted(retire_model_ids & set(models_by_id)):
        model = models_by_id.pop(model_id)
        source = target.root / str(model["canonical_sql"])
        if source.exists():
            mutations.append(_delete_mutation(source, target.root))

    if scope_complete and registry.get("models"):
        missing = sorted((set(models_by_id) - observed_ids) - retire_model_ids)
        if missing:
            diagnostics.append(
                _diagnostic(
                    "MODEL_REMOVAL_REQUIRES_REVIEW",
                    "error",
                    "full-scope refresh did not observe current model(s): " + ", ".join(missing),
                )
            )

    semantic_slots = [dict(item) for item in registry.get("semantic_slots", [])]
    slots_by_id = {str(item.get("slot_id") or ""): item for item in semantic_slots}
    for slot_id, model_id in slot_bindings.items():
        if slot_id not in slots_by_id:
            diagnostics.append(_diagnostic("SLOT_BINDING_NOT_REGISTERED", "error", f"unknown semantic slot: {slot_id}"))
            continue
        slots_by_id[slot_id]["current_model_id"] = model_id

    registry_after = {
        "schema_version": REGISTRY_SCHEMA_VERSION,
        "domain": target.domain,
        "canonical_filename_policy": f"data_center_{target.dataset_prefix}_<model_id>.sql",
        "models": sorted(models_by_id.values(), key=_model_sort_key),
        "semantic_slots": semantic_slots,
    }
    diagnostics.extend(_validate_registry(target, registry_after))
    registry_bytes = _json_bytes(registry_after)
    registry_after_sha256 = _bytes_sha256(registry_bytes)
    if registry_before_sha256 != registry_after_sha256:
        mutations.append(_write_mutation(registry_path, target.root, registry_bytes))

    doc_path = target.root / "knowledge" / "dashboards" / target.doc_filename
    doc_bytes = _build_index_doc(target, registry_after, run_date=run_date).encode("utf-8")
    if _file_sha256(doc_path) != _bytes_sha256(doc_bytes):
        mutations.append(_write_mutation(doc_path, target.root, doc_bytes))

    changed_records = [item for item in records if item.changed]
    if update_changelog and changed_records:
        changelog_path = target.root / "knowledge" / "update_log" / "changelog.md"
        if changelog_path.exists():
            current = changelog_path.read_text(encoding="utf-8")
            updated = _updated_changelog(current, target, changed_records, run_date)
            if updated != current:
                mutations.append(_write_mutation(changelog_path, target.root, updated.encode("utf-8")))

    return DataCenterSkillSyncPlan(
        target=target,
        run_date=run_date,
        scope_complete=scope_complete,
        datasets=records,
        registry_before_sha256=registry_before_sha256,
        registry_after_sha256=registry_after_sha256,
        registry_payload=registry_after,
        mutations=_dedupe_mutations(mutations),
        diagnostics=diagnostics,
    )


def combined_plan_sha256(plans: list[DataCenterSkillSyncPlan]) -> str:
    payload = {
        "schema_version": PLAN_SCHEMA_VERSION,
        "plans": [plan.to_json() for plan in plans],
    }
    return _bytes_sha256(_json_bytes(payload))


def _data_center_apply_lock_path(plans: list[DataCenterSkillSyncPlan]) -> Path:
    if not plans:
        raise UsageError("Data Center sync requires at least one plan")
    skills_root = plans[0].target.root.parent.resolve()
    key = hashlib.sha256(str(skills_root).casefold().encode("utf-8")).hexdigest()[:20]
    return Path(tempfile.gettempdir()) / f"codex-data-center-sync-{key}.lock"


@contextmanager
def data_center_apply_lock(plans: list[DataCenterSkillSyncPlan]):
    """Serialize Apply across processes; a stale lock blocks safely for manual review."""

    lock_path = _data_center_apply_lock_path(plans)
    try:
        descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise UsageError(
            f"another Data Center Apply is running or left a stale lock: {lock_path}"
        ) from exc
    try:
        os.write(descriptor, f"pid={os.getpid()}\n".encode("ascii"))
    finally:
        os.close(descriptor)
    try:
        yield lock_path
    finally:
        lock_path.unlink(missing_ok=True)


def apply_data_center_plans(
    plans: list[DataCenterSkillSyncPlan],
    *,
    expected_plan_sha256: str,
) -> list[DataCenterSkillSyncResult]:
    with data_center_apply_lock(plans):
        return _apply_data_center_plans_locked(
            plans,
            expected_plan_sha256=expected_plan_sha256,
        )


def _apply_data_center_plans_locked(
    plans: list[DataCenterSkillSyncPlan],
    *,
    expected_plan_sha256: str,
) -> list[DataCenterSkillSyncResult]:
    actual_plan_sha256 = combined_plan_sha256(plans)
    if expected_plan_sha256 != actual_plan_sha256:
        raise UsageError(
            "Data Center sync plan hash mismatch; rerun dry-run and review the new plan: "
            f"expected={expected_plan_sha256}, actual={actual_plan_sha256}"
        )
    blocked = [plan.target.name for plan in plans if plan.status != "ready"]
    if blocked:
        raise UsageError("Data Center sync plan is blocked for: " + ", ".join(blocked))

    mutations = _merge_plan_mutations(plans)
    for mutation in mutations:
        if _file_sha256(mutation.path) != mutation.before_sha256:
            raise UsageError(f"Data Center sync precondition drift: {mutation.path}")

    snapshot_paths = set(mutation.path for mutation in mutations)
    snapshot_paths.update(_maintenance_output_paths(plans))
    snapshots = {path: path.read_bytes() if path.exists() else None for path in snapshot_paths}
    maintenance: list[dict[str, Any]] = []
    try:
        for mutation in mutations:
            if mutation.action == "delete":
                mutation.path.unlink(missing_ok=True)
            else:
                if mutation.content is None:
                    raise UsageError(f"missing mutation content: {mutation.path}")
                _atomic_write_bytes(mutation.path, mutation.content)
        maintenance = run_mandatory_maintenance(plans)
    except Exception as exc:  # noqa: BLE001
        _restore_snapshots(snapshots)
        raise UsageError(f"Data Center sync failed and was rolled back: {exc}") from exc

    results: list[DataCenterSkillSyncResult] = []
    for plan in plans:
        changed = [item for item in plan.mutations]
        results.append(
            DataCenterSkillSyncResult(
                skill=plan.target.name,
                root=str(plan.target.root),
                mode="apply",
                run_date=plan.run_date.isoformat(),
                plan_sha256=actual_plan_sha256,
                status="applied",
                datasets_seen=len(plan.datasets),
                raw_sql_changed=sum(1 for item in plan.datasets if item.changed),
                changed_files=[_rel_to_root(item.path, plan.target.root) for item in changed],
                maintenance=maintenance,
            )
        )
    return results


def dry_run_results(plans: list[DataCenterSkillSyncPlan]) -> list[DataCenterSkillSyncResult]:
    plan_sha = combined_plan_sha256(plans)
    return [
        DataCenterSkillSyncResult(
            skill=plan.target.name,
            root=str(plan.target.root),
            mode="dry_run",
            run_date=plan.run_date.isoformat(),
            plan_sha256=plan_sha,
            status=plan.status,
            datasets_seen=len(plan.datasets),
            raw_sql_changed=sum(1 for item in plan.datasets if item.changed),
            changed_files=[_rel_to_root(item.path, plan.target.root) for item in plan.mutations],
        )
        for plan in plans
    ]


def run_mandatory_maintenance(plans: list[DataCenterSkillSyncPlan]) -> list[dict[str, Any]]:
    targets = list(dict.fromkeys(plan.target.root for plan in plans))
    skills_root = plans[0].target.root.parent
    commands: list[tuple[str, list[str], Path]] = []
    for root in targets:
        commands.append((f"reverse_indexes:{root.name}", [sys.executable, "scripts/build_reverse_indexes.py"], root))
    commands.append(("build_text2sql_catalog", [sys.executable, "scripts/build_text2sql_catalog.py"], skills_root))
    commands.append(("audit_knowledge_versions", [sys.executable, "scripts/audit_knowledge_versions.py"], skills_root))
    for root in targets:
        commands.append((f"integrity:{root.name}", [sys.executable, "scripts/check_skill_integrity.py"], root))
    commands.append(("validate_text2sql_stack", [sys.executable, "scripts/validate_text2sql_stack.py"], skills_root))

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
        item = {
            "name": name,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
        results.append(item)
        if completed.returncode != 0:
            raise UsageError(f"mandatory maintenance failed: {name}")
    return results


def _load_registry(target: DataCenterSkillTarget, path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "schema_version": REGISTRY_SCHEMA_VERSION,
            "domain": target.domain,
            "models": [],
            "semantic_slots": [],
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UsageError(f"invalid current-model registry: {path}: {exc}") from exc
    if payload.get("domain") != target.domain:
        raise UsageError(f"current-model registry domain mismatch: {path}")
    return payload


def _validate_registry(target: DataCenterSkillTarget, registry: dict[str, Any]) -> list[dict[str, str]]:
    diagnostics: list[dict[str, str]] = []
    model_ids: set[str] = set()
    for model in registry.get("models", []):
        model_id = str(model.get("model_id") or "")
        if not model_id or model_id in model_ids:
            diagnostics.append(_diagnostic("DUPLICATE_CURRENT_MODEL", "error", f"duplicate/empty model_id: {model_id}"))
            continue
        model_ids.add(model_id)
        expected = f"resources/raw_sql/data_center_{target.dataset_prefix}_{model_id}.sql"
        if model.get("canonical_sql") != expected:
            diagnostics.append(_diagnostic("UNSTABLE_CANONICAL_PATH", "error", f"{model_id} must use {expected}"))

    slot_ids: set[str] = set()
    for slot in registry.get("semantic_slots", []):
        slot_id = str(slot.get("slot_id") or "")
        current_model = str(slot.get("current_model_id") or "")
        if not slot_id or slot_id in slot_ids:
            diagnostics.append(_diagnostic("DUPLICATE_SEMANTIC_SLOT", "error", f"duplicate/empty slot_id: {slot_id}"))
        slot_ids.add(slot_id)
        if slot_id and not slot_id.startswith(target.domain + ":"):
            diagnostics.append(_diagnostic("CROSS_DOMAIN_SEMANTIC_SLOT", "error", f"foreign slot_id: {slot_id}"))
        if current_model not in model_ids:
            diagnostics.append(_diagnostic("SLOT_MODEL_NOT_CURRENT", "error", f"{slot_id} points to non-current model {current_model}"))
        evidence_path = str(slot.get("evidence_path") or "")
        if evidence_path and not (target.root / evidence_path).is_file():
            diagnostics.append(_diagnostic("SLOT_EVIDENCE_MISSING", "error", f"{slot_id} evidence is missing: {evidence_path}"))
    return diagnostics


def _build_index_doc(target: DataCenterSkillTarget, registry: dict[str, Any], *, run_date: date) -> str:
    lines = [
        f"# {target.title}",
        "",
        "## 1. 来源与范围",
        "",
        f"- 最近同步计划日期：{run_date.isoformat()}",
        f"- 来源页面：{DATA_CENTER_DATASET_URL}",
        f"- 同步范围：{target.scope_note}",
        "- canonical SQL 使用稳定文件名；更新时间与 SHA-256 由 `semantic/current_model_bindings.json` 记录。",
        "- 更新必须执行 `dry-run -> expected plan hash -> atomic apply -> full validation`，旧日期文件不得进入活跃知识库。",
        "",
        "## 2. 当前数据集清单",
        "",
        "| 序号 | 数据集名称 | 数据集 ID | model_id | subjectId | 数据源 ID | 所属路径 | canonical SQL | SQL SHA-256 | 行数 |",
        "|---:|---|---|---|---|---|---|---|---|---:|",
    ]
    for index, model in enumerate(sorted(registry.get("models", []), key=_model_sort_key), start=1):
        raw_name = Path(str(model["canonical_sql"])).name
        raw_link = f"[{raw_name}](../../resources/raw_sql/{raw_name})"
        lines.append(
            "| "
            + " | ".join(
                [
                    str(index),
                    _md_code(str(model.get("dataset_name") or "")),
                    _md_code(str(model.get("dataset_id") or "")),
                    _md_code(str(model.get("model_id") or "")),
                    _md_code(str(model.get("subject_id") or "")),
                    _md_code(str(model.get("data_source_id") or "")),
                    _escape_cell(str(model.get("path") or "")),
                    raw_link,
                    f"`{str(model.get('sql_sha256') or '')}`",
                    str(model.get("sql_lines") or 0),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## 3. 维护说明",
            "",
            "- 默认命令只生成同步计划；Apply 必须携带完全匹配的 `--expected-plan-sha256`。",
            "- 同一 model_id 只能覆盖稳定 canonical 文件，不能创建日期后缀副本。",
            "- 模型替换涉及业务用途变化时，先更新 `semantic_slots` 的 current model 和看板证据，再 Apply。",
            "- 青橙与市场顾问 current-model registry 相互隔离，不得跨域引用。",
            "",
        ]
    )
    return "\n".join(lines)


def _updated_changelog(
    text: str,
    target: DataCenterSkillTarget,
    records: list[DataCenterDatasetWriteResult],
    run_date: date,
) -> str:
    heading = f"## {run_date.isoformat()} 数据中心 stable canonical SQL 同步"
    if heading in text:
        return text
    model_ids = ", ".join(item.model_id for item in records)
    entry = (
        f"\n{heading}\n\n"
        f"- 按已审阅同步计划原子更新 model_id：`{model_ids}`；每个 model_id 只保留稳定 canonical 路径。\n"
        "- 写入后已强制重建反向索引和目录，并运行唯一版本审计、域内 integrity 与完整 Text2SQL 栈验证。\n"
    )
    return text.rstrip() + "\n" + entry


def _maintenance_output_paths(plans: list[DataCenterSkillSyncPlan]) -> set[Path]:
    skills_root = plans[0].target.root.parent
    paths: set[Path] = set()
    for plan in plans:
        reverse_root = plan.target.root / "knowledge" / "reverse_index"
        paths.update(reverse_root / name for name in REVERSE_INDEX_FILES)
    for skill_name in ("sql-query-writer-for-dashboard", "qingcheng-dashboard-sql"):
        root = skills_root / skill_name
        paths.add(root / "semantic" / "domain_manifest.json")
        paths.add(root / "semantic" / "generated" / "contract_index.json")
    paths.add(skills_root / "_shared" / "text2sql_core" / "catalog" / "physical_catalog.json")
    return paths


def _merge_plan_mutations(plans: list[DataCenterSkillSyncPlan]) -> list[FileMutation]:
    by_path: dict[Path, FileMutation] = {}
    for plan in plans:
        for mutation in plan.mutations:
            previous = by_path.get(mutation.path)
            if previous and previous.to_json() != mutation.to_json():
                raise UsageError(f"conflicting Data Center mutations: {mutation.path}")
            by_path[mutation.path] = mutation
    return [by_path[path] for path in sorted(by_path, key=str)]


def _dedupe_mutations(mutations: list[FileMutation]) -> list[FileMutation]:
    by_path: dict[Path, FileMutation] = {}
    for mutation in mutations:
        by_path[mutation.path] = mutation
    return [by_path[path] for path in sorted(by_path, key=str)]


def _write_mutation(path: Path, root: Path, content: bytes) -> FileMutation:
    before = _file_sha256(path)
    after = _bytes_sha256(content)
    return FileMutation(
        path=path,
        root=root,
        action="replace" if before else "create",
        before_sha256=before,
        after_sha256=after,
        content=content,
    )


def _delete_mutation(path: Path, root: Path) -> FileMutation:
    return FileMutation(
        path=path,
        root=root,
        action="delete",
        before_sha256=_file_sha256(path),
        after_sha256=None,
    )


def _raw_sql_filename(target: DataCenterSkillTarget, model_id: str) -> str:
    return f"data_center_{target.dataset_prefix}_{model_id}.sql"


def _stable_model_id(item: DataCenterDatasetSql) -> str:
    stable_id = item.dataset.file_value or item.dataset.subject_id or item.dataset.id
    stable_id = re.sub(r"[^A-Za-z0-9_]+", "_", stable_id).strip("_")
    if not stable_id:
        raise UsageError(f"Data Center dataset has no stable model id: {item.dataset.name}")
    return stable_id


def _model_sort_key(item: dict[str, Any]) -> tuple[int, int | str]:
    ordinal = int(item.get("ordinal") or 100000)
    model_id = str(item.get("model_id") or "")
    return ordinal, int(model_id) if model_id.isdigit() else model_id


def _diagnostic(code: str, severity: str, message: str) -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


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


def _rel_to_root(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _escape_cell(value: str) -> str:
    text = str(value or "").replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text.replace("|", r"\|")


def _md_code(value: str) -> str:
    return f"`{_escape_cell(value)}`" if value else ""


def result_to_json(results: list[DataCenterSkillSyncResult]) -> str:
    return json.dumps([result.to_json() for result in results], ensure_ascii=False, indent=2)
