"""Run bounded runtime value health checks from a cached config profile."""

from __future__ import annotations

import json

from _shared.auth import ensure_authenticated
from _shared.browser import import_playwright, launch_context
from _shared.env import load_env_file
from _shared.errors import UsageError
from _shared.fs_utils import ensure_runtime, safe_artifact_dir

from ..common import write_json
from ..profile import dashboard_url, probe_profile_values
from ..value_health import policy_from_args


def cmd_check_dashboard_values(args) -> int:
    load_env_file(args.env_file)
    if not args.profile.is_file():
        raise UsageError(f"Dashboard config profile does not exist: {args.profile}")
    profile = json.loads(args.profile.read_text(encoding="utf-8"))
    if profile.get("profile_mode") not in {"config_only", "full"}:
        raise UsageError("--profile must be a dashboard config profile created by profile-dashboard/folder/all.")
    dashboard_id = str(profile.get("dashboard_id") or "")
    if not dashboard_id:
        raise UsageError("Dashboard config profile is missing dashboard_id.")

    sync_playwright = import_playwright()
    ensure_runtime([args.state_path.parent, args.artifacts_dir])
    artifacts_dir = safe_artifact_dir(args.artifacts_dir)
    output_path = args.output or (artifacts_dir / f"{dashboard_id}_value_health.json")

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
            page.goto(
                str(profile.get("open_url") or dashboard_url(dashboard_id)),
                wait_until="domcontentloaded",
                timeout=45_000,
            )
            page.wait_for_timeout(args.wait_ms)
            health = probe_profile_values(page, profile, policy_from_args(args))
        finally:
            browser.close()

    write_json(health, output_path)
    summary = {
        "ok": bool(health.get("ok")),
        "dashboard_id": dashboard_id,
        "dashboard_name": profile.get("dashboard_name"),
        "source_profile": str(args.profile),
        "output_path": str(output_path),
        **(health.get("refresh_validation") or {}),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["ok"] else 1
