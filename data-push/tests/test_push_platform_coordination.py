from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

import pytest

from lark_delivery.integrations import push_platform as coordinator
from lark_delivery.integrations import push_platform_child
import fetch_qingcheng_process_source as qing_source


@pytest.fixture
def platform(monkeypatch, tmp_path):
    runtime = tmp_path / "operator-runtime"
    runtime.mkdir()
    monkeypatch.setattr(coordinator, "OPERATOR_RUNTIME", runtime)
    monkeypatch.setattr(coordinator, "_operator_revision", lambda: "revision-a")
    calls = []

    def run(argv, **kwargs):
        calls.append(argv)
        marker = Path(argv[argv.index("--start-marker") + 1])
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(json.dumps({"started_at": time.time()}), encoding="utf-8")
        folder = runtime / f"run-{len(calls)}"
        folder.mkdir()
        data = json.dumps({"executions": [{"id": len(calls)}]}).encode()
        (folder / "history.json").write_bytes(data)
        manifest = {"read_only": True, "remote_mutations": 0,
                    "artifact_files": [{"path": "history.json", "bytes": len(data),
                                        "sha256": hashlib.sha256(data).hexdigest()}]}
        (folder / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        reply = {"ok": True, "read_only": True, "remote_mutations": 0, "artifact_dir": str(folder)}
        time.sleep(0.03)
        return subprocess.CompletedProcess(argv, 0, json.dumps(reply), "")

    monkeypatch.setattr(coordinator.subprocess, "run", run)
    return runtime, calls


def read(binding=None):
    argv = ["python", str(coordinator.OPERATOR_SCRIPTS / "tiangong2_task.py"), "list-execution-history",
            "--task-name", "producer", "--limit", "12"]
    return coordinator.tiangong_read(argv, cwd=".", timeout=10, env={}, binding=binding or {"version": 1})


def test_identical_concurrent_readers_share_one_verified_result(platform):
    _, calls = platform
    with ThreadPoolExecutor(max_workers=8) as pool:
        replies = list(pool.map(lambda _: json.loads(read().stdout), range(8)))
    assert len(calls) == 1
    assert len({reply["artifact_dir"] for reply in replies}) == 1
    assert Path(calls[0][1]).name == "push_platform_child.py"


def test_changed_binding_or_artifact_cannot_reuse_the_cache(platform):
    runtime, calls = platform
    first = json.loads(read().stdout)
    read({"version": 2})
    (Path(first["artifact_dir"]) / "history.json").write_text("{}", encoding="utf-8")
    read()
    assert len(calls) == 3


def test_expired_result_is_rechecked_from_its_observation_start(platform):
    _, calls = platform
    read()
    cache = next((coordinator.coordinator_root() / "operator-cache").glob("*.json"))
    item = json.loads(cache.read_text(encoding="utf-8"))
    item["observed_started_at"] = time.time() - 91
    cache.write_text(json.dumps(item), encoding="utf-8")
    read()
    assert len(calls) == 2


def test_stable_published_plan_is_shared_without_treating_blocked_as_an_error(platform, monkeypatch):
    runtime, calls = platform

    def run(argv, **kwargs):
        calls.append(argv)
        plan = runtime / "plan.json"
        plan.write_text(json.dumps({"plan_sha256": "reviewed"}), encoding="utf-8")
        reply = {"ok": False, "read_only": True, "remote_mutations": 0,
                 "status": "blocked_already_published", "source_matches_latest_published": True,
                 "plan_file": str(plan), "plan_sha256": "reviewed"}
        return subprocess.CompletedProcess(argv, 0, json.dumps(reply), "")

    monkeypatch.setattr(coordinator.subprocess, "run", run)
    argv = ["python", str(coordinator.OPERATOR_SCRIPTS / "tiangong2_task.py"), "plan-task-publish",
            "--task-name", "producer"]
    first = coordinator.tiangong_read(argv, cwd=".", timeout=10, env={}, binding={"version": 1})
    second = coordinator.tiangong_read(argv, cwd=".", timeout=10, env={}, binding={"version": 1})
    assert len(calls) == 1
    assert json.loads(first.stdout)["status"] == json.loads(second.stdout)["status"] == "blocked_already_published"


def test_terminal_log_cache_is_bound_to_exact_execution_and_stage_hash(platform, monkeypatch):
    runtime, calls = platform

    def run(argv, **kwargs):
        calls.append(argv)
        folder = runtime / f"log-{len(calls)}"
        folder.mkdir()
        contents = {"execution.json": b"{}", "stage.log": b"complete"}
        entries = []
        for name, data in contents.items():
            (folder / name).write_bytes(data)
            entries.append({"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        (folder / "manifest.json").write_text(json.dumps({"read_only": True, "remote_mutations": 0,
                                                          "artifact_files": entries}), encoding="utf-8")
        reply = {"ok": True, "read_only": True, "remote_mutations": 0, "artifact_dir": str(folder),
                 "diagnostic": {"classification": "execution_success"}}
        return subprocess.CompletedProcess(argv, 0, json.dumps(reply), "")

    monkeypatch.setattr(coordinator.subprocess, "run", run)
    argv = ["python", str(coordinator.OPERATOR_SCRIPTS / "tiangong2_task.py"), "fetch-execution-log", "--exec-id", "1"]
    first = json.loads(coordinator.tiangong_read(argv, cwd=".", timeout=10, env={}, binding={}).stdout)
    coordinator.tiangong_read(argv, cwd=".", timeout=10, env={}, binding={})
    assert len(calls) == 1
    (Path(first["artifact_dir"]) / "stage.log").write_bytes(b"changed")
    coordinator.tiangong_read(argv, cwd=".", timeout=10, env={}, binding={})
    assert len(calls) == 2
    argv[-1] = "2"
    coordinator.tiangong_read(argv, cwd=".", timeout=10, env={}, binding={})
    assert len(calls) == 3


