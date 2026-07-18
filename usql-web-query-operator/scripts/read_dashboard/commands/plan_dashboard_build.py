"""Build a zero-write P4C DashboardBuildPlan from a declarative spec."""

from __future__ import annotations

import json

from ..common import write_json
from ..dashboard_build import (
    bind_build_upstream_artifacts,
    normalize_build_spec,
    plan_dashboard_build,
    read_json_artifact,
)


def cmd_plan_dashboard_build(args) -> int:
    raw_spec = read_json_artifact(args.build_spec, "DashboardBuildSpec")
    spec = normalize_build_spec(raw_spec)
    raw_resolutions = (
        read_json_artifact(args.dataset_resolutions, "DashboardDatasetResolutions")
        if args.dataset_resolutions
        else None
    )
    resolutions = bind_build_upstream_artifacts(spec, raw_resolutions)
    name_available = None
    if args.dashboard_name_available:
        name_available = True
    if args.dashboard_name_conflict:
        name_available = False
    plan = plan_dashboard_build(
        spec,
        resolutions,
        folder_snapshot_sha256=args.folder_snapshot_sha256,
        dashboard_name_available=name_available,
    )
    write_json(plan, args.output)
    summary = {
        "ok": plan.get("status") == "ready",
        "dry_run": True,
        "write_calls": 0,
        "domain": plan.get("domain"),
        "build_id": plan.get("build_id"),
        "dashboard_name": plan.get("dashboard_name"),
        "status": plan.get("status"),
        "dashboard_build_spec_sha256": plan.get("dashboard_build_spec_sha256"),
        "dashboard_build_plan_sha256": plan.get("dashboard_build_plan_sha256"),
        "target_state_sha256": plan.get("target_state_sha256"),
        "pending_reasons": plan.get("pending_reasons") or [],
        "blocked_reasons": plan.get("blocked_reasons") or [],
        "output_path": str(args.output),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["ok"] else 1
