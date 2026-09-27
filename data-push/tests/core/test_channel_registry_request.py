import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "read_channel_registry_request.py"
SPEC = importlib.util.spec_from_file_location("read_channel_registry_request", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def test_candidate_projection_stays_below_lark_limit():
    assert len(MODULE.CANDIDATE_FIELDS) <= 50
    assert len(MODULE.CANDIDATE_FIELDS) == len(set(MODULE.CANDIDATE_FIELDS))


def test_build_candidate_normalizes_base_markdown_url():
    candidate = MODULE.build_candidate({
        "申请编号": "market_consultant/url",
        "申请部门": ["市场顾问部"],
        "渠道标准名称": "链接示例",
        "数据源链接": "[https://example.invalid/base](https://example.invalid/base)",
        "原始表名称": "原始数据",
        "目标群": [{"id": "oc_example"}],
        "期次规则": ["自然日日期"],
        "数据维度": ["顾问"],
        "过程指标（逐项勾选）": ["退后线索"],
    }, record_id="rec_url")

    assert candidate["business"]["data_source_url"] == "https://example.invalid/base"


def test_build_candidate_keeps_department_metrics_and_stable_chat_id():
    candidate = MODULE.build_candidate({
        "申请编号": "qingcheng/example",
        "申请状态": ["待技术评审"],
        "申请部门": ["青橙项目部"],
        "渠道标准名称": "青橙示例",
        "数据源链接": "https://example.invalid/base",
        "原始表名称": "原始数据",
        "目标群": [{"id": "oc_example"}],
        "期次规则": ["自然日日期"],
        "过程数据星期": ["周一", "周三"],
        "转化数据星期": ["周五"],
        "期望推送时段": "09:00",
        "数据维度": ["期次", "顾问"],
        "年级范围": ["不限"],
        "过程指标（逐项勾选）": ["实际进量", "量级完成度"],
        "转化指标（逐项勾选）": [],
        "过程重点提醒指标": ["量级完成度"],
        "提醒对象": ["顾问"],
        "过程指标提醒方向": ["最低"],
        "播报层级": ["顾问"],
        "过程文字提醒名次": ["最后1名"],
        "转化文字提醒名次": ["不适用"],
    }, record_id="rec_example")

    assert candidate["routing"]["domain"] == "qingcheng"
    assert candidate["business"]["target_chat_id"] == "oc_example"
    assert candidate["report"]["process_metrics"] == ["实际进量", "量级完成度"]
    assert candidate["reminder"]["process_metric"] == "量级完成度"
    assert candidate["reminder"]["report_level"] == "顾问"
    assert candidate["reminder"]["process_rank"] == "最后1名"
    assert candidate["reminder"]["result_rank"] == "不适用"
    assert candidate["reminder"]["process_direction"] == "最低"
    assert candidate["reminder"]["result_direction"] is None
    assert candidate["validation"]["complete_for_technical_review"] is True


def test_build_candidate_reports_missing_business_fields_without_inventing_defaults():
    candidate = MODULE.build_candidate({
        "申请编号": "market_consultant/incomplete",
        "申请部门": ["市场顾问部"],
        "渠道标准名称": "未完成渠道",
    }, record_id="rec_incomplete")

    assert candidate["routing"]["domain"] == "market_consultant"
    assert candidate["routing"]["execution_surface"] is None
    assert candidate["routing"]["channel_id"] is None
    assert candidate["validation"]["complete_for_technical_review"] is False
    assert "目标群" in candidate["validation"]["missing_business_fields"]
