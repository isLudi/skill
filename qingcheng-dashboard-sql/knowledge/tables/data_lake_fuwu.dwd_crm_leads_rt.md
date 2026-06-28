# data_lake_fuwu.dwd_crm_leads_rt

## 1. 中文名称

线索统计表

## 2. 表用途

用于补充 CRM 原始线索侧字段，适合在青橙场景下做以下排查：

- 从 `lead_id` / `crm_leads_id` 回查原始线索状态、场景、获客方式、归因 source。
- 追溯 `previous_model_id`、`model_type`、`model_type_desc` 这组“模型阶段”字段，辅助判断线索是否由上阶段模型流转而来。
- 补充原始线索跟进状态类字段，如接通、到课、铺课、预报名、关单阻力、无效原因等。

## 3. 数据粒度

按数据地图和 DDL 语义看，本表是线索实时宽表，主键候选字段为 `crm_leads_id`。  
是否严格“一行一条线索最新状态”仍待业务侧或 SQL live 抽样补验。

## 4. 查询引擎

Presto

## 5. 分区字段

数据地图 `partitionColumns` 为空；当前未登记显式分区字段。

| 字段名 | 类型 | 说明 |
|---|---|---|
| 无 | - | DDL 为 Iceberg 表，数据地图未给出 `dt/hour` 分区列 |

## 6. 强制范围限定字段

本表在数据地图中未体现青橙专属部门范围字段，通常不单独作为青橙事实主表使用。  
若与青橙主宽表联查，建议把青橙范围限定写在 `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` 一侧，而不是先对本表硬筛部门。

## 7. 字段清单

### 7.1 核心标识与模型阶段字段

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `crm_leads_id` | bigint | 线索ID | 与青橙主宽表 `lead_id` 字段语义一致；2026-06-27 小样本验证 `lead_id = crm_leads_id` 命中 30/30 |
| `user_id` | bigint | 用户ID | 可与青橙主宽表 `user_id` 做用户级回查 |
| `previous_model_id` | bigint | 上阶段模型ID | 当 `previous_model_id > 0` 时可回连本表 `crm_leads_id`；2026-06-27 小样本命中 30/30，上一阶段多为 `潜客` |
| `model_type` | int | 模型类型 | 与 `model_type_desc` 配合判断当前记录所处模型阶段 |
| `model_type_desc` | string | 模型类型-描述 | 用于辅助判断 `previous_model_id` 是否指向上阶段潜客/线索模型 |
| `purchase_intention_id` | bigint | 购买意向ID | 原始线索意向字段 |
| `purchase_intention_name` | string | 购买意向名称 | 原始线索意向字段 |
| `scenario_type` | int | 线索场景 | 原始线索场景枚举 |
| `channel` | int | 线索渠道 | 原始线索渠道枚举 |
| `leads_id` | string | 流量id | 原始流量侧标识 |
| `source` | string | 归因source | 适合配合 `rule_name` 之外的原始来源排查 |

### 7.2 数据地图字段补充（2026-06-27）

> 来源：天工 2 数据地图 `tableV2/searchTableList`、`getTableInfo`、`normalColumns` 和 `getDdl`。  
> 本节记录的是平台登记字段与说明，不等同于青橙业务口径已完全确认。

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `crm_leads_id` | bigint | 线索ID | 数据地图字段 |
| `user_id` | bigint | 用户ID | 数据地图字段 |
| `purchase_intention_id` | bigint | 购买意向ID | 数据地图字段 |
| `purchase_intention_name` | string | 购买意向名称 | 数据地图字段 |
| `scenario_type` | int | 线索场景 | 数据地图字段 |
| `channel` | int | 线索渠道 | 数据地图字段 |
| `leads_id` | string | 流量id | 数据地图字段 |
| `source` | string | 归因source | 数据地图字段 |
| `get_customer_way_id` | bigint | 获客方式ID | 数据地图字段 |
| `state` | int | 线索状态-枚举 | 数据地图字段 |
| `state_desc` | string | 线索状态-描述 | 数据地图字段 |
| `state_change_reason` | int | 线索状态变更原因 | 数据地图字段 |
| `trace_id` | bigint | 归因留痕ID | 数据地图字段 |
| `org_number` | bigint | 校区number | 数据地图字段 |
| `model_type` | int | 模型类型 | 数据地图字段 |
| `model_type_desc` | string | 模型类型-描述 | 数据地图字段 |
| `previous_model_id` | bigint | 上阶段模型ID | 数据地图字段 |
| `level` | int | 线索等级 | 数据地图字段 |
| `close_time` | string | 线索关闭时间 | 数据地图字段 |
| `protect_time` | string | 保护器截止时间 | 数据地图字段 |
| `call_situation` | string | 接通情况 | 数据地图字段 |
| `attend_first_lesson` | string | 第一节到课 | 数据地图字段 |
| `attend_first_lesson_comment` | string | 第一节到课说明 | 数据地图字段 |
| `able_to_attend_this_period` | string | 本期听课 | 数据地图字段 |
| `able_to_attend_this_period_comment` | string | 本期听课说明 | 数据地图字段 |
| `send_double_table` | string | 双表发送 | 数据地图字段 |
| `attend_person` | string | 听课人 | 数据地图字段 |
| `foreshadow_purchase` | string | 铺课 | 数据地图字段 |
| `foreshadow_purchase_comment` | string | 铺课说明 | 数据地图字段 |
| `close_order_resistance` | string | 关单阻力 | 数据地图字段 |
| `is_pre_signup` | string | 预报名 | 数据地图字段 |
| `class_experience` | string | 上课感受 | 数据地图字段 |
| `class_experience_comment` | string | 上课感受说明 | 数据地图字段 |
| `app_screenshot` | string | app截图 | 数据地图字段 |
| `first_call` | string | 首call情况 | 数据地图字段 |
| `follow_up_status` | string | 跟进状态 | 数据地图字段 |
| `deep_communicate_method` | string | 深沟方式 | 数据地图字段 |
| `deep_communicate_duration` | string | 深沟时长 | 数据地图字段 |
| `pre_sign_up` | string | 预报名学科 | 数据地图字段 |
| `invalid_reason` | string | 无效原因 | 数据地图字段 |
| `leads_valid_mark` | string | 有效标记 | 数据地图字段 |
| `leads_invalid_mark` | string | 无效标记 | 数据地图字段 |
| `union_id_snapshot` | string | union_id快照 | 数据地图字段 |
| `transfer_times` | string | 转移次数 | 数据地图字段 |
| `quality_tilt_resource_number` | string | 往期大盘参考数 | 数据地图字段 |
| `quality_tilt_resource_weignt_up` | string | 指导资源包权重参数-上限 | 数据地图字段 |
| `quality_tilt_resource_weignt_lower` | string | 指导资源包权重参数-下限 | 数据地图字段 |
| `target_gmv` | string | 资源目标GMV | 数据地图字段 |
| `business_opportunity` | string | 商机类型 | 数据地图字段 |
| `first_circulation_time` | string | 商机流转时间 | 数据地图字段 |
| `not_attribution_flag` | string | 不归因标识 | 数据地图字段 |

## 8. 常用过滤条件

```sql
where crm_leads_id is not null
```

若和青橙主宽表联查，优先把部门、期次和快照范围写在 `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` 一侧。

## 9. 常用 join key

- `crm_leads_id = bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df.lead_id`
  - 字段语义：两侧均为“线索 ID”。
  - 当前状态：2026-06-27 使用 `dt='20260627' and hour='16'` 的青橙主宽表样本验证，30 行命中 30 行；query id `1433250612`。
- `user_id = bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df.user_id`
  - 适用于用户级回查；若一个用户对应多条线索，不能替代线索级 join。
- `previous_model_id = dwd_crm_leads_rt.crm_leads_id`
  - 当前状态：`previous_model_id > 0` 样本 30 行命中 30 行；query id `1433259664`。`previous_model_id = 0` 不能作为有效上一阶段 ID 使用。

## 10. 常用 SQL 片段

```sql
select
    f.lead_id,
    f.user_id,
    l.state_desc,
    l.source,
    l.model_type_desc,
    l.previous_model_id
from bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df f
left join data_lake_fuwu.dwd_crm_leads_rt l
  on cast(f.lead_id as bigint) = l.crm_leads_id
where f.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
  and f.hour = format_datetime(now() - interval '2' hour, 'HH')
  and f.section_assign_employee_first_level_department_name = 'H业务线'
  and f.section_assign_employee_second_level_department_name = '青橙项目部'
```

## 11. 注意事项

- 本表来自数据湖服务域，DDL 显示为 Iceberg 表；数据地图未登记 `dt/hour` 分区，不要想当然套用小时快照表写法。
- `previous_model_id` 目前稳妥理解为“上一阶段模型 ID”。正数样本可回连到本表 `crm_leads_id`，且上一阶段 `model_type_desc` 多为 `潜客`；但 `previous_model_id = 0` 是无效上阶段标识，写 SQL 时必须过滤。
- 2026-06-27 已通过数据地图脚本确认表存在、字段共 51 个、无显式分区列；同日通过网页 SQL 小样本补验完成 `lead_id = crm_leads_id` 和 `previous_model_id > 0 = prev.crm_leads_id` 两条关系。
