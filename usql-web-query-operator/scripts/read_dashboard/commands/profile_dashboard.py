"""Profile one dashboard and write its raw JSON summary."""

from __future__ import annotations

import json

from _shared.auth import ensure_authenticated
from _shared.browser import import_playwright, launch_context
from _shared.env import load_env_file
from _shared.fs_utils import ensure_runtime, safe_artifact_dir

from ..profile import build_error_profile, build_profile_summary, profile_dashboard
from ..common import write_json
from ..value_health import policy_from_args


def cmd_profile_dashboard(args) -> int:
    load_env_file(args.env_file)
    sync_playwright = import_playwright()
    ensure_runtime([args.state_path.parent, args.artifacts_dir])
    artifacts_dir = safe_artifact_dir(args.artifacts_dir)
    dashboard_id = args.dashboard_id
    output_path = args.output or (artifacts_dir / f"{dashboard_id}_profile.json")

    with sync_playwright() as playwright:
        browser, context = launch_context(playwright, args.state_path, args.headed, args.browser_channel, args.executable_path)
        page = context.new_page()
        try:
            ensure_authenticated(page, args, context=context)
            profile = profile_dashboard(
                page=page,
                dashboard_id=dashboard_id,
                dashboard_name=args.dashboard_name,
                folder_name=args.folder,
                wait_ms=args.wait_ms,
                artifacts_dir=artifacts_dir,
                debug_artifacts=args.debug_artifacts,
                include_values=args.profile_mode == "full",
                value_policy=policy_from_args(args),
            )
        except Exception as exc:  # noqa: BLE001
            profile = build_error_profile(dashboard_id, args.dashboard_name or dashboard_id, args.folder, str(exc))
        finally:
            browser.close()

    write_json(profile, output_path)
    summary = build_profile_summary(profile, output_path)
    print(json.dumps(summary.__dict__, ensure_ascii=False, indent=2))
    return 0 if summary.ok else 1
