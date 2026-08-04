# 青橙退费分析（20260710期-20260728期）

## 1. 来源与适用范围

本条目是 20260710 期至 20260728 期青橙项目部退费分析的人工核对说明。可执行查询代码保存在以下 raw SQL 文件中：

| 数据集 | SQL 文件 | SHA-256 | 输出用途 |
|---|---|---|---|
| 退费率及科目数 | `resources/raw_sql/qingcheng_refund_rate_analysis_20260710_20260728.sql` | `3315B5FFBF0157DA0C04C6380C55CC12723F39B54A2C60157C73A99AE14C6D6D` | 退费率透视表、线索数、退费人头和 1-6 科 GMV 退费率 |
| 年级/产品/科目退费金额占比 | `resources/raw_sql/qingcheng_refund_structure_share_analysis_20260710_20260728.sql` | `ACFA35AE0138441B7892E641FFA0DE456CDDA906697E8CE20F7AFA30A21062E1` | 三类结构占比透视表；产品归属按课程二级部门重算 |
| 退费原因 | `resources/raw_sql/qingcheng_refund_reason_analysis_20260710_20260728.sql` | `8954D2E0A353234783160FA0829B358B60FF29C84C3050DCE9CAD649D2A6A169` | refund_reason 金额及退费正价课人头透视表 |

三份查询均以当前青橙转化看板数据集 `resources/raw_sql/data_center_qingcheng_2460.sql` 的订单归属、线索归属、渠道 CASE、期次日历和团队架构为基础。当前 canonical SQL 的 SHA-256 为：
`3A451998811769B79DBC110482AB08AFD03D01CD0DADCB86DE414E5FD9647186`。

本条目只适用于青橙项目部；不能把市场顾问部的退款表、渠道映射、订单归属或退款阈值替换进来。业务已确认财务退款类型范围为 `refund_type in (1, 2)`、原因金额按财务原因源金额分摊、以及退费正价课人头阈值为用户总退费金额严格大于 500 元。

## 2. 期次与共同订单归属

本批次使用业务日历，不按自然周周五强行推导期次：

| 期次 | 业务日期 |
|---|---|
| `20260710期` | 2026-07-07 至 2026-07-13 |
| `20260716期` | 2026-07-14 至 2026-07-19 |
| `20260722期` | 2026-07-20 至 2026-07-25 |
| `20260728期` | 2026-07-26 至 2026-07-31 |

订单侧沿用 2460 的 `service_gmv + course_transfer_gmv` 订单集合：

1. 主订单来自 `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf`，按 `trade_timestamp` 先匹配业务期次。
2. 订单通过 `lead_id + performance_employee_email_name` 回连线索宽表，取得渠道、年级、主管等归属字段。
3. service 明细已包含内部调课调班金额时，沿用转化看板规则剔除该行收入、退款和净营收。
4. 20260722 期起，只有交易时处于同一青橙顾问有效私海保护期的 B 用户课程转移正向支付，才进入隔离的 `course_transfer_gmv` 补数分支。
5. 团队架构使用 `temp_table.dingxi01_qing_team_jg` 的 `employee_email_name + qici` 关联，避免用最新架构覆盖历史期次。

## 3. 数据集一：退费率

最终明细粒度为 `qici + channel_1 + channel_map_2 + grade_1 + employee_email_name`，并保留 `dept_2 + xiaozu + dazu + jingli` 供透视筛选。SQL 同时输出分子和分母字段，Excel 或 BI 透视表必须先求和后计算比率：

```text
GMV退费率 = SUM(refund_amount) / SUM(income_gmv)
人头退费率 = SUM(refund_headcount) / SUM(pay_headcount)
N科GMV退费率 = SUM(refund_N_subject_gmv) / SUM(income_N_subject_gmv)
```

输出的 `lead_count` 是有效线索数；`income_gmv`、`refund_amount` 是订单归属一致的元金额；`refund_headcount` 和 `pay_headcount` 是用户去重数。1-6 科字段按用户实际支付的非“定制方案”科目数分桶，分桶后汇总用户全部 GMV，而不是只汇总某一门科目的金额。

## 4. 数据集二：退费结构占比

查询先保留正向退费订单，再一次性展开 `analysis_type = grade / product / subject` 三种分析类型。每条输出记录的 `dim_value` 分别表示：

- `grade`：订单年级，空值归为 `未知`。
- `product`：按 `course_second_level_department_name` 统一识别 `大班`、`小班`、`一对一`、`本地化`、`清北`，其余归为 `其他`。
- `subject`：识别数学、英语、物理、化学、语文、生物、地理、政治、历史、定制方案，其余归为 `其他`。

结构占比的分母是同一 `qici + dept_2 + xiaozu + dazu + jingli + channel_1 + channel_map_2 + analysis_type` 切片下全部维度值的退费金额：

```text
退费金额占比 = SUM(当前年级/产品/科目退费金额)
             / SUM(同一切片下全部年级/产品/科目退费金额)
```

