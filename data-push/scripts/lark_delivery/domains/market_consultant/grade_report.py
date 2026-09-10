"""Grade tables and minimum reminders at the same manager grain."""
from __future__ import annotations

from collections import Counter
from decimal import Decimal
from fractions import Fraction
import html
import json
import os
from pathlib import Path
import re
from urllib.parse import quote
from typing import Mapping

from .channels import grade_compact as policy
from ...common.records import numeric, text, value

SECTIONS = {"process": "过程数据", "result": "转化数据"}
DIMENSIONS = ("lead_id", "期次", "渠道", "经理", "年级", "分区日期", "分区小时")
COMMON = ("退前线索", "退后线索")
PROCESS = ("首call完成标记", "48h外呼标记", "5min标记", "好友标记", "深沟标记", "双沟标记")
RESULT = ("首节到课标记", "当期净收款", "净收款")
COLUMNS = {
    "process": (("期次", "期次", "text"), ("负责人", "负责人", "text"),
                ("退后线索", "退后线索", "count"), ("首call", "首call", "rate"),
                ("48h外呼", "48h外呼", "rate"), ("5min", "5min", "rate"),
                ("好友率", "好友率", "rate"), ("深沟率", "深沟率", "rate"), ("双沟率", "双沟率", "rate")),
    "result": (("期次", "期次", "text"), ("负责人", "负责人", "text"),
               ("退后线索", "退后线索", "count"), ("首节到课率", "首节到课率", "rate"),
               ("单效（当期）", "单效（当期）", "amount"), ("单效", "单效", "amount")),
}
WIDTHS = {"process": (240, 280, 200, 200, 200, 200, 200, 200, 200),
          "result": (280, 320, 260, 340, 360, 360)}
RATE_FIELDS = {"首call": "首call完成标记", "48h外呼": "48h外呼标记", "5min": "5min标记",
               "好友率": "好友标记", "深沟率": "深沟标记", "双沟率": "双沟标记", "首节到课率": "首节到课标记"}


def sections(report_type):
    if report_type not in {"process", "result", "both"}:
        raise ValueError("未知的播报类型")
    return ("process", "result") if report_type == "both" else (report_type,)


def projection(field_names, report_type):
    counters = list(COMMON)
    for section in sections(report_type):
        counters.extend(PROCESS if section == "process" else RESULT)
    required = list(DIMENSIONS) + counters
    missing = sorted(set(required) - set(field_names))
    if missing:
        raise ValueError("分年级播报缺少原始字段：" + "、".join(missing))
    return required, tuple(counters)


def validate_scope(records, channel, period):
    if not period:
        raise ValueError("分年级播报必须先确定本周业务期次")
    if not records:
        raise ValueError(f"{channel}在当期{period}没有数据；不回退到其他期次")
    seen = set()
    snapshots = set()
    for row in records:
        for field in DIMENSIONS:
            if not text(value(row, field)):
                raise ValueError("线索缺少必要字段：" + field)
        if text(value(row, "渠道")) != channel or text(value(row, "期次")) != period:
            raise ValueError("返回记录超出本次渠道或期次")
        key = (period, text(value(row, "lead_id")))
        if key in seen:
            raise ValueError("期次+lead_id重复，停止汇总")
        seen.add(key)
        snapshots.add((text(value(row, "分区日期")), text(value(row, "分区小时"))))
    if len(snapshots) != 1:
        raise ValueError("原始线索不是同一数据快照")
    return list(next(iter(snapshots)))


def _empty(counters):
    return {field: Decimal(0) for field in counters}


def _add(target, amounts):
    for field, amount in amounts.items():
        target[field] += amount


def _metrics(sums):
    den = sums["退后线索"]
    result = {field: float(amount) for field, amount in sums.items()}
    for display, numerator in RATE_FIELDS.items():
        if numerator in sums:
            result[display] = f"{sums[numerator] / den * 100:.8f}%" if den else "-"
    for display, numerator in (("单效（当期）", "当期净收款"), ("单效", "净收款")):
        if numerator in sums:
            result[display] = float(sums[numerator] / den) if den else "-"
    return result


