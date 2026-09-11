from copy import deepcopy
import unittest

from lark_delivery.core import catalog
from lark_delivery.domains.market_consultant import adapter
from lark_delivery.domains.market_consultant.channels import supervisor_private_app_sync as policy


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
        self.assertEqual(self.definition["state_dir"], "C:/Users/Ludim/.codex/runtime/channel-broadcast-push/supervisor-private-app-sync")

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


if __name__ == "__main__":
    unittest.main()
