"""Independent period claims and retries for the grade-nine daily policy."""
from datetime import datetime
import hashlib
import json
from types import SimpleNamespace

from . import grade9_daily_policy as policy
from . import grade_bundle_delivery as delivery
from . import grade_bundle_source as source
from .channels.grade_compact import TZ, business_period, next_business_period

CLEAN = {'sent_verified', 'skipped_no_eligible_rows', 'skipped_no_source_rows', 'prepared'}


def _legacy_fence(definition, db, token, child_token, guard):
    """Preserve old same-slot deliveries during deployment; never clear a claim."""
    allowed = {item['id'] for item in definition['components']}
    outcomes = {}
    for row in db.execute('SELECT * FROM bundle_messages WHERE slot=?', (token,)).fetchall():
        identifiers = set(json.loads(row[5])) & allowed
        try:
            result = delivery.send_staged(db, row, guard)
        except Exception as exc:
            result = {'status': 'blocked_legacy_delivery', 'reason': type(exc).__name__ + ': ' + str(exc)[:200]}
        outcomes.update({name: result for name in identifiers})
    for (name,) in db.execute('SELECT channel FROM deliveries WHERE slot=?', (token,)).fetchall():
        if name in allowed and name not in outcomes:
            outcomes[name] = {'status': 'blocked_legacy_delivery', 'reason': 'Legacy claim has no recoverable bundle'}
    for name, result in outcomes.items():
        key = hashlib.sha256(('grade9-legacy|' + child_token + '|' + name).encode()).hexdigest()[:40]
        detail = json.dumps({'legacy_slot': token, 'migration_alias': True})
        db.execute('INSERT OR IGNORE INTO deliveries VALUES (?,?,?,?,?,?)',
            (key, child_token, name, result['status'], result.get('message_id', ''), detail))
        db.execute('UPDATE deliveries SET status=?,message_id=?,detail=? WHERE key=?',
            (result['status'], result.get('message_id', ''), detail, key))
    db.commit()
    return outcomes


def round_once(definition, target, db, state, slot, token, time_guard, preflight, log, run_one):
    delivery.init(db)
    at = datetime.now(TZ)
    period = business_period(at)
    specifications = policy.specifications(at.weekday(), period, next_business_period(period))
    cache = {}

    def load_source():
        if 'failure' in cache:
            raise RuntimeError(cache['failure'])
        if 'data' not in cache:
            try:
                folder = state / ('source-' + datetime.now(TZ).strftime('%H%M%S-%f'))
                folder.mkdir(parents=True, exist_ok=True)
                cache['data'] = source.read(definition, target, folder, slot)
            except Exception as exc:
                cache['failure'] = type(exc).__name__ + ': ' + str(exc)[:300]
                raise
        return cache['data']

    outcomes, paths = {}, []
    for specification in specifications:
        role = specification['role']
        child_token = token + '|grade9|' + role + '|' + specification['period']
        folder = state / 'periods' / role
        folder.mkdir(parents=True, exist_ok=True)
        proxy = SimpleNamespace(outcomes={})

        def report(name, status, reason='', **extra):
            proxy.outcomes[name] = {'status': status, 'reason': reason, **extra}
            log.outcome(role + '/' + name, status, reason, **extra)
        proxy.outcome = report
        legacy = {}
        try:
            time_guard()
            if not preflight and role != 'next_process':
                legacy = _legacy_fence(definition, db, token, child_token, time_guard)
            result = run_one(definition, target, db, folder, slot, child_token, time_guard, preflight, proxy,
                             grade9_spec=specification, grade9_source=load_source)
            period_outcomes = {**legacy, **result['outcomes']}
            if result.get('context_path'):
                paths.append(result['context_path'])
        except Exception as exc:
            period_outcomes = {**legacy, **{item['id']: {'status': 'blocked_period_prepare_or_delivery',
                'reason': type(exc).__name__ + ': ' + str(exc)[:300]}
                for item in definition['components'] if item['id'] not in legacy}}
            for row in db.execute('SELECT * FROM bundle_messages WHERE slot=?', (child_token,)).fetchall():
                if row[2] == 'sent_verified':
                    period_outcomes.update({name: {'status': 'sent_verified', 'message_id': row[3]}
                        for name in json.loads(row[5])})
        for name, result in period_outcomes.items():
            key = role + '/' + name
            outcomes[key] = result
            if name not in proxy.outcomes:
                log.outcome(key, result['status'], result.get('reason', ''), message_id=result.get('message_id'))
    return {'outcomes': outcomes, 'context_path': paths[0] if paths else None, 'context_paths': paths,
        'preflight': preflight, 'status': 'complete' if all(item['status'] in CLEAN for item in outcomes.values()) else 'needs_attention'}
