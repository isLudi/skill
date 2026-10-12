"""Internal books uses existing batches without coupling their failure outcomes."""
from copy import deepcopy
from datetime import datetime, timedelta
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]/"scripts"
sys.path.insert(0,str(SCRIPTS))
import qingcheng_internal_books as books
import qingcheng_internal_books_source as source
import run_qingcheng_partner_process as partner
import run_qingcheng_transformation as conversion

ZONE = ZoneInfo("Asia/Shanghai")
SLOT = datetime(2026,10,13,13,50,tzinfo=ZONE)


def sources(scores, *, report_type="process"):
    processes, conversions = [], []
    for name,grade,score in scores:
        identity = {"qici":"20261009期","xiaozu":"主管甲","employee_email_name":name,"grade_1":grade}
        processes.append({**identity,"v_lead":10,"is_friend_lead":5,"first_call_time_diff_hour":20,
            "is_long_call":score*10,"first_call_in_24h":8,"first_call_connected_cnt":7,
            "call_duration":21,"zong_call_ci":30,"daoke1":5})
        conversions.append({**identity,"v_lead":10,"pay_user":2,"pay_sub":3,"income":score*10,
            "refund":0,"promit":score*10,"p_income":score*10,"podan":2,"sc":4})
    result = {"snapshot":["20261010","11"]}
    for model,rows in (("2064",processes),("2460",conversions)):
        if model == "2460" and report_type == "process":
            continue
        result[model] = {"model":model,"rows":rows,"query_id":"123","complete":True,"sql_sha256":"a"*64}
    return result


def build_review(monkeypatch, tmp_path, data, report_type="process"):
    monkeypatch.setattr(books,"_table_image",lambda *args,**kwargs:None)
    tmp_path.mkdir(parents=True,exist_ok=True)
    return books.build(books.config(),data,report_type,"20261009期",tmp_path)


def test_process_ties_are_all_reminded_separately_by_grade(monkeypatch,tmp_path):
    data = sources([("甲","高一",0),("乙","高一",0),("丙","高一",.1),
                    ("丁","高二",.12341),("戊","高二",.12344)])
    review = build_review(monkeypatch,tmp_path,data)
    item = review["results"]["internal_books"]["levels"]["consultant"]
    assert {p["name"] for p in item["reminder_by_grade"]["高一"]} == {"甲","乙"}
    assert [p["name"] for p in item["reminder_by_grade"]["高二"]] == ["丁"]
    assert all(p["account"] is None for g in item["reminder_by_grade"].values() for p in g)


def test_conversion_cutoff_ties_and_small_grades_all_reminded(monkeypatch,tmp_path):
    data = sources([("甲","高一",4),("乙","高一",3),("丙","高一",2),("丁","高一",2),
                    ("戊","高一",1),("己","高二",.5)],report_type="transformation")
    review = build_review(monkeypatch,tmp_path,data,"transformation")
    item = review["results"]["internal_books"]["levels"]["consultant"]
    assert {p["name"] for p in item["reminder_by_grade"]["高一"]} == {"甲","乙","丙","丁"}
    assert [p["name"] for p in item["reminder_by_grade"]["高二"]] == ["己"]
    assert books._display_conversion(123.45,"综合营收") == "123.5"
    assert books._display_conversion(10,"有效线索") == "10"


def test_conversion_denominator_mismatch_and_finance_mismatch_block():
    data = sources([("甲","高一",4)],report_type="transformation")
    data["2460"]["rows"][0]["v_lead"] = 11
    with pytest.raises(ValueError,match="denominators"):
        books.aggregate(data,"transformation",3)
    data["2460"]["rows"][0].update(v_lead=10,promit=39)
    with pytest.raises(ValueError,match="reconcile"):
        books.aggregate(data,"transformation",3)


