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

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import scheduled_push as sp
from lark_delivery.domains.market_consultant import delivery_gate


class ScheduledPushTests(unittest.TestCase):
    def setUp(self):
        self.cfg = sp.load_config(sp.DEFAULT_CONFIG)
        # These tests retain the old names-only/log protocol as an isolated
        # helper fixture. Current-profile outlet tests live in test_scheduled_grade.
        self.cfg.pop("report_profile")
        self.cfg["upstream"].pop("log_protocol", None)
        self.slot = datetime(2026, 9, 8, 13, tzinfo=sp.TZ)
        self.clock = patch.object(sp, "now", return_value=self.slot + timedelta(minutes=20))
        self.clock.start()
        self.addCleanup(self.clock.stop)

    def history(self):
        u = self.cfg["upstream"]
        stamp = self.slot.strftime("%Y-%m-%d %H:%M:%S")
        row = {"id": 123, "taskId": u["nezha_task_id"], "status": 6,
               "periodTime": stamp, "planRunTime": stamp,
               "startTime": "2026-09-08 13:00:04", "endTime": "2026-09-08 13:07:35",
               "runConfig": json.dumps({"execFileId": u["exec_file_id"], "triggerSourceEnum": "SCHEDULE"})}
        return {"scope": u.copy(), "identity": {"name": u["owner"]},
                "task_schedule": {"supervisor": u["owner"], "scheduleId": u["schedule_id"], "scheduleFrequency": "4h"},
                "executions": [row]}

    def context(self):
        return {"period": "20260911期", "raw_count": 2, "channel": self.cfg["channels"][0],
                "snapshot": ["20260908", "11"], "raw_read_audit": {"has_more": False, "rev": 17},
                "mention_target": "none", "markdown": "本次5min率较低顾问：A\n![p](img_process_preview)\n![r](img_result_preview)",
                "image_path": Path("p.png"), "result_image_path": Path("r.png")}

    def evidence(self):
        return {"period": "20260911期", "dt": "20260908", "hour": 11,
                "channel_counts": {self.cfg["channels"][0]: 2}}

    def test_two_slots_only(self):
        for hour in range(24):
            at = datetime(2026, 9, 8, hour, 20, tzinfo=sp.TZ)
            self.assertEqual(sp.active_slot(at, self.cfg) is not None, hour in [13, 17])

    def test_first_round_boundary(self):
        self.assertIsNone(sp.active_slot(datetime(2026, 9, 8, 12, 20, tzinfo=sp.TZ), self.cfg))
        self.assertIsNotNone(sp.active_slot(self.slot + timedelta(minutes=20), self.cfg))

    def test_report_kind_is_part_of_delivery_key(self):
        regular = sp.delivery_key(self.cfg, self.slot, "KOC渠道进量", "regular")
        volume = sp.delivery_key(self.cfg, self.slot, "KOC渠道进量", "volume")
        self.assertNotEqual(regular, volume)

    def test_17_slot_routes_only_to_volume_report(self):
        slot = self.slot.replace(hour=17)
        context = {
            "report_kind": "volume", "report_profile": "volume", "channel": "KOC渠道进量",
            "channels": ["KOC-A"], "period": "20260911期", "raw_count": 2,
            "raw_read_audit": {"has_more": False, "rev": 17}, "lead_read_audit": {"rev": 18},
            "markdown": "【KOC渠道】\n![图](img_volume_preview)", "image_path": None,
            "result_image_path": None, "volume_image_path": Path("volume.png"),
        }
        with tempfile.TemporaryDirectory() as folder, patch.object(sp, "now", return_value=slot + timedelta(minutes=20)), \
             patch.object(sp, "verify_bot"), patch.object(sp, "upstream_ready", return_value={
                 "volume": {"periods": ["20260904期", "20260911期"], "total": 2}}), \
             patch.object(sp.vr, "prepare_context", return_value=context) as prepare_volume, \
             patch.object(sp, "prepare_report") as prepare_regular, patch.object(sp, "assert_current_revision"), \
             patch.object(sp.gp, "send_markdown") as dry_send:
            db = sp.connect_ledger(Path(folder))
            self.assertEqual(sp.run_slot(self.cfg, True, slot, Path(folder), db), 0)
            db.close()
        prepare_volume.assert_called_once()
        prepare_regular.assert_not_called()
        self.assertTrue(dry_send.call_args.kwargs["dry_run"])

    def test_volume_producer_requires_exact_schedule_file_and_complete_log(self):
        slot = self.slot.replace(hour=17)
        cfg = copy.deepcopy(self.cfg)
        cfg["upstream"] = cfg["volume_report"]["upstream"]
        u = cfg["upstream"]
        stamp = slot.strftime("%Y-%m-%d %H:%M:%S")
        execution = {"id": 99, "taskId": u["nezha_task_id"], "status": 6,
                     "periodTime": stamp, "planRunTime": stamp,
                     "startTime": "2026-09-08 17:00:04", "endTime": "2026-09-08 17:04:00",
                     "runConfig": json.dumps({"execFileId": u["exec_file_id"], "triggerSourceEnum": "SCHEDULE"})}
        log = ("采用dt=20260908, hour=15，延迟2小时\nKyuubi查询完成：3行、13列\n"
               "数据校验通过：3行，期次[u'20260904\\u671f', u'20260911\\u671f']，2个归因渠道\n"
               "目标多维表格校验通过：table_id=tblGUCxgUTZPjv3c\n目标字段校验通过：14个字段\n"
               "写入前旧记录数：2\n新记录创建完成：3条\n"
               "数据校验通过：3行，期次[u'20260904\\u671f', u'20260911\\u671f']，2个归因渠道\n"
               "新记录回读校验通过\n旧记录删除完成：2条\n"
               "数据校验通过：3行，期次[u'20260904\\u671f', u'20260911\\u671f']，2个归因渠道\n"
               "最终回读校验通过：3条\n已按要求跳过旧KOC汇总表写入\nSUCCESS: done\nexit_code:  0\n")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "stage.log"
            path.write_text(log, encoding="utf-8")
            doc = {"scope": u.copy(), "identity": {"name": u["owner"]}, "execution": execution,
                   "execution_detail": {"status": 6}, "task_schedule": {
                       "supervisor": u["owner"], "scheduleId": u["schedule_id"], "scheduleFrequency": "4h"},
                   "stages": [{"metadata": {"statusDesc": "success", "taskId": u["nezha_task_id"]},
                               "log_file": path.name, "log_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}]}
            self.assertEqual(sp.parse_volume_log(doc, Path(folder), cfg, slot, execution)["total"], 3)
            bad = copy.deepcopy(doc)
            bad["execution"]["runConfig"] = json.dumps({"execFileId": u["exec_file_id"] - 1,
                                                         "triggerSourceEnum": "SCHEDULE"})
            with self.assertRaisesRegex(ValueError, "published execution file"):
                sp.parse_volume_log(bad, Path(folder), cfg, slot, execution)
            path.write_text(log.replace("旧记录删除完成：2条", "旧记录删除完成：1条"), encoding="utf-8")
            doc["stages"][0]["log_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            with self.assertRaisesRegex(ValueError, "volume create/delete/readback"):
                sp.parse_volume_log(doc, Path(folder), cfg, slot, execution)

    def test_volume_and_lead_producers_must_agree_on_periods(self):
        lead = {"periods": {"20260918期": {}, "20260925期": {}}}
        sp.require_shared_periods(lead, {"periods": ["20260925期", "20260918期"]})
        with self.assertRaisesRegex(ValueError, "periods disagree"):
            sp.require_shared_periods(lead, {"periods": ["20260918期", "20261002期"]})

    def test_business_config_routes_regular_and_volume_after_approval(self):
        definition = sp.catalog.load_channel("market_consultant/business_koc_math")
        target = sp.catalog.select_targets(definition)[0]
        cfg = sp.catalog.schedule_config(definition, target)
        sp.validate_config(cfg)
        self.assertEqual(cfg["slot_reports"], {"13": "regular", "17": "volume"})
        self.assertEqual(cfg["hours"], [13, 17])
        self.assertEqual(cfg["volume_report"]["stage"], "scheduled")
        self.assertEqual(sp.report_for_slot(cfg, 13), "regular")
        self.assertEqual(sp.report_for_slot(cfg, 17), "volume")

    def test_volume_revision_guard_checks_both_tables(self):
        context = {"report_kind": "volume", "base_token": "base", "revision_sources": (
            {"table_id": "volume", "field": "期次", "rev": 11},
            {"table_id": "lead", "field": "期次", "rev": 12},
        )}
        replies = [json.dumps({"rev": 11}), json.dumps({"rev": 12})]
        with patch.object(sp.vr.gp, "run_lark", side_effect=replies) as run_lark:
            sp.assert_current_revision(context, self.cfg)
        self.assertEqual(run_lark.call_count, 2)
        self.assertEqual([call.args[0][5] for call in run_lark.call_args_list], ["volume", "lead"])

    def test_no_late_catchup(self):
        self.assertIsNone(sp.active_slot(self.slot + timedelta(minutes=51), self.cfg))
        self.assertIsNone(sp.active_slot(self.slot + timedelta(minutes=19), self.cfg))

    def test_retry_grid_and_deadline(self):
        self.assertEqual(sp.next_check(self.slot + timedelta(minutes=15), self.slot, self.cfg).minute, 20)
        self.assertEqual(sp.next_check(self.slot + timedelta(minutes=20, seconds=43), self.slot, self.cfg).minute, 22)
        self.assertEqual(sp.next_check(self.slot + timedelta(minutes=49), self.slot, self.cfg).minute, 50)
        self.assertEqual(sp.next_check(self.slot + timedelta(minutes=50), self.slot, self.cfg).minute, 52)

    def test_staggered_retry_grid_starts_from_each_task_minute(self):
        cfg = sp.load_config(sp.DEFAULT_CONFIG)
        cfg.update({"stagger_order": 4, "prepare_minute": 21, "send_minute": 21})
        sp.validate_config(cfg)
        self.assertEqual(sp.next_check(self.slot + timedelta(minutes=21, seconds=1), self.slot, cfg).minute, 23)
        self.assertEqual(sp.next_check(self.slot + timedelta(minutes=47), self.slot, cfg).minute, 49)
        self.assertEqual(sp.next_check(self.slot + timedelta(minutes=49), self.slot, cfg).minute, 51)

    def test_registered_tasks_start_in_pairs_without_changing_order(self):
        rows = []
        for key in sp.catalog.registry()["channels"]:
            definition = sp.catalog.load_channel(key)
            if not definition["schedule"]["enabled"] or definition["adapter"] != "market-grade-manager-v1":
                continue
            cfg = sp.catalog.schedule_config(definition, sp.catalog.select_targets(definition)[0])
            sp.validate_config(cfg)
            rows.append((cfg["stagger_order"], cfg["prepare_minute"], cfg["send_minute"]))
        self.assertEqual(sorted(rows), [(order, 20 + (order - 1) // 2, 20 + (order - 1) // 2)
                                        for order in range(1, len(rows) + 1)])
        self.assertEqual(
            [minute for _, minute, _ in sorted(rows)],
            [20, 20, 21, 21, 22, 22, 23, 23, 24],
        )
        old = sp.load_config(sp.DEFAULT_CONFIG)
        old.update({"stagger_order": 4, "prepare_minute": 23, "send_minute": 23})
        with self.assertRaisesRegex(ValueError, "retry window"):
            sp.validate_config(old)

    def test_live_status_is_removed_when_run_scope_ends(self):
        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder)
            with sp.live_status(state, self.cfg, self.slot) as status_path:
                sp.emit("checking_upstream", attempt=1)
                payload = json.loads(status_path.read_text(encoding="utf-8"))
                self.assertEqual(payload["event"], "checking_upstream")
            self.assertFalse((state / "live-status.json").exists())

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
        h["executions"].append({"id": 124, "startTime": "2026-09-08 13:10:00"})
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
        valid = ('采用dt=20260908, hour=11，延迟2小时\n'
                 '目标多维表格校验通过：table_id=tbljWRvaqKTdrCx4\n'
                 '渠道分布：{"KOC-周帅数学":2}\n'
                 '数据校验通过：2行，期次20260911期，1个渠道\n'
                 '新记录回读校验通过\n旧记录删除完成：1条\n'
                 '最终回读校验通过：2条\nSUCCESS: done\nexit_code:  0\n')
        bad_logs = [valid.replace('最终回读校验通过：2条', '最终回读校验通过：3条'),
                    valid.replace('新记录回读校验通过', '新记录回读失败'),
                    valid.replace('hour=11', 'hour=15'), valid.replace('exit_code:  0', 'exit_code:  1'),
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

    def test_uncertain_resends_with_the_same_key_and_never_cleans(self):
        # 2026-09-29 12:20: an unconfirmed send must not end the slot. The retry
        # re-issues the SAME idempotency key, so the platform dedupes if the first
        # attempt did land, and nothing is cleaned up while delivery is unknown.
        with tempfile.TemporaryDirectory() as folder:
            db = sp.connect_ledger(Path(folder))
            with patch.object(sp, "assert_current_revision"), patch.object(sp.gp, "upload_image", return_value="img_key"), \
                 patch.object(sp.gp, "send_markdown", side_effect=TimeoutError) as send, patch.object(sp.gp, "_cleanup_local_image") as cleanup:
                self.assertFalse(sp.deliver(self.context(), self.cfg, self.slot, db, self.evidence()))
                self.assertFalse(sp.deliver(self.context(), self.cfg, self.slot, db, self.evidence()))
                self.assertEqual(send.call_count, 2)
                self.assertEqual(send.call_args_list[0].args[2], send.call_args_list[1].args[2])
                cleanup.assert_not_called()
                self.assertEqual(db.execute("SELECT status FROM deliveries").fetchone()[0], "uncertain")
            db.close()

    def test_uncertain_converges_when_the_platform_returns_the_original_message(self):
        # Why re-issuing the same key is worth doing: an outcome that was lost after
        # dispatch is recovered rather than left ambiguous forever. The platform
        # returns the ORIGINAL message, the readback verifies, the slot converges.
        with tempfile.TemporaryDirectory() as folder:
            db = sp.connect_ledger(Path(folder))
            with patch.object(sp, "assert_current_revision"), patch.object(sp.gp, "upload_image", return_value="img_key"), \
                 patch.object(sp.gp, "send_markdown", side_effect=[TimeoutError, {"message_id": "om_original"}]) as send, \
                 patch.object(sp.gp, "_cleanup_local_image", return_value={"deleted": True}), \
                 patch.object(sp, "receipt_readback", return_value={"verified": True}):
                self.assertFalse(sp.deliver(self.context(), self.cfg, self.slot, db, self.evidence()))
                self.assertTrue(sp.deliver(self.context(), self.cfg, self.slot, db, self.evidence()))
                self.assertEqual(send.call_count, 2)
                self.assertEqual(send.call_args_list[0].args[2], send.call_args_list[1].args[2])
                self.assertEqual(db.execute("SELECT status,message_id FROM deliveries").fetchone(),
                                 ("sent_verified", "om_original"))
            db.close()

    def test_recorded_message_id_is_only_reverified_never_resent(self):
        # The safety half of the rule: a message already in the group is never
        # re-issued, so a failing readback can never publish a second copy.
        with tempfile.TemporaryDirectory() as folder:
            db = sp.connect_ledger(Path(folder))
            channel = self.cfg["channels"][0]
            key = sp.delivery_key(self.cfg, self.slot, channel)
            db.execute("INSERT INTO deliveries VALUES (?,?,?,?,?,?)",
                       (key, self.slot.isoformat(), channel, "sent_unverified", "om_original",
                        json.dumps({"image_keys": {"process": "img_p"}})))
            db.commit()
            # The readback-only path lives in delivery_gate, so that is where its
            # readback has to be patched.
            with patch.object(sp.gp, "send_markdown") as send, \
                 patch.object(delivery_gate, "receipt_readback", return_value={"verified": True}):
                self.assertTrue(sp.deliver(self.context(), self.cfg, self.slot, db, self.evidence()))
                send.assert_not_called()
                self.assertEqual(db.execute("SELECT status FROM deliveries").fetchone()[0], "sent_verified")
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
