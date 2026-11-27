import copy
import json
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import tiangong2_task.execution as execution
from tiangong2_task.publishing import finalize_hash
from _shared.errors import UsageError


@pytest.fixture
def accepted(tmp_path,monkeypatch):
    monkeypatch.setattr(execution,'TIANGONG2_TASK_RUNTIME_DIR',tmp_path)
    scope={'project_id':308,'folder':'吕帅','menu_id':101900,'task_id':46817,'nezha_task_id':65369,
           'task_name':'market2lark_koc','owner_name':'lvshuai01'}
    current={'current_source_sha256':'a'*64,'current_source_comparison_sha256':'b'*64,
             'task_metadata_sha256':'c'*64,'version_state_sha256':'d'*64,'latest_published_version_id':8,
             'source_matches_latest_published':True}
    plan=finalize_hash({'schema_version':execution.PLAN_SCHEMA_VERSION,'operation':execution.PLAN_OPERATION,
        'status':'ready','identity':{'name':'lvshuai01'},'scope':scope,
        'execution':{'period_time':'2026-11-25 12:44:00','trigger_successor':False,'params':{},'disabled_stages':[]},
        'baseline':dict(current,baseline_execution_ids=[1,2])},'plan_sha256')
    plan_file=tmp_path/'plan.json';plan_file.write_text(json.dumps(plan),encoding='utf-8')
    receipt=finalize_hash({'schema_version':execution.RECEIPT_SCHEMA_VERSION,'operation':execution.PLAN_OPERATION,
        'scope':scope,'plan_file':str(plan_file),'plan_sha256':plan['plan_sha256'],'execute_request_sent':True,
        'execute_response':{'status':'success','errorCode':0},'fully_verified':False,'manual_attention_required':True,
        'ok':False,'trigger_successor':False,'started_at':'2026-11-25T04:45:19+00:00','failed_at':'2026-11-25T04:46:00+00:00',
        'error':'Tiangong2 execute-once request was accepted but no exact new execution was read back'},'receipt_sha256')
    path=tmp_path/'receipt.json';path.write_text(json.dumps(receipt),encoding='utf-8')
    config={'projectId':308,'execFileId':55,'triggerSourceEnum':'EXECUTE','triggerSuccessor':False,
            'disabledStages':[],'rerunTaskId':None,'params':{}}
    row={'id':3,'taskId':65369,'taskName':'market2lark_koc','periodTime':'2026-11-25 12:00:00',
         'triggerTime':'2026-11-25 12:45:28','runConfig':json.dumps(config)}
    rows=[row]
    monkeypatch.setattr(execution,'read_publish_state',lambda *a:current)
    monkeypatch.setattr(execution,'list_execution_history_bundle',lambda *a,**k:{'executions':rows})
    task=SimpleNamespace(**{k:v for k,v in scope.items() if k not in ('folder',)},folder_name='吕帅')
    return SimpleNamespace(path=path,plan=plan,receipt=receipt,current=current,rows=rows,row=row,task=task,config=config)


def test_reconciliation_is_read_only_and_retains_original_evidence(accepted):
    before=accepted.path.read_bytes()
    result=execution.reconcile_accepted_execution(object(),object(),task=accepted.task,receipt_file=accepted.path)
    assert accepted.path.read_bytes()==before
    assert result['execution_id']==3 and result['fully_verified'] and result['read_only_reconciliation']
    assert result['terminal_status_verified'] is False
    assert result['reconciliation']['original_receipt_sha256']==accepted.receipt['receipt_sha256']
    assert execution.reconciled_execution_period_matches(accepted.plan,accepted.row,result)
    assert not execution.reconciled_execution_period_matches(accepted.plan,accepted.row,accepted.receipt)


@pytest.mark.parametrize('fault',['ambiguous','late','different_period','wrong_task','scheduled','source_drift','receipt_tamper'])
def test_reconciliation_rejects_uncertain_or_drifted_associations(accepted,fault):
    if fault=='ambiguous':accepted.rows.append(dict(accepted.row,id=4))
    elif fault=='late':accepted.row['triggerTime']='2026-11-25 13:00:00'
    elif fault=='different_period':accepted.row['periodTime']='2026-11-25 12:01:00'
    elif fault=='wrong_task':accepted.row['taskId']=999
    elif fault=='source_drift':accepted.current['current_source_sha256']='e'*64
    elif fault=='receipt_tamper':
        value=copy.deepcopy(accepted.receipt);value['execute_response']['status']='error'
        accepted.path.write_text(json.dumps(value),encoding='utf-8')
    else:
        config=copy.deepcopy(accepted.config);config['triggerSourceEnum']='SCHEDULE'
        accepted.row['runConfig']=json.dumps(config)
    with pytest.raises(UsageError):
        execution.reconcile_accepted_execution(object(),object(),task=accepted.task,receipt_file=accepted.path)


@pytest.mark.parametrize('patch',[{'triggerSuccessor':True},{'params':{'custom':'value'}},{'disabledStages':[1]},{'projectId':999}])
def test_reconciliation_rejects_incompatible_execution_payload(accepted,patch):
    accepted.row['runConfig']=json.dumps(dict(accepted.config,**patch))
    with pytest.raises(UsageError,match='incompatible'):
        execution.reconcile_accepted_execution(object(),object(),task=accepted.task,receipt_file=accepted.path)


def test_reconciliation_proof_fails_if_original_receipt_is_changed(accepted):
    result=execution.reconcile_accepted_execution(object(),object(),task=accepted.task,receipt_file=accepted.path)
    value=copy.deepcopy(accepted.receipt);value['started_at']='2026-11-25T04:45:20+00:00'
    accepted.path.write_text(json.dumps(value),encoding='utf-8')
    with pytest.raises(UsageError):
        execution.reconciled_execution_period_matches(accepted.plan,accepted.row,result)


@pytest.mark.parametrize('value,expected',[('2026-11-25 12:44:00','2026-11-25 12:00:00'),('2026-11-25 00:00:00','2026-11-25 00:00:00')])
def test_native_hour_period_normalization(value,expected):
    assert execution.normalized_execution_period_time(value)==expected
