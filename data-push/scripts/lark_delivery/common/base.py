"""Read-only Base coordinates and complete version-consistent pagination."""
from __future__ import annotations
import argparse
import json
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import parse_qs, urlparse
from .runtime import run_lark
from .values import _json_payload, _unwrap, _find_first, _string


def resolve_coordinates(args: argparse.Namespace, *, runner=None) -> dict[str, str]:
    base_token = (args.base_token or "").strip()
    table_id = (args.table_id or "").strip()
    view_id = (args.view_id or "").strip()
    source_url = (args.source_url or "").strip()
    resolved: Any = None
    if source_url and (not base_token or not table_id or not view_id):
        resolved = _unwrap(
            _json_payload(
                (runner or run_lark)(
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
        base_token = base_token or _string(_find_first(resolved, ("base_token", "baseToken")))
        table_id = table_id or _string(_find_first(resolved, ("table_id", "tableId")))
        view_id = view_id or _string(_find_first(resolved, ("view_id", "viewId")))

        query = parse_qs(urlparse(source_url).query)
        table_id = table_id or (query.get("table", [""])[0] or "")
        view_id = view_id or (query.get("view", [""])[0] or "")

    if not base_token or not table_id or not view_id:
        raise SystemExit(
            "数据源坐标不完整：请设置 BASE_TOKEN、TABLE_ID、VIEW_ID，"
            "或提供 --source-url 让 lark-cli base +url-resolve 解析"
        )
    return {
        "base_token": base_token,
        "table_id": table_id,
        "view_id": view_id,
        "source_url": source_url,
    }


def _fetch_view_records(
    coords: Mapping[str, str],
    args: argparse.Namespace,
    fields: Sequence[str],
    *,
    temp_prefix: str,
    filter_json: Mapping[str, Any] | None = None,
    audit: dict[str, Any] | None = None,
    runner=None,
) -> list[dict[str, Any]]:
    """Read a complete selected view with a minimum field projection."""

    records: list[dict[str, Any]] = []
    offset = 0
    page_no = 0
    first_rev = None
    first_context = None
    seen_record_ids: set[str] = set()
    with tempfile.TemporaryDirectory(prefix=temp_prefix) as temp_dir:
        page_dir = Path(temp_dir)
        while True:
            page_no += 1
            page_file = page_dir / ("page-%d.ndjson" % page_no)
            command: list[str] = [
                "base",
                "+record-list",
                "--base-token",
                coords["base_token"],
                "--table-id",
                coords["table_id"],
                "--limit",
                "2000",
                "--offset",
                str(offset),
                "--format",
                "ndjson",
                "--output",
                "./%s" % page_file.name,
                "--overwrite",
                "--as",
                args.base_as,
            ]
            if coords.get("view_id"):
                command[6:6] = ["--view-id", coords["view_id"]]
            if filter_json is not None:
                filter_path = page_dir / "filter.json"
                filter_path.write_text(json.dumps(filter_json, ensure_ascii=True), encoding="utf-8")
                command.extend(("--filter-json", "@./filter.json"))
            for field in fields:
                command.extend(("--field-id", field))
            manifest = _unwrap(_json_payload((runner or run_lark)(command, cwd=str(page_dir), timeout=args.timeout)))
            if not page_file.exists():
                raise RuntimeError("record-list 没有生成 NDJSON 文件: %s" % page_file)
            page_rows = [
                _json_payload(line)
                for line in page_file.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            if not isinstance(manifest, Mapping) or not isinstance(manifest.get("has_more"), bool):
                raise RuntimeError("读取清单缺少 has_more，无法确认查询完整性")
            count = manifest.get("records_count")
            if count != len(page_rows):
                raise RuntimeError("读取清单与实际行数不一致")
            rev, query_context = manifest.get("rev"), manifest.get("query_context")
            if page_no == 1:
                first_rev, first_context = rev, query_context
            elif rev != first_rev or query_context != first_context:
                raise RuntimeError("分页期间数据版本或查询范围改变，请重新读取")
            for row in page_rows:
                record_id = row.get("record_id") if isinstance(row, dict) else None
                if not record_id or record_id in seen_record_ids:
                    raise RuntimeError("分页记录 ID 缺失或重复，无法确认完整性")
                seen_record_ids.add(record_id)
            records.extend(page_rows)
            has_more = manifest["has_more"]
            if not has_more:
                break
            if count <= 0:
                raise RuntimeError("record-list 返回 has_more=true 但本页没有记录，停止避免死循环")
            if first_rev is None:
                raise RuntimeError("分页清单缺少 rev，无法确认同一数据快照")
            next_offset = manifest.get("next_offset")
            if not isinstance(next_offset, int) or next_offset <= offset:
                raise RuntimeError("分页清单没有有效 next_offset")
            offset = next_offset
            if page_no >= args.max_pages:
                raise RuntimeError("record-list 超过 --max-pages=%d，未完成分页" % args.max_pages)
    if audit is not None:
        audit.update({"records_count": len(records), "pages": page_no, "rev": first_rev,
                      "has_more": False, "table_id": coords["table_id"], "view_id": coords.get("view_id", "")})
    return records
