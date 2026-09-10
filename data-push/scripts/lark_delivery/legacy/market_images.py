"""Legacy process/result PNG layout; no transport or scheduling."""
from __future__ import annotations
from pathlib import Path
from typing import Any, Mapping, Sequence
from .market_schema import RESULT_IMAGE_COLUMNS, RESULT_BAR_FIELDS, RESULT_IMAGE_WIDTHS, BAR_FIELDS, IMAGE_WIDTHS
from .market_aggregation import _raw_field, available_image_columns, make_total_row, make_result_total_row, _result_bar_fraction, visible_image_rows, _image_value
from ..common.values import _string, _rate, _format_value
from ..common.images import _find_font, _center_text
from ..domains.market_consultant.style import _result_cell_fill, _retention_color


def render_result_image(
    rows: Sequence[Mapping[str, Any]], output_path: Path, *,
    columns: Sequence[tuple[str, str, str]] | None = None,
    total: Mapping[str, Any] | None = None,
) -> Path:
    """Render the result-data reference layout as a second wide PNG."""

    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise RuntimeError("生成图片需要 Pillow；请在当前 D:\\anaconda3 环境安装 Pillow") from exc
    if not rows:
        raise SystemExit("结果数据视图没有可生成图片的记录")
    # Preserve the complete-scope total before applying the display-only filter.
    total = total if total is not None else make_result_total_row(rows, _string(_raw_field(rows[0], "期次")))
    rows = visible_image_rows(rows)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    columns = tuple(columns) if columns is not None else RESULT_IMAGE_COLUMNS
    widths = [RESULT_IMAGE_WIDTHS[source] for source, _label, _kind in columns]
    header_height, row_height, total_height = 92, 64, 70
    width = sum(widths)
    height = header_height + row_height * len(rows) + total_height
    navy = "#203b72"
    grid = "#b8c4d3"
    image = Image.new("RGB", (width, height), "#ffffff")
    draw = ImageDraw.Draw(image)
    header_font = _find_font(27, bold=True)
    body_font = _find_font(25, bold=False)
    total_font = _find_font(28, bold=True)
    x_positions = [0]
    for column_width in widths:
        x_positions.append(x_positions[-1] + column_width)

    draw.rectangle((0, 0, width, header_height), fill=navy)
    for (_source, label, _kind), left, right in zip(columns, x_positions, x_positions[1:]):
        _center_text(draw, (left + 2, 0, right - 2, header_height), label, header_font, "#ffffff")
        draw.line((right - 1, 0, right - 1, height), fill=grid, width=1)
    draw.line((0, header_height - 1, width, header_height - 1), fill=grid, width=1)

    for row_index, row in enumerate(rows):
        top = header_height + row_index * row_height
        bottom = top + row_height
        for (source, _label, kind), left, right in zip(columns, x_positions, x_positions[1:]):
            value = _raw_field(row, source)
            draw.rectangle((left, top, right, bottom), fill=_result_cell_fill(source, value))
            if source in RESULT_BAR_FIELDS:
                fraction = _result_bar_fraction(source, value, rows)
                if fraction is not None:
                    bar_width = max(0, min(1, fraction)) * max(0, right - left - 12)
                    draw.rectangle(
                        (left + 6, top + 10, left + 6 + int(bar_width), bottom - 10),
                        fill=RESULT_BAR_FIELDS[source],
                    )
            text = _format_value(value, kind)
            _center_text(draw, (left + 2, top + 1, right - 2, bottom - 1), text, body_font, "#111827")
            draw.rectangle((left, top, right, bottom), outline=grid, width=1)

    total_top = header_height + row_height * len(rows)
    draw.rectangle((0, total_top, width, height), fill=navy)
    for (source, _label, kind), left, right in zip(columns, x_positions, x_positions[1:]):
        text = _format_value(_raw_field(total, source), kind)
        _center_text(draw, (left + 2, total_top + 1, right - 2, height - 1), text, total_font, "#ffffff")
        draw.rectangle((left, total_top, right, height), outline=grid, width=1)

    try:
        image.save(output_path, format="PNG", optimize=True)
    finally:
        image.close()
    return output_path


