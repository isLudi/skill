# 顾问销售评优看板

## 1. 来源

原始 SQL：`resources/raw_sql/consultant_sales_ranking_evaluation.sql`

来源文件：`D:\Feishu\评优.txt`

入库时间：2026-05-02

## 2. 查询目标

用于计算市场顾问销售评优数据。底层使用财务业绩流水计算顾问净收、总收、退款、人产 ROI、退费率和排名位置，并分别按期次、月度、季度、半年四种周期聚合。

该 SQL 与 `data_center_market_2253.sql` 都服务于顾问销售数据分析，但聚合口径不同：

- `data_center_market_2253.sql`：基于线索成本转化全链路表，按期次、渠道、规则、年级、顾问等维度聚合转化、GMV、净收等指标。
- `consultant_sales_ranking_evaluation.sql`：基于财务业绩流水和评优临时架构人产表，按顾问及不同时间周期聚合销售评优排名指标。

## 3. 使用表

| 表名 | 别名/CTE | 用途 |
|---|---|---|
| `finance_dw.app_finance_performance_extend_details_hf` | `dd` 来源表 | 财务业绩扩展明细，提供订单流水、交易状态、交易类型、价格、顾问、交易时间和课程信息 |
| `temp_table.zhangjunyan01_pingyou_jg` | `pg` | 评优架构人产临时表，提供顾问期次、架构、渠道、人产、年级、在职和是否参与评优；`is_emp='是'` 表示参与评优，`is_emp='否'` 表示不参与评优 |
| `temp_table.dingxi01_jiagou_zx` | `jiagou_zx_active` | 当前在职架构顾问名单；季度和半年度 clean 脚本用它额外剔除已离职顾问 |

## 4. SQL 结构

原始文件包含 4 段独立 SQL，结构基本一致，仅 `process` 之后的聚合周期不同。

| 段落 | 聚合周期 | 输出周期字段 | 说明 |
|---|---|---|---|
| 期次数据 | 期次 | `qici` | 按每个期次计算顾问 ROI、退费率和排名 |
| 月度数据 | 月 | `moth` | `substring(qici, 1, 6)` 聚合到月份，字段名保留原 SQL 拼写 `moth` |
| 季度数据 | 季度 | `quarter` | 按季度聚合，并包含 2026/2027 部分硬编码季度规则 |
| 半年数据 | 半年 | `half_year` | 1-6 月归为上半年，7-12 月归为下半年 |

## 5. CTE 结构

| CTE | 用途 | 关键字段 |
|---|---|---|
| `dd` | 从财务业绩流水表抽取订单/退款明细，按 `trade_time` 推导期次 | `qici`, `name`, `user_id1`, `trade_type`, `trade_status`, `price` |
| `gmv_t` | 处理 `调课调班`，按 `name + user_id1` 汇总并去重，排除总金额为 0 的记录 | `name_total_price`, `dup_rn` |
| `gmv_z` | 处理 `正常订单`，按订单、用户、顾问、期次等维度汇总 `price` | `name_total_price` |
| `rd` | 合并正常订单和调课调班结果 | `name`, `qici`, `name_total_price` |
| `jiagou_zx_active` | 当前在职架构顾问名单，按顾问姓名去重 | `employee_email_name` |
| `process` | 将评优架构人产表与财务流水按顾问和期次关联，计算净收、总收、退款 | `pt`, `inc`, `ref`, `renchan` |
| `rank` | 计算或保留测试渠道标记，并在期次段直接计算 `roi`、`refd` | `ceshi`, `roi`, `refd` |
| `rank_h` | 月度/季度/半年段聚合到周期-顾问粒度，并计算 `roi`、`refd` | `moth`/`quarter`/`half_year`, `roi`, `refd` |
| `rk_r` | 按周期内 ROI 降序排名 | `rank_in_roi` |
| `ref_rank` | 按退费率和退款金额规则排名 | `rank_in_ref` |
| final select | 输出排名百分比和测试渠道标签 | `rank_position_roi`, `rank_position_ref`, `cs_channel_rank`, `cs_80_rank` |

## 6. join 关系

| 左表/CTE | 右表/CTE | join key | join 类型 | 说明 |
|---|---|---|---|---|
| `temp_table.zhangjunyan01_pingyou_jg pg` | `jiagou_zx_active zx` | `pg.employee_email_name = zx.employee_email_name` | inner join | 季度和半年度 clean 脚本额外限定当前在职顾问，避免历史期次聚合展示已离职顾问 |
| `temp_table.zhangjunyan01_pingyou_jg pg` | `rd` | `pg.employee_email_name = rd.name` + `pg.qici = rd.qici` | left join | 将顾问期次架构人产信息与财务流水结果关联 |

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
qici >= '20260101期'
```

评优临时表范围：

```sql
cast(pg.zaizhi as varchar) = '1'
and pg.is_emp = '是'
```

其中 `pg.zaizhi = '1'` 表示在职过滤；`pg.is_emp = '是'` 表示只纳入参与评优的人员，`is_emp = '否'` 的人员即使在 `pingyou_jg` 中维护，也不会进入严格参评口径结果。

季度和半年度 clean 脚本额外使用当前在职架构名单：

```sql
inner join jiagou_zx_active zx
  on zx.employee_email_name = pg.employee_email_name
