"""Channel-specific thresholds, image-only days and exact weekly period roles."""
from copy import deepcopy
from datetime import datetime, timezone, timedelta
from fractions import Fraction
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from lark_delivery.domains.market_consultant import grade9_daily_policy as policy
from lark_delivery.domains.market_consultant import grade9_daily_prepare as prepare
from lark_delivery.domains.market_consultant import grade9_daily_post as post
from lark_delivery.domains.market_consultant import supervisor_report as supervisor
from lark_delivery.domains.market_consultant.channels.grade_compact import next_business_period

TZ = timezone(timedelta(hours=8))


def fixture():
    root = Path(__file__).resolve().parents[1]
    definition = json.loads((root / 'config/departments/market_consultant/grade9_supervisor_bundle.json').read_text(encoding='utf-8'))
    definition['report']['grade9_daily_policy'] = policy.group_settings()
    for component in definition['components']:
        component['grade9_benchmarks'] = policy.channel_settings(policy.PROFILE_BY_ID[component['id']])
    rows, counts = [], {}
    for period in ['20261127期', '20261204期']:
        distribution = {}
        for component in definition['components']:
            channel = component['source_values'][0]
            distribution[channel] = 10
            for name, five, double, friend, net in [('甲', 4, 0, 1, 100), ('乙', 1, 1, 3, 500)]:
                for index in range(5):
                    counters = {field: 0 for field in (*supervisor.COMMON, *supervisor.PROCESS, *supervisor.RESULT_REPORT)}
                    rows.append({**counters, 'lead_id': str(len(rows)), '期次': period, '渠道': channel,
                        '经理': '负责人', '主管': name, '年级': '初三', '分区日期': '20261123', '分区小时': 7,
                        '退前线索': 1, '退后线索': 1, '5min标记': int(index < five),
                        '双沟标记': int(index < double), '好友标记': int(index < friend),
                        '净收款': net if index == 0 else 0, '收款': net if index == 0 else 0})
        counts[period] = {'channel_counts': distribution}
    proof = {'period': '20261127期', 'snapshot': ['20261123', 7], 'evidence': {'periods': counts}}
    return definition, rows, proof


def build(tmp_path, weekday, specification_index=0):
    definition, rows, proof = fixture()
    at = datetime(2026, 11, 23 + weekday, 14, tzinfo=TZ)
    specification = policy.specifications(weekday, proof['period'], '20261204期')[specification_index]
    return prepare.build_period(definition, definition['targets'][0], rows, proof, tmp_path, at,
                                specification, definition['components'])


@pytest.mark.parametrize('weekday', [0, 1])
def test_monday_tuesday_body_has_only_images_and_no_mentions(tmp_path, weekday):
    context = build(tmp_path, weekday)
    payload = post.native_post(context, ['img_test'], {'resolved': {}, 'display_names': {}})['zh_cn']
    assert len(payload['content']) == 1 and payload['content'][0][0]['tag'] == 'img'
    assert not any(artifact['reminders'] or artifact['standards'] for artifact in context['artifacts'])
    for result in context['results']:
        assert [row['fields']['主管'] for row in result['report']['blocks'][0]['ordered_rows']] == ['甲', '乙']


def test_wednesday_standards_are_channel_specific_and_all_below_are_named(tmp_path):
    context = build(tmp_path, 2)
    standards = {item['channel']: item['target'] for item in context['artifacts'][0]['standards']}
    assert standards == {'江苏本地化': '0.30', '安徽本地化': '0.35',
                         'KOC-孟亚飞数学': '0.35', '自孵化KOC-5元纯课': '0.35'}
    assert len(context['artifacts'][0]['reminders']) == 4
    assert all(item['names'] == ['乙'] for item in context['artifacts'][0]['reminders'])
    payload = post.native_post(context, ['img_test'], {'resolved': {'乙': 'ou_person'}, 'display_names': {'乙': '乙'}})
    text = json.dumps(payload, ensure_ascii=False)
    assert '30.00%' in text and '35.00%' in text and '未达到5min标准' in text
    assert '广东本地化≥' not in text and '山东本地化≥' not in text
    assert sum(node['tag'] == 'at' for row in payload['zh_cn']['content'] for node in row) == 4


def test_thursday_sort_is_double_communication_not_five_minutes(tmp_path):
    context = build(tmp_path, 3)
    for result in context['results']:
        assert [row['fields']['主管'] for row in result['report']['blocks'][0]['ordered_rows']] == ['乙', '甲']
    assert {item['channel']: item['target'] for item in context['artifacts'][0]['standards']} == {
        '江苏本地化': '0.10', '安徽本地化': '0.12', 'KOC-孟亚飞数学': '0.12', '自孵化KOC-5元纯课': '0.12'}
    assert all(item['names'] == ['甲'] for item in context['artifacts'][0]['reminders'])


