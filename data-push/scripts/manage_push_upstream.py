"""Verify and adopt one reviewed Tiangong2 binding without editing consumers."""

from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time
from zoneinfo import ZoneInfo

from lark_delivery.core.locks import runner_lock
from lark_delivery.domains.market_consultant import upstream as market_upstream
from lark_delivery.integrations.producer_bindings import PRODUCER_FILES, binding_path, read_binding_document
from lark_delivery.paths import SKILLS_ROOT


CHINA = ZoneInfo("Asia/Shanghai")
SCOPE_FIELDS = ("project_id", "folder", "menu_id", "task_id", "task_name", "nezha_task_id")
SHA256 = re.compile(r"[0-9a-f]{64}")


def _arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("verify", "adopt"))
    parser.add_argument("task_key", choices=tuple(PRODUCER_FILES))
    for name in ("version-id", "exec-file-id", "execution-id"):
        parser.add_argument("--" + name, type=int, required=True)
    parser.add_argument("--review-reference", help="Reviewed mapping and independent Base readback reference")
    parser.add_argument("--approve-source-sha256", help="Exact reviewed new raw published-source SHA-256")
    parser.add_argument("--channel-mapping-version", help="Reviewed four-digit market lead mapping version")
    parser.add_argument("--execution-receipt", type=Path,
                        help="Qingcheng controlled execution receipt for an approved release write")
    args = parser.parse_args()
    if min(args.version_id, args.exec_file_id, args.execution_id) <= 0:
        parser.error("IDs must be positive")
    if args.command == "adopt" and not (args.review_reference or "").strip():
        parser.error("adopt requires --review-reference")
    if args.review_reference and (
        len(args.review_reference) > 512 or any(ord(c) < 32 for c in args.review_reference)
    ):
        parser.error("review reference must be a single line of at most 512 characters")
    if args.approve_source_sha256 and not SHA256.fullmatch(args.approve_source_sha256):
        parser.error("--approve-source-sha256 must be 64 lowercase hex characters")
    if args.channel_mapping_version is not None and (
        args.task_key != "market_consultant.leads"
        or not re.fullmatch(r"\d{4}", args.channel_mapping_version)
    ):
        parser.error("--channel-mapping-version requires market_consultant.leads and four digits")
    return args


def _local_datetime(value):
    observed = datetime.fromisoformat(value)
    return observed.astimezone(CHINA) if observed.tzinfo else observed.replace(tzinfo=CHINA)


def _sha256(content):
    return hashlib.sha256(content).hexdigest()


def _publication(development, task_id, channel_mapping_version=None):
    rows = [row for row in development.list_versions(task_id) if row.get("status") == "已发布"]
    if len(rows) != 1:
        raise ValueError("current published version missing or ambiguous")
    row = rows[0]
    code = development.get_version_code(row["id"]).get("code")
    if not isinstance(code, str) or not code:
        raise ValueError("published source missing")
    if channel_mapping_version is not None:
        assignments = [
            node.value.value if isinstance(node.value, ast.Constant) else None
            for node in ast.walk(ast.parse(code))
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "CHANNEL_MAPPING_VERSION" for target in node.targets)
        ]
        if assignments != [channel_mapping_version]:
            raise ValueError("reviewed channel mapping version differs from the unique published source marker")
    return row["id"], row["ver"], row["publishTime"], _sha256(code.encode("utf-8"))


def _reviewed_market_binding(binding, args):
    version = getattr(args, "channel_mapping_version", None)
    if version is None:
        return binding
    if binding.get("task_key") != "market_consultant.leads" or not re.fullmatch(r"\d{4}", version):
        raise ValueError("channel mapping version requires the market lead producer and four digits")
    return {**binding, "channel_mapping_version": version}


