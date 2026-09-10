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
