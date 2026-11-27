"""Offline regression checks for explicit outbound scheduled-slot backfills."""
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from lark_delivery import cli
from lark_delivery.core import catalog
from lark_delivery.domains.market_consultant import volume_backfill as backfill
from lark_delivery.domains.market_consultant.grade_bundle_source import save
from lark_delivery.domains.market_consultant.window import TZ

SLOT = datetime(2026, 11, 16, 17, tzinfo=TZ)


@pytest.fixture
def setup(monkeypatch, tmp_path):
    definition = catalog.load_channel('market_consultant/outbound_volume')
    definition['state_dir'] = str(tmp_path)
    target = definition['targets'][0]

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 11, 16, 19, tzinfo=TZ)

    @contextmanager
    def scope(*args):
        yield SimpleNamespace(exit_code=0, outcome=lambda *args, **kwargs: None)

    monkeypatch.setattr(backfill, 'datetime', Clock)
    monkeypatch.setattr(backfill.push_log, 'run_scope', scope)
    monkeypatch.setattr(backfill.catalog, 'load_channel', lambda key: definition)
    monkeypatch.setattr(backfill.immediate, 'latest_upstream_slot', lambda now: SLOT)
    monkeypatch.setattr(backfill.adapter, 'guard', lambda context: None)
    monkeypatch.setattr(backfill.adapter, 'write_preview', lambda context: None)
    preparations = []

    def prepare(definition, target, *, state_dir, slot):
        preparations.append(slot)
        context = {'definition': definition, 'target': target, 'directory': str(state_dir),
                   'snapshot': ['20261116', 15], 'section': 'volume',
                   'component_ids': ['outbound_volume'], 'source': {'source_slot': slot.isoformat()}}
        save(state_dir/'context.json', context)
        return context

    monkeypatch.setattr(backfill.adapter, 'prepare', prepare)
    return definition, target, preparations


def test_preflight_has_no_send_or_message_claim(setup, monkeypatch):
    definition, target, preparations = setup
    monkeypatch.setattr(backfill.delivery, 'stage_and_send', lambda *args: pytest.fail('Sending in preflight'))
    assert backfill.run(definition, target, 'preview', SLOT, preflight=True) == 0
    with backfill.connect_ledger(Path(definition['state_dir'])) as db:
        assert db.execute('SELECT COUNT(*) FROM bundle_messages').fetchone()[0] == 0
    assert preparations == [SLOT]


def test_backfill_reuses_formal_slot_across_request_ids(setup, monkeypatch):
    definition, target, preparations = setup
    claims = []

    def send_staged(db, row, guard):
        guard()
        claims.append((row[0], row[1]))
        return {'status': 'sent_verified', 'message_id': 'mock-message'}

    monkeypatch.setattr(backfill.delivery, 'send_staged', send_staged)
    for request in ['first', 'second']:
        assert backfill.run(definition, target, request, SLOT) == 0
    assert claims[0] == claims[1]
    assert claims[0][1] == SLOT.isoformat()
    assert preparations == [SLOT]


def test_existing_immediate_cycle_blocks_backfill(setup):
    definition, target, preparations = setup
    state = Path(definition['state_dir'])
    context_path = state/'old-context.json'
    save(context_path, {'source': {'source_slot': SLOT.isoformat()}, 'target': target})
    with backfill.connect_ledger(state) as db:
        backfill.delivery.init(db)
        db.execute('INSERT INTO bundle_messages VALUES (?,?,?,?,?,?,?)',
                   ('old-key', 'now:old-request', 'sent_verified', 'mock-message', str(context_path), '[]', '{}'))
        db.commit()
    with pytest.raises(ValueError, match='immediate claim'):
        backfill.run(definition, target, 'another', SLOT)
    assert preparations == []


def test_rejects_app_and_naive_slot(setup):
    definition, target, _ = setup
    with pytest.raises(ValueError, match='explicit'):
        backfill.run(definition, target, 'naive', SLOT.replace(tzinfo=None))
    app = {**definition, 'channel_id': 'app_volume', 'channel': 'APP', 'channels': ['APP']}
    with pytest.raises(ValueError):
        backfill.run(app, target, 'app', SLOT)


def test_cli_requires_confirmation_before_backfill(monkeypatch):
    monkeypatch.setattr(backfill.adapter, 'send_backfill', lambda *args, **kwargs: pytest.fail('Reached send'))
    with pytest.raises(SystemExit) as exc:
        cli.main(['send-backfill', '--target', 'outbound', '--slot', SLOT.isoformat(),
                  '--request-id', 'outbound-volume-backfill-20261116-1700'],
                 bound_channel='market_consultant/outbound_volume')
    assert exc.value.code == 2
