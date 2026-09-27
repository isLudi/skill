from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from lark_delivery.core import catalog
from lark_delivery.domains.market_consultant import adapter
from lark_delivery.domains.market_consultant import scheduler
from lark_delivery.domains.market_consultant.channels import supervisor_private_app_sync as policy
from lark_delivery.paths import WORKSPACE_ROOT


KEY = "market_consultant/supervisor_private_app_sync"


class SupervisorPrivateAppSyncTests(unittest.TestCase):
    def setUp(self):
        self.definition = catalog.load_channel(KEY)
        self.target = catalog.select_targets(self.definition)[0]

    def test_registered_scope_target_profile_and_schedule(self):
        self.assertEqual(tuple(self.definition["channels"]), ("集团私域", "app"))
        self.assertEqual(tuple(self.definition["channels"]), policy.CHANNELS)
        self.assertEqual(self.target["chat_id"], policy.CHAT_ID)
        self.assertEqual(self.definition["source"]["report_profile"], "supervisor-detail")
        self.assertTrue(self.definition["schedule"]["enabled"])
        expected_state_dir = (WORKSPACE_ROOT / "runtime" / "channel-broadcast-push" / "supervisor-private-app-sync").as_posix()
        self.assertEqual(self.definition["state_dir"], expected_state_dir)

    def test_each_channel_uses_supervisor_report_arguments(self):
        args = [adapter.report_arguments(self.definition, self.target, channel=channel, report_type="both")
                for channel in policy.CHANNELS]
        self.assertEqual([item.channel for item in args], list(policy.CHANNELS))
        self.assertTrue(all(item.chat_id == policy.CHAT_ID for item in args))
        self.assertTrue(all(item.report_profile == "supervisor-detail" for item in args))
        self.assertTrue(all(item.mention_target == "supervisor" for item in args))

    def test_target_and_channel_drift_are_blocked(self):
        changed = deepcopy(self.definition)
        changed["targets"][0]["chat_id"] = "oc_wrong"
        with self.assertRaisesRegex(ValueError, "target"):
            adapter.validate_definition(changed)
        changed = deepcopy(self.definition)
        changed["channels"].reverse()
        with self.assertRaisesRegex(ValueError, "channels"):
            adapter.validate_definition(changed)

    def test_only_app_may_use_casefold_matching(self):
        changed = deepcopy(self.definition)
        changed["source"]["channel_match"]["casefold_channels"] = ["集团私域"]
        with self.assertRaisesRegex(ValueError, "只允许"):
            adapter.validate_definition(changed)

    def test_scheduled_group_delivers_app_when_private_channel_is_absent(self):
        cfg = catalog.schedule_config(self.definition, self.target)
        slot = datetime(2026, 9, 21, 21, tzinfo=scheduler.TZ)
        evidence = {"periods": {"20260925期": {"channel_counts": {"APP": 507}}}}
        context = {"channel": "app", "period": "20260925期", "raw_read_audit": {"rev": 123}}
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(scheduler, "now", return_value=slot + timedelta(minutes=23)), \
             patch.object(scheduler, "verify_bot"), \
             patch.object(scheduler, "upstream_ready", return_value=evidence), \
             patch.object(scheduler, "prepare_report", return_value=context) as prepare, \
             patch.object(scheduler, "validate_context"), \
             patch.object(scheduler, "assert_current_revision"), \
             patch.object(scheduler, "deliver", return_value=True) as deliver:
            db = scheduler.connect_ledger(Path(directory))
            try:
                self.assertEqual(scheduler.run_slot(cfg, False, slot, Path(directory), db), 0)
            finally:
                db.close()
        self.assertEqual(prepare.call_count, 1)
        self.assertEqual(prepare.call_args.args[0].channel, "app")
        self.assertEqual(deliver.call_count, 1)


if __name__ == "__main__":
    unittest.main()
