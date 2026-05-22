# bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df

## 1. 中文名称

线索成本 GMV 沟通学习全链路表

## 2. 表用途

在青橙过程数据 SQL 中作为有效线索主表，提供线索、用户、分配、规则、渠道、年级、顾问、部门和期次字段。

## 3. 数据粒度

待人工确认。当前 SQL 按 `lead_id` 使用，并通过 `select distinct f.*` 进入基础层。

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 说明 |
|---|---|---|
| `dt` | 待人工确认 | 日期分区 |
| `hour` | 待人工确认 | 小时分区 |

## 6. 强制范围限定字段

| 字段名 | 默认取值/占位符 | 说明 |
|---|---|---|
| `section_assign_employee_first_level_department_name` | `'H业务线'` | 截面分配员工一级部门 |
| `section_assign_employee_second_level_department_name` | `'青橙项目部'` | 截面分配员工二级部门 |
| `period_mapping_first_level_department_name` | `'H业务线'` | 期次映射一级部门 |
| `period_mapping_second_level_department_name` | `('精品班学部','青橙项目部')` | 期次映射二级部门 |
| `virtual_second_department_name` | `'青橙项目部'` | 虚拟二级部门，最终 prc 层过滤 |

## 7. 字段清单

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `lead_id` | 待人工确认 | 线索 ID | join 首次接通、到课 |
| `user_id` | 待人工确认 | 用户编号 | join APP 登录、外呼、上课 |
| `employee_email_prefix` | 待人工确认 | 员工邮箱前缀 | join 外呼、到课 |
| `employee_email_name` | 待人工确认 | 员工姓名/邮箱名 | join 架构 |
| `group_period_year` | 待人工确认 | 期次年份 | 计算 `qici` |
| `group_period_term` | 待人工确认 | 期次期号 | 计算 `qici` |
| `section_assign_time` | 待人工确认 | 分配时间 | 计算分配日期和首次触达时间差 |
| `first_call_time` | 待人工确认 | 首次触达时间 | 计算 `first_call_time_diff_hour` |
| `rule_name` | 待人工确认 | 分配规则名称 | 青橙渠道和年级映射 |
| `lead_purchase_intention_level2_category_name` | 待人工确认 | 意向二级分类/年级 | 年级兜底 |
| `valid_lead_count` | 待人工确认 | 有效线索标记 | SQL 使用 `'1'` |
| `friend_lead_count` | 待人工确认 | 加微标记/数量 | 有效线索时汇总 |
| `virtual_second_department_name` | 待人工确认 | 虚拟二级部门 | 青橙过滤 |
| `put_plan_name` | 待人工确认 | 投放计划名称 | 转化 SQL 取出 |
| `channel_name_1` | 待人工确认 | 一级渠道名称 | 转化 SQL 取出 |
| `channel_name_2` | 待人工确认 | 二级渠道名称 | 转化 SQL 取出 |
| `channel_name_3` | 待人工确认 | 三级渠道名称 | 转化 SQL 取出 |
| `flow_pool_name` | 待人工确认 | 流量池名称 | 转化 SQL 取出 |
| `get_customer_way_name` | 待人工确认 | 获客方式 | 转化 SQL 取出 |
| `virtual_direct_leader_email_name` | 待人工确认 | 虚拟直属主管 | 转化 SQL 输出主管维度 |

## 8. 常用过滤条件

```sql
where f.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
  and f.hour = format_datetime(now() - interval '3' hour, 'HH')
  and f.section_assign_employee_first_level_department_name = 'H业务线'
  and f.section_assign_employee_second_level_department_name = '青橙项目部'
  and f.period_mapping_first_level_department_name = 'H业务线'
  and f.period_mapping_second_level_department_name in ('精品班学部','青橙项目部')
  and f.valid_lead_count = '1'
```

## 9. 常用 join key

- `lead_id`
- `user_id`
- `employee_email_prefix`
- `employee_email_name`

## 10. 常用 SQL 片段

```sql
case when f.valid_lead_count = '1' then 1 else 0 end as v_lead
```

## 11. 注意事项

- 当前 SQL 中本表小时为 `now()-interval '3' hour`，其他小时表多为 `now()-interval '2' hour`，原因待确认。
- 后续生成新 SQL 时不得使用三参数 `date_add` 计算期次，应改为 `interval` 写法。
