"""Production-shaped faults must stay within one Qingcheng message."""
from collections import Counter
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import fetch_qingcheng_process_source as source
import run_qingcheng_sec_process as sec
import run_qingcheng_special_process as special
import run_qingcheng_partner_process as partner
import run_qingcheng_process as process
import run_qingcheng_transformation as conversion

ZONE = ZoneInfo("Asia/Shanghai")
SLOT = datetime(2026, 10, 23, 16, 0, tzinfo=ZONE)
PERIOD = "20261023期"
SNAPSHOT = ["20261023", "13"]


def raw_row(index, channel, department="SEC"):
    return {"record_id": f"rec{index}", "记录键": f"key{index}", "期次": PERIOD,
            "一级渠道": "订单复用", "渠道": channel, "部门": department,
            "分区日期": SNAPSHOT[0], "分区小时": SNAPSHOT[1]}


def fake_base(monkeypatch, rows):
    filters = []
    def read(args, **kwargs):
        condition = json.loads(args[args.index("--filter-json") + 1])["conditions"]
        filters.append(condition)
        selected = [r for r in rows if all(r.get(key) == value for key, op, value in condition)]
        offset = int(args[args.index("--offset") + 1]) if "--offset" in args else 0
        limit = int(args[args.index("--limit") + 1])
        selected = selected[offset:offset + limit]
        path = Path(args[args.index("--output") + 1])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in selected), encoding="utf-8")
        path.with_suffix(".manifest.json").write_text(json.dumps({"base_token": source.BASE_TOKEN,
            "table_id": source.TABLE_ID, "records_count": len(selected), "has_more": False, "rev": 42}), encoding="utf-8")
    monkeypatch.setattr(source, "run_lark", read)
    return filters


def test_order_reuse_includes_every_secondary_and_department_but_supervisor_is_exact(monkeypatch, tmp_path):
    rows = [raw_row(1, "SEC未加好友"), raw_row(2, "SEC内部未加好友"), raw_row(3, "新增二级渠道", "一部")]
    filters = fake_base(monkeypatch, rows)
    manifest = source.fetch("sec_order_reuse", PERIOD, tmp_path / "all.ndjson")
    assert manifest["records_count"] == 3
    assert filters[0] == [["一级渠道", "==", "订单复用"], ["期次", "==", PERIOD]]
    source.fetch("sec_order_reuse", PERIOD, tmp_path / "supervisor.ndjson", secondary_channel="SEC未加好友")
    source.probe_revision("sec_order_reuse", PERIOD, tmp_path / "probe.ndjson", secondary_channel="SEC未加好友")
    assert all(["渠道", "==", "SEC未加好友"] in f for f in filters[1:])


def test_order_reuse_count_audit_covers_new_secondary_without_department_filter(monkeypatch, tmp_path):
    rows = [raw_row(1, "SEC未加好友"), raw_row(2, "SEC内部未加好友"), raw_row(3, "新增二级渠道", "一部")]
    fake_base(monkeypatch, rows)
    audit = {"raw_channel_counts": dict(Counter(r["渠道"] for r in rows)), "snapshot": SNAPSHOT}
    selected, manifest = sec._source_rows("sec_order_reuse", PERIOD, tmp_path, audit, sec._config(), SLOT)
    assert selected == rows and manifest["scope_audit"]["department"] is None
    assert manifest["scope_audit"]["raw_channel_counts"] == audit["raw_channel_counts"]
    audit["raw_channel_counts"]["SEC内部未加好友"] += 1
    with pytest.raises(ValueError, match="count"):
        sec._source_rows("sec_order_reuse", PERIOD, tmp_path, audit, sec._config(), SLOT)


@pytest.mark.parametrize("fault", ["source", "build", "delivery", "receipt", "pin"])
def test_sec_one_report_failure_does_not_block_any_sibling(monkeypatch, tmp_path, fault):
    cfg = sec._config()
    cfg["additional_reports"] = []
    monkeypatch.setattr(sec, "_config", lambda **kwargs: deepcopy(cfg))
    failed = "sec_no_friend_supervisor"
    monkeypatch.setattr(sec, "_upstream_audit", lambda *a: {"snapshot": SNAPSHOT,
        "raw_channel_counts": {"公域学霸": 1, "SEC未加好友": 1, "SEC首期掉海": 1, "SEC内部未加好友": 1}})
    def get_rows(key, period, folder, audit, scoped, slot):
        if fault == "source" and folder.name == failed:
            raise ValueError("one source failed")
        return [], {"period": period, "snapshot": SNAPSHOT, "rev": 42}
    def build(entry, *args):
        if fault == "build" and entry["id"] == failed:
            raise ValueError("one image failed")
        return {"period": PERIOD}
    delivered = []
    def send(entry, *args):
        delivered.append(entry["id"])
        if fault == "delivery" and entry["id"] == failed:
            raise ValueError("one send failed")
        return {"status": "sent_verified"}
    monkeypatch.setattr(sec, "_source_rows", get_rows)
    monkeypatch.setattr(sec, "_build_report", build)
    monkeypatch.setattr(sec, "_deliver", send)
    if fault in {"receipt", "pin"}:
        folder = tmp_path / failed
        folder.mkdir()
        (folder / ("send_receipt.json" if fault == "receipt" else "source_version.json")).write_text("{", encoding="utf-8")
    result = sec.run(now=SLOT, output=tmp_path)
    assert result["reports"][failed]["status"] == "blocked"
    assert all(v["status"] == "sent_verified" for key, v in result["reports"].items() if key != failed)
    assert set(delivered) >= set(sec.REPORT_IDS) - {failed}


