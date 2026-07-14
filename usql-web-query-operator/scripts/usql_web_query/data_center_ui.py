"""Shared UI and synchronization primitives for Data Center write workflows."""

from __future__ import annotations

import base64
import json
import re
import time
from datetime import date, datetime
from typing import Any

from _shared.config import DATA_CENTER_DATASET_URL
from _shared.errors import UsageError

from .data_center import DataCenterClient, DataCenterFolder, DataCenterScheduleRun
from .data_center_replacement import canonical_sql_text, sql_sha256


SUCCESS_STATUSES = {"SUCCESS"}
FAILURE_STATUSES = {"FAIL", "FAILED", "ERROR", "CANCELLED", "CANCELED"}


def get_codemirror_sql(editor: Any) -> str:
    value = editor.evaluate("el => el.CodeMirror && el.CodeMirror.getValue()")
    if not isinstance(value, str):
        raise UsageError("Data Center CodeMirror value is unavailable")
    return canonical_sql_text(value)


def wait_for_editor_sql_hash(
    *,
    page: Any,
    editor: Any,
    expected_sha256: str,
    timeout_ms: int,
) -> str:
    deadline = time.monotonic() + timeout_ms / 1000
    latest = get_codemirror_sql(editor)
    while time.monotonic() < deadline:
        latest = get_codemirror_sql(editor)
        if sql_sha256(latest) == expected_sha256:
            return latest
        page.wait_for_timeout(250)
    return latest


def set_codemirror_sql(editor: Any, sql: str) -> None:
    encoded = base64.b64encode(sql.encode("utf-8")).decode("ascii")
    changed = editor.evaluate(
        """(el, sqlB64) => {
            if (!el.CodeMirror) return false;
            const bytes = Uint8Array.from(atob(sqlB64), ch => ch.charCodeAt(0));
            const sql = new TextDecoder('utf-8').decode(bytes);
            el.CodeMirror.setValue(sql);
            el.CodeMirror.execCommand('selectAll');
            return true;
        }""",
        encoded,
    )
    if not changed:
        raise UsageError("Data Center CodeMirror replacement failed")


def click_optional_save_confirmation(page: Any) -> bool:
    dialog = page.locator('.ant-modal:visible, [role="dialog"]:visible').last
    try:
        dialog.wait_for(state="visible", timeout=3_000)
    except Exception:
        return False
    confirm = dialog.locator("button").filter(
        has_text=re.compile(r"^\s*(?:确\s*认|确\s*定)\s*$")
    ).last
    if confirm.count() == 0:
        return False
    confirm.wait_for(state="visible", timeout=3_000)
    confirm.click()
    return True


def visible_save_debug(page: Any) -> dict[str, Any]:
    try:
        dialogs = page.locator('.ant-modal:visible, [role="dialog"]:visible').all_inner_texts()
    except Exception:
        dialogs = []
    try:
        buttons = page.locator("button:visible").all_inner_texts()
    except Exception:
        buttons = []
    return {
        "dialogs": [text.strip()[:500] for text in dialogs[:5]],
        "buttons": [text.strip()[:100] for text in buttons[:30]],
    }


def matches_sql_response(
    response: Any,
    *,
    endpoint: str,
    expected_sql_sha256: str,
    expected_dataset_id: str | None = None,
    require_null_dataset_id: bool = False,
    expected_parent_id: str | None = None,
    expected_data_source_id: str | None = None,
) -> bool:
    if not response.url.endswith(endpoint):
        return False
    payload = request_payload(response.request)
    sql = payload.get("executeSql")
    if not isinstance(sql, str) or sql_sha256(sql) != expected_sql_sha256:
        return False
    if expected_dataset_id is not None and str(payload.get("id") or "") != expected_dataset_id:
        return False
    if require_null_dataset_id and payload.get("id") not in (None, ""):
        return False
    if expected_parent_id is not None and str(payload.get("parentId") or "") != expected_parent_id:
        return False
    if (
        expected_data_source_id is not None
        and str(payload.get("dataSourceId") or "") != expected_data_source_id
    ):
        return False
    return True


