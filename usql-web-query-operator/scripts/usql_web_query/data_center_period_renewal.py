"""Independent recovery: only forward date/period lower bounds plus expired dates."""
from __future__ import annotations
import copy
import json
import re
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
import sqlglot
from sqlglot import exp
from _shared.errors import UsageError
from .data_center_replacement import canonical_sql_text, sql_sha256
from .data_center_schedule import (
    DataCenterScheduleRenewalExecutor, build_renewal_plan, digest,
    dismiss_editor_memory_notice, parameter_values, preview_saved_sql_if_required,
    schedule_values, validate_range, verify_save_payload,
)
from .data_center_ui import (get_codemirror_sql, set_codemirror_sql, request_payload,
                             trigger_synchronization, poll_for_new_success)

SCHEMA = 'data-center-period-renewal-v1'
OPERATION = 'narrow_period_lower_bounds_and_renew_expired_schedule'


def _date_literal(expression: Any) -> tuple[Any, date, str]:
    literal = expression
    kind = 'period'
    if isinstance(expression, exp.Cast) and str(expression.args.get('to')).upper() == 'DATE':
        literal = expression.this
        kind = 'date'
    if not isinstance(literal, exp.Literal) or not literal.is_string:
        raise UsageError('Recovery permits only literal date/period lower bounds')
    value = str(literal.this)
    if kind == 'period' and re.fullmatch(r'\d{8}期', value):
        parsed = datetime.strptime(value[:8], '%Y%m%d').date()
    elif re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        parsed = date.fromisoformat(value)
        kind = 'date'
    else:
        raise UsageError('Recovery lower bound is not a calendar date or period')
    return literal, parsed, kind


def _positive_where_conjunction(node: Any) -> None:
    parent = node.parent
    while isinstance(parent, (exp.And, exp.Paren)):
        parent = parent.parent
    if not isinstance(parent, exp.Where):
        raise UsageError('Recovery date change must be a positive WHERE conjunction')


def prove_period_narrowing(before: str, after: str) -> list[dict[str, str]]:
    before, after = canonical_sql_text(before), canonical_sql_text(after)
    old, new = sqlglot.parse_one(before, read='presto'), sqlglot.parse_one(after, read='presto')
    if not isinstance(old, exp.Query) or not isinstance(new, exp.Query):
        raise UsageError('Recovery SQL must be one read-only query')
    if len(sqlglot.parse(after, read='presto')) != 1:
        raise UsageError('Recovery rejects multiple SQL statements')
    old_nodes, new_nodes = list(old.find_all(exp.GTE)), list(new.find_all(exp.GTE))
    if len(old_nodes) != len(new_nodes):
        raise UsageError('Recovery may not add or remove SQL predicates')
    restored = new.copy()
    restored_nodes = list(restored.find_all(exp.GTE))
    changes, text_edits = [], []
    for previous, candidate, revert in zip(old_nodes, new_nodes, restored_nodes):
        if previous == candidate:
            continue
        if previous.this != candidate.this:
            raise UsageError('Recovery cannot change the filtered expression')
        _positive_where_conjunction(previous)
        _positive_where_conjunction(candidate)
        old_lit, old_date, old_kind = _date_literal(previous.expression)
        new_lit, new_date, new_kind = _date_literal(candidate.expression)
        if old_kind != new_kind or new_date <= old_date:
            raise UsageError('Recovery requires a strictly later date/period lower bound')
        if previous.expression.copy().transform(lambda n: new_lit.copy() if n == old_lit else n) != candidate.expression:
            raise UsageError('Recovery cannot change the bound type or expression')
        revert.set('expression', previous.expression.copy())
        positions = (old_lit.meta.get('start'), old_lit.meta.get('end'), new_lit.meta.get('start'), new_lit.meta.get('end'))
        if any(not isinstance(i, int) for i in positions):
            raise UsageError('Missing exact SQL literal source positions')
        a, b, c, d = positions
        text_edits.append((c, d + 1, before[a:b + 1]))
        changes.append({'expression': previous.this.sql(dialect='presto'), 'before': str(old_lit.this), 'after': str(new_lit.this)})
    if not changes or restored != old:
        raise UsageError('Recovery permits only reviewed date/period lower-bound changes')
    restored_text = after
    for start, end, original in sorted(text_edits, reverse=True):
        restored_text = restored_text[:start] + original + restored_text[end:]
    if restored_text != before:
        raise UsageError('Recovery must preserve all other SQL bytes, including comments')
    return changes