def _schedule(development, operations, spec, binding):
    scope = binding["upstream"]
    live = operations.get_task_and_schedule(spec.nezha_task_id)
    effective = operations.get_schedule_config(spec.nezha_task_id)
    saved = development.get_schedule(spec.task_id)
    interval = binding["schedule_interval_hours"]
    minute = binding["schedule_start_minute"]
    phase = binding["schedule_anchor_hour"] % interval
    phase_times = [_local_datetime(row["firstRunTime"]) for row in (live, effective, saved)]
    if (
        live.get("taskId") != spec.nezha_task_id
        or live.get("taskName") != scope["task_name"]
        or live.get("supervisor") != scope["owner"]
        or live.get("scheduleStatus") != 0
        or live.get("scheduleFrequency") != f"{interval}h"
        or ("schedule_id" in scope and live.get("scheduleId") != scope["schedule_id"])
        or effective.get("taskId") != spec.nezha_task_id
        or effective.get("periodic") is not True
        or effective.get("status") != 0
        or effective.get("runInterval") != interval
        or effective.get("timeUnit") != 1
        or saved.get("taskId") != spec.task_id
        or saved.get("runInterval") != interval
        or saved.get("timeUnit") != 1
        or any(time.minute != minute or time.hour % interval != phase for time in phase_times)
    ):
        raise ValueError("live effective or development schedule differs from the registered schedule")
    return live


def _run_config(row):
    config = row.get("runConfig")
    return json.loads(config) if isinstance(config, str) else config or {}


def _started(row):
    return row.get("startTime") or row.get("dispatchTime")


def _validate_execution(operations, spec, binding, execution, publication, args):
    upstream = binding["upstream"]
    config = _run_config(execution)
    period = _local_datetime(execution["periodTime"])
    started = _local_datetime(execution["startTime"])
    ended = _local_datetime(execution["endTime"])
    interval = binding["schedule_interval_hours"]
    if (
        execution.get("id") != args.execution_id
        or execution.get("taskId") != spec.nezha_task_id
        or execution.get("taskName") != upstream["task_name"]
        or execution.get("status") != 6
        or config.get("projectId") != spec.project_id
        or config.get("execFileId") != args.exec_file_id
        or period.minute != 0
        or not _local_datetime(publication[2]) <= started <= ended
    ):
        raise ValueError("reviewed execution is not a successful current-schedule instance of the exact binding")
    if config.get("triggerSourceEnum") == "EXECUTE":
        _verify_controlled_execution(binding, spec, execution, publication, args)
        return period
    if config.get("triggerSourceEnum") != "SCHEDULE":
        raise ValueError("unreviewed execution trigger")
    if period.hour % interval != binding["schedule_anchor_hour"] % interval:
        raise ValueError("reviewed SCHEDULE period differs from the registered schedule phase")
    if getattr(args, "execution_receipt", None) is not None:
        raise ValueError("execution receipt is only for a controlled EXECUTE")
    rows = operations.list_task_executions(spec.nezha_task_id, execution["periodTime"])
    scheduled = [row for row in rows if _run_config(row).get("triggerSourceEnum") == "SCHEDULE"]
    if len(scheduled) != 1 or scheduled[0].get("id") != args.execution_id:
        raise ValueError("reviewed execution is not the unique SCHEDULE instance for its period")
    return period


