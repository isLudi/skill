# 青橙退费原因分析模板

## 1. 定位

- 业务域：`qingcheng`
- 模板编号：Q1
- 用途：按结果期次、渠道、架构、年级、顾问、用户和退费原因分摊退费金额。
- 证据 SQL：`resources/raw_sql/qingcheng_refund_reason_analysis_20260718.sql`
- 历史验证工作簿：`runtime/qingcheng_refund_reason_analysis/qingcheng_refund_reason_analysis_20260501_20260703_20260710.xlsx`

## 2. QuerySpec 骨架

| 槽位 | 取值/要求 |
|---|---|
| `domain` | `qingcheng` |
| `intent` | 青橙退费原因结构和用户退费原因明细 |
| `time_range` | 结果期次日期范围；历史样例为 20260501 至 20260703 |
| `calculation_grain` | 先订单—原因，再用户—原因 |
| `output_grain` | `qici + channel + org + grade + consultant + uid + refund_reason` |
| `business_scope` | 青橙项目部；订单范围、线索范围、架构期次都要明确 |
| `candidate_tables` | 青橙线索全链路、service 订单归因、财务退款原因/退款明细/订单变更、青橙期次架构 |
| `join_path` | 多表人工 SQL；退款原因金额需按订单退款金额重新分摊 |

## 3. 计算链路

1. `lead_map`：青橙线索、渠道和顾问归因。
2. `order_change`：展开订单变更链，识别内部调课调班。
3. `gmv` / `gmv_order`：按结果期次形成订单退款金额，只保留正退款。
4. `refund_reason_txn`：从 `finance_dw.dwd_finance_order_refund_df` 读取订单、退费原因和原因源金额。
5. `order_reason_alloc`：把订单退款金额按原因源金额比例分摊；无金额时按原因数均分；无原因时归“未获取到退费原因”。
6. `user_reason_detail`：汇总到用户—原因，并计算涉及订单数。
7. `reason_detail_with_org`：按结果期次关联 `temp_table.dingxi01_qing_team_jg`，补团队架构。

## 4. 退费原因金额分摊

```text
若 reason_source_total > 0：
  订单原因退费金额 = 订单退款金额 × 原因源金额 / 原因源金额合计

若存在原因但原因源金额合计为 0：
  订单原因退费金额 = 订单退款金额 / 原因数

若无原因记录：
  全额归入“未获取到退费原因”
```

该分摊能保证订单层原因金额合计回到订单退款金额，但“原因源金额是否适合作权重”尚未完成业务确认，因此契约保持 `pending_confirmation`。

## 5. 调用时必须替换的参数

1. 结果期次范围，优先使用明确的开始/结束期次；不要直接沿用 `between '20260501' and '20260703'`。
2. 退款原因表分区 `dt`；历史 SQL 使用 `now()-24h` 的天分区，复用前先检查最新可用分区。
3. `refund_type in (1,2)` 是否覆盖目标业务退款类型。
4. 青橙渠道映射版本；历史 SQL 的一级渠道 CASE 对部分记录输出“未知”。
5. 架构口径：当前按 `ur.qici = jg.qici` 使用结果期次架构。
6. 退费人头阈值：历史 `refund_head_key` 使用用户总退费金额 `>500` 元。

## 6. 输出与聚合

| 字段 | 说明 | 聚合规则 |
|---|---|---|
| `refund_amount` | 分摊到用户—原因的退费金额（元） | 可 sum |
| `refund_order_count` | 用户—原因涉及订单数 | 当前粒度可 sum；跨原因会重复同一订单 |
| `user_total_refund_amount` | 同用户同切片原因金额合计 | 每个原因行重复带出，不可直接 sum |
| `refund_head_key` | 用户总退费金额 >500 元时生成的去重键 | 用 `count(distinct refund_head_key)` |

## 7. 已验证样例与数据质量

- 原因明细 1,109 行、842 个用户、138 个原因，分摊退费金额合计 2,088,625.40 元。
- 一级渠道为“未知”的行占 739/1,109；使用前必须评估渠道 CASE 覆盖。
- 期次架构字段有 36 行未匹配，不能把空架构解释为无人承接。

## 8. 门禁

- 当前只作为人工 SQL 模板；退费原因分摊、退款类型、渠道 CASE 和结果期次架构仍需在具体 QuerySpec 中确认。
- 不得用市场顾问退费原因模型补齐青橙语义。
