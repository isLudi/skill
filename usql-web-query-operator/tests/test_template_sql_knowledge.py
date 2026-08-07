from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from _shared.errors import UsageError  # noqa: E402
from usql_web_query.data_center_replacement import (  # noqa: E402
    canonical_sql_text,
    sql_sha256,
)
from usql_web_query.template_permanent import (  # noqa: E402
    canonical_template_sql,
    template_sql_sha256,
)
from usql_web_query.template_query import (  # noqa: E402
    canonical_template_sql_text,
    template_sql_sha256 as fetched_template_sql_sha256,
)
from usql_web_query.template_sql_knowledge import (  # noqa: E402
    apply_template_sql_plan,
    combined_plan_sha256,
    plan_template_sql_sync,
    resolve_template_canonical_path,
)


def template(*, template_id: int = 9002, status: int = 2, sql: str = "select 1\r\n") -> SimpleNamespace:
    return SimpleNamespace(
        id=template_id,
        name="AI分析市场顾问部_宽表",
        status=status,
        update_time="2026-08-07 19:09:55",
        publish_time="2026-08-07 19:09:55",
        sql_detail=sql,
    )


class TemplateSqlKnowledgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name) / "market-consultant-dashboard-sql"
        (root / "resources/raw_sql").mkdir(parents=True)
        (root / "knowledge/update_log").mkdir(parents=True)
        (root / "knowledge/update_log/changelog.md").write_text("# Log\n", encoding="utf-8")
        self.target = SimpleNamespace(
            target="market",
            domain_id="market_consultant",
            skill_root=root,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_template_save_hash_matches_data_center_canonicalization(self) -> None:
        for sql in ("select 1\r\n\r\n", "\ufeffselect 1\r\n", "select 1  \n"):
            self.assertEqual(canonical_sql_text(sql), canonical_template_sql(sql))
            self.assertEqual(canonical_sql_text(sql), canonical_template_sql_text(sql))
            self.assertEqual(sql_sha256(sql), template_sql_sha256(sql))
            self.assertEqual(sql_sha256(sql), fetched_template_sql_sha256(sql))

    def test_only_stable_template_filename_is_accepted(self) -> None:
        stable = resolve_template_canonical_path(
            self.target,
            Path("resources/raw_sql/template_query_market_wide.sql"),
        )
        self.assertEqual("template_query_market_wide.sql", stable.name)
        with self.assertRaisesRegex(UsageError, "date-suffixed"):
            resolve_template_canonical_path(
                self.target,
                Path("resources/raw_sql/template_query_market_wide_20260807.sql"),
            )

    def test_plan_binds_live_hash_and_detects_dated_legacy_files(self) -> None:
        legacy = self.target.skill_root / "resources/raw_sql/template_query_market_wide_20260806.sql"
        legacy.write_text("select 0\n", encoding="utf-8")
        plan = plan_template_sql_sync(
            self.target,
            template(),
            canonical_file=Path("resources/raw_sql/template_query_market_wide.sql"),
            run_date=date(2026, 8, 7),
        )
        self.assertEqual("ready", plan.status)
        self.assertEqual(hashlib.sha256(b"select 1\n").hexdigest(), plan.remote_sql_sha256)
        self.assertEqual([legacy], [item.path for item in plan.legacy_files])
        self.assertEqual("resources/raw_sql/template_query_market_wide.sql", plan.to_json()["canonical_sql_file"])
        self.assertNotIn("select 0", plan.to_json().__repr__())

    def test_apply_requires_exact_plan_hash_and_removes_legacy_code(self) -> None:
        legacy = self.target.skill_root / "resources/raw_sql/template_query_market_wide_20260806.sql"
        legacy.write_text("select 0\n", encoding="utf-8")
        plan = plan_template_sql_sync(
            self.target,
            template(),
            canonical_file=Path("resources/raw_sql/template_query_market_wide.sql"),
            run_date=date(2026, 8, 7),
        )
        with self.assertRaisesRegex(UsageError, "plan hash mismatch"):
            apply_template_sql_plan(plan, expected_plan_sha256="wrong")
        self.assertTrue(legacy.exists())
        with patch("usql_web_query.template_sql_knowledge.run_mandatory_maintenance", return_value=[]):
            receipt = apply_template_sql_plan(plan, expected_plan_sha256=combined_plan_sha256([plan]))
        stable = self.target.skill_root / "resources/raw_sql/template_query_market_wide.sql"
        self.assertEqual("select 1\n", stable.read_text(encoding="utf-8"))
        self.assertFalse(legacy.exists())
        self.assertTrue(receipt.fully_verified)

    def test_unpublished_template_is_blocked(self) -> None:
        plan = plan_template_sql_sync(
            self.target,
            template(status=1),
            canonical_file=Path("resources/raw_sql/template_query_market_wide.sql"),
            run_date=date(2026, 8, 7),
        )
        self.assertEqual("blocked", plan.status)
        with self.assertRaisesRegex(UsageError, "published"):
            apply_template_sql_plan(plan, expected_plan_sha256=combined_plan_sha256([plan]))


if __name__ == "__main__":
    unittest.main()
