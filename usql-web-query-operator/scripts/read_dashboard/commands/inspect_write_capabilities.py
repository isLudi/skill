"""Inspect the validated P4A/P4B dashboard write capability registry."""

from __future__ import annotations

import json

from ..common import write_json
from ..write_capabilities import load_capability_registry, registry_summary


def cmd_inspect_write_capabilities(args) -> int:
    registry = load_capability_registry(args.registry)
    summary = registry_summary(registry)
    if args.output:
        write_json(registry, args.output)
        summary["output_path"] = str(args.output)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0
