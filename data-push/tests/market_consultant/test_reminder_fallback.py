"""Offline checks for the final, no-send reminder membership review."""

from datetime import datetime

from lark_delivery.domains.market_consultant.reminder_fallback import review_before_send, validate_coverage


def test_review_before_send_downgrades_departed_member_and_revalidates():
    context = {
        "channel": "app",
        "markdown": '<at user_id="ou_manager">负责人A</at>',
        "grade_report": {"reminder_names": ["负责人A"]},
        "mention_info": {"names": ["负责人A"], "resolved": {"负责人A": "ou_manager"},
                         "display_names": {"负责人A": "负责人A"}},
    }
    cfg = {"chat_id": "oc_test"}
    slot = datetime(2026, 10, 12, 12)
    validated, emitted = [], []

    def validate(current, evidence, config, current_slot):
        assert evidence == {} and config is cfg and current_slot is slot
        validate_coverage(current["grade_report"]["reminder_names"], current["mention_info"], current["markdown"])
        validated.append(current["markdown"])

    def lookup(chat_id, resolved, identity, timeout):
        assert (chat_id, resolved, identity, timeout) == ("oc_test", {"负责人A": "ou_manager"}, "bot", 60)
        return ["负责人A"]

    review_before_send(context, {}, cfg, slot, validate, lookup,
                       lambda event, **fields: emitted.append((event, fields)))

    assert validated == ['<at user_id="ou_manager">负责人A</at>', "负责人A"]
    assert context["mention_info"]["resolved"] == {}
    assert context["mention_info"]["text_fallback_names"] == ["负责人A"]
    assert emitted[0][0] == "reminder_text_fallback"
    assert emitted[0][1]["names"] == ["负责人A"]
