"""Explicit legacy helper-table maintenance; never part of current channel execution."""
from __future__ import annotations
import argparse
import json
from typing import Any, Mapping
from .market_schema import HELPER_RAW_FIELDS, HELPER_DIMENSION_FIELDS
from .market_aggregation import _raw_field
from ..common.values import _string


def _dimension_record(row: Mapping[str, Any]) -> dict[str, str] | None:
    consultant = _string(_raw_field(row, "顾问"))
    supervisor = _string(_raw_field(row, "主管"))
    channel = _string(_raw_field(row, "渠道"))
    if not consultant or not supervisor or not channel:
        return None
    return {
        "维度键": "%s|%s|%s" % (consultant, supervisor, channel),
        "顾问": consultant,
        "主管": supervisor,
        "渠道": channel,
    }


def sync_helper_dimension(args: argparse.Namespace, *, services) -> int:
    """Append missing consultant/team dimension rows without deleting anything."""

    source_coords = services.resolve_coordinates(args)
    helper_table_id = services._string(args.helper_table_id)
    raw_table_id = services._string(args.helper_raw_table_id)
    raw_coords = {
        "base_token": source_coords["base_token"],
        "table_id": raw_table_id,
        "view_id": "",
    }
    helper_coords = {
        "base_token": source_coords["base_token"],
        "table_id": helper_table_id,
        "view_id": "",
    }
    raw_records = services._fetch_view_records(coords=raw_coords, args=args, fields=HELPER_RAW_FIELDS, temp_prefix=".ip-helper-raw-pages-")
    existing_records = services._fetch_view_records(coords=helper_coords, args=args, fields=HELPER_DIMENSION_FIELDS, temp_prefix=".ip-helper-existing-pages-")
    candidates: dict[str, dict[str, str]] = {}
    for row in raw_records:
        dimension = _dimension_record(row)
        if dimension:
            candidates[dimension["维度键"]] = dimension
    existing_keys = {
        services._string(services._raw_field(row, "维度键"))
        for row in existing_records
        if services._string(services._raw_field(row, "维度键"))
    }
    missing = [candidates[key] for key in sorted(candidates) if key not in existing_keys]
    report: dict[str, Any] = {
        "mode": "helper_sync_preview" if not args.confirm_helper_sync else "helper_sync",
        "raw_table": raw_table_id,
        "helper_table": helper_table_id,
        "raw_row_count": len(raw_records),
        "existing_dimension_count": len(existing_records),
        "candidate_dimension_count": len(candidates),
        "missing_dimension_count": len(missing),
        "missing_dimensions": [row["维度键"] for row in missing],
        "created_dimension_count": 0,
    }
    if not args.confirm_helper_sync or not missing:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    for start in range(0, len(missing), 200):
        batch = missing[start : start + 200]
        payload = json.dumps({"create_records": batch}, ensure_ascii=False, separators=(",", ":"))
        response = services._unwrap(
            services._json_payload(
                services.run_lark(
                    [
                        "base",
                        "+record-batch-create",
                        "--base-token",
                        source_coords["base_token"],
                        "--table-id",
                        helper_table_id,
                        "--json",
                        payload,
                        "--format",
                        "json",
                        "--as",
                        args.base_as,
                    ],
                    timeout=args.timeout,
                )
            )
        )
        if response is None:
            raise RuntimeError("提醒计算表维度行写入未返回成功响应")
        report["created_dimension_count"] += len(batch)
    report["status"] = "synced"
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0
