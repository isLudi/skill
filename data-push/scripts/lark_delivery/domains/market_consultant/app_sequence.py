"""One owner and four separately receipted APP grade-9 messages."""
from __future__ import annotations

from contextlib import closing
from datetime import timedelta
import base64
import hashlib
import html
import json
from pathlib import Path
import time

from ...core import catalog
from ...core.locks import runner_lock
from .channels import app_grade_9 as policy

KEY = "market_consultant/app_grade_9"
SUPERVISOR_KEY = "market_consultant/supervisor_yafei_grade_9"
WEEKEND_ORDER = ("supervisor_result", "advisor_result", "supervisor_process", "advisor_process")
WEEKDAY_ORDER = ("supervisor_process", "advisor_process")


def validate_definition(definition):
    from . import adapter
    adapter.validate_definition(definition)
    sequence = definition.get("delivery_sequence", {})
    if (definition["channel_id"] != "app_grade_9"
            or sequence.get("stage") not in {"preview_only", "scheduled"}
            or sequence.get("supervisor_channel_ref") != SUPERVISOR_KEY
            or tuple(sequence.get("weekend_order", ())) != WEEKEND_ORDER
            or tuple(sequence.get("weekday_order", ())) != WEEKDAY_ORDER):
        raise ValueError("APP有序消息配置与已确认的顺序不一致")
    supervisor = catalog.load_channel(SUPERVISOR_KEY)
    adapter.validate_definition(supervisor)
    if (supervisor["report"]["included_grades"] != ["初三"]
            or supervisor["source"]["raw_table_id"] != definition["source"]["raw_table_id"]
            or supervisor["sender"] != definition["sender"]
            or supervisor["base_identity"] != definition["base_identity"]
            or "app" not in supervisor["channels"]):
        raise ValueError("APP主管和顾问的年级、源表或身份不一致")
    return supervisor


def delegated_channels(cfg, channels):
    """Move APP to the coordinator only after its schedule is explicitly enabled."""
    if cfg.get("channel_key") != SUPERVISOR_KEY or "app" not in channels:
        return channels
    if KEY not in catalog.registry()["channels"]:
        return channels
    definition = catalog.load_channel(KEY)
    if not definition["schedule"]["enabled"]:
        return channels
    validate_definition(definition)
    if definition["delivery_sequence"]["stage"] != "scheduled":
        raise ValueError("APP有序入口已启用但仍处于预览阶段")
    targets = catalog.select_targets(definition)
    if len(targets) != 1 or targets[0]["chat_id"] != cfg["chat_id"]:
        raise ValueError("APP有序入口与主管入口的目标群不一致")
    return [channel for channel in channels if channel != "app"]


def specs(slot):
    weekend = policy.business_date(slot).weekday() >= 4
    current = policy.business_period(slot)
    order = WEEKEND_ORDER if weekend else WEEKDAY_ORDER
    result = []
    for part in order:
        grain, section = part.split("_")
        period = policy.next_business_period(current) if weekend and section == "process" else current
        grain_label = "主管" if grain == "supervisor" else "顾问"
        period_label = "下期" if weekend and section == "process" else "本期"
        label = "APP" + grain_label + period_label + ("转化" if section == "result" else "过程")
        result.append({"part": part, "owner": SUPERVISOR_KEY if grain == "supervisor" else KEY,
                       "section": section, "period": period, "label": label})
    return result


def prepare(definition, target, slot, state_dir, *, no_mentions=False):
    from . import adapter
    supervisor = validate_definition(definition)
    definitions = {KEY: definition, SUPERVISOR_KEY: supervisor}
    messages = []
    for spec in specs(slot):
        owner = definitions[spec["owner"]]
        owner_targets = [item for item in catalog.select_targets(owner) if item["chat_id"] == target["chat_id"]]
        if len(owner_targets) != 1:
            raise ValueError("APP消息组件未登记在同一个目标群")
        context = adapter.prepare(owner, owner_targets[0], channel="app", report_type=spec["section"],
            period=spec["period"], slot=slot, allow_period_override=True,
            state_dir=Path(state_dir) / spec["part"], no_mentions=no_mentions)
        context["report_kind"] = "app_" + spec["part"]
        if not context.get("skip_delivery"):
            lines = context["markdown"].splitlines()
            lines[0] = f'## 🔥 **【{spec["period"]}】{spec["label"]}播报**'
            context["markdown"] = "\n".join(lines)
        messages.append({**spec, "context": context,
                         "validation_cfg": catalog.schedule_config(owner, owner_targets[0])})
    bundle = {"messages": messages}
    require_consistent_snapshot(bundle)
    return bundle


