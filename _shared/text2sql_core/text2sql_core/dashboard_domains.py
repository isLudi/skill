"""Validate dashboard ownership against domain-local governed profile registries."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


DOMAIN_SKILLS = {
    "market_consultant": "sql-query-writer-for-dashboard",
    "qingcheng": "qingcheng-dashboard-sql",
}


def _diagnostic(code: str, message: str, path: str | None = None) -> dict[str, Any]:
    item: dict[str, Any] = {
        "code": code,
        "severity": "error",
        "message": message,
    }
    if path:
        item["path"] = path
    return item


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_manifest(repo_root: Path, domain: str) -> tuple[Path, Mapping[str, Any]]:
    skill_root = repo_root / DOMAIN_SKILLS[domain]
    manifest_path = skill_root / "semantic" / "domain_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return skill_root, manifest


def _registered_dashboard_evidence(
    skill_root: Path,
    manifest: Mapping[str, Any],
    dashboard_id: str,
) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    diagnostics: list[dict[str, Any]] = []
    registry = manifest.get("dashboard_registry")
    if not isinstance(registry, Mapping):
        return [], [
            _diagnostic(
                "DASHBOARD_DOMAIN_REGISTRY_MISSING",
                "domain manifest does not contain dashboard_registry; rebuild the Text2SQL catalog",
                "dashboard_registry",
            )
        ]
    registered = registry.get("registered")
    if not isinstance(registered, list):
        return [], [
            _diagnostic(
                "DASHBOARD_DOMAIN_REGISTRY_INVALID",
                "dashboard_registry.registered must be an array",
                "dashboard_registry.registered",
            )
        ]
    matching = [
        item
        for item in registered
        if isinstance(item, Mapping) and str(item.get("dashboard_id") or "") == dashboard_id
    ]
    if not matching:
        return [], diagnostics
    if len(matching) != 1:
        diagnostics.append(
            _diagnostic(
                "DASHBOARD_DOMAIN_REGISTRY_DUPLICATE",
                f"dashboard {dashboard_id!r} is duplicated inside one domain registry",
                "dashboard_registry.registered",
            )
        )
        return [], diagnostics
    item = matching[0]
    raw_evidence = item.get("evidence")
    if item.get("status") != "registered" or not isinstance(raw_evidence, list) or not raw_evidence:
        diagnostics.append(
            _diagnostic(
                "DASHBOARD_DOMAIN_EVIDENCE_REQUIRED",
                f"dashboard {dashboard_id!r} has no registered source evidence",
                "dashboard_registry.registered.evidence",
            )
        )
        return [], diagnostics
    manifest_sources = {
        str(source.get("source_path") or ""): str(source.get("sha256") or "")
        for source in manifest.get("entities", {}).get("dashboard_web_profiles", [])
        if isinstance(source, Mapping)
    }
    evidence: list[dict[str, str]] = []
    for index, raw in enumerate(raw_evidence):
        if not isinstance(raw, Mapping):
            diagnostics.append(
                _diagnostic(
                    "DASHBOARD_DOMAIN_EVIDENCE_INVALID",
                    "dashboard registry evidence entries must be objects",
                    f"dashboard_registry.registered.evidence[{index}]",
                )
            )
            continue
        source_path = str(raw.get("source_path") or "").replace("\\", "/")
        expected_sha256 = str(raw.get("source_sha256") or "")
        parts = [part for part in source_path.split("/") if part]
        path = skill_root.joinpath(*parts)
        if not source_path or source_path.startswith("/") or ".." in parts:
            diagnostics.append(
                _diagnostic(
                    "DASHBOARD_DOMAIN_EVIDENCE_PATH_INVALID",
                    "dashboard registry evidence must use a non-escaping relative path",
                    f"dashboard_registry.registered.evidence[{index}].source_path",
                )
            )
            continue
        if manifest_sources.get(source_path) != expected_sha256:
            diagnostics.append(
                _diagnostic(
                    "DASHBOARD_DOMAIN_EVIDENCE_MANIFEST_MISMATCH",
                    f"dashboard evidence {source_path!r} does not match the domain manifest",
                    f"dashboard_registry.registered.evidence[{index}]",
                )
            )
            continue
        if not path.is_file():
            diagnostics.append(
                _diagnostic(
                    "DASHBOARD_DOMAIN_EVIDENCE_FILE_MISSING",
                    f"dashboard evidence file does not exist: {source_path}",
                    f"dashboard_registry.registered.evidence[{index}].source_path",
                )
            )
            continue
        actual_sha256 = _sha256(path)
        if actual_sha256 != expected_sha256:
            diagnostics.append(
                _diagnostic(
                    "DASHBOARD_DOMAIN_EVIDENCE_HASH_MISMATCH",
                    f"dashboard evidence hash is stale: {source_path}",
                    f"dashboard_registry.registered.evidence[{index}].source_sha256",
                )
            )
            continue
        evidence.append(
            {
                "source_path": source_path,
                "source_sha256": actual_sha256,
            }
        )
    return evidence, diagnostics


def validate_dashboard_domain_registration(
    dashboard_id: str,
    domain: str,
    *,
    repo_root: Path | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Resolve dashboard ownership from both isolated business manifests.

    Unregistered dashboards remain available for read-only profiling, but they
    cannot enter a DesignSpec or any mutation chain.
    """

    identity = str(dashboard_id or "").strip()
    resolution: dict[str, Any] = {
        "dashboard_id": identity,
        "requested_domain": domain,
        "status": "blocked",
        "registered_domain": None,
        "evidence": [],
    }
    diagnostics: list[dict[str, Any]] = []
    if domain not in DOMAIN_SKILLS:
        diagnostics.append(
            _diagnostic(
                "DASHBOARD_DOMAIN_UNRESOLVED",
                "dashboard domain must resolve to one supported business skill",
                "domain",
            )
        )
        return resolution, diagnostics
    root = (repo_root or _default_repo_root()).resolve()
    owners: dict[str, list[dict[str, str]]] = {}
    for candidate_domain in DOMAIN_SKILLS:
        try:
            skill_root, manifest = _load_manifest(root, candidate_domain)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            diagnostics.append(
                _diagnostic(
                    "DASHBOARD_DOMAIN_REGISTRY_UNAVAILABLE",
                    f"cannot load {candidate_domain} dashboard registry: {exc}",
                    "dashboard_registry",
                )
            )
            continue
        manifest_domain = manifest.get("domain", {})
        if not isinstance(manifest_domain, Mapping) or manifest_domain.get("id") != candidate_domain:
            diagnostics.append(
                _diagnostic(
                    "DASHBOARD_DOMAIN_MANIFEST_INVALID",
                    f"{candidate_domain} domain manifest identity is invalid",
                    "domain.id",
                )
            )
            continue
        evidence, candidate_diagnostics = _registered_dashboard_evidence(
            skill_root,
            manifest,
            identity,
        )
        diagnostics.extend(candidate_diagnostics)
        if evidence:
            owners[candidate_domain] = evidence
    if len(owners) > 1:
        diagnostics.append(
            _diagnostic(
                "DASHBOARD_DOMAIN_AMBIGUOUS",
                f"dashboard {identity!r} is registered to multiple business domains: {sorted(owners)}",
                "dashboard_id",
            )
        )
        return resolution, diagnostics
    if not owners:
        diagnostics.append(
            _diagnostic(
                "DASHBOARD_DOMAIN_UNREGISTERED",
                f"dashboard {identity!r} is not registered in either business skill; sync its governed web profile first",
                "dashboard_id",
            )
        )
        return resolution, diagnostics
    registered_domain, evidence = next(iter(owners.items()))
    resolution["registered_domain"] = registered_domain
    resolution["evidence"] = evidence
    if registered_domain != domain:
        diagnostics.append(
            _diagnostic(
                "DASHBOARD_DOMAIN_REGISTRATION_MISMATCH",
                f"dashboard {identity!r} is registered to {registered_domain!r}, not {domain!r}",
                "domain",
            )
        )
        return resolution, diagnostics
    resolution["status"] = "registered"
    return resolution, diagnostics
