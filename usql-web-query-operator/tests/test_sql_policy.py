from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from _shared.errors import UsageError  # noqa: E402
from usql_web_query.commands.run import cmd_run  # noqa: E402
from usql_web_query.sql_policy import PolicyBudgets, analyze_sql_policy  # noqa: E402


class SqlPolicyTests(unittest.TestCase):
    def test_select_and_with_queries_are_allowed(self) -> None:
        for sql in ("select 1 limit 1", "with x as (select 1) select * from x limit 1"):
            with self.subTest(sql=sql):
                report = analyze_sql_policy(sql, require_limit=True)
                self.assertTrue(report["allowed"], report)
                self.assertEqual(report["counts"]["statements"], 1)

    def test_ddl_dml_and_multiple_statements_are_hard_blocked(self) -> None:
        cases = (
            "delete from example_table",
            "insert into example_table select 1",
            "create table example_table as select 1",
            "select 1; select 2",
        )
        for sql in cases:
            with self.subTest(sql=sql):
                report = analyze_sql_policy(sql)
                self.assertFalse(report["allowed"])
                self.assertTrue(any(item["hard_block"] for item in report["diagnostics"]))
                self.assertFalse(analyze_sql_policy(sql, mode="audit")["allowed"])

    def test_complexity_is_warning_in_audit_and_error_in_enforce(self) -> None:
        sql = "select * from a join b on a.id = b.id"
        budgets = PolicyBudgets(joins=0)
        self.assertTrue(analyze_sql_policy(sql, mode="audit", budgets=budgets)["allowed"])
        self.assertFalse(analyze_sql_policy(sql, mode="enforce", budgets=budgets)["allowed"])

    def test_explicit_partition_and_limit_requirements_are_checked(self) -> None:
        blocked = analyze_sql_policy("select 1", required_partition_fields=["dt"], require_limit=True)
        codes = {item["code"] for item in blocked["diagnostics"]}
        self.assertIn("REQUIRED_PARTITION_FILTER_MISSING", codes)
        self.assertIn("LIMIT_REQUIRED", codes)
        allowed = analyze_sql_policy(
            "select * from example_table where dt = '20260802' limit 10",
            required_partition_fields=["dt"],
            require_limit=True,
        )
        self.assertTrue(allowed["allowed"], allowed)

    def test_unsafe_sql_stops_before_playwright_import(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            sql_path = root / "unsafe.sql"
            sql_path.write_text("drop table example_table", encoding="utf-8")
            args = SimpleNamespace(
                env_file=None,
                sql_file=sql_path,
                query_plan=None,
                download=False,
                state_path=root / "state.json",
                artifacts_dir=root / "artifacts",
                policy_mode="enforce",
                policy_report=None,
                required_partition_field=[],
                require_limit=False,
            )
            with patch("usql_web_query.commands.run.import_playwright") as browser_import:
                with self.assertRaisesRegex(UsageError, "SQL policy blocked"):
                    cmd_run(args)
            browser_import.assert_not_called()
            self.assertEqual(len(list((root / "artifacts").rglob("sql_policy_report.json"))), 1)


if __name__ == "__main__":
    unittest.main()
