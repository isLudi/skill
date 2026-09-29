"""One preview batch and independent delivery outcomes for six groups."""

import importlib.util
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/run_qingcheng_process.py"
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("qingcheng_process_batch", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_schedule_excludes_0225_and_rolls_to_business_friday():
    batch = MODULE._batch()
    now = datetime(2026, 9, 29, 14, 26, tzinfo=ZoneInfo("Asia/Shanghai"))
    slot = MODULE._slot(now, batch)
    assert slot.strftime("%Y%m%d%H%M") == "202609291425"
    assert MODULE._period(slot.date()) == "20261002期"
    with pytest.raises(ValueError, match="Outside"):
        MODULE._slot(datetime(2026, 9, 29, 2, 25, tzinfo=ZoneInfo("Asia/Shanghai")), batch)


def test_one_groups_mention_failure_does_not_block_other_groups(monkeypatch, tmp_path):
    batch = MODULE._batch()
    result = {"period": "20261002期", "channels": {key: {"source_rev": 100,
              "groups": {level: {"status": "prepared"} for level in MODULE.LEVELS}}
              for key in ("public_pool", "private", "douyin_dm")}}
    monkeypatch.setattr(MODULE, "probe_revision", lambda *args: 100)
    calls = []

    def send(channel, level, *_args):
        calls.append((channel, level))
        if (channel, level) == ("private", "supervisor"):
            raise ValueError("Reminder person is not in this group")
        return {"status": "sent_verified"}

    monkeypatch.setattr(MODULE, "_send_group", send)
    MODULE._deliver_groups(batch, result, tmp_path, datetime(2026, 9, 29, 14, 25, tzinfo=ZoneInfo("Asia/Shanghai")))
    assert calls == [("public_pool", "supervisor"), ("public_pool", "consultant"),
                     ("private", "supervisor"), ("private", "consultant"),
                     ("douyin_dm", "supervisor"), ("douyin_dm", "consultant")]
    assert result["channels"]["private"]["groups"]["supervisor"]["status"] == "blocked"
    assert result["channels"]["private"]["groups"]["consultant"]["status"] == "sent_verified"
    assert result["channels"]["douyin_dm"]["groups"]["supervisor"]["status"] == "sent_verified"


def test_batch_send_is_disabled_when_config_is_preview_only(monkeypatch):
    original = MODULE._batch()
    monkeypatch.setattr(MODULE, "_batch", lambda: {**original, "status": "preview_only", "schedule_enabled": False})
    with pytest.raises(ValueError, match="disabled"):
        MODULE.run(confirm_send=True, now=datetime(2026, 9, 29, 14, 25, tzinfo=ZoneInfo("Asia/Shanghai")))


def test_one_groups_image_failure_does_not_block_other_groups(monkeypatch, tmp_path):
    original = MODULE._batch()
    monkeypatch.setattr(MODULE, "_batch", lambda: original)
    for entry in original["channels"]:
        original_config = MODULE.CONFIG_DIR / entry["config"]
        (tmp_path / entry["config"]).write_text(original_config.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(MODULE, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(MODULE, "_upstream_audit", lambda *_args: {
        "execution_id": 1, "snapshot": ["20260929", "12"],
        "expected_counts": {channel: 1 for channel in MODULE.AUDIT_CHANNELS}})
    monkeypatch.setattr(MODULE, "fetch", lambda channel, period, output: {
        "rev": 100, "records_count": 1, "snapshot": ["20260929", "12"]})

    def build(_source, _supervisor, _consultant, _output, _config, *, levels):
        level = levels[0]
        if (_output.parent.name, level) == ("private", "supervisor"):
            raise ValueError("Image failed")
        return {"period": "20261002期", "snapshot": "20260929 12:00",
                "results": {level: {"level": "主管" if level == "supervisor" else "顾问",
                                    "process_rows": 1, "process_png": "x.png", "process_message": "x"}}}

    monkeypatch.setattr(MODULE, "build", build)
    monkeypatch.setattr(MODULE, "probe_revision", lambda *_args: 100)
    sent = []
    monkeypatch.setattr(MODULE, "_send_group", lambda channel, level, *_args: sent.append((channel, level)) or {"status": "sent_verified"})
    result = MODULE.run(confirm_send=True, now=datetime(2026, 9, 29, 14, 25,
                        tzinfo=ZoneInfo("Asia/Shanghai")), output=tmp_path / "slot")
    assert result["channels"]["private"]["groups"]["supervisor"]["status"] == "blocked_prepare"
    assert len(sent) == 5
    assert ("private", "consultant") in sent
    assert ("douyin_dm", "supervisor") in sent
