"""One scheduled group batch; each channel, grain and period fails independently."""
from __future__ import annotations

from contextlib import closing
from datetime import timedelta
import json
from pathlib import Path
import time

from ...core import catalog
from ...core.locks import runner_lock
from ...common import resend
from .channels import app_grade_9 as policy
from .grade9_components import (
    KEY, specs, prepare_one, validate_definition, validate_message, require_receipt_snapshot,
    prepare as prepare, write_preview as write_preview,
    delegated_channels as delegated_channels,
    validate_component_calendar as validate_component_calendar,
)
from .workflow import source_channel_count

__all__ = ['prepare', 'write_preview', 'delegated_channels', 'validate_component_calendar',
           'validate_definition', 'run_slot', 'send_now']


def _record(schedule, db, slot, spec, status, reason='', **extra):
    schedule.record_channel(db, slot, spec['report_kind'], status, reason,
                            source_channel=spec['channel'], label=spec['label'], period=spec['period'], **extra)


def _run_round(definition, target, slot, state, db, evidence, pending, key_for, time_guard, *, preflight):
    from . import scheduler as schedule
    state.mkdir(parents=True, exist_ok=True)
    failed, outcomes = [], []
    for spec in pending:
        key = key_for(spec)
        try:
            prior = db.execute('SELECT status,message_id FROM deliveries WHERE key=?', (key,)).fetchone()
            if prior and resend.decide(prior[0], prior[1]) == resend.DONE:
                _record(schedule, db, slot, spec, 'duplicate_suppressed', message_id=prior[1])
                outcomes.append({**spec, 'status': 'duplicate_suppressed', 'message_id': prior[1]})
                continue
            period = evidence['periods'].get(spec['period'])
            if not period:
                raise ValueError('本条期次不在上游完整双期审计中')
            owner = catalog.load_channel(spec['owner'])
            count = source_channel_count(period['channel_counts'], owner['source']['channel_match'], spec['channel'])
            if count == 0:
                _record(schedule, db, slot, spec, 'skipped_no_source_rows')
                outcomes.append({**spec, 'status': 'skipped_no_source_rows'})
                continue
            message = prepare_one(definition, target, spec, slot, state / 'prepared')
            validate_message(message, evidence, slot)
            context = message['context']
            require_receipt_snapshot(message, db, key)
            if context.get('skip_delivery'):
                _record(schedule, db, slot, spec, 'skipped_no_eligible_rows', context.get('skip_reason', ''))
                outcomes.append({**spec, 'status': 'skipped_no_eligible_rows'})
                continue
            schedule.assert_current_revision(context, message['validation_cfg'])
            preview = write_preview({'messages': [message]}, state / 'previews' / spec['part'])
            if preview['messages'][0]['status'] != 'preview_ready':
                raise ValueError('本条本地预览失败：' + preview['messages'][0].get('error', 'unknown'))
            if preflight:
                _record(schedule, db, slot, spec, 'preflight_ready')
                outcomes.append({**spec, 'status': 'preflight_ready', 'preview': preview})
                continue
            verified = schedule._deliver_verified(context, message['validation_cfg'], slot, db, evidence,
                                                   key=key, time_guard=time_guard)
            receipt = db.execute('SELECT status,message_id FROM deliveries WHERE key=?', (key,)).fetchone()
            status, message_id = receipt if receipt else ('not_sent', '')
            _record(schedule, db, slot, spec, status, message_id=message_id)
            outcomes.append({**spec, 'status': status, 'message_id': message_id})
            if not verified:
                failed.append(spec)
        except (Exception, SystemExit) as exc:
            reason = type(exc).__name__ + ': ' + str(exc)[:200]
            _record(schedule, db, slot, spec, 'blocked_component', reason)
            outcomes.append({**spec, 'status': 'blocked_component', 'reason': reason})
            failed.append(spec)
            # Continue immediately: no component is a prerequisite for another.
            continue
    summary = {'slot': slot.isoformat(), 'preflight': preflight, 'outcomes': outcomes,
               'pending': [item['report_kind'] for item in failed]}
    (state / ('preflight.json' if preflight else 'component-outcomes.json')).write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    return failed


