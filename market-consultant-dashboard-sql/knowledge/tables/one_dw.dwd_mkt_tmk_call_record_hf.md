# one_dw.dwd_mkt_tmk_call_record_hf

## 1. 中文名称

先驱通话记录表（天工数据地图表 ID `22814`）。

## 2. 表用途

市场域“打电话”业务子域的先驱通话记录小时全量表，保存员工、用户、拨打时间、接通后通话时长、呼入呼出类型、任务与预测式外呼任务等字段。

本表是市场顾问 AI 外呼看板“使用段”的候选通话事实源。它不能单表提供渠道、经理、主管、伙伴、线索 ID、总线索数或 AI 加好友结果；这些字段必须从已限定的市场顾问线索底座、组织架构和好友事件表取得。

## 3. 数据粒度

候选为通话记录小时快照粒度。数据地图提供 `call_id`、`task_id` 与 `predict_task_id`，但未声明唯一键；同一通话在小时全量分区内及跨分区的重复关系需实测，聚合前不能直接假定 `COUNT(*)` 等于拨打次数。

## 4. 查询引擎

Presto。数据地图登记为 Hive 内表、ORC 格式，存储量约 2.27 TB。

## 5. 分区字段

`dt` 为天级分区（`yyyyMMdd`），`hour` 为小时级分区（`HH`）。数据地图登记为小时全量表，保留期 30 天；每次扫描必须同时限定 `dt` 和 `hour`，并按业务事件窗口限定 `call_time`。

## 6. 强制范围限定字段

- 必须限定具体 `dt`、`hour` 和 `call_time` 窗口。
- 仅统计外呼时，候选条件为 `call_type = 2`；枚举来自数据地图字段说明。
- 本表没有可独立确认 `ai_call_auto_add_friend` 场景的字段。AI 外呼范围需通过 `predict_task_id` 关联触达表 `outer_channel_task_id`，并由触达表限定 `scene_code = 'ai_call_auto_add_friend'`、`reach_type = 25` 及经确认的任务状态。
- 市场顾问范围必须从已限定线索人群半连接进入；不得把全表通话量解释为市场顾问指标。

## 7. 字段清单

字段、类型与说明由天工数据地图同步命令维护。

### 7.1 数据地图字段补充（2026-10-18）

> 来源：天工2数据地图字段信息。该补充段只补齐平台已登记字段、类型和字段说明；具体业务口径仍以本 Skill 已沉淀的 SQL 和指标规则为准。

| 字段名 | 类型 | 字段说明 | 常见用途 | 是否常用 |
|---|---|---|---|---|
| dt | string | 天级别分区 yyyyMMdd | 数据地图补充 | 否 |
| hour | string | 小时级分区 HH | 数据地图补充 | 否 |
| display_number | string | 员工工号 | 数据地图补充 | 否 |
| employee_type | bigint | 员工类型 | 数据地图补充 | 否 |
| employee_type_name | string | 员工类型名称 | 数据地图补充 | 否 |
| user_number | bigint | 用户编号 | 数据地图补充 | 否 |
| email_prefix | string | 老师邮箱前缀 | 数据地图补充 | 否 |
| call_time | string | 拨打时间 | 数据地图补充 | 否 |
| call_duration | bigint | 接通后通话时长 | 数据地图补充 | 否 |
| call_status | bigint | 是否接通 1 是 0 否 | 数据地图补充 | 否 |
| call_type | bigint | 0未知 1 呼入 2 呼出 | 数据地图补充 | 否 |
| call_type_name | string | 0未知 1 呼入 2 呼出 | 数据地图补充 | 否 |
| call_phone_number | string | 用户脱敏手机号码 | 数据地图补充 | 否 |
| call_url | string | 录音url | 数据地图补充 | 否 |
| scene_id | string | 场景id | 数据地图补充 | 否 |
| task_id | bigint | 任务id | 数据地图补充 | 否 |
| call_id | string | 通话id | 数据地图补充 | 否 |
| caller_number | string | 主叫号码（座席号） | 数据地图补充 | 否 |
| mark_id | bigint | 标记id | 数据地图补充 | 否 |
| create_time | string | 创建时间 | 数据地图补充 | 否 |
| update_time | string | 更新时间 | 数据地图补充 | 否 |
| exten | string | 分机号 | 数据地图补充 | 否 |
| owner_ship | string | 归属地 | 数据地图补充 | 否 |
| predict_task_id | bigint | 预测式外呼任务id | 数据地图补充 | 否 |
| sip_cause | string | 呼叫结果 | 数据地图补充 | 否 |

## 8. 常用过滤条件

### 8.1 看板字段与候选计算映射

下表是基于数据地图物理字段和本地交接稿形成的设计记录，不是可直接执行的 confirmed contract。

