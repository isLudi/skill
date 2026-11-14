from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
import json
import sys
from tempfile import TemporaryDirectory
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from _shared.errors import UsageError
from read_dashboard.commands.pivot_ratio_draft import (
    PLAN_TYPE, SANDBOX_TEMPLATE, LiveDraft, _formula_lookup, _mutate, _validate_live_filters, _verify_values,
    _write_backup,
    cmd_pivot_ratio_draft,
)
from read_dashboard.dashboard_change import canonical_sha256
from read_dashboard.pivot_ratio_fields import expected_rate, formula_definition, formula_matches, projection, replace_ratio_fields, validate_selection


SELECTION = {
    "domain": "market_consultant", "dashboard_id": "dashboard_1", "dashboard_name": "指标测试沙箱",
    "owner": "owner", "model_id": 2, "subject_id": 3, "component_id": "node_4", "unit_id": "unit_5",
    "unit_name": "负责人", "denominator": {"field_id": "100", "field_name": "lead_count"},
    "ratios": [{"name": "新指标", "numerator": {"field_id": "101", "field_name": "qualified_num"}}],
    "remove_ids": ["customized_112"], "move_to_end_ids": ["113"], "anchor_id": "111",
    "header_color": "#f1ecaf", "decimals": 1,
}


def fixture():
    fields = [
        {"fieldId": "100", "showName": "退后线索", "format": {"id": 100}},
        {"fieldId": "111", "showName": "客单价", "format": {"id": 111}},
        {"fieldId": "customized_112", "showName": "旧率", "format": {
            "orgParamType": 4, "dataType": 1, "numberType": 2, "isAggregation": False,
            "filterType": ["aggregationFilter"],
            "columnVisualStyle": {"header": {"bgColor": "#f1ecaf"}, "body": {"bgColor": "#ffffff"}},
        }},
        {"fieldId": "113", "showName": "AB率", "format": {"id": 113}},
        {"fieldId": "114", "showName": "深沟率", "format": {"id": 114}},
    ]
    return {"unitMeasureList": fields, "format": {"fieldMeasureNameSortList": [f["showName"] for f in fields]}}


