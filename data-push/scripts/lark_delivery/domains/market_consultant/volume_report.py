"""Read-only KOC volume-progress aggregation for preview and scheduled delivery."""
from __future__ import annotations

import argparse
from collections import defaultdict
import html
import json
from pathlib import Path
import tempfile
from typing import Any, Iterable, Mapping
import unicodedata

from PIL import Image, ImageDraw

from ...common import feishu as gp
from ...common.base import _fetch_view_records
from ...common.images import _center_text, _find_font
from ...common.records import value
from . import grade_report as gr


VOLUME_FIELDS = ("期次", "年级", "渠道", "预估量级", "实际进量", "退前线索", "退后线索", "接量顾问数")
LEAD_FIELDS = ("期次", "年级", "渠道", "异常流量标记")
IMAGE_COLUMNS = ("期次", "年级", "预估量级", "实际进量", "线索留存率", "人均带班", "量级完成度")
REPORT_GRADE_ORDER = ("初三", "高一", "高二", "高三")
GRADE_ORDER = {grade: index for index, grade in enumerate(REPORT_GRADE_ORDER)}
REPORT_BAR_COLORS = {"线索留存率": "#4f78ae", "量级完成度": "#f5ae23"}
REPORT_COLORS = {"header": "#203b72", "header_text": "#ffffff",
                 "body": "#ffffff", "body_text": "#111827", "grid": "#b8c4d3"}
RULE_KOC_AND_SELF_INCUBATED = "contains_koc_case_insensitive_and_contains_自孵化"
RULE_KOC_NOT_SELF_INCUBATED = "contains_koc_case_insensitive_and_not_contains_自孵化"
CHANNEL_RULE_DESCRIPTIONS = {
    RULE_KOC_AND_SELF_INCUBATED: "渠道名称同时包含自孵化和KOC（KOC不区分大小写）",
    RULE_KOC_NOT_SELF_INCUBATED: "渠道名称包含KOC（不区分大小写）且不包含自孵化",
}


def _text(row: Mapping[str, Any], field: str) -> str:
    raw = value(row, field)
    return "" if raw is None else str(raw).strip()


def _number(row: Mapping[str, Any], field: str) -> float:
    raw = value(row, field)
    if raw in (None, ""):
        return 0.0
    try:
        return float(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"字段{field}不是数值: {raw!r}") from exc


def _ratio(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator else None


def normalize_channel(channel: str) -> str:
    return unicodedata.normalize("NFKC", channel).strip()


def eligible_channel(channel: str, rule: str = RULE_KOC_AND_SELF_INCUBATED) -> bool:
    """Apply one reviewed dynamic rule without an exact-name whitelist."""
    normalized = normalize_channel(channel)
    contains_koc = "koc" in normalized.casefold()
    if rule == RULE_KOC_AND_SELF_INCUBATED:
        return contains_koc and "自孵化" in normalized
    if rule == RULE_KOC_NOT_SELF_INCUBATED:
        return contains_koc and "自孵化" not in normalized
    raise ValueError(f"未审核的进量渠道规则: {rule}")


def latest_period(rows: Iterable[Mapping[str, Any]], rule: str = RULE_KOC_AND_SELF_INCUBATED) -> str:
    periods = {_text(row, "期次") for row in rows
               if eligible_channel(_text(row, "渠道"), rule) and _text(row, "期次")}
    if not periods:
        raise ValueError("进量表没有符合渠道规则的期次")
    return max(periods)


def aggregate_volume(rows: Iterable[Mapping[str, Any]], period: str,
                     rule: str = RULE_KOC_AND_SELF_INCUBATED) -> tuple[list[dict[str, Any]], set[str], set[tuple[str, str]]]:
    """Aggregate additive facts by grade, then calculate derived metrics."""
    buckets: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "预估量级": 0.0, "实际进量": 0.0, "退前线索": 0.0, "退后线索": 0.0,
        "接量顾问数": 0.0, "channels": set(), "source_rows": 0,
    })
    channels: set[str] = set()
    channel_grades: set[tuple[str, str]] = set()
    for row in rows:
        channel, grade = _text(row, "渠道"), _text(row, "年级")
        if _text(row, "期次") != period or not eligible_channel(channel, rule) or not grade:
            continue
        bucket = buckets[grade]
        for field in ("预估量级", "实际进量", "退前线索", "退后线索", "接量顾问数"):
            bucket[field] += _number(row, field)
        bucket["channels"].add(channel)
        bucket["source_rows"] += 1
        channels.add(channel)
        # A zero-lead placeholder can carry forecast/headcount but has no lead
        # rows and therefore no valid abnormal-traffic denominator.
        if _number(row, "退前线索") or _number(row, "实际进量") or _number(row, "退后线索"):
            channel_grades.add((channel, grade))
    if not buckets:
        raise ValueError(f"进量表在{period}没有符合KOC/自孵化筛选的数据")
    result = []
    for grade, bucket in buckets.items():
        result.append({
            "期次": period, "年级": grade,
            "预估量级": bucket["预估量级"], "实际进量": bucket["实际进量"],
            "线索留存率": _ratio(bucket["退后线索"], bucket["退前线索"]),
            "人均带班": _ratio(bucket["实际进量"], bucket["接量顾问数"]),
            "量级完成度": _ratio(bucket["实际进量"], bucket["预估量级"]),
            "_退前线索": bucket["退前线索"], "_退后线索": bucket["退后线索"],
            "_接量顾问数": bucket["接量顾问数"], "_渠道": sorted(bucket["channels"]),
            "_源行数": bucket["source_rows"],
        })
    result.sort(key=lambda row: GRADE_ORDER.get(row["年级"], len(GRADE_ORDER)))
    return result, channels, channel_grades


