"""Fail-closed Tiangong2 log parser for the lead-detail producer."""
from __future__ import annotations

from datetime import datetime, timedelta
import hashlib
import json
import re

from ...core import catalog
from ...integrations import tiangong_release as rb

AUDIT_PROTOCOLS = {"two_period_audit_v1", "two_period_clear_then_replace_v1", "two_period_clear_then_replace_v1_retry"}
CLEAR_REPLACE_PROTOCOLS = {"two_period_clear_then_replace_v1", "two_period_clear_then_replace_v1_retry"}


def parse_complete_log(doc, directory, cfg, slot, execution, validate_history, tz):
    validate_history({**doc, "executions": [doc["execution"]]}, cfg, slot)
    if doc["execution"]["id"] != execution["id"] or doc["execution_detail"].get("status") != 6:
        raise ValueError("execution detail mismatch")
    stages = doc["stages"]
    if not stages:
        raise ValueError("upstream stages incomplete")
    stage_statuses = [stage.get("metadata", {}).get("statusDesc") for stage in stages]
    if any(status not in {"failed", "success"} for status in stage_statuses) or stage_statuses[-1] != "success":
        raise ValueError("upstream stages incomplete")
    for stage_info in stages:
        task_id = stage_info.get("metadata", {}).get("taskId")
        if task_id is not None and task_id != cfg["upstream"]["nezha_task_id"]:
            raise ValueError("stage task mismatch")
    stage = stages[-1]
    if stage["metadata"].get("taskId") != cfg["upstream"]["nezha_task_id"]:
        raise ValueError("stage task mismatch")
    path = (directory / stage["log_file"]).resolve()
    if not path.is_relative_to(directory.resolve()):
        raise ValueError("invalid stage log path")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != stage["log_sha256"]:
        raise ValueError("stage log Hash mismatch")
    log = raw.decode("utf-8")
    protocol = cfg["upstream"].get("log_protocol")
    required = ["新记录回读校验通过", "最终回读校验通过：", "SUCCESS:"]
    if protocol in (None, "two_period_audit_v1"):
        required.append("旧记录删除完成：")
    elif protocol in CLEAR_REPLACE_PROTOCOLS:
        required.extend(["清空前旧记录数：", "写入前清空回读确认：0条", "写入前旧记录数：0", "新记录创建完成："])
    else:
        raise ValueError("unsupported upstream log protocol")
    if any(x not in log for x in required) or not re.search(r"exit_code:\s+0\s*$", log):
        raise ValueError("no complete write/readback success evidence")
    partitions = re.findall(r"采用dt=(\d{8}), hour=(\d+)，延迟(\d+)小时", log)
    counts = re.findall(r"数据校验通过：(\d+)行，期次([^，\r\n]+)，", log)
    final = re.findall(r"最终回读校验通过：(\d+)条", log)
    distributions = re.findall(r"渠道分布：(\{[^\r\n]+\})", log)
    if len(partitions) != 1 or not counts or not final or not distributions:
        raise ValueError("required upstream evidence missing")
    dt, hour, lag = partitions[0]
    if not 2 <= int(lag) <= 7:
        raise ValueError("source partition outside approved 2-7 hour lookback")
    source_at = datetime.strptime(dt + "%02d" % int(hour), "%Y%m%d%H").replace(tzinfo=tz)
    if slot - source_at != timedelta(hours=int(lag)):
        raise ValueError("source partition not bound to current slot")
    total, period = counts[-1]
    channels = json.loads(distributions[-1])
    if int(total) != int(final[-1]) or sum(channels.values()) != int(total):
        raise ValueError("upstream counts disagree")
    if protocol in CLEAR_REPLACE_PROTOCOLS:
        before_clear = re.findall(r"^清空前旧记录数：(\d+)$", log, re.M)
        cleared = re.findall(r"^写入前旧记录清空完成：(\d+)条$", log, re.M)
        created = re.findall(r"^新记录创建完成：(\d+)条$", log, re.M)
        if (len(before_clear) != 1 or len(created) != 1
                or log.count("写入前清空回读确认：0条") != 1
                or len(re.findall(r"^写入前旧记录数：0$", log, re.M)) != 1):
            raise ValueError("invalid clear-then-replace evidence")
        old_count = int(before_clear[0])
        if ((old_count > 0 and (len(cleared) != 1 or int(cleared[0]) != old_count))
                or (old_count == 0 and cleared)
                or int(created[0]) != int(total)):
            raise ValueError("clear-then-replace counts disagree")
    raw_table_id = cfg.get("raw_table_id") or catalog.load_channel(catalog.DEFAULT_CHANNEL)["source"]["raw_table_id"]
    if "目标多维表格校验通过：table_id=" + raw_table_id not in log:
        raise ValueError("upstream Base destination changed")
    period_details = None
    if protocol in AUDIT_PROTOCOLS:
        audit_lines = re.findall(r"^双期快照清单：(\{[^\r\n]+\})\s*$", log, re.M)
        mapping_version = cfg["upstream"].get("channel_mapping_version", "0904")
        if len(audit_lines) != 1 or f"渠道映射版本：{mapping_version}" not in log:
            raise ValueError("two-period audit or channel-mapping evidence missing")
        audit = json.loads(audit_lines[0])
        period_details = audit.get("periods", {})
        if (audit.get("schema_version") != "market2lark-two-period-audit-v1" or audit.get("field_count") != 45
                or audit.get("row_count") != int(total) or len(period_details) != 2
                or sorted(period_details) != sorted(period.split("、"))):
            raise ValueError("invalid two-period source audit")
        combined_channels = {}
        for p, info in period_details.items():
            if not re.fullmatch(r"\d{8}期", p):
                raise ValueError("invalid audited period")
            datetime.strptime(p[:8], "%Y%m%d")
            n = info.get("row_count")
            distribution = info.get("channel_counts", {})
            if type(n) is not int or n <= 0 or any(type(v) is not int or v < 0 for v in distribution.values()) or sum(distribution.values()) != n:
                raise ValueError("period/channel audit counts disagree")
            snapshots = info.get("snapshots", [])
            if len(snapshots) != 1 or snapshots[0][0] != dt or int(snapshots[0][1]) != int(hour):
                raise ValueError("period audit has a different data snapshot")
            if any(not re.fullmatch(r"[0-9a-f]{64}", str(info.get(key, ""))) for key in ("key_sha256", "records_sha256")):
                raise ValueError("period audit fingerprints missing")
            for channel, count in distribution.items():
                combined_channels[channel] = combined_channels.get(channel, 0) + count
        if sum(info["row_count"] for info in period_details.values()) != int(total) or combined_channels != channels:
            raise ValueError("two-period totals disagree")
    policy = rb.active_policy(cfg, slot)
    if policy:
        rb.verify_raw_only_log(log, policy, period)
    return {"execution_id": execution["id"], "period": period, "periods": period_details, "dt": dt, "hour": int(hour),
            "total": int(total), "channel_counts": channels, "log_sha256": stage["log_sha256"],
            "artifact_dir": str(directory), "end_time": execution["endTime"]}
