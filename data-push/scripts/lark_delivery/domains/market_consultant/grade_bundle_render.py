"""Multi-image artifact protocol v2: one PNG per grade, ordered channel panels."""
from copy import deepcopy
import html
import json
from pathlib import Path

from PIL import Image

from ...common.images import _center_text, _find_font
from ...common.values import _format_value, _rate
from .channels.grade_compact import grade_sort_key
from .grade_bundle_model import columns, renderer


def render(results, section, period, target_name, directory, outcomes, *, style='legacy-v2'):
    if style == 'compact-original-colors-v1':
        from .grade_bundle_compact import render as render_compact
        kept, artifacts, _checks = render_compact(results, section, period, target_name, directory, outcomes)
        return kept, artifacts
    if style != 'legacy-v2':
        raise ValueError('Unreviewed grade-bundle image style')
    return _legacy_render(results, section, period, target_name, directory, outcomes)


def _legacy_render(results, section, period, target_name, directory, outcomes):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    panels, failed = {}, set()
    for result in results:
        component, report = result['component'], result['report']
        try:
            for block_index,block in enumerate(report['blocks']):
                path = directory / (component['id'] + '-' + str(block_index) + '.png')
                display_block = deepcopy(block)
                display_block['grade'] = component['label']
                cols, widths = columns(component, section)
                kwargs = dict(columns=cols, widths=widths, font_loader=_find_font,
                              center_text=_center_text, format_value=_format_value, rate_parser=_rate)
                if component['grain'] == '主管':
                    kwargs['show_totals'] = False
                renderer(component).render_image({**report, 'blocks': [display_block], 'show_totals': False},
                                                   section, path, **kwargs)
                panels[(component['id'], block['grade'])] = path
        except Exception as exc:
            failed.add(component['id'])
            outcomes[component['id']] = {'status': 'blocked_prepare', 'channel': component['label'],
                'reason': 'render: ' + type(exc).__name__ + ': ' + str(exc)[:200]}
    results = [result for result in results if result['component']['id'] not in failed]
    grades = sorted({block['grade'] for result in results for block in result['report']['blocks']}, key=grade_sort_key)
    artifacts = []
    for index, grade in enumerate(grades):
        present = [result for result in results if (result['component']['id'], grade) in panels]
        parts = [Image.open(panels[(result['component']['id'], grade)]).convert('RGB') for result in present]
        width, gap, margin = 2428, 20, 24
        height = margin * 2 + sum(part.height for part in parts) + gap * (len(parts)-1)
        canvas = Image.new('RGB', (width, height), '#ffffff')
        try:
            y = margin
            for part in parts:
                canvas.paste(part, (margin,y))
                y += part.height + gap
            path = directory / ('grade-%02d.png' % index)
            canvas.save(path, format='PNG', optimize=True)
        finally:
            canvas.close()
            for part in parts:
                part.close()
        reminders = []
        for result in present:
            block = next(block for block in result['report']['blocks'] if block['grade'] == grade)
            if block['reminders'][section]:
                reminders.append({'channel': result['component']['label'], 'names': block['reminders'][section],
                    'grain': result['component']['grain']})
        artifacts.append({'grade': grade, 'path': str(path), 'component_ids': [result['component']['id'] for result in present],
                          'reminders': reminders, 'width': width, 'height': height})
    return results, artifacts


def write_preview(context):
    path = Path(context['directory']) / 'message-preview.html'
    label = '过程' if context['section'] == 'process' else '转化'
    pieces = [f'<h1>🔥【{html.escape(context["period"])}】{html.escape(context["target"]["display_name"])}{label}数据播报</h1>',
              f'<p>截至dt={context["snapshot"][0]}，hour={context["snapshot"][1]}时</p>']
    for item in context['artifacts']:
        relative = Path(item['path']).relative_to(path.parent).as_posix()
        pieces.append(f'<h2>{html.escape(item["grade"])}</h2><img src="{relative}">')
        for reminder in item['reminders']:
            metric = '5min率' if context['section'] == 'process' else '截面单效'
            people = '、'.join(html.escape(name) for name in reminder['names'])
            pieces.append(f'<p>{html.escape(reminder["channel"])}：{people}，{metric}较低。</p>')
    pieces.append('<p>继续加油，<b>【祝本期爆单】</b> 🚀🔥</p>')
    page = '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><style>body{font:16px Microsoft YaHei;background:#f3f6fb;color:#20334d;padding:24px}main{max-width:1480px;margin:auto;background:white;padding:24px;border-radius:14px}img{width:100%}h1{font-size:25px}h2{font-size:20px}</style><main>'+''.join(pieces)+'</main></html>'
    path.write_text(page, encoding='utf-8')
    metadata = {key: context[key] for key in ['period','section','snapshot','outcomes','artifacts','artifact_protocol']}
    meta = path.with_name('preview-metadata.json')
    meta.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    return {'html': str(path), 'metadata': str(meta)}