def matches_schedule_trigger(response: Any, schedule_task_id: str) -> bool:
    if not response.url.endswith("/data/set/schedules/executeOnce"):
        return False
    payload = request_payload(response.request)
    return str(payload.get("id") or "") == schedule_task_id


def request_payload(request: Any) -> dict[str, Any]:
    raw = request.post_data
    if not raw:
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def require_success_response(response: Any, *, phase: str) -> dict[str, Any]:
    if not response.ok:
        raise UsageError(f"Data Center {phase} failed with HTTP {response.status}")
    try:
        payload = response.json()
    except Exception as exc:
        raise UsageError(f"Data Center {phase} returned non-JSON content") from exc
    if not isinstance(payload, dict):
        raise UsageError(f"Data Center {phase} response is not an object")
    if payload.get("status") not in (None, "success") or payload.get("errorCode") not in (None, 0):
        raise UsageError(
            f"Data Center {phase} failed: "
            + json.dumps(compact_api_response(payload), ensure_ascii=False)
        )
    return payload


def preview_summary(payload: dict[str, Any]) -> dict[str, Any]:
    result = ((payload.get("data") or {}).get("result") or {})
    return {
        "status": payload.get("status"),
        "errorCode": payload.get("errorCode"),
        "taskId": result.get("taskId"),
        "metaCount": len(result.get("meta") or []),
        "rowCount": len(result.get("data") or []),
    }


