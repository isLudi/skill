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
 			when substr(trade_time, 1, 10) >= '2026-02-25' and substr(trade_time, 1, 10) <= '2026-03-02' then '20260227期'
 			when substr(trade_time, 1, 10) >= '2026-02-17' and substr(trade_time, 1, 10) <= '2026-02-24' then '20260220期'
 			when substr(trade_time, 1, 10) >= '2026-02-09' and substr(trade_time, 1, 10) <= '2026-02-16' then '20260213期'
 			when substr(trade_time, 1, 10) >= '2026-02-03' and substr(trade_time, 1, 10) <= '2026-02-08' then '20260206期'
 			when substr(trade_time, 1, 10) >= '2026-01-27' and substr(trade_time, 1, 10) <= '2026-02-02' then '20260130期'
 			when substr(trade_time, 1, 10) >= '2026-01-20' and substr(trade_time, 1, 10) <= '2026-01-26' then '20260123期'
 		else concat(date_format(date_add('day', 4, date_trunc('week', date_add('day', -1, cast(trade_time as timestamp)))), '%Y%m%d'), '期') end as qici,
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
    where base.qici >= '20260320期'
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
,process as (select
pg.qici, substring(pg.qici, 1, 6) as moth,  pg.employee_email_name,pg.dept,pg.jingli,pg.xiaozu,pg.channel,cast(pg.renchan as decimal) as renchan,pg.grade,pg.is_emp,
sum(name_total_price) as pt,
sum(case when name_total_price >0 then name_total_price else 0 end) as inc,
sum(case when name_total_price <0 then name_total_price else 0 end) as ref
from temp_table.dingxi01_pingyou_jg pg
left join rd on pg.employee_email_name = rd.name and pg.qici = rd.qici
where pg.zaizhi = '1' and pg.is_emp = '是'
and pg.qici >= '20260320期'
group by pg.qici,substring(pg.qici, 1, 6),
pg.employee_email_name,pg.dept,pg.jingli,pg.xiaozu,pg.channel,pg.renchan,pg.grade,pg.is_emp)
,rank as (select *,
round(coalesce(pt/renchan,0),4) as roi,-----净收/人产
round(coalesce(-ref / nullif(inc, 0), 0), 4) as refd,------退费/总营收
case when channel like '%抖音私域%' then 10 else 0 end as ceshi
from process )
,rk_r as (select *,
rank() over (partition by rank.qici order by rank.roi desc) as rank_in_roi
from rank )
,ref_rank as (
    select *,
        row_number() over (partition by qici order by
                case when inc > 0 then 1 else 2 end,
                case when inc > 0 then refd else null end,
                case when inc = 0 and ref = 0 then 1 else 2 end,
                case when inc = 0 and ref < 0 then abs(ref) else null end ) as rank_in_ref
    from rk_r
)
select
*,
    round(rank_in_roi * 1.0 / nullif(count(*) over (partition by qici), 0), 5) as rank_position_roi,
    round(rank_in_ref * 1.0 / nullif(count(*) over (partition by qici), 0), 5) as rank_position_ref,
    case when channel like '%抖音私域%' or channel like '%抖音私信%' then 10 else 0 end as cs_channel_rank,
 	case when (channel like '%抖音私域%' or channel like '%抖音私信%') and roi >= 0.8  then 2 else 0 end as cs_80_rank
from ref_rank;
