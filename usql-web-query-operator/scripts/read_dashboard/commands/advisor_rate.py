"""Hash-bound Qingcheng adviser breakthrough rate, shared draft and publication.

This deliberately does not expand the generic component-local update_formula.
Only the registered Qingcheng conversion board, one existing shared percentage,
its complete reference set and the three reviewed physical helpers are writable.
"""
from __future__ import annotations

import copy
from decimal import Decimal
import json
from pathlib import Path

from _shared.browser import import_playwright, launch_context
from _shared.config import RUNTIME_DIR
from _shared.fs_utils import ensure_runtime, safe_artifact_dir
from usql_web_query.query_auth import verify_query_identity
from ..common import write_json
from ..dashboard_change import _core_api, canonical_sha256, publish_config_sha256
from ..dashboard_write_adapters import _formula_item, _formula_projection, _write_dashboard_schema, _write_formula, _write_unit_detail
from ..edit_profile import EDIT_API_ROOT, build_edit_url, fetch_edit_unit_detail
from ..filter_edit import fetch_edit_config, publish_dashboard
from ..pivot_rebind import project_unit_field_state
from ..profile import default_unit_value_payload, fetch_dashboard_config, parse_dashboard_html, post_json
from ..write_capabilities import capability_by_operation, load_capability_registry
from .conversion_ratio_draft import _expected_profile
from .pivot_ratio_draft import _config, _profile
from ..pivot_ratio_fields import require

OPERATION = "update_qingcheng_shared_advisor_rate"
ADAPTER = "read_dashboard.commands.advisor_rate.cmd_advisor_rate"
PLAN_TYPE = "QingchengAdvisorRatePlan"
RECEIPT_TYPE = "QingchengAdvisorRateApplyReceipt"
EXPRESSION = "if(sum(${advisor_negative_income_rows})>0,null,ifnull(1.0*count(DISTINCT ${advisor_positive_revenue_key})/nullif(count(DISTINCT ${advisor_identity_key}),0),0))"
HELPERS = [("advisor_negative_income_rows", 1), ("advisor_positive_revenue_key", 2), ("advisor_identity_key", 2)]
BOARD = "dashboard_3885764906392891392"
FORMULA = "customized_1043617514272440320"


def _hash(body: dict, key: str) -> str:
    return canonical_sha256({k: v for k, v in body.items() if k != key})


def validate_selection(s: dict) -> None:
    require(set(s) == {"domain", "dashboard_id", "dashboard_name", "owner", "model_id", "subject_id", "formula_id", "helpers", "targets", "period", "period_filter"}, "Exact selection keys are required.")
    require(s["domain"] == "qingcheng" and s["dashboard_id"] == BOARD and s["dashboard_name"] == "转化数据看板"
            and s["owner"] == "lvshuai01" and s["model_id"] == 2460 and s["subject_id"] == 216472 and s["formula_id"] == FORMULA,
            "Only the registered Qingcheng conversion dashboard and its existing rate are in scope.")
    require([(x["field_name"], x["org_param_type"]) for x in s["helpers"]] == HELPERS
            and len({x["field_id"] for x in s["helpers"]}) == 3
            and all(set(x) == {"field_name", "field_id", "org_param_type"} and str(x["field_id"]).isdigit() for x in s["helpers"]),
            "Helpers must bind exact physical IDs in expression first-occurrence order.")
    require(isinstance(s["targets"], list) and 1 <= len(s["targets"]) <= 12
            and len({x["unit_id"] for x in s["targets"]}) == len(s["targets"])
            and len({x["component_id"] for x in s["targets"]}) == len(s["targets"]), "Bind the full unique pivot reference set.")
    require(s["period"].endswith("期") and s["period"][:-1].isdigit()
            and set(s["period_filter"]) == {"field_id", "filter_id"}, "Bind an existing period filter and exact validation period.")


def definition(before: dict, s: dict) -> dict:
    after = copy.deepcopy(before)
    after["formula"] = EXPRESSION
    after["dependencyIndicators"] = [{"paramId": x["field_id"], "orgParamType": x["org_param_type"], "needBoundaryValue": False} for x in s["helpers"]]
    return after


