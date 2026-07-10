"""Create a read-only dashboard dataset design from a QueryPlan."""

from __future__ import annotations

from typing import Any

from .models import QueryPlan


def build_dataset_spec(plan: QueryPlan) -> dict[str, Any]:
    fields: list[dict[str, Any]] = []
    for dimension in plan.dimensions:
        fields.append(
            {
                "name": dimension.get("output_alias"),
                "role": "dimension",
                "data_type": dimension.get("data_type") or "unknown",
                "filterable": True,
                "aggregation": "none",
                "contract_id": dimension.get("id"),
                "source_path": dimension.get("source_path"),
            }
        )
    for metric in plan.metrics:
        aggregation = str(metric.get("aggregation") or "unknown")
        fields.append(
            {
                "name": metric.get("output_alias"),
                "role": "measure",
                "data_type": "number",
                "filterable": False,
                "aggregation": aggregation,
                "bi_aggregation_policy": (
                    "sum_sql_output" if aggregation == "sum" else "do_not_reaggregate"
                ),
                "contract_id": metric.get("id"),
                "source_path": metric.get("source_path"),
            }
        )
    return {
        "schema_version": "2.0.0",
        "artifact_type": "dashboard_dataset_spec",
        "mode": "read_only_design",
        "domain": plan.domain,
        "plan_id": plan.plan_id,
        "status": "ready" if plan.executable and plan.sql_sha256 else "draft",
        "grain": plan.output_grain,
        "base_table": plan.base_table,
        "scope_contracts": plan.scopes,
        "fields": fields,
        "default_filters": [
            {
                "field": item.get("field"),
                "operator": item.get("operator"),
                "value": item.get("value"),
                "role": item.get("role", "business_scope"),
                "contract_id": item.get("contract_id"),
            }
            for item in plan.filters
        ],
        "lineage": plan.lineage,
        "write_boundary": {
            "may_profile_existing_dashboard": True,
            "may_generate_diff_plan": True,
            "may_modify_dashboard": False,
            "may_publish_dashboard": False,
        },
    }
