"""Profile metric meanings and formulas from a Taitan dashboard edit page."""

from __future__ import annotations

import json

from _shared.browser import import_playwright, launch_context
from _shared.env import load_env_file
from _shared.errors import UsageError
from _shared.fs_utils import ensure_runtime, safe_artifact_dir

from ..common import write_json
from ..dashboard_change import normalize_profile
from ..edit_profile import (
    build_edit_error_profile,
    build_edit_profile_summary,
    build_edit_url,
    canonical_dashboard_id,
    open_edit_page,
    parse_edit_url,
    profile_edit_dashboard,
)


def cmd_profile_edit_dashboard(args) -> int:
    load_env_file(args.env_file)
    sync_playwright = import_playwright()
    ensure_runtime([args.state_path.parent, args.artifacts_dir])
    artifacts_dir = safe_artifact_dir(args.artifacts_dir)

    parsed_url = parse_edit_url(args.edit_url)
    dashboard_id = canonical_dashboard_id(args.dashboard_id or parsed_url.get("dashboard_id") or "")
    html_id = args.html_id or parsed_url.get("html_id")
    if not dashboard_id:
        raise UsageError("--dashboard-id or --edit-url with dashboardId is required.")
    edit_url = args.edit_url or build_edit_url(dashboard_id, html_id)
    output_path = args.output or (artifacts_dir / f"{dashboard_id}_edit_metrics_profile.json")

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
            open_edit_page(page, args, context=context, edit_url=edit_url)
            profile = profile_edit_dashboard(
                page=page,
                dashboard_id=dashboard_id,
                html_id=html_id,
                edit_url=edit_url,
                version_id=args.version_id,
                artifacts_dir=artifacts_dir,
                debug_artifacts=args.debug_artifacts,
                include_dataset_fields=not args.skip_dataset_fields,
                domain=args.domain,
            )
        except Exception as exc:  # noqa: BLE001
            profile = build_edit_error_profile(dashboard_id, edit_url, args.version_id, str(exc), domain=args.domain)
        finally:
            browser.close()

    normalized_output_path = args.normalized_output
    if profile.get("ok"):
        normalized_profile = normalize_profile(profile)
        profile["profile_sha256"] = normalized_profile["profile_sha256"]
        profile["normalized_profile"] = normalized_profile
        if normalized_output_path:
            write_json(normalized_profile, normalized_output_path)
    write_json(profile, output_path)
    summary = build_edit_profile_summary(profile, output_path)
    summary["normalized_output_path"] = str(normalized_output_path) if normalized_output_path else None
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["ok"] else 1
