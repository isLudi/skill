"""Supervisor-scoped manager report built from additive lead-detail fields."""
from __future__ import annotations

from decimal import Decimal
from fractions import Fraction
import html
import json
import os
from pathlib import Path
from urllib.parse import quote

from ...common.records import numeric, text, value
from . import grade_report
from .channels import grade_compact as grade_policy

SECTIONS = {"process": "过程数据", "result": "转化数据"}
DIMENSIONS = ("lead_id", "期次", "渠道", "经理", "主管", "年级", "分区日期", "分区小时")
COMMON = ("退前线索", "退后线索")
PROCESS = ("总通时秒", "首call完成标记", "48h外呼标记", "外呼次数", "5min标记",
           "好友标记", "APP登陆标记", "深沟标记", "双沟标记")
RESULT = ("首节到课标记", "当期净收款", "报科数", "成交人头", "订单数",
          "净收款", "收款", "退费")
RESULT_REPORT = ("5min标记", "双沟标记", "首节到课标记", "当期净收款", "报科数", "成交人头", "订单数",
                 "净收款", "收款", "退费")
COLUMNS = {
    "process": (("期次", "期次", "text"), ("负责人", "负责人", "text"), ("主管", "主管", "text"),
                ("退前线索", "退前线索", "count"), ("退后线索", "退后线索", "count"),
                ("线索留存率", "线索留存率", "rate"), ("总通时", "总通时", "duration"),
                ("首call率", "首call率", "rate"), ("48h外呼", "48h外呼", "rate"),
                ("外呼频次", "外呼频次", "frequency"), ("5min", "5min", "rate"),
                ("好友率", "好友率", "rate"), ("APP登陆率", "APP登陆率", "rate"),
                ("深沟率", "深沟率", "rate"), ("双沟率", "双沟率", "rate")),
    "result": (("期次", "期次", "text"), ("负责人", "负责人", "text"), ("主管", "主管", "text"),
               ("退后线索", "退后线索", "count"), ("5min", "5min", "rate"),
               ("双沟率", "双沟率", "rate"), ("首节到课率", "首节到课率", "rate"),
               ("当期单效", "当期单效", "amount"), ("截面单效", "截面单效", "amount")),
}
WIDTHS = {
    "process": (150, 190, 170, 125, 125, 155, 135, 135, 135, 145, 125, 125, 150, 125, 125),
    "result": (130, 180, 150, 130, 150, 165, 180, 180, 180),
}
RATE_NUMERATORS = {
    "线索留存率": "退后线索", "首call率": "首call完成标记",
    "48h外呼": "48h外呼标记", "5min": "5min标记", "好友率": "好友标记",
    "APP登陆率": "APP登陆标记", "深沟率": "深沟标记", "双沟率": "双沟标记",
    "首节到课率": "首节到课标记", "人头转化": "成交人头", "订单转化": "报科数",
}
BAR_COLORS = {"首call率": "#4f78ae", "5min": "#f5ae23", "双沟率": "#138de2",
              "人均报科": "#f5ae23", "退费率": "#fb5a68"}
HIGH_SCHOOL_GRADES = frozenset({"高一", "高二", "高三"})
RETENTION_COLOR_SCALE = (
    (Decimal("0.88"), "#62bc7f"),
    (Decimal("0.80"), "#d9df83"),
    (Decimal("0.75"), "#f9c777"),
    (Decimal("0.72"), "#fa9a7e"),
)
RETENTION_LOW_COLOR = "#fb626b"


def sections(report_type):
    if report_type not in {"process", "result", "both"}:
        raise ValueError("未知的播报类型")
    return ("process", "result") if report_type == "both" else (report_type,)


def projection(field_names, report_type):
    counters = list(COMMON)
    for section in sections(report_type):
        counters.extend(PROCESS if section == "process" else RESULT_REPORT)
    counters = tuple(dict.fromkeys(counters))
    required = list(DIMENSIONS) + list(counters)
    missing = sorted(set(required) - set(field_names))
    if missing:
        raise ValueError("主管明细播报缺少原始字段：" + "、".join(missing))
    return required, counters


def validate_scope(records, channel, period, *, source_channel=None):
    source_channel = source_channel or channel
    if not records:
        raise ValueError(f"{channel}在当期{period}没有数据；不回退到其他期次")
    seen, snapshots = set(), set()
    for row in records:
        for field in DIMENSIONS:
            if not text(value(row, field)):
                raise ValueError("线索缺少必要字段：" + field)
        if text(value(row, "渠道")) != source_channel or text(value(row, "期次")) != period:
            raise ValueError("返回记录超出本次渠道或期次")
        key = (period, text(value(row, "lead_id")))
        if key in seen:
            raise ValueError("期次+lead_id重复，停止汇总")
        seen.add(key)
        snapshots.add((text(value(row, "分区日期")), text(value(row, "分区小时"))))
    if len(snapshots) != 1:
        raise ValueError("原始数据跨多个数仓快照，停止汇总")
    return next(iter(snapshots))


