# service_dw.dim_crm_assign_rule_plan_item_info_hf

## 1. 中文名称

分配规则计划 item 信息表

## 2. 表用途

用于记录线索分配规则计划下的顾问 item 配置，包括顾问、顾问分配状态、已分配/计划分配数量、分配上限和启停状态。

该文档是公共表结构的最小说明，字段主要来自历史 SQL 使用字段推断；真实 DDL、字段类型、字段中文名和维护来源待人工确认。

## 3. 数据粒度

待确认；根据 SQL 推断为 `rule_id + plan_id + employee_email_name` 或计划 item 粒度的小时快照。

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 含义 | 是否必填 |
|---|---|---|---|
| dt | string | 天级分区 yyyyMMdd | 是 |
| hour | string | 小时级分区 HH | 是 |

## 6. 强制范围限定字段

| 字段名 | 类型 | 推荐取值 | 是否必填 | 说明 |
|---|---|---|---|---|
| 无 | - | - | 否 | SQL 中未出现 department_name 字段；应通过规则表、计划组或顾问范围收窄 |

## 7. 字段清单

| 字段名 | 类型 | 字段描述 | 常见用途 | 是否常用 |
|---|---|---|---|---|
| dt | string（待确认） | 天级分区 yyyyMMdd | 分区过滤 | 是 |
| hour | string（待确认） | 小时级分区 HH | 分区过滤 | 是 |
| rule_id | bigint（待确认） | 分配规则 ID | 与规则明细表关联 | 是 |
| plan_id | bigint（待确认） | 分配计划 ID | 与规则明细表关联 | 是 |
| employee_email_name | string（待确认） | 顾问姓名/带编号名称 | 顾问维度、与实际量和架构表关联 | 是 |
| employee_state | string/int（待确认） | 顾问分配状态枚举 | 派生可分配、离职、分配达到上限等状态 | 是 |
| assign_lead_count | bigint（待确认） | 计划分配数量或已分配数量 | 计划侧数量指标 | 是 |
| assign_ceiling_count | bigint（待确认） | 分配上限数量 | 计划侧数量指标 | 是 |
| employee_is_enable | string/int（待确认） | 顾问 item 是否启用枚举 | 派生启用/禁用状态 | 是 |
| is_del | string/int（待确认） | 删除标记 | 过滤有效 item，历史 SQL 使用 `is_del = '0'` | 是 |

## 8. 常用过滤条件

- `t.dt = 'YYYYMMDD'`
- `t.hour = 'HH'`
- `t.is_del = '0'`

## 9. 常用 join key

| 左表 | 左字段 | 右表 | 右字段 | 说明 |
|---|---|---|---|---|
| service_dw.dim_crm_assign_rule_lead_detail_hf | rule_id, plan_id | service_dw.dim_crm_assign_rule_plan_item_info_hf | rule_id, plan_id | 获取规则计划下的顾问配置 |
| service_dw.dim_crm_assign_rule_plan_item_info_hf | employee_email_name | finance_dw.dim_finance_employee_df | employee_email_name | 补充顾问在职和组织维度；使用前需确认姓名唯一性 |

## 10. 常用 SQL 片段

### 简单抽样

```sql
select
    t.dt,
    t.hour,
    t.rule_id,
    t.plan_id,
    t.employee_email_name,
    t.employee_state,
    t.assign_lead_count,
    t.assign_ceiling_count,
    t.employee_is_enable,
    t.is_del
from service_dw.dim_crm_assign_rule_plan_item_info_hf t
where t.dt = 'YYYYMMDD'
  and t.hour = 'HH'
  and t.is_del = '0'
limit 20;
```

### 规则计划 item 去重检查

```sql
select
    t.rule_id,
    t.plan_id,
    t.employee_email_name,
    count(*) as cnt
from service_dw.dim_crm_assign_rule_plan_item_info_hf t
where t.dt = 'YYYYMMDD'
  and t.hour = 'HH'
  and t.is_del = '0'
group by 1, 2, 3
having count(*) > 1
limit 50;
```

## 11. 注意事项

- 该表为 SQL 反推最小表文档，完整字段清单需通过数据地图或 `desc service_dw.dim_crm_assign_rule_plan_item_info_hf` 补全。
- 小时表查询必须同时限定 `dt` 和 `hour`。
- `employee_state` 与 `employee_is_enable` 的枚举口径来自用户 SQL：`0/1/2/3` 和 `0/1`，是否与线上字典一致待确认。
- `assign_lead_count` 中文含义待确认；历史 SQL 常按“计划分配数量/已分配数量”使用，实际口径需结合具体查询确认。
- 与规则明细表关联时，必须确认 `rule_id + plan_id` 在当前分区下的唯一性，否则会放大计划侧数量。
