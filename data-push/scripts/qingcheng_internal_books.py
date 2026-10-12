"""Internal-books adapter used by the existing partner and conversion runners."""
from collections import defaultdict
from datetime import datetime, timedelta
import hashlib
import json
import math
from pathlib import Path
import re
from zoneinfo import ZoneInfo

from lark_delivery.common import resend
from lark_delivery.common.im import upload_image, verify_chat
from lark_delivery.common.reminders import resolve_contacts
from preview_qingcheng_public_pool_process import _table_image, _sort_process_rows, _reminder_by_grade
from preview_qingcheng_transformation import (_sort_rows, _total_transformation, _display_transformation,
    _reminder_consultant_by_grade, FALLBACK_REMINDER)
from send_qingcheng_process import _data, _verify_message, _render_message
from send_qingcheng_transformation import _render_message as _render_conversion
from run_qingcheng_sec_process import _members
from qingcheng_internal_books_source import fetch, live_sources

CONFIG = Path(__file__).resolve().parents[1]/"config/departments/qingcheng/internal_books.json"


class NoEligibleRows(ValueError):
    pass


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix+".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def config():
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    if (cfg["domain"],cfg["channel_id"],cfg["channel"],cfg["status"],cfg["schedule_enabled"],
            cfg["target"]["chat_id"],cfg["report"]["level"],cfg["report"]["minimum_effective_leads"]) != (
            "qingcheng","internal_books","内部图书","active",True,
            "oc_34c7aa744d1bed96c2d97863531f4e7b","顾问",3):
        raise ValueError("Internal-books channel identity or scope differs")
    if cfg["report"]["split_grade"] is not True or cfg["delivery"]["on_mention_gap"] != "invite_then_text":
        raise ValueError("Internal-books grade or mention policy differs")
    return cfg


def _groups(rows):
    result = defaultdict(list)
    for row in rows:
        if not row.get("employee_email_name") or row.get("xiaozu") in (None,"","-","未分配主管"):
            raise ValueError("Internal-books source lacks a consultant or supervisor identity")
        result[(row["qici"],row["xiaozu"],row["employee_email_name"],row["grade_1"])].append(row)
    return result


def aggregate(sources, report_type, minimum):
    def number(row, field):
        value = float(row[field])
        if not math.isfinite(value):
            raise ValueError(f"Internal-books non-finite source field: {field}")
        return value
    pg = _groups(sources["2064"]["rows"])
    cg = _groups(sources["2460"]["rows"]) if report_type == "transformation" else {}
    if report_type == "transformation" and (set(pg) != set(cg) or any(len(g)!=1 for g in cg.values())):
        raise ValueError("Internal-books conversion grain does not match the process source")
    rows = []
    for key, items in sorted(pg.items()):
        total = lambda field: sum(number(row,field) for row in items)
        leads = total("v_lead")
        if report_type == "transformation" and leads != number(cg[key][0],"v_lead"):
            raise ValueError("Internal-books process and conversion lead denominators differ")
        if leads < minimum:
            continue
        out = {"key":key,"主管":key[1],"顾问":key[2],"顾问账号":key[2],"年级":key[3],
               "_accounts":frozenset({key[2]})}
        if report_type == "process":
            metrics = {"有效线索":leads,"好友率":total("is_friend_lead")/leads,
                "等待时长":total("first_call_time_diff_hour")/leads,"8min":total("is_long_call")/leads,
                "24h首call":total("first_call_in_24h")/leads,"沟通率":total("first_call_connected_cnt")/leads,
                "外呼时长":total("call_duration")/leads,"外呼频次":total("zong_call_ci")/leads,
                "总通时":total("call_duration")}
        else:
            src = cg[key][0]
            heads, subjects = number(src,"pay_user"),number(src,"pay_sub")
            income,refund,net = number(src,"income"),number(src,"refund"),number(src,"promit")
            if not math.isclose(income-refund,net,abs_tol=1e-6):
                raise ValueError("Internal-books net amount does not reconcile")
            metrics = {"有效线索":leads,"首节到课率":total("daoke1")/leads,"成交人头_分子":heads,
                "综合人头转化率":heads/leads,"综合订单转化率":subjects/leads,
                "综合营收":income,"退费金额":refund,"净收款":net,"综合单效":net/leads,
                "联报率":subjects/heads if heads else None}
            out.update(_first_lesson=total("daoke1"),_subjects=subjects,_period_income=number(src,"p_income"),
                       _podan=number(src,"podan"),_cycle_num=number(src,"sc"),_cycle_den=heads)
        out["metrics"] = metrics
        rows.append(out)
    return rows


