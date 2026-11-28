# temp_table.lvshuai01_daoke_1_6_t

字段类型合并说明（2026-11-28）：类型栏采用本地已记录的平台 SQL 解析输出；历史 Excel 推断不作为当前类型结论。查询输出结构不等同完整 DDL，也不证明当前数据覆盖、唯一性或生产消费者已切换。

维护账号迁移：2026-11-28 用户确认同后缀表由 lvshuai01 接续维护；线上新表身份已核实。字段及业务含义沿用已确认结构，历史 SQL、Excel 扫描和 Query 证据不等于新表本次数据验证。当前使用规则见 [临时表维护迁移](../temp_table_maintenance.md)。

## 1. 中文名称

到课课次映射表

## 2. 表用途

稳定临时表，按渠道、期次、年级、开课时间映射第 1-6 课课次，支持首节到课、有效到课和课次到课口径。

数据来源：`E:\2000_work\GAOTU\看板维护表格\daoke_t_one_six.xlsx`，sheet `Sheet1`。

本次扫描：Excel 数据行 2862 行，字段 7 个。检测到空行 1 行。

## 3. 数据粒度

- 渠道-期次-年级-开课时间-课次粒度；Excel 中存在重复 key，join 前建议先 distinct。
- 稳定临时表，无 `dt`/`hour` 分区，生成 SQL 时必须用期次、架构、渠道或员工条件收窄范围。

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 含义 | 是否必填 |
| --- | --- | --- | --- |
| 无 | 无 | 稳定临时表无 dt/hour 分区 | 否 |

## 6. 强制范围限定字段

| 字段名 | 类型 | 推荐取值 | 是否必填 | 说明 |
| --- | --- | --- | --- | --- |
| qici | string | <YYYYMMDD期> | 是 | 必须限定期次防止扫全表 |
| qudao | string | <渠道> | 是 | 与看板 channel_map_1 关联 |
| grade | string | <年级> | 是 | 与线索年级关联 |
| ke_1 | string | 1/3 | 是 | 首节到课通常取 1；曹忆IP99元取 3 |

说明：临时表虽然规模不大，但生成看板 SQL 时仍应避免无条件扫全表或无约束 join。

## 7. 字段清单

| 字段名 | 类型 | 字段描述 | 常见用途 | 样例值 | 是否常用 |
| --- | --- | --- | --- | --- | --- |
| qudao | string | 原始渠道/看板渠道匹配字段 | 到课渠道匹配 | 春春ip99元；koc5元；图书KOC | 是 |
| begin_time | string | 开课时间，用于与行课明细的 begin_time 匹配 | 开课时间 join | 2026-01-16 18:20:00；2026-01-16 19:40:00；2026-01-17 18:20:00 | 是 |
| qici | string | 期次，格式通常为 yyyyMMdd期 | 期次过滤/join | 20260116期；20260109期；20260123期 | 是 |
| dow | string | 周几/星期标签，Excel 中为数字 | 课程时间标签 | 4；5；6 | 否 |
| grade | string | 年级 | 年级维度/join | 高一；高二；高三 | 是 |
| ke_1 | string | 第 1-6 课课次标签 | 首节/课次到课口径 | 1；2；3 | 是 |
| channel | string | 展示/归因渠道名称 | 渠道展示/聚合 | 陈瑞春；自孵化KOC-5元纯课；图书KOC达人 | 是 |

## 8. 常用过滤条件

- `t.qici = '20260403期'`
- `t.ke_1 in (1, 3)`
- `t.qudao = '<渠道>'`
- `t.grade = '<年级>'`

## 9. 常用 join key

- `qici + qudao + grade + begin_time` 关联 `service_dw.dws_service_user_learn_detail_hf` 的 `qici/channel_map_1/grade_1/begin_time`。
- `ke_1` 只用于课次筛选，不建议单独作为 join key。

本次 Excel key 重复检查：

| join key | 唯一组合数 | 重复组合数 | 涉及重复行数 | 最大重复次数 |
|---|---:|---:|---:|---:|
| qici + qudao + grade + begin_time | 2556 | 306 | 612 | 2 |
| qici + qudao + grade + begin_time + ke_1 | 2556 | 306 | 612 | 2 |

## 10. 常用 SQL 片段

### 简单抽样

```sql
select *
from temp_table.lvshuai01_daoke_1_6_t t
where t.qici = '20260403期'
limit 20;
```

### 字段分布探索

```sql
select
    t.qici,
    count(*) as cnt
from temp_table.lvshuai01_daoke_1_6_t t
group by t.qici
order by cnt desc
limit 50;
```

### 去重 join 前处理模板

```sql
with mapped as (
    select *
    from (
        select
            t.*,
            row_number() over (
                partition by t.qici, t.qudao, t.grade, t.begin_time
                order by t.qici desc
            ) as rn
        from temp_table.lvshuai01_daoke_1_6_t t
    ) x
    where x.rn = 1
)
select *
from mapped
limit 20;
```

## 11. 注意事项

- 字段类型来自 Excel 内容推断，若查询平台中实际 DDL 不同，以平台为准。
- 所有探索查询必须加 `limit`；涉及架构或部门字段时必须加范围限定。
- 如果 join key 存在重复，生成 SQL 时需使用 `row_number`、`distinct` 或先聚合，避免主表行数被放大。
- 市场顾问线索转化到课最新 raw SQL 中，本表只补充手工课次 `manual_ke_1`；最终主指标 `ke_*` / `v_ke_*` 使用按 `qici + channel_map_1 + grade_1` 内实际开课 `begin_time` 自动排序得到的 `auto_ke_1`。

