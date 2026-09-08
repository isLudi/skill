"""Offline schedule, freshness and durable send guards; no live calls."""
import copy
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import scheduled_push as sp


class ScheduledPushTests(unittest.TestCase):
    def setUp(self):
        self.cfg = sp.load_config(sp.DEFAULT_CONFIG)
        self.slot = datetime(2026, 9, 7, 21, tzinfo=sp.TZ)
        self.clock = patch.object(sp, "now", return_value=self.slot + timedelta(minutes=20))
        self.clock.start()
        self.addCleanup(self.clock.stop)

    def history(self):
        u = self.cfg["upstream"]
        row = {"id": 123, "taskId": u["nezha_task_id"], "status": 6,
               "periodTime": "2026-09-07 21:00:00", "planRunTime": "2026-09-07 21:00:00",
               "startTime": "2026-09-07 21:00:04", "endTime": "2026-09-07 21:07:35",
               "runConfig": json.dumps({"execFileId": u["exec_file_id"], "triggerSourceEnum": "SCHEDULE"})}
        return {"scope": u.copy(), "identity": {"name": u["owner"]},
                "task_schedule": {"supervisor": u["owner"], "scheduleId": u["schedule_id"], "scheduleFrequency": "4h"},
                "executions": [row]}

    def context(self):
        return {"period": "20260911期", "raw_count": 2, "channel": self.cfg["channels"][0],
                "snapshot": ["20260907", "19"], "raw_read_audit": {"has_more": False, "rev": 17},
                "mention_target": "none", "markdown": "本次5min率较低顾问：A\n![p](img_process_preview)\n![r](img_result_preview)",
                "image_path": Path("p.png"), "result_image_path": Path("r.png")}

    def evidence(self):
        return {"period": "20260911期", "dt": "20260907", "hour": 19,
                "channel_counts": {self.cfg["channels"][0]: 2}}

    def test_four_slots_only(self):
        for hour in range(24):
            at = datetime(2026, 9, 8, hour, 20, tzinfo=sp.TZ)
            self.assertEqual(sp.active_slot(at, self.cfg) is not None, hour in [9, 13, 17, 21])

    def test_first_round_boundary(self):
        self.assertIsNone(sp.active_slot(datetime(2026, 9, 7, 17, 20, tzinfo=sp.TZ), self.cfg))
        self.assertIsNotNone(sp.active_slot(self.slot + timedelta(minutes=15), self.cfg))

    def test_no_late_catchup(self):
        self.assertIsNone(sp.active_slot(self.slot + timedelta(minutes=51), self.cfg))
        self.assertIsNone(sp.active_slot(self.slot + timedelta(minutes=14), self.cfg))

    def test_retry_grid_and_deadline(self):
        self.assertEqual(sp.next_check(self.slot + timedelta(minutes=15), self.slot).minute, 20)
        self.assertEqual(sp.next_check(self.slot + timedelta(minutes=20, seconds=43), self.slot).minute, 22)
        self.assertEqual(sp.next_check(self.slot + timedelta(minutes=49), self.slot).minute, 50)
        self.assertEqual(sp.next_check(self.slot + timedelta(minutes=50), self.slot).minute, 52)

    def test_actual_message_window(self):
        for minute in [15, 19, 51, 59]:
            with patch.object(sp, 'now', return_value=self.slot + timedelta(minutes=minute)):
                with self.assertRaises(ValueError):
                    sp.require_send_window(self.slot)
        for minute in [20, 22, 50]:
            with patch.object(sp, 'now', return_value=self.slot + timedelta(minutes=minute)):
                sp.require_send_window(self.slot)

    def test_upload_finishing_after_cutoff_cannot_send(self):
        with tempfile.TemporaryDirectory() as folder:
            db = sp.connect_ledger(Path(folder))
            with patch.object(sp, 'assert_current_revision'), patch.object(sp.gp, 'upload_image', return_value='img_key'), \
                 patch.object(sp, 'require_send_window', side_effect=[None, ValueError('deadline')]), \
                 patch.object(sp.gp, 'send_markdown') as send:
                with self.assertRaises(ValueError):
                    sp.deliver(self.context(), self.cfg, self.slot, db, self.evidence())
                self.assertEqual(db.execute('SELECT count(*) FROM deliveries').fetchone()[0], 0)
                send.assert_not_called()
            db.close()

    def test_current_success_required(self):
        h = self.history()
        self.assertEqual(sp.validate_history(h, self.cfg, self.slot)["id"], 123)
        for field, value in [("status", 5), ("periodTime", "2026-09-07 17:00:00"), ("taskId", 1)]:
            bad = copy.deepcopy(h)
            bad["executions"][0][field] = value
            with self.assertRaises(ValueError):
                sp.validate_history(bad, self.cfg, self.slot)

    def test_scope_schedule_and_publication_drift(self):
        for key in ("project_id", "folder", "menu_id", "task_name", "task_id", "nezha_task_id"):
            h = self.history()
            h["scope"][key] = "wrong"
            with self.assertRaises(ValueError):
                sp.validate_history(h, self.cfg, self.slot)
        h = self.history()
        h["executions"][0]["runConfig"] = '{"execFileId":42,"triggerSourceEnum":"SCHEDULE"}'
        with self.assertRaises(ValueError):
            sp.validate_history(h, self.cfg, self.slot)

    def test_newer_execution_blocks(self):
        h = self.history()
        h["executions"].append({"id": 124, "startTime": "2026-09-07 21:10:00"})
        with self.assertRaises(ValueError):
            sp.validate_history(h, self.cfg, self.slot)

    def test_ambiguous_execution_blocks(self):
        h = self.history()
        h["executions"].append(copy.deepcopy(h["executions"][0]))
        with self.assertRaises(ValueError):
            sp.validate_history(h, self.cfg, self.slot)

    def test_context_count_period_partition(self):
        c = self.context()
        sp.validate_context(c, self.evidence())
        for key, value in [("period", "old"), ("raw_count", 1), ("snapshot", ["20260907", "15"]),
                           ("mention_target", "supervisor"), ("markdown", '<at user_id="all">'), ("result_image_path", None)]:
            bad = {**c, key: value}
            with self.assertRaises(ValueError):
                sp.validate_context(bad, self.evidence())

    def test_complete_log_protocol_and_hash(self):
        h = self.history()
        row = h["executions"][0]
        valid = ('采用dt=20260907, hour=19，延迟2小时\n'
                 '目标多维表格校验通过：table_id=tbljWRvaqKTdrCx4\n'
                 '渠道分布：{"KOC-周帅数学":2}\n'
                 '数据校验通过：2行，期次20260911期，1个渠道\n'
                 '新记录回读校验通过\n旧记录删除完成：1条\n'
                 '最终回读校验通过：2条\nSUCCESS: done\nexit_code:  0\n')
        bad_logs = [valid.replace('最终回读校验通过：2条', '最终回读校验通过：3条'),
                    valid.replace('新记录回读校验通过', '新记录回读失败'),
                    valid.replace('hour=19', 'hour=15'), valid.replace('exit_code:  0', 'exit_code:  1'),
                    valid.replace('tbljWRvaqKTdrCx4', 'another_table')]
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            for content in [valid, *bad_logs]:
                raw = content.encode('utf-8')
                (directory / 'stage.log').write_bytes(raw)
                doc = {**h, 'execution': row, 'execution_detail': {'status': 6},
                       'stages': [{'metadata': {'statusDesc': 'success', 'taskId': 66504},
                                   'log_file': 'stage.log', 'log_sha256': hashlib.sha256(raw).hexdigest()}]}
                if content == valid:
                    result = sp.parse_complete_log(doc, directory, self.cfg, self.slot, row)
                    self.assertEqual(result['total'], 2)
                    doc['stages'][0]['log_sha256'] = 'bad-hash'
                    with self.assertRaises(ValueError):
                        sp.parse_complete_log(doc, directory, self.cfg, self.slot, row)
                else:
                    with self.assertRaises(ValueError):
                        sp.parse_complete_log(doc, directory, self.cfg, self.slot, row)

    def test_readback_requires_both_images_period_and_no_mentions(self):
        context = self.context()
        message = {'message_id': 'om_real', 'chat_id': self.cfg['chat_id'],
                   'sender': {'name': '管家'}, 'content': '20260911期 ![p](img_p) ![r](img_r)'}
        with patch.object(sp.gp, 'run_lark', return_value=json.dumps({'ok': True, 'data': {'messages': [message]}})):
            self.assertTrue(sp.receipt_readback('om_real', self.cfg, context, {'process': 'img_p', 'result': 'img_r'})['verified'])
        for field, value in [('content', '20260911期 img_p'), ('content', '20260911期 img_p img_r <at user_id="all">'),
                             ('sender', {'name': 'another-bot'}), ('chat_id', 'another-chat')]:
            bad = {**message, field: value}
            with patch.object(sp.gp, 'run_lark', return_value=json.dumps({'ok': True, 'data': {'messages': [bad]}})):
                with self.assertRaises(ValueError):
                    sp.receipt_readback('om_real', self.cfg, context, {'process': 'img_p', 'result': 'img_r'})

    def test_slot_dedup_ignores_content_changes(self):
        a = sp.delivery_key(self.cfg, self.slot, "A")
        self.assertEqual(a, sp.delivery_key(self.cfg, self.slot, "A"))
        self.assertNotEqual(a, sp.delivery_key(self.cfg, self.slot + timedelta(hours=4), "A"))
        self.assertNotEqual(a, sp.delivery_key(self.cfg, self.slot, "B"))
        self.assertLessEqual(len(a), 50)

    def test_atomic_claim(self):
        with tempfile.TemporaryDirectory() as folder:
            one = sp.connect_ledger(Path(folder))
            two = sp.connect_ledger(Path(folder))
            self.assertTrue(sp.claim(one, "key", self.slot, "A"))
            self.assertFalse(sp.claim(two, "key", self.slot, "A"))
            one.close()
            two.close()

    def test_uncertain_never_resends_or_cleans(self):
        with tempfile.TemporaryDirectory() as folder:
            db = sp.connect_ledger(Path(folder))
            with patch.object(sp, "assert_current_revision"), patch.object(sp.gp, "upload_image", return_value="img_key"), \
                 patch.object(sp.gp, "send_markdown", side_effect=TimeoutError) as send, patch.object(sp.gp, "_cleanup_local_image") as cleanup:
                self.assertFalse(sp.deliver(self.context(), self.cfg, self.slot, db, self.evidence()))
                self.assertFalse(sp.deliver(self.context(), self.cfg, self.slot, db, self.evidence()))
                self.assertEqual(send.call_count, 1)
                cleanup.assert_not_called()
                self.assertEqual(db.execute("SELECT status FROM deliveries").fetchone()[0], "uncertain")
            db.close()

    def test_real_message_id_before_cleanup(self):
        with tempfile.TemporaryDirectory() as folder:
            db = sp.connect_ledger(Path(folder))
            def clean(path):
                self.assertEqual(db.execute("SELECT message_id FROM deliveries").fetchone()[0], "om_actual")
                return {"deleted": True}
            with patch.object(sp, "assert_current_revision"), patch.object(sp.gp, "upload_image", return_value="img_key"), \
                 patch.object(sp.gp, "send_markdown", return_value={"message_id": "om_actual"}) as send, \
                 patch.object(sp.gp, "_cleanup_local_image", side_effect=clean) as cleanup, \
                 patch.object(sp, "receipt_readback", return_value={"verified": True}):
                self.assertTrue(sp.deliver(self.context(), self.cfg, self.slot, db, self.evidence()))
                self.assertTrue(sp.deliver(self.context(), self.cfg, self.slot, db, self.evidence()))
                self.assertEqual(send.call_count, 1)
                self.assertEqual(cleanup.call_count, 2)
            db.close()

    def test_upload_failure_does_not_claim_or_send(self):
        with tempfile.TemporaryDirectory() as folder:
            db = sp.connect_ledger(Path(folder))
            with patch.object(sp, "assert_current_revision"), patch.object(sp.gp, "upload_image", side_effect=RuntimeError), \
                 patch.object(sp.gp, "send_markdown") as send:
                with self.assertRaises(RuntimeError):
                    sp.deliver(self.context(), self.cfg, self.slot, db, self.evidence())
                self.assertEqual(db.execute("SELECT count(*) FROM deliveries").fetchone()[0], 0)
                send.assert_not_called()
            db.close()


if __name__ == "__main__":
    unittest.main()