def _published(page, s: dict, require_isolation: bool = True) -> dict:
    cfg = fetch_dashboard_config(page, s["dashboard_id"])
    require(cfg.get("dashboardId") == s["dashboard_id"] and cfg.get("dashboardName") == s["dashboard_name"], "Published identity mismatch.")
    units, formulas = {}, {}
    for t in s["targets"]:
        uid = t["unit_id"]
        d = post_json(page, f"{EDIT_API_ROOT}/value/unit/detail", {"id": uid, "dashboardId": s["dashboard_id"], "isConfig": False})["data"]
        require(d.get("unitId") == uid and d.get("unitType") == "u_pivot", "Published pivot identity mismatch.")
        units[uid] = project_unit_field_state(d)
        fields = [f for f in d["unitMeasureList"] if f.get("showName") == "破蛋率"]
        if not fields:
            fields = [f for f in d["unitMeasureList"] if "破蛋率" in str(f.get("displayName") or f.get("columnName") or "")]
        require(len(fields) == 1, "Published pivot must contain one identifiable rate column.")
        key = fields[0]["fieldId"]
        item = _formula_projection(_formula_item(page, key))
        if require_isolation:
            require(item["subjectId"] != s["subject_id"] and key != s["formula_id"], "Published and draft rate identities are not isolated.")
        formulas[key] = item
    return {"schema_sha256": canonical_sha256(parse_dashboard_html(cfg)), "units": units, "formulas": formulas}


def _live(page, s: dict, artifacts: Path) -> tuple[dict, dict, dict, dict]:
    validate_selection(s)
    _core_api()
    from text2sql_core.dashboard_domains import validate_dashboard_domain_registration
    resolved, issues = validate_dashboard_domain_registration(s["dashboard_id"], s["domain"])
    require(resolved.get("status") == "registered" and not issues, "Live domain registration is required.")
    schema = parse_dashboard_html(_config(page, s))
    raw, profile = _profile(page, s, artifacts)
    shared = [f for f in profile["formulas"] if f["formula_id"] == s["formula_id"]]
    require(len(shared) == 1 and set(shared[0]["component_ids"]) == {t["component_id"] for t in s["targets"]},
            "The complete shared formula reference set must match the reviewed pivots.")
    formulas = [x for x in profile["formulas"] if x["formula_id"] == s["formula_id"]]
    require(len(formulas) == 1 and formulas[0]["name"] == "破蛋率"
            and set(formulas[0]["component_ids"]) == {t["component_id"] for t in s["targets"]}, "Shared formula reference scope drifted.")
    tree = [t for t in raw["dataset_fields"] if t.get("subject_id") == s["subject_id"] and t.get("model_type") == 2]
    require(len(tree) == 1, "Exact model subject field tree is required.")
    for x in s["helpers"]:
        fields = [f for f in tree[0]["fields"] if str(f["key"]) == x["field_id"]]
        require(len(fields) == 1 and fields[0]["title"] == x["field_name"]
                and fields[0]["org_param_type"] == fields[0]["change_param_type"] == x["org_param_type"], "Helper field identity or type drifted.")
    units = {}
    for t in s["targets"]:
        component = [c for c in profile["components"] if c["component_id"] == t["component_id"]]
        require(len(component) == 1 and component[0]["unit_id"] == t["unit_id"] and component[0]["component_type"] == "u_pivot", "Selected pivot identity drifted.")
        d = fetch_edit_unit_detail(page, t["unit_id"], s["dashboard_id"], "draft")
        require(d["dashboardModel"] == {"applicationModelId": s["model_id"], "dashboardId": s["dashboard_id"], "subjectId": s["subject_id"], "modelType": 2}, "Pivot model identity drifted.")
        measures = [f for f in d["unitMeasureList"] if f["fieldId"] == s["formula_id"]]
        require(len(measures) == 1 and measures[0]["format"].get("numberType") == 2, "Existing rate percentage format must be retained.")
        require(any(f["filter_id"] == s["period_filter"]["filter_id"] and f["field_id"] == s["period_filter"]["field_id"] and t["component_id"] in f["target_component_ids"] for f in profile["public_filters"]), "Period validation filter does not target this pivot.")
        units[t["unit_id"]] = d
    before = _formula_projection(_formula_item(page, s["formula_id"]))
    require(before["subjectId"] == s["subject_id"] and before["columnName"] == "破蛋率", "Formula identity drifted.")
    state = {"profile_sha256": profile["profile_sha256"], "schema_sha256": canonical_sha256(schema), "formula": before,
             "units": {uid: project_unit_field_state(d) for uid, d in units.items()}, "published": _published(page, s)}
    return state, profile, schema, units


