from datetime import datetime, timedelta
import json
import sys
from zoneinfo import ZoneInfo

import pytest

import fetch_qingcheng_process_source as process_source
import run_qingcheng_transformation as runner
import send_qingcheng_transformation as sender


def prepare(tmp_path, monkeypatch):
    config = {"report_type": "transformation", "status": "active", "schedule_enabled": True,
              "delivery": {"sender_identity": "bot", "mention_format": "native_at",
                           "require_complete_group_membership": True, "on_mention_gap": "invite_then_text",
                           "sender_open_id": "ou_bot"},
              "channels": [{"id": "partner_books", "profiles": {"consultant": {
                  "level": "顾问", "target_chat_id": "oc_test"}}}]}
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")
    review = {"period": "20261120期", "results": {"partner_books": {"levels": {"consultant": {
        "level": "顾问", "reminder_people": [], "png": "x.png", "message_file": "message.md"}}}}}
    (tmp_path / "review.json").write_text(json.dumps(review, ensure_ascii=False), encoding="utf-8")
    (tmp_path / "message.md").write_text("test", encoding="utf-8")
    deadline = (datetime.now(ZoneInfo("Asia/Shanghai")) + timedelta(minutes=5)).isoformat()
    monkeypatch.setattr(sys, "argv", ["send", "--channel", "partner_books", "--level", "consultant",
        "--review-dir", str(tmp_path), "--config", str(config_path), "--idempotency-key", "test_key",
        "--send", "--image-key", "img_test", "--delivery-deadline", deadline,
        "--expected-process-rev", "10", "--expected-conversion-rev", "20"])


def test_missing_group_membership_stops_before_tiangong_read(tmp_path, monkeypatch):
    prepare(tmp_path, monkeypatch)
    monkeypatch.setattr(sender, "verify_sender_membership", lambda *_: (_ for _ in ()).throw(ValueError("not in chat")))
    monkeypatch.setattr(runner, "_conversion_upstream_ready", lambda *_: pytest.fail("platform must not be called"))
    with pytest.raises(ValueError, match="not in chat"):
        sender.main()


def test_base_revision_is_checked_after_waiting_for_tiangong(tmp_path, monkeypatch):
    prepare(tmp_path, monkeypatch)
    monkeypatch.setattr(sender, "verify_sender_membership", lambda *_: None)
    monkeypatch.setattr(runner, "_batch", lambda: {})
    monkeypatch.setattr(runner, "_conversion_upstream_ready", lambda *_: 123)
    monkeypatch.setattr(process_source, "probe_revision", lambda *_, **__: 11)
    monkeypatch.setattr(runner, "_probe_conversion_rev", lambda *_: 20)
    monkeypatch.setattr(sender, "_render_message", lambda *_: "message")
    monkeypatch.setattr(sender, "_data", lambda *_: pytest.fail("stale data must not be sent"))
    with pytest.raises(ValueError, match="revision changed"):
        sender.main()
