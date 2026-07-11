"""Filesystem helpers for runtime directories and artifacts."""

from __future__ import annotations

import os
import time
import uuid
from pathlib import Path


def ensure_runtime(paths: list[Path]) -> None:
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def safe_artifact_dir(root: Path) -> Path:
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    unique_suffix = f"{os.getpid()}-{uuid.uuid4().hex[:8]}"
    path = root / f"{timestamp}-{unique_suffix}"
    path.mkdir(parents=True, exist_ok=False)
    return path
