"""Explicit market-consultant adapter; Qingcheng cannot select it."""
from argparse import Namespace
from pathlib import Path

from ...core import catalog
from .channels import (
    business_koc_math, self_incubated_koc_5, supervisor_koc_douyin_sync,
    supervisor_private_app_sync, supervisor_self_incubated_koc_5_grade_9,
    supervisor_yafei_grade_9, supervisor_yafei_grade_9_advisor,
    supervisor_zhu_doctor_video49,
    supervisor_chenruichun,
)
from .weekend_dual import REPORT_TYPE as WEEKEND_DUAL_REPORT_TYPE, write_preview as write_weekend_dual_preview

SUPERVISOR_PROFILES = frozenset({"supervisor-detail", "supervisor-video49", "supervisor-advisor-detail"})

POLICIES = {
    "self_incubated_koc_5": self_incubated_koc_5,
    "business_koc_math": business_koc_math,
    "supervisor_koc_douyin_sync": supervisor_koc_douyin_sync,
    "supervisor_private_app_sync": supervisor_private_app_sync,
    "supervisor_self_incubated_koc_5_grade_9": supervisor_self_incubated_koc_5_grade_9,
    "supervisor_yafei_grade_9": supervisor_yafei_grade_9,
    "supervisor_yafei_grade_9_advisor": supervisor_yafei_grade_9_advisor,
    "supervisor_zhu_doctor_video49": supervisor_zhu_doctor_video49,
    "supervisor_chenruichun": supervisor_chenruichun,
}

ADVISOR_GRAIN_CHANNELS = frozenset({
    "supervisor_zhu_doctor_video49",
    "supervisor_chenruichun",
    "supervisor_yafei_grade_9_advisor",
})

ADVISOR_REPORT_CHANNELS = {
    "supervisor_zhu_doctor_video49": "supervisor_video49_report",
    "supervisor_chenruichun": "supervisor_video49_report",
    "supervisor_yafei_grade_9_advisor": "supervisor_yafei_advisor_report",
}


def policy_for(definition):
    try:
        return POLICIES[definition["channel_id"]]
    except KeyError as exc:
        raise ValueError("No reviewed market channel policy for " + definition["channel_id"]) from exc


def report_module_for(definition):
    """Return the report implementation explicitly owned by this channel."""
    if definition["channel_id"] in ADVISOR_REPORT_CHANNELS:
        from . import supervisor_video49_report, supervisor_yafei_advisor_report
        modules = {
            "supervisor_video49_report": supervisor_video49_report,
            "supervisor_yafei_advisor_report": supervisor_yafei_advisor_report,
        }
        return modules[ADVISOR_REPORT_CHANNELS[definition["channel_id"]]]
    if definition["source"]["report_profile"] == "supervisor-detail":
        from . import supervisor_report
        return supervisor_report
    from . import grade_report
    return grade_report


