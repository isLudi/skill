"""One explicit, hash-bound existing-formula transaction in a named sandbox.

This is candidate-interface verification, not a production formula adapter.
It never publishes, changes schema, creates fields or promotes a capability.
"""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

from _shared.errors import UsageError
from _shared.config import RUNTIME_DIR
from .dashboard_change import artifact_sha256, canonical_sha256
from .dashboard_write_adapters import _formula_item, _formula_projection, _write_formula, _write_unit_detail
from .edit_profile import fetch_dataset_fields, fetch_edit_unit_detail
from .pivot_rebind import project_unit_field_state
from .profile import default_unit_value_payload, post_json
from .constants import UNIT_VALUE_API


def require(condition: bool, message: str) -> None:
    if not condition:
        raise UsageError(message)


def load_probe_plan(path: Path, expected_hash: str, args: Any) -> dict:
    plan = json.loads(path.read_text(encoding="utf-8"))
    require(canonical_sha256(plan) == expected_hash, "Formula probe plan Hash does not match.")
    require(set(plan) == {"artifact_type", "domain", "dashboard_id", "dashboard_name", "profile_sha256",
                         "subject_id", "model_id", "unit_id", "formula_id", "formula_name",
                         "expected_formula_sha256", "new_expression", "source_fields",
                         "isolation_receipt_path", "isolation_receipt_sha256", "isolation_build_plan_path",
                         "refresh_units"}, "Unexpected formula probe plan fields.")
    require(plan["artifact_type"] == "SandboxExistingFormulaProbePlan" and args.operation == "update_formula",
            "Controlled probes only support one existing formula.")
    require(plan["domain"] == args.domain and plan["dashboard_id"] == args.sandbox_dashboard_id
            and plan["dashboard_name"] == args.expected_dashboard_name, "Formula probe sandbox identity mismatch.")
    require(any(marker in plan["dashboard_name"].lower() for marker in ("沙箱", "测试", "sandbox", "test", "p4a")),
            "Formula probe target must be an explicitly named sandbox.")
    require(re.fullmatch(r"customized_\d+", plan["formula_id"]) is not None
            and re.fullmatch(r"unit_\d+", plan["unit_id"]) is not None, "Invalid exact formula or unit identity.")
    require(type(plan["subject_id"]) is int and plan["subject_id"] > 0
            and type(plan["model_id"]) is int and plan["model_id"] > 0, "Invalid subject/model identity.")
    expression = plan["new_expression"]
    require(isinstance(expression, str) and 1 <= len(expression) <= 8000
            and not re.search(r";|\b(select|insert|delete|update|drop|create|alter|grant)\b|https?://", expression, re.I),
            "A formula probe accepts only one calculation expression.")
    fields = plan["source_fields"]
    require(isinstance(fields, list) and 1 <= len(fields) <= 8, "Bind all exact formula inputs.")
    for field in fields:
        require(set(field) == {"field_id", "field_name", "org_param_type"}
                and re.fullmatch(r"\d+", field["field_id"]) is not None
                and re.fullmatch(r"[a-zA-Z_][a-zA-Z_0-9]*", field["field_name"]) is not None
                and field["org_param_type"] in (1, 2), "Invalid physical formula input.")
    require(len({field["field_id"] for field in fields}) == len(fields), "Duplicate formula input.")
    require(set(re.findall(r"\$\{([^}]+)\}", expression)) == {field["field_name"] for field in fields},
            "Expression inputs do not match the bound physical fields.")
    receipt = json.loads(Path(plan["isolation_receipt_path"]).read_text(encoding="utf-8"))
    receipt_hash = artifact_sha256(receipt, "dashboard_build_receipt_sha256")
    require(receipt_hash == plan["isolation_receipt_sha256"] == receipt.get("dashboard_build_receipt_sha256")
            and receipt.get("ok") is True and receipt.get("status") == "applied"
            and receipt.get("dashboard_id") == plan["dashboard_id"] and receipt.get("domain") == plan["domain"],
            "A verified creation receipt for this isolated sandbox is required.")
    require(any(resource.get("resource_type") == "calculated_column" and resource.get("field_id") == plan["formula_id"]
                and str(resource.get("subject_id")) == str(plan["subject_id"])
                for resource in receipt.get("created_resources", [])),
            "Only a formula created in this isolated sandbox may be probed; inherited production formulas are forbidden.")
    build = json.loads(Path(plan["isolation_build_plan_path"]).read_text(encoding="utf-8"))
    build_hash = artifact_sha256(build, "dashboard_build_plan_sha256")
    require(build_hash == build.get("dashboard_build_plan_sha256") == receipt.get("dashboard_build_plan_sha256"),
            "Sandbox creation plan and receipt do not bind the same exact Hash.")
    require(any(dataset.get("config", {}).get("subject_identity_policy") == "dashboard_scoped_clone"
                and str(dataset.get("application_model_id")) == str(plan["model_id"])
                and str(dataset.get("subject_id")) != str(plan["subject_id"]) for dataset in build["datasets"]),
            "The formula probe requires a separately allocated cloned subject, not the source production subject.")
    require(isinstance(plan["refresh_units"], list) and len(plan["refresh_units"]) <= 8, "Invalid neutral unit-refresh scope.")
    created_units = {resource.get("unit_id") for resource in receipt.get("created_resources", [])
                     if str(resource.get("subject_id")) == str(plan["subject_id"])}
    for unit in plan["refresh_units"]:
        require(set(unit) == {"unit_id", "before_sha256"} and unit["unit_id"] in created_units,
                "Only units created in this same isolated sandbox may be neutrally refreshed.")
    require(not (RUNTIME_DIR / "formula-probe-attempts" / f"{expected_hash}.json").exists(),
            "This exact probe was already attempted; read its ledger instead of repeating it.")
    return plan


