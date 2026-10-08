from pathlib import Path
import sys
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from lark_delivery.core import catalog
from lark_delivery.core.contracts import ReportPorts
from lark_delivery.domains.market_consultant import adapter
from lark_delivery.domains.market_consultant.channels import supervisor_chenruichun as policy
from lark_delivery.domains.market_consultant import supervisor_video49_report as report
from lark_delivery.domains.market_consultant.workflow import (
    _channel_filter, _channel_matches, _channel_scope, prepare_report, source_channel_count,
)


KEY = "market_consultant/supervisor_chenruichun"
PERIOD = "20260918期"


def lead(index, source_channel, consultant, *, post=1, five=1, net=1):
    return {"fields": {
        "lead_id": f"chen-{index}", "期次": PERIOD, "渠道": source_channel,
        "经理": "负责人甲", "主管": "主管甲", "顾问": consultant, "年级": "高一",
        "分区日期": "20260918", "分区小时": "19", "退前线索": 1,
        "退后线索": post, "总通时秒": 60, "首call完成标记": 1,
        "48h外呼标记": 1, "外呼次数": 2, "5min标记": five,
        "好友标记": 1, "APP登陆标记": 1, "深沟标记": 0, "双沟标记": 0,
        "首节到课标记": 1, "当期净收款": 1, "报科数": 1, "成交人头": 1,
        "订单数": 1, "净收款": net, "收款": net, "退费": 0,
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


def test_contains_scope_includes_douyin_199_and_keywords_at_any_position():
    definition = catalog.load_channel(KEY)
    scope = _channel_scope(definition, "陈瑞春")
    assert scope == {"match_mode": "contains", "keyword": "陈瑞春", "case_sensitive": True}
    assert _channel_filter(scope) == ["渠道", "contains", "陈瑞春"]
    for name in ("陈瑞春-视频号49", "陈瑞春-百度", "陈瑞春-B站", "陈瑞春-抖音199",
                 "陈瑞春抖音199", "B站信息流-陈瑞春", "新投放-陈瑞春-其他产品"):
        assert _channel_matches(name, scope)
    assert not _channel_matches("朱博士-视频号49", scope)
    assert source_channel_count({"陈瑞春-抖音199": 3, "B站信息流-陈瑞春": 2,
                                 "新投放-陈瑞春-其他产品": 4, "朱博士-抖音199": 50},
                                definition["source"]["channel_match"], "陈瑞春") == 9


@pytest.mark.parametrize("report_type", ["process", "result", "both"])
def test_process_and_conversion_merge_all_keyword_channels(monkeypatch, tmp_path, report_type):
    definition = catalog.load_channel(KEY)
    target = catalog.select_targets(definition)[0]
    channels = ("陈瑞春-视频号49", "陈瑞春-百度", "陈瑞春-B站", "陈瑞春-抖音199",
                "陈瑞春抖音199", "B站信息流-陈瑞春", "新投放-陈瑞春-其他产品")
    rows = [lead(index, name, "顾问甲", five=int("199" in name), net=199 if "199" in name else 0)
            for index, name in enumerate(channels)]
    rows.append(lead(100, "朱博士-抖音199", "顾问甲", net=9999))
    other_period = lead(101, "陈瑞春-抖音199", "顾问甲", net=9999)
    other_period["fields"]["期次"] = "20260925期"
    rows.append(other_period)
    ports = Mock(spec=ReportPorts)
    ports.resolve_source.return_value = {"base_token": "fake", "table_id": definition["source"]["raw_table_id"], "view_id": ""}
    ports.field_names.return_value = set(rows[0]["fields"])

    def read(coords, args, fields, *, filter_json, audit):
        assert filter_json == {"logic": "and", "conditions": [
            ["渠道", "contains", "陈瑞春"], ["期次", "==", PERIOD]]}
        audit.update(records_count=len(rows), pages=1, rev=123, has_more=False)
        return rows

    ports.read_records.side_effect = read
    ports.verify_target.return_value = {"name": target["display_name"], "name_changed": False}
    monkeypatch.setattr(policy, "business_period", lambda *args: PERIOD)
    args = adapter.report_arguments(definition, target, report_type=report_type, period=PERIOD,
                                    state_dir=tmp_path, no_mentions=True)
    args.with_image = False
    context = prepare_report(args, definition, ports=ports)
    assert context["raw_count"] == 7
    assert context["raw_read_audit"]["matched_channel_values"] == sorted(channels)
    assert context["raw_read_audit"]["client_excluded_count"] == 2
    built = context["grade_report"]
    assert built["reminder_names"] == ["顾问甲"]
    fields = built["blocks"][0]["rows"][0]["fields"]
    assert fields["退后线索"] == 7
    assert built["blocks"][0]["total"]["fields"]["退后线索"] == 7
    if report_type != "result":
        assert float(fields["5min"].removesuffix("%")) == pytest.approx(200 / 7)
    if report_type != "process":
        assert fields["净收款"] == 398
        assert fields["单效"] == pytest.approx(398 / 7)
    ports.search_users.assert_not_called()


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
