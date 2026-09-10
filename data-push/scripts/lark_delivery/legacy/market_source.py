"""Legacy view/config reading; transport supplied by the compatibility facade."""
from __future__ import annotations
import argparse
import json
from typing import Any, Mapping
from urllib.parse import parse_qs, urlparse
from .market_schema import TEXT_FIELDS, RESULT_FIELDS
from . import market_leads as lead_report


def resolve_text_coordinates(args: argparse.Namespace, source_coords: Mapping[str, str], *, services) -> dict[str, str]:
    """Resolve the independent message-config table in the same Base."""

    base_token = services._string(source_coords.get("base_token"))
    table_id = services._string(getattr(args, "text_table_id", ""))
    view_id = services._string(getattr(args, "text_view_id", ""))
    source_url = services._string(getattr(args, "text_source_url", ""))
    if source_url and (not table_id or not view_id):
        resolved = services._unwrap(
            services._json_payload(
                services.run_lark(
                    [
                        "base",
                        "+url-resolve",
                        "--url",
                        source_url,
                        "--format",
                        "json",
                        "--as",
                        args.base_as,
                    ],
                    timeout=args.timeout,
                )
            )
        )
        resolved_base = services._string(services._find_first(resolved, ("base_token", "baseToken")))
        if resolved_base and base_token and resolved_base != base_token:
            raise SystemExit("推送文字表必须与过程数据表位于同一个 Base")
        table_id = table_id or services._string(services._find_first(resolved, ("table_id", "tableId")))
        view_id = view_id or services._string(services._find_first(resolved, ("view_id", "viewId")))
        query = parse_qs(urlparse(source_url).query)
        table_id = table_id or (query.get("table", [""])[0] or "")
        view_id = view_id or (query.get("view", [""])[0] or "")

    if not table_id or not view_id:
        raise SystemExit(
            "推送文字坐标不完整：请设置 --text-table-id、--text-view-id，"
            "或提供 --text-source-url"
        )
    return {
        "base_token": base_token,
        "table_id": table_id,
        "view_id": view_id,
        "source_url": source_url,
    }


def fetch_records(coords: Mapping[str, str], args: argparse.Namespace, *, services) -> list[dict[str, Any]]:
    """Read the complete process-data view."""

    return services._fetch_view_records(coords, args, services._source_fields(), temp_prefix=".ip-process-pages-")


def fetch_result_records(coords: Mapping[str, str], args: argparse.Namespace, *, services) -> list[dict[str, Any]]:
    """Read the complete, already-aggregated result-data view."""

    return services._fetch_view_records(coords, args, RESULT_FIELDS, temp_prefix=".ip-result-pages-")


def fetch_text_records(coords: Mapping[str, str], args: argparse.Namespace, *, services) -> list[dict[str, Any]]:
    """Read the complete ``推送文字`` view with only message fields."""

    return services._fetch_view_records(coords, args, TEXT_FIELDS, temp_prefix=".ip-text-pages-")


def _read_channel_configs(args: argparse.Namespace, *, services) -> tuple[dict[str, str], list[dict[str, Any]]]:
    coords = services.resolve_coordinates(args)
    records = services._fetch_view_records(coords, args, lead_report.CONFIG_FIELDS, temp_prefix=".channel-config-")
    return coords, records


def list_channels(args: argparse.Namespace, *, services) -> int:
    _coords, records = services._read_channel_configs(args)
    channels: dict[str, dict[str, Any]] = {}
    for row in records:
        channel = lead_report.text(lead_report.value(row, "渠道"))
        item = channels.setdefault(channel, {"channel": channel, "periods": set(), "sections": set(), "configured_group_count": 0})
        item["periods"].add(lead_report.text(lead_report.value(row, "推送期次")))
        item["sections"].add(lead_report.text(lead_report.value(row, "推送类型")))
        item["configured_group_count"] = max(item["configured_group_count"], len(lead_report.value(row, "接收群") or []))
    for channel in sorted(channels):
        item = channels[channel]
        item["periods"] = sorted(item["periods"])
        item["sections"] = sorted(item["sections"])
        print(json.dumps(item, ensure_ascii=False))
    print("以上是配置表中的渠道；新增渠道也可用 --channel 精确选择。此命令不发送消息。")
    return 0
