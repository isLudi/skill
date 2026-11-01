"""Hash-bound, date-only renewal of an enabled expired Data Center schedule."""
from __future__ import annotations

import copy
import hashlib
import json
import re
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from _shared.config import DATA_CENTER_DATASET_URL
from _shared.errors import UsageError
from .data_center import select_dataset_for_replacement
from .data_center_replacement import sql_sha256
from .data_center_ui import (
    _select_range_date, click_optional_save_confirmation, get_codemirror_sql,
    matches_sql_response, request_payload, require_success_response,
    wait_for_editor_sql_hash, preview_summary,
)

PARAM_KEYS = ('fieldName', 'fieldType', 'paramId', 'showName', 'dataTypeCode', 'orgParamType')
DERIVED_SCHEDULE_KEYS = {'isExpire', 'taskId'}


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=True, sort_keys=True,
                                     separators=(',', ':')).encode('utf-8')).hexdigest()


def schedule_values(schedule: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in schedule.items() if k not in DERIVED_SCHEDULE_KEYS}


def parameter_values(detail: dict[str, Any]) -> list[dict[str, Any]]:
    rows = detail.get('dataParamList')
    if not isinstance(rows, list) or not rows:
        raise UsageError('Data Center renewal requires complete saved field metadata')
    projected = [{k: r.get(k) for k in PARAM_KEYS} for r in rows]
    # Detail exposes SQL types; the native save form sends UI families. Keep
    # exact dataTypeCode (e.g. 4 BIGINT vs 6 DOUBLE), IDs, names and all other
    # metadata while canonicalizing only these observed transport spellings.
    families = {'VARCHAR': 'TEXT', 'CHAR': 'TEXT', 'TINYINT': 'NUM', 'INT': 'NUM',
                'BIGINT': 'NUM', 'DOUBLE': 'NUM', 'DECIMAL': 'NUM'}
    for item in projected:
        item['fieldType'] = families.get(item['fieldType'], item['fieldType'])
    names = [str(item['fieldName'] or '') for item in projected]
    if any(not name for name in names) or len(set(names)) != len(names):
        raise UsageError('Saved field metadata has missing or ambiguous field names')
    # Detail is returned by persistent field ID; preview/save uses SQL output
    # order. Compare every property by stable field identity, not array order.
    return sorted(projected, key=lambda item: (str(item['fieldName']), str(item['paramId'])))


def validate_range(start: date, end: date, *, today: date | None = None) -> None:
    if start < (today or date.today()) or not 0 < (end - start).days <= 90:
        raise UsageError('Renewal range must start today or later and span 1 to 90 days')


def build_renewal_plan(*, domain: str, current: Any, start: date, end: date,
                       today: date | None = None) -> dict[str, Any]:
    validate_range(start, end, today=today)
    # Reuse the registered domain boundary; never extend the target selector.
    select_dataset_for_replacement([current.dataset], domain=domain,
                                   dataset_id=current.dataset.id)
    schedule = copy.deepcopy(current.detail_payload.get('schedule') or {})
    if schedule.get('taskStatus') is not True or schedule.get('isExpire') is not True:
        raise UsageError('Only enabled, expired schedules may be renewed')
    if not schedule.get('taskId') or not schedule.get('synchronizationFrequency'):
        raise UsageError('Saved schedule identity or frequency is missing')
    replacement = schedule_values(schedule)
    replacement['dateRange'] = [start.isoformat(), end.isoformat()]
    plan = {
        'schema_version': 'data-center-schedule-renewal-v1', 'status': 'ready',
        'operation': 'renew_expired_dataset_schedule_dates_only',
        'preview_policy': 'saved_sql_once_if_save_disabled',
        'created_at': datetime.now(timezone.utc).isoformat(), 'domain': domain,
        'dataset': current.to_summary_json(), 'sql_sha256': sql_sha256(current.execute_sql),
        'parameters': parameter_values(current.detail_payload),
        'baseline_schedule': schedule, 'replacement_schedule': replacement,
        'baseline_schedule_sha256': digest(schedule),
    }
    plan['plan_sha256'] = digest(plan)
    return plan


