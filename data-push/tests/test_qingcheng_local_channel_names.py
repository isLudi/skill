"""Both reviewed localization channels contribute once to existing reports."""
import json
import sys
from pathlib import Path
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from preview_qingcheng_public_pool_process import _matches_channel, _read_snapshot
import preview_qingcheng_transformation as conversion

MATCH = {'一级渠道': '本地化', '渠道': ['河南APP', '河南私域']}


def test_complete_local_snapshot_accepts_both_channels_and_rejects_other_rows(tmp_path):
    path = tmp_path / 'local.ndjson'
    rows = [{'record_id': str(i), '记录键': str(i), '期次': '20261023期',
             '分区日期': '20261022', '分区小时': '14', '一级渠道': '本地化', '渠道': channel}
            for i, channel in enumerate(MATCH['渠道'])]
    path.with_suffix('.manifest.json').write_text(json.dumps({'has_more': False, 'records_count': 2}), encoding='utf-8')
    def read():
        path.write_text('\n'.join(json.dumps(r, ensure_ascii=True) for r in rows), encoding='utf-8')
        return _read_snapshot(path, {'source': {'match': MATCH}})[0]
    assert len(read()) == 2
    rows[1]['渠道'] = '其他本地化'
    with pytest.raises(ValueError, match='outside'):
        read()
    rows[1].update({'渠道': '河南私域', '一级渠道': '私域'})
    with pytest.raises(ValueError, match='outside'):
        read()
    assert _matches_channel({'一级渠道': '公海', '渠道': '顾问未加好友'},
                            {'一级渠道': '公海', '渠道': '顾问未加好友'})
    assert not _matches_channel({'一级渠道': '本地化', '渠道': '河南APP'}, {'渠道': []})


def test_local_channels_merge_leads_and_money_without_double_counting_people():
    cfg = json.loads(conversion.DEFAULT_CONFIG.read_text(encoding='utf-8'))
    channel = next(c for c in cfg['channels'] if c['id'] == 'partner_local')
    request = json.loads((SCRIPTS.parent / 'config/departments/qingcheng' / channel['consultant_request']).read_text(encoding='utf-8'))
    process, finance = [], []
    for i, (name, leads, cash) in enumerate([('河南APP', 2, 100), ('河南私域', 3, 200), ('其他本地化', 99, 999)]):
        common = {'一级渠道': '本地化', '渠道': name, '期次': '20261023期', '年级': '初三',
                  '主管': '主管甲', '顾问': '顾问甲', '顾问账号': 'consultant_a'}
        process.append({**common, '退后线索': leads, '首节到课标记': 0})
        finance.append({**common, '记录键': f'20261023期|conversion_fact|{i}|a|b|c',
                        '收款': cash, '退费': 0, '净收款': cash, '当期收款': cash,
                        '成交人头': 1, '报科数': 1, '破蛋人数标记': 1,
                        '成交周期天数分子': 1, '成交周期成交人数分母': 1})
    selected = lambda rows: [r for r in rows if _matches_channel(r, channel['match'])]
    result = conversion._aggregate(selected(process), selected(finance), '顾问', request, channel, period='20261023期')
    assert len(result) == 1
    assert result[0]['metrics']['有效线索'] == 5
    assert result[0]['metrics']['综合营收'] == result[0]['metrics']['净收款'] == 300
    assert result[0]['metrics']['综合单效'] == 60
    assert result[0]['metrics']['带班人数'] == 1
