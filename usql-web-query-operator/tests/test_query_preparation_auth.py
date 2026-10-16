from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from _shared.errors import UsageError
from usql_web_query.cli import build_parser
from usql_web_query.commands.run import cmd_run
from usql_web_query.query_auth import query_credentials, verify_query_identity
from usql_web_query.query_contract import exact_sql_sha256, load_query_plan_contract
from usql_web_query.sql_utils import enforce_query_prefix, prepare_query_sql


class QueryPreparationAuthTests(unittest.TestCase):
    def test_only_prefix_removed_literals_and_internal_comments_preserved(self):
        statement = "SELECT '--not comment', '/*literal*/' /* keep */ AS x\nLIMIT 1\n"
        self.assertEqual(prepare_query_sql(" \n-- explanation\r\n/* outer /* nested */ end */\n" + statement), statement)
        self.assertEqual(prepare_query_sql("\ufeff-- explanation\nSELECT 1"), "SELECT 1")
        self.assertEqual(prepare_query_sql(statement), statement)

    def test_hints_incomplete_comments_and_empty_input_fail(self):
        for sql in ("/*+ hint */ SELECT 1", "/*! directive */ SELECT 1", "--+ hint\nSELECT 1", "--! directive\nSELECT 1", "/* open", "-- only", "/* only */ ", " "):
            with self.subTest(sql=sql), self.assertRaises(UsageError):
                prepare_query_sql(sql)

    def test_prepare_preserves_source_and_does_not_rebind_old_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, output = root / "source.sql", root / "prepared.sql"
            original = "-- note\nSELECT 1 LIMIT 1\n"
            source.write_text(original, encoding="utf-8")
            args = build_parser().parse_args(["prepare-sql", "--sql-file", str(source), "--output", str(output)])
            with patch("builtins.print"):
                self.assertEqual(args.func(args), 0)
            self.assertEqual(source.read_text(encoding="utf-8"), original)
            self.assertEqual(output.read_text(encoding="utf-8"), "SELECT 1 LIMIT 1\n")
            with self.assertRaises(UsageError):
                args.func(args)
            plan = root / "plan.json"
            plan.write_text(json.dumps({"schema_version": "2.0.0", "domain": "market_consultant", "status": "executable", "unresolved_slots": [], "diagnostics": [], "sql_sha256": exact_sql_sha256(original)}), encoding="utf-8")
            with self.assertRaisesRegex(UsageError, "exact SQL"):
                load_query_plan_contract(plan, output.read_text(encoding="utf-8"))

    def test_run_prefix_fails_before_browser_and_never_rewrites_source(self):
        with self.assertRaisesRegex(UsageError, "prepare-sql"):
            enforce_query_prefix("\ufeff -- note\nSELECT 1")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "source.sql"
            sql = "-- note\nSELECT 1 LIMIT 1"
            path.write_text(sql, encoding="utf-8")
            args = build_parser().parse_args(["run", "--sql-file", str(path)])
            with patch("usql_web_query.commands.run.import_playwright") as launch:
                with self.assertRaisesRegex(UsageError, "prepare-sql"):
                    cmd_run(args)
                launch.assert_not_called()
            self.assertEqual(path.read_text(encoding="utf-8"), sql)

    def test_exact_credential_section_wins_over_other_section_and_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.env"
            path.write_text("# tiangong2 Web Query (Playwright) credentials\nBAIJIA_USERNAME=other\nBAIJIA_PASSWORD=other-secret\n# USQL Web Query (Playwright) credentials\nBAIJIA_USERNAME=expected\nBAIJIA_PASSWORD=expected-secret\n", encoding="utf-8")
            with patch.dict(os.environ, {"BAIJIA_USERNAME": "stale", "BAIJIA_PASSWORD": "stale-secret"}):
                self.assertEqual(query_credentials(path), ("expected", "expected-secret"))
                self.assertEqual(query_credentials(path, "explicit", "explicit-secret"), ("explicit", "explicit-secret"))
            path.write_text("BAIJIA_USERNAME=wrong\nBAIJIA_PASSWORD=wrong-secret\n", encoding="utf-8")
            with self.assertRaises(UsageError):
                query_credentials(path)

    def test_identity_match_mismatch_and_missing_are_checked(self):
        def page(payload):
            response = SimpleNamespace(ok=True, json=lambda: payload)
            return SimpleNamespace(context=SimpleNamespace(request=SimpleNamespace(get=lambda *a, **kw: response)))
        self.assertTrue(verify_query_identity(page({"status": "success", "errorCode": 0, "data": {"name": "Expected"}}), "expected")["verified"])
        for payload in ({"data": {"name": "wrong"}}, {"data": {}}, {"status": "error", "data": {"name": "expected"}}):
            with self.assertRaises(UsageError):
                verify_query_identity(page(payload), "expected")


if __name__ == "__main__":
    unittest.main()
