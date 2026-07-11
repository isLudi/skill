from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from _shared.errors import UsageError  # noqa: E402
from read_dashboard.cli import build_parser  # noqa: E402
from read_dashboard.dashboard_change import (  # noqa: E402
    _core_api,
    apply_change_plan_to_draft,
    artifact_sha256,
    build_change_plan,
    build_design_spec,
    normalize_profile,
    preflight_apply_plan,
    preflight_publish_receipt,
    publish_applied_draft,
    require_complete_profile,
)
from read_dashboard.commands.design_dashboard import cmd_design_dashboard  # noqa: E402
from read_dashboard.edit_profile import (  # noqa: E402
    build_dashboard_snapshot,
    canonical_dashboard_id,
    fetch_edit_dashboard_config,
    profile_edit_dashboard,
    validate_pivot_bindings,
)
from read_dashboard.filter_edit import (  # noqa: E402
    apply_stable_public_filter_operations,
    assert_stable_public_filter_preconditions,
    public_filter_field_state,
)


def public_filter_detail() -> dict:
    return {
        "unitId": "relation_1",
        "unitList": [
            {
                "unitId": "public_filter_1",
                "unitName": "Period",
                "format": {
                    "unitConfig": {
                        "unitDimensionList": [
                            {
                                "fieldId": "period",
                                "showName": "period",
                                "format": {
                                    "condition": "in",
                                    "filterValue": [],
                                    "dynamicsFilter": True,
                                    "dynamicsFilterValue": "1",
                                    "autoSearchDefaultValue": False,
                                },
                            },
                            {
                                "fieldId": "grade",
                                "showName": "grade",
                                "format": {
                                    "condition": "in",
                                    "filterValue": [],
                                    "dynamicsFilter": True,
                                    "dynamicsFilterValue": "1",
                                    "autoSearchDefaultValue": False,
                                },
                            },
                        ]
                    }
                },
            }
        ],
    }


def dashboard_html() -> dict:
    return {
        "componentsTree": [
            {
                "id": "root",
                "componentName": "RootContentNew",
                "props": {
                    "layout": [
                        {"i": ".$filter_node", "x": 0, "y": 0, "w": 12, "h": 4},
                        {"i": ".$pivot_node", "x": 0, "y": 4, "w": 12, "h": 8},
                    ]
                },
                "children": [
                    {
                        "id": "filter_node",
                        "componentName": "GlobalFilter",
                        "props": {
                            "settings": {
                                "unitId": "relation_1",
                                "componentType": "public_filter_relation",
                                "componentName": "Global filters",
                            }
                        },
                    },
                    {
                        "id": "pivot_node",
                        "componentName": "PivotTable",
                        "props": {
                            "settings": {
                                "unitId": "pivot_1",
                                "componentType": "u_pivot",
                                "componentName": "Pivot",
                            }
                        },
                    },
                ],
            }
        ]
    }


def pivot_profile() -> dict:
    return {
        "unit_id": "pivot_1",
        "model_id": "model_1",
        "model_name": "Lead model",
        "model_type": 2,
        "dashboard_model": {
            "subjectId": 101,
            "applicationModelId": "model_1",
            "modelType": 2,
        },
        "component": {"node_id": "pivot_node"},
        "selected_fields": [
            {"key": "formula_1", "changeParamType": None, "orgParamType": 4},
            {"key": "grade", "changeParamType": None, "orgParamType": 2},
        ],
        "fields": [
            {
                "field_id": "formula_1",
                "group": "measure",
                "role": "custom_measure",
                "business_name": "Rate",
                "formula": "sum(a)/sum(b)",
                "dependencies": ["a", "b"],
                "detail": {"detail_type": "customized_column"},
            },
            {
                "field_id": "grade",
                "group": "filter",
                "role": "dimension",
                "business_name": "Grade",
                "formula": "",
                "dependencies": [],
                "detail": {"detail_type": "dimension"},
            },
        ],
    }


def raw_profile() -> dict:
    snapshot = build_dashboard_snapshot(
        dashboard_id="dashboard_3852445620602875904",
        dashboard_name="Dashboard",
        version_id="draft",
        html_id="html_1",
        domain="qingcheng",
        dashboard_html=dashboard_html(),
        pivot_units=[pivot_profile()],
        public_filters={"relation_1": public_filter_detail()},
    )
    return {
        "domain": "qingcheng",
        "dashboard_id": "dashboard_3852445620602875904",
        "dashboard_name": "Dashboard",
        "version_id": "draft",
        "snapshot": snapshot,
    }


