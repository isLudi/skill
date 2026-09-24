from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


CORE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = CORE_ROOT.parents[1]
SKILL_ROOT = REPO_ROOT / "jingpin-dashboard-sql"
sys.path.insert(0, str(CORE_ROOT))

from text2sql_core.models import QueryPlan, QuerySpec  # noqa: E402
from text2sql_core.planner import build_query_plan  # noqa: E402


class JingpinQueryDomainTests(unittest.TestCase):
    def test_query_plan_schema_and_model_accept_jingpin(self) -> None:
        payload = {
            "schema_version": "2.0.0",
            "plan_id": "plan_0123456789abcdef0123",
            "domain": "jingpin_department",
            "intent": "refund_analysis",
            "status": "blocked",
            "base_table": None,
            "metrics": [],
            "dimensions": [],
            "filters": [],
            "scopes": [],
            "joins": [],
            "calculation_grain": [],
            "output_grain": [],
            "evidence": [],
            "lineage": [],
            "unresolved_slots": ["metric_contract"],
            "diagnostics": [],
            "execution_policy": {
                "allow_download": False,
                "max_direct_download_rows": 1000,
                "requires_preview": True,
                "execution_mode": "exploratory"
            },
            "sql_sha256": None
        }
        schema = json.loads((CORE_ROOT / "schemas" / "query_plan.schema.json").read_text(encoding="utf-8"))
        self.assertEqual([], list(Draft202012Validator(schema).iter_errors(payload)))
        self.assertEqual(QueryPlan.from_dict(payload).domain, "jingpin_department")

    def test_confirmed_refund_bundle_still_requires_manual_recipe(self) -> None:
        spec = QuerySpec.from_dict(
            {
                "domain": "jingpin_department",
                "intent": "metric_query",
                "metrics": [{
                    "id": "jingpin_department:metric:refund_core_bundle",
                    "name": "精品班退费核心指标组",
                    "source_path": "knowledge/metrics/scope_metrics.md"
                }],
                "dimensions": [],
                "filters": [{"field": "dt", "operator": "=", "value": "20260919"}],
                "time_range": {"start": "2026-05-01", "end": "2026-09-19"},
                "calculation_grain": ["learner", "observation_window"],
                "output_grain": ["learner"],
                "candidate_tables": [{
                    "name": "service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf",
                    "source_path": "knowledge/metrics/scope_metrics.md"
                }],
                "join_path": [],
                "evidence": [],
                "unresolved_slots": []
            }
        )
        plan = build_query_plan(spec, skill_root=SKILL_ROOT, core_root=CORE_ROOT)
        self.assertFalse(plan.executable)
        self.assertIn("PLAN_METRIC_MANUAL_RECIPE_REQUIRED", {item.code for item in plan.diagnostics})
        self.assertNotIn("PLAN_METRIC_PENDING", {item.code for item in plan.diagnostics})


if __name__ == "__main__":
    unittest.main()
