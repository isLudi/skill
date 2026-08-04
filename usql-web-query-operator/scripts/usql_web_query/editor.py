"""CodeMirror SQL editor operations with deterministic readback."""

from __future__ import annotations

import base64
import hashlib
import time
from dataclasses import dataclass
from typing import Any

from _shared.errors import UsageError

from .page_helpers import get_sql_frame


SQL_FRAME_PREFIX = "https://uanalysis.baijia.com/sql/"


@dataclass(frozen=True)
class EditorWriteEvidence:
    sql_sha256: str
    byte_length: int
    stable_reads: int

    def to_summary(self) -> dict[str, Any]:
        return {
            "sql_sha256": self.sql_sha256,
            "byte_length": self.byte_length,
            "stable_reads": self.stable_reads,
        }


def sql_text_sha256(sql: str) -> str:
    return hashlib.sha256(sql.encode("utf-8")).hexdigest()


def _sql_frames(page: Any) -> list[Any]:
    return [
        frame
        for frame in getattr(page, "frames", [])
        if str(getattr(frame, "url", "")).startswith(SQL_FRAME_PREFIX)
    ]


def get_editor_sql(page: Any) -> str | None:
    for frame in _sql_frames(page):
        try:
            value = frame.evaluate(
                """() => {
                    const cmEl = document.querySelector('.CodeMirror');
                    return cmEl && cmEl.CodeMirror ? cmEl.CodeMirror.getValue() : null;
                }"""
            )
        except Exception:
            continue
        if isinstance(value, str):
            return value
    return None


def _set_editor_value(page: Any, sql_b64: str) -> bool:
    for frame in _sql_frames(page):
        try:
            changed = frame.evaluate(
                """sqlB64 => {
                    const bytes = Uint8Array.from(atob(sqlB64), ch => ch.charCodeAt(0));
                    const sql = new TextDecoder('utf-8').decode(bytes);
                    const cmEl = document.querySelector('.CodeMirror');
                    if (!cmEl || !cmEl.CodeMirror) return false;
                    const cm = cmEl.CodeMirror;
                    cm.focus();
                    cm.setValue(sql);
                    if (typeof cm.save === 'function') cm.save();
                    const input = typeof cm.getInputField === 'function' ? cm.getInputField() : null;
                    if (input) {
                        input.dispatchEvent(new Event('input', {bubbles: true}));
                        input.dispatchEvent(new Event('change', {bubbles: true}));
                    }
                    cm.execCommand('selectAll');
                    return true;
                }""",
                sql_b64,
            )
        except Exception:
            continue
        if changed:
            return True
    return False


def _fallback_type_sql(page: Any, sql: str) -> None:
    frame = get_sql_frame(page)
    editor = frame.locator(".CodeMirror").last
    editor.click(timeout=10_000)
    page.keyboard.press("Control+A")
    page.keyboard.insert_text(sql)
    page.keyboard.press("Control+A")


def set_monaco_sql(
    page: Any,
    sql: str,
    *,
    timeout_ms: int = 10_000,
    stable_reads_required: int = 2,
) -> EditorWriteEvidence:
    """Set SQL and require exact, stable CodeMirror readback before submission."""
    expected_sha256 = sql_text_sha256(sql)
    sql_b64 = base64.b64encode(sql.encode("utf-8")).decode("ascii")
    if not _set_editor_value(page, sql_b64):
        _fallback_type_sql(page, sql)

    deadline = time.monotonic() + max(timeout_ms, 0) / 1000
    stable_reads = 0
    latest: str | None = None
    while True:
        latest = get_editor_sql(page)
        if latest == sql:
            stable_reads += 1
            if stable_reads >= max(stable_reads_required, 1):
                return EditorWriteEvidence(
                    sql_sha256=expected_sha256,
                    byte_length=len(sql.encode("utf-8")),
                    stable_reads=stable_reads,
                )
        else:
            stable_reads = 0
        if time.monotonic() >= deadline:
            actual_sha256 = sql_text_sha256(latest) if isinstance(latest, str) else None
            raise UsageError(
                "SQL editor readback did not stabilize at the submitted SQL hash: "
                f"expected={expected_sha256}, actual={actual_sha256 or '<unavailable>'}"
            )
        page.wait_for_timeout(100)
