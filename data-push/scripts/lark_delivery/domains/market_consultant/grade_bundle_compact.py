"""Reviewed compact grade-bundle layout; original colors and visible-row totals."""
from decimal import Decimal
from pathlib import Path

from PIL import Image, ImageDraw

from ...common.images import _center_text, _find_font
from ...common.values import _format_value, _rate
from .channels.grade_compact import grade_sort_key
from .grade_bundle_model import columns, renderer
from . import supervisor_report
from .style import _result_cell_fill

NAVY = '#203b72'
MUTED = '#60718b'
GRID = '#b8c4d3'
BAND = '#e8eef8'


def desired_width(source, label, values, kind):
    font = _find_font(20)
    measure = lambda text: round(font.getlength(str(text)))
    baseline = 136 if source == '期次' else 120 if source in {'负责人', '主管', '顾问'} else 100
    return max(baseline, measure(label) + 22,
               max((measure(_format_value(value, kind)) + 24 for value in values), default=0))


def layout(results, section):
    sizes = {}
    for result in results:
        cols, _ = columns(result['component'], section)
        fields = [row['fields'] for block in result['report']['blocks']
                  for row in [*block['rows'], *([block['total']] if result['report'].get('show_totals') else [])]]
        for source, label, kind in cols:
            key = (source, label, kind)
            sizes[key] = max(sizes.get(key, 0), desired_width(source, label,
                [row.get(source, '') for row in fields], kind))
    panel_width = max([sum(sizes[col] for col in columns(result['component'], section)[0])
                       for result in results] + [1380 if section == 'process' else 1160])
    return sizes, panel_width


def panel(component, block, section, width, sizes, path):
    cols, _ = columns(component, section)
    widths = [sizes[col] for col in cols]
    extra = width - sum(widths)
    weights = [1.2 if kind == 'text' else 1 for _, _, kind in cols]
    widths = [size + round(extra * weight / sum(weights)) for size, weight in zip(widths, weights)]
    widths[-1] += width - sum(widths)
    xs = [0]
    for size in widths:
        xs.append(xs[-1] + size)
    ordered = renderer(component).sorted_rows(block, section)
    band, header, row_height = 42, 46, 44
    show_total = component.get('show_totals', False)
    image_rows = [*ordered, block['total']] if show_total else ordered
    height = band + header + len(image_rows) * row_height + 1
    image = Image.new('RGB', (width, height), '#ffffff')
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, width, band), fill=BAND)
    draw.text((14, 5), component['label'], font=_find_font(23, True), fill=NAVY)
    metric = '5min' if section == 'process' else '截面单效'
    bars = renderer(component).BAR_COLORS
    if component['grain'] == '顾问' and section == 'process':
        bars = {'首call率': '#4f78ae', '5min': '#f5ae23', '双沟率': '#138de2'}
    effect_values = sorted({float(row['fields']['截面单效']) for row in ordered
                            if isinstance(row['fields'].get('截面单效'), (int, float, Decimal))}, reverse=True)
    cells = []
    for col, left, right in zip(cols, xs, xs[1:]):
        _, label, _ = col
        draw.rectangle((left, band, right, band+header), fill=NAVY)
        _center_text(draw, (left+5, band, right-5, band+header), label, _find_font(20, True), '#ffffff')
    for index, row in enumerate(image_rows):
        y = band + header + index * row_height
        total = show_total and index == len(ordered)
        draw.rectangle((0, y, width, y+row_height), fill=NAVY if total else '#ffffff')
        for (source, _, kind), left, right in zip(cols, xs, xs[1:]):
            value = row['fields'].get(source, '')
            text = _format_value(value, kind)
            if not total and source == '线索留存率':
                draw.rectangle((left+1, y+1, right-1, y+row_height-1),
                               fill=supervisor_report._retention_fill(value, _rate))
            if not total and source == '截面单效' and isinstance(value, (int, float, Decimal)):
                palette = ('#62bc7f', '#d9df83', '#f9c777', '#fa9a7e', '#fb626b')
                rank = effect_values.index(float(value))
                position = 2 if len(effect_values) <= 1 else round(rank * 4 / (len(effect_values)-1))
                color = palette[position] if component['grain'] == '主管' else _result_cell_fill(
                    '单效', value, rank, len(effect_values))
                draw.rectangle((left+1, y+1, right-1, y+row_height-1), fill=color)
            if not total and source in bars:
                rate = _rate(value) if kind == 'rate' else None
                if source == '人均报科' and isinstance(value, (int, float, Decimal)):
                    rate = min(1.0, max(0.0, float(value) / 3.0))
                if rate is not None and rate > 0:
                    draw.rectangle((left+4, y+7, left+4+int((right-left-8)*min(1, rate)),
                                    y+row_height-7), fill=bars[source])
            _center_text(draw, (left+6, y, right-6, y+row_height), text,
                         _find_font(20, total or source == metric), '#ffffff' if total else '#111827')
            cells.append({'row': index, 'field': source, 'text': text, 'box': [left, y, right, y+row_height]})
        draw.line((0, y+row_height, width, y+row_height), fill=GRID)
    for index in range(len(image_rows)+1):
        y = band + header + index * row_height
        draw.line((0, y, width, y), fill=GRID)
    for x in xs:
        draw.line((min(width-1, x), band, min(width-1, x), height-1), fill=GRID)
    draw.line((0, band, width, band), fill=GRID)
    draw.line((0, band+header, width, band+header), fill=GRID)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format='PNG', optimize=True)
    image.close()
    return {'path': str(path), 'width': width, 'height': height, 'rows': len(ordered),
            'total_rows': int(show_total), 'cells': cells}


