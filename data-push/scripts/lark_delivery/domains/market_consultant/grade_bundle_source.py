"""Full Base verification against a pinned SCHEDULE; no automatic release adoption."""
from datetime import datetime, timedelta
import json
from pathlib import Path
from types import SimpleNamespace

from ...common.base import _fetch_view_records
from ...core import catalog
from . import immediate, reporting, scheduler, raw_source_audit
from .channels.grade_compact import TZ, business_period


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str)+'\n', encoding='utf-8')


def fingerprint(definition):
    import hashlib
    return hashlib.sha256(json.dumps(definition, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


def schedule_config(definition, target):
    pin = catalog.load_shared_release_pin()
    u = definition['upstream']
    for key in ['project_id','folder','menu_id','task_name','task_id','nezha_task_id','schedule_id','owner']:
        if u[key] != pin['upstream'][key]:
            raise ValueError('Bundle upstream identity differs from shared release')
    return {**definition['schedule'], 'domain': 'market_consultant', 'channel_id': definition['channel_id'],
        'channel_key': 'market_consultant/'+definition['channel_id'], 'target_id': target['id'],
        'channels': definition['channels'], 'chat_id': target['chat_id'], 'chat_name': target['display_name'],
        'bot_name': definition['sender']['name'], 'bot_open_id': definition['sender']['open_id'],
        'base_as': definition['base_identity'], 'state_dir': definition['state_dir'],
        'raw_table_id': definition['source']['raw_table_id'],
        'upstream': {**pin['upstream'], 'channel_mapping_version': pin['channel_mapping_version']}}


def source_slot(at, slot=None):
    if slot is None:
        return immediate.latest_upstream_slot(at)
    if slot.hour not in {14,19} or slot.minute or slot.second:
        raise ValueError('Bundle scheduled slot must be exactly 14:00 or 19:00')
    return slot.replace(hour={14:13,19:17}[slot.hour])


def read(definition, target, directory, slot=None):
    at = datetime.now(TZ)
    cfg = schedule_config(definition,target)
    selected_slot = source_slot(at,slot)
    evidence = scheduler.upstream_ready(cfg,selected_slot)
    publication = immediate.verify_publication(cfg)
    period = business_period(at)
    if period not in evidence['periods']:
        raise ValueError('Calendar period is absent from the successful source audit')
    contract = json.loads((catalog.CONFIG_ROOT/definition['source']['field_contract']).read_text(encoding='utf-8'))
    audit = {}
    rows = _fetch_view_records({'base_token': definition['source']['base_token'], 'table_id': cfg['raw_table_id'], 'view_id': ''},
        SimpleNamespace(base_as='user',timeout=60,max_pages=50), list(contract['field_mapping'].values()),
        temp_prefix='.market-grade-bundle-', audit=audit)
    actual = raw_source_audit.audit(rows,contract)
    expected = {'schema_version':'market2lark-two-period-audit-v1','field_count':45,'row_count':evidence['total'],
                'numeric_hash_decimal_places':6,'periods':evidence['periods']}
    if actual != expected or audit.get('has_more') is not False or audit.get('rev') is None:
        raise ValueError('Bundle Base full field audit differs from successful upstream')
    snapshot_at = datetime.strptime(str(evidence['dt'])+f"{evidence['hour']:02d}",'%Y%m%d%H').replace(tzinfo=TZ)
    if not timedelta(0) <= at-snapshot_at <= timedelta(hours=definition['source']['max_snapshot_age_hours']):
        raise ValueError('Bundle source snapshot is not fresh')
    source = {'period':period,'source_slot':selected_slot.isoformat(),'evidence':evidence,'read_audit':audit,
              'snapshot':[evidence['dt'],evidence['hour']],'publication':publication}
    save(Path(directory)/'source-receipt.json', source)
    return rows,source


def guard(context):
    definition = catalog.load_channel('market_consultant/'+context['definition']['channel_id'])
    if fingerprint(definition) != context['definition_sha256']:
        raise ValueError('Bundle configuration changed after preparation')
    at = datetime.now(TZ)
    snapshot_at = datetime.strptime(str(context['snapshot'][0])+f"{int(context['snapshot'][1]):02d}",'%Y%m%d%H').replace(tzinfo=TZ)
    if business_period(at) != context['period'] or not timedelta(0) <= at-snapshot_at <= timedelta(hours=7):
        raise ValueError('Bundle calendar or source freshness changed')
    cfg = schedule_config(definition,context['target'])
    directory = scheduler.operator('list-execution-history',cfg,'--limit','12')
    history = json.loads((directory/'history.json').read_text(encoding='utf-8'))
    selected = scheduler.validate_history(history,cfg,datetime.fromisoformat(context['source']['source_slot']))
    if selected['id'] != context['source']['evidence']['execution_id']:
        raise ValueError('Bundle upstream execution changed')
    reporting.assert_current_revision({'coords':{'base_token':definition['source']['base_token']},
        'raw_table_id':definition['source']['raw_table_id'],'raw_read_audit':context['source']['read_audit']},cfg)