def dataset_spec() -> dict:
    value = {
        "schema_version": "2.0.0",
        "artifact_type": "dashboard_dataset_spec",
        "mode": "read_only_design",
        "domain": "qingcheng",
        "plan_id": "plan_1",
        "status": "ready",
        "grain": ["lead_id"],
        "base_table": "db.table",
        "scope_contracts": [],
        "fields": [],
        "default_filters": [],
        "lineage": [],
        "query_plan_sha256": "a" * 64,
        "write_boundary": {
            "may_profile_existing_dashboard": True,
            "may_generate_diff_plan": True,
            "may_modify_dashboard": False,
            "may_publish_dashboard": False,
        },
    }
    value["dataset_spec_sha256"] = artifact_sha256(value, "dataset_spec_sha256")
    return value


def filter_operation(relation_id: str = "relation_1", field_id: str = "grade") -> dict:
    return {
        "operation_id": f"op_{relation_id}_{field_id}",
        "type": "update_filter_dynamic_default",
        "collection": "public_filters",
        "target": {
            "relation_id": relation_id,
            "filter_id": "public_filter_1",
            "field_id": field_id,
        },
        "before": {"default_value": "1", "dynamic_default": True},
        "after": {
            "default_value": "2",
            "dynamic_default": True,
            "dynamics_filter": True,
            "dynamics_filter_value": "2",
            "auto_search_default_value": False,
            "values": [],
        },
        "write_status": "supported",
        "status": "planned",
        "risk": "low",
        "blocked_reasons": [],
    }


def governed_filter_plan(relation_count: int = 1) -> dict:
    profile = raw_profile()
    if relation_count > 1:
        original = list(profile["snapshot"]["public_filters"])
        for relation_index in range(2, relation_count + 1):
            for item in original:
                clone = json.loads(json.dumps(item))
                clone["relation_id"] = f"relation_{relation_index}"
                clone["filter_id"] = f"public_filter_{relation_index}"
                profile["snapshot"]["public_filters"].append(clone)
    normalized = normalize_profile(profile)
    desired_filters = json.loads(json.dumps(normalized["public_filters"]))
    changed_relations: set[str] = set()
    for item in desired_filters:
        relation_id = str(item.get("relation_id") or "")
        if relation_id in changed_relations:
            continue
        changed_relations.add(relation_id)
        item["default_value"] = "2"
        item["dynamic_default"] = True
        item["dynamics_filter"] = True
        item["dynamics_filter_value"] = "2"
        item["auto_search_default_value"] = False
    design = build_design_spec(
        dataset_spec(),
        profile,
        {"public_filters": desired_filters},
        query_plan_sha256="a" * 64,
        design_intent="change dynamic defaults",
    )
    return build_change_plan(profile, design)


def governed_noop_plan() -> dict:
    profile = raw_profile()
    design = build_design_spec(
        dataset_spec(),
        profile,
        None,
        query_plan_sha256="a" * 64,
        design_intent="preserve current",
    )
    return build_change_plan(profile, design)


def governed_layout_plan() -> dict:
    profile = raw_profile()
    normalized = normalize_profile(profile)
    desired_layout = json.loads(json.dumps(normalized["layout"]))
    target = next(item for item in desired_layout if item["component_id"] == "pivot_node")
    target["x"] = 1
    design = build_design_spec(
        dataset_spec(),
        profile,
        {"layout": desired_layout},
        query_plan_sha256="a" * 64,
        design_intent="move pivot",
    )
    return build_change_plan(profile, design)


def governed_applied_receipt() -> tuple[dict, dict, dict]:
    plan = governed_filter_plan()
    post_profile = normalize_profile(raw_profile())
    post_profile["public_filters"] = json.loads(json.dumps(plan["target_state"]["public_filters"]))
    post_profile = normalize_profile(post_profile)
    receipt = _core_api().build_apply_receipt(plan, post_profile)
    if not receipt.get("ok"):
        raise AssertionError(receipt)
    return plan, post_profile, receipt


