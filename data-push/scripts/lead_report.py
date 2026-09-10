"""Compatibility import for the legacy lead aggregation interface."""
import sys
from lark_delivery.legacy import market_leads as _implementation

sys.modules[__name__] = _implementation
