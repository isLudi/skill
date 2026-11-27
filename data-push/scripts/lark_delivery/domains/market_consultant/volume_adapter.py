"""Reviewed channel volume reports using the shared producer and image template."""
from datetime import datetime
import hashlib
import html
from pathlib import Path

from ...core import catalog
from ...integrations.push_platform import shared_base_snapshot
from . import immediate, scheduler, volume_report as volume
from .grade_bundle_source import fingerprint, save
from .window import TZ

SCOPES = {
    'app_volume': ('APP', 'oc_9dc33c5731ce57c03d0589a2ac1d2e99', volume.RULE_APP),
    'outbound_volume': ('人工外呼', 'oc_6eb68afaf15aa7ca366a50704868aabc', volume.RULE_OUTBOUND),
}


def validate_definition(definition):
    scope = SCOPES.get(definition.get('channel_id'))
    if scope is None:
        raise ValueError('Unreviewed volume channel')
    channel, chat_id, rule = scope
    if (definition.get('domain') != 'market_consultant'
            or definition.get('adapter') != 'market-volume-v1' or definition['channel'] != channel
            or definition['channels'] != [channel]
            or len(definition['targets']) != 1
            or definition['targets'][0]['chat_id'] != chat_id
            or definition['sender'] != {'identity':'bot','name':'管家','open_id':'ou_f3907e865135732c15a1dfce27828411'}):
        raise ValueError('Unreviewed volume identity or target')
    spec, schedule = definition['volume_report'], definition['schedule']
    if definition['channel_id'] == 'outbound_volume' and (
            spec.get('source_values') != list(volume.OUTBOUND_RULE_CHANNELS)
            or spec.get('included_grades') != ['高一','高二','高三']):
        raise ValueError('Unreviewed outbound volume scope')
    if (spec['volume_table_id'] != 'tblGUCxgUTZPjv3c' or spec['channel_rule'] != rule
            or spec['period_rule'] != 'latest_available' or spec.get('include_abnormal') is not False
            or definition['source']['report_profile'] != 'volume'
            or definition['source']['base_token'] != 'PmpybDuXGaudYost6I3cTwChn3d'
            or definition['source']['raw_table_id'] != spec['volume_table_id']
            or definition['source']['base_token'] != spec['base_token'] or schedule['hours'] != [17]
            or schedule['prepare_minute'] != 20 or schedule['send_minute'] != 20
            or schedule['deadline_minute'] != 50 or schedule['retry_minutes'] != 2):
        raise ValueError('Unreviewed volume source or schedule')
    return definition


def schedule_config(definition, target):
    validate_definition(definition)
    if target not in definition['targets']:
        raise ValueError('Volume target is not registered')
    binding = catalog.market_volume_binding(definition['volume_report'])
    return {**definition['schedule'], 'domain':'market_consultant', 'channel_id':definition['channel_id'],
        'channel_key':'market_consultant/'+definition['channel_id'], 'target_id':target['id'],
        'chat_id':target['chat_id'], 'chat_name':target['display_name'], 'base_as':definition['base_identity'],
        'bot_name':definition['sender']['name'], 'bot_open_id':definition['sender']['open_id'],
        'state_dir':definition['state_dir'], 'upstream':binding,
        'volume_report':{**definition['volume_report'], 'upstream':binding}}


