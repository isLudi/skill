"""Data Center dataset discovery and SQL-detail API client."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from _shared.auth import fill_login_if_present
from _shared.config import DATA_CENTER_API_BASE, DATA_CENTER_DATASET_URL
from _shared.errors import UsageError


DATASET_MENU_TYPE = "DATA_SET"
DATASET_SQL_FILE_TYPE = "DATA_SET_SQL"
DEFAULT_MARKET_START_DATASET = "(内部渠道)外呼过程数据"


@dataclass(frozen=True)
class DataCenterDataset:
    """A SQL dataset node from the Data Center menu tree."""

    id: str
    key: str
    name: str
    file_value: str
    subject_id: str
    parent_id: str
    owner: str
    create_time: str
    path: tuple[str, ...]

    @property
    def path_text(self) -> str:
        return "/".join(self.path)

    @property
    def parent_path(self) -> tuple[str, ...]:
        return self.path[:-1]

    def to_json(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "key": self.key,
            "name": self.name,
            "fileValue": self.file_value,
            "subjectId": self.subject_id,
            "parentId": self.parent_id,
            "owner": self.owner,
            "createTime": self.create_time,
            "path": self.path_text,
        }


@dataclass(frozen=True)
class DataCenterDatasetSql:
    """Full source SQL and detail metadata for one Data Center dataset."""

    dataset: DataCenterDataset
    execute_sql: str
    data_source_id: str
    open_external: str
    detail_payload: dict[str, Any]

    def to_summary_json(self) -> dict[str, Any]:
        data = self.dataset.to_json()
        data.update(
            {
                "dataSourceId": self.data_source_id,
                "openExternal": self.open_external,
                "sqlBytes": len(self.execute_sql.encode("utf-8")),
                "sqlLines": len(self.execute_sql.splitlines()),
            }
        )
        return data


@dataclass(frozen=True)
class DataCenterScheduleRun:
    """One execution record from a dataset synchronization schedule."""

    id: str
    start_time: str
    end_time: str
    elapsed_seconds: int | None
    status: str

    def to_json(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "startTime": self.start_time,
            "endTime": self.end_time,
            "elapsedSeconds": self.elapsed_seconds,
            "status": self.status,
        }


class DataCenterClient:
    """Authenticated browser-backed client for Data Center dataset APIs."""

    def __init__(self, page: Any, state_path: Path):
        self.page = page
        self.context = page.context
        self.state_path = state_path

    def ensure_authenticated(self, username: str | None, password: str | None) -> None:
        self.page.goto(DATA_CENTER_DATASET_URL, wait_until="domcontentloaded", timeout=45_000)
        self.page.wait_for_timeout(1500)
        if _is_login_url(self.page.url):
            fill_login_if_present(self.page, username, password)
            self.page.wait_for_load_state("domcontentloaded", timeout=45_000)
            self.page.wait_for_timeout(3000)
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            self.context.storage_state(path=str(self.state_path))
        if _is_login_url(self.page.url):
            raise UsageError("Data Center login failed or requires manual verification.")

    def post_json(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{DATA_CENTER_API_BASE}/{endpoint}"
        response = self.page.request.post(
            url,
            data=json.dumps(payload, ensure_ascii=False),
            headers={"Content-Type": "application/json;charset=UTF-8"},
            timeout=45_000,
        )
        if not response.ok:
            raise UsageError(f"Data Center API failed: {endpoint} HTTP {response.status}")
        data = response.json()
        if not isinstance(data, dict) or data.get("status") not in (None, "success"):
            error = data.get("error") if isinstance(data, dict) else data
            raise UsageError(f"Data Center API returned an error for {endpoint}: {error}")
        return data

    def fetch_menu(self) -> dict[str, Any]:
        return self.post_json("menu/manage", {"menuType": DATASET_MENU_TYPE})

    def discover_datasets(self) -> list[DataCenterDataset]:
        menu = self.fetch_menu()
        return list(iter_sql_datasets(menu))

    def fetch_dataset_sql(self, dataset: DataCenterDataset) -> DataCenterDatasetSql:
        payload = self.post_json("set/detail", {"id": dataset.id})
        detail = payload.get("data") or {}
        if not isinstance(detail, dict):
            raise UsageError(f"Data Center dataset detail is not an object: {dataset.name}")
        execute_sql = str(detail.get("executeSql") or "").strip()
        if not execute_sql:
            raise UsageError(f"Data Center dataset has empty source SQL: {dataset.name} ({dataset.id})")
        return DataCenterDatasetSql(
            dataset=dataset,
            execute_sql=execute_sql,
            data_source_id=str(detail.get("dataSourceId") or ""),
            open_external=str(detail.get("openExternal") or ""),
            detail_payload=detail,
        )

    def fetch_schedule_runs(
        self,
        schedule_task_id: str,
        *,
        page_no: int = 1,
        page_size: int = 10,
    ) -> list[DataCenterScheduleRun]:
        """Read synchronization history without triggering a run."""

        if not schedule_task_id.strip():
            raise UsageError("Data Center schedule taskId is empty.")
        payload = self.post_json(
            "set/schedules/list",
            {
                "taskId": schedule_task_id,
                "pageNo": page_no,
                "pageSize": page_size,
            },
        )
        rows = payload.get("data") or []
        if not isinstance(rows, list):
            raise UsageError("Data Center schedule history is not a list.")
        runs: list[DataCenterScheduleRun] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            elapsed = row.get("elapsed")
            try:
                elapsed_seconds = int(elapsed) if elapsed is not None else None
            except (TypeError, ValueError):
                elapsed_seconds = None
            runs.append(
                DataCenterScheduleRun(
                    id=_clean_text(row.get("id")),
                    start_time=_clean_text(row.get("startTime")),
                    end_time=_clean_text(row.get("endTime")),
                    elapsed_seconds=elapsed_seconds,
                    status=_clean_text(row.get("status")).upper(),
                )
            )
        return runs


def iter_sql_datasets(menu_payload: dict[str, Any]) -> Iterable[DataCenterDataset]:
    """Yield SQL dataset file nodes from a Data Center menu/manage payload."""

    seen: set[str] = set()
    for root in _menu_roots(menu_payload):
        for dataset in _walk_menu_node(root, ()):
            if dataset.id in seen:
                continue
            seen.add(dataset.id)
            yield dataset


def select_qingcheng_datasets(datasets: Iterable[DataCenterDataset]) -> list[DataCenterDataset]:
    """Select all Qingcheng project datasets under 市场顾问部/青橙项目部."""

    selected = [
        dataset
        for dataset in datasets
        if _parent_endswith(dataset, ("市场顾问部", "青橙项目部"))
    ]
    if not selected:
        raise UsageError("No Qingcheng Data Center datasets were found under 市场顾问部/青橙项目部.")
    return selected


def select_market_datasets(
    datasets: Iterable[DataCenterDataset],
    *,
    start_name: str = DEFAULT_MARKET_START_DATASET,
) -> list[DataCenterDataset]:
    """Select market-consultant datasets from the configured start node to the end."""

    candidates = [
        dataset
        for dataset in datasets
        if _parent_endswith(dataset, ("市场顾问部", "市场顾问部"))
    ]
    for index, dataset in enumerate(candidates):
        if dataset.name == start_name:
            return candidates[index:]
    raise UsageError(f"Market Data Center start dataset was not found: {start_name}")


def filter_datasets_by_name(
    datasets: Iterable[DataCenterDataset],
    requested_names: list[str] | None,
) -> list[DataCenterDataset]:
    selected = list(datasets)
    if not requested_names:
        return selected
    requested = set(requested_names)
    filtered = [dataset for dataset in selected if dataset.name in requested]
    missing = sorted(requested - {dataset.name for dataset in filtered})
    if missing:
        raise UsageError("Requested Data Center dataset(s) were not found: " + ", ".join(missing))
    return filtered


def select_dataset_for_replacement(
    datasets: Iterable[DataCenterDataset],
    *,
    domain: str,
    dataset_name: str | None = None,
    dataset_id: str | None = None,
) -> DataCenterDataset:
    """Resolve one exact dataset inside a department boundary."""

    if bool(dataset_name) == bool(dataset_id):
        raise UsageError("provide exactly one of dataset_name or dataset_id")
    if domain == "market":
        candidates = [
            item
            for item in datasets
            if _parent_endswith(item, ("市场顾问部", "市场顾问部"))
        ]
    elif domain == "qingcheng":
        candidates = [
            item
            for item in datasets
            if _parent_endswith(item, ("市场顾问部", "青橙项目部"))
        ]
    else:
        raise UsageError(f"unsupported Data Center replacement domain: {domain}")

    if dataset_id:
        matches = [item for item in candidates if item.id == dataset_id]
        label = dataset_id
    else:
        matches = [item for item in candidates if item.name == dataset_name]
        label = str(dataset_name)
    if not matches:
        raise UsageError(f"Data Center dataset was not found in {domain}: {label}")
    if len(matches) > 1:
        identities = ", ".join(f"{item.id} ({item.path_text})" for item in matches)
        raise UsageError(f"Data Center dataset identity is ambiguous: {label}: {identities}")
    return matches[0]


def _is_login_url(url: str) -> bool:
    return "cas.baijia.com" in url or "login" in url.lower()


def _menu_roots(menu_payload: dict[str, Any]) -> list[dict[str, Any]]:
    data = menu_payload.get("data")
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if not isinstance(data, dict):
        return []

    roots: list[dict[str, Any]] = []
    for key in ("commonList", "ownerList", "shareList", "favoriteList"):
        value = data.get(key)
        if isinstance(value, list):
            roots.extend(item for item in value if isinstance(item, dict))
    if roots:
        return roots
    for value in data.values():
        if isinstance(value, list):
            roots.extend(item for item in value if isinstance(item, dict))
    return roots


def _walk_menu_node(node: dict[str, Any], parent_path: tuple[str, ...]) -> Iterable[DataCenterDataset]:
    name = _clean_text(node.get("name") or node.get("title") or node.get("label"))
    current_path = (*parent_path, name) if name else parent_path
    if _is_sql_dataset_node(node):
        dataset_id = _clean_text(node.get("id") or node.get("key"))
        if dataset_id:
            yield DataCenterDataset(
                id=dataset_id,
                key=_clean_text(node.get("key")),
                name=name or dataset_id,
                file_value=_clean_text(node.get("fileValue")),
                subject_id=_clean_text(node.get("subjectId")),
                parent_id=_clean_text(node.get("parentId")),
                owner=_clean_text(node.get("owner") or node.get("ownerName") or node.get("creator")),
                create_time=_clean_text(node.get("createTime") or node.get("createdAt")),
                path=current_path,
            )
    children = node.get("children") or node.get("childList") or []
    if isinstance(children, list):
        for child in children:
            if isinstance(child, dict):
                yield from _walk_menu_node(child, current_path)


def _is_sql_dataset_node(node: dict[str, Any]) -> bool:
    file_type = _clean_text(node.get("fileType") or node.get("type"))
    return str(node.get("isFile")) == "1" and file_type == DATASET_SQL_FILE_TYPE


def _parent_endswith(dataset: DataCenterDataset, suffix: tuple[str, ...]) -> bool:
    parent = dataset.parent_path
    return len(parent) >= len(suffix) and parent[-len(suffix) :] == suffix


def _clean_text(value: Any) -> str:
    return str(value or "").strip()
