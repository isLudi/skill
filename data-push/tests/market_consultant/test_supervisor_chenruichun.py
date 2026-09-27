from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from lark_delivery.core import catalog
from lark_delivery.domains.market_consultant import adapter
from lark_delivery.domains.market_consultant.channels import supervisor_chenruichun as policy
from lark_delivery.domains.market_consultant import supervisor_video49_report as report
from lark_delivery.domains.market_consultant.workflow import _channel_matches, _channel_scope


KEY = "market_consultant/supervisor_chenruichun"
PERIOD = "20260918期"


def lead(index, source_channel, consultant, *, post=1):
    return {"fields": {
        "lead_id": f"chen-{index}", "期次": PERIOD, "渠道": source_channel,
        "经理": "负责人甲", "主管": "主管甲", "顾问": consultant, "年级": "高一",
        "分区日期": "20260918", "分区小时": "19", "退前线索": 1,
        "退后线索": post, "总通时秒": 60, "首call完成标记": 1,
        "48h外呼标记": 1, "外呼次数": 2, "5min标记": 1,
        "好友标记": 1, "APP登陆标记": 1, "深沟标记": 0, "双沟标记": 0,
        "首节到课标记": 1, "当期净收款": 1, "报科数": 1, "成交人头": 1,
        "订单数": 1, "净收款": 1, "收款": 1, "退费": 0,
    }}


def test_registered_scope_uses_advisor_grain_and_fixed_target():
    definition = catalog.load_channel(KEY)
    target = catalog.select_targets(definition)[0]
    assert target["chat_id"] == policy.CHAT_ID
    assert definition["report"]["minimum_post_leads"] == policy.MIN_POST_LEADS == 6
    assert adapter.report_module_for(definition) is report
    assert adapter.report_arguments(definition, target, report_type="both").mention_target == "consultant"
    assert adapter.report_arguments(definition, target, report_type="both",
                                    strict_mentions=False).strict_mentions is False


def test_contains_scope_aggregates_the_three_chenruichun_raw_channels():
    definition = catalog.load_channel(KEY)
    scope = _channel_scope(definition, "陈瑞春")
    assert scope == {"match_mode": "contains", "keyword": "陈瑞春", "case_sensitive": True}
    assert _channel_matches("陈瑞春-视频号49", scope)
    assert _channel_matches("陈瑞春-百度", scope)
    assert _channel_matches("陈瑞春-B站", scope)
    assert not _channel_matches("朱博士-视频号49", scope)

    rows = [lead(index, "陈瑞春-视频号49" if index % 2 else "陈瑞春-B站", "顾问甲")
            for index in range(1, 7)]
    _, counters = report.projection(set(rows[0]["fields"]), "both")
    report.validate_scope(rows, "陈瑞春", PERIOD, source_channel=scope)
    built = report.build_report(rows, counters, PERIOD, "both", min_post_leads=policy.MIN_POST_LEADS,
                                included_grades=("高一", "高二", "高三"))
    assert built["blocks"][0]["rows"][0]["fields"]["退后线索"] == 6
    assert built["reminder_names"] == ["顾问甲"]


def test_preview_marks_resolved_but_nonmember_advisors_without_native_at():
    markdown = report.build_markdown(
        {"blocks": [{"grade": "高一", "reminders": {"process": ["顾问甲"], "result": []}}]},
        PERIOD, "陈瑞春", "process",
        {"resolved": {"顾问甲": "ou_advisor"}, "display_names": {"顾问甲": "顾问甲"},
         "nonmembers": ["顾问甲"]},
        {"process": "img_process", "result": None},
    )
    assert "顾问甲（未入群，待核验）" in markdown
    assert '<at user_id="ou_advisor">' not in markdown