def _empty(counters):
    return {field: Decimal(0) for field in counters}


def _add(target, amounts):
    for field, amount in amounts.items():
        target[field] += amount


def _rate(numerator, denominator):
    return f"{numerator / denominator * 100:.8f}%" if denominator else "-"


def _metrics(sums):
    pre, post = sums["退前线索"], sums["退后线索"]
    result = {field: float(amount) for field, amount in sums.items()}
    for display, numerator in RATE_NUMERATORS.items():
        if numerator in sums:
            result[display] = _rate(sums[numerator], pre if display == "线索留存率" else post)
    if "总通时秒" in sums:
        result["总通时"] = float(sums["总通时秒"])
        result["外呼频次"] = float(sums["外呼次数"] / post) if post else "-"
    if "净收款" in sums:
        result["单效（当期）"] = float(sums["当期净收款"] / post) if post else "-"
        result["人均报科"] = float(sums["报科数"] / sums["成交人头"]) if sums["成交人头"] else "-"
        result["退费率"] = _rate(sums["退费"], sums["收款"])
        result["单效"] = float(sums["净收款"] / post) if post else "-"
        result["当期单效"] = result["单效（当期）"]
        result["截面单效"] = result["单效"]
    return result


def build_report(records, counters, period, report_type, *, min_post_leads=10,
                 included_grades=HIGH_SCHOOL_GRADES, **_unused):
    minimum = Decimal(min_post_leads)
    included_grades = frozenset(included_grades)
    if not included_grades:
        raise ValueError("年级主管明细播报必须至少包含一个年级")
    grades = {}
    excluded_grade_counts = {}
    for row in records:
        supervisor, manager, grade = (text(value(row, field)) for field in ("主管", "经理", "年级"))
        if not supervisor or not manager or not grade:
            raise ValueError("年级主管明细播报不接受空年级、主管或负责人")
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
                                          "reminder_supervisors": {}, "raw_count": 0})
        _add(group["sums"], amounts)
        _add(group["advisors"].setdefault((supervisor, manager), _empty(counters)), amounts)
        _add(group["reminder_supervisors"].setdefault(supervisor, _empty(counters)), amounts)
        group["raw_count"] += 1
    blocks = []
    hidden_image_rows = []
    for grade in sorted(grades, key=grade_policy.grade_sort_key):
        group = grades[grade]
        rows = []
        visible_sums = _empty(counters)
        for (supervisor, manager), sums in sorted(group["advisors"].items()):
            if sums["退后线索"] < minimum:
                hidden_image_rows.append({"grade": grade, "负责人": manager, "主管": supervisor,
                                          "退后线索": str(sums["退后线索"])})
                continue
            rows.append({"fields": {**_metrics(sums), "期次": period, "负责人": manager, "主管": supervisor},
                         "sums": {field: str(amount) for field, amount in sums.items()}})
            _add(visible_sums, sums)
        if not rows:
            continue
        total = {"fields": {**_metrics(visible_sums), "期次": "总计", "负责人": "", "主管": ""}}
        reminders, supervisor_metrics = {}, {}
        for section in sections(report_type):
            numerator = "5min标记" if section == "process" else "净收款"
            eligible = {name: Fraction(sums[numerator]) / Fraction(sums["退后线索"])
                        for name, sums in group["reminder_supervisors"].items()
                        if sums["退后线索"] >= minimum}
            lowest = min(eligible.values()) if eligible else None
            reminders[section] = sorted(name for name, metric in eligible.items() if metric == lowest)
            supervisor_metrics[section] = {
                name: {"numerator": str(group["reminder_supervisors"][name][numerator]),
                       "denominator": str(group["reminder_supervisors"][name]["退后线索"])}
                for name in eligible
            }
        hidden = sorted(name for name, sums in group["reminder_supervisors"].items()
                        if sums["退后线索"] < minimum)
        blocks.append({"grade": grade, "rows": rows, "total": total,
                       "reminders": reminders, "supervisor_metrics": supervisor_metrics,
                       "hidden_supervisors_below_minimum": hidden, "raw_count": group["raw_count"]})
    return {"blocks": blocks, "raw_count": len(records), "min_post_leads": min_post_leads,
            "included_grades": sorted(included_grades, key=grade_policy.grade_sort_key),
            "excluded_grade_counts": excluded_grade_counts,
            "hidden_image_rows_below_minimum": hidden_image_rows,
            "empty_after_minimum_filter": not blocks,
            "reminder_names": sorted({name for block in blocks
                                         for names in block["reminders"].values() for name in names}),
            "reminder_rule": "channel_grade_source_supervisor_minimum_all_ties"}


