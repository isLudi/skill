"""Department-owned adapter for the reviewed daily channel comparison broadcast."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from pathlib import Path
import uuid

from . import warning_data as wd, warning_upstream as wu
from .warning_mentions import resolve
from .upstream import verify_bot

KEY = 'market_consultant/supervisor_koc_zhoushuai_warning'


def validate_definition(definition):
    if (definition.get('domain') != 'market_consultant'
            or definition.get('channel_id') != 'supervisor_koc_zhoushuai_warning'
            or definition.get('channel') != 'KOC-周帅数学'
            or definition.get('channels') != ['KOC-周帅数学']
            or definition.get('adapter') != 'market-channel-warning-v1'):
        raise ValueError('Unreviewed warning adapter/channel identity')
    s, report, upstream = definition['schedule'], definition['report'], definition['upstream']
    first = datetime.fromisoformat(s['first_send_at'])
    if (s.get('kind') != 'daily_once' or s.get('hours') != [17] or s.get('prepare_minute') != 45
            or s.get('send_minute') != 50 or s.get('deadline_minute') != 50 or s.get('retry_minutes') != 0
            or s.get('timezone') != 'Asia/Shanghai'
            or s.get('windows_task_name') != 'Codex-Lark-Market-KOC-Zhoushuai-Warning-Push'
            or first.tzinfo is None or first.utcoffset().total_seconds() != 28800
            or (first.hour, first.minute, first.second, first.microsecond) != (17,50,0,0)):
        raise ValueError('Warning schedule must prepare 17:45, send once 17:50 without catch-up')
    if (report.get('period_rule') != 'natural_week_friday'
            or report.get('process_weekdays') != [0,1,2,3] or report.get('result_weekdays') != [4,5,6]
            or report.get('included_grades') != ['高一','高二','高三']
            or report.get('process_metric_order') != ['first_call','five_min','frequency']
            or report.get('process_reminder_metric') != 'five_min' or report.get('result_reminder_metric') != 'unit'):
        raise ValueError('Warning business scope, metric order or weekday policy changed')
    source = definition['source']
    if (source.get('base_token') != 'PmpybDuXGaudYost6I3cTwChn3d'
            or source.get('raw_table_id') != 'tblaeYJ6N0DHG449'
            or source.get('report_profile') != 'supervisor-channel-warning'
            or source.get('reminder_rule') != 'all_current_supervisors_above_full_channel_team'
            or definition.get('base_identity') != 'user' or definition.get('verification_identity') != 'bot'
            or definition['sender'] != {'identity': 'bot', 'name': '管家', 'open_id': 'ou_f3907e865135732c15a1dfce27828411'}
            or len(definition['targets']) != 1
            or definition['targets'][0]['chat_id'] != 'oc_6f06cad338d520a89e1607a18592e56b'):
        raise ValueError('Warning source, target or identity changed')
    expected = {'project_id': 308, 'folder': '吕帅', 'menu_id': 104255, 'task_name': 'market2lark_warning',
                'task_id': 47889, 'nezha_task_id': 67653, 'schedule_id': 55203, 'owner': 'lvshuai01',
                'log_protocol': 'warning_two_period_create_then_delete_v1', 'scheduled_time': '17:10:00'}
    if any(upstream.get(k) != v for k, v in expected.items()):
        raise ValueError('Warning producer identity or protocol changed')
    return definition


def schedule_config(definition, target):
    validate_definition(definition)
    return {**deepcopy(definition['schedule']), **deepcopy(definition['report']),
            'domain': definition['domain'], 'channel_id': definition['channel_id'], 'channel_key': KEY,
            'target_id': target['id'], 'chat_id': target['chat_id'], 'chat_name': target['display_name'],
            'bot_name': definition['sender']['name'], 'bot_open_id': definition['sender']['open_id'],
            'base_as': definition['base_identity'], 'state_dir': definition['state_dir'],
            'raw_table_id': definition['source']['raw_table_id'],
            'report_profile': definition['source']['report_profile'],
            'channels': deepcopy(definition['channels']), 'upstream': deepcopy(definition['upstream'])}


def report_kind(definition, day):
    return 'process' if day.weekday() in definition['report']['process_weekdays'] else 'result'


def prepare(definition, target, *, channel=None, report_type='auto', state_dir=None,
            period=None, allow_period_override=False, strict_mentions=True, scheduled=False):
    validate_definition(definition)
    if channel not in (None, definition['channel']) or period or allow_period_override or not strict_mentions:
        raise ValueError('Warning preview cannot redirect source, period or reminder policy')
    day = datetime.now(wu.TZ)
    kind = report_kind(definition, day) if report_type == 'auto' else report_type
    if kind not in {'process','result'} or scheduled and kind != report_kind(definition, day):
        raise ValueError('Unsupported warning report selection')
    root = Path(state_dir or definition['state_dir']) / (kind + '-' + uuid.uuid4().hex[:12])
    root.mkdir(parents=True, exist_ok=True)
    verify_bot(schedule_config(definition, target))
    evidence = wu.ready(definition, day, scheduled=scheduled)
    rows, rev = wd.read_all(definition, root / 'source', evidence['audit'])
    data = wd.aggregate(definition, target, rows, rev, evidence, kind)
    wd.save(root / 'upstream_evidence.json', evidence)
    context = {'definition': definition, 'target': target, 'root': root, 'kind': kind,
               'evidence': evidence, 'source_rev': rev,
               'period': max(evidence['audit']['periods']), 'skip_delivery': data is None}
    if data is not None:
        wd.save(root / 'computed_metrics.json', data)
        metric = 'five_min' if kind == 'process' else 'unit'
        context.update(data=data, mentions=resolve(data, metric, root))
    return context


def write_preview(context):
    if context['skip_delivery']:
        return {'status': 'skipped_no_source_rows', 'evidence': str(context['root'] / 'upstream_evidence.json')}
    if context['kind'] == 'process':
        from .warning_process_render import render_preview
        image_name = 'channel-process-preview.png'
    else:
        from .warning_conversion_render import render_preview
        image_name = 'channel-conversion-preview.png'
    receipt = render_preview(context['data'], context['root'], context['mentions'])
    context.update(receipt=receipt, image=context['root'] / image_name,
                   markdown=(context['root'] / 'message-preview.md').read_text(encoding='utf-8'),
                   idempotency_key='warning-preview-' + receipt['image_sha256'][:32])
    return {'image': str(context['image']), 'html': str(context['root'] / 'message-preview.html'),
            'markdown': str(context['root'] / 'message-preview.md'), 'receipt': str(context['root'] / 'preview_receipt.json')}


def schedule(definition, target, preflight=False):
    from .warning_delivery import run
    return run(definition, target, preflight=preflight)
