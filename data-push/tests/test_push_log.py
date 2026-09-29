"""The shared external run log: layout, stdout capture, verdicts and degradation.

Both departments write here. The rules that matter: a run always leaves a
readable trace, the task's own exit code is never altered, and an unusable log
root can never block a push.
"""

from datetime import datetime
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from lark_delivery.common import push_log

STARTED = datetime(2026, 9, 29, 12, 20, 5, tzinfo=push_log.TZ)


class RunScopeTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        machine = self.root / "machine.local.json"
        machine.write_text(json.dumps({"schema_version": 1, "paths": {"push_log_root": str(self.root / "logs")}}),
                           encoding="utf-8")
        patcher = patch.object(push_log, "MACHINE_LOCAL", machine)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_scope_writes_events_process_log_and_result(self):
        with push_log.run_scope("qingcheng", "sec_process_batch",
                                "Codex-Lark-Qingcheng-SEC-Process-GroupPush", STARTED) as scope:
            scope.event("run_started", confirmed=True)
            print("hello from the runner")
            scope.outcome("sec_no_friend_supervisor", "sent_verified")
            scope.exit_code = 0
            scope.event("run_finished")
        log = scope.log
        self.assertIsNotNone(log)
        self.assertEqual(log.department, "qingcheng")
        self.assertTrue(log.stream_path.is_relative_to(self.root / "logs" / "qingcheng" / "sec_process_batch"))
        events = [json.loads(line)["event"] for line in log.stream_path.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(events, ["run_started", "outcome", "run_finished"])
        self.assertIn("hello from the runner", log.process_path.read_text(encoding="utf-8"))
        summary = json.loads(log.result_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["exit_code"], 0)
        self.assertEqual(summary["needs_attention"], [])
        self.assertEqual(summary["outcomes"]["sec_no_friend_supervisor"]["status"], "sent_verified")

    def test_system_exit_still_propagates_and_is_recorded(self):
        with self.assertRaises(SystemExit) as raised:
            with push_log.run_scope("qingcheng", "process_batch", "Codex-Lark-QT", STARTED) as scope:
                scope.outcome("public_pool/supervisor", "blocked_source", "upstream audit failed")
                scope.exit_code = 1
                raise SystemExit(1)
        self.assertEqual(raised.exception.code, 1)
        summary = json.loads(scope.log.result_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["exit_code"], 1)
        self.assertEqual(summary["needs_attention"], ["public_pool/supervisor"])

    def test_stdout_passes_through_and_logging_failure_never_raises(self):
        with patch.object(push_log, "MACHINE_LOCAL", self.root / "absent.json"):
            with push_log.run_scope("qingcheng", "process_batch", "Codex-Lark-QT", STARTED) as scope:
                self.assertIsNone(scope.log)
                print("still printed")
                scope.outcome("x", "blocked")
                scope.exit_code = 0
        self.assertEqual(scope.outcomes["x"]["status"], "blocked")

    def test_result_index_accumulates_one_line_per_run(self):
        for minute in (20, 22):
            with push_log.run_scope("qingcheng", "process_batch", "Codex-Lark-QT",
                                    STARTED.replace(minute=minute)) as scope:
                scope.exit_code = 0
        index = (self.root / "logs" / "_index" / "runs.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(index), 2)
        self.assertEqual([json.loads(line)["task_name"] for line in index], ["Codex-Lark-QT"] * 2)


class IterOutcomesTests(unittest.TestCase):
    def test_process_shape_reports_one_verdict_per_channel_and_level(self):
        result = {"channels": {"public_pool": {"groups": {"supervisor": {"status": "sent_verified"},
                                                         "consultant": {"status": "blocked", "error": "image missing"}}}}}
        self.assertEqual(push_log.iter_outcomes(result),
                         [("public_pool/supervisor", "sent_verified", ""),
                          ("public_pool/consultant", "blocked", "image missing")])

    def test_special_shape_reports_one_flat_verdict_per_channel(self):
        result = {"channels": {"special_private": {"status": "skipped_no_eligible_rows"},
                               "special_public": {"status": "readback_failed", "receipt": "r.json"}}}
        self.assertEqual(push_log.iter_outcomes(result),
                         [("special_private", "skipped_no_eligible_rows", ""),
                          ("special_public", "readback_failed", "r.json")])

    def test_sec_shape_reports_one_verdict_per_report(self):
        result = {"reports": {"sec_public_supervisor": {"status": "blocked_or_uncertain", "error": "timeout"}}}
        self.assertEqual(push_log.iter_outcomes(result),
                         [("sec_public_supervisor", "blocked_or_uncertain", "timeout")])

    def test_unknown_and_empty_results_are_safe(self):
        self.assertEqual(push_log.iter_outcomes(None), [])
        self.assertEqual(push_log.iter_outcomes({}), [])

    def test_clean_statuses_are_not_flagged(self):
        for status in sorted(push_log.CLEAN_STATUSES):
            self.assertNotIn(status, {"blocked", "blocked_source", "readback_failed", "uncertain"})


if __name__ == "__main__":
    unittest.main()
