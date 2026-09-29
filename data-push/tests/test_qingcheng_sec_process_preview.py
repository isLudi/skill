"""SEC previews use pre-return leads and raw friend rates for ranking."""

import json
import sys
from pathlib import Path

from PIL import Image, ImageColor


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import preview_qingcheng_sec_process as sec  # noqa: E402
from preview_qingcheng_public_pool_process import _display, _table_image, _total_row  # noqa: E402
import preview_qingcheng_sec_secondary_supervisors as secondary  # noqa: E402


def _row(account: str, friend: int) -> dict:
    return {
        "期次": "20260925期", "主管": "主管甲", "顾问": account,
        "顾问账号": account, "年级": "高三", "退前线索": 1,
        "退后线索": 0, "好友标记": friend, "首call等待时长小时": 2,
        "8min标记": 0, "24h首call标记": 1, "沟通标记": 1,
        "总通时秒": 90, "外呼次数": 2,
    }


def test_sec_effective_leads_use_pre_return_source_and_recalculate_total():
    rows = [_row("advisor-a", 1), _row("advisor-a", 0), _row("advisor-a", 0),
            _row("advisor-b", 1), _row("advisor-b", 1), _row("advisor-b", 0)]
    request = {"business": {"grades": ["高三"]}, "report": {"minimum": {"value": 3}}}

    detail = sec._aggregate(rows, "顾问", request, lead_field="退前线索")
    assert {item["顾问账号"]: item["metrics"]["好友率"] for item in detail} == {
        "advisor-a": 1 / 3, "advisor-b": 2 / 3}
    assert _total_row(detail)["metrics"]["有效线索"] == 6
    assert _total_row(detail)["metrics"]["好友率"] == 0.5
    assert sec._aggregate(rows, "顾问", request) == []


def test_sec_reminder_includes_every_exactly_tied_lowest_account():
    rows = [
        {"顾问": "乙", "顾问账号": "advisor-b", "年级": "高三", "metrics": {"好友率": 0.0}},
        {"顾问": "甲", "顾问账号": "advisor-a", "年级": "高三", "metrics": {"好友率": 0.0}},
        {"顾问": "丙", "顾问账号": "advisor-c", "年级": "高三", "metrics": {"好友率": 0.2}},
    ]
    reminder = sec._reminder(rows, "顾问")
    assert [(person["name"], person["account"]) for person in reminder["people"]] == [
        ("甲", "advisor-a"), ("乙", "advisor-b")]
    assert reminder["tied_rows"] == 2
    assert reminder["tie_handling"] == "all_tied_minimum"


def test_sec_preview_precision_matches_current_qingcheng_process_images():
    assert _display(561, "有效线索") == "561"
    assert _display(24, "带班人数") == "24"
    assert _display(595.2, "总通时") == "595"
    assert _display(0.02173, "好友率") == "2.2%"
    assert _display(46.045, "等待时长") == "46.0"


def test_sec_four_distinct_bars_exclude_waiting_time(tmp_path):
    config = json.loads((SCRIPTS.parent / "config/departments/qingcheng/sec_public_process_preview.json").read_text(encoding="utf-8"))
    specs = config["visual"]["metric_bars"]
    assert tuple(specs) == sec.SEC_BAR_FIELDS
    assert all(profile["process_bars"] == list(specs) for profile in config["profiles"].values())
    assert len({spec["color"] for spec in specs.values()}) == 4

    request = {"business": {"grades": ["高三"]}, "report": {"minimum": {"value": 3}}}
    row = sec._aggregate([_row("advisor-a", 1), _row("advisor-a", 0), _row("advisor-a", 0)],
                         "顾问", request, lead_field="退前线索")[0]
    columns = ["期次", "顾问", "好友率", "等待时长", "24h首call", "外呼时长", "外呼频次"]
    image_path = tmp_path / "sec.png"
    _table_image([row], columns, image_path, "顾问", "20260925期", "公域",
                 bar_specs={field: (spec["min"], spec["max"], spec["color"]) for field, spec in specs.items()})
    with Image.open(image_path) as image:
        for field, x in (("好友率", 274), ("24h首call", 564), ("外呼时长", 709), ("外呼频次", 854)):
            assert image.getpixel((x, 120)) == ImageColor.getrgb(specs[field]["color"])
        assert image.getpixel((419, 120)) == (255, 255, 255)


def test_sec_consultants_sort_and_remind_within_each_grade():
    rows = [
        {"顾问": "高二乙", "顾问账号": "b2", "年级": "高二", "metrics": {"好友率": 0.5}},
        {"顾问": "高一甲", "顾问账号": "a1", "年级": "高一", "metrics": {"好友率": 0.2}},
        {"顾问": "高二甲", "顾问账号": "a2", "年级": "高二", "metrics": {"好友率": 0.8}},
        {"顾问": "高一乙", "顾问账号": "b1", "年级": "高一", "metrics": {"好友率": 0.9}},
    ]
    grades = ["高一", "高二", "高三"]
    ordered = sec._sort_rows(rows, grades, split_grade=True)
    assert [row["顾问"] for row in ordered] == ["高一乙", "高一甲", "高二甲", "高二乙"]
    reminders = sec._reminders(ordered, grades, "顾问", split_grade=True)
    assert [(item["grade"], item["people"][0]["name"]) for item in reminders] == [
        ("高一", "高一甲"), ("高二", "高二乙")]


def test_sec_secondary_supervisors_show_pre_return_leads_and_remind_all_grade_ties():
    rows = []
    for supervisor, grade, friend in (("主管甲", "高二", 0), ("主管乙", "高二", 0),
                                      ("主管丙", "高三", 1)):
        for index in range(5):
            row = _row(f"{supervisor}-顾问", friend if index == 0 else 0)
            row.update({"主管": supervisor, "年级": grade})
            rows.append(row)
    request = {"business": {"grades": ["高一", "高二", "高三", "初三"]},
               "report": {"minimum": {"value": 5}, "process_metrics": ["退前线索"]}}
    grouped = sec._aggregate(rows, "主管", request, split_grade=True, lead_field="退前线索")
    ordered = sec._sort_rows(grouped, request["business"]["grades"], split_grade=True)
    reminders = sec._reminders(ordered, request["business"]["grades"], "主管", split_grade=True)

    assert [row["年级"] for row in ordered] == ["高二", "高二", "高三"]
    assert {person["name"] for person in reminders[0]["people"]} == {"主管甲", "主管乙"}
    assert [person["name"] for person in reminders[1]["people"]] == ["主管丙"]
    assert _total_row(ordered[:2])["metrics"]["退前线索"] == 10
    assert _display(10, "退前线索", integer_fields=frozenset({"退前线索"})) == "10"
    config = json.loads(secondary.CONFIG.read_text(encoding="utf-8"))
    assert secondary._validate_config(config)
    for profile in config["reports"]:
        request_snapshot = json.loads((secondary.CONFIG.parent / profile["request_file"]).read_text(encoding="utf-8"))
        assert secondary._validate_report(profile, request_snapshot) == secondary.EXPECTED_COLUMNS
