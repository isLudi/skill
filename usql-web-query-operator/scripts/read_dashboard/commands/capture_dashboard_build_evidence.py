"""Capture one redacted P4C request/readback evidence item in an authorized sandbox."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from _shared.auth import ensure_authenticated
from _shared.browser import import_playwright, launch_context
from _shared.env import load_env_file
from _shared.errors import UsageError
from _shared.fs_utils import ensure_runtime, safe_artifact_dir

from ..common import safe_filename, write_json
from ..constants import DASHBOARD_MARKET_URL
from ..dashboard_build_evidence import (
    build_dashboard_build_evidence,
    menu_folder_snapshot,
    preflight_build_evidence_capture,
)
from ..dashboard_change import require_complete_profile
from ..edit_profile import build_edit_url, open_edit_page, profile_edit_dashboard
from ..menu import fetch_dashboard_menu
from ..write_capabilities import is_dangerous_request, request_observation


BUILD_DANGEROUS_URL_FRAGMENTS = (
    "/move/",
    "movefolder",
    "changeparent",
    "createfolder",
    "folder/save",
)

COMPONENT_PALETTE_TITLES = {
    "create_metric_group_component": "指标卡组",
    "create_pivot_component": "透视表",
    "create_bar_component": "柱状图",
    "create_pie_component": "饼图",
    "create_public_filter": "全局筛选器",
}


def _load_sandbox_action_manifest(args) -> dict[str, Any] | None:
    path = getattr(args, "sandbox_action_manifest", None)
    if path is None:
        return None
    if not isinstance(path, Path) or not path.is_file():
        raise UsageError(f"Sandbox action manifest does not exist: {path}")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UsageError(f"Invalid sandbox action manifest: {path}") from exc
    if not isinstance(manifest, dict):
        raise UsageError("Sandbox action manifest must be a JSON object.")
    if manifest.get("artifact_type") != "DashboardBuildSandboxAction":
        raise UsageError(
            "Sandbox action manifest artifact_type must be DashboardBuildSandboxAction."
        )
    if manifest.get("schema_version") != "1.0.0":
        raise UsageError("Unsupported sandbox action manifest schema_version.")
    if manifest.get("operation") != args.operation:
        raise UsageError("Sandbox action manifest operation does not match the CLI operation.")
    if args.scope == "dashboard":
        if manifest.get("dashboard_id") != args.sandbox_dashboard_id:
            raise UsageError("Sandbox action manifest dashboard identity mismatch.")
        if manifest.get("dashboard_name") != args.expected_dashboard_name:
            raise UsageError("Sandbox action manifest dashboard name mismatch.")
        if args.operation in set(COMPONENT_PALETTE_TITLES) - {"create_public_filter"}:
            dataset = manifest.get("dataset")
            if not isinstance(dataset, dict):
                raise UsageError("Component sandbox action requires an exact dataset object.")
            required_dataset_keys = {
                "dataset_name",
                "application_model_id",
                "subject_id",
                "model_type",
                "dataset_schema_sha256",
                "field_binding_sha256",
            }
            missing = sorted(required_dataset_keys - set(dataset))
            if missing:
                raise UsageError(
                    "Component sandbox action dataset is missing: " + ", ".join(missing)
                )
            if not any(
                marker in str(dataset["dataset_name"]).casefold()
                for marker in ("sandbox", "test", "p4c", "沙箱", "测试")
            ):
                raise UsageError("Component evidence requires a dedicated sandbox dataset name.")
            for hash_key in ("dataset_schema_sha256", "field_binding_sha256"):
                value = str(dataset.get(hash_key) or "")
                if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
                    raise UsageError(f"Invalid {hash_key} in sandbox action manifest.")
    elif manifest.get("folder_id") not in {None, args.folder_id}:
        raise UsageError("Sandbox action manifest folder identity mismatch.")
    return manifest


def _visible_control_snapshot(page) -> dict[str, Any]:
    controls: list[dict[str, Any]] = []
    locator = page.locator("input:visible, textarea:visible, button:visible, [role=tab]:visible")
    for index in range(min(locator.count(), 250)):
        item = locator.nth(index)
        try:
            controls.append(
                {
                    "tag": item.evaluate("element => element.tagName.toLowerCase()"),
                    "text": (item.inner_text(timeout=500) or "")[:200],
                    "placeholder": item.get_attribute("placeholder"),
                    "title": item.get_attribute("title"),
                    "aria_label": item.get_attribute("aria-label"),
                    "type": item.get_attribute("type"),
                }
            )
        except Exception:  # noqa: BLE001 - diagnostic snapshot must not break the governed action
            continue
    body_text = page.locator("body").inner_text(timeout=5_000)
    return {"body_text": body_text[:30_000], "controls": controls}


def _write_automation_diagnostic(
    *, artifacts_dir: Path, operation: str, page, manifest: Mapping[str, Any]
) -> None:
    frames: list[dict[str, Any]] = []
    for frame in page.frames:
        try:
            frames.append(
                {
                    "name": frame.name,
                    "url": frame.url,
                    "body_text": frame.locator("body").inner_text(timeout=2_000)[:20_000],
                }
            )
        except Exception:  # noqa: BLE001 - a transient iframe must not abort evidence capture
            continue
    probe_texts = ["维度", "指标", "筛选", "数据"]
    for group_name in ("dimensions", "measures", "local_filters"):
        for field in manifest.get(group_name) or []:
            if isinstance(field, Mapping):
                value = field.get("logical_field_ref") or field.get("field_name")
                if value:
                    probe_texts.append(str(value))
    text_matches: dict[str, list[dict[str, Any]]] = {}
    for probe in dict.fromkeys(probe_texts):
        matches = page.get_by_text(probe, exact=True)
        values: list[dict[str, Any]] = []
        for index in range(min(matches.count(), 20)):
            item = matches.nth(index)
            try:
                values.append(
                    {
                        "tag": item.evaluate("element => element.tagName.toLowerCase()"),
                        "class": item.get_attribute("class"),
                        "parent_html": item.evaluate(
                            "element => (element.parentElement?.outerHTML || element.outerHTML).slice(0, 5000)"
                        ),
                    }
                )
            except Exception:  # noqa: BLE001 - diagnostic snapshot only
                continue
        text_matches[probe] = values
    write_json(
        {
            "artifact_type": "DashboardBuildSandboxUiDiagnostic",
            "operation": operation,
            "logical_resource_id": manifest.get("logical_resource_id"),
            "page": _visible_control_snapshot(page),
            "frames": frames,
            "text_matches": text_matches,
        },
        artifacts_dir / "dashboard-build-ui" / f"{safe_filename(operation)}.json",
    )


def _drag_palette_item_to_dashboard(page, palette_title: str) -> None:
    page.locator(".next-icon-zujianku").click()
    source = page.locator(f'div.snippet[title="{palette_title}"]')
    source.wait_for(state="visible", timeout=15_000)
    simulator = page.frame_locator('iframe[name="undefined-SimulatorRenderer"]')
    target = simulator.locator("#rootContent")
    target.wait_for(state="visible", timeout=15_000)
    source_box = source.bounding_box()
    target_box = target.bounding_box()
    if not source_box or not target_box:
        raise UsageError(f"Could not resolve drag coordinates for {palette_title}.")
    source_x = source_box["x"] + source_box["width"] / 2
    source_y = source_box["y"] + source_box["height"] / 2
    target_x = target_box["x"] + min(max(target_box["width"] / 2, 160), 480)
    target_y = target_box["y"] + min(max(target_box["height"] / 3, 140), 300)
    page.mouse.move(source_x, source_y)
    page.mouse.down()
    page.mouse.move(target_x, target_y, steps=24)
    page.wait_for_timeout(600)
    page.mouse.up()
    page.wait_for_timeout(4_000)


def _drag_between_locators(page, source, target, label: str) -> None:
    source.wait_for(state="visible", timeout=10_000)
    target.wait_for(state="visible", timeout=10_000)
    source_box = source.bounding_box()
    target_box = target.bounding_box()
    if not source_box or not target_box:
        raise UsageError(f"Could not resolve field drag coordinates for {label}.")
    page.mouse.move(
        source_box["x"] + source_box["width"] / 2,
        source_box["y"] + source_box["height"] / 2,
    )
    page.mouse.down()
    page.mouse.move(
        target_box["x"] + min(max(target_box["width"] / 2, 80), 220),
        target_box["y"] + max(target_box["height"] / 2, 8),
        steps=18,
    )
    page.wait_for_timeout(400)
    page.mouse.up()
    page.wait_for_timeout(1_500)


def _drag_field_to_slot(page, field_name: str, slot_name: str) -> None:
    source_text = page.get_by_text(field_name, exact=True)
    if source_text.count() != 1:
        raise UsageError(
            f"Expected exactly one dataset field named {field_name}; found {source_text.count()}."
        )
    source = source_text.locator("xpath=parent::*")
    slot_labels = page.get_by_text(slot_name, exact=True)
    if slot_labels.count() < 1:
        raise UsageError(f"Component slot not found: {slot_name}")
    slot_label = slot_labels.nth(0)
    target = slot_label.locator("xpath=following-sibling::div//main")
    _drag_between_locators(page, source, target, f"{field_name}->{slot_name}")


def _field_name(field: Mapping[str, Any]) -> str:
    value = field.get("field_name") or field.get("logical_field_ref")
    if not value:
        raise UsageError("Sandbox action field entry requires field_name or logical_field_ref.")
    return str(value)


def _automate_dashboard_component_creation(page, args, manifest, artifacts_dir: Path) -> None:
    palette_title = COMPONENT_PALETTE_TITLES.get(args.operation)
    if not palette_title:
        raise UsageError(f"No component palette mapping exists for {args.operation}.")
    requested_title = manifest.get("palette_title")
    if requested_title not in {None, palette_title}:
        raise UsageError("Sandbox action manifest palette title does not match the operation.")
    _drag_palette_item_to_dashboard(page, palette_title)
    if args.operation != "create_public_filter":
        dataset = manifest["dataset"]
        chooser = page.get_by_text("+ 请选择数据集", exact=True)
        chooser.wait_for(state="visible", timeout=10_000)
        chooser.click()
        page.wait_for_timeout(2_000)
        page.get_by_text("SQL数据集", exact=True).click()
        page.wait_for_timeout(1_000)
        modal_inputs = page.locator("input:visible")
        if modal_inputs.count() > 0:
            modal_inputs.last.fill(str(dataset["dataset_name"]))
            page.wait_for_timeout(2_000)
        dataset_option = page.get_by_text(str(dataset["dataset_name"]), exact=True)
        if dataset_option.count() == 1:
            dataset_option.click()
            page.get_by_text("确 定", exact=True).click()
            page.wait_for_timeout(5_000)
        else:
            raise UsageError(
                f"Expected exactly one sandbox dataset named {dataset['dataset_name']}; "
                f"found {dataset_option.count()}."
            )
        for field in manifest.get("dimensions") or []:
            if not isinstance(field, Mapping):
                raise UsageError("Dimension entries must be objects.")
            _drag_field_to_slot(page, _field_name(field), "维度")
        for field in manifest.get("measures") or []:
            if not isinstance(field, Mapping):
                raise UsageError("Measure entries must be objects.")
            _drag_field_to_slot(page, _field_name(field), "指标")
        for field in manifest.get("local_filters") or []:
            if not isinstance(field, Mapping):
                raise UsageError("Local filter entries must be objects.")
            _drag_field_to_slot(page, _field_name(field), "筛选")
            modal = page.locator(".ant-modal-wrap:visible").last
            modal.wait_for(state="visible", timeout=10_000)
            checkboxes = modal.locator('input[type="checkbox"]')
            if checkboxes.count() < 2:
                raise UsageError("Local filter dialog did not expose a selectable value.")
            checkboxes.nth(1).check(force=True)
            modal.get_by_text("确 定", exact=True).click()
            page.wait_for_timeout(3_000)
        _write_automation_diagnostic(
            artifacts_dir=artifacts_dir,
            operation=f"{args.operation}-configured",
            page=page,
            manifest=manifest,
        )
        page.get_by_text("更 新", exact=True).click()
        page.wait_for_timeout(6_000)
        page.get_by_text("保存到草稿箱", exact=True).click()
        page.wait_for_timeout(8_000)
    _write_automation_diagnostic(
        artifacts_dir=artifacts_dir,
        operation=args.operation,
        page=page,
        manifest=manifest,
    )


def _automate_folder_dashboard_creation(page, args) -> None:
    """Create one sandbox dashboard through the visible folder UI.

    The menu identity, folder path/name and unique dashboard name have already
    passed the capture preflight and live menu snapshot.  This helper only
    replaces the formerly manual click sequence; request observation and all
    dangerous-request blocking remain owned by the caller.
    """

    if not args.expected_new_dashboard_name:
        raise UsageError(
            "Automated create_dashboard evidence requires --expected-new-dashboard-name."
        )
    search = page.get_by_placeholder("请输入报表名称")
    search.fill(args.folder_name)
    page.wait_for_timeout(1_500)
    folder = page.locator(f"#{args.folder_id}")
    folder.wait_for(state="visible", timeout=15_000)
    folder.hover()
    page.wait_for_timeout(300)
    folder.get_by_label("more").click(force=True)
    page.get_by_text("新建报表", exact=True).click()
    modal = page.locator(".ant-modal:visible")
    modal.wait_for(state="visible", timeout=10_000)
    modal.get_by_placeholder("请输入").fill(args.expected_new_dashboard_name)
    modal.get_by_text("确 定", exact=True).click()
    page.wait_for_timeout(4_000)


def _automate_confirmed_sandbox_action(page, args, manifest, artifacts_dir: Path) -> None:
    if args.scope == "folder" and args.operation == "create_dashboard":
        _automate_folder_dashboard_creation(page, args)
        return
    if args.scope == "dashboard" and args.operation in COMPONENT_PALETTE_TITLES:
        if manifest is None:
            raise UsageError(
                f"Automated {args.operation} evidence requires --sandbox-action-manifest."
            )
        _automate_dashboard_component_creation(page, args, manifest, artifacts_dir)
        return
    raise UsageError(
        f"Operator-owned sandbox UI automation is not implemented for {args.operation}."
    )

def cmd_capture_dashboard_build_evidence(args) -> int:
    if not 10 <= args.capture_seconds <= 300:
        raise UsageError("--capture-seconds must be between 10 and 300.")
    preflight_build_evidence_capture(
        operation=args.operation,
        scope=args.scope,
        domain=args.domain,
        confirmed=bool(args.confirm_sandbox_write),
        headed=bool(args.headed),
        sandbox_dashboard_id=args.sandbox_dashboard_id,
        expected_dashboard_name=args.expected_dashboard_name,
        folder_id=args.folder_id,
        folder_path=args.folder_path,
        folder_name=args.folder_name,
        sandbox_subject_id=args.sandbox_subject_id,
        sandbox_subject_name=args.sandbox_subject_name,
    )
    action_manifest = _load_sandbox_action_manifest(args)
    load_env_file(args.env_file)
    sync_playwright = import_playwright()
    ensure_runtime([args.state_path.parent, args.artifacts_dir])
    artifacts_dir = safe_artifact_dir(args.artifacts_dir)
    observations: list[dict[str, object]] = []
    blocked_requests: list[dict[str, object]] = []
    started_at = datetime.now(timezone.utc).isoformat()
    target: dict[str, object]
    created_resources: list[dict[str, object]] = []

    with sync_playwright() as playwright:
        browser, context = launch_context(
            playwright,
            args.state_path,
            True,
            args.browser_channel,
            args.executable_path,
        )
        page = context.new_page()
        try:
            if args.scope == "folder":
                ensure_authenticated(page, args, context=context)
                page.goto(DASHBOARD_MARKET_URL, wait_until="domcontentloaded", timeout=45_000)
                page.wait_for_timeout(args.wait_ms)
                before_menu = menu_folder_snapshot(
                    fetch_dashboard_menu(page),
                    folder_id=args.folder_id,
                    folder_path=args.folder_path,
                    folder_name=args.folder_name,
                )
                before_state_sha256 = str(before_menu["snapshot_sha256"])
                target = {
                    "folder_id": args.folder_id,
                    "folder_path": args.folder_path,
                    "folder_name": args.folder_name,
                    "expected_new_dashboard_name": args.expected_new_dashboard_name,
                }
            else:
                edit_url = build_edit_url(args.sandbox_dashboard_id, args.html_id)
                open_edit_page(page, args, context=context, edit_url=edit_url)
                before_raw = profile_edit_dashboard(
                    page=page,
                    dashboard_id=args.sandbox_dashboard_id,
                    html_id=args.html_id,
                    edit_url=edit_url,
                    version_id="draft",
                    artifacts_dir=artifacts_dir,
                    debug_artifacts=args.debug_artifacts,
                    include_dataset_fields=False,
                    domain=args.domain,
                )
                before = require_complete_profile(
                    before_raw, "Pre-capture P4C sandbox DashboardProfile"
                )
                if before_raw.get("dashboard_name") != args.expected_dashboard_name:
                    raise UsageError("Sandbox dashboard name mismatch.")
                if before_raw.get("config_summary", {}).get("have_edit_permission") is not True:
                    raise UsageError("Current identity has no confirmed sandbox edit permission.")
                before_state_sha256 = str(before["profile_sha256"])
                target = {
                    "dashboard_id": args.sandbox_dashboard_id,
                    "dashboard_name": args.expected_dashboard_name,
                }
                if args.operation == "create_formula":
                    target.update(
                        {
                            "sandbox_subject_id": args.sandbox_subject_id,
                            "sandbox_subject_name": args.sandbox_subject_name,
                        }
                    )

            pending_by_url: dict[str, list[dict[str, object]]] = {}

            def observe_request(request) -> None:
                if str(request.method).upper() in {"GET", "HEAD", "OPTIONS"}:
                    return
                observation = request_observation(request)
                observations.append(observation)
                pending_by_url.setdefault(str(request.url), []).append(observation)

            def observe_response(response) -> None:
                pending = pending_by_url.get(str(response.url)) or []
                if pending:
                    observation = pending[-1]
                    observation["response_status"] = int(response.status)
                    observation["response_content_type"] = response.headers.get("content-type")

            def safety_route(route) -> None:
                request = route.request
                lowered_url = str(request.url).lower()
                dangerous = is_dangerous_request(request) or any(
                    marker in lowered_url for marker in BUILD_DANGEROUS_URL_FRAGMENTS
                )
                if dangerous:
                    blocked_requests.append(request_observation(request, blocked=True))
                    route.abort("blockedbyclient")
                    return
                route.continue_()

            page.on("request", observe_request)
            page.on("response", observe_response)
            page.route("**/*", safety_route)
            print(
                f"Perform exactly one sandbox draft action for {args.operation}. "
                f"Capture closes after {args.capture_seconds} seconds. "
                "Do not publish, delete, move, create folders, or edit permissions.",
                file=sys.stderr,
                flush=True,
            )
            if bool(getattr(args, "automate_sandbox_ui", False)):
                _automate_confirmed_sandbox_action(
                    page, args, action_manifest, artifacts_dir
                )
                page.wait_for_timeout(min(args.capture_seconds, 10) * 1000)
            else:
                page.wait_for_timeout(args.capture_seconds * 1000)
            page.unroute("**/*", safety_route)
            page.remove_listener("request", observe_request)
            page.remove_listener("response", observe_response)

            if args.scope == "folder":
                after_menu = menu_folder_snapshot(
                    fetch_dashboard_menu(page),
                    folder_id=args.folder_id,
                    folder_path=args.folder_path,
                    folder_name=args.folder_name,
                )
                after_state_sha256 = str(after_menu["snapshot_sha256"])
                before_ids = {
                    str(item["dashboard_id"]): item
                    for item in before_menu.get("dashboards") or []
                }
                new_dashboards = [
                    item
                    for item in after_menu.get("dashboards") or []
                    if str(item["dashboard_id"]) not in before_ids
                ]
                if len(new_dashboards) != 1:
                    raise UsageError(
                        f"create_dashboard evidence requires exactly one new menu identity; found {len(new_dashboards)}."
                    )
                created = dict(new_dashboards[0])
                if (
                    args.expected_new_dashboard_name
                    and created.get("dashboard_name") != args.expected_new_dashboard_name
                ):
                    raise UsageError("Created sandbox dashboard name does not match the expected unique name.")
                created_resources.append(
                    {
                        "resource_type": "dashboard",
                        "resource_id": created["dashboard_id"],
                        "resource_name": created["dashboard_name"],
                    }
                )
            else:
                after_raw = profile_edit_dashboard(
                    page=page,
                    dashboard_id=args.sandbox_dashboard_id,
                    html_id=args.html_id,
                    edit_url=edit_url,
                    version_id="draft",
                    artifacts_dir=artifacts_dir,
                    debug_artifacts=args.debug_artifacts,
                    include_dataset_fields=False,
                    domain=args.domain,
                )
                after = require_complete_profile(
                    after_raw, "Post-capture P4C sandbox DashboardProfile"
                )
                after_state_sha256 = str(after["profile_sha256"])
        finally:
            browser.close()

    evidence = build_dashboard_build_evidence(
        operation=args.operation,
        domain=args.domain,
        scope=args.scope,
        target=target,
        started_at=started_at,
        before_state_sha256=before_state_sha256,
        after_state_sha256=after_state_sha256,
        observations=observations,
        blocked_requests=blocked_requests,
        created_resources=created_resources,
    )
    output_path = args.output or (
        artifacts_dir
        / "dashboard-build-evidence"
        / safe_filename(args.operation)
        / f"{safe_filename(str(target.get('dashboard_id') or target.get('folder_id') or 'sandbox'))}.json"
    )
    write_json(evidence, output_path)
    summary = {
        "ok": evidence["status"] == "evidence_captured",
        "status": evidence["status"],
        "operation": evidence["operation"],
        "scope": evidence["scope"],
        "state_changed": evidence["state_changed"],
        "observed_request_count": len(observations),
        "blocked_request_count": len(blocked_requests),
        "created_resources": created_resources,
        "evidence_sha256": evidence["evidence_sha256"],
        "registry_promoted": False,
        "output_path": str(output_path),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["ok"] else 1
