# dw.dim_employee_chain

## 1. 中文名称

员工组织链维表

## 2. 表用途

在青橙年季月营收 SQL 中用于确认员工在青橙项目部路径下的任职起止时间，从而只保留交易发生在员工属于青橙期间的财务业绩。

## 3. 数据粒度

待人工确认。当前 SQL 按 `email_prefix + dep_path + name` 聚合，取最早 `begin_time` 和最晚 `end_time`。

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 说明 |
|---|---|---|
| `dt` | 待人工确认 | 日期分区 |

## 6. 强制范围限定字段

| 字段名 | 默认取值/占位符 | 说明 |
|---|---|---|
| `path_name` | `'高途-H业务线-青橙项目部'` 的前三层路径 | 青橙组织路径 |

## 7. 字段清单

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `email_prefix` | 待人工确认 | 员工邮箱前缀 | 当前 SQL 取出但 join 使用 `name` |
| `path_name` | 待人工确认 | 组织路径 | 取前三层作为 `dep_path` |
| `name` | 待人工确认 | 员工姓名/邮箱名 | join 财务表 `employee_email_name` |
| `talent_type_name` | 待人工确认 | 人才类型 | 当前 SQL 取出 |
| `position_name` | 待人工确认 | 岗位名称 | 当前 SQL 取出 |
| `source_hr_status` | 待人工确认 | HR 状态 | 当前 SQL 取出 |
| `leave_time` | 待人工确认 | 离职时间 | 当前 SQL 取出 |
| `execute_time` | 待人工确认 | 执行时间 | 当前 SQL 取出 |
| `begin_time` | 待人工确认 | 组织关系开始时间 | 用于交易时间过滤 |
| `end_time` | 待人工确认 | 组织关系结束时间 | 用于交易时间过滤 |

## 8. 常用过滤条件

```sql
where dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
  and array_join(slice(split(path_name, '-'), 1, 3), '-') = '高途-H业务线-青橙项目部'
```

## 9. 常用 join key

- `name = finance_dw.app_finance_performance_extend_details_hf.employee_email_name`
- `trade_time >= begin_time and trade_time <= end_time`

## 10. 常用 SQL 片段

```sql
array_join(slice(split(path_name, '-'), 1, 3), '-') as dep_path
```

## 11. 注意事项

- 当前 SQL 使用 `name` join 财务表，若存在重名可能误匹配；更稳妥的标准 key 待确认。
- 使用当前 `dt = now() - interval '24' hour` 的组织链快照读取历史 `begin_time/end_time`，需确认是否覆盖历史组织变更。

