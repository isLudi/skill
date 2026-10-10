"""Dedicated local warning CLI with the configured department/channel identity."""
from pathlib import Path
import sys

SCRIPTS = Path(__file__).resolve().parents[2]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from lark_delivery.common.runtime import ensure_console_streams
from lark_delivery.cli import main

if __name__ == '__main__':
    ensure_console_streams()
    raise SystemExit(main(bound_channel="market_consultant/supervisor_koc_zhoushuai_warning"))
