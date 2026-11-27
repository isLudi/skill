from __future__ import annotations

import sys
import tempfile
import unittest
import io
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from _shared.errors import UsageError
from usql_web_query.commands.upload_temp_table import assert_file_unchanged, assert_import_row_count, cmd_upload_temp_table, file_sha256
from usql_web_query.temp_table_upload import (
    find_matching_history_row, install_reuse_request_guard, matching_table_ids, validate_mapping_fields,
)


class TempTableUploadSafetyTests(unittest.TestCase):
    def test_history_requires_matching_target_file_and_new_import_time(self):
        started = datetime(2026, 11, 14, 14, 30, 0)
        rows = [
            {"临时表名": "lvshuai01_other", "源文件": "cost.xlsx", "导入时间": "2026-11-14 14:30:01", "状态": "成功"},
            {"临时表名": "lvshuai01_cost", "源文件": "other.xlsx", "导入时间": "2026-11-14 14:30:01", "状态": "成功"},
            {"临时表名": "lvshuai01_cost", "源文件": "cost.xlsx", "导入时间": "2026-11-14 14:20:00", "状态": "成功"},
        ]
        self.assertIsNone(find_matching_history_row(rows, "cost", "lvshuai01_cost", started_at=started))
        matching = {"临时表名": "lvshuai01_cost", "源文件": "cost20261114.xlsx", "导入时间": "2026-11-14 14:30:01", "状态": "成功"}
        self.assertEqual(find_matching_history_row([*rows, matching], "cost", "lvshuai01_cost", started_at=started), matching)

    def test_file_hash_and_imported_count_are_enforced(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "table.csv"
            file.write_text("name\na\n", encoding="utf-8")
            expected = file_sha256(file)
            self.assertEqual(assert_file_unchanged(file, expected), expected)
            file.write_text("name\nb\n", encoding="utf-8")
            with self.assertRaisesRegex(UsageError, "SHA-256 changed"):
                assert_file_unchanged(file, expected)
        assert_import_row_count({"数据量": "10,079"}, 10079)
        with self.assertRaisesRegex(UsageError, "row count does not match"):
            assert_import_row_count({"数据量": "10,078"}, 10079)
        with self.assertRaisesRegex(UsageError, "row count does not match"):
            assert_import_row_count({}, 10079)

    def test_quoted_or_duplicate_mapping_columns_are_rejected(self):
        frame = MagicMock()
        modal = MagicMock()
        rows = MagicMock()
        frame.locator.return_value.last = modal
        modal.locator.return_value = rows
        rows.count.return_value = 2
        for fields, allowed in [(["channel", "channel_group"], True),
                                (['"channel"', '"channel_group"'], False),
                                (["channel", "CHANNEL"], False)]:
            def row(index):
                cells = MagicMock()
                cells.count.return_value = 5
                cells.nth.side_effect = lambda col: self._mapping_cell(col, fields[index])
                return SimpleNamespace(locator=lambda _: cells)
            rows.nth.side_effect = row
            if allowed:
                self.assertEqual(validate_mapping_fields(frame, "lvshuai01_test"), fields)
            else:
                with self.assertRaises(UsageError):
                    validate_mapping_fields(frame, "lvshuai01_test")

    @staticmethod
    def _mapping_cell(column, field):
        cell = MagicMock()
        cell.inner_text.return_value = {1: "source.xlsx", 3: "lvshuai01_test"}.get(column, "")
        input_box = MagicMock()
        input_box.count.return_value = 1
        input_box.first.input_value.return_value = field
        cell.locator.return_value = input_box
        return cell

    def test_wrong_live_identity_stops_before_opening_import(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            file = root / "table.csv"
            file.write_text("name\na\n", encoding="utf-8")
            args = SimpleNamespace(env_file=None, username=None, password=None, expected_account="lvshuai01",
                                   file=file, file_type="csv", expected_file_sha256=file_sha256(file),
                                   expected_data_rows=1, registry_path=None, target_table="lvshuai01_table",
                                   validate_manual_table=True, strict_validation=False, state_path=root / "state.json",
                                   artifacts_dir=root / "artifacts", headed=False, browser_channel=None,
                                   executable_path=None, header_row=True, debug_artifacts=False,
                                   target_mode="new", import_mode="overwrite", timeout_ms=1000, keep_history_open=False)
            registry = MagicMock()
            registry.infer_target_table.return_value = ("lvshuai01_table", None)
            browser, context = MagicMock(), MagicMock()
            module = "usql_web_query.commands.upload_temp_table"
            with patch(module + ".query_credentials", return_value=("lvshuai01", "test-secret")), \
                 patch(module + ".ManualTableRegistry.load", return_value=registry), \
                 patch(module + ".validate_manual_table", return_value={"checked": True, "ok": True, "status": "passed"}), \
                 patch(module + ".import_playwright") as playwright, \
                 patch(module + ".launch_context", return_value=(browser, context)), \
                 patch(module + ".navigate_query_page"), \
                 patch(module + ".verify_query_identity", side_effect=UsageError("wrong live account")), \
                 patch(module + ".open_temp_table_panel") as open_panel, \
                 redirect_stdout(io.StringIO()):
                playwright.return_value.return_value.__enter__.return_value = MagicMock()
                self.assertEqual(cmd_upload_temp_table(args), 1)
                open_panel.assert_not_called()

    def test_rejects_double_prefixed_mapping_target(self):
        frame = MagicMock()
        modal = MagicMock()
        rows = MagicMock()
        frame.locator.return_value.last = modal
        modal.locator.return_value = rows
        rows.count.return_value = 1
        cells = MagicMock()
        cells.count.return_value = 5
        def cell(column):
            value = self._mapping_cell(column, "channel")
            if column == 3:
                value.inner_text.return_value = "lvshuai01_lvshuai01_test"
            return value
        cells.nth.side_effect = cell
        rows.nth.return_value.locator.return_value = cells
        with self.assertRaisesRegex(UsageError, "target differs"):
            validate_mapping_fields(frame, "lvshuai01_test")
        self.assertEqual(validate_mapping_fields(frame, "lvshuai01_test",
                                                verified_display_alias="lvshuai01_lvshuai01_test"), ["channel"])

    def test_reuse_request_must_match_live_table_id_and_overwrite_mode(self):
        payload = {"data": [{"id": 14049, "name": "lvshuai01_jiagou_zx"},
                            {"id": 123, "name": "lvshuai01_other"}]}
        self.assertEqual(matching_table_ids(payload, "lvshuai01_jiagou_zx"), {"14049"})
        for table_id, mode, allowed in [(14049, 1, True), (123, 1, False), (14049, 2, False)]:
            context, route = MagicMock(), MagicMock()
            state = install_reuse_request_guard(context, "14049", "overwrite")
            guard = context.route.call_args.args[1]
            request = SimpleNamespace(url="https://example.test/uanalysis-sql/api/tempTable/reuseTable",
                                      method="POST", post_data_json={"tableId": table_id, "type": mode})
            guard(route, request)
            self.assertEqual(route.continue_.called, allowed)
            self.assertEqual(route.abort.called, not allowed)
            self.assertEqual(bool(state["error"]), not allowed)


if __name__ == "__main__":
    unittest.main()
