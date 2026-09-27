from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from lark_delivery.core import catalog
from lark_delivery.domains.market_consultant import adapter
from lark_delivery.domains.market_consultant.channels import supervisor_zhu_doctor_video49 as policy
from lark_delivery.domains.market_consultant import supervisor_video49_report as report
from lark_delivery.domains.market_consultant.workflow import _channel_filter, _channel_matches, _channel_scope
from lark_delivery.common.images import _center_text, _find_font
from lark_delivery.common.values import _format_value, _rate


KEY = "market_consultant/supervisor_zhu_doctor_video49"
PERIOD = "20260918期"
CHANNEL = "朱博士"


def lead(manager, index, *, post=1, five=1, net=1, grade="高一", source_channel=CHANNEL,
         supervisor="主管甲", consultant=None):
    consultant = consultant or manager
    return {"fields": {
        "lead_id": f"{manager}-{index}", "期次": PERIOD, "渠道": source_channel,
        "经理": manager, "主管": supervisor, "顾问": consultant, "年级": grade,
        "分区日期": "20260918", "分区小时": "19", "退前线索": 1,
        "退后线索": post, "总通时秒": 60, "首call完成标记": 1,
        "48h外呼标记": 1, "外呼次数": 2, "5min标记": five,
        "好友标记": 1, "APP登陆标记": 1, "深沟标记": 0, "双沟标记": 0,
        "首节到课标记": 1, "当期净收款": net, "报科数": 1, "成交人头": 1,
        "订单数": 1, "净收款": net, "收款": net, "退费": 0,
    }}


def test_registered_scope_and_advisor_mention_target():
    definition = catalog.load_channel(KEY)
    target = catalog.select_targets(definition)[0]
    assert target["chat_id"] == policy.CHAT_ID
    assert definition["source"]["report_profile"] == policy.PROFILE
    assert definition["report"]["minimum_post_leads"] == 1
    assert definition["source"]["channel_match"] == {
        "field": "渠道", "match_mode": "contains", "keyword": "朱博士", "case_sensitive": True,
    }
    args = adapter.report_arguments(definition, target, report_type="both")
    assert args.mention_target == "consultant"
    assert adapter.report_module_for(definition) is report


def test_source_scope_uses_the_generic_zhu_doctor_contains_rule():
    definition = catalog.load_channel(KEY)
    scope = _channel_scope(definition, "朱博士")
    assert scope == {"match_mode": "contains", "keyword": "朱博士", "case_sensitive": True}
    assert _channel_filter(scope) == ["渠道", "contains", "朱博士"]
    assert _channel_matches("朱博士-视频号49", scope)
    assert _channel_matches("朱博士-抖音199", scope)
    assert not _channel_matches("视频号49", scope)


def test_exact_advisor_columns():
    assert [column[1] for column in report.COLUMNS["process"]] == [
        "期次", "负责人", "主管", "顾问", "退前线索", "退后线索", "线索留存率", "总通时(min)",
        "首call率", "48h外呼", "外呼频次", "5min", "好友率", "APP登陆率", "深沟率", "双沟率",
    ]
    assert [column[1] for column in report.COLUMNS["result"]] == [
        "期次", "负责人", "主管", "顾问", "退后线索", "首节到课率", "单效（当期）", "人均报科",
        "人头转化", "订单转化", "净收款", "退费率", "单效",
    ]


def test_advisor_threshold_controls_images_sorting_and_mentions():
    rows = [lead("负责人甲", 0, post=1, five=1, net=1, source_channel="朱博士-视频号49",
                 consultant="顾问甲")]
    rows += [lead("负责人乙", 0, post=0, five=0, net=0, source_channel="朱博士-抖音199",
                   consultant="顾问乙")]
    fields, counters = report.projection(set(rows[0]["fields"]), "both")
    assert "主管" in fields  # raw source integrity is still checked, not displayed
    report.validate_scope(rows, CHANNEL, PERIOD, source_channel={
        "match_mode": "contains", "keyword": "朱博士", "case_sensitive": True,
    })
    built = report.build_report(rows, counters, PERIOD, "both", min_post_leads=1)
    block = built["blocks"][0]
    assert [row["fields"]["负责人"] for row in block["rows"]] == ["负责人甲"]
    assert [(row["fields"]["主管"], row["fields"]["顾问"]) for row in block["rows"]] == [("主管甲", "顾问甲")]
    assert block["reminders"]["process"] == ["顾问甲"]
    assert block["reminders"]["result"] == ["顾问甲"]
    assert built["hidden_image_rows_below_minimum"] == [
        {"grade": "高一", "负责人": "负责人乙", "主管": "主管甲", "顾问": "顾问乙", "退后线索": "0"}
    ]
    markdown = report.build_markdown(
        built, PERIOD, CHANNEL, "both",
        {"resolved": {"顾问甲": "ou_advisor"}, "display_names": {"顾问甲": "顾问甲"}},
        {"process": "img_process", "result": "img_result"},
    )
    assert '<at user_id="ou_advisor">顾问甲</at>' in markdown
    assert "顾问乙" not in markdown
    assert "主管甲" not in markdown


def test_both_advisor_images_render_with_the_new_column_contract():
    rows = [lead("顾问甲", index, post=1, five=1, net=1) for index in range(5)]
    _, counters = report.projection(set(rows[0]["fields"]), "both")
    built = report.build_report(rows, counters, PERIOD, "both", min_post_leads=5)
    with tempfile.TemporaryDirectory() as directory:
        process = Path(directory) / "process.png"
        result = Path(directory) / "result.png"
        report.render_image(built, "process", process, font_loader=_find_font,
                            center_text=_center_text, format_value=_format_value,
                            rate_parser=_rate)
        report.render_image(built, "result", result, font_loader=_find_font,
                            center_text=_center_text, format_value=_format_value,
                            rate_parser=_rate)
        assert process.is_file() and process.stat().st_size > 0
        assert result.is_file() and result.stat().st_size > 0
