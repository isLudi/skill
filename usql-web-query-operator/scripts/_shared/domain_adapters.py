"""Validated domain-to-skill adapters shared by operator command packages."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import UsageError


SCHEMA_VERSION = "1.0.0"
OPERATOR_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY_PATH = OPERATOR_ROOT / "references" / "domain_adapters.json"
DEFAULT_SKILLS_ROOT = OPERATOR_ROOT.parent
ALLOWED_TARGETS = {"market", "qingcheng"}
ALLOWED_DOMAINS = {"market_consultant", "qingcheng"}
ALLOWED_ROW_STYLES = {"market", "qingcheng"}
ALLOWED_DATA_CENTER_SELECTORS = {"market_from_start", "qingcheng_folder"}


@dataclass(frozen=True)
class DashboardDomainAdapter:
    profile_folders: tuple[str, ...]
    edit_folders: tuple[str, ...]
    knowledge_folders: tuple[str, ...]
    profiles_dir: Path
    profiles_readme: Path
    dashboards_readme: Path | None
    changelog: Path


@dataclass(frozen=True)
class DataCenterDomainAdapter:
    selector: str
    dataset_prefix: str
    doc_filename: str
    title: str
    scope_note_template: str


@dataclass(frozen=True)
class DomainAdapter:
    target: str
    domain_id: str
    skill_name: str
    skill_root: Path
    row_style: str
    dashboard: DashboardDomainAdapter
    data_center: DataCenterDomainAdapter


def load_domain_adapters(
    registry_path: Path | None = None,
    *,
    skills_root: Path | None = None,
) -> tuple[DomainAdapter, ...]:
    path = (registry_path or DEFAULT_REGISTRY_PATH).resolve()
    root = (skills_root or DEFAULT_SKILLS_ROOT).resolve()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UsageError(f"invalid domain adapter registry {path}: {exc}") from exc
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise UsageError(
            f"unsupported domain adapter schema_version: {payload.get('schema_version')}"
        )
    raw_adapters = payload.get("adapters")
    if not isinstance(raw_adapters, list) or not raw_adapters:
        raise UsageError("domain adapter registry must contain a non-empty adapters list")

    adapters = tuple(_parse_adapter(item, root) for item in raw_adapters)
    _validate_unique(adapters, "target")
    _validate_unique(adapters, "domain_id")
    _validate_unique(adapters, "skill_name")
    folder_owners: dict[str, str] = {}
    for adapter in adapters:
        for folder in adapter.dashboard.knowledge_folders:
            previous = folder_owners.setdefault(folder, adapter.domain_id)
            if previous != adapter.domain_id:
                raise UsageError(
                    f"dashboard knowledge folder {folder!r} is registered by multiple domains"
                )
    return adapters


def adapters_by_target(
    adapters: tuple[DomainAdapter, ...] | None = None,
) -> dict[str, DomainAdapter]:
    values = adapters or load_domain_adapters()
    return {adapter.target: adapter for adapter in values}


def adapters_by_domain(
    adapters: tuple[DomainAdapter, ...] | None = None,
) -> dict[str, DomainAdapter]:
    values = adapters or load_domain_adapters()
    return {adapter.domain_id: adapter for adapter in values}


def dashboard_folder_adapters(
    adapters: tuple[DomainAdapter, ...] | None = None,
) -> dict[str, DomainAdapter]:
    values = adapters or load_domain_adapters()
    return {
        folder: adapter
        for adapter in values
        for folder in adapter.dashboard.knowledge_folders
    }


def default_profile_folders(
    adapters: tuple[DomainAdapter, ...] | None = None,
) -> tuple[str, ...]:
    values = adapters or load_domain_adapters()
    return tuple(
        folder
        for adapter in values
        for folder in adapter.dashboard.profile_folders
    )


def default_edit_folders(
    adapters: tuple[DomainAdapter, ...] | None = None,
) -> tuple[str, ...]:
    values = adapters or load_domain_adapters()
    return tuple(
        folder
        for adapter in values
        for folder in adapter.dashboard.edit_folders
    )


def _parse_adapter(value: Any, skills_root: Path) -> DomainAdapter:
    if not isinstance(value, dict):
        raise UsageError("each domain adapter must be an object")
    target = _required_text(value, "target")
    domain_id = _required_text(value, "domain_id")
    skill_name = _required_text(value, "skill_name")
    row_style = _required_text(value, "row_style")
    if target not in ALLOWED_TARGETS:
        raise UsageError(f"unsupported domain adapter target: {target}")
    if domain_id not in ALLOWED_DOMAINS:
        raise UsageError(f"unsupported domain adapter domain_id: {domain_id}")
    if row_style not in ALLOWED_ROW_STYLES:
        raise UsageError(f"unsupported domain adapter row_style: {row_style}")
    if not skill_name or any(char not in "abcdefghijklmnopqrstuvwxyz0123456789-" for char in skill_name):
        raise UsageError(f"invalid domain adapter skill_name: {skill_name}")

    skill_root = (skills_root / skill_name).resolve()
    if skill_root.parent != skills_root:
        raise UsageError(f"domain adapter skill root escapes skills directory: {skill_name}")
    if not skill_root.is_dir():
        raise UsageError(f"registered domain skill does not exist: {skill_root}")
    _validate_skill_metadata(skill_root, skill_name, domain_id)

    dashboard_raw = value.get("dashboard")
    data_center_raw = value.get("data_center")
    if not isinstance(dashboard_raw, dict) or not isinstance(data_center_raw, dict):
        raise UsageError(f"domain adapter {target} is missing dashboard/data_center configuration")
    dashboard = DashboardDomainAdapter(
        profile_folders=_string_tuple(dashboard_raw, "profile_folders"),
        edit_folders=_string_tuple(dashboard_raw, "edit_folders"),
        knowledge_folders=_string_tuple(dashboard_raw, "knowledge_folders"),
        profiles_dir=_relative_path(dashboard_raw, "profiles_dir"),
        profiles_readme=_relative_path(dashboard_raw, "profiles_readme"),
        dashboards_readme=_optional_relative_path(dashboard_raw, "dashboards_readme"),
        changelog=_relative_path(dashboard_raw, "changelog"),
    )
    if not set(dashboard.profile_folders).issubset(dashboard.knowledge_folders):
        raise UsageError(f"profile_folders must be knowledge_folders for target {target}")
    if not set(dashboard.edit_folders).issubset(dashboard.knowledge_folders):
        raise UsageError(f"edit_folders must be knowledge_folders for target {target}")

    selector = _required_text(data_center_raw, "selector")
    if selector not in ALLOWED_DATA_CENTER_SELECTORS:
        raise UsageError(f"unsupported Data Center selector for target {target}: {selector}")
    data_center = DataCenterDomainAdapter(
        selector=selector,
        dataset_prefix=_required_text(data_center_raw, "dataset_prefix"),
        doc_filename=_safe_filename(data_center_raw, "doc_filename"),
        title=_required_text(data_center_raw, "title"),
        scope_note_template=_required_text(data_center_raw, "scope_note_template"),
    )
    return DomainAdapter(
        target=target,
        domain_id=domain_id,
        skill_name=skill_name,
        skill_root=skill_root,
        row_style=row_style,
        dashboard=dashboard,
        data_center=data_center,
    )


def _validate_skill_metadata(skill_root: Path, skill_name: str, domain_id: str) -> None:
    metadata_path = skill_root / "metadata.json"
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UsageError(f"invalid registered skill metadata {metadata_path}: {exc}") from exc
    if metadata.get("name") != skill_name:
        raise UsageError(f"registered skill metadata name mismatch: {metadata_path}")
    if metadata.get("domain_id") != domain_id:
        raise UsageError(f"registered skill metadata domain mismatch: {metadata_path}")


def _validate_unique(adapters: tuple[DomainAdapter, ...], field: str) -> None:
    values = [getattr(adapter, field) for adapter in adapters]
    if len(values) != len(set(values)):
        raise UsageError(f"domain adapter {field} values must be unique")


def _required_text(value: dict[str, Any], key: str) -> str:
    text = str(value.get(key) or "").strip()
    if not text:
        raise UsageError(f"domain adapter field {key} cannot be blank")
    return text


def _string_tuple(value: dict[str, Any], key: str) -> tuple[str, ...]:
    raw = value.get(key)
    if not isinstance(raw, list) or not raw:
        raise UsageError(f"domain adapter field {key} must be a non-empty list")
    items = tuple(str(item).strip() for item in raw)
    if any(not item for item in items) or len(items) != len(set(items)):
        raise UsageError(f"domain adapter field {key} contains blank or duplicate values")
    return items


def _relative_path(value: dict[str, Any], key: str) -> Path:
    text = _required_text(value, key)
    path = Path(text)
    if path.is_absolute() or ".." in path.parts:
        raise UsageError(f"domain adapter field {key} must be a safe relative path")
    return path


def _optional_relative_path(value: dict[str, Any], key: str) -> Path | None:
    if value.get(key) is None:
        return None
    return _relative_path(value, key)


def _safe_filename(value: dict[str, Any], key: str) -> str:
    text = _required_text(value, key)
    if Path(text).name != text or text in {".", ".."}:
        raise UsageError(f"domain adapter field {key} must be a filename")
    return text
