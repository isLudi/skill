# temp_table.lvshuai01_qing_team_goal

字段类型合并说明（2026-11-28）：类型栏采用本地已记录的平台 SQL 解析输出；历史 Excel 推断不作为当前类型结论。查询输出结构不等同完整 DDL，也不证明当前数据覆盖、唯一性或生产消费者已切换。

维护账号迁移：2026-11-28 用户确认同后缀表由 lvshuai01 接续维护；线上新表身份已核实。字段及业务含义沿用已确认结构，历史 SQL、Excel 扫描和 Query 证据不等于新表本次数据验证。当前使用规则见 [临时表维护迁移](../temp_table_maintenance.md)。

## 1. 临时表用途

青橙团队月目标表。当前在 `qingcheng_team_completion_month_raw_20260522.sql` 最终层作为主表，提供月份、学部、小组、大组、目标和层级控制字段，并左连实际业绩。

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
month + xuebu + xiaozu + dazu
```

待人工确认 `emye_c` 是否改变展示粒度。

## 4. 字段清单

| 字段名 | 类型 | 中文含义 | 备注 |
| --- | --- | --- | --- |
| `month` | string | 月份 | join `renchan.moth` |
| `xuebu` | string | 学部 | 最终输出维度 |
| `xiaozu` | string | 小组/主管邮箱 | join `renchan.leader_employee_email_name` |
| `dazu` | string | 大组 | 最终输出维度 |
| `emye_c` | string | 层级/展示控制字段 | `emye_c != '1'` 时展示小组，否则为 `'-'` |
| `goal` | string | 月目标 | 与 `promit`/`promit_4` 对比 |

## 5. 适用看板

- `qingcheng_team_completion_month_raw_20260522`

## 6. join key

```sql
qg.xiaozu = rc.leader_employee_email_name
and qg.month = rc.moth
```

## 7. 不可复用边界

- 默认只用于青橙团队完成度【月】。
- 不得与 `temp_table.lvshuai01_qing_team_g_qi` 期目标表混用。
- 目标单位必须与实际业绩金额单位一致，未确认前不得直接计算完成率。
- 如果 `emye_c = '1'` 代表学部/大组层级目标，则小组展示为 `'-'`；具体业务含义待确认。

## 8. 待确认事项

- 表来源、维护人和刷新频率。
- `goal` 单位。
- `emye_c` 的枚举和值含义。
- `xiaozu` 字段是否存主管邮箱，还是小组名称。

## 本地登记与平台核验补充（2026-11-28）

### 1. 临时表用途

青橙团队月目标表。历史 SQL 在 `qingcheng_team_completion_month_raw_20260522.sql` 最终层作为主表，提供月份、学部、小组、大组、目标和层级控制字段，并左连实际业绩。

### 8. 待确认事项

- 表来源、维护人和刷新频率。
- `goal` 单位。
- `emye_c` 的枚举和值含义。
- `xiaozu` 字段是否存主管邮箱，还是小组名称。

来源维护以临时表上传治理登记及最新回执为准；具体数据新鲜度和质量须重新核验。

### 平台结构与迁移核验

2026-11-28 使用平台 SQL 解析器分别读取新、旧表的 `SELECT *` 输出，字段名、类型和顺序一致。解析器返回字段均为 `string`；这是查询输出结构，不等同于完整 DDL，也不证明两表数据内容、覆盖期次、唯一性或最新上传状态相同。

字段顺序：`month`、`xuebu`、`jingli`、`dazu`、`xiaozu`、`emye_c`、`goal`。
