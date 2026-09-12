from copy import deepcopy
import unittest

from lark_delivery.core import catalog
from lark_delivery.domains.market_consultant import adapter
from lark_delivery.domains.market_consultant.channels import business_koc_math as policy


KEY = "market_consultant/business_koc_math"


class BusinessKocMathTests(unittest.TestCase):
    def setUp(self):
        self.definition = catalog.load_channel(KEY)
        self.target = catalog.select_targets(self.definition)[0]

    def test_registered_scope_order_target_and_enabled_schedule(self):
        self.assertEqual(tuple(self.definition["channels"]), policy.CHANNELS)
        self.assertEqual(self.target["chat_id"], policy.CHAT_ID)
        self.assertTrue(self.definition["schedule"]["enabled"])
        self.assertEqual(self.definition["schedule"]["first_send_at"], "2026-09-10T21:20:00+08:00")
        self.assertEqual(catalog.schedule_config(self.definition, self.target)["channels"], list(policy.CHANNELS))
        self.assertEqual(self.definition["volume_report"]["stage"], "scheduled")
        self.assertEqual(self.definition["volume_report"]["channel_rule"],
                         "contains_koc_case_insensitive_and_not_contains_自孵化")
        self.assertEqual(self.definition["schedule"]["hours"], [13, 17])
        self.assertEqual(self.definition["schedule"]["slot_reports"], {"13": "regular", "17": "volume"})

    def test_each_channel_gets_its_own_report_arguments(self):
        args = [adapter.report_arguments(self.definition, self.target, channel=channel, report_type="both")
                for channel in policy.CHANNELS]
        self.assertEqual([item.channel for item in args], list(policy.CHANNELS))
        self.assertTrue(all(item.chat_id == policy.CHAT_ID for item in args))
        with self.assertRaisesRegex(ValueError, "outside"):
            adapter.report_arguments(self.definition, self.target, channel="KOC-其他数学")

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
