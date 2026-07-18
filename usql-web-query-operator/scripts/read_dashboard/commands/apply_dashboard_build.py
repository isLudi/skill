"""Apply one exact verified P4C DashboardBuildPlan to a new unpublished draft."""

from __future__ import annotations

import json

from _shared.browser import import_playwright, launch_context
from _shared.env import load_env_file
from _shared.fs_utils import ensure_runtime, safe_artifact_dir

from ..common import safe_filename, write_json
from ..dashboard_build import (
    execute_dashboard_build_saga,
    preflight_apply_build_plan,
    read_json_artifact,
)
from ..dashboard_build_adapters import resolve_production_build_adapter


def cmd_apply_dashboard_build(args) -> int:
    plan = read_json_artifact(args.build_plan, "DashboardBuildPlan")
    preflight_apply_build_plan(
        plan,
        args.build_plan_sha256,
        expected_domain=args.domain,
        confirmed=bool(args.confirm_production_write),
        registry_path=args.registry,
    )
    resume_receipt = (
        read_json_artifact(args.resume_receipt, "DashboardBuildReceipt")
        if args.resume_receipt
        else None
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
            adapter = resolve_production_build_adapter(plan, page=page, args=args)
            receipt = execute_dashboard_build_saga(
                plan,
                adapter,
                resume_receipt=resume_receipt,
            )
        finally:
            browser.close()

    output_path = args.output or (
        artifacts_dir
        / safe_filename(str(plan.get("build_id") or "dashboard_build"))
        / "dashboard_build_receipt.json"
    )
    write_json(receipt, output_path)
    summary = {
        "ok": bool(receipt.get("ok")),
        "status": receipt.get("status"),
        "domain": receipt.get("domain"),
        "build_id": receipt.get("build_id"),
        "dashboard_id": receipt.get("dashboard_id"),
        "dashboard_build_plan_sha256": receipt.get("dashboard_build_plan_sha256"),
        "dashboard_build_receipt_sha256": receipt.get("dashboard_build_receipt_sha256"),
        "created_resource_count": len(receipt.get("created_resources") or []),
        "reused_resource_count": len(receipt.get("reused_resources") or []),
        "orphaned_resource_count": len(receipt.get("orphaned_resources") or []),
        "manual_cleanup_required": bool(receipt.get("manual_cleanup_required")),
        "published": False,
        "output_path": str(output_path),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["ok"] else 1
