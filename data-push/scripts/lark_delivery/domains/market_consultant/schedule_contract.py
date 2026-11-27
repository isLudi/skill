"""Validate the registered local market push schedule and producer binding."""
import re

from ...core import catalog
from .adapter import SUPERVISOR_PROFILES
from .channels import self_incubated_koc_5 as bp
from . import volume_report as vr


def validate_config(cfg):
    catalog.require_registered_schedule(cfg)
    slot_reports = cfg.get("slot_reports")
    routed = slot_reports is not None
    if cfg.get("timezone") != "Asia/Shanghai":
        raise ValueError("Unreviewed schedule timezone")
    if routed:
        if cfg.get("hours") != [13, 17] or slot_reports != {"13": "regular", "17": "volume"}:
            raise ValueError("Unreviewed two-slot report routing")
    elif cfg.get("hours") not in ([13, 17], [13, 17, 21]):
        raise ValueError("Unreviewed legacy schedule")
    order = cfg.get("stagger_order")
    start_minute = cfg.get("prepare_minute")
    if (type(order) is not int or order < 1 or start_minute != 20 + (order - 1) // 2
            or start_minute > 50
            or cfg.get("send_minute") != start_minute
            or cfg.get("deadline_minute") != 50 or cfg.get("retry_minutes") != 2
            or not re.fullmatch(r"Codex-Lark-[A-Za-z0-9-]+Push", cfg.get("windows_task_name", ""))):
        raise ValueError("Unreviewed retry window")
    if cfg.get("report_profile") not in {bp.PROFILE, *SUPERVISOR_PROFILES}:
        raise ValueError("Unreviewed delivery profile")
    if not cfg.get("channel_key") and (cfg.get("channels") != [bp.CHANNEL] or cfg.get("chat_id") != bp.CHAT_ID):
        raise ValueError("Unreviewed delivery scope")
    if (cfg.get("period_rule") != "natural_week_friday" or cfg.get("process_weekdays") != list(range(7))
            or cfg.get("result_weekdays") != [4, 5, 6]):
        raise ValueError("Unreviewed business-week period or weekday policy")
    volume = cfg.get("volume_report", {})
    if volume:
        if (volume.get("stage") not in {"preview_only", "scheduled"}
                or volume.get("period_rule") != "latest_available" or volume.get("grain") != "年级"
                or volume.get("channel_rule") not in vr.CHANNEL_RULE_DESCRIPTIONS):
            raise ValueError("Unreviewed volume-report policy")
        if volume.get("stage") == "scheduled":
            producer = volume.get("upstream", {})
            if (producer.get("task_name") != "market2lark_jinliang"
                    or producer.get("log_protocol") != "volume_two_period_create_then_delete_v1"
                    or not re.fullmatch(r"[0-9a-f]{64}", str(producer.get("verified_source_sha256", "")))):
                raise ValueError("Scheduled volume producer is not release-bound")
    if routed and volume.get("stage") != "scheduled":
        raise ValueError("Routed volume report must be scheduled")
    return cfg
