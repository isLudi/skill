"""Build four image-only Qingcheng special-channel process previews locally."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import html
import json
from pathlib import Path

from preview_qingcheng_public_pool_process import _number, _ratio, _table_image


SKILL = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = SKILL / "config/departments/qingcheng/special_process_preview.json"
GRADES = ["高一", "高二", "高三", "初三"]
DISPLAY_COLUMNS = ["期次", "负责人", "年级", "带班人数", "有效线索",
                   "好友率", "等待时长", "8min", "24h首call",
                   "沟通率", "外呼时长", "外呼频次"]
SOURCE_NUMBERS = ["退后线索", "好友标记", "首call等待时长小时", "8min标记",
                  "24h首call标记", "沟通标记", "总通时秒", "外呼次数"]


def _read_lines(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _config(path: Path) -> dict:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    if (cfg["schema_version"], cfg["domain"], cfg["execution_surface"], cfg["report_type"],
            cfg["report_level"], cfg["status"], cfg["schedule_enabled"], cfg["image_only"],
            cfg["text_header"], cfg["show_total"], cfg["split_grade"], cfg["source"]["dimension_field"],
            cfg["source"]["dimension_label"], cfg["source"]["lead_field"], cfg["sort"],
            cfg["target_chat_id"], cfg["sender"]["identity"], cfg["sender"]["open_id"]) != (
            1, "qingcheng", "local", "process", "学部", "preview_only", False, False,
            True, True, True, "经理", "负责人", "退后线索",
            {"metric": "8min", "direction": "desc", "value": "unrounded"},
            "oc_a95c83e488e0dfcc777d5ffad849d8a4", "bot",
            "ou_f3907e865135732c15a1dfce27828411"):
        raise ValueError("Special-channel image preview config differs")
    if ([item["name"] for item in cfg["channels"]] != ["私域", "图书", "抖音私信", "公海"]
            or len({item["operator_record_id"] for item in cfg["channels"]}) != 4):
        raise ValueError("Special-channel list differs")
    return cfg


def _request(row: dict, entry: dict, cfg: dict) -> tuple[list[str], int]:
    columns = [part.strip() for part in row["过程指标展示顺序（选填）"].split("、")]
    if (row["record_id"], row["申请编号"], row["渠道标准名称"], row["原始渠道示例"],
            row["目标群"][0]["id"], row["数据维度"], row["年级范围"],
            row["展示门槛指标"], row["门槛运算符"], row["门槛值"],
            row["播报层级"], row["提醒对象"], row["过程文字提醒名次"], columns) != (
            entry["operator_record_id"], f"qingcheng/{entry['id']}", entry["name"], entry["name"],
            cfg["target_chat_id"], ["期次", "渠道", "负责人", "年级"], GRADES,
            "有效线索", [">="], 5, ["学部"], ["不提醒"], ["不提醒"], DISPLAY_COLUMNS):
        raise ValueError(f"Special-channel Base request differs: {entry['id']}")
    if set(row["过程指标（逐项勾选）"]) != set(DISPLAY_COLUMNS) - {"期次", "负责人", "年级"}:
        raise ValueError(f"Special-channel Base metric selection differs: {entry['id']}")
    if row["展示总计行"] is not False:
        raise ValueError("Special-channel Base total-row baseline changed")
    return columns, int(row["门槛值"])


def _aggregate(rows: list[dict], period: str, threshold: int) -> list[dict]:
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for source in rows:
        if source["年级"] not in GRADES:
            continue
        if not source.get("经理") or not source.get("顾问账号"):
            raise ValueError("Special-channel owner or consultant account is missing")
        groups[(source["经理"], source["年级"])].append(source)
    result = []
    for (manager, grade), items in groups.items():
        effective = sum(_number(item, "退后线索") for item in items)
        if effective < threshold:
            continue
        metrics = {
            "带班人数": len({item["顾问账号"] for item in items}),
            "有效线索": effective,
            "好友率": _ratio(sum(_number(item, "好友标记") for item in items), effective),
            "等待时长": _ratio(sum(_number(item, "首call等待时长小时") for item in items), effective),
            "8min": _ratio(sum(_number(item, "8min标记") for item in items), effective),
            "24h首call": _ratio(sum(_number(item, "24h首call标记") for item in items), effective),
            "沟通率": _ratio(sum(_number(item, "沟通标记") for item in items), effective),
            "外呼时长": _ratio(sum(_number(item, "总通时秒") for item in items) / 60, effective),
            "外呼频次": _ratio(sum(_number(item, "外呼次数") for item in items), effective),
            "总通时": sum(_number(item, "总通时秒") for item in items) / 60,
        }
        if metrics["8min"] is None:
            raise ValueError("Eligible special-channel row has no 8min denominator")
        result.append({"key": (period, manager, grade), "负责人": manager, "年级": grade,
                       "metrics": metrics, "_accounts": frozenset(item["顾问账号"] for item in items)})
    order = {grade: index for index, grade in enumerate(GRADES)}
    return sorted(result, key=lambda item: (order[item["年级"]], -item["metrics"]["8min"], item["负责人"]))


def build(source: Path, operator: Path, output: Path, *, config_path: Path = DEFAULT_CONFIG) -> dict:
    cfg = _config(config_path)
    manifest = json.loads(source.with_suffix(".manifest.json").read_text(encoding="utf-8"))
    source_rows = _read_lines(source)
    if (len(source_rows) != manifest["rows"] or len({row["record_id"] for row in source_rows}) != len(source_rows)
            or len({(row["分区日期"], row["分区小时"]) for row in source_rows}) != 1
            or {row["期次"] for row in source_rows} != {manifest["period"]}
            or Counter(row["渠道"] for row in source_rows) != Counter(manifest["channels"])):
        raise ValueError("Special-channel source differs from its complete-period manifest")
    for row in source_rows:
        for field in SOURCE_NUMBERS:
            _number(row, field)
    operator_rows = _read_lines(operator)
    operator_manifest = json.loads(operator.with_suffix(".manifest.json").read_text(encoding="utf-8"))
    if operator_manifest["has_more"] is not False or len(operator_rows) != operator_manifest["records_count"]:
        raise ValueError("Special-channel Base applications are incomplete")
    by_id = {row["record_id"]: row for row in operator_rows}
    if len(by_id) != len(operator_rows):
        raise ValueError("Duplicate special-channel Base application IDs")
    bars = cfg["visual"]["metric_bars"]
    if set(bars) != {"好友率", "等待时长", "8min", "24h首call"} or bars["等待时长"]["color"] != "#fc999f":
        raise ValueError("Special-channel process bars differ")
    bar_specs = {field: (spec["min"], spec["max"], spec["color"]) for field, spec in bars.items()}
    output.mkdir(parents=True, exist_ok=True)
    summary = {"status": "preview_only", "period": manifest["period"], "source_rev": manifest["rev"],
               "operator_rev": operator_manifest["rev"],
               "snapshot": manifest["snapshot"], "source_rows": len(source_rows),
               "image_only": False, "text_header": True, "sort": cfg["sort"], "reports": []}
    cards = []
    for entry in cfg["channels"]:
        request = by_id[entry["operator_record_id"]]
        columns, threshold = _request(request, entry, cfg)
        selected = [row for row in source_rows if row["一级渠道"] == entry["name"]]
        if not selected:
            raise ValueError(f"No raw rows for requested special channel: {entry['name']}")
        if any(row["年级"] not in GRADES and row["年级"] != "初二" for row in selected):
            raise ValueError(f"Unreviewed special-channel grade: {entry['name']}")
        grouped = _aggregate(selected, manifest["period"], threshold)
        if not grouped:
            raise ValueError(f"No eligible special-channel rows: {entry['name']}")
        destination = output / entry["id"]
        destination.mkdir(parents=True, exist_ok=True)
        image_path = destination / "process.png"
        _table_image(grouped, columns, image_path, "学部", manifest["period"], entry["name"],
                     split_grade=True, bar_specs=bar_specs,
                     integer_fields=frozenset(cfg["visual"]["integer_fields"]))
        message = "\n".join([f"## 🔥 **【{manifest['period']}】{entry['name']}渠道学部过程数据播报**", "",
                             "![过程数据](process.png)"])
        (destination / "message.md").write_text(message + "\n", encoding="utf-8")
        review = {"channel": entry["name"], "request_id": request["申请编号"],
                  "source_rows": len(selected), "eligible_rows": len(grouped),
                  "grades": [grade for grade in GRADES if any(row["年级"] == grade for row in grouped)],
                  "displayed_effective_leads": sum(row["metrics"]["有效线索"] for row in grouped),
                  "owner_mapping": "负责人=原始表经理", "image": image_path.name,
                  "image_only": False, "text_header": True, "message": message,
                  "columns": columns, "threshold": threshold,
                  "base_show_total": request["展示总计行"], "preview_show_total": cfg["show_total"]}
        (destination / "review.json").write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n",
                                                  encoding="utf-8")
        summary["reports"].append({"id": entry["id"], **review})
        cards.append(f"<section><h2>{html.escape(entry['name'])} · 学部 · {html.escape(manifest['period'])}</h2>"
                     f"<pre>{html.escape(message)}</pre>"
                     f"<img src='{entry['id']}/process.png' alt='{html.escape(entry['name'])}过程数据图片'></section>")
    page = ("<!doctype html><html lang='zh-CN'><meta charset='utf-8'><title>青橙渠道专项过程图片预览</title>"
            "<style>body{font:16px 'Microsoft YaHei',sans-serif;background:#edf2f8;color:#20314c;padding:24px}"
            "main{max-width:2100px;margin:auto}section{background:white;margin:22px 0;padding:20px;border-radius:12px}"
            "img{max-width:100%;border:1px solid #c3cfe2}</style>"
            f"<main><h1>青橙渠道专项 · 过程数据图片本地预览</h1><p>{html.escape(manifest['period'])}</p>"
            + "".join(cards) + "</main></html>")
    (output / "index.html").write_text(page, encoding="utf-8")
    (output / "batch.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--operator", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.source, args.operator, args.output)
    print(json.dumps({"status": result["status"], "period": result["period"],
                      "reports": [{"channel": report["channel"], "source_rows": report["source_rows"],
                                   "eligible_rows": report["eligible_rows"], "grades": report["grades"]}
                                  for report in result["reports"]]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
