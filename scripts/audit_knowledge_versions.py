"""Reject duplicate canonical versions and duplicate current knowledge ownership."""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DOMAIN_SKILLS = (
    "sql-query-writer-for-dashboard",
    "qingcheng-dashboard-sql",
)
CANONICAL_VERSION_PATTERNS = (
    re.compile(r"^(data_center_market_\d+)_(20\d{6})\.sql$"),
    re.compile(r"^(data_center_qingcheng_\d+)_(20\d{6})\.sql$"),
    re.compile(r"^(market_channel_case_when)_(?:20\d{6}|\d{4})\.sql$"),
)
STABLE_DATA_CENTER_PATTERNS = {
    "sql-query-writer-for-dashboard": re.compile(r"^data_center_market_(\d+)\.sql$"),
    "qingcheng-dashboard-sql": re.compile(r"^data_center_qingcheng_(\d+)\.sql$"),
}
LEGACY_DATA_CENTER_PATTERNS = {
    "sql-query-writer-for-dashboard": re.compile(r"^data_center_market_(\d+)_20\d{6}\.sql$"),
    "qingcheng-dashboard-sql": re.compile(r"^data_center_qingcheng_(\d+)_20\d{6}\.sql$"),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _duplicates_by_hash(paths: list[Path], root: Path) -> list[dict[str, Any]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for path in paths:
        groups[_sha256(path)].append(path.relative_to(root).as_posix())
    return [
        {"sha256": digest, "sources": sorted(sources)}
        for digest, sources in sorted(groups.items())
        if len(sources) > 1
    ]


def _canonical_family(name: str) -> str | None:
    for pattern in CANONICAL_VERSION_PATTERNS:
        match = pattern.match(name)
        if match:
            return match.group(1)
    return None


def audit_skill(skill_root: Path) -> dict[str, Any]:
    raw_sql = sorted(path for path in (skill_root / "resources" / "raw_sql").rglob("*") if path.is_file())
    knowledge = sorted((skill_root / "knowledge").rglob("*.md"))

    version_groups: dict[str, list[str]] = defaultdict(list)
    for path in raw_sql:
        family = _canonical_family(path.name)
        if family:
            version_groups[family].append(path.relative_to(skill_root).as_posix())
    duplicate_versions = [
        {"family": family, "sources": sorted(sources)}
        for family, sources in sorted(version_groups.items())
        if len(sources) > 1
    ]

    stable_pattern = STABLE_DATA_CENTER_PATTERNS[skill_root.name]
    legacy_pattern = LEGACY_DATA_CENTER_PATTERNS[skill_root.name]
    legacy_versioned_canonical_files = [
        path.relative_to(skill_root).as_posix()
        for path in raw_sql
        if legacy_pattern.match(path.name)
    ]
    stable_files = {
        stable_pattern.match(path.name).group(1): path
        for path in raw_sql
        if stable_pattern.match(path.name)
    }
    registry_issues = _audit_current_model_registry(skill_root, stable_files)

    contract_ids: dict[str, list[str]] = defaultdict(list)
    field_owners: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    for path in sorted((skill_root / "semantic" / "contracts").glob("*_contracts.json")):
        relative = path.relative_to(skill_root).as_posix()
        payload = json.loads(path.read_text(encoding="utf-8"))
        for contract in payload.get("contracts", []):
            contract_id = str(contract["id"])
            contract_ids[contract_id].append(relative)
            kind = str(contract.get("kind", ""))
            table = contract.get("table")
            field = contract.get("field")
            if table and field:
                field_owners[(kind, str(table), str(field))].append(contract_id)

    duplicate_contract_ids = [
        {"contract_id": contract_id, "sources": sorted(sources)}
        for contract_id, sources in sorted(contract_ids.items())
        if len(sources) > 1
    ]
    duplicate_field_owners = [
        {
            "kind": key[0],
            "table": key[1],
            "field": key[2],
            "contract_ids": sorted(contract_ids_for_field),
        }
        for key, contract_ids_for_field in sorted(field_owners.items())
        if len(set(contract_ids_for_field)) > 1
    ]

    result = {
        "duplicate_canonical_versions": duplicate_versions,
        "legacy_versioned_canonical_files": legacy_versioned_canonical_files,
        "current_model_registry_issues": registry_issues,
        "duplicate_raw_sql_content": _duplicates_by_hash(raw_sql, skill_root),
        "duplicate_knowledge_content": _duplicates_by_hash(knowledge, skill_root),
        "duplicate_contract_ids": duplicate_contract_ids,
        "duplicate_field_owners": duplicate_field_owners,
    }
    result["ok"] = not any(result.values())
    return result


def _audit_current_model_registry(skill_root: Path, stable_files: dict[str, Path]) -> list[dict[str, Any]]:
    path = skill_root / "semantic" / "current_model_bindings.json"
    if not path.exists():
        return [{"code": "MISSING_CURRENT_MODEL_REGISTRY", "path": path.relative_to(skill_root).as_posix()}]
    try:
        registry = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [{"code": "INVALID_CURRENT_MODEL_REGISTRY", "detail": str(exc)}]

    issues: list[dict[str, Any]] = []
    expected_domain = "market_consultant" if skill_root.name == "sql-query-writer-for-dashboard" else "qingcheng"
    if registry.get("domain") != expected_domain:
        issues.append({"code": "CURRENT_MODEL_DOMAIN_MISMATCH", "actual": registry.get("domain")})

    model_ids: set[str] = set()
    registered_paths: set[str] = set()
    expected_prefix = "market" if expected_domain == "market_consultant" else "qingcheng"
    for model in registry.get("models", []):
        model_id = str(model.get("model_id") or "")
        if not model_id or model_id in model_ids:
            issues.append({"code": "DUPLICATE_CURRENT_MODEL", "model_id": model_id})
            continue
        model_ids.add(model_id)
        expected = f"resources/raw_sql/data_center_{expected_prefix}_{model_id}.sql"
        canonical_sql = str(model.get("canonical_sql") or "")
        registered_paths.add(canonical_sql)
        if canonical_sql != expected:
            issues.append({"code": "UNSTABLE_CANONICAL_PATH", "model_id": model_id, "actual": canonical_sql})
            continue
        source = skill_root / canonical_sql
        if not source.exists():
            issues.append({"code": "MISSING_CURRENT_MODEL_SQL", "model_id": model_id})
        elif _sha256(source) != model.get("sql_sha256"):
            issues.append({"code": "CURRENT_MODEL_HASH_DRIFT", "model_id": model_id})

    for model_id, source in stable_files.items():
        relative = source.relative_to(skill_root).as_posix()
        if relative not in registered_paths:
            issues.append({"code": "UNREGISTERED_STABLE_MODEL", "model_id": model_id, "path": relative})

    slot_ids: set[str] = set()
    for slot in registry.get("semantic_slots", []):
        slot_id = str(slot.get("slot_id") or "")
        current_model_id = str(slot.get("current_model_id") or "")
        if not slot_id or slot_id in slot_ids:
            issues.append({"code": "DUPLICATE_SEMANTIC_SLOT", "slot_id": slot_id})
        slot_ids.add(slot_id)
        if slot_id and not slot_id.startswith(expected_domain + ":"):
            issues.append({"code": "CROSS_DOMAIN_SEMANTIC_SLOT", "slot_id": slot_id})
        if current_model_id not in model_ids:
            issues.append({"code": "SLOT_MODEL_NOT_CURRENT", "slot_id": slot_id, "model_id": current_model_id})
        evidence_path = str(slot.get("evidence_path") or "")
        if evidence_path and not (skill_root / evidence_path).is_file():
            issues.append({"code": "SLOT_EVIDENCE_MISSING", "slot_id": slot_id, "path": evidence_path})
    return issues


def main() -> int:
    skills = {name: audit_skill(REPO_ROOT / name) for name in DOMAIN_SKILLS}
    payload = {"ok": all(item["ok"] for item in skills.values()), "skills": skills}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
