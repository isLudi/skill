"""Dynamic grade coverage, the >=3 boundary and header-free table composition."""
from copy import deepcopy
from pathlib import Path
import sys

from PIL import Image

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from lark_delivery.common.images import _find_font,_center_text
from lark_delivery.common.values import _format_value
from lark_delivery.domains.market_consultant import grade_bundle_model as model
from lark_delivery.domains.market_consultant import grade_bundle_compact as compact
from lark_delivery.domains.market_consultant import grade_bundle_render as combined
from lark_delivery.domains.market_consultant import high_school_channel_render as channel_image
from lark_delivery.domains.market_consultant import grade_report,volume_report


def fixture():
    root=Path(__file__).resolve().parents[1]
    import json
    definition=json.loads((root/'config/departments/market_consultant/douyin_advisor_bundle.json').read_text(encoding='utf-8'))
    component=deepcopy(definition['components'][0])
    component.pop('grade_grouping', None)
    rows=[]
    for grade,advisor,count,net in [('高一','顾问甲',3,30),('学习分享','顾问乙',3,25500),
                                    ('未来分类','顾问丙',3,300),('学习分享','顾问丁',2,100)]:
        for index in range(count):
            rows.append({'lead_id':str(len(rows)+1),'期次':'20261106期','渠道':'抖音私信',
                '经理':'经理','主管':'主管','顾问':advisor,'年级':grade,'分区日期':'20261106','分区小时':11,
                '退前线索':1,'退后线索':1,'5min标记':1,'双沟标记':0,'首节到课标记':1,
                '当期净收款':net if index==0 else 0,'净收款':net if index==0 else 0,
                '收款':net if index==0 else 0,'退费':0,'报科数':1,'成交人头':1,'订单数':1})
    evidence={'periods':{'20261106期':{'channel_counts':{'抖音私信':len(rows)}}}}
    results,outcomes=model.calculate(rows,evidence,'20261106期','result',[component])
    assert outcomes[component['id']]['status']=='prepared'
    return results,outcomes


def test_all_actual_grades_and_exactly_three_leads_are_included():
    results,_=fixture()
    report=results[0]['report']
    assert set(report['included_grades'])=={'高一','学习分享','未来分类'}
    assert not report['excluded_grade_counts']
    learning=next(block for block in report['blocks'] if block['grade']=='学习分享')
    assert [row['fields']['顾问'] for row in learning['rows']]==['顾问乙']
    assert learning['total']['fields']['净收款']==25500
    assert learning['total']['fields']['退后线索']==3
    assert all(block['reminders']['result']==[] for block in report['blocks'])


def test_unknown_grade_panels_have_unique_paths_and_no_outer_heading(tmp_path):
    results,outcomes=fixture()
    _,artifacts,checks=compact.render(results,'result','20261106期','Group heading must not be drawn',tmp_path,outcomes)
    assert len(artifacts)==3 and len({check['path'] for check in checks})==3
    for artifact in artifacts:
        check=next(check for check in checks if check['grade']==artifact['grade'])
        assert artifact['height']==32+check['height']
        with Image.open(artifact['path']) as image,Image.open(check['path']) as panel:
            region=image.crop((16,16,16+panel.width,16+panel.height))
            assert region.tobytes()==panel.tobytes()


def test_legacy_composition_and_channel_composition_have_no_outer_heading(tmp_path):
    results,outcomes=fixture()
    _,artifacts=combined.render(deepcopy(results),'result','20261106期','Group',tmp_path/'legacy',deepcopy(outcomes))
    paths=list((tmp_path/'legacy').glob('draft_24_1-*.png'))
    assert len(paths)==3
    for artifact in artifacts:
        assert artifact['height']==48+48+58+50
    artifact,checks=channel_image.render_channel(results[0],'result','20261106期',tmp_path/'channel')
    assert artifact['height']==32+sum(check['height'] for check in checks)+14*(len(checks)-1)


def test_owner_and_volume_templates_start_directly_at_the_table(tmp_path):
    records=[{'年级':'高一','经理':'经理','退前线索':1,'退后线索':1,'5min标记':1,'双沟标记':0,
              '首节到课标记':1,'当期净收款':10,'净收款':10} for _ in range(10)]
    report=grade_report.build_report(records,(*grade_report.COMMON,*grade_report.RESULT_REPORT),
                                    '20261106期','result')
    path=tmp_path/'owner.png'
    grade_report.render_image(report,'result',path,font_loader=_find_font,center_text=_center_text,
                              format_value=_format_value)
    with Image.open(path) as image:
        assert image.height==52+64+54+58
    row={'期次':'20261106期','年级':'高一','预估量级':10,'实际进量':5,'_退前线索':5,
         '_退后线索':4,'_接量顾问数':1,'线索留存率':0.8,'人均带班':5,'量级完成度':0.5}
    geometry=volume_report.render_image([row],tmp_path/'volume.png')
    assert geometry['height']==76+68*2


