"""Upstream rebinding for the Qingcheng process push: qing2lark -> qing2lark_guocheng.

The task was renamed (and republished as V29) on 2026-09-28 while keeping the same
immutable Nezha task id. These tests pin the reviewed binding and the two places a
rename leaks into: the execution ledger keeps the name a row was created with, and
the stage log filename carries the task name.
"""

import importlib.util
import json
from datetime import datetime
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

import pytest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
CONFIG_DIR = Path(__file__).resolve().parents[1] / "config/departments/qingcheng"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("qingcheng_process_rebind", SCRIPTS / "run_qingcheng_process.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

REVIEWED = {
    "project_id": 308, "folder": "吕帅", "menu_id": 103625, "task_id": 47728,
    "nezha_task_id": 67318, "task_name": "qing2lark_guocheng", "owner": "lvshuai01",
    "published_version": "V29", "version_id": 207387, "exec_file_id": 831981,
    "source_sha256": "2da69b923428509481cb185017d8ad05a1a126e5600c8f418396f51d12130de6",
    "audit_schema": "market2lark-two-period-audit-v1",
}
BATCH_FILES = ("process_batch_preview.json", "sec_process_batch.json", "special_process_batch.json",
               "partner_process_batch.json")
SLOT = datetime(2026, 9, 29, 14, 2, tzinfo=ZoneInfo("Asia/Shanghai"))


def upstream(path):
    return json.loads(path.read_text(encoding="utf-8"))["upstream"]


def test_every_qingcheng_batch_carries_the_same_reviewed_pin():
    for name in BATCH_FILES:
        assert upstream(CONFIG_DIR / name) == REVIEWED, name


def test_process_runner_pin_matches_the_shipped_configs():
    batch = MODULE._batch()
    assert batch["upstream"] == REVIEWED
    assert batch["windows_task_name"] == "Codex-Lark-Qingcheng-Process-GroupPush"


def test_operator_read_uses_the_configured_identity(monkeypatch):
    captured = []

    class Result:
        returncode = 0
        stdout = json.dumps({"ok": True, "read_only": True, "remote_mutations": 0, "artifact_dir": "x"})
        stderr = ""

    def run(argv, **kwargs):
        captured.append(argv)
        return Result()

    monkeypatch.setattr(MODULE.subprocess, "run", run)
    MODULE._operator_read("list-execution-history", "--limit", "50")
    argv = captured[0]
    assert argv[argv.index("--task-name") + 1] == "qing2lark_guocheng"
    assert argv[argv.index("--folder") + 1] == "吕帅"
    assert argv[argv.index("--menu-id") + 1] == "103625"
    assert argv[argv.index("--project-id") + 1] == "308"


def _artifact(tmp_path, *, row_name="qing2lark", stage_name="stage_4123_qing2lark_guocheng.log",
              exec_file_id=831981, trigger="EXECUTE", execution_id=173400001, row_count=3,
              status=6):
    period = MODULE._period(SLOT.date())
    current_hour = MODULE._expected_upstream_period_time(SLOT)
    history_dir = tmp_path / "history"
    history_dir.mkdir(parents=True)
    (history_dir / "history.json").write_text(json.dumps({"executions": [{
        "id": execution_id, "taskId": 67318, "taskName": row_name, "status": status,
        "periodTime": current_hour, "planRunTime": current_hour, "startTime": current_hour,
        "triggerSource": 0 if trigger == "SCHEDULE" else 1,
        "runConfig": json.dumps({"projectId": 308, "execFileId": exec_file_id, "triggerSourceEnum": trigger}),
    }]}), encoding="utf-8")
    audit = {"schema_version": "market2lark-two-period-audit-v1", "field_count": 27, "row_count": row_count,
             "periods": {period: {"snapshots": [["20260928", "19"]], "row_count": row_count,
                                  "channel_counts": {"顾问未加好友": row_count}}}}
    log_dir = tmp_path / "log"
    log_dir.mkdir(parents=True)
    (log_dir / "execution.json").write_text(json.dumps({
        "scope": {"project_id": 308, "menu_id": 103625, "task_id": 47728,
                  "nezha_task_id": 67318, "execution_id": execution_id},
        "identity": {"name": "lvshuai01"},
        "diagnostic": {"classification": "execution_success"},
    }), encoding="utf-8")
    (log_dir / stage_name).write_text("\n".join([
        "process表快照清单：{0}".format(json.dumps(audit, ensure_ascii=False)),
        "渠道映射版本：qingcheng-full-link-attribution-v1",
        "最终回读校验通过：{0}条".format(row_count),
        "SUCCESS: 青橙项目部最新两期{0}过程数据已独立覆盖写入并回读通过".format(period),
        "exit_code:  0",
    ]), encoding="utf-8")
    return history_dir, log_dir


def _audit(tmp_path, **kwargs):
    history_dir, log_dir = _artifact(tmp_path, **kwargs)

    def fake(command, *args):
        return {"artifact_dir": str(history_dir if command == "list-execution-history" else log_dir)}

    original = MODULE._operator_read
    MODULE._operator_read = fake
    try:
        return MODULE._upstream_audit(MODULE._period(SLOT.date()), SLOT)
    finally:
        MODULE._operator_read = original


def test_audit_accepts_both_the_old_and_new_execution_row_name(tmp_path):
    for row_name in ("qing2lark_guocheng", "qing2lark"):
        result = _audit(tmp_path / row_name, row_name=row_name)
        assert result["snapshot"] == ["20260928", "19"]
        # AUDIT_CHANNELS maps 顾问未加好友 to public_pool only.
        assert result["expected_counts"] == {"public_pool": 3, "private": 0, "douyin_dm": 0}


def test_audit_maps_on_the_hour_local_slot_to_the_upstream_40_minute_run():
    slot = datetime(2026, 10, 1, 12, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
    assert MODULE._expected_upstream_period_time(slot) == "2026-10-01 11:00:00"


def test_audit_accepts_either_stage_log_filename(tmp_path):
    for stage in ("stage_4123_qing2lark_guocheng.log", "stage_4123_qing2lark.log"):
        assert _audit(tmp_path / stage, stage_name=stage)["raw_channel_counts"] == {"顾问未加好友": 3}


def test_audit_rejects_an_unrelated_task_name(tmp_path):
    with pytest.raises(ValueError, match="not the qing2lark task"):
        _audit(tmp_path, row_name="qing2lark_zhuanhua")


def test_audit_rejects_the_superseded_exec_file(tmp_path):
    with pytest.raises(ValueError, match="is not unique"):
        _audit(tmp_path, exec_file_id=831661)


def test_audit_rejects_an_hour_without_a_successful_backfill(tmp_path):
    # The 2026-09-29 20:00 shape: the SCHEDULE row died on the upstream defect and
    # no successful V29 execution exists for the hour, so the audit refuses.
    with pytest.raises(ValueError, match="is not unique"):
        _audit(tmp_path, status=7)


def test_audit_rejects_an_unrelated_stage_log(tmp_path):
    with pytest.raises(ValueError, match="stage is not unique"):
        _audit(tmp_path, stage_name="stage_4123_market2lark.log")
