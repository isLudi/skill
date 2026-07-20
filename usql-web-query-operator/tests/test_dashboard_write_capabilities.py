from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from _shared.errors import UsageError  # noqa: E402
from _shared.fs_utils import safe_artifact_dir  # noqa: E402
from read_dashboard.write_capabilities import (  # noqa: E402
    build_probe_artifact,
    load_capability_registry,
    preflight_manual_probe,
    registry_summary,
    request_key_paths,
)


class DashboardWriteCapabilityRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_capability_registry()

    def test_registry_exposes_verified_p4b_apply_operations(self) -> None:
        summary = registry_summary(self.registry)
        self.assertEqual(29, summary["capability_count"])
        self.assertEqual(
            {"allowlisted": 22, "blocked": 5, "sandbox_only": 1, "separate_confirmation": 1},
            summary["by_write_policy"],
        )
        self.assertEqual(
            [
                "assemble_new_dashboard",
                "assemble_tab_slots",
                "create_bar_component",
                "create_dashboard",
                "create_formula",
                "create_metric_group_component",
                "create_pie_component",
                "create_pivot_component",
                "create_public_filter",
                "create_tab_container",
                "create_text_component",
                "rename_new_component_metrics",
                "style_new_components",
                "update_component_fields",
                "update_component_filter_label",
                "update_component_title",
                "update_filter_dynamic_default",
                "update_formula",
                "update_layout",
                "update_public_filter_title",
                "update_tab_label",
                "update_theme",
            ],
            summary["allowlisted_operations"],
        )
        self.assertEqual(["rebuild_pivot_unit_by_copy"], summary["sandbox_only_operations"])
        self.assertEqual(["publish_dashboard"], summary["separate_confirmation_operations"])
        self.assertEqual(
            [
                "bind_dataset",
                "clone_dashboard",
                "move_dashboard_folder",
                "update_component_filter",
                "update_permissions",
            ],
            summary["blocked_operations"],
        )
        self.assertEqual(
            "creation_saga_no_auto_delete",
            next(
                item
                for item in self.registry["capabilities"]
                if item["operation"] == "create_dashboard"
            )["recovery_policy"],
        )
        self.assertEqual(
            "compensating_restore",
            next(
                item
                for item in self.registry["capabilities"]
                if item["operation"] == "update_layout"
            )["transaction_class"],
        )

    def test_manual_probe_requires_visible_confirmed_sandbox(self) -> None:
        with self.assertRaisesRegex(UsageError, "confirm-sandbox-write"):
            preflight_manual_probe(
                self.registry,
                operation="update_layout",
                dashboard_id="dashboard_123",
                expected_dashboard_name="P4A sandbox",
                domain="market_consultant",
                headed=True,
                confirmed=False,
            )
        with self.assertRaisesRegex(UsageError, "requires --headed"):
            preflight_manual_probe(
                self.registry,
                operation="update_layout",
                dashboard_id="dashboard_123",
                expected_dashboard_name="P4A sandbox",
                domain="market_consultant",
                headed=False,
                confirmed=True,
            )

    def test_publish_and_permissions_are_not_manual_probe_operations(self) -> None:
        for operation in ("publish_dashboard", "update_permissions"):
            with self.subTest(operation=operation):
                with self.assertRaisesRegex(UsageError, "not eligible"):
                    preflight_manual_probe(
                        self.registry,
                        operation=operation,
                        dashboard_id="dashboard_123",
                        expected_dashboard_name="P4A sandbox",
                        domain="market_consultant",
                        headed=True,
                        confirmed=True,
                    )

    def test_manual_probe_rejects_business_dashboard_name(self) -> None:
        with self.assertRaisesRegex(UsageError, "Sandbox dashboard name"):
            preflight_manual_probe(
                self.registry,
                operation="update_layout",
                dashboard_id="dashboard_123",
                expected_dashboard_name="市场顾问转化数据",
                domain="market_consultant",
                headed=True,
                confirmed=True,
            )

    def test_request_shape_keeps_keys_not_values(self) -> None:
        payload = {
            "dashboardId": "dashboard_secret",
            "config": {"fieldId": "user_email", "values": ["sensitive"]},
        }
        paths = request_key_paths(payload)
        self.assertIn("dashboardId", paths)
        self.assertIn("config.fieldId", paths)
        self.assertIn("config.values[]", paths)
        self.assertNotIn("dashboard_secret", paths)
        self.assertNotIn("sensitive", paths)

    def test_probe_artifact_never_promotes_registry(self) -> None:
        probe = build_probe_artifact(
            operation="update_layout",
            domain="market_consultant",
            dashboard_id="dashboard_123",
            dashboard_name="P4A sandbox",
            started_at="2026-07-11T00:00:00+00:00",
            before_profile_sha256="a" * 64,
            after_profile_sha256="b" * 64,
            observations=[
                {
                    "method": "POST",
                    "url_path": "/candidate/update",
                    "host": "example.invalid",
                    "payload_bytes": 10,
                    "request_key_paths": ["dashboardId"],
                    "response_status": 200,
                    "response_content_type": "application/json",
                    "blocked": False,
                }
            ],
            blocked_requests=[],
        )
        self.assertEqual("evidence_captured", probe["status"])
        self.assertTrue(probe["profile_changed"])
        self.assertEqual(64, len(probe["probe_sha256"]))
        self.assertNotIn("registry_promoted", probe)

    def test_artifact_directories_are_unique_within_one_second(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first = safe_artifact_dir(root)
            second = safe_artifact_dir(root)
        self.assertNotEqual(first.name, second.name)


if __name__ == "__main__":
    unittest.main()
