"""The SEC pool consultant excludes only the two ordinary-pool secondaries."""
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

EXCLUDED = ("顾问未加好友", "0元信息流")
RETAINED = ("SEC未加好友", "SEC首期掉海", "SEC招生退费", "SEC内部复用")
PERIOD = "20261120期"
SNAPSHOT = ["20261117", "09"]
SLOT = datetime(2026, 11, 17, 12, 0, tzinfo=ZoneInfo("Asia/Shanghai"))


def rows():
    return [{"record_id": f"rec{i}", "记录键": f"key{i}", "期次": PERIOD, "一级渠道": "公海",
             "渠道": channel, "部门": "SEC", "分区日期": SNAPSHOT[0], "分区小时": SNAPSHOT[1],
             "主管": "主管甲", "顾问": f"顾问{i}", "顾问账号": f"advisor{i}", "年级": "高一",
             "退前线索": 100 if channel in EXCLUDED else 5, "退后线索": 1, "好友标记": 1,
             "首call等待时长小时": 2, "8min标记": 0, "24h首call标记": 1, "沟通标记": 1,
             "总通时秒": 120, "外呼次数": 1}
            for i, channel in enumerate((*EXCLUDED, *RETAINED))]


def fake_base(monkeypatch, items, *, ignore_exclusions=False):
    filters = []
    def run(args, **kwargs):
        conditions = json.loads(args[args.index("--filter-json") + 1])["conditions"]
        filters.append(conditions)
        def match(row):
            for key, op, value in conditions:
                if op == "==" and row[key] != value:
                    return False
                if op == "!=" and row[key] == value and not ignore_exclusions:
                    return False
            return True
        selected = [r for r in items if match(r)]
        offset = int(args[args.index("--offset") + 1]) if "--offset" in args else 0
        limit = int(args[args.index("--limit") + 1])
        page = selected[offset:offset + limit]
        path = Path(args[args.index("--output") + 1])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in page), encoding="utf-8")
        path.with_suffix(".manifest.json").write_text(json.dumps({"base_token": source.BASE_TOKEN,
            "table_id": source.TABLE_ID, "rev": 42, "records_count": len(page),
            "has_more": offset + limit < len(selected)}), encoding="utf-8")
    monkeypatch.setattr(source, "run_lark", run)
    return filters


def target():
    cfg = sec._config()
    entry = next(e for e in cfg["reports"] if e["id"] == "sec_order_reuse_consultant")
    return entry, cfg, sec._report_config(entry, cfg)


def test_fetch_and_probe_share_exact_exclusions_and_complete_pagination(monkeypatch, tmp_path):
    calls = fake_base(monkeypatch, rows())
    monkeypatch.setattr(source, "PAGE_SIZE", 2)
    path = tmp_path / "source.ndjson"
    manifest = source.fetch("sec_order_reuse", PERIOD, path, excluded_secondary_channels=EXCLUDED)
    selected = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert {r["渠道"] for r in selected} == set(RETAINED)
    assert manifest["records_count"] == 4 and manifest["page_count"] == 2 and manifest["has_more"] is False
    assert manifest["excluded_secondary_channels"] == list(EXCLUDED)
    assert source.probe_revision("sec_order_reuse", PERIOD, tmp_path / "probe.ndjson", excluded_secondary_channels=EXCLUDED) == 42
    assert all(["渠道", "!=", name] in condition for condition in calls for name in EXCLUDED)


def test_server_returning_excluded_records_is_rejected(monkeypatch, tmp_path):
    fake_base(monkeypatch, rows(), ignore_exclusions=True)
    with pytest.raises(ValueError, match="excluded secondary"):
        source.fetch("sec_order_reuse", PERIOD, tmp_path / "source.ndjson", excluded_secondary_channels=EXCLUDED)


def test_exclusions_are_owned_only_by_this_message():
    entry, cfg, scoped = target()
    original = deepcopy(cfg)
    assert scoped["source"]["sources"]["sec_order_reuse"]["excluded_secondary_channels"] == list(EXCLUDED)
    assert "excluded_secondary_channels" not in cfg["source"]["sources"]["sec_order_reuse"]
    for sibling in cfg["reports"]:
        if sibling["id"] != entry["id"]:
            other = sec._report_config(sibling, cfg)
            assert not other["source"]["sources"][sibling["source"]].get("excluded_secondary_channels")
    assert cfg == original


