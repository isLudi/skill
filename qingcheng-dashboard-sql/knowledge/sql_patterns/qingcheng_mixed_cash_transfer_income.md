# 青橙混合现金收入与调课调班内部转入处理规则

## 1. 适用范围

本文适用于青橙个人转化和团队完成度数据集中，同时使用以下字段计算收入、退款和折算后产出的场景：

- `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf.income_amount`
- `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf.refund_amount`
- `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf.transfer_in_amount`
- `service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf.transfer_out_amount`
- `finance_dw.dim_finance_order_change_df` 中的调课调班链路

当前直接受此规则约束的生产模型为：

- `2769`：青橙个人转化
- `2680`：团队完成度【期】
- `2677`：团队完成度【月】

退款侧的事件金额级分配、退 4/点睛退 2 和课程部门兜底规则，继续以 `qingcheng_personal_completion_discounted_output_risks.md` 为准。本文只固化“真实现金收入与内部转入可在同一 service 行共存”的收入侧规则。

## 2. 已确认字段语义

`income_amount` 与 `transfer_in_amount/transfer_out_amount` 不是互斥口径：

- `income_amount` 是该 service 行应计入业绩的外部现金收入。
- `transfer_in_amount`、`transfer_out_amount` 是订单变更链路中的内部转移组成。
- 同一行同时出现正 `income_amount` 和正 transfer 金额时，不能据此认定整行都是内部流水。
- `income_amount` 已是外部收入部分，不能再减一次 `transfer_in_amount`，否则会重复扣减。

阿锦奎样例订单 `430591355717157063` 的已核对证据：

```text
财务支付金额                 2,750.00
service.income_amount        2,312.91
service.transfer_in_amount     437.09
合计                         2,750.00
```

其中 `2,312.91` 是调班后新增支付的真实收入，`437.09` 是从父单搬入子单的内部金额。旧逻辑只要 `transfer_in/out > 0` 就将整行 `income_amount` 清零，因而错误少算 `2,312.91`。

## 3. 安全 SQL 模式

收入和收入对应的科目必须优先保留正的 service 现金收入，再处理纯内部变更行：

```sql
case
    -- 混合行可以同时包含外部现金收入和内部转入。income_amount 已是现金部分，
    -- 不得因 transfer_in/out > 0 清空整行，也不得再次减 transfer_in。
    when source_type = 'service' and income_amount_yuan > 0
    then income_amount_yuan
    when is_internal_order_change = 1
    then 0
    else income_amount_yuan
end as income
```

`p_sub` 等收入归属字段使用同样的判断顺序：

```sql
case
    when source_type = 'service' and income_amount_yuan > 0
    then subject
    when is_internal_order_change = 1
    then null
    else subject
end as p_sub
```

该顺序只改变混合 service 收入行；纯内部调课调班行仍由 `is_internal_order_change = 1` 排除。不能把本规则扩展为无条件保留所有 finance 补数行。

## 4. 禁止回退的写法

以下写法会误杀真实收入，禁止用于 `income`、`H_promit_4`、`n_H_promit_4` 或其科目归属：

```sql
case when is_internal_order_change = 1 then 0 else income_amount_yuan end
```

也禁止用以下方式二次扣减：

```sql
greatest(income_amount_yuan - transfer_in_amount_yuan, 0)
```

不能用“订单命中过调课调班链路”或“当前行 transfer 非零”替代金额组成判断。订单级标记用于识别链路，不能证明当前 service 行的全部收入均为内部金额。

## 5. 回归与上线验收

修改上述三个模型时至少完成以下验证：

1. 三份 SQL 的收入及 `p_sub` 判断顺序保持一致。
2. 阿锦奎订单 `430591355717157063` 的 `2,312.91` 必须保留，`437.09` 不得重复计入收入。
3. 阿锦奎聚合预期为：`income_all=21706.91`、`refund_all=2282.44`、`H_income_4=21706.91`、`H_refund_4=2282.44`、`H_promit_4=19424.47`，折算后产出为 `19424.47`。
4. 生产保存后必须回读 SQL SHA-256，并触发新的抽数；旧 SUCCESS 不能作为本次上线证据。
5. 抽数成功后检查个人与团队看板组件 `data_ready`。若 SQL 查询账号不能访问 BI 内部物化表，应使用数据中心保存回执、新 SUCCESS 记录和看板原生数据接口验证，不能把权限拒绝写成数据为空。

2026-10-04 的生产基线：

| 模型 | SQL SHA-256 | 新 SUCCESS run |
|---|---|---|
| `2769` | `af7185af6265e10a597b4441dcf7cac639ab3ea5542a033fed924220fd80f174` | `174407084` |
| `2680` | `fb0d0c260fbfa212a8d38935a2b107318e6eeb3afc3140650b9dc3388427b70f` | `174407087` |
| `2677` | `5e480777aabb933394112344496604030433d38bd58fb57ed917aa855fe64cf1` | `174407089` |
