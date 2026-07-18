"""Capture one redacted P4C request/readback evidence item in an authorized sandbox."""

from __future__ import annotations

import json
import re
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
from ..dashboard_change import canonical_sha256, require_complete_profile
from ..edit_profile import (
    build_edit_url,
    fetch_edit_dashboard_config,
    fetch_dataset_fields,
    open_edit_page,
    profile_edit_dashboard,
)
from ..menu import fetch_dashboard_menu
from ..dashboard_write_adapters import find_layout_item, _write_dashboard_schema
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
    probe_texts = ["维度", "行维度", "列维度", "指标", "筛选", "数据"]
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
    checkbox_matches: list[dict[str, Any]] = []
    checkboxes = page.locator('input[type="checkbox"]:visible')
    for index in range(min(checkboxes.count(), 30)):
        checkbox = checkboxes.nth(index)
        try:
            checkbox_matches.append(
                {
                    "checked": checkbox.is_checked(),
                    "ancestor_html": checkbox.evaluate(
                        "element => (element.closest('label')?.outerHTML || "
                        "element.parentElement?.parentElement?.outerHTML || element.outerHTML).slice(0, 5000)"
                    ),
                }
            )
        except Exception:  # noqa: BLE001 - diagnostic snapshot only
            continue
    visible_modal_html: list[str] = []
    modals = page.locator(".ant-modal-wrap:visible")
    for index in range(min(modals.count(), 5)):
        try:
            visible_modal_html.append(
                modals.nth(index).evaluate("element => element.outerHTML.slice(0, 100000)")
            )
        except Exception:  # noqa: BLE001 - diagnostic snapshot only
            continue
    action_icons: list[dict[str, Any]] = []
    icons = page.locator('[aria-label="plus-square"]:visible')
    for index in range(min(icons.count(), 20)):
        icon = icons.nth(index)
        try:
            action_icons.append(
                {
                    "ancestor_html": icon.evaluate(
                        "element => (element.parentElement?.parentElement?.parentElement?.outerHTML "
                        "|| element.outerHTML).slice(0, 10000)"
                    )
                }
            )
        except Exception:  # noqa: BLE001 - diagnostic snapshot only
            continue
    aria_controls: list[dict[str, Any]] = []
    aria_items = page.locator("[aria-label]:visible")
    for index in range(min(aria_items.count(), 100)):
        item = aria_items.nth(index)
        try:
            aria_controls.append(
                {
                    "tag": item.evaluate("element => element.tagName.toLowerCase()"),
                    "aria_label": item.get_attribute("aria-label"),
                    "class": item.get_attribute("class"),
                    "ancestor_text": item.evaluate(
                        "element => (element.closest('button')?.innerText || "
                        "element.parentElement?.parentElement?.innerText || '').slice(0, 300)"
                    ),
                }
            )
        except Exception:  # noqa: BLE001 - diagnostic snapshot only
            continue
    write_json(
        {
            "artifact_type": "DashboardBuildSandboxUiDiagnostic",
            "operation": operation,
            "logical_resource_id": manifest.get("logical_resource_id"),
            "page": _visible_control_snapshot(page),
            "frames": frames,
            "text_matches": text_matches,
            "checkbox_matches": checkbox_matches,
            "visible_modal_html": visible_modal_html,
            "action_icons": action_icons,
            "aria_controls": aria_controls,
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
    expanded_customized_group = False
    if source_text.count() == 0:
        customized_group = page.get_by_text("自定义指标", exact=True)
        if customized_group.count() == 1:
            expanded_customized_group = True
            tree_node = customized_group.locator(
                "xpath=ancestor::*[contains(@class,'ant-tree-treenode')][1]"
            )
            switcher = tree_node.locator("span.ant-tree-switcher")
            if switcher.count() == 1:
                expanded = tree_node.get_attribute("aria-expanded") == "true"
                if expanded:
                    switcher.click()
                    page.wait_for_timeout(300)
                switcher.click()
            else:
                customized_group.click()
            visible_tree_holders = page.locator("div.ant-tree-list-holder:visible")
            if visible_tree_holders.count() >= 1:
                visible_tree_holders.last.evaluate(
                    "node => { node.scrollTop = node.scrollHeight; }"
                )
            page.wait_for_timeout(1_200)
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
    if expanded_customized_group and page.get_by_text(field_name, exact=True).count() < 2:
        source.drag_to(target, force=True, timeout=10_000)
        page.wait_for_timeout(1_500)
    if expanded_customized_group and page.get_by_text(field_name, exact=True).count() < 2:
        raise UsageError(f"Custom field was not accepted by component slot: {field_name}")


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
        component_name = str(manifest.get("component_name") or "").strip()
        if component_name:
            name_inputs = page.locator('input[placeholder="请输入"]:visible')
            if name_inputs.count() < 1:
                raise UsageError("Component name input was not found.")
            name_inputs.first.fill(component_name)
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
        _write_automation_diagnostic(
            artifacts_dir=artifacts_dir,
            operation=f"{args.operation}-dataset-ready",
            page=page,
            manifest=manifest,
        )
        dimension_slot = "行维度" if args.operation == "create_pivot_component" else "维度"
        for field in manifest.get("dimensions") or []:
            if not isinstance(field, Mapping):
                raise UsageError("Dimension entries must be objects.")
            _drag_field_to_slot(page, _field_name(field), dimension_slot)
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
            _write_automation_diagnostic(
                artifacts_dir=artifacts_dir,
                operation=f"{args.operation}-local-filter-dialog",
                page=page,
                manifest=manifest,
            )
            value_nodes = modal.locator(".ant-tree-node-content-wrapper:visible")
            if value_nodes.count() < 1:
                raise UsageError("Local filter dialog did not expose a selectable value.")
            value_nodes.first.click(force=True)
            page.wait_for_timeout(1_500)
            if not re.search(r"已选\s*[1-9]\d*", modal.inner_text()):
                raise UsageError("Local filter value selection did not update the selected count.")
            modal.get_by_text("确 定", exact=True).click()
            page.wait_for_timeout(3_000)
            if page.locator(".ant-modal-wrap:visible").count() != 0:
                raise UsageError("Local filter dialog did not close after confirmation.")
        _write_automation_diagnostic(
            artifacts_dir=artifacts_dir,
            operation=f"{args.operation}-configured",
            page=page,
            manifest=manifest,
        )
        page.get_by_text("更 新", exact=True).click()
        page.wait_for_timeout(6_000)
        page.get_by_text("保存到草稿箱", exact=True).click()
        page.get_by_text("确认保存修改吗", exact=True).wait_for(
            state="visible", timeout=10_000
        )
        page.get_by_text("确 认", exact=True).click()
        page.wait_for_timeout(10_000)
    else:
        target_entries = manifest.get("target_components") or []
        targets = manifest.get("target_component_names") or []
        target_specs = (
            [item for item in target_entries if isinstance(item, Mapping) and item.get("name")]
            if target_entries
            else [{"name": str(name)} for name in targets]
        )
        if not target_specs:
            raise UsageError("Public filter action requires target_component_names.")
        for target in target_specs:
            target_name = str(target.get("name") or "")
            labels = page.get_by_text(str(target_name), exact=True).locator(
                "xpath=ancestor::label[contains(@class,'ant-checkbox-group-item')][1]"
            )
            if labels.count() == 1:
                labels.click()
                continue
            stable_ids = {
                str(target.get("component_id") or ""),
                str(target.get("unit_id") or ""),
            } - {""}
            matches = []
            candidate_values = []
            for index in range(labels.count()):
                label = labels.nth(index)
                checkbox = label.locator('input[type="checkbox"]')
                values = {
                    str(checkbox.get_attribute("value") or "") if checkbox.count() else "",
                    str(label.get_attribute("data-component-id") or ""),
                    str(label.get_attribute("data-unit-id") or ""),
                    str(label.get_attribute("data-row-key") or ""),
                } - {""}
                candidate_values.append(sorted(values))
                if stable_ids.intersection(values):
                    matches.append(label)
            if len(matches) != 1:
                raise UsageError(
                    f"Expected one public-filter target component named {target_name}; "
                    f"found {labels.count()} and stable-id matches={len(matches)}; "
                    f"candidate identifiers={candidate_values}."
                )
            matches[0].click()
        page.wait_for_timeout(4_000)
        page.get_by_text("点击设置", exact=True).click()
        page.wait_for_timeout(3_000)
        _write_automation_diagnostic(
            artifacts_dir=artifacts_dir,
            operation=f"{args.operation}-targets-selected",
            page=page,
            manifest=manifest,
        )
        modal = page.locator(".ant-modal-wrap:visible").last
        modal.wait_for(state="visible", timeout=10_000)
        combobox = modal.locator('input[role="combobox"]')
        if combobox.count() != 1:
            raise UsageError("Public filter field combobox was not found uniquely.")
        combobox.click()
        page.wait_for_timeout(2_000)
        field = manifest.get("field")
        if not isinstance(field, Mapping):
            raise UsageError("Public filter action requires one exact field object.")
        field_name = _field_name(field)
        field_options = page.get_by_text(field_name, exact=True)
        if field_options.count() < 1:
            raise UsageError(f"Public-filter field option not found: {field_name}")
        field_options.last.click()
        page.wait_for_timeout(1_500)
        modal.get_by_text("确 定", exact=True).click()
        page.wait_for_timeout(4_000)
        if page.locator(".ant-modal-wrap:visible").count() != 0:
            raise UsageError("Public filter field dialog did not close after confirmation.")
        page.get_by_text("更 新", exact=True).click()
        page.wait_for_timeout(6_000)
        page.get_by_text("保存到草稿箱", exact=True).click()
        page.get_by_text("确认保存修改吗", exact=True).wait_for(
            state="visible", timeout=10_000
        )
        page.get_by_text("确 认", exact=True).click()
        page.wait_for_timeout(10_000)
    _write_automation_diagnostic(
        artifacts_dir=artifacts_dir,
        operation=args.operation,
        page=page,
        manifest=manifest,
    )


def _automate_formula_creation(page, args, manifest, artifacts_dir: Path) -> None:
    target_component_name = str(manifest.get("target_component_name") or "").strip()
    if not target_component_name:
        raise UsageError("Formula sandbox action requires target_component_name.")
    simulator = page.frame_locator('iframe[name="undefined-SimulatorRenderer"]')
    target = simulator.get_by_text(target_component_name, exact=True)
    if target.count() != 1:
        raise UsageError(
            f"Expected one formula host component named {target_component_name}; "
            f"found {target.count()}."
        )
    target.click()
    page.wait_for_timeout(4_000)
    _write_automation_diagnostic(
        artifacts_dir=artifacts_dir,
        operation=f"{args.operation}-component-selected",
        page=page,
        manifest=manifest,
    )
    dataset_menu = page.locator('[aria-label="unordered-list"]:visible')
    if dataset_menu.count() != 1:
        raise UsageError(
            f"Expected one selected-dataset action menu; found {dataset_menu.count()}."
        )
    dataset_menu.click()
    page.get_by_text("新增计算列", exact=True).click()
    page.wait_for_timeout(3_000)
    _write_automation_diagnostic(
        artifacts_dir=artifacts_dir,
        operation=f"{args.operation}-entrypoint-opened",
        page=page,
        manifest=manifest,
    )
    formula = manifest.get("formula")
    if not isinstance(formula, Mapping):
        raise UsageError("Formula sandbox action requires a formula object.")
    formula_name = str(formula.get("name") or "").strip()
    dependencies = formula.get("dependencies") or []
    if not formula_name or len(dependencies) != 1 or not isinstance(dependencies[0], Mapping):
        raise UsageError("Formula sandbox action requires a name and exactly one dependency.")
    modal = page.locator(".ant-modal-wrap:visible").last
    modal.get_by_placeholder("计算列名称").fill(formula_name)
    type_select = modal.locator('input[role="combobox"]')
    if type_select.count() != 1:
        raise UsageError("Formula data-type selector was not found uniquely.")
    type_select.locator(
        "xpath=ancestor::div[contains(@class,'ant-select-selector')][1]"
    ).click()
    page.get_by_text("数值", exact=True).last.click()
    dependency_name = _field_name(dependencies[0])
    dependency = modal.get_by_text(dependency_name, exact=True)
    if dependency.count() != 1:
        raise UsageError(
            f"Expected one formula dependency named {dependency_name}; found {dependency.count()}."
        )
    dependency.click()
    page.wait_for_timeout(2_000)
    _write_automation_diagnostic(
        artifacts_dir=artifacts_dir,
        operation=f"{args.operation}-configured",
        page=page,
        manifest=manifest,
    )
    modal.get_by_text("确 定", exact=True).click()
    page.wait_for_timeout(8_000)
    if page.locator(".ant-modal-wrap:visible").count() != 0:
        raise UsageError("Formula dialog did not close after confirmation.")


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


def _automate_dashboard_assembly(page, args, manifest, observations) -> None:
    patch = manifest.get("layout_patch")
    if not isinstance(patch, Mapping):
        raise UsageError("assemble_new_dashboard requires one exact layout_patch object.")
    component_id = str(patch.get("component_id") or "")
    before = patch.get("before")
    after = patch.get("after")
    if not component_id or not isinstance(before, Mapping) or not isinstance(after, Mapping):
        raise UsageError("Assembly layout_patch requires component_id, before, and after.")
    layout_keys = ("x", "y", "w", "h")
    if set(before) != set(layout_keys) or set(after) != set(layout_keys):
        raise UsageError("Assembly layout before/after must contain only x, y, w, h.")
    config = fetch_edit_dashboard_config(page, args.sandbox_dashboard_id, "draft")
    if str(config.get("dashboardName") or "") != args.expected_dashboard_name:
        raise UsageError("Sandbox dashboard identity drifted before assembly evidence write.")
    try:
        schema = json.loads(str(config.get("dashboardHtmlJson") or "{}"))
    except json.JSONDecodeError as exc:
        raise UsageError("Dashboard HTML schema is not valid JSON.") from exc
    layout = find_layout_item(schema, component_id)
    current = {key: layout.get(key) for key in layout_keys}
    expected = {key: before[key] for key in layout_keys}
    if current != expected:
        raise UsageError(
            f"Assembly layout drifted before write: expected {expected}, got {current}."
        )
    target = {key: after[key] for key in layout_keys}
    for key in layout_keys:
        layout[key] = target[key]
    observation_start = len(observations)
    _write_dashboard_schema(
        page,
        args.sandbox_dashboard_id,
        args.expected_dashboard_name,
        schema,
        observations,
    )
    allowed_observation_keys = {
        "method",
        "host",
        "url_path",
        "payload_bytes",
        "request_key_paths",
        "response_status",
        "response_content_type",
        "blocked",
    }
    for index in range(observation_start, len(observations)):
        observations[index] = {
            key: value
            for key, value in observations[index].items()
            if key in allowed_observation_keys
        }
        observations[index].setdefault("blocked", False)
    page.wait_for_timeout(5_000)
    readback = fetch_edit_dashboard_config(page, args.sandbox_dashboard_id, "draft")
    readback_schema = json.loads(str(readback.get("dashboardHtmlJson") or "{}"))
    readback_layout = find_layout_item(readback_schema, component_id)
    actual = {key: readback_layout.get(key) for key in layout_keys}
    if actual != target:
        raise UsageError(
            f"Assembly layout readback mismatch: expected {target}, got {actual}."
        )


def _automate_confirmed_sandbox_action(
    page, args, manifest, artifacts_dir: Path, observations
) -> None:
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
    if args.scope == "dashboard" and args.operation == "create_formula":
        if manifest is None:
            raise UsageError("Automated create_formula evidence requires --sandbox-action-manifest.")
        _automate_formula_creation(page, args, manifest, artifacts_dir)
        return
    if args.scope == "dashboard" and args.operation == "assemble_new_dashboard":
        if manifest is None:
            raise UsageError(
                "Automated assemble_new_dashboard evidence requires --sandbox-action-manifest."
            )
        _automate_dashboard_assembly(page, args, manifest, observations)
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
                    before_subject_fields = fetch_dataset_fields(
                        page,
                        args.sandbox_dashboard_id,
                        [int(args.sandbox_subject_id)],
                        [2],
                        [],
                    )
                    before_state_sha256 = canonical_sha256(
                        {
                            "profile_sha256": before["profile_sha256"],
                            "subject_fields": before_subject_fields,
                        }
                    )
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
                    page, args, action_manifest, artifacts_dir, observations
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
                if args.operation == "create_formula":
                    after_subject_fields = fetch_dataset_fields(
                        page,
                        args.sandbox_dashboard_id,
                        [int(args.sandbox_subject_id)],
                        [2],
                        [],
                    )
                    after_state_sha256 = canonical_sha256(
                        {
                            "profile_sha256": after["profile_sha256"],
                            "subject_fields": after_subject_fields,
                        }
                    )
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
