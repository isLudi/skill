"""Domain-bound contract evidence verification for dashboard design artifacts."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping

from .contracts import ContractRegistry


DOMAIN_SKILL_NAMES = {
    "market_consultant": "sql-query-writer-for-dashboard",
    "qingcheng": "qingcheng-dashboard-sql",
}


def _diagnostic(
    code: str, message: str, path: str | None = None
) -> dict[str, Any]:
    return {
        key: value
        for key, value in {
            "code": code,
            "severity": "error",
            "message": message,
            "path": path,
        }.items()
        if value is not None
    }


def _default_skills_root() -> Path:
    # dashboard_contracts.py lives at
    # skills/_shared/text2sql_core/text2sql_core/dashboard_contracts.py.
    return Path(__file__).resolve().parents[3]


def _business_skill_root(
    domain: str,
    business_skill_roots: Mapping[str, str | Path] | None,
) -> Path | None:
    if domain not in DOMAIN_SKILL_NAMES:
        return None
    if business_skill_roots is not None:
        raw_root = business_skill_roots.get(domain)
        return Path(raw_root).resolve() if raw_root is not None else None
    return (_default_skills_root() / DOMAIN_SKILL_NAMES[domain]).resolve()


def _contract_evidence_items(
    dataset_spec: Mapping[str, Any],
) -> list[tuple[str, Mapping[str, Any], str]]:
    items: list[tuple[str, Mapping[str, Any], str]] = []
    for collection in ("fields", "scope_contracts", "default_filters"):
        raw_items = dataset_spec.get(collection, [])
        if not isinstance(raw_items, list):
            continue
        for index, item in enumerate(raw_items):
            if not isinstance(item, Mapping):
                continue
            contract_id = item.get("contract_id")
            if collection == "scope_contracts":
                contract_id = contract_id or item.get("id")
            contract_expected = (
                collection == "scope_contracts"
                or item.get("role") == "scope_contract"
                or bool(contract_id)
            )
            if contract_expected:
                items.append((f"{collection}[{index}]", item, str(contract_id or "").strip()))
    return items


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_dataset_contract_registry_evidence(
    dataset_spec: Mapping[str, Any],
    domain: str,
    *,
    business_skill_roots: Mapping[str, str | Path] | None = None,
) -> list[dict[str, Any]]:
    """Verify referenced DatasetSpec contracts against the live domain registry.

    The DatasetSpec is untrusted input.  A contract-backed field, scope, or
    filter is accepted only when the contract exists in the selected domain's
    registry, the evidence tuple matches that registry exactly, and the real
    source file still hashes to the registered SHA-256.
    """

    evidence_items = _contract_evidence_items(dataset_spec)
    if not evidence_items:
        return []

    diagnostics: list[dict[str, Any]] = []
    skill_root = _business_skill_root(domain, business_skill_roots)
    if skill_root is None:
        return [
            _diagnostic(
                "DASHBOARD_CONTRACT_REGISTRY_ROOT_MISSING",
                f"no business skill root is configured for domain {domain!r}",
                "domain",
            )
        ]
    if not skill_root.is_dir():
        return [
            _diagnostic(
                "DASHBOARD_CONTRACT_REGISTRY_ROOT_MISSING",
                f"business skill root does not exist for domain {domain!r}",
                "domain",
            )
        ]

    registry = ContractRegistry.load(skill_root, domain)
    for item in registry.diagnostics:
        if item.severity != "error":
            continue
        diagnostics.append(
            _diagnostic(
                "DASHBOARD_CONTRACT_REGISTRY_INVALID",
                f"domain contract registry is invalid ({item.code}): {item.message}",
                item.path or "semantic/contracts",
            )
        )

    for path, supplied, contract_id in evidence_items:
        if not contract_id:
            # The structural evidence validator emits the precise missing-ID
            # diagnostic; there is nothing safe to look up here.
            continue
        registered = registry.by_id(contract_id)
        if registered is None:
            diagnostics.append(
                _diagnostic(
                    "DASHBOARD_CONTRACT_NOT_REGISTERED",
                    f"contract {contract_id!r} does not exist in the {domain!r} registry",
                    f"{path}.contract_id",
                )
            )
            continue

        registered_status = str(registered.get("status") or "")
        supplied_status = str(supplied.get("contract_status") or "")
        if registered_status != "confirmed":
            diagnostics.append(
                _diagnostic(
                    "DASHBOARD_CONTRACT_REGISTRY_NOT_CONFIRMED",
                    f"registered contract {contract_id!r} is not confirmed",
                    f"{path}.contract_id",
                )
            )
        if supplied_status != registered_status:
            diagnostics.append(
                _diagnostic(
                    "DASHBOARD_CONTRACT_STATUS_MISMATCH",
                    "DatasetSpec contract_status does not match the domain registry",
                    f"{path}.contract_status",
                )
            )

        registered_source_path = str(registered.get("source_path") or "")
        supplied_source_path = str(supplied.get("source_path") or "")
        if supplied_source_path != registered_source_path:
            diagnostics.append(
                _diagnostic(
                    "DASHBOARD_CONTRACT_SOURCE_PATH_MISMATCH",
                    "DatasetSpec source_path does not exactly match the domain registry",
                    f"{path}.source_path",
                )
            )

        registered_source_hash = str(registered.get("source_sha256") or "")
        supplied_source_hash = str(supplied.get("source_sha256") or "")
        if supplied_source_hash != registered_source_hash:
            diagnostics.append(
                _diagnostic(
                    "DASHBOARD_CONTRACT_SOURCE_HASH_MISMATCH",
                    "DatasetSpec source_sha256 does not exactly match the domain registry",
                    f"{path}.source_sha256",
                )
            )

        source_target = (skill_root / registered_source_path).resolve()
        if (
            not registered_source_path
            or not source_target.is_relative_to(skill_root)
            or not source_target.is_file()
        ):
            diagnostics.append(
                _diagnostic(
                    "DASHBOARD_CONTRACT_SOURCE_FILE_MISSING",
                    f"registered source file is missing or escapes the {domain!r} skill",
                    f"{path}.source_path",
                )
            )
            continue
        actual_source_hash = _sha256(source_target)
        if actual_source_hash != registered_source_hash:
            diagnostics.append(
                _diagnostic(
                    "DASHBOARD_CONTRACT_SOURCE_FILE_HASH_MISMATCH",
                    "real source file SHA-256 does not match the domain registry",
                    f"{path}.source_sha256",
                )
            )

    return diagnostics


__all__ = ["DOMAIN_SKILL_NAMES", "validate_dataset_contract_registry_evidence"]
