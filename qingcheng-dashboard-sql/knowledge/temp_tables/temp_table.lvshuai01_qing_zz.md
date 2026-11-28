# temp_table.lvshuai01_qing_zz

## 1. 临时表用途

青橙组织架构补充表。历史 SQL 在 `qingcheng_revenue_year_quarter_month_raw_20260522.sql` 中按员工姓名补充直属主管、大主管和学部。

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

平台结构已包含 `qici`；旧营收 SQL 仅按员工关联，是否按期次关联需另行确认。

## 4. 字段清单

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `employee_email_name` | string | 员工姓名/邮箱名 | join `rd.name` |
| `leader_employee_email_name` | string | 直属主管 | 最终输出维度 |
| `dazhuguan` | string | 大主管 | 最终输出维度 |
| `xuebu` | string | 学部 | 最终输出维度 |

## 5. 适用看板

- `qingcheng_revenue_year_quarter_month_raw_20260522`

## 6. join key

```sql
zz.employee_email_name = rd.name
```

## 7. 不可复用边界

- 默认仅用于青橙年季月营收看板。
- 不得默认等同于 `temp_table.lvshuai01_qing_team_jg` 或 `temp_table.lvshuai01_jiagou_db`。
- 如果需要历史架构归属，必须核对 `qici` 的覆盖和粒度；历史 SQL 未按期次 join。

## 8. 待确认事项

- 表来源、维护人和刷新频率。
- 是否只维护青橙员工。
- 是否存在多行员工架构记录。


## 平台结构与迁移核验

2026-11-28 使用平台 SQL 解析器分别读取新、旧表的 `SELECT *` 输出，字段名、类型和顺序一致。解析器返回字段均为 `string`；这是查询输出结构，不等同于完整 DDL，也不证明两表数据内容、覆盖期次、唯一性或最新上传状态相同。

字段顺序：`employee_name`、`employee_email_name`、`email_prefix`、`leader_employee_email_name`、`leader_email_prefix`、`dazhuguan`、`xuebu`、`qici`。