def validate_probe_state(plan: dict, profile: dict, item: dict, fields: list[dict]) -> None:
    require(profile["domain"] == plan["domain"] and profile["dashboard_id"] == plan["dashboard_id"]
            and profile["dashboard_name"] == plan["dashboard_name"] and profile["profile_sha256"] == plan["profile_sha256"],
            "Formula probe full sandbox profile drifted.")
    require(any(str(unit.get("unit_id")) == plan["unit_id"] for unit in profile["data_units"]),
            "Formula probe unit is outside its sandbox.")
    subjects = {(str(dataset.get("source", {}).get("subject_id")), str(dataset.get("source", {}).get("application_model_id")))
                for dataset in profile["datasets"]}
    require((str(plan["subject_id"]), str(plan["model_id"])) in subjects,
            "Probe subject/model is outside the sandbox's selected datasets.")
    matched = [formula for formula in profile["formulas"] if formula["formula_id"] == plan["formula_id"]]
    require(len(matched) == 1 and matched[0]["name"] == plan["formula_name"], "Formula is not selected in the sandbox.")
    require(str(item.get("subjectId")) == str(plan["subject_id"]) and item.get("columnKey") == plan["formula_id"]
            and item.get("columnName") == plan["formula_name"], "Formula has a different subject or identity.")
    require(canonical_sha256(_formula_projection(item)) == plan["expected_formula_sha256"], "Formula metadata drifted.")
    catalog = {str(field.get("key") or field.get("field_id")): field for field in fields}
    for expected in plan["source_fields"]:
        actual = catalog.get(expected["field_id"], {})
        require(actual.get("title") == expected["field_name"] and actual.get("org_param_type") == expected["org_param_type"],
                "Formula input is missing or has a different identity/type in the sandbox subject.")


