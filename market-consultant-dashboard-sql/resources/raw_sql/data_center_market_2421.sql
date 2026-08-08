with biz_qici_calendar as (
    select *
    from (
        values
            ('20251226期', date '2025-12-23', date '2025-12-29'),
            ('20260101期', date '2025-12-30', date '2026-01-05'),
            ('20260109期', date '2026-01-06', date '2026-01-12'),
            ('20260116期', date '2026-01-13', date '2026-01-19'),
            ('20260123期', date '2026-01-20', date '2026-01-26'),
            ('20260130期', date '2026-01-27', date '2026-02-02'),
            ('20260205期', date '2026-02-03', date '2026-02-08'),
            ('20260211期', date '2026-02-09', date '2026-02-15'),
            ('20260227期', date '2026-02-16', date '2026-03-02'),
            ('20260306期', date '2026-03-03', date '2026-03-09'),
            ('20260313期', date '2026-03-10', date '2026-03-16'),
            ('20260320期', date '2026-03-17', date '2026-03-23'),
            ('20260327期', date '2026-03-24', date '2026-03-30'),
            ('20260403期', date '2026-03-31', date '2026-04-06'),
            ('20260410期', date '2026-04-07', date '2026-04-13'),
            ('20260417期', date '2026-04-14', date '2026-04-20'),
            ('20260424期', date '2026-04-21', date '2026-04-27'),
            ('20260501期', date '2026-04-28', date '2026-05-04'),
            ('20260508期', date '2026-05-05', date '2026-05-11'),
            ('20260515期', date '2026-05-12', date '2026-05-18'),
            ('20260522期', date '2026-05-19', date '2026-05-25'),
            ('20260529期', date '2026-05-26', date '2026-06-01'),
            ('20260605期', date '2026-06-02', date '2026-06-08'),
            ('20260612期', date '2026-06-09', date '2026-06-15'),
            ('20260619期', date '2026-06-16', date '2026-06-22'),
            ('20260626期', date '2026-06-23', date '2026-06-29'),
            ('20260703期', date '2026-06-30', date '2026-07-07'),
            ('20260710期', date '2026-07-08', date '2026-07-13'),
            ('20260716期', date '2026-07-14', date '2026-07-19'),
            ('20260722期', date '2026-07-20', date '2026-07-25'),
            ('20260728期', date '2026-07-26', date '2026-07-31'),
            ('20260803期', date '2026-08-01', date '2026-08-06'),
            ('20260808期', date '2026-08-07', date '2026-08-12'),
            ('20260815期', date '2026-08-13', date '2026-08-18')
    ) as t(qici, start_date, end_date)
),
crm_source as (
    select
        t.employee_email_name,
        t.lead_id,
        t.user_id,
        cast(
            date_parse(
                replace(concat(t.group_period_year, t.group_period_term), '期', ''),
                '%Y%m%d'
            ) as date
        ) as period_date,
        coalesce(t.income_amount, 0) as income_amount,
        coalesce(t.in_pay_period_refund_amount, 0) as in_pay_period_refund_amount,
        coalesce(t.non_pay_period_refund_amount, 0) as non_pay_period_refund_amount
    from bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df t
    where t.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
      and t.hour = format_datetime(now() - interval '3' hour, 'HH')
      and t.section_assign_employee_first_level_department_name = 'H业务线'
      and t.section_assign_employee_second_level_department_name = '市场部'
      and t.section_assign_employee_third_level_department_name = '市场顾问部'
      and t.period_mapping_first_level_department_name = 'H业务线'
),
crm_fact_row as (
    select distinct
        coalesce(
            cal.qici,
            concat(
                date_format(
                    date_trunc('week', cast(s.period_date as timestamp) - interval '1' day)
                        + interval '4' day,
                    '%Y%m%d'
                ),
                '期'
            )
        ) as qici,
        s.employee_email_name,
        s.lead_id,
        s.user_id,
        s.income_amount,
        s.in_pay_period_refund_amount,
        s.non_pay_period_refund_amount
    from crm_source s
    left join biz_qici_calendar cal
      on s.period_date between cal.start_date and cal.end_date
),
crm_fact as (
    select
        qici,
        employee_email_name,
        sum(income_amount - in_pay_period_refund_amount - non_pay_period_refund_amount) / 100.0 as pt,
        sum(income_amount) / 100.0 as inc,
        -sum(in_pay_period_refund_amount + non_pay_period_refund_amount) / 100.0 as ref
    from crm_fact_row
    where qici >= '20260101期'
    group by qici, employee_email_name
),
eligible_roster as (
    select
        qici,
        employee_email_name,
        dept,
        jingli,
        xiaozu,
        channel,
        cast(renchan as decimal) as renchan,
        grade,
        is_emp
    from (
        select
            pg.*,
            row_number() over (
                partition by pg.qici, pg.employee_email_name
                order by
                    coalesce(pg.channel, ''),
                    coalesce(pg.grade, ''),
                    coalesce(pg.dept, ''),
                    coalesce(pg.jingli, ''),
                    coalesce(pg.xiaozu, '')
            ) as rn
        from temp_table.zhangjunyan01_pingyou_jg pg
        where pg.qici >= '20260101期'
          and cast(pg.zaizhi as varchar) = '1'
          and pg.is_emp = '是'
    ) t
    where rn = 1
),
process as (
    select
        pg.qici,
        substring(pg.qici, 1, 6) as moth,
        pg.employee_email_name,
        pg.dept,
        pg.jingli,
        pg.xiaozu,
        pg.channel,
        coalesce(pg.renchan, cast(0 as decimal)) as renchan,
        pg.grade,
        pg.is_emp,
        coalesce(f.pt, 0.0) as pt,
        coalesce(f.inc, 0.0) as inc,
        coalesce(f.ref, 0.0) as ref
    from eligible_roster pg
    left join crm_fact f
      on f.qici = pg.qici
     and f.employee_email_name = pg.employee_email_name
),
rank_data as (
    select
        *,
        round(coalesce(pt / nullif(renchan, 0), 0), 4) as roi,
        round(coalesce(-ref / nullif(inc, 0), 0), 4) as refd,
        case when channel like '%抖音私域%' then 10 else 0 end as ceshi
    from process
),
rk_r as (
    select
        *,
        rank() over (partition by qici order by roi desc) as rank_in_roi
    from rank_data
),
ref_rank as (
    select
        *,
        row_number() over (
            partition by qici
            order by
                case when inc > 0 then 1 else 2 end,
                case when inc > 0 then refd else null end,
                case when inc = 0 and ref = 0 then 1 else 2 end,
                case when inc = 0 and ref < 0 then abs(ref) else null end
        ) as rank_in_ref
    from rk_r
)
select
    qici,
    moth,
    employee_email_name,
    dept,
    jingli,
    xiaozu,
    channel,
    renchan,
    grade,
    is_emp,
    pt,
    inc,
    ref,
    roi,
    refd,
    ceshi,
    rank_in_roi,
    rank_in_ref,
    round(rank_in_roi * 1.0 / nullif(count(*) over (partition by qici), 0), 5) as rank_position_roi,
    round(rank_in_ref * 1.0 / nullif(count(*) over (partition by qici), 0), 5) as rank_position_ref,
    case when channel like '%抖音私域%' or channel like '%抖音私信%' then 10 else 0 end as cs_channel_rank,
    case
        when (channel like '%抖音私域%' or channel like '%抖音私信%') and roi >= 0.8 then 2
        else 0
    end as cs_80_rank
from ref_rank
