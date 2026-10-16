"""Independent APP and Bilibili supervisor/advisor message components."""
from __future__ import annotations

import base64
import hashlib
import html
import json
from pathlib import Path

from ...core import catalog
from .channels import app_grade_9 as policy

KEY = 'market_consultant/app_grade_9'
SUPERVISOR_KEY = 'market_consultant/supervisor_yafei_grade_9'
BILIBILI_ADVISOR_KEY = 'market_consultant/supervisor_yafei_grade_9_advisor'
CHANNELS = ('app', 'B站信息流-亚飞')
WEEKEND_ORDER = ('supervisor_result', 'advisor_result', 'supervisor_process', 'advisor_process')
WEEKDAY_ORDER = ('supervisor_process', 'advisor_process')


def validate_definition(definition):
    from . import adapter
    adapter.validate_definition(definition)
    sequence = definition.get('delivery_sequence', {})
    if (definition['channel_id'] != 'app_grade_9'
            or sequence.get('stage') not in {'preview_only', 'scheduled'}
            or sequence.get('supervisor_channel_ref') != SUPERVISOR_KEY
            or sequence.get('bilibili_advisor_channel_ref') != BILIBILI_ADVISOR_KEY
            or tuple(sequence.get('channel_order', ())) != CHANNELS
            or sequence.get('failure_policy') != 'independent_messages'
            or tuple(sequence.get('weekend_order', ())) != WEEKEND_ORDER
            or tuple(sequence.get('weekday_order', ())) != WEEKDAY_ORDER):
        raise ValueError('初三双渠道消息编排配置超出已确认范围')


def delegated_channels(cfg, channels):
    """Legacy tasks retain their ledgers and delegate only this exact group."""
    if cfg.get('channel_key') not in {SUPERVISOR_KEY, BILIBILI_ADVISOR_KEY}:
        return channels
    definition = catalog.load_channel(KEY)
    if not definition['schedule']['enabled']:
        return channels
    validate_definition(definition)
    if definition['delivery_sequence']['stage'] != 'scheduled':
        raise ValueError('初三协调任务已启用但未处于定时阶段')
    targets = catalog.select_targets(definition)
    if len(targets) != 1 or targets[0]['chat_id'] != cfg['chat_id']:
        raise ValueError('初三协调任务与原入口的目标群不一致')
    return [channel for channel in channels if channel not in CHANNELS]


def specs(slot):
    weekend = policy.business_date(slot).weekday() >= 4
    current = policy.business_period(slot)
    result = []
    for channel in CHANNELS:
        for original in WEEKEND_ORDER if weekend else WEEKDAY_ORDER:
            grain, section = original.split('_')
            owner = SUPERVISOR_KEY if grain == 'supervisor' else KEY if channel == 'app' else BILIBILI_ADVISOR_KEY
            period = policy.next_business_period(current) if weekend and section == 'process' else current
            prefix = 'app' if channel == 'app' else 'bilibili'
            part = original if channel == 'app' else prefix + '_' + original
            label = ('APP' if channel == 'app' else 'B站') + ('主管' if grain == 'supervisor' else '顾问')
            label += ('下期' if weekend and section == 'process' else '本期') + ('转化' if section == 'result' else '过程')
            result.append({'part': part, 'report_kind': prefix + '_' + original, 'channel': channel,
                           'owner': owner, 'section': section, 'period': period, 'label': label})
    return result


def prepare_one(definition, target, spec, slot, state_dir, *, no_mentions=False):
    from . import adapter
    owner = definition if spec['owner'] == KEY else catalog.load_channel(spec['owner'])
    adapter.validate_definition(owner)
    targets = [item for item in catalog.select_targets(owner) if item['chat_id'] == target['chat_id']]
    if (len(targets) != 1 or owner['sender'] != definition['sender']
            or owner['base_identity'] != definition['base_identity']
            or owner['source']['raw_table_id'] != definition['source']['raw_table_id']
            or owner['report']['included_grades'] != ['初三']):
        raise ValueError('消息组件的群、身份、源表或年级不一致')
    context = adapter.prepare(owner, targets[0], channel=spec['channel'], report_type=spec['section'],
        period=spec['period'], slot=slot, allow_period_override=True,
        state_dir=Path(state_dir) / spec['part'], no_mentions=no_mentions)
    context['report_kind'] = spec['report_kind']
    context['delivery_component'] = {'coordinator_ref': KEY, 'owner': spec['owner'], 'part': spec['part']}
    if not context.get('skip_delivery'):
        lines = context['markdown'].splitlines()
        lines[0] = f'## 🔥 **【{spec["period"]}】{spec["label"]}播报**'
        context['markdown'] = '\n'.join(lines)
    return {**spec, 'context': context, 'validation_cfg': catalog.schedule_config(owner, targets[0])}