def combined_fixture():
    import json
    from lark_delivery.domains.market_consultant import supervisor_yafei_advisor_report as advisor

    root = Path(__file__).resolve().parents[1]
    definition = json.loads((root/'config/departments/market_consultant/douyin_advisor_bundle.json').read_text(encoding='utf-8'))
    definition['components'][0]['grade_grouping'] = 'combined'
    rows = []
    for grade, name, count, net in [
        ('高一', '顾问甲', 2, 100), ('学习分享', '顾问甲', 1, 200),
        ('未来分类', '顾问乙', 3, 600), ('', '顾问丁', 1, 150),
        ('高二', '顾问丁', 2, 50), ('学习分享', '门槛以下', 2, 99),
    ]:
        for index in range(count):
            amounts = {field: 0 for field in (*advisor.COMMON, *advisor.PROCESS, *advisor.RESULT_REPORT)}
            rows.append({**amounts, 'lead_id': str(len(rows)+1), '期次': '20261113期',
                '渠道': '抖音私信', '经理': '经理', '主管': '主管', '顾问': name, '年级': grade,
                '分区日期': '20261112', '分区小时': 11, '退前线索': 1, '退后线索': 1,
                '5min标记': int(index == 0), '首call完成标记': int(index == 0),
                '净收款': net if index == 0 else 0, '当期净收款': net if index == 0 else 0,
                '收款': net if index == 0 else 0})
    evidence = {'periods': {'20261113期': {'channel_counts': {'抖音私信': len(rows)}}}}
    return definition, rows, evidence


def test_combined_grades_aggregate_before_the_advisor_threshold():
    from lark_delivery.domains.market_consultant import grade_bundle_adapter as adapter

    definition, rows, evidence = combined_fixture()
    original = deepcopy(rows)
    adapter.validate_definition(definition)
    results, outcomes = model.calculate(rows, evidence, '20261113期', 'result', definition['components'])
    assert outcomes['draft_24_1']['status'] == 'prepared'
    assert rows == original
    report = results[0]['report']
    assert not report['excluded_grade_counts']
    assert len(report['blocks']) == 1
    block = report['blocks'][0]
    assert block['grade'] == '抖音私信'
    people = {row['fields']['顾问']: row for row in block['rows']}
    assert set(people) == {'顾问甲', '顾问乙', '顾问丁'}
    assert people['顾问甲']['fields']['退后线索'] == 3
    assert people['顾问甲']['fields']['净收款'] == 300
    assert round(float(people['顾问甲']['fields']['5min'].rstrip('%')), 2) == 66.67
    assert people['顾问丁']['fields']['退后线索'] == 3
    assert block['total']['fields']['退后线索'] == 9
    assert block['total']['fields']['净收款'] == 1100


def test_combined_process_and_conversion_render_one_image_and_one_channel_label(tmp_path):
    from lark_delivery.domains.market_consultant import grade_bundle_delivery as delivery

    definition, rows, evidence = combined_fixture()
    for section in ['process', 'result']:
        results, outcomes = model.calculate(rows, evidence, '20261113期', section, definition['components'])
        results, artifacts, _checks = compact.render(results, section, '20261113期', 'Group', tmp_path/section, outcomes)
        assert len(artifacts) == 1 and artifacts[0]['grade'] == '抖音私信'
        assert not artifacts[0]['reminders']
        context = {'definition': definition, 'period': '20261113期', 'snapshot': ['20261112', 11],
            'section': section, 'artifacts': artifacts}
        post = delivery.native_post(context, ['local-image'], {'resolved': {}, 'display_names': {}})
        content = post['zh_cn']['content']
        assert sum(item['tag'] == 'img' for line in content for item in line) == 1
        text = ''.join(item.get('text', '') for line in content for item in line)
        assert '抖音私信' in text and '高一' not in text and '学习分享' not in text


def test_combined_registry_export_records_the_aggregation_scope():
    from lark_delivery.domains.market_consultant.registry_export import records

    definition, _rows, _evidence = combined_fixture()
    operator = records('market_consultant/douyin_advisor_bundle', definition, 'operator')[0]
    assert operator['数据维度'] == ['期次', '渠道', '负责人', '主管', '顾问']
    assert operator['年级范围'] == []
    assert '全部年级合并为一张图' in operator['图片分组与排版']
    assert operator['门槛值'] == 3
    technical = records('market_consultant/douyin_advisor_bundle', definition, 'technical')[0]
    assert technical['minimum_post_leads'] == 3
