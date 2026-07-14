"""Create a read-only, hash-bound plan for one Data Center dataset creation."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from _shared.browser import import_playwright, launch_context
from _shared.env import load_env_file
from _shared.errors import UsageError

from usql_web_query.data_center import DataCenterClient, select_folder_for_creation
from usql_web_query.data_center_creation import (
    build_creation_plan,
    load_creation_sql,
    write_creation_plan,
)


def cmd_plan_data_center_dataset_creation(args: argparse.Namespace) -> int:
    """Read folder/name state and emit a plan without creating a remote dataset."""

    load_env_file(args.env_file)
    sql_text = load_creation_sql(args.sql_file)
    schedule_start = (
        _parse_date(args.schedule_start, label="schedule start")
        if args.schedule_start
        else date.today()
    )
    schedule_end = (
        _parse_date(args.schedule_end, label="schedule end")
        if args.schedule_end
        else schedule_start + timedelta(days=90)
    )
    schedule_hours = tuple(args.schedule_hour or [f"{hour}:00" for hour in range(24)])
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
            folders = client.discover_folders()
            datasets = client.discover_datasets()
            folder = select_folder_for_creation(
                folders,
                domain=args.domain,
                folder_path=args.folder_path,
                folder_id=args.folder_id,
            )
        finally:
            context.close()
            browser.close()

    plan = build_creation_plan(
        domain=args.domain,
        folder=folder,
        datasets=datasets,
        dataset_name=args.dataset_name,
        sql_file=args.sql_file,
        sql_text=sql_text,
        data_source_name=args.data_source_name,
        data_source_id=args.data_source_id,
        schedule_start=schedule_start,
        schedule_end=schedule_end,
        schedule_hours=schedule_hours,
    )
    plan_path = args.output_file or _default_plan_path(args.artifacts_dir, plan.plan_sha256)
    write_creation_plan(plan_path, plan)
    output = {
        "ok": plan.status == "ready",
        "mode": "read_only_plan",
        "status": plan.status,
        "plan_sha256": plan.plan_sha256,
        "plan_path": str(plan_path.resolve()),
        "domain": plan.domain,
        "folder": plan.folder,
        "dataset_name": plan.dataset_name,
        "sql_file": plan.sql_file,
        "sql_sha256": plan.sql_sha256,
        "data_source": plan.data_source,
        "schedule": plan.schedule,
        "diagnostics": list(plan.diagnostics),
        "remote_write_performed": False,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if plan.status == "ready" else 1


def _default_plan_path(artifacts_dir: Path, plan_sha256: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return artifacts_dir / f"data_center_creation_plan_{stamp}_{plan_sha256[:12]}.json"


def _parse_date(value: str, *, label: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise UsageError(f"invalid Data Center {label}; expected YYYY-MM-DD: {value}") from exc