def _values(page, s: dict, published: bool = False) -> dict:
    result = {}
    for t in s["targets"]:
        uid = t["unit_id"]
        p = default_unit_value_payload(uid, 2000)
        p.update(isConfig=not published)
        if not published:
            p["versionId"] = "draft"
        p["publicFilterList"] = [dict(paramId=s["period_filter"]["field_id"], fieldId=s["period_filter"]["field_id"],
                                           filterUnitId=s["period_filter"]["filter_id"], filterValue=[s["period"]], condition="in", orgParamType=2, isSelectAll=0)]
        detail = (post_json(page, f"{EDIT_API_ROOT}/value/unit/detail", {"id": uid, "dashboardId": s["dashboard_id"], "isConfig": False})["data"]
                  if published else fetch_edit_unit_detail(page, uid, s["dashboard_id"], "draft"))
        p["filterList"] = [{"paramId": f["fieldId"], "fieldId": f["fieldId"], "filterUnitId": f["filterUnitId"],
                            "filterValue": f["format"]["filterValue"], "condition": f["format"].get("condition", "in"),
                            "orgParamType": f["format"]["orgParamType"], "isSelectAll": 0}
                           for f in detail.get("unitFilterList", []) if f.get("format", {}).get("filterValue")
                           and f["format"].get("isSelectAll") != 1]
        response = post_json(page, f"{EDIT_API_ROOT}/value/unit", p, timeout_ms=60000)
        value = response.get("data", {}).get(uid, {})
        require(value.get("unitId") == uid and value.get("hasMore") is not True, "Pivot value read failed or is incomplete.")
        rows = value.get("data") or []
        require(value.get("totalSize", len(rows)) == len(rows), "Pivot rows exceed bounded complete capture.")
        result[uid] = value
    return result


def verify_rates(values: dict, bindings: dict) -> dict:
    checks = {}
    for uid, v in values.items():
        key = bindings[uid]
        rows = list(v.get("data") or []) + [v.get("totalData") or {}]
        require(rows and all(key in row and row[key] is not None for row in rows), "Missing rate or negative-income guard tripped.")
        require(all(Decimal(0) <= Decimal(str(row[key])) <= Decimal(1) for row in rows), "Rate outside [0,1].")
        checks[uid] = {"rows": len(rows) - 1, "total_rate": str(rows[-1][key]), "task_id": v.get("totalTaskId")}
    return checks


def _formula_equal(page, expected: dict) -> None:
    require(_formula_projection(_formula_item(page, expected["columnKey"])) == expected, "Formula metadata or ordered dependencies differ.")


def _units_equal(page, s: dict, expected: dict) -> None:
    for uid, d in expected.items():
        require(project_unit_field_state(fetch_edit_unit_detail(page, uid, s["dashboard_id"], "draft")) == d, "Pivot configuration drifted.")


def mutate(page, plan: dict, profile: dict, schema: dict, units: dict, artifacts: Path, receipt: dict) -> None:
    s, baseline = plan["selection"], plan["baseline"]
    after = definition(baseline["formula"], s)
    touched = False
    try:
        _units_equal(page, s, baseline["units"])
        _formula_equal(page, baseline["formula"])
        _formula_equal(page, baseline["formula"])
        touched = True
        _write_formula(page, after, receipt["writes"])
        _formula_equal(page, after)
        for uid, d in units.items():
            _units_equal(page, s, {uid: baseline["units"][uid]})
            _write_unit_detail(page, s["dashboard_id"], d, receipt["writes"])
        values = _values(page, s)
        receipt["value_checks"] = verify_rates(values, {uid: s["formula_id"] for uid in units})
        write_json(values, artifacts / f"{plan['plan_sha256']}-draft-values.json")
        require(_published(page, s) == baseline["published"], "Published configuration changed during draft Apply.")
        _write_dashboard_schema(page, s["dashboard_id"], s["dashboard_name"], schema, receipt["writes"], baseline["schema_sha256"])
        _, post = _profile(page, s, artifacts)
        _expected_profile(profile, post, {"after": [after]})
        _formula_equal(page, after)
        _units_equal(page, s, baseline["units"])
        require(_published(page, s) == baseline["published"], "Published configuration changed before draft acceptance.")
        receipt.update(saved_draft_verified=True, post_profile_sha256=post["profile_sha256"], published_formulas_unchanged=True)
    finally:
        if touched and not receipt.get("saved_draft_verified"):
            current = _formula_projection(_formula_item(page, s["formula_id"]))
            require(current in (baseline["formula"], after), "Third formula state; recovery blocked.")
            _units_equal(page, s, baseline["units"])
            if current != baseline["formula"]:
                _write_formula(page, baseline["formula"], receipt["writes"])
            for d in units.values():
                _write_unit_detail(page, s["dashboard_id"], d, receipt["writes"])
            _write_dashboard_schema(page, s["dashboard_id"], s["dashboard_name"], schema, receipt["writes"], baseline["schema_sha256"])
            _, restored = _profile(page, s, artifacts)
            require(restored["profile_sha256"] == baseline["profile_sha256"], "Full draft recovery failed.")
            receipt["restored_profile_sha256"] = restored["profile_sha256"]


