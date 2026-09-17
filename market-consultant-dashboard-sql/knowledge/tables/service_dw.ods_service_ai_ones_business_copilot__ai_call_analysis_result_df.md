# service_dw.ods_service_ai_ones_business_copilot__ai_call_analysis_result_df

## 1. 中文名称

语音分析结果表（天工数据地图表 ID `27200`）。

## 2. 表用途

保存通话主题、抗性点、概要和分析状态等结果。数据地图将其标为 Hive 全量表，保留期 30 天。

## 3. 数据粒度

待实测确认。数据地图描述 `id` 为唯一编号，另有 `call_id`；同一通话是否有多条有效分析结果需要分区实测。

## 4. 查询引擎

Presto。

## 5. 分区字段

`dt` 为天级快照分区；与通话记录关联时先限定两表快照分区。

## 6. 强制范围限定字段

数据地图未列出部门字段。市场顾问范围应从已限定的通话记录传递，不应直接把此表所有分析结果计入市场顾问。

## 7. 字段清单

字段、类型与描述由天工数据地图同步命令维护。

### 7.1 数据地图字段补充（2026-09-17）

> 来源：天工2数据地图字段信息。该补充段只补齐平台已登记字段、类型和字段说明；具体业务口径仍以本 Skill 已沉淀的 SQL 和指标规则为准。

| 字段名 | 类型 | 字段说明 | 常见用途 | 是否常用 |
|---|---|---|---|---|
| dt | string | 天级别分区 yyyyMMdd | 数据地图补充 | 否 |
| id | bigint | ID,ID,唯一编号 | 数据地图补充 | 否 |
| call_id | string | 通话ID,通话ID | 数据地图补充 | 否 |
| create_time | string | 创建时间,创建时间 | 数据地图补充 | 否 |
| update_time | string | 修改时间,修改时间 | 数据地图补充 | 否 |
| is_del | bigint | 已删除,数据是否已被删除,已删除,数据是否已被删除 | 数据地图补充 | 否 |
| call_target | string | 沟通对象,沟通对象 | 数据地图补充 | 否 |
| call_topic | string | 通话主题,通话主题 | 数据地图补充 | 否 |
| user_resistance_points | string | 用户抗性点,用户抗性点 | 数据地图补充 | 否 |
| follow_up_item | string | 待跟进项,待跟进项 | 数据地图补充 | 否 |
| call_summary | string | 通话概要,通话概要 | 数据地图补充 | 否 |
| asr_text | string | ASR原文,ASR原文 | 数据地图补充 | 否 |
| dialogue_text | string | 对话文本,对话文本 | 数据地图补充 | 否 |
| analysis_status | bigint | 分析状态,分析状态 | 数据地图补充 | 否 |
| callback_time_consumption | bigint | 分析回调耗时,分析回调耗时 | 数据地图补充 | 否 |
| single_select | bigint | 是否违规 | 数据地图补充 | 否 |

## 8. 常用过滤条件

用户提供的预期 SQL 取 `is_del = 0` 的分析结果。数据地图字段类型为 `bigint`，SQL 中应使用数值 `0`；是否还需限定 `analysis_status` 待业务确认。

## 9. 常用 join key

候选：`dt + call_id` 关联通话记录。分区内有效 `call_id` 若重复，直接 `LEFT JOIN` 将放大通话记录和时长。

## 10. 常用 SQL 片段

暂无经过市场顾问人群范围和关联基数验证的可复用生产 SQL；候选关联和探查结果见 `knowledge/joins/ai_call_asr_relationship.md`。

## 11. 注意事项

- `call_summary`、`asr_text`、`dialogue_text` 是原文或概要，知识库只保存聚合统计。
- `asr_text` 与独立 ASR 表 `parsed_content` 的一致性尚未验证，不应混用。

## 12. 分区与关联探查（2026-09-17）

- `dt='20260915'` 全表 69,375,212 行（Query `1591083960`）；该数不是市场顾问部 AI 概要数。
- 按附件条件 `dt + call_id` 且 `is_del=0`，受限的 88 条通话样本均匹配一条 AI 结果，没有多匹配（Query `1591086950`）。仅证明此诊断样本，没有证明整个分区的 `call_id` 唯一。
- 数据地图确认 `is_del` 是 `bigint`；附件写法 `is_del = '0'` 应改为数值比较 `is_del = 0`。`analysis_status` 是否也是有效结果门槛仍待确认。
