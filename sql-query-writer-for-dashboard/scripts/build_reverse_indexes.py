#!/usr/bin/env python3
"""Build market-consultant reverse indexes through the shared Text2SQL core."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORE_ROOT = ROOT.parent / "_shared" / "text2sql_core"
sys.path.insert(0, str(CORE_ROOT))

from text2sql_core.reverse_index import main_for_skill  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main_for_skill(ROOT))
