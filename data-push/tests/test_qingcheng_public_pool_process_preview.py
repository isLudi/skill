"""Meaningful aggregation checks for the local Qingcheng public-pool preview."""

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "preview_qingcheng_public_pool_process.py"
SPEC = importlib.util.spec_from_file_location("qingcheng_public_pool_process_preview", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _row(account, lead, friend, long_call):
    return {
        "期次": "20260925期",
        "主管": "主管甲",
        "顾问": account,
        "顾问账号": account,
        "年级": "高三",
        "退后线索": lead,
        "好友标记": friend,
        "首call等待时长小时": 2,
        "8min标记": long_call,
        "24h首call标记": 1,
        "沟通标记": 1,
        "总通时秒": 120,
        "外呼次数": 2,
    }


def test_aggregates_raw_numerators_before_ratio_and_applies_level_threshold():
    rows = [_row("顾问甲", 2, 1, 1), _row("顾问甲", 1, 0, 0), _row("顾问乙", 2, 1, 0)]
    request = {"business": {"grades": ["高三"]}, "report": {"minimum": {"value": 3}}}

    advisors = MODULE._aggregate(rows, "顾问", request)
    assert len(advisors) == 1
    assert advisors[0]["顾问"] == "顾问甲"
    assert advisors[0]["metrics"]["有效线索"] == 3
    assert advisors[0]["metrics"]["好友率"] == 1 / 3
    assert advisors[0]["metrics"]["8min"] == 1 / 3

    supervisors = MODULE._aggregate(rows, "主管", request)
    assert len(supervisors) == 1
    assert supervisors[0]["metrics"]["有效线索"] == 5
    assert supervisors[0]["metrics"]["带班人数"] == 2
    assert supervisors[0]["metrics"]["外呼时长"] == 1.2

    request["report"]["minimum"]["value"] = 2
    total = MODULE._total_row(MODULE._aggregate(rows, "顾问", request))
    assert total["metrics"]["有效线索"] == 5
    assert total["metrics"]["好友率"] == 2 / 5
    assert total["metrics"]["8min"] == 1 / 5
    assert total["metrics"]["带班人数"] == 2


def test_only_requested_process_metrics_have_bars():
    assert set(MODULE.SCALES) == {"好友率", "24h首call", "8min", "等待时长"}
    assert set(MODULE.BAR_COLORS) == set(MODULE.SCALES)
    assert MODULE.BAR_COLORS["等待时长"] == "#fb626b"


def test_process_display_precision_keeps_total_call_time_whole():
    assert MODULE._display(0.56414, "好友率") == "56.4%"
    assert MODULE._display(39, "有效线索") == "39"
    assert MODULE._display(4, "带班人数") == "4"
    assert MODULE._display(2.437, "等待时长") == "2.4"
    assert MODULE._display(595.2, "总通时") == "595"


def test_process_rows_sort_by_unrounded_focus_metric_descending():
    rows = [
        {"主管": "甲", "顾问账号": None, "年级": None, "metrics": {"8min": 0.12331}},
        {"主管": "乙", "顾问账号": None, "年级": None, "metrics": {"8min": 0.12339}},
    ]
    assert [row["主管"] for row in MODULE._sort_process_rows(rows)] == ["乙", "甲"]
    assert MODULE._band_label("公海", "主管", "20260925期") == "公海-主管-20260925期"
    assert MODULE._band_label("公海", "顾问", "20260925期") == "公海-顾问-20260925期"


def test_process_message_uses_only_base_reminder_and_market_layout():
    request = {"reminder": {"report_level": "主管", "target": "主管", "process_metric": "8min", "process_direction": "最低", "process_rank": "最后1名"}}
    rows = [{"主管": "主管甲", "顾问账号": None, "年级": None, "metrics": {"8min": 0.1}}]
    message = MODULE._message("主管", "20260925期", rows, request, "supervisor_process.png")
    assert message == "\n".join([
        "## 🔥 **【20260925期】公海渠道主管过程数据播报**",
        "",
        "![主管维度过程数据](supervisor_process.png)",
        "",
        "- 8min较低的主管：主管甲",
    ])

    tied = [
        {"主管": "主管乙", "顾问账号": None, "年级": None, "metrics": {"8min": 0.0}},
        {"主管": "主管甲", "顾问账号": None, "年级": None, "metrics": {"8min": 0.0}},
        {"主管": "主管丙", "顾问账号": None, "年级": None, "metrics": {"8min": 0.1}},
    ]
    tied_message = MODULE._message("主管", "20260925期", tied, request, "supervisor_process.png")
    assert tied_message.endswith("- 8min较低的主管：主管乙、主管甲")


def test_consultant_process_message_reminds_every_tied_lowest_advisor():
    request = {"reminder": {"report_level": "顾问", "target": "顾问", "process_metric": "8min", "process_direction": "最低", "process_rank": "最后1名"}}
    rows = [
        {"主管": "甲", "顾问": "顾问甲", "顾问账号": "advisor-a", "年级": "高三", "metrics": {"8min": 0.0}},
        {"主管": "乙", "顾问": "顾问乙", "顾问账号": "advisor-b", "年级": "高三", "metrics": {"8min": 0.0}},
        {"主管": "丙", "顾问": "顾问丙", "顾问账号": "advisor-c", "年级": "高三", "metrics": {"8min": 0.1}},
    ]
    message = MODULE._message("顾问", "20260925期", rows, request, "consultant_process.png")
    assert message.endswith("- 8min较低的顾问：顾问甲、顾问乙")


def test_private_supervisor_is_split_by_grade_with_every_tied_minimum():
    request = {"business": {"grades": ["高一", "高二"]}, "report": {"minimum": {"value": 2}},
               "reminder": {"report_level": "主管", "target": "主管", "process_metric": "8min", "process_direction": "最低", "process_rank": "最后1名"}}
    rows = []
    for grade, supervisor, mark in (("高一", "甲", 0), ("高一", "乙", 0), ("高二", "甲", 1), ("高二", "丙", 0)):
        for index in range(2):
            row = _row(f"{supervisor}{grade}{index}", 1, 1, mark)
            row["主管"] = supervisor
            row["年级"] = grade
            rows.append(row)
    grouped = MODULE._sort_process_rows(MODULE._aggregate(rows, "主管", request, split_grade=True), split_grade=True)
    assert len(grouped) == 4
    assert [row["年级"] for row in grouped] == ["高一", "高一", "高二", "高二"]
    message = MODULE._message("主管", "20260925期", grouped, request, "supervisor_process.png", "私域")
    assert "- 高一年级8min较低的主管：乙、甲" in message
    assert "- 高二年级8min较低的主管：丙" in message


def test_douyin_supervisor_retention_uses_summed_leads_for_detail_and_total():
    rows = [_row("顾问甲", 4, 2, 1), _row("顾问乙", 6, 3, 2)]
    rows[0]["退前线索"] = 5
    rows[1]["退前线索"] = 10
    rows[1]["主管"] = "主管乙"
    request = {"business": {"grades": ["高三"]},
               "report": {"minimum": {"value": 1}, "process_metrics": ["线索留存率"]}}
    detail = MODULE._aggregate(rows, "主管", request)
    assert {item["主管"]: item["metrics"]["线索留存率"] for item in detail} == {"主管甲": 4 / 5, "主管乙": 6 / 10}
    total = MODULE._total_row(detail)
    assert total["metrics"]["退前线索"] == 15
    assert total["metrics"]["有效线索"] == 10
    assert total["metrics"]["线索留存率"] == 10 / 15
