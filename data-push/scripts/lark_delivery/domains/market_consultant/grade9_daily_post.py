"""Native @ standards reminders and image-only Monday/Tuesday messages."""
from fractions import Fraction
import html
import json
from pathlib import Path


def native_post(context, image_keys, people):
    if context.get('grade9_preview_only'):
        raise ValueError('Preview parts must be sent as independent period messages')
    if len(image_keys) != len(context['artifacts']) or not image_keys:
        raise ValueError('Grade-nine image keys differ from prepared artifacts')
    only_images = context['section'] == 'process' and context['grade9_weekday'] in [0, 1]
    content = [] if only_images else [[{'tag': 'text', 'text': f"截至dt={context['snapshot'][0]}，hour={context['snapshot'][1]}时"}]]
    for artifact, image_key in zip(context['artifacts'], image_keys):
        content.append([{'tag': 'img', 'image_key': image_key}])
        if only_images:
            continue
        standards = artifact.get('standards', [])
        if standards:
            text = '；'.join(f"{item['channel']}≥{float(Fraction(item['target']))*100:.2f}%" for item in standards)
            content.append([{'tag': 'text', 'text': f"📌 {standards[0]['metric']}标准：{text}。", 'style': ['bold']}])
        for reminder in artifact['reminders']:
            row = [{'tag': 'text', 'text': reminder['channel'] + '：'}]
            for index, name in enumerate(reminder['names']):
                if index:
                    row.append({'tag': 'text', 'text': '、'})
                if name in people['resolved']:
                    row.append({'tag': 'at', 'user_id': people['resolved'][name],
                                'user_name': people['display_names'].get(name, name)})
                else:
                    row.append({'tag': 'text', 'text': name})
            ending = (f"未达到{reminder['metric']}标准，请重点跟进。" if reminder.get('standard') is not None
                      else f"的{reminder['metric']}较低，请重点关注。")
            row.append({'tag': 'text', 'text': ending})
            content.append(row)
    if not only_images:
        content.append([{'tag':'text','text':'继续加油，'}, {'tag':'text','text':'【祝本期爆单】','style':['bold']},
                        {'tag':'text','text':' 🚀🔥'}])
    return {'zh_cn': {'title': context['message_title'], 'content': content}}


def write_preview(context):
    from . import grade_bundle_delivery as delivery
    directory = Path(context['directory'])
    directory.mkdir(parents=True, exist_ok=True)
    parts = context.get('grade9_preview_parts', [context])
    people = delivery.resolve_people(context)
    pieces = []
    for part in parts:
        if not part['artifacts']:
            reasons = '；'.join(sorted({value.get('reason', value['status']) for value in part['outcomes'].values()}))
            pieces.append('<aside>' + html.escape(part['message_title']) + '：当前快照暂无可用图片。' + html.escape(reasons) + '</aside>')
            continue
        keys = ['LOCAL_IMAGE_' + str(index) for index in range(len(part['artifacts']))]
        message = native_post(part, keys, people)['zh_cn']
        pieces.append('<article><h2>' + html.escape(message['title']) + '</h2>')
        paths = {key: Path(item['path']).relative_to(directory).as_posix() for key, item in zip(keys, part['artifacts'])}
        for row in message['content']:
            fragments = []
            for node in row:
                if node['tag'] == 'img':
                    fragments.append('<img src="' + paths[node['image_key']] + '">')
                elif node['tag'] == 'at':
                    fragments.append('<span class="at">@' + html.escape(node['user_name']) + '</span>')
                else:
                    text = html.escape(node['text'])
                    fragments.append('<b>' + text + '</b>' if 'bold' in node.get('style', []) else text)
            pieces.append('<div class="row">' + ''.join(fragments) + '</div>')
        pieces.append('</article>')
        filename = directory / ('native-message-' + part['grade9_role'] + '.json')
        filename.write_text(json.dumps({'zh_cn': message}, ensure_ascii=False, indent=2), encoding='utf-8')
    page = '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><style>body{font:16px Microsoft YaHei;background:#f2f5f9;color:#20334d;padding:20px}main{max-width:1600px;margin:auto}article{background:white;border:1px solid #dce4f0;border-radius:12px;padding:22px;margin-bottom:20px}h2{font-size:23px}img{width:100%}.row{line-height:1.9;margin:10px 0}.at{color:#3376f4;background:#edf3ff;padding:2px 4px}aside{background:#fff8e6;padding:16px;margin:16px 0}</style><main>' + ''.join(pieces) + '</main></html>'
    path = directory / 'message-preview.html'
    path.write_text(page, encoding='utf-8')
    return {'html': str(path)}
