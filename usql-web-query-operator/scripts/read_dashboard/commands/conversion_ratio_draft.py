"""Update denominators of existing conversion ratios in an isolated dashboard draft."""

from __future__ import annotations

from decimal import Decimal
import json
from pathlib import Path
import re
from typing import Any

from _shared.browser import import_playwright, launch_context
from _shared.config import RUNTIME_DIR
from _shared.fs_utils import ensure_runtime, safe_artifact_dir
from usql_web_query.query_auth import verify_query_identity

from ..common import write_json
from ..constants import UNIT_VALUE_API
from ..dashboard_change import _core_api, canonical_sha256
from ..dashboard_write_adapters import _formula_item, _formula_projection, _write_dashboard_schema, _write_formula
from ..edit_profile import EDIT_API_ROOT, build_edit_url, fetch_edit_unit_detail
from ..pivot_ratio_fields import expected_rate, formula_definition, formula_matches, projection, require
from ..profile import default_unit_value_payload, extract_component_units, fetch_dashboard_config, fetch_unit_detail, parse_dashboard_html, post_json
from ..write_capabilities import capability_by_operation, load_capability_registry
from .pivot_ratio_draft import _config, _profile, _read, _validate_live_filters


OPERATION = "change_draft_conversion_ratio_denominators"
PLAN_TYPE = "DashboardDraftConversionDenominatorPlan"
ADAPTER = "read_dashboard.commands.conversion_ratio_draft.cmd_conversion_ratio_draft"


def _write_backup(artifacts: Path, dashboard_id: str, plan_sha256: str, payload: dict) -> Path:
    path = artifacts / "conversion-ratio" / dashboard_id / f"{plan_sha256}-baseline.json"
    require(not path.exists(), "An immutable baseline backup already exists for this plan; inspect it before continuing.")
    write_json(payload, path)
    return path


def _identifier(value: Any, pattern: str) -> bool:
    return isinstance(value, str) and re.fullmatch(pattern, value) is not None


def _metric_key(metric: dict) -> str:
    require(isinstance(metric, dict) and set(metric) == {"field_id", "field_name"}
            and _identifier(metric["field_id"], r"\d+") and _identifier(metric["field_name"], r"[a-zA-Z_][a-zA-Z0-9_]*"),
            "An exact physical metric ID and identifier name are required.")
    return metric["field_id"]


