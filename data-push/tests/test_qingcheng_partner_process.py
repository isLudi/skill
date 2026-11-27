"""Local supervisor reports retain grade-only reminders after the rollback."""

import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import run_qingcheng_partner_process as PROCESS
import preview_qingcheng_partner_process as PARTNER
import preview_qingcheng_transformation as CONVERSION
import send_qingcheng_transformation as SEND


def _score(grade, supervisor, process=0, leads=1, net=0):
    return {"年级": grade, "主管": supervisor, "顾问": None, "顾问账号": None,
            "metrics": {"8min": process, "有效线索": leads, "净收款": net}}


def _process_review(monkeypatch, tmp_path, rows, channel="supervisor_local"):
    cfg = PROCESS._config()
    entry = next(c for c in cfg["channels"] if c["id"] == channel)
    monkeypatch.setattr(PROCESS, "_aggregate", lambda *args, **kwargs: rows)
    images = []
    monkeypatch.setattr(PROCESS, "_table_image", lambda *args, **kwargs: images.append((args, kwargs)))
    review = PROCESS._build(entry, [], {"period": "20261016期", "rev": 1, "snapshot": ["20261008", "18"]},
                            cfg, tmp_path)
    return review, images


def test_process_reminds_only_every_grade_tied_for_the_minimum(monkeypatch, tmp_path):
    rows = [_score("高一", "主管甲", .3), _score("高一", "主管乙", .2),
            _score("高二", "主管甲", 0), _score("高二", "主管乙", 0),
            _score("高三", "主管甲", .2), _score("高三", "主管丙", 0)]
    review, images = _process_review(monkeypatch, tmp_path, rows)
    assert review["reminder_grades"] == ["高二", "高三"]
    assert review["reminder_people"] == []
    assert "- 8min较低年级：高二、高三" in review["message"]
    assert all(row["主管"] not in review["message"] for row in rows)
    assert images[0][1]["split_grade"] is True


def test_process_uses_unrounded_grade_minima_and_never_mentions_people(monkeypatch, tmp_path):
    rows = [_score("高一", "主管甲", .12341), _score("高二", "主管乙", .12344)]
    review, _ = _process_review(monkeypatch, tmp_path, rows)
    assert review["reminder_grades"] == ["高一"]
    rendered = PROCESS._render(review, {"主管甲": "ou_a"}, {"主管甲": "主管甲"}, "img_preview")
    assert "<at " not in rendered
    assert "主管乙" not in rendered
    assert "](img_preview)" in rendered
    damaged = {**review, "message": review["message"].replace("较低年级：高一", "较低年级：高三")}
    with pytest.raises(ValueError, match="grade hint"):
        PROCESS._render(damaged, {"主管甲": "ou_a"}, {"主管甲": "主管甲"}, "img_preview")


def test_other_partner_channels_keep_their_whole_report_person_reminder(monkeypatch, tmp_path):
    rows = [{**_score("高一", "主管甲", .2), "顾问": "顾问甲", "顾问账号": "a"},
            {**_score("高二", "主管乙", .1), "顾问": "顾问乙", "顾问账号": "b"}]
    review, _ = _process_review(monkeypatch, tmp_path, rows, channel="partner_local")
    assert "- 8min较低的顾问：顾问乙" in review["message"]
    assert review["reminder_people"] == [{"name": "顾问乙", "account": "b"}]


def test_conversion_ranks_aggregated_grades_and_includes_all_tied_grades():
    rows = [_score("高一", "主管甲", leads=10, net=100),
            _score("高一", "主管乙", leads=90, net=0),
            _score("高二", "主管甲", leads=20, net=40),
            _score("高三", "主管丙", leads=10, net=20),
            _score("初三", "主管丁", leads=1, net=0)]
    assert CONVERSION._reminder_grades(rows) == ["高二", "高三"]
    assert CONVERSION._reminder_grades([_score("高一", "主管甲")]) == []


def test_conversion_sender_preserves_grade_text_without_native_mentions():
    item = {"level": "主管", "png": "conversion.png", "reminder_people": None,
            "reminder_by_grade": None, "reminder_grades": ["高二", "高三"]}
    message = "![转化数据](conversion.png)\n- 综合单效较高年级：高二、高三 🎉🎉🎉"
    rendered = SEND._render_message(message, item, {"主管甲": "ou_a"}, {"主管甲": "主管甲"}, "img_preview")
    assert "<at " not in rendered
    assert "综合单效较高年级：高二、高三" in rendered
    assert "主管甲" not in rendered


