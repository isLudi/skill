"""Channel faults, retries and card mentions must stay within their message."""
from collections import Counter
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
from types import SimpleNamespace
import sys
from zoneinfo import ZoneInfo

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from lark_delivery.domains.market_consultant import high_school_channel_runner as runner
from lark_delivery.domains.market_consultant import high_school_channel_card as cards
from lark_delivery.domains.market_consultant import grade_bundle_delivery as delivery
from lark_delivery.domains.market_consultant.delivery_ledger import connect_ledger
from lark_delivery import cli

SLOT = datetime(2026,11,6,14,tzinfo=ZoneInfo('Asia/Shanghai'))


def scenario(monkeypatch,tmp_path,phase):
    components = [{'id':name,'label':name} for name in ['external','self','app','outbound']]
    components[0]['source_component_ids'] = ['old_external_a','old_external_b']
    definition = {'components':components}
    calls = Counter()
    sent = []
    failed = set()

    def prepare(_definition,_target,*,state_dir,slot,component_ids):
        identifier = component_ids[0]
        calls[identifier] += 1
        if phase=='prepare' and identifier=='external' and identifier not in failed:
            failed.add(identifier)
            raise ValueError('Injected prepare failure')
        state_dir.mkdir(parents=True,exist_ok=True)
        return {'directory':str(state_dir),'component_ids':[identifier],
                'outcomes':{identifier:{'status':'prepared'}},'artifacts':[{'path':'image'}]}

    def preview(context):
        identifier = context['component_ids'][0]
        if phase=='preview' and identifier=='external' and identifier not in failed:
            failed.add(identifier)
            raise OSError('Injected HTML preview failure')

    def stage(db,context,token,_guard):
        identifier = context['component_ids'][0]
        if phase=='delivery' and identifier=='external' and identifier not in failed:
            failed.add(identifier)
            raise OSError('Injected delivery failure')
        sent.append(identifier)
        message_id = 'om_'+identifier
        db.execute('INSERT INTO bundle_messages VALUES (?,?,?,?,?,?,?)',
            (identifier,token,'sent_verified',message_id,'context',json.dumps([identifier]),'{}'))
        db.execute('INSERT INTO deliveries VALUES (?,?,?,?,?,?)',
            (identifier,token,identifier,'sent_verified',message_id,'{}'))
        db.commit()
        return {'status':'sent_verified','message_id':message_id,'component_ids':[identifier]}

    def resume(_db,row,_guard):
        return {'status':row[2],'message_id':row[3],'component_ids':json.loads(row[5])}

    log = SimpleNamespace(outcomes={})
    def outcome(identifier,status,reason='',**extras):
        log.outcomes[identifier] = {'status':status,'reason':reason,**extras}
    log.outcome = outcome
    monkeypatch.setattr(runner,'adapter_for',lambda _definition:SimpleNamespace(prepare=prepare,write_preview=preview))
    monkeypatch.setattr(delivery,'stage_and_send',stage)
    monkeypatch.setattr(delivery,'send_staged',resume)
    db = connect_ledger(tmp_path/'ledger')
    return definition,db,log,calls,sent


@pytest.mark.parametrize('phase',['prepare','preview','delivery'])
def test_first_failure_does_not_block_others_and_retry_is_local(monkeypatch,tmp_path,phase):
    definition,db,log,calls,sent = scenario(monkeypatch,tmp_path,phase)
    first = runner.round_once(definition,{},db,tmp_path,SLOT,SLOT.isoformat(),lambda:None,False,log)
    assert first['status']=='needs_attention'
    assert first['outcomes']['external']['status'] in {'blocked_prepare','blocked_delivery'}
    assert sent==['self','app','outbound']
    second = runner.round_once(definition,{},db,tmp_path,SLOT,SLOT.isoformat(),lambda:None,False,log)
    assert second['status']=='complete'
    assert sent==['self','app','outbound','external']
    assert calls=={'external':2,'self':1,'app':1,'outbound':1}
    db.close()


def test_old_combined_delivery_covers_aliases_without_resending(monkeypatch,tmp_path):
    definition,db,log,calls,sent = scenario(monkeypatch,tmp_path,'none')
    delivery.init(db)
    identifiers = ['old_external_a','old_external_b','self','app','outbound']
    db.execute('INSERT INTO bundle_messages VALUES (?,?,?,?,?,?,?)',
        ('legacy',SLOT.isoformat(),'sent_verified','om_legacy','context',json.dumps(identifiers),'{}'))
    for identifier in identifiers:
        db.execute('INSERT INTO deliveries VALUES (?,?,?,?,?,?)',
            (identifier,SLOT.isoformat(),identifier,'sent_verified','om_legacy','{}'))
    db.commit()
    result = runner.round_once(definition,{},db,tmp_path,SLOT,SLOT.isoformat(),lambda:None,False,log)
    assert result['status']=='complete' and len(result['outcomes'])==4
    assert not sent and not calls
    db.close()


