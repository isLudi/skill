# fairy_data_center.dwd_service_reach_wide_channel_subtask_prod_v2_di

## 1. 中文名称

触达发送明细宽表（天工数据地图表 ID `35146`）。

## 2. 表用途

以通道子任务（`channel_subtask`）为粒度，聚合触达链路全生命周期数据，包含任务状态、发送/接收人、通道内容、场景策略、目标达成及业务字段，用于触达效果分析和发送质量监控。

本表可作为 `scene_code = 'ai_call_auto_add_friend'`、`reach_type = 25` 场景的 AI 外呼触达候选底表。本次仅登记物理结构和候选用途；市场顾问人群范围、线索挂接、接通及好友指标仍需由业务契约和关联表确认。

## 3. 数据粒度

通道子任务粒度。数据地图描述以 `channel_subtask` 为粒度；`channel_subtask_id` 的分区内及跨分区唯一性仍需实测。

## 4. 查询引擎

Presto。数据地图存储类型为 Hive 内表、Parquet 格式。

## 5. 分区字段

`dt` 为按 `create_time` 生成的天级增量分区，格式 `yyyyMMdd`。数据地图登记为增量表，保留期 730 天。事件时间分析还应按业务需求限定 `trigger_time`、`actual_send_time` 或 `finish_time`，不可只用分区替代业务时间。

## 6. 强制范围限定字段

市场顾问 AI 外呼探查至少限定具体 `dt` 范围、`scene_code = 'ai_call_auto_add_friend'` 和 `reach_type = 25`。交接稿将 `channel_subtask_status IN (3, 4)` 作为包含失败尝试的候选触达范围，但状态枚举及生产适用性尚未在本 Skill 中确认为可执行契约。

本表没有市场顾问部门、渠道、经理、主管、伙伴或 `lead_id` 字段；必须先由已限定的市场顾问线索人群关联，不得把全表触达量直接解释为市场顾问指标。

## 7. 字段清单

字段、类型与说明由天工数据地图同步命令维护。

### 7.1 数据地图字段补充（2026-10-16）

> 来源：天工2数据地图字段信息。该补充段只补齐平台已登记字段、类型和字段说明；具体业务口径仍以本 Skill 已沉淀的 SQL 和指标规则为准。

| 字段名 | 类型 | 字段说明 | 常见用途 | 是否常用 |
|---|---|---|---|---|
| dt | string | 日期分区, 格式yyyyMMdd | 数据地图补充 | 否 |
| channel_subtask_id | bigint | 通道子任务ID | 数据地图补充 | 否 |
| channel_task_id | bigint | 通道任务ID | 数据地图补充 | 否 |
| notice_subtask_id | bigint | 通知子任务ID | 数据地图补充 | 否 |
| notice_task_id | bigint | 通知任务ID | 数据地图补充 | 否 |
| notice_timed_task_id | bigint | 通知定时任务ID | 数据地图补充 | 否 |
| outer_channel_task_id | string | 外部通道关联ID | 数据地图补充 | 否 |
| channel_subtask_status | string | 通道子任务状态 | 数据地图补充 | 否 |
| status_detail | string | 状态明细 | 数据地图补充 | 否 |
| fail_reason | string | 失败原因 | 数据地图补充 | 否 |
| trigger_time | string | 业务事件触发时间 | 数据地图补充 | 否 |
| task_create_time | string | 任务创建时间 | 数据地图补充 | 否 |
| expect_send_time | string | 预期发送时间 | 数据地图补充 | 否 |
| actual_send_time | string | 下发通道时间 | 数据地图补充 | 否 |
| finish_time | string | 任务完成时间 | 数据地图补充 | 否 |
| send_type | string | 发送人类型(0自动 1手动) | 数据地图补充 | 否 |
| sender_id | bigint | 发送人ID | 数据地图补充 | 否 |
| sender_account | string | 发送人账号 | 数据地图补充 | 否 |
| sender_name | string | 发送人姓名 | 数据地图补充 | 否 |
| receiver_type | string | 接收人类型 | 数据地图补充 | 否 |
| receiver_id | string | 接收人ID | 数据地图补充 | 否 |
| receiver_account | string | 受众账号 | 数据地图补充 | 否 |
| receiver_name | string | 受众姓名 | 数据地图补充 | 否 |
| reach_type | int | 触达方式 | 数据地图补充 | 否 |
| reach_type_name | string | 触达方式名称 | 数据地图补充 | 否 |
| channel_account | string | 三方通道账户 | 数据地图补充 | 否 |
| template_id | string | 模版ID | 数据地图补充 | 否 |
| template_content | string | 模板内容 | 数据地图补充 | 否 |
| msg_content | string | 发送内容 | 数据地图补充 | 否 |
| scene_id | int | 场景ID | 数据地图补充 | 否 |
| scene_code | string | 场景编码 | 数据地图补充 | 否 |
| scene_name | string | 场景名称(三级用-隔开) | 数据地图补充 | 否 |
| plan_id | int | 策略ID | 数据地图补充 | 否 |
| plan_name | string | 策略名称 | 数据地图补充 | 否 |
| anchor_code | string | 发布入口 | 数据地图补充 | 否 |
| publish_record_id | int | 手动通知ID | 数据地图补充 | 否 |
| reach_goal | int | 目标类型 | 数据地图补充 | 否 |
| reach_goal_name | string | 目标名称 | 数据地图补充 | 否 |
| reach_goal_status | int | 目标完成状态(0处理中 1已完成 2未完成) | 数据地图补充 | 否 |
| reach_goal_finish_time | string | 目标完成时间 | 数据地图补充 | 否 |
| biz_id | string | 业务ID(预留) | 数据地图补充 | 否 |
| clazz_number | string | 班级编号 | 数据地图补充 | 否 |
| clazz_lesson_number | string | 课节编号 | 数据地图补充 | 否 |
| subclazz_number | string | 辅导班编号 | 数据地图补充 | 否 |
| order_number | bigint | 订单编号 | 数据地图补充 | 否 |
| voice_url | string | 语音文件地址(预留) | 数据地图补充 | 否 |
| duration | bigint | 接听时长 | 数据地图补充 | 否 |
| course_department_ids | string | 课程部门层级ID列表(逗号分隔) | 数据地图补充 | 否 |
| course_department_names | string | 课程部门层级名称列表(逗号分隔) | 数据地图补充 | 否 |
| create_time | string | 创建时间 | 数据地图补充 | 否 |
| update_time | string | 更新时间 | 数据地图补充 | 否 |