def render(results, section, period, target_name, directory, outcomes):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    # A malformed channel must not fail the shared width pass for healthy channels.
    validated = []
    for result in results:
        component = result['component']
        try:
            layout([result], section)
            validated.append(result)
        except Exception as exc:
            outcomes[component['id']] = {'status': 'blocked_prepare', 'channel': component['label'],
                'reason': 'layout: ' + type(exc).__name__ + ': ' + str(exc)[:200]}
    results = validated
    if not results:
        return [], [], []
    sizes, panel_width = layout(results, section)
    panels, failed, checks = {}, set(), []
    for result in results:
        component = result['component']
        try:
            for block in result['report']['blocks']:
                path = directory / f"{component['id']}-{grade_sort_key(block['grade'])[0]}.png"
                check = panel(component, block, section, panel_width, sizes, path)
                checks.append({'component': component['id'], 'grade': block['grade'], **check})
                panels[component['id'], block['grade']] = path
        except Exception as exc:
            failed.add(component['id'])
            outcomes[component['id']] = {'status': 'blocked_prepare', 'channel': component['label'],
                                        'reason': 'render: ' + type(exc).__name__ + ': ' + str(exc)[:200]}
    results = [result for result in results if result['component']['id'] not in failed]
    grades = sorted({block['grade'] for result in results for block in result['report']['blocks']}, key=grade_sort_key)
    artifacts = []
    for index, grade in enumerate(grades):
        present = [result for result in results if (result['component']['id'], grade) in panels]
        width, margin, title, gap = panel_width + 32, 16, 90, 14
        parts = []
        for result in present:
            with Image.open(panels[result['component']['id'], grade]) as image:
                parts.append(image.convert('RGB'))
        height = title + sum(part.height for part in parts) + gap * max(0, len(parts)-1) + margin
        canvas = Image.new('RGB', (width, height), '#ffffff')
        draw = ImageDraw.Draw(canvas)
        label = '过程' if section == 'process' else '转化'
        grain = present[0]['component']['grain']
        draw.rectangle((0, 0, width, title-10), fill=BAND)
        draw.text((margin, 18), f'{period} · {grade} · {grain}{label}数据', font=_find_font(25, True), fill=NAVY)
        draw.text((margin, 59), target_name, font=_find_font(17), fill=MUTED)
        draw.line((margin, 83, width-margin, 83), fill=GRID)
        y = title
        for part in parts:
            canvas.paste(part, (margin, y))
            y += part.height + gap
            part.close()
        path = directory / f'grade-{index:02d}.png'
        canvas.save(path, format='PNG', optimize=True)
        canvas.close()
        reminders = []
        for result in present:
            block = next(item for item in result['report']['blocks'] if item['grade'] == grade)
            if block['reminders'][section]:
                reminders.append({'channel': result['component']['label'], 'names': block['reminders'][section],
                                  'grain': result['component']['grain']})
        artifacts.append({'grade': grade, 'path': str(path), 'component_ids': [item['component']['id'] for item in present],
                          'reminders': reminders, 'width': width, 'height': height})
    return results, artifacts, checks
