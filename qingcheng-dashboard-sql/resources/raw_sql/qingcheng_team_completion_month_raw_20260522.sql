-- 伙伴在部门开始时间
with org_t as (
    select 
        email_prefix,
        name,
        min(begin_time) as begin_time,
        max(end_time) as end_time
    from dw.dim_employee_chain
    where dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
      and path_name like '高途-H业务线-青橙项目部%'
    group by email_prefix, name
)
-- 订单明细
,dd_0 as (
    select
        id,order_number,sub_biz_number,pre_biz_number,clazz_name,
        user_id1,pre_employee_id,type,trade_status,trade_type, paid_time,trade_time,real_price_0,
        transfer_price,price,email_prefix,name,talent_type_name, city,
        department,biz_number,grade_list,subject,qici,
        leader_employee_email_name,teacher_name,
        school_term_id,
        note,
        case
            when course_first_level_department_name is not null then course_first_level_department_name
            when grade_list like '%小学%' or grade_list like '%初%' then '小初业务线'
            else 'H业务线'
        end as course_first_level_department_name,
        case
            when course_second_level_department_name is not null then course_second_level_department_name
            when course_first_level_department_name = 'H业务线' then '精品班学部'
            when course_first_level_department_name is null
             and not (grade_list like '%小学%' or grade_list like '%初%') then '精品班学部'
            else course_second_level_department_name
        end as course_second_level_department_name,
        course_top_level_department_name
from (
    select
        id,order_number,substring(biz_number, 1, 10) as sub_biz_number,pre_biz_number,clazz_name,
        user_id as user_id1,pre_employee_id,type,trade_status,trade_type, order_paid_time as paid_time,trade_time,
        case when trade_status in ('全部退款', '部分退款') then -real_price else real_price end as real_price_0,
        transfer_price,price,email_prefix,employee_email_name as name,talent_type_name, city_name as city,
        department,biz_number,course_grade as grade_list,
	    case when course_subject like '%英语%' or course_subject like '%英文%' then '英语' 
	           when course_subject like '%语文%'  then '语文'  when course_subject like '%数学%'  then '数学' 
	           when course_subject like '%物理%'  then '物理' when course_subject like '%化学%'  then '化学'
	           when course_subject like '%历史%'  then '历史' when course_subject like '%政治%'  then '政治'
	           when course_subject like '%生物%'  then '生物' when course_subject like '%地理%'  then '地理'
	           when course_subject like '%日语%'  then '日语' else course_subject end 
	     as subject,
        concat(date_format(date_trunc('week', cast(trade_time as timestamp) - interval '1' day) + interval '4' day, '%Y%m%d'), '期') as qici,
        leader_employee_email_name,teacher_name,
        case course_term_id when 'C' then '春季' when 'X' then '夏季' when 'Q' then '秋季' when 'D' then '冬季' else '其他'end as school_term_id,
        note,course_first_level_department_name,course_second_level_department_name,course_top_level_department_name,
	case when clazz_name like '%试听%' then 0 else 1 end as shiting
    from finance_dw.app_finance_performance_extend_details_hf 
    where dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
      and hour = format_datetime(now() - interval '2' hour, 'HH')
      and employee_first_level_department_name = 'H业务线'
      and employee_second_level_department_name = '青橙项目部')
where qici > '20260424期' 
		  and shiting = '1'
)
-- 只查询员工在当前部门期间产生的营收和退费
,dd as (
    select 
        a.*
    from dd_0 a
    inner join org_t ot 
        on ot.name = a.name 
        and cast(coalesce(a.paid_time, a.trade_time) as timestamp) >= cast(ot.begin_time as timestamp)
        and (
            ot.end_time is null
            or cast(coalesce(a.paid_time, a.trade_time) as timestamp) <= cast(ot.end_time as timestamp)
        )
)
-- 调课调班（按订单/课程维度汇总，避免把同一顾问同一用户的多笔调课调班揉成一条）
,gmv_t as (
    select
        min(id) as id,
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
        course_first_level_department_name,
        course_second_level_department_name,
        round(sum(price), 3) as name_total_price
    from dd
    where trade_type = '调课调班'
    group by
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
        course_first_level_department_name,
        course_second_level_department_name
    having abs(round(sum(price), 3)) > 0.001
)
-- 正常订单
,gmv_z as (
    select 
        id,order_number,clazz_name,user_id1,
        trade_status,trade_time,
        trade_type,
        email_prefix,
        name,
        grade_list,
        subject,
        qici,
        school_term_id,teacher_name,
        course_first_level_department_name,course_second_level_department_name,
        sum(price) as name_total_price
    from dd
    where trade_type = '正常订单'
    group by id,order_number,clazz_name,user_id1,trade_status,trade_time,
             trade_type,email_prefix,name,grade_list,subject,
             qici,school_term_id,teacher_name,
             course_first_level_department_name,course_second_level_department_name
)
-- 整合结果
,rd as (
    select 
        id, order_number, clazz_name, user_id1, trade_status, trade_time,
        trade_type, email_prefix, name, grade_list, subject, 
        qici, school_term_id, teacher_name,
        course_first_level_department_name, course_second_level_department_name,
        name_total_price
    from gmv_z
    union all
    select 
        id, order_number, clazz_name, user_id1, trade_status, trade_time,
        trade_type, email_prefix, name, grade_list, subject, 
        qici, school_term_id, teacher_name,
        course_first_level_department_name, course_second_level_department_name,
        name_total_price
    from gmv_t
)
-----------------退费行课节数
,ord as (
	SELECT
          order_number,user_number,final_paid_timestamp,full_refund_timestamp,total_refund_amount,talent_type_name,
          employee_email_name,email_prefix,
		  full_refund_finish_lesson_count,-----完全退款时已完课课节数(直播课，不包含类直播赠课)
          full_refund_chain_finish_lesson_count,---完全退款时调课链路总完课课节数
		  original_order_pay_success_clazz_remain_lesson_count,-----原始父订单下单时剩余课节数
          clazz_number,clazz_biz_number,clazz_name,school_year,school_term_name,school_department_name,school_subject_name,
		concat(date_format(date_trunc('week', cast(full_refund_timestamp as timestamp) - interval '1' day) + interval '4' day, '%Y%m%d'), '期') as qici_re,
          CASE
            WHEN course_category_code = 10 THEN '公开课'
            WHEN course_category_code = 20 THEN '体验课'
            WHEN course_category_code = 30 THEN '专题课'
            WHEN course_category_code = 40 THEN '系列课'
            ELSE course_category_code
          END AS course_category,
          course_first_level_department_name,course_second_level_department_name,course_third_level_department_name
        FROM
          finance_dw.dm_finance_order_refund_detail_df
        WHERE dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
          AND course_first_level_department_name = 'H业务线'
		  and course_second_level_department_name in ( '精品班学部','菁英班学部','一对一学部')
          AND is_full_refund_order = 1------------------是否全部退款
          AND total_refund_amount IS NOT NULL
          AND total_refund_amount <> 0)
