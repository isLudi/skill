"""Append-only external run logs for the local broadcaster.

The broadcaster previously kept no historical record: ``emit`` wrote a single
``live-status.json`` inside the state directory and deleted it in a ``finally``,
and every ``run_*.ps1`` piped the process output to ``Out-Null``. A silent skip
or a blocked retry loop therefore left nothing behind, and the four 2026-09-28
silences could not be explained after the fact.

Two rules govern this module:

1. **Logging never breaks delivery.** Every write is best effort. A missing or
   unwritable log root degrades to a single loud stdout warning and the run
   continues; no exception from here may reach the caller.
2. **Logs never live on the system drive.** The root comes from the
   machine-local ``paths.push_log_root``, which points at a data drive.

Layout (``<root>`` = ``paths.push_log_root``)::

    <root>/market_consultant/<channel_id>/<YYYY-MM-DD>/<HHMMSS>-<task>.jsonl
    <root>/market_consultant/<channel_id>/<YYYY-MM-DD>/<HHMMSS>-<task>.result.json
    <root>/_index/runs.jsonl

The ``.jsonl`` file is the full ordered event stream of one process run (all
retries of one slot included). The ``.result.json`` is the one-line-per-channel
verdict written once at exit. ``_index/runs.jsonl`` appends the same verdict
summary for every run, so a single ``grep`` over one file answers "which slots
failed today, in which channel, and why".
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sys
from typing import Any

from ..paths import WORKSPACE_ROOT

TZ = timezone(timedelta(hours=8))
MACHINE_LOCAL = WORKSPACE_ROOT / "machine.local.json"
DEPARTMENT = "market_consultant"
RETENTION_DAYS = 30

# Verdicts that mean "this run needs no follow-up". Everything else is surfaced
# in ``needs_attention`` so a blocked channel is never mistaken for a delivered one.
# `sent_unverifiable` (resend.UNVERIFIABLE) means the write was acknowledged but this
# group's content cannot be read back at all, so verification is impossible by policy.
# It is clean: the group is receiving its reports, and reporting a failure every push
# would be a false alarm. Only groups declared or probed as unreadable produce it.
CLEAN_STATUSES = frozenset({
    "sent_verified", "sent_unverified", "sent_unverifiable", "skipped_no_eligible_rows",
    "skipped_no_source_rows", "prepared",
})

# Event field carried by run_slot's per-channel verdicts; the summary collects
# the last one seen for each channel.
OUTCOME_EVENT = "channel_outcome"

_warned = False


def _warn(detail: str) -> None:
    """Report a logging failure once, on stdout; never raise."""
    global _warned
    if _warned:
        return
    _warned = True
    print(json.dumps({"at": None, "event": "push_log_unavailable", "reason": detail[:400]},
                     ensure_ascii=False), flush=True)


def log_root() -> Path:
    """Return the configured external log root.

    Raises ``ValueError`` when unset, which the callers below turn into a
    degraded no-file run rather than a failed push.
    """
    configured = json.loads(MACHINE_LOCAL.read_text(encoding="utf-8"))
    value = (configured.get("paths") or {}).get("push_log_root")
    if not isinstance(value, str) or not value.strip():
        raise ValueError("machine.local.json paths.push_log_root is not configured")
    root = Path(value)
    if not root.is_absolute():
        raise ValueError("machine.local.json paths.push_log_root must be absolute")
    return root


def _write_atomic(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n",
                         encoding="utf-8")
    os.replace(temporary, path)


def _prune(root: Path, today: str) -> None:
    """Drop day directories older than the retention window; best effort."""
    from datetime import date, timedelta

    cutoff = date.fromisoformat(today) - timedelta(days=RETENTION_DAYS)
    base = root / DEPARTMENT
    if not base.is_dir():
        return
    for channel_dir in base.iterdir():
        if not channel_dir.is_dir():
            continue
        for day_dir in channel_dir.iterdir():
            if not day_dir.is_dir():
                continue
            try:
                day = date.fromisoformat(day_dir.name)
            except ValueError:
                continue
            if day >= cutoff:
                continue
            for stale in day_dir.iterdir():
                if stale.is_file() and (stale.suffix in {".jsonl", ".json"} or stale.name.endswith(".tmp")):
                    stale.unlink(missing_ok=True)
            try:
                day_dir.rmdir()
            except OSError:
                pass


class RunLog:
    """One file per process run, plus a durable per-channel verdict summary."""

    def __init__(self, channel_id: str, task_name: str, started_at,
                 department: str = DEPARTMENT) -> None:
        self.root = log_root()
        day = started_at.strftime("%Y-%m-%d")
        stamp = started_at.strftime("%H%M%S")
        stem = "%s-%s" % (stamp, task_name)
        self.department = department
        self.directory = self.root / department / channel_id / day
        self.directory.mkdir(parents=True, exist_ok=True)
        self.stream_path = self.directory / (stem + ".jsonl")
        self.result_path = self.directory / (stem + ".result.json")
        self.process_path = self.directory / (stem + "-process.log")
        self.index_path = self.root / "_index" / "runs.jsonl"
        self.stream_path.parent.mkdir(parents=True, exist_ok=True)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.channel_id = channel_id
        self.task_name = task_name
        self.started_at = started_at
        self.slot: str | None = None
        self.last_event: str | None = None
        self.outcomes: dict[str, dict[str, Any]] = {}
        _prune(self.root, day)

    def event(self, payload: dict[str, Any]) -> None:
        if isinstance(payload.get("slot"), str):
            self.slot = payload["slot"]
        name = payload.get("event")
        self.last_event = name if isinstance(name, str) else self.last_event
        if name == OUTCOME_EVENT and isinstance(payload.get("channel"), str):
            self.outcomes[payload["channel"]] = {
                "status": payload.get("status"),
                "reason": payload.get("reason"),
                "message_id": payload.get("message_id"),
            }
        with self.stream_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")

    def finish(self, exit_code: int, finished_at,
               outcomes: dict[str, dict[str, Any]] | None = None) -> None:
        """Persist the run verdict. Summary only: never the full event stream."""
        verdicts = self.outcomes if outcomes is None else outcomes
        summary = {
            "department": self.department,
            "channel_id": self.channel_id,
            "task_name": self.task_name,
            "slot": self.slot,
            "started_at": self.started_at.isoformat(),
            "finished_at": finished_at.isoformat() if finished_at is not None else None,
            "exit_code": exit_code,
            "last_event": self.last_event,
            "channels": self.outcomes,
            "outcomes": verdicts,
            "needs_attention": sorted(key for key, value in verdicts.items()
                                      if value.get("status") not in CLEAN_STATUSES),
        }
        _write_atomic(self.result_path, summary)
        with self.index_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(summary, ensure_ascii=False, default=str) + "\n")


def open_run_log(channel_id: str, task_name: str, started_at,
                 department: str = DEPARTMENT) -> RunLog | None:
    """Build a run log, or ``None`` when logging is unavailable (never raises)."""
    try:
        return RunLog(channel_id, task_name, started_at, department)
    except Exception as exc:  # noqa: BLE001 - logging must never break a push
        _warn("%s: %s" % (type(exc).__name__, exc))
        return None


def iter_outcomes(result: Any) -> list[tuple[str, str, str]]:
    """Flatten a Qingcheng batch result into (key, status, reason) verdicts.

    Covers both shapes the local runners return: process/special report a
    ``channels`` map of ``{level: {"status": ...}}``, SEC reports a flat
    ``reports`` map.
    """
    verdicts: list[tuple[str, str, str]] = []
    if not isinstance(result, dict):
        return verdicts
    for channel, item in (result.get("channels") or {}).items():
        if not isinstance(item, dict):
            continue
        groups = item.get("groups")
        if groups is None:
            # The special-channel batch reports one flat status per channel.
            verdicts.append((str(channel), item.get("status", "unknown"),
                             str(item.get("error") or item.get("receipt") or "")[:400]))
            continue
        for level, group in groups.items():
            group = group or {}
            verdicts.append(("%s/%s" % (channel, level), group.get("status", "unknown"),
                             str(group.get("error") or "")[:400]))
    for report, item in (result.get("reports") or {}).items():
        item = item or {}
        reason = item.get("error") or item.get("receipt") or ""
        verdicts.append((str(report), item.get("status", "unknown"), str(reason)[:400]))
    return verdicts


class _Tee:
    """Mirror a text stream into the run's process log, then pass it through."""

    def __init__(self, stream, handle) -> None:
        self._stream = stream
        self._handle = handle

    def write(self, data):
        try:
            self._handle.write(data)
            self._handle.flush()
        except Exception:  # noqa: BLE001
            pass
        return self._stream.write(data)

    def flush(self):
        try:
            self._handle.flush()
        except Exception:  # noqa: BLE001
            pass
        self._stream.flush()

    def __getattr__(self, name):
        return getattr(self._stream, name)


