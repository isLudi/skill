# service_dw.app_h_crm_lead_task_process_info_detail_hf

## 1. 中文名称

CRM 线索任务处理信息明细小时表

## 2. 表用途

在青橙转化宽表-市场渠道 SQL 中作为首次外呼数据来源，用于标记线索是否有 F 类外呼记录（`is_f_call`）。

## 3. 数据粒度

待人工确认。当前 SQL 按 `flow_order_period_name + assign_employee_email_name + user_id + call_answer_lead_count（作为 lead_id）` 使用 `select distinct`。

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 说明 |
|---|---|---|
| `dt` | string | 日期分区 |
| `hour` | string | 小时分区 |
## 6. 强制范围限定字段

| 字段名 | 默认取值/占位符 | 说明 |
|---|---|---|
| `dt` | `format_datetime(now() - interval '2' hour, 'YYYYMMdd')` | 最新日期快照 |
| `hour` | `format_datetime(now() - interval '3' hour, 'HH')` | 小时级分区 HH |

## 7. 字段清单

以下字段基于本 SQL 实际使用情况整理，完整字段清单待表结构确认。

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `dt` | string | 日期分区 | 必加 |
| `hour` | string | 小时分区 | 建议加 |
| `flow_order_period_name` | string | 订单期次名称 | 格式如 `2026YYMM期`，用于拼接 `period_name` |
| `assign_employee_email_name` | string | 分配员工邮箱名 | join key，对应宽表的 `employee_email_name` |
| `user_id` | bigint | 用户 ID | join key |
| `call_answer_lead_count` | bigint | 外呼接通线索数/线索 ID | 本 SQL 中作为 `lead_id` 使用，语义待确认 |
| `period_create_time` | string | 期次创建时间 | 过滤条件 `> '2026-01-01'` |
| `is_refund_before_clazz_begin` | bigint | 是否课前退款 | 过滤条件 `= 0`，排除课前退款 |

### 7.1 数据地图字段补充（2026-06-17）

> 来源：天工2数据地图字段信息。该补充段只补齐平台已登记字段、类型和字段说明；具体业务口径仍以本 Skill 已沉淀的 SQL 和指标规则为准。

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `private_sea_id` | bigint | 私海id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `employee_id` | bigint | 顾问id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `team_id` | bigint | 团队id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `stage` | int | 线索状态 我的线索(4) 我的客户(5) 我的成单(6) | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `other_customer` | int | 是否属于其他人的客户 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `private_source` | int | 来源，1公开课报名 2手动录入 3公海领取 4主管分配 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `last_follow_time` | string | 跟进时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `last_follow_content` | string | 最后一次跟进内容 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `intention_level` | int | 意向度 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `assign_time` | string | 线索分配时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `fall_sea_time` | string | 线索掉海时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `private_sea_create_time` | string | 创建时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `private_sea_update_time` | string | 更新时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `intention_level_time` | string | 首次记录意向度时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `assign_customer_time` | string | 转客户时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_id` | bigint | 线索id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `account_id` | bigint | 顾问accountId | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `active_time` | string | 激活时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `b_client` | int | 1线上 2线下 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trace_id` | bigint | 留痕id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `scenario_type` | int | 录入场景，线上(1)/线下(2) | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trace_create_time` | string | 创建时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `trace_update_time` | string | 更新时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `state` | int | 分配状态，0:初始状态，1:待分配，2:已分配，3:分配失败 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `source` | string | 归因source | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `order_no` | bigint | 订单号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `get_customer_way_id` | string | source中的获客方式id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `union_id` | string | 微信unionId | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `type` | int | 留痕类型：1.引流课 2.手动录入 3.公海领取 4.主管分配 5.批量导入 6.留单 7.销售分边 8.正价课 9.微信私域 10.修改意向 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `purchase_intention` | bigint | 购买意向，一级品类id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_create_time` | string | 创建时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_update_time` | string | 更新时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `purchase_intention3` | bigint | 三级品类ID | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_source` | string | source | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_state` | int | 线索状态 1待分配 2已分配 3分配失败 4close线索生命周期结束 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `state_change_reason` | int | 状态变更原因 1.待分配：初始状态 2.分配失败：未配置规则（未在执行期）3.分配失败：未分配规则执行失败 4.正常分配 5.close:掉海 6.close:修改购买意向 7.close:顾问无服务能力 8.close:微信线索合并 9.异常中断导致分配失败 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `assign_plan_id` | bigint | 分配应用的规则下的计划id 只记录第一次分配计划id因为后面会走唯一性 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `gy_trace_id` | bigint | 归因留痕（分配留痕）id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `clazz_number` | bigint | 班级id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `flow_order_period_number` | bigint | 编号 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `period_start_time` | string | 期开始时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `period_end_time` | string | 期结束时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `period_update_time` | string | 更新时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `assign_employee_email_prefix` | string | 分配顾问员工邮箱前缀 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `employee_role` | bigint | 员工角色，eg：0-普通组员｜1-虚线管辖｜2-实线汇报 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `employee_virtual_department_code` | bigint | 虚拟组织架构部门编码 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `employee_virtual_department_name` | string | 虚拟组织架构部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `virtual_department_path` | string | 虚拟组织架构路径 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `virtual_department_code_0` | string | 虚拟组织架构零级部门code | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `virtual_department_code_1` | string | 虚拟组织架构一级部门code | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `virtual_department_code_2` | string | 虚拟组织架构二级部门code | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `virtual_department_code_3` | string | 虚拟组织架构三级部门code | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `virtual_department_name_0` | string | 虚拟组织架构零级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `virtual_department_name_1` | string | 虚拟组织架构一级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `virtual_department_name_2` | string | 虚拟组织架构二级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `virtual_department_name_3` | string | 虚拟组织架构三级部门名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `owner_account_id` | bigint | 实线汇报account_id | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `owner_name` | string | 实线汇报员工名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `owner_email_name` | string | 实线汇报员工带数字名称 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `owner_email_prefix` | string | 实线汇报邮箱前缀 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_wx_friend` | string | 是否微信好友：好友 \| 非好友 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `call_connected_count` | bigint | 线索id（电话接通） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `call_missed_count` | bigint | 线索id（电话未接通） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `all_call_duration` | bigint | 总通话时长(s) | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `call_duration_total` | bigint | 总通话时长(min) | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `first_call_time` | string | 首次拨打时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `last_call_time` | string | 最后一次拨打时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `first_call_connected_time` | string | 首次接通时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `last_call_connected_time` | string | 最后一次接通时间 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `zdzx_field_value` | string | 走读住校字段取值 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `zdzx_field_value_desc` | string | 走读住校字段取值描述 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `able_to_attend_this_period` | string | 本期听课 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `close_order_resistance` | string | 关单阻力 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `deep_communicate_method` | string | 深沟方式 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_pre_signup` | string | 预报名 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `send_double_table` | string | 双表发送 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_sign_up` | string | 预报名学科 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `lead_first_call` | string | 首call情况 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `order_lead_count` | bigint | 线索id（线索数） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `jingpin_last_active_date` | string | 用户在高中规划最近活跃日期1 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `friend_lead_count` | bigint | 线索id（加好友线索） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `shallow_follow_lead_count` | bigint | 线索id（浅沟线索） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `deep_follow_lead_count` | bigint | 线索id（深沟线索） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `noda_lead_count` | bigint | 线索id（诺达线索） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `plan_lead_count` | bigint | 线索id（规划线索） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_apply_lead_count` | bigint | 线索id（预报名线索） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `close_order_lead_count` | bigint | 线索id（关单线索） | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `shallow_follow_lead_state` | string | 浅沟线索状态 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `deep_follow_lead_state` | string | 深沟线索状态 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `noda_lead_state` | string | 诺达线索状态 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `plan_lead_state` | string | 规划线索状态 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `pre_apply_lead_state` | string | 预报名线索状态 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `close_order_lead_state` | string | 关单线索状态 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `l15d_jingpin_active_lead_count` | bigint | 近15日规划精品app活跃线索数 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |
| `is_gy_trace_id` | bigint | 是否归因留痕 | 数据地图补充，业务口径需结合青橙 SQL 使用场景确认 |

## 8. 常用过滤条件

```sql
where dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
  and hour = format_datetime(now() - interval '3' hour, 'HH')
  and period_create_time > '2026-01-01'
  and is_refund_before_clazz_begin = 0
  and call_answer_lead_count is not null
```

## 9. 常用 join key

- `assign_employee_email_name`（对应宽表的 `employee_email_name`）
- `user_id`
- `call_answer_lead_count`（本 SQL 中作为 `lead_id` 使用，对应宽表的 `lead_id`）
- `flow_order_period_name`（拼接后对应 `period_name`）

## 10. 常用 SQL 片段

```sql
select distinct
    concat(substr(flow_order_period_name, 1, 4), substr(flow_order_period_name, 7, 4), '期') as period_name,
    assign_employee_email_name,
    user_id,
    call_answer_lead_count as lead_id,
    1 as is_f_call
from service_dw.app_h_crm_lead_task_process_info_detail_hf
where dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
  and hour = format_datetime(now() - interval '3' hour, 'HH')
  and period_create_time > '2026-01-01'
  and is_refund_before_clazz_begin = 0
  and call_answer_lead_count is not null
```

## 11. 注意事项

- 本表在青橙知识库中首次入库，字段含义均来源于历史 SQL 推断，需表结构确认。
- `call_answer_lead_count` 字段名暗示为"计数"类型，但本 SQL 将其作为 `lead_id`（标识符）使用，语义存在矛盾，待确认。
- 本表 hour 使用 `now()-3h`，与其他表（主表 `now()-2h`）偏移不同，可能是数据延迟差异。
- `flow_order_period_name` 格式假设为 `YYYYMMdd期` 或类似格式，通过 `substr(1,4) + substr(7,4)` 拼接，若格式变化会导致 `period_name` 解析错误。
- 本表目前仅在转化宽表-市场渠道 SQL 中使用，是否可用于其他青橙看板待确认。
