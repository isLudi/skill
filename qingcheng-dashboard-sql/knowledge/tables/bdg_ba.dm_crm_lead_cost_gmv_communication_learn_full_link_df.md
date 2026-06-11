# bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df

## 1. 中文名称

线索成本 GMV 沟通学习全链路表

## 2. 表用途

在青橙过程数据 SQL 中作为有效线索主表，提供线索、用户、分配、规则、渠道、年级、顾问、部门和期次字段。

## 3. 数据粒度

待人工确认。当前 SQL 按 `lead_id` 使用，并通过 `select distinct f.*` 进入基础层。

## 4. 查询引擎

Presto

## 5. 分区字段

| 字段名 | 类型 | 说明 |
|---|---|---|
| `dt` | 待人工确认 | 日期分区 |
| `hour` | 待人工确认 | 小时分区 |

## 6. 强制范围限定字段

| 字段名 | 默认取值/占位符 | 说明 |
|---|---|---|
| `section_assign_employee_first_level_department_name` | `'H业务线'` | 截面分配员工一级部门 |
| `section_assign_employee_second_level_department_name` | `'青橙项目部'` | 截面分配员工二级部门 |
| `period_mapping_first_level_department_name` | `'H业务线'` | 期次映射一级部门 |
| `period_mapping_second_level_department_name` | `('精品班学部','青橙项目部')` | 期次映射二级部门 |
| `virtual_second_department_name` | `'青橙项目部'` | 虚拟二级部门，最终 prc 层过滤 |

## 7. 字段清单

### 7.1 核心标识和期次字段

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `lead_id` | 待人工确认 | 线索 ID | join 首次接通、到课、F 类外呼 |
| `user_id` | 待人工确认 | 用户编号 | join APP 登录、外呼、上课、F 类外呼 |
| `employee_email_prefix` | 待人工确认 | 员工邮箱前缀 | join 外呼、到课 |
| `employee_email_name` | 待人工确认 | 员工姓名/邮箱名 | join 架构、F 类外呼 |
| `group_period_year` | 待人工确认 | 期次年份 | 计算 `qici` / `period_name` |
| `group_period_term` | 待人工确认 | 期次期号 | 计算 `qici` / `period_name` |

### 7.2 时间字段

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `section_assign_time` | 待人工确认 | 截面分配时间 | 计算分配日期和首次触达时间差 |
| `first_call_time` | 待人工确认 | 首次触达时间 | 计算 `first_call_time_diff_hour` 和 `first_call_in_24h` |
| `lead_create_time` | 待人工确认 | 线索创建时间 | 市场渠道 CASE WHEN 中使用（如 KOC 菁英初三 2026-04-15 条件） |

### 7.3 渠道和投放字段

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `rule_name` | 待人工确认 | 分配规则名称 | 青橙渠道和年级映射、市场渠道 CASE WHEN |
| `channel_name_1` | 待人工确认 | 一级渠道名称 | 市场渠道 CASE WHEN |
| `channel_name_2` | 待人工确认 | 二级渠道名称 | 市场渠道 CASE WHEN |
| `channel_name_3` | 待人工确认 | 三级渠道名称 | 市场渠道 CASE WHEN |
| `flow_pool_name` | 待人工确认 | 流量池名称 | 市场渠道 CASE WHEN（核心字段） |
| `put_plan_name` | 待人工确认 | 投放计划名称 | 市场渠道 CASE WHEN（核心字段） |
| `ad_account_name` | 待人工确认 | 广告账户名称 | 市场渠道 CASE WHEN |
| `channel_provider_name` | 待人工确认 | 渠道供应商名称 | 市场渠道 CASE WHEN |
| `source_manager_name` | 待人工确认 | 来源负责人姓名 | 市场渠道 CASE WHEN（核心字段，区分进校/创新/商务/KOC） |
| `source_put_plan_name` | 待人工确认 | 来源投放计划名称 | 市场渠道 CASE WHEN |
| `channel_second_provider_name` | 待人工确认 | 二级渠道供应商名称 | 市场渠道 CASE WHEN |
| `get_customer_way_name` | 待人工确认 | 获客方式名称 | 市场渠道 CASE WHEN |
| `page_id_name` | 待人工确认 | 落地页 ID/名称 | 市场渠道 CASE WHEN（B 站信息流细分） |
| `sku_id_name` | 待人工确认 | SKU ID/名称 | 市场渠道 CASE WHEN（核心字段，区分名师/IP/产品） |
| `flow_original_order_activity_price` | 待人工确认 | 原始订单活动价格 | 市场渠道 CASE WHEN（价格分层，区分信息流19/低价单/5元朱汉祺等） |
| `flow_order_price` | 待人工确认 | 订单价格 | 市场渠道 CASE WHEN |
| `flow_orders_income_amount` | 待人工确认 | 订单收入金额 | 市场渠道 CASE WHEN |

