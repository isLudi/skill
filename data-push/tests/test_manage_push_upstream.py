from argparse import Namespace
import copy
import json

import pytest
from playwright.sync_api import Error as PlaywrightError

from lark_delivery.integrations.producer_bindings import read_binding_document
import manage_push_upstream as maintenance
from manage_push_upstream import _replace_binding, _require_latest, _updated_binding


def _evidence(source, version_id=224569):
    return {
        "version_id": version_id,
        "version_label": "V42",
        "source_sha256": source,
        "exec_file_id": 871466,
        "execution_id": 181803615,
        "execution_start": "2026-11-12T09:40:03+08:00",
        "execution_period": "2026-11-12T09:00:00+08:00",
    }


def test_update_keeps_the_rest_of_the_producer_contract():
    original = read_binding_document("qingcheng.process", expected_domain="qingcheng")
    source = original["upstream"]["source_sha256"]
    evidence = _evidence(source)
    args = Namespace(approve_source_sha256=None, review_reference="verified release review")

    updated = _updated_binding(original, evidence, args)

    preserved = copy.deepcopy(updated)
    for key in ("release_name", "bound_execution_id", "bound_execution_start"):
        preserved[key] = original[key]
    del preserved["release_review"]
    for key in ("published_version", "version_id", "exec_file_id"):
        preserved["upstream"][key] = original["upstream"][key]
    original_contract = copy.deepcopy(original)
    original_contract.pop("release_review", None)
    assert preserved == original_contract
    assert updated["upstream"]["version_id"] == evidence["version_id"]
    assert updated["upstream"]["exec_file_id"] == evidence["exec_file_id"]
    assert updated["release_review"]["association"] == "explicitly_reviewed_mapping"
    assert _updated_binding(updated, evidence, args) is None


def test_changed_hash_needs_approval_of_the_actual_source():
    original = read_binding_document("qingcheng.process", expected_domain="qingcheng")
    source = "b" * 64
    evidence = _evidence(source)
    args = Namespace(approve_source_sha256=None, review_reference="verified release review")

    with pytest.raises(ValueError, match="requires exact"):
        _updated_binding(original, evidence, args)
    args.approve_source_sha256 = "a" * 64
    with pytest.raises(ValueError, match="does not match"):
        _updated_binding(original, evidence, args)
    args.approve_source_sha256 = source
    assert _updated_binding(original, evidence, args)["upstream"]["source_sha256"] == source


def test_reviewed_traffic_field_count_is_bound_to_the_release():
    original = read_binding_document("qingcheng.process", expected_domain="qingcheng")
    evidence = {**_evidence(original["upstream"]["source_sha256"]), "audit_field_count": 50}
    args = Namespace(approve_source_sha256=None, review_reference="traffic fields verified")
    updated = _updated_binding(original, evidence, args)
    assert updated["upstream"]["audit_field_count"] == 50
    assert updated["release_review"]["audit_field_count"] == 50
    assert _updated_binding(updated, evidence, args) is None


@pytest.mark.parametrize("kind,fields", [("process", 33), ("process", 50), ("process", 51), ("conversion", 31), ("conversion", 48), ("conversion", 49)])
def test_qingcheng_evidence_accepts_only_reviewed_field_counts(kind, fields):
    target = "tblTrafficFields"
    periods = {period: {"row_count": 1, "channel_counts": {"私域表单": 1}, "snapshots": [["20261115", "14"]]}
               for period in ("20261113期", "20261120期")}
    manifest = {"field_count": fields, "row_count": 2, "periods": periods}
    label = "过程" if kind == "process" else "转化"
    log = "\n".join([f"目标多维表格校验通过：table_id={target}", f"目标字段校验通过：{fields}个字段",
                     "写入前清空回读确认：0条", "新记录回读校验通过", "新记录创建完成：2条", "最终回读校验通过：2条",
                     kind + "表快照清单：" + json.dumps(manifest, ensure_ascii=False),
                     f"SUCCESS: 青橙项目部最新两期{label}数据已独立覆盖写入并回读通过", "exit_code:  0"])
    key = "qingcheng.process" if kind == "process" else "qingcheng.transformation"
    assert maintenance._qingcheng_evidence(log, key, target)["field_count"] == fields
    with pytest.raises(ValueError, match="unreviewed"):
        maintenance._qingcheng_evidence(log.replace('"field_count": ' + str(fields), '"field_count": 52'), key, target)


def test_atomic_replace_rejects_drift(tmp_path):
    path = tmp_path / "producer.json"
    baseline = b'{"exec_file_id": 1}'
    path.write_bytes(baseline)
    _replace_binding(path, baseline, {"exec_file_id": 2})
    assert json.loads(path.read_bytes()) == {"exec_file_id": 2}

    with pytest.raises(ValueError, match="changed during"):
        _replace_binding(path, baseline, {"exec_file_id": 3})
    assert json.loads(path.read_bytes()) == {"exec_file_id": 2}
    assert list(tmp_path.iterdir()) == [path]