def _validate(s: dict, checks: list, sandbox: bool) -> None:
    fields = {"domain", "dashboard_id", "dashboard_name", "owner", "model_id", "subject_id",
              "targets", "all_leads", "ratios"}
    require(set(s) == fields and s["domain"] == "market_consultant", "An exact market consultant selection is required.")
    require(_identifier(s["dashboard_id"], r"dashboard_\d+") and _identifier(s["owner"], r"[a-zA-Z0-9._-]+")
            and isinstance(s["dashboard_name"], str) and s["dashboard_name"]
            and all(type(s[k]) is int and s[k] > 0 for k in ("model_id", "subject_id")), "Invalid dashboard or subject identity.")
    if sandbox:
        require("测试沙箱" in s["dashboard_name"], "The exact confirmed sandbox name is required.")
    targets = s["targets"]
    require(isinstance(targets, list) and 1 <= len(targets) <= 4, "Bind one to four exact draft pivots.")
    for target in targets:
        require(isinstance(target, dict) and set(target) == {"component_id", "unit_id"}
                and _identifier(target["component_id"], r"node_[a-zA-Z0-9]+")
                and _identifier(target["unit_id"], r"unit_\d+"), "Invalid target component or pivot.")
    for key in ("component_id", "unit_id"):
        require(len({t[key] for t in targets}) == len(targets), "Duplicate pivot identity.")
    ratios = s["ratios"]
    require(isinstance(ratios, list) and 1 <= len(ratios) <= 3, "Bind one to three exact conversion formulas.")
    metric_ids = [_metric_key(s["all_leads"])]
    formula_ids = []
    formula_names = []
    for ratio in ratios:
        require(isinstance(ratio, dict) and set(ratio) == {
            "name", "formula_id", "share_name", "share_id", "converted", "qualified",
        }, "Bind each conversion formula and its corresponding share formula.")
        for field in ("formula_id", "share_id"):
            require(_identifier(ratio[field], r"customized_\d+"), "An existing calculated field ID is required.")
            formula_ids.append(ratio[field])
        for field in ("name", "share_name"):
            require(_identifier(ratio[field], r"[^<>\x00-\x1f]{1,40}"), "Invalid formula name.")
            formula_names.append(ratio[field])
        metric_ids.extend(_metric_key(ratio[k]) for k in ("converted", "qualified"))
    require(len(metric_ids) == len(set(metric_ids)) and len(formula_ids) == len(set(formula_ids))
            and len(formula_names) == len(set(formula_names)), "Metric and formula references must be unique.")
    require(isinstance(checks, list) and len(targets) <= len(checks) <= 160, "Provide bounded checks for all target units.")
    seen = set()
    for check in checks:
        require(isinstance(check, dict) and set(check) == {"unit_id", "label", "filters", "row", "all_leads", "counts"}
                and isinstance(check["label"], str) and check["label"], "Invalid value check.")
        require(isinstance(check["row"], list) and all(isinstance(x, str) for x in check["row"]), "A row key must be a list of exact labels.")
        require(isinstance(check["filters"], list) and len(check["filters"]) <= 2
                and all(isinstance(item, list) and len(item) == 3 and _identifier(item[0], r"\d+")
                        and _identifier(item[1], r"public_filter_\d+") and isinstance(item[2], str)
                        and item[2] for item in check["filters"]), "Invalid linked filter check.")
        require(type(check["all_leads"]) is int and check["all_leads"] >= 0 and isinstance(check["counts"], list)
                and len(check["counts"]) == len(ratios), "One set of exact counts per ratio is required.")
        for counts in check["counts"]:
            require(isinstance(counts, list) and len(counts) == 2 and all(type(x) is int for x in counts)
                    and 0 <= counts[0] <= counts[1] <= check["all_leads"], "Require converted <= qualified <= all leads.")
        seen.add(check["unit_id"])
    require(seen == {t["unit_id"] for t in targets}, "Each selected unit must have its own checks.")


def _definition(s: dict, ratio: dict, mode: str) -> dict:
    """Construct only the resolved physical-field sum ratios. Preserve the formula key."""
    share = mode == "share"
    result = formula_definition(
        {"name": ratio["share_name" if share else "name"], "numerator": ratio["qualified" if share else "converted"]},
        ratio["qualified"] if mode == "after" else s["all_leads"], s["subject_id"],
    )
    result["columnKey"] = ratio["share_id" if share else "formula_id"]
    return result


def _verified_formula(page, definition: dict) -> dict:
    field_id = definition["columnKey"]
    actual = _formula_item(page, field_id)
    require(formula_matches(actual, definition, field_id), f"Formula or dependencies differ for {definition['columnName']}.")
    return _formula_projection(actual)


def _catalog(raw: dict, s: dict) -> dict[str, dict]:
    trees = [t for t in raw["dataset_fields"] if t.get("subject_id") == s["subject_id"] and t.get("model_type") == 2]
    require(len(trees) == 1 and trees[0].get("fields"), "The live subject field tree is missing or ambiguous.")
    fields = trees[0]["fields"]
    index = {str(f["key"]): f for f in fields}
    require(len(index) == len(fields), "The subject contains ambiguous field IDs.")
    reviewer = [s["all_leads"], *(r[k] for r in s["ratios"] for k in ("converted", "qualified"))]
    for metric in reviewer:
        field = index.get(metric["field_id"]) or {}
        require(field.get("title") == metric["field_name"] and field.get("org_param_type") == field.get("change_param_type") == 1
                and field.get("data_type") == 1 and field.get("is_choice") is True,
                f"Not a selectable physical metric in the selected subject: {metric['field_name']}.")
    for ratio in s["ratios"]:
        for key, label in (("formula_id", "name"), ("share_id", "share_name")):
            field = index.get(ratio[key]) or {}
            require(field.get("title") == ratio[label] and field.get("org_param_type") == 4,
                    f"Calculated field is missing from the selected subject: {ratio[label]}.")
    used_ids = {m["field_id"] for m in reviewer} | {r[k] for r in s["ratios"] for k in ("formula_id", "share_id")}
    return {key: index[key] for key in sorted(used_ids)}