def test_platform_lock_serializes_independent_workers():
    active = 0
    maximum = 0
    mutex = threading.Lock()

    def worker(_):
        nonlocal active, maximum
        with coordinator.platform_operation():
            with mutex:
                active += 1
                maximum = max(maximum, active)
            time.sleep(0.025)
            with mutex:
                active -= 1

    with ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(worker, range(6)))
    assert maximum == 1


def test_only_reviewed_read_operations_can_use_shared_coordinator():
    with pytest.raises(ValueError, match="Unsupported"):
        coordinator.tiangong_read(["python", str(coordinator.OPERATOR_SCRIPTS / "tiangong2_task.py"), "publish-task"],
                                  cwd=".", timeout=1, env={}, binding={})


def test_guarded_child_rejects_write_commands_before_taking_lock(monkeypatch):
    script = coordinator.OPERATOR_SCRIPTS / "tiangong2_task.py"
    monkeypatch.setattr(sys, "argv", ["guard", "--", str(script), "publish-task"])
    with pytest.raises(ValueError, match="Unsupported platform operation"):
        push_platform_child.main()


def test_base_read_is_shared_only_for_identical_complete_source_evidence(tmp_path):
    calls = []
    scope = {"domain": "market", "table": "one", "identity": "user"}

    def load():
        calls.append(1)
        return [{"record_id": "r1"}], {"records_count": 1, "rev": 12, "has_more": False}

    first = coordinator.shared_base_snapshot(scope, {"execution_id": 1}, load)
    second = coordinator.shared_base_snapshot(scope, {"execution_id": 1}, load)
    assert first == second and len(calls) == 1
    coordinator.shared_base_snapshot(scope, {"execution_id": 2}, load)
    assert len(calls) == 2
    cache = next((coordinator.coordinator_root() / "base-snapshots").glob("*.json"))
    item = json.loads(cache.read_text(encoding="utf-8"))
    item["rows"][0]["record_id"] = "changed"
    cache.write_text(json.dumps(item), encoding="utf-8")
    coordinator.shared_base_snapshot(scope, {"execution_id": 2}, load)
    assert len(calls) == 3


