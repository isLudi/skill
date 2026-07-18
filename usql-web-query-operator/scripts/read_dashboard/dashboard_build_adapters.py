"""Production P4C adapter registry.

Entries are added only after immutable sandbox evidence, full readback tests,
and capability-registry promotion.  Keeping this registry empty is an explicit
safety state: planning and failure-injection tests remain available, while no
unverified payload can reach Taitan.
"""

from __future__ import annotations

from typing import Any, Callable

from _shared.errors import UsageError


PRODUCTION_BUILD_ADAPTER_FACTORIES: dict[str, Callable[..., Any]] = {}


def resolve_production_build_adapter(plan: dict[str, Any], *, page: Any, args: Any) -> Any:
    adapter_id = str(plan.get("production_adapter") or "")
    factory = PRODUCTION_BUILD_ADAPTER_FACTORIES.get(adapter_id)
    if factory is None:
        raise UsageError(
            "No production DashboardBuild adapter is registered for this plan. "
            "Capture and verify real sandbox request/readback evidence before promotion."
        )
    return factory(page=page, args=args)


__all__ = ["PRODUCTION_BUILD_ADAPTER_FACTORIES", "resolve_production_build_adapter"]
