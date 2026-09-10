"""自孵化KOC-5元纯课: stable dedicated entrypoint for one channel, multiple targets."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lark_delivery.cli import main

if __name__ == "__main__":
    raise SystemExit(main(bound_channel="market_consultant/self_incubated_koc_5"))
