"""Build local SEC secondary-channel supervisor previews; never send messages."""

from __future__ import annotations

import argparse
import html
import json
from collections import Counter
from pathlib import Path

from preview_qingcheng_public_pool_process import _aggregate, _read_snapshot, _table_image
from preview_qingcheng_sec_process import SEC_BAR_FIELDS, _audit, _reminders, _sort_rows


SKILL = Path(__file__).resolve().parents[1]
CONFIG = SKILL / "config/departments/qingcheng/sec_secondary_supervisor_process_preview.json"
EXPECTED_COLUMNS = ["期次", "年级", "主管", "带班人数", "有效线索", "好友率", "等待时长",
                    "24h首call", "沟通率", "外呼时长", "外呼频次"]


def _validate_config(config: dict) -> dict:
    if (config["domain"], config["execution_surface"], config["report_type"],
            config["status"], config["schedule_enabled"], config["source"]["process_lead_field"]) != (
            "qingcheng", "local", "process", "preview_only", False, "退前线索"):
        raise ValueError("Secondary SEC supervisor configuration is outside local preview scope")
    if config["source"]["match"] != {"一级渠道": "订单复用", "部门": "SEC"}:
        raise ValueError("Secondary SEC source match differs")
    reports = config["reports"]
    if {(item["channel_id"], item["channel_name"], item["request_id"]) for item in reports} != {
            ("sec_no_friend_supervisor", "SEC未加好友", "qingcheng/sec_supervisor_no_friend"),
            ("sec_first_period_drop_supervisor", "SEC首期掉海", "qingcheng/sec_supervisor_first_period_drop")}:
        raise ValueError("Unexpected secondary SEC report list")
    bars = config["visual"]["metric_bars"]
    if tuple(bars) != SEC_BAR_FIELDS or len({item["color"] for item in bars.values()}) != 4:
        raise ValueError("Secondary SEC bars differ from reviewed SEC color assignment")
    if any(item["min"] != 0 or item["max"] <= 0 for item in bars.values()):
        raise ValueError("Secondary SEC bars require fixed positive ranges")
    if set(config["visual"]["integer_fields"]) != {"退前线索", "带班人数"}:
        raise ValueError("Secondary SEC integer column rule differs")
    return bars


def _validate_report(profile: dict, request: dict) -> list[str]:
    columns = [item.strip() for item in request["report"]["process_display_order"].split("、")]
    if columns != EXPECTED_COLUMNS:
        raise ValueError("Secondary SEC supervisor columns differ from the Base request")
    if (request["source"]["request_id"], request["business"]["channel_name"],
            request["business"]["target_chat_id"], request["reminder"]["report_level"],
            request["reminder"]["target"], request["reminder"]["process_metric"],
            request["reminder"]["process_direction"], request["reminder"]["process_rank"],
            request["report"]["minimum"], request["business"]["grades"]) != (
            profile["request_id"], profile["channel_name"], profile["target_chat_id"], "主管", "主管",
            "好友率", "最低", "最后1名", {"metric": "退前线索", "operator": ">=", "value": 5},
            profile["allowed_grades"]):
        raise ValueError("Secondary SEC supervisor profile differs from the Base request")
    if (profile["level"], profile["minimum_effective_leads"], profile["process_sort"],
            profile["process_bars"], profile["process_reminder"], profile["split_grade"],
            profile["reminder_by_grade"], profile["show_total"],
            profile["unresolved_mention_action"]) != (
            "主管", 5, {"metric": "好友率", "direction": "desc", "value": "unrounded"},
            list(SEC_BAR_FIELDS),
            {"metric": "好友率", "direction": "最低", "rank": "最后1名",
             "tie_handling": "all_tied_minimum"}, True, True, True, "invite_then_text"):
        raise ValueError("Secondary SEC supervisor preview behavior differs")
    return columns


