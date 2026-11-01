from __future__ import annotations
import copy
import sys
import tempfile
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock,patch
import json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from _shared.errors import UsageError
from usql_web_query.data_center_period_renewal import (
    DataCenterPeriodRenewalExecutor, build_period_renewal_plan,
    prove_period_narrowing, validate_period_plan,
)
from usql_web_query.data_center_schedule import digest
from usql_web_query.data_center import DataCenterScheduleRun
from test_data_center_schedule_renewal import current, payload_for

OLD="select value from sample where qici >= '20260626期' and cast(raw_day as date) >= date '2026-05-11' -- keep\n"
NEW=OLD.replace('20260626','20260925').replace('2026-05-11','2026-09-21')


class PeriodRenewalGates(TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.baseline=self.root/'baseline.sql';self.baseline.write_text(OLD,encoding='utf-8')
        self.candidate=self.root/'candidate.sql';self.candidate.write_text(NEW,encoding='utf-8')
        self.live=replace(current(),execute_sql=OLD)
        self.plan=build_period_renewal_plan(domain='market',current=self.live,
             baseline_file=self.baseline,sql_file=self.candidate,candidate=NEW,
             start=date.today(),end=date.today()+timedelta(days=90))

    def test_only_forward_date_literals_and_all_other_bytes_preserved(self):
        proof=prove_period_narrowing(OLD,NEW)
        self.assertEqual(len(proof),2)
        self.assertEqual(validate_period_plan(self.plan,self.plan['plan_sha256'],True),NEW)

    def test_widening_numbers_multiple_statements_and_non_queries_rejected(self):
        for after in [OLD.replace('20260626','20260101'),OLD+'select 2;',
                      'delete from sample',OLD.replace("'20260626期'",'42')]:
            with self.assertRaises(Exception):prove_period_narrowing(OLD,after)

    def test_case_fields_dept_joins_formula_comments_and_whitespace_changes_rejected(self):
        for after in [NEW.replace('select value','select value+1 as value'),
                      NEW.replace('from sample','from other'),NEW.replace('-- keep','-- changed'),
                      NEW.replace('where','where department=\'different\' and'),NEW.replace('select ','select  '),
                      NEW.replace('value from','case when value=1 then 2 else value end as value from')]:
            with self.assertRaises(Exception):prove_period_narrowing(OLD,after)

    def test_negative_or_non_where_bounds_cannot_broaden_scope(self):
        for a in ["select value from sample where not(qici >= '20260626期')\n",
                  "select value from sample where qici >= '20260626期' or value=1\n",
                  "select case when qici >= '20260626期' then 1 else 0 end as value from sample\n"]:
            with self.assertRaises(UsageError):prove_period_narrowing(a,a.replace('20260626','20260925'))

    def test_no_change_and_missing_or_stale_baselines_rejected(self):
        with self.assertRaises(UsageError):prove_period_narrowing(OLD,OLD)
        self.baseline.write_text('select 2',encoding='utf-8')
        with self.assertRaises(UsageError):validate_period_plan(self.plan,self.plan['plan_sha256'],True)

    def test_confirmation_hash_file_and_schedule_tampering_blocked(self):
        with self.assertRaises(UsageError):validate_period_plan(self.plan,self.plan['plan_sha256'],False)
        with self.assertRaises(UsageError):validate_period_plan(self.plan,'0'*64,True)
        bad=copy.deepcopy(self.plan);bad['replacement_schedule']['alarmReceiver']=['other']
        bad['plan_sha256']=digest({k:v for k,v in bad.items() if k!='plan_sha256'})
        with self.assertRaises(UsageError):validate_period_plan(bad,bad['plan_sha256'],True)
        self.candidate.write_text(NEW+'-- drift\n',encoding='utf-8')
        with self.assertRaises(UsageError):validate_period_plan(self.plan,self.plan['plan_sha256'],True)

    def test_native_save_accepts_only_exact_candidate_fields_schedule_and_one_intent(self):
        executor=DataCenterPeriodRenewalExecutor(page=None,client=None,plan=self.plan,candidate=NEW,claim_dir=self.root/'claims')
        projected={**self.plan,'sql_sha256':self.plan['candidate_sql_sha256']}
        body=payload_for(projected);body['executeSql']=NEW
        old=copy.deepcopy(body);old['executeSql']=OLD
        with self.assertRaises(UsageError):executor.claim_write(old)
        bad=copy.deepcopy(body);bad['dataParamList'][0]['showName']='changed'
        with self.assertRaises(UsageError):executor.claim_write(bad)
        executor.claim_write(body)
        self.assertEqual(executor.progress['write_request_count'],1)
        another=DataCenterPeriodRenewalExecutor(page=None,client=None,plan=self.plan,candidate=NEW,claim_dir=self.root/'claims')
        with self.assertRaises(UsageError):another.claim_write(body)

    def test_readback_requires_candidate_fields_and_unexpired_dates(self):
        executor=DataCenterPeriodRenewalExecutor(page=None,client=None,plan=self.plan,candidate=NEW,claim_dir=self.root/'claims')
        saved=replace(current(),execute_sql=NEW)
        saved.detail_payload['schedule']={**copy.deepcopy(self.plan['replacement_schedule']),'taskId':'new','isExpire':False}
        self.assertTrue(executor.verify_saved(saved)['fully_verified'])
        with self.assertRaises(UsageError):executor.verify_saved(replace(saved,execute_sql=OLD))
        saved.detail_payload['schedule']['taskStatus']=False
        with self.assertRaises(UsageError):executor.verify_saved(saved)

    def test_refresh_requires_bound_flag_and_exact_saved_state(self):
        executor=DataCenterPeriodRenewalExecutor(page=None,client=None,plan=self.plan,candidate=NEW,claim_dir=self.root/'claims')
        with self.assertRaises(UsageError):executor.refresh_saved_once(artifacts_dir=self.root,timeout_ms=1)
        plan=copy.deepcopy(self.plan);plan['refresh_after_save']=True
        plan['plan_sha256']=digest({k:v for k,v in plan.items() if k!='plan_sha256'})
        executor=DataCenterPeriodRenewalExecutor(page=None,client=None,plan=plan,candidate=NEW,claim_dir=self.root/'claims')
        with self.assertRaises(UsageError):executor.refresh_saved_once(artifacts_dir=self.root,timeout_ms=1)

    def test_post_save_refresh_uses_fresh_child_hash_and_one_exact_native_request(self):
        plan=copy.deepcopy(self.plan);plan['refresh_after_save']=True
        plan['plan_sha256']=digest({k:v for k,v in plan.items() if k!='plan_sha256'})
        saved=replace(current(),execute_sql=NEW)
        saved.detail_payload['schedule']={**copy.deepcopy(plan['replacement_schedule']),'taskId':'new','isExpire':False}
        page=MagicMock();client=MagicMock()
        client.discover_datasets.return_value=[saved.dataset]
        client.fetch_dataset_sql.return_value=saved
        client.fetch_schedule_runs.return_value=[]
        executor=DataCenterPeriodRenewalExecutor(page=page,client=client,plan=plan,candidate=NEW,claim_dir=self.root/'claims')
        executor.claim_dir.mkdir()
        executor.progress['write_request_count']=1
        def trigger(**kwargs):
            self.assertEqual(kwargs['schedule_task_id'],'new')
            guard=page.route.call_args.args[1]
            wrong=MagicMock();wrong.request.post_data=json.dumps({'id':'other'})
            guard(wrong);wrong.abort.assert_called_once()
            good=MagicMock();good.request.post_data=json.dumps({'id':'new'})
            guard(good);good.continue_.assert_called_once()
            repeat=MagicMock();repeat.request.post_data=good.request.post_data
            guard(repeat);repeat.abort.assert_called_once()
            return datetime.now().astimezone().isoformat(),{'status':'success','errorCode':0}
        from datetime import datetime
        run=DataCenterScheduleRun(id='fresh',start_time='2026-10-29 15:00:00',end_time='2026-10-29 15:00:01',elapsed_seconds=1,status='SUCCESS')
        module='usql_web_query.data_center_period_renewal'
        with patch(module+'.trigger_synchronization',side_effect=trigger),patch(module+'.poll_for_new_success',return_value=run):
            result=executor.refresh_saved_once(artifacts_dir=self.root,timeout_ms=1000)
        self.assertTrue(result['fully_verified'])
        self.assertEqual(result['refresh_request_count'],1)
        child=json.loads(Path(result['refresh_step_plan']).read_text())
        given=child.pop('plan_sha256')
        self.assertEqual(given,digest(child))
        self.assertEqual(child['sql_sha256'],plan['candidate_sql_sha256'])
        self.assertEqual(child['execution_budget'],1)
