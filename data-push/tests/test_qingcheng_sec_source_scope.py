"""SEC selection follows complete-channel validation, without sending messages."""

import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import run_qingcheng_sec_process as sec  # noqa: E402

PERIOD = "20261009期"
SNAPSHOT = ["20261009", "09"]
SLOT = datetime(2026, 10, 9, 12, 0, tzinfo=ZoneInfo("Asia/Shanghai"))


def _rows(departments, channel="公域学霸"):
    return [{"record_id": f"rec{index}", "记录键": f"key{index}",
             "期次": PERIOD, "一级渠道": "公域" if channel == "公域学霸" else "订单复用",
             "渠道": channel, "部门": department, "分区日期": SNAPSHOT[0], "分区小时": SNAPSHOT[1],
             "年级": "高一", "主管": "主管甲", "顾问": "顾问甲", "顾问账号": "advisor",
             "退前线索": 1, "退后线索": 1, "好友标记": 1, "首call等待时长小时": 2,
             "8min标记": 0, "24h首call标记": 1, "沟通标记": 1, "总通时秒": 90, "外呼次数": 2}
            for index, department in enumerate(departments)]


def _fetch_stub(monkeypatch, rows, **overrides):
    def fetch(source, period, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
        manifest = {"records_count": len(rows), "has_more": False, "period": PERIOD,
                    "snapshot": SNAPSHOT, "rev": 42, **overrides}
        path.with_suffix(".manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        return manifest
    monkeypatch.setattr(sec, "fetch", fetch)


def _audit(count, channel="公域学霸"):
    return {"raw_channel_counts": {channel: count}, "snapshot": SNAPSHOT}


def test_mixed_departments_are_verified_then_selected(monkeypatch, tmp_path):
    original = _rows(["SEC"] * 694 + ["一部"] * 27)
    _fetch_stub(monkeypatch, original)
    rows, manifest = sec._source_rows("sec_public", PERIOD, tmp_path, _audit(721), sec._config(), SLOT)
    assert len(rows) == 694 and {row["部门"] for row in rows} == {"SEC"}
    assert manifest["records_count"] == 721
    scope = manifest["scope_audit"]
    assert scope["selected_records_count"] == 694
    assert scope["excluded_records_count"] == 27
    assert scope["excluded_department_counts"] == {"一部": 27}
    assert scope["raw_channel_counts"] == {"公域学霸": 721}
    assert scope["selected_channel_counts"] == {"公域学霸": 694}
    assert json.loads((tmp_path / "sec_public/scope_audit.json").read_text(encoding="utf-8")) == scope
    assert len((tmp_path / "sec_public/source.ndjson").read_text(encoding="utf-8").splitlines()) == 721


def test_audit_must_match_unfiltered_rows_not_selected_rows(monkeypatch, tmp_path):
    _fetch_stub(monkeypatch, _rows(["SEC"] * 3 + ["一部"]))
    with pytest.raises(ValueError, match="source count"):
        sec._source_rows("sec_public", PERIOD, tmp_path, _audit(3), sec._config(), SLOT)
    assert not (tmp_path / "sec_public/scope_audit.json").exists()


@pytest.mark.parametrize("fault", ["missing_page", "duplicate_key", "mixed_snapshot", "wrong_channel",
                                   "wrong_period", "missing_department", "upstream_snapshot"])
def test_outside_department_rows_still_pass_integrity_checks_first(monkeypatch, tmp_path, fault):
    rows = _rows(["SEC", "一部"])
    overrides = {}
    audit = _audit(2)
    if fault == "missing_page":
        overrides["has_more"] = True
    elif fault == "duplicate_key":
        rows[1]["记录键"] = rows[0]["记录键"]
    elif fault == "mixed_snapshot":
        rows[1]["分区小时"] = "07"
    elif fault == "wrong_channel":
        rows[1]["渠道"] = "公域自然流"
    elif fault == "wrong_period":
        rows[1]["期次"] = "20261002期"
    elif fault == "missing_department":
        rows[1].pop("部门")
    else:
        audit["snapshot"] = ["20261009", "07"]
    _fetch_stub(monkeypatch, rows, **overrides)
    with pytest.raises(ValueError):
        sec._source_rows("sec_public", PERIOD, tmp_path, audit, sec._config(), SLOT)


def test_order_reuse_checks_all_channel_counts_before_department_selection(monkeypatch, tmp_path):
    rows = _rows(["SEC", "一部"], "SEC未加好友")
    rows += [{**row, "record_id": "other", "记录键": "other"}
             for row in _rows(["SEC"], "SEC首期掉海")]
    _fetch_stub(monkeypatch, rows)
    audit = {"snapshot": SNAPSHOT, "raw_channel_counts": {"SEC未加好友": 2, "SEC首期掉海": 1}}
    selected, manifest = sec._source_rows("sec_order_reuse", PERIOD, tmp_path, audit, sec._config(), SLOT)
    assert len(selected) == 2
    assert manifest["scope_audit"]["selected_channel_counts"] == {"SEC未加好友": 1, "SEC首期掉海": 1}
    audit["raw_channel_counts"] = {"SEC未加好友": 1, "SEC首期掉海": 2}
    with pytest.raises(ValueError, match="raw source count"):
        sec._source_rows("sec_order_reuse", PERIOD, tmp_path, audit, sec._config(), SLOT)


def test_both_public_reports_receive_only_sec_rows_and_record_exclusions(monkeypatch, tmp_path):
    _fetch_stub(monkeypatch, _rows(["SEC"] * 6 + ["一部"]))
    monkeypatch.setattr(sec, "_upstream_audit", lambda *_: _audit(7))
    built = []
    delivered = []

    def build(entry, rows, manifest, cfg, output):
        assert len(rows) == 6 and all(row["部门"] == "SEC" for row in rows)
        built.append(entry["id"])
        return {"report_id": entry["id"]}

    def deliver(entry, *_):
        delivered.append(entry["id"])
        return {"status": "sent_verified", "message_id": "offline_fixture"}

    monkeypatch.setattr(sec, "_build_report", build)
    monkeypatch.setattr(sec, "_deliver", deliver)
    batch = sec.run(now=SLOT, output=tmp_path)
    assert built == delivered == ["sec_public_consultant", "sec_public_supervisor"]
    assert batch["source_scope_audits"]["sec_public"]["excluded_records_count"] == 1


def test_zero_sec_rows_skip_without_building_empty_message(monkeypatch, tmp_path):
    _fetch_stub(monkeypatch, _rows(["一部", "二部"]))
    monkeypatch.setattr(sec, "_upstream_audit", lambda *_: _audit(2))

    def forbidden(*_, **__):
        raise AssertionError("An empty SEC slice must not render or send")

    monkeypatch.setattr(sec, "_table_image", forbidden)
    monkeypatch.setattr(sec, "_deliver", forbidden)
    batch = sec.run(now=SLOT, output=tmp_path)
    for report_id in ("sec_public_consultant", "sec_public_supervisor"):
        assert batch["reports"][report_id]["status"] == "skipped_no_eligible_rows"
    assert batch["source_scope_audits"]["sec_public"]["selected_records_count"] == 0
