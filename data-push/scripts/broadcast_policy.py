"""Compatibility import/entrypoint; implementation lives in lark_delivery.domains.market_consultant.channels.self_incubated_koc_5."""
import sys
from lark_delivery.domains.market_consultant.channels import self_incubated_koc_5 as _implementation

sys.modules[__name__] = _implementation