def _scoped_units(page, profile: dict, s: dict, checks: list) -> dict:
    refs = {t["component_id"] for t in s["targets"]}
    components = {c["component_id"]: c for c in profile["components"]}
    formulas = {f["formula_id"]: f for f in profile["formulas"]}
    verified_ids = {r[k] for r in s["ratios"] for k in ("formula_id", "share_id")}
    for field_id in verified_ids:
        formula = formulas.get(field_id) or {}
        require(set(formula.get("component_ids", [])) == refs, "A shared formula has dependencies outside the reviewed pivots.")
    model = {"applicationModelId": s["model_id"], "dashboardId": s["dashboard_id"],
             "subjectId": s["subject_id"], "modelType": 2}
    units = {}
    for t in s["targets"]:
        component = components.get(t["component_id"]) or {}
        uid = t["unit_id"]
        require(component.get("unit_id") == uid and component.get("component_type") == "u_pivot",
                "A reviewed component does not resolve to its existing pivot.")
        current = fetch_edit_unit_detail(page, uid, s["dashboard_id"], "draft")
        require(current.get("unitId") == uid and current.get("unitType") == "u_pivot" and current.get("dashboardModel") == model,
                "All draft pivots must use the exact same dashboard-scoped model and subject.")
        fields = {f["fieldId"]: f for f in current["unitMeasureList"]}
        for field in verified_ids:
            require(field in fields and fields[field]["format"].get("numberType") == 2
                    and fields[field]["format"].get("orgParamType") == 4, "A reviewed formula column is absent or no longer a percentage.")
        _validate_live_filters(profile, t, [c for c in checks if c["unit_id"] == uid])
        units[uid] = current
    return units


def _field_keys(value: Any) -> set[str]:
    if isinstance(value, list):
        return {key for item in value for key in _field_keys(item)}
    if isinstance(value, dict):
        direct = {v for k, v in value.items() if k in {"paramId", "fieldId", "columnKey"} and isinstance(v, str)}
        return direct.union(*(_field_keys(v) for v in value.values() if isinstance(v, (list, dict))))
    return set()


def _verify_published_bindings(page, s: dict, published: dict) -> None:
    """Recheck that the published pivots serve their original calculated fields."""
    by_name = {row["columnName"]: row for row in published["formulas"].values()}
    mutable = {r["formula_id"] for r in s["ratios"]}
    labels = {r[k] for r in s["ratios"] for k in ("name", "share_name")}
    require(labels.issubset(by_name), "The published counterpart formulas were not all identified.")
    for ratio in s["ratios"]:
        for role, name in (("before", ratio["name"]), ("share", ratio["share_name"])):
            column = by_name[name]
            expected = _definition(s, ratio, role)
            expected["subjectId"] = column["subjectId"]
            require(formula_matches(column | {"indicatorType": "CUSTOMIZED_MEASURE"}, expected, column["columnKey"]),
                    f"The published formula does not match the original denominator for {name}.")
    for target in s["targets"]:
        uid = target["unit_id"]
        payload = default_unit_value_payload(uid, 1)
        view = (post_json(page, UNIT_VALUE_API, payload, timeout_ms=60_000).get("data") or {}).get(uid) or {}
        field_ids = _field_keys(view.get("title"))
        require(view.get("unitId") == uid and not mutable.intersection(field_ids)
                and {by_name[name]["columnKey"] for name in labels}.issubset(field_ids),
                f"The published pivot no longer serves the original counterpart metrics: {uid}.")


