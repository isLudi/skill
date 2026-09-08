#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Offline tests for the Base -> group process-data renderer."""

from __future__ import annotations

import sys
from copy import deepcopy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
import group_push as gp  # noqa: E402


def fixture_rows():
    return [
        {
            "record_id": "rec-1",
            "fields": {
                "期次": "20260815期",
                "顾问": "薛源02",
                "主管": "邱君武",
                "部门": "郑州市场顾问部",
                "渠道": "陈瑞春-视频号49",
                "退前线索": "177",
                "退后线索": "148",
                "线索留存率": "83.62%",
                "总通时": "1951",
                "首call完成数": "123",
                "首call率": "83.10%",
                "6h外呼": "65.50%",
                "12h外呼": "70.30%",
                "24h外呼": "83.10%",
                "48h外呼": "83.10%",
                "48h外呼数": "123",
                "外呼频次": "4.1",
                "外呼次数": "607",
                "5min": "59.50%",
                "5min线索数": "88",
                "好友率": "75.00%",
                "好友线索数": "111",
                "APP登陆率": "49.30%",
                "APP登陆线索数": "73",
                "深沟率": "26.40%",
                "深沟线索数": "39",
                "双沟率": "12.80%",
                "双沟线索数": "19",
            },
        },
        {
            "record_id": "rec-2",
            "fields": {
                "期次": "20260815期",
                "顾问": "吴志强03",
                "主管": "马会龙",
                "部门": "郑州市场顾问部",
                "渠道": "朱博士-视频号49",
                "退前线索": "63",
                "退后线索": "54",
                "线索留存率": "85.71%",
                "总通时": "858",
                "首call完成数": "42",
                "首call率": "77.80%",
                "6h外呼": "77.80%",
                "12h外呼": "77.80%",
                "24h外呼": "87.00%",
                "48h外呼": "87.00%",
                "48h外呼数": "47",
                "外呼频次": "4.6",
                "外呼次数": "248",
                "5min": "59.30%",
                "5min线索数": "32",
                "好友率": "50.00%",
                "好友线索数": "27",
                "APP登陆率": "50.00%",
                "APP登陆线索数": "27",
                "深沟率": "40.70%",
                "深沟线索数": "22",
                "双沟率": "22.20%",
                "双沟线索数": "12",
            },
        },
    ]


def fixture_text_sections():
    return {
        "过程数据": {
            "record_id": "text-1",
            "fields": {
                "说明": "过程数据",
                "推送标题": "过程数据标题",
                "推送期次": "20260815期",
                "推送说明": "过程口径说明",
                "计算_提醒顾问": "薛源02",
                "提醒": "本次5min率较低顾问：薛源02",
            },
        },
        "结果数据": {
            "record_id": "text-2",
            "fields": {
                "说明": "结果数据",
                "推送标题": "结果数据标题",
                "推送期次": "20260815期",
                "推送说明": "结果口径说明",
                "计算_提醒顾问": "吴志强03",
                "提醒": "本次单效较低顾问：吴志强03",
            },
        },
    }


def fixture_result_rows():
    return [
        {
            "record_id": "result-1",
            "fields": {
                "期次": "20260815期",
                "经理": "薛源02",
                "主管": "张旭辉",
                "退前线索": "196",
                "退后线索": "145",
                "线索留存率": "73.98%",
                "首call率": "80.69%",
                "48h外呼": "74.48%",
                "5min": "38.62%",
                "好友率": "82.76%",
                "深沟率": "78.62%",
                "双沟率": "0%",
                "首节到课率": "55.17%",
                "单效（当期）": "66.21",
                "人均报科": "2",
                "人头转化": "0.69%",
                "订单转化": "1.38%",
                "收款": "9600",
                "退费": "0",
                "退费率": "0%",
                "净收款": "9600",
                "单效": "66.21",
                "报科数": "2",
                "成交人头": "1",
                "当期净收款": "9600",
            },
        },
        {
            "record_id": "result-2",
            "fields": {
                "期次": "20260815期",
                "经理": "吴志强03",
                "主管": "李帅辉",
                "退前线索": "109",
                "退后线索": "85",
                "线索留存率": "77.98%",
                "首call率": "88.24%",
                "48h外呼": "83.53%",
                "5min": "55.29%",
                "好友率": "91.76%",
                "深沟率": "78.82%",
                "双沟率": "0%",
                "首节到课率": "63.53%",
                "单效（当期）": "42.35",
                "人均报科": "1",
                "人头转化": "1.18%",
                "订单转化": "1.18%",
                "收款": "3600",
                "退费": "14641.14",
                "退费率": "406.7%",
                "净收款": "-11041.14",
                "单效": "-129.9",
                "报科数": "1",
                "成交人头": "1",
                "当期净收款": "3600",
            },
        },
    ]


