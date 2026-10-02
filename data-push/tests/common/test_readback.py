"""Whether a group's content can be read back, and the safe direction when unsure.

A group with 保密模式 (restricted mode) cannot have its message content read through the
API, while sending stays allowed. On 2026-09-29 that made a delivered broadcast report
`readback_failed` forever and led a manual new-key retry to post a duplicate.
"""

import unittest
from unittest.mock import patch

from lark_delivery.common import readback


class DeclaredTests(unittest.TestCase):
    def test_declaration_is_authoritative_both_ways(self):
        self.assertFalse(readback.available({"readback_unavailable": True}, "oc_x"))
        self.assertTrue(readback.available({"readback_unavailable": False}, "oc_x"))
        self.assertIsNone(readback.declared({}))
        self.assertIsNone(readback.declared(None))

    def test_declaration_short_circuits_the_probe(self):
        with patch.object(readback, "restricted") as probe:
            self.assertFalse(readback.available({"readback_unavailable": True}, "oc_x"))
            probe.assert_not_called()


class ProbeTests(unittest.TestCase):
    def setUp(self):
        readback.reset_cache()

    def _probe(self, payload):
        with patch.object(readback, "run_lark", return_value=payload):
            return readback.restricted("oc_x")

    def test_restricted_mode_status_makes_content_unreadable(self):
        self.assertTrue(self._probe(
            '{"data": {"restricted_mode_setting": {"status": true,'
            ' "message_has_permission_setting": "not_anyone"}}}'))

    def test_message_permission_alone_is_enough(self):
        self.assertTrue(self._probe(
            '{"data": {"restricted_mode_setting": {"status": false,'
            ' "message_has_permission_setting": "not_anyone"}}}'))

    def test_ordinary_group_is_readable(self):
        self.assertFalse(self._probe(
            '{"data": {"restricted_mode_setting": {"status": false,'
            ' "message_has_permission_setting": "all_members"}}}'))

    def test_probe_error_must_not_downgrade_verification(self):
        # Every failure resolves to "readable": this must never silently accept a real
        # delivery failure just because the probe itself could not run.
        with patch.object(readback, "run_lark", side_effect=RuntimeError("transport reset")):
            self.assertFalse(readback.restricted("oc_x"))
        with patch.object(readback, "run_lark", return_value="not json"):
            readback.reset_cache()
            self.assertFalse(readback.restricted("oc_x"))

    def test_missing_chat_id_is_readable(self):
        self.assertTrue(readback.available({}, None))
        self.assertTrue(readback.available({}, ""))

    def test_probe_is_cached_per_process(self):
        with patch.object(readback, "run_lark",
                          return_value='{"data": {"restricted_mode_setting": {"status": true}}}') as call:
            self.assertFalse(readback.available({}, "oc_x"))
            self.assertFalse(readback.available({}, "oc_x"))
            self.assertEqual(call.call_count, 1)


if __name__ == "__main__":
    unittest.main()
