"""Recursive read-only exploration orchestration."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from typing import Any

from _shared.config import TIANGONG2_TASK_URL
from _shared.errors import UsageError

from .analysis import analyze_source
from .client import Tiangong2ReadOnlyClient
from .config import DATA_DEVELOPMENT_ROOT, TaskContentSpec
from .models import ExplorationSnapshot, SourceSnapshot, TaskSnapshot, VersionSnapshot
from .redaction import redact_structure, redact_text, structure_as_redacted_json


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _source_snapshot(spec: TaskContentSpec, content: dict[str, Any]) -> SourceSnapshot:
    if spec.source_keys:
        source = next(
            (content.get(key) for key in spec.source_keys if isinstance(content.get(key), str)),
            None,
        )
        if source is None:
            raise UsageError(f"No source field found in {spec.endpoint}: expected {list(spec.source_keys)}")
        result = redact_text(source)
    else:
        source = json.dumps(content, ensure_ascii=False, indent=2, sort_keys=True)
        result = structure_as_redacted_json(content)
    return SourceSnapshot(
        source_kind=spec.source_kind,
        extension=spec.extension,
        original_sha256=_sha256(source),
        redacted_sha256=_sha256(result.text),
        redacted_text=result.text,
        redactions=[dict(item) for item in result.findings],
    )


def _version_source_snapshot(
    *,
    source_kind: str,
    extension: str,
    code: str,
) -> SourceSnapshot:
    result = redact_text(code)
    return SourceSnapshot(
        source_kind=source_kind,
        extension=extension,
        original_sha256=_sha256(code),
        redacted_sha256=_sha256(result.text),
        redacted_text=result.text,
        redactions=[dict(item) for item in result.findings],
    )


def _normalized_editor_source(source_kind: str, text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if source_kind in {"kyuubi_sql", "spark_sql"}:
        normalized = re.sub(r"^\s*sql\s*:\s*", "", normalized, count=1, flags=re.I)
        normalized = re.sub(r"\n\s*SQL参数\s*:.*\Z", "", normalized, flags=re.S)
    return "\n".join(line.rstrip() for line in normalized.splitlines()).strip()


class Tiangong2TaskExplorer:
    def __init__(self, client: Tiangong2ReadOnlyClient) -> None:
        self.client = client

    def _resolve_project(self, project_id: int) -> dict[str, Any]:
        matches = [item for item in self.client.list_projects() if int(item.get("id") or 0) == project_id]
        if len(matches) != 1:
            raise UsageError(f"Exact Tiangong2 project id was not uniquely accessible: {project_id}")
        return matches[0]

    def _resolve_folder_roots(self, project_id: int, folder_names: list[str]) -> list[dict[str, Any]]:
        roots = self.client.list_menu_children(project_id, -1)
        data_roots = [
            item
            for item in roots
            if item.get("name") == DATA_DEVELOPMENT_ROOT and int(item.get("ifDir") or 0) == 1
        ]
        if len(data_roots) != 1:
            raise UsageError(f"Expected one exact {DATA_DEVELOPMENT_ROOT!r} root, found {len(data_roots)}")
        children = self.client.list_menu_children(project_id, int(data_roots[0]["id"]))
        resolved: list[dict[str, Any]] = []
        for name in folder_names:
            matches = [
                item
                for item in children
                if item.get("name") == name and int(item.get("ifDir") or 0) == 1
            ]
            if len(matches) != 1:
                raise UsageError(f"Exact target folder {name!r} was not uniquely found under {DATA_DEVELOPMENT_ROOT!r}")
            resolved.append(matches[0])
        return resolved

    def _walk_tasks(
        self,
        *,
        project_id: int,
        root: dict[str, Any],
    ) -> list[tuple[dict[str, Any], list[str]]]:
        tasks: list[tuple[dict[str, Any], list[str]]] = []

        def walk(node: dict[str, Any], path: list[str]) -> None:
            current_path = [*path, str(node.get("name") or "")]
            if int(node.get("ifDir") or 0) == 1:
                for child in self.client.list_menu_children(project_id, int(node["id"])):
                    walk(child, current_path)
            else:
                tasks.append((node, current_path))

        walk(root, [DATA_DEVELOPMENT_ROOT])
        return tasks

    @staticmethod
    def _safe_structure(value: Any) -> Any:
        redacted, _ = redact_structure(value)
        return redacted

    def _explore_task(
        self,
        *,
        menu: dict[str, Any],
        path: list[str],
        quality_inventory: list[dict[str, Any]],
        include_version_code: bool,
    ) -> TaskSnapshot:
        menu_id = int(menu.get("id") or 0)
        metadata = self.client.get_task(menu_id)
        task_id = int(metadata.get("taskId") or menu.get("taskId") or 0)
        task_type = int(metadata.get("taskType") or menu.get("taskType") or 0)
        if not task_id:
            raise UsageError(f"Task id is missing for menu {menu_id}")
        spec, content = self.client.get_task_content(
            menu_id=menu_id,
            task_id=task_id,
            task_type=task_type,
        )
        current_source = _source_snapshot(spec, content)
        content_metadata_raw = {
            key: value for key, value in content.items() if key not in set(spec.source_keys)
        }
        content_metadata = self._safe_structure(content_metadata_raw)
        warnings: list[str] = []

        try:
            schedule = self._safe_structure(self.client.get_schedule(task_id))
            schedule_status = "configured" if schedule else "unconfigured"
        except UsageError as exc:
            schedule = None
            schedule_status = "unavailable"
            warnings.append(f"schedule_unavailable: {exc}")

        try:
            resources = self._safe_structure(self.client.list_resources(menu_id))
        except UsageError as exc:
            resources = []
            warnings.append(f"resources_unavailable: {exc}")

        try:
            version_metadata = self.client.list_versions(task_id)
        except UsageError as exc:
            version_metadata = []
            warnings.append(f"versions_unavailable: {exc}")

        versions: list[VersionSnapshot] = []
        for raw_version in version_metadata:
            safe_metadata = self._safe_structure(raw_version)
            version_source = None
            if include_version_code:
                version_id = int(raw_version.get("id") or 0)
                if not version_id:
                    warnings.append("version_missing_id")
                else:
                    try:
                        code_payload = self.client.get_version_code(version_id)
                        code = code_payload.get("code")
                        if not isinstance(code, str):
                            warnings.append(f"version_code_missing: {version_id}")
                        else:
                            version_source = _version_source_snapshot(
                                source_kind=spec.source_kind,
                                extension=spec.extension,
                                code=code,
                            )
                    except UsageError as exc:
                        warnings.append(f"version_code_unavailable:{version_id}: {exc}")
            versions.append(VersionSnapshot(metadata=safe_metadata, source=version_source))

        latest_published = next(
            (item for item in versions if str(item.metadata.get("status") or "") == "已发布"),
            versions[0] if versions else None,
        )
        current_matches_latest = None
        comparison_basis = (
            "normalized_editor_source"
            if spec.source_kind in {"kyuubi_sql", "spark_sql"}
            else "exact_source_sha256"
        )
        if latest_published and latest_published.source:
            if comparison_basis == "normalized_editor_source":
                current_matches_latest = _normalized_editor_source(
                    spec.source_kind,
                    current_source.redacted_text,
                ) == _normalized_editor_source(
                    spec.source_kind,
                    latest_published.source.redacted_text,
                )
            else:
                current_matches_latest = (
                    current_source.original_sha256 == latest_published.source.original_sha256
                )

        analysis = analyze_source(
            task_name=str(metadata.get("taskName") or menu.get("name") or ""),
            path=path,
            task_type_name=spec.type_name,
            source_kind=spec.source_kind,
            source=current_source.redacted_text,
            redactions=current_source.redactions,
        )
        produced = {
            item.lower()
            for item in [*analysis.get("write_tables", []), *analysis.get("created_tables", [])]
        }
        analysis["matching_quality_tables"] = [
            self._safe_structure(item)
            for item in quality_inventory
            if str(item.get("tableName") or "").lower() in produced
        ]

        return TaskSnapshot(
            menu=self._safe_structure({key: value for key, value in menu.items() if key != "children"}),
            path=path,
            task_type_name=spec.type_name,
            metadata=self._safe_structure(metadata),
            current_source=current_source,
            content_metadata=content_metadata,
            schedule=schedule,
            schedule_status=schedule_status,
            resources=resources,
            versions=versions,
            analysis=analysis,
            current_matches_latest_published=current_matches_latest,
            published_comparison_basis=comparison_basis,
            warnings=warnings,
        )

    def explore(
        self,
        *,
        identity: dict[str, Any],
        login_performed: bool,
        project_id: int,
        folder_names: list[str],
        include_version_code: bool,
    ) -> ExplorationSnapshot:
        if not folder_names or any(not name.strip() for name in folder_names):
            raise UsageError("At least one non-empty exact --folder is required")
        if len(folder_names) != len(set(folder_names)):
            raise UsageError("Duplicate --folder values are not allowed")
        project = self._resolve_project(project_id)
        folder_roots = self._resolve_folder_roots(project_id, folder_names)
        task_type_mapping = self.client.task_type_mapping()
        quality_inventory = self.client.list_quality_inventory(project_id)
        task_nodes: list[tuple[dict[str, Any], list[str]]] = []
        for root in folder_roots:
            task_nodes.extend(self._walk_tasks(project_id=project_id, root=root))
        tasks = [
            self._explore_task(
                menu=menu,
                path=path,
                quality_inventory=quality_inventory,
                include_version_code=include_version_code,
            )
            for menu, path in task_nodes
        ]
        safe_identity = {
            key: identity.get(key)
            for key in ("id", "name", "displayName", "department", "manager")
            if identity.get(key) is not None
        }
        return ExplorationSnapshot(
            schema_version="tiangong2-task-exploration-v1",
            generated_at=datetime.now().astimezone().isoformat(timespec="seconds"),
            target_url=TIANGONG2_TASK_URL,
            identity=safe_identity,
            login_performed=login_performed,
            project=self._safe_structure(project),
            requested_folders=list(folder_names),
            folder_roots=[self._safe_structure(item) for item in folder_roots],
            task_type_mapping=self._safe_structure(task_type_mapping),
            quality_inventory=self._safe_structure(quality_inventory),
            tasks=tasks,
            read_only_endpoints=sorted(self.client.used_endpoints),
        )
