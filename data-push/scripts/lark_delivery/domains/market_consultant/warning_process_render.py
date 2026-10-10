"""Reusable local PNG/message renderer. Accepts aggregated data; never sends."""
from __future__ import annotations

import argparse
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from functools import lru_cache
import hashlib
import html
import json
from pathlib import Path
import re
import sys

from PIL import Image, ImageDraw, ImageFont

# Header and total-row fills: blend the original colors with 40% white.
NAVY, TEAL, PURPLE = "#798aa9", "#7dacb0", "#a493b7"
GREEN, RED, GRAY = "#177d58", "#c64743", "#68758b"
METRICS = (("first_call", "首call率", NAVY, "📞"),
           ("five_min", "5min率", TEAL, "☎️"),
           ("frequency", "外呼频次", PURPLE, "🔁"))
WIDTHS = (214,) + (180, 206, 206) * len(METRICS)
WEEKDAYS = ("周一", "周二", "周三", "周四", "周五", "周六", "周日")
CHAT_ID = "oc_6f06cad338d520a89e1607a18592e56b"


def fixed(value):
    return format(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), ".2f")


def percentage(value, signed=False):
    if value is None:
        return "—"
    value = Decimal(str(value))
    return ("+" if signed and value > 0 else "") + fixed(value * 100) + "%"


def change_text(value):
    if value is None:
        return "不可计算"
    value = Decimal(str(value))
    return "持平" if value == 0 else ("增加" if value > 0 else "减少") + percentage(abs(value))


def metric_text(value, key, five_min=False):
    if value is None:
        return "—"
    return fixed(value) if key == "frequency" else percentage(value)


def unavailable_reason(row, key):
    if row["now"][key] is None:
        return "无退后线索"
    if row["prior"][key] is None:
        return "上期无退后线索"
    return "上期为0" if Decimal(str(row["prior"][key])) == 0 else "上期为负"


def select_display_rows(rows):
    """Filter supervisor display only; team metrics keep the complete scope."""
    displayed, excluded = [], []
    rules = [("now_sums", "退后线索", "本期无退后线索"),
             ("prior_sums", "退后线索", "上期无退后线索")]
    for row in rows:
        reasons = []
        for period, field, reason in rules:
            value = row[period][field]
            if value is None or not Decimal(str(value)).is_finite():
                raise ValueError(f"Missing/invalid display filter metric: {row['supervisor']} {period} {field}")
            if Decimal(str(value)) <= 0:
                reasons.append(reason)
        if reasons:
            excluded.append({"supervisor": row["supervisor"], "reasons": reasons})
        else:
            displayed.append(row)
    displayed.sort(key=lambda row: (row["now"]["five_min"] is None,
                                    -Decimal(str(row["now"]["five_min"])) if row["now"]["five_min"] is not None else Decimal(0),
                                    row["supervisor"]))
    return displayed, excluded


