"""Qingcheng domain wrapper for the shared Text2SQL core."""

from __future__ import annotations

import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_ROOT.parent
CORE_ROOT = REPO_ROOT / "_shared" / "text2sql_core"
sys.path.insert(0, str(CORE_ROOT))

from text2sql_core.cli import main_for_domain  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(
        main_for_domain(
            domain="qingcheng",
            skill_root=SKILL_ROOT,
            core_root=CORE_ROOT,
        )
    )

