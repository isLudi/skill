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
from ...common.values import _format_value
from ...common.report_ports import FeishuReportPorts
from ...common.images import _find_font, _center_text
from ...core import catalog
from ...core.contracts import ReportPorts
from . import grade_report
from .style import BAR_FIELDS, _result_cell_fill
from .adapter import policy_for


def _state_dir(args):
    return Path(args.state_dir or os.environ.get("PUSH_STATE_DIR", "runtime/channel-broadcast-push")).expanduser().resolve()


def prepare_report(args: argparse.Namespace, definition, *, ports: ReportPorts | None = None, services=feishu) -> dict[str, Any]:
    ports = ports or FeishuReportPorts(services)
    broadcast_policy = policy_for(definition)
    defaults = catalog.source_defaults(definition)
    channel = args.channel.strip()
    chat_id = args.chat_id.strip()
    allowed = {target["chat_id"] for target in catalog.select_targets(definition)}
    if channel not in definition.get("channels", [definition["channel"]]) or chat_id not in allowed:
        raise ValueError("渠道或群ID不在本渠道已登记的投递范围")
    period = broadcast_policy.business_period()
    if args.period and args.period != period:
        raise ValueError(f"本周业务期次为{period}，不能用其他期次替代")
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
    fields, counters = grade_report.projection(names, report_type)
    raw_audit = {}
    records = ports.read_records(raw_coords, args, fields, audit=raw_audit,
        filter_json={"logic": "and", "conditions": [["渠道", "==", channel], ["期次", "==", period]]})
    snapshot = grade_report.validate_scope(records, channel, period)
    report = grade_report.build_report(records, counters, period, report_type,
        excluded_grades=tuple(definition["report"]["excluded_grades"]),
        min_post_leads=definition["report"]["minimum_post_leads"])
    chat = ports.verify_target(chat_id, args.chat_name, args.identity, args.timeout)
    disabled = ("none" if args.no_mentions else args.mention_target) == "none"
    mention_info = {"names": report["reminder_names"], "resolved": {}, "display_names": {},
                    "unresolved": [], "ambiguous": {}, "lookup_error": "", "nonmembers": []}
    if not disabled:
        if ("none" if args.no_mentions else args.mention_target) != "manager":
            raise ValueError("分年级最低提醒须使用manager模式")
        queries = sorted(set(grade_report.manager_queries(report["reminder_names"]).values()))
        try:
            payload = ports.search_users(queries, args)
            mention_info = grade_report.resolve_manager_candidates(report["reminder_names"], payload)
            mention_info["nonmembers"] = ports.missing_members(chat_id, mention_info["resolved"], args.identity, args.timeout)
        except Exception as exc:
            mention_info["lookup_error"] = str(exc)
            mention_info["unresolved"] = [name for name in report["reminder_names"] if name not in mention_info["resolved"]]
    if args.strict_mentions and any(mention_info.get(k) for k in ("unresolved", "ambiguous", "lookup_error", "nonmembers")):
        raise ValueError("负责人账号或群成员资格未能完整核验")
    paths = {"process": None, "result": None}
    geometry = {}
    if args.with_image:
        state = _state_dir(args)
        state.mkdir(parents=True, exist_ok=True)
        run_dir = Path(tempfile.mkdtemp(prefix="grade-preview-", dir=state))
        for section in grade_report.sections(report_type):
            override = args.output_image if section == "process" else args.output_result_image
            path = Path(override).expanduser().resolve() if override else run_dir / f"{grade_report.SECTIONS[section]}_{period}_{channel}.png"
            if path.exists() or path in paths.values():
                raise ValueError("图片路径已存在或重复，停止覆盖")
            geometry[section] = grade_report.render_image(report, section, path, font_loader=_find_font,
                                                         center_text=_center_text, format_value=_format_value,
                                                         bar_colors={"首call": BAR_FIELDS["首call率"], "5min": BAR_FIELDS["5min"], "双沟率": BAR_FIELDS["双沟率"]},
                                                         cell_fill=_result_cell_fill)
            paths[section] = path
    refs = {section: f"img_{section}_preview" if path else None for section, path in paths.items()}
    markdown = grade_report.build_markdown(report, period, channel, report_type, mention_info, refs)
    canonical = {"profile": "grade-compact-v1", "source": {"table": args.raw_table_id, "url": raw_args.source_url},
                 "chat_id": chat_id, "channel": channel, "period": period, "report_type": report_type,
                 "identity": args.identity, "snapshot": snapshot, "report": report, "markdown": markdown}
    digest = hashlib.sha256(json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()[:28]
    flat_rows = {section: [row for block in report["blocks"] for row in grade_report.sorted_rows(block, section)]
                 for section in grade_report.sections(report_type)}
    return {"coords": raw_coords, "source_mode": "lead-detail", "report_profile": "grade-compact", "channel": channel,
            "report_type": report_type, "period": period, "snapshot": snapshot, "raw_table_id": args.raw_table_id,
            "raw_count": len(records), "raw_read_audit": raw_audit, "grade_report": report, "image_geometry": geometry,
            "rows": flat_rows.get("process", []), "result_rows": flat_rows.get("result", []),
            "image_columns": grade_report.COLUMNS["process"] if report_type != "result" else (),
            "result_image_columns": grade_report.COLUMNS["result"] if report_type != "process" else (),
            "image_path": paths["process"], "result_image_path": paths["result"], "text_sections": {},
            "mention_target": "none" if disabled else "manager", "mention_info": mention_info, "chat_id": chat_id,
            "chat_name": chat["name"], "chat_name_changed": chat["name_changed"], "identity": args.identity,
            "markdown": markdown, "idempotency_key": "grade-" + digest,
            "reminder_rule": report["reminder_rule"], "scheduled_report_type_today": broadcast_policy.scheduled_report_type(),
            "ledger": Path(args.ledger).expanduser().resolve() if args.ledger else _state_dir(args) / "send_ledger.jsonl"}
