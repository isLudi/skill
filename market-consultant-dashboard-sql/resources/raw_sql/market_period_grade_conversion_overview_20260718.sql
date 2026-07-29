with base_raw as (
    select
        concat(
            date_format(
                date_trunc(
                    'week',
                    date_parse(replace(concat(t.group_period_year, t.group_period_term), '期', ''), '%Y%m%d') - interval '1' day
                ) + interval '4' day,
                '%Y%m%d'
            ),
            '期'
        ) as period_name,
        case
            when t.rule_name like '%初一%' then '初一'
            when t.rule_name like '%初二%' then '初二'
            when t.rule_name like '%初三%' then '初三'
            else t.lead_purchase_intention_level2_category_name
        end as grade,
        t.lead_id,
        t.user_id,
        t.employee_email_prefix,
        t.employee_email_name,
        t.rule_name,
        coalesce(t.lead_count, 0) as lead_count,
        coalesce(t.conversion_lead_count, 0) as conversion_lead_count,
        coalesce(t.order_count, 0) as order_count,
        coalesce(t.income_amount, 0) as income_amount,
        coalesce(t.in_pay_period_refund_amount, 0) as in_pay_period_refund_amount,
        coalesce(t.non_pay_period_refund_amount, 0) as non_pay_period_refund_amount
    from bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df t
    where t.dt = format_datetime(now() - interval '3' hour, 'YYYYMMdd')
      and t.hour = format_datetime(now() - interval '3' hour, 'HH')
      and t.section_assign_employee_first_level_department_name = 'H业务线'
      and t.section_assign_employee_second_level_department_name in ('市场部', '精品班学部', '青橙项目部', '菁英班学部')
      and t.virtual_third_department_name in ('学习顾问部', '市场顾问部', '中价产品项目部')
      and (t.period_mapping_first_level_department_name = 'H业务线' or t.period_mapping_first_level_department_name is null)
), base as (
    select
        period_name,
        grade,
        lead_id,
        user_id,
        employee_email_prefix,
        employee_email_name,
        rule_name,
        lead_count,
        conversion_lead_count,
        order_count,
        income_amount,
        in_pay_period_refund_amount,
        non_pay_period_refund_amount
    from base_raw
    group by
        period_name,
        grade,
        lead_id,
        user_id,
        employee_email_prefix,
        employee_email_name,
        rule_name,
        lead_count,
        conversion_lead_count,
        order_count,
        income_amount,
        in_pay_period_refund_amount,
        non_pay_period_refund_amount
), filtered as (
    select
        period_name,
        grade,
        lead_count,
        conversion_lead_count,
        order_count,
        income_amount,
        in_pay_period_refund_amount,
        non_pay_period_refund_amount
    from base
    where period_name >= '20250502期'
      and period_name <= '20251226期'
      and grade in ('初一', '初二', '初三')
)
select
    period_name,
    grade,
    sum(lead_count) as lead_count,
    sum(conversion_lead_count) as head_conversion_users_num,
    sum(lead_count) as head_conversion_leads_den,
    sum(order_count) as order_conversion_orders_num,
    sum(lead_count) as order_conversion_leads_den,
    sum((income_amount - in_pay_period_refund_amount - non_pay_period_refund_amount) / 100.00) as net_income_amt,
    sum((income_amount - in_pay_period_refund_amount - non_pay_period_refund_amount) / 100.00) as unit_efficiency_profit_num,
    sum(lead_count) as unit_efficiency_leads_den
from filtered
group by
    period_name,
    grade
order by
    period_name,
    grade
limit 1000