def aggregate_abnormal(rows: Iterable[Mapping[str, Any]], period: str, channels: set[str],
                       channel_grades: set[tuple[str, str]]) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Match exact period+channel+grade, aggregate binary facts, then divide."""
    buckets = defaultdict(lambda: {"异常量": 0.0, "线索量": 0, "matched_dimensions": set()})
    observed_dimensions: set[tuple[str, str]] = set()
    for row in rows:
        channel, grade = _text(row, "渠道"), _text(row, "年级")
        dimension = (channel, grade)
        if _text(row, "期次") != period or channel not in channels or dimension not in channel_grades:
            continue
        flag = _number(row, "异常流量标记")
        if flag < 0 or flag > 1:
            raise ValueError(f"异常流量标记不在0到1之间: {flag}")
        buckets[grade]["异常量"] += flag
        buckets[grade]["线索量"] += 1
        buckets[grade]["matched_dimensions"].add(dimension)
        observed_dimensions.add(dimension)
    missing = sorted(channel_grades - observed_dimensions)
    result = {grade: {
        "异常流量占比": _ratio(bucket["异常量"], bucket["线索量"]),
        "异常量": bucket["异常量"], "线索量": bucket["线索量"],
        "匹配渠道年级数": len(bucket["matched_dimensions"]),
    } for grade, bucket in buckets.items()}
    return result, {"expected_dimensions": len(channel_grades), "matched_dimensions": len(observed_dimensions),
                    "missing_dimensions": [{"渠道": c, "年级": g} for c, g in missing]}


def _fmt_number(number: float) -> str:
    return f"{number:,.0f}"


def _fmt_ratio(number: float | None) -> str:
    return "-" if number is None else f"{number:.2%}"


def build_total_row(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Recalculate total derived metrics from their additive components."""
    if not rows:
        raise ValueError("没有可用于生成总计行的年级数据")
    totals = {field: sum(float(row[field]) for row in rows)
              for field in ("预估量级", "实际进量", "_退前线索", "_退后线索", "_接量顾问数")}
    return {
        "期次": rows[0]["期次"], "年级": "总计",
        "预估量级": totals["预估量级"], "实际进量": totals["实际进量"],
        "线索留存率": _ratio(totals["_退后线索"], totals["_退前线索"]),
        "人均带班": _ratio(totals["实际进量"], totals["_接量顾问数"]),
        "量级完成度": _ratio(totals["实际进量"], totals["预估量级"]),
    }


