"""Upstream and bot-identity checks that do not read the clock.

Split out of ``scheduler`` along the upstream-readiness boundary to keep that
module inside the layout size limit. The checks that do call the clock
(``upstream_ready``, ``operator``, ``operator_reply``, ``volume_upstream_ready``)
stay in ``scheduler``: the test suite patches the scheduler's clock and
operator seams, and moving those would silently bypass every such patch.
"""
from __future__ import annotations

import json
from pathlib import Path

from ...common import feishu as gp
from . import lead_upstream as lu
from . import volume_upstream as vu
from .window import TZ


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_history(history, cfg, slot):
    u = cfg["upstream"]
    scope = history["scope"]
    for k in ("project_id", "folder", "menu_id", "task_name", "task_id", "nezha_task_id"):
        if scope.get(k) != u[k]:
            raise ValueError("upstream scope drift: " + k)
    schedule = history["task_schedule"]
    if (history["identity"].get("name") != u["owner"] or schedule.get("supervisor") != u["owner"]
            or schedule.get("scheduleId") != u["schedule_id"] or schedule.get("scheduleFrequency") != "4h"):
        raise ValueError("upstream identity or schedule drift")
    stamp = slot.strftime("%Y-%m-%d %H:%M:%S")
    rows = history["executions"]
    matches = [r for r in rows if r.get("periodTime") == stamp and r.get("planRunTime") == stamp]
    if len(matches) != 1:
        raise ValueError("current scheduled execution missing or ambiguous")
    row = matches[0]
    if row.get("status") != 6 or row.get("taskId") != u["nezha_task_id"]:
        raise ValueError("current upstream execution not successful")
    run = json.loads(row["runConfig"])
    if run.get("execFileId") != u["exec_file_id"] or run.get("triggerSourceEnum") != "SCHEDULE":
        raise ValueError("published execution file changed or non-scheduled run")
    if any(r["id"] != row["id"] and (r.get("startTime") or r.get("planRunTime") or "") > row["startTime"] for r in rows):
        raise ValueError("newer execution observed; data may be replacing")
    return row


def parse_complete_log(doc, directory, cfg, slot, execution):
    return lu.parse_complete_log(doc, directory, cfg, slot, execution, validate_history, TZ)


def parse_volume_log(doc, directory, cfg, slot, execution):
    return vu.parse_volume_log(doc, directory, cfg, slot, execution, validate_history, TZ)


def require_shared_periods(lead_evidence, volume_evidence):
    if sorted(volume_evidence["periods"]) != sorted((lead_evidence.get("periods") or {}).keys()):
        raise ValueError("lead and volume upstream periods disagree")


def verify_bot(cfg):
    status = json.loads(gp.run_lark(["auth", "status", "--json", "--verify"], timeout=60))
    bot = status.get("identities", {}).get("bot", {})
    if not bot.get("verified") or bot.get("openId") != cfg["bot_open_id"] or bot.get("appName") != cfg["bot_name"]:
        raise ValueError("configured bot identity unavailable or changed")
    gp.verify_chat(cfg["chat_id"], cfg["chat_name"], "bot", 60)
