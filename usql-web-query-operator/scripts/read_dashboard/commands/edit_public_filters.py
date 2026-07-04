"""Edit public-filter dynamic defaults and optionally publish dashboards."""

from __future__ import annotations

import json

from _shared.auth import ensure_authenticated
from _shared.browser import import_playwright, launch_context
from _shared.env import load_env_file
from _shared.fs_utils import ensure_runtime, safe_artifact_dir

from ..common import write_json
from ..constants import DASHBOARD_MARKET_URL
from ..filter_edit import (
    QINGCHENG_FILTER_TARGET_NAMES,
    edit_dashboard_public_filters,
    resolve_dashboard_targets,
    split_csv_or_pipe,
)


def cmd_edit_public_filters(args) -> int:
    load_env_file(args.env_file)
    sync_playwright = import_playwright()
    ensure_runtime([args.state_path.parent, args.artifacts_dir])
    artifacts_dir = safe_artifact_dir(args.artifacts_dir)
    output_path = args.output or (artifacts_dir / "edit_public_filters_summary.json")

    names = split_csv_or_pipe(args.name)
    if args.target_set == "qingcheng-required":
        names.extend(name for name in QINGCHENG_FILTER_TARGET_NAMES if name not in names)
    dashboard_ids = split_csv_or_pipe(args.dashboard_id)
    plan = {1: str(args.first_value), 2: str(args.second_value)}

    results: list[dict] = []
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
            ensure_authenticated(page, args, context=context)
            page.goto(DASHBOARD_MARKET_URL, wait_until="domcontentloaded", timeout=45_000)
            page.wait_for_timeout(args.scan_wait_ms)
            targets = resolve_dashboard_targets(page, args.folder, names, dashboard_ids)
            for target in targets:
                dashboard_id = str(target["dashboard_id"] or "")
                try:
                    results.append(
                        edit_dashboard_public_filters(
                            page=page,
                            args=args,
                            dashboard_id=dashboard_id,
                            dashboard_name=target.get("dashboard_name"),
                            folder_name=target.get("folder"),
                            plan=plan,
                            artifacts_dir=artifacts_dir,
                        )
                    )
                except Exception as exc:  # noqa: BLE001
                    results.append(
                        {
                            "ok": False,
                            "dashboard_id": dashboard_id,
                            "dashboard_name": target.get("dashboard_name"),
                            "folder": target.get("folder"),
                            "message": str(exc),
                        }
                    )
        finally:
            browser.close()

    summary = {
        "ok": bool(results) and all(item.get("ok") for item in results),
        "target_set": args.target_set,
        "folder": args.folder,
        "publish": args.publish,
        "dry_run": args.dry_run,
        "filter_plan": plan,
        "count": len(results),
        "success_count": sum(1 for item in results if item.get("ok")),
        "failure_count": sum(1 for item in results if not item.get("ok")),
        "output_path": str(output_path),
        "results": results,
    }
    write_json(summary, output_path)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["ok"] else 1
