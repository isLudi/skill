# service_dw.dim_crm_assign_rule_lead_detail_hf

## 1. 中文名称

线索分配规则记录

## 2. 表用途

线索分配规则记录。

本 Skill 仅复用该公共表的结构说明，不引入市场顾问部的计划组、渠道或退费分析口径。

库名前缀状态：已确认，来自 `table_fields_full_20260420_092405.json`。

data-map 高频统计：500 条成功 SQL 中出现 60 次，占比 12.0%。

## 3. 数据粒度

待确认；字段目录未提供数据粒度

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
| 无 | - | - | 否 | 未识别 department_name 字段；若查询涉及青橙业务范围，需在主事实表、员工维表或外层过滤中补充范围限定 | 字段目录 |

说明：
- 该表本身不提供稳定的青橙范围字段。
- 如需限定青橙范围，应结合员工维表、主事实表或规则归属来源一起确认。

## 7. 字段清单

| 字段名 | 类型 | 字段描述 | 常见用途 | 是否常用 |
|---|---|---|---|---|
| dt | string | 天级别分区 yyyyMMdd | 分区过滤 | 是 |
| hour | string | 小时级分区 HH | 分区过滤 | 是 |
| lead_id | bigint | 线索id | 主键/关联键 | 是 |
| trace_id | bigint | 留痕id | 主键/关联键 | 是 |
| rule_id | bigint | 规则id | 待按需求确认 | 否 |
| rule_name | string | 规则名字 | 待按需求确认 | 否 |
| plan_id | bigint | 计划id | 待按需求确认 | 否 |
| item_id | bigint | 计划itemId | 待按需求确认 | 否 |
| account_id | bigint | 顾问id | 指标聚合 | 是 |
| account_domain | string | 顾问名字 | 指标聚合 | 是 |
| state | int | 分配状态 | 待按需求确认 | 否 |
| fail_reason | int | 失败原因 | 待按需求确认 | 否 |
| qr_code_type | int | u群二维码类型 | 待按需求确认 | 否 |
| snap_shot | string | 快照信息 | 待按需求确认 | 否 |
| create_by | string | 创建人 | 待按需求确认 | 否 |
| create_time | timestamp | 创建时间 | 时间分析 | 否 |
| update_time | timestamp | 更新时间 | 时间分析 | 否 |
| lead_provider_type | int | 线索类型 | 待按需求确认 | 否 |
| lead_provider_type_name | string | 线索类型 | 待按需求确认 | 否 |
| purchase_intention_id | bigint | 购买意向 | 待按需求确认 | 否 |
| group_id | bigint | 规则组id | 待按需求确认 | 否 |
| scenario_type | int | 0 未知 1 原线下 2 线上 3 线下校区 | 待按需求确认 | 否 |
| assign_way | int | 分配方式 1 权重平均 2 完全平均 3 顺序分配 | 待按需求确认 | 否 |
| assign_way_name | string | 分配方式 1 权重平均 2 完全平均 3 顺序分配 | 待按需求确认 | 否 |

## 8. 常用过滤条件

- `t.dt = 'YYYYMMDD'`
- `t.hour = 'HH'`

## 9. 常用 join key

- `lead_id`：线索关联/去重
- `trace_id`：留痕/线索链路关联
- `rule_id + plan_id`：关联 `service_dw.dim_crm_assign_rule_plan_item_info_hf` 获取计划 item 顾问配置

## 10. 常用 SQL 片段

### 简单抽样

```sql
select
    t.dt,
    t.hour,
    t.lead_id,
    t.trace_id,
    t.rule_id,
    t.rule_name,
    t.plan_id,
    t.item_id,
    t.account_id,
    t.account_domain,
    t.state,
    t.fail_reason,
    t.qr_code_type,
    t.snap_shot,
    t.create_by,
    t.create_time
from service_dw.dim_crm_assign_rule_lead_detail_hf t
where t.dt = 'YYYYMMDD'
  and t.hour = 'HH'
limit 20;
```

## 11. 注意事项

- 字段目录来源：`table_fields_full_20260420_092405.json`，字段数 24。
- 所属项目：服务域；owner：王杰42。
- 字段类型和业务口径仍需结合线上 SQL 执行结果或业务文档复核。
- 如果需要按 `group_id` 限定规则组，必须先在青橙知识库中确认对应映射来源；不得直接复用其他部门的计划组临时表。
