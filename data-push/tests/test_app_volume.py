"""APP volume scope, source isolation, native post and same-slot delivery tests."""
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from lark_delivery.core import catalog
from lark_delivery.core.registry import adapter_for
from lark_delivery.domains.market_consultant import volume_adapter as adapter
from lark_delivery.domains.market_consultant import volume_report as volume
from lark_delivery.domains.market_consultant import grade_bundle_delivery as delivery
from lark_delivery.domains.market_consultant import upstream, window
from lark_delivery.domains.market_consultant.delivery_ledger import connect_ledger


def prepared(monkeypatch,tmp_path,**options):
    definition=catalog.load_channel('market_consultant/app_volume')
    rows=[{'期次':'20261113期','年级':grade,'渠道':channel,'预估量级':forecast,'实际进量':actual,
        '退前线索':pre,'退后线索':actual,'接量顾问数':staff} for grade,channel,forecast,actual,pre,staff in [
            ('高一','APP',100,80,100,2),('高一','app',50,40,50,1),('高二','ＡＰＰ',20,20,20,1),
            ('高一','APP其他',999,999,999,1)]]
    rows.append({**rows[0],'期次':'20261106期'})
    evidence={'total':5,'periods':['20261106期','20261113期'],'dt':'20261112','hour':15,'execution_id':123}
    monkeypatch.setattr(adapter.scheduler,'volume_upstream_ready',lambda *args:deepcopy(evidence))
    monkeypatch.setattr(adapter.immediate,'verify_publication',lambda *args:{'verified':True})
    calls=[]
    def read(base,table,fields,args):
        calls.append((table,fields))
        return deepcopy(rows),{'has_more':False,'rev':1,'records_count':len(rows)}
    monkeypatch.setattr(volume,'_read_table',read)
    monkeypatch.setattr(volume,'aggregate_abnormal',lambda *args:pytest.fail('Unexpected abnormal calculation'))
    context=adapter.prepare(definition,definition['targets'][0],state_dir=tmp_path,
        slot=datetime(2026,11,12,17,tzinfo=window.TZ),**options)
    assert calls==[('tblGUCxgUTZPjv3c',volume.VOLUME_FIELDS)]
    return context


def test_registered_target_and_volume_binding():
    definition=catalog.load_channel('market_consultant/app_volume')
    assert adapter_for(definition) is adapter
    cfg=catalog.schedule_config(definition,definition['targets'][0])
    assert cfg['upstream']==catalog.market_volume_binding(definition['volume_report'])
    assert cfg['chat_id']=='oc_9dc33c5731ce57c03d0589a2ac1d2e99'
    assert (cfg['hours'],cfg['send_minute'],cfg['deadline_minute'],cfg['retry_minutes'])==([17],20,50,2)
    changed=deepcopy(definition)
    changed['source']['raw_table_id']='another_table'
    with pytest.raises(ValueError,match='source or schedule'):
        adapter.validate_definition(changed)


def test_app_exact_matching_and_weighted_totals(monkeypatch,tmp_path):
    context=prepared(monkeypatch,tmp_path)
    assert len(context['artifacts'])==1
    assert [row['年级'] for row in context['rows']]==['高一','高二']
    assert context['rows'][0]['预估量级']==150
    total=volume.build_total_row(context['rows'])
    assert total['预估量级']==170 and total['实际进量']==140
    assert total['线索留存率']==140/170 and total['人均带班']==140/4
    post=delivery.native_post(context,['preview-image'],{'resolved':{}})
    assert post['zh_cn']['title']=='【APP渠道】进量进度如下，辛苦各位老师知悉 ❤️'
    text=json.dumps(post,ensure_ascii=False)
    assert '异常流量' not in text and '请重点关注高一年级' in text
    assert not context['artifacts'][0]['reminders']
    with pytest.raises(ValueError,match='period must match'):
        prepared(monkeypatch,tmp_path/'wrong-period',period='20261106期')
    with pytest.raises(ValueError,match='configured volume report'):
        prepared(monkeypatch,tmp_path/'wrong-report',report_type='result')


