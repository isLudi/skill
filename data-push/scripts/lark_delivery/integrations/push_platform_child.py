"""Run a platform CLI while the actual worker owns the shared push lock."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import runpy
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lark_delivery.integrations.push_platform import OPERATOR_SCRIPTS, coordinator_root, platform_operation, trace_root


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-marker", type=Path)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        raise ValueError("Missing platform CLI")
    script = Path(command[0]).resolve()
    if (script.name not in {"tiangong2_task.py", "usql_web_query.py"} or not script.is_file()
            or script != (OPERATOR_SCRIPTS / script.name).resolve()):
        raise ValueError("Unsupported platform CLI")
    allowed = ({"list-projects", "list-execution-history", "fetch-execution-log", "plan-task-publish"}
               if script.name == "tiangong2_task.py" else {"run"})
    if len(command) < 2 or command[1] not in allowed:
        raise ValueError("Unsupported platform operation")
    os.environ["CODEX_PUSH_GUARDED_PLATFORM"] = "1"
    os.environ["CODEX_PUSH_COORDINATOR_ROOT"] = str(coordinator_root())
    trace = trace_root()
    if trace is not None:
        os.environ["CODEX_PUSH_PLATFORM_TRACE_ROOT"] = str(trace)
    with platform_operation(start_marker=args.start_marker):
        sys.argv = [str(script), *command[1:]]
        sys.path.insert(0, str(script.parent))
        runpy.run_path(str(script), run_name="__main__")


if __name__ == "__main__":
    main()
