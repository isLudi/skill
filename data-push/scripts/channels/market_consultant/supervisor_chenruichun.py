"""Pinned restored Chen Ruichun daily entrypoint."""
import os
import sys
from pathlib import Path
os.environ["PYTHONIOENCODING"]="utf-8"
os.environ["PYTHONUTF8"]="1"
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from lark_delivery.cli import main
from lark_delivery.common.runtime import ensure_console_streams
ensure_console_streams()
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

if __name__=="__main__":
    raise SystemExit(main(bound_channel="market_consultant/supervisor_chenruichun"))
