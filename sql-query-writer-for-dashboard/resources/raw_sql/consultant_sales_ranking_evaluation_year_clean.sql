with params as (
    select '2026' as qici_year
),
dd as (
    select
        id,
        order_number,
        substring(biz_number, 1, 10) as sub_biz_number,
        pre_biz_number,
        clazz_name,
        user_id as user_id1,
        pre_employee_id,
        type,
        trade_status,
        trade_type,
        order_paid_time as paid_time,
        trade_time,
        case
            when trade_status in ('全部退款', '部分退款') then -real_price
            else real_price
        end as real_price_0,
        transfer_price,
        price,
        email_prefix,
        employee_email_name as name,
        talent_type_name,
        city_name as city,
        department,
        biz_number,
        course_grade as grade_list,
        course_subject as subject,
        case
            when substr(trade_time, 1, 10) >= '2026-02-25' and substr(trade_time, 1, 10) <= '2026-03-02' then '20260227期'
            when substr(trade_time, 1, 10) >= '2026-02-17' and substr(trade_time, 1, 10) <= '2026-02-24' then '20260220期'
            when substr(trade_time, 1, 10) >= '2026-02-09' and substr(trade_time, 1, 10) <= '2026-02-16' then '20260213期'
            when substr(trade_time, 1, 10) >= '2026-02-03' and substr(trade_time, 1, 10) <= '2026-02-08' then '20260206期'
            when substr(trade_time, 1, 10) >= '2026-01-27' and substr(trade_time, 1, 10) <= '2026-02-02' then '20260130期'
            when substr(trade_time, 1, 10) >= '2026-01-20' and substr(trade_time, 1, 10) <= '2026-01-26' then '20260123期'
            else concat(
                date_format(
                    date_trunc('week', cast(trade_time as timestamp) - interval '1' day) + interval '4' day,
                    '%Y%m%d'
                ),
                '期'
            )
        end as qici,
        leader_employee_email_name,
        teacher_name,
        case course_term_id
            when 'C' then '春季'
            when 'X' then '夏季'
            when 'Q' then '秋季'
            when 'D' then '冬季'
            else '其他'
        end as school_term_id,
        note
    from finance_dw.app_finance_performance_extend_details_hf
    where dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
      and hour = format_datetime(now() - interval '2' hour, 'HH')
      and employee_first_level_department_name = 'H业务线'
      and employee_second_level_department_name = '市场部'
      and employee_third_level_department_name = '市场顾问部'
      and (
            case
                when substr(trade_time, 1, 10) >= '2026-02-25' and substr(trade_time, 1, 10) <= '2026-03-02' then '20260227期'
                when substr(trade_time, 1, 10) >= '2026-02-17' and substr(trade_time, 1, 10) <= '2026-02-24' then '20260220期'
                when substr(trade_time, 1, 10) >= '2026-02-09' and substr(trade_time, 1, 10) <= '2026-02-16' then '20260213期'
                when substr(trade_time, 1, 10) >= '2026-02-03' and substr(trade_time, 1, 10) <= '2026-02-08' then '20260206期'
                when substr(trade_time, 1, 10) >= '2026-01-27' and substr(trade_time, 1, 10) <= '2026-02-02' then '20260130期'
                when substr(trade_time, 1, 10) >= '2026-01-20' and substr(trade_time, 1, 10) <= '2026-01-26' then '20260123期'
                else concat(
                    date_format(
                        date_trunc('week', cast(trade_time as timestamp) - interval '1' day) + interval '4' day,
                        '%Y%m%d'
                    ),
                    '期'
                )
            end
          ) >= '20260320期'
),
gmv_t as (
    select
        id,
        order_number,
        clazz_name,
        user_id1,
        trade_status,
        trade_time,
        trade_type,
        email_prefix,
        name,
        grade_list,
        subject,
        qici,
        school_term_id,
        teacher_name,
        name_total_price
    from (
        select
            *,
            row_number() over (
                partition by name, user_id1
                order by id
            ) as dup_rn
        from (
            select
                *,
                round(sum(price) over (partition by name, user_id1), 3) as name_total_price
            from dd
            where trade_type = '调课调班'
        ) t1
        where name_total_price != 0
    ) t2
    where dup_rn = 1
),
gmv_z as (
    select
        id,
        order_number,
        clazz_name,
        user_id1,
        trade_status,
        trade_time,
        trade_type,
        email_prefix,
        name,
        grade_list,
        subject,
        qici,
        school_term_id,
        teacher_name,
        sum(price) as name_total_price
    from dd
    where trade_type = '正常订单'
    group by
        id,
        order_number,
        clazz_name,
        user_id1,
        trade_status,
        trade_time,
        trade_type,
        email_prefix,
        name,
        grade_list,
        subject,
        qici,
        school_term_id,
        teacher_name
),
rd as (
    select
        id,
        order_number,
        clazz_name,
        user_id1,
        trade_status,
        trade_time,
        trade_type,
        email_prefix,
        name,
        grade_list,
        subject,
        qici,
        school_term_id,
        teacher_name,
        name_total_price
    from gmv_z

    union all

    select
        id,
        order_number,
        clazz_name,
        user_id1,
        trade_status,
        trade_time,
        trade_type,
        email_prefix,
        name,
        grade_list,
        subject,
        qici,
        school_term_id,
        teacher_name,
        name_total_price
    from gmv_t
),
jiagou_zx_active as (
    select
        employee_email_name
    from (
        select
            zx.*,
            row_number() over (
                partition by zx.employee_email_name
                order by
                    case
                        when zx.department = '郑州顾问部' then 1
                        when zx.department = '西安一部' then 2
                        when zx.department = '西安二部' then 3
                        else 9
                    end,
                    zx.employee_email_prefix,
                    zx.xiaozu,
                    zx.jingli
            ) as rn
        from temp_table.dingxi01_jiagou_zx zx
        where cast(zx.zaizhi as varchar) = '1'
          and zx.department in ('郑州顾问部', '西安一部', '西安二部')
    ) t
    where rn = 1
),
pingyou_base as (
    select
        pg.*,
        case
            when try_cast(substring(pg.qici, 5, 2) as int) between 4 and 9 then
                concat(substring(pg.qici, 1, 4), '上半年')
            when try_cast(substring(pg.qici, 5, 2) as int) between 10 and 12 then
                concat(substring(pg.qici, 1, 4), '下半年')
            when try_cast(substring(pg.qici, 5, 2) as int) between 1 and 3 then
                concat(cast(cast(substring(pg.qici, 1, 4) as int) - 1 as varchar), '下半年')
            else '其他'
        end as half_year
    from temp_table.zhangjunyan01_pingyou_jg pg
    inner join jiagou_zx_active zx
      on zx.employee_email_name = pg.employee_email_name
    where cast(pg.zaizhi as varchar) = '1'
      and pg.is_emp = '是'
      and pg.qici >= '20260320期'
),
period_total as (
    select
        half_year,
        count(distinct qici) as total_period_count
    from pingyou_base
    group by half_year
),
consultant_period as (
    select
        half_year,
        employee_email_name,
        count(distinct qici) as consultant_period_count
    from pingyou_base
    group by
        half_year,
        employee_email_name
),
attendance_metric as (
    select
        cp.half_year,
        cp.employee_email_name,
        cp.consultant_period_count,
        pt.total_period_count
    from consultant_period cp
    left join period_total pt
      on pt.half_year = cp.half_year
),
ceshi_metric as (
    select
        name as employee_email_name,
        1 as is_join_test_channel,
        max(
            case
                when cast(gmv as double) / nullif(cast(gmv_goal as double), 0) > 0.8 then 1
                else 0
            end
        ) as is_test_gmv_rate_over_80
    from temp_table.dingxi01_ceshiqudao_pingyou
    where name is not null
    group by name
),
process as (
    select
        pg.half_year,
        pg.employee_email_name,
        pg.dept,
        pg.jingli,
        pg.xiaozu,
        pg.channel,
        cast(pg.renchan as decimal) as renchan,
        pg.grade,
        pg.is_emp,
        sum(name_total_price) as pt,
        sum(case when name_total_price > 0 then name_total_price else 0 end) as inc,
        sum(case when name_total_price < 0 then name_total_price else 0 end) as ref
    from pingyou_base pg
    left join rd
      on pg.employee_email_name = rd.name
     and pg.qici = rd.qici
    group by
        pg.half_year,
        pg.employee_email_name,
        pg.dept,
        pg.jingli,
        pg.xiaozu,
        pg.channel,
        pg.renchan,
        pg.grade,
        pg.is_emp
),
rank_data as (
    select
        *,
        case when channel like '%抖音私域%' then 10 else 0 end as ceshi
    from process
),
rank_h as (
    select
        half_year,
        employee_email_name,
        dept,
        jingli,
        xiaozu,
        array_join(array_agg(distinct channel), ',') as channel,
        sum(renchan) as renchan,
        sum(inc) as inc,
        sum(pt) as pt,
        sum(ref) as ref,
        round(coalesce(sum(pt) / sum(renchan), 0), 4) as roi,
        round(coalesce(sum(-ref) / nullif(sum(inc), 0), 0), 4) as refd
    from rank_data
    group by
        half_year,
        employee_email_name,
        dept,
        jingli,
        xiaozu
),
rk_r as (
    select
        *,
        rank() over (
            partition by rank_h.half_year
            order by rank_h.roi desc
        ) as rank_in_roi
    from rank_h
),
ref_rank as (
    select
        *,
        row_number() over (
            partition by half_year
            order by
                case when inc > 0 then 1 else 2 end,
                case when inc > 0 then refd else null end,
                case when inc = 0 and ref = 0 then 1 else 2 end,
                case when inc = 0 and ref < 0 then abs(ref) else null end
        ) as rank_in_ref
    from rk_r
),
final_result as (
    select
        rr.*,
        coalesce(am.consultant_period_count, 0) as consultant_period_count,
        coalesce(am.total_period_count, 0) as total_period_count,
        coalesce(cm.is_join_test_channel, 0) as is_join_test_channel,
        coalesce(cm.is_test_gmv_rate_over_80, 0) as is_test_gmv_rate_over_80
    from ref_rank rr
    left join attendance_metric am
      on am.half_year = rr.half_year
     and am.employee_email_name = rr.employee_email_name
    left join ceshi_metric cm
      on cm.employee_email_name = rr.employee_email_name
)
select
    *,
    round(
        rank_in_roi * 1.0 / nullif(count(*) over (partition by half_year), 0),
        5
    ) as rank_position_roi,
    round(
        rank_in_ref * 1.0 / nullif(count(*) over (partition by half_year), 0),
        5
    ) as rank_position_ref,
    case
        when channel like '%抖音私域%' or channel like '%抖音私信%' then 10
        else 0
    end as cs_channel_rank,
    case
        when (channel like '%抖音私域%' or channel like '%抖音私信%')
         and roi >= 0.8 then 2
        else 0
    end as cs_80_rank
from final_result
