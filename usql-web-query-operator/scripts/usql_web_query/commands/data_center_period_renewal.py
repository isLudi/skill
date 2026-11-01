"""Plan/apply an independent, strictly narrowing expired-dataset recovery."""
from __future__ import annotations
import json
from datetime import date, timedelta, datetime, timezone
from _shared.browser import import_playwright
from _shared.env import load_env_file
from _shared.errors import UsageError
from .apply_data_center_sql_replacement import _browser_session
from .data_center_schedule import _write
from usql_web_query.data_center import DataCenterClient, select_dataset_for_replacement
from usql_web_query.data_center_replacement import load_replacement_sql, data_center_replacement_lock
from usql_web_query.data_center_period_renewal import (
    build_period_renewal_plan, validate_period_plan, DataCenterPeriodRenewalExecutor,
)


def cmd_plan_data_center_period_renewal(args):
    load_env_file(args.env_file)
    candidate = load_replacement_sql(args.sql_file)
    start = date.fromisoformat(args.schedule_start) if args.schedule_start else date.today()
    end = date.fromisoformat(args.schedule_end) if args.schedule_end else start + timedelta(days=90)
    with import_playwright()() as p, _browser_session(p,args) as (_,context):
        client = DataCenterClient(context.new_page(),args.state_path)
        client.ensure_authenticated(args.username,args.password)
        dataset = select_dataset_for_replacement(client.discover_datasets(),domain=args.domain,dataset_id=args.dataset_id)
        current = client.fetch_dataset_sql(dataset)
        plan = build_period_renewal_plan(domain=args.domain,current=current,
               baseline_file=args.baseline_file,sql_file=args.sql_file,candidate=candidate,start=start,end=end,
               refresh_after_save=args.refresh_after_save)
    path = args.output_file or args.artifacts_dir / ('period_renewal_plan_'+plan['plan_sha256'][:16]+'.json')
    _write(path,plan)
    print(json.dumps({'ok':True,'status':'ready','plan_file':str(path.resolve()),
          'plan_sha256':plan['plan_sha256'],'narrowing_proof':plan['narrowing_proof'],
          'date_range':plan['replacement_schedule']['dateRange'],'remote_write_performed':False},ensure_ascii=False,indent=2))
    return 0


def cmd_apply_data_center_period_renewal(args):
    plan = json.loads(args.plan_file.read_text(encoding='utf-8'))
    candidate = validate_period_plan(plan,args.expected_plan_sha256,args.confirm_production_write)
    load_env_file(args.env_file)
    path = args.output_file or args.artifacts_dir / ('period_renewal_receipt_'+plan['plan_sha256'][:16]+'.json')
    if path.exists():
        raise UsageError('Recovery receipt already exists; read back its state')
    receipt = {'operation':plan['operation'],'plan_sha256':plan['plan_sha256'],
               'dataset':plan['dataset'],'started_at':datetime.now(timezone.utc).isoformat(),
               'fully_verified':False,'remote_write_performed':False,'automatic_rollback_attempted':False}
    executor = None
    try:
        with data_center_replacement_lock(plan['dataset']['id']):
            with import_playwright()() as p, _browser_session(p,args) as (_,context):
                page = context.new_page()
                client = DataCenterClient(page,args.state_path)
                client.ensure_authenticated(args.username,args.password)
                executor = DataCenterPeriodRenewalExecutor(page=page,client=client,plan=plan,
                           candidate=candidate,claim_dir=args.artifacts_dir/'period_renewal_claims')
                workflow = executor.execute()
                if plan.get('refresh_after_save'):
                    workflow = executor.refresh_saved_once(artifacts_dir=args.artifacts_dir,
                                                          timeout_ms=args.refresh_timeout_ms)
        receipt.update(ok=True,status='success',fully_verified=True,remote_write_performed=True,
                       workflow=workflow,completed_at=datetime.now(timezone.utc).isoformat())
    except Exception as exc:
        progress = dict(executor.progress) if executor else {'phase':'startup'}
        receipt.update(ok=False,status='failed',error_type=type(exc).__name__,
                       error=str(exc) if isinstance(exc,UsageError) else 'Inspect bound phase; no automatic retry',
                       workflow=progress,remote_write_performed=progress.get('write_request_sent',False),
                       manual_attention_required=progress.get('write_request_sent',False),
                       failed_at=datetime.now(timezone.utc).isoformat())
    _write(path,receipt)
    print(json.dumps({**receipt,'receipt_file':str(path.resolve())},ensure_ascii=False,indent=2))
    return 0 if receipt['fully_verified'] else 1
