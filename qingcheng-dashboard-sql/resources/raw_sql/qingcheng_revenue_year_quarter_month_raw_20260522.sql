---------------伙伴在部门开始时间
with org_t as (select 
dep_path,email_prefix,name,min(begin_time) as begin_time ,max(end_time) as end_time			 
from (
select distinct 
email_prefix,
path_name,
array_join(slice(split(path_name, '-'), 1, 3), '-') as dep_path, 
name,
talent_type_name,
position_name,
source_hr_status,
leave_time,
execute_time,
begin_time,
end_time
from dw.dim_employee_chain
where dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
and array_join(slice(split(path_name, '-'), 1, 3), '-') = '高途-H业务线-青橙项目部')
group by 1,2,3)
--------------------
,dd_0 as (
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
        concat(date_format(date_add('day', 4, date_trunc('week', date_add('day', -1, cast(trade_time as timestamp)))), '%Y%m%d'), '期') as qici,
        leader_employee_email_name, teacher_name,
        case course_term_id 
            when 'C' then '春季' 
            when 'X' then '夏季' 
            when 'Q' then '秋季' 
            when 'D' then '冬季' 
            else '其他'
        end as school_term_id,
        note, course_first_level_department_name,
        course_second_level_department_name,
        course_top_level_department_name
    from finance_dw.app_finance_performance_extend_details_hf 
    where dt = FORMAT_DATETIME(NOW() - INTERVAL '2' HOUR, 'YYYYMMdd')
        and hour = FORMAT_DATETIME(NOW() - INTERVAL '2' HOUR, 'HH')
        and employee_first_level_department_name = 'H业务线'
        and employee_second_level_department_name = '青橙项目部'
        and concat(date_format(date_add('day', 4, date_trunc('week', date_add('day', -1, cast(trade_time as timestamp)))), '%Y%m%d'), '期') >= '20250103期'
)
,dd as (select dd_0.*
from dd_0
left join  org_t ot on ot.name = dd_0.name 
where dd_0.trade_time >= ot.begin_time and dd_0.trade_time <= ot.end_time)
-- 调课调班（按name和user_id1去重，每个用户保留一条记录）
,gmv_t as (
    select 
        id, order_number, clazz_name, user_id1, trade_status, trade_time,  -- 这里加了逗号
        trade_type, email_prefix, name, grade_list, subject, 
        qici, school_term_id, teacher_name,
        course_first_level_department_name,
        course_second_level_department_name,
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
)
-- 正常订单
,gmv_z as (
    select 
        id, order_number, clazz_name, user_id1, trade_status, trade_time,  -- 这里加了逗号
        trade_type, email_prefix, name, grade_list, subject,
        qici, school_term_id, teacher_name,
        course_first_level_department_name,
        course_second_level_department_name,
        sum(price) as name_total_price
    from dd
    where trade_type = '正常订单'
    group by id, order_number, clazz_name, user_id1, trade_status, trade_time,  -- 这里加了逗号
             trade_type, email_prefix, name, grade_list, subject,
             qici, school_term_id, teacher_name,
             course_first_level_department_name,
             course_second_level_department_name
)
-- 整合结果
,rd as (
    select 
        id, order_number, clazz_name, user_id1, trade_status, trade_time,
        trade_type, email_prefix, name, grade_list, subject, 
        qici, school_term_id, teacher_name,
        course_first_level_department_name,
        course_second_level_department_name,
        name_total_price
    from gmv_z
    union all
    select 
        id, order_number, clazz_name, user_id1, trade_status, trade_time,
        trade_type, email_prefix, name, grade_list, subject, 
        qici, school_term_id, teacher_name,
        course_first_level_department_name,
        course_second_level_department_name,
        name_total_price
    from gmv_t
)
---------------------关键条件筛选
,rd_0 as (select 
rd.qici,course_first_level_department_name,course_second_level_department_name,name,user_id1,
case when trade_status like '%退款%' then '退款' when trade_status like '%支付%' then '支付' else '未知' end as trade_status,
zz.leader_employee_email_name,zz.dazhuguan,zz.xuebu,grade_list,-------------------------新增年级字段
date(max(cast(trade_time as timestamp))) as max_trade_date,
cast(year(max(cast(trade_time as timestamp))) as varchar) || '年' as max_year,
'Q' || cast(quarter(max(cast(trade_time as timestamp))) as varchar ) as max_quarter,
cast(month(max(cast(trade_time as timestamp))) as varchar) || '月' as max_month,
sum(case when name_total_price >= 0 then name_total_price else 0 end) as income,
sum(case when name_total_price < 0 then abs(name_total_price) else 0 end) as refund,
sum(name_total_price) as promit,
count(distinct case when subject not in ('选科志愿','定制方案') then subject end) as sub
from rd
left join temp_table.dingxi01_qing_zz zz on zz.employee_email_name = rd.name
group by rd.qici,course_first_level_department_name,course_second_level_department_name,name,user_id1,trade_status,zz.leader_employee_email_name,zz.dazhuguan,zz.xuebu,grade_list)
---------------------------------
,wa as (select *,
case when trade_status = '支付' then sum(sub) else 0 end as p_sub,        
case when trade_status = '退款' and refund > 500 then sum(sub) else 0 end as r_sub
from rd_0
group by 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18
)

-- 最终查询：在这里做聚合
select 
    course_first_level_department_name,
    course_second_level_department_name,
    trade_status,
    leader_employee_email_name,
    dazhuguan,
    xuebu,
	grade_list,
    qici,
    max_trade_date,
    max_year,
    max_quarter,
    max_month, 
    sum(income) as income,
    sum(refund) as refund,
    sum(promit) as promit, 
    sum(p_sub) as p_sub,
    sum(r_sub) as r_sub,
    count(distinct(case when trade_status = '支付' then user_id1 end)) as p_payer,
    count(distinct(case when trade_status = '退款' and refund > 500 then user_id1 end)) as r_payer
from wa
group by 
    qici,grade_list,
    course_first_level_department_name,
    course_second_level_department_name,
    trade_status,
    leader_employee_email_name,
    dazhuguan,
    xuebu,
    max_trade_date,
    max_year,
    max_quarter,
    max_month
