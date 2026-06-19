"""Template Query discovery and SQL-detail API client."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from _shared.auth import fill_login_if_present
from _shared.config import TEMPLATE_QUERY_API_BASE, TEMPLATE_QUERY_MY_CREATE_URL
from _shared.errors import UsageError


STATUS_LABELS = {
    1: "unpublished",
    2: "published",
    3: "offline",
}

STATUS_VALUES = {
    "unpublished": 1,
    "published": 2,
    "offline": 3,
    "1": 1,
    "2": 2,
    "3": 3,
}


@dataclass(frozen=True)
class TemplateQuery:
    """One template-query row from the user's created-template list."""

    id: int
    name: str
    description: str
    owner: str
    status: int | None
    is_del: int | None
    publish_time: str
    create_time: str
    update_time: str
    creator: str
    updater: str
    sql_detail: str
    raw_payload: dict[str, Any]

    @property
    def status_label(self) -> str:
        if self.status is None:
            return ""
        return STATUS_LABELS.get(self.status, str(self.status))

    def to_summary_json(self, *, sql_path: Path | None = None) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "owner": self.owner,
            "status": self.status,
            "statusLabel": self.status_label,
            "isDel": self.is_del,
            "publishTime": self.publish_time,
            "createTime": self.create_time,
            "updateTime": self.update_time,
            "creator": self.creator,
            "updater": self.updater,
            "sqlBytes": len(self.sql_detail.encode("utf-8")),
            "sqlLines": len(self.sql_detail.splitlines()),
            "sqlPath": str(sql_path) if sql_path else None,
        }


class TemplateQueryClient:
    """Authenticated browser-backed client for Template Query APIs."""

    def __init__(self, page: Any, state_path: Path):
        self.page = page
        self.context = page.context
        self.state_path = state_path

    def ensure_authenticated(self, username: str | None, password: str | None) -> None:
        self.page.goto(TEMPLATE_QUERY_MY_CREATE_URL, wait_until="domcontentloaded", timeout=45_000)
        self.page.wait_for_timeout(1500)
        if _is_login_url(self.page.url):
            fill_login_if_present(self.page, username, password)
            self.page.wait_for_load_state("domcontentloaded", timeout=45_000)
            self.page.wait_for_timeout(3000)
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            self.context.storage_state(path=str(self.state_path))
            self.page.goto(TEMPLATE_QUERY_MY_CREATE_URL, wait_until="domcontentloaded", timeout=45_000)
            self.page.wait_for_timeout(1500)
        if _is_login_url(self.page.url):
            raise UsageError("Template Query login failed or requires manual verification.")

    def post_json(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{TEMPLATE_QUERY_API_BASE}/{endpoint}"
        response = self.page.request.post(
            url,
            data=json.dumps(payload, ensure_ascii=False),
            headers={"Content-Type": "application/json;charset=UTF-8"},
            timeout=45_000,
        )
        if not response.ok:
            raise UsageError(f"Template Query API failed: {endpoint} HTTP {response.status}")
        data = response.json()
        if not isinstance(data, dict) or data.get("status") not in (None, "success"):
            error = data.get("error") if isinstance(data, dict) else data
            raise UsageError(f"Template Query API returned an error for {endpoint}: {error}")
        return data

    def fetch_created_templates(
        self,
        *,
        name: str | None = None,
        status: int | None = None,
        page_size: int = 100,
        max_pages: int = 20,
    ) -> list[TemplateQuery]:
        templates: list[TemplateQuery] = []
        for page_no in range(1, max_pages + 1):
            payload: dict[str, Any] = {"pager": {"pageSize": page_size, "pageNo": page_no}}
            if name:
                payload["name"] = name
            if status is not None:
                payload["status"] = status
            data = self.post_json("template/createList", payload)
            rows = data.get("data") or []
            if not isinstance(rows, list):
                raise UsageError("Template Query createList returned non-list data.")
            templates.extend(parse_template_rows(rows))
            if len(rows) < page_size:
                break
        return templates

    def find_template(
        self,
        *,
        name: str,
        match: str = "exact",
        status: int | None = None,
        page_size: int = 100,
        max_pages: int = 20,
    ) -> tuple[TemplateQuery, list[TemplateQuery]]:
        api_name = name if match == "exact" else None
        candidates = self.fetch_created_templates(
            name=api_name,
            status=status,
            page_size=page_size,
            max_pages=max_pages,
        )
        if match == "exact":
            matches = [template for template in candidates if template.name == name]
        elif match == "contains":
            matches = [template for template in candidates if name in template.name]
        else:
            raise UsageError(f"Unsupported template match mode: {match}")
        if not matches:
            raise UsageError(f"Template Query template was not found: {name}")
        selected = sorted(matches, key=lambda item: (item.update_time, item.id), reverse=True)[0]
        if not selected.sql_detail.strip():
            raise UsageError(f"Template Query template has empty SQL detail: {selected.name} ({selected.id})")
        return selected, matches


def parse_template_rows(rows: Iterable[dict[str, Any]]) -> list[TemplateQuery]:
    return [parse_template_row(row) for row in rows if isinstance(row, dict)]


def parse_template_row(row: dict[str, Any]) -> TemplateQuery:
    return TemplateQuery(
        id=_int_value(row.get("id")) or 0,
        name=_text(row.get("name")),
        description=_text(row.get("description")),
        owner=_text(row.get("owner")),
        status=_int_value(row.get("status")),
        is_del=_int_value(row.get("isDel")),
        publish_time=_text(row.get("publishTime")),
        create_time=_text(row.get("createTime")),
        update_time=_text(row.get("updateTime")),
        creator=_text(row.get("creator")),
        updater=_text(row.get("updater")),
        sql_detail=_text(row.get("sqlDetail")),
        raw_payload=row,
    )


def parse_status(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    normalized = value.strip().lower()
    if normalized not in STATUS_VALUES:
        raise UsageError(f"Unsupported template status: {value}")
    return STATUS_VALUES[normalized]


def write_template_sql(path: Path, sql: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(sql.rstrip() + "\n", encoding="utf-8", newline="\n")


def _is_login_url(url: str) -> bool:
    return "cas.baijia.com" in url or "login" in url.lower()


def _text(value: Any) -> str:
    return str(value or "").strip()


def _int_value(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
