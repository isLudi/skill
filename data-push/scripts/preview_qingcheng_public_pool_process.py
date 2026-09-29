"""Build local-only public-pool process previews from a Qingcheng Base export.

The input is an NDJSON artifact made by lark-cli. This script performs no
network calls, registration, upload, scheduling, or message sending.
"""

from __future__ import annotations

import argparse
import html
import json
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


NAVY = "#3d8b4f"
GRID = "#aecfb2"
BAND = "#dcebdd"
BAND_TEXT = "#111827"
PAPER = "#ffffff"
FONT_PATH = "C:/Windows/Fonts/msyh.ttc"
DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "config" / "departments" / "qingcheng" / "public_pool_process_preview.json"

# Fixed scales shared by preview and the reviewed public-pool process report.
SCALES = {
    "好友率": (0.0, 1.0),
    "等待时长": (0.0, 48.0),
    "8min": (0.0, 1.0),
    "24h首call": (0.0, 1.0),
}
BAR_COLORS = {
    "好友率": "#4f78ae",
    "等待时长": "#fb626b",
    "8min": "#f5ae23",
    "24h首call": "#2e9e6b",
}
PROCESS_TIE_HANDLING = "all_tied_minimum"


def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = "C:/Windows/Fonts/msyhbd.ttc" if bold else FONT_PATH
    return ImageFont.truetype(path, size)


def _number(row: dict, field: str) -> float:
    value = row.get(field)
    if value is None:
        raise ValueError(f"Missing numeric source field: {field}")
    return float(value)