def test_readback_failure_rechecks_only_that_message_and_continues(monkeypatch,tmp_path):
    definition,db,log,calls,sent = scenario(monkeypatch,tmp_path,'none')
    delivery.init(db)
    db.execute('INSERT INTO bundle_messages VALUES (?,?,?,?,?,?,?)',
        ('existing',SLOT.isoformat(),'sent_unverified','om_existing','context',json.dumps(['external']),'{}'))
    db.execute('INSERT INTO deliveries VALUES (?,?,?,?,?,?)',
        ('existing',SLOT.isoformat(),'external','sent_unverified','om_existing','{}'))
    db.commit()
    real_resume = delivery.send_staged
    def resume(db,row,guard):
        return {'status':'readback_failed','message_id':'om_existing'} if row[0]=='existing' else real_resume(db,row,guard)
    monkeypatch.setattr(delivery,'send_staged',resume)
    for _ in range(2):
        result = runner.round_once(definition,{},db,tmp_path,SLOT,SLOT.isoformat(),lambda:None,False,log)
        assert result['outcomes']['external']['status']=='readback_failed'
    assert sent==['self','app','outbound'] and 'external' not in calls
    db.close()


def test_card_mentions_accept_card_ids_and_reject_invalid_tags():
    content = json.dumps({'elements':[{'content':'<at id=ou_alice></at> <at id="ou_bob"></at>'}]})
    assert cards.mention_ids(content)=={'ou_alice','ou_bob'}
    assert '__invalid_at__' in cards.mention_ids('<at id=unknown></at>')


def test_grade_label_bold_delimiters_exclude_trailing_space():
    context = {'section':'process','artifacts':[{'reminders':[
        {'grade':'高一','names':['Alice']}]}]}
    people = {'resolved':{'Alice':'ou_alice'}}
    line = cards.reminder_lines(context,people)[0]
    assert line.startswith('**高一年级** <at id=ou_alice>')
    assert '年级 **' not in line


@pytest.mark.parametrize('message_type',['post','interactive'])
def test_card_readback_checks_image_sender_group_period_and_mentions(monkeypatch,message_type):
    context = {'target':{'chat_id':'oc_group'},'definition':{'sender':{'open_id':'ou_bot'}},
               'message_type':message_type,'period':'20261106期'}
    details = {'image_keys':['img_one'],'people':{'resolved':{'Alice':'ou_alice'}}}
    text = '<at id=ou_alice></at>' if message_type=='interactive' else '<at user_id="ou_alice"></at>'
    message = {'message_id':'om_one','chat_id':'oc_group','deleted':False,'msg_type':message_type,
               'sender':{'open_bot_id':'ou_bot'},'content':json.dumps({'title':'20261106期',
               'image_key':'img_one','text':text}),'mentions':[]}
    monkeypatch.setattr(delivery,'api',lambda _args:{'messages':[message]})
    assert delivery.readback('om_one',context,details)['verified'] is True
    bad = deepcopy(message)
    bad['chat_id'] = 'oc_other'
    monkeypatch.setattr(delivery,'api',lambda _args:{'messages':[bad]})
    with pytest.raises(ValueError):
        delivery.readback('om_one',context,details)


def test_cli_preview_continues_after_first_channel_fails(monkeypatch,tmp_path,capsys):
    definition = {'domain':'market_consultant','channel_id':'high_school_supervisor_bundle',
                  'adapter':'test','channel':'one','channels':['one','two'],
                  'targets':[{'id':'group','chat_id':'oc_group','enabled':True}],
                  'state_dir':str(tmp_path),'sender':{'identity':'bot'}}
    processed = []
    def prepare(_definition,_target,**kwargs):
        processed.append(kwargs['channel'])
        if kwargs['channel']=='one':
            raise OSError('First preview failed')
        return {'period':'20261106期','skip_delivery':False}
    adapter = SimpleNamespace(prepare=prepare,write_preview=lambda _: {'html':'preview'})
    monkeypatch.setattr(cli.catalog,'load_channel',lambda _:definition)
    monkeypatch.setattr(cli.catalog,'select_targets',lambda *_:definition['targets'])
    monkeypatch.setattr(cli,'adapter_for',lambda _:adapter)
    assert cli.main(['preview'],bound_channel='market_consultant/high_school_supervisor_bundle')==1
    assert processed==['one','two']
    output = capsys.readouterr().out
    assert 'preview_generated' in output and 'preview_failed' in output
