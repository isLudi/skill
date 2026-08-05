"""Publish one exact, verified permanent-template creation or update receipt."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from _shared.browser import import_playwright, launch_context
from _shared.env import load_env_file
from _shared.errors import UsageError

from usql_web_query.template_permanent import (
    PLAN_SCHEMA_VERSION,
    PUBLISH_RECEIPT_OPERATION,
    load_create_receipt,
    load_plan,
    load_template_sql,
    permanent_template_lock,
    template_sql_sha256,
    verify_template_readback,
    write_receipt,
)
from usql_web_query.template_query import TemplateQueryClient


def cmd_publish_template(args: argparse.Namespace) -> int:
    create_receipt = load_create_receipt(args.receipt_file)
    validate_publish_request(args, create_receipt)
    plan = load_plan(Path(str(create_receipt["plan_file"])))
    if create_receipt.get("plan_sha256") != plan.plan_sha256:
        raise UsageError("creation/update receipt does not bind the loaded permanent-template plan")
    sql_text = load_template_sql(Path(plan.sql_file))
    if template_sql_sha256(sql_text) != plan.sql_sha256:
        raise UsageError("template SQL file changed before publication")
    template_id = int(create_receipt["template_id"])

    load_env_file(args.env_file)
    args.state_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path = args.output_file or _default_receipt_path(args.artifacts_dir, template_id)
    receipt: dict[str, Any] = {
        "schema_version": PLAN_SCHEMA_VERSION,
        "operation": PUBLISH_RECEIPT_OPERATION,
        "ok": False,
        "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "create_receipt_file": str(args.receipt_file.expanduser().resolve()),
        "create_receipt_sha256": create_receipt["receipt_sha256"],
        "plan_sha256": plan.plan_sha256,
        "template_id": template_id,
        "template_name": plan.template_name,
        "remote_publish_performed": False,
        "automatic_delete_offline_or_rollback_attempted": False,
        "manual_attention_required": False,
    }
    sync_playwright = import_playwright()
    browser = None
    context = None
    page = None
    publish_requested = False
    try:
        with permanent_template_lock(plan.template_name):
            with sync_playwright() as playwright:
                browser, context = launch_context(
                    playwright,
                    args.state_path,
                    args.headed,
                    args.browser_channel,
                    args.executable_path,
                )
                page = context.new_page()
                client = TemplateQueryClient(page, args.state_path)
                client.ensure_authenticated(args.username, args.password)
                creator = str(client.fetch_auth_profile().get("name") or "").strip()
                if creator != plan.creator:
                    raise UsageError("authenticated Template Query creator changed before publication")
                before = client.fetch_template_detail(template_id)
                before_readback = verify_template_readback(before, plan, expected_status=1)
                publish_requested = True
                client.publish_template(template_id)
                after = client.fetch_template_detail(template_id)
                after_readback = verify_template_readback(after, plan, expected_status=2)

        receipt.update(
            {
                "ok": True,
                "status": "success",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "remote_publish_performed": True,
                "before_publish_readback": before_readback,
                "after_publish_readback": after_readback,
                "fully_verified": True,
            }
        )
        finalized = write_receipt(receipt_path, receipt)
        print(json.dumps({**finalized, "receipt_path": str(receipt_path.resolve())}, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        if args.debug_artifacts and page is not None:
            try:
                screenshot = receipt_path.with_suffix(".png")
                screenshot.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(screenshot), full_page=True)
                receipt["debug_screenshot"] = str(screenshot.resolve())
            except Exception:
                receipt["debug_screenshot"] = None
        receipt.update(
            {
                "ok": False,
                "status": "failed",
                "failed_at": datetime.now(timezone.utc).isoformat(),
                "error": str(exc),
                "remote_publish_performed": publish_requested,
                "manual_attention_required": publish_requested,
                "fully_verified": False,
            }
        )
        write_receipt(receipt_path, receipt)
        if isinstance(exc, UsageError):
            raise
        raise UsageError(f"permanent-template publication failed: {exc}") from exc
    finally:
        if context is not None:
            try:
                context.close()
            except Exception:
                pass
        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass


def validate_publish_request(args: argparse.Namespace, receipt: dict[str, Any]) -> None:
    if not args.confirm_publish:
        raise UsageError("publish-template requires --confirm-publish")
    if args.expected_receipt_sha256 != receipt.get("receipt_sha256"):
        raise UsageError(
            "permanent-template creation/update receipt hash mismatch: "
            f"expected={args.expected_receipt_sha256}, actual={receipt.get('receipt_sha256')}"
        )
    if not (
        receipt.get("ok") is True
        and receipt.get("status") == "success"
        and receipt.get("fully_verified") is True
        and receipt.get("template_id")
    ):
        raise UsageError("publish-template requires a successful fully verified creation/update receipt")


def _default_receipt_path(artifacts_dir: Path, template_id: int) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return artifacts_dir / f"permanent_template_publish_receipt_{stamp}_{template_id}.json"