def _ratio(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator else None


def _read_snapshot(path: Path, config: dict | None = None) -> tuple[list[dict], dict]:
    manifest = json.loads(path.with_suffix(".manifest.json").read_text(encoding="utf-8"))
    if manifest.get("has_more") is not False or manifest.get("records_count") is None:
        raise ValueError("Base export is incomplete")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    if len(rows) != manifest["records_count"]:
        raise ValueError("Base export count differs from manifest")
    if len({r.get("record_id") for r in rows}) != len(rows):
        raise ValueError("Duplicate or missing Base record IDs")
    if len({r.get("记录键") for r in rows}) != len(rows):
        raise ValueError("Duplicate or missing business keys")
    match = (config or {"source": {"match": {"一级渠道": "公海", "渠道": "顾问未加好友"}}})["source"]["match"]
    if not rows or any({field: row.get(field) for field in match} != match for row in rows):
        raise ValueError("Export contains rows outside the configured Qingcheng channel")
    if len({(r.get("分区日期"), r.get("分区小时")) for r in rows}) != 1:
        raise ValueError("Source rows span multiple warehouse snapshots")
    if len({r.get("期次") for r in rows}) != 1:
        raise ValueError("Preview must use one business period")
    return rows, manifest


def _aggregate(rows: list[dict], level: str, request: dict, *, split_grade: bool = False,
               lead_field: str = "退后线索") -> list[dict]:
    business = request["business"]
    allowed_grades = set(business["grades"])
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for row in rows:
        if row["年级"] not in allowed_grades:
            continue
        if level == "主管":
            key = (row["期次"], row["主管"], row["年级"]) if split_grade else (row["期次"], row["主管"])
        else:
            key = (row["期次"], row["主管"], row["顾问账号"], row["年级"])
        groups[key].append(row)

    minimum = float(request["report"]["minimum"]["value"])
    show_retention = "线索留存率" in request["report"].get("process_metrics", [])
    show_before_leads = show_retention or "退前线索" in request["report"].get("process_metrics", [])
    output = []
    for key, items in groups.items():
        leads = sum(_number(item, lead_field) for item in items)
        if leads < minimum:
            continue
        if level == "顾问" and len({item["顾问"] for item in items}) != 1:
            raise ValueError(f"One consultant account has conflicting names: {key}")
        metrics = {
            "有效线索": leads,
            "好友率": _ratio(sum(_number(item, "好友标记") for item in items), leads),
            "等待时长": _ratio(sum(_number(item, "首call等待时长小时") for item in items), leads),
            "8min": _ratio(sum(_number(item, "8min标记") for item in items), leads),
            "24h首call": _ratio(sum(_number(item, "24h首call标记") for item in items), leads),
            "沟通率": _ratio(sum(_number(item, "沟通标记") for item in items), leads),
            "外呼时长": _ratio(sum(_number(item, "总通时秒") for item in items) / 60, leads),
            "外呼频次": _ratio(sum(_number(item, "外呼次数") for item in items), leads),
            "总通时": sum(_number(item, "总通时秒") for item in items) / 60,
            "带班人数": len({item["顾问账号"] for item in items}),
        }
        if show_before_leads:
            before_leads = sum(_number(item, "退前线索") for item in items)
            metrics["退前线索"] = before_leads
            if show_retention:
                metrics["线索留存率"] = _ratio(leads, before_leads)
        output.append({
            "key": key,
            "主管": key[1],
            "顾问": items[0]["顾问"] if level == "顾问" else None,
            "顾问账号": key[2] if level == "顾问" else None,
            "年级": key[3] if level == "顾问" else key[2] if split_grade else None,
            "metrics": metrics,
            "_accounts": frozenset(item["顾问账号"] for item in items),
        })
    return sorted(output, key=lambda item: (item["主管"], item["顾问账号"] or "", item["年级"] or ""))


def _sort_process_rows(rows: list[dict], *, split_grade: bool = False) -> list[dict]:
    """Show the configured focus metric before rounding, highest first."""
    grade_order = {name: index for index, name in enumerate(("高一", "高二", "高三", "初三"))}
    return sorted(rows, key=lambda item: (grade_order.get(item["年级"], 99) if split_grade else 0, -item["metrics"]["8min"], item["主管"], item["顾问账号"] or "", item["年级"] or ""))


def _display(value: float | None, field: str, *, integer_fields: frozenset[str] = frozenset()) -> str:
    if value is None:
        return "—"
    if field in {"好友率", "8min", "24h首call", "沟通率", "线索留存率"}:
        return f"{value:.1%}"
    if field in {"总通时", "有效线索", "带班人数", "退前线索", "退后线索"} | integer_fields:
        return f"{value:,.0f}"
    return f"{value:,.1f}"


def _total_row(rows: list[dict]) -> dict:
    """Recalculate ratios from displayed detail, including distinct headcount."""
    leads = sum(row["metrics"]["有效线索"] for row in rows)
    if not leads:
        raise ValueError("Cannot total an empty report block")
    ratio_fields = ("好友率", "等待时长", "8min", "24h首call", "沟通率", "外呼时长", "外呼频次")
    metrics = {field: sum(row["metrics"][field] * row["metrics"]["有效线索"] for row in rows) / leads for field in ratio_fields}
    metrics.update({
        "有效线索": leads,
        "总通时": sum(row["metrics"]["总通时"] for row in rows),
        "带班人数": len(set().union(*(row["_accounts"] for row in rows))),
    })
    if "退前线索" in rows[0]["metrics"]:
        before_leads = sum(row["metrics"]["退前线索"] for row in rows)
        metrics["退前线索"] = before_leads
        if "线索留存率" in rows[0]["metrics"]:
            metrics["线索留存率"] = _ratio(leads, before_leads)
    return {"is_total": True, "metrics": metrics}


def _band_label(channel: str, level: str, period: str) -> str:
    return f"{channel}-{level}-{period}"


def _table_image(rows: list[dict], columns: list[str], path: Path, level: str, period: str, channel: str = "公海", *,
                 split_grade: bool = False, bar_specs: dict[str, tuple[float, float, str]] | None = None,
                 integer_fields: frozenset[str] = frozenset()) -> None:
    if bar_specs is None:
        bar_specs = {field: (*scale, BAR_COLORS[field]) for field, scale in SCALES.items()}
    identity = {"期次", "主管", "顾问", "负责人", "年级"}
    widths = [136 if c == "期次" else 132 if c in identity else 145 for c in columns]
    width = sum(widths)
    band_h, header_h, row_h, gap = 50, 62, 56, 18
    grades = list(dict.fromkeys(row["年级"] for row in rows)) if split_grade else [None]
    blocks = [(grade, [row for row in rows if row["年级"] == grade]) for grade in grades] if split_grade else [(None, rows)]
    height = sum(band_h + header_h + (len(block_rows) + 1) * row_h for _, block_rows in blocks) + gap * max(0, len(blocks) - 1)
    im = Image.new("RGB", (width, height), PAPER)
    d = ImageDraw.Draw(im)
    top = 0
    for grade, block_rows in blocks:
        if not block_rows:
            raise ValueError("No eligible rows in report block")
        d.rectangle((0, top, width, top + band_h), fill=BAND)
        band = _band_label(channel, level, period) + (f"｜{grade}" if grade else "")
        d.text((16, top + 9), band, font=_font(23, bold=True), fill=BAND_TEXT)
        header = top + band_h
        x = 0
        for col, col_width in zip(columns, widths):
            d.rectangle((x, header, x + col_width, header + header_h), fill=NAVY, outline=GRID)
            _center_text(d, (x, header, x + col_width, header + header_h), col, _font(19, bold=True), PAPER)
            x += col_width
        for index, row in enumerate([*block_rows, _total_row(block_rows)]):
            y = header + header_h + index * row_h
            is_total = row.get("is_total", False)
            x = 0
            for col, col_width in zip(columns, widths):
                d.rectangle((x, y, x + col_width, y + row_h), fill=NAVY if is_total else PAPER, outline=GRID)
                if is_total and col in identity:
                    label = "总计" if col == "期次" else ""
                elif col in identity:
                    value = row["key"][0] if col == "期次" else row[col]
                    label = str(value)
                else:
                    raw = row["metrics"].get(col)
                    label = _display(raw, col, integer_fields=integer_fields)
                    if not is_total and col in bar_specs and raw is not None:
                        lo, hi, color = bar_specs[col]
                        fraction = max(0.0, min(1.0, (raw - lo) / (hi - lo)))
                        if fraction:
                            d.rectangle((x + 5, y + 7, x + 5 + int((col_width - 10) * fraction), y + row_h - 7), fill=color)
                d.rectangle((x, y, x + col_width, y + row_h), outline=GRID)
                _center_text(d, (x, y, x + col_width, y + row_h), label, _font(18, bold=is_total), PAPER if is_total else "#111827")
                x += col_width
        top = header + header_h + (len(block_rows) + 1) * row_h + gap
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path)


