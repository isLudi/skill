"""Manual-table registry for local Excel uploads."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from _shared.errors import UsageError


DEFAULT_REGISTRY_PATH = Path(__file__).resolve().parents[2] / "references" / "manual_temp_table_registry.json"


@dataclass(frozen=True)
class ManualTableEntry:
    """One local manual table and its platform mapping metadata."""

    raw: dict[str, Any]
    file_path: Path

    @property
    def id(self) -> str:
        return str(self.raw.get("id", ""))

    @property
    def local_filename(self) -> str:
        return str(self.raw.get("local_filename", ""))

    @property
    def standard_temp_table(self) -> str | None:
        value = self.raw.get("standard_temp_table")
        return str(value).strip() if value else None

    @property
    def auto_target(self) -> bool:
        return bool(self.raw.get("auto_target", False))

    def as_summary(self) -> dict[str, Any]:
        return {
            "id": self.raw.get("id"),
            "domain": self.raw.get("domain"),
            "business_name": self.raw.get("business_name"),
            "local_filename": self.raw.get("local_filename"),
            "standard_temp_table": self.raw.get("standard_temp_table"),
            "mapping_status": self.raw.get("mapping_status"),
            "confidence": self.raw.get("confidence"),
            "auto_target": self.raw.get("auto_target"),
            "candidate_temp_tables": self.raw.get("candidate_temp_tables"),
            "sheet": self.raw.get("sheet"),
            "header_row": self.raw.get("header_row", True),
            "notes": self.raw.get("notes", []),
        }


class ManualTableRegistry:
    """Load and query the manual temp-table registry."""

    def __init__(self, path: Path, data: dict[str, Any]) -> None:
        self.path = path
        self.data = data
        self.roots = {str(key): Path(value) for key, value in data.get("roots", {}).items()}

    @classmethod
    def load(cls, path: Path | None = None) -> "ManualTableRegistry":
        registry_path = path or DEFAULT_REGISTRY_PATH
        if not registry_path.exists():
            raise UsageError(f"Manual table registry not found: {registry_path}")
        data = json.loads(registry_path.read_text(encoding="utf-8"))
        return cls(registry_path, data)

    def entries(self) -> list[ManualTableEntry]:
        return [ManualTableEntry(raw=raw, file_path=self.entry_file_path(raw)) for raw in self.data.get("tables", [])]

    def entry_file_path(self, raw: dict[str, Any]) -> Path:
        root = self.roots.get(str(raw.get("domain", "")))
        filename = str(raw.get("local_filename", ""))
        return (root / filename) if root else Path(filename)

    def resolve_file(self, file_path: Path) -> ManualTableEntry | None:
        normalized = _normalize_path(file_path)
        for entry in self.entries():
            if normalized == _normalize_path(entry.file_path):
                return entry

        matching_by_name = [
            entry
            for entry in self.entries()
            if entry.local_filename.casefold() == file_path.name.casefold()
        ]
        if len(matching_by_name) == 1:
            return matching_by_name[0]
        return None

    def infer_target_table(self, file_path: Path, explicit_target_table: str | None) -> tuple[str | None, ManualTableEntry | None]:
        entry = self.resolve_file(file_path)
        explicit_target = explicit_target_table.strip() if explicit_target_table else None
        if explicit_target:
            return explicit_target, entry
        if entry is None:
            return None, None
        if entry.standard_temp_table and entry.auto_target:
            return entry.standard_temp_table, entry
        if entry.standard_temp_table:
            candidates = entry.raw.get("candidate_temp_tables") or [entry.standard_temp_table]
            raise UsageError(
                "Manual table mapping requires confirmation for "
                f"{entry.local_filename}: candidates={candidates}. "
                "Pass --target-table explicitly after confirming the table."
            )
        candidates = entry.raw.get("candidate_temp_tables") or []
        raise UsageError(
            "No safe temporary-table target is registered for "
            f"{entry.local_filename}. Candidate tables: {candidates}"
        )


def _normalize_path(path: Path) -> str:
    return str(path.resolve(strict=False)).casefold()
