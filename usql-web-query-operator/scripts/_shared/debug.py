"""Debug artifact helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def save_debug_artifacts(page: Any, artifacts_dir: Path, prefix: str = "page") -> None:
    page.screenshot(path=str(artifacts_dir / f"{prefix}.png"), full_page=True)
    (artifacts_dir / f"{prefix}.html").write_text(page.content(), encoding="utf-8")
