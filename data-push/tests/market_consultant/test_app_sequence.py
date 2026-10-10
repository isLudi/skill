from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from lark_delivery.core import catalog
from lark_delivery.domains.market_consultant import adapter, app_sequence as sequence, scheduler

SLOT = datetime(2026, 10, 10, 13, tzinfo=timezone(timedelta(hours=8)))


def test_weekend_order_and_weekday_periods():
    specs = sequence.specs(SLOT)
    assert [item["label"] for item in specs] == [
        "APP主管本期转化", "APP顾问本期转化", "APP主管下期过程", "APP顾问下期过程"]
    assert [item["period"] for item in specs] == ["20261009期", "20261009期", "20261016期", "20261016期"]
    weekday = sequence.specs(SLOT + timedelta(days=2))
    assert [item["label"] for item in weekday] == ["APP主管本期过程", "APP顾问本期过程"]
    assert {item["period"] for item in weekday} == {"20261016期"}


def test_real_registered_owners_prepare_four_independent_messages(monkeypatch, tmp_path):
    calls = []
    def prepare(definition, target, **kwargs):
        calls.append((definition["channel_id"], kwargs["report_type"], kwargs["period"], kwargs["no_mentions"]))
        return {"coords": {"base_token": "same-base"}, "raw_table_id": definition["source"]["raw_table_id"],
                "snapshot": ("20261010", "15"), "raw_read_audit": {"rev": 22, "has_more": False},
                "markdown": "original title\n\nimage\nreminder", "period": kwargs["period"],
                "report_type": kwargs["report_type"], "channel": "app"}
    monkeypatch.setattr(adapter, "prepare", prepare)
    definition = catalog.load_channel(sequence.KEY)
    bundle = sequence.prepare(definition, definition["targets"][0], SLOT, tmp_path, no_mentions=True)
    assert [item[0] for item in calls] == ["supervisor_yafei_grade_9", "app_grade_9"] * 2
    assert [item[1] for item in calls] == ["result", "result", "process", "process"]
    assert all(item[3] is True for item in calls)
    assert len({item["context"]["report_kind"] for item in bundle["messages"]}) == 4
    assert all(item["label"] in item["context"]["markdown"].splitlines()[0] for item in bundle["messages"])


def bundle_for_delivery():
    return {"messages": [{**spec, "context": {
        "channel": "app", "period": spec["period"], "report_type": spec["section"],
        "report_kind": "app_" + spec["part"], "report_profile": "supervisor-detail",
        "coords": {"base_token": "same-base"}, "raw_table_id": "same-table",
        "snapshot": ("20261010", "15"), "raw_count": 1,
        "raw_read_audit": {"rev": 22, "has_more": False},
        "markdown": spec["label"], "image_path": None, "result_image_path": None,
    }} for spec in sequence.specs(SLOT)]}


def test_mixed_revision_or_partition_is_rejected_before_any_delivery():
    bundle = bundle_for_delivery()
    sequence.require_consistent_snapshot(bundle)
    bundle["messages"][2]["context"]["raw_read_audit"]["rev"] = 23
    with pytest.raises(ValueError, match="同一完整Base版本"):
        sequence.require_consistent_snapshot(bundle)
    bundle["messages"][2]["context"]["raw_read_audit"]["rev"] = 22
    bundle["messages"][3]["context"]["snapshot"] = ("20261010", "16")
    with pytest.raises(ValueError):
        sequence.require_consistent_snapshot(bundle)


def test_retry_preserves_order_and_deduplicates_real_durable_claims(monkeypatch, tmp_path):
    definition = catalog.load_channel(sequence.KEY)
    cfg = catalog.schedule_config(definition, definition["targets"][0])
    bundle = bundle_for_delivery()
    platform_messages, attempted = {}, []
    failed = False
    def send(chat_id, markdown, key, identity, **kwargs):
        nonlocal failed
        attempted.append(markdown)
        platform_messages.setdefault(key, {"message_id": f"msg-{len(platform_messages) + 1}"})
        if markdown == "APP顾问本期转化" and not failed:
            failed = True
            raise TimeoutError("receipt lost after platform write")
        return platform_messages[key]
    monkeypatch.setattr(scheduler.gp, "send_markdown", send)
    monkeypatch.setattr(scheduler, "assert_current_revision", lambda *args: None)
    monkeypatch.setattr(scheduler, "require_send_window", lambda *args: None)
    monkeypatch.setattr(scheduler, "receipt_readback", lambda *args: {"verified": True})
    monkeypatch.setattr(scheduler, "readback_available", lambda *args: True)
    monkeypatch.setattr(scheduler, "emit", lambda *args, **kwargs: None)
    db = scheduler.connect_ledger(tmp_path)
    try:
        assert sequence.deliver_in_order(bundle, lambda item: scheduler.deliver(item["context"], cfg, SLOT, db, {})) is False
        assert attempted == ["APP主管本期转化", "APP顾问本期转化"]
    finally:
        db.close()
    # A new process/connection sees the previous receipts and reuses every key.
    db = scheduler.connect_ledger(tmp_path)
    try:
        key_for = lambda item: scheduler.delivery_key(cfg, SLOT, "app", item["context"]["report_kind"])
        sequence.require_receipt_snapshot(bundle, db, key_for)
        assert sequence.deliver_in_order(bundle, lambda item: scheduler.deliver(item["context"], cfg, SLOT, db, {})) is True
        assert len(platform_messages) == 4
        assert attempted == ["APP主管本期转化", "APP顾问本期转化", "APP顾问本期转化", "APP主管下期过程", "APP顾问下期过程"]
        changed = deepcopy(bundle)
        changed["messages"][0]["context"]["raw_read_audit"]["rev"] = 23
        with pytest.raises(ValueError, match="Base版本或期次已变化"):
            sequence.require_receipt_snapshot(changed, db, key_for)
        rows = db.execute("SELECT status,detail FROM deliveries").fetchall()
        assert len(rows) == 4 and all(status == "sent_verified" for status, _ in rows)
        assert {json.loads(detail)["report_kind"] for _, detail in rows} == {"app_" + item for item in sequence.WEEKEND_ORDER}
    finally:
        db.close()


def test_legacy_app_delegates_only_after_coordinator_activation(monkeypatch):
    original = catalog.load_channel(sequence.KEY)
    cfg = {"channel_key": sequence.SUPERVISOR_KEY, "chat_id": original["targets"][0]["chat_id"]}
    channels = ["B站信息流-亚飞", "app"]
    assert sequence.delegated_channels(cfg, channels) == channels
    real_load = catalog.load_channel
    enabled = deepcopy(original)
    enabled["schedule"]["enabled"] = True
    enabled["delivery_sequence"]["stage"] = "scheduled"
    monkeypatch.setattr(catalog, "load_channel", lambda key: enabled if key == sequence.KEY else real_load(key))
    assert sequence.delegated_channels(cfg, channels) == ["B站信息流-亚飞"]
    assert sequence.delegated_channels({"channel_key": "market_consultant/supervisor_private_app_sync"}, channels) == channels
