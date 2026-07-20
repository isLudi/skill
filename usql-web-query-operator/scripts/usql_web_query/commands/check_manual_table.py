"""Check registered manual temp-table mappings and local workbook rules."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from usql_web_query.manual_table_registry import ManualTableRegistry
from usql_web_query.manual_table_validation import validate_manual_table


def cmd_check_manual_table(args: argparse.Namespace) -> int:
    registry = ManualTableRegistry.load(args.registry_path)
    records = []
    if args.file:
        for file_path in args.file:
            records.append(_record_for_file(registry, file_path.resolve()))
    else:
        for entry in registry.entries():
            records.append(_record_for_entry(entry.file_path.resolve(), entry))

    error_count = sum(record["validation"].get("error_count", 0) for record in records)
    warning_count = sum(record["validation"].get("warning_count", 0) for record in records)
    review_required_count = sum(
        1 for record in records if (record.get("mapping") or {}).get("auto_target") is False
    )
    summary = {
        "ok": error_count == 0 and (not args.strict or review_required_count == 0),
        "registry_path": str(registry.path),
        "checked_count": len(records),
        "error_count": error_count,
        "warning_count": warning_count,
        "review_required_count": review_required_count,
        "records": records,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 1 if args.strict and not summary["ok"] else 0


def _record_for_file(registry: ManualTableRegistry, file_path: Path) -> dict[str, Any]:
    entry = registry.resolve_file(file_path)
    return _record_for_entry(file_path, entry)


def _record_for_entry(file_path: Path, entry: Any) -> dict[str, Any]:
    validation = validate_manual_table(file_path, entry)
    mapping = entry.as_summary() if entry else None
    return {
        "file_path": str(file_path),
        "exists": file_path.exists(),
        "mapping": mapping,
        "auto_target_table": entry.standard_temp_table if entry and entry.auto_target else None,
        "requires_explicit_target": bool(entry and entry.standard_temp_table and not entry.auto_target),
        "validation": validation,
    }