def _display_conversion(value, field, *, integer_fields=frozenset()):
    if field in {"综合营收","退费金额","净收款"}:
        return "—" if value is None else f"{value:,.1f}"
    return _display_transformation(value,field,integer_fields=integer_fields)


def build(config_data, sources, report_type, period, folder):
    rows = aggregate(sources,report_type,config_data["report"]["minimum_effective_leads"])
    if not rows:
        raise NoEligibleRows("Internal-books complete source has no eligible consultants")
    is_process = report_type == "process"
    rows = _sort_process_rows(rows,split_grade=True) if is_process else _sort_rows(rows,split_grade=True,level="顾问")
    columns = config_data["report"]["process_columns" if is_process else "transformation_columns"]
    bars = config_data["visual"]["process_bars" if is_process else "transformation_bars"]
    bar_specs = {}
    for field, (lo,hi,color) in bars.items():
        if hi is None:
            values = [r["metrics"][field] for r in rows if r["metrics"].get(field) is not None]
            maximum = max(values,default=1.0)
            hi = maximum if maximum > lo else lo+1.0
        bar_specs[field] = (lo,hi,color)
    png = "consultant_process.png" if is_process else "consultant_transformation.png"
    kwargs = {} if is_process else {"total_fn":_total_transformation,"display_fn":_display_conversion}
    _table_image(rows,columns,folder/png,"顾问",period,"内部图书",split_grade=True,bar_specs=bar_specs,**kwargs)
    reminders = _reminder_by_grade("顾问",rows) if is_process else _reminder_consultant_by_grade(rows)
    # The source gives names, not email prefixes: never pass a name as an account.
    for people in reminders.values():
        for person in people:
            person["account"] = None
    focus = "8min较低" if is_process else "综合单效较高"
    suffix = "" if is_process else " 🎉🎉🎉"
    lines = [f"- {g}年级{focus}的顾问：{'、'.join(p['name'] for p in people)}{suffix}" for g,people in reminders.items()]
    if not lines and not is_process:
        lines = ["- "+FALLBACK_REMINDER]
    word = "过程" if is_process else "转化"
    message = "\n".join([f"## 🔥 **【{period}】内部图书渠道顾问{word}数据播报**","",
                          f"![顾问维度{word}数据]({png})","",*lines])+"\n"
    message_file = "consultant_"+report_type+"_message.md"
    (folder/message_file).write_text(message,encoding="utf-8")
    snapshot = " ".join(sources["snapshot"])+":00"
    item = {"level":"顾问","png":png,"message_file":message_file,"message":message,"rows":len(rows),
            "reminder_by_grade":reminders,"reminder_people":None}
    review = {"period":period,"process_snapshot":snapshot,"conversion_snapshot":snapshot if not is_process else None,
        "source_kind":"data_center","report_type":report_type,
        "source_queries":{m:{k:sources[m][k] for k in ("model","query_id","complete","sql_sha256")} for m in ("2064",) if m in sources},
        "results":{"internal_books":{"levels":{"consultant":item}}}}
    if "2460" in sources:
        review["source_queries"]["2460"] = {k:sources["2460"][k] for k in ("model","query_id","complete","sql_sha256")}
    _write(folder/"review.json",review)
    return review


def prepare(report_type, period, folder):
    cfg = config()
    folder.mkdir(parents=True,exist_ok=True)
    sources = fetch(cfg,report_type,period,folder/"source")
    return build(cfg,sources,report_type,period,folder)


def _window(slot, report_type):
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    minutes = 50 if report_type == "process" else 53
    if not slot <= now <= slot+timedelta(minutes=minutes):
        raise ValueError("Internal-books delivery missed its authorized batch window")


def _fresh_review(review, cfg):
    source_at = datetime.strptime(review["process_snapshot"], "%Y%m%d %H:%M").replace(
        tzinfo=ZoneInfo("Asia/Shanghai"))
    age = (datetime.now(ZoneInfo("Asia/Shanghai"))-source_at).total_seconds()/60
    if not 0 <= age <= cfg["source"]["freshness_max_age_minutes"]:
        raise ValueError("Internal-books source snapshot became stale before delivery")
    if review["report_type"] == "transformation" and review["conversion_snapshot"] != review["process_snapshot"]:
        raise ValueError("Internal-books delivery sources have different snapshots")


