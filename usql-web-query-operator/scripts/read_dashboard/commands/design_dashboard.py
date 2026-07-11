"""Build a domain-bound DashboardDesignSpec without browser writes."""

from __future__ import annotations

import json

from ..common import write_json
from ..dashboard_change import build_design_spec, read_json_artifact, require_resolved_domain


def cmd_design_dashboard(args) -> int:
    profile = read_json_artifact(args.profile, "DashboardProfile")
    require_resolved_domain(profile, args.domain)
    dataset_spec = read_json_artifact(args.dataset_spec, "DashboardDatasetSpec")
    desired_state = read_json_artifact(args.desired_state, "desired dashboard state") if args.desired_state else None
    design_spec = build_design_spec(
        dataset_spec,
        profile,
        desired_state,
        query_plan_sha256=args.query_plan_sha256,
        design_intent=args.design_intent,
    )
    write_json(design_spec, args.output)
    blocked = str(design_spec.get("status") or "") != "ready"
    summary = {
        "ok": not blocked,
        "dry_run": True,
        "write_calls": 0,
        "domain": design_spec.get("domain"),
        "dashboard_id": design_spec.get("dashboard_id"),
        "profile_sha256": design_spec.get("source_profile_sha256"),
        "design_sha256": design_spec.get("design_sha256"),
        "status": design_spec.get("status"),
        "diagnostics": design_spec.get("diagnostics") or [],
        "output_path": str(args.output),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 1 if blocked else 0
