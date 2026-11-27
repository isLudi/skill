"""Reviewed daily standards, name-only native reminders and a matching HTML preview."""
from fractions import Fraction
import html
import json
from pathlib import Path

from .high_school_daily_policy import WEEKDAYS


def title(context):
    component = context['results'][0]['component']
    return f"🔥【{context['period']}】【{component['label']}】主管数据播报"


def section_title(specification):
    name = '下期过程数据' if specification['role'] == 'next_process' else '本期转化数据' if specification['section'] == 'result' else '本期过程数据'
    return name + ' · ' + specification['period']


def lines(section, weekday, people, native):
    specification = section['specification']
    metric = specification['metric']
    if specification['section'] == 'result':
        result = ['📊 本期转化按截面单效从高到低排列。']
    elif specification['targets'] is None:
        return []
    else:
        standards = '、'.join(f'{grade}≥{float(Fraction(value))*100:.2f}%'
                             for grade, value in specification['targets'].items())
        result = [f'📌 {WEEKDAYS[weekday]}{metric}达标标准：{standards}。']
    for audit in section['audits']:
        names = []
        for name in audit['names']:
            label = html.escape(people['display_names'].get(name, name))
            if name in people['resolved']:
                label = f"<at id={people['resolved'][name]}></at>" if native else f'<span class="at">@{label}</span>'
            names.append(label)
        people_text = '、'.join(names)
        if specification['section'] == 'result':
            if names:
                result.append(f"📍 {audit['grade']}：{people_text}的截面单效较低，请重点关注。")
        elif names:
            result.append(f"⚠️ {audit['grade']}：{people_text}未达到{metric}标准，请重点跟进。")
        else:
            result.append(f"✅ {audit['grade']}：本次展示主管均达到{metric}标准。")
    return result


def build(context, image_keys, people):
    if len(image_keys) != len(context['artifacts']) or not image_keys:
        raise ValueError('Daily card image keys differ from prepared artifacts')
    elements = [{'tag': 'markdown', 'content': f"截至dt={context['snapshot'][0]}，hour={context['snapshot'][1]}时"}]
    for section in context['daily_sections']:
        if section['status'] != 'prepared':
            continue
        label = section_title(section['specification'])
        items = [{'tag': 'markdown', 'content': '**' + label + '**'},
            {'tag': 'img', 'img_key': image_keys[section['artifact_index']],
             'alt': {'tag': 'plain_text', 'content': label}, 'scale_type': 'fit_horizontal', 'preview': True}]
        reminders = lines(section, context['daily_weekday'], people, True)
        if reminders:
            items.append({'tag': 'markdown', 'content': '\n'.join(reminders)})
        elements.append({'tag': 'column_set', 'flex_mode': 'none', 'columns': [
            {'tag': 'column', 'width': 'weighted', 'weight': 1, 'direction': 'vertical',
             'vertical_spacing': '12px', 'elements': items}]})
    elements.append({'tag': 'markdown', 'content': "<font color='green'>继续加油，</font> **<font color='orange'>【祝本期爆单】</font>** 🚀🔥"})
    return {'schema': '2.0', 'config': {'width_mode': 'fill', 'update_multi': True},
        'header': {'title': {'tag': 'plain_text', 'content': title(context)}, 'template': 'default'},
        'body': {'direction': 'vertical', 'padding': '12px 12px 20px 12px', 'vertical_spacing': '12px', 'elements': elements}}


def write_preview(context):
    from . import grade_bundle_delivery as delivery
    directory = Path(context['directory'])
    people = delivery.resolve_people(context)
    elements = [f'<h1>{html.escape(title(context))}</h1>',
        f'<p>截至dt={context["snapshot"][0]}，hour={context["snapshot"][1]}时</p>']
    for section in context['daily_sections']:
        if section['status'] != 'prepared':
            continue
        artifact = context['artifacts'][section['artifact_index']]
        path = Path(artifact['path']).relative_to(directory).as_posix()
        elements += ['<section><h2>' + section_title(section['specification']) + '</h2>',
            f'<a href="{path}" target="_blank"><img src="{path}"></a>']
        elements += ['<p>' + line + '</p>' for line in lines(section, context['daily_weekday'], people, False)]
        elements.append('</section>')
    elements.append('<p><span class="green">继续加油，</span><b class="orange">【祝本期爆单】</b> 🚀🔥</p>')
    page = '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><style>body{font:16px Microsoft YaHei;background:#f2f5f9;color:#20334d;padding:24px}main{max-width:1400px;margin:auto;background:white;padding:24px;border-radius:14px}h1{font-size:25px}h2{font-size:21px}p{line-height:1.9}img{width:100%}.at{color:#3376f4;background:#edf3ff;padding:2px 4px}.green{color:#177d58}.orange{color:#d17808}</style><main>' + ''.join(elements) + '</main></html>'
    path = directory / 'message-preview.html'
    path.write_text(page, encoding='utf-8')
    card = directory / 'native-card-preview.json'
    card.write_text(json.dumps(build(context, ['LOCAL_PREVIEW_' + str(index) for index in range(len(context['artifacts']))], people),
        ensure_ascii=False, indent=2), encoding='utf-8')
    return {'html': str(path), 'card': str(card)}
