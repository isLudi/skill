"""Exact project/folder/task ownership resolution for Tiangong2 operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from _shared.errors import UsageError

from .client import Tiangong2ReadOnlyClient
from .config import DATA_DEVELOPMENT_ROOT
from .session import identity_matches_username


@dataclass(frozen=True)
class ScopedTask:
    project: dict[str, Any]
    menu: dict[str, Any]
    metadata: dict[str, Any]
    path: tuple[str, ...]
    project_id: int
    folder_name: str
    menu_id: int
    task_id: int
    nezha_task_id: int
    task_name: str
    owner_name: str


def _exact_project(client: Tiangong2ReadOnlyClient, project_id: int) -> dict[str, Any]:
    matches = [item for item in client.list_projects() if int(item.get("id") or 0) == project_id]
    if len(matches) != 1:
        raise UsageError(f"Exact Tiangong2 project id was not uniquely accessible: {project_id}")
    return matches[0]


def _exact_data_folder(
    client: Tiangong2ReadOnlyClient,
    *,
    project_id: int,
    folder_name: str,
) -> dict[str, Any]:
    roots = client.list_menu_children(project_id, -1)
    data_roots = [
        item
        for item in roots
        if item.get("name") == DATA_DEVELOPMENT_ROOT and int(item.get("ifDir") or 0) == 1
    ]
    if len(data_roots) != 1:
        raise UsageError(f"Expected one exact {DATA_DEVELOPMENT_ROOT!r} root, found {len(data_roots)}")
    children = client.list_menu_children(project_id, int(data_roots[0]["id"]))
    matches = [
        item
        for item in children
        if item.get("name") == folder_name and int(item.get("ifDir") or 0) == 1
    ]
    if len(matches) != 1:
        raise UsageError(
            f"Exact target folder {folder_name!r} was not uniquely found under {DATA_DEVELOPMENT_ROOT!r}"
        )
    return matches[0]


def _find_menu(
    client: Tiangong2ReadOnlyClient,
    *,
    project_id: int,
    folder: dict[str, Any],
    menu_id: int,
) -> tuple[dict[str, Any], tuple[str, ...]]:
    found: list[tuple[dict[str, Any], tuple[str, ...]]] = []
    seen: set[int] = set()

    def walk(node: dict[str, Any], path: tuple[str, ...]) -> None:
        node_id = int(node.get("id") or 0)
        if not node_id or node_id in seen:
            return
        seen.add(node_id)
        current_path = (*path, str(node.get("name") or ""))
        if node_id == menu_id:
            found.append((node, current_path))
            return
        if int(node.get("ifDir") or 0) == 1:
            for child in client.list_menu_children(project_id, node_id):
                walk(child, current_path)

    walk(folder, (DATA_DEVELOPMENT_ROOT,))
    if len(found) != 1:
        raise UsageError(
            f"Exact menu id {menu_id} was not uniquely found inside "
            f"{DATA_DEVELOPMENT_ROOT}/{folder.get('name')}"
        )
    return found[0]


def _owned_by_active_identity(metadata: dict[str, Any], identity: dict[str, Any]) -> bool:
    identity_name = str(identity.get("name") or "").strip()
    identity_id = str(identity.get("id") or "").strip()
    principal = str(metadata.get("principal") or "").strip()
    if principal:
        return bool(
            (identity_id and principal == identity_id)
            or identity_matches_username({"name": principal}, identity_name)
        )
    creator = str(metadata.get("creator") or "").strip()
    return identity_matches_username({"name": creator}, identity_name)


def resolve_owned_task(
    client: Tiangong2ReadOnlyClient,
    *,
    identity: dict[str, Any],
    project_id: int,
    folder_name: str,
    menu_id: int,
    task_name: str,
) -> ScopedTask:
    """Resolve one exact task and reject cross-project, cross-folder, or cross-owner access."""

    identity_name = str(identity.get("name") or "").strip()
    if not identity_name:
        raise UsageError("Authenticated Tiangong2 identity has no stable name")
    if not folder_name.strip() or not task_name.strip():
        raise UsageError("Exact non-empty folder and task names are required")
    project = _exact_project(client, project_id)
    folder = _exact_data_folder(client, project_id=project_id, folder_name=folder_name)
    menu, path = _find_menu(client, project_id=project_id, folder=folder, menu_id=menu_id)
    if int(menu.get("ifDir") or 0) == 1:
        raise UsageError(f"Menu id {menu_id} resolves to a folder, not a task")
    metadata = client.get_task(menu_id)
    resolved_name = str(metadata.get("taskName") or menu.get("name") or "").strip()
    if resolved_name != task_name:
        raise UsageError(
            f"Tiangong2 task name mismatch for menu {menu_id}: expected={task_name!r}, actual={resolved_name!r}"
        )
    if not _owned_by_active_identity(metadata, identity):
        raise UsageError(
            f"Tiangong2 task {menu_id} is not owned by the authenticated identity {identity_name!r}"
        )
    task_id = int(metadata.get("taskId") or menu.get("taskId") or 0)
    nezha_task_id = int(metadata.get("nezhaId") or 0)
    if task_id <= 0:
        raise UsageError(f"Tiangong2 task id is missing for menu {menu_id}")
    return ScopedTask(
        project=dict(project),
        menu=dict(menu),
        metadata=dict(metadata),
        path=path,
        project_id=project_id,
        folder_name=folder_name,
        menu_id=menu_id,
        task_id=task_id,
        nezha_task_id=nezha_task_id,
        task_name=resolved_name,
        owner_name=identity_name,
    )
