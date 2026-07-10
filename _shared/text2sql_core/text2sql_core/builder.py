"""Build deterministic domain manifests and a neutral physical catalog."""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from .contracts import CONTRACT_FILES, ContractRegistry


SCHEMA_VERSION = "2.0.0"
DOMAIN_CONFIG = {
    "market_consultant": {
        "skill": "sql-query-writer-for-dashboard",
        "name": "市场顾问部",
        "isolated_from": "qingcheng",
    },
    "qingcheng": {
        "skill": "qingcheng-dashboard-sql",
        "name": "青橙项目部",
        "isolated_from": "market_consultant",
    },
}
ENTITY_FOLDERS = {
    "tables": "tables",
    "temp_tables": "temp_tables",
    "metrics": "metrics",
    "dashboards": "dashboards",
    "dashboard_web_profiles": "dashboard_web_profiles",
    "joins": "joins",
    "sql_patterns": "sql_patterns",
    "pitfalls": "pitfalls",
    "reverse_index": "reverse_index",
    "update_log": "update_log",
}
RAW_SQL_REFERENCE_RE = re.compile(r"resources/raw_sql/([A-Za-z0-9_.-]+\.sql)")
IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
TYPE_RE = re.compile(
    r"^(?:string|varchar(?:\([^)]*\))?|char(?:\([^)]*\))?|bigint|integer|int|smallint|tinyint|double|float|real|decimal(?:\([^)]*\))?|boolean|date|timestamp|datetime|array(?:<.*>)?|map(?:<.*>)?|row(?:\(.*\))?)$",
    re.IGNORECASE,
)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _first_heading(text: str, fallback: str) -> str:
    for line in text.lstrip("\ufeff").splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return fallback


def _category(path: Path, skill_root: Path) -> str:
    relative = path.relative_to(skill_root).as_posix()
    if relative.startswith("resources/raw_sql/"):
        return "raw_sql"
    if relative.startswith("knowledge/"):
        parts = Path(relative).parts
        if len(parts) > 2:
            if parts[1] == "tables" and path.name.lower().startswith("temp_table."):
                return "temp_tables"
            return next((key for key, folder in ENTITY_FOLDERS.items() if parts[1] == folder), "governance")
        return "governance"
    return "governance"


def _table_name_from_doc(path: Path, category: str) -> str | None:
    if category not in {"tables", "temp_tables"}:
        return None
    name = path.name.removesuffix(".md")
    return name if "." in name else None


def _known_tables(repo_root: Path) -> set[str]:
    names: set[str] = set()
    for config in DOMAIN_CONFIG.values():
        skill_root = repo_root / str(config["skill"])
        for folder in ("tables", "temp_tables"):
            for path in (skill_root / "knowledge" / folder).glob("*.md"):
                name = path.name.removesuffix(".md")
                if "." in name:
                    names.add(name.lower())
    return names


def _extract_table_refs(text: str, known_tables: set[str]) -> list[str]:
    lowered = text.lower()
    return sorted(table for table in known_tables if re.search(rf"(?<![A-Za-z0-9_]){re.escape(table)}(?![A-Za-z0-9_])", lowered))


def _extract_raw_sql_refs(text: str, existing: set[str]) -> list[str]:
    found = {match.group(1) for match in RAW_SQL_REFERENCE_RE.finditer(text)}
    return sorted(name for name in found if name in existing)


def _source_files(skill_root: Path) -> list[Path]:
    files = list((skill_root / "knowledge").rglob("*.md"))
    raw_root = skill_root / "resources" / "raw_sql"
    if raw_root.exists():
        files.extend(path for path in raw_root.rglob("*") if path.is_file())
    return sorted(files, key=lambda path: path.relative_to(skill_root).as_posix())


def _entity_id(domain: str, category: str, source_path: str) -> str:
    slug = source_path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    return f"{domain}:{category}:{slug}"


