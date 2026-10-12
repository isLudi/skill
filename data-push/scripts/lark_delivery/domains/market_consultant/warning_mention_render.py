"""Render verified native mentions and explicitly allowed plain-name fallbacks."""
import html
import re


def fragments(data, evidence, names):
    resolved, fallback = evidence['resolved'], evidence.get('fallback_names', {})
    if set(resolved) | set(fallback) != set(names) or set(resolved) & set(fallback):
        raise ValueError('Reminder person evidence differs from selected names')
    if fallback and (data.get('mention_failure_policy') != 'plain_name'
                     or evidence.get('mention_failure_policy') != 'plain_name'):
        raise ValueError('Plain-name reminder fallback is not configured')
    if resolved and evidence.get('member_read_complete') is not True:
        raise ValueError('Native reminder accounts require a complete membership read')
    entries, markdown, markup, nodes, plain_entries = [], [], [], [], []
    for name in names:
        if nodes:
            nodes.append({'tag': 'text', 'text': ' '})
        if name in fallback:
            person = fallback[name]
            label = person['display_name']
            # These are ordinary text nodes. No @ or account ID is fabricated.
            markdown.append(html.escape(label))
            markup.append(html.escape(label))
            nodes.append({'tag': 'text', 'text': label})
            plain_entries.append({'supervisor': name, **person})
            continue
        person = resolved[name]
        user_id = person.get('open_id', '')
        if not person.get('in_chat') or not re.fullmatch(r'ou_[A-Za-z0-9]+', user_id):
            raise ValueError('Native reminder target is not verified in this group: ' + name)
        account = person.get('account_label', '')
        if account and not re.fullmatch(r'[A-Za-z0-9._-]+', account):
            raise ValueError('Invalid reminder account display label')
        suffix = f'（{account}）' if account else ''
        label = html.escape(person['display_name'])
        # The client renders the real account label for native @ nodes.
        # Adding the account suffix ourselves can duplicate it in the chat.
        markdown.append(f'<at user_id="{user_id}">{label}</at>')
        markup.append(f'<span class="mention" data-user-id="{user_id}">@{label}{suffix}</span>')
        nodes.append({'tag': 'at', 'user_id': user_id})
        entries.append({'supervisor': name, 'display_name': person['display_name'],
                        'open_id': user_id, 'account_label': account})
    if len({p['open_id'] for p in entries}) != len(entries):
        raise ValueError('Duplicate native reminder IDs')
    return entries, markdown, markup, nodes, plain_entries