@pytest.mark.parametrize("base_failed,internal_failed",[(False,True),(True,False)])
def test_partner_batch_source_failure_does_not_cross_branches(monkeypatch,tmp_path,base_failed,internal_failed):
    cfg = deepcopy(partner._config())
    cfg["channels"][-1]["scheduled"] = True
    monkeypatch.setattr(partner,"_config",lambda **kwargs:cfg)
    monkeypatch.setattr(partner,"_slot",lambda *args:SLOT)
    def base(**kwargs):
        if base_failed:
            raise ValueError("partner Base unavailable")
        return {"period":"20261016期","slot":SLOT.isoformat(),"channels":{
            ch:{"status":"sent_verified"} for ch in partner.CHANNEL_IDS}}
    def prepare(*args):
        if internal_failed:
            raise ValueError("internal Data Center unavailable")
        return {}
    delivered = []
    monkeypatch.setattr(partner,"_run_base",base)
    monkeypatch.setattr(books,"prepare",prepare)
    monkeypatch.setattr(books,"deliver",lambda *args:delivered.append("internal_books") or {"status":"sent_verified"})
    result = partner.run(now=SLOT,output=tmp_path)
    assert result["channels"]["internal_books"]["status"] == ("blocked" if internal_failed else "sent_verified")
    assert all(result["channels"][ch]["status"] == ("blocked" if base_failed else "sent_verified")
               for ch in partner.CHANNEL_IDS)
    assert delivered == ([] if internal_failed else ["internal_books"])


@pytest.mark.parametrize("failure",["request","receipt"])
def test_invalid_partner_channel_state_does_not_block_siblings(monkeypatch,tmp_path,failure):
    cfg = partner._config()
    monkeypatch.setattr(partner,"_config",lambda **kwargs:cfg)
    monkeypatch.setattr(partner,"_slot",lambda *args:SLOT)
    def existing(path):
        if failure == "receipt" and path.parent.name == "partner_books":
            raise ValueError("one malformed channel receipt")
        return None
    monkeypatch.setattr(partner,"_existing",existing)
    def validate(entry):
        if failure == "request" and entry["id"] == "partner_books":
            raise ValueError("one malformed channel request")
    monkeypatch.setattr(partner,"_validate_entry",validate)
    monkeypatch.setattr(partner,"_upstream_audit",lambda *args:{"raw_channel_counts":{"河南本地化":10,"武汉图书":10}})
    monkeypatch.setattr(partner,"_source",lambda *args:([{"渠道":"河南本地化"}],{"rev":1,"snapshot":["20261013","10"]}))
    monkeypatch.setattr(partner,"_expected",lambda *args:1)
    monkeypatch.setattr(partner,"_build",lambda *args:{})
    delivered = []
    monkeypatch.setattr(partner,"_deliver",lambda entry,*args:delivered.append(entry["id"]) or {"status":"sent_verified"})
    result = partner._run_base(now=SLOT,output=tmp_path)
    assert result["channels"]["partner_books"]["status"] == "blocked"
    assert delivered == ["partner_local","supervisor_local"]


@pytest.mark.parametrize("failed_channel",["internal_books","partner_books"])
def test_conversion_send_failure_does_not_stop_other_channels(monkeypatch,tmp_path,failed_channel):
    batch = {"channels":[{"id":"internal_books"},{"id":"partner_books"}]}
    result = {"period":"20261009期","channels":{ch:{"review":{},"process_rev":1,"conversion_rev":2,
        "groups":{"consultant":{"status":"prepared"}}} for ch in ("internal_books","partner_books")}}
    sent = []
    def send(channel):
        sent.append(channel)
        if channel == failed_channel:
            raise ValueError("one account lookup failed")
        return {"status":"sent_verified"}
    monkeypatch.setattr(books,"deliver",lambda *args:send("internal_books"))
    monkeypatch.setattr(conversion,"_send_group",lambda channel,*args:send(channel))
    monkeypatch.setattr(conversion,"probe_revision",lambda *args:1)
    monkeypatch.setattr(conversion,"_probe_conversion_rev",lambda *args:2)
    conversion._deliver_groups(batch,result,tmp_path,SLOT)
    assert sent == ["internal_books","partner_books"]
    assert result["channels"][failed_channel]["groups"]["consultant"]["status"] == "blocked"
    other = next(ch for ch in sent if ch != failed_channel)
    assert result["channels"][other]["groups"]["consultant"]["status"] == "sent_verified"
    assert conversion._channel_levels("internal_books","dept") == ()


def test_conversion_prepare_failure_does_not_stop_later_channel(monkeypatch,tmp_path):
    batch = {"channels":[{"id":"partner_books","scheduled":True},{"id":"internal_books","scheduled":True}]}
    monkeypatch.setattr(conversion,"_batch",lambda:batch)
    monkeypatch.setattr(conversion,"fetch",lambda *args:(_ for _ in ()).throw(ValueError("Base unavailable")))
    monkeypatch.setattr(books,"prepare",lambda *args:{"process_snapshot":"20261010 11:00","conversion_snapshot":"20261010 11:00"})
    monkeypatch.setattr(conversion,"_index",lambda *args:None)
    result = conversion.run(period_date="20261009",output=tmp_path,audience="standard")
    assert result["channels"]["partner_books"]["groups"]["consultant"]["status"] == "blocked_prepare"
    assert result["channels"]["internal_books"]["groups"]["consultant"]["status"] == "prepared"