def _verify_controlled_execution(binding, spec, execution, publication, args):
    """Bind a Qingcheng release write to the operator's single-execution plan."""
    from _shared.config import TIANGONG2_TASK_RUNTIME_DIR
    from tiangong2_task.execution import load_execution_plan, reconciled_execution_period_matches
    from tiangong2_task.publishing import finalize_hash

    receipt_file = getattr(args, "execution_receipt", None)
    if binding["domain"] != "qingcheng" or receipt_file is None:
        raise ValueError("controlled execution requires a Qingcheng operator receipt")
    receipt_file = Path(receipt_file).resolve()
    runtime = TIANGONG2_TASK_RUNTIME_DIR.resolve()
    if not receipt_file.is_relative_to(runtime):
        raise ValueError("execution receipt is outside the operator runtime")
    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
    plan_file = Path(receipt.get("plan_file", "")).resolve()
    if not plan_file.is_relative_to(runtime):
        raise ValueError("execution plan is outside the operator runtime")
    plan = load_execution_plan(plan_file)
    scope = binding["upstream"]
    config = _run_config(execution)
    expected_scope = {key: scope[key] for key in SCOPE_FIELDS}
    if (
        receipt.get("schema_version") != "tiangong2-task-execution-receipt-v1"
        or finalize_hash(receipt, "receipt_sha256")["receipt_sha256"] != receipt.get("receipt_sha256")
        or receipt.get("ok") is not True or receipt.get("fully_verified") is not True
        or receipt.get("execute_request_sent") is not True
        or receipt.get("manual_attention_required") is not False
        or receipt.get("plan_sha256") != plan["plan_sha256"]
        or receipt.get("execution_id") != execution["id"]
        or receipt.get("trigger_successor") is not False
        or any(receipt.get("scope", {}).get(key) != value for key, value in expected_scope.items())
        or any(plan["scope"].get(key) != value for key, value in expected_scope.items())
        or plan["scope"].get("owner_name") != scope["owner"]
        or plan["baseline"].get("latest_published_version_id") != publication[0]
        or plan["baseline"].get("current_source_sha256") != publication[3]
        or not reconciled_execution_period_matches(plan, execution, receipt)
        or execution["id"] in plan["baseline"].get("baseline_execution_ids", [])
        or config.get("triggerSuccessor") is not False
        or config.get("disabledStages") != [] or config.get("rerunTaskId") is not None
        or config.get("params", {}) != {}
    ):
        raise ValueError("controlled execution receipt, source or scope differs")


def _require_latest(history, execution):
    execution_id = execution["id"]
    started = _local_datetime(execution["startTime"])
    rows = history["executions"]
    if sum(row.get("id") == execution_id for row in rows) != 1:
        raise ValueError("reviewed execution is outside the bounded latest execution history")
    for row in rows:
        if row.get("id") == execution_id:
            continue
        point = _started(row)
        if point and _local_datetime(point) >= started:
            raise ValueError("another upstream execution may have replaced the reviewed Base snapshot")
        if not point and row.get("status") != 0:
            raise ValueError("execution history has an unclassifiable write risk")


def _stage_evidence(bundle, binding, scope, period, execution, redact, runtime_dir):
    stages = bundle["stages"]
    if (
        bundle["execution_detail"].get("status") != 6
        or not stages
        or stages[-1]["metadata"].get("statusDesc") != "success"
        or any(
            stage["metadata"].get("taskId") != scope["nezha_task_id"]
            or stage["metadata"].get("statusDesc") not in {"success", "failed"}
            or not stage["log"]
            for stage in stages
        )
    ):
        raise ValueError("execution does not have complete terminal stage evidence")
    final_log = stages[-1]["log"]
    target = binding["target_table_id"]
    if binding["domain"] == "qingcheng":
        summary = _qingcheng_evidence(final_log, binding["task_key"], target)
    else:
        summary = _market_evidence(
            bundle, binding, scope, period, execution, redact(final_log).text, target, runtime_dir,
        )
    return {
        "target_table_id": target,
        "rows": summary["total"],
        "business_periods": sorted(summary["periods"]),
        **({"audit_field_count": summary["field_count"]} if binding["domain"] == "qingcheng" else {}),
        "stage_logs": [
            {"stage_id": stage["metadata"]["id"], "sha256": _sha256(stage["log"].encode("utf-8"))}
            for stage in stages
        ],
    }


def _market_evidence(bundle, binding, scope, period, execution, final_log, target, runtime_dir):
    market_scope = {**scope, "exec_file_id": _run_config(execution)["execFileId"]}
    if "channel_mapping_version" in binding:
        market_scope["channel_mapping_version"] = binding["channel_mapping_version"]
    config = {
        "upstream": market_scope,
        "raw_table_id": target,
        "volume_report": {"volume_table_id": target},
    }
    with tempfile.TemporaryDirectory(prefix="data-push-release-", dir=runtime_dir) as directory:
        root = Path(directory)
        raw = final_log.encode("utf-8")
        (root / "stage.log").write_bytes(raw)
        metadata = [{"metadata": stage["metadata"]} for stage in bundle["stages"]]
        metadata[-1].update(log_file="stage.log", log_sha256=_sha256(raw))
        evidence = {
            **bundle,
            "identity": {"name": scope["owner"]},
            "scope": {key: scope[key] for key in SCOPE_FIELDS},
            "stages": metadata,
        }
        parser = (
            market_upstream.parse_complete_log
            if binding["task_key"] == "market_consultant.leads"
            else market_upstream.parse_volume_log
        )
        return parser(evidence, root, config, period, execution)


