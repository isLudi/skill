from argparse import Namespace
from contextlib import contextmanager
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from usql_web_query.commands import apply_data_center_sql_replacement as command
from usql_web_query.data_center_write import _dismiss_preview_error
from _shared.errors import UsageError


@pytest.mark.parametrize("failure", [False, True])
def test_resources_close_before_dispatcher_stops(monkeypatch, failure):
    events = []

    class Resource:
        def __init__(self, name):
            self.name = name

        def close(self):
            assert "dispatcher_stopped" not in events
            events.append(self.name + "_closed")

    browser, context = Resource("browser"), Resource("context")
    monkeypatch.setattr(command, "launch_context", lambda *args: (browser, context))
    args = Namespace(state_path=None, headed=False, browser_channel=None, executable_path=None)

    @contextmanager
    def dispatcher():
        try:
            yield object()
        finally:
            events.append("dispatcher_stopped")

    def execute():
        with dispatcher() as pw, command._browser_session(pw, args):
            if failure:
                raise ValueError("original preview failure")

    if failure:
        with pytest.raises(ValueError, match="original preview failure"):
            execute()
    else:
        execute()
    assert events == ["context_closed", "browser_closed", "dispatcher_stopped"]


def test_browser_closes_when_context_cleanup_fails(monkeypatch):
    events = []

    class Context:
        def close(self):
            events.append("context_close_attempted")
            raise RuntimeError("context already disconnected")

    class Browser:
        def close(self):
            events.append("browser_closed")

    monkeypatch.setattr(command, "launch_context", lambda *args: (Browser(), Context()))
    args = Namespace(state_path=None, headed=False, browser_channel=None, executable_path=None)
    with pytest.raises(ValueError, match="original failure"):
        with command._browser_session(object(), args):
            raise ValueError("original failure")
    assert events == ["context_close_attempted", "browser_closed"]


def test_error_acknowledgement_requires_one_exact_button():
    class Modal:
        def __init__(self, count):
            self.button_count = count
            self.clicked = False

        def inner_text(self):
            return "SQL parse failed"

        def get_by_role(self, role, name):
            assert role == "button"
            assert name.fullmatch("确定")
            assert name.fullmatch("知道了")
            assert name.fullmatch("OK")
            assert not name.fullmatch("确认保存")
            assert not name.fullmatch("确认")
            assert not name.fullmatch("立即执行")
            return self

        def count(self):
            return self.button_count

        def click(self):
            self.clicked = True

    one = Modal(1)
    progress = {}
    _dismiss_preview_error(one, progress)
    assert one.clicked and progress["pre_preview_error_acknowledgement"] == "SQL parse failed"
    for count in (0, 2):
        ambiguous = Modal(count)
        with pytest.raises(UsageError, match="ambiguous"):
            _dismiss_preview_error(ambiguous, {})
        assert not ambiguous.clicked
