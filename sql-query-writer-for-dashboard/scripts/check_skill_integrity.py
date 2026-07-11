#!/usr/bin/env python3
"""Check the sql-query-writer-for-dashboard skill package structure."""

from __future__ import annotations

import json
import hashlib
import re
import sys
from datetime import date, time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "SKILL.md",
    "README.md",
    "metadata.json",
    "docs/USAGE_PROMPTS.md",
    "references/quick_reference.md",
    "references/decision_tree.md",
    "knowledge/00_global_rules.md",
    "knowledge/01_table_index.md",
    "knowledge/02_query_engine_presto.md",
    "knowledge/03_range_limit_rules.md",
    "knowledge/quick_reference.md",
    "knowledge/decision_tree.md",
    "knowledge/dashboard_web_profiles/README.md",
    "knowledge/joins/common_join_keys.md",
    "knowledge/joins/table_relationships.md",
    "knowledge/reverse_index/field_to_metrics.md",
    "knowledge/reverse_index/metric_to_raw_sql.md",
    "knowledge/reverse_index/table_to_dashboards.md",
    "knowledge/reverse_index/join_risk_index.md",
    "knowledge/update_log/changelog.md",
    "scripts/build_reverse_indexes.py",
    "scripts/extract_pdf_to_md.py",
    "scripts/normalize_schema_md.py",
    "scripts/ingest_dashboard_sql.py",
    "scripts/validate_sql_rules.py",
    "scripts/text2sql.py",
    "semantic/domain_manifest.json",
    "semantic/current_model_bindings.json",
    "semantic/contracts/metric_contracts.json",
    "semantic/contracts/dimension_contracts.json",
    "semantic/contracts/join_contracts.json",
    "semantic/contracts/scope_contracts.json",
    "semantic/evals/resolution_cases.json",
    "semantic/generated/contract_index.json",
]

REQUIRED_DIRS = [
    "examples",
    "knowledge/tables",
    "knowledge/dashboards",
    "knowledge/dashboard_web_profiles",
    "knowledge/metrics",
    "knowledge/joins",
    "knowledge/sql_patterns",
    "knowledge/reverse_index",
    "resources/raw_pdfs",
    "resources/raw_sql",
    "resources/raw_images",
    "resources/rendered_pages",
    "references",
    "scripts",
    "semantic",
    "semantic/contracts",
    "semantic/evals",
    "semantic/generated",
]

TABLE_SECTIONS = [
    "## 1. 中文名称",
    "## 2. 表用途",
    "## 3. 数据粒度",
    "## 4. 查询引擎",
    "## 5. 分区字段",
    "## 6. 强制范围限定字段",
    "## 7. 字段清单",
    "## 8. 常用过滤条件",
    "## 9. 常用 join key",
    "## 10. 常用 SQL 片段",
    "## 11. 注意事项",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)
    print(f"[FAIL] {message}")


def warn(message: str) -> None:
    print(f"[WARN] {message}")


def ok(message: str) -> None:
    print(f"[OK] {message}")


def check_metadata(failures: list[str]) -> None:
    metadata_path = ROOT / "metadata.json"
    try:
        metadata = json.loads(read_text(metadata_path))
    except Exception as exc:  # noqa: BLE001
        fail(f"metadata.json is not valid JSON: {exc}", failures)
        return

    if metadata.get("name") != "sql-query-writer-for-dashboard":
        fail("metadata.name must be sql-query-writer-for-dashboard", failures)
    if metadata.get("query_engine") != "Presto":
        fail("metadata.query_engine must be Presto", failures)
    if metadata.get("entrypoint") != "SKILL.md":
        fail("metadata.entrypoint must be SKILL.md", failures)
    if metadata.get("domain_id") != "market_consultant":
        fail("metadata.domain_id must be market_consultant", failures)
    if metadata.get("business_domain") != "市场顾问部":
        fail("metadata.business_domain must be 市场顾问部", failures)
    if not metadata.get("forbid_cross_domain_defaulting"):
        fail("metadata.forbid_cross_domain_defaulting must be true", failures)
    if metadata.get("semantic_contract_version") != "2.0.0":
        fail("metadata.semantic_contract_version must be 2.0.0", failures)
    if metadata.get("query_spec_schema_version") != "2.0.0":
        fail("metadata.query_spec_schema_version must be 2.0.0", failures)
    if metadata.get("query_plan_schema_version") != "2.0.0":
        fail("metadata.query_plan_schema_version must be 2.0.0", failures)
    if metadata.get("pending_contract_policy") != "block_production_compilation":
        fail("metadata.pending_contract_policy must block production compilation", failures)
    expected_capabilities = {
        "resolve",
        "plan",
        "compile_single_base_table",
        "probe_read_only",
        "dataset_spec_read_only",
    }
    if set(metadata.get("p2_capabilities", [])) != expected_capabilities:
        fail("metadata.p2_capabilities must declare the complete supported P2 surface", failures)
    if metadata.get("automatic_compile_flag_required") is not True:
        fail("metadata.automatic_compile_flag_required must be true", failures)
    for rel in metadata.get("knowledge_dirs", []):
        if not (ROOT / rel).is_dir():
            fail(f"metadata knowledge dir missing: {rel}", failures)
    for key in (
        "semantic_manifest",
        "semantic_contract_dir",
        "semantic_contract_index",
        "semantic_eval_cases",
        "semantic_contract_schema",
        "text2sql_cli",
        "physical_catalog",
        "query_spec_schema",
        "query_plan_schema",
        "dashboard_dataset_spec_schema",
    ):
        rel = metadata.get(key)
        target = (ROOT / rel).resolve() if rel else None
        expected_type_ok = target.is_dir() if key == "semantic_contract_dir" and target else target.is_file() if target else False
        if not rel or not expected_type_ok:
            fail(f"metadata {key} target missing: {rel}", failures)
    ok("metadata.json")