def run_slot(cfg, preflight, slot, state, db):
    from . import scheduler as schedule
    definition = catalog.load_channel(KEY)
    validate_definition(definition)
    if not preflight and definition['delivery_sequence']['stage'] != 'scheduled':
        raise ValueError('初三双渠道任务尚未启用')
    target = catalog.select_targets(definition, [cfg['target_id']])[0]
    pending = specs(slot)
    deadline = slot + timedelta(minutes=cfg['deadline_minute'] + 1)
    while schedule.now() < deadline:
        try:
            schedule.verify_bot(cfg)
            evidence = schedule.upstream_ready(cfg, slot)
            pending = _run_round(definition, target, slot, state, db, evidence, pending,
                lambda spec: schedule.delivery_key(cfg, slot, spec['channel'], spec['report_kind']),
                lambda: schedule.require_send_window(slot, cfg), preflight=preflight)
            if not pending:
                schedule.emit('grade9_group_finished', slot=slot.isoformat(), preflight=preflight)
                return 0
            if preflight:
                return 1
        except (Exception, SystemExit) as exc:
            schedule.emit('grade9_shared_source_not_ready', reason=type(exc).__name__ + ': ' + str(exc)[:200])
            if preflight:
                return 1
        wake = schedule.next_check(schedule.now(), slot, cfg)
        if wake >= deadline:
            break
        schedule.emit('grade9_retry_pending_components', parts=[item['report_kind'] for item in pending],
                      next_retry_at=wake.isoformat())
        while schedule.now() < wake:
            time.sleep(min(20, max(0.01, (wake - schedule.now()).total_seconds())))
    schedule.emit('grade9_deadline_with_partial_outcomes', pending=[item['report_kind'] for item in pending])
    return 1


def send_now(definition, target, request_id, *, preflight=False, requested_slot=None, allow_expired=False):
    from . import immediate, scheduler as schedule
    validate_definition(definition)
    cfg = catalog.schedule_config(definition, target)
    schedule.validate_config(cfg)
    state = Path(cfg['state_dir'])
    with runner_lock(state) as acquired:
        if not acquired:
            raise ValueError('Another broadcast instance owns this group batch')
        with closing(schedule.connect_ledger(state)) as db:
            started = schedule.now()
            slot = requested_slot or immediate.latest_upstream_slot(started)
            if requested_slot is not None and (slot.tzinfo is None or slot.minute or slot.hour not in cfg['hours'] or not allow_expired):
                raise ValueError('补发需要已登记槽位及明确授权')
            immediate.request_key(cfg, request_id)
            schedule.verify_bot(cfg)
            publication = immediate.verify_publication(cfg)
            evidence = schedule.upstream_ready(cfg, slot)
            evidence.update(mode='grade9_group_immediate', request_id=request_id, publication=publication)
            logical = {'period': policy.business_period(slot), 'report_type': policy.scheduled_report_type(slot)}

            def time_guard():
                immediate.require_fresh_request(started, slot, evidence, logical, schedule.now(),
                                                allow_expired=allow_expired, cfg=cfg)
                directory = schedule.operator('list-execution-history', cfg, '--limit', '12')
                latest = schedule.validate_history(schedule.read_json(directory / 'history.json'), cfg, slot)
                if latest['id'] != evidence['execution_id']:
                    raise ValueError('Upstream execution changed during one-time preparation')

            time_guard()
            failed = _run_round(definition, target, slot, state / 'ordered-now', db, evidence, specs(slot),
                lambda spec: immediate.request_key(cfg, request_id, spec['report_kind']),
                time_guard, preflight=preflight)
            return 1 if failed else 0
