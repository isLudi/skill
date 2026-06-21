"""Template Query lifecycle and query-execution API client."""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qs, unquote, urlparse

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

QUERY_STATUS_LABELS = {
    1: "pending",
    2: "running",
    3: "success",
    4: "failed",
    5: "cancelled",
}

QUERY_TYPE_LABELS = {
    1: "instant",
}

DOWNLOAD_TYPE_VALUES = {
    "csv": 1,
    "xls": 2,
    "xlsx": 2,
    "1": 1,
    "2": 2,
}

RUNNING_QUERY_STATUSES = {1, 2}


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


@dataclass(frozen=True)
class TemplateQueryExecution:
    """One executed query row from Template Query > My Query."""

    id: int
    name: str
    template_name: str
    type: int | None
    status: int | None
    count: int | None
    initiation_time: str
    execution_time: int | None
    copy_status: bool | None
    task_id: int | None
    raw_payload: dict[str, Any]

    @property
    def status_label(self) -> str:
        if self.status is None:
            return ""
        return QUERY_STATUS_LABELS.get(self.status, str(self.status))

    @property
    def type_label(self) -> str:
        if self.type is None:
            return ""
        return QUERY_TYPE_LABELS.get(self.type, str(self.type))

    def to_summary_json(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "templateName": self.template_name,
            "type": self.type,
            "typeLabel": self.type_label,
            "status": self.status,
            "statusLabel": self.status_label,
            "count": self.count,
            "initiationTime": self.initiation_time,
            "executionTime": self.execution_time,
            "copyStatus": self.copy_status,
            "taskId": self.task_id,
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

    def post_json(self, endpoint: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{TEMPLATE_QUERY_API_BASE}/{endpoint}"
        request_kwargs: dict[str, Any] = {"timeout": 45_000}
        if payload is not None:
            request_kwargs["data"] = json.dumps(payload, ensure_ascii=False)
            request_kwargs["headers"] = {"Content-Type": "application/json;charset=UTF-8"}
        response = self.page.request.post(url, **request_kwargs)
        if not response.ok:
            raise UsageError(f"Template Query API failed: {endpoint} HTTP {response.status}")
        data = response.json()
        if not isinstance(data, dict) or data.get("status") not in (None, "success"):
            error = data.get("error") if isinstance(data, dict) else data
            raise UsageError(f"Template Query API returned an error for {endpoint}: {error}")
        return data

    def get_json(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{TEMPLATE_QUERY_API_BASE}/{endpoint}"
        response = self.page.request.get(url, params=params, timeout=45_000)
        if not response.ok:
            raise UsageError(f"Template Query API failed: {endpoint} HTTP {response.status}")
        data = response.json()
        if not isinstance(data, dict) or data.get("status") not in (None, "success"):
            error = data.get("error") if isinstance(data, dict) else data
            raise UsageError(f"Template Query API returned an error for {endpoint}: {error}")
        return data

    def fetch_auth_profile(self) -> dict[str, Any]:
        data = self.post_json("api/cas/getAuth").get("data") or {}
        if not isinstance(data, dict):
            raise UsageError("Template Query auth profile returned non-dict data.")
        return data

    def parse_sql(self, sql: str) -> dict[str, Any]:
        payload = {
            "value": sql,
            "sqlParserVO": {
                "templateVariable": [],
                "templateParam": [],
                "tableName": [],
            },
        }
        data = self.post_json("template/sqlParser", payload).get("data") or {}
        if not isinstance(data, dict):
            raise UsageError("Template Query sqlParser returned non-dict data.")
        return data

    def save_template(
        self,
        *,
        name: str,
        description: str,
        sql: str,
        creator: str,
        owner: str = "",
        max_lookup_attempts: int = 5,
    ) -> TemplateQuery:
        parsed = self.parse_sql(sql)
        payload = {
            "id": None,
            "name": name,
            "description": description,
            "sqlDetail": sql,
            "templateVariable": normalize_template_variables(parsed.get("templateVariable")),
            "templateParam": normalize_template_params(parsed.get("templateParam")),
            "creator": creator,
            "owner": owner,
        }
        self.post_json("template/saveAndUpdate", payload)
        last_error: UsageError | None = None
        for attempt in range(max_lookup_attempts):
            try:
                saved, _ = self.find_template(name=name, match="exact", page_size=20, max_pages=5)
                return saved
            except UsageError as exc:
                last_error = exc
                if attempt + 1 >= max_lookup_attempts:
                    break
                time.sleep(1)
        raise UsageError(f"Template Query template was saved but could not be reloaded: {name}") from last_error

    def publish_template(self, template_id: int) -> None:
        self.post_json("template/publish", {"id": template_id})

    def offline_template(self, template_id: int) -> None:
        self.post_json("template/offline", {"id": template_id})

    def delete_template(self, template_id: int) -> None:
        self.post_json("template/delete", {"id": template_id})

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

    def fetch_query_detail(self, *, template_id: int, query_type: int = 1) -> dict[str, Any]:
        data = self.post_json("query/detail", {"id": template_id, "type": query_type}).get("data") or {}
        if not isinstance(data, dict):
            raise UsageError("Template Query query/detail returned non-dict data.")
        return data

    def create_query(
        self,
        *,
        query_name: str,
        template_id: int,
        query_type: int,
        required_conditions: list[dict[str, Any]],
        partition_conditions: list[dict[str, Any]],
        query_column: list[dict[str, Any]],
        query_conditions: list[dict[str, Any]],
    ) -> int:
        payload = {
            "queryName": query_name,
            "templateId": template_id,
            "queryType": query_type,
            "requiredConditions": required_conditions,
            "partitionConditions": partition_conditions,
            "queryColumn": query_column,
            "queryConditions": query_conditions,
        }
        query_id = self.post_json("query/create", payload).get("data")
        query_id_value = _int_value(query_id)
        if query_id_value is None:
            raise UsageError("Template Query query/create did not return a valid query id.")
        return query_id_value

    def fetch_queries(
        self,
        *,
        name: str | None = None,
        template_name: str | None = None,
        status: int | None = None,
        page_size: int = 20,
        max_pages: int = 5,
    ) -> list[TemplateQueryExecution]:
        queries: list[TemplateQueryExecution] = []
        for page_no in range(1, max_pages + 1):
            payload: dict[str, Any] = {"pager": {"pageSize": page_size, "pageNo": page_no}}
            if name:
                payload["name"] = name
            if template_name:
                payload["templateName"] = template_name
            if status is not None:
                payload["status"] = status
            data = self.post_json("query/list", payload)
            rows = data.get("data") or []
            if not isinstance(rows, list):
                raise UsageError("Template Query query/list returned non-list data.")
            queries.extend(parse_query_rows(rows))
            if len(rows) < page_size:
                break
        return queries

    def find_query(
        self,
        *,
        query_id: int,
        page_size: int = 20,
        max_pages: int = 5,
    ) -> TemplateQueryExecution:
        candidates = self.fetch_queries(page_size=page_size, max_pages=max_pages)
        matches = [query for query in candidates if query.id == query_id]
        if not matches:
            raise UsageError(f"Template Query query was not found: {query_id}")
        return matches[0]

    def wait_for_query_completion(
        self,
        *,
        query_id: int,
        timeout_ms: int,
        poll_interval_ms: int = 2000,
        page_size: int = 20,
        max_pages: int = 5,
    ) -> TemplateQueryExecution:
        deadline = time.monotonic() + max(timeout_ms, 0) / 1000
        last_seen: TemplateQueryExecution | None = None
        while time.monotonic() < deadline:
            try:
                current = self.find_query(query_id=query_id, page_size=page_size, max_pages=max_pages)
            except UsageError:
                self.page.wait_for_timeout(poll_interval_ms)
                continue
            last_seen = current
            if current.status not in RUNNING_QUERY_STATUSES:
                return current
            self.page.wait_for_timeout(poll_interval_ms)
        if last_seen is not None:
            return last_seen
        raise UsageError(f"Timed out waiting for Template Query query {query_id} to appear.")

    def fetch_query_log(self, query_id: int) -> dict[str, Any]:
        data = self.get_json("query/log", {"queryId": query_id}).get("data") or {}
        if not isinstance(data, dict):
            raise UsageError("Template Query query/log returned non-dict data.")
        return data

    def fetch_query_result(self, query_id: int) -> dict[str, Any]:
        data = self.post_json("query/result", {"id": query_id}).get("data") or {}
        if not isinstance(data, dict):
            raise UsageError("Template Query query/result returned non-dict data.")
        return data

    def fetch_query_download_url(self, query_id: int, download_type: int) -> str:
        data = self.get_json("query/download", {"queryId": query_id, "type": download_type}).get("data")
        url = _text(data)
        if not url:
            raise UsageError(f"Template Query query/download returned an empty URL for query {query_id}.")
        return url

    def download_query_result(
        self,
        *,
        query_id: int,
        download_type: int,
        artifacts_dir: Path,
        output_file: Path | None = None,
    ) -> Path:
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        signed_url = self.fetch_query_download_url(query_id, download_type)
        response = self.page.request.get(signed_url, timeout=120_000)
        content = response.body()
        if not response.ok or not content:
            raise UsageError(f"Template Query signed download failed for query {query_id}.")

        fallback_name = f"template_query_{query_id}{download_suffix(download_type)}"
        filename = _filename_from_disposition(response.headers.get("content-disposition"), fallback_name)
        if filename == fallback_name:
            filename = _filename_from_signed_url(signed_url, fallback_name)

        target = output_file or (artifacts_dir / filename)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return target


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


def parse_download_type(value: str | int | None) -> int:
    if value is None:
        return DOWNLOAD_TYPE_VALUES["csv"]
    normalized = str(value).strip().lower()
    if normalized not in DOWNLOAD_TYPE_VALUES:
        raise UsageError(f"Unsupported download format: {value}")
    return DOWNLOAD_TYPE_VALUES[normalized]


def download_suffix(download_type: int) -> str:
    return ".csv" if download_type == 1 else ".xlsx"


def normalize_template_variables(rows: Any) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        item = dict(row)
        item["category"] = 1
        normalized.append(item)
    return normalized


def normalize_template_params(rows: Any) -> list[dict[str, Any]]:
    return [dict(row) for row in rows or [] if isinstance(row, dict)]


def parse_query_rows(rows: Iterable[dict[str, Any]]) -> list[TemplateQueryExecution]:
    return [parse_query_row(row) for row in rows if isinstance(row, dict)]


def parse_query_row(row: dict[str, Any]) -> TemplateQueryExecution:
    return TemplateQueryExecution(
        id=_int_value(row.get("id")) or 0,
        name=_text(row.get("name")),
        template_name=_text(row.get("templateName")),
        type=_int_value(row.get("type")),
        status=_int_value(row.get("status")),
        count=_int_value(row.get("count")),
        initiation_time=_text(row.get("initiationTime")),
        execution_time=_int_value(row.get("executionTime")),
        copy_status=_bool_value(row.get("copyStatus")),
        task_id=_int_value(row.get("taskId")),
        raw_payload=row,
    )


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


def _bool_value(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1"}:
            return True
        if normalized in {"false", "0"}:
            return False
    if isinstance(value, (int, float)):
        return bool(value)
    return None


def _filename_from_disposition(value: str | None, fallback: str) -> str:
    if not value:
        return fallback
    match = re.search(r"filename\*=UTF-8''([^;]+)|filename=\"?([^\";]+)", value)
    if not match:
        return fallback
    filename = match.group(1) or match.group(2) or fallback
    filename = re.sub(r'[<>:"/\\|?*]+', "_", filename).strip()
    return filename or fallback


def _filename_from_signed_url(url: str, fallback: str) -> str:
    try:
        query = parse_qs(urlparse(url).query)
        dispositions = query.get("response-content-disposition") or []
        if dispositions:
            return _filename_from_disposition(unquote(dispositions[0]), fallback)
    except Exception:
        return fallback
    return fallback
