"""Advisor-grain report for reviewed market channel scopes.

The process and conversion tables are intentionally channel-specific: they keep
the requested columns while ranking and reminding at advisor grain. The source
organization path is ``经理 -> 主管 -> 顾问``; the image labels the first
source field as ``负责人`` for the business-facing report contract.
"""
from __future__ import annotations

from decimal import Decimal
from fractions import Fraction
import html
from pathlib import Path
from typing import Mapping

from ...common.records import numeric, text, value
from .channels import grade_compact as grade_policy
from . import supervisor_report as base_report
from .style import _result_cell_fill


SUPERVISOR_REPORT = True
REPORT_GRAIN = "advisor"
MENTION_TARGET = "consultant"
MIN_POST_LEADS = 1
SECTIONS = base_report.SECTIONS
DIMENSIONS = (*base_report.DIMENSIONS, "顾问")
COMMON = base_report.COMMON
PROCESS = base_report.PROCESS
RESULT = ("首节到课标记", "当期净收款", "报科数", "成交人头", "订单数",
          "净收款", "收款", "退费")
RESULT_REPORT = RESULT
DEFAULT_INCLUDED_GRADES = ("初一", "初三", "高一", "高二", "高三")

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
        ("退后线索", "退后线索", "count"), ("首节到课率", "首节到课率", "rate"),
        ("单效（当期）", "单效（当期）", "amount"), ("人均报科", "人均报科", "number"),
        ("人头转化", "人头转化", "rate"), ("订单转化", "订单转化", "rate"),
        ("净收款", "净收款", "amount"), ("退费率", "退费率", "rate"),
        ("单效", "单效", "amount"),
    ),
}
WIDTHS = {
    "process": (145, 180, 150, 180, 115, 115, 145, 130, 130, 130, 140, 120, 120, 145, 120, 120),
    "result": (125, 170, 145, 175, 115, 160, 160, 145, 145, 145, 165, 135, 145),
}
RATE_NUMERATORS = base_report.RATE_NUMERATORS
BAR_COLORS = {
    "5min": "#f5ae23", "双沟率": "#138de2",
    "首节到课率": "#4f78ae", "人头转化": "#62bc7f", "订单转化": "#138de2",
    "人均报科": "#f5ae23", "退费率": "#fb5a68",
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
        raise ValueError("朱博士-视频号49主管播报缺少原始字段：" + "、".join(missing))
    return required, counters


def validate_scope(records, channel, period, *, source_channel=None):
    scope = source_channel or channel
    if not records:
        raise ValueError(f"{channel}在当期{period}没有数据；不回退到其他期次")
    seen, snapshots = set(), set()
    for row in records:
        for field in DIMENSIONS:
            if not text(value(row, field)):
                raise ValueError("线索缺少必要字段：" + field)
        candidate = text(value(row, "渠道"))
        if isinstance(scope, Mapping) and scope.get("match_mode") == "contains":
            keyword = text(scope.get("keyword"))
            matches = keyword in candidate if scope.get("case_sensitive", True) else keyword.casefold() in candidate.casefold()
        else:
            matches = candidate == scope
        if not matches or text(value(row, "期次")) != period:
            raise ValueError("返回记录超出本次渠道范围或期次")
        key = (period, text(value(row, "lead_id")))
        if key in seen:
            raise ValueError("期次+lead_id重复，停止汇总")
        seen.add(key)
        snapshots.add((text(value(row, "分区日期")), text(value(row, "分区小时"))))
    if len(snapshots) != 1:
        raise ValueError("原始数据跨多个数仓快照，停止汇总")
    return next(iter(snapshots))
_empty = base_report._empty
_add = base_report._add
_metrics = base_report._metrics
manager_queries = base_report.manager_queries
resolve_manager_candidates = base_report.resolve_manager_candidates
mention_queries = base_report.manager_queries
resolve_mention_candidates = base_report.resolve_manager_candidates
mention_ids = base_report.mention_ids


def build_report(records, counters, period, report_type, *, min_post_leads=MIN_POST_LEADS,
                 included_grades=DEFAULT_INCLUDED_GRADES, **_unused):
    minimum = Decimal(min_post_leads)
    included_grades = frozenset(included_grades)
    if not included_grades:
        raise ValueError("朱博士-视频号49主管播报必须至少包含一个年级")
    grades = {}
    excluded_grade_counts = {}
    for row in records:
        supervisor, manager, consultant, grade = (
            text(value(row, field)) for field in ("主管", "经理", "顾问", "年级")
        )
        if not supervisor or not manager or not consultant or not grade:
            raise ValueError("顾问粒度播报不接受空年级、负责人、主管或顾问")
        if grade not in included_grades:
            excluded_grade_counts[grade] = excluded_grade_counts.get(grade, 0) + 1
            continue
        amounts = {field: numeric(value(row, field), field) for field in counters}
        for field, amount in amounts.items():
            if field not in {"当期净收款", "净收款"} and amount < 0:
                raise ValueError("非净收款指标出现负数：" + field)
        for field in ("首call完成标记", "48h外呼标记", "5min标记", "好友标记",
                      "APP登陆标记", "深沟标记", "双沟标记", "首节到课标记"):
            if field in amounts and amounts[field] not in (0, 1):
                raise ValueError("原始标记必须为0或1：" + field)
        group = grades.setdefault(grade, {"sums": _empty(counters), "advisors": {},
                                          "raw_count": 0})
        _add(group["sums"], amounts)
        advisor_key = (manager, supervisor, consultant)
        _add(group["advisors"].setdefault(advisor_key, _empty(counters)), amounts)
        group["raw_count"] += 1

    blocks = []
    hidden_image_rows = []
    for grade in sorted(grades, key=grade_policy.grade_sort_key):
        group = grades[grade]
        rows = []
        visible_sums = _empty(counters)
        for (manager, supervisor, consultant), sums in sorted(group["advisors"].items()):
            if sums["退后线索"] < minimum:
                hidden_image_rows.append({"grade": grade, "负责人": manager, "主管": supervisor,
                                          "顾问": consultant, "退后线索": str(sums["退后线索"])})
                continue
            rows.append({"fields": {**_metrics(sums), "期次": period, "负责人": manager,
                                     "主管": supervisor, "顾问": consultant},
                         "sums": {field: str(amount) for field, amount in sums.items()}})
            _add(visible_sums, sums)
        if not rows:
            continue
        total = {"fields": {**_metrics(visible_sums), "期次": "总计", "负责人": "",
                             "主管": "", "顾问": ""}}
        reminders, advisor_metrics = {}, {}
        for section in sections(report_type):
            numerator = "5min标记" if section == "process" else "净收款"
            eligible = {key: Fraction(sums[numerator]) / Fraction(sums["退后线索"])
                        for key, sums in group["advisors"].items()
                        if sums["退后线索"] >= minimum}
            lowest = min(eligible.values()) if eligible else None
            reminders[section] = sorted({key[2] for key, metric in eligible.items() if metric == lowest})
            advisor_metrics[section] = {
                "|".join(key): {"负责人": key[0], "主管": key[1], "顾问": key[2],
                                "numerator": str(group["advisors"][key][numerator]),
                                "denominator": str(group["advisors"][key]["退后线索"])}
                for key in eligible
            }
        hidden = sorted("|".join(key) for key, sums in group["advisors"].items()
                        if sums["退后线索"] < minimum)
        blocks.append({"grade": grade, "rows": rows, "total": total,
                       "reminders": reminders, "advisor_metrics": advisor_metrics,
                       "hidden_advisors_below_minimum": hidden, "raw_count": group["raw_count"]})

    return {"blocks": blocks, "raw_count": len(records), "min_post_leads": min_post_leads,
            "included_grades": sorted(included_grades, key=grade_policy.grade_sort_key),
            "excluded_grade_counts": excluded_grade_counts,
            "hidden_image_rows_below_minimum": hidden_image_rows,
            "empty_after_minimum_filter": not blocks,
            "reminder_names": sorted({name for block in blocks
                                       for names in block["reminders"].values() for name in names}),
            "reminder_rule": "channel_grade_source_advisor_minimum_all_ties"}


def sorted_rows(block, section):
    def key(row):
        sums = row["sums"]
        post_leads = Fraction(sums["退后线索"])
        if section == "process":
            pre_leads = Fraction(sums["退前线索"])
            five_min_rate = Fraction(sums["5min标记"]) / post_leads if post_leads else None
            retention_rate = post_leads / pre_leads if pre_leads else None
            return (five_min_rate is None, -five_min_rate if five_min_rate is not None else Fraction(0),
                    retention_rate is None, -retention_rate if retention_rate is not None else Fraction(0),
                    row["fields"].get("负责人", ""), row["fields"].get("主管", ""),
                    row["fields"].get("顾问", ""))
        effect = Fraction(sums["净收款"]) / post_leads if post_leads else None
        attendance = Fraction(sums["首节到课标记"]) / post_leads if post_leads else None
        return (effect is None, -effect if effect is not None else Fraction(0),
                attendance is None, -attendance if attendance is not None else Fraction(0),
                row["fields"].get("负责人", ""), row["fields"].get("主管", ""),
                row["fields"].get("顾问", ""))
    return sorted(block["rows"], key=key)


def build_markdown(report, period, channel, report_type, mention_info, image_refs):
    lines = []
    for section in sections(report_type):
        if lines:
            lines.append("")
        lines.extend([f"## 🔥 **【{period}】{html.escape(channel)}渠道{SECTIONS[section]}播报**", ""])
        if image_refs.get(section):
            lines.extend([f"![负责人-主管-顾问三级维度{SECTIONS[section]}]({image_refs[section]})", ""])
        lines.append(f"- 推送期次：{period}")
        metric = "5min 率" if section == "process" else "单效"
        for block in report["blocks"]:
            if not block["reminders"][section]:
                continue
            people = []
            nonmembers = set(mention_info.get("nonmembers", ()))
            for name in block["reminders"][section]:
                open_id = mention_info["resolved"].get(name)
                label = html.escape(mention_info.get("display_names", {}).get(name, name))
                if open_id and name not in nonmembers:
                    people.append(f'<at user_id="{open_id}">{label}</at>')
                elif name in nonmembers:
                    people.append(label + "（未入群，待核验）")
                else:
                    people.append(label + "（待核验）")
            lines.append(f"- {html.escape(channel)}渠道{html.escape(block['grade'])}年级 {metric}较低的顾问："
                         + ("、".join(people) or f"暂无退后线索不少于{report['min_post_leads']}的顾问"))
    return "\n".join(lines)


def render_image(report, section, output_path, *, font_loader, center_text, format_value, rate_parser,
                 columns=None, widths=None):
    from PIL import Image, ImageDraw

    columns = COLUMNS[section] if columns is None else columns
    widths = WIDTHS[section] if widths is None else widths
    if len(columns) != len(widths):
        raise ValueError("Image column widths differ from the column contract")
    width = sum(widths)
    band_h, header_h, row_h, total_h, gap = 48, 58, 50, 54, 20
    show_totals = report.get("show_totals", True)
    heights = [band_h + header_h + len(block["rows"]) * row_h + (total_h if show_totals else 0)
               for block in report["blocks"]]
    image = Image.new("RGB", (width, sum(heights) + gap * (len(heights) - 1)), "#ffffff")
    draw = ImageDraw.Draw(image)
    navy, grid = "#203b72", "#b8c4d3"
    process_bars = {"首call率": "#4f78ae", "5min": "#f5ae23", "双沟率": "#138de2"}
    xs = [0]
    for size in widths:
        xs.append(xs[-1] + size)
    top, geometry = 0, []
    try:
        for block, height in zip(report["blocks"], heights):
            geometry.append({"grade": block["grade"], "top": top, "height": height,
                             "rows": len(block["rows"])})
            draw.rectangle((0, top, width, top + band_h), fill="#e8eef8")
            draw.text((16, top + 8), block["grade"], font=font_loader(24, True), fill=navy)
            header = top + band_h
            draw.rectangle((0, header, width, header + header_h), fill=navy)
            for (_source, label, _kind), left, right in zip(columns, xs, xs[1:]):
                center_text(draw, (left + 3, header, right - 3, header + header_h), label,
                            font_loader(20, True), "#ffffff")
            ordered = sorted_rows(block, section)
            effect_source = "截面单效" if any(source == "截面单效" for source, _label, _kind in columns) else "单效"
            effect_values = sorted({float(item["fields"][effect_source]) for item in ordered
                                    if isinstance(item["fields"].get(effect_source), (int, float, Decimal))},
                                   reverse=True)
            effect_rank = {id(item): effect_values.index(float(item["fields"][effect_source]))
                           for item in ordered if isinstance(item["fields"].get(effect_source), (int, float, Decimal))}
            image_rows = [*ordered, block["total"]] if show_totals else ordered
            for index, row in enumerate(image_rows):
                y, total = header + header_h + index * row_h, index == len(ordered)
                bottom = y + (total_h if total else row_h)
                draw.rectangle((0, y, width, bottom), fill=navy if total else "#ffffff")
                for (source, _label, kind), left, right in zip(columns, xs, xs[1:]):
                    cell = row["fields"].get(source, "")
                    if not total and section == "process" and source == "线索留存率":
                        draw.rectangle((left, y, right, bottom),
                                       fill=base_report._retention_fill(cell, rate_parser))
                    if not total and source in {"单效", "截面单效"} and isinstance(cell, (int, float, Decimal)):
                        draw.rectangle((left, y, right, bottom), fill=_result_cell_fill(
                            "单效", cell, effect_rank.get(id(row)), len(effect_values)))
                    bars = process_bars if section == "process" else BAR_COLORS
                    if not total and source in bars:
                        rate = rate_parser(cell) if kind == "rate" else None
                        if source == "人均报科" and isinstance(cell, (int, float, Decimal)):
                            rate = min(1.0, max(0.0, float(cell) / 3.0))
                        if rate is not None and rate > 0:
                            draw.rectangle((left + 4, y + 7,
                                            left + 4 + int((right - left - 8) * min(1, rate)), bottom - 7),
                                           fill=bars[source])
                    draw.rectangle((left, y, right, bottom), outline=grid, width=1)
                    center_text(draw, (left + 3, y, right - 3, bottom), format_value(cell, kind),
                                font_loader(19, total), "#ffffff" if total else "#111827")
            top += height + gap
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path, format="PNG", optimize=True)
    finally:
        image.close()
    return geometry


def write_preview(context, directory):
    return base_report.write_preview(context, directory)
