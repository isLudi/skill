"""Retry a precondition read that failed on the connection, not on a verdict.

On 2026-09-29 the SEC 16:20 slot wasted three rounds because the pre-send Base
revision probe hit a transport reset ("wsarecv: An existing connection was forcibly
closed by the remote host"). The probe is a *read used to decide whether a send is
still safe*: when it cannot complete, nothing at all has been learned about the data,
yet the round was marked failed and a whole 2-minute slot discarded.

The distinction that matters:

* a probe that **returns** a different revision is a verdict -- fail closed, never
  retried, because the data really did move;
* a probe that **raises** a transport error is an inability to verify -- retried
  briefly in the round, and if it still fails the error propagates so the round fails
  as before.

Retrying therefore cannot mask a real drift, because a drift is a *return value* while
only *exceptions* are retried -- and only those classified as transport. Everything
else (a rejected call, a bad argument, a genuine assertion) is re-raised on the first
attempt. The budget is deliberately small: rounds are 2 minutes apart and the round
already runs its own work, so a few seconds of backoff is cheap and a long one is not.
"""
from __future__ import annotations

import subprocess
import time
from typing import Callable, TypeVar

from .runtime import LarkTransportError

T = TypeVar("T")

ATTEMPTS = 3
DELAY_SECONDS = 2.0


def is_transport(exc: BaseException) -> bool:
    """Whether ``exc`` means "the call did not happen", not "the call said no"."""
    if isinstance(exc, (LarkTransportError, subprocess.TimeoutExpired)):
        return True
    # Belt and braces for an error raised by an intermediate layer that re-worded the
    # CLI failure without keeping the type.
    return any(marker in str(exc) for marker in (
        '"subtype": "transport"', '"type": "network"', "wsarecv", "forcibly closed",
        "Connection reset", "Connection aborted", "i/o timeout"))


def retry_transport(fn: Callable[[], T], *, attempts: int = ATTEMPTS,
                    delay: float = DELAY_SECONDS, sleep: Callable[[float], None] | None = None,
                    on_retry: Callable[[int, BaseException], None] | None = None) -> T:
    """Call ``fn``, retrying only transport failures; re-raise everything else at once."""
    # Resolved per call rather than bound as a default, so a caller (or a test) can
    # neutralise the backoff without the module freezing ``time.sleep`` at import.
    sleeper = time.sleep if sleep is None else sleep
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except BaseException as exc:  # noqa: BLE001 - re-raised below, never swallowed
            if attempt >= attempts or not is_transport(exc):
                raise
            if on_retry is not None:
                on_retry(attempt, exc)
            sleeper(delay)
    raise AssertionError("unreachable: the loop either returns or raises")
