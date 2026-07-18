"""Publish a successful DashboardBuildReceipt under a separate confirmation."""

from __future__ import annotations

import json

from _shared.browser import import_playwright, launch_context
from _shared.env import load_env_file
from _shared.fs_utils import ensure_runtime, safe_artifact_dir

from ..common import safe_filename, write_json
from ..dashboard_build import (
    preflight_publish_build,
    publish_dashboard_build,
    read_json_artifact,
)


def cmd_publish_dashboard_build(args) -> int:
    plan = read_json_artifact(args.build_plan, "DashboardBuildPlan")
    build_receipt = read_json_artifact(args.build_receipt, "DashboardBuildReceipt")
    preflight_publish_build(
        plan,
        args.build_plan_sha256,
        build_receipt,
        args.build_receipt_sha256,
        expected_domain=args.domain,
        confirmed=bool(args.confirm_publish),
        version_description=args.version_description,
    )

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
            receipt = publish_dashboard_build(
                page=page,
                args=args,
                plan=plan,
                build_receipt=build_receipt,
                artifacts_dir=artifacts_dir,
            )
        finally:
            browser.close()
    output_path = args.output or (
        artifacts_dir
        / safe_filename(str(plan.get("build_id") or "dashboard_build"))
        / "dashboard_build_publish_receipt.json"
    )
    write_json(receipt, output_path)
    summary = {
        "ok": bool(receipt.get("confirmed")),
        "domain": receipt.get("domain"),
        "dashboard_id": receipt.get("dashboard_id"),
        "publish_status": receipt.get("publish_status"),
        "verification_status": receipt.get("verification_status"),
        "fully_verified": receipt.get("fully_verified"),
        "dashboard_build_publish_receipt_sha256": receipt.get(
            "dashboard_build_publish_receipt_sha256"
        ),
        "output_path": str(output_path),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0
