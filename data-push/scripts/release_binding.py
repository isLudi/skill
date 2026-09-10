"""Compatibility import/entrypoint; implementation lives in lark_delivery.integrations.tiangong_release."""
import sys
from lark_delivery.integrations import tiangong_release as _implementation

sys.modules[__name__] = _implementation
