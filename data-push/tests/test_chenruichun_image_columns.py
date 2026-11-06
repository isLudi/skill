"""Chen's field order and efficiency aliases must retain weighted metrics."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from lark_delivery.domains.market_consultant import chenruichun_daily_adapter as adapter
from lark_delivery.domains.market_consultant import supervisor_video49_report as report

ORDER=['期次','负责人','主管','顾问','退后线索','首节到课率','人均报科','人头转化',
       '订单转化','退费率','当期单效','截面单效']


def test_old_config_uses_the_existing_columns_and_widths():
    columns,widths=adapter.image_columns({'report':{}},'result')
    assert columns==list(report.COLUMNS['result'])
    assert widths==list(report.WIDTHS['result'])


def test_new_column_order_replaces_amount_column_and_names_efficiencies():
    definition={'report':{'column_order':{'result':ORDER}}}
    columns,widths=adapter.image_columns(definition,'result')
    assert [column[0] for column in columns]==ORDER
    assert len(widths)==len(columns)==12
    assert columns[-2:]==[('当期单效','当期单效','amount'),('截面单效','截面单效','amount')]
    assert '净收款' not in [column[0] for column in columns]
    broken=deepcopy(definition)
    broken['report']['column_order']['result'].append('unknown_metric')
    with pytest.raises(ValueError):
        adapter.image_columns(broken,'result')


def test_efficiency_aliases_are_populated_and_total_is_weighted():
    rows=[]
    for name,count,current,net in [('顾问甲',6,20,15),('顾问乙',12,5,2.5)]:
        for _ in range(count):
            rows.append({'年级':'高一','经理':'负责人','主管':'主管','顾问':name,
                '退前线索':1,'退后线索':1,'首节到课标记':1,'当期净收款':current,
                '报科数':1,'成交人头':1,'订单数':1,'净收款':net,'收款':current,'退费':current-net})
    counters=(*report.COMMON,*report.RESULT_REPORT)
    computed=report.build_report(rows,counters,'20261106期','result',min_post_leads=6,included_grades=['高一'])
    block=computed['blocks'][0]
    fields={row['fields']['顾问']:row['fields'] for row in block['rows']}
    assert fields['顾问甲']['当期单效']==20 and fields['顾问甲']['截面单效']==15
    assert fields['顾问乙']['当期单效']==5 and fields['顾问乙']['截面单效']==2.5
    assert block['total']['fields']['当期单效']==10
    assert block['total']['fields']['截面单效']==pytest.approx(120/18)
    assert block['reminders']['result']==['顾问乙']


def test_registry_export_reads_the_configured_column_order():
    skill=Path(__file__).resolve().parents[1]
    spec=importlib.util.spec_from_file_location('chen_column_export',skill/'scripts/export_channel_registry_records.py')
    exporter=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(exporter)
    definition=json.loads((skill/'config/departments/market_consultant/supervisor_chenruichun.json').read_text(encoding='utf-8'))
    definition['report']['column_order']={'process':[column[0] for column in report.COLUMNS['process']],
                                          'result':ORDER}
    fields=exporter._operator_record('market_consultant/supervisor_chenruichun',definition)
    assert fields['转化指标展示顺序（选填）']=='、'.join(ORDER)
    assert fields['转化指标（逐项勾选）']==ORDER[4:]
    assert fields['转化重点提醒指标']==['截面单效']
