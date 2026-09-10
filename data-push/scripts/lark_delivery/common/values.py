"""Neutral CLI payload and display-value helpers; no business field contracts."""
from __future__ import annotations
import json
from typing import Any, Iterable, Mapping, Sequence


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
