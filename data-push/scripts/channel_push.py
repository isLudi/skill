"""Generic registered-channel command; prefers a dedicated channel entrypoint."""
from lark_delivery.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