def build_period_renewal_plan(*, domain: str, current: Any, baseline_file: Path,
                            sql_file: Path, candidate: str, start: date, end: date,
                            refresh_after_save: bool = False) -> dict[str, Any]:
    if sql_sha256(baseline_file.read_text(encoding='utf-8')) != sql_sha256(current.execute_sql):
        raise UsageError('Recovery baseline file must match the freshly fetched complete SQL')
    changes = prove_period_narrowing(current.execute_sql, candidate)
    plan = build_renewal_plan(domain=domain, current=current, start=start, end=end)
    plan.update(schema_version=SCHEMA, operation=OPERATION,
                baseline_file=str(baseline_file.resolve()), candidate_file=str(sql_file.resolve()),
                candidate_sql_sha256=sql_sha256(candidate), narrowing_proof=changes,
                refresh_after_save=refresh_after_save,
                preview_policy='candidate_sql_once_before_save')
    plan.pop('plan_sha256')
    plan['plan_sha256'] = digest(plan)
    return plan


def validate_period_plan(plan: dict[str, Any], expected: str, confirmed: bool) -> str:
    if not confirmed or plan.get('plan_sha256') != expected or digest({k:v for k,v in plan.items() if k!='plan_sha256'}) != expected:
        raise UsageError('Recovery requires the exact Plan Hash and production confirmation')
    if plan.get('schema_version') != SCHEMA or plan.get('operation') != OPERATION or plan.get('status') != 'ready':
        raise UsageError('Invalid independent period renewal recovery plan')
    if plan.get('preview_policy') != 'candidate_sql_once_before_save':
        raise UsageError('Recovery always requires candidate SQL preview')
    if not isinstance(plan.get('refresh_after_save', False), bool):
        raise UsageError('Recovery refresh policy must be boolean')
    old, new = plan['baseline_schedule'], plan['replacement_schedule']
    if old.get('isExpire') is not True or old.get('taskStatus') is not True or digest(old) != plan['baseline_schedule_sha256']:
        raise UsageError('Recovery requires an enabled expired exact schedule baseline')
    start, end = map(date.fromisoformat, new['dateRange'])
    validate_range(start, end)
    expected_schedule = schedule_values(old)
    expected_schedule['dateRange'] = new['dateRange']
    if new != expected_schedule:
        raise UsageError('Recovery cannot change frequency, alarms or enabled state')
    from .data_center_replacement import load_replacement_sql
    baseline = load_replacement_sql(Path(plan['baseline_file']))
    candidate = load_replacement_sql(Path(plan['candidate_file']))
    if sql_sha256(baseline) != plan['sql_sha256'] or sql_sha256(candidate) != plan['candidate_sql_sha256']:
        raise UsageError('Recovery baseline or candidate file drift')
    if prove_period_narrowing(baseline, candidate) != plan['narrowing_proof']:
        raise UsageError('Recovery narrowing proof changed')
    return candidate