不要对明细行的 `refund_amount_ratio` 做平均；透视表应使用 `refund_amount` 和 `total_refund_amount` 重新计算。

### 产品分类口径（已迁移）

产品归属已与已确认的市场顾问部产品归类逻辑对齐，但仍使用青橙订单集合和青橙订单归属。产品 CASE 只读取 `course_second_level_department_name`，不再根据 `clazz_name` 中是否出现“大班/小班”判断：

| 课程二级部门条件 | 标准产品 |
|---|---|
| `like '%精品班学部%'` | `大班` |
| `like '%菁英班学部%'` | `小班` |
| `like '%一对一学部%'` | `一对一` |
| `like '%本地化学部%'` | `本地化` |
| `like '%清北班学部%'` | `清北` |
| 以上均不满足 | `其他` |

因此，原导出中“其他”占 81.61% 是旧版 CASE 的结果，不能继续作为新口径的产品结论。`精品班学部` 的非标准班型也会归入 `大班`；`本地化大班学部`、`精品班部` 和单独的 `清北` 不满足当前连续字符串条件，仍会归入 `其他`，除非业务后续明确增加映射规则。

## 5. 数据集三：退费原因

最终明细粒度为 `qici + name + channel_1 + channel_map_2 + dept_2 + dazu + xiaozu + jingli + grade_list + uid + refund_reason`。处理顺序如下：

1. 从与转化看板相同的 `gmv` 订单集合中取 `refund_amount > 0` 的订单，并按 `qici + 渠道 + 年级 + 顾问 + uid + order_number` 汇总。
2. 为保证订单能与财务原因明细连接，退费原因 SQL 在 `service_gmv` 和 `course_transfer_gmv` 中显式保留 `order_number`。
3. 关联 `finance_dw.dwd_finance_order_refund_df`，当前快照读取 `dt = now() - 24h`，且 `refund_type in (1, 2)`。
4. `refund_reason` 为空字符串或空值时统一为 `未获取到退费原因`。
5. 同一订单有多个原因时，以财务原因源金额作为权重，把订单退款金额按原因拆分；原因源金额合计为 0 时等额拆分；没有任何原因记录时，整笔金额落到 `未获取到退费原因`。
6. 在 `qici + 渠道 + 年级 + 顾问 + uid` 粒度汇总用户原因金额，并按用户全因原因金额计算 `user_total_refund_amount`。
7. 退费正价课人头使用 `user_total_refund_amount > 500` 的去重用户键 `refund_head_key`。该键包含期次、渠道、年级、顾问和 uid，目的是与当前转化看板的归属切片保持一致。

退费原因透视表中的比率必须按当前筛选切片重新计算：

```text
退费金额占比 = 当前 refund_reason 的退费金额 / 当前筛选切片全部退费金额
退费正价课人头占比 = 当前 refund_reason 的去重退费正价课人头 / 当前筛选切片全部退费正价课人头
```

## 6. 当前查询中的关键修复

- 退费原因 SQL 的 `gmv_order` 对 `channel_map_1`、`qudao`、`grade_0` 使用 `coalesce(..., '未知')`，并在 `group by` 使用同样的表达式。这样 NULL 渠道不会使 `refund_head_key` 拼接结果变成 NULL。
- 原因分摊先在 `order_number + refund_reason` 粒度聚合，再回连订单退款金额，避免财务原因一对多直接 join 放大退款金额。
- 三类结构占比使用同一个 `share_order` 订单参考集，再用 `cross join values` 展开分析类型，避免三次独立扫描导致的分母不一致。
- 所有比率在透视表层保留可加总的金额/人数分子和分母，不使用平均行比率。

## 7. 本期校验快照

以下是本次查询下载结果的固定快照，只用于核对本批次，不代表未来执行结果：

| 校验项 | 结果 |
|---|---:|
| 退费率明细行数 | 1,587 |
| 结构占比明细行数 | 1,108 |
| 退费原因明细行数 | 780 |
| 有效线索数 | 25,702 |
| 支付 GMV | 10,953,792.30 元 |
| 退费金额 | 1,347,448.07 元 |
| 退费正价课人头 | 337 |
| 支付人头 | 2,118 |
| GMV 退费率 | 12.3012% |
| 人头退费率 | 15.9112% |
| 三类结构退费金额合计 | 1,347,448.07 元 |
| 退费原因明细退费金额合计 | 1,347,448.07 元 |

金额守恒、退费人头与转化看板一致，是本批次输出可交付的必要条件。若后续财务原因分区、渠道规则或业务期次发生变化，应重新生成 SQL 哈希和校验快照，不直接覆盖本条目中的历史证据。

## 8. 相关文档

- 指标分子、分母和业务话术：`knowledge/metrics/qingcheng_refund_analysis_metrics.md`
- 可复用查询思路与校验清单：`knowledge/sql_patterns/qingcheng_refund_analysis.md`
- 当前转化看板基准：`knowledge/dashboards/qingcheng_conversion_raw_20260626.md`
- 历史退费原因模板及未决语义：`knowledge/dashboards/qingcheng_refund_reason_analysis_template.md`
