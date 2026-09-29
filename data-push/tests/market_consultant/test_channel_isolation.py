"""Per-channel isolation and external run logging; offline, no live calls.

These lock in the 2026-09-28 fix: a single channel's failure must never deny
the other channels of the same group their message, and a silent skip must
leave a durable trace instead of vanishing.
"""
from contextlib import ExitStack
from datetime import datetime, timedelta
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from lark_delivery.common import push_log
from lark_delivery.core import catalog
from lark_delivery.domains.market_consultant import scheduler

KEY = "market_consultant/business_koc_math"
PERIOD = "20260925期"
SLOT = datetime(2026, 9, 21, 13, tzinfo=scheduler.TZ)


def evidence():
    return {"periods": {PERIOD: {"channel_counts": {"KOC-周帅数学": 2, "KOC-孟亚飞数学": 3}}}}


def context(channel, rev=123, **extra):
    return {"channel": channel, "period": PERIOD, "raw_read_audit": {"has_more": False, "rev": rev}, **extra}


class ChannelIsolationTests(unittest.TestCase):
    def setUp(self):
        self.definition = catalog.load_channel(KEY)
        self.target = catalog.select_targets(self.definition)[0]
        self.cfg = catalog.schedule_config(self.definition, self.target)
        self.channels = list(self.cfg["channels"])
        self.assertGreater(len(self.channels), 1, "isolation needs a multi-channel group")

    def run_slot(self, directory, prepare, *, deliver=None):
        # The frozen test clock cannot advance through a retry sleep, so pin the
        # retry schedule past the deadline: the loop then gives up deterministically
        # exactly as it does at :50 in production.
        with ExitStack() as stack:
            for patcher in (
                patch.object(scheduler, "now", return_value=SLOT + timedelta(minutes=20)),
                patch.object(scheduler, "verify_bot"),
                patch.object(scheduler, "upstream_ready", return_value=evidence()),
                patch.object(scheduler, "prepare_report", side_effect=prepare),
                patch.object(scheduler, "validate_context"),
                patch.object(scheduler, "assert_current_revision"),
                patch.object(scheduler, "next_check", return_value=SLOT + timedelta(minutes=51)),
            ):
                stack.enter_context(patcher)
            if deliver is not None:
                stack.enter_context(patch.object(scheduler, "deliver", side_effect=deliver))
            db = scheduler.connect_ledger(Path(directory))
            try:
                return scheduler.run_slot(self.cfg, False, SLOT, Path(directory), db)
            finally:
                db.close()

    def events(self, directory, channel):
        import sqlite3
        with sqlite3.connect(Path(directory) / "deliveries.sqlite3") as db:
            return [row[0] for row in db.execute(
                "SELECT status FROM channel_events WHERE channel=? ORDER BY rowid", (channel,))]

    def test_one_channel_failure_does_not_deny_the_other(self):
        blocked, healthy = self.channels[0], self.channels[1]
        delivered = []

        def prepare(args, definition):
            if args.channel == blocked:
                raise ValueError("期次+lead_id重复，停止汇总")
            return context(args.channel)

        def deliver(item, cfg, slot, db, evidence_arg):
            delivered.append(item["channel"])
            return True

        with tempfile.TemporaryDirectory() as directory:
            code = self.run_slot(directory, prepare, deliver=deliver)
            self.assertEqual(delivered, [healthy])
            self.assertEqual(code, 1, "the blocked channel must still surface as needing attention")
            self.assertIn("blocked_prepare", self.events(directory, blocked))
            # `deliver` is stubbed here, so the healthy channel has no verdict of
            # its own — what matters is that it was reached and never blocked.
            self.assertNotIn("blocked_prepare", self.events(directory, healthy))

    def test_prepare_runs_once_per_channel_per_attempt(self):
        calls = []

        def prepare(args, definition):
            calls.append(args.channel)
            return context(args.channel)

        with tempfile.TemporaryDirectory() as directory:
            code = self.run_slot(directory, prepare, deliver=lambda *a: True)
        self.assertEqual(code, 0)
        self.assertEqual(calls, self.channels)

    def test_revision_mismatch_isolates_only_the_deviant_channel(self):
        first, second = self.channels[0], self.channels[1]
        delivered = []

        def prepare(args, definition):
            return context(args.channel, rev=111 if args.channel == first else 222)

        def deliver(item, cfg, slot, db, evidence_arg):
            delivered.append(item["channel"])
            return True

        with tempfile.TemporaryDirectory() as directory:
            code = self.run_slot(directory, prepare, deliver=deliver)
            self.assertEqual(delivered, [first])
            self.assertEqual(code, 1)
            self.assertIn("blocked_revision", self.events(directory, second))
            self.assertNotIn("blocked_revision", self.events(directory, first))

    def test_skip_is_recorded_instead_of_vanishing(self):
        def prepare(args, definition):
            return context(args.channel, skip_delivery=True,
                           skip_reason="no_supervisor_rows_meet_minimum_post_leads")

        with tempfile.TemporaryDirectory() as directory:
            code = self.run_slot(directory, prepare)
            for channel in self.channels:
                self.assertEqual(self.events(directory, channel), ["skipped_no_eligible_rows"])
            self.assertEqual(code, 0, "a legitimate no-data skip is not a failure")

    def test_empty_round_is_reported_not_silently_successful(self):
        def prepare(args, definition):
            raise ValueError("always blocked")

        with tempfile.TemporaryDirectory() as directory:
            code = self.run_slot(directory, prepare)
        self.assertEqual(code, 1)


class RunLogTests(unittest.TestCase):
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

    def test_events_and_summary_land_under_the_configured_root(self):
        started = datetime(2026, 9, 28, 17, 20, 3, tzinfo=scheduler.TZ)
        run_log = push_log.open_run_log("supervisor_zhu_doctor_video49", "Codex-Lark-Test-Push", started)
        self.assertIsNotNone(run_log)
        token = scheduler._RUN_LOG.set(run_log)
        try:
            scheduler.emit("checking_upstream", attempt=1, slot=SLOT.isoformat())
            scheduler.record_channel(None, SLOT, "朱博士", "skipped_no_eligible_rows",
                                     "no_advisor_rows_meet_minimum_post_leads")
        finally:
            scheduler._RUN_LOG.reset(token)
        run_log.finish(0, started + timedelta(minutes=2))

        stream = list(run_log.stream_path.read_text(encoding="utf-8").splitlines())
        self.assertEqual([json.loads(line)["event"] for line in stream],
                         ["checking_upstream", "channel_outcome"])
        summary = json.loads(run_log.result_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["slot"], SLOT.isoformat())
        self.assertEqual(summary["exit_code"], 0)
        self.assertEqual(summary["needs_attention"], [])
        self.assertEqual(summary["channels"]["朱博士"]["status"], "skipped_no_eligible_rows")
        self.assertTrue(run_log.stream_path.is_relative_to(self.root))
        self.assertIn("channel_outcome", run_log.index_path.read_text(encoding="utf-8"))

    def test_missing_log_root_degrades_without_raising(self):
        with patch.object(push_log, "MACHINE_LOCAL", self.root / "absent.json"):
            self.assertIsNone(push_log.open_run_log("c", "t", datetime(2026, 9, 28, tzinfo=scheduler.TZ)))

    def test_emit_survives_a_failing_sink(self):
        class Broken:
            def event(self, payload):
                raise OSError("disk full")

        token = scheduler._RUN_LOG.set(Broken())
        try:
            scheduler.emit("checking_upstream", attempt=1)  # must not raise
        finally:
            scheduler._RUN_LOG.reset(token)


if __name__ == "__main__":
    unittest.main()