def check_semantic_contracts(failures: list[str]) -> None:
    core_root = (ROOT.parent / "_shared" / "text2sql_core").resolve()
    if not core_root.is_dir():
        fail(f"shared Text2SQL core is missing: {core_root}", failures)
        return
    sys.path.insert(0, str(core_root))
    try:
        from text2sql_core.contracts import ContractRegistry
        from text2sql_core.evaluator import evaluate_resolution_cases
    except Exception as exc:  # noqa: BLE001
        fail(f"cannot import shared semantic contract validators: {exc}", failures)
        return

    registry = ContractRegistry.load(ROOT, "market_consultant")
    errors = [item for item in registry.diagnostics if item.severity == "error"]
    if errors:
        for item in errors:
            fail(f"semantic contract {item.code}: {item.message}", failures)
        return

    expected_ambiguity = [
        "market_consultant:metric:same_period_conversion_subject_count",
        "market_consultant:metric:same_period_conversion_users",
    ]
    generated_index = registry.generated_index()
    if generated_index.get("alias_collisions", {}).get("当期转化") != expected_ambiguity:
        fail("当期转化 alias must remain ambiguous between user and subject-count metrics", failures)

    generated_path = ROOT / "semantic" / "generated" / "contract_index.json"
    try:
        actual_index = json.loads(read_text(generated_path))
    except Exception as exc:  # noqa: BLE001
        fail(f"semantic/generated/contract_index.json is not valid JSON: {exc}", failures)
        return
    expected_index = generated_index
    if actual_index != expected_index:
        fail(
            "semantic/generated/contract_index.json is stale; run repository scripts/build_text2sql_catalog.py",
            failures,
        )
    else:
        counts = expected_index.get("counts", {})
        ok(
            "semantic contracts and generated index "
            f"(metrics={counts.get('metric', 0)}, dimensions={counts.get('dimension', 0)}, "
            f"joins={counts.get('join', 0)}, scopes={counts.get('scope', 0)})"
        )

    evaluation = evaluate_resolution_cases(ROOT, "market_consultant")
    if not evaluation.get("ok"):
        for item in evaluation.get("failures", []):
            fail(f"semantic resolution eval failed: {item}", failures)
    else:
        ok(f"semantic resolution evals: {evaluation.get('passed')}/{evaluation.get('total')}")


def check_domain_manifest(failures: list[str]) -> None:
    path = ROOT / "semantic" / "domain_manifest.json"
    try:
        manifest = json.loads(read_text(path))
    except Exception as exc:  # noqa: BLE001
        fail(f"semantic/domain_manifest.json is not valid JSON: {exc}", failures)
        return
    if manifest.get("domain", {}).get("id") != "market_consultant":
        fail("semantic manifest domain must be market_consultant", failures)
    inventory = {item.get("source_path"): item for item in manifest.get("source_inventory", [])}
    sources = sorted((ROOT / "knowledge").rglob("*.md"))
    sources.extend(sorted(path for path in (ROOT / "resources" / "raw_sql").rglob("*") if path.is_file()))
    expected = {source.relative_to(ROOT).as_posix() for source in sources}
    if set(inventory) != expected:
        fail("semantic manifest does not cover the exact knowledge/raw SQL source set", failures)
        return
    stale = []
    for source in sources:
        relative = source.relative_to(ROOT).as_posix()
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if inventory[relative].get("sha256") != digest:
            stale.append(relative)
    if stale:
        fail(f"semantic manifest has stale source hashes: {', '.join(stale)}", failures)
    else:
        ok("semantic manifest coverage and hashes")


