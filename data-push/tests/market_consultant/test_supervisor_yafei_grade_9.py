from copy import deepcopy
import unittest

from lark_delivery.core import catalog
from lark_delivery.domains.market_consultant import adapter
from lark_delivery.domains.market_consultant.channels import supervisor_yafei_grade_9 as policy


KEY = "market_consultant/supervisor_yafei_grade_9"


class SupervisorYafeiGrade9Tests(unittest.TestCase):
    def setUp(self):
        self.definition = catalog.load_channel(KEY)
        self.target = catalog.select_targets(self.definition)[0]

    def test_registered_scope_target_profile_and_schedule(self):
        expected = ("B站信息流-亚飞",)
        self.assertEqual(tuple(self.definition["channels"]), expected)
        self.assertEqual(tuple(self.definition["channels"]), policy.CHANNELS)
        self.assertEqual(tuple(self.definition["report"]["included_grades"]), ("初三",))
        self.assertEqual(tuple(self.definition["report"]["included_grades"]), policy.INCLUDED_GRADES)
        self.assertEqual(self.target["chat_id"], policy.CHAT_ID)
        self.assertEqual(self.definition["source"]["report_profile"], "supervisor-detail")
        self.assertIs(self.definition["source"]["channel_match"]["case_sensitive"], True)
        self.assertEqual(tuple(self.definition["source"]["channel_match"]["values"]), expected)
        self.assertEqual(self.definition["schedule"]["windows_task_name"], "Codex-Lark-Supervisor-Yafei-Grade9-Push")
        self.assertEqual(self.definition["schedule"]["stagger_order"], 6)
        self.assertEqual(self.definition["schedule"]["prepare_minute"], 25)

    def test_each_channel_keeps_supervisor_contract(self):
        for channel in policy.CHANNELS:
            args = adapter.report_arguments(self.definition, self.target, channel=channel, report_type="both")
            self.assertEqual(args.channel, channel)
            self.assertEqual(args.chat_id, policy.CHAT_ID)
            self.assertEqual(args.report_profile, "supervisor-detail")
            self.assertEqual(args.mention_target, "supervisor")
            self.assertEqual(args.identity, "bot")
            self.assertEqual(args.verification_identity, "user")
            self.assertEqual(tuple(self.definition["report"]["included_grades"]), policy.INCLUDED_GRADES)

    def test_target_channel_and_grade_drift_are_blocked(self):
        for mutate in (
            lambda cfg: cfg["targets"][0].update(chat_id="oc_wrong"),
            lambda cfg: cfg["channels"].append("抖音私信"),
            lambda cfg: cfg["report"].update(included_grades=["初二"]),
        ):
            changed = deepcopy(self.definition)
            mutate(changed)
            with self.assertRaises(ValueError):
                adapter.validate_definition(changed)


if __name__ == "__main__":
    unittest.main()
