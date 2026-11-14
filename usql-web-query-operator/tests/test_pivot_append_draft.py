from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from _shared.errors import UsageError
from read_dashboard.commands import append_pivot_draft as append


def live_append() -> append.LiveAppend:
    container = {
        "id": "node_grid",
        "componentName": "RootContentNew",
        "props": {"layoutMode": "magnetic", "layout": [
            {"i": ".$node_old", "x": 0, "y": 0, "w": 20, "h": 12},
        ]},
        "children": [{"id": "node_old", "componentName": "PivotTable", "props": {"settings": {"unitId": "unit_1"}}}],
    }
    schema = {"componentsTree": [{"id": "node_page", "componentName": "Page", "children": [container]}]}
    period = {
        "fieldId": "10", "showName": "period", "filterUnitId": "filter_3",
        "format": {"filterValue": ["latest"], "dynamicsFilter": True, "dynamicsFilterValue": "1",
                   "preFilterTaskId": "cached", "preFilterValueList": ["latest"], "displayFilterName": "Period", "orgParamType": 2},
    }
    unit = {
        "modelId": 100, "unitId": "unit_2", "format": {"pageSize": 100, "isTotal": 1},
        "unitFilterList": [period],
        "unitDimensionList": [{"fieldId": "10", "showName": "period"}, {"fieldId": "11", "showName": "Channel"}],
        "unitColumnDimensionList": [], "unitAideMeasureList": [],
        "unitMeasureList": [{"fieldId": "customized_1", "showName": "Rate", "format": {"decimalPlaces": 2}}],
    }
    plan = {
        "selection": {"target_container_id": "node_grid", "title": "By channel"},
        "formula_bindings": {"customized_1": {"target_field_id": "customized_2"}},
        "layout": append._layout_at_bottom(schema, {"x": 0, "y": 4, "w": 20, "h": 7}, "node_grid", "node_new"),
    }
    node = {"id": "node_new", "componentName": "PivotTable", "props": {"settings": {}}}
    return append.LiveAppend(plan, schema, unit, {"subjectId": 200}, node, period)


class PivotAppendDraftTests(unittest.TestCase):
    def test_new_unit_reuses_formula_and_creates_independent_local_filter(self) -> None:
        live = live_append()
        field = append._new_filter(live)
        self.assertNotIn("filterUnitId", field)
        self.assertNotIn("preFilterTaskId", field["format"])
        self.assertEqual([], field["format"]["filterValue"])
        self.assertIs(field["format"]["dynamicsFilter"], True)
        field["filterUnitId"] = "filter_4"
        pivot = append._new_pivot(live, field)
        self.assertEqual(["11"], [f["fieldId"] for f in pivot["unitDimensionList"]])
        self.assertEqual("customized_2", pivot["unitMeasureList"][0]["fieldId"])
        self.assertEqual("Rate", pivot["unitMeasureList"][0]["showName"])
        self.assertEqual(2, pivot["unitMeasureList"][0]["format"]["decimalPlaces"])
        self.assertEqual("filter_3", live.filter["filterUnitId"])

    def test_layout_append_preserves_existing_schema(self) -> None:
        live = live_append()
        before = copy.deepcopy(live.target_schema)
        field = append._new_filter(live)
        field["filterUnitId"] = "filter_4"
        schema = append._append_schema(live, "unit_4", field)
        self.assertEqual(before, live.target_schema)
        grid = schema["componentsTree"][0]["children"][0]
        self.assertEqual({"i": ".$node_new", "x": 0, "y": 12, "w": 20, "h": 7}, grid["props"]["layout"].pop())
        settings = grid["children"].pop()["props"]["settings"]
        self.assertEqual("unit_4", settings["unitId"])
        self.assertEqual("filter_4", settings["filterConfigList"][0]["filterUnitId"])
        self.assertEqual(before, schema)

    def test_malformed_layout_is_blocked(self) -> None:
        live = live_append()
        grid = live.target_schema["componentsTree"][0]["children"][0]
        grid["props"]["layout"][0]["i"] = ".$unknown"
        with self.assertRaisesRegex(UsageError, "one to one"):
            append._layout_at_bottom(live.target_schema, live.plan["layout"], "node_grid", "node_new")

    def test_filter_task_id_does_not_mask_real_filter_drift(self) -> None:
        unit = live_append().source_unit
        newer = copy.deepcopy(unit)
        fmt = newer["unitFilterList"][0]["format"]
        fmt["preFilterTaskId"] = "new_task"
        self.assertEqual(append._unit_config(unit), append._unit_config(newer))
        fmt["filterValue"] = ["different"]
        self.assertNotEqual(append._unit_config(unit), append._unit_config(newer))

    def test_formula_whitespace_equivalence_preserves_literals(self) -> None:
        left = {"formula": "ifnull(sum(${metric}),0)"}
        right = {"formula": "ifnull(sum(${metric}), 0)"}
        self.assertEqual(append._formula_semantics(left), append._formula_semantics(right))
        self.assertNotEqual(
            append._formula_semantics({"formula": "'a b'"}),
            append._formula_semantics({"formula": "'ab'"}),
        )

    @patch.object(append, "post_json")
    def test_draft_values_use_local_filter_and_match_by_display_name(self, post: Mock) -> None:
        unit = live_append().source_unit
        post.return_value = {"data": {"unit_2": {
            "unitId": "unit_2", "hasMore": False,
            "title": [{"paramId": "11", "name": "Channel"}, {"paramId": "customized_99", "name": "Rate"}],
            "data": [{"11": "A", "customized_99": "0.0100"}], "totalData": {"customized_99": "0.010"},
        }}}
        result = append._value_projection(Mock(), unit, "latest", draft=True)
        payload = post.call_args.args[2]
        self.assertEqual("draft", payload["versionId"])
        self.assertEqual([], payload["publicFilterList"])
        self.assertEqual("filter_3", payload["filterList"][0]["filterUnitId"])
        self.assertEqual(["latest"], payload["filterList"][0]["filterValue"])
        self.assertEqual({"Rate": "0.01"}, result["totals"])
        post.return_value["data"]["unit_2"]["hasMore"] = True
        with self.assertRaisesRegex(UsageError, "complete"):
            append._value_projection(Mock(), unit, "latest", draft=True)

    @patch.object(append, "import_playwright")
    @patch.object(append, "_registry_hash", return_value="active")
    def test_incorrect_plan_hash_blocks_browser_launch(self, _registry: Mock, browser: Mock) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plan.json"
            path.write_text("{}", encoding="utf-8")
            args = SimpleNamespace(command="apply-pivot-append", plan=path, plan_sha256="wrong", confirm_production_write=True)
            with self.assertRaisesRegex(UsageError, "exact hash"):
                append.cmd_append_pivot_draft(args)
        browser.assert_not_called()
