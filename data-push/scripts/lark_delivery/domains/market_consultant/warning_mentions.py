"""Resolve exact reminder accounts against a complete bot group membership read."""
from __future__ import annotations

from datetime import datetime
import re

from .warning_data import api, save


def resolve(data, metric, directory):
    baseline = data['team']['now'][metric]
    if baseline is None:
        raise ValueError('Team reminder denominator unavailable')
    names = [r['supervisor'] for r in data['rows']
             if r['now'][metric] is not None and r['now'][metric] > baseline]
    result = api(['im', '+chat-members-list', '--chat-id', data['target_chat_id'],
                  '--member-types', 'user', '--member-id-type', 'open_id', '--page-all',
                  '--page-limit', '0', '--as', 'bot', '--format', 'json'])
    members = result['data']
    save(directory / 'member_evidence.json', result)
    users = members.get('users', [])
    ids = {u['member_id'] for u in users}
    if (members.get('has_more') is not False or members.get('truncations')
            or len(ids) != len(users) or len(users) != int(members['user_total'])):
        raise ValueError('Incomplete or duplicate chat membership')
    resolved, missing = {}, []
    for name in names:
        candidates = [u for u in users if u.get('name') == name]
        if len(candidates) == 1:
            user = candidates[0]
            resolved[name] = {'open_id': user['member_id'], 'display_name': user['name'],
                              'source': 'unique_exact_chat_member_name', 'in_chat': True}
        else:
            missing.append(name)
    if missing:
        queries = {name: re.sub(r'\d+$', '', name) for name in missing}
        search = api(['contact', '+search-user', '--queries', ','.join(dict.fromkeys(queries.values())),
                      '--lang', 'zh_cn', '--as', 'user', '--format', 'json'])
        save(directory / 'contact_evidence.json', search)
        for name in missing:
            query_name = queries[name]
            query = next((q for q in search['data'].get('queries', []) if q['query'] == query_name), None)
            if query is None or query.get('error') or query.get('has_more'):
                raise ValueError('Incomplete reminder identity search: ' + name)
            candidates = []
            account_suffix = re.search(r'\d+$', name)
            for user in search['data'].get('users', []):
                if (user.get('matched_query') != query_name
                        or user.get('localized_name') not in {name, query_name}
                        or not user.get('is_activated') or user.get('is_cross_tenant')
                        or user.get('open_id') not in ids):
                    continue
                if account_suffix and user['localized_name'] != name:
                    prefix = (user.get('enterprise_email') or '').split('@', 1)[0]
                    suffix = re.search(r'\d+$', prefix)
                    if not suffix or suffix.group() != account_suffix.group():
                        continue
                candidates.append(user)
            if len({u['open_id'] for u in candidates}) != 1:
                raise ValueError('Reminder identity not unique in this chat: ' + name)
            user = candidates[0]
            resolved[name] = {'open_id': user['open_id'], 'display_name': user['localized_name'],
                              'source': 'contact_account_suffix_and_chat_membership', 'in_chat': True}
    labels = {'ou_d60ecaf6c5bc783d44f69267dfd3a724': 'lixiya02',
              'ou_06bad7a2ed473b356c5d518a3116b735': 'zhanghaofei01'}
    for person in resolved.values():
        if person['open_id'] in labels:
            person['account_label'] = labels[person['open_id']]
    if (set(resolved) != set(names) or len({u['open_id'] for u in resolved.values()}) != len(names)
            or any(not re.fullmatch(r'ou_[A-Za-z0-9]+', u['open_id']) for u in resolved.values())):
        raise ValueError('Missing or duplicate reminder account identity')
    evidence = {'chat_id': data['target_chat_id'], 'verification_identity': 'bot',
                'member_read_complete': True, 'user_total': len(users),
                'verified_at': datetime.now().isoformat(timespec='seconds'),
                'current_snapshot': data['current_snapshot'], 'source_table_id': data['source_table_id'],
                'source_rev': data['source_rev'], 'target_names': names, 'resolved': resolved,
                'selection': 'all_current_supervisors_above_full_channel_team_' + metric,
                'external_writes': False, 'message_sent': False}
    save(directory / 'mention_evidence.json', evidence)
    return evidence