def _publish(page, args, plan: dict, applied: dict, artifacts: Path) -> dict:
    require(args.confirm_publish and applied.get("ok") is True and applied.get("saved_draft_verified") is True,
            "Exact successful draft receipt and explicit publication confirmation are required.")
    require(applied.get("receipt_sha256") == args.receipt_sha256 == _hash(applied, "receipt_sha256")
            and applied.get("plan_sha256") == plan["plan_sha256"] and applied.get("artifact_type") == RECEIPT_TYPE, "Apply receipt Hash or Plan binding differs.")
    cap = capability_by_operation(load_capability_registry(), "publish_dashboard")
    require(cap["write_policy"] == "separate_confirmation", "Publication capability is not registered.")
    s = plan["selection"]
    state, _, _, _ = _live(page, s, artifacts)
    require(state["profile_sha256"] == applied["post_profile_sha256"] and state["formula"] == definition(plan["baseline"]["formula"], s)
            and state["published"] == plan["baseline"]["published"], "Draft or published baseline drifted before publication.")
    cfg = fetch_edit_config(page, s["dashboard_id"])
    html_id = cfg.get("htmlId")
    cfg_hash = publish_config_sha256(cfg, html_id)
    _, immediate = _profile(page, s, artifacts)
    fresh = fetch_edit_config(page, s["dashboard_id"])
    require(immediate["profile_sha256"] == applied["post_profile_sha256"]
            and publish_config_sha256(fresh, html_id) == cfg_hash, "Immediate pre-publication profile or payload drifted.")
    marker = RUNTIME_DIR / "advisor-rate-publication-attempts" / f"{plan['plan_sha256']}.json"
    marker.parent.mkdir(parents=True, exist_ok=True)
    require(not marker.exists(), "This publication was already attempted; inspect its receipt instead of repeating it.")
    with marker.open("x", encoding="utf-8") as stream:
        json.dump({"plan_sha256": plan["plan_sha256"], "apply_receipt_sha256": applied["receipt_sha256"], "config_sha256": cfg_hash}, stream)
    write_json({"artifact_type": "QingchengAdvisorRatePublishReceipt", "plan_sha256": plan["plan_sha256"],
                "publish_status": "attempt_started", "fully_verified": False}, args.output)
    result = publish_dashboard(page, fresh, args.version_description, html_id)
    receipt = {"artifact_type": "QingchengAdvisorRatePublishReceipt", "plan_sha256": plan["plan_sha256"], "apply_receipt_sha256": applied["receipt_sha256"],
               "confirmed": True, "result": result, "publish_status": "publish_requested_unverified", "fully_verified": False}
    write_json(receipt, args.output)
    require(result.get("publish_status") == "success", "Publication acknowledgment failed; inspect receipt before further action.")
    return verify_publication(page, plan, receipt, artifacts)


def verify_publication(page, plan: dict, receipt: dict, artifacts: Path) -> dict:
    require(receipt.get("plan_sha256") == plan["plan_sha256"] and receipt.get("confirmed") is True
            and receipt.get("result", {}).get("publish_status") == "success", "An existing successful publication acknowledgment is required; verification never republishes.")
    s = plan["selection"]
    online = _published(page, s, require_isolation=False)
    require(online["schema_sha256"] == plan["baseline"]["schema_sha256"], "Published schema changed unexpectedly.")
    for item in online["formulas"].values():
        require(item["formula"] == EXPRESSION and [(str(x["paramId"]), x["orgParamType"]) for x in item["dependencyIndicators"]]
                == [(x["field_id"], x["org_param_type"]) for x in s["helpers"]], "Published rate formula or dependencies did not take effect.")
    bindings = {uid: next(f["field_id"] for f in u["groups"]["unitMeasureList"] if f["showName"] == "破蛋率") for uid, u in online["units"].items()}
    values = _values(page, s, True)
    receipt["value_checks"] = verify_rates(values, bindings)
    write_json(values, artifacts / f"{plan['plan_sha256']}-published-values.json")
    receipt.update(published_formula_readback=online, published_functionally_verified=True,
                   limitation="No published-version identifier API; exact published formulas, references and values independently read back.")
    return receipt


