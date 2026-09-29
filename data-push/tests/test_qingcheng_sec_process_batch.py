"""The scheduled SEC batch keeps periods, mentions, and reports isolated."""

import json
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import run_qingcheng_sec_process as sec  # noqa: E402


def test_sec_calendar_uses_same_week_friday_through_sunday():
    config = sec._config()
    assert sec._period(date(2026, 9, 26)) == "20260925期"
    assert sec._period(date(2026, 9, 27)) == "20260925期"
    assert sec._period(date(2026, 9, 29)) == "20261002期"
    zone = ZoneInfo("Asia/Shanghai")
    assert sec._slot(datetime(2026, 9, 27, 20, 21, tzinfo=zone), config).minute == 20
    with pytest.raises(ValueError, match="Outside"):
        sec._slot(datetime(2026, 9, 28, 12, 20, tzinfo=zone), config)
    with pytest.raises(ValueError, match="Outside"):
        sec._slot(datetime(2026, 9, 29, 20, 19, tzinfo=zone), config)


def test_supervisor_resolution_requires_one_group_member_even_for_same_name(monkeypatch):
    def contacts(args, timeout=90):
        assert args[:2] == ["contact", "+search-user"]
        return {"queries": [{"query": "杨亮", "has_more": False}], "users": [
            {"matched_query": "杨亮", "localized_name": "杨亮", "open_id": "ou_group1",
             "enterprise_email": "yangliang@gaotu.cn", "is_activated": True, "is_cross_tenant": False},
            {"matched_query": "杨亮", "localized_name": "杨亮", "open_id": "ou_else2",
             "enterprise_email": "yangliang02@gaotu.cn", "is_activated": True, "is_cross_tenant": False}]}

    monkeypatch.setattr(sec, "_data", contacts)
    review = {"reminders": [{"people": [{"name": "杨亮", "account": None}]}]}
    entry = {"unresolved_mention_action": "block_send"}
    resolved, display, text_only = sec._resolve(entry, review, {"ou_group1"})
    assert resolved == {"杨亮": "ou_group1"}
    assert display == {"杨亮": "杨亮"}
    assert text_only == set()
    with pytest.raises(ValueError, match="unresolved or ambiguous"):
        sec._resolve(entry, review, {"ou_group1", "ou_else2"})


def test_consultant_text_exception_does_not_mask_incomplete_contacts(monkeypatch):
    review = {"reminders": [{"people": [{"name": "离职顾问", "account": "former"}]}]}
    entry = {"unresolved_mention_action": "text_only_for_that_person"}
    monkeypatch.setattr(sec, "_data", lambda args, timeout=90: {
        "queries": [{"query": "former@gaotu.cn", "has_more": False}], "users": []})
    assert sec._resolve(entry, review, set())[2] == {"former"}
    monkeypatch.setattr(sec, "_data", lambda args, timeout=90: {
        "queries": [{"query": "former@gaotu.cn", "has_more": True}], "users": []})
    with pytest.raises(ValueError, match="incomplete"):
        sec._resolve(entry, review, set())


def test_one_sec_report_failure_does_not_block_other_reports(monkeypatch, tmp_path):
    zone = ZoneInfo("Asia/Shanghai")
    now = datetime(2026, 9, 29, 12, 20, tzinfo=zone)
    monkeypatch.setattr(sec, "_upstream_audit", lambda period, slot: {
        "snapshot": ["20260929", "10"],
        "raw_channel_counts": {"公域学霸": 10, "SEC未加好友": 10, "SEC首期掉海": 10,
                               "SEC招生退费": 0}})
    monkeypatch.setattr(sec, "_source_rows", lambda source, period, output, audit, cfg, slot: (
        [{"渠道": "SEC未加好友"}], {"rev": 42, "snapshot": ["20260929", "10"], "period": period}))
    monkeypatch.setattr(sec, "_build_report", lambda entry, rows, manifest, cfg, output: {"period": manifest["period"]})

    def deliver(entry, review, manifest, cfg, output, slot):
        if entry["id"] == "sec_no_friend_supervisor":
            raise ValueError("one group reminder cannot be resolved")
        return {"status": "sent_verified", "message_id": "om_example"}

    monkeypatch.setattr(sec, "_deliver", deliver)
    result = sec.run(now=now, output=tmp_path)
    assert result["reports"]["sec_no_friend_supervisor"]["status"] == "blocked"
    assert [result["reports"][report]["status"] for report in sec.REPORT_IDS[1:]] == ["sent_verified"] * 4
    assert json.loads((tmp_path / "batch.json").read_text(encoding="utf-8"))["reports"] == result["reports"]