def test_started_newer_execution_blocks_adoption():
    execution = {"id": 10, "startTime": "2026-11-12 09:40:00"}
    future = {"id": 11, "status": 0, "planRunTime": "2026-11-12 13:40:00"}
    _require_latest({"executions": [execution, future]}, execution)
    future["dispatchTime"] = "2026-11-12 13:40:00"
    with pytest.raises(ValueError, match="may have replaced"):
        _require_latest({"executions": [execution, future]}, execution)


def test_transient_transport_errors_are_retried_and_sanitized(monkeypatch, capsys):
    args = Namespace(task_key="qingcheng.process")
    delays = []
    attempts = []

    def failing_read(*_):
        attempts.append(True)
        raise PlaywrightError("ECONNRESET request headers: cookie=private-test-value")

    monkeypatch.setattr(maintenance, "_arguments", lambda: args)
    monkeypatch.setattr(maintenance, "_run", lambda args: maintenance._prepare_evidence({}, args))
    monkeypatch.setattr(maintenance, "_read_evidence", failing_read)
    monkeypatch.setattr(maintenance.time, "sleep", delays.append)

    assert maintenance.main() == 1
    output = capsys.readouterr()
    assert json.loads(output.out)["reason"] == "Tiangong2 read-only session unavailable after retry"
    assert not output.err
    assert len(attempts) == 3 and delays == [1, 3]


def test_controlled_qingcheng_adoption_requires_exact_operator_receipt(tmp_path, monkeypatch):
    import sys
    from pathlib import Path
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'usql-web-query-operator/scripts'))
    from _shared import config
    from tiangong2_task.publishing import finalize_hash
    monkeypatch.setattr(config,'TIANGONG2_TASK_RUNTIME_DIR',tmp_path)
    binding=read_binding_document('qingcheng.process',expected_domain='qingcheng')
    scope={key:binding['upstream'][key] for key in maintenance.SCOPE_FIELDS}
    scope['owner_name']=binding['upstream']['owner']
    source='a'*64
    plan=finalize_hash({'schema_version':'tiangong2-task-execution-plan-v1',
        'operation':'execute_owned_published_tiangong2_task_once','scope':scope,
        'execution':{'period_time':'2026-11-13 17:00:00','trigger_successor':False,'params':{},'disabled_stages':[]},
        'baseline':{'latest_published_version_id':42,'current_source_sha256':source,'baseline_execution_ids':[99]}},'plan_sha256')
    plan_file=tmp_path/'plan.json';plan_file.write_text(json.dumps(plan),encoding='utf-8')
    receipt=finalize_hash({'schema_version':'tiangong2-task-execution-receipt-v1','scope':scope,
        'ok':True,'fully_verified':True,'manual_attention_required':False,'execute_request_sent':True,
        'plan_file':str(plan_file),'plan_sha256':plan['plan_sha256'],'execution_id':100,'trigger_successor':False},'receipt_sha256')
    receipt_file=tmp_path/'receipt.json';receipt_file.write_text(json.dumps(receipt),encoding='utf-8')
    execution={'id':100,'periodTime':'2026-11-13 17:00:00','runConfig':json.dumps({'triggerSuccessor':False,'disabledStages':[],'rerunTaskId':None})}
    args=Namespace(execution_receipt=receipt_file)
    maintenance._verify_controlled_execution(binding,None,execution,(42,'V42','',source),args)
    with pytest.raises(ValueError):maintenance._verify_controlled_execution(binding,None,execution,(43,'V43','',source),args)
    with pytest.raises(ValueError):maintenance._verify_controlled_execution(binding,None,execution,(42,'V42','','b'*64),args)
    with pytest.raises(ValueError):maintenance._verify_controlled_execution(binding,None,execution,(42,'V42','',source),Namespace(execution_receipt=None))
    changed=copy.deepcopy(execution);changed['id']=101
    with pytest.raises(ValueError):maintenance._verify_controlled_execution(binding,None,changed,(42,'V42','',source),args)
    receipt['trigger_successor']=True
    receipt_file.write_text(json.dumps(receipt),encoding='utf-8')
    with pytest.raises(ValueError):maintenance._verify_controlled_execution(binding,None,execution,(42,'V42','',source),args)


class PublishedTask:
    def __init__(self, code):
        self.code = code

    def list_versions(self, task_id):
        assert task_id == 47252
        return [{"id": 99, "ver": "V99", "publishTime": "2026-11-14 12:50:00", "status": "已发布"}]

    def get_version_code(self, version_id):
        assert version_id == 99
        return {"code": self.code}


