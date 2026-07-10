#!/usr/bin/env python3
"""Check the qingcheng-dashboard-sql skill package structure."""

from __future__ import annotations

import json
import hashlib
import re
import sys
from datetime import date, time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DIRS = [
    "agents",
    "docs",
    "examples",
    "knowledge/tables",
    "knowledge/temp_tables",
    "knowledge/dashboards",
    "knowledge/dashboard_web_profiles",
    "knowledge/metrics",
    "knowledge/joins",
    "knowledge/sql_patterns",
    "knowledge/reverse_index",
    "knowledge/update_log",
    "resources/raw_sql",
    "resources/raw_pdfs",
    "resources/raw_images",
    "resources/rendered_pages",
    "scripts",
    "semantic",
    "semantic/contracts",
    "semantic/evals",
    "semantic/generated",
]

REQUIRED_FILES = [
    "SKILL.md",
    "metadata.json",
    "docs/USAGE_PROMPTS.md",
    "knowledge/00_global_rules.md",
    "knowledge/quick_reference.md",
    "knowledge/01_table_index.md",
    "knowledge/02_query_engine_presto.md",
    "knowledge/03_range_limit_rules.md",
    "knowledge/04_qingcheng_project_profile.md",
    "knowledge/decision_tree.md",
    "knowledge/tables/_table_template.md",
    "knowledge/temp_tables/_temp_table_template.md",
    "knowledge/dashboards/_dashboard_template.md",
    "knowledge/dashboard_web_profiles/README.md",
    "knowledge/metrics/_metric_template.md",
    "knowledge/joins/common_join_keys.md",
    "knowledge/joins/table_relationships.md",
    "knowledge/sql_patterns/dashboard_query_patterns.md",
    "knowledge/sql_patterns/exploratory_query_patterns.md",
    "knowledge/sql_patterns/presto_date_partition_patterns.md",
    "knowledge/sql_patterns/qingcheng_scope_patterns.md",
    "knowledge/reverse_index/field_to_metrics.md",
    "knowledge/reverse_index/metric_to_raw_sql.md",
    "knowledge/reverse_index/table_to_dashboards.md",
    "knowledge/reverse_index/join_risk_index.md",
    "knowledge/update_log/changelog.md",
    "scripts/build_reverse_indexes.py",
    "scripts/check_skill_integrity.py",
    "scripts/ingest_dashboard_sql.py",
    "scripts/validate_sql_rules.py",
    "scripts/text2sql.py",
    "semantic/domain_manifest.json",
    "semantic/contracts/metric_contracts.json",
    "semantic/contracts/dimension_contracts.json",
    "semantic/contracts/join_contracts.json",
    "semantic/contracts/scope_contracts.json",
    "semantic/evals/resolution_cases.json",
    "semantic/generated/contract_index.json",
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

TEMP_TABLE_SECTIONS = [
    "## 1. 临时表用途",
    "## 2. 来源和刷新方式",
    "## 3. 数据粒度",
    "## 4. 字段清单",
    "## 5. 适用看板",
    "## 6. join key",
    "## 7. 不可复用边界",
    "## 8. 待确认事项",
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

    if metadata.get("name") != "qingcheng-dashboard-sql":
        fail("metadata.name must be qingcheng-dashboard-sql", failures)
    if metadata.get("query_engine") != "Presto":
        fail("metadata.query_engine must be Presto", failures)
    if metadata.get("business_domain") != "青橙项目部":
        fail("metadata.business_domain must be 青橙项目部", failures)
    if metadata.get("domain_id") != "qingcheng":
        fail("metadata.domain_id must be qingcheng", failures)
    if metadata.get("entrypoint") != "SKILL.md":
        fail("metadata.entrypoint must be SKILL.md", failures)
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
    if metadata.get("consultant_alias_policy") != "require_section_or_performance_disambiguation":
        fail("metadata.consultant_alias_policy must require consultant disambiguation", failures)
    required_capabilities = {
        "resolve",
        "plan",
        "compile_single_base_table",
        "probe_read_only",
        "dataset_spec_read_only",
    }
    if set(metadata.get("p2_capabilities", [])) != required_capabilities:
        fail("metadata.p2_capabilities must declare the complete P2 surface", failures)
    if metadata.get("automatic_compile_flag_required") is not True:
        fail("metadata.automatic_compile_flag_required must be true", failures)

    for rel in metadata.get("knowledge_dirs", []):
        if not (ROOT / rel).is_dir():
            fail(f"metadata knowledge dir missing: {rel}", failures)
    contract_dir = metadata.get("semantic_contract_dir")
    if not contract_dir or not (ROOT / contract_dir).resolve().is_dir():
        fail(f"metadata semantic_contract_dir target missing: {contract_dir}", failures)
    for key in (
        "semantic_manifest",
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
        if not rel or not (ROOT / rel).resolve().is_file():
            fail(f"metadata {key} target missing: {rel}", failures)
    ok("metadata.json")


def check_semantic_contracts(failures: list[str]) -> None:
    core_root = (ROOT.parent / "_shared" / "text2sql_core").resolve()
    if str(core_root) not in sys.path:
        sys.path.insert(0, str(core_root))
    try:
        from text2sql_core.contracts import ContractRegistry
        from text2sql_core.evaluator import evaluate_resolution_cases
    except Exception as exc:  # noqa: BLE001
        fail(f"cannot load Text2SQL contract validators: {exc}", failures)
        return

    registry = ContractRegistry.load(ROOT, "qingcheng")
    contract_errors = [item for item in registry.diagnostics if item.severity == "error"]
    for item in contract_errors:
        fail(f"semantic contract {item.code}: {item.message}", failures)
    if contract_errors:
        return

    expected_consultant_ids = [
        "qingcheng:dimension:performance_consultant",
        "qingcheng:dimension:section_consultant",
    ]
    generated = registry.generated_index()
    if generated.get("alias_collisions", {}).get("顾问") != expected_consultant_ids:
        fail("consultant alias must remain ambiguous between section and performance consultants", failures)

    index_path = ROOT / "semantic" / "generated" / "contract_index.json"
    try:
        stored_index = json.loads(read_text(index_path))
    except Exception as exc:  # noqa: BLE001
        fail(f"semantic/generated/contract_index.json is not valid JSON: {exc}", failures)
    else:
        if stored_index != generated:
            fail("semantic/generated/contract_index.json is stale; rebuild the Text2SQL catalog", failures)
        else:
            ok(f"semantic contracts and generated index: {len(registry.values())}")

    eval_result = evaluate_resolution_cases(ROOT, "qingcheng")
    if not eval_result.get("ok"):
        for item in eval_result.get("failures", []):
            fail(f"semantic eval failed: {item}", failures)
    else:
        ok(f"semantic resolution evals: {eval_result['passed']}/{eval_result['total']}")


def check_domain_manifest(failures: list[str]) -> None:
    path = ROOT / "semantic" / "domain_manifest.json"
    try:
        manifest = json.loads(read_text(path))
    except Exception as exc:  # noqa: BLE001
        fail(f"semantic/domain_manifest.json is not valid JSON: {exc}", failures)
        return
    if manifest.get("domain", {}).get("id") != "qingcheng":
        fail("semantic manifest domain must be qingcheng", failures)
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


def check_markdown_docs(folder: str, sections: list[str], failures: list[str]) -> None:
    doc_dir = ROOT / folder
    files = sorted(p for p in doc_dir.glob("*.md") if not p.name.startswith("_"))
    if not files:
        warn(f"{folder} has no ingested markdown files yet")
        return

    for path in files:
        text = read_text(path)
        missing = [section for section in sections if section not in text]
        if missing:
            fail(f"{path.relative_to(ROOT)} missing sections: {', '.join(missing)}", failures)
        if "待人工确认" in text:
            warn(f"{path.relative_to(ROOT)} contains pending manual-confirmation items")
    ok(f"{folder} docs checked: {len(files)}")


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
    check_markdown_docs("knowledge/tables", TABLE_SECTIONS, failures)
    check_markdown_docs("knowledge/temp_tables", TEMP_TABLE_SECTIONS, failures)
    check_changelog_order(failures)

    if failures:
        print(f"\nSkill integrity check failed: {len(failures)} issue(s).")
        return 1

    print("\nSkill integrity check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