class DashboardProfileTests(unittest.TestCase):
    def test_canonical_dashboard_id_adds_required_prefix(self) -> None:
        self.assertEqual("dashboard_123", canonical_dashboard_id("123"))
        self.assertEqual("dashboard_123", canonical_dashboard_id("dashboard_123"))

    def test_edit_config_rejects_empty_success_payload(self) -> None:
        with patch("read_dashboard.edit_profile.post_json", return_value={"data": {}}):
            with self.assertRaisesRegex(UsageError, "config is incomplete"):
                fetch_edit_dashboard_config(Mock(), "dashboard_123", "draft")

    @staticmethod
    def binding_fixture() -> tuple[list[dict], list[dict], dict, list[dict]]:
        pivot = pivot_profile()
        component_units = [
            {
                "node_id": "pivot_node",
                "node_component": "PivotTable",
                "unit_id": "pivot_1",
                "component_type": "u_pivot",
            }
        ]
        dataset_fields = [
            {
                "subject_id": 101,
                "model_type": 2,
                "field_count": 4,
                "fields": [
                    {"key": "formula_1"},
                    {"key": "grade"},
                    {"key": "a"},
                    {"key": "b"},
                ],
            }
        ]
        snapshot = build_dashboard_snapshot(
            dashboard_id="dashboard_3852445620602875904",
            dashboard_name="Dashboard",
            version_id="draft",
            html_id="html_1",
            domain="qingcheng",
            dashboard_html=dashboard_html(),
            pivot_units=[pivot],
            public_filters={"relation_1": public_filter_detail()},
            dataset_fields=dataset_fields,
        )
        return component_units, [pivot], snapshot, dataset_fields

    def test_real_operator_snapshot_normalizes_composite_filters_and_is_domain_bound(self) -> None:
        profile = raw_profile()
        normalized = normalize_profile(profile)
        self.assertEqual(normalized, normalize_profile(normalized))

        self.assertEqual(normalized["domain"], "qingcheng")
        self.assertEqual(len(normalized["public_filters"]), 2)
        self.assertEqual(len({item["filter_key"] for item in normalized["public_filters"]}), 2)
        self.assertTrue(all(item["filter_id"] == "public_filter_1" for item in normalized["public_filters"]))
        self.assertIn("pivot_node", {item["component_id"] for item in normalized["components"]})
        self.assertIn("pivot_node", {item["component_id"] for item in normalized["layout"]})
        pivot = next(item for item in normalized["components"] if item["component_id"] == "pivot_node")
        self.assertEqual("subject_101", pivot["dataset_id"])
        self.assertEqual(["formula_1"], pivot["formula_ids"])
        self.assertEqual("formula_1", pivot["fields"]["metrics"][0]["field_id"])
        self.assertEqual(["subject_101"], [item["dataset_id"] for item in normalized["datasets"]])

        other = raw_profile()
        other["domain"] = "market_consultant"
        other["snapshot"]["dashboard"]["domain"] = "market_consultant"
        self.assertNotEqual(normalized["profile_sha256"], normalize_profile(other)["profile_sha256"])

    def test_profile_edit_dashboard_keeps_legacy_rich_fields(self) -> None:
        config = {
            "dashboardId": "dashboard_3852445620602875904",
            "dashboardName": "Dashboard",
            "htmlId": "html_1",
            "dashboardHtmlJson": json.dumps(dashboard_html()),
        }
        pivot_detail = {
            "unitId": "pivot_1",
            "unitName": "Pivot",
            "unitType": "u_pivot",
            "modelId": "model_1",
            "modelName": "Lead model",
            "dashboardModel": {
                "subjectId": 101,
                "applicationModelId": "model_1",
                "modelType": 2,
            },
            "unitMeasureList": [],
        }
        fake_page = SimpleNamespace(url="https://example.invalid/?dashboardId=dashboard_3852445620602875904&htmlId=html_1")
        with tempfile.TemporaryDirectory() as temp_dir, patch(
            "read_dashboard.edit_profile.fetch_edit_dashboard_config", return_value=config
        ), patch(
            "read_dashboard.edit_profile.fetch_edit_unit_detail",
            side_effect=lambda _page, unit_id, _dashboard_id, _version: (
                public_filter_detail() if unit_id == "relation_1" else pivot_detail
            ),
        ):
            profile = profile_edit_dashboard(
                page=fake_page,
                dashboard_id="dashboard_3852445620602875904",
                html_id="html_1",
                edit_url=fake_page.url,
                version_id="draft",
                artifacts_dir=Path(temp_dir),
                debug_artifacts=False,
                include_dataset_fields=False,
                domain="qingcheng",
            )

        self.assertIn("components", profile)
        self.assertIn("pivot_units", profile)
        self.assertIn("dataset_fields", profile)
        self.assertIn("text_notes", profile)
        self.assertIn("snapshot", profile)
        self.assertIn("profile_sha256", profile)
        self.assertTrue(profile["complete"])
        self.assertEqual("complete", profile["completeness"]["status"])
        self.assertEqual("complete", profile["binding_validation"]["status"])

    def test_profile_binding_resolves_pivot_dataset_fields_formulas_and_filters(self) -> None:
        component_units, pivots, snapshot, dataset_fields = self.binding_fixture()
        validation = validate_pivot_bindings(
            component_units=component_units,
            pivot_units=pivots,
            snapshot=snapshot,
            dataset_fields=dataset_fields,
            include_dataset_fields=True,
        )

        self.assertEqual("complete", validation["status"])
        self.assertEqual(1, validation["validated_pivot_count"])
        self.assertEqual(0, validation["error_count"])

    def test_profile_binding_marks_dangling_dataset_formula_and_filter_references(self) -> None:
        component_units, pivots, snapshot, dataset_fields = self.binding_fixture()
        snapshot["datasets"] = []
        snapshot["formulas"] = []
        snapshot["component_filters"] = []
        validation = validate_pivot_bindings(
            component_units=component_units,
            pivot_units=pivots,
            snapshot=snapshot,
            dataset_fields=dataset_fields,
            include_dataset_fields=True,
        )

        codes = {item["code"] for item in validation["errors"]}
        self.assertEqual("incomplete", validation["status"])
        self.assertIn("PIVOT_DATASET_REFERENCE_DANGLING", codes)
        self.assertIn("PIVOT_FORMULA_REFERENCE_DANGLING", codes)
        self.assertIn("PIVOT_COMPONENT_FILTER_REFERENCE_DANGLING", codes)

    def test_profile_binding_marks_selected_field_absent_from_dataset(self) -> None:
        component_units, pivots, snapshot, dataset_fields = self.binding_fixture()
        dataset_fields[0]["fields"] = [
            item for item in dataset_fields[0]["fields"] if item["key"] != "formula_1"
        ]
        validation = validate_pivot_bindings(
            component_units=component_units,
            pivot_units=pivots,
            snapshot=snapshot,
            dataset_fields=dataset_fields,
            include_dataset_fields=True,
        )

        codes = {item["code"] for item in validation["errors"]}
        self.assertEqual("incomplete", validation["status"])
        self.assertIn("PIVOT_SELECTED_FIELD_DATASET_REFERENCE_DANGLING", codes)

    def test_profile_binding_marks_dangling_selected_field_reference(self) -> None:
        component_units, pivots, snapshot, dataset_fields = self.binding_fixture()
        pivots[0]["selected_fields"].append(
            {"key": "ghost_field", "changeParamType": None, "orgParamType": 1}
        )
        validation = validate_pivot_bindings(
            component_units=component_units,
            pivot_units=pivots,
            snapshot=snapshot,
            dataset_fields=dataset_fields,
            include_dataset_fields=True,
        )

        codes = {item["code"] for item in validation["errors"]}
        self.assertEqual("incomplete", validation["status"])
        self.assertIn("PIVOT_SELECTED_FIELD_REFERENCE_DANGLING", codes)

    def test_unbound_pivot_keeps_rich_profile_but_blocks_governed_chain(self) -> None:
        config = {
            "dashboardId": "dashboard_3852445620602875904",
            "dashboardName": "Dashboard",
            "htmlId": "html_1",
            "dashboardHtmlJson": json.dumps(dashboard_html()),
        }
        pivot_detail = {
            "unitId": "pivot_1",
            "unitName": "Pivot",
            "unitType": "u_pivot",
            "unitMeasureList": [],
        }
        fake_page = SimpleNamespace(url="https://example.invalid/?dashboardId=dashboard_3852445620602875904&htmlId=html_1")
        with tempfile.TemporaryDirectory() as temp_dir, patch(
            "read_dashboard.edit_profile.fetch_edit_dashboard_config", return_value=config
        ), patch(
            "read_dashboard.edit_profile.fetch_edit_unit_detail",
            side_effect=lambda _page, unit_id, _dashboard_id, _version: (
                public_filter_detail() if unit_id == "relation_1" else pivot_detail
            ),
        ):
            profile = profile_edit_dashboard(
                page=fake_page,
                dashboard_id="dashboard_3852445620602875904",
                html_id="html_1",
                edit_url=fake_page.url,
                version_id="draft",
                artifacts_dir=Path(temp_dir),
                debug_artifacts=False,
                include_dataset_fields=False,
                domain="qingcheng",
            )

        self.assertEqual(1, len(profile["pivot_units"]))
        self.assertFalse(profile["complete"])
        self.assertEqual("incomplete", profile["completeness"]["status"])
        self.assertIn(
            "PIVOT_DATASET_IDENTITY_UNRESOLVED",
            {item.get("code") for item in profile["binding_validation"]["errors"]},
        )
        with self.assertRaisesRegex(UsageError, "incomplete"):
            require_complete_profile(profile)

    def test_blank_and_non_data_components_do_not_fail_binding_validation(self) -> None:
        html = {
            "componentsTree": [
                {
                    "id": "root",
                    "componentName": "RootContentNew",
                    "children": [
                        {"id": "blank", "componentName": "EmptyContainer", "props": {}},
                        {
                            "id": "note",
                            "componentName": "TextBox",
                            "props": {
                                "settings": {
                                    "unitId": "text_1",
                                    "componentType": "u_text",
                                    "componentName": "Note",
                                }
                            },
                        },
                    ],
                }
            ]
        }
        config = {
            "dashboardId": "dashboard_3852445620602875904",
            "dashboardName": "Dashboard",
            "htmlId": "html_1",
            "dashboardHtmlJson": json.dumps(html),
        }
        fake_page = SimpleNamespace(url="https://example.invalid/?dashboardId=dashboard_3852445620602875904&htmlId=html_1")
        with tempfile.TemporaryDirectory() as temp_dir, patch(
            "read_dashboard.edit_profile.fetch_edit_dashboard_config", return_value=config
        ), patch(
            "read_dashboard.edit_profile.fetch_edit_unit_detail",
            return_value={"unitId": "text_1", "unitName": "Note", "unitType": "u_text"},
        ):
            profile = profile_edit_dashboard(
                page=fake_page,
                dashboard_id="dashboard_3852445620602875904",
                html_id="html_1",
                edit_url=fake_page.url,
                version_id="draft",
                artifacts_dir=Path(temp_dir),
                debug_artifacts=False,
                include_dataset_fields=True,
                domain="qingcheng",
            )

        self.assertTrue(profile["complete"])
        self.assertEqual("complete", profile["binding_validation"]["status"])
        self.assertEqual(0, profile["binding_validation"]["editable_pivot_count"])
        self.assertEqual(1, profile["binding_validation"]["ignored_non_data_component_count"])

    def test_incomplete_profile_is_saved_for_diagnosis_but_blocked_from_design(self) -> None:
        profile = raw_profile()
        profile["completeness"] = {
            "status": "incomplete",
            "required": ["components", "layout", "formulas", "public_filters", "component_filters", "datasets"],
            "observed": ["components", "layout", "formulas", "public_filters", "component_filters", "datasets"],
            "missing": [],
            "reasons": ["unit:pivot_1:timeout"],
            "details": {"errors": [{"category": "unit", "unit_id": "pivot_1"}]},
        }
        with self.assertRaisesRegex(UsageError, "incomplete"):
            require_complete_profile(profile)