| 看板字段 | 候选来源或公式 | 当前状态 |
|---|---|---|
| 渠道 | 市场顾问线索全链路表的受治理 `channel_map` 或对应渠道维度 | 本表无此字段，待确认目标渠道口径 |
| 经理 | 线索全链路/架构表的 `virtual_leader_email_name` | 本表无此字段，需按目标时间截面确认 |
| 主管 | 线索全链路/架构表的 `virtual_direct_leader_email_name` | 本表无此字段，需按目标时间截面确认 |
| 伙伴 | 候选为线索全链路表 `employee_email_name`；本表只有 `email_prefix` | 需确认显示字段及员工桥接唯一性 |
| 总线索数 | 候选为线索底座聚合 `SUM(lead_count)` 或去重 `lead_id` | 必须与看板人群、渠道和时间圈一致，不能从本表计算 |
| AI外呼线索数 | 触达任务挂到线索后 `COUNT(DISTINCT lead_id)` | 需验证 `receiver_id/user_number`、班级和时间兜底挂线索规则 |
| AI拨打频次 | AI 范围内去重后的外呼通话次数，候选 `COUNT(DISTINCT call_id)` 且 `call_type=2` | `call_id` 唯一性及任务关联基数待实测 |
| AI例均频次 | AI拨打频次 ÷ AI外呼线索数 | 分母按交接稿为去重 AI 外呼线索，需业务确认“例均”定义 |
| AI接通率 | AI 接通外呼次数 ÷ AI 外呼次数；本表字典候选接通条件为 `call_status=1` | 与交接稿原始先驱表 `call_status=33` 存在来源层级差异，禁止混用 |
| AI例均接通时长 | 候选为 `SUM(call_duration)` ÷ AI 接通外呼次数 | “例均”也可能要求除以 AI 外呼线索数，分母必须由业务确认 |
| AI好友率 | ODS `status=2` 的 AI 加好友线索 ÷ AI 外呼线索 | 分子不在本表；候选 `好友.task_id = 本表.predict_task_id = 触达.outer_channel_task_id` |

### 8.2 过滤条件清单

- 小时全量快照：明确 `dt`、`hour`，通常同一 `dt` 选定一个经确认的小时快照，不能跨小时直接累加。
- 外呼候选：`call_type = 2`。
- 接通候选：本表数据地图定义 `call_status = 1` 为接通、`0` 为未接通。
- AI 自动加好友场景不能只凭 `predict_task_id IS NOT NULL` 推断，必须关联经场景过滤的触达任务集合。

## 9. 常用 join key

- `predict_task_id`：候选关联 `fairy_data_center.dwd_service_reach_wide_channel_subtask_prod_v2_di.outer_channel_task_id`；连接时统一类型并先验证两侧重复度。
- `user_number`：候选关联触达 `receiver_id`、好友关系 `user_number` 及线索全链路用户字段；一名用户可能对应多条线索，不是一对一键。
- `email_prefix`：候选关联市场顾问伙伴/员工字段；需使用受治理员工桥并核对时间截面与唯一性。
- `task_id`：普通任务 ID。交接稿明确 AI 批次不应以该字段挂好友；AI 好友候选使用 `predict_task_id`。

## 10. 常用 SQL 片段

暂无可直接执行的市场顾问生产 SQL。当前仍需确认 AI 任务范围、小时快照选择、`call_id` 去重、用户挂线索规则、组织时间截面，以及“例均接通时长”的分母；在这些槽位解决前不生成伪可执行 SQL。

## 11. 注意事项

- 数据地图当前完整物理名是 `one_dw.dwd_mkt_tmk_call_record_hf`；交接稿写的是原始层 `dw_noumenon_crm.crm.dwd_crm_call_tmk_record_rt`，两者不是同一个表名。
- 本表字典的接通枚举为 `call_status=1`，交接稿原始表的接通枚举为 `call_status=33`。只有经实际对账证明语义映射一致后，才能用本表替代原始表；不能把 33 直接套到本表。
- 小时全量分区可能重复承载同一通话，必须先确定快照选择和 `call_id` 去重规则，否则拨打次数、接通次数和时长都会放大。
- `call_phone_number`、`call_url`、`caller_number` 属于敏感或可关联个人的信息，知识库不保存样例值或明细结果。
- 交接稿给出的 AI 加好友率是产出指标；接通率、频次和通话时长属于使用指标。看板可并列展示，但不得改变各自分子、分母和来源。

## 12. 数据地图探查记录（2026-10-18）

- 通过 `usql-web-query-operator sync-datamap-fields` 使用短名 `dwd_mkt_tmk_call_record_hf` 实时搜索；数据地图唯一选中 `one_dw.dwd_mkt_tmk_call_record_hf`，中文名“先驱通话记录表”，表 ID `22814`，项目“市场&用户域数据仓库”。
- 数据地图当前返回 23 个普通字段和 2 个分区字段；平台登记为在线 Hive 内表、ORC 格式、小时全量表、保留 30 天。
- 平台表信息记录创建时间 `2022-08-18 15:56:12`、更新时间 `2026-09-29 11:40:31`；这些是表元数据时间，不是最新业务事件时间。
- 本地交接稿 `D:/Feishu/给伙伴_产出逻辑与SQL_看板加好友块_20260813.md` 用于识别 AI 场景、任务桥、好友率以及覆盖/使用/产出边界；表层差异和未验证指标均保留为待确认。
- 本次只读取数据地图结构和本地交接稿，没有执行 SQL、下载通话明细或修改远端平台。
