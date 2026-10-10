#!/usr/bin/env python
"""APP grade-9 advisor channel entry point."""
from pathlib import Path
import sys

SCRIPTS = Path(__file__).resolve().parents[2]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from lark_delivery.cli import main


if __name__ == "__main__":
    raise SystemExit(main(bound_channel="market_consultant/app_grade_9"))