class StableFilterApplyTests(unittest.TestCase):
    def test_stable_ids_update_only_the_target_field(self) -> None:
        detail = public_filter_detail()
        before_period = public_filter_field_state(detail["unitList"][0], "period")

        updated, results = apply_stable_public_filter_operations(
            detail,
            "relation_1",
            [filter_operation()],
        )

        unit = updated["unitList"][0]
        self.assertEqual(public_filter_field_state(unit, "period"), before_period)
        self.assertEqual(public_filter_field_state(unit, "grade")["dynamics_filter_value"], "2")
        self.assertTrue(results[0]["ok"])

    def test_immediate_filter_state_must_match_plan_before(self) -> None:
        plan = governed_filter_plan()
        operation = plan["operations"][0]
        detail = public_filter_detail()
        target_field = str(operation["target"]["field_id"])
        for field in detail["unitList"][0]["format"]["unitConfig"]["unitDimensionList"]:
            if field["fieldId"] == target_field:
                field["format"]["dynamicsFilterValue"] = "concurrent-change"
        with self.assertRaisesRegex(UsageError, "state drifted before apply"):
            assert_stable_public_filter_preconditions(
                detail,
                str(operation["target"]["relation_id"]),
                [operation],
            )

    def test_preflight_blocks_unsupported_and_multi_relation_without_browser(self) -> None:
        unsupported = governed_layout_plan()
        with self.assertRaisesRegex(UsageError, "blocked"):
            preflight_apply_plan(unsupported, unsupported["change_plan_sha256"], expected_domain="qingcheng")

        multi = governed_filter_plan(relation_count=2)
        with self.assertRaisesRegex(UsageError, "only one public-filter relation"):
            preflight_apply_plan(multi, multi["change_plan_sha256"], expected_domain="qingcheng")

    def test_no_changes_plan_and_receipt_cannot_apply_or_publish(self) -> None:
        plan = governed_noop_plan()
        with self.assertRaisesRegex(UsageError, "ready_for_dry_run"):
            preflight_apply_plan(plan, plan["change_plan_sha256"], expected_domain="qingcheng")

        receipt = {
            "artifact_type": "dashboard_apply_receipt",
            "domain": "qingcheng",
            "dashboard_id": "dashboard_3852445620602875904",
            "status": "no_changes",
            "ok": True,
            "operations": [],
        }
        receipt["apply_receipt_sha256"] = artifact_sha256(receipt, "apply_receipt_sha256")
        with self.assertRaisesRegex(UsageError, "not successful"):
            preflight_publish_receipt(
                receipt,
                plan,
                receipt["apply_receipt_sha256"],
                expected_domain="qingcheng",
                confirmed=True,
            )

    def test_malformed_self_authorized_plan_and_unbound_receipt_are_blocked(self) -> None:
        plan = governed_filter_plan()
        plan["authorization"]["apply_authorized"] = True
        plan["change_plan_sha256"] = artifact_sha256(plan, "change_plan_sha256")
        with self.assertRaisesRegex(UsageError, "shared-core policy validation"):
            preflight_apply_plan(plan, plan["change_plan_sha256"], expected_domain="qingcheng")

        valid_plan = governed_filter_plan()
        receipt = {
            "artifact_type": "dashboard_apply_receipt",
            "domain": "qingcheng",
            "dashboard_id": "dashboard_3852445620602875904",
            "change_plan_sha256": "wrong",
            "status": "applied",
            "ok": True,
            "operations": [{"operation_id": valid_plan["operations"][0]["operation_id"], "status": "applied"}],
            "verification": {"profile_readback_performed": True, "target_state_matches": True},
        }
        receipt["apply_receipt_sha256"] = artifact_sha256(receipt, "apply_receipt_sha256")
        with self.assertRaisesRegex(UsageError, "shared-core plan binding"):
            preflight_publish_receipt(
                receipt,
                valid_plan,
                receipt["apply_receipt_sha256"],
                expected_domain="qingcheng",
                confirmed=True,
            )

    def test_design_to_plan_preflight_uses_real_snapshot_shape(self) -> None:
        profile = raw_profile()
        normalized = normalize_profile(profile)
        desired_filters = json.loads(json.dumps(normalized["public_filters"]))
        desired_filters[0]["default_value"] = "2"
        desired_filters[0]["dynamic_default"] = True
        desired = {"public_filters": desired_filters}
        design = build_design_spec(
            dataset_spec(),
            profile,
            desired,
            query_plan_sha256="a" * 64,
            design_intent="change one dynamic default",
        )
        plan = build_change_plan(profile, design)

        self.assertEqual(plan["status"], "ready_for_dry_run")
        self.assertEqual(len(plan["operations"]), 1)
        self.assertEqual(plan["operations"][0]["type"], "update_filter_dynamic_default")
        preflight_apply_plan(plan, plan["change_plan_sha256"], expected_domain="qingcheng")


