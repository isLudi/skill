from datetime import datetime, timedelta
import json
from zoneinfo import ZoneInfo

import pytest

import run_qingcheng_process as process
import run_qingcheng_transformation as conversion
from qingcheng_schedule import delivery_deadline, require_delivery_window


SLOT = datetime(2026, 11, 20, 13, 52, tzinfo=ZoneInfo("Asia/Shanghai"))


def test_process_skips_platform_when_every_group_was_verified(monkeypatch, tmp_path):
    batch = {"status": "active", "schedule_enabled": True, "upstream_binding": {},
             "channels": [{"id": "private", "config": "private.json"}]}
    (tmp_path / "private.json").write_text(json.dumps({"channel_id": "private", "report_type": "process",
                                                       "status": "active", "schedule_enabled": True}), encoding="utf-8")
    monkeypatch.setattr(process, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(process, "_batch", lambda: batch)
    monkeypatch.setattr(process, "_slot", lambda *_: SLOT)
    monkeypatch.setattr(process, "_period", lambda *_: "20261120期")
    monkeypatch.setattr(process, "_receipt_path", lambda *args: tmp_path / "receipt.json")
    monkeypatch.setattr(process, "_receipt_state", lambda *_: (process.resend.DONE, "message"))
    monkeypatch.setattr(process, "_upstream_audit", lambda *_: pytest.fail("already sent groups need no platform audit"))
    monkeypatch.setattr(process, "fetch", lambda *_: pytest.fail("already sent groups need no Base fetch"))
    monkeypatch.setattr(process, "_index", lambda *_: None)
    monkeypatch.setattr(process, "_deliver_groups", lambda *_: None)
    result = process.run(confirm_send=True, now=SLOT, output=tmp_path / "slot")
    assert result["upstream_check_skipped"] == "all_groups_already_verified"
    assert {v["status"] for v in result["channels"]["private"]["groups"].values()} == {"sent_verified"}


def test_conversion_skips_source_fetch_for_verified_group(monkeypatch, tmp_path):
    batch = {"status": "active", "schedule_enabled": True,
             "channels": [{"id": "partner_books", "config": "unused.json", "scheduled": True}]}
    monkeypatch.setattr(conversion, "_batch", lambda: batch)
    monkeypatch.setattr(conversion, "_slot", lambda *_: SLOT)
    monkeypatch.setattr(conversion, "_period", lambda *_: "20261120期")
    monkeypatch.setattr(conversion, "_channel_levels", lambda *_: ("consultant",))
    monkeypatch.setattr(conversion, "_config_chat_id", lambda *_: "chat")
    monkeypatch.setattr(conversion, "_receipt_state", lambda *_: (conversion.resend.DONE, "message"))
    monkeypatch.setattr(conversion, "fetch", lambda *_, **__: pytest.fail("verified group needs no process fetch"))
    monkeypatch.setattr(conversion, "export_conversion", lambda *_, **__: pytest.fail("verified group needs no conversion fetch"))
    monkeypatch.setattr(conversion, "_index", lambda *_: None)
    monkeypatch.setattr(conversion, "_deliver_groups", lambda *_: None)
    result = conversion.run(confirm_send=True, now=SLOT, output=tmp_path / "slot")
    assert result["channels"]["partner_books"]["groups"]["consultant"]["status"] == "sent_verified"


@pytest.mark.parametrize("window, expected_minutes", [(50, 51), (53, 53)])
def test_delayed_send_cannot_escape_last_authorized_retry_minute(window, expected_minutes):
    calendar = {"retry_window_minutes": window, "retry_interval_minutes": 2}
    deadline = delivery_deadline(SLOT, calendar)
    assert deadline == SLOT + timedelta(minutes=expected_minutes)
    require_delivery_window(SLOT, calendar, now=deadline - timedelta(milliseconds=1))
    with pytest.raises(ValueError, match="missed"):
        require_delivery_window(SLOT, calendar, now=deadline)
