from threading import Barrier
import unittest
from lark_delivery.core.fanout import run_targets


class FanoutTests(unittest.TestCase):
    def setUp(self):
        self.targets = [{"id": "a", "chat_id": "oc_a"}, {"id": "b", "chat_id": "oc_b"}]

    def test_failed_group_does_not_skip_or_replay_other_groups(self):
        calls = []
        def deliver(target):
            calls.append(target["id"])
            if target["id"] == "a":
                raise TimeoutError("uncertain; manual verification required")
            return 0
        result = run_targets(self.targets, deliver)
        self.assertEqual(calls, ["a", "b"])
        self.assertEqual([item["ok"] for item in result], [False, True])

    def test_parallel_targets_do_not_queue_behind_retry_window(self):
        gate = Barrier(2)
        def operation(target):
            gate.wait(timeout=2)
            return 0
        self.assertTrue(all(item["ok"] for item in run_targets(self.targets, operation, parallel=True)))

    def test_duplicate_chat_id_rejected_before_any_operation(self):
        calls = []
        with self.assertRaises(ValueError):
            run_targets([self.targets[0], self.targets[0]], lambda target: calls.append(target))
        self.assertEqual(calls, [])