class DesignCommandBoundaryTests(unittest.TestCase):
    def test_blocked_design_returns_nonzero_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            profile_path = root / "profile.json"
            dataset_path = root / "dataset.json"
            output_path = root / "design.json"
            profile_path.write_text(json.dumps(raw_profile()), encoding="utf-8")
            dataset = dataset_spec()
            dataset["status"] = "draft"
            dataset["dataset_spec_sha256"] = artifact_sha256(
                dataset,
                "dataset_spec_sha256",
            )
            dataset_path.write_text(json.dumps(dataset), encoding="utf-8")
            args = SimpleNamespace(
                profile=profile_path,
                dataset_spec=dataset_path,
                desired_state=None,
                domain="qingcheng",
                query_plan_sha256="a" * 64,
                design_intent="blocked test",
                output=output_path,
            )
            self.assertEqual(1, cmd_design_dashboard(args))
            artifact = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual("blocked", artifact["status"])


class ApplyReadbackTests(unittest.TestCase):
    def test_profile_drift_blocks_before_update_call(self) -> None:
        plan = governed_filter_plan()
        fake_page = SimpleNamespace(
            url="https://example.invalid/?dashboardId=dashboard_3852445620602875904&htmlId=html_1",
            wait_for_timeout=lambda _value: None,
        )
        args = SimpleNamespace(domain="qingcheng", wait_ms=0, debug_artifacts=False)
        with patch("read_dashboard.dashboard_change.open_edit_page"), patch(
            "read_dashboard.dashboard_change._read_current_profile", return_value={}
        ), patch(
            "read_dashboard.dashboard_change.normalize_profile",
            return_value={
                "profile_sha256": "c" * 64,
                "completeness": {"status": "complete"},
            },
        ), patch(
            "read_dashboard.dashboard_change.update_public_filter_detail"
        ) as update_call:
            with self.assertRaisesRegex(UsageError, "profile drifted"):
                apply_change_plan_to_draft(
                    page=fake_page,
                    args=args,
                    plan=plan,
                    supplied_sha256=plan["change_plan_sha256"],
                    artifacts_dir=Path("."),
                )
        update_call.assert_not_called()

    def test_apply_updates_once_then_uses_post_profile_readback_for_receipt(self) -> None:
        plan = governed_filter_plan()
        pre_profile = {
            "profile_sha256": plan["base_profile_sha256"],
            "domain": "qingcheng",
            "dashboard_id": "dashboard_3852445620602875904",
            "completeness": {"status": "complete"},
        }
        post_profile = {
            "profile_sha256": "c" * 64,
            "domain": "qingcheng",
            "dashboard_id": "dashboard_3852445620602875904",
            "completeness": {"status": "complete"},
        }
        fake_page = SimpleNamespace(
            url="https://example.invalid/?dashboardId=dashboard_3852445620602875904&htmlId=html_1",
            wait_for_timeout=lambda _value: None,
        )
        args = SimpleNamespace(domain="qingcheng", wait_ms=0, debug_artifacts=False)

        class FakeCore:
            @staticmethod
            def canonical_sha256(value):
                import hashlib

                raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                return hashlib.sha256(raw.encode("utf-8")).hexdigest()

            @staticmethod
            def artifact_sha256(value, field_name):
                import hashlib

                payload = dict(value)
                payload.pop(field_name, None)
                raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                return hashlib.sha256(raw.encode("utf-8")).hexdigest()

            @staticmethod
            def validate_dashboard_change_plan(_plan, current_profile=None):
                return []

            @staticmethod
            def build_apply_receipt(_plan, current, operation_results=None):
                self.assertIs(current, post_profile)
                self.assertEqual(operation_results[0]["status"], "applied")
                return {
                    "artifact_type": "dashboard_apply_receipt",
                    "domain": "qingcheng",
                    "dashboard_id": "dashboard_3852445620602875904",
                    "change_plan_sha256": _plan["change_plan_sha256"],
                    "post_profile_sha256": current["profile_sha256"],
                    "operations": operation_results,
                    "status": "applied",
                    "ok": True,
                    "apply_receipt_sha256": "d" * 64,
                }

            @staticmethod
            def validate_apply_receipt(_receipt, _plan, post_profile=None):
                self.assertIs(post_profile, after_profile)
                return []

        after_profile = post_profile

        with patch("read_dashboard.dashboard_change.open_edit_page"), patch(
            "read_dashboard.dashboard_change._read_current_profile", side_effect=[{"raw": 1}, {"raw": 2}]
        ) as readback, patch(
            "read_dashboard.dashboard_change.normalize_profile", side_effect=[pre_profile, post_profile]
        ), patch(
            "read_dashboard.dashboard_change.fetch_public_filter_detail", return_value=public_filter_detail()
        ), patch(
            "read_dashboard.dashboard_change.update_public_filter_detail",
            return_value={"status": "success"},
        ) as update_call, patch(
            "read_dashboard.dashboard_change._core_api", return_value=FakeCore()
        ):
            receipt, before, after = apply_change_plan_to_draft(
                page=fake_page,
                args=args,
                plan=plan,
                supplied_sha256=plan["change_plan_sha256"],
                artifacts_dir=Path("."),
            )

        self.assertTrue(receipt["ok"])
        self.assertIs(before, pre_profile)
        self.assertIs(after, post_profile)
        self.assertEqual(readback.call_count, 2)
        update_call.assert_called_once()


