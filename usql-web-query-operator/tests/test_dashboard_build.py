from __future__ import annotations

import json
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from _shared.errors import UsageError  # noqa: E402
from read_dashboard.cli import build_parser  # noqa: E402
from read_dashboard.commands.apply_dashboard_build import cmd_apply_dashboard_build  # noqa: E402
from read_dashboard.dashboard_build import (  # noqa: E402
    bind_build_upstream_artifacts,
    execute_dashboard_build_saga,
    normalize_build_spec,
    plan_dashboard_build,
    preflight_apply_build_plan,
    preflight_publish_build,
)
from read_dashboard.dashboard_build_evidence import (  # noqa: E402
    BUILD_EVIDENCE_OPERATIONS,
    build_dashboard_build_evidence,
    menu_folder_snapshot,
    preflight_build_evidence_capture,
    verify_dashboard_build_evidence_manifest,
)
from read_dashboard.dashboard_change import canonical_sha256, normalize_profile  # noqa: E402


def raw_spec() -> dict:
    return {
        "domain": "qingcheng",
        "build_id": "sandbox_build",
        "target_folder": {
            "folder_id": "folder_test",
            "folder_path": "Root/P4C Test",
            "folder_name": "P4C Test",
        },
        "dashboard_name": "P4C Test Dashboard",
        "datasets": [
            {
                "dataset_ref": "main",
                "mode": "existing",
                "query_plan_path": "runtime/query_plan.json",
                "query_plan_sha256": "1" * 64,
                "dataset_spec_path": "runtime/dataset_spec.json",
                "dataset_spec_sha256": "2" * 64,
                "application_model_id": "model_1",
                "subject_id": "subject_1",
                "model_type": 2,
            }
        ],
        "calculated_columns": [
            {
                "logical_id": "rate",
                "dataset_ref": "main",
                "name": "Rate",
                "data_type": "decimal",
                "formula_template": "${amount}/${orders}",
                "dependencies": ["amount", "orders"],
            }
        ],
        "components": [
            {"component_id": "card", "type": "metric_group", "dataset_ref": "main", "measures": ["amount"], "layout": {"x": 0, "y": 0, "w": 6, "h": 6}},
            {"component_id": "pivot", "type": "pivot", "dataset_ref": "main", "dimensions": ["grade"], "measures": ["amount"], "local_filters": [{"field_ref": "period"}], "layout": {"x": 6, "y": 0, "w": 6, "h": 6}},
            {"component_id": "bar", "type": "bar", "dataset_ref": "main", "dimensions": ["grade"], "measures": ["amount"], "layout": {"x": 12, "y": 0, "w": 6, "h": 6}},
            {"component_id": "pie", "type": "pie", "dataset_ref": "main", "dimensions": ["grade"], "measures": ["amount"], "layout": {"x": 18, "y": 0, "w": 6, "h": 6}},
        ],
        "global_filters": [
            {"filter_id": "period", "dataset_ref": "main", "field_ref": "period", "target_component_refs": ["card", "pivot", "bar", "pie"]}
        ],
        "theme": {"background_color": "#FFFFFF"},
        "validation_checks": [
            {"check_id": "period_filtered_amount", "expected": 100}
        ],
        "publish_requested": False,
    }


def resolution() -> dict:
    bindings = [
        {"field_ref": "amount", "field_id": "f_amount", "field_group": "metric"},
        {"field_ref": "orders", "field_id": "f_orders", "field_group": "metric"},
        {"field_ref": "grade", "field_id": "f_grade", "field_group": "dimension"},
        {"field_ref": "period", "field_id": "f_period", "field_group": "dimension"},
    ]
    field_tree = json.loads(json.dumps(bindings))
    return {
        "datasets": [
            {
                "dataset_ref": "main",
                "domain": "qingcheng",
                "status": "ready",
                "query_plan_sha256": "1" * 64,
                "dataset_spec_sha256": "2" * 64,
                "query_plan_status": "executable",
                "dataset_spec_status": "ready",
                "contracts_confirmed": True,
                "source_hashes_valid": True,
                "dataset_fields_match": True,
                "application_model_id": "model_1",
                "subject_id": "subject_1",
                "model_type": 2,
                "dataset_schema_sha256": canonical_sha256(
                    sorted(field_tree, key=lambda item: item["field_id"])
                ),
                "field_binding_sha256": canonical_sha256(
                    sorted(bindings, key=lambda item: item["field_ref"])
                ),
                "field_bindings": bindings,
                "field_tree": field_tree,
            }
        ]
    }


