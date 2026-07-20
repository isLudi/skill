"""Run reversible P4B adapters and transaction recovery in an explicit sandbox."""

from __future__ import annotations

import json
from pathlib import Path

from _shared.browser import import_playwright, launch_context
from _shared.env import load_env_file
from _shared.errors import UsageError
from _shared.fs_utils import ensure_runtime, safe_artifact_dir

from ..common import write_json
from ..dashboard_change import require_complete_profile
from ..dashboard_write_adapters import (
    ADAPTERS,
    apply_adapter_target,
    canonical_sha256,
    restore_planned_operation,
    verify_reversible_adapter,
)
from ..edit_profile import build_edit_url, fetch_edit_dashboard_config, open_edit_page, profile_edit_dashboard


OPERATION_ORDER = (
    "update_component_fields",
    "update_component_filter_label",
    "update_component_title",
    "update_filter_dynamic_default",
    "update_public_filter_title",
    "update_tab_label",
    "update_formula",
    "update_layout",
    "update_theme",
)


def _load_manifest(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UsageError(f"Unable to read sandbox adapter manifest: {exc}") from exc
    if not isinstance(value, dict) or value.get("artifact_type") != "DashboardSandboxAdapterManifest":
        raise UsageError("Sandbox adapter manifest has an invalid artifact_type.")
    if value.get("schema_version") != "1.0.0":
        raise UsageError("Sandbox adapter manifest schema_version must be 1.0.0.")
    return value


def _preflight(args, manifest: dict) -> list[str]:
    if not args.confirm_sandbox_write:
        raise UsageError("Sandbox adapter verification requires --confirm-sandbox-write.")
    if args.domain not in {"market_consultant", "qingcheng"}:
        raise UsageError("Sandbox adapter verification requires a resolved business domain.")
    if manifest.get("domain") != args.domain:
        raise UsageError("Sandbox adapter manifest domain does not match --domain.")
    if manifest.get("dashboard_id") != args.sandbox_dashboard_id:
        raise UsageError("Sandbox adapter manifest dashboard_id does not match the requested dashboard.")
    if manifest.get("dashboard_name") != args.expected_dashboard_name:
        raise UsageError("Sandbox adapter manifest dashboard_name does not match the expected live name.")
    dashboard_id = str(args.sandbox_dashboard_id)
    if not dashboard_id.startswith("dashboard_") or not dashboard_id.removeprefix("dashboard_").isdigit():
        raise UsageError("Sandbox dashboard ID must use dashboard_<digits>.")
    lowered = str(args.expected_dashboard_name).casefold()
    if not any(marker in lowered for marker in ("p4a", "sandbox", "test", "沙箱", "测试")):
        raise UsageError("Sandbox dashboard name must contain P4A, sandbox, test, 沙箱, or 测试.")
    raw_operations = manifest.get("operations")
    if not isinstance(raw_operations, dict) or not raw_operations:
        raise UsageError("Sandbox adapter manifest requires an operations object.")
    operations = [operation for operation in OPERATION_ORDER if operation in raw_operations]
    unknown = set(raw_operations) - set(ADAPTERS)
    if unknown:
        raise UsageError(f"Sandbox adapter manifest contains unknown operations: {sorted(unknown)}")
    if set(operations) != set(raw_operations):
        raise UsageError("Sandbox adapter manifest operation ordering could not be resolved.")
    expected_profile = str(manifest.get("expected_profile_sha256") or "")
    if len(expected_profile) != 64 or any(char not in "0123456789abcdef" for char in expected_profile):
        raise UsageError("Sandbox adapter manifest requires expected_profile_sha256.")
    return operations


def cmd_verify_sandbox_write_adapters(args) -> int:
    manifest = _load_manifest(args.target_manifest)
    operations = _preflight(args, manifest)
    load_env_file(args.env_file)
    sync_playwright = import_playwright()
    ensure_runtime([args.state_path.parent, args.artifacts_dir])
    artifacts_dir = safe_artifact_dir(args.artifacts_dir)
    output_path = args.output or (artifacts_dir / "p4a-sandbox-adapter-verification.json")

    with sync_playwright() as playwright:
        browser, context = launch_context(
            playwright,
            args.state_path,
            args.headed,
            args.browser_channel,
            args.executable_path,
        )
        page = context.new_page()
        try:
            edit_url = build_edit_url(args.sandbox_dashboard_id)
            open_edit_page(page, args, context=context, edit_url=edit_url)
            config = fetch_edit_dashboard_config(page, args.sandbox_dashboard_id, "draft")
            if str(config.get("dashboardName") or "") != args.expected_dashboard_name:
                raise UsageError("Live sandbox dashboard name does not match the manifest.")
            if config.get("haveEditPermission") is not True:
                raise UsageError("Current identity does not have confirmed edit permission on the sandbox dashboard.")

            results = []
            for operation in operations:
                results.append(
                    verify_reversible_adapter(
                        page=page,
                        dashboard_id=args.sandbox_dashboard_id,
                        dashboard_name=args.expected_dashboard_name,
                        operation=operation,
                        target=manifest["operations"][operation],
                    )
                )
                if results[-1]["status"] != "verified_and_restored":
                    break

            transaction = {
                "status": "not_run",
                "applied": [],
                "restored": [],
                "error": None,
            }
            if len(results) == len(operations) and all(
                item["status"] == "verified_and_restored" for item in results
            ):
                mutations = []
                try:
                    for operation in operations:
                        mutation = apply_adapter_target(
                            page=page,
                            dashboard_id=args.sandbox_dashboard_id,
                            dashboard_name=args.expected_dashboard_name,
                            operation_id=f"sandbox_tx_{operation}",
                            operation_type=operation,
                            target=manifest["operations"][operation],
                        )
                        mutations.append(mutation)
                        transaction["applied"].append(
                            {
                                "operation": operation,
                                "operation_id": mutation.operation_id,
                                "after_sha256": canonical_sha256(mutation.after_state),
                            }
                        )
                    transaction["status"] = "applied_pending_recovery"
                except Exception as exc:  # noqa: BLE001
                    transaction["error"] = f"{type(exc).__name__}: {exc}"
                finally:
                    recovery_errors = []
                    for mutation in reversed(mutations):
                        try:
                            transaction["restored"].append(
                                restore_planned_operation(
                                    page=page,
                                    dashboard_id=args.sandbox_dashboard_id,
                                    dashboard_name=args.expected_dashboard_name,
                                    mutation=mutation,
                                )
                            )
                        except Exception as exc:  # noqa: BLE001
                            recovery_errors.append(
                                f"{mutation.operation_id}: {type(exc).__name__}: {exc}"
                            )
                    if recovery_errors:
                        transaction["error"] = "; ".join(recovery_errors)
                    elif transaction["error"] is None and len(mutations) == len(operations):
                        transaction["status"] = "verified_and_restored"
                    else:
                        transaction["status"] = "failed_and_restored"

            final_raw = profile_edit_dashboard(
                page=page,
                dashboard_id=args.sandbox_dashboard_id,
                html_id=str(config.get("htmlId") or "") or None,
                edit_url=edit_url,
                version_id="draft",
                artifacts_dir=artifacts_dir,
                debug_artifacts=args.debug_artifacts,
                include_dataset_fields=True,
                domain=args.domain,
            )
            final_profile = require_complete_profile(final_raw, "Post-verification sandbox profile")
        finally:
            browser.close()

    expected_profile_sha256 = str(manifest["expected_profile_sha256"])
    final_profile_sha256 = str(final_profile.get("profile_sha256") or "")
    restored_to_baseline = final_profile_sha256 == expected_profile_sha256
    ok = (
        len(results) == len(operations)
        and all(item["status"] == "verified_and_restored" for item in results)
        and transaction["status"] == "verified_and_restored"
        and restored_to_baseline
    )
    bundle = {
        "schema_version": "1.0.0",
        "artifact_type": "DashboardSandboxAdapterVerification",
        "domain": args.domain,
        "dashboard_id": args.sandbox_dashboard_id,
        "dashboard_name": args.expected_dashboard_name,
        "manifest_sha256": canonical_sha256(manifest),
        "expected_profile_sha256": expected_profile_sha256,
        "final_profile_sha256": final_profile_sha256,
        "restored_to_baseline": restored_to_baseline,
        "status": "verified_and_restored" if ok else "failed",
        "results": results,
        "transaction": transaction,
        "verification_sha256": "",
    }
    bundle["verification_sha256"] = canonical_sha256(
        {key: value for key, value in bundle.items() if key != "verification_sha256"}
    )
    write_json(bundle, output_path)
    print(
        json.dumps(
            {
                "ok": ok,
                "status": bundle["status"],
                "operation_count": len(results),
                "operations": [item["operation"] for item in results],
                "transaction_status": transaction["status"],
                "expected_profile_sha256": expected_profile_sha256,
                "final_profile_sha256": final_profile_sha256,
                "restored_to_baseline": restored_to_baseline,
                "verification_sha256": bundle["verification_sha256"],
                "output_path": str(output_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if ok else 1
