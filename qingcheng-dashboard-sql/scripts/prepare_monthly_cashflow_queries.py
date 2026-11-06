"""Prepare scoped monthly cashflow SQL; never execute queries or infer permissions."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

PATTERNS = Path(__file__).resolve().parents[1] / "knowledge/sql_patterns"
RECIPES = {"finance": "finance", "lookup": "stat_lookup", "tt": "tt_supplement"}
SCOPE_KEYS = ("goods_first", "goods_second", "course_first", "course_second")


def scope_hash(scopes: dict) -> str:
    values = {key: scopes[key] for key in SCOPE_KEYS}
    return hashlib.sha256(json.dumps(values, ensure_ascii=True, sort_keys=True).encode("utf-8")).hexdigest()


def sql_list(values: list[str]) -> str:
    if not isinstance(values, list) or not values or any(not isinstance(v, str) or not v.strip() for v in values):
        raise ValueError("Every permission scope must be a nonempty list of department names")
    return ",".join("'" + value.replace("'", "''") + "'" for value in values)


def prepare(start_date: str, end_date: str, snapshot_dt: str, snapshot_hour: str,
            scopes: dict, verified_counts: dict | None = None) -> dict[str, str]:
    start, end = date.fromisoformat(start_date), date.fromisoformat(end_date)
    snapshot = date.fromisoformat(f"{snapshot_dt[:4]}-{snapshot_dt[4:6]}-{snapshot_dt[6:8]}")
    if not re.fullmatch(r"\d{8}", snapshot_dt) or end < start or snapshot < end:
        raise ValueError("Use an ordered business period and a snapshot on or after its inclusive end")
    if not re.fullmatch(r"(?:[01]\d|2[0-3])", snapshot_hour):
        raise ValueError("snapshot_hour must be HH, from 00 through 23")
    if not scopes.get("scope_evidence"):
        raise ValueError("Provide current permission/scope evidence; historical examples are insufficient")
    params = {key + "_scope_sql": sql_list(scopes.get(key)) for key in SCOPE_KEYS}
    params.update(start_date=start.isoformat(), end_exclusive=(end + timedelta(days=1)).isoformat(),
                  snapshot_dt=snapshot_dt, snapshot_hour=snapshot_hour)
    if verified_counts is not None:
        for name in RECIPES:
            item = verified_counts.get(name, {})
            count = item.get("row_count")
            if not isinstance(count, int) or isinstance(count, bool) or count < 0 or not item.get("query_id"):
                raise ValueError(f"{name} needs an exact nonnegative row count and its control Query ID")
            if (item.get("snapshot_dt") != snapshot_dt or item.get("snapshot_hour") != snapshot_hour
                    or item.get("start_date") != start_date or item.get("end_date") != end_date
                    or item.get("scope_sha256") != scope_hash(scopes)):
                raise ValueError(f"{name} control scope/date drift")
    output = {}
    for name, suffix in RECIPES.items():
        template = (PATTERNS / f"qingcheng_monthly_cashflow_{suffix}.sql").read_text(encoding="utf-8")
        template = re.sub(r"\A(?:\s*--[^\n]*(?:\n|$))*\s*", "", template)
        limit = verified_counts[name]["row_count"] + 1 if verified_counts is not None else 1
        query = template.replace("{{verified_export_limit}}", str(limit))
        for key, value in params.items():
            query = query.replace("{{" + key + "}}", value)
        if "{{" in query or "}}" in query:
            raise ValueError("Unresolved recipe parameter")
        if verified_counts is not None:
            output[f"{name}.sql"] = query
        scan = query[query.index("\nFROM ") + 1:]
        scan = re.sub(r"\nLIMIT \d+\s*$", "\n", scan)
        if name == "finance":
            prefix = "SELECT f.goods_first_level_department_name AS first_dept, f.goods_second_level_department_name AS second_dept, count(*) AS row_count, sum(coalesce(f.income_amount,0))/100 AS income_yuan, sum(coalesce(f.refund_amount,0))/100 AS refund_yuan\n"
        elif name == "tt":
            prefix = "SELECT course_first_level_department_name AS first_dept, course_second_level_department_name AS second_dept, count(*) AS row_count, sum(coalesce(income_amount,0))/100 AS income_yuan, sum(coalesce(refund_amount,0))/100 AS refund_yuan\n"
        else:
            prefix = "SELECT course_first_level_department_name AS first_dept, course_second_level_department_name AS second_dept, count(*) AS row_count\n"
        if name == "tt":
            distribution_scan, removed = re.subn(
                r"(?m)^\s+AND course_second_level_department_name IN \([^\n]*\)\n", "", scan, count=1)
            if removed != 1:
                raise ValueError("TT department distribution query must inspect all second-level departments")
            output["tt_department_distribution.sql"] = (
                prefix + distribution_scan + "GROUP BY 1,2\nORDER BY 1,2\nLIMIT 1000\n")
        output[f"{name}_control.sql"] = prefix + scan + "GROUP BY 1,2\nORDER BY 1,2\nLIMIT 1000\n"
    return output


def build_manifest(start_date: str, end_date: str, snapshot_dt: str, snapshot_hour: str,
                   scopes: dict, queries: dict[str, str], verified_counts: dict | None = None) -> dict:
    receipt_fields = ("row_count", "query_id", "start_date", "end_date", "snapshot_dt",
                      "snapshot_hour", "scope_sha256")
    control_receipts = None
    if verified_counts is not None:
        control_receipts = {
            name: {key: verified_counts[name][key] for key in receipt_fields}
            for name in RECIPES
        }
    return {
        "domain": "qingcheng",
        "execution": "not_executed",
        "start_date": start_date,
        "end_date_inclusive": end_date,
        "snapshot_dt": snapshot_dt,
        "snapshot_hour": snapshot_hour,
        "scope_evidence": scopes["scope_evidence"],
        "scope_sha256": scope_hash(scopes),
        "control_receipts": control_receipts,
        "queries": {name: hashlib.sha256(query.encode("utf-8")).hexdigest()
                    for name, query in queries.items()},
    }


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True, help="Inclusive business date")
    parser.add_argument("--snapshot-dt", required=True)
    parser.add_argument("--snapshot-hour", required=True)
    parser.add_argument("--scopes", type=Path, required=True)
    parser.add_argument("--verified-counts", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    scopes = json.loads(args.scopes.read_text(encoding="utf-8"))
    counts = json.loads(args.verified_counts.read_text(encoding="utf-8")) if args.verified_counts else None
    queries = prepare(args.start_date, args.end_date, args.snapshot_dt, args.snapshot_hour, scopes, counts)
    manifest_content = json.dumps(build_manifest(args.start_date, args.end_date, args.snapshot_dt,
                                                args.snapshot_hour, scopes, queries, counts),
                                  ensure_ascii=False, indent=2)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    target_contents = {**queries, "query_manifest.json": manifest_content}
    for name, content in target_contents.items():
        target = args.output_dir / name
        if target.exists() and target.read_text(encoding="utf-8") != content:
            raise ValueError(f"Refusing to overwrite a different query: {target}")
    for name, query in queries.items():
        (args.output_dir / name).write_text(query, encoding="utf-8")
    (args.output_dir / "query_manifest.json").write_text(manifest_content, encoding="utf-8")
    print(json.dumps({"status": "prepared", "query_count": len(queries), "output_dir": str(args.output_dir)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
