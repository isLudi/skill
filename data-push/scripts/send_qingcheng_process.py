"""Send one reviewed Qingcheng process group report with verified native mentions."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

from lark_delivery.common import resend
from lark_delivery.common.im import invite_members, mention_nonmembers, upload_image
from lark_delivery.common.runtime import run_lark


DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "config" / "departments" / "qingcheng" / "public_pool_process_preview.json"


def _data(args: list[str]) -> dict:
    payload = json.loads(run_lark(args))
    if payload.get("ok") is not True or not isinstance(payload.get("data"), dict):
        raise RuntimeError(f"Feishu read or write did not succeed: {payload.get('error')}")
    return payload["data"]


def _resolve_people(people: list[dict]) -> tuple[dict[str, str], dict[str, str]]:
    """Match source identities to one active employee using name and email account."""
    if not people or any(not p.get("name") for p in people):
        raise ValueError("Missing process reminder people")
    identities = {(person["name"], person.get("account")) for person in people}
    if len({name for name, _ in identities}) != len(identities):
        raise ValueError("Two reminder accounts share one source display name")
    def query_for(person: dict) -> str:
        account = person.get("account")
        return f"{account}@gaotu.cn" if account else re.sub(r"\d+$", "", person["name"])

    queries = sorted({query_for(p) for p in people})
    responses = [_data(["contact", "+search-user", "--queries", ",".join(queries[start:start + 20]),
                        "--exclude-external-users", "--lang", "zh_cn", "--as", "user", "--format", "json"])
                 for start in range(0, len(queries), 20)]
    status = {item["query"]: item for data in responses for item in data.get("queries", [])}
    users = [user for data in responses for user in data.get("users", [])]
    resolved, display = {}, {}
    for person in people:
        source_name = person["name"]
        query = query_for(person)
        if query not in status or status[query].get("error") or status[query].get("has_more") is not False:
            raise ValueError(f"Contact search was incomplete for {source_name}")
        suffix = re.search(r"(\d+)$", source_name)
        account = person.get("account")
        candidates = {}
        for user in users:
            if user.get("matched_query") != query or user.get("is_activated") is not True or user.get("is_cross_tenant"):
                continue
            label = user.get("localized_name")
            email_account = str(user.get("enterprise_email") or "").split("@", 1)[0]
            if account:
                if str(user.get("enterprise_email") or "").casefold() != query.casefold():
                    continue
            elif label not in {source_name, query} or (suffix and not email_account.endswith(suffix.group(1))):
                continue
            open_id = user.get("open_id")
            if isinstance(open_id, str) and re.fullmatch(r"ou_[A-Za-z0-9]+", open_id):
                candidates[open_id] = label
        if len(candidates) != 1:
            raise ValueError(f"Reminder identity is unresolved or ambiguous: {source_name}")
        open_id, label = next(iter(candidates.items()))
        resolved[source_name] = open_id
        display[source_name] = label
    if len(set(resolved.values())) != len(resolved):
        raise ValueError("Two reminder names resolved to the same employee")
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
        # invited by the bot already and still not in the group (or unresolvable).
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
    resolved_all, display = _resolve_people(people)
    # 2026-10-04 policy: never block on person resolution. Absent members are invited
    # once by the sender bot; anyone still absent afterwards degrades to a plain name.
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