def _center_text(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], label: str, font: ImageFont.FreeTypeFont, fill: str) -> None:
    left, top, right, bottom = box
    extent = draw.textbbox((0, 0), label, font=font)
    text_width, text_height = extent[2] - extent[0], extent[3] - extent[1]
    draw.text((left + (right - left - text_width) / 2 - extent[0], top + (bottom - top - text_height) / 2 - extent[1]), label, font=font, fill=fill)


def _message(level: str, period: str, rows: list[dict], request: dict, image_name: str, channel: str = "公海") -> str:
    reminder = request["reminder"]
    if (reminder["report_level"], reminder["target"], reminder["process_metric"], reminder["process_direction"], reminder["process_rank"]) != (level, level, "8min", "最低", "最后1名"):
        raise ValueError("Process reminder does not match the reviewed Base request")
    if not rows:
        raise ValueError("Cannot write a reminder without eligible detail rows")
    if channel == "私域":
        reminders = [f"- {grade}年级8min较低的{level}：{'、'.join(person['name'] for person in people)}"
                     for grade, people in _reminder_by_grade(level, rows).items()]
    else:
        names = [person["name"] for person in _reminder_people(level, rows)]
        reminders = [f"- 8min较低的{level}：{'、'.join(names)}"]
    return "\n".join([
        f"## 🔥 **【{period}】{channel}渠道{level}过程数据播报**",
        "",
        f"![{level}维度过程数据]({image_name})",
        "",
        *reminders,
    ])


def _reminder_people(level: str, rows: list[dict]) -> list[dict]:
    minimum = min(row["metrics"]["8min"] for row in rows)
    tied = sorted((row for row in rows if row["metrics"]["8min"] == minimum), key=lambda row: (row["顾问账号"] or row["主管"], row["年级"] or ""))
    people = {}
    for row in tied:
        name = row["主管"] if level == "主管" else row["顾问"]
        account = None if level == "主管" else row["顾问账号"]
        people.setdefault(account or name, {"name": name, "account": account})
    return list(people.values())


def _reminder_by_grade(level: str, rows: list[dict]) -> dict[str, list[dict]]:
    return {grade: _reminder_people(level, [row for row in rows if row["年级"] == grade])
            for grade in dict.fromkeys(row["年级"] for row in rows)}