--------------调课调班/课程转移主链路
,order_change_raw as (
    select
        order_number,
        parent_order_number,
        original_order_number,
        latest_child_order_number,
        case
            when order_change_type = 0 then '调课调班'
            when order_change_type = 1 then '课程转移'
            else cast(order_change_type as varchar)
        end as refund_type,
        case when cast(is_orginal_order as varchar) = '1' then 1 else 0 end as is_original_order,
        case when cast(is_orginal_order as varchar) = '0' then 1 else 0 end as is_child_order,
        cast(coalesce(transfer_in_amount, 0) as double) / 100.0 as transfer_in_amount_yuan,
        cast(coalesce(transfer_out_amount, 0) as double) / 100.0 as transfer_out_amount_yuan
    from finance_dw.dim_finance_order_change_df
    where dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
      and latest_child_order_status in (2, 6, 7)
      and biz_type in (2, 7)
)
,order_change_order_map as (
    select order_number as join_order_number, refund_type, is_original_order, is_child_order, transfer_in_amount_yuan, transfer_out_amount_yuan
    from order_change_raw
    where order_number is not null
    union all
    select parent_order_number as join_order_number, refund_type, is_original_order, is_child_order, transfer_in_amount_yuan, transfer_out_amount_yuan
    from order_change_raw
    where parent_order_number is not null
    union all
    select original_order_number as join_order_number, refund_type, is_original_order, is_child_order, transfer_in_amount_yuan, transfer_out_amount_yuan
    from order_change_raw
    where original_order_number is not null
    union all
    select latest_child_order_number as join_order_number, refund_type, is_original_order, is_child_order, transfer_in_amount_yuan, transfer_out_amount_yuan
    from order_change_raw
    where latest_child_order_number is not null
)
,order_change as (
    select
        join_order_number as order_number,
        1 as has_order_change,
        max(is_original_order) as is_original_order,
        max(is_child_order) as is_child_order,
        max(transfer_in_amount_yuan) as transfer_in_amount_yuan,
        max(transfer_out_amount_yuan) as transfer_out_amount_yuan,
        array_join(array_distinct(array_agg(coalesce(refund_type, '未知'))), ',') as refund_type
    from order_change_order_map
    group by join_order_number
)
---------------合并退费行课节数
,re_ke as (
    select
        ord.qici_re,
        ord.order_number,
        max(ord.full_refund_chain_finish_lesson_count) as full_refund_chain_finish_lesson_count,
        array_join(array_distinct(array_agg(coalesce(order_change.refund_type, '非调课调班'))), ',') as refund_type
    from ord
    left join order_change
        on ord.order_number = order_change.order_number
    group by
        ord.qici_re,
        ord.order_number
)
------------------------连接各订单退费行课节数和主交易调课调班链路
,t4 as (
    select
        rd.*,
        coalesce(re_ke.full_refund_chain_finish_lesson_count, 0) as re_lc,
        coalesce(order_change.has_order_change, 0) as main_has_order_change,
        coalesce(order_change.is_original_order, 0) as main_is_original_order,
        coalesce(order_change.is_child_order, 0) as main_is_child_order,
        coalesce(order_change.transfer_in_amount_yuan, 0) as main_transfer_in_amount_yuan,
        coalesce(order_change.transfer_out_amount_yuan, 0) as main_transfer_out_amount_yuan,
        coalesce(order_change.refund_type, '非调课调班') as main_order_change_type
    from rd
    left join re_ke on re_ke.qici_re = rd.qici and re_ke.order_number = rd.order_number
    left join order_change on rd.order_number = order_change.order_number
)
--------------------
,rd_0 as (
    select 
        qici,
        course_first_level_department_name,
        course_second_level_department_name,
        name,
        user_id1,
        case when trade_status like '%退款%' then '退款' when trade_status like '%支付%' then '支付' else '未知' end as trade_status,
        grade_list,
        sum(
            case
                when main_has_order_change = 1
                 and trade_type = '调课调班'
                 and (main_transfer_in_amount_yuan > 0 or main_transfer_out_amount_yuan > 0)
                then 0
                when name_total_price >= 0 then name_total_price
                else 0
            end
        ) as income,
sum(
    case 
        when main_has_order_change = 1
         and trade_type = '调课调班'
         and (main_transfer_in_amount_yuan > 0 or main_transfer_out_amount_yuan > 0)
        then 0
        when course_second_level_department_name = '一对一学部' and course_first_level_department_name = 'H业务线' 
        then case when name_total_price < 0 then abs(name_total_price) else 0 end ---------一对一
        else 
	case when clazz_name like '%点睛%' and name_total_price < 0 and re_lc < 2 then abs(name_total_price) when (clazz_name not like '%点睛%' or clazz_name is null) and name_total_price < 0 and re_lc < 4 then abs(name_total_price) else 0 end-------------班课
    end ) as refund_4,----行课退费4
	    sum(
            case
                when main_has_order_change = 1
                 and trade_type = '调课调班'
                 and (main_transfer_in_amount_yuan > 0 or main_transfer_out_amount_yuan > 0)
                then 0
                when name_total_price < 0 then abs(name_total_price)
                else 0
            end
        ) as refund,---全部退费
        count(distinct case
            when main_has_order_change = 1
             and trade_type = '调课调班'
             and (main_transfer_in_amount_yuan > 0 or main_transfer_out_amount_yuan > 0)
            then null
            when subject not in ('选科志愿','定制方案') then subject
        end) as sub
    from t4
    group by qici,course_first_level_department_name,course_second_level_department_name,name,user_id1,
             case when trade_status like '%退款%' then '退款' when trade_status like '%支付%' then '支付' else '未知' end,
             grade_list
)
------------
,wa as (
    select  
        rd_0.qici, qm.moth,
        course_first_level_department_name,
        course_second_level_department_name,
        name,
        user_id1,
        trade_status,
        grade_list,
        income,
        refund_4,
	    refund,
        (income - refund_4) as promit_4,----剔除行课4节课退费净收
	    (income - refund) as promit
    from rd_0
	left join temp_table.dingxi01_qing_qi_moth qm on qm.qici = rd_0.qici
)
-- 聚合人维度
,renchan as (
    select 
        qici,moth,
        name,qtg.leader_employee_email_name,
        sum(case when course_first_level_department_name = 'H业务线' then promit else 0 end) as H_promit,------H业绩不剔除退4
        sum(case when course_first_level_department_name != 'H业务线' then promit_4 else 0 end) as n_H_promit,---非H
        sum(income) as income,
        sum(refund) as refund,
        sum(promit) as promit, 
        count(distinct case when refund > 0 then user_id1 end) as re_payer,----退费人数
	----------------------剔除退费4
sum(case when course_first_level_department_name = 'H业务线' and course_second_level_department_name = '一对一学部' then promit_4 else 0 end) as Y_promit_4,------一对一 净收 
sum(case when course_first_level_department_name = 'H业务线' and course_second_level_department_name = '一对一学部' then income else 0 end) as Y_income_4,-------一对一 营收 
sum(case when course_first_level_department_name = 'H业务线' and course_second_level_department_name = '一对一学部' then refund_4 else 0 end) as Y_refund_4,-------一对一 退费 
	    sum(case when course_first_level_department_name = 'H业务线' then promit_4 else 0 end) as H_promit_4,------H业绩不剔除退4
        sum(case when course_first_level_department_name != 'H业务线' then promit_4 else 0 end) as n_H_promit_4,---非H
        sum(refund_4) as refund_4,
        sum(promit_4) as promit_4, 
        count(distinct case when refund_4 > 500 then user_id1 end) as re_payer_4
    from wa
		left join 
	(select distinct employee_email_name,leader_employee_email_name
	 from temp_table.dingxi01_qing_team_jg
	where qici = (select max(qici) from temp_table.dingxi01_qing_team_jg)
	) qtg on qtg.employee_email_name = wa.name
	where qtg.leader_employee_email_name is not null
    group by qici,moth,name,qtg.leader_employee_email_name
)
-- 架构+目标
select *, case when xiaozu1 != '-' then xiaozu1 else '-' end as xiaozu
from (
   select 
	    qg.month,qg.xuebu,xiaozu as xiaozu1,qg.dazu,cast(qg.emye_c as decimal) as emye_c,cast(qg.goal as decimal) as goal,
	    coalesce(sum(H_promit),0) as H_promit,
        coalesce(sum(n_H_promit),0) as n_H_promit,
        coalesce(sum(income),0) as income,
        coalesce(sum(refund),0) as refund,
        coalesce(sum(promit),0) as promit, 
        coalesce(sum(re_payer),0) as re_payer,
		count(distinct case when promit > 0 then name end) as podan,
		---------------------退4
	    coalesce(sum(Y_promit_4),0) as Y_promit_4,-------H一对一净收
		 coalesce(sum(Y_income_4),0) as Y_income_4,-------H一对一营收
		 coalesce(sum(H_promit_4),0) as H_promit_4,
        coalesce(sum(n_H_promit_4),0) as n_H_promit_4,
        coalesce(sum(refund_4),0) as refund_4,
        coalesce(sum(promit_4),0) as promit_4, 
        coalesce(sum(re_payer_4),0) as re_payer_4,
        count(distinct case when promit > 0 then name end) as podan_4
    from temp_table.dingxi01_qing_team_goal qg 
    left join renchan rc on qg.xiaozu = rc.leader_employee_email_name and qg.month = rc.moth
group by qg.month,qg.xuebu,qg.xiaozu,qg.dazu,leader_employee_email_name,qg.emye_c,qg.goal)
