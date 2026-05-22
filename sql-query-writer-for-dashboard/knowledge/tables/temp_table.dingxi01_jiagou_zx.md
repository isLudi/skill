# temp_table.dingxi01_jiagou_zx

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
|---|---|---|---|
| 无 | 无 | 稳定临时表无 dt/hour 分区 | 否 |

## 6. 强制范围限定字段

| 字段名 | 类型 | 推荐取值 | 是否必填 | 说明 |
|---|---|---|---|---|
| department | string | <部门> | 是 | 架构范围限定 |
| zaizhi | string/bigint（Excel 混合） | 1 | 是 | 通常只取在职顾问 |
| employee_email_name | string | <顾问姓名> | 是 | 按员工关联时建议限定范围 |

说明：临时表虽然规模不大，但生成看板 SQL 时仍应避免无条件扫全表或无约束 join。

## 7. 字段清单

| 字段名 | 类型 | 字段描述 | 常见用途 | 样例值 | 是否常用 |
|---|---|---|---|---|---|
| xiaozu_z | string | 小组长邮箱前缀/拼音标识 | 小组长标识 | zuoyingxue；zhuzhaorong；zhoumaorong | 否 |
| employee_email_prefix | string | 顾问/员工邮箱前缀 | 顾问 join key | zhuxiangyao；zhangyaxin13；songzeshuo | 是 |
| xiaozu | string | 小组长姓名或带编号姓名 | 小组维度 | 左颖雪；朱兆荣；周茂荣 | 是 |
| employee_email_name | string | 顾问/员工姓名，部分值带数字编号 | 顾问 join key | 朱湘瑶；张雅馨13；宋泽硕 | 是 |
| department | string | 架构/部门名称 | 架构范围限定 | 西安一部；西安二部；郑州顾问部 | 是 |
| zaizhi | string/bigint（Excel 混合） | 在职状态标记，常用 1 表示在职 | 在职过滤 | 1；0 | 是 |
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
from temp_table.dingxi01_jiagou_zx t
where t.zaizhi = '1'
limit 20;
```

### 字段分布探索

```sql
select
    t.department,
    count(*) as cnt
from temp_table.dingxi01_jiagou_zx t
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
        from temp_table.dingxi01_jiagou_zx t
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
- 该表无 `qici` 字段，适合作为当前在职架构名单或展示架构补充，不适合表达“某期次参评名单”。用于替代 `temp_table.dingxi01_pingyou_jg` 时，必须说明口径从“参评顾问”变为“在职架构顾问”。

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
        from temp_table.dingxi01_jiagou_zx t
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

- `traffic_profile.sql` 最终层通过 `zx.employee_email_name = zz.employee_email_name` 补充 `xiaozu`。
- 该表无 `qici` 字段，流量画像中得到的是当前专项架构口径，不代表某期次历史架构；跨期复盘时需确认是否改用 `temp_table.dingxi01_jiagou_db`。

### 退费分析 SQL 使用备注

- `refund_multi_subject_user_ratio.sql`、`refund_subject_product.sql`、`refund_reason_analysis.sql` 均通过 `employee_email_name = name` 关联该表，补充 `xiaozu`、`jingli`。
- 该表无 `qici` 字段，因此三份退费分析 SQL 的架构是当前专项架构口径，不是订单发生期的历史架构。
