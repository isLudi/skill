"""Append the exact Market Consultant 2h outbound ratio to its approved draft pivot.

Generic ratio editing remains sandbox-only. This production adapter only adds
one fixed physical ratio, reusing the established hash/readback/recovery engine.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

from _shared.browser import import_playwright, launch_context
from _shared.config import RUNTIME_DIR
from _shared.fs_utils import ensure_runtime, safe_artifact_dir
from usql_web_query.query_auth import verify_query_identity
from ..common import write_json
from ..dashboard_change import _core_api, canonical_sha256
from ..dashboard_write_adapters import _formula_item
from ..edit_profile import build_edit_url
from ..pivot_ratio_fields import require, validate_selection as validate_ratio_selection
from ..write_capabilities import capability_by_operation, load_capability_registry
from .pivot_ratio_draft import _live, _mutate, _read, _validate_checks, _write_backup

OPERATION = "append_market_outbound_2h_draft"
ADAPTER = "read_dashboard.commands.outbound_2h.cmd_outbound_2h"
PLAN_TYPE = "MarketOutbound2hDraftPlan"
BOARD = "dashboard_3730722176629411841"
UNIT = "unit_3730781607175761920"
COMPONENT = "node_ocmki2t94b1"
ANCHOR = "customized_1032719140202569728"
TEMPLATE = "customized_1032719140399702017"
DENOMINATOR = {"field_id": "8103974494234625", "field_name": "valid_lead_count"}
TIMELY_FIELDS = {
    "6h外呼": (TEMPLATE, "first_call_in_6h"),
    "12h外呼": ("customized_1032719139728613377", "first_call_in_12h"),
    "24h外呼": ("customized_1032719139825082368", "first_call_in_24h"),
}


def validate_selection(s: dict) -> None:
    validate_ratio_selection(s, False, inherit_template_style=True)
    require((s["domain"], s["dashboard_id"], s["dashboard_name"], s["owner"], s["model_id"],
             s["subject_id"], s["unit_id"], s["component_id"], s["unit_name"]) ==
            ("market_consultant", BOARD, "外呼过程数据看板", "lvshuai01", 2054, 207787, UNIT, COMPONENT, "总体数据"),
            "Only the registered Market Consultant overall outbound pivot is in scope.")
    require(s["denominator"] == DENOMINATOR and len(s["ratios"]) == 1
            and s["ratios"][0]["name"] == "2h外呼"
            and s["ratios"][0]["numerator"]["field_name"] == "first_call_in_2h",
            "Only the physical 2h numerator over the existing valid-lead denominator is supported.")
    require(not s["remove_ids"] and not s["move_to_end_ids"] and s["anchor_id"] == ANCHOR
            and s["decimals"] == 1 and s["header_color"] is None,
            "The 2h column must be appended after 5min with the inherited 6h style and no removal or reordering.")


def denominator_proof(page, unit: dict, subject_id: int) -> list[dict]:
    result = []
    for label, (field_id, numerator) in TIMELY_FIELDS.items():
        fields = [f for f in unit["unitMeasureList"] if f["fieldId"] == field_id and f["showName"] == label]
        require(len(fields) == 1, f"Existing {label} column identity drifted.")
        item = _formula_item(page, field_id)
        expression = "".join(str(item.get("formula") or "").split())
        fraction = f"sum(${{{numerator}}})/sum(${{valid_lead_count}})"
        require(item.get("subjectId") == subject_id and expression in (fraction, f"ifnull({fraction},0)")
                and any(str(x.get("paramId")) == DENOMINATOR["field_id"] and x.get("orgParamType") == 1
                        for x in item.get("dependencyIndicators") or []),
                f"Existing {label} no longer uses the approved valid-lead denominator.")
        result.append({"field_id": field_id, "formula_sha256": canonical_sha256(item), "denominator": DENOMINATOR})
    return result


def bind_live_plan(page, s: dict, artifacts: Path, checks: list[dict]):
    live = _live(page, s, artifacts, False, checks, template_field_id=TEMPLATE, preserve_template_style=True)
    ids = [f["fieldId"] for f in live.unit["unitMeasureList"]]
    require(ids.index(ANCHOR) + 1 == ids.index(TEMPLATE), "5min and 6h are no longer adjacent.")
    live.plan.update(artifact_type=PLAN_TYPE, operation=OPERATION,
                     denominator_proof=denominator_proof(page, live.unit, s["subject_id"]))
    live.plan.pop("plan_sha256", None)
    live.plan["plan_sha256"] = canonical_sha256(live.plan)
    return live


def preflight(args, document: dict) -> tuple[dict, list[dict]]:
    require(not args.output.exists(), "The output path already exists; refusing to overwrite it.")
    s, checks = document.get("selection") or {}, document.get("checks")
    validate_selection(s)
    _validate_checks(checks, 1)
    require(args.domain == s["domain"], "Domain mismatch.")
    _core_api()
    from text2sql_core.dashboard_domains import validate_dashboard_domain_registration
    registration, issues = validate_dashboard_domain_registration(s["dashboard_id"], args.domain)
    require(registration.get("status") == "registered" and not issues, "Dashboard domain registration is unavailable.")
    if args.mode == "apply":
        digest = canonical_sha256({k: v for k, v in document.items() if k != "plan_sha256"})
        require(document.get("artifact_type") == PLAN_TYPE and document.get("operation") == OPERATION
                and document.get("sandbox") is False and digest == document.get("plan_sha256") == args.plan_sha256,
                "An exact reviewed outbound plan and hash are required.")
        require(args.confirm_production_write, "Explicit production-draft confirmation is required.")
        cap = capability_by_operation(load_capability_registry(), OPERATION)
        require(cap.get("maturity") == "verified" and cap.get("write_policy") == "allowlisted"
                and cap.get("adapter") == ADAPTER and cap.get("readback_coverage") == "full",
                "The dedicated outbound draft adapter is not allowlisted.")
    require(args.state_path.is_file(), "The authenticated operator state is unavailable.")
    return s, checks


def cmd_outbound_2h(args) -> int:
    document = _read(args.input)
    s, checks = preflight(args, document)
    ensure_runtime([args.artifacts_dir, args.output.parent])
    artifacts = safe_artifact_dir(args.artifacts_dir)
    with import_playwright()() as playwright:
        browser, context = launch_context(playwright, args.state_path, args.headed, args.browser_channel, None)
        try:
            page = context.new_page()
            verify_query_identity(page, s["owner"])
            page.goto(build_edit_url(s["dashboard_id"]), wait_until="domcontentloaded", timeout=45000)
            live = bind_live_plan(page, s, artifacts, checks)
            if args.mode == "plan":
                write_json(live.plan, args.output)
                print(json.dumps({"ok": True, "plan_sha256": live.plan["plan_sha256"], "writes": 0}))
                return 0
            require(live.plan == document, "The draft, numerator, denominator, style or published baseline drifted.")
            locks = RUNTIME_DIR / "draft-rebind-locks"
            locks.mkdir(parents=True, exist_ok=True)
            lock = locks / f"{s['dashboard_id']}.lock"
            with lock.open("x", encoding="utf-8") as stream:
                stream.write(args.plan_sha256 + "\n")
            try:
                attempt = RUNTIME_DIR / "outbound-2h-attempts" / s["dashboard_id"] / f"{args.plan_sha256}.attempt"
                attempt.parent.mkdir(parents=True, exist_ok=True)
                require(not attempt.exists(), "This plan already has an attempted write; inspect its receipt.")
                backup = _write_backup(artifacts, s["dashboard_id"], args.plan_sha256,
                                       {"schema": live.schema, "unit": live.unit, "plan_sha256": args.plan_sha256})
                with attempt.open("x", encoding="utf-8") as stream:
                    stream.write(args.plan_sha256 + "\n")
                receipt = {"artifact_type": "MarketOutbound2hDraftReceipt", "operation": OPERATION,
                           "plan_sha256": args.plan_sha256, "dashboard_id": BOARD, "unit_id": UNIT,
                           "sandbox": False, "published": False, "backup": str(backup), "writes": [], "formulas": []}
                try:
                    _mutate(page, live, artifacts, receipt)
                    receipt["ok"] = True
                except Exception as exc:
                    receipt.update(ok=False, error=str(exc))
                write_json(receipt, args.output)
                print(json.dumps({k: v for k, v in receipt.items() if k not in ("writes", "value_checks")}, ensure_ascii=False))
                return 0 if receipt["ok"] else 1
            finally:
                lock.unlink()
        finally:
            browser.close()
