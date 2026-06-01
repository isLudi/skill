# temp_table.dingxi01_jiagou_db

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
|---|---|---|---|
| 无 | 无 | 稳定临时表无 dt/hour 分区 | 否 |

## 6. 强制范围限定字段

| 字段名 | 类型 | 推荐取值 | 是否必填 | 说明 |
|---|---|---|---|---|
| qici | string | <YYYYMMDD期> | 是 | 无分区表，必须限定期次 |
| department | string | <部门> | 是 | 架构范围限定 |
| dept_1 | string | <一级架构> | 是 | 架构范围限定 |
| dept_2 | string | <二级架构> | 是 | 架构范围限定 |
| zaizhi | string/bigint（Excel 混合） | 1 | 是 | 通常只取在职顾问 |

说明：临时表虽然规模不大，但生成看板 SQL 时仍应避免无条件扫全表或无约束 join。

## 7. 字段清单

| 字段名 | 类型 | 字段描述 | 常见用途 | 样例值 | 是否常用 |
|---|---|---|---|---|---|
| xiaozu_z | string | 小组长邮箱前缀/拼音标识 | 小组长标识 | hanyuying02；xueyuan02；guojiyuan | 否 |
| employee_email_prefix | string/bigint（Excel 混合） | 顾问/员工邮箱前缀 | 顾问 join key | liujuying；huyajie；qiujunwu | 是 |
| xiaozu | string | 小组长姓名或带编号姓名 | 小组维度 | 韩玉颖02；薛源02；郭纪园 | 是 |
| employee_email_name | string | 顾问/员工姓名，部分值带数字编号 | 顾问 join key | 刘菊颖；呼雅洁；邱君武 | 是 |
| department | string | 架构/部门名称 | 架构范围限定 | 郑州市场顾问部；西安学习顾问一部；西安学习顾问二部 | 是 |
| zaizhi | string/bigint（Excel 混合） | 在职状态标记，常用 1 表示在职 | 在职过滤 | 1 | 是 |
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
from temp_table.dingxi01_jiagou_db t
where t.qici = '20260403期'
limit 20;
```

### 字段分布探索

```sql
select
    t.qici,
    count(*) as cnt
from temp_table.dingxi01_jiagou_db t
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
        from temp_table.dingxi01_jiagou_db t
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

- `traffic_profile.sql` 最终层通过 `qici + department + xiaozu + employee_email_name` 关联该表，其中 `department = zz.depart`、`xiaozu = zz.zhuguan`。
- 当前结果未输出 `jg` 字段，该 join 可能只是历史遗留；如该 join key 不唯一，仍可能放大结果行。

## 12. 反向联动速查

被以下看板使用：

- `../dashboards/market_consultant_conversion.md`：期次内架构映射。
- `../dashboards/lead_assign_plan_actual_valid_count.md`：按规则名期次尾号补小组和经理。
- `../dashboards/outbound_call_process_dashboard.md`：按期次和顾问邮箱前缀补架构。
- `../dashboards/traffic_profile.md`：历史遗留 join，可能影响行数。

已知风险：

- Web 查询环境正常可用。市场顾问场景必须同时限定 `qici` 和目标部门。
- 本表存在未来期次架构不代表事实主表已有该期数据，排查缺失先读 `../sql_patterns/dashboard_query_patterns.md`。