def test_conversion_profile_parse_failure_does_not_block_internal_books(monkeypatch,tmp_path):
    batch = {"channels":[{"id":"partner_books","scheduled":True},{"id":"internal_books","scheduled":True}]}
    monkeypatch.setattr(conversion,"_batch",lambda:batch)
    def levels(channel,*args):
        if channel == "partner_books":
            raise ValueError("one profile cannot be parsed")
        return ("consultant",)
    monkeypatch.setattr(conversion,"_channel_levels",levels)
    monkeypatch.setattr(books,"prepare",lambda *args:{"process_snapshot":"20261010 11:00","conversion_snapshot":"20261010 11:00"})
    monkeypatch.setattr(conversion,"_index",lambda *args:None)
    result = conversion.run(period_date="20261009",output=tmp_path,audience="standard")
    assert result["channels"]["partner_books"]["groups"]["configuration"]["status"] == "blocked_prepare"
    assert result["channels"]["internal_books"]["groups"]["consultant"]["status"] == "prepared"


@pytest.mark.parametrize("evidence",[
    {"state":"success_with_rows","preview":{"no_more":False}},
    {"state":"success_with_rows","preview":{"no_more":True,"headers":["qici"],"rows":[["20261009期"]]*1000}},
])
def test_incomplete_or_bounded_result_cannot_be_sent(monkeypatch,tmp_path,evidence):
    (tmp_path/"summary.json").write_text(json.dumps({"ok":True,"query_id":"123"}),encoding="utf-8")
    monkeypatch.setattr(source,"_result_rows",lambda *args:evidence)
    with pytest.raises(ValueError,match="incomplete|bounded"):
        source._query("2064","select 1","20261009期",tmp_path)


@pytest.mark.parametrize("old_summary",[False,True])
def test_unknown_query_outcome_does_not_submit_another_query(tmp_path,old_summary):
    (tmp_path/"query_attempt.json").write_text('{"status":"started"}',encoding="utf-8")
    if old_summary:
        (tmp_path/"summary.json").write_text('{"ok":true,"query_id":"123"}',encoding="utf-8")
    with pytest.raises(ValueError,match="no outcome"):
        source._query("2064","select 1","20261009期",tmp_path)


def test_operator_chinese_json_with_unset_parent_encoding(monkeypatch):
    monkeypatch.delenv("PYTHONIOENCODING",raising=False)
    monkeypatch.delenv("PYTHONUTF8",raising=False)
    def run(command,**kwargs):
        assert kwargs["env"]["PYTHONIOENCODING"] == "utf-8"
        assert kwargs["env"]["PYTHONUTF8"] == "1"
        assert kwargs["encoding"] == "utf-8"
        return SimpleNamespace(returncode=0,stdout=json.dumps({"period":"20261009期","channel":"内部图书"},ensure_ascii=False))
    monkeypatch.setattr(source.subprocess,"run",run)
    outcome = source._operator_run([source._python(),"-c",
        "import json; print(json.dumps({'period':'20261009期','channel':'内部图书'},ensure_ascii=False))"])
    assert outcome.returncode == 0
    assert json.loads(outcome.stdout) == {"period":"20261009期","channel":"内部图书"}


