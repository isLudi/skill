"""Legacy CLI parsing and preview presentation; operations delegated through its boundary."""
from __future__ import annotations
import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence
from .market_schema import IMAGE_COLUMNS, OUTCOME_TERMS
from .market_aggregation import _raw_field, reminder_names, visible_image_rows
from ..common.values import _string
from . import market_leads as lead_report
from ..domains.market_consultant import grade_report
from ..paths import SKILL_ROOT
from ..core.catalog import resolve_compat_config
from . import market_delivery as manual_delivery
SCRIPT_DIR = SKILL_ROOT / "scripts"


def _state_dir(args: argparse.Namespace) -> Path:
    value = args.state_dir or os.environ.get("PUSH_STATE_DIR", "runtime/channel-broadcast-push")
    return Path(value).expanduser().resolve()


def push_defaults() -> dict[str, Any]:
    path = SCRIPT_DIR.parent / "config" / "push_source.json"
    defaults = resolve_compat_config(path, "source")
    if defaults.get("reminder_rule") not in {"channel_bottom_quartile", "grade_manager_minimum_all_ties"}:
        raise ValueError("未知推送提醒规则")
    if defaults.get("reminder_population") != "raw_leads":
        raise ValueError("推送提醒范围必须使用原始线索全量顾问，不依赖辅助表覆盖范围")
    if defaults.get("mention_target", "none") not in {"none", "consultant", "supervisor", "manager"}:
        raise ValueError("未知@对象类型")
    return defaults


def effective_mention_target(args: argparse.Namespace) -> str:
    # Explicit no-mentions and the names-only profile override stale flags.
    return "none" if args.no_mentions else getattr(args, "mention_target", "none")


def add_common_arguments(parser: argparse.ArgumentParser, *, services) -> None:
    defaults = push_defaults()
    parser.add_argument("--source-mode", choices=("lead-detail", "summary-view"), default=defaults["source_mode"], help="默认：新 Base 的线索明细；summary-view 为旧汇总视图兼容模式")
    parser.add_argument("--base-token", default="", help="可选：显式覆盖 Base 坐标，不继承旧 BASE_TOKEN")
    parser.add_argument("--table-id", default="", help="可选：推送配置表 ID/名称")
    parser.add_argument("--view-id", default="", help="可选：推送配置视图 ID/名称")
    parser.add_argument("--source-url", default=defaults["source_url"], help="默认使用 config/push_source.json 中的新推送配置 URL")
    parser.add_argument("--raw-table-id", default=defaults["raw_table_id"], help="同一 Base 中的线索明细表 ID/名称")
    parser.add_argument("--raw-source-url", default=defaults.get("raw_source_url", ""), help="分年级模式的原始数据表链接")
    parser.add_argument("--report-profile", choices=("standard", "grade-compact"), default=defaults.get("report_profile", "standard"))
    parser.add_argument("--channel", default=defaults.get("default_channel", ""), help="精确渠道名称；目标固定群仅允许已配置渠道")
    parser.add_argument("--report-type", choices=("auto", *lead_report.SECTIONS), default=defaults["report_type"], help="auto按周一至四仅过程、周五至日两类；预览可显式指定类型")
    parser.add_argument("--text-table-id", default=os.environ.get("TEXT_TABLE_ID", ""), help="推送文字表 ID/名称")
    parser.add_argument("--text-view-id", default=os.environ.get("TEXT_VIEW_ID", ""), help="推送文字视图 ID/名称")
    parser.add_argument("--text-source-url", default=os.environ.get("TEXT_SOURCE_URL", ""), help="可选：由 Base/Wiki URL 解析推送文字表")
    parser.add_argument(
        "--result-view-id",
        default=os.environ.get("RESULT_VIEW_ID", "结果数据"),
        help="结果数据视图 ID/名称；默认读取同一表的“结果数据”",
    )
    parser.add_argument("--base-as", choices=("user", "bot"), default=os.environ.get("BASE_AS", "user"))
    parser.add_argument("--chat-id", default=os.environ.get("CHAT_ID", defaults.get("default_chat_id", "")), help="目标群唯一chat_id；群名称仅供展示")
    parser.add_argument("--chat-name", default=os.environ.get("CHAT_NAME", ""), help="可选：旧群名称提示，不用于定位或阻断改名后的群")
    parser.add_argument("--as", dest="identity", choices=("user", "bot"), default=os.environ.get("SEND_AS", defaults.get("sender_identity", "user")), help="发送身份")
    parser.add_argument("--period", default=os.environ.get("PERIOD", ""), help="精确期次；多期视图时必填")
    parser.add_argument("--mention-map", default=os.environ.get("MENTION_MAP", ""), help="可选 JSON：{姓名: ou_xxx}")
    parser.add_argument("--mention-target", choices=("none", "consultant", "supervisor", "manager"), default=defaults.get("mention_target", "none"),
                        help="分年级模式按经理独立汇总并@最低负责人；并列最低全部提醒")
    parser.add_argument("--require-mention-membership", action="store_true", help="必须完整回读目标群并核验所有@账号已在群内")
    parser.add_argument("--no-mentions", action="store_true", default=defaults.get("mention_target", "none") == "none",
                        help="仅供无@预览或旧模式使用；固定群正式播报不允许禁用已要求的@")
    parser.add_argument("--strict-mentions", action="store_true", help="预览时也要求所有姓名都能精确解析")
    parser.add_argument("--allow-unresolved-mentions", action="store_true", help="发送时允许无法精确解析的姓名以纯文本发送")
    parser.add_argument("--no-image", dest="with_image", action="store_false", help="不生成汇总表图片")
    parser.set_defaults(with_image=True)
    parser.add_argument("--output-image", default=os.environ.get("OUTPUT_IMAGE", ""), help="图片输出路径；默认写入状态目录")
    parser.add_argument(
        "--output-result-image",
        default=os.environ.get("OUTPUT_RESULT_IMAGE", ""),
        help="结果图片输出路径；默认写入状态目录",
    )
    parser.add_argument("--state-dir", default=os.environ.get("PUSH_STATE_DIR", ""), help="状态/台账目录")
    parser.add_argument("--ledger", default=os.environ.get("PUSH_LEDGER", ""), help="幂等台账路径")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--max-pages", type=int, default=100)


