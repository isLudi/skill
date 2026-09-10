"""Compatibility import/entrypoint; implementation lives in lark_delivery.legacy.market_group."""
import sys
from lark_delivery.legacy import market_group as _implementation

if __name__ == "__main__":
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
