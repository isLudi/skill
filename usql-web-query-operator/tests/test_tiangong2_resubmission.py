from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_tiangong2_editing_execution import FakeReader, FakeRequest, SOURCE, make_task
from _shared.errors import UsageError
from tiangong2_task.cli import build_parser
from tiangong2_task.publishing import finalize_hash
from tiangong2_task.resubmission import consume_resubmission_attempt
from tiangong2_task.schedule import build_schedule_update_plan, verify_schedule_update_readback
from tiangong2_task.submission import (
    Tiangong2SubmitClient, authorize_submit, build_submit_plan, validate_pre_submit_drift,
    validate_submit_plan, verify_submit_readback,
)


class FakeOperations:
    def __init__(self, reader):
        self.reader = reader
        self.config_override = {}
        self.effective_override = {}

    def get_schedule_config(self, task_id):
        return {**self.reader.schedule, "taskId": task_id, "periodic": True,
                **self.config_override}

    def get_task_and_schedule(self, task_id):
        return {**self.reader.schedule, "taskId": task_id, "taskName": make_task().task_name,
                "scheduleFrequency": "2h", **self.effective_override}


class ResubmissionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for module in ("tiangong2_task.artifacts", "tiangong2_task.resubmission"):
            replacement = patch(module + ".TIANGONG2_TASK_RUNTIME_DIR", self.root)
            replacement.start()
            self.addCleanup(replacement.stop)
        self.task = make_task()
        self.reader = FakeReader()
        self.reader.schedule.update(scheduleType=1, firstRunTime="2026-01-01 01:40:00",
                                    endRunTime="2027-12-31 23:59:59", runInterval=2, timeUnit=1)
        self.operations = FakeOperations(self.reader)
        self.original = build_submit_plan(self.reader, task=self.task,
                                          identity={"name": self.task.owner_name}, note="reviewed_channels")
        original_path = self.write("submit_plan.json", self.original, "plan_sha256")
        self.prior_path = self.write("submit_receipt.json", {
            "schema_version": "tiangong2-task-submit-receipt-v1",
            "operation": self.original["operation"], "scope": self.original["scope"],
            "plan_file": str(original_path), "plan_sha256": self.original["plan_sha256"],
            "ok": True, "fully_verified": True, "manual_attention_required": False,
            "remote_mutation_confirmed": True, "submit_request_sent": True,
            "readback": {"saved_source_unchanged": True}, "completed_at": "2026-01-01T01:00:00+00:00",
        })
        self.reader.versions.append({"id": 2, "status": "未发布", "ver": "-"})
        self.reader.version_codes[2] = SOURCE
        schedule_patch = self.root / "schedule_patch.json"
        schedule_patch.write_text(json.dumps({"schema_version": "tiangong2-task-schedule-patch-v1",
                                              "changes": {"firstRunTime": "2026-01-01 23:40:00"}}), encoding="utf-8")
        schedule_plan = build_schedule_update_plan(self.reader, task=self.task,
                                                   identity={"name": self.task.owner_name},
                                                   schedule_patch_file=schedule_patch)
        schedule_plan_path = self.write("schedule_plan.json", schedule_plan, "plan_sha256")
        self.reader.schedule.update(schedule_plan["desired"]["schedule"])
        self.schedule_path = self.write("schedule_receipt.json", {
            "schema_version": "tiangong2-task-schedule-update-receipt-v1",
            "operation": schedule_plan["operation"], "scope": self.original["scope"],
            "plan_file": str(schedule_plan_path), "plan_sha256": schedule_plan["plan_sha256"],
            "status": "saved_effective_scheduler_mismatch", "remote_mutation_confirmed": True,
            "save_request_sent": True, "started_at": "2026-01-01T02:00:00+00:00",
            "completed_at": "2026-01-01T02:01:00+00:00",
            "readback": verify_schedule_update_readback(self.reader, task=self.task, plan=schedule_plan),
        })

    def write(self, name, value, field="receipt_sha256"):
        path = self.root / name
        path.write_text(json.dumps(finalize_hash(value, field), ensure_ascii=False), encoding="utf-8")
        return path

    def plan(self, **kwargs):
        args = dict(reader=self.reader, task=self.task, identity={"name": self.task.owner_name},
                    note="reconfirm_channels", previous_submit_receipt=self.prior_path,
                    resubmit_after_schedule_receipt=self.schedule_path, operations=self.operations)
        args.update(kwargs)
        return build_submit_plan(**args)

    def test_explicit_evidence_enables_only_reconfirmation(self):
        plan = self.plan()
        self.assertEqual(plan["status"], "ready")
        self.assertEqual(plan["resubmission"]["pending_version_id"], 2)
        validate_submit_plan(plan)
        validate_pre_submit_drift(self.reader, task=self.task, plan=plan, operations=self.operations)
        with self.assertRaisesRegex(UsageError, "confirm-submit"):
            authorize_submit(plan, expected_plan_sha256=plan["plan_sha256"], confirm_submit=False)
        auth = authorize_submit(plan, expected_plan_sha256=plan["plan_sha256"], confirm_submit=True)
        request = FakeRequest()
        writer = Tiangong2SubmitClient(request, authorization=auth)
        claim = consume_resubmission_attempt(plan)
        self.assertTrue(Path(claim).is_file())
        writer.submit_task(task_id=self.task.task_id, note="reconfirm_channels")
        self.assertEqual(len(request.calls), 1)
        with self.assertRaisesRegex(UsageError, "single-use"):
            writer.submit_task(task_id=self.task.task_id, note="reconfirm_channels")
        with self.assertRaisesRegex(UsageError, "single resubmission attempt"):
            self.plan()
        with self.assertRaisesRegex(UsageError, "single resubmission attempt"):
            consume_resubmission_attempt(plan)

    def test_default_duplicate_and_rehashed_ready_still_blocked(self):
        plan = build_submit_plan(self.reader, task=self.task, identity={"name": self.task.owner_name}, note="ordinary")
        self.assertEqual(plan["status"], "blocked_already_submitted")
        plan["status"] = "ready"
        with self.assertRaisesRegex(UsageError, "resubmission evidence"):
            validate_submit_plan(finalize_hash(plan, "plan_sha256"))

    def test_requires_both_receipts_and_live_scheduler(self):
        with self.assertRaisesRegex(UsageError, "both"):
            self.plan(previous_submit_receipt=None)
        with self.assertRaisesRegex(UsageError, "live Nezha"):
            self.plan(operations=None)
        self.operations.effective_override["taskId"] = 999
        with self.assertRaisesRegex(UsageError, "Effective Nezha"):
            self.plan()

    def test_receipt_hash_tampering_and_cross_owner_rejected(self):
        receipt = json.loads(self.prior_path.read_text(encoding="utf-8"))
        receipt["scope"]["owner_name"] = "another_owner"
        self.prior_path.write_text(json.dumps(receipt), encoding="utf-8")
        with self.assertRaisesRegex(UsageError, "SHA-256"):
            self.plan()
        self.write(self.prior_path.name, receipt)
        with self.assertRaisesRegex(UsageError, "scope or owner"):
            self.plan()

    def test_unverified_submit_and_schedule_not_sufficient(self):
        for path, field in ((self.prior_path, "fully_verified"), (self.schedule_path, "save_request_sent")):
            original = json.loads(path.read_text(encoding="utf-8"))
            changed = copy.deepcopy(original)
            changed[field] = False
            self.write(path.name, changed)
            with self.assertRaises(UsageError):
                self.plan()
            self.write(path.name, original)

    def test_schedule_before_submission_is_rejected(self):
        receipt = json.loads(self.schedule_path.read_text(encoding="utf-8"))
        receipt["started_at"] = "2025-01-01T00:00:00+00:00"
        self.write(self.schedule_path.name, receipt)
        with self.assertRaisesRegex(UsageError, "follow"):
            self.plan()

    def test_source_changed_or_ambiguous_pending_is_rejected(self):
        self.reader.source = SOURCE + "\n# another change\n"
        with self.assertRaisesRegex(UsageError, "source or published"):
            self.plan()
        self.reader.source = SOURCE
        self.reader.versions.append({"id": 3, "status": "未发布", "ver": "-"})
        self.reader.version_codes[3] = SOURCE
        with self.assertRaisesRegex(UsageError, "exactly one"):
            self.plan()

    def test_live_schedule_and_evidence_drift_rejected(self):
        plan = self.plan()
        self.reader.schedule["retryInterval"] = 100
        with self.assertRaisesRegex(UsageError, "schedule_state_sha256"):
            validate_pre_submit_drift(self.reader, task=self.task, plan=plan, operations=self.operations)
        self.reader.schedule.pop("retryInterval")
        self.operations.config_override["endRunTime"] = "2027-01-01 00:00:00"
        with self.assertRaisesRegex(UsageError, "Effective Nezha"):
            validate_pre_submit_drift(self.reader, task=self.task, plan=plan, operations=self.operations)
        self.operations.config_override.clear()
        receipt = json.loads(self.schedule_path.read_text(encoding="utf-8"))
        receipt["extra"] = "changed"
        self.write(self.schedule_path.name, receipt)
        with self.assertRaisesRegex(UsageError, "evidence changed"):
            validate_submit_plan(plan)

    def test_next_run_time_can_advance_before_planning_not_after(self):
        self.reader.schedule["nextRunTime"] = "2026-01-02 01:00:00"
        plan = self.plan()
        self.reader.schedule["nextRunTime"] = "2026-01-02 03:00:00"
        with self.assertRaisesRegex(UsageError, "schedule_state_sha256"):
            validate_pre_submit_drift(self.reader, task=self.task, plan=plan, operations=self.operations)

    def test_readback_reports_unique_version_and_stable_acceptance_honestly(self):
        plan = self.plan()
        stable = verify_submit_readback(self.reader, task=self.task, plan=plan, attempts=1)
        self.assertFalse(stable["fully_verified"])
        self.assertEqual(stable["matching_unpublished_version_ids"], [2])
        self.reader.metadata["updateTime"] = "2026-01-01 03:00:00"
        changed = verify_submit_readback(self.reader, task=self.task, plan=plan, attempts=1)
        self.assertTrue(changed["fully_verified"])
        self.reader.versions.append({"id": 3, "status": "未发布", "ver": "-"})
        self.reader.version_codes[3] = SOURCE
        with self.assertRaisesRegex(UsageError, "unique pending version"):
            verify_submit_readback(self.reader, task=self.task, plan=plan, attempts=1)

    def test_cli_exposes_receipt_bound_mode_without_force_flag(self):
        args = build_parser().parse_args([
            "plan-task-submit", "--project-id", "308", "--folder", "owner", "--menu-id", "1",
            "--task-name", "task", "--note", "reviewed", "--previous-submit-receipt", str(self.prior_path),
            "--resubmit-after-schedule-receipt", str(self.schedule_path)])
        self.assertEqual(args.resubmit_after_schedule_receipt, self.schedule_path)


if __name__ == "__main__":
    unittest.main()
