"""Optional process target coloring and financial numerator coverage."""
from copy import deepcopy
import json
from pathlib import Path
import sys

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from lark_delivery.domains.market_consultant import grade_bundle_model as model
from lark_delivery.domains.market_consultant import grade_bundle_compact as compact
from lark_delivery.domains.market_consultant import grade_bundle_delivery as delivery
from lark_delivery.domains.market_consultant import grade_bundle_render as rendering
from lark_delivery.domains.market_consultant import supervisor_yafei_advisor_report as advisor


def fixture():
    root = Path(__file__).resolve().parents[1]
    definition = json.loads((root / 'config/departments/market_consultant/douyin_advisor_bundle.json').read_text(encoding='utf-8'))
    component = definition['components'][0]
    component['process_5min_target'] = '0.40'
    if '截面单效' not in component['column_order']['process']:
        component['column_order']['process'].append('截面单效')
    rows = []
    for name, count, five, net in [('低于', 3, 1, -30), ('等于', 5, 2, 100), ('高于', 5, 3, 300)]:
        for index in range(count):
            sums = {field: 0 for field in (*advisor.COMMON, *advisor.PROCESS, *advisor.RESULT_REPORT)}
            rows.append({**sums, 'lead_id': str(len(rows)+1), '期次': '20261120期',
                '渠道': '抖音私信', '经理': '经理', '主管': '主管', '顾问': name,
                '年级': '高一' if index % 2 else '学习分享', '分区日期': '20261120', '分区小时': 15,
                '退前线索': 1, '退后线索': 1, '5min标记': int(index < five),
                '净收款': net if index == 0 else 0, '当期净收款': 0,
                '收款': max(0, net) if index == 0 else 0, '退费': max(0, -net) if index == 0 else 0})
    evidence = {'periods': {'20261120期': {'channel_counts': {'抖音私信': len(rows)}}}}
    return definition, rows, evidence


def calculate(definition, rows, evidence, section='process'):
    results, outcomes = model.calculate(rows, evidence, '20261120期', section, definition['components'])
    assert outcomes[definition['components'][0]['id']]['status'] == 'prepared', outcomes
    return results, outcomes


def test_financial_numerator_is_aggregated_and_existing_process_values_are_preserved():
    definition, rows, evidence = fixture()
    results, _ = calculate(definition, rows, evidence)
    block = results[0]['report']['blocks'][0]
    effects = {row['fields']['顾问']: row['fields']['截面单效'] for row in block['rows']}
    assert effects == {'低于': -10, '等于': 20, '高于': 60}
    assert block['total']['fields']['截面单效'] == 370 / 13
    baseline = deepcopy(definition)
    baseline['components'][0].pop('process_5min_target')
    baseline['components'][0]['column_order']['process'].remove('截面单效')
    old, _ = calculate(baseline, rows, evidence)
    old_block = old[0]['report']['blocks'][0]
    for before, after in zip([*old_block['rows'], old_block['total']], [*block['rows'], block['total']]):
        assert all(after['fields'][key] == value for key, value in before['fields'].items())
    assert not model.below_5min_target(baseline['components'][0], block['rows'][0])


def test_threshold_uses_exact_raw_counts_including_zero_and_exactly_forty():
    component = {'process_5min_target': '0.40'}
    row = lambda n, d: {'sums': {'5min标记': str(n), '退后线索': str(d)}}
    assert model.below_5min_target(component, row('39.99999999', 100))
    assert model.below_5min_target(component, row(0, 3))
    assert not model.below_5min_target(component, row(2, 5))
    assert not model.below_5min_target(component, row(0, 0))


def test_image_pixels_and_native_notice_follow_the_same_target(tmp_path):
    definition, rows, evidence = fixture()
    results, outcomes = calculate(definition, rows, evidence)
    _, artifacts, checks = compact.render(results, 'process', '20261120期', 'Group', tmp_path, outcomes)
    cells = [cell for cell in checks[0]['cells'] if cell['field'] == '5min']
    assert [cell['below_target'] for cell in cells] == [False, False, True, False]
    with Image.open(checks[0]['path']) as image:
        for cell in cells[:-1]:
            left, top, right, _ = cell['box']
            assert image.getpixel((right-3, top+3)) == ((255, 240, 240) if cell['below_target'] else (255, 255, 255))
            assert image.getpixel((left+5, top+8)) == ((239, 138, 138) if cell['below_target'] else (245, 174, 35))
    context = {'definition': definition, 'component_ids': [definition['components'][0]['id']],
        'period': '20261120期', 'snapshot': ['20261120', 15], 'section': 'process', 'directory': str(tmp_path),
        'target': definition['targets'][0], 'artifacts': artifacts, 'outcomes': outcomes,
        'artifact_protocol': 'market-grade-bundle-artifacts-v2'}
    post = delivery.native_post(context, ['preview-only'], {'resolved': {}})
    text = json.dumps(post, ensure_ascii=False)
    assert '≥40.00%' in text and '浅红底' in text
    preview = rendering.write_preview(context)
    assert '≥40.00%' in Path(preview['html']).read_text(encoding='utf-8')


def test_result_data_and_message_do_not_gain_process_target_notice():
    definition, rows, evidence = fixture()
    before, _ = calculate(definition, rows, evidence, 'result')
    baseline = deepcopy(definition)
    baseline['components'][0].pop('process_5min_target')
    baseline['components'][0]['column_order']['process'].remove('截面单效')
    after, _ = calculate(baseline, rows, evidence, 'result')
    assert before[0]['report'] == after[0]['report']
    assert model.process_notices({'section': 'result'}) == []


def test_registry_export_records_the_target_and_financial_process_column():
    from lark_delivery.domains.market_consultant.registry_export import records
    definition, _, _ = fixture()
    record = records('market_consultant/douyin_advisor_bundle', definition, 'operator')[0]
    assert record['过程指标（逐项勾选）'][-1] == '截面单效'
    assert record['过程指标展示顺序（选填）'].endswith('截面单效')
    assert '低于40.00%' in record['图片分组与排版']
    assert '≥40.00%' in record['运营备注']
