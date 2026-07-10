from __future__ import annotations

import sys
import unittest
from pathlib import Path


CORE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CORE_ROOT))

from text2sql_core.models import QuerySpec  # noqa: E402


def valid_spec(domain: str = "market_consultant") -> QuerySpec:
    return QuerySpec.from_dict(
        {
            "domain": domain,
            "intent": "metric_query",
            "metrics": [
                {
                    "id": f"{domain}:net_revenue",
                    "name": "net_revenue",
                    "source_path": "knowledge/metrics/example.md",
                }
            ],
            "dimensions": ["period"],
            "filters": [{"field": "dt", "operator": "=", "value": "20260701"}],
            "time_range": {"start": "2026-07-01", "end": "2026-07-01"},
            "calculation_grain": ["period", "consultant"],
            "output_grain": ["period", "consultant"],
            "candidate_tables": [
                {
                    "name": "finance_dw.app_finance_performance_extend_details_hf",
                    "source_path": "knowledge/tables/finance_dw.app_finance_performance_extend_details_hf.md",
                }
            ],
            "join_path": [],
            "evidence": [
                {
                    "source_path": "knowledge/metrics/example.md",
                    "kind": "metric",
                    "supports": ["net_revenue"],
                }
            ],
            "unresolved_slots": [],
        }
    )


class QuerySpecTest(unittest.TestCase):
    def test_valid_spec_is_executable(self) -> None:
        self.assertTrue(valid_spec().is_executable)

    def test_unresolved_slot_blocks_execution(self) -> None:
        spec = valid_spec()
        spec.unresolved_slots.append("department_scope")
        self.assertIn("SPEC_UNRESOLVED_SLOTS", {item.code for item in spec.validate()})
        self.assertFalse(spec.is_executable)

    def test_cross_domain_evidence_is_rejected(self) -> None:
        spec = valid_spec("qingcheng")
        spec.evidence.append(
            {
                "source_path": "sql-query-writer-for-dashboard/knowledge/metrics/market.md",
                "kind": "metric",
                "supports": ["market metric"],
            }
        )
        self.assertIn("SPEC_CROSS_DOMAIN_EVIDENCE", {item.code for item in spec.validate()})

    def test_metric_id_requires_domain_namespace(self) -> None:
        spec = valid_spec()
        spec.metrics[0]["id"] = "net_revenue"
        self.assertIn("SPEC_METRIC_NOT_NAMESPACED", {item.code for item in spec.validate()})

    def test_unresolved_domain_can_be_planned_but_not_executed(self) -> None:
        spec = QuerySpec.from_dict(
            {
                "domain": "unresolved",
                "intent": "metric_query",
                "metrics": [],
                "dimensions": [],
                "filters": [],
                "time_range": None,
                "calculation_grain": [],
                "output_grain": [],
                "candidate_tables": [],
                "join_path": [],
                "evidence": [],
                "unresolved_slots": ["domain"],
            }
        )
        self.assertIn("SPEC_DOMAIN_UNRESOLVED", {item.code for item in spec.validate()})
        self.assertFalse(spec.is_executable)


if __name__ == "__main__":
    unittest.main()