def test_incomplete_base_snapshot_is_never_cached():
    def load():
        return [{"record_id": "r1"}], {"records_count": 1, "rev": 12, "has_more": True}

    with pytest.raises(ValueError, match="Incomplete"):
        coordinator.shared_base_snapshot({"table": "one"}, {"execution_id": 1}, load)
    assert not list((coordinator.coordinator_root() / "base-snapshots").glob("*.json"))


def test_processes_share_the_same_platform_lock(tmp_path):
    scripts = Path(__file__).resolve().parents[1] / "scripts"
    output = tmp_path / "events.jsonl"
    code = "\n".join([
        "import json, os, time",
        "from pathlib import Path",
        "from lark_delivery.integrations.push_platform import platform_operation",
        "p = Path(os.environ['PUSH_TEST_OUTPUT'])",
        "with platform_operation():",
        "    with p.open('a', encoding='utf-8') as f: f.write(json.dumps(['start', os.getpid()]) + '\\n')",
        "    time.sleep(0.08)",
        "    with p.open('a', encoding='utf-8') as f: f.write(json.dumps(['end', os.getpid()]) + '\\n')",
    ])
    env = dict(os.environ, PYTHONPATH=str(scripts), PUSH_TEST_OUTPUT=str(output))
    workers = [subprocess.Popen([sys.executable, "-c", code], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
               for _ in range(4)]
    for worker in workers:
        _, error = worker.communicate(timeout=20)
        assert worker.returncode == 0, error.decode("utf-8", errors="replace")
    events = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert len(events) == 8
    assert all(events[i][0] == "start" and events[i + 1] == ["end", events[i][1]] for i in range(0, 8, 2))


def test_rate_limit_failure_is_shared_and_starts_global_cooldown(platform, monkeypatch):
    _, calls = platform

    def failed(argv, **kwargs):
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 1, "", "HTTP 429")

    monkeypatch.setattr(coordinator.subprocess, "run", failed)
    assert read().returncode == 1
    assert read().returncode == 1
    assert len(calls) == 1
    with pytest.raises(RuntimeError, match="cooling down"):
        with coordinator.platform_operation():
            pytest.fail("cooldown should stop the platform operation")


def test_shared_ndjson_copies_only_same_complete_slice(tmp_path):
    calls = []
    scope = {"table": "same", "channel": "private"}

    def load(path):
        calls.append(1)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{"record_id":"r1"}\n', encoding="utf-8")
        return {"records_count": 1, "rev": 12, "has_more": False}

    first, second, third = (tmp_path / f"{name}.ndjson" for name in ("a", "b", "c"))
    coordinator.shared_ndjson_snapshot(scope, {"period": "one"}, first, lambda: load(first))
    coordinator.shared_ndjson_snapshot(scope, {"period": "one"}, second, lambda: load(second))
    assert len(calls) == 1 and first.read_bytes() == second.read_bytes()
    coordinator.shared_ndjson_snapshot(scope, {"period": "two"}, third, lambda: load(third))
    assert len(calls) == 2


def test_equivalent_qingcheng_pool_slices_share_rows_but_keep_their_own_manifest(tmp_path):
    calls = []

    def fetch(channel, period, output, **kwargs):
        calls.append(channel)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text('{"record_id":"r1"}\n', encoding="utf-8")
        return {"records_count": 1, "rev": 12, "has_more": False, "channel": channel}

    first = tmp_path / "first.ndjson"
    second = tmp_path / "second.ndjson"
    a = qing_source.shared_fetch("public_pool", "20261120期", first, fetcher=fetch)
    b = qing_source.shared_fetch("special_public_pool", "20261120期", second, fetcher=fetch)
    assert calls == ["public_pool"] and first.read_bytes() == second.read_bytes()
    assert a["channel"] == "public_pool" and b["channel"] == "special_public_pool"
    assert json.loads(second.with_suffix(".manifest.json").read_text(encoding="utf-8"))["channel"] == "special_public_pool"
