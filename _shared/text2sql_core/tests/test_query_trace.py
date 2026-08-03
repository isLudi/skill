from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


CORE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CORE_ROOT))

from text2sql_core.trace import (  # noqa: E402
    append_trace_stage,
    bind_query_plan,
    bind_sql_sha256,
    canonical_json_sha256,
    create_query_trace,
    load_query_trace,
    write_query_trace,
)


class QueryTraceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.spec = {
            "schema_version": "2.0.0",
            "spec_id": "spec_example",
            "domain": "market_consultant",
            "intent": "metric_query",
        }
        self.plan = {
            "schema_version": "2.0.0",
            "plan_id": "plan_0123456789abcdef0123",
            "domain": "market_consultant",
            "sql_sha256": None,
        }

    def test_trace_contains_hashes_but_not_raw_question(self) -> None:
        question = "sensitive natural-language request"
        digest = hashlib.sha256(question.encode("utf-8")).hexdigest()
        trace = create_query_trace(
            domain="market_consultant",
            question_sha256=digest,
            spec=self.spec,
        )
        bind_query_plan(trace, self.plan)
        append_trace_stage(trace, name="plan", status="success", duration_ms=1.25)

        rendered = json.dumps(trace, ensure_ascii=False)
        self.assertNotIn(question, rendered)
        self.assertEqual(trace["question_sha256"], digest)
        self.assertEqual(trace["references"]["spec_sha256"], canonical_json_sha256(self.spec))
        self.assertEqual(trace["references"]["plan_sha256"], canonical_json_sha256(self.plan))

    def test_sql_hash_binding_rejects_drift(self) -> None:
        trace = create_query_trace(domain="qingcheng")
        bind_sql_sha256(trace, "a" * 64)
        with self.assertRaisesRegex(ValueError, "does not match"):
            bind_sql_sha256(trace, "b" * 64)

    def test_atomic_round_trip_is_schema_valid(self) -> None:
        trace = create_query_trace(domain="unresolved", sql_sha256="c" * 64)
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "query_trace.json"
            write_query_trace(path, trace)
            loaded = load_query_trace(path)
        self.assertEqual(loaded["trace_id"], trace["trace_id"])
        self.assertEqual(loaded["references"]["sql_sha256"], "c" * 64)


if __name__ == "__main__":
    unittest.main()
