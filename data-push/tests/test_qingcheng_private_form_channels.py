"""Private form channels retain pagination, revision and report scope checks."""
import json
from pathlib import Path
import sys

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import fetch_qingcheng_process_source as source
import export_conversion_refresh as conversion
import run_qingcheng_process as process
import run_qingcheng_special_process as special
from preview_qingcheng_public_pool_process import _aggregate, _read_snapshot

PERIOD = "20261023期"


def row(index, channel):
    return {"record_id": f"rec{index}", "记录键": f"key{index}", "一级渠道": "私域",
            "渠道": channel, "期次": PERIOD, "分区日期": "20261017", "分区小时": "08",
            "年级": "高一", "主管": "主管甲", "顾问": "顾问甲", "顾问账号": "advisor",
            "退后线索": 3, "好友标记": 1, "首call等待时长小时": 2, "8min标记": 1,
            "24h首call标记": 1, "沟通标记": 1, "总通时秒": 120, "外呼次数": 2}


def fake_pages(monkeypatch, pages, revisions=(42, 42)):
    offsets = []

    def run(args, **kwargs):
        page = len(offsets)
        offsets.append(int(args[args.index("--offset") + 1]))
        destination = Path(args[args.index("--output") + 1])
        items = pages[page]
        destination.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in items), encoding="utf-8")
        destination.with_suffix(".manifest.json").write_text(json.dumps({
            "base_token": source.BASE_TOKEN, "table_id": source.TABLE_ID,
            "records_count": len(items), "rev": revisions[page], "has_more": page + 1 < len(pages)}), encoding="utf-8")
        return "{}"

    monkeypatch.setattr(source, "run_lark", run)
    return offsets


def test_new_forms_contribute_to_private_reports_after_complete_export(monkeypatch, tmp_path):
    pages = [[row(1, "私域表单"), row(2, "私域图书"), row(3, "表单浙江")],
             [row(4, "私域品效"), row(5, "表单江苏")]]
    offsets = fake_pages(monkeypatch, pages)
    path = tmp_path / "private.ndjson"
    manifest = source.fetch("private", PERIOD, path)
    assert offsets == [0, 3]  # The excluded row still counts in server pagination.
    assert manifest["export_records_count"] == 5 and manifest["records_count"] == 4
    assert manifest["excluded_secondary_channel_counts"] == {"私域图书": 1}
    rows, _ = _read_snapshot(path, {"source": {"match": {"一级渠道": "私域"}}})
    request = {"business": {"grades": ["高一"]}, "report": {"minimum": {"value": 3}}}
    for level in ("主管", "顾问"):
        report = _aggregate(rows, level, request, split_grade=True)
        assert report[0]["metrics"]["有效线索"] == 12
        assert report[0]["metrics"]["好友率"] == 1 / 3
    assert process.AUDIT_CHANNELS["private"] == source.PRIVATE_CHANNELS
    entry = special._config()["channels"][0]
    assert special._expected(entry, {"raw_channel_counts": {r["渠道"]: 1 for p in pages for r in p}}) == 4
    assert {condition[2] for condition in conversion.FILTERS["private"]["conditions"]} == set(source.PRIVATE_CHANNELS)


def test_revision_drift_still_blocks_even_when_drifted_page_is_excluded(monkeypatch, tmp_path):
    fake_pages(monkeypatch, [[row(1, "表单浙江")], [row(2, "私域图书")]], (42, 43))
    with pytest.raises(ValueError, match="revision changed"):
        source.fetch("private", PERIOD, tmp_path / "private.ndjson")


def test_missing_secondary_channel_is_not_silently_filtered(monkeypatch, tmp_path):
    fake_pages(monkeypatch, [[row(1, "表单江苏"), row(2, "")]])
    with pytest.raises(ValueError, match="secondary channel is missing"):
        source.fetch("private", PERIOD, tmp_path / "private.ndjson")


def test_operator_read_sets_its_own_utf8_environment(monkeypatch):
    monkeypatch.delenv("PYTHONIOENCODING", raising=False)
    monkeypatch.delenv("PYTHONUTF8", raising=False)

    def run(args, **kwargs):
        assert kwargs["env"]["PYTHONIOENCODING"] == "utf-8"
        assert kwargs["env"]["PYTHONUTF8"] == "1"
        assert kwargs["encoding"] == "utf-8" and "errors" not in kwargs
        return type("Result", (), {"returncode": 0, "stdout": json.dumps({
            "ok": True, "read_only": True, "remote_mutations": 0, "label": "表单江苏"}), "stderr": ""})()

    monkeypatch.setattr(process.subprocess, "run", run)
    assert process._operator_read("list-execution-history")["label"] == "表单江苏"
