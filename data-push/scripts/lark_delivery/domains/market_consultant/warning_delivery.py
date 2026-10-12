"""One shared audited read, independent channel preparations and daily sends."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutureTimeout
from datetime import datetime, timedelta
import json
from pathlib import Path
import time

from ...core.catalog import load_channel
from ...core.locks import runner_lock
from ...common.push_log import run_scope
from .delivery_ledger import connect_ledger, record_outcome
from . import warning_adapter as wa, warning_data as wd, warning_upstream as wu
from . import warning_channel_delivery as channel_delivery
from . import warning_routes as routes
from .upstream import verify_bot

CLEAN = {'prepared', 'sent_verified', 'skipped_no_source_rows'}


def now():
    return datetime.now(wu.TZ)


def parallel_phase(items, operation, emit, failure_status, deadline=None):
    """A slow or failed channel cannot consume another channel's send window.

    Preparation/upload workers have no send capability. Their late results
    are discarded. Actual sends use bounded API calls and durable claims.
    """
    if not items:
        return {}
    pool = ThreadPoolExecutor(max_workers=len(items))
    futures = {pool.submit(operation, channel, item): channel for channel, item in items.items()}
    completed, results = set(), {}
    timeout = None if deadline is None else max(0, (deadline - now()).total_seconds())
    try:
        for future in as_completed(futures, timeout=timeout):
            channel = futures[future]
            completed.add(channel)
            try:
                results[channel] = future.result()
            except Exception as exc:
                emit(channel, {'status': failure_status, 'reason': str(exc)[:1000]})
    except FutureTimeout:
        pass
    finally:
        for future, channel in futures.items():
            if channel not in completed:
                future.cancel()
                emit(channel, {'status': failure_status, 'reason': 'Channel phase exceeded its preparation deadline'})
        pool.shutdown(wait=False, cancel_futures=True)
    return results


def run(definition, targets, preflight=False):
    wa.validate_definition(definition)
    started = now()
    cfg = wa.schedule_config(definition, targets[0])
    state = Path(definition['state_dir'])
    slot = started.replace(hour=17, minute=50, second=0, microsecond=0)
    first = datetime.fromisoformat(definition['schedule']['first_send_at'])
    kind = wa.report_kind(definition, started)
    reports = routes.selected(definition, targets)
    channels = list(reports)
    live, outcomes = state / 'live-status.json', {}
    with run_scope(definition['domain'], definition['channel_id'], cfg['windows_task_name'], started) as log:
        with runner_lock(state) as locked:
            def emit(channel, result):
                route = reports[channel]
                result = {'reason': '', **result, 'channel': route['channel'],
                          'chat_id': route['target']['chat_id'], 'included_grades': route['included_grades']}
                outcomes[channel] = result
                db = None
                try:
                    db = connect_ledger(channel_delivery.state_for(definition, route))
                    record_outcome(db, now().isoformat(), slot, route['channel'], result['status'], result['reason'])
                except Exception as exc:
                    log.event('channel_event_ledger_unavailable', channel=channel, reason=str(exc)[:400])
                finally:
                    if db is not None:
                        db.close()
                log.event('channel_outcome', report_id=channel, slot=slot.isoformat(), **result)
                log.outcome(channel, **result)

            def finish():
                # CLI fanout requires an integer exit code; detailed verdicts
                # remain in the per-channel ledger and shared run summary.
                log.exit_code = 0 if len(outcomes) == len(channels) and all(
                    item['status'] in CLEAN for item in outcomes.values()) else 1
                print(json.dumps({'slot': slot.isoformat(), 'channels': outcomes,
                                  'exit_code': log.exit_code}, ensure_ascii=False, default=str), flush=True)
                return log.exit_code

            try:
                if not reports:
                    log.event('no_enabled_report_routes', slot=slot.isoformat())
                    return finish()
                reason, status = '', 'prepared'
                if not locked:
                    reason, status = 'Process lock already held', 'blocked_parallel_run'
                elif not preflight and not definition['schedule']['enabled']:
                    reason = 'Schedule or target paused'
                elif not preflight and slot < first:
                    reason = 'Before the configured first daily slot'
                elif not preflight and not slot - timedelta(minutes=5) <= started < slot + timedelta(minutes=1):
                    reason, status = 'Outside 17:45 preparation / 17:50 send window; no catch-up', 'blocked_outside_slot'
                if reason:
                    for channel in channels:
                        emit(channel, {'status': status, 'reason': reason})
                    return finish()
                pending = {}
                for channel in channels:
                    try:
                        routes.initialize_state(definition, reports[channel])
                        prior = None if preflight else channel_delivery.existing_outcome(
                            definition, reports[channel], slot, kind)
                        if prior:
                            emit(channel, prior)
                        else:
                            pending[channel] = reports[channel]
                    except Exception as exc:
                        emit(channel, {'status': 'blocked_channel_ledger', 'reason': str(exc)[:1000]})
                if not pending:
                    return finish()
                wd.save(live, {'status': 'preparing', 'slot': slot.isoformat(), 'report_kind': kind,
                               'channels': list(pending), 'started_at': started.isoformat()})
                source = wa.prepare_source(definition, targets[0], state / 'shared-source', scheduled=not preflight)
                prepared = parallel_phase(pending, lambda _, route: channel_delivery.prepare_channel(
                    definition, route, source, kind, preflight), emit, 'blocked_channel_preparation',
                    None if preflight else slot - timedelta(minutes=1))
                ready = {}
                for channel, context in prepared.items():
                    if context['skip_delivery']:
                        try:
                            if not preflight:
                                channel_delivery.mark_absent(definition, reports[channel], slot, kind, source['evidence'])
                            emit(channel, {'status': 'skipped_no_source_rows',
                                           'reason': 'Complete audited source has no current channel post leads'})
                        except Exception as exc:
                            emit(channel, {'status': 'blocked_channel_ledger', 'reason': str(exc)[:1000]})
                    elif preflight:
                        emit(channel, {'status': 'prepared', 'reason': 'Read-only preflight', 'files': context['files']})
                    else:
                        ready[channel] = context
                if preflight or not ready:
                    return finish()
                if load_channel(wa.KEY) != definition:
                    raise ValueError('Canonical warning configuration changed')
                wu.publication(definition)
                if wu.history(definition, slot, scheduled=True)['id'] != source['evidence']['execution_id']:
                    raise ValueError('Newer warning producer replaced the prepared data')
                verify_bot(cfg)
                wd.unchanged(definition, source['root'] / 'revision-check', source['rev'])
                staged = parallel_phase(ready, lambda _, context: channel_delivery.stage_upload(context, slot),
                                        emit, 'blocked_channel_upload', slot - timedelta(seconds=15))
                if not staged:
                    return finish()
                wd.save(live, {'status': 'waiting_for_17_50', 'slot': slot.isoformat(), 'channels': list(staged)})
                while now() < slot - timedelta(seconds=15):
                    time.sleep(min(1, max(0, (slot - timedelta(seconds=15) - now()).total_seconds())))
                if load_channel(wa.KEY) != definition:
                    raise ValueError('Configuration paused or changed before send')
                if wu.history(definition, slot, scheduled=True)['id'] != source['evidence']['execution_id']:
                    raise ValueError('Producer started another execution before send')
                wd.unchanged(definition, source['root'] / 'send-revision-check', source['rev'])
                while now() < slot:
                    time.sleep(min(1, max(0, (slot - now()).total_seconds())))
                if now() >= slot + timedelta(minutes=1):
                    raise ValueError('Final shared source check exceeded the send window')
                results = parallel_phase(staged, lambda _, context: channel_delivery.send_channel(context, slot),
                                         emit, 'blocked_channel_delivery')
                for channel, result in results.items():
                    emit(channel, result)
                return finish()
            except Exception as exc:
                for channel in channels:
                    if channel not in outcomes:
                        emit(channel, {'status': 'blocked_before_send', 'reason': str(exc)[:1000]})
                return finish()
            finally:
                if locked:
                    live.unlink(missing_ok=True)