def _qingcheng_evidence(log, task_key, target):
    process = task_key == "qingcheng.process"
    prefix, supported_fields, label = ("process", (33, 50, 51), "过程") if process else ("conversion", (31, 48, 49), "转化")
    manifests = [json.loads(row) for row in re.findall(r"^" + prefix + r"表快照清单：(\{[^\r\n]+\})$", log, re.M)]
    if not manifests or any(manifest != manifests[0] for manifest in manifests[1:]):
        raise ValueError("missing or inconsistent Qingcheng snapshot manifest")
    manifest = manifests[0]
    fields = manifest.get("field_count")
    if type(fields) is not int or fields not in supported_fields:
        raise ValueError("unreviewed Qingcheng snapshot field count")
    required = (
        f"目标字段校验通过：{fields}个字段",
        "写入前清空回读确认：0条",
        "新记录回读校验通过",
    )
    targets = re.findall(r"^目标多维表格校验通过：table_id=(\w+)\s*$", log, re.M)
    if (
        any(marker not in log for marker in required)
        or (process and targets != [target])
        or (targets and set(targets) != {target})
        or not re.search(r"^SUCCESS: 青橙项目部.*" + label + r"数据.*回读通过\s*$", log, re.M)
        or not re.search(r"exit_code:\s+0\s*\Z", log)
    ):
        raise ValueError("incomplete Qingcheng Base write/readback evidence")
    periods = manifest["periods"]
    total = manifest["row_count"]
    if (
        manifest.get("field_count") != fields
        or len(periods) != 2
        or type(total) is not int
        or total <= 0
        or sum(row["row_count"] for row in periods.values()) != total
        or any(
            not re.fullmatch(r"\d{8}期", name)
            or sum(row["channel_counts"].values()) != row["row_count"]
            or len(row["snapshots"]) != 1
            for name, row in periods.items()
        )
        or re.findall(r"^新记录创建完成：(\d+)条\s*$", log, re.M) != [str(total)]
        or re.findall(r"^最终回读校验通过：(\d+)条\s*$", log, re.M) != [str(total)]
    ):
        raise ValueError("Qingcheng snapshot and Base row counts disagree")
    return {"total": total, "periods": periods, "field_count": fields}


