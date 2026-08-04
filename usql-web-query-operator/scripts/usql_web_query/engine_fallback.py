"""Validated engine fallback policy and conservative retry classification."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from _shared.errors import UsageError

from .engine import QUERY_ENGINE_CHOICES, normalize_query_engine
from .models import RunSummary


SKILL_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = SKILL_ROOT / "references" / "query_engine_fallbacks.json"
REGISTRY_SCHEMA_PATH = SKILL_ROOT / "references" / "query_engine_fallbacks.schema.json"


@dataclass(frozen=True)
class FallbackEngineResolution:
    primary_engine: str
    fallback_engine: str
    resolution_source: str
    equivalence_group: str | None
    registry_sha256: str


@dataclass(frozen=True)
class FallbackDecision:
    eligible: bool
    trigger: str | None
    transient_error_code: str | None
    reason_code: str


def load_engine_fallback_registry(
    path: Path = REGISTRY_PATH,
    schema_path: Path = REGISTRY_SCHEMA_PATH,
) -> tuple[dict[str, Any], str]:
    registry = json.loads(path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(schema).iter_errors(registry),
        key=lambda item: list(item.path),
    )
    if errors:
        rendered = "; ".join(
            f"{'.'.join(map(str, item.path)) or '<root>'}: {item.message}"
            for item in errors
        )
        raise UsageError(f"Query engine fallback registry is invalid: {rendered}")

    supported = tuple(registry["supported_engines"])
    if set(supported) != set(QUERY_ENGINE_CHOICES):
        raise UsageError(
            "Query engine fallback registry supported engines differ from the CLI: "
            f"registry={sorted(supported)}, cli={sorted(QUERY_ENGINE_CHOICES)}"
        )
    groups: dict[str, str] = {}
    seen_group_ids: set[str] = set()
    for group in registry["equivalence_groups"]:
        group_id = str(group["group_id"])
        if group_id in seen_group_ids:
            raise UsageError(f"Duplicate query engine equivalence group: {group_id}")
        seen_group_ids.add(group_id)
        for engine in group["engines"]:
            if engine in groups:
                raise UsageError(f"Query engine appears in multiple equivalence groups: {engine}")
            groups[str(engine)] = group_id

    explicit_only = set(registry["explicit_only_engines"])
    for primary, fallback in registry["default_fallback_by_primary"].items():
        if primary == fallback:
            raise UsageError(f"Default fallback engine duplicates primary engine: {primary}")
        if fallback in explicit_only:
            raise UsageError(f"Explicit-only engine cannot be a global default fallback: {fallback}")
        if groups.get(primary) is None or groups.get(primary) != groups.get(fallback):
            raise UsageError(
                f"Global default fallback must be directory-equivalent: {primary} -> {fallback}"
            )
    for domain, overrides in registry["domain_overrides"].items():
        for primary, fallback in overrides.items():
            if primary == fallback:
                raise UsageError(
                    f"Domain fallback engine duplicates primary engine: {domain} {primary}"
                )
    return registry, hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_fallback_engine(
    primary_engine: str,
    *,
    requested_fallback: str | None,
    domain: str | None,
    registry_path: Path = REGISTRY_PATH,
    registry_schema_path: Path = REGISTRY_SCHEMA_PATH,
) -> FallbackEngineResolution:
    registry, registry_sha256 = load_engine_fallback_registry(
        registry_path,
        registry_schema_path,
    )
    primary = normalize_query_engine(primary_engine)
    group_by_engine = {
        str(engine): str(group["group_id"])
        for group in registry["equivalence_groups"]
        for engine in group["engines"]
    }
    if requested_fallback is not None:
        fallback = normalize_query_engine(requested_fallback)
        source = "explicit"
    else:
        domain_fallback = None
        if domain in registry["domain_overrides"]:
            domain_fallback = registry["domain_overrides"][domain].get(primary)
        if domain_fallback:
            fallback = normalize_query_engine(domain_fallback)
            source = "domain_registered"
        else:
            default_fallback = registry["default_fallback_by_primary"].get(primary)
            if not default_fallback:
                raise UsageError(
                    f"No default fallback engine is registered for primary engine {primary}; "
                    "pass --fallback-engine explicitly."
                )
            fallback = normalize_query_engine(default_fallback)
            source = "default_equivalent"
    if fallback == primary:
        raise UsageError("Fallback engine must differ from the primary engine.")
    if source == "default_equivalent" and fallback in set(registry["explicit_only_engines"]):
        raise UsageError(f"Fallback engine {fallback} requires explicit or domain registration.")
    equivalence_group = (
        group_by_engine.get(primary)
        if group_by_engine.get(primary) == group_by_engine.get(fallback)
        else None
    )
    return FallbackEngineResolution(
        primary_engine=primary,
        fallback_engine=fallback,
        resolution_source=source,
        equivalence_group=equivalence_group,
        registry_sha256=registry_sha256,
    )


_NON_TRANSIENT_PATTERNS = re.compile(
    r"validate_sql_error|mismatched\s+input|syntax\s+error|column\b.*(?:not found|does not exist)|"
    r"table\b.*(?:not found|does not exist)|unknown\s+(?:column|table)|cannot\s+cast|cast\s+error|"
    r"type\s+mismatch|join\s+mismatch|permission|access\s+denied|forbidden|\b403\b|\b429\b|"
    r"captcha|mfa|number\s+of\s+stages|exceeds\s+the\s+allowed\s+maximum|partition",
    flags=re.I | re.S,
)

_TRANSIENT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("http_502", re.compile(r"\b502\b|bad\s+gateway", flags=re.I)),
    ("http_503", re.compile(r"\b503\b|service\s+unavailable", flags=re.I)),
    ("http_504", re.compile(r"\b504\b|gateway\s+timeout", flags=re.I)),
    (
        "engine_temporarily_unavailable",
        re.compile(
            r"(?:engine|cluster|coordinator|worker).{0,60}(?:busy|unavailable|overloaded)|"
            r"(?:queue|scheduler).{0,60}(?:busy|unavailable|temporar)",
            flags=re.I | re.S,
        ),
    ),
    (
        "service_temporarily_unavailable",
        re.compile(r"temporar(?:ily)?\s+unavailable|temporary\s+service\s+failure", flags=re.I),
    ),
    (
        "connection_failure",
        re.compile(
            r"connection\s+(?:reset|refused|closed)|connect(?:ion)?\s+timed\s+out|"
            r"upstream\s+connect\s+error",
            flags=re.I,
        ),
    ),
    ("backend_internal_error", re.compile(r"internal\s+server\s+error", flags=re.I)),
)


def _error_text(summary: RunSummary) -> str:
    details = summary.error_details or {}
    return "\n".join(
        str(value)
        for value in (
            details.get("title"),
            details.get("detail"),
            details.get("raw_snippet"),
            summary.message,
        )
        if value
    )[:12_000]


def decide_fallback(summary: RunSummary) -> FallbackDecision:
    if summary.result_state == "result_unresolved":
        return FallbackDecision(True, "result_unresolved", None, "exact_result_unresolved")
    if summary.result_state == "success_empty_verified":
        return FallbackDecision(False, None, None, "verified_empty_requires_crosscheck_only")
    if summary.status == "Timeout":
        return FallbackDecision(False, None, None, "primary_job_may_still_be_running")
    if summary.status not in {"Failed", "Error"}:
        return FallbackDecision(False, None, None, "primary_result_not_retryable")

    submission_status = (summary.submission_evidence or {}).get("http_status")
    if submission_status in {502, 503, 504}:
        code = f"submission_http_{submission_status}"
        return FallbackDecision(True, "engine_transient_error", code, code)

    text = _error_text(summary)
    if _NON_TRANSIENT_PATTERNS.search(text):
        return FallbackDecision(False, None, None, "sql_permission_or_governance_error")
    for code, pattern in _TRANSIENT_PATTERNS:
        if pattern.search(text):
            return FallbackDecision(True, "engine_transient_error", code, code)
    return FallbackDecision(False, None, None, "no_explicit_transient_engine_evidence")
