from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from read_dashboard.cli import build_parser  # noqa: E402
from read_dashboard.edit_batch import (  # noqa: E402
    commit_staged_profile,
    resolve_folder_domain,
    reusable_cached_profile,
)
from read_dashboard.profile import profile_dashboard  # noqa: E402
from read_dashboard.value_health import ValueProbePolicy, probe_value_targets  # noqa: E402


class DashboardConfigModeTests(unittest.TestCase):
    def test_profile_dashboard_config_mode_skips_value_api(self) -> None:
        config = {
            "dashboardName": "Config only",
            "dashboardHtmlJson": json.dumps(
                {
                    "componentsTree": [
                        {
                            "id": "node_1",
                            "componentName": "PivotTable",
                            "props": {"settings": {"unitId": "unit_1", "pageSize": 100}},
                        }
                    ]
                }
            ),
        }
        detail = {"unitId": "unit_1", "unitName": "Pivot", "unitType": "u_pivot", "format": {}}
        page = SimpleNamespace(
            url="https://example.invalid/dashboard",
            goto=Mock(),
            wait_for_timeout=Mock(),
            locator=Mock(return_value=SimpleNamespace(inner_text=Mock(return_value="Config only"))),
            title=Mock(return_value="Dashboard"),
        )
        with tempfile.TemporaryDirectory() as temp_dir, patch(
            "read_dashboard.profile.fetch_dashboard_config", return_value=config
        ), patch("read_dashboard.profile.fetch_unit_detail", return_value=detail), patch(
            "read_dashboard.profile.probe_profile_values"
        ) as value_probe:
            profile = profile_dashboard(
                page=page,
                dashboard_id="dashboard_1",
                dashboard_name=None,
                folder_name="Folder",
                wait_ms=0,
                artifacts_dir=Path(temp_dir),
                debug_artifacts=False,
                include_values=False,
            )
        value_probe.assert_not_called()
        self.assertEqual("config_only", profile["profile_mode"])
        self.assertEqual("not_run", profile["refresh_validation"]["status"])
        self.assertEqual({}, profile["unit_values"])
        self.assertTrue(profile["profile_sha256"])

    def test_cli_defaults_bulk_profiles_to_config_mode(self) -> None:
        parser = build_parser()
        self.assertEqual("config", parser.parse_args(["profile-dashboard", "--dashboard-id", "dashboard_1"]).profile_mode)
        self.assertEqual("config", parser.parse_args(["profile-folder"]).profile_mode)
        self.assertEqual("config", parser.parse_args(["profile-all"]).profile_mode)
        self.assertEqual(2, parser.parse_args(["profile-edit-all"]).max_workers)


class ValueHealthPolicyTests(unittest.TestCase):
    def test_retryable_timeout_is_retried_then_succeeds(self) -> None:
        attempts = {"count": 0}

        def fetch(_target, _timeout_ms):
            attempts["count"] += 1
            if attempts["count"] == 1:
                raise TimeoutError("request timeout")
            return {"unit_id": "unit_1", "status": "data_ready"}

        result = probe_value_targets(
            dashboard_id="dashboard_1",
            targets=[{"unit_id": "unit_1"}],
            fetch_value=fetch,
            policy=ValueProbePolicy(max_attempts=2, retry_backoff_ms=0, use_failure_cache=False),
        )
        self.assertEqual(2, result["attempted_request_count"])
        self.assertEqual([], result["errors"])
        self.assertEqual("data_ready", result["unit_values"]["unit_1"]["status"])

    def test_recent_failure_cache_skips_repeated_request(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "failures.json"
            policy = ValueProbePolicy(
                max_attempts=1,
                failure_cache_path=cache_path,
                failure_cache_ttl_seconds=3600,
            )
            first_fetch = Mock(side_effect=TimeoutError("request timeout"))
            first = probe_value_targets(
                dashboard_id="dashboard_1",
                targets=[{"unit_id": "unit_1"}],
                fetch_value=first_fetch,
                policy=policy,
            )
            second_fetch = Mock()
            second = probe_value_targets(
                dashboard_id="dashboard_1",
                targets=[{"unit_id": "unit_1"}],
                fetch_value=second_fetch,
                policy=policy,
            )
        self.assertEqual("value_probe_failed", first["errors"][0]["category"])
        second_fetch.assert_not_called()
        self.assertEqual(1, second["cache_hit_count"])
        self.assertEqual("cached_failure", second["errors"][0]["category"])


class EditBatchCacheTests(unittest.TestCase):
    def test_folder_domain_mapping_blocks_cross_domain_use(self) -> None:
        self.assertEqual("qingcheng", resolve_folder_domain("青橙播报", "auto"))
        with self.assertRaisesRegex(ValueError, "belongs to qingcheng"):
            resolve_folder_domain("青橙项目部", "market_consultant")

    def test_commit_staged_profile_preserves_unchanged_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / "target.json"
            staged = root / "staged.json"
            profile = {
                "dashboard_id": "dashboard_1",
                "domain": "qingcheng",
                "complete": True,
                "profile_sha256": "same",
            }
            target.write_text(json.dumps(profile), encoding="utf-8")
            before = target.stat().st_mtime_ns
            staged.write_text(json.dumps({**profile, "generated_at": "later"}), encoding="utf-8")
            status, committed = commit_staged_profile(staged, target)
            after = target.stat().st_mtime_ns
        self.assertEqual("unchanged", status)
        self.assertEqual("same", committed["profile_sha256"])
        self.assertEqual(before, after)

    def test_resume_cache_requires_complete_domain_bound_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "profile.json"
            path.write_text(
                json.dumps(
                    {
                        "dashboard_id": "dashboard_1",
                        "domain": "qingcheng",
                        "complete": True,
                        "profile_sha256": "hash",
                    }
                ),
                encoding="utf-8",
            )
            cached = reusable_cached_profile(
                path,
                dashboard_id="dashboard_1",
                domain="qingcheng",
                max_age_seconds=3600,
                now=path.stat().st_mtime,
            )
            wrong_domain = reusable_cached_profile(
                path,
                dashboard_id="dashboard_1",
                domain="market_consultant",
                max_age_seconds=3600,
                now=path.stat().st_mtime,
            )
        self.assertIsNotNone(cached)
        self.assertIsNone(wrong_domain)


if __name__ == "__main__":
    unittest.main()