class RunScope:
    """One scheduled run's event stream, process log and final verdict.

    Lets a runner that Task Scheduler invokes directly (no PowerShell wrapper)
    capture its own stdout/stderr, which is where crashes and argparse errors
    otherwise disappear to.
    """

    def __init__(self, log: RunLog | None) -> None:
        self.log = log
        self.exit_code = 1
        self.outcomes: dict[str, dict[str, Any]] = {}

    def event(self, name: str, **fields: Any) -> None:
        if self.log is None:
            return
        try:
            self.log.event({"at": self.log.started_at.isoformat(), "event": name, **fields})
        except Exception:  # noqa: BLE001
            pass

    def outcome(self, key: str, status: str, reason: str = "", **extra: Any) -> None:
        self.outcomes[key] = {"status": status, "reason": reason}
        self.event("outcome", key=key, status=status, reason=reason, **extra)

    def adopt(self, result: Any) -> None:
        """Record one verdict per channel/level (or per report) from a batch result."""
        for key, status, reason in iter_outcomes(result):
            self.outcome(key, status, reason)

    def finish(self) -> None:
        if self.log is None:
            return
        try:
            self.log.finish(self.exit_code, datetime.now(TZ), self.outcomes)
        except Exception:  # noqa: BLE001
            pass


@contextmanager
def run_scope(department: str, channel_id: str, task_name: str, started_at=None):
    """Open the external run log and mirror stdout/stderr into it.

    Logging is best effort throughout: without a usable log root the scope is a
    no-op and the push proceeds exactly as before.
    """
    log = open_run_log(channel_id, task_name, started_at or datetime.now(TZ), department)
    scope = RunScope(log)
    original_out, original_err = sys.stdout, sys.stderr
    handle = None
    try:
        if log is not None:
            try:
                handle = log.process_path.open("a", encoding="utf-8")
                sys.stdout = _Tee(original_out, handle)
                sys.stderr = _Tee(original_err, handle)
            except Exception as exc:  # noqa: BLE001
                _warn("%s: %s" % (type(exc).__name__, exc))
        yield scope
    finally:
        if handle is not None:
            sys.stdout, sys.stderr = original_out, original_err
            try:
                handle.close()
            except Exception:  # noqa: BLE001
                pass
        scope.finish()
