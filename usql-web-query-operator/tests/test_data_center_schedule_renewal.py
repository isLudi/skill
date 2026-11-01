from __future__ import annotations
import copy
import json
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from _shared.errors import UsageError
from usql_web_query.data_center import DataCenterDataset, DataCenterDatasetSql
from usql_web_query.data_center_schedule import (
    build_renewal_plan, claim_single_write, digest, dismiss_editor_memory_notice, parameter_values,
    preview_saved_sql_if_required,
    validate_plan, validate_range, verify_current, verify_readback, verify_save_payload,
)

def current():
    ds = DataCenterDataset(id='menu_set_1001', key='menu_set_1001', name='Existing dataset',
         file_value='1001', subject_id='99', parent_id='folder', owner='owner',
         create_time='1', path=('Root', '市场顾问部', '市场顾问部', 'Existing dataset'))
    return DataCenterDatasetSql(dataset=ds, execute_sql='select 1 as value\n',
        data_source_id='source', open_external='0', detail_payload={
        'dataParamList':[{'fieldName':'value','fieldType':'NUM','paramId':'1',
                         'showName':'value','dataTypeCode':6,'orgParamType':1}],
        'schedule':{'taskStatus':True,'isExpire':True,'taskId':'old',
                    'dateRange':['2026-01-01','2026-03-01'], 'alarmReceiver':['owner'],
                    'scheduleType':1,'synchronizationFrequency':{'timeUnit':1,'timeHourMinuteList':['9:00','17:00']}}})

def plan_for(cur=None):
    return build_renewal_plan(domain='market',current=cur or current(),
           start=date.today(),end=date.today()+timedelta(days=90))

def payload_for(plan):
    return {'id':plan['dataset']['id'],'name':plan['dataset']['name'],'menuType':'DATA_SET',
            'dataSourceId':plan['dataset']['dataSourceId'],'dataParamList':copy.deepcopy(plan['parameters']),
            'executeSql':current().execute_sql,'schedule':copy.deepcopy(plan['replacement_schedule'])}

