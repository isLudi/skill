"""Accuracy-first SQL quality gate for Tiangong2 query_sql updates."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import sqlglot
from sqlglot import exp

from _shared.errors import UsageError


SQL_REVIEW_SCHEMA_VERSION = "tiangong2-query-sql-review-v1"
PLACEHOLDER_PATTERN = re.compile(r"__[A-Z][A-Z0-9_]*__")
REVIEW_METHODS = {"code-simplifier", "equivalent-structured-review"}
PERFORMANCE_STATUSES = {"static_passed", "runtime_passed"}


def _text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _require_nonempty_strings(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise UsageError(f"Tiangong2 SQL review requires a non-empty {field} list")
    items = [str(item).strip() for item in value]
    if any(not item for item in items):
        raise UsageError(f"Tiangong2 SQL review {field} entries must be non-empty strings")
    if len(items) != len(set(items)):
        raise UsageError(f"Tiangong2 SQL review {field} entries must be unique")
    return items


def _load_review(path: Path, *, sql_sha256: str) -> tuple[dict[str, Any], str]:
    try:
        raw = path.read_text(encoding="utf-8")
        review = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise UsageError(f"Unable to read UTF-8 Tiangong2 SQL review JSON: {path}: {exc}") from exc
    if raw.startswith("\ufeff"):
        raise UsageError("Tiangong2 SQL review JSON must be UTF-8 without BOM")
    if not isinstance(review, dict):
        raise UsageError("Tiangong2 SQL review must be a JSON object")
    if review.get("schema_version") != SQL_REVIEW_SCHEMA_VERSION:
        raise UsageError("Unsupported Tiangong2 SQL review schema")
    if str(review.get("sql_sha256") or "") != sql_sha256:
        raise UsageError("Tiangong2 SQL review is not bound to the replacement SQL SHA-256")
    method = str(review.get("review_method") or "")
    if method not in REVIEW_METHODS:
        raise UsageError(
            "Tiangong2 SQL review method must be code-simplifier or equivalent-structured-review"
        )

    accuracy = review.get("accuracy")
    if not isinstance(accuracy, dict) or accuracy.get("status") != "passed":
        raise UsageError("Tiangong2 SQL review accuracy.status must be passed")
    if not str(accuracy.get("output_grain") or "").strip():
        raise UsageError("Tiangong2 SQL review requires accuracy.output_grain")
    _require_nonempty_strings(accuracy.get("required_output_columns"), "accuracy.required_output_columns")
    _require_nonempty_strings(accuracy.get("invariants"), "accuracy.invariants")
    evidence = accuracy.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        raise UsageError("Tiangong2 SQL review requires non-empty accuracy.evidence")
    for item in evidence:
        if not isinstance(item, dict):
            raise UsageError("Tiangong2 SQL review evidence entries must be objects")
        if not str(item.get("type") or "").strip() or not str(item.get("reference") or "").strip():
            raise UsageError("Tiangong2 SQL review evidence requires type and reference")

    simplification = review.get("simplification")
    if not isinstance(simplification, dict) or simplification.get("status") != "passed":
        raise UsageError("Tiangong2 SQL review simplification.status must be passed")
    _require_nonempty_strings(simplification.get("changes"), "simplification.changes")
    _require_nonempty_strings(
        simplification.get("preserved_semantics"),
        "simplification.preserved_semantics",
    )
    _require_nonempty_strings(
        simplification.get("repeated_processing_removed"),
        "simplification.repeated_processing_removed",
    )

    performance = review.get("performance")
    if not isinstance(performance, dict) or performance.get("status") not in PERFORMANCE_STATUSES:
        raise UsageError(
            "Tiangong2 SQL review performance.status must be static_passed or runtime_passed"
        )
    justifications = performance.get("justifications", [])
    if not isinstance(justifications, list):
        raise UsageError("Tiangong2 SQL review performance.justifications must be a list")
    seen_codes: set[str] = set()
    for item in justifications:
        if not isinstance(item, dict):
            raise UsageError("Tiangong2 SQL review performance justifications must be objects")
        code = str(item.get("code") or "").strip()
        reason = str(item.get("reason") or "").strip()
        if not code or not reason:
            raise UsageError("Tiangong2 SQL review performance justifications require code and reason")
        if code in seen_codes:
            raise UsageError("Tiangong2 SQL review performance justification codes must be unique")
        seen_codes.add(code)
    runtime_evidence = performance.get("runtime_evidence", [])
    if not isinstance(runtime_evidence, list):
        raise UsageError("Tiangong2 SQL review performance.runtime_evidence must be a list")
    if performance.get("status") == "runtime_passed" and not runtime_evidence:
        raise UsageError("runtime_passed requires non-empty performance.runtime_evidence")
    return review, _text_sha256(raw)


def _parse_query(sql: str) -> exp.Expression:
    try:
        statements = [statement for statement in sqlglot.parse(sql, read="spark") if statement]
    except sqlglot.errors.ParseError as exc:
        raise UsageError(f"Tiangong2 replacement SQL failed Spark syntax parsing: {exc}") from exc
    if len(statements) != 1:
        raise UsageError("Tiangong2 replacement SQL must contain exactly one statement")
    statement = statements[0]
    if not isinstance(statement, (exp.Select, exp.Union)):
        raise UsageError("Tiangong2 replacement SQL must be one read-only SELECT query")
    return statement


def _cte_names(statement: exp.Expression) -> set[str]:
    return {str(cte.alias_or_name).lower() for cte in statement.find_all(exp.CTE)}


def _relation_name(table: exp.Table) -> str:
    parts = [str(item) for item in (table.catalog, table.db, table.name) if item]
    return ".".join(parts).lower()


def _is_cte_reference(table: exp.Table, cte_names: set[str]) -> bool:
    return not table.catalog and not table.db and str(table.name).lower() in cte_names


def _direct_sources(select: exp.Select) -> list[exp.Expression]:
    sources: list[exp.Expression] = []
    from_clause = select.args.get("from_")
    if from_clause is not None:
        if from_clause.this is not None:
            sources.append(from_clause.this)
        sources.extend(from_clause.expressions)
    sources.extend(join.this for join in select.args.get("joins") or [] if join.this is not None)
    return sources


def _has_star_projection(select: exp.Select) -> bool:
    return any(
        isinstance(item, exp.Star)
        or (isinstance(item, exp.Column) and isinstance(item.this, exp.Star))
        for item in select.expressions
    )


def _output_columns(statement: exp.Expression) -> list[str]:
    select = statement if isinstance(statement, exp.Select) else next(statement.find_all(exp.Select), None)
    if select is None:
        return []
    return [str(item.alias_or_name or "").strip() for item in select.expressions]


def _union_leaves(expression: exp.Expression) -> list[exp.Expression]:
    if isinstance(expression, exp.Union) and expression.args.get("distinct") is False:
        return _union_leaves(expression.this) + _union_leaves(expression.expression)
    return [expression]


def _top_union_all_groups(statement: exp.Expression) -> list[exp.Union]:
    groups: list[exp.Union] = []
    for union in statement.find_all(exp.Union):
        if union.args.get("distinct") is not False:
            continue
        parent = union.parent
        nested = False
        while parent is not None and not isinstance(parent, exp.CTE):
            if isinstance(parent, exp.Union) and parent.args.get("distinct") is False:
                nested = True
                break
            parent = parent.parent
        if not nested:
            groups.append(union)
    if isinstance(statement, exp.Union) and statement.args.get("distinct") is False:
        groups.insert(0, statement)
    return list(dict.fromkeys(groups))


def _numeric_limit(statement: exp.Expression) -> int | None:
    limit = statement.args.get("limit")
    value = limit.expression if limit is not None else None
    if isinstance(value, exp.Literal) and not value.is_string:
        try:
            return int(value.this)
        except (TypeError, ValueError):
            return None
    return None


def _query_profile(sql: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    statement = _parse_query(sql)
    cte_names = _cte_names(statement)
    tables = list(statement.find_all(exp.Table))
    physical_relations = [
        _relation_name(table) for table in tables if not _is_cte_reference(table, cte_names)
    ]
    selects = list(statement.find_all(exp.Select))
    findings: list[dict[str, Any]] = []

    for select in selects:
        if not _has_star_projection(select):
            continue
        if select.args.get("distinct") is not None:
            findings.append(
                {
                    "code": "select_distinct_star",
                    "severity": "error",
                    "message": "SELECT DISTINCT * is prohibited; project the deduplication key explicitly.",
                }
            )
        direct_tables = [source for source in _direct_sources(select) if isinstance(source, exp.Table)]
        if any(not _is_cte_reference(table, cte_names) for table in direct_tables):
            findings.append(
                {
                    "code": "physical_select_star",
                    "severity": "error",
                    "message": "SELECT * from a physical relation is prohibited; project required columns.",
                }
            )

    physical_counts = Counter(physical_relations)
    repeated_physical = {name: count for name, count in physical_counts.items() if count > 1}
    if repeated_physical:
        findings.append(
            {
                "code": "repeated_physical_scan",
                "severity": "review_required",
                "message": "A physical relation is scanned more than once and requires an accuracy necessity review.",
                "details": repeated_physical,
            }
        )

    for index, union in enumerate(_top_union_all_groups(statement), start=1):
        branch_counts: Counter[str] = Counter()
        leaves = _union_leaves(union)
        for leaf in leaves:
            branch_relations = {
                _relation_name(table)
                for table in leaf.find_all(exp.Table)
                if _relation_name(table)
            }
            branch_counts.update(branch_relations)
        repeated = {name: count for name, count in branch_counts.items() if count >= 3}
        if repeated:
            findings.append(
                {
                    "code": "repeated_union_source",
                    "severity": "review_required",
                    "message": "Three or more UNION ALL branches reread the same relation; prefer one scan plus conditional projection.",
                    "details": {"group": index, "branch_count": len(leaves), "relations": repeated},
                }
            )

    cte_bodies: defaultdict[str, list[str]] = defaultdict(list)
    for cte in statement.find_all(exp.CTE):
        body_sha256 = _text_sha256(cte.this.sql(dialect="spark", pretty=False))
        cte_bodies[body_sha256].append(str(cte.alias_or_name))
    duplicate_ctes = [names for names in cte_bodies.values() if len(names) > 1]
    if duplicate_ctes:
        findings.append(
            {
                "code": "duplicate_cte_body",
                "severity": "review_required",
                "message": "Equivalent CTE bodies repeat the same processing and should be consolidated.",
                "details": duplicate_ctes,
            }
        )

    limit = _numeric_limit(statement)
    if statement.args.get("order") is not None and (limit is None or limit >= 1000):
        findings.append(
            {
                "code": "bulk_final_order_by",
                "severity": "review_required",
                "message": "A large or unbounded final ORDER BY requires an accuracy necessity review.",
                "details": {"limit": limit},
            }
        )

    profile = {
        "sql_bytes": len(sql.encode("utf-8")),
        "select_count": len(selects),
        "cte_count": len(cte_names),
        "join_count": len(list(statement.find_all(exp.Join))),
        "union_all_count": sum(
            1
            for union in statement.find_all(exp.Union)
            if union.args.get("distinct") is False
        ),
        "distinct_select_count": sum(
            1 for select in selects if select.args.get("distinct") is not None
        ),
        "physical_scan_count": len(physical_relations),
        "unique_physical_relation_count": len(set(physical_relations)),
        "physical_relations": sorted(set(physical_relations)),
        "output_columns": _output_columns(statement),
        "placeholders": sorted(set(PLACEHOLDER_PATTERN.findall(sql))),
        "final_order_by": statement.args.get("order") is not None,
        "final_limit": limit,
    }
    return profile, findings


def build_sql_quality_gate(
    *,
    current_sql: str,
    replacement_sql: str,
    review_file: Path,
) -> dict[str, Any]:
    replacement_sha256 = _text_sha256(replacement_sql)
    review, review_file_sha256 = _load_review(review_file, sql_sha256=replacement_sha256)
    baseline, _ = _query_profile(current_sql)
    replacement, findings = _query_profile(replacement_sql)

    required_columns = [str(item).strip() for item in review["accuracy"]["required_output_columns"]]
    if not replacement["output_columns"] or any(not item for item in replacement["output_columns"]):
        findings.append(
            {
                "code": "unnamed_output_column",
                "severity": "error",
                "message": "Every final output expression must have a stable column name.",
            }
        )
    if replacement["output_columns"] != required_columns:
        findings.append(
            {
                "code": "output_contract_mismatch",
                "severity": "error",
                "message": "Final output columns do not exactly match the reviewed ordered contract.",
            }
        )
    if baseline["placeholders"] != replacement["placeholders"]:
        findings.append(
            {
                "code": "placeholder_contract_mismatch",
                "severity": "error",
                "message": "Replacement SQL changed the Python-managed placeholder contract.",
                "details": {
                    "baseline": baseline["placeholders"],
                    "replacement": replacement["placeholders"],
                },
            }
        )

    complexity_fields = ("select_count", "join_count", "union_all_count", "physical_scan_count")
    regressions = {
        field: {"baseline": baseline[field], "replacement": replacement[field]}
        for field in complexity_fields
        if replacement[field] > baseline[field]
    }
    if regressions:
        findings.append(
            {
                "code": "complexity_regression",
                "severity": "review_required",
                "message": "Replacement SQL increases structural work and requires an accuracy necessity review.",
                "details": regressions,
            }
        )

    justification_codes = {
        str(item["code"]).strip() for item in review["performance"].get("justifications", [])
    }
    review_required_codes = {
        str(item["code"]) for item in findings if item["severity"] == "review_required"
    }
    stale_justifications = sorted(justification_codes - review_required_codes)
    if stale_justifications:
        raise UsageError(
            "Tiangong2 SQL review contains stale performance justification codes: "
            + ", ".join(stale_justifications)
        )
    unresolved = sorted(review_required_codes - justification_codes)
    hard_errors = sorted(
        {str(item["code"]) for item in findings if item["severity"] == "error"}
    )
    status = "passed" if not hard_errors and not unresolved else "blocked"

    return {
        "schema_version": SQL_REVIEW_SCHEMA_VERSION,
        "status": status,
        "review_file": str(review_file.resolve()),
        "review_file_sha256": review_file_sha256,
        "review_method": review["review_method"],
        "accuracy": {
            "status": review["accuracy"]["status"],
            "output_grain": str(review["accuracy"]["output_grain"]).strip(),
            "required_output_columns": required_columns,
            "required_output_columns_sha256": _text_sha256("\n".join(required_columns)),
            "invariant_count": len(review["accuracy"]["invariants"]),
            "evidence_count": len(review["accuracy"]["evidence"]),
        },
        "simplification": {
            "status": review["simplification"]["status"],
            "change_count": len(review["simplification"]["changes"]),
            "preserved_semantics_count": len(review["simplification"]["preserved_semantics"]),
            "repeated_processing_removed_count": len(
                review["simplification"]["repeated_processing_removed"]
            ),
        },
        "performance": {
            "status": review["performance"]["status"],
            "runtime_evidence_count": len(review["performance"].get("runtime_evidence", [])),
            "justified_finding_codes": sorted(justification_codes),
        },
        "static_analysis": {
            "baseline": baseline,
            "replacement": replacement,
            "findings": findings,
            "hard_error_codes": hard_errors,
            "unresolved_review_codes": unresolved,
        },
    }
