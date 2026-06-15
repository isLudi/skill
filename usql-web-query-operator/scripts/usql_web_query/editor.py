"""Monaco SQL editor operations."""

from __future__ import annotations

import base64
from typing import Any

from .page_helpers import get_sql_frame


def set_monaco_sql(page: Any, sql: str) -> None:
    """Set SQL text in the CodeMirror editor inside the /sql/ iframe and select all.

    The platform requires SQL text to be selected before execution.
    """
    frame = get_sql_frame(page)

    # Preserve UTF-8 exactly by shipping ASCII-safe base64 into the page and
    # decoding it in the browser.
    sql_b64 = base64.b64encode(sql.encode("utf-8")).decode("ascii")

    for frame_obj in page.frames:
        if not frame_obj.url.startswith("https://uanalysis.baijia.com/sql/"):
            continue
        set_result = frame_obj.evaluate(
            """sqlB64 => {
                const bytes = Uint8Array.from(atob(sqlB64), ch => ch.charCodeAt(0));
                const sql = new TextDecoder('utf-8').decode(bytes);
                const cmEl = document.querySelector('.CodeMirror');
                if (cmEl && cmEl.CodeMirror) {
                    const cm = cmEl.CodeMirror;
                    cm.setValue(sql);
                    cm.execCommand('selectAll');
                    return true;
                }
                return false;
            }""",
            sql_b64,
        )
        if set_result:
            return
        break

    editor = frame.locator(".CodeMirror").last
    editor.click(timeout=10_000)
    page.keyboard.press("Control+A")
    page.keyboard.insert_text(sql)
    page.keyboard.press("Control+A")
