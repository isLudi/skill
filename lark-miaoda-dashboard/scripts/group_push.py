#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Push process-data snapshots from a Feishu Base view to a group.

This is intentionally a local, CLI-orchestrated workflow.  It keeps the
boundaries between the official skills visible in the code:

* ``base +record-list`` reads one named view with a minimum projection;
* ``contact +search-user`` resolves exact names before an @ mention;
* the independent ``推送文字`` table supplies title/period/explanation/reminders;
* ``IP播报_主管 / 结果数据`` supplies a second, already-aggregated result image;
  no result calculation is written back to ``IP原始数据``;
* ``im images create`` uploads the generated process/result images only for a real send;
* ``im +messages-send`` sends one Markdown post with a stable idempotency key.
* after a verified real delivery, the generated local PNG is removed; a failed
  final send keeps it available for retry.

The default operation is ``preview``.  ``send`` requires
``--confirm-send`` and records the returned message_id in an append-only local
ledger.  The process image keeps its explicit process-only whitelist.  The
result image is a separate, explicitly selected view and may contain outcome
metrics such as single effect and net receipts.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import parse_qs, urlparse


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from lark_runtime import run_lark  # noqa: E402


try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except AttributeError:
    pass


# The whitelist is deliberately explicit.  In particular, no 收款、成交、退费、
# 单效、订单 or other outcome field is allowed to enter the message.
PROCESS_FIELDS: tuple[str, ...] = (
    "期次",
    "顾问",
    "主管",
    "部门",
    "渠道",
    "退前线索",
    "退后线索",
    "线索留存率",
    "总通时",
    "首call完成数",
    "首call率",
    "6h外呼",
    "12h外呼",
    "24h外呼",
    "48h外呼",
    "48h外呼数",
    "外呼频次",
    "外呼次数",
    "5min",
    "5min线索数",
    "好友率",
    "好友线索数",
    "APP登陆率",
    "APP登陆线索数",
    "深沟率",
    "深沟线索数",
    "双沟率",
    "双沟线索数",
)

TEXT_FIELDS: tuple[str, ...] = (
    "说明",
    "推送标题",
    "推送期次",
    "推送说明",
    "计算_提醒顾问",
    "提醒",
)

TEXT_SECTION_ORDER: tuple[str, ...] = ("过程数据", "结果数据")

HELPER_RAW_FIELDS: tuple[str, ...] = ("期次", "顾问", "主管", "渠道")
HELPER_DIMENSION_FIELDS: tuple[str, ...] = ("维度键", "顾问", "主管", "渠道")

# Result data is read from the already-aggregated ``IP播报_主管 / 结果数据``
# view.  Keeping this projection separate from PROCESS_FIELDS is intentional:
# outcome fields must not leak into the process section, while the result
# section is explicitly allowed to show the business result metrics.
RESULT_FIELDS: tuple[str, ...] = (
    "期次",
    "经理",
    "主管",
    "顾问",
    "渠道",
    "退前线索",
    "退后线索",
    "线索留存率",
    "首call率",
    "48h外呼",
    "5min",
    "好友率",
    "深沟率",
    "双沟率",
    "首节到课率",
    "单效（当期）",
    "人均报科",
    "人头转化",
    "订单转化",
    "收款",
    "退费",
    "退费率",
    "净收款",
    "单效",
    "报科数",
    "成交人头",
    "当期净收款",
    "当期报科数",
    "当期成交人头",
)

RESULT_IMAGE_COLUMNS: tuple[tuple[str, str, str], ...] = (
    ("期次", "期", "text"),
    ("经理", "经理", "text"),
    ("主管", "主管", "text"),
    ("退前线索", "退前线索", "count"),
    ("退后线索", "退后线索", "count"),
    ("线索留存率", "线索留存率", "rate"),
    ("首call率", "首call率", "rate"),
    ("48h外呼", "48h外呼", "rate"),
    ("5min", "5min", "rate"),
    ("好友率", "好友率", "rate"),
    ("深沟率", "深沟率", "rate"),
    ("双沟率", "双沟率", "rate"),
    ("首节到课率", "首节到课率", "rate"),
    ("单效（当期）", "单效(当期)", "number"),
    ("人均报科", "人均报科", "number"),
    ("人头转化", "人头转化", "rate"),
    ("订单转化", "订单转化", "rate"),
    ("净收款", "净收款", "amount"),
    ("退费率", "退费率", "rate"),
    ("单效", "单效", "number"),
)

RESULT_RATE_DENOMINATORS: dict[str, str] = {
    "线索留存率": "退前线索",
    "首call率": "退后线索",
    "48h外呼": "退后线索",
    "5min": "退后线索",
    "好友率": "退后线索",
    "深沟率": "退后线索",
    "双沟率": "退后线索",
    "首节到课率": "退后线索",
    "人头转化": "退后线索",
    "订单转化": "退后线索",
}

RESULT_SUM_FIELDS: tuple[str, ...] = (
    "退前线索",
    "退后线索",
    "收款",
    "退费",
    "净收款",
    "报科数",
    "成交人头",
    "当期净收款",
    "当期报科数",
    "当期成交人头",
)

RESULT_BAR_FIELDS: dict[str, str] = {
    "首call率": "#4f78ae",
    "5min": "#62bc7f",
    "双沟率": "#138de2",
    "人均报科": "#f5ae23",
    "退费率": "#fb5a68",
}

RESULT_IMAGE_WIDTHS: dict[str, int] = {
    "期次": 140,
    "经理": 180,
    "主管": 180,
    "退前线索": 155,
    "退后线索": 155,
    "线索留存率": 190,
    "首call率": 150,
    "48h外呼": 150,
    "5min": 150,
    "好友率": 150,
    "深沟率": 150,
    "双沟率": 150,
    "首节到课率": 170,
    "单效（当期）": 185,
    "人均报科": 180,
    "人头转化": 165,
    "订单转化": 165,
    "净收款": 175,
    "退费率": 150,
    "单效": 155,
}

IMAGE_COLUMNS: tuple[tuple[str, str, str], ...] = (
    ("期次", "期次", "text"),
    ("顾问", "负责人", "text"),
    ("主管", "主管", "text"),
    ("退前线索", "退前线索", "count"),
    ("退后线索", "退后线索", "count"),
    ("线索留存率", "线索留存率", "rate"),
    ("总通时", "总通时", "duration"),
    ("首call率", "首call", "rate"),
    ("6h外呼", "6h外呼", "rate"),
    ("12h外呼", "12h外呼", "rate"),
    ("24h外呼", "24h外呼", "rate"),
    ("48h外呼", "48h外呼", "rate"),
    ("外呼频次", "外呼频次", "frequency"),
    ("5min", "5min比例", "rate"),
    ("好友率", "好友率", "rate"),
    ("APP登陆率", "APP登录率", "rate"),
    ("深沟率", "深沟率", "rate"),
    ("双沟率", "双沟率", "rate"),
)

FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "顾问": ("顾问", "负责人"),
    "APP登陆率": ("APP登陆率", "APP登录率"),
    "APP登陆线索数": ("APP登陆线索数", "APP登录线索数"),
    "5min": ("5min", "5min比例"),
}

RATE_NUMERATORS: dict[str, tuple[str, str]] = {
    "线索留存率": ("退后线索", "退前线索"),
    "首call率": ("首call完成数", "退后线索"),
    "48h外呼": ("48h外呼数", "退后线索"),
    "5min": ("5min线索数", "退后线索"),
    "好友率": ("好友线索数", "退后线索"),
    "APP登陆率": ("APP登陆线索数", "退后线索"),
    "深沟率": ("深沟线索数", "退后线索"),
    "双沟率": ("双沟线索数", "退后线索"),
}

RATE_FIELDS = {source for source, _label, kind in IMAGE_COLUMNS if kind == "rate"}
BAR_FIELDS = {
    "首call率": "#4f78ae",
    "5min": "#f5ae23",
    "双沟率": "#138de2",
}

IMAGE_WIDTHS = {
    "期次": 155,
    "顾问": 175,
    "主管": 155,
    "退前线索": 155,
    "退后线索": 155,
    "线索留存率": 200,
    "总通时": 155,
    "首call率": 160,
    "6h外呼": 155,
    "12h外呼": 155,
    "24h外呼": 155,
    "48h外呼": 155,
    "外呼频次": 140,
    "5min": 175,
    "好友率": 170,
    "APP登陆率": 195,
    "深沟率": 165,
    "双沟率": 165,
}

OUTCOME_TERMS = ("收款", "成交", "退费", "单效", "订单", "支付", "营收", "收入", "GMV")


