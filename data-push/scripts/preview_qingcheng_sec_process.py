"""Build local Qingcheng SEC process images and message previews without sending."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

from preview_qingcheng_public_pool_process import _aggregate, _read_snapshot, _table_image


SKILL = Path(__file__).resolve().parents[1]
CONFIG = SKILL / "config/departments/qingcheng"
REPORTS = (
    ("sec_public", "supervisor", "sec_public_supervisor_request.json", "sec_public_process_preview.json"),
    ("sec_public", "consultant", "sec_public_consultant_request.json", "sec_public_process_preview.json"),
    ("sec_order_reuse", "consultant", "sec_order_reuse_consultant_request.json", "sec_order_reuse_process_preview.json"),
)
AUDIT_CHANNELS = {"sec_public": ("公域学霸",),
                  "sec_order_reuse": ("SEC未加好友", "SEC首期掉海", "SEC招生退费")}
SEC_BAR_FIELDS = ("好友率", "24h首call", "外呼时长", "外呼频次")


def _audit(path: Path, period: str) -> dict:
    lines = path.read_text(encoding="utf-8").splitlines()
    entries = [line.split("：", 1)[1] for line in lines if line.startswith("process表快照清单：")]
    if len(entries) != 1 or not any(line.startswith("SUCCESS: 青橙项目部") for line in lines) or "exit_code:  0" not in lines:
        raise ValueError("Qingcheng process audit is incomplete")
    audit = json.loads(entries[0])
    if audit.get("schema_version") != "market2lark-two-period-audit-v1" or audit.get("field_count") != 27:
        raise ValueError("Unexpected process audit schema")
    info = audit.get("periods", {}).get(period)
    if not info or len(info["snapshots"]) != 1:
        raise ValueError("Business period or source snapshot is absent from audit")
    return {"snapshot": info["snapshots"][0],
            "counts": {channel: sum(info["channel_counts"].get(name, 0) for name in names)
                       for channel, names in AUDIT_CHANNELS.items()},
            "secondary_counts": {name: info["channel_counts"].get(name, 0)
                                 for name in AUDIT_CHANNELS["sec_order_reuse"]}}


def _reminder(rows: list[dict], level: str) -> dict:
    least = min(row["metrics"]["好友率"] for row in rows)
    tied = [row for row in rows if row["metrics"]["好友率"] == least]
    tied.sort(key=lambda row: (row["顾问账号"] or row["主管"], row["年级"] or ""))
    return {"people": [{"name": row["顾问"] if level == "顾问" else row["主管"],
                         "account": row["顾问账号"] if level == "顾问" else None}
                        for row in tied],
            "raw_rate": least, "tied_rows": len(tied), "tie_handling": "all_tied_minimum"}


def _sort_rows(rows: list[dict], grades: list[str], *, split_grade: bool) -> list[dict]:
    grade_order = {grade: index for index, grade in enumerate(grades)}
    return sorted(rows, key=lambda row: (grade_order[row["年级"]] if split_grade else 0,
                                         -row["metrics"]["好友率"], row["顾问账号"] or row["主管"],
                                         row["年级"] or ""))


def _reminders(rows: list[dict], grades: list[str], level: str, *, split_grade: bool) -> list[dict]:
    if not split_grade:
        return [{"grade": None, **_reminder(rows, level)}]
    return [{"grade": grade, **_reminder([row for row in rows if row["年级"] == grade], level)}
            for grade in grades if any(row["年级"] == grade for row in rows)]


def _build_one(source: Path, request_path: Path, config_path: Path, level_slug: str, output: Path) -> dict:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    request = json.loads(request_path.read_text(encoding="utf-8"))
    level = "主管" if level_slug == "supervisor" else "顾问"
    profile = config["profiles"][level_slug]
    if (config["domain"], config["report_type"], config["status"], config["schedule_enabled"],
            config["source"]["process_lead_field"]) != ("qingcheng", "process", "preview_only", False, "退前线索"):
        raise ValueError("SEC preview scope or denominator differs")
    if (profile["request_id"], profile["target_chat_id"], profile["level"], profile["allowed_grades"],
            profile["minimum_effective_leads"], profile["process_sort"], profile["process_bars"],
            profile["process_reminder"]) != (
            request["source"]["request_id"], request["business"]["target_chat_id"], level,
            request["business"]["grades"], request["report"]["minimum"]["value"],
            {"metric": "好友率", "direction": "desc", "value": "unrounded"},
            list(SEC_BAR_FIELDS),
            {"metric": "好友率", "direction": "最低", "rank": "最后1名", "tie_handling": "all_tied_minimum"}):
        raise ValueError("SEC profile differs from the Base application")
    if (request["business"]["channel_name"], request["reminder"]["report_level"],
            request["reminder"]["process_metric"], request["reminder"]["process_direction"],
            request["reminder"]["process_rank"]) != (
            config["source"]["match"]["一级渠道"], level, "好友率", "最低", "最后1名"):
        raise ValueError("SEC request process reminder differs")
    split_grade = level == "顾问"
    if (profile["split_grade"], profile["reminder_by_grade"]) != (split_grade, split_grade):
        raise ValueError("SEC consultant grade partition differs")
    rows, manifest = _read_snapshot(source, config)
    if manifest["channel"] != config["channel_id"]:
        raise ValueError("SEC source channel identity differs")
    allowed_secondary = set(config["source"].get("allowed_secondary_channels", []))
    if allowed_secondary and any(row["渠道"] not in allowed_secondary for row in rows):
        raise ValueError("Unreviewed order-reuse secondary channel")
    grouped = _aggregate(rows, level, request, lead_field="退前线索")
    if not grouped:
        raise ValueError("No eligible SEC process rows")
    grades = request["business"]["grades"]
    grouped = _sort_rows(grouped, grades, split_grade=split_grade)
    reminders = _reminders(grouped, grades, level, split_grade=split_grade)
    columns = [column.strip() for column in request["report"]["process_display_order"].split("、")]
    if "8min" in columns or set(columns) - {"期次", "主管", "顾问", "年级", "带班人数", "有效线索",
                                          "好友率", "等待时长", "24h首call", "沟通率", "外呼时长", "外呼频次", "总通时"}:
        raise ValueError("SEC process display columns differ from the reviewed scope")
    bars = config["visual"]["metric_bars"]
    if tuple(bars) != SEC_BAR_FIELDS or not set(bars).issubset(columns):
        raise ValueError("SEC color-bar fields differ from the image columns")
    colors = [spec["color"] for spec in bars.values()]
    if len(set(colors)) != 4 or any(spec["min"] != 0 or spec["max"] <= 0 for spec in bars.values()):
        raise ValueError("SEC color bars require distinct colors and fixed positive scales")
    bar_specs = {field: (spec["min"], spec["max"], spec["color"]) for field, spec in bars.items()}
    channel = request["business"]["channel_name"]
    period = rows[0]["期次"]
    output.mkdir(parents=True, exist_ok=True)
    image_path = output / f"{level_slug}_process.png"
    _table_image(grouped, columns, image_path, level, period, channel,
                 split_grade=split_grade, bar_specs=bar_specs)
    message_lines = [f"## 🔥 **【{period}】{channel}渠道{level}过程数据播报**", "",
                     f"![{level}维度过程数据]({image_path.name})", ""]
    message_lines.extend(f"- {item['grade'] + '年级' if item['grade'] else ''}好友率较低的{level}："
                         + "、".join(person["name"] for person in item["people"])
                         for item in reminders)
    message = "\n".join(message_lines)
    message_path = output / f"{level_slug}_process_message.md"
    message_path.write_text(message + "\n", encoding="utf-8")
    review = {"channel_id": config["channel_id"], "level": level, "period": period,
              "source_rev": manifest["rev"], "source_record_count": len(rows),
              "snapshot": manifest["snapshot"], "process_lead_field": "退前线索",
              "eligible_rows": len(grouped), "displayed_effective_leads": sum(row["metrics"]["有效线索"] for row in grouped),
              "sort": "grade_then_好友率_desc_raw" if split_grade else "好友率_desc_raw",
              "grade_blocks": [item["grade"] for item in reminders] if split_grade else [],
              "metric_bars": bars, "reminders": reminders,
              "target_chat_id": profile["target_chat_id"], "image": image_path.name,
              "message": message, "message_file": message_path.name, "status": "preview_only"}
    (output / "review.json").write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return review


def build(source_root: Path, output: Path, audit_log: Path, period_date: str) -> dict:
    period = period_date + "期"
    audit = _audit(audit_log, period)
    manifests = {}
    for channel in AUDIT_CHANNELS:
        source = source_root / channel / "source.ndjson"
        manifest = json.loads(source.with_suffix(".manifest.json").read_text(encoding="utf-8"))
        if (manifest["records_count"], manifest["snapshot"], manifest["period"]) != (
                audit["counts"][channel], audit["snapshot"], period):
            raise ValueError(f"SEC {channel} Base source differs from upstream audit")
        manifests[channel] = manifest
    if len({(manifest["rev"], tuple(manifest["snapshot"])) for manifest in manifests.values()}) != 1:
        raise ValueError("SEC sources do not share a Base revision and snapshot")
    reviews = {}
    cards = []
    for channel, level, request_name, config_name in REPORTS:
        path = output / channel / level
        review = _build_one(source_root / channel / "source.ndjson", CONFIG / request_name,
                            CONFIG / config_name, level, path)
        key = f"{channel}/{level}"
        reviews[key] = review
        cards.append(f"<section><h2>{html.escape(channel)} · {html.escape(review['level'])}</h2>"
                     f"<img src='{key}/{review['image']}' alt='过程图片'>"
                     f"<pre>{html.escape(review['message'])}</pre></section>")
    output.mkdir(parents=True, exist_ok=True)
    page = ("<!doctype html><html lang='zh-CN'><meta charset='utf-8'><title>青橙 SEC 过程数据本地预览</title>"
            "<style>body{font:16px 'Microsoft YaHei',sans-serif;background:#edf2f8;color:#20314c;padding:24px}"
            "main{max-width:1900px;margin:auto}section{background:white;margin:22px 0;padding:20px;border-radius:12px}"
            "img{max-width:100%;border:1px solid #c3cfe2}pre{white-space:pre-wrap;background:#f2f6fb;padding:14px}</style>"
            f"<main><h1>青橙 SEC · 公域与订单复用过程数据本地预览</h1><p>{html.escape(period)}</p>"
            + "".join(cards) + "</main></html>")
    (output / "index.html").write_text(page, encoding="utf-8")
    summary = {"period": period, "source_rev": next(iter(manifests.values()))["rev"],
               "snapshot": audit["snapshot"], "audit_log": str(audit_log), "reviews": reviews}
    (output / "batch.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--audit-log", type=Path, required=True)
    parser.add_argument("--period-date", required=True)
    args = parser.parse_args()
    result = build(args.source_root, args.output, args.audit_log, args.period_date)
    print(json.dumps({"period": result["period"], "source_rev": result["source_rev"],
                      "reports": {key: {"rows": item["eligible_rows"], "effective_leads": item["displayed_effective_leads"],
                                        "reminders": [person["name"] for entry in item["reminders"]
                                                      for person in entry["people"]]}
                                  for key, item in result["reviews"].items()}}, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
