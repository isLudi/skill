from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from usql_web_query.commands.check_manual_table import cmd_check_manual_table  # noqa: E402
from usql_web_query.manual_table_registry import ManualTableRegistry  # noqa: E402


class ManualTableRegistryTests(unittest.TestCase):
    def test_resolve_file_accepts_registered_alias(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            registry_path = root / "registry.json"
            registry_path.write_text(
                json.dumps(
                    {
                        "roots": {"qingcheng": str(root)},
                        "tables": [
                            {
                                "id": "qingcheng.goal",
                                "domain": "qingcheng",
                                "local_filename": "qing_goal.xlsx",
                                "local_filename_aliases": ["qing_qici_goal.xlsx"],
                                "standard_temp_table": "dingxi01_qing_goal",
                                "auto_target": True,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            registry = ManualTableRegistry.load(registry_path)

            resolved = registry.resolve_file(root / "qing_qici_goal.xlsx")

            self.assertIsNotNone(resolved)
            self.assertEqual(resolved.id, "qingcheng.goal")

    def test_check_unregistered_file_returns_skipped_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            registry_path = root / "registry.json"
            registry_path.write_text(json.dumps({"roots": {}, "tables": []}), encoding="utf-8")
            args = SimpleNamespace(
                registry_path=registry_path,
                file=[root / "unknown.xlsx"],
                strict=False,
            )
            output = io.StringIO()

            with redirect_stdout(output):
                exit_code = cmd_check_manual_table(args)

            summary = json.loads(output.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertEqual(summary["review_required_count"], 0)
            self.assertIsNone(summary["records"][0]["mapping"])
            self.assertEqual(summary["records"][0]["validation"]["status"], "skipped")


if __name__ == "__main__":
    unittest.main()
