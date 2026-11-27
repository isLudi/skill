with src as (
    select
        case
            when cast(date_parse(replace(concat(t.group_period_year, t.group_period_term), '期', ''), '%Y%m%d') as date)
                between date '2026-07-14' and date '2026-07-19'
            then '20260716期'
            when cast(date_parse(replace(concat(t.group_period_year, t.group_period_term), '期', ''), '%Y%m%d') as date)
                between date '2026-07-20' and date '2026-07-25'
            then '20260722期'
            when cast(date_parse(replace(concat(t.group_period_year, t.group_period_term), '期', ''), '%Y%m%d') as date)
                between date '2026-07-26' and date '2026-07-31'
            then '20260728期'
            when cast(date_parse(replace(concat(t.group_period_year, t.group_period_term), '期', ''), '%Y%m%d') as date)
                between date '2026-08-01' and date '2026-08-06'
            then '20260803期'
            when cast(date_parse(replace(concat(t.group_period_year, t.group_period_term), '期', ''), '%Y%m%d') as date)
                between date '2026-08-07' and date '2026-08-12'
            then '20260808期'
            when cast(date_parse(replace(concat(t.group_period_year, t.group_period_term), '期', ''), '%Y%m%d') as date)
                between date '2026-08-13' and date '2026-08-18'
            then '20260815期'
            else concat(
                date_format(
                    date_trunc('week', cast(date_parse(replace(concat(t.group_period_year, t.group_period_term), '期', ''), '%Y%m%d') as date)) + interval '4' day,
                    '%Y%m%d'
                ),
                '期'
            )
        end as period_name,
        t.lead_id,
        t.user_id,
        t.rule_name,
        t.flow_pool_name,
        t.sku_id_name,
        t.ad_account_name,
        t.source_manager_name,
        t.channel_name_1,
        t.channel_name_2,
        t.channel_name_3,
        t.put_plan_name,
        cast(t.flow_original_order_activity_price as varchar) as flow_original_order_activity_price,
        cast(t.flow_orders_income_amount as varchar) as flow_orders_income_amount,
        cast(t.flow_order_price as varchar) as flow_order_price,
        t.channel_provider_name,
        t.channel_second_provider_name,
        t.page_id_name,
        t.source_put_plan_name,
        t.get_customer_way_name,
        t.first_department_name,
        t.second_department_name,
        t.third_department_name,
        t.virtual_second_department_name,
        t.virtual_third_department_name,
        t.virtual_fourth_department_name,
        t.virtual_fifth_department_name,
        t.lead_purchase_intention_name,
        t.trace_type_name,
        t.lead_purchase_intention_level1_category_name,
        t.lead_purchase_intention_level2_category_name,
        t.lead_create_time,
        coalesce(t.virtual_leader_email_name, '未知') as manager_name,
        coalesce(t.lead_count, 0) as lead_count,
        coalesce(t.merge_assign_lead_count, 0) as merge_assign_lead_count,
        coalesce(t.valid_lead_count, 0) as valid_lead_count,
        coalesce(t.merge_valid_lead_count, 0) as merge_valid_lead_count,
        coalesce(t.conversion_lead_count, 0) as conversion_lead_count,
        coalesce(t.subject_count, 0) as subject_count,
        coalesce(t.order_count, 0) as order_count,
        coalesce(t.income_amount, 0) as income_amount,
        coalesce(t.in_pay_period_refund_amount, 0) as in_pay_period_refund_amount,
        coalesce(t.non_pay_period_refund_amount, 0) as non_pay_period_refund_amount
    from bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df t
    where t.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
      and t.hour = format_datetime(now() - interval '3' hour, 'HH')
      and t.section_assign_employee_first_level_department_name = 'H业务线'
      and t.section_assign_employee_second_level_department_name = '市场部'
      and t.section_assign_employee_third_level_department_name = '市场顾问部'
      and t.virtual_third_department_name = '市场顾问部'
      and t.period_mapping_first_level_department_name = 'H业务线'
      and t.period_mapping_second_level_department_name IN ('市场部', '精品班学部')
),
lead_channel_dim as (
    select lead_id, channel_map
    from gaotu_hl.dim_mkt_h_lead_channel_df
    where dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
),
src_mapped as (
    select s.*, coalesce(c.channel_map, '未知') as channel_map
    from src s
    left join lead_channel_dim c on cast(s.lead_id as varchar) = c.lead_id
),
data as (
    select
        period_name,
        channel_map,
        case
            when rule_name like '%高一%' then '高一'
            when rule_name like '%高二%' then '高二'
            when rule_name like '%高三%' then '高三'
            when rule_name like '%初二%' then '初二'
            when rule_name like '%初三%' then '初三'
            else '未知'
        end as grade_name,
        manager_name,
        lead_id,
        user_id,
        lead_count,
        merge_assign_lead_count,
        valid_lead_count,
        merge_valid_lead_count,
        conversion_lead_count,
        subject_count,
        order_count,
        income_amount,
        in_pay_period_refund_amount,
        non_pay_period_refund_amount
    from src_mapped
    where period_name >= ${qici:1} and period_name < ${qici:2}
),
user_base as (
    select
        period_name,
        channel_map,
        grade_name,
        manager_name,
        user_id,
        sum(lead_count) as lead_count,
        sum(valid_lead_count) as valid_lead_count,
        sum(conversion_lead_count) as regular_course_user_count,
        sum(order_count) as regular_course_order_count,
        sum(subject_count) as pay_subject_person_count,
        sum(income_amount / 100.0) as trade_income,
        sum((income_amount - in_pay_period_refund_amount - non_pay_period_refund_amount) / 100.0) as net_income
    from data
    group by
        period_name,
        channel_map,
        grade_name,
        manager_name,
        user_id
),
agg as (
    select
        period_name,
        channel_map,
        grade_name,
        manager_name,
        sum(lead_count) as lead_count,
        sum(case when regular_course_user_count > 0 then 1 else 0 end) as pay_user_head_count,
        sum(pay_subject_person_count) as pay_subject_person_count,
        sum(net_income) as net_income,
        sum(case when regular_course_user_count > 0 and pay_subject_person_count = 1 then 1 else 0 end) as subject_1_user_count,
        sum(case when regular_course_user_count > 0 and pay_subject_person_count = 1 then net_income else 0 end) as subject_1_gmv,
        sum(case when regular_course_user_count > 0 and pay_subject_person_count between 2 and 3 then 1 else 0 end) as subject_2_3_user_count,
        sum(case when regular_course_user_count > 0 and pay_subject_person_count between 2 and 3 then net_income else 0 end) as subject_2_3_gmv,
        sum(case when regular_course_user_count > 0 and pay_subject_person_count > 3 then 1 else 0 end) as subject_3_plus_user_count,
        sum(case when regular_course_user_count > 0 and pay_subject_person_count > 3 then net_income else 0 end) as subject_3_plus_gmv,
        sum(case when regular_course_user_count > 0 and pay_subject_person_count = 0 then 1 else 0 end) as subject_0_user_count,
        sum(case when regular_course_user_count > 0 and pay_subject_person_count = 0 then net_income else 0 end) as subject_0_gmv,
        sum(valid_lead_count) as valid_lead_count,
        sum(trade_income) as trade_income,
        sum(net_income) as net_trade_income,
        sum(regular_course_user_count) as regular_course_user_count,
        sum(regular_course_order_count) as regular_course_order_count
    from user_base
    group by
        period_name,
        channel_map,
        grade_name,
        manager_name
)
select
    period_name,
    channel_map,
    grade_name,
    manager_name,
    lead_count,
    pay_user_head_count,
    pay_subject_person_count,
    net_income,
    subject_1_user_count,
    subject_1_gmv,
    subject_2_3_user_count,
    subject_2_3_gmv,
    subject_3_plus_user_count,
    subject_3_plus_gmv,
    subject_0_user_count,
    subject_0_gmv,
    valid_lead_count,
    trade_income,
    net_trade_income,
    regular_course_user_count,
    regular_course_order_count,
    case when regular_course_user_count = 0 then 0 else trade_income / regular_course_user_count end as avg_income_per_regular_course_user
from agg
order by
    period_name,
    channel_map,
    grade_name,
    manager_name
