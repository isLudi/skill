"""Send one reviewed Qingcheng transformation report with verified native mentions.

Reads the per-channel review.json produced by preview_qingcheng_transformation.py
(results.<channel>.levels.<slug>), resolves reminder people to active employees,
checks group membership, uploads the PNG, renders native @mentions into the
reminder lines and sends with an idempotency key plus readback verification.
The fallback reminder line (no eligible people) is kept verbatim without mentions.
The local-supervisor grade_text mode (review item carries reminder_grades and no
people) sends the reviewed message verbatim -- it names top grades instead of
mentioning people, so the readback expects an empty mention set.
"""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

from lark_delivery.common import resend
from lark_delivery.common.im import invite_members, mention_nonmembers, upload_image

from send_qingcheng_process import _data, _resolve_people, _verify_message

DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "config" / "departments" / "qingcheng" / "transformation_preview.json"
REMINDER_METRIC = "综合单效"
PRAISE_SUFFIX = " 🎉🎉🎉"


def _reminder_line(kind: str, grade: str | None, names: list[str]) -> str:
    if kind == "supervisor":
        return f"- {REMINDER_METRIC}较高的主管：{'、'.join(names)}{PRAISE_SUFFIX}"
    return f"- {grade}年级{REMINDER_METRIC}较高的顾问：{'、'.join(names)}{PRAISE_SUFFIX}"


def _render_message(markdown: str, item: dict, resolved: dict[str, str], display: dict[str, str], image_key: str) -> str:
    groups: list[tuple[str, str | None, list[dict]]] = []
    if item.get("reminder_people"):
        groups.append(("supervisor", None, item["reminder_people"]))
    for grade, people in (item.get("reminder_by_grade") or {}).items():
        groups.append(("consultant", grade, people))
    for kind, grade, people in groups:
        names = [person["name"] for person in people]
        original = _reminder_line(kind, grade, names)
        # Names absent from `resolved` are the sanctioned plain-name fallback
        # (bot invitation already attempted, still absent or unresolvable).
        mentions = "、".join(
            f'<at user_id="{resolved[name]}">{html.escape(display[name])}</at>' if name in resolved
            else html.escape(name) for name in names)
        prefix = original.split("：", 1)[0]
        if markdown.count(original) != 1:
            raise ValueError("Reviewed reminder line differs from resolved people")
        markdown = markdown.replace(original, prefix + "：" + mentions + PRAISE_SUFFIX)
    image_ref = f"]({item['png']})"
    if markdown.count(image_ref) != 1 or not image_key.startswith("img_"):
        raise ValueError("Reviewed message has no single uploaded image reference")
    rendered = markdown.replace(image_ref, f"]({image_key})")
    expected = {open_id for group in groups for _, _, people in [group]
                for person in people if person["name"] in resolved
                for open_id in [resolved[person["name"]]]}
    actual_ids = set(re.findall(r'<at user_id="(ou_[A-Za-z0-9]+)">', rendered))
    if actual_ids != expected:
        raise ValueError("Native mentions do not match the verified reminder set")
    return rendered


def _verify_message_transformation(chat_id: str, message_id: str, image_key: str, period: str,
                                   expected_ids: set[str], sender_id: str) -> dict:
    return _verify_message(chat_id, message_id, image_key, period, expected_ids, sender_id)


