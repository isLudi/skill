# 市场顾问 AI 外呼看板数据集探查记录（2026-10-19）

## 结论

当前可以形成候选数据集设计并计算总线索数、AI 外呼线索数、AI 拨打频次、AI 例均频次和候选 AI 接通率；完整生产数据集仍被 AI 好友 ODS 查询权限、原始通话时长源查询权限和少量通话归属歧义阻断。

## 固定业务范围候选

- 触达策略：plan_id IN (4214, 4235)。
- 场景：scene_code = ai_call_auto_add_friend，reach_type = 25。
- 触达状态：channel_subtask_status IN (3, 4)，含失败尝试。
- 每次先用有界 Probe 动态找各小时全量表最新完整 dt/hour；正式查询只能选一个完整快照，同时用业务事件时间限制统计日。
- 上述口径来自用户确认、交接稿和本轮 Probe；尚未建立 source-Hash-bound confirmed contract，不得据此直接生成生产可执行 QueryPlan。

## 表与职责

| 表 | 用途 | 已验证状态 |
|---|---|---|
| fairy_data_center.dwd_service_reach_wide_channel_subtask_prod_v2_di | 策略/场景受限触达任务、用户、班级、触达状态和候选接听时长 | 可查；最新完整 dt=20261018 |
| one_dw.dwd_mkt_tmk_call_record_hf | 任务+用户级拨打次数和候选接通次数 | 可查；最新完整 dt=20261018/hour=23 |
| service_dw.dm_crm_trace_lead_full_link_data_hf | 触达用户/班级挂 lead_id | 可查；必须先用触达用户半连接限缩 |
| bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df | 渠道、经理、主管、伙伴及总线索底座 | 可查；最新完整 dt=20261018/hour=23 |
| data_lake_ods.ods_ones_business_agent_ai_add_friend_record_rt | AI 好友成功事件 | 无查询权限，用户已申请 |
| data_lake_fuwu.dwd_crm_call_tmk_record_rt | call_status=33 与原始接通时长候选核对 | 无查询权限，需申请；表本身无 predict_task_id |

## 已验证关联

1. 触达与 one_dw 通话必须使用 outer_channel_task_id = predict_task_id 且 receiver_id = user_number 双键；单任务键会产生多对多放大。
2. 触达挂线索优先 receiver_id + clazz_number = user_id + flow_order_clazz_number；无班级或精确未命中时，在同用户候选内选 lead_create_time 距触达 create_time 最近者，并用 lead_time DESC、lead_id DESC 稳定打破并列。
3. 选中 lead_id 回连业财表取得 channel_map 候选原始字段、virtual_leader_email_name 作为经理、virtual_direct_leader_email_name 作为主管、employee_email_name 作为伙伴。渠道必须使用当前受治理渠道 CASE，不能直接任选 channel_name_1/2/3。
4. 好友 ODS 获权后必须用 task_id = outer_channel_task_id 且 user_id = receiver_id 双键；status=2 是成功候选，is_del 和 source_type 仍需实际值对账。

## 2026-10-18 实际基数

- 触达：4214 为 146 条子任务/137 用户；4235 为 2,236 条子任务/1,299 用户。每个策略仅 1 个 outer_channel_task_id，证明必须带用户键。
- 通话：4214 为 112 次拨打/34 次候选接通；4235 为 1,578 次拨打/430 次候选接通。one_dw 的接通 call_duration 全为 0，因此不能计算正式均通时。
- 触达 duration：status=3 的 193 条全部大于 0，status=4 的 2,189 条全部为 0；4214/4235 正时长均值为 98.3636/53.0934 秒（Query ID 1645485272）。它与 one_dw 候选接通次数不一致，只能作为待对账的时长候选。
- 线索挂接：4214 的 clazz_number 全为空，137 个键全部走用户兜底并成功选出；4235 选中 1,299 个键、4 个未命中。4235 的 1,303 个用户班级键对应 1,299 用户，说明 4 个用户有多班级归属风险。
- 组织回连：4214 已选 137 条全部命中且维度完整；4235 已选 1,299 条全部命中且维度完整，但 1 个 lead_id 有多个维度组合，需稳定去重。

## 指标组件与公式

为保证看板总计正确，数据集应优先输出加法组件，再由看板重算比例：

| 展示指标 | 数据集组件/公式 | 当前状态 |
|---|---|---|
| 渠道 | 当前受治理 channel_map CASE | 可设计，需带完整当前 CASE |
| 经理 | virtual_leader_email_name | 已验证覆盖 |
| 主管 | virtual_direct_leader_email_name | 已验证覆盖 |
| 伙伴 | employee_email_name | 已验证覆盖 |
| 总线索数 | 同一业务范围内 SUM(lead_count)；不能从 AI 触达子集倒推 | 可计算，最终时间圈需确认 |
| AI 外呼线索数 | COUNT DISTINCT 挂接成功的 lead_id | 候选可计算，4 个未命中需暴露质量列 |
| AI 拨打频次 | COUNT DISTINCT call_id | 可计算 |
| AI 例均频次 | AI 拨打频次 / AI 外呼线索数 | 可计算 |
| AI 接通率 | 候选接通次数 / AI 拨打频次；one_dw 候选条件 call_status=1 | 可计算候选值，需与原始层 call_status=33 对账 |
| AI 例均接通时长 | 接通时长合计 / 接通次数，或按业务另确认是否除以外呼线索数 | 阻断；one_dw 时长为 0，分母语义也待确认 |
| AI 好友率 | AI 好友 lead 数 / AI 外呼线索数 | 阻断；ODS 权限审批中 |

## 必须保留的质量列

- unmatched_lead_count：触达但未挂上 lead 的数量。
- ambiguous_dimension_lead_count：同 lead 对应多个组织/渠道维度组合的数量。
- multi_clazz_user_count：同一任务+用户出现多个班级的数量；通话归属未决时不得把一次通话复制给多个 lead。
- friend_probe_status 和 duration_probe_status：明确区分权限待审批、口径待对账与真实零值。

## 生产阻断项

1. 好友 ODS 获权后验证最新事件时间、status/is_del/source_type 分布、task_id+user_id 重复度及双键命中率。
2. 原始通话候选表获权后验证 call_status=33、时长、call_id 唯一性；因其无 predict_task_id，还需证明可通过好友 ODS call_id 或其他受治理键回到策略任务。
3. 明确 AI 例均接通时长的分母是接通次数还是 AI 外呼线索数。
4. 明确 4 个多班级用户的通话应按最近触达归属一个 lead，还是允许按多个 AI 外呼线索展示；未确认前禁止重复分摊通话。
5. 创建远端 Data Center 数据集需另行执行 Creation Plan、用户授权 Apply、SQL/调度回读及首抽 SUCCESS；本记录不构成远端写入授权。
