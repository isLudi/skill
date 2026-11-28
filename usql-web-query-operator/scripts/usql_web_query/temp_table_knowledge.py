"""Hash-bound local knowledge migration for a confirmed temporary-table owner change."""

from __future__ import annotations

from datetime import date
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from types import SimpleNamespace
from typing import Any
import zipfile

from _shared.domain_adapters import adapters_by_target, load_domain_adapters
from _shared.errors import UsageError
from .data_center_knowledge import data_center_apply_lock, _atomic_write_bytes


PLAN_TYPE = "TempTableKnowledgeMigrationPlan"
TABLE_RE = re.compile(r"temp_table\.dingxi01_([a-z0-9_]+)")
FOLDERS = {"qingcheng": "temp_tables", "market": "tables"}


def digest(value: bytes | dict) -> str:
    if isinstance(value, dict):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def file_hash(path: Path) -> str | None:
    return digest(path.read_bytes()) if path.is_file() else None


def encode(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def safe_path(root: Path, relative: str) -> Path:
    part = PurePosixPath(relative)
    if not relative or "\\" in relative or ":" in relative or part.is_absolute() or any(x in {"..", "."} for x in part.parts):
        raise UsageError("Migration paths must be repository-relative without traversal.")
    path = root.joinpath(*part.parts)
    if not path.resolve().is_relative_to(root.resolve()) or any(p.is_symlink() for p in (path, *path.parents) if p != root.parent):
        raise UsageError("Migration path escapes the repository or traverses a symlink.")
    return path


def _replace(text: str, names: dict[str, str]) -> str:
    if not names:
        return text
    pattern = re.compile(r"(?<![a-zA-Z0-9_])(" + "|".join(re.escape(k) for k in sorted(names, key=len, reverse=True)) + r")(?![a-zA-Z0-9_])")
    return pattern.sub(lambda m: names[m.group()], text)


def _replace_json(value: Any, names: dict[str, str]) -> Any:
    if isinstance(value, str):
        return _replace(value, names)
    if isinstance(value, list):
        return [_replace_json(v, names) for v in value]
    if isinstance(value, dict):
        return {k: _replace_json(v, names) for k, v in value.items()}
    return value


def source_paths(root: Path, adapters: list) -> set[Path]:
    paths = set()
    for adapter in adapters:
        for folder in ("knowledge", "semantic", "resources/raw_sql", "references", "docs", "examples"):
            paths.update(p for p in (adapter.skill_root / folder).rglob("*") if p.is_file())
        paths.add(adapter.skill_root / "metadata.json")
        paths.add(adapter.skill_root / "SKILL.md")
    paths.add(root / "usql-web-query-operator/references/domain_adapters.json")
    return paths


def generated_paths(adapters: list) -> set[Path]:
    paths = set()
    for adapter in adapters:
        base = adapter.skill_root
        paths.update(base / "knowledge/reverse_index" / name for name in (
            "field_to_metrics.md", "metric_to_raw_sql.md", "table_to_dashboards.md", "join_risk_index.md"))
        paths.update((base / "semantic/domain_manifest.json", base / "semantic/generated/contract_index.json"))
    repo = adapters[0].skill_root.parent
    # Shared boundary generation may update another domain's derived manifest.
    for metadata in repo.glob("*/metadata.json"):
        value = json.loads(metadata.read_text(encoding="utf-8"))
        if value.get("semantic_manifest") == "semantic/domain_manifest.json":
            paths.update((metadata.parent / "semantic/domain_manifest.json",
                          metadata.parent / "semantic/generated/contract_index.json"))
    paths.add(repo / "_shared/text2sql_core/catalog/physical_catalog.json")
    return paths


def build_plan(root: Path, request: dict, catalog: dict) -> dict:
    root = root.resolve()
    if set(request) - {"schema_version", "as_of", "maintenance_change_confirmed", "mappings", "document_updates"} or request.get("schema_version") != "1.0.0" or request.get("maintenance_change_confirmed") is not True:
        raise UsageError("A typed, explicitly confirmed maintenance migration request is required.")
    date.fromisoformat(request["as_of"])
    mappings = request["mappings"]
    if not isinstance(mappings, list) or len(mappings) > 50 or (not mappings and not request.get("document_updates")):
        raise UsageError("Migration needs explicit table mappings or reviewed document corrections.")
    registry = adapters_by_target(load_domain_adapters(skills_root=root))
    targets, seen = [], set()
    writes: dict[Path, bytes | None] = {}
    mapping_paths: set[Path] = set()
    by_target: dict[str, list[dict]] = {}
    for item in mappings:
        if set(item) - {"target", "old_table", "new_table", "merged_markdown", "current_reference_table", "production_evidence", "retire_destination"} or not {"target", "old_table", "new_table"} <= set(item):
            raise UsageError("Invalid temporary-table mapping keys.")
        target = item["target"]
        match = TABLE_RE.fullmatch(item["old_table"])
        if target not in FOLDERS or not match or item["new_table"] != "temp_table.lvshuai01_" + match.group(1):
            raise UsageError("Only registered domains and exact dingxi01-to-lvshuai01 owner changes are supported.")
        key = (target, item["old_table"])
        if key in seen:
            raise UsageError("Duplicate migration mapping.")
        seen.add(key)
        adapter = registry[target]
        reference = item.get("current_reference_table", item["new_table"])
        if reference != item["new_table"]:
            reference_doc = adapter.skill_root / "knowledge" / FOLDERS[target] / (reference + ".md")
            if not re.fullmatch(r"temp_table\.[a-z0-9_]+", reference) or not reference_doc.is_file():
                raise UsageError("A different current source requires an existing same-domain table document.")
            evidence = item.get("production_evidence")
            if not isinstance(evidence, list) or not evidence:
                raise UsageError("A semantic source replacement requires exact saved production SQL evidence.")
            for record in evidence:
                observed = catalog.get("production_sql", {}).get(record["dataset_id"], {})
                if any(observed.get(k) != record.get(k) for k in ("dataset_id", "model_id", "sql_sha256")) or reference not in observed.get("temp_tables", []):
                    raise UsageError("The current source is not proven by the live production SQL Hash.")
        if adapter not in targets:
            targets.append(adapter)
        by_target.setdefault(target, []).append(item)
        live = catalog.get(item["new_table"])
        if not isinstance(live, dict) or set(live) != {"id", "name"} or live["name"] != item["new_table"] or not str(live["id"]).isdigit():
            raise UsageError("The new temporary table has no unique live catalog identity: " + item["new_table"])
        folder = adapter.skill_root / "knowledge" / FOLDERS[target]
        old, new = folder / (item["old_table"] + ".md"), folder / (item["new_table"] + ".md")
        mapping_paths.update((old, new))
        if item.get("retire_destination") is True:
            if reference == item["new_table"] or not new.is_file() or old.exists():
                raise UsageError("Retirement requires a migrated destination and a separately proven current source.")
            writes[new] = None
            continue
        merged = item.get("merged_markdown")
        if not old.is_file() and (merged is None or new.exists()):
            raise UsageError("Missing legacy documentation requires a reviewed new document and an absent destination.")
        if new.exists() and merged is None:
            raise UsageError("An existing destination requires reviewed merged_markdown: " + str(new))
        if merged is not None and (not isinstance(merged, str) or not merged.startswith("# " + item["new_table"] + "\n")):
            raise UsageError("Reviewed merged document must have the exact new table heading.")
        text = merged if merged is not None else old.read_text(encoding="utf-8")
        names = {row["old_table"].split(".", 1)[1]: row.get("current_reference_table", row["new_table"]).split(".", 1)[1] for row in mappings if row["target"] == target}
        # A physical owner rename can coexist with a different semantic successor.
        names[item["old_table"].split(".", 1)[1]] = item["new_table"].split(".", 1)[1]
        text = _replace(text, names)
        heading, _, body = text.partition("\n")
        notice = (f"\n维护账号迁移：{request['as_of']} 用户确认同后缀表由 lvshuai01 接续维护；线上新表身份已核实。"
                  "字段及业务含义沿用已确认结构，历史 SQL、Excel 扫描和 Query 证据不等于新表本次数据验证。"
                  "当前使用规则见 [临时表维护迁移](../temp_table_maintenance.md)。\n")
        writes[new] = (heading + "\n" + notice + body).replace("\r\n", "\n").encode("utf-8")
        if old.exists():
            writes[old] = None
    updates = request.get("document_updates", [])
    if not isinstance(updates, list) or any(not isinstance(u, dict) or set(u) != {"target", "path", "before_sha256", "content"} or u["target"] not in FOLDERS for u in updates):
        raise UsageError("Reviewed document corrections must belong to a registered migration domain.")
    for update in updates:
        adapter = registry[update["target"]]
        if adapter not in targets:
            targets.append(adapter)
        by_target.setdefault(update["target"], [])
    if len({(u["target"], u["path"]) for u in updates}) != len(updates):
        raise UsageError("Duplicate reviewed document correction.")
    # Rewrite current semantic references, while keeping historical records and raw SQL truthful.
    for target, rows in by_target.items():
        adapter = registry[target]
        names = {row["old_table"].split(".", 1)[1]: row.get("current_reference_table", row["new_table"]).split(".", 1)[1] for row in rows}
        markdown = list((adapter.skill_root / "knowledge").rglob("*.md"))
        for folder in ("references", "docs", "examples"):
            markdown.extend((adapter.skill_root / folder).rglob("*.md"))
        for path in sorted(markdown):
            if path in writes or "reverse_index" in path.parts or "dashboard_web_profiles" in path.parts:
                continue
            before = path.read_text(encoding="utf-8")
            if "update_log" in path.parts:
                after = before
                for old, new in names.items():
                    after = after.replace(old + ".md", new + ".md")
            else:
                after = _replace(before, names)
            if before != after:
                writes[path] = after.replace("\r\n", "\n").encode("utf-8")
        for update in request.get("document_updates", []):
            if update["target"] != target:
                continue
            relative = update["path"]
            path = safe_path(adapter.skill_root, relative)
            if not relative.startswith("knowledge/") or path.suffix != ".md" or "update_log" in path.parts or "reverse_index" in path.parts or "dashboard_web_profiles" in path.parts or path in writes and writes[path] is None:
                raise UsageError("Reviewed corrections must be retained same-domain Markdown knowledge documents.")
            if file_hash(path) != update["before_sha256"] or not isinstance(update["content"], str) or not update["content"].startswith("# "):
                raise UsageError("Reviewed correction source Hash drift or missing source.")
            writes[path] = update["content"].replace("\r\n", "\n").encode("utf-8")
        guide = adapter.skill_root / "knowledge/temp_table_maintenance.md"
        migration_path = adapter.skill_root / "semantic/temp_table_migrations.json"
        retained = {}
        if migration_path.exists():
            previous_migration = json.loads(migration_path.read_text(encoding="utf-8"))
            if previous_migration.get("domain") != adapter.domain_id or previous_migration.get("schema_version") != "1.0.0":
                raise UsageError("Existing migration registry has an invalid domain or schema.")
            retained = {r["old_table"]: r for r in previous_migration["mappings"]}
        for row in rows:
            record = {"old_table": row["old_table"], "new_table": row["new_table"],
                      "current_reference_table": row.get("current_reference_table", row["new_table"]),
                      "production_evidence": row.get("production_evidence", []),
                      "live_id": catalog[row["new_table"]]["id"]}
            previous_record = retained.get(row["old_table"])
            if previous_record is not None and {k: v for k, v in previous_record.items() if k != "document_retired"} != record:
                raise UsageError("Existing migration mapping differs; an incremental request cannot replace it.")
            if row.get("retire_destination") is True:
                if previous_record is None:
                    raise UsageError("Retirement requires an existing migration record.")
                record["document_retired"] = True
            retained[row["old_table"]] = record
        cumulative = [retained[k] for k in sorted(retained)]
        lines = ["# 临时表维护迁移", "", f"核实日期：{request['as_of']}。用户确认本次为维护账号变更，业务结构基本一致。", "",
                 "当前生成、修订 SQL 使用下列 lvshuai01 表名；旧维护人名称只作为历史来源，不再作为当前知识入口。",
                 "resources/raw_sql 中的线上/历史 SQL 快照保持原文；不把本次知识迁移描述成生产 SQL 已更新。",
                 "历史样本行数、Excel 扫描、旧 Query 及旧 SQL 的使用关系不能直接证明新表最新内容、唯一性或刷新状态。",
                 "两域共享物理表不代表共享业务口径；各自保留部门范围、Join 键及上传切片门禁。", "",
                 "| 原表名（历史） | 当前表名 | 线上表 ID | 当前文档 |", "|---|---|---|---|"]
        for row in cumulative:
            current = row.get("current_reference_table", row["new_table"]) if row.get("document_retired") else row["new_table"]
            label = "已删除副本文档；当前使用 " + current if row.get("document_retired") else row["new_table"]
            lines.append(f"| `{row['old_table']}` | {label} | `{row['live_id']}` | [{current}]({FOLDERS[target]}/{current}.md) |")
        for row in cumulative:
            if row.get("current_reference_table", row["new_table"]) != row["new_table"]:
                lines.append(f"\n业务来源例外：`{row['new_table']}` 不作为完整业务来源，当前引用改用 `{row['current_reference_table']}`；按精确线上 SQL Hash 重新验证，不据前缀推断等价。\n")
        writes[guide] = ("\n".join(lines).rstrip() + "\n").encode("utf-8")
        migration = {"schema_version": "1.0.0", "domain": adapter.domain_id, "as_of": request["as_of"],
                     "mappings": cumulative,
                     "raw_sql_policy": "preserve_exact_historical_or_online_snapshot"}
        writes[migration_path] = encode(migration)
        changelog = adapter.skill_root / adapter.dashboard.changelog
        previous = writes.get(changelog) or changelog.read_bytes()
        action = (f"核实 {len(rows)} 张新表身份，合并/修订当前表知识及契约；映射见 `knowledge/temp_table_maintenance.md`。"
                  if rows else "按精确源 Hash 审阅修订本地知识文档，刷新契约和生成目录；不改变业务口径。")
        writes[changelog] = previous.rstrip() + (f"\n\n## {request['as_of']} 临时表知识维护\n\n"
            f"- {action}\n"
            "- 保留历史 Query、线上/历史 SQL 快照及原有业务边界；未上传、删除或修改任何线上表/数据集。\n").encode("utf-8")
        for path in sorted((adapter.skill_root / "semantic/contracts").glob("*.json")):
            before = path.read_bytes()
            payload = _replace_json(json.loads(before), names)
            for contract in payload.get("contracts", []):
                source = adapter.skill_root / contract["source_path"]
                content = writes.get(source, source.read_bytes() if source.exists() else None)
                if content is None:
                    raise UsageError("Contract points to missing migrated source: " + str(source))
                # Only rebind evidence actually changed by this reviewed migration.
                if source in writes:
                    contract["source_sha256"] = digest(content)
            if payload != json.loads(before):
                writes[path] = encode(payload)
    reads = source_paths(root, targets) | set(writes) | generated_paths(targets) | mapping_paths
    # Bind all inputs of the shared boundary/physical catalog, without editing them.
    for metadata in root.glob("*/metadata.json"):
        value = json.loads(metadata.read_text(encoding="utf-8"))
        if value.get("semantic_manifest") == "semantic/domain_manifest.json":
            other = SimpleNamespace(skill_root=metadata.parent)
            reads.update(source_paths(root, [other]))
    # Bind implementation and maintenance programs too, not just business documents.
    reads.update(p for p in (root / "_shared/text2sql_core/text2sql_core").glob("*.py"))
    scripts = root / "usql-web-query-operator/scripts"
    reads.update(scripts / name for name in (
        "usql_web_query/commands/temp_table_knowledge.py", "usql_web_query/data_center_knowledge.py",
        "usql_web_query/data_center.py", "usql_web_query/query_auth.py", "usql_web_query/temp_table_upload.py",
        "usql_web_query/cli.py", "_shared/domain_adapters.py", "_shared/browser.py", "_shared/auth.py",
        "_shared/config.py", "_shared/env.py", "_shared/errors.py", "_shared/fs_utils.py"))
    reads.update((root / "usql-web-query-operator/scripts/usql_web_query/temp_table_knowledge.py", root / "scripts/validate_text2sql_stack.py", root / "scripts/build_text2sql_catalog.py"))
    for path in reads:
        safe_path(root, path.relative_to(root).as_posix())
    plan = {"artifact_type": PLAN_TYPE, "schema_version": "1.0.0", "request": request,
            "catalog": {**{r["new_table"]: catalog[r["new_table"]] for r in mappings},
                        "production_sql": catalog.get("production_sql", {})},
            "read_set": {p.relative_to(root).as_posix(): file_hash(p) for p in sorted(reads)},
            "mutations": [{"path": p.relative_to(root).as_posix(), "before_sha256": file_hash(p),
                           "content": value.decode("utf-8") if value is not None else None,
                           "after_sha256": digest(value) if value is not None else None} for p, value in sorted(writes.items())],
            "targets": sorted(by_target)}
    plan["plan_sha256"] = digest(plan)
    return plan


def maintenance(root: Path, adapters: list, log_dir: Path, journal: dict, snapshots: dict) -> list[dict]:
    core = root / "_shared/text2sql_core"
    sys.path.insert(0, str(core))
    from text2sql_core.builder import build_outputs
    from text2sql_core.reverse_index import render_reverse_indexes

    def write_generated(path, content):
        before = snapshots[path]
        if file_hash(path) != (digest(before) if before is not None else None):
            raise UsageError("Generated output drifted before regeneration: " + str(path))
        journal[path] = digest(content)
        _atomic_write_bytes(path, content)

    for adapter in adapters:
        for name, text in render_reverse_indexes(adapter.skill_root).items():
            write_generated(adapter.skill_root / "knowledge/reverse_index" / name, text.encode("utf-8"))
    for path, text in build_outputs(root).items():
        content = text.encode("utf-8")
        if path in snapshots:
            write_generated(path, content)
        elif file_hash(path) != digest(content):
            raise UsageError("An unrelated domain catalog is stale; refusing an out-of-scope rewrite: " + str(path))
    result = subprocess.run([sys.executable, "scripts/validate_text2sql_stack.py"], cwd=root,
                            capture_output=True, encoding="utf-8", errors="strict")
    log = log_dir / "stack.log"
    log.write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode:
        raise UsageError("Mandatory migration stack failed; see " + str(log))
    return [{"name": "stack", "returncode": 0, "log": str(log)}]


def apply_plan(root: Path, plan: dict, expected: str, catalog: dict, artifacts: Path, *, maintain=maintenance) -> dict:
    root = root.resolve()
    if plan.get("artifact_type") != PLAN_TYPE or digest({k: v for k, v in plan.items() if k != "plan_sha256"}) != expected or plan.get("plan_sha256") != expected:
        raise UsageError("Exact reviewed migration Plan Hash required.")
    artifacts = artifacts.resolve()
    if artifacts.is_relative_to(root) or artifacts.exists():
        raise UsageError("Use a new runtime artifacts directory outside skills.")
    adapters = adapters_by_target(load_domain_adapters(skills_root=root))
    selected = [adapters[name] for name in plan["targets"]]
    lock_plans = [SimpleNamespace(target=SimpleNamespace(root=a.skill_root)) for a in selected]
    with data_center_apply_lock(lock_plans):
        for relative, before in plan["read_set"].items():
            if file_hash(safe_path(root, relative)) != before:
                raise UsageError("Migration source Hash drift: " + relative)
        if build_plan(root, plan["request"], catalog) != plan:
            raise UsageError("Migration plan, live table identity or reviewed content drifted.")
        artifacts.mkdir(parents=True)
        touched = {safe_path(root, m["path"]) for m in plan["mutations"]} | generated_paths(selected)
        snapshots = {p: p.read_bytes() if p.exists() else None for p in touched}
        with zipfile.ZipFile(artifacts / "baseline.zip", "x", zipfile.ZIP_DEFLATED) as backup:
            for path, content in sorted(snapshots.items()):
                if content is not None:
                    backup.writestr(path.relative_to(root).as_posix(), content)
        receipt = {"artifact_type": "TempTableKnowledgeMigrationReceipt", "plan_sha256": expected,
                   "ok": False, "backup": str(artifacts / "baseline.zip"), "remote_writes": 0, "recovery": "not_needed"}
        applied = {}
        try:
            for item in plan["mutations"]:
                path = safe_path(root, item["path"])
                if file_hash(path) != item["before_sha256"]:
                    raise UsageError("Pre-write Hash drift: " + item["path"])
                applied[path] = item["after_sha256"]
                if item["content"] is None:
                    path.unlink()
                else:
                    _atomic_write_bytes(path, item["content"].encode("utf-8"))
            receipt["maintenance"] = maintain(root, selected, artifacts, applied, snapshots)
            for path, sha in applied.items():
                if file_hash(path) != sha:
                    raise UsageError("Migration write readback drift: " + str(path))
            for relative, sha in plan["read_set"].items():
                path = safe_path(root, relative)
                if path not in applied and file_hash(path) != sha:
                    raise UsageError("Unmodified migration evidence changed during validation: " + relative)
            receipt.update(ok=True, changed_files=[m["path"] for m in plan["mutations"]])
        except BaseException as exc:
            conflicts = [str(p) for p, sha in applied.items()
                         if file_hash(p) not in {sha, digest(snapshots[p]) if snapshots[p] is not None else None}]
            for path in applied:
                content = snapshots[path]
                if str(path) in conflicts:
                    continue
                if content is None:
                    path.unlink(missing_ok=True)
                else:
                    _atomic_write_bytes(path, content)
            restored = all(file_hash(p) == (digest(b) if b is not None else None) for p, b in snapshots.items())
            receipt.update(error=str(exc), recovery="restored" if restored else "blocked_concurrent_change", conflicts=conflicts)
            (artifacts / "receipt.json").write_bytes(encode(receipt))
            raise UsageError("Migration failed; recovery=" + receipt["recovery"] + "; " + str(exc)) from exc
        (artifacts / "receipt.json").write_bytes(encode(receipt))
        return receipt
