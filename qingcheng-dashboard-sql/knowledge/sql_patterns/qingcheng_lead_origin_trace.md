# 青橙 lead_id 原始来源追溯

## 1. 适用场景

当业务想回答以下问题时，优先使用本模式，而不是直接看 `rule_name`：

- 某批青橙 `lead_id` 最原始的分配线索从哪里来；
- 某批 `lead_id` 是否本质上属于公开课、赠课、流量复用或某个投放计划；
- 为什么同一批线索的 `rule_name`、`period_name`、`lead_group_period_name` 看起来都偏“青橙IP”，但业务仍想看更接近原始来源的字段。

## 2. 核心边界

- 本模式基于 `bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df` 做“当前可追到的最原始来源线索”排查。
- 这不是严格意义上的最早上游 source-of-truth，只是当前青橙知识库内最可操作、可复用的追溯路径。
- 追溯时必须区分两类字段：

### 2.1 更像当前归因/展示结果的字段

- `rule_name`
- `period_name`
- `group_period_name`
- `sku_id_name`

这些字段更适合看当前归因结果、期次展示结果或投放标签，不宜直接当“原始来源”。

### 2.2 更像原始来源线索的候选字段

- `trace_type_name`
- `final_new_source`
- `channel_name_1`
- `channel_name_2`
- `channel_name_3`
- `flow_pool_name`
- `put_plan_name`
- `source_put_plan_name`
- `source_manager_name`
- `get_customer_way_name`

## 3. 已验证样例（2026-06-21）

样例切片：

- 青橙项目部
- `20260619期`
- `rule_name like '%青橙IP%'`
- `period_name like '%公开课%'`

已验证结论：

- 该切片共 2230 条 `lead_id`。
- `rule_name like '%公开课%'` 的结果为 0。
- `period_name` / `lead_period_name` 可以命中 `公开课`。
- 抽样 30 条 `lead_id` 后，`trace_type_name = '引流课报名'`、`channel_name_1 = '内部'`、`channel_name_2 = '流量复用'`、`flow_pool_name = '电商退款用户池'`、`get_customer_way_name = '赠课'`，而 `put_plan_name` / `source_put_plan_name` 能继续区分更细来源。

因此：

- 不要用 `rule_name like '%公开课%'` 识别这批公开课线索。
- 这批线索里，`period_name` 更像“系统期次标签”，`put_plan_name` / `source_put_plan_name` / `flow_pool_name` 更像“来源线索”。

## 4. 推荐排查流程

1. 先拿 20-50 个 `lead_id` 抽样。
2. 看这些样本在 `rule_name`、`period_name`、`lead_group_period_name` 和来源候选字段上的分布。
3. 如果样本规律稳定，再做全量一行一 `lead_id` 导出。
4. 导出后优先看：
   - `trace_type_name`
   - `channel_name_1/2/3`
   - `flow_pool_name`
   - `put_plan_name`
   - `source_put_plan_name`
   - `source_manager_name`
   - `get_customer_way_name`
5. 若业务问“是不是公开课”，优先看 `period_name` / `lead_period_name`，不要先看 `rule_name`。

## 5. SQL 模板

### 5.1 抽样 lead_id 查看字段分布

> 用于先看 20-50 个 `lead_id` 的来源候选字段是否稳定。把 `values` 内替换成真实 `lead_id`。

```sql
with input_leads as (
    select *
    from (
        values
            (12345678901),
            (12345678902),
            (12345678903)
    ) as t(lead_id)
),
base as (
    select
        f.*,
        row_number() over (
            partition by f.lead_id
            order by coalesce(f.section_assign_time, '') desc,
                     coalesce(f.lead_create_time, '') desc
        ) as export_row_num
    from bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df f
    join input_leads l
      on f.lead_id = l.lead_id
    where f.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
      and f.hour = format_datetime(now() - interval '3' hour, 'HH')
      and f.section_assign_employee_first_level_department_name = 'H业务线'
      and f.section_assign_employee_second_level_department_name = '青橙项目部'
      and f.period_mapping_first_level_department_name = 'H业务线'
      and f.period_mapping_second_level_department_name in ('精品班学部', '青橙项目部')
      and f.valid_lead_count = '1'
)
select
    field_name,
    field_value,
    count(*) as lead_cnt
from (
    select 'rule_name' as field_name, coalesce(rule_name, '<null>') as field_value
    from base
    where export_row_num = 1

    union all

    select 'period_name' as field_name, coalesce(period_name, '<null>') as field_value
    from base
    where export_row_num = 1

    union all

    select 'lead_group_period_name' as field_name, coalesce(group_period_name, '<null>') as field_value
    from base
    where export_row_num = 1

    union all

    select 'trace_type_name' as field_name, coalesce(trace_type_name, '<null>') as field_value
    from base
    where export_row_num = 1

    union all

    select 'channel_name_1' as field_name, coalesce(channel_name_1, '<null>') as field_value
    from base
    where export_row_num = 1

    union all

    select 'channel_name_2' as field_name, coalesce(channel_name_2, '<null>') as field_value
    from base
    where export_row_num = 1

    union all

    select 'flow_pool_name' as field_name, coalesce(flow_pool_name, '<null>') as field_value
    from base
    where export_row_num = 1

    union all

    select 'put_plan_name' as field_name, coalesce(put_plan_name, '<null>') as field_value
    from base
    where export_row_num = 1

    union all

    select 'source_put_plan_name' as field_name, coalesce(source_put_plan_name, '<null>') as field_value
    from base
    where export_row_num = 1

    union all

    select 'source_manager_name' as field_name, coalesce(source_manager_name, '<null>') as field_value
    from base
    where export_row_num = 1

    union all

    select 'get_customer_way_name' as field_name, coalesce(get_customer_way_name, '<null>') as field_value
    from base
    where export_row_num = 1
) t
group by 1, 2
order by field_name, lead_cnt desc
limit 500;
```

