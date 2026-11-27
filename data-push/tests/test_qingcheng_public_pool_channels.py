import json
import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import fetch_qingcheng_process_source as source
import export_conversion_refresh as conversion
from preview_qingcheng_public_pool_process import _matches_channel

def records(channels):
    return [{'record_id':f'rec{i}','记录键':f'key{i}','期次':'20261113期',
             '一级渠道':'公海','渠道':ch,'分区日期':'20261107','分区小时':'11'}
            for i,ch in enumerate(channels)]

def fake_reader(rows,table,calls):
    def read(args,**kwargs):
        calls.append(args)
        path=Path(args[args.index('--output')+1]);path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')
        path.with_suffix('.manifest.json').write_text(json.dumps({'base_token':source.BASE_TOKEN,'table_id':table,
            'rev':123,'records_count':len(rows),'has_more':False}),encoding='utf-8')
    return read

@pytest.mark.parametrize('channel',['public_pool','special_public_pool'])
@pytest.mark.parametrize('channels',[['0元信息流'],['顾问未加好友'],['顾问未加好友','0元信息流']])
def test_process_includes_each_channel_without_requiring_the_other(monkeypatch,tmp_path,channel,channels):
    calls=[];monkeypatch.setattr(source,'run_lark',fake_reader(records(channels),source.TABLE_ID,calls))
    result=source.fetch(channel,'20261113期',tmp_path/'rows.ndjson')
    assert result['records_count']==len(channels)
    condition=json.loads(calls[0][calls[0].index('--filter-json')+1])
    assert ['一级渠道','==','公海'] in condition['conditions']
    assert all(c[0]!='渠道' for c in condition['conditions'])

@pytest.mark.parametrize('bad',['SEC未加好友','SEC内部复用','河南未加好友'])
def test_unrelated_secondary_channels_do_not_enter_public_pool(monkeypatch,tmp_path,bad):
    monkeypatch.setattr(source,'run_lark',fake_reader(records([bad]),source.TABLE_ID,[]))
    with pytest.raises(ValueError,match='secondary channel'):source.fetch('public_pool','20261113期',tmp_path/'rows.ndjson')

def test_conversion_exports_both_public_channels_and_excludes_sec(monkeypatch,tmp_path):
    calls=[];monkeypatch.setattr(conversion,'run_lark',fake_reader(records(['0元信息流','顾问未加好友']),conversion.TABLE_ID,calls))
    result=conversion.export_conversion('public_pool','20261113期',tmp_path/'rows.ndjson',cache_dir=tmp_path/'pages')
    assert result['records_count']==2
    monkeypatch.setattr(conversion,'run_lark',fake_reader(records(['SEC内部复用']),conversion.TABLE_ID,[]))
    excluded=conversion.export_conversion('public_pool','20261113期',tmp_path/'bad.ndjson',cache_dir=tmp_path/'badpages')
    assert excluded['records_count']==0 and excluded['export_records_count']==1

def test_preview_config_combines_exact_two_secondaries_only():
    cfg=Path(__file__).resolve().parents[1]/'config/departments/qingcheng'
    process=json.loads((cfg/'public_pool_process_preview.json').read_text(encoding='utf-8'))['source']['match']
    trans=next(c for c in json.loads((cfg/'transformation_preview.json').read_text(encoding='utf-8'))['channels'] if c['id']=='public_pool')['match']
    assert process==trans=={'一级渠道':'公海','渠道':['顾问未加好友','0元信息流']}
    assert all(_matches_channel(r,process) for r in records(['顾问未加好友','0元信息流']))
    assert not _matches_channel(records(['SEC未加好友'])[0],process)
    row=records(['0元信息流'])[0];row['一级渠道']='本地化'
    assert not _matches_channel(row,process)