def validate_definition(definition):
    if definition["domain"] != "market_consultant" or definition["adapter"] != "market-grade-manager-v1":
        raise ValueError("The market adapter cannot interpret another department's data")
    if definition["source"]["report_profile"] not in {"grade-compact", *SUPERVISOR_PROFILES}:
        raise ValueError("This adapter only supports reviewed market report profiles")
    report = definition["report"]
    if (report["period_rule"] != "natural_week_friday" or report["process_weekdays"] != list(range(7))
            or report["result_weekdays"] != [4, 5, 6]):
        raise ValueError("Unsupported market business-week policy")
    if type(report["minimum_post_leads"]) is not int or report["minimum_post_leads"] < 0:
        raise ValueError("Invalid post-lead threshold")
    if definition["sender"]["identity"] != "bot":
        raise ValueError("This report requires the pinned bot identity")
    if definition.get("verification_identity", definition["sender"]["identity"]) not in {"user", "bot"}:
        raise ValueError("Unsupported read-only target verification identity")
    policy = policy_for(definition)
    if definition["channel_id"] == "supervisor_self_incubated_koc_5_grade_9":
        if (report["minimum_post_leads"] != 10
                or report.get("weekend_next_process_enabled") is not True
                or report.get("weekend_next_process_minimum_post_leads")
                != policy.WEEKEND_NEXT_PROCESS_MIN_POST_LEADS):
            raise ValueError("KOC初中周末下一期过程数据的主管门槛与已审阅规则不一致")
    report_module = report_module_for(definition)
    expected_mention_target = getattr(report_module, "MENTION_TARGET",
                                      "supervisor" if definition["source"]["report_profile"] in SUPERVISOR_PROFILES else "manager")
    if definition["source"].get("mention_target") != expected_mention_target:
        raise ValueError("Configured mention target differs from the reviewed report module")
    if type(report.get("weekend_next_process_enabled", False)) is not bool:
        raise ValueError("weekend_next_process_enabled must be an explicit boolean")
    channels = tuple(definition.get("channels", [definition["channel"]]))
    if channels != policy.CHANNELS:
        raise ValueError("Configured channels differ from the reviewed channel policy")
    match = definition["source"].get("channel_match")
    if not isinstance(match, dict) or match.get("field") != "渠道" or match.get("case_sensitive") is not True:
        raise ValueError("渠道配置必须声明渠道字段的大小写敏感匹配契约")
    match_mode = match.get("match_mode", "exact")
    if match_mode == "exact":
        values = match.get("values")
        if not isinstance(values, dict) or tuple(values) != channels or any(values.get(name) != name for name in channels):
            raise ValueError("渠道匹配契约必须为每个登记渠道声明相同的规范值")
        folded = match.get("casefold_channels", [])
        if (not isinstance(folded, list) or
                (folded and (definition["channel_id"] != "supervisor_private_app_sync" or folded != ["app"]))):
            raise ValueError("只允许集团私域与APP渠道的app使用大小写不敏感精确匹配")
    elif match_mode == "contains":
        if not isinstance(match.get("keyword"), str) or not match["keyword"].strip():
            raise ValueError("包含式渠道匹配必须声明非空 keyword")
    else:
        raise ValueError("未审阅的渠道匹配模式：" + str(match_mode))
    if hasattr(policy, "INCLUDED_GRADES"):
        if tuple(report.get("included_grades", ())) != policy.INCLUDED_GRADES:
            raise ValueError("Configured grades differ from the reviewed channel policy")
    if definition["channel_id"] == "supervisor_chenruichun":
        if report["minimum_post_leads"] != policy.MIN_POST_LEADS:
            raise ValueError("陈瑞春顾问退后线索门槛与已审阅规则不一致")
    for target in definition["targets"]:
        if definition["channel_id"] in {
                "business_koc_math", "supervisor_koc_douyin_sync", "supervisor_private_app_sync",
                "supervisor_self_incubated_koc_5_grade_9", "supervisor_yafei_grade_9",
                "supervisor_yafei_grade_9_advisor",
                "supervisor_zhu_doctor_video49", "supervisor_chenruichun"
        } and target["chat_id"] != policy.CHAT_ID:
            raise ValueError("Configured target differs from the reviewed channel policy")
        policy.enforce_group_scope(target["chat_id"], channels[0], definition["source"]["report_profile"])