### 7.4 部门和架构字段

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `first_department_name` | 待人工确认 | 一级部门名称 | 市场渠道 CASE WHEN（区分市场部/TT 业务线/KM 等） |
| `second_department_name` | 待人工确认 | 二级部门名称 | 市场渠道 CASE WHEN（区分市场二部/市场四部/战略客户部/微信生态部） |
| `third_department_name` | 待人工确认 | 三级部门名称 | 市场渠道 CASE WHEN（核心字段，区分直播部/图书营销部/私域运营部/投放部/线上商务部/KOC孵化部等） |
| `virtual_second_department_name` | 待人工确认 | 虚拟二级部门 | 青橙过滤、市场渠道 CASE WHEN |
| `virtual_third_department_name` | 待人工确认 | 虚拟三级部门 | 输出为 `depart_1` |
| `virtual_fourth_department_name` | 待人工确认 | 虚拟四级部门 | 输出为 `depart`；市场渠道 CASE WHEN（区分郑州学习顾问部等） |
| `virtual_fifth_department_name` | 待人工确认 | 虚拟五级部门 | 市场渠道 CASE WHEN（区分罗江博团队等） |
| `virtual_leader_email_name` | 待人工确认 | 虚拟经理邮箱名 | 输出为 `jingli` |
| `virtual_direct_leader_email_name` | 待人工确认 | 虚拟直属主管邮箱名 | 输出为 `zhuguan` |

### 7.5 线索量指标字段

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `lead_count` | 待人工确认 | 线索数量 | nvl 后聚合 |
| `valid_lead_count` | 待人工确认 | 有效线索数量 | nvl 后聚合；同时用于 `can_renew_ds_count_a`、`first_call_in_24h` 条件、`is_friend_lead` 条件 |
| `friend_lead_count` | 待人工确认 | 加微线索数量 | 仅当 `valid_lead_count = 1` 时取值，否则为 0 |

### 7.6 转化量指标字段

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `conversion_lead_count` | 待人工确认 | 转化线索数（支付用户数） | nvl 后聚合为 `pay_users` |
| `same_lead_period_conversion_lead_count` | 待人工确认 | 同期线索转化数 | nvl 后聚合为 `pay_users_on_period` |
| `subject_count` | 待人工确认 | 科目数（支付科目数） | nvl 后聚合为 `pay_user_subs` |
| `same_lead_period_subject_count` | 待人工确认 | 同期科目数 | nvl 后聚合为 `pay_user_subs_on_period` |
| `lb_subject_count` | 待人工确认 | 联报科目数 | nvl 后聚合为 `pay_user_subs_joint`；lb = 联报 |
| `same_lead_period_lb_subject_count` | 待人工确认 | 同期联报科目数 | nvl 后聚合为 `pay_user_subs_joint_onp` |
| `order_count` | 待人工确认 | 订单数量 | nvl 处理但未参与最终聚合（可能冗余） |
| `same_lead_period_order_count` | 待人工确认 | 同期订单数量 | nvl 处理但未参与最终聚合（可能冗余） |