def _build_domain_manifest(
    repo_root: Path,
    domain: str,
    known_tables: set[str],
    registry: ContractRegistry,
) -> dict[str, Any]:
    config = DOMAIN_CONFIG[domain]
    skill_root = repo_root / str(config["skill"])
    raw_names = {path.name for path in (skill_root / "resources" / "raw_sql").glob("*.sql")}
    entities: dict[str, list[dict[str, Any]]] = defaultdict(list)
    inventory: list[dict[str, Any]] = []
    table_to_sources: dict[str, list[str]] = defaultdict(list)
    raw_sql_to_sources: dict[str, list[str]] = defaultdict(list)
    for path in _source_files(skill_root):
        source_path = path.relative_to(skill_root).as_posix()
        category = _category(path, skill_root)
        text = _read_text(path) if path.suffix.lower() in {".md", ".sql", ".txt"} else ""
        table_refs = _extract_table_refs(text, known_tables)
        raw_sql_refs = _extract_raw_sql_refs(text, raw_names)
        entry: dict[str, Any] = {
            "id": _entity_id(domain, category, source_path),
            "source_path": source_path,
            "sha256": _sha256(path),
            "bytes": path.stat().st_size,
            "title": _first_heading(text, path.stem),
            "table_refs": table_refs,
            "raw_sql_refs": raw_sql_refs,
            "status": "pending_confirmation" if "待人工确认" in text else "documented",
        }
        table_name = _table_name_from_doc(path, category)
        if table_name:
            entry["table_name"] = table_name
        entry["aliases"] = sorted(
            {
                alias
                for alias in (path.stem, entry["title"], table_name)
                if alias
            }
        )
        inventory.append(
            {
                "source_path": source_path,
                "sha256": entry["sha256"],
                "bytes": entry["bytes"],
                "category": category,
            }
        )
        entities[category].append(entry)
        for table_ref in table_refs:
            table_to_sources[table_ref].append(source_path)
        for raw_ref in raw_sql_refs:
            raw_sql_to_sources[raw_ref].append(source_path)
    counts = {category: len(items) for category, items in sorted(entities.items())}
    own_temps = {
        item["table_name"]
        for item in entities.get("temp_tables", [])
        if item.get("table_name")
    }
    other_domain = str(config["isolated_from"])
    other_skill = repo_root / str(DOMAIN_CONFIG[other_domain]["skill"])
    other_temp_paths = list((other_skill / "knowledge" / "temp_tables").glob("*.md"))
    other_temp_paths.extend(
        path
        for path in (other_skill / "knowledge" / "tables").glob("temp_table.*.md")
    )
    other_temps = {
        path.name.removesuffix(".md")
        for path in other_temp_paths
        if path.name.lower().startswith("temp_table.")
    }
    exclusive_own = sorted(own_temps - other_temps)
    forbidden = sorted(other_temps - own_temps)
    return {
        "schema_version": SCHEMA_VERSION,
        "domain": {
            "id": domain,
            "name": config["name"],
            "skill": config["skill"],
            "isolated_from": [other_domain],
        },
        "authority": {
            "business_semantics": "domain_markdown_and_raw_sql",
            "semantic_contract_role": "hash_bound_machine_interpretation_for_confirmed_entries_only",
            "generated_manifest_role": "routing_and_validation_index",
            "physical_catalog_role": "neutral_physical_facts_only",
        },
        "progressive_disclosure": {
            "forward": [
                "semantic/domain_manifest.json",
                "semantic/generated/contract_index.json",
                "knowledge/quick_reference.md",
                "knowledge/decision_tree.md",
                "targeted domain documents",
                "resources/raw_sql/<selected evidence>.sql",
            ],
            "reverse": sorted(item["source_path"] for item in entities.get("reverse_index", [])),
        },
        "boundary": {
            "domain_local_temp_tables": sorted(own_temps),
            "exclusive_temp_tables": exclusive_own,
            "forbidden_temp_tables": forbidden,
            "same_name_temp_tables_require_domain_evidence": sorted(own_temps & other_temps),
            "forbid_cross_domain_metric_defaulting": True,
            "cross_department_comparison_requires_two_specs": True,
        },
        "counts": {
            "knowledge_files": sum(1 for item in inventory if item["source_path"].startswith("knowledge/")),
            "raw_sql_files": sum(1 for item in inventory if item["source_path"].startswith("resources/raw_sql/")),
            "by_category": counts,
        },
        "semantic_contracts": {
            "schema_version": "2.0.0",
            "index_path": "semantic/generated/contract_index.json",
            "counts": {
                kind: len(values)
                for kind, values in sorted(registry.contracts.items())
            },
            "confirmed_counts": {
                kind: sum(item.get("status") == "confirmed" for item in values)
                for kind, values in sorted(registry.contracts.items())
            },
            "source_files": [
                {
                    "source_path": f"semantic/contracts/{filename}",
                    "sha256": _sha256(skill_root / "semantic" / "contracts" / filename),
                }
                for filename in CONTRACT_FILES.values()
            ],
        },
        "entities": {category: items for category, items in sorted(entities.items())},
        "reverse_lookup": {
            "table_to_sources": {key: sorted(set(value)) for key, value in sorted(table_to_sources.items())},
            "raw_sql_to_sources": {key: sorted(set(value)) for key, value in sorted(raw_sql_to_sources.items())},
        },
        "source_inventory": inventory,
    }


def _markdown_rows(text: str) -> Iterable[list[str]]:
    for line in text.splitlines():
        stripped = line.strip()
        if not (stripped.startswith("|") and stripped.endswith("|")):
            continue
        cells = [cell.strip().strip("`") for cell in stripped.strip("|").split("|")]
        if any(cell and set(cell) <= {"-", ":"} for cell in cells):
            continue
        yield cells


