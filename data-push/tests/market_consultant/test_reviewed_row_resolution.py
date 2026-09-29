"""Reviewed 2026-09-28 resolutions for two upstream data defects.

Defect A: one lead reassigned upstream arrives as two rows sharing (期次, lead_id).
Defect B: 规则 values that cannot resolve an assignment channel.

Both used to stop a whole channel (or a whole volume batch). These lock in the
reviewed narrowing: keep the row that still carries the lead markers, and skip
unparseable rule rows while counting them.
"""
import unittest

from lark_delivery.domains.market_consultant import grade_report
from lark_delivery.domains.market_consultant import volume_report as vr
from lark_delivery.domains.market_consultant import workflow as wf

PERIOD = "20261002期"


def lead_row(supervisor="张宏胜", pre=1, post=0, **extra):
    row = {"lead_id": "334814970", "期次": PERIOD, "渠道": "KOC-周帅数学", "经理": "靳煜08",
           "年级": "高一", "分区日期": "20260928", "分区小时": "19",
           "主管": supervisor, "顾问": "李泽乾01", "退前线索": pre, "退后线索": post,
           "record_id": "rec_" + supervisor}
    row.update(extra)
    return row


class DuplicateLeadIdMergeTests(unittest.TestCase):
    def test_keeps_the_row_that_still_carries_the_markers(self):
        superseded = lead_row(supervisor="左颖雪", pre=0, post=0)
        marked = lead_row(supervisor="张宏胜", pre=1, post=0)
        audit = {}
        self.assertEqual(wf.merge_duplicate_lead_ids([superseded, marked], audit), [marked])
        self.assertEqual([entry["主管"] for entry in audit["duplicate_lead_id_merged"]], ["左颖雪"])

    def test_marker_row_wins_regardless_of_read_order(self):
        superseded = lead_row(supervisor="左颖雪", pre=0, post=0)
        marked = lead_row(supervisor="张宏胜", pre=1, post=0)
        self.assertEqual(wf.merge_duplicate_lead_ids([marked, superseded], {}), [marked])

    def test_tie_falls_back_to_the_first_row_read(self):
        first = lead_row(supervisor="左颖雪", pre=0, post=0)
        second = lead_row(supervisor="张宏胜", pre=0, post=0)
        self.assertEqual(wf.merge_duplicate_lead_ids([first, second], {}), [first])

    def test_rows_without_duplicates_are_returned_untouched(self):
        rows = [lead_row(), lead_row(lead_id="2", supervisor="左颖雪")]
        audit = {}
        self.assertIs(wf.merge_duplicate_lead_ids(rows, audit), rows)
        self.assertNotIn("duplicate_lead_id_merged", audit)

    def test_merge_evidence_names_every_dropped_row(self):
        audit = {}
        wf.merge_duplicate_lead_ids([lead_row(supervisor="左颖雪", pre=0, post=0), lead_row(pre=1)], audit)
        entry = audit["duplicate_lead_id_merged"][0]
        self.assertEqual(set(entry), set(wf.DEDUP_EVIDENCE_FIELDS))
        self.assertEqual(entry["record_id"], "rec_左颖雪")

    def test_the_original_duplicate_still_fails_closed_without_the_merge(self):
        # Reproduces the 2026-09-28 outage, then shows the merge clears it.
        duplicates = [lead_row(supervisor="左颖雪", pre=0, post=0), lead_row(pre=1)]
        with self.assertRaisesRegex(ValueError, "重复"):
            grade_report.validate_scope(duplicates, "KOC-周帅数学", PERIOD)
        merged = wf.merge_duplicate_lead_ids(duplicates, {})
        self.assertEqual(grade_report.validate_scope(merged, "KOC-周帅数学", PERIOD), ["20260928", "19"])


class UnparseableRuleRowTests(unittest.TestCase):
    CHANNEL = "koc常规线索复用"

    def record(self, **fields):
        return {"fields": fields}

    def good(self, grade="高一", flag=1):
        return self.record(期次=PERIOD, 规则=f"1002期-复用-{self.CHANNEL}-{grade}", 年级=grade, 异常流量标记=flag)

    def fallback(self, flag=1):
        return self.record(期次=PERIOD, 规则="未识别规则", 年级="未识别年级", 异常流量标记=flag)

    def test_unparseable_rows_are_skipped_and_counted(self):
        rows = [self.good(), self.fallback(), self.fallback(flag=0)]
        result, audit = vr.aggregate_abnormal(rows, PERIOD, {self.CHANNEL}, {(self.CHANNEL, "高一")})
        self.assertEqual(result["高一"]["线索量"], 1)
        self.assertEqual(audit["unparseable_rule_rows"], {"未识别规则": 2})
        self.assertEqual(audit["unparseable_rule_count"], 2)
        self.assertEqual(audit["missing_dimensions"], [])

    def test_fallback_rows_cannot_move_a_reported_number(self):
        good = [self.good()]
        noise = [self.fallback() for _ in range(998)]
        dimensions = {(self.CHANNEL, "高一")}
        baseline, audit = vr.aggregate_abnormal(good, PERIOD, {self.CHANNEL}, dimensions)
        polluted, noisy_audit = vr.aggregate_abnormal(good + noise, PERIOD, {self.CHANNEL}, dimensions)
        self.assertEqual(baseline, polluted)
        self.assertEqual(audit["matched_dimensions"], noisy_audit["matched_dimensions"])
        self.assertEqual(noisy_audit["unparseable_rule_count"], 998)

    def test_assignment_rule_channel_stays_strict(self):
        with self.assertRaisesRegex(ValueError, "无法解析分配渠道"):
            vr.assignment_rule_channel("未识别规则")

    def test_delivery_detail_surfaces_the_skipped_count(self):
        context = {"channels": [self.CHANNEL], "lead_read_audit": {"rev": 7},
                   "dimension_matching": {"unparseable_rule_rows": {"未识别规则": 998},
                                          "unparseable_rule_count": 998}}
        detail = vr.delivery_detail(context)
        self.assertEqual(detail["unparseable_rule_rows"], {"未识别规则": 998})
        self.assertEqual(detail["unparseable_rule_count"], 998)


if __name__ == "__main__":
    unittest.main()
