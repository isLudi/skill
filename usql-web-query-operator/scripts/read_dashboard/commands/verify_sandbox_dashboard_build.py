"""Offline verification for a complete immutable P4C sandbox evidence manifest."""

from __future__ import annotations

import json

from ..common import write_json
from ..dashboard_build_evidence import verify_dashboard_build_evidence_manifest
from ..dashboard_change import read_json_artifact


def cmd_verify_sandbox_dashboard_build(args) -> int:
    manifest = read_json_artifact(args.evidence_manifest, "DashboardBuildEvidenceManifest")
    result = verify_dashboard_build_evidence_manifest(manifest)
    if args.output:
        write_json(result, args.output)
        result["output_path"] = str(args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1
