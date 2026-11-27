"""Failed channel/period previews must not block independent deliveries or resend successes."""
from datetime import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

_spec = importlib.util.spec_from_file_location('grade9_standard_fixtures', Path(__file__).with_name('test_grade9_daily_standards.py'))
_fixtures = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fixtures)
fixture, TZ = _fixtures.fixture, _fixtures.TZ
from lark_delivery.domains.market_consultant import grade_bundle_runner as runner
from lark_delivery.domains.market_consultant import grade_bundle_adapter as adapter
from lark_delivery.domains.market_consultant import grade_bundle_delivery as delivery
from lark_delivery.domains.market_consultant import grade_bundle_source as source
from lark_delivery.domains.market_consultant import grade9_daily_runner as daily_runner
from lark_delivery.domains.market_consultant import grade9_daily_prepare as preparing
from lark_delivery.domains.market_consultant import grade9_daily_policy as policy
from lark_delivery.domains.market_consultant.delivery_ledger import connect_ledger

AT = datetime(2026, 11, 27, 14, tzinfo=TZ)


class Clock(datetime):
    @classmethod
    def now(cls, tz=None):
        return AT


def scenario(monkeypatch, tmp_path):
    definition, rows, proof = fixture()
    monkeypatch.setattr(runner, 'datetime', Clock)
    monkeypatch.setattr(adapter, 'datetime', Clock)
    monkeypatch.setattr(daily_runner, 'datetime', Clock)
    monkeypatch.setattr(preparing, 'datetime', Clock)
    reader = Mock(return_value=(rows, proof))
    monkeypatch.setattr(source, 'read', reader)
    monkeypatch.setattr(adapter, 'write_preview', lambda _: None)
    calls = []

    def stage(db, context, token, guard):
        guard()
        calls.append((context['grade9_role'], context['component_ids']))
        key = hashlib.sha256((token + '|' + ','.join(context['component_ids'])).encode()).hexdigest()[:40]
        message_id = 'om_' + key
        db.execute('INSERT INTO bundle_messages VALUES (?,?,?,?,?,?,?)',
            (key, token, 'sent_verified', message_id, str(Path(context['directory'])/'context.json'),
             json.dumps(context['component_ids']), '{}'))
        for name in context['component_ids']:
            component_key = hashlib.sha256((key + name).encode()).hexdigest()[:40]
            db.execute('INSERT INTO deliveries VALUES (?,?,?,?,?,?)',
                (component_key, token, name, 'sent_verified', message_id, '{}'))
        db.commit()
        return {'status': 'sent_verified', 'message_id': message_id, 'component_ids': context['component_ids']}

    monkeypatch.setattr(delivery, 'stage_and_send', stage)
    monkeypatch.setattr(delivery, 'send_staged', lambda db, row, guard:
        {'status': row[2], 'message_id': row[3], 'component_ids': json.loads(row[5])})
    log = SimpleNamespace(outcomes={})
    log.outcome = lambda name, status, reason='', **extra: log.outcomes.update({name: {'status':status, **extra}})
    db = connect_ledger(tmp_path/'ledger')
    return definition, db, log, calls, reader, proof


def run(definition, db, log, tmp_path):
    return runner.round_once(definition, definition['targets'][0], db, tmp_path/'state', AT,
        AT.isoformat(), lambda: None, False, log)


def test_one_channel_standard_failure_is_local_to_one_period_and_retry(monkeypatch, tmp_path):
    definition, db, log, calls, reader, _ = scenario(monkeypatch, tmp_path)
    normal = policy.apply
    failing = {'active': True}

    def injected(result, specification, weekday):
        if failing['active'] and result['component']['id'] == 'draft_13_1' and specification['role'] == 'current_conversion':
            raise ValueError('Injected one-channel policy failure')
        return normal(result, specification, weekday)

    monkeypatch.setattr(policy, 'apply', injected)
    first = run(definition, db, log, tmp_path)
    assert first['status'] == 'needs_attention'
    assert calls[0][0] == 'current_conversion' and 'draft_13_1' not in calls[0][1]
    assert calls[1][0] == 'next_process' and len(calls[1][1]) == 6
    assert reader.call_count == 1
    failing['active'] = False
    second = run(definition, db, log, tmp_path)
    assert second['status'] == 'complete'
    assert calls[2] == ('current_conversion', ['draft_13_1']) and len(calls) == 3
    db.close()


def test_current_preview_failure_does_not_claim_or_block_next_period(monkeypatch, tmp_path):
    definition, db, log, calls, _, _ = scenario(monkeypatch, tmp_path)
    def fail_current(context):
        if context['grade9_role'] == 'current_conversion':
            raise OSError('Injected current HTML failure')
    monkeypatch.setattr(adapter, 'write_preview', fail_current)
    first = run(definition, db, log, tmp_path)
    assert first['status'] == 'needs_attention'
    assert [role for role, _ in calls] == ['next_process']
    monkeypatch.setattr(adapter, 'write_preview', lambda _: None)
    second = run(definition, db, log, tmp_path)
    assert second['status'] == 'complete'
    assert [role for role, _ in calls] == ['next_process', 'current_conversion']
    db.close()


def test_missing_future_audit_still_sends_current_and_never_substitutes_previous_period(monkeypatch, tmp_path):
    definition, db, log, calls, reader, proof = scenario(monkeypatch, tmp_path)
    del proof['evidence']['periods']['20261204期']
    first = run(definition, db, log, tmp_path)
    assert first['status'] == 'needs_attention'
    assert [role for role, _ in calls] == ['current_conversion']
    assert all(value['status'] == 'blocked_source_period' for name, value in first['outcomes'].items() if name.startswith('next_process/'))
    assert reader.call_count == 1
    db.close()


def test_old_same_slot_receipt_fences_current_but_not_new_next_period(monkeypatch, tmp_path):
    definition, db, log, calls, _, _ = scenario(monkeypatch, tmp_path)
    delivery.init(db)
    identifiers = [item['id'] for item in definition['components']]
    db.execute('INSERT INTO bundle_messages VALUES (?,?,?,?,?,?,?)',
        ('old', AT.isoformat(), 'sent_verified', 'om_old', 'old-context', json.dumps(identifiers), '{}'))
    for name in identifiers:
        db.execute('INSERT INTO deliveries VALUES (?,?,?,?,?,?)',
            ('old-'+name, AT.isoformat(), name, 'sent_verified', 'om_old', '{}'))
    db.commit()
    result = run(definition, db, log, tmp_path)
    assert result['status'] == 'complete'
    assert [role for role, _ in calls] == ['next_process']
    assert db.execute('SELECT status FROM bundle_messages WHERE key=?', ('old',)).fetchone()[0] == 'sent_verified'
    db.close()
