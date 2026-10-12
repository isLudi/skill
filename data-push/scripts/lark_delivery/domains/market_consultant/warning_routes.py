"""Exact report-to-group routing and isolated state for the warning batch."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path

# This allowlist binds the reviewed scope; values and enablement live in JSON.
APPROVED = {
    'koc_zhoushuai_high_school': ('KOC-周帅数学', 'koc_douyin_sync', ['高一', '高二', '高三'], '.'),
    'douyin_private_message_high_school': ('抖音私信', 'koc_douyin_sync', ['高一', '高二', '高三'],
                                           'channels/douyin_private_message'),
    'mengyafei_grade_9': ('KOC-孟亚飞数学', 'koc_middle_grade_9', ['初三'], 'reports/mengyafei_grade_9'),
    'self_incubated_grade_9': ('自孵化KOC-5元纯课', 'koc_middle_grade_9', ['初三'],
                              'reports/self_incubated_grade_9'),
    'self_incubated_high_school': ('自孵化KOC-5元纯课', 'self_incubated_high_school', ['高一', '高二', '高三'],
                                  'reports/self_incubated_high_school'),
}
TARGETS = {'koc_douyin_sync': 'oc_6f06cad338d520a89e1607a18592e56b',
           'koc_middle_grade_9': 'oc_601bde838d4fbda7ac09840a58228f9c',
           'self_incubated_high_school': 'oc_b9dc09ba622ca00059bbc472922a803d'}


def validate(definition):
    targets = definition['targets']
    if {t['id']: t['chat_id'] for t in targets} != TARGETS or len(targets) != len(TARGETS):
        raise ValueError('Warning report destination differs from the reviewed stable group IDs')
    routes = definition.get('broadcasts', [])
    if [r.get('id') for r in routes] != list(APPROVED):
        raise ValueError('Warning report identities or ordering changed')
    pairs, paths = set(), set()
    for route in routes:
        expected = APPROVED[route['id']]
        if (route.get('channel'), route.get('target_id'), route.get('included_grades'),
                route.get('state_relative')) != expected:
            raise ValueError('Warning report group, channel, grade scope or ledger path changed: ' + route['id'])
        if type(route.get('enabled')) is not bool:
            raise ValueError('Warning report enablement must be explicit')
        expected_scope = '初三' if expected[2] == ['初三'] else '高中'
        if route.get('school_scope') != expected_scope:
            raise ValueError('Warning report display scope differs from its grade filter')
        pair = (route['target_id'], route['channel'])
        path = state_for(definition, route)
        if pair in pairs or path in paths:
            raise ValueError('Duplicate warning route or report state')
        pairs.add(pair)
        paths.add(path)
    if list(dict.fromkeys(r['channel'] for r in routes)) != definition['channels']:
        raise ValueError('Warning source channels differ from report routes')


def selected(definition, targets):
    requested = {t['id']: t for t in targets}
    if any(t not in definition['targets'] for t in targets):
        raise ValueError('Unregistered warning target')
    return {r['id']: {**deepcopy(r), 'target': deepcopy(requested[r['target_id']])}
            for r in definition['broadcasts'] if r['enabled'] and r['target_id'] in requested
            and requested[r['target_id']]['enabled']}


def for_target(definition, target, channel):
    matches = [r for r in selected(definition, [target]).values() if r['channel'] == channel]
    if len(matches) != 1:
        raise ValueError('Channel is not routed to this warning group')
    return matches[0]


def state_for(definition, route):
    root = Path(definition['state_dir']).resolve()
    path = (root / route['state_relative']).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f'Warning report state escaped the batch root: {path} (root={root})')
    return path


def initialize_state(definition, route):
    """Create and recheck each ledger root before starting parallel workers."""
    path = state_for(definition, route)
    path.mkdir(parents=True, exist_ok=True)
    if path.resolve() != state_for(definition, route):
        raise ValueError('Warning report state changed during directory initialization')
    return path


def scoped_definition(definition, route):
    scope = deepcopy(definition)
    scope['report']['included_grades'] = deepcopy(route['included_grades'])
    return scope
