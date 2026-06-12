"""Common helpers for dashboard commands and markdown generation."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def write_json(data: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def safe_filename(value: str) -> str:
    cleaned = re.sub(r'[<>:"/\\\\|?*\x00-\x1f]', "_", value).strip(" .")
    return cleaned or "dashboard"


def parse_dashboard_names(values: list[str] | None) -> list[str]:
    if not values:
        return []
    names: list[str] = []
    for value in values:
        for item in re.split(r"[|,]", value):
            item = item.strip()
            if item:
                names.append(item)
    return names


def format_task_ids(value: Any) -> str:
    if isinstance(value, list):
        return ",".join(str(item) for item in value if str(item).strip())
    if value is None:
        return ""
    return str(value).strip()


def markdown_cell(value: Any) -> str:
    text = str(value or "")
    return text.replace("|", "\\|").replace("\n", "<br>")
