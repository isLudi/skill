# temp_table.lvshuai01_cost

字段类型合并说明（2026-11-28）：类型栏采用本地已记录的平台 SQL 解析输出；历史 Excel 推断不作为当前类型结论。查询输出结构不等同完整 DDL，也不证明当前数据覆盖、唯一性或生产消费者已切换。

维护账号迁移：2026-11-28 用户确认同后缀表由 lvshuai01 接续维护；线上新表身份已核实。字段及业务含义沿用已确认结构，历史 SQL、Excel 扫描和 Query 证据不等于新表本次数据验证。当前使用规则见 [临时表维护迁移](../temp_table_maintenance.md)。

## 1. 中文名称

渠道成本目标表

## 2. 表用途

稳定临时表，用于按渠道、年级和期次补充单例子成本 `cost` 与目标 `goal`。

字段来源：`resources/raw_sql/data_center_market_2253.sql`。

## 3. 数据粒度

渠道-年级-期次粒度，待确认。

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 含义 | 是否必填 |
| --- | --- | --- | --- |
| 无 | - | 稳定临时表无固定分区；查询时必须限定期次、渠道或年级 | 否 |

## 6. 强制范围限定字段

| 字段名 | 类型 | 推荐取值 | 是否必填 | 说明 |
| --- | --- | --- | --- | --- |
| qici | string | '<期次>' | 是 | 期次 |
| channel | string | '<渠道名称>' | 是 | 渠道名称，与 `channel_map` 关联 |
| grade | string | '<年级>' | 是 | 年级，与 `grade_1` 关联 |

说明：
- 对所有 department_name 相关字段，标记为需要范围限定；
- 不知道默认值时，推荐取值写 `'<待填写>'`。


## 7. 字段清单

| 字段名 | 类型 | 字段描述 | 常见用途 | 是否常用 |
| --- | --- | --- | --- | --- |
| channel | string | 渠道名称 | join `channel_map` | 是 |
| grade | string | 年级 | join `grade_1` | 是 |
| qici | string | 期次 | join `period_name` | 是 |
| cost | string | 单例子成本 | 看板指标 `cb_cb` | 是 |
| goal | string | 单例子目标 | 看板指标 `gl_gl` | 是 |

## 8. 常用过滤条件

- `t.qici = '<期次>'`
- `t.channel = '<渠道名称>'`
- `t.grade = '<年级>'`

## 9. 常用 join key

- `channel + grade + qici`：与 `channel_map + grade_1 + period_name` 关联。

## 10. 常用 SQL 片段

### 简单抽样

```sql
select *
from temp_table.lvshuai01_cost t
where t.qici = '<期次>'
  and t.channel = '<渠道名称>'
  and t.grade = '<年级>'
limit 20;
```

### 成本目标分布

```sql
select
    t.qici,
    t.channel,
    t.grade,
    max(t.cost) as cost,
    max(t.goal) as goal
from temp_table.lvshuai01_cost t
where t.qici = '<期次>'
group by
    t.qici,
    t.channel,
    t.grade
limit 200;
```

## 11. 注意事项

- 字段和口径根据历史 SQL 推断，真实类型、单位和维护来源需人工确认。
- `channel + grade + qici` 应唯一；如果不唯一，关联看板会放大行数。
- **`grade = '0'` 为全年级通配**：当 grade 取值为 `'0'` 时，表示该渠道的 `cost`/`goal` 适用于所有年级。生成 JOIN SQL 时必须加 `or ct.grade = '0'`，否则只匹配到有具体年级值的行（绝大多数渠道 GMV 目标将全为 0）。已验证：同一 `(channel, qici)` 不会同时存在 `grade='0'` 和具体年级值，不会产生行膨胀。

### 流量画像 SQL 使用备注

