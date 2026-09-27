from pathlib import Path
import sys
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from lark_delivery.core import catalog
from lark_delivery.domains.market_consultant import adapter
from lark_delivery.domains.market_consultant import supervisor_yafei_advisor_report as report
from lark_delivery.domains.market_consultant.channels import supervisor_yafei_grade_9_advisor as policy


KEY = "market_consultant/supervisor_yafei_grade_9_advisor"
PERIOD = "20260925期"


def lead(index, *, five=1, net=1):
    return {"fields": {
        "lead_id": f"advisor-{index}", "期次": PERIOD, "渠道": "B站信息流-亚飞",
        "经理": "负责人甲", "主管": "主管甲", "顾问": f"顾问{index}", "年级": "初三",
        "分区日期": "20260925", "分区小时": "19", "退前线索": 10, "退后线索": 10,
        "总通时秒": 60, "首call完成标记": 1, "48h外呼标记": 1, "外呼次数": 2,
        "5min标记": five, "好友标记": 1, "APP登陆标记": 1, "深沟标记": 0,
        "双沟标记": 0, "首节到课标记": 1, "当期净收款": net, "报科数": 1,
        "成交人头": 1, "订单数": 1, "净收款": net, "收款": net, "退费": 0,
    }}


def test_registered_scope_is_enabled_and_advisor_grain():
    definition = catalog.load_channel(KEY)
    target = catalog.select_targets(definition)[0]
    assert target["chat_id"] == policy.CHAT_ID
    assert definition["source"]["report_profile"] == policy.PROFILE
    assert definition["source"]["mention_target"] == "consultant"
    assert definition["schedule"]["enabled"] is True
    assert definition["report"]["minimum_post_leads"] == 5
    assert adapter.report_module_for(definition) is report


def test_weekend_routes_current_result_and_next_process():
    slot = datetime(2026, 9, 26, 13, tzinfo=timezone(timedelta(hours=8)))
    target = catalog.select_targets(catalog.load_channel(KEY))[0]
    args = adapter.report_arguments(catalog.load_channel(KEY), target, slot=slot)
    assert args.report_type == "result_and_next_process"
    assert args.period == "20260925期"
    preview_args = adapter.report_arguments(catalog.load_channel(KEY), target,
                                            report_type="result_and_next_process", slot=slot)
    assert preview_args.report_type == "result_and_next_process"
    assert policy.next_business_period(args.period) == "20261002期"
    policy.enforce_component_calendar("20260925期", "result", slot)
    policy.enforce_component_calendar("20261002期", "process", slot)


def test_bottom_ten_percent_reminders_are_selected_per_section():
    rows = [lead(index, five=0 if index == 0 else 1, net=0 if index == 1 else 1)
            for index in range(10)]
    _, counters = report.projection(set(rows[0]["fields"]), "both")
    built = report.build_report(rows, counters, PERIOD, "both", min_post_leads=10,
                                included_grades=("初三",))
    block = built["blocks"][0]
    assert block["reminder_quotas"] == {"process": 1, "result": 1}
    assert block["reminders"]["process"] == ["顾问0"]
    assert block["reminders"]["result"] == ["顾问1"]
    assert built["reminder_rule"] == "channel_grade_source_advisor_bottom_10pct_minimum_one"
    assert len(block["rows"]) == 10


def test_conversion_rows_are_sorted_by_cross_section_effect_descending():
    rows = [lead(0, net=5), lead(1, net=2), lead(2, net=9)]
    _, counters = report.projection(set(rows[0]["fields"]), "result")
    built = report.build_report(rows, counters, PERIOD, "result", min_post_leads=10,
                                included_grades=("初三",))
    ordered = report.sorted_rows(built["blocks"][0], "result")
    assert [row["fields"]["截面单效"] for row in ordered] == [0.9, 0.5, 0.2]


def test_conversion_report_includes_five_minute_and_double_communication_rates():
    row = lead(0, five=1)
    _, counters = report.projection(set(row["fields"]), "result")
    assert "5min标记" in counters
    assert "双沟标记" in counters

    built = report.build_report([row], counters, PERIOD, "result", min_post_leads=10,
                                included_grades=("初三",))
    fields = built["blocks"][0]["rows"][0]["fields"]
    assert fields["5min"] == "10.00000000%"
    assert fields["双沟率"] == "0.00000000%"


def test_conversion_indicator_colors_match_supervisor_palette():
    assert report.BAR_COLORS["5min"] == "#f5ae23"
    assert report.BAR_COLORS["双沟率"] == "#138de2"