## 8. 常用过滤条件

- AI 自动加好友场景候选：`scene_code = 'ai_call_auto_add_friend' AND reach_type = 25`。
- 交接稿候选触达尝试：`channel_subtask_status IN (3, 4)`，包含失败尝试；投入生产前需确认状态枚举。
- 每个物理扫描保留明确 `dt` 范围；按事件时间统计时同时限定对应时间字段。

## 9. 常用 join key

- `receiver_id` 是接收人 ID，可作为 `user_id` 的候选桥接键；同一用户可能对应多条线索，必须通过班级及时间规则消歧，不能直接假定一对一。
- `outer_channel_task_id` 是外部通道关联 ID。交接稿候选链路为先驱通话表 `predict_task_id` 及 AI 加好友 ODS 表 `task_id`，不得改用先驱通话表自身的 `task_id`。
- `clazz_number` 可作为用户挂线索时的班级辅助键；具体“同用户同班取最新、同用户最近兜底”规则来自本地交接稿，尚未登记为市场顾问 confirmed contract。

## 10. 常用 SQL 片段

暂无可直接执行的市场顾问生产 SQL。候选底表过滤如下，实际查询还必须补充市场顾问人群、时间、关联基数及去重规则：

```sql
FROM fairy_data_center.dwd_service_reach_wide_channel_subtask_prod_v2_di
WHERE dt BETWEEN '<start_yyyymmdd>' AND '<end_yyyymmdd>'
  AND scene_code = 'ai_call_auto_add_friend'
  AND reach_type = 25
  AND channel_subtask_status IN ('3', '4')
```

## 11. 注意事项

- 本表粒度是通道子任务，不是线索；外呼尝试次数与 AI 外呼线索数必须分别聚合，避免把任务行数当线索数。
- `duration` 的数据地图说明为接听时长，但交接稿明确 AI 接通应由 `dw_noumenon_crm.crm.dwd_crm_call_tmk_record_rt.call_status = 33` 判定。未完成先驱表关联基数和时长一致性验证前，不以本表 `duration` 单独固化 AI 接通率或例均接通时长。
- AI 好友率的分子不在本表。交接稿指定 `data_lake_ods.ods_ones_business_agent_ai_add_friend_record_rt.status = 2`，通过 `task_id = outer_channel_task_id` 关联；该本地稿是候选业务证据，不自动升级为市场顾问 confirmed contract。
- 渠道、经理、主管、伙伴及总线索底座不在本表。候选维度来自市场顾问线索全链路数据或受治理架构表，需按目标看板的人群和时间截面另行确认。
- `receiver_account`、`channel_account`、消息内容和语音 URL 可能包含敏感信息，知识库不保存样例值或明细结果。

## 12. 数据地图探查记录（2026-10-16）

- 通过 `usql-web-query-operator sync-datamap-fields` 实时刷新并命中表，数据地图名称为“触达发送明细宽表”，表 ID `35146`，项目“运营工作台数据中心”，当前登记为在线 Hive 内表。
- 数据地图当前返回 50 个普通字段及 1 个 `dt` 分区字段；表用途描述中的“47 个维度”是平台描述文本，不作为当前字段总数。本次探查只读取表结构，没有执行 SQL、下载明细或修改远端平台。
- 数据地图记录的创建时间为 `2026-05-06 17:19:34`、更新时间为 `2026-05-07 12:01:21`；这些是平台表元数据时间，不代表数据最新业务日期。
- 本地交接稿 `D:/Feishu/给伙伴_产出逻辑与SQL_看板加好友块_20260813.md` 用于识别候选场景过滤、任务桥和指标边界；因其不属于本 Skill 的已确认契约，本文保留所有未验证项。