def render_image(rows: list[dict[str, Any]], output: Path) -> dict[str, Any]:
    widths = (190, 120, 150, 150, 155, 145, 155)
    row_height, header_height = 68, 76
    rendered_rows = [*rows, build_total_row(rows)]
    width, height = sum(widths), header_height + row_height * len(rendered_rows)
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font, bold_font, header_font = _find_font(24), _find_font(24, True), _find_font(25, True)
    x = 0
    for column, cell_width in zip(IMAGE_COLUMNS, widths):
        draw.rectangle((x, 0, x + cell_width, header_height), fill=REPORT_COLORS["header"],
                       outline=REPORT_COLORS["grid"], width=1)
        _center_text(draw, (x, 0, x + cell_width, header_height), column, header_font,
                     REPORT_COLORS["header_text"])
        x += cell_width
    for index, row in enumerate(rendered_rows):
        is_total = row["年级"] == "总计"
        top, x = header_height + index * row_height, 0
        for column, cell_width in zip(IMAGE_COLUMNS, widths):
            draw.rectangle((x, top, x + cell_width, top + row_height),
                           fill=REPORT_COLORS["header"] if is_total else REPORT_COLORS["body"],
                           outline=REPORT_COLORS["grid"], width=1)
            raw = row[column]
            if not is_total and column in REPORT_BAR_COLORS and raw is not None:
                bar_left, bar_top = x + 6, top + 9
                bar_right = bar_left + round((cell_width - 12) * max(0.0, min(1.0, raw)))
                if bar_right > bar_left:
                    draw.rectangle((bar_left, bar_top, bar_right, top + row_height - 9),
                                   fill=REPORT_BAR_COLORS[column])
            text = (_fmt_ratio(raw) if column in {"线索留存率", "量级完成度"}
                    else f"{raw:.2f}" if column == "人均带班" and raw is not None
                    else "-" if raw is None else _fmt_number(raw) if column in {"预估量级", "实际进量"}
                    else str(raw))
            _center_text(draw, (x, top, x + cell_width, top + row_height), text,
                         bold_font if is_total else font,
                         REPORT_COLORS["header_text"] if is_total else REPORT_COLORS["body_text"])
            x += cell_width
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG")
    return {"width": width, "height": height, "row_count": len(rows), "total_row_count": 1,
            "total_row": rendered_rows[-1], "sort": "年级固定升序，总计置底",
            "grade_order": list(REPORT_GRADE_ORDER), "progress_bar_fields": list(REPORT_BAR_COLORS),
            "progress_bar_colors": REPORT_BAR_COLORS, "colors": REPORT_COLORS}


def build_markdown(period: str, rows: list[dict[str, Any]], abnormal: Mapping[str, Mapping[str, Any]]) -> str:
    comparable = [row for row in rows if row["量级完成度"] is not None]
    if not comparable:
        raise ValueError("没有可用于识别量级完成度最低年级的数据")
    slowest = min(comparable, key=lambda row: (row["量级完成度"],
                                                GRADE_ORDER.get(row["年级"], len(GRADE_ORDER))))
    grade = slowest["年级"]
    lines = ["【KOC渠道】进量进度如下，辛苦各位老师知悉 ❤️", "![进量进度](img_volume_preview)",
             f"推送期次：{period}",
             f"重点关注量级进展较慢的年级：{grade}", ""]
    for row in rows:
        row_grade = row["年级"]
        lines.append(f"{row_grade}异常流量占比：{_fmt_ratio(abnormal.get(row_grade, {}).get('异常流量占比'))}")
    return "\n".join(lines)


