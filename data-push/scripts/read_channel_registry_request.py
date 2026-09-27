"""Read one operator intake from the channel registry Base.

This command is intentionally read-only.  It converts the business-facing
record into a reviewable candidate specification; it never edits production
channel files, registers tasks, enables schedules, or sends messages.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping, Sequence


SKILL_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_CONFIG = SKILL_ROOT / "config" / "channel_registry_base.json"
DOMAIN_BY_DEPARTMENT = {
    "市场顾问部": "market_consultant",
    "青橙项目部": "qingcheng",
}
CANDIDATE_FIELDS = (
    "申请编号", "申请状态", "申请部门", "渠道标准名称", "原始渠道示例",
    "数据源链接", "原始表名称", "目标群", "目标群名称（备用）", "期次规则",
    "过程数据星期", "转化数据星期", "期望首次上线日期", "期望推送时段",
    "数据维度", "年级范围", "其他范围或排除规则", "展示门槛指标",
    "门槛运算符", "门槛值", "过程指标（逐项勾选）", "其他过程指标（每行一项）",
    "过程指标展示顺序（选填）", "转化指标（逐项勾选）", "其他转化指标（每行一项）",
    "转化指标展示顺序（选填）", "指标口径补充（每行一项）", "图片分组与排版",
    "颜色或样式参考", "过程重点提醒指标", "转化重点提醒指标", "提醒对象",
    "过程指标提醒方向", "转化指标提醒方向", "并列处理",
    "播报层级", "过程文字提醒名次", "转化文字提醒名次",
)


def _single(value: Any) -> Any:
    if isinstance(value, list) and len(value) == 1 and not isinstance(value[0], Mapping):
        return value[0]
    return value


def _list(value: Any) -> list[Any]:
    if value in (None, ""):
        return []
    return list(value) if isinstance(value, list) else [value]


def _chat_id(value: Any) -> str:
    for item in _list(value):
        if isinstance(item, Mapping) and item.get("id"):
            return str(item["id"])
    return ""


def _url(value: Any) -> Any:
    """Normalize Base URL values while preserving non-string payloads."""
    if not isinstance(value, str):
        return value
    text = value.strip()
    if text.startswith("[") and "](" in text and text.endswith(")"):
        return text.split("](", 1)[1][:-1]
    return text


def build_candidate(fields: Mapping[str, Any], *, record_id: str) -> dict[str, Any]:
    """Build a stable, review-only candidate from one operator record."""
    department = str(_single(fields.get("申请部门")) or "")
    process_metrics = [str(item) for item in _list(fields.get("过程指标（逐项勾选）"))]
    result_metrics = [str(item) for item in _list(fields.get("转化指标（逐项勾选）"))]
    required = {
        "申请编号": fields.get("申请编号"),
        "申请部门": department,
        "渠道标准名称": fields.get("渠道标准名称"),
        "数据源链接": _url(fields.get("数据源链接")),
        "原始表名称": fields.get("原始表名称"),
        "目标群": _chat_id(fields.get("目标群")),
        "期次规则": _single(fields.get("期次规则")),
        "数据维度": _list(fields.get("数据维度")),
    }
    missing = [name for name, value in required.items() if value in (None, "", [])]
    if not process_metrics and not result_metrics:
        missing.append("过程指标（逐项勾选）或转化指标（逐项勾选）")

    return {
        "schema_version": 1,
        "source": {
            "system": "lark_base",
            "operator_record_id": record_id,
            "request_id": str(fields.get("申请编号") or ""),
            "request_status": _single(fields.get("申请状态")),
        },
        "routing": {
            "department": department,
            "domain": DOMAIN_BY_DEPARTMENT.get(department),
            "execution_surface": None,
            "channel_id": None,
        },
        "business": {
            "channel_name": fields.get("渠道标准名称"),
            "source_channel_examples": fields.get("原始渠道示例"),
            "data_source_url": _url(fields.get("数据源链接")),
            "raw_table_name": fields.get("原始表名称"),
            "target_chat_id": _chat_id(fields.get("目标群")),
            "target_chat_name": fields.get("目标群名称（备用）"),
            "period_rule": _single(fields.get("期次规则")),
            "process_weekdays": _list(fields.get("过程数据星期")),
            "result_weekdays": _list(fields.get("转化数据星期")),
            "requested_first_send_at": fields.get("期望首次上线日期"),
            "requested_send_windows": fields.get("期望推送时段"),
            "dimensions": _list(fields.get("数据维度")),
            "grades": _list(fields.get("年级范围")),
            "scope_notes": fields.get("其他范围或排除规则"),
        },
        "report": {
            "minimum": {
                "metric": fields.get("展示门槛指标"),
                "operator": _single(fields.get("门槛运算符")),
                "value": fields.get("门槛值"),
            },
            "process_metrics": process_metrics,
            "other_process_metrics": fields.get("其他过程指标（每行一项）"),
            "process_display_order": fields.get("过程指标展示顺序（选填）"),
            "result_metrics": result_metrics,
            "other_result_metrics": fields.get("其他转化指标（每行一项）"),
            "result_display_order": fields.get("转化指标展示顺序（选填）"),
            "metric_definitions": fields.get("指标口径补充（每行一项）"),
            "layout": fields.get("图片分组与排版"),
            "style_reference": fields.get("颜色或样式参考"),
        },
        "reminder": {
            "process_metric": _single(fields.get("过程重点提醒指标")),
            "result_metric": _single(fields.get("转化重点提醒指标")),
            "target": _single(fields.get("提醒对象")),
            "process_direction": _single(fields.get("过程指标提醒方向")),
            "result_direction": _single(fields.get("转化指标提醒方向")),
            "tie_handling": _single(fields.get("并列处理")),
            "report_level": _single(fields.get("播报层级")),
            "process_rank": _single(fields.get("过程文字提醒名次")),
            "result_rank": _single(fields.get("转化文字提醒名次")),
        },
        "validation": {
            "complete_for_technical_review": not missing,
            "missing_business_fields": missing,
            "technical_decisions_required": [
                "execution_surface",
                "channel_id",
                "adapter/report_profile",
                "source field mapping and metric formulas",
                "sender identity IDs",
                "local paths and state directory",
                "schedule staggering and task name",
                "upstream version gates",
            ],
        },
    }


def _field_names() -> list[str]:
    return list(CANDIDATE_FIELDS)


def _run_lark(args: Sequence[str]) -> dict[str, Any]:
    env = os.environ.copy()
    env["LARKSUITE_CLI_NO_UPDATE_NOTIFIER"] = "1"
    env["LARKSUITE_CLI_NO_SKILLS_NOTIFIER"] = "1"
    completed = subprocess.run(
        ["lark-cli", *args],
        text=True,
        encoding="utf-8",
        capture_output=True,
        env=env,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    payload = json.loads(completed.stdout)
    if not payload.get("ok"):
        raise RuntimeError(json.dumps(payload.get("error", payload), ensure_ascii=False))
    return payload


def _rows(payload: Mapping[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    data = payload.get("data", {}).get("data", [])
    names = payload.get("data", {}).get("fields", [])
    record_ids = payload.get("data", {}).get("record_id_list", [])
    return [
        (str(record_id), dict(zip(names, values)))
        for record_id, values in zip(record_ids, data)
    ]


def read_request(*, record_id: str | None, request_id: str | None) -> dict[str, Any]:
    registry = json.loads(REGISTRY_CONFIG.read_text(encoding="utf-8"))
    base_token = registry["base_token"]
    table_id = registry["tables"]["operator"]["table_id"]
    fields = _field_names()
    projection = [item for name in fields for item in ("--field-id", name)]
    if record_id:
        payload = _run_lark([
            "base", "+record-get", "--base-token", base_token,
            "--table-id", table_id, "--record-id", record_id,
            *projection, "--format", "json", "--as", "user",
        ])
        rows = _rows(payload)
    else:
        payload = _run_lark([
            "base", "+record-search", "--base-token", base_token,
            "--table-id", table_id, "--keyword", str(request_id),
            "--search-field", "申请编号", *projection,
            "--limit", "20", "--format", "json", "--as", "user",
        ])
        rows = [(rid, row) for rid, row in _rows(payload)
                if str(row.get("申请编号") or "") == str(request_id)]
    if len(rows) != 1:
        raise RuntimeError(f"expected exactly one operator record, found {len(rows)}")
    rid, fields_by_name = rows[0]
    candidate = build_candidate(fields_by_name, record_id=rid)
    candidate["source"]["base_token"] = base_token
    candidate["source"]["table_id"] = table_id
    return candidate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--record-id")
    target.add_argument("--request-id")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        candidate = read_request(record_id=args.record_id, request_id=args.request_id)
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    output = json.dumps(candidate, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