def test_market_mapping_version_is_bound_to_the_published_source():
    code = 'CHANNEL_MAPPING_VERSION = "1113"\nquery_sql = "SELECT 1 AS value"\n'
    publication = maintenance._publication(PublishedTask(code), 47252, "1113")
    assert publication[0] == 99
    assert publication[3] == maintenance._sha256(code.encode("utf-8"))
    with pytest.raises(ValueError, match="unique published source marker"):
        maintenance._publication(PublishedTask(code), 47252, "1030")
    with pytest.raises(ValueError, match="unique published source marker"):
        maintenance._publication(PublishedTask(code + 'CHANNEL_MAPPING_VERSION = "1113"\n'), 47252, "1113")
    assert maintenance._publication(PublishedTask("legacy source"), 47252)[0] == 99


def test_market_mapping_version_adoption_keeps_consumer_contracts():
    original = read_binding_document("market_consultant.leads", expected_domain="market_consultant")
    original["channel_mapping_version"] = "1030"
    source = "c" * 64
    evidence = {**_evidence(source), "channel_mapping_version": "1113"}
    args = Namespace(approve_source_sha256=source, review_reference="1113 source and Base review", channel_mapping_version="1113")
    updated = _updated_binding(original, evidence, args)
    assert original["channel_mapping_version"] == "1030"
    assert updated["channel_mapping_version"] == "1113"
    assert updated["release_review"]["channel_mapping_version"] == "1113"
    assert updated["upstream"]["verified_source_sha256"] == source
    for field in ("target_table_id", "schedule_interval_hours", "schedule_start_minute", "schedule_anchor_hour", "task_key"):
        assert updated[field] == original[field]
    assert _updated_binding(updated, evidence, args) is None
    with pytest.raises(ValueError, match="mapping evidence differs"):
        _updated_binding(original, {**evidence, "channel_mapping_version": "1030"}, args)
    with pytest.raises(ValueError, match="mapping evidence differs"):
        _updated_binding(original, evidence, Namespace(**{**vars(args), "channel_mapping_version": None}))


def test_marker_only_registry_correction_is_not_skipped():
    original = read_binding_document("market_consultant.leads", expected_domain="market_consultant")
    original["channel_mapping_version"] = "1030"
    evidence = {**_evidence(original["upstream"]["verified_source_sha256"]),
                "version_id": original["upstream"]["verified_version_id"],
                "exec_file_id": original["upstream"]["exec_file_id"], "channel_mapping_version": "1113"}
    args = Namespace(approve_source_sha256=None, review_reference="marker correction review", channel_mapping_version="1113")
    assert _updated_binding(original, evidence, args)["channel_mapping_version"] == "1113"


def test_mapping_flag_is_limited_to_market_leads_and_default_is_unchanged():
    original = read_binding_document("market_consultant.leads", expected_domain="market_consultant")
    assert maintenance._reviewed_market_binding(original, Namespace()) is original
    for producer, domain in (("market_consultant.volume", "market_consultant"), ("qingcheng.process", "qingcheng")):
        binding = read_binding_document(producer, expected_domain=domain)
        with pytest.raises(ValueError, match="market lead producer"):
            maintenance._reviewed_market_binding(binding, Namespace(channel_mapping_version="1113"))
    with pytest.raises(ValueError, match="four digits"):
        maintenance._reviewed_market_binding(original, Namespace(channel_mapping_version="20261113"))


def test_market_mapping_flag_preserves_scheduled_execution_requirement():
    binding = read_binding_document("market_consultant.leads", expected_domain="market_consultant")
    with pytest.raises(ValueError, match="Qingcheng operator receipt"):
        maintenance._verify_controlled_execution(binding, None, {}, (), Namespace(channel_mapping_version="1113", execution_receipt=None))


def test_mapping_version_cli_defaults_and_producer_scope(monkeypatch):
    import sys
    base = ["manage_push_upstream.py", "verify", "market_consultant.leads",
            "--version-id", "99", "--exec-file-id", "100", "--execution-id", "101"]
    monkeypatch.setattr(sys, "argv", base)
    assert maintenance._arguments().channel_mapping_version is None
    monkeypatch.setattr(sys, "argv", base + ["--channel-mapping-version", "1113"])
    assert maintenance._arguments().channel_mapping_version == "1113"
    monkeypatch.setattr(sys, "argv", base + ["--channel-mapping-version", "20261113"])
    with pytest.raises(SystemExit):
        maintenance._arguments()
    changed = list(base)
    changed[2] = "market_consultant.volume"
    monkeypatch.setattr(sys, "argv", changed + ["--channel-mapping-version", "1113"])
    with pytest.raises(SystemExit):
        maintenance._arguments()
