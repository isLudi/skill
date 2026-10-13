from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('market_sql_rules_under_test', ROOT / 'scripts' / 'validate_sql_rules.py')
rules = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = rules
SPEC.loader.exec_module(rules)
TABLE = 'demo.hourly_leads'
KNOWLEDGE = {TABLE: rules.TableKnowledge(TABLE, {'lead_id', 'dt', 'hour', 'department_name', 'channel_name', 'qty'}, {'dt', 'hour'}, True, {'department_name'})}
FILTER = "t.dt = '20261009' and t.hour = '12'"


class MarketScopeValidationTests(unittest.TestCase):
    def validate(self, sql: str, exploratory: bool = False) -> list[str]:
        with patch.object(rules, 'load_knowledge', return_value=KNOWLEDGE):
            return rules.validate(sql, exploratory)

    def test_window_select_is_not_compared_with_later_cte_group(self) -> None:
        sql = f"with raw as (select t.lead_id,t.channel_name,sum(t.qty) over(partition by t.lead_id) as n from {TABLE} t where {FILTER}) select channel_name,count(*) from raw group by channel_name"
        self.assertEqual(self.validate(sql), [])

    def test_distinct_select_is_not_compared_with_outer_group(self) -> None:
        sql = f"with raw as (select distinct t.lead_id,t.channel_name from {TABLE} t where {FILTER}) select channel_name,count(*) from raw group by channel_name"
        self.assertEqual(self.validate(sql), [])

    def test_department_filter_is_checked_in_its_own_cte(self) -> None:
        sql = f"with raw as (select t.department_name from {TABLE} t where {FILTER} and t.department_name='市场部') select * from raw"
        self.assertEqual(self.validate(sql), [])

    def test_outer_department_filter_cannot_cover_unfiltered_scan(self) -> None:
        sql = f"with raw as (select t.department_name from {TABLE} t where {FILTER}) select * from raw where department_name='市场部'"
        self.assertIn('涉及 department_name 字段但未过滤：t.department_name', self.validate(sql))

    def test_alias_reuse_cannot_borrow_other_cte_partition(self) -> None:
        sql = f"with a as (select t.lead_id from {TABLE} t where {FILTER}), b as (select t.lead_id from {TABLE} t where t.hour='12') select * from a join b on a.lead_id=b.lead_id"
        self.assertIn(f'分区表遗漏 dt 条件：{TABLE} alias t', self.validate(sql))

    def test_join_alias_cannot_borrow_another_tables_filter(self) -> None:
        sql = f"select a.lead_id,b.lead_id from {TABLE} a join {TABLE} b on a.lead_id=b.lead_id where a.dt='20261009' and a.hour='12'"
        self.assertIn(f'分区表遗漏 dt 条件：{TABLE} alias b', self.validate(sql))

    def test_nested_alias_cannot_cover_outer_partition(self) -> None:
        sql = f"select t.lead_id from {TABLE} t where t.hour='12' and exists (select 1 from {TABLE} t where {FILTER})"
        self.assertIn(f'分区表遗漏 dt 条件：{TABLE} alias t', self.validate(sql))

    def test_actual_missing_group_field_is_still_rejected(self) -> None:
        sql = f"select t.channel_name,t.lead_id,count(*) from {TABLE} t where {FILTER} group by t.channel_name"
        self.assertTrue(any('t.lead_id' in issue and '未分组' in issue for issue in self.validate(sql)))

    def test_column_added_to_aggregate_expression_is_rejected(self) -> None:
        sql = f"select t.channel_name,sum(t.qty)+t.lead_id from {TABLE} t where {FILTER} group by t.channel_name"
        self.assertTrue(any('未分组' in issue for issue in self.validate(sql)))

    def test_aggregate_without_group_cannot_select_plain_column(self) -> None:
        sql = f"select t.channel_name,count(*) from {TABLE} t where {FILTER}"
        self.assertTrue(any('未分组' in issue for issue in self.validate(sql)))

    def test_ordinal_and_alias_groups_are_valid(self) -> None:
        for group in ['1', 'channel', 't.channel_name']:
            sql = f"select t.channel_name as channel,count(*) from {TABLE} t where {FILTER} group by {group}"
            self.assertEqual(self.validate(sql), [], group)

    def test_expression_of_grouped_column_is_valid(self) -> None:
        sql = f"select coalesce(t.channel_name,'未知'),count(*) from {TABLE} t where {FILTER} group by t.channel_name"
        self.assertEqual(self.validate(sql), [])

    def test_window_over_grouped_aggregate_is_valid(self) -> None:
        sql = f"select t.channel_name,sum(sum(t.qty)) over(partition by t.channel_name) from {TABLE} t where {FILTER} group by t.channel_name"
        self.assertEqual(self.validate(sql), [])

    def test_window_cannot_read_ungrouped_column_after_group(self) -> None:
        sql = f"select t.channel_name,sum(t.qty) over(partition by t.channel_name),count(*) from {TABLE} t where {FILTER} group by t.channel_name"
        self.assertTrue(any('未分组' in issue for issue in self.validate(sql)))

    def test_unknown_table_and_qualified_field_are_rejected(self) -> None:
        self.assertIn('表未出现在知识库：demo.unknown', self.validate('select x.lead_id from demo.unknown x'))
        sql = f"select t.unknown_field from {TABLE} t where {FILTER}"
        self.assertIn(f'字段未出现在知识库：t.unknown_field -> {TABLE}', self.validate(sql))

    def test_cte_field_alias_is_not_mistaken_for_physical_field(self) -> None:
        sql = f"with c as (select t.qty as renamed from {TABLE} t where {FILTER}) select c.renamed from c"
        self.assertEqual(self.validate(sql), [])

    def test_date_add_and_numeric_string_gates_remain(self) -> None:
        self.assertTrue(any('三参数' in issue for issue in self.validate("select date_add('day',1,timestamp '2026-10-09 00:00:00')")))
        self.assertTrue(any('字符串数字混用' in issue for issue in self.validate("select 1 as lead_count where lead_count='1'")))

    def test_exploration_requires_outer_limit(self) -> None:
        self.assertIn('探索型查询遗漏 limit', self.validate('with a as (select 1 limit 1) select * from a', True))
        self.assertEqual(self.validate('select 1 limit 1', True), [])

    def test_no_star_in_grouped_projection(self) -> None:
        sql = f"select t.*,count(*) from {TABLE} t where {FILTER} group by t.lead_id"
        self.assertTrue(any('未分组' in issue for issue in self.validate(sql)))


if __name__ == '__main__':
    unittest.main()