manager_queries = grade_report.manager_queries
resolve_manager_candidates = grade_report.resolve_manager_candidates
mention_ids = grade_report.mention_ids


def sorted_rows(block, section):
    def key(row):
        post_leads = Fraction(row["sums"]["退后线索"])
        if section == "process":
            pre_leads = Fraction(row["sums"]["退前线索"])
            five_min_rate = Fraction(row["sums"]["5min标记"]) / post_leads if post_leads else None
            retention_rate = post_leads / pre_leads if pre_leads else None
            return (
                five_min_rate is None,
                -five_min_rate if five_min_rate is not None else Fraction(0),
                retention_rate is None,
                -retention_rate if retention_rate is not None else Fraction(0),
                row["fields"]["负责人"],
            )
        metric = Fraction(row["sums"]["净收款"]) / post_leads if post_leads else None
        return (metric is None, -metric if metric is not None else Fraction(0), row["fields"]["负责人"])
    return sorted(block["rows"], key=key)


def build_markdown(report, period, channel, report_type, mention_info, image_refs):
    lines = []
    for section in sections(report_type):
        if lines:
            lines.append("")
        lines.extend([f"## 🔥 **【{period}】{html.escape(channel)}渠道{SECTIONS[section]}播报**", ""])
        if image_refs.get(section):
            lines.extend([f"![主管维度{SECTIONS[section]}]({image_refs[section]})", ""])
        lines.append(f"- 推送期次：{period}")
        metric = "5min 率" if section == "process" else "单效"
        for block in report["blocks"]:
            if not block["reminders"][section]:
                continue
            people = []
            for name in block["reminders"][section]:
                open_id = mention_info["resolved"].get(name)
                label = html.escape(mention_info.get("display_names", {}).get(name, name))
                people.append(f'<at user_id="{open_id}">{label}</at>' if open_id else label + "（待核验）")
            lines.append(f"- {html.escape(channel)}渠道{html.escape(block['grade'])}年级 {metric}较低："
                         + ("、".join(people) or "暂无退后线索不少于10的主管"))
    return "\n".join(lines)


def _retention_fill(value, rate_parser):
    rate = rate_parser(value)
    if rate is None:
        return "#ffffff"
    normalized = Decimal(str(rate))
    for threshold, color in RETENTION_COLOR_SCALE:
        if normalized >= threshold:
            return color
    return RETENTION_LOW_COLOR