def render_process_image(
    rows: Sequence[Mapping[str, Any]], output_path: Path, *,
    columns: Sequence[tuple[str, str, str]] | None = None,
    total: Mapping[str, Any] | None = None,
) -> Path:
    """Render the requested navy-header, conditional-color table image."""

    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise RuntimeError("生成图片需要 Pillow；请在当前 D:\\anaconda3 环境安装 Pillow") from exc

    if not rows:
        raise SystemExit("过程数据视图没有可生成图片的记录")
    total = total if total is not None else make_total_row(rows, _string(_raw_field(rows[0], "期次")))
    rows = visible_image_rows(rows)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    # These widths deliberately follow the supplied reference image's wide,
    # dense table layout rather than producing a narrow chart card.  Optional
    # 6h/12h/24h columns disappear when the source view does not contain them.
    columns = tuple(columns) if columns is not None else available_image_columns(rows)
    widths = [IMAGE_WIDTHS[source] for source, _label, _kind in columns]
    header_height, row_height, total_height = 92, 64, 70
    width = sum(widths)
    height = header_height + row_height * len(rows) + total_height
    navy = "#203b72"
    grid = "#b8c4d3"
    image = Image.new("RGB", (width, height), "#ffffff")
    draw = ImageDraw.Draw(image)
    header_font = _find_font(27, bold=True)
    body_font = _find_font(25, bold=False)
    total_font = _find_font(28, bold=True)

    x_positions = [0]
    for column_width in widths:
        x_positions.append(x_positions[-1] + column_width)

    draw.rectangle((0, 0, width, header_height), fill=navy)
    for index, ((_source, label, _kind), left, right) in enumerate(zip(columns, x_positions, x_positions[1:])):
        header = label
        _center_text(draw, (left + 2, 0, right - 2, header_height), header, header_font, "#ffffff")
        draw.line((right - 1, 0, right - 1, height), fill=grid, width=1)
    draw.line((0, header_height - 1, width, header_height - 1), fill=grid, width=1)

    for row_index, row in enumerate(rows):
        top = header_height + row_index * row_height
        bottom = top + row_height
        for col_index, ((source, _label, kind), left, right) in enumerate(zip(columns, x_positions, x_positions[1:])):
            value = _raw_field(row, source)
            if source == "线索留存率":
                draw.rectangle((left, top, right, bottom), fill=_retention_color(value))
            else:
                draw.rectangle((left, top, right, bottom), fill="#ffffff")
            if source in BAR_FIELDS:
                rate = _rate(value)
                if rate is not None:
                    bar_width = max(0, min(1, rate)) * max(0, right - left - 12)
                    draw.rectangle((left + 6, top + 10, left + 6 + int(bar_width), bottom - 10), fill=BAR_FIELDS[source])
            text = _image_value(row, source, kind)
            _center_text(draw, (left + 2, top + 1, right - 2, bottom - 1), text, body_font, "#111827")
            draw.rectangle((left, top, right, bottom), outline=grid, width=1)

    total_top = header_height + row_height * len(rows)
    draw.rectangle((0, total_top, width, height), fill=navy)
    for (source, _label, kind), left, right in zip(columns, x_positions, x_positions[1:]):
        text = _image_value(total, source, kind)
        _center_text(draw, (left + 2, total_top + 1, right - 2, height - 1), text, total_font, "#ffffff")
        draw.rectangle((left, total_top, right, height), outline=grid, width=1)

    try:
        image.save(output_path, format="PNG", optimize=True)
    finally:
        # ``image.save`` has completed before this point; explicitly close the
        # Pillow object so the pixel buffer is released before the caller
        # proceeds to upload or send the message.
        image.close()
    return output_path
