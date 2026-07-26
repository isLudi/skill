# 青橙保护期课程转移转化补数

## 1. 适用场景

适用于续班后发生课程转移，订单从 A 用户调整到 B 用户，且交易发生时 B 用户处于青橙顾问私海保护期的场景。

该场景不能只依赖 `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf`：

- service 主明细可能仍使用 A 用户或原线索归因。
- service 行带 `transfer_in_amount` / `transfer_out_amount` 时，原转化逻辑会把内部转单金额置 0。
- B 用户的有效归因必须同时证明“课程转移子订单”“财务正向支付”“交易时处于青橙私海保护期”“顾问一致”。

当前仅用于 `转化数据` / model `2460`，从 `2026-07-20`（`20260722期`）起生效，不回刷更早期次。

## 2. 四层证据链

### 2.1 课程转移订单

从 `finance_dw.dim_finance_order_change_df` 取最新子订单：

```sql
order_change_type = 1
and latest_child_order_status in (2, 6, 7)
and biz_type in (2, 7)
and latest_child_order_number is not null
```

以 `latest_child_order_number` 作为补数订单号，按订单聚合转入、转出金额。不能把普通 `order_change_type = 0` 调课调班纳入该补数分支。

### 2.2 财务正向支付

将最新子订单关联 `finance_dw.app_finance_performance_extend_details_hf`，必须同时满足：

```sql
employee_first_level_department_name = 'H业务线'
and employee_second_level_department_name = '青橙项目部'
and cast(trade_time as date) >= date '2026-07-20'
and trade_type = '调课调班'
and trade_status like '%支付%'
and price > 0
```

补数金额直接使用财务表的 `price`，该表金额单位为元，不再除以 100。按 `order_number + target_user_number + employee_email_name + subject` 聚合，避免同订单财务明细重复。

### 2.3 B 用户交易时保护期

将财务行关联 `service_dw.dwd_crm_assign_private_detail_hf`：

```sql
cast(private.user_number as varchar) = cast(finance.target_user_number as varchar)
and private.employee_email_name = finance.employee_email_name
```

保护期必须按交易时点判断：

```sql
model_type = 0
and is_del = 0
and assign_time <= trade_time
and (close_time is null
     or close_time = timestamp '1970-01-01 08:00:00'
     or close_time > trade_time)
and coalesce(
    try_cast(fall_sea_time as timestamp),
    timestamp '9999-12-31 23:59:59'
) > trade_time
```

同一订单、科目存在多条有效私海记录时，按 `assign_time desc, private_sea_update_time desc, private_sea_id desc` 取一条。

### 2.4 线索与渠道归因

保护期记录提供 B 用户的正常 `lead_id`，再按：

```sql
protected.lead_id = lead_map.lead_id
and protected.employee_email_name = lead_map.employee_email_name
```

复用 model 2460 当前 `lead_map` 的 `channel_map_1`、`rule_name0`、`rule_name`、`grade_0` 和主管。不得另写一套渠道 CASE；这样可同时保留抖音正价退费等已上线的渠道归因修复。

## 3. 与原服务链路隔离

原 `dd -> service_gmv` 逻辑保持不变，继续把 service 主明细中的内部调课调班金额置 0。

补数行单独生成 `course_transfer_gmv`，再执行：

```sql
select * from service_gmv
union all
select * from course_transfer_gmv
```

随后复用原 `udd -> ud -> mm` 聚合。不要把补数行提前 union 到 `dd`：

- 会让补数订单进入原 `prc`、退款课消和订单变更联表。
- 会改变原服务分支执行计划并增加历史指标漂移风险。
- 无法证明删除新增分支后仍精确还原上线前 SQL。

生产前应机械移除新增课程转移 CTE、`course_transfer_gmv`，并把 `service_gmv` 还原为 `gmv`；还原结果的 SHA-256 必须等于当前线上基线。

## 4. 回归门禁

1. 目标订单明细：指定期次、B 用户、顾问、渠道和金额必须逐笔核对。
2. 目标用户聚合：验证 `pay_user`、`p_pay_user`、`pay_sub`、`p_pay_sub`、`income`、`refund`、`promit`、`p_income`、`podan`、`sc`。
3. 全渠道分桶：按 `qici + channel_1 + channel_map_2` 比较基线与候选；除目标桶外，线索、成单、科次、营收、退费、净营收、退款人数和破蛋人数必须一致。
4. 历史边界：`20260722期` 之前不得出现补数行。
5. 并发修改：生产计划前重新读取线上 SQL；候选去除本次新增段后必须等于线上最新哈希。
6. 数据中心：必须完成 Preview、保存后 SQL hash 回读、`executeOnce` 和新的 `SUCCESS` 同步记录。

`sc` 当前依赖 `prc` 的 `row_number() over (partition by lead_id order by qici_lead desc)`；同一 `lead_id` 存在并列 `qici_lead` 时，完全相同的基线 SQL重复执行也可能漂移。应单独验证新增分支的 `sc` 增量，不把跨次执行的全量 `sc` 差异误判为本次补数影响。

## 5. 2026-07-26 验证证据

- 目标课程转移明细 query id `1500597979`：2 个最新子订单，合计 4000 元，只命中 `20260722期 / 私域 / 私域表单`。
- 目标分支聚合 query id `1500617507`：支付用户 1、当期支付用户 1、科目 1、当期科目 1、营收 4000、退款 0、净营收 4000、破蛋 1、成单周期 2 天。
- 完整候选 query id `1500653571`：`Success`。
- 基线/候选渠道分桶 query id `1500621493`、`1500658395`：除目标桶外，核心指标无差异。
- Data Center Preview task `1500672337`；新抽数记录 `161027733` 为 `SUCCESS`。
