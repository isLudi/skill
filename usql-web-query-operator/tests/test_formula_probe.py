import copy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from _shared.errors import UsageError
from read_dashboard import formula_probe as probe
from read_dashboard.dashboard_change import canonical_sha256
from read_dashboard.dashboard_write_adapters import _formula_projection


@pytest.fixture
def scenario(monkeypatch, tmp_path):
    monkeypatch.setattr(probe, "RUNTIME_DIR", tmp_path)
    before = {"subjectId": 20, "columnKey": "customized_1", "columnName": "Test rate", "columnDesc": "keep",
              "dataType": 1, "formula": "sum(${old})", "dependencyIndicators": [{"paramId": "10", "orgParamType": 1}],
              "globalFilterSpecialConfig": []}
    profile = {"domain": "qingcheng", "dashboard_id": "dashboard_1", "dashboard_name": "Test sandbox",
               "profile_sha256": "f" * 64, "data_units": [{"unit_id": "unit_1"}],
               "formulas": [{"formula_id": "customized_1", "name": "Test rate"}],
               "datasets": [{"source": {"subject_id": 20, "application_model_id": 2460}}]}
    plan = {"domain": "qingcheng", "dashboard_id": "dashboard_1", "dashboard_name": "Test sandbox",
            "profile_sha256": "f" * 64, "subject_id": 20, "model_id": 2460,
            "unit_id": "unit_1", "formula_id": "customized_1", "formula_name": "Test rate",
            "expected_formula_sha256": canonical_sha256(_formula_projection(before)), "new_expression": "sum(${income})",
            "source_fields": [{"field_id": "11", "field_name": "income", "org_param_type": 1}]}
    state = {"item": copy.deepcopy(before), "writes": []}
    monkeypatch.setattr(probe, "fetch_dataset_fields", lambda *a: [{"fields": [{"key": "11", "title": "income", "org_param_type": 1}]}])
    monkeypatch.setattr(probe, "_formula_item", lambda *a: copy.deepcopy(state["item"]))
    def write(page, item, log):
        state["writes"].append(copy.deepcopy(item))
        state["item"] = copy.deepcopy(item)
        log.append({"method": "POST", "host": "udata.baijia.com", "url_path": "/model/customized/column/saveAndUpdate",
                    "payload_bytes": 1, "request_key_paths": [], "response_status": 200, "response_content_type": "application/json"})
    monkeypatch.setattr(probe, "_write_formula", write)
    monkeypatch.setattr(probe, "post_json", lambda *a, **k: {"data": {"unit_1": {"data": []}}})
    return plan, profile, before, state


def test_one_candidate_write_readback_and_exact_restoration(scenario):
    plan, profile, before, state = scenario
    observations = []
    result = probe.execute_formula_probe(object(), plan, profile, observations)
    assert result["restored"] is True and result["production_authority"] is False
    assert len(state["writes"]) == len(observations) == 2
    assert state["item"] == before


def test_same_hash_cannot_be_repeated_after_successful_restore(scenario):
    plan, profile, before, state = scenario
    probe.execute_formula_probe(object(), plan, profile, [])
    with pytest.raises(UsageError, match="already attempted"):
        probe.execute_formula_probe(object(), plan, profile, [])
    assert len(state["writes"]) == 2


def test_query_error_does_not_leave_candidate_formula_active(scenario, monkeypatch):
    plan, profile, before, state = scenario
    def fail(*a, **k):
        raise UsageError("Function not supported")
    monkeypatch.setattr(probe, "post_json", fail)
    result = probe.execute_formula_probe(object(), plan, profile, [])
    assert result["restored"] is True
    assert "error" in result["value_responses"]["unit_1"]
    assert state["item"] == before


def test_third_state_blocks_automatic_restoration_and_retains_receipt(scenario, monkeypatch):
    plan, profile, before, state = scenario
    def drift(*a, **k):
        state["item"]["formula"] = "somebody_else"
        return {"data": {}}
    monkeypatch.setattr(probe, "post_json", drift)
    result = probe.execute_formula_probe(object(), plan, profile, [])
    assert result["restored"] is False and "third formula state" in result["recovery_error"]
    assert len(state["writes"]) == 1 and state["item"]["formula"] == "somebody_else"


def test_profile_drift_fails_before_any_write(scenario):
    plan, profile, before, state = scenario
    profile["profile_sha256"] = "0" * 64
    with pytest.raises(UsageError, match="profile drifted"):
        probe.execute_formula_probe(object(), plan, profile, [])
    assert not state["writes"]


def test_wrong_subject_or_physical_field_is_rejected(scenario):
    plan, profile, before, state = scenario
    plan["source_fields"][0]["field_id"] = "99"
    with pytest.raises(UsageError, match="input is missing"):
        probe.execute_formula_probe(object(), plan, profile, [])
    assert not state["writes"]
