# data_lake_fuwu.dwd_crm_call_tmk_record_rt

## 1. 中文名称

先驱通话原始记录候选表（天工数据地图表 ID 34742；平台未提供中文名）。

## 2. 表用途

记录用户、顾问账号、呼叫时间、状态和通话时长等原始通话事件。该表是本地交接稿所写 dw_noumenon_crm.crm.dwd_crm_call_tmk_record_rt 经短名回退后在数据地图命中的候选物理表，但两者库名不同，不能直接视为同一张表。

## 3. 数据粒度

候选为通话事件粒度。数据地图提供 call_id，但尚未通过实际值验证唯一性、重复更新方式或删除语义。

## 4. 查询引擎

Presto。数据地图登记为 Iceberg 外表，Parquet 格式，Iceberg format-version 为 2。

## 5. 分区字段

无物理分区字段。查询必须用 call_time 业务事件窗口和必要的人群半连接限缩，避免无界扫描。

## 6. 强制范围限定字段

- 本表无 plan_id、predict_task_id、task_id 或 AI 场景字段，不能单表识别市场顾问策略 4235/4214，也不能按任务键关联触达表。
- call_type、call_status、data_source、scene_id 的实际枚举尚未验证。
- 交接稿候选接通条件 call_status = 33 只属于交接稿描述；实际值验证完成前不得提升为本表 confirmed contract。

## 7. 字段清单

字段、类型与说明由天工数据地图同步命令维护。

### 7.1 数据地图字段补充（2026-10-19）

> 来源：天工2数据地图字段信息。该补充段只补齐平台已登记字段、类型和字段说明；具体业务口径仍以本 Skill 已沉淀的 SQL 和指标规则为准。

| 字段名 | 类型 | 字段说明 | 常见用途 | 是否常用 |
|---|---|---|---|---|
| user_number | bigint | from deserializer | 数据地图补充 | 否 |
| email_prefix | string | from deserializer | 数据地图补充 | 否 |
| call_time | string | from deserializer | 数据地图补充 | 否 |
| call_duration | string | from deserializer | 数据地图补充 | 否 |
| call_status | int | from deserializer | 数据地图补充 | 否 |
| call_type | int | from deserializer | 数据地图补充 | 否 |
| call_url | string | from deserializer | 数据地图补充 | 否 |
| call_id | bigint | from deserializer | 数据地图补充 | 否 |
| data_source | string | from deserializer | 数据地图补充 | 否 |
| account_id | string | from deserializer | 数据地图补充 | 否 |
| scene_id | string | from deserializer | 数据地图补充 | 否 |

## 8. 常用过滤条件

- 使用 call_time 限定业务事件日或时间窗。
- 仅在受治理用户集合内按 user_number 半连接，不扫描全量用户。
- 不能把 call_status = 33 套到 one_dw.dwd_mkt_tmk_call_record_hf；后者当前数据地图字典的接通候选值为 1。

## 9. 常用 join key

- user_number 可候选关联触达 receiver_id，但单用户键无法证明某次通话属于策略 4235/4214。
- call_id 可候选关联好友 ODS call_id，需先验证类型、覆盖率和唯一性。
- 本表缺少 predict_task_id，不能执行交接稿要求的 outer_channel_task_id = predict_task_id 任务桥。

## 10. 常用 SQL 片段

正式 SQL 尚不可生成。先对受限业务事件窗验证查询权限、call_status/call_type/data_source/scene_id 分布和 call_id 唯一性。

## 11. 注意事项

- 数据地图对交接稿三段名精确搜索无结果，短名搜索命中 data_lake_fuwu.dwd_crm_call_tmk_record_rt。库名漂移和字段缺失都必须保留为未决项。
- 本表不能替代已登记的 one_dw.dwd_mkt_tmk_call_record_hf 完成策略任务 Join；后者有 predict_task_id，本表没有。
- 通话 URL 和用户/顾问标识属于敏感明细，知识库不保存样例值。

## 12. 数据地图探查记录（2026-10-19）

- 通过 usql-web-query-operator sync-datamap-fields 使用交接稿表名检索；精确三段名未命中，短名回退唯一命中 data_lake_fuwu.dwd_crm_call_tmk_record_rt，表 ID 34742，项目“数据湖-服务域”。
- 数据地图返回 11 个普通字段、0 个分区字段；平台登记为在线 Iceberg 外表、Parquet 格式。
- 表元数据创建时间为 2026-03-31 10:44:56，更新时间为 2026-05-07 12:01:18；这些不是最新业务事件时间。
- 本次登记只固化物理字段和不可用边界，不确认交接稿库名映射或接通枚举。
- 2026-10-19 实际值 Probe 被平台以“无查询权限”阻断，未生成 Query ID。需要申请 data_lake_fuwu.dwd_crm_call_tmk_record_rt 查询权限后再验证 call_status=33、时长、call_id 唯一性和好友 ODS 桥。
