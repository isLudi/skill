"""Shared validation and readback helpers for market-consultant delivery."""
from __future__ import annotations

import json

from ...common import feishu as gp
from ...core import catalog
from . import grade_report as gr
from .adapter import SUPERVISOR_PROFILES, policy_for, report_module_for
from .channels import self_incubated_koc_5 as bp
from .weekend_dual import REPORT_TYPE as WEEKEND_DUAL_REPORT_TYPE


def validate_weekend_dual_context(context, evidence, cfg, slot, validate_child):
    if cfg is None or not cfg.get("channel_key"):
        raise ValueError("周末双期播报缺少已登记渠道配置")
    definition = catalog.load_channel(cfg["channel_key"])
    policy = policy_for(definition)
    sections = context.get("dual_sections") or {}
    if set(sections) != {"result", "process"}:
        raise ValueError("周末双期播报必须同时包含转化和过程组件")
    if (context.get("period") != policy.business_period(slot)
            or context.get("next_process_period") != policy.next_business_period(context["period"])
            or context.get("report_type") != WEEKEND_DUAL_REPORT_TYPE):
        raise ValueError("周末双期播报的期次路由不符合当前自然周")
    for section in ("result", "process"):
        child = sections[section]
        validate_child(child, evidence, cfg, slot, enforce_calendar=False)
        expected_minimum = definition["report"]["minimum_post_leads"]
        if section == "process":
            expected_minimum = definition["report"].get(
                "weekend_next_process_minimum_post_leads", expected_minimum)
        if child["grade_report"].get("min_post_leads") != expected_minimum:
            raise ValueError("周末双期播报的主管入图门槛与登记配置不一致")
        if child.get("chat_id") != cfg["chat_id"] or child.get("identity") != "bot":
            raise ValueError("周末双期播报的群或发送身份不一致")
        if not hasattr(policy, "enforce_component_calendar"):
            raise ValueError("当前渠道未登记周末双期组件日历规则")
        policy.enforce_component_calendar(child["period"], child["report_type"], slot)
    revisions = {sections[section]["raw_read_audit"].get("rev") for section in sections}
    if len(revisions) != 1 or context["raw_read_audit"].get("rev") not in revisions:
        raise ValueError("周末双期播报的两个期次不来自同一Base版本")
    expected_mentions = set()
    for child in sections.values():
        expected_mentions.update(child.get("mention_info", {}).get("resolved", {}).values())
    if set(context.get("mention_info", {}).get("resolved", {}).values()) != expected_mentions:
        raise ValueError("周末双期播报的提醒账号集合不一致")
    if gr.mention_ids(context["markdown"]) != expected_mentions:
        raise ValueError("周末双期播报正文缺少或多出提醒账号")
    if context.get("skip_delivery") != all(child.get("skip_delivery") for child in sections.values()):
        raise ValueError("周末双期播报的空数据跳过状态不一致")


def receipt_readback(message_id, cfg, context, image_keys):
    data = gp._unwrap(json.loads(gp.run_lark(["im", "+messages-mget", "--message-ids", message_id,
                                            "--no-reactions", "--as", "bot", "--format", "json"], timeout=60)))
    matches = [x for x in data.get("messages", []) if x.get("message_id") == message_id]
    if len(matches) != 1:
        raise ValueError("message readback missing")
    msg = matches[0]
    content = msg.get("content", "")
    text = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
    expected_periods = [context["period"]]
    if context.get("report_type") == WEEKEND_DUAL_REPORT_TYPE:
        expected_periods = [child["period"] for child in context["dual_sections"].values()
                            if not child.get("skip_delivery")]
    if any(key not in text for key in image_keys.values()) or any(period not in text for period in expected_periods):
        raise ValueError("message readback images or period mismatch")
    expected_mentions = (set(context.get("mention_info", {}).get("resolved", {}).values())
                         if context.get("report_profile") in {bp.PROFILE, *SUPERVISOR_PROFILES} else set())
    actual_mentions = gr.mention_ids(content) | gr.mention_ids({"mentions": msg.get("mentions", [])})
    if actual_mentions != expected_mentions:
        raise ValueError("delivered mention accounts differ from the verified reminder set")
    if msg.get("chat_id") and msg["chat_id"] != cfg["chat_id"]:
        raise ValueError("message readback target mismatch")
    sender = msg.get("sender", {})
    sender_id = sender.get("open_bot_id") or sender.get("open_id") or sender.get("id")
    if str(sender_id).startswith("ou_") and sender_id != cfg["bot_open_id"]:
        raise ValueError("message readback sender ID mismatch")
    if not str(sender_id).startswith("ou_") and sender.get("name") and sender["name"] != cfg["bot_name"]:
        raise ValueError("message readback sender mismatch")
    return {"message_id": message_id, "verified": True, "sender": sender,
            "image_count": len(image_keys), "contains_mentions": bool(actual_mentions),
            "mention_ids": sorted(actual_mentions)}