def _read_table(base_token: str, table_id: str, fields: tuple[str, ...], args: argparse.Namespace,
                filter_json: Mapping[str, Any] | None = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    audit: dict[str, Any] = {}
    rows = _fetch_view_records({"base_token": base_token, "table_id": table_id, "view_id": ""}, args, fields,
                               temp_prefix=".koc-volume-preview-", filter_json=filter_json, audit=audit)
    return rows, audit


def prepare_context(config: Mapping[str, Any], output_root: Path, *, timeout: int = 60) -> dict[str, Any]:
    """Build one production-ready message from two complete, revision-pinned Base reads."""
    spec = config["volume_report"]
    if spec.get("stage") != "scheduled":
        raise ValueError("进量报告未进入scheduled阶段")
    rule = spec.get("channel_rule", "")
    if rule not in CHANNEL_RULE_DESCRIPTIONS:
        raise ValueError("进量报告渠道规则未审核")
    cli_args = argparse.Namespace(base_as=config.get("base_as", config.get("base_identity", "user")),
                                  timeout=timeout, max_pages=100)
    volume_rows, volume_audit = _read_table(spec["base_token"], spec["volume_table_id"], VOLUME_FIELDS, cli_args)
    period = latest_period(volume_rows, rule)
    rows, channels, dimensions = aggregate_volume(volume_rows, period, rule)
    lead_filter = {"logic": "and", "conditions": [["期次", "==", period]]}
    lead_rows, lead_audit = _read_table(spec["base_token"], spec["lead_table_id"], LEAD_FIELDS, cli_args, lead_filter)
    abnormal, matching = aggregate_abnormal(lead_rows, period, channels, dimensions)
    if matching["missing_dimensions"]:
        raise ValueError("非零进量渠道年级在线索明细中缺失，拒绝发送不完整异常占比: " +
                         json.dumps(matching["missing_dimensions"], ensure_ascii=False))
    for label, audit in (("进量表", volume_audit), ("线索表", lead_audit)):
        if audit.get("has_more") is not False or audit.get("rev") is None:
            raise ValueError(f"{label}读取不完整或缺少版本号")
    output_root.mkdir(parents=True, exist_ok=True)
    run_dir = Path(tempfile.mkdtemp(prefix="volume-scheduled-", dir=output_root.resolve()))
    image_path = run_dir / f"进量数据_{period}_KOC渠道.png"
    render_image(rows, image_path)
    return {
        "report_kind": "volume", "report_profile": "volume", "channel": "KOC渠道进量",
        "period": period, "markdown": build_markdown(period, rows, abnormal),
        "image_path": None, "result_image_path": None, "volume_image_path": image_path,
        "raw_count": len(volume_rows), "raw_read_audit": volume_audit,
        "volume_read_audit": volume_audit, "lead_read_audit": lead_audit,
        "revision_sources": (
            {"table_id": spec["volume_table_id"], "field": "期次", "rev": volume_audit["rev"]},
            {"table_id": spec["lead_table_id"], "field": "期次", "rev": lead_audit["rev"]},
        ),
        "base_token": spec["base_token"], "channel_rule": rule, "channels": sorted(channels), "rows": rows,
        "abnormal_by_grade": abnormal, "dimension_matching": matching,
        "mention_info": {"resolved": {}}, "chat_id": config["chat_id"], "identity": "bot",
    }


def validate_scheduled_context(context: Mapping[str, Any], config: Mapping[str, Any]) -> None:
    if (context.get("report_kind") != "volume" or context.get("chat_id") != config["chat_id"]
            or context.get("identity") != "bot" or gr.mention_ids(context["markdown"])
            or not context.get("volume_image_path") or context.get("image_path")
            or context.get("result_image_path")):
        raise ValueError("invalid scheduled volume-report context")


def assert_current_revisions(context: Mapping[str, Any], config: Mapping[str, Any]) -> None:
    """Recheck both source revisions immediately before a scheduled send."""
    for source in context["revision_sources"]:
        with tempfile.TemporaryDirectory(prefix=".broadcast-volume-rev-") as folder:
            data = gp._unwrap(json.loads(gp.run_lark([
                "base", "+record-list", "--base-token", context["base_token"],
                "--table-id", source["table_id"], "--field-id", source["field"], "--limit", "1",
                "--output", "./revision.ndjson", "--format", "ndjson", "--as", config["base_as"]],
                cwd=folder, timeout=60)))
        if data.get("rev") != source["rev"]:
            raise ValueError("Base changed after volume snapshot; rebuild before sending")


def delivery_detail(context: Mapping[str, Any]) -> dict[str, Any]:
    return {"channels": context["channels"], "lead_rev": context["lead_read_audit"]["rev"]}


def generate_preview(config_path: Path, output_root: Path, *, timeout: int = 60) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    spec = config["volume_report"]
    if spec.get("stage") not in {"preview_only", "scheduled"}:
        raise ValueError("进量报告阶段无效，拒绝使用只读预览入口")
    rule = spec.get("channel_rule", "")
    if rule not in CHANNEL_RULE_DESCRIPTIONS:
        raise ValueError("进量报告渠道规则未审核")
    cli_args = argparse.Namespace(base_as=config.get("base_identity", "user"), timeout=timeout, max_pages=100)
    volume_rows, volume_audit = _read_table(spec["base_token"], spec["volume_table_id"], VOLUME_FIELDS, cli_args)
    period = latest_period(volume_rows, rule)
    rows, channels, dimensions = aggregate_volume(volume_rows, period, rule)
    lead_filter = {"logic": "and", "conditions": [["期次", "==", period]]}
    lead_rows, lead_audit = _read_table(spec["base_token"], spec["lead_table_id"], LEAD_FIELDS, cli_args, lead_filter)
    abnormal, matching = aggregate_abnormal(lead_rows, period, channels, dimensions)
    if matching["missing_dimensions"]:
        raise ValueError("非零进量渠道年级在线索明细中缺失，拒绝生成不完整异常占比: " +
                         json.dumps(matching["missing_dimensions"], ensure_ascii=False))
    output_root.mkdir(parents=True, exist_ok=True)
    run_dir = Path(tempfile.mkdtemp(prefix="volume-preview-", dir=output_root.resolve()))
    image_path = run_dir / f"进量数据_{period}_KOC渠道.png"
    geometry = render_image(rows, image_path)
    markdown = build_markdown(period, rows, abnormal)
    metadata = {
        "mode": "preview_only", "message_sent": False, "schedule_changed": False, "period": period,
        "channel_rule": rule, "channel_rule_description": CHANNEL_RULE_DESCRIPTIONS[rule],
        "regular_report_channels": list(config.get("channels", [config.get("channel")])),
        "channels": sorted(channels),
        "rows": rows, "abnormal_by_grade": abnormal, "dimension_matching": matching,
        "formula_contract": {"线索留存率": "Σ退后线索/Σ退前线索", "人均带班": "Σ实际进量/Σ接量顾问数",
                             "量级完成度": "Σ实际进量/Σ预估量级", "异常流量占比": "Σ异常流量标记/匹配明细线索数"},
        "source": {"base_token": spec["base_token"], "volume_table_id": spec["volume_table_id"],
                   "volume_table_name": spec["volume_table_name"], "lead_table_id": spec["lead_table_id"],
                   "lead_table_name": spec["lead_table_name"], "volume_read_audit": volume_audit,
                   "lead_read_audit": lead_audit},
        "image_geometry": geometry, "image_file": str(image_path), "markdown": markdown,
    }
    markdown_path, metadata_path, html_path = (run_dir / "message-preview.md", run_dir / "preview-metadata.json",
                                                run_dir / "message-preview.html")
    markdown_path.write_text(markdown + "\n", encoding="utf-8")
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    escaped = html.escape(markdown).replace("![进量进度](img_volume_preview)",
        f'<img src="{html.escape(image_path.name)}" alt="进量进度">').replace("\n", "<br>")
    document = f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>KOC进量预览</title>
<style>body{{margin:0;background:#f2f3f5;font:16px/1.65 'Microsoft YaHei',sans-serif;color:#1f2329}}main{{max-width:1180px;margin:32px auto}}.note{{background:#fff4e8;border:1px solid #ffd6a3;padding:14px 18px;border-radius:10px;margin-bottom:18px}}.chat{{background:white;padding:24px;border-radius:12px;box-shadow:0 4px 20px #0001}}.sender{{color:#646a73;margin-bottom:8px}}.bubble{{display:inline-block;max-width:1080px;background:#f5f6f7;border-radius:4px 14px 14px;padding:16px}}img{{display:block;max-width:100%;margin:12px 0;border:1px solid #d9dfe8}}</style>
<body><main><div class="note"><b>仅本地预览</b>：未发送消息，未修改任务计划。指标均按年级先汇总分子/分母后计算。</div><div class="chat"><div class="sender">管家 · 消息样式预览</div><div class="bubble">{escaped}</div></div></main></body></html>'''
    html_path.write_text(document, encoding="utf-8")
    return {"html": str(html_path), "markdown": str(markdown_path), "metadata": str(metadata_path), "image": str(image_path)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="生成KOC进量消息的只读本地预览；不会发送消息")
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--timeout", type=int, default=60)
    args = parser.parse_args(argv)
    result = generate_preview(Path(args.config).expanduser().resolve(), Path(args.output_root).expanduser().resolve(),
                              timeout=args.timeout)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
