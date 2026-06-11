"""Query engine selector operations."""

from __future__ import annotations

import re
from typing import Any

from _shared.errors import UsageError

from .config import DEFAULT_QUERY_ENGINE
from .page_helpers import get_sql_frame


def get_query_engine_selector(page: Any) -> Any:
    frame = get_sql_frame(page)
    selector = frame.locator(".antd-pro-src-components-editor-index-changeModeBox .ant-select-selector").first
    selector.wait_for(state="visible", timeout=15_000)
    return selector

def get_query_engine_label(page: Any) -> str:
    try:
        text = get_query_engine_selector(page).inner_text(timeout=5000)
        return text.strip()
    except Exception:
        return ""

def _click_engine_menu_item(page: Any, pattern: str) -> None:
    frame = get_sql_frame(page)
    locator = frame.locator(".ant-cascader-menu-item").filter(has_text=re.compile(pattern)).last
    if locator.count() == 0:
        raise UsageError(f"Could not find engine menu item matching {pattern!r}.")
    locator.click(timeout=5000)

def switch_query_engine(page: Any, engine: str) -> str:
    """Switch the SQL query engine before writing SQL into the editor."""
    normalized = (engine or DEFAULT_QUERY_ENGINE).strip().lower()
    if normalized not in {"presto", "doris-presto"}:
        raise UsageError(f"Unsupported query engine: {engine}")

    selector = get_query_engine_selector(page)
    selector.click(timeout=5000)
    page.wait_for_timeout(500)

    if normalized == "presto":
        _click_engine_menu_item(page, r"^Presto$")
    else:
        _click_engine_menu_item(page, r"^Doris-Presto$")
        page.wait_for_timeout(400)
        _click_engine_menu_item(page, r"^doris内测加速版$")

    page.wait_for_timeout(1200)
    selected_label = get_query_engine_label(page)
    if normalized == "presto":
        if selected_label != "Presto":
            raise UsageError(f"Expected Presto after engine switch, got: {selected_label or '<empty>'}")
    else:
        if selected_label == "Presto":
            raise UsageError("Engine switch to Doris-Presto did not take effect; selector still shows Presto.")
    return selected_label
