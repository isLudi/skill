"""Readback-only delivery recovery, split out to keep ``scheduler`` under its size limit.

This holds the one path that can move a delivery forward *without* any ability to
send, so it is also the only path that is safe to run against a message that is
already in the group.
"""
from __future__ import annotations

import json

from ...common import resend
from .delivery_validation import receipt_readback


def reverify_unverified_delivery(db, key, cfg, context):
    """Read back one already-sent message; this function has no send capability.

    Any status that recorded a real send is eligible: ``sent`` when the process died
    between committing the receipt and attempting the readback, and the ``*unverified``
    states when the readback itself failed. ``resend.DISPATCHED_STATUSES`` is the shared
    definition of "this message is in the group".
    """
    row = db.execute("SELECT status,message_id,detail FROM deliveries WHERE key=?", (key,)).fetchone()
    if not row or row[0] not in resend.DISPATCHED_STATUSES or not row[1]:
        raise ValueError("delivery is not eligible for readback-only reverification")
    detail = json.loads(row[2])
    detail["readback"] = receipt_readback(row[1], cfg, context, detail["image_keys"])
    detail.pop("readback_error_type", None)
    updated = db.execute(
        "UPDATE deliveries SET status='sent_verified',detail=? WHERE key=? AND status=? AND message_id=?",
        (json.dumps(detail, ensure_ascii=False), key, row[0], row[1]))
    if updated.rowcount != 1:
        db.rollback()
        raise ValueError("delivery status changed during reverification")
    db.commit()
    return {"key": key, "message_id": row[1], "status": "sent_verified",
            "readback": detail["readback"]}
