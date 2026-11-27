from copy import deepcopy
from fractions import Fraction
import importlib.util
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from lark_delivery.domains.market_consultant import high_school_daily_policy as policy
from lark_delivery.domains.market_consultant.channels.grade_compact import next_business_period


def row(name, five, double, friend, net=100, post=10):
    return {'fields': {'主管': name, '负责人': '负责人'}, 'sums': {
        '退后线索': str(post), '5min标记': str(five), '双沟标记': str(double),
        '好友标记': str(friend), '净收款': str(net)}}


def result(grade='高一'):
    return {'component': {'id': 'external_koc'}, 'report': {'blocks': [{
        'grade': grade, 'rows': [row('甲', 6, 0, 4, 100), row('乙', 2, 2, 5, 300), row('丙', 3, 1, 6, 200)],
        'total': {'fields': {'退后线索': 30}}, 'reminders': {'process': ['丙'], 'result': ['甲']}}]}}


def apply(weekday, grade='高一', future=False):
    specification = policy.specifications(weekday, '20261120期', '20261127期')[-1 if future else 0]
    return policy.apply(result(grade), specification)


def test_no_threshold_is_not_zero_or_a_carried_forward_target():
    for weekday in [0, 1]:
        report = apply(weekday)
        assert report['daily_audits'][0]['names'] == []
        assert report['daily_audits'][0]['target'] is None
        assert report['daily_audits'][0]['row_order'] == ['甲', '丙', '乙']
    assert len(policy.specifications(4, '20261120期', '20261127期')) == 1


def test_wednesday_uses_strict_exact_thirty_percent_for_all_three_grades():
    for grade in policy.GRADES:
        audit = apply(2, grade)['daily_audits'][0]
        assert audit['names'] == ['乙']
        assert audit['target'] == '0.30'
    assert policy.below(Fraction('0.29999999999'), '0.30')
    assert not policy.below(Fraction(3, 10), '0.30')
    assert not policy.below(None, '0.30')


def test_thursday_sorts_by_double_communication_instead_of_five_minutes():
    report = apply(3)
    audit = report['daily_audits'][0]
    assert audit['row_order'] == ['乙', '丙', '甲']
    assert audit['names'] == ['甲']
    assert report['report']['blocks'][0]['rows'][0]['below_standard_fields'] == ['双沟率']
    assert policy.TARGETS[3] == {'高一': '0.10', '高二': '0.09', '高三': '0.10'}
    assert not policy.below(Fraction(9, 100), policy.TARGETS[3]['高二'])
    assert policy.below(Fraction(9, 100), policy.TARGETS[3]['高一'])


def test_weekend_friend_targets_are_fifty_then_sixty_and_exact_target_passes():
    saturday = apply(5, future=True)['daily_audits'][0]
    sunday = apply(6, future=True)['daily_audits'][0]
    assert saturday['row_order'] == sunday['row_order'] == ['丙', '乙', '甲']
    assert saturday['names'] == ['甲']
    assert sunday['names'] == ['乙', '甲']
    assert saturday['target'] == '0.50' and sunday['target'] == '0.60'


def test_weekend_separates_current_conversion_from_exact_following_period():
    following = next_business_period('20261225期')
    assert following == '20270101期'
    for weekday in [5, 6]:
        current, future = policy.specifications(weekday, '20261225期', following)
        assert (current['period'], current['section'], current['metric']) == ('20261225期', 'result', '截面单效')
        assert (future['period'], future['section'], future['metric']) == ('20270101期', 'process', '好友率')
        assert apply(weekday)['daily_audits'][0]['row_order'] == ['乙', '丙', '甲']


def test_sort_and_threshold_evaluation_preserve_source_rows_and_totals():
    original = result()
    before = deepcopy(original)
    after = policy.apply(original, policy.specifications(3, '20261120期', '20261127期')[0])
    assert original == before
    assert after['report']['blocks'][0]['total'] == original['report']['blocks'][0]['total']
    assert len(after['report']['blocks'][0]['rows']) == 3


def test_fractional_weighted_supervisor_comparison_is_not_average_of_percentages():
    data = result()
    data['report']['blocks'][0]['rows'] = [row('主管', 0, 0, 0, post=5), row('主管', 40, 0, 0, post=95)]
    report = policy.apply(data, policy.specifications(2, '20261120期', '20261127期')[0])
    assert report['daily_audits'][0]['names'] == []
    value = report['daily_audits'][0]['values']['主管']
    assert Fraction(int(value['numerator']), int(value['denominator'])) == Fraction(2, 5)
