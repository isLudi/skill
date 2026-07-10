"""Offline semantic-resolution evaluation for one isolated domain."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

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
    cases = envelope.get("cases", [])
    passed = 0
    for case in cases:
        result = registry.resolve(str(case.get("query", "")))
        actual_ids = sorted(item["id"] for item in result.candidates)
        expected_ids = sorted(map(str, case.get("expected_ids", [])))
        expected_status = case.get("expected_status")
        if actual_ids == expected_ids and result.status == expected_status:
            passed += 1
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
    return {
        "ok": not failures,
        "domain": domain,
        "total": len(cases),
        "passed": passed,
        "failures": failures,
    }
