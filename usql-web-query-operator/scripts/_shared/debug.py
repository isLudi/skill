"""Debug artifact helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def save_debug_artifacts(page: Any, artifacts_dir: Path, prefix: str = "page") -> None:
    page.screenshot(path=str(artifacts_dir / f"{prefix}.png"), full_page=True)
    (artifacts_dir / f"{prefix}.html").write_text(page.content(), encoding="utf-8")
    for index, frame_obj in enumerate(getattr(page, "frames", [])):
        try:
            frame_html = frame_obj.content()
            (artifacts_dir / f"{prefix}.frame{index}.html").write_text(frame_html, encoding="utf-8")
        except Exception:
            pass
        try:
            frame_text = frame_obj.locator("body").inner_text(timeout=3000)
            (artifacts_dir / f"{prefix}.frame{index}.txt").write_text(frame_text, encoding="utf-8")
        except Exception:
            pass
