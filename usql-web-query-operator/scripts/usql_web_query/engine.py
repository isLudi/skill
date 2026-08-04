"""Query engine selector operations with stable label verification."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Any

from _shared.errors import UsageError

from .config import DEFAULT_QUERY_ENGINE
from .page_helpers import get_sql_frame


QUERY_ENGINE_CHOICES = ("presto", "presto-lakehouse", "doris-presto")


@dataclass(frozen=True)
class EngineSelectionEvidence:
    requested: str
    selected_key: str
    selected_label: str
    stable_reads: int

    def to_summary(self) -> dict[str, Any]:
        return {
            "requested": self.requested,
            "selected_key": self.selected_key,
            "selected_label": self.selected_label,
            "stable_reads": self.stable_reads,
        }


def normalize_query_engine(engine: str | None) -> str:
    normalized = (engine or DEFAULT_QUERY_ENGINE).strip().lower().replace("_", "-")
    if normalized not in QUERY_ENGINE_CHOICES:
        raise UsageError(f"Unsupported query engine: {engine}")
    return normalized


def get_query_engine_selector(page: Any) -> Any:
    frame = get_sql_frame(page)
    selector = frame.locator(".antd-pro-src-components-editor-index-changeModeBox .ant-select-selector").first
    selector.wait_for(state="visible", timeout=15_000)
    return selector


def get_query_engine_label(page: Any) -> str:
    try:
        text = get_query_engine_selector(page).inner_text(timeout=5000)
        return " ".join(text.split())
    except Exception:
        return ""


def engine_label_matches(engine: str, label: str) -> bool:
    normalized = normalize_query_engine(engine)
    compact = re.sub(r"[\s_-]+", "", (label or "").strip().lower())
    if normalized == "presto":
        return compact == "presto"
    if normalized == "presto-lakehouse":
        return compact == "prestolakehouse"
    return "dorispresto" in compact or "doris内测加速版" in compact


def recognize_engine_value(value: str | None) -> str | None:
    compact = re.sub(r"[\s_-]+", "", (value or "").strip().lower())
    if not compact:
        return None
    if "doris" in compact:
        return "doris-presto"
    if "lakehouse" in compact:
        return "presto-lakehouse"
    if "presto" in compact:
        return "presto"
    return None


def _click_engine_menu_item(page: Any, pattern: str) -> None:
    frame = get_sql_frame(page)
    locator = frame.locator(".ant-cascader-menu-item").filter(
        has_text=re.compile(pattern, flags=re.I)
    ).last
    if locator.count() == 0:
        raise UsageError(f"Could not find engine menu item matching {pattern!r}.")
    locator.click(timeout=5000)


def _wait_for_stable_engine_label(
    page: Any,
    engine: str,
    *,
    timeout_ms: int,
    stable_reads_required: int,
) -> EngineSelectionEvidence:
    deadline = time.monotonic() + max(timeout_ms, 0) / 1000
    stable_reads = 0
    previous = ""
    while True:
        label = get_query_engine_label(page)
        if label == previous and engine_label_matches(engine, label):
            stable_reads += 1
        elif engine_label_matches(engine, label):
            stable_reads = 1
        else:
            stable_reads = 0
        previous = label
        if stable_reads >= max(stable_reads_required, 1):
            canonical = normalize_query_engine(engine)
            return EngineSelectionEvidence(
                requested=engine,
                selected_key=canonical,
                selected_label=label,
                stable_reads=stable_reads,
            )
        if time.monotonic() >= deadline:
            raise UsageError(
                f"Engine selection did not stabilize for {engine}: {label or '<empty>'}"
            )
        page.wait_for_timeout(200)


def switch_query_engine(
    page: Any,
    engine: str,
    *,
    timeout_ms: int = 10_000,
    stable_reads_required: int = 2,
) -> EngineSelectionEvidence:
    """Switch engine and require a stable exact/family label before SQL submission."""
    normalized = normalize_query_engine(engine)
    current_label = get_query_engine_label(page)
    if not engine_label_matches(normalized, current_label):
        selector = get_query_engine_selector(page)
        selector.click(timeout=5000)
        page.wait_for_timeout(250)
        if normalized == "presto":
            _click_engine_menu_item(page, r"^Presto$")
        elif normalized == "presto-lakehouse":
            _click_engine_menu_item(page, r"^Presto[_-]lakehouse$")
        else:
            _click_engine_menu_item(page, r"^Doris-Presto$")
            page.wait_for_timeout(250)
            _click_engine_menu_item(page, r"^doris内测加速版$")
    return _wait_for_stable_engine_label(
        page,
        normalized,
        timeout_ms=timeout_ms,
        stable_reads_required=stable_reads_required,
    )
