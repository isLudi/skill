from __future__ import annotations

import copy
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from governed_temp_table_sync import (  # noqa: E402
    WorkflowError,
    build_navigation_failure_recovery,
    sha256_file,
    upload_production,
    validate_navigation_failure_recovery,
    write_artifact,
)


class UploadRecoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.target = self.root / "jiagou_db.xlsx"
        self.target.write_bytes(b"locally applied workbook")
        self.target_sha = sha256_file(self.target)
        self.registry = self.root / "registry.json"
        self.registry.write_text("{}", encoding="utf-8")
        self.family = "market_period_architecture"
        self.message = {"message_id": "om_latest", "source_sha256": "source-hash"}
        self.original = {
            "family_id": self.family,
            "source_message": self.message,
            "target_path": str(self.target),
            "platform_temp_table": "dingxi01_jiagou_db",
            "target_after_sha256": self.target_sha,
            "diff": {"changed": True, "source_slices": ["20261113期"]},
        }
        old_plan = {"status": "ready", "tables": [self.original]}
        old_plan_path = self.root / "old_plan.json"
        old_plan_hash = write_artifact(old_plan_path, old_plan, "plan_sha256")
        old_local = {
            "status": "success",
            "plan_path": str(old_plan_path),
            "plan_sha256": old_plan_hash,
            "tables": [{
                "family_id": self.family,
                "target_path": str(self.target),
                "changed": True,
                "current_sha256": self.target_sha,
                "expected_sha256": self.target_sha,
            }],
        }
        old_local_path = self.root / "old_local.json"
        old_local_hash = write_artifact(old_local_path, old_local, "receipt_sha256")
        self.failed = {
            "artifact_type": "GovernedDepartmentTempTableUploadReceipt",
            "status": "partial_failure",
            "local_receipt_path": str(old_local_path),
            "local_receipt_sha256": old_local_hash,
            "uploads": [],
            "failure": {
                "family_id": self.family,
                "error_type": "WorkflowError",
                "message": 'Locator.wait_for: Timeout 2000ms exceeded.\n  - waiting for get_by_text("临时表", exact=True).last to be visible',
            },
            "pending_families": [self.family],
        }
        self.failed_path = self.root / "failed_upload.json"
        self.failed_hash = write_artifact(self.failed_path, self.failed, "receipt_sha256")
        self.plan = {
            "status": "ready",
            "registry_path": str(self.registry),
            "registry_sha256": sha256_file(self.registry),
            "runtime_dir": str(self.root),
            "selection": {"family_ids": [self.family], "explicit_message_ids": {}},
            "selected_message_ids": {self.family: "om_latest"},
            "tables": [{
                "family_id": self.family,
                "source_message": self.message,
                "target_path": str(self.target),
                "platform_temp_table": "dingxi01_jiagou_db",
                "target_before_sha256": self.target_sha,
                "target_after_sha256": self.target_sha,
                "diff": {"changed": False},
                "source_selection": {"target_equivalent_slices": ["20261113期"]},
                "allow_baseline_target_errors": True,
                "validation_after": {"error_count": 0},
            }],
        }

    def test_recovery_is_bound_to_source_target_and_failure_stage(self) -> None:
        proof = build_navigation_failure_recovery(self.plan, self.failed_path, self.failed_hash)
        self.plan["upload_recovery"] = proof
        self.assertEqual(validate_navigation_failure_recovery(self.plan), self.family)
        for key, value in (("message_id", "om_new"), ("source_sha256", "other")):
            other = copy.deepcopy(self.plan)
            other["tables"][0]["source_message"][key] = value
            with self.subTest(key=key), self.assertRaises(WorkflowError):
                validate_navigation_failure_recovery(other)
        other = copy.deepcopy(self.plan)
        other["tables"][0]["target_before_sha256"] = "other"
        with self.assertRaises(WorkflowError):
            validate_navigation_failure_recovery(other)
        other = copy.deepcopy(self.plan)
        other["tables"][0]["source_selection"]["target_equivalent_slices"] = []
        with self.assertRaisesRegex(WorkflowError, "still pending"):
            validate_navigation_failure_recovery(other)
        self.failed["failure"]["message"] = "Timeout after import was submitted"
        updated_hash = write_artifact(self.failed_path, self.failed, "receipt_sha256")
        with self.assertRaisesRegex(WorkflowError, "pre-import"):
            build_navigation_failure_recovery(self.plan, self.failed_path, updated_hash)

    def test_recovery_no_change_plan_calls_upload_operator(self) -> None:
        self.plan["upload_recovery"] = build_navigation_failure_recovery(
            self.plan, self.failed_path, self.failed_hash
        )
        plan_path = self.root / "sync_plan.json"
        plan_hash = write_artifact(plan_path, self.plan, "plan_sha256")
        local = {
            "status": "success_no_local_changes",
            "plan_path": str(plan_path),
            "plan_sha256": plan_hash,
            "tables": [{"target_path": str(self.target), "expected_sha256": self.target_sha}],
        }
        local_path = self.root / "local_apply_receipt.json"
        local_hash = write_artifact(local_path, local, "receipt_sha256")
        args = SimpleNamespace(
            confirm_production_upload=True,
            local_receipt=local_path,
            expected_receipt_sha256=local_hash,
            headed=False,
            timeout_seconds=600,
        )
        operator_result = {
            "ok": True,
            "status": "Success",
            "import_history_row": {"status": "success"},
            "validation_result": {"ok": True},
        }
        with (
            mock.patch("governed_temp_table_sync.load_registry", return_value={}),
            mock.patch("governed_temp_table_sync.assert_source_baseline_state_current"),
            mock.patch("governed_temp_table_sync.assert_plan_source_bundles_current"),
            mock.patch("governed_temp_table_sync.assert_plan_source_quality_current"),
            mock.patch("governed_temp_table_sync.discover_live_messages", return_value=({}, [])),
            mock.patch("governed_temp_table_sync.select_messages", return_value=({self.family: {"message_id": "om_latest"}}, {}, [])),
            mock.patch("governed_temp_table_sync.update_source_baseline_state", return_value=None),
            mock.patch("governed_temp_table_sync.run_json_command", return_value=operator_result) as call,
            redirect_stdout(io.StringIO()),
        ):
            self.assertEqual(upload_production(args), 0)
        self.assertEqual(call.call_count, 1)
        self.assertIn("upload-temp-table", call.call_args.args[1])
        receipt = json.loads((self.root / "upload_receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["uploads"][0]["status"], "Success")
        self.assertIsNotNone(receipt["uploads"][0]["import_history_row"])


if __name__ == "__main__":
    unittest.main()
