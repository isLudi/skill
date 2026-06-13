"""Capture one dashboard after applying a target period filter."""

from __future__ import annotations

import json

from _shared.auth import ensure_authenticated
from _shared.browser import import_playwright, launch_browser
from _shared.env import load_env_file
from _shared.fs_utils import ensure_runtime, safe_artifact_dir

from ..capture import capture_dashboard_period, period_slug


def cmd_capture_dashboard(args) -> int:
    load_env_file(args.env_file)
    sync_playwright = import_playwright()
    ensure_runtime([args.state_path.parent, args.artifacts_dir])
    artifacts_dir = safe_artifact_dir(args.artifacts_dir)
    period_tag = period_slug(args.period)
    output_dir = args.output_dir or (artifacts_dir / f"{args.dashboard_id}_{period_tag}")

    with sync_playwright() as playwright:
        browser = launch_browser(playwright, args.headed, args.browser_channel, args.executable_path)
        context_kwargs = {
            "viewport": {"width": args.viewport_width, "height": args.viewport_height},
            "device_scale_factor": args.device_scale_factor,
            "accept_downloads": True,
        }
        if args.state_path.exists():
            context_kwargs["storage_state"] = str(args.state_path)
        context = browser.new_context(**context_kwargs)
        page = context.new_page()
        try:
            ensure_authenticated(page, args, context=context)
            summary = capture_dashboard_period(
                page=page,
                dashboard_id=args.dashboard_id,
                dashboard_name=args.dashboard_name,
                folder_name=args.folder,
                period=args.period,
                wait_ms=args.wait_ms,
                apply_wait_ms=args.apply_wait_ms,
                output_dir=output_dir,
                debug_artifacts=args.debug_artifacts,
            )
        finally:
            browser.close()

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary.get("ok") else 1