def require_consistent_snapshot(bundle):
    contexts = [item["context"] for item in bundle["messages"]]
    if not contexts:
        raise ValueError("APP有序消息不能为空")
    revisions = {item["raw_read_audit"].get("rev") for item in contexts}
    snapshots = {tuple(item["snapshot"]) for item in contexts}
    sources = {(item["coords"]["base_token"], item["raw_table_id"]) for item in contexts}
    if (len(revisions) != 1 or None in revisions or len(snapshots) != 1 or len(sources) != 1
            or any(item["raw_read_audit"].get("has_more") is not False for item in contexts)):
        raise ValueError("APP四条消息必须使用同一完整Base版本、源表和数仓快照")


def validate(bundle, evidence, slot):
    from . import adapter
    from .reporting import validate_context
    require_consistent_snapshot(bundle)
    expected = specs(slot)
    if [item["part"] for item in bundle["messages"]] != [item["part"] for item in expected]:
        raise ValueError("APP消息顺序不符合业务日历")
    for message, spec in zip(bundle["messages"], expected):
        context, cfg = message["context"], message["validation_cfg"]
        if (context["period"] != spec["period"] or context["report_type"] != spec["section"]
                or cfg["channel_key"] != spec["owner"]):
            raise ValueError("APP消息的期次、类型或所有者不一致")
        definition = catalog.load_channel(spec["owner"])
        adapter.policy_for(definition).enforce_component_calendar(context["period"], context["report_type"], slot)
        if context["grade_report"]["min_post_leads"] != definition["report"]["minimum_post_leads"]:
            raise ValueError("APP消息入图门槛与已登记配置不一致")
        validate_context(context, evidence, cfg, slot, enforce_calendar=False)


def deliver_in_order(bundle, deliver_one):
    """A failed/uncertain predecessor always blocks the later messages."""
    for message in bundle["messages"]:
        if not deliver_one(message):
            return False
    return True


def require_receipt_snapshot(bundle, db, key_for):
    """A retry cannot mix a new Base revision with already attempted messages."""
    for message in bundle["messages"]:
        prior = db.execute("SELECT detail FROM deliveries WHERE key=?", (key_for(message),)).fetchone()
        if not prior:
            continue
        detail = json.loads(prior[0])
        context = message["context"]
        if detail.get("rev") != context["raw_read_audit"]["rev"] or detail.get("period") != context["period"]:
            raise ValueError("APP已尝试消息的Base版本或期次已变化，停止后续投递")