def test_sec_versions_belong_to_each_message_and_verified_receipts_survive(monkeypatch, tmp_path):
    entry = sec._config()["reports"][0]
    other = sec._config()["reports"][1]
    sec._pin_report_source(entry, {"rev": 42, "snapshot": SNAPSHOT}, PERIOD, SLOT, tmp_path)
    sec._pin_report_source(other, {"rev": 43, "snapshot": SNAPSHOT}, PERIOD, SLOT, tmp_path)
    with pytest.raises(ValueError, match="version changed"):
        sec._pin_report_source(entry, {"rev": 43, "snapshot": SNAPSHOT}, PERIOD, SLOT, tmp_path)
    receipt = tmp_path / entry["id"] / "send_receipt.json"
    receipt.write_text(json.dumps({"status": "sent_verified", "message_id": "om_prior"}), encoding="utf-8")
    before = receipt.read_bytes()
    monkeypatch.setattr(sec, "_deliver", lambda *a: pytest.fail("settled receipt must not be resent"))
    assert sec._receipt_status(receipt)["message_id"] == "om_prior"
    assert receipt.read_bytes() == before


@pytest.mark.parametrize("fault", ["source", "build", "delivery", "receipt", "pin", "different_revision"])
def test_special_images_do_not_share_failure_state(monkeypatch, tmp_path, fault):
    cfg = special._config()
    failed = "special_books"
    monkeypatch.setattr(special, "_upstream_audit", lambda *a: {"snapshot": SNAPSHOT,
        "raw_channel_counts": {name: 1 for group in special.AUDIT_NAMES for name in group}})
    def get_rows(entry, period, folder, audit, slot):
        if fault == "source" and entry["id"] == failed:
            raise ValueError("one source failed")
        return [], {"period": period, "snapshot": SNAPSHOT,
                    "rev": 43 if fault == "different_revision" and entry["id"] == failed else 42}
    def build(entry, *args):
        if fault == "build" and entry["id"] == failed:
            raise ValueError("one image failed")
        return {"period": PERIOD}
    def send(entry, *args):
        if fault == "delivery" and entry["id"] == failed:
            raise ValueError("one delivery failed")
        return {"status": "sent_verified"}
    monkeypatch.setattr(special, "_source", get_rows)
    monkeypatch.setattr(special, "_build", build)
    monkeypatch.setattr(special, "_deliver", send)
    if fault in {"receipt", "pin"}:
        folder = tmp_path / failed
        folder.mkdir()
        (folder / ("send_receipt.json" if fault == "receipt" else "source_version.json")).write_text("{", encoding="utf-8")
    batch = special.run(now=datetime(2026, 10, 22, 13, 50, tzinfo=ZONE), output=tmp_path)
    for entry in cfg["channels"]:
        status = batch["channels"][entry["id"]]["status"]
        assert (status == "sent_verified") == (entry["id"] != failed or fault == "different_revision")


@pytest.mark.parametrize("fault", ["source", "build", "delivery", "receipt", "pin"])
def test_partner_messages_with_the_same_source_are_independent(monkeypatch, tmp_path, fault):
    cfg = partner._config()
    failed = "partner_local"
    monkeypatch.setattr(partner, "_upstream_audit", lambda *a: {"snapshot": SNAPSHOT,
        "raw_channel_counts": {name: 1 for entry in cfg["channels"] for name in entry["audit_secondary_channels"]}})
    def get_rows(key, match, period, folder, audit, slot, names):
        if fault == "source" and folder.parent.name == failed:
            raise ValueError("one source failed")
        return [{"渠道": names[0]}], {"period": period, "snapshot": SNAPSHOT, "rev": 42}
    def build(entry, *args):
        if fault == "build" and entry["id"] == failed:
            raise ValueError("one image failed")
        return {"period": PERIOD}
    def send(entry, *args):
        if fault == "delivery" and entry["id"] == failed:
            raise ValueError("one delivery failed")
        return {"status": "sent_verified"}
    monkeypatch.setattr(partner, "_source", get_rows)
    monkeypatch.setattr(partner, "_build", build)
    monkeypatch.setattr(partner, "_deliver", send)
    if fault in {"receipt", "pin"}:
        folder = tmp_path / failed
        folder.mkdir()
        (folder / ("send_receipt.json" if fault == "receipt" else "source_version.json")).write_text("{", encoding="utf-8")
    batch = partner.run(now=datetime(2026, 10, 22, 13, 50, tzinfo=ZONE), output=tmp_path)
    assert batch["channels"][failed]["status"] != "sent_verified"
    assert all(v["status"] == "sent_verified" for key, v in batch["channels"].items() if key != failed)


