from datetime import datetime
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from _shared.errors import UsageError
from oes_achievement.base_client import BaseClient
from oes_achievement.base_records import HEADERS, canonical, field_definitions, timestamp_ms, verify_records, workbook_records
from oes_achievement.base_sync import run_base_sync
from oes_achievement.cli import build_parser
from oes_achievement.workbook import atomic_json


def record(index=1):
    row = {name: f"value{index}" for name in HEADERS}
    row.update({"时间": timestamp_ms("2026-06-19T00:00:00+08:00"), "订单号": "001234567890123456789",
                "手机号": "000012345", "userId": "00111111111111111", "业绩金额": 1.25,
                "班级bizNumber": "", "转介绍归属类型": None})
    return row


def workbook(path, rows):
    from openpyxl import Workbook
    book = Workbook()
    sheet = book.active
    sheet.append(HEADERS)
    for row in rows:
        sheet.append([row[name] for name in HEADERS])
    book.save(path)
    book.close()


class ExcelBaseContractTests(unittest.TestCase):
    def test_every_field_preserves_long_text_ids_and_duplicate_orders(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "native.xlsx"
            rows = [record(1), record(2)]
            workbook(path, rows)
            converted = workbook_records([path], 2)
            self.assertEqual(converted[0]["订单号"], rows[0]["订单号"])
            self.assertEqual(converted[0]["手机号"], rows[0]["手机号"])
            self.assertEqual(verify_records(rows, converted)["cell_comparisons"], 26)

    def test_a_change_in_any_of_the_13_fields_blocks_completion(self):
        row = record()
        for name in HEADERS:
            with self.subTest(field=name):
                changed = {**row, name: row[name] + 1 if name == "时间" else 2 if name == "业绩金额" else "changed"}
                with self.assertRaisesRegex(UsageError, "readback differs"):
                    verify_records([row], [changed])

    def test_datetime_offsets_and_empty_text_are_equivalent(self):
        row = record()
        actual = {**row, "时间": "2026-06-18T16:00:00Z", "班级bizNumber": None, "转介绍归属类型": ""}
        self.assertEqual(canonical(row), canonical(actual))


class NativeBatchAndPaginationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        with patch("oes_achievement.base_client.resolve_cli", return_value="native-cli"):
            self.client = BaseClient("baseToken", Path(self.temp.name))

    def test_native_create_uses_500_and_stdin_without_a_shell(self):
        response = {"ok": True, "identity": "user", "data": {"code": 0, "data": {"records": [{"record_id": f"r{i}"} for i in range(500)]}}}
        with patch("oes_achievement.base_client.subprocess.run", return_value=subprocess.CompletedProcess([], 0, json.dumps(response), "")) as invoke:
            self.assertEqual(len(self.client.create("tblTarget", [record()] * 500)), 500)
        call = invoke.call_args
        self.assertIn("/records/batch_create", call.args[0][3])
        self.assertFalse(call.kwargs["shell"])
        self.assertEqual(len(json.loads(call.kwargs["input"])["records"]), 500)
        self.assertIn("--data", call.args[0])
        with self.assertRaisesRegex(UsageError, "1 to 500"):
            self.client.create("tblTarget", [record()] * 501)

    def test_native_delete_checks_every_response_id_and_deleted_status(self):
        with patch.object(self.client, "native", return_value={"records": [{"record_id": "a", "deleted": False}]}):
            with self.assertRaisesRegex(UsageError, "did not confirm"):
                self.client.delete("tblTarget", ["a"])
        with self.assertRaisesRegex(UsageError, "at most 500"):
            self.client.delete("tblTarget", ["a"] * 501)

    def test_complete_read_uses_2000_has_more_and_authoritative_next_offset(self):
        pages = [[{"record_id": "r1", "订单号": "one"}], [{"record_id": "r2", "订单号": "two"}]]
        def call(command, *options):
            offset = int(options[options.index("--offset") + 1])
            index = 0 if offset == 0 else 1
            path = self.client.directory / options[options.index("--output") + 1]
            path.write_text("\n".join(json.dumps(row) for row in pages[index]), encoding="utf-8")
            self.assertEqual(options[options.index("--limit") + 1], "2000")
            self.assertEqual(offset, 0 if index == 0 else 123)
            return {"base_token": "baseToken", "table_id": "tblTarget", "rev": 5,
                    "query_context": {"record_scope": "all_records"}, "records_count": 1,
                    "has_more": index == 0, "next_offset": 123}
        with patch.object(self.client, "call", side_effect=call):
            self.assertEqual(len(self.client.records("tblTarget", ["订单号"], "full")), 2)


class FakeClient:
    def __init__(self):
        self.rows = [{**record(0), "record_id": "old"}]
        self.created_sizes = []
        self.deleted_sizes = []
        self.deleted = threading.Event()
        self.source_entered = threading.Event()
        self.wait_source = True
        self.counter = 0

    def fields(self, table):
        return field_definitions()

    def records(self, table, fields, label):
        if table == "tblConfig":
            return [{"record_id": "config", "开始时间": "2026-06-19T00:00:00+08:00", "启用": True, "数据表ID": "tblTarget"}]
        return [dict(row) for row in self.rows]

    def delete(self, table, ids):
        if self.wait_source:
            if not self.source_entered.wait(5):
                raise AssertionError("OES collection did not run concurrently with deletion")
        self.deleted_sizes.append(len(ids))
        self.rows = [row for row in self.rows if row["record_id"] not in ids]
        self.deleted.set()

    def create(self, table, values):
        self.created_sizes.append(len(values))
        ids = []
        for row in values:
            self.counter += 1
            identity = f"new{self.counter}"
            self.rows.append({**row, "record_id": identity})
            ids.append(identity)
        return ids

    def call(self, *args, **kwargs):
        return {}


class ParallelReplacementTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.args = build_parser().parse_args(["sync-base", "--base-token", "baseToken", "--table-id", "tblTarget",
            "--config-table-id", "tblConfig", "--output-dir", str(self.root / "out"), "--run-key", "one-run"])
        self.client = FakeClient()
        self.patchers = [patch("oes_achievement.base_sync.BaseClient", return_value=self.client),
                         patch("oes_achievement.base_sync.OES_RUNTIME_DIR", self.root / "runtime")]
        for patcher in self.patchers:
            patcher.start()
            self.addCleanup(patcher.stop)

    def source(self, playwright, args, start, end):
        self.client.source_entered.set()
        self.assertTrue(self.client.deleted.wait(5), "Deletion must overlap mail collection")
        self.assertEqual(args.time_window.start_ms, timestamp_ms("2026-06-19T00:00:00+08:00"))
        values = [record(index) for index in range(1001)]
        args.output_dir.mkdir(parents=True, exist_ok=True)
        path = args.output_dir / "native.xlsx"
        workbook(path, values)
        receipt = {"status": "completed", "row_count": len(values), "mail_download": {"file": {"path": str(path)}}}
        receipt_path = args.output_dir / "source.json"
        receipt["receipt_path"] = str(receipt_path)
        atomic_json(receipt_path, receipt)
        return receipt

    def test_parallel_delete_then_full_replacement_and_verified_reuse(self):
        with patch("oes_achievement.base_sync.run_partitioned_pipeline", side_effect=self.source) as source:
            result = run_base_sync(None, self.args)
            self.assertEqual(self.client.created_sizes, [500, 500, 1])
            self.assertEqual(self.client.deleted_sizes, [1])
            self.assertEqual(result["verification"]["cell_comparisons"], 13013)
            repeated = run_base_sync(None, self.args)
            self.assertTrue(repeated["reused_completed_run"])
            self.assertEqual(source.call_count, 1)
            self.assertEqual(len(self.client.rows), 1001)
            events = [json.loads(line)["event"] for line in Path(result["log_file"]).read_text(encoding="utf-8").splitlines()]
            self.assertIn("base_backup_completed", events)
            self.assertEqual(events.count("base_write_batch_completed"), 3)
            self.assertIn("source_collection_completed", events)
            self.assertIn("base_readback_verified", events)
            self.assertIn("run_completed", events)
            self.assertEqual(result["log_write_errors"], 0)
            self.assertEqual(len(list((self.root / "completed-runs").glob("*/*.json"))), 1)

    def test_source_failure_restores_previous_values(self):
        self.client.rows[0]["时间"] = "2026-06-19T00:00:00+08:00"
        def failed(*args):
            self.client.source_entered.set()
            self.assertTrue(self.client.deleted.wait(5))
            raise UsageError("Mail failed")
        with patch("oes_achievement.base_sync.run_partitioned_pipeline", side_effect=failed):
            with self.assertRaisesRegex(UsageError, "failed_restored"):
                run_base_sync(None, self.args)
        self.assertEqual(len(self.client.rows), 1)
        self.assertIsInstance(self.client.rows[0]["时间"], int)
        self.assertEqual(canonical(self.client.rows[0]), canonical(record(0)))
        logs = list((self.root / "logs").glob("*/*.jsonl"))
        self.assertIn('"event": "run_failed"', logs[0].read_text(encoding="utf-8"))
        self.assertFalse(list((self.root / "completed-runs").glob("*/*.json")))

    def test_uncertain_write_keeps_backup_and_blocks_resubmission(self):
        with patch("oes_achievement.base_sync.run_partitioned_pipeline", side_effect=self.source), \
             patch.object(self.client, "create", side_effect=UsageError("uncertain")):
            with self.assertRaisesRegex(UsageError, "base_write_uncertain"):
                run_base_sync(None, self.args)
            with self.assertRaisesRegex(UsageError, "inspect the saved backup"):
                run_base_sync(None, self.args)
        self.assertTrue(list((self.root / "out").glob("*/previous-records.json")))


if __name__ == "__main__":
    unittest.main()