def validate_plan(plan: dict[str, Any], expected: str, confirmed: bool) -> None:
    body = {k: v for k, v in plan.items() if k != 'plan_sha256'}
    if not confirmed or expected != plan.get('plan_sha256') or digest(body) != expected:
        raise UsageError('Renewal requires confirmation and the exact untampered Plan Hash')
    if plan.get('schema_version') != 'data-center-schedule-renewal-v1' or plan.get('status') != 'ready':
        raise UsageError('Invalid renewal plan')
    if plan.get('operation') != 'renew_expired_dataset_schedule_dates_only':
        raise UsageError('Unexpected renewal operation')
    if plan.get('preview_policy') != 'saved_sql_once_if_save_disabled':
        raise UsageError('Unreviewed renewal preview policy')
    old = plan['baseline_schedule']
    if digest(old) != plan['baseline_schedule_sha256'] or old.get('isExpire') is not True or old.get('taskStatus') is not True:
        raise UsageError('Invalid enabled/expired baseline')
    new = copy.deepcopy(plan['replacement_schedule'])
    start, end = map(date.fromisoformat, new.pop('dateRange'))
    validate_range(start, end)
    previous = schedule_values(old)
    previous.pop('dateRange', None)
    if new != previous:
        raise UsageError('Renewal plan changes fields other than the date range')


def verify_current(plan: dict[str, Any], current: Any) -> None:
    if current.to_summary_json() != plan['dataset'] or sql_sha256(current.execute_sql) != plan['sql_sha256']:
        raise UsageError('Dataset identity or SQL drift blocks renewal')
    if parameter_values(current.detail_payload) != plan['parameters']:
        raise UsageError('Dataset field metadata drift blocks renewal')
    if digest(current.detail_payload.get('schedule') or {}) != plan['baseline_schedule_sha256']:
        raise UsageError('Schedule drift blocks renewal')


def verify_save_payload(plan: dict[str, Any], payload: dict[str, Any]) -> None:
    if set(payload) != {'id', 'name', 'menuType', 'dataSourceId', 'dataParamList', 'schedule', 'executeSql'}:
        raise UsageError('Unreviewed Data Center renewal save payload shape')
    for key in ('id', 'name', 'dataSourceId'):
        if str(payload.get(key) or '') != str(plan['dataset'].get(key) or ''):
            raise UsageError('Renewal save identity drift: ' + key)
    if payload.get('menuType') != 'DATA_SET' or sql_sha256(payload.get('executeSql') or '') != plan['sql_sha256']:
        raise UsageError('Renewal may not change dataset type or SQL')
    if parameter_values(payload) != plan['parameters'] or payload['schedule'] != plan['replacement_schedule']:
        raise UsageError('Renewal may only change schedule dateRange')


def verify_readback(plan: dict[str, Any], saved: Any) -> dict[str, Any]:
    if saved.to_summary_json() != plan['dataset'] or sql_sha256(saved.execute_sql) != plan['sql_sha256']:
        raise UsageError('Renewal SQL or dataset identity readback mismatch')
    if parameter_values(saved.detail_payload) != plan['parameters']:
        raise UsageError('Renewal field metadata readback mismatch')
    schedule = saved.detail_payload.get('schedule') or {}
    if schedule.get('isExpire') is not False or not schedule.get('taskId'):
        raise UsageError('Renewed schedule remains expired or has no task identity')
    if schedule_values(schedule) != plan['replacement_schedule']:
        raise UsageError('Renewal schedule readback mismatch')
    return {'sql_sha256': plan['sql_sha256'], 'schedule': schedule,
            'fields_unchanged': True, 'fully_verified': True}