@pytest.mark.parametrize("fault", ["source", "build", "delivery", "receipt"])
def test_six_group_process_single_message_failure_continues(monkeypatch, tmp_path, fault):
    cfg = process._batch()
    monkeypatch.setattr(process, "_upstream_audit", lambda *a: {"snapshot": SNAPSHOT,
        "expected_counts": {e["id"]: 1 for e in cfg["channels"]}})
    def fetch(channel, period, path):
        if fault == "source" and (channel, path.parent.name) == ("private", "supervisor"):
            raise ValueError("one source failed")
        return {"rev": 42, "snapshot": SNAPSHOT, "records_count": 1}
    def build(src, sup, con, out, config, *, levels):
        level = levels[0]
        if fault == "build" and (out.parent.name, level) == ("private", "supervisor"):
            raise ValueError("one image failed")
        return {"period": PERIOD, "snapshot": "20261023 13:00", "results": {level: {}}}
    def send(channel, level, *args):
        if fault == "delivery" and (channel, level) == ("private", "supervisor"):
            raise ValueError("one send failed")
        return {"status": "sent_verified"}
    monkeypatch.setattr(process, "fetch", fetch)
    monkeypatch.setattr(process, "build", build)
    monkeypatch.setattr(process, "_fresh", lambda *a: None)
    monkeypatch.setattr(process, "_index", lambda *a: None)
    monkeypatch.setattr(process, "probe_revision", lambda *a: 42)
    monkeypatch.setattr(process, "_send_group", send)
    if fault == "receipt":
        monkeypatch.setattr(process, "_receipt_state", lambda path: (_ for _ in ()).throw(ValueError("bad receipt"))
            if (path.parent.parent.name, path.parent.name) == ("private", "supervisor") else (process.resend.RESEND, ""))
    result = process.run(confirm_send=True, now=datetime(2026, 10, 22, 13, 50, tzinfo=ZONE), output=tmp_path)
    assert result["channels"]["private"]["groups"]["supervisor"]["status"] != "sent_verified"
    assert all(value["status"] == "sent_verified" for ch, item in result["channels"].items()
               for level, value in item["groups"].items() if (ch, level) != ("private", "supervisor"))


@pytest.mark.parametrize("audience", ["standard", "dept"])
@pytest.mark.parametrize("fault", ["source", "build", "delivery"])
def test_both_transformation_tasks_continue_after_single_message_failure(monkeypatch, tmp_path, audience, fault):
    failed_channel = "public_pool"
    failed_level = "dept" if audience == "dept" else "supervisor"
    def fetch(channel, period, path, **kwargs):
        if fault == "source" and (channel, path.parent.name) == (failed_channel, failed_level):
            raise ValueError("one source failed")
        return {"rev": 42, "snapshot": SNAPSHOT}
    def export(channel, period, path, **kwargs):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n", encoding="utf-8")
        return {"rev": 43}
    def build(src, conv, out, config, *, channels, period, levels):
        channel, level = channels[0], levels[0]
        if fault == "build" and (channel, level) == (failed_channel, failed_level):
            raise ValueError("one image failed")
        return {"period": period, "conversion_snapshot": "20261023 13:00",
                "results": {channel: {"levels": {level: {}}}}}
    def send(channel, level, *args):
        if fault == "delivery" and (channel, level) == (failed_channel, failed_level):
            raise ValueError("one send failed")
        return {"status": "sent_verified"}
    monkeypatch.setattr(conversion, "fetch", fetch)
    monkeypatch.setattr(conversion, "export_conversion", export)
    monkeypatch.setattr(conversion, "build", build)
    monkeypatch.setattr(conversion, "_fresh", lambda *a: None)
    monkeypatch.setattr(conversion, "_index", lambda *a: None)
    monkeypatch.setattr(conversion, "probe_revision", lambda *a, **kwargs: 42)
    monkeypatch.setattr(conversion, "_probe_conversion_rev", lambda *a: 43)
    monkeypatch.setattr(conversion, "_send_group", send)
    now = datetime(2026, 10, 23, 13, 50 if audience == "dept" else 52, tzinfo=ZONE)
    result = conversion.run(confirm_send=True, now=now, output=tmp_path, audience=audience)
    failed = result["channels"][failed_channel]["groups"][failed_level]
    assert failed["status"] != "sent_verified"
    others = [v["status"] for ch, item in result["channels"].items() for lv, v in item["groups"].items()
              if (ch, lv) != (failed_channel, failed_level)]
    assert "sent_verified" in others
    assert all(s in {"sent_verified", "skipped_schedule_disabled"} for s in others)