### 7.7 收入和退款字段（原始单位：分）

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `income_amount` | 待人工确认 | 收入金额（分） | nvl 后除以 100 聚合为 `trade_income` |
| `in_pay_period_refund_amount` | 待人工确认 | 当期退款金额（分） | nvl 后除以 100，参与 `trade_refund` |
| `non_pay_period_refund_amount` | 待人工确认 | 非当期退款金额（分） | nvl 后除以 100，参与 `trade_refund` 和 `pre_refund` |
| `same_lead_period_income_amount` | 待人工确认 | 同期收入金额（分） | nvl 后除以 100 聚合为 `xb_trade_income` |
| `same_lead_period_refund_amount` | 待人工确认 | 同期退款金额（分） | nvl 后除以 100，参与 `xb_trade_profit` |
| `jp_cross_department_refund_amount` | 待人工确认 | 跨部门退款金额（分） | nvl 处理但未参与最终聚合（可能冗余或遗漏） |

### 7.8 意向/年级字段

| 字段名 | 类型 | 中文含义 | 备注 |
|---|---|---|---|
| `lead_purchase_intention_level1_category_name` | 待人工确认 | 购买意向一级分类 | 市场渠道 CASE WHEN（区分规划系统等） |
| `lead_purchase_intention_level2_category_name` | 待人工确认 | 购买意向二级分类/年级 | 年级兜底；市场渠道 CASE WHEN |
| `lead_purchase_intention_name` | 待人工确认 | 购买意向名称 | 市场渠道 CASE WHEN（区分 AI 定制等） |

## 8. 常用过滤条件

### 8.1 过程数据 raw / 转化 raw 版本

```sql
where f.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
  and f.hour = format_datetime(now() - interval '3' hour, 'HH')
  and f.section_assign_employee_first_level_department_name = 'H业务线'
  and f.section_assign_employee_second_level_department_name = '青橙项目部'
  and f.period_mapping_first_level_department_name = 'H业务线'
  and f.period_mapping_second_level_department_name in ('精品班学部','青橙项目部')
  and f.valid_lead_count = '1'
```

### 8.2 转化宽表-市场渠道版本

```sql
where t1.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
  and t1.hour = format_datetime(now() - interval '2' hour, 'HH')
  and t1.section_assign_employee_first_level_department_name = 'H业务线'
  and t1.section_assign_employee_second_level_department_name in ('青橙项目部')
  and t1.period_mapping_first_level_department_name = 'H业务线'
```

注意差异：
- hour 偏移不同（`-2h` vs `-3h`）。
- 未加 `period_mapping_second_level_department_name` 过滤。
- 未加 `valid_lead_count = '1'` 过滤（宽表市场渠道看板需要全量线索，不限于有效线索）。

## 9. 常用 join key

- `lead_id`
- `user_id`
- `employee_email_prefix`
- `employee_email_name`

## 10. 常用 SQL 片段

```sql
case when f.valid_lead_count = '1' then 1 else 0 end as v_lead
```

## 11. 注意事项

- 本表在不同看板 SQL 中 hour 偏移不一致：过程数据/转化 raw 使用 `now()-3h`，宽表市场渠道使用 `now()-2h`，原因待确认。
- 宽表市场渠道 SQL 使用 `select distinct t1.*`，若宽表本身有重复行，distinct 可能掩盖数据质量问题。
- 宽表市场渠道 SQL 未加 `valid_lead_count = '1'` 过滤，输出全量线索（含无效线索）。
- 宽表市场渠道 SQL 未加 `period_mapping_second_level_department_name` 过滤，是否会引入非青橙期次数据待确认。
- 后续生成新 SQL 时不得使用三参数 `date_add` 计算期次，应改为 `interval` 写法。
- 本表字段清单已大幅扩充（从 19 个增至 50+），新增字段均来自 `qingcheng_conversion_wide_table_market_channel_20260611.sql` 实际使用，完整字段含义待表结构确认。
