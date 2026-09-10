"""Stable extension contracts. Department-specific payloads remain inside report data."""
from pathlib import Path
from typing import Any, Mapping, Protocol, TypedDict, runtime_checkable


class DeliveryTarget(TypedDict):
    id: str
    chat_id: str
    display_name: str
    enabled: bool


class PreviewArtifacts(TypedDict):
    html: str
    markdown: str
    metadata: str


class PreparedReport(TypedDict):
    """Minimum transport envelope; never persist coordinates containing a Base token."""
    report_profile: str
    channel: str
    period: str
    report_type: str
    chat_id: str
    identity: str
    markdown: str
    idempotency_key: str
    raw_count: int
    raw_read_audit: dict[str, Any]
    snapshot: list[str]
    image_path: Path | None
    result_image_path: Path | None


@runtime_checkable
class DepartmentAdapter(Protocol):
    def validate_definition(self, definition: Mapping[str, Any]) -> None: ...
    def prepare(self, definition, target: DeliveryTarget, *, report_type="auto", state_dir=None) -> PreparedReport: ...
    def write_preview(self, context: PreparedReport) -> PreviewArtifacts: ...
    def schedule(self, definition, target: DeliveryTarget, *, preflight=False) -> int: ...


class ReportPorts(Protocol):
    """Read-only preparation boundary; no upload/send method is exposed here."""
    def resolve_source(self, args) -> dict[str, str]: ...
    def field_names(self, coordinates, args) -> set[str]: ...
    def read_records(self, coordinates, args, fields, *, filter_json, audit) -> list[dict[str, Any]]: ...
    def search_users(self, queries, args) -> dict[str, Any]: ...
    def verify_target(self, chat_id, name, identity, timeout) -> dict[str, Any]: ...
    def missing_members(self, chat_id, resolved, identity, timeout) -> list[str]: ...
