"""Current profile integration guards; all delivery APIs are mocked."""
import argparse
import copy
from datetime import datetime, timedelta
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import broadcast_policy as bp
import grade_report as gr
import group_push as gp
import scheduled_push as sp
from .test_grade_report import leads, build


class ScheduledGradeTests(unittest.TestCase):
    def setUp(self):
        self.cfg = sp.load_config(sp.DEFAULT_CONFIG)
        self.slot = datetime(2026, 9, 10, 13, tzinfo=sp.TZ)
        clock = patch.object(sp, "now", return_value=self.slot + timedelta(minutes=20))
        clock.start()
        self.addCleanup(clock.stop)

    def context(self, kind="process"):
        report = build(leads(), kind)
        info = {"resolved": {"负责人A": "ou_manager"}, "names": ["负责人A"], "display_names": {},
                "unresolved": [], "ambiguous": {}, "lookup_error": "", "nonmembers": []}
        return {"report_profile": bp.PROFILE, "channel": bp.CHANNEL, "chat_id": bp.CHAT_ID, "identity": "bot",
                "period": "20260911期", "report_type": kind, "raw_count": 10, "raw_read_audit": {"has_more": False, "rev": 100},
                "snapshot": ["20260910", "11"], "mention_target": "manager", "mention_info": info,
                "grade_report": report, "image_path": Path("p.png") if kind != "result" else None,
                "result_image_path": Path("r.png") if kind != "process" else None,
                "markdown": gr.build_markdown(report, "20260911期", bp.CHANNEL, kind, info,
                           {"process": "img_process_preview", "result": "img_result_preview"})}

    def evidence(self):
        return {"period": "20260911期、20260918期", "dt": "20260910", "hour": 11,
                "channel_counts": {bp.CHANNEL: 11}, "periods": {
                    "20260911期": {"row_count": 10, "channel_counts": {bp.CHANNEL: 10}},
                    "20260918期": {"row_count": 1, "channel_counts": {bp.CHANNEL: 1}}}}

    def test_disabled_scope_does_not_open_outlet(self):
        self.cfg["enabled"] = False
        self.assertEqual(self.cfg["channels"], [bp.CHANNEL])
        self.assertEqual(self.cfg["chat_id"], bp.CHAT_ID)
        with patch.object(sp, "verify_bot") as verify:
            self.assertEqual(sp.run(self.cfg), 0)
            verify.assert_not_called()

    def test_slot_arguments_use_business_week_and_weekday_sections(self):
        thursday = sp.report_args(self.cfg, bp.CHANNEL, self.slot)
        friday = sp.report_args(self.cfg, bp.CHANNEL, self.slot + timedelta(days=1))
        monday = sp.report_args(self.cfg, bp.CHANNEL, self.slot + timedelta(days=4))
        self.assertEqual((thursday.period, thursday.report_type, thursday.mention_target), ("20260911期", "process", "manager"))
        self.assertFalse(thursday.no_mentions)
        self.assertEqual((friday.period, friday.report_type), ("20260911期", "both"))
        self.assertEqual((monday.period, monday.report_type), ("20260918期", "process"))

    def test_two_period_evidence_does_not_choose_maximum_period(self):
        sp.validate_context(self.context(), self.evidence(), self.cfg, self.slot)
        with self.assertRaises(ValueError):
            sp.validate_context({**self.context(), "period": "20260918期", "raw_count": 1}, self.evidence(), self.cfg, self.slot)

    def test_missing_or_extra_mentions_and_legacy_profile_are_blocked(self):
        for changes in ({"markdown": "no mentions"}, {"markdown": '<at user_id="all"></at>'},
                        {"report_profile": "standard"}, {"mention_target": "none"}, {"image_path": None},
                        {"report_type": "both"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                sp.validate_context({**self.context(), **changes}, self.evidence(), self.cfg, self.slot)
        for field, bad in (("unresolved", ["甲"]), ("nonmembers", ["甲"]), ("ambiguous", {"甲": ["ou_x"]}), ("lookup_error", "error")):
            context = self.context()
            context["mention_info"][field] = bad
            with self.assertRaises(ValueError):
                sp.validate_context(context, self.evidence(), self.cfg, self.slot)

    def log_doc(self, directory, audit=None):
        u = self.cfg["upstream"]
        stamp = self.slot.strftime("%Y-%m-%d %H:%M:%S")
        execution = {"id": 99, "taskId": 66504, "status": 6, "periodTime": stamp, "planRunTime": stamp,
                     "startTime": "2026-09-10 13:00:03", "endTime": "2026-09-10 13:10:00",
                     "runConfig": json.dumps({"execFileId": u["exec_file_id"], "triggerSourceEnum": "SCHEDULE"})}
        if audit is None:
            audit = {"schema_version": "market2lark-two-period-audit-v1", "field_count": 45, "row_count": 11,
                     "periods": {p: {"row_count": n, "channel_counts": {bp.CHANNEL: n}, "snapshots": [["20260910", "11"]],
                                     "key_sha256": "a" * 64, "records_sha256": "b" * 64}
                                 for p, n in (("20260911期", 10), ("20260918期", 1))}}
        log = ("采用dt=20260910, hour=11，延迟2小时\n"
               "目标多维表格校验通过：table_id=tbljWRvaqKTdrCx4\n"
               "数据校验通过：11行，期次20260911期、20260918期，1个渠道\n"
               "渠道分布：" + json.dumps({bp.CHANNEL: 11}, ensure_ascii=False) + "\n"
               "双期快照清单：" + json.dumps(audit) + "\n渠道映射版本：0904\n"
               "新记录回读校验通过\n旧记录删除完成：1条\n最终回读校验通过：11条\n"
               "SUCCESS: done\nexit_code:  0\n")
        raw = log.encode("utf-8")
        (directory / "stage.log").write_bytes(raw)
        doc = {"scope": u.copy(), "identity": {"name": u["owner"]}, "execution": execution,
               "execution_detail": {"status": 6}, "task_schedule": {"supervisor": u["owner"], "scheduleId": u["schedule_id"], "scheduleFrequency": "4h"},
               "stages": [{"metadata": {"statusDesc": "success", "taskId": 66504}, "log_file": "stage.log", "log_sha256": hashlib.sha256(raw).hexdigest()}]}
        return doc, audit

    def test_actual_two_period_protocol_and_cross_checks(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            doc, audit = self.log_doc(directory)
            result = sp.parse_complete_log(doc, directory, self.cfg, self.slot, doc["execution"])
            self.assertEqual(result["periods"]["20260911期"]["row_count"], 10)
            sp.validate_context(self.context(), result, self.cfg, self.slot)
            for mutate in (
                lambda a: a["periods"].pop("20260911期"),
                lambda a: a["periods"]["20260911期"].update(row_count=9),
                lambda a: a["periods"]["20260911期"].update(key_sha256="wrong"),
                lambda a: a["periods"]["20260911期"].update(snapshots=[["20260909", "11"]]),
                lambda a: a.update(field_count=44),
            ):
                bad = copy.deepcopy(audit)
                mutate(bad)
                invalid, _ = self.log_doc(directory, bad)
                with self.assertRaises(ValueError):
                    sp.parse_complete_log(invalid, directory, self.cfg, self.slot, invalid["execution"])

    def test_single_process_image_is_sent_and_cleaned_only_after_receipt(self):
        context = self.context()
        with tempfile.TemporaryDirectory() as folder:
            db = sp.connect_ledger(Path(folder))
            def cleanup(path):
                self.assertEqual(db.execute("SELECT message_id FROM deliveries").fetchone()[0], "om_mock")
                return {"deleted": True}
            with patch.object(sp, "assert_current_revision"), patch.object(sp.gp, "mention_nonmembers", return_value=[]), \
                 patch.object(sp.gp, "upload_image", return_value="img_mock") as upload, \
                 patch.object(sp.gp, "send_markdown", return_value={"message_id": "om_mock"}) as send, \
                 patch.object(sp.gp, "_cleanup_local_image", side_effect=cleanup) as clean, \
                 patch.object(sp, "receipt_readback", return_value={"verified": True}):
                self.assertTrue(sp.deliver(context, self.cfg, self.slot, db, self.evidence()))
                self.assertTrue(sp.deliver(context, self.cfg, self.slot, db, self.evidence()))
                self.assertEqual(upload.call_count, 1)
                self.assertEqual(send.call_count, 1)
                self.assertEqual(clean.call_count, 1)
            db.close()

    def test_exact_manager_mentions_are_verified_on_readback(self):
        context = self.context()
        message = {"message_id": "om_mock", "chat_id": bp.CHAT_ID, "sender": {"id": self.cfg["bot_open_id"], "name": "管家"},
                   "content": '20260911期 img_p <at user_id="ou_manager">负责人A</at>'}
        with patch.object(sp.gp, "run_lark", return_value=json.dumps({"ok": True, "data": {"messages": [message]}})):
            self.assertTrue(sp.receipt_readback("om_mock", self.cfg, context, {"process": "img_p"})["contains_mentions"])
        for text in ('20260911期 img_p', '20260911期 img_p <at user_id="all"></at>', '20260911期 img_p <at user_id="ou_other"></at>'):
            with patch.object(sp.gp, "run_lark", return_value=json.dumps({"ok": True, "data": {"messages": [{**message, "content": text}]}})), self.assertRaises(ValueError):
                sp.receipt_readback("om_mock", self.cfg, context, {"process": "img_p"})

    def test_default_preview_uses_only_read_calls_and_current_period(self):
        parser = argparse.ArgumentParser()
        gp.add_common_arguments(parser)
        args = parser.parse_args(["--no-image"])
        source = leads()
        captured = []
        def fetch(coords, parsed, fields, **kwargs):
            captured.append((fields, kwargs["filter_json"]))
            kwargs["audit"].update({"records_count": len(source), "has_more": False, "rev": 1})
            return [{key: value for key, value in row.items() if key in fields} for row in source]
        def cli(argv, **kwargs):
            if argv[:2] == ["base", "+field-list"]:
                return json.dumps({"fields": [{"name": key} for key in source[0]]})
            if argv[:2] == ["contact", "+search-user"]:
                return json.dumps({"queries": [{"query": "负责人A", "has_more": False}], "users": [{"matched_query": "负责人A", "localized_name": "负责人A", "is_activated": True, "is_cross_tenant": False, "open_id": "ou_manager"}]})
            raise AssertionError("Unexpected CLI call: " + str(argv[:2]))
        with patch.object(bp, "business_period", return_value="20260911期"), patch.object(bp, "scheduled_report_type", return_value="process"), \
             patch.object(gp, "resolve_coordinates", return_value={"base_token": "base_fixture", "table_id": args.raw_table_id, "view_id": "view_fixture"}), \
             patch.object(gp, "_fetch_view_records", side_effect=fetch), patch.object(gp, "run_lark", side_effect=cli), \
             patch.object(gp, "verify_chat", return_value={"name": "改名后的同一群", "name_changed": True}), \
             patch.object(gp, "mention_nonmembers", return_value=[]), patch.object(gp, "upload_image") as upload, patch.object(gp, "send_markdown") as send:
            context = gp.prepare(args)
        self.assertEqual(context["report_type"], "process")
        self.assertEqual(context["period"], "20260911期")
        self.assertEqual(context["mention_info"]["resolved"], {"负责人A": "ou_manager"})
        self.assertFalse(set(gr.RESULT) & set(captured[0][0]))
        self.assertEqual(captured[0][1]["conditions"], [["渠道", "==", bp.CHANNEL], ["期次", "==", "20260911期"]])
        upload.assert_not_called()
        send.assert_not_called()

    def test_local_preview_artifacts_contain_no_source_credentials(self):
        context = self.context()
        context.update(chat_name="预览群", image_geometry={}, scheduled_report_type_today="process",
                       coords={"base_token": "do-not-copy-source-resource"})
        with tempfile.TemporaryDirectory() as folder:
            context["image_path"] = Path(folder) / "p.png"
            files = gr.write_preview(context, Path(folder))
            page = Path(files["html"]).read_text(encoding="utf-8")
            metadata = Path(files["metadata"]).read_text(encoding="utf-8")
            markdown = Path(files["markdown"]).read_text(encoding="utf-8")
            self.assertIn("@负责人A", page)
            self.assertIn("不会触发@通知", page)
            self.assertIn('src="p.png"', page)
            self.assertNotIn("img_process_preview", markdown)
            self.assertNotIn("do-not-copy-source-resource", page + metadata + markdown)
            self.assertFalse(json.loads(metadata)["message_sent"])

    def test_no_image_preview_creates_new_state_directory_without_sending(self):
        context = self.context()
        context.update(chat_name="预览群", image_geometry={}, scheduled_report_type_today="process", image_path=None)
        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder) / "new-state"
            with patch.object(gp, "prepare", return_value=context), patch.object(gp, "print_preview"), \
                 patch.object(gp, "upload_image") as upload, patch.object(gp, "send_markdown") as send, redirect_stdout(io.StringIO()):
                self.assertEqual(gp.main(["preview", "--no-image", "--state-dir", str(state)]), 0)
                self.assertEqual(len(list(state.rglob("message-preview.html"))), 1)
                upload.assert_not_called()
                send.assert_not_called()


if __name__ == "__main__":
    unittest.main()
