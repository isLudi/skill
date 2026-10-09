from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from _shared.errors import UsageError
from oes_achievement.base_records import verify_records
from oes_achievement.base_sync import run_base_sync
from oes_achievement.board import SHANGHAI
from oes_achievement.cli import _run, build_parser
from oes_achievement.event_log import EventLog
from oes_achievement.retention import CacheRetention
from oes_achievement.workbook import atomic_json

NOW = datetime(2026, 10, 4, 10, tzinfo=SHANGHAI)


class RetentionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.output = self.root / "runs"
        self.logger = EventLog(self.root / "logs", "test", "tblTarget", clock=lambda: NOW)
        self.retention = CacheRetention(self.output, self.root / "index", "baseToken", "tblTarget", 7,
                                        self.logger, clock=lambda: NOW)

    def completed_run(self, key, age=8):
        digest = hashlib.sha256(key.encode()).hexdigest()
        directory = self.output / f"base-sync-{digest[:24]}"
        directory.mkdir()
        receipt = {"status": "completed", "identity": {"run_key_hash": digest, "base_token": "baseToken",
                   "table_id": "tblTarget", "config_table_id": "tblConfig", "config_record_id": "config"},
                   "completed_at": (NOW - timedelta(days=age)).isoformat(), "end_ms": 1,
                   "row_count": 0, "verification": verify_records([], [])}
        atomic_json(directory / "base-receipt.json", receipt)
        source = directory / "source"
        source.mkdir()
        (source / "attachment.xlsx").write_bytes(b"synthetic cache")
        return directory, receipt

    def test_old_verified_run_is_removed_and_compact_replay_guard_survives(self):
        directory, receipt = self.completed_run("old")
        expected_bytes = sum(path.stat().st_size for path in directory.rglob("*") if path.is_file())
        result = self.retention.cleanup()
        self.assertFalse(directory.exists())
        self.assertEqual((result["deleted_runs"], result["deleted_files"], result["deleted_bytes"]), (1, 2, expected_bytes))
        marker = self.retention.expired_completion(receipt["identity"]["run_key_hash"])
        self.assertEqual(marker["cache_state"], "purged")
        self.assertEqual(marker["verification"]["mismatch_count"], 0)
        self.assertIn("cache_run_deleted", self.logger.path.read_text(encoding="utf-8"))

    def test_seven_day_boundary_uses_completion_time_not_query_date(self):
        boundary, _ = self.completed_run("boundary", 7)
        recent, receipt = self.completed_run("recent", 1)
        receipt["identity"]["start_ms"] = 0
        atomic_json(recent / "base-receipt.json", receipt)
        old, _ = self.completed_run("older", 7 + 1 / 86400)
        result = self.retention.cleanup()
        self.assertTrue(boundary.is_dir())
        self.assertTrue(recent.is_dir())
        self.assertFalse(old.exists())
        self.assertEqual(result["retained_runs"], 2)

    def test_unfinished_unknown_and_other_base_are_never_deleted(self):
        directories = []
        for status in ("collecting", "failed_restored", "base_write_uncertain", "failed_requires_recovery"):
            directory, receipt = self.completed_run(status, 90)
            receipt["status"] = status
            atomic_json(directory / "base-receipt.json", receipt)
            directories.append(directory)
        other, receipt = self.completed_run("other-base", 90)
        receipt["identity"]["base_token"] = "differentBase"
        atomic_json(other / "base-receipt.json", receipt)
        unknown = self.output / "base-sync-unknown"
        unknown.mkdir()
        private = self.root / "private"
        private.mkdir()
        (private / "usql_api.env").write_text("synthetic credential", encoding="utf-8")
        state = self.root / "runtime" / "oes-achievement"
        state.mkdir(parents=True)
        (state / "state.json").write_text("{}", encoding="utf-8")
        result = self.retention.cleanup()
        self.assertEqual(result["deleted_runs"], 0)
        self.assertTrue(all(path.is_dir() for path in directories + [other, unknown]))
        self.assertTrue((private / "usql_api.env").is_file())
        self.assertTrue((state / "state.json").is_file())

    def test_incomplete_or_malformed_verification_blocks_deletion(self):
        for value in (None, {}, {"verified": True, "fields_verified": None}):
            directory, receipt = self.completed_run(f"bad-{value}")
            receipt["verification"] = value
            atomic_json(directory / "base-receipt.json", receipt)
        result = self.retention.cleanup()
        self.assertEqual(result["failed_runs"], 3)
        self.assertEqual(result["deleted_runs"], 0)
        self.assertEqual(len(list(self.output.glob("base-sync-*"))), 3)

    def test_nested_link_or_junction_stops_recursive_cleanup(self):
        directory, _ = self.completed_run("link")
        link = directory / "source"
        with patch("oes_achievement.retention.is_link", side_effect=lambda path: path == link):
            result = self.retention.cleanup()
        self.assertEqual(result["failed_runs"], 1)
        self.assertTrue((link / "attachment.xlsx").is_file())

    def test_real_directory_link_preserves_its_external_target(self):
        directory, _ = self.completed_run("real-link")
        outside = self.root / "outside-cache"
        outside.mkdir()
        (outside / "keep.txt").write_text("keep", encoding="utf-8")
        link = directory / "linked-data"
        if os.name == "nt":
            import _winapi
            _winapi.CreateJunction(str(outside), str(link))
            self.addCleanup(link.rmdir)
        else:
            link.symlink_to(outside, target_is_directory=True)
            self.addCleanup(lambda: link.unlink(missing_ok=True))
        self.assertEqual((link / "keep.txt").read_text(encoding="utf-8"), "keep")
        self.assertEqual(self.retention.cleanup()["failed_runs"], 1)
        self.assertEqual((outside / "keep.txt").read_text(encoding="utf-8"), "keep")

    def test_partial_cleanup_keeps_replay_guard_and_can_finish_later(self):
        directory, receipt = self.completed_run("partial")
        def interrupted(path):
            (path / "base-receipt.json").unlink()
            raise PermissionError("synthetic file lock")
        with patch("oes_achievement.retention.shutil.rmtree", side_effect=interrupted):
            result = self.retention.cleanup()
        self.assertEqual(result["failed_runs"], 1)
        marker = self.retention.expired_completion(receipt["identity"]["run_key_hash"])
        self.assertEqual(marker["cache_state"], "cleanup_pending")
        self.assertEqual(self.retention.cleanup()["deleted_runs"], 1)
        self.assertFalse(directory.exists())

    def test_index_write_failure_preserves_entire_cache(self):
        directory, receipt = self.completed_run("index-failure")
        self.retention.register(receipt)
        with patch("oes_achievement.retention.atomic_json", side_effect=PermissionError("synthetic failure")):
            result = self.retention.cleanup()
        self.assertEqual(result["failed_runs"], 1)
        self.assertTrue((directory / "base-receipt.json").is_file())
        self.assertTrue((directory / "source/attachment.xlsx").is_file())

    def test_changed_receipt_prevents_deletion_even_with_a_verified_index(self):
        directory, receipt = self.completed_run("changed")
        self.retention.register(receipt)
        receipt["status"] = "failed_requires_recovery"
        atomic_json(directory / "base-receipt.json", receipt)
        self.assertEqual(self.retention.cleanup()["skipped_runs"], 1)
        self.assertTrue(directory.exists())

    def test_expired_run_never_opens_base_or_resubmits_export(self):
        directory, _ = self.completed_run("expired-job")
        self.assertEqual(self.retention.cleanup()["deleted_runs"], 1)
        args = build_parser().parse_args(["sync-base", "--base-token", "baseToken", "--table-id", "tblTarget",
              "--config-table-id", "tblConfig", "--output-dir", str(self.output), "--run-key", "expired-job"])
        args.event_log, args.cache_retention = self.logger, self.retention
        with patch("oes_achievement.base_sync.BaseClient") as client, \
             patch("oes_achievement.base_sync.run_partitioned_pipeline") as source, \
             patch("oes_achievement.base_sync.OES_RUNTIME_DIR", self.root / "runtime/oes-achievement"):
            result = run_base_sync(None, args)
        client.assert_not_called()
        source.assert_not_called()
        self.assertEqual(result["status"], "completed_cache_expired")
        self.assertFalse(result["remote_readback_performed"])
        self.assertFalse(directory.exists())

    def test_manual_cleanup_does_not_import_browser_or_use_remote_clients(self):
        args = build_parser().parse_args(["clean-cache", "--base-token", "baseToken", "--table-id", "tblTarget",
                                        "--output-dir", str(self.output)])
        with patch("oes_achievement.base_sync.OES_RUNTIME_DIR", self.root / "runtime/oes-achievement"), \
             patch("oes_achievement.cli.import_playwright") as browser, \
             patch("oes_achievement.base_sync.BaseClient") as client:
            result = _run(args)
        browser.assert_not_called()
        client.assert_not_called()
        self.assertEqual(result["status"], "completed")
        self.assertTrue(Path(result["log_file"]).is_file())

    def test_invalid_retention_and_index_inside_cache_are_rejected(self):
        for days in (0, -1, True, 1.5, 3651):
            with self.subTest(days=days), self.assertRaises(UsageError):
                CacheRetention(self.output, self.root / "index", "baseToken", "tblTarget", days, self.logger)
        with self.assertRaises(UsageError):
            CacheRetention(self.output, self.output / "index", "baseToken", "tblTarget", 7, self.logger)


class EventLogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.clock = NOW
        self.logger = EventLog(self.root, "hash", "tblTarget", clock=lambda: self.clock)

    def test_concurrent_phases_remain_valid_json_without_credentials_or_rows(self):
        def write(worker):
            for index in range(40):
                self.logger.emit("phase_completed", batch_index=index, row_count=worker,
                                 password="secret-value", token="secret-token", rows=[{"手机号": "personal"}],
                                 exception="secret exception contents")
        with ThreadPoolExecutor(max_workers=5) as pool:
            list(pool.map(write, range(5)))
        content = self.logger.path.read_text(encoding="utf-8")
        records = [json.loads(line) for line in content.splitlines()]
        self.assertEqual(len(records), 201)
        self.assertNotIn("secret", content)
        self.assertNotIn("personal", content)
        self.assertEqual(self.logger.write_errors, 0)

    def test_daily_rotation_and_thirty_calendar_day_retention(self):
        old = self.root / "oes-base-2026-09-04.jsonl"
        old.write_text("old", encoding="utf-8")
        boundary = self.root / "oes-base-2026-09-05.jsonl"
        boundary.write_text("boundary", encoding="utf-8")
        unrelated = self.root / "manual-notes.txt"
        unrelated.write_text("keep", encoding="utf-8")
        self.assertEqual(self.logger.prune(30), 1)
        self.assertFalse(old.exists())
        self.assertTrue(boundary.exists())
        self.assertTrue(unrelated.exists())
        self.clock += timedelta(days=1)
        self.logger.emit("next_day")
        self.assertTrue((self.root / "oes-base-2026-10-05.jsonl").is_file())

    def test_initial_log_failure_stops_before_any_replacement(self):
        with patch.object(EventLog, "emit", return_value=False), self.assertRaisesRegex(UsageError, "no Base replacement"):
            EventLog(self.root, "hash", "tblTarget")

    def test_later_log_failure_is_reported_without_raising_after_remote_write(self):
        with patch.object(Path, "open", side_effect=PermissionError("synthetic disk failure")):
            self.assertFalse(self.logger.emit("base_write_batch_completed", batch_rows=500))
        self.assertEqual(self.logger.write_errors, 1)


if __name__ == "__main__":
    unittest.main()