def execute_formula_probe(page: Any, plan: dict, profile: dict, observations: list[dict]) -> dict:
    datasets = fetch_dataset_fields(page, plan["dashboard_id"], [plan["subject_id"]], [2], [])
    require(len(datasets) == 1 and not datasets[0].get("error"), "Sandbox field-tree read failed.")
    before = _formula_item(page, plan["formula_id"])
    validate_probe_state(plan, profile, before, datasets[0]["fields"])
    confirmed = _formula_item(page, plan["formula_id"])
    require(canonical_sha256(_formula_projection(confirmed)) == plan["expected_formula_sha256"],
            "Formula changed during pre-write double-read.")
    original_units = {}
    for unit in plan.get("refresh_units", []):
        detail = fetch_edit_unit_detail(page, unit["unit_id"], plan["dashboard_id"], "draft")
        require(canonical_sha256(project_unit_field_state(detail)) == unit["before_sha256"], "Neutral refresh unit drifted.")
        original_units[unit["unit_id"]] = detail
    payload = copy.deepcopy(before)
    payload["formula"] = plan["new_expression"]
    payload["dependencyIndicators"] = [{"paramId": field["field_id"], "orgParamType": field["org_param_type"],
                                        "needBoundaryValue": False} for field in plan["source_fields"]]
    digest = canonical_sha256(plan)
    ledger = RUNTIME_DIR / "formula-probe-attempts"
    ledger.mkdir(parents=True, exist_ok=True)
    marker = ledger / f"{digest}.json"
    require(not marker.exists(), "This exact probe was already attempted; inspect its receipt instead of repeating it.")
    with marker.open("x", encoding="utf-8") as stream:
        json.dump({"plan_sha256": digest, "dashboard_id": plan["dashboard_id"], "formula_id": plan["formula_id"],
                   "started_at": datetime.now(timezone.utc).isoformat()}, stream)
    writes: list[dict] = []
    result = {"status": "started", "writes": writes, "before_formula": _formula_projection(before),
              "value_responses": {}, "production_authority": False}
    expected_bindings = {(field["field_id"], field["org_param_type"]) for field in plan["source_fields"]}

    def is_after(item):
        bindings = {(str(field["paramId"]), field["orgParamType"]) for field in item.get("dependencyIndicators", [])}
        return item.get("formula") == plan["new_expression"] and bindings == expected_bindings

    try:
        _write_formula(page, payload, writes)
        after = _formula_item(page, plan["formula_id"])
        require(is_after(after), "Acknowledged formula probe did not read back its exact expression/dependencies.")
        require({k: v for k, v in _formula_projection(before).items() if k not in {"formula", "dependencyIndicators"}}
                == {k: v for k, v in _formula_projection(after).items() if k not in {"formula", "dependencyIndicators"}},
                "Formula probe changed unrelated column metadata.")
        result["after_formula"] = _formula_projection(after)
        for uid, detail in original_units.items():
            current = fetch_edit_unit_detail(page, uid, plan["dashboard_id"], "draft")
            require(canonical_sha256(project_unit_field_state(current)) == canonical_sha256(project_unit_field_state(detail)),
                    "Unit fields changed before neutral refresh.")
            _write_unit_detail(page, plan["dashboard_id"], detail, writes)
        require(len(profile["data_units"]) <= 8, "A controlled formula probe is limited to eight sandbox units.")
        for unit in profile["data_units"]:
            unit_id = unit["unit_id"]
            request = default_unit_value_payload(unit_id, 2000)
            request.update(isConfig=True, versionId="draft")
            try:
                result["value_responses"][unit_id] = post_json(page, UNIT_VALUE_API, request, timeout_ms=45000)
            except Exception as exc:
                result["value_responses"][unit_id] = {"error": str(exc)}
        result["status"] = "value_capture_complete"
    except Exception as exc:
        result["status"] = "probe_error"
        result["error"] = str(exc)
    finally:
        try:
            current = _formula_item(page, plan["formula_id"])
            if canonical_sha256(_formula_projection(current)) != plan["expected_formula_sha256"]:
                require(is_after(current), "A third formula state was observed; automatic restoration is blocked.")
                _write_formula(page, before, writes)
            restored = _formula_item(page, plan["formula_id"])
            require(canonical_sha256(_formula_projection(restored)) == plan["expected_formula_sha256"],
                    "The sandbox formula was not restored to the exact baseline.")
            for uid, detail in original_units.items():
                current = fetch_edit_unit_detail(page, uid, plan["dashboard_id"], "draft")
                require(canonical_sha256(project_unit_field_state(current)) == canonical_sha256(project_unit_field_state(detail)),
                        "A neutral-refresh unit reached a third state; recovery is blocked.")
                _write_unit_detail(page, plan["dashboard_id"], detail, writes)
            result["restored"] = True
        except Exception as exc:
            result["restored"] = False
            result["recovery_error"] = str(exc)
        # APIRequestContext requests do not emit browser page request events.
        # These observations come from the existing recorded HTTP adapter.
        observations.extend({key: value for key, value in {**write, "blocked": False}.items()
                             if key in {"method", "host", "url_path", "payload_bytes", "request_key_paths",
                                        "response_status", "response_content_type", "blocked"}} for write in writes)
        (ledger / f"{digest}-result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    result["query_values_not_yet_verified"] = True
    return result
