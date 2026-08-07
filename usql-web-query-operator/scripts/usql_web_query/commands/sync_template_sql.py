"""Sync one published Template Query SQL into a stable Skill canonical file."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any

from _shared.browser import import_playwright, launch_context
from _shared.domain_adapters import adapters_by_target
from _shared.env import load_env_file
from _shared.errors import UsageError

from usql_web_query.template_query import TemplateQueryClient
from usql_web_query.template_sql_knowledge import (
    apply_template_sql_plan,
    combined_plan_sha256,
    dry_run_result,
    plan_template_sql_sync,
)


def cmd_sync_template_sql(args: argparse.Namespace) -> int:
    validate_sync_write_mode(args)
    load_env_file(args.env_file)
    run_date = date.fromisoformat(args.run_date) if args.run_date else date.today()
    target = adapters_by_target()[args.target_skill]
    selected, matches = _fetch_published_template(args)
    if selected.id != args.template_id:
        raise UsageError(
            f"exact template identity mismatch: name {args.template_name!r} resolved to "
            f"id {selected.id}, expected {args.template_id}"
        )
    plan = plan_template_sql_sync(
        target,
        selected,
        canonical_file=args.canonical_file,
        run_date=run_date,
        update_changelog=args.update_changelog,
    )
    plan_sha256 = combined_plan_sha256([plan])
    plan_path = _plan_path(args.artifacts_dir, run_date=run_date, template_id=selected.id, plan_sha256=plan_sha256)
    plan_payload = {
        "schema_version": "1.0.0",
        "plan_sha256": plan_sha256,
        "status": plan.status,
        "plan": plan.to_json(),
    }
    _write_json(plan_path, plan_payload)

    if args.write:
        result = apply_template_sql_plan(plan, expected_plan_sha256=args.expected_plan_sha256)
    else:
        result = dry_run_result(plan, plan_sha256)

    output: dict[str, Any] = {
        "ok": True,
        "mode": "write" if args.write else "dry_run",
        "plan_sha256": plan_sha256,
        "plan_path": str(plan_path),
        "plan_status": plan.status,
        "target_skill": target.target,
        "domain": target.domain_id,
        "template": selected.to_summary_json(),
        "matched_count": len(matches),
        "remote_sql_sha256": plan.remote_sql_sha256,
        "canonical_sql_file": plan.to_json()["canonical_sql_file"],
        "result": result.to_json(),
    }
    if args.write:
        _write_json(_summary_path(args.artifacts_dir, run_date=run_date, template_id=selected.id), output)
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if plan.status == "ready" else 1


def validate_sync_write_mode(args: argparse.Namespace) -> None:
    if not args.write:
        return
    if not args.expected_plan_sha256:
        raise UsageError(
            "sync-template-sql --write requires --expected-plan-sha256 from a reviewed dry-run"
        )
    disabled: list[str] = []
    if not args.update_changelog:
        disabled.append("--no-update-changelog")
    if not args.rebuild_indexes:
        disabled.append("--no-rebuild-indexes")
    if not args.check_integrity:
        disabled.append("--no-check-integrity")
    if not args.validate_stack:
        disabled.append("--no-validate-stack")
    if disabled:
        raise UsageError("unsafe Template SQL knowledge-write options are forbidden: " + ", ".join(disabled))


def _fetch_published_template(args: argparse.Namespace):
    sync_playwright = import_playwright()
    args.state_path.parent.mkdir(parents=True, exist_ok=True)
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
            selected, matches = client.find_template(
                name=args.template_name,
                match="exact",
                status=2,
                page_size=args.page_size,
                max_pages=args.max_pages,
            )
            return selected, matches
        finally:
            context.close()
            browser.close()


def _plan_path(artifacts_dir: Path, *, run_date: date, template_id: int, plan_sha256: str) -> Path:
    return artifacts_dir / f"template_sql_plan_{template_id}_{run_date:%Y%m%d}_{plan_sha256[:12]}.json"


def _summary_path(artifacts_dir: Path, *, run_date: date, template_id: int) -> Path:
    return artifacts_dir / f"template_sql_sync_{template_id}_{run_date:%Y%m%d}.json"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