def test_local_supervisor_configs_agree_for_both_report_types():
    cfg = PROCESS._config()
    entry = next(c for c in cfg["channels"] if c["id"] == "supervisor_local")
    request = PROCESS._request(entry)
    conversion = json.loads(CONVERSION.DEFAULT_CONFIG.read_text(encoding="utf-8"))
    profile = next(c for c in conversion["channels"] if c["id"] == "partner_local")["profiles"]["supervisor"]
    preview = PARTNER._config(PARTNER.DEFAULT_CONFIG)
    preview_entry = next(c for c in preview["channels"] if c["id"] == "supervisor_local")
    assert entry["process_reminder"] == preview_entry["process_reminder"] == "8min_minimum_grade_text"
    assert profile["reminder_mode"] == "grade_text"
    assert request["reminder"]["target"] == "不提醒"
    assert request["reminder"]["process_rank"] == "不提醒"
    assert request["reminder"]["result_rank"] == "第1名"


def test_local_partner_group_names_match_batch_preview_and_requests():
    cfg = PROCESS._config()
    preview = PARTNER._config(PARTNER.DEFAULT_CONFIG)
    expected = {"partner_local": "🍊青橙本地化伙伴", "supervisor_local": "青橙-本地化项目"}
    for channel, name in expected.items():
        entry = next(item for item in cfg["channels"] if item["id"] == channel)
        preview_entry = next(item for item in preview["channels"] if item["id"] == channel)
        request = PROCESS._request(entry)
        assert entry["target_chat_name"] == preview_entry["target_chat_name"] == name
        assert request["business"]["target_chat_name"] == name
        assert entry["target_chat_id"] == preview_entry["target_chat_id"] == request["business"]["target_chat_id"]


@pytest.mark.parametrize("channel", ["partner_local", "supervisor_local"])
def test_partner_delivery_uses_fixed_id_after_group_rename(monkeypatch, tmp_path, channel):
    cfg = PROCESS._config()
    cfg["upstream_binding"] = {"test": True}
    entry = next(item for item in cfg["channels"] if item["id"] == channel)
    (tmp_path / "process.png").write_bytes(b"test image")
    review = {
        "period": "20261120期", "level": entry["level"], "image": "process.png",
        "message": "![过程数据](process.png)", "reminder_people": [],
    }
    calls = []
    monkeypatch.setattr(PROCESS, "probe_revision", lambda *args: 7)
    monkeypatch.setattr(PROCESS, "verify_chat", lambda *args: calls.append(args) or {
        "chat_id": entry["target_chat_id"], "name": "改名后的同一群", "name_changed": True,
    })
    monkeypatch.setattr(PROCESS, "upload_image", lambda *args: "img_test")
    monkeypatch.setattr(PROCESS, "run_lark", lambda *args, **kwargs: json.dumps({"ok": True}))
    monkeypatch.setattr(PROCESS, "require_process_binding_unchanged", lambda *args: None)
    monkeypatch.setattr(PROCESS, "require_delivery_window", lambda *args: None)
    monkeypatch.setattr(PROCESS, "_data", lambda *args, **kwargs: {"message_id": "om_test"})
    monkeypatch.setattr(PROCESS, "_verify_message", lambda *args: {"ok": True})

    result = PROCESS._deliver(entry, review, {"rev": 7}, cfg, tmp_path,
                              datetime(2026, 11, 19, 13, 50, tzinfo=ZoneInfo("Asia/Shanghai")))

    assert calls[0][0] == entry["target_chat_id"]
    assert result["status"] == "sent_verified"
    receipt = json.loads((tmp_path / "send_receipt.json").read_text(encoding="utf-8"))
    assert receipt["chat_id"] == entry["target_chat_id"]
    assert receipt["target_chat_name"] == "改名后的同一群"
    assert receipt["target_chat_name_changed"] is True


def test_partner_delivery_still_blocks_an_invalid_group_id(monkeypatch, tmp_path):
    cfg = PROCESS._config()
    entry = next(item for item in cfg["channels"] if item["id"] == "supervisor_local")
    review = {"period": "20261120期", "reminder_people": []}
    monkeypatch.setattr(PROCESS, "probe_revision", lambda *args: 7)
    def reject_chat(*args):
        raise ValueError("group identity mismatch")
    monkeypatch.setattr(PROCESS, "verify_chat", reject_chat)
    with pytest.raises(ValueError, match="group identity mismatch"):
        PROCESS._deliver(entry, review, {"rev": 7}, cfg, tmp_path,
                         datetime(2026, 11, 19, 13, 50, tzinfo=ZoneInfo("Asia/Shanghai")))
    assert not (tmp_path / "send_receipt.json").exists()