def render_image(report, section, output_path, *, font_loader, center_text, format_value, rate_parser):
    from PIL import Image, ImageDraw
    columns, widths = COLUMNS[section], WIDTHS[section]
    width = sum(widths)
    band_h, header_h, row_h, total_h, gap = 48, 58, 50, 54, 20
    if not report["blocks"]:
        height = 180
        image = Image.new("RGB", (width, height), "#ffffff")
        draw = ImageDraw.Draw(image)
        try:
            draw.rectangle((0, 0, width, 58), fill="#203b72")
            center_text(draw, (0, 0, width, 58), SECTIONS[section], font_loader(22, True), "#ffffff")
            center_text(draw, (0, 58, width, height),
                        f"暂无主管聚合退后线索不少于{report['min_post_leads']}的数据",
                        font_loader(24, True), "#64748b")
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            image.save(output_path, format="PNG", optimize=True)
        finally:
            image.close()
        return [{"empty": True, "top": 0, "height": height, "rows": 0}]
    heights = [band_h + header_h + len(block["rows"]) * row_h + total_h for block in report["blocks"]]
    image = Image.new("RGB", (width, sum(heights) + gap * (len(heights) - 1)), "#ffffff")
    draw = ImageDraw.Draw(image)
    navy, grid = "#203b72", "#b8c4d3"
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
            effect_rows = ordered if section == "result" else []
            effect_values = sorted({float(item["fields"]["截面单效"]) for item in effect_rows
                                    if isinstance(item["fields"].get("截面单效"), (int, float, Decimal))},
                                   reverse=True)
            effect_rank = {id(item): effect_values.index(float(item["fields"]["截面单效"]))
                           for item in effect_rows
                           if isinstance(item["fields"].get("截面单效"), (int, float, Decimal))}
            for index, row in enumerate([*ordered, block["total"]]):
                y, total = header + header_h + index * row_h, index == len(ordered)
                bottom = y + (total_h if total else row_h)
                draw.rectangle((0, y, width, bottom), fill=navy if total else "#ffffff")
                for (source, _label, kind), left, right in zip(columns, xs, xs[1:]):
                    cell = row["fields"].get(source, "")
                    if not total and source == "线索留存率":
                        draw.rectangle((left, y, right, bottom), fill=_retention_fill(cell, rate_parser))
                    if not total and source == "截面单效" and isinstance(cell, (int, float, Decimal)):
                        rank = effect_rank.get(id(row), 0)
                        palette = ("#62bc7f", "#d9df83", "#f9c777", "#fa9a7e", "#fb626b")
                        if len(effect_values) <= 1:
                            color = palette[len(palette) // 2]
                        else:
                            color = palette[min(len(palette) - 1, max(0, round(rank * (len(palette) - 1) / (len(effect_values) - 1))))]
                        draw.rectangle((left, y, right, bottom), fill=color)
                    if not total and source in BAR_COLORS:
                        rate = rate_parser(cell) if kind == "rate" else None
                        if source == "人均报科" and isinstance(cell, (int, float, Decimal)):
                            rate = min(1.0, max(0.0, float(cell) / 3.0))
                        if rate is not None and rate > 0:
                            draw.rectangle((left + 4, y + 7,
                                            left + 4 + int((right - left - 8) * min(1, rate)), bottom - 7),
                                           fill=BAR_COLORS[source])
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
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    report, info = context["supervisor_report"], context["mention_info"]
    markdown, cards, image_files = context["markdown"], [], {}
    for section in sections(context["report_type"]):
        path = Path(context["image_path" if section == "process" else "result_image_path"])
        image_files[section] = str(path)
        local = quote(os.path.relpath(path, directory).replace(os.sep, "/"))
        escaped = html.escape(local, quote=True)
        markdown = markdown.replace(f"](img_{section}_preview)", f"]({path.as_posix()})")
        metric = "5min 率" if section == "process" else "单效"
        reminders = []
        for block in report["blocks"]:
            if not block["reminders"][section]:
                continue
            people = []
            for name in block["reminders"][section]:
                label = html.escape(info.get("display_names", {}).get(name, name))
                people.append(f'<span class="mention">@{label}</span>' if name in info["resolved"]
                              else label + "（待核验）")
            reminders.append(f"<li>{html.escape(context['channel'])}渠道{html.escape(block['grade'])}年级 "
                             f"{metric}较低：{'、'.join(people)}</li>")
        cards.append(f'<section><h2>🔥 <strong>【{context["period"]}】{html.escape(context["channel"])}渠道{SECTIONS[section]}播报</strong></h2>'
                     f'<a href="{escaped}"><img src="{escaped}"></a><ul>'
                     f'<li>推送期次：{context["period"]}</li>{"".join(reminders)}</ul></section>')
    dt, hour = context["snapshot"]
    document = '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>飞书群消息预览</title>'
    document += '<style>body{margin:0;background:#f4f6fa;color:#1f2329;font:16px/1.6 "Microsoft YaHei",sans-serif}.wrap{max-width:1300px;margin:28px auto;padding:0 20px}.note{background:#eaf1ff;color:#244c87;border-radius:12px;padding:16px 20px}.bubble{background:#fff;border:1px solid #e3e7ef;border-radius:14px;padding:22px;margin-top:18px}h2{margin:12px 0}img{width:100%;height:auto;border:1px solid #e3e7ef}.mention{color:#3370ff;background:#eff4ff;padding:1px 4px}section+section{border-top:1px solid #ddd;margin-top:24px;padding-top:18px}</style>'
    document += f'<body><main class="wrap"><h1>{html.escape(context["chat_name"])}</h1><div class="note">仅本地预览：没有发送消息，也不会触发@通知。<br>固定群ID：{context["chat_id"]}｜数据分区：{dt} {int(hour):02d}:00</div><div class="bubble"><b>管家 · 消息样式预览</b>{"".join(cards)}</div></main></body></html>'
    html_path, markdown_path = directory / "message-preview.html", directory / "message-preview.md"
    metadata_path = directory / "preview-metadata.json"
    html_path.write_text(document, encoding="utf-8")
    markdown_path.write_text(markdown + "\n", encoding="utf-8")
    metadata = {key: context[key] for key in ("report_profile", "period", "report_type", "channel", "chat_id",
                                               "chat_name", "identity", "raw_count", "raw_read_audit", "snapshot",
                                               "mention_info", "image_geometry")}
    metadata.update({"mode": "preview_only", "message_sent": False, "image_files": image_files, "report": report})
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"html": str(html_path), "markdown": str(markdown_path), "metadata": str(metadata_path)}
