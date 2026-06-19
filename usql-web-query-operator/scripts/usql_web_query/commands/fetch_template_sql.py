"""Fetch the stored SQL for a Template Query template created by the user."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from _shared.browser import import_playwright, launch_context
from _shared.config import TEMPLATE_QUERY_RUNTIME_DIR
from _shared.env import load_env_file
from _shared.fs_utils import ensure_runtime

from usql_web_query.template_query import (
    TemplateQueryClient,
    parse_status,
    write_template_sql,
)


def cmd_fetch_template_sql(args: argparse.Namespace) -> int:
    load_env_file(args.env_file)
    status = parse_status(args.status)
    output_file = args.output_file
    ensure_runtime([args.state_path.parent, args.artifacts_dir])

    sync_playwright = import_playwright()
    started_at = time.monotonic()
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
                match=args.match,
                status=status,
                page_size=args.page_size,
                max_pages=args.max_pages,
            )
        finally:
            context.close()
            browser.close()

    if output_file is None:
        output_file = _default_sql_path(args.artifacts_dir, selected.id)
    write_template_sql(output_file, selected.sql_detail)

    summary: dict[str, Any] = {
        "ok": True,
        "message": "Template SQL fetched.",
        "template": selected.to_summary_json(sql_path=output_file),
        "matchedCount": len(matches),
        "matches": [template.to_summary_json() for template in matches],
        "state_path": str(args.state_path),
        "artifacts_dir": str(args.artifacts_dir),
        "elapsed_seconds": round(time.monotonic() - started_at, 3),
    }
    if args.include_sql:
        summary["sql"] = selected.sql_detail
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def _default_sql_path(artifacts_dir: Path, template_id: int) -> Path:
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    return artifacts_dir / f"template_sql_{template_id}_{timestamp}.sql"
