"""Plan/apply a local knowledge owner migration using live temporary-table identities."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
from urllib.parse import urlparse

from _shared.browser import import_playwright, launch_context
from _shared.domain_adapters import DEFAULT_SKILLS_ROOT
from _shared.errors import UsageError
from usql_web_query.query_auth import query_credentials, verify_query_identity
from usql_web_query.data_center import DataCenterClient
from usql_web_query.temp_table_upload import navigate_query_page, open_temp_table_panel, wait_for_sql_frame
from usql_web_query.temp_table_knowledge import apply_plan, build_plan, encode


def collect_catalog(args, tables: set[str], production_evidence: list[dict]) -> dict:
    args.username, args.password = query_credentials(args.env_file)
    if args.username != "lvshuai01":
        raise UsageError("Temporary-table migration requires the lvshuai01 operator identity.")
    payloads = []
    with import_playwright()() as playwright:
        browser, context = launch_context(playwright, args.state_path, args.headed, args.browser_channel, None)
        try:
            page = context.new_page()

            def observe(response):
                if urlparse(response.url).path.endswith("/tempTable/listTables") and response.status == 200:
                    payloads.append(response.json())

            page.on("response", observe)
            navigate_query_page(page, args, context=context)
            verify_query_identity(page, "lvshuai01")
            open_temp_table_panel(wait_for_sql_frame(page))
            page.wait_for_timeout(1000)
            candidates = {name: set() for name in tables}

            def walk(value):
                if isinstance(value, dict):
                    name = value.get("name") or value.get("tableName")
                    identifier = value.get("id") or value.get("tableId")
                    full = name if str(name).startswith("temp_table.") else "temp_table." + str(name)
                    if full in candidates and identifier is not None:
                        candidates[full].add(str(identifier))
                    for child in value.values():
                        walk(child)
                elif isinstance(value, list):
                    for child in value:
                        walk(child)

            walk(payloads)
            missing = [name for name, ids in candidates.items() if len(ids) != 1]
            if missing:
                raise UsageError("Live temp-table catalog has missing/ambiguous identities: " + ", ".join(missing))
            catalog = {name: {"id": next(iter(ids)), "name": name} for name, ids in sorted(candidates.items())}
            if production_evidence:
                import sqlglot
                from sqlglot import exp
                client = DataCenterClient(page, args.state_path)
                datasets = {d.id: d for d in client.discover_datasets()}
                verified = {}
                for record in production_evidence:
                    dataset = datasets.get(record["dataset_id"])
                    if dataset is None or str(dataset.file_value) != record["model_id"]:
                        raise UsageError("Production evidence dataset identity drift.")
                    sql = client.fetch_dataset_sql(dataset).execute_sql
                    sha = hashlib.sha256(sql.encode("utf-8")).hexdigest()
                    if sha != record["sql_sha256"]:
                        raise UsageError("Production evidence SQL Hash drift.")
                    tree = sqlglot.parse_one(sql, read="presto")
                    tables_read = sorted({f"{t.db}.{t.name}".lower() for t in tree.find_all(exp.Table) if t.db})
                    verified[dataset.id] = {**record, "temp_tables": tables_read}
                catalog["production_sql"] = verified
            return catalog
        finally:
            context.close()
            browser.close()


def cmd_temp_table_knowledge(args) -> int:
    if args.output.exists() or args.output.resolve().is_relative_to(DEFAULT_SKILLS_ROOT.resolve()):
        raise UsageError("Use a new output file outside skills.")
    if args.mode == "apply" and not args.confirm_skill_maintenance:
        raise UsageError("Apply requires explicit local Skill maintenance confirmation.")
    document = json.loads(args.input.read_text(encoding="utf-8"))
    request = document if args.mode == "plan" else document["request"]
    evidence = {item["dataset_id"]: item for row in request["mappings"] for item in row.get("production_evidence", [])}
    catalog = collect_catalog(args, {row["new_table"] for row in request["mappings"]}, list(evidence.values()))
    if args.mode == "plan":
        result = build_plan(DEFAULT_SKILLS_ROOT, request, catalog)
    else:
        result = apply_plan(DEFAULT_SKILLS_ROOT, document, args.plan_sha256, catalog, args.artifacts_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as stream:
        stream.write(encode(result))
    print(json.dumps({"ok": True, "output": str(args.output), "plan_sha256": result["plan_sha256"],
                      "mutations": len(result.get("mutations", result.get("changed_files", [])))}, ensure_ascii=False))
    return 0