def report_arguments(definition, target, *, channel=None, report_type="auto", state_dir=None,
                     slot=None, period=None, allow_period_override=False,
                     no_mentions=False, strict_mentions=True):
    validate_definition(definition)
    policy = policy_for(definition)
    source = definition["source"]
    report_module = report_module_for(definition)
    channel = channel or definition["channel"]
    if channel not in definition.get("channels", [definition["channel"]]):
        raise ValueError("Channel is outside the registered report scope")
    cfg = catalog.schedule_config(definition, target)
    state = Path(state_dir) if state_dir else Path(cfg["state_dir"])
    effective_period = period or policy.business_period(slot)
    scheduled_type = policy.scheduled_report_type(slot)
    if (scheduled_type == WEEKEND_DUAL_REPORT_TYPE
            and not definition["report"].get("weekend_next_process_enabled", False)):
        scheduled_type = "result"
    return Namespace(channel=channel, chat_id=target["chat_id"], chat_name=target["display_name"],
        report_type=scheduled_type if report_type == "auto" else report_type,
        period=effective_period, slot=slot, allow_period_override=allow_period_override,
        identity=definition["sender"]["identity"], base_as=definition["base_identity"],
        raw_source_url=source["raw_source_url"], raw_table_id=source["raw_table_id"],
        base_token="", table_id="", view_id="", source_url=source["raw_source_url"],
        report_profile=source["report_profile"], source_mode="lead-detail",
        mention_target=getattr(report_module, "MENTION_TARGET",
                               "supervisor" if source["report_profile"] in SUPERVISOR_PROFILES else "manager"),
        verification_identity=definition.get("verification_identity", definition["sender"]["identity"]),
        strict_mentions=strict_mentions, allow_unresolved_mentions=False, with_image=True,
        no_mentions=no_mentions,
        output_image="", output_result_image="", ledger="", state_dir=str(state), timeout=60, max_pages=100)


def prepare(definition, target, *, channel=None, report_type="auto", state_dir=None,
            period=None, slot=None, allow_period_override=False, no_mentions=False,
            strict_mentions=True):
    from .workflow import prepare_report, prepare_weekend_dual_report
    args = report_arguments(definition, target, channel=channel, report_type=report_type,
                            state_dir=state_dir, period=period, slot=slot,
                            allow_period_override=allow_period_override,
                            no_mentions=no_mentions, strict_mentions=strict_mentions)
    if args.report_type == WEEKEND_DUAL_REPORT_TYPE:
        return prepare_weekend_dual_report(args, definition)
    return prepare_report(args, definition)


def write_preview(context):
    if context.get("skip_delivery"):
        return {"status": "skipped_no_eligible_rows", "reason": context["skip_reason"],
                "image_files": [], "message_sent": False}
    path = context.get("image_path") or context.get("result_image_path")
    if context.get("report_type") == WEEKEND_DUAL_REPORT_TYPE:
        return write_weekend_dual_preview(context, Path(path).parent)
    if context["report_profile"] == "supervisor-video49":
        from . import supervisor_video49_report as report_module
    elif context["report_profile"] == "supervisor-advisor-detail":
        from . import supervisor_yafei_advisor_report as report_module
    elif context["report_profile"] == "supervisor-detail":
        from . import supervisor_report as report_module
    else:
        from . import grade_report as report_module
    write = report_module.write_preview
    return write(context, Path(path).parent)


def schedule(definition, target, *, preflight=False):
    from . import scheduler
    validate_definition(definition)
    cfg = catalog.schedule_config(definition, target)
    scheduler.validate_config(cfg)
    # Each target owns a state directory and OS lock; one slow target cannot block others.
    return scheduler.run_locked(cfg, preflight=preflight)


def send_now(definition, target, request_id, *, preflight=False):
    from . import immediate
    validate_definition(definition)
    return immediate.run(definition, target, request_id, preflight=preflight)


def send_volume_now(definition, target, request_id, *, preflight=False):
    from . import immediate
    validate_definition(definition)
    return immediate.run(definition, target, request_id, preflight=preflight, volume=True)


def send_backfill(definition, target, request_id, slot, *, preflight=False):
    """Explicitly deliver one already-expired scheduled slot.

    This path is separate from ``send_now`` so a late catch-up can never be
    inferred from a normal immediate request or a recurring task retry.
    """
    from . import immediate
    validate_definition(definition)
    return immediate.run(definition, target, request_id, preflight=preflight,
                         requested_slot=slot, allow_expired=True)
