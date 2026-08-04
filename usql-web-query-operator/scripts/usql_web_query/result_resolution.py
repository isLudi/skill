"""Resolve exact-query API and UI result evidence without hiding conflicts."""

from __future__ import annotations

from typing import Any


EXACT_EMPTY_COMPLETION_SOURCES = {"log_api", "history"}


def resolve_result_state(
    api_evidence: dict[str, Any] | None,
    ui_preview: dict[str, Any] | None,
    *,
    completion_source: str | None,
) -> tuple[str, dict[str, Any] | None, dict[str, Any]]:
    """Return the public result state, preview, and redaction-safe evidence.

    The exact-query result API is primary. An empty response without an explicit
    total is accepted as zero rows only after the same query ID has completed in
    history or the log API. Contradictory exact-query evidence remains unresolved.
    """
    evidence = dict(api_evidence or {})
    api_state = evidence.get("state")
    evidence["completion_source"] = completion_source
    evidence["evidence_conflict"] = None

    if api_state == "success_with_rows":
        if ui_preview:
            evidence["source"] = "result_api_and_ui"
            return "success_with_rows", evidence.get("preview"), evidence
        evidence["source"] = "result_api"
        return "success_ui_missing_recovered", evidence.get("preview"), evidence

    if api_state == "success_empty_verified":
        if ui_preview:
            evidence["source"] = "result_api_and_ui"
            evidence["evidence_conflict"] = "api_zero_ui_rows"
            return "result_unresolved", None, evidence
        evidence["source"] = "result_api"
        return "success_empty_verified", evidence.get("preview"), evidence

    if api_state == "success_empty_candidate":
        if ui_preview:
            evidence["source"] = "ui"
            return "success_with_rows_ui", ui_preview, evidence
        evidence["source"] = "result_api"
        if completion_source in EXACT_EMPTY_COMPLETION_SOURCES:
            return "success_empty_verified", evidence.get("preview"), evidence
        return "result_unresolved", None, evidence

    if api_state == "result_api_failed" and ui_preview:
        evidence["source"] = "result_api_and_ui"
        evidence["evidence_conflict"] = "api_failure_ui_rows"
        return "result_unresolved", None, evidence

    if ui_preview:
        evidence["source"] = "ui"
        return "success_with_rows_ui", ui_preview, evidence

    evidence.setdefault("source", "result_api" if api_evidence else None)
    return "result_unresolved", None, evidence
