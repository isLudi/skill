"""Resolve exact reminder accounts against a complete bot group membership read."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
import re

from .warning_data import api, save
from .warning_reminder_policy import conversion_policy


def resolve(data, metric, directory):
    baseline = data['team']['now'][metric]
    if baseline is None:
        raise ValueError('Team reminder denominator unavailable')
    policy = conversion_policy(data) if metric == 'unit' else None
    names = policy['target_names'] if policy else [r['supervisor'] for r in data['rows']
             if r['now'][metric] is not None and Decimal(str(r['now'][metric])) > Decimal(str(baseline))]
    data['mention_failure_policy'] = 'plain_name'
    membership_error = ''
    try:
        result = api(['im', '+chat-members-list', '--chat-id', data['target_chat_id'],
                      '--member-types', 'user', '--member-id-type', 'open_id', '--page-all',
                      '--page-limit', '0', '--as', 'bot', '--format', 'json'])
        members = result['data']
        users = members.get('users', [])
        ids = {u['member_id'] for u in users}
        if (members.get('has_more') is not False or members.get('truncations')
                or len(ids) != len(users) or len(users) != int(members['user_total'])
                or any(not re.fullmatch(r'ou_[A-Za-z0-9]+', str(oid)) for oid in ids)):
            raise ValueError('Incomplete or duplicate chat membership')
    except Exception as exc:
        membership_error = type(exc).__name__
        result = {'membership_read_complete': False, 'error_type': membership_error}
        users, ids = [], set()
    save(directory / 'member_evidence.json', result)
    resolved, missing, fallback_names = {}, [], {}
    for name in names:
        if membership_error:
            fallback_names[name] = {'display_name': name, 'reason': 'Chat membership not verified'}
            continue
        candidates = [u for u in users if u.get('name') == name]
        if len(candidates) == 1:
            user = candidates[0]
            resolved[name] = {'open_id': user['member_id'], 'display_name': user['name'],
                              'source': 'unique_exact_chat_member_name', 'in_chat': True}
        else:
            missing.append(name)
    if missing:
        queries = {name: re.sub(r'\d+$', '', name) for name in missing}
        try:
            search = api(['contact', '+search-user', '--queries', ','.join(dict.fromkeys(queries.values())),
                          '--lang', 'zh_cn', '--as', 'user', '--format', 'json'])
            payload = search.get('data')
            if (not isinstance(payload, dict) or not isinstance(payload.get('queries'), list)
                    or not isinstance(payload.get('users'), list)):
                raise ValueError('Incomplete contact search response')
        except Exception as exc:
            search = {'data': {'queries': [], 'users': []}, 'lookup_error': str(exc)[:500]}
        save(directory / 'contact_evidence.json', search)
        for name in missing:
            query_name = queries[name]
            query = next((q for q in search.get('data', {}).get('queries', [])
                          if isinstance(q, dict) and q.get('query') == query_name), None)
            if query is None or query.get('error') or query.get('has_more') is not False:
                fallback_names[name] = {'display_name': name, 'reason': 'Reminder identity search incomplete'}
                continue
            candidates = []
            account_suffix = re.search(r'\d+$', name)
            for user in search.get('data', {}).get('users', []):
                if not isinstance(user, dict) or not isinstance(user.get('localized_name'), str):
                    continue
                if (user.get('matched_query') != query_name
                        or user.get('localized_name') not in {name, query_name}
                        or not user.get('is_activated') or user.get('is_cross_tenant')):
                    continue
                if account_suffix and user['localized_name'] != name:
                    prefix = (user.get('enterprise_email') or '').split('@', 1)[0]
                    suffix = re.search(r'\d+$', prefix)
                    if not suffix or suffix.group() != account_suffix.group():
                        continue
                candidates.append(user)
            invalid_ids = any(not isinstance(u.get('open_id'), str)
                              or not re.fullmatch(r'ou_[A-Za-z0-9]+', u['open_id']) for u in candidates)
            unique = {u['open_id'] for u in candidates if isinstance(u.get('open_id'), str)}
            if invalid_ids or len(unique) != 1 or not unique.issubset(ids):
                label = candidates[0]['localized_name'] if len(unique) == 1 else name
                reason = 'Not in target chat' if len(unique) == 1 else 'Reminder account not uniquely verified'
                fallback_names[name] = {'display_name': label, 'reason': reason}
                continue
            user = candidates[0]
            resolved[name] = {'open_id': user['open_id'], 'display_name': user['localized_name'],
                              'source': 'contact_account_suffix_and_chat_membership', 'in_chat': True}
    labels = {'ou_d60ecaf6c5bc783d44f69267dfd3a724': 'lixiya02',
              'ou_06bad7a2ed473b356c5d518a3116b735': 'zhanghaofei01'}
    for person in resolved.values():
        if person['open_id'] in labels:
            person['account_label'] = labels[person['open_id']]
    accounts = [person['open_id'] for person in resolved.values()]
    for name, person in list(resolved.items()):
        if accounts.count(person['open_id']) > 1 or not re.fullmatch(r'ou_[A-Za-z0-9]+', str(person['open_id'])):
            fallback_names[name] = {'display_name': person['display_name'], 'reason': 'Reminder account not uniquely verified'}
            resolved.pop(name)
    if (set(resolved) | set(fallback_names) != set(names)
            or set(resolved) & set(fallback_names)
            or len({u['open_id'] for u in resolved.values()}) != len(resolved)
            or any(not re.fullmatch(r'ou_[A-Za-z0-9]+', u['open_id']) for u in resolved.values())):
        raise ValueError('Missing or duplicate reminder account identity')
    evidence = {'chat_id': data['target_chat_id'], 'verification_identity': 'bot',
                'member_read_complete': not membership_error, 'user_total': len(users) if not membership_error else None,
                'member_lookup_error': membership_error,
                'verified_at': datetime.now().isoformat(timespec='seconds'),
                'current_snapshot': data['current_snapshot'], 'source_table_id': data['source_table_id'],
                'source_rev': data['source_rev'], 'target_names': names, 'resolved': resolved,
                'fallback_names': fallback_names, 'mention_failure_policy': 'plain_name',
                'all_reminder_people_in_chat': not fallback_names,
                'selection': policy['selection'] if policy else
                             'all_current_supervisors_above_full_channel_team_' + metric,
                'external_writes': False, 'message_sent': False}
    if policy:
        evidence.update(reminder_mode=policy['mode'], reminder_population=policy['population'])
    save(directory / 'mention_evidence.json', evidence)
    return evidence
