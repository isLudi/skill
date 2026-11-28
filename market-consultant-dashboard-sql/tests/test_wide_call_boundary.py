"""Check the local canonical wide-template call expressions with synthetic rows."""

import re
import sqlite3
import unittest
from pathlib import Path

import sqlglot
from sqlglot import exp


TEMPLATE = Path(__file__).resolve().parents[1] / "resources/raw_sql/template_query_market_wide.sql"
FIELDS = (
    "is_long_call", "is_5m_call", "is_20m_call", "is_40m_call",
    "long_call_z", "call_5m_z", "call_20m_z", "call_40m_z",
)


def expressions(cte, names):
    aliases = {node.alias_or_name: node.this for node in cte.expressions if isinstance(node, exp.Alias)}
    missing = set(names) - aliases.keys()
    if missing:
        raise AssertionError(f"Canonical SQL is missing aliases: {sorted(missing)}")
    return {name: aliases[name] for name in names}


def replace_columns(node):
    replacements = {
        ("b", "valid_lead_count"): "valid_flag",
        ("b", "conversion_lead_count"): "converted_flag",
        ("call_c", "call_duration_1"): "total_seconds",
        ("call_c", "is_long_call"): "single_long_flag",
        ("sub", "call_duration"): "duration",
    }
    if isinstance(node, exp.Column):
        name = replacements.get((node.table, node.name))
        if name:
            return exp.column(name)
    return node


class WideCallBoundaryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = TEMPLATE.read_text(encoding="utf-8")
        statement = sqlglot.parse_one(re.sub(r"\$\{[^}]+\}", "NULL", source), read="presto")
        ctes = {cte.alias_or_name: cte.this for cte in statement.ctes}
        cls.call_expr = expressions(ctes["call_c"], ("is_long_call",))["is_long_call"]
        cls.metrics = expressions(ctes["lead_enriched"], FIELDS)

    def evaluate(self, durations, valid=1, converted=1):
        db = sqlite3.connect(":memory:")
        self.addCleanup(db.close)
        db.execute("CREATE TABLE calls(duration REAL)")
        db.executemany("INSERT INTO calls VALUES (?)", [(duration,) for duration in durations])
        call_expr = self.call_expr.copy().transform(replace_columns).sql(dialect="sqlite")
        single, total = db.execute(f"SELECT {call_expr}, SUM(duration) FROM calls").fetchone()
        db.execute("CREATE TABLE sample(valid_flag, converted_flag, total_seconds, single_long_flag)")
        db.execute("INSERT INTO sample VALUES (?, ?, ?, ?)", (valid, converted, total, single))
        selected = ", ".join(
            f"{node.copy().transform(replace_columns).sql(dialect='sqlite')} AS {name}"
            for name, node in self.metrics.items()
        )
        cursor = db.execute("SELECT " + selected + " FROM sample")
        return dict(zip((column[0] for column in cursor.description), cursor.fetchone()))

    def test_thresholds_and_cumulative_bands(self):
        cases = [
            (29, 0, 0, 0, 0), (30, 0, 1, 0, 0), (299, 0, 1, 0, 0),
            (300, 0, 1, 0, 0), (301, 1, 1, 0, 0), (1199, 1, 1, 0, 0),
            (1200, 1, 0, 1, 0), (2399, 1, 0, 1, 0), (2400, 1, 0, 0, 1),
        ]
        for seconds, long_call, band5, band20, band40 in cases:
            with self.subTest(seconds=seconds):
                result = self.evaluate([seconds])
                self.assertEqual((result["is_long_call"], result["is_5m_call"],
                                  result["is_20m_call"], result["is_40m_call"]),
                                 (long_call, band5, band20, band40))

    def test_short_calls_do_not_become_single_long_calls(self):
        result = self.evaluate([240] * 10)
        self.assertEqual(result["is_long_call"], 0)
        self.assertEqual(result["is_40m_call"], 1)
        self.assertEqual(result["call_40m_z"], 1)
        self.assertEqual(result["long_call_z"], 0)

    def test_conversion_and_valid_lead_gates_differ(self):
        result = self.evaluate([1800], valid=0, converted=1)
        self.assertEqual(result["is_long_call"], 0)
        self.assertEqual(result["long_call_z"], 0)
        self.assertEqual(result["call_20m_z"], 1)
        result = self.evaluate([1800], valid=1, converted=0)
        self.assertEqual(result["is_long_call"], 1)
        self.assertEqual(result["call_20m_z"], 0)

    def test_null_duration_has_no_call_band(self):
        result = self.evaluate([None])
        self.assertTrue(all(result[name] == 0 for name in FIELDS))


if __name__ == "__main__":
    unittest.main()
