from __future__ import annotations

import sys
import unittest
from types import SimpleNamespace
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from _shared.errors import UsageError  # noqa: E402
from read_dashboard.pivot_rebind import (  # noqa: E402
    assert_filtered_value_response,
    normalize_filtered_value_checks,
    project_unit_field_state,
    rebuild_pivot_unit_fields,
)
from read_dashboard.cli import build_parser  # noqa: E402
from read_dashboard.commands.rebind_pivot_fields_sandbox import (  # noqa: E402
    _count_component_unit_refs,
    _execution_mode,
    _replace_component_unit_id,
)


def field(field_id: str, name: str, show_name: str | None = None) -> dict[str, object]:
    return {
        "fieldId": field_id,
        "name": name,
        "showName": show_name or name,
        "fieldType": 1,
        "orgParamType": 1,
        "format": {"sortValue": "NONE"},
    }


class PivotRebindTests(unittest.TestCase):
    def test_production_rebind_has_no_cli_entrypoint(self) -> None:
        parser = build_parser()
        subparsers = next(
            action for action in parser._actions if action.__class__.__name__ == "_SubParsersAction"
        )
        self.assertIn("rebind-pivot-fields-sandbox", subparsers.choices)
        self.assertNotIn("rebind-pivot-fields-production", subparsers.choices)

    def test_rebuild_uses_source_measures_and_target_dimension_display(self) -> None:
        target = {
            "unitId": "unit_target",
            "unitName": "channel1",
            "modelId": "2064",
            "unitDimensionList": [
                field("channel_map_1", "channel_map_1", "channel"),
                field("old_dept", "old_dept", "old dept"),
            ],
            "unitColumnDimensionList": [field("legacy_col", "legacy_col")],
            "unitMeasureList": [field("v_lead", "v_lead", "old lead")],
            "unitAideMeasureList": [],
            "unitFilterList": [field("qici", "qici")],
        }
        source = {
            "unitId": "unit_source",
            "unitName": "channel2",
            "modelId": "2064",
            "unitDimensionList": [
                field("channel_map_1", "channel_map_1", "level1"),
                field("channel_map_2", "channel_map_2", "level2"),
                field("dept_2", "dept_2", "dept"),
            ],
            "unitColumnDimensionList": [],
            "unitMeasureList": [
                field("v_lead", "v_lead", "lead"),
                field("call_8min_user_cnt", "call_8min_user_cnt", "8min"),
            ],
            "unitAideMeasureList": [field("friend_rate", "friend_rate")],
            "unitFilterList": [field("qici", "qici")],
        }

        rebuilt = rebuild_pivot_unit_fields(
            target_detail=target,
            source_detail=source,
            dimension_field_ids=["channel_map_1", "dept_2"],
            required_measure_field_ids=["v_lead", "call_8min_user_cnt"],
        )

        state = project_unit_field_state(rebuilt)
        self.assertEqual(
            ["channel_map_1", "dept_2"],
            [item["field_id"] for item in state["groups"]["unitDimensionList"]],
        )
        self.assertEqual("channel", rebuilt["unitDimensionList"][0]["showName"])
        self.assertEqual([], rebuilt["unitColumnDimensionList"])
        self.assertEqual(
            ["v_lead", "call_8min_user_cnt"],
            [item["field_id"] for item in state["groups"]["unitMeasureList"]],
        )
        self.assertEqual(["friend_rate"], [item["field_id"] for item in state["groups"]["unitAideMeasureList"]])
        self.assertEqual(["qici"], [item["field_id"] for item in state["groups"]["unitFilterList"]])

    def test_model_mismatch_blocks_rebuild(self) -> None:
        with self.assertRaisesRegex(UsageError, "model mismatch"):
            rebuild_pivot_unit_fields(
                target_detail={"modelId": "2064", "unitDimensionList": [], "unitMeasureList": []},
                source_detail={"modelId": "9999", "unitDimensionList": [], "unitMeasureList": []},
                dimension_field_ids=["channel_map_1"],
            )

    def test_missing_required_measure_blocks_rebuild(self) -> None:
        with self.assertRaisesRegex(UsageError, "Required measure fields"):
            rebuild_pivot_unit_fields(
                target_detail={
                    "modelId": "2064",
                    "unitDimensionList": [field("channel_map_1", "channel_map_1")],
                    "unitMeasureList": [],
                },
                source_detail={
                    "modelId": "2064",
                    "unitDimensionList": [field("channel_map_1", "channel_map_1")],
                    "unitMeasureList": [],
                },
                dimension_field_ids=["channel_map_1"],
                required_measure_field_ids=["v_lead"],
            )

    def test_component_unit_replacement_counts_logical_components(self) -> None:
        schema = {
            "componentsTree": [
                {
                    "id": "node_1",
                    "componentName": "Pivot",
                    "settings": {"unitId": "unit_old"},
                    "props": {"settings": {"unitId": "unit_old"}},
                },
                {
                    "id": "node_2",
                    "componentName": "Pivot",
                    "props": {"settings": {"unitId": "unit_other"}},
                },
            ]
        }
        self.assertEqual(1, _replace_component_unit_id(schema, "unit_old", "unit_new"))
        self.assertEqual(0, _count_component_unit_refs(schema, "unit_old"))
        self.assertEqual(1, _count_component_unit_refs(schema, "unit_new"))
        self.assertEqual("unit_new", schema["componentsTree"][0]["settings"]["unitId"])
        self.assertEqual("unit_new", schema["componentsTree"][0]["props"]["settings"]["unitId"])

    def test_strict_validation_requires_filtered_value_checks(self) -> None:
        manifest = {
            "artifact_type": "DashboardPivotFieldRebindManifest",
            "schema_version": "1.0.0",
        }
        operations = [{"operation_id": "channel1_overall"}]
        with self.assertRaisesRegex(UsageError, "requires filtered_value_checks"):
            normalize_filtered_value_checks(manifest, operations, require=True)

    def test_production_execution_mode_is_blocked_before_browser_launch(self) -> None:
        args = SimpleNamespace(
            confirm_production_write=True,
            confirm_sandbox_write=False,
        )
        with self.assertRaisesRegex(UsageError, "blocked_unsupported"):
            _execution_mode(args, {})

    def test_filtered_value_checks_require_period_public_filter(self) -> None:
        operations = [{"operation_id": "channel1_overall"}]
        base_manifest = {
            "artifact_type": "DashboardPivotFieldRebindManifest",
            "schema_version": "1.0.0",
            "required_public_filters": [
                {
                    "field_id": "qici",
                    "expected_values": ["20260722期"],
                }
            ],
            "filtered_value_checks": [
                {
                    "check_id": "channel1_book_sec_20260722",
                    "operation_id": "channel1_overall",
                    "public_filter_list": [
                        {
                            "fieldId": "qici",
                            "filterValue": ["20260722期"],
                        }
                    ],
                    "row_match": {
                        "channel_map_1": "图书",
                        "dept_2": "SEC",
                    },
                    "measure_field_id": "v_lead",
                    "expected_value": 55,
                }
            ],
        }

        checks = normalize_filtered_value_checks(base_manifest, operations, require=True)
        self.assertEqual(1, len(checks))
        self.assertEqual("channel1_book_sec_20260722", checks[0]["check_id"])

        wrong_period_manifest = {
            **base_manifest,
            "filtered_value_checks": [
                {
                    **base_manifest["filtered_value_checks"][0],
                    "public_filter_list": [
                        {
                            "fieldId": "qici",
                            "filterValue": ["20260728期"],
                        }
                    ],
                }
            ],
        }
        with self.assertRaisesRegex(UsageError, "required filter/value"):
            normalize_filtered_value_checks(wrong_period_manifest, operations, require=True)

    def test_filtered_value_response_asserts_expected_row_and_measure(self) -> None:
        check = {
            "check_id": "channel1_book_sec_20260722",
            "row_match": {
                "channel_map_1": "图书",
                "dept_2": "SEC",
            },
            "measure_field_id": "v_lead",
            "expected_value": 55,
        }
        response = {
            "data": {
                "unit_new": {
                    "data": [
                        {
                            "channel_map_1": "图书",
                            "dept_2": "SEC",
                            "v_lead": "55",
                        }
                    ],
                    "taskIds": "task_1",
                    "totalTaskId": "task_total",
                }
            }
        }

        result = assert_filtered_value_response(check=check, unit_id="unit_new", value_payload=response)
        self.assertEqual("passed", result["status"])
        self.assertEqual("55", result["actual_value"])

        mismatch = {
            "data": {
                "unit_new": {
                    "data": [
                        {
                            "channel_map_1": "图书",
                            "dept_2": "SEC",
                            "v_lead": "13277",
                        }
                    ],
                }
            }
        }
        with self.assertRaisesRegex(UsageError, "expected v_lead=55"):
            assert_filtered_value_response(check=check, unit_id="unit_new", value_payload=mismatch)


if __name__ == "__main__":
    unittest.main()
