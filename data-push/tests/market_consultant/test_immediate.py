from contextlib import redirect_stdout
from copy import deepcopy
from datetime import datetime, timedelta
import io
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
import unittest

from lark_delivery import cli
from lark_delivery.core import catalog
from lark_delivery.domains.market_consultant import adapter
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

    def test_expired_backfill_requires_closed_window_and_is_bounded(self):
        started = self.slot + timedelta(minutes=35)
        with self.assertRaisesRegex(ValueError, "after the scheduled deadline"):
            one.require_fresh_request(started, self.slot, self.evidence, self.context,
                                      self.slot + timedelta(minutes=40), allow_expired=True)
        one.require_fresh_request(self.slot + timedelta(minutes=55), self.slot, self.evidence, self.context,
                                  self.slot + timedelta(hours=1), allow_expired=True)
        started = self.slot + timedelta(hours=4, minutes=55)
        with self.assertRaisesRegex(ValueError, "window elapsed"):
            one.require_fresh_request(started, self.slot, self.evidence, self.context,
                                      self.slot + timedelta(hours=5), allow_expired=True)

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
        for args in (("send-now", "--request-id", "explicit-request-01"), ("send-now", "--confirm-send"),
                     ("send-volume-now", "--request-id", "explicit-request-01"),
                     ("send-volume-now", "--confirm-send")):
            with self.assertRaises(SystemExit), redirect_stdout(io.StringIO()):
                cli.main(args, bound_channel=catalog.DEFAULT_CHANNEL)

    def test_volume_freshness_requires_exact_latest_write_and_skips_weekday_report_type(self):
        started = datetime(2026, 9, 25, 21, 20, tzinfo=schedule.TZ)
        slot = started.replace(minute=0)
        evidence = {"dt": "20260925", "hour": 19,
                    "volume": {"dt": "20260925", "hour": 19,
                               "periods": ["20260925期", "20261002期"], "total": 49}}
        context = {"period": "20261002期", "raw_count": 49}
        one.require_fresh_request(started, slot, evidence, context, started, volume=True)
        with self.assertRaisesRegex(ValueError, "Volume Base snapshot differs"):
            one.require_fresh_request(started, slot, evidence, {**context, "raw_count": 48}, started,
                                      volume=True)
        self.assertNotEqual(one.request_key({"channel_key": "market/a", "chat_id": "oc_x",
                                             "bot_open_id": "ou_x"}, "explicit-request-01", "volume"),
                            one.request_key({"channel_key": "market/a", "chat_id": "oc_x",
                                             "bot_open_id": "ou_x"}, "explicit-request-01"))

    def test_volume_preflight_uses_volume_context_and_does_not_send(self):
        definition = catalog.load_channel(catalog.DEFAULT_CHANNEL)
        target = catalog.select_targets(definition)[0]
        started = datetime(2026, 9, 25, 21, 20, tzinfo=schedule.TZ)
        evidence = {"dt": "20260925", "hour": 19, "execution_id": 1,
                    "volume": {"dt": "20260925", "hour": 19, "execution_id": 2,
                               "periods": ["20260925期", "20261002期"], "total": 49}}
        context = {"report_kind": "volume", "channel": "KOC渠道进量", "period": "20261002期",
                   "raw_count": 49, "raw_read_audit": {"rev": 5}, "mention_info": {"resolved": {}},
                   "volume_image_path": Path("volume.png"), "markdown": "volume image", "rows": []}
        with tempfile.TemporaryDirectory() as directory:
            cfg = catalog.schedule_config(definition, target)
            cfg["state_dir"] = directory
            with (patch.object(catalog, "schedule_config", return_value=cfg),
                  patch.object(schedule, "validate_config"), patch.object(schedule, "now", return_value=started),
                  patch.object(schedule, "verify_bot"), patch.object(one, "verify_publication", return_value={}),
                  patch.object(schedule, "upstream_ready", return_value=evidence) as upstream,
                  patch.object(one.vr, "prepare_context", return_value=context),
                  patch.object(one.vr, "validate_scheduled_context"),
                  patch.object(schedule, "assert_current_revision"),
                  patch.object(schedule.gp, "send_markdown", return_value={"dry_run": True}) as send,
                  patch.object(adapter, "prepare", side_effect=AssertionError("regular report used"))):
                self.assertEqual(one.run(definition, target, "volume-request-01", preflight=True,
                                         volume=True), 0)
            self.assertEqual(upstream.call_args.args[0]["slot_reports"]["21"], "volume")
            self.assertTrue(send.call_args.kwargs["dry_run"])
            saved = json.loads((Path(directory) / "immediate/volume-request-01/preflight.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["channels"][0]["report_kind"], "volume")
            self.assertEqual(saved["channels"][0]["raw_count"], 49)

    def test_volume_request_uses_separate_receipt_key(self):
        definition = catalog.load_channel(catalog.DEFAULT_CHANNEL)
        target = catalog.select_targets(definition)[0]
        with tempfile.TemporaryDirectory() as directory:
            cfg = catalog.schedule_config(definition, target)
            cfg["state_dir"] = directory
            key = one.request_key(cfg, "volume-request-02", "volume")
            db = schedule.connect_ledger(Path(directory))
            schedule.claim(db, key, self.slot, "KOC渠道进量")
            db.execute("UPDATE deliveries SET status='sent_verified',message_id='om_volume' WHERE key=?", (key,))
            db.commit()
            db.close()
            with (patch.object(catalog, "schedule_config", return_value=cfg),
                  patch.object(schedule, "validate_config"),
                  patch.object(schedule, "verify_bot") as verify,
                  redirect_stdout(io.StringIO())):
                self.assertEqual(one.run(definition, target, "volume-request-02", volume=True), 0)
            verify.assert_not_called()

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
