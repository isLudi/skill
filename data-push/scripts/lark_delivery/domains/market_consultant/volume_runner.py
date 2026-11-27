"""Independently locked volume jobs with the KOC 17:20 retry window."""
from contextlib import closing
from datetime import datetime, timedelta
import json
from pathlib import Path
import time

from ...common import push_log
from ...core import catalog
from ...core.locks import runner_lock
from .delivery_ledger import connect_ledger, record_outcome
from .grade_bundle_source import fingerprint, save
from . import grade_bundle_delivery as delivery
from . import volume_adapter as adapter
from . import window


def run(definition, target, *, preflight=False):
    started = datetime.now(window.TZ)
    cfg = adapter.schedule_config(definition, target)
    component_id = definition['components'][0]['id']
    slot = window.active_slot(started, cfg, preflight=preflight)
    task = cfg['windows_task_name']
    with push_log.run_scope('market_consultant', definition['channel_id'], task, started) as log:
        if slot is None:
            log.outcome(component_id, 'outside_authorized_window', 'No active volume slot')
            log.exit_code = 0
            return 0
        state = Path(definition['state_dir'])/'slots'/slot.strftime('%Y%m%d-%H00')
        state.mkdir(parents=True, exist_ok=True)
        deadline = slot+timedelta(minutes=cfg['deadline_minute']+1)

        def time_guard():
            live = catalog.load_channel(cfg['channel_key'])
            if fingerprint(live) != fingerprint(definition) or not live['schedule']['enabled']:
                raise ValueError('Volume job was paused or its configuration changed')
            current = datetime.now(window.TZ)
            if not slot+timedelta(minutes=cfg['send_minute']) <= current < deadline:
                raise ValueError('Volume send window ended')

        with runner_lock(Path(definition['state_dir'])) as acquired:
            if not acquired:
                log.outcome(component_id, 'another_instance_active', 'Volume lock is held')
                log.exit_code = 0
                return 0
            with closing(connect_ledger(Path(definition['state_dir']))) as db:
                delivery.init(db)
                token = slot.isoformat()
                while datetime.now(window.TZ) < deadline:
                    try:
                        staged = db.execute('SELECT * FROM bundle_messages WHERE slot=?', (token,)).fetchall()
                        if len(staged) > 1:
                            raise ValueError('Multiple volume message claims for one slot')
                        if staged and not preflight:
                            result = delivery.send_staged(db, staged[0], time_guard)
                        else:
                            folder = state/('prepare-'+datetime.now(window.TZ).strftime('%H%M%S-%f'))
                            context = adapter.prepare(definition, target, state_dir=folder, slot=slot)
                            adapter.write_preview(context)
                            if preflight:
                                from .upstream import verify_bot
                                from ...common import im
                                verify_bot(cfg)
                                im.verify_sender_membership(target['chat_id'], definition['sender']['open_id'])
                                result = {'status':'preflight_ready','context_path':str(folder/'context.json')}
                            else:
                                result = delivery.stage_and_send(db, context, token, time_guard)
                    except Exception as exc:
                        result = {'status':'blocked_source_or_delivery',
                            'reason':type(exc).__name__+': '+str(exc)[:350]}
                    log.outcome(component_id, result['status'], result.get('reason',''),
                        message_id=result.get('message_id'))
                    record_outcome(db, datetime.now(window.TZ).isoformat(), slot, component_id,
                        result['status'], result.get('reason',''))
                    save(state/'last-run.json', {'slot':token, **result})
                    if result['status'] in {'sent_verified','preflight_ready'} or preflight:
                        code = 0 if result['status'] in {'sent_verified','preflight_ready'} else 1
                        log.exit_code = code
                        print(json.dumps(result, ensure_ascii=False), flush=True)
                        return code
                    next_check = window.next_check(datetime.now(window.TZ), slot, cfg)
                    if next_check >= deadline:
                        break
                    while datetime.now(window.TZ) < next_check:
                        time.sleep(min(20, max(.01, (next_check-datetime.now(window.TZ)).total_seconds())))
                log.exit_code = 1
                return 1
