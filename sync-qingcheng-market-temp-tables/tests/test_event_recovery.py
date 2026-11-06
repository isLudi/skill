from __future__ import annotations

import logging
import json
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))
sys.path.insert(0, str(SKILL_ROOT / "tests"))

import governed_temp_table_event_service as service_module  # noqa: E402
from test_event_service import (  # noqa: E402
    APPROVER,
    CHAT,
    MARKET_CHAT,
    event,
    test_config as make_test_config,
)


class EventRecoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = make_test_config(self.root)
        self.config["config_path"] = str(self.root / "config.json")
        self.config["event_key"] = "im.message.receive_v1"
        self.config["event_ready_timeout_seconds"] = 2
        logger = logging.getLogger(f"event-recovery-test-{id(self)}")
        logger.addHandler(logging.NullHandler())
        self.logging_patch = mock.patch.object(service_module, "configure_logging", return_value=logger)
        self.logging_patch.start()
        self.addCleanup(self.logging_patch.stop)

    def test_stdout_eof_is_failure_even_if_process_has_not_exited_yet(self) -> None:
        consumer = service_module.LarkEventConsumer(self.config, logging.getLogger("test-eof"), "lark")
        consumer.process = mock.Mock()
        consumer.process.poll.return_value = None
        consumer.stdout_queue.put(None)
        with self.assertRaises(service_module.ConsumerStoppedError):
            consumer.get(timeout=0.01)

    def test_reconnect_closes_failed_consumer_before_replacing_it(self) -> None:
        service = service_module.GovernedTempTableEventService(self.config)
        service.lark_cli_path = "native-lark"
        original = mock.Mock()
        failed = mock.Mock()
        failed.start.side_effect = service_module.ServiceError("transient start failure")
        healthy = mock.Mock()
        service.consumer = original
        worker = object()
        service.worker = worker
        with (
            mock.patch.object(service, "_wait_for_reconnect", side_effect=[True, True]),
            mock.patch.object(service, "write_status") as status,
            mock.patch.object(service_module.workflow, "resolve_lark_cli", return_value="native-lark"),
            mock.patch.object(service_module, "LarkEventConsumer", side_effect=[failed, healthy]),
        ):
            self.assertTrue(service._reconnect_consumer(service_module.ConsumerStoppedError("eof"), 1))
        original.close.assert_called_once_with()
        failed.close.assert_called_once_with()
        healthy.start.assert_called_once_with()
        self.assertIs(service.consumer, healthy)
        self.assertIs(service.worker, worker)
        self.assertEqual(service.consumer_reconnect_count, 1)
        self.assertEqual(status.call_args_list[0].args[0], "reconnecting")
        self.assertFalse(status.call_args_list[0].kwargs["event_ready"])
        self.assertEqual(status.call_args_list[-1].args[0], "running")
        self.assertTrue(status.call_args_list[-1].kwargs["event_ready"])

    def test_reconnect_wait_respects_stop_file(self) -> None:
        service = service_module.GovernedTempTableEventService(self.config)
        service.stop_path.write_text("stop", encoding="utf-8")
        self.assertFalse(service._wait_for_reconnect(1))
        self.assertTrue(service.stop_event.is_set())

    def test_reconnect_does_not_start_a_new_consumer_until_old_one_closes(self) -> None:
        service = service_module.GovernedTempTableEventService(self.config)
        service.lark_cli_path = "native-lark"
        old = mock.Mock()
        old.close.side_effect = [service_module.ServiceError("still running"), None]
        healthy = mock.Mock()
        service.consumer = old
        with (
            mock.patch.object(service, "_wait_for_reconnect", side_effect=[True, True]),
            mock.patch.object(service, "write_status"),
            mock.patch.object(service_module.workflow, "resolve_lark_cli", return_value="native-lark"),
            mock.patch.object(service_module, "LarkEventConsumer", return_value=healthy) as factory,
        ):
            self.assertTrue(service._reconnect_consumer(service_module.ConsumerStoppedError("eof"), 1))
        self.assertEqual(old.close.call_count, 2)
        factory.assert_called_once()
        healthy.start.assert_called_once()

    def test_precheck_commands_from_both_chats_continue_after_reconnect(self) -> None:
        service = service_module.GovernedTempTableEventService(self.config)
        old = mock.Mock()
        old.get.side_effect = service_module.ConsumerStoppedError("stdout closed")
        new = mock.Mock()
        qing = event("om_reconnectqing", APPROVER, "@管家 预检个人期度")
        market = event("om_reconnectmarket", APPROVER, "@管家 预检带班架构")
        market["chat_id"] = MARKET_CHAT
        def stop_after_events(*args: object, **kwargs: object) -> None:
            service.stop_event.set()
            return None
        queue_values = [qing, market, stop_after_events]
        def read_event(*args: object, **kwargs: object):
            value = queue_values.pop(0)
            return value(*args, **kwargs) if callable(value) else value
        new.get.side_effect = read_event
        gateway = mock.Mock(cli="native-lark")
        worker = mock.Mock()
        with (
            mock.patch.object(service_module, "LarkGateway", return_value=gateway),
            mock.patch.object(service_module, "LarkEventConsumer", side_effect=[old, new]),
            mock.patch.object(service_module, "JobWorker", return_value=worker),
            mock.patch.object(service_module.workflow, "resolve_lark_cli", return_value="native-lark"),
            mock.patch.object(service, "_wait_for_reconnect", return_value=True),
            mock.patch.object(service_module.signal, "signal"),
        ):
            self.assertEqual(service.run(), 0)
        jobs = service.ledger.recent_jobs(10)
        by_chat = {job["chat_id"]: job for job in jobs}
        self.assertEqual(set(by_chat), {CHAT, MARKET_CHAT})
        self.assertEqual(by_chat[CHAT]["family_ids"], ["personal_period_goal"])
        self.assertEqual(by_chat[MARKET_CHAT]["family_ids"], ["market_period_architecture"])
        self.assertTrue(all(job["action"] == "plan" for job in jobs))
        self.assertEqual(worker.start.call_count, 1)
        self.assertEqual(worker.submit.call_count, 2)
        self.assertEqual(service.consumer_reconnect_count, 1)

    def test_real_child_eof_reconnects_and_routes_both_chats(self) -> None:
        service = service_module.GovernedTempTableEventService(self.config)
        qing = event("om_liveqing", APPROVER, "@管家 预检个人期度")
        market = event("om_livemarket", APPROVER, "@管家 预检带班架构")
        market["chat_id"] = MARKET_CHAT
        marker = self.root / "consumer-started"
        fake_cli = self.root / "fake_lark.py"
        source = (
            "import json,sys\n"
            "from pathlib import Path\n"
            f"marker=Path({str(marker)!r})\n"
            "restarted=marker.exists()\n"
            "marker.write_text('started',encoding='utf-8')\n"
            "print('[event] ready event_key=im.message.receive_v1',file=sys.stderr,flush=True)\n"
            f"events=json.loads({json.dumps(json.dumps([qing, market], ensure_ascii=True))})\n"
            "if restarted:\n"
            "    for event in events: print(json.dumps(event,ensure_ascii=True),flush=True)\n"
            "sys.stdin.read()\n"
            "print('[event] exited reason: signal',file=sys.stderr,flush=True)\n"
        )
        fake_cli.write_text(source, encoding="utf-8")
        worker = mock.Mock()
        errors: list[BaseException] = []
        def run_service() -> None:
            try:
                service.run()
            except BaseException as exc:
                errors.append(exc)
        def wait_for(predicate, seconds: float = 10) -> bool:
            deadline = time.monotonic() + seconds
            while time.monotonic() < deadline:
                if predicate():
                    return True
                time.sleep(0.05)
            return False
        with (
            mock.patch.object(service_module, "LarkGateway", return_value=mock.Mock(cli="fake-lark")),
            mock.patch.object(service_module, "JobWorker", return_value=worker),
            mock.patch.object(service_module.workflow, "resolve_lark_cli", return_value="fake-lark"),
            mock.patch.object(service_module.workflow, "_command_argv", return_value=[sys.executable, "-u", str(fake_cli)]),
            mock.patch.object(service_module.signal, "signal"),
        ):
            thread = threading.Thread(target=run_service, daemon=True)
            thread.start()
            try:
                self.assertTrue(wait_for(lambda: service.status_path.exists() and service_module.read_json(service.status_path).get("event_ready") is True))
                self.assertIsNotNone(service.consumer)
                first = service.consumer.process
                self.assertIsNotNone(first)
                first_pid = first.pid
                first.stdin.close()
                self.assertTrue(wait_for(lambda: service.consumer_reconnect_count == 1))
                self.assertNotEqual(service.consumer.process.pid, first_pid)
                self.assertTrue(first.stdout.closed)
                self.assertTrue(first.stderr.closed)
                second = service.consumer.process
                self.assertTrue(wait_for(lambda: len(service.ledger.recent_jobs(10)) == 2))
            finally:
                service.request_stop()
                thread.join(timeout=10)
            self.assertFalse(thread.is_alive())
            self.assertTrue(second.stdin.closed)
            self.assertTrue(second.stdout.closed)
            self.assertTrue(second.stderr.closed)
        self.assertEqual(errors, [])
        jobs = service.ledger.recent_jobs(10)
        self.assertEqual({job["chat_id"] for job in jobs}, {CHAT, MARKET_CHAT})
        self.assertTrue(all(job["action"] == "plan" for job in jobs))
        self.assertEqual(worker.start.call_count, 1)
        self.assertEqual(worker.submit.call_count, 2)


if __name__ == "__main__":
    unittest.main()
