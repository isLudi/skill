"""CLI for governed Tiangong2 task exploration, execution logs, and publication."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

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
from .explorer import Tiangong2TaskExplorer
from .operations import (
    Tiangong2OperationsReadOnlyClient,
    fetch_execution_log_bundle,
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


def _add_browser_arguments(command: argparse.ArgumentParser) -> None:
    command.add_argument("--headed", action="store_true", help="Show the isolated Tiangong2 browser window.")
    command.add_argument("--state-path", type=Path, default=DEFAULT_TIANGONG2_TASK_STATE)
    command.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    command.add_argument("--browser-channel", default=DEFAULT_BROWSER_CHANNEL)
    command.add_argument("--executable-path", default=None)


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
    publish.add_argument("--confirm-publish", action="store_true", required=True)
    publish.add_argument(
        "--artifacts-dir",
        type=Path,
        default=TIANGONG2_TASK_RUNTIME_DIR / "publish-receipts",
    )
    publish.add_argument("--output-file", type=Path, default=None)
    _add_browser_arguments(publish)
    publish.set_defaults(func=cmd_publish_task)
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
                        "status": execution_payload["execution"].get("statusDesc"),
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
    authorization = authorize_publish(
        plan,
        expected_plan_sha256=args.expected_plan_sha256,
        confirm_publish=args.confirm_publish,
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
