from __future__ import annotations

import sys
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import build_command_reference  # noqa: E402


class CommandReferenceTests(unittest.TestCase):
    def test_registry_exactly_covers_both_cli_parsers(self) -> None:
        registry = build_command_reference.load_registry()
        help_index = build_command_reference.validate_registry(registry)
        self.assertEqual(
            set(help_index),
            {"usql_web_query.py", "read_dashboard.py", "tiangong2_task.py"},
        )
        self.assertIn("run", help_index["usql_web_query.py"])
        run_entry = next(
            item
            for entry in registry["entrypoints"]
            if entry["entrypoint"] == "usql_web_query.py"
            for item in entry["commands"]
            if item["name"] == "run"
        )
        self.assertEqual(run_entry["parameters"]["default_engine"], "presto-lakehouse")
        self.assertIn("capture-dashboard-build-evidence", help_index["read_dashboard.py"])
        self.assertIn("verify-sandbox-dashboard-build", help_index["read_dashboard.py"])
        self.assertIn("explore", help_index["tiangong2_task.py"])

    def test_generated_reference_is_current(self) -> None:
        self.assertEqual(
            build_command_reference.OUTPUT_PATH.read_text(encoding="utf-8"),
            build_command_reference.build(),
        )


if __name__ == "__main__":
    unittest.main()
