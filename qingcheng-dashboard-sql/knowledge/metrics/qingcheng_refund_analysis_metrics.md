# 青橙退费分析指标

## 1. 适用范围

适用于：

- `resources/raw_sql/qingcheng_refund_rate_analysis_20260710_20260728.sql`
- `resources/raw_sql/qingcheng_refund_structure_share_analysis_20260710_20260728.sql`
- `resources/raw_sql/qingcheng_refund_reason_analysis_20260710_20260728.sql`

基础订单、线索、渠道和团队归属来自 `resources/raw_sql/data_center_qingcheng_2460.sql`。本文件描述业务可理解的分子和分母；退款类型范围、原因金额分摊和 500 元退费正价课人头阈值已由业务确认。

## 2. 退费率透视表指标

| 展示指标 | 分子 | 分母 | 业务解释 |
|---|---|---|---|
| 线索数 | 有效线索记录数 | 无 | 当前期次、渠道、年级和顾问归属下的有效线索量 |
| GMV退费率 | 退费金额 `refund_amount` | 有支付的 GMV `income_gmv` | 已支付 GMV 中有多少金额最终退回 |
| 退费金额 | 订单退费金额 `refund_amount` | 无 | 与青橙转化看板订单归属一致的退费金额，单位元 |
| 退费人头 | 退费金额大于 500 元的去重用户数 `refund_headcount` | 无 | 按当前归属切片识别达到正价课退费阈值的用户数 |
| 人头退费率 | 退费金额大于 500 元的去重用户数 `refund_headcount` | 有支付 GMV 的去重用户数 `pay_headcount` | 已支付用户中，达到 500 元退费阈值的用户占比 |
| 1科GMV退费率 | 恰好支付 1 门非“定制方案”科目的用户对应的退费 GMV `refund_1_subject_gmv` | 同一批用户对应的支付 GMV `income_1_subject_gmv` | 只购买 1 门科目的用户，其支付 GMV 的退费比例 |
| 2科GMV退费率 | 恰好支付 2 门非“定制方案”科目的用户对应的退费 GMV `refund_2_subject_gmv` | 同一批用户对应的支付 GMV `income_2_subject_gmv` | 只购买 2 门科目的用户，其支付 GMV 的退费比例 |
| 3科GMV退费率 | 恰好支付 3 门非“定制方案”科目的用户对应的退费 GMV `refund_3_subject_gmv` | 同一批用户对应的支付 GMV `income_3_subject_gmv` | 只购买 3 门科目的用户，其支付 GMV 的退费比例 |
| 4科GMV退费率 | 恰好支付 4 门非“定制方案”科目的用户对应的退费 GMV `refund_4_subject_gmv` | 同一批用户对应的支付 GMV `income_4_subject_gmv` | 只购买 4 门科目的用户，其支付 GMV 的退费比例 |
| 5科GMV退费率 | 恰好支付 5 门非“定制方案”科目的用户对应的退费 GMV `refund_5_subject_gmv` | 同一批用户对应的支付 GMV `income_5_subject_gmv` | 只购买 5 门科目的用户，其支付 GMV 的退费比例 |
| 6科GMV退费率 | 恰好支付 6 门非“定制方案”科目的用户对应的退费 GMV `refund_6_subject_gmv` | 同一批用户对应的支付 GMV `income_6_subject_gmv` | 只购买 6 门科目的用户，其支付 GMV 的退费比例 |

计算时先汇总分子和分母，再做除法：

```sql
sum(refund_amount) / nullif(sum(income_gmv), 0)
sum(refund_headcount) / nullif(sum(pay_headcount), 0)
sum(refund_1_subject_gmv) / nullif(sum(income_1_subject_gmv), 0)
```

`pay_headcount` 是 `income > 0` 的 uid 去重数；`refund_headcount` 是用户层 `refund > 500` 的 uid 去重数。两者都在当前 `qici + 渠道 + 年级 + 顾问` 归属切片内计算，不能用原始订单行数替代。

## 3. 结构占比指标

结构查询输出 `analysis_type` 和 `dim_value`，分别对应年级、产品、科目及其具体值。每个结构透视表的比率口径如下：

