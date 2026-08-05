# 青橙完成度 SQL 修复检查清单

## 1. 适用范围

以下三份 canonical raw SQL 必须同步维护，不能只改其中一份：

- `resources/raw_sql/qingcheng_personal_conversion_raw_20260522.sql`
- `resources/raw_sql/qingcheng_team_completion_period_raw_20260522.sql`
- `resources/raw_sql/qingcheng_team_completion_month_raw_20260522.sql`

适用问题：

- 个人完成度 / 团队完成度看板与订单明细模板不一致
- 某个顾问跨期营收看起来被复制到多个期次
- 调课调班退款被误算进班课退费
- 非 H 折算后产出偏高/偏低
- 顾问活水进青橙后，历史订单退款被串进青橙完成度

## 2. 本轮已确认的稳定口径

### 2.1 任职窗口必须优先看原始支付时间

不要只用 `finance_dw.app_finance_performance_extend_details_hf.order_paid_time` 或 `trade_time`。

当前稳定写法：

1. 先从 `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf` 取：
   - `original_order_pay_success_timestamp`
   - `pay_success_timestamp`
   - `trade_timestamp`
2. 生成：

```sql
cast(coalesce(original_order_pay_success_timestamp, pay_success_timestamp, trade_timestamp) as timestamp) as original_paid_time
```

3. 再用 `original_paid_time` 去匹配 `dw.dim_employee_chain.begin_time/end_time`。

原因：历史订单在顾问转入青橙后发生退款，不应因为退款发生时间落在青橙任职期内就被计入青橙。

### 2.2 组织链有延迟时，要允许期次架构兜底

仅按 `org_t` 过滤会漏掉当前有效订单，因为组织链 `begin_time` 可能晚于业务实际生效时间。

当前稳定写法：

- 增加 `team_hist`：

```sql
select distinct qici, employee_email_name
from temp_table.dingxi01_qing_team_jg
```

- 用 `original_paid_time` 推导期次后，允许 `team_hist` 命中作为兜底保留条件。

这条规则的目的不是替代组织链，而是补偿组织链起始时间滞后。

### 2.3 调课调班不能再按 `name + user_id1` 粗粒度聚合

`gmv_t` 必须保留至少这些字段：

- `order_number`
- `clazz_name`
- `user_id1`
- `trade_time`
- `trade_type`
- `name`
- `subject`
- `qici`
- `course_first_level_department_name`
- `course_second_level_department_name`

否则会吞掉部分退款或把多笔调课调班揉成一条。

### 2.4 正常订单层不能只写 `trade_type = '正常订单'`

当前稳定写法：

```sql
where coalesce(trade_type, '') <> '调课调班'
```

原因：部分应保留的正常绩效订单并不一定严格标成 `正常订单`，但只要不是调课调班流水本身，就不应被提前排掉。

### 2.5 `dim_finance_order_change_df` 必须同时接退款层和主交易层

只接 `re_ke/ord` 退款明细层不够，必须把展开后的订单号映射接到 `rd/t4` 主交易层。

至少覆盖：

- `order_number`
- `parent_order_number`
- `original_order_number`
- `latest_child_order_number`

且：

```sql
biz_type in (2, 7)
```

不能只保留 `biz_type = 2`。

### 2.6 只剔除调课调班流水本身，不要把整条链路正常订单一起剔掉

这是 2026-06-28 最关键修复点。

错误写法的后果：

- 只要命中 `dim_finance_order_change_df`，就把该链路上的正常订单一起当内部流水排除；
- 最终造成顾问营收被少算，例如 `李孟笛06` 被压成 `9150`。

当前稳定写法：

```sql
case
    when rd.trade_type = '调课调班'
     and (
            (
                coalesce(order_change.has_order_change, 0) = 1
                and (
                    coalesce(order_change.transfer_in_amount_yuan, 0) > 0
                    or coalesce(order_change.transfer_out_amount_yuan, 0) > 0
                )
            )
            or coalesce(rd.service_transfer_in_amount_yuan, 0) > 0
            or coalesce(rd.service_transfer_out_amount_yuan, 0) > 0
            or rd.name_total_price < 0
         )
    then 1
    else 0
end as is_internal_order_change
```

含义：

- 只剔除 `trade_type='调课调班'` 的内部变更流水；
- 命中变更链路但本身是正常成交的订单，绩效仍要保留。

