"""Legacy manual delivery outlet; current channel delivery uses its guarded scheduler."""
from __future__ import annotations
import json
from typing import Any
from ..domains.market_consultant import grade_report
from ..domains.market_consultant.channels import self_incubated_koc_5 as broadcast_policy


def deliver_context(context, args, *, services):
    if context.get("report_profile") == "grade-compact":
        if context["identity"] != "bot":
            raise SystemExit("该固定群的正式播报只允许已核验的管家机器人身份")
        if context["mention_target"] != "manager" or any(context["mention_info"].get(k) for k in ("lookup_error", "unresolved", "ambiguous", "nonmembers")):
            raise SystemExit("正式分年级播报要求所有最低负责人均已核验并在群内，不能降级为纯姓名")
        if grade_report.mention_ids(context["markdown"]) != set(context["mention_info"]["resolved"].values()):
            raise SystemExit("消息中的@账号与已核验负责人集合不一致")
        if not args.dry_run:
            services.verify_grade_bot_identity()
            broadcast_policy.enforce_live_calendar(context["period"], context["report_type"])
            for section in grade_report.sections(context["report_type"]):
                if not context.get("image_path" if section == "process" else "result_image_path"):
                    raise SystemExit("正式分年级播报必须包含所选类型的图片")
        services.verify_chat(context["chat_id"], context.get("chat_name", ""), context["identity"], args.timeout)

    if context["mention_info"]["lookup_error"] and not args.allow_unresolved_mentions and not args.no_mentions:
        raise SystemExit("通讯录查询失败，未取得可验证的 @ 结果；请修复 user 权限、提供 --mention-map，或显式 --allow-unresolved-mentions")
    if (context["mention_info"]["unresolved"] or context["mention_info"]["ambiguous"]) and not args.allow_unresolved_mentions and not args.no_mentions:
        raise SystemExit("存在未唯一解析的 @ 姓名；为避免误 @，请补充 --mention-map/权限，或显式 --allow-unresolved-mentions")
    if not context["chat_id"]:
        raise SystemExit("真实发送需要 --chat-id 或 CHAT_ID")
    if context["mention_info"].get("nonmembers"):
        raise SystemExit("存在尚未入群的 @ 人员，停止发送")

    if args.dry_run:
        services.send_markdown(context["chat_id"], context["markdown"], context["idempotency_key"], context["identity"], dry_run=True, timeout=args.timeout)
        services.print_preview(context)
        print("\n[ok] lark-cli dry-run 通过（未上传图片、未发送）")
        return 0

    prior = services._ledger_records(context["ledger"]).get(context["idempotency_key"])
    if prior and prior.get("status") == "sent" and prior.get("message_id"):
        cleanup = {}
        for slot, path, _refs in services._image_slots(context):
            if path:
                cleanup[slot] = services._cleanup_local_image(path)
        print(
            json.dumps(
                {
                    "status": "already_sent",
                    "message_id": prior["message_id"],
                    "idempotency_key": context["idempotency_key"],
                    "image_local_cleanup": cleanup,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    markdown = context["markdown"]
    image_keys: dict[str, str] = {}
    image_cleanup: dict[str, Any] = {}
    for slot, path, _refs in services._image_slots(context):
        if path:
            image_cleanup[slot] = {
                "attempted": False,
                "deleted": False,
                "status": "not_attempted",
                "error": "",
            }
    try:
        for slot, path, refs in services._image_slots(context):
            if not path:
                continue
            image_key = services.upload_image(path, context["identity"], args.timeout)
            image_keys[slot] = image_key
            for ref in refs:
                markdown = markdown.replace("](%s)" % ref, "](%s)" % image_key)
        if context.get("report_profile") == "grade-compact":
            broadcast_policy.enforce_live_calendar(context["period"], context["report_type"])
            if services.mention_nonmembers(context["chat_id"], context["mention_info"]["resolved"], "bot", args.timeout):
                raise ValueError("负责人已离开目标群，停止发送")
        response = services.send_markdown(context["chat_id"], markdown, context["idempotency_key"], context["identity"], dry_run=False, timeout=args.timeout)
        message_id = services._message_id(response)
        if not message_id:
            raise RuntimeError("发送接口未返回 message_id，不能视为已送达")
        # Keep the PNG when upload succeeded but final message delivery did
        # not; after message_id is verified, remove it immediately to avoid
        # accumulating period snapshots on the local disk.
        for slot, path, _refs in services._image_slots(context):
            if not path or not image_keys.get(slot):
                continue
            image_cleanup[slot] = services._cleanup_local_image(path)
            if not image_cleanup[slot]["deleted"]:
                print("[warning] 群消息已送达，但%s图片删除失败：%s" % (slot, image_cleanup[slot]["error"]))
        services._append_ledger(
            context["ledger"],
            {
                "status": "sent",
                "message_id": message_id,
                "idempotency_key": context["idempotency_key"],
                "period": context["period"],
                "chat_id": context["chat_id"],
                "image_key": image_keys.get("process") or None,
                "result_image_key": image_keys.get("result") or None,
                "image_local_cleanup": image_cleanup,
            },
        )
        print(
            json.dumps(
                {
                    "status": "sent",
                    "message_id": message_id,
                    "idempotency_key": context["idempotency_key"],
                    "ledger": str(context["ledger"]),
                    "image_keys": image_keys,
                    "image_local_cleanup": image_cleanup,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    except Exception as exc:
        for slot, path, _refs in services._image_slots(context):
            if path:
                image_cleanup[slot] = {
                    "attempted": False,
                    "deleted": False,
                    "status": "preserved_after_send_failure",
                    "error": "",
                }
        services._append_ledger(
            context["ledger"],
            {
                "status": "failed",
                "idempotency_key": context["idempotency_key"],
                "period": context["period"],
                "chat_id": context["chat_id"],
                "error": str(exc)[:500],
                "image_key": image_keys.get("process") or None,
                "result_image_key": image_keys.get("result") or None,
                "image_local_cleanup": image_cleanup,
            },
        )
        raise