def _receipt_status(saved: dict) -> str:
    if saved.get("status"):
        return saved["status"]
    return "sent_verified" if (saved.get("readback") or {}).get("verified") is True else "sent_unverified"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel", required=True,
                        choices=("private", "douyin_dm", "public_pool", "partner_books", "partner_local"))
    parser.add_argument("--level", choices=("supervisor", "consultant", "dept"), required=True)
    parser.add_argument("--review-dir", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--image-key", default="")
    parser.add_argument("--idempotency-key", required=True)
    parser.add_argument("--send", action="store_true")
    parser.add_argument("--allow-fallback", action="store_true",
                        help="allow sending a fallback-only message (no reminder people) on explicit manual order")
    parser.add_argument("--reverify-only", action="store_true",
                        help="re-run the readback of an already-sent message; never sends")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,50}", args.idempotency_key):
        raise ValueError("Idempotency key must be 1-50 safe characters")
    config = json.loads(args.config.read_text(encoding="utf-8"))
    delivery = config["delivery"]
    if (config["report_type"] != "transformation" or (config["status"], config["schedule_enabled"]) not in
            (("preview_only", False), ("active", True))
            or delivery["sender_identity"] != "bot" or delivery["mention_format"] != "native_at"
            or delivery["require_complete_group_membership"] is not True or delivery["on_mention_gap"] != "invite_then_text"):
        raise ValueError("Transformation delivery configuration is invalid")
    channel_cfg = next((c for c in config["channels"] if c["id"] == args.channel), None)
    if channel_cfg is None:
        raise ValueError(f"Channel not configured: {args.channel}")
    profile = channel_cfg["profiles"][args.level]
    level, chat_id = profile["level"], profile["target_chat_id"]
    receipt = args.review_dir / f"{args.level}_transformation_send_{args.idempotency_key}.json"
    if args.reverify_only:
        if not receipt.exists():
            raise ValueError("No receipt exists for this idempotency key")
        saved = json.loads(receipt.read_text(encoding="utf-8"))
        saved["readback"] = _verify_message_transformation(
            chat_id, (saved.get("response") or {}).get("message_id"), saved.get("image_key", ""),
            saved.get("period", ""), set(saved.get("mention_ids") or ()), delivery["sender_open_id"])
        receipt.write_text(json.dumps(saved, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(saved, ensure_ascii=False, indent=2))
        if not saved["readback"]["verified"]:
            raise SystemExit(1)
        return
    if args.send and receipt.exists():
        saved = json.loads(receipt.read_text(encoding="utf-8"))
        verdict = resend.decide(_receipt_status(saved), (saved.get("response") or {}).get("message_id"))
        if verdict != resend.RESEND:
            raise ValueError("This idempotency key already has a recorded outcome; re-verify instead of re-sending")
    review = json.loads((args.review_dir / "review.json").read_text(encoding="utf-8"))
    item = review["results"][args.channel]["levels"][args.level]
    if item["level"] != level:
        raise ValueError("Review and transformation configuration differ")
    people = list(item.get("reminder_people") or [])
    for group in (item.get("reminder_by_grade") or {}).values():
        people.extend(group)
    if item.get("reminder_mode") == "none":
        # 学部级：消息本就不含提醒行（文字抬头 + 图片），原样发送、无 @。
        resolved, display = {}, {}
        mention_ids: list[str] = []
    elif not people and item.get("reminder_grades"):
        # 本地化主管 grade_text 模式：消息只点名年级、不含任何 @，原样发送。
        resolved, display = {}, {}
        mention_ids: list[str] = []
    elif not people and args.allow_fallback:
        # 手动指令明确授权：fallback 文案（无可比数据）原样发送，无 @。
        resolved, display = {}, {}
        mention_ids = []
    elif not people:
        raise ValueError("No reminder people in review; a fallback-only message needs manual sending")
    else:
        resolved_all, display = _resolve_people(people)
        # 2026-10-04 policy: never block on person resolution; invite first, text after.
        missing = mention_nonmembers(chat_id, resolved_all, "bot", 60)
        invite_note = {"invited": [], "pending": [], "error": ""}
        if missing:
            invite_note = invite_members(chat_id, [resolved_all[name] for name in missing], "bot", 60)
            try:
                missing = mention_nonmembers(chat_id, resolved_all, "bot", 60)
            except Exception as exc:  # noqa: BLE001 - a re-check failure degrades to text
                invite_note["recheck_error"] = str(exc)[:300]
        text_only = set(missing)
        resolved = {name: open_id for name, open_id in resolved_all.items() if name not in text_only}
        mention_ids = sorted(resolved.values())
    image_key = args.image_key or (upload_image(args.review_dir / item["png"], "bot", 60) if args.send else "img_dry_run")
    markdown = (args.review_dir / item["message_file"]).read_text(encoding="utf-8")
    message = _render_message(markdown, item, resolved, display, image_key)
    command = ["im", "+messages-send", "--chat-id", chat_id, "--markdown", message,
               "--idempotency-key", args.idempotency_key, "--as", "bot", "--format", "json"]
    if not args.send:
        command.append("--dry-run")
    if args.send:
        receipt.write_text(json.dumps({"status": "send_attempt_started", "chat_id": chat_id,
                                       "channel": args.channel, "period": review["period"],
                                       "idempotency_key": args.idempotency_key,
                                       "mention_ids": mention_ids}, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        response = _data(command)
    except Exception as exc:
        if args.send:
            receipt.write_text(json.dumps({"status": "send_result_uncertain", "chat_id": chat_id,
                                           "channel": args.channel, "period": review["period"],
                                           "idempotency_key": args.idempotency_key,
                                           "mention_ids": mention_ids, "error": str(exc)},
                                          ensure_ascii=False, indent=2), encoding="utf-8")
        raise
    output = {"level": level, "channel": args.channel, "chat_id": chat_id, "period": review["period"],
              "image_key": image_key, "mention_ids": mention_ids,
              "text_fallback_names": sorted(text_only) if people else [],
              "invite_attempt": invite_note if people else {"invited": [], "pending": [], "error": ""},
              "dry_run": not args.send, "response": response}
    if args.send:
        message_id = response.get("message_id")
        if not isinstance(message_id, str) or not message_id.startswith("om_"):
            raise ValueError("Send response had no message ID; delivery is uncertain")
        receipt.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        try:
            output["readback"] = _verify_message_transformation(chat_id, message_id, image_key, review["period"],
                                                                set(mention_ids), delivery["sender_open_id"])
        except Exception as exc:
            output["readback"] = {"verified": False, "error": str(exc)}
        receipt.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))
    if args.send and not output["readback"]["verified"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
