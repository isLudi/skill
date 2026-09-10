"""Compatibility import/entrypoint; implementation lives in lark_delivery.domains.market_consultant.grade_report."""
import sys
from lark_delivery.domains.market_consultant import grade_report as _implementation

sys.modules[__name__] = _implementation
