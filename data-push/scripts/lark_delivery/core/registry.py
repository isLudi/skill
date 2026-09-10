"""Only explicitly paired department/adapter combinations can execute."""


def adapter_for(definition):
    key = (definition["domain"], definition["adapter"])
    if key == ("market_consultant", "market-grade-manager-v1"):
        from ..domains.market_consultant import adapter
        adapter.validate_definition(definition)
        return adapter
    raise ValueError(f"No reviewed adapter for {key}; do not borrow another department's rules")
