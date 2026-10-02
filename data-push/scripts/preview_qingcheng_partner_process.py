"""Build local-only process previews for the three new Qingcheng partner channels.

Channels: partner_books (TuShu consultant), partner_local (Bendi-hua consultant),
supervisor_local (Bendi-hua supervisor). Reads complete same-revision Base
snapshots produced by fetch_qingcheng_process_source and the operator Base
export, then renders images through the production renderer and composes the
reviewed message text. No network calls, no sending, no scheduling.
"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

from preview_qingcheng_public_pool_process import (
    _aggregate,
    _read_snapshot,
    _reminder_people,
    _sort_process_rows,
    _table_image,
)

SKILL = Path(__file__).resolve().parents[1]
CONFIG_DIR = SKILL / "config" / "departments" / "qingcheng"
DEFAULT_CONFIG = CONFIG_DIR / "partner_process_preview.json"
GRADES = ["高一", "高二", "高三", "初三"]
DISPLAY_COLUMNS = {"期次", "主管", "顾问", "年级", "带班人数", "有效线索", "好友率", "等待时长",
                   "8min", "24h首call", "沟通率", "外呼时长", "外呼频次", "总通时",
                   "退前线索", "线索留存率"}


def _config(path: Path) -> dict:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    if (cfg["schema_version"], cfg["domain"], cfg["execution_surface"], cfg["report_type"],
            cfg["status"], cfg["schedule_enabled"], cfg["source"]["lead_field"],
            cfg["sender"]["identity"], cfg["sender"]["open_id"],
            cfg["process_sort"], cfg["process_reminder"]) != (
            1, "qingcheng", "local", "process", "preview_only", False, "退后线索",
            "bot", "ou_f3907e865135732c15a1dfce27828411",
            {"metric": "8min", "direction": "desc", "value": "unrounded"},
            {"metric": "8min", "direction": "最低", "rank": "最后1名", "tie_handling": "all_tied_minimum"}):
        raise ValueError("Partner process preview config differs")
    if [entry["id"] for entry in cfg["channels"]] != ["partner_books", "partner_local", "supervisor_local"]:
        raise ValueError("Partner channel list or order differs")
    layout = {"partner_books": (False, "8min_minimum"), "partner_local": (False, "8min_minimum"),
              "supervisor_local": (True, "8min_minimum_grade_text")}
    for entry in cfg["channels"]:
        if (entry["split_grade"], entry["process_reminder"]) != layout[entry["id"]]:
            raise ValueError(f"Partner channel layout differs: {entry['id']}")
    bars = cfg["visual"]["metric_bars"]
    if (set(bars) != {"好友率", "等待时长", "8min", "24h首call"}
            or bars["等待时长"]["color"] != "#fc999f" or bars["24h首call"]["color"] != "#77c09f"
            or any(spec["min"] != 0 or spec["max"] <= 0 for spec in bars.values())):
        raise ValueError("Partner process bar scales differ")
    if set(cfg["visual"]["integer_fields"]) != {"带班人数", "有效线索", "退前线索", "退后线索", "总通时"}:
        raise ValueError("Partner integer display fields differ")
    return cfg


def _request(entry: dict, cfg: dict, operator_rows: dict[str, dict]) -> dict:
    request = json.loads((CONFIG_DIR / entry["request_file"]).read_text(encoding="utf-8"))
    row = operator_rows.get(entry["operator_record_id"])
    if row is None:
        raise ValueError(f"Partner operator application is missing: {entry['id']}")
    columns = [part.strip() for part in row["过程指标展示顺序（选填）"].split("、")]
    if entry["process_reminder"] != "8min_minimum":
        # supervisor_local: single supervisor carries the channel; 2026-09-30 the user
        # cancelled the person reminder and @; only a grade-level text hint remains.
        expected_operator = (["不提醒"], ["不提醒"], ["最低"])
        expected_reminder = (entry["level"], "不提醒", "不适用", "不适用", "不提醒")
    else:
        expected_operator = ([entry["level"]], ["最后1名"], ["最低"])
        expected_reminder = (entry["level"], entry["level"], "8min", "最低", "最后1名")
    if (row["申请编号"], row["渠道标准名称"], row["目标群"][0]["id"], row["播报层级"],
            row["提醒对象"], row["年级范围"], row["展示门槛指标"], row["门槛运算符"],
            int(row["门槛值"]), row["过程文字提醒名次"], row["过程重点提醒指标"],
            row["过程指标提醒方向"], row["申请状态"]) != (
            f"qingcheng/{entry['id']}", entry["name"], entry["target_chat_id"], [entry["level"]],
            expected_operator[0], GRADES, "有效线索", [">="], entry["minimum_effective_leads"],
            expected_operator[1], ["8min"], expected_operator[2], ["已上线"]):
        raise ValueError(f"Partner Base application differs: {entry['id']}")
    if (request["source"]["request_id"], request["source"]["operator_record_id"],
            request["business"]["channel_name"], request["business"]["target_chat_id"],
            request["business"]["grades"], request["reminder"]["report_level"],
            request["reminder"]["target"], request["reminder"]["process_metric"],
            request["reminder"]["process_direction"], request["reminder"]["process_rank"],
            request["report"]["minimum"]) != (
            f"qingcheng/{entry['id']}", entry["operator_record_id"], entry["name"],
            entry["target_chat_id"], GRADES, *expected_reminder,
            {"metric": "有效线索", "operator": ">=", "value": entry["minimum_effective_leads"]}):
        raise ValueError(f"Partner request snapshot differs from config: {entry['id']}")
    if (not columns or len(columns) != len(set(columns)) or set(columns) - DISPLAY_COLUMNS
            or columns != [part.strip() for part in request["report"]["process_display_order"].split("、")]
            or (entry["level"] == "主管" and "主管" not in columns)
            or (entry["level"] == "顾问" and not {"主管", "顾问", "年级"} <= set(columns))):
        raise ValueError(f"Partner display columns differ: {entry['id']}")
    if set(row["过程指标（逐项勾选）"]) != set(columns) - {"期次", "主管", "顾问", "年级"}:
        raise ValueError(f"Partner metric selection differs: {entry['id']}")
    if row["展示总计行"] is not False:
        raise ValueError(f"Partner total-row baseline changed: {entry['id']}")
    return request


def build(sources: dict[str, Path], operator: Path, output: Path, *,
          config_path: Path = DEFAULT_CONFIG) -> dict:
    cfg = _config(config_path)
    operator_manifest = json.loads(operator.with_suffix(".manifest.json").read_text(encoding="utf-8"))
    operator_rows = [json.loads(line) for line in operator.read_text(encoding="utf-8").splitlines() if line]
    if (operator_manifest.get("has_more") is not False
            or len(operator_rows) != operator_manifest.get("records_count")
            or len({row["record_id"] for row in operator_rows}) != len(operator_rows)):
        raise ValueError("Partner operator Base export is incomplete")
    by_id = {row["record_id"]: row for row in operator_rows}
    bars = cfg["visual"]["metric_bars"]
    bar_specs = {field: (spec["min"], spec["max"], spec["color"]) for field, spec in bars.items()}
    integer_fields = frozenset(cfg["visual"]["integer_fields"])
    output.mkdir(parents=True, exist_ok=True)
    summary = {"status": "preview_only", "reports": []}
    cards = []
    for entry in cfg["channels"]:
        request = _request(entry, cfg, by_id)
        match = cfg["source"]["matches"][entry["id"]]
        rows, manifest = _read_snapshot(sources[entry["id"]], {"source": {"match": match}})
        if any(row["渠道"] != match["渠道"] for row in rows):
            raise ValueError(f"Partner source contains an unreviewed secondary channel: {entry['id']}")
        grouped = _sort_process_rows(
            _aggregate(rows, entry["level"], request, split_grade=entry["split_grade"],
                       lead_field=cfg["source"]["lead_field"]),
            split_grade=entry["split_grade"])
        folder = output / entry["id"]
        folder.mkdir(parents=True, exist_ok=True)
        image = folder / "process.png"
        columns = [part.strip() for part in request["report"]["process_display_order"].split("、")]
        period = manifest["period"]
        if not grouped:
            summary["reports"].append({"id": entry["id"], "status": "skipped_no_eligible_rows",
                                       "snapshot": manifest["snapshot"]})
            continue
        _table_image(grouped, columns, image, entry["level"], period, entry["name"],
                     split_grade=entry["split_grade"], bar_specs=bar_specs,
                     integer_fields=integer_fields)
        lines = [f"## 🔥 **【{period}】{entry['name']}渠道{entry['level']}过程数据播报**", "",
                 "![过程数据](process.png)"]
        reminder_grades: list[str] = []
        if entry["process_reminder"] == "8min_minimum_grade_text":
            people = []
            by_grade: dict[str, list[float]] = {}
            for row in grouped:
                by_grade.setdefault(row["年级"], []).append(row["metrics"]["8min"])
            grade_min = {grade: min(values) for grade, values in by_grade.items()}
            least = min(grade_min.values())
            reminder_grades = [grade for grade in ("高一", "高二", "高三", "初三")
                               if grade_min.get(grade) == least]
            lines += ["", "- 8min较低年级：" + "、".join(reminder_grades)]
        elif entry["process_reminder"] == "none":
            people = []
        else:
            people = _reminder_people(entry["level"], grouped)
            names = "、".join(person["name"] for person in people)
            lines += ["", f"- 8min较低的{entry['level']}：{names}"]
        message = "\n".join(lines)
        (folder / "message.md").write_text(message + "\n", encoding="utf-8")
        review = {"id": entry["id"], "channel": entry["name"], "level": entry["level"],
                  "period": period, "source_rev": manifest["rev"], "snapshot": manifest["snapshot"],
                  "raw_rows": len(rows), "eligible_rows": len(grouped),
                  "reminder_people": people, "reminder_grades": reminder_grades,
                  "image": image.name, "message": message,
                  "target_chat_id": entry["target_chat_id"],
                  "target_chat_name": entry["target_chat_name"]}
        (folder / "review.json").write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n",
                                            encoding="utf-8")
        summary["reports"].append(review)
        cards.append(f"<section><h2>{html.escape(entry['name'])} · {html.escape(entry['level'])} · "
                     f"{html.escape(period)} → {html.escape(entry['target_chat_name'])}</h2>"
                     f"<pre>{html.escape(message)}</pre>"
                     f"<img src='{entry['id']}/process.png' alt='{html.escape(entry['name'])}过程数据图片'></section>")
    page = ("<!doctype html><html lang='zh-CN'><meta charset='utf-8'><title>青橙伙伴渠道过程数据本地预览</title>"
            "<style>body{font:16px 'Microsoft YaHei',sans-serif;background:#eef4ee;color:#20314c;padding:24px}"
            "main{max-width:2100px;margin:auto}section{background:white;margin:22px 0;padding:20px;border-radius:12px}"
            "pre{white-space:pre-wrap;background:#f2f8f3;padding:14px;border-radius:8px;font:16px 'Microsoft YaHei',sans-serif}"
            "img{max-width:100%;border:1px solid #c3cfe2}</style>"
            "<main><h1>青橙伙伴渠道（图书/本地化）· 过程数据本地预览</h1>"
            + "".join(cards) + "</main></html>")
    (output / "index.html").write_text(page, encoding="utf-8")
    (output / "batch.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-books", type=Path, required=True)
    parser.add_argument("--source-local", type=Path, required=True)
    parser.add_argument("--operator", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sources = {"partner_books": args.source_books,
               "partner_local": args.source_local,
               "supervisor_local": args.source_local}
    summary = build(sources, args.operator, args.output, config_path=args.config)
    print(json.dumps({"reports": [{"id": item.get("id"), "eligible_rows": item.get("eligible_rows", 0)}
                                  for item in summary["reports"]]}, ensure_ascii=True))


if __name__ == "__main__":
    main()
