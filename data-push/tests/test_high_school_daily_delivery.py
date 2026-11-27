"""Two-period evidence, image composition and native reminder coverage."""
from copy import deepcopy
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import re
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from lark_delivery.domains.market_consultant import high_school_daily as daily
from lark_delivery.domains.market_consultant import high_school_daily_policy as policy
from lark_delivery.domains.market_consultant import high_school_daily_card as cards
from lark_delivery.domains.market_consultant import high_school_channel_adapter as adapter
from lark_delivery.domains.market_consultant import grade_bundle_delivery as delivery
from lark_delivery.domains.market_consultant import grade_bundle_source as source
from lark_delivery.domains.market_consultant import supervisor_report as report


def fixture():
    root = Path(__file__).resolve().parents[1]
    definition = json.loads((root / 'config/departments/market_consultant/high_school_supervisor_bundle.json').read_text(encoding='utf-8'))
    for item in definition['components']:
        item.pop('daily_standards', None)
        item['reminders']['process_rank'] = '最低值'
    component = definition['components'][0]
    component['daily_standards'] = policy.settings()
    rows, counts = [], {}
    for period in ['20261120期', '20261127期']:
        count = {channel: 0 for channel in component['source_values']}
        for grade in policy.GRADES:
            for name, five, double, friend, net in [('主管甲', 2, 0, 4, 100), ('主管乙', 6, 2, 6, 300)]:
                for index in range(10):
                    channel = component['source_values'][index % len(component['source_values'])]
                    count[channel] += 1
                    amounts = {field: 0 for field in (*report.COMMON, *report.PROCESS, *report.RESULT_REPORT)}
                    rows.append({**amounts, 'lead_id': str(len(rows)), '期次': period, '渠道': channel,
                        '经理': '负责人', '主管': name, '年级': grade, '分区日期': '20261120', '分区小时': 15,
                        '退前线索': 1, '退后线索': 1, '5min标记': int(index < five),
                        '双沟标记': int(index < double), '好友标记': int(index < friend),
                        '净收款': net if index == 0 else 0, '收款': net if index == 0 else 0})
        counts[period] = {'channel_counts': count}
    proof = {'period': '20261120期', 'snapshot': ['20261120', 15], 'evidence': {'periods': counts}}
    return definition, rows, proof


def prepare(tmp_path, weekday=5):
    definition, rows, proof = fixture()
    at = datetime(2026, 11, 16 + weekday, 19, tzinfo=timezone(timedelta(hours=8)))
    return daily.prepare(definition, definition['targets'][0], rows, proof, tmp_path, at, definition['components'][0])


def test_weekend_card_binds_both_periods_and_omits_empty_standard_notices(tmp_path):
    context = prepare(tmp_path)
    assert context['delivery_periods'] == ['20261120期', '20261127期']
    assert len(context['artifacts']) == 2
    assert context['component_ids'] == [context['definition']['components'][0]['id']]
    card = cards.build(context, ['img_current', 'img_next'], {'resolved': {'主管甲': 'ou_a'}, 'display_names': {}})
    text = json.dumps(card, ensure_ascii=False)
    assert 'img_current' in text and 'img_next' in text
    assert '20261120期' in text and '20261127期' in text
    assert '不设' not in text and '达标线' not in text
    assert '<at id=ou_a>' in text
    assert not re.search(r'</at>\s*[（(]\d', text)


def test_saturday_and_thursday_use_reviewed_metric_and_all_below_target(tmp_path):
    saturday = prepare(tmp_path / 'sat', 5)
    part = saturday['daily_sections'][1]
    assert all(audit['names'] == ['主管甲'] for audit in part['audits'])
    assert all(audit['target'] == '0.50' for audit in part['audits'])
    thursday = prepare(tmp_path / 'thu', 3)
    assert len(thursday['artifacts']) == 1
    assert all(audit['metric'] == '双沟率' and audit['names'] == ['主管甲']
               for audit in thursday['daily_sections'][0]['audits'])


