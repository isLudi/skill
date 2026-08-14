from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from _shared.config import DEFAULT_STATE, DEFAULT_TIANGONG2_TASK_STATE, TIANGONG2_TASK_RUNTIME_DIR
from _shared.env import read_env_section
from _shared.errors import UsageError
from tiangong2_task.session import identity_matches_username, validate_runtime_state_path


class Tiangong2EnvironmentTests(unittest.TestCase):
    def test_exact_duplicate_key_section_is_selected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "usql_api.env"
            path.write_text(
                "# USQL Web Query (Playwright) credentials\n"
                "BAIJIA_USERNAME=usql-user\n"
                "BAIJIA_PASSWORD=usql-pass\n"
                "# tiangong2 Web Query (Playwright) credentials\n"
                "BAIJIA_USERNAME=tiangong-user\n"
                "BAIJIA_PASSWORD=tiangong-pass\n",
                encoding="utf-8",
            )
            values = read_env_section(path, "tiangong2 Web Query (Playwright) credentials")
        self.assertEqual(values["BAIJIA_USERNAME"], "tiangong-user")
        self.assertEqual(values["BAIJIA_PASSWORD"], "tiangong-pass")

    def test_duplicate_key_inside_one_section_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "usql_api.env"
            path.write_text(
                "# target\nBAIJIA_USERNAME=one\nBAIJIA_USERNAME=two\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "Duplicate key"):
                read_env_section(path, "target")


class Tiangong2SessionSafetyTests(unittest.TestCase):
    def test_state_is_distinct_from_usql_state(self) -> None:
        self.assertNotEqual(DEFAULT_TIANGONG2_TASK_STATE, DEFAULT_STATE)
        self.assertEqual(DEFAULT_TIANGONG2_TASK_STATE.parent, TIANGONG2_TASK_RUNTIME_DIR)

    def test_state_outside_isolated_runtime_is_rejected(self) -> None:
        with self.assertRaisesRegex(UsageError, "isolated runtime"):
            validate_runtime_state_path(DEFAULT_STATE)

    def test_scoped_identity_must_match_username(self) -> None:
        self.assertTrue(identity_matches_username({"name": "reader01"}, "reader01"))
        self.assertTrue(identity_matches_username({"name": "reader01"}, "reader01@example.com"))
        self.assertFalse(identity_matches_username({"name": "other"}, "reader01"))


if __name__ == "__main__":
    unittest.main()
