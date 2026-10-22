"""15min shares the existing 8min denominator and stays out of SEC reports."""
from copy import deepcopy
from pathlib import Path
import sys

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import preview_qingcheng_public_pool_process as process
import preview_qingcheng_special_process as special


def source(account, leads, eight, fifteen, *, grade="高一", manager="经理甲"):
    return {"期次": "20261023期", "主管": "主管甲", "经理": manager, "顾问": account,
            "顾问账号": account, "年级": grade, "退后线索": leads, "退前线索": leads + 5,
            "好友标记": 1, "首call等待时长小时": 2, "8min标记": eight,
            "15min标记": fifteen, "15min分母": 999,
            "24h首call标记": 1, "沟通标记": 1, "总通时秒": 120, "外呼次数": 3}


def request(*, include=True, minimum=1):
    return {"business": {"grades": ["高一", "高二", "高三", "初三"]},
            "report": {"minimum": {"value": minimum}, "process_metrics": ["8min", "15min"] if include else ["好友率"]}}


@pytest.mark.parametrize("level,split_grade", [("主管", False), ("主管", True), ("顾问", True)])
def test_15min_uses_the_exact_8min_lead_denominator(level, split_grade):
    rows = [source("甲", 2, 2, 1), source("甲", 8, 4, 2)]
    grouped = process._aggregate(rows, level, request(), split_grade=split_grade)
    assert len(grouped) == 1
    assert grouped[0]["metrics"]["8min"] == .6
    assert grouped[0]["metrics"]["15min"] == .3
    assert grouped[0]["metrics"]["有效线索"] == 10


def test_15min_total_recalculates_weighted_rate_instead_of_averaging_rows():
    grouped = process._aggregate([source("甲", 2, 2, 1), source("乙", 8, 4, 1)], "顾问", request())
    assert {row["顾问账号"]: row["metrics"]["15min"] for row in grouped} == {"甲": .5, "乙": .125}
    assert process._total_row(grouped)["metrics"]["15min"] == .2


@pytest.mark.parametrize("bad", ["missing", "null"])
def test_selected_15min_missing_source_is_an_error_not_zero(bad):
    row = source("甲", 5, 2, 1)
    if bad == "missing":
        del row["15min标记"]
    else:
        row["15min标记"] = None
    with pytest.raises(ValueError, match="15min标记"):
        process._aggregate([row], "顾问", request())


def test_sec_style_request_does_not_require_or_add_15min():
    row = source("甲", 5, 2, 1)
    del row["15min标记"]
    grouped = process._aggregate([row], "顾问", request(include=False), lead_field="退前线索")
    assert "15min" not in grouped[0]["metrics"]
    assert "15min" not in process._total_row(grouped)["metrics"]


def test_15min_zero_denominator_and_percentage_precision():
    grouped = process._aggregate([source("甲", 0, 0, 0)], "顾问", request(minimum=0))
    assert grouped[0]["metrics"]["15min"] is None
    assert process._display(None, "15min") == "—"
    assert process._display(0, "15min") == "0.0%"
    assert process._display(1 / 3, "15min") == "33.3%"


def test_partial_15min_metrics_cannot_silently_change_total_coverage():
    grouped = process._aggregate([source("甲", 2, 2, 1), source("乙", 8, 4, 1)], "顾问", request())
    del grouped[1]["metrics"]["15min"]
    with pytest.raises(ValueError, match="inconsistent 15min"):
        process._total_row(grouped)


def test_special_report_15min_uses_post_refund_scope_and_keeps_8min_sort():
    rows = [source("甲", 5, 4, 1, manager="经理甲"), source("乙", 10, 3, 3, manager="经理乙"),
            source("丙", 4, 4, 4, manager="低量经理"), source("丁", 10, 5, 5, grade="初二")]
    grouped = special._aggregate(rows, "20261023期", 5)
    assert [row["负责人"] for row in grouped] == ["经理甲", "经理乙"]
    assert [row["metrics"]["15min"] for row in grouped] == [.2, .3]
    assert process._total_row(grouped)["metrics"]["15min"] == pytest.approx(4 / 15)
    assert special.DISPLAY_COLUMNS.index("15min") == special.DISPLAY_COLUMNS.index("8min") + 1


def test_15min_does_not_change_original_8min_reminders():
    rows = [source("甲", 5, 1, 0), source("乙", 5, 1, 1), source("丙", 5, 3, 2)]
    grouped = process._aggregate(rows, "顾问", request())
    old = deepcopy(grouped)
    for row in old:
        del row["metrics"]["15min"]
    assert process._reminder_people("顾问", grouped) == process._reminder_people("顾问", old)
    assert {p["account"] for p in process._reminder_people("顾问", grouped)} == {"甲", "乙"}
