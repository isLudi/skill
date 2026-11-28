# temp_table.lvshuai01_jiagou_db

字段类型合并说明（2026-11-28）：类型栏采用本地已记录的平台 SQL 解析输出；历史 Excel 推断不作为当前类型结论。查询输出结构不等同完整 DDL，也不证明当前数据覆盖、唯一性或生产消费者已切换。

维护账号迁移：2026-11-28 用户确认同后缀表由 lvshuai01 接续维护；线上新表身份已核实。字段及业务含义沿用已确认结构，历史 SQL、Excel 扫描和 Query 证据不等于新表本次数据验证。当前使用规则见 [临时表维护迁移](../temp_table_maintenance.md)。

## 1. 中文名称

架构映射表

## 2. 表用途

稳定临时表，用于按期次维护顾问、小组、经理和部门架构映射，常用于外呼过程看板和市场顾问转化看板的架构补全。

数据来源：`E:\2000_work\GAOTU\看板维护表格\jiagou_xian_zhengzhou.xlsx`，sheet `zhengzhou`。

本次扫描：Excel 数据行 5017 行，字段 10 个。检测到空行 7 行。

## 3. 数据粒度

- 顾问-期次-架构映射粒度；存在少量重复 key，join 前建议按目标 key 去重。
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
| qici | string | <YYYYMMDD期> | 是 | 无分区表，必须限定期次 |
| department | string | <部门> | 是 | 架构范围限定 |
| dept_1 | string | <一级架构> | 是 | 架构范围限定 |
| dept_2 | string | <二级架构> | 是 | 架构范围限定 |
| zaizhi | string | 1 | 是 | 通常只取在职顾问 |

说明：临时表虽然规模不大，但生成看板 SQL 时仍应避免无条件扫全表或无约束 join。

## 7. 字段清单

| 字段名 | 类型 | 字段描述 | 常见用途 | 样例值 | 是否常用 |
| --- | --- | --- | --- | --- | --- |
| xiaozu_z | string | 小组长邮箱前缀/拼音标识 | 小组长标识 | hanyuying02；xueyuan02；guojiyuan | 否 |
| employee_email_prefix | string | 顾问/员工邮箱前缀 | 顾问 join key | liujuying；huyajie；qiujunwu | 是 |
| xiaozu | string | 小组长姓名或带编号姓名 | 小组维度 | 韩玉颖02；薛源02；郭纪园 | 是 |
| employee_email_name | string | 顾问/员工姓名，部分值带数字编号 | 顾问 join key | 刘菊颖；呼雅洁；邱君武 | 是 |
| department | string | 架构/部门名称 | 架构范围限定 | 郑州市场顾问部；西安学习顾问一部；西安学习顾问二部 | 是 |
| zaizhi | string | 在职状态标记，常用 1 表示在职 | 在职过滤 | 1 | 是 |
| qici | string | 期次，格式通常为 yyyyMMdd期 | 期次过滤/join | 20260109期；20260116期；20260123期 | 是 |
| dept_1 | string | 一级/业务展示部门 | 一级架构维度 | 市场顾问部；青橙项目部 | 是 |
| dept_2 | string | 二级/城市或团队展示部门 | 二级架构维度 | 郑州顾问部；西安一部；西安二部 | 是 |
| jingli | string | 经理/主管姓名 | 经理维度 | 薛源02；吴志强03；靳煜08 | 是 |

## 8. 常用过滤条件

- `t.qici = '20260403期'`
- `t.zaizhi = '1'`
- `t.department = '<部门>'`

## 9. 常用 join key

- `qici + employee_email_prefix` 关联线索/顾问明细的顾问邮箱前缀。
- `qici + department + xiaozu + employee_email_name` 曾用于市场顾问转化看板的架构匹配。
- `employee_email_name + substr(qici, -5)` 曾用于线索分配计划与实际有效量看板补充 `xiaozu`、`jingli`；跨年份存在期次尾号重复风险，优先确认能否改为完整期次。

本次 Excel key 重复检查：

| join key | 唯一组合数 | 重复组合数 | 涉及重复行数 | 最大重复次数 |
|---|---:|---:|---:|---:|
| qici + employee_email_prefix | 5015 | 2 | 4 | 2 |
| qici + department + xiaozu + employee_email_name | 5015 | 2 | 4 | 2 |

## 10. 常用 SQL 片段

### 简单抽样

```sql
select *
from temp_table.lvshuai01_jiagou_db t
where t.qici = '20260403期'
limit 20;
```

### 字段分布探索