| 展示指标 | 分子 | 分母 |
|---|---|---|
| 年级退费金额占比 | 当前年级的退费金额 `refund_amount` | 当前期次、组织、渠道下全部年级的退费金额 `total_refund_amount` |
| 产品退费金额占比 | 当前标准产品的退费金额 `refund_amount` | 当前期次、组织、渠道下全部标准产品的退费金额 `total_refund_amount` |
| 科目退费金额占比 | 当前科目的退费金额 `refund_amount` | 当前期次、组织、渠道下全部科目的退费金额 `total_refund_amount` |

这里的“当前组织、渠道”包含 `qici + dept_2 + xiaozu + dazu + jingli + channel_1 + channel_map_2`。Excel 透视表改变筛选器后，应重新用金额分子除以同一筛选切片的金额总和，不应平均 `refund_amount_ratio`。

### 3.1 产品归类规则

产品标签来自订单的 `course_second_level_department_name`，不使用 `clazz_name` 作为大班/小班的判定字段。按以下顺序归类：

```sql
case
    when course_second_level_department_name like '%精品班学部%' then '大班'
    when course_second_level_department_name like '%菁英班学部%' then '小班'
    when course_second_level_department_name like '%一对一学部%' then '一对一'
    when course_second_level_department_name like '%本地化学部%' then '本地化'
    when course_second_level_department_name like '%清北班学部%' then '清北'
    else '其他'
end as product_value
```

业务话术：课程二级部门属于“精品班学部”的退款，统一计入大班；属于“菁英班学部”的退款，统一计入小班；其余依次按上表归类，无法匹配标准二级部门的退款进入其他。`本地化大班学部` 不包含连续字符串 `本地化学部`，当前仍归入其他，不能仅凭名称中的“大班”自动改归大班。

## 4. 退费原因指标

| 展示指标 | 分子 | 分母 | 业务解释 |
|---|---|---|---|
| 退费原因 | 订单在财务退款原因表中的原因；空值统一为“未获取到退费原因” | 无 | 用户实际填写或系统记录的退款原因 |
| 退费金额 | 按财务原因源金额权重分摊后的订单退费金额 | 无 | 一笔订单多个原因时，分摊后的原因金额之和必须回到订单退费金额 |
| 退费金额占比 | 当前原因的退费金额 | 当前筛选切片全部原因的退费金额 | 该原因占全部退费金额的比例 |
| 退费正价课人头数 | `user_total_refund_amount > 500` 的去重 `refund_head_key` 数 | 无 | 达到 500 元退费阈值、并且属于当前归属切片的去重用户数 |
| 退费正价课人头占比 | 当前原因对应的去重退费正价课人头数 | 当前筛选切片全部原因对应的去重退费正价课人头数 | 达到退费阈值的用户中，该原因涉及的人头比例 |

退费正价课人头占比不能直接把每条原因记录的 `count(distinct uid)` 相加：同一用户可能有多个退款原因。推荐使用 `refund_head_key` 去重，或先按用户分配唯一的主原因后再做展示；当前 SQL 采用第一种方式，并在透视表中以分子、分母分别重算。

## 5. 退费原因金额分摊

当前 SQL 的业务话术是：先找到与青橙转化看板一致的退费订单，再读取财务原因源金额，把该笔订单的退费金额按各原因源金额占比分配。规则等价于：

```sql
case
  when reason_source_total > 0
    then order_refund_amount * reason_source_amount / reason_source_total
  when reason_count > 0
    then order_refund_amount / reason_count
  else order_refund_amount
end
```

其中 `reason_source_amount = abs(finance.refund_amount) / 100.0`，金额单位统一为元。当前确认口径为：财务退款明细使用 `refund_type in (1, 2)`；原因源金额只用于计算各原因在订单退费金额中的分配权重；“退费正价课”按用户同一归属切片的总退费金额严格大于 500 元认定。

## 6. 空值、去重和聚合边界

- 渠道、二级渠道、年级空值统一为 `未知`，组织架构空值统一为 `-`，避免连接键或人头键因 NULL 丢失。
- 人头指标以 uid 去重；退费原因人头使用带归属切片的 `refund_head_key`，避免同一用户跨期次、顾问或渠道串组。
- 金额指标先在订单或用户层聚合，再进入组织、渠道、期次透视；禁止直接对重复 join 后的订单明细求和。
- 所有比例均使用可加总的分子、分母重算；行级百分比只做展示参考，不作为下一层汇总值。
