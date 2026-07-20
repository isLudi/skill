from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from text2sql_core.dashboard_build import (
    build_dashboard_build_plan,
    build_dashboard_build_publish_receipt,
    build_dashboard_build_receipt,
    normalize_dashboard_build_spec,
    validate_dashboard_build_plan,
    validate_dashboard_build_publish_receipt,
    validate_dashboard_build_receipt,
    validate_dashboard_build_spec,
)
from text2sql_core.dashboard_change import canonical_sha256


CORE_ROOT = Path(__file__).resolve().parents[1]


def build_spec() -> dict:
    return {
        "domain": "qingcheng",
        "build_id": "p4c_acceptance",
        "target_folder": {
            "folder_id": "folder_test_1",
            "folder_path": "Market/Qingcheng/P4C Test",
            "folder_name": "P4C Test",
        },
        "dashboard_name": "P4C Acceptance Dashboard",
        "datasets": [
            {
                "dataset_ref": "primary",
                "mode": "existing",
                "domain": "qingcheng",
                "query_plan_path": "runtime/query_plan.json",
                "query_plan_sha256": "1" * 64,
                "dataset_spec_path": "runtime/dataset_spec.json",
                "dataset_spec_sha256": "2" * 64,
                "application_model_id": "model_1",
                "subject_id": "subject_1",
                "model_type": 2,
            }
        ],
        "calculated_columns": [
            {
                "logical_id": "margin_rate",
                "dataset_ref": "primary",
                "name": "Margin rate",
                "data_type": "decimal",
                "formula_template": "${revenue}/${orders}",
                "dependencies": ["revenue", "orders"],
            }
        ],
        "components": [
            {
                "component_id": "metric_group",
                "type": "metric_group",
                "dataset_ref": "primary",
                "measures": ["revenue", "calc:margin_rate"],
                "layout": {"x": 0, "y": 0, "w": 6, "h": 6},
            },
            {
                "component_id": "pivot",
                "type": "pivot",
                "dataset_ref": "primary",
                "dimensions": ["grade"],
                "measures": ["revenue"],
                "local_filters": [{"field_ref": "period", "operator": "in", "values": ["current"]}],
                "layout": {"x": 6, "y": 0, "w": 6, "h": 6},
            },
            {
                "component_id": "bar",
                "type": "bar",
                "dataset_ref": "primary",
                "dimensions": ["grade"],
                "measures": ["revenue"],
                "layout": {"x": 12, "y": 0, "w": 6, "h": 6},
            },
            {
                "component_id": "pie",
                "type": "pie",
                "dataset_ref": "primary",
                "dimensions": ["grade"],
                "measures": ["revenue"],
                "layout": {"x": 18, "y": 0, "w": 6, "h": 6},
            },
        ],
        "global_filters": [
            {
                "filter_id": "period_filter",
                "dataset_ref": "primary",
                "title": "Period",
                "field_ref": "period",
                "operator": "in",
                "default_values": ["current"],
                "target_component_refs": ["metric_group", "pivot", "bar", "pie"],
            }
        ],
        "theme": {"background_color": "#FFFFFF"},
        "validation_checks": [{"check_id": "filtered_total", "expected": 100}],
        "publish_requested": False,
    }


def resolutions() -> dict:
    bindings = [
        {"field_ref": "revenue", "field_id": "field_revenue", "field_group": "metric", "data_type": "decimal"},
        {"field_ref": "orders", "field_id": "field_orders", "field_group": "metric", "data_type": "integer"},
        {"field_ref": "grade", "field_id": "field_grade", "field_group": "dimension", "data_type": "string"},
        {"field_ref": "period", "field_id": "field_period", "field_group": "dimension", "data_type": "string"},
    ]
    field_tree = copy.deepcopy(bindings)
    return {
        "datasets": [
            {
                "dataset_ref": "primary",
                "domain": "qingcheng",
                "status": "ready",
                "query_plan_sha256": "1" * 64,
                "dataset_spec_sha256": "2" * 64,
                "query_plan_status": "executable",
                "dataset_spec_status": "ready",
                "contracts_confirmed": True,
                "source_hashes_valid": True,
                "dataset_fields_match": True,
                "application_model_id": "model_1",
                "subject_id": "subject_1",
                "model_type": 2,
                "dataset_schema_sha256": canonical_sha256(
                    sorted(field_tree, key=lambda item: item["field_id"])
                ),
                "field_binding_sha256": canonical_sha256(
                    sorted(bindings, key=lambda item: item["field_ref"])
                ),
                "field_bindings": bindings,
                "field_tree": field_tree,
            }
        ]
    }


