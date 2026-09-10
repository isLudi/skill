"""Record cell access and finite decimal parsing; no report aggregation semantics."""
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

def value(row: Mapping[str, Any], field: str) -> Any:
    return row.get("fields", row).get(field)


def text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(text(item) for item in value)
    return str(value).strip()


def numeric(value: Any, field: str) -> Decimal:
    try:
        number = Decimal(text(value))
    except InvalidOperation as exc:
        raise ValueError(f"线索字段 {field} 存在空值或非数字，无法可靠汇总") from exc
    if not number.is_finite():
        raise ValueError(f"线索字段 {field} 存在非有限数字")
    return number