def write_preview(bundle, directory):
    """A portable, read-only preview of the actual four-message plan."""
    require_consistent_snapshot(bundle)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    cards, messages, markdown = [], [], []
    for number, message in enumerate(bundle["messages"], 1):
        context = message["context"]
        path = context.get("result_image_path" if message["section"] == "result" else "image_path")
        image = (f'<img alt="{html.escape(message["label"])}" src="data:image/png;base64,'
                 + base64.b64encode(Path(path).read_bytes()).decode("ascii") + '">') if path else "<p>没有达到展示门槛的数据，本条跳过。</p>"
        reminders = "".join('<li>' + html.escape(line[2:]) + '</li>'
                            for line in context["markdown"].splitlines() if line.startswith("- "))
        cards.append(f'<article><h2>{number}. {message["label"]} · {context["period"]}</h2>'
                     f'<p>管家 · 一条独立群消息</p>{image}<ul>{reminders}</ul></article>')
        local_markdown = context["markdown"]
        if path:
            local_markdown = local_markdown.replace(f'](img_{message["section"]}_preview)',
                                                    f']({Path(path).as_posix()})')
        markdown.append(f'{number}. {message["label"]}\n\n{local_markdown}')
        messages.append({"number": number, "label": message["label"], "owner": message["owner"],
            "period": context["period"], "report_type": context["report_type"],
            "report_kind": context["report_kind"], "revision": context["raw_read_audit"]["rev"],
            "snapshot": list(context["snapshot"]), "minimum_post_leads": context["grade_report"]["min_post_leads"],
            "skip_delivery": context.get("skip_delivery", False), "image_file": str(path) if path else None,
            "image_sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest() if path else None,
            "reminder_names": context["grade_report"]["reminder_names"], "message_sent": False})
    html_path = directory / "app-message-order-preview.html"
    html_path.write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width"><title>APP群消息顺序预览</title>'
        '<style>body{font:16px Microsoft YaHei,sans-serif;background:#f4f6fa;color:#203b72;'
        'max-width:1600px;margin:28px auto;padding:0 20px}article{background:white;border:1px solid #cbd5e1;'
        'border-radius:12px;margin:24px 0;padding:20px}img{display:block;max-width:100%;height:auto}li{margin:12px 0}</style>'
        '<h1>APP群消息顺序 · 本地预览</h1><p>按下列顺序逐条发送，前条未完成时等待；未发送群消息。</p>'
        + "".join(cards) + '</html>', encoding="utf-8")
    markdown_path = directory / "app-message-order-preview.md"
    markdown_path.write_text("\n\n---\n\n".join(markdown), encoding="utf-8")
    metadata_path = directory / "app-message-order-manifest.json"
    metadata_path.write_text(json.dumps({"channel_key": KEY, "messages": messages,
        "message_sent": False}, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"html_file": str(html_path), "markdown_file": str(markdown_path),
            "metadata_file": str(metadata_path), "image_files": [item["image_file"] for item in messages if item["image_file"]],
            "message_sent": False}


def run_slot(cfg, preflight, slot, state, db):
    from . import scheduler as schedule
    definition = catalog.load_channel(KEY)
    validate_definition(definition)
    if not preflight and definition["delivery_sequence"]["stage"] != "scheduled":
        raise ValueError("APP有序消息尚未启用")
    target = catalog.select_targets(definition, [cfg["target_id"]])[0]
    deadline = slot + timedelta(minutes=cfg["deadline_minute"] + 1)
    while schedule.now() < deadline:
        try:
            schedule.verify_bot(cfg)
            evidence = schedule.upstream_ready(cfg, slot)
            bundle = prepare(definition, target, slot, state / "ordered")
            validate(bundle, evidence, slot)
            key_for = lambda message: schedule.delivery_key(cfg, slot, "app", message["context"]["report_kind"])
            require_receipt_snapshot(bundle, db, key_for)
            if preflight:
                summary = {"status": "preflight_passed_no_send", "message_sent": False,
                           "order": [item["label"] for item in bundle["messages"]]}
                (state / "preflight.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
                schedule.emit(summary["status"], order=summary["order"])
                return 0
            while schedule.now() < slot + timedelta(minutes=cfg["send_minute"]):
                time.sleep(min(20, max(0.01, (slot + timedelta(minutes=cfg["send_minute"]) - schedule.now()).total_seconds())))
            def deliver_one(message):
                validate(bundle, evidence, slot)
                return schedule.deliver(message["context"], cfg, slot, db, evidence)
            if deliver_in_order(bundle, deliver_one):
                schedule.emit("app_sequence_finished", order=[item["label"] for item in bundle["messages"]])
                return 0
        except (Exception, SystemExit) as exc:
            schedule.emit("app_sequence_not_ready", reason=str(exc)[:220], slot=slot.isoformat())
            if preflight:
                return 1
        wake = schedule.next_check(schedule.now(), slot, cfg)
        if wake >= deadline:
            break
        schedule.emit("app_sequence_waiting_to_retry", next_retry_at=wake.isoformat())
        while schedule.now() < wake:
            time.sleep(min(20, max(0.01, (wake - schedule.now()).total_seconds())))
    schedule.emit("app_sequence_deadline_skipped", slot=slot.isoformat())
    return 1


def send_now(definition, target, request_id, *, preflight=False, requested_slot=None, allow_expired=False):
    from . import immediate, scheduler as schedule
    validate_definition(definition)
    cfg = catalog.schedule_config(definition, target)
    schedule.validate_config(cfg)
    state = Path(cfg["state_dir"])
    with runner_lock(state) as acquired:
        if not acquired:
            raise ValueError("Another broadcast instance owns this APP sequence")
        with closing(schedule.connect_ledger(state)) as db:
            started = schedule.now()
            slot = requested_slot or immediate.latest_upstream_slot(started)
            if requested_slot is not None and (slot.tzinfo is None or slot.minute or slot.hour not in cfg["hours"] or not allow_expired):
                raise ValueError("APP补发需要带时区的已登记整点槽位和明确的补发授权")
            # Validate the request ID before any external work.
            immediate.request_key(cfg, request_id)
            schedule.verify_bot(cfg)
            publication = immediate.verify_publication(cfg)
            evidence = schedule.upstream_ready(cfg, slot)
            evidence.update(mode="app_sequence_immediate", request_id=request_id, publication=publication)
            bundle = prepare(definition, target, slot, state / "ordered-now")
            validate(bundle, evidence, slot)
            key_for = lambda message: immediate.request_key(cfg, request_id, message["context"]["report_kind"])
            require_receipt_snapshot(bundle, db, key_for)
            logical = {"period": policy.business_period(slot), "report_type": policy.scheduled_report_type(slot)}
            def time_guard():
                immediate.require_fresh_request(started, slot, evidence, logical, schedule.now(),
                    allow_expired=allow_expired, cfg=cfg)
                directory = schedule.operator("list-execution-history", cfg, "--limit", "12")
                latest = schedule.validate_history(schedule.read_json(directory / "history.json"), cfg, slot)
                if latest["id"] != evidence["execution_id"]:
                    raise ValueError("Upstream execution changed during APP one-time preparation")
            time_guard()
            if preflight:
                schedule.emit("app_sequence_immediate_preflight_passed_no_send", order=[item["label"] for item in bundle["messages"]])
                return 0
            def deliver_one(message):
                validate(bundle, evidence, slot)
                return schedule._deliver_verified(message["context"], cfg, slot, db, evidence,
                    key=key_for(message), time_guard=time_guard)
            return 0 if deliver_in_order(bundle, deliver_one) else 1
