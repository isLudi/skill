"""Offline semantic-resolution evaluation for one isolated domain."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .contracts import CONTRACT_SCHEMA_VERSION, ContractRegistry


def evaluate_resolution_cases(skill_root: Path, domain: str) -> dict[str, Any]:
    registry = ContractRegistry.load(skill_root, domain)
    path = skill_root / "semantic" / "evals" / "resolution_cases.json"
    failures: list[dict[str, Any]] = []
    if not registry.ok:
        failures.extend(
            {"id": "contract_registry", "message": item.message, "code": item.code}
            for item in registry.diagnostics
            if item.severity == "error"
        )
    try:
        envelope = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "domain": domain,
            "total": 0,
            "passed": 0,
            "failures": [{"id": "eval_file", "message": str(exc)}],
        }
    if envelope.get("schema_version") != CONTRACT_SCHEMA_VERSION:
        failures.append({"id": "eval_schema", "message": "schema_version must be 2.0.0"})
    if envelope.get("domain") != domain:
        failures.append({"id": "eval_domain", "message": "eval domain mismatch"})
    schema_path = Path(__file__).resolve().parents[1] / "schemas" / "resolution_eval.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    schema_errors = sorted(Draft202012Validator(schema).iter_errors(envelope), key=lambda item: list(item.path))
    failures.extend(
        {
            "id": "eval_schema",
            "message": f"{'.'.join(map(str, item.path)) or '<root>'}: {item.message}",
        }
        for item in schema_errors
    )
    cases = envelope.get("cases", [])
    passed = 0
    category_counts: dict[str, dict[str, int]] = {}
    for case in cases:
        result = registry.resolve(str(case.get("query", "")))
        actual_ids = sorted(item["id"] for item in result.candidates)
        expected_ids = sorted(map(str, case.get("expected_ids", [])))
        expected_status = case.get("expected_status")
        category = str(case.get("category") or "curated")
        category_counts.setdefault(category, {"total": 0, "passed": 0})["total"] += 1
        if actual_ids == expected_ids and result.status == expected_status:
            passed += 1
            category_counts[category]["passed"] += 1
        else:
            failures.append(
                {
                    "id": case.get("id"),
                    "query": case.get("query"),
                    "expected_ids": expected_ids,
                    "actual_ids": actual_ids,
                    "expected_status": expected_status,
                    "actual_status": result.status,
                }
            )
    alias_recall = _evaluate_alias_recall(registry)
    failures.extend(alias_recall["failures"])
    total = len(cases) + alias_recall["total"]
    total_passed = passed + alias_recall["passed"]
    return {
        "ok": not failures,
        "domain": domain,
        "total": total,
        "passed": total_passed,
        "accuracy": round(total_passed / total, 6) if total else 0.0,
        "curated": {
            "total": len(cases),
            "passed": passed,
            "categories": category_counts,
        },
        "alias_recall": alias_recall,
        "failures": failures,
    }


def _evaluate_alias_recall(registry: ContractRegistry) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    total = 0
    passed = 0
    skipped_short_aliases = 0
    for kind in sorted(registry.contracts):
        for contract in registry.values(kind):
            contract_id = str(contract["id"])
            probes = [("contract_id", contract_id), ("canonical_name", str(contract.get("name", "")))]
            probes.extend(("alias", str(alias)) for alias in contract.get("aliases", []))
            canonical_name = str(contract.get("name", "")).strip()
            if canonical_name:
                probes.append(("prefixed_name", "查询" + canonical_name))
            seen: set[tuple[str, str]] = set()
            for probe_type, query in probes:
                normalized = query.casefold().strip()
                if not normalized or (probe_type == "alias" and len(normalized) < 2):
                    skipped_short_aliases += 1
                    continue
                key = (probe_type, normalized)
                if key in seen:
                    continue
                seen.add(key)
                total += 1
                result = registry.resolve(query, kind)
                actual_ids = sorted(str(item["id"]) for item in result.candidates)
                if contract_id in actual_ids and all(item.startswith(f"{registry.domain}:") for item in actual_ids):
                    passed += 1
                else:
                    failures.append(
                        {
                            "id": f"alias_recall:{contract_id}:{probe_type}",
                            "expected_ids": [contract_id],
                            "actual_ids": actual_ids,
                            "actual_status": result.status,
                        }
                    )
    return {
        "total": total,
        "passed": passed,
        "recall": round(passed / total, 6) if total else 0.0,
        "skipped_short_aliases": skipped_short_aliases,
        "failures": failures,
    }
