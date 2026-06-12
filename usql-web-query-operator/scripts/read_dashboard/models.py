"""Structured models for dashboard discovery and profiling."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DashboardRecord:
    name: str
    dashboard_id: str | None
    numeric_id: str | None
    file_value: str | None
    parent_id: str | None
    owner: str | None
    folder_path: str | None
    href: str | None = None
    source: str = "menu_manage_api"


@dataclass
class DashboardScanSummary:
    ok: bool
    folder: str
    count: int
    output_path: str
    records: list[DashboardRecord]
    message: str


@dataclass
class DashboardProfileSummary:
    ok: bool
    dashboard_name: str
    dashboard_id: str
    output_path: str
    rendered: bool
    unit_count: int
    value_unit_count: int
    data_ready_unit_count: int
    message: str


@dataclass
class DashboardKnowledgeEntry:
    folder: str
    dashboard_name: str
    dashboard_id: str
    filename: str
    ok: bool
    rendered: bool
    message: str
