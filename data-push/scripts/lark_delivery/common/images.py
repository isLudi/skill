"""Fonts, positioning and safe cleanup of a caller-owned generated PNG."""
from __future__ import annotations
from pathlib import Path
from typing import Any, Mapping


def _find_font(size: int, bold: bool = False):
    try:
        from PIL import ImageFont
    except ImportError as exc:
        raise RuntimeError("生成图片需要 Pillow；请在当前 D:\\anaconda3 环境安装 Pillow") from exc
    candidates = (
        [
            r"C:\Windows\Fonts\msyhbd.ttc",
            r"C:\Windows\Fonts\simhei.ttf",
            r"C:\Windows\Fonts\simsunb.ttf",
        ]
        if bold
        else [
            r"C:\Windows\Fonts\msyh.ttc",
            r"C:\Windows\Fonts\simsun.ttc",
            r"C:\Windows\Fonts\simfang.ttf",
        ]
    )
    for candidate in candidates:
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def _center_text(draw: Any, box: tuple[int, int, int, int], text: str, font: Any, fill: str) -> None:
    left, top, right, bottom = box
    bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=2, align="center")
    while bbox[2] - bbox[0] > right - left - 4 and hasattr(font, "font_variant") and font.size > 12:
        font = font.font_variant(size=font.size - 1)
        bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=2, align="center")
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    x = left + max(0, (right - left - width) // 2) - bbox[0]
    y = top + max(0, (bottom - top - height) // 2) - bbox[1]
    draw.multiline_text((x, y), text, font=font, fill=fill, spacing=2, align="center")


def _cleanup_local_image(image_path: Path | None) -> dict[str, Any]:
    """Remove a generated local PNG after final message delivery.

    Cleanup is deliberately best-effort: a failed unlink must not turn a
    successfully delivered Feishu message into a false delivery failure.
    """

    if image_path is None:
        return {"attempted": False, "deleted": False, "status": "not_generated", "error": ""}
    try:
        image_path.unlink()
    except FileNotFoundError:
        return {"attempted": True, "deleted": True, "status": "already_absent", "error": ""}
    except OSError as exc:
        return {"attempted": True, "deleted": False, "status": "delete_failed", "error": str(exc)[:500]}
    return {"attempted": True, "deleted": True, "status": "deleted", "error": ""}


def _image_slots(context: Mapping[str, Any]) -> tuple[tuple[str, Path | None, tuple[str, ...]], ...]:
    """Return generated image paths and their Markdown placeholders."""

    return (
        (
            "process",
            context.get("image_path"),
            ("img_process_preview", "img_preview"),
        ),
        (
            "result",
            context.get("result_image_path"),
            ("img_result_preview",),
        ),
    )