def _extract_columns(path: Path) -> dict[str, str]:
    columns: dict[str, str] = {}
    for cells in _markdown_rows(_read_text(path)):
        if len(cells) < 2:
            continue
        name, data_type = cells[0], cells[1].lower()
        if IDENTIFIER_RE.fullmatch(name) and TYPE_RE.fullmatch(data_type):
            columns.setdefault(name.lower(), data_type)
    return columns


def _build_physical_catalog(repo_root: Path, manifests: dict[str, dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[tuple[str, Path, dict[str, str]]]] = defaultdict(list)
    for domain, config in DOMAIN_CONFIG.items():
        skill_root = repo_root / str(config["skill"])
        for path in sorted((skill_root / "knowledge" / "tables").glob("*.md")):
            table_name = path.name.removesuffix(".md").lower()
            if table_name.startswith("temp_table."):
                continue
            grouped[table_name].append((domain, path, _extract_columns(path)))
    tables: list[dict[str, Any]] = []
    for table_name, sources in sorted(grouped.items()):
        field_sources: dict[str, list[dict[str, str]]] = defaultdict(list)
        for domain, path, columns in sources:
            skill_root = repo_root / str(DOMAIN_CONFIG[domain]["skill"])
            for name, data_type in columns.items():
                field_sources[name].append(
                    {
                        "domain": domain,
                        "type": data_type,
                        "source_path": f"{skill_root.name}/{path.relative_to(skill_root).as_posix()}",
                    }
                )
        columns: list[dict[str, Any]] = []
        conflicts: list[dict[str, Any]] = []
        for name, provenance in sorted(field_sources.items()):
            types = sorted({item["type"] for item in provenance})
            columns.append({"name": name, "types": types, "provenance": provenance})
            if len(types) > 1:
                conflicts.append({"field": name, "types": types, "provenance": provenance})
        source_docs = []
        for domain, path, _ in sources:
            skill_root = repo_root / str(DOMAIN_CONFIG[domain]["skill"])
            source_docs.append(
                {
                    "domain": domain,
                    "source_path": f"{skill_root.name}/{path.relative_to(skill_root).as_posix()}",
                    "sha256": _sha256(path),
                }
            )
        column_names = {item["name"] for item in columns}
        tables.append(
            {
                "id": f"physical:{table_name}",
                "name": table_name,
                "domains": sorted(domain for domain, _, _ in sources),
                "source_docs": source_docs,
                "columns": columns,
                "partition_candidates": [name for name in ("dt", "hour") if name in column_names],
                "conflicts": conflicts,
                "business_semantics_excluded": True,
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "scope": "neutral_physical_tables_only",
        "excluded": [
            "metrics",
            "dashboards",
            "temporary_tables",
            "business_join_semantics",
            "department_range_values",
            "channel_and_period_rules",
            "raw_sql",
        ],
        "domains": sorted(manifests),
        "tables": tables,
    }


def build_outputs(repo_root: Path) -> dict[Path, str]:
    known_tables = _known_tables(repo_root)
    registries: dict[str, ContractRegistry] = {}
    manifests: dict[str, dict[str, Any]] = {}
    for domain in sorted(DOMAIN_CONFIG):
        skill = str(DOMAIN_CONFIG[domain]["skill"])
        registry = ContractRegistry.load(repo_root / skill, domain)
        if not registry.ok:
            messages = "; ".join(item.message for item in registry.diagnostics if item.severity == "error")
            raise ValueError(f"invalid {domain} semantic contracts: {messages}")
        registries[domain] = registry
        manifests[domain] = _build_domain_manifest(repo_root, domain, known_tables, registry)
    outputs: dict[Path, str] = {}
    for domain, manifest in manifests.items():
        skill = str(DOMAIN_CONFIG[domain]["skill"])
        outputs[repo_root / skill / "semantic" / "domain_manifest.json"] = _json_text(manifest)
        outputs[repo_root / skill / "semantic" / "generated" / "contract_index.json"] = _json_text(
            registries[domain].generated_index()
        )
    physical = _build_physical_catalog(repo_root, manifests)
    outputs[repo_root / "_shared" / "text2sql_core" / "catalog" / "physical_catalog.json"] = _json_text(physical)
    return outputs


def _json_text(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n"


def write_outputs(outputs: dict[Path, str]) -> None:
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")


def check_outputs(outputs: dict[Path, str]) -> list[str]:
    failures: list[str] = []
    for path, expected in outputs.items():
        if not path.exists():
            failures.append(f"missing generated file: {path}")
        elif path.read_text(encoding="utf-8") != expected:
            failures.append(f"stale generated file: {path}")
    return failures
