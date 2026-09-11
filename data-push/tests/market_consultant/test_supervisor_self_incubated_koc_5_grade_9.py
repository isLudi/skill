from copy import deepcopy
import unittest

from lark_delivery.core import catalog
from lark_delivery.domains.market_consultant import adapter, supervisor_report
from lark_delivery.domains.market_consultant.channels import supervisor_self_incubated_koc_5_grade_9 as policy


KEY = "market_consultant/supervisor_self_incubated_koc_5_grade_9"


class SupervisorSelfIncubatedKocGrade9Tests(unittest.TestCase):
    def setUp(self):
        self.definition = catalog.load_channel(KEY)
        self.target = catalog.select_targets(self.definition)[0]

    def test_registered_scope_target_profile_and_schedule(self):
        self.assertEqual(tuple(self.definition["channels"]), ("KOC-孟亚飞数学", "自孵化KOC-5元纯课"))
        self.assertEqual(tuple(self.definition["report"]["included_grades"]), ("初三",))
        self.assertEqual(tuple(self.definition["channels"]), policy.CHANNELS)
        self.assertEqual(tuple(self.definition["report"]["included_grades"]), policy.INCLUDED_GRADES)
        self.assertEqual(self.target["chat_id"], policy.CHAT_ID)
        self.assertEqual(self.definition["source"]["report_profile"], "supervisor-detail")
        self.assertIs(self.definition["source"]["channel_match"]["case_sensitive"], True)
        self.assertEqual(self.definition["source"]["channel_match"]["values"],
                         {"KOC-孟亚飞数学": "KOC-孟亚飞数学",
                          "自孵化KOC-5元纯课": "自孵化KOC-5元纯课"})
        self.assertEqual(self.definition["schedule"]["windows_task_name"], "Codex-Lark-Supervisor-KOC-Grade9-Push")
        self.assertEqual(self.definition["schedule"]["stagger_order"], 5)
        self.assertEqual(self.definition["schedule"]["prepare_minute"], 24)

    def test_report_arguments_keep_supervisor_contract(self):
        for channel in policy.CHANNELS:
            args = adapter.report_arguments(self.definition, self.target, channel=channel, report_type="both")
            self.assertEqual(args.channel, channel)
            self.assertEqual(args.chat_id, policy.CHAT_ID)
            self.assertEqual(args.report_profile, "supervisor-detail")
            self.assertEqual(args.mention_target, "supervisor")
            self.assertEqual(args.identity, "bot")
            self.assertEqual(args.verification_identity, "user")

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

    def test_supervisor_report_can_be_pinned_to_grade_9(self):
        records = [
            {"fields": {"主管": "甲", "经理": "甲一", "年级": "初三", "退前线索": 1, "退后线索": 1, "5min标记": 1}},
            {"fields": {"主管": "乙", "经理": "乙一", "年级": "高一", "退前线索": 1, "退后线索": 1, "5min标记": 0}},
        ]
        report = supervisor_report.build_report(records, ("退前线索", "退后线索", "5min标记"),
                                                "0911期", "process", min_post_leads=1,
                                                included_grades=("初三",))
        self.assertEqual([block["grade"] for block in report["blocks"]], ["初三"])
        self.assertEqual(report["included_grades"], ["初三"])
        self.assertEqual(report["excluded_grade_counts"], {"高一": 1})


if __name__ == "__main__":
    unittest.main()