def deliver(review, folder, slot):
    cfg = config()
    report_type,period = review["report_type"],review["period"]
    _window(slot,report_type)
    receipt_path = folder/"send_receipt.json"
    prior = json.loads(receipt_path.read_text(encoding="utf-8")) if receipt_path.exists() else None
    if prior:
        if (prior["period"],prior["slot"],prior["report_type"],prior["chat_id"]) != (
                period,slot.isoformat(),report_type,cfg["target"]["chat_id"]):
            raise ValueError("Internal-books receipt identity differs from the active slot")
        verdict = resend.decide(prior.get("status"),prior.get("message_id"))
        if verdict == resend.DONE:
            return {"status":"sent_verified","message_id":prior["message_id"],"receipt":str(receipt_path)}
        if verdict == resend.REVERIFY:
            prior["readback"] = _verify_message(cfg["target"]["chat_id"],prior["message_id"],prior["image_key"],period,
                                                  set(prior["mention_ids"]),cfg["sender"]["open_id"])
            prior["status"] = "sent_verified"
            _write(receipt_path,prior)
            return {"status":"sent_verified","message_id":prior["message_id"],"receipt":str(receipt_path)}
    if prior:
        # Retry an uncertain write with exactly the stored payload and UUID.
        receipt = prior
        markdown = receipt["markdown"]
    else:
        _fresh_review(review,cfg)
        models = ("2064",) if report_type == "process" else ("2064","2460")
        live_sources(cfg,models,folder/"source_before_send")
        verify_chat(cfg["target"]["chat_id"],cfg["target"]["name"],"bot",90)
        members = _members(cfg["target"]["chat_id"],cfg["sender"]["open_id"])
        item = review["results"]["internal_books"]["levels"]["consultant"]
        people = [p for group in item["reminder_by_grade"].values() for p in group]
        resolution = {"reminders":[{"people":people}]}
        if people:
            resolved,display,fallback_reasons = resolve_contacts(people,_data,member_ids=members)
            text_only = set(fallback_reasons)
            resolution["text_fallback_reasons"] = fallback_reasons
        else:
            resolved,display,text_only = {},{},set()
        image_key = upload_image(folder/item["png"],"bot",90)
        if report_type == "process":
            markdown = _render_message(item["message"],"顾问",people,resolved,display,image_key,item["reminder_by_grade"])
        else:
            markdown = _render_conversion(item["message"],item,resolved,display,image_key)
        seed = "|".join(("qingcheng","internal_books",report_type,period,slot.isoformat(),cfg["target"]["chat_id"]))
        key = "qcib_"+report_type[:4]+"_"+hashlib.sha256(seed.encode("utf-8")).hexdigest()[:32]
        if set(re.findall(r'<at user_id="(ou_[A-Za-z0-9]+)">',markdown)) != set(resolved.values()):
            raise ValueError("Internal-books native mentions differ from the resolved set")
        receipt = {"status":"send_attempt_started","period":period,"slot":slot.isoformat(),
            "report_type":report_type,"chat_id":cfg["target"]["chat_id"],"image_key":image_key,
            "mention_ids":sorted(resolved.values()),"markdown":markdown,"idempotency_key":key,
            "text_fallback_names":sorted(text_only),"invite_attempts":resolution.get("invite_attempts",[]),
            "text_fallback_reasons":resolution.get("text_fallback_reasons",{}),
            "source_queries":review["source_queries"],"source_snapshot":review["process_snapshot"]}
    _window(slot,report_type)
    _data(["im","+messages-send","--chat-id",cfg["target"]["chat_id"],"--markdown",markdown,
           "--idempotency-key",receipt["idempotency_key"],"--as","bot","--dry-run","--format","json"])
    _write(receipt_path,receipt)
    try:
        response = _data(["im","+messages-send","--chat-id",cfg["target"]["chat_id"],"--markdown",markdown,
                          "--idempotency-key",receipt["idempotency_key"],"--as","bot","--format","json"])
        if not isinstance(response.get("message_id"),str) or not response["message_id"].startswith("om_"):
            raise ValueError("Internal-books send returned no message ID")
    except Exception as exc:
        receipt.update(status="send_result_uncertain",error=str(exc))
        _write(receipt_path,receipt)
        raise
    receipt.update(status="sent_unverified",message_id=response["message_id"])
    _write(receipt_path,receipt)
    receipt["readback"] = _verify_message(cfg["target"]["chat_id"],receipt["message_id"],receipt["image_key"],period,
                                            set(receipt["mention_ids"]),cfg["sender"]["open_id"])
    receipt["status"] = "sent_verified"
    _write(receipt_path,receipt)
    return {"status":"sent_verified","message_id":receipt["message_id"],"receipt":str(receipt_path)}
