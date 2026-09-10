from contextlib import redirect_stdout
from copy import deepcopy
from datetime import datetime, timedelta
import io
from pathlib import Path
import tempfile
from unittest.mock import patch
import unittest

from lark_delivery import cli
from lark_delivery.core import catalog
from lark_delivery.domains.market_consultant import immediate as one
from lark_delivery.domains.market_consultant import scheduler as schedule


class ImmediateTests(unittest.TestCase):
    def setUp(self):
        self.started = datetime(2026, 9, 10, 18, 40, tzinfo=schedule.TZ)
        self.slot = self.started.replace(hour=17, minute=0)
        self.evidence = {"dt": "20260910", "hour": 14}
        self.context = {"period": "20260911期", "report_type": "process"}

    def test_latest_upstream_cycle_includes_night_runs(self):
        self.assertEqual(one.latest_upstream_slot(self.started), self.slot)
        self.assertEqual(one.latest_upstream_slot(self.started.replace(hour=0)).hour, 21)
        self.assertEqual(one.latest_upstream_slot(self.started.replace(hour=6)).hour, 5)

    def test_immediate_has_independent_time_guard_not_fake_clock(self):
        one.require_fresh_request(self.started, self.slot, self.evidence, self.context, self.started)
        with patch.object(schedule, "now", return_value=self.started), self.assertRaises(ValueError):
            schedule.require_send_window(self.slot)

    def test_expired_request_new_cycle_stale_snapshot_rejected(self):
        for now, evidence in ((self.started + timedelta(minutes=11), self.evidence),
                              (self.started, {"dt": "20260910", "hour": 9})):
            with self.assertRaises(ValueError):
                one.require_fresh_request(self.started, self.slot, evidence, self.context, now)
        start = self.started.replace(hour=20, minute=59)
        with self.assertRaises(ValueError):
            one.require_fresh_request(start, self.slot, self.evidence, self.context, start + timedelta(minutes=2))

    def test_thursday_still_cannot_send_conversion(self):
        with self.assertRaises(ValueError):
            one.require_fresh_request(self.started, self.slot, self.evidence,
                                      {"period": "20260911期", "report_type": "both"}, self.started)

    def test_one_time_key_is_stable_target_bound_and_separate_from_schedule(self):
        definition = catalog.load_channel(catalog.DEFAULT_CHANNEL)
        cfg = catalog.schedule_config(definition, catalog.select_targets(definition)[0])
        key = one.request_key(cfg, "explicit-request-01")
        self.assertEqual(key, one.request_key(cfg, "explicit-request-01"))
        self.assertNotEqual(key, one.request_key({**cfg, "chat_id": "oc_other"}, "explicit-request-01"))
        self.assertNotEqual(key, schedule.delivery_key(cfg, self.slot, definition["channel"]))
        with self.assertRaises(ValueError):
            one.request_key(cfg, "")

    def test_confirm_and_request_id_are_required_before_any_outlet(self):
        for args in (("send-now", "--request-id", "explicit-request-01"), ("send-now", "--confirm-send")):
            with self.assertRaises(SystemExit), redirect_stdout(io.StringIO()):
                cli.main(args, bound_channel=catalog.DEFAULT_CHANNEL)

    def test_known_receipt_is_never_replayed_even_when_paused(self):
        definition = catalog.load_channel(catalog.DEFAULT_CHANNEL)
        definition["schedule"]["enabled"] = False
        with tempfile.TemporaryDirectory() as directory:
            definition["state_dir"] = directory
            target = catalog.select_targets(definition)[0]
            cfg = catalog.schedule_config(definition, target)
            key = one.request_key(cfg, "explicit-request-01")
            db = schedule.connect_ledger(Path(directory))
            schedule.claim(db, key, self.slot, definition["channel"])
            db.execute("UPDATE deliveries SET status='sent_verified',message_id='om_test' WHERE key=?", (key,))
            db.commit()
            db.close()
            with patch.object(schedule, "verify_bot") as verify, redirect_stdout(io.StringIO()):
                self.assertEqual(one.run(definition, target, "explicit-request-01"), 0)
                verify.assert_not_called()
