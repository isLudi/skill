"""Optional pacing for the serialized local push Tiangong reader only."""
from __future__ import annotations

import os
from datetime import datetime, timezone
import json
from pathlib import Path
import threading
import time
import uuid

_lock = threading.Lock()
_last_start = None
MINIMUM_INTERVAL_SECONDS = 1.2


def request_options() -> dict:
    # Redirects can issue additional requests that would bypass pacing.
    return {"max_redirects": 0, "max_retries": 0} if os.environ.get("CODEX_PUSH_GUARDED_PLATFORM") == "1" else {}


def signal_cooldown(status) -> None:
    """Persist a rate-limit verdict before the worker releases the global lock."""
    if os.environ.get("CODEX_PUSH_GUARDED_PLATFORM") != "1" or status not in (429, 503):
        return
    root = os.environ.get("CODEX_PUSH_COORDINATOR_ROOT")
    if not root:
        raise RuntimeError("Guarded platform coordinator root is missing")
    folder = Path(root)
    folder.mkdir(parents=True, exist_ok=True)
    now = time.time()
    temporary = folder / ("cooldown." + uuid.uuid4().hex + ".tmp")
    try:
        temporary.write_text(json.dumps({"created_at": now, "until": now + 120}), encoding="utf-8")
        temporary.replace(folder / "cooldown.json")
    finally:
        temporary.unlink(missing_ok=True)


def before_request(label: str = "") -> None:
    if os.environ.get("CODEX_PUSH_GUARDED_PLATFORM") != "1":
        return
    global _last_start
    with _lock:
        if _last_start is None:
            time.sleep(MINIMUM_INTERVAL_SECONDS)
        else:
            remaining = MINIMUM_INTERVAL_SECONDS - (time.monotonic() - _last_start)
            if remaining > 0:
                time.sleep(remaining)
        trace_root = os.environ.get("CODEX_PUSH_PLATFORM_TRACE_ROOT")
        if trace_root:
            try:
                at = datetime.now(timezone.utc)
                folder = Path(trace_root)
                folder.mkdir(parents=True, exist_ok=True)
                with (folder / (at.strftime("%Y-%m-%d") + ".jsonl")).open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps({"at_utc": at.isoformat(), "event": "request_start",
                                             "endpoint": label}, ensure_ascii=True) + "\n")
            except OSError:
                pass  # Diagnostic logging must not create a second network attempt.
        _last_start = time.monotonic()
