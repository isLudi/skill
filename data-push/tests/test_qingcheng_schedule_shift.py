"""Cross-hour windows, independent audiences and production period regression checks."""
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import run_qingcheng_process as process
import run_qingcheng_partner_process as partner
import run_qingcheng_special_process as special
import run_qingcheng_sec_process as sec
import run_qingcheng_transformation as conversion
import export_conversion_refresh as export

ZONE = ZoneInfo('Asia/Shanghai')


@pytest.mark.parametrize('runner,config', [(process, process._batch), (partner, partner._config),
                                          (special, special._config)])
def test_process_crosses_hour_without_changing_the_original_slot(runner, config):
    cfg = config()
    start = datetime(2026, 10, 8, 13, 50, tzinfo=ZONE)
    for now in (start, start.replace(minute=52), start.replace(hour=14, minute=0),
                start.replace(hour=14, minute=40, second=59)):
        assert runner._slot(now, cfg) == start
    assert runner._period(start.date()) == '20261009期'
    for now in (start.replace(minute=48), start.replace(minute=51),
                start.replace(hour=14, minute=42), start.replace(day=9),
                start.replace(tzinfo=ZoneInfo('UTC'))):
        with pytest.raises(ValueError):
            runner._slot(now, cfg)


def test_new_process_start_reads_the_immediately_preceding_upstream_cycle():
    # The source cycle is normalized to HH:00; the execution actually starts at :40.
    assert process._expected_upstream_period_time(datetime(2026, 10, 8, 13, 50, tzinfo=ZONE)) == '2026-10-08 13:00:00'


def test_sec_clock_remains_at_the_reviewed_hours():
    cfg = sec._config()
    for hour in (12, 16, 20):
        now = datetime(2026, 10, 8, hour, 0, tzinfo=ZONE)
        assert sec._slot(now, cfg) == now
    with pytest.raises(ValueError):
        sec._slot(datetime(2026, 10, 8, 13, 50, tzinfo=ZONE), cfg)


@pytest.mark.parametrize('audience,expected_count', [('standard', 9), ('dept', 4)])
def test_audience_preparation_and_send_failures_are_isolated(monkeypatch, tmp_path, audience, expected_count):
    sent, built, caches = [], [], []
    def fetch(channel, period, output):
        return {'rev': 1, 'snapshot': ['20261009', '12']}
    def refresh(channel, period, output, *, cache_dir):
        caches.append(cache_dir)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text('{}\n', encoding='utf-8')
        return {'rev': 2}
    def build(_p, _c, output, _config, *, channels, period, levels):
        channel, level = channels[0], levels[0]
        built.append((channel, level))
        if channel == 'private' and level == ('dept' if audience == 'dept' else 'supervisor'):
            raise ValueError('one image cannot be prepared')
        return {'period': period, 'process_snapshot': '20261009 12:00',
                'conversion_snapshot': '20261009 12:00',
                'results': {channel: {'levels': {level: {'level': level}}}}}
    def send(channel, level, *_args):
        sent.append((channel, level))
        if channel == 'public_pool' and level == ('dept' if audience == 'dept' else 'supervisor'):
            raise ValueError('one person cannot be resolved')
        return {'status': 'sent_verified'}
    monkeypatch.setattr(conversion, 'fetch', fetch)
    monkeypatch.setattr(conversion, 'export_conversion', refresh)
    monkeypatch.setattr(conversion, 'build', build)
    monkeypatch.setattr(conversion, '_index', lambda *args: None)
    monkeypatch.setattr(conversion, 'probe_revision', lambda *args: 1)
    monkeypatch.setattr(conversion, '_probe_conversion_rev', lambda *args: 2)
    monkeypatch.setattr(conversion, '_send_group', send)
    now = datetime(2026, 10, 9, 13, 50 if audience == 'dept' else 52, tzinfo=ZONE)
    result = conversion.run(confirm_send=True, now=now, output=tmp_path / audience, audience=audience)
    assert len(built) == expected_count
    assert len(sent) == expected_count - 1
    assert all((level == 'dept') == (audience == 'dept') for _, level in built)
    assert all(audience in str(path) for path in caches)
    statuses = [group['status'] for item in result['channels'].values() for group in item['groups'].values()]
    assert statuses.count('blocked_prepare') == 1
    assert statuses.count('blocked') == 1
    assert statuses.count('sent_verified') == expected_count - 2
    if audience == 'standard':
        assert result['channels']['private']['groups']['consultant']['status'] == 'sent_verified'
        review = json.loads((tmp_path / audience / 'public_pool/review.json').read_text(encoding='utf-8'))
        assert set(review['results']['public_pool']['levels']) == {'supervisor', 'consultant'}
    else:
        assert 'partner_local' not in result['channels']


def test_all_audiences_cannot_be_sent_by_one_production_invocation(tmp_path):
    with pytest.raises(ValueError, match='separate'):
        conversion.run(confirm_send=True, audience='all', output=tmp_path)


def test_audience_locks_allow_independent_runs_and_reject_same_audience(monkeypatch, tmp_path):
    monkeypatch.setattr(conversion, 'STATE', tmp_path)
    with conversion._single_instance('standard'):
        with conversion._single_instance('dept'):
            # Windows can reject reading the byte before the explicit lock attempt.
            with pytest.raises((PermissionError, RuntimeError)):
                with conversion._single_instance('standard'):
                    pytest.fail('same audience acquired the lock twice')
    for runner in (partner, special):
        monkeypatch.setattr(runner, 'STATE', tmp_path / runner.__name__)
        with runner._single_instance():
            with pytest.raises((PermissionError, RuntimeError)):
                with runner._single_instance():
                    pytest.fail('process batch acquired the lock twice')


def test_conversion_exports_do_not_share_the_page_files(monkeypatch, tmp_path):
    paths = []
    def lark(args, **_kwargs):
        path = Path(args[args.index('--output') + 1])
        paths.append(path)
        path.write_text('{}\n', encoding='utf-8')
        path.with_suffix('.manifest.json').write_text(json.dumps({'rev': 1, 'has_more': False}), encoding='utf-8')
    monkeypatch.setattr(export, 'run_lark', lark)
    for audience in ('standard', 'dept'):
        export.export_conversion('public_pool', '', tmp_path / audience / 'source.ndjson',
                                 cache_dir=tmp_path / audience / 'pages')
    assert paths[0] != paths[1]


def test_incomplete_conversion_pagination_cannot_claim_a_complete_export(monkeypatch, tmp_path):
    def lark(args, **_kwargs):
        path = Path(args[args.index('--output') + 1])
        path.write_text('{}\n', encoding='utf-8')
        path.with_suffix('.manifest.json').write_text(json.dumps({'rev': 1, 'has_more': True}), encoding='utf-8')
    monkeypatch.setattr(export, 'run_lark', lark)
    output = tmp_path / 'source.ndjson'
    with pytest.raises(ValueError, match='complete result'):
        export.export_conversion('public_pool', '', output, cache_dir=tmp_path / 'pages')
    assert not output.exists()
