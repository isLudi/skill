# 顾问销售评优看板

## 1. 来源

原始 SQL：`resources/raw_sql/consultant_sales_ranking_evaluation.sql`

来源文件：`D:\Feishu\评优.txt`

入库时间：2026-05-02

## 2. 查询目标

用于计算市场顾问销售评优数据。底层使用财务业绩流水计算顾问净收、总收、退款、人产 ROI、退费率和排名位置，并分别按期次、月度、季度、半年四种周期聚合。

该 SQL 与 `market_consultant_conversion.sql` 都服务于顾问销售数据分析，但聚合口径不同：

- `market_consultant_conversion.sql`：基于线索成本转化全链路表，按期次、渠道、规则、年级、顾问等维度聚合转化、GMV、净收等指标。
- `consultant_sales_ranking_evaluation.sql`：基于财务业绩流水和评优临时架构人产表，按顾问及不同时间周期聚合销售评优排名指标。

## 3. 使用表

| 表名 | 别名/CTE | 用途 |
|---|---|---|
| `finance_dw.app_finance_performance_extend_details_hf` | `dd` 来源表 | 财务业绩扩展明细，提供订单流水、交易状态、交易类型、价格、顾问、交易时间和课程信息 |
| `temp_table.dingxi01_pingyou_jg` | `pg` | 评优架构人产临时表，提供顾问期次、架构、渠道、人产、年级、在职和是否参与评优 |

## 4. SQL 结构

原始文件包含 4 段独立 SQL，结构基本一致，仅 `process` 之后的聚合周期不同。

| 段落 | 聚合周期 | 输出周期字段 | 说明 |
|---|---|---|---|
| 期次数据 | 期次 | `qici` | 按每个期次计算顾问 ROI、退费率和排名 |
| 月度数据 | 月 | `moth` | `substring(qici, 1, 6)` 聚合到月份，字段名保留原 SQL 拼写 `moth` |
| 季度数据 | 季度 | `quarter` | 按季度聚合，并包含 2026/2027 部分硬编码季度规则 |
| 半年数据 | 半年 | `half_year` | 4-9 月归为上半年，10-次年 3 月归为上一年下半年 |

## 5. CTE 结构

| CTE | 用途 | 关键字段 |
|---|---|---|
| `dd` | 从财务业绩流水表抽取订单/退款明细，按 `trade_time` 推导期次 | `qici`, `name`, `user_id1`, `trade_type`, `trade_status`, `price` |
| `gmv_t` | 处理 `调课调班`，按 `name + user_id1` 汇总并去重，排除总金额为 0 的记录 | `name_total_price`, `dup_rn` |
| `gmv_z` | 处理 `正常订单`，按订单、用户、顾问、期次等维度汇总 `price` | `name_total_price` |
| `rd` | 合并正常订单和调课调班结果 | `name`, `qici`, `name_total_price` |
| `process` | 将评优架构人产表与财务流水按顾问和期次关联，计算净收、总收、退款 | `pt`, `inc`, `ref`, `renchan` |
| `rank` | 计算或保留测试渠道标记，并在期次段直接计算 `roi`、`refd` | `ceshi`, `roi`, `refd` |
| `rank_h` | 月度/季度/半年段聚合到周期-顾问粒度，并计算 `roi`、`refd` | `moth`/`quarter`/`half_year`, `roi`, `refd` |
| `rk_r` | 按周期内 ROI 降序排名 | `rank_in_roi` |
| `ref_rank` | 按退费率和退款金额规则排名 | `rank_in_ref` |
| final select | 输出排名百分比和测试渠道标签 | `rank_position_roi`, `rank_position_ref`, `cs_channel_rank`, `cs_80_rank` |

## 6. join 关系

| 左表/CTE | 右表/CTE | join key | join 类型 | 说明 |
|---|---|---|---|---|
| `temp_table.dingxi01_pingyou_jg pg` | `rd` | `pg.employee_email_name = rd.name` + `pg.qici = rd.qici` | left join | 将顾问期次架构人产信息与财务流水结果关联 |

## 7. where 条件

财务流水分区：

```sql
dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
and hour = format_datetime(now() - interval '2' hour, 'HH')
```

财务流水部门范围：

