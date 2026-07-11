from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from _shared.errors import UsageError  # noqa: E402
from usql_web_query.commands.sync_datamap_fields import validate_datamap_write_mode  # noqa: E402


class DataMapSyncSafetyTests(unittest.TestCase):
    def test_dry_run_does_not_require_maintenance(self) -> None:
        args = SimpleNamespace(
            write=False,
            rebuild_indexes=False,
            build_catalog=False,
            check_integrity=False,
            validate_stack=False,
        )
        validate_datamap_write_mode(args)

    def test_write_requires_complete_maintenance_stack(self) -> None:
        args = SimpleNamespace(
            write=True,
            rebuild_indexes=True,
            build_catalog=True,
            check_integrity=True,
            validate_stack=False,
        )
        with self.assertRaisesRegex(UsageError, "mandatory maintenance cannot be disabled"):
            validate_datamap_write_mode(args)

    def test_write_accepts_all_mandatory_gates(self) -> None:
        args = SimpleNamespace(
            write=True,
            rebuild_indexes=True,
            build_catalog=True,
            check_integrity=True,
            validate_stack=True,
        )
        validate_datamap_write_mode(args)


if __name__ == "__main__":
    unittest.main()