def compact_api_response(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data")
    return {
        "status": payload.get("status"),
        "errorCode": payload.get("errorCode"),
        "data": data if isinstance(data, (str, int, float, bool, type(None))) else None,
    }


def elapsed_ms(started: float) -> int:
    return round((time.perf_counter() - started) * 1000)


def open_creation_draft(page: Any, folder: DataCenterFolder) -> None:
    page.goto(
        f"{DATA_CENTER_DATASET_URL}?selectId={folder.id}",
        wait_until="domcontentloaded",
        timeout=45_000,
    )
    folder_label = page.get_by_text(folder.name, exact=True).first
    folder_label.wait_for(state="visible", timeout=30_000)
    more = folder_label.locator("xpath=../..").locator('[aria-label="more"]').first
    more.wait_for(state="visible", timeout=15_000)
    more.click()
    create = page.get_by_text("新建数据集", exact=True).last
    create.wait_for(state="visible", timeout=10_000)
    create.click()
    page.wait_for_url(
        re.compile(rf"/data-center/edit-data-set\?parentId={re.escape(folder.id)}(?:&|$)"),
        timeout=30_000,
    )


def set_dataset_title(page: Any, name: str) -> None:
    edit = page.locator('[aria-label="edit"]:visible').first
    edit.wait_for(state="visible", timeout=15_000)
    edit.click()
    title_input = page.locator('input.ant-input[maxlength="50"]:visible').first
    title_input.wait_for(state="visible", timeout=10_000)
    title_input.fill(name)
    title_input.press("Tab")


def select_data_source(page: Any, name: str) -> None:
    select = page.locator(".ant-tree-select:visible").first
    select.wait_for(state="visible", timeout=15_000)
    select.click()
    option = page.get_by_text(name, exact=True).last
    option.wait_for(state="visible", timeout=15_000)
    option.click()
    select.get_by_title(name).last.wait_for(state="visible", timeout=10_000)


def configure_hourly_schedule(
    page: Any,
    *,
    start_date: date,
    end_date: date,
    hours: tuple[str, ...],
) -> None:
    if end_date < start_date:
        raise UsageError("Data Center schedule end date precedes start date")
    if (end_date - start_date).days > 90:
        raise UsageError("Data Center schedule range cannot exceed 90 days")
    if not hours:
        raise UsageError("Data Center hourly schedule requires at least one time")

    page.get_by_text("同步状态", exact=True).last.click()
    switch = page.locator('[role="switch"]:visible').first
    switch.wait_for(state="visible", timeout=10_000)
    if switch.get_attribute("aria-checked") != "true":
        switch.click()

    start_input = page.locator('input[placeholder="开始日期"]:visible')
    start_input.locator("xpath=..").click()
    page.wait_for_timeout(500)
    _select_range_date(page, start_date)
    _select_range_date(page, end_date)

    unit_input = page.locator("#synchronousState_synchronizationFrequency_timeUnit")
    unit_input.locator("xpath=../..").click()
    page.get_by_text("小时级", exact=True).last.click()

    time_select = page.locator(".ant-select:visible").filter(
        has_text=re.compile(r"^\s*选择时间\s*$")
    ).first
    time_select.click()
    time_input = page.locator(
        "#synchronousState_synchronizationFrequency_timeHourMinuteList"
    )
    for value in hours:
        time_input.fill(value)
        time_input.press("Enter")
    page.keyboard.press("Escape")


def trigger_synchronization(
    *,
    page: Any,
    dataset_id: str,
    schedule_task_id: str,
) -> tuple[str, dict[str, Any]]:
    page.goto(
        f"{DATA_CENTER_DATASET_URL}?selectId={dataset_id}",
        wait_until="domcontentloaded",
        timeout=45_000,
    )
    sync_tab = page.get_by_text("同步状态", exact=True).first
    sync_tab.wait_for(state="visible", timeout=30_000)
    sync_tab.click()
    sync_now = page.locator("button").filter(has_text=re.compile(r"立即\s*执行")).first
    sync_now.wait_for(state="visible", timeout=45_000)
    sync_now.click()
    confirm = page.locator("button").filter(
        has_text=re.compile(r"^\s*确\s*认\s*$")
    ).last
    confirm.wait_for(state="visible", timeout=10_000)
    triggered_at = datetime.now().astimezone().isoformat()
    with page.expect_response(
        lambda response: matches_schedule_trigger(response, schedule_task_id),
        timeout=60_000,
    ) as trigger_info:
        confirm.click()
    payload = require_success_response(trigger_info.value, phase="refresh_trigger")
    return triggered_at, compact_api_response(payload)


def poll_for_new_success(
    *,
    page: Any,
    client: DataCenterClient,
    schedule_task_id: str,
    baseline_ids: set[str],
    timeout_ms: int,
    poll_interval_ms: int,
) -> DataCenterScheduleRun:
    deadline = time.monotonic() + timeout_ms / 1000
    last_run: DataCenterScheduleRun | None = None
    while time.monotonic() < deadline:
        runs = client.fetch_schedule_runs(schedule_task_id)
        new_run = next((run for run in runs if run.id and run.id not in baseline_ids), None)
        if new_run is not None:
            last_run = new_run
            if new_run.status in SUCCESS_STATUSES:
                return new_run
            if new_run.status in FAILURE_STATUSES:
                raise UsageError(
                    "Data Center synchronization failed: "
                    + json.dumps(new_run.to_json(), ensure_ascii=False)
                )
        page.wait_for_timeout(poll_interval_ms)
    suffix = (
        json.dumps(last_run.to_json(), ensure_ascii=False)
        if last_run is not None
        else "no new execution record"
    )
    raise UsageError(f"Data Center synchronization timed out: {suffix}")


def _select_range_date(page: Any, value: date) -> None:
    title = value.isoformat()
    cell = page.locator(
        f'.ant-picker-dropdown:visible td[title="{title}"]:not(.ant-picker-cell-disabled)'
    )
    for _ in range(6):
        if cell.count() > 0:
            cell.first.click()
            return
        next_button = page.locator(
            ".ant-picker-dropdown:visible .ant-picker-header-next-btn:visible"
        ).last
        next_button.click()
        page.wait_for_timeout(150)
    raise UsageError(f"Data Center schedule date is outside the selectable range: {title}")