def prepare(definition, target, slot, state_dir, *, no_mentions=False):
    validate_definition(definition)
    messages = []
    for spec in specs(slot):
        try:
            message = prepare_one(definition, target, spec, slot, state_dir, no_mentions=no_mentions)
        except (Exception, SystemExit) as exc:
            message = {**spec, 'context': None, 'error': type(exc).__name__ + ': ' + str(exc)[:200]}
        messages.append(message)
    return {'messages': messages}


def validate_component_calendar(context, cfg, slot):
    """Exact owner/part/calendar checks for separately sent weekend components."""
    component = context.get('delivery_component') or {}
    expected = [item for item in specs(slot) if item['report_kind'] == context.get('report_kind')]
    if len(expected) != 1:
        raise ValueError('初三消息组件未登记在当前日历中')
    spec = expected[0]
    if (component != {'coordinator_ref': KEY, 'owner': spec['owner'], 'part': spec['part']}
            or cfg.get('channel_key') != spec['owner']
            or context['channel'] != spec['channel'] or context['period'] != spec['period']
            or context['report_type'] != spec['section'] or context['chat_id'] != policy.CHAT_ID):
        raise ValueError('初三消息组件的归属、期次或类型不一致')
    from .adapter import policy_for
    owner = catalog.load_channel(spec['owner'])
    owner_policy = policy_for(owner)
    owner_policy.enforce_component_calendar(context['period'], context['report_type'], slot)


def validate_message(message, evidence, slot):
    from .reporting import validate_context
    context = message['context']
    if not context:
        raise ValueError(message.get('error', '消息未准备成功'))
    validate_context(context, evidence, message['validation_cfg'], slot)


def require_receipt_snapshot(message, db, key):
    prior = db.execute('SELECT detail FROM deliveries WHERE key=?', (key,)).fetchone()
    if not prior:
        return
    detail = json.loads(prior[0])
    context = message['context']
    if detail.get('rev') != context['raw_read_audit']['rev'] or detail.get('period') != context['period']:
        raise ValueError('本条已尝试消息的Base版本或期次已变化')


def write_preview(bundle, directory):
    """Each preview failure becomes one placeholder; other messages continue."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    cards, manifests, markdown = [], [], []
    for number, message in enumerate(bundle['messages'], 1):
        context = message.get('context')
        summary = {name: message[name] for name in ('label', 'owner', 'period', 'section', 'channel', 'report_kind')}
        summary.update(number=number, message_sent=False)
        try:
            if not context:
                raise ValueError(message.get('error', '消息未准备成功'))
            path = context.get('image_path' if message['section'] == 'process' else 'result_image_path')
            image = '<p>本条无合格数据，单独跳过。</p>'
            if path:
                raw = Path(path).read_bytes()
                image = '<img src="data:image/png;base64,' + base64.b64encode(raw).decode('ascii') + '">'
                summary.update(image_file=str(path), image_sha256=hashlib.sha256(raw).hexdigest())
            summary.update(status='skipped_no_eligible_rows' if context.get('skip_delivery') else 'preview_ready',
                           revision=context['raw_read_audit']['rev'], snapshot=context['snapshot'],
                           visible_rows=sum(len(block['rows']) for block in context['grade_report']['blocks']),
                           show_totals=context['grade_report'].get('show_totals', True))
            content = image + '<pre>' + html.escape(context['markdown']) + '</pre>'
            markdown.append(message['label'] + '\n\n' + context['markdown'])
        except (Exception, SystemExit) as exc:
            summary.update(status='preview_failed', error=type(exc).__name__ + ': ' + str(exc)[:200])
            content = '<p>本条预览失败，其他消息继续。</p><pre>' + html.escape(summary['error']) + '</pre>'
        cards.append('<article><h2>' + str(number) + '. ' + html.escape(message['label']) + ' · '
                     + message['period'] + '</h2>' + content + '</article>')
        manifests.append(summary)
    html_path = directory / 'app-message-order-preview.html'
    html_path.write_text('<!doctype html><meta charset="utf-8"><title>APP与B站初三消息预览</title>'
        '<style>body{font:16px Microsoft YaHei,sans-serif;background:#f4f6fa;color:#203b72;max-width:1700px;margin:24px auto}article{background:white;padding:20px;margin:20px;border-radius:12px}img{max-width:100%}pre{white-space:pre-wrap}</style>'
        '<h1>APP与B站 · 主管及顾问 · 独立消息预览</h1>' + ''.join(cards), encoding='utf-8')
    metadata_path = directory / 'app-message-order-manifest.json'
    metadata_path.write_text(json.dumps({'channel_key': KEY, 'messages': manifests, 'message_sent': False},
                                        ensure_ascii=False, indent=2), encoding='utf-8')
    markdown_path = directory / 'app-message-order-preview.md'
    markdown_path.write_text('\n\n---\n\n'.join(markdown), encoding='utf-8')
    return {'html_file': str(html_path), 'metadata_file': str(metadata_path), 'markdown_file': str(markdown_path),
            'message_sent': False, 'messages': manifests}
