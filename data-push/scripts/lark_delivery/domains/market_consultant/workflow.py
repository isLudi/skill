"""Current market report orchestration; does not import the legacy report engine."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from ...common import feishu
from ...common.values import _format_value, _rate
from ...common.records import value
from ...common.records import value
from ...common.report_ports import FeishuReportPorts
from ...common.images import _find_font, _center_text
from ...core import catalog
from ...core.contracts import ReportPorts
from . import grade_report, supervisor_report
from .style import BAR_FIELDS, _result_cell_fill
from .adapter import policy_for, report_module_for
from .weekend_dual import REPORT_TYPE as WEEKEND_DUAL_REPORT_TYPE, compose_markdown, merge_mention_info


def _state_dir(args):
    return Path(args.state_dir or os.environ.get("PUSH_STATE_DIR", "runtime/channel-broadcast-push")).expanduser().resolve()


def _channel_scope(definition, requested):
    contract = definition.get("source", {}).get("channel_match", {})
    if contract.get("case_sensitive") is not True:
        raise ValueError("渠道查询契约必须显式声明 case_sensitive=true")
    match_mode = contract.get("match_mode", "exact")
    if match_mode == "exact":
        source_value = contract.get("values", {}).get(requested)
        if not isinstance(source_value, str) or not source_value:
            raise ValueError(f"渠道 {requested} 缺少大小写敏感的 source_value 规范")
        if requested in contract.get("casefold_channels", []):
            return {"match_mode": "casefold_exact", "value": source_value}
        return source_value
    if match_mode == "contains":
        keyword = contract.get("keyword")
        if not isinstance(keyword, str) or not keyword.strip():
            raise ValueError("包含式渠道匹配缺少 keyword")
        return {"match_mode": "contains", "keyword": keyword, "case_sensitive": contract["case_sensitive"]}
    raise ValueError("未审阅的渠道匹配模式：" + str(match_mode))


def _channel_matches(candidate, scope):
    candidate = str(candidate or "")
    if isinstance(scope, str):
        return candidate == scope
    if scope.get("match_mode") == "casefold_exact":
        return candidate.casefold() == scope["value"].casefold()
    if scope.get("match_mode") == "contains":
        keyword = scope["keyword"]
        if scope.get("case_sensitive", True):
            return keyword in candidate
        return keyword.casefold() in candidate.casefold()
    raise ValueError("未知的渠道匹配范围")


def _channel_filter(scope):
    if isinstance(scope, str):
        return ["渠道", "==", scope]
    if scope.get("match_mode") == "casefold_exact":
        return None  # Base has no reviewed casefold filter; read the period, then match locally.
    return ["渠道", "contains", scope["keyword"]]


def source_channel_count(counts, match, channel):
    if channel in match.get("casefold_channels", []):
        source_value = match["values"][channel]
        return sum(n for name, n in counts.items() if str(name).casefold() == source_value.casefold())
    if match.get("match_mode") == "contains":
        keyword = match["keyword"]
        return sum(n for name, n in counts.items() if keyword in str(name))
    return counts.get(channel, 0)


def source_present_channels(cfg, evidence, period):
    """Skip audited zero-row members without blocking other channels in a group."""
    channels = list(cfg["channels"])
    if len(channels) < 2:
        return channels, []
    info = (evidence.get("periods") or {}).get(period)
    counts = info.get("channel_counts") if isinstance(info, dict) else None
    if not isinstance(counts, dict) or any(type(n) is not int or n < 0 for n in counts.values()):
        raise ValueError("多渠道群缺少可信的当期期次渠道清单")
    present, absent = [], []
    for channel in channels:
        (present if source_channel_count(counts, cfg["channel_match"], channel) > 0 else absent).append(channel)
    return present, absent


def prepare_report(args: argparse.Namespace, definition, *, ports: ReportPorts | None = None, services=feishu) -> dict[str, Any]:
    ports = ports or FeishuReportPorts(services)
    broadcast_policy = policy_for(definition)
    report_module = report_module_for(definition)
    is_supervisor = getattr(report_module, "SUPERVISOR_REPORT", False)
    defaults = catalog.source_defaults(definition)
    channel = args.channel.strip()
    chat_id = args.chat_id.strip()
    allowed = {target["chat_id"] for target in catalog.select_targets(definition)}
    if channel not in definition.get("channels", [definition["channel"]]) or chat_id not in allowed:
        raise ValueError("渠道或群ID不在本渠道已登记的投递范围")
    period = broadcast_policy.business_period()
    if args.period and args.period != period and not getattr(args, "allow_period_override", False):
        raise ValueError(f"本周业务期次为{period}，不能用其他期次替代")
    if getattr(args, "allow_period_override", False) and not args.period:
        raise ValueError("期次预览覆盖必须提供明确期次")
    period = args.period or period
    report_type = broadcast_policy.scheduled_report_type() if args.report_type == "auto" else args.report_type
    raw_args = argparse.Namespace(**vars(args))
    if args.base_token or args.table_id or args.view_id:
        raise ValueError("分年级模式使用--raw-source-url和--raw-table-id，不接受旧配置表坐标覆盖")
    raw_args.source_url = getattr(args, "raw_source_url", "") or defaults["raw_source_url"]
    raw_args.base_token = raw_args.table_id = raw_args.view_id = ""
    coords = ports.resolve_source(raw_args)
    if coords["table_id"] != args.raw_table_id:
        raise ValueError("原始数据链接与固定数据表ID不一致")
    raw_coords = {**coords, "view_id": ""}
    names = ports.field_names(coords, args)
    fields, counters = report_module.projection(names, report_type)
    raw_audit = {}
    source_channel = _channel_scope(definition, channel)
    channel_filter = _channel_filter(source_channel)
    conditions = [["期次", "==", period]]
    if channel_filter is not None:
        conditions.insert(0, channel_filter)
    records = ports.read_records(raw_coords, args, fields, audit=raw_audit,
        filter_json={"logic": "and", "conditions": conditions})
    server_returned_count = len(records)
    records = [row for row in records if _channel_matches(value(row, "渠道"), source_channel)
               and str(value(row, "期次")) == period]
    raw_audit["server_returned_count"] = server_returned_count
    raw_audit["client_excluded_count"] = server_returned_count - len(records)
    raw_audit["channel_match_mode"] = source_channel.get("match_mode", "exact") if isinstance(source_channel, dict) else "exact"
    raw_audit["matched_channel_values"] = sorted({str(value(row, "渠道")) for row in records})
    snapshot = report_module.validate_scope(records, channel, period, source_channel=source_channel)
    report_options = {
        "excluded_grades": tuple(definition["report"]["excluded_grades"]),
        "min_post_leads": definition["report"]["minimum_post_leads"],
    }
    weekend_minimum = definition["report"].get("weekend_next_process_minimum_post_leads")
    report_at = getattr(args, "slot", None)
    if (weekend_minimum is not None and report_type == "process"
            and broadcast_policy.scheduled_report_type(report_at) == WEEKEND_DUAL_REPORT_TYPE
            and period == broadcast_policy.next_business_period(broadcast_policy.business_period(report_at))):
        report_options["min_post_leads"] = weekend_minimum
    if is_supervisor:
        report_options["included_grades"] = tuple(
            definition["report"].get("included_grades",
                                     getattr(report_module, "DEFAULT_INCLUDED_GRADES",
                                             supervisor_report.HIGH_SCHOOL_GRADES))
        )
    report = report_module.build_report(records, counters, period, report_type, **report_options)
    profile = definition["source"]["report_profile"]
    skip_delivery = is_supervisor and report["empty_after_minimum_filter"]
    verification_identity = getattr(args, "verification_identity", args.identity)
    chat = ports.verify_target(chat_id, args.chat_name, verification_identity, args.timeout)
    disabled = ("none" if args.no_mentions else args.mention_target) == "none"
    mention_info = {"names": report["reminder_names"], "resolved": {}, "display_names": {},
                    "unresolved": [], "ambiguous": {}, "lookup_error": "", "nonmembers": []}
    if not disabled and report["reminder_names"]:
        expected_target = getattr(report_module, "MENTION_TARGET", "supervisor" if is_supervisor else "manager")
        if ("none" if args.no_mentions else args.mention_target) != expected_target:
            raise ValueError("分年级最低提醒的@对象与报表配置不一致")
        query_builder = getattr(report_module, "mention_queries", report_module.manager_queries)
        candidate_resolver = getattr(report_module, "resolve_mention_candidates",
                                     report_module.resolve_manager_candidates)
        queries = sorted(set(query_builder(report["reminder_names"]).values()))
        try:
            payload = ports.search_users(queries, args)
            mention_info = candidate_resolver(report["reminder_names"], payload)
            mention_info["nonmembers"] = ports.missing_members(
                chat_id, mention_info["resolved"], verification_identity, args.timeout
            )
        except Exception as exc:
            mention_info["lookup_error"] = str(exc)
            mention_info["unresolved"] = [name for name in report["reminder_names"] if name not in mention_info["resolved"]]
    if args.strict_mentions and any(mention_info.get(k) for k in ("unresolved", "ambiguous", "lookup_error", "nonmembers")):
        diagnostic = {key: mention_info.get(key) for key in ("unresolved", "ambiguous", "lookup_error", "nonmembers")
                      if mention_info.get(key)}
        raise ValueError("负责人账号或群成员资格未能完整核验：" + json.dumps(diagnostic, ensure_ascii=False, sort_keys=True))
    paths = {"process": None, "result": None}
    geometry = {}
    if args.with_image and not skip_delivery:
        state = _state_dir(args)
        state.mkdir(parents=True, exist_ok=True)
        prefix = "supervisor-preview-" if is_supervisor else "grade-preview-"
        run_dir = Path(tempfile.mkdtemp(prefix=prefix, dir=state))
        for section in report_module.sections(report_type):
            override = args.output_image if section == "process" else args.output_result_image
            path = Path(override).expanduser().resolve() if override else run_dir / f"{report_module.SECTIONS[section]}_{period}_{channel}.png"
            if path.exists() or path in paths.values():
                raise ValueError("图片路径已存在或重复，停止覆盖")
            if is_supervisor:
                geometry[section] = report_module.render_image(report, section, path, font_loader=_find_font,
                                                                center_text=_center_text, format_value=_format_value,
                                                                rate_parser=_rate)
            else:
                geometry[section] = report_module.render_image(report, section, path, font_loader=_find_font,
                    center_text=_center_text, format_value=_format_value,
                    bar_colors={"首call": BAR_FIELDS["首call率"], "5min": BAR_FIELDS["5min"], "双沟率": BAR_FIELDS["双沟率"]},
                    cell_fill=_result_cell_fill)
            paths[section] = path
    refs = {section: f"img_{section}_preview" if path else None for section, path in paths.items()}
    markdown = "" if skip_delivery else report_module.build_markdown(
        report, period, channel, report_type, mention_info, refs)
    canonical = {"profile": profile + "-v1", "source": {"table": args.raw_table_id, "url": raw_args.source_url},
                 "chat_id": chat_id, "channel": channel, "period": period, "report_type": report_type,
                 "identity": args.identity, "snapshot": snapshot, "report": report, "markdown": markdown}
    digest = hashlib.sha256(json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()[:28]
    flat_rows = {section: [row for block in report["blocks"] for row in report_module.sorted_rows(block, section)]
                 for section in report_module.sections(report_type)}
    return {"coords": raw_coords, "source_mode": "lead-detail", "report_profile": profile, "channel": channel,
            "report_type": report_type, "period": period, "snapshot": snapshot, "raw_table_id": args.raw_table_id,
            "skip_delivery": skip_delivery,
            "skip_reason": ("no_advisor_rows_meet_minimum_post_leads"
                            if getattr(report_module, "REPORT_GRAIN", "") == "advisor"
                            else "no_supervisor_rows_meet_minimum_post_leads") if skip_delivery else "",
            "raw_count": len(records), "raw_read_audit": raw_audit, "grade_report": report,
            "supervisor_report": report if is_supervisor else None, "image_geometry": geometry,
            "rows": flat_rows.get("process", []), "result_rows": flat_rows.get("result", []),
            "image_columns": report_module.COLUMNS["process"] if report_type != "result" else (),
            "result_image_columns": report_module.COLUMNS["result"] if report_type != "process" else (),
            "image_path": paths["process"], "result_image_path": paths["result"], "text_sections": {},
            "mention_target": "none" if disabled else args.mention_target, "mention_info": mention_info, "chat_id": chat_id,
            "chat_name": chat["name"], "chat_name_changed": chat["name_changed"], "identity": args.identity,
            "markdown": markdown, "idempotency_key": ("supervisor-" if is_supervisor else "grade-") + digest,
            "reminder_rule": report["reminder_rule"], "scheduled_report_type_today": broadcast_policy.scheduled_report_type(),
            "ledger": Path(args.ledger).expanduser().resolve() if args.ledger else _state_dir(args) / "send_ledger.jsonl"}


def prepare_weekend_dual_report(args: argparse.Namespace, definition) -> dict[str, Any]:
    """Prepare current-period conversion plus following-period process data."""
    policy = policy_for(definition)
    current_period = args.period or policy.business_period()
    next_period = policy.next_business_period(current_period)

    result_args = argparse.Namespace(**vars(args))
    result_args.report_type = "result"
    result_args.period = current_period
    result_args.allow_period_override = True
    result_context = prepare_report(result_args, definition)

    process_args = argparse.Namespace(**vars(args))
    process_args.report_type = "process"
    process_args.period = next_period
    process_args.allow_period_override = True
    process_context = prepare_report(process_args, definition)

    if result_context["chat_id"] != process_context["chat_id"]:
        raise ValueError("周末双期播报的目标群不一致")
    if result_context["raw_read_audit"].get("rev") != process_context["raw_read_audit"].get("rev"):
        raise ValueError("周末双期播报的两个期次不来自同一Base版本")

    report_profile = result_context["report_profile"]
    is_supervisor = bool(result_context.get("supervisor_report"))
    dual_sections = {"result": result_context, "process": process_context}
    mention_info = merge_mention_info(result_context["mention_info"], process_context["mention_info"])
    skip_delivery = result_context.get("skip_delivery", False) and process_context.get("skip_delivery", False)
    raw_audit = dict(result_context["raw_read_audit"])
    raw_audit["periods"] = {
        current_period: result_context["raw_read_audit"],
        next_period: process_context["raw_read_audit"],
    }
    canonical = {
        "profile": report_profile + "-v1",
        "source": {"table": args.raw_table_id, "url": args.raw_source_url},
        "chat_id": result_context["chat_id"], "channel": result_context["channel"],
        "report_type": WEEKEND_DUAL_REPORT_TYPE,
        "sections": {
            section: {"period": child["period"], "report": child["grade_report"],
                      "markdown": child["markdown"]}
            for section, child in dual_sections.items()
        },
    }
    digest = hashlib.sha256(
        json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:28]
    return {
        "coords": result_context["coords"], "source_mode": "lead-detail", "report_profile": report_profile,
        "channel": result_context["channel"], "report_type": WEEKEND_DUAL_REPORT_TYPE,
        "period": current_period, "next_process_period": next_period,
        "snapshot": result_context["snapshot"], "raw_table_id": args.raw_table_id,
        "raw_count": result_context["raw_count"] + process_context["raw_count"],
        "raw_read_audit": raw_audit, "grade_report": result_context["grade_report"],
        "supervisor_report": result_context.get("supervisor_report") if is_supervisor else None,
        "dual_sections": dual_sections, "skip_delivery": skip_delivery,
        "skip_reason": "no_eligible_rows_in_both_periods" if skip_delivery else "",
        "image_geometry": {"result": result_context["image_geometry"].get("result"),
                           "process": process_context["image_geometry"].get("process")},
        "rows": process_context.get("rows", []), "result_rows": result_context.get("result_rows", []),
        "image_columns": process_context.get("image_columns", ()),
        "result_image_columns": result_context.get("result_image_columns", ()),
        "image_path": process_context.get("image_path"),
        "result_image_path": result_context.get("result_image_path"),
        "text_sections": {}, "mention_target": result_context["mention_target"],
        "mention_info": mention_info, "chat_id": result_context["chat_id"],
        "chat_name": result_context["chat_name"],
        "chat_name_changed": result_context["chat_name_changed"], "identity": result_context["identity"],
        "markdown": compose_markdown({"dual_sections": dual_sections}),
        "idempotency_key": ("supervisor-dual-" if is_supervisor else "grade-dual-") + digest,
        "reminder_rule": result_context["reminder_rule"],
        "scheduled_report_type_today": policy.scheduled_report_type(),
        "ledger": Path(args.ledger).expanduser().resolve() if args.ledger else _state_dir(args) / "send_ledger.jsonl",
    }
