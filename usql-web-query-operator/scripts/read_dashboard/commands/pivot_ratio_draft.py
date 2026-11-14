"""Plan and apply ratio columns on one existing Taitan pivot draft."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import re
from typing import Any

from _shared.browser import import_playwright, launch_context
from _shared.config import RUNTIME_DIR
from _shared.fs_utils import ensure_runtime, safe_artifact_dir
from usql_web_query.query_auth import verify_query_identity

from ..common import write_json
from ..dashboard_change import _core_api, canonical_sha256, require_complete_profile
from ..dashboard_write_adapters import _formula_item, _write_dashboard_schema, _write_formula, _write_unit_detail
from ..edit_profile import EDIT_API_ROOT, build_edit_url, fetch_dataset_fields, fetch_edit_dashboard_config, fetch_edit_unit_detail, profile_edit_dashboard
from ..pivot_ratio_fields import OPERATION, expected_rate, formula_definition, formula_matches, projection, replace_ratio_fields, require, validate_selection
from ..profile import default_unit_value_payload, fetch_dashboard_config, fetch_unit_detail, parse_dashboard_html, post_json
from ..write_capabilities import capability_by_operation, load_capability_registry


PLAN_TYPE = "DashboardPivotRatioDraftPlan"
ADAPTER = "read_dashboard.commands.pivot_ratio_draft.cmd_pivot_ratio_draft"
SANDBOX_TEMPLATE = {
    "fieldType": 1,
    "frontRender": 0,
    "format": {
        "measureType": "main", "dataType": 1, "numberType": 2, "isAggregation": False,
        "changeParamType": 4, "orgParamType": 4, "filterType": ["aggregationFilter"],
        "columnVisualStyle": {
            "header": {"color": "#000", "textAlign": "center", "underline": False,
                       "fontSize": 11, "fontStyle": "normal", "fontWeight": "bold"},
            "body": {"color": "#000", "bgColor": "#ffffff", "textAlign": "center", "underline": False,
                     "fontSize": 11, "fontStyle": "normal", "fontWeight": "normal"},
        },
    },
}


@dataclass
class LiveDraft:
    schema: dict
    profile: dict
    unit: dict
    template: dict
    plan: dict


def _write_backup(artifacts: Path, dashboard_id: str, plan_sha256: str, payload: dict) -> Path:
    path = artifacts / "pivot-ratio" / dashboard_id / f"{plan_sha256}-baseline.json"
    require(not path.exists(), "An immutable baseline backup already exists for this plan; inspect it before continuing.")
    write_json(payload, path)
    return path


def _config(page, s: dict) -> dict:
    cfg = fetch_edit_dashboard_config(page, s["dashboard_id"], "draft")
    require(cfg.get("dashboardId") == s["dashboard_id"] and cfg.get("dashboardName") == s["dashboard_name"]
            and cfg.get("haveEditPermission") is True and s["owner"] in (cfg.get("ownerList") or []),
            "Live dashboard name, ID, ownership or edit permission differs from the plan.")
    return cfg


def _profile(page, s: dict, artifacts: Path) -> tuple[dict, dict]:
    raw = profile_edit_dashboard(page, s["dashboard_id"], None, build_edit_url(s["dashboard_id"]),
                                 "draft", artifacts, False, True, s["domain"])
    return raw, require_complete_profile(raw)


def _checked_fields(tree: list[dict], s: dict) -> list[dict]:
    result = []
    for x in (s["denominator"], *(r["numerator"] for r in s["ratios"])):
        matching = [f for f in tree if f.get("title") == x["field_name"]]
        require(len(matching) == 1, f"Ambiguous or missing field name {x['field_name']}.")
        field = matching[0]
        require(field.get("key") == x["field_id"] and field.get("org_param_type") == 1
                and field.get("change_param_type") == 1 and field.get("data_type") == 1
                and field.get("is_choice") is True,
                f"The approved subject has no selectable physical metric {x['field_name']}.")
        result.append(field)
    return result


def _formula_lookup(page, tree: list[dict], definition: dict) -> str | None:
    name = definition["columnName"]
    ranked = [f for f in tree if f.get("title") == name]
    require(len(ranked) <= 1, f"Formula name is ambiguous: {name}.")
    if not ranked:
        return None
    field_id = str(ranked[0].get("key") or "")
    require(re.fullmatch(r"customized_\d+", field_id)
            and formula_matches(_formula_item(page, field_id), definition, field_id),
            f"Existing field named {name!r} conflicts with the reviewed formula.")
    return field_id


def _tree(page, s: dict) -> list[dict]:
    trees = fetch_dataset_fields(page, s["dashboard_id"], [s["subject_id"]], [2], [])
    require(len(trees) == 1 and not trees[0].get("error") and trees[0].get("fields"),
            "The subject field tree is unavailable.")
    return trees[0]["fields"]


def _published_hashes(page, s: dict) -> dict:
    published = fetch_dashboard_config(page, s["dashboard_id"])
    require(published.get("dashboardId") == s["dashboard_id"] and published.get("dashboardName") == s["dashboard_name"],
            "Published dashboard identity could not be confirmed.")
    published_unit = fetch_unit_detail(page, s["unit_id"])
    require(published_unit.get("unitId") == s["unit_id"], "Published unit identity could not be confirmed.")
    return {"schema": canonical_sha256(parse_dashboard_html(published)), "unit": canonical_sha256(projection(published_unit))}


def _validate_live_filters(profile: dict, s: dict, checks: list[dict]) -> None:
    aliases = {f["field_id"] for c in profile["components"] if c["component_id"] == s["component_id"]
               for f in c["fields"]["dimensions"]}
    bound = {(f["field_id"], f["filter_id"]) for f in profile["public_filters"]
             if s["component_id"] in f["target_component_ids"]}
    for check in checks:
        for field_id, filter_id, value in check["filters"]:
            # The caller may filter a verified row dimension that shares the
            # same model pivot. Its field ID remains explicit even when the
            # visible public control uses a separate display field.
            require((field_id, filter_id) in bound
                    or (field_id in aliases and any(pair[1] == filter_id for pair in bound)),
                    f"Check {check['label']} uses a filter outside the selected pivot.")


def _template(unit: dict, s: dict, sandbox: bool) -> dict:
    items = [
        f for f in unit["unitMeasureList"] if f["fieldId"] in s["remove_ids"]
        and (f.get("format") or {}).get("numberType") == 2
        and ((f["format"].get("columnVisualStyle") or {}).get("header") or {}).get("bgColor") == s["header_color"]
    ]
    if items:
        return items[0]
    require(sandbox, "A live matching percentage style template is required for a production change.")
    return SANDBOX_TEMPLATE


def _live(page, s: dict, artifacts: Path, sandbox: bool, checks: list[dict]) -> LiveDraft:
    schema = parse_dashboard_html(_config(page, s))
    raw, profile = _profile(page, s, artifacts)
    selected = [c for c in profile["components"] if c["component_id"] == s["component_id"]]
    require(len(selected) == 1 and selected[0]["unit_id"] == s["unit_id"]
            and selected[0]["component_type"] == "u_pivot" and selected[0]["title"] == s["unit_name"],
            "The selected component no longer resolves to the exact pivot.")
    unit = fetch_edit_unit_detail(page, s["unit_id"], s["dashboard_id"], "draft")
    require(unit.get("unitId") == s["unit_id"] and unit.get("unitType") == "u_pivot" and unit.get("modelId") == s["model_id"]
            and unit.get("unitName") == s["unit_name"] and unit.get("dashboardModel") == {
                "applicationModelId": s["model_id"], "dashboardId": s["dashboard_id"], "subjectId": s["subject_id"], "modelType": 2,
            }, "The unit, model or subject changed.")
    trees = [t for t in raw["dataset_fields"] if t.get("subject_id") == s["subject_id"] and t.get("model_type") == 2]
    require(len(trees) == 1 and trees[0].get("fields"), "Expected exactly one verified field tree.")
    tree = trees[0]["fields"]
    physical = _checked_fields(tree, s)
    _validate_live_filters(profile, s, checks)
    template = _template(unit, s, sandbox)
    projected = replace_ratio_fields(unit, s, [f"customized_{1000+i}" for i in range(len(s["ratios"]))], template)
    definitions = [formula_definition(r, s["denominator"], s["subject_id"]) for r in s["ratios"]]
    plan = {
        "artifact_type": PLAN_TYPE, "schema_version": "1.0.0", "sandbox": sandbox, "selection": s,
        "profile_sha256": profile["profile_sha256"], "schema_sha256": canonical_sha256(schema),
        "unit_sha256": canonical_sha256(projection(unit)),
        "published": None if sandbox else _published_hashes(page, s),
        "fields_sha256": canonical_sha256(physical),
        "projected_names": projected["format"]["fieldMeasureNameSortList"],
        "existing_formulas": {f["columnName"]: _formula_lookup(page, tree, f) for f in definitions},
        "formula_definitions": definitions, "checks": checks,
    }
    plan["plan_sha256"] = canonical_sha256(plan)
    return LiveDraft(schema, profile, unit, template, plan)


def _unit_read(page, s: dict) -> dict:
    return fetch_edit_unit_detail(page, s["unit_id"], s["dashboard_id"], "draft")


def _expect_before(page, live: LiveDraft) -> None:
    s, plan = live.plan["selection"], live.plan
    require(canonical_sha256(parse_dashboard_html(_config(page, s))) == plan["schema_sha256"]
            and all(canonical_sha256(projection(_unit_read(page, s))) == plan["unit_sha256"] for _ in range(2)),
            "The draft schema or unit drifted immediately before a write.")


def _resolve_formulas(page, live: LiveDraft, receipt: dict) -> list[str]:
    plan = live.plan
    s = plan["selection"]
    ids = []
    for definition in plan["formula_definitions"]:
        name = definition["columnName"]
        _expect_before(page, live)
        tree = _tree(page, s)
        require(canonical_sha256(_checked_fields(tree, s)) == plan["fields_sha256"], "Physical formula dependency metadata drifted.")
        field_id = _formula_lookup(page, tree, definition)
        require(field_id == plan["existing_formulas"][name], f"Formula {name} drifted after planning.")
        resource = {"name": name, "field_id": field_id, "created": field_id is None}
        receipt["formulas"].append(resource)
        if field_id is None:
            resource["status"] = "create_attempted"
            _write_formula(page, definition, receipt["writes"])
            resource["status"] = "created_unverified"
            field_id = _formula_lookup(page, _tree(page, s), definition)
            require(field_id, f"Created formula {name} did not resolve from the exact subject.")
            resource["field_id"] = field_id
        resource["status"] = "verified"
        ids.append(field_id)
    return ids


def _project_profile(profile: dict, s: dict, removed_or_new: set[str]) -> dict:
    component = s["component_id"]
    unaffected = {key: profile[key] for key in ("layout", "public_filters", "component_filters", "datasets", "theme")}
    unaffected["components"] = [c for c in profile["components"] if c["component_id"] != component]
    unaffected["data_units"] = [u for u in profile["data_units"] if u["unit_id"] != s["unit_id"]]
    formulas = []
    for row in profile["formulas"]:
        if row["formula_id"] in removed_or_new and component in row["component_ids"]:
            formula = dict(row)
            formula["component_ids"] = [x for x in row["component_ids"] if x != component]
            if not formula["component_ids"]:
                continue
            formula["shared"] = len(formula["component_ids"]) > 1
            formulas.append(formula)
        else:
            formulas.append(row)
    unaffected["formulas"] = formulas
    return unaffected


def _verify_values(page, live: LiveDraft, formula_ids: list[str], target: dict) -> list[dict]:
    from decimal import Decimal

    plan = live.plan
    s = plan["selection"]
    ids = [f["fieldId"] for f in live.unit["unitDimensionList"]]
    measures = [f["fieldId"] for f in target["unitMeasureList"]]
    results = []
    for check in plan["checks"]:
        payload = default_unit_value_payload(s["unit_id"], 100)
        payload.update(isConfig=True, versionId="draft")
        for field_id, filter_id, value in check["filters"]:
            payload["publicFilterList"].append({
                "paramId": field_id, "fieldId": field_id, "filterUnitId": filter_id,
                "filterValue": [value], "condition": "in", "orgParamType": 2, "isSelectAll": 0,
            })
        value = post_json(page, f"{EDIT_API_ROOT}/value/unit", payload, timeout_ms=60_000)["data"].get(s["unit_id"])
        require(value and value.get("unitId") == s["unit_id"] and value.get("hasMore") is False,
                f"Exact complete value readback failed for {check['label']}.")
        titles = [str(f.get("paramId") or f.get("fieldId")) for f in value["title"]]
        require([x for x in titles if x in measures] == measures and not set(s["remove_ids"]).intersection(titles),
                "Result headers did not return the saved measure order.")
        key = check["row"]
        if key:
            rows = [row for row in value.get("data", []) if [row.get(field_id) for field_id in ids] == key]
            require(len(rows) == 1, f"Expected one row for {check['label']}; found {len(rows)}.")
        else:
            rows = [value.get("totalData") or {}]
            require(rows[0], f"Grand total missing for {check['label']}.")
        row = rows[0]
        den = check["denominator"]
        den_id = s["denominator"]["field_id"]
        require(plan["sandbox"] or den_id in titles, "The production pivot did not return the physical denominator.")
        if den_id in titles:
            require(Decimal(str(row[den_id])) == den, f"Denominator differs for {check['label']}.")
        observed = [Decimal(str(row[field_id])) for field_id in formula_ids]
        expected = [expected_rate(num, den) for num in check["numerators"]]
        require(all(actual.is_finite() and abs(actual - goal) <= Decimal("0.00000001")
                    for actual, goal in zip(observed, expected, strict=True)),
                f"Calculated ratio differs for {check['label']}: {observed} vs {expected}.")
        if den_id in titles and den:
            require(all(abs(actual * den - raw_count) <= Decimal("0.00001")
                        for actual, raw_count in zip(observed, check["numerators"], strict=True)),
                    f"Physical numerator totals do not reconcile for {check['label']}.")
        results.append({"label": check["label"], "row": key, "filters": check["filters"], "denominator": den,
                        "denominator_read_back": den_id in titles,
                        "numerators": check["numerators"], "observed_ratios": [str(x) for x in observed],
                        "task_id": value.get("totalTaskId")})
    return results


def _restore(page, live: LiveDraft, target: dict, artifacts: Path, receipt: dict) -> None:
    s, plan = live.plan["selection"], live.plan
    draft_hash = canonical_sha256(parse_dashboard_html(_config(page, s)))
    require(draft_hash == plan["schema_sha256"], "The saved schema changed, so automatic pivot recovery stopped.")
    current_hash = canonical_sha256(projection(_unit_read(page, s)))
    if current_hash != plan["unit_sha256"]:
        require(current_hash == canonical_sha256(projection(target))
                and canonical_sha256(projection(_unit_read(page, s))) == current_hash,
                "Current pivot differs from both assessed configurations; recovery stopped.")
        _write_unit_detail(page, s["dashboard_id"], live.unit, receipt["writes"])
        require(canonical_sha256(projection(_unit_read(page, s))) == plan["unit_sha256"], "Restored unit failed exact readback.")
        _write_dashboard_schema(page, s["dashboard_id"], s["dashboard_name"], live.schema, receipt["writes"], plan["schema_sha256"])
    _, restored = _profile(page, s, artifacts)
    require(restored["profile_sha256"] == plan["profile_sha256"], "The restored dashboard profile did not match the baseline.")
    receipt["restored_profile_sha256"] = restored["profile_sha256"]


def _mutate(page, live: LiveDraft, artifacts: Path, receipt: dict) -> None:
    plan, target = live.plan, None
    s = plan["selection"]
    try:
        formula_ids = _resolve_formulas(page, live, receipt)
        _expect_before(page, live)
        target = replace_ratio_fields(live.unit, s, formula_ids, live.template)
        _write_unit_detail(page, s["dashboard_id"], target, receipt["writes"])
        require(projection(_unit_read(page, s)) == projection(target), "Pivot field/style update did not read back exactly.")
        _write_dashboard_schema(page, s["dashboard_id"], s["dashboard_name"], live.schema, receipt["writes"], plan["schema_sha256"])
        require(projection(_unit_read(page, s)) == projection(target), "Saved pivot no longer matches the reviewed update.")
        require(canonical_sha256(parse_dashboard_html(_config(page, s))) == plan["schema_sha256"], "Draft layout or schema changed.")
        _, post = _profile(page, s, artifacts)
        require(_project_profile(post, s, set(formula_ids)) == _project_profile(live.profile, s, set(s["remove_ids"])),
                "The complete readback shows an out-of-scope change.")
        if not plan["sandbox"]:
            actual_public = _published_hashes(page, s)
            require(plan["published"] == actual_public, "The published dashboard schema or unit changed.")
            receipt["published_before_after"] = actual_public
        receipt["value_checks"] = _verify_values(page, live, formula_ids, target)
        receipt["post_profile_sha256"] = post["profile_sha256"]
        receipt["saved_draft_verified"] = True
        receipt["final_measure_count"] = len(target["unitMeasureList"])
    except Exception as exc:
        receipt["apply_error"] = str(exc)
        raise
    finally:
        try:
            if target is not None and (plan["sandbox"] or not receipt.get("saved_draft_verified")):
                _restore(page, live, target, artifacts, receipt)
        finally:
            receipt["retained_formulas_after_failure_or_sandbox"] = [
                f for f in receipt["formulas"]
                if f["created"] and (plan["sandbox"] or not receipt.get("saved_draft_verified"))
            ]


def _read(path: Path) -> dict:
    item = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(item, dict), "Expected a JSON object.")
    return item


def _validate_checks(checks: list[dict], ratio_count: int) -> None:
    require(isinstance(checks, list) and 1 <= len(checks) <= 100, "One to 100 value checks are required.")
    for c in checks:
        require(isinstance(c, dict) and set(c) == {"label", "row", "filters", "denominator", "numerators"}, "Invalid value check.")
        require(isinstance(c["label"], str) and c["label"] and isinstance(c["row"], list)
                and all(isinstance(x, str) for x in c["row"]), "A check requires a label and an exact row key.")
        require(type(c["denominator"]) is int and isinstance(c["numerators"], list)
                and len(c["numerators"]) == ratio_count and all(type(x) is int for x in c["numerators"]),
                "Expected one integer count for each numerator and the denominator.")
        for n in c["numerators"]:
            expected_rate(n, c["denominator"])
        require(isinstance(c["filters"], list) and len(c["filters"]) <= 2
                and all(isinstance(f, list) and len(f) == 3 and all(isinstance(x, str) for x in f)
                        and f[0].isdigit() and re.fullmatch(r"public_filter_\d+", f[1]) and f[2] for f in c["filters"]),
                "Invalid exact period/owner filter values.")


def cmd_pivot_ratio_draft(args) -> int:
    planning = args.mode == "plan"
    input_json = _read(args.input)
    s, checks = input_json.get("selection") or {}, input_json.get("checks")
    validate_selection(s, args.sandbox)
    _validate_checks(checks, len(s["ratios"]))
    require(args.domain == s["domain"], "Domain mismatch.")
    if not args.sandbox:
        _core_api()
        from text2sql_core.dashboard_domains import validate_dashboard_domain_registration

        status, diagnostics = validate_dashboard_domain_registration(s["dashboard_id"], args.domain)
        require(status.get("status") == "registered" and not diagnostics, "The production dashboard must have verified domain registration.")
    if not planning:
        digest = canonical_sha256({k: v for k, v in input_json.items() if k != "plan_sha256"})
        require(input_json.get("artifact_type") == PLAN_TYPE and input_json.get("sandbox") is args.sandbox
                and digest == input_json.get("plan_sha256") == args.plan_sha256,
                "Exact reviewed plan hash and sandbox mode are required.")
        if args.sandbox:
            require(args.confirm_sandbox_write and args.headed and not args.confirm_production_write,
                    "Sandbox writes require explicit confirmation and a headed browser.")
        else:
            require(args.confirm_production_write and not args.confirm_sandbox_write, "Production draft confirmation is required.")
            capability = capability_by_operation(load_capability_registry(), OPERATION)
            require(capability.get("maturity") == "verified" and capability.get("write_policy") == "allowlisted"
                    and capability.get("adapter") == ADAPTER, "This production adapter is not allowlisted.")
    require(args.state_path.is_file(), "An isolated authenticated account session is required.")
    ensure_runtime([args.artifacts_dir, args.output.parent])
    artifacts = safe_artifact_dir(args.artifacts_dir)
    with import_playwright()() as pw:
        browser, context = launch_context(pw, args.state_path, args.headed, args.browser_channel, None)
        try:
            page = context.new_page()
            verify_query_identity(page, s["owner"])
            page.goto(build_edit_url(s["dashboard_id"]), wait_until="domcontentloaded", timeout=45_000)
            live = _live(page, s, artifacts, args.sandbox, checks)
            if planning:
                write_json(live.plan, args.output)
                print(json.dumps({"ok": True, "plan_sha256": live.plan["plan_sha256"], "writes": 0}))
                return 0
            require(live.plan == input_json, "The live draft, physical fields, formulas or published baseline differ from the plan.")
            lock_dir = RUNTIME_DIR / "draft-rebind-locks"
            lock_dir.mkdir(parents=True, exist_ok=True)
            lock_path = lock_dir / f"{s['dashboard_id']}.lock"
            with lock_path.open("x", encoding="utf-8") as lock:
                lock.write(args.plan_sha256 + "\n")
            try:
                attempt = RUNTIME_DIR / "pivot-ratio-attempts" / s["dashboard_id"] / f"{args.plan_sha256}.attempt"
                attempt.parent.mkdir(parents=True, exist_ok=True)
                require(not attempt.exists(), "This exact plan has an earlier attempt. Inspect its write outcome.")
                backup = _write_backup(artifacts, s["dashboard_id"], args.plan_sha256,
                                       {"plan_sha256": args.plan_sha256, "schema": live.schema, "unit": live.unit})
                with attempt.open("x", encoding="utf-8") as marker:
                    marker.write(args.plan_sha256 + "\n")
                receipt: dict[str, Any] = {
                    "artifact_type": "DashboardPivotRatioDraftReceipt", "plan_sha256": args.plan_sha256,
                    "dashboard_id": s["dashboard_id"], "unit_id": s["unit_id"], "sandbox": args.sandbox,
                    "published": False, "backup": str(backup), "writes": [], "formulas": [],
                }
                try:
                    _mutate(page, live, artifacts, receipt)
                    receipt["ok"] = True
                except Exception as exc:
                    receipt.update(ok=False, error=str(exc))
                write_json(receipt, args.output)
                print(json.dumps({k: v for k, v in receipt.items() if k not in ("writes", "value_checks")}, ensure_ascii=False))
                return 0 if receipt["ok"] else 1
            finally:
                lock_path.unlink()
        finally:
            browser.close()
