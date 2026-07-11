"""Profile selected dashboards under one BI folder."""

from __future__ import annotations

import json
import time

from _shared.auth import ensure_authenticated
from _shared.browser import import_playwright, launch_context
from _shared.env import load_env_file
from _shared.fs_utils import ensure_runtime, safe_artifact_dir

from ..common import parse_dashboard_names, write_json
from ..constants import DASHBOARD_MARKET_URL
from ..menu import collect_dashboard_records, fetch_dashboard_menu
from ..profile import profile_records
from ..value_health import policy_from_args


def cmd_profile_folder(args) -> int:
    load_env_file(args.env_file)
    sync_playwright = import_playwright()
    ensure_runtime([args.state_path.parent, args.artifacts_dir])
    artifacts_dir = safe_artifact_dir(args.artifacts_dir)
    output_dir = args.output_dir or artifacts_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    wanted_names = set(parse_dashboard_names(args.names))

    results: list[dict[str, object]] = []
    profiles: list[dict[str, object]] = []
    with sync_playwright() as playwright:
        browser, context = launch_context(playwright, args.state_path, args.headed, args.browser_channel, args.executable_path)
        page = context.new_page()
        try:
            ensure_authenticated(page, args, context=context)
            page.goto(DASHBOARD_MARKET_URL, wait_until="domcontentloaded", timeout=45_000)
            page.wait_for_timeout(args.wait_ms)
            records = collect_dashboard_records(fetch_dashboard_menu(page), args.folder)
            targets = [record for record in records if not wanted_names or record.name in wanted_names]
            missing = sorted(wanted_names - {record.name for record in targets})
            if missing:
                results.extend({"ok": False, "dashboard_name": name, "message": "Dashboard name not found in folder"} for name in missing)

            folder_results, folder_profiles = profile_records(
                page=page,
                folder_name=args.folder,
                records=targets,
                output_dir=output_dir,
                dashboard_wait_ms=args.dashboard_wait_ms,
                debug_artifacts=args.debug_artifacts,
                include_values=args.profile_mode == "full",
                value_policy=policy_from_args(args),
            )
            results.extend(folder_results)
            profiles.extend(
                {
                    "folder": args.folder,
                    "dashboard_name": item["record"].name,
                    "dashboard_id": item["record"].dashboard_id,
                    "profile_path": str(item["profile_path"]),
                    "profile": item["profile"],
                }
                for item in folder_profiles
            )
        finally:
            browser.close()

    consolidated = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "folder": args.folder,
        "output_dir": str(output_dir),
        "profile_mode": args.profile_mode,
        "target_count": len(results),
        "ok_count": sum(1 for item in results if item.get("ok")),
        "results": results,
        "profiles": profiles,
    }
    consolidated_path = output_dir / "profiles_consolidated.json"
    write_json(consolidated, consolidated_path)
    print(json.dumps({k: v for k, v in consolidated.items() if k != "profiles"}, ensure_ascii=False, indent=2))
    return 0 if all(item.get("ok") for item in results) else 1