def claim_single_write(plan: dict[str, Any], payload: dict[str, Any],
                       claim_dir: Path, progress: dict[str, Any]) -> None:
    if progress.get('write_request_count'):
        raise UsageError('Renewal permits exactly one save request')
    verify_save_payload(plan, payload)
    claim_dir.mkdir(parents=True, exist_ok=True)
    key = digest([plan['dataset']['id'], plan['sql_sha256'],
                  plan['baseline_schedule_sha256'], plan['replacement_schedule']])
    try:
        with (claim_dir / (key + '.json')).open('x', encoding='utf-8') as stream:
            json.dump({'plan_sha256': plan['plan_sha256'], 'attempted_at':
                       datetime.now(timezone.utc).isoformat()}, stream)
    except FileExistsError:
        raise UsageError('This renewal write intent was already attempted; read back its state') from None
    progress.update(write_request_count=1, write_request_sent=True)


def dismiss_editor_memory_notice(page: Any, *, grace_ms: int = 3_000) -> bool:
    """Acknowledge only the observed automatic-preview memory error notice.

    This acknowledgement neither retries a query nor counts as successful
    extraction; the separate refresh must still obtain a new SUCCESS.
    """
    dialogs = page.locator('.ant-modal-wrap:visible')
    deadline = time.monotonic() + grace_ms / 1000
    # The automatic preview response may arrive just after CodeMirror has its
    # saved SQL. Give that response time to create its blocking notice.
    while True:
        count = dialogs.count()
        if count:
            break
        if time.monotonic() >= deadline:
            return False
        page.wait_for_timeout(100)
    if count != 1:
        raise UsageError('Ambiguous editor dialogs block schedule renewal')
    dialog = dialogs.first
    text = dialog.inner_text().strip()
    acknowledgement = dialog.get_by_role('button', name='知道了', exact=True)
    if (not text.startswith('SQL执行失败') or 'MEM_LIMIT_EXCEEDED' not in text
            or acknowledgement.count() != 1 or dialog.locator('button').count() != 1):
        raise UsageError('Unreviewed editor dialog blocks schedule renewal')
    acknowledgement.click()
    dialog.wait_for(state='hidden', timeout=10_000)
    return True


def preview_saved_sql_if_required(page: Any, plan: dict[str, Any], editor: Any,
                                  progress: dict[str, Any], *, force: bool = False) -> None:
    """Keep the native Save gate; validate the unchanged SQL once if required."""
    if not force and not page.locator('button[type=submit]').first.is_disabled():
        return
    if plan.get('preview_policy') != 'saved_sql_once_if_save_disabled':
        raise UsageError('The renewal plan does not allow the required preview')
    if sql_sha256(get_codemirror_sql(editor)) != plan['sql_sha256']:
        raise UsageError('SQL drift blocks the renewal preview')
    progress['phase'] = 'saved_sql_preview'

    def guard_preview(route: Any) -> None:
        payload = request_payload(route.request)
        if (progress.get('preview_request_count', 0)
                or sql_sha256(payload.get('executeSql') or '') != plan['sql_sha256']):
            progress['preview_blocked_reason'] = 'Repeated or changed SQL preview'
            route.abort()
            return
        progress['preview_request_count'] = 1
        route.continue_()

    page.route('**/data/set/execute', guard_preview)
    try:
        with page.expect_response(lambda response: matches_sql_response(response,
                endpoint='/data/set/execute', expected_sql_sha256=plan['sql_sha256']),
                timeout=300_000) as info:
            run = page.locator('[aria-label="play-circle"]').first
            run.wait_for(state='visible', timeout=15_000)
            run.click()
        try:
            payload = require_success_response(info.value, phase='renewal_saved_sql_preview')
        except UsageError:
            failed = info.value.json()
            progress['preview_failure'] = {k: failed.get(k) for k in ('status','errorCode','extraCode','error')}
            raise
        progress['preview'] = preview_summary(payload)
    finally:
        page.unroute('**/data/set/execute', guard_preview)
    # React may update Save eligibility after the response callback. The native
    # click's enabled-state wait remains authoritative; never force the button.


