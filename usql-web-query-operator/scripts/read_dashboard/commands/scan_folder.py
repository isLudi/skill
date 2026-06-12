"""Scan dashboard names and IDs under one BI folder."""

from __future__ import annotations

import json

from _shared.auth import ensure_authenticated
from _shared.browser import import_playwright, launch_context
from _shared.debug import save_debug_artifacts
from _shared.env import load_env_file
from _shared.fs_utils import ensure_runtime, safe_artifact_dir

from ..constants import DASHBOARD_MARKET_URL
from ..menu import collect_dashboard_records, fetch_dashboard_menu
from ..models import DashboardScanSummary


def cmd_scan_folder(args) -> int:
    load_env_file(args.env_file)
    sync_playwright = import_playwright()
    ensure_runtime([args.state_path.parent, args.artifacts_dir])
    artifacts_dir = safe_artifact_dir(args.artifacts_dir)
    output_path = args.output or (artifacts_dir / "dashboards.json")

    with sync_playwright() as playwright:
        browser, context = launch_context(playwright, args.state_path, args.headed, args.browser_channel, args.executable_path)
        page = context.new_page()
        try:
            ensure_authenticated(page, args, context=context)
            page.goto(DASHBOARD_MARKET_URL, wait_until="domcontentloaded", timeout=45_000)
            page.wait_for_timeout(args.wait_ms)
            records = collect_dashboard_records(fetch_dashboard_menu(page), args.folder)
            if args.debug_artifacts:
                save_debug_artifacts(page, artifacts_dir, "scan_folder")
            summary = DashboardScanSummary(
                ok=True,
                folder=args.folder,
                count=len(records),
                output_path=str(output_path),
                records=records,
                message="Dashboard folder scan finished.",
            )
        except Exception as exc:  # noqa: BLE001
            if args.debug_artifacts:
                try:
                    save_debug_artifacts(page, artifacts_dir, "scan_folder_error")
                except Exception:
                    pass
            summary = DashboardScanSummary(
                ok=False,
                folder=args.folder,
                count=0,
                output_path=str(output_path),
                records=[],
                message=str(exc),
            )
        finally:
            browser.close()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_data = {
        "ok": summary.ok,
        "folder": summary.folder,
        "count": summary.count,
        "output_path": summary.output_path,
        "message": summary.message,
        "records": [record.__dict__ for record in summary.records],
    }
    output_path.write_text(json.dumps(output_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output_data, ensure_ascii=False, indent=2))
    return 0 if summary.ok else 1
