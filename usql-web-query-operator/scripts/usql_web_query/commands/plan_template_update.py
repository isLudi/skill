"""Create a read-only, hash-bound in-place update plan for one permanent template."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from _shared.browser import import_playwright, launch_context
from _shared.env import load_env_file
from _shared.errors import UsageError

from usql_web_query.template_permanent import (
    build_permanent_template_plan,
    load_parameter_config,
    load_template_sql,
    normalize_readback_metadata,
    parse_display_name_overrides,
    sha256_json,
    template_sql_sha256,
    write_plan,
)
from usql_web_query.template_query import TemplateQueryClient


def cmd_plan_template_update(args: argparse.Namespace) -> int:
    """Read exact target/baseline/parser state and emit a plan without saving."""

    load_env_file(args.env_file)
    sql_text = load_template_sql(args.sql_file)
    parameter_config = load_parameter_config(args.parameter_config)
    variable_display_names = parse_display_name_overrides(args.variable_display_name)
    args.state_path.parent.mkdir(parents=True, exist_ok=True)
    sync_playwright = import_playwright()

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
            client = TemplateQueryClient(page, args.state_path)
            client.ensure_authenticated(args.username, args.password)
            auth_profile = client.fetch_auth_profile()
            creator = str(auth_profile.get("name") or "").strip()
            existing = [
                item
                for item in client.fetch_created_templates(
                    name=args.template_name,
                    page_size=100,
                    max_pages=20,
                )
                if item.name == args.template_name
            ]
            if [item.id for item in existing] != [args.template_id]:
                raise UsageError(
                    "exact-name template listing does not contain exactly the requested template id"
                )
            detail = client.fetch_template_detail(args.template_id)
            if int(detail.get("id") or 0) != args.template_id:
                raise UsageError("template detail id does not match the requested target id")
            if str(detail.get("name") or "") != args.template_name:
                raise UsageError("template detail name does not match the requested exact name")
            status = int(detail.get("status") or 0)
            if status not in {1, 2}:
                raise UsageError("in-place update requires an existing unpublished or published template")
            parser_payload = client.parse_sql(sql_text, instance_key=args.instance_key)
            baseline_state = {
                "id": args.template_id,
                "name": args.template_name,
                "status": status,
                "sql_sha256": template_sql_sha256(str(detail.get("sqlDetail") or "")),
                "metadata_sha256": sha256_json(normalize_readback_metadata(detail)),
            }
        finally:
            context.close()
            browser.close()

    plan = build_permanent_template_plan(
        template_name=args.template_name,
        description=args.template_description or "",
        owner=args.owner or "",
        creator=creator,
        sql_file=args.sql_file,
        sql_text=sql_text,
        instance_key=args.instance_key,
        existing_template_ids=[item.id for item in existing],
        parser_payload=parser_payload,
        parameter_config=parameter_config,
        variable_display_names=variable_display_names,
        target_template_id=args.template_id,
        baseline_state=baseline_state,
    )
    plan_path = args.output_file or _default_plan_path(args.artifacts_dir, plan.plan_sha256)
    write_plan(plan_path, plan)
    output = {
        "ok": plan.status == "ready",
        "mode": "read_only_update_plan",
        "status": plan.status,
        "plan_sha256": plan.plan_sha256,
        "plan_path": str(plan_path.resolve()),
        "template_id": args.template_id,
        "template_name": plan.template_name,
        "creator": plan.creator,
        "instance_key": plan.instance_key,
        "sql_file": plan.sql_file,
        "sql_sha256": plan.sql_sha256,
        "parser_sha256": plan.parser_sha256,
        "metadata_sha256": plan.metadata_sha256,
        "variable_count": len(plan.template_variables),
        "parameter_count": len(plan.template_params),
        "baseline_state": baseline_state,
        "diagnostics": list(plan.diagnostics),
        "remote_write_performed": False,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if plan.status == "ready" else 1


def _default_plan_path(artifacts_dir: Path, plan_sha256: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return artifacts_dir / f"permanent_template_update_plan_{stamp}_{plan_sha256[:12]}.json"
