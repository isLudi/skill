"""APP advisor messages from the app_grade_9 Base request."""
from __future__ import annotations

import html
import json
from pathlib import Path
from urllib.parse import quote

from ...common.records import text, value
from . import supervisor_report, supervisor_video49_report as base_report
from . import supervisor_yafei_advisor_report as advisor_style

SUPERVISOR_REPORT = True
REPORT_GRAIN = "advisor"
MENTION_TARGET = "consultant"
MIN_POST_LEADS = 5
DEFAULT_INCLUDED_GRADES = ("初三",)
SECTIONS = base_report.SECTIONS
DIMENSIONS = base_report.DIMENSIONS
COMMON = base_report.COMMON
PROCESS = base_report.PROCESS
RESULT = base_report.RESULT
RESULT_REPORT = advisor_style.RESULT_REPORT
RATE_NUMERATORS = base_report.RATE_NUMERATORS
BAR_COLORS = base_report.BAR_COLORS

COLUMNS = {
    "process": (
        ("期次", "期次", "text"), ("负责人", "负责人", "text"),
        ("主管", "主管", "text"), ("顾问", "顾问", "text"),
        ("退后线索", "退后线索", "count"), ("首call率", "首call", "rate"),
        ("48h外呼", "48h外呼", "rate"), ("外呼频次", "外呼频次", "frequency"),
        ("5min", "5min", "rate"), ("好友率", "好友率", "rate"),
        ("深沟率", "深沟率", "rate"), ("双沟率", "双沟率", "rate"),
    ),
    "result": advisor_style.COLUMNS["result"],
}
WIDTHS = {
    "process": (140, 175, 145, 175, 110, 120, 125, 125, 120, 115, 115, 115),
    "result": advisor_style.WIDTHS["result"],
}

sections = base_report.sections
manager_queries = base_report.manager_queries
resolve_manager_candidates = base_report.resolve_manager_candidates
mention_queries = base_report.mention_queries
resolve_mention_candidates = base_report.resolve_mention_candidates
mention_ids = base_report.mention_ids
sorted_rows = base_report.sorted_rows


def projection(field_names, report_type):
    counters = list(COMMON)
    for section in sections(report_type):
        counters.extend(PROCESS if section == "process" else RESULT_REPORT)
    counters = tuple(dict.fromkeys(counters))
    required = list(DIMENSIONS) + list(counters)
    missing = sorted(set(required) - set(field_names))
    if missing:
        raise ValueError("APP初三顾问播报缺少原始字段：" + "、".join(missing))
    return required, counters


def validate_scope(records, channel, period, *, source_channel=None):
    snapshot = supervisor_report.validate_scope(records, channel, period, source_channel=source_channel)
    for row in records:
        if not text(value(row, "顾问")):
            raise ValueError("APP初三顾问播报不接受空顾问")
    return snapshot


def build_report(records, counters, period, report_type, *, min_post_leads=MIN_POST_LEADS,
                 included_grades=DEFAULT_INCLUDED_GRADES, **unused):
    report = base_report.build_report(records, counters, period, report_type,
                                      min_post_leads=min_post_leads,
                                      included_grades=included_grades, **unused)
    report.update(show_totals=False, result_reminder_metric="截面单效")
    return report


def build_markdown(report, period, channel, report_type, mention_info, image_refs):
    return base_report.build_markdown(report, period, channel, report_type, mention_info,
                                      image_refs).replace("单效较低的顾问", "截面单效最低的顾问")


def render_image(report, section, output_path, **kwargs):
    return base_report.render_image(report, section, output_path,
                                    columns=COLUMNS[section], widths=WIDTHS[section], **kwargs)


def write_preview(context, directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    markdown_path = directory / "message.md"
    html_path = directory / "message.html"
    json_path = directory / "preview.json"
    markdown = context["markdown"]
    for section, field in (("result", "result_image_path"), ("process", "image_path")):
        if context.get(field):
            markdown = markdown.replace(f"](img_{section}_preview)", f"]({Path(context[field]).as_posix()})")
    markdown_path.write_text(markdown, encoding="utf-8")
    images = [Path(path) for path in (context.get("result_image_path"), context.get("image_path")) if path]
    cards = "".join(f'<img src="{quote(path.name)}" alt="APP顾问数据表">' for path in images)
    body = html.escape(context["markdown"])
    html_path.write_text(
        '<!doctype html><meta charset="utf-8"><title>APP初三顾问消息预览</title>'
        '<style>body{font-family:Microsoft YaHei,sans-serif;margin:24px;color:#203b72}'
        'img{display:block;max-width:100%;margin:20px 0}pre{white-space:pre-wrap}</style>'
        '<h1>APP初三顾问消息预览</h1><p>退后线索至少5；隐藏总计行；最低值全部并列提醒。</p>'
        f'{cards}<pre>{body}</pre>', encoding="utf-8")
    json_path.write_text(json.dumps({
        "channel_key": context["channel_key"], "period": context["period"],
        "report_type": context["report_type"], "snapshot": context["snapshot"],
        "raw_count": context["raw_count"], "report": context["grade_report"],
        "message_sent": False,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"html_file": str(html_path), "markdown_file": str(markdown_path),
            "json_file": str(json_path), "image_files": [str(path) for path in images],
            "message_sent": False}
