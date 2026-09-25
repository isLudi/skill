# bdg_ba.dws_crm_order_income_refund_period_detail_hf

## 1. 中文名称

订单业绩收退款流水期归因明细。

## 2. 表用途

订单业绩收退款流水期归因明细，是市场顾问部现金流水/MBR 口径的正价课收退款事实源。粒度为订单号 + 交易时间 + 收款/退款类型，同一订单可有多条独立流水。数据地图表 ID 为 36724，属于 dt/hour 全量小时快照。

## 3. 数据粒度

2026-09-24 使用 dt=20260923、hour=23 探查；Query ID 1599261552 验证该小时 614 行、446 个订单、383 条收款、84 条退款。

## 4. 查询引擎

Presto / Presto_lakehouse。

## 5. 分区字段

dt（日快照）与 hour（小时快照）。

## 6. 强制范围限定字段

必须限定 dt、hour、业绩归属一二三级部门、商品一级部门和获准的商品二级部门集合。

## 7. 字段清单

| 字段 | 含义/用法 |
|---|---|
| order_number / original_order_number | 订单号 / 原始订单号；不得仅按订单号去重 |
| stats_trade_timestamp | MBR 交易时间基准；当前模板按源时间减 8 小时展示 |
| pay_success_timestamp / original_order_pay_success_timestamp | 支付时间 / 原始订单支付时间 |
| income_amount / refund_amount | 收款 / 退款金额，单位为分 |
| is_stats_conversion_amount | 正价统计金额标记使用 Y |
| performance_employee_email_name | 业绩归属人带数字姓名；MBR 归属人姓名使用此字段 |
| performance_employee_email_prefix | 业绩归属人邮箱前缀 |
| performance_type | 21 续班、22 扩科、23 召回、24 拉新 |
| stat_judge_type | 1 拉新、2 续扩 |
| course_* / clazz_name | 课程品类、年级、科目、班级信息 |
| goods_* / performance_* department fields | 商品与业绩归属组织范围 |

## 8. 常用过滤条件

- 业绩归属范围为 H业务线 / 市场部 / 大客户运营部；商品一级部门为 H业务线。平台允许的商品二级部门集合为创新项目部、市场部、本地化部、精品班部、菁英班部、精品班学部、菁英班学部、青橙项目部、Theta智学项目部。
- 必须固定 dt/hour 快照，并以 stats_trade_timestamp 限制业务时间；不可把快照日期当交易日期。
- finance_dw.app_finance_order_income_refund_info_df 是原始订单收退款交易日快照，适合探查原始交易字段；不是本次历史 MBR 正价课主源。
- 本 DWS 是已做业绩期归因的正价课主源。促销课/引流课另取 bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df 的 flow_order_* / flow_orders_* 字段；归属人使用 source_manager_username / source_manager_name。
- 正价课和促销课分别在事实粒度生成流水，最后 UNION ALL；禁止把 DWS 或 App 表直接 Join 到 GMV 明细后汇总金额。

## 9. 常用 join key

本表与 GMV 不使用金额明细 Join。App↔DWS 仅可用订单、交易时间、金额与归属字段作诊断候选键，不能假定一一关系。

## 10. 常用 SQL 片段

固定 dt/hour 和部门范围后，以 stats_trade_timestamp 限制交易周期，并以 is_stats_conversion_amount=Y 取正价统计流水。

## 11. 注意事项

- 8 月模板 Query ID 1599327539：70 行 × 36 列，五项金额/人次汇总一致；仅一笔 GMV 退款时间因历史快照漂移相差 54 秒。
- GMV 单笔 Query ID 1599324316：当前源时间唯一且可追溯，未人为改写。
- 完整周期临时模板任务 ID 1599331293：2026-04-01 至 2026-09-23 共 2,708 行；临时模板已下线并删除。
