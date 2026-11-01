"""Four independent group jobs; exact 14/19 slots and isolated channel recovery."""
from contextlib import closing
from datetime import datetime, timedelta
import json
from pathlib import Path
import re
import time

from ...common import push_log
from ...common.runtime import ensure_console_streams
from ...core import catalog
from ...core.registry import adapter_for
from ...core.locks import runner_lock
from .channels.grade_compact import TZ, business_period, scheduled_report_type
from .delivery_ledger import connect_ledger, record_outcome
from . import grade_bundle_delivery as delivery
from . import grade_bundle_source as source

CLEAN = {'sent_verified','skipped_no_eligible_rows','skipped_no_source_rows','prepared'}


def round_once(definition,target,db,state,slot,token,time_guard,preflight,log):
    adapter=adapter_for(definition)
    delivery.init(db)
    settled, outcomes = set(), {}
    for row in db.execute('SELECT * FROM bundle_messages WHERE slot=?',(token,)).fetchall():
        try:
            if preflight:
                continue
            result = delivery.send_staged(db,row,time_guard)
            component_ids = json.loads(row[5])
            for component_id in component_ids:
                outcomes[component_id] = result
                if result['status'] == 'sent_verified':
                    settled.add(component_id)
        except Exception as exc:
            for component_id in json.loads(row[5]):
                outcomes[component_id] = {'status':'blocked_delivery','reason':type(exc).__name__+': '+str(exc)[:300]}
    claimed = {row[0] for row in db.execute('SELECT channel FROM deliveries WHERE slot=?',(token,)).fetchall()}
    pending = [c['id'] for c in definition['components'] if c['id'] not in settled and c['id'] not in claimed]
    context_path = None
    if pending:
        pointer = state/'latest-preparation.json'
        context = None
        if pointer.is_file():
            previous = json.loads(pointer.read_text(encoding='utf-8'))
            candidate = Path(previous['context'])
            if candidate.is_file() and datetime.now(TZ).timestamp()-candidate.stat().st_mtime < 600:
                cached = json.loads(candidate.read_text(encoding='utf-8'))
                if (cached['definition_sha256'] == source.fingerprint(definition)
                        and cached['section'] == scheduled_report_type(datetime.now(TZ))
                        and set(cached['outcomes']) == set(pending)):
                    context = cached
        if context is None:
            folder = state/('prepare-'+datetime.now(TZ).strftime('%Y%m%d-%H%M%S-%f'))
            context = adapter.prepare(definition,target,state_dir=folder,slot=slot,component_ids=pending)
            adapter.write_preview(context)
            source.save(pointer,{'context':str(folder/'context.json')})
        context_path = str(Path(context['directory'])/'context.json')
        outcomes.update(context['outcomes'])
        if context['artifacts'] and not preflight:
            result = delivery.stage_and_send(db,context,token,time_guard)
            for component_id in context['component_ids']:
                outcomes[component_id] = result
    for component_id,result in outcomes.items():
        log.outcome(component_id,result['status'],result.get('reason',''),message_id=result.get('message_id'))
        log.outcomes[component_id]['message_id'] = result.get('message_id')
        record_outcome(db,datetime.now(TZ).isoformat(),slot or datetime.now(TZ),component_id,
                       result['status'],result.get('reason',''))
    return {'outcomes':outcomes,'context_path':context_path,'preflight':preflight,
            'status':'complete' if all(result['status'] in CLEAN for result in outcomes.values()) else 'needs_attention'}


def run(definition,target,*,request_id=None,preflight=False):
    ensure_console_streams()
    started = datetime.now(TZ)
    schedule = definition['schedule']
    if request_id is not None and not re.fullmatch(r'[A-Za-z0-9_-]{8,80}',request_id):
        raise ValueError('An explicit stable immediate request ID is required')
    if request_id is None:
        if not preflight and not schedule['enabled']:
            return 0
        candidates = [started.replace(hour=hour,minute=0,second=0,microsecond=0) for hour in schedule['hours']]
        slots = [slot for slot in candidates if slot <= started < slot+timedelta(minutes=51)]
        if len(slots) != 1:
            raise ValueError('Outside the authorized 14:00/19:00 bundle window')
        slot = slots[0]
        if not preflight and slot < datetime.fromisoformat(schedule['first_send_at']):
            return 0
        token = slot.isoformat()
        state = Path(definition['state_dir'])/'slots'/slot.strftime('%Y%m%d-%H00')
        deadline = slot+timedelta(minutes=51)
    else:
        slot,token = None,'now:'+request_id
        state = Path(definition['state_dir'])/'immediate'/request_id
        deadline = started+timedelta(minutes=10)
    state.mkdir(parents=True,exist_ok=True)

    def time_guard():
        current = datetime.now(TZ)
        live = catalog.load_channel('market_consultant/'+definition['channel_id'])
        if source.fingerprint(live) != source.fingerprint(definition):
            raise ValueError('Bundle config changed; stop this exact attempt')
        if not started <= current < deadline:
            raise ValueError('Bundle send window or immediate request expired')
        if slot is not None and (not live['schedule']['enabled'] or business_period(current) != business_period(slot)):
            raise ValueError('Bundle paused or business calendar changed')

    task = schedule['windows_task_name'] + ('-Immediate' if request_id else '')
    with push_log.run_scope('market_consultant',definition['channel_id'],task,started) as log:
        with runner_lock(Path(definition['state_dir'])) as acquired:
            if not acquired:
                raise ValueError('Another instance owns this exact bundle group')
            with closing(connect_ledger(Path(definition['state_dir']))) as db:
                db.execute('CREATE TABLE IF NOT EXISTS bundle_request_bindings (token TEXT PRIMARY KEY,period TEXT,section TEXT)')
                db.execute('INSERT OR IGNORE INTO bundle_request_bindings VALUES (?,?,?)',
                    (token,business_period(started),scheduled_report_type(started)))
                db.commit()
                binding = db.execute('SELECT period,section FROM bundle_request_bindings WHERE token=?',(token,)).fetchone()
                if binding != (business_period(started),scheduled_report_type(started)):
                    raise ValueError('An existing request cannot switch business period or report section')
                attempt,code = 0,1
                while datetime.now(TZ) < deadline:
                    attempt += 1
                    log.event('started' if attempt == 1 else 'retry',slot=token,attempt=attempt)
                    try:
                        result = round_once(definition,target,db,state,slot,token,time_guard,preflight,log)
                        result.update(at=datetime.now(TZ).isoformat(),slot=token,channel_id=definition['channel_id'])
                        code = 0 if result['status'] == 'complete' else 1
                    except Exception as exc:
                        result = {'status':'blocked_source_or_delivery','reason':type(exc).__name__+': '+str(exc)[:350],
                                  'at':datetime.now(TZ).isoformat(),'slot':token,'outcomes':{}}
                        log.outcome('shared_source', 'blocked_source',result['reason'])
                    source.save(state/'last-run.json',result)
                    if not code or preflight or request_id:
                        log.exit_code = code
                        print(json.dumps(result,ensure_ascii=False,default=str),flush=True)
                        return code
                    next_try = slot+timedelta(minutes=2*(int((datetime.now(TZ)-slot).total_seconds()//120)+1))
                    if next_try >= deadline:
                        break
                    while datetime.now(TZ) < next_try:
                        time.sleep(min(20,max(.01,(next_try-datetime.now(TZ)).total_seconds())))
                log.exit_code = 1
                return 1
