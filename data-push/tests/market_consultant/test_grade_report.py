"""Offline compact report, manager ranking and calendar tests; no real messages."""
from datetime import date, datetime, timezone
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import broadcast_policy as bp
import grade_report as gr
import group_push as gp


def leads(grade="高一", manager="负责人A", supervisor="主管A", count=10, long_calls=5, net=0):
    return [{"lead_id": f"{grade}-{manager}-{supervisor}-{i}", "期次": "20260911期", "渠道": bp.CHANNEL,
             "年级": grade, "经理": manager, "主管": supervisor, "分区日期": "20260910", "分区小时": "11",
             "退前线索": 1, "退后线索": 1, "首call完成标记": 1, "48h外呼标记": 1,
             "5min标记": int(i < long_calls), "好友标记": 1, "深沟标记": 0, "双沟标记": 0,
             "首节到课标记": 0, "当期净收款": 0, "净收款": net} for i in range(count)]


def build(rows, kind="both"):
    _, counters = gr.projection(set(rows[0]), kind)
    gr.validate_scope(rows, bp.CHANNEL, "20260911期")
    return gr.build_report(rows, counters, "20260911期", kind)


class GradeReportTests(unittest.TestCase):
    def test_entire_week_uses_friday_period(self):
        for day in range(7, 14):
            self.assertEqual(bp.business_period(date(2026, 9, day)), "20260911期")
        self.assertEqual(bp.business_period(date(2026, 9, 14)), "20260918期")

    def test_week_year_boundary(self):
        self.assertEqual(bp.business_period(date(2026, 12, 28)), "20270101期")
        self.assertEqual(bp.business_period(date(2027, 1, 3)), "20270101期")

    def test_china_midnight_and_naive_time(self):
        self.assertEqual(bp.business_period(datetime(2026, 9, 13, 16, 1, tzinfo=timezone.utc)), "20260918期")
        with self.assertRaises(ValueError):
            bp.business_period(datetime(2026, 9, 10))

    def test_result_only_friday_to_sunday(self):
        for day in range(7, 14):
            self.assertEqual(bp.scheduled_report_type(date(2026, 9, day)), "both" if day >= 11 else "process")
        with self.assertRaises(ValueError):
            bp.enforce_live_calendar("20260918期", "process", date(2026, 9, 10))
        with self.assertRaises(ValueError):
            bp.enforce_live_calendar("20260911期", "both", date(2026, 9, 10))

    def test_fixed_group_channel_guard(self):
        bp.enforce_group_scope(bp.CHAT_ID, bp.CHANNEL, bp.PROFILE)
        for channel, profile in (("KOC-周帅数学", bp.PROFILE), (bp.CHANNEL, "standard")):
            with self.assertRaises(ValueError):
                bp.enforce_group_scope(bp.CHAT_ID, channel, profile)

    def test_exact_compact_columns(self):
        self.assertEqual([c[1] for c in gr.COLUMNS["process"]], ["期次", "负责人", "退后线索", "首call", "48h外呼", "5min", "好友率", "深沟率", "双沟率"])
        self.assertEqual([c[1] for c in gr.COLUMNS["result"]], ["期次", "负责人", "退后线索", "首节到课率", "单效（当期）", "单效"])

    def test_process_does_not_read_conversion_fields(self):
        fields, _ = gr.projection(set(leads()[0]), "process")
        self.assertFalse(set(gr.RESULT) & set(fields))
        self.assertIn("年级", fields)
        self.assertNotIn("主管", fields)

    def test_manager_ranking_not_minimum_supervisor_row_or_mean_rate(self):
        rows = leads(manager="A", supervisor="A1", count=1, long_calls=0)
        rows += leads(manager="A", supervisor="A2", count=19, long_calls=17)
        rows += leads(manager="B", count=20, long_calls=10)
        report = build(rows)
        block = report["blocks"][0]
        self.assertEqual(len(block["rows"]), 2)
        self.assertTrue(all("主管" not in row["fields"] for row in block["rows"]))
        manager_a = next(row for row in block["rows"] if row["fields"]["负责人"] == "A")
        self.assertEqual(manager_a["fields"]["退后线索"], 20)
        self.assertEqual(block["reminders"]["process"], ["B"])
        self.assertAlmostEqual(block["manager_metrics"]["process"]["A"]["value"], .85)

    def test_all_exact_ties_included(self):
        report = build(leads(manager="A", count=3, long_calls=1) + leads(manager="B", count=6, long_calls=2) + leads(manager="C", count=10, long_calls=9))
        self.assertEqual(report["blocks"][0]["reminders"]["process"], ["A", "B"])

    def test_ranking_does_not_round_before_comparison(self):
        report = build(leads(manager="A", count=333, long_calls=1) + leads(manager="B", count=665, long_calls=2))
        self.assertEqual(report["blocks"][0]["reminders"]["process"], ["A"])

    def test_result_uses_total_effect_not_current_period_effect(self):
        rows = leads(manager="A", net=-10) + leads(manager="B", net=2)
        for row in rows:
            row["当期净收款"] = 100 if row["经理"] == "A" else -100
        block = build(rows)["blocks"][0]
        self.assertEqual(block["reminders"]["result"], ["A"])

    def test_all_zero_result_ties_all_eligible_managers(self):
        block = build(leads(manager="A") + leads(manager="B"))["blocks"][0]
        self.assertEqual(block["reminders"]["result"], ["A", "B"])

    def test_grade_scope_excludes_chu2_and_small_grades_from_both_parts(self):
        report = build(leads("初二", count=20) + leads("初三", count=10) + leads("高二", count=9))
        self.assertEqual([b["grade"] for b in report["blocks"]], ["初三"])
        self.assertEqual(report["excluded_grade_counts"], {"初二": 20})
        self.assertEqual(report["omitted_grades"][0]["grade"], "高二")

    def test_threshold_is_post_leads_not_raw_count(self):
        rows = leads(count=20)
        for row in rows[9:]:
            row["退后线索"] = 0
        with self.assertRaisesRegex(ValueError, "无可推送年级"):
            build(rows)

    def test_zero_denominator_manager_not_ranked(self):
        rows = leads(manager="A") + leads(manager="Z", count=1, long_calls=0)
        rows[-1]["退后线索"] = 0
        block = build(rows)["blocks"][0]
        self.assertEqual(block["reminders"]["process"], ["A"])

    def test_missing_current_period_never_falls_back(self):
        with self.assertRaises(ValueError):
            gr.validate_scope(leads(), bp.CHANNEL, "20260918期")
        with self.assertRaises(ValueError):
            gr.validate_scope([], bp.CHANNEL, "20260911期")

    def test_duplicate_and_mixed_snapshot_rejected(self):
        rows = leads()
        with self.assertRaises(ValueError):
            gr.validate_scope(rows + [rows[0]], bp.CHANNEL, "20260911期")
        rows[0]["分区小时"] = "10"
        with self.assertRaises(ValueError):
            gr.validate_scope(rows, bp.CHANNEL, "20260911期")

    def candidate(self, name="薛源", email="xueyuan02@gaotu.cn", open_id="ou_one"):
        return {"matched_query": name, "localized_name": name, "enterprise_email": email, "open_id": open_id,
                "is_activated": True, "is_cross_tenant": False}

    def test_numeric_alias_requires_exact_email_suffix_and_unique_result(self):
        payload = {"queries": [{"query": "薛源", "has_more": False}], "users": [self.candidate()]}
        self.assertEqual(gr.resolve_manager_candidates(["薛源02"], payload)["resolved"], {"薛源02": "ou_one"})
        payload["users"][0]["enterprise_email"] = "xueyuan12@gaotu.cn"
        self.assertEqual(gr.resolve_manager_candidates(["薛源02"], payload)["unresolved"], ["薛源02"])

    def test_ambiguous_or_incomplete_contact_is_not_selected(self):
        payload = {"queries": [{"query": "薛源", "has_more": False}], "users": [self.candidate(), self.candidate(open_id="ou_two")]}
        self.assertIn("薛源02", gr.resolve_manager_candidates(["薛源02"], payload)["ambiguous"])
        payload["queries"][0]["has_more"] = True
        self.assertFalse(gr.resolve_manager_candidates(["薛源02"], payload)["resolved"])

    def test_chat_rename_keeps_fixed_id_and_never_searches_name(self):
        with patch.object(gp, "run_lark", return_value=json.dumps({"ok": True, "data": {"name": "新群名", "chat_mode": "group"}})) as call:
            result = gp.verify_chat(bp.CHAT_ID, "旧群名", "bot", 60)
        self.assertTrue(result["name_changed"])
        self.assertEqual(result["chat_id"], bp.CHAT_ID)
        argv = call.call_args.args[0]
        self.assertNotIn("+chat-search", argv)
        self.assertEqual(json.loads(argv[argv.index("--params") + 1])["chat_id"], bp.CHAT_ID)

    def test_brief_markdown_only_period_and_grade_mentions(self):
        report = build(leads())
        info = {"resolved": {"负责人A": "ou_test"}, "display_names": {"负责人A": "真实姓名"}}
        md = gr.build_markdown(report, "20260911期", bp.CHANNEL, "process", info, {"process": "img_process_preview"})
        self.assertIn('<at user_id="ou_test">真实姓名</at>', md)
        self.assertNotIn("提醒规则", md)
        self.assertNotIn("退前线索", md)
        self.assertNotIn("后25%", md)
        self.assertEqual(len([line for line in md.splitlines() if line.startswith("- ")]), 2)

    def test_multiple_grade_tables_share_one_image(self):
        report = build(leads("初三") + leads("高一") + leads("高二") + leads("高三"))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "p.png"
            geometry = gr.render_image(report, "process", path, font_loader=gp._find_font,
                                       center_text=gp._center_text, format_value=gp._format_value)
            self.assertTrue(path.is_file())
            self.assertEqual(len(geometry), 4)
            self.assertTrue(all(b["top"] >= a["top"] + a["height"] for a, b in zip(geometry, geometry[1:])))

    def test_each_grade_has_independent_descending_metric_order(self):
        rows = leads(manager="A", long_calls=2, net=30) + leads(manager="B", long_calls=8, net=-10)
        block = build(rows)["blocks"][0]
        self.assertEqual([r["fields"]["负责人"] for r in gr.sorted_rows(block, "process")], ["B", "A"])
        self.assertEqual([r["fields"]["负责人"] for r in gr.sorted_rows(block, "result")], ["A", "B"])

    def test_result_cells_reuse_original_effect_color_blocks(self):
        from PIL import Image
        report = build(leads(manager="A", net=-10) + leads(manager="B", net=250))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "result.png"
            gr.render_image(report, "result", path, font_loader=gp._find_font,
                            center_text=gp._center_text, format_value=gp._format_value, cell_fill=gp._result_cell_fill)
            with Image.open(path) as image:
                x = sum(gr.WIDTHS["result"][:-1]) + 8
                self.assertEqual(image.getpixel((x, 52 + 64 + 6)), (98, 188, 127))
                self.assertEqual(image.getpixel((x, 52 + 64 + 54 + 6)), (251, 98, 107))

    def test_native_and_inline_mentions_have_same_account_set(self):
        self.assertEqual(gr.mention_ids({'zh_cn': {'content': [[{'tag': 'at', 'user_id': 'ou_x'}]]}}), {'ou_x'})
        self.assertEqual(gr.mention_ids(json.dumps({'text': '<at user_id="ou_x">甲</at>'})), {'ou_x'})
        self.assertEqual(gr.mention_ids({'mentions': [{'id': 'ou_x'}]}), {'ou_x'})
        self.assertIn('all', gr.mention_ids('<at user_id="all">所有人</at>'))


if __name__ == "__main__":
    unittest.main()