def prepare(definition, target, *, state_dir=None, slot=None, period=None, report_type='auto', **_unused):
    if report_type != 'auto':
        raise ValueError('Volume supports only its configured volume report')
    cfg = schedule_config(definition, target)
    source_slot = slot or immediate.latest_upstream_slot(datetime.now(TZ))
    evidence = scheduler.volume_upstream_ready(cfg, source_slot)
    publication = immediate.verify_publication(cfg)
    directory = Path(state_dir or definition['state_dir'])
    directory.mkdir(parents=True, exist_ok=True)
    import argparse
    records, audit = shared_base_snapshot(
        {'domain': 'market_consultant', 'kind': 'volume', 'base_token': definition['source']['base_token'],
         'table_id': definition['source']['raw_table_id'], 'identity': cfg['base_as'], 'fields': volume.VOLUME_FIELDS},
        {'execution_id': evidence['execution_id'], 'periods': evidence['periods'], 'total': evidence['total'],
         'binding': fingerprint(cfg['upstream'])},
        lambda: volume._read_table(definition['source']['base_token'], definition['source']['raw_table_id'],
                                   volume.VOLUME_FIELDS, argparse.Namespace(base_as=cfg['base_as'], timeout=60, max_pages=100)))
    periods = sorted({volume._text(row, '期次') for row in records})
    if (audit.get('has_more') is not False or audit.get('rev') is None
            or len(records) != evidence['total'] or periods != sorted(evidence['periods'])):
        raise ValueError('Volume Base snapshot differs from complete producer evidence')
    rule = definition['volume_report']['channel_rule']
    latest_period = volume.latest_period(records, rule)
    if period is not None and period != latest_period:
        raise ValueError('Volume period must match the latest available source period')
    period = latest_period
    rows, _channels, _dimensions = volume.aggregate_volume(records, period, rule)
    included = definition['volume_report'].get('included_grades')
    if included:
        rows = [row for row in rows if row['年级'] in included]
    image = directory/('app-volume.png' if definition['channel_id']=='app_volume' else 'outbound-volume.png')
    geometry = volume.render_image(rows, image)
    comparable = [row for row in rows if row['量级完成度'] is not None]
    slowest = min(comparable, key=lambda row: (row['量级完成度'],
        volume.GRADE_ORDER.get(row['年级'], len(volume.GRADE_ORDER)))) if comparable else None
    closing = f'请重点关注{slowest["年级"]}年级的量级进展。' if slowest else ''
    opening = '【'+definition['channel']+'渠道】进量进度如下，辛苦各位老师知悉 ❤️'
    component_id = definition['components'][0]['id']
    artifact = {'grade':definition['channel']+'渠道', 'path':str(image), 'component_ids':[component_id], 'reminders':[],
        'sha256':hashlib.sha256(image.read_bytes()).hexdigest(), **geometry}
    context = {'definition':definition, 'definition_sha256':fingerprint(definition), 'target':target,
        'directory':str(directory), 'period':period, 'section':'volume', 'component_ids':[component_id],
        'artifact_protocol':'market-volume-artifacts-v1', 'artifacts':[artifact], 'rows':rows,
        'opening':opening, 'closing':closing, 'message_title':opening,
        'snapshot':[evidence['dt'], evidence['hour']],
        'source':{'source_slot':source_slot.isoformat(), 'evidence':evidence, 'publication':publication,
            'read_audit':audit, 'upstream_binding_sha256':fingerprint(cfg['upstream'])},
        'outcomes':{component_id:{'status':'prepared','channel':definition['channel']}}}
    save(directory/'context.json', context)
    return context


def write_preview(context):
    directory = Path(context['directory'])
    image = Path(context['artifacts'][0]['path']).name
    text = f"{context['opening']}\n\n![{context['definition']['channel']}渠道进量进度]({image})\n\n推送期次为{context['period']}\n\n{context['closing']}"
    (directory/'message-preview.md').write_text(text+'\n', encoding='utf-8')
    page = directory/'message-preview.html'
    page.write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8">'
        '<style>body{margin:24px;background:#f2f3f5;font:17px/1.65 Microsoft YaHei;color:#1f2329}'
        'main{max-width:1080px;margin:auto;background:white;padding:24px;border-radius:12px}'
        'img{display:block;width:100%;margin:12px 0}</style><main><p>'+html.escape(context['opening'])+
        '</p><img src="'+image+'"><p>推送期次为'+html.escape(context['period'])+'</p><p>'+
        html.escape(context['closing'])+'</p></main></html>', encoding='utf-8')
    return {'html':str(page), 'image':context['artifacts'][0]['path']}


def native_post(context, image_keys):
    if len(image_keys) != 1:
        raise ValueError('Volume requires exactly one image')
    content = [[{'tag':'img','image_key':image_keys[0]}],
        [{'tag':'text','text':'推送期次为'+context['period']}]]
    if context['closing']:
        content.append([{'tag':'text','text':context['closing']}])
    return {'zh_cn':{'title':context['opening'], 'content':content}}


def guard(context):
    definition = catalog.load_channel('market_consultant/'+context['definition']['channel_id'])
    if fingerprint(definition) != context['definition_sha256']:
        raise ValueError('Volume definition changed after preparation')
    cfg = schedule_config(definition, context['target'])
    if fingerprint(cfg['upstream']) != context['source']['upstream_binding_sha256']:
        raise ValueError('Approved volume binding changed after preparation')
    slot = datetime.fromisoformat(context['source']['source_slot'])
    latest = scheduler.volume_upstream_ready(cfg, slot)
    if latest['execution_id'] != context['source']['evidence']['execution_id']:
        raise ValueError('Volume execution changed after preparation')
    immediate.verify_publication(cfg)
    volume.assert_current_revisions({'base_token':definition['source']['base_token'],
        'revision_sources':[{'table_id':definition['source']['raw_table_id'],'field':'期次',
            'rev':context['source']['read_audit']['rev']}]}, cfg)


def schedule(definition, target, *, preflight=False):
    from .volume_runner import run
    return run(definition, target, preflight=preflight)


def dry_run(context):
    guard(context)


def send_backfill(definition, target, request_id, slot, *, preflight=False):
    from .volume_backfill import run
    return run(definition, target, request_id, slot, preflight=preflight)
