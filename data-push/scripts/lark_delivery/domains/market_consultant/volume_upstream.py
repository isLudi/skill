"""Fail-closed Tiangong2 evidence parser for the scheduled volume producer."""
from __future__ import annotations

import ast
from datetime import datetime, timedelta
import hashlib
import re


def parse_volume_log(doc, directory, cfg, slot, execution, validate_history, tz):
    """Require one bound create-then-delete Base replacement and full readback."""
    validate_history({**doc, "executions": [doc["execution"]]}, cfg, slot)
    if doc["execution"]["id"] != execution["id"] or doc["execution_detail"].get("status") != 6:
        raise ValueError("volume execution detail mismatch")
    stages = doc["stages"]
    if (not stages or stages[-1]["metadata"].get("statusDesc") != "success"
            or any(s["metadata"].get("statusDesc") not in {"failed", "success"}
                   or s["metadata"].get("taskId") != cfg["upstream"]["nezha_task_id"] for s in stages)):
        raise ValueError("volume stages incomplete")
    stage = stages[-1]
    path = (directory / stage["log_file"]).resolve()
    if not path.is_relative_to(directory.resolve()):
        raise ValueError("invalid volume log path")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != stage["log_sha256"]:
        raise ValueError("volume stage log Hash mismatch")
    log = raw.decode("utf-8")
    if cfg["upstream"]["log_protocol"] != "volume_two_period_create_then_delete_v1":
        raise ValueError("unsupported volume log protocol")
    required = ("Kyuubi查询完成：", "目标字段校验通过：14个字段",
                "新记录回读校验通过", "已按要求跳过旧KOC汇总表写入", "SUCCESS:")
    if (any(fragment not in log for fragment in required)
            or f"目标多维表格校验通过：table_id={cfg['volume_report']['volume_table_id']}" not in log
            or not re.search(r"exit_code:\s+0\s*$", log)):
        raise ValueError("incomplete volume write/readback success evidence")
    partitions = re.findall(r"采用dt=(\d{8}), hour=(\d+)，延迟(\d+)小时", log)
    counts = re.findall(r"数据校验通过：(\d+)行，期次(\[[^\r\n]+\])，(\d+)个归因渠道", log)
    old = re.findall(r"^写入前旧记录数：(\d+)\r?$", log, re.M)
    created = re.findall(r"^新记录创建完成：(\d+)条\r?$", log, re.M)
    deleted = re.findall(r"^旧记录删除完成：(\d+)条\r?$", log, re.M)
    final = re.findall(r"^最终回读校验通过：(\d+)条\r?$", log, re.M)
    if (len(partitions) != 1 or len(counts) != 3 or len(old) != 1
            or len(created) != 1 or len(final) != 1):
        raise ValueError("incomplete volume count/partition evidence: "
                         f"partitions={len(partitions)} counts={len(counts)} old={len(old)} "
                         f"created={len(created)} final={len(final)}")
    dt, hour, lag = partitions[0]
    if not 2 <= int(lag) <= 7:
        raise ValueError("volume source partition outside approved lookback")
    source_at = datetime.strptime(dt + "%02d" % int(hour), "%Y%m%d%H").replace(tzinfo=tz)
    if slot - source_at != timedelta(hours=int(lag)):
        raise ValueError("volume source partition not bound to slot")
    if len(set(counts)) != 1:
        raise ValueError("volume audit counts disagree")
    total, period_repr, channel_count = counts[0]
    periods = ast.literal_eval(period_repr)
    if (not isinstance(periods, list) or len(periods) != 2
            or len(set(periods)) != 2 or any(not re.fullmatch(r"\d{8}期", p) for p in periods)
            or int(channel_count) <= 0 or int(total) <= 0
            or int(created[0]) != int(total) or int(final[0]) != int(total)
            or (int(old[0]) > 0 and deleted != old)
            or (int(old[0]) == 0 and deleted)):
        raise ValueError("volume create/delete/readback counts disagree")
    return {"execution_id": execution["id"], "periods": periods, "total": int(total),
            "dt": dt, "hour": int(hour), "log_sha256": stage["log_sha256"]}
