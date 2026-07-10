from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from _shared.errors import UsageError  # noqa: E402
from read_dashboard.cli import build_parser  # noqa: E402
from read_dashboard.commands.edit_public_filters import validate_edit_mode  # noqa: E402


class DashboardEditSafetyTests(unittest.TestCase):
    def test_edit_public_filters_defaults_to_dry_run_without_publish(self) -> None:
        args = build_parser().parse_args(["edit-public-filters", "--dashboard-id", "dashboard_test"])
        self.assertTrue(args.dry_run)
        self.assertFalse(args.publish)
        self.assertFalse(args.confirm_publish)
        validate_edit_mode(args)

    def test_publish_requires_apply(self) -> None:
        args = SimpleNamespace(dry_run=True, publish=True, confirm_publish=True)
        with self.assertRaisesRegex(UsageError, "--publish requires --apply"):
            validate_edit_mode(args)

    def test_publish_requires_explicit_confirmation(self) -> None:
        args = SimpleNamespace(dry_run=False, publish=True, confirm_publish=False)
        with self.assertRaisesRegex(UsageError, "--publish requires --confirm-publish"):
            validate_edit_mode(args)

    def test_apply_and_confirmed_publish_is_allowed(self) -> None:
        args = SimpleNamespace(dry_run=False, publish=True, confirm_publish=True)
        validate_edit_mode(args)

    def test_confirmation_without_publish_is_rejected(self) -> None:
        args = SimpleNamespace(dry_run=False, publish=False, confirm_publish=True)
        with self.assertRaisesRegex(UsageError, "only valid together with --publish"):
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
