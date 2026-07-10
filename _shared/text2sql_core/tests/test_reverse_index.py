from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


CORE_ROOT = Path(__file__).resolve().parents[1]

import sys

sys.path.insert(0, str(CORE_ROOT))

from text2sql_core.reverse_index import (  # noqa: E402
    ReverseIndexBuilder,
    build_reverse_indexes,
    main_for_skill,
)


class ReverseIndexTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.skill_root = Path(self.temp_dir.name) / "domain-skill"
        for relative in (
            "knowledge/tables",
            "knowledge/dashboards",
            "knowledge/metrics",
            "knowledge/joins",
            "knowledge/reverse_index",
            "resources/raw_sql",
        ):
            (self.skill_root / relative).mkdir(parents=True, exist_ok=True)
        (self.skill_root / "knowledge/tables/service_dw.fact_df.md").write_text(
            "# service_dw.fact_df\n",
            encoding="utf-8",
        )
        (self.skill_root / "resources/raw_sql/real_query.sql").write_text(
            "select * from service_dw.fact_df",
            encoding="utf-8",
        )
        (self.skill_root / "knowledge/dashboards/dashboard.md").write_text(
            "# Dashboard\n\n"
            "Uses `service_dw.fact_df` and resources/raw_sql/real_query.sql.\n"
            "The historical placeholder `_20260705.sql` does not exist.\n",
            encoding="utf-8",
        )
        (self.skill_root / "knowledge/metrics/metric.md").write_text(
            "\ufeff# Metric Title\n\n"
            "Field `amount`, table `service_dw.fact_df`, source `real_query.sql`.\n",
            encoding="utf-8",
        )
        (self.skill_root / "knowledge/joins/risks.md").write_text(
            "# Join Risk\n\n- join may cause duplicate rows and risk.\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_render_is_deterministic_and_uses_only_existing_raw_sql(self) -> None:
        builder = ReverseIndexBuilder(self.skill_root)
        first = builder.render()
        second = builder.render()
        self.assertEqual(first, second)
        combined = "\n".join(first.values())
        self.assertIn("real_query.sql", combined)
        self.assertNotIn("_20260705.sql", combined)
        self.assertIn("[Metric Title]", first["metric_to_raw_sql.md"])

    def test_check_is_read_only_and_detects_stale_output(self) -> None:
        with redirect_stdout(io.StringIO()):
            self.assertEqual(0, build_reverse_indexes(self.skill_root))
        target = self.skill_root / "knowledge/reverse_index/field_to_metrics.md"
        target.write_text("stale\n", encoding="utf-8")
        before = target.read_bytes()
        with redirect_stdout(io.StringIO()):
            result = build_reverse_indexes(self.skill_root, check=True)
        self.assertEqual(1, result)
        self.assertEqual(before, target.read_bytes())

    def test_legacy_no_argument_cli_and_check(self) -> None:
        with redirect_stdout(io.StringIO()):
            self.assertEqual(0, main_for_skill(self.skill_root, []))
            self.assertEqual(0, main_for_skill(self.skill_root, ["--check"]))
        first = {
            path.name: path.read_bytes()
            for path in (self.skill_root / "knowledge/reverse_index").glob("*.md")
        }
        with redirect_stdout(io.StringIO()):
            self.assertEqual(0, main_for_skill(self.skill_root, []))
        second = {
            path.name: path.read_bytes()
            for path in (self.skill_root / "knowledge/reverse_index").glob("*.md")
        }
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
