from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from validate_sql_rules import TableKnowledge, validate  # noqa: E402


TABLE = "demo.hourly_leads"
KNOWLEDGE = {
    TABLE: TableKnowledge(
        full_name=TABLE,
        fields={"lead_id", "dt", "hour", "department_name", "channel_name"},
        partitions={"dt", "hour"},
        has_hour=True,
        scope_fields={"department_name"},
    )
}


class AstAwareScopeValidationTests(unittest.TestCase):
    def validate_with_fixture(self, sql: str) -> list[str]:
        with patch("validate_sql_rules.load_knowledge", return_value=KNOWLEDGE):
            return validate(sql)

    def test_cte_internal_filters_satisfy_physical_table_scope(self) -> None:
        sql = """
        with scoped as (
            select distinct
                t.lead_id,
                t.department_name,
                t.channel_name
            from demo.hourly_leads t
            where t.dt = '20260710'
              and t.hour = '10'
              and t.department_name = '青橙项目部'
        )
        select department_name, count(*) as lead_count
        from scoped
        group by department_name
        """

        self.assertEqual(self.validate_with_fixture(sql), [])

    def test_select_distinct_is_not_compared_with_outer_group_by(self) -> None:
        sql = """
        with scoped as (
            select distinct t.lead_id, t.channel_name
            from demo.hourly_leads t
            where t.dt = '20260710' and t.hour = '10'
        )
        select channel_name, count(*) as lead_count
        from scoped
        group by channel_name
        """

        issues = self.validate_with_fixture(sql)

        self.assertFalse(any("group by 可能不完整" in issue for issue in issues), issues)

    def test_missing_filter_inside_owner_cte_is_reported(self) -> None:
        sql = """
        with scoped as (
            select t.lead_id, t.department_name
            from demo.hourly_leads t
            where t.dt = '20260710' and t.hour = '10'
        )
        select * from scoped where department_name = '青橙项目部'
        """

        issues = self.validate_with_fixture(sql)

        self.assertIn("涉及范围字段但未过滤：t.department_name", issues)

    def test_missing_partition_filter_is_reported_per_cte(self) -> None:
        sql = """
        with scoped as (
            select t.lead_id
            from demo.hourly_leads t
            where t.hour = '10'
        )
        select * from scoped
        """

        issues = self.validate_with_fixture(sql)

        self.assertIn(f"分区表遗漏 dt 条件：{TABLE} alias t", issues)

    def test_group_by_check_stays_inside_one_select(self) -> None:
        sql = """
        select t.channel_name, t.lead_id, count(*) as lead_count
        from demo.hourly_leads t
        where t.dt = '20260710' and t.hour = '10'
        group by t.channel_name
        """

        issues = self.validate_with_fixture(sql)

        self.assertTrue(any("t.lead_id" in issue for issue in issues), issues)

    def test_canonical_2064_has_no_cte_scope_or_distinct_false_positives(self) -> None:
        sql = (
            SKILL_ROOT
            / "resources"
            / "raw_sql"
            / "data_center_qingcheng_2064_20260625.sql"
        ).read_text(encoding="utf-8")

        issues = validate(sql)

        false_positive_markers = (
            "涉及范围字段但未过滤",
            "SQL 涉及疑似部门/项目范围字段",
            "分区表遗漏 dt 条件",
            "小时表建议补充 hour 条件",
            "group by 可能不完整",
        )
        self.assertFalse(
            any(marker in issue for marker in false_positive_markers for issue in issues),
            issues,
        )


if __name__ == "__main__":
    unittest.main()