def print_preview(context: Mapping[str, Any]) -> None:
    mention_info = context["mention_info"]
    summary = {
        "mode": "preview",
        "period": context["period"],
        "row_count": len(context["rows"]),
        "result_row_count": len(context["result_rows"]),
        "image_row_count": len(visible_image_rows(context["rows"])),
        "result_image_row_count": len(visible_image_rows(context["result_rows"])),
        "image_hidden_zero_lead_rows": len(context["rows"]) - len(visible_image_rows(context["rows"])),
        "result_image_hidden_zero_lead_rows": len(context["result_rows"]) - len(visible_image_rows(context["result_rows"])),
        "text_section_count": len(context["text_sections"]),
        "text_sections": {
            section: {
                "title": _string(_raw_field(row, "推送标题")),
                "reminder_names": reminder_names(row),
            }
            for section, row in context["text_sections"].items()
        },
        "chat_id": context["chat_id"] or None,
        "identity": context["identity"],
        "image_path": str(context["image_path"]) if context["image_path"] else None,
        "result_image_path": str(context["result_image_path"]) if context["result_image_path"] else None,
        "image_columns": [label for _source, label, _kind in context["image_columns"]],
        "image_omitted_columns": [
            label for source, label, _kind in IMAGE_COLUMNS if source not in {item[0] for item in context["image_columns"]}
        ],
        "result_image_columns": [label for _source, label, _kind in context["result_image_columns"]],
        "idempotency_key": context["idempotency_key"],
        "mention_resolved": sorted(mention_info["resolved"]),
        "mention_unresolved": mention_info["unresolved"],
        "mention_ambiguous": mention_info["ambiguous"],
        "mention_nonmembers": mention_info.get("nonmembers", []),
        "process_excluded_outcome_fields": list(OUTCOME_TERMS),
        "result_section_policy": "结果图片从同一批线索聚合，不改写原始表" if context.get("source_mode") == "lead-detail" else "结果图片读取独立结果视图；不改写原始表",
    }
    for field in ("source_mode", "channel", "report_type", "raw_table_id", "raw_count", "raw_read_audit", "snapshot", "reminder_rule", "reminder_quotas", "config_reminder_check", "consultant_count", "totals", "mention_target", "reminder_supervisors"):
        if field in context:
            summary[field] = context[field]
    if context.get("report_profile") == "grade-compact":
        report = context["grade_report"]
        summary.pop("image_omitted_columns", None)
        summary.update({"report_profile": "grade-compact", "chat_name": context["chat_name"],
                        "displayed_grades": [b["grade"] for b in report["blocks"]],
                        "grade_manager_reminders": {b["grade"]: b["reminders"] for b in report["blocks"]},
                        "omitted_grades": report["omitted_grades"], "excluded_grade_counts": report["excluded_grade_counts"],
                        "scheduled_report_type_today": context["scheduled_report_type_today"]})
        summary["text_section_count"] = len(grade_report.sections(context["report_type"]))
        summary["text_sections"] = {section: {"title": grade_report.SECTIONS[section],
                                  "reminder_names": sorted({name for b in report["blocks"] for name in b["reminders"][section]})}
                                  for section in grade_report.sections(context["report_type"])}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if mention_info.get("lookup_error"):
        print("[warning] 通讯录解析未完成：%s" % mention_info["lookup_error"])
    if any(not item["matches"] for item in context.get("config_reminder_check", {}).values()):
        print("[warning] 配置表的提醒名单与原始线索计算不同；当前预览使用原始线索全量后25%，请核对辅助表覆盖范围/刷新状态。")
    print("\n----- 群消息 Markdown 预览 -----\n")
    print(context["markdown"])


