import json
from argparse import Namespace
from types import SimpleNamespace

import pytest

import manage_push_upstream as maintenance
from lark_delivery.integrations.producer_bindings import read_binding_document


def test_controlled_off_phase_period_still_requires_exact_authorization(tmp_path,monkeypatch):
    import sys
    from pathlib import Path
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'usql-web-query-operator/scripts'))
    from _shared import config
    from tiangong2_task.publishing import finalize_hash
    monkeypatch.setattr(config,'TIANGONG2_TASK_RUNTIME_DIR',tmp_path)
    binding=read_binding_document('qingcheng.transformation',expected_domain='qingcheng')
    scope={key:binding['upstream'][key] for key in maintenance.SCOPE_FIELDS}
    scope['owner_name']=binding['upstream']['owner']
    source='a'*64
    plan=finalize_hash({'schema_version':'tiangong2-task-execution-plan-v1',
        'operation':'execute_owned_published_tiangong2_task_once','scope':scope,
        'execution':{'period_time':'2026-11-25 12:00:00','trigger_successor':False,'params':{},'disabled_stages':[]},
        'baseline':{'latest_published_version_id':42,'current_source_sha256':source,'baseline_execution_ids':[99]}},'plan_sha256')
    plan_file=tmp_path/'plan.json';plan_file.write_text(json.dumps(plan),encoding='utf-8')
    receipt=finalize_hash({'schema_version':'tiangong2-task-execution-receipt-v1','scope':scope,
        'ok':True,'fully_verified':True,'manual_attention_required':False,'execute_request_sent':True,
        'plan_file':str(plan_file),'plan_sha256':plan['plan_sha256'],'execution_id':100,'trigger_successor':False},'receipt_sha256')
    receipt_file=tmp_path/'receipt.json';receipt_file.write_text(json.dumps(receipt),encoding='utf-8')
    upstream=binding['upstream']
    run={'projectId':308,'execFileId':55,'triggerSourceEnum':'EXECUTE','triggerSuccessor':False,'disabledStages':[],'rerunTaskId':None}
    row={'id':100,'taskId':upstream['nezha_task_id'],'taskName':upstream['task_name'],'status':6,
         'startTime':'2026-11-25 12:45:42','endTime':'2026-11-25 13:01:47','periodTime':'2026-11-25 12:00:00','runConfig':json.dumps(run)}
    spec=SimpleNamespace(nezha_task_id=upstream['nezha_task_id'],project_id=308)
    args=Namespace(execution_id=100,exec_file_id=55,execution_receipt=receipt_file)
    publication=(42,'V42','2026-11-25 12:44:00',source)
    assert maintenance._validate_execution(object(),spec,binding,row,publication,args).hour==12
    args.execution_receipt=None
    with pytest.raises(ValueError,match='operator receipt'):
        maintenance._validate_execution(object(),spec,binding,row,publication,args)
    run['triggerSourceEnum']='SCHEDULE';row['runConfig']=json.dumps(run)
    with pytest.raises(ValueError,match='schedule phase'):
        maintenance._validate_execution(object(),spec,binding,row,publication,args)
