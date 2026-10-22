"""The migrated channel uses SEC delivery without coupling existing reports."""
from datetime import datetime
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import fetch_qingcheng_process_source as source
import qingcheng_internal_books as legacy
import run_qingcheng_partner_process as partner
import run_qingcheng_sec_process as sec
import run_qingcheng_transformation as transformation

SLOT = datetime(2026, 10, 18, 12, 0, tzinfo=ZoneInfo("Asia/Shanghai"))


def test_internal_books_has_exactly_one_active_owner_and_no_conversion():
    cfg = sec._config()
    entry, scoped = sec.internal_books_definition(cfg)
    assert "internal_books" not in [e["id"] for e in partner._config()["channels"]]
    assert "internal_books" not in [e["id"] for e in transformation._batch()["channels"]]
    assert cfg["additional_reports"] == ["internal_books"]
    assert entry["chat_id"] == "oc_a8e793c81080ebf5b14dd22bd83a05a1"
    assert scoped["source"]["sources"]["internal_books"]["match"] == {"一级渠道": "图书", "渠道": "内部图书"}
    with pytest.raises(ValueError, match="moved to the SEC"):
        legacy.prepare("process", "20261016期", Path("unused"))


@pytest.mark.parametrize("base_failed,books_failed", [(True, False), (False, True)])
def test_internal_books_and_existing_sec_failures_are_independent(monkeypatch, tmp_path, base_failed, books_failed):
    def base(**kwargs):
        if base_failed:
            raise ValueError("existing SEC batch failed")
        return {"period": "20261016期", "slot": SLOT.isoformat(),
                "reports": {report: {"status": "sent_verified"} for report in sec.REPORT_IDS}}
    def books(*args):
        if books_failed:
            raise ValueError("internal-books source or mention preparation failed")
        return {"status": "sent_verified", "message_id": "om_books"}
    monkeypatch.setattr(sec, "_run_base", base)
    monkeypatch.setattr(sec, "_run_internal_books", books)
    result = sec.run(now=SLOT, output=tmp_path)
    assert result["reports"]["internal_books_consultant"]["status"] == ("blocked" if books_failed else "sent_verified")
    assert all(result["reports"][r]["status"] == ("blocked" if base_failed else "sent_verified") for r in sec.REPORT_IDS)


def raw(account, grade, leads, friends):
    return {"期次": "20261016期", "主管": "主管甲", "顾问": account, "顾问账号": account, "年级": grade,
            "退前线索": leads, "退后线索": 1, "好友标记": friends, "首call等待时长小时": 10,
            "8min标记": 0, "24h首call标记": 2, "沟通标记": 3, "总通时秒": 600, "外呼次数": 10}


def test_before_refund_denominator_sort_grade_ties_and_columns(monkeypatch, tmp_path):
    entry, cfg = sec.internal_books_definition(sec._config())
    rows = [raw("a", "高一", 5, 0), raw("b", "高一", 10, 0), raw("c", "高一", 5, 2),
            raw("small", "高一", 4, 4), raw("excluded", "初二", 10, 0), raw("d", "高二", 5, 1)]
    captured = {}
    def image(grouped, columns, *args, **kwargs):
        captured.update(rows=grouped, columns=columns, options=kwargs)
    monkeypatch.setattr(sec, "_table_image", image)
    review = sec._build_report(entry, rows, {"period": "20261016期", "snapshot": ["20261018", "08"], "rev": 42}, cfg, tmp_path)
    assert [r["顾问账号"] for r in captured["rows"]] == ["c", "a", "b", "d"]
    assert review["eligible_rows"] == 4
    assert {p["account"] for p in review["reminders"][0]["people"]} == {"a", "b"}
    assert review["reminders"][1]["grade"] == "高二"
    assert captured["rows"][0]["metrics"]["好友率"] == .4
    assert captured["rows"][0]["metrics"]["外呼时长"] == 2
    assert "退前线索" in captured["columns"] and "有效线索" not in captured["columns"]
    assert not {"8min", "总通时"}.intersection(captured["columns"])
    assert set(captured["options"]["bar_specs"]) == set(sec.SEC_BAR_FIELDS)
    assert len({spec[2] for spec in captured["options"]["bar_specs"].values()}) == 4
    assert "高一年级好友率较低的顾问" in review["message"]


