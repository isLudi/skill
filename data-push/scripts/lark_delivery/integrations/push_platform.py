"""Coordinate the local push clients that read company platforms.

The operation lock is held by the process actually performing the network
operation. A separate per-key lock coalesces identical, read-only Tiangong
requests across independently scheduled push processes.
"""
from __future__ import annotations

from contextlib import contextmanager
import errno
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import uuid


ROOT = Path(__file__).resolve().parents[5]
OPERATOR_RUNTIME = ROOT / "runtime" / "usql-web-query-operator" / "tiangong2-task"
OPERATOR_SCRIPTS = ROOT / "skills" / "usql-web-query-operator" / "scripts"
GUARDED_CHILD = Path(__file__).with_name("push_platform_child.py")
_MAX_AGE = {"list-execution-history": 90, "fetch-execution-log": 3600, "plan-task-publish": 90}
_LOCK_TIMEOUT = 900.0


def coordinator_root() -> Path:
    override = os.environ.get("CODEX_PUSH_COORDINATOR_ROOT")
    return Path(override).resolve() if override else ROOT / "runtime" / "data-push-platform-coordinator"


def trace_root() -> Path | None:
    try:
        config = json.loads((ROOT / "machine.local.json").read_text(encoding="utf-8"))
        return Path(config["paths"]["push_log_root"]) / "_platform"
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return None


def _digest(value) -> str:
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _state_revision():
    try:
        state = (OPERATOR_RUNTIME / "state.json").stat()
        return [state.st_mtime_ns, state.st_size]
    except OSError:
        return None


def _operator_revision() -> str:
    digest = hashlib.sha256()
    for relative in ("tiangong2_task/cli.py", "tiangong2_task/client.py", "tiangong2_task/operations.py",
                     "tiangong2_task/scope.py", "tiangong2_task/session.py", "_shared/push_request_pacing.py"):
        path = OPERATOR_SCRIPTS / relative
        digest.update(relative.encode("ascii"))
        digest.update(path.read_bytes())
    digest.update(Path(__file__).read_bytes())
    digest.update(GUARDED_CHILD.read_bytes())
    return digest.hexdigest()


@contextmanager
def file_lock(path: Path, *, timeout: float = _LOCK_TIMEOUT):
    """Hold an OS-owned lock; a crashed process cannot leave it locked."""
    path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout
    with path.open("a+b") as stream:
        while True:
            try:
                stream.seek(0)
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError as exc:
                if exc.errno not in {errno.EACCES, errno.EAGAIN, errno.EDEADLK}:
                    raise
                if time.monotonic() >= deadline:
                    raise TimeoutError("Timed out waiting for the shared push platform coordinator")
                time.sleep(0.2)
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


@contextmanager
def platform_operation(*, start_marker: Path | None = None):
    """Serialize push platform work, including browser startup, across processes."""
    with file_lock(coordinator_root() / "platform-operation.lock"):
        cooldown = coordinator_root() / "cooldown.json"
        try:
            state = json.loads(cooldown.read_text(encoding="utf-8"))
            blocked_until = float(state["until"]) if 0 <= time.time() - float(state["created_at"]) <= 120 else 0.0
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            blocked_until = 0.0
        if time.time() < blocked_until:
            raise RuntimeError("Company platform is cooling down after a rate-limit or temporary error")
        if start_marker is not None:
            _write_json(start_marker, {"started_at": time.time()})
        yield


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        temporary.write_text(json.dumps(value, ensure_ascii=True, sort_keys=True), encoding="utf-8")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _inside_runtime(path: Path) -> bool:
    return path.resolve().is_relative_to(OPERATOR_RUNTIME.resolve())


