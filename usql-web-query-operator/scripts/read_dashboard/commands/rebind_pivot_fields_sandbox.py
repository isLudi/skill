"""Sandbox-only pivot field rebinding with full pre-write backups."""

from __future__ import annotations

import copy
import json
import time
from pathlib import Path
from typing import Any

from _shared.browser import import_playwright, launch_context
from _shared.env import load_env_file
from _shared.errors import UsageError
from _shared.fs_utils import ensure_runtime, safe_artifact_dir

from ..common import safe_filename, write_json
from ..constants import UNIT_VALUE_API
from ..dashboard_change import require_complete_profile
from ..dashboard_write_adapters import _write_dashboard_schema, _write_unit_detail, canonical_sha256
from ..edit_profile import (
    build_edit_url,
    fetch_edit_dashboard_config,
    fetch_edit_unit_detail,
    open_edit_page,
    profile_edit_dashboard,
)
from ..pivot_rebind import (
    FIELD_LIST_GROUPS,
    assert_filtered_value_response,
    normalize_filtered_value_checks,
    project_unit_field_state,
    rebuild_pivot_unit_fields,
)
from ..profile import (
    default_unit_value_payload,
    extract_component_units,
    fetch_dashboard_config,
    parse_dashboard_html,
    post_json,
)
SANDBOX_MARKERS = ("p4a", "sandbox", "test", "沙箱", "测试")
COPY_UNIT_API = "https://udata.baijia.com/uanalysis-intelligence/config/copy/unit"


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UsageError(f"Unable to read pivot rebind manifest: {exc}") from exc
    if not isinstance(value, dict) or value.get("artifact_type") != "DashboardPivotFieldRebindManifest":
        raise UsageError("Pivot rebind manifest has an invalid artifact_type.")
    if value.get("schema_version") != "1.0.0":
        raise UsageError("Pivot rebind manifest schema_version must be 1.0.0.")
    return value


def _require_sandbox(dashboard_id: str, expected_name: str) -> None:
    if not dashboard_id.startswith("dashboard_") or not dashboard_id.removeprefix("dashboard_").isdigit():
        raise UsageError("Sandbox dashboard ID must use dashboard_<digits>.")
    lowered_name = expected_name.casefold()
    if not any(marker in lowered_name for marker in SANDBOX_MARKERS):
        raise UsageError("Sandbox dashboard name must contain P4A, sandbox, test, 沙箱, or 测试.")


def _component_unit_ids(config: dict[str, Any]) -> list[str]:
    dashboard_html = parse_dashboard_html(config)
    unit_ids: list[str] = []
    for component in extract_component_units(dashboard_html):
        unit_id = str(component.get("unit_id") or "")
        if unit_id and unit_id not in unit_ids:
            unit_ids.append(unit_id)
    return unit_ids


def _backup_dashboard(
    *,
    page: Any,
    dashboard_id: str,
    expected_name: str | None,
    domain: str,
    artifacts_dir: Path,
    label: str,
) -> dict[str, Any]:
    edit_config = fetch_edit_dashboard_config(page, dashboard_id, "draft")
    live_name = str(edit_config.get("dashboardName") or "")
    if expected_name and live_name != expected_name:
        raise UsageError(f"Dashboard backup name mismatch for {dashboard_id}: expected {expected_name}, got {live_name}.")
    unit_details: dict[str, Any] = {}
    unit_errors: list[dict[str, str]] = []
    for unit_id in _component_unit_ids(edit_config):
        try:
            unit_details[unit_id] = fetch_edit_unit_detail(page, unit_id, dashboard_id, "draft")
        except Exception as exc:  # noqa: BLE001
            unit_errors.append({"unit_id": unit_id, "message": str(exc)})
    published_config: dict[str, Any] | None = None
    published_error: str | None = None
    try:
        published_config = fetch_dashboard_config(page, dashboard_id)
    except Exception as exc:  # noqa: BLE001
        published_error = str(exc)
    backup = {
        "schema_version": "1.0.0",
        "artifact_type": "DashboardFullConfigBackup",
        "domain": domain,
        "dashboard_id": dashboard_id,
        "dashboard_name": live_name,
        "label": label,
        "captured_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "edit_config": edit_config,
        "unit_details": unit_details,
        "unit_errors": unit_errors,
        "published_config": published_config,
        "published_error": published_error,
        "backup_sha256": "",
    }
    backup["backup_sha256"] = canonical_sha256({key: value for key, value in backup.items() if key != "backup_sha256"})
    output_path = (
        artifacts_dir
        / "dashboard-config-backups"
        / f"{safe_filename(label)}_{safe_filename(dashboard_id)}.json"
    )
    write_json(backup, output_path)
    return {
        "label": label,
        "dashboard_id": dashboard_id,
        "dashboard_name": live_name,
        "backup_sha256": backup["backup_sha256"],
        "output_path": str(output_path),
        "unit_count": len(unit_details),
        "unit_error_count": len(unit_errors),
        "published_config_captured": published_config is not None,
        "published_error": published_error,
    }


