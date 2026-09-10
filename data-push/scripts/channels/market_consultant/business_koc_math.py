"""Dedicated entrypoint for the two business-KOC math channels."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lark_delivery.cli import main


if __name__ == "__main__":
    raise SystemExit(main(bound_channel="market_consultant/business_koc_math"))
