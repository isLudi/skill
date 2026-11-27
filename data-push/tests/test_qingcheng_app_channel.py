import json
from pathlib import Path
import preview_qingcheng_transformation as conversion
from preview_qingcheng_public_pool_process import _matches_channel

def test_app_is_in_both_localization_process_profiles_and_conversion():
    root = Path(__file__).resolve().parents[1] / 'config/departments/qingcheng'
    preview = json.loads((root / 'partner_process_preview.json').read_text(encoding='utf-8'))
    for profile in ('partner_local', 'supervisor_local'):
        match = preview['source']['matches'][profile]
        assert match['一级渠道'] == '本地化' and 'APP' in match['渠道']
        assert len(match['渠道']) == len(set(match['渠道']))
    config = json.loads(conversion.DEFAULT_CONFIG.read_text(encoding='utf-8'))
    channel = next(item for item in config['channels'] if item['id'] == 'partner_local')
    assert _matches_channel({'一级渠道': '本地化', '渠道': 'APP'}, channel['match'])
    assert not _matches_channel({'一级渠道': '付费', '渠道': '山东直播间'}, channel['match'])

def test_merged_app_and_historical_labels_count_once_per_advisor():
    config = json.loads(conversion.DEFAULT_CONFIG.read_text(encoding='utf-8'))
    channel = next(item for item in config['channels'] if item['id'] == 'partner_local')
    root = Path(__file__).resolve().parents[1] / 'config/departments/qingcheng'
    request = json.loads((root / channel['consultant_request']).read_text(encoding='utf-8'))
    process, finance = [], []
    for index, label in enumerate(('APP', '河南APP', '安徽APP')):
        row = {'一级渠道': '本地化', '渠道': label, '期次': '20261120期', '年级': '初三',
               '主管': '主管甲', '顾问': '顾问甲', '顾问账号': 'advisor_a'}
        process.append({**row, '退后线索': 2, '首节到课标记': 0})
        finance.append({**row, '记录键': f'20261120期|conversion_fact|{index}|a|b|c', '收款': 100, '退费': 20, '净收款': 80,
                        '当期收款': 100, '成交人头': 1, '报科数': 1, '破蛋人数标记': 1,
                        '成交周期天数分子': 1, '成交周期成交人数分母': 1})
    result = conversion._aggregate(process, finance, '顾问', request, channel, period='20261120期')
    assert len(result) == 1
    assert result[0]['metrics']['有效线索'] == 6
    assert result[0]['metrics']['综合营收'] == 300
    assert result[0]['metrics']['净收款'] == 240
    assert result[0]['metrics']['带班人数'] == 1