class DataCenterScheduleRenewalExecutor:
    def __init__(self, *, page: Any, client: Any, plan: dict[str, Any], claim_dir: Path):
        self.page, self.client, self.plan, self.claim_dir = page, client, plan, claim_dir
        self.progress = {'phase': 'preflight', 'write_request_sent': False,
                         'write_request_count': 0, 'fully_verified': False}

    def prepare_editor_sql(self, editor: Any) -> None:
        self.progress['editor_memory_notice_acknowledged'] = dismiss_editor_memory_notice(self.page)

    def ensure_save_ready(self, editor: Any) -> None:
        preview_saved_sql_if_required(self.page, self.plan, editor, self.progress)

    def expected_save_sql_sha256(self) -> str:
        return self.plan['sql_sha256']

    def claim_write(self, payload: dict[str, Any]) -> None:
        try:
            claim_single_write(self.plan, payload, self.claim_dir, self.progress)
        except UsageError:
            self.progress['blocked_field_metadata'] = parameter_values(payload)
            self.progress['blocked_schedule'] = payload.get('schedule')
            raise

    def verify_saved(self, saved: Any) -> dict[str, Any]:
        return verify_readback(self.plan, saved)

    def execute(self) -> dict[str, Any]:
        plan, page = self.plan, self.page
        dataset = select_dataset_for_replacement(self.client.discover_datasets(),
                   domain=plan['domain'], dataset_id=plan['dataset']['id'])
        current = self.client.fetch_dataset_sql(dataset)
        verify_current(plan, current)
        page.goto(f'{DATA_CENTER_DATASET_URL}?selectId={dataset.id}',
                  wait_until='domcontentloaded', timeout=45_000)
        page.locator('button').filter(has_text=re.compile(r'编\s*辑')).first.click()
        editor = page.locator('.CodeMirror').first
        editor.wait_for(state='visible', timeout=45_000)
        sql = wait_for_editor_sql_hash(page=page, editor=editor,
                  expected_sha256=plan['sql_sha256'], timeout_ms=45_000)
        if sql_sha256(sql) != plan['sql_sha256']:
            raise UsageError('Renewal editor SQL differs from saved baseline')
        self.prepare_editor_sql(editor)
        self.progress['phase'] = 'open_schedule'
        page.get_by_text('同步状态', exact=True).last.click()
        # Clear the expired range, then wait for the current calendar to render.
        self.progress['phase'] = 'select_dates'
        picker = page.locator('.ant-picker-range:visible').first
        picker.hover()
        picker.locator('.ant-picker-clear').click()
        page.locator('input[placeholder="开始日期"]:visible').locator('xpath=..').click()
        page.locator('.ant-picker-dropdown:visible').wait_for(state='visible', timeout=10_000)
        for value in plan['replacement_schedule']['dateRange']:
            _select_range_date(page, date.fromisoformat(value))
        for label, expected in zip(('开始日期', '结束日期'), plan['replacement_schedule']['dateRange']):
            if page.locator(f'input[placeholder="{label}"]:visible').input_value() != expected:
                raise UsageError('Renewal calendar date readback mismatch')
        if sql_sha256(get_codemirror_sql(editor)) != self.expected_save_sql_sha256():
            raise UsageError('SQL changed while selecting the renewal range')
        self.ensure_save_ready(editor)
        self.progress['phase'] = 'save'
        def guarded_save(route: Any) -> None:
            try:
                self.claim_write(request_payload(route.request))
            except Exception as exc:
                self.progress['blocked_reason'] = type(exc).__name__ + ': ' + str(exc)
                route.abort()
                return
            route.continue_()

        page.route('**/data/set/saveAndUpdate', guarded_save)
        try:
            with page.expect_response(lambda response: matches_sql_response(response,
                    endpoint='/data/set/saveAndUpdate', expected_sql_sha256=self.expected_save_sql_sha256(),
                    expected_dataset_id=dataset.id), timeout=60_000) as info:
                page.locator('button[type=submit]').first.click()
                if self.progress.get('blocked_reason'):
                    raise UsageError(self.progress['blocked_reason'])
                click_optional_save_confirmation(page)
            require_success_response(info.value, phase='schedule_renewal')
        finally:
            page.unroute('**/data/set/saveAndUpdate', guarded_save)
        self.progress['phase'] = 'readback'
        readback = self.verify_saved(self.client.fetch_dataset_sql(dataset))
        self.progress.update(phase='complete', fully_verified=True, readback=readback)
        return dict(self.progress)
