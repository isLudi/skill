# service_dw.ods_service_ai_ones_business_copilot__call_record_df

## 1. 中文名称

AI 途途通话记录表（天工数据地图表 ID `26754`）。

## 2. 表用途

保存通话事件、用户、员工、通话时间、时长和录音 URL。数据地图将其标为 Hive 全量表，保留期 30 天。

## 3. 数据粒度

待实测确认。数据地图描述 `unique_key` 为唯一标识，同时另有 `call_id`、`id`；这些字段在分区内的唯一性及关系需实测。

## 4. 查询引擎

Presto。

## 5. 分区字段

`dt` 为天级快照分区。`call_time` 为字符串形式的通话开始时间；事件窗口与快照时间应分别限定。

## 6. 强制范围限定字段

数据地图未列出部门字段。市场顾问取数应以已限定的业务人群按 `user_number` 半连接，并保留具体 `dt`、通话时间窗口。

## 7. 字段清单

字段、类型与描述由天工数据地图同步命令维护。

### 7.1 数据地图字段补充（2026-09-17）

> 来源：天工2数据地图字段信息。该补充段只补齐平台已登记字段、类型和字段说明；具体业务口径仍以本 Skill 已沉淀的 SQL 和指标规则为准。

| 字段名 | 类型 | 字段说明 | 常见用途 | 是否常用 |
|---|---|---|---|---|
| dt | string | 天级别分区 yyyyMMdd | 数据地图补充 | 否 |
| id | bigint | ID,id,id | 数据地图补充 | 否 |
| unique_key | string | 唯一标识,unique_key,unique_key | 数据地图补充 | 否 |
| user_number | bigint | 用户id,用户id,用户id | 数据地图补充 | 否 |
| email_prefix | string | 邮箱前缀,邮箱前缀,邮箱前缀 | 数据地图补充 | 否 |
| call_time | string | 通话开始时间,通话开始时间,通话开始时间 | 数据地图补充 | 否 |
| call_duration | bigint | 通话时长,通话时长,通话时长 | 数据地图补充 | 否 |
| call_status | bigint | 通话状态,通话状态,通话状态 | 数据地图补充 | 否 |
| call_type | bigint | 呼入呼出,呼入呼出,呼入呼出 | 数据地图补充 | 否 |
| call_phone_number | string | 手机号,手机号,手机号 | 数据地图补充 | 否 |
| call_url | string | 录音,录音,录音 | 数据地图补充 | 否 |
| call_id | string | 记录id,记录id,记录id | 数据地图补充 | 否 |
| from_username | string | from_username,from_username,from_username | 数据地图补充 | 否 |
| to_username | string | to_username,to_username,to_username | 数据地图补充 | 否 |
| account_id | bigint | 员工,员工,account_id | 数据地图补充 | 否 |
| data_source_type | bigint | 上报来源（枚举）,上报来源（枚举）,上报来源（枚举） | 数据地图补充 | 否 |
| msg_type | bigint | 消息类型（枚举）,消息类型（枚举）,消息类型（枚举） | 数据地图补充 | 否 |
| create_time | string | 创建时间,创建时间,创建时间 | 数据地图补充 | 否 |
| update_time | string | 更新时间,更新时间,更新时间 | 数据地图补充 | 否 |
| is_del | bigint | 是否删除,是否删除,是否删除,是否删除 | 数据地图补充 | 否 |
| data_source_type_merged | bigint | 上报来源（合并）,上报来源（合并） | 数据地图补充 | 否 |

## 8. 常用过滤条件

用户提供的预期 SQL 使用 `dt`、`substr(call_time,1,10)` 时间窗口及市场顾问线索用户集合。`is_del` 是否纳入有效通话条件待业务确认。

## 9. 常用 join key

- 候选：`dt + call_id` 关联 AI 通话分析结果。
- 候选：`call_url` 关联 ASR 的 `origin_file_url`。
- `user_number` 可对齐已限定线索用户，但一名用户可有多条线索或通话，不可据此认定一对一。

## 10. 常用 SQL 片段

暂无经过市场顾问人群范围和关联基数验证的可复用生产 SQL；候选关联和探查结果见 `knowledge/joins/ai_call_asr_relationship.md`。

## 11. 注意事项

- `call_url` 和手机号属于敏感信息，知识库只保存聚合探查结果。
- 关联 AI/ASR 前应先核查下游键重复，否则 `COUNT(*)`、`SUM(call_duration)` 与 `ARRAY_AGG` 会被放大。

## 12. 分区与关联探查（2026-09-17）

- `dt='20260915'` 全表 81,108,669 行（Query `1591083960`）；该数不是市场顾问部通话量。
- 附件关联条件的物理诊断样本限定 `dt='20260915'`、`call_time` 日期为 `2026-09-15`、`user_number IS NOT NULL` 且 `mod(user_number,1000)=0`，共 88 条通话、88 个不同 `call_id`，没有空 `call_id` 或空 `call_url`（Query `1591086950`）。样本未限定市场顾问部门，不能外推覆盖率或唯一性。
- 同一探针中，AI 结果与 ASR 都命中 88 条通话；3 条通话匹配多条 ASR，直接关联后的样本时长从 7,887 秒增至 9,484 秒，放大 1,597 秒（约 20.25%）。电话数、录音数、AI 概要数和 JSON 数组同样有放大风险；生产聚合须先确定 ASR 每 URL 的取舍规则并复验。