def build_reminder(data, mention_info):
    """Use the complete current population, distinct from the image filter."""
    team_five_min = data["team"]["now"]["five_min"]
    if team_five_min is None:
        raise ValueError("Team five_min efficiency is missing")
    names = [row["supervisor"] for row in data["rows"] if row["now"]["five_min"] is not None
             and Decimal(str(row["now"]["five_min"])) > Decimal(str(team_five_min))]
    if (mention_info.get("chat_id") != data.get("target_chat_id", CHAT_ID)
            or mention_info.get("member_read_complete") is not True
            or mention_info.get("current_snapshot") != data["current_snapshot"]
            or mention_info.get("source_table_id") != data["source_table_id"]
            or mention_info.get("source_rev") != data["source_rev"]
            or mention_info.get("target_names") != names):
        raise ValueError("Mention evidence does not match the group, source, snapshot or targets")
    entries, md_mentions, html_mentions, nodes = [], [], [], []
    for name in names:
        person = mention_info["resolved"].get(name)
        if not person or not person.get("in_chat") or not re.fullmatch(r"ou_[A-Za-z0-9]+", person.get("open_id", "")):
            raise ValueError(f"Mention target is not verified: {name}")
        label, user_id = html.escape(person["display_name"]), person["open_id"]
        account = person.get("account_label", "")
        if account and not re.fullmatch(r"[A-Za-z0-9._-]+", account):
            raise ValueError(f"Invalid account display label: {name}")
        account_suffix = f"（{account}）" if account else ""
        md_mentions.append(f'<at user_id="{user_id}">{label}</at>{account_suffix}')
        html_mentions.append(f'<span class="mention" data-user-id="{user_id}">@{label}{account_suffix}</span>')
        entries.append({"supervisor": name, "display_name": person["display_name"], "open_id": user_id,
                        "account_label": account})
        if nodes:
            nodes.append({"tag": "text", "text": " "})
        nodes.append({"tag": "at", "user_id": user_id})
        if account_suffix:
            nodes.append({"tag": "text", "text": account_suffix})
    if len({entry["open_id"] for entry in entries}) != len(entries):
        raise ValueError("Duplicate user IDs in mention targets")
    snapshot = data["current_snapshot"]
    prefix = f"截至dt={snapshot['dt']}，hour={snapshot['hour']}时，"
    suffix = "的5min率"
    if names:
        md_line = prefix + "\n" + " ".join(md_mentions) + suffix + "**【比团队整体高】** 🌟👏"
        html_line = html.escape(prefix) + "<br>" + " ".join(html_mentions) + suffix + '<strong class="highlight-good">【比团队整体高】</strong> 🌟👏'
        post_lines = [[{"tag": "text", "text": prefix}],
                      [*nodes, {"tag": "text", "text": suffix},
                       {"tag": "text", "text": "【比团队整体高】", "style": ["bold"]},
                       {"tag": "text", "text": " 🌟👏"}]]
    else:
        md_line = prefix + "\n暂无主管的5min率高于团队整体。"
        html_line = html.escape(md_line).replace("\n", "<br>")
        post_lines = [[{"tag": "text", "text": prefix}],
                      [{"tag": "text", "text": "暂无主管的5min率高于团队整体。"}]]
    post_line = [*post_lines[0], {"tag": "text", "text": "\n"}, *post_lines[1]]
    return {"markdown": md_line, "html": html_line, "post_line": post_line, "post_lines": post_lines, "targets": entries,
            "chat_id": mention_info["chat_id"], "selection": "all_current_supervisors_5min_above_full_channel_team"}


@lru_cache(maxsize=80)
def font(size, bold=False):
    return ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc", size)


def centered(draw, box, text, size=25, ink="#26354a", bold=False):
    x0, y0, x1, y1 = box
    while True:
        face = font(size, bold)
        bounds = draw.multiline_textbbox((0, 0), text, font=face, spacing=4, align="center")
        if bounds[2] - bounds[0] <= x1 - x0 - 12 or size <= 16:
            break
        size -= 1
    if bounds[2] - bounds[0] > x1 - x0 - 8 or bounds[3] - bounds[1] > y1 - y0 - 6:
        raise ValueError(f"Text does not fit cell: {text}")
    draw.multiline_text(((x0 + x1 - bounds[2] - bounds[0]) / 2,
                        (y0 + y1 - bounds[3] - bounds[1]) / 2),
                       text, font=face, fill=ink, spacing=4, align="center")


