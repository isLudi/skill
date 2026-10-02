"""One preview batch and independent delivery outcomes for six groups."""

import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

from lark_delivery.common import resend


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/run_qingcheng_process.py"
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("qingcheng_process_batch", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_schedule_excludes_0200_and_rolls_to_business_friday():
    batch = MODULE._batch()
    now = datetime(2026, 9, 29, 14, 2, tzinfo=ZoneInfo("Asia/Shanghai"))
    slot = MODULE._slot(now, batch)
    assert slot.strftime("%Y%m%d%H%M") == "202609291400"
    assert MODULE._period(slot.date()) == "20261002期"
    with pytest.raises(ValueError, match="Outside"):
        MODULE._slot(datetime(2026, 9, 29, 2, 0, tzinfo=ZoneInfo("Asia/Shanghai")), batch)


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
    MODULE._deliver_groups(batch, result, tmp_path, datetime(2026, 9, 29, 14, 2, tzinfo=ZoneInfo("Asia/Shanghai")))
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
        MODULE.run(confirm_send=True, now=datetime(2026, 9, 29, 14, 2, tzinfo=ZoneInfo("Asia/Shanghai")))


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
    result = MODULE.run(confirm_send=True, now=datetime(2026, 9, 29, 14, 2,
                        tzinfo=ZoneInfo("Asia/Shanghai")), output=tmp_path / "slot")
    assert result["channels"]["private"]["groups"]["supervisor"]["status"] == "blocked_prepare"
    assert len(sent) == 5
    assert ("private", "consultant") in sent
    assert ("douyin_dm", "supervisor") in sent


def test_receipt_verdicts_cover_both_child_receipt_shapes(tmp_path):
    # The child writes two shapes: a failure carries `status`; a success is the raw
    # send output with NO status field at all, so `readback.verified` decides it.
    def verdict(payload):
        path = tmp_path / "receipt.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return MODULE._receipt_state(path)[0]

    assert verdict({"status": "send_attempt_started"}) == resend.RESEND
    assert verdict({"status": "send_result_uncertain"}) == resend.RESEND
    assert verdict({"response": {"message_id": "om_x"}}) == resend.REVERIFY
    assert verdict({"response": {"message_id": "om_x"}, "readback": {"verified": False}}) == resend.REVERIFY
    assert verdict({"response": {"message_id": "om_x"}, "readback": {"verified": True}}) == resend.DONE
    assert MODULE._receipt_state(tmp_path / "absent.json") == (resend.RESEND, "")


def _group_fixture(tmp_path):
    entry = MODULE._batch()["channels"][0]
    review_dir = tmp_path / "supervisor"
    review_dir.mkdir()
    return (entry["id"], MODULE.CONFIG_DIR / entry["config"], review_dir,
            "20261002期", datetime(2026, 9, 29, 14, 2, tzinfo=ZoneInfo("Asia/Shanghai")))


def _record_commands(monkeypatch):
    """Record the child *sender* invocations only.

    `_send_group` also probes the readback-availability API on a failure path, and that
    goes through the same `subprocess.run`; counting it would confuse "was a send
    issued?" with "was the group asked about"."""
    calls = []

    def fake_run(command, **_kwargs):
        if any("send_qingcheng_process.py" in str(part) for part in command):
            calls.append(command)
        return SimpleNamespace(returncode=0, stderr="",
                              stdout=json.dumps({"readback": {"verified": True, "message_id": "om_prior"}}))

    monkeypatch.setattr(MODULE.subprocess, "run", fake_run)
    return calls


def test_receipt_with_a_message_id_is_reverified_never_resent(monkeypatch, tmp_path):
    # The safety half: a message already in the group must never be re-issued.
    channel, config_path, review_dir, period, slot = _group_fixture(tmp_path)
    receipt = MODULE._receipt_path(channel, "supervisor", config_path, review_dir, period, slot)
    receipt.write_text(json.dumps({"response": {"message_id": "om_prior"}, "image_key": "img_k",
                                   "readback": {"verified": False}}), encoding="utf-8")
    calls = _record_commands(monkeypatch)
    out = MODULE._send_group(channel, "supervisor", config_path, review_dir, period, slot)
    assert out["status"] == "sent_verified"
    assert len(calls) == 1
    assert "--reverify-only" in calls[0] and "--send" not in calls[0]


def test_unconfirmed_receipt_is_resent_with_the_same_key(monkeypatch, tmp_path):
    # An unconfirmed send must be re-driven rather than freezing the slot, and the key
    # is the one already on record so the platform dedupes if the first attempt landed.
    channel, config_path, review_dir, period, slot = _group_fixture(tmp_path)
    receipt = MODULE._receipt_path(channel, "supervisor", config_path, review_dir, period, slot)
    receipt.write_text(json.dumps({"status": "send_result_uncertain"}), encoding="utf-8")
    key = receipt.stem.split("_send_")[-1]
    calls = _record_commands(monkeypatch)
    out = MODULE._send_group(channel, "supervisor", config_path, review_dir, period, slot)
    assert out["status"] == "sent_verified"
    assert "--send" in calls[0] and "--reverify-only" not in calls[0]
    assert key in calls[0]