def _manifest_backups(
    manifest: dict[str, Any],
    dashboard_id: str,
    dashboard_name: str,
    *,
    target_label: str,
) -> list[dict[str, str]]:
    backups = [
        item
        for item in manifest.get("backup_dashboards") or []
        if isinstance(item, dict)
    ]
    backups.append(
        {
            "label": target_label,
            "dashboard_id": dashboard_id,
            "dashboard_name": dashboard_name,
        }
    )
    result: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for index, item in enumerate(backups):
        dashboard_id = str(item.get("dashboard_id") or "").strip()
        dashboard_name = str(item.get("dashboard_name") or "").strip()
        label = str(item.get("label") or f"backup_{index + 1}").strip()
        if not dashboard_id:
            raise UsageError("Every backup dashboard entry requires dashboard_id.")
        key = (label, dashboard_id)
        if key in seen:
            continue
        seen.add(key)
        result.append({"label": label, "dashboard_id": dashboard_id, "dashboard_name": dashboard_name})
    return result


def _operation_list(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    operations = manifest.get("operations")
    if not isinstance(operations, list) or not operations:
        raise UsageError("Pivot rebind manifest requires a non-empty operations list.")
    for operation in operations:
        if not isinstance(operation, dict):
            raise UsageError("Pivot rebind operations must be JSON objects.")
        for key in ("operation_id", "target_unit_id", "source_unit_id", "dimension_field_ids"):
            if operation.get(key) in (None, "", []):
                raise UsageError(f"Pivot rebind operation requires {key}.")
    return operations


def _source_dimension_field_ids(source_detail: dict[str, Any]) -> list[str]:
    result: list[str] = []
    for field in source_detail.get("unitDimensionList") or []:
        if not isinstance(field, dict):
            continue
        field_id = str(field.get("fieldId") or field.get("paramId") or "").strip()
        if field_id:
            result.append(field_id)
    return result


def _restore_units(
    *,
    page: Any,
    dashboard_id: str,
    dashboard_name: str,
    completed: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    restored: list[dict[str, Any]] = []
    for item in reversed(completed):
        observations: list[dict[str, Any]] = []
        _write_unit_detail(page, dashboard_id, item["before_raw"], observations)
        readback = fetch_edit_unit_detail(page, item["target_unit_id"], dashboard_id, "draft")
        restored_state = project_unit_field_state(readback)
        ok = restored_state == item["before_state"]
        restored.append(
            {
                "operation_id": item["operation_id"],
                "target_unit_id": item["target_unit_id"],
                "status": "restored" if ok else "restore_mismatch",
                "observations": observations,
            }
        )
        if not ok:
            raise UsageError(f"Recovery failed for {item['operation_id']} on {dashboard_name}.")
    return restored


def _replace_component_unit_id(schema: dict[str, Any], old_unit_id: str, new_unit_id: str) -> int:
    replacements = 0

    def walk(value: Any) -> None:
        nonlocal replacements
        if isinstance(value, dict):
            replaced_node = False
            settings = value.get("settings")
            if isinstance(settings, dict) and str(settings.get("unitId") or "") == old_unit_id:
                settings["unitId"] = new_unit_id
                replaced_node = True
            props = value.get("props")
            if isinstance(props, dict):
                prop_settings = props.get("settings")
                if isinstance(prop_settings, dict) and str(prop_settings.get("unitId") or "") == old_unit_id:
                    prop_settings["unitId"] = new_unit_id
                    replaced_node = True
            if replaced_node:
                replacements += 1
            for child in value.values():
                if isinstance(child, (dict, list)):
                    walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(schema.get("componentsTree") or [])
    return replacements


def _count_component_unit_refs(schema: dict[str, Any], unit_id: str) -> int:
    return sum(
        1
        for component in extract_component_units(schema)
        if str(component.get("unit_id") or "") == unit_id
    )


def _field_rebound_copy(
    *,
    copied_detail: dict[str, Any],
    source_detail: dict[str, Any],
    target_detail: dict[str, Any],
    operation: dict[str, Any],
) -> dict[str, Any]:
    target_field_projection = rebuild_pivot_unit_fields(
        target_detail=target_detail,
        source_detail=source_detail,
        dimension_field_ids=operation["dimension_field_ids"],
        measure_mode=str(operation.get("measure_mode") or "source_all"),
        measure_field_ids=operation.get("measure_field_ids"),
        required_measure_field_ids=operation.get("required_measure_field_ids") or [],
        preserve_target_display=operation.get("preserve_target_display", True) is not False,
    )
    rebound = copy.deepcopy(copied_detail)
    for group in FIELD_LIST_GROUPS:
        rebound[group] = copy.deepcopy(target_field_projection.get(group) or [])
    for key in ("unitName", "description", "format"):
        if key in target_detail:
            rebound[key] = copy.deepcopy(target_detail.get(key))
    return rebound


def _run_filtered_value_checks(
    *,
    page: Any,
    checks: list[dict[str, Any]],
    operation_unit_ids: dict[str, str],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for check in checks:
        unit_id = str(check.get("unit_id") or "").strip()
        operation_id = str(check.get("operation_id") or "").strip()
        if not unit_id:
            unit_id = operation_unit_ids.get(operation_id, "")
        if not unit_id:
            raise UsageError(f"{check['check_id']} could not resolve a unit_id for value/unit validation.")

        payload = default_unit_value_payload(unit_id, check.get("page_size") or 200)
        payload["publicFilterList"] = copy.deepcopy(check["public_filter_list"])
        for key, value in (check.get("payload_overrides") or {}).items():
            payload[key] = copy.deepcopy(value)

        value_payload = post_json(page, UNIT_VALUE_API, payload, timeout_ms=60_000)
        result = assert_filtered_value_response(check=check, unit_id=unit_id, value_payload=value_payload)
        result.update(
            {
                "operation_id": operation_id or None,
                "public_filter_sha256": canonical_sha256(check["public_filter_list"]),
                "required_public_filters": copy.deepcopy(check["required_public_filters"]),
            }
        )
        results.append(result)
    return results


def _execution_mode(args: Any, manifest: dict[str, Any]) -> dict[str, Any]:
    production = bool(getattr(args, "confirm_production_write", False))
    sandbox = bool(getattr(args, "confirm_sandbox_write", False))
    if production:
        raise UsageError(
            "Production pivot copy/rebind is blocked_unsupported. "
            "This command is sandbox-only and accepts only --confirm-sandbox-write."
        )
    if not sandbox:
        raise UsageError("Sandbox pivot rebind requires --confirm-sandbox-write.")

    dashboard_id = str(
        getattr(args, "dashboard_id", None)
        or getattr(args, "sandbox_dashboard_id", None)
        or manifest.get("dashboard_id")
        or ""
    ).strip()
    expected_name = str(getattr(args, "expected_dashboard_name", None) or manifest.get("dashboard_name") or "").strip()
    if not dashboard_id or not expected_name:
        raise UsageError("Pivot rebind requires dashboard id and expected dashboard name.")
    if manifest.get("dashboard_id") and str(manifest["dashboard_id"]) != dashboard_id:
        raise UsageError("Manifest dashboard_id does not match the command dashboard id.")
    if manifest.get("dashboard_name") and str(manifest["dashboard_name"]) != expected_name:
        raise UsageError("Manifest dashboard_name does not match --expected-dashboard-name.")

    _require_sandbox(dashboard_id, expected_name)
    return {
        "name": "sandbox",
        "dashboard_id": dashboard_id,
        "expected_name": expected_name,
        "target_backup_label": "sandbox_prewrite",
        "receipt_artifact_type": "DashboardPivotFieldRebindSandboxReceipt",
        "requires_allowlist": False,
    }


def cmd_rebind_pivot_fields_sandbox(args) -> int:
    manifest = _load_manifest(args.target_manifest)
    domain = str(manifest.get("domain") or "")
    if domain != args.domain:
        raise UsageError("Pivot rebind manifest domain does not match --domain.")
    mode = _execution_mode(args, manifest)
    sandbox_dashboard_id = mode["dashboard_id"]
    expected_name = mode["expected_name"]
    operations = _operation_list(manifest)
    filtered_value_checks = normalize_filtered_value_checks(
        manifest,
        operations,
        require=False,
    )

    load_env_file(args.env_file)
    sync_playwright = import_playwright()
    ensure_runtime([args.state_path.parent, args.artifacts_dir])
    artifacts_dir = safe_artifact_dir(args.artifacts_dir)
    output_path = args.output or (artifacts_dir / f"pivot-field-rebind-{mode['name']}-receipt.json")

    with sync_playwright() as playwright:
        browser, context = launch_context(
            playwright,
            args.state_path,
            args.headed,
            args.browser_channel,
            args.executable_path,
        )
        page = context.new_page()
        completed: list[dict[str, Any]] = []
        copied_unit_results: list[dict[str, Any]] = []
        filtered_value_results: list[dict[str, Any]] = []
        dashboard_schema_result: dict[str, Any] | None = None
        original_schema: dict[str, Any] | None = None
        schema_written = False
        recovery: dict[str, Any] = {"attempted": False, "status": "not_needed", "operations": [], "error": None}
        try:
            edit_url = build_edit_url(sandbox_dashboard_id)
            open_edit_page(page, args, context=context, edit_url=edit_url)
            config = fetch_edit_dashboard_config(page, sandbox_dashboard_id, "draft")
            if str(config.get("dashboardName") or "") != expected_name:
                raise UsageError("Live dashboard name does not match expected_dashboard_name.")
            if config.get("haveEditPermission") is not True:
                raise UsageError("Current identity does not have confirmed edit permission on the target dashboard.")

            backup_results = [
                _backup_dashboard(
                    page=page,
                    dashboard_id=item["dashboard_id"],
                    expected_name=item.get("dashboard_name") or None,
                    domain=domain,
                    artifacts_dir=artifacts_dir,
                    label=item["label"],
                )
                for item in _manifest_backups(
                    manifest,
                    sandbox_dashboard_id,
                    expected_name,
                    target_label=mode["target_backup_label"],
                )
            ]
            if not backup_results:
                raise UsageError("No configuration backups were written; refusing to edit dashboard.")
            if any(item["unit_error_count"] for item in backup_results):
                raise UsageError("Configuration backup had unit detail errors; refusing to edit dashboard.")

            pre_raw = profile_edit_dashboard(
                page=page,
                dashboard_id=sandbox_dashboard_id,
                html_id=str(config.get("htmlId") or "") or None,
                edit_url=edit_url,
                version_id="draft",
                artifacts_dir=artifacts_dir,
                debug_artifacts=args.debug_artifacts,
                include_dataset_fields=True,
                domain=domain,
            )
            pre_profile = require_complete_profile(pre_raw, f"Pre-rebind {mode['name']} profile")
            expected_profile = str(manifest.get("expected_profile_sha256") or "")
            if expected_profile and str(pre_profile.get("profile_sha256") or "") != expected_profile:
                raise UsageError(f"{mode['name']} profile SHA-256 does not match the manifest expected_profile_sha256.")

            operation_results: list[dict[str, Any]] = []
            original_schema = parse_dashboard_html(config)
            working_schema = copy.deepcopy(original_schema)
            for operation in operations:
                target_unit_id = str(operation["target_unit_id"])
                source_unit_id = str(operation["source_unit_id"])
                before_raw = fetch_edit_unit_detail(page, target_unit_id, sandbox_dashboard_id, "draft")
                source_raw = fetch_edit_unit_detail(page, source_unit_id, sandbox_dashboard_id, "draft")
                before_state = project_unit_field_state(before_raw)

                if operation.get("rebuild_by_copy") is True:
                    copy_response = post_json(page, COPY_UNIT_API, {"id": source_unit_id}, timeout_ms=60_000)
                    new_unit_id = str(copy_response.get("data") or "").strip()
                    if not new_unit_id.startswith("unit_"):
                        raise UsageError(f"Copy unit did not return a stable unit id: {copy_response}")
                    copied_raw = fetch_edit_unit_detail(page, new_unit_id, sandbox_dashboard_id, "draft")
                    rebuilt_raw = _field_rebound_copy(
                        copied_detail=copied_raw,
                        source_detail=source_raw,
                        target_detail=before_raw,
                        operation=operation,
                    )
                    expected_after_state = project_unit_field_state(rebuilt_raw)
                    observations: list[dict[str, Any]] = []
                    _write_unit_detail(page, sandbox_dashboard_id, rebuilt_raw, observations)
                    page.wait_for_timeout(max(0, int(getattr(args, "touch_wait_ms", 1_000))))
                    after_raw = fetch_edit_unit_detail(page, new_unit_id, sandbox_dashboard_id, "draft")
                    after_state = project_unit_field_state(after_raw)
                    if after_state != expected_after_state:
                        raise UsageError(f"Copied unit rebind readback mismatch: {operation['operation_id']}")
                    replacement_count = _replace_component_unit_id(working_schema, target_unit_id, new_unit_id)
                    if replacement_count != 1:
                        raise UsageError(
                            f"Expected exactly one component reference for {target_unit_id}, got {replacement_count}."
                        )
                    copied_unit_result = {
                        "operation_id": str(operation["operation_id"]),
                        "target_unit_id": target_unit_id,
                        "source_unit_id": source_unit_id,
                        "new_unit_id": new_unit_id,
                        "copy_status": copy_response.get("status"),
                        "replacement_count": replacement_count,
                        "after_sha256": canonical_sha256(after_state),
                        "observations": observations,
                    }
                    copied_unit_results.append(copied_unit_result)
                    operation_results.append(
                        {
                            **copied_unit_result,
                            "status": "copied_and_rebound",
                            "before_sha256": canonical_sha256(before_state),
                            "projection_changed": True,
                            "rebuild_by_copy": True,
                        }
                    )
                    continue

                recovery_registered = False

                def register_recovery() -> None:
                    nonlocal recovery_registered
                    if recovery_registered:
                        return
                    completed.append(
                        {
                            "operation_id": str(operation["operation_id"]),
                            "target_unit_id": target_unit_id,
                            "before_raw": before_raw,
                            "before_state": before_state,
                        }
                    )
                    recovery_registered = True

                observations: list[dict[str, Any]] = []
                touch_state: dict[str, Any] | None = None
                touch_projection_changed = False
                if operation.get("touch_before_final") is True:
                    touch_dimension_ids = operation.get("touch_dimension_field_ids") or _source_dimension_field_ids(source_raw)
                    touch_raw = rebuild_pivot_unit_fields(
                        target_detail=before_raw,
                        source_detail=source_raw,
                        dimension_field_ids=touch_dimension_ids,
                        measure_mode=str(operation.get("measure_mode") or "source_all"),
                        measure_field_ids=operation.get("measure_field_ids"),
                        required_measure_field_ids=operation.get("required_measure_field_ids") or [],
                        preserve_target_display=operation.get("preserve_target_display", True) is not False,
                    )
                    expected_touch_state = project_unit_field_state(touch_raw)
                    _write_unit_detail(page, sandbox_dashboard_id, touch_raw, observations)
                    register_recovery()
                    page.wait_for_timeout(max(0, int(getattr(args, "touch_wait_ms", 1_000))))
                    touch_readback = fetch_edit_unit_detail(page, target_unit_id, sandbox_dashboard_id, "draft")
                    touch_state = project_unit_field_state(touch_readback)
                    if touch_state != expected_touch_state:
                        raise UsageError(f"Unit touch readback mismatch: {operation['operation_id']}")
                    touch_projection_changed = before_state != touch_state

                rebuilt_raw = rebuild_pivot_unit_fields(
                    target_detail=before_raw,
                    source_detail=source_raw,
                    dimension_field_ids=operation["dimension_field_ids"],
                    measure_mode=str(operation.get("measure_mode") or "source_all"),
                    measure_field_ids=operation.get("measure_field_ids"),
                    required_measure_field_ids=operation.get("required_measure_field_ids") or [],
                    preserve_target_display=operation.get("preserve_target_display", True) is not False,
                )
                expected_after_state = project_unit_field_state(rebuilt_raw)
                _write_unit_detail(page, sandbox_dashboard_id, rebuilt_raw, observations)
                register_recovery()
                page.wait_for_timeout(max(0, int(getattr(args, "touch_wait_ms", 1_000))))
                after_raw = fetch_edit_unit_detail(page, target_unit_id, sandbox_dashboard_id, "draft")
                after_state = project_unit_field_state(after_raw)
                if after_state != expected_after_state:
                    _write_unit_detail(page, sandbox_dashboard_id, before_raw, observations)
                    raise UsageError(f"Unit rebind readback mismatch: {operation['operation_id']}")
                operation_results.append(
                    {
                        "operation_id": str(operation["operation_id"]),
                        "target_unit_id": target_unit_id,
                        "source_unit_id": source_unit_id,
                        "status": "saved",
                        "before_sha256": canonical_sha256(before_state),
                        "touch_sha256": canonical_sha256(touch_state) if touch_state is not None else None,
                        "after_sha256": canonical_sha256(after_state),
                        "touch_projection_changed": touch_projection_changed,
                        "projection_changed": before_state != after_state,
                        "observations": observations,
                    }
                )

            if copied_unit_results:
                schema_observations: list[dict[str, Any]] = []
                _write_dashboard_schema(page, sandbox_dashboard_id, expected_name, working_schema, schema_observations)
                schema_written = True
                latest_config = fetch_edit_dashboard_config(page, sandbox_dashboard_id, "draft")
                latest_schema = parse_dashboard_html(latest_config)
                verification = []
                for item in copied_unit_results:
                    old_count = _count_component_unit_refs(latest_schema, item["target_unit_id"])
                    new_count = _count_component_unit_refs(latest_schema, item["new_unit_id"])
                    verification.append(
                        {
                            "target_unit_id": item["target_unit_id"],
                            "new_unit_id": item["new_unit_id"],
                            "old_reference_count": old_count,
                            "new_reference_count": new_count,
                        }
                    )
                bad_verification = [
                    item for item in verification if item["old_reference_count"] != 0 or item["new_reference_count"] != 1
                ]
                if bad_verification:
                    raise UsageError(f"Dashboard schema unit reference verification failed: {bad_verification}")
                dashboard_schema_result = {
                    "status": "saved",
                    "observations": schema_observations,
                    "verification": verification,
                }

            post_raw = profile_edit_dashboard(
                page=page,
                dashboard_id=sandbox_dashboard_id,
                html_id=str(config.get("htmlId") or "") or None,
                edit_url=edit_url,
                version_id="draft",
                artifacts_dir=artifacts_dir,
                debug_artifacts=args.debug_artifacts,
                include_dataset_fields=True,
                domain=domain,
            )
            post_profile = require_complete_profile(post_raw, f"Post-rebind {mode['name']} profile")
            operation_unit_ids = {
                str(operation["operation_id"]): str(operation["target_unit_id"])
                for operation in operations
            }
            for item in copied_unit_results:
                operation_unit_ids[str(item["operation_id"])] = str(item["new_unit_id"])
            filtered_value_results = _run_filtered_value_checks(
                page=page,
                checks=filtered_value_checks,
                operation_unit_ids=operation_unit_ids,
            )
            if args.restore_after_apply:
                recovery["attempted"] = True
                if schema_written and original_schema is not None:
                    schema_recovery_observations: list[dict[str, Any]] = []
                    _write_dashboard_schema(
                        page,
                        sandbox_dashboard_id,
                        expected_name,
                        original_schema,
                        schema_recovery_observations,
                    )
                    schema_written = False
                    recovery["schema"] = {
                        "status": "restored",
                        "observations": schema_recovery_observations,
                    }
                recovery["operations"] = _restore_units(
                    page=page,
                    dashboard_id=sandbox_dashboard_id,
                    dashboard_name=expected_name,
                    completed=completed,
                )
                recovery["status"] = "restored"
        except Exception as exc:  # noqa: BLE001
            if schema_written and original_schema is not None:
                recovery["attempted"] = True
                try:
                    schema_recovery_observations = []
                    _write_dashboard_schema(
                        page,
                        sandbox_dashboard_id,
                        expected_name,
                        original_schema,
                        schema_recovery_observations,
                    )
                    schema_written = False
                    recovery["schema"] = {
                        "status": "restored",
                        "observations": schema_recovery_observations,
                    }
                    recovery["status"] = "restored"
                except Exception as recovery_exc:  # noqa: BLE001
                    recovery["schema"] = {
                        "status": "failed",
                        "error": f"{type(recovery_exc).__name__}: {recovery_exc}",
                    }
                    recovery["status"] = "failed"
            if completed:
                recovery["attempted"] = True
                try:
                    recovery["operations"] = _restore_units(
                        page=page,
                        dashboard_id=sandbox_dashboard_id,
                        dashboard_name=expected_name,
                        completed=completed,
                    )
                    recovery["status"] = "restored"
                except Exception as recovery_exc:  # noqa: BLE001
                    recovery["status"] = "failed"
                    recovery["error"] = f"{type(recovery_exc).__name__}: {recovery_exc}"
            raise UsageError(f"Pivot rebind failed: {exc}; recovery={recovery['status']}") from exc
        finally:
            browser.close()

    receipt = {
        "schema_version": "1.0.0",
        "artifact_type": mode["receipt_artifact_type"],
        "execution_mode": mode["name"],
        "domain": domain,
        "dashboard_id": sandbox_dashboard_id,
        "dashboard_name": expected_name,
        "manifest_sha256": canonical_sha256(manifest),
        "capability": mode.get("capability"),
        "pre_profile_sha256": str(pre_profile.get("profile_sha256") or ""),
        "post_profile_sha256": str(post_profile.get("profile_sha256") or ""),
        "backups": backup_results,
        "operations": operation_results,
        "copied_units": copied_unit_results,
        "filtered_value_checks": filtered_value_results,
        "dashboard_schema": dashboard_schema_result,
        "recovery": recovery,
        "status": "restored" if recovery["status"] == "restored" else "applied",
        "receipt_sha256": "",
    }
    receipt["receipt_sha256"] = canonical_sha256({key: value for key, value in receipt.items() if key != "receipt_sha256"})
    write_json(receipt, output_path)
    summary = {
        "ok": True,
        "status": receipt["status"],
        "dashboard_id": sandbox_dashboard_id,
        "dashboard_name": expected_name,
        "operation_count": len(operation_results),
        "projection_changed_count": sum(1 for item in operation_results if item.get("projection_changed")),
        "filtered_value_check_count": len(filtered_value_results),
        "pre_profile_sha256": receipt["pre_profile_sha256"],
        "post_profile_sha256": receipt["post_profile_sha256"],
        "receipt_sha256": receipt["receipt_sha256"],
        "output_path": str(output_path),
        "backup_paths": [item["output_path"] for item in backup_results],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0
