"""CLI for governed Tiangong2 task exploration, execution logs, and publication."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from _shared.browser import import_playwright
from _shared.config import (
    DEFAULT_BROWSER_CHANNEL,
    DEFAULT_ENV_FILE,
    DEFAULT_TIANGONG2_TASK_STATE,
    TIANGONG2_TASK_RUNTIME_DIR,
)
from _shared.errors import UsageError

from .artifacts import validate_artifact_root, write_artifact_bundle
from .client import Tiangong2ReadOnlyClient
from .editing import (
    RECEIPT_SCHEMA_VERSION as QUERY_UPDATE_RECEIPT_SCHEMA_VERSION,
    Tiangong2QueryUpdateClient,
    authorize_query_update,
    build_query_update_plan,
    load_query_update_plan,
    prepare_query_update,
    task_query_update_lock,
    verify_query_update_readback,
)
from .execution import (
    RECEIPT_SCHEMA_VERSION as EXECUTION_RECEIPT_SCHEMA_VERSION,
    Tiangong2ExecuteOnceClient,
    authorize_execution,
    build_execution_plan,
    load_execution_plan,
    task_execution_lock,
    validate_pre_execution_drift,
    wait_for_new_execution,
)
from .explorer import Tiangong2TaskExplorer
from .maintenance import (
    PATCH_RECEIPT_SCHEMA_VERSION,
    Tiangong2PythonPatchClient,
    activate_maintenance_session,
    authorize_phase_with_maintenance_session,
    authorize_python_patch,
    build_maintenance_session_plan,
    build_python_patch_plan,
    load_maintenance_session,
    load_maintenance_session_plan,
    load_python_patch_plan,
    prepare_python_patch,
    validate_live_maintenance_session_source,
    validate_maintenance_session_activation,
    verify_python_patch_readback,
)
from .operations import (
    Tiangong2OperationsReadOnlyClient,
    execution_status_label,
    fetch_execution_log_bundle,
    list_execution_history_bundle,
    write_execution_history_bundle,
    write_execution_log_bundle,
)
from .publishing import (
    RECEIPT_SCHEMA_VERSION,
    Tiangong2PublishClient,
    authorize_publish,
    build_publish_plan,
    load_publish_plan,
    task_publish_lock,
    validate_pre_publish_drift,
    verify_publish_readback,
    write_hashed_json,
)
from .scope import resolve_owned_task
from .session import open_authenticated_session
from .submission import (
    RECEIPT_SCHEMA_VERSION as SUBMIT_RECEIPT_SCHEMA_VERSION,
    Tiangong2SubmitClient,
    authorize_submit,
    build_submit_plan,
    load_submit_plan,
    task_submit_lock,
    validate_pre_submit_drift,
    verify_submit_readback,
)


def _add_browser_arguments(command: argparse.ArgumentParser) -> None:
    command.add_argument("--headed", action="store_true", help="Show the isolated Tiangong2 browser window.")
    command.add_argument("--state-path", type=Path, default=DEFAULT_TIANGONG2_TASK_STATE)
    command.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    command.add_argument("--browser-channel", default=DEFAULT_BROWSER_CHANNEL)
    command.add_argument("--executable-path", default=None)


def _add_phase_authorization_arguments(
    command: argparse.ArgumentParser,
    *,
    confirmation_flag: str,
    confirmation_dest: str,
) -> None:
    group = command.add_mutually_exclusive_group(required=True)
    group.add_argument(confirmation_flag, dest=confirmation_dest, action="store_true")
    group.add_argument(
        "--maintenance-session-file",
        type=Path,
        help="Active exact-task maintenance session created from one user confirmation.",
    )
    command.add_argument(
        "--expected-maintenance-session-sha256",
        default=None,
        help="Exact active maintenance-session SHA-256; required with --maintenance-session-file.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_projects = subparsers.add_parser(
        "list-projects",
        help="Verify the scoped Tiangong2 identity and list accessible projects read-only.",
    )
    _add_browser_arguments(list_projects)
    list_projects.set_defaults(func=cmd_list_projects)

    explore = subparsers.add_parser(
        "explore",
        help="Recursively snapshot exact data-development folders without running or changing tasks.",
    )
    explore.add_argument("--project-id", type=int, required=True, help="Exact accessible Tiangong2 project id.")
    explore.add_argument(
        "--folder",
        action="append",
        required=True,
        help="Exact folder name directly under 数据开发. Repeat for multiple folders.",
    )
    explore.add_argument(
        "--include-version-code",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Read and save a redacted code snapshot for every listed version; metadata is always included.",
    )
    explore.add_argument(
        "--artifacts-dir",
        type=Path,
        default=TIANGONG2_TASK_RUNTIME_DIR / "explorations",
        help="Runtime root for timestamped artifacts; paths outside the isolated runtime are rejected.",
    )
    _add_browser_arguments(explore)
    explore.set_defaults(func=cmd_explore)

    execution_log = subparsers.add_parser(
        "fetch-execution-log",
        help="Read one exact owned Tiangong2 execution and all stage logs into redacted runtime artifacts.",
    )
    _add_exact_task_arguments(execution_log)
    execution_log.add_argument("--exec-id", type=int, required=True, help="Exact Nezha task execution id.")
    execution_log.add_argument(
        "--artifacts-dir",
        type=Path,
        default=TIANGONG2_TASK_RUNTIME_DIR / "execution-logs",
        help="Isolated runtime root for redacted execution-log artifacts.",
    )
    _add_browser_arguments(execution_log)
    execution_log.set_defaults(func=cmd_fetch_execution_log)

    execution_history = subparsers.add_parser(
        "list-execution-history",
        help="List recent execution attempts for one exact owned Tiangong2 task into redacted runtime artifacts.",
    )
    _add_exact_task_arguments(execution_history)
    execution_history.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum recent execution attempts to return (1-100).",
    )
    execution_history.add_argument(
        "--artifacts-dir",
        type=Path,
        default=TIANGONG2_TASK_RUNTIME_DIR / "execution-history",
        help="Isolated runtime root for redacted execution-history artifacts.",
    )
    _add_browser_arguments(execution_history)
    execution_history.set_defaults(func=cmd_list_execution_history)

    plan_maintenance = subparsers.add_parser(
        "plan-task-maintenance-session",
        help=(
            "Plan one time-bounded authorization session for exact-task save, submit, "
            "publish, and bounded debug execution."
        ),
    )
    _add_exact_task_arguments(plan_maintenance)
    plan_maintenance.add_argument(
        "--reason",
        required=True,
        help="Reviewed maintenance objective; max 200 supported characters.",
    )
    plan_maintenance.add_argument("--duration-minutes", type=int, default=180)
    plan_maintenance.add_argument("--max-executions", type=int, default=3)
    plan_maintenance.add_argument(
        "--artifacts-dir",
        type=Path,
        default=TIANGONG2_TASK_RUNTIME_DIR / "maintenance-session-plans",
    )
    plan_maintenance.add_argument("--output-file", type=Path, default=None)
    _add_browser_arguments(plan_maintenance)
    plan_maintenance.set_defaults(func=cmd_plan_task_maintenance_session)

    authorize_maintenance = subparsers.add_parser(
        "authorize-task-maintenance-session",
        help=(
            "Activate one reviewed exact-task maintenance session; this writes only a local "
            "authorization artifact and performs no remote mutation."
        ),
    )
    authorize_maintenance.add_argument("--plan-file", type=Path, required=True)
    authorize_maintenance.add_argument("--expected-plan-sha256", required=True)
    authorize_maintenance.add_argument(
        "--confirm-maintenance",
        action="store_true",
        required=True,
    )
    authorize_maintenance.add_argument(
        "--artifacts-dir",
        type=Path,
        default=TIANGONG2_TASK_RUNTIME_DIR / "maintenance-sessions",
    )
    authorize_maintenance.add_argument("--output-file", type=Path, default=None)
    _add_browser_arguments(authorize_maintenance)
    authorize_maintenance.set_defaults(func=cmd_authorize_task_maintenance_session)

    plan_python_patch = subparsers.add_parser(
        "plan-task-python-patch",
        help=(
            "Plan exact non-secret Python text replacements for one owned task while preserving "
            "query_sql, the company default block, and resource binding."
        ),
    )
    _add_exact_task_arguments(plan_python_patch)
    plan_python_patch.add_argument("--patch-file", type=Path, required=True)
    plan_python_patch.add_argument(
        "--artifacts-dir",
        type=Path,
        default=TIANGONG2_TASK_RUNTIME_DIR / "python-patch-plans",
    )
    plan_python_patch.add_argument("--output-file", type=Path, default=None)
    _add_browser_arguments(plan_python_patch)
    plan_python_patch.set_defaults(func=cmd_plan_task_python_patch)

    apply_python_patch = subparsers.add_parser(
        "apply-task-python-patch",
        help=(
            "Save one exact reviewed non-secret Python patch and verify full protected-source readback."
        ),
    )
    apply_python_patch.add_argument("--plan-file", type=Path, required=True)
    apply_python_patch.add_argument("--expected-plan-sha256", required=True)
    _add_phase_authorization_arguments(
        apply_python_patch,
        confirmation_flag="--confirm-save-python-patch",
        confirmation_dest="confirm_save_python_patch",
    )
    apply_python_patch.add_argument(
        "--artifacts-dir",
        type=Path,
        default=TIANGONG2_TASK_RUNTIME_DIR / "python-patch-receipts",
    )
    apply_python_patch.add_argument("--output-file", type=Path, default=None)
    _add_browser_arguments(apply_python_patch)
    apply_python_patch.set_defaults(func=cmd_apply_task_python_patch)

    plan_query_update = subparsers.add_parser(
        "plan-task-query-update",
        help=(
            "Plan a quality-gated query_sql-only update for one exact owned Python task "
            "without remote writes."
        ),
    )
    _add_exact_task_arguments(plan_query_update)
    plan_query_update.add_argument("--replacement-sql-file", type=Path, required=True)
    plan_query_update.add_argument(
        "--sql-review-file",
        type=Path,
        required=True,
        help=(
            "Hash-bound accuracy, output-contract, simplification, and performance review JSON."
        ),
    )
    plan_query_update.add_argument(
        "--artifacts-dir",
        type=Path,
        default=TIANGONG2_TASK_RUNTIME_DIR / "query-update-plans",
    )
    plan_query_update.add_argument("--output-file", type=Path, default=None)
    _add_browser_arguments(plan_query_update)
    plan_query_update.set_defaults(func=cmd_plan_task_query_update)

    apply_query_update = subparsers.add_parser(
        "apply-task-query-update",
        help="Save one reviewed query_sql-only update and verify exact source/default-block readback.",
    )
    apply_query_update.add_argument("--plan-file", type=Path, required=True)
    apply_query_update.add_argument("--expected-plan-sha256", required=True)
    _add_phase_authorization_arguments(
        apply_query_update,
        confirmation_flag="--confirm-save-query",
        confirmation_dest="confirm_save_query",
    )
    apply_query_update.add_argument(
        "--artifacts-dir",
        type=Path,
        default=TIANGONG2_TASK_RUNTIME_DIR / "query-update-receipts",
    )
    apply_query_update.add_argument("--output-file", type=Path, default=None)
    _add_browser_arguments(apply_query_update)
    apply_query_update.set_defaults(func=cmd_apply_task_query_update)

    plan_submit = subparsers.add_parser(
        "plan-task-submit",
        help="Build a read-only, note-bound plan for submitting one exact saved owned task.",
    )
    _add_exact_task_arguments(plan_submit)
    plan_submit.add_argument(
        "--note",
        required=True,
        help="Required version note: Chinese, letters, digits, and underscores only; max 200 characters.",
    )
    plan_submit.add_argument(
        "--artifacts-dir",
        type=Path,
        default=TIANGONG2_TASK_RUNTIME_DIR / "submit-plans",
    )
    plan_submit.add_argument("--output-file", type=Path, default=None)
    _add_browser_arguments(plan_submit)
    plan_submit.set_defaults(func=cmd_plan_task_submit)

    submit = subparsers.add_parser(
        "submit-task",
        help="Submit one exact reviewed saved task with its hash-bound version note.",
    )
    submit.add_argument("--plan-file", type=Path, required=True)
    submit.add_argument("--expected-plan-sha256", required=True)
    _add_phase_authorization_arguments(
        submit,
        confirmation_flag="--confirm-submit",
        confirmation_dest="confirm_submit",
    )
    submit.add_argument(
        "--artifacts-dir",
        type=Path,
        default=TIANGONG2_TASK_RUNTIME_DIR / "submit-receipts",
    )
    submit.add_argument("--output-file", type=Path, default=None)
    _add_browser_arguments(submit)
    submit.set_defaults(func=cmd_submit_task)

    plan_publish = subparsers.add_parser(
        "plan-task-publish",
        help="Build a read-only, identity-scoped, hash-bound plan for publishing one saved task.",
    )
    _add_exact_task_arguments(plan_publish)
    plan_publish.add_argument(
        "--artifacts-dir",
        type=Path,
        default=TIANGONG2_TASK_RUNTIME_DIR / "publish-plans",
    )
    plan_publish.add_argument("--output-file", type=Path, default=None)
    _add_browser_arguments(plan_publish)
    plan_publish.set_defaults(func=cmd_plan_task_publish)

    publish = subparsers.add_parser(
        "publish-task",
        help="Publish one exact reviewed Tiangong2 task plan; never saves, edits, submits, or executes code.",
    )
    publish.add_argument("--plan-file", type=Path, required=True)
    publish.add_argument("--expected-plan-sha256", required=True)
    _add_phase_authorization_arguments(
        publish,
        confirmation_flag="--confirm-publish",
        confirmation_dest="confirm_publish",
    )
    publish.add_argument(
        "--artifacts-dir",
        type=Path,
        default=TIANGONG2_TASK_RUNTIME_DIR / "publish-receipts",
    )
    publish.add_argument("--output-file", type=Path, default=None)
    _add_browser_arguments(publish)
    publish.set_defaults(func=cmd_publish_task)

    plan_execution = subparsers.add_parser(
        "plan-task-execution",
        help="Plan one downstream-disabled execution of an exact owned and published task.",
    )
    _add_exact_task_arguments(plan_execution)
    plan_execution.add_argument(
        "--period-time",
        default=None,
        help="Execution data period in YYYY-MM-DD HH:mm:ss; defaults to current Asia/Shanghai minute.",
    )
    plan_execution.add_argument(
        "--artifacts-dir",
        type=Path,
        default=TIANGONG2_TASK_RUNTIME_DIR / "execution-plans",
    )
    plan_execution.add_argument("--output-file", type=Path, default=None)
    _add_browser_arguments(plan_execution)
    plan_execution.set_defaults(func=cmd_plan_task_execution)

    execute_once = subparsers.add_parser(
        "execute-task-once",
        help="Execute one exact reviewed task plan once with downstream triggering disabled.",
    )
    execute_once.add_argument("--plan-file", type=Path, required=True)
    execute_once.add_argument("--expected-plan-sha256", required=True)
    _add_phase_authorization_arguments(
        execute_once,
        confirmation_flag="--confirm-execute",
        confirmation_dest="confirm_execute",
    )
    execute_once.add_argument(
        "--artifacts-dir",
        type=Path,
        default=TIANGONG2_TASK_RUNTIME_DIR / "execution-receipts",
    )
    execute_once.add_argument("--output-file", type=Path, default=None)
    _add_browser_arguments(execute_once)
    execute_once.set_defaults(func=cmd_execute_task_once)
    return parser


def _add_exact_task_arguments(command: argparse.ArgumentParser) -> None:
    command.add_argument("--project-id", type=int, required=True, help="Exact accessible Tiangong2 project id.")
    command.add_argument(
        "--folder",
        required=True,
        help="Exact direct child folder under 数据开发; task scope cannot escape it.",
    )
    command.add_argument("--menu-id", type=int, required=True, help="Exact data-development menu id.")
    command.add_argument("--task-name", required=True, help="Exact task name for identity readback.")


def _validate_runtime_output(path: Path) -> None:
    validate_artifact_root(path.parent)


def _default_hashed_path(root: Path, prefix: str, identifier: int, sha256: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return root / f"{prefix}_{identifier}_{stamp}_{sha256[:12]}.json"


def _maintenance_phase_authorization(
    args: argparse.Namespace,
    *,
    plan: dict[str, Any],
    operation: str,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    session_file = getattr(args, "maintenance_session_file", None)
    expected_sha256 = getattr(args, "expected_maintenance_session_sha256", None)
    if session_file is None:
        if expected_sha256:
            raise UsageError(
                "--expected-maintenance-session-sha256 requires --maintenance-session-file"
            )
        return None, None
    if not expected_sha256:
        raise UsageError(
            "--maintenance-session-file requires --expected-maintenance-session-sha256"
        )
    _validate_runtime_output(session_file)
    session = load_maintenance_session(
        session_file,
        expected_session_sha256=str(expected_sha256),
    )
    context = authorize_phase_with_maintenance_session(
        session,
        phase_plan=plan,
        operation=operation,
    )
    return session, context


def _phase_authorization_receipt(
    context: dict[str, Any] | None,
) -> dict[str, Any]:
    if context is None:
        return {"authorization_mode": "exact_phase_confirmation"}
    return dict(context)


def cmd_list_projects(args: argparse.Namespace) -> int:
    sync_playwright = import_playwright()
    with sync_playwright() as playwright:
        session = open_authenticated_session(playwright, args)
        try:
            client = Tiangong2ReadOnlyClient(session.context.request)
            projects = client.list_projects()
            payload = {
                "ok": True,
                "read_only": True,
                "identity": {
                    key: session.identity.get(key)
                    for key in ("id", "name", "displayName", "department")
                    if session.identity.get(key) is not None
                },
                "login_performed": session.login_performed,
                "projects": projects,
                "used_endpoints": sorted(client.used_endpoints),
            }
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        finally:
            session.close()
    return 0


def cmd_explore(args: argparse.Namespace) -> int:
    validate_artifact_root(args.artifacts_dir)
    sync_playwright = import_playwright()
    with sync_playwright() as playwright:
        session = open_authenticated_session(playwright, args)
        try:
            client = Tiangong2ReadOnlyClient(session.context.request)
            explorer = Tiangong2TaskExplorer(client)
            snapshot = explorer.explore(
                identity=session.identity,
                login_performed=session.login_performed,
                project_id=args.project_id,
                folder_names=args.folder,
                include_version_code=args.include_version_code,
            )
            run_dir = write_artifact_bundle(snapshot, args.artifacts_dir)
            print(
                json.dumps(
                    {
                        "ok": True,
                        "read_only": True,
                        "remote_mutations": 0,
                        "project_id": args.project_id,
                        "folders": args.folder,
                        "task_count": len(snapshot.tasks),
                        "artifact_dir": str(run_dir),
                        "login_performed": session.login_performed,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        finally:
            session.close()
    return 0


def cmd_fetch_execution_log(args: argparse.Namespace) -> int:
    validate_artifact_root(args.artifacts_dir)
    sync_playwright = import_playwright()
    with sync_playwright() as playwright:
        session = open_authenticated_session(playwright, args)
        try:
            task_client = Tiangong2ReadOnlyClient(session.context.request)
            task = resolve_owned_task(
                task_client,
                identity=session.identity,
                project_id=args.project_id,
                folder_name=args.folder,
                menu_id=args.menu_id,
                task_name=args.task_name,
            )
            operations_client = Tiangong2OperationsReadOnlyClient(session.context.request)
            bundle = fetch_execution_log_bundle(
                operations_client,
                task=task,
                execution_id=args.exec_id,
            )
            run_dir = write_execution_log_bundle(
                task=task,
                identity=session.identity,
                execution_id=args.exec_id,
                bundle=bundle,
                used_endpoints=task_client.used_endpoints | operations_client.used_endpoints,
                artifact_root=args.artifacts_dir,
            )
            execution_payload = json.loads((run_dir / "execution.json").read_text(encoding="utf-8"))
            print(
                json.dumps(
                    {
                        "ok": True,
                        "read_only": True,
                        "remote_mutations": 0,
                        "execution_id": args.exec_id,
                        "status": execution_status_label(
                            {
                                **execution_payload["execution"],
                                "statusDesc": (
                                    execution_payload["execution"].get("statusDesc")
                                    or execution_payload["execution_detail"].get("statusDesc")
                                ),
                            }
                        ),
                        "diagnostic": execution_payload["diagnostic"],
                        "artifact_dir": str(run_dir),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        finally:
            session.close()
    return 0


def cmd_list_execution_history(args: argparse.Namespace) -> int:
    validate_artifact_root(args.artifacts_dir)
    sync_playwright = import_playwright()
    with sync_playwright() as playwright:
        session = open_authenticated_session(playwright, args)
        try:
            task_client = Tiangong2ReadOnlyClient(session.context.request)
            task = resolve_owned_task(
                task_client,
                identity=session.identity,
                project_id=args.project_id,
                folder_name=args.folder,
                menu_id=args.menu_id,
                task_name=args.task_name,
            )
            operations_client = Tiangong2OperationsReadOnlyClient(session.context.request)
            bundle = list_execution_history_bundle(
                operations_client,
                task=task,
                limit=args.limit,
            )
            run_dir = write_execution_history_bundle(
                task=task,
                identity=session.identity,
                limit=args.limit,
                bundle=bundle,
                used_endpoints=task_client.used_endpoints | operations_client.used_endpoints,
                artifact_root=args.artifacts_dir,
            )
            statuses: dict[str, int] = {}
            for row in bundle["executions"]:
                status = execution_status_label(row)
                statuses[status] = statuses.get(status, 0) + 1
            print(
                json.dumps(
                    {
                        "ok": True,
                        "read_only": True,
                        "remote_mutations": 0,
                        "execution_count": len(bundle["executions"]),
                        "status_counts": statuses,
                        "latest_execution_id": (
                            int(bundle["executions"][0].get("id") or 0)
                            if bundle["executions"]
                            else None
                        ),
                        "artifact_dir": str(run_dir),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        finally:
            session.close()
    return 0


def cmd_plan_task_maintenance_session(args: argparse.Namespace) -> int:
    validate_artifact_root(args.artifacts_dir)
    if args.output_file is not None:
        _validate_runtime_output(args.output_file)
    sync_playwright = import_playwright()
    with sync_playwright() as playwright:
        session = open_authenticated_session(playwright, args)
        try:
            reader = Tiangong2ReadOnlyClient(session.context.request)
            task = resolve_owned_task(
                reader,
                identity=session.identity,
                project_id=args.project_id,
                folder_name=args.folder,
                menu_id=args.menu_id,
                task_name=args.task_name,
            )
            operations = Tiangong2OperationsReadOnlyClient(session.context.request)
            history = list_execution_history_bundle(operations, task=task, limit=100)
            execution_ids = [
                int(row.get("id") or 0)
                for row in history.get("executions") or []
                if int(row.get("id") or 0) > 0
            ]
            plan = build_maintenance_session_plan(
                reader,
                task=task,
                identity=session.identity,
                reason=args.reason,
                duration_minutes=args.duration_minutes,
                max_executions=args.max_executions,
                baseline_execution_ids=execution_ids,
            )
            plan_path = args.output_file or _default_hashed_path(
                args.artifacts_dir,
                "task_maintenance_session_plan",
                task.menu_id,
                plan["plan_sha256"],
            )
            _validate_runtime_output(plan_path)
            finalized = write_hashed_json(plan_path, plan, hash_field="plan_sha256")
            print(
                json.dumps(
                    {
                        "ok": True,
                        "read_only": True,
                        "remote_mutations": 0,
                        "status": finalized["status"],
                        "plan_sha256": finalized["plan_sha256"],
                        "plan_file": str(plan_path.resolve()),
                        "expires_at": finalized["expires_at"],
                        "max_executions": finalized["authorization"]["max_executions"],
                        "allowed_operations": finalized["authorization"]["allowed_operations"],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        finally:
            session.close()
    return 0


def cmd_authorize_task_maintenance_session(args: argparse.Namespace) -> int:
    _validate_runtime_output(args.plan_file)
    validate_artifact_root(args.artifacts_dir)
    plan = load_maintenance_session_plan(args.plan_file)
    activated = activate_maintenance_session(
        plan,
        expected_plan_sha256=args.expected_plan_sha256,
        confirm_maintenance=args.confirm_maintenance,
    )
    scope = plan["scope"]
    session_path = args.output_file or _default_hashed_path(
        args.artifacts_dir,
        "task_maintenance_session",
        int(scope["menu_id"]),
        activated["session_sha256"],
    )
    _validate_runtime_output(session_path)
    sync_playwright = import_playwright()
    with sync_playwright() as playwright:
        browser_session = open_authenticated_session(playwright, args)
        try:
            if str(browser_session.identity.get("name") or "") != str(
                plan["identity"].get("name") or ""
            ):
                raise UsageError(
                    "Authenticated Tiangong2 identity changed after maintenance-session planning"
                )
            reader = Tiangong2ReadOnlyClient(browser_session.context.request)
            task = resolve_owned_task(
                reader,
                identity=browser_session.identity,
                project_id=int(scope["project_id"]),
                folder_name=str(scope["folder"]),
                menu_id=int(scope["menu_id"]),
                task_name=str(scope["task_name"]),
            )
            operations = Tiangong2OperationsReadOnlyClient(browser_session.context.request)
            history = list_execution_history_bundle(operations, task=task, limit=100)
            execution_ids = [
                int(row.get("id") or 0)
                for row in history.get("executions") or []
                if int(row.get("id") or 0) > 0
            ]
            readback = validate_maintenance_session_activation(
                reader,
                task=task,
                plan=plan,
                current_execution_ids=execution_ids,
            )
            finalized = write_hashed_json(
                session_path,
                activated,
                hash_field="session_sha256",
            )
            print(
                json.dumps(
                    {
                        "ok": True,
                        "read_only_remote": True,
                        "remote_mutations": 0,
                        "local_authorization_artifact_created": True,
                        "status": finalized["status"],
                        "session_sha256": finalized["session_sha256"],
                        "session_file": str(session_path.resolve()),
                        "expires_at": finalized["expires_at"],
                        "scope": finalized["scope"],
                        "activation_readback": readback,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        finally:
            browser_session.close()
    return 0


def cmd_plan_task_python_patch(args: argparse.Namespace) -> int:
    validate_artifact_root(args.artifacts_dir)
    _validate_runtime_output(args.patch_file)
    if args.output_file is not None:
        _validate_runtime_output(args.output_file)
    sync_playwright = import_playwright()
    with sync_playwright() as playwright:
        session = open_authenticated_session(playwright, args)
        try:
            reader = Tiangong2ReadOnlyClient(session.context.request)
            task = resolve_owned_task(
                reader,
                identity=session.identity,
                project_id=args.project_id,
                folder_name=args.folder,
                menu_id=args.menu_id,
                task_name=args.task_name,
            )
            plan = build_python_patch_plan(
                reader,
                task=task,
                identity=session.identity,
                patch_file=args.patch_file,
            )
            plan_path = args.output_file or _default_hashed_path(
                args.artifacts_dir,
                "task_python_patch_plan",
                task.menu_id,
                plan["plan_sha256"],
            )
            _validate_runtime_output(plan_path)
            finalized = write_hashed_json(plan_path, plan, hash_field="plan_sha256")
            print(
                json.dumps(
                    {
                        "ok": True,
                        "read_only": True,
                        "remote_mutations": 0,
                        "status": finalized["status"],
                        "plan_sha256": finalized["plan_sha256"],
                        "plan_file": str(plan_path.resolve()),
                        "replacement_count": finalized["patch"]["replacement_count"],
                        "current_source_sha256": finalized["baseline"][
                            "current_source_sha256"
                        ],
                        "projected_source_sha256": finalized["baseline"][
                            "projected_source_sha256"
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        finally:
            session.close()
    return 0


def cmd_apply_task_python_patch(args: argparse.Namespace) -> int:
    _validate_runtime_output(args.plan_file)
    validate_artifact_root(args.artifacts_dir)
    plan = load_python_patch_plan(args.plan_file)
    maintenance_session, maintenance_context = _maintenance_phase_authorization(
        args,
        plan=plan,
        operation="python_patch_save",
    )
    authorization = authorize_python_patch(
        plan,
        expected_plan_sha256=args.expected_plan_sha256,
        confirmed=bool(args.confirm_save_python_patch or maintenance_context),
    )
    scope = plan["scope"]
    receipt_path = args.output_file or _default_hashed_path(
        args.artifacts_dir,
        "task_python_patch_receipt",
        int(scope["menu_id"]),
        plan["plan_sha256"],
    )
    _validate_runtime_output(receipt_path)
    receipt = {
        "schema_version": PATCH_RECEIPT_SCHEMA_VERSION,
        "operation": plan["operation"],
        "status": "running",
        "ok": False,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "plan_file": str(args.plan_file.resolve()),
        "plan_sha256": plan["plan_sha256"],
        "scope": scope,
        "authorization": _phase_authorization_receipt(maintenance_context),
        "save_request_sent": False,
        "remote_mutation_confirmed": False,
        "manual_attention_required": False,
        "submit_requested": False,
        "publish_requested": False,
        "task_execution_requested": False,
    }
    sync_playwright = import_playwright()
    writer = None
    browser_session = None
    try:
        with sync_playwright() as playwright:
            browser_session = open_authenticated_session(playwright, args)
            try:
                if str(browser_session.identity.get("name") or "") != str(
                    plan["identity"].get("name") or ""
                ):
                    raise UsageError(
                        "Authenticated Tiangong2 identity changed after Python-patch planning"
                    )
                reader = Tiangong2ReadOnlyClient(browser_session.context.request)
                task = resolve_owned_task(
                    reader,
                    identity=browser_session.identity,
                    project_id=int(scope["project_id"]),
                    folder_name=str(scope["folder"]),
                    menu_id=int(scope["menu_id"]),
                    task_name=str(scope["task_name"]),
                )
                if maintenance_session is not None:
                    receipt["maintenance_session_live_readback"] = (
                        validate_live_maintenance_session_source(
                            reader,
                            task=task,
                            session=maintenance_session,
                        )
                    )
                with task_query_update_lock(task.menu_id):
                    projected, observed = prepare_python_patch(
                        reader,
                        task=task,
                        plan=plan,
                    )
                    writer = Tiangong2PythonPatchClient(
                        browser_session.context.request,
                        authorization=authorization,
                    )
                    save_response = writer.save_python(
                        task_id=task.task_id,
                        source=projected,
                        resource_id=int(plan["baseline"]["normalized_resource_id"]),
                    )
                    receipt["save_request_sent"] = True
                    receipt["save_response"] = save_response
                    receipt["pre_save_readback"] = observed
                    receipt["readback"] = verify_python_patch_readback(
                        reader,
                        task=task,
                        plan=plan,
                    )
                receipt.update(
                    {
                        "ok": True,
                        "status": "success",
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                        "remote_mutation_confirmed": True,
                        "fully_verified": True,
                    }
                )
                finalized = write_hashed_json(receipt_path, receipt, hash_field="receipt_sha256")
                print(
                    json.dumps(
                        {**finalized, "receipt_file": str(receipt_path.resolve())},
                        ensure_ascii=False,
                        indent=2,
                    )
                )
                return 0
            finally:
                browser_session.close()
                browser_session = None
    except Exception as exc:
        request_sent = bool(writer is not None and writer.write_count > 0)
        receipt.update(
            {
                "ok": False,
                "status": "failed",
                "failed_at": datetime.now(timezone.utc).isoformat(),
                "error": str(exc),
                "save_request_sent": request_sent,
                "remote_mutation_confirmed": False,
                "manual_attention_required": request_sent,
                "fully_verified": False,
            }
        )
        write_hashed_json(receipt_path, receipt, hash_field="receipt_sha256")
        if isinstance(exc, UsageError):
            raise
        raise UsageError(f"Tiangong2 task Python patch failed: {exc}") from exc
    finally:
        if browser_session is not None:
            browser_session.close()


def cmd_plan_task_query_update(args: argparse.Namespace) -> int:
    validate_artifact_root(args.artifacts_dir)
    if args.output_file is not None:
        _validate_runtime_output(args.output_file)
    sync_playwright = import_playwright()
    with sync_playwright() as playwright:
        session = open_authenticated_session(playwright, args)
        try:
            client = Tiangong2ReadOnlyClient(session.context.request)
            task = resolve_owned_task(
                client,
                identity=session.identity,
                project_id=args.project_id,
                folder_name=args.folder,
                menu_id=args.menu_id,
                task_name=args.task_name,
            )
            plan = build_query_update_plan(
                client,
                task=task,
                identity=session.identity,
                replacement_sql_file=args.replacement_sql_file,
                sql_review_file=args.sql_review_file,
            )
            plan_path = args.output_file or _default_hashed_path(
                args.artifacts_dir,
                "task_query_update_plan",
                task.menu_id,
                plan["plan_sha256"],
            )
            _validate_runtime_output(plan_path)
            finalized = write_hashed_json(plan_path, plan, hash_field="plan_sha256")
            print(
                json.dumps(
                    {
                        "ok": finalized["status"] == "ready",
                        "read_only": True,
                        "remote_mutations": 0,
                        "status": finalized["status"],
                        "plan_sha256": finalized["plan_sha256"],
                        "plan_file": str(plan_path.resolve()),
                        "current_source_sha256": finalized["baseline"][
                            "current_source_sha256"
                        ],
                        "projected_source_sha256": finalized["baseline"][
                            "projected_source_sha256"
                        ],
                        "company_default_block_sha256": finalized["baseline"][
                            "company_default_block_sha256"
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        finally:
            session.close()
    return 0


def cmd_apply_task_query_update(args: argparse.Namespace) -> int:
    _validate_runtime_output(args.plan_file)
    validate_artifact_root(args.artifacts_dir)
    plan = load_query_update_plan(args.plan_file)
    maintenance_session, maintenance_context = _maintenance_phase_authorization(
        args,
        plan=plan,
        operation="query_sql_save",
    )
    authorization = authorize_query_update(
        plan,
        expected_plan_sha256=args.expected_plan_sha256,
        confirm_save_query=bool(args.confirm_save_query or maintenance_context),
    )
    scope = plan["scope"]
    receipt_path = args.output_file or _default_hashed_path(
        args.artifacts_dir,
        "task_query_update_receipt",
        int(scope["menu_id"]),
        plan["plan_sha256"],
    )
    _validate_runtime_output(receipt_path)
    receipt = {
        "schema_version": QUERY_UPDATE_RECEIPT_SCHEMA_VERSION,
        "operation": plan["operation"],
        "status": "running",
        "ok": False,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "plan_file": str(args.plan_file.resolve()),
        "plan_sha256": plan["plan_sha256"],
        "scope": scope,
        "authorization": _phase_authorization_receipt(maintenance_context),
        "save_request_sent": False,
        "remote_mutation_confirmed": False,
        "manual_attention_required": False,
        "publish_requested": False,
        "task_execution_requested": False,
    }
    sync_playwright = import_playwright()
    writer = None
    session = None
    try:
        with sync_playwright() as playwright:
            session = open_authenticated_session(playwright, args)
            try:
                if str(session.identity.get("name") or "") != str(
                    plan["identity"].get("name") or ""
                ):
                    raise UsageError("Authenticated Tiangong2 identity changed after update planning")
                reader = Tiangong2ReadOnlyClient(session.context.request)
                task = resolve_owned_task(
                    reader,
                    identity=session.identity,
                    project_id=int(scope["project_id"]),
                    folder_name=str(scope["folder"]),
                    menu_id=int(scope["menu_id"]),
                    task_name=str(scope["task_name"]),
                )
                if maintenance_session is not None:
                    receipt["maintenance_session_live_readback"] = (
                        validate_live_maintenance_session_source(
                            reader,
                            task=task,
                            session=maintenance_session,
                        )
                    )
                with task_query_update_lock(task.menu_id):
                    projected, observed = prepare_query_update(
                        reader,
                        task=task,
                        plan=plan,
                    )
                    writer = Tiangong2QueryUpdateClient(
                        session.context.request,
                        authorization=authorization,
                    )
                    save_response = writer.save_python(
                        task_id=task.task_id,
                        source=projected,
                        resource_id=int(plan["baseline"]["normalized_resource_id"]),
                    )
                    receipt["save_request_sent"] = True
                    receipt["save_response"] = save_response
                    receipt["pre_save_readback"] = observed
                    receipt["readback"] = verify_query_update_readback(
                        reader,
                        task=task,
                        plan=plan,
                    )
                receipt.update(
                    {
                        "ok": True,
                        "status": "success",
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                        "remote_mutation_confirmed": True,
                        "fully_verified": True,
                    }
                )
                finalized = write_hashed_json(receipt_path, receipt, hash_field="receipt_sha256")
                print(
                    json.dumps(
                        {**finalized, "receipt_file": str(receipt_path.resolve())},
                        ensure_ascii=False,
                        indent=2,
                    )
                )
                return 0
            finally:
                session.close()
                session = None
    except Exception as exc:
        request_sent = bool(writer is not None and writer.write_count > 0)
        receipt.update(
            {
                "ok": False,
                "status": "failed",
                "failed_at": datetime.now(timezone.utc).isoformat(),
                "error": str(exc),
                "save_request_sent": request_sent,
                "remote_mutation_confirmed": False,
                "manual_attention_required": request_sent,
                "fully_verified": False,
            }
        )
        write_hashed_json(receipt_path, receipt, hash_field="receipt_sha256")
        if isinstance(exc, UsageError):
            raise
        raise UsageError(f"Tiangong2 task query update failed: {exc}") from exc
    finally:
        if session is not None:
            session.close()


def cmd_plan_task_submit(args: argparse.Namespace) -> int:
    validate_artifact_root(args.artifacts_dir)
    if args.output_file is not None:
        _validate_runtime_output(args.output_file)
    sync_playwright = import_playwright()
    with sync_playwright() as playwright:
        session = open_authenticated_session(playwright, args)
        try:
            reader = Tiangong2ReadOnlyClient(session.context.request)
            task = resolve_owned_task(
                reader,
                identity=session.identity,
                project_id=args.project_id,
                folder_name=args.folder,
                menu_id=args.menu_id,
                task_name=args.task_name,
            )
            plan = build_submit_plan(
                reader,
                task=task,
                identity=session.identity,
                note=args.note,
            )
            plan_path = args.output_file or _default_hashed_path(
                args.artifacts_dir,
                "task_submit_plan",
                task.menu_id,
                plan["plan_sha256"],
            )
            _validate_runtime_output(plan_path)
            finalized = write_hashed_json(plan_path, plan, hash_field="plan_sha256")
            print(
                json.dumps(
                    {
                        "ok": finalized["status"] == "ready",
                        "read_only": True,
                        "remote_mutations": 0,
                        "status": finalized["status"],
                        "plan_sha256": finalized["plan_sha256"],
                        "plan_file": str(plan_path.resolve()),
                        "note_sha256": finalized["submission"]["note_sha256"],
                        "source_matches_latest_published": finalized["baseline"][
                            "source_matches_latest_published"
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        finally:
            session.close()
    return 0


def cmd_submit_task(args: argparse.Namespace) -> int:
    _validate_runtime_output(args.plan_file)
    validate_artifact_root(args.artifacts_dir)
    plan = load_submit_plan(args.plan_file)
    maintenance_session, maintenance_context = _maintenance_phase_authorization(
        args,
        plan=plan,
        operation="submit",
    )
    authorization = authorize_submit(
        plan,
        expected_plan_sha256=args.expected_plan_sha256,
        confirm_submit=bool(args.confirm_submit or maintenance_context),
    )
    scope = plan["scope"]
    receipt_path = args.output_file or _default_hashed_path(
        args.artifacts_dir,
        "task_submit_receipt",
        int(scope["menu_id"]),
        plan["plan_sha256"],
    )
    _validate_runtime_output(receipt_path)
    receipt = {
        "schema_version": SUBMIT_RECEIPT_SCHEMA_VERSION,
        "operation": plan["operation"],
        "status": "running",
        "ok": False,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "plan_file": str(args.plan_file.resolve()),
        "plan_sha256": plan["plan_sha256"],
        "scope": scope,
        "submission": plan["submission"],
        "authorization": _phase_authorization_receipt(maintenance_context),
        "submit_request_sent": False,
        "remote_mutation_confirmed": False,
        "manual_attention_required": False,
        "save_requested": False,
        "publish_requested": False,
        "task_execution_requested": False,
    }
    sync_playwright = import_playwright()
    writer = None
    session = None
    try:
        with sync_playwright() as playwright:
            session = open_authenticated_session(playwright, args)
            try:
                if str(session.identity.get("name") or "") != str(
                    plan["identity"].get("name") or ""
                ):
                    raise UsageError("Authenticated Tiangong2 identity changed after submit planning")
                reader = Tiangong2ReadOnlyClient(session.context.request)
                task = resolve_owned_task(
                    reader,
                    identity=session.identity,
                    project_id=int(scope["project_id"]),
                    folder_name=str(scope["folder"]),
                    menu_id=int(scope["menu_id"]),
                    task_name=str(scope["task_name"]),
                )
                if maintenance_session is not None:
                    receipt["maintenance_session_live_readback"] = (
                        validate_live_maintenance_session_source(
                            reader,
                            task=task,
                            session=maintenance_session,
                        )
                    )
                with task_submit_lock(task.task_id):
                    receipt["pre_submit_readback"] = validate_pre_submit_drift(
                        reader,
                        task=task,
                        plan=plan,
                    )
                    writer = Tiangong2SubmitClient(
                        session.context.request,
                        authorization=authorization,
                    )
                    submit_response = writer.submit_task(
                        task_id=task.task_id,
                        note=str(plan["submission"]["note"]),
                    )
                    receipt["submit_request_sent"] = True
                    receipt["submit_response"] = submit_response
                    receipt["readback"] = verify_submit_readback(
                        reader,
                        task=task,
                        plan=plan,
                    )
                fully_verified = bool(receipt["readback"]["fully_verified"])
                receipt.update(
                    {
                        "ok": True,
                        "status": (
                            "accepted_and_submit_state_observed"
                            if fully_verified
                            else "accepted_with_stable_source_readback"
                        ),
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                        "remote_mutation_confirmed": True,
                        "fully_verified": fully_verified,
                    }
                )
                finalized = write_hashed_json(receipt_path, receipt, hash_field="receipt_sha256")
                print(
                    json.dumps(
                        {**finalized, "receipt_file": str(receipt_path.resolve())},
                        ensure_ascii=False,
                        indent=2,
                    )
                )
                return 0
            finally:
                session.close()
                session = None
    except Exception as exc:
        request_sent = bool(writer is not None and writer.write_count > 0)
        receipt.update(
            {
                "ok": False,
                "status": "failed",
                "failed_at": datetime.now(timezone.utc).isoformat(),
                "error": str(exc),
                "submit_request_sent": request_sent,
                "remote_mutation_confirmed": False,
                "manual_attention_required": request_sent,
                "fully_verified": False,
            }
        )
        write_hashed_json(receipt_path, receipt, hash_field="receipt_sha256")
        if isinstance(exc, UsageError):
            raise
        raise UsageError(f"Tiangong2 task submit failed: {exc}") from exc
    finally:
        if session is not None:
            session.close()


def cmd_plan_task_publish(args: argparse.Namespace) -> int:
    validate_artifact_root(args.artifacts_dir)
    if args.output_file is not None:
        _validate_runtime_output(args.output_file)
    sync_playwright = import_playwright()
    with sync_playwright() as playwright:
        session = open_authenticated_session(playwright, args)
        try:
            client = Tiangong2ReadOnlyClient(session.context.request)
            task = resolve_owned_task(
                client,
                identity=session.identity,
                project_id=args.project_id,
                folder_name=args.folder,
                menu_id=args.menu_id,
                task_name=args.task_name,
            )
            plan = build_publish_plan(client, task=task, identity=session.identity)
            plan_path = args.output_file or _default_hashed_path(
                args.artifacts_dir,
                "task_publish_plan",
                task.menu_id,
                plan["plan_sha256"],
            )
            _validate_runtime_output(plan_path)
            finalized = write_hashed_json(plan_path, plan, hash_field="plan_sha256")
            print(
                json.dumps(
                    {
                        "ok": finalized["status"] == "ready",
                        "read_only": True,
                        "remote_mutations": 0,
                        "status": finalized["status"],
                        "plan_sha256": finalized["plan_sha256"],
                        "plan_file": str(plan_path.resolve()),
                        "source_matches_latest_published": finalized["baseline"][
                            "source_matches_latest_published"
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        finally:
            session.close()
    return 0


def cmd_publish_task(args: argparse.Namespace) -> int:
    _validate_runtime_output(args.plan_file)
    validate_artifact_root(args.artifacts_dir)
    plan = load_publish_plan(args.plan_file)
    maintenance_session, maintenance_context = _maintenance_phase_authorization(
        args,
        plan=plan,
        operation="publish",
    )
    authorization = authorize_publish(
        plan,
        expected_plan_sha256=args.expected_plan_sha256,
        confirm_publish=bool(args.confirm_publish or maintenance_context),
    )
    scope = plan["scope"]
    receipt_path = args.output_file or _default_hashed_path(
        args.artifacts_dir,
        "task_publish_receipt",
        int(scope["menu_id"]),
        plan["plan_sha256"],
    )
    _validate_runtime_output(receipt_path)
    receipt = {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "operation": plan["operation"],
        "status": "running",
        "ok": False,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "plan_file": str(args.plan_file.resolve()),
        "plan_sha256": plan["plan_sha256"],
        "scope": scope,
        "authorization": _phase_authorization_receipt(maintenance_context),
        "publish_request_sent": False,
        "remote_mutation_confirmed": False,
        "manual_attention_required": False,
        "task_execution_requested": False,
    }
    sync_playwright = import_playwright()
    writer = None
    session = None
    try:
        with sync_playwright() as playwright:
            session = open_authenticated_session(playwright, args)
            try:
                active_name = str(session.identity.get("name") or "")
                if active_name != str(plan["identity"].get("name") or ""):
                    raise UsageError("Authenticated Tiangong2 identity changed after publish planning")
                reader = Tiangong2ReadOnlyClient(session.context.request)
                task = resolve_owned_task(
                    reader,
                    identity=session.identity,
                    project_id=int(scope["project_id"]),
                    folder_name=str(scope["folder"]),
                    menu_id=int(scope["menu_id"]),
                    task_name=str(scope["task_name"]),
                )
                if maintenance_session is not None:
                    receipt["maintenance_session_live_readback"] = (
                        validate_live_maintenance_session_source(
                            reader,
                            task=task,
                            session=maintenance_session,
                        )
                    )
                with task_publish_lock(task.menu_id):
                    validate_pre_publish_drift(reader, task=task, plan=plan)
                    writer = Tiangong2PublishClient(
                        session.context.request,
                        authorization=authorization,
                    )
                    publish_response = writer.publish_task(task.menu_id)
                    receipt["publish_request_sent"] = True
                    receipt["publish_response"] = publish_response
                    receipt["readback"] = verify_publish_readback(reader, task=task, plan=plan)
                receipt.update(
                    {
                        "ok": True,
                        "status": "success",
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                        "remote_mutation_confirmed": True,
                        "fully_verified": True,
                    }
                )
                finalized = write_hashed_json(receipt_path, receipt, hash_field="receipt_sha256")
                print(
                    json.dumps(
                        {**finalized, "receipt_file": str(receipt_path.resolve())},
                        ensure_ascii=False,
                        indent=2,
                    )
                )
                return 0
            finally:
                session.close()
                session = None
    except Exception as exc:
        request_sent = bool(writer is not None and writer.write_count > 0)
        receipt.update(
            {
                "ok": False,
                "status": "failed",
                "failed_at": datetime.now(timezone.utc).isoformat(),
                "error": str(exc),
                "publish_request_sent": request_sent,
                "remote_mutation_confirmed": False,
                "manual_attention_required": request_sent,
                "fully_verified": False,
            }
        )
        write_hashed_json(receipt_path, receipt, hash_field="receipt_sha256")
        if isinstance(exc, UsageError):
            raise
        raise UsageError(f"Tiangong2 task publish failed: {exc}") from exc
    finally:
        if session is not None:
            session.close()


def cmd_plan_task_execution(args: argparse.Namespace) -> int:
    validate_artifact_root(args.artifacts_dir)
    if args.output_file is not None:
        _validate_runtime_output(args.output_file)
    period_time = args.period_time or datetime.now(ZoneInfo("Asia/Shanghai")).replace(
        second=0,
        microsecond=0,
    ).strftime("%Y-%m-%d %H:%M:%S")
    sync_playwright = import_playwright()
    with sync_playwright() as playwright:
        session = open_authenticated_session(playwright, args)
        try:
            reader = Tiangong2ReadOnlyClient(session.context.request)
            task = resolve_owned_task(
                reader,
                identity=session.identity,
                project_id=args.project_id,
                folder_name=args.folder,
                menu_id=args.menu_id,
                task_name=args.task_name,
            )
            operations = Tiangong2OperationsReadOnlyClient(session.context.request)
            plan = build_execution_plan(
                reader,
                operations,
                task=task,
                identity=session.identity,
                period_time=period_time,
            )
            plan_path = args.output_file or _default_hashed_path(
                args.artifacts_dir,
                "task_execution_plan",
                task.menu_id,
                plan["plan_sha256"],
            )
            _validate_runtime_output(plan_path)
            finalized = write_hashed_json(plan_path, plan, hash_field="plan_sha256")
            print(
                json.dumps(
                    {
                        "ok": finalized["status"] == "ready",
                        "read_only": True,
                        "remote_mutations": 0,
                        "status": finalized["status"],
                        "period_time": finalized["execution"]["period_time"],
                        "plan_sha256": finalized["plan_sha256"],
                        "plan_file": str(plan_path.resolve()),
                        "baseline_execution_count": len(
                            finalized["baseline"]["baseline_execution_ids"]
                        ),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        finally:
            session.close()
    return 0


def cmd_execute_task_once(args: argparse.Namespace) -> int:
    _validate_runtime_output(args.plan_file)
    validate_artifact_root(args.artifacts_dir)
    plan = load_execution_plan(args.plan_file)
    maintenance_session, maintenance_context = _maintenance_phase_authorization(
        args,
        plan=plan,
        operation="execute",
    )
    authorization = authorize_execution(
        plan,
        expected_plan_sha256=args.expected_plan_sha256,
        confirm_execute=bool(args.confirm_execute or maintenance_context),
    )
    scope = plan["scope"]
    receipt_path = args.output_file or _default_hashed_path(
        args.artifacts_dir,
        "task_execution_receipt",
        int(scope["menu_id"]),
        plan["plan_sha256"],
    )
    _validate_runtime_output(receipt_path)
    receipt = {
        "schema_version": EXECUTION_RECEIPT_SCHEMA_VERSION,
        "operation": plan["operation"],
        "status": "running",
        "ok": False,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "plan_file": str(args.plan_file.resolve()),
        "plan_sha256": plan["plan_sha256"],
        "scope": scope,
        "authorization": _phase_authorization_receipt(maintenance_context),
        "execute_request_sent": False,
        "remote_mutation_confirmed": False,
        "manual_attention_required": False,
        "save_requested": False,
        "publish_requested": False,
        "schedule_change_requested": False,
        "trigger_successor": False,
    }
    sync_playwright = import_playwright()
    writer = None
    session = None
    try:
        with sync_playwright() as playwright:
            session = open_authenticated_session(playwright, args)
            try:
                if str(session.identity.get("name") or "") != str(
                    plan["identity"].get("name") or ""
                ):
                    raise UsageError("Authenticated Tiangong2 identity changed after execution planning")
                reader = Tiangong2ReadOnlyClient(session.context.request)
                task = resolve_owned_task(
                    reader,
                    identity=session.identity,
                    project_id=int(scope["project_id"]),
                    folder_name=str(scope["folder"]),
                    menu_id=int(scope["menu_id"]),
                    task_name=str(scope["task_name"]),
                )
                if maintenance_session is not None:
                    receipt["maintenance_session_live_readback"] = (
                        validate_live_maintenance_session_source(
                            reader,
                            task=task,
                            session=maintenance_session,
                        )
                    )
                operations = Tiangong2OperationsReadOnlyClient(session.context.request)
                with task_execution_lock(task.nezha_task_id):
                    validate_pre_execution_drift(
                        reader,
                        operations,
                        task=task,
                        plan=plan,
                    )
                    writer = Tiangong2ExecuteOnceClient(
                        session.context.request,
                        authorization=authorization,
                    )
                    execute_response = writer.execute_once(
                        task_id=task.nezha_task_id,
                        period_time=str(plan["execution"]["period_time"]),
                    )
                    receipt["execute_request_sent"] = True
                    receipt["execute_response"] = execute_response
                    receipt["readback"] = wait_for_new_execution(
                        operations,
                        task=task,
                        plan=plan,
                    )
                receipt.update(
                    {
                        "ok": True,
                        "status": "accepted_and_execution_id_verified",
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                        "remote_mutation_confirmed": True,
                        "execution_id": receipt["readback"]["execution_id"],
                        "fully_verified": True,
                        "terminal_status_verified": False,
                    }
                )
                finalized = write_hashed_json(receipt_path, receipt, hash_field="receipt_sha256")
                print(
                    json.dumps(
                        {**finalized, "receipt_file": str(receipt_path.resolve())},
                        ensure_ascii=False,
                        indent=2,
                    )
                )
                return 0
            finally:
                session.close()
                session = None
    except Exception as exc:
        request_sent = bool(writer is not None and writer.write_count > 0)
        receipt.update(
            {
                "ok": False,
                "status": "failed",
                "failed_at": datetime.now(timezone.utc).isoformat(),
                "error": str(exc),
                "execute_request_sent": request_sent,
                "remote_mutation_confirmed": False,
                "manual_attention_required": request_sent,
                "fully_verified": False,
            }
        )
        write_hashed_json(receipt_path, receipt, hash_field="receipt_sha256")
        if isinstance(exc, UsageError):
            raise
        raise UsageError(f"Tiangong2 task execute-once failed: {exc}") from exc
    finally:
        if session is not None:
            session.close()


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except UsageError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