class PivotRatioDraftTest(unittest.TestCase):
    def test_baseline_backup_is_plan_scoped_and_never_overwritten(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            first = _write_backup(root, "dashboard_1", "a" * 64, {"plan": 1})
            self.assertTrue(first.is_file())
            self.assertNotEqual(first, root / "pivot-ratio-baseline.json")
            with self.assertRaisesRegex(UsageError, "immutable baseline backup"):
                _write_backup(root, "dashboard_1", "a" * 64, {"plan": 2})
            second = _write_backup(root, "dashboard_1", "b" * 64, {"plan": 2})
            self.assertNotEqual(first, second)

    def test_replaces_and_moves_only_reviewed_ids_and_reuses_yellow_format(self):
        unit = fixture()
        result = replace_ratio_fields(unit, SELECTION, ["customized_1"], SANDBOX_TEMPLATE)
        self.assertEqual([m["fieldId"] for m in result["unitMeasureList"]],
                         ["100", "111", "customized_1", "114", "113"])
        self.assertEqual(result["format"]["fieldMeasureNameSortList"], ["退后线索", "客单价", "新指标", "深沟率", "AB率"])
        new_format = result["unitMeasureList"][2]["format"]
        self.assertEqual(new_format["columnVisualStyle"]["header"]["bgColor"], "#f1ecaf")
        self.assertEqual(new_format["columnVisualStyle"]["body"]["bgColor"], "#ffffff")
        self.assertEqual((new_format["numberType"], new_format["decimalPlaces"]), (2, 1))
        self.assertEqual(result["unitMeasureList"][-1], unit["unitMeasureList"][-2])
        self.assertEqual(len(unit["unitMeasureList"]), 5)

    def test_does_not_remove_physical_measures(self):
        selection = deepcopy(SELECTION)
        selection["remove_ids"] = ["100"]
        with self.assertRaisesRegex(UsageError, "Only existing calculated percentage measures"):
            replace_ratio_fields(fixture(), selection, ["customized_1"], SANDBOX_TEMPLATE)

    def test_rejects_drifted_or_duplicate_measure_names_and_conflicting_formula(self):
        unit = fixture()
        unit["format"]["fieldMeasureNameSortList"].reverse()
        with self.assertRaisesRegex(UsageError, "displayed order"):
            replace_ratio_fields(unit, SELECTION, ["customized_1"], SANDBOX_TEMPLATE)
        proposed = formula_definition(SELECTION["ratios"][0], SELECTION["denominator"], 3)
        actual = {**proposed, "indicatorType": "CUSTOMIZED_MEASURE", "columnKey": "customized_1"}
        actual["dependencyIndicators"] = list(reversed(proposed["dependencyIndicators"]))
        self.assertTrue(formula_matches(actual, proposed, "customized_1"))
        actual["subjectId"] = 7
        self.assertFalse(formula_matches(actual, proposed, "customized_1"))
        with patch("read_dashboard.commands.pivot_ratio_draft._formula_item", return_value=actual):
            with self.assertRaisesRegex(UsageError, "conflicts"):
                _formula_lookup(None, [{"title": "新指标", "key": "customized_1"}], proposed)

    def test_rejects_arbitrary_formula_text_and_cross_domain_selection(self):
        invalid = deepcopy(SELECTION)
        invalid["ratios"][0]["numerator"]["field_name"] = "bad})/0+("
        with self.assertRaisesRegex(UsageError, "literal physical"):
            validate_selection(invalid, True)
        invalid = {**SELECTION, "domain": "qingcheng"}
        with self.assertRaisesRegex(UsageError, "market consultant"):
            validate_selection(invalid, False)

    def test_rejects_checks_for_unrelated_filter_and_preserves_zero_denominator(self):
        profile = {
            "components": [{"component_id": "node_4", "fields": {"dimensions": [{"field_id": "1"}]}}],
            "public_filters": [{"target_component_ids": ["node_4"], "field_id": "2", "filter_id": "public_filter_8"}],
        }
        _validate_live_filters(profile, SELECTION, [{"label": "verified", "filters": [["1", "public_filter_8", "a"]]}])
        with self.assertRaisesRegex(UsageError, "outside the selected pivot"):
            _validate_live_filters(profile, SELECTION, [{"label": "unrelated", "filters": [["1", "public_filter_9", "a"]]}])
        self.assertEqual(expected_rate(0, 0), Decimal(0))
        with self.assertRaisesRegex(UsageError, "outside the verified count bounds"):
            expected_rate(4, 3)

    def test_period_owner_and_total_verify_counts_before_accepting_rates(self):
        before = {**fixture(), "unitDimensionList": [{"fieldId": "10"}, {"fieldId": "11"}]}
        target = replace_ratio_fields(before, SELECTION, ["customized_1"], SANDBOX_TEMPLATE)
        plan = {"selection": SELECTION, "sandbox": False, "checks": [
            {"label": "period owner", "row": ["期", ""], "filters": [["10", "public_filter_9", "期"]],
             "denominator": 4, "numerators": [1]},
            {"label": "total", "row": [], "filters": [], "denominator": 4, "numerators": [1]},
        ]}
        live = LiveDraft({}, {}, before, SANDBOX_TEMPLATE, plan)
        cells = {"10": "期", "11": "", "100": "4", "customized_1": "0.25"}
        value = {"unitId": "unit_5", "hasMore": False,
                 "title": [{"paramId": m["fieldId"]} for m in target["unitMeasureList"]],
                 "data": [cells], "totalData": cells}
        with patch("read_dashboard.commands.pivot_ratio_draft.post_json", return_value={"data": {"unit_5": value}}):
            checked = _verify_values(None, live, ["customized_1"], target)
            self.assertEqual(len(checked), 2)
            self.assertEqual(checked[0]["observed_ratios"], ["0.25"])
            cells["100"] = "8"
            with self.assertRaisesRegex(UsageError, "Denominator differs"):
                _verify_values(None, live, ["customized_1"], target)

    def test_selection_hash_mode_and_confirmation_gate_browser(self):
        plan = {"artifact_type": PLAN_TYPE, "sandbox": True, "selection": SELECTION, "checks": [
            {"label": "test", "row": ["period"], "filters": [], "denominator": 2, "numerators": [1]},
        ]}
        plan["plan_sha256"] = canonical_sha256(plan)
        args = SimpleNamespace(mode="apply", input=None, sandbox=True, domain="market_consultant",
                               plan_sha256="0" * 64, confirm_sandbox_write=False, confirm_production_write=False, headed=True)
        with patch("read_dashboard.commands.pivot_ratio_draft._read", return_value=plan), \
             patch("read_dashboard.commands.pivot_ratio_draft.import_playwright") as launch:
            with self.assertRaisesRegex(UsageError, "Exact reviewed plan"):
                cmd_pivot_ratio_draft(args)
            args.plan_sha256 = plan["plan_sha256"]
            with self.assertRaisesRegex(UsageError, "explicit confirmation"):
                cmd_pivot_ratio_draft(args)
            launch.assert_not_called()

    def test_production_apply_is_blocked_for_sandbox_only_capability(self):
        checks = [{"label": "total", "row": [], "filters": [], "denominator": 1, "numerators": [0]}]
        plan = {"artifact_type": PLAN_TYPE, "schema_version": "1.0.0", "sandbox": False,
                "selection": SELECTION, "checks": checks}
        plan["plan_sha256"] = canonical_sha256(plan)
        capability = {"maturity": "sandbox_verified", "write_policy": "sandbox_only",
                      "adapter": "read_dashboard.commands.pivot_ratio_draft.cmd_pivot_ratio_draft"}
        args = SimpleNamespace(mode="apply", input=Path("unused.json"), domain="market_consultant", sandbox=False,
                               plan_sha256=plan["plan_sha256"], confirm_production_write=True,
                               confirm_sandbox_write=False, headed=False, state_path=Path("unused-state.json"))
        with patch("read_dashboard.commands.pivot_ratio_draft._read", return_value=plan), \
             patch("read_dashboard.commands.pivot_ratio_draft._core_api"), \
             patch("text2sql_core.dashboard_domains.validate_dashboard_domain_registration",
                   return_value=({"status": "registered"}, [])), \
             patch("read_dashboard.commands.pivot_ratio_draft.capability_by_operation", return_value=capability), \
             patch("read_dashboard.commands.pivot_ratio_draft.import_playwright") as launch:
            with self.assertRaisesRegex(UsageError, "not allowlisted"):
                cmd_pivot_ratio_draft(args)
            launch.assert_not_called()

    def test_production_apply_is_blocked_for_sandbox_only_capability(self):
        checks = [{"label": "total", "row": [], "filters": [], "denominator": 1, "numerators": [0]}]
        plan = {"artifact_type": PLAN_TYPE, "schema_version": "1.0.0", "sandbox": False,
                "selection": SELECTION, "checks": checks}
        plan["plan_sha256"] = canonical_sha256(plan)
        capability = {"maturity": "sandbox_verified", "write_policy": "sandbox_only",
                      "adapter": "read_dashboard.commands.pivot_ratio_draft.cmd_pivot_ratio_draft"}
        args = SimpleNamespace(mode="apply", input=Path("unused.json"), domain="market_consultant", sandbox=False,
                               plan_sha256=plan["plan_sha256"], confirm_production_write=True,
                               confirm_sandbox_write=False, headed=False, state_path=Path("unused-state.json"))
        with patch("read_dashboard.commands.pivot_ratio_draft._read", return_value=plan), \
             patch("read_dashboard.commands.pivot_ratio_draft._core_api"), \
             patch("text2sql_core.dashboard_domains.validate_dashboard_domain_registration",
                   return_value=({"status": "registered"}, [])), \
             patch("read_dashboard.commands.pivot_ratio_draft.capability_by_operation", return_value=capability), \
             patch("read_dashboard.commands.pivot_ratio_draft.import_playwright") as launch:
            with self.assertRaisesRegex(UsageError, "not allowlisted"):
                cmd_pivot_ratio_draft(args)
            launch.assert_not_called()

    def test_failed_value_check_restores_unit_and_reports_created_formula(self):
        before = fixture()
        plan = {"selection": SELECTION, "sandbox": True, "schema_sha256": canonical_sha256({})}
        live = LiveDraft({}, {}, before, SANDBOX_TEMPLATE, plan)
        receipt = {"writes": [], "formulas": [{"field_id": "customized_1", "created": True}]}
        target = replace_ratio_fields(before, SELECTION, ["customized_1"], SANDBOX_TEMPLATE)
        prefix = "read_dashboard.commands.pivot_ratio_draft."
        with patch(prefix + "_resolve_formulas", return_value=["customized_1"]), \
             patch(prefix + "_expect_before"), patch(prefix + "_write_unit_detail"), \
             patch(prefix + "_unit_read", return_value=target), patch(prefix + "_write_dashboard_schema"), \
             patch(prefix + "_config", return_value={}), patch(prefix + "_profile", return_value=({}, {})), \
             patch(prefix + "_project_profile", return_value={}), patch(prefix + "_restore") as restore, \
             patch(prefix + "_verify_values", side_effect=UsageError("filtered check failed")):
            with self.assertRaisesRegex(UsageError, "filtered check failed"):
                _mutate(None, live, Path("."), receipt)
            restore.assert_called_once()
            self.assertEqual(receipt["retained_formulas_after_failure_or_sandbox"], receipt["formulas"])
            self.assertEqual(receipt["apply_error"], "filtered check failed")
