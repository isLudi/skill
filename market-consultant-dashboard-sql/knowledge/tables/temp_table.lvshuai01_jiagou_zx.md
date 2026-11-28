# temp_table.lvshuai01_jiagou_zx

字段类型合并说明（2026-11-28）：类型栏采用本地已记录的平台 SQL 解析输出；历史 Excel 推断不作为当前类型结论。查询输出结构不等同完整 DDL，也不证明当前数据覆盖、唯一性或生产消费者已切换。

维护账号迁移：2026-11-28 用户确认同后缀表由 lvshuai01 接续维护；线上新表身份已核实。字段及业务含义沿用已确认结构，历史 SQL、Excel 扫描和 Query 证据不等于新表本次数据验证。当前使用规则见 [临时表维护迁移](../temp_table_maintenance.md)。

## 1. 中文名称

员工专项架构映射表

## 2. 表用途

稳定临时表，用于按员工补充专项架构、小组和经理信息，市场顾问转化看板中常用于补充 `xiaozu` 和 `jingli`。

数据来源：`E:\2000_work\GAOTU\看板维护表格\jiagou2026_zx.xlsx`，sheet `Sheet1`。

本次扫描：Excel 数据行 885 行，字段 7 个。

## 3. 数据粒度

- 顾问-专项架构粒度；没有 qici 字段，使用时需注意是否可跨期复用。
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
| department | string | <部门> | 是 | 架构范围限定 |
| zaizhi | string | 1 | 是 | 通常只取在职顾问 |
| employee_email_name | string | <顾问姓名> | 是 | 按员工关联时建议限定范围 |

说明：临时表虽然规模不大，但生成看板 SQL 时仍应避免无条件扫全表或无约束 join。

## 7. 字段清单

| 字段名 | 类型 | 字段描述 | 常见用途 | 样例值 | 是否常用 |
| --- | --- | --- | --- | --- | --- |
| xiaozu_z | string | 小组长邮箱前缀/拼音标识 | 小组长标识 | zuoyingxue；zhuzhaorong；zhoumaorong | 否 |
| employee_email_prefix | string | 顾问/员工邮箱前缀 | 顾问 join key | zhuxiangyao；zhangyaxin13；songzeshuo | 是 |
| xiaozu | string | 小组长姓名或带编号姓名 | 小组维度 | 左颖雪；朱兆荣；周茂荣 | 是 |
| employee_email_name | string | 顾问/员工姓名，部分值带数字编号 | 顾问 join key | 朱湘瑶；张雅馨13；宋泽硕 | 是 |
| department | string | 架构/部门名称 | 架构范围限定 | 西安一部；西安二部；郑州顾问部 | 是 |
| zaizhi | string | 在职状态标记，常用 1 表示在职 | 在职过滤 | 1；0 | 是 |
| jingli | string | 经理/主管姓名 | 经理维度 | 靳煜；位克兢；- | 是 |

## 8. 常用过滤条件

- `t.zaizhi = '1'`
- `t.department = '<部门>'`

## 9. 常用 join key

- `employee_email_name` 关联主表顾问姓名。
- `employee_email_prefix` 可关联邮箱前缀，但需先确认主表字段口径。

本次 Excel key 重复检查：

| join key | 唯一组合数 | 重复组合数 | 涉及重复行数 | 最大重复次数 |
|---|---:|---:|---:|---:|
| employee_email_name | 881 | 4 | 8 | 2 |
| employee_email_prefix | 881 | 4 | 8 | 2 |

## 10. 常用 SQL 片段

### 简单抽样

```sql
select *
from temp_table.lvshuai01_jiagou_zx t
where t.zaizhi = '1'
limit 20;
```

### 字段分布探索

