"""Create a read-only dashboard dataset design from a QueryPlan."""

from __future__ import annotations

from typing import Any

from .dashboard_change import artifact_sha256, canonical_sha256
from .models import QueryPlan


def build_dataset_spec(plan: QueryPlan) -> dict[str, Any]:
    def contract_evidence(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "contract_status": item.get("contract_status"),
            "source_domain": item.get("source_domain"),
            "source_path": item.get("source_path"),
            "source_sha256": item.get("source_sha256"),
        }

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
                **contract_evidence(dimension),
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
                **contract_evidence(metric),
            }
        )
    contract_records = {
        str(item.get("id")): item
        for item in [*plan.metrics, *plan.dimensions, *plan.scopes]
        if item.get("id")
    }
    default_filters: list[dict[str, Any]] = []
    for item in plan.filters:
        row = {
            "field": item.get("field"),
            "operator": item.get("operator"),
            "value": item.get("value"),
            "role": item.get("role", "business_scope"),
            "contract_id": item.get("contract_id"),
        }
        contract = contract_records.get(str(item.get("contract_id") or ""))
        if contract:
            row.update(contract_evidence(contract))
        default_filters.append(row)
    payload = {
        "schema_version": "2.0.0",
        "artifact_type": "dashboard_dataset_spec",
        "mode": "read_only_design",
        "domain": plan.domain,
        "plan_id": plan.plan_id,
        "status": "ready" if plan.executable and plan.sql_sha256 else "draft",
        "grain": plan.output_grain,
        "base_table": plan.base_table,
        "scope_contracts": [dict(item) for item in plan.scopes],
        "fields": fields,
        "default_filters": default_filters,
        "lineage": plan.lineage,
        "query_plan_sha256": canonical_sha256(plan.to_dict()),
        "write_boundary": {
            "may_profile_existing_dashboard": True,
            "may_generate_diff_plan": True,
            "may_modify_dashboard": False,
            "may_publish_dashboard": False,
        },
    }
    payload["dataset_spec_sha256"] = artifact_sha256(payload, "dataset_spec_sha256")
    return payload
