import unittest

from prepare_monthly_cashflow_queries import build_manifest, prepare, scope_hash


class MonthlyQueryPreparationTests(unittest.TestCase):
    def setUp(self):
        self.scopes = {"goods_first": ["H业务线"], "goods_second": ["青橙项目部"],
                       "course_first": ["H业务线", "TT"], "course_second": ["青橙项目部", "V学部"],
                       "scope_evidence": {"source": "reviewed current permission response"}}

    def counts(self):
        return {name: {"row_count": count, "query_id": str(100 + count),
                       "start_date": "2026-10-01", "end_date": "2026-10-31",
                       "snapshot_dt": "20261104", "snapshot_hour": "23",
                       "scope_sha256": scope_hash(self.scopes)}
                for name, count in [("finance", 2000), ("lookup", 1900), ("tt", 0)]}

    def build(self, **kwargs):
        args = dict(start_date="2026-10-01", end_date="2026-10-31", snapshot_dt="20261104",
                    snapshot_hour="23", scopes=self.scopes)
        args.update(kwargs)
        return prepare(**args)

    def test_controls_only_until_counts_are_verified(self):
        output = self.build()
        self.assertEqual(set(output), {"finance_control.sql", "lookup_control.sql", "tt_control.sql",
                                       "tt_department_distribution.sql"})
        self.assertIn("2026-11-01 00:00:00", output["finance_control.sql"])
        self.assertIn("f.dt = '20261104'", output["finance_control.sql"])
        self.assertIn("performance_second_level_department_name='青橙项目部'", output["finance_control.sql"])
        self.assertNotIn("course_second_level_department_name IN", output["tt_department_distribution.sql"])
        self.assertIn("course_second_level_department_name IN", output["tt_control.sql"])

    def test_exports_keep_source_grain_and_use_counts_plus_one(self):
        output = self.build(verified_counts=self.counts())
        self.assertTrue(output["finance.sql"].rstrip().endswith("LIMIT 2001"))
        self.assertTrue(output["lookup.sql"].rstrip().endswith("LIMIT 1901"))
        self.assertTrue(output["tt.sql"].rstrip().endswith("LIMIT 1"))
        self.assertNotIn("course_second_level_department_name IN", output["tt_department_distribution.sql"])
        self.assertIn("course_second_level_department_name IN", output["tt.sql"])
        self.assertNotIn("GROUP BY", output["finance.sql"])
        self.assertNotIn("DISTINCT", output["tt.sql"])
        self.assertTrue(all("{{" not in query and not query.startswith("--") for query in output.values()))

    def test_manifest_records_verified_control_receipts(self):
        counts = self.counts()
        queries = self.build(verified_counts=counts)
        manifest = build_manifest("2026-10-01", "2026-10-31", "20261104", "23",
                                  self.scopes, queries, counts)
        self.assertEqual(manifest["control_receipts"]["tt"]["row_count"], 0)
        self.assertEqual(manifest["control_receipts"]["tt"]["query_id"], "100")
        self.assertIn("tt_department_distribution.sql", manifest["queries"])

    def test_end_is_inclusive_and_snapshot_cannot_precede_it(self):
        with self.assertRaises(ValueError):
            self.build(snapshot_dt="20261030")
        with self.assertRaises(ValueError):
            self.build(end_date="2026-09-30")

    def test_scopes_require_evidence_and_nonempty_names(self):
        with self.assertRaises(ValueError):
            self.build(scopes={**self.scopes, "scope_evidence": None})
        with self.assertRaises(ValueError):
            self.build(scopes={**self.scopes, "goods_second": []})

    def test_control_scope_or_hour_drift_blocks_export(self):
        for key, value in [("scope_sha256", "wrong"), ("snapshot_hour", "22")]:
            counts = self.counts()
            counts["finance"][key] = value
            with self.assertRaises(ValueError):
                self.build(verified_counts=counts)

    def test_department_quotes_remain_sql_literals(self):
        scopes = {**self.scopes, "goods_second": ["a'b"]}
        self.assertIn("IN ('a''b')", self.build(scopes=scopes)["finance_control.sql"])


if __name__ == "__main__":
    unittest.main()
