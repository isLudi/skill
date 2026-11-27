from __future__ import annotations

from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from _shared import push_request_pacing as pacing
from _shared.errors import UsageError
from tiangong2_task import session


def test_guarded_requests_are_spaced_and_do_not_follow_redirects(monkeypatch):
    monkeypatch.setenv("CODEX_PUSH_GUARDED_PLATFORM", "1")
    clock = [100.0]
    waits = []
    monkeypatch.setattr(pacing, "_last_start", None)
    monkeypatch.setattr(pacing.time, "monotonic", lambda: clock[0])

    def sleep(seconds):
        waits.append(seconds)
        clock[0] += seconds

    monkeypatch.setattr(pacing.time, "sleep", sleep)
    pacing.before_request()
    pacing.before_request()
    assert waits == pytest.approx([1.2, 1.2])
    assert pacing.request_options() == {"max_redirects": 0, "max_retries": 0}


def test_guarded_session_uses_only_validated_existing_identity(monkeypatch, tmp_path):
    monkeypatch.setenv("CODEX_PUSH_GUARDED_PLATFORM", "1")
    monkeypatch.setattr(session, "_read_identity", lambda context: {"name": "owner"})
    context = SimpleNamespace(new_page=lambda: pytest.fail("push must not navigate a page"))
    identity, logged_in = session._authenticate_context(
        context, state_path=tmp_path / "state.json", credentials=session.ScopedCredentials("owner", "secret"))
    assert identity["name"] == "owner" and logged_in is False
    monkeypatch.setattr(session, "_read_identity", lambda context: {"name": "different"})
    with pytest.raises(UsageError, match="expired or has the wrong identity"):
        session._authenticate_context(context, state_path=tmp_path / "state.json",
                                      credentials=session.ScopedCredentials("owner", "secret"))


def test_rate_limit_sets_shared_cooldown_before_worker_exits(monkeypatch, tmp_path):
    monkeypatch.setenv("CODEX_PUSH_GUARDED_PLATFORM", "1")
    monkeypatch.setenv("CODEX_PUSH_COORDINATOR_ROOT", str(tmp_path))
    from tiangong2_task.client import Tiangong2ReadOnlyClient
    with pytest.raises(UsageError, match="HTTP 429"):
        Tiangong2ReadOnlyClient._json_body(SimpleNamespace(ok=False, status=429), "test")
    import json
    state = json.loads((tmp_path / "cooldown.json").read_text(encoding="utf-8"))
    assert state["until"] - state["created_at"] == 120