def _artifact_fingerprint(reply: dict, command: str) -> str:
    """Bind cached replies to existing, unchanged operator artifacts."""
    if reply.get("read_only") is not True or reply.get("remote_mutations") != 0:
        raise ValueError("The platform response is not a verified read-only receipt")
    if command == "plan-task-publish":
        if reply.get("status") != "blocked_already_published" or reply.get("source_matches_latest_published") is not True:
            raise ValueError("Publication state is not a stable published version")
        path = Path(reply["plan_file"])
        if not _inside_runtime(path) or not path.is_file():
            raise ValueError("Publication plan escaped the operator runtime")
        content = path.read_bytes()
        if json.loads(content).get("plan_sha256") != reply.get("plan_sha256"):
            raise ValueError("Publication plan identity changed")
        return hashlib.sha256(content).hexdigest()
    if reply.get("ok") is not True:
        raise ValueError("The operator read did not complete successfully")
    if command == "fetch-execution-log" and (reply.get("diagnostic") or {}).get("classification") != "execution_success":
        raise ValueError("Only completed successful execution logs can be reused")
    folder = Path(reply["artifact_dir"])
    if not _inside_runtime(folder) or not folder.is_dir():
        raise ValueError("Operator artifact escaped its runtime")
    manifest_path = folder / "manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    if manifest.get("read_only") is not True or manifest.get("remote_mutations") != 0:
        raise ValueError("Invalid read-only artifact manifest")
    entries = manifest.get("artifact_files")
    if not isinstance(entries, list) or not entries:
        raise ValueError("Artifact manifest is empty")
    digest = hashlib.sha256(manifest_bytes)
    names = set()
    for entry in entries:
        name = entry.get("path")
        if not isinstance(name, str) or Path(name).name != name or name in names:
            raise ValueError("Invalid artifact path")
        names.add(name)
        path = folder / name
        if not _inside_runtime(path) or not path.is_file():
            raise ValueError("Operator artifact is missing")
        data = path.read_bytes()
        if len(data) != entry.get("bytes") or hashlib.sha256(data).hexdigest() != entry.get("sha256"):
            raise ValueError("Operator artifact content changed")
        digest.update(name.encode("utf-8"))
        digest.update(data)
    required = "history.json" if command == "list-execution-history" else "execution.json"
    if required not in names:
        raise ValueError("Required operator artifact is missing")
    return digest.hexdigest()


def _cached(cache_path: Path, command: str, cache_key: str, now: float):
    try:
        item = json.loads(cache_path.read_text(encoding="utf-8"))
        age = now - float(item["observed_started_at"])
        if item.get("key") != cache_key or age < 0 or age > _MAX_AGE[command]:
            return None
        reply = item["reply"]
        if _artifact_fingerprint(reply, command) != item["artifact_fingerprint"]:
            return None
        return reply
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return None


def _recent_failure(cache_path: Path, cache_key: str, now: float) -> bool:
    try:
        item = json.loads(cache_path.read_text(encoding="utf-8"))
        return (item.get("key") == cache_key and 0 <= now - float(item["failed_at"]) <= 30
                and now < float(item["failed_until"]))
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return False