### 5.2 一行一 lead_id 全量导出来源候选字段

> 用于模板取数下载。可替换 `input_leads` 为实际 lead_id 列表，也可改为业务切片过滤。

```sql
with input_leads as (
    select *
    from (
        values
            (12345678901),
            (12345678902),
            (12345678903)
    ) as t(lead_id)
),
base as (
    select
        f.*,
        row_number() over (
            partition by f.lead_id
            order by coalesce(f.section_assign_time, '') desc,
                     coalesce(f.lead_create_time, '') desc
        ) as export_row_num
    from bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df f
    join input_leads l
      on f.lead_id = l.lead_id
    where f.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
      and f.hour = format_datetime(now() - interval '3' hour, 'HH')
      and f.section_assign_employee_first_level_department_name = 'H业务线'
      and f.section_assign_employee_second_level_department_name = '青橙项目部'
      and f.period_mapping_first_level_department_name = 'H业务线'
      and f.period_mapping_second_level_department_name in ('精品班学部', '青橙项目部')
      and f.valid_lead_count = '1'
)
select
    lead_id,
    user_id,
    rule_name,
    period_name,
    group_period_name as lead_group_period_name,
    group_period_year,
    group_period_term,
    period_number,
    main_period_name,
    trace_type,
    trace_type_name,
    final_new_source,
    channel_name_1,
    channel_name_2,
    channel_name_3,
    channel_provider_name,
    channel_second_provider_name,
    flow_pool_name,
    put_plan_name,
    source_put_plan_name,
    source_manager_name,
    source_manager_username,
    get_customer_way_name,
    page_id_name,
    sku_id_name,
    flow_original_order_activity_number,
    flow_original_order_activity_name,
    lead_purchase_intention_level2_category_name,
    period_first_level_course_project_name,
    period_second_level_course_project_name,
    main_period_first_level_course_project_name,
    section_assign_time,
    lead_create_time
from base
where export_row_num = 1
order by lead_id;
```

### 5.3 诊断为什么 `rule_name like '%公开课%'` 为 0

> 用于快速证明“公开课”可能记录在期次字段，而不是 `rule_name`。

```sql
select
    count(distinct case when rule_name like '%0619期%' then lead_id end) as leads_0619,
    count(distinct case when rule_name like '%青橙IP%' then lead_id end) as leads_ip,
    count(distinct case when rule_name like '%0619期%' and rule_name like '%青橙IP%' then lead_id end) as leads_0619_ip,
    count(distinct case when rule_name like '%0619期%' and rule_name like '%青橙IP%' and rule_name like '%公开课%' then lead_id end) as leads_0619_ip_public_in_rule_name,
    count(distinct case when rule_name like '%0619期%' and rule_name like '%青橙IP%' and period_name like '%公开课%' then lead_id end) as leads_0619_ip_public_in_period_name
from bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df
where dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
  and hour = format_datetime(now() - interval '3' hour, 'HH')
  and section_assign_employee_first_level_department_name = 'H业务线'
  and section_assign_employee_second_level_department_name = '青橙项目部'
  and period_mapping_first_level_department_name = 'H业务线'
  and period_mapping_second_level_department_name in ('精品班学部', '青橙项目部')
  and valid_lead_count = '1';
```

## 6. 高风险误区

- 不要把 `rule_name` 当成“原始来源字段”。
- 不要因为 `period_name` / `lead_group_period_name` 看起来都是青橙IP，就忽略 `put_plan_name`、`source_put_plan_name`、`flow_pool_name`。
- 窗口函数别名不要命名成 `rn`。这张宽表存在物理字段 `rn`，容易报 `Column 'rn' is ambiguous`。
- 若业务要看“最早、最原始、未被任何当前归因覆盖”的 source，当前知识库只能先用本模式逼近，是否存在更上游明细表仍待人工确认。