class RenewalGates(TestCase):
    def test_pristine_editor_does_not_trigger_preview_before_date_change(self):
        from usql_web_query.data_center_schedule import DataCenterScheduleRenewalExecutor
        page=MagicMock();page.locator.return_value.count.return_value=0
        executor=DataCenterScheduleRenewalExecutor(page=page,client=None,plan=plan_for(),claim_dir=Path('unused'))
        from unittest.mock import patch
        with patch('usql_web_query.data_center_schedule.dismiss_editor_memory_notice',return_value=False):
            executor.prepare_editor_sql(MagicMock())
        page.expect_response.assert_not_called()
        page.locator.return_value.first.is_disabled.return_value=False
        executor.ensure_save_ready(MagicMock())
        page.expect_response.assert_not_called()

    def test_native_field_reordering_preserves_exact_field_identity_and_metadata(self):
        detail=copy.deepcopy(current().detail_payload)
        detail['dataParamList'].append({'fieldName':'another','fieldType':'TEXT','paramId':'2',
                                       'showName':'another','dataTypeCode':11,'orgParamType':1})
        reversed_detail=copy.deepcopy(detail)
        reversed_detail['dataParamList'].reverse()
        self.assertEqual(parameter_values(detail),parameter_values(reversed_detail))
        reversed_detail['dataParamList'][0]['paramId']='changed'
        self.assertNotEqual(parameter_values(detail),parameter_values(reversed_detail))
        detail['dataParamList'].append(copy.deepcopy(detail['dataParamList'][0]))
        with self.assertRaises(UsageError):parameter_values(detail)

    def test_required_preview_keeps_native_save_and_single_sql_request_gates(self):
        page=MagicMock();editor=MagicMock();progress={}
        page.locator.return_value.first.is_disabled.side_effect=[True,False]
        editor.evaluate.return_value=current().execute_sql
        response=page.expect_response.return_value.__enter__.return_value.value
        response.ok=True
        response.json.return_value={'status':'success','errorCode':0,'data':{'result':{'taskId':7,'meta':[{}],'data':[]}}}
        preview_saved_sql_if_required(page,plan_for(),editor,progress)
        self.assertEqual(progress['preview']['taskId'],7)
        guard=page.route.call_args.args[1]
        good=MagicMock();good.request.post_data=json.dumps({'executeSql':current().execute_sql})
        guard(good)
        good.continue_.assert_called_once_with()
        repeated=MagicMock();repeated.request.post_data=good.request.post_data
        guard(repeated)
        repeated.abort.assert_called_once_with()
        changed=MagicMock();changed.request.post_data=json.dumps({'executeSql':'select 2'})
        guard(changed)
        changed.abort.assert_called_once_with()
        self.assertEqual(progress['preview_request_count'],1)

    def test_enabled_save_needs_no_preview_and_sql_drift_blocks_preview(self):
        page=MagicMock();editor=MagicMock();progress={}
        page.locator.return_value.first.is_disabled.return_value=False
        preview_saved_sql_if_required(page,plan_for(),editor,progress)
        page.expect_response.assert_not_called()
        page.locator.return_value.first.is_disabled.return_value=True
        editor.evaluate.return_value='select 2 as value\n'
        with self.assertRaises(UsageError):preview_saved_sql_if_required(page,plan_for(),editor,progress)
        page.expect_response.assert_not_called()

    def test_failed_required_preview_never_becomes_renewal_success(self):
        page=MagicMock();editor=MagicMock();progress={}
        page.locator.return_value.first.is_disabled.return_value=True
        editor.evaluate.return_value=current().execute_sql
        response=page.expect_response.return_value.__enter__.return_value.value
        response.ok=True
        response.json.return_value={'status':'error','errorCode':3021,'error':'MEM_LIMIT_EXCEEDED'}
        with self.assertRaises(UsageError):preview_saved_sql_if_required(page,plan_for(),editor,progress)
        self.assertEqual(progress['phase'],'saved_sql_preview')
        self.assertNotIn('preview',progress)
        self.assertNotIn('write_request_sent',progress)
        self.assertEqual(progress['preview_failure']['error'],'MEM_LIMIT_EXCEEDED')
        page.unroute.assert_called_once()

    def test_unreviewed_preview_policy_blocks_plan(self):
        p=plan_for();p['preview_policy']='arbitrary_sql'
        p['plan_sha256']=digest({k:v for k,v in p.items() if k!='plan_sha256'})
        with self.assertRaises(UsageError):validate_plan(p,p['plan_sha256'],True)

    def test_only_observed_editor_memory_notice_is_acknowledged(self):
        page=MagicMock()
        dialogs=page.locator.return_value
        dialogs.count.return_value=1
        dialog=dialogs.first
        dialog.inner_text.return_value='SQL执行失败\nSQL执行异常：MEM_LIMIT_EXCEEDED\n知道了'
        dialog.get_by_role.return_value.count.return_value=1
        dialog.locator.return_value.count.return_value=1
        self.assertTrue(dismiss_editor_memory_notice(page))
        dialog.get_by_role.assert_called_once_with('button',name='知道了',exact=True)
        dialog.get_by_role.return_value.click.assert_called_once_with()
        dialog.wait_for.assert_called_once_with(state='hidden',timeout=10_000)

    def test_other_errors_permissions_or_confirmation_dialogs_block(self):
        for message in ['权限不足 知道了','SQL执行失败 语法错误 知道了','确认保存 MEM_LIMIT_EXCEEDED']:
            page=MagicMock()
            page.locator.return_value.count.return_value=1
            dialog=page.locator.return_value.first
            dialog.inner_text.return_value=message
            dialog.get_by_role.return_value.count.return_value=1
            dialog.locator.return_value.count.return_value=1
            with self.assertRaises(UsageError):dismiss_editor_memory_notice(page)
            dialog.get_by_role.return_value.click.assert_not_called()
        page=MagicMock();page.locator.return_value.count.return_value=2
        with self.assertRaises(UsageError):dismiss_editor_memory_notice(page)

    def test_no_notice_needs_no_click_and_extra_actions_are_rejected(self):
        page=MagicMock();page.locator.return_value.count.return_value=0
        self.assertFalse(dismiss_editor_memory_notice(page,grace_ms=0))
        page.get_by_role.assert_not_called()
        page=MagicMock();page.locator.return_value.count.return_value=1
        dialog=page.locator.return_value.first
        dialog.inner_text.return_value='SQL执行失败 MEM_LIMIT_EXCEEDED 知道了 重新执行'
        dialog.get_by_role.return_value.count.return_value=1
        dialog.locator.return_value.count.return_value=2
        with self.assertRaises(UsageError):dismiss_editor_memory_notice(page)
        dialog.get_by_role.return_value.click.assert_not_called()

    def test_delayed_automatic_preview_notice_is_not_missed(self):
        page=MagicMock()
        page.locator.return_value.count.side_effect=[0,1]
        dialog=page.locator.return_value.first
        dialog.inner_text.return_value='SQL执行失败 MEM_LIMIT_EXCEEDED 知道了'
        dialog.get_by_role.return_value.count.return_value=1
        dialog.locator.return_value.count.return_value=1
        self.assertTrue(dismiss_editor_memory_notice(page))
        page.wait_for_timeout.assert_called_once_with(100)
        dialog.get_by_role.return_value.click.assert_called_once_with()

    def test_date_only_plan_preserves_every_schedule_setting(self):
        cur=current();before=copy.deepcopy(cur.detail_payload)
        plan=plan_for(cur);validate_plan(plan,plan['plan_sha256'],True)
        self.assertEqual(cur.detail_payload,before)
        changed=copy.deepcopy(plan['replacement_schedule']);changed['dateRange']=before['schedule']['dateRange']
        self.assertEqual(changed,{k:v for k,v in before['schedule'].items() if k not in ('isExpire','taskId')})

    def test_disabled_unexpired_and_outside_domain_are_rejected(self):
        for field,value in [('taskStatus',False),('isExpire',False)]:
            cur=current();cur.detail_payload['schedule'][field]=value
            with self.assertRaises(UsageError):plan_for(cur)
        cur=current()
        with self.assertRaises(UsageError):build_renewal_plan(domain='qingcheng',current=cur,start=date.today(),end=date.today()+timedelta(days=1))

    def test_period_bounds_and_missing_metadata(self):
        for a,b in [(date.today()-timedelta(days=1),date.today()),(date.today(),date.today()),(date.today(),date.today()+timedelta(days=91))]:
            with self.assertRaises(UsageError):validate_range(a,b)
        with self.assertRaises(UsageError):parameter_values({})

    def test_hash_confirmation_and_rehashed_scope_tampering_blocked(self):
        p=plan_for()
        with self.assertRaises(UsageError):validate_plan(p,p['plan_sha256'],False)
        with self.assertRaises(UsageError):validate_plan(p,'0'*64,True)
        p['replacement_schedule']['alarmReceiver']=['another']
        p['plan_sha256']=digest({k:v for k,v in p.items() if k!='plan_sha256'})
        with self.assertRaises(UsageError):validate_plan(p,p['plan_sha256'],True)

    def test_current_sql_fields_schedule_and_identity_drift_blocked(self):
        p=plan_for()
        mutations=[lambda c:setattr(c,'execute_sql','select 2 as value'),
                   lambda c:c.detail_payload['dataParamList'][0].update(showName='renamed'),
                   lambda c:c.detail_payload['schedule'].update(taskId='different')]
        # Dataclasses are frozen; replace rather than mutating the SQL attribute.
        from dataclasses import replace
        c=replace(current(),execute_sql='select 2 as value')
        with self.assertRaises(UsageError):verify_current(p,c)
        for change in mutations[1:]:
            c=current();change(c)
            with self.assertRaises(UsageError):verify_current(p,c)

    def test_network_gate_rejects_sql_field_scope_and_schedule_changes(self):
        p=plan_for();body=payload_for(p);verify_save_payload(p,body)
        for k,v in [('id','menu_set_other'),('executeSql','select 2'),('dataSourceId','other'),('extra','value')]:
            bad=copy.deepcopy(body);bad[k]=v
            with self.assertRaises(UsageError):verify_save_payload(p,bad)
        bad=copy.deepcopy(body);bad['schedule']['synchronizationFrequency']['timeHourMinuteList']=['12:00']
        with self.assertRaises(UsageError):verify_save_payload(p,bad)
        bad=copy.deepcopy(body);bad['dataParamList'][0]['showName']='rename'
        with self.assertRaises(UsageError):verify_save_payload(p,bad)

    def test_same_intent_cannot_repeat_even_after_new_plan_timestamp(self):
        p=plan_for();body=payload_for(p);progress={}
        with tempfile.TemporaryDirectory() as td:
            claim_single_write(p,body,Path(td),progress)
            self.assertTrue(progress['write_request_sent'])
            with self.assertRaises(UsageError):claim_single_write(p,body,Path(td),progress)
            p2=plan_for()
            with self.assertRaises(UsageError):claim_single_write(p2,body,Path(td),{})

    def test_observed_wire_families_keep_exact_numeric_type_code(self):
        for physical,wire,code in [('VARCHAR','TEXT',11),('CHAR','TEXT',12),('TINYINT','NUM',1),('INT','NUM',3),('BIGINT','NUM',4),('DOUBLE','NUM',6),('DECIMAL','NUM',7)]:
            detail=current().detail_payload
            detail['dataParamList'][0].update(fieldType=physical,dataTypeCode=code)
            p=plan_for(DataCenterDatasetSql(dataset=current().dataset,
                execute_sql=current().execute_sql,data_source_id='source',open_external='0',detail_payload=detail))
            self.assertEqual(p['parameters'][0]['fieldType'],wire)
            body=payload_for(p);verify_save_payload(p,body)
            body['dataParamList'][0]['dataTypeCode']=999
            with self.assertRaises(UsageError):verify_save_payload(p,body)

    def test_readback_accepts_only_renewed_dates_and_derived_task_id(self):
        p=plan_for();saved=current()
        saved.detail_payload['schedule']={**copy.deepcopy(p['replacement_schedule']),'taskId':'new','isExpire':False}
        self.assertTrue(verify_readback(p,saved)['fully_verified'])
        saved.detail_payload['schedule']['alarmReceiver']=['changed']
        with self.assertRaises(UsageError):verify_readback(p,saved)
