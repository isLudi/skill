"""Independent preparation, preview, claims and delivery for each channel card."""
from datetime import datetime
import json

from ...core.registry import adapter_for
from .channels.grade_compact import TZ
from .delivery_ledger import record_outcome
from . import grade_bundle_delivery as delivery

CLEAN = {'sent_verified','duplicate_suppressed','prepared','skipped_no_source_rows','skipped_no_eligible_rows'}


def round_once(definition,target,db,state,slot,token,time_guard,preflight,log):
    adapter = adapter_for(definition)
    delivery.init(db)
    outcomes,settled = {},set()
    aliases = {}
    for component in definition['components']:
        for identifier in [component['id'], *component.get('source_component_ids',[])]:
            aliases[identifier] = component['id']
    if not preflight:
        for row in db.execute('SELECT * FROM bundle_messages WHERE slot=?',(token,)).fetchall():
            identifiers = {aliases[identifier] for identifier in json.loads(row[5]) if identifier in aliases}
            try:
                result = delivery.send_staged(db,row,time_guard)
            except Exception as exc:
                result = {'status':'blocked_delivery','reason':type(exc).__name__+': '+str(exc)[:300]}
            for identifier in identifiers:
                outcomes[identifier] = result
                if result['status']=='sent_verified':
                    settled.add(identifier)
    claimed = set() if preflight else {aliases[row[0]] for row in
        db.execute('SELECT channel FROM deliveries WHERE slot=?',(token,)).fetchall() if row[0] in aliases}
    contexts = []
    for component in definition['components']:
        identifier = component['id']
        if identifier in settled:
            continue
        if identifier in claimed:
            if identifier not in outcomes:
                outcomes[identifier] = {'status':'blocked_delivery','channel':component['label'],
                    'reason':'Existing claim has no recoverable staged message'}
            continue
        folder = state/'channels'/identifier/('prepare-'+datetime.now(TZ).strftime('%Y%m%d-%H%M%S-%f'))
        try:
            time_guard()
            context = adapter.prepare(definition,target,state_dir=folder,slot=slot,component_ids=[identifier])
            adapter.write_preview(context)
            contexts.append(str(folder/'context.json'))
            outcomes.update(context['outcomes'])
        except Exception as exc:
            outcomes[identifier] = {'status':'blocked_prepare','channel':component['label'],
                                    'reason':type(exc).__name__+': '+str(exc)[:300]}
            continue
        if context['artifacts'] and not preflight:
            try:
                outcomes[identifier] = delivery.stage_and_send(db,context,token,time_guard)
            except Exception as exc:
                outcomes[identifier] = {'status':'blocked_delivery','channel':component['label'],
                                        'reason':type(exc).__name__+': '+str(exc)[:300]}
    for identifier,result in outcomes.items():
        log.outcome(identifier,result['status'],result.get('reason',''),message_id=result.get('message_id'))
        log.outcomes[identifier]['message_id'] = result.get('message_id')
        record_outcome(db,datetime.now(TZ).isoformat(),slot or datetime.now(TZ),identifier,
                       result['status'],result.get('reason',''))
    return {'outcomes':outcomes,'context_path':contexts[0] if contexts else None,'context_paths':contexts,
            'preflight':preflight,'status':'complete' if all(result['status'] in CLEAN for result in outcomes.values())
            else 'needs_attention'}
