"""Command-line interface used by thin domain skill wrappers."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from jsonschema import Draft202012Validator

from .ast_validator import validate_sql_ast
from .catalog import CatalogBundle, read_json
from .compiler import compile_query_plan
from .contracts import CONTRACT_FILES, ContractRegistry
from .dataset import build_dataset_spec
from .evaluator import evaluate_resolution_cases
from .models import QueryPlan, QuerySpec
from .planner import build_query_plan
from .probe import generate_probe


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Domain-safe Text2SQL routing, planning, and validation")
    subparsers = parser.add_subparsers(dest="command", required=True)

    summary = subparsers.add_parser("summary", help="show domain catalog, contract, and boundary counts")
    summary.add_argument("--json", action="store_true")

    init_spec = subparsers.add_parser("init-spec", help="print a domain-resolved QuerySpec skeleton")
    init_spec.add_argument("--intent", required=True)

    search = subparsers.add_parser("search", help="search the domain manifest")
    search.add_argument("--query", required=True)
    search.add_argument("--kind", default="all")
    search.add_argument("--limit", type=int, default=20)

    resolve = subparsers.add_parser("resolve", help="resolve domain-local semantic contract aliases")
    resolve.add_argument("--query", required=True)
    resolve.add_argument("--kind", choices=sorted(CONTRACT_FILES))

    validate_spec = subparsers.add_parser("validate-spec", help="validate a QuerySpec JSON file")
    validate_spec.add_argument("--spec", required=True, type=Path)

    plan = subparsers.add_parser("plan", help="build a governed QueryPlan from a QuerySpec")
    plan.add_argument("--spec", required=True, type=Path)
    plan.add_argument("--output", type=Path)

    compile_command = subparsers.add_parser("compile", help="compile a safe single-table QueryPlan")
    compile_command.add_argument("--spec", required=True, type=Path)
    compile_command.add_argument("--sql-output", required=True, type=Path)
    compile_command.add_argument("--plan-output", type=Path)

    probe = subparsers.add_parser("probe", help="generate a bounded data-quality probe")
    probe.add_argument("--kind", required=True, choices=("freshness", "distribution", "duplicates", "join-cardinality"))
    probe.add_argument("--table", required=True)
    probe.add_argument("--start-value", required=True)
    probe.add_argument("--end-value", required=True)
    probe.add_argument("--partition-field")
    probe.add_argument("--field")
    probe.add_argument("--keys", nargs="+")
    probe.add_argument("--right-table")
    probe.add_argument("--right-keys", nargs="+")
    probe.add_argument("--right-partition-field")
    probe.add_argument("--limit", type=int, default=100)
    probe.add_argument("--output", type=Path)

    dataset = subparsers.add_parser("dataset-spec", help="derive a read-only dashboard dataset design")
    dataset.add_argument("--plan", required=True, type=Path)
    dataset.add_argument("--output", type=Path)

    subparsers.add_parser("evaluate", help="run offline semantic resolution evals")

    validate_sql = subparsers.add_parser("validate-sql", help="validate concrete Presto SQL with AST checks")
    sql_group = validate_sql.add_mutually_exclusive_group(required=True)
    sql_group.add_argument("--sql")
    sql_group.add_argument("--sql-file", type=Path)
    validate_sql.add_argument("--spec", type=Path)
    validate_sql.add_argument("--allow-unknown-tables", action="store_true")
    return parser


def _schema_errors(value: dict[str, Any], schema_path: Path) -> list[str]:
    errors = sorted(
        Draft202012Validator(read_json(schema_path)).iter_errors(value),
        key=lambda error: list(error.path),
    )
    return [
        f"{'.'.join(str(part) for part in error.path) or '<root>'}: {error.message}"
        for error in errors
    ]


def _load_query_spec(path: Path, core_root: Path) -> QuerySpec:
    raw = read_json(path)
    errors = _schema_errors(raw, core_root / "schemas" / "query_spec.schema.json")
    if errors:
        raise ValueError("QuerySpec schema validation failed:\n" + "\n".join(errors))
    return QuerySpec.from_dict(raw)


def _load_query_plan(path: Path, core_root: Path) -> QueryPlan:
    raw = read_json(path)
    errors = _schema_errors(raw, core_root / "schemas" / "query_plan.schema.json")
    if errors:
        raise ValueError("QueryPlan schema validation failed:\n" + "\n".join(errors))
    return QueryPlan.from_dict(raw)


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8", newline="\n")


def _emit_json(value: dict[str, Any], output: Path | None = None) -> None:
    rendered = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if output:
        _write_text(output, rendered)
        print(f"Wrote {output.resolve()}")
    else:
        print(rendered, end="")


def main_for_domain(
    *,
    domain: str,
    skill_root: Path,
    core_root: Path,
    argv: Sequence[str] | None = None,
) -> int:
    args = _parser().parse_args(argv)
    bundle = CatalogBundle.load(skill_root, core_root)
    if bundle.domain != domain:
        print(f"catalog domain mismatch: expected {domain}, found {bundle.domain}", file=sys.stderr)
        return 2

    registry = ContractRegistry.load(skill_root, domain)
    if args.command == "summary":
        payload = {
            "domain": domain,
            "counts": bundle.domain_manifest["counts"],
            "semantic_contracts": {
                "counts": {kind: len(values) for kind, values in sorted(registry.contracts.items())},
                "confirmed_counts": {
                    kind: sum(item.get("status") == "confirmed" for item in values)
                    for kind, values in sorted(registry.contracts.items())
                },
                "valid": registry.ok,
            },
            "boundary": bundle.domain_manifest["boundary"],
            "physical_tables": len(bundle.physical_catalog.get("tables", [])),
        }
        if args.json:
            _emit_json(payload)
        else:
            print(f"domain: {domain}")
            print(f"knowledge files: {payload['counts']['knowledge_files']}")
            print(f"raw SQL files: {payload['counts']['raw_sql_files']}")
            print(f"semantic contracts: {sum(payload['semantic_contracts']['counts'].values())}")
            print(f"physical tables: {payload['physical_tables']}")
        return 0 if registry.ok else 1

    if args.command == "init-spec":
        _emit_json(
            {
                "schema_version": "2.0.0",
                "spec_id": None,
                "domain": domain,
                "intent": args.intent,
                "metrics": [],
                "dimensions": [],
                "filters": [],
                "business_scope": [],
                "scopes": [],
                "time_range": None,
                "calculation_grain": [],
                "output_grain": [],
                "candidate_tables": [],
                "join_path": [],
                "evidence": [],
                "unresolved_slots": [
                    "metrics_or_requested_fields",
                    "time_range",
                    "business_scope",
                    "calculation_grain",
                    "output_grain",
                ],
                "execution_mode": "production",
            }
        )
        return 0

    if args.command == "search":
        print(json.dumps(bundle.search(args.query, args.kind, args.limit), ensure_ascii=False, indent=2))
        return 0

    if args.command == "resolve":
        payload = registry.resolve(args.query, args.kind).to_dict()
        payload["registry_diagnostics"] = [item.to_dict() for item in registry.diagnostics]
        _emit_json(payload)
        return 0 if registry.ok and payload["status"] != "unknown" else 1

    if args.command == "evaluate":
        report = evaluate_resolution_cases(skill_root, domain)
        _emit_json(report)
        return 0 if report["ok"] else 1

    if args.command == "probe":
        try:
            probe = generate_probe(
                bundle,
                kind=args.kind,
                table=args.table,
                start_value=args.start_value,
                end_value=args.end_value,
                partition_field=args.partition_field,
                field=args.field,
                keys=args.keys,
                right_table=args.right_table,
                right_keys=args.right_keys,
                right_partition_field=args.right_partition_field,
                limit=args.limit,
            )
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        if args.output:
            _write_text(args.output, probe.sql)
            _emit_json({key: value for key, value in probe.to_dict().items() if key != "sql"})
        else:
            print(probe.sql, end="")
        return 0

    if args.command == "dataset-spec":
        try:
            plan = _load_query_plan(args.plan, core_root)
            payload = build_dataset_spec(plan)
            errors = _schema_errors(payload, core_root / "schemas" / "dashboard_dataset_spec.schema.json")
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        if errors:
            print("DashboardDatasetSpec schema validation failed:\n" + "\n".join(errors), file=sys.stderr)
            return 1
        _emit_json(payload, args.output)
        return 0

    try:
        query_spec = _load_query_spec(args.spec, core_root) if getattr(args, "spec", None) else None
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.command == "validate-spec":
        diagnostics = bundle.validate_query_spec(query_spec) if query_spec else []
        for item in diagnostics:
            print(f"[{item.severity}] {item.code}: {item.message}")
        if any(item.severity == "error" for item in diagnostics):
            return 1
        print("QuerySpec validation passed.")
        return 0

    if args.command in {"plan", "compile"}:
        if query_spec is None:
            print("QuerySpec is required", file=sys.stderr)
            return 1
        query_plan = build_query_plan(query_spec, skill_root=skill_root, core_root=core_root)
        plan_errors = _schema_errors(query_plan.to_dict(), core_root / "schemas" / "query_plan.schema.json")
        if plan_errors:
            print("QueryPlan schema validation failed:\n" + "\n".join(plan_errors), file=sys.stderr)
            return 1
        if args.command == "plan":
            _emit_json(query_plan.to_dict(), args.output)
            return 1 if query_plan.status == "blocked" else 0
        if not query_plan.executable:
            if args.plan_output:
                _emit_json(query_plan.to_dict(), args.plan_output)
            else:
                _emit_json(query_plan.to_dict())
            print(f"QueryPlan is not executable: {query_plan.status}", file=sys.stderr)
            return 1
        try:
            compiled = compile_query_plan(query_plan, registry)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        _write_text(args.sql_output, compiled.sql)
        print(f"Wrote {args.sql_output.resolve()}")
        if args.plan_output:
            _emit_json(compiled.plan.to_dict(), args.plan_output)
        else:
            _emit_json(compiled.summary())
        return 0

    sql = args.sql if args.sql is not None else args.sql_file.read_text(encoding="utf-8-sig")
    result = validate_sql_ast(
        sql,
        skill_root=skill_root,
        core_root=core_root,
        expected_domain=domain,
        allow_unknown_tables=args.allow_unknown_tables,
        query_spec=query_spec,
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.ok else 1
