from copy import deepcopy
from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import sys
from unittest.mock import patch

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / 'scripts'))
from lark_delivery.domains.market_consultant import grade_bundle_model as live
from lark_delivery.domains.market_consultant import grade_bundle_compact as compact
from lark_delivery.domains.market_consultant import supervisor_report as supervisor
candidate = live


def fixture():
    definition = json.loads((SKILL / 'config/departments/market_consultant/high_school_supervisor_bundle.json').read_text(encoding='utf-8'))
    component = next(item for item in definition['components'] if item['id'] == 'draft_22_1')
    rows = []
    for name, count, five, current, total in [('甲', 5, 5, -10, 50), ('乙', 10, 6, 1000, 300), ('丙', 6, 1, 1200, 1200)]:
        for index in range(count):
            counters = {field: 0 for field in (*supervisor.COMMON, *supervisor.PROCESS, *supervisor.RESULT_REPORT)}
            rows.append({**counters, 'lead_id': str(len(rows)), '期次': '20261120期', '渠道': 'app',
                '经理': '负责人', '主管': name, '年级': '高一', '分区日期': '20261122', '分区小时': 11,
                '退前线索': 1, '退后线索': 1, '5min标记': int(index < five),
                '当期净收款': current if index == 0 else 0, '净收款': total if index == 0 else 0,
                '收款': total if index == 0 else 0})
    proof = {'periods': {'20261120期': {'channel_counts': {'app': len(rows)}}}}
    return component, rows, proof


def calculate(module, component, rows, proof, section='process'):
    results, outcomes = module.calculate(rows, proof, '20261120期', section, [component])
    assert outcomes['draft_22_1']['status'] == 'prepared', outcomes
    return results[0]


def test_financial_numerators_and_weighted_total_are_populated():
    component, rows, proof = fixture()
    result = calculate(candidate, component, rows, proof)
    block = result['report']['blocks'][0]
    values = {row['fields']['主管']: (row['fields']['当期单效'], row['fields']['截面单效']) for row in block['rows']}
    assert values == {'甲': (-2, 10), '乙': (100, 30), '丙': (200, 200)}
    assert block['total']['fields']['当期单效'] == 2190 / 21
    assert block['total']['fields']['截面单效'] == 1550 / 21


def test_five_minute_sort_and_existing_reminders_survive_the_finance_columns(tmp_path):
    component, rows, proof = fixture()
    result = calculate(candidate, component, rows, proof)
    original = deepcopy(component)
    original['column_order']['process'] = [name for name in original['column_order']['process'] if name not in {'当期单效', '截面单效'}]
    baseline = calculate(live, original, rows, proof)
    before, after = baseline['report']['blocks'][0], result['report']['blocks'][0]
    assert before['reminders'] == after['reminders']
    assert [row['fields']['主管'] for row in supervisor.sorted_rows(after, 'process')] == ['甲', '乙', '丙']
    assert all(after['total']['fields'][name] == value for name, value in before['total']['fields'].items())
    with patch.object(compact, 'columns', candidate.columns):
        _, _, checks = compact.render([result], 'process', '20261120期', 'APP', tmp_path, {})
    names = [cell['text'] for cell in checks[0]['cells'] if cell['field'] == '主管']
    assert names[:3] == ['甲', '乙', '丙']
    financial = [cell for cell in checks[0]['cells'] if cell['field'] in {'当期单效', '截面单效'}]
    assert len(financial) == 8 and all(cell['text'] not in ['', '-'] for cell in financial)
    assert [item[0] for item in candidate.columns(component, 'process')[0][-2:]] == ['当期单效', '截面单效']


def test_current_effect_only_also_requests_the_required_financial_sources():
    component, rows, proof = fixture()
    component['column_order']['process'].remove('截面单效')
    result = calculate(candidate, component, rows, proof)
    assert result['report']['blocks'][0]['total']['fields']['当期单效'] == 2190 / 21
    assert candidate.columns(component, 'process')[0][-1][0] == '当期单效'


def test_result_report_and_unmodified_process_contract_are_identical():
    component, rows, proof = fixture()
    original = deepcopy(component)
    original['column_order']['process'] = [name for name in original['column_order']['process'] if name not in {'当期单效', '截面单效'}]
    assert calculate(candidate, original, rows, proof) == calculate(live, original, rows, proof)
    assert calculate(candidate, component, rows, proof, 'result')['report'] == calculate(live, original, rows, proof, 'result')['report']
