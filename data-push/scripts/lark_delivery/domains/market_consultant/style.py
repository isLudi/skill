"""Reviewed market-consultant conditional colors; not a cross-domain metric rule."""
from typing import Any
from ...common.values import _number, _rate

BAR_FIELDS = {"首call率": "#4f78ae", "5min": "#f5ae23", "双沟率": "#138de2"}


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
