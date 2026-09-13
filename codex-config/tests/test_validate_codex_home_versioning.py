from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "validate_codex_home_versioning.py"
)
SPEC = importlib.util.spec_from_file_location("codex_home_validator", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class PortableSourceTests(unittest.TestCase):
    def test_placeholder_template_is_portable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "machine.local.example.json"
            path.write_text(
                '{"codex_home":"<ABSOLUTE_PATH_TO_CODEX_HOME>"}',
                encoding="utf-8",
            )
            self.assertEqual(VALIDATOR.scan_portable_text(path), [])

    def test_windows_absolute_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "portable.toml"
            drive_path = "C" + ":\\Users\\Example\\.codex"
            path.write_text(f'codex_home = "{drive_path}"', encoding="utf-8")
            failures = VALIDATOR.scan_portable_text(path)
            self.assertTrue(any("absolute path" in item for item in failures))


class TrackedBoundaryTests(unittest.TestCase):
    def test_runtime_and_credentials_are_rejected(self) -> None:
        tracked = [
            "portable/SKILL.md",
            "runtime/state.json",
            "nested/auth.json",
            "data/result.sqlite-wal",
        ]
        self.assertEqual(
            VALIDATOR.tracked_path_policy_violations(tracked),
            ["runtime/state.json", "nested/auth.json", "data/result.sqlite-wal"],
        )

    def test_source_files_are_allowed(self) -> None:
        tracked = [
            "data-push/scripts/lark_delivery/common/runtime.py",
            "codex-config/config.shared.toml",
            "codex-config/machine.local.example.json",
        ]
        self.assertEqual(VALIDATOR.tracked_path_policy_violations(tracked), [])


if __name__ == "__main__":
    unittest.main()
