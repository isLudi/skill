"""The special-channel image task isolates each report and keeps its slot rules."""

import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import run_qingcheng_special_process as special  # noqa: E402
import fetch_qingcheng_process_source as source  # noqa: E402


def test_special_process_slot_and_period():
    cfg = special._config()
    zone = ZoneInfo("Asia/Shanghai")
    slot = special._slot(datetime(2026, 9, 29, 13, 52, tzinfo=zone), cfg)
    assert (slot.hour, slot.minute) == (13, 50)
    assert special._period(datetime(2026, 9, 29).date()) == "20261002期"
    for now in (datetime(2026, 9, 29, 2, 0, tzinfo=zone),
                datetime(2026, 9, 29, 14, 3, tzinfo=zone),
                datetime(2026, 9, 29, 14, 51, tzinfo=zone),
                datetime(2026, 9, 27, 14, 0, tzinfo=zone)):
        with pytest.raises(ValueError, match="Outside"):
            special._slot(now, cfg)


@pytest.mark.parametrize("source_key,primary,secondary", [
    ("special_books", "图书", "武汉图书"),
    ("special_public_pool", "公海", "顾问未加好友"),
])
def test_special_source_fetch_filters_primary_channel_only(monkeypatch, tmp_path, source_key, primary, secondary):
    def fake_lark(args, **kwargs):
        condition = json.loads(args[args.index("--filter-json") + 1])["conditions"]
        assert condition == [["一级渠道", "==", primary], ["期次", "==", "20260925期"]]
        path = Path(args[args.index("--output") + 1])
        path.write_text(json.dumps({"record_id": "rec_1", "记录键": "business_1", "一级渠道": primary,
                                    "期次": "20260925期", "渠道": secondary,
                                    "分区日期": "20260927", "分区小时": "18"}, ensure_ascii=False) + "\n",
                        encoding="utf-8")
        path.with_suffix(".manifest.json").write_text(json.dumps({
            "base_token": source.BASE_TOKEN, "table_id": source.TABLE_ID,
            "records_count": 1, "rev": 42, "has_more": False}), encoding="utf-8")
        return ""

    monkeypatch.setattr(source, "run_lark", fake_lark)
    manifest = source.fetch(source_key, "20260925期", tmp_path / "source.ndjson")
    assert manifest["channel"] == source_key
    assert manifest["records_count"] == 1


@pytest.mark.parametrize("failed_stage", ["source", "build", "delivery"])
def test_one_special_channel_failure_does_not_block_other_images(monkeypatch, tmp_path, failed_stage):
    now = datetime(2026, 9, 29, 13, 52, tzinfo=ZoneInfo("Asia/Shanghai"))
    counts = {name: 10 for group in special.AUDIT_NAMES for name in group}
    monkeypatch.setattr(special, "_upstream_audit", lambda period, slot: {
        "snapshot": ["20260929", "12"], "raw_channel_counts": counts})

    def source(entry, period, folder, audit, slot):
        if failed_stage == "source" and entry["id"] == "special_books":
            raise ValueError("bad book source")
        return [{}], {"rev": 42, "snapshot": ["20260929", "12"], "period": period}

    def build(entry, rows, manifest, cfg, folder):
        if failed_stage == "build" and entry["id"] == "special_books":
            raise ValueError("bad book image")
        return {"period": manifest["period"]}

    def deliver(entry, review, manifest, cfg, folder, slot):
        if failed_stage == "delivery" and entry["id"] == "special_books":
            raise ValueError("bad book delivery")
        return {"status": "sent_verified", "message_id": "om_example"}

    monkeypatch.setattr(special, "_source", source)
    monkeypatch.setattr(special, "_build", build)
    monkeypatch.setattr(special, "_deliver", deliver)
    result = special.run(now=now, output=tmp_path)
    assert result["channels"]["special_books"]["status"] == (
        "blocked_delivery" if failed_stage == "delivery" else "blocked_prepare")
    assert [result["channels"][channel]["status"] for channel in special.CHANNEL_IDS
            if channel != "special_books"] == ["sent_verified"] * 3
    assert json.loads((tmp_path / "batch.json").read_text(encoding="utf-8"))["channels"] == result["channels"]


def test_only_a_verified_receipt_is_terminal(tmp_path):
    # A receipt that never recorded a message id must be re-driven, not treated as
    # the end of the slot: that guard cost the 2026-09-29 12:20 SEC broadcast.
    settled = tmp_path / "settled.json"
    settled.write_text(json.dumps({"status": "sent_verified", "message_id": "om_ok"}), encoding="utf-8")
    assert special._existing(settled)["status"] == "sent_verified"

    uncertain = tmp_path / "uncertain.json"
    uncertain.write_text(json.dumps({"status": "send_result_uncertain"}), encoding="utf-8")
    assert special._existing(uncertain) is None

    unverified = tmp_path / "unverified.json"
    unverified.write_text(json.dumps({"status": "sent_unverified", "message_id": "om_prior"}), encoding="utf-8")
    assert special._existing(unverified) is None


def test_unconfirmed_receipt_no_longer_ends_the_round(monkeypatch, tmp_path):
    now = datetime(2026, 9, 29, 13, 52, tzinfo=ZoneInfo("Asia/Shanghai"))
    folder = tmp_path / "special_private"
    folder.mkdir()
    (folder / "send_receipt.json").write_text(
        json.dumps({"status": "send_result_uncertain"}), encoding="utf-8")
    monkeypatch.setattr(special, "_upstream_audit", lambda period, slot: {
        "snapshot": ["20260929", "12"], "raw_channel_counts": {}})
    result = special.run(now=now, output=tmp_path)
    # The stale receipt no longer freezes this channel; it is re-driven like the rest.
    assert all(result["channels"][channel]["status"] == "skipped_no_source_rows"
               for channel in special.CHANNEL_IDS)


def test_recorded_message_id_is_reverified_without_sending(monkeypatch, tmp_path):
    # The safety half: a message already in the group is only ever re-read.
    folder = tmp_path / "special_private"
    folder.mkdir()
    receipt_path = folder / "send_receipt.json"
    receipt_path.write_text(json.dumps({
        "status": "sent_unverified", "message_id": "om_prior", "image_key": "img_k",
        "period": "20261002期", "resend_attempts": 0}), encoding="utf-8")
    touched = []
    monkeypatch.setattr(special, "upload_image", lambda *a, **k: touched.append("upload"))
    monkeypatch.setattr(special, "_data", lambda *a, **k: touched.append("send"))
    monkeypatch.setattr(special, "_verify_message",
                        lambda *a, **k: {"message_id": "om_prior", "verified": True})
    via = {"target_chat_id": "oc_x", "sender": {"open_id": "ou_x"}}
    out = special._deliver({"id": "special_private", "source_key": "private", "name": "私域"},
                           {"period": "20261002期", "image": "process.png"}, {"rev": 1},
                           via, folder, datetime(2026, 9, 29, 13, 52, tzinfo=ZoneInfo("Asia/Shanghai")))
    assert out["status"] == "sent_verified"
    assert touched == []
    assert special._existing(receipt_path)["status"] == "sent_verified"
