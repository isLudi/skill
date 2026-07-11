"""Bounded retries, deadlines, and runtime-only failure caching for dashboard values."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable


@dataclass(frozen=True)
class ValueProbePolicy:
    request_timeout_ms: int = 15_000
    max_attempts: int = 2
    retry_backoff_ms: int = 500
    dashboard_timeout_ms: int = 90_000
    failure_cache_path: Path | None = None
    failure_cache_ttl_seconds: int = 900
    use_failure_cache: bool = True

    def validated(self) -> "ValueProbePolicy":
        if self.request_timeout_ms <= 0:
            raise ValueError("request_timeout_ms must be positive")
        if self.max_attempts <= 0:
            raise ValueError("max_attempts must be positive")
        if self.retry_backoff_ms < 0:
            raise ValueError("retry_backoff_ms must be non-negative")
        if self.dashboard_timeout_ms <= 0:
            raise ValueError("dashboard_timeout_ms must be positive")
        if self.failure_cache_ttl_seconds < 0:
            raise ValueError("failure_cache_ttl_seconds must be non-negative")
        return self


def policy_from_args(args: Any) -> ValueProbePolicy:
    return ValueProbePolicy(
        request_timeout_ms=int(args.value_request_timeout_ms),
        max_attempts=int(args.value_max_attempts),
        retry_backoff_ms=int(args.value_retry_backoff_ms),
        dashboard_timeout_ms=int(args.value_dashboard_timeout_ms),
        failure_cache_path=args.value_failure_cache,
        failure_cache_ttl_seconds=int(args.value_failure_cache_ttl_seconds),
        use_failure_cache=not bool(args.no_value_failure_cache),
    ).validated()


def _read_cache(path: Path | None) -> dict[str, Any]:
    if path is None or not path.is_file():
        return {"schema_version": "1.0.0", "failures": {}}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"schema_version": "1.0.0", "failures": {}}
    if not isinstance(value, dict) or not isinstance(value.get("failures"), dict):
        return {"schema_version": "1.0.0", "failures": {}}
    return value


def _write_cache(path: Path | None, cache: dict[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    temp_path.replace(path)


def _cache_key(dashboard_id: str, unit_id: str) -> str:
    return f"{dashboard_id}::{unit_id}"


def _retryable(exc: Exception) -> bool:
    text = str(exc).lower()
    return any(
        marker in text
        for marker in (
            "timeout",
            "timed out",
            "http 429",
            "http 500",
            "http 502",
            "http 503",
            "http 504",
            "connection reset",
            "network",
        )
    )


def probe_value_targets(
    *,
    dashboard_id: str,
    targets: Iterable[dict[str, Any]],
    fetch_value: Callable[[dict[str, Any], int], dict[str, Any]],
    policy: ValueProbePolicy,
    monotonic: Callable[[], float] = time.monotonic,
    wall_clock: Callable[[], float] = time.time,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    """Probe value targets without allowing one dashboard to consume unbounded time."""

    policy = policy.validated()
    target_list = list(targets)
    started = monotonic()
    deadline = started + policy.dashboard_timeout_ms / 1000
    cache = _read_cache(policy.failure_cache_path)
    failures = cache.setdefault("failures", {})
    now_epoch = wall_clock()
    ttl = policy.failure_cache_ttl_seconds
    for key, entry in list(failures.items()):
        failed_at = float(entry.get("failed_at_epoch") or 0) if isinstance(entry, dict) else 0
        if ttl == 0 or now_epoch - failed_at >= ttl:
            failures.pop(key, None)

    values: dict[str, Any] = {}
    errors: list[dict[str, Any]] = []
    cache_hits = 0
    attempted_requests = 0

    for index, target in enumerate(target_list):
        unit_id = str(target.get("unit_id") or "")
        if not unit_id:
            continue
        remaining_ms = int(max(0, (deadline - monotonic()) * 1000))
        if remaining_ms <= 0:
            for skipped in target_list[index:]:
                skipped_id = str(skipped.get("unit_id") or "")
                if not skipped_id:
                    continue
                values[skipped_id] = {"unit_id": skipped_id, "status": "not_run_dashboard_timeout"}
                errors.append(
                    {
                        "category": "dashboard_timeout",
                        "unit_id": skipped_id,
                        "attempts": 0,
                        "cached": False,
                        "message": f"Dashboard value-health deadline exceeded ({policy.dashboard_timeout_ms} ms).",
                    }
                )
            break

        key = _cache_key(dashboard_id, unit_id)
        cached = failures.get(key) if policy.use_failure_cache else None
        if isinstance(cached, dict):
            cache_hits += 1
            values[unit_id] = {
                "unit_id": unit_id,
                "status": "skipped_cached_failure",
                "cached_failure": True,
            }
            errors.append(
                {
                    "category": "cached_failure",
                    "unit_id": unit_id,
                    "attempts": 0,
                    "cached": True,
                    "message": str(cached.get("message") or "Recent value probe failure cached."),
                }
            )
            continue

        last_error: Exception | None = None
        attempts = 0
        for attempt in range(1, policy.max_attempts + 1):
            remaining_ms = int(max(0, (deadline - monotonic()) * 1000))
            if remaining_ms <= 0:
                break
            attempts = attempt
            attempted_requests += 1
            request_timeout_ms = max(1, min(policy.request_timeout_ms, remaining_ms))
            try:
                values[unit_id] = fetch_value(target, request_timeout_ms)
                failures.pop(key, None)
                last_error = None
                break
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt >= policy.max_attempts or not _retryable(exc):
                    break
                remaining_after_error = deadline - monotonic()
                if remaining_after_error <= 0:
                    break
                sleeper(min(policy.retry_backoff_ms / 1000, remaining_after_error))

        if last_error is None and unit_id in values:
            continue
        message = str(last_error or f"Dashboard value-health deadline exceeded ({policy.dashboard_timeout_ms} ms).")
        category = "dashboard_timeout" if monotonic() >= deadline else "value_probe_failed"
        values[unit_id] = {
            "unit_id": unit_id,
            "status": "probe_failed",
            "attempts": attempts,
        }
        errors.append(
            {
                "category": category,
                "unit_id": unit_id,
                "attempts": attempts,
                "cached": False,
                "message": message,
            }
        )
        if policy.use_failure_cache:
            failures[key] = {
                "failed_at_epoch": wall_clock(),
                "message": message,
                "attempts": attempts,
            }

    cache["updated_at_epoch"] = wall_clock()
    if policy.use_failure_cache:
        _write_cache(policy.failure_cache_path, cache)
    return {
        "unit_values": values,
        "errors": errors,
        "attempted_request_count": attempted_requests,
        "cache_hit_count": cache_hits,
        "elapsed_ms": int((monotonic() - started) * 1000),
        "deadline_exceeded": monotonic() >= deadline,
        "policy": {
            "request_timeout_ms": policy.request_timeout_ms,
            "max_attempts": policy.max_attempts,
            "retry_backoff_ms": policy.retry_backoff_ms,
            "dashboard_timeout_ms": policy.dashboard_timeout_ms,
            "failure_cache_ttl_seconds": policy.failure_cache_ttl_seconds,
            "failure_cache_enabled": policy.use_failure_cache,
        },
    }
