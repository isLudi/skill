"""Explicit outbound backfills sharing the scheduled lock and slot claim."""
from contextlib import closing
from datetime import datetime, timedelta
import json
from pathlib import Path
import re

from ...common import push_log
from ...core import catalog
from ...core.locks import runner_lock
from . import grade_bundle_delivery as delivery
from . import immediate, volume_adapter as adapter
from .delivery_ledger import connect_ledger
from .grade_bundle_source import fingerprint, save
from .window import TZ


def run(definition, target, request_id, slot, *, preflight=False):
    adapter.validate_definition(definition)
    if definition['channel_id'] != 'outbound_volume' or target not in definition['targets']:
        raise ValueError('Backfill is registered only for the outbound target')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', request_id):
        raise ValueError('Invalid backfill request ID')
    if slot.tzinfo is None or slot.utcoffset() != timedelta(hours=8):
        raise ValueError('Backfill slot requires an explicit +08:00 offset')
    slot = slot.astimezone(TZ)
    if (slot.hour != 17 or slot.minute or slot.second or slot.microsecond
            or slot + timedelta(minutes=20) < datetime.fromisoformat(definition['schedule']['first_send_at'])):
        raise ValueError('Backfill requires a registered 17:00 scheduled slot')
    started = datetime.now(TZ)
    if started < slot + timedelta(minutes=51):
        raise ValueError('Backfill requires an expired scheduled window')
    state = Path(definition['state_dir'])
    token = slot.isoformat()
    folder = state/'backfill'/request_id
    binding = {'slot': token, 'target': target['id'], 'request_id': request_id}
    task = definition['schedule']['windows_task_name']+'-Backfill'
    with push_log.run_scope('market_consultant', 'outbound_volume', task, started) as log:
        with runner_lock(state) as acquired:
            if not acquired:
                raise RuntimeError('Outbound volume runner is active')
            binding_path = folder/'request.json'
            if binding_path.exists() and json.loads(binding_path.read_text(encoding='utf-8')) != binding:
                raise ValueError('Backfill request ID is already bound to another slot or target')
            save(binding_path, binding)
            with closing(connect_ledger(state)) as db:
                delivery.init(db)
                # Immediate claims use another key. Refuse a second send for the same producer cycle.
                for path, in db.execute("SELECT context_path FROM bundle_messages WHERE slot LIKE 'now:%'"):
                    prior = json.loads(Path(path).read_text(encoding='utf-8'))
                    if prior['source']['source_slot'] == token and prior['target']['chat_id'] == target['chat_id']:
                        raise ValueError('An immediate claim already exists for this outbound source slot')
                staged = db.execute('SELECT * FROM bundle_messages WHERE slot=?', (token,)).fetchall()
                if len(staged) > 1:
                    raise ValueError('Multiple outbound claims for one scheduled slot')

                def time_guard():
                    current = datetime.now(TZ)
                    if not started <= current < started + timedelta(minutes=10):
                        raise ValueError('Backfill preparation expired')
                    if fingerprint(catalog.load_channel('market_consultant/outbound_volume')) != fingerprint(definition):
                        raise ValueError('Outbound configuration changed during backfill')
                    if immediate.latest_upstream_slot(current) != slot:
                        raise ValueError('Backfill source slot is no longer the latest producer cycle')

                time_guard()
                if staged:
                    context = json.loads(Path(staged[0][4]).read_text(encoding='utf-8'))
                else:
                    context = adapter.prepare(definition, target, state_dir=folder, slot=slot)
                    adapter.write_preview(context)
                snapshot = datetime.strptime(str(context['snapshot'][0])+f"{int(context['snapshot'][1]):02d}", '%Y%m%d%H').replace(tzinfo=TZ)
                if not timedelta(0) <= started-snapshot <= timedelta(hours=7):
                    raise ValueError('Backfill snapshot is stale')
                if preflight:
                    adapter.guard(context)
                    result = {'status': 'preflight_ready', 'message_sent': False,
                              'context_path': str(Path(context['directory'])/'context.json')}
                else:
                    result = delivery.stage_and_send(db, context, token, time_guard)
                save(folder/'result.json', {**binding, **result})
                log.outcome('outbound_volume', result['status'], result.get('reason', ''),
                            message_id=result.get('message_id'))
                log.exit_code = 0 if result['status'] in {'sent_verified', 'preflight_ready'} else 1
                print(json.dumps({**binding, **result}, ensure_ascii=False), flush=True)
                return log.exit_code
