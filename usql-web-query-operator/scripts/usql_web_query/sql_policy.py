"""Read-only SQL statement and complexity policy enforced before browser launch."""

from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import sqlglot
from jsonschema import Draft202012Validator
from sqlglot import exp

from _shared.errors import UsageError


POLICY_SCHEMA_VERSION = "1.0.0"
POLICY_MODES = frozenset({"audit", "enforce"})
_TEMPLATE_RE = re.compile(r"\$\{[^}]*\}|\{\{[^}]*\}\}")


@dataclass(frozen=True)
class PolicyBudgets:
    joins: int = 12
    ctes: int = 24
    subqueries: int = 32
    set_operations: int = 8
    windows: int = 32

    def to_dict(self) -> dict[str, int]:
        return {
            "joins": self.joins,
            "ctes": self.ctes,
            "subqueries": self.subqueries,
            "set_operations": self.set_operations,
            "windows": self.windows,
        }


def analyze_sql_policy(
    sql: str,
    *,
    mode: str = "enforce",
    budgets: PolicyBudgets | None = None,
    required_partition_fields: list[str] | tuple[str, ...] | None = None,
    require_limit: bool = False,
) -> dict[str, Any]:
    if mode not in POLICY_MODES:
        raise ValueError(f"policy mode must be one of: {', '.join(sorted(POLICY_MODES))}")
    active_budgets = budgets or PolicyBudgets()
    normalized_required = sorted(
        {str(field).strip().lower() for field in required_partition_fields or [] if str(field).strip()}
    )
    diagnostics: list[dict[str, Any]] = []
    statements: list[exp.Expression] = []
    if _TEMPLATE_RE.search(sql):
        diagnostics.append(
            _diagnostic(
                "UNRESOLVED_TEMPLATE_PARAMETER",
                "error",
                "SQL contains an unresolved template parameter.",
                hard_block=True,
            )
        )
    try:
        statements = sqlglot.parse(sql, read="presto")
    except sqlglot.errors.ParseError:
        diagnostics.append(
            _diagnostic(
                "SQL_PARSE_FAILED",
                "error",
                "SQL could not be parsed as Presto.",
                hard_block=True,
            )
        )

    statement_type = type(statements[0]).__name__ if len(statements) == 1 else None
    if len(statements) != 1:
        diagnostics.append(
            _diagnostic(
                "SINGLE_STATEMENT_REQUIRED",
                "error",
                f"Exactly one SQL statement is required; found {len(statements)}.",
                hard_block=True,
            )
        )
    elif not isinstance(statements[0], exp.Query):
        diagnostics.append(
            _diagnostic(
                "READ_ONLY_QUERY_REQUIRED",
                "error",
                f"Only SELECT/WITH/set-operation queries are allowed; found {statement_type}.",
                hard_block=True,
            )
        )

    tree = statements[0] if len(statements) == 1 else None
    counts = {
        "statements": len(statements),
        "joins": _count(tree, exp.Join),
        "ctes": _count(tree, exp.CTE),
        "subqueries": _count(tree, exp.Subquery),
        "set_operations": _count(tree, exp.SetOperation),
        "windows": _count(tree, exp.Window),
    }
    for name, maximum in active_budgets.to_dict().items():
        observed = counts[name]
        if observed > maximum:
            severity = "error" if mode == "enforce" else "warning"
            diagnostics.append(
                _diagnostic(
                    f"{name.upper()}_BUDGET_EXCEEDED",
                    severity,
                    f"SQL {name} count {observed} exceeds the configured budget {maximum}.",
                    hard_block=False,
                )
            )

    where_fields = sorted(_where_fields(tree))
    has_limit = bool(tree and any(isinstance(node, exp.Limit) for node in tree.walk()))
    missing_partitions = sorted(set(normalized_required) - set(where_fields))
    if missing_partitions:
        diagnostics.append(
            _diagnostic(
                "REQUIRED_PARTITION_FILTER_MISSING",
                "error",
                "Required partition filters are missing: " + ", ".join(missing_partitions),
                hard_block=True,
            )
        )
    if require_limit and not has_limit:
        diagnostics.append(
            _diagnostic(
                "LIMIT_REQUIRED",
                "error",
                "This execution contract requires an explicit LIMIT.",
                hard_block=True,
            )
        )

    report: dict[str, Any] = {
        "artifact_type": "sql_policy_report",
        "schema_version": POLICY_SCHEMA_VERSION,
        "report_sha256": "",
        "created_at": _utc_now(),
        "sql_sha256": hashlib.sha256(sql.encode("utf-8")).hexdigest(),
        "mode": mode,
        "allowed": not any(item["severity"] == "error" for item in diagnostics),
        "statement_type": statement_type,
        "counts": counts,
        "budgets": active_budgets.to_dict(),
        "requirements": {
            "require_limit": require_limit,
            "required_partition_fields": normalized_required,
        },
        "observed": {
            "has_limit": has_limit,
            "where_fields": where_fields,
        },
        "diagnostics": diagnostics,
    }
    report["report_sha256"] = _report_sha256(report)
    validate_policy_report(report)
    return report


def enforce_sql_policy(report: dict[str, Any]) -> None:
    if report.get("allowed") is True:
        return
    codes = ", ".join(str(item.get("code")) for item in report.get("diagnostics", []) if item.get("severity") == "error")
    raise UsageError(f"SQL policy blocked browser execution: {codes or 'unknown policy error'}.")


def validate_policy_report(report: dict[str, Any]) -> None:
    schema_path = Path(__file__).resolve().parents[2] / "references" / "sql_policy_report.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(report), key=lambda item: list(item.path))
    if errors:
        rendered = "; ".join(
            f"{'.'.join(map(str, item.path)) or '<root>'}: {item.message}"
            for item in errors
        )
        raise ValueError(f"SQL policy report schema validation failed: {rendered}")
    expected = _report_sha256(report)
    if report.get("report_sha256") != expected:
        raise ValueError("SQL policy report hash is invalid")


def write_policy_report(path: Path, report: dict[str, Any]) -> None:
    validate_policy_report(report)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        temporary.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _count(tree: exp.Expression | None, node_type: type[exp.Expression]) -> int:
    return 0 if tree is None else sum(isinstance(node, node_type) for node in tree.walk())


def _where_fields(tree: exp.Expression | None) -> set[str]:
    if tree is None:
        return set()
    return {
        str(column.name).lower()
        for where in tree.find_all(exp.Where)
        for column in where.find_all(exp.Column)
        if column.name
    }


def _diagnostic(code: str, severity: str, message: str, *, hard_block: bool) -> dict[str, Any]:
    return {
        "code": code,
        "severity": severity,
        "message": message,
        "hard_block": hard_block,
    }


def _report_sha256(report: dict[str, Any]) -> str:
    payload = {key: value for key, value in report.items() if key != "report_sha256"}
    rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