```sql
employee_first_level_department_name = 'H业务线'
and employee_second_level_department_name = '市场部'
and employee_third_level_department_name = '市场顾问部'
```

期次范围：

```sql
qici >= '20260320期'
```

评优临时表范围：

```sql
pg.zaizhi = '1'
and pg.is_emp = '是'
```

## 8. group by 维度

期次段：

- `qici`
- `employee_email_name`
- `dept`
- `jingli`
- `xiaozu`
- `channel`
- `renchan`
- `grade`
- `is_emp`

月度/季度/半年段最终顾问聚合：

- `moth` / `quarter` / `half_year`
- `employee_email_name`
- `dept`
- `jingli`
- `xiaozu`

## 9. 聚合指标

| 指标名 | SQL 表达式 | 口径说明 | 状态 |
|---|---|---|---|
| `pt` | `sum(name_total_price)` | 净收，正负流水合计 | 来自历史 SQL |
| `inc` | `sum(case when name_total_price > 0 then name_total_price else 0 end)` | 总收，只累计正向流水 | 来自历史 SQL |
| `ref` | `sum(case when name_total_price < 0 then name_total_price else 0 end)` | 退款，只累计负向流水 | 来自历史 SQL |
| `renchan` | `cast(pg.renchan as decimal)` 或周期聚合 `sum(renchan)` | 人产分母/目标值 | 待人工确认字段含义 |
| `roi` | `round(coalesce(pt / renchan, 0), 4)` 或 `round(coalesce(sum(pt) / sum(renchan), 0), 4)` | 净收 / 人产 | 来自历史 SQL |
| `refd` | `round(coalesce(-ref / nullif(inc, 0), 0), 4)` 或周期聚合版本 | 退费率，退款绝对值 / 总收 | 来自历史 SQL |
| `rank_in_roi` | `rank() over (partition by 周期 order by roi desc)` | 周期内 ROI 排名 | 来自历史 SQL |
| `rank_in_ref` | `row_number() over (partition by 周期 order by ...)` | 周期内退费排名，优先有营收且退费率低 | 来自历史 SQL |
| `rank_position_roi` | `rank_in_roi / count(*) over (partition by 周期)` | ROI 排名位置百分比 | 来自历史 SQL |
| `rank_position_ref` | `rank_in_ref / count(*) over (partition by 周期)` | 退费排名位置百分比 | 来自历史 SQL |
| `cs_channel_rank` | `case when channel like '%抖音私域%' or channel like '%抖音私信%' then 10 else 0 end` | 测试渠道标记 | 来自历史 SQL |
| `cs_80_rank` | `case when 测试渠道 and roi >= 0.8 then 2 else 0 end` | 测试渠道 ROI 达标标记 | 来自历史 SQL |

## 10. 可复用 SQL 模式

- 财务流水正负金额：正向流水计入 `inc`，负向流水计入 `ref`，正负合计为 `pt`。
- 调课调班去重：对 `trade_type = '调课调班'` 按 `name + user_id1` 汇总 `price`，总额不为 0 后取第一条。
- 正常订单聚合：对 `trade_type = '正常订单'` 按订单和顾问明细维度汇总 `price`。
- 评优人群范围：`pg.zaizhi = '1' and pg.is_emp = '是'`。
- 周期排名：ROI 使用降序 `rank()`，退费使用自定义 `row_number()` 排序。

## 11. 待确认事项

- `finance_dw.app_finance_performance_extend_details_hf` 字段类型来自 SQL 推断，需用 DDL 校验。
- `temp_table.dingxi01_pingyou_jg` 来源和唯一键需确认，尤其是 `employee_email_name + qici` 是否唯一。
- `renchan` 的业务含义和是否可跨渠道、跨期直接求和需确认。
- `moth` 是原 SQL 字段名，实际含义为月份。
- 原始文件含多段独立 SQL，执行时需要单独运行目标段落，不能作为一个单一 SQL 一次性提交。
- 期次特殊日期映射硬编码到 2026 年部分日期，后续新增期次需确认是否继续维护。
- 校验脚本提示 `course_first_level_department_name`、`course_second_level_department_name`、`course_top_level_department_name` 被选出但未单独过滤；原始 SQL 只限定了员工部门，复用时需确认是否也要限定课程部门。
- 所有指标口径来自历史 SQL，尚未与正式指标文档核对。
