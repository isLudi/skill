"""Environment-file loading helpers."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping


def load_env_file(path: Path | None) -> None:
    if not path or not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def read_env_section(path: Path | None, section_name: str) -> dict[str, str]:
    """Read key/value pairs only from one exact comment-delimited section.

    The local ``usql_api.env`` intentionally contains two credential sections
    with the same key names. A normal dotenv load cannot distinguish them, so
    callers that need an isolated account must use this helper and pass the
    returned values directly instead of mutating process-wide environment state.
    """

    if not path or not path.is_file():
        return {}
    current_section = ""
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("#"):
            current_section = line.lstrip("#").strip()
            continue
        if current_section != section_name or not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        if key in values:
            raise ValueError(f"Duplicate key in environment section {section_name!r}: {key}")
        values[key] = value.strip().strip('"').strip("'")
    return values


def load_env_section(
    path: Path | None,
    section_name: str,
    *,
    override: bool = False,
) -> Mapping[str, str]:
    """Load one exact section into ``os.environ`` and return its values."""

    values = read_env_section(path, section_name)
    for key, value in values.items():
        if override or key not in os.environ:
            os.environ[key] = value
    return values
