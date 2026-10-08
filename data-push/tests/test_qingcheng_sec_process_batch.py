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
from lark_delivery.common import retry  # noqa: E402
from lark_delivery.common import runtime  # noqa: E402


def test_sec_calendar_uses_same_week_friday_through_sunday():
    config = sec._config()
    assert sec._period(date(2026, 9, 26)) == "20260925期"
    assert sec._period(date(2026, 9, 27)) == "20260925期"
    assert sec._period(date(2026, 9, 29)) == "20261002期"
    zone = ZoneInfo("Asia/Shanghai")
    assert sec._slot(datetime(2026, 9, 27, 20, 2, tzinfo=zone), config).minute == 0
    with pytest.raises(ValueError, match="Outside"):
        sec._slot(datetime(2026, 9, 28, 12, 0, tzinfo=zone), config)
    with pytest.raises(ValueError, match="Outside"):
        sec._slot(datetime(2026, 9, 29, 20, 51, tzinfo=zone), config)


def test_supervisor_resolution_disambiguates_by_group_membership(monkeypatch):
    def contacts(args, timeout=90):
        assert args[:2] == ["contact", "+search-user"]
        return {"queries": [{"query": "杨亮", "has_more": False}], "users": [
            {"matched_query": "杨亮", "localized_name": "杨亮", "open_id": "ou_group1",
             "enterprise_email": "yangliang@gaotu.cn", "is_activated": True, "is_cross_tenant": False},
            {"matched_query": "杨亮", "localized_name": "杨亮", "open_id": "ou_else2",
             "enterprise_email": "yangliang02@gaotu.cn", "is_activated": True, "is_cross_tenant": False}]}

    monkeypatch.setattr(sec, "_data", contacts)
    review = {"reminders": [{"people": [{"name": "杨亮", "account": None}]}]}
    entry = {"unresolved_mention_action": "invite_then_text"}
    # Exactly one candidate in the group: membership disambiguates to a precise @.
    resolved, display, text_only = sec._resolve(entry, review, {"ou_group1"})
    assert resolved == {"杨亮": "ou_group1"}
    assert display == {"杨亮": "杨亮"}
    assert text_only == set()
    # Both candidates in the group: still ambiguous; 2026-10-04 policy falls back to
    # a plain-name mention instead of blocking the push.
    resolved, display, text_only = sec._resolve(entry, review, {"ou_group1", "ou_else2"})
    assert resolved == {}
    assert text_only == {"杨亮"}


def test_consultant_text_exception_does_not_mask_incomplete_contacts(monkeypatch):
    review = {"reminders": [{"people": [{"name": "离职顾问", "account": "former"}]}]}
    entry = {"unresolved_mention_action": "invite_then_text"}
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


def test_only_a_verified_receipt_is_settled(tmp_path):
    # The 2026-09-29 12:20 regression: a receipt whose send was never confirmed ended
    # the slot for good. It must come back as re-drivable instead.
    def status(payload):
        path = tmp_path / "receipt.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return sec._receipt_status(path)

    assert status({"status": "sent_verified", "message_id": "om_ok"})["status"] == "sent_verified"
    assert status({"status": "send_result_uncertain"}) is None
    assert status({"status": "send_attempt_started"}) is None
    assert status({"status": "sent_unverified", "message_id": "om_x"}) is None
    assert sec._receipt_status(tmp_path / "absent.json") is None


def test_recorded_message_id_is_reverified_without_sending(monkeypatch, tmp_path):
    # The safety half: a message already in the group is only ever re-read.
    folder = tmp_path / "sec_public_supervisor"
    folder.mkdir()
    receipt_path = folder / "send_receipt.json"
    receipt_path.write_text(json.dumps({
        "status": "sent_unverified", "message_id": "om_prior", "image_key": "img_k",
        "period": "20261002期", "mention_ids": ["ou_a"]}), encoding="utf-8")
    touched = []
    monkeypatch.setattr(sec, "upload_image", lambda *a, **k: touched.append("upload"))
    monkeypatch.setattr(sec, "_members", lambda *a, **k: touched.append("members"))
    monkeypatch.setattr(sec, "_verify_message",
                        lambda *a, **k: {"message_id": "om_prior", "verified": True})
    config = {"sender": {"open_id": "ou_bot"}}
    slot = datetime(2026, 9, 29, 12, 20, tzinfo=ZoneInfo("Asia/Shanghai"))
    entry = {"id": "sec_public_supervisor", "chat_id": "oc_x"}
    out = sec._deliver(entry, {"period": "20261002期", "image": "process.png"},
                       {"rev": 1}, config, folder, slot)
    assert out["status"] == "sent_verified"
    assert touched == []
    assert sec._receipt_status(receipt_path)["status"] == "sent_verified"


