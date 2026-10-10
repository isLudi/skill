"""Synthetic fixtures only: monthly TT coverage and financial merge invariants."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from assemble_monthly_cashflow import KEYS, TEMPLATE, TT_MISSING_COLUMNS, assemble


COLUMNS = [item["name"] for item in json.loads(TEMPLATE.read_text(encoding="utf-8"))["columns"]]


def event(order="900000000000000001", *, tt=False, **changes):
    row = dict.fromkeys(COLUMNS, "")
    row.update(dt="20260901", trade_timestamp="2026-09-01 12:00:00", order_timestamp="2026-09-01 12:00:00",
               order_number=order, original_order_number=order, user_number="001234",
               course_number="800000000000000001", course_name='测试"课程"',
               course_first_level_department_name="TT" if tt else "H业务线",
               course_second_level_department_name="TT小学学部" if tt else "精品班学部",
               performance_employee_id="0123", performance_second_level_department_name="青橙项目部",
               income_yuan="10.00", refund_yuan="0.00", gross_profit_yuan="10.00",
               stat_judge_type="1", biz_type="7", goods_type="2")
    row.update(changes)
    return row


class MonthlyCashflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="qingcheng-cashflow-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def run_assembly(self, base, tt, *, labels=None, zero_verified=False):
        finance, lookup, supplement = [self.root / name for name in ["finance.csv", "labels.csv", "tt.csv"]]
        pd.DataFrame(base, columns=[c for c in COLUMNS if c != "stat_judge_type"]).to_csv(finance, index=False)
        pd.DataFrame(labels if labels is not None else base, columns=KEYS + ["stat_judge_type"]).to_csv(lookup, index=False)
        pd.DataFrame(tt, columns=[c for c in COLUMNS if c not in TT_MISSING_COLUMNS]).to_csv(supplement, index=False)
        output = self.root / "result.csv"
        qa = assemble(finance, lookup, output, self.root / "qa.json", tt_supplement=supplement,
                      start_date="2026-09-01", end_date="2026-09-30", tt_zero_verified=zero_verified)
        return pd.read_csv(output, dtype=str, keep_default_na=False), qa

    def test_tt_is_appended_with_exact_ids_and_explicit_missing_codes(self):
        result, qa = self.run_assembly([event()], [event("900000000000000002", tt=True)])
        self.assertEqual(list(result), COLUMNS)
        self.assertEqual(result.order_number.tolist(), ["900000000000000001", "900000000000000002"])
        self.assertEqual(result.user_number.tolist(), ["001234", "001234"])
        self.assertEqual(result.iloc[1][TT_MISSING_COLUMNS].tolist(), ["", ""])
        self.assertEqual(qa["totals"]["gross_profit_yuan"], "20.00")
        self.assertTrue(qa["tt_source_checked"])
        self.assertFalse(qa["full_population_confirmed"])

    def test_existing_tt_is_skipped_but_new_refund_on_same_order_is_kept(self):
        paid = event(tt=True)
        refund = event(tt=True, dt="20260902", trade_timestamp="2026-09-02 12:00:00",
                       income_yuan="0", refund_yuan="4.00", gross_profit_yuan="-4.00")
        result, qa = self.run_assembly([paid], [paid, refund])
        self.assertEqual(len(result), 2)
        self.assertEqual(qa["tt_overlap_rows_skipped"], 1)
        self.assertEqual(qa["tt_rows_added"], 1)
        self.assertEqual(result.iloc[0].biz_type, "7")
        self.assertEqual(qa["totals"]["gross_profit_yuan"], "6.00")

    def test_same_event_changed_money_course_or_attribution_is_rejected(self):
        for changes in [dict(income_yuan="20", gross_profit_yuan="20"),
                        dict(course_number="800000000000000099"),
                        dict(performance_employee_id="0999")]:
            with self.subTest(changes=changes):
                with self.assertRaisesRegex(ValueError, "Conflicting TT event"):
                    self.run_assembly([event(tt=True)], [event(tt=True, **changes)])
                self.assertFalse((self.root / "result.csv").exists())

    def test_split_multiplicity_cannot_be_silently_collapsed(self):
        with self.assertRaisesRegex(ValueError, "Conflicting TT event"):
            self.run_assembly([event(tt=True), event(tt=True)], [event(tt=True)])

    def test_unknown_tt_department_requires_scope_review(self):
        with self.assertRaisesRegex(ValueError, "unreviewed department"):
            self.run_assembly([event()], [event("other", tt=True, course_second_level_department_name="新学部")])

    def test_period_and_net_amount_must_match_contract(self):
        for changes, message in [(dict(dt="20261001", trade_timestamp="2026-10-01 00:00:00"), "outside"),
                                 (dict(gross_profit_yuan="1"), "Net cash"),
                                 (dict(dt="20261008"), "snapshot dt")]:
            with self.subTest(changes=changes):
                with self.assertRaisesRegex(ValueError, message):
                    self.run_assembly([event()], [event("other", tt=True, **changes)])

    def test_stat_conflict_rejected_and_unmatched_stays_blank(self):
        labels = [event(), event(stat_judge_type="2")]
        with self.assertRaisesRegex(ValueError, "Conflicting stat_judge_type"):
            self.run_assembly([event()], [event("other", tt=True)], labels=labels)
        result, qa = self.run_assembly([event()], [event("other", tt=True)], labels=[])
        self.assertEqual(result.iloc[0].stat_judge_type, "")
        self.assertEqual(qa["stat_unmatched_rows"], 1)

    def test_empty_tt_is_not_implicitly_treated_as_no_business(self):
        with self.assertRaisesRegex(ValueError, "success_empty_verified"):
            self.run_assembly([event()], [])
        result, qa = self.run_assembly([event()], [], zero_verified=True)
        self.assertEqual(len(result), 1)
        self.assertTrue(qa["tt_zero_verified_assertion"])

    def test_standard_tt_csv_keeps_literal_backslash_and_quotes(self):
        name = '语文\\写作"强化"'
        result, _ = self.run_assembly([event()], [event("other", tt=True, course_name=name)])
        self.assertEqual(result.iloc[1].course_name, name)


if __name__ == "__main__":
    unittest.main()
