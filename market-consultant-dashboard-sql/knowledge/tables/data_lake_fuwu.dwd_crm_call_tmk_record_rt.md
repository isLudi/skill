# data_lake_fuwu.dwd_crm_call_tmk_record_rt

## 1. 中文名称

先驱通话原始记录候选表（天工数据地图表 ID 34742；平台未提供中文名）。

## 2. 表用途

记录用户、顾问账号、呼叫时间、状态和通话时长等原始通话事件。该表是本地交接稿所写 dw_noumenon_crm.crm.dwd_crm_call_tmk_record_rt 经短名回退后在数据地图命中的候选物理表，但两者库名不同，不能直接视为同一张表。

## 3. 数据粒度

通话事件粒度。第 13 节的受限样本中，`call_id` 在原始表时间窗内一通一条，重复更新和删除语义仍需按实际扫描范围检查。

## 4. 查询引擎

Presto。数据地图登记为 Iceberg 外表，Parquet 格式，Iceberg format-version 为 2。

## 5. 分区字段

无物理分区字段。查询必须用 call_time 业务事件窗口和必要的人群半连接限缩，避免无界扫描。

## 6. 强制范围限定字段

- AI 范围由[市场顾问触达策略](fairy_data_center.dwd_service_reach_wide_channel_subtask_prod_v2_di.md)和 `one_dw` 的任务学员双键确定，随后按 `call_id` 读取原始通话。原始表只提供逐通属性。
- 已对账的 AI 样本中，原始 `call_status=33` 对应 `one_dw.call_status=1`，原始 `call_type=5` 对应 `one_dw.call_type=2` 的本次外呼样本。来源与场景枚举仍待业务释义。

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
- AI 通话使用已限定业务范围的 `one_dw.call_id` 集合半连接原始表，并保留原始 `call_time` 窗口。
- 不能把 call_status = 33 套到 one_dw.dwd_mkt_tmk_call_record_hf；后者当前数据地图字典的接通候选值为 1。

## 9. 常用 join key

- 逐通关联用 `try_cast(trim(one_dw.call_id) AS bigint) = raw.call_id`。接入前检查两侧 ID 基数及原始时间窗。
- 策略和学员取触达与 `one_dw` 双键对齐的记录。原始表 `user_number` 在两批 AI 样本中均为空。
- 好友 ODS 的 `call_id` 属于另一条待验证的事件桥，当前逐通证据覆盖 `one_dw` 与本表。

## 10. 常用 SQL 片段

只读逐通对账先限定触达场景、策略及 `one_dw` 的单个 `dt/hour` 快照和拨打窗口，再用去重后的数字 `call_id` 集合和原始时间窗筛原始表。每个原始 ID 在窗口内只取一条已验收记录。生产通时需先确认有效时长来源。

## 11. 注意事项

- 数据地图对交接稿三段名精确搜索无结果，短名搜索命中 data_lake_fuwu.dwd_crm_call_tmk_record_rt。库名漂移和字段缺失都必须保留为未决项。
- 本表不能替代已登记的 one_dw.dwd_mkt_tmk_call_record_hf 完成策略任务 Join；后者有 predict_task_id，本表没有。
- 通话 URL 和用户/顾问标识属于敏感明细，知识库不保存样例值。

## 12. 数据地图探查记录（2026-10-19）

- 通过 usql-web-query-operator sync-datamap-fields 使用交接稿表名检索；精确三段名未命中，短名回退唯一命中 data_lake_fuwu.dwd_crm_call_tmk_record_rt，表 ID 34742，项目“数据湖-服务域”。
- 数据地图返回 11 个普通字段、0 个分区字段；平台登记为在线 Iceberg 外表、Parquet 格式。
- 表元数据创建时间为 2026-03-31 10:44:56，更新时间为 2026-05-07 12:01:18；这些不是最新业务事件时间。
- 本次登记只固化物理字段和不可用边界，不确认交接稿库名映射或接通枚举。
- 2026-10-19 实际值 Probe 被平台以“无查询权限”阻断，未生成 Query ID。授权后的逐通对账见第 13 节。