def _published(page, s: dict, *, baseline: dict | None = None) -> dict:
    dashboard = fetch_dashboard_config(page, s["dashboard_id"])
    require(dashboard.get("dashboardId") == s["dashboard_id"] and dashboard.get("dashboardName") == s["dashboard_name"],
            "The published dashboard identity must be verified.")
    schema = parse_dashboard_html(dashboard)
    digest = canonical_sha256(schema)
    require(schema and (baseline is None or digest == baseline["schema_sha256"]), "The published schema changed.")
    targets = {t["unit_id"] for t in s["targets"]}
    mutable = {r["formula_id"] for r in s["ratios"]}
    names = {r[k] for r in s["ratios"] for k in ("name", "share_name")}
    exposures = {}
    details = {}
    published_formulas = {}
    model_units = []
    for component in extract_component_units(schema):
        uid = component["unit_id"]
        if component.get("component_type") in {"iframe", "u_text"} or not uid.startswith("unit_"):
            continue
        detail = fetch_unit_detail(page, uid)
        require(detail.get("unitId") == uid, "Could not prove the published unit identity.")
        if uid not in targets and str(detail.get("modelId") or (detail.get("dashboardModel") or {}).get("applicationModelId")) != str(s["model_id"]):
            continue
        require((detail.get("dashboardModel") or {}).get("subjectId") != s["subject_id"],
                "A published unit uses the same subject as the draft.")
        model_units.append(uid)
        details[uid] = canonical_sha256(projection(detail))
        if baseline is None:
            payload = default_unit_value_payload(uid, 1)
            result = post_json(page, UNIT_VALUE_API, payload, timeout_ms=60_000).get("data") or {}
            value = result.get(uid) or {}
            require(value.get("unitId") == uid and any(key in value for key in ("title", "titleList", "displayDataList", "series", "data")),
                    f"Unable to prove the published model's field scope for {uid}.")
            field_ids = _field_keys(value)
            require(field_ids, f"No identifiable published metric or dimension for {uid}.")
            require(not mutable.intersection(field_ids | _field_keys(detail)), "A changed draft formula is referenced by the published board.")
            exposures[uid] = sorted(field_ids)
            if uid in targets:
                for column in value.get("title") or []:
                    if column.get("name") in names:
                        field_id = str(column.get("paramId") or column.get("fieldId"))
                        if _identifier(field_id, r"customized_\d+") and field_id not in published_formulas:
                            formula = _formula_projection(_formula_item(page, field_id))
                            require(formula["subjectId"] != s["subject_id"], "A published formula inhabits the draft subject.")
                            published_formulas[field_id] = formula
    require(targets.issubset(model_units), "Published pivot identity is missing.")
    if baseline is None:
        return {"schema_sha256": digest, "unit_sha256": details, "field_ids": exposures, "formulas": published_formulas}
    require(baseline["unit_sha256"] == details, "The published unit configuration changed.")
    require(all(_formula_projection(_formula_item(page, key)) == formula for key, formula in baseline["formulas"].items()),
            "A published counterpart formula changed.")
    return baseline


def _live(page, s: dict, checks: list, artifacts: Path, sandbox: bool) -> tuple[dict, dict, dict, dict]:
    schema = parse_dashboard_html(_config(page, s))
    raw, profile = _profile(page, s, artifacts)
    catalog = _catalog(raw, s)
    units = _scoped_units(page, profile, s, checks)
    before = [_verified_formula(page, _definition(s, r, "before")) for r in s["ratios"]]
    after = [_definition(s, r, "after") for r in s["ratios"]]
    shares = [_verified_formula(page, _definition(s, r, "share")) for r in s["ratios"]]
    plan = {
        "artifact_type": PLAN_TYPE, "schema_version": "1.0.0", "sandbox": sandbox,
        "selection": s, "checks": checks, "profile_sha256": profile["profile_sha256"],
        "schema_sha256": canonical_sha256(schema), "fields_sha256": canonical_sha256(catalog),
        "units": {uid: canonical_sha256(projection(unit)) for uid, unit in units.items()},
        "before": before, "after": after, "shares": shares,
        "published": None if sandbox else _published(page, s),
    }
    plan["plan_sha256"] = canonical_sha256(plan)
    return plan, profile, units, schema


