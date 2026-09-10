"""Legacy report composition with an injected compatibility boundary."""
from __future__ import annotations
import argparse
import re
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence
from .market_schema import PROCESS_FIELDS, TEXT_SECTION_ORDER, RESULT_FIELDS, RESULT_IMAGE_COLUMNS, IMAGE_ROW_FILTER
from . import market_leads as lead_report
from ..domains.market_consultant.channels import self_incubated_koc_5 as broadcast_policy


def prepare_lead_report(args: argparse.Namespace, *, services) -> dict[str, Any]:
    channel = args.channel.strip()
    if not channel:
        raise SystemExit("请用 --channel 选择精确渠道（list-channels 可查看配置）；全部推送必须显式选择“全部渠道”")
    coords, config_records = services._read_channel_configs(args)
    configs = lead_report.select_configs(config_records, channel, args.report_type, args.period)
    requested = lead_report.requested_period(configs, args.period)
    raw_coords = {"base_token": coords["base_token"], "table_id": args.raw_table_id, "view_id": ""}
    schema = services._unwrap(services._json_payload(services.run_lark([
        "base", "+field-list", "--base-token", coords["base_token"], "--table-id", args.raw_table_id,
        "--format", "json", "--as", args.base_as,
    ], timeout=args.timeout)))
    field_names = {services._string(item.get("field_name") or item.get("name")) for item in services._iter_dicts(schema)}
    fields, counters = lead_report.projection(field_names, args.report_type)
    conditions = []
    if channel != "全部渠道":
        conditions.append(["渠道", "==", channel])
    if requested:
        conditions.append(["期次", "==", requested])
    # Explicit filters replace view filters: query the raw table without a
    # view, and bind both channel and period here instead of trusting a view.
    raw_audit: dict[str, Any] = {}
    records = services._fetch_view_records(
        raw_coords, args, fields, temp_prefix=".channel-leads-",
        filter_json={"logic": "and", "conditions": conditions} if conditions else None, audit=raw_audit,
    )
    scoped, period, snapshot = lead_report.validate_scope(records, channel, requested)
    if len(scoped) != len(records):
        raise ValueError("原始表返回了筛选范围以外的记录，停止推送")
    report = lead_report.build_report(scoped, counters, period)
    text_sections = lead_report.text_sections(configs, report, period, channel, snapshot)
    config_reminder_check = {}
    for section, configured in configs.items():
        # Remote reminder columns are optional legacy diagnostics, never a
        # runtime dependency. The lean Base retains only seven config fields.
        has_cached_reminder = any(k in configured.get("fields", configured) for k in ("计算_提醒顾问", "提醒"))
        if has_cached_reminder and configured.get("record_id") and services._string(services._raw_field(configured, "推送期次")) == period:
            cached_names = set(services.reminder_names(configured))
            fresh_names = set(services.reminder_names(text_sections[section]))
            config_reminder_check[section] = {
                "matches": cached_names == fresh_names, "config_name_count": len(cached_names),
                "raw_name_count": len(fresh_names), "only_config_count": len(cached_names - fresh_names),
                "only_raw_count": len(fresh_names - cached_names),
            }
    mention_target = services.effective_mention_target(args)
    mentions_disabled = mention_target == "none"
    if mention_target == "supervisor":
        for section, row in text_sections.items():
            row["fields"].update({"_mention_target": "supervisor",
                                  "_reminder_supervisors": report["reminder_supervisors"][section]})
        configured_names = sorted({name for section in text_sections for name in report["reminder_supervisors"][section]})
        if any(not name for name in configured_names):
            raise ValueError("提醒顾问缺少对应主管，不能可靠生成主管提醒")
    else:
        configured_names = sorted({name for row in text_sections.values() for name in services.reminder_names(row)})
        if mentions_disabled:
            for row in text_sections.values():
                row["fields"]["_mention_target"] = "none"
    mention_info = services.resolve_mentions(
        [], mention_map={} if mentions_disabled else services._load_mention_map(args.mention_map or None), no_lookup=False,
        disable_mentions=mentions_disabled, extra_names=configured_names, timeout=args.timeout,
    )
    if args.strict_mentions and (mention_info["unresolved"] or mention_info["ambiguous"]):
        raise SystemExit("存在未能唯一解析的 @ 姓名，请提供 --mention-map 消歧")
    chat_id = lead_report.configured_chat(configs, args.chat_id.strip())
    if args.chat_name:
        if not chat_id:
            raise SystemExit("校验群名称前需要接收群配置或 --chat-id")
        services.verify_chat(chat_id, args.chat_name, args.identity, args.timeout)
    if getattr(args, "require_mention_membership", False) and not mentions_disabled:
        mention_info["nonmembers"] = services.mention_nonmembers(chat_id, mention_info["resolved"], args.identity, args.timeout)
        if args.strict_mentions and mention_info["nonmembers"]:
            raise SystemExit("以下 @ 人员未在目标群内：" + "、".join(mention_info["nonmembers"]))

    def project_rows(allowed: Sequence[str], sort_field: str, rate: bool = False) -> list[dict[str, Any]]:
        selected = [{"record_id": "", "fields": {k: v for k, v in row["fields"].items() if k in allowed}}
                    for row in report["rows"]]
        def sort_key(row: Mapping[str, Any]) -> tuple[Any, ...]:
            raw = services._raw_field(row, sort_field)
            number = services._rate(raw) if rate else services._number(raw)
            return (number is None, -number if number is not None else 0,
                    services._string(services._raw_field(row, "渠道")), services._string(services._raw_field(row, "主管")))
        return sorted(selected, key=sort_key)

    rows = project_rows(PROCESS_FIELDS, "5min", True) if args.report_type != "result" else []
    result_rows = project_rows(RESULT_FIELDS, "单效") if args.report_type != "process" else []
    image_columns = services.available_image_columns(rows) if rows else ()
    result_columns = RESULT_IMAGE_COLUMNS if result_rows else ()
    if channel == "全部渠道":
        if rows:
            image_columns = (image_columns[0], ("渠道", "渠道", "text"), *image_columns[1:])
        if result_rows:
            result_columns = (result_columns[0], ("渠道", "渠道", "text"), *result_columns[1:])
    total_fields = {**report["totals"], "期次": "总计"}
    process_total = {"fields": {k: v for k, v in total_fields.items() if k in PROCESS_FIELDS}}
    result_total = {"fields": {k: v for k, v in total_fields.items() if k in RESULT_FIELDS}}
    image_path = result_image_path = None
    if args.with_image:
        state_dir = services._state_dir(args)
        state_dir.mkdir(parents=True, exist_ok=True)
        run_dir = Path(tempfile.mkdtemp(prefix="preview-", dir=state_dir))
        suffix = "%s_%s" % (services._safe_period(period), re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", channel))
        if rows:
            image_path = Path(args.output_image).expanduser().resolve() if args.output_image else run_dir / ("过程数据_%s.png" % suffix)
        if result_rows:
            result_image_path = Path(args.output_result_image).expanduser().resolve() if args.output_result_image else run_dir / ("结果数据_%s.png" % suffix)
        if image_path and image_path == result_image_path:
            raise ValueError("过程图片与结果图片不能使用同一个输出路径")
        for path in (image_path, result_image_path):
            if path and path.exists():
                raise ValueError("图片路径已存在，请选择新路径，避免覆盖已有预览")
        if image_path:
            services.render_process_image(rows, image_path, columns=image_columns, total=process_total)
        if result_image_path:
            services.render_result_image(result_rows, result_image_path, columns=result_columns, total=result_total)
    markdown = services.build_markdown(
        rows, period=period, source_label="市场顾问原始数据 / 按期次、渠道汇总 / lark-cli",
        mention_info=mention_info, image_ref="img_process_preview" if image_path else None,
        text_sections=text_sections, result_image_ref="img_result_preview" if result_image_path else None,
    ).replace("![IP过程数据表]", "![过程数据表]").replace("![IP结果数据表]", "![结果数据表]")
    key = services.idempotency_key(
        coords, chat_id, period, rows, text_coords=coords, text_sections=text_sections,
        result_coords=raw_coords, result_rows=result_rows,
        delivery={"source_mode": "lead-detail", "channel": channel, "snapshot": snapshot,
                  "mention_target": mention_target,
                  "report_type": args.report_type, "identity": args.identity, "markdown": markdown,
                  "reminder_rule": "channel_bottom_quartile",
                  "image_row_filter": IMAGE_ROW_FILTER if args.with_image else None,
                  "totals": {k: v for k, v in report["totals"].items() if k in set(PROCESS_FIELDS + RESULT_FIELDS)}},
    )
    return {
        "coords": coords, "source_mode": "lead-detail", "channel": channel, "report_type": args.report_type,
        "raw_table_id": args.raw_table_id, "raw_count": len(scoped), "raw_read_audit": raw_audit,
        "snapshot": snapshot, "reminder_rule": "同一期次、所属渠道后25%",
        "mention_target": mention_target, "reminder_supervisors": report["reminder_supervisors"],
        "reminder_quotas": report["reminder_quotas"],
        "config_reminder_check": config_reminder_check,
        "totals": report["totals"], "consultant_count": report["consultant_count"],
        "rows": rows, "result_rows": result_rows, "period": period, "text_sections": text_sections,
        "mention_info": mention_info, "chat_id": chat_id, "chat_name": args.chat_name, "identity": args.identity,
        "image_path": image_path, "result_image_path": result_image_path, "image_columns": image_columns,
        "result_image_columns": result_columns, "markdown": markdown, "idempotency_key": key,
        "ledger": Path(args.ledger).expanduser().resolve() if args.ledger else services._state_dir(args) / "send_ledger.jsonl",
    }


def prepare_summary_view(args: argparse.Namespace, *, services) -> dict[str, Any]:
    coords = services.resolve_coordinates(args)
    records = services.fetch_records(coords, args)
    period = services.select_period(records, args.period or None)
    rows = services.select_rows(records, period)
    result_coords = {
        "base_token": coords["base_token"],
        "table_id": coords["table_id"],
        "view_id": services._string(getattr(args, "result_view_id", "")) or "结果数据",
        "source_url": coords.get("source_url", ""),
    }
    result_records = services.fetch_result_records(result_coords, args)
    result_source_rows = services.select_rows(result_records, period)
    result_rows = services.aggregate_result_rows(result_source_rows, period)
    text_coords = services.resolve_text_coordinates(args, coords)
    text_records = services.fetch_text_records(text_coords, args)
    text_sections = services.select_text_config(text_records, period)
    mention_target = services.effective_mention_target(args)
    mentions_disabled = mention_target == "none"
    if mentions_disabled:
        for row in text_sections.values():
            row["fields"]["_mention_target"] = "none"
    configured_reminder_names: list[str] = []
    for section in TEXT_SECTION_ORDER:
        row = text_sections.get(section)
        if not row:
            continue
        for name in services.reminder_names(row):
            if name not in configured_reminder_names:
                configured_reminder_names.append(name)
    mention_info = services.resolve_mentions(
        [],
        mention_map={} if mentions_disabled else services._load_mention_map(args.mention_map or None),
        no_lookup=False,
        disable_mentions=mentions_disabled,
        extra_names=configured_reminder_names,
        timeout=args.timeout,
    )
    if args.strict_mentions and (mention_info["unresolved"] or mention_info["ambiguous"]):
        raise SystemExit("存在未能唯一解析的 @ 姓名：%s" % ", ".join(mention_info["unresolved"] + list(mention_info["ambiguous"])))
    chat_id = (args.chat_id or "").strip()
    if args.chat_name:
        services.verify_chat(chat_id, args.chat_name, args.identity, args.timeout)
    if not chat_id and args.chat_name:
        raise SystemExit("--chat-name 校验通过后仍需要 --chat-id 或 CHAT_ID")
    image_path: Path | None = None
    result_image_path: Path | None = None
    image_ref = None
    result_image_ref = None
    image_columns = services.available_image_columns(rows)
    if args.with_image:
        state_dir = services._state_dir(args)
        image_path = Path(args.output_image).expanduser().resolve() if args.output_image else state_dir / ("IP过程数据_%s.png" % services._safe_period(period))
        result_image_path = (
            Path(args.output_result_image).expanduser().resolve()
            if args.output_result_image
            else state_dir / ("IP结果数据_%s.png" % services._safe_period(period))
        )
        if image_path == result_image_path:
            raise SystemExit("过程图片与结果图片不能使用同一个输出路径")
        services.render_process_image(rows, image_path)
        services.render_result_image(result_rows, result_image_path)
        image_ref = "img_process_preview"
        result_image_ref = "img_result_preview"
    # Never put the full source URL into the group message: a Wiki/Base URL
    # can contain a share token.  The table/view coordinates are sufficient
    # for human traceability and remain safe to display.
    source_label = "%s / %s / lark-cli" % (coords["table_id"], coords["view_id"])
    markdown = services.build_markdown(
        rows,
        period=period,
        source_label=source_label,
        mention_info=mention_info,
        image_ref=image_ref,
        text_sections=text_sections,
        result_image_ref=result_image_ref,
    )
    key = services.idempotency_key(
        coords,
        chat_id,
        period,
        rows,
        text_coords=text_coords,
        text_sections=text_sections,
        result_coords=result_coords,
        result_rows=result_rows,
        delivery={"image_row_filter": IMAGE_ROW_FILTER if args.with_image else None,
                  "mention_target": mention_target, "markdown": markdown},
    )
    ledger = Path(args.ledger).expanduser().resolve() if args.ledger else services._state_dir(args) / "send_ledger.jsonl"
    return {
        "coords": coords,
        "records": records,
        "mention_target": mention_target,
        "rows": rows,
        "result_coords": result_coords,
        "result_records": result_records,
        "result_source_rows": result_source_rows,
        "result_rows": result_rows,
        "period": period,
        "text_coords": text_coords,
        "text_records": text_records,
        "text_sections": text_sections,
        "mention_info": mention_info,
        "chat_id": chat_id,
        "chat_name": args.chat_name,
        "identity": args.identity,
        "image_path": image_path,
        "image_columns": image_columns,
        "result_image_path": result_image_path,
        "result_image_columns": RESULT_IMAGE_COLUMNS,
        "markdown": markdown,
        "idempotency_key": key,
        "ledger": ledger,
    }


def prepare(args: argparse.Namespace, *, services) -> dict[str, Any]:
    if args.report_type == "auto":
        args.report_type = broadcast_policy.scheduled_report_type()
    profile = getattr(args, "report_profile", "standard")
    broadcast_policy.enforce_group_scope(args.chat_id, args.channel, profile)
    if profile == "grade-compact":
        if args.source_mode != "lead-detail":
            raise ValueError("分年级精简播报仅支持原始线索模式")
        return services.prepare_grade_report(args)
    if args.source_mode == "lead-detail":
        return services.prepare_lead_report(args)
    if services.effective_mention_target(args) != "none" and (
        services.effective_mention_target(args) != "consultant" or getattr(args, "require_mention_membership", False)
    ):
        raise ValueError("主管提醒及群成员核验仅支持新线索明细模式")
    return services.prepare_summary_view(args)
