"""Offline contract tests for the four-channel supervisor-detail report."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from lark_delivery.domains.market_consultant import supervisor_report as sr
from lark_delivery.common.values import _rate as parse_rate
from lark_delivery.domains.market_consultant.style import _result_cell_fill


CHANNEL = "KOC-周帅数学"
PERIOD = "20260911期"


def leads(supervisor, manager, count, five_min, net, grade="高一"):
    rows = []
    for index in range(count):
        rows.append({
            "lead_id": f"{supervisor}-{manager}-{index}", "期次": PERIOD, "渠道": CHANNEL,
            "经理": manager, "主管": supervisor, "年级": grade,
            "分区日期": "20260910", "分区小时": "14",
            "退前线索": 1, "退后线索": 1, "总通时秒": 60, "首call完成标记": 1,
            "48h外呼标记": 1, "外呼次数": 2, "5min标记": int(index < five_min),
            "好友标记": 1, "APP登陆标记": 1, "深沟标记": 0, "双沟标记": 0,
            "首节到课标记": 0, "当期净收款": 0, "报科数": 0, "成交人头": 0,
            "订单数": 0, "净收款": net, "收款": max(net, 0), "退费": 0,
        })
    return rows


def build(rows):
    _, counters = sr.projection(set(rows[0]), "both")
    sr.validate_scope(rows, CHANNEL, PERIOD)
    return sr.build_report(rows, counters, PERIOD, "both")


def test_exact_supervisor_columns():
    assert [column[1] for column in sr.COLUMNS["process"]] == [
        "期次", "负责人", "主管", "退前线索", "退后线索", "线索留存率", "总通时",
        "首call率", "48h外呼", "外呼频次", "5min", "好友率", "APP登陆率", "深沟率", "双沟率",
    ]
    assert [column[1] for column in sr.COLUMNS["result"]] == [
        "期次", "负责人", "主管", "退后线索", "5min", "双沟率",
        "首节到课率", "当期单效", "截面单效",
    ]


def test_reminders_are_independent_by_grade_and_include_exact_ties():
    rows = leads("主管甲", "经理甲", 12, 3, 1, "高一")
    rows += leads("主管乙", "经理乙", 12, 3, 1, "高一")
    rows += leads("主管丙", "经理丙", 12, 9, 20, "高一")
    rows += leads("主管丁", "经理甲", 12, 12, 20, "高二")
    rows += leads("主管戊", "经理乙", 12, 0, 1, "高二")
    report = build(rows)
    assert report["blocks"][0]["reminders"]["process"] == ["主管乙", "主管甲"]
    assert report["blocks"][0]["reminders"]["result"] == ["主管乙", "主管甲"]
    assert report["blocks"][1]["reminders"]["process"] == ["主管戊"]
    assert report["blocks"][1]["reminders"]["result"] == ["主管戊"]
    assert not ({"经理甲", "经理乙", "经理丙"} & set(report["reminder_names"]))


def test_image_blocks_are_grades_and_each_row_is_one_advisor():
    rows = leads("主管甲", "顾问甲", 10, 5, 2, "高二")
    rows += leads("主管乙", "顾问乙", 10, 5, 2, "高一")
    report = build(rows)
    assert [block["grade"] for block in report["blocks"]] == ["高一", "高二"]
    assert all("supervisor" not in block for block in report["blocks"])
    assert [(row["fields"]["负责人"], row["fields"]["主管"])
            for block in report["blocks"] for row in block["rows"]] == [("顾问乙", "主管乙"), ("顾问甲", "主管甲")]


def test_supervisors_below_ten_post_leads_are_hidden_from_image_and_ranking():
    rows = leads("有效主管", "经理甲", 10, 8, 20) + leads("低样本主管", "经理乙", 9, 0, 0)
    report = build(rows)
    block = report["blocks"][0]
    assert {row["fields"]["负责人"] for row in block["rows"]} == {"经理甲"}
    assert block["total"]["fields"]["退后线索"] == 10
    assert block["hidden_supervisors_below_minimum"] == ["低样本主管"]
    assert report["hidden_image_rows_below_minimum"] == [
        {"grade": "高一", "负责人": "经理乙", "主管": "低样本主管", "退后线索": "9"}
    ]
    assert block["reminders"]["process"] == ["有效主管"]
    assert block["reminders"]["result"] == ["有效主管"]


def test_grade_with_no_eligible_supervisor_is_omitted_from_text_reminders():
    report = build(leads("低样本主管", "经理甲", 9, 0, 0))
    assert report["blocks"] == []
    assert report["empty_after_minimum_filter"] is True
    markdown = sr.build_markdown(
        report, PERIOD, CHANNEL, "both",
        {"resolved": {}, "display_names": {}},
        {"process": "img_process", "result": "img_result"},
    )
    assert "较低" not in markdown
    assert "暂无退后线索" not in markdown


def test_image_filter_uses_individual_grade_manager_supervisor_row():
    rows = leads("顾问甲", "同一主管", 5, 2, 1) + leads("顾问乙", "同一主管", 5, 2, 1)
    report = build(rows)
    assert report["blocks"] == []
    assert len(report["hidden_image_rows_below_minimum"]) == 2


def test_latest_title_and_native_mentions():
    report = build(leads("主管甲", "经理甲", 10, 5, 20))
    markdown = sr.build_markdown(
        report, PERIOD, CHANNEL, "both",
        {"resolved": {"主管甲": "ou_test"}, "display_names": {"主管甲": "主管甲"}},
        {"process": "img_process", "result": "img_result"},
    )
    assert f"🔥 **【{PERIOD}】{CHANNEL}渠道过程数据播报**" in markdown
    assert f"🔥 **【{PERIOD}】{CHANNEL}渠道转化数据播报**" in markdown
    assert "高中" not in markdown
    assert f"【{CHANNEL}】" not in markdown
    assert '<at user_id="ou_test">主管甲</at>' in markdown
    assert "经理甲" not in markdown
    assert f"{CHANNEL}渠道高一年级 5min 率较低：" in markdown


def test_all_middle_school_grades_are_excluded_before_images_and_reminders():
    rows = leads("高中主管", "高中经理", 10, 5, 20, "高一")
    rows += leads("初中主管甲", "初中经理甲", 20, 0, 0, "初一")
    rows += leads("初中主管乙", "初中经理乙", 20, 0, 0, "初三")
    report = build(rows)
    assert [block["grade"] for block in report["blocks"]] == ["高一"]
    assert report["excluded_grade_counts"] == {"初一": 20, "初三": 20}
    assert report["reminder_names"] == ["高中主管"]


def test_retention_rate_uses_one_fixed_low_red_to_high_green_scale():
    cases = {
        "0%": "#fb626b", "71.99%": "#fb626b",
        "72%": "#fa9a7e", "74.99%": "#fa9a7e",
        "75%": "#f9c777", "79.99%": "#f9c777",
        "80%": "#d9df83", "87.99%": "#d9df83",
        "88%": "#62bc7f", "100%": "#62bc7f",
    }
    assert {value: sr._retention_fill(value, parse_rate) for value in cases} == cases


def test_process_rows_follow_exact_retention_scale_high_to_low():
    rows = []
    for advisor, pre, post in [
        ("绿档", 10000, 8801),
        ("绿档边界", 10000, 8800),
        ("黄绿档", 10000, 8799),
        ("黄档", 10000, 7999),
        ("橙档", 10000, 7499),
        ("红档", 10000, 7199),
    ]:
        rows.append({
            "fields": {"负责人": advisor},
            "sums": {"退前线索": str(pre), "退后线索": str(post),
                     "5min标记": "0", "净收款": "0"},
        })
    ordered = sr.sorted_rows({"rows": list(reversed(rows))}, "process")
    assert [row["fields"]["负责人"] for row in ordered] == [
        "绿档", "绿档边界", "黄绿档", "黄档", "橙档", "红档",
    ]


def test_process_retention_order_uses_raw_fraction_before_display_rounding():
    block = {"rows": [
        {"fields": {"负责人": "略低"},
         "sums": {"退前线索": "100000", "退后线索": "88000", "5min标记": "0"}},
        {"fields": {"负责人": "略高"},
         "sums": {"退前线索": "100000", "退后线索": "88001", "5min标记": "0"}},
    ]}
    assert [row["fields"]["负责人"] for row in sr.sorted_rows(block, "process")] == ["略高", "略低"]


def test_process_rows_sort_by_raw_five_min_rate_descending_before_retention():
    block = {"rows": [
        {"fields": {"负责人": "高留存低5min"},
         "sums": {"退前线索": "100", "退后线索": "90", "5min标记": "18"}},
        {"fields": {"负责人": "低留存高5min"},
         "sums": {"退前线索": "100", "退后线索": "80", "5min标记": "24"}},
        {"fields": {"负责人": "中间"},
         "sums": {"退前线索": "100", "退后线索": "85", "5min标记": "21"}},
    ]}
    assert [row["fields"]["负责人"] for row in sr.sorted_rows(block, "process")] == [
        "低留存高5min", "中间", "高留存低5min",
    ]


def test_process_five_min_order_uses_raw_fraction_before_display_rounding():
    block = {"rows": [
        {"fields": {"负责人": "略低"},
         "sums": {"退前线索": "100000", "退后线索": "100000", "5min标记": "20000"}},
        {"fields": {"负责人": "略高"},
         "sums": {"退前线索": "100001", "退后线索": "100001", "5min标记": "20001"}},
    ]}
    assert [row["fields"]["负责人"] for row in sr.sorted_rows(block, "process")] == ["略高", "略低"]


def test_result_effect_equal_values_share_one_color_and_distinct_values_descend():
    assert _result_cell_fill("截面单效", 0, 0, 1) == _result_cell_fill("截面单效", 0, 0, 1)
    assert _result_cell_fill("截面单效", 100, 0, 3) == "#62bc7f"
    assert _result_cell_fill("截面单效", 50, 1, 3) == "#f9c777"
    assert _result_cell_fill("截面单效", 0, 2, 3) == "#fb626b"
