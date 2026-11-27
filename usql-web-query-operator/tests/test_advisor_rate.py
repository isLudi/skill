import copy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from _shared.errors import UsageError
from read_dashboard.commands import advisor_rate as rate
from read_dashboard.dashboard_write_adapters import _formula_projection


def selection():
    return {"domain": "qingcheng", "dashboard_id": rate.BOARD, "dashboard_name": "转化数据看板", "owner": "lvshuai01",
            "model_id": 2460, "subject_id": 216472, "formula_id": rate.FORMULA,
            "helpers": [{"field_name": n, "org_param_type": t, "field_id": str(i)} for i, (n, t) in enumerate(rate.HELPERS, 1)],
            "targets": [{"component_id": "node_a", "unit_id": "unit_1"}], "period": "20261120期",
            "period_filter": {"field_id": "408276", "filter_id": "public_filter_1"}}


@pytest.mark.parametrize("key,value", [("domain", "market_consultant"), ("dashboard_id", "dashboard_1"),
                                      ("subject_id", 216470), ("model_id", 1), ("formula_id", "customized_1")])
def test_rejects_other_domain_board_subject_model_or_formula(key, value):
    s = selection()
    s[key] = value
    with pytest.raises(UsageError):
        rate.validate_selection(s)


def test_dependency_order_is_not_an_unordered_set():
    s = selection()
    rate.validate_selection(s)
    s["helpers"].reverse()
    with pytest.raises(UsageError, match="first-occurrence order"):
        rate.validate_selection(s)


def test_definition_preserves_identity_and_unrelated_properties():
    s = selection()
    before = {"columnKey": rate.FORMULA, "columnDesc": "keep", "formula": "old", "globalFilterSpecialConfig": [{"key": "keep"}]}
    after = rate.definition(before, s)
    assert after["formula"] == rate.EXPRESSION and before["formula"] == "old"
    assert after["columnKey"] == before["columnKey"] and after["globalFilterSpecialConfig"] == before["globalFilterSpecialConfig"]
    assert [x["paramId"] for x in after["dependencyIndicators"]] == ["1", "2", "3"]


@pytest.mark.parametrize("value", [None, "-0.1", "1.00001", "NaN"])
def test_null_signed_scope_or_impossible_rate_blocks_acceptance(value):
    with pytest.raises((UsageError, ArithmeticError)):
        rate.verify_rates({"u": {"data": [{"f": value}], "totalData": {"f": "0"}}}, {"u": "f"})


def test_values_are_complete_and_each_rate_is_bounded():
    raw = {"u": {"data": [{"f": "0"}, {"f": "0.66666"}, {"f": "1"}], "totalData": {"f": "0.5"}}}
    assert rate.verify_rates(raw, {"u": "f"})["u"]["total_rate"] == "0.5"


@pytest.fixture
def transaction(monkeypatch):
    before = _formula_projection({"columnKey": rate.FORMULA, "formula": "old", "columnName": "破蛋率", "dependencyIndicators": []})
    s = selection()
    state = {"formula": copy.deepcopy(before), "writes": []}
    plan = {"plan_sha256": "a" * 64, "selection": s, "baseline": {"formula": before, "units": {"unit_1": {}}, "schema_sha256": "schema",
                                             "profile_sha256": "baseline", "published": {"keep": True}}}
    monkeypatch.setattr(rate, "_formula_item", lambda *a: copy.deepcopy(state["formula"]))
    monkeypatch.setattr(rate, "_units_equal", lambda *a: None)
    def write(page, item, log):
        state["writes"].append(copy.deepcopy(item))
        state["formula"] = copy.deepcopy(item)
    monkeypatch.setattr(rate, "_write_formula", write)
    monkeypatch.setattr(rate, "_write_unit_detail", lambda *a: None)
    monkeypatch.setattr(rate, "_write_dashboard_schema", lambda *a: None)
    monkeypatch.setattr(rate, "_profile", lambda *a: ({}, {"profile_sha256": "baseline"}))
    monkeypatch.setattr(rate, "_published", lambda *a: {"keep": True})
    monkeypatch.setattr(rate, "_expected_profile", lambda *a: None)
    monkeypatch.setattr(rate, "_values", lambda *a: {"unit_1": {"data": [{rate.FORMULA: "0.5"}], "totalData": {rate.FORMULA: "0.5"}}})
    return plan, state


def test_failed_value_read_restores_original_formula_and_full_profile(transaction, monkeypatch, tmp_path):
    plan, state = transaction
    monkeypatch.setattr(rate, "_values", lambda *a: (_ for _ in ()).throw(UsageError("query failed")))
    receipt = {"writes": []}
    with pytest.raises(UsageError, match="query failed"):
        rate.mutate(None, plan, {}, {}, {"unit_1": {}}, tmp_path, receipt)
    assert state["formula"] == plan["baseline"]["formula"] and len(state["writes"]) == 2
    assert receipt["restored_profile_sha256"] == "baseline"


def test_success_keeps_reviewed_draft_and_does_not_publish(transaction, tmp_path):
    plan, state = transaction
    receipt = {"writes": []}
    rate.mutate(None, plan, {}, {}, {"unit_1": {}}, tmp_path, receipt)
    assert receipt["saved_draft_verified"] is True and state["formula"]["formula"] == rate.EXPRESSION
    assert len(state["writes"]) == 1 and receipt["published_formulas_unchanged"] is True


def test_third_state_stops_restoration(transaction, monkeypatch, tmp_path):
    plan, state = transaction
    def drift(*a):
        state["formula"]["formula"] = "external"
        raise UsageError("query failed")
    monkeypatch.setattr(rate, "_values", drift)
    with pytest.raises(UsageError, match="Third formula state"):
        rate.mutate(None, plan, {}, {}, {"unit_1": {}}, tmp_path, {"writes": []})
    assert state["formula"]["formula"] == "external" and len(state["writes"]) == 1
