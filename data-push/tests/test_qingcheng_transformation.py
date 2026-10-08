"""Schedule and upstream pin checks for the Qingcheng transformation batch."""

import importlib.util
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


def test_monday_window_starts_at_four_and_reads_the_zero_partition_cycle():
    batch = MODULE._batch()
    with pytest.raises(ValueError, match="Outside"):
        MODULE._slot(datetime(2026, 10, 5, 2, 0, tzinfo=SHANGHAI), batch)

    slot = MODULE._slot(datetime(2026, 10, 5, 4, 0, tzinfo=SHANGHAI), batch)
    assert slot.strftime("%Y%m%d%H%M") == "202610050400"
    retry_slot = MODULE._slot(datetime(2026, 10, 5, 4, 2, tzinfo=SHANGHAI), batch)
    assert retry_slot == slot
    assert MODULE._dept_active(slot) is True


def test_other_transformation_windows_keep_the_two_minute_start():
    batch = MODULE._batch()
    slot = MODULE._slot(datetime(2026, 10, 2, 14, 2, tzinfo=SHANGHAI), batch)
    assert slot.strftime("%Y%m%d%H%M") == "202610021402"
    assert MODULE._dept_active(slot) is True


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
