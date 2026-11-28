"""Tests for Qingcheng intermediate page cleanup and 7-day rolling slot retention."""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import sys
from unittest.mock import patch
from zoneinfo import ZoneInfo

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import export_conversion_refresh as conv_mod
import fetch_qingcheng_process_source as fetch_mod


def test_fetch_removes_intermediate_page_files_after_merge(tmp_path: Path) -> None:
    out = tmp_path / "source.ndjson"
    pages = [
        [
            {
                "record_id": "rec_1",
                "记录键": "k1",
                "一级渠道": "抖音私信",
                "渠道": "抖音私信",
                "期次": "20261127期",
                "分区日期": "20261128",
                "分区小时": "12",
            }
        ],
        [
            {
                "record_id": "rec_2",
                "记录键": "k2",
                "一级渠道": "抖音私信",
                "渠道": "抖音私信",
                "期次": "20261127期",
                "分区日期": "20261128",
                "分区小时": "12",
            }
        ],
    ]
    call_idx = {"n": 0}

    def fake_run_lark(args, cwd, timeout):
        idx = call_idx["n"]
        call_idx["n"] += 1
        out_idx = args.index("--output") + 1
        page_file = Path(args[out_idx])
        rows = pages[idx]
        page_file.write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
            encoding="utf-8",
        )
        manifest = {
            "base_token": fetch_mod.BASE_TOKEN,
            "table_id": fetch_mod.TABLE_ID,
            "rev": 42,
            "records_count": len(rows),
            "has_more": idx == 0,
        }
        page_file.with_suffix(".manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False), encoding="utf-8"
        )
        return "{}"

    with patch.object(fetch_mod, "run_lark", side_effect=fake_run_lark):
        combined = fetch_mod.fetch("douyin_dm", "20261127期", out)

    assert combined["records_count"] == 2
    assert combined["page_count"] == 2
    assert out.exists()
    assert out.with_suffix(".manifest.json").exists()
    assert len(out.read_text(encoding="utf-8").splitlines()) == 2
    assert not (tmp_path / "source.page1.ndjson").exists()
    assert not (tmp_path / "source.page2.ndjson").exists()
    assert not (tmp_path / "source.page1.manifest.json").exists()
    assert not (tmp_path / "source.page2.manifest.json").exists()


def test_export_conversion_removes_intermediate_page_files_after_merge(tmp_path: Path) -> None:
    out = tmp_path / "source_conversion.ndjson"
    cache_dir = tmp_path / "pages"
    pages = [
        [{"record_id": "c1", "渠道": "抖音私信", "期次": "20261127期"}],
        [{"record_id": "c2", "渠道": "抖音私信", "期次": "20261127期"}],
    ]
    call_idx = {"n": 0}

    def fake_run_lark(args, cwd, timeout):
        idx = call_idx["n"]
        call_idx["n"] += 1
        out_idx = args.index("--output") + 1
        page_file = Path(args[out_idx])
        rows = pages[idx]
        page_file.write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
            encoding="utf-8",
        )
        manifest = {
            "base_token": conv_mod.BASE_TOKEN,
            "table_id": conv_mod.TABLE_ID,
            "rev": 77,
            "records_count": len(rows),
            "has_more": idx == 0,
        }
        page_file.with_suffix(".manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False), encoding="utf-8"
        )
        return "{}"

    with patch.object(conv_mod, "run_lark", side_effect=fake_run_lark):
        manifest = conv_mod.export_conversion("douyin_dm", "20261127期", out, cache_dir=cache_dir)

    assert manifest["records_count"] == 2
    assert out.exists()
    assert out.with_suffix(".manifest.json").exists()
    assert not (cache_dir / "douyin_dm.page1.ndjson").exists()
    assert not (cache_dir / "douyin_dm.page2.ndjson").exists()
    assert not (cache_dir / "douyin_dm.page1.manifest.json").exists()
    assert not (cache_dir / "douyin_dm.page2.manifest.json").exists()


def test_prune_old_slot_dirs_keeps_7_days_and_protects_current_and_non_slots(tmp_path: Path) -> None:
    slots = tmp_path / "slots"
    slots.mkdir()
    old_slot = slots / "20261120-1352"
    old_slot.mkdir()
    (old_slot / "source.ndjson").write_text("{}\n", encoding="utf-8")

    boundary_slot = slots / "20261121-1400"
    boundary_slot.mkdir()

    recent_slot = slots / "20261128-1352"
    recent_slot.mkdir()

    protected_old = slots / "20261110-1352"
    protected_old.mkdir()

    non_slot_dir = slots / "previews"
    non_slot_dir.mkdir()
    lock_file = slots / "scheduled.lock"
    lock_file.write_text("", encoding="utf-8")

    now = datetime(2026, 11, 28, 14, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
    removed = fetch_mod.prune_old_slot_dirs(
        slots, keep_days=7, current_slot_dir=protected_old, now=now
    )

    assert removed == ["20261120-1352"]
    assert not old_slot.exists()
    assert boundary_slot.exists()
    assert recent_slot.exists()
    assert protected_old.exists()
    assert non_slot_dir.exists()
    assert lock_file.exists()
