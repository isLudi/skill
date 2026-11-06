"""One channel image containing ordered grade tables, using the deployed style."""
from copy import deepcopy
import hashlib
from pathlib import Path

from PIL import Image

from . import grade_bundle_compact as compact
from .channels.grade_compact import grade_sort_key


def render_channel(result, section, period, directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    component = result['component']
    sizes, panel_width = compact.layout([result], section)
    panels, checks, reminders = [], [], []
    for block in sorted(result['report']['blocks'], key=lambda item: grade_sort_key(item['grade'])):
        display = deepcopy(component)
        display['label'] = block['grade']
        path = directory / (block['grade'] + '-panel.png')
        check = compact.panel(display, block, section, panel_width, sizes, path)
        checks.append({'grade': block['grade'], **check})
        panels.append(path)
        names = block['reminders'][section]
        if names:
            reminders.append({'grade': block['grade'], 'channel': component['label'],
                              'names': names, 'grain': '主管'})
    if not panels:
        raise ValueError('Channel has no eligible grade blocks')
    margin, gap = 16, 14
    parts = []
    for path in panels:
        with Image.open(path) as image:
            parts.append(image.convert('RGB'))
    width = panel_width + margin * 2
    height = margin * 2 + sum(part.height for part in parts) + gap * (len(parts)-1)
    canvas = Image.new('RGB', (width, height), '#ffffff')
    try:
        y = margin
        for part in parts:
            canvas.paste(part, (margin, y))
            y += part.height + gap
        path = directory / 'channel-grades.png'
        canvas.save(path, format='PNG', optimize=True)
    finally:
        canvas.close()
        for part in parts:
            part.close()
    artifact = {'channel': component['label'], 'component_id': component['id'],
                'grades': [check['grade'] for check in checks], 'path': str(path),
                'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'width': width, 'height': height,
                'reminders': reminders}
    return artifact, checks
