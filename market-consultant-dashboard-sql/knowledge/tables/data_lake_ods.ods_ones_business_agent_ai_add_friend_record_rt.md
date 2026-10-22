# data_lake_ods.ods_ones_business_agent_ai_add_friend_record_rt

## 1. 中文名称

添加好友记录（天工数据地图表 ID 36507）。

## 2. 表用途

记录 AI 外呼关联任务、用户、顾问及加好友状态，是市场顾问 AI 自动加好友场景“AI好友率”分子的候选事件源。

本表只提供好友事件及状态，不提供渠道、经理、主管、伙伴组织名称、线索 ID 或触达分母。正式指标必须先从已确认策略 plan_id IN (4235, 4214) 的触达用户集合进入，再按任务和用户双键半连接本表。

## 3. 数据粒度

候选为添加好友记录事件粒度。数据地图提供主键 id，但尚未实测其唯一性；同一 task_id + user_id 可能存在多条状态变化记录，计算好友用户数时应先按目标状态去重，不能直接使用 COUNT(*)。

## 4. 查询引擎

Presto。数据地图登记为 Iceberg 外表、Parquet 格式，Iceberg format-version 为 2。

## 5. 分区字段

无物理分区字段。数据地图登记为全量表，保留期 9999 天。每次查询必须使用触达任务集合半连接缩小范围，并按 create_time / update_time 限定业务窗口或探查时效，避免无界全表扫描。

## 6. 强制范围限定字段

- AI 加好友成功候选条件为 status = 2，数据地图说明为“已加好友”。
- 市场顾问当前确认策略为触达表 plan_id IN (4235, 4214)；本表没有 plan_id，必须由受限触达任务集合传入 task_id + user_id。
- is_del = 0 是否必须作为有效记录条件，交接稿未锁定，投入生产前需定向对账。
- 不得只按 task_id 关联。已验证每个策略单日可只有一个外部任务而覆盖大量用户，必须同时使用 user_id。

## 7. 字段清单

字段、类型与说明由天工数据地图同步命令维护。

### 7.1 数据地图字段补充（2026-10-19）

> 来源：天工2数据地图字段信息。该补充段只补齐平台已登记字段、类型和字段说明；具体业务口径仍以本 Skill 已沉淀的 SQL 和指标规则为准。

| 字段名 | 类型 | 字段说明 | 常见用途 | 是否常用 |
|---|---|---|---|---|
| id | bigint | 主键id | 数据地图补充 | 否 |
| call_id | string | 外呼id | 数据地图补充 | 否 |
| task_id | bigint | 任务id | 数据地图补充 | 否 |
| user_id | bigint | 用户id | 数据地图补充 | 否 |
| account_id | bigint | 顾问id | 数据地图补充 | 否 |
| status | int | 0未发送,1已发送,2已加好友 | 数据地图补充 | 否 |
| create_time | timestamp | 创建时间 | 数据地图补充 | 否 |
| update_time | timestamp | 更新时间 | 数据地图补充 | 否 |
| is_del | int | 0:有效 1:无效 | 数据地图补充 | 否 |
| ali_unique_id | string | 阿里唯一id | 数据地图补充 | 否 |
| open_session | int | 是否已开启会话：0=未开启, 1=已开启 | 数据地图补充 | 否 |
| source_type | int | 回调来源:1=阿里机器人,2=呼叫中心 | 数据地图补充 | 否 |

## 8. 常用过滤条件

- AI 好友成功候选：status = 2。
- 时效探查：按 create_time 或 update_time 限定近期窗口并读取最大时间。
- 生产范围：先构造 plan_id IN (4235, 4214)、scene_code = 'ai_call_auto_add_friend'、reach_type = 25 的触达任务-用户集合，再半连接本表。
- 数据地图定义 source_type=1 为阿里机器人、2 为呼叫中心；不得套用交接稿中“2私海全AI、3公海全AI”的另一套枚举。

## 9. 常用 join key

- task_id = fairy_data_center.dwd_service_reach_wide_channel_subtask_prod_v2_di.outer_channel_task_id，需统一为 bigint。
- user_id = fairy_data_center.dwd_service_reach_wide_channel_subtask_prod_v2_di.receiver_id，需统一为 bigint。
- 推荐以 task_id + user_id 双键关联。单任务键在已确认策略下会造成大量用户之间的多对多放大。
- call_id 可作为通话事件候选桥，但唯一性及与先驱通话表的覆盖率尚未实测。
- account_id 是顾问 ID，不等同于市场顾问组织架构中的姓名或邮箱字段；需要受治理员工维桥。

## 10. 常用 SQL 片段

正式 SQL 尚需验证 is_del、重复状态记录和时间窗。候选好友分子为在受限触达任务集合内筛选 status = 2，并按 task_id + user_id 去重。

## 11. 注意事项

- AI好友率分母是受限策略下挂线索后的去重 AI 外呼线索，不是本表总用户数，也不是接通用户数。
- 数据地图与本地交接稿对 source_type 的枚举说明冲突。未完成实际值与上游配置对账前，不用该字段拆分私海/公海或机器人来源。
- status=2 来自数据地图和交接稿的一致说明，但删除/失效记录是否需叠加 is_del=0 仍待确认。
- 无分区表禁止无界扫描；优先使用已确认策略任务集合进行动态过滤。
- 知识库不保存用户、顾问或会话明细样例。

## 12. 数据地图探查记录（2026-10-19）

- 通过 usql-web-query-operator sync-datamap-fields 实时命中完整表 data_lake_ods.ods_ones_business_agent_ai_add_friend_record_rt，中文名“添加好友记录”，表 ID 36507，项目“数据湖ods层”。
- 数据地图当前返回 12 个普通字段、0 个分区字段；平台登记为在线 Iceberg 外表、Parquet 格式、全量表、保留9999天。
- 表元数据创建与更新时间均登记为 2026-08-05 17:44:31；该时间不是最新好友业务事件时间，后续通过事件时间 Probe 验证时效。
- 本次登记只固化物理字段、候选关联和明确冲突，不把交接稿自动升级为 confirmed contract。
- 2026-10-19 事件时效 Probe 在提交阶段被平台以“无查询权限”阻断，未生成 Query ID；用户已发起权限申请。审批完成前，status、is_del、source_type、重复度和双键 Join 均不得声称已实际验证。