def build(source: Path, supervisor_request: Path, consultant_request: Path, output: Path,
          config_path: Path = DEFAULT_CONFIG, levels: tuple[str, ...] = ("supervisor", "consultant")) -> dict:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if (config["domain"], config["channel_id"], config["report_type"]) not in (("qingcheng", "public_pool", "process"), ("qingcheng", "private", "process"), ("qingcheng", "douyin_dm", "process")):
        raise ValueError("Process config has unexpected scope")
    if (config["status"], config["schedule_enabled"]) not in (("preview_only", False), ("active", True)):
        raise ValueError("Process config has inconsistent delivery state")
    rows, manifest = _read_snapshot(source, config)
    channel = config["source"]["match"]["一级渠道"]
    requests = {
        "主管": json.loads(supervisor_request.read_text(encoding="utf-8")),
        "顾问": json.loads(consultant_request.read_text(encoding="utf-8")),
    }
    period = rows[0]["期次"]
    source_dt, source_hour = rows[0]["分区日期"], rows[0]["分区小时"]
    results = {}
    if not levels or len(set(levels)) != len(levels) or set(levels) - {"supervisor", "consultant"}:
        raise ValueError("Invalid process report levels")
    for slug in levels:
        level = "主管" if slug == "supervisor" else "顾问"
        request = requests[level]
        if request["reminder"]["report_level"] != level or request["business"]["channel_name"] != channel:
            raise ValueError("Request level or channel mismatch")
        profile = config["profiles"][slug]
        if (profile["request_id"], profile["target_chat_id"], profile["level"], profile["allowed_grades"], profile["minimum_effective_leads"]) != (
            request["source"]["request_id"], request["business"]["target_chat_id"], level, request["business"]["grades"], request["report"]["minimum"]["value"]
        ):
            raise ValueError(f"Process config and Base request differ for {level}")
        if profile["process_sort"] != {"metric": "8min", "direction": "desc", "value": "unrounded"} or profile["process_bars"] != ["好友率", "24h首call", "8min", "等待时长"]:
            raise ValueError(f"Unexpected process sort or bars for {level}")
        if profile["process_reminder"] != {"metric": "8min", "direction": "最低", "rank": "最后1名", "tie_handling": PROCESS_TIE_HANDLING}:
            raise ValueError(f"Unexpected process reminder config for {level}")
        split_grade = config["channel_id"] == "private"
        grouped = _sort_process_rows(_aggregate(rows, level, request, split_grade=split_grade), split_grade=split_grade)
        columns = [c.strip() for c in request["report"]["process_display_order"].split("、")]
        process_png = output / f"{slug}_process.png"
        _table_image(grouped, columns, process_png, level, period, channel, split_grade=split_grade)
        process_message = _message(level, period, grouped, request, process_png.name, channel)
        process_message_file = output / f"{slug}_process_message.md"
        process_message_file.write_text(process_message + "\n", encoding="utf-8")
        by_grade = _reminder_by_grade(level, grouped) if split_grade else None
        unique_people = list({person["account"] or person["name"]: person
                              for people in (by_grade or {}).values() for person in people}.values()) if split_grade else _reminder_people(level, grouped)
        results[slug] = {
            "level": level,
            "process_rows": len(grouped),
            "process_sort": "8min_desc_raw",
            "process_tie_handling": PROCESS_TIE_HANDLING,
            "reminder_people": unique_people,
            "reminder_by_grade": by_grade,
            "process_png": process_png.name,
            "process_message_file": process_message_file.name,
            "process_message": process_message,
        }
    output.mkdir(parents=True, exist_ok=True)
    review = {
        "source_record_count": len(rows),
        "source_rev": manifest["rev"],
        "period": period,
        "snapshot": f"{source_dt} {source_hour}:00",
        "channel_filter": config["source"]["match"],
        "visual_scales_status": "fixed_v1" if config["status"] == "active" else "draft_for_review",
        "results": results,
    }
    (output / "review.json").write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
    cards = []
    for item in results.values():
        cards.append(f"<section><h2>{html.escape(item['level'])}</h2><h3>过程图片</h3><img src='{item['process_png']}'><h3>过程消息 <a href='{item['process_message_file']}'>查看 Markdown</a></h3><pre>{html.escape(item['process_message'])}</pre></section>")
    page = """<!doctype html><html lang='zh-CN'><meta charset='utf-8'><title>青橙过程数据本地预览</title><style>body{font:16px 'Microsoft YaHei',sans-serif;background:#eef4ee;color:#20314c;margin:0;padding:32px}main{max-width:1800px;margin:auto}section{background:white;border-radius:16px;padding:24px;margin:24px 0;box-shadow:0 6px 24px 0 #3d8b4f18}img{max-width:100%;height:auto;border:1px solid #aecfb2}pre{white-space:pre-wrap;background:#f2f8f3;padding:18px;border-radius:8px;font:16px 'Microsoft YaHei',sans-serif}aside{background:#fff2dd;border-left:5px solid #de9b35;padding:16px}</style><main>""" + f"<h1>青橙{html.escape(channel)} · 过程数据本地预览</h1><aside>原始数据：{html.escape(period)}，分区 {html.escape(source_dt)} {html.escape(source_hour)}:00，共 {len(rows):,} 条。</aside>" + "".join(cards) + "</main></html>"
    (output / "index.html").write_text(page, encoding="utf-8")
    return review


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--supervisor-request", type=Path, required=True)
    parser.add_argument("--consultant-request", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.source, args.supervisor_request, args.consultant_request, args.output, args.config), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