def main(argv: Sequence[str] | None = None, *, services) -> int:
    parser = argparse.ArgumentParser(description="飞书多维表格按渠道推送过程/结果数据：默认预览，真实发送需显式确认")
    subparsers = parser.add_subparsers(dest="command", required=True)
    preview_parser = subparsers.add_parser("preview", help="读取视图并生成本地图片/Markdown预览，不发送")
    services.add_common_arguments(preview_parser)
    preview_parser.add_argument("--cli-dry-run", action="store_true", help="额外调用 im +messages-send --dry-run 校验请求形状")

    channels_parser = subparsers.add_parser("list-channels", help="只读列出新配置表的渠道、期次与推送类型")
    services.add_common_arguments(channels_parser)

    send_parser = subparsers.add_parser("send", help="发送群消息；必须 --confirm-send，或使用 --dry-run")
    services.add_common_arguments(send_parser)
    send_parser.add_argument("--confirm-send", action="store_true", help="确认执行真实群消息发送")
    send_parser.add_argument("--dry-run", action="store_true", help="调用 lark-cli dry-run，不上传图片、不发送消息")

    sync_parser = subparsers.add_parser("sync-helper", help="预览或追加提醒计算表缺失的顾问维度行，不删除任何记录")
    services.add_common_arguments(sync_parser)
    sync_parser.add_argument(
        "--helper-table-id",
        default=os.environ.get("HELPER_TABLE_ID", "IP播报_提醒计算"),
        help="提醒计算表 ID/名称；默认 IP播报_提醒计算",
    )
    sync_parser.add_argument(
        "--helper-raw-table-id",
        default=os.environ.get("HELPER_RAW_TABLE_ID", "IP原始数据"),
        help="原始明细表 ID/名称；默认 IP原始数据",
    )
    sync_parser.add_argument("--confirm-helper-sync", action="store_true", help="确认追加缺失维度行")

    args = parser.parse_args(argv)
    if args.command == "sync-helper":
        if args.source_mode != "summary-view":
            raise SystemExit("新线索模式在本地计算渠道提醒，无需同步提醒表；旧辅助表操作必须显式选择 --source-mode summary-view")
        return services.sync_helper_dimension(args)
    if args.command == "list-channels":
        return services.list_channels(args)
    if args.command == "send" and not args.confirm_send and not args.dry_run:
        raise SystemExit("send 默认不执行外发；请先用 preview，确认后再传 --confirm-send，或传 --dry-run")
    context = services.prepare(args)
    if args.command == "preview":
        services.print_preview(context)
        if context.get("report_profile") == "grade-compact":
            picture = context.get("image_path") or context.get("result_image_path")
            state = _state_dir(args)
            state.mkdir(parents=True, exist_ok=True)
            preview_dir = Path(picture).parent if picture else Path(tempfile.mkdtemp(prefix="grade-text-preview-", dir=state))
            artifacts = grade_report.write_preview(context, preview_dir)
            print(json.dumps({"preview_files": artifacts, "message_sent": False}, ensure_ascii=False, indent=2))
        if args.cli_dry_run:
            if not context["chat_id"]:
                raise SystemExit("--cli-dry-run 需要 --chat-id 或 CHAT_ID")
            services.send_markdown(context["chat_id"], context["markdown"], context["idempotency_key"], context["identity"], dry_run=True, timeout=args.timeout)
            print("\n[ok] lark-cli im +messages-send --dry-run 通过（未发送）")
        return 0

    return manual_delivery.deliver_context(context, args, services=services)