def _json_payload(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError("lark-cli 未返回可解析的 JSON: %s" % text[-500:]) from exc


def _unwrap(payload: Any) -> Any:
    """Accept both the CLI envelope and raw manifest responses."""

    if isinstance(payload, Mapping) and payload.get("ok") is False:
        raise RuntimeError("lark-cli 返回失败: %s" % payload.get("error", payload))
    if isinstance(payload, Mapping) and "data" in payload and payload.get("ok") is True:
        return payload["data"]
    return payload


def _iter_dicts(value: Any) -> Iterable[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        yield value
        for nested in value.values():
            yield from _iter_dicts(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _iter_dicts(nested)


def _find_first(value: Any, keys: Sequence[str]) -> Any:
    wanted = set(keys)
    for item in _iter_dicts(value):
        for key in wanted:
            if key in item and item[key] not in (None, ""):
                return item[key]
    return None


def _string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, list):
        return ", ".join(_string(item) for item in value if _string(item))
    if isinstance(value, Mapping):
        for key in ("text", "value", "name", "display_name", "localized_name"):
            if key in value and value[key] not in (None, ""):
                return _string(value[key])
    return str(value).strip()


def _raw_field(row: Mapping[str, Any], field: str) -> Any:
    fields = row.get("fields", row)
    if not isinstance(fields, Mapping):
        return None
    for candidate in FIELD_ALIASES.get(field, (field,)):
        if candidate in fields:
            return fields[candidate]
    return None


def _number(value: Any) -> float | None:
    text = _string(value).replace(",", "")
    if not text or text in {"-", "—", "/", "N/A", "null"}:
        return None
    is_percent = text.endswith("%")
    if is_percent:
        text = text[:-1].strip()
    try:
        number = float(text)
    except ValueError:
        return None
    if is_percent:
        number /= 100.0
    return number


def _rate(value: Any) -> float | None:
    text = _string(value)
    number = _number(value)
    if number is None:
        return None
    # ``_number`` already converts a value carrying a literal ``%`` suffix.
    # Do not normalize it a second time: a legitimate refund rate such as
    # ``406.7%`` must remain 4.067 rather than becoming 4.07%.
    if text.endswith("%"):
        return number
    # Formula exports sometimes return 0.7398 and sometimes 73.98.
    if abs(number) > 1.0:
        number /= 100.0
    return number


def _format_rate(value: Any) -> str:
    number = _rate(value)
    if number is None:
        return _string(value)
    return "%.2f%%" % (number * 100)


def _format_value(value: Any, kind: str) -> str:
    if kind == "rate":
        return _format_rate(value)
    if kind == "count":
        number = _number(value)
        return str(int(round(number))) if number is not None else _string(value)
    if kind == "duration":
        number = _number(value)
        return str(int(round(number))) if number is not None else _string(value)
    if kind == "frequency":
        number = _number(value)
        return "%.1f" % number if number is not None else _string(value)
    if kind == "number":
        number = _number(value)
        return "%.2f" % number if number is not None else _string(value)
    if kind == "amount":
        number = _number(value)
        if number is None:
            return _string(value)
        if abs(number - round(number)) < 1e-9:
            return str(int(round(number)))
        return "%.2f" % number
    return _string(value)


def _safe_period(value: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z_-]+", "", value)
    return cleaned or "period"


def _source_fields() -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for field in PROCESS_FIELDS:
        # Fetch canonical names only; aliases are for reading copied views that
        # use the display spelling, not for making a request with unknown names.
        if field not in seen:
            result.append(field)
            seen.add(field)
    return result


def resolve_coordinates(args: argparse.Namespace) -> dict[str, str]:
    base_token = (args.base_token or "").strip()
    table_id = (args.table_id or "").strip()
    view_id = (args.view_id or "").strip()
    source_url = (args.source_url or "").strip()
    resolved: Any = None
    if source_url and (not base_token or not table_id or not view_id):
        resolved = _unwrap(
            _json_payload(
                run_lark(
                    [
                        "base",
                        "+url-resolve",
                        "--url",
                        source_url,
                        "--format",
                        "json",
                        "--as",
                        args.base_as,
                    ],
                    timeout=args.timeout,
                )
            )
        )
        base_token = base_token or _string(_find_first(resolved, ("base_token", "baseToken")))
        table_id = table_id or _string(_find_first(resolved, ("table_id", "tableId")))
        view_id = view_id or _string(_find_first(resolved, ("view_id", "viewId")))

        query = parse_qs(urlparse(source_url).query)
        table_id = table_id or (query.get("table", [""])[0] or "")
        view_id = view_id or (query.get("view", [""])[0] or "")

    if not base_token or not table_id or not view_id:
        raise SystemExit(
            "数据源坐标不完整：请设置 BASE_TOKEN、TABLE_ID、VIEW_ID，"
            "或提供 --source-url 让 lark-cli base +url-resolve 解析"
        )
    return {
        "base_token": base_token,
        "table_id": table_id,
        "view_id": view_id,
        "source_url": source_url,
    }


def resolve_text_coordinates(args: argparse.Namespace, source_coords: Mapping[str, str]) -> dict[str, str]:
    """Resolve the independent message-config table in the same Base."""

    base_token = _string(source_coords.get("base_token"))
    table_id = _string(getattr(args, "text_table_id", ""))
    view_id = _string(getattr(args, "text_view_id", ""))
    source_url = _string(getattr(args, "text_source_url", ""))
    if source_url and (not table_id or not view_id):
        resolved = _unwrap(
            _json_payload(
                run_lark(
                    [
                        "base",
                        "+url-resolve",
                        "--url",
                        source_url,
                        "--format",
                        "json",
                        "--as",
                        args.base_as,
                    ],
                    timeout=args.timeout,
                )
            )
        )
        resolved_base = _string(_find_first(resolved, ("base_token", "baseToken")))
        if resolved_base and base_token and resolved_base != base_token:
            raise SystemExit("推送文字表必须与过程数据表位于同一个 Base")
        table_id = table_id or _string(_find_first(resolved, ("table_id", "tableId")))
        view_id = view_id or _string(_find_first(resolved, ("view_id", "viewId")))
        query = parse_qs(urlparse(source_url).query)
        table_id = table_id or (query.get("table", [""])[0] or "")
        view_id = view_id or (query.get("view", [""])[0] or "")

    if not table_id or not view_id:
        raise SystemExit(
            "推送文字坐标不完整：请设置 --text-table-id、--text-view-id，"
            "或提供 --text-source-url"
        )
    return {
        "base_token": base_token,
        "table_id": table_id,
        "view_id": view_id,
        "source_url": source_url,
    }


def _fetch_view_records(
    coords: Mapping[str, str],
    args: argparse.Namespace,
    fields: Sequence[str],
    *,
    temp_prefix: str,
) -> list[dict[str, Any]]:
    """Read a complete selected view with a minimum field projection."""

    records: list[dict[str, Any]] = []
    offset = 0
    page_no = 0
    with tempfile.TemporaryDirectory(prefix=temp_prefix) as temp_dir:
        page_dir = Path(temp_dir)
        while True:
            page_no += 1
            page_file = page_dir / "page.ndjson"
            command: list[str] = [
                "base",
                "+record-list",
                "--base-token",
                coords["base_token"],
                "--table-id",
                coords["table_id"],
                "--limit",
                "2000",
                "--offset",
                str(offset),
                "--format",
                "ndjson",
                "--output",
                "./page.ndjson",
                "--overwrite",
                "--as",
                args.base_as,
            ]
            if coords.get("view_id"):
                command[6:6] = ["--view-id", coords["view_id"]]
            for field in fields:
                command.extend(("--field-id", field))
            manifest = _unwrap(_json_payload(run_lark(command, cwd=str(page_dir), timeout=args.timeout)))
            if not page_file.exists():
                raise RuntimeError("record-list 没有生成 NDJSON 文件: %s" % page_file)
            page_rows = [
                _json_payload(line)
                for line in page_file.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            records.extend(row for row in page_rows if isinstance(row, dict))
            count = int(manifest.get("records_count", len(page_rows)) or 0) if isinstance(manifest, Mapping) else len(page_rows)
            has_more = bool(manifest.get("has_more")) if isinstance(manifest, Mapping) else False
            if not has_more:
                break
            if count <= 0:
                raise RuntimeError("record-list 返回 has_more=true 但本页没有记录，停止避免死循环")
            offset += count
            if page_no >= args.max_pages:
                raise RuntimeError("record-list 超过 --max-pages=%d，未完成分页" % args.max_pages)
    return records


def fetch_records(coords: Mapping[str, str], args: argparse.Namespace) -> list[dict[str, Any]]:
    """Read the complete process-data view."""

    return _fetch_view_records(coords, args, _source_fields(), temp_prefix=".ip-process-pages-")


def fetch_result_records(coords: Mapping[str, str], args: argparse.Namespace) -> list[dict[str, Any]]:
    """Read the complete, already-aggregated result-data view."""

    return _fetch_view_records(coords, args, RESULT_FIELDS, temp_prefix=".ip-result-pages-")


def fetch_text_records(coords: Mapping[str, str], args: argparse.Namespace) -> list[dict[str, Any]]:
    """Read the complete ``推送文字`` view with only message fields."""

    return _fetch_view_records(coords, args, TEXT_FIELDS, temp_prefix=".ip-text-pages-")


def select_period(records: Sequence[Mapping[str, Any]], requested: str | None) -> str:
    periods = sorted({_string(_raw_field(row, "期次")) for row in records if _string(_raw_field(row, "期次"))})
    if requested:
        if periods and requested not in periods:
            raise SystemExit("指定期次 %s 不在当前视图中；当前期次：%s" % (requested, ", ".join(periods)))
        return requested
    if len(periods) > 1:
        raise SystemExit("当前视图包含多个期次：%s；请用 --period 精确指定" % ", ".join(periods))
    if periods:
        return periods[0]
    raise SystemExit("当前视图记录没有 期次 字段值；请用 --period 指定播报期次")


def select_rows(records: Sequence[Mapping[str, Any]], period: str) -> list[dict[str, Any]]:
    selected = []
    for row in records:
        if _string(_raw_field(row, "期次")) == period:
            fields = row.get("fields", row)
            selected.append({"record_id": row.get("record_id", ""), "fields": dict(fields) if isinstance(fields, Mapping) else {}})
    if not selected:
        raise SystemExit("期次 %s 没有可推送记录" % period)
    return selected


def reminder_names(row: Mapping[str, Any]) -> list[str]:
    """Return exact consultant names from the calculated reminder column."""

    calculated = _string(_raw_field(row, "计算_提醒顾问"))
    if not calculated:
        reminder = _string(_raw_field(row, "提醒"))
        if "：" in reminder:
            calculated = reminder.split("：", 1)[1]
        elif ":" in reminder:
            calculated = reminder.split(":", 1)[1]
    result: list[str] = []
    for item in re.split(r"[、,，;；\n]+", calculated):
        name = item.strip()
        if name and name not in result:
            result.append(name)
    return result


def select_text_config(
    records: Sequence[Mapping[str, Any]],
    period: str,
) -> dict[str, dict[str, Any]]:
    """Select one row per configured message section for the source period."""

    selected: dict[str, dict[str, Any]] = {}
    for row in records:
        if _string(_raw_field(row, "推送期次")) != period:
            continue
        section = _string(_raw_field(row, "说明"))
        if section not in TEXT_SECTION_ORDER:
            continue
        if section in selected:
            raise SystemExit("推送文字表中期次 %s 的%s存在重复配置行" % (period, section))
        fields = row.get("fields", row)
        selected[section] = {
            "record_id": row.get("record_id", ""),
            "fields": dict(fields) if isinstance(fields, Mapping) else {},
        }
    if "过程数据" not in selected:
        raise SystemExit("推送文字表没有期次 %s 的“过程数据”配置行" % period)
    return selected


def _load_mention_map(path: str | None) -> dict[str, str]:
    if not path:
        return {}
    data = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    if not isinstance(data, Mapping):
        raise SystemExit("--mention-map 必须是 JSON 对象，格式为 {\"姓名\": \"ou_xxx\"}")
    result: dict[str, str] = {}
    for name, value in data.items():
        open_id = value.get("open_id") if isinstance(value, Mapping) else value
        if isinstance(open_id, str) and open_id.startswith("ou_"):
            result[str(name)] = open_id
        else:
            raise SystemExit("--mention-map 中 %s 的 open_id 不是 ou_ 开头" % name)
    return result


def _user_candidates(payload: Any) -> list[Mapping[str, Any]]:
    seen: set[str] = set()
    result: list[Mapping[str, Any]] = []
    for item in _iter_dicts(payload):
        open_id = _string(item.get("open_id") or item.get("user_id"))
        if open_id and open_id.startswith("ou_") and open_id not in seen:
            seen.add(open_id)
            result.append(item)
    return result


def resolve_mentions(
    rows: Sequence[Mapping[str, Any]],
    *,
    mention_map: Mapping[str, str],
    no_lookup: bool,
    disable_mentions: bool = False,
    extra_names: Sequence[str] = (),
    timeout: int,
) -> dict[str, Any]:
    names = []
    for row in rows:
        for field in ("顾问", "主管"):
            name = _string(_raw_field(row, field))
            if name and name not in names:
                names.append(name)
    for name in extra_names:
        name = _string(name)
        if name and name not in names:
            names.append(name)
    resolved = {name: mention_map[name] for name in names if name in mention_map}
    unresolved = [name for name in names if name not in resolved]
    ambiguous: dict[str, list[str]] = {}
    lookup_error = ""
    if disable_mentions:
        return {
            "resolved": {},
            "unresolved": [],
            "ambiguous": {},
            "lookup_error": "",
            "names": names,
        }
    if unresolved and not no_lookup:
        try:
            for start in range(0, len(unresolved), 20):
                chunk = unresolved[start : start + 20]
                payload = _unwrap(
                    _json_payload(
                        run_lark(
                            [
                                "contact",
                                "+search-user",
                                "--queries",
                                ",".join(chunk),
                                "--lang",
                                "zh_cn",
                                "--format",
                                "json",
                                "--as",
                                "user",
                            ],
                            timeout=timeout,
                        )
                    )
                )
                users = _user_candidates(payload)
                for name in chunk:
                    exact = []
                    for user in users:
                        labels = {
                            _string(user.get("localized_name")),
                            _string(user.get("name")),
                            _string(user.get("real_name")),
                        }
                        if name in labels:
                            exact.append(user)
                    ids = sorted({_string(item.get("open_id") or item.get("user_id")) for item in exact})
                    if len(ids) == 1:
                        resolved[name] = ids[0]
                    elif len(ids) > 1:
                        ambiguous[name] = ids
        except Exception as exc:  # preview remains useful when contact scope is absent
            lookup_error = str(exc)
    unresolved = [name for name in names if name not in resolved]
    return {
        "resolved": resolved,
        "unresolved": unresolved,
        "ambiguous": ambiguous,
        "lookup_error": lookup_error,
        "names": names,
    }


def _mention(name: str, resolved: Mapping[str, str]) -> str:
    open_id = resolved.get(name)
    if not open_id:
        return html.escape(name)
    return '<at user_id="%s">%s</at>' % (html.escape(open_id, quote=True), html.escape(name))


def _display(row: Mapping[str, Any], field: str, kind: str | None = None) -> str:
    if kind is None:
        kind = next((item_kind for source, _label, item_kind in IMAGE_COLUMNS if source == field), "text")
    return _format_value(_raw_field(row, field), kind)


def available_image_columns(rows: Sequence[Mapping[str, Any]]) -> tuple[tuple[str, str, str], ...]:
    """Keep the reference layout, but omit unavailable optional source fields.

    The current ``IP播报_主管`` view has 48h外呼 but not 6h/12h/24h fields.
    Blank metric columns would look like a broken report, so those columns are
    rendered only when the selected view actually supplies at least one value.
    """

    optional = {"6h外呼", "12h外呼", "24h外呼"}
    result = []
    for spec in IMAGE_COLUMNS:
        source = spec[0]
        if source in optional and not any(_string(_raw_field(row, source)) not in {"", "-", "—"} for row in rows):
            continue
        result.append(spec)
    return tuple(result)


def _weighted_rate(rows: Sequence[Mapping[str, Any]], field: str) -> float | None:
    numerator_field, denominator_field = RATE_NUMERATORS.get(field, ("", ""))
    if numerator_field:
        numerator = sum(_number(_raw_field(row, numerator_field)) or 0.0 for row in rows)
        denominator = sum(_number(_raw_field(row, denominator_field)) or 0.0 for row in rows)
        if denominator:
            return numerator / denominator
    weighted = 0.0
    weight = 0.0
    for row in rows:
        value = _rate(_raw_field(row, field))
        denominator = _number(_raw_field(row, "退后线索")) or 0.0
        if value is not None and denominator > 0:
            weighted += value * denominator
            weight += denominator
    return weighted / weight if weight else None


def make_total_row(rows: Sequence[Mapping[str, Any]], period: str) -> dict[str, Any]:
    fields: dict[str, Any] = {"期次": "总计", "顾问": "", "主管": "", "部门": "", "渠道": ""}
    for field in ("退前线索", "退后线索", "总通时", "首call完成数", "48h外呼数", "外呼次数", "5min线索数", "好友线索数", "APP登陆线索数", "深沟线索数", "双沟线索数"):
        fields[field] = sum(_number(_raw_field(row, field)) or 0.0 for row in rows)
    for field in RATE_FIELDS:
        value = _weighted_rate(rows, field)
        fields[field] = value if value is not None else ""
    denominator = sum(_number(_raw_field(row, "退后线索")) or 0.0 for row in rows)
    calls = sum(_number(_raw_field(row, "外呼次数")) or 0.0 for row in rows)
    fields["外呼频次"] = calls / denominator if denominator else ""
    return {"record_id": "__total__", "fields": fields, "period": period}


def _sum_result_field(rows: Sequence[Mapping[str, Any]], field: str) -> float:
    return sum(_number(_raw_field(row, field)) or 0.0 for row in rows)


def _result_ratio(numerator: float, denominator: float) -> float | str:
    if not denominator:
        return ""
    # Keep the percent marker so values above 100% (for example a refund rate
    # after refunds exceed current receipts) are not normalized twice.
    return "%.6f%%" % (numerator / denominator * 100)


def _weighted_result_rate(rows: Sequence[Mapping[str, Any]], field: str) -> float | str:
    denominator_field = RESULT_RATE_DENOMINATORS.get(field)
    if not denominator_field:
        return ""
    denominator = _sum_result_field(rows, denominator_field)
    if not denominator:
        return ""
    weighted = 0.0
    observed = False
    for row in rows:
        value = _rate(_raw_field(row, field))
        weight = _number(_raw_field(row, denominator_field)) or 0.0
        if value is not None and weight > 0:
            weighted += value * weight
            observed = True
    return weighted / denominator if observed else ""


def _result_effect(rows: Sequence[Mapping[str, Any]], value_field: str, numerator_field: str) -> float | str:
    denominator = _sum_result_field(rows, "退后线索")
    numerator_values = [_number(_raw_field(row, numerator_field)) for row in rows]
    if denominator and any(value is not None for value in numerator_values):
        return sum(value or 0.0 for value in numerator_values) / denominator
    weighted = 0.0
    weight = 0.0
    for row in rows:
        value = _number(_raw_field(row, value_field))
        row_weight = _number(_raw_field(row, "退后线索")) or 0.0
        if value is not None and row_weight > 0:
            weighted += value * row_weight
            weight += row_weight
    return weighted / weight if weight else ""


def _result_group_key(row: Mapping[str, Any]) -> tuple[str, str]:
    """Use the two visible hierarchy columns as the result-image grain."""

    manager = _string(_raw_field(row, "经理"))
    supervisor = _string(_raw_field(row, "主管"))
    if not manager and not supervisor:
        # This fallback keeps malformed/legacy rows separate rather than
        # silently merging every blank-dimension row into one result.
        manager = _string(_raw_field(row, "顾问"))
        supervisor = _string(_raw_field(row, "渠道"))
    return manager, supervisor


def _aggregate_result_group(
    rows: Sequence[Mapping[str, Any]],
    period: str,
    manager: str,
    supervisor: str,
    *,
    record_id: str,
) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "期次": period,
        "经理": manager,
        "主管": supervisor,
        "顾问": "",
        "渠道": "",
    }
    for field in RESULT_SUM_FIELDS:
        fields[field] = _sum_result_field(rows, field)
    for field in RESULT_RATE_DENOMINATORS:
        fields[field] = _weighted_result_rate(rows, field)

    fields["单效（当期）"] = _result_effect(rows, "单效（当期）", "当期净收款")
    fields["单效"] = _result_effect(rows, "单效", "净收款")

    head_denominator = _sum_result_field(rows, "成交人头")
    if head_denominator:
        fields["人均报科"] = _sum_result_field(rows, "报科数") / head_denominator
    else:
        weighted = 0.0
        weight = 0.0
        for row in rows:
            value = _number(_raw_field(row, "人均报科"))
            row_weight = _number(_raw_field(row, "成交人头")) or 0.0
            if value is not None and row_weight > 0:
                weighted += value * row_weight
                weight += row_weight
        fields["人均报科"] = weighted / weight if weight else ""

    retained = _sum_result_field(rows, "退后线索")
    fields["人头转化"] = _result_ratio(_sum_result_field(rows, "成交人头"), retained)
    # This follows the existing IP播报_主管 field formula, which defines
    # 订单转化 from 报科数 rather than from 订单数.
    fields["订单转化"] = _result_ratio(_sum_result_field(rows, "报科数"), retained)
    fields["退费率"] = _result_ratio(_sum_result_field(rows, "退费"), _sum_result_field(rows, "收款"))
    return {"record_id": record_id, "fields": fields, "period": period}


def aggregate_result_rows(rows: Sequence[Mapping[str, Any]], period: str) -> list[dict[str, Any]]:
    """Merge result-view rows to the visible 经理 + 主管 grain."""

    groups: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
    for row in rows:
        groups.setdefault(_result_group_key(row), []).append(row)
    result = []
    for (manager, supervisor), group_rows in groups.items():
        key = "%s|%s" % (manager, supervisor)
        result.append(
            _aggregate_result_group(
                group_rows,
                period,
                manager,
                supervisor,
                record_id="__result_group__%s" % hashlib.sha256(key.encode("utf-8")).hexdigest()[:12],
            )
        )
    return sorted(
        result,
        key=lambda row: (
            _number(_raw_field(row, "单效")) is not None,
            _number(_raw_field(row, "单效")) or float("-inf"),
        ),
        reverse=True,
    )


def make_result_total_row(rows: Sequence[Mapping[str, Any]], period: str) -> dict[str, Any]:
    total = _aggregate_result_group(rows, period, "", "", record_id="__result_total__")
    total["fields"]["期次"] = "总计"
    return total


def _result_cell_fill(source: str, value: Any) -> str:
    if source == "线索留存率":
        return _retention_color(value)
    if source != "单效":
        return "#ffffff"
    number = _number(value)
    if number is None:
        return "#ffffff"
    if number < 0:
        return "#fb626b"
    if number < 50:
        return "#fa9a7e"
    if number < 100:
        return "#f9c777"
    if number < 200:
        return "#d9df83"
    return "#62bc7f"


def _result_bar_fraction(source: str, value: Any, rows: Sequence[Mapping[str, Any]]) -> float | None:
    if source == "人均报科":
        maximum = max((_number(_raw_field(row, source)) or 0.0 for row in rows), default=0.0)
        number = _number(value)
        return number / maximum if number is not None and maximum > 0 else None
    return _rate(value)


def render_result_image(rows: Sequence[Mapping[str, Any]], output_path: Path) -> Path:
    """Render the result-data reference layout as a second wide PNG."""

    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise RuntimeError("生成图片需要 Pillow；请在当前 D:\\anaconda3 环境安装 Pillow") from exc
    if not rows:
        raise SystemExit("结果数据视图没有可生成图片的记录")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    columns = RESULT_IMAGE_COLUMNS
    widths = [RESULT_IMAGE_WIDTHS[source] for source, _label, _kind in columns]
    header_height, row_height, total_height = 92, 64, 70
    width = sum(widths)
    height = header_height + row_height * len(rows) + total_height
    navy = "#203b72"
    grid = "#b8c4d3"
    image = Image.new("RGB", (width, height), "#ffffff")
    draw = ImageDraw.Draw(image)
    header_font = _find_font(27, bold=True)
    body_font = _find_font(25, bold=False)
    total_font = _find_font(28, bold=True)
    x_positions = [0]
    for column_width in widths:
        x_positions.append(x_positions[-1] + column_width)

    draw.rectangle((0, 0, width, header_height), fill=navy)
    for (_source, label, _kind), left, right in zip(columns, x_positions, x_positions[1:]):
        _center_text(draw, (left + 2, 0, right - 2, header_height), label, header_font, "#ffffff")
        draw.line((right - 1, 0, right - 1, height), fill=grid, width=1)
    draw.line((0, header_height - 1, width, header_height - 1), fill=grid, width=1)

    for row_index, row in enumerate(rows):
        top = header_height + row_index * row_height
        bottom = top + row_height
        for (source, _label, kind), left, right in zip(columns, x_positions, x_positions[1:]):
            value = _raw_field(row, source)
            draw.rectangle((left, top, right, bottom), fill=_result_cell_fill(source, value))
            if source in RESULT_BAR_FIELDS:
                fraction = _result_bar_fraction(source, value, rows)
                if fraction is not None:
                    bar_width = max(0, min(1, fraction)) * max(0, right - left - 12)
                    draw.rectangle(
                        (left + 6, top + 10, left + 6 + int(bar_width), bottom - 10),
                        fill=RESULT_BAR_FIELDS[source],
                    )
            text = _format_value(value, kind)
            _center_text(draw, (left + 2, top + 1, right - 2, bottom - 1), text, body_font, "#111827")
            draw.rectangle((left, top, right, bottom), outline=grid, width=1)

    total = make_result_total_row(rows, _string(_raw_field(rows[0], "期次")))
    total_top = header_height + row_height * len(rows)
    draw.rectangle((0, total_top, width, height), fill=navy)
    for (source, _label, kind), left, right in zip(columns, x_positions, x_positions[1:]):
        text = _format_value(_raw_field(total, source), kind)
        _center_text(draw, (left + 2, total_top + 1, right - 2, height - 1), text, total_font, "#ffffff")
        draw.rectangle((left, total_top, right, height), outline=grid, width=1)

    try:
        image.save(output_path, format="PNG", optimize=True)
    finally:
        image.close()
    return output_path


def _image_value(row: Mapping[str, Any], source: str, kind: str) -> str:
    if row.get("record_id") == "__total__" and kind == "rate":
        return _format_rate(_raw_field(row, source))
    return _display(row, source, kind)


def _find_font(size: int, bold: bool = False):
    try:
        from PIL import ImageFont
    except ImportError as exc:
        raise RuntimeError("生成图片需要 Pillow；请在当前 D:\\anaconda3 环境安装 Pillow") from exc
    candidates = (
        [
            r"C:\Windows\Fonts\msyhbd.ttc",
            r"C:\Windows\Fonts\simhei.ttf",
            r"C:\Windows\Fonts\simsunb.ttf",
        ]
        if bold
        else [
            r"C:\Windows\Fonts\msyh.ttc",
            r"C:\Windows\Fonts\simsun.ttc",
            r"C:\Windows\Fonts\simfang.ttf",
        ]
    )
    for candidate in candidates:
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def _center_text(draw: Any, box: tuple[int, int, int, int], text: str, font: Any, fill: str) -> None:
    left, top, right, bottom = box
    bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=2, align="center")
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    x = left + max(0, (right - left - width) // 2) - bbox[0]
    y = top + max(0, (bottom - top - height) // 2) - bbox[1]
    draw.multiline_text((x, y), text, font=font, fill=fill, spacing=2, align="center")


def _retention_color(value: Any) -> str:
    rate = _rate(value)
    if rate is None:
        return "#ffffff"
    if rate >= 0.88:
        return "#62bc7f"
    if rate >= 0.80:
        return "#d9df83"
    if rate >= 0.75:
        return "#f9c777"
    if rate >= 0.72:
        return "#fa9a7e"
    return "#fb626b"


def render_process_image(rows: Sequence[Mapping[str, Any]], output_path: Path) -> Path:
    """Render the requested navy-header, conditional-color table image."""

    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise RuntimeError("生成图片需要 Pillow；请在当前 D:\\anaconda3 环境安装 Pillow") from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)
    # These widths deliberately follow the supplied reference image's wide,
    # dense table layout rather than producing a narrow chart card.  Optional
    # 6h/12h/24h columns disappear when the source view does not contain them.
    columns = available_image_columns(rows)
    widths = [IMAGE_WIDTHS[source] for source, _label, _kind in columns]
    header_height, row_height, total_height = 92, 64, 70
    width = sum(widths)
    height = header_height + row_height * len(rows) + total_height
    navy = "#203b72"
    grid = "#b8c4d3"
    image = Image.new("RGB", (width, height), "#ffffff")
    draw = ImageDraw.Draw(image)
    header_font = _find_font(27, bold=True)
    body_font = _find_font(25, bold=False)
    total_font = _find_font(28, bold=True)

    x_positions = [0]
    for column_width in widths:
        x_positions.append(x_positions[-1] + column_width)

    draw.rectangle((0, 0, width, header_height), fill=navy)
    for index, ((_source, label, _kind), left, right) in enumerate(zip(columns, x_positions, x_positions[1:])):
        header = label
        _center_text(draw, (left + 2, 0, right - 2, header_height), header, header_font, "#ffffff")
        draw.line((right - 1, 0, right - 1, height), fill=grid, width=1)
    draw.line((0, header_height - 1, width, header_height - 1), fill=grid, width=1)

    for row_index, row in enumerate(rows):
        top = header_height + row_index * row_height
        bottom = top + row_height
        for col_index, ((source, _label, kind), left, right) in enumerate(zip(columns, x_positions, x_positions[1:])):
            value = _raw_field(row, source)
            if source == "线索留存率":
                draw.rectangle((left, top, right, bottom), fill=_retention_color(value))
            else:
                draw.rectangle((left, top, right, bottom), fill="#ffffff")
            if source in BAR_FIELDS:
                rate = _rate(value)
                if rate is not None:
                    bar_width = max(0, min(1, rate)) * max(0, right - left - 12)
                    draw.rectangle((left + 6, top + 10, left + 6 + int(bar_width), bottom - 10), fill=BAR_FIELDS[source])
            text = _image_value(row, source, kind)
            _center_text(draw, (left + 2, top + 1, right - 2, bottom - 1), text, body_font, "#111827")
            draw.rectangle((left, top, right, bottom), outline=grid, width=1)

    total = make_total_row(rows, _string(_raw_field(rows[0], "期次")))
    total_top = header_height + row_height * len(rows)
    draw.rectangle((0, total_top, width, height), fill=navy)
    for (source, _label, kind), left, right in zip(columns, x_positions, x_positions[1:]):
        text = _image_value(total, source, kind)
        _center_text(draw, (left + 2, total_top + 1, right - 2, height - 1), text, total_font, "#ffffff")
        draw.rectangle((left, total_top, right, height), outline=grid, width=1)

    try:
        image.save(output_path, format="PNG", optimize=True)
    finally:
        # ``image.save`` has completed before this point; explicitly close the
        # Pillow object so the pixel buffer is released before the caller
        # proceeds to upload or send the message.
        image.close()
    return output_path


def _render_configured_reminder(row: Mapping[str, Any], resolved: Mapping[str, str]) -> str:
    reminder = _string(_raw_field(row, "提醒"))
    if not reminder:
        return "无"
    rendered = html.escape(reminder)
    for name in sorted(reminder_names(row), key=len, reverse=True):
        escaped_name = html.escape(name)
        rendered = rendered.replace(escaped_name, _mention(name, resolved))
    return rendered


def _build_configured_markdown(
    *,
    period: str,
    source_label: str,
    text_sections: Mapping[str, Mapping[str, Any]],
    mention_info: Mapping[str, Any],
    image_ref: str | None,
    result_image_ref: str | None,
) -> str:
    resolved = mention_info.get("resolved", {})
    lines: list[str] = []
    for section in TEXT_SECTION_ORDER:
        row = text_sections.get(section)
        if not row:
            continue
        title = _string(_raw_field(row, "推送标题")) or ("IP%s" % section)
        configured_period = _string(_raw_field(row, "推送期次")) or period
        explanation = _string(_raw_field(row, "推送说明"))
        lines.extend(["## %s" % html.escape(title)])
        if section == "过程数据" and image_ref:
            lines.extend(["", "![IP过程数据表](%s)" % image_ref])
        if section == "结果数据" and result_image_ref:
            lines.extend(["", "![IP结果数据表](%s)" % result_image_ref])
        lines.extend(["", "- 推送期次：%s" % html.escape(configured_period)])
        if explanation:
            lines.append("- 推送说明：%s" % html.escape(explanation).replace("\n", "\n  "))
        lines.append("- 提醒：%s" % _render_configured_reminder(row, resolved))
    lines.extend(
        [
            "",
            "> 数据来源：%s" % html.escape(source_label),
            "> 结果图片来自 IP播报_主管 / 结果数据；提醒中的姓名仍按推送文字表计算并 @ 到人。",
        ]
    )
    return "\n".join(lines)


def build_markdown(
    rows: Sequence[Mapping[str, Any]],
    *,
    period: str,
    source_label: str,
    mention_info: Mapping[str, Any],
    image_ref: str | None,
    text_sections: Mapping[str, Mapping[str, Any]] | None = None,
    result_image_ref: str | None = None,
) -> str:
    if text_sections is not None:
        return _build_configured_markdown(
            period=period,
            source_label=source_label,
            text_sections=text_sections,
            mention_info=mention_info,
            image_ref=image_ref,
            result_image_ref=result_image_ref,
        )
    resolved = mention_info.get("resolved", {})
    lines = [
        "## IP过程数据播报｜%s" % period,
        "> 数据来源：%s" % source_label,
        "> 本消息仅推送过程数据，不含收款、成交、退费、单效等结果字段。",
    ]
    if image_ref:
        lines.extend(["", "![IP过程数据表](%s)" % image_ref])
    lines.extend(["", "### 明细数据（%d 条）" % len(rows)])
    for index, row in enumerate(rows, start=1):
        consultant = _string(_raw_field(row, "顾问"))
        supervisor = _string(_raw_field(row, "主管"))
        department = _string(_raw_field(row, "部门"))
        channel = _string(_raw_field(row, "渠道"))
        context = "｜".join(item for item in (department, channel) if item)
        title = "### %d. %s" % (index, context or consultant or supervisor or "过程数据")
        lines.append(title)
        lines.append("- 负责人：%s　主管：%s" % (_mention(consultant, resolved), _mention(supervisor, resolved)))
        lines.append(
            "- 退前线索：%s　退后线索：%s　线索留存率：%s"
            % (_display(row, "退前线索", "count"), _display(row, "退后线索", "count"), _display(row, "线索留存率", "rate"))
        )
        lines.append(
            "- 总通时：%s　首call：%s%s"
            % (
                _display(row, "总通时", "duration"),
                _display(row, "首call率", "rate"),
                "　外呼：" + " / ".join(
                    "%s=%s" % (label, _display(row, field, "rate"))
                    for field, label in (("6h外呼", "6h"), ("12h外呼", "12h"), ("24h外呼", "24h"), ("48h外呼", "48h"))
                    if _string(_raw_field(row, field)) not in {"", "-", "—"}
                ),
            )
        )
        lines.append(
            "- 外呼频次：%s　5min比例：%s　好友率：%s　APP登录率：%s　深沟率：%s　双沟率：%s"
            % (
                _display(row, "外呼频次", "frequency"),
                _display(row, "5min", "rate"),
                _display(row, "好友率", "rate"),
                _display(row, "APP登陆率", "rate"),
                _display(row, "深沟率", "rate"),
                _display(row, "双沟率", "rate"),
            )
        )
    total = make_total_row(rows, period)
    lines.extend(
        [
            "",
            "### 汇总",
            "- 退前线索：%s　退后线索：%s　线索留存率：%s　总通时：%s"
            % (
                _image_value(total, "退前线索", "count"),
                _image_value(total, "退后线索", "count"),
                _image_value(total, "线索留存率", "rate"),
                _image_value(total, "总通时", "duration"),
            ),
            "- 首call：%s　外呼频次：%s　5min比例：%s　好友率：%s　APP登录率：%s　深沟率：%s　双沟率：%s"
            % (
                _image_value(total, "首call率", "rate"),
                _image_value(total, "外呼频次", "frequency"),
                _image_value(total, "5min", "rate"),
                _image_value(total, "好友率", "rate"),
                _image_value(total, "APP登陆率", "rate"),
                _image_value(total, "深沟率", "rate"),
                _image_value(total, "双沟率", "rate"),
            ),
        ]
    )
    return "\n".join(lines)


def idempotency_key(
    coords: Mapping[str, str],
    chat_id: str,
    period: str,
    rows: Sequence[Mapping[str, Any]],
    *,
    text_coords: Mapping[str, str] | None = None,
    text_sections: Mapping[str, Mapping[str, Any]] | None = None,
    result_coords: Mapping[str, str] | None = None,
    result_rows: Sequence[Mapping[str, Any]] | None = None,
) -> str:
    stable_rows = []
    for row in rows:
        stable_rows.append(
            {
                "record_id": row.get("record_id", ""),
                "fields": {field: _string(_raw_field(row, field)) for field in PROCESS_FIELDS},
            }
        )
    canonical_payload: dict[str, Any] = {
        "base": coords["base_token"],
        "table": coords["table_id"],
        "view": coords["view_id"],
        "chat": chat_id,
        "period": period,
        "rows": stable_rows,
    }
    if text_coords:
        canonical_payload["text_coords"] = {
            "table": text_coords.get("table_id", ""),
            "view": text_coords.get("view_id", ""),
        }
    if text_sections is not None:
        canonical_payload["text_sections"] = {
            section: {
                field: _string(_raw_field(row, field))
                for field in TEXT_FIELDS
            }
            for section, row in sorted(text_sections.items())
        }
    if result_coords:
        canonical_payload["result_coords"] = {
            "table": result_coords.get("table_id", ""),
            "view": result_coords.get("view_id", ""),
        }
    if result_rows is not None:
        canonical_payload["result_rows"] = [
            {
                "fields": {field: _string(_raw_field(row, field)) for field in RESULT_FIELDS},
            }
            for row in result_rows
        ]
    canonical = json.dumps(
        canonical_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]
    return "ipproc-%s-%s" % (_safe_period(period)[:12], digest)


def _ledger_records(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    result: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, Mapping) and item.get("idempotency_key"):
            result[str(item["idempotency_key"])] = dict(item)
    return result


def _append_ledger(path: Path, item: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(dict(item), ensure_ascii=False, sort_keys=True) + "\n")


def verify_chat(chat_id: str, chat_name: str, identity: str, timeout: int) -> None:
    if not chat_name:
        return
    payload = _unwrap(
        _json_payload(
            run_lark(
                [
                    "im",
                    "+chat-search",
                    "--query",
                    chat_name,
                    "--disable-search-by-user",
                    "--search-types",
                    "private,external,public_joined",
                    "--page-size",
                    "100",
                    "--format",
                    "json",
                    "--as",
                    identity,
                ],
                timeout=timeout,
            )
        )
    )
    matches: list[Mapping[str, Any]] = []
    seen: set[str] = set()
    for item in _iter_dicts(payload):
        found_id = _string(item.get("chat_id") or item.get("id"))
        found_name = _string(item.get("name") or item.get("chat_name") or item.get("title"))
        if found_id and found_name == chat_name and found_id not in seen:
            matches.append(item)
            seen.add(found_id)
    if len(matches) != 1:
        raise SystemExit("群名称精确校验失败：%s 个匹配" % len(matches))
    found_id = _string(matches[0].get("chat_id") or matches[0].get("id"))
    if chat_id and found_id != chat_id:
        raise SystemExit("群名称与 chat_id 不一致；停止发送")


def upload_image(image_path: Path, identity: str, timeout: int) -> str:
    try:
        payload = _unwrap(
            _json_payload(
                run_lark(
                    [
                        "im",
                        "images",
                        "create",
                        "--data",
                        '{"image_type":"message"}',
                        "--file",
                        "./%s" % image_path.name,
                        "--format",
                        "json",
                        "--as",
                        identity,
                    ],
                    cwd=str(image_path.parent),
                    timeout=timeout,
                )
            )
        )
    except RuntimeError as exc:
        if "im:resource" in str(exc):
            raise RuntimeError("图片推送需要发送身份具备 im:resource；当前身份未授权，请先补授权或改用已具备该权限的 bot") from exc
        raise
    image_key = _string(_find_first(payload, ("image_key", "imageKey")))
    if not image_key.startswith("img_"):
        raise RuntimeError("图片上传未返回可用 image_key")
    return image_key


def _cleanup_local_image(image_path: Path | None) -> dict[str, Any]:
    """Remove a generated local PNG after final message delivery.

    Cleanup is deliberately best-effort: a failed unlink must not turn a
    successfully delivered Feishu message into a false delivery failure.
    """

    if image_path is None:
        return {"attempted": False, "deleted": False, "status": "not_generated", "error": ""}
    try:
        image_path.unlink()
    except FileNotFoundError:
        return {"attempted": True, "deleted": True, "status": "already_absent", "error": ""}
    except OSError as exc:
        return {"attempted": True, "deleted": False, "status": "delete_failed", "error": str(exc)[:500]}
    return {"attempted": True, "deleted": True, "status": "deleted", "error": ""}


def send_markdown(chat_id: str, markdown: str, key: str, identity: str, *, dry_run: bool, timeout: int) -> Any:
    command = [
        "im",
        "+messages-send",
        "--chat-id",
        chat_id,
        "--markdown",
        markdown,
        "--idempotency-key",
        key,
        "--format",
        "json",
        "--as",
        identity,
    ]
    if dry_run:
        command.append("--dry-run")
    return _unwrap(_json_payload(run_lark(command, timeout=timeout)))


def _message_id(payload: Any) -> str:
    return _string(_find_first(payload, ("message_id", "messageId", "msg_id")))


def _dimension_record(row: Mapping[str, Any]) -> dict[str, str] | None:
    consultant = _string(_raw_field(row, "顾问"))
    supervisor = _string(_raw_field(row, "主管"))
    channel = _string(_raw_field(row, "渠道"))
    if not consultant or not supervisor or not channel:
        return None
    return {
        "维度键": "%s|%s|%s" % (consultant, supervisor, channel),
        "顾问": consultant,
        "主管": supervisor,
        "渠道": channel,
    }


def sync_helper_dimension(args: argparse.Namespace) -> int:
    """Append missing consultant/team dimension rows without deleting anything."""

    source_coords = resolve_coordinates(args)
    helper_table_id = _string(args.helper_table_id)
    raw_table_id = _string(args.helper_raw_table_id)
    raw_coords = {
        "base_token": source_coords["base_token"],
        "table_id": raw_table_id,
        "view_id": "",
    }
    helper_coords = {
        "base_token": source_coords["base_token"],
        "table_id": helper_table_id,
        "view_id": "",
    }
    raw_records = _fetch_view_records(coords=raw_coords, args=args, fields=HELPER_RAW_FIELDS, temp_prefix=".ip-helper-raw-pages-")
    existing_records = _fetch_view_records(coords=helper_coords, args=args, fields=HELPER_DIMENSION_FIELDS, temp_prefix=".ip-helper-existing-pages-")
    candidates: dict[str, dict[str, str]] = {}
    for row in raw_records:
        dimension = _dimension_record(row)
        if dimension:
            candidates[dimension["维度键"]] = dimension
    existing_keys = {
        _string(_raw_field(row, "维度键"))
        for row in existing_records
        if _string(_raw_field(row, "维度键"))
    }
    missing = [candidates[key] for key in sorted(candidates) if key not in existing_keys]
    report: dict[str, Any] = {
        "mode": "helper_sync_preview" if not args.confirm_helper_sync else "helper_sync",
        "raw_table": raw_table_id,
        "helper_table": helper_table_id,
        "raw_row_count": len(raw_records),
        "existing_dimension_count": len(existing_records),
        "candidate_dimension_count": len(candidates),
        "missing_dimension_count": len(missing),
        "missing_dimensions": [row["维度键"] for row in missing],
        "created_dimension_count": 0,
    }
    if not args.confirm_helper_sync or not missing:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    for start in range(0, len(missing), 200):
        batch = missing[start : start + 200]
        payload = json.dumps({"create_records": batch}, ensure_ascii=False, separators=(",", ":"))
        response = _unwrap(
            _json_payload(
                run_lark(
                    [
                        "base",
                        "+record-batch-create",
                        "--base-token",
                        source_coords["base_token"],
                        "--table-id",
                        helper_table_id,
                        "--json",
                        payload,
                        "--format",
                        "json",
                        "--as",
                        args.base_as,
                    ],
                    timeout=args.timeout,
                )
            )
        )
        if response is None:
            raise RuntimeError("提醒计算表维度行写入未返回成功响应")
        report["created_dimension_count"] += len(batch)
    report["status"] = "synced"
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def _state_dir(args: argparse.Namespace) -> Path:
    value = args.state_dir or os.environ.get("PUSH_STATE_DIR", "runtime/ip-broadcast-push")
    return Path(value).expanduser().resolve()


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--base-token", default=os.environ.get("BASE_TOKEN", ""), help="Base token；也可用 BASE_TOKEN")
    parser.add_argument("--table-id", default=os.environ.get("TABLE_ID", ""), help="表 ID/名称；也可用 TABLE_ID")
    parser.add_argument("--view-id", default=os.environ.get("VIEW_ID", ""), help="视图 ID/名称；也可用 VIEW_ID")
    parser.add_argument("--source-url", default=os.environ.get("SOURCE_URL", ""), help="可选：由 base +url-resolve 解析 Base URL")
    parser.add_argument("--text-table-id", default=os.environ.get("TEXT_TABLE_ID", ""), help="推送文字表 ID/名称")
    parser.add_argument("--text-view-id", default=os.environ.get("TEXT_VIEW_ID", ""), help="推送文字视图 ID/名称")
    parser.add_argument("--text-source-url", default=os.environ.get("TEXT_SOURCE_URL", ""), help="可选：由 Base/Wiki URL 解析推送文字表")
    parser.add_argument(
        "--result-view-id",
        default=os.environ.get("RESULT_VIEW_ID", "结果数据"),
        help="结果数据视图 ID/名称；默认读取同一表的“结果数据”",
    )
    parser.add_argument("--base-as", choices=("user", "bot"), default=os.environ.get("BASE_AS", "user"))
    parser.add_argument("--chat-id", default=os.environ.get("CHAT_ID", ""), help="目标群 chat_id；也可用 CHAT_ID")
    parser.add_argument("--chat-name", default=os.environ.get("CHAT_NAME", ""), help="可选：精确校验群名称")
    parser.add_argument("--as", dest="identity", choices=("user", "bot"), default=os.environ.get("SEND_AS", "user"), help="发送身份")
    parser.add_argument("--period", default=os.environ.get("PERIOD", ""), help="精确期次；多期视图时必填")
    parser.add_argument("--mention-map", default=os.environ.get("MENTION_MAP", ""), help="可选 JSON：{姓名: ou_xxx}")
    parser.add_argument("--no-mentions", action="store_true", help="不解析/不生成 @")
    parser.add_argument("--strict-mentions", action="store_true", help="预览时也要求所有姓名都能精确解析")
    parser.add_argument("--allow-unresolved-mentions", action="store_true", help="发送时允许无法精确解析的姓名以纯文本发送")
    parser.add_argument("--no-image", dest="with_image", action="store_false", help="不生成汇总表图片")
    parser.set_defaults(with_image=True)
    parser.add_argument("--output-image", default=os.environ.get("OUTPUT_IMAGE", ""), help="图片输出路径；默认写入状态目录")
    parser.add_argument(
        "--output-result-image",
        default=os.environ.get("OUTPUT_RESULT_IMAGE", ""),
        help="结果图片输出路径；默认写入状态目录",
    )
    parser.add_argument("--state-dir", default=os.environ.get("PUSH_STATE_DIR", ""), help="状态/台账目录")
    parser.add_argument("--ledger", default=os.environ.get("PUSH_LEDGER", ""), help="幂等台账路径")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--max-pages", type=int, default=100)


def prepare(args: argparse.Namespace) -> dict[str, Any]:
    coords = resolve_coordinates(args)
    records = fetch_records(coords, args)
    period = select_period(records, args.period or None)
    rows = select_rows(records, period)
    result_coords = {
        "base_token": coords["base_token"],
        "table_id": coords["table_id"],
        "view_id": _string(getattr(args, "result_view_id", "")) or "结果数据",
        "source_url": coords.get("source_url", ""),
    }
    result_records = fetch_result_records(result_coords, args)
    result_source_rows = select_rows(result_records, period)
    result_rows = aggregate_result_rows(result_source_rows, period)
    text_coords = resolve_text_coordinates(args, coords)
    text_records = fetch_text_records(text_coords, args)
    text_sections = select_text_config(text_records, period)
    configured_reminder_names: list[str] = []
    for section in TEXT_SECTION_ORDER:
        row = text_sections.get(section)
        if not row:
            continue
        for name in reminder_names(row):
            if name not in configured_reminder_names:
                configured_reminder_names.append(name)
    mention_info = resolve_mentions(
        [],
        mention_map=_load_mention_map(args.mention_map or None),
        no_lookup=False,
        disable_mentions=args.no_mentions,
        extra_names=configured_reminder_names,
        timeout=args.timeout,
    )
    if args.strict_mentions and (mention_info["unresolved"] or mention_info["ambiguous"]):
        raise SystemExit("存在未能唯一解析的 @ 姓名：%s" % ", ".join(mention_info["unresolved"] + list(mention_info["ambiguous"])))
    chat_id = (args.chat_id or "").strip()
    if args.chat_name:
        verify_chat(chat_id, args.chat_name, args.identity, args.timeout)
    if not chat_id and args.chat_name:
        raise SystemExit("--chat-name 校验通过后仍需要 --chat-id 或 CHAT_ID")
    image_path: Path | None = None
    result_image_path: Path | None = None
    image_ref = None
    result_image_ref = None
    image_columns = available_image_columns(rows)
    if args.with_image:
        state_dir = _state_dir(args)
        image_path = Path(args.output_image).expanduser().resolve() if args.output_image else state_dir / ("IP过程数据_%s.png" % _safe_period(period))
        result_image_path = (
            Path(args.output_result_image).expanduser().resolve()
            if args.output_result_image
            else state_dir / ("IP结果数据_%s.png" % _safe_period(period))
        )
        if image_path == result_image_path:
            raise SystemExit("过程图片与结果图片不能使用同一个输出路径")
        render_process_image(rows, image_path)
        render_result_image(result_rows, result_image_path)
        image_ref = "img_process_preview"
        result_image_ref = "img_result_preview"
    # Never put the full source URL into the group message: a Wiki/Base URL
    # can contain a share token.  The table/view coordinates are sufficient
    # for human traceability and remain safe to display.
    source_label = "%s / %s / lark-cli" % (coords["table_id"], coords["view_id"])
    markdown = build_markdown(
        rows,
        period=period,
        source_label=source_label,
        mention_info=mention_info,
        image_ref=image_ref,
        text_sections=text_sections,
        result_image_ref=result_image_ref,
    )
    key = idempotency_key(
        coords,
        chat_id,
        period,
        rows,
        text_coords=text_coords,
        text_sections=text_sections,
        result_coords=result_coords,
        result_rows=result_rows,
    )
    ledger = Path(args.ledger).expanduser().resolve() if args.ledger else _state_dir(args) / "send_ledger.jsonl"
    return {
        "coords": coords,
        "records": records,
        "rows": rows,
        "result_coords": result_coords,
        "result_records": result_records,
        "result_source_rows": result_source_rows,
        "result_rows": result_rows,
        "period": period,
        "text_coords": text_coords,
        "text_records": text_records,
        "text_sections": text_sections,
        "mention_info": mention_info,
        "chat_id": chat_id,
        "chat_name": args.chat_name,
        "identity": args.identity,
        "image_path": image_path,
        "image_columns": image_columns,
        "result_image_path": result_image_path,
        "result_image_columns": RESULT_IMAGE_COLUMNS,
        "markdown": markdown,
        "idempotency_key": key,
        "ledger": ledger,
    }


def print_preview(context: Mapping[str, Any]) -> None:
    mention_info = context["mention_info"]
    summary = {
        "mode": "preview",
        "period": context["period"],
        "row_count": len(context["rows"]),
        "result_row_count": len(context["result_rows"]),
        "text_section_count": len(context["text_sections"]),
        "text_sections": {
            section: {
                "title": _string(_raw_field(row, "推送标题")),
                "reminder_names": reminder_names(row),
            }
            for section, row in context["text_sections"].items()
        },
        "chat_id": context["chat_id"] or None,
        "identity": context["identity"],
        "image_path": str(context["image_path"]) if context["image_path"] else None,
        "result_image_path": str(context["result_image_path"]) if context["result_image_path"] else None,
        "image_columns": [label for _source, label, _kind in context["image_columns"]],
        "image_omitted_columns": [
            label for source, label, _kind in IMAGE_COLUMNS if source not in {item[0] for item in context["image_columns"]}
        ],
        "result_image_columns": [label for _source, label, _kind in context["result_image_columns"]],
        "idempotency_key": context["idempotency_key"],
        "mention_resolved": sorted(mention_info["resolved"]),
        "mention_unresolved": mention_info["unresolved"],
        "mention_ambiguous": mention_info["ambiguous"],
        "excluded_outcome_fields": list(OUTCOME_TERMS),
        "result_section_policy": "结果图片读取 IP播报_主管 / 结果数据；不改写 IP原始数据",
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if mention_info.get("lookup_error"):
        print("[warning] 通讯录解析未完成：%s" % mention_info["lookup_error"])
    print("\n----- 群消息 Markdown 预览 -----\n")
    print(context["markdown"])


def _image_slots(context: Mapping[str, Any]) -> tuple[tuple[str, Path | None, tuple[str, ...]], ...]:
    """Return generated image paths and their Markdown placeholders."""

    return (
        (
            "process",
            context.get("image_path"),
            ("img_process_preview", "img_preview"),
        ),
        (
            "result",
            context.get("result_image_path"),
            ("img_result_preview", "img_result"),
        ),
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="飞书多维表格过程数据群推送：默认预览，真实发送需显式确认")
    subparsers = parser.add_subparsers(dest="command", required=True)
    preview_parser = subparsers.add_parser("preview", help="读取视图并生成本地图片/Markdown预览，不发送")
    add_common_arguments(preview_parser)
    preview_parser.add_argument("--cli-dry-run", action="store_true", help="额外调用 im +messages-send --dry-run 校验请求形状")

    send_parser = subparsers.add_parser("send", help="发送群消息；必须 --confirm-send，或使用 --dry-run")
    add_common_arguments(send_parser)
    send_parser.add_argument("--confirm-send", action="store_true", help="确认执行真实群消息发送")
    send_parser.add_argument("--dry-run", action="store_true", help="调用 lark-cli dry-run，不上传图片、不发送消息")

    sync_parser = subparsers.add_parser("sync-helper", help="预览或追加提醒计算表缺失的顾问维度行，不删除任何记录")
    add_common_arguments(sync_parser)
    sync_parser.add_argument(
        "--helper-table-id",
        default=os.environ.get("HELPER_TABLE_ID", "IP播报_提醒计算"),
        help="提醒计算表 ID/名称；默认 IP播报_提醒计算",
    )
    sync_parser.add_argument(
        "--helper-raw-table-id",
        default=os.environ.get("HELPER_RAW_TABLE_ID", "IP原始数据"),
        help="原始明细表 ID/名称；默认 IP原始数据",
    )
    sync_parser.add_argument("--confirm-helper-sync", action="store_true", help="确认追加缺失维度行")

    args = parser.parse_args(argv)
    if args.command == "sync-helper":
        return sync_helper_dimension(args)
    if args.command == "send" and not args.confirm_send and not args.dry_run:
        raise SystemExit("send 默认不执行外发；请先用 preview，确认后再传 --confirm-send，或传 --dry-run")
    context = prepare(args)
    if args.command == "preview":
        print_preview(context)
        if args.cli_dry_run:
            if not context["chat_id"]:
                raise SystemExit("--cli-dry-run 需要 --chat-id 或 CHAT_ID")
            send_markdown(context["chat_id"], context["markdown"], context["idempotency_key"], context["identity"], dry_run=True, timeout=args.timeout)
            print("\n[ok] lark-cli im +messages-send --dry-run 通过（未发送）")
        return 0

    if context["mention_info"]["lookup_error"] and not args.allow_unresolved_mentions and not args.no_mentions:
        raise SystemExit("通讯录查询失败，未取得可验证的 @ 结果；请修复 user 权限、提供 --mention-map，或显式 --allow-unresolved-mentions")
    if (context["mention_info"]["unresolved"] or context["mention_info"]["ambiguous"]) and not args.allow_unresolved_mentions and not args.no_mentions:
        raise SystemExit("存在未唯一解析的 @ 姓名；为避免误 @，请补充 --mention-map/权限，或显式 --allow-unresolved-mentions")
    if not context["chat_id"]:
        raise SystemExit("真实发送需要 --chat-id 或 CHAT_ID")

    if args.dry_run:
        send_markdown(context["chat_id"], context["markdown"], context["idempotency_key"], context["identity"], dry_run=True, timeout=args.timeout)
        print_preview(context)
        print("\n[ok] lark-cli dry-run 通过（未上传图片、未发送）")
        return 0

    prior = _ledger_records(context["ledger"]).get(context["idempotency_key"])
    if prior and prior.get("status") == "sent" and prior.get("message_id"):
        cleanup = {}
        for slot, path, _refs in _image_slots(context):
            if path:
                cleanup[slot] = _cleanup_local_image(path)
        print(
            json.dumps(
                {
                    "status": "already_sent",
                    "message_id": prior["message_id"],
                    "idempotency_key": context["idempotency_key"],
                    "image_local_cleanup": cleanup,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    markdown = context["markdown"]
    image_keys: dict[str, str] = {}
    image_cleanup: dict[str, Any] = {}
    for slot, path, _refs in _image_slots(context):
        if path:
            image_cleanup[slot] = {
                "attempted": False,
                "deleted": False,
                "status": "not_attempted",
                "error": "",
            }
    try:
        for slot, path, refs in _image_slots(context):
            if not path:
                continue
            image_key = upload_image(path, context["identity"], args.timeout)
            image_keys[slot] = image_key
            for ref in refs:
                markdown = markdown.replace(ref, image_key)
        response = send_markdown(context["chat_id"], markdown, context["idempotency_key"], context["identity"], dry_run=False, timeout=args.timeout)
        message_id = _message_id(response)
        if not message_id:
            raise RuntimeError("发送接口未返回 message_id，不能视为已送达")
        # Keep the PNG when upload succeeded but final message delivery did
        # not; after message_id is verified, remove it immediately to avoid
        # accumulating period snapshots on the local disk.
        for slot, path, _refs in _image_slots(context):
            if not path or not image_keys.get(slot):
                continue
            image_cleanup[slot] = _cleanup_local_image(path)
            if not image_cleanup[slot]["deleted"]:
                print("[warning] 群消息已送达，但%s图片删除失败：%s" % (slot, image_cleanup[slot]["error"]))
        _append_ledger(
            context["ledger"],
            {
                "status": "sent",
                "message_id": message_id,
                "idempotency_key": context["idempotency_key"],
                "period": context["period"],
                "chat_id": context["chat_id"],
                "image_key": image_keys.get("process") or None,
                "result_image_key": image_keys.get("result") or None,
                "image_local_cleanup": image_cleanup,
            },
        )
        print(
            json.dumps(
                {
                    "status": "sent",
                    "message_id": message_id,
                    "idempotency_key": context["idempotency_key"],
                    "ledger": str(context["ledger"]),
                    "image_keys": image_keys,
                    "image_local_cleanup": image_cleanup,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    except Exception as exc:
        for slot, path, _refs in _image_slots(context):
            if path:
                image_cleanup[slot] = {
                    "attempted": False,
                    "deleted": False,
                    "status": "preserved_after_send_failure",
                    "error": "",
                }
        _append_ledger(
            context["ledger"],
            {
                "status": "failed",
                "idempotency_key": context["idempotency_key"],
                "period": context["period"],
                "chat_id": context["chat_id"],
                "error": str(exc)[:500],
                "image_key": image_keys.get("process") or None,
                "result_image_key": image_keys.get("result") or None,
                "image_local_cleanup": image_cleanup,
            },
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
