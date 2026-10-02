"""Strict identity and native mention checks for Qingcheng process delivery."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "send_qingcheng_process.py"
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("qingcheng_public_pool_process_send", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_account_suffix_selects_exact_employee(monkeypatch):
    monkeypatch.setattr(MODULE, "_data", lambda _: {
        "queries": [{"query": "yangtingting29@gaotu.cn", "has_more": False}],
        "users": [
            {"matched_query": "yangtingting29@gaotu.cn", "localized_name": "杨婷婷", "enterprise_email": "yangtingting28@gaotu.cn", "open_id": "ou_wrong", "is_activated": True, "is_cross_tenant": False},
            {"matched_query": "yangtingting29@gaotu.cn", "localized_name": "杨婷婷", "enterprise_email": "yangtingting29@gaotu.cn", "open_id": "ou_right", "is_activated": True, "is_cross_tenant": False},
        ],
    })
    resolved, display = MODULE._resolve_people([{"name": "杨婷婷29", "account": "yangtingting29"}])
    assert resolved == {"杨婷婷29": "ou_right"}
    assert display == {"杨婷婷29": "杨婷婷"}


def test_incomplete_contact_search_blocks_delivery(monkeypatch):
    monkeypatch.setattr(MODULE, "_data", lambda _: {"queries": [{"query": "shiyuyan@gaotu.cn", "has_more": True}], "users": []})
    with pytest.raises(ValueError, match="incomplete"):
        MODULE._resolve_people([{"name": "师豫雁", "account": "shiyuyan"}])


def test_exact_email_account_uses_contacts_current_display_name(monkeypatch):
    monkeypatch.setattr(MODULE, "_data", lambda _: {
        "queries": [{"query": "zhangxiang12@gaotu.cn", "has_more": False}],
        "users": [{"matched_query": "zhangxiang12@gaotu.cn", "localized_name": "张翔",
                   "enterprise_email": "zhangxiang12@gaotu.cn", "open_id": "ou_exact",
                   "is_activated": True, "is_cross_tenant": False}],
    })
    resolved, display = MODULE._resolve_people([{"name": "张翔12", "account": "zhangxiang12"}])
    assert resolved == {"张翔12": "ou_exact"}
    assert display == {"张翔12": "张翔"}


def test_two_accounts_with_one_source_name_block_before_contact_lookup():
    with pytest.raises(ValueError, match="share one source display name"):
        MODULE._resolve_people([{"name": "同名", "account": "account01"},
                                {"name": "同名", "account": "account02"}])


def test_render_replaces_every_tied_name_with_native_at():
    markdown = "## 标题\n\n![顾问](consultant_process.png)\n\n- 8min较低的顾问：师豫雁、杨婷婷29"
    people = [{"name": "师豫雁", "account": "shiyuyan"}, {"name": "杨婷婷29", "account": "yangtingting29"}]
    resolved = {"师豫雁": "ou_a", "杨婷婷29": "ou_b"}
    display = {"师豫雁": "师豫雁", "杨婷婷29": "杨婷婷"}
    result = MODULE._render_message(markdown, "顾问", people, resolved, display, "img_test")
    assert '<at user_id="ou_a">师豫雁</at>、<at user_id="ou_b">杨婷婷</at>' in result
    assert "](img_test)" in result
    assert "杨婷婷29" not in result


def test_readback_requires_all_native_mentions(monkeypatch):
    monkeypatch.setattr(MODULE, "_data", lambda _: {"messages": [{
        "message_id": "om_test", "chat_id": "oc_test", "msg_type": "post",
        "content": "20260925期 ![图](img_test)", "sender": {"open_bot_id": "ou_bot"},
        "mentions": [{"id": "ou_a"}],
    }]})
    with pytest.raises(ValueError, match="native mentions"):
        MODULE._verify_message("oc_test", "om_test", "img_test", "20260925期", {"ou_a", "ou_b"}, "ou_bot")


def test_private_grade_lines_all_use_native_mentions():
    markdown = ("## 标题\n\n![顾问](consultant_process.png)\n\n"
                "- 高一年级8min较低的顾问：甲、乙\n- 高二年级8min较低的顾问：丙")
    by_grade = {"高一": [{"name": "甲"}, {"name": "乙"}], "高二": [{"name": "丙"}]}
    people = [person for group in by_grade.values() for person in group]
    result = MODULE._render_message(markdown, "顾问", people, {"甲": "ou_a", "乙": "ou_b", "丙": "ou_c"},
                                    {"甲": "甲", "乙": "乙", "丙": "丙"}, "img_test", by_grade)
    assert result.count("<at user_id=") == 3
    assert "- 高二年级8min较低的顾问：<at user_id=\"ou_c\">丙</at>" in result


def test_receipt_status_reads_both_shapes_this_sender_writes():
    # A failure receipt carries `status`; a success receipt is the raw send output with
    # no status at all, so `readback.verified` is the only confirmation signal.
    assert MODULE._receipt_status({"status": "send_attempt_started"}) == "send_attempt_started"
    assert MODULE._receipt_status({"status": "send_result_uncertain"}) == "send_result_uncertain"
    assert MODULE._receipt_status({"response": {"message_id": "om_x"}}) == "sent_unverified"
    assert MODULE._receipt_status({"response": {"message_id": "om_x"},
                                   "readback": {"verified": True}}) == "sent_verified"
    assert MODULE._receipt_status({"response": {"message_id": "om_x"},
                                   "readback": {"verified": False}}) == "sent_unverified"


def test_reverify_sends_nothing_and_updates_the_receipt(monkeypatch, tmp_path):
    # `--reverify-only` has no send capability: it must not reach upload or the send
    # outlet, and a message already in the group can therefore never be doubled.
    touched = []
    monkeypatch.setattr(MODULE, "upload_image", lambda *a, **k: touched.append("upload"))
    monkeypatch.setattr(MODULE, "_data", lambda *a, **k: touched.append("send"))
    monkeypatch.setattr(MODULE, "_verify_message",
                        lambda *a, **k: {"message_id": "om_prior", "verified": True})
    receipt_path = tmp_path / "supervisor_process_send_k.json"
    receipt = {"response": {"message_id": "om_prior"}, "image_key": "img_k",
               "chat_id": "oc_x", "period": "20261002期", "mention_ids": ["ou_a"]}
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    out = MODULE._reverify(json.loads(receipt_path.read_text(encoding="utf-8")),
                           receipt_path, "ou_bot")
    assert out["readback"]["verified"] is True
    assert touched == []
    assert json.loads(receipt_path.read_text(encoding="utf-8"))["readback"]["verified"] is True


def test_reverify_refuses_a_receipt_without_a_message_id(monkeypatch, tmp_path):
    monkeypatch.setattr(MODULE, "_verify_message", lambda *a, **k: {"verified": True})
    receipt_path = tmp_path / "supervisor_process_send_k.json"
    (receipt_path).write_text(json.dumps({"status": "send_result_uncertain"}), encoding="utf-8")
    with pytest.raises(ValueError, match="message id"):
        MODULE._reverify({"status": "send_result_uncertain"}, receipt_path, "ou_bot")
