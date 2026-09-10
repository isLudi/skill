"""Legacy market row selection and weighted aggregation."""
from __future__ import annotations
import hashlib
import re
from typing import Any, Mapping, Sequence
from .market_schema import PROCESS_FIELDS, TEXT_SECTION_ORDER, RESULT_RATE_DENOMINATORS, RESULT_SUM_FIELDS, IMAGE_COLUMNS, FIELD_ALIASES, RATE_NUMERATORS, RATE_FIELDS
from ..common.values import _string, _number, _rate, _format_rate, _format_value


def _raw_field(row: Mapping[str, Any], field: str) -> Any:
    fields = row.get("fields", row)
    if not isinstance(fields, Mapping):
        return None
    for candidate in FIELD_ALIASES.get(field, (field,)):
        if candidate in fields:
            return fields[candidate]
    return None


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
        if name and name not in {"无", "暂无", "-"} and name not in result:
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


def _result_bar_fraction(source: str, value: Any, rows: Sequence[Mapping[str, Any]]) -> float | None:
    if source == "人均报科":
        maximum = max((_number(_raw_field(row, source)) or 0.0 for row in rows), default=0.0)
        number = _number(value)
        return number / maximum if number is not None and maximum > 0 else None
    return _rate(value)


def visible_image_rows(rows: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    """Hide only explicitly zero/zero lead rows, without altering source data."""

    return [row for row in rows if not (
        _number(_raw_field(row, "退前线索")) == 0
        and _number(_raw_field(row, "退后线索")) == 0
    )]


def _image_value(row: Mapping[str, Any], source: str, kind: str) -> str:
    if row.get("record_id") == "__total__" and kind == "rate":
        return _format_rate(_raw_field(row, source))
    return _display(row, source, kind)
