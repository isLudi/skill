"""CLI for read-only Tiangong2 data-development task exploration."""

from __future__ import annotations

import argparse
import json
import sys
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
    return parser


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