@pytest.mark.parametrize('weekday,local,koc', [(5,'0.30','0.40'), (6,'0.40','0.50')])
def test_next_period_friend_standards_and_period_evidence(tmp_path, weekday, local, koc):
    context = build(tmp_path, weekday, 1)
    assert context['period'] == '20261127期' and context['report_period'] == '20261204期'
    assert context['delivery_periods'] == ['20261204期']
    standards = {item['channel']: item['target'] for item in context['artifacts'][0]['standards']}
    assert standards == {'江苏本地化': local, '安徽本地化': local, 'KOC-孟亚飞数学': koc, '自孵化KOC-5元纯课': koc}
    assert all(item['names'] == ['甲'] for item in context['artifacts'][0]['reminders'])


def test_friday_includes_next_period_image_without_invented_standard(tmp_path):
    context = build(tmp_path, 4, 1)
    assert len(context['artifacts']) == 1 and context['artifacts'][0]['period'] == '20261204期'
    assert context['artifacts'][0]['standards'] == context['artifacts'][0]['reminders'] == []
    text = json.dumps(post.native_post(context, ['img_next'], {'resolved': {}, 'display_names': {}}), ensure_ascii=False)
    assert '20261204期' in text and '标准' not in text and '不设' not in text


def test_threshold_uses_exact_fraction_and_keeps_koc_channels_separate():
    definition, _, _ = fixture()
    components = definition['components'][-2:]
    assert components[0]['label'] != components[1]['label']
    assert components[0]['grade9_benchmarks'] == components[1]['grade9_benchmarks']
    result = {'component': components[0], 'report': {'blocks': [{'grade': '初三',
        'rows': [{'fields': {'主管': '主管', '负责人': '负责人'}, 'sums': {'退后线索': '20', '5min标记': '7'}}],
        'reminders': {'process': ['主管']}}]}}
    specification = policy.specifications(2, '20261127期', '20261204期')[0]
    exact = policy.apply(result, specification, 2)
    assert exact['report']['blocks'][0]['reminders']['process'] == []
    result['report']['blocks'][0]['rows'][0]['sums']['5min标记'] = '6.99999999'
    assert policy.apply(result, specification, 2)['report']['blocks'][0]['reminders']['process'] == ['主管']
    assert next_business_period('20261225期') == '20270101期'


def test_missing_future_audit_blocks_only_that_part_and_guard_rejects_wrong_period(tmp_path):
    definition, rows, proof = fixture()
    del proof['evidence']['periods']['20261204期']
    specification = policy.specifications(5, '20261127期', '20261204期')[1]
    at = datetime(2026, 11, 28, 14, tzinfo=TZ)
    context = prepare.build_period(definition, definition['targets'][0], rows, proof, tmp_path, at, specification, definition['components'])
    assert context['skip_delivery'] and all(value['status'] == 'blocked_source_period' for value in context['outcomes'].values())
    valid = {'grade9_role': 'next_process', 'grade9_policy_date': at.date().isoformat(), 'grade9_weekday': 5,
        'report_period': '20261204期', 'section': 'process', 'delivery_periods': ['20261204期']}
    prepare.validate_context(valid, definition, at)
    valid['report_period'] = '20261120期'
    with pytest.raises(ValueError, match='date, period or standards changed'):
        prepare.validate_context(valid, definition, at)
    with pytest.raises(ValueError, match='not an executable message'):
        prepare.validate_context({'grade9_preview_only': True}, definition, at)


def test_registry_preserves_two_koc_panels_and_records_the_right_standard_groups():
    from lark_delivery.domains.market_consultant.registry_export import records
    definition, _, _ = fixture()
    operators = records('market_consultant/grade9_supervisor_bundle', definition, 'operator')
    assert len(operators) == 5
    by_id = {item['申请编号']: item for item in operators}
    assert '30%' in by_id['market_consultant/grade9_supervisor_bundle/draft_13']['运营备注']
    assert '周四双沟率≥10%' in by_id['market_consultant/grade9_supervisor_bundle/draft_13']['运营备注']
    assert '周六下期好友率≥40%' in by_id['market_consultant/grade9_supervisor_bundle/draft_16']['运营备注']
    assert by_id['market_consultant/grade9_supervisor_bundle/draft_15']['过程文字提醒名次'] == ['不提醒']
    assert by_id['market_consultant/grade9_supervisor_bundle/shandong']['过程文字提醒名次'] == ['不提醒']
    assert all(len(item['过程数据星期']) == 7 for item in operators)
