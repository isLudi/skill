"""Capture redacted request-shape evidence from one manual sandbox dashboard action."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

from _shared.browser import import_playwright, launch_context
from _shared.env import load_env_file
from _shared.errors import UsageError
from _shared.fs_utils import ensure_runtime, safe_artifact_dir

from ..common import safe_filename, write_json
from ..dashboard_change import require_complete_profile
from ..edit_profile import build_edit_url, open_edit_page, profile_edit_dashboard
from ..write_capabilities import (
    build_probe_artifact,
    is_dangerous_request,
    load_capability_registry,
    preflight_manual_probe,
    request_observation,
)


def cmd_capture_write_evidence(args) -> int:
    if not 10 <= args.capture_seconds <= 300:
        raise UsageError("--capture-seconds must be between 10 and 300.")
    registry = load_capability_registry(args.registry)
    preflight_manual_probe(
        registry,
        operation=args.operation,
        dashboard_id=args.sandbox_dashboard_id,
        expected_dashboard_name=args.expected_dashboard_name,
        domain=args.domain,
        headed=args.headed,
        confirmed=args.confirm_sandbox_write,
    )

    load_env_file(args.env_file)
    sync_playwright = import_playwright()
    ensure_runtime([args.state_path.parent, args.artifacts_dir])
    artifacts_dir = safe_artifact_dir(args.artifacts_dir)
    edit_url = build_edit_url(args.sandbox_dashboard_id, args.html_id)
    output_path = args.output or (
        artifacts_dir
        / "write-capability-probes"
        / safe_filename(args.sandbox_dashboard_id)
        / f"{safe_filename(args.operation)}.probe.json"
    )
    observations: list[dict[str, object]] = []
    blocked_requests: list[dict[str, object]] = []
    started_at = datetime.now(timezone.utc).isoformat()

    with sync_playwright() as playwright:
        browser, context = launch_context(
            playwright,
            args.state_path,
            True,
            args.browser_channel,
            args.executable_path,
        )
        page = context.new_page()
        try:
            open_edit_page(page, args, context=context, edit_url=edit_url)
            before_raw = profile_edit_dashboard(
                page=page,
                dashboard_id=args.sandbox_dashboard_id,
                html_id=args.html_id,
                edit_url=edit_url,
                version_id="draft",
                artifacts_dir=artifacts_dir,
                debug_artifacts=args.debug_artifacts,
                include_dataset_fields=False,
                domain=args.domain,
            )
            before = require_complete_profile(before_raw, "Pre-probe sandbox dashboard profile")
            if str(before_raw.get("dashboard_name") or "") != args.expected_dashboard_name:
                raise UsageError(
                    "Sandbox dashboard name mismatch: "
                    f"expected {args.expected_dashboard_name!r}, got {before_raw.get('dashboard_name')!r}."
                )
            if before_raw.get("config_summary", {}).get("have_edit_permission") is not True:
                raise UsageError("Current identity does not have confirmed edit permission on the sandbox dashboard.")
            pending_by_url: dict[str, list[dict[str, object]]] = {}

            def observe_request(request) -> None:
                if str(request.method).upper() in {"GET", "HEAD", "OPTIONS"}:
                    return
                observation = request_observation(request)
                observations.append(observation)
                pending_by_url.setdefault(str(request.url), []).append(observation)

            def observe_response(response) -> None:
                pending = pending_by_url.get(str(response.url)) or []
                if not pending:
                    return
                observation = pending[-1]
                observation["response_status"] = int(response.status)
                observation["response_content_type"] = response.headers.get("content-type")

            def safety_route(route) -> None:
                request = route.request
                if is_dangerous_request(request):
                    blocked_requests.append(request_observation(request, blocked=True))
                    route.abort("blockedbyclient")
                    return
                route.continue_()

            page.on("request", observe_request)
            page.on("response", observe_response)
            page.route("**/*", safety_route)
            print(
                f"Perform exactly one manual sandbox action for {args.operation} in the visible dashboard. "
                f"Capture closes after {args.capture_seconds} seconds. Do not publish, delete, or edit permissions.",
                file=sys.stderr,
                flush=True,
            )
            page.wait_for_timeout(args.capture_seconds * 1000)
            page.unroute("**/*", safety_route)
            page.remove_listener("request", observe_request)
            page.remove_listener("response", observe_response)

            after_raw = profile_edit_dashboard(
                page=page,
                dashboard_id=args.sandbox_dashboard_id,
                html_id=args.html_id,
                edit_url=edit_url,
                version_id="draft",
                artifacts_dir=artifacts_dir,
                debug_artifacts=args.debug_artifacts,
                include_dataset_fields=False,
                domain=args.domain,
            )
            after = require_complete_profile(after_raw, "Post-probe sandbox dashboard profile")
        finally:
            browser.close()

    probe = build_probe_artifact(
        operation=args.operation,
        domain=args.domain,
        dashboard_id=args.sandbox_dashboard_id,
        dashboard_name=args.expected_dashboard_name,
        started_at=started_at,
        before_profile_sha256=str(before["profile_sha256"]),
        after_profile_sha256=str(after["profile_sha256"]),
        observations=observations,
        blocked_requests=blocked_requests,
    )
    write_json(probe, output_path)
    summary = {
        "ok": probe["status"] == "evidence_captured",
        "status": probe["status"],
        "operation": args.operation,
        "domain": args.domain,
        "sandbox_dashboard_id": args.sandbox_dashboard_id,
        "profile_changed": probe["profile_changed"],
        "observed_request_count": len(observations),
        "blocked_request_count": len(blocked_requests),
        "probe_sha256": probe["probe_sha256"],
        "output_path": str(output_path),
        "registry_promoted": False,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["ok"] else 1