def _read_evidence(binding, args):
    reviewed_binding = _reviewed_market_binding(binding, args)
    reviewed_version = getattr(args, "channel_mapping_version", None)
    operator = SKILLS_ROOT / "usql-web-query-operator" / "scripts"
    if not operator.is_dir():
        operator = Path.home() / ".codex" / "skills" / "usql-web-query-operator" / "scripts"
    if not operator.is_dir():
        raise ValueError("installed Tiangong2 operator not found")
    sys.path.insert(0, str(operator))
    from _shared.browser import import_playwright
    from _shared.config import TIANGONG2_TASK_RUNTIME_DIR
    from tiangong2_task.cli import build_parser
    from tiangong2_task.client import Tiangong2ReadOnlyClient
    from tiangong2_task.operations import (
        Tiangong2OperationsReadOnlyClient,
        fetch_execution_log_bundle,
        list_execution_history_bundle,
    )
    from tiangong2_task.redaction import redact_text
    from tiangong2_task.scope import resolve_owned_task
    from tiangong2_task.session import open_authenticated_session

    scope = binding["upstream"]
    # Parse only to reuse the operator's authenticated read-only session options.
    session_args = build_parser().parse_args([
        "plan-task-publish", "--project-id", str(scope["project_id"]),
        "--folder", scope["folder"], "--menu-id", str(scope["menu_id"]),
        "--task-name", scope["task_name"],
    ])
    with import_playwright()() as playwright:
        session = open_authenticated_session(playwright, session_args)
        try:
            development = Tiangong2ReadOnlyClient(session.context.request)
            operations = Tiangong2OperationsReadOnlyClient(session.context.request)
            spec = resolve_owned_task(
                development, identity=session.identity, project_id=scope["project_id"],
                folder_name=scope["folder"], menu_id=scope["menu_id"], task_name=scope["task_name"],
            )
            if (
                session.identity.get("name") != scope["owner"]
                or any(getattr(spec, key) != scope[key] for key in ("task_id", "nezha_task_id"))
            ):
                raise ValueError("live task identity differs from registered producer")
            publication = _publication(development, spec.task_id, reviewed_version)
            if publication[0] != args.version_id:
                raise ValueError("reviewed version is not the current published version")
            _schedule(development, operations, spec, binding)
            bundle = fetch_execution_log_bundle(operations, task=spec, execution_id=args.execution_id)
            execution = bundle["execution"]
            period = _validate_execution(operations, spec, binding, execution, publication, args)
            evidence = _stage_evidence(
                bundle, reviewed_binding, scope, period, execution, redact_text, TIANGONG2_TASK_RUNTIME_DIR,
            )
            history = list_execution_history_bundle(operations, task=spec, limit=16)
            _require_latest(history, execution)
            _schedule(development, operations, spec, binding)
            if _publication(development, spec.task_id, reviewed_version) != publication:
                raise ValueError("publication changed during verification")
            evidence = {
                **evidence,
                "version_id": publication[0],
                "version_label": publication[1],
                "published_at": publication[2],
                "source_sha256": publication[3],
                "exec_file_id": args.exec_file_id,
                "execution_id": args.execution_id,
                "execution_period": period.isoformat(),
                "execution_start": _local_datetime(execution["startTime"]).isoformat(),
            }
            if reviewed_binding.get("task_key") == "market_consultant.leads":
                evidence["channel_mapping_version"] = reviewed_binding["channel_mapping_version"]
            receipt_file = getattr(args, "execution_receipt", None)
            if receipt_file is not None:
                evidence["controlled_execution_receipt"] = {
                    "path": str(Path(receipt_file).resolve()),
                    "sha256": _sha256(Path(receipt_file).read_bytes()),
                }
            return evidence
        finally:
            session.close()


def _prepare_evidence(binding, args):
    """Retry the entire read-only sample after a transient transport failure."""
    from playwright.sync_api import Error as PlaywrightError

    for delay in (0, 1, 3):
        if delay:
            time.sleep(delay)
        try:
            return _read_evidence(binding, args)
        except PlaywrightError as error:
            if not any(marker in str(error) for marker in ("ECONNRESET", "ETIMEDOUT", "Timeout")):
                raise ValueError("Tiangong2 read-only session request failed") from None
    raise ValueError("Tiangong2 read-only session unavailable after retry")


def _updated_binding(binding, evidence, args):
    reviewed_binding = _reviewed_market_binding(binding, args)
    if (getattr(args, "channel_mapping_version", None) is not None
            or (binding.get("task_key") == "market_consultant.leads" and "channel_mapping_version" in evidence)) and (
        evidence.get("channel_mapping_version") != reviewed_binding["channel_mapping_version"]
    ):
        raise ValueError("verified channel mapping evidence differs from the reviewed version")
    upstream = binding["upstream"]
    market = binding["domain"] == "market_consultant"
    version_key = "verified_version_id" if market else "version_id"
    hash_key = "verified_source_sha256" if market else "source_sha256"
    source = evidence["source_sha256"]
    if args.approve_source_sha256 and args.approve_source_sha256 != source:
        raise ValueError("approved source SHA-256 does not match published source")
    if source != upstream[hash_key] and args.approve_source_sha256 != source:
        raise ValueError("changed published source requires exact --approve-source-sha256")
    if _matches_registered_binding(binding, evidence):
        return None
    updated_scope = {
        **upstream, version_key: evidence["version_id"], hash_key: source,
        "exec_file_id": evidence["exec_file_id"],
    }
    if not market:
        updated_scope["published_version"] = evidence["version_label"]
        if "audit_field_count" in evidence:
            updated_scope["audit_field_count"] = evidence["audit_field_count"]
    return {
        **reviewed_binding, "upstream": updated_scope,
        "release_name": f"{upstream['task_name']}-{evidence['version_id']}",
        "bound_execution_id": evidence["execution_id"],
        "bound_execution_start": evidence["execution_start"],
        "release_review": {
            "reference": args.review_reference.strip(),
            "association": "explicitly_reviewed_mapping",
            "verified_at": datetime.now(timezone.utc).isoformat(),
            **evidence,
        },
    }


