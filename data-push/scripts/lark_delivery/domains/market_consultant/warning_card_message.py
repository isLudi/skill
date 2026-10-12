"""Native Card 2.0 formatting shared by warning previews and delivery."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import html
import json
from pathlib import Path
import re

COLORS = {'red': '#c64743', 'green': '#177d58', 'orange': '#c76b08', 'grey': '#68758b'}
LOCAL_IMAGE = 'img_local_warning_preview'
POST_AT = re.compile(r'<at user_id="(ou_[A-Za-z0-9]+)">[^<]*</at>')
CARD_AT = re.compile(r'<at id=(ou_[A-Za-z0-9]+)></at>')
TOKENS = re.compile(r"<font color='(red|green|orange|grey)'>|</font>|<at id=(ou_[A-Za-z0-9]+)></at>|\*\*")


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True,
                                     separators=(',', ':')).encode('utf-8')).hexdigest()


def markdown(value):
    return POST_AT.sub(lambda match: f'<at id={match[1]}></at>', value)


def validate(card, mentions, *, image_key=LOCAL_IMAGE):
    """Fail before upload/send if styling, image or native @ scope drifted."""
    elements = card.get('body', {}).get('elements', [])
    if (card.get('schema') != '2.0' or card.get('config') != {
            'update_multi': True, 'width_mode': 'default'}
            or [e.get('element_id') for e in elements] != ['heading', 'metrics', 'image', 'reminder', 'closing']
            or [e.get('tag') for e in elements] != ['markdown', 'markdown', 'img', 'markdown', 'markdown']
            or elements[2].get('img_key') != image_key
            or elements[2].get('scale_type') != 'fit_horizontal'):
        raise ValueError('Warning card structure or image differs from the reviewed template')
    texts = [e['content'] for e in elements if e['tag'] == 'markdown']
    combined = '\n'.join(texts)
    stripped = TOKENS.sub('', combined)
    if re.search(r'<[^>]+>|style=|user_id=', stripped) or any(t.count('**') % 2 for t in texts):
        raise ValueError('Warning card contains unsupported markup or unbalanced emphasis')
    if combined.count('<font ') != combined.count('</font>'):
        raise ValueError('Warning card color markup is unbalanced')
    actual = CARD_AT.findall(combined)
    expected = {p['open_id'] for p in mentions['resolved'].values()}
    if set(actual) != expected or len(actual) != len(expected):
        raise ValueError('Warning card native reminders differ from verified group members')
    if elements[0].get('text_size') != 'heading-3' or any(
            e.get('text_size') != 'normal' for e in elements[1:] if e['tag'] == 'markdown'):
        raise ValueError('Warning card must have one title focus')
    if 'color=\'red\'' not in elements[0]['content']:
        raise ValueError('Warning channel title must use native red text')
    return card


def materialize(template, image_key, mentions):
    validate(template, mentions)
    if not re.fullmatch(r'img_[A-Za-z0-9_-]+', image_key) or image_key == LOCAL_IMAGE:
        raise ValueError('Warning card requires a real uploaded image key')
    card = deepcopy(template)
    card['body']['elements'][2]['img_key'] = image_key
    return validate(card, mentions, image_key=image_key)


def _html(value, mentions):
    people = {p['open_id']: p for p in mentions['resolved'].values()}
    result, cursor, bold = [], 0, False
    for token in TOKENS.finditer(value):
        result.append(html.escape(html.unescape(value[cursor:token.start()])).replace('\n', '<br>'))
        if token[1]:
            result.append(f'<span style="color:{COLORS[token[1]]}">')
        elif token[2]:
            person = people[token[2]]
            label = person['display_name']
            account = person.get('account_label')
            if account:
                label += f'（{account}）'
            result.append(f'<span class="mention">@{html.escape(label)}</span>')
        elif token[0] == '</font>':
            result.append('</span>')
        else:
            result.append('</strong>' if bold else '<strong>')
            bold = not bold
        cursor = token.end()
    result.append(html.escape(html.unescape(value[cursor:])).replace('\n', '<br>'))
    return ''.join(result)


def write_preview(output_dir, heading, metrics, reminder, closing, image_name, mentions):
    root = Path(output_dir)
    def block(element_id, content, size='normal'):
        return {'tag': 'markdown', 'element_id': element_id, 'text_size': size, 'content': markdown(content)}
    card = {'schema': '2.0', 'config': {'update_multi': True, 'width_mode': 'default'},
            'body': {'direction': 'vertical', 'padding': '12px 12px 20px 12px', 'vertical_spacing': '8px',
                     'elements': [block('heading', heading, 'heading-3'), block('metrics', '\n'.join(metrics)),
                                  {'tag': 'img', 'element_id': 'image', 'img_key': LOCAL_IMAGE,
                                   'alt': {'tag': 'plain_text', 'content': '渠道主管指标对比'},
                                   'scale_type': 'fit_horizontal', 'preview': True},
                                  block('reminder', reminder), block('closing', closing)]}}
    validate(card, mentions)
    (root / 'message-card-template.json').write_text(
        json.dumps(card, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    parts = []
    for element in card['body']['elements']:
        if element['tag'] == 'img':
            parts.append(f'<a href="{html.escape(image_name)}"><img src="{html.escape(image_name)}" alt="渠道主管指标对比"></a>')
        else:
            tag = 'h1' if element['element_id'] == 'heading' else 'p'
            parts.append(f'<{tag}>{_html(element["content"], mentions)}</{tag}>')
    document = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>预警消息 · 本地预览</title>
<style>body{margin:0;background:#f1f5fa;color:#243246;font:16px/1.8 "Microsoft YaHei",sans-serif}main{max-width:1100px;margin:24px auto;padding:0 16px}.status{color:#68758b;margin-bottom:12px}article{background:#fff;border:1px solid #dbe3ee;border-radius:12px;padding:20px 24px}h1{font-size:22px;line-height:1.5;margin:0 0 12px}p{margin:8px 0}img{display:block;width:100%;height:auto;margin:12px 0}.mention{color:#3370ff;background:#edf3ff;white-space:nowrap}a{color:inherit}@media(max-width:600px){main{padding:0 8px}article{padding:12px}h1{font-size:19px}}</style>
<main><div class="status">管家 · 本地卡片预览 · 尚未发送</div><article>''' + ''.join(parts) + '</article></main></html>'
    (root / 'message-preview.html').write_text(document, encoding='utf-8')
    preview = '\n\n'.join(e['content'] if e['tag'] == 'markdown' else f'![渠道主管指标对比]({image_name})'
                            for e in card['body']['elements']) + '\n'
    (root / 'message-preview.md').write_text(preview, encoding='utf-8')
    return {'message_type': 'interactive', 'card_schema': '2.0', 'message_card_sha256': fingerprint(card),
            'color_rendering_surface': 'feishu_card_markdown', 'remote_color_rendering_verified': False,
            'card_review': {'P0': 'required content and verified reminders present',
                            'P1': 'one heading focus', 'P2': 'heading metrics image reminder closing separated',
                            'P3': 'five blocks with a table image and three semantic color families',
                            'P4': 'title larger than body', 'P5': 'uniform container spacing',
                            'P6': 'red warning green advantage orange encouragement',
                            'P7': 'native colors responsive width and full image'}}


def send(chat_id, card, key, root):
    from . import warning_data as wd
    path = Path(root) / 'send_card.json'
    wd.save(path, card)
    return wd.api(['im', '+messages-send', '--chat-id', chat_id, '--msg-type', 'interactive',
                   '--content', '@' + str(path), '--idempotency-key', key, '--as', 'bot', '--format', 'json'])


def read_original(message_id):
    from . import warning_data as wd
    return wd.api(['api', 'GET', '/open-apis/im/v1/messages/' + message_id,
                   '--params', json.dumps({'user_id_type': 'open_id', 'card_msg_content_type': 'user_card_content'}),
                   '--as', 'bot', '--format', 'json'])
