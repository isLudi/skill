"""Diff a profile and design spec into a zero-write DashboardChangePlan."""

from __future__ import annotations

import json

from ..common import write_json
from ..dashboard_change import build_change_plan, read_json_artifact, require_resolved_domain


def cmd_plan_dashboard_change(args) -> int:
    profile = read_json_artifact(args.profile, "DashboardProfile")
    require_resolved_domain(profile, args.domain)
    design_spec = read_json_artifact(args.design_spec, "DashboardDesignSpec")
    plan = build_change_plan(profile, design_spec)
    write_json(plan, args.output)
    blocked = bool(plan.get("blocked_reasons")) or str(plan.get("status") or "").lower() == "blocked"
    summary = {
        "ok": not blocked,
        "dry_run": True,
        "write_calls": 0,
        "domain": plan.get("domain"),
        "dashboard_id": plan.get("dashboard_id"),
        "profile_sha256": (
            plan.get("base_profile_sha256")
            or plan.get("profile_sha256")
            or plan.get("source_profile_sha256")
        ),
        "design_sha256": plan.get("design_sha256"),
        "change_plan_sha256": plan.get("change_plan_sha256"),
        "operation_count": len(plan.get("operations") or []),
        "blocked_reasons": plan.get("blocked_reasons") or [],
        "output_path": str(args.output),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["ok"] else 1
