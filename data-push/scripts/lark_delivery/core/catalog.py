"""Explicit department/channel registry and one canonical configuration per channel."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from pathlib import PurePosixPath
import re

from ..paths import CONFIG_ROOT, WORKSPACE_ROOT

DEFAULT_CHANNEL = "market_consultant/self_incubated_koc_5"
DEFAULT_MIAODA_DEPLOYMENT = "market_consultant/miaoda/cloud_data_push"
DEFAULT_MIAODA_WORKFLOW = "supervisor_koc_douyin_sync"


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def registry(root=CONFIG_ROOT):
    result = read_json(Path(root) / "channels.json")
    if result.get("schema_version") != 1:
        raise ValueError("Unsupported channel registry schema")
    return result


def _relative_deployment_path(value, field):
    path = PurePosixPath(str(value).replace("\\", "/"))
    if not value or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Invalid deployment path: {field}")
    return path


def validate_deployment_workflow(workflow_id, definition, domain):
    if not re.fullmatch(r"[a-z][a-z0-9_]*", workflow_id):
        raise ValueError("Invalid Miaoda workflow identity")
    contract_ref = _relative_deployment_path(definition.get("contract_ref", ""), "contract_ref")
    expected_contract_prefix = PurePosixPath("departments") / domain
    if contract_ref.parent != expected_contract_prefix or contract_ref.suffix != ".md":
        raise ValueError("Miaoda workflow contract_ref must belong to its department")
    source_ref = definition.get("source_channel_ref")
    if source_ref is not None:
        if (not re.fullmatch(r"[a-z][a-z0-9_]*/[a-z][a-z0-9_]*", source_ref)
                or source_ref.split("/", 1)[0] != domain):
            raise ValueError("Miaoda source_channel_ref must be an explicit same-department local channel")
    _relative_deployment_path(definition.get("module_root", ""), "module_root")
    if not re.fullmatch(r"[a-z][a-z0-9-]*", definition.get("automation_namespace", "")):
        raise ValueError("Invalid Miaoda automation namespace")
    if not re.fullmatch(r"[a-z][a-z0-9_]*", definition.get("ledger_namespace", "")):
        raise ValueError("Invalid Miaoda ledger namespace")
    if definition.get("style_owner") != domain:
        raise ValueError("Miaoda style owner must match its department")
    return definition


def validate_deployment(definition, key):
    """Validate one department-owned Miaoda app and its isolated workflows."""
    if definition.get("schema_version") != 1:
        raise ValueError("Unsupported deployment schema")
    domain = definition.get("domain", "")
    surface = definition.get("execution_surface", "")
    deployment_id = definition.get("deployment_id", "")
    if key != f"{domain}/{surface}/{deployment_id}":
        raise ValueError("Department/surface/deployment identity mismatch")
    if not re.fullmatch(r"[a-z][a-z0-9_]*", domain) or not re.fullmatch(r"[a-z][a-z0-9_]*", deployment_id):
        raise ValueError("Invalid deployment identity")
    if surface != "miaoda":
        raise ValueError("Only explicit Miaoda deployments belong in deployments.json")
    if definition.get("runtime_base") != "codex_home":
        raise ValueError("Miaoda runtime_base must be codex_home")
    runtime_path = _relative_deployment_path(definition.get("runtime_root", ""), "runtime_root")
    _relative_deployment_path(definition.get("identity_file", ""), "identity_file")
    if runtime_path.parts[0] != "runtime":
        raise ValueError("Miaoda runtime_root must stay under the Codex runtime directory")
    if not re.fullmatch(r"app_[A-Za-z0-9]+", definition.get("expected_app_id", "")):
        raise ValueError("A pinned Miaoda app_id is required")
    if definition.get("lifecycle") not in {"prototype", "disabled", "active"}:
        raise ValueError("Unsupported Miaoda deployment lifecycle")
    if definition.get("local_schedule_relation") != "independent":
        raise ValueError("Miaoda maintenance must not take ownership of a local schedule")
    workflows = definition.get("workflows")
    if not isinstance(workflows, dict) or not workflows:
        raise ValueError("A Miaoda deployment must register at least one workflow")
    for workflow_id, workflow in workflows.items():
        validate_deployment_workflow(workflow_id, workflow, domain)
    return definition


def validate_deployment_registry(index):
    if index.get("schema_version") != 1 or not isinstance(index.get("deployments"), dict):
        raise ValueError("Unsupported deployment registry schema")
    definitions = []
    for key, definition in index["deployments"].items():
        definitions.append((key, validate_deployment(definition, key)))
    for field in ("runtime_root", "expected_app_id"):
        values = [str(definition[field]).replace("\\", "/").lower() for _, definition in definitions]
        if len(values) != len(set(values)):
            raise ValueError(f"Miaoda deployments must not share {field}")
    workflow_resources = [
        (key, workflow_id, definition, workflow)
        for key, definition in definitions
        for workflow_id, workflow in definition["workflows"].items()
    ]
    for field in ("automation_namespace", "ledger_namespace"):
        values = [str(workflow[field]).lower() for _, _, _, workflow in workflow_resources]
        if len(values) != len(set(values)):
            raise ValueError(f"Miaoda workflows must not share {field}")
    module_paths = [
        f"{definition['runtime_root']}/{workflow['module_root']}".replace("\\", "/").lower()
        for _, _, definition, workflow in workflow_resources
    ]
    if len(module_paths) != len(set(module_paths)):
        raise ValueError("Miaoda workflows must not share module_root")
    return index


def deployment_registry(root=CONFIG_ROOT):
    return validate_deployment_registry(read_json(Path(root) / "deployments.json"))


def load_deployment(key, root=CONFIG_ROOT, workspace_root=WORKSPACE_ROOT):
    """Resolve a reviewed Miaoda binding and independently read its local app identity."""
    root = Path(root).resolve()
    workspace_root = Path(workspace_root).resolve()
    deployments = deployment_registry(root)
    if key not in deployments["deployments"]:
        raise ValueError(f"Deployment is not registered: {key}; no cross-department fallback")
    definition = validate_deployment(deepcopy(deployments["deployments"][key]), key)
    channels = registry(root)
    if definition["domain"] not in channels["domains"]:
        raise ValueError("Unknown deployment department")
    runtime_root = (workspace_root / Path(definition["runtime_root"])).resolve()
    runtime_base = (workspace_root / "runtime").resolve()
    if not runtime_root.is_relative_to(runtime_base) or not runtime_root.is_dir():
        raise ValueError("Miaoda runtime root is missing or escaped the Codex runtime directory")
    identity_path = (runtime_root / Path(definition["identity_file"])).resolve()
    if not identity_path.is_relative_to(runtime_root):
        raise ValueError("Miaoda deployment resource escaped its runtime root")
    if not identity_path.is_file():
        raise ValueError("Miaoda identity file is missing")
    identity = read_json(identity_path)
    if identity.get("app_id") != definition["expected_app_id"]:
        raise ValueError("Miaoda app identity drift")
    references_root = (root.parent / "references").resolve()
    for workflow_id, workflow in definition["workflows"].items():
        contract_path = (references_root / Path(workflow["contract_ref"])).resolve()
        module_root = (runtime_root / Path(workflow["module_root"])).resolve()
        if not contract_path.is_relative_to(references_root) or not module_root.is_relative_to(runtime_root):
            raise ValueError(f"Miaoda workflow {workflow_id} resource escaped its owner root")
        if not contract_path.is_file() or not module_root.is_dir():
            raise ValueError(f"Miaoda workflow {workflow_id} contract or module root is missing")
        source_ref = workflow.get("source_channel_ref")
        if source_ref is not None:
            if source_ref not in channels["channels"]:
                raise ValueError("Miaoda workflow references an unregistered local channel contract")
            source_channel = load_channel(source_ref, root)
            if source_channel["domain"] != definition["domain"]:
                raise ValueError("Miaoda workflow references a cross-department local channel contract")
    return definition


def load_deployment_workflow(deployment_key, workflow_id, root=CONFIG_ROOT, workspace_root=WORKSPACE_ROOT):
    deployment = load_deployment(deployment_key, root, workspace_root)
    if workflow_id not in deployment["workflows"]:
        raise ValueError(f"Miaoda workflow is not registered: {workflow_id}; no cross-department fallback")
    return deepcopy(deployment["workflows"][workflow_id])


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
