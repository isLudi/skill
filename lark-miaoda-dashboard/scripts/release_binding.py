"""One-time, explicitly approved Tiangong release handoff; no remote writes."""
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import tempfile


def digest(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def active_policy(cfg, slot):
    policy = cfg["upstream"].get("approved_release_binding")
    if not policy or slot < datetime.fromisoformat(policy["not_before"]):
        return None
    if type(policy["version_id"]) is not int or policy["version_id"] <= 0:
        raise ValueError("invalid approved release identity")
    return policy


def binding_path(cfg, policy):
    return Path(cfg["state_dir"]) / ("upstream-release-%d.json" % policy["version_id"])


def scope_digest(cfg):
    keys = ("project_id", "folder", "menu_id", "task_name", "task_id", "nezha_task_id", "schedule_id", "owner")
    return digest({key: cfg["upstream"][key] for key in keys})


def bound_file_id(cfg, policy):
    path = binding_path(cfg, policy)
    if not path.exists():
        return None
    record = json.loads(path.read_text(encoding="utf-8"))
    signature = record.pop("binding_sha256", None)
    if (signature != digest(record) or record.get("policy_sha256") != digest(policy)
            or record.get("scope_sha256") != scope_digest(cfg)):
        raise ValueError("approved release binding is corrupt or changed")
    file_id = record.get("exec_file_id")
    if type(file_id) is not int or file_id <= 0 or record.get("version_id") != policy["version_id"]:
        raise ValueError("invalid bound execution file")
    return file_id


def validate_publication(plan, cfg, policy, execution, at):
    unsigned = {key: value for key, value in plan.items() if key != "plan_sha256"}
    if plan.get("plan_sha256") != digest(unsigned):
        raise ValueError("publication evidence Hash mismatch")
    if (plan.get("schema_version") != "tiangong2-task-publish-plan-v2"
            or plan.get("operation") != "publish_saved_tiangong2_task"
            or plan.get("status") != "blocked_already_published"
            or plan.get("read_only_plan") is not True or plan.get("remote_mutations") != 0):
        raise ValueError("approved release is not currently published")
    u = cfg["upstream"]
    for key in ("project_id", "folder", "menu_id", "task_name", "task_id", "nezha_task_id"):
        if plan["scope"].get(key) != u[key]:
            raise ValueError("publication scope drift: " + key)
    if plan["identity"].get("name") != u["owner"] or plan["scope"].get("owner_name") != u["owner"]:
        raise ValueError("publication owner drift")
    state = plan["baseline"]
    if (state.get("current_source_sha256") != policy["source_sha256"]
            or state.get("current_source_comparison_sha256") != policy["source_comparison_sha256"]
            or state.get("latest_published_source_comparison_sha256") != policy["source_comparison_sha256"]
            or state.get("latest_published_version_id") != policy["version_id"]
            or state.get("source_matches_latest_published") is not True):
        raise ValueError("publication differs from the exact approved source/version")
    versions = [item for item in state["versions"] if item.get("id") == policy["version_id"] and item.get("status") == "已发布"]
    if len(versions) != 1:
        raise ValueError("approved published version missing or ambiguous")
    published_at = datetime.fromisoformat(versions[0]["publishTime"]).replace(tzinfo=at.tzinfo)
    verified_at = datetime.fromisoformat(policy["publication_verified_at"])
    started_at = datetime.fromisoformat(execution["startTime"]).replace(tzinfo=at.tzinfo)
    ended_at = datetime.fromisoformat(execution["endTime"]).replace(tzinfo=at.tzinfo)
    observed_at = datetime.fromisoformat(plan["created_at"])
    if (not published_at <= started_at <= ended_at <= observed_at or verified_at > started_at
            or not 0 <= (at - observed_at).total_seconds() <= 300):
        raise ValueError("publication evidence is stale or postdates execution start")


def verify_raw_only_log(log, policy, period):
    expected = policy["success_template"].format(period=period)
    if log.splitlines().count(expected) != 1 or any(
        marker in log for marker in ("汇总键同步完成", "汇总表字段校验通过")
    ):
        raise ValueError("execution log does not identify the approved raw-only release")


def persist_binding(cfg, policy, file_id, execution, plan, at):
    path = binding_path(cfg, policy)
    if path.exists():
        if bound_file_id(cfg, policy) != file_id:
            raise ValueError("execution file changed after one-time binding")
        return
    if type(file_id) is not int or file_id <= 0:
        raise ValueError("invalid candidate execution file")
    record = {"version_id": policy["version_id"], "exec_file_id": file_id,
              "policy_sha256": digest(policy), "scope_sha256": scope_digest(cfg), "execution_id": execution["id"],
              "publication_plan_sha256": plan["plan_sha256"], "bound_at": at.isoformat()}
    record["binding_sha256"] = digest(record)
    path.parent.mkdir(parents=True, exist_ok=True)
    # The scheduler's OS lock serializes this operation. Atomic replacement keeps
    # a crash from leaving a half-written permanent pin; delivery receipts are untouched.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, prefix="release-binding-", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(record, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    if bound_file_id(cfg, policy) != file_id:
        raise ValueError("execution file pin readback failed")