## 13. 逐通核验与字段解读（2026-11-08）

天工数据地图只读复查精确命中表 ID `34742`，返回第 7 节的 11 个普通字段和 0 个分区字段。本次 `sync-datamap-fields` dry-run 的新增字段、类型更新及描述更新均为 0。字段备注仍为 `from deserializer`，以下业务解读来自本节的受限探查。

| 字段 | 实测用途或边界 |
|---|---|
| `call_id` | `bigint`。与 `one_dw.call_id` 转为 `bigint` 后逐通对应，已通过原始记录基数、记录时间和录音键对照。 |
| `user_number` | `bigint`。两批 AI 样本均为空，学员维度从已验证的 `one_dw.user_number` 保留。 |
| `email_prefix` | 邮箱前缀字段。11 月 7 日四策略样本为空。 |
| `account_id` | 字符串账号字段。11 月 7 日四策略样本为空。 |
| `call_time` | 字符串记录时间，样本解析后与 `one_dw.call_time` 一致。业务时点尚需源端时序定义。 |
| `call_duration` | 字符串时长。两批 AI 接通样本均可解析为 `0`。`call_type=4` 的 80 通正值对照与已标注为秒的工作量明细逐通相等。 |
| `call_status` | 原始状态码。样本中 `33` 与归一化 `call_status=1` 双向对应。 |
| `call_type` | 原始呼叫类型码。四策略已验证外呼样本均为 `5`，对应 `one_dw` 外呼值 `2`。 |
| `call_url` | 录音引用。两批已接通样本与 `one_dw` 的录音键逐通一致。 |
| `data_source` | 来源字段。11 月 7 日样本有值，枚举语义未核验。 |
| `scene_id` | 场景标识字段。11 月 7 日样本有值，市场顾问策略范围由触达表确定。 |

### 13.1 关联基数和状态

- 11 月 5 日使用策略 `4214/4235`、`one_dw dt=20261105/hour=23`、当天通话事件窗及原始表 `[2026-11-04, 2026-11-07)` 时间窗。1,313 通全部唯一命中原始记录，记录时间全部一致。633 通接通均为原始 `33`，录音键一致，时长均为 `0`。Query `1690945713`。
- 11 月 7 日使用四个已启用策略、`one_dw dt=20261107/hour=23`、当天通话事件窗及原始表 `[2026-11-06, 2026-11-09)` 时间窗。1,704 通全部唯一命中，记录时间全部一致。650 通接通均为原始 `33`，录音键一致。两批均无数字 ID 碰撞，且非接通样本无原始 `33`。Query `1691003845`。

| 策略 `plan_id` | 11 月 7 日外呼 | 接通 | 唯一原始记录 | 接通时长为 0 |
|---|---:|---:|---:|---:|
| `4214` | 345 | 179 | 345 | 179 |
| `4235` | 846 | 307 | 846 | 307 |
| `4255` | 216 | 95 | 216 | 95 |
| `4288` | 297 | 69 | 297 | 69 |

### 13.2 真实通时与单位

表结构没有独立的接通或挂断时间字段。需要事件起止时间时，须从能按同一通电话回连的上游事件取得。

单位核验使用 `service_dw.app_h_crm_lead_employee_workload_detail_hf.call_duration` 的秒值参考，按通话 ID 及相同记录时间或录音键交叉检查。80 通原始 `call_type=4`、`call_status=33` 的正值记录均与秒值完全相等，除以 1,000 的比对命中 0 通。11 月 5 日的 633 通 AI 接通样本在该参考表的正时长匹配也为 0。Query `1690989217`。

已验证的两批 AI 接通共 1,283 通，原始 `call_duration` 全为 0，因此本表当前能补充逐通原始状态和记录核验，真实 AI 接通时长仍缺有效数据。秒单位证据限于本次正值对照，AI 类型无正值可独立校验。10 秒挂断率和时长相关分子需另有可信逐通时长。