```sql
select
    t.qici,
    count(*) as cnt
from temp_table.lvshuai01_jiagou_db t
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
                partition by t.qici, t.employee_email_prefix
                order by t.qici desc
            ) as rn
        from temp_table.lvshuai01_jiagou_db t
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
- 仅使用 `substr(qici, -5)` 与规则名期次片段关联时，不能保证跨年份唯一；需要长期跨年分析时应改用完整期次字段。
- 该表可能提前维护未来期次架构；某期次在本表存在，不代表事实主表已经产出该期线索或业绩数据。排查“某期次查不到”时，必须单独验证事实主表的派生期次和指标是否非 0。

### 流量画像 SQL 使用备注

- `data_center_market_2683.sql` 最终层通过 `qici + department + xiaozu + employee_email_name` 关联该表，其中 `department = zz.depart`、`xiaozu = zz.zhuguan`。
- 当前结果未输出 `jg` 字段，该 join 可能只是历史遗留；如该 join key 不唯一，仍可能放大结果行。

### 运营侧个人数据 2293 使用备注

- `resources/raw_sql/data_center_market_2293.sql` 的最终层用于修正运营侧个人数据的展示架构：优先使用本表按 `qici + department + xiaozu + employee_email_name` 匹配出来的 `jg.jingli`、`jg.xiaozu`，其次才使用 `temp_table.lvshuai01_jiagou_zx` 和事实宽表字段。
- 典型错误：事实宽表 `virtual_leader_email_name` / `virtual_direct_leader_email_name` 与期次架构表不一致，BI 透视表又绑定最终输出的 `jingli` 字段，导致主管或经理展示到旧架构下。
- 修复原则：最终输出层不要 `select zz.*` 后原样暴露 `zz.jingli`、`zz.zhuguan`；应显式输出 `coalesce(jg.jingli, zx.jingli, zz.jingli) as jingli` 和 `coalesce(jg.xiaozu, zx.xiaozu, zz.zhuguan) as zhuguan`。
- 该 SQL 先构造 `jiagou_period`，按 `qici + department + employee_email_name` 去重后再 join；不要在 `zhuanhua` 聚合后直接 join 本表原始行，否则会同步放大线索、收款和退款等 `sum` 指标。

## 12. 反向联动速查

被以下看板使用：

- `../dashboards/market_consultant_conversion.md`：期次内架构映射。
- `../dashboards/lead_assign_plan_actual_valid_count.md`：按规则名期次尾号补小组和经理。
- `../dashboards/outbound_call_process_dashboard.md`：按期次和顾问邮箱前缀补架构。
- `../dashboards/traffic_profile.md`：历史遗留 join，可能影响行数。
- `../dashboards/data_center_market_datasets.md`：运营侧个人数据 2293 最终展示架构优先使用本表期次架构。

已知风险：

- Web 查询环境正常可用。市场顾问场景必须同时限定 `qici` 和目标部门。
- 本表存在未来期次架构不代表事实主表已有该期数据，排查缺失先读 `../sql_patterns/dashboard_query_patterns.md`。

## 本地登记与平台核验补充（2026-11-28）

历史类型记录（仅说明原文推断来源）：`employee_email_prefix` 原记为 string/bigint（Excel 混合）；`zaizhi` 原记为 string/bigint（Excel 混合）。当前查询输出类型采用上文平台解析记录。

### 1. 中文名称

市场顾问期次带班架构映射表（当前物理绑定）。

### 2. 表用途

市场顾问部当前使用的期次带班架构临时表。2026-11-28 从生产数据集 2054 完整保存 SQL 回读确认，当前表名为 `temp_table.lvshuai01_jiagou_db`。本条记录当前物理绑定，不从其他部门推断市场业务口径。

该物理表由两部门共用，市场切片须限定 `dept_1 = '市场顾问部'`；青橙切片由青橙知识库独立定义。相同表名不代表可混用两个部门的数据范围、指标或架构含义。

### 3. 数据粒度

市场登记的业务键为 `qici + employee_email_prefix`。当前快照的键唯一性、重复行和空值需实测，不继承旧表扫描数值。

### 4. 查询引擎

Presto。天宫任务使用的 Spark 查询另按其实际 SQL 审阅。

### 5. 分区字段

无 `dt/hour` 分区，按期次和本部门切片限定读取。

### 6. 强制范围限定字段

- 市场切片：`dept_1 = '市场顾问部'`。
- 期次：`qici` 使用当前目标所需的完整期次。
- `department`、`dept_2`、`zaizhi` 沿用目标已审定范围，不为渠道 CASE 升级修改它们。

### 7. 字段清单

以下为治理登记的上传列；平台 SQL 解析结果均为 string。

### 8. 常用过滤条件

`dept_1 = '市场顾问部' AND qici = '<YYYYMMDD期>'`。模板占位值需在执行前解析。

### 9. 常用 join key

`qici + employee_email_prefix` 为市场登记键；Join 前按当前 SQL 的去重合同核验，不能据登记键推断当前数据唯一。

### 10. 常用 SQL 片段

```sql
SELECT qici, employee_email_prefix, xiaozu, jingli
FROM temp_table.lvshuai01_jiagou_db
WHERE dept_1 = '市场顾问部'
  AND qici = '<YYYYMMDD期>'
```

此片段仅说明本域范围，不能直接进入生产执行。

### 11. 注意事项

[临时表治理登记](../../../sync-qingcheng-market-temp-tables/references/workflow_registry.json)中的 `market_period_architecture` 登记当前平台表名、目标列、`qici + employee_email_prefix` 键与 `dept_1` 市场范围。生产 SQL 的实际字段、去重与联接逻辑须从实时 SQL 核验，本记录不授权更换生产联接或缩小部门范围。

新任务不得从历史知识快照推断此表的行数、最新期次、上传成功状态或当前数据质量；这些信息需读取当前上传回执或执行受治理查询。

### 补充业务语义与风险

历史关联包含完整期次与员工邮箱前缀；其他 SQL 曾使用员工姓名、部门、小组或期次尾号。使用期次尾号跨年可能错配，应核验目标粒度并检查重复。

### 平台结构与迁移核验

2026-11-28 使用平台 SQL 解析器分别读取新、旧表的 `SELECT *` 输出，字段名、类型和顺序一致。解析器返回字段均为 `string`；这是查询输出结构，不等同于完整 DDL，也不证明两表数据内容、覆盖期次、唯一性或最新上传状态相同。

字段顺序：`xiaozu_z`、`employee_email_prefix`、`xiaozu`、`employee_email_name`、`department`、`zaizhi`、`qici`、`dept_1`、`dept_2`、`jingli`。
