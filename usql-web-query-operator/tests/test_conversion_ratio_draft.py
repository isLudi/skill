import json
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from _shared.errors import UsageError
from read_dashboard.commands.conversion_ratio_draft import (
    _check_result, _definition, _field_keys, _expected_profile, _published, _scoped_units, _write_backup,
)


def metric(field_id, name):
    return {"field_id": field_id, "field_name": name}


RATIO = {
    "name": "达标转化率", "formula_id": "customized_1", "share_name": "达标占比", "share_id": "customized_2",
    "converted": metric("301", "converted"), "qualified": metric("302", "qualified"),
}
SELECTION = {"subject_id": 42, "all_leads": metric("303", "all_leads"), "ratios": [RATIO],
             "dashboard_id": "dashboard_321", "dashboard_name": "Controller", "model_id": 2293,
             "targets": [{"component_id": "node_321", "unit_id": "unit_321"}]}


class ConversionRatioDraftTest(unittest.TestCase):
    def test_baseline_backup_is_plan_scoped_and_never_overwritten(self):
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as temp:
            root = Path(temp)
            first = _write_backup(root, "dashboard_321", "a" * 64, {"plan": 1})
            self.assertTrue(first.is_file())
            with self.assertRaisesRegex(UsageError, "immutable baseline backup"):
                _write_backup(root, "dashboard_321", "a" * 64, {"plan": 2})
            second = _write_backup(root, "dashboard_321", "b" * 64, {"plan": 2})
            self.assertNotEqual(first, second)

    def test_constructs_three_bound_expressions(self):
        for mode, formula, ids in (
            ("before", "ifnull(sum(${converted})/sum(${all_leads}),0)", ["301", "303"]),
            ("share", "ifnull(sum(${qualified})/sum(${all_leads}),0)", ["302", "303"]),
            ("after", "ifnull(sum(${converted})/sum(${qualified}),0)", ["301", "302"]),
        ):
            definition = _definition(SELECTION, RATIO, mode)
            self.assertEqual(definition["formula"], formula)
            self.assertEqual([d["paramId"] for d in definition["dependencyIndicators"]], ids)
            self.assertEqual(definition["columnKey"], "customized_2" if mode == "share" else "customized_1")

    def test_checks_conversion_share_and_zero_denominator_independently(self):
        unit = {"unitDimensionList": [], "unitMeasureList": [{"fieldId": cid} for cid in ["303", "customized_1", "customized_2"]]}
        raw = {"unitId": "unit_321", "totalTaskId": "1", "title": [{"paramId": c["fieldId"]} for c in unit["unitMeasureList"]],
               "totalData": {"303": "100", "customized_1": "0.2", "customized_2": "0.4"}}
        check = {"unit_id": "unit_321", "label": "total", "filters": [], "row": [], "all_leads": 100, "counts": [[8, 40]]}
        self.assertEqual(_check_result(raw, SELECTION, unit, check, False)["ratios"][0]["qualified"], 40)
        raw["totalData"]["customized_2"] = "0.8"
        with self.assertRaisesRegex(UsageError, "Unchanged share"):
            _check_result(raw, SELECTION, unit, check, False)
        raw["totalData"].update({"customized_1": "0", "customized_2": "0"})
        self.assertEqual(_check_result(raw, SELECTION, unit, check | {"counts": [[0, 0]]}, False)["ratios"][0]["conversion_rate"], "0")

    def test_rejects_shared_formula_outside_selected_pivots(self):
        profile = {"components": [], "formulas": [
            {"formula_id": f, "component_ids": ["node_321", "node_other"]} for f in ("customized_1", "customized_2")
        ]}
        with self.assertRaisesRegex(UsageError, "outside the reviewed pivots"):
            _scoped_units(None, profile, SELECTION, [])

    def test_rejects_published_formula_and_parses_card_shape(self):
        self.assertEqual(_field_keys({"data": [{"measure": {"paramId": "customized_1"}, "value": "0.2"}]}), {"customized_1"})
        with (
            patch("read_dashboard.commands.conversion_ratio_draft.fetch_dashboard_config",
                  return_value={"dashboardId": "dashboard_321", "dashboardName": "Controller", "dashboardHtmlJson": '{"a":1}'}),
            patch("read_dashboard.commands.conversion_ratio_draft.extract_component_units",
                  return_value=[{"unit_id": "unit_321", "component_type": "u_pivot"}]),
            patch("read_dashboard.commands.conversion_ratio_draft.fetch_unit_detail",
                  return_value={"unitId": "unit_321", "dashboardModel": {"subjectId": 5}}),
            patch("read_dashboard.commands.conversion_ratio_draft.post_json",
                  return_value={"data": {"unit_321": {"unitId": "unit_321", "title": [{"paramId": "customized_1"}]}}}),
        ):
            with self.assertRaisesRegex(UsageError, "referenced by the published"):
                _published(None, SELECTION)

    def test_profile_comparison_keeps_other_formulas_unchanged(self):
        common = {k: [] for k in ("components", "data_units", "layout", "public_filters", "component_filters", "datasets", "theme")}
        prior = _definition(SELECTION, RATIO, "before")
        final = _definition(SELECTION, RATIO, "after")
        share = _definition(SELECTION, RATIO, "share")

        def row(d):
            return {"formula_id": d["columnKey"], "expression": d["formula"], "dependencies": d["dependencyIndicators"],
                    "component_ids": ["node_321"]}

        before = common | {"formulas": [row(prior), row(share)]}
        after = common | {"formulas": [row(final), row(share)]}
        _expected_profile(before, after, {"after": [final]})
        after["formulas"][1]["expression"] = "bad_expression"
        with self.assertRaisesRegex(UsageError, "Another formula changed"):
            _expected_profile(before, after, {"after": [final]})

    def test_production_apply_is_blocked_for_sandbox_only_capability(self):
        from read_dashboard.commands import conversion_ratio_draft as conversion
        from read_dashboard.dashboard_change import canonical_sha256

        selection = {**SELECTION, "domain": "market_consultant", "owner": "owner"}
        checks = [{"unit_id": "unit_321", "label": "total", "filters": [], "row": [],
                   "all_leads": 1, "counts": [[0, 0]]}]
        plan = {"artifact_type": conversion.PLAN_TYPE, "sandbox": False,
                "selection": selection, "checks": checks}
        plan["plan_sha256"] = canonical_sha256(plan)
        capability = {"maturity": "sandbox_verified", "write_policy": "sandbox_only",
                      "adapter": conversion.ADAPTER}
        args = SimpleNamespace(mode="apply", input=Path("unused.json"), domain="market_consultant", sandbox=False,
                               plan_sha256=plan["plan_sha256"], confirm_production_write=True,
                               confirm_sandbox_write=False, headed=False, state_path=Path("unused-state.json"))
        with patch.object(conversion, "_read", return_value=plan), \
             patch.object(conversion, "_core_api"), \
             patch("text2sql_core.dashboard_domains.validate_dashboard_domain_registration",
                   return_value=({"status": "registered"}, [])), \
             patch.object(conversion, "capability_by_operation", return_value=capability), \
             patch.object(conversion, "import_playwright") as launch:
            with self.assertRaisesRegex(UsageError, "not allowlisted"):
                conversion.cmd_conversion_ratio_draft(args)
            launch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
