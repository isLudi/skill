"""Apply one exact, supported DashboardChangePlan to a dashboard draft."""

from __future__ import annotations

import json

from _shared.browser import import_playwright, launch_context
from _shared.env import load_env_file
from _shared.fs_utils import ensure_runtime, safe_artifact_dir

from ..common import safe_filename, write_json
from ..dashboard_change import (
    apply_change_plan_to_draft,
    preflight_apply_plan,
    read_json_artifact,
)


def cmd_apply_dashboard_change(args) -> int:
    plan = read_json_artifact(args.change_plan, "DashboardChangePlan")
    # Preflight runs before Playwright import/browser launch. Unsupported or stale
    # plans therefore cannot accidentally reach any platform write endpoint.
    preflight_apply_plan(plan, args.change_plan_sha256, expected_domain=args.domain)

    load_env_file(args.env_file)
    sync_playwright = import_playwright()
    ensure_runtime([args.state_path.parent, args.artifacts_dir])
    artifacts_dir = safe_artifact_dir(args.artifacts_dir)

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
            receipt, pre_profile, post_profile = apply_change_plan_to_draft(
                page=page,
                args=args,
                plan=plan,
                supplied_sha256=args.change_plan_sha256,
                artifacts_dir=artifacts_dir,
            )
        finally:
            browser.close()

    dashboard_id = str(receipt.get("dashboard_id") or plan.get("dashboard_id") or "dashboard")
    output_path = args.output or (artifacts_dir / safe_filename(dashboard_id) / "dashboard_apply_receipt.json")
    write_json(receipt, output_path)
    summary = {
        "ok": bool(receipt.get("ok")),
        "domain": receipt.get("domain"),
        "dashboard_id": dashboard_id,
        "change_plan_sha256": receipt.get("change_plan_sha256"),
        "pre_profile_sha256": pre_profile.get("profile_sha256"),
        "post_profile_sha256": post_profile.get("profile_sha256"),
        "apply_receipt_sha256": receipt.get("apply_receipt_sha256"),
        "operation_count": len(receipt.get("operations") or receipt.get("operation_results") or []),
        "published": False,
        "output_path": str(output_path),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["ok"] else 1
