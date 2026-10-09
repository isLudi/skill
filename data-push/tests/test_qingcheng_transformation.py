"""Schedule and upstream pin checks for the Qingcheng transformation batch."""

import importlib.util
import json
from datetime import datetime
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/run_qingcheng_transformation.py"
CONFIG_DIR = Path(__file__).resolve().parents[1] / "config/departments/qingcheng"
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("qingcheng_transformation_batch", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
import preview_qingcheng_transformation as PREVIEW
import send_qingcheng_transformation as SEND

SHANGHAI = ZoneInfo("Asia/Shanghai")


def test_batch_pins_the_published_t5_upstream():
    batch = MODULE._batch()
    assert batch["upstream"]["task_id"] == 47775
    assert batch["upstream"]["nezha_task_id"] == 67397
    assert batch["upstream"]["published_version"] == "V6"
    assert batch["upstream"]["version_id"] == 207547
    assert batch["upstream"]["source_sha256"] == (
        "97aed7e48398d6a4321e0b11fab0cff44de67edb8f5f21622e7d1424a0521a39"
    )


@pytest.mark.parametrize("day", [9, 10, 11, 12])
@pytest.mark.parametrize("hour", [13, 17, 21])
def test_conversion_runs_three_daytime_windows_including_monday(day, hour):
    batch = MODULE._batch()
    slot = MODULE._slot(datetime(2026, 10, day, hour, 52, tzinfo=SHANGHAI), batch)
    retry = MODULE._slot(datetime(2026, 10, day, hour + 1, 44, tzinfo=SHANGHAI), batch)
    assert retry == slot
    assert MODULE._period(slot.date()) == "20261009期"


def test_dept_has_one_independent_slot_and_no_monday_night_slot():
    batch = MODULE._batch()
    for day in (9, 10, 11, 12):
        now = datetime(2026, 10, day, 13, 50, tzinfo=SHANGHAI)
        slot = MODULE._slot(now, batch, "dept")
        assert MODULE._slot(now.replace(hour=14, minute=42), batch, "dept") == slot
        with pytest.raises(ValueError, match="Outside"):
            MODULE._slot(now.replace(hour=17), batch, "dept")
    for audience in ("standard", "dept"):
        with pytest.raises(ValueError, match="Outside"):
            MODULE._slot(datetime(2026, 10, 12, 4, 0, tzinfo=SHANGHAI), batch, audience)
        with pytest.raises(ValueError, match="Outside"):
            MODULE._slot(datetime(2026, 10, 12, 14, 46, tzinfo=SHANGHAI), batch, audience)


def test_conversion_metric_label_is_comprehensive_effect_everywhere():
    config = (CONFIG_DIR / "transformation_preview.json").read_text(encoding="utf-8")
    assert "综合单效" in config
    assert PREVIEW.REMINDER_METRIC == "综合单效"
    assert SEND.REMINDER_METRIC == "综合单效"
    assert PREVIEW._display_transformation(1234.5, "综合单效") == "1,234.5"
    with pytest.raises(ValueError, match="display rule"):
        PREVIEW._display_transformation(1234.5, "旧版单效")

    for path in CONFIG_DIR.glob("*_request.json"):
        text = path.read_text(encoding="utf-8")
        if '"result_display_order": "' in text or '"result_metric": "' in text:
            assert "综合单效" in text, path.name


@pytest.mark.parametrize("period_date", ["20261009", "20261016"])
def test_batch_passes_its_requested_period_to_every_channel(monkeypatch, tmp_path, period_date):
    calls = []

    def fetch(channel, period, output):
        return {"rev": 1, "snapshot": ["20261008", "12"]}

    def export(channel, period, output, *, cache_dir):
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(dict.fromkeys(MODULE.ZERO_FIELDS, 0)), encoding="utf-8")
        return {"rev": 2}

    def build(process_source, conversion_source, output, config_path, channels, *, period, levels):
        calls.append((channels, period, levels))
        return {"period": period, "conversion_snapshot": "20261008 12:00",
                "results": {channels[0]: {"levels": {levels[0]: {}}}}}

    monkeypatch.setattr(MODULE, "fetch", fetch)
    monkeypatch.setattr(MODULE, "export_conversion", export)
    monkeypatch.setattr(MODULE, "build", build)
    monkeypatch.setattr(MODULE, "_index", lambda *args: None)
    result = MODULE.run(period_date=period_date, output=tmp_path)
    assert calls == [((channel,), period_date + "期", (level,))
                     for channel in MODULE.CHANNEL_IDS for level in MODULE._channel_levels(channel)]
    assert all(group["status"] == "prepared" for item in result["channels"].values()
               for group in item["groups"].values())


