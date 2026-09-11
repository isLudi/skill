"""Explicit market-consultant adapter; Qingcheng cannot select it."""
from argparse import Namespace
from pathlib import Path

from ...core import catalog
from .channels import (
    business_koc_math, self_incubated_koc_5, supervisor_koc_douyin_sync,
    supervisor_private_app_sync, supervisor_self_incubated_koc_5_grade_9,
)

POLICIES = {
    "self_incubated_koc_5": self_incubated_koc_5,
    "business_koc_math": business_koc_math,
    "supervisor_koc_douyin_sync": supervisor_koc_douyin_sync,
    "supervisor_private_app_sync": supervisor_private_app_sync,
    "supervisor_self_incubated_koc_5_grade_9": supervisor_self_incubated_koc_5_grade_9,
}


def policy_for(definition):
    try:
        return POLICIES[definition["channel_id"]]
    except KeyError as exc:
        raise ValueError("No reviewed market channel policy for " + definition["channel_id"]) from exc


def validate_definition(definition):
    if definition["domain"] != "market_consultant" or definition["adapter"] != "market-grade-manager-v1":
        raise ValueError("The market adapter cannot interpret another department's data")
    if definition["source"]["report_profile"] not in {"grade-compact", "supervisor-detail"}:
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
    channels = tuple(definition.get("channels", [definition["channel"]]))
    if channels != policy.CHANNELS:
        raise ValueError("Configured channels differ from the reviewed channel policy")
    match = definition["source"].get("channel_match")
    if not isinstance(match, dict) or match.get("field") != "渠道" or match.get("case_sensitive") is not True:
        raise ValueError("渠道配置必须声明渠道字段的大小写敏感匹配契约")
    values = match.get("values")
    if not isinstance(values, dict) or tuple(values) != channels or any(values.get(name) != name for name in channels):
        raise ValueError("渠道匹配契约必须为每个登记渠道声明相同的规范值")
    if hasattr(policy, "INCLUDED_GRADES"):
        if tuple(report.get("included_grades", ())) != policy.INCLUDED_GRADES:
            raise ValueError("Configured grades differ from the reviewed channel policy")
    for target in definition["targets"]:
        if definition["channel_id"] in {
                "business_koc_math", "supervisor_koc_douyin_sync", "supervisor_private_app_sync",
                "supervisor_self_incubated_koc_5_grade_9"
        } and target["chat_id"] != policy.CHAT_ID:
            raise ValueError("Configured target differs from the reviewed channel policy")
        policy.enforce_group_scope(target["chat_id"], channels[0], definition["source"]["report_profile"])


def report_arguments(definition, target, *, channel=None, report_type="auto", state_dir=None, slot=None):
    validate_definition(definition)
    policy = policy_for(definition)
    source = definition["source"]
    channel = channel or definition["channel"]
    if channel not in definition.get("channels", [definition["channel"]]):
        raise ValueError("Channel is outside the registered report scope")
    cfg = catalog.schedule_config(definition, target)
    state = Path(state_dir) if state_dir else Path(cfg["state_dir"])
    return Namespace(channel=channel, chat_id=target["chat_id"], chat_name=target["display_name"],
        report_type=policy.scheduled_report_type(slot) if report_type == "auto" else report_type,
        period=policy.business_period(slot), identity=definition["sender"]["identity"], base_as=definition["base_identity"],
        raw_source_url=source["raw_source_url"], raw_table_id=source["raw_table_id"],
        base_token="", table_id="", view_id="", source_url=source["raw_source_url"],
        report_profile=source["report_profile"], source_mode="lead-detail",
        mention_target="supervisor" if source["report_profile"] == "supervisor-detail" else "manager",
        verification_identity=definition.get("verification_identity", definition["sender"]["identity"]),
        no_mentions=False,
        strict_mentions=True, allow_unresolved_mentions=False, with_image=True,
        output_image="", output_result_image="", ledger="", state_dir=str(state), timeout=60, max_pages=100)


def prepare(definition, target, *, channel=None, report_type="auto", state_dir=None):
    from .workflow import prepare_report
    args = report_arguments(definition, target, channel=channel, report_type=report_type, state_dir=state_dir)
    return prepare_report(args, definition)


def write_preview(context):
    if context.get("skip_delivery"):
        return {"status": "skipped_no_eligible_rows", "reason": context["skip_reason"],
                "image_files": [], "message_sent": False}
    if context["report_profile"] == "supervisor-detail":
        from .supervisor_report import write_preview as write
    else:
        from .grade_report import write_preview as write
    path = context.get("image_path") or context.get("result_image_path")
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
