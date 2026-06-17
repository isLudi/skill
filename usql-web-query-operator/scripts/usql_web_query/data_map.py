"""Data Map API client used for table schema enrichment."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from _shared.auth import fill_login_if_present
from _shared.config import DATAMAP_API_BASE, DATAMAP_URL
from _shared.errors import UsageError


PARTITION_DESCRIPTIONS = {
    "dt": "\u5929\u7ea7\u522b\u5206\u533a yyyyMMdd",
    "hour": "\u5c0f\u65f6\u7ea7\u5206\u533a HH",
}


@dataclass
class DataMapColumn:
    name: str
    type: str = ""
    description: str = ""
    is_partition: bool = False

    @classmethod
    def from_payload(cls, payload: dict[str, Any], *, is_partition: bool) -> "DataMapColumn | None":
        name = str(payload.get("name") or payload.get("fieldName") or "").strip()
        if not name:
            return None
        description = clean_description(payload.get("description") or payload.get("comment") or "")
        if is_partition and not description:
            description = PARTITION_DESCRIPTIONS.get(name, "\u5206\u533a\u5b57\u6bb5")
        return cls(
            name=name,
            type=str(payload.get("type") or payload.get("dataType") or "").strip(),
            description=description,
            is_partition=is_partition,
        )

    def to_json(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "isPartition": self.is_partition,
        }


def clean_description(value: Any) -> str:
    text = str(value or "").replace("\r", " ").replace("\n", " ").strip()
    text = re.sub(r"&001&1&001&1&001&", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_ddl_types(ddl: str) -> dict[str, str]:
    types: dict[str, str] = {}
    for line in ddl.splitlines():
        match = re.match(r"\s*`([^`]+)`\s+([^\s,]+(?:\([^)]*\))?)", line)
        if match:
            types[match.group(1)] = match.group(2)
    return types


def iter_cached_columns(table_info: dict[str, Any]) -> list[DataMapColumn]:
    columns: list[DataMapColumn] = []
    seen: set[str] = set()
    for key, is_partition in (("partitionColumns", True), ("normalColumns", False)):
        for raw in table_info.get(key) or []:
            column = DataMapColumn.from_payload(raw, is_partition=is_partition)
            if not column or column.name in seen:
                continue
            seen.add(column.name)
            columns.append(column)
    return columns


def _extract_rows_and_total(payload: Any) -> tuple[list[dict[str, Any]], int | None]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)], None
    if not isinstance(payload, dict):
        return [], None
    rows: Any = None
    for key in ("list", "records", "rows", "data", "columns", "result"):
        candidate = payload.get(key)
        if isinstance(candidate, list):
            rows = candidate
            break
        if isinstance(candidate, dict):
            nested_rows, _ = _extract_rows_and_total(candidate)
            if nested_rows:
                rows = nested_rows
                break
    if rows is None:
        rows = []
    total = payload.get("total") or payload.get("totalCount") or payload.get("count")
    return [row for row in rows if isinstance(row, dict)], int(total) if str(total or "").isdigit() else None


class DataMapClient:
    """Authenticated browser-backed client for Data Map table APIs."""

    def __init__(self, page: Any, state_path: Path):
        self.page = page
        self.context = page.context
        self.state_path = state_path

    def ensure_authenticated(self, username: str | None, password: str | None) -> None:
        self.page.goto(DATAMAP_URL, wait_until="domcontentloaded", timeout=45_000)
        self.page.wait_for_timeout(1500)
        if "cas.baijia.com" in self.page.url or "login" in self.page.url.lower():
            fill_login_if_present(self.page, username, password)
            self.page.wait_for_load_state("domcontentloaded", timeout=45_000)
            self.page.wait_for_timeout(3000)
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            self.context.storage_state(path=str(self.state_path))
        if "cas.baijia.com" in self.page.url or "login" in self.page.url.lower():
            raise UsageError("Data Map login failed or requires manual verification.")

    def post_json(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{DATAMAP_API_BASE}/{endpoint}"
        response = self.page.request.post(
            url,
            data=json.dumps(payload, ensure_ascii=False),
            headers={"Content-Type": "application/json;charset=UTF-8"},
            timeout=45_000,
        )
        if not response.ok:
            raise UsageError(f"Data Map API failed: {endpoint} HTTP {response.status}")
        data = response.json()
        if not isinstance(data, dict) or data.get("status") not in (None, "success"):
            raise UsageError(f"Data Map API returned an unexpected payload: {endpoint}")
        return data

    def search_table(self, table_name: str) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        queries = [table_name]
        short_name = table_name.rsplit(".", 1)[-1]
        if short_name != table_name:
            queries.append(short_name)

        attempts: list[dict[str, Any]] = []
        for query in queries:
            payload = {"topicIds": [], "searchContent": query, "pageNo": 1, "pageSize": 10}
            result = self.post_json("searchTableList", payload)
            rows, _ = _extract_rows_and_total(result.get("data"))
            selected = _select_table_row(table_name, rows)
            attempts.append({"query": query, "rows": rows[:10], "raw_status": result.get("status")})
            if selected:
                return selected, {"attempts": attempts}
        return None, {"attempts": attempts}

    def fetch_table(self, table_name: str) -> dict[str, Any]:
        selected, search_summary = self.search_table(table_name)
        if not selected:
            return {"found": False, "search": search_summary}
        table_id = selected.get("id") or selected.get("tableId")
        if not table_id:
            return {"found": False, "selected": selected, "search": search_summary, "error": "missing_table_id"}

        table_info = self.post_json("getTableInfo", {"tableId": table_id}).get("data") or {}
        normal_columns = self._fetch_columns("normalColumns", int(table_id), is_partition=False)
        partition_columns = self._fetch_columns("partitionColumns", int(table_id), is_partition=True)
        ddl = self._fetch_ddl(int(table_id))
        _enrich_blank_types_from_ddl(normal_columns, partition_columns, ddl)

        return {
            "found": True,
            "tableId": table_id,
            "selected": selected,
            "tableInfo": table_info,
            "normalColumns": [column.to_json() for column in normal_columns],
            "normalTotal": len(normal_columns),
            "partitionColumns": [column.to_json() for column in partition_columns],
            "ddl": ddl,
            "search": search_summary,
        }

    def _fetch_columns(self, endpoint: str, table_id: int, *, is_partition: bool) -> list[DataMapColumn]:
        columns: list[DataMapColumn] = []
        seen: set[str] = set()
        page_no = 1
        page_size = 500
        while True:
            payload = {"tableId": table_id, "pageNo": page_no, "pageSize": page_size}
            result = self.post_json(endpoint, payload)
            rows, total = _extract_rows_and_total(result.get("data"))
            for row in rows:
                column = DataMapColumn.from_payload(row, is_partition=is_partition)
                if column and column.name not in seen:
                    seen.add(column.name)
                    columns.append(column)
            if not rows or total is None or len(columns) >= total:
                break
            page_no += 1
            if page_no > 20:
                raise UsageError(f"Data Map {endpoint} pagination exceeded safety limit for tableId={table_id}.")
        return columns

    def _fetch_ddl(self, table_id: int) -> str:
        result = self.post_json("getDdl", {"tableId": table_id})
        data = result.get("data")
        return data if isinstance(data, str) else ""


def _select_table_row(table_name: str, rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    for row in rows:
        names = {
            str(row.get("name") or "").strip(),
            str(row.get("tableName") or "").strip(),
        }
        db = str(row.get("db") or row.get("dbName") or "").strip()
        short_name = str(row.get("name") or row.get("tableName") or "").strip()
        if db and short_name and "." not in short_name:
            names.add(f"{db}.{short_name}")
        if table_name in names:
            return row
    return rows[0] if rows else None


def _enrich_blank_types_from_ddl(
    normal_columns: list[DataMapColumn],
    partition_columns: list[DataMapColumn],
    ddl: str,
) -> None:
    ddl_types = parse_ddl_types(ddl)
    if not ddl_types:
        return
    for column in [*partition_columns, *normal_columns]:
        if not column.type and column.name in ddl_types:
            column.type = ddl_types[column.name]
