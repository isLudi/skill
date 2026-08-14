"""Allowlisted read-only Tiangong2 API adapter."""

from __future__ import annotations

from typing import Any

from _shared.config import TIANGONG2_BASE_API_BASE, TIANGONG2_DP_API_BASE
from _shared.errors import UsageError

from .config import (
    BASE_READ_ENDPOINTS,
    FORBIDDEN_ENDPOINT_TERMS,
    FORM_READ_ENDPOINTS,
    JSON_READ_ENDPOINTS,
    TASK_CONTENT_SPECS,
    TaskContentSpec,
)


class Tiangong2ReadOnlyClient:
    """Small API client with no generic request or mutation escape hatch."""

    def __init__(
        self,
        request_context: Any,
        *,
        dp_api_base: str = TIANGONG2_DP_API_BASE,
        base_api_base: str = TIANGONG2_BASE_API_BASE,
    ) -> None:
        self._request = request_context
        self._dp_api_base = dp_api_base.rstrip("/")
        self._base_api_base = base_api_base.rstrip("/")
        self._validate_registry()
        self.used_endpoints: set[str] = set()

    @staticmethod
    def _validate_registry() -> None:
        all_endpoints = set(FORM_READ_ENDPOINTS) | set(JSON_READ_ENDPOINTS) | set(BASE_READ_ENDPOINTS)
        for endpoint in all_endpoints:
            segments = {segment.lower() for segment in endpoint.replace("-", "/").replace("_", "/").split("/")}
            blocked = segments & FORBIDDEN_ENDPOINT_TERMS
            if blocked:
                raise RuntimeError(f"Read-only endpoint registry contains a forbidden operation: {endpoint}: {sorted(blocked)}")

    @staticmethod
    def _json_body(response: Any, endpoint: str) -> dict[str, Any]:
        if not getattr(response, "ok", False):
            raise UsageError(f"Tiangong2 read failed: HTTP {getattr(response, 'status', '?')} from {endpoint}")
        body = response.json()
        if not isinstance(body, dict):
            raise UsageError(f"Tiangong2 returned a non-object response from {endpoint}")
        if body.get("status") != "success" or body.get("errorCode") not in (0, None):
            message = str(body.get("error") or "platform returned an error")
            raise UsageError(f"Tiangong2 read failed at {endpoint}: {message}")
        return body

    def _get_base(self, endpoint: str) -> dict[str, Any]:
        if endpoint not in BASE_READ_ENDPOINTS:
            raise UsageError(f"Blocked non-allowlisted Tiangong2 base endpoint: {endpoint}")
        self.used_endpoints.add(f"GET base/{endpoint}")
        response = self._request.get(f"{self._base_api_base}/{endpoint}", timeout=45_000)
        return self._json_body(response, f"base/{endpoint}")

    def _post_form_body(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        if endpoint not in FORM_READ_ENDPOINTS:
            raise UsageError(f"Blocked non-allowlisted Tiangong2 form endpoint: {endpoint}")
        self.used_endpoints.add(f"POST form/{endpoint}")
        response = self._request.post(
            f"{self._dp_api_base}/{endpoint}",
            form={key: "" if value is None else str(value) for key, value in payload.items()},
            timeout=45_000,
        )
        return self._json_body(response, endpoint)

    def _post_json_body(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        if endpoint not in JSON_READ_ENDPOINTS:
            raise UsageError(f"Blocked non-allowlisted Tiangong2 JSON endpoint: {endpoint}")
        self.used_endpoints.add(f"POST json/{endpoint}")
        response = self._request.post(f"{self._dp_api_base}/{endpoint}", data=payload, timeout=45_000)
        return self._json_body(response, endpoint)

    def get_identity(self) -> dict[str, Any]:
        return dict(self._get_base("cas/getAuth").get("data") or {})

    def list_projects(self) -> list[dict[str, Any]]:
        return list(self._get_base("menu/listProjects").get("data") or [])

    def list_menu_children(self, project_id: int, parent_id: int) -> list[dict[str, Any]]:
        body = self._post_form_body(
            "menu/listMenus",
            {"projectId": project_id, "nodeType": 1, "parentId": parent_id},
        )
        data = body.get("data") or {}
        return list(data.get("menus") or [])

    def task_type_mapping(self) -> list[dict[str, Any]]:
        return list(self._post_form_body("constant/taskTypeNameCodeMapping", {}).get("data") or [])

    def get_task(self, menu_id: int) -> dict[str, Any]:
        return dict(self._post_form_body("dataDevelop/getTask", {"id": menu_id}).get("data") or {})

    def get_task_content(
        self,
        *,
        menu_id: int,
        task_id: int,
        task_type: int,
    ) -> tuple[TaskContentSpec, dict[str, Any]]:
        spec = TASK_CONTENT_SPECS.get(task_type)
        if spec is None:
            raise UsageError(f"Unsupported Tiangong2 task type {task_type} at menu {menu_id}")
        identifier = menu_id if spec.use_menu_id else task_id
        body = self._post_form_body(spec.endpoint, {spec.payload_key: identifier})
        data = body.get("data")
        if not isinstance(data, dict):
            raise UsageError(f"Tiangong2 returned no task content for menu {menu_id}")
        return spec, data

    def get_schedule(self, task_id: int) -> dict[str, Any]:
        return dict(self._post_json_body("task/getScheduleConfig", {"taskId": task_id}).get("data") or {})

    def list_resources(self, menu_id: int, *, page_size: int = 500) -> list[dict[str, Any]]:
        body = self._post_json_body(
            "resource/task/list",
            {"menuId": menu_id, "pageNo": 1, "pageSize": page_size},
        )
        return list(body.get("data") or [])

    def list_versions(self, task_id: int) -> list[dict[str, Any]]:
        return list(self._post_form_body("ver/listVersions", {"taskId": task_id}).get("data") or [])

    def get_version_code(self, version_id: int) -> dict[str, Any]:
        return dict(self._post_form_body("ver/getCode", {"verId": version_id}).get("data") or {})

    def list_quality_inventory(self, project_id: int, *, page_size: int = 100) -> list[dict[str, Any]]:
        page_no = 1
        items: list[dict[str, Any]] = []
        while True:
            body = self._post_json_body(
                "quality/list",
                {"search": None, "projectId": project_id, "pageNo": page_no, "pageSize": page_size},
            )
            items.extend(list(body.get("data") or []))
            page_query = body.get("pageQuery") or {}
            page_total = int(page_query.get("pageTotal") or 1)
            if page_no >= page_total:
                break
            page_no += 1
        return items