class DataCenterPeriodRenewalExecutor(DataCenterScheduleRenewalExecutor):
    def __init__(self, *, candidate: str, **kwargs):
        super().__init__(**kwargs)
        self.candidate = candidate

    def expected_save_sql_sha256(self) -> str:
        return self.plan['candidate_sql_sha256']

    def ensure_save_ready(self, editor: Any) -> None:
        # Candidate preview was mandatory before the dates were changed. Avoid
        # replaying it; native Save still waits for enabled state before click.
        if self.progress.get('preview',{}).get('status') != 'success':
            raise UsageError('Recovery cannot save without its successful candidate preview')

    def prepare_editor_sql(self, editor: Any) -> None:
        self.progress['editor_memory_notice_acknowledged'] = dismiss_editor_memory_notice(self.page)
        set_codemirror_sql(editor, self.candidate)
        if sql_sha256(get_codemirror_sql(editor)) != self.expected_save_sql_sha256():
            raise UsageError('Recovery candidate editor Hash mismatch')
        preview_plan = {**self.plan, 'sql_sha256': self.expected_save_sql_sha256(), 'preview_policy': 'saved_sql_once_if_save_disabled'}
        started = time.monotonic()
        preview_saved_sql_if_required(self.page, preview_plan, editor, self.progress, force=True)
        self.progress['preview_seconds'] = round(time.monotonic() - started, 3)
        if self.progress['preview']['metaCount'] != len(self.plan['parameters']):
            raise UsageError('Recovery preview field count changed')

    def claim_write(self, payload: dict[str, Any]) -> None:
        if self.progress.get('write_request_count'):
            raise UsageError('Recovery permits only one save request')
        projected = {**self.plan, 'sql_sha256': self.expected_save_sql_sha256()}
        try:
            verify_save_payload(projected, payload)
        except UsageError:
            self.progress['blocked_field_metadata'] = parameter_values(payload)
            self.progress['blocked_schedule'] = payload.get('schedule')
            raise
        self.claim_dir.mkdir(parents=True, exist_ok=True)
        key = digest([self.plan['dataset']['id'], self.plan['sql_sha256'],
                      self.plan['baseline_schedule_sha256'], self.expected_save_sql_sha256(), self.plan['replacement_schedule']])
        try:
            with (self.claim_dir / (key + '.json')).open('x', encoding='utf-8') as stream:
                json.dump({'plan_sha256': self.plan['plan_sha256'], 'attempted_at':datetime.now(timezone.utc).isoformat()}, stream)
        except FileExistsError:
            raise UsageError('Recovery write intent already attempted; read back instead') from None
        self.progress.update(write_request_count=1, write_request_sent=True)

    def verify_saved(self, saved: Any) -> dict[str, Any]:
        stable = lambda d: {k:v for k,v in d.items() if k not in ('sqlBytes','sqlLines')}
        if stable(saved.to_summary_json()) != stable(self.plan['dataset']) or sql_sha256(saved.execute_sql) != self.expected_save_sql_sha256():
            raise UsageError('Recovery SQL or dataset identity readback mismatch')
        if parameter_values(saved.detail_payload) != self.plan['parameters']:
            raise UsageError('Recovery field metadata changed')
        schedule = saved.detail_payload.get('schedule') or {}
        if schedule.get('isExpire') is not False or not schedule.get('taskId') or schedule_values(schedule) != self.plan['replacement_schedule']:
            raise UsageError('Recovery schedule readback mismatch')
        return {'sql_sha256':self.expected_save_sql_sha256(), 'schedule':schedule, 'fields_unchanged':True, 'fully_verified':True}

    def refresh_saved_once(self, *, artifacts_dir: Path, timeout_ms: int) -> dict[str, Any]:
        """Fresh readback-bound child plan; no SQL save or query replay here."""
        validate_period_plan(self.plan,self.plan['plan_sha256'],True)
        if self.plan.get('refresh_after_save') is not True or self.progress.get('write_request_count') != 1:
            raise UsageError('Post-save refresh requires the explicit parent policy and one saved write')
        from .data_center import select_dataset_for_replacement
        dataset = select_dataset_for_replacement(self.client.discover_datasets(),domain=self.plan['domain'],dataset_id=self.plan['dataset']['id'])
        current = self.client.fetch_dataset_sql(dataset)
        checked = self.verify_saved(current)
        schedule = checked['schedule'];task_id = str(schedule['taskId'])
        runs = self.client.fetch_schedule_runs(task_id,page_size=50)
        child = {'operation':'refresh_verified_period_renewal_once','parent_plan_sha256':self.plan['plan_sha256'],
                 'dataset_id':dataset.id,'sql_sha256':self.expected_save_sql_sha256(),
                 'schedule_sha256':digest(schedule),'task_id':task_id,
                 'baseline_run_ids':[r.id for r in runs], 'execution_budget':1}
        child['plan_sha256'] = digest(child)
        artifacts_dir.mkdir(parents=True,exist_ok=True)
        child_file = artifacts_dir/('refresh_step_'+self.plan['plan_sha256'][:16]+'.json')
        with child_file.open('x',encoding='utf-8') as stream:
            json.dump(child,stream,ensure_ascii=True,indent=2)
        self.progress.update(phase='refresh_trigger',fully_verified=False,
             refresh_step_plan=str(child_file),refresh_step_plan_sha256=child['plan_sha256'],
             post_save_sql_sha256=child['sql_sha256'],schedule_task_id=task_id,
             baseline_latest_run=max(runs,key=lambda r:r.start_time).to_json() if runs else None)

        def guard_refresh(route: Any) -> None:
            payload = request_payload(route.request)
            if self.progress.get('refresh_request_count') or payload != {'id':task_id}:
                self.progress['refresh_blocked_reason'] = 'Repeated or mismatched refresh request'
                route.abort();return
            key = digest([dataset.id,child['sql_sha256'],child['schedule_sha256'],'refresh_after_period_renewal'])
            try:
                with (self.claim_dir/(key+'.refresh.json')).open('x',encoding='utf-8') as stream:
                    json.dump({'refresh_plan_sha256':child['plan_sha256']},stream)
            except FileExistsError:
                self.progress['refresh_blocked_reason'] = 'Refresh intent was already attempted'
                route.abort();return
            self.progress['refresh_request_count'] = 1
            self.progress['refresh_request_sent_at'] = datetime.now().astimezone().isoformat()
            route.continue_()

        self.page.route('**/data/set/schedules/executeOnce',guard_refresh)
        try:
            triggered,response = trigger_synchronization(page=self.page,dataset_id=dataset.id,schedule_task_id=task_id)
        finally:
            self.page.unroute('**/data/set/schedules/executeOnce',guard_refresh)
        self.progress.update(phase='refresh_poll',refresh_triggered=True,
                             refresh_triggered_at=triggered,refresh_response=response)
        latest = poll_for_new_success(page=self.page,client=self.client,schedule_task_id=task_id,
               baseline_ids={r.id for r in runs},timeout_ms=timeout_ms,poll_interval_ms=5000)
        self.progress.update(phase='complete',fully_verified=True,latest_run=latest.to_json())
        return dict(self.progress)
