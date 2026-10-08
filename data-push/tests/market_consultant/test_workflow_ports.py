from copy import deepcopy
from pathlib import Path
import tempfile
from unittest.mock import Mock, patch
import unittest

from lark_delivery.core import catalog
from lark_delivery.core.contracts import ReportPorts
from lark_delivery.domains.market_consultant.adapter import report_arguments
from lark_delivery.domains.market_consultant.workflow import (
    prepare_report, _channel_scope, _channel_filter, _channel_matches, source_present_channels,
)
from lark_delivery.domains.market_consultant.channels import self_incubated_koc_5 as policy
from lark_delivery.domains.market_consultant.channels import supervisor_private_app_sync as private_policy
from .test_supervisor_report import leads as supervisor_leads
from .test_grade_report import leads


class WorkflowPortTests(unittest.TestCase):
    def setUp(self):
        self.definition = catalog.load_channel(catalog.DEFAULT_CHANNEL)
        self.rows = leads()
        self.ports = Mock(spec=ReportPorts)
        self.ports.resolve_source.return_value = {"base_token": "fake_base", "table_id": self.definition["source"]["raw_table_id"], "view_id": "fake_view"}
        self.ports.field_names.return_value = set(self.rows[0])
        def read(coords, args, fields, *, filter_json, audit):
            audit.update(records_count=len(self.rows), pages=1, rev=123, has_more=False)
            return deepcopy(self.rows)
        self.ports.read_records.side_effect = read
        self.ports.search_users.return_value = {"queries": [{"query": "负责人A", "has_more": False}], "users": [
            {"matched_query": "负责人A", "localized_name": "负责人A", "open_id": "ou_manager",
             "is_activated": True, "is_cross_tenant": False}]}
        self.ports.verify_target.return_value = {"name": "Test group", "name_changed": True}
        self.ports.missing_members.return_value = []
        clock = patch.object(policy, "business_period", return_value="20260911期")
        clock.start()
        self.addCleanup(clock.stop)

    def test_real_pipeline_accepts_fake_ports_and_separate_target_artifacts(self):
        self.definition["targets"].append({"id": "second", "chat_id": "oc_second", "display_name": "Second", "enabled": True})
        with tempfile.TemporaryDirectory() as directory:
            contexts = []
            for target in catalog.select_targets(self.definition):
                args = report_arguments(self.definition, target, report_type="both", state_dir=directory)
                contexts.append(prepare_report(args, self.definition, ports=self.ports))
            self.assertNotEqual(contexts[0]["idempotency_key"], contexts[1]["idempotency_key"])
            self.assertNotEqual(contexts[0]["image_path"], contexts[1]["image_path"])
            self.assertTrue(all(Path(context["image_path"]).is_file() for context in contexts))
            self.assertEqual(contexts[0]["grade_report"], contexts[1]["grade_report"])
            self.assertEqual(contexts[0]["mention_info"]["resolved"], {"负责人A": "ou_manager"})
            self.assertEqual({call.args[0] for call in self.ports.missing_members.call_args_list}, {target["chat_id"] for target in self.definition["targets"]})

    def test_out_of_registry_target_stops_before_reading(self):
        args = report_arguments(self.definition, catalog.select_targets(self.definition)[0])
        args.chat_id = "oc_not_registered"
        with self.assertRaises(ValueError):
            prepare_report(args, self.definition, ports=self.ports)
        self.ports.resolve_source.assert_not_called()

    def test_member_failure_degrades_to_names_only_after_bot_invite(self):
        args = report_arguments(self.definition, catalog.select_targets(self.definition)[0])
        self.ports.missing_members.side_effect = [["负责人A"], ["负责人A"]]
        context = prepare_report(args, self.definition, ports=self.ports)
        # 2026-10-04 policy: the bot invites the absent member once; when they are
        # still absent, the push proceeds with a plain-name mention, never a block.
        self.ports.invite_members.assert_called_once()
        self.assertEqual(self.ports.missing_members.call_count, 2)
        self.assertEqual(context["mention_info"]["resolved"], {})
        self.assertEqual(context["mention_info"]["text_fallback_names"], ["负责人A"])

    def test_app_matches_exactly_without_case_sensitivity(self):
        definition = catalog.load_channel("market_consultant/supervisor_private_app_sync")
        scope = _channel_scope(definition, "app")
        self.assertEqual(scope, {"match_mode": "casefold_exact", "value": "app"})
        self.assertEqual(_channel_scope(definition, "集团私域"), "集团私域")
        self.assertIsNone(_channel_filter(scope))
        self.assertTrue(all(_channel_matches(name, scope) for name in ("app", "APP", "App", "aPp")))
        self.assertFalse(any(_channel_matches(name, scope) for name in ("APP推广", "途途APP", "集团私域")))

    def test_app_period_read_keeps_all_case_variants_and_excludes_other_channels(self):
        definition = catalog.load_channel("market_consultant/supervisor_private_app_sync")
        target = catalog.select_targets(definition)[0]
        rows = supervisor_leads("主管甲", "经理甲", 10, 5, 0)
        for index, row in enumerate(rows):
            row["渠道"] = ("app", "APP", "App", "aPp")[index % 4]
        unrelated = deepcopy(rows[0])
        unrelated["lead_id"] = "unrelated"
        unrelated["渠道"] = "APP推广"
        rows.append(unrelated)
        ports = Mock(spec=ReportPorts)
        ports.resolve_source.return_value = {"base_token": "fake", "table_id": definition["source"]["raw_table_id"], "view_id": "view"}
        ports.field_names.return_value = set(rows[0])
        def read(coords, args, fields, *, filter_json, audit):
            self.assertEqual(filter_json, {"logic": "and", "conditions": [["期次", "==", "20260911期"]]})
            audit.update(records_count=len(rows), pages=1, rev=123, has_more=False)
            return deepcopy(rows)
        ports.read_records.side_effect = read
        ports.verify_target.return_value = {"name": "Test group", "name_changed": False}
        with patch.object(private_policy, "business_period", return_value="20260911期"), tempfile.TemporaryDirectory() as directory:
            args = report_arguments(definition, target, channel="app", report_type="process",
                                    period="20260911期", state_dir=directory, no_mentions=True)
            args.with_image = False
            context = prepare_report(args, definition, ports=ports)
        self.assertEqual(context["raw_count"], 10)
        self.assertEqual(context["raw_read_audit"]["server_returned_count"], 11)
        self.assertEqual(context["raw_read_audit"]["matched_channel_values"], ["APP", "App", "aPp", "app"])

    def test_source_audit_preserves_pre_dedupe_count(self):
        original_count = len(self.rows)
        self.rows.append(deepcopy(self.rows[0]))
        target = catalog.select_targets(self.definition)[0]
        with tempfile.TemporaryDirectory() as directory:
            args = report_arguments(self.definition, target, report_type="process", state_dir=directory,
                                    no_mentions=True)
            args.with_image = False
            context = prepare_report(args, self.definition, ports=self.ports)
        self.assertEqual(context["raw_count"], original_count)
        self.assertEqual(context["raw_read_audit"]["matched_count"], original_count + 1)
        self.assertEqual(context["raw_read_audit"]["deduped_count"], original_count)
        self.assertEqual(len(context["raw_read_audit"]["duplicate_lead_id_merged"]), 1)

    def test_every_registered_multi_channel_group_skips_only_audited_zero_rows(self):
        keys = ("business_koc_math", "supervisor_koc_douyin_sync",
                "supervisor_private_app_sync", "supervisor_self_incubated_koc_5_grade_9")
        period = "20260925期"
        for key in keys:
            with self.subTest(key=key):
                definition = catalog.load_channel("market_consultant/" + key)
                cfg = catalog.schedule_config(definition, catalog.select_targets(definition)[0])
                counts = {name: 3 for name in cfg["channels"][1:]}
                if key == "supervisor_private_app_sync":
                    counts = {"APP": 3}
                evidence = {"periods": {period: {"channel_counts": counts}}}
                selected, absent = source_present_channels(cfg, evidence, period)
                self.assertEqual(selected, cfg["channels"][1:])
                self.assertEqual(absent, [cfg["channels"][0]])
                self.assertEqual(source_present_channels(cfg, {"periods": {period: {"channel_counts": {}}}}, period),
                                 ([], cfg["channels"]))
                with self.assertRaisesRegex(ValueError, "审计|清单"):
                    source_present_channels(cfg, {"periods": {}}, period)