def ready_plan() -> dict:
    return plan_dashboard_build(
        normalize_build_spec(raw_spec()),
        resolution(),
        folder_snapshot_sha256="5" * 64,
        dashboard_name_available=True,
    )


def complete_profile() -> dict:
    return normalize_profile(
        {
            "domain": "qingcheng",
            "dashboard_id": "dashboard_999",
            "dashboard_name": "P4C Test Dashboard",
            "version_id": "draft",
            "snapshot": {
                "components": [],
                "data_units": [],
                "layout": [],
                "formulas": [],
                "public_filters": [],
                "component_filters": [],
                "datasets": [],
                "theme": {},
            },
            "completeness": {
                "status": "complete",
                "required": ["components", "data_units", "layout", "formulas", "public_filters", "component_filters", "datasets", "theme"],
                "observed": ["components", "data_units", "layout", "formulas", "public_filters", "component_filters", "datasets", "theme"],
                "missing": [],
                "reasons": [],
                "details": {},
            },
        }
    )


class FakeBuildAdapter:
    def __init__(self, fail_component: str | None = None) -> None:
        self.fail_component = fail_component

    @staticmethod
    def _result(logical_id: str, resource: dict, resources: dict) -> dict:
        return {"status": "reused" if logical_id in resources else "applied", "resource": resource}

    def verify_target_folder(self, plan):
        return {
            "ok": True,
            "dashboard_name_available": True,
            "folder_snapshot_sha256": plan["folder_snapshot_sha256"],
        }

    def verify_dataset_bindings(self, plan):
        return [
            {
                "ok": True,
                **{
                    key: dataset[key]
                    for key in (
                        "dataset_ref",
                        "application_model_id",
                        "subject_id",
                        "model_type",
                        "dataset_schema_sha256",
                        "field_binding_sha256",
                    )
                },
            }
            for dataset in plan["datasets"]
        ]

    def ensure_dashboard_shell(self, plan, resources):
        return self._result("dashboard", {"logical_id": "dashboard", "resource_id": "dashboard_999", "dashboard_id": "dashboard_999", "html_id": "html_999"}, resources)

    def ensure_calculated_column(self, plan, column, resources):
        logical = f"formula:{column['logical_id']}"
        return self._result(logical, {"logical_id": logical, "resource_id": "formula_999"}, resources)

    def ensure_component(self, plan, component, resources):
        if component["component_id"] == self.fail_component:
            raise RuntimeError("injected component failure")
        logical = f"component:{component['component_id']}"
        return self._result(logical, {"logical_id": logical, "resource_id": f"unit_{component['component_id']}"}, resources)

    def ensure_global_filter(self, plan, global_filter, resources):
        logical = f"filter:{global_filter['filter_id']}"
        return self._result(logical, {"logical_id": logical, "resource_id": "public_filter_999"}, resources)

    def assemble_dashboard(self, plan, resources):
        return self._result("dashboard_html", {"logical_id": "dashboard_html", "resource_id": "html_999"}, resources)

    def read_complete_profile(self, plan, resources):
        return complete_profile()

    def verify_profile_target(self, plan, profile, resources):
        return {"ok": True, "mismatches": []}

    def check_component_values(self, plan, resources):
        return [
            {
                "component_id": item["component_id"],
                "ok": True,
                "response_shape": {
                    "metric_group": "metric_group",
                    "pivot": "pivot",
                    "bar": "chart",
                    "pie": "chart",
                }[item["type"]],
            }
            for item in plan["components"]
        ]

    def check_global_filters(self, plan, resources):
        return [
            {
                "filter_id": item["filter_id"],
                "ok": True,
                "public_filter_list_applied": True,
                "assertions_passed": True,
            }
            for item in plan["global_filters"]
        ]


