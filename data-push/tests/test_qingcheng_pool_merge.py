import json
import sys
from pathlib import Path
import pytest
import fetch_qingcheng_process_source as source
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_qingcheng_public_pool_channels import records,fake_reader

@pytest.mark.parametrize('report,expected',[('sec_order_reuse',9),('public_pool',2),('special_public_pool',2)])
def test_merged_pool_keeps_each_report_scope(monkeypatch,tmp_path,report,expected):
    rows=records(list(source.MERGED_POOL_CHANNELS))
    monkeypatch.setattr(source,'run_lark',fake_reader(rows,source.TABLE_ID,[]))
    result=source.fetch(report,'20261113期',tmp_path/(report+'.ndjson'))
    assert result['records_count']==expected
    actual=[json.loads(line) for line in (tmp_path/(report+'.ndjson')).read_text(encoding='utf-8').splitlines()]
    assert {row['渠道'] for row in actual}==(set(source.MERGED_POOL_CHANNELS) if report=='sec_order_reuse' else set(source.PUBLIC_POOL_CHANNELS))

def test_anhui_is_in_localization_process_and_conversion_reports():
    root=Path(__file__).resolve().parents[1]/'config/departments/qingcheng'
    process=json.loads((root/'partner_process_preview.json').read_text(encoding='utf-8'))
    assert '安徽APP' in process['source']['matches']['partner_local']['渠道']
    assert '安徽APP' in process['source']['matches']['supervisor_local']['渠道']
    conversion=json.loads((root/'transformation_preview.json').read_text(encoding='utf-8'))
    local=next(c for c in conversion['channels'] if c['id']=='partner_local')
    assert '安徽APP' in local['match']['渠道']
