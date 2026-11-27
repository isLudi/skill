"""Registered outbound volume entrypoint."""
import os
from pathlib import Path
import sys

os.environ['PYTHONIOENCODING']='utf-8'
os.environ['PYTHONUTF8']='1'
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from lark_delivery.cli import main
from lark_delivery.common.runtime import ensure_console_streams

ensure_console_streams()
if __name__=='__main__':
    raise SystemExit(main(bound_channel="market_consultant/outbound_volume"))