def _expect_draft(page, plan: dict) -> None:
    s = plan["selection"]
    require(canonical_sha256(parse_dashboard_html(_config(page, s))) == plan["schema_sha256"],
            "The draft schema changed before the formula write.")
    for uid, expected in plan["units"].items():
        unit = fetch_edit_unit_detail(page, uid, s["dashboard_id"], "draft")
        require(canonical_sha256(projection(unit)) == expected, f"Draft pivot {uid} changed before the formula write.")


def _check_result(raw: dict, s: dict, unit: dict, check: dict, sandbox: bool) -> dict:
    uid = check["unit_id"]
    require(raw.get("unitId") == uid and raw.get("totalTaskId"), f"Value response failed for {check['label']}.")
    ids = [f["fieldId"] for f in unit["unitDimensionList"]]
    measures = [f["fieldId"] for f in unit["unitMeasureList"]]
    titles = [str(f.get("paramId") or f.get("fieldId")) for f in raw["title"]]
    require([x for x in titles if x in measures] == measures, "Pivot column order changed.")
    if check["row"]:
        require(raw.get("hasMore") is False, f"A row-level value check cannot use a truncated page: {check['label']}.")
        available = [r for r in raw.get("data", []) if [r.get(fid) for fid in ids] == check["row"]]
        require(len(available) == 1, f"Missing or ambiguous pivot row for {check['label']}.")
        result = available[0]
    else:
        result = raw.get("totalData") or {}
    overall = check["all_leads"]
    overall_id = s["all_leads"]["field_id"]
    require((sandbox and overall_id not in titles) or Decimal(str(result[overall_id])) == overall,
            f"The eligible count or sync snapshot changed for {check['label']}.")
    measured = []
    for ratio, (converted, qualified) in zip(s["ratios"], check["counts"], strict=True):
        actual = Decimal(str(result[ratio["formula_id"]]))
        share = Decimal(str(result[ratio["share_id"]]))
        require(actual.is_finite() and abs(actual - expected_rate(converted, qualified)) <= Decimal("0.00000001")
                and abs(actual * qualified - converted) <= Decimal("0.00001"),
                f"Conditional conversion rate mismatch for {check['label']} / {ratio['name']}.")
        require(share.is_finite() and abs(share - expected_rate(qualified, overall)) <= Decimal("0.00000001")
                and abs(share * overall - qualified) <= Decimal("0.00001"),
                f"Unchanged share mismatch for {check['label']} / {ratio['share_name']}.")
        measured.append({"name": ratio["name"], "converted": converted, "qualified": qualified,
                         "conversion_rate": str(actual), "share": str(share)})
    return {"unit_id": uid, "label": check["label"], "filters": check["filters"], "row": check["row"],
            "all_leads": overall, "ratios": measured, "task_id": raw["totalTaskId"]}


def _verify_values(page, plan: dict, units: dict) -> list[dict]:
    responses = {}
    results = []
    for check in plan["checks"]:
        uid = check["unit_id"]
        key = (uid, tuple(tuple(x) for x in check["filters"]))
        if key not in responses:
            payload = default_unit_value_payload(uid, 100)
            payload.update(isConfig=True, versionId="draft")
            payload["publicFilterList"] = [
                dict(paramId=field, fieldId=field, filterUnitId=leaf, filterValue=[value], condition="in", orgParamType=2, isSelectAll=0)
                for field, leaf, value in check["filters"]
            ]
            values = post_json(page, f"{EDIT_API_ROOT}/value/unit", payload, timeout_ms=60_000)["data"]
            responses[key] = values.get(uid) or {}
        results.append(_check_result(responses[key], plan["selection"], units[uid], check, plan["sandbox"]))
    return results


