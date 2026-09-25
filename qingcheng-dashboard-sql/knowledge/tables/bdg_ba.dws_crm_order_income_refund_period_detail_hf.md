# bdg_ba.dws_crm_order_income_refund_period_detail_hf

## 1. 中文名称

订单业绩收退款流水期归因明细。

## 2. 表用途

订单业绩收退款流水期归因明细，是已完成交易、课程、商品、业绩归属人与组织部门期归因的正价课收退款事实源。粒度为订单号 + 交易时间 + 收款/退款类型。数据地图表 ID 为 36724，属于 dt/hour 全量小时快照。

## 3. 数据粒度

市场大客户运营部物理探查 Query ID 1599261552 验证 dt=20260923、hour=23 有 614 行、446 个订单、383 条收款、84 条退款；该结果不替代青橙范围独立验证。

## 4. 查询引擎

Presto / Presto_lakehouse。

## 5. 分区字段

dt（日快照）与 hour（小时快照）。

## 6. 强制范围限定字段

必须限定 dt、hour；青橙业绩和商品部门范围、权限集合须本域独立验证后填写。

## 7. 字段清单

| 字段 | 含义/用法 |
|---|---|
| order_number / original_order_number | 订单号 / 原始订单号；不得仅按订单号去重 |
| stats_trade_timestamp | MBR 交易时间基准；模板按源时间减 8 小时展示 |
| pay_success_timestamp / original_order_pay_success_timestamp | 支付时间 / 原始订单支付时间 |
| income_amount / refund_amount | 收款 / 退款金额，单位为分 |
| is_stats_conversion_amount | 正价统计金额标记使用 Y |
| performance_employee_email_name / performance_employee_email_prefix | 归属人带数字姓名 / 邮箱前缀 |
| performance_type | 21 续班、22 扩科、23 召回、24 拉新 |
| stat_judge_type | 1 拉新、2 续扩 |
| course_* / clazz_name | 课程品类、年级、科目、班级信息 |

## 8. 常用过滤条件

- finance_dw.app_finance_order_income_refund_info_df 是原始交易日快照，本 DWS 是已做业绩期归因的正价课流水事实。Query ID 1599294111 的宽松键仍有 8 个 app-only 和 8 个 DWS-only，不能硬 Join 或互相替代。
- 与 GMV Communication 的用户+归属人候选键存在多对多放大。正价课和促销课应分别生成金额与事件行后 UNION ALL，禁止直接明细 Join 汇总金额。
- GMV 促销分支归属人使用 source_manager_username / source_manager_name；该映射在市场模板成立，青橙使用前仍须本域复验。
- 必须固定 dt/hour 快照并以 stats_trade_timestamp 限制业务时间。青橙部门范围和权限集合必须独立验证。

## 9. 常用 join key

本表与 GMV 不使用金额明细 Join。App↔DWS 仅可用订单、交易时间、金额与归属字段作诊断候选键，不能假定一一关系。

## 10. 常用 SQL 片段

固定 dt/hour 和本域确认的部门范围后，以 stats_trade_timestamp 限制交易周期，并以 is_stats_conversion_amount=Y 取正价统计流水。

## 11. 注意事项

- App↔DWS Query ID 1599294111：606 个匹配键、8 个 app-only、8 个 DWS-only。
- 市场模板 Query ID 1599327539：DWS 正价课 + GMV 促销课双分支 70 行 × 36 列，五项汇总一致。
- 完整周期任务 ID 1599331293：市场大客户运营部共 2,708 行；只作为物理和方法证据。