def build_report(records, counters, period, report_type, *, excluded_grades=policy.EXCLUDED_GRADES,
                 min_post_leads=policy.MIN_POST_LEADS):
    by_grade = {}
    excluded = Counter()
    for row in records:
        grade = text(value(row, "年级"))
        if grade in excluded_grades:
            excluded[grade] += 1
            continue
        if not grade:
            raise ValueError("原始线索缺少年级")
        amounts = {field: numeric(value(row, field), field) for field in counters}
        if any(amounts[field] < 0 for field in counters if field not in ("当期净收款", "净收款")):
            raise ValueError("非金额线索指标出现负数")
        for field in (*PROCESS, "首节到课标记"):
            if field in amounts and amounts[field] not in (0, 1):
                raise ValueError("原始标记必须为0或1：" + field)
        manager = text(value(row, "经理"))
        group = by_grade.setdefault(grade, {"sums": _empty(counters), "managers": {}, "raw_count": 0})
        _add(group["sums"], amounts)
        _add(group["managers"].setdefault(manager, _empty(counters)), amounts)
        group["raw_count"] += 1
    blocks = []
    omitted = []
    for grade in sorted(by_grade, key=policy.grade_sort_key):
        group = by_grade[grade]
        if group["sums"]["退后线索"] < Decimal(min_post_leads):
            omitted.append({"grade": grade, "raw_count": group["raw_count"],
                            "post_leads": float(group["sums"]["退后线索"]), "reason": "post_leads_below_minimum"})
            continue
        rows = []
        hidden = 0
        for manager, sums in sorted(group["managers"].items()):
            if sums["退前线索"] == 0 and sums["退后线索"] == 0:
                hidden += 1
                continue
            rows.append({"fields": {**_metrics(sums), "期次": period, "年级": grade,
                                     "负责人": manager, "经理": manager},
                         "sums": {field: str(amount) for field, amount in sums.items()}})
        total = {"fields": {**_metrics(group["sums"]), "期次": "总计", "负责人": ""}}
        minima = {}
        manager_metrics = {}
        for section in sections(report_type):
            numerator = "5min标记" if section == "process" else "净收款"
            eligible = {name: Fraction(sums[numerator]) / Fraction(sums["退后线索"])
                        for name, sums in group["managers"].items() if sums["退后线索"] > 0}
            lowest = min(eligible.values()) if eligible else None
            names = sorted(name for name, ratio in eligible.items() if ratio == lowest)
            minima[section] = names
            manager_metrics[section] = {name: {"numerator": str(group["managers"][name][numerator]),
                                               "denominator": str(group["managers"][name]["退后线索"]),
                                               "value": float(ratio)} for name, ratio in sorted(eligible.items())}
        blocks.append({"grade": grade, "rows": rows, "total": total, "reminders": minima,
                       "manager_metrics": manager_metrics, "raw_count": group["raw_count"],
                       "hidden_zero_lead_rows": hidden})
    if not blocks:
        raise ValueError("排除初二及退后线索不足10的年级后，无可推送年级；本次不生成或发送消息")
    return {"blocks": blocks, "excluded_grade_counts": dict(excluded), "omitted_grades": omitted,
            "raw_count": len(records), "included_raw_count": sum(block["raw_count"] for block in blocks),
            "reminder_names": sorted({name for block in blocks for names in block["reminders"].values() for name in names}),
            "reminder_rule": "grade_manager_minimum_all_ties", "min_post_leads": min_post_leads}


def manager_queries(names):
    return {name: re.sub(r"\d+$", "", name) for name in names}


def resolve_manager_candidates(names, payload):
    """Exact display name + numeric email suffix; partial/ambiguous search fails closed."""
    queries = manager_queries(names)
    query_status = {item.get("query"): item for item in payload.get("queries", [])}
    info = {"names": list(names), "resolved": {}, "display_names": {}, "unresolved": [],
            "ambiguous": {}, "lookup_error": "", "nonmembers": []}
    for name, query in queries.items():
        status = query_status.get(query)
        if status is None or status.get("has_more") is not False or status.get("error"):
            info["unresolved"].append(name)
            continue
        suffix_match = re.search(r"(\d+)$", name)
        suffix = suffix_match.group(1) if suffix_match else None
        candidates = {}
        for person in payload.get("users", []):
            if person.get("matched_query") != query or not person.get("is_activated") or person.get("is_cross_tenant"):
                continue
            label = text(person.get("localized_name"))
            if label not in {name, query}:
                continue
            if suffix and label != name:
                prefix = text(person.get("enterprise_email")).split("@", 1)[0]
                email_suffix = re.search(r"(\d+)$", prefix)
                if not email_suffix or email_suffix.group(1) != suffix:
                    continue
            open_id = text(person.get("open_id"))
            if re.fullmatch(r"ou_[A-Za-z0-9]+", open_id):
                candidates[open_id] = label
        if len(candidates) == 1:
            open_id, label = next(iter(candidates.items()))
            info["resolved"][name] = open_id
            info["display_names"][name] = label
        else:
            info["unresolved"].append(name)
            if candidates:
                info["ambiguous"][name] = sorted(candidates)
    return info


