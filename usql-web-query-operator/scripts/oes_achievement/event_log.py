"""Small daily JSONL logs containing operational metadata, never source rows."""

from datetime import datetime, timedelta
import json
from pathlib import Path
import re
import stat
from threading import Lock

from _shared.errors import UsageError
from .board import SHANGHAI
from .workbook import validate_output_dir

FIELDS = {"phase", "status", "row_count", "batch_index", "batch_rows", "batch_count", "previous_rows",
          "deleted_runs", "deleted_files", "deleted_bytes", "retained_runs", "skipped_runs", "failed_runs",
          "reason", "error_type", "seconds", "receipt_path", "start_time", "cutoff_time", "retention_days",
          "cache_path", "exit_code", "reused", "message_hash", "log_files_deleted"}


def is_link(path: Path) -> bool:
    return path.is_symlink() or bool(getattr(path.lstat(), "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))


class EventLog:
    def __init__(self, directory: Path, run_hash: str, table_id: str, *, clock=None):
        self.directory = validate_output_dir(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.run_hash, self.table_id = run_hash, table_id
        self.clock = clock or (lambda: datetime.now(SHANGHAI))
        self.lock = Lock()
        self.write_errors = 0
        if not self.emit("logging_ready"):
            raise UsageError("The run log cannot be written; no Base replacement was started.")

    @property
    def path(self) -> Path:
        return self.directory / f"oes-base-{self.clock().astimezone(SHANGHAI):%Y-%m-%d}.jsonl"

    def emit(self, event: str, **values) -> bool:
        if not re.fullmatch(r"[a-z_0-9]+", event):
            raise ValueError("Log event names must be fixed identifiers.")
        record = {"time": self.clock().astimezone(SHANGHAI).isoformat(timespec="milliseconds"),
                  "event": event, "run_hash": self.run_hash, "table_id": self.table_id}
        # Do not accept arbitrary exception messages, credentials, or source rows.
        for key, value in values.items():
            if key in FIELDS and type(value) in (str, int, float, bool, type(None)):
                record[key] = value[:800] if isinstance(value, str) else value
        try:
            with self.lock:
                path = self.path
                if (path.exists() or path.is_symlink()) and is_link(path):
                    raise OSError("Log link is unsupported.")
                with path.open("a", encoding="utf-8", newline="\n") as output:
                    output.write(json.dumps(record, ensure_ascii=False) + "\n")
            return True
        except OSError:
            self.write_errors += 1
            return False

    def prune(self, days: int) -> int:
        cutoff = self.clock().astimezone(SHANGHAI).date() - timedelta(days=days - 1)
        removed = 0
        for path in self.directory.glob("oes-base-????-??-??.jsonl"):
            try:
                day = datetime.strptime(path.stem.removeprefix("oes-base-"), "%Y-%m-%d").date()
                if day < cutoff and path.is_file() and not is_link(path) and path.resolve().parent == self.directory:
                    path.unlink()
                    removed += 1
            except (OSError, ValueError):
                self.write_errors += 1
        self.emit("log_retention_completed", retention_days=days, log_files_deleted=removed)
        return removed


def emit_event(args, event: str, **values) -> None:
    logger = getattr(args, "event_log", None)
    if logger is not None:
        logger.emit(event, **values)
