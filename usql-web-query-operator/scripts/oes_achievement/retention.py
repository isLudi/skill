"""Expire verified completed runs while keeping a compact replay guard."""

from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import re
import shutil

from _shared.errors import UsageError
from .base_records import HEADERS
from .board import SHANGHAI
from .event_log import is_link
from .workbook import atomic_json, validate_output_dir


def validate_days(value: int, name: str) -> int:
    if type(value) is not int or not 1 <= value <= 3650:
        raise UsageError(f"{name} must be an integer from 1 to 3650.")
    return value


def completed_time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("Timezone missing")
        return parsed.astimezone(SHANGHAI)
    except (TypeError, ValueError, AttributeError) as exc:
        raise UsageError("Cache completion time must be a timezone-aware ISO timestamp.") from exc


class CacheRetention:
    def __init__(self, output: Path, index: Path, base_token: str, table_id: str, days: int, logger, *, clock=None):
        self.output, self.index = validate_output_dir(output), validate_output_dir(index)
        if self.output == self.index or self.output in self.index.parents:
            raise UsageError("The completion index must stay outside the cache directory.")
        self.output.mkdir(parents=True, exist_ok=True)
        self.index.mkdir(parents=True, exist_ok=True)
        self.base_token, self.table_id = base_token, table_id
        self.days, self.logger = validate_days(days, "cache_retention_days"), logger
        self.clock = clock or (lambda: datetime.now(SHANGHAI))

    def _index_path(self, name: str) -> Path:
        if not re.fullmatch(r"base-sync-[0-9a-f]{24}", name):
            raise UsageError("Unrecognized cache directory name.")
        path = self.index / f"{name}.json"
        for candidate in (path, path.with_suffix(".json.tmp")):
            if (candidate.exists() or candidate.is_symlink()) and is_link(candidate):
                raise UsageError("Completion index links are unsupported.")
        return path

    def _valid(self, metadata: dict, directory: Path) -> bool:
        identity, verification = metadata.get("identity", {}), metadata.get("verification", {})
        if not isinstance(identity, dict) or not isinstance(verification, dict):
            return False
        fields = verification.get("fields_verified")
        if not isinstance(fields, list) or not all(isinstance(field, str) for field in fields):
            return False
        run_hash = identity.get("run_key_hash", "")
        return (metadata.get("schema_version") == 1 and metadata.get("status") == "completed"
                and identity.get("base_token") == self.base_token and identity.get("table_id") == self.table_id
                and isinstance(run_hash, str) and re.fullmatch(r"[0-9a-f]{64}", run_hash) is not None
                and directory.name == f"base-sync-{run_hash[:24]}"
                and metadata.get("cache_directory") == str(directory)
                and type(metadata.get("row_count")) is int and metadata["row_count"] >= 0
                and verification.get("verified") is True and type(verification.get("mismatch_count")) is int
                and verification["mismatch_count"] == 0 and type(verification.get("row_count")) is int
                and verification.get("row_count") == metadata["row_count"]
                and len(fields) == len(HEADERS) and set(fields) == set(HEADERS)
                and type(verification.get("cell_comparisons")) is int
                and verification["cell_comparisons"] == metadata["row_count"] * len(HEADERS)
                and isinstance(verification.get("row_multiset_sha256"), str)
                and re.fullmatch(r"[0-9a-f]{64}", verification["row_multiset_sha256"]) is not None)

    def _load(self, path: Path) -> dict:
        try:
            result = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(result, dict):
                raise ValueError("Expected object")
            return result
        except (OSError, ValueError) as exc:
            raise UsageError("Cache receipt or completion index is unreadable; no automatic cleanup/replay.") from exc

    def register(self, receipt: dict) -> dict:
        identity = receipt.get("identity")
        run_hash = identity.get("run_key_hash", "") if isinstance(identity, dict) else ""
        if receipt.get("status") != "completed" or not isinstance(run_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", run_hash):
            raise UsageError("Completed run hash is invalid.")
        directory = self.output / f"base-sync-{run_hash[:24]}"
        metadata = {"schema_version": 1, "status": "completed", "identity": receipt["identity"],
                    "row_count": receipt.get("row_count"), "verification": receipt.get("verification"),
                    "end_ms": receipt.get("end_ms"), "completed_at": receipt.get("completed_at"),
                    "cache_directory": str(directory), "cache_state": "retained"}
        if not self._valid(metadata, directory):
            raise UsageError("Only fully verified Base runs may enter the completion index.")
        completed_time(metadata["completed_at"])
        atomic_json(self._index_path(directory.name), metadata)
        return metadata

    def expired_completion(self, run_hash: str) -> dict | None:
        directory = self.output / f"base-sync-{run_hash[:24]}"
        path = self._index_path(directory.name)
        if not path.exists():
            return None
        metadata = self._load(path)
        if not self._valid(metadata, directory) or metadata["identity"]["run_key_hash"] != run_hash:
            raise UsageError("Completion index identity changed; no new export or replacement was started.")
        if metadata.get("cache_state") in ("cleanup_pending", "purged") or not directory.exists():
            return metadata
        return None

    def _safe_tree(self, directory: Path) -> tuple[int, int]:
        # Validate the absolute target and every entry before recursive deletion.
        if directory.resolve() != directory or directory.parent != self.output or is_link(directory):
            raise UsageError("Cache target resolved outside its intended directory.")
        files, size = 0, 0
        def unreadable(error):
            raise error
        for current, folders, names in os.walk(directory, followlinks=False, onerror=unreadable):
            for name in folders + names:
                path = Path(current) / name
                if is_link(path) or directory not in path.resolve().parents:
                    raise UsageError("Cache contains a link or junction; cleanup was stopped.")
            for name in names:
                files += 1
                size += (Path(current) / name).stat().st_size
        return files, size

    def cleanup(self) -> dict:
        cutoff = self.clock().astimezone(SHANGHAI) - timedelta(days=self.days)
        result = {"retention_days": self.days, "deleted_runs": 0, "deleted_files": 0, "deleted_bytes": 0,
                  "retained_runs": 0, "skipped_runs": 0, "failed_runs": 0}
        self.logger.emit("cache_cleanup_started", retention_days=self.days, cutoff_time=cutoff.isoformat())
        for directory in self.output.glob("base-sync-*"):
            try:
                if not re.fullmatch(r"base-sync-[0-9a-f]{24}", directory.name) or not directory.is_dir() or is_link(directory):
                    result["skipped_runs"] += 1
                    self.logger.emit("cache_retained", cache_path=str(directory), reason="unrecognized_directory_or_link")
                    continue
                path = self._index_path(directory.name)
                receipt_path = directory / "base-receipt.json"
                if path.exists():
                    metadata = self._load(path)
                    if not self._valid(metadata, directory):
                        raise UsageError("Cache/index coordinates changed.")
                elif receipt_path.is_file() and not is_link(receipt_path):
                    receipt = self._load(receipt_path)
                    identity = receipt.get("identity")
                    if receipt.get("status") != "completed" or not isinstance(identity, dict) or identity.get("base_token") != self.base_token or identity.get("table_id") != self.table_id:
                        result["skipped_runs"] += 1
                        self.logger.emit("cache_retained", cache_path=str(directory), reason="unfinished_or_other_target")
                        continue
                    metadata = self.register(receipt)
                else:
                    result["skipped_runs"] += 1
                    continue
                if completed_time(metadata["completed_at"]) >= cutoff:
                    result["retained_runs"] += 1
                    continue
                if receipt_path.exists():
                    if is_link(receipt_path):
                        raise UsageError("Cache receipt link is unsupported.")
                    receipt = self._load(receipt_path)
                    if receipt.get("status") != "completed" or receipt.get("identity") != metadata["identity"]:
                        result["skipped_runs"] += 1
                        self.logger.emit("cache_retained", cache_path=str(directory), reason="receipt_changed")
                        continue
                elif metadata.get("cache_state") != "cleanup_pending":
                    result["skipped_runs"] += 1
                    continue
                files, size = self._safe_tree(directory)
                metadata["cache_state"] = "cleanup_pending"
                atomic_json(path, metadata)  # Save replay guard before removing any cached file.
                shutil.rmtree(directory)
                metadata.update(cache_state="purged", cache_removed_at=self.clock().astimezone(SHANGHAI).isoformat())
                atomic_json(path, metadata)
                result["deleted_runs"] += 1
                result["deleted_files"] += files
                result["deleted_bytes"] += size
                self.logger.emit("cache_run_deleted", cache_path=str(directory), deleted_files=files, deleted_bytes=size)
            except (OSError, UsageError, TypeError, KeyError, ValueError) as exc:
                result["failed_runs"] += 1
                self.logger.emit("cache_cleanup_failed", cache_path=str(directory), error_type=type(exc).__name__)
        self.logger.emit("cache_cleanup_completed", **result)
        return result
