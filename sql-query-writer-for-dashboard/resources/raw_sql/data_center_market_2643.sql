with dd as (
    select *
    from (
    select
        id, order_number,
        substring(biz_number, 1, 10) AS sub_biz_number,
        pre_biz_number, clazz_name, user_id AS user_id1,
        pre_employee_id, type, trade_status, trade_type,
        order_paid_time as paid_time, trade_time,
        case
            when trade_status in ('全部退款','部分退款') then -real_price
            else real_price
        end as real_price_0,
        transfer_price, price, email_prefix,
        employee_email_name as name,
        talent_type_name, city_name as city, department,
        biz_number, course_grade as grade_list,
        course_subject as subject,
 	    case
			when substr(trade_time, 1, 10) between '2026-07-14' and '2026-07-19' then '20260716期'
			when substr(trade_time, 1, 10) between '2026-07-20' and '2026-07-25' then '20260722期'
			when substr(trade_time, 1, 10) between '2026-07-26' and '2026-07-31' then '20260728期'
			when substr(trade_time, 1, 10) between '2026-08-01' and '2026-08-06' then '20260803期'
			when substr(trade_time, 1, 10) between '2026-08-07' and '2026-08-12' then '20260809期'
 			when substr(trade_time, 1, 10) >= '2026-02-16' and substr(trade_time, 1, 10) <= '2026-03-02' then '20260227期'
 			when substr(trade_time, 1, 10) >= '2026-02-09' and substr(trade_time, 1, 10) <= '2026-02-15' then '20260211期'
 			when substr(trade_time, 1, 10) >= '2026-02-03' and substr(trade_time, 1, 10) <= '2026-02-08' then '20260205期'
 			when substr(trade_time, 1, 10) >= '2026-01-27' and substr(trade_time, 1, 10) <= '2026-02-02' then '20260130期'
 			when substr(trade_time, 1, 10) >= '2026-01-20' and substr(trade_time, 1, 10) <= '2026-01-26' then '20260123期'
 		else concat(date_format(date_trunc('week', cast(trade_time as timestamp) - interval '1' day) + interval '4' day, '%Y%m%d'), '期') end as qici,
        leader_employee_email_name, teacher_name,
        case course_term_id
            when 'C' then '春季'
            when 'X' then '夏季'
            when 'Q' then '秋季'
            when 'D' then '冬季'
            else '其他'
        end as school_term_id,
        note
    from finance_dw.app_finance_performance_extend_details_hf
    where dt = FORMAT_DATETIME(NOW() - INTERVAL '2' HOUR, 'YYYYMMdd')
        and hour = FORMAT_DATETIME(NOW() - INTERVAL '2' HOUR, 'HH')
        and employee_first_level_department_name = 'H业务线'
 	    and employee_second_level_department_name = '市场部'
        and employee_third_level_department_name = '市场顾问部'
    ) base
    where base.qici >= '20251226期'
)
,gmv_t as (
    select
        id, order_number, clazz_name, user_id1, trade_status, trade_time,
        trade_type, email_prefix, name, grade_list, subject,
        qici, school_term_id, teacher_name,
        name_total_price
    from (
        select
            *,row_number() over (partition by name, user_id1 order by id) as dup_rn
        from (
            select
                *,round(sum(price) over (partition by name, user_id1), 3) as name_total_price
            from dd
            where trade_type = '调课调班'
        ) t1
        where name_total_price != 0
    ) t2
    where dup_rn = 1
)
,gmv_z as (
    select
        id, order_number, clazz_name, user_id1, trade_status, trade_time,
        trade_type, email_prefix, name, grade_list, subject,
        qici, school_term_id, teacher_name,
        sum(price) as name_total_price
    from dd
    where trade_type = '正常订单'
    group by id, order_number, clazz_name, user_id1, trade_status, trade_time,
             trade_type, email_prefix, name, grade_list, subject,
             qici, school_term_id, teacher_name
)
,rd as (
    select
        id, order_number, clazz_name, user_id1, trade_status, trade_time,
        trade_type, email_prefix, name, grade_list, subject,
        qici, school_term_id, teacher_name,
        name_total_price
    from gmv_z
    union all
    select
        id, order_number, clazz_name, user_id1, trade_status, trade_time,
        trade_type, email_prefix, name, grade_list, subject,
        qici, school_term_id, teacher_name,
        name_total_price
    from gmv_t
)
,jiagou_zx_active as (
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
)
,process as (select
    case
        when substring(pg.qici, 1, 6) between '202601' and '202603' then '2026Q1'
        when substring(pg.qici, 1, 6) between '202604' and '202606' then '2026Q2'
        when substring(pg.qici, 1, 6) between '202607' and '202609' then '2026Q3'
        when substring(pg.qici, 1, 6) between '202610' and '202612' then '2026Q4'
        when substring(pg.qici, 1, 6) between '202701' and '202703' then '2027Q1'
        else concat(substring(pg.qici, 1, 4), 'Q',
                    cast((cast(substring(pg.qici, 5, 2) as int) - 1) / 3 + 1 as varchar))
    end as quarter,
    pg.employee_email_name, pg.dept, pg.jingli, pg.xiaozu, pg.channel,
    cast(pg.renchan as decimal) as renchan, pg.grade, pg.is_emp,
    sum(name_total_price) as pt,
    sum(case when name_total_price > 0 then name_total_price else 0 end) as inc,
    sum(case when name_total_price < 0 then name_total_price else 0 end) as ref
from temp_table.zhangjunyan01_pingyou_jg pg
inner join jiagou_zx_active zx on zx.employee_email_name = pg.employee_email_name
left join rd on pg.employee_email_name = rd.name and pg.qici = rd.qici
where cast(pg.zaizhi as varchar) = '1' and pg.is_emp = '是'
and pg.qici >= '20251226期'
group by
    case
        when substring(pg.qici, 1, 6) between '202601' and '202603' then '2026Q1'
        when substring(pg.qici, 1, 6) between '202604' and '202606' then '2026Q2'
        when substring(pg.qici, 1, 6) between '202607' and '202609' then '2026Q3'
        when substring(pg.qici, 1, 6) between '202610' and '202612' then '2026Q4'
        when substring(pg.qici, 1, 6) between '202701' and '202703' then '2027Q1'
        else concat(substring(pg.qici, 1, 4), 'Q',
                    cast((cast(substring(pg.qici, 5, 2) as int) - 1) / 3 + 1 as varchar))
    end,
    pg.employee_email_name, pg.dept, pg.jingli, pg.xiaozu, pg.channel,
    pg.renchan, pg.grade, pg.is_emp
)
,rank as (select *,
    case when channel like '%抖音私域%' then 10 else 0 end as ceshi
from process)
,rank_h as (select
    quarter,
    employee_email_name, dept, jingli, xiaozu,
    array_join(array_agg(distinct channel), ',') as channel,
    sum(renchan) as renchan,
    sum(inc) as inc,
    sum(pt) as pt,
    sum(ref) as ref,
    round(coalesce(sum(pt)/sum(renchan), 0), 4) as roi,
    round(coalesce(sum(-ref) / nullif(sum(inc), 0), 0), 4) as refd
from rank
group by quarter, employee_email_name, dept, jingli, xiaozu)
,rk_r as (select *,
    rank() over (partition by rank_h.quarter order by rank_h.roi desc) as rank_in_roi
from rank_h)
,ref_rank as (
    select *,
        row_number() over (partition by quarter order by
                case when inc > 0 then 1 else 2 end,
                case when inc > 0 then refd else null end,
                case when inc = 0 and ref = 0 then 1 else 2 end,
                case when inc = 0 and ref < 0 then abs(ref) else null end) as rank_in_ref
    from rk_r
)
,attendance_base as (
    select distinct
        case
        when substring(pg.qici, 1, 6) between '202601' and '202603' then '2026Q1'
        when substring(pg.qici, 1, 6) between '202604' and '202606' then '2026Q2'
        when substring(pg.qici, 1, 6) between '202607' and '202609' then '2026Q3'
        when substring(pg.qici, 1, 6) between '202610' and '202612' then '2026Q4'
        when substring(pg.qici, 1, 6) between '202701' and '202703' then '2027Q1'
        else concat(substring(pg.qici, 1, 4), 'Q',
                    cast((cast(substring(pg.qici, 5, 2) as int) - 1) / 3 + 1 as varchar))
    end as quarter,
        pg.qici,
        pg.employee_email_name
    from temp_table.dingxi01_pingyou_jg pg
    inner join jiagou_zx_active zx
      on zx.employee_email_name = pg.employee_email_name
    where cast(pg.zaizhi as varchar) = '1'
      and pg.is_emp = '是'
      and pg.qici >= '20260320期'
)
,attendance_metric as (
    select
        cp.quarter,
        cp.employee_email_name,
        cp.consultant_period_count,
        pt.total_period_count
    from (
        select
            quarter,
            employee_email_name,
            count(distinct qici) as consultant_period_count
        from attendance_base
        group by quarter, employee_email_name
    ) cp
    left join (
        select
            quarter,
            count(distinct qici) as total_period_count
        from attendance_base
        group by quarter
    ) pt
      on pt.quarter = cp.quarter
)
,final_result as (
    select
        rr.*,
        coalesce(am.consultant_period_count, 0) as consultant_period_count,
        coalesce(am.total_period_count, 0) as total_period_count
    from ref_rank rr
    left join attendance_metric am
      on am.quarter = rr.quarter
     and am.employee_email_name = rr.employee_email_name
)

select
*,
    round(rank_in_roi * 1.0 / nullif(count(*) over (partition by quarter), 0), 5) as rank_position_roi,
    round(rank_in_ref * 1.0 / nullif(count(*) over (partition by quarter), 0), 5) as rank_position_ref,
    case when channel like '%抖音私域%' or channel like '%抖音私信%' then 10 else 0 end as cs_channel_rank,
    case when (channel like '%抖音私域%' or channel like '%抖音私信%') and roi >= 0.8 then 2 else 0 end as cs_80_rank
from final_result
