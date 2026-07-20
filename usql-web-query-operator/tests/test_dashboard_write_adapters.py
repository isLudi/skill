from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from _shared.errors import UsageError  # noqa: E402
from read_dashboard.dashboard_write_adapters import (  # noqa: E402
    ADAPTERS,
    ReversibleAdapter,
    apply_adapter_target,
    assert_expected_state,
    canonical_sha256,
    find_filter_formats,
    planned_operation_target,
)


class DashboardWriteAdapterTests(unittest.TestCase):
    def test_redacted_live_evidence_covers_all_reversible_adapters(self) -> None:
        evidence_path = SKILL_ROOT / "tests" / "fixtures" / "p4a_sandbox_adapter_evidence.json"
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        self.assertTrue(evidence["restored_to_baseline"])
        self.assertEqual(evidence["expected_profile_sha256"], evidence["final_profile_sha256"])
        by_operation = {item["operation"]: item for item in evidence["operations"]}
        self.assertEqual(set(ADAPTERS), set(by_operation))
        for operation, item in by_operation.items():
            with self.subTest(operation=operation):
                self.assertTrue(item["drift_blocked_without_write"])
                self.assertTrue(item["restored"])
                self.assertGreaterEqual(len(item["write_response_statuses"]), 2)
                self.assertTrue(all(status == 200 for status in item["write_response_statuses"]))
                self.assertEqual(
                    len(item["write_response_statuses"]), len(item["payload_sha256"])
                )

    def test_redacted_p4b_evidence_proves_forward_and_reverse_transaction_order(self) -> None:
        evidence = json.loads(
            (SKILL_ROOT / "tests" / "fixtures" / "p4b_sandbox_transaction_evidence.json")
            .read_text(encoding="utf-8")
        )
        forward = [item["operation"] for item in evidence["operations"]]
        self.assertEqual("verified_and_restored", evidence["transaction"]["status"])
        self.assertEqual(forward, evidence["transaction"]["applied_operations"])
        self.assertEqual(list(reversed(forward)), evidence["transaction"]["restored_operations"])
        self.assertEqual(evidence["expected_profile_sha256"], evidence["final_profile_sha256"])

    def test_drift_guard_rejects_before_write(self) -> None:
        state = {"x": 1}
        with self.assertRaisesRegex(UsageError, "no write was attempted"):
            assert_expected_state(state, "0" * 64, "layout")
        assert_expected_state(state, canonical_sha256(state), "layout")

    def test_layout_adapter_changes_and_restores_only_target_layout(self) -> None:
        adapter = ADAPTERS["update_layout"]
        target = {"node_id": "node_a", "probe_patch": {"static": True}}
        before = {
            "componentsTree": [
                {"props": {"layout": [{"i": ".$node_a", "x": 0, "y": 1, "w": 5, "h": 6, "static": False}]}}
            ]
        }
        changed = adapter.mutate(copy.deepcopy(before), target)
        self.assertTrue(adapter.project(changed, target)["static"])
        changed["unrelated"] = "preserve"
        restored = adapter.restore(changed, before, target)
        self.assertEqual(adapter.project(before, target), adapter.project(restored, target))
        self.assertEqual("preserve", restored["unrelated"])

    def test_component_adapter_uses_stable_unit_group_and_field_id(self) -> None:
        adapter = ADAPTERS["update_component_fields"]
        target = {
            "unit_id": "unit_1",
            "field_group": "unitMeasureList",
            "field_id": "metric_1",
            "probe_show_name": "Metric P4A",
        }
        before = {
            "unitId": "unit_1",
            "unitMeasureList": [{"fieldId": "metric_1", "showName": "Metric"}],
        }
        changed = adapter.mutate(copy.deepcopy(before), target)
        self.assertEqual("Metric P4A", adapter.project(changed, target)["show_name"])
        restored = adapter.restore(changed, before, target)
        self.assertEqual("Metric", adapter.project(restored, target)["show_name"])

    def test_component_filter_label_adapter_is_limited_to_unit_filter_show_name(self) -> None:
        adapter = ADAPTERS["update_component_filter_label"]
        target = {
            "unit_id": "unit_1",
            "field_group": "unitFilterList",
            "field_id": "dimension_1",
            "probe_show_name": "Owner",
        }
        before = {
            "unitId": "unit_1",
            "unitFilterList": [
                {"fieldId": "dimension_1", "showName": "Manager", "format": {"condition": "in"}}
            ],
        }
        changed = adapter.mutate(copy.deepcopy(before), target)
        self.assertEqual("Owner", adapter.project(changed, target)["show_name"])
        self.assertEqual("in", changed["unitFilterList"][0]["format"]["condition"])
        restored = adapter.restore(changed, before, target)
        self.assertEqual("Manager", adapter.project(restored, target)["show_name"])

    def test_component_title_adapter_updates_schema_and_unit_name_together(self) -> None:
        adapter = ADAPTERS["update_component_title"]
        target = {
            "component_id": "node_1",
            "unit_id": "unit_1",
            "probe_title": "Owner analysis",
        }
        before = {
            "schema": {
                "componentsTree": [
                    {
                        "id": "node_1",
                        "componentName": "PivotTable",
                        "props": {"settings": {"componentName": "Manager analysis", "unitId": "unit_1"}},
                    }
                ]
            },
            "unit": {"unitId": "unit_1", "unitName": "Manager analysis"},
        }
        changed = adapter.mutate(copy.deepcopy(before), target)
        self.assertEqual("Owner analysis", adapter.project(changed, target)["schema_title"])
        self.assertEqual("Owner analysis", adapter.project(changed, target)["unit_name"])
        restored = adapter.restore(changed, before, target)
        self.assertEqual(adapter.project(before, target), adapter.project(restored, target))

    def test_ambiguous_partial_write_is_compensated_before_error_returns(self) -> None:
        state = {"value": "before"}
        write_count = 0

        def read(_page, _dashboard_id, _target):
            return copy.deepcopy(state)

        def project(raw, _target):
            return {"value": raw["value"]}

        def mutate(raw, _target):
            raw["value"] = "after"
            return raw

        def restore(current, before, _target):
            current["value"] = before["value"]
            return current

        def write(_page, _dashboard_id, _dashboard_name, raw, _observations):
            nonlocal write_count
            write_count += 1
            state.update(copy.deepcopy(raw))
            if write_count == 1:
                raise UsageError("ambiguous transport failure")
            return {"status": "success"}

        operation = "test_partial_compensation"
        ADAPTERS[operation] = ReversibleAdapter(
            operation, read, project, mutate, restore, write, lambda expected, actual, _target: expected == actual
        )
        try:
            with self.assertRaisesRegex(UsageError, "any observed write was restored"):
                apply_adapter_target(
                    page=None,
                    dashboard_id="dashboard_1",
                    dashboard_name="sandbox",
                    operation_id="op_1",
                    operation_type=operation,
                    target={},
                )
        finally:
            ADAPTERS.pop(operation, None)
        self.assertEqual({"value": "before"}, state)
        self.assertEqual(2, write_count)

    def test_tab_label_adapter_uses_component_slot_key_and_slot_id(self) -> None:
        adapter = ADAPTERS["update_tab_label"]
        target = {
            "component_id": "tabs_1",
            "slot_key": "manager",
            "slot_id": "slot_node_1",
            "probe_label": "Owner",
        }
        before = {
            "componentsTree": [
                {
                    "id": "tabs_1",
                    "componentName": "SingleTabs",
                    "props": {
                        "list": [
                            {
                                "key": "manager",
                                "label": "Manager",
                                "children": {"id": "slot_node_1", "name": "slot_a", "value": []},
                            },
                            {
                                "key": "team",
                                "label": "Team",
                                "children": {"id": "slot_node_2", "name": "slot_b", "value": []},
                            },
                        ]
                    },
                }
            ]
        }
        changed = adapter.mutate(copy.deepcopy(before), target)
        self.assertEqual("Owner", adapter.project(changed, target)["label"])
        self.assertEqual("Team", changed["componentsTree"][0]["props"]["list"][1]["label"])
        restored = adapter.restore(changed, before, target)
        self.assertEqual("Manager", adapter.project(restored, target)["label"])

    def test_public_filter_title_adapter_uses_stable_filter_triple(self) -> None:
        adapter = ADAPTERS["update_public_filter_title"]
        target = {
            "relation_id": "public_filter_relation_1",
            "filter_id": "public_filter_1",
            "field_id": "field_1",
            "probe_title": "Owner",
        }
        before = {
            "unitList": [
                {
                    "unitList": [
                        {
                            "unitId": "public_filter_1",
                            "unitName": "Manager",
                            "format": {
                                "unitConfig": {
                                    "unitDimensionList": [
                                        {
                                            "filterUnitId": "public_filter_1",
                                            "fieldId": "field_1",
                                            "format": {},
                                        }
                                    ]
                                }
                            },
                        }
                    ]
                }
            ]
        }
        changed = adapter.mutate(copy.deepcopy(before), target)
        self.assertEqual("Owner", adapter.project(changed, target)["title"])
        restored = adapter.restore(changed, before, target)
        self.assertEqual("Manager", adapter.project(restored, target)["title"])

    def test_formula_projection_ignores_volatile_server_metadata(self) -> None:
        adapter = ADAPTERS["update_formula"]
        target = {"formula_id": "customized_1", "probe_formula": "(sum(${x}))"}
        before = {
            "subjectId": 1,
            "columnKey": "customized_1",
            "columnName": "Metric",
            "columnDesc": "",
            "dataType": 1,
            "formula": "sum(${x})",
            "dependencyIndicators": [{"paramId": "x", "orgParamType": 1}],
            "updateTime": 1,
        }
        server_readback = copy.deepcopy(before)
        server_readback["updateTime"] = 2
        self.assertEqual(adapter.project(before, target), adapter.project(server_readback, target))
        changed = adapter.mutate(copy.deepcopy(before), target)
        restored = adapter.restore(changed, before, target)
        self.assertEqual("sum(${x})", restored["formula"])

    def test_filter_recovery_clears_server_derived_cache_fields(self) -> None:
        adapter = ADAPTERS["update_filter_dynamic_default"]
        target = {
            "relation_id": "relation_1",
            "filter_id": "filter_1",
            "field_id": "field_1",
            "probe_value": "2",
        }
        before_format = {
            "dynamicsFilter": False,
            "autoSearchDefaultValue": False,
            "filterValue": [],
            "defaultFilterValue": [],
        }
        before = {
            "unitList": [
                {
                    "unitList": [
                        {
                            "format": {
                                "unitConfig": {
                                    "unitDimensionList": [
                                        {"filterUnitId": "filter_1", "fieldId": "field_1", "format": copy.deepcopy(before_format)}
                                    ]
                                }
                            },
                            "relationUnit": {
                                "unitConfig": {
                                    "unitDimensionList": [
                                        {"filterUnitId": "filter_1", "fieldId": "field_1", "format": copy.deepcopy(before_format)}
                                    ]
                                }
                            },
                        }
                    ]
                }
            ]
        }
        changed = adapter.mutate(copy.deepcopy(before), target)
        for fmt in find_filter_formats(changed, "filter_1", "field_1"):
            fmt["filterValue"] = ["20260710期"]
            fmt["preFilterValueList"] = ["20260710期"]
            fmt["preFilterTaskId"] = "task_1"
        restored = adapter.restore(changed, before, target)
        for fmt in find_filter_formats(restored, "filter_1", "field_1"):
            self.assertFalse(fmt["dynamicsFilter"])
            self.assertEqual([], fmt["filterValue"])
            self.assertEqual([], fmt["preFilterValueList"])
            self.assertIsNone(fmt["preFilterTaskId"])

    def test_filter_after_match_tolerates_only_server_derived_cache_changes(self) -> None:
        adapter = ADAPTERS["update_filter_dynamic_default"]
        target = {
            "relation_id": "relation_1",
            "filter_id": "filter_1",
            "field_id": "field_1",
            "probe_value": "2",
        }
        expected = {
            "copies": [
                {
                    "dynamicsFilter": True,
                    "dynamicsFilterValue": "2",
                    "autoSearchDefaultValue": False,
                    "filterValue": [],
                }
            ]
        }
        actual = copy.deepcopy(expected)
        actual["copies"][0]["filterValue"] = ["20260710期"]
        actual["copies"][0]["preFilterValueList"] = ["20260710期"]
        self.assertTrue(adapter.after_matches(expected, actual, target))
        actual["copies"][0]["dynamicsFilterValue"] = "3"
        self.assertFalse(adapter.after_matches(expected, actual, target))

    def test_theme_adapter_preserves_non_theme_schema(self) -> None:
        adapter = ADAPTERS["update_theme"]
        target = {"probe_value": "#f2f3f6"}
        before = {
            "componentsTree": [{"props": {"style": {"backgroundColor": "#f2f3f5"}}}],
            "config": {"themeType": "default", "styleId": "theme_1"},
            "unrelated": {"keep": True},
        }
        changed = adapter.mutate(copy.deepcopy(before), target)
        self.assertEqual("#f2f3f6", adapter.project(changed, target)["backgroundColor"])
        restored = adapter.restore(changed, before, target)
        self.assertEqual(adapter.project(before, target), adapter.project(restored, target))
        self.assertTrue(restored["unrelated"]["keep"])

    def test_change_plan_operations_map_to_minimal_adapter_targets(self) -> None:
        layout = planned_operation_target(
            {
                "type": "update_layout",
                "target": {"component_id": "node_1"},
                "before": {"x": 0, "y": 0, "w": 10, "h": 8},
                "after": {"x": 1, "y": 0, "w": 10, "h": 8},
            }
        )
        self.assertEqual("node_1", layout["node_id"])
        self.assertEqual({"x": 1}, layout["probe_patch"])

        component = planned_operation_target(
            {
                "type": "update_component_fields",
                "target": {
                    "component_id": "node_1",
                    "unit_id": "unit_1",
                    "field_group": "unitMeasureList",
                    "field_id": "metric_1",
                },
                "after": {
                    "fields": {
                        "dimensions": [],
                        "metrics": [
                            {"field_id": "metric_1", "display_name": "Renamed"}
                        ],
                    }
                },
            }
        )
        self.assertEqual("Renamed", component["probe_show_name"])

        component_filter = planned_operation_target(
            {
                "type": "update_component_filter_label",
                "target": {
                    "unit_id": "unit_1",
                    "field_group": "unitFilterList",
                    "field_id": "dimension_1",
                },
                "after": {"business_name": "Owner"},
            }
        )
        self.assertEqual("Owner", component_filter["probe_show_name"])

        component_title = planned_operation_target(
            {
                "type": "update_component_title",
                "target": {"component_id": "node_1", "unit_id": "unit_1"},
                "after": {"title": "Owner analysis"},
            }
        )
        self.assertEqual("Owner analysis", component_title["probe_title"])

        public_title = planned_operation_target(
            {
                "type": "update_public_filter_title",
                "target": {
                    "relation_id": "relation_1",
                    "filter_id": "filter_1",
                    "field_id": "field_1",
                },
                "after": {"title": "Owner"},
            }
        )
        self.assertEqual("Owner", public_title["probe_title"])

        tab_label = planned_operation_target(
            {
                "type": "update_tab_label",
                "target": {
                    "component_id": "tabs_1",
                    "slot_key": "manager",
                    "slot_id": "slot_node_1",
                },
                "after": {
                    "config": {
                        "slots": [
                            {
                                "key": "manager",
                                "slot_id": "slot_node_1",
                                "label": "Owner",
                            }
                        ]
                    }
                },
            }
        )
        self.assertEqual("Owner", tab_label["probe_label"])

        formula = planned_operation_target(
            {
                "type": "update_formula",
                "target": {"formula_id": "customized_1"},
                "after": {"expression": "sum(${x})"},
            }
        )
        self.assertEqual("sum(${x})", formula["probe_formula"])

        theme = planned_operation_target(
            {
                "type": "update_theme",
                "target": {"scope": "dashboard_root"},
                "after": {"background_color": "#f2f3f6"},
            }
        )
        self.assertEqual("#f2f3f6", theme["probe_value"])


if __name__ == "__main__":
    unittest.main()
