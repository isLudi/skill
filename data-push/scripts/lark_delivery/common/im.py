"""Immutable chat ID checks, complete membership and image/post transport."""
from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Any, Mapping
from .runtime import run_lark
from .values import _json_payload, _unwrap, _string, _find_first


def verify_chat(chat_id: str, chat_name: str, identity: str, timeout: int, *, runner=None) -> dict[str, Any]:
    """Resolve the already-approved immutable ID; names are display metadata only."""
    if not re.fullmatch(r"oc_[A-Za-z0-9]+", chat_id or ""):
        raise ValueError("必须提供有效的群唯一chat_id，不能使用群名称代替")
    payload = _unwrap(_json_payload((runner or run_lark)([
        "im", "chats", "get", "--params", json.dumps({"chat_id": chat_id, "user_id_type": "open_id"}),
        "--as", identity, "--format", "json",
    ], timeout=timeout)))
    data = payload.get("chat", payload)
    if data.get("chat_id") and data["chat_id"] != chat_id:
        raise ValueError("群信息回读ID不匹配")
    if data.get("chat_mode") not in (None, "group", "topic") or not data.get("name"):
        raise ValueError("群唯一ID未返回可验证的群信息")
    current_name = _string(data["name"])
    return {"chat_id": chat_id, "name": current_name,
            "name_changed": bool(chat_name and chat_name != current_name)}


def mention_nonmembers(chat_id: str, resolved: Mapping[str, str], identity: str, timeout: int, *, runner=None) -> list[str]:
    """Verify exact account IDs against a complete, untruncated member list."""
    if not chat_id:
        raise ValueError("核验 @ 人员群成员资格需要明确接收群")
    data = _unwrap(_json_payload((runner or run_lark)([
        "im", "+chat-members-list", "--chat-id", chat_id, "--member-types", "user",
        "--member-id-type", "open_id", "--page-all", "--page-limit", "10",
        "--as", identity, "--format", "json",
    ], timeout=timeout)))
    if data.get("has_more") is not False or data.get("truncations"):
        raise ValueError("群成员列表不完整，不能确认 @ 人员资格")
    users = data.get("users", [])
    ids = {item.get("member_id") for item in users}
    if not all(ids) or len(ids) != len(users) or len(ids) != int(data["user_total"]):
        raise ValueError("群成员列表数量或账号校验失败")
    return sorted(name for name, open_id in resolved.items() if open_id not in ids)


def invite_members(chat_id: str, open_ids, identity: str, timeout: int, *, runner=None) -> dict[str, Any]:
    """Invite @-targets into the chat as the sender bot; never raises for person-level failures.

    2026-10-04 policy: a push must not depend on any specific human identity, and a
    missing member must be invited by the bot before falling back to plain-name text.
    The return value records the attempt for the delivery ledger: ``invited`` ids are
    usable immediately, ``pending`` ids await group-owner approval and stay text-only,
    and ``error`` carries any transport/API failure (which also leaves everyone
    text-only instead of blocking the push).
    """
    ids = sorted({open_id for open_id in open_ids if isinstance(open_id, str) and open_id.startswith("ou_")})
    if not ids:
        return {"invited": [], "pending": [], "error": ""}
    try:
        payload = _unwrap(_json_payload((runner or run_lark)([
            "im", "chat.members", "create", "--chat-id", chat_id,
            "--member-id-type", "open_id",
            "--data", json.dumps({"id_list": ids}, ensure_ascii=False),
            "--as", identity, "--format", "json",
        ], timeout=timeout)))
    except Exception as exc:  # noqa: BLE001 - an invitation failure degrades to text, never a block
        return {"invited": [], "pending": [], "error": str(exc)[:300]}
    rejected = set(payload.get("invalid_id_list") or []) | set(payload.get("not_existed_id_list") or [])
    pending = list(payload.get("pending_approval_id_list") or [])
    return {"invited": [item for item in ids if item not in rejected and item not in set(pending)],
            "pending": pending, "error": ""}


def upload_image(image_path: Path, identity: str, timeout: int, *, runner=None) -> str:
    try:
        payload = _unwrap(
            _json_payload(
                (runner or run_lark)(
                    [
                        "im",
                        "images",
                        "create",
                        "--data",
                        '{"image_type":"message"}',
                        "--file",
                        "./%s" % image_path.name,
                        "--format",
                        "json",
                        "--as",
                        identity,
                    ],
                    cwd=str(image_path.parent),
                    timeout=timeout,
                )
            )
        )
    except RuntimeError as exc:
        if "im:resource" in str(exc):
            raise RuntimeError("图片推送需要发送身份具备 im:resource；当前身份未授权，请先补授权或改用已具备该权限的 bot") from exc
        raise
    image_key = _string(_find_first(payload, ("image_key", "imageKey")))
    if not image_key.startswith("img_"):
        raise RuntimeError("图片上传未返回可用 image_key")
    return image_key


def send_markdown(chat_id: str, markdown: str, key: str, identity: str, *, dry_run: bool, timeout: int, runner=None) -> Any:
    command = [
        "im",
        "+messages-send",
        "--chat-id",
        chat_id,
        "--markdown",
        markdown,
        "--idempotency-key",
        key,
        "--format",
        "json",
        "--as",
        identity,
    ]
    if dry_run:
        command.append("--dry-run")
    return _unwrap(_json_payload((runner or run_lark)(command, timeout=timeout)))


def _message_id(payload: Any) -> str:
    return _string(_find_first(payload, ("message_id", "messageId", "msg_id")))
