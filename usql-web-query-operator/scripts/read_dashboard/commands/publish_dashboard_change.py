"""Publish only a verified draft from an exact ApplyReceipt and ChangePlan."""

from __future__ import annotations

import json

from _shared.browser import import_playwright, launch_context
from _shared.env import load_env_file
from _shared.errors import UsageError
from _shared.fs_utils import ensure_runtime, safe_artifact_dir

from ..common import safe_filename, write_json
from ..dashboard_change import (
    artifact_sha256,
    preflight_apply_plan,
    preflight_publish_receipt,
    publish_applied_draft,
    read_json_artifact,
)


def cmd_publish_dashboard_change(args) -> int:
    plan = read_json_artifact(args.change_plan, "DashboardChangePlan")
    preflight_apply_plan(plan, args.change_plan_sha256, expected_domain=args.domain)
    apply_receipt = read_json_artifact(args.apply_receipt, "DashboardApplyReceipt")
    preflight_publish_receipt(
        apply_receipt,
        plan,
        args.apply_receipt_sha256,
        expected_domain=args.domain,
        confirmed=args.confirm_publish,
    )
    if str(apply_receipt.get("change_plan_sha256") or "") != artifact_sha256(plan, "change_plan_sha256"):
        raise UsageError("ApplyReceipt does not bind the supplied ChangePlan.")

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
            receipt = publish_applied_draft(
                page=page,
                args=args,
                apply_receipt=apply_receipt,
                change_plan=plan,
                supplied_sha256=args.apply_receipt_sha256,
                artifacts_dir=artifacts_dir,
            )
        finally:
            browser.close()

    dashboard_id = str(receipt.get("dashboard_id") or apply_receipt.get("dashboard_id") or "dashboard")
    output_path = args.output or (artifacts_dir / safe_filename(dashboard_id) / "dashboard_publish_receipt.json")
    write_json(receipt, output_path)
    summary = {
        "ok": bool(receipt.get("ok")),
        "domain": receipt.get("domain"),
        "dashboard_id": dashboard_id,
        "apply_receipt_sha256": receipt.get("apply_receipt_sha256"),
        "publish_receipt_sha256": receipt.get("publish_receipt_sha256"),
        "publish_status": receipt.get("publish_status"),
        "verification_status": receipt.get("verification_status"),
        "fully_verified": receipt.get("fully_verified"),
        "confirmed": receipt.get("confirmed"),
        "output_path": str(output_path),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["ok"] else 1
