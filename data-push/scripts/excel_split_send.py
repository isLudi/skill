"""Compatibility import/entrypoint; implementation lives in lark_delivery.workflows.excel_distribution."""
import sys
from lark_delivery.workflows import excel_distribution as _implementation

if __name__ == "__main__":
    raise SystemExit(_implementation.main())
else:
    sys.modules[__name__] = _implementation