def build_markdown(report, period, channel, report_type, mention_info, image_refs):
    lines = []
    for section in sections(report_type):
        if lines:
            lines.append("")
        lines.extend([f"## 🔥【{html.escape(channel)}】{SECTIONS[section]}", ""])
        if image_refs.get(section):
            lines.extend([f"![分年级{SECTIONS[section]}]({image_refs[section]})", ""])
        lines.append(f"- 推送期次：{period}")
        metric = "5min率" if section == "process" else "单效"
        for block in report["blocks"]:
            people = []
            for name in block["reminders"][section]:
                open_id = mention_info["resolved"].get(name)
                label = html.escape(mention_info.get("display_names", {}).get(name, name))
                people.append(f'<at user_id="{html.escape(open_id, quote=True)}">{label}</at>' if open_id else label)
            lines.append(f"- {html.escape(block['grade'])}年级{metric}较低：" + ("、".join(people) or "暂无有效负责人"))
    return "\n".join(lines)


def mention_ids(content):
    """Read both inline Markdown mentions and native post at/mentions nodes."""
    result = set()
    if isinstance(content, Mapping):
        if content.get("tag") == "at":
            result.add(str(content.get("user_id") or "__invalid_at__"))
        for item in content.get("mentions", []):
            if isinstance(item, Mapping):
                result.add(str(item.get("id") or item.get("user_id") or "__invalid_at__"))
        for key, item in content.items():
            if key != "mentions":
                result.update(mention_ids(item))
    elif isinstance(content, (list, tuple)):
        for item in content:
            result.update(mention_ids(item))
    elif isinstance(content, str):
        try:
            decoded = json.loads(content)
        except (TypeError, ValueError):
            decoded = None
        if isinstance(decoded, (dict, list)):
            result.update(mention_ids(decoded))
        normalized = html.unescape(content).replace('\\"', '"')
        tags = re.findall(r"<at\b[^>]*>", normalized, re.I)
        for tag in tags:
            match = re.search(r'''\buser_id\s*=\s*["']([^"']+)["']''', tag)
            result.add(match.group(1) if match else "__invalid_at__")
        if re.search(r"<mention\b", normalized, re.I):
            result.add("__invalid_at__")
    return result


def sorted_rows(block, section):
    numerator = "5min标记" if section == "process" else "净收款"
    def key(row):
        sums = row["sums"]
        den = Fraction(sums["退后线索"])
        ratio = Fraction(sums[numerator]) / den if den else None
        return (ratio is None, -ratio if ratio is not None else Fraction(0),
                row["fields"]["负责人"])
    return sorted(block["rows"], key=key)


def render_image(report, section, output_path, *, font_loader, center_text, format_value,
                 bar_colors=None, cell_fill=None):
    from PIL import Image, ImageDraw
    columns, widths = COLUMNS[section], WIDTHS[section]
    width = sum(widths)
    band_h, header_h, row_h, total_h, gap = 52, 64, 54, 58, 24
    heights = [band_h + header_h + len(block["rows"]) * row_h + total_h for block in report["blocks"]]
    image = Image.new("RGB", (width, sum(heights) + gap * (len(heights) - 1)), "#ffffff")
    draw = ImageDraw.Draw(image)
    bar_colors = bar_colors or {"首call": "#4f78ae", "5min": "#f5ae23", "双沟率": "#138de2"}
    navy, grid = "#203b72", "#b8c4d3"
    xs = [0]
    for size in widths:
        xs.append(xs[-1] + size)
    top = 0
    geometry = []
    try:
        for block, height in zip(report["blocks"], heights):
            geometry.append({"grade": block["grade"], "top": top, "height": height, "rows": len(block["rows"])})
            draw.rectangle((0, top, width, top + band_h), fill="#e8eef8")
            draw.text((18, top + 9), block["grade"] + "年级", font=font_loader(27, True), fill=navy)
            header = top + band_h
            draw.rectangle((0, header, width, header + header_h), fill=navy)
            for (_source, label, _kind), left, right in zip(columns, xs, xs[1:]):
                center_text(draw, (left + 4, header, right - 4, header + header_h), label, font_loader(25, True), "#ffffff")
            ordered = sorted_rows(block, section)
            for index, row in enumerate([*ordered, block["total"]]):
                y = header + header_h + index * row_h
                total = index == len(ordered)
                bottom = y + (total_h if total else row_h)
                draw.rectangle((0, y, width, bottom), fill=navy if total else "#ffffff")
                for (source, _label, kind), left, right in zip(columns, xs, xs[1:]):
                    cell = row["fields"].get(source, "")
                    if not total and section == "result" and cell_fill is not None:
                        draw.rectangle((left, y, right, bottom), fill=cell_fill(source, cell))
                    if not total and source in {"首call", "5min", "双沟率"} and isinstance(cell, str) and cell.endswith("%"):
                        ratio = max(0, min(1, float(cell[:-1]) / 100))
                        color = bar_colors[source]
                        if ratio:
                            draw.rectangle((left + 5, y + 8, left + 5 + int((right - left - 10) * ratio), bottom - 8), fill=color)
                    draw.rectangle((left, y, right, bottom), outline=grid, width=1)
                    rendered = f"{float(cell):.2f}" if kind == "amount" and isinstance(cell, (int, float, Decimal)) else format_value(cell, kind)
                    center_text(draw, (left + 4, y, right - 4, bottom), rendered, font_loader(25, total), "#ffffff" if total else "#111827")
            top += height + gap
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path, format="PNG", optimize=True)
    finally:
        image.close()
    return geometry


