#!/usr/bin/env python3
"""Export registered local data-push channels as Base record payloads.

The exporter is read-only with respect to both local configuration and Feishu.
It emits deterministic ``record-batch-create`` payloads for the two-table
channel registry template.  Technical records include the complete source JSON
so that parameters not promoted to searchable columns remain auditable.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys


SKILL_ROOT = Path(__file__).resolve().parents[1]
CONFIG_ROOT = SKILL_ROOT / "config"
WEEKDAYS = ("周一", "周二", "周三", "周四", "周五", "周六", "周日")
DEFAULT_GRADES = ("初一", "初二", "初三", "高一", "高二", "高三")

DISPLAY_NAMES = {
    "supervisor_koc_zhoushuai_warning": "KOC-周帅数学高中双期预警",
    "self_incubated_koc_5": "自孵化KOC-5元纯课",
    "business_koc_math": "商务KOC数学",
    "supervisor_koc_douyin_sync": "KOC与抖音私信",
    "supervisor_private_app_sync": "集团私域与APP",
    "supervisor_self_incubated_koc_5_grade_9": "KOC初三",
    "supervisor_yafei_grade_9": "亚飞B站初三",
    "supervisor_yafei_grade_9_advisor": "亚飞B站初三顾问",
    "supervisor_zhu_doctor_video49": "朱博士",
    "supervisor_chenruichun": "陈瑞春",
}

SCHEDULE_FILES = {
    "app_grade_9": None,  # Preview-only; no Windows task is registered.
    "supervisor_koc_zhoushuai_warning": "supervisor_koc_zhoushuai_warning_scheduled_push.json",
    "self_incubated_koc_5": "scheduled_push.json",
    "business_koc_math": "business_koc_math_scheduled_push.json",
    "supervisor_koc_douyin_sync": "supervisor_koc_douyin_sync_scheduled_push.json",
    "supervisor_private_app_sync": "supervisor_private_app_sync_scheduled_push.json",
    "supervisor_self_incubated_koc_5_grade_9": "supervisor_self_incubated_koc_5_grade_9_scheduled_push.json",
    "supervisor_yafei_grade_9": "supervisor_yafei_grade_9_scheduled_push.json",
    "supervisor_yafei_grade_9_advisor": "supervisor_yafei_grade_9_advisor_scheduled_push.json",
    "supervisor_zhu_doctor_video49": "supervisor_zhu_doctor_video49_scheduled_push.json",
    "supervisor_chenruichun": "supervisor_chenruichun_scheduled_push.json",
}

SCRIPT_STEMS = {
    "app_grade_9": (None, None),
    "supervisor_koc_zhoushuai_warning": ("channels/market_consultant/supervisor_koc_zhoushuai_warning.py", "register_supervisor_koc_zhoushuai_warning_scheduled_push.ps1"),
    "self_incubated_koc_5": ("run_scheduled_push.ps1", "register_scheduled_push.ps1"),
    "business_koc_math": ("run_business_koc_math_scheduled_push.ps1", "register_business_koc_math_scheduled_push.ps1"),
    "supervisor_koc_douyin_sync": ("run_supervisor_koc_douyin_sync_scheduled_push.ps1", "register_supervisor_koc_douyin_sync_scheduled_push.ps1"),
    "supervisor_private_app_sync": ("run_supervisor_private_app_sync_scheduled_push.ps1", "register_supervisor_private_app_sync_scheduled_push.ps1"),
    "supervisor_self_incubated_koc_5_grade_9": ("run_supervisor_self_incubated_koc_5_grade_9_scheduled_push.ps1", "register_supervisor_self_incubated_koc_5_grade_9_scheduled_push.ps1"),
    "supervisor_yafei_grade_9": ("run_supervisor_yafei_grade_9_scheduled_push.ps1", "register_supervisor_yafei_grade_9_scheduled_push.ps1"),
    "supervisor_yafei_grade_9_advisor": ("run_supervisor_yafei_grade_9_advisor_scheduled_push.ps1", "register_supervisor_yafei_grade_9_advisor_scheduled_push.ps1"),
    "supervisor_zhu_doctor_video49": ("run_supervisor_zhu_doctor_video49_scheduled_push.ps1", "register_supervisor_zhu_doctor_video49_scheduled_push.ps1"),
    "supervisor_chenruichun": ("run_supervisor_chenruichun_scheduled_push.ps1", "register_supervisor_chenruichun_scheduled_push.ps1"),
}

PROFILE_COLUMNS = {
    "supervisor-channel-warning": {
        "dimensions": ["期次", "渠道", "年级", "主管"],
        "process": "主管、首call率、5min率、外呼频次",
        "result": "主管、截面单效、退费率",
    },
    "grade-compact": {
        "dimensions": ["期次", "渠道", "年级", "负责人"],
        "process": "期次、负责人、退后线索、首call、48h外呼、5min、好友率、深沟率、双沟率",
        "result": "期次、负责人、退后线索、5min、双沟率、首节到课率、当期单效、截面单效",
    },
    "supervisor-detail": {
        "dimensions": ["期次", "渠道", "年级", "负责人", "主管"],
        "process": "期次、负责人、主管、退前线索、退后线索、线索留存率、总通时(min)、首call率、48h外呼、外呼频次、5min、好友率、APP登陆率、深沟率、双沟率",
        "result": "期次、负责人、主管、退后线索、5min、双沟率、首节到课率、当期单效、截面单效",
    },
    "supervisor-video49": {
        "dimensions": ["期次", "渠道", "年级", "负责人", "主管", "顾问"],
        "process": "期次、负责人、主管、顾问、退前线索、退后线索、线索留存率、总通时(min)、首call率、48h外呼、外呼频次、5min、好友率、APP登陆率、深沟率、双沟率",
        "result": "期次、负责人、主管、顾问、退后线索、首节到课率、单效（当期）、人均报科、人头转化、订单转化、净收款、退费率、单效",
    },
    "supervisor-advisor-detail": {
        "dimensions": ["期次", "渠道", "年级", "负责人", "主管", "顾问"],
        "process": "期次、负责人、主管、顾问、退前线索、退后线索、线索留存率、总通时(min)、首call率、48h外呼、外呼频次、5min、好友率、APP登陆率、深沟率、双沟率",
        "result": "期次、负责人、主管、顾问、退后线索、5min、双沟率、首节到课率、当期单效、截面单效",
    },
}


def _load(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _compact(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _select(value: str):
    return [value] if value else []


def _datetime_cell(value: str):
    if not value:
        return None
    return datetime.fromisoformat(value).strftime("%Y-%m-%d %H:%M")


def _weekdays(values):
    return [WEEKDAYS[int(value)] for value in values or []]


def _channels(config):
    if config.get("channels"):
        return list(config["channels"])
    match = config.get("source", {}).get("channel_match", {})
    if match.get("values"):
        return list(match["values"])
    if match.get("keyword"):
        return [match["keyword"]]
    return [config.get("channel", "")]


def _match_mode(config):
    match = config.get("source", {}).get("channel_match", {})
    if match.get("match_mode") == "contains":
        return "名称包含"
    return "多个精确值" if len(_channels(config)) > 1 else "精确匹配"


def _grades(report):
    if report.get("included_grades"):
        return list(report["included_grades"])
    excluded = set(report.get("excluded_grades") or [])
    if excluded:
        return [grade for grade in DEFAULT_GRADES if grade not in excluded]
    return ["不限"]


def _mention_label(value):
    return {"manager": "负责人", "supervisor": "主管", "consultant": "顾问"}.get(value, "其他待评审")


def _business_metrics(profile, section):
    dimensions = {"期次", "渠道", "年级", "负责人", "主管", "顾问"}
    return [name for name in profile[section].split("、") if name not in dimensions]


def _task_state(task_name: str):
    if sys.platform != "win32" or not task_name:
        return False, "未在当前平台核验"
    safe_name = task_name.replace("'", "''")
    command = (
        "$t=Get-ScheduledTask -TaskName '" + safe_name + "' -ErrorAction SilentlyContinue;"
        "if($null -eq $t){'false|不存在'}else{([string]$t.Settings.Enabled).ToLower()+'|'+[string]$t.State}"
    )
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=15,
        )
        line = result.stdout.strip().splitlines()[-1]
        enabled, state = line.split("|", 1)
        return enabled == "true", state
    except (OSError, subprocess.SubprocessError, IndexError, ValueError):
        return False, "核验失败"


def _paths(domain: str, channel_id: str):
    run_name, register_name = SCRIPT_STEMS[channel_id]
    schedule_name = SCHEDULE_FILES[channel_id]
    return {
        "配置文件路径": str((CONFIG_ROOT / "departments" / domain / f"{channel_id}.json").resolve()),
        "入口脚本路径": str((SKILL_ROOT / "scripts" / "channels" / domain / f"{channel_id}.py").resolve()),
        "定时参数文件路径": str((CONFIG_ROOT / schedule_name).resolve()) if schedule_name else "",
        "任务执行脚本路径": str((SKILL_ROOT / "scripts" / run_name).resolve()) if run_name else "",
        "任务注册脚本路径": str((SKILL_ROOT / "scripts" / register_name).resolve()) if register_name else "",
    }


def _operator_record(channel_ref: str, config):
    domain, channel_id = channel_ref.split("/", 1)
    source = config.get("source", {})
    report = config.get("report", {})
    schedule = config.get("schedule", {})
    target = (config.get("targets") or [{}])[0]
    match = source.get("channel_match", {})
    profile = PROFILE_COLUMNS[source.get("report_profile", "grade-compact")]
    mention = _mention_label(source.get("mention_target"))
    reminder_rank_by_rule = {
        "grade_manager_minimum_all_ties": "最低值",
        "channel_grade_source_supervisor_minimum_all_ties": "最低值",
        "channel_grade_source_advisor_minimum_all_ties": "最低值",
        "channel_grade_source_advisor_bottom_10pct_minimum_one": "底部10%（每年级至少1名）",
        "all_current_supervisors_above_full_channel_team": "较团队整体高",
    }
    reminder_rule = source.get("reminder_rule")
    if reminder_rule not in reminder_rank_by_rule:
        raise ValueError(f"unmapped market reminder rule: {reminder_rule}")
    reminder_rank = reminder_rank_by_rule[reminder_rule]
    department = {"market_consultant": "市场顾问部", "qingcheng": "青橙项目部"}.get(domain, "其他")
    first_send = schedule.get("first_send_at", "")
    if source.get("report_type") == "auto" and report.get("period_rule") == "natural_week_friday":
        process_weekdays = list(range(7)) if report.get("weekend_next_process_enabled") else [0, 1, 2, 3]
        result_weekdays = [4, 5, 6]
    else:
        process_weekdays = report.get("process_weekdays")
        result_weekdays = report.get("result_weekdays")
    process_sort = "5min精确值降序；并列按线索留存率降序，再按组织字段稳定排序"
    result_sort = (
        "截面单效精确值降序；并列按首节到课率降序，再按组织字段稳定排序"
        if source.get("report_profile") in {"supervisor-video49", "supervisor-advisor-detail"}
        else "单效精确值降序；并列按首节到课率降序，再按组织字段稳定排序"
    )
    if source.get("report_profile") == "supervisor-advisor-detail":
        layout = "按渠道、年级分块；每行同时展示负责人、主管、顾问三级维度；过程/转化分别生成长图；顾问退后线索<5不展示。"
        style = "市场顾问部主管维度配色：深藏青表头与总计；5min使用橙色色块，双沟率使用蓝色色块；截面单效按降序标色。"
        reminder_suffix = "；按顾问维度取底部10%，每个年级至少提醒1名"
    else:
        layout = "按渠道、年级分块；维度字段在前；同一报告类型合并为一张长图。"
        style = "市场顾问部既有深藏青表头、总计和固定指标色阶。"
        reminder_suffix = ""
    weekend_note = ""
    if report.get("weekend_next_process_enabled"):
        weekend_note = (
            "周五至周日本期转化与下一自然周周五期次过程同条播报；"
            f"本期转化主管退后线索≥{report.get('minimum_post_leads')}，"
            f"下一期过程主管退后线索≥{report.get('weekend_next_process_minimum_post_leads', report.get('minimum_post_leads'))}；"
            "各期独立制图和按最低指标@，无符合门槛主管的部分跳过。"
        )
    fields = {
        "申请编号": channel_ref,
        "申请状态": _select("已上线" if schedule.get("enabled") else "已暂停"),
        "申请部门": _select(department),
        "业务负责人": config.get("upstream", {}).get("owner", ""),
        "需求背景": "已登记本地数据推送；由data-push现有配置导入。",
        "渠道标准名称": DISPLAY_NAMES.get(channel_id, config.get("channel", channel_id)),
        "原始渠道示例": "；".join(_channels(config)),
        "渠道匹配方式": _select(_match_mode(config)),
        "匹配关键词或规范值": match.get("keyword") or " OR ".join(_channels(config)),
        "数据源链接": source.get("source_url", ""),
        "原始表名称": source.get("raw_table_name", ""),
        "原始表链接": source.get("raw_source_url", ""),
        "数据刷新频率": "由上游天宫任务与发送前新鲜度门禁共同控制",
        "目标群": [{"id": target["chat_id"]}] if target.get("chat_id") else [],
        "发送身份": _select("管家机器人" if config.get("sender", {}).get("identity") == "bot" else "用户身份"),
        "期次规则": _select("自然周周五期次" if report.get("period_rule") == "natural_week_friday" else "其他待评审"),
        "过程数据星期": _weekdays(process_weekdays),
        "转化数据星期": _weekdays(result_weekdays),
        "期望首次上线日期": (first_send[:10] + " 00:00") if first_send else None,
        "期望推送时段": "、".join(f"{int(hour):02d}:00" for hour in schedule.get("hours", [])),
        "时区": _select(schedule.get("timezone", "Asia/Shanghai")),
        "数据维度": profile["dimensions"],
        "年级范围": _grades(report),
        "其他范围或排除规则": "排除：" + "、".join(report.get("excluded_grades") or []) if report.get("excluded_grades") else "",
        "展示门槛指标": "退后线索",
        "门槛运算符": _select(">="),
        "门槛值": report.get("minimum_post_leads", 0),
        "过程指标（逐项勾选）": _business_metrics(profile, "process"),
        "过程指标展示顺序（选填）": profile["process"],
        "转化指标（逐项勾选）": _business_metrics(profile, "result"),
        "转化指标展示顺序（选填）": profile["result"],
        "过程重点提醒指标": _select("5min"),
        "转化重点提醒指标": _select("单效" if source.get("report_profile") == "supervisor-video49" else "截面单效"),
        "过程数据排序规则": process_sort,
        "转化数据排序规则": result_sort,
        "展示总计行": True,
        "图片分组与排版": layout,
        "颜色或样式参考": style,
        "过程提醒指标": "SUM(5min标记)/SUM(退后线索)" + reminder_suffix,
        "转化提醒指标": "SUM(净收款)/SUM(退后线索)（截面单效）" + reminder_suffix,
        "提醒对象": _select(mention),
        "播报层级": _select(mention),
        "过程文字提醒名次": _select(reminder_rank),
        "转化文字提醒名次": _select(reminder_rank),
        "过程指标提醒方向": _select("最低"),
        "转化指标提醒方向": _select("最低"),
        "并列处理": _select("全部提醒"),
        "@规则说明": "仅原生@唯一解析且已验证属于目标群的open_id；解析失败或成员不在群时阻断。",
        "过程消息文案模板": "🔥 **【{期次}】{渠道}渠道过程数据播报**",
        "转化消息文案模板": "🔥 **【{期次}】{渠道}渠道转化数据播报**",
        "无符合条件数据时": _select("跳过不发送"),
        "异常与重试要求": f"失败后每{schedule.get('retry_minutes', 2)}分钟重试至:{schedule.get('deadline_minute', 50):02d}；不盲目补发历史批次。",
        "运营备注": "由本地配置自动导入；修改运营需求后仍需技术评审并同步到受治理配置。" + weekend_note,
    }
    if config.get("adapter") == "market-channel-warning-v1":
        fields.update({
            "期望推送时段": "17:50",
            "展示门槛指标": "两期退后线索；转化另需两期收款大于0",
            "过程数据排序规则": "本期5min率降序；并列按主管名称",
            "转化数据排序规则": "本期截面单效降序；并列按主管名称",
            "图片分组与排版": "高中年级合并；每个指标合并表头下分指标值、较上期环比、较团队整体三列",
            "颜色或样式参考": "表头及团队整体蓝绿淡色；过程另有紫色外呼频次；图片无单位、无注释",
            "异常与重试要求": "每日只发送一次；无追加触发或错过补发；不确定发送留存台账等待核验",
            "运营备注": "团队整体按全部渠道高中线索的原始分子分母汇总；主管展示过滤不影响团队口径。",
        })
        # Above-team reminders use the reviewed technical rule. Legacy rank-select
        # options do not represent it; do not generate unsupported select values.
        for name in ("过程文字提醒名次", "转化文字提醒名次", "过程指标提醒方向", "转化指标提醒方向"):
            fields.pop(name, None)
    return {key: value for key, value in fields.items() if value is not None}


def _technical_record(channel_ref: str, config):
    domain, channel_id = channel_ref.split("/", 1)
    source = config.get("source", {})
    match = source.get("channel_match", {})
    report = config.get("report", {})
    schedule = config.get("schedule", {})
    sender = config.get("sender", {})
    target = (config.get("targets") or [{}])[0]
    upstream = config.get("upstream", {})
    config_path = CONFIG_ROOT / "departments" / domain / f"{channel_id}.json"
    task_enabled, task_state = _task_state(schedule.get("windows_task_name", ""))
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    fields = {
        "配置单ID": channel_ref,
        "记录类型": _select("本地渠道推送"),
        "实施状态": _select("已上线" if schedule.get("enabled") else "已暂停"),
        "domain": domain,
        "execution_surface": "local",
        "deployment_id": channel_id,
        "channel_ref": channel_ref,
        "channel_id": channel_id,
        "adapter": config.get("adapter", ""),
        "report_profile": source.get("report_profile", ""),
        "source_mode": source.get("source_mode", ""),
        "source_url": source.get("source_url", ""),
        "raw_source_url": source.get("raw_source_url", ""),
        "raw_table_id": source.get("raw_table_id", ""),
        "raw_table_name": source.get("raw_table_name", ""),
        "channel_match_field": match.get("field", ""),
        "channel_match_mode": match.get("match_mode", "values"),
        "channel_match_case_sensitive": bool(match.get("case_sensitive", False)),
        "channel_match_values": _compact(match.get("values") or {"keyword": match.get("keyword", "")}),
        "reminder_rule": source.get("reminder_rule", ""),
        "reminder_population": source.get("reminder_population", ""),
        "mention_target": source.get("mention_target", ""),
        "report_type": source.get("report_type", ""),
        "sender_identity": sender.get("identity", ""),
        "sender_name": sender.get("name", ""),
        "sender_open_id": sender.get("open_id", ""),
        "target_id": target.get("id", ""),
        "chat_id": target.get("chat_id", ""),
        "chat_display_name": target.get("display_name", ""),
        "target_enabled": bool(target.get("enabled", False)),
        "period_rule": report.get("period_rule", ""),
        "process_weekdays": _compact(report.get("process_weekdays", [])),
        "result_weekdays": _compact(report.get("result_weekdays", [])),
        "included_grades": _compact(report.get("included_grades", [])),
        "excluded_grades": _compact(report.get("excluded_grades", [])),
        "minimum_post_leads": report.get("minimum_post_leads", 0),
        "weekend_next_process_enabled": bool(report.get("weekend_next_process_enabled", False)),
        "weekend_next_process_minimum_post_leads": (
            report.get("weekend_next_process_minimum_post_leads", report.get("minimum_post_leads", 0))
            if report.get("weekend_next_process_enabled") else None),
        "schedule_enabled": bool(schedule.get("enabled", False)),
        "first_send_at": _datetime_cell(schedule.get("first_send_at", "")),
        "timezone": schedule.get("timezone", ""),
        "hours": _compact(schedule.get("hours", [])),
        "slot_reports": _compact(schedule.get("slot_reports", {})),
        "windows_task_name": schedule.get("windows_task_name", ""),
        "stagger_order": schedule.get("stagger_order", 0),
        "prepare_minute": schedule.get("prepare_minute", 0),
        "send_minute": schedule.get("send_minute", 0),
        "deadline_minute": schedule.get("deadline_minute", 0),
        "retry_minutes": schedule.get("retry_minutes", 0),
        "计划任务已启用": task_enabled,
        "计划任务状态": task_state,
        "base_identity": config.get("base_identity", ""),
        "verification_identity": config.get("verification_identity", ""),
        "state_dir": config.get("state_dir", ""),
        **_paths(domain, channel_id),
        "upstream_project_id": upstream.get("project_id", 0),
        "upstream_folder": upstream.get("folder", ""),
        "upstream_menu_id": upstream.get("menu_id", 0),
        "upstream_task_name": upstream.get("task_name", ""),
        "upstream_task_id": upstream.get("task_id", 0),
        "upstream_nezha_task_id": upstream.get("nezha_task_id", 0),
        "upstream_schedule_id": upstream.get("schedule_id", 0),
        "upstream_exec_file_id": upstream.get("exec_file_id", 0),
        "upstream_verified_version_id": upstream.get("verified_version_id", 0),
        "upstream_verified_source_sha256": upstream.get("verified_source_sha256", ""),
        "upstream_log_protocol": upstream.get("log_protocol", ""),
        "upstream_owner": upstream.get("owner", ""),
        "volume_report_json": _compact(config.get("volume_report", {})),
        "配置JSON快照": json.dumps(config, ensure_ascii=False, sort_keys=True, indent=2),
        "本地配置修改时间": datetime.fromtimestamp(config_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
        "最近导入时间": now,
        "源字段校验": _select("未校验"),
        "群及成员校验": _select("未校验"),
        "本地预览": _select("未验证"),
        "群内试发": _select("未试发"),
        "离线测试": _select("未验证"),
        "最终授权": _select("已授权" if schedule.get("enabled") else "未申请"),
        "实际上线时间": _datetime_cell(schedule.get("first_send_at", "")),
        "维护备注": "完整参数以本行配置JSON快照和本地受治理配置为准；Base不直接驱动生产任务。" + (
            f"周五至周日下一期过程主管退后线索≥{report.get('weekend_next_process_minimum_post_leads', report.get('minimum_post_leads'))}；"
            "本期转化沿用原门槛。" if report.get("weekend_next_process_enabled") else ""),
    }
    return {key: value for key, value in fields.items() if value is not None}


def export(mode: str, link_map):
    registry = _load(CONFIG_ROOT / "channels.json")
    records = []
    for channel_ref, relative_path in registry["channels"].items():
        config = _load(CONFIG_ROOT / relative_path)
        if mode == "operator":
            fields = _operator_record(channel_ref, config)
        else:
            fields = _technical_record(channel_ref, config)
            if link_map:
                record_id = link_map.get(channel_ref)
                if not record_id:
                    raise ValueError(f"link map is missing {channel_ref}")
                fields["关联运营申请"] = [{"id": record_id}]
        records.append(fields)
    return {"create_records": records}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("operator", "technical"), required=True)
    parser.add_argument("--link-map", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.mode == "technical" and args.link_map:
        link_map = _load(args.link_map)
    else:
        link_map = None
    payload = export(args.mode, link_map)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
