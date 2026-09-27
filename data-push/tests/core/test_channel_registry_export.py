import importlib.util
import json
from pathlib import Path
from unittest.mock import patch


SKILL_ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "channel_registry_export",
    SKILL_ROOT / "scripts" / "export_channel_registry_records.py",
)
EXPORTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EXPORTER)


def _by_id(payload, field):
    return {record[field]: record for record in payload["create_records"]}


def test_operator_export_covers_registry_and_uses_business_calendar():
    records = _by_id(EXPORTER.export("operator", None), "申请编号")
    assert len(records) == len(EXPORTER._load(EXPORTER.CONFIG_ROOT / "channels.json")["channels"])
    zhu = records["market_consultant/supervisor_zhu_doctor_video49"]
    assert zhu["申请部门"] == ["市场顾问部"]
    assert zhu["渠道标准名称"] == "朱博士"
    assert zhu["渠道匹配方式"] == ["名称包含"]
    assert zhu["过程数据星期"] == ["周一", "周二", "周三", "周四"]
    assert zhu["转化数据星期"] == ["周五", "周六", "周日"]
    assert zhu["门槛值"] == 1
    assert zhu["数据维度"] == ["期次", "渠道", "年级", "负责人", "主管", "顾问"]
    assert "顾问" in zhu["过程指标展示顺序（选填）"]
    assert "人均报科" in zhu["转化指标（逐项勾选）"]
    assert "顾问" not in zhu["过程指标（逐项勾选）"]
    assert zhu["过程重点提醒指标"] == ["5min"]
    assert zhu["转化重点提醒指标"] == ["单效"]
    assert zhu["过程指标提醒方向"] == ["最低"]
    assert zhu["转化指标提醒方向"] == ["最低"]
    assert zhu["播报层级"] == ["顾问"]
    assert zhu["过程文字提醒名次"] == ["最低值"]
    assert zhu["转化文字提醒名次"] == ["最低值"]
    chen = records["market_consultant/supervisor_chenruichun"]
    assert chen["渠道标准名称"] == "陈瑞春"
    assert chen["渠道匹配方式"] == ["名称包含"]
    assert chen["数据维度"] == ["期次", "渠道", "年级", "负责人", "主管", "顾问"]
    assert chen["门槛值"] == 1
    advisor = records["market_consultant/supervisor_yafei_grade_9_advisor"]
    assert advisor["渠道标准名称"] == "亚飞B站初三顾问"
    assert advisor["门槛值"] == 5
    assert advisor["提醒对象"] == ["顾问"]
    assert advisor["过程文字提醒名次"] == ["底部10%（每年级至少1名）"]
    assert advisor["转化文字提醒名次"] == ["底部10%（每年级至少1名）"]
    assert advisor["数据维度"] == ["期次", "渠道", "年级", "负责人", "主管", "顾问"]
    assert advisor["转化指标展示顺序（选填）"] == "期次、负责人、主管、顾问、退后线索、5min、双沟率、首节到课率、当期单效、截面单效"
    assert "5min使用橙色色块" in advisor["颜色或样式参考"]


def test_technical_export_preserves_full_config_and_link_mapping():
    link_map = {
        ref: f"rec_{index}"
        for index, ref in enumerate(EXPORTER._load(EXPORTER.CONFIG_ROOT / "channels.json")["channels"], 1)
    }
    with patch.object(EXPORTER, "_task_state", return_value=(True, "Ready")):
        records = _by_id(EXPORTER.export("technical", link_map), "配置单ID")
    assert len(records) == len(EXPORTER._load(EXPORTER.CONFIG_ROOT / "channels.json")["channels"])
    zhu = records["market_consultant/supervisor_zhu_doctor_video49"]
    assert zhu["domain"] == "market_consultant"
    assert zhu["minimum_post_leads"] == 1
    assert zhu["计划任务已启用"] is True
    assert zhu["关联运营申请"] == [{"id": link_map[zhu["配置单ID"]]}]
    assert '"channel_id": "supervisor_zhu_doctor_video49"' in zhu["配置JSON快照"]
    chen = records["market_consultant/supervisor_chenruichun"]
    assert '"channel_id": "supervisor_chenruichun"' in chen["配置JSON快照"]
    assert json.loads(chen["配置JSON快照"])["schedule"]["enabled"] is True
    assert chen["计划任务已启用"] is True
    advisor = records["market_consultant/supervisor_yafei_grade_9_advisor"]
    assert advisor["minimum_post_leads"] == 5
    assert advisor["schedule_enabled"] is True
    assert advisor["关联运营申请"] == [{"id": link_map[advisor["配置单ID"]]}]