def _expected_profile(before: dict, after: dict, plan: dict) -> None:
    keys = ("components", "data_units", "layout", "public_filters", "component_filters", "datasets", "theme")
    require(all(before[k] == after[k] for k in keys), "Unexpected configuration changed outside the formulas.")
    expected = {d["columnKey"]: d for d in plan["after"]}
    old = {p["formula_id"]: p for p in before["formulas"]}
    new = {p["formula_id"]: p for p in after["formulas"]}
    require(old.keys() == new.keys(), "The draft formula identities changed.")
    for key, original in old.items():
        current = new[key]
        if key in expected:
            require({k: v for k, v in original.items() if k not in ("expression", "dependencies")}
                    == {k: v for k, v in current.items() if k not in ("expression", "dependencies")}
                    and current["expression"] == expected[key]["formula"]
                    and {x["paramId"] for x in current["dependencies"]} == {x["paramId"] for x in expected[key]["dependencyIndicators"]},
                    "A modified formula was rebound or lost its exact dependencies.")
        else:
            require(original == current, "Another formula changed.")


def _restore(page, plan: dict, touched: list[tuple], schema: dict, artifacts: Path, receipt: dict) -> None:
    s = plan["selection"]
    _expect_draft(page, plan)
    for before, after in reversed(touched):
        key = before["columnKey"]
        current = _formula_item(page, key)
        if not formula_matches(current, before, key):
            require(formula_matches(current, after, key), "A formula drifted. Automatic recovery stopped.")
            _verified_formula(page, after)
            _write_formula(page, before, receipt["writes"])
            _verified_formula(page, before)
    _write_dashboard_schema(page, s["dashboard_id"], s["dashboard_name"], schema, receipt["writes"], plan["schema_sha256"])
    _, readback = _profile(page, s, artifacts)
    require(readback["profile_sha256"] == plan["profile_sha256"], "Recovery did not return the full draft profile to its baseline.")
    receipt["restored_profile_sha256"] = readback["profile_sha256"]


def _mutate(page, plan: dict, profile: dict, units: dict, schema: dict, artifacts: Path, receipt: dict) -> None:
    s = plan["selection"]
    touched = []
    try:
        for before, after in zip(plan["before"], plan["after"], strict=True):
            _expect_draft(page, plan)
            _verified_formula(page, before)
            _verified_formula(page, before)
            touched.append((before, after))
            _write_formula(page, after, receipt["writes"])
            _verified_formula(page, after)
        for unchanged in plan["shares"]:
            _verified_formula(page, unchanged)
        receipt["value_checks"] = _verify_values(page, plan, units)
        _expect_draft(page, plan)
        if not plan["sandbox"]:
            _published(page, s, baseline=plan["published"])
            _verify_published_bindings(page, s, plan["published"])
        _write_dashboard_schema(page, s["dashboard_id"], s["dashboard_name"], schema, receipt["writes"], plan["schema_sha256"])
        _expect_draft(page, plan)
        raw, post = _profile(page, s, artifacts)
        _catalog(raw, s)
        _expected_profile(profile, post, plan)
        for formula in plan["after"] + plan["shares"]:
            _verified_formula(page, formula)
        if not plan["sandbox"]:
            published = _published(page, s, baseline=plan["published"])
            _verify_published_bindings(page, s, published)
            receipt["published_schema_sha256"] = published["schema_sha256"]
            receipt["published_formulas_unchanged"] = True
        receipt["post_profile_sha256"] = post["profile_sha256"]
        receipt["saved_draft_verified"] = True
    finally:
        if touched and (plan["sandbox"] or not receipt.get("saved_draft_verified")):
            _restore(page, plan, touched, schema, artifacts, receipt)


