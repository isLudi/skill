from argparse import Namespace
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import unittest

from lark_delivery.common.report_ports import FeishuReportPorts
from lark_delivery.common import im
from lark_delivery.core.contracts import DepartmentAdapter
from lark_delivery.domains.market_consultant import adapter


class PortTests(unittest.TestCase):
    def test_market_module_implements_department_adapter(self):
        self.assertIsInstance(adapter, DepartmentAdapter)

    def test_prepare_ports_expose_no_mutation_method(self):
        ports = FeishuReportPorts(SimpleNamespace())
        self.assertFalse(hasattr(ports, "send_markdown"))
        self.assertFalse(hasattr(ports, "upload_image"))

    def test_record_projection_and_filter_pass_through_unchanged(self):
        backend = SimpleNamespace(_fetch_view_records=Mock(return_value=[{"record_id": "r"}]))
        ports = FeishuReportPorts(backend)
        coords, fields, audit, scope = {"table_id": "table"}, ["lead_id"], {}, {"logic": "and"}
        self.assertEqual(ports.read_records(coords, object(), fields, filter_json=scope, audit=audit), [{"record_id": "r"}])
        self.assertIs(backend._fetch_view_records.call_args.kwargs["filter_json"], scope)
        self.assertIs(backend._fetch_view_records.call_args.kwargs["audit"], audit)

    def test_user_lookup_batches_and_keeps_completeness_evidence(self):
        replies = [{"queries": [{"has_more": True}], "users": [{"open_id": "ou_a"}]},
                   {"queries": [{"error": "lookup failed"}], "users": []}]
        backend = SimpleNamespace(run_lark=Mock(side_effect=[json.dumps({"ok": True, "data": x}) for x in replies]))
        result = FeishuReportPorts(backend).search_users([f"user{i}" for i in range(21)], Namespace(timeout=60))
        self.assertEqual(backend.run_lark.call_count, 2)
        self.assertTrue(result["queries"][0]["has_more"])
        self.assertIn("error", result["queries"][1])

    def test_send_dry_run_stays_dry_run_and_keeps_identity(self):
        runner = Mock(return_value=json.dumps({"ok": True, "data": {}}))
        im.send_markdown("oc_fixed", "message", "key", "bot", dry_run=True, timeout=60, runner=runner)
        argv = runner.call_args.args[0]
        self.assertIn("--dry-run", argv)
        self.assertEqual(argv[argv.index("--as") + 1], "bot")

    def test_upload_uses_relative_path_and_same_identity(self):
        runner = Mock(return_value=json.dumps({"ok": True, "data": {"image_key": "img_test"}}))
        path = Path("folder") / "render.png"
        self.assertEqual(im.upload_image(path, "bot", 60, runner=runner), "img_test")
        argv = runner.call_args.args[0]
        self.assertEqual(argv[argv.index("--file") + 1], "./render.png")
        self.assertEqual(runner.call_args.kwargs["cwd"], str(path.parent))
