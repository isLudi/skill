"""Advisor-grain Yafei report using the existing supervisor metric contract.

This module deliberately wraps the reviewed advisor aggregation/rendering code
without changing the Zhu Doctor or Chen Ruichun channels.  Its only channel-
specific behavior is the Yafei image column contract and bottom-10% reminder
selection, with at least one eligible advisor per grade and report section.
"""
from __future__ import annotations

from fractions import Fraction
from math import ceil
from pathlib import Path

from . import supervisor_video49_report as base_report


SUPERVISOR_REPORT = True
REPORT_GRAIN = "advisor"
MENTION_TARGET = "consultant"
MIN_POST_LEADS = 5
REMINDER_FRACTION = 0.10
SECTIONS = base_report.SECTIONS
DIMENSIONS = base_report.DIMENSIONS
COMMON = base_report.COMMON
PROCESS = base_report.PROCESS
RESULT = base_report.RESULT
# The conversion image intentionally includes the two process indicators
# needed for advisor-level reminders and review.  The reused Zhu Doctor
# advisor module's result contract does not request them, so they must be
# added here before projection/aggregation; otherwise the columns render
# blank even though the source contains the marker fields.
RESULT_REPORT = tuple(dict.fromkeys(("5min标记", "双沟标记", *base_report.RESULT_REPORT)))
DEFAULT_INCLUDED_GRADES = ("初三",)
RATE_NUMERATORS = base_report.RATE_NUMERATORS
BAR_COLORS = base_report.BAR_COLORS

COLUMNS = {
    "process": (
        ("期次", "期次", "text"), ("负责人", "负责人", "text"),
        ("主管", "主管", "text"), ("顾问", "顾问", "text"),
        ("退前线索", "退前线索", "count"), ("退后线索", "退后线索", "count"),
        ("线索留存率", "线索留存率", "rate"), ("总通时(min)", "总通时(min)", "duration"),
        ("首call率", "首call率", "rate"), ("48h外呼", "48h外呼", "rate"),
        ("外呼频次", "外呼频次", "frequency"), ("5min", "5min", "rate"),
        ("好友率", "好友率", "rate"), ("APP登陆率", "APP登陆率", "rate"),
        ("深沟率", "深沟率", "rate"), ("双沟率", "双沟率", "rate"),
    ),
    "result": (
        ("期次", "期次", "text"), ("负责人", "负责人", "text"),
        ("主管", "主管", "text"), ("顾问", "顾问", "text"),
        ("退后线索", "退后线索", "count"), ("5min", "5min", "rate"),
        ("双沟率", "双沟率", "rate"), ("首节到课率", "首节到课率", "rate"),
        ("当期单效", "当期单效", "amount"), ("截面单效", "截面单效", "amount"),
    ),
}
WIDTHS = {
    "process": (140, 175, 145, 175, 110, 110, 140, 125, 125, 125, 135, 115, 115, 135, 115, 115),
    "result": (125, 165, 140, 165, 110, 145, 145, 160, 160, 160),
}


def sections(report_type):
    return base_report.sections(report_type)


def projection(field_names, report_type):
    counters = list(COMMON)
    for section in sections(report_type):
        counters.extend(PROCESS if section == "process" else RESULT_REPORT)
    counters = tuple(dict.fromkeys(counters))
    required = list(DIMENSIONS) + list(counters)
    missing = sorted(set(required) - set(field_names))
    if missing:
        raise ValueError("亚飞B站初三顾问播报缺少原始字段：" + "、".join(missing))
    return required, counters


validate_scope = base_report.validate_scope
manager_queries = base_report.manager_queries
resolve_manager_candidates = base_report.resolve_manager_candidates
mention_queries = base_report.mention_queries
resolve_mention_candidates = base_report.resolve_mention_candidates
mention_ids = base_report.mention_ids
build_markdown = base_report.build_markdown
write_preview = base_report.write_preview


def _metric(item):
    return Fraction(int(item["numerator"]), int(item["denominator"]))


def build_report(records, counters, period, report_type, *, min_post_leads=MIN_POST_LEADS,
                 included_grades=DEFAULT_INCLUDED_GRADES, **unused):
    report = base_report.build_report(
        records,
        counters,
        period,
        report_type,
        min_post_leads=min_post_leads,
        included_grades=included_grades,
        **unused,
    )
    for block in report["blocks"]:
        quotas = {}
        for section in sections(report_type):
            metrics = block.get("advisor_metrics", {}).get(section, {})
            ranked = sorted(
                metrics.values(),
                key=lambda item: (
                    _metric(item),
                    item.get("负责人", ""),
                    item.get("主管", ""),
                    item.get("顾问", ""),
                ),
            )
            quota = max(1, ceil(len(ranked) * REMINDER_FRACTION)) if ranked else 0
            quotas[section] = quota
            block["reminders"][section] = [item["顾问"] for item in ranked[:quota]]
        block["reminder_quotas"] = quotas
    report["reminder_fraction"] = REMINDER_FRACTION
    report["reminder_rule"] = "channel_grade_source_advisor_bottom_10pct_minimum_one"
    report["reminder_names"] = sorted({
        name
        for block in report["blocks"]
        for names in block["reminders"].values()
        for name in names
    })
    return report


def sorted_rows(block, section):
    """Keep process order, but explicitly rank conversion rows by 截面单效 desc."""
    if section != "result":
        return base_report.sorted_rows(block, section)

    def key(row):
        sums = row["sums"]
        post_leads = Fraction(sums["退后线索"])
        effect = Fraction(sums["净收款"]) / post_leads if post_leads else None
        attendance = Fraction(sums["首节到课标记"]) / post_leads if post_leads else None
        return (
            effect is None,
            -effect if effect is not None else Fraction(0),
            attendance is None,
            -attendance if attendance is not None else Fraction(0),
            row["fields"].get("负责人", ""),
            row["fields"].get("主管", ""),
            row["fields"].get("顾问", ""),
        )

    return sorted(block["rows"], key=key)


def render_image(report, section, output_path, *, font_loader, center_text, format_value, rate_parser):
    """Reuse the reviewed renderer with the Yafei advisor column contract."""
    original_columns, original_widths = base_report.COLUMNS, base_report.WIDTHS
    base_report.COLUMNS, base_report.WIDTHS = COLUMNS, WIDTHS
    try:
        return base_report.render_image(
            report,
            section,
            output_path,
            font_loader=font_loader,
            center_text=center_text,
            format_value=format_value,
            rate_parser=rate_parser,
        )
    finally:
        base_report.COLUMNS, base_report.WIDTHS = original_columns, original_widths
