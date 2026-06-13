"""Single-dashboard period filtering and focused screenshot capture."""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any

from _shared.debug import save_debug_artifacts
from _shared.errors import UsageError

from .common import write_json
from .profile import dashboard_url, extract_component_units, fetch_dashboard_config, parse_dashboard_html


PERIOD_LABEL = "\u671f\u6b21"
PERIOD_SUFFIX = "\u671f"
FILTER_BOX_SELECTOR = ".g-filter-item-box-global"
SELECTOR_BOX_SELECTOR = ".big-data-select-selector"
DROPDOWN_SELECTOR = ".big-data-select-dropdown"
GRID_LAYOUT_SELECTOR = ".react-grid-layout"


def normalize_period(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise UsageError("Period is required. Pass --period 20260612 or --period 20260612期.")
    return text if text.endswith(PERIOD_SUFFIX) else f"{text}{PERIOD_SUFFIX}"


def period_slug(value: str) -> str:
    digits = re.sub(r"\D", "", normalize_period(value))
    return digits or "period"


def wait_for_dashboard_shell(page: Any, wait_ms: int) -> None:
    page.locator(GRID_LAYOUT_SELECTOR).first.wait_for(state="visible", timeout=45_000)
    page.wait_for_timeout(wait_ms)


def _visible_bbox(locator: Any) -> dict[str, float] | None:
    try:
        count = locator.count()
    except Exception:  # noqa: BLE001
        return None
    for index in range(count):
        try:
            box = locator.nth(index).bounding_box()
        except Exception:  # noqa: BLE001
            continue
        if box and box.get("width", 0) > 0 and box.get("height", 0) > 0:
            return box
    return None


def _union_bbox(boxes: list[dict[str, float]], page: Any, padding: int = 12) -> dict[str, float]:
    if not boxes:
        raise UsageError("No capture region was found on the dashboard page.")
    viewport = page.viewport_size or {"width": 1600, "height": 1000}
    min_x = max(0.0, min(box["x"] for box in boxes) - padding)
    min_y = max(0.0, min(box["y"] for box in boxes) - padding)
    max_x = min(float(viewport["width"]), max(box["x"] + box["width"] for box in boxes) + padding)
    max_y = min(float(viewport["height"]), max(box["y"] + box["height"] for box in boxes) + padding)
    return {
        "x": min_x,
        "y": min_y,
        "width": max_x - min_x,
        "height": max_y - min_y,
    }


def _find_period_filter_box(page: Any) -> Any:
    boxes = page.locator(FILTER_BOX_SELECTOR)
    count = boxes.count()
    for index in range(count):
        candidate = boxes.nth(index)
        try:
            text = candidate.inner_text(timeout=2_000)
        except Exception:  # noqa: BLE001
            continue
        if PERIOD_LABEL in text:
            return candidate
    raise UsageError("The dashboard does not expose a visible 期次 filter box.")


def _selected_periods_from_dropdown(dropdown: Any) -> list[str]:
    return [
        str(value or "").strip()
        for value in dropdown.locator(".big-data-select-tree-treenode-checkbox-checked [title]").evaluate_all(
            "nodes => nodes.map(node => node.getAttribute('title') || node.textContent || '')"
        )
        if str(value or "").strip()
    ]


def _selected_period_display(selector: Any) -> str:
    return str(selector.inner_text(timeout=5_000) or "").strip()


def apply_period_filter(page: Any, period: str, wait_ms: int) -> dict[str, Any]:
    normalized_period = normalize_period(period)
    filter_box = _find_period_filter_box(page)
    selector = filter_box.locator(SELECTOR_BOX_SELECTOR).first
    before_display = _selected_period_display(selector)
    if normalized_period in before_display and "+" not in before_display and "..." not in before_display:
        return {
            "filter_label": PERIOD_LABEL,
            "period": normalized_period,
            "before_display": before_display,
            "after_display": before_display,
            "changed": False,
        }

    selector.click()
    dropdown = page.locator(DROPDOWN_SELECTOR).last
    dropdown.wait_for(state="visible", timeout=10_000)

    checked_values = _selected_periods_from_dropdown(dropdown)
    for value in checked_values:
        if value != normalized_period:
            dropdown.locator(f"[title='{value}']").first.click()
            page.wait_for_timeout(300)

    checked_values = _selected_periods_from_dropdown(dropdown)
    if normalized_period not in checked_values:
        search = dropdown.locator("input.big-data-input").first
        if search.count():
            search.fill(normalized_period)
            page.wait_for_timeout(250)
        target = dropdown.locator(f"[title='{normalized_period}']").first
        if target.count() == 0:
            raise UsageError(f"Requested period was not found in the filter dropdown: {normalized_period}")
        target.click()
        page.wait_for_timeout(300)

    viewport = page.viewport_size or {"width": 1600, "height": 1000}
    page.mouse.click(max(40, viewport["width"] - 120), 150)
    try:
        dropdown.wait_for(state="hidden", timeout=5_000)
    except Exception:  # noqa: BLE001
        pass
    page.wait_for_timeout(wait_ms)

    after_display = _selected_period_display(selector)
    if normalized_period not in after_display:
        raise UsageError(
            f"Period filter did not update to {normalized_period}. Current selection text: {after_display or '<empty>'}"
        )
    if "+" in after_display or "..." in after_display:
        raise UsageError(f"Period filter still has multiple selections: {after_display}")

    return {
        "filter_label": PERIOD_LABEL,
        "period": normalized_period,
        "before_display": before_display,
        "after_display": after_display,
        "changed": before_display != after_display,
    }


def inspect_dashboard_structure(page: Any, dashboard_id: str) -> dict[str, Any]:
    config = fetch_dashboard_config(page, dashboard_id)
    component_units = extract_component_units(parse_dashboard_html(config))
    title_units = [
        str(component["unit_id"])
        for component in component_units
        if str(component.get("component_type") or "") == "u_material"
    ]
    analytic_units = [
        str(component["unit_id"])
        for component in component_units
        if str(component.get("component_type") or "") not in {"u_material", "public_filter_relation"}
    ]
    public_filter_units = [
        str(component["unit_id"])
        for component in component_units
        if str(component.get("component_type") or "") == "public_filter_relation"
    ]
    return {
        "dashboard_name": str(config.get("dashboardName") or dashboard_id),
        "component_count": len(component_units),
        "components": component_units,
        "title_unit_ids": title_units,
        "analytic_unit_ids": analytic_units,
        "public_filter_unit_ids": public_filter_units,
        "primary_title_unit_id": title_units[0] if title_units else None,
        "primary_analytic_unit_id": analytic_units[0] if analytic_units else None,
    }


def capture_core_region(
    page: Any,
    output_path: Path,
    filter_box: Any,
    structure: dict[str, Any],
) -> dict[str, Any]:
    boxes: list[dict[str, float]] = []
    title_unit_id = structure.get("primary_title_unit_id")
    table_unit_id = structure.get("primary_analytic_unit_id")
    grid_box = _visible_bbox(page.locator(GRID_LAYOUT_SELECTOR))
    if grid_box:
        boxes.append(grid_box)

    if title_unit_id:
        title_box = _visible_bbox(page.locator(f"#{title_unit_id}"))
        if title_box:
            boxes.append(title_box)
    filter_box_rect = _visible_bbox(filter_box)
    if filter_box_rect:
        boxes.append(filter_box_rect)
    if table_unit_id:
        table_box = _visible_bbox(page.locator(f"#{table_unit_id}"))
        if table_box:
            boxes.append(table_box)

    if not boxes:
        raise UsageError("Could not derive a focused screenshot region from the dashboard page.")

    clip = _union_bbox(boxes, page)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(output_path), clip=clip, scale="device")
    return {
        "screenshot_path": str(output_path),
        "clip": clip,
        "title_unit_id": title_unit_id,
        "table_unit_id": table_unit_id,
    }


