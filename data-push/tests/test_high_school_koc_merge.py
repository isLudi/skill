"""Combine source numerators before filtering and preserve historical claims."""
from copy import deepcopy
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from lark_delivery.domains.market_consultant import grade_bundle_model as model
from lark_delivery.domains.market_consultant import supervisor_report as report
from lark_delivery.domains.market_consultant import high_school_channel_runner as runner
from lark_delivery.domains.market_consultant import grade_bundle_delivery as delivery
from lark_delivery.domains.market_consultant.delivery_ledger import connect_ledger


def definition():
    root = Path(__file__).resolve().parents[1]
    return json.loads((root / 'config/departments/market_consultant/high_school_supervisor_bundle.json').read_text(encoding='utf-8'))


def make_rows(sources, counts):
    rows = []
    for source_index, (channel, count) in enumerate(zip(sources, counts)):
        for index in range(count):
            counters = {name: 0 for name in (*report.COMMON, *report.PROCESS, *report.RESULT_REPORT)}
            rows.append({**counters, 'lead_id': str(len(rows)), '期次': '20261120期', '渠道': channel,
                '经理': '负责人', '主管': '同一主管', '年级': '高一', '分区日期': '20261120', '分区小时': 19,
                '退前线索': 1, '退后线索': 1, '5min标记': int(source_index == 0 or (source_index == 2 and index == 0)),
                '净收款': [100, 200, 600][source_index] if index == 0 else 0,
                '收款': [100, 200, 600][source_index] if index == 0 else 0})
    return rows, {'periods': {'20261120期': {'channel_counts': dict(zip(sources, counts))}}}


@pytest.mark.parametrize('section', ['process', 'result'])
def test_three_sources_merge_before_minimum_and_recompute_weighted_metrics(section):
    component = definition()['components'][0]
    assert component['id'] == 'koc_channel' and len(component['source_values']) == 3
    rows, evidence = make_rows(component['source_values'], [2, 2, 2])
    results, outcomes = model.calculate(rows, evidence, '20261120期', section, [component])
    assert outcomes['koc_channel']['status'] == 'prepared'
    block = results[0]['report']['blocks'][0]
    assert len(block['rows']) == 1 and block['total']['fields']['退后线索'] == 6
    assert block['total']['fields']['5min'] == '50.00000000%'
    if section == 'result':
        assert block['total']['fields']['净收款'] == 900
        assert block['total']['fields']['截面单效'] == 150


@pytest.mark.parametrize('source_index', [0, 1, 2])
def test_any_one_koc_source_can_produce_the_merged_message(source_index):
    component = definition()['components'][0]
    counts = [0, 0, 0]
    counts[source_index] = 6
    rows, evidence = make_rows(component['source_values'], counts)
    results, outcomes = model.calculate(rows, evidence, '20261120期', 'process', [component])
    assert outcomes['koc_channel']['status'] == 'prepared'
    assert results[0]['report']['blocks'][0]['total']['fields']['退后线索'] == 6


def test_previous_external_and_self_claims_map_to_the_merged_channel(monkeypatch, tmp_path):
    cfg = definition()
    db = connect_ledger(tmp_path / 'ledger')
    delivery.init(db)
    token = '2026-11-20T19:00:00+08:00'
    for identifier in ['external_koc', 'draft_21_1']:
        db.execute('INSERT INTO bundle_messages VALUES (?,?,?,?,?,?,?)',
            (identifier, token, 'sent_verified', 'om_' + identifier, 'old-context', json.dumps([identifier]), '{}'))
        db.execute('INSERT INTO deliveries VALUES (?,?,?,?,?,?)',
            (identifier, token, identifier, 'sent_verified', 'om_' + identifier, '{}'))
    db.commit()
    calls = []
    def prepare(_definition, _target, **kwargs):
        identifier = kwargs['component_ids'][0]
        calls.append(identifier)
        folder = kwargs['state_dir']
        folder.mkdir(parents=True, exist_ok=True)
        return {'directory': str(folder), 'artifacts': [], 'component_ids': [identifier],
                'outcomes': {identifier: {'status': 'prepared'}}}
    monkeypatch.setattr(runner, 'adapter_for', lambda _: SimpleNamespace(prepare=prepare, write_preview=lambda _: None))
    monkeypatch.setattr(delivery, 'send_staged', lambda _db, row, _guard:
        {'status': 'sent_verified', 'message_id': row[3], 'component_ids': json.loads(row[5])})
    log = SimpleNamespace(outcomes={})
    log.outcome = lambda identifier, status, reason='', **extra: log.outcomes.update({identifier: {'status': status}})
    result = runner.round_once(cfg, {}, db, tmp_path, datetime(2026, 11, 20, 19,
        tzinfo=timezone(timedelta(hours=8))), token, lambda: None, False, log)
    assert result['status'] == 'complete'
    assert result['outcomes']['koc_channel']['status'] == 'sent_verified'
    assert calls == ['draft_22_1', 'draft_23_1']
    db.close()
