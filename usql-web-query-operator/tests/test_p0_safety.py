from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from _shared.errors import UsageError  # noqa: E402
from read_dashboard.cli import build_parser  # noqa: E402
from read_dashboard.commands.edit_public_filters import (  # noqa: E402
    cmd_edit_public_filters,
    validate_edit_mode,
)


class DashboardEditSafetyTests(unittest.TestCase):
    def test_edit_public_filters_defaults_to_dry_run_without_publish(self) -> None:
        args = build_parser().parse_args(["edit-public-filters", "--dashboard-id", "dashboard_test"])
        self.assertTrue(args.dry_run)
        self.assertFalse(args.publish)
        self.assertFalse(args.confirm_publish)
        validate_edit_mode(args)

    def test_legacy_publish_is_rejected(self) -> None:
        args = SimpleNamespace(dry_run=True, publish=True, confirm_publish=True)
        with self.assertRaisesRegex(UsageError, "Legacy edit-public-filters is read-only"):
            validate_edit_mode(args)

    def test_legacy_apply_and_publish_is_rejected(self) -> None:
        args = SimpleNamespace(dry_run=False, publish=True, confirm_publish=False)
        with self.assertRaisesRegex(UsageError, "Legacy edit-public-filters is read-only"):
            validate_edit_mode(args)

    def test_legacy_confirmed_apply_and_publish_is_rejected(self) -> None:
        args = SimpleNamespace(dry_run=False, publish=True, confirm_publish=True)
        with self.assertRaisesRegex(UsageError, "Legacy edit-public-filters is read-only"):
            validate_edit_mode(args)

    def test_legacy_write_is_rejected_before_browser_import(self) -> None:
        args = SimpleNamespace(dry_run=False, publish=False, confirm_publish=False)
        with patch(
            "read_dashboard.commands.edit_public_filters.import_playwright"
        ) as browser_import:
            with self.assertRaisesRegex(UsageError, "Legacy edit-public-filters is read-only"):
                cmd_edit_public_filters(args)
        browser_import.assert_not_called()

    def test_legacy_confirmation_without_publish_is_rejected(self) -> None:
        args = SimpleNamespace(dry_run=False, publish=False, confirm_publish=True)
        with self.assertRaisesRegex(UsageError, "Legacy edit-public-filters is read-only"):
            validate_edit_mode(args)


class EnvironmentFileConfigurationTests(unittest.TestCase):
    def test_cli_env_file_argument_overrides_default(self) -> None:
        requested = Path(os.environ.get("TEMP", ".")) / "custom-usql.env"
        args = build_parser().parse_args(["scan-folder", "--env-file", str(requested)])
        self.assertEqual(args.env_file, requested)

    def test_usql_env_file_controls_shared_default(self) -> None:
        requested = Path(os.environ.get("TEMP", ".")) / "configured-usql.env"
        env = os.environ.copy()
        env["USQL_ENV_FILE"] = str(requested)
        env["PYTHONPATH"] = str(SCRIPTS_DIR)
        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                "from _shared.config import DEFAULT_ENV_FILE; print(DEFAULT_ENV_FILE)",
            ],
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(Path(completed.stdout.strip()), requested)

    def test_blank_usql_env_file_uses_legacy_fallback(self) -> None:
        env = os.environ.copy()
        env["USQL_ENV_FILE"] = "   "
        env["PYTHONPATH"] = str(SCRIPTS_DIR)
        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                "from _shared.config import DEFAULT_ENV_FILE, LEGACY_DEFAULT_ENV_FILE; "
                "print(DEFAULT_ENV_FILE == LEGACY_DEFAULT_ENV_FILE)",
            ],
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), "True")


if __name__ == "__main__":
    unittest.main()
