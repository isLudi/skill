"""Bridge the operator to the shared QueryTrace contract without duplicating it."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from _shared.errors import UsageError


SKILLS_ROOT = Path(__file__).resolve().parents[3]
CORE_ROOT = SKILLS_ROOT / "_shared" / "text2sql_core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

from text2sql_core.trace import (  # noqa: E402
    append_trace_stage,
    bind_execution,
    bind_plan_reference,
    bind_result_artifact,
    bind_sql_sha256,
    create_query_trace,
    load_query_trace,
    write_query_trace,
)

from .query_contract import QueryPlanContract  # noqa: E402


def prepare_query_trace(
    *,
    requested_path: Path | None,
    artifacts_dir: Path,
    sql_sha256: str,
    query_plan_contract: QueryPlanContract | None,
) -> tuple[dict[str, Any], Path]:
    path = requested_path or artifacts_dir / "query_trace.json"
    try:
        trace = load_query_trace(path) if path.is_file() else create_query_trace(
            domain=query_plan_contract.domain if query_plan_contract else "unresolved",
            sql_sha256=sql_sha256,
        )
        bind_sql_sha256(trace, sql_sha256)
        if query_plan_contract:
            bind_plan_reference(
                trace,
                domain=query_plan_contract.domain,
                plan_id=query_plan_contract.plan_id,
                plan_sha256=query_plan_contract.source_sha256,
            )
        write_query_trace(path, trace)
    except ValueError as exc:
        raise UsageError(str(exc)) from exc
    return trace, path


__all__ = [
    "append_trace_stage",
    "bind_execution",
    "bind_result_artifact",
    "prepare_query_trace",
    "write_query_trace",
]
