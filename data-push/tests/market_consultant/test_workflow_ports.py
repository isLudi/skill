from copy import deepcopy
from pathlib import Path
import tempfile
from unittest.mock import Mock, patch
import unittest

from lark_delivery.core import catalog
from lark_delivery.core.contracts import ReportPorts
from lark_delivery.domains.market_consultant.adapter import report_arguments
from lark_delivery.domains.market_consultant.workflow import prepare_report, _channel_scope
from lark_delivery.domains.market_consultant.channels import self_incubated_koc_5 as policy
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

    def test_member_failure_cannot_silently_become_names_only(self):
        args = report_arguments(self.definition, catalog.select_targets(self.definition)[0])
        self.ports.missing_members.return_value = ["负责人A"]
        with self.assertRaisesRegex(ValueError, "负责人账号或群成员"):
            prepare_report(args, self.definition, ports=self.ports)

    def test_channel_match_contract_excludes_case_variant_before_scope_validation(self):
        definition = catalog.load_channel("market_consultant/supervisor_private_app_sync")
        self.assertEqual(_channel_scope(definition, "app"), "app")
        self.assertEqual(_channel_scope(definition, "集团私域"), "集团私域")
        self.assertNotEqual(_channel_scope(definition, "app"), "APP")
