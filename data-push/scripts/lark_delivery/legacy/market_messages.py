"""Legacy text construction and deterministic content keys."""
from __future__ import annotations
import hashlib
import html
import json
import re
from typing import Any, Mapping, Sequence
from .market_schema import PROCESS_FIELDS, TEXT_FIELDS, TEXT_SECTION_ORDER, RESULT_FIELDS
from .market_aggregation import _raw_field, _safe_period, reminder_names, _display, make_total_row, _image_value
from ..common.values import _string


def _mention(name: str, resolved: Mapping[str, str]) -> str:
    open_id = resolved.get(name)
    if not open_id:
        return html.escape(name)
    return '<at user_id="%s">%s</at>' % (html.escape(open_id, quote=True), html.escape(name))


def _render_configured_reminder(row: Mapping[str, Any], resolved: Mapping[str, str]) -> str:
    reminder = _string(_raw_field(row, "提醒"))
    if not reminder:
        return "无"
    if _raw_field(row, "_mention_target") == "none":
        return html.escape(reminder)
    if _raw_field(row, "_mention_target") == "supervisor":
        supervisors = _raw_field(row, "_reminder_supervisors") or []
        suffix = "\n  请主管关注：" + "、".join(_mention(name, resolved) for name in supervisors) if supervisors else ""
        return html.escape(reminder) + suffix
    names = sorted(reminder_names(row), key=len, reverse=True)
    if not names:
        return html.escape(reminder)
    pattern = re.compile("(" + "|".join(re.escape(name) for name in names) + ")")
    return "".join(_mention(part, resolved) if part in names else html.escape(part)
                   for part in pattern.split(reminder))


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
        if lines:
            lines.append("")
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
    delivery: Mapping[str, Any] | None = None,
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
    if delivery is not None:
        canonical_payload["delivery"] = delivery
    canonical = json.dumps(
        canonical_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]
    return "ipproc-%s-%s" % (_safe_period(period)[:12], digest)
