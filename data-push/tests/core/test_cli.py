from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
from types import SimpleNamespace
from unittest.mock import Mock, patch
import unittest

from lark_delivery import cli
from lark_delivery.core import catalog


class ChannelCliTests(unittest.TestCase):
    def setUp(self):
        self.config = catalog.load_channel(catalog.DEFAULT_CHANNEL)

    def invoke(self, *args):
        with redirect_stdout(io.StringIO()):
            return cli.main(list(args), bound_channel=catalog.DEFAULT_CHANNEL)

    def test_describe_default_uses_no_remote_operation(self):
        with patch.object(cli, "adapter_for") as adapter:
            self.assertEqual(self.invoke(), 0)
            adapter.return_value.prepare.assert_not_called()
            adapter.return_value.schedule.assert_not_called()

    def test_paused_run_does_not_enable_or_prepare(self):
        self.config["schedule"]["enabled"] = False
        with patch.object(catalog, "load_channel", return_value=self.config), patch.object(cli, "adapter_for") as adapter:
            self.assertEqual(self.invoke("run", "--confirm-send"), 0)
            adapter.return_value.schedule.assert_not_called()

    def test_run_requires_explicit_confirmation(self):
        with self.assertRaises(SystemExit):
            self.invoke("run")

    def test_bound_script_cannot_switch_department_or_channel(self):
        with self.assertRaises(SystemExit):
            self.invoke("describe", "--domain", "qingcheng")

    def test_scheduled_period_and_ledger_cannot_be_overridden(self):
        for args in (("preflight", "--report-type", "both"), ("run", "--confirm-send", "--state-dir", "other")):
            with self.assertRaises(SystemExit):
                self.invoke(*args)

    def test_preview_isolated_per_group_and_never_sends(self):
        self.config["targets"].append({"id": "second", "chat_id": "oc_second", "display_name": "Second", "enabled": True})
        adapter = SimpleNamespace(prepare=Mock(return_value={"period": "20260911期"}), write_preview=Mock(return_value={}))
        with patch.object(catalog, "load_channel", return_value=self.config), patch.object(cli, "adapter_for", return_value=adapter), \
             patch.object(cli.feishu, "send_markdown") as send:
            self.assertEqual(self.invoke("preview"), 0)
        self.assertEqual(adapter.prepare.call_count, 2)
        self.assertNotEqual(adapter.prepare.call_args_list[0].kwargs["state_dir"], adapter.prepare.call_args_list[1].kwargs["state_dir"])
        send.assert_not_called()

    def test_dry_run_never_opens_message_outlet(self):
        context = {"period": "20260911期", "markdown": "preview", "idempotency_key": "fixture"}
        adapter = SimpleNamespace(prepare=Mock(return_value=context), write_preview=Mock(return_value={}))
        with patch.object(cli, "adapter_for", return_value=adapter), patch.object(cli.feishu, "send_markdown") as send:
            self.assertEqual(self.invoke("dry-run"), 0)
        self.assertIs(send.call_args.kwargs["dry_run"], True)

    def test_empty_channel_preview_is_reported_and_dry_run_does_not_open_outlet(self):
        context = {"period": "20260911期", "markdown": "", "idempotency_key": "fixture",
                   "skip_delivery": True,
                   "skip_reason": "no_supervisor_rows_meet_minimum_post_leads"}
        artifacts = {"status": "skipped_no_eligible_rows", "image_files": [], "message_sent": False}
        adapter = SimpleNamespace(prepare=Mock(return_value=context), write_preview=Mock(return_value=artifacts))
        output = io.StringIO()
        with patch.object(cli, "adapter_for", return_value=adapter), \
             patch.object(cli.feishu, "send_markdown") as send, redirect_stdout(output):
            self.assertEqual(cli.main(["dry-run"], bound_channel=catalog.DEFAULT_CHANNEL), 0)
        self.assertIn("skipped_no_eligible_rows", output.getvalue())
        adapter.write_preview.assert_called_once_with(context)
        send.assert_not_called()

    def test_app_advisor_preview_disables_person_lookup_and_member_invites(self):
        adapter = SimpleNamespace(prepare=Mock(return_value={"period": "20261009期"}),
                                  write_preview=Mock(return_value={}))
        with patch.object(cli, "adapter_for", return_value=adapter), \
             patch.object(cli.feishu, "send_markdown") as send, redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(["preview"], bound_channel="market_consultant/app_grade_9"), 0)
        self.assertIs(adapter.prepare.call_args.kwargs["no_mentions"], True)
        send.assert_not_called()

    def test_app_order_preview_uses_readonly_sequence_and_never_sends(self):
        adapter = SimpleNamespace(preview_order=Mock(return_value={"message_sent": False}))
        with patch.object(cli, "adapter_for", return_value=adapter), \
             patch.object(cli.feishu, "send_markdown") as send, redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(["preview-order"], bound_channel="market_consultant/app_grade_9"), 0)
        adapter.preview_order.assert_called_once()
        send.assert_not_called()

    def test_order_preview_cannot_override_report_policy(self):
        with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
            cli.main(["preview-order", "--report-type", "result"], bound_channel="market_consultant/app_grade_9")
