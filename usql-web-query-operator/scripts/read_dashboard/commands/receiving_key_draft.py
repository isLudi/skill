"""Switch the 2460 receiving metric in an isolated draft and verify its published version."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import time
from types import SimpleNamespace
from typing import Any

from _shared.browser import import_playwright, launch_context
from _shared.config import DEFAULT_ENV_FILE, RUNTIME_DIR
from _shared.errors import UsageError
from _shared.fs_utils import ensure_runtime, safe_artifact_dir
from usql_web_query.data_center import DataCenterClient, select_dataset_for_replacement
from usql_web_query.data_center_replacement import sql_sha256
from usql_web_query.data_center_schedule import parameter_values
from usql_web_query.query_auth import query_credentials, verify_query_identity

from ..common import write_json
from ..constants import UNIT_VALUE_API
from ..dashboard_change import _core_api, canonical_sha256
from ..dashboard_write_adapters import _formula_item, _formula_projection, _write_dashboard_schema, _write_formula
from ..edit_profile import (
    EDIT_API_ROOT, build_edit_url, extract_loaded_html_id, fetch_dataset_fields,
    fetch_edit_dashboard_config, fetch_edit_unit_detail, open_edit_page,
)
from ..filter_edit import build_publish_payload, publish_dashboard
from ..pivot_ratio_fields import require
from ..pivot_rebind import _cell_value
from ..profile import (
    default_unit_value_payload, extract_component_units, fetch_dashboard_config, fetch_unit_detail,
    parse_dashboard_html, post_json, summarize_public_filter_detail,
)
from ..write_capabilities import capability_by_operation, load_capability_registry


OPERATION = "switch_qingcheng_receiving_key_draft"
ADAPTER = "read_dashboard.commands.receiving_key_draft.cmd_receiving_key_draft"
PLAN_TYPE = "DashboardReceivingKeyPlan"
RECEIPT_TYPE = "DashboardReceivingKeyDraftReceipt"
VERSION_LIST_API = f"{EDIT_API_ROOT}/version/dashboard/searchPublishVersionList"

OWNER = "lvshuai01"
DATASET_ID = "menu_set_3833505841890963456"
MODEL_ID = "2460"
BOARDS = {
    "dashboard_3885764906392891392": "转化数据看板",
    "dashboard_4019042032853901313": "青橙运营侧看板",
}
FORMULA_NAME = "接量人力"
KEY_FIELD = "legacy_receiving_key"
OLD_FORMULA = "count(DISTINCT case ${v_lead} when 0 then 0 when 1 then 0 when 2 then 0 else ${employee_email_name} end) -1"
NEW_FORMULA = "count(DISTINCT ${legacy_receiving_key}) - 1"
STOCK_COMPATIBILITY_SQL_SHA256 = "993718275e3f2e6a013bb225602e8fec8ffb23403d0fb2990ba6cec91fdc0995"
FORMULA_ID = re.compile(r"customized_\d+")
VERSION_ID = re.compile(r"version_\d+")
SHA256 = re.compile(r"[a-f0-9]{64}")


@dataclass
class BoardVersion:
    version: str
    config: dict[str, Any]
    layout: dict[str, Any]
    semantic: dict[str, Any]
    definitions: dict[str, dict[str, Any]]
    targets: dict[str, str]
    receiving: dict[str, Any]
    receiving_key: str
    old_dependencies: list[dict[str, Any]]


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), "The reviewed artifact must be a JSON object.")
    return value


def _active_version(page: Any, dashboard_id: str) -> dict[str, Any]:
    payload = post_json(page, VERSION_LIST_API, {"id": dashboard_id})
    entries = payload.get("data")
    require(isinstance(entries, list), "Published version list is unavailable.")
    current = [
        row for row in entries if isinstance(row, dict) and row.get("versionStatus") == 1
        and row.get("isGrayscale") == 0
    ]
    require(len(current) == 1, "The dashboard needs one unambiguous active full-release version.")
    active = current[0]
    require(active.get("dashboardId") == dashboard_id and active.get("dashboardName") == BOARDS[dashboard_id]
            and VERSION_ID.fullmatch(str(active.get("versionId") or "")), "The active published identity differs from the target.")
    return active


def _sanitize_version_fields(value: Any, aliases: dict[str, str], subjects: dict[int, str]) -> Any:
    if isinstance(value, str):
        return FORMULA_ID.sub(lambda match: aliases.get(match.group(), match.group()), value)
    if isinstance(value, list):
        return [_sanitize_version_fields(row, aliases, subjects) for row in value]
    if not isinstance(value, dict):
        return value
    cleaned = {}
    for key, data in value.items():
        if key in {"htmlId", "versionId"}:
            continue
        if key == "preFilterTaskId" and re.fullmatch(r"[\d,;]*", str(data or "")):
            continue
        if key == "subjectId" and type(data) is int and data in subjects:
            data = subjects[data]
        name = FORMULA_ID.sub(lambda match: aliases.get(match.group(), match.group()), key)
        require(name not in cleaned, "Version-normalized configuration keys are ambiguous.")
        cleaned[name] = _sanitize_version_fields(data, aliases, subjects)
    return cleaned


def _field(tree: list[dict[str, Any]], title: str, org_type: int, data_type: int) -> dict[str, Any]:
    matches = [row for row in tree if row.get("title") == title]
    require(len(matches) == 1, f"The subject has no unique {title} field.")
    field = matches[0]
    require(field.get("org_param_type") == field.get("change_param_type") == org_type
            and field.get("data_type") == data_type and field.get("is_choice") is True,
            f"The model field {title} has an unexpected type.")
    return field


def _dependency(field: dict[str, Any]) -> dict[str, Any]:
    return {"paramId": str(field["key"]), "orgParamType": field["org_param_type"], "needBoundaryValue": False}


def _normalized_expression(expression: str) -> str:
    return re.sub(r"\s+", "", expression).casefold()


def _headcount_change(draft: BoardVersion, mode: str = "compatibility") -> dict[str, Any]:
    original = draft.receiving
    key_dependencies = [{"paramId": draft.receiving_key, "orgParamType": 2, "needBoundaryValue": False}]
    require(mode in {"compatibility", "restore-stock"}, "Unsupported receiving-key change.")
    source = OLD_FORMULA if mode == "compatibility" else NEW_FORMULA
    expected = draft.old_dependencies if mode == "compatibility" else key_dependencies
    require(_normalized_expression(original["formula"]) == _normalized_expression(source)
            and original["dependencyIndicators"] == expected,
            "The existing receiving formula differs from the supported metric contract.")
    return {
        **original,
        "formula": NEW_FORMULA if mode == "compatibility" else OLD_FORMULA,
        "dependencyIndicators": key_dependencies if mode == "compatibility" else draft.old_dependencies,
    }


def _read_version(page: Any, dashboard_id: str, version: str) -> BoardVersion:
    config = fetch_edit_dashboard_config(page, dashboard_id, version)
    require(config.get("dashboardId") == dashboard_id and config.get("dashboardName") == BOARDS[dashboard_id],
            "The dashboard revision did not resolve to the requested identity.")
    if version == "draft":
        require(config.get("haveEditPermission") is True and OWNER in config.get("ownerList", []),
                "The current identity is not an owner with edit access to this draft.")
    layout = parse_dashboard_html(config)
    components = extract_component_units(layout)
    require(layout.get("componentsTree") and components, "The dashboard layout has no verified component tree.")
    units = {}
    subjects = {}
    for component in components:
        uid = str(component["unit_id"])
        unit = fetch_edit_unit_detail(page, uid, dashboard_id, version)
        require(unit.get("unitId") == uid or (uid.startswith("public_filter_relation_") and not unit.get("unitId")),
                "A component returned a different unit identity.")
        units[uid] = unit
        model = unit.get("dashboardModel") or {}
        if subject := model.get("subjectId"):
            require(type(subject) is int and model.get("modelType") == 2,
                    "A dashboard unit returned an unsupported model binding.")
            model_id = str(model.get("applicationModelId") or "")
            require(model.get("dashboardId") == dashboard_id and model_id.isdigit(), "A subject belongs to another dashboard.")
            require(subject not in subjects or subjects[subject] == model_id, "A subject maps to multiple application models.")
            subjects[subject] = model_id
    model_subjects = [key for key, value in subjects.items() if value == MODEL_ID]
    require(len(model_subjects) == 1 and len(set(subjects.values())) == len(subjects), "The dataset subject is ambiguous.")
    model_subject = model_subjects[0]
    trees = fetch_dataset_fields(page, dashboard_id, sorted(subjects), [2], [])
    require({tree.get("subject_id") for tree in trees} == set(subjects) and len(trees) == len(subjects),
            "A dashboard subject was absent from the field catalog.")
    aliases = {}
    formulas = {}
    model_tree = []
    for tree in trees:
        subject = tree["subject_id"]
        rows = tree.get("fields") or []
        require(rows and not tree.get("error"), "A subject field catalog is incomplete.")
        if subject == model_subject:
            model_tree = rows
        for entry in rows:
            key = str(entry["key"])
            if not FORMULA_ID.fullmatch(key):
                continue
            identity = f"formula:{subjects[subject]}:{entry['title']}"
            require(key not in aliases and identity not in formulas, "A calculated field identity is not unique.")
            data = _formula_projection(_formula_item(page, key))
            require(data["subjectId"] == subject and data["columnKey"] == key and data["columnName"] == entry["title"],
                    "A calculated field readback disagrees with its catalog.")
            aliases[key] = identity
            formulas[identity] = data
    field = _field(model_tree, KEY_FIELD, 2, 2)
    receiving_key = str(field["key"])
    require(receiving_key.isdigit(), "The compatibility key must be a physical text dimension.")
    receiving = formulas[f"formula:{MODEL_ID}:{FORMULA_NAME}"]
    old_dependencies = [_dependency(_field(model_tree, "v_lead", 1, 1)),
                        _dependency(_field(model_tree, "employee_email_name", 2, 2))]
    affected = {receiving["columnKey"]}
    for _ in formulas:
        consumers = {row["columnKey"] for row in formulas.values()
                     if any(str(dep["paramId"]) in affected for dep in row["dependencyIndicators"])}
        if consumers <= affected:
            break
        affected.update(consumers)
    require(any(row["columnName"] == "人效" and row["columnKey"] in affected for row in formulas.values()),
            "The shared productivity dependency is missing.")
    targets = {}
    for uid, unit in units.items():
        if affected.intersection(FORMULA_ID.findall(json.dumps(unit, ensure_ascii=False))):
            model = unit.get("dashboardModel") or {}
            require(model.get("subjectId") == model_subject, "A receiving metric is referenced outside the reviewed model subject.")
            targets[uid] = str(unit.get("unitName") or "")
    require(targets, "There are no verifiable consumers of the receiving metric.")
    # Numeric unit record IDs and filter prefetch IDs are generated for each version.
    unit_projection = {uid: {k: v for k, v in unit.items() if k != "id"} for uid, unit in units.items()}
    catalogs = {
        subjects[tree["subject_id"]]: sorted(
            (_sanitize_version_fields(row, aliases, subjects) for row in tree["fields"]),
            key=lambda row: str(row["key"]),
        )
        for tree in trees
    }
    projected = {
        "layout": _sanitize_version_fields(layout, aliases, subjects),
        "units": _sanitize_version_fields(unit_projection, aliases, subjects),
        "catalogs": catalogs,
        "formulas": {
            ident: _sanitize_version_fields({**item, "formula": item["formula"].strip()}, aliases, subjects)
            for ident, item in formulas.items()
        },
    }
    return BoardVersion(version, config, layout, projected, formulas, targets, receiving, receiving_key, old_dependencies)


def _published(page: Any, dashboard_id: str) -> BoardVersion:
    row = _active_version(page, dashboard_id)
    published = _read_version(page, dashboard_id, row["versionId"])
    market = fetch_dashboard_config(page, dashboard_id)
    require(market.get("dashboardId") == dashboard_id and market.get("dashboardName") == BOARDS[dashboard_id]
            and parse_dashboard_html(market) == published.layout == parse_dashboard_html(row),
            "The version list, editor and published dashboard layout did not agree.")
    return published


def _compatibility(page: Any, state_path: Path, receipt: dict[str, Any], physical_key: str) -> dict[str, Any]:
    require(receipt.get("fully_verified") is True and receipt.get("model_id") == MODEL_ID
            and receipt.get("dataset_id") == DATASET_ID and receipt.get("field", {}).get("paramId") == physical_key,
            "A verified compatibility extraction receipt for this field is required.")
    expected_hash = str(receipt.get("saved_sql_sha256") or "")
    run_id = str(receipt.get("latest_run", {}).get("id") or "")
    require(SHA256.fullmatch(expected_hash) and run_id.isdigit(), "The compatibility receipt is incomplete.")
    client = DataCenterClient(page, state_path)
    dataset = select_dataset_for_replacement(client.discover_datasets(), domain="qingcheng", dataset_id=DATASET_ID)
    saved = client.fetch_dataset_sql(dataset)
    require(dataset.file_value == MODEL_ID and dataset.name == "转化数据"
            and sql_sha256(saved.execute_sql) == expected_hash, "Live SQL differs from the verified compatibility version.")
    fields = [row for row in parameter_values(saved.detail_payload) if row["fieldName"] == KEY_FIELD]
    require(len(fields) == 1 and fields[0]["paramId"] == physical_key and fields[0]["fieldType"] == "TEXT",
            "The compatibility field is missing from saved Data Center metadata.")
    schedule = saved.detail_payload.get("schedule") or {}
    require(schedule.get("taskStatus") is True and schedule.get("isExpire") is False and schedule.get("taskId"),
            "The Data Center extraction schedule became unavailable.")
    require(any(run.id == run_id and run.status == "SUCCESS" for run in client.fetch_schedule_runs(schedule["taskId"], page_size=50)),
            "The compatibility extraction is not verified in the current run history.")
    return {"dataset_id": DATASET_ID, "sql_sha256": expected_hash, "run_id": run_id, "physical_key": physical_key}


def _expected_semantic(state: BoardVersion, requested: dict[str, Any]) -> dict[str, Any]:
    name = f"formula:{MODEL_ID}:{FORMULA_NAME}"
    updated = {**state.semantic, "formulas": dict(state.semantic["formulas"])}
    updated["formulas"][name] = {
        **state.semantic["formulas"][name],
        "formula": requested["formula"].strip(),
        "dependencyIndicators": requested["dependencyIndicators"],
    }
    return updated


def _build_plan(
    page: Any, dashboard_id: str, state_path: Path, compatibility: dict[str, Any],
    mode: str = "compatibility",
) -> tuple[dict[str, Any], BoardVersion]:
    draft = _read_version(page, dashboard_id, "draft")
    published = _published(page, dashboard_id)
    require(draft.semantic == published.semantic, "The draft contains other changes relative to the current published version.")
    require(draft.receiving["subjectId"] != published.receiving["subjectId"]
            and draft.receiving["columnKey"] != published.receiving["columnKey"],
            "The receiving metric is not isolated from the published version.")
    after = _headcount_change(draft, mode)
    data = _compatibility(page, state_path, compatibility, draft.receiving_key)
    if mode == "restore-stock":
        require(data["sql_sha256"] == STOCK_COMPATIBILITY_SQL_SHA256,
                "Native stock receiving calculation requires the reconciled presplit compatibility SQL.")
    plan = {
        "artifact_type": PLAN_TYPE, "schema_version": "1.0.0", "operation": OPERATION,
        "dashboard_id": dashboard_id, "dashboard_name": BOARDS[dashboard_id], "owner": OWNER, "calculation_mode": mode,
        "published_version": published.version, "published_sha256": canonical_sha256(published.semantic),
        "published_receiving_field_id": str(published.receiving["columnKey"]),
        "draft_sha256": canonical_sha256(draft.semantic), "draft_layout_sha256": canonical_sha256(draft.layout),
        "after_sha256": canonical_sha256(_expected_semantic(draft, after)),
        "before": draft.receiving, "after": after, "targets": draft.targets, "compatibility": data,
    }
    plan["plan_sha256"] = canonical_sha256(plan)
    return plan, draft


def _assert_current_public(page: Any, plan: dict[str, Any]) -> None:
    state = _published(page, plan["dashboard_id"])
    require(state.version == plan["published_version"] and canonical_sha256(state.semantic) == plan["published_sha256"],
            "The published version drifted from the reviewed baseline.")


def _checked_plan(path: Path, expected: str) -> dict[str, Any]:
    plan = _read(path)
    require(plan.get("artifact_type") == PLAN_TYPE and plan.get("operation") == OPERATION
            and plan.get("dashboard_id") in BOARDS and plan.get("owner") == OWNER,
            "The plan is not an authorized receiving-key artifact.")
    body = {key: value for key, value in plan.items() if key != "plan_sha256"}
    require(canonical_sha256(body) == expected == plan.get("plan_sha256"), "The exact reviewed plan SHA-256 is required.")
    return plan


def _claim(plan: dict[str, Any], stage: str) -> None:
    claims = RUNTIME_DIR / "receiving-key-attempts" / plan["dashboard_id"]
    claims.mkdir(parents=True, exist_ok=True)
    try:
        with (claims / f"{plan['plan_sha256']}-{stage}.json").open("x", encoding="utf-8") as handle:
            json.dump({"stage": stage, "at": datetime.now(timezone.utc).isoformat()}, handle)
    except FileExistsError:
        raise UsageError("This exact plan already attempted this write. Read the existing outcome before proceeding.") from None


def _verify_pivot_values(page: Any, plan: dict[str, Any], *, draft: bool) -> list[dict[str, Any]]:
    dashboard_id = plan["dashboard_id"]
    public = fetch_dashboard_config(page, dashboard_id)
    filters = []
    for component in extract_component_units(parse_dashboard_html(public)):
        unit_id = component["unit_id"]
        if unit_id.startswith("public_filter_relation_"):
            detail = fetch_unit_detail(page, unit_id)
            filters.extend(summarize_public_filter_detail(detail)["filters"])
    verified = []
    for unit_id, label in plan["targets"].items():
        payload = default_unit_value_payload(unit_id, 25)
        api = UNIT_VALUE_API
        if draft:
            api = EDIT_API_ROOT + "/value/unit"
            payload.update(isConfig=True, versionId="draft")
        for control in filters:
            if unit_id not in control["dashboard_units"] or "期次" not in str(control["unit_name"]):
                continue
            match = next((str(f["field_id"]) for f in control["fields"] if str(f["field_id"]) == "408276"), None)
            if match:
                payload["publicFilterList"].append({
                    "paramId": match, "fieldId": match, "filterUnitId": control["unit_id"],
                    "filterValue": ["20261120期"], "condition": "in", "orgParamType": 2, "isSelectAll": 0,
                })
                break
        result = post_json(page, api, payload, timeout_ms=35000)
        unit = (result.get("data") or {}).get(unit_id) or {}
        require(unit.get("unitId") == unit_id and unit.get("errorCode") in (None, 0)
                and not unit.get("error") and unit.get("title") and isinstance(unit.get("data"), list),
                f"Native query failed in {label}: {unit.get('error') or unit.get('errorCode') or result.get('extraCode')}.")
        field_id = str(plan["after"]["columnKey"] if draft else plan["published_receiving_field_id"])
        rows = unit["data"]
        require(rows and all(isinstance(row, dict) and field_id in row for row in rows),
                f"Native query did not return the receiving metric for every row in {label}.")
        values = [_cell_value(row[field_id]) for row in rows]
        try:
            numeric_values = [float(value) for value in values]
        except (TypeError, ValueError):
            raise UsageError(f"Native query returned a non-numeric receiving metric in {label}.") from None
        require(all(value is not None and math.isfinite(number) for value, number in zip(values, numeric_values)),
                f"Native query returned a null or non-finite receiving metric in {label}.")
        verified.append({"unit_id": unit_id, "name": label, "row_count": len(unit["data"]),
                         "metric_field_id": field_id, "metric_value_count": len(values),
                         "task_ids": unit.get("taskIds"), "period_filtered": bool(payload["publicFilterList"])})
    return verified


def _apply(page: Any, plan: dict[str, Any], draft: BoardVersion, artifacts: Path, receipt: dict[str, Any]) -> None:
    dashboard_id = plan["dashboard_id"]
    _assert_current_public(page, plan)
    with (artifacts / "receiving-key-draft-backup.json").open("x", encoding="utf-8") as handle:
        json.dump({"plan": plan, "layout": draft.layout}, handle, ensure_ascii=False, indent=2)
    _claim(plan, "apply")
    try:
        _write_formula(page, plan["after"], receipt["writes"])
        saved = _read_version(page, dashboard_id, "draft")
        require(saved.receiving == plan["after"] and canonical_sha256(saved.semantic) == plan["after_sha256"],
                "The formula or the draft readback differs from the reviewed change.")
        receipt["draft_pivot_queries"] = _verify_pivot_values(page, plan, draft=True)
        _assert_current_public(page, plan)
        _write_dashboard_schema(page, dashboard_id, plan["dashboard_name"], draft.layout,
                                receipt["writes"], plan["draft_layout_sha256"])
        final = _read_version(page, dashboard_id, "draft")
        require(final.receiving == plan["after"] and canonical_sha256(final.semantic) == plan["after_sha256"],
                "The saved draft differs from the authorized formula-only result.")
        _assert_current_public(page, plan)
        receipt.update({"saved_draft_verified": True, "post_draft_sha256": plan["after_sha256"]})
    except Exception:
        _assert_current_public(page, plan)
        actual = _read_version(page, dashboard_id, "draft")
        if actual.receiving == plan["after"] and canonical_sha256(actual.semantic) == plan["after_sha256"]:
            _write_formula(page, plan["before"], receipt["writes"])
            restored = _read_version(page, dashboard_id, "draft")
            require(restored.receiving == plan["before"] and canonical_sha256(restored.semantic) == plan["draft_sha256"],
                    "The exact draft baseline could not be restored.")
            receipt["restored_draft_sha256"] = plan["draft_sha256"]
        raise


def _publish(page: Any, plan: dict[str, Any], compatibility: dict[str, Any], state_path: Path,
             description: str, receipt: dict[str, Any]) -> None:
    dashboard_id = plan["dashboard_id"]
    _assert_current_public(page, plan)
    draft = _read_version(page, dashboard_id, "draft")
    require(draft.receiving == plan["after"] and canonical_sha256(draft.semantic) == plan["after_sha256"],
            "The verified draft drifted before publish.")
    require(_compatibility(page, state_path, compatibility, draft.receiving_key) == plan["compatibility"],
            "The compatibility SQL, schema or extraction changed.")
    # The edit API issues a fresh htmlId on each read. Pin both checks and the
    # write to the HTML identity already loaded in this editor tab.
    html_id = extract_loaded_html_id(page.url)
    require(re.fullmatch(r"html_\d+", str(html_id or "")), "The editor did not expose a loaded draft HTML ID.")
    body_hash = canonical_sha256(build_publish_payload(draft.config, description, html_id))
    confirmed = _read_version(page, dashboard_id, "draft")
    require(confirmed.receiving == plan["after"] and canonical_sha256(confirmed.semantic) == plan["after_sha256"]
            and canonical_sha256(build_publish_payload(confirmed.config, description, html_id)) == body_hash,
            "The publish payload was not stable across immediate readbacks.")
    _assert_current_public(page, plan)
    _claim(plan, "publish")
    receipt["publish_submitted"] = True
    receipt["response"] = publish_dashboard(page, confirmed.config, description, html_id)
    require(receipt["response"].get("publish_status") in ("success", None)
            and receipt["response"].get("publish_error_code") in (0, None), "The dashboard publish returned an error.")
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        active = _active_version(page, dashboard_id)
        if active["versionId"] != plan["published_version"]:
            require(active.get("versionDescription") == description, "Another publish took the active version.")
            observed = _published(page, dashboard_id)
            require(observed.version == active["versionId"] and canonical_sha256(observed.semantic) == plan["after_sha256"],
                    "The active full-release version did not contain the exact authorized change.")
            require(observed.receiving["formula"].strip() == plan["after"]["formula"].strip()
                    and observed.receiving["dependencyIndicators"] == plan["after"]["dependencyIndicators"],
                    "The active published formula or field binding differs from the plan.")
            receipt["published_pivot_queries"] = _verify_pivot_values(page, plan, draft=False)
            receipt.update(fully_verified=True, published_version=observed.version,
                           published_sha256=plan["after_sha256"], published_formula=observed.receiving)
            return
        page.wait_for_timeout(2000)
    raise UsageError("The publish request was accepted but the active version was not verified.")


def cmd_receiving_key_draft(args: Any) -> int:
    plan = None if args.mode == "plan" else _checked_plan(args.plan, args.plan_sha256)
    dashboard_id = args.dashboard_id if plan is None else plan["dashboard_id"]
    require(dashboard_id in BOARDS and args.state_path.is_file(), "The exact dashboard and its isolated owner session are required.")
    _core_api()
    from text2sql_core.dashboard_domains import validate_dashboard_domain_registration

    resolution, problems = validate_dashboard_domain_registration(dashboard_id, "qingcheng")
    require(resolution.get("status") == "registered" and not problems, "The dashboard domain registry must be valid.")
    compatibility = _read(args.compatibility_receipt)
    if plan is not None:
        cap = capability_by_operation(load_capability_registry(), OPERATION)
        require(cap.get("maturity") == "verified" and cap.get("write_policy") == "allowlisted"
                and cap.get("adapter") == ADAPTER, "The receiving-key write is not allowlisted.")
    if args.mode == "apply":
        require(args.confirm_production_write, "Editing the isolated draft requires explicit confirmation.")
    if args.mode == "publish":
        publish_cap = capability_by_operation(load_capability_registry(), "publish_dashboard")
        require(publish_cap.get("write_policy") == "separate_confirmation", "Independent dashboard publish is unavailable.")
        applied = _read(args.apply_receipt)
        require(args.confirm_publish and args.version_description.strip()
                and canonical_sha256(applied) == args.apply_receipt_sha256
                and applied.get("artifact_type") == RECEIPT_TYPE and applied.get("saved_draft_verified") is True
                and applied.get("plan_sha256") == plan["plan_sha256"] and applied.get("post_draft_sha256") == plan["after_sha256"],
                "Publishing requires the independently approved exact verified draft receipt and version description.")
    artifacts = safe_artifact_dir(args.artifacts_dir)
    ensure_runtime([artifacts, args.output.parent])
    require(not args.output.exists(), "An existing output receipt or plan would be overwritten.")
    receipt = {"artifact_type": RECEIPT_TYPE if args.mode == "apply" else "DashboardReceivingKeyPublishReceipt",
               "plan_sha256": plan["plan_sha256"] if plan else None, "dashboard_id": dashboard_id, "writes": []}
    with import_playwright()() as playwright:
        browser, context = launch_context(playwright, args.state_path, args.headed, args.browser_channel, None)
        try:
            page = context.new_page()
            username, password = query_credentials(DEFAULT_ENV_FILE)
            require(username == OWNER, "The configured USQL owner does not match the receiving-key scope.")
            DataCenterClient(page, args.state_path).ensure_authenticated(username, password)
            verify_query_identity(page, OWNER)
            auth = SimpleNamespace(username=username, password=password, wait_ms=1500, state_path=args.state_path)
            open_edit_page(page, auth, context, build_edit_url(dashboard_id))
            context.storage_state(path=str(args.state_path))
            if args.mode == "plan":
                prepared, _ = _build_plan(page, dashboard_id, args.state_path, compatibility, args.calculation_mode)
                write_json(prepared, args.output)
                print(json.dumps({"plan_sha256": prepared["plan_sha256"], "components": len(prepared["targets"])}))
                return 0
            lock_dir = RUNTIME_DIR / "draft-rebind-locks"
            lock_dir.mkdir(parents=True, exist_ok=True)
            lock = lock_dir / (dashboard_id + ".lock")
            with lock.open("x", encoding="utf-8") as handle:
                handle.write(plan["plan_sha256"] + "\n")
            try:
                if args.mode == "apply":
                    prepared, draft = _build_plan(
                        page, dashboard_id, args.state_path, compatibility, plan.get("calculation_mode", "compatibility"),
                    )
                    require(prepared == plan, "The draft, published version or compatibility proof drifted from the plan.")
                    _apply(page, plan, draft, artifacts, receipt)
                else:
                    _publish(page, plan, compatibility, args.state_path, args.version_description.strip(), receipt)
            except Exception as exc:
                receipt.update(error=str(exc), ok=False)
                write_json(receipt, args.output)
                raise
            finally:
                lock.unlink()
            receipt["ok"] = True
            write_json(receipt, args.output)
            print(json.dumps({k: v for k, v in receipt.items() if k != "writes"}, ensure_ascii=False))
            return 0
        finally:
            context.close()
            browser.close()