def check_table_docs(failures: list[str]) -> None:
    table_dir = ROOT / "knowledge" / "tables"
    table_files = sorted(p for p in table_dir.glob("*.md") if not p.name.startswith("_") and p.name != "README.md")
    if not table_files:
        fail("knowledge/tables has no table markdown files", failures)
        return

    for path in table_files:
        text = read_text(path)
        missing = [section for section in TABLE_SECTIONS if section not in text]
        if missing:
            fail(f"{path.relative_to(ROOT)} missing sections: {', '.join(missing)}", failures)
        if "Presto" not in text:
            warn(f"{path.relative_to(ROOT)} does not mention Presto")
        if "待人工确认" in text:
            warn(f"{path.relative_to(ROOT)} contains pending manual-confirmation items")
    ok(f"table docs checked: {len(table_files)}")


def check_index_coverage(failures: list[str]) -> None:
    index_text = read_text(ROOT / "knowledge" / "01_table_index.md")
    # 2026-05-31: USQL status column removed in favor of Playwright Web automation.
    # The index no longer needs a per-table API-readability column.
    if "完整表名" not in index_text:
        fail("knowledge/01_table_index.md missing required table header column", failures)
    table_dir = ROOT / "knowledge" / "tables"
    missing = []
    for path in table_dir.glob("*.md"):
        if path.name.startswith("_") or path.name == "README.md":
            continue
        table_name = path.stem
        if table_name not in index_text:
            missing.append(table_name)
    if missing:
        fail(f"tables missing from knowledge/01_table_index.md: {', '.join(sorted(missing))}", failures)
    else:
        ok("table index coverage")


def check_channel_case_latest(failures: list[str]) -> None:
    stale_refs: list[str] = []
    knowledge_dir = ROOT / "knowledge"
    for path in knowledge_dir.rglob("*.md"):
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith("knowledge/update_log/"):
            continue
        for line_no, line in enumerate(read_text(path).splitlines(), start=1):
            if "market_channel_case_when_0522.sql" in line:
                stale_refs.append(f"{rel}:{line_no}")

    if stale_refs:
        fail(
            "non-changelog knowledge docs still reference market_channel_case_when_0522.sql; "
            f"use 0524 or explicitly mark historical old-version usage: {', '.join(stale_refs)}",
            failures,
        )
    else:
        ok("latest channel CASE references")


def check_changelog_order(failures: list[str]) -> None:
    changelog_path = ROOT / "knowledge" / "update_log" / "changelog.md"
    text = read_text(changelog_path)
    heading_re = re.compile(r"^## (\d{4}-\d{2}-\d{2})(?: (\d{2}:\d{2}:\d{2}))?", re.M)
    entries = list(heading_re.finditer(text))
    if not entries:
        fail("knowledge/update_log/changelog.md has no dated headings", failures)
        return

    prev_date: date | None = None
    latest_time_by_date: dict[date, time] = {}
    for match in entries:
        current_date = date.fromisoformat(match.group(1))
        current_time = time.fromisoformat(match.group(2)) if match.group(2) else None
        heading = match.group(0)

        if prev_date is not None and current_date < prev_date:
            fail(
                "knowledge/update_log/changelog.md must be chronological ascending; "
                f"out-of-order heading: {heading}",
                failures,
            )
            return

        if current_time is not None:
            latest_time = latest_time_by_date.get(current_date)
            if latest_time is not None and current_time < latest_time:
                fail(
                    "knowledge/update_log/changelog.md timed headings must be ascending within a date; "
                    f"out-of-order heading: {heading}",
                    failures,
                )
                return
            latest_time_by_date[current_date] = current_time

        prev_date = current_date

    ok("changelog chronological order")


def main() -> int:
    failures: list[str] = []

    for rel in REQUIRED_DIRS:
        if (ROOT / rel).is_dir():
            ok(rel)
        else:
            fail(f"missing dir: {rel}", failures)

    for rel in REQUIRED_FILES:
        if (ROOT / rel).is_file():
            ok(rel)
        else:
            fail(f"missing file: {rel}", failures)

    check_metadata(failures)
    check_domain_manifest(failures)
    check_semantic_contracts(failures)
    check_table_docs(failures)
    check_index_coverage(failures)
    check_channel_case_latest(failures)
    check_changelog_order(failures)

    if failures:
        print(f"\nSkill integrity check failed: {len(failures)} issue(s).")
        return 1

    print("\nSkill integrity check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