def test_internal_books_fetch_and_probe_use_exact_secondary_channel(monkeypatch, tmp_path):
    calls = []
    def read(args, **kwargs):
        calls.append(args)
        path = Path(args[args.index("--output") + 1])
        row = {"record_id": "rec_one", "记录键": "key_one", "一级渠道": "图书", "渠道": "内部图书",
               "期次": "20261016期", "分区日期": "20261018", "分区小时": "08"}
        path.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")
        path.with_suffix(".manifest.json").write_text(json.dumps({"base_token": source.BASE_TOKEN,
            "table_id": source.TABLE_ID, "records_count": 1, "rev": 42, "has_more": False}), encoding="utf-8")
    monkeypatch.setattr(source, "run_lark", read)
    manifest = source.fetch("internal_books", "20261016期", tmp_path / "source.ndjson")
    assert manifest["records_count"] == 1
    assert source.probe_revision("internal_books", "20261016期", tmp_path / "probe.ndjson") == 42
    assert all(["渠道", "==", "内部图书"] in json.loads(args[args.index("--filter-json") + 1])["conditions"] for args in calls)


def test_new_channel_version_pin_is_separate_from_existing_sec(monkeypatch, tmp_path):
    cfg = sec._config()
    audit = {"raw_channel_counts": {"内部图书": 1}, "snapshot": ["20261018", "08"]}
    source_pin = {"period": "20261016期", "slot": SLOT.isoformat(), "rev": 99, "snapshot": audit["snapshot"]}
    (tmp_path / "source_version.json").write_text(json.dumps(source_pin), encoding="utf-8")
    monkeypatch.setattr(sec, "_source_rows", lambda *a: ([], {"period": "20261016期", "rev": 42, "snapshot": audit["snapshot"]}))
    monkeypatch.setattr(sec, "_build_report", lambda *a: None)
    assert sec._run_internal_books(cfg, "20261016期", SLOT, tmp_path, audit)["status"] == "skipped_no_eligible_rows"
    assert json.loads((tmp_path / "source_version.json").read_text(encoding="utf-8")) == source_pin
    assert json.loads((tmp_path / "internal_books_consultant/source_version.json").read_text(encoding="utf-8"))["rev"] == 42


def test_internal_books_missing_audit_is_not_assumed_empty(tmp_path):
    with pytest.raises(ValueError, match="no internal-books channel evidence"):
        sec._run_internal_books(sec._config(), "20261016期", SLOT, tmp_path, {"raw_channel_counts": {}})


@pytest.mark.parametrize("failure", ["request", "receipt"])
def test_one_existing_report_parse_error_does_not_block_siblings_or_books(monkeypatch, tmp_path, failure):
    validate = sec._validate_entry
    def checked(entry):
        if failure == "request" and entry["id"] == "sec_public_consultant":
            raise ValueError("one invalid request")
        return validate(entry)
    def receipt(path):
        if failure == "receipt" and path.parent.name == "sec_public_consultant":
            raise ValueError("one invalid receipt")
        return None
    monkeypatch.setattr(sec, "_validate_entry", checked)
    monkeypatch.setattr(sec, "_receipt_status", receipt)
    monkeypatch.setattr(sec, "_upstream_audit", lambda *a: {"snapshot": ["20261018", "08"], "raw_channel_counts": {
        "公域学霸": 1, "SEC未加好友": 1, "SEC首期掉海": 1, "SEC招生退费": 1, "内部图书": 1}})
    monkeypatch.setattr(sec, "_source_rows", lambda *a: ([], {"rev": 42, "period": "20261016期", "snapshot": ["20261018", "08"]}))
    monkeypatch.setattr(sec, "_build_report", lambda *a: {"period": "20261016期"})
    monkeypatch.setattr(sec, "_deliver", lambda *a: {"status": "sent_verified"})
    result = sec.run(now=SLOT, output=tmp_path)
    assert result["reports"]["sec_public_consultant"]["status"] == "blocked"
    assert all(value["status"] == "sent_verified" for key, value in result["reports"].items() if key != "sec_public_consultant")