### 流量画像 SQL 使用备注

- `data_center_market_2683.sql` 使用 `qici + channel + grade + begin_time` 关联，而不是 `qudao` 字段。
- `曹忆` 渠道使用 `ke_1 = '3'` 判断到课/有效到课，其他渠道使用 `ke_1 = '1'`。
- 普通到课判断来自行课表 `live_learn_duration > 0`，有效到课判断来自行课表 `is_valid_live_learn = '1'`；该临时表只提供课次映射。

### 市场顾问线索转化到课 SQL 使用备注

- `market_consultant_lead_conversion_attendance.sql` 使用 `qici + channel_map_1 + grade_1 + begin_time_slot` 关联本表的 `qici + qudao + grade + begin_time`，并先按该 key 去重。
- 该 SQL 的最终主到课字段 `ke_1` ~ `ke_6`、`v_ke_1` ~ `v_ke_6` 使用自动排序得到的 `auto_ke_1`；手工映射字段输出为 `manual_ke_1` ~ `manual_ke_6`、`manual_v_ke_1` ~ `manual_v_ke_6`。
- 同一 SQL 保留自动/手工课次对照计数，用于检查临时表课次维护与行课自动课次是否一致。

## 12. 反向联动速查

被以下看板使用：

- `../dashboards/market_consultant_lead_conversion_attendance.md`：首节/有效到课映射。
- `../dashboards/traffic_profile.md`：流量画像到课映射。
- `../dashboards/outbound_call_process_dashboard.md`：外呼过程到课补充。

已知风险：

- `manual_*` 或自动/手工对照异常时先读 `../pitfalls/common_join_failures.md`，重点检查 `(qici, channel/qudao, grade, begin_time)`；主口径 `ke_*` / `v_ke_*` 异常时还要检查自动槽位排序和候选窗口。
- Web 查询环境正常可用。必须按期次收窄。

## 本地登记与平台核验补充（2026-11-28）

历史类型记录（仅说明原文推断来源）：`dow` 原记为 bigint（Excel 推断）；`ke_1` 原记为 bigint（Excel 推断）。当前查询输出类型采用上文平台解析记录。

### 1. 中文名称

市场顾问到课课次映射表（当前物理绑定）。

### 2. 表用途

市场顾问部当前到课课次临时表。2026-11-28 从生产数据集 2054 完整保存 SQL 回读确认，当前表名为 `temp_table.lvshuai01_daoke_1_6_t`。

### 3. 数据粒度

治理登记按期次、渠道、年级、开课时间与课次管理；具体 Join 键和当前唯一性按目标 SQL 与本次数据核验。

### 4. 查询引擎

Presto。

### 5. 分区字段

无 `dt/hour` 分区，读取限定实际业务期次。

### 6. 强制范围限定字段

`qici` 限定目标完整业务期次；`qudao/channel`、`grade`、`begin_time`、`dow/ke_1` 沿用目标已审定的渠道与课次条件。

### 7. 字段清单

以下为治理登记的七个上传列；平台 SQL 解析结果均为 string。

### 8. 常用过滤条件

`qici = '<YYYYMMDD期>'`，再结合目标现有的渠道、年级及课次范围。

### 9. 常用 join key

以各生产 SQL 已审定的期次、渠道、年级和课次组合为准。上传登记包含 `qici/qudao/grade/begin_time/dow/ke_1` 组合，不据此保证 Join 不放大。

### 10. 常用 SQL 片段

```sql
SELECT qici, qudao, channel, grade, begin_time
FROM temp_table.lvshuai01_daoke_1_6_t
WHERE qici = '<YYYYMMDD期>'
```

此片段仅展示字段与期次范围，须先补齐目标已审定条件才能执行。

### 11. 注意事项

[临时表治理登记](../../../sync-qingcheng-market-temp-tables/references/workflow_registry.json)中的 `market_attendance_schedule` 记录当前平台表名、输入列、期次与渠道约束。这里只同步已登记的市场物理绑定，不把生产 SQL 里的字段用法提升为新的已确认指标契约。

查询保留其实际期次、渠道、年级与时间联接条件；不得仅因渠道共享 CASE 升级而修改课次记录、联接粒度或到课计算。当前上传质量、行数和可用期次需以新回执或实际查询验证。

### 补充业务语义与风险

历史课次映射使用 `qici + qudao + grade + begin_time` 匹配，`ke_1` 表示第 1 至第 6 课而非只能表示首课；历史源曾出现重复键，当前必须重新核验。特殊渠道的首课规则应以目标 SQL 为准。

### 平台结构与迁移核验

2026-11-28 使用平台 SQL 解析器分别读取新、旧表的 `SELECT *` 输出，字段名、类型和顺序一致。解析器返回字段均为 `string`；这是查询输出结构，不等同于完整 DDL，也不证明两表数据内容、覆盖期次、唯一性或最新上传状态相同。

字段顺序：`qudao`、`begin_time`、`qici`、`dow`、`grade`、`ke_1`、`channel`。
