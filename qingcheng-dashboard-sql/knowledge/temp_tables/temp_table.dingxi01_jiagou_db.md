# temp_table.dingxi01_jiagou_db

## 1. 临时表用途

青橙架构映射表。当前用于按期次和员工补充 `department`、`dept_2`、`xiaozu`，并通过 `jg.department is not null` 保留能匹配到架构的线索。

已入库使用场景：

- `qingcheng_process_data_raw_20260522.sql`：按 `employee_email_name + qici` join。
- `qingcheng_daoke_raw_20260522.sql`：按 `employee_email_prefix + qici` join。

两个 join key 不一致，后续复用前必须确认该临时表的员工主键。

## 2. 来源和刷新方式

| 项目 | 内容 |
|---|---|
| 创建来源 | 待人工确认 |
| 刷新方式 | 待人工确认 |
| 刷新频率 | 待人工确认 |
| 有效期 | 待人工确认 |

## 3. 数据粒度

疑似为以下两种之一，待人工确认：

```text
qici + employee_email_name
qici + employee_email_prefix
```

如果一名员工在同一期次存在多条架构记录，join 会放大线索。

## 4. 字段清单

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `qici` | 待人工确认 | 期次 | join 必用 |
| `employee_email_name` | 待人工确认 | 员工姓名/邮箱名 | 过程数据 raw 使用 |
| `employee_email_prefix` | 待人工确认 | 员工邮箱前缀 | 到课 raw 使用 |
| `department` | 待人工确认 | 一级架构/部门 | SQL 要求非空 |
| `dept_2` | 待人工确认 | 二级架构/部门 | 最终输出维度 |
| `xiaozu` | 待人工确认 | 小组 | 最终输出维度 |

## 5. 适用看板

- `qingcheng_process_data_raw_20260522`
- `qingcheng_daoke_raw_20260522`

## 6. join key

过程数据 raw：

```sql
data.employee_email_name = jg.employee_email_name
and data.qici = jg.qici
```

到课 raw：

```sql
data.employee_email_prefix = jg.employee_email_prefix
and data.qici = jg.qici
```

## 7. 不可复用边界

- 该表名不含 `qing`，但当前 SQL 将其作为青橙架构表使用；是否为青橙专用待确认。
- 默认只在已入库的青橙过程数据和到课看板中复用。
- 不得把它等同于市场顾问部架构表或评优架构表。
- 复用前必须确认使用 `employee_email_name` 还是 `employee_email_prefix`。

## 8. 待确认事项

- 表来源、维护人和刷新频率。
- `department`、`dept_2`、`xiaozu` 的层级定义。
- 是否需要额外过滤青橙范围，还是该表已只维护青橙人员。
- 员工主键唯一性：`employee_email_name` 与 `employee_email_prefix` 哪个是标准 join key。

