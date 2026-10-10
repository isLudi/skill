from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from lark_delivery.core import catalog
from lark_delivery.domains.market_consultant import adapter
from lark_delivery.domains.market_consultant import supervisor_app_grade9_report as report
from lark_delivery.domains.market_consultant.channels import app_grade_9 as policy
from lark_delivery.common.images import _find_font, _center_text
from lark_delivery.common.values import _format_value, _rate

KEY = "market_consultant/app_grade_9"
PERIOD = "20261009期"
SLOT = datetime(2026, 10, 10, 13, tzinfo=timezone(timedelta(hours=8)))


def leads(name, count, *, net=2, current=100, five=0, grade="初三", channel="APP"):
    return [{"fields": {
        "lead_id": f"{name}-{index}", "期次": PERIOD, "渠道": channel,
        "经理": "负责人甲", "主管": "主管甲", "顾问": name, "年级": grade,
        "分区日期": "20261010", "分区小时": "15", "退前线索": 1, "退后线索": 1,
        "总通时秒": 60, "首call完成标记": 1, "48h外呼标记": 1, "外呼次数": 2,
        "5min标记": int(index < five), "好友标记": 1, "APP登陆标记": 1,
        "深沟标记": 0, "双沟标记": 1, "首节到课标记": 1, "当期净收款": current,
        "报科数": 1, "成交人头": 1, "订单数": 1, "净收款": net, "收款": net, "退费": 0,
    }} for index in range(count)]


def built_report(kind="both"):
    rows = (leads("顾问甲", 5, five=2) + leads("顾问乙", 10, five=4)
            + leads("顾问丙", 5, net=6, current=0, five=4)
            + leads("不足5", 4, net=0) + leads("高中顾问", 5, grade="高三", net=0))
    _, counters = report.projection(set(rows[0]["fields"]), kind)
    return report.build_report(rows, counters, PERIOD, kind)


def test_registered_scope_is_paused_and_exactly_app_grade9():
    definition = catalog.load_channel(KEY)
    adapter.validate_definition(definition)
    assert definition["schedule"]["enabled"] is False
    assert definition["channels"] == ["app"]
    assert definition["targets"][0]["chat_id"] == policy.CHAT_ID
    assert definition["report"]["minimum_post_leads"] == 5
    assert adapter.report_module_for(definition) is report
    args = adapter.report_arguments(definition, definition["targets"][0], slot=SLOT)
    assert args.report_type == "result_and_next_process" and args.period == PERIOD


def test_eligible_minimum_ties_use_cross_section_effect_and_five_minute_rate():
    built = built_report()
    block = built["blocks"][0]
    assert block["reminders"] == {"process": ["顾问乙", "顾问甲"], "result": ["顾问乙", "顾问甲"]}
    assert len(block["rows"]) == 3
    assert built["excluded_grade_counts"] == {"高三": 5}
    assert built["show_totals"] is False
    assert built["result_reminder_metric"] == "截面单效"
    assert [r["fields"]["截面单效"] for r in report.sorted_rows(block, "result")] == [6, 2, 2]
    assert set(built["reminder_names"]) == {"顾问甲", "顾问乙"}


def test_casefold_match_is_exact_and_empty_advisors_fail():
    rows = leads("顾问", 5)
    rows[0]["fields"]["渠道"] = "app"
    scope = {"match_mode": "casefold_exact", "value": "app"}
    assert report.validate_scope(rows, "app", PERIOD, source_channel=scope) == ("20261010", "15")
    rows[0]["fields"]["渠道"] = "APP广告"
    with pytest.raises(ValueError):
        report.validate_scope(rows, "app", PERIOD, source_channel=scope)
    rows[0]["fields"].update(渠道="app", 顾问="")
    with pytest.raises(ValueError, match="空顾问"):
        report.validate_scope(rows, "app", PERIOD, source_channel=scope)


@pytest.mark.parametrize("section", ["process", "result"])
def test_requested_columns_render_without_total_row(tmp_path, section):
    labels = []
    def capture(draw, box, label, font, fill):
        labels.append(label)
        return _center_text(draw, box, label, font, fill)
    path = tmp_path / f"{section}.png"
    geometry = report.render_image(built_report(), section, path, font_loader=_find_font,
        center_text=capture, format_value=_format_value, rate_parser=_rate)
    with Image.open(path) as rendered:
        assert rendered.size == (sum(report.WIDTHS[section]), 48 + 58 + 3 * 50)
    assert geometry[0]["rows"] == 3 and "总计" not in labels
    assert "顾问" in labels and "不足5" not in labels
    if section == "process":
        assert "首call" in labels and "APP登陆率" not in labels
    else:
        assert "截面单效" in labels and "5min" in labels and "双沟率" in labels


def test_component_calendar_is_current_result_then_next_process():
    policy.enforce_component_calendar(PERIOD, "result", SLOT)
    policy.enforce_component_calendar("20261016期", "process", SLOT)
    with pytest.raises(ValueError):
        policy.enforce_component_calendar(PERIOD, "process", SLOT)
    with pytest.raises(ValueError):
        policy.enforce_component_calendar("20261016期", "result", SLOT)
