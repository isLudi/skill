"""Compatibility import/entrypoint; implementation lives in lark_delivery.common.runtime."""
import sys
from lark_delivery.common import runtime as _implementation

sys.modules[__name__] = _implementation