class DashboardBuildContractTests(unittest.TestCase):
    def assert_schema(self, filename: str, value: dict) -> None:
        schema = json.loads((CORE_ROOT / "schemas" / filename).read_text(encoding="utf-8"))
        errors = list(Draft202012Validator(schema).iter_errors(value))
        self.assertEqual([], [error.message for error in errors])

    def ready_plan(self) -> tuple[dict, dict]:
        spec = normalize_dashboard_build_spec(build_spec())
        plan = build_dashboard_build_plan(
            spec,
            resolutions(),
            folder_snapshot_sha256="5" * 64,
            dashboard_name_available=True,
        )
        return spec, plan

    def test_artifacts_hash_and_schema(self) -> None:
        spec, plan = self.ready_plan()
        self.assertEqual("ready", plan["status"])
        self.assertEqual([], validate_dashboard_build_spec(spec))
        self.assertEqual([], validate_dashboard_build_plan(plan))
        self.assert_schema("dashboard_build_spec.schema.json", spec)
        self.assert_schema("dashboard_build_plan.schema.json", plan)

        operations = [
            {"operation_id": "create", "operation_type": "create_dashboard", "status": "applied"}
        ]
        receipt = build_dashboard_build_receipt(
            plan,
            operation_results=operations,
            created_resources=[{"logical_id": "dashboard", "resource_id": "dashboard_1"}],
            dashboard_id="dashboard_1",
            html_id="html_1",
            post_profile_sha256="6" * 64,
            value_checks=[
                {
                    "component_id": item["component_id"],
                    "ok": True,
                    "response_shape": {
                        "metric_group": "metric_group",
                        "pivot": "pivot",
                        "bar": "chart",
                        "pie": "chart",
                    }[item["type"]],
                }
                for item in plan["components"]
            ],
            global_filter_checks=[
                {
                    "filter_id": "period_filter",
                    "ok": True,
                    "public_filter_list_applied": True,
                    "assertions_passed": True,
                }
            ],
        )
        self.assertTrue(receipt["ok"])
        self.assertEqual([], validate_dashboard_build_receipt(receipt, plan))
        self.assert_schema("dashboard_build_receipt.schema.json", receipt)

        publish = build_dashboard_build_publish_receipt(
            plan,
            receipt,
            version_description="approved build",
            publish_payload_sha256="7" * 64,
            pre_publish_profile_sha256="6" * 64,
            post_publish_draft_profile_sha256="6" * 64,
        )
        self.assertFalse(publish["fully_verified"])
        self.assertEqual("publish_requested_unverified", publish["publish_status"])
        self.assertEqual([], validate_dashboard_build_publish_receipt(publish, receipt))
        self.assert_schema("dashboard_build_publish_receipt.schema.json", publish)

    def test_advanced_build_contract_resolves_metric_names_tabs_text_and_styles(self) -> None:
        raw = build_spec()
        for component in raw["components"]:
            component["measures"] = [
                {"field_ref": value, "display_name": f"Display {value}"}
                for value in component["measures"]
            ]
        raw["components"].extend(
            [
                {
                    "component_id": "slot_pivot_grade",
                    "type": "pivot",
                    "dataset_ref": "primary",
                    "dimensions": ["grade"],
                    "measures": [
                        {"field_ref": "revenue", "display_name": "Slot revenue by grade"}
                    ],
                    "container_ref": "analysis_tabs",
                    "slot_ref": "grade_view",
                    "style_preset": "arco_blue",
                    "layout": {"x": 0, "y": 0, "w": 24, "h": 8},
                },
                {
                    "component_id": "slot_pivot_period",
                    "type": "pivot",
                    "dataset_ref": "primary",
                    "dimensions": ["period"],
                    "measures": [
                        {"field_ref": "revenue", "display_name": "Slot revenue by period"}
                    ],
                    "container_ref": "analysis_tabs",
                    "slot_ref": "period_view",
                    "layout": {"x": 0, "y": 0, "w": 24, "h": 8},
                },
            ]
        )
        raw["containers"] = [
            {
                "container_id": "analysis_tabs",
                "type": "tabs",
                "title": "Analysis tabs",
                "description": "Two governed perspectives",
                "slots": [
                    {"slot_id": "grade_view", "label": "By grade"},
                    {"slot_id": "period_view", "label": "By period"},
                ],
                "style_preset": "wide",
                "layout": {"x": 0, "y": 8, "w": 24, "h": 10},
            }
        ]
        raw["text_components"] = [
            {
                "text_id": "header",
                "title": "Dashboard heading",
                "initial_text": "Advanced dashboard",
                "content_html": "<p><strong>Advanced dashboard</strong></p>",
                "style_preset": "default",
                "layout": {"x": 0, "y": 6, "w": 24, "h": 2},
            }
        ]
        spec = normalize_dashboard_build_spec(raw)
        plan = build_dashboard_build_plan(
            spec,
            resolutions(),
            folder_snapshot_sha256="5" * 64,
            dashboard_name_available=True,
        )
        self.assertEqual("1.1.0", spec["schema_version"])
        self.assertEqual("ready", plan["status"])
        self.assertEqual("Display revenue", plan["components"][0]["measures"][0]["display_name"])
        self.assertEqual(1, len(plan["containers"]))
        self.assertEqual(1, len(plan["text_components"]))
        self.assertTrue(
            {
                "rename_new_component_metrics",
                "create_tab_container",
                "assemble_tab_slots",
                "create_text_component",
                "style_new_components",
            }.issubset(set(plan["required_capabilities"]))
        )
        self.assert_schema("dashboard_build_spec.schema.json", spec)
        self.assert_schema("dashboard_build_plan.schema.json", plan)

    def test_advanced_build_rejects_partial_metric_names_and_unproven_slot_filters(self) -> None:
        partial = build_spec()
        partial["components"][0]["measures"][0] = {
            "field_ref": "revenue",
            "display_name": "Revenue display",
        }
        with self.assertRaisesRegex(ValueError, "all-or-none"):
            normalize_dashboard_build_spec(partial)

        nested = build_spec()
        nested["containers"] = [
            {
                "container_id": "tabs",
                "type": "tabs",
                "title": "Tabs",
                "slots": [
                    {"slot_id": "left", "label": "Left"},
                    {"slot_id": "right", "label": "Right"},
                ],
                "layout": {"x": 0, "y": 6, "w": 24, "h": 8},
            }
        ]
        nested["components"].extend(
            [
                {
                    "component_id": "left_pivot",
                    "type": "pivot",
                    "dataset_ref": "primary",
                    "dimensions": ["grade"],
                    "measures": ["revenue"],
                    "local_filters": [{"field_ref": "period"}],
                    "container_ref": "tabs",
                    "slot_ref": "left",
                },
                {
                    "component_id": "right_pivot",
                    "type": "pivot",
                    "dataset_ref": "primary",
                    "dimensions": ["period"],
                    "measures": ["revenue"],
                    "container_ref": "tabs",
                    "slot_ref": "right",
                },
            ]
        )
        with self.assertRaisesRegex(ValueError, "cannot carry local filters"):
            normalize_dashboard_build_spec(nested)

    def test_hash_tamper_is_rejected(self) -> None:
        spec, plan = self.ready_plan()
        tampered_spec = copy.deepcopy(spec)
        tampered_spec["dashboard_name"] = "Tampered"
        self.assertEqual("BUILD_SPEC_HASH_MISMATCH", validate_dashboard_build_spec(tampered_spec)[0]["code"])
        tampered_plan = copy.deepcopy(plan)
        tampered_plan["dashboard_name"] = "Tampered"
        self.assertEqual("BUILD_PLAN_HASH_MISMATCH", validate_dashboard_build_plan(tampered_plan)[0]["code"])

    def test_missing_and_duplicate_field_bindings_block_plan(self) -> None:
        spec = normalize_dashboard_build_spec(build_spec())
        missing = resolutions()
        missing["datasets"][0]["field_bindings"] = [
            item for item in missing["datasets"][0]["field_bindings"] if item["field_ref"] != "grade"
        ]
        plan = build_dashboard_build_plan(spec, missing)
        self.assertEqual("blocked", plan["status"])
        self.assertTrue(any("missing field binding grade" in item for item in plan["blocked_reasons"]))

        duplicate = resolutions()
        duplicate["datasets"][0]["field_bindings"].append(copy.deepcopy(duplicate["datasets"][0]["field_bindings"][0]))
        plan = build_dashboard_build_plan(spec, duplicate)
        self.assertTrue(any("duplicate field binding" in item for item in plan["blocked_reasons"]))

    def test_field_group_type_mismatch_blocks_plan(self) -> None:
        spec = normalize_dashboard_build_spec(build_spec())
        incompatible = resolutions()
        grade = next(
            item
            for item in incompatible["datasets"][0]["field_bindings"]
            if item["field_ref"] == "grade"
        )
        grade["field_group"] = "metric"
        incompatible["datasets"][0]["field_binding_sha256"] = canonical_sha256(
            sorted(
                incompatible["datasets"][0]["field_bindings"],
                key=lambda item: item["field_ref"],
            )
        )
        plan = build_dashboard_build_plan(spec, incompatible)
        self.assertEqual("blocked", plan["status"])
        self.assertTrue(
            any("type-incompatible with dimension" in item for item in plan["blocked_reasons"])
        )

        stale_identity = resolutions()
        stale_identity["datasets"][0]["subject_id"] = "subject_other"
        plan = build_dashboard_build_plan(spec, stale_identity)
        self.assertTrue(
            any("subject_id conflicts" in item for item in plan["blocked_reasons"])
        )

        stale_status = resolutions()
        stale_status["datasets"][0]["status"] = "observed"
        plan = build_dashboard_build_plan(spec, stale_status)
        self.assertTrue(
            any("platform resolution is not ready" in item for item in plan["blocked_reasons"])
        )

    def test_two_ready_datasets_are_bound_independently(self) -> None:
        raw = build_spec()
        secondary = copy.deepcopy(raw["datasets"][0])
        secondary.update(
            {
                "dataset_ref": "secondary",
                "query_plan_path": "runtime/query_plan_secondary.json",
                "query_plan_sha256": "3" * 64,
                "dataset_spec_path": "runtime/dataset_spec_secondary.json",
                "dataset_spec_sha256": "4" * 64,
                "application_model_id": "model_2",
                "subject_id": "subject_2",
            }
        )
        raw["datasets"].append(secondary)
        raw["components"][3]["dataset_ref"] = "secondary"
        raw["global_filters"][0]["target_component_refs"].remove("pie")
        spec = normalize_dashboard_build_spec(raw)

        resolved = resolutions()
        secondary_resolution = copy.deepcopy(resolved["datasets"][0])
        secondary_resolution.update(
            {
                "dataset_ref": "secondary",
                "query_plan_sha256": "3" * 64,
                "dataset_spec_sha256": "4" * 64,
                "application_model_id": "model_2",
                "subject_id": "subject_2",
            }
        )
        resolved["datasets"].append(secondary_resolution)
        plan = build_dashboard_build_plan(
            spec,
            resolved,
            folder_snapshot_sha256="5" * 64,
            dashboard_name_available=True,
        )
        self.assertEqual("ready", plan["status"])
        self.assertEqual(
            {"primary", "secondary"},
            {item["dataset_ref"] for item in plan["datasets"]},
        )

    def test_dataset_creation_stays_pending_without_independent_receipt_success(self) -> None:
        raw = build_spec()
        raw["datasets"][0]["mode"] = "create"
        raw["datasets"][0]["data_center_creation_plan_sha256"] = "8" * 64
        spec = normalize_dashboard_build_spec(raw)
        create_resolution = resolutions()
        create_resolution["datasets"][0]["data_center_creation_plan_sha256"] = "8" * 64
        create_resolution["datasets"][0]["data_center_receipt_status"] = "created"
        create_resolution["datasets"][0]["first_sync_status"] = "RUNNING"
        plan = build_dashboard_build_plan(
            spec,
            create_resolution,
            folder_snapshot_sha256="5" * 64,
            dashboard_name_available=True,
        )
        self.assertEqual("pending_dataset_creation", plan["status"])
        self.assertFalse(plan["write_boundary"]["authorizes_data_center_apply"])

    def test_cross_domain_cycle_collision_and_duplicate_ids_are_rejected(self) -> None:
        cross = build_spec()
        cross["datasets"][0]["domain"] = "market_consultant"
        with self.assertRaisesRegex(ValueError, "crosses domain"):
            normalize_dashboard_build_spec(cross)

        cycle = build_spec()
        cycle["calculated_columns"].append(
            {
                "logical_id": "other_calc",
                "dataset_ref": "primary",
                "name": "Other",
                "data_type": "decimal",
                "formula_template": "${margin_rate}",
                "dependencies": ["calc:margin_rate"],
            }
        )
        cycle["calculated_columns"][0]["dependencies"].append("calc:other_calc")
        with self.assertRaisesRegex(ValueError, "dependency cycle"):
            normalize_dashboard_build_spec(cycle)

        collision = build_spec()
        collision["components"][1]["layout"]["x"] = 0
        with self.assertRaisesRegex(ValueError, "collide"):
            normalize_dashboard_build_spec(collision)

        duplicate = build_spec()
        duplicate["components"][1]["component_id"] = "metric_group"
        with self.assertRaisesRegex(ValueError, "duplicate component_id"):
            normalize_dashboard_build_spec(duplicate)

        duplicate_formula_name = build_spec()
        second_formula = copy.deepcopy(duplicate_formula_name["calculated_columns"][0])
        second_formula["logical_id"] = "margin_rate_copy"
        duplicate_formula_name["calculated_columns"].append(second_formula)
        with self.assertRaisesRegex(ValueError, "duplicate calculated column name"):
            normalize_dashboard_build_spec(duplicate_formula_name)

        no_assertion = build_spec()
        no_assertion["validation_checks"] = []
        with self.assertRaisesRegex(ValueError, "value validation check"):
            normalize_dashboard_build_spec(no_assertion)

    def test_failure_receipt_never_claims_rollback_and_lists_orphans(self) -> None:
        _spec, plan = self.ready_plan()
        receipt = build_dashboard_build_receipt(
            plan,
            operation_results=[{"operation_id": "formula", "status": "failed", "message": "fault"}],
            created_resources=[{"logical_id": "dashboard", "resource_id": "dashboard_1"}],
            failure="fault",
        )
        self.assertFalse(receipt["ok"])
        self.assertTrue(receipt["manual_cleanup_required"])
        self.assertFalse(receipt["recovery"]["automatic_delete_attempted"])
        self.assertFalse(receipt["recovery"]["rolled_back"])
        self.assertEqual(1, len(receipt["orphaned_resources"]))


if __name__ == "__main__":
    unittest.main()