def write_preview(context, directory):
    """Local-only HTML/Markdown/metadata handoff; never embeds remote media."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    report = context["grade_report"]
    info = context["mention_info"]
    cards = []
    markdown = context["markdown"]
    image_files = {}
    for section in sections(context["report_type"]):
        path = context.get("image_path" if section == "process" else "result_image_path")
        picture = ""
        if path:
            path = Path(path)
            image_files[section] = str(path)
            local = quote(os.path.relpath(path, directory).replace(os.sep, "/"))
            escaped_local = html.escape(local, quote=True)
            picture = f'<a href="{escaped_local}" target="_blank" title="查看原图"><img class="table-image" src="{escaped_local}" alt="分年级{SECTIONS[section]}"></a>'
            markdown = markdown.replace(f"](img_{section}_preview)", f"]({path.as_posix()})")
        metric = "5min率" if section == "process" else "单效"
        lines = [f"<li>推送期次：{html.escape(context['period'])}</li>"]
        for block in report["blocks"]:
            people = []
            for name in block["reminders"][section]:
                label = html.escape(info.get("display_names", {}).get(name, name))
                if name in info["resolved"]:
                    people.append(f'<span class="mention">@{label}</span>')
                else:
                    people.append(f'<span class="unresolved">{label}（待核验）</span>')
            lines.append(f"<li>{html.escape(block['grade'])}年级{metric}较低：" + ("、".join(people) or "暂无有效负责人") + "</li>")
        cards.append(f'<section class="section"><h2>🔥【{html.escape(context["channel"])}】{SECTIONS[section]}</h2>{picture}<ul>{"".join(lines)}</ul></section>')
    today = "仅过程数据" if context["scheduled_report_type_today"] == "process" else "过程＋转化数据"
    dt, hour = context["snapshot"]
    document = '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>飞书群消息预览</title><style>'
    document += 'body{margin:0;background:#f4f6fa;color:#1f2329;font:16px/1.6 "Microsoft YaHei",sans-serif}.wrap{max-width:1180px;margin:28px auto;padding:0 20px}.note{background:#eaf1ff;color:#244c87;border-radius:12px;padding:16px 20px;margin-bottom:20px}.chat{display:flex;gap:14px}.avatar{background:#3370ff;color:white;border-radius:12px;width:44px;height:44px;display:grid;place-items:center;flex:none;font-weight:700}.bubble{background:white;border:1px solid #e3e7ef;border-radius:14px;padding:22px;min-width:0;flex:1}.sender{color:#646a73;font-size:14px;margin-bottom:10px}h1{font-size:22px}h2{font-size:21px;line-height:1.5;margin:0 0 16px}.table-image{display:block;width:100%;height:auto;border:1px solid #e3e7ef}ul{padding-left:24px;margin:16px 0 0}li{margin:5px 0}.mention{color:#3370ff;background:#eff4ff;border-radius:4px;padding:1px 4px}.unresolved{color:#bd5b00}.section+.section{border-top:1px solid #e5e8ee;margin-top:28px;padding-top:24px}small{color:#646a73}</style>'
    document += f'<body><main class="wrap"><h1>{html.escape(context["chat_name"])}</h1><div class="note">仅本地预览：没有发送消息，也不会触发@通知。<br>今日定时规则：{today}。若下方含转化样式，仍只会在周五至周日随定时消息发送。<br><small>数据分区：{dt[:4]}-{dt[4:6]}-{dt[6:8]} {int(hour):02d}:00（北京时间）｜群ID：{html.escape(context["chat_id"])}</small></div><div class="chat"><div class="avatar">管</div><div class="bubble"><div class="sender">管家 · 消息样式预览</div>{"".join(cards)}</div></div></main></body></html>'
    html_path = directory / "message-preview.html"
    markdown_path = directory / "message-preview.md"
    metadata_path = directory / "preview-metadata.json"
    html_path.write_text(document, encoding="utf-8")
    markdown_path.write_text(markdown + "\n", encoding="utf-8")
    metadata = {key: context[key] for key in ("report_profile", "period", "report_type", "channel", "chat_id", "chat_name", "identity", "raw_count", "raw_read_audit", "snapshot", "scheduled_report_type_today", "mention_info", "image_geometry")}
    metadata.update({"mode": "preview_only", "message_sent": False, "image_files": image_files, "report": report})
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"html": str(html_path), "markdown": str(markdown_path), "metadata": str(metadata_path)}
