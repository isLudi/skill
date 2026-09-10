"""Explicit department/channel registry and one canonical configuration per channel."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re

from ..paths import CONFIG_ROOT

DEFAULT_CHANNEL = "market_consultant/self_incubated_koc_5"


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def registry(root=CONFIG_ROOT):
    result = read_json(Path(root) / "channels.json")
    if result.get("schema_version") != 1:
        raise ValueError("Unsupported channel registry schema")
    return result


def validate_config(config, key):
    """Validate neutral identities; business semantics remain in the selected adapter."""
    if config.get("schema_version") != 1 or key != f"{config.get('domain')}/{config.get('channel_id')}":
        raise ValueError("Department/channel identity mismatch")
    if any(not re.fullmatch(r"[a-z][a-z0-9_]*", config.get(k, "")) for k in ("domain", "channel_id")):
        raise ValueError("Invalid department/channel key")
    if not config.get("channel") or not config.get("adapter"):
        raise ValueError("Channel and adapter must be explicit")
    channels = config.get("channels", [config["channel"]])
    if (not channels or any(not isinstance(channel, str) or not channel.strip() for channel in channels)
            or len(channels) != len(set(channels)) or config["channel"] != channels[0]):
        raise ValueError("Channels must be unique, non-empty, and start with the primary channel")
    targets = config.get("targets", [])
    if not targets or len({t["id"] for t in targets}) != len(targets) or len({t["chat_id"] for t in targets}) != len(targets):
        raise ValueError("Missing or duplicate delivery targets")
    for target in targets:
        if not re.fullmatch(r"[a-z][a-z0-9_]*", target["id"]) or not re.fullmatch(r"oc_[A-Za-z0-9]+", target["chat_id"]):
            raise ValueError("Invalid target ID; names must not be used as destinations")
        if type(target.get("enabled")) is not bool:
            raise ValueError("Each target must declare enabled explicitly")
    if type(config.get("schedule", {}).get("enabled")) is not bool:
        raise ValueError("Schedule enablement must be explicit")
    sender = config.get("sender", {})
    if sender.get("identity") not in {"user", "bot"} or not re.fullmatch(r"ou_[A-Za-z0-9]+", sender.get("open_id", "")):
        raise ValueError("Sender identity/open_id must be pinned")
    if not config.get("state_dir"):
        raise ValueError("A channel-owned state directory is required")
    return config


def load_channel(key, root=CONFIG_ROOT):
    root = Path(root).resolve()
    index = registry(root)
    if key not in index["channels"]:
        raise ValueError(f"Channel is not registered: {key}; no cross-department fallback")
    path = (root / index["channels"][key]).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Channel config escaped its configuration directory")
    config = validate_config(read_json(path), key)
    if config["domain"] not in index["domains"]:
        raise ValueError("Unknown department")
    state = Path(config["state_dir"]).resolve()
    for other_key, other_file in index["channels"].items():
        if other_key == key:
            continue
        other_path = (root / other_file).resolve()
        if not other_path.is_relative_to(root):
            raise ValueError("Channel config escaped its configuration directory")
        other_state = Path(read_json(other_path)["state_dir"]).resolve()
        if state.is_relative_to(other_state) or other_state.is_relative_to(state):
            raise ValueError("Channel state directories overlap; departments/channels must be isolated")
    return config


def select_targets(config, target_ids=None):
    requested = list(target_ids or [])
    if len(requested) != len(set(requested)):
        raise ValueError("Repeated target selection")
    known = {target["id"]: target for target in config["targets"]}
    if any(target not in known or not known[target]["enabled"] for target in requested):
        raise ValueError("Unknown or disabled target; do not substitute a group name")
    selected = [known[target] for target in requested] if requested else [t for t in config["targets"] if t["enabled"]]
    if not selected:
        raise ValueError("No enabled delivery target")
    return deepcopy(selected)


def source_defaults(config, target=None):
    target = target or select_targets(config)[0]
    return {**deepcopy(config["source"]), "default_channel": config["channel"],
            "default_channels": deepcopy(config.get("channels", [config["channel"]])),
            "default_chat_id": target["chat_id"], "sender_identity": config["sender"]["identity"]}


def schedule_config(config, target):
    state = Path(config["state_dir"])
    # Preserve the deployed primary ledger; extra groups get independent state.
    if target["id"] != config["targets"][0]["id"]:
        state = state / "targets" / target["id"]
    return {**deepcopy(config["schedule"]), "schema_version": 2,
            "domain": config["domain"], "channel_id": config["channel_id"], "target_id": target["id"],
            "channel_key": f"{config['domain']}/{config['channel_id']}",
            "report_profile": config["source"]["report_profile"], **deepcopy(config["report"]),
            "channels": deepcopy(config.get("channels", [config["channel"]])),
            "chat_id": target["chat_id"], "chat_name": target["display_name"],
            "bot_name": config["sender"]["name"], "bot_open_id": config["sender"]["open_id"],
            "base_as": config["base_identity"], "state_dir": str(state),
            "raw_table_id": config["source"]["raw_table_id"],
            "upstream": deepcopy(config["upstream"])}


def resolve_compat_config(path, kind):
    """Small pointer files keep existing launch commands valid without duplicate settings."""
    data = read_json(path)
    if "channel_ref" not in data:
        return data
    config = load_channel(data["channel_ref"])
    target = select_targets(config, [data["target_id"]])[0]
    return source_defaults(config, target) if kind == "source" else schedule_config(config, target)


def require_registered_schedule(cfg):
    if "channel_key" not in cfg:
        return
    registered = load_channel(cfg["channel_key"])
    target = select_targets(registered, [cfg["target_id"]])[0]
    expected = schedule_config(registered, target)
    for name in ("domain", "channel_id", "channels", "chat_id", "report_profile", "bot_open_id", "raw_table_id"):
        if cfg.get(name) != expected[name]:
            raise ValueError("Registered delivery scope drift: " + name)