@pytest.mark.parametrize("period", ["20261009期", "20261016期"])
def test_restored_supervisor_style_uses_batch_period_instead_of_preview_default(monkeypatch, tmp_path, period):
    config = json.loads(PREVIEW.DEFAULT_CONFIG.read_text(encoding="utf-8"))
    channel = next(c for c in config["channels"] if c["id"] == "partner_local")
    channel.pop("consultant_request")
    config["channels"] = [channel]
    config["source"]["current_periods"] = ["20261002期"]
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config, ensure_ascii=True), encoding="utf-8")
    cases = [("20261002期", "高一", "旧期主管", 1000),
             (period, "高一", "新期主管", 100),
             (period, "高二", "并列主管甲", 50),
             (period, "高二", "并列主管乙", 50)]
    process, conversion = [], []
    for i, (row_period, grade, name, income) in enumerate(cases):
        row = {**channel["match"], "期次": row_period, "年级": grade, "主管": name,
               "顾问账号": f"account_{i}", "顾问": f"顾问{i}",
               "分区日期": "20261008", "分区小时": "12"}
        process.append({**row, "record_id": f"process_{i}", "退后线索": 5, "首节到课标记": 0})
        conversion.append({**row, "record_id": f"conversion_{i}",
                           "记录键": f"{row_period}|conversion_fact|{i}|a|b|c",
                           "收款": income, "退费": 0, "净收款": income, "当期收款": income,
                           "成交人头": 1, "报科数": 1, "破蛋人数标记": 1,
                           "成交周期天数分子": 1, "成交周期成交人数分母": 1})
    for name, rows in (("process", process), ("conversion", conversion)):
        (tmp_path / f"{name}.ndjson").write_text(
            "\n".join(json.dumps(row, ensure_ascii=True) for row in rows), encoding="utf-8")
        (tmp_path / f"{name}.manifest.json").write_text(
            json.dumps({"has_more": False, "records_count": len(rows), "rev": 1}), encoding="utf-8")
    images = []
    monkeypatch.setattr(PREVIEW, "_table_image", lambda *args, **kwargs: images.append((args, kwargs)))

    review = PREVIEW.build(tmp_path / "process.ndjson", tmp_path / "conversion.ndjson",
                           tmp_path / "new", config_path, period=period)
    item = review["results"]["partner_local"]["levels"]["supervisor"]
    assert review["period"] == period
    assert item["reminder_mode"] == "grade_text"
    assert item["reminder_grades"] == ["高一"]
    assert item["reminder_people"] is None
    assert item["reminder_by_grade"] is None
    assert "综合单效较高年级：高一" in item["message"]
    assert "新期主管" not in item["message"]
    assert "并列主管" not in item["message"]
    assert "旧期主管" not in item["message"]
    assert f"【{period}】" in item["message"]
    assert images[-1][0][4] == period
    assert images[-1][1]["split_grade"] is True

    # Standalone previews retain the explicitly configured historical period.
    old = PREVIEW.build(tmp_path / "process.ndjson", tmp_path / "conversion.ndjson",
                        tmp_path / "old", config_path)
    assert old["period"] == "20261002期"
    assert old["results"]["partner_local"]["levels"]["supervisor"]["reminder_grades"] == ["高一"]
    assert "旧期主管" not in old["results"]["partner_local"]["levels"]["supervisor"]["message"]
