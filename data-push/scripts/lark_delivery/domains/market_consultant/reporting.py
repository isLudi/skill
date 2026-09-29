"""Report argument assembly and the fail-closed snapshot/context gates.

Split out of ``scheduler`` along the report-validation boundary to keep that
module inside the layout size limit. Everything here is re-exported from
``scheduler``, so the existing ``patch.object(scheduler, ...)`` seams keep
working.
"""
from __future__ import annotations

import json
import tempfile

from ...common import feishu as gp
from ...core import catalog
from . import grade_report as gr
from . import volume_report as vr
from .adapter import SUPERVISOR_PROFILES, policy_for, report_arguments, report_module_for
from .channels import self_incubated_koc_5 as bp
from .delivery_validation import validate_weekend_dual_context
from .weekend_dual import REPORT_TYPE as WEEKEND_DUAL_REPORT_TYPE
from .workflow import source_channel_count


def _clock():
    """Resolve the scheduler's clock late.

    ``scheduler.now`` is patched throughout the test suite; binding it at import
    time would freeze the patch out. Only the slot-less fallback needs this.
    """
    from . import scheduler
    return scheduler.now()


def report_args(cfg, channel, slot=None):
    definition = catalog.load_channel(cfg.get("channel_key", catalog.DEFAULT_CHANNEL))
    targets = [target for target in catalog.select_targets(definition) if target["chat_id"] == cfg["chat_id"]]
    if len(targets) != 1 or channel not in definition.get("channels", [definition["channel"]]):
        raise ValueError("Channel/target is not registered")
    return report_arguments(definition, targets[0], channel=channel, state_dir=cfg["state_dir"], slot=slot or _clock())


def validate_context(context, evidence, cfg=None, slot=None, *, enforce_calendar=True):
    if context.get("report_type") == WEEKEND_DUAL_REPORT_TYPE:
        return validate_weekend_dual_context(context, evidence, cfg, slot, validate_context)
    policy = bp
    if cfg is not None and cfg.get("channel_key"):
        policy = policy_for(catalog.load_channel(cfg["channel_key"]))
    source_period = (evidence.get("periods") or {}).get(context["period"])
    counts = source_period["channel_counts"] if source_period else evidence["channel_counts"]
    match = (cfg or {}).get("channel_match", {})
    expected_count = source_channel_count(counts, match, context["channel"])
    period_matches = source_period is not None if evidence.get("periods") is not None else context["period"] == evidence["period"]
    if (not period_matches or context["raw_count"] != expected_count
            or str(context["snapshot"][0]) != evidence["dt"] or int(context["snapshot"][1]) != evidence["hour"]):
        raise ValueError("Base channel/period/partition/count disagrees with complete upstream write")
    if context["raw_read_audit"].get("has_more") is not False or context["raw_read_audit"].get("rev") is None:
        raise ValueError("incomplete Base snapshot")
    if context.get("report_profile") in {bp.PROFILE, *SUPERVISOR_PROFILES}:
        policy.enforce_group_scope(context["chat_id"], context["channel"], context["report_profile"])
        if cfg is not None:
            if context["chat_id"] != cfg["chat_id"] or context["identity"] != "bot":
                raise ValueError("configured group or sender mismatch")
            if enforce_calendar:
                policy.enforce_live_calendar(context["period"], context["report_type"], slot or _clock())
            if enforce_calendar and context["report_type"] != policy.scheduled_report_type(slot or _clock()):
                raise ValueError("scheduled report type does not match the weekday policy")
        if context.get("skip_delivery"):
            report = context.get("supervisor_report")
            if (context.get("report_profile") not in SUPERVISOR_PROFILES
                    or context.get("skip_reason") not in {
                        "no_supervisor_rows_meet_minimum_post_leads",
                        "no_advisor_rows_meet_minimum_post_leads",
                    }
                    or not report or report["blocks"] or context.get("markdown")
                    or context.get("image_path") or context.get("result_image_path")
                    or report["reminder_names"]):
                raise ValueError("invalid no-data skip context")
            return
        info = context["mention_info"]
        definition = catalog.load_channel(cfg["channel_key"]) if cfg is not None else None
        report_module = report_module_for(definition) if definition is not None else None
        expected_target = getattr(report_module, "MENTION_TARGET",
                                   "supervisor" if context["report_profile"] in SUPERVISOR_PROFILES else "manager")
        if context["mention_target"] != expected_target or any(info.get(k) for k in ("unresolved", "ambiguous", "lookup_error", "nonmembers")):
            raise ValueError("all lowest reminder accounts must be resolved and in the group")
        if set(info["resolved"]) != set(context["grade_report"]["reminder_names"]):
            raise ValueError("reminder account set mismatch")
        if gr.mention_ids(context["markdown"]) != set(info["resolved"].values()):
            raise ValueError("unexpected or missing manager mentions")
        report_sections = gr.sections(context["report_type"])
        if context["report_profile"] in SUPERVISOR_PROFILES:
            definition = catalog.load_channel(cfg["channel_key"])
            report_sections = report_module_for(definition).sections(context["report_type"])
        for section in report_sections:
            if not context.get("image_path" if section == "process" else "result_image_path"):
                raise ValueError("selected report image missing")
    else:
        if cfg is not None and cfg.get("report_profile") == bp.PROFILE:
            raise ValueError("legacy report cannot be sent through the current group profile")
        if context["mention_target"] != "none" or gr.mention_ids(context["markdown"]):
            raise ValueError("mentions are forbidden in the legacy names-only profile")
        if not context.get("image_path") or not context.get("result_image_path"):
            raise ValueError("both report images are required")


def assert_current_revision(context, cfg):
    # The one-row read is only a revision guard, never the source for aggregation.
    if context.get("report_kind") == "volume":
        vr.assert_current_revisions(context, cfg)
        return
    with tempfile.TemporaryDirectory(prefix=".broadcast-rev-") as folder:
        data = gp._unwrap(json.loads(gp.run_lark([
            "base", "+record-list", "--base-token", context["coords"]["base_token"],
            "--table-id", context["raw_table_id"], "--field-id", "lead_id", "--limit", "1",
            "--output", "./revision.ndjson", "--format", "ndjson", "--as", cfg["base_as"]], cwd=folder, timeout=60)))
    if data.get("rev") != context["raw_read_audit"]["rev"]:
        raise ValueError("Base changed after snapshot; rebuild before sending")
