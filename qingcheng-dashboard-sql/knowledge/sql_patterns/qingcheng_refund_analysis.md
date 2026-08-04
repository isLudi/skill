# 青橙退费分析查询与校验模式

## 1. 目的

本模式用于从青橙转化看板标准订单集合派生三类退费分析：退费率、年级/产品/科目退费金额占比、退费原因分析。完整查询代码以本期 SQL 为可复现快照，业务语义和筛选范围必须回到 `knowledge/dashboards/qingcheng_refund_analysis_20260710_20260728.md` 与 `knowledge/metrics/qingcheng_refund_analysis_metrics.md`。

## 2. 查询分层

### 2.1 公共底座

1. 复制当前 `data_center_qingcheng_2460.sql` 的 `biz_qici_calendar`、线索归属、订单归属、调课调班识别和团队架构关联。
2. 保持 `service_gmv` 和 `course_transfer_gmv` 的字段顺序一致，再 `union all` 成 `gmv`。
3. 只在派生查询的最外层限定目标期次；涉及订单扫描的 CTE 同时保留青橙项目部、课程部门和分区条件。
4. 组织架构必须按 `employee_email_name + qici` 关联；订单到线索必须按 `lead_id + performance_employee_email_name` 关联。

### 2.2 退费率派生

在标准用户层 `udd` 中保留用户级金额和科目数，再扩展 1-6 科分桶：

```sql
case when ub.pay_sub = 1 then ub.income else 0 end as income_1_subject_gmv,
case when ub.pay_sub = 1 then ub.refund else 0 end as refund_1_subject_gmv
```

对 2 至 6 科重复相同结构。然后在顾问层 `ud` 求和，最终与线索层 `bb_dedup` 按以下完整键对齐：

```text
qici + employee_email_name + channel_map_1 + channel_map_2
     + grade_1 + virtual_direct_leader_email_name
```

这一顺序很重要：如果先算行级比率再汇总，会把小分母行的比率放大；如果在线索和订单之间省略年级或主管，会出现同顾问同渠道跨年级吞数。

### 2.3 结构占比派生

只建立一次 `share_order`：

- 过滤 `gmv.refund_amount > 0`；
- 保留期次、组织、渠道、年级、产品、科目和退费金额；
- 用 `cross join (values ('grade'), ('product'), ('subject'))` 生成三种分析类型。

产品维度必须在 `share_order` 中先完成标准化，再聚合退费金额。产品字段来自订单的 `course_second_level_department_name`，统一使用以下 CASE；不得回退到只检查 `clazz_name` 的旧逻辑：

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

这套规则可解释原产品占比中“其他”异常偏高的原因：`精品班学部` 的标准班型名称不一定包含“大班”，但仍应按课程二级部门归入大班；`本地化大班学部` 等未命中连续字符串的部门仍保留在其他，不能无证据强行拆分。

再按 `analysis_type + dim_value` 汇总，并用窗口求同一切片的分母：

```sql
sum(refund_amount) over (
  partition by qici, dept_2, xiaozu, dazu, jingli,
               channel_1, channel_map_2, analysis_type
) as total_refund_amount
```

Excel 透视表展示时保留 `refund_amount` 和 `total_refund_amount` 两列，筛选后用两列之比计算占比。

### 2.4 退费原因派生

退费原因查询必须先把 `order_number` 传到 `service_gmv` 和 `course_transfer_gmv`，再执行以下步骤：

```text
gmv
 -> gmv_order（按订单、归属切片聚合正向退费）
 -> refund_reason_txn（财务原因源金额）
 -> refund_reason_by_order（订单+原因去重）
 -> refund_reason_order_total（订单原因总额）
 -> order_reason_alloc（按权重/等额/无原因分配）
 -> user_reason_detail（用户+原因汇总）
 -> user_reason_with_total（用户全部原因金额）
 -> reason_detail_with_org（期次架构回填与退费人头键）
```

关键连接和处理代码：

```sql
inner join (select distinct order_number from gmv_order) s
  on r.order_number = s.order_number
where r.dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
  and r.refund_type in (1, 2)
```

```sql
coalesce(channel_map_1, '未知') as channel_1,
coalesce(qudao, '未知') as channel_map_2,
coalesce(grade_0, '未知') as grade_list
```

```sql
case when user_total_refund_amount > 500 and uid is not null
     then concat(qici, '|', channel_1, '|', channel_map_2, '|',
                 grade_list, '|', name, '|', uid)
     else null
end as refund_head_key
```

原因金额的守恒检查必须在 `order_reason_alloc` 和最终明细两个层次执行：

```text
每订单原因金额之和 = 该订单 gmv_order.order_refund_amount
全部原因金额之和 = 退费率数据集 refund_amount 之和
```

## 3. 可复用边界

- 允许更换期次范围，但必须同时更新 `biz_qici_calendar` 和最外层期次过滤，并重新做线索、GMV、退费金额和退费人头核对。
- 不允许把当前查询的财务 `dt = now() - 24h` 直接当作历史快照日期；要按实际数据新鲜度和财务分区规则确认。
- 不允许另建渠道 CASE 或改用市场顾问部渠道映射；渠道规则统一复用 2460 的 `lead_map`。
- 不允许用最新团队架构表覆盖历史期次；架构连接必须带 `qici`。
- 退款类型 `refund_type in (1, 2)`、原因金额按财务原因源金额分摊、以及 500 元人头阈值已经业务确认；后续仍必须保留订单集合限域、订单级金额守恒和用户级去重检查。

## 4. 交付前校验清单

1. SQL 规则检查通过，所有事实表具备分区过滤，且没有将三参数 `date_add` 等平台禁用函数带入派生查询。
2. 退费率数据集按 `qici + 渠道` 汇总后，与转化看板的线索数、支付 GMV、退费金额和人头退费率核对。
3. 结构数据集三种 `analysis_type` 的金额合计相等，且同一筛选切片的维度占比合计约等于 100%。
4. 退费原因数据集的金额合计与退费率数据集一致；`refund_head_key` 去重数与退费率数据集 `refund_headcount` 一致。
5. 检查 NULL 渠道、年级、顾问和 uid；任何 NULL 造成的键丢失都要先解释，再决定是否归为 `未知`。
6. 透视表比率全部由分子和分母计算，不平均行级百分比；Excel 重算后检查公式错误。

## 5. 本期验证证据

20260710-20260728 快照的关键结果：退费金额 `1,347,448.07` 元，退费正价课人头 `337`，支付 GMV `10,953,792.30` 元，支付人头 `2,118`，GMV 退费率 `12.3012%`，人头退费率 `15.9112%`。退费结构与退费原因两条路径的金额均闭合到 `1,347,448.07` 元。

本批次退费原因路径曾出现 17 个用户键因 NULL 渠道而无法生成 `refund_head_key`；将渠道、二级渠道、年级统一归一为 `未知` 后，退费原因去重人头恢复为 337，与转化看板一致。该修复是退费分析的必要数据质量规则，不是市场顾问部口径。
