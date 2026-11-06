"""One channel card, grade-specific reminders and a matching local preview."""
import html
import json
from pathlib import Path
import re

from . import grade_report


def title(context):
    label = '过程' if context['section'] == 'process' else '转化'
    channel = context['results'][0]['component']['label']
    return f"🔥【{context['period']}】【{channel}】主管{label}数据播报"


def reminder_lines(context, people):
    metric = '5min率' if context['section'] == 'process' else '截面单效'
    lines = []
    for reminder in context['artifacts'][0]['reminders']:
        parts = []
        for name in reminder['names']:
            if name in people['resolved']:
                parts.append(f"<at id={people['resolved'][name]}></at>")
            else:
                parts.append(html.escape(name))
        lines.append(f"**{reminder['grade']}年级** " + '、'.join(parts) + f'的{metric}较低，请重点关注。')
    return lines


def build(context, image_keys, people):
    if len(image_keys) != 1 or len(context['artifacts']) != 1:
        raise ValueError('A channel card requires exactly one channel image')
    snapshot = f"截至dt={context['snapshot'][0]}，hour={context['snapshot'][1]}时"
    return {'schema':'2.0', 'config':{'width_mode':'fill','update_multi':True},
        'header':{'title':{'tag':'plain_text','content':title(context)},'template':'default'},
        'body':{'direction':'vertical','padding':'12px 12px 20px 12px','vertical_spacing':'12px',
            'elements':[
                {'tag':'markdown','content':snapshot},
                {'tag':'img','img_key':image_keys[0], 'alt':{'tag':'plain_text',
                    'content':context['results'][0]['component']['label']+'分年级数据'},
                    'scale_type':'fit_horizontal','preview':True},
                {'tag':'markdown','content':'\n'.join(reminder_lines(context,people))},
                {'tag':'markdown','content':"<font color='green'>继续加油，</font> **<font color='orange'>【祝本期爆单】</font>** 🚀🔥"}
            ]}}


def _normalize_mentions(value):
    if isinstance(value, dict):
        return {key:_normalize_mentions(item) for key,item in value.items()}
    if isinstance(value, list):
        return [_normalize_mentions(item) for item in value]
    if not isinstance(value, str):
        return value
    try:
        decoded = json.loads(value)
    except (ValueError, TypeError):
        decoded = None
    if isinstance(decoded, (dict,list)):
        return _normalize_mentions(decoded)
    return re.sub(r'''<at\s+id\s*=\s*["']?(ou_[A-Za-z0-9]+)["']?\s*>''',
                  lambda match: '<at user_id="'+match.group(1)+'">', html.unescape(value))


def mention_ids(content):
    return grade_report.mention_ids(_normalize_mentions(content))


def write_preview(context):
    from . import grade_bundle_delivery as delivery
    directory = Path(context['directory'])
    path = directory/'message-preview.html'
    if not context['artifacts']:
        path.write_text('<!doctype html><meta charset="utf-8"><p>当前渠道没有达到展示门槛的数据。</p>',encoding='utf-8')
        return {'html':str(path)}
    people = delivery.resolve_people(context)
    card = build(context,['LOCAL_PREVIEW_IMAGE_KEY'],people)
    artifact = context['artifacts'][0]
    relative = Path(artifact['path']).relative_to(directory).as_posix()
    reminders = []
    metric = '5min率' if context['section']=='process' else '截面单效'
    for reminder in artifact['reminders']:
        labels = []
        for name in reminder['names']:
            label = html.escape(people['display_names'].get(name,name))
            labels.append('<span class="at">@'+label+'</span>' if name in people['resolved'] else label)
        reminders.append('<p><b>'+html.escape(reminder['grade'])+'年级 </b>'+'、'.join(labels)+f'的{metric}较低，请重点关注。</p>')
    page = '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><style>body{font:16px Microsoft YaHei;background:#f2f5f9;color:#20334d;padding:24px}main{max-width:1180px;margin:auto;background:white;padding:24px;border-radius:14px}h1{font-size:23px}img{width:100%}.at{color:#3376f4}.green{color:#177d58}.orange{color:#d17808}</style><main><h1>'+html.escape(title(context))+f'</h1><p>截至dt={context["snapshot"][0]}，hour={context["snapshot"][1]}时</p><img src="{relative}">'+''.join(reminders)+'<p><span class="green">继续加油，</span> <strong class="orange">【祝本期爆单】</strong> 🚀🔥</p></main></html>'
    path.write_text(page,encoding='utf-8')
    card_path = directory/'native-card-preview.json'
    card_path.write_text(json.dumps(card,ensure_ascii=False,indent=2),encoding='utf-8')
    return {'html':str(path),'card':str(card_path)}