- `data_center_market_2683.sql` 使用 `ct.channel = channel_map`、`ct.grade = grade_1`、`ct.qici = period_name` 补充 `cb_cb = cost` 和 `gl_gl = goal`。
- 成本目标在结果层用 `coalesce(..., 0)`，无法区分真实 0 和未维护缺失，复用时可额外输出命中标记。

## 12. 反向联动速查

被以下看板使用：

- `../dashboards/market_consultant_conversion.md`：成本 `cb_cb` 和目标 `gl_gl`。
- `../dashboards/market_consultant_lead_conversion_attendance.md`：线索转化到课成本目标。
- `../dashboards/traffic_profile.md`：流量画像成本目标。

已知风险：

- `grade='0'` 是全年级通配，生成 join 时必须使用 `(ct.grade = grade_1 or ct.grade = '0')`，详见 `../pitfalls/common_join_failures.md`。
- Web 查询环境正常可用。必须按 `qici` 收窄。

## 本地登记与平台核验补充（2026-11-28）

历史类型记录（仅说明原文推断来源）：`channel` 原记为 string，待确认；`grade` 原记为 string，待确认；`cost` 原记为 double，待确认；`goal` 原记为 double，待确认；`qici` 原记为 string，待确认。当前查询输出类型采用上文平台解析记录。

### 1. 中文名称

当前市场渠道成本目标表。

### 2. 表用途

当前生产SQL按渠道、年级和期次补充成本与目标，金额和成本含义沿用各模型既有定义。 2026-11-28从实时生产模型2253、2293、2345、2461、2623、2683、3039读取的完整SQL确认当前表名。

### 3. 数据粒度

登记或关联键为`qici + channel + grade`；这不保证当前数据唯一。当前重复、空值、历史覆盖与具体Join粒度须按目标验证。

### 4. 查询引擎

Presto，当前生产查询已实际执行。其他引擎按各目标运行证据确认。

### 5. 分区字段

当前消费者未使用本表的dt/hour分区条件；完整物理分区结构未确认，不能仅据SQL推断无分区。

### 6. 强制范围限定字段

保留各模型已有期次、渠道、年级或员工范围及主查询业务范围。尚未确认通用部门限定或新的联接合同，不自动放宽范围或复用其他部门定义。

### 7. 字段清单

以下为治理登记的上传列，不是重新生成的完整DDL；字段类型见下方平台结构核验。

### 8. 常用过滤条件

`qici = '<YYYYMMDD期>'`仅为占位示意，须以目标已审定范围替换；不能直接进入生产执行。

### 9. 常用 join key

`qici + channel + grade`仅记录现有用法。对映射表或目标表Join前检查键唯一性，禁止未经验证的明细放大或跨期关联。

### 10. 常用 SQL 片段

```sql
SELECT channel, grade, cost, goal
FROM temp_table.lvshuai01_cost
WHERE qici = '<YYYYMMDD期>'
```

该片段不提供独立执行授权，也不确认任何新业务指标。

### 11. 注意事项

[治理登记](../../../sync-qingcheng-market-temp-tables/references/workflow_registry.json)中的`market_cost`确认本域平台表名、上传列与登记键。 本轮只维护当前物理绑定，不上传、重命名或改写临时表数据，不推断当前行数、最新期次或质量状态；这些信息需新回执或受治理查询。confirmed及automatic_compile状态不因本条记录自动提升。

### 补充业务语义与风险

`cost`、`goal` 是各模型使用的成本及目标字段，关联通常使用期次、归一化渠道和年级。`grade='0'` 的渠道级默认值是否回退须按目标 SQL 确认，不能静默扩大匹配；数值计算须显式处理字符串转换。

### 平台结构与迁移核验

2026-11-28 使用平台 SQL 解析器分别读取新、旧表的 `SELECT *` 输出，字段名、类型和顺序一致。解析器返回字段均为 `string`；这是查询输出结构，不等同于完整 DDL，也不证明两表数据内容、覆盖期次、唯一性或最新上传状态相同。

字段顺序：`channel`、`grade`、`cost`、`goal`、`qici`。
