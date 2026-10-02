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
            ('20260306期', date '2026-03-02', date '2026-03-08'),
            ('20260313期', date '2026-03-09', date '2026-03-15'),
            ('20260320期', date '2026-03-16', date '2026-03-22'),
            ('20260327期', date '2026-03-23', date '2026-03-29'),
            ('20260403期', date '2026-03-30', date '2026-04-05'),
            ('20260410期', date '2026-04-06', date '2026-04-12'),
            ('20260417期', date '2026-04-13', date '2026-04-19'),
            ('20260424期', date '2026-04-20', date '2026-04-26'),
            ('20260501期', date '2026-04-27', date '2026-05-03'),
            ('20260508期', date '2026-05-04', date '2026-05-10'),
            ('20260515期', date '2026-05-11', date '2026-05-17'),
            ('20260522期', date '2026-05-18', date '2026-05-24'),
            ('20260529期', date '2026-05-25', date '2026-05-31'),
            ('20260605期', date '2026-06-01', date '2026-06-07'),
            ('20260612期', date '2026-06-08', date '2026-06-14'),
            ('20260619期', date '2026-06-15', date '2026-06-21'),
            ('20260626期', date '2026-06-22', date '2026-06-28'),
            ('20260703期', date '2026-06-29', date '2026-07-05'),
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
        o.performance_employee_email_name as employee_email_name,
        cast(o.lead_id as varchar) as lead_id,
        cast(o.original_order_user_number as varchar) as user_id,
        cast(
            date_parse(
                replace(concat(o.trade_group_period_year, o.trade_group_period_term), '期', ''),
                '%Y%m%d'
            ) as date
        ) as period_date,
        case
            when o.pay_refund_type = '支付'
             and o.is_pay_success_order = 1
             and o.is_stats_conversion_amount = 'Y'
            then coalesce(cast(o.income_amount as double), 0.0)
            else 0.0
        end as income_amount,
        case
            when o.pay_refund_type = '退款'
            then coalesce(cast(o.refund_amount as double), 0.0)
            else 0.0
        end as refund_amount
    from service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf o
    where o.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
      and o.hour = format_datetime(now() - interval '2' hour, 'HH')
      and o.performance_first_level_department_name = 'H业务线'
      and o.performance_second_level_department_name = '市场部'
      and o.performance_third_level_department_name = '市场顾问部'
      and o.course_first_level_department_name = 'H业务线'
      and o.course_second_level_department_name in (
          '精品班学部',
          '菁英班学部',
          '本地化大班学部'
      )
      and o.trade_period_mapping_first_level_department_name = 'H业务线'
      and o.pay_period_mapping_first_level_department_name = 'H业务线'
),
crm_fact_row as (
    select
        coalesce(
            cal.qici,
            concat(
                date_format(
                    date_trunc('week', cast(s.period_date as timestamp))
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
        s.refund_amount
    from crm_source s
    left join biz_qici_calendar cal
      on s.period_date between cal.start_date and cal.end_date
),
crm_fact as (
    select
        qici,
        employee_email_name,
        sum(income_amount - refund_amount) / 100.0 as pt,
        sum(income_amount) / 100.0 as inc,
        -sum(refund_amount) / 100.0 as ref
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
period_agg as (
    select
        moth,
        employee_email_name,
        array_join(array_agg(distinct channel), ',') as channel,
        sum(renchan) as renchan,
        sum(inc) as inc,
        sum(pt) as pt,
        sum(ref) as ref
    from process
    group by moth, employee_email_name
),
period_profile as (
    select
        moth,
        employee_email_name,
        dept,
        jingli,
        xiaozu
    from (
        select
            moth,
            qici,
            employee_email_name,
            dept,
            jingli,
            xiaozu,
            row_number() over (
                partition by moth, employee_email_name
                order by qici desc
            ) as rn
        from process
    ) t
    where rn = 1
),
rank_h as (
    select
        a.moth,
        a.employee_email_name,
        p.dept,
        p.jingli,
        p.xiaozu,
        a.channel,
        a.renchan,
        a.inc,
        a.pt,
        a.ref,
        round(coalesce(a.pt / nullif(a.renchan, 0), 0), 4) as roi,
        round(coalesce(-a.ref / nullif(a.inc, 0), 0), 4) as refd
    from period_agg a
    left join period_profile p
      on p.moth = a.moth
     and p.employee_email_name = a.employee_email_name
),
rk_r as (
    select
        *,
        rank() over (partition by moth order by roi desc) as rank_in_roi
    from rank_h
),
ref_rank as (
    select
        *,
        row_number() over (
            partition by moth
            order by
                case when inc > 0 then 1 else 2 end,
                case when inc > 0 then refd else null end,
                case when inc = 0 and ref = 0 then 1 else 2 end,
                case when inc = 0 and ref < 0 then abs(ref) else null end
        ) as rank_in_ref
    from rk_r
),
attendance_base as (
    select distinct
        moth,
        qici,
        employee_email_name
    from process
),
attendance_metric as (
    select
        cp.moth,
        cp.employee_email_name,
        cp.consultant_period_count,
        pt.total_period_count
    from (
        select
            moth,
            employee_email_name,
            count(distinct qici) as consultant_period_count
        from attendance_base
        group by moth, employee_email_name
    ) cp
    left join (
        select
            moth,
            count(distinct qici) as total_period_count
        from attendance_base
        group by moth
    ) pt
      on pt.moth = cp.moth
),
final_result as (
    select
        rr.*,
        coalesce(am.consultant_period_count, 0) as consultant_period_count,
        coalesce(am.total_period_count, 0) as total_period_count
    from ref_rank rr
    left join attendance_metric am
      on am.moth = rr.moth
     and am.employee_email_name = rr.employee_email_name
)
select
    moth,
    employee_email_name,
    dept,
    jingli,
    xiaozu,
    channel,
    renchan,
    inc,
    pt,
    ref,
    roi,
    refd,
    rank_in_roi,
    rank_in_ref,
    consultant_period_count,
    total_period_count,
    round(rank_in_roi * 1.0 / nullif(count(*) over (partition by moth), 0), 5) as rank_position_roi,
    round(rank_in_ref * 1.0 / nullif(count(*) over (partition by moth), 0), 5) as rank_position_ref,
    case when channel like '%抖音私域%' or channel like '%抖音私信%' then 10 else 0 end as cs_channel_rank,
    case
        when (channel like '%抖音私域%' or channel like '%抖音私信%') and roi >= 0.8 then 2
        else 0
    end as cs_80_rank
from final_result
