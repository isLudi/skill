"""Plan, verify and apply a bounded Taitan period/date rebind."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any
from uuid import uuid4

from _shared.auth import is_login_page
from _shared.browser import import_playwright, launch_context
from _shared.config import DEFAULT_ARTIFACTS, RUNTIME_DIR
from _shared.env import load_env_file
from _shared.fs_utils import ensure_runtime, safe_artifact_dir

from ..common import write_json
from ..dashboard_change import _core_api, canonical_sha256, require_complete_profile
from ..dashboard_write_adapters import _write_dashboard_schema, _write_filter_detail, _write_unit_detail
from ..draft_dimension_rebind import OPERATION, checked_field, rebind_chart, rebind_filter, require, stable_unit
from ..edit_profile import EDIT_API_ROOT, build_edit_url, extract_component_units, fetch_edit_dashboard_config, fetch_edit_unit_detail, open_edit_page, profile_edit_dashboard
from ..profile import default_unit_value_payload, fetch_dashboard_config, parse_dashboard_html, post_json, summarize_unit_value
from ..write_capabilities import capability_by_operation, load_capability_registry


PLAN_TYPE = "DashboardPeriodDateRebindPlan"


def _id(value: Any, prefix: str) -> bool:
    return isinstance(value, str) and re.fullmatch(prefix + r"_\d+", value) is not None


def validate_selection(s: dict, domain: str) -> None:
    require(s.get("domain") == domain == "market_consultant", "The registered market consultant domain is required.")
    require(_id(s.get("dashboard_id"), "dashboard") and _id(s.get("relation_id"), "public_filter_relation")
            and _id(s.get("filter_id"), "public_filter"), "Stable dashboard, relation and filter IDs are required.")
    require(isinstance(s.get("model_id"), int) and isinstance(s.get("subject_id"), int), "Exact numeric model and subject IDs are required.")
    charts = s.get("charts") or []
    require(1 <= len(charts) <= 4 and len({c.get("unit_id") for c in charts}) == len(charts), "Provide one to four unique target charts.")
    for chart in charts:
        require(_id(chart.get("unit_id"), "unit") and chart.get("unit_type") in {"u_pivot", "u_line"}
                and str(chart.get("from_field_id", "")).isdigit(), "Each chart needs a stable unit, type and existing row dimension.")
    require(any(chart["unit_type"] == "u_pivot" for chart in charts), "A verified pivot is required.")
    for key in ("period_from_field_id", "period_to_field_id", "date_to_field_id"):
        require(str(s.get(key, "")).isdigit(), f"Expected a physical field ID in {key}.")
    require(s["period_from_field_id"] != s["period_to_field_id"], "The new period field must differ from the old one.")
    for key in ("dashboard_name", "owner", "period_label", "date_label"):
        require(isinstance(s.get(key), str) and bool(s[key].strip()) and not re.search(r"[<>\x00-\x1f]", s[key]), f"Expected a plain-text {key}.")
    values = s.get("verification_periods") or []
    require(1 <= len(values) <= 3 and all(re.fullmatch(r"\d{8}期", value) for value in values), "Provide one to three explicit period values for readback.")


@dataclass
class LiveDraft:
    schema: dict
    units: dict
    projected: dict
    plan: dict


def _attempt_marker_path(dashboard_id: str, plan_sha256: str) -> Path:
    return RUNTIME_DIR / "period-date-rebind-attempts" / dashboard_id / f"{plan_sha256}.attempt"


def _backup_path(artifacts: Path, dashboard_id: str, plan_sha256: str) -> Path:
    return artifacts / "period-date-rebind" / dashboard_id / plan_sha256 / f"baseline-{uuid4().hex}.json"


def _config(page, s: dict) -> dict:
    config = fetch_edit_dashboard_config(page, s["dashboard_id"], "draft")
    require(config.get("dashboardId") == s["dashboard_id"] and config.get("dashboardName") == s["dashboard_name"]
            and config.get("haveEditPermission") is True and s["owner"] in (config.get("ownerList") or []),
            "Dashboard identity, owner or edit permission failed readback.")
    return config


def _profile(page, s, artifacts, *, include_fields):
    raw = profile_edit_dashboard(page, s["dashboard_id"], None, build_edit_url(s["dashboard_id"]),
                                 "draft", artifacts, False, include_fields, s["domain"])
    return raw, require_complete_profile(raw)


def _untouched_profile_sha256(profile: dict, s: dict) -> str:
    chart_ids = {chart["unit_id"] for chart in s["charts"]}
    projection = {key: profile[key] for key in ("layout", "theme", "formulas", "component_filters")}
    projection["components"] = [c for c in profile["components"] if c.get("unit_id") not in chart_ids | {s["relation_id"]}]
    projection["data_units"] = [u for u in profile["data_units"] if u.get("unit_id") not in chart_ids]
    projection["public_filters"] = [f for f in profile["public_filters"] if f.get("filter_id") != s["filter_id"]]
    return canonical_sha256(projection)


def _live(page, s: dict, artifacts: Path, sandbox: bool) -> LiveDraft:
    config = _config(page, s)
    schema = parse_dashboard_html(config)
    rich, profile = _profile(page, s, artifacts, include_fields=True)
    matches = [item for item in rich["dataset_fields"] if item.get("subject_id") == s["subject_id"] and item.get("model_type") == 2]
    require(len(matches) == 1 and not matches[0].get("error"), "The verified subject field tree is required.")
    fields = {item["key"]: item for item in matches[0]["fields"]}
    period = checked_field(fields, s["period_to_field_id"], 2)
    date = checked_field(fields, s["date_to_field_id"], 3)
    targets = extract_component_units(schema)
    units = {}
    projected = {}
    for chart in s["charts"]:
        unit_id = chart["unit_id"]
        require(sum(node.get("unit_id") == unit_id and node.get("component_type") == chart["unit_type"] for node in targets) == 1,
                f"Chart {unit_id} does not resolve to one matching schema component.")
        units[unit_id] = fetch_edit_unit_detail(page, unit_id, s["dashboard_id"], "draft")
        projected[unit_id] = rebind_chart(units[unit_id], chart, dashboard_id=s["dashboard_id"], model_id=s["model_id"],
                                          subject_id=s["subject_id"], date_field=date, date_label=s["date_label"])
    relation_id = s["relation_id"]
    require(sum(node.get("unit_id") == relation_id for node in targets) == 1, "The relation must exist in exactly one dashboard component.")
    units[relation_id] = fetch_edit_unit_detail(page, relation_id, s["dashboard_id"], "draft")
    projected[relation_id] = rebind_filter(units[relation_id], s, period)
    public_hash = None
    if not sandbox:
        public = fetch_dashboard_config(page, s["dashboard_id"])
        require(public.get("dashboardId") == s["dashboard_id"] and public.get("dashboardName") == s["dashboard_name"], "Published view identity drifted.")
        public_hash = canonical_sha256(parse_dashboard_html(public))
    plan = {
        "artifact_type": PLAN_TYPE, "version": 1, "selection": s, "sandbox": sandbox,
        "base_profile_sha256": profile["profile_sha256"], "schema_sha256": canonical_sha256(schema),
        "untouched_profile_sha256": _untouched_profile_sha256(profile, s),
        "published_schema_sha256": public_hash, "field_sha256": canonical_sha256([period, date]),
        "before": {identity: canonical_sha256(stable_unit(unit)) for identity, unit in units.items()},
        "after": {identity: canonical_sha256(stable_unit(unit)) for identity, unit in projected.items()},
    }
    plan["plan_sha256"] = canonical_sha256(plan)
    return LiveDraft(schema, units, projected, plan)


def _snapshot_unit(page, dashboard_id: str, identity: str) -> str:
    return canonical_sha256(stable_unit(fetch_edit_unit_detail(page, identity, dashboard_id, "draft")))


def _write(page, s, identity, value, observations):
    _config(page, s)
    writer = _write_filter_detail if identity == s["relation_id"] else _write_unit_detail
    writer(page, s["dashboard_id"], value, observations)


def _filtered_checks(page, s: dict, *, rebound: bool) -> list[dict]:
    outcomes = []
    period_id = s["period_to_field_id" if rebound else "period_from_field_id"]
    for chart in s["charts"]:
        unit_id = chart["unit_id"]
        for period in s["verification_periods"]:
            payload = default_unit_value_payload(unit_id, 100)
            payload.update(isConfig=True, versionId="draft", publicFilterList=[{
                "paramId": period_id, "fieldId": period_id, "filterUnitId": s["filter_id"], "filterValue": [period],
                "condition": "in", "orgParamType": 2, "isSelectAll": 0,
            }])
            result = post_json(page, f"{EDIT_API_ROOT}/value/unit", payload, timeout_ms=60_000)
            summary = summarize_unit_value(unit_id, result, chart["unit_type"])
            require(summary.get("status") == "data_ready", f"Filtered draft data unavailable for {unit_id} / {period}: {summary.get('status')}.")
            expected_axis = s["date_to_field_id"] if rebound else chart["from_field_id"]
            axis_ids = (
                {str(summary["x_axis_field_id"])} if chart["unit_type"] == "u_line"
                else {str(field["field_id"]) for field in summary["title_fields"]}
            )
            require(expected_axis in axis_ids and summary.get("has_more") is not True,
                    f"Filtered draft values for {unit_id} did not return the reviewed date field and a complete result.")
            outcomes.append({"unit_id": unit_id, "period": period, "filter_field_id": period_id,
                             "axis_field_id": expected_axis, "status": summary["status"],
                             "rows": summary["data_row_count"] or summary["x_axis_count"],
                             "task_ids": summary["task_ids"], "total_task_id": summary["total_task_id"]})
    return outcomes


def _restore(page, s, live, touched, observations):
    dashboard_id = s["dashboard_id"]
    plan = live.plan
    require(canonical_sha256(parse_dashboard_html(_config(page, s))) == plan["schema_sha256"], "Draft schema drifted; recovery stopped.")
    for identity in reversed(touched):
        before, after = plan["before"][identity], plan["after"][identity]
        current = _snapshot_unit(page, dashboard_id, identity)
        if current != before:
            require(current == after and _snapshot_unit(page, dashboard_id, identity) == current,
                    f"Unit {identity} differs from both reviewed states; recovery stopped.")
            _write(page, s, identity, live.units[identity], observations)
            require(_snapshot_unit(page, dashboard_id, identity) == before, f"Recovery readback failed for {identity}.")
    _write_dashboard_schema(page, dashboard_id, s["dashboard_name"], live.schema, observations, plan["schema_sha256"])


def _mutate(page, live: LiveDraft, artifacts: Path, receipt: dict) -> None:
    plan = live.plan
    s, dashboard_id = plan["selection"], plan["selection"]["dashboard_id"]
    touched: list[str] = []
    try:
        for identity, before in plan["before"].items():
            require(_snapshot_unit(page, dashboard_id, identity) == before and _snapshot_unit(page, dashboard_id, identity) == before,
                    f"Unit {identity} drifted during the write preflight.")
            touched.append(identity)
            _write(page, s, identity, live.projected[identity], receipt["writes"])
            require(_snapshot_unit(page, dashboard_id, identity) == plan["after"][identity], f"Rebound unit {identity} did not match the reviewed projection.")
        _write_dashboard_schema(page, dashboard_id, s["dashboard_name"], live.schema, receipt["writes"], plan["schema_sha256"])
        require(canonical_sha256(parse_dashboard_html(_config(page, s))) == plan["schema_sha256"], "Saved schema does not match the baseline.")
        for identity, expected in plan["after"].items():
            require(_snapshot_unit(page, dashboard_id, identity) == expected, f"Saved draft unit drifted: {identity}.")
        receipt["draft_value_checks"] = _filtered_checks(page, s, rebound=True)
        _, post = _profile(page, s, artifacts, include_fields=True)
        require(_untouched_profile_sha256(post, s) == plan["untouched_profile_sha256"], "Out-of-scope draft profile changed.")
        receipt["post_profile_sha256"] = post["profile_sha256"]
        if not plan["sandbox"]:
            public_hash = canonical_sha256(parse_dashboard_html(fetch_dashboard_config(page, dashboard_id)))
            require(public_hash == plan["published_schema_sha256"], "Published schema changed during the draft operation.")
            receipt["published_schema_sha256"] = public_hash
        receipt["saved_draft_verified"] = True
    except Exception as exc:
        receipt["apply_error"] = str(exc)
        raise
    finally:
        if touched and (plan["sandbox"] or not receipt.get("saved_draft_verified")):
            _restore(page, s, live, touched, receipt["writes"])
            current = _live(page, s, artifacts, plan["sandbox"])
            require(current.plan["plan_sha256"] == plan["plan_sha256"], "Full draft baseline could not be proven after recovery.")
            receipt["restored_baseline"] = True


def _read(path: Path) -> dict:
    result = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(result, dict), "Expected a JSON object.")
    return result


def cmd_period_date_rebind(args) -> int:
    planning = args.mode == "plan"
    sandbox = bool(args.sandbox)
    if planning:
        selection = _read(args.input)
        plan = None
    else:
        plan = _read(args.input)
        selection = plan.get("selection") or {}
        observed_sha = canonical_sha256({k: v for k, v in plan.items() if k != "plan_sha256"})
        require(plan.get("artifact_type") == PLAN_TYPE and plan.get("version") == 1 and plan.get("sandbox") is sandbox
                and observed_sha == plan.get("plan_sha256") == args.plan_sha256, "The exact reviewed plan and execution mode are required.")
        if sandbox:
            require(args.confirm_sandbox_write and not args.confirm_production_write and args.headed,
                    "Sandbox execution needs a visible browser and explicit sandbox confirmation.")
        else:
            require(args.confirm_production_write and not args.confirm_sandbox_write, "Draft Apply needs explicit production confirmation.")
            capability = capability_by_operation(load_capability_registry(), OPERATION)
            require(capability.get("maturity") == "verified" and capability.get("write_policy") == "allowlisted"
                    and capability.get("adapter") == "read_dashboard.commands.period_date_rebind.cmd_period_date_rebind", "The exact production draft adapter is not allowlisted.")
    validate_selection(selection, args.domain)
    if sandbox:
        require("沙箱" in selection["dashboard_name"] and "测试" in selection["dashboard_name"], "Sandbox execution requires the exact named test sandbox.")
    else:
        _core_api()
        from text2sql_core.dashboard_domains import validate_dashboard_domain_registration

        registered, diagnostics = validate_dashboard_domain_registration(selection["dashboard_id"], args.domain)
        require(registered.get("status") == "registered", f"Dashboard domain registration failed: {diagnostics}.")
    if args.existing_session_only:
        require(args.state_path.is_file(), "The isolated authenticated state file is required.")
    else:
        load_env_file(args.env_file)
    ensure_runtime([args.artifacts_dir, args.state_path.parent, args.output.parent])
    artifacts = safe_artifact_dir(args.artifacts_dir)
    with import_playwright()() as playwright:
        browser, context = launch_context(playwright, args.state_path, args.headed, args.browser_channel, args.executable_path)
        page = context.new_page()
        try:
            edit_url = build_edit_url(selection["dashboard_id"])
            if args.existing_session_only:
                page.goto(edit_url, wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(args.wait_ms)
                require(not is_login_page(page), "The isolated Taitan login has expired.")
            else:
                open_edit_page(page, args, context, edit_url)
            live = _live(page, selection, artifacts, sandbox)
            if planning:
                write_json(live.plan, args.output)
                print(json.dumps({"ok": True, "plan_sha256": live.plan["plan_sha256"], "writes": 0}))
                return 0
            require(plan == live.plan, "The live draft or published baseline no longer matches the exact plan.")
            receipt = {"artifact_type": "DashboardPeriodDateRebindReceipt", "plan_sha256": args.plan_sha256,
                       "dashboard_id": selection["dashboard_id"], "sandbox": sandbox, "writes": [], "published": False}
            lock_dir = DEFAULT_ARTIFACTS.parent / "draft-rebind-locks"
            lock_dir.mkdir(parents=True, exist_ok=True)
            target_lock = lock_dir / f"{selection['dashboard_id']}.lock"
            with target_lock.open("x", encoding="utf-8") as lock:
                lock.write(args.plan_sha256 + "\n")
            try:
                attempt = _attempt_marker_path(selection["dashboard_id"], args.plan_sha256)
                attempt.parent.mkdir(parents=True, exist_ok=True)
                require(not attempt.exists(), f"An attempt already exists for this plan. Review {attempt} before taking further action.")
                backup = _backup_path(artifacts, selection["dashboard_id"], args.plan_sha256)
                write_json({"plan_sha256": args.plan_sha256, "schema": live.schema, "units": live.units}, backup)
                with attempt.open("x", encoding="utf-8") as marker:
                    marker.write(args.plan_sha256 + "\n")
                receipt.update(backup=str(backup), attempt_marker=str(attempt))
                try:
                    _mutate(page, live, artifacts, receipt)
                    receipt["ok"] = True
                except Exception as exc:
                    receipt.update(ok=False, error=str(exc))
            finally:
                target_lock.unlink()
            write_json(receipt, args.output)
            print(json.dumps({k: v for k, v in receipt.items() if k != "writes"}, ensure_ascii=False))
            return 0 if receipt["ok"] else 1
        finally:
            browser.close()