def cmd_advisor_rate(args) -> int:
    body = json.loads(args.input.read_text(encoding="utf-8"))
    s = body.get("selection", body)
    validate_selection(s)
    if args.mode != "plan":
        require(body.get("artifact_type") == PLAN_TYPE and body.get("plan_sha256") == args.plan_sha256 == _hash(body, "plan_sha256"), "Exact reviewed Plan Hash is required.")
        cap = capability_by_operation(load_capability_registry(), OPERATION)
        require(cap["maturity"] == "verified" and cap["write_policy"] == "allowlisted" and cap["adapter"] == ADAPTER, "Dedicated shared rate adapter is not allowlisted.")
        require(args.mode in {"publish", "verify"} or args.confirm_production_write, "Explicit production draft confirmation is required.")
    ensure_runtime([args.artifacts_dir, args.output.parent])
    artifacts = safe_artifact_dir(args.artifacts_dir)
    with import_playwright()() as pw:
        browser, context = launch_context(pw, args.state_path, args.headed, args.browser_channel, None)
        try:
            page = context.new_page()
            verify_query_identity(page, s["owner"])
            page.goto(build_edit_url(s["dashboard_id"]), wait_until="domcontentloaded", timeout=45000)
            if args.mode in {"publish", "verify"}:
                applied = json.loads(args.apply_receipt.read_text(encoding="utf-8"))
                if args.mode == "verify":
                    require(applied.get("receipt_sha256") == args.receipt_sha256 == _hash(applied, "receipt_sha256"), "Apply receipt Hash differs.")
                    receipt = verify_publication(page, body, json.loads(args.output.read_text(encoding="utf-8")), artifacts)
                else:
                    receipt = _publish(page, args, body, applied, artifacts)
                receipt["receipt_sha256"] = _hash(receipt, "receipt_sha256")
                write_json(receipt, args.output)
                print(json.dumps({k: v for k, v in receipt.items() if k not in {"published_formula_readback", "value_checks"}}, ensure_ascii=False))
                return 0
            state, profile, schema, units = _live(page, s, artifacts)
            plan = {"artifact_type": PLAN_TYPE, "selection": s, "baseline": state, "expression": EXPRESSION}
            plan["plan_sha256"] = _hash(plan, "plan_sha256")
            if args.mode == "plan":
                require(state["formula"]["formula"] == "ifnull(sum(${podan})/sum(${v_lead}),0)", "Original rate baseline no longer matches the reviewed migration.")
                write_json(plan, args.output)
                print(json.dumps({"ok": True, "writes": 0, "plan_sha256": plan["plan_sha256"]}))
                return 0
            require(plan == body, "Live production state differs from the reviewed Plan.")
            lock_dir = RUNTIME_DIR / "draft-rebind-locks"
            lock_dir.mkdir(parents=True, exist_ok=True)
            lock_path = lock_dir / f"{s['dashboard_id']}.lock"
            with lock_path.open("x", encoding="utf-8") as lock:
                lock.write(args.plan_sha256)
            try:
                backup = artifacts / "advisor-rate" / s["dashboard_id"] / f"{args.plan_sha256}-baseline.json"
                require(not backup.exists(), "This Plan has an earlier attempt; inspect its backup and receipt.")
                write_json({"plan": plan, "schema": schema, "units": units}, backup)
                receipt = {"artifact_type": RECEIPT_TYPE, "plan_sha256": args.plan_sha256, "published": False, "writes": [], "backup": str(backup)}
                try:
                    mutate(page, plan, profile, schema, units, artifacts, receipt)
                    receipt["ok"] = receipt.get("saved_draft_verified") is True
                except Exception as exc:
                    receipt.update(ok=False, error=str(exc))
                receipt["receipt_sha256"] = _hash(receipt, "receipt_sha256")
                write_json(receipt, args.output)
                print(json.dumps({k: v for k, v in receipt.items() if k not in {"writes", "value_checks"}}, ensure_ascii=False))
                return 0 if receipt["ok"] else 1
            finally:
                lock_path.unlink()
        finally:
            browser.close()