```

`jiagou_zx_active` 取 `temp_table.dingxi01_jiagou_zx` 中 `cast(zaizhi as varchar) = '1'` 且部门为 `郑州顾问部`、`西安一部`、`西安二部` 的顾问，并按 `employee_email_name` 去重。

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
- 财务流水期次推导必须与 `temp_table.zhangjunyan01_pingyou_jg.qici` 保持一致；2026 年春节前后按 `D:\Feishu\日期-期次对照.xlsx` 的运营区间校准：`2026-01-20` 至 `2026-01-26` 为 `20260123期`，`2026-01-27` 至 `2026-02-02` 为 `20260130期`，`2026-02-03` 至 `2026-02-08` 为 `20260205期`，`2026-02-09` 至 `2026-02-15` 为 `20260211期`，`2026-02-16` 至 `2026-03-02` 为 `20260227期`。
- 调课调班去重：对 `trade_type = '调课调班'` 按 `name + user_id1` 汇总 `price`，总额不为 0 后取第一条。
- 正常订单聚合：对 `trade_type = '正常订单'` 按订单和顾问明细维度汇总 `price`。
- 评优人群范围：`cast(pg.zaizhi as varchar) = '1' and pg.is_emp = '是'`，其中 `is_emp='是'` 表示参与评优。
- 季度/半年度当前在职过滤：在 `process` 中 `inner join jiagou_zx_active`，剔除已不在当前架构表的离职顾问。
- 周期排名：ROI 使用降序 `rank()`，退费使用自定义 `row_number()` 排序。

## 11. 待确认事项

- `finance_dw.app_finance_performance_extend_details_hf` 字段类型来自 SQL 推断，需用 DDL 校验。
- `temp_table.zhangjunyan01_pingyou_jg` 来源和唯一键需确认，尤其是 `employee_email_name + qici` 是否唯一。
- `renchan` 的业务含义和是否可跨渠道、跨期直接求和需确认。
- `moth` 是原 SQL 字段名，实际含义为月份。
- 原始文件含多段独立 SQL，执行时需要单独运行目标段落，不能作为一个单一 SQL 一次性提交。
- 期次特殊日期映射硬编码到 2026 年部分日期，后续新增期次需确认是否继续维护。
- 校验脚本提示 `course_first_level_department_name`、`course_second_level_department_name`、`course_top_level_department_name` 被选出但未单独过滤；原始 SQL 只限定了员工部门，复用时需确认是否也要限定课程部门。
- 所有指标口径来自历史 SQL，尚未与正式指标文档核对。

## 12. 变体 SQL：自然月份排名（month_clean）

来源：`resources/raw_sql/consultant_sales_ranking_evaluation_month_clean.sql`

最近更新：2026-05-24（覆盖为暑期激励按月排名版本）

### 与主 SQL 的核心差异

| 维度 | 主 SQL (evaluation) | month_clean 变体 |
|---|---|---|
| 聚合周期 | 期次/月/季/半年分层聚合 | **自然月份**聚合（多期次合并为一个自然月） |
| 顾问名单来源 | `temp_table.zhangjunyan01_pingyou_jg` | `temp_table.dingxi01_jiagou_zx`（`zaizhi='1'`，郑州/西安部门优先级去重） |
| 组织链过滤 | 无 | `dw.dim_employee_chain` 取 `高途-H业务线-市场部-市场顾问部` 路径，按 `email_prefix` 内连接任职期间流水 |
| 期次计算 | 硬编码 2026 年特殊日期 + `day_of_week` | 统一 `day_of_week` 公式（无硬编码特殊日期） |
| 自然月 | 无 | `trade_qici = '20260731期' → '202608'` 特殊处理；其余取 `substr(qici, 1, 6)` |
| 渠道 CASE | 使用 `channel` 字段（来自评优临时表） | 历史 CASE（pre-0524 版本，不含后续 0524/0612 渠道细分，信息流-抖音私信 位于旧位置） |
| 转化侧 | 无 | 包含完整的线索→转化→渠道成本→目标完成率链路 |
| 成本维度 | 无 | `temp_table.dingxi01_cost` 按 `channel` 取 `cost`，计算 `receive_target = leads_count * cost` |
| 排名指标 | ROI 排名 + 退费排名 | pmit 排名 + 目标完成率排名（双排名体系） |
| 拓科率 | 无 | `tuoke_rate = pay_user_subs / pay_users` |
| qici_list | 无 | 自然月内所有期次的去重排序拼接 |

### CTE 结构

| CTE | 侧 | 用途 |
|---|---|---|
| org_t | 财务侧 | 组织链过滤，取在职顾问在 `市场顾问部` 路径下的任职时间范围 |
| finance_base | 财务侧 | 从财务业绩表推导 `trade_qici` |
| dd_0 / dd | 财务侧 | 退款处理 + 组织链内连接（仅保留任职期间流水） |
| gmv_t / gmv_z | 财务侧 | 调课调班去重 / 正常订单聚合 |
| rd | 财务侧 | 合并 gmv_z 和 gmv_t |
| jiagou_zx_active | 共享 | 在职顾问名单，按 `zaizhi='1'` + 郑州/西安部门优先去重 |
| rd_0 / base_result | 财务侧 | 按人-期次聚合 income/refund/pmit |
| month_agg → month_ranked | 财务侧 | 自然月聚合 + pmit 排名 |
| eligible_consultant_name | 共享 | 仅在职顾问名单用于过滤转化侧数据 |
| cost_dim | 转化侧 | 渠道成本（`try_cast(cost as double) > 0` 过滤） |
| conversion_base | 转化侧 | 从全链路表推导 `period_name_calc`（`regexp_like` 校验 8 位日期格式） |
| conversion_data | 转化侧 | 渠道映射 + 指标空值处理 |
| conversion_by_channel → conversion_with_target | 转化侧 | 按人-渠道聚合并附加 `receive_target` |
| conversion_agg → conversion_metric_base | 转化侧 | 按人-自然月聚合，派生 `s_lead/podan/target_completion_rate/tuoke_rate` |
| target_completion_rank_raw → target_completion_ranked | 转化侧 | 目标完成率排名 |
| combined | 合并 | 财务侧 pmit + 转化侧指标 + 目标完成率排名的最终合并 |

### 新增/差异指标

| 指标名 | 说明 | 状态 |
|---|---|---|
| natural_month | 自然月（YYYYMM），`20260731期` 特殊映射为 `202608` | 待确认 |
| qici_list | 自然月内去重排序期次列表 | 来自 SQL |
| pmit | `sum(name_total_price)` = 净收（正负合计），与旧 `pt` 同口径 | 来自 SQL |
| period_dept_rank_no | 自然月-部门内按 pmit 降序排名 | 来自 SQL |
| period_dept_need_pmit_to_previous | 距前一名 pmit 差值 | 来自 SQL |
| target_completion_rate | `trade_profit / receive_target` | 待确认 |
| target_completion_period_dept_rank_no | 目标完成率排名 | 来自 SQL |
| target_completion_need_rate_to_previous | 距前一名目标完成率差值 | 来自 SQL |
| receive_target | `leads_count * cost` | 待确认成本表口径 |
| tuoke_rate | `pay_user_subs / pay_users` | 待确认 |
| leads_count | `sum(merge_assign_lead_count for 抖音私域 else lead_count)` | 来自 SQL |
| s_lead / podan | 有效线索 >=5 门槛 / 破单标记 | 来自 SQL |

### 待确认事项

- channel_map CASE 版本未同步最新 `market_channel_case_when_0612.sql`；如与转化看板在同一前端展示，会出现渠道口径不一致。
- `period_mapping_first_level_department_name is null` 和 `period_mapping_second_level_department_name is null` 的放宽条件。
- `conversion_base` 使用 `select fl.*`（全字段扫描宽表 283 列），违反知识库规则。
- `temp_table.dingxi01_cost` 中 `cost` 字段为字符串，需 `try_cast` 且 `> 0` 过滤；`trim(channel)` 后 `max(cost)` 取最大唯一值，如存在同一渠道多行不同成本值会丢失信息。
- `jiagou_zx_active` 的部门优先级去重逻辑（郑州>西安一部>西安二部）为非标准顺序，如果顾问同时在多部门兼职取第一条。
- `finance_dw.dim_finance_employee_df` 未在财务侧使用，财务侧顾问范围完全由 `dw.dim_employee_chain` + `jiagou_zx_active` 控制。
- `day_of_week` 期次公式的 `trade_dt - interval '1' day` 后 weekday 1=周日对应的 `+3 day` 逻辑需与业务周五对齐的期次口径确认。
- `20260731期 → 202608` 自然月映射是否为特例硬编码需确认。
- 最终 `combined` 仅通过 `eligible_consultant_name` 内连接限定在职架构顾问，未对财务侧 `name` 做在职过滤（已在 `dd` 的 `org_t` join 中间接过滤）。
