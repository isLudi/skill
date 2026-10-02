"""Retrying a precondition read, and — more importantly — never retrying a verdict.

On 2026-09-29 the SEC 16:20 slot lost three rounds to a transport reset on the pre-send
Base revision probe. The probe is a read used to decide whether a send is still safe:
when it cannot complete, nothing was learned, yet the round was discarded. The fix
retries only that case. The property that must hold is the converse: a probe that
*returns* a different revision is a verdict, and a verdict is never retried.
"""

import subprocess
import unittest
from unittest.mock import Mock, patch

from lark_delivery.common import retry, runtime
from lark_delivery.domains.market_consultant import reporting


class ClassificationTests(unittest.TestCase):
    def test_typed_transport_and_timeout_are_retryable(self):
        self.assertTrue(retry.is_transport(runtime.LarkTransportError("reset")))
        self.assertTrue(retry.is_transport(subprocess.TimeoutExpired("lark", 60)))

    def test_rewording_by_an_intermediate_layer_is_still_retryable(self):
        self.assertTrue(retry.is_transport(RuntimeError(
            'lark-cli 失败: im +chat-messages-list\n{"error": {"subtype": "transport"}}')))
        self.assertTrue(retry.is_transport(RuntimeError(
            "read tcp 10.0.0.1:1->2.2.2.2:443: wsarecv: An existing connection was "
            "forcibly closed by the remote host.")))

    def test_a_rejection_is_not_transport(self):
        for exc in (ValueError("Base changed after snapshot; rebuild before sending"),
                    RuntimeError('lark-cli 失败: im +messages-send\n{"error": {"code": 99991663}}'),
                    KeyError("rev")):
            with self.subTest(exc=type(exc).__name__):
                self.assertFalse(retry.is_transport(exc))


class RunLarkTypingTests(unittest.TestCase):
    def _run(self, returncode, stderr):
        completed = subprocess.CompletedProcess(["lark-cli"], returncode, stdout="", stderr=stderr)
        with patch.object(runtime, "resolve_lark_cli", return_value="lark-cli"), \
             patch.object(runtime.subprocess, "run", return_value=completed):
            return runtime.run_lark(["im", "+chat-messages-list"])

    def test_transport_failure_raises_the_typed_error(self):
        with self.assertRaises(runtime.LarkTransportError):
            self._run(1, '{"ok": false, "error": {"type": "network", "subtype": "transport"}}')

    def test_other_failure_stays_a_plain_runtime_error(self):
        # Must NOT be retryable: the call was rejected, so repeating it changes nothing.
        with self.assertRaises(RuntimeError) as raised:
            self._run(2, '{"ok": false, "error": {"code": 99991663, "msg": "no permission"}}')
        self.assertNotIsInstance(raised.exception, runtime.LarkTransportError)


class RetryTests(unittest.TestCase):
    def test_a_transport_failure_is_retried_until_it_succeeds(self):
        calls = []
        def flaky():
            calls.append(1)
            if len(calls) < 3:
                raise runtime.LarkTransportError("reset")
            return "rev-7"
        self.assertEqual(retry.retry_transport(flaky, sleep=lambda _: None), "rev-7")
        self.assertEqual(len(calls), 3)

    def test_exhausting_the_budget_still_fails_the_round(self):
        def always():
            raise runtime.LarkTransportError("reset")
        with self.assertRaises(runtime.LarkTransportError):
            retry.retry_transport(always, attempts=3, sleep=lambda _: None)

    def test_a_verdict_is_never_retried_and_never_delayed(self):
        # The safety property: a drift must fail closed on the first attempt.
        calls, slept = [], []
        def drift():
            calls.append(1)
            raise ValueError("Base changed after snapshot; rebuild before sending")
        with self.assertRaises(ValueError):
            retry.retry_transport(drift, attempts=3, sleep=slept.append)
        self.assertEqual(len(calls), 1)
        self.assertEqual(slept, [])

    def test_backoff_is_bounded_and_reported(self):
        seen = []
        def flaky():
            raise runtime.LarkTransportError("reset")
        with self.assertRaises(runtime.LarkTransportError):
            retry.retry_transport(flaky, attempts=3, delay=2.0, sleep=lambda s: seen.append(s),
                                  on_retry=lambda attempt, exc: seen.append(attempt))
        self.assertEqual(seen, [1, 2.0, 2, 2.0])


class PreSendProbeTests(unittest.TestCase):
    """The wrapper around the market's pre-send revision guard."""

    def test_a_transport_failure_at_the_probe_is_retried(self):
        calls = []
        def probe(*_args):
            calls.append(1)
            if len(calls) < 2:
                raise runtime.LarkTransportError("reset")
        with patch.object(reporting, "_assert_current_revision", probe), \
             patch.object(retry.time, "sleep", lambda _: None):
            reporting.assert_current_revision({}, {})
        self.assertEqual(len(calls), 2)

    def test_a_revision_drift_is_not_retried(self):
        calls = []
        def drift(*_args):
            calls.append(1)
            raise ValueError("Base changed after snapshot; rebuild before sending")
        with patch.object(reporting, "_assert_current_revision", drift):
            with self.assertRaises(ValueError):
                reporting.assert_current_revision({}, {})
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