def capture_dashboard_period(
    page: Any,
    dashboard_id: str,
    dashboard_name: str | None,
    folder_name: str | None,
    period: str,
    wait_ms: int,
    apply_wait_ms: int,
    output_dir: Path,
    debug_artifacts: bool,
) -> dict[str, Any]:
    normalized_period = normalize_period(period)
    output_dir.mkdir(parents=True, exist_ok=True)
    opened_url = dashboard_url(dashboard_id)
    page.goto(opened_url, wait_until="domcontentloaded", timeout=45_000)
    wait_for_dashboard_shell(page, wait_ms)
    if debug_artifacts:
        save_debug_artifacts(page, output_dir, "capture_before_filter")

    structure = inspect_dashboard_structure(page, dashboard_id)
    filter_result = apply_period_filter(page, normalized_period, apply_wait_ms)
    if debug_artifacts:
        save_debug_artifacts(page, output_dir, "capture_after_filter")

    screenshot_path = output_dir / f"{dashboard_id}_{period_slug(normalized_period)}.png"
    capture_result = capture_core_region(
        page=page,
        output_path=screenshot_path,
        filter_box=_find_period_filter_box(page),
        structure=structure,
    )

    result = {
        "ok": True,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source_folder": folder_name,
        "dashboard_id": dashboard_id,
        "dashboard_name": dashboard_name or structure.get("dashboard_name") or dashboard_id,
        "open_url": opened_url,
        "loaded_url": page.url,
        "page_title": page.title(),
        "period": normalized_period,
        "period_filter": filter_result,
        "structure_summary": {
            "component_count": structure["component_count"],
            "title_unit_ids": structure["title_unit_ids"],
            "analytic_unit_ids": structure["analytic_unit_ids"],
            "public_filter_unit_ids": structure["public_filter_unit_ids"],
        },
        "capture": capture_result,
        "output_dir": str(output_dir),
    }
    write_json(result, output_dir / "capture_summary.json")
    write_json(structure, output_dir / "structure_summary.json")
    return result
