"""Filesystem helpers for runtime directories and artifacts."""

from __future__ import annotations

import time
from pathlib import Path


def ensure_runtime(paths: list[Path]) -> None:
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def safe_artifact_dir(root: Path) -> Path:
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    path = root / timestamp
    path.mkdir(parents=True, exist_ok=False)
    return path
