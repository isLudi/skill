"""Compatibility import/entrypoint; implementation lives in lark_delivery.domains.market_consultant.scheduler."""
import sys
from lark_delivery.domains.market_consultant import scheduler as _implementation

if __name__ == "__main__":
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