def test_unconfirmed_receipt_is_resent_to_the_send_path(monkeypatch, tmp_path):
    # No message id means nothing is in the group yet: the round must reach the send
    # path again rather than returning a "needs review" verdict.
    folder = tmp_path / "sec_public_supervisor"
    folder.mkdir()
    receipt_path = folder / "send_receipt.json"
    receipt_path.write_text(json.dumps({"status": "send_result_uncertain"}), encoding="utf-8")
    (folder / "process.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    monkeypatch.setattr(sec, "probe_revision", lambda *a, **k: 1)
    monkeypatch.setattr(sec, "_members", lambda *a, **k: {"ou_a"})
    monkeypatch.setattr(sec, "_resolve", lambda *a, **k: ({"A": "ou_a"}, {"A": "A"}, set()))
    monkeypatch.setattr(sec, "upload_image", lambda *a, **k: "img_uploaded")
    monkeypatch.setattr(sec, "_render", lambda *a, **k: "rendered")
    monkeypatch.setattr(sec, "_data", lambda *a, **k: {"message_id": "om_new"})
    monkeypatch.setattr(sec, "_verify_message",
                        lambda *a, **k: {"message_id": "om_new", "verified": True})
    monkeypatch.setattr(sec, "run_lark", lambda *a, **k: json.dumps({"ok": True}))
    config = {"sender": {"open_id": "ou_bot"}}
    slot = datetime(2026, 9, 29, 12, 20, tzinfo=ZoneInfo("Asia/Shanghai"))
    entry = {"id": "sec_public_supervisor", "chat_id": "oc_x", "source": "sec_public"}
    review = {"period": "20261002期", "image": "process.png", "reminders": [], "level": "主管"}
    out = sec._deliver(entry, review, {"rev": 1}, config, folder, slot)
    assert out["status"] == "sent_verified"
    saved = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert saved["resend_attempts"] == 1 and saved["prior_status"] == "send_result_uncertain"


def _send_stubs(monkeypatch, probe):
    """Everything a report needs to reach the send path, with the probe controlled."""
    monkeypatch.setattr(sec, "probe_revision", probe)
    monkeypatch.setattr(sec, "_members", lambda *a, **k: {"ou_a"})
    monkeypatch.setattr(sec, "_resolve", lambda *a, **k: ({"A": "ou_a"}, {"A": "A"}, set()))
    monkeypatch.setattr(sec, "upload_image", lambda *a, **k: "img_uploaded")
    monkeypatch.setattr(sec, "_render", lambda *a, **k: "rendered")
    monkeypatch.setattr(sec, "_data", lambda *a, **k: {"message_id": "om_new"})
    monkeypatch.setattr(sec, "_verify_message",
                        lambda *a, **k: {"message_id": "om_new", "verified": True})
    monkeypatch.setattr(sec, "run_lark", lambda *a, **k: json.dumps({"ok": True}))


def _report(tmp_path):
    folder = tmp_path / "sec_public_supervisor"
    folder.mkdir()
    (folder / "process.png").write_bytes(b"\x89PNG")
    return folder


def test_probe_transport_failure_is_retried_in_round(monkeypatch, tmp_path):
    # 2026-09-29 16:20: the pre-send Base probe hit a transport reset and three rounds
    # were discarded although nothing had been learned about the data. The probe is a
    # precondition read, so a connection failure is now retried inside the round.
    folder = _report(tmp_path)
    attempts = []

    def probe(*_a, **_k):
        attempts.append(1)
        if len(attempts) < 3:
            raise runtime.LarkTransportError("wsarecv: forcibly closed")
        return 1

    _send_stubs(monkeypatch, probe)
    monkeypatch.setattr(retry.time, "sleep", lambda _s: None)
    config = {"sender": {"open_id": "ou_bot"}}
    slot = datetime(2026, 9, 29, 16, 20, tzinfo=ZoneInfo("Asia/Shanghai"))
    entry = {"id": "sec_public_supervisor", "chat_id": "oc_x", "source": "sec_public"}
    review = {"period": "20261002期", "image": "process.png", "reminders": [], "level": "主管"}
    out = sec._deliver(entry, review, {"rev": 1}, config, folder, slot)
    assert out["status"] == "sent_verified"
    assert len(attempts) == 3


def test_probe_revision_drift_still_fails_closed(monkeypatch, tmp_path):
    # The converse property: a probe that *returns* a different revision is a verdict,
    # so it is never retried and the send never happens.
    folder = _report(tmp_path)
    attempts = []

    def probe(*_a, **_k):
        attempts.append(1)
        return 99  # a different revision than the snapshot's

    _send_stubs(monkeypatch, probe)
    monkeypatch.setattr(sec, "_data", lambda *a, **k: (_ for _ in ()).throw(
        AssertionError("no send may happen after a drift")))
    config = {"sender": {"open_id": "ou_bot"}}
    slot = datetime(2026, 9, 29, 16, 20, tzinfo=ZoneInfo("Asia/Shanghai"))
    entry = {"id": "sec_public_supervisor", "chat_id": "oc_x", "source": "sec_public"}
    review = {"period": "20261002期", "image": "process.png", "reminders": [], "level": "主管"}
    with pytest.raises(ValueError, match="revision changed before delivery"):
        sec._deliver(entry, review, {"rev": 1}, config, folder, slot)
    assert len(attempts) == 1
    assert not (folder / "send_receipt.json").exists()
