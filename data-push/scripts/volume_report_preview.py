"""Compatibility entrypoint for the read-only KOC volume preview."""
from lark_delivery.domains.market_consultant.volume_report import main


if __name__ == "__main__":
    raise SystemExit(main())
