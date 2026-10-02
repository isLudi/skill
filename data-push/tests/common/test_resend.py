"""The resend verdict: which receipts may be re-driven, and which must not be.

The rule under test is one line -- a message id on record means "verify only,
never re-issue"; no message id means "re-issue with the same idempotency key".
It replaced a guard that blocked every non-``sent_verified`` receipt, which on
2026-09-29 12:20 cost a whole broadcast to a few-second transport reset.
"""

from pathlib import Path
import unittest

from lark_delivery.common import resend


class DecideTests(unittest.TestCase):
    def test_confirmed_send_is_done(self):
        self.assertEqual(resend.decide("sent_verified"), resend.DONE)
        self.assertEqual(resend.decide("sent_verified", "om_x"), resend.DONE)

    def test_unconfirmed_send_is_resent_with_the_same_key(self):
        # The 2026-09-29 12:20 SEC failure verbatim: a token-endpoint transport
        # reset left `send_result_uncertain` with no message id.
        self.assertEqual(resend.decide("send_result_uncertain"), resend.RESEND)
        self.assertEqual(resend.decide("send_result_uncertain", ""), resend.RESEND)
        self.assertEqual(resend.decide("send_result_uncertain", None), resend.RESEND)
        # Written before the send call, so it may mean the send never dispatched.
        self.assertEqual(resend.decide("send_attempt_started"), resend.RESEND)
        self.assertEqual(resend.decide("sending"), resend.RESEND)

    def test_recorded_message_id_is_never_reissued(self):
        # The one property that must hold for every status: a message already in
        # the group is only ever re-read, never re-sent.
        for status in ("sent", "sent_unverified", "sent_readback_unverified",
                       "sending", "send_attempt_started", "send_result_uncertain",
                       "sent_verified", "something_new", None):
            with self.subTest(status=status):
                self.assertNotEqual(resend.decide(status, "om_x100b"), resend.RESEND)

    def test_dispatched_status_is_verified_even_without_a_recorded_id(self):
        for status in sorted(resend.DISPATCHED_STATUSES):
            with self.subTest(status=status):
                self.assertEqual(resend.decide(status), resend.REVERIFY)

    def test_unreadable_outcome_with_an_id_is_verified(self):
        self.assertEqual(resend.decide("send_result_uncertain", "om_x100b"), resend.REVERIFY)
        self.assertEqual(resend.decide("sent_unverified", "om_x100b"), resend.REVERIFY)

    def test_unrecognised_status_does_not_block(self):
        # A guard that blocks on a status it does not understand is the defect
        # this module removes; the key makes an unconfirmed re-issue safe.
        self.assertEqual(resend.decide("some_future_status"), resend.RESEND)
        self.assertEqual(resend.decide(None), resend.RESEND)

    def test_the_old_blocking_verdict_is_gone(self):
        # `previous_attempt_requires_review` was a reader-computed status that
        # only ever meant "do nothing". It must not reappear as a decision.
        for status in ("send_result_uncertain", "send_attempt_started", "sending"):
            self.assertNotEqual(resend.decide(status), resend.DONE)


class UnreadableGroupTests(unittest.TestCase):
    """A group whose content cannot be read back at all (保密模式)."""

    def test_recorded_message_id_is_accepted_not_reissued(self):
        # The readback there fails structurally, so a recorded message id is a completed
        # delivery. Re-issuing -- especially under a new key -- would post a second copy
        # every round.
        for status in ("sent_unverified", "sent_readback_unverified", "sent",
                       "send_result_uncertain", "unknown"):
            with self.subTest(status=status):
                self.assertEqual(resend.decide(status, "om_x", readback_available=False),
                                 resend.UNVERIFIABLE)

    def test_never_confirmed_send_is_still_reissued_with_the_same_key(self):
        # Nothing is known to be in the group, so a same-key re-issue is still safe.
        self.assertEqual(resend.decide("send_result_uncertain", None, readback_available=False),
                         resend.RESEND)
        self.assertEqual(resend.decide("sending", "", readback_available=False), resend.RESEND)

    def test_verified_stays_verified(self):
        self.assertEqual(resend.decide("sent_verified", "om_x", readback_available=False), resend.DONE)

    def test_no_verdict_ever_means_a_new_key(self):
        # The whole point of the guard: a new idempotency key must never be produced for
        # an unreadable group, because "the message is missing" is a certainty there.
        allowed = {resend.DONE, resend.REVERIFY, resend.RESEND, resend.UNVERIFIABLE}
        for status in ("sent_verified", "sent_unverified", "sent_readback_unverified", "sent",
                       "send_attempt_started", "send_result_uncertain", "sending", None, "future"):
            for mid in ("om_x", "", None):
                for readable in (True, False):
                    with self.subTest(status=status, mid=mid, readable=readable):
                        self.assertIn(resend.decide(status, mid, readback_available=readable), allowed)

    def test_unverifiable_is_a_clean_status(self):
        # The task must exit 0 for such a group; otherwise every push is a false failure.
        from lark_delivery.common import push_log
        self.assertIn(resend.UNVERIFIABLE, push_log.CLEAN_STATUSES)


class PurityTests(unittest.TestCase):
    def test_policy_module_has_no_io_and_no_domain_dependency(self):
        source = Path(resend.__file__).read_text(encoding="utf-8")
        body = "\n".join(line for line in source.splitlines()
                         if line.strip().startswith(("import ", "from ")))
        for forbidden in ("domains", "legacy", "sqlite3", "pathlib", "os", "subprocess"):
            self.assertNotIn(forbidden, body,
                             f"common/resend.py must stay a pure policy module; found {forbidden}")


if __name__ == "__main__":
    unittest.main()
