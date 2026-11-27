"""Full Base verification against a pinned SCHEDULE; no automatic release adoption."""
from datetime import datetime, timedelta
import json
from pathlib import Path
from types import SimpleNamespace

from ...common.base import _fetch_view_records
from ...core import catalog
from ...integrations.push_platform import shared_base_snapshot
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
    if definition.get('adapter') == 'market-volume-v1':
        from .volume_adapter import schedule_config as volume_config
        return volume_config(definition, target)
    return {**definition['schedule'], 'domain': 'market_consultant', 'channel_id': definition['channel_id'],
        'channel_key': 'market_consultant/'+definition['channel_id'], 'target_id': target['id'],
        'channels': definition['channels'], 'chat_id': target['chat_id'], 'chat_name': target['display_name'],
        'bot_name': definition['sender']['name'], 'bot_open_id': definition['sender']['open_id'],
        'base_as': definition['base_identity'], 'state_dir': definition['state_dir'],
        'raw_table_id': definition['source']['raw_table_id'],
        'upstream': catalog.market_lead_binding(definition)}


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
    expected = {'schema_version':'market2lark-two-period-audit-v1','field_count':45,'row_count':evidence['total'],
                'numeric_hash_decimal_places':6,'periods':evidence['periods']}
    fields = list(contract['field_mapping'].values())
    coords = {'base_token': definition['source']['base_token'], 'table_id': cfg['raw_table_id'], 'view_id': ''}

    def load_snapshot():
        audit = {}
        rows = _fetch_view_records(coords, SimpleNamespace(base_as='user',timeout=60,max_pages=50), fields,
                                   temp_prefix='.market-grade-bundle-', audit=audit)
        if (raw_source_audit.audit(rows,contract) != expected or audit.get('has_more') is not False
                or type(audit.get('rev')) is not int):
            raise ValueError('Bundle Base full field audit differs from successful upstream')
        return rows, audit

    rows, audit = shared_base_snapshot(
        {'domain': 'market_consultant', 'coords': coords, 'identity': 'user', 'fields': fields},
        {'execution_id': evidence['execution_id'], 'audit': expected,
         'binding': fingerprint(cfg['upstream']), 'contract': fingerprint(contract)}, load_snapshot)
    if raw_source_audit.audit(rows, contract) != expected:
        raise ValueError('Shared bundle snapshot differs from the current source audit')
    snapshot_at = datetime.strptime(str(evidence['dt'])+f"{evidence['hour']:02d}",'%Y%m%d%H').replace(tzinfo=TZ)
    if not timedelta(0) <= at-snapshot_at <= timedelta(hours=definition['source']['max_snapshot_age_hours']):
        raise ValueError('Bundle source snapshot is not fresh')
    source = {'period':period,'source_slot':selected_slot.isoformat(),'evidence':evidence,'read_audit':audit,
              'snapshot':[evidence['dt'],evidence['hour']],'publication':publication,
              'upstream_binding_sha256':fingerprint(cfg['upstream'])}
    save(Path(directory)/'source-receipt.json', source)
    return rows,source


def guard(context):
    if context['definition'].get('adapter') == 'market-volume-v1':
        from .volume_adapter import guard as volume_guard
        return volume_guard(context)
    definition = catalog.load_channel('market_consultant/'+context['definition']['channel_id'])
    if fingerprint(definition) != context['definition_sha256']:
        raise ValueError('Bundle configuration changed after preparation')
    at = datetime.now(TZ)
    if context.get('grade9_role') is not None or context.get('grade9_preview_only'):
        from .grade9_daily_prepare import validate_context
        validate_context(context, definition, at)
    if context.get('daily_policy_date') is not None and context['daily_policy_date'] != at.date().isoformat():
        raise ValueError('Daily KOC standards changed at midnight; prepare a fresh card')
    snapshot_at = datetime.strptime(str(context['snapshot'][0])+f"{int(context['snapshot'][1]):02d}",'%Y%m%d%H').replace(tzinfo=TZ)
    if business_period(at) != context['period'] or not timedelta(0) <= at-snapshot_at <= timedelta(hours=7):
        raise ValueError('Bundle calendar or source freshness changed')
    cfg = schedule_config(definition,context['target'])
    prepared_binding = context['source'].get('upstream_binding_sha256')
    if prepared_binding is not None and prepared_binding != fingerprint(cfg['upstream']):
        raise ValueError('Approved bundle upstream binding changed after preparation')
    directory = scheduler.operator('list-execution-history',cfg,'--limit','12')
    history = json.loads((directory/'history.json').read_text(encoding='utf-8'))
    selected = scheduler.validate_history(history,cfg,datetime.fromisoformat(context['source']['source_slot']))
    if selected['id'] != context['source']['evidence']['execution_id']:
        raise ValueError('Bundle upstream execution changed')
    reporting.assert_current_revision({'coords':{'base_token':definition['source']['base_token']},
        'raw_table_id':definition['source']['raw_table_id'],'raw_read_audit':context['source']['read_audit']},cfg)