def test_same_slot_delivery_reuses_the_message_claim(monkeypatch,tmp_path):
    context=prepared(monkeypatch,tmp_path)
    monkeypatch.setattr(delivery.source,'guard',lambda context:None)
    monkeypatch.setattr(upstream,'verify_bot',lambda cfg:None)
    monkeypatch.setattr(delivery.im,'verify_sender_membership',lambda *args:None)
    monkeypatch.setattr(delivery.im,'upload_image',lambda *args:'image-key')
    monkeypatch.setattr(delivery,'resolve_people',lambda context:{'names':[],'resolved':{},'display_names':{},'fallback_reasons':{}})
    monkeypatch.setattr(delivery.reminders,'refresh_membership',lambda *args:({},{}))
    monkeypatch.setattr(delivery,'readback',lambda *args:{'verified':True,'message_id':'om_test'})
    writes=[]
    def api(args):
        if '--dry-run' not in args:
            writes.append(args)
        return {'message_id':'om_test'}
    monkeypatch.setattr(delivery,'api',api)
    with connect_ledger(tmp_path/'ledger') as db:
        delivery.init(db)
        for _attempt in range(2):
            result=delivery.stage_and_send(db,context,'2026-11-12T17:00:00+08:00',lambda:None)
            assert result['status']=='sent_verified'
        assert len(writes)==1
        assert db.execute('SELECT COUNT(*) FROM bundle_messages').fetchone()[0]==1


def test_volume_window_matches_koc():
    definition=catalog.load_channel('market_consultant/app_volume')
    cfg={**definition['schedule'],'first_send_at':'2026-11-12T17:20:00+08:00'}
    assert window.active_slot(datetime(2026,11,12,17,19,tzinfo=window.TZ),cfg) is None
    assert window.active_slot(datetime(2026,11,12,17,20,tzinfo=window.TZ),cfg) is not None
    assert window.active_slot(datetime(2026,11,12,17,50,tzinfo=window.TZ),cfg) is not None
    assert window.active_slot(datetime(2026,11,12,17,51,tzinfo=window.TZ),cfg) is None


def test_outbound_rule_scope_is_exact_and_can_use_one_source():
    definition=catalog.load_channel('market_consultant/outbound_volume')
    assert adapter_for(definition) is adapter
    assert volume.eligible_channel('ＴＭＫ3元',volume.RULE_OUTBOUND)
    assert volume.eligible_channel('唐山TMK',volume.RULE_OUTBOUND)
    assert not volume.eligible_channel('tmk3元周帅',volume.RULE_OUTBOUND)
    assert not volume.eligible_channel('APP',volume.RULE_OUTBOUND)
    source=[{'期次':'20261120期','年级':'高一','渠道':'唐山tmk','预估量级':100,
        '实际进量':30,'退前线索':40,'退后线索':30,'接量顾问数':2}]
    rows,channels,_=volume.aggregate_volume(source,'20261120期',volume.RULE_OUTBOUND)
    assert len(rows)==1 and channels=={'唐山tmk'}
    assert rows[0]['实际进量']==30 and rows[0]['线索留存率']==.75
    assert rows[0]['人均带班']==15 and rows[0]['量级完成度']==.3


def test_outbound_forecast_and_counters_merge_before_ratios():
    source=[{'期次':'20261120期','年级':'高一','渠道':channel,'预估量级':forecast,
        '实际进量':actual,'退前线索':pre,'退后线索':actual,'接量顾问数':staff}
        for channel,forecast,actual,pre,staff in [('tmk3元',200,60,100,3),('唐山tmk',100,30,50,2),('APP',999,999,999,9)]]
    rows,channels,_=volume.aggregate_volume(source,'20261120期',volume.RULE_OUTBOUND)
    assert len(rows)==1 and channels=={'tmk3元','唐山tmk'}
    total=volume.build_total_row(rows)
    assert total['预估量级']==300 and total['实际进量']==90
    assert total['线索留存率']==.6 and total['人均带班']==18 and total['量级完成度']==.3