def draw_image(data, path):
    team, rows = data["team"], data["rows"]
    edges = [28]
    for width in WIDTHS:
        edges.append(edges[-1] + width)
    width, top, group_h, lower_h, row_h = edges[-1] + 28, 28, 44, 52, 70
    header_bottom = top + group_h + lower_h
    bottom = header_bottom + row_h * (len(rows) + 1)
    canvas = Image.new("RGB", (width, bottom + 28), "white")
    draw = ImageDraw.Draw(canvas)
    # Each metric spans three columns; the image contains no unit labels.
    draw.rectangle((edges[0], top, edges[1], header_bottom), fill=NAVY)
    centered(draw, (edges[0], top, edges[1], header_bottom), "主管", 25, "white", True)
    for mi, (key, label, color, icon) in enumerate(METRICS):
        start, end = 1 + 3 * mi, 4 + 3 * mi
        draw.rectangle((edges[start], top, edges[end], header_bottom), fill=color)
        centered(draw, (edges[start], top, edges[end], top + group_h), label, 26, "white", True)
    labels = [label for _, title, _, _ in METRICS for label in (title, "较上期环比", "较团队整体")]
    for ci, label in enumerate(labels, 1):
        centered(draw, (edges[ci], top + group_h, edges[ci + 1], header_bottom), label, 23, "white", True)
    for ri, row in enumerate(rows + [team]):
        total = ri == len(rows)
        y = header_bottom + ri * row_h
        values = [row["supervisor"]]
        delta_keys = {}
        for mi, (key, label, color, icon) in enumerate(METRICS):
            values.extend([metric_text(row["now"][key], key), percentage(row[key+"_mom"], True),
                           "基准" if total else percentage(row[key+"_team"], True)])
            delta_keys[2+3*mi], delta_keys[3+3*mi] = key+"_mom", key+"_team"
        if not total:
            for mi, (key, label, color, icon) in enumerate(METRICS):
                ci = 2 + 3 * mi
                if row[key + "_mom"] is None:
                    values[ci] = "—\n" + unavailable_reason(row, key)
        for ci, text in enumerate(values):
            band_color = NAVY if ci == 0 else METRICS[(ci-1)//3][2]
            background = band_color if total else ("#f7f9fc" if ri % 2 else "white")
            ink, size = ("white" if total else "#26354a"), 25
            if not total and ci in delta_keys:
                delta = row[delta_keys[ci]]
                if delta is None:
                    background, ink, size = "#f0f2f5", GRAY, 19 if "\n" in text else 25
                elif Decimal(str(delta)) != 0:
                    good = Decimal(str(delta)) > 0
                    background, ink = ("#e8f5ed", GREEN) if good else ("#fff0ee", RED)
            draw.rectangle((edges[ci], y, edges[ci + 1], y + row_h), fill=background)
            centered(draw, (edges[ci], y, edges[ci + 1], y + row_h), text, size, ink, total)
        draw.line((edges[0], y + row_h, edges[-1], y + row_h), fill="#d6dfe9")
    for ci, edge in enumerate(edges):
        start_y = top if ci == 0 or (ci - 1) % 3 == 0 else top + group_h
        draw.line((edge, start_y, edge, bottom), fill="#d6dfe9")
    draw.line((edges[1], top + group_h, edges[-1], top + group_h), fill="#d6dfe9")
    canvas.save(path)
    return canvas.size


def render_preview(data, output_dir, mention_info):
    """Render from a computed_metrics payload; dates and counts come from data."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    reminder = build_reminder(data, mention_info)
    png = output_dir / "channel-process-preview.png"
    displayed, excluded = select_display_rows(data["rows"])
    dimensions = draw_image({**data, "rows": displayed}, png)
    date = datetime.strptime(data["current_snapshot"]["dt"], "%Y%m%d")
    weekday = WEEKDAYS[date.weekday()]
    team = data["team"]
    heading = f"今日{data['channel']}渠道过程数据概览（{date.month}月{date.day}日）"
    heading_md = f"📊 今日<span style=\"color:{RED}\">**{html.escape(data['channel'])}**</span>渠道过程数据概览（{date.month}月{date.day}日）"
    heading_html = f'📊 今日<strong class="channel-name">{html.escape(data["channel"])}</strong>渠道过程数据概览（{date.month}月{date.day}日）'
    def decorated_line(line, change, key, as_html=False):
        if change is None:
            return line
        delta = Decimal(str(change))
        icon = "⬆️" if delta > 0 else "⬇️" if delta < 0 else "↔️"
        good = delta > 0
        color = GREEN if good else RED if delta else GRAY
        phrase = f"较上{weekday}{change_text(change)}"
        opening = f'<strong style="color:{color}">' if as_html else f'<span style="color:{color}">**'
        closing = "</strong>" if as_html else "**</span>"
        return line.replace(phrase, opening + phrase + " " + icon + closing)
    md_lines, html_lines = [], []
    for mi, (key, label, color, icon) in enumerate(METRICS):
        value, prior = metric_text(team['now'][key], key), metric_text(team['prior'][key], key)
        # Units are absent from the picture; the message uses the confirmed frequency unit.
        unit = "次/条" if key == "frequency" else ""
        stop = "。" if mi == len(METRICS)-1 else "；"
        line = f"{icon} {label} **{value}{unit}**，较上{weekday}{change_text(team[key+'_mom'])}（{prior}{unit}）{stop}"
        md_lines.append(decorated_line(line, team[key+'_mom'], key))
        html_line = line.replace(f"**{value}{unit}**", f"<b>{value}{unit}</b>")
        html_lines.append(decorated_line(html_line, team[key+'_mom'], key, True))
    closing_md = "继续加油，**【祝本期爆单】** 🚀🔥"
    message = heading_md+"\n\n"+"\n".join(md_lines)+f"\n\n![渠道主管过程对比]({png.name})\n\n{reminder['markdown']}\n{closing_md}\n"
    (output_dir / "message-preview.md").write_text(message, encoding="utf-8")
    metrics_html = "<br>".join(html_lines)
    # Only the message content belongs in the bubble. Source/audit stay in JSON.
    document = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(heading)} · 本地预览</title>
<style>body{{margin:0;background:#f1f5fa;color:#243246;font:16px/1.8 'Microsoft YaHei',sans-serif}}main{{max-width:1520px;margin:24px auto;padding:0 20px}}.status{{background:#edf6f1;color:#266445;padding:12px 18px;border-radius:10px;margin-bottom:18px}}.chat{{display:flex;gap:14px}}.avatar{{width:44px;height:44px;flex:none;display:grid;place-items:center;background:#3370ff;color:white;border-radius:10px;font-weight:bold}}article{{padding:22px 26px;border:1px solid #dbe3ee;border-radius:12px;background:white;flex:1;min-width:0}}.sender{{color:#6f7d91;font-size:14px}}h1{{font-size:23px;line-height:1.5;margin:8px 0 16px}}.metric{{font-size:18px;margin:8px 0}}img{{display:block;width:100%;height:auto;margin:20px 0;border:1px solid #e2e8f0}}.closing{{font-size:19px;font-weight:600;margin:12px 0 0}}@media(max-width:600px){{main{{padding:0 9px}}.chat{{gap:8px}}.avatar{{width:32px;height:32px}}article{{padding:14px 12px}}h1{{font-size:19px}}.metric{{font-size:16px}}}}</style></head>
<body><main><div class="status">本地消息预览 · 尚未发送</div><div class="chat"><div class="avatar">管</div><article><div class="sender">管家 · 消息样式预览</div><h1>{heading_html}</h1>
<p class="metric">{metrics_html}</p><a href="{png.name}" target="_blank"><img src="{png.name}" alt="主管首call率、5min率和外呼频次过程对比"></a><p class="reminder">{reminder['html']}<br>继续加油，<strong class="highlight-cheer">【祝本期爆单】</strong> 🚀🔥</p></article></div></main></body></html>"""
    document = document.replace("</style>", ".channel-name{color:#c64743}.mention{color:#3370ff;background:#edf3ff;padding:1px 4px;border-radius:3px;white-space:nowrap}.reminder{font-size:17px;line-height:1.9;margin:16px 0}.highlight-good{color:#177d58;background:#e8f5ed;padding:1px 3px;border-radius:3px}.highlight-cheer{color:#c76b08;background:#fff3dd;padding:1px 3px;border-radius:3px}</style>")
    (output_dir / "message-preview.html").write_text(document, encoding="utf-8")
    (output_dir / "reminder-preview.json").write_text(json.dumps({"local_only": True, "message_sent": False,
        "chat_id": reminder["chat_id"], "current_snapshot": data["current_snapshot"],
        "post_line": reminder["post_line"], "post_lines": reminder["post_lines"],
        "targets": reminder["targets"], "selection": reminder["selection"]},
        ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    receipt = {"local_only": True, "message_sent": False, "renderer": "render_preview.py", "layout_version": 11,
               "sorting": "current_five_min_descending_unavailable_last_supervisor_name_tiebreak",
               "metric_display_order": [key for key, _, _, _ in METRICS],
               "image_has_unit_labels": False,
               "image_band_colors": {"blue": NAVY, "green": TEAL, "purple": PURPLE,
                                     "original_blue": "#203c70", "original_green": "#26757b",
                                     "white_blend": 0.4},
               "message_style": "red_channel_bold_highlights_icons_three_line_reminder",
               "color_rendering_surface": "local_html", "remote_color_rendering_verified": False,
               "source_table_id": data["source_table_id"], "source_rev": data["source_rev"],
               "current_snapshot": data["current_snapshot"], "prior_snapshot": data["prior_snapshot"],
               "supervisors": len(displayed), "source_supervisors": len(data["rows"]),
               "displayed_supervisors": [row["supervisor"] for row in displayed],
               "excluded_supervisors": excluded,
               "display_filter": "两期退后线索均大于0；仅影响主管展示，团队指标保持全量口径",
               "mention_targets": reminder["targets"], "mention_selection": reminder["selection"],
               "mention_membership_verified": True, "target_chat_id": reminder["chat_id"],
               "image_dimensions": dimensions,
               "image_sha256": hashlib.sha256(png.read_bytes()).hexdigest(), "generated_at": datetime.now().isoformat(timespec="seconds")}
    (output_dir / "preview_receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return receipt


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--mentions", type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.data.read_text(encoding="utf-8"))
    mention_info = json.loads(args.mentions.read_text(encoding="utf-8"))
    print(json.dumps(render_preview(data, args.output_dir, mention_info), ensure_ascii=False))


if __name__ == "__main__":
    main()
