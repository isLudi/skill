# service_dw.dim_crm_assign_rule_lead_detail_hf

## 1. 中文名称

线索分配规则记录

## 2. 表用途

线索分配规则记录。

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
| 无 | - | - | 否 | 未识别 department_name 字段；若查询涉及业务范围仍需人工限定 | 字段目录 |

说明：
- 推荐取值来自 `baijia-data-map/row_permissions.json` 的历史 SQL 归纳；不是永久业务授权边界。
- 用户未给出取值时，生成 SQL 应优先使用占位符或向用户确认，不能擅自扩大范围。

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
- `group_id`：关联 `temp_table.dingxi01_plan_id` 过滤被维护的分配规则组

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
- `lead_assign_plan_actual_valid_count.sql` 将该表作为计划侧主表，通过 `rule_id + plan_id` 关联计划 item，通过 `group_id` 关联计划组维护表。

### 退费分析 SQL 使用备注

- 三份退费分析 SQL 通过 `lead_id + account_domain` 关联该表，其中 `account_domain` 对应财务业绩明细的 `email_prefix`。
- SQL 按 `rule_name` 长 CASE 派生 `channel_1`，该渠道口径来自退费分析历史 SQL，不等同于 `market_channel_case_when_0612.sql` 的最新渠道映射。
- `group_period_term` 从 `rule_name` 前 4 位数字提取，再推导 `friday_period`；规则名前缀格式不符合 MMDD 时会得到 null。
- 该表在退费分析 SQL 中只限定 `dt/hour`，没有独立部门字段过滤，依赖 `lead_id` 来源范围。

### 历史备注

- 字段目录来源：`table_fields_full_20260420_092405.json`，字段数 24。
- 所属项目：服务域；owner：王杰42。
- 字段类型和业务口径仍需结合线上 SQL 执行结果或业务文档复核。

### 历史备注

- 字段目录来源：`table_fields_full_20260420_092405.json`，字段数 24。
- 所属项目：服务域；owner：王杰42。
- 字段类型和业务口径仍需结合线上 SQL 执行结果或业务文档复核。
