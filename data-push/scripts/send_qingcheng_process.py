"""Send one reviewed Qingcheng process group report with verified native mentions."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

from lark_delivery.common import resend
from lark_delivery.common.im import upload_image, verify_sender_membership
from lark_delivery.common.reminders import resolve_contacts, refresh_membership
from lark_delivery.common.runtime import run_lark


DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "config" / "departments" / "qingcheng" / "public_pool_process_preview.json"


def _data(args: list[str]) -> dict:
    payload = json.loads(run_lark(args))
    if payload.get("ok") is not True or not isinstance(payload.get("data"), dict):
        raise RuntimeError(f"Feishu read or write did not succeed: {payload.get('error')}")
    return payload["data"]


def _resolve_people(people: list[dict]) -> tuple[dict[str, str], dict[str, str]]:
    """Keep every selected name; only uniquely verified contacts get native @."""
    resolved, display, _ = resolve_contacts(people, _data)
    return resolved, display


def _render_message(markdown: str, level: str, people: list[dict], resolved: dict[str, str], display: dict[str, str], image_key: str, reminder_by_grade: dict | None = None) -> str:
    reminder_lines = []
    if reminder_by_grade:
        for grade, group in reminder_by_grade.items():
            names = [person["name"] for person in group]
            reminder_lines.append((f"- {grade}年级8min较低的{level}：{'、'.join(names)}", names))
    else:
        names = [person["name"] for person in people]
        reminder_lines.append((f"- 8min较低的{level}：{'、'.join(names)}", names))
    for original, names in reminder_lines:
        # Names absent from `resolved` are the sanctioned plain-name fallback:
        # identity or group membership could not be verified.
        mentions = "、".join(
            f'<at user_id="{resolved[name]}">{html.escape(display[name])}</at>' if name in resolved
            else html.escape(name) for name in names)
        if markdown.count(original) != 1:
            raise ValueError("Reviewed reminder line differs from resolved people")
        markdown = markdown.replace(original, original.split("：", 1)[0] + "：" + mentions)
    slug = "supervisor" if level == "主管" else "consultant"
    image_ref = f"]({slug}_process.png)"
    if markdown.count(image_ref) != 1 or not image_key.startswith("img_"):
        raise ValueError("Reviewed message has no single uploaded image reference")
    rendered = markdown.replace(image_ref, f"]({image_key})")
    actual_ids = set(re.findall(r'<at user_id="(ou_[A-Za-z0-9]+)">', rendered))
    if actual_ids != set(resolved.values()):
        raise ValueError("Native mentions do not match the verified reminder set")
    return rendered


def _verify_message(chat_id: str, message_id: str, image_key: str, period: str, expected_ids: set[str], sender_id: str) -> dict:
    data = _data(["im", "+chat-messages-list", "--chat-id", chat_id, "--order", "desc",
                  "--page-size", "50", "--no-reactions", "--as", "bot", "--format", "json"])
    matches = [message for message in data.get("messages", []) if message.get("message_id") == message_id]
    if len(matches) != 1:
        raise ValueError("Sent process message was not found in the target group")
    message = matches[0]
    actual_ids = {mention.get("id") for mention in message.get("mentions", [])}
    if (message.get("chat_id") != chat_id or message.get("msg_type") != "post"
            or image_key not in str(message.get("content")) or period not in str(message.get("content"))
            or actual_ids != expected_ids or message.get("sender", {}).get("open_bot_id") != sender_id):
        raise ValueError("Delivered image, period, sender, or native mentions differ from review")
    return {"message_id": message_id, "verified": True, "mention_ids": sorted(actual_ids)}


def _receipt_status(saved: dict) -> str:
    """Normalise this script's two receipt shapes into one lifecycle word.

    A success receipt is the raw send output and carries **no** ``status`` field;
    its only confirmation signal is ``readback.verified``.
    """
    if saved.get("status"):
        return saved["status"]
    return "sent_verified" if (saved.get("readback") or {}).get("verified") is True else "sent_unverified"


def _reverify(receipt: dict, receipt_path: Path, sender_open_id: str) -> dict:
    """Read back one already-sent report; this path has no send capability.

    Every input the readback needs was recorded by the first attempt, so no contact
    search, group-membership probe or upload is repeated -- and no send is possible,
    so a message already in the group can never be doubled by re-running this.
    """
    message_id = (receipt.get("response") or {}).get("message_id")
    image_key = receipt.get("image_key")
    if not (isinstance(message_id, str) and message_id.startswith("om_")) or not image_key:
        raise ValueError("Receipt lacks the message id or image key needed to re-verify")
    try:
        receipt["readback"] = _verify_message(receipt["chat_id"], message_id, image_key, receipt["period"],
                                              set(receipt.get("mention_ids") or ()), sender_open_id)
    except Exception as exc:
        receipt["readback"] = {"verified": False, "error": str(exc)}
        receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
        raise
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--level", choices=("supervisor", "consultant"), required=True)
    parser.add_argument("--review-dir", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--image-key", default="")
    parser.add_argument("--idempotency-key", required=True)
    parser.add_argument("--send", action="store_true")
    parser.add_argument("--reverify-only", action="store_true",
                        help="re-run the readback of an already-sent message; never sends")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,50}", args.idempotency_key):
        raise ValueError("Idempotency key must be 1-50 safe characters")
    config = json.loads(args.config.read_text(encoding="utf-8"))
    delivery = config["delivery"]
    if (config["report_type"] != "process" or (config["status"], config["schedule_enabled"]) not in (("preview_only", False), ("active", True))
            or delivery["sender_identity"] != "bot" or delivery["mention_format"] != "native_at"
            or delivery["require_complete_group_membership"] is not True or delivery["on_mention_gap"] != "invite_then_text"):
        raise ValueError("Process delivery configuration is invalid")
    profile = config["profiles"][args.level]
    level, chat_id = profile["level"], profile["target_chat_id"]
    receipt = args.review_dir / f"{args.level}_process_send_{args.idempotency_key}.json"
    if args.reverify_only:
        if not receipt.exists():
            raise ValueError("No receipt exists for this idempotency key")
        saved = _reverify(json.loads(receipt.read_text(encoding="utf-8")), receipt, delivery["sender_open_id"])
        print(json.dumps(saved, ensure_ascii=False, indent=2))
        if not saved["readback"]["verified"]:
            raise SystemExit(1)
        return
    if args.send and receipt.exists():
        saved = json.loads(receipt.read_text(encoding="utf-8"))
        verdict = resend.decide(_receipt_status(saved), (saved.get("response") or {}).get("message_id"))
        if verdict != resend.RESEND:
            raise ValueError("This idempotency key already has a recorded outcome; re-verify instead of re-sending")
        # Never confirmed: fall through and re-issue with the SAME key, so the platform
        # dedupes if an earlier attempt did reach the group.
    review = json.loads((args.review_dir / "review.json").read_text(encoding="utf-8"))
    item = review["results"][args.level]
    if item["level"] != level or item["process_tie_handling"] != "all_tied_minimum":
        raise ValueError("Review and process configuration differ")
    people = item["reminder_people"]
    verify_sender_membership(chat_id, delivery["sender_open_id"])
    resolved_all, display = _resolve_people(people)
    resolved, membership_note = refresh_membership(chat_id, resolved_all)
    text_only = {person['name'] for person in people} - set(resolved)
    invite_note = {"invited": [], "pending": [], "error": ""}
    image_key = args.image_key or (upload_image(args.review_dir / item["process_png"], "bot", 60) if args.send else "img_dry_run")
    markdown = (args.review_dir / item["process_message_file"]).read_text(encoding="utf-8")
    message = _render_message(markdown, level, people, resolved, display, image_key, item.get("reminder_by_grade"))
    command = ["im", "+messages-send", "--chat-id", chat_id, "--markdown", message,
               "--idempotency-key", args.idempotency_key, "--as", "bot", "--format", "json"]
    if not args.send:
        command.append("--dry-run")
    if args.send:
        receipt.write_text(json.dumps({"status": "send_attempt_started", "chat_id": chat_id,
                                       "period": review["period"], "idempotency_key": args.idempotency_key,
                                       "mention_ids": sorted(resolved.values())}, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        response = _data(command)
    except Exception as exc:
        if args.send:
            receipt.write_text(json.dumps({"status": "send_result_uncertain", "chat_id": chat_id,
                                           "period": review["period"], "idempotency_key": args.idempotency_key,
                                           "mention_ids": sorted(resolved.values()), "error": str(exc)},
                                          ensure_ascii=False, indent=2), encoding="utf-8")
        raise
    output = {"level": level, "chat_id": chat_id, "period": review["period"],
              "image_key": image_key, "mention_ids": sorted(resolved.values()),
              "text_fallback_names": sorted(text_only), "invite_attempt": invite_note,
              "member_lookup_error": membership_note.get("member_lookup_error", ""),
              "dry_run": not args.send, "response": response}
    if args.send:
        message_id = response.get("message_id")
        if not isinstance(message_id, str) or not message_id.startswith("om_"):
            raise ValueError("Send response had no message ID; delivery is uncertain")
        receipt.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        try:
            output["readback"] = _verify_message(chat_id, message_id, image_key, review["period"],
                                                   set(resolved.values()), delivery["sender_open_id"])
        except Exception as exc:
            output["readback"] = {"verified": False, "error": str(exc)}
        receipt.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))
    if args.send and not output["readback"]["verified"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
