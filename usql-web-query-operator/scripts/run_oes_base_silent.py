"""Console-free Task Scheduler entry; keep only safe launcher metadata in logs."""

import argparse
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import time
import uuid

SHANGHAI = timezone(timedelta(hours=8))


def _is_link(path):
    return path.is_symlink() or bool(getattr(path.lstat(), "st_file_attributes", 0) & 0x400)


class LauncherLog:
    def __init__(self, settings_path, action, *, clock=None):
        self.clock = clock or (lambda: datetime.now(SHANGHAI))
        settings_path = settings_path.expanduser().resolve()
        root, settings = settings_path.parent, {}
        try:
            value = json.loads(settings_path.read_text(encoding="utf-8-sig"))
            if isinstance(value, dict):
                settings = value
        except (OSError, ValueError):
            pass  # Broken settings are reported by the job and logged without their contents.
        runtime_value = settings.get("runtime_dir", "data/runtime")
        runtime = Path(runtime_value if isinstance(runtime_value, str) else "data/runtime").expanduser()
        runtime = (runtime if runtime.is_absolute() else root / runtime).resolve()
        skills = Path(__file__).resolve().parents[2]
        if runtime == skills or skills in runtime.parents:
            raise ValueError("Launcher logs must stay outside the skills directory")
        self.directory = runtime / "launcher-logs"
        self.directory.mkdir(parents=True, exist_ok=True)
        days = settings.get("log_retention_days", 30)
        self.days = days if type(days) is int and 1 <= days <= 3650 else 30
        self.action, self.launch_id = action, uuid.uuid4().hex
        self.write_errors = 0
        if not self.emit("silent_launcher_started"):
            raise OSError("Launcher log cannot be written")
        cutoff = self.clock().date() - timedelta(days=self.days - 1)
        for path in self.directory.glob("oes-launcher-????-??-??.jsonl"):
            try:
                day = datetime.strptime(path.stem.removeprefix("oes-launcher-"), "%Y-%m-%d").date()
                if day < cutoff and path.is_file() and not _is_link(path) and path.resolve().parent == self.directory:
                    path.unlink()
            except (OSError, ValueError):
                self.write_errors += 1

    @property
    def path(self):
        return self.directory / f"oes-launcher-{self.clock():%Y-%m-%d}.jsonl"

    def emit(self, event, **values):
        record = {"time": self.clock().isoformat(timespec="milliseconds"), "event": event,
                  "launch_id": self.launch_id, "action": self.action, "pid": os.getpid()}
        record.update({key: value for key, value in values.items()
                       if key in {"exit_code", "error_type", "seconds", "log_write_errors"}})
        try:
            path = self.path
            if (path.exists() or path.is_symlink()) and _is_link(path):
                raise OSError("Launcher log link is unsupported")
            with path.open("a", encoding="utf-8", newline="\n") as output:
                output.write(json.dumps(record, ensure_ascii=False) + "\n")
            return True
        except OSError:
            self.write_errors += 1
            return False


def _run(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--settings", type=Path, required=True)
    parser.add_argument("--action", choices=("sync", "cleanup", "check"), default="sync")
    parser.add_argument("--run-key")
    args = parser.parse_args(argv)
    started = time.monotonic()
    try:
        logger = LauncherLog(args.settings, args.action)
    except Exception:
        return 2  # Never start a data replacement without a writable launcher log.
    code = 2
    try:
        from run_oes_base_job import main as run_job
        options = [args.action, "--settings", str(args.settings)]
        if args.run_key:
            options.extend(["--run-key", args.run_key])
        code = run_job(options)
    except SystemExit as exc:
        code = exc.code if type(exc.code) is int else 0 if exc.code is None else 2
        logger.emit("silent_launcher_failed", error_type=type(exc).__name__, exit_code=code)
    except Exception as exc:
        logger.emit("silent_launcher_failed", error_type=type(exc).__name__, exit_code=2)
    logger.emit("silent_launcher_completed", exit_code=code, seconds=round(time.monotonic() - started, 3),
                log_write_errors=logger.write_errors)
    return code


def main(argv=None):
    # pythonw has no console streams. Discard raw CLI output, retaining JSONL metadata.
    with open(os.devnull, "w", encoding="utf-8") as sink, redirect_stdout(sink), redirect_stderr(sink):
        try:
            return _run(argv)
        except SystemExit as exc:
            return exc.code if type(exc.code) is int else 2


if __name__ == "__main__":
    raise SystemExit(main())