class FaultInjectingBuildAdapter(FakeBuildAdapter):
    def __init__(self, fail_at: str) -> None:
        super().__init__()
        self.fail_at = fail_at

    def _raise(self, step: str) -> None:
        if self.fail_at == step:
            raise RuntimeError(f"injected {step} failure")

    def verify_target_folder(self, plan):
        self._raise("folder")
        return super().verify_target_folder(plan)

    def verify_dataset_bindings(self, plan):
        self._raise("dataset")
        return super().verify_dataset_bindings(plan)

    def ensure_dashboard_shell(self, plan, resources):
        self._raise("shell")
        return super().ensure_dashboard_shell(plan, resources)

    def ensure_calculated_column(self, plan, column, resources):
        self._raise("formula")
        return super().ensure_calculated_column(plan, column, resources)

    def ensure_component(self, plan, component, resources):
        self._raise("component")
        return super().ensure_component(plan, component, resources)

    def ensure_global_filter(self, plan, global_filter, resources):
        self._raise("filter")
        return super().ensure_global_filter(plan, global_filter, resources)

    def assemble_dashboard(self, plan, resources):
        self._raise("assemble")
        return super().assemble_dashboard(plan, resources)

    def read_complete_profile(self, plan, resources):
        self._raise("profile")
        return super().read_complete_profile(plan, resources)

    def verify_profile_target(self, plan, profile, resources):
        self._raise("target")
        return super().verify_profile_target(plan, profile, resources)

    def check_component_values(self, plan, resources):
        self._raise("value")
        return super().check_component_values(plan, resources)

    def check_global_filters(self, plan, resources):
        self._raise("global_filter_value")
        return super().check_global_filters(plan, resources)


