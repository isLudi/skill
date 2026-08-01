from __future__ import annotations

import logging
import json
import sqlite3
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import governed_temp_table_sync as workflow  # noqa: E402
from governed_temp_table_event_service import (  # noqa: E402
    EventProcessor,
    Ledger,
    LarkGateway,
    ReplyDispatcher,
    ServiceError,
    SyncExecutor,
    families_for_chat,
    load_config,
    parse_command,
)


APPROVER = "ou_approver"
SOURCE = "ou_bf111effd2d71a52ee40c58c7cb4d105"
COURSE_SOURCE = "ou_3168c83ffe93b49a192755c8e31e2bc5"
MARKET_SOURCE = "ou_04f543bec3cdd195bbdd53a582f68443"
CHAT = "oc_e604e064976c022ab4289fc2fb979332"
MARKET_CHAT = "oc_7b9873ee89b18d11cf60c8768c6eba9e"


def test_config(runtime_root: Path, **overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "mode": "shadow",
        "chat_ids": [CHAT, MARKET_CHAT],
        "source_sender_ids": [SOURCE, COURSE_SOURCE, MARKET_SOURCE],
        "approver_ids": [APPROVER],
        "bot_open_id": None,
        "bot_names": ["管家"],
        "mention_required": True,
        "auto_plan_source_attachments": True,
        "attachment_quiet_seconds": 1,
        "send_replies": False,
        "reply_on_commands": True,
        "reply_on_unknown_commands": False,
        "reply_on_source_attachments": False,
        "reply_progress_updates": False,
        "allow_local_apply": False,
        "allow_production_upload": False,
        "command_timeout_seconds": 60,
        "python_executable": r"D:\anaconda3\python.exe",
        "sync_script": str(
            SKILL_ROOT / "scripts" / "governed_temp_table_sync.py"
        ),
        "workflow_registry": str(SKILL_ROOT / "references" / "workflow_registry.json"),
        "runtime_root": str(runtime_root),
        "sync_runtime_root": str(runtime_root / "sync"),
    }
    value.update(overrides)
    return value


def event(message_id: str, sender_id: str, content: str, message_type: str = "text") -> dict[str, object]:
    return {
        "message_id": message_id,
        "chat_id": CHAT,
        "sender_id": sender_id,
        "sender_type": "user",
        "message_type": message_type,
        "content": content,
        "create_time": "1000",
        "mentions": [{"name": "管家"}],
    }


class FakeReplies:
    def __init__(self) -> None:
        self.items: list[tuple[str, str, str | None, str, str]] = []

    def send(
        self,
        reply_to: str,
        content: str,
        *,
        job_id: str | None = None,
        suffix: str = "reply",
        category: str = "command",
        phase: str = "direct",
    ) -> str:
        self.items.append((reply_to, content, job_id, category, phase))
        return "sent"


class FakeGateway:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[tuple[str, str, str]] = []

    def reply(self, message_id: str, content: str, idempotency_key: str) -> dict[str, object]:
        self.calls.append((message_id, content, idempotency_key))
        if self.fail:
            raise ServiceError(r"reply transport failed at C:\internal\bot-state.json")
        return {"data": {"message_id": "om_bot_reply"}}


class EventServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.runtime_root = Path(self.temporary.name)
        self.config = test_config(self.runtime_root)
        self.registry = workflow.load_registry(Path(self.config["workflow_registry"]))
        self.ledger = Ledger(self.runtime_root / "jobs.sqlite3")
        self.replies = ReplyDispatcher(self.config, self.ledger, None)
        self.logger = logging.getLogger(f"test-{id(self)}")
        self.logger.addHandler(logging.NullHandler())
        self.processor = EventProcessor(
            self.config,
            self.registry,
            self.ledger,
            self.replies,
            None,
            None,
            self.logger,
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_command_parser_resolves_three_goal_tables(self) -> None:
        intent = parse_command(
            "@管家 预检最新目标表",
            self.config,
            self.registry,
            families_for_chat(self.registry, CHAT),
        )

        self.assertEqual(intent.action, "plan")
        self.assertEqual(
            intent.family_ids,
            ["personal_period_goal", "team_period_goal", "team_month_goal"],
        )

    def test_command_parser_resolves_latest_course_schedule(self) -> None:
        intent = parse_command(
            "@管家 预检最新开课时间表",
            self.config,
            self.registry,
            families_for_chat(self.registry, CHAT),
        )

        self.assertEqual(intent.action, "plan")
        self.assertEqual(intent.family_ids, ["course_schedule"])

    def test_market_chat_command_is_domain_scoped(self) -> None:
        allowed = families_for_chat(self.registry, MARKET_CHAT)
        intent = parse_command(
            "@管家 预检最新临时表",
            self.config,
            self.registry,
            allowed,
        )

        self.assertEqual(
            allowed,
            [
                "market_cost",
                "market_period_architecture",
                "market_attendance_schedule",
                "market_lead_goal",
                "market_evaluation_architecture",
                "market_plan_id",
            ],
        )
        self.assertEqual(intent.action, "plan")
        self.assertEqual(intent.family_ids, allowed)

    def test_market_attachment_routes_only_in_registered_market_chat(
        self,
    ) -> None:
        market_event = event(
            "om_marketcost",
            MARKET_SOURCE,
            '<file key="file_cost" name="cost.xlsx"/>',
            "file",
        )
        market_event["chat_id"] = MARKET_CHAT

        self.assertEqual(
            self.processor.process(market_event),
            "source_message_queued",
        )
        with sqlite3.connect(self.ledger.path) as connection:
            row = connection.execute(
                "SELECT family_id, chat_id FROM pending_attachments "
                "WHERE message_id = ?",
                ("om_marketcost",),
            ).fetchone()
        self.assertEqual(row, ("market_cost", MARKET_CHAT))

        wrong_chat_event = event(
            "om_marketcostwrongchat",
            MARKET_SOURCE,
            '<file key="file_cost_2" name="cost.xlsx"/>',
            "file",
        )
        self.assertEqual(
            self.processor.process(wrong_chat_event),
            "ignored_type",
        )

    def test_job_status_isolated_by_chat(self) -> None:
        job_id = self.ledger.create_job(
            request_message_id="om_marketjob",
            chat_id=MARKET_CHAT,
            requester_id=APPROVER,
            source="chat_command",
            action="plan",
            family_ids=["market_cost"],
        )

        result = self.processor.process(
            event(
                "om_crosschatstatus",
                APPROVER,
                f"@管家 状态 {job_id}",
            )
        )

        self.assertEqual(result, "status")
        with sqlite3.connect(self.ledger.path) as connection:
            content = connection.execute(
                "SELECT content FROM outbound_messages "
                "ORDER BY id DESC LIMIT 1"
            ).fetchone()[0]
        self.assertEqual(content, f"未找到任务：{job_id}")

    def test_config_rejects_shadow_mode_with_write_gates(self) -> None:
        path = self.runtime_root / "unsafe-config.json"
        unsafe = test_config(self.runtime_root, allow_local_apply=True)
        path.write_text(json.dumps(unsafe, ensure_ascii=False), encoding="utf-8")

        with self.assertRaisesRegex(ServiceError, "Shadow mode"):
            load_config(path)

    def test_config_rejects_string_boolean(self) -> None:
        path = self.runtime_root / "bad-boolean.json"
        unsafe = test_config(self.runtime_root, send_replies="false")
        path.write_text(json.dumps(unsafe, ensure_ascii=False), encoding="utf-8")

        with self.assertRaisesRegex(ServiceError, "JSON boolean"):
            load_config(path)

    def test_processor_rejects_missing_registered_source_sender(self) -> None:
        incomplete = test_config(self.runtime_root, source_sender_ids=[SOURCE])

        with self.assertRaisesRegex(ServiceError, "missing registered workflow senders"):
            EventProcessor(
                incomplete,
                self.registry,
                self.ledger,
                self.replies,
                None,
                None,
                self.logger,
            )

    def test_reply_policy_defaults_to_final_known_commands_only(self) -> None:
        config = test_config(self.runtime_root, send_replies=True)
        gateway = FakeGateway()
        replies = ReplyDispatcher(config, self.ledger, gateway, self.logger)

        progress = replies.send("om_progress", "working", phase="progress")
        final = replies.send("om_final", "done", phase="final")
        unknown = replies.send("om_unknown", "unknown", category="unknown_command")
        attachment = replies.send(
            "om_attachment",
            "attachment done",
            category="source_attachment",
            phase="final",
        )

        self.assertEqual(progress, "suppressed")
        self.assertEqual(final, "sent")
        self.assertEqual(unknown, "suppressed")
        self.assertEqual(attachment, "suppressed")
        self.assertEqual(len(gateway.calls), 1)

    def test_reply_delivery_failure_is_non_fatal_and_audited(self) -> None:
        config = test_config(self.runtime_root, send_replies=True)
        replies = ReplyDispatcher(config, self.ledger, FakeGateway(fail=True), self.logger)

        result = replies.send("om_reply_fail", "safe reply", phase="final")

        self.assertEqual(result, "failed")
        with sqlite3.connect(self.ledger.path) as connection:
            row = connection.execute(
                "SELECT delivery_status, error FROM outbound_messages ORDER BY id DESC LIMIT 1"
            ).fetchone()
        self.assertEqual(row[0], "failed")
        self.assertIn("reply transport failed", row[1])

    def test_reply_uses_escaped_json_after_bot_and_idempotency_flags(self) -> None:
        gateway = LarkGateway(self.config)
        gateway.cli = "lark-cli"
        content = "line one\nline two\nline three"

        with mock.patch.object(
            workflow,
            "run_json_command",
            return_value={"data": {"message_id": "om_bot_reply"}},
        ) as run:
            gateway.reply("om_target", content, "qc-" + ("x" * 60))

        argv = run.call_args.args[1]
        content_index = argv.index("--content")
        as_index = argv.index("--as")
        idempotency_index = argv.index("--idempotency-key")
        self.assertNotIn("--text", argv)
        self.assertLess(as_index, content_index)
        self.assertLess(idempotency_index, content_index)
        self.assertEqual(argv[as_index + 1], "bot")
        self.assertEqual(len(argv[idempotency_index + 1]), 50)
        self.assertNotIn("\n", argv[content_index + 1])
        self.assertEqual(json.loads(argv[content_index + 1]), {"text": content})

    @unittest.skipUnless(sys.platform == "win32", "Windows native argv regression")
    def test_windows_native_exe_preserves_multiline_and_shell_metacharacters(self) -> None:
        original_run_json_command = workflow.run_json_command
        capture_script = (
            "import json,sys; "
            "print(json.dumps({'ok':True,'data':{'argv':sys.argv[1:]}}, "
            "ensure_ascii=True))"
        )

        def capture_with_native_executable(
            _executable: str,
            argv: list[str],
            **kwargs: object,
        ) -> dict[str, object]:
            return original_run_json_command(
                sys.executable,
                ["-c", capture_script, *argv],
                timeout=int(kwargs.get("timeout", 60)),
            )

        gateway = LarkGateway(self.config)
        gateway.cli = str(Path(sys.executable).resolve())
        content = "line one\n<target> | failed & retry > audit\n%PATH% ^ (test)"

        with mock.patch.object(
            workflow,
            "run_json_command",
            side_effect=capture_with_native_executable,
        ):
            result = gateway.reply("om_target", content, "qc-windows-metacharacters")

        argv = result["data"]["argv"]
        content_index = argv.index("--content")
        as_index = argv.index("--as")
        idempotency_index = argv.index("--idempotency-key")
        self.assertLess(as_index, content_index)
        self.assertLess(idempotency_index, content_index)
        self.assertEqual(argv[as_index + 1], "bot")
        self.assertEqual(
            json.loads(argv[content_index + 1]),
            {"text": content},
        )

    def test_unknown_command_is_silently_suppressed_by_default(self) -> None:
        config = test_config(self.runtime_root, send_replies=True)
        gateway = FakeGateway()
        replies = ReplyDispatcher(config, self.ledger, gateway, self.logger)
        processor = EventProcessor(
            config,
            self.registry,
            self.ledger,
            replies,
            None,
            gateway,
            self.logger,
        )

        result = processor.process(event("om_unknown1", "ou_regular", "@管家 记得提醒吕帅"))

        self.assertEqual(result, "unknown")
        self.assertEqual(gateway.calls, [])
        with sqlite3.connect(self.ledger.path) as connection:
            row = connection.execute(
                "SELECT delivery_status, error FROM outbound_messages ORDER BY id DESC LIMIT 1"
            ).fetchone()
        self.assertEqual(row, ("suppressed", "unknown_command_replies_disabled"))

    def test_reply_bound_source_error_is_redacted(self) -> None:
        replies = FakeReplies()
        gateway = mock.Mock()
        raw_error = r"cannot read C:\internal\lark\message-cache.json"
        gateway.get_message.side_effect = ServiceError(raw_error)
        processor = EventProcessor(
            self.config,
            self.registry,
            self.ledger,
            replies,
            None,
            gateway,
            self.logger,
        )
        request = event("om_replybound", APPROVER, "@管家 预检此文件")
        request["reply_to"] = "om_sourcefile"

        result = processor.process(request)

        reply_text = replies.items[-1][1]
        self.assertEqual(result, "reply_file_error")
        self.assertNotIn(raw_error, reply_text)
        self.assertNotIn("C:\\internal", reply_text)
        self.assertRegex(reply_text, r"错误编号：TT-[A-F0-9]{10}")

    def test_non_approver_cannot_create_upload_job(self) -> None:
        result = self.processor.process(event("om_evt1", "ou_regular", "@管家 上传最新目标表"))

        self.assertEqual(result, "upload_denied")
        self.assertEqual(self.ledger.recent_jobs(), [])

    def test_shadow_upload_command_is_downgraded_to_plan(self) -> None:
        result = self.processor.process(event("om_evt2", APPROVER, "@管家 上传最新目标表"))
        job = self.ledger.recent_jobs(1)[0]

        self.assertEqual(result, "job_queued")
        self.assertEqual(job["action"], "plan")
        self.assertEqual(job["status"], "queued")
        self.assertIsNone(job["authorized_by"])

    def test_message_id_is_the_idempotency_key(self) -> None:
        first = self.processor.process(event("om_evt3", APPROVER, "@管家 预检最新目标表"))
        second = self.processor.process(event("om_evt3", APPROVER, "@管家 预检最新目标表"))

        self.assertEqual(first, "job_queued")
        self.assertEqual(second, "duplicate")
        self.assertEqual(len(self.ledger.recent_jobs()), 1)

    def test_source_attachment_is_batched_into_an_exact_message_plan(self) -> None:
        queued = self.processor.process(
            event(
                "om_file1",
                SOURCE,
                '<file key="file_key_1" name="个人期度目标表.xlsx" />',
                message_type="file",
            )
        )
        with sqlite3.connect(self.ledger.path) as connection:
            connection.execute(
                "UPDATE pending_attachments SET queued_epoch = ? WHERE message_id = ?",
                (time.time() - 10, "om_file1"),
            )

        job_id = self.processor.flush_pending()
        job = self.ledger.get_job(job_id or "")

        self.assertEqual(queued, "source_message_queued")
        self.assertIsNotNone(job)
        self.assertEqual(job["family_ids"], ["personal_period_goal"])
        self.assertEqual(job["message_bindings"], {"personal_period_goal": "om_file1"})
        self.assertEqual(job["action"], "plan")

    def test_course_link_from_registered_sender_is_auto_batched(self) -> None:
        source = event(
            "om_course1",
            COURSE_SOURCE,
            (
                "【青橙行课--开课时间(1-6节课)】\n"
                "https://docs.baijia.com/sheet/DQUZrYU50dkZPa1FtZWJSU1JE?tab=vhzqxm"
            ),
        )
        source["mentions"] = []

        queued = self.processor.process(source)
        with sqlite3.connect(self.ledger.path) as connection:
            connection.execute(
                "UPDATE pending_attachments SET queued_epoch = ? WHERE message_id = ?",
                (time.time() - 10, "om_course1"),
            )

        job_id = self.processor.flush_pending()
        job = self.ledger.get_job(job_id or "")

        self.assertEqual(queued, "source_message_queued")
        self.assertEqual(job["family_ids"], ["course_schedule"])
        self.assertEqual(job["message_bindings"], {"course_schedule": "om_course1"})

    def test_reply_bound_course_link_creates_exact_message_plan(self) -> None:
        gateway = mock.Mock()
        gateway.get_message.return_value = {
            "message_id": "om_coursesource",
            "chat_id": CHAT,
            "sender": {"id": COURSE_SOURCE, "name": "李怡青"},
            "content": (
                "【青橙行课--开课时间(1-6节课)】\n"
                "https://docs.baijia.com/sheet/DQUZrYU50dkZPa1FtZWJSU1JE?tab=vhzqxm"
            ),
        }
        processor = EventProcessor(
            self.config,
            self.registry,
            self.ledger,
            self.replies,
            None,
            gateway,
            self.logger,
        )
        request = event("om_courserequest", APPROVER, "@管家 预检此表")
        request["reply_to"] = "om_coursesource"

        result = processor.process(request)
        job = self.ledger.recent_jobs(1)[0]

        self.assertEqual(result, "job_queued")
        self.assertEqual(job["family_ids"], ["course_schedule"])
        self.assertEqual(job["message_bindings"], {"course_schedule": "om_coursesource"})

    def test_executor_runs_plan_apply_upload_in_order_only_with_gates(self) -> None:
        production = test_config(
            self.runtime_root,
            mode="production",
            allow_local_apply=True,
            allow_production_upload=True,
        )
        replies = FakeReplies()
        executor = SyncExecutor(production, self.ledger, replies, self.logger)
        job_id = self.ledger.create_job(
            request_message_id="om_upload1",
            chat_id=CHAT,
            requester_id=APPROVER,
            source="test",
            action="upload",
            family_ids=["personal_period_goal"],
            authorized_by=APPROVER,
        )
        responses = [
            {"ok": True, "plan_path": "C:/runtime/plan.json", "plan_sha256": "planhash"},
            {"ok": True, "status": "success", "receipt_path": "C:/runtime/local.json", "receipt_sha256": "localhash"},
            {"ok": True, "status": "success", "receipt_path": "C:/runtime/upload.json", "receipt_sha256": "uploadhash", "uploads": [{}]},
        ]

        with mock.patch.object(executor, "_run", side_effect=responses) as run:
            executor.execute(job_id)

        job = self.ledger.get_job(job_id)
        self.assertEqual(run.call_count, 3)
        self.assertEqual(job["status"], "success")
        self.assertEqual(job["upload_receipt_sha256"], "uploadhash")
        self.assertTrue(replies.items)
        reply_text = replies.items[-1][1]
        self.assertNotIn("C:/runtime", reply_text)
        self.assertNotIn("uploadhash", reply_text)

    def test_planned_reply_hides_plan_path_and_hash(self) -> None:
        replies = FakeReplies()
        executor = SyncExecutor(self.config, self.ledger, replies, self.logger)
        job_id = self.ledger.create_job(
            request_message_id="om_plan_safe_reply",
            chat_id=CHAT,
            requester_id=APPROVER,
            source="chat_command",
            action="plan",
            family_ids=["personal_period_goal"],
        )
        response = {
            "ok": True,
            "plan_path": r"C:\internal\plans\sync_plan.json",
            "plan_sha256": "super-secret-plan-hash",
        }

        with mock.patch.object(executor, "_run", return_value=response):
            executor.execute(job_id)

        reply_text = replies.items[-1][1]
        self.assertIn("状态：planned", reply_text)
        self.assertNotIn(response["plan_path"], reply_text)
        self.assertNotIn(response["plan_sha256"], reply_text)

    def test_reply_failure_does_not_change_successful_upload_status(self) -> None:
        production = test_config(
            self.runtime_root,
            mode="production",
            send_replies=True,
            allow_local_apply=True,
            allow_production_upload=True,
        )
        replies = ReplyDispatcher(production, self.ledger, FakeGateway(fail=True), self.logger)
        executor = SyncExecutor(production, self.ledger, replies, self.logger)
        job_id = self.ledger.create_job(
            request_message_id="om_upload_reply_failure",
            chat_id=CHAT,
            requester_id=APPROVER,
            source="chat_command",
            action="upload",
            family_ids=["personal_period_goal"],
            authorized_by=APPROVER,
        )
        responses = [
            {"ok": True, "plan_path": "C:/runtime/plan.json", "plan_sha256": "planhash"},
            {
                "ok": True,
                "status": "success",
                "receipt_path": "C:/runtime/local.json",
                "receipt_sha256": "localhash",
            },
            {
                "ok": True,
                "status": "success",
                "receipt_path": "C:/runtime/upload.json",
                "receipt_sha256": "uploadhash",
                "uploads": [{}],
            },
        ]

        with mock.patch.object(executor, "_run", side_effect=responses):
            executor.execute(job_id)

        job = self.ledger.get_job(job_id)
        self.assertEqual(job["status"], "success")
        with sqlite3.connect(self.ledger.path) as connection:
            delivery = connection.execute(
                "SELECT delivery_status FROM outbound_messages ORDER BY id DESC LIMIT 1"
            ).fetchone()[0]
        self.assertEqual(delivery, "failed")

    def test_failure_reply_redacts_raw_error_but_keeps_local_evidence(self) -> None:
        replies = FakeReplies()
        executor = SyncExecutor(self.config, self.ledger, replies, self.logger)
        job_id = self.ledger.create_job(
            request_message_id="om_plan_failure",
            chat_id=CHAT,
            requester_id=APPROVER,
            source="chat_command",
            action="plan",
            family_ids=["personal_period_goal"],
        )
        raw_error = r"failed while reading C:\internal\secret\plan.json"

        with mock.patch.object(executor, "_run", side_effect=ServiceError(raw_error)):
            executor.execute(job_id)

        job = self.ledger.get_job(job_id)
        reply_text = replies.items[-1][1]
        stored_error = json.loads(job["error"])
        self.assertEqual(job["status"], "failed")
        self.assertEqual(stored_error["message"], raw_error)
        self.assertNotIn(raw_error, reply_text)
        self.assertNotIn("C:\\internal", reply_text)
        self.assertRegex(reply_text, r"错误编号：TT-[A-F0-9]{10}")

    def test_status_reply_redacts_stored_error(self) -> None:
        job_id = self.ledger.create_job(
            request_message_id="om_status_source",
            chat_id=CHAT,
            requester_id=APPROVER,
            source="chat_command",
            action="plan",
            family_ids=["personal_period_goal"],
        )
        raw_error = r"private failure at C:\internal\plans\sync_plan.json"
        self.ledger.update_job(job_id, status="failed", stage="failed", error=raw_error)

        result = self.processor.process(
            event("om_statusquery", APPROVER, f"@管家 状态 {job_id}")
        )

        self.assertEqual(result, "status")
        with sqlite3.connect(self.ledger.path) as connection:
            content = connection.execute(
                "SELECT content FROM outbound_messages ORDER BY id DESC LIMIT 1"
            ).fetchone()[0]
        self.assertNotIn(raw_error, content)
        self.assertNotIn("C:\\internal", content)
        self.assertRegex(content, r"错误编号：TT-[A-F0-9]{10}")


if __name__ == "__main__":
    unittest.main()
