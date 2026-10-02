"""Decide whether an already-attempted send may be re-driven.

On 2026-09-29 12:20 a SEC broadcast died on a few-second transport reset while
fetching the tenant token. Its receipt became ``send_result_uncertain``, and from
then on every round read that receipt and refused -- so the 2-minute retry loop
burned its whole window without ever re-trying, and the broadcast was lost. The
retry loop exists precisely to absorb that kind of blip; it was disabled by its
own guard.

The guard was too wide. Two situations must be told apart, and one fact settles
both: every real send carries a **deterministic idempotency key** (the slot is
normalised to a fixed minute, so each round of a slot derives the same key
byte for byte, and the key is already recorded in the receipt). Re-issuing the
SAME request is therefore safe:

* **No message id on record** -- the send was never confirmed. Re-issue it with
  the same key: if the original did reach Feishu the platform dedupes and returns
  the original message instead of posting a second one. This also resolves the
  genuinely ambiguous case (response lost after dispatch): the returned message id
  makes the readback verify, so the slot converges instead of stalling.
* **A message id on record** -- the message is in the group. Never re-issue it;
  only redo the readback that failed.

An error string must never decide this. A cached tenant token can let a send
succeed while the token *refresh* fails, so "the error happened before dispatch"
does not prove the message was not delivered. Only the key settles it.

This module is pure policy: no I/O, and no import of ``domains`` or ``legacy``
(``validate_layout`` forbids ``common`` depending on either). Both departments
share the rule while keeping their own receipt machinery -- Qingcheng uses JSON
receipts, the market broadcaster a SQLite ledger.
"""
from __future__ import annotations

# The send is confirmed; there is nothing left to do.
DONE = "done"
# The message reached the group (a message id is on record); redo the readback only.
REVERIFY = "reverify"
# The send was never confirmed; re-issue it with the same idempotency key.
RESEND = "resend"
# The write was acknowledged, and this group's messages cannot be read back at all,
# so verification is impossible by policy. Accepted as terminal -- never re-issued.
UNVERIFIABLE = "sent_unverifiable"

CONFIRMED_STATUSES = frozenset({"sent_verified"})

# Receipt statuses that mean "dispatched, outcome recorded as sent". A message id
# should accompany them; if it is somehow missing we still must not re-issue,
# because these are written only after a send returned.
DISPATCHED_STATUSES = frozenset({"sent", "sent_unverified", "sent_readback_unverified"})


def decide(status: str | None, message_id: str | None = None, *,
           readback_available: bool = True) -> str:
    """Return the verdict for a receipt already on record.

    Unrecognised statuses fall through to :data:`RESEND`: the dedupe makes an
    unconfirmed re-issue safe, and a guard that blocks on a status it does not
    understand is exactly the defect this module removes.

    ``readback_available=False`` is for a group whose message content cannot be read
    back at all (see :mod:`readback`). There, a missing message id is a *structural
    certainty* rather than evidence of a lost send, so:

    * a recorded message id is accepted as :data:`UNVERIFIABLE` -- terminal, and the
      read is not retried because it cannot ever succeed;
    * an unconfirmed send is still re-issued, but only ever with the SAME key.

    **This function never returns a new-key action.** Re-issuing under a new key on a
    group like this would post a fresh copy every round, because the readback would
    report the message missing every time.
    """
    if status in CONFIRMED_STATUSES:
        return DONE
    if not readback_available:
        return UNVERIFIABLE if message_id else RESEND
    if message_id or status in DISPATCHED_STATUSES:
        return REVERIFY
    return RESEND
