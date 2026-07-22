from __future__ import annotations

import sys
import tempfile
import unittest
import json
from pathlib import Path
from unittest import mock


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from qingcheng_temp_table_sync import (  # noqa: E402
    build_selection_spec,
    merge_records,
    load_registry,
    resolve_lark_cli,
    select_messages,
    validate_source_records,
)


class MergeWorkflowTests(unittest.TestCase):
    def test_registry_upload_order_must_cover_each_family_once(self) -> None:
        registry = {
            "families": [{"id": "a"}, {"id": "b"}],
            "upload_order": ["a", "a"],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "registry.json"
            path.write_text(json.dumps(registry), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "upload_order"):
                load_registry(path)

    def test_lark_cli_is_resolved_before_download_cwd_changes(self) -> None:
        with mock.patch("qingcheng_temp_table_sync.shutil.which", return_value=r".\lark-cli.cmd"):
            resolved = resolve_lark_cli()

        self.assertTrue(Path(resolved).is_absolute())
        self.assertEqual(Path(resolved).name, "lark-cli.cmd")

    def test_overlapping_slice_is_replaced_instead_of_appended(self) -> None:
        family = {
            "target_columns": ["qici", "name", "goal"],
            "slice_column": "qici",
            "slice_order": "asc",
            "key_columns": ["qici", "name"],
        }
        target = [
            {"qici": "20260710期", "name": "A", "goal": 10},
            {"qici": "20260716期", "name": "A", "goal": 20},
        ]
        source = [{"qici": "20260716期", "name": "A", "goal": 25}]

        merged, effective, diff = merge_records(family, target, target, source, source)

        self.assertEqual(merged, effective)
        self.assertEqual([row["goal"] for row in effective], [10, 25])
        self.assertEqual(diff["replaced_slices"], ["20260716期"])
        self.assertEqual(diff["target_rows_after"], 2)

    def test_qingcheng_scope_replacement_preserves_market_rows(self) -> None:
        family = {
            "target_columns": ["qici", "employee_email_name", "dept_1"],
            "slice_column": "qici",
            "slice_order": "desc",
            "key_columns": ["qici", "employee_email_name"],
            "target_scope": {"column": "dept_1", "equals": "青橙项目部"},
        }
        target = [
            {"qici": "20260722期", "employee_email_name": "old", "dept_1": "青橙项目部"},
            {"qici": "20260722期", "employee_email_name": "market", "dept_1": "市场顾问部"},
        ]
        source = [{"qici": "20260722期", "employee_email_name": "new", "dept_1": "青橙项目部"}]

        _, effective, diff = merge_records(family, target, target, source, source)

        self.assertEqual([row["employee_email_name"] for row in effective], ["new", "market"])
        self.assertEqual(diff["scoped_rows_removed"], 1)
        self.assertEqual(diff["replaced_slices"], ["20260722期"])

    def test_same_effective_values_are_idempotent_even_if_formula_stream_differs(self) -> None:
        family = {
            "target_columns": ["qici", "name", "goal"],
            "slice_column": "qici",
            "slice_order": "asc",
            "key_columns": ["qici", "name"],
        }
        target_write = [{"qici": "20260716期", "name": "A", "goal": "=10+10"}]
        target_effective = [{"qici": "20260716期", "name": "A", "goal": 20}]
        source_write = [{"qici": "20260716期", "name": "A", "goal": 20}]
        source_effective = [{"qici": "20260716期", "name": "A", "goal": 20}]

        _, _, diff = merge_records(
            family, target_write, target_effective, source_write, source_effective
        )

        self.assertFalse(diff["changed"])
        self.assertEqual(diff["unchanged_slices"], ["20260716期"])

    def test_duplicate_source_key_is_blocking(self) -> None:
        family = {
            "key_columns": ["qici", "name"],
            "validation_rules": [{"type": "slice_format", "column": "qici", "pattern": "^\\d{8}期$"}],
        }
        rows = [
            {"qici": "20260716期", "name": "A"},
            {"qici": "20260716期", "name": "A"},
        ]

        issues = validate_source_records(family, rows)

        self.assertTrue(any(issue["rule"] == "unique_key" for issue in issues))

    def test_subset_selection_uses_only_requested_families(self) -> None:
        registry = {
            "families": [
                {"id": "a", "source_filename_patterns": ["^a\\.xlsx$"]},
                {"id": "b", "source_filename_patterns": ["^b\\.xlsx$"]},
            ],
            "upload_order": ["a", "b"],
        }
        selection = build_selection_spec(registry, family_ids=["b"])
        messages = [
            {"message_id": "om_a", "file_name": "a.xlsx", "create_time": "1000"},
            {"message_id": "om_b", "file_name": "b.xlsx", "create_time": "2000"},
        ]

        selected, _, _ = select_messages(registry, messages, selection)

        self.assertEqual(selection["family_ids"], ["b"])
        self.assertEqual(selected["b"]["message_id"], "om_b")

    def test_explicit_message_binding_does_not_float_to_a_newer_message(self) -> None:
        registry = {
            "families": [{"id": "a", "source_filename_patterns": ["^a\\.xlsx$"]}],
            "upload_order": ["a"],
        }
        selection = build_selection_spec(
            registry,
            family_ids=["a"],
            explicit_message_specs=["a=om_old"],
        )
        messages = [
            {"message_id": "om_old", "file_name": "a.xlsx", "create_time": "1000"},
            {"message_id": "om_new", "file_name": "a.xlsx", "create_time": "2000"},
        ]

        selected, _, _ = select_messages(registry, messages, selection)

        self.assertEqual(selected["a"]["message_id"], "om_old")

    def test_after_cutoff_is_strict(self) -> None:
        registry = {
            "families": [{"id": "a", "source_filename_patterns": ["^a\\.xlsx$"]}],
            "upload_order": ["a"],
        }
        selection = build_selection_spec(registry, family_ids=["a"], after="1970-01-01T00:00:01Z")
        messages = [
            {"message_id": "om_equal", "file_name": "a.xlsx", "create_time": "1000"},
            {"message_id": "om_after", "file_name": "a.xlsx", "create_time": "2000"},
        ]

        selected, _, _ = select_messages(registry, messages, selection)

        self.assertEqual(selected["a"]["message_id"], "om_after")


if __name__ == "__main__":
    unittest.main()