def test_empty_next_period_keeps_current_card_with_explicit_empty_audit(tmp_path):
    definition, rows, proof = fixture()
    rows = [row for row in rows if row['期次'] == proof['period']]
    proof['evidence']['periods']['20261127期']['channel_counts'] = {}
    context = daily.prepare(definition, definition['targets'][0], rows, proof, tmp_path,
        datetime(2026, 11, 21, 19, tzinfo=timezone(timedelta(hours=8))), definition['components'][0])
    assert len(context['artifacts']) == 1
    assert context['daily_sections'][1]['status'] == 'skipped_no_source_rows'
    assert context['delivery_periods'] == ['20261120期']


def test_unproved_next_period_cannot_be_presented_as_zero(tmp_path):
    definition, rows, proof = fixture()
    del proof['evidence']['periods']['20261127期']
    with pytest.raises(ValueError, match='absent from the complete source audit'):
        daily.prepare(definition, definition['targets'][0], rows, proof, tmp_path,
            datetime(2026, 11, 21, 19, tzinfo=timezone(timedelta(hours=8))), definition['components'][0])


def test_policy_is_explicit_and_other_channel_activation_is_rejected():
    definition, _, _ = fixture()
    adapter.validate_definition(definition)
    definition['components'][2]['daily_standards'] = policy.settings()
    with pytest.raises(ValueError, match='Unreviewed daily KOC'):
        adapter.validate_definition(definition)


def test_readback_requires_the_next_period_as_well_as_both_images(monkeypatch):
    context = {'target': {'chat_id': 'oc_group'}, 'definition': {'sender': {'open_id': 'ou_bot'}},
        'message_type': 'interactive', 'period': '20261120期', 'delivery_periods': ['20261120期', '20261127期']}
    detail = {'image_keys': ['img_current', 'img_next'], 'people': {'resolved': {}}}
    message = {'message_id': 'om_test', 'chat_id': 'oc_group', 'deleted': False, 'msg_type': 'interactive',
        'sender': {'open_bot_id': 'ou_bot'}, 'content': '20261120期 img_current img_next', 'mentions': []}
    monkeypatch.setattr(delivery, 'api', lambda _: {'messages': [message]})
    with pytest.raises(ValueError, match='period/images differ'):
        delivery.readback('om_test', context, detail)
    message['content'] += ' 20261127期'
    assert delivery.readback('om_test', context, detail)['verified']


def test_cross_midnight_standard_change_blocks_before_external_reads(monkeypatch):
    definition, _, _ = fixture()
    monkeypatch.setattr(source.catalog, 'load_channel', lambda _: definition)
    context = {'definition': definition, 'definition_sha256': source.fingerprint(definition),
        'daily_policy_date': '2000-01-01'}
    with pytest.raises(ValueError, match='changed at midnight'):
        source.guard(context)


def test_registry_export_distinguishes_added_weekend_process_from_other_channels():
    from lark_delivery.domains.market_consultant.registry_export import records
    definition, _, _ = fixture()
    exported = records('market_consultant/high_school_supervisor_bundle', definition, 'operator')
    assert exported[0]['过程数据星期'] == ['周一','周二','周三','周四','周六','周日']
    assert exported[0]['过程文字提醒名次'] == ['低于每日标准']
    assert all(row['过程数据星期'] == ['周一','周二','周三','周四'] for row in exported[1:])
    technical = records('market_consultant/high_school_supervisor_bundle', definition, 'technical')
    assert technical[0]['weekend_next_process_enabled'] is True
    assert technical[0]['weekend_next_process_minimum_post_leads'] == 5
    assert all('weekend_next_process_enabled' not in row for row in technical[1:])
    assert technical[0]['process_weekdays'] == '[0,1,2,3,5,6]'


def test_friday_prepares_only_current_conversion_without_requesting_next_period(tmp_path):
    definition, rows, proof = fixture()
    del proof['evidence']['periods']['20261127期']
    rows = [row for row in rows if row['期次'] == '20261120期']
    context = daily.prepare(definition, definition['targets'][0], rows, proof, tmp_path,
        datetime(2026, 11, 20, 19, tzinfo=timezone(timedelta(hours=8))), definition['components'][0])
    assert len(context['artifacts']) == len(context['daily_sections']) == 1
    assert context['delivery_periods'] == ['20261120期']
    text = json.dumps(cards.build(context, ['img_current'], {'resolved': {}, 'display_names': {}}), ensure_ascii=False)
    assert '下期过程' not in text and '好友率达标' not in text