```sql
select
    t.department,
    count(*) as cnt
from temp_table.lvshuai01_jiagou_zx t
group by t.department
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
                partition by t.employee_email_name
                order by t.employee_email_name desc
            ) as rn
        from temp_table.lvshuai01_jiagou_zx t
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
- 该表无 `qici` 字段，适合作为当前在职架构名单或展示架构补充，不适合表达“某期次参评名单”。用于替代 `temp_table.zhangjunyan01_pingyou_jg` 时，必须说明口径从“参评顾问”变为“在职架构顾问”。

## 12. 替代评优名单使用模板

当用户不要求严格评优参评名单，只需要市场顾问在职架构范围时，可使用以下模板生成顾问名单：

```sql
jiagou_zx_active as (
    select
        employee_email_name,
        employee_email_prefix,
        xiaozu,
        jingli,
        department
    from (
        select
            t.*,
            row_number() over (
                partition by t.employee_email_name
                order by
                    case
                        when t.department = '郑州顾问部' then 1
                        when t.department = '西安一部' then 2
                        when t.department = '西安二部' then 3
                        else 9
                    end,
                    t.employee_email_prefix,
                    t.xiaozu,
                    t.jingli
            ) as rn
        from temp_table.lvshuai01_jiagou_zx t
        where cast(t.zaizhi as varchar) = '1'
          and t.department in ('郑州顾问部', '西安一部', '西安二部')
    ) x
    where rn = 1
),
eligible_consultant_name as (
    select distinct
        employee_email_name as name
    from jiagou_zx_active
)
```

### 流量画像 SQL 使用备注

- `data_center_market_2683.sql` 最终层通过 `zx.employee_email_name = zz.employee_email_name` 补充 `xiaozu`。
- 该表无 `qici` 字段，流量画像中得到的是当前专项架构口径，不代表某期次历史架构；跨期复盘时需确认是否改用 `temp_table.lvshuai01_jiagou_db`。

### 运营侧个人数据 2293 使用备注

- `resources/raw_sql/data_center_market_2293.sql` 中本表只作为当前在职架构兜底，不能优先替代 `temp_table.lvshuai01_jiagou_db` 的期次架构。
- 该 SQL 使用 `zx_active` 先按 `employee_email_name` 去重，并限定 `cast(zaizhi as varchar) = '1'`、`department in ('郑州顾问部', '西安一部', '西安二部')`，避免当前架构表重复 key 放大运营侧个人数据。
- 展示经理/主管字段的优先级为：`temp_table.lvshuai01_jiagou_db` 期次架构 > 本表当前在职架构 > 事实宽表 `virtual_*` 字段。

### 退费分析 SQL 使用备注

- 当前 2349 科目/产品/年级退款金额占比 SQL 通过 `employee_email_name = name` 关联该表，补充 `xiaozu`、`jingli`。
- 当前 2349 与 2353 通过同一方式关联该表。该表无 `qici` 字段，因此两者使用当前专项架构，不是订单发生期架构。

## 13. 反向联动速查

被以下看板使用：

- `../dashboards/market_consultant_conversion.md`、`../dashboards/traffic_profile.md`：补充当前小组或经理。
- `../dashboards/consultant_sales_ranking_evaluation.md`：季度/半年 clean 脚本用作当前在职顾问名单。
- `../dashboards/market_channel_conversion_profile.md`：2349 与 2353 的唯一当前说明入口。
- `../dashboards/data_center_market_datasets.md`：运营侧个人数据 2293 当前架构兜底和去重来源。

已知风险：

- Web 查询环境正常可用。作为在职名单时必须限定 `cast(zaizhi as varchar) = '1'` 和目标部门，并按 `employee_email_name` 去重。
- 该表无 `qici`，不能替代期次历史架构或严格参评名单。

## 本地登记与平台核验补充（2026-11-28）

历史类型记录（仅说明原文推断来源）：`zaizhi` 原记为 string/bigint（Excel 混合）。当前查询输出类型采用上文平台解析记录。

### 1. 中文名称

当前员工专项架构关联表。

### 2. 表用途

当前生产SQL按员工关联补充专项小组与经理，不据表名推断跨期或跨部门可用范围。 2026-11-28从实时生产模型2253、2293、2344、2345、2349、2350、2353、2423、2424、2461、2623、2634、2683、2742、3039读取的完整SQL确认当前表名。

### 3. 数据粒度

登记或关联键为`以各生产SQL的实际员工关联条件为准`；这不保证当前数据唯一。当前重复、空值、历史覆盖与具体Join粒度须按目标验证。

### 4. 查询引擎

Presto，当前生产查询已实际执行。其他引擎按各目标运行证据确认。

### 5. 分区字段

当前消费者未使用本表的dt/hour分区条件；完整物理分区结构未确认，不能仅据SQL推断无分区。

### 6. 强制范围限定字段

保留各模型已有期次、渠道、年级或员工范围及主查询业务范围。尚未确认通用部门限定或新的联接合同，不自动放宽范围或复用其他部门定义。

### 7. 字段清单

以下为当前SQL实际引用的列名子集，不是重新生成的完整DDL；字段类型见下方平台结构核验。

### 8. 常用过滤条件

`department = '<已审定值>'`仅为占位示意，须以目标已审定范围替换；不能直接进入生产执行。

### 9. 常用 join key

`以各生产SQL的实际员工关联条件为准`仅记录现有用法。对映射表或目标表Join前检查键唯一性，禁止未经验证的明细放大或跨期关联。

### 10. 常用 SQL 片段

```sql
SELECT department, employee_email_name, employee_email_prefix, jingli
FROM temp_table.lvshuai01_jiagou_zx
WHERE department = '<已审定值>'
```

该片段不提供独立执行授权，也不确认任何新业务指标。

### 11. 注意事项

当前仅根据本域生产SQL的实际引用登记物理绑定；上游工作簿、完整DDL、业务键唯一性与完整适用范围仍待确认。 本轮只维护当前物理绑定，不上传、重命名或改写临时表数据，不推断当前行数、最新期次或质量状态；这些信息需新回执或受治理查询。confirmed及automatic_compile状态不因本条记录自动提升。

### 补充业务语义与风险

该表包含 `xiaozu_z`，没有 `qici`；按姓名或邮箱前缀关联前须验证同名及重复，不能直接把当前架构当成历史期次架构。

### 平台结构与迁移核验

2026-11-28 使用平台 SQL 解析器分别读取新、旧表的 `SELECT *` 输出，字段名、类型和顺序一致。解析器返回字段均为 `string`；这是查询输出结构，不等同于完整 DDL，也不证明两表数据内容、覆盖期次、唯一性或最新上传状态相同。

字段顺序：`xiaozu_z`、`employee_email_prefix`、`xiaozu`、`employee_email_name`、`department`、`zaizhi`、`jingli`。
