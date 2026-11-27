"""Advisor breakthrough follows revenue and distinct accounts, never customer flags."""
from decimal import Decimal

import pytest

import preview_qingcheng_transformation as preview


def process(account, grade="高一", *, supervisor="主管甲", manager="经理甲"):
    return {"期次": "20261120期", "主管": supervisor, "经理": manager, "年级": grade,
            "顾问账号": account, "顾问": account, "退后线索": 10, "首节到课标记": 0}


def conversion(account, revenue, grade="高一", *, supervisor="主管甲", manager="经理甲", podan=99):
    return {"期次": "20261120期", "主管": supervisor, "经理": manager, "年级": grade,
            "顾问账号": account, "记录键": "q|conversion_fact|lead|uid|x|y", "成交人头": 1,
            "收款": revenue, "净收款": -100, "当期收款": 0, "报科数": 1, "退费": 100,
            "破蛋人数标记": podan, "成交周期天数分子": 1, "成交周期成交人数分母": 1}


def aggregate(p, c, level="主管"):
    return preview._aggregate_with_extras(p, c, level, {"report": {"minimum": {"value": 1}}},
                                          {"split_grade": True}, period="20261120期")


@pytest.mark.parametrize("level", ["主管", "学部"])
def test_counts_advisers_once_after_summing_revenue_not_customers_or_net(level):
    p = [process("a"), process("a"), process("b"), process("c")]
    c = [conversion("a", 100), conversion("a", 100), conversion("b", 0), conversion("c", -1)]
    row = aggregate(p, c, level)[0]
    assert row["metrics"]["破蛋率"] == pytest.approx(1 / 3)
    assert row["metrics"]["带班人数"] == 3
    assert row["metrics"]["净收款"] < 0  # gross revenue is intentionally independent of refunds


def test_revenue_is_summed_before_strictly_positive_threshold():
    p = [process("a"), process("b")]
    c = [conversion("a", 100), conversion("a", -100), conversion("b", 0)]
    assert aggregate(p, c)[0]["metrics"]["破蛋率"] == 0


def test_total_recalculates_distinct_accounts_and_merged_revenue_across_grades():
    p = [process("a"), process("b"), process("a", "高二"), process("c", "高二")]
    c = [conversion("a", 100), conversion("a", -100, "高二"), conversion("c", 50, "高二")]
    rows = aggregate(p, c)
    assert [r["metrics"]["破蛋率"] for r in rows] == [0.5, 0.5]
    total = preview._total_transformation(rows)["metrics"]
    assert total["带班人数"] == 3
    assert total["破蛋率"] == pytest.approx(1 / 3)


def test_empty_conversion_keeps_all_in_scope_advisers_in_denominator():
    row = aggregate([process("a"), process("b")], [])[0]
    assert row["metrics"]["破蛋率"] == 0


def test_each_consultant_is_zero_or_one_and_other_scopes_do_not_leak():
    p = [process("a"), process("b")]
    c = [conversion("a", 5), conversion("outside", 100), conversion("b", 100, "高二")]
    rows = aggregate(p, c, "顾问")
    assert {r["顾问账号"]: r["metrics"]["破蛋率"] for r in rows} == {"a": 1, "b": 0}


def test_decimal_cancellation_is_not_falsely_counted_as_positive():
    p = [process("a")]
    c = [conversion("a", "0.1"), conversion("a", "0.2"), conversion("a", "-0.3")]
    row = aggregate(p, c)[0]
    assert row["_advisor_revenue"] == {"a": Decimal(0)}
    assert row["metrics"]["破蛋率"] == 0
