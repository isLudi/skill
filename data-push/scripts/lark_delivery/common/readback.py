"""Whether a target group's messages can be read back at all.

On 2026-09-29 the qingcheng Process task's `private` / supervisor group (⏰私域讨论)
reported `readback_failed` on a broadcast that had in fact been delivered. The group
had 保密模式 (restricted mode) enabled:

    "restricted_mode_setting": {"download_has_permission_setting": "not_anyone",
                                "message_has_permission_setting": "not_anyone",
                                "screenshot_has_permission_setting": "not_anyone",
                                "status": true}

Sending is a write and stays allowed; reading message *content* does not. So
`chat-messages-list` and `messages-mget` return nothing, and the recorded message id
does not resolve -- through the bot identity or a user identity alike. Absence of read
access is indistinguishable from absence of the message.

That produced two distinct hazards, and this module exists to prevent both:

1. **A permanent false failure.** The channel reports `readback_failed` and the task
   exits non-zero on *every* push, for as long as the mode is on, while the group is
   actually receiving every report.
2. **A duplicate.** "The message id does not resolve" is a structural certainty here,
   so any rule that escalates to a *new* idempotency key when a message looks missing
   would post another copy on every retry round -- up to ~13 per slot. On 2026-09-29 a
   single manual new-key attempt did exactly that, and that is why
   :func:`resend.decide` only ever offers a same-key re-issue.

Resolution order:

* the channel profile's explicit ``readback_unavailable`` declaration wins;
* otherwise the API is probed once per process, cached, and only on a readback-failure
  path (the caller decides when to ask), so the happy path pays no extra call;
* every error -- unreadable config, transport reset, unexpected payload -- resolves to
  ``True``. This must never silently accept a real delivery failure, so the safe
  direction is always "assume the readback would have worked".
"""
from __future__ import annotations

import json
from typing import Any, Mapping

from .runtime import run_lark

DECLARED_KEY = "readback_unavailable"
# A group whose content may not be read by anyone: restricted mode's own switch, or
# the specific permission that governs message content.
RESTRICTED_PERMISSION = "not_anyone"

_probe_cache: dict[str, bool] = {}


def declared(profile: Mapping[str, Any] | None) -> bool | None:
    """``True``/``False`` when the profile states it; ``None`` when it stays silent."""
    if not isinstance(profile, Mapping) or DECLARED_KEY not in profile:
        return None
    return bool(profile[DECLARED_KEY])


def restricted(chat_id: str) -> bool:
    """Probe whether the group's content is unreadable. Cached; errors mean "no"."""
    if chat_id in _probe_cache:
        return _probe_cache[chat_id]
    result = False
    try:
        payload = json.loads(run_lark(["im", "chats", "get", "--chat-id", chat_id,
                                       "--format", "json"], timeout=45))
        data = payload.get("data") or {}
        setting = data.get("restricted_mode_setting") or {}
        result = (setting.get("status") is True
                  or setting.get("message_has_permission_setting") == RESTRICTED_PERMISSION)
    except Exception:
        result = False
    _probe_cache[chat_id] = result
    return result


def available(profile: Mapping[str, Any] | None, chat_id: str | None) -> bool:
    """Whether a readback of this target could verify a message.

    ``False`` means the group's content is unreadable, so a readback failure carries
    no information and must not be reported as a delivery failure.
    """
    stated = declared(profile)
    if stated is not None:
        return not stated
    if not chat_id:
        return True
    return not restricted(chat_id)


def reset_cache() -> None:
    """Drop the probe cache; for tests and for callers that outlive a group change."""
    _probe_cache.clear()
