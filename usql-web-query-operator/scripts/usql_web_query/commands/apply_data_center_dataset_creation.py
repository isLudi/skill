"""Apply one reviewed Data Center dataset creation in production."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from _shared.browser import import_playwright, launch_context
from _shared.env import load_env_file
from _shared.errors import UsageError

from usql_web_query.data_center import DataCenterClient
from usql_web_query.data_center_creation import (
    data_center_creation_lock,
    load_creation_plan,
    load_creation_sql,
)
from usql_web_query.data_center_creation_write import DataCenterCreationExecutor
from usql_web_query.data_center_replacement import sql_sha256


def cmd_apply_data_center_dataset_creation(args: argparse.Namespace) -> int:
    """Run the production create chain and persist a success/failure receipt."""

    plan = load_creation_plan(args.plan_file)
    validate_apply_request(args, plan)
    sql_text = load_creation_sql(Path(plan.sql_file))
    if sql_sha256(sql_text) != plan.sql_sha256:
        raise UsageError("creation SQL file changed after the reviewed plan was created")

    load_env_file(args.env_file)
    args.state_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path = args.output_file or _default_receipt_path(args.artifacts_dir, plan.plan_sha256)
    receipt: dict[str, Any] = {
        "schema_version": "1.0.0",
        "operation": "apply_data_center_dataset_creation",
        "ok": False,
        "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "plan_file": str(args.plan_file.expanduser().resolve()),
        "plan_sha256": plan.plan_sha256,
        "folder": plan.folder,
        "dataset_name": plan.dataset_name,
        "sql_sha256": plan.sql_sha256,
        "remote_write_performed": False,
        "automatic_delete_or_rollback_attempted": False,
        "manual_attention_required": False,
    }

    sync_playwright = import_playwright()
    executor: DataCenterCreationExecutor | None = None
    browser = None
    context = None
    page = None
    try:
        with data_center_creation_lock(str(plan.folder.get("id") or ""), plan.dataset_name):
            with sync_playwright() as playwright:
                browser, context = launch_context(
                    playwright,
                    args.state_path,
                    args.headed,
                    args.browser_channel,
                    args.executable_path,
                )
                page = context.new_page()
                client = DataCenterClient(page, args.state_path)
                client.ensure_authenticated(args.username, args.password)
                executor = DataCenterCreationExecutor(
                    page=page,
                    client=client,
                    plan=plan,
                    sql_text=sql_text,
                    preview_timeout_ms=args.preview_timeout_ms,
                    refresh_timeout_ms=args.refresh_timeout_ms,
                    poll_interval_ms=args.poll_interval_ms,
                )
                workflow = executor.execute()
                receipt.update(
                    {
                        "ok": True,
                        "status": "success",
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                        "remote_write_performed": True,
                        "workflow": workflow,
                        "fully_verified": workflow.get("fully_verified") is True,
                    }
                )
                _write_receipt(receipt_path, receipt)
                print(
                    json.dumps(
                        {**receipt, "receipt_path": str(receipt_path.resolve())},
                        ensure_ascii=False,
                        indent=2,
                    )
                )
                return 0
    except Exception as exc:
        progress = dict(executor.progress) if executor is not None else {"phase": "startup"}
        remote_write = bool(
            progress.get("remote_dataset_created") or progress.get("refresh_triggered")
        )
        debug_screenshot = None
        if args.debug_artifacts and page is not None:
            debug_screenshot = receipt_path.with_suffix(".png")
            try:
                page.screenshot(path=str(debug_screenshot), full_page=True)
            except Exception:
                debug_screenshot = None
        receipt.update(
            {
                "ok": False,
                "status": "failed",
                "failed_at": datetime.now(timezone.utc).isoformat(),
                "error": str(exc),
                "remote_write_performed": remote_write,
                "manual_attention_required": remote_write,
                "workflow": progress,
                "fully_verified": False,
                "debug_screenshot": str(debug_screenshot) if debug_screenshot else None,
            }
        )
        _write_receipt(receipt_path, receipt)
        if isinstance(exc, UsageError):
            raise
        raise UsageError(f"Data Center creation failed: {exc}") from exc
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


def validate_apply_request(args: argparse.Namespace, plan: Any) -> None:
    if not args.confirm_production_write:
        raise UsageError(
            "apply-data-center-dataset-creation requires --confirm-production-write"
        )
    if not args.expected_plan_sha256:
        raise UsageError(
            "apply-data-center-dataset-creation requires --expected-plan-sha256"
        )
    if args.expected_plan_sha256 != plan.plan_sha256:
        raise UsageError(
            "Data Center creation plan hash mismatch: "
            f"expected={args.expected_plan_sha256}, actual={plan.plan_sha256}"
        )
    if plan.status != "ready":
        raise UsageError("Data Center creation plan is blocked")


def _default_receipt_path(artifacts_dir: Path, plan_sha256: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return artifacts_dir / f"data_center_creation_receipt_{stamp}_{plan_sha256[:12]}.json"


def _write_receipt(path: Path, receipt: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )
