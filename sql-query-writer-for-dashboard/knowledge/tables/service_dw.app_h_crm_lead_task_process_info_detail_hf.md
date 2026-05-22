# service_dw.app_h_crm_lead_task_process_info_detail_hf

## 1. 中文名称

高中线索服务跟进明细

## 2. 表用途

高中线索服务任务跟进过程明细。

库名前缀状态：已确认，来自 `table_fields_full_20260420_092405.json`。

## 3. 数据粒度

线索-任务-小时粒度，待确认

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 含义 | 是否必填 |
|---|---|---|---|
| dt | string | 天级别分区 yyyyMMdd | 是 |
| hour | string | 小时级分区 HH | 是 |

## 6. 强制范围限定字段

| 字段名 | 类型 | 推荐取值 | 是否必填 | 说明 | 来源 |
|---|---|---|---|---|---|
| employee_virtual_department_name | string | '<待填写>' | 是 | 虚拟组织架构部门名称 | 待人工确认 |
| virtual_department_name_0 | string | '<待填写>' | 是 | 虚拟组织架构零级部门名称 | 待人工确认 |
| virtual_department_name_1 | string | '<待填写>' | 是 | 虚拟组织架构一级部门名称 | 待人工确认 |
| virtual_department_name_2 | string | '<待填写>' | 是 | 虚拟组织架构二级部门名称 | 待人工确认 |
| virtual_department_name_3 | string | '<待填写>' | 是 | 虚拟组织架构三级部门名称 | 待人工确认 |

说明：
- 推荐取值来自 `baijia-data-map/row_permissions.json` 的历史 SQL 归纳；不是永久业务授权边界。
- 用户未给出取值时，生成 SQL 应优先使用占位符或向用户确认，不能擅自扩大范围。

## 7. 字段清单

| 字段名 | 类型 | 字段描述 | 常见用途 | 是否常用 |
|---|---|---|---|---|
| dt | string | 天级别分区 yyyyMMdd | 分区过滤 | 是 |
| hour | string | 小时级分区 HH | 分区过滤 | 是 |
| private_sea_id | bigint | 私海id | 待按需求确认 | 否 |
| user_id | bigint | 用户id | 主键/关联键 | 是 |
| employee_id | bigint | 顾问id | 主键/关联键 | 是 |
| team_id | bigint | 团队id | 待按需求确认 | 否 |
| stage | int | 线索状态 我的线索(4) 我的客户(5) 我的成单(6) | 待按需求确认 | 否 |
| other_customer | int | 是否属于其他人的客户 | 待按需求确认 | 否 |
| private_source | int | 来源，1公开课报名 2手动录入 3公海领取 4主管分配 | 待按需求确认 | 否 |
| last_follow_time | string | 跟进时间 | 时间分析 | 否 |
| last_follow_content | string | 最后一次跟进内容 | 待按需求确认 | 否 |
| intention_level | int | 意向度 | 待按需求确认 | 否 |
| assign_time | string | 线索分配时间 | 时间分析 | 否 |
| fall_sea_time | string | 线索掉海时间 | 时间分析 | 否 |
| private_sea_create_time | string | 创建时间 | 时间分析 | 否 |
| private_sea_update_time | string | 更新时间 | 时间分析 | 否 |
| intention_level_time | string | 首次记录意向度时间 | 时间分析 | 否 |
| assign_customer_time | string | 转客户时间 | 时间分析 | 否 |
| lead_id | bigint | 线索id | 主键/关联键 | 是 |
| account_id | bigint | 顾问accountId | 指标聚合 | 是 |
| active_time | string | 激活时间 | 时间分析 | 否 |
| b_client | int | 1线上 2线下 | 待按需求确认 | 否 |
| trace_id | bigint | 留痕id | 主键/关联键 | 是 |
| scenario_type | int | 录入场景，线上(1)/线下(2) | 待按需求确认 | 否 |
| trace_create_time | string | 创建时间 | 时间分析 | 否 |
| trace_update_time | string | 更新时间 | 时间分析 | 否 |
| state | int | 分配状态，0:初始状态，1:待分配，2:已分配，3:分配失败 | 待按需求确认 | 否 |
| source | string | 归因source | 待按需求确认 | 否 |
| order_no | bigint | 订单号 | 待按需求确认 | 否 |
| get_customer_way_id | string | source中的获客方式id | 待按需求确认 | 否 |
| union_id | string | 微信unionId | 待按需求确认 | 否 |
| type | int | 留痕类型：1.引流课 2.手动录入 3.公海领取 4.主管分配 5.批量导入 6.留单 7.销售分边 8.正价课 9.微信私域 10.修改意向 | 待按需求确认 | 否 |
| purchase_intention | bigint | 购买意向，一级品类id | 待按需求确认 | 否 |
| lead_create_time | string | 创建时间 | 时间分析 | 否 |
| lead_update_time | string | 更新时间 | 时间分析 | 否 |
| purchase_intention3 | bigint | 三级品类ID | 待按需求确认 | 否 |
| lead_source | string | source | 待按需求确认 | 否 |
| lead_state | int | 线索状态 1待分配 2已分配 3分配失败 4close线索生命周期结束 | 待按需求确认 | 否 |
| state_change_reason | int | 状态变更原因 1.待分配：初始状态 2.分配失败：未配置规则（未在执行期）3.分配失败：未分配规则执行失败 4.正常分配 5.close:掉海 6.close:修改购买意向 7.close:顾问无服务能力 8.close:微信线索合并 9.异常中断导致分配失败 | 待按需求确认 | 否 |
| assign_plan_id | bigint | 分配应用的规则下的计划id 只记录第一次分配计划id因为后面会走唯一性 | 待按需求确认 | 否 |
| gy_trace_id | bigint | 归因留痕（分配留痕）id | 待按需求确认 | 否 |
| clazz_number | bigint | 班级id | 待按需求确认 | 否 |
| flow_order_period_number | bigint | 编号 | 常用维度 | 是 |
| flow_order_period_name | string | 期名称 | 常用维度 | 是 |
| period_start_time | string | 期开始时间 | 常用维度 | 是 |
| period_end_time | string | 期结束时间 | 常用维度 | 是 |
| period_create_time | string | 创建时间 | 常用维度 | 是 |
| period_update_time | string | 更新时间 | 常用维度 | 是 |
| assign_employee_email_name | string | 分配顾问员工带数字名称 | 常用维度 | 是 |
| assign_employee_email_prefix | string | 分配顾问员工邮箱前缀 | 常用维度 | 是 |
| employee_role | bigint | 员工角色，eg：0-普通组员｜1-虚线管辖｜2-实线汇报 | 常用维度 | 是 |
| employee_virtual_department_code | bigint | 虚拟组织架构部门编码 | 常用维度 | 是 |
| employee_virtual_department_name | string | 虚拟组织架构部门名称 | 权限/业务范围限定 | 是 |
| virtual_department_path | string | 虚拟组织架构路径 | 常用维度 | 是 |
| virtual_department_code_0 | string | 虚拟组织架构零级部门code | 常用维度 | 是 |
| virtual_department_code_1 | string | 虚拟组织架构一级部门code | 常用维度 | 是 |
| virtual_department_code_2 | string | 虚拟组织架构二级部门code | 常用维度 | 是 |
| virtual_department_code_3 | string | 虚拟组织架构三级部门code | 常用维度 | 是 |
| virtual_department_name_0 | string | 虚拟组织架构零级部门名称 | 权限/业务范围限定 | 是 |
| virtual_department_name_1 | string | 虚拟组织架构一级部门名称 | 权限/业务范围限定 | 是 |
| virtual_department_name_2 | string | 虚拟组织架构二级部门名称 | 权限/业务范围限定 | 是 |
| virtual_department_name_3 | string | 虚拟组织架构三级部门名称 | 权限/业务范围限定 | 是 |
| owner_account_id | bigint | 实线汇报account_id | 指标聚合 | 是 |
| owner_name | string | 实线汇报员工名称 | 待按需求确认 | 否 |
| owner_email_name | string | 实线汇报员工带数字名称 | 待按需求确认 | 否 |
| owner_email_prefix | string | 实线汇报邮箱前缀 | 待按需求确认 | 否 |
| is_wx_friend | string | 是否微信好友：好友 \| 非好友 | 待按需求确认 | 否 |
| call_connected_count | bigint | 线索id（电话接通） | 指标聚合 | 是 |
| call_missed_count | bigint | 线索id（电话未接通） | 指标聚合 | 是 |
| all_call_duration | bigint | 总通话时长(s) | 指标聚合 | 是 |
| call_duration_total | bigint | 总通话时长(min) | 指标聚合 | 是 |
| first_call_time | string | 首次拨打时间 | 时间分析 | 否 |
| last_call_time | string | 最后一次拨打时间 | 时间分析 | 否 |
| first_call_connected_time | string | 首次接通时间 | 时间分析 | 否 |
| last_call_connected_time | string | 最后一次接通时间 | 时间分析 | 否 |
| zdzx_field_value | string | 走读住校字段取值 | 待按需求确认 | 否 |
| zdzx_field_value_desc | string | 走读住校字段取值描述 | 待按需求确认 | 否 |
| able_to_attend_this_period | string | 本期听课 | 常用维度 | 是 |
| close_order_resistance | string | 关单阻力 | 待按需求确认 | 否 |
| deep_communicate_method | string | 深沟方式 | 待按需求确认 | 否 |
| is_pre_signup | string | 预报名 | 待按需求确认 | 否 |
| send_double_table | string | 双表发送 | 待按需求确认 | 否 |
| pre_sign_up | string | 预报名学科 | 待按需求确认 | 否 |
| lead_first_call | string | 首call情况 | 待按需求确认 | 否 |
| order_lead_count | bigint | 线索id（线索数） | 指标聚合 | 是 |
| jingpin_last_active_date | string | 用户在高中规划最近活跃日期1 | 时间分析 | 否 |
| friend_lead_count | bigint | 线索id（加好友线索） | 指标聚合 | 是 |
| call_answer_lead_count | bigint | 线索id（电话接通线索） | 指标聚合 | 是 |
| shallow_follow_lead_count | bigint | 线索id（浅沟线索） | 指标聚合 | 是 |
| deep_follow_lead_count | bigint | 线索id（深沟线索） | 指标聚合 | 是 |
| noda_lead_count | bigint | 线索id（诺达线索） | 指标聚合 | 是 |
| plan_lead_count | bigint | 线索id（规划线索） | 指标聚合 | 是 |
| pre_apply_lead_count | bigint | 线索id（预报名线索） | 指标聚合 | 是 |
| close_order_lead_count | bigint | 线索id（关单线索） | 指标聚合 | 是 |
| shallow_follow_lead_state | string | 浅沟线索状态 | 待按需求确认 | 否 |
| deep_follow_lead_state | string | 深沟线索状态 | 待按需求确认 | 否 |
| noda_lead_state | string | 诺达线索状态 | 待按需求确认 | 否 |
| plan_lead_state | string | 规划线索状态 | 待按需求确认 | 否 |
| pre_apply_lead_state | string | 预报名线索状态 | 待按需求确认 | 否 |
| close_order_lead_state | string | 关单线索状态 | 待按需求确认 | 否 |
| l15d_jingpin_active_lead_count | bigint | 近15日规划精品app活跃线索数 | 指标聚合 | 是 |
| is_refund_before_clazz_begin | bigint | 是否开课前退款 | 待按需求确认 | 否 |
| is_gy_trace_id | bigint | 是否归因留痕 | 待按需求确认 | 否 |

## 8. 常用过滤条件

- `t.dt = 'YYYYMMDD'`
- `t.hour = 'HH'`
- `t.employee_virtual_department_name = '<待填写>'`
- `t.virtual_department_name_0 = '<待填写>'`
- `t.virtual_department_name_1 = '<待填写>'`
- `t.virtual_department_name_2 = '<待填写>'`
- `t.virtual_department_name_3 = '<待填写>'`

## 9. 常用 join key

- `lead_id`：线索关联/去重
- `user_id`：用户关联
- `trace_id`：留痕/线索链路关联
- `private_sea_id`：私海记录关联
- `employee_id`：员工关联
- `clazz_number`：班级关联

## 10. 常用 SQL 片段

### 简单抽样

```sql
select
    t.dt,
    t.hour,
    t.lead_id,
    t.trace_id,
    t.user_id,
    t.virtual_department_name_0,
    t.virtual_department_name_1,
    t.virtual_department_name_2,
    t.employee_virtual_department_name,
    t.virtual_department_name_3,
    t.private_sea_id,
    t.employee_id,
    t.team_id,
    t.stage,
    t.other_customer,
    t.private_source
from service_dw.app_h_crm_lead_task_process_info_detail_hf t
where t.dt = 'YYYYMMDD'
  and t.hour = 'HH'
  and t.employee_virtual_department_name = '<待填写>'
  and t.virtual_department_name_0 = '<待填写>'
  and t.virtual_department_name_1 = '<待填写>'
limit 20;
```

## 11. 注意事项

- 字段目录来源：`table_fields_full_20260420_092405.json`，字段数 103。
- 所属项目：服务域；owner：王杰42。
- 字段类型和业务口径仍需结合线上 SQL 执行结果或业务文档复核。
- 大宽表查询禁止 `select *`，应只选择需要字段。
- 2026-05-22 起，新 SQL 禁止使用本表 `call_answer_lead_count` 作为 `is_f_call`、首 call 任务数或首 call 任务率来源；首 call 任务指标必须改用 `gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf`，通过 `account_id` 关联 `finance_dw.dim_finance_employee_df` 后再用顾问姓名和 `user_id` 关联主线索数据。
- 本表仍可用于双表发送/回收、任务过程、电话接通线索等字段；使用这些字段时需明确不是 CRM 首 call 任务完成口径。

### 历史备注

- 字段目录来源：`table_fields_full_20260420_092405.json`，字段数 103。
- 所属项目：服务域；owner：王杰42。
- 字段类型和业务口径仍需结合线上 SQL 执行结果或业务文档复核。
- 大宽表查询禁止 `select *`，应只选择需要字段。

### 历史备注

- 字段目录来源：`table_fields_full_20260420_092405.json`，字段数 103。
- 所属项目：服务域；owner：王杰42。
- 字段类型和业务口径仍需结合线上 SQL 执行结果或业务文档复核。
- 大宽表查询禁止 `select *`，应只选择需要字段。

### 历史备注

- 分区限制：查询分区表必须带分区条件。
- department_name 范围限定：涉及部门字段必须过滤；未给取值时使用占位符。
- 字段类型注意事项：PDF 图片 OCR 低置信度字段必须先人工确认。
- 常见报错：字段不存在、库名前缀不正确、小时表遗漏 hour、group by 不完整。
- 待人工确认问题：
- PDF 第 23-25 页字段表为图片型，需人工校验。