class GroupPushTests(unittest.TestCase):
    def test_image_row_filter_requires_both_counts_to_be_explicit_zero(self):
        values = [(0, 0), ("0", "0.00"), (0, 1), (1, 0), (None, 0), (0, ""), ("-", 0)]
        rows = [{"record_id": str(i), "退前线索": before, "退后线索": after, "总通时": 100}
                for i, (before, after) in enumerate(values)]
        original = deepcopy(rows)
        self.assertEqual([r["record_id"] for r in gp.visible_image_rows(rows)], ["2", "3", "4", "5", "6"])
        self.assertEqual(rows, original)

    def test_both_images_hide_zero_lead_people_but_keep_original_totals(self):
        for renderer, fixtures, total_builder in (
            (gp.render_process_image, fixture_rows, "make_total_row"),
            (gp.render_result_image, fixture_result_rows, "make_result_total_row"),
        ):
            rows = fixtures()
            rows[1]["fields"].update({"顾问": "HIDDEN_PERSON", "经理": "HIDDEN_PERSON", "主管": "HIDDEN_SUPERVISOR",
                                       "退前线索": 0, "退后线索": "0", "总通时": 777, "净收款": 400})
            original = deepcopy(rows)
            with self.subTest(renderer=renderer.__name__), tempfile.TemporaryDirectory() as directory:
                with patch.object(gp, total_builder, wraps=getattr(gp, total_builder)) as totals, patch.object(gp, "_center_text", wraps=gp._center_text) as labels:
                    path = renderer(rows, Path(directory) / "preview.png")
                totals.assert_called_once_with(rows, "20260815期")
                displayed = [call.args[2] for call in labels.call_args_list]
                self.assertNotIn("HIDDEN_PERSON", displayed)
                self.assertNotIn("HIDDEN_SUPERVISOR", displayed)
                self.assertIn("2728" if renderer == gp.render_process_image else "10000", displayed)
                from PIL import Image
                with Image.open(path) as image:
                    self.assertEqual(image.height, 92 + 64 + 70)
            self.assertEqual(rows, original)

    def test_all_hidden_rows_render_total_only_and_honor_supplied_total(self):
        row = {"fields": {"期次": "20260911期", "顾问": "HIDDEN_PERSON", "经理": "HIDDEN_PERSON",
                          "主管": "HIDDEN_PERSON", "退前线索": 0, "退后线索": 0, "总通时": 200}}
        total = {"fields": {"期次": "总计", "退前线索": 0, "退后线索": 0, "总通时": 987, "净收款": 987}}
        for renderer in (gp.render_process_image, gp.render_result_image):
            with self.subTest(renderer=renderer.__name__), tempfile.TemporaryDirectory() as directory:
                with patch.object(gp, "_center_text", wraps=gp._center_text) as labels:
                    path = renderer([row], Path(directory) / "preview.png", total=total)
                displayed = [call.args[2] for call in labels.call_args_list]
                self.assertNotIn("HIDDEN_PERSON", displayed)
                self.assertIn("987", displayed)
                from PIL import Image
                with Image.open(path) as image:
                    self.assertEqual(image.height, 92 + 70)

    def test_process_whitelist_excludes_outcomes(self):
        self.assertTrue(gp.PROCESS_FIELDS)
        self.assertFalse(any(term in field for field in gp.PROCESS_FIELDS for term in gp.OUTCOME_TERMS))
        total = gp.make_total_row(fixture_rows(), "20260815期")
        self.assertNotIn("收款", total["fields"])
        self.assertNotIn("成交", total["fields"])
        self.assertEqual(gp._format_rate(total["fields"]["线索留存率"]), "84.17%")

    def test_rate_preserves_percentages_above_100(self):
        self.assertEqual(gp._format_rate("406.7%"), "406.70%")

    def test_result_aggregation_and_image_matches_reference_shape(self):
        rows = gp.aggregate_result_rows(fixture_result_rows(), "20260815期")
        self.assertEqual(len(rows), 2)
        self.assertEqual(gp._string(gp._raw_field(rows[0], "经理")), "薛源02")
        self.assertEqual(gp._format_value(gp._raw_field(rows[0], "单效"), "number"), "66.21")
        total = gp.make_result_total_row(rows, "20260815期")
        self.assertEqual(gp._format_value(gp._raw_field(total, "退前线索"), "count"), "305")
        self.assertEqual(gp._format_value(gp._raw_field(total, "退后线索"), "count"), "230")
        self.assertEqual(gp._format_value(gp._raw_field(total, "净收款"), "amount"), "-1441.14")
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = gp.render_result_image(rows, Path(temp_dir) / "result.png")
            from PIL import Image

            with Image.open(image_path) as image:
                self.assertEqual(image.width, sum(gp.RESULT_IMAGE_WIDTHS[source] for source, _label, _kind in gp.RESULT_IMAGE_COLUMNS))
                self.assertEqual(image.height, 92 + 64 * 2 + 70)
                self.assertEqual(image.getpixel((10, 10)), (32, 59, 114))

    def test_markdown_contains_image_data_and_exact_mentions(self):
        rows = fixture_rows()
        mentions = gp.resolve_mentions(rows, mention_map={"薛源02": "ou_consultant", "邱君武": "ou_supervisor"}, no_lookup=True, timeout=1)
        markdown = gp.build_markdown(rows, period="20260815期", source_label="IP播报_主管 / 过程数据 / lark-cli", mention_info=mentions, image_ref="img_preview")
        self.assertIn("![IP过程数据表](img_preview)", markdown)
        self.assertIn('<at user_id="ou_consultant">薛源02</at>', markdown)
        self.assertIn('<at user_id="ou_supervisor">邱君武</at>', markdown)
        self.assertIn("退前线索", markdown)
        self.assertIn("线索留存率", markdown)
        self.assertIn("不含收款、成交、退费、单效", markdown)
        self.assertNotIn("收款：", markdown)
        self.assertNotIn("成交：", markdown)

    def test_idempotency_is_stable_and_bounded(self):
        coords = {"base_token": "base", "table_id": "tbl", "view_id": "vew"}
        first = gp.idempotency_key(coords, "oc_chat", "20260815期", fixture_rows())
        second = gp.idempotency_key(coords, "oc_chat", "20260815期", fixture_rows())
        changed = gp.idempotency_key(coords, "oc_chat", "20260816期", fixture_rows())
        self.assertEqual(first, second)
        self.assertNotEqual(first, changed)
        self.assertLessEqual(len(first), 50)

    def test_image_matches_wide_table_shape(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = gp.render_process_image(fixture_rows(), Path(temp_dir) / "process.png")
            from PIL import Image

            with Image.open(image_path) as image:
                self.assertEqual(image.width, 2940)
                self.assertEqual(image.height, 92 + 64 * 2 + 70)
                self.assertEqual(image.getpixel((10, 10)), (32, 59, 114))

    def test_local_image_cleanup_deletes_png_after_delivery(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "process.png"
            image_path.write_bytes(b"png-placeholder")
            result = gp._cleanup_local_image(image_path)
            self.assertTrue(result["deleted"])
            self.assertEqual(result["status"], "deleted")
            self.assertFalse(image_path.exists())

    def test_send_deletes_png_only_after_message_id(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "process.png"
            image_path.write_bytes(b"png-placeholder")
            context = {
                "mention_info": {"lookup_error": "", "unresolved": [], "ambiguous": {}},
                "chat_id": "oc_chat",
                "markdown": "![IP过程数据表](img_preview)",
                "idempotency_key": "ipproc-test",
                "identity": "user",
                "image_path": image_path,
                "ledger": Path(temp_dir) / "ledger.jsonl",
                "period": "20260815期",
            }
            with patch.object(gp, "prepare", return_value=context), patch.object(
                gp, "_ledger_records", return_value={}
            ), patch.object(gp, "upload_image", return_value="img_test") as upload, patch.object(
                gp, "send_markdown", return_value={"message_id": "om_test"}
            ) as send:
                self.assertEqual(gp.main(["send", "--confirm-send", "--chat-id", "oc_chat"]), 0)
            upload.assert_called_once()
            send.assert_called_once()
            self.assertFalse(image_path.exists())

    def test_send_deletes_process_and_result_png_after_message_id(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            process_path = Path(temp_dir) / "process.png"
            result_path = Path(temp_dir) / "result.png"
            process_path.write_bytes(b"process-placeholder")
            result_path.write_bytes(b"result-placeholder")
            context = {
                "mention_info": {"lookup_error": "", "unresolved": [], "ambiguous": {}},
                "chat_id": "oc_chat",
                "markdown": "![IP过程数据表](img_process_preview)\n![IP结果数据表](img_result_preview)",
                "idempotency_key": "ipproc-two-images",
                "identity": "user",
                "image_path": process_path,
                "result_image_path": result_path,
                "ledger": Path(temp_dir) / "ledger.jsonl",
                "period": "20260815期",
            }
            with patch.object(gp, "prepare", return_value=context), patch.object(
                gp, "_ledger_records", return_value={}
            ), patch.object(
                gp, "upload_image", side_effect=["img_process", "img_result"]
            ) as upload, patch.object(gp, "send_markdown", return_value={"message_id": "om_two"}) as send:
                self.assertEqual(gp.main(["send", "--confirm-send", "--chat-id", "oc_chat"]), 0)
            self.assertEqual(upload.call_count, 2)
            send.assert_called_once()
            sent_markdown = send.call_args.args[1]
            self.assertIn("![IP过程数据表](img_process)", sent_markdown)
            self.assertIn("![IP结果数据表](img_result)", sent_markdown)
            self.assertFalse(process_path.exists())
            self.assertFalse(result_path.exists())

    def test_send_failure_keeps_png_for_retry(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "process.png"
            image_path.write_bytes(b"png-placeholder")
            context = {
                "mention_info": {"lookup_error": "", "unresolved": [], "ambiguous": {}},
                "chat_id": "oc_chat",
                "markdown": "![IP过程数据表](img_preview)",
                "idempotency_key": "ipproc-test-failure",
                "identity": "user",
                "image_path": image_path,
                "ledger": Path(temp_dir) / "ledger.jsonl",
                "period": "20260815期",
            }
            with patch.object(gp, "prepare", return_value=context), patch.object(
                gp, "_ledger_records", return_value={}
            ), patch.object(gp, "upload_image", return_value="img_test"), patch.object(
                gp, "send_markdown", side_effect=RuntimeError("send failed")
            ):
                with self.assertRaises(RuntimeError):
                    gp.main(["send", "--confirm-send", "--chat-id", "oc_chat"])
            self.assertTrue(image_path.exists())

    def test_missing_optional_hour_columns_are_not_rendered_blank(self):
        rows = fixture_rows()
        for row in rows:
            for field in ("6h外呼", "12h外呼", "24h外呼"):
                row["fields"].pop(field, None)
        labels = [label for _source, label, _kind in gp.available_image_columns(rows)]
        self.assertNotIn("6h外呼", labels)
        self.assertNotIn("12h外呼", labels)
        self.assertNotIn("24h外呼", labels)
        mentions = gp.resolve_mentions(rows, mention_map={}, no_lookup=True, timeout=1)
        markdown = gp.build_markdown(rows, period="20260815期", source_label="safe", mention_info=mentions, image_ref=None)
        self.assertNotIn("6h=", markdown)
        self.assertNotIn("12h=", markdown)
        self.assertNotIn("24h=", markdown)

    def test_configured_markdown_uses_text_table_and_result_image(self):
        rows = fixture_rows()
        sections = fixture_text_sections()
        names = [name for row in sections.values() for name in gp.reminder_names(row)]
        mentions = gp.resolve_mentions(
            [],
            mention_map={"薛源02": "ou_consultant", "吴志强03": "ou_result"},
            no_lookup=True,
            extra_names=names,
            timeout=1,
        )
        markdown = gp.build_markdown(
            rows,
            period="20260815期",
            source_label="safe",
            mention_info=mentions,
            image_ref="img_preview",
            text_sections=sections,
            result_image_ref="result_preview",
        )
        self.assertIn("## 过程数据标题", markdown)
        self.assertIn("![IP过程数据表](img_preview)", markdown)
        self.assertIn("## 结果数据标题", markdown)
        self.assertIn("![IP结果数据表](result_preview)", markdown)
        self.assertIn('<at user_id="ou_result">吴志强03</at>', markdown)
        self.assertIn("数据来源：safe", markdown)
        self.assertNotIn("结果图片来自 IP播报_主管", markdown)

    def test_idempotency_changes_when_text_config_changes(self):
        coords = {"base_token": "base", "table_id": "tbl", "view_id": "vew"}
        sections = fixture_text_sections()
        first = gp.idempotency_key(coords, "oc_chat", "20260815期", fixture_rows(), text_sections=sections)
        sections["过程数据"]["fields"]["推送说明"] = "changed"
        changed = gp.idempotency_key(coords, "oc_chat", "20260815期", fixture_rows(), text_sections=sections)
        self.assertNotEqual(first, changed)


if __name__ == "__main__":
    unittest.main()
