"""Offline contracts for the two reviewed province reports and their isolation."""
from copy import deepcopy
from datetime import datetime, timedelta
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

from PIL import Image
import pytest

from lark_delivery.common.images import _center_text, _find_font
from lark_delivery.common.values import _format_value, _rate
from lark_delivery.core import catalog
from lark_delivery.domains.market_consultant import adapter, immediate, localization
from lark_delivery.domains.market_consultant import supervisor_localization_report as report
from lark_delivery.domains.market_consultant import supervisor_report as base_report
from lark_delivery.domains.market_consultant import workflow
from lark_delivery.domains.market_consultant.channels import supervisor_localization_grade_9 as policy


REF = "market_consultant/supervisor_localization_grade_9"
PERIOD = "20261023期"
EXPECTED_PROCESS = ["期次", "负责人", "主管", "退前线索", "退后线索", "首call率", "48h外呼",
                    "外呼频次", "5min", "好友率", "APP登陆率", "深沟率", "双沟率"]
EXPECTED_RESULT = ["期次", "负责人", "主管", "退后线索", "5min", "双沟率", "首节到课率", "当期单效", "截面单效"]


@pytest.fixture
def definition():
    return catalog.load_channel(REF)


def raw_rows(supervisor, manager, count, five_min, net=10, grade="初三"):
    rows = []
    for index in range(count):
        rows.append({
            "lead_id": f"{supervisor}-{manager}-{index}", "期次": PERIOD,
            "渠道": "江苏本地化", "经理": manager, "主管": supervisor, "年级": grade,
            "分区日期": "20261020", "分区小时": "15", "退前线索": 1, "退后线索": 1,
            "总通时秒": 60, "首call完成标记": 1, "48h外呼标记": 1, "外呼次数": 2,
            "5min标记": int(index < five_min), "好友标记": 1, "APP登陆标记": 1,
            "深沟标记": 0, "双沟标记": 0, "首节到课标记": 0,
            "当期净收款": 0, "报科数": 0, "成交人头": 0, "订单数": 0,
            "净收款": net, "收款": max(net, 0), "退费": 0,
        })
    return rows


def build(rows):
    _, counters = report.projection(set(rows[0]), "both")
    return report.build_report(rows, counters, PERIOD, "both", min_post_leads=5, included_grades=["初三"])


def test_registered_definition_matches_reviewed_group_and_columns(definition):
    adapter.validate_definition(definition)
    assert adapter.report_module_for(definition) is report
    assert definition["source"]["channel_match"]["values"] == {
        "江苏本地化": "西安图书直播间-挂链", "安徽本地化": "西安直播安徽"}
    assert definition["targets"][0]["chat_id"] == policy.CHAT_ID
    assert definition["report"]["included_grades"] == ["初三"]
    assert definition["report"]["minimum_post_leads"] == 5
    assert definition["report"]["show_totals"] is False
    assert not definition["report"].get("weekend_next_process_enabled", False)
    assert report.DISPLAY_COLUMNS == {"process": EXPECTED_PROCESS, "result": EXPECTED_RESULT}
    assert definition["report"]["display_columns"] == report.DISPLAY_COLUMNS
    assert "净收款" not in report.DISPLAY_COLUMNS["result"]


@pytest.mark.parametrize("field,value", [
    ("minimum_post_leads", 4), ("show_totals", True), ("weekend_next_process_enabled", True),
    ("display_columns", {"process": EXPECTED_PROCESS, "result": EXPECTED_RESULT + ["净收款"]}),
])
def test_reviewed_display_contract_rejects_drift(definition, field, value):
    definition["report"][field] = value
    with pytest.raises(ValueError):
        adapter.validate_definition(definition)


@pytest.mark.parametrize("offset,kind", [(0, "process"), (1, "process"), (2, "process"),
                                         (3, "process"), (4, "result"), (5, "result"), (6, "result")])
def test_calendar_uses_current_friday_period_and_weekday_report(offset, kind):
    at = datetime(2026, 10, 19, 17, 25, tzinfo=policy.TZ) + timedelta(days=offset)
    assert policy.business_period(at) == PERIOD
    assert policy.scheduled_report_type(at) == kind
    policy.enforce_live_calendar(PERIOD, kind, at)
    with pytest.raises(ValueError):
        policy.enforce_live_calendar("20261030期", kind, at)


