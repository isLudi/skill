# 青橙个人完成度折算后产出风险排查

## 1. 适用场景

当青橙个人完成度/个人转化看板中的 `折算后产出`、`折算后净收`、`H_promit_4`、`n_H_promit_4`、`Y_promit_4` 与支付订单流水或业务手工核对不一致时，先读本文，再读：

- `knowledge/dashboards/qingcheng_personal_conversion_raw_20260522.md`
- `knowledge/metrics/qingcheng_personal_conversion_metrics.md`
- `knowledge/tables/finance_dw.app_finance_performance_extend_details_hf.md`
- `knowledge/tables/finance_dw.dim_finance_order_change_df.md`

## 2. 业务口径

业务侧给出的折算后净收口径：

- 剔除 4 节课之后的班课退费。
- 点睛班 2 节课后退费不再剔除，2 节课前退费计入剔除。
- 小初业务线按 50% 折算。

个人完成度前端计算字段当前为：

```text
ifnull(sum(${n_H_promit_4}) * 0.5 + (sum(${H_promit_4}) - sum(${Y_promit_4})), 0)
```

因此，排查不能只看前端公式；必须先确认源 SQL 中 `H_promit_4`、`n_H_promit_4`、`Y_promit_4`、`refund_4` 是否已经按订单/课程/部门粒度正确入桶。

## 3. 2026-06-21 已修复风险

### 3.1 课程部门为空导致金额漏入折算桶

`finance_dw.app_finance_performance_extend_details_hf` 中存在 `course_first_level_department_name`、`course_second_level_department_name` 为空的订单流水。历史 SQL 直接用这两个字段判断 H/非 H/一对一，导致空部门流水不进入任何桶：

- 不进入 `H_promit_4`。
- 不进入 `n_H_promit_4`。
- 不进入 `Y_promit_4`。
- 最终 `折算后产出` 被低估。

已采用的兜底规则：

```sql
case
    when course_first_level_department_name is not null then course_first_level_department_name
    when grade_list like '%小学%' or grade_list like '%初%' then '小初业务线'
    else 'H业务线'
end as course_first_level_department_name
```

二级课程部门兜底：

```sql
case
    when course_second_level_department_name is not null then course_second_level_department_name
    when course_first_level_department_name = 'H业务线' then '精品班学部'
    when course_first_level_department_name is null
     and not (grade_list like '%小学%' or grade_list like '%初%') then '精品班学部'
    else course_second_level_department_name
end as course_second_level_department_name
```

生成新 SQL 时不得回退为直接透传空课程部门字段。

### 3.2 调课调班按用户聚合会吃掉部分退款

历史 `gmv_t` 曾按 `name + user_id1` 汇总调课调班，只保留一条记录。该写法会把同一顾问同一用户的多笔调课调班揉在一起，弱化订单、课程、期次、课程部门和科目维度，导致部分调课调班退款无法正确进入 `refund_4`。

已修复为订单/课程粒度：

```sql
group by
    order_number,
    clazz_name,
    user_id1,
    trade_status,
    trade_time,
    trade_type,
    email_prefix,
    name,
    grade_list,
    subject,
    qici,
    school_term_id,
    teacher_name,
    course_first_level_department_name,
    course_second_level_department_name
```

生成新 SQL 时不得把 `gmv_t` 合并回 `name + user_id1` 粒度，也不要为了去重删除 `order_number`、`qici`、`subject`、课程部门字段。

### 3.3 任职窗口时间字段要一致

历史口径混用 `paid_time >= begin_time` 和 `trade_time <= end_time`。个人完成度当前按交易发生时间归属青橙任职窗口，使用：

```sql
ot.name = a.name
and a.trade_time >= ot.begin_time
and (ot.end_time is null or a.trade_time <= ot.end_time)
```

如果业务要求按支付时间归属，需要整体切换为同一个时间字段，不要只改开始或结束边界的一侧。

### 3.4 订单明细侧 service 表不完整保留调课调班链路金额

`service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf` 的原始 `income_amount`、`refund_amount` 在部分调课调班链路上可能直接缺失或为 0。用订单明细侧反查个人/团队完成度时，不能只按 service 原始金额核对，应采用以下补偿口径：

```sql
cast(coalesce(income_amount, 0) + coalesce(transfer_in_amount, 0) as double) / 100.0 as income_amount,
cast(coalesce(refund_amount, 0) + coalesce(transfer_out_amount, 0) as double) / 100.0 as refund_amount
```

如果 service 侧仍缺少完整流水，应以 `finance_dw.app_finance_performance_extend_details_hf` 作为金额事实源补齐缺失事件。个人完成度、团队完成度【期】和团队完成度【月】的看板 SQL 不使用 `where f.trade_timestamp > ${begin_trade_time} and f.trade_timestamp < ${end_trade_time}` 这类模板时间参数；看板 SQL 继续通过 `qici > '20260424期'`、期次映射表和目标/架构表控制展示范围。

## 4. 快速诊断 SQL 片段

### 4.1 查空课程部门金额

```sql
select
    name,
    qici,
    sum(case when price > 0 then price else 0 end) as income_amount,
    sum(case when price < 0 then abs(price) else 0 end) as refund_amount,
    count(*) as row_count
from finance_dw.app_finance_performance_extend_details_hf
where dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
  and hour = format_datetime(now() - interval '2' hour, 'HH')
  and employee_first_level_department_name = 'H业务线'
  and employee_second_level_department_name = '青橙项目部'
  and qici = '20260619期'
  and (course_first_level_department_name is null or course_second_level_department_name is null)
group by 1, 2
order by abs(sum(price)) desc
```

### 4.2 查同一顾问同一用户多笔调课调班

```sql
select
    name,
    user_id1,
    count(distinct order_number) as order_cnt,
    count(distinct qici) as qici_cnt,
    sum(price) as total_price,
    array_join(array_agg(distinct order_number), ',') as order_numbers
from finance_dw.app_finance_performance_extend_details_hf
where dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
  and hour = format_datetime(now() - interval '2' hour, 'HH')
  and employee_first_level_department_name = 'H业务线'
  and employee_second_level_department_name = '青橙项目部'
  and trade_type = '调课调班'
  and qici = '20260619期'
group by 1, 2
having count(distinct order_number) > 1
order by abs(sum(price)) desc
```

### 4.3 对比旧/新折算源指标

```sql
select
    name,
    qici,
    sum(H_promit_4) as H_promit_4,
    sum(n_H_promit_4) as n_H_promit_4,
    sum(Y_promit_4) as Y_promit_4,
    sum(n_H_promit_4) * 0.5 + (sum(H_promit_4) - sum(Y_promit_4)) as discounted_output
from fixed_personal_completion_result
where qici = '20260619期'
  and name in ('宋青蔓', '李孟笛06', '许世杰05')
group by 1, 2
```

## 5. 已验证样例

2026-06-21 修复验证中，以下人员曾出现看板与支付订单流水不一致：

- `宋青蔓`：历史折算后产出 `8206.34`，修复后 `7132.73`；差异来自调课调班退款 `1073.61` 被历史 `gmv_t` 聚合吃掉。
- `李孟笛06`：历史折算后产出 `4600.00`，修复后 `9150.00`；差异来自空课程部门流水 `4600` 被兜底进 H 班课，同时 `50` 退款进入剔除逻辑。
- `许世杰05`：历史折算后产出 `12400.00`，修复后 `17000.00`；差异来自空课程部门流水 `4600` 被兜底进 H 班课。

验证时应同时看订单明细和聚合结果，不要只看前端自定义字段公式。