def _matches_registered_binding(binding, evidence):
    market = binding["domain"] == "market_consultant"
    version_key = "verified_version_id" if market else "version_id"
    hash_key = "verified_source_sha256" if market else "source_sha256"
    current = binding["upstream"]
    marker_matches = evidence.get("channel_mapping_version", binding.get("channel_mapping_version")) == binding.get("channel_mapping_version")
    fields_match = evidence.get("audit_field_count", current.get("audit_field_count")) == current.get("audit_field_count")
    return marker_matches and fields_match and (current[version_key], current["exec_file_id"], current[hash_key]) == (
        evidence["version_id"], evidence["exec_file_id"], evidence["source_sha256"]
    )


def _replace_binding(path, baseline, replacement):
    raw = (json.dumps(replacement, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", dir=path.parent, prefix=".producer-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        if path.read_bytes() != baseline:
            raise ValueError("registered producer changed during verification")
        os.replace(temporary, path)
        if path.read_bytes() != raw:
            raise ValueError("producer binding readback differs after replacement")
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _run(args):
    domain = args.task_key.split(".", 1)[0]
    path = binding_path(args.task_key, expected_domain=domain)
    binding = read_binding_document(args.task_key, expected_domain=domain)
    if args.command == "verify":
        evidence = _prepare_evidence(binding, args)
        hash_key = "verified_source_sha256" if domain == "market_consultant" else "source_sha256"
        registered = _matches_registered_binding(binding, evidence)
        return {
            "status": "verified", "changed": False,
            "registry_matches_observed": registered,
            "association": "registered_binding" if registered else "review_required",
            "source_approval_required": evidence["source_sha256"] != binding["upstream"][hash_key],
            **evidence,
        }
    lock = Path.home() / ".codex" / "runtime" / "data-push-producer-maintenance" / args.task_key
    with runner_lock(lock) as acquired:
        if not acquired:
            raise ValueError("another producer adoption is running")
        baseline = path.read_bytes()
        binding = read_binding_document(args.task_key, expected_domain=domain)
        if json.loads(baseline.decode("utf-8-sig")) != binding:
            raise ValueError("registered producer changed before verification")
        evidence = _prepare_evidence(binding, args)
        replacement = _updated_binding(binding, evidence, args)
        if replacement is None:
            return {
                "status": "already_bound", "changed": False, "registry_matches_observed": True,
                "association": "registered_binding", **evidence,
            }
        _replace_binding(path, baseline, replacement)
        if read_binding_document(args.task_key, expected_domain=domain) != replacement:
            raise ValueError("producer binding did not pass registry readback")
        return {
            "status": "adopted", "changed": True, "registry_matches_observed": True,
            "association": "explicitly_reviewed_mapping", **evidence,
        }


def main():
    args = _arguments()
    try:
        report = _run(args)
    except Exception as exc:
        # Avoid serializing API replies, source, or stage log excerpts on failures.
        message = str(exc) if type(exc) is ValueError and not isinstance(exc, json.JSONDecodeError) else type(exc).__name__
        print(json.dumps({"status": "blocked", "task_key": args.task_key, "reason": message}))
        return 1
    print(json.dumps({"task_key": args.task_key, "remote_mutations": 0, **report}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
