"""Monaco SQL editor operations."""

from __future__ import annotations

from typing import Any

from .page_helpers import get_sql_frame


def set_monaco_sql(page: Any, sql: str) -> None:
    """Set SQL text in the CodeMirror editor inside the /sql/ iframe and select all.

    The platform requires SQL text to be selected (highlighted) before execution,
    otherwise it shows "请选中执行的sql！" (Please select the SQL to execute).
    """
    frame = get_sql_frame(page)

    # Method 1: use CodeMirror API via evaluate on the iframe.
    for frame_obj in page.frames:
        if frame_obj.url.startswith("https://uanalysis.baijia.com/sql/"):
            set_result = frame_obj.evaluate(
                """sql => {
                    const cmEl = document.querySelector('.CodeMirror');
                    if (cmEl && cmEl.CodeMirror) {
                        const cm = cmEl.CodeMirror;
                        cm.setValue(sql);
                        // Select all text — required by the platform before execution.
                        cm.execCommand('selectAll');
                        return true;
                    }
                    return false;
                }""",
                sql,
            )
            if set_result:
                return
            break

    # Method 2: click the CodeMirror editor, paste, and select all.
    editor = frame.locator(".CodeMirror").last
    editor.click(timeout=10_000)
    page.keyboard.press("Control+A")
    page.keyboard.insert_text(sql)
    page.keyboard.press("Control+A")