def test_success_artifact_recovers_the_original_query_without_resubmission(monkeypatch,tmp_path):
    def completed(command):
        query_file = Path(command[command.index("--sql-file")+1])
        query_hash = source.hashlib.sha256(query_file.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
        artifact_file = Path(command[command.index("--result-artifact")+1])
        artifact_file.parent.mkdir(parents=True,exist_ok=True)
        artifact_file.write_text(json.dumps({"artifact_type":"result_artifact","ok":True,"status":"Success",
            "query_id":"123","sql_sha256":query_hash,"editor":{"sql_sha256":query_hash},
            "submission":{"submitted_sql_sha256":query_hash},"validation":{"status":"passed"},"result":{}}),encoding="utf-8")
        raise TypeError("scheduled child stdout was unavailable")
    monkeypatch.setattr(source,"_operator_run",completed)
    with pytest.raises(TypeError):
        source._query("2064","select 1","20261009期",tmp_path)
    monkeypatch.setattr(source,"_operator_run",lambda *args:pytest.fail("successful query must not be submitted again"))
    fields = [*source.PROCESS_FIELDS,"__snapshot_dt","__snapshot_hour"]
    data = sources([("甲","高一",.1)])["2064"]["rows"][0]
    data.update(__snapshot_dt="20261011",__snapshot_hour="19")
    monkeypatch.setattr(source,"_result_rows",lambda query_id:{"state":"success_with_rows", "preview":{
        "headers":fields,"rows":[[data[field] for field in fields]],"no_more":True}})
    result = source._query("2064","select 1","20261009期",tmp_path)
    assert result["query_id"] == "123" and result["complete"] is True
    assert json.loads((tmp_path/"query_attempt.json").read_text(encoding="utf-8"))["status"] == "outcome_recorded"


def test_recovery_rejects_sql_hash_drift_and_ambiguous_queries(tmp_path):
    artifact = {"artifact_type":"result_artifact","ok":True,"status":"Success","query_id":"123",
        "sql_sha256":"a"*64,"editor":{"sql_sha256":"a"*64},"submission":{"submitted_sql_sha256":"a"*64},
        "validation":{"status":"passed"},"result":{}}
    path = tmp_path/"operator/one/result_artifact.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(artifact),encoding="utf-8")
    with pytest.raises(ValueError,match="hash differs"):
        source._recover_outcome(tmp_path,{},"b"*64)
    path2 = tmp_path/"operator/two/result_artifact.json"
    path2.parent.mkdir(parents=True)
    path2.write_text(json.dumps({**artifact,"query_id":"456"}),encoding="utf-8")
    with pytest.raises(ValueError,match="ambiguous"):
        source._recover_outcome(tmp_path,{},"a"*64)


def test_stale_review_cannot_start_a_send():
    stale = (datetime.now(ZONE)-timedelta(hours=6)).strftime("%Y%m%d %H:00")
    with pytest.raises(ValueError,match="stale"):
        books._fresh_review({"process_snapshot":stale,"report_type":"process"},books.config())


def test_known_message_id_is_only_reverified(monkeypatch,tmp_path):
    cfg = books.config()
    review = {"report_type":"process","period":"20261016期"}
    receipt = {"status":"sent_unverified","message_id":"om_saved","period":review["period"],
        "report_type":"process","slot":SLOT.isoformat(),"chat_id":cfg["target"]["chat_id"],
        "image_key":"img_saved","mention_ids":["ou_saved"]}
    (tmp_path/"send_receipt.json").write_text(json.dumps(receipt),encoding="utf-8")
    monkeypatch.setattr(books,"_window",lambda *args:None)
    monkeypatch.setattr(books,"_verify_message",lambda *args:{"verified":True})
    monkeypatch.setattr(books,"_data",lambda *args:pytest.fail("known message must not be resent"))
    assert books.deliver(review,tmp_path,SLOT)["status"] == "sent_verified"


def test_uncertain_retry_keeps_payload_and_idempotency_key(monkeypatch,tmp_path):
    cfg = books.config()
    review = {"report_type":"process","period":"20261016期"}
    receipt = {"status":"send_result_uncertain","period":review["period"],"report_type":"process",
        "slot":SLOT.isoformat(),"chat_id":cfg["target"]["chat_id"],"image_key":"img_saved",
        "mention_ids":[],"markdown":"original payload","idempotency_key":"qcib_saved"}
    (tmp_path/"send_receipt.json").write_text(json.dumps(receipt),encoding="utf-8")
    monkeypatch.setattr(books,"_window",lambda *args:None)
    monkeypatch.setattr(books,"_verify_message",lambda *args:{"verified":True})
    calls = []
    monkeypatch.setattr(books,"_data",lambda args:calls.append(args) or {"message_id":"om_retry"})
    assert books.deliver(review,tmp_path,SLOT)["status"] == "sent_verified"
    assert len(calls) == 2 and "--dry-run" in calls[0] and "--dry-run" not in calls[1]
    assert all(args[args.index("--markdown")+1] == receipt["markdown"] and
               args[args.index("--idempotency-key")+1] == receipt["idempotency_key"] for args in calls)
