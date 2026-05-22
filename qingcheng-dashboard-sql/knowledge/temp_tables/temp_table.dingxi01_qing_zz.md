# temp_table.dingxi01_qing_zz

## 1. 临时表用途

青橙组织架构补充表。当前在 `qingcheng_revenue_year_quarter_month_raw_20260522.sql` 中按员工姓名补充直属主管、大主管和学部。

## 2. 来源和刷新方式

| 项目 | 内容 |
|---|---|
| 创建来源 | 待人工确认 |
| 刷新方式 | 待人工确认 |
| 刷新频率 | 待人工确认 |
| 有效期 | 待人工确认 |

## 3. 数据粒度

疑似为：

```text
employee_email_name
```

待人工确认是否存在期次或日期维度。

## 4. 字段清单

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `employee_email_name` | 待人工确认 | 员工姓名/邮箱名 | join `rd.name` |
| `leader_employee_email_name` | 待人工确认 | 直属主管 | 最终输出维度 |
| `dazhuguan` | 待人工确认 | 大主管 | 最终输出维度 |
| `xuebu` | 待人工确认 | 学部 | 最终输出维度 |

## 5. 适用看板

- `qingcheng_revenue_year_quarter_month_raw_20260522`

## 6. join key

```sql
zz.employee_email_name = rd.name
```

## 7. 不可复用边界

- 默认仅用于青橙年季月营收看板。
- 不得默认等同于 `temp_table.dingxi01_qing_team_jg` 或 `temp_table.dingxi01_jiagou_db`。
- 如果需要历史架构归属，必须确认该表是否有期次/日期字段；当前 SQL 未按期次 join。

## 8. 待确认事项

- 表来源、维护人和刷新频率。
- 是否只维护青橙员工。
- 是否存在多行员工架构记录。