def test_filtered_counts_are_verified_against_primary_secondary_audit(monkeypatch, tmp_path):
    all_rows = rows()
    fake_base(monkeypatch, all_rows)
    entry, cfg, scoped = target()
    counts = dict(Counter(r["渠道"] for r in all_rows))
    audit = {"snapshot": SNAPSHOT, "base_revision": 42, "raw_channel_counts": counts,
             "primary_secondary_counts": {"公海": counts}}
    selected, manifest = sec._source_rows("sec_order_reuse", PERIOD, tmp_path, audit, scoped)
    assert {r["渠道"] for r in selected} == set(RETAINED)
    assert manifest["scope_audit"]["excluded_secondary_channels"] == list(EXCLUDED)
    audit["primary_secondary_counts"]["公海"]["SEC内部复用"] += 1
    with pytest.raises(ValueError, match="verified primary/secondary scope"):
        sec._source_rows("sec_order_reuse", PERIOD, tmp_path, audit, scoped)


def test_excluded_leads_cannot_enter_image_totals_or_reminders(monkeypatch, tmp_path):
    entry, cfg, scoped = target()
    rendered = []
    monkeypatch.setattr(sec, "_table_image", lambda grouped, *a, **k: rendered.extend(grouped))
    review = sec._build_report(entry, rows(), {"period": PERIOD, "snapshot": SNAPSHOT, "rev": 42}, scoped, tmp_path)
    assert review["raw_rows"] == 4 and review["eligible_rows"] == 4
    assert sum(r["metrics"]["有效线索"] for r in rendered) == 20
    assert {r["顾问账号"] for r in rendered} == {f"advisor{i}" for i in range(2, 6)}
    assert all(p["account"] not in {"advisor0", "advisor1"} for group in review["reminders"] for p in group["people"])


@pytest.mark.parametrize("has_pool_rows", [True, False])
def test_all_excluded_rows_skip_only_this_report(monkeypatch, tmp_path, has_pool_rows):
    entry, cfg, scoped = target()
    cfg["additional_reports"] = []
    monkeypatch.setattr(sec, "_config", lambda **kwargs: deepcopy(cfg))
    counts = {"顾问未加好友": 3, "0元信息流": 5} if has_pool_rows else {}
    audit = {"snapshot": SNAPSHOT, "base_revision": 42, "raw_channel_counts": {**counts, "公域学霸": 1},
             "primary_secondary_counts": {"公海": counts, "公域": {"公域学霸": 1}}}
    monkeypatch.setattr(sec, "_latest_verified_snapshot", lambda *a: audit)
    touched = []
    def read(key, period, folder, *args):
        touched.append(folder.name)
        assert key == "sec_public"
        return [], {"period": period, "snapshot": SNAPSHOT, "rev": 42}
    monkeypatch.setattr(sec, "_source_rows", read)
    monkeypatch.setattr(sec, "_build_report", lambda *a: {"period": PERIOD})
    monkeypatch.setattr(sec, "_deliver", lambda *a: {"status": "sent_verified"})
    batch = sec.run(now=SLOT, output=tmp_path)
    assert batch["reports"][entry["id"]]["status"] == "skipped_no_source_rows"
    assert entry["id"] not in touched
    assert batch["reports"]["sec_public_consultant"]["status"] == "sent_verified"
    assert batch["reports"]["sec_public_supervisor"]["status"] == "sent_verified"


def test_ordinary_public_pool_still_contains_both_ordinary_secondaries(monkeypatch, tmp_path):
    fake_base(monkeypatch, rows())
    path = tmp_path / "ordinary.ndjson"
    source.fetch("public_pool", PERIOD, path)
    selected = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert {r["渠道"] for r in selected} == set(EXCLUDED)


def test_delivery_revision_probe_uses_the_same_report_exclusions(monkeypatch, tmp_path):
    entry, cfg, scoped = target()
    captured = []
    def probe(*args, **kwargs):
        captured.append(kwargs)
        return 43
    monkeypatch.setattr(sec, "probe_revision", probe)
    with pytest.raises(ValueError, match="revision changed before delivery"):
        sec._deliver(entry, {"period": PERIOD}, {"rev": 42}, scoped, tmp_path, SLOT)
    assert captured == [{"excluded_secondary_channels": EXCLUDED}]
