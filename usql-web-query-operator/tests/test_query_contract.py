from __future__ import annotations

import json
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
from usql_web_query.cli import build_parser  # noqa: E402
from usql_web_query.commands.run import cmd_run  # noqa: E402
from usql_web_query.models import RunSummary  # noqa: E402
from usql_web_query.query_contract import (  # noqa: E402
    enforce_query_plan_download_policy,
    exact_sql_sha256,
    load_query_plan_contract,
)


class QueryPlanContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.sql = "select 1 as value\nlimit 10;\n"

    def write_plan(self, **overrides: object) -> Path:
        payload: dict[str, object] = {
            "schema_version": "2.0.0",
            "domain": "market_consultant",
            "status": "executable",
            "unresolved_slots": [],
            "diagnostics": [],
            "sql_sha256": exact_sql_sha256(self.sql),
            "execution_policy": {
                "allow_download": False,
                "max_direct_download_rows": 1000,
                "requires_preview": True,
                "execution_mode": "production",
            },
        }
        payload.update(overrides)
        path = self.root / "query_plan.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_valid_plan_loads_and_returns_compact_summary(self) -> None:
        path = self.write_plan(
            execution_policy={
                "allow_download": True,
                "max_direct_download_rows": 1000,
                "requires_preview": True,
                "execution_mode": "production",
            }
        )

        contract = load_query_plan_contract(path, self.sql)

        self.assertEqual(contract.domain, "market_consultant")
        self.assertTrue(contract.allow_download)
        summary = contract.to_summary()
        self.assertEqual(summary["schema_version"], "2.0.0")
        self.assertEqual(summary["sql_sha256"], exact_sql_sha256(self.sql))
        self.assertNotIn("max_direct_download_rows", summary)

    def test_hash_mismatch_is_rejected(self) -> None:
        path = self.write_plan(sql_sha256="0" * 64)

        with self.assertRaisesRegex(UsageError, "does not match the exact SQL"):
            load_query_plan_contract(path, self.sql)

    def test_schema_and_domain_are_strict(self) -> None:
        with self.assertRaisesRegex(UsageError, "schema_version must be"):
            load_query_plan_contract(self.write_plan(schema_version="1.0.0"), self.sql)

        with self.assertRaisesRegex(UsageError, "domain must be one of"):
            load_query_plan_contract(self.write_plan(domain="shared_physical"), self.sql)

    def test_unresolved_plan_is_rejected(self) -> None:
        path = self.write_plan(unresolved_slots=["department_scope"])

        with self.assertRaisesRegex(UsageError, "unresolved_slots must be empty"):
            load_query_plan_contract(path, self.sql)

    def test_non_executable_plan_is_rejected(self) -> None:
        path = self.write_plan(status="needs_clarification")

        with self.assertRaisesRegex(UsageError, "status must be 'executable'"):
            load_query_plan_contract(path, self.sql)

    def test_download_requires_explicit_contract_permission(self) -> None:
        contract = load_query_plan_contract(self.write_plan(), self.sql)

        with self.assertRaisesRegex(UsageError, "allow_download must be true"):
            enforce_query_plan_download_policy(contract, download=True)

        enforce_query_plan_download_policy(contract, download=False)

    def test_execution_policy_is_required(self) -> None:
        path = self.write_plan(execution_policy=None)

        with self.assertRaisesRegex(UsageError, "execution_policy must exist"):
            load_query_plan_contract(path, self.sql)

    def test_execution_policy_safety_fields_are_strict(self) -> None:
        base = {
            "allow_download": False,
            "max_direct_download_rows": 1000,
            "requires_preview": True,
            "execution_mode": "production",
        }
        for key, value, message in (
            ("max_direct_download_rows", 1001, "max_direct_download_rows"),
            ("requires_preview", False, "requires_preview"),
            ("execution_mode", "unsafe", "execution_mode"),
        ):
            with self.subTest(key=key):
                policy = dict(base)
                policy[key] = value
                with self.assertRaisesRegex(UsageError, message):
                    load_query_plan_contract(self.write_plan(execution_policy=policy), self.sql)

    def test_error_diagnostics_are_rejected(self) -> None:
        path = self.write_plan(diagnostics=[{"severity": "error", "code": "BLOCKED"}])

        with self.assertRaisesRegex(UsageError, "must not contain error"):
            load_query_plan_contract(path, self.sql)

    def test_run_parser_accepts_query_plan(self) -> None:
        sql_path = self.root / "query.sql"
        plan_path = self.root / "query_plan.json"
        args = build_parser().parse_args(
            ["run", "--sql-file", str(sql_path), "--query-plan", str(plan_path)]
        )

        self.assertEqual(args.sql_file, sql_path)
        self.assertEqual(args.query_plan, plan_path)
        self.assertFalse(args.download)

    def test_invalid_contract_stops_before_playwright_import(self) -> None:
        sql_path = self.root / "query.sql"
        sql_path.write_text(self.sql, encoding="utf-8")
        plan_path = self.write_plan(sql_sha256="0" * 64)
        args = SimpleNamespace(
            env_file=None,
            sql_file=sql_path,
            query_plan=plan_path,
            download=False,
        )

        with patch("usql_web_query.commands.run.import_playwright") as import_playwright:
            with self.assertRaisesRegex(UsageError, "does not match the exact SQL"):
                cmd_run(args)
        import_playwright.assert_not_called()

    def test_legacy_run_summary_omits_contract_field(self) -> None:
        payload = json.loads(
            RunSummary(ok=True, status="Success", message="done", artifacts_dir="runtime").to_json()
        )

        self.assertNotIn("query_plan_contract", payload)


if __name__ == "__main__":
    unittest.main()
