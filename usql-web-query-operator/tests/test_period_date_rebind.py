from copy import deepcopy
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from _shared.errors import UsageError
from read_dashboard.commands.period_date_rebind import (
    PLAN_TYPE,
    _attempt_marker_path,
    _backup_path,
    cmd_period_date_rebind,
)
from read_dashboard.dashboard_change import canonical_sha256
from read_dashboard.draft_dimension_rebind import checked_field, rebind_chart, rebind_filter, stable_unit


def text_format():
    return {"dataType": 2, "definition": [], "orgParamType": 2, "changeParamType": 2,
            "isAggregation": False, "filterType": ["detailFilter"]}


class PeriodDateRebindTest(unittest.TestCase):
    def setUp(self):
        self.selection = {
            "relation_id": "public_filter_relation_1", "filter_id": "public_filter_2",
            "model_id": 2345, "subject_id": 12, "period_from_field_id": "100",
            "period_label": "原线索期次", "charts": [{"unit_id": "unit_3"}, {"unit_id": "unit_4"}],
        }
        self.period = {"key": "200", "title": "lead_period_name"}
        self.date = {"key": "300", "data_type": 3}

    def unit(self, kind):
        return {
            "unitId": "unit_3", "unitType": kind, "modelId": 2345,
            "dashboardModel": {"dashboardId": "dashboard_1", "applicationModelId": 2345, "subjectId": 12},
            "unitDimensionList": [{"fieldId": "101", "fieldType": 2, "showName": "日期", "sortValue": "desc",
                                   "uniqueKeyWithTimeStamp": "101-instance", "format": dict(text_format(), dimensionType="row")}],
            "unitMeasureList": [{"fieldId": "customized_501", "showName": "当期单效"}],
            "unitFilterList": [{"fieldId": "102"}], "format": {"isTotal": 1},
        }

    def relation(self):
        targets = ["unit_3", "unit_4"]
        field = {"fieldId": "100", "fieldType": 2, "showName": "period_name", "format": text_format()}
        fmt = dict(text_format(), condition="in", dynamicsFilter=True, dynamicsFilterValue="1",
                   displayFilterName="期次", filterValue=["20261106期"], preFilterTaskId="transient")
        binding = {
            "dashboardUnitList": targets,
            "filterUnitParamList": [dict(field, unitIdList=" ".join(targets), modelId=2345, subjectId=12)],
            "unitConfig": {"unitDimensionList": [dict(field, filterUnitId="public_filter_2", format=fmt)]},
        }
        return {"unitId": "public_filter_relation_1", "unitList": [{"unitId": "public_filter_relation_5", "unitList": [
            {"unitId": "public_filter_2", "unitName": "期次", "format": deepcopy(binding), "relationUnit": deepcopy(binding)},
            {"unitId": "public_filter_6", "unitName": "渠道"},
        ]}]}

    def test_rebind_pivot_and_line_preserves_other_chart_fields(self):
        for kind in ("u_pivot", "u_line"):
            with self.subTest(kind=kind):
                before = self.unit(kind)
                target = rebind_chart(before, {"unit_id": "unit_3", "unit_type": kind, "from_field_id": "101"},
                                      dashboard_id="dashboard_1", model_id=2345, subject_id=12,
                                      date_field=self.date, date_label="原分配日")
                dim = target["unitDimensionList"][0]
                self.assertEqual(("300", "asc", "原分配日", 3), (dim["fieldId"], dim["sortValue"], dim["showName"], dim["format"]["dataType"]))
                self.assertEqual("300-instance", dim["uniqueKeyWithTimeStamp"])
                self.assertEqual("", dim["format"]["condition"])
                self.assertEqual("101", before["unitDimensionList"][0]["fieldId"])
                self.assertEqual({k: v for k, v in before.items() if k != "unitDimensionList"},
                                 {k: v for k, v in target.items() if k != "unitDimensionList"})

    def test_period_rebind_preserves_other_filters_and_dynamic_rules(self):
        before = self.relation()
        after = rebind_filter(before, self.selection, self.period)
        leaf, unrelated = after["unitList"][0]["unitList"]
        self.assertEqual("原线索期次", leaf["unitName"])
        self.assertEqual(before["unitList"][0]["unitList"][1], unrelated)
        for key in ("relationUnit", "format"):
            binding = leaf[key]
            dim = binding["unitConfig"]["unitDimensionList"][0]
            self.assertEqual("200", dim["fieldId"])
            self.assertEqual("200", binding["filterUnitParamList"][0]["fieldId"])
            self.assertEqual("1", dim["format"]["dynamicsFilterValue"])
            self.assertEqual([], dim["format"]["filterValue"])
            self.assertNotIn("preFilterTaskId", dim["format"])

    def test_target_drift_and_local_date_filter_are_rejected(self):
        selection = deepcopy(self.selection)
        selection["charts"].pop()
        with self.assertRaisesRegex(UsageError, "scope drifted"):
            rebind_filter(self.relation(), selection, self.period)
        unit = self.unit("u_pivot")
        unit["unitFilterList"][0]["fieldId"] = "101"
        with self.assertRaisesRegex(UsageError, "local filter"):
            rebind_chart(unit, {"unit_id": "unit_3", "unit_type": "u_pivot", "from_field_id": "101"},
                         dashboard_id="dashboard_1", model_id=2345, subject_id=12, date_field=self.date, date_label="原分配日")

    def test_unreviewed_or_wrong_type_fields_are_rejected(self):
        with self.assertRaisesRegex(UsageError, "reviewed type"):
            checked_field({"300": self.date}, "300", 2)

    def test_attempt_marker_is_dashboard_plan_bound_and_backups_are_unique(self):
        with TemporaryDirectory() as temp:
            runtime = Path(temp) / "runtime"
            artifacts = Path(temp) / "artifacts"
            with patch("read_dashboard.commands.period_date_rebind.RUNTIME_DIR", runtime):
                first = _attempt_marker_path("dashboard_1", "a" * 64)
                self.assertEqual(first, _attempt_marker_path("dashboard_1", "a" * 64))
                self.assertNotEqual(first, _attempt_marker_path("dashboard_1", "b" * 64))
                self.assertNotEqual(first, _attempt_marker_path("dashboard_2", "a" * 64))
            backup1 = _backup_path(artifacts, "dashboard_1", "a" * 64)
            backup2 = _backup_path(artifacts, "dashboard_1", "a" * 64)
            self.assertNotEqual(backup1, backup2)
            self.assertTrue(backup1.is_relative_to(artifacts))

    def test_projection_ignores_only_derived_filter_values(self):
        self.assertEqual(stable_unit({"dynamicsFilter": True, "filterValue": ["first"], "preFilterTaskId": "a"}),
                         stable_unit({"dynamicsFilter": True, "filterValue": ["second"], "preFilterTaskId": "b"}))
        self.assertNotEqual(stable_unit({"filterValue": ["first"]}), stable_unit({"filterValue": ["second"]}))

    def test_sandbox_plan_cannot_enter_production_and_confirmation_is_required(self):
        with TemporaryDirectory() as temp:
            plan = {"artifact_type": PLAN_TYPE, "version": 1, "selection": {}, "sandbox": True}
            plan["plan_sha256"] = canonical_sha256(plan)
            path = Path(temp) / "plan.json"
            path.write_text(json.dumps(plan), encoding="utf-8")
            args = SimpleNamespace(mode="apply", sandbox=False, input=path, plan_sha256=plan["plan_sha256"],
                                   confirm_production_write=True, confirm_sandbox_write=False, headed=True)
            with patch("read_dashboard.commands.period_date_rebind.import_playwright") as launch:
                with self.assertRaisesRegex(UsageError, "execution mode"):
                    cmd_period_date_rebind(args)
                args.sandbox = True
                args.confirm_production_write = False
                with self.assertRaisesRegex(UsageError, "sandbox confirmation"):
                    cmd_period_date_rebind(args)
                launch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
