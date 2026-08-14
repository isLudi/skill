"""Artifact-neutral data models for Tiangong2 task exploration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SourceSnapshot:
    source_kind: str
    extension: str
    original_sha256: str
    redacted_sha256: str
    redacted_text: str = field(repr=False)
    redactions: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class VersionSnapshot:
    metadata: dict[str, Any]
    source: SourceSnapshot | None = None


@dataclass
class TaskSnapshot:
    menu: dict[str, Any]
    path: list[str]
    task_type_name: str
    metadata: dict[str, Any]
    current_source: SourceSnapshot
    content_metadata: dict[str, Any]
    schedule: dict[str, Any] | None
    schedule_status: str
    resources: list[dict[str, Any]]
    versions: list[VersionSnapshot]
    analysis: dict[str, Any]
    current_matches_latest_published: bool | None
    published_comparison_basis: str
    warnings: list[str] = field(default_factory=list)


@dataclass
class ExplorationSnapshot:
    schema_version: str
    generated_at: str
    target_url: str
    identity: dict[str, Any]
    login_performed: bool
    project: dict[str, Any]
    requested_folders: list[str]
    folder_roots: list[dict[str, Any]]
    task_type_mapping: list[dict[str, Any]]
    quality_inventory: list[dict[str, Any]]
    tasks: list[TaskSnapshot]
    read_only_endpoints: list[str]
    warnings: list[str] = field(default_factory=list)