def build(source: Path, output: Path, audit_log: Path, config_path: Path = CONFIG) -> dict:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    bars = _validate_config(config)
    rows, manifest = _read_snapshot(source, config)
    if manifest["channel"] != "sec_order_reuse" or manifest["period"] != rows[0]["期次"]:
        raise ValueError("Order-reuse source identity differs")
    audit = _audit(audit_log, manifest["period"])
    if (manifest["records_count"], manifest["snapshot"]) != (
            audit["counts"]["sec_order_reuse"], audit["snapshot"]):
        raise ValueError("Complete Base source differs from upstream audit")
    actual_counts = Counter(row["渠道"] for row in rows)
    expected_counts = audit["secondary_counts"]
    if {name: actual_counts.get(name, 0) for name in expected_counts} != expected_counts or sum(actual_counts.values()) != len(rows):
        raise ValueError("SEC secondary channel rows differ from verified source scope")

    result = {"period": manifest["period"], "snapshot": manifest["snapshot"],
              "source_rev": manifest["rev"], "source_record_count": len(rows),
              "status": "preview_only", "reports": {}}
    cards = []
    for profile in config["reports"]:
        request_path = config_path.parent / profile["request_file"]
        request = json.loads(request_path.read_text(encoding="utf-8"))
        columns = _validate_report(profile, request)
        subset = [row for row in rows if row["渠道"] == profile["channel_name"]]
        grouped = _aggregate(subset, "主管", request, split_grade=True, lead_field="退前线索")
        if not grouped:
            raise ValueError(f"No eligible supervisor rows for {profile['channel_name']}")
        grades = request["business"]["grades"]
        grouped = _sort_rows(grouped, grades, split_grade=True)
        reminders = _reminders(grouped, grades, "主管", split_grade=True)
        report_dir = output / profile["channel_id"]
        report_dir.mkdir(parents=True, exist_ok=True)
        image_path = report_dir / "supervisor_process.png"
        _table_image(grouped, columns, image_path, "主管", manifest["period"], profile["channel_name"],
                     split_grade=True,
                     bar_specs={field: (item["min"], item["max"], item["color"])
                                for field, item in bars.items()},
                     integer_fields=frozenset(config["visual"]["integer_fields"]))
        message_lines = [f"## 🔥 **【{manifest['period']}】{profile['channel_name']}渠道主管过程数据播报**", "",
                         "![主管维度过程数据](supervisor_process.png)", ""]
        message_lines.extend(f"- {item['grade']}年级好友率较低的主管："
                             + "、".join(person["name"] for person in item["people"])
                             for item in reminders)
        message = "\n".join(message_lines)
        (report_dir / "supervisor_process_message.md").write_text(message + "\n", encoding="utf-8")
        review = {"channel_id": profile["channel_id"], "channel_name": profile["channel_name"],
                  "level": "主管", "period": manifest["period"], "source_rev": manifest["rev"],
                  "snapshot": manifest["snapshot"], "raw_rows": len(subset),
                  "eligible_rows": len(grouped), "grade_blocks": [item["grade"] for item in reminders],
                  "sort": "grade_then_好友率_desc_raw", "process_lead_field": "退前线索",
                  "displayed_pre_return_leads": sum(row["metrics"]["退前线索"] for row in grouped),
                  "reminders": reminders, "target_chat_id": profile["target_chat_id"],
                  "unresolved_mention_action": "invite_then_text", "image": image_path.name,
                  "message_file": "supervisor_process_message.md", "message": message,
                  "status": "preview_only"}
        (report_dir / "review.json").write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        result["reports"][profile["channel_id"]] = review
        rel = profile["channel_id"]
        cards.append(f"<section><h2>{html.escape(profile['channel_name'])} · 主管</h2>"
                     f"<img src='{rel}/{image_path.name}' alt='过程图片'>"
                     f"<pre>{html.escape(message)}</pre></section>")

    output.mkdir(parents=True, exist_ok=True)
    page = ("<!doctype html><html lang='zh-CN'><meta charset='utf-8'><title>青橙 SEC 主管过程本地预览</title>"
            "<style>body{font:16px 'Microsoft YaHei',sans-serif;background:#edf2f8;color:#20314c;padding:24px}"
            "main{max-width:1900px;margin:auto}section{background:white;margin:22px 0;padding:20px;border-radius:12px}"
            "img{max-width:100%;border:1px solid #c3cfe2}pre{white-space:pre-wrap;background:#f2f6fb;padding:14px}</style>"
            f"<main><h1>青橙 SEC · 主管过程数据本地预览</h1><p>{html.escape(manifest['period'])}</p>"
            + "".join(cards) + "</main></html>")
    (output / "index.html").write_text(page, encoding="utf-8")
    (output / "batch.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--audit-log", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=CONFIG)
    args = parser.parse_args()
    result = build(args.source, args.output, args.audit_log, args.config)
    print(json.dumps({"period": result["period"], "source_rev": result["source_rev"],
                      "reports": {key: {"rows": value["eligible_rows"],
                                        "grade_blocks": value["grade_blocks"],
                                        "reminders": value["reminders"]}
                                  for key, value in result["reports"].items()}}, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