def cmd_conversion_ratio_draft(args) -> int:
    body = _read(args.input)
    s, checks = body.get("selection") or {}, body.get("checks")
    _validate(s, checks, args.sandbox)
    require(s["domain"] == args.domain, "Domain mismatch.")
    if not args.sandbox:
        _core_api()
        from text2sql_core.dashboard_domains import validate_dashboard_domain_registration

        resolution, issues = validate_dashboard_domain_registration(s["dashboard_id"], args.domain)
        require(resolution.get("status") == "registered" and not issues, "The dashboard domain registry binding must be verified.")
    if args.mode == "apply":
        digest = canonical_sha256({k: v for k, v in body.items() if k != "plan_sha256"})
        require(body.get("artifact_type") == PLAN_TYPE and body.get("sandbox") is args.sandbox
                and digest == body.get("plan_sha256") == args.plan_sha256, "The reviewed Plan and hash are required.")
        if args.sandbox:
            require(args.confirm_sandbox_write and args.headed and not args.confirm_production_write,
                    "Sandbox verification needs explicit confirmation and a visible browser.")
        else:
            require(args.confirm_production_write and not args.confirm_sandbox_write, "The exact production-draft confirmation is required.")
            capability = capability_by_operation(load_capability_registry(), OPERATION)
            require(capability.get("maturity") == "verified" and capability.get("write_policy") == "allowlisted"
                    and capability.get("adapter") == ADAPTER, "This production adapter is not allowlisted.")
    require(args.state_path.is_file(), "An isolated authenticated owner session is required.")
    ensure_runtime([args.artifacts_dir, args.output.parent])
    artifacts = safe_artifact_dir(args.artifacts_dir)
    with import_playwright()() as pw:
        browser, context = launch_context(pw, args.state_path, args.headed, args.browser_channel, None)
        try:
            page = context.new_page()
            verify_query_identity(page, s["owner"])
            page.goto(build_edit_url(s["dashboard_id"]), wait_until="domcontentloaded", timeout=45_000)
            plan, profile, units, schema = _live(page, s, checks, artifacts, args.sandbox)
            if args.mode == "plan":
                write_json(plan, args.output)
                print(json.dumps({"ok": True, "plan_sha256": plan["plan_sha256"], "writes": 0}))
                return 0
            require(plan == body, "The live draft or published state no longer matches the reviewed Plan.")
            lock_dir = RUNTIME_DIR / "draft-rebind-locks"
            lock_dir.mkdir(parents=True, exist_ok=True)
            lock_path = lock_dir / f"{s['dashboard_id']}.lock"
            with lock_path.open("x", encoding="utf-8") as lock:
                lock.write(args.plan_sha256 + "\n")
            try:
                marker = RUNTIME_DIR / "conversion-ratio-attempts" / s["dashboard_id"] / f"{args.plan_sha256}.attempt"
                marker.parent.mkdir(parents=True, exist_ok=True)
                require(not marker.exists(), "This Plan has an earlier attempt. Read the outcome before taking further action.")
                backup = _write_backup(artifacts, s["dashboard_id"], args.plan_sha256,
                                       {"plan": plan, "schema": schema, "units": units})
                with marker.open("x", encoding="utf-8") as handle:
                    handle.write(args.plan_sha256 + "\n")
                receipt: dict[str, Any] = {"artifact_type": "DashboardDraftConversionDenominatorReceipt",
                                           "dashboard_id": s["dashboard_id"], "sandbox": args.sandbox,
                                           "published": False, "plan_sha256": args.plan_sha256, "backup": str(backup), "writes": []}
                try:
                    _mutate(page, plan, profile, units, schema, artifacts, receipt)
                    receipt["ok"] = receipt.get("saved_draft_verified") is True
                except Exception as exc:
                    receipt.update({"ok": False, "error": str(exc)})
                write_json(receipt, args.output)
                print(json.dumps({k: v for k, v in receipt.items() if k not in ("writes", "value_checks")}, ensure_ascii=False))
                return 0 if receipt["ok"] else 1
            finally:
                lock_path.unlink()
        finally:
            browser.close()