@pytest.mark.parametrize("chat,channel,profile", [
    ("oc_other", "江苏本地化", "supervisor-detail"),
    (policy.CHAT_ID, "人工外呼", "supervisor-detail"),
    (policy.CHAT_ID, "安徽本地化", "grade-compact"),
])
def test_group_scope_never_substitutes_another_group_or_channel(chat, channel, profile):
    with pytest.raises(ValueError):
        policy.enforce_group_scope(chat, channel, profile)


def test_threshold_is_inclusive_five_and_grade_scope_is_independent():
    rows = raw_rows("主管甲", "负责人甲", 5, 2)
    rows += raw_rows("主管乙", "负责人乙", 4, 0)
    rows += raw_rows("高中主管", "高中负责人", 20, 0, grade="高一")
    block = build(rows)["blocks"][0]
    assert [row["fields"]["主管"] for row in block["rows"]] == ["主管甲"]
    assert block["reminders"] == {"process": ["主管甲"], "result": ["主管甲"]}
    assert block["hidden_supervisors_below_minimum"] == ["主管乙"]


def test_sorting_and_tied_reminders_use_exact_aggregated_values():
    rows = raw_rows("主管甲", "负责人甲", 5, 2, net=20)
    rows += raw_rows("主管乙", "负责人乙", 10, 4, net=20)
    rows += raw_rows("主管丙", "负责人丙", 5, 4, net=30)
    block = build(rows)["blocks"][0]
    assert block["reminders"]["process"] == ["主管乙", "主管甲"]
    assert block["reminders"]["result"] == ["主管乙", "主管甲"]
    for section in ("process", "result"):
        assert report.sorted_rows(block, section)[0]["fields"]["主管"] == "主管丙"
    assert block["rows"][0]["fields"]["外呼频次"] == 2


def test_unresolved_person_falls_back_to_text_without_losing_other_mentions():
    rows = raw_rows("未入群主管", "负责人甲", 5, 2)
    rows += raw_rows("在群主管", "负责人乙", 5, 2)
    markdown = report.build_markdown(build(rows), PERIOD, "江苏本地化", "process",
        {"resolved": {"在群主管": "ou_offline"}, "display_names": {}}, {"process": "offline_image"})
    assert "未入群主管" in markdown
    assert '<at user_id="ou_offline">在群主管</at>' in markdown
    assert '<at user_id="None">' not in markdown


@pytest.mark.parametrize("section", ["process", "result"])
def test_localized_images_have_exact_columns_and_no_total_row(tmp_path, section):
    data = build(raw_rows("主管甲", "负责人甲", 5, 2))
    rendered = []

    def capture(draw, box, content, font, fill):
        rendered.append(content)
        _center_text(draw, box, content, font, fill)

    path = tmp_path / f"{section}.png"
    geometry = report.render_image(data, section, path, font_loader=_find_font,
        center_text=capture, format_value=_format_value, rate_parser=_rate)
    assert rendered[:len(report.COLUMNS[section])] == report.DISPLAY_COLUMNS[section]
    assert "总计" not in rendered
    assert geometry == [{"grade": "初三", "top": 0, "height": 156, "rows": 1}]
    with Image.open(path) as image:
        assert image.size == (sum(report.WIDTHS[section]), 156)


def test_shared_renderer_still_includes_totals_by_default(tmp_path):
    rendered = []
    base_report.render_image(build(raw_rows("主管甲", "负责人甲", 5, 2)), "result", tmp_path / "default.png",
        font_loader=_find_font, center_text=lambda draw, box, content, font, fill: rendered.append(content),
        format_value=_format_value, rate_parser=_rate)
    assert "总计" in rendered


@pytest.mark.parametrize("counts,present,absent", [
    ({"西安图书直播间-挂链": 8}, ["江苏本地化"], ["安徽本地化"]),
    ({"西安直播安徽": 8}, ["安徽本地化"], ["江苏本地化"]),
    ({"西安图书直播间-挂链": 8, "西安直播安徽": 4}, ["江苏本地化", "安徽本地化"], []),
    ({"其他": 20}, [], ["江苏本地化", "安徽本地化"]),
])
def test_missing_source_only_skips_that_province(definition, counts, present, absent):
    cfg = catalog.schedule_config(definition, definition["targets"][0])
    assert workflow.source_present_channels(cfg, {"periods": {PERIOD: {"channel_counts": counts}}}, PERIOD) == (present, absent)


