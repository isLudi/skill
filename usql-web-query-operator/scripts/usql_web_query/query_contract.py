"""Validate the QueryPlan contract before opening the SQL web UI."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from _shared.errors import UsageError


QUERY_PLAN_SCHEMA_VERSION = "2.0.0"
ALLOWED_QUERY_PLAN_DOMAINS = frozenset({"market_consultant", "qingcheng"})
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class QueryPlanContract:
    """The execution-critical subset of a validated QueryPlan."""

    source_path: Path
    schema_version: str
    domain: str
    status: str
    sql_sha256: str
    execution_policy: dict[str, Any]

    @property
    def allow_download(self) -> bool:
        return self.execution_policy.get("allow_download") is True

    def to_summary(self) -> dict[str, Any]:
        """Return a compact summary without copying the complete QueryPlan."""

        return {
            "source_path": str(self.source_path),
            "schema_version": self.schema_version,
            "domain": self.domain,
            "status": self.status,
            "sql_sha256": self.sql_sha256,
            "allow_download": self.allow_download,
        }


def exact_sql_sha256(sql: str) -> str:
    """Hash the exact SQL text that will be submitted, without normalization."""

    return hashlib.sha256(sql.encode("utf-8")).hexdigest()


def load_query_plan_contract(path: Path, sql: str) -> QueryPlanContract:
    """Load and validate a QueryPlan against the exact submitted SQL text."""

    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise UsageError(f"QueryPlan file not found: {path}") from exc
    except OSError as exc:
        raise UsageError(f"Unable to read QueryPlan file {path}: {exc}") from exc

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise UsageError(f"Invalid QueryPlan JSON in {path}: {exc.msg}") from exc

    if not isinstance(payload, dict):
        raise UsageError("QueryPlan must be a JSON object.")

    schema_version = payload.get("schema_version")
    if schema_version != QUERY_PLAN_SCHEMA_VERSION:
        raise UsageError(
            "QueryPlan schema_version must be "
            f"{QUERY_PLAN_SCHEMA_VERSION!r}; got {schema_version!r}."
        )

    domain = payload.get("domain")
    if domain not in ALLOWED_QUERY_PLAN_DOMAINS:
        allowed = ", ".join(sorted(ALLOWED_QUERY_PLAN_DOMAINS))
        raise UsageError(f"QueryPlan domain must be one of: {allowed}; got {domain!r}.")

    status = payload.get("status")
    if status != "executable":
        raise UsageError(f"QueryPlan status must be 'executable'; got {status!r}.")

    unresolved_slots = payload.get("unresolved_slots")
    if not isinstance(unresolved_slots, list):
        raise UsageError("QueryPlan unresolved_slots must be a JSON array.")
    if unresolved_slots:
        raise UsageError(
            "QueryPlan unresolved_slots must be empty before execution: "
            + ", ".join(str(item) for item in unresolved_slots)
        )

    diagnostics = payload.get("diagnostics")
    if not isinstance(diagnostics, list):
        raise UsageError("QueryPlan diagnostics must be a JSON array.")
    error_diagnostics = [
        item
        for item in diagnostics
        if isinstance(item, dict) and str(item.get("severity", "")).lower() == "error"
    ]
    if error_diagnostics:
        raise UsageError("QueryPlan diagnostics must not contain error-severity entries.")

    sql_sha256 = payload.get("sql_sha256")
    if not isinstance(sql_sha256, str) or not _SHA256_RE.fullmatch(sql_sha256):
        raise UsageError("QueryPlan sql_sha256 must be a lowercase 64-character SHA-256 hex digest.")
    actual_sha256 = exact_sql_sha256(sql)
    if sql_sha256 != actual_sha256:
        raise UsageError(
            "QueryPlan sql_sha256 does not match the exact SQL submitted: "
            f"expected {sql_sha256}, actual {actual_sha256}."
        )

    execution_policy = payload.get("execution_policy")
    if not isinstance(execution_policy, dict):
        raise UsageError("QueryPlan execution_policy must exist and be a JSON object.")
    allow_download = execution_policy.get("allow_download")
    if not isinstance(allow_download, bool):
        raise UsageError("QueryPlan execution_policy.allow_download must be a boolean.")
    max_rows = execution_policy.get("max_direct_download_rows")
    if isinstance(max_rows, bool) or not isinstance(max_rows, int) or not 1 <= max_rows <= 1000:
        raise UsageError(
            "QueryPlan execution_policy.max_direct_download_rows must be an integer from 1 to 1000."
        )
    if execution_policy.get("requires_preview") is not True:
        raise UsageError("QueryPlan execution_policy.requires_preview must be true.")
    if execution_policy.get("execution_mode") not in {"production", "exploratory"}:
        raise UsageError(
            "QueryPlan execution_policy.execution_mode must be 'production' or 'exploratory'."
        )

    return QueryPlanContract(
        source_path=path,
        schema_version=schema_version,
        domain=domain,
        status=status,
        sql_sha256=sql_sha256,
        execution_policy=dict(execution_policy),
    )


def enforce_query_plan_download_policy(contract: QueryPlanContract, *, download: bool) -> None:
    """Require explicit QueryPlan permission before a requested download."""

    if download and not contract.allow_download:
        raise UsageError(
            "Download is blocked by QueryPlan execution_policy: "
            "allow_download must be true."
        )
