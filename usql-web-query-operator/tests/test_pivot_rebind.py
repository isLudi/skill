from __future__ import annotations

import copy
import json
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
    replace_pivot_measure_fields,
    rebuild_pivot_unit_fields,
)
from read_dashboard.cli import build_parser  # noqa: E402
from read_dashboard.dashboard_write_adapters import canonical_sha256  # noqa: E402
from read_dashboard.commands.rebind_pivot_fields_sandbox import (  # noqa: E402
    _count_component_unit_refs,
    _execution_mode,
    _materialize_custom_formulas,
    _orphaned_formula_resources,
    _profile_complete_with_retry,
    _remap_formula_references,
    _restore_schema_if_expected,
    _restore_units,
    _replace_component_unit_id,
    _verify_exact_schema_readback,
)


def field(field_id: str, name: str, show_name: str | None = None) -> dict[str, object]:
    return {
        "fieldId": field_id,
        "name": name,
        "showName": show_name or name,
        "fieldType": 1,
        "orgParamType": 1,
        "format": {"sortValue": "NONE", "orgParamType": 1, "changeParamType": 1},
        "frontRender": False,
        "uniqueKeyWithTimeStamp": f"{field_id}_stable",
    }


class PivotRebindTests(unittest.TestCase):
    def test_complete_profile_retry_is_bounded(self) -> None:
        class Page:
            def __init__(self) -> None:
                self.waits: list[int] = []

            def wait_for_timeout(self, value: int) -> None:
                self.waits.append(value)

        page = Page()
        profile = {"schema_version": "1.0.0", "artifact_type": "DashboardProfile"}
        from unittest.mock import patch
        with patch(
            "read_dashboard.commands.rebind_pivot_fields_sandbox.profile_edit_dashboard",
            return_value=profile,
        ), patch(
            "read_dashboard.commands.rebind_pivot_fields_sandbox.require_complete_profile",
            side_effect=[UsageError("settling"), {"profile_sha256": "ok"}],
        ):
            result, attempts = _profile_complete_with_retry(page=page, label="post", retry_wait_ms=25)
        self.assertEqual({"profile_sha256": "ok"}, result)
        self.assertEqual(2, attempts)
        self.assertEqual([25], page.waits)

    def test_replace_measures_adds_and_reorders_without_mutating_existing_payloads(self) -> None:
        existing_8min = field("8190136223229952", "is_long_call", "8min人数")
        existing_8min["format"] = {"sortValue": "DESC", "condition": {"precision": 0}}
        first_lesson = field("first_lesson_valid", "first_lesson_valid", "首节有效")
        target = {
            "unitId": "unit_3993036395152396288",
            "unitName": "渠道-整体",
            "modelId": "2064",
            "unitDimensionList": [field("channel_map_1", "channel_map_1")],
            "unitColumnDimensionList": [],
            "unitMeasureList": [existing_8min, first_lesson],
            "unitAideMeasureList": [],
            "unitFilterList": [field("qici", "qici")],
            "unrelatedConfig": {"pageSize": 100},
        }
        additions = {
            "8183691126073344": {
                "model_id": "2064",
                "payload": field("8183691126073344", "is_friend_lead", "新增好友数"),
            },
            "8149654467340288": {
                "model_id": "2064",
                "payload": field("8149654467340288", "is_app_denglu", "APP数"),
            },
        }
        after_ids = [
            "first_lesson_valid",
            "8183691126073344",
            "8149654467340288",
            "8190136223229952",
        ]

        rebuilt = replace_pivot_measure_fields(
            target_detail=target,
            expected_model_id="2064",
            expected_before_field_ids=["8190136223229952", "first_lesson_valid"],
            after_field_ids=after_ids,
            field_catalog=additions,
        )

        self.assertEqual(after_ids, [item["fieldId"] for item in rebuilt["unitMeasureList"]])
        self.assertEqual(first_lesson, rebuilt["unitMeasureList"][0])
        self.assertEqual(existing_8min, rebuilt["unitMeasureList"][3])
        self.assertEqual(target["unitDimensionList"], rebuilt["unitDimensionList"])
        self.assertEqual({"pageSize": 100}, rebuilt["unrelatedConfig"])
        self.assertEqual(
            ["8190136223229952", "first_lesson_valid"],
            [item["fieldId"] for item in target["unitMeasureList"]],
        )

    def test_replace_measures_rejects_drift_duplicates_removal_and_cross_model_addition(self) -> None:
        target = {
            "unitId": "unit_1",
            "modelId": "2064",
            "unitMeasureList": [field("a", "a"), field("b", "b")],
        }
        catalog = {"c": {"model_id": "9999", "payload": field("c", "c")}}
        common = {"target_detail": target, "expected_model_id": "2064", "field_catalog": catalog}
        with self.assertRaisesRegex(UsageError, "order drifted"):
            replace_pivot_measure_fields(
                **common, expected_before_field_ids=["b", "a"], after_field_ids=["a", "b", "c"]
            )
        with self.assertRaisesRegex(UsageError, "duplicate"):
            replace_pivot_measure_fields(
                **common, expected_before_field_ids=["a", "b"], after_field_ids=["a", "b", "b"]
            )
        with self.assertRaisesRegex(UsageError, "cannot remove"):
            replace_pivot_measure_fields(
                **common, expected_before_field_ids=["a", "b"], after_field_ids=["a"]
            )
        with self.assertRaisesRegex(UsageError, "belongs to model 9999"):
            replace_pivot_measure_fields(
                **common, expected_before_field_ids=["a", "b"], after_field_ids=["a", "b", "c"]
            )
        non_atomic = {"123": {"model_id": "2064", "payload": field("123", "formula")}}
        non_atomic["123"]["payload"]["format"]["orgParamType"] = 4
        with self.assertRaisesRegex(UsageError, "not a verified atomic metric"):
            replace_pivot_measure_fields(
                target_detail=target, expected_model_id="2064",
                expected_before_field_ids=["a", "b"], after_field_ids=["a", "b", "123"],
                field_catalog=non_atomic,
            )

    def test_production_rebind_has_explicit_draft_only_cli_entrypoint(self) -> None:
        parser = build_parser()
        subparsers = next(
            action for action in parser._actions if action.__class__.__name__ == "_SubParsersAction"
        )
        self.assertIn("rebind-pivot-fields-sandbox", subparsers.choices)
        self.assertIn("sync-pivot-fields-draft", subparsers.choices)
        production_parser = subparsers.choices["sync-pivot-fields-draft"]
        for option in ("--confirm-production-write", "--manifest-sha256"):
            action = next(action for action in production_parser._actions if option in action.option_strings)
            self.assertTrue(action.required)

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

    def test_rebuild_syncs_formulas_colors_order_and_renames_dimensions(self) -> None:
        target_dimension = field("319195", "jingli", "jingli")
        source_measure = field("9001", "formula_metric", "转化率")
        source_measure["frontRender"] = 3
        source_measure["format"] = {
            "definition": [{"label": "divide", "functionParams": [1, 2]}],
            "decimal": 2,
            "columnVisualStyle": {"fontColor": "#d0021b", "backgroundColor": "#d7b3f6"},
        }
        target = {
            "unitId": "unit_target", "unitName": "分团队转化数据", "modelId": "2293",
            "format": {"isOpen": 1, "fieldMeasureNameSortList": ["old"], "userBehaviorRecord": {"enabled": 0}},
            "unitDimensionList": [target_dimension], "unitColumnDimensionList": [],
            "unitMeasureList": [field("old", "old")], "unitAideMeasureList": [], "unitFilterList": [],
        }
        source = {
            "unitId": "unit_source", "unitName": "个人", "modelId": "2293",
            "format": {"isOpen": 0, "freezeRow": [0, 0], "fieldMeasureNameSortList": ["转化率"]},
            "unitDimensionList": [field("319190", "qici", "期")], "unitColumnDimensionList": [],
            "unitMeasureList": [source_measure], "unitAideMeasureList": [], "unitFilterList": [],
        }

        rebuilt = rebuild_pivot_unit_fields(
            target_detail=target, source_detail=source, dimension_field_ids=["319195"],
            preserve_target_display=False, dimension_show_names={"319195": "负责人"},
            sync_source_format=True,
        )

        self.assertEqual("unit_target", rebuilt["unitId"])
        self.assertEqual("分团队转化数据", rebuilt["unitName"])
        self.assertEqual("负责人", rebuilt["unitDimensionList"][0]["showName"])
        self.assertNotIn("319190", [item["fieldId"] for item in rebuilt["unitDimensionList"]])
        self.assertEqual(source_measure, rebuilt["unitMeasureList"][0])
        self.assertEqual(0, rebuilt["format"]["isOpen"])
        self.assertEqual([0, 0], rebuilt["format"]["freezeRow"])
        self.assertEqual(["转化率"], rebuilt["format"]["fieldMeasureNameSortList"])
        self.assertEqual({"enabled": 0}, rebuilt["format"]["userBehaviorRecord"])
        state = project_unit_field_state(rebuilt)
        self.assertEqual(source_measure["format"], state["groups"]["unitMeasureList"][0]["format"])
        self.assertEqual(3, state["groups"]["unitMeasureList"][0]["frontRender"])

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

    def test_production_execution_mode_requires_reviewed_manifest(self) -> None:
        args = SimpleNamespace(
            confirm_production_write=True,
            confirm_sandbox_write=False,
            dashboard_id="dashboard_1",
            expected_dashboard_name="conversion",
        )
        with self.assertRaisesRegex(UsageError, "production_draft_sync=true"):
            _execution_mode(args, {})

    def test_production_execution_mode_is_draft_only_and_keeps_unit_identity(self) -> None:
        manifest = {
            "production_draft_sync": True, "dashboard_id": "dashboard_1",
            "dashboard_name": "conversion",
            "expected_profile_sha256": "a" * 64,
            "operations": [{"operation_id": "personal", "target_unit_id": "unit_1",
                            "source_unit_id": "unit_2", "dimension_field_ids": ["manager"],
                            "expected_before_sha256": "b" * 64,
                            "expected_source_sha256": "c" * 64}],
        }
        args = SimpleNamespace(
            confirm_production_write=True, confirm_sandbox_write=False,
            dashboard_id="dashboard_1", expected_dashboard_name="conversion",
            manifest_sha256=canonical_sha256(manifest),
        )
        mode = _execution_mode(args, manifest)
        self.assertEqual("production_draft", mode["name"])
        self.assertEqual("DashboardPivotFieldSyncDraftReceipt", mode["receipt_artifact_type"])
        self.assertTrue(mode["registry_sha256"])
        self.assertEqual(canonical_sha256(manifest), mode["manifest_sha256"])

    def test_production_execution_mode_requires_exact_hashes_and_registry_allowlist(self) -> None:
        manifest = {
            "production_draft_sync": True, "dashboard_id": "dashboard_1",
            "dashboard_name": "conversion", "expected_profile_sha256": "a" * 64,
            "operations": [{"operation_id": "personal", "target_unit_id": "unit_1",
                            "source_unit_id": "unit_2", "dimension_field_ids": ["manager"],
                            "expected_before_sha256": "b" * 64,
                            "expected_source_sha256": "c" * 64}],
        }
        args = SimpleNamespace(
            confirm_production_write=True, confirm_sandbox_write=False,
            dashboard_id="dashboard_1", expected_dashboard_name="conversion",
            manifest_sha256="0" * 64,
        )
        with self.assertRaisesRegex(UsageError, "manifest hash mismatch"):
            _execution_mode(args, manifest)
        without_profile_hash = {**manifest, "expected_profile_sha256": ""}
        args.manifest_sha256 = canonical_sha256(without_profile_hash)
        with self.assertRaisesRegex(UsageError, "expected_profile_sha256"):
            _execution_mode(args, without_profile_hash)

        from unittest.mock import patch
        blocked_registry = {
            "registry_sha256": "d" * 64,
            "capabilities": [{
                "operation": "sync_existing_pivot_fields_from_same_model_source",
                "write_policy": "blocked", "maturity": "observed", "phase": "draft",
                "transaction_class": "compensating_restore", "recovery_policy": "compensating_restore",
                "readback_coverage": "full",
                "adapter": "read_dashboard.commands.rebind_pivot_fields_sandbox.cmd_rebind_pivot_fields_sandbox[production_draft]",
                "write_endpoints": ["config/save/dashboardHtml", "config/update/unit", "model/customized/column/saveAndUpdate"],
            }],
        }
        args.manifest_sha256 = canonical_sha256(manifest)
        with patch(
            "read_dashboard.commands.rebind_pivot_fields_sandbox.load_capability_registry",
            return_value=blocked_registry,
        ):
            with self.assertRaisesRegex(UsageError, "not enabled"):
                _execution_mode(args, manifest)

    def test_production_sync_is_limited_to_one_pivot(self) -> None:
        operation = {"operation_id": "personal", "target_unit_id": "unit_1",
                     "source_unit_id": "unit_2", "dimension_field_ids": ["manager"],
                     "expected_before_sha256": "b" * 64,
                     "expected_source_sha256": "c" * 64}
        manifest = {
            "production_draft_sync": True, "dashboard_id": "dashboard_1",
            "dashboard_name": "conversion", "expected_profile_sha256": "a" * 64,
            "operations": [operation, {**operation, "operation_id": "team", "target_unit_id": "unit_3"}],
        }
        args = SimpleNamespace(
            confirm_production_write=True, confirm_sandbox_write=False,
            dashboard_id="dashboard_1", expected_dashboard_name="conversion",
            manifest_sha256=canonical_sha256(manifest),
        )
        with self.assertRaisesRegex(UsageError, "exactly one existing pivot"):
            _execution_mode(args, manifest)

    def test_production_component_style_requires_source_and_target_hashes(self) -> None:
        manifest = {
            "production_draft_sync": True, "dashboard_id": "dashboard_1",
            "dashboard_name": "conversion", "expected_profile_sha256": "a" * 64,
            "operations": [{"operation_id": "personal", "target_unit_id": "unit_1",
                            "source_unit_id": "unit_2", "dimension_field_ids": ["manager"],
                            "expected_before_sha256": "b" * 64,
                            "expected_source_sha256": "c" * 64,
                            "sync_component_style": True}],
        }
        args = SimpleNamespace(
            confirm_production_write=True, confirm_sandbox_write=False,
            dashboard_id="dashboard_1", expected_dashboard_name="conversion",
            manifest_sha256=canonical_sha256(manifest),
        )
        with self.assertRaisesRegex(UsageError, "expected_target_style_sha256"):
            _execution_mode(args, manifest)

    def test_failure_receipt_classifies_created_or_uncertain_formulas_as_orphans(self) -> None:
        orphaned = _orphaned_formula_resources([
            {"target_field_id": "customized_1", "name": "new", "status": "created"},
            {"target_field_id": None, "name": "uncertain", "status": "create_outcome_unknown"},
            {"target_field_id": "customized_2", "name": "reused", "status": "reused"},
        ])
        self.assertEqual(["customized_1", None], [item["resource_id"] for item in orphaned])
        self.assertTrue(all(item["manual_cleanup_required"] for item in orphaned))

    def test_formula_dependencies_are_remapped_and_forward_references_blocked(self) -> None:
        source_ids = {"customized_source_a", "customized_source_b"}
        value = {
            "dependencyIndicators": [{"paramId": "customized_source_a"}],
            "globalFilterSpecialConfig": [{"nested": {"paramId": "customized_source_a"}}],
        }
        remapped = _remap_formula_references(value, {"customized_source_a": "customized_target_a"}, source_ids)
        self.assertEqual("customized_target_a", remapped["dependencyIndicators"][0]["paramId"])
        self.assertEqual("customized_target_a", remapped["globalFilterSpecialConfig"][0]["nested"]["paramId"])
        with self.assertRaisesRegex(UsageError, "not ordered"):
            _remap_formula_references(
                {"paramId": "customized_source_b"},
                {"customized_source_a": "customized_target_a"},
                source_ids,
            )
        with self.assertRaisesRegex(UsageError, "unsupported source-specific"):
            _remap_formula_references(
                {"fieldId": "customized_source_a"},
                {"customized_source_a": "customized_target_a"},
                source_ids,
            )

    def test_source_custom_formulas_require_reviewed_catalog(self) -> None:
        with self.assertRaisesRegex(UsageError, "explicit reviewed source_custom_formulas"):
            _materialize_custom_formulas(
                page=None,
                dashboard_id="dashboard_1",
                source_detail={"unitMeasureList": [{"fieldId": "customized_source_a"}]},
                target_detail={},
                operation={},
                observations=[],
                formula_results=[],
            )

    def test_unit_recovery_does_not_overwrite_unexpected_drift(self) -> None:
        from unittest.mock import patch

        baseline = {"unitId": "unit_1", "modelId": "model_1", "unitMeasureList": [],
                    "unitDimensionList": [field("region", "region", "before")],
                    "unitColumnDimensionList": [], "unitAideMeasureList": [], "unitFilterList": []}
        changed = copy.deepcopy(baseline)
        changed["unitDimensionList"][0]["showName"] = "external edit"
        record = {
            "operation_id": "sync",
            "target_unit_id": "unit_1",
            "before_raw": baseline,
            "before_state": project_unit_field_state(baseline),
            "allowed_current_states": [project_unit_field_state(baseline)],
        }
        with patch(
            "read_dashboard.commands.rebind_pivot_fields_sandbox.fetch_edit_unit_detail",
            return_value=changed,
        ), patch(
            "read_dashboard.commands.rebind_pivot_fields_sandbox._write_unit_detail",
        ) as write:
            with self.assertRaisesRegex(UsageError, "changed outside"):
                _restore_units(page=None, dashboard_id="dashboard_1", dashboard_name="test", completed=[record])
        write.assert_not_called()

    def test_schema_recovery_preserves_external_drift(self) -> None:
        from unittest.mock import patch

        original = {"componentsTree": [{"id": "original"}]}
        attempted = {"componentsTree": [{"id": "attempted"}]}
        external = {"componentsTree": [{"id": "external"}]}
        config = {"dashboardHtmlJson": json.dumps(external)}
        with patch(
            "read_dashboard.commands.rebind_pivot_fields_sandbox.fetch_edit_dashboard_config",
            return_value=config,
        ), patch(
            "read_dashboard.commands.rebind_pivot_fields_sandbox._write_dashboard_schema",
        ) as write:
            with self.assertRaisesRegex(UsageError, "did not overwrite"):
                _restore_schema_if_expected(
                    page=None, dashboard_id="dashboard_1", dashboard_name="test",
                    original_schema=original, attempted_schema=attempted, observations=[],
                )
        write.assert_not_called()

    def test_production_schema_readback_requires_full_exact_match(self) -> None:
        expected = {"componentsTree": [{"id": "pivot", "props": {"layout": {"x": 1}}}]}
        result = _verify_exact_schema_readback(copy.deepcopy(expected), copy.deepcopy(expected))
        self.assertEqual("matched", result["status"])
        self.assertEqual(result["expected_sha256"], result["actual_sha256"])
        changed_elsewhere = copy.deepcopy(expected)
        changed_elsewhere["componentsTree"][0]["props"]["layout"]["x"] = 2
        with self.assertRaisesRegex(UsageError, "complete expected schema"):
            _verify_exact_schema_readback(expected, changed_elsewhere)

    def test_production_execution_mode_rejects_copy_rebuild(self) -> None:
        args = SimpleNamespace(
            confirm_production_write=True, confirm_sandbox_write=False,
            dashboard_id="dashboard_1", expected_dashboard_name="conversion",
        )
        manifest = {
            "production_draft_sync": True,
            "operations": [{"operation_id": "personal", "target_unit_id": "unit_1",
                            "source_unit_id": "unit_2", "dimension_field_ids": ["manager"],
                            "rebuild_by_copy": True}],
        }
        with self.assertRaisesRegex(UsageError, "cannot copy"):
            _execution_mode(args, manifest)

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
