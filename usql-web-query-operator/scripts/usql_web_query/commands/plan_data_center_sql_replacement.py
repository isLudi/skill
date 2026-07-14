"""Create a read-only, hash-bound plan for one Data Center SQL replacement."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from _shared.browser import import_playwright, launch_context
from _shared.env import load_env_file

from usql_web_query.data_center import DataCenterClient, select_dataset_for_replacement
from usql_web_query.data_center_replacement import (
    build_replacement_plan,
    load_replacement_sql,
    write_replacement_plan,
)


def cmd_plan_data_center_sql_replacement(args: argparse.Namespace) -> int:
    """Read current state and emit a plan without changing the remote dataset."""

    load_env_file(args.env_file)
    replacement_sql = load_replacement_sql(args.sql_file)
    args.state_path.parent.mkdir(parents=True, exist_ok=True)
    sync_playwright = import_playwright()

    with sync_playwright() as playwright:
        browser, context = launch_context(
            playwright,
            args.state_path,
            args.headed,
            args.browser_channel,
            args.executable_path,
        )
        page = context.new_page()
        try:
            client = DataCenterClient(page, args.state_path)
            client.ensure_authenticated(args.username, args.password)
            discovered = client.discover_datasets()
            dataset = select_dataset_for_replacement(
                discovered,
                domain=args.domain,
                dataset_name=args.dataset_name,
                dataset_id=args.dataset_id,
            )
            dataset_sql = client.fetch_dataset_sql(dataset)
        finally:
            context.close()
            browser.close()

    plan = build_replacement_plan(
        domain=args.domain,
        dataset_sql=dataset_sql,
        sql_file=args.sql_file,
        replacement_sql=replacement_sql,
        allow_noop=args.allow_noop,
    )
    plan_path = args.output_file or _default_plan_path(args.artifacts_dir, plan.plan_sha256)
    write_replacement_plan(plan_path, plan)
    output = {
        "ok": plan.status == "ready",
        "mode": "read_only_plan",
        "status": plan.status,
        "plan_sha256": plan.plan_sha256,
        "plan_path": str(plan_path.resolve()),
        "domain": plan.domain,
        "dataset": plan.dataset,
        "sql_file": plan.sql_file,
        "current_sql_sha256": plan.current_sql_sha256,
        "replacement_sql_sha256": plan.replacement_sql_sha256,
        "content_change": plan.content_change,
        "allow_noop": plan.allow_noop,
        "diagnostics": list(plan.diagnostics),
        "remote_write_performed": False,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if plan.status == "ready" else 1


def _default_plan_path(artifacts_dir: Path, plan_sha256: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return artifacts_dir / f"data_center_replacement_plan_{stamp}_{plan_sha256[:12]}.json"