@pytest.mark.parametrize("subset,volume", [([], False), (["未登记渠道"], False),
                                        (["江苏本地化", "江苏本地化"], False), (["江苏本地化"], True)])
def test_invalid_one_time_subset_is_rejected_before_any_outlet(definition, subset, volume):
    with patch.object(immediate, "runner_lock", side_effect=AssertionError("lock must not be reached")):
        with pytest.raises(ValueError, match="registered subset"):
            immediate.run(definition, definition["targets"][0], "offline-invalid", only_channels=subset, volume=volume)


@pytest.mark.parametrize("failing_channel", ["江苏本地化", "安徽本地化"])
def test_one_time_channel_error_does_not_block_other_province(definition, tmp_path, failing_channel):
    definition["state_dir"] = str(tmp_path)
    called = []
    folder = tmp_path / "immediate/offline-isolation"

    def fake_run(_definition, _target, request_id, *, preflight, only_channels):
        called.extend(only_channels)
        if only_channels == [failing_channel]:
            raise ValueError("offline simulated preparation failure")
        (folder / "preflight.json").write_text(json.dumps({"status": "immediate_preflight_passed_no_send",
            "channels": [{"channel": only_channels[0]}]}), encoding="utf-8")
        return 0

    with patch.object(immediate, "run", side_effect=fake_run):
        assert localization.send_now(definition, definition["targets"][0], "offline-isolation", preflight=True) == 1
    assert called == list(policy.CHANNELS)
    bundle = json.loads((folder / "preflight-bundle.json").read_text(encoding="utf-8"))
    assert [row["channel"] for row in bundle["outcomes"]] == list(policy.CHANNELS)
    assert next(row for row in bundle["outcomes"] if row["channel"] != failing_channel)["exit_code"] == 0


def test_one_time_receipt_rejects_cross_channel_fresh_receipts(definition, tmp_path):
    definition["state_dir"] = str(tmp_path)
    folder = tmp_path / "immediate/offline-wrong-receipt"

    def fake_run(*args, **kwargs):
        (folder / "preflight.json").write_text(json.dumps({"status": "unexpected",
            "channels": [{"channel": "其他渠道"}]}), encoding="utf-8")
        return 0

    with patch.object(immediate, "run", side_effect=fake_run):
        assert localization.send_now(definition, definition["targets"][0], "offline-wrong-receipt", preflight=True) == 1
    assert all(row["status"] == "failed" for row in json.loads(
        (folder / "preflight-bundle.json").read_text(encoding="utf-8"))["outcomes"])


@pytest.fixture
def exporter():
    path = Path(__file__).resolve().parents[2] / "scripts/export_channel_registry_records.py"
    spec = importlib.util.spec_from_file_location("localization_registry_export_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_operator_export_preserves_columns_threshold_and_no_totals(definition, exporter):
    record = exporter._operator_record(REF, definition)
    assert record["过程指标展示顺序（选填）"] == "、".join(EXPECTED_PROCESS)
    assert record["转化指标展示顺序（选填）"] == "、".join(EXPECTED_RESULT)
    assert record["门槛值"] == 5
    assert record["展示总计行"] is False


def test_operator_export_default_total_behavior_is_preserved(definition, exporter):
    definition["report"].pop("show_totals")
    assert exporter._operator_record(REF, definition)["展示总计行"] is True


def test_technical_export_retains_config_and_registered_scheduler(definition, exporter):
    with patch.object(exporter, "_task_state", return_value=(True, "Ready")):
        record = exporter._technical_record(REF, definition)
    assert record["计划任务已启用"] is True
    assert record["windows_task_name"] == "Codex-Lark-Supervisor-Localization-Grade9-Push"
    assert record["minimum_post_leads"] == 5
    assert json.loads(record["配置JSON快照"]) == deepcopy(definition)
    for field in ("定时参数文件路径", "任务执行脚本路径", "任务注册脚本路径"):
        assert "supervisor_localization_grade_9" in record[field]