### 2.6.1 service transfer 是内部调课调班补充识别

`dim_finance_order_change_df` 是主链路识别来源，但不是唯一来源。2026-07-03 排查发现，service 订单明细已记录 `transfer_in_amount/transfer_out_amount` 的内部调课调班正向调入，可能没有命中 `dim_finance_order_change_df` 展开的订单号映射。

当前稳定规则：

- `order_attr` 从 `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf` 按 `order_number + performance_employee_email_name` 聚合 `transfer_in_amount/transfer_out_amount`，字段单位从分换算为元。
- 聚合后的 service transfer 标记随 `dd -> gmv_t/gmv_z -> rd -> t4` 传递。
- 仅当 `rd.trade_type = '调课调班'` 时，service transfer 非 0 才把 `is_internal_order_change` 置 1。
- service transfer 只作为内部变更识别信号，不替代 service 的 `income_amount/refund_amount` 正常金额主事实；finance 只用于 service 缺失的课程转移补充和规则字段。

### 2.7 非 H 折算口径已经确认，不再是待确认项

业务确认口径：

- `H业务线` 按 100% 计入；
- 所有 `非H业务线` 统一按 50% 折算，不是只针对小初。

注意：

- SQL 输出的 `n_H_promit` / `n_H_promit_4` 当前保存的是非 H 原始净收；
- 0.5 折算由前端公式或下游聚合再乘；

### 2.8 团队架构不能再固定取 `max(qici)`

团队完成度【月/期】和个人完成度都必须按交易期次/结果期次回连架构：

```sql
qtg.employee_email_name = wa.name
and qtg.qici = wa.qici
```

不能再写：

```sql
where qici = (select max(qici) ...)
```

否则同一顾问在 `20260619期` 和 `20260626期` 会被套用同一套最新架构，出现跨期数据看起来一样的错误。

## 3. 对账时最容易猜错的坑

### 3.1 当前金额字段使用 service 主事实，finance 只做受限补充

`service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf` 在当前完成度 SQL 中承担主金额事实和辅助属性两个用途：

- 用 `original_order_pay_success_timestamp / pay_success_timestamp / trade_timestamp` 辅助确定原始支付归属期；
- 用来补看 lead/order 属性。

当前看板全部收入/退款字段使用：

```text
income_all  = sum(case when source_type = 'service' then income_amount_yuan else 0 end)
refund_all  = sum(case when source_type = 'service' then refund_amount_yuan else 0 end)
```

`income_all/refund_all` 不剔除 service 内部调课调班流水。`income/refund` 仍是内部调课识别后的 legacy/rule 字段，`refund_4/class_refund_4` 仍服务于退 4/点睛退 2 规则。finance 仅在 service 缺失课程转移链路时补充，并且必须先去重、聚合到唯一业务粒度后再 join。

若与渠道模板核对，还必须先统一 `clazz_name` 含“试听”的过滤；当前完成度 SQL 排除试听，保留的模板原始 SQL 未排除试听。

### 3.2 不要只看看板前端自定义公式

前端公式只是聚合层，根因通常出在源 SQL 的：

- 空课程部门兜底
- 调课调班聚合粒度
- 内部变更链路识别
- 任职窗口归属时间
- 架构期次 join

### 3.3 不要只改个人版或只改团队版

这三份 SQL 共用同一类事实逻辑。只修一份，会把后续排查重新打乱。

推荐顺序：

1. 先改个人完成度
2. 同步改团队完成度【期】
3. 再同步改团队完成度【月】
4. 最后统一更新知识库和索引

## 4. 本轮回归样例

建议后续继续用这些样例做冒烟验证：

- `陈贺新`：验证历史订单退款不会串入青橙
- `谷锦茜`：验证 `biz_type=7` 调课调班不会误算
- `张宁晴`、`许多03`：验证调课调班调出退款不会落入班课退费
- `李孟笛06`：验证正常订单不会因命中变更链路被整体剔除

## 5. 发布前检查

1. 三份 canonical raw SQL 是否已同步覆盖。
2. `n_H_promit` / `n_H_promit_4` 文档是否已改成“非 H 原始净收，前端再乘 0.5”。
3. 是否已运行：
   - `scripts/build_reverse_indexes.py`
   - `scripts/check_skill_integrity.py`
