"""Choose conversion wording and mention targets from all current supervisors."""
from __future__ import annotations

from decimal import Decimal


def _number(value):
    if value is None:
        return None
    number = Decimal(str(value))
    if not number.is_finite():
        raise ValueError("Invalid conversion reminder metric")
    return number


def conversion_policy(data):
    """Do not celebrate a relative advantage when nobody has positive efficiency.

    Rows with no calculable efficiency are excluded from the sign check. The
    complete current population is used, before filtering rows for the image.
    """
    baseline = _number(data["team"]["now"]["unit"])
    if baseline is None:
        raise ValueError("Team unit efficiency is missing")
    population = [(row["supervisor"], _number(row["now"]["unit"])) for row in data["rows"]]
    available = [(name, value) for name, value in population if value is not None]
    negative = sum(value < 0 for _, value in available)
    zero = sum(value == 0 for _, value in available)
    positive = sum(value > 0 for _, value in available)
    mode, text = "above_team", None
    if available and negative == len(available):
        mode, text = "all_negative", "所有主管截面单效均为负 😢😞"
    elif available and positive == 0:
        mode = "all_nonpositive" if negative else "all_zero"
        text = "所有主管截面单效均未转正 😢😞" if negative else "所有主管截面单效均为0 😢😞"
    names = [name for name, value in available if value > baseline] if mode == "above_team" else []
    return {"mode": mode, "text": text, "target_names": names,
            "selection": "all_current_supervisors_unit_above_full_channel_team"
            if mode == "above_team" else "all_current_supervisors_unit_" + mode,
            "population": {"total": len(population), "available": len(available),
                           "unavailable": len(population) - len(available),
                           "negative": negative, "zero": zero, "positive": positive}}
