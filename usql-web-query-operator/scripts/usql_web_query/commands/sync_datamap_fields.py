"""Refresh table field descriptions from Data Map into SQL skill docs."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from _shared.browser import import_playwright, launch_context
from _shared.env import load_env_file
from _shared.errors import UsageError

from usql_web_query.data_map import DataMapClient
from usql_web_query.knowledge_field_sync import (
    SkillTarget,
    append_changelog,
    discover_tables,
    load_catalog,
    run_maintenance,
    save_catalog,
    sync_skill_target,
)


def cmd_sync_datamap_fields(args: argparse.Namespace) -> int:
    validate_datamap_write_mode(args)
    load_env_file(args.env_file)
    targets = _resolve_targets(args)
    table_names = discover_tables(targets, args.table)
    if not table_names:
        raise UsageError("No physical table docs were found to sync.")

    catalog = load_catalog(args.cache_file)
    if args.refresh_datamap:
        catalog = _refresh_datamap_catalog(args, table_names, catalog)
        save_catalog(args.cache_file, catalog)

    missing_in_cache = [table for table in table_names if table not in catalog]
    if missing_in_cache:
        raise UsageError(
            "Data Map cache is missing table(s): "
            + ", ".join(missing_in_cache[:20])
            + (f" ... ({len(missing_in_cache)} total)" if len(missing_in_cache) > 20 else "")
        )

    run_date = date.fromisoformat(args.run_date) if args.run_date else date.today()
    summaries = []
    results = []
    maintenance_failed = False
    for target in targets:
        result = sync_skill_target(
            target,
            catalog,
            requested_tables=args.table,
            write=args.write,
            run_date=run_date,
        )
        if args.update_changelog:
            append_changelog(target, result, run_date=run_date, write=args.write)
        results.append(result)

    changed_targets = [
        target
        for target, result in zip(targets, results)
        if result.changed_files or result.changelog_updated
    ]
    if args.write and changed_targets:
        try:
            maintenance = run_maintenance(
                changed_targets,
                rebuild_indexes=args.rebuild_indexes,
                build_catalog=args.build_catalog,
                check_integrity=args.check_integrity,
                validate_stack=args.validate_stack,
                enabled=True,
            )
            for result in results:
                if result.changed_files or result.changelog_updated:
                    result.maintenance = maintenance
        except UsageError:
            maintenance_failed = True
            raise
    summaries = [result.to_json() for result in results]

    output = {
        "ok": not maintenance_failed,
        "mode": "write" if args.write else "dry_run",
        "run_date": run_date.isoformat(),
        "tables_requested": len(table_names),
        "cache_file": str(args.cache_file),
        "datamap_state_path": str(args.datamap_state_path),
        "refresh_datamap": args.refresh_datamap,
        "skills": summaries,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


def validate_datamap_write_mode(args: argparse.Namespace) -> None:
    if not args.write:
        return
    disabled = [
        name
        for name in ("rebuild_indexes", "build_catalog", "check_integrity", "validate_stack")
        if not getattr(args, name, False)
    ]
    if disabled:
        raise UsageError(
            "unsafe Data Map write options; mandatory maintenance cannot be disabled: "
            + ", ".join(disabled)
        )


def _refresh_datamap_catalog(args: argparse.Namespace, table_names: list[str], catalog: dict[str, object]) -> dict[str, object]:
    sync_playwright = import_playwright()
    args.datamap_state_path.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser, context = launch_context(
            playwright,
            args.datamap_state_path,
            args.headed,
            args.browser_channel,
            args.executable_path,
        )
        page = context.new_page()
        try:
            client = DataMapClient(page, args.datamap_state_path)
            client.ensure_authenticated(args.username, args.password)
            for table in table_names:
                if args.only_missing_cache and table in catalog:
                    continue
                catalog[table] = client.fetch_table(table)
        finally:
            context.close()
            browser.close()
    return catalog


def _resolve_targets(args: argparse.Namespace) -> list[SkillTarget]:
    if args.skill_root:
        row_style = args.row_style or "market"
        return [
            SkillTarget(name=root.name, root=root.resolve(), row_style=_infer_row_style(root, row_style))
            for root in args.skill_root
        ]

    skill_root = Path(__file__).resolve().parents[3]
    skills_root = skill_root.parent
    configured = {
        "market": SkillTarget(
            name="market",
            root=skills_root / "sql-query-writer-for-dashboard",
            row_style="market",
        ),
        "qingcheng": SkillTarget(
            name="qingcheng",
            root=skills_root / "qingcheng-dashboard-sql",
            row_style="qingcheng",
        ),
    }
    if args.target_skill == "all":
        return [configured["market"], configured["qingcheng"]]
    return [configured[args.target_skill]]


def _infer_row_style(root: Path, default: str) -> str:
    lowered = root.name.lower()
    if "qingcheng" in lowered:
        return "qingcheng"
    if "sql-query-writer" in lowered:
        return "market"
    return default