class PublishReadbackTests(unittest.TestCase):
    @staticmethod
    def args() -> SimpleNamespace:
        return SimpleNamespace(
            domain="qingcheng",
            confirm_publish=True,
            wait_ms=0,
            debug_artifacts=False,
            version_description="reviewed change",
        )

    @staticmethod
    def config() -> dict:
        return {
            "dashboardId": "dashboard_3852445620602875904",
            "dashboardName": "Dashboard",
            "dashboardHtmlJson": json.dumps(dashboard_html()),
            "ownerList": [],
        }

    def test_publish_requires_immediate_profile_stability_before_api_call(self) -> None:
        plan, post_profile, receipt = governed_applied_receipt()
        drifted = json.loads(json.dumps(post_profile))
        drifted["components"][0]["title"] = "concurrent edit"
        drifted = normalize_profile(drifted)
        fake_page = SimpleNamespace(
            url="https://example.invalid/?dashboardId=dashboard_3852445620602875904&htmlId=html_1",
            wait_for_timeout=lambda _value: None,
        )
        with patch("read_dashboard.dashboard_change.open_edit_page"), patch(
            "read_dashboard.dashboard_change._read_current_profile",
            side_effect=[post_profile, drifted],
        ), patch(
            "read_dashboard.dashboard_change.fetch_edit_config",
            return_value=self.config(),
        ), patch(
            "read_dashboard.dashboard_change.publish_dashboard"
        ) as publish_call:
            with self.assertRaisesRegex(UsageError, "changed immediately before publish"):
                publish_applied_draft(
                    page=fake_page,
                    args=self.args(),
                    apply_receipt=receipt,
                    change_plan=plan,
                    supplied_sha256=receipt["apply_receipt_sha256"],
                    artifacts_dir=Path("."),
                )
        publish_call.assert_not_called()

    def test_successful_publish_requires_post_publish_draft_readback(self) -> None:
        plan, post_profile, receipt = governed_applied_receipt()
        fake_page = SimpleNamespace(
            url="https://example.invalid/?dashboardId=dashboard_3852445620602875904&htmlId=html_1",
            wait_for_timeout=lambda _value: None,
        )
        with patch("read_dashboard.dashboard_change.open_edit_page"), patch(
            "read_dashboard.dashboard_change._read_current_profile",
            side_effect=[post_profile, post_profile, post_profile],
        ) as profile_read, patch(
            "read_dashboard.dashboard_change.fetch_edit_config",
            side_effect=[self.config(), self.config()],
        ), patch(
            "read_dashboard.dashboard_change.publish_dashboard",
            return_value={"publish_status": "success"},
        ) as publish_call:
            publish_receipt = publish_applied_draft(
                page=fake_page,
                args=self.args(),
                apply_receipt=receipt,
                change_plan=plan,
                supplied_sha256=receipt["apply_receipt_sha256"],
                artifacts_dir=Path("."),
            )
        self.assertTrue(publish_receipt["ok"])
        self.assertTrue(publish_receipt["readback_performed"])
        self.assertEqual(
            "publish_requested_unverified",
            publish_receipt["publish_status"],
        )
        self.assertEqual(
            "draft_only_unverified_published_version",
            publish_receipt["verification_status"],
        )
        self.assertFalse(publish_receipt["fully_verified"])
        self.assertFalse(publish_receipt["published_version_readback_performed"])
        self.assertEqual(
            post_profile["profile_sha256"],
            publish_receipt["post_publish_draft_profile_sha256"],
        )
        self.assertEqual(3, profile_read.call_count)
        publish_call.assert_called_once()


class CliBoundaryTests(unittest.TestCase):
    def test_apply_command_has_no_publish_switch(self) -> None:
        parser = build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(
                [
                    "apply-dashboard-change",
                    "--change-plan",
                    "plan.json",
                    "--change-plan-sha256",
                    "a" * 64,
                    "--domain",
                    "qingcheng",
                    "--publish",
                ]
            )


if __name__ == "__main__":
    unittest.main()