class DashboardBuildOperatorTests(unittest.TestCase):
    def test_upstream_artifact_binding_reads_real_files_and_source_hashes(self) -> None:
        source_path = "knowledge/00_global_rules.md"
        source_file = SKILL_ROOT.parent / "qingcheng-dashboard-sql" / source_path
        source_sha256 = hashlib.sha256(source_file.read_bytes()).hexdigest()
        query_plan = {
            "schema_version": "2.0.0",
            "plan_id": "plan_p4c_test",
            "domain": "qingcheng",
            "intent": "dashboard_query",
            "status": "executable",
            "base_table": "service_dw.example",
            "metrics": [],
            "dimensions": [],
            "filters": [],
            "scopes": [],
            "joins": [],
            "calculation_grain": ["grade"],
            "output_grain": ["grade"],
            "evidence": [],
            "lineage": [],
            "unresolved_slots": [],
            "diagnostics": [],
            "execution_policy": {
                "allow_download": False,
                "max_direct_download_rows": 1000,
                "requires_preview": True,
            },
            "sql_sha256": "9" * 64,
        }
        query_plan_sha256 = canonical_sha256(query_plan)
        fields = [
            {
                "name": name,
                "role": role,
                "contract_id": f"qingcheng:test:{name}",
                "contract_status": "confirmed",
                "source_domain": "qingcheng",
                "source_path": source_path,
                "source_sha256": source_sha256,
            }
            for name, role in (
                ("amount", "measure"),
                ("orders", "measure"),
                ("grade", "dimension"),
                ("period", "dimension"),
            )
        ]
        dataset_spec = {
            "schema_version": "2.0.0",
            "artifact_type": "dashboard_dataset_spec",
            "mode": "read_only_design",
            "domain": "qingcheng",
            "plan_id": "plan_p4c_test",
            "status": "ready",
            "grain": ["grade"],
            "base_table": "service_dw.example",
            "scope_contracts": [],
            "fields": fields,
            "default_filters": [],
            "lineage": [],
            "query_plan_sha256": query_plan_sha256,
            "write_boundary": {
                "may_profile_existing_dashboard": True,
                "may_generate_diff_plan": True,
                "may_modify_dashboard": False,
                "may_publish_dashboard": False,
            },
        }
        dataset_spec["dataset_spec_sha256"] = canonical_sha256(dataset_spec)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            query_path = tmp_path / "query_plan.json"
            dataset_path = tmp_path / "dataset_spec.json"
            query_path.write_text(json.dumps(query_plan), encoding="utf-8")
            dataset_path.write_text(json.dumps(dataset_spec), encoding="utf-8")
            spec_value = raw_spec()
            spec_value["datasets"][0].update(
                {
                    "query_plan_path": str(query_path),
                    "query_plan_sha256": query_plan_sha256,
                    "dataset_spec_path": str(dataset_path),
                    "dataset_spec_sha256": dataset_spec["dataset_spec_sha256"],
                }
            )
            bound = bind_build_upstream_artifacts(
                normalize_build_spec(spec_value),
                resolution(),
            )
        resolved = bound["datasets"][0]
        self.assertEqual([], resolved["upstream_errors"])
        self.assertTrue(resolved["contracts_confirmed"])
        self.assertTrue(resolved["source_hashes_valid"])
        self.assertTrue(resolved["dataset_fields_match"])

    def test_every_creation_stage_failure_emits_non_rollback_receipt(self) -> None:
        plan = ready_plan()
        early_steps = {"folder", "dataset", "shell"}
        for step in (
            "folder",
            "dataset",
            "shell",
            "formula",
            "component",
            "filter",
            "assemble",
            "profile",
            "target",
            "value",
            "global_filter_value",
        ):
            with self.subTest(step=step):
                receipt = execute_dashboard_build_saga(
                    plan,
                    FaultInjectingBuildAdapter(step),
                )
                self.assertFalse(receipt["ok"])
                self.assertFalse(receipt["recovery"]["automatic_delete_attempted"])
                self.assertFalse(receipt["recovery"]["rolled_back"])
                self.assertEqual(step not in early_steps, receipt["manual_cleanup_required"])

    def test_cli_exposes_all_p4c_commands(self) -> None:
        parser = build_parser()
        commands = parser._subparsers._group_actions[0].choices
        for command in (
            "plan-dashboard-build",
            "apply-dashboard-build",
            "publish-dashboard-build",
            "capture-dashboard-build-evidence",
            "verify-sandbox-dashboard-build",
        ):
            self.assertIn(command, commands)

    def test_production_apply_is_blocked_by_registry_before_browser_import(self) -> None:
        plan = ready_plan()
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "plan.json"
            path.write_text(json.dumps(plan), encoding="utf-8")
            args = SimpleNamespace(
                build_plan=path,
                build_plan_sha256=plan["dashboard_build_plan_sha256"],
                domain="qingcheng",
                confirm_production_write=True,
                registry=SKILL_ROOT / "references" / "dashboard_write_capabilities.json",
                resume_receipt=None,
            )
            with patch("read_dashboard.commands.apply_dashboard_build.import_playwright") as browser_import:
                with self.assertRaisesRegex(UsageError, "not production verified/allowlisted"):
                    cmd_apply_dashboard_build(args)
                browser_import.assert_not_called()

    def test_apply_requires_exact_hash_and_confirmation(self) -> None:
        plan = ready_plan()
        with self.assertRaisesRegex(UsageError, "SHA-256 mismatch"):
            preflight_apply_build_plan(plan, "0" * 64, expected_domain="qingcheng", confirmed=True)
        with self.assertRaisesRegex(UsageError, "confirm-production-write"):
            preflight_apply_build_plan(
                plan,
                plan["dashboard_build_plan_sha256"],
                expected_domain="qingcheng",
                confirmed=False,
            )

    def test_saga_success_never_publishes(self) -> None:
        receipt = execute_dashboard_build_saga(ready_plan(), FakeBuildAdapter())
        self.assertTrue(receipt["ok"])
        self.assertEqual("applied", receipt["status"])
        self.assertFalse(receipt["publish_boundary"]["published"])
        self.assertFalse(receipt["recovery"]["automatic_delete_attempted"])
        self.assertEqual(0, len(receipt["orphaned_resources"]))

    def test_fault_injection_records_orphans_and_resume_reuses_exact_resources(self) -> None:
        plan = ready_plan()
        failed = execute_dashboard_build_saga(plan, FakeBuildAdapter(fail_component="bar"))
        self.assertFalse(failed["ok"])
        self.assertTrue(failed["manual_cleanup_required"])
        self.assertGreater(len(failed["orphaned_resources"]), 0)
        resumed = execute_dashboard_build_saga(plan, FakeBuildAdapter(), resume_receipt=failed)
        self.assertTrue(resumed["ok"])
        self.assertGreater(len(resumed["reused_resources"]), 0)

    def test_publish_preflight_requires_successful_receipt_and_separate_confirmation(self) -> None:
        plan = ready_plan()
        receipt = execute_dashboard_build_saga(plan, FakeBuildAdapter())
        with self.assertRaisesRegex(UsageError, "confirm-publish"):
            preflight_publish_build(
                plan,
                plan["dashboard_build_plan_sha256"],
                receipt,
                receipt["dashboard_build_receipt_sha256"],
                expected_domain="qingcheng",
                confirmed=False,
                version_description="approved",
            )
        tampered = dict(receipt)
        tampered["status"] = "failed"
        with self.assertRaisesRegex(UsageError, "SHA-256 mismatch"):
            preflight_publish_build(
                plan,
                plan["dashboard_build_plan_sha256"],
                tampered,
                receipt["dashboard_build_receipt_sha256"],
                expected_domain="qingcheng",
                confirmed=True,
                version_description="approved",
            )

    def test_evidence_capture_is_limited_to_authorized_sandbox(self) -> None:
        with self.assertRaisesRegex(UsageError, "marked as test/sandbox"):
            preflight_build_evidence_capture(
                operation="create_formula",
                scope="dashboard",
                domain="qingcheng",
                confirmed=True,
                headed=True,
                sandbox_dashboard_id="dashboard_1",
                expected_dashboard_name="Production Dashboard",
                folder_id=None,
                folder_path=None,
                folder_name=None,
                sandbox_subject_id="subject_test",
                sandbox_subject_name="P4C Test Subject",
            )
        preflight_build_evidence_capture(
            operation="create_dashboard",
            scope="folder",
            domain="qingcheng",
            confirmed=True,
            headed=True,
            sandbox_dashboard_id=None,
            expected_dashboard_name=None,
            folder_id="folder_1",
            folder_path="Root/P4C Test",
            folder_name="P4C Test",
        )

    def test_menu_snapshot_and_evidence_keep_only_redacted_request_shape(self) -> None:
        menu = {
            "data": [
                {
                    "id": "root",
                    "name": "Root",
                    "children": [
                        {
                            "id": "folder_1",
                            "name": "P4C Test",
                            "children": [{"id": "dashboard_1", "name": "Existing"}],
                        }
                    ],
                }
            ]
        }
        snapshot = menu_folder_snapshot(
            menu,
            folder_id="folder_1",
            folder_path="Root/P4C Test",
            folder_name="P4C Test",
        )
        self.assertEqual("dashboard_1", snapshot["dashboards"][0]["dashboard_id"])
        evidence = build_dashboard_build_evidence(
            operation="create_dashboard",
            domain="qingcheng",
            scope="folder",
            target={"folder_id": "folder_1"},
            started_at="2026-07-18T00:00:00+00:00",
            before_state_sha256="a" * 64,
            after_state_sha256="b" * 64,
            observations=[
                {
                    "method": "POST",
                    "url_path": "/create",
                    "host": "example.invalid",
                    "payload_bytes": 100,
                    "request_key_paths": ["name", "parentId"],
                    "response_status": 200,
                    "response_content_type": "application/json",
                    "blocked": False,
                }
            ],
            blocked_requests=[],
            created_resources=[{"resource_id": "dashboard_2"}],
        )
        self.assertEqual("evidence_captured", evidence["status"])
        serialized = json.dumps(evidence)
        self.assertNotIn("cookie", serialized.lower())
        self.assertFalse(evidence["registry_promoted"])

    def test_evidence_manifest_binds_one_selected_successful_request_per_operation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entries = []
            for index, operation in enumerate(sorted(BUILD_EVIDENCE_OPERATIONS)):
                evidence = build_dashboard_build_evidence(
                    operation=operation,
                    domain="qingcheng",
                    scope="folder" if operation == "create_dashboard" else "dashboard",
                    target={"resource_id": f"sandbox_{index}"},
                    started_at="2026-07-18T00:00:00+00:00",
                    before_state_sha256=f"{index + 1:064x}",
                    after_state_sha256=f"{index + 101:064x}",
                    observations=[
                        {
                            "method": "POST",
                            "url_path": f"/candidate/{operation}",
                            "host": "example.invalid",
                            "payload_bytes": 10,
                            "request_key_paths": ["id"],
                            "response_status": 200,
                            "response_content_type": "application/json",
                            "blocked": False,
                        }
                    ],
                    blocked_requests=[],
                    created_resources=[],
                )
                path = Path(tmp) / f"{operation}.json"
                path.write_text(json.dumps(evidence), encoding="utf-8")
                entries.append(
                    {
                        "operation": operation,
                        "path": str(path),
                        "evidence_sha256": evidence["evidence_sha256"],
                        "selected_observation_sha256": evidence["observations"][0][
                            "observation_sha256"
                        ],
                    }
                )
            manifest = {
                "artifact_type": "DashboardBuildEvidenceManifest",
                "evidence": entries,
            }
            verification = verify_dashboard_build_evidence_manifest(manifest)
            self.assertTrue(verification["ok"])
            manifest["evidence"][0]["selected_observation_sha256"] = "0" * 64
            self.assertFalse(verify_dashboard_build_evidence_manifest(manifest)["ok"])


if __name__ == "__main__":
    unittest.main()