def tiangong_read(argv, *, cwd, timeout, env, binding):
    """Run or share one exact read-only operation; never bypass the coordinator."""
    argv = list(map(str, argv))
    if (len(argv) < 3 or Path(argv[1]).resolve() != (OPERATOR_SCRIPTS / "tiangong2_task.py").resolve()
            or argv[2] not in _MAX_AGE):
        raise ValueError("Unsupported push Tiangong read operation")
    command = argv[2]
    key = _digest({"argv": argv[1:], "binding": binding, "operator_revision": _operator_revision(),
                   "state_revision": _state_revision()})
    root = coordinator_root()
    cache_path = root / "operator-cache" / (key + ".json")
    with file_lock(root / "operator-locks" / (key + ".lock")):
        if _recent_failure(cache_path, key, time.time()):
            return subprocess.CompletedProcess(argv, 1, "", "A shared platform read failed recently; retry later")
        cached = _cached(cache_path, command, key, time.time())
        if cached is not None:
            return subprocess.CompletedProcess(argv, 0, json.dumps(cached, ensure_ascii=False), "")
        marker = root / "starts" / (uuid.uuid4().hex + ".json")
        started = time.time()
        child = [argv[0], str(GUARDED_CHILD), "--start-marker", str(marker), "--", *argv[1:]]
        try:
            try:
                result = subprocess.run(child, cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                                        timeout=timeout, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                                        env=env)
            except subprocess.TimeoutExpired:
                failed_at = time.time()
                _write_json(cache_path, {"key": key, "failed_at": failed_at, "failed_until": failed_at + 30})
                raise
            if marker.is_file():
                started = float(json.loads(marker.read_text(encoding="utf-8"))["started_at"])
            if result.returncode == 0:
                try:
                    reply = json.loads(result.stdout)
                    fingerprint = _artifact_fingerprint(reply, command)
                    if 0 <= time.time() - started <= _MAX_AGE[command]:
                        _write_json(cache_path, {"key": key, "observed_started_at": started,
                                                 "artifact_fingerprint": fingerprint, "reply": reply})
                except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
                    pass  # The caller still receives the original receipt and validates it.
            else:
                failed_at = time.time()
                _write_json(cache_path, {"key": key, "failed_at": failed_at, "failed_until": failed_at + 30})
                failure = ((result.stdout or "") + "\n" + (result.stderr or "")).lower()
                if any(term in failure for term in ("http 429", "http 503", "too many requests", "rate limit")):
                    _write_json(root / "cooldown.json", {"created_at": failed_at, "until": failed_at + 120})
            return result
        finally:
            marker.unlink(missing_ok=True)


def guarded_command(argv):
    """Run a separate platform CLI in a child that owns the global lock."""
    argv = list(map(str, argv))
    if (len(argv) < 2 or Path(argv[1]).name not in {"usql_web_query.py", "tiangong2_task.py"}
            or Path(argv[1]).resolve() != (OPERATOR_SCRIPTS / Path(argv[1]).name).resolve()):
        raise ValueError("Unsupported guarded platform CLI")
    return [argv[0], str(GUARDED_CHILD), "--", *argv[1:]]


def shared_base_snapshot(scope: dict, evidence: dict, load, *, max_age: float = 120):
    """Share a complete, audited Base snapshot only for the same source and writer."""
    scope_key = _digest(scope)
    evidence_key = _digest(evidence)
    root = coordinator_root()
    path = root / "base-snapshots" / (scope_key + ".json")
    with file_lock(root / "base-locks" / (scope_key + ".lock")):
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
            age = time.time() - float(item["observed_started_at"])
            snapshot = {"rows": item["rows"], "audit": item["audit"]}
            if (item.get("evidence_key") == evidence_key and 0 <= age <= max_age
                    and _digest(snapshot) == item.get("content_sha256")
                    and snapshot["audit"].get("has_more") is False
                    and type(snapshot["audit"].get("rev")) is int
                    and snapshot["audit"].get("records_count") == len(snapshot["rows"])):
                return snapshot["rows"], snapshot["audit"]
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            pass
        started = time.time()
        rows, audit = load()
        if (audit.get("has_more") is not False or type(audit.get("rev")) is not int
                or audit.get("records_count") != len(rows)):
            raise ValueError("Incomplete Base snapshot cannot be shared")
        snapshot = {"rows": rows, "audit": audit}
        if 0 <= time.time() - started <= max_age:
            _write_json(path, {"evidence_key": evidence_key, "observed_started_at": started,
                               "content_sha256": _digest(snapshot), **snapshot})
        return rows, audit


def shared_ndjson_snapshot(scope: dict, evidence: dict, output: Path, load, *, max_age: float = 90) -> dict:
    """Reuse one validated Base slice while preserving each caller's output files."""
    output = Path(output)

    def read_once():
        audit = load()
        rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines() if line]
        return rows, audit

    rows, audit = shared_base_snapshot(scope, evidence, read_once, max_age=max_age)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    output.with_suffix(".manifest.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
                                                     encoding="utf-8")
    return audit
