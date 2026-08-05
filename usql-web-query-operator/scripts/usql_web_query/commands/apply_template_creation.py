"""Create one reviewed permanent parameterized template as an unpublished draft."""

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
    CREATE_RECEIPT_OPERATION,
    UPDATE_PLAN_OPERATION,
    UPDATE_RECEIPT_OPERATION,
    PLAN_SCHEMA_VERSION,
    load_plan,
    load_template_sql,
    normalize_readback_metadata,
    permanent_template_lock,
    sha256_json,
    template_params_for_save,
    template_sql_sha256,
    validate_parser_drift,
    verify_template_readback,
    write_receipt,
)
from usql_web_query.template_query import TemplateQueryClient


def cmd_apply_template_creation(args: argparse.Namespace) -> int:
    plan = load_plan(args.plan_file)
    validate_apply_request(args, plan)
    is_update = plan.operation == UPDATE_PLAN_OPERATION
    sql_text = load_template_sql(Path(plan.sql_file))
    if template_sql_sha256(sql_text) != plan.sql_sha256:
        raise UsageError("template SQL file changed after the reviewed plan was created")

    load_env_file(args.env_file)
    args.state_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path = args.output_file or _default_receipt_path(args.artifacts_dir, plan.plan_sha256)
    receipt: dict[str, Any] = {
        "schema_version": PLAN_SCHEMA_VERSION,
        "operation": UPDATE_RECEIPT_OPERATION if is_update else CREATE_RECEIPT_OPERATION,
        "ok": False,
        "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "plan_file": str(args.plan_file.expanduser().resolve()),
        "plan_sha256": plan.plan_sha256,
        "template_name": plan.template_name,
        "sql_sha256": plan.sql_sha256,
        "metadata_sha256": plan.metadata_sha256,
        "remote_write_performed": False,
        "automatic_delete_offline_or_rollback_attempted": False,
        "in_place_update": is_update,
        "manual_attention_required": False,
    }
    sync_playwright = import_playwright()
    browser = None
    context = None
    page = None
    save_requested = False
    saved_template_id: int | None = None
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
                    raise UsageError("authenticated Template Query creator changed after planning")
                exact_matches = [
                    item
                    for item in client.fetch_created_templates(
                        name=plan.template_name,
                        page_size=100,
                        max_pages=20,
                    )
                    if item.name == plan.template_name
                ]
                if sorted(item.id for item in exact_matches) != sorted(plan.baseline_template_ids):
                    raise UsageError("exact-name Template Query state drifted after planning")
                target_template_id = int(plan.policy.get("target_template_id") or 0)
                if is_update:
                    if target_template_id <= 0:
                        raise UsageError("update plan is missing its exact target template id")
                    if sorted(item.id for item in exact_matches) != [target_template_id]:
                        raise UsageError("exact-name Template Query update target drifted after planning")
                    baseline = plan.policy.get("baseline_state") or {}
                    current = client.fetch_template_detail(target_template_id)
                    if int(current.get("id") or 0) != target_template_id:
                        raise UsageError("template update target id readback mismatch before save")
                    if str(current.get("name") or "") != plan.template_name:
                        raise UsageError("template update target name mismatch before save")
                    if int(current.get("status") or 0) != int(baseline.get("status") or 0):
                        raise UsageError("template update target status drifted after planning")
                    if baseline.get("sql_sha256") and template_sql_sha256(str(current.get("sqlDetail") or "")) != baseline["sql_sha256"]:
                        raise UsageError("template update target SQL drifted after planning")
                    if baseline.get("metadata_sha256") and sha256_json(normalize_readback_metadata(current)) != baseline["metadata_sha256"]:
                        raise UsageError("template update target metadata drifted after planning")
                parser_payload = client.parse_sql(sql_text, instance_key=plan.instance_key)
                validate_parser_drift(parser_payload, plan)
                save_requested = True
                saved = client.save_template(
                    name=plan.template_name,
                    description=plan.description,
                    sql=sql_text,
                    creator=plan.creator,
                    owner=plan.owner,
                    instance_key=plan.instance_key,
                    template_variables=[dict(item) for item in plan.template_variables],
                    template_params=template_params_for_save(plan.template_params),
                    baseline_template_ids=set(plan.baseline_template_ids),
                    template_id=target_template_id if is_update else None,
                )
                saved_template_id = saved.id
                detail = client.fetch_template_detail(saved.id)
                readback = verify_template_readback(detail, plan, expected_status=1)

        receipt.update(
            {
                "ok": True,
                "status": "success",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "remote_write_performed": True,
                "template_id": saved_template_id,
                "readback": readback,
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
                "remote_write_performed": save_requested,
                "template_id": saved_template_id,
                "manual_attention_required": save_requested,
                "fully_verified": False,
            }
        )
        write_receipt(receipt_path, receipt)
        if isinstance(exc, UsageError):
            raise
        raise UsageError(f"permanent-template {'update' if is_update else 'creation'} failed: {exc}") from exc
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
        raise UsageError("apply-template-creation requires --confirm-production-write")
    if args.expected_plan_sha256 != plan.plan_sha256:
        raise UsageError(
            "permanent-template plan hash mismatch: "
            f"expected={args.expected_plan_sha256}, actual={plan.plan_sha256}"
        )
    if plan.status != "ready":
        raise UsageError("permanent-template creation/update plan is blocked")
    if plan.operation not in {"create_permanent_parameterized_template", UPDATE_PLAN_OPERATION}:
        raise UsageError("unsupported permanent-template apply plan operation")


def _default_receipt_path(artifacts_dir: Path, plan_sha256: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return artifacts_dir / f"permanent_template_create_receipt_{stamp}_{plan_sha256[:12]}.json"
