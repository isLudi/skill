import unittest
from pathlib import Path
import tempfile

from lark_delivery.domains.market_consultant import volume_report as vr


def record(**fields):
    return {"fields": fields}


class VolumeReportTests(unittest.TestCase):
    def test_filters_latest_period_and_eligible_channels(self):
        rows = [record(期次="20260911期", 渠道="koc自孵化下引"),
                record(期次="20260918期", 渠道="自孵化KOC-5元纯课"),
                record(期次="20260925期", 渠道="自孵化KOC下引"),
                record(期次="20260925期", 渠道="KOC-周帅数学"),
                record(期次="20260925期", 渠道="自孵化渠道")]
        self.assertEqual(vr.latest_period(rows), "20260925期")
        self.assertTrue(vr.eligible_channel("ＫＯＣ自孵化下引"))
        self.assertFalse(vr.eligible_channel("KOC-周帅数学"))
        self.assertFalse(vr.eligible_channel("自孵化渠道"))
        self.assertTrue(vr.eligible_channel("自孵化KOC下引"))

    def test_business_rule_contains_koc_but_excludes_self_incubated(self):
        rule = vr.RULE_KOC_NOT_SELF_INCUBATED
        self.assertTrue(vr.eligible_channel("KOC-周帅数学", rule))
        self.assertTrue(vr.eligible_channel("koc常规5元", rule))
        self.assertTrue(vr.eligible_channel("ＫＯＣ-孟亚飞数学", rule))
        self.assertFalse(vr.eligible_channel("自孵化KOC-5元纯课", rule))
        self.assertFalse(vr.eligible_channel("koc自孵化下引", rule))
        self.assertFalse(vr.eligible_channel("商务常规渠道", rule))

    def test_business_rule_is_dynamic_and_controls_latest_period_and_pivot(self):
        rule = vr.RULE_KOC_NOT_SELF_INCUBATED
        rows = [
            record(期次="20260918期", 年级="高一", 渠道="未来新增Koc渠道", 预估量级=20, 实际进量=10,
                   退前线索=10, 退后线索=8, 接量顾问数=2),
            record(期次="20260925期", 年级="高一", 渠道="kOc常规新品", 预估量级=30, 实际进量=15,
                   退前线索=15, 退后线索=12, 接量顾问数=3),
            record(期次="20261002期", 年级="高一", 渠道="自孵化KOC新品", 预估量级=99, 实际进量=99,
                   退前线索=99, 退后线索=99, 接量顾问数=1),
        ]
        self.assertEqual(vr.latest_period(rows, rule), "20260925期")
        result, channels, dimensions = vr.aggregate_volume(rows, "20260925期", rule)
        self.assertEqual(channels, {"kOc常规新品"})
        self.assertEqual(dimensions, {("kOc常规新品", "高一")})
        self.assertEqual(result[0]["实际进量"], 15)

    def test_unknown_channel_rule_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "未审核"):
            vr.eligible_channel("KOC-A", "contains_koc_or_anything")

    def test_derived_metrics_are_recomputed_after_grade_pivot(self):
        rows = [
            record(期次="20260918期", 年级="初三", 渠道="koc自孵化下引", 预估量级=100, 实际进量=50,
                   退前线索=100, 退后线索=50, 接量顾问数=10, 线索留存率=0.5, 人均带班=5, 量级完成度=0.5),
            record(期次="20260918期", 年级="初三", 渠道="自孵化KOC-5元纯课", 预估量级=300, 实际进量=240,
                   退前线索=300, 退后线索=270, 接量顾问数=20, 线索留存率=0.9, 人均带班=12, 量级完成度=0.8),
        ]
        result, channels, dimensions = vr.aggregate_volume(rows, "20260918期")
        self.assertEqual(len(result), 1)
        row = result[0]
        self.assertAlmostEqual(row["线索留存率"], 320 / 400)
        self.assertAlmostEqual(row["人均带班"], 290 / 30)
        self.assertAlmostEqual(row["量级完成度"], 290 / 400)
        self.assertNotEqual(row["线索留存率"], 0.5 + 0.9)
        self.assertEqual(channels, {"koc自孵化下引", "自孵化KOC-5元纯课"})
        self.assertEqual(dimensions, {("koc自孵化下引", "初三"), ("自孵化KOC-5元纯课", "初三")})

    def test_zero_lead_placeholder_affects_forecast_but_not_abnormal_dimensions(self):
        rows = [record(期次="20260918期", 年级="高一", 渠道="koc自孵化下引", 预估量级=10, 实际进量=0,
                       退前线索=0, 退后线索=0, 接量顾问数=4)]
        result, channels, dimensions = vr.aggregate_volume(rows, "20260918期")
        self.assertEqual(result[0]["预估量级"], 10)
        self.assertEqual(result[0]["实际进量"], 0)
        self.assertEqual(result[0]["量级完成度"], 0)
        self.assertEqual(channels, {"koc自孵化下引"})
        self.assertEqual(dimensions, set())

    def test_grade_rows_use_fixed_ascending_order(self):
        rows = [record(期次="20260918期", 年级=grade, 渠道="koc自孵化下引", 预估量级=100, 实际进量=actual,
                       退前线索=100, 退后线索=actual, 接量顾问数=10)
                for grade, actual in (("高三", 99), ("高一", 20), ("初三", 80), ("高二", 50))]
        result, _, _ = vr.aggregate_volume(rows, "20260918期")
        self.assertEqual([row["年级"] for row in result], ["初三", "高一", "高二", "高三"])

    def test_grade_rows_start_at_high_one_when_grade_nine_is_absent(self):
        rows = [record(期次="20260918期", 年级=grade, 渠道="koc自孵化下引", 预估量级=100, 实际进量=50,
                       退前线索=100, 退后线索=50, 接量顾问数=10)
                for grade in ("高三", "高二", "高一")]
        result, _, _ = vr.aggregate_volume(rows, "20260918期")
        self.assertEqual([row["年级"] for row in result], ["高一", "高二", "高三"])

    def test_abnormal_ratio_uses_exact_period_channel_grade_then_divides(self):
        rows = [record(期次="20260918期", 渠道="KOC-A", 年级="初三", 异常流量标记=1),
                record(期次="20260918期", 渠道="KOC-A", 年级="初三", 异常流量标记=0),
                record(期次="20260918期", 渠道="自孵化B", 年级="初三", 异常流量标记=1),
                record(期次="20260918期", 渠道="其他", 年级="初三", 异常流量标记=1),
                record(期次="20260911期", 渠道="KOC-A", 年级="初三", 异常流量标记=1),
                record(期次="20260918期", 渠道="KOC-A", 年级="高一", 异常流量标记=1)]
        result, audit = vr.aggregate_abnormal(rows, "20260918期", {"KOC-A", "自孵化B"},
                                                {("KOC-A", "初三"), ("自孵化B", "初三")})
        self.assertAlmostEqual(result["初三"]["异常流量占比"], 2 / 3)
        self.assertEqual(result["初三"]["线索量"], 3)
        self.assertEqual(audit["matched_dimensions"], 2)
        self.assertEqual(audit["missing_dimensions"], [])

    def test_markdown_names_lowest_grade_and_lists_every_grade_abnormal_ratio(self):
        rows = [{"年级": grade, "量级完成度": completion} for grade, completion in
                (("初三", .8), ("高一", .4), ("高二", .6), ("高三", .2))]
        abnormal = {grade: {"异常流量占比": ratio} for grade, ratio in
                    (("初三", .1), ("高一", .2), ("高二", .3), ("高三", .4))}
        text = vr.build_markdown("20260918期", rows, abnormal)
        self.assertIn("重点关注量级进展较慢的年级：高三", text)
        self.assertNotIn("重点关注量级进展较慢的年级：高三（", text)
        self.assertIn("重点关注量级进展较慢的年级：高三\n\n初三异常流量占比", text)
        self.assertIn("高三异常流量占比：40.00%", text)
        self.assertIn("高一异常流量占比：20.00%", text)
        self.assertIn("高二异常流量占比：30.00%", text)
        self.assertIn("初三异常流量占比：10.00%", text)
        self.assertLess(text.index("初三异常流量占比"), text.index("高一异常流量占比"))
        self.assertLess(text.index("高一异常流量占比"), text.index("高二异常流量占比"))
        self.assertLess(text.index("高二异常流量占比"), text.index("高三异常流量占比"))

    def test_total_row_recalculates_derived_metrics_from_additive_components(self):
        rows = [
            {"期次": "20260918期", "年级": "初三", "预估量级": 100, "实际进量": 50,
             "_退前线索": 100, "_退后线索": 50, "_接量顾问数": 10},
            {"期次": "20260918期", "年级": "高一", "预估量级": 300, "实际进量": 240,
             "_退前线索": 300, "_退后线索": 270, "_接量顾问数": 20},
        ]
        total = vr.build_total_row(rows)
        self.assertEqual(total["年级"], "总计")
        self.assertEqual(total["预估量级"], 400)
        self.assertEqual(total["实际进量"], 290)
        self.assertAlmostEqual(total["线索留存率"], 320 / 400)
        self.assertAlmostEqual(total["人均带班"], 290 / 30)
        self.assertAlmostEqual(total["量级完成度"], 290 / 400)

    def test_image_metadata_uses_reviewed_colors_and_progress_bars(self):
        rows = [{"期次": "20260918期", "年级": "初三", "预估量级": 100, "实际进量": 80,
                 "线索留存率": .9, "人均带班": 8.0, "量级完成度": .8,
                 "_退前线索": 100, "_退后线索": 90, "_接量顾问数": 10}]
        with tempfile.TemporaryDirectory() as temp_dir:
            metadata = vr.render_image(rows, Path(temp_dir) / "preview.png")
        self.assertEqual(metadata["sort"], "年级固定升序，总计置底")
        self.assertEqual(metadata["total_row_count"], 1)
        self.assertEqual(metadata["total_row"]["年级"], "总计")
        self.assertEqual(metadata["progress_bar_fields"], ["线索留存率", "量级完成度"])
        self.assertEqual(metadata["progress_bar_colors"],
                         {"线索留存率": "#4f78ae", "量级完成度": "#f5ae23"})
        self.assertEqual(metadata["colors"]["header"], "#203b72")
        self.assertEqual(metadata["colors"]["body_text"], "#111827")

    def test_shared_image_slots_include_volume_placeholder(self):
        from lark_delivery.common import images
        path = Path("volume.png")
        slots = images._image_slots({"volume_image_path": path})
        self.assertIn(("volume", path, ("img_volume_preview",)), slots)


if __name__ == "__main__":
    unittest.main()
