"""Shandong onboarding and Wuhan-book consultant retirement stay target-scoped."""
import json
from pathlib import Path
import sys

from PIL import Image
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import fetch_qingcheng_process_source as source
import run_qingcheng_partner_process as partner
import run_qingcheng_transformation as conversion
import preview_qingcheng_public_pool_process as picture
import send_qingcheng_transformation as sender

CHANNEL = "partner_shandong_live"
CHAT = "oc_44a0a613badf0d70cfd574d3aafc0917"
RETIRED = "oc_854e5427ec0f6ef2bf654fee0a759f83"


def raw(account, grade="初三", eight=1):
    return {"record_id": account + grade, "记录键": account + grade, "期次": "20261120期", "一级渠道": "付费",
        "渠道": "山东直播间", "主管": "主管甲", "顾问": account, "顾问账号": account, "年级": grade,
        "分区日期": "20261120", "分区小时": "11", "退后线索": 5, "好友标记": 2,
        "首call等待时长小时": 1, "8min标记": eight, "15min标记": 0, "24h首call标记": 2,
        "沟通标记": 3, "总通时秒": 120, "外呼次数": 4}


def entry_and_config():
    cfg = partner._config()
    return next(e for e in cfg["channels"] if e["id"] == CHANNEL), cfg


def test_only_new_group_is_registered_and_old_group_has_no_active_consultant_route():
    entry, cfg = entry_and_config()
    assert entry["target_chat_id"] == CHAT and entry["show_total"] is True
    assert cfg["source"]["matches"][CHANNEL] == {"一级渠道": "付费", "渠道": "山东直播间"}
    assert all(e["target_chat_id"] != RETIRED for e in cfg["channels"])
    assert conversion._config_chat_id(CHANNEL, "consultant") == CHAT
    assert conversion._channel_levels("partner_books", "standard") == ()
    assert conversion._channel_levels("partner_books", "dept") == ("dept",)
    assert conversion._config_chat_id("partner_books", "dept") == "oc_a95c83e488e0dfcc777d5ffad849d8a4"
    with pytest.raises(KeyError):
        conversion._config_chat_id("partner_books", "consultant")


def test_process_preview_has_totals_and_every_grade_minimum_tie_is_reminded(monkeypatch, tmp_path):
    entry, cfg = entry_and_config()
    captured = {}
    def image(rows, *args, **kwargs):
        captured.update(rows=rows, options=kwargs)
    monkeypatch.setattr(partner, "_table_image", image)
    rows = [raw("甲", "高一", 0), raw("乙", "高一", 0), raw("丙", "高一", 2), raw("丁", "初三", 1)]
    review = partner._build(entry, rows, {"period": "20261120期", "rev": 42, "snapshot": ["20261120", "11"]}, cfg, tmp_path)
    assert captured["options"]["show_total"] is True
    assert [r["顾问账号"] for r in captured["rows"][:3]] == ["丙", "乙", "甲"]
    assert {p["account"] for p in review["reminder_by_grade"]["高一"]} == {"甲", "乙"}
    assert {p["account"] for p in review["reminder_by_grade"]["初三"]} == {"丁"}
    body = partner._render(review, {"甲": "ou_a", "丁": "ou_d"}, {"甲": "甲", "丁": "丁"}, "img_verified")
    assert '<at user_id="ou_a">甲</at>' in body and '<at user_id="ou_d">丁</at>' in body
    assert "高一年级8min较低的顾问" in body and "初三年级8min较低的顾问" in body
    assert "乙" in body and "img_verified" in body


def test_renderer_total_switch_preserves_legacy_default(tmp_path):
    entry, cfg = entry_and_config()
    request = partner._request(entry)
    rows = picture._aggregate([raw("甲", "高一"), raw("乙", "初三")], "顾问", request, split_grade=True)
    columns = ["期次", "顾问", "年级", "有效线索", "8min"]
    normal, no_total = tmp_path / "normal.png", tmp_path / "no_total.png"
    picture._table_image(rows, columns, normal, "顾问", "20261120期", split_grade=True)
    picture._table_image(rows, columns, no_total, "顾问", "20261120期", split_grade=True, show_total=False)
    with Image.open(normal) as old, Image.open(no_total) as new:
        assert old.height - new.height == 2 * 56 and old.width == new.width


def test_shandong_native_source_and_probe_use_exact_primary_and_secondary(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setenv("CODEX_PUSH_COORDINATOR_ROOT", str(tmp_path / "cache"))
    def native(args, **kwargs):
        conditions = json.loads(args[args.index("--filter-json") + 1])["conditions"]
        calls.append(conditions)
        dest = Path(args[args.index("--output") + 1])
        dest.write_text(json.dumps(raw("甲"), ensure_ascii=False) + "\n", encoding="utf-8")
        dest.with_suffix(".manifest.json").write_text(json.dumps({"base_token": source.BASE_TOKEN, "table_id": source.TABLE_ID,
            "records_count": 1, "rev": 42, "has_more": False}), encoding="utf-8")
    monkeypatch.setattr(source, "run_lark", native)
    assert source.fetch(CHANNEL, "20261120期", tmp_path / "source.ndjson")["records_count"] == 1
    assert source.probe_revision(CHANNEL, "20261120期", tmp_path / "probe.ndjson") == 42
    assert all(["一级渠道", "==", "付费"] in c and ["渠道", "==", "山东直播间"] in c for c in calls)


def test_real_send_cli_accepts_new_channel_without_any_network_call(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["send_qingcheng_transformation.py", "--channel", CHANNEL, "--help"])
    with pytest.raises(SystemExit) as stopped:
        sender.main()
    assert stopped.value.code == 0 and CHANNEL in capsys.readouterr().out
