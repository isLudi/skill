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
,order_attr as (
    select distinct
        order_number,
        performance_employee_email_name,
        cast(coalesce(original_order_pay_success_timestamp, pay_success_timestamp, trade_timestamp) as timestamp) as original_paid_time
    from service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf
    where dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
      and hour = format_datetime(now() - interval '2' hour, 'HH')
      and performance_second_level_department_name = '青橙项目部'
      and course_first_level_department_name in ('H业务线', 'LL业务线', 'TUTU', 'TT', 'A业务线', 'EM业务线', 'KA业务线', 'TT业务线', '创新中心')
      and course_second_level_department_name in ('精品班学部', '菁英班学部', '一对一学部', '创新学部', '升学规划中心', '线上考研学部')
)
,team_hist as (
    select distinct
        qici,
        employee_email_name
    from temp_table.dingxi01_qing_team_jg
)
,dd_0 as (
    select
        id,
        order_number,
        sub_biz_number,
        pre_biz_number,
        clazz_name,
        user_id1,
        pre_employee_id,
        type,
        trade_status,
        trade_type,
        paid_time,
        trade_time,
        real_price_0,
        transfer_price,
        price,
        email_prefix,
        name,
        talent_type_name,
        city,
        department,
        biz_number,
        grade_list,
        subject,
        qici,
        leader_employee_email_name,
        teacher_name,
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
            case when trade_status in ('全部退款', '部分退款') then -real_price else real_price end as real_price_0,
            transfer_price,
            price,
            email_prefix,
            employee_email_name as name,
            talent_type_name,
            city_name as city,
            department,
            biz_number,
            course_grade as grade_list,
            case
                when course_subject like '%英语%' or course_subject like '%英文%' then '英语'
                when course_subject like '%语文%' then '语文'
                when course_subject like '%数学%' then '数学'
                when course_subject like '%物理%' then '物理'
                when course_subject like '%化学%' then '化学'
                when course_subject like '%历史%' then '历史'
                when course_subject like '%政治%' then '政治'
                when course_subject like '%生物%' then '生物'
                when course_subject like '%地理%' then '地理'
                when course_subject like '%日语%' then '日语'
                else course_subject
            end as subject,
            concat(date_format(date_trunc('week', cast(trade_time as timestamp) - interval '1' day) + interval '4' day, '%Y%m%d'), '期') as qici,
            leader_employee_email_name,
            teacher_name,
            case course_term_id
                when 'C' then '春季'
                when 'X' then '夏季'
                when 'Q' then '秋季'
                when 'D' then '冬季'
                else '其他'
            end as school_term_id,
            note,
            course_first_level_department_name,
            course_second_level_department_name,
            course_top_level_department_name,
            case when clazz_name like '%试听%' then 0 else 1 end as shiting
        from finance_dw.app_finance_performance_extend_details_hf
        where dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
          and hour = format_datetime(now() - interval '2' hour, 'HH')
          and employee_first_level_department_name = 'H业务线'
          and employee_second_level_department_name = '青橙项目部'
    )
    where qici > '20260424期'
      and shiting = '1'
)
-- 兼顾两类约束：
-- 1. 历史订单在顾问活水进青橙后发生退款，不应计入青橙；
-- 2. 组织链 begin_time 滞后时，当前有效订单不能被误切掉。
,dd as (
    select
        a.*
    from dd_0 a
    left join order_attr oa
        on oa.order_number = a.order_number
       and oa.performance_employee_email_name = a.name
    left join org_t ot
        on ot.name = a.name
    left join team_hist th
        on th.employee_email_name = a.name
       and th.qici = concat(
            date_format(
                date_trunc('week', cast(coalesce(oa.original_paid_time, a.paid_time, a.trade_time) as timestamp) - interval '1' day) + interval '4' day,
                '%Y%m%d'
            ),
            '期'
        )
    where (
        cast(coalesce(oa.original_paid_time, a.paid_time, a.trade_time) as timestamp) >= cast(ot.begin_time as timestamp)
        and (
            ot.end_time is null
            or cast(coalesce(oa.original_paid_time, a.paid_time, a.trade_time) as timestamp) <= cast(ot.end_time as timestamp)
        )
    )
    or th.employee_email_name is not null
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
        course_first_level_department_name,
        course_second_level_department_name,
        sum(price) as name_total_price
    from dd
    where coalesce(trade_type, '') <> '调课调班'
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
        teacher_name,
        course_first_level_department_name,
        course_second_level_department_name
)
-- 整合结果
,rd as (
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
        course_first_level_department_name,
        course_second_level_department_name,
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
        course_first_level_department_name,
        course_second_level_department_name,
        name_total_price
    from gmv_t
)
-----------------退费行课节数
,ord as (
    select
        order_number,
        user_number,
        final_paid_timestamp,
        full_refund_timestamp,
        total_refund_amount,
        talent_type_name,
        employee_email_name,
        email_prefix,
        full_refund_finish_lesson_count,
        full_refund_chain_finish_lesson_count,
        original_order_pay_success_clazz_remain_lesson_count,
        clazz_number,
        clazz_biz_number,
        clazz_name,
        school_year,
        school_term_name,
        school_department_name,
        school_subject_name,
        concat(date_format(date_trunc('week', cast(full_refund_timestamp as timestamp) - interval '1' day) + interval '4' day, '%Y%m%d'), '期') as qici_re,
        case
            when course_category_code = 10 then '公开课'
            when course_category_code = 20 then '体验课'
            when course_category_code = 30 then '专题课'
            when course_category_code = 40 then '系列课'
            else course_category_code
        end as course_category,
        course_first_level_department_name,
        course_second_level_department_name,
        course_third_level_department_name
    from finance_dw.dm_finance_order_refund_detail_df
    where dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
      and course_first_level_department_name = 'H业务线'
      and course_second_level_department_name in ('精品班学部', '菁英班学部', '一对一学部')
      and is_full_refund_order = 1
      and total_refund_amount is not null
      and total_refund_amount <> 0
)
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
        coalesce(order_change.refund_type, '非调课调班') as main_order_change_type,
        case
            -- 只剔除调课调班流水本身；命中课程转移链路的正常订单仍然保留绩效。
            when rd.trade_type = '调课调班'
             and (
                    (
                        coalesce(order_change.has_order_change, 0) = 1
                        and (
                            coalesce(order_change.transfer_in_amount_yuan, 0) > 0
                            or coalesce(order_change.transfer_out_amount_yuan, 0) > 0
                        )
                    )
                    or rd.name_total_price < 0
                 )
            then 1
            else 0
        end as is_internal_order_change
    from rd
    left join re_ke
        on re_ke.qici_re = rd.qici
       and re_ke.order_number = rd.order_number
    left join order_change
        on rd.order_number = order_change.order_number
)
--------------------
,rd_0 as (
    select
        qici,
        course_first_level_department_name,
        course_second_level_department_name,
        name,
        user_id1,
        case
            when trade_status like '%退款%' then '退款'
            when trade_status like '%支付%' then '支付'
            else '未知'
        end as trade_status,
        grade_list,
        sum(
            case
                when is_internal_order_change = 1
                then 0
                when name_total_price >= 0 then name_total_price
                else 0
            end
        ) as income,
        sum(
            case
                when is_internal_order_change = 1
                then 0
                when course_second_level_department_name = '一对一学部'
                 and course_first_level_department_name = 'H业务线'
                then case when name_total_price < 0 then abs(name_total_price) else 0 end
                else case
                    when clazz_name like '%点睛%' and name_total_price < 0 and re_lc < 2 then abs(name_total_price)
                    when (clazz_name not like '%点睛%' or clazz_name is null) and name_total_price < 0 and re_lc < 4 then abs(name_total_price)
                    else 0
                end
            end
        ) as refund_4,
        sum(
            case
                when is_internal_order_change = 1
                then 0
                when name_total_price < 0 then abs(name_total_price)
                else 0
            end
        ) as refund,
        count(distinct case
            when is_internal_order_change = 1
            then null
            when subject not in ('选科志愿', '定制方案') and name_total_price > 0 then subject
        end) as p_sub,
        count(distinct case
            when is_internal_order_change = 1
            then null
            when subject not in ('选科志愿', '定制方案') and name_total_price < 0 then subject
        end) as r_sub
    from t4
    group by
        qici,
        course_first_level_department_name,
        course_second_level_department_name,
        name,
        user_id1,
        case
            when trade_status like '%退款%' then '退款'
            when trade_status like '%支付%' then '支付'
            else '未知'
        end,
        grade_list
)
------------
,wa as (
    select
        qici,
        course_first_level_department_name,
        course_second_level_department_name,
        name,
        user_id1,
        trade_status,
        grade_list,
        income,
        refund_4,
        refund,
        (income - refund_4) as promit_4,
        (income - refund) as promit,
        p_sub as jing_sub
    from rd_0
)
-- 聚合人维度
,renchan as (
    select
        qtg.qici,
        qm.moth,
        qtg.employee_email_name,
        qtg.leader_employee_email_name,
        qtg.dazu,
        qtg.jingli,
        qtg.xuebu,
        sum(case when course_first_level_department_name = 'H业务线' then promit else 0 end) as H_promit,
        sum(case when course_first_level_department_name = 'H业务线' then 0 else promit end) as n_H_promit,
        sum(income) as income,
        sum(refund) as refund,
        sum(promit) as promit,
        count(distinct case when refund > 500 then user_id1 end) as re_payer,
        sum(case when course_first_level_department_name = 'H业务线' and course_second_level_department_name = '一对一学部' then promit_4 else 0 end) as Y_promit_4,
        sum(case when course_first_level_department_name = 'H业务线' and course_second_level_department_name = '一对一学部' then income else 0 end) as Y_income_4,
        sum(case when course_first_level_department_name = 'H业务线' and course_second_level_department_name = '一对一学部' then refund_4 else 0 end) as Y_refund_4,
        sum(case when course_first_level_department_name = 'H业务线' then promit_4 else 0 end) as H_promit_4,
        sum(case when course_first_level_department_name = 'H业务线' then income else 0 end) as H_income_4,
        sum(case when course_first_level_department_name = 'H业务线' then refund_4 else 0 end) as H_refund_4,
        sum(case when course_first_level_department_name = 'H业务线' then 0 else promit_4 end) as n_H_promit_4,
        count(distinct case when refund_4 > 0 then user_id1 end) as re_payer_4,
        count(distinct case when promit > 0 then user_id1 end) as in_payer_4,
        sum(jing_sub) as j_sub
    from (
        select qici, employee_email_name, leader_employee_email_name, dazu, jingli, xuebu,
            row_number() over (partition by qici, employee_email_name order by leader_employee_email_name) as rn
        from temp_table.dingxi01_qing_team_jg
        where leader_employee_email_name is not null
    ) qtg
    left join wa
        on qtg.employee_email_name = wa.name
       and qtg.qici = wa.qici
    left join temp_table.dingxi01_qing_qi_moth qm
        on qm.qici = qtg.qici
    where qtg.rn = 1
    group by
        qtg.qici,
        qm.moth,
        qtg.employee_email_name,
        qtg.leader_employee_email_name,
        qtg.dazu,
        qtg.jingli,
        qtg.xuebu
)
-- 目标字段
,goal_qici as (
    select
        name as employee_email_name,
        qici,
        max(cast(goal as decimal(18, 2))) as qici_goal
    from temp_table.dingxi01_qing_goal
    group by name, qici
)
,goal_moth as (
    select
        month as moth,
        name as employee_email_name,
        sum(cast(goal as decimal(18, 2))) as moth_goal
    from temp_table.dingxi01_qing_goal
    group by month, name
)
,final_base as (
    select
        r.qici,
        r.moth,
        r.employee_email_name as name,
        r.leader_employee_email_name,
        r.dazu,
        r.jingli,
        r.xuebu,
        max(gq.qici_goal) as qici_goal,
        max(gm.moth_goal) as moth_goal,
        coalesce(sum(r.H_promit), 0) as H_promit,
        coalesce(sum(r.n_H_promit), 0) as n_H_promit,
        coalesce(sum(r.income), 0) as income,
        coalesce(sum(r.refund), 0) as refund,
        coalesce(sum(r.promit), 0) as promit,
        coalesce(sum(r.re_payer), 0) as re_payer,
        coalesce(sum(r.in_payer_4), 0) as in_payer_4,
        coalesce(sum(r.j_sub), 0) as j_sub,
        count(distinct case when r.promit > 0 then r.employee_email_name end) as podan,
        coalesce(sum(r.Y_promit_4), 0) as Y_promit_4,
        coalesce(sum(r.H_promit_4), 0) as H_promit_4,
        coalesce(sum(r.Y_income_4), 0) as Y_income_4,
        coalesce(sum(r.H_income_4), 0) as H_income_4,
        coalesce(sum(r.Y_refund_4), 0) as Y_refund_4,
        coalesce(sum(r.H_refund_4), 0) as H_refund_4,
        coalesce(sum(r.n_H_promit_4), 0) as n_H_promit_4
    from renchan r
    left join goal_qici gq
        on gq.qici = r.qici
       and gq.employee_email_name = r.employee_email_name
    left join goal_moth gm
        on gm.moth = r.moth
       and gm.employee_email_name = r.employee_email_name
    group by
        r.qici,
        r.moth,
        r.employee_email_name,
        r.leader_employee_email_name,
        r.dazu,
        r.jingli,
        r.xuebu
)
-- ============================================================
-- 双粒度输出：qici 粒度 + moth 粒度
-- data_level = 'qici' → 期产出单元使用
-- data_level = 'moth' → 月度产出单元使用
-- ============================================================
select
    'qici' as data_level,
    qici,
    moth,
    name,
    leader_employee_email_name,
    dazu,
    jingli,
    xuebu,
    qici_goal,
    case
        when row_number() over (partition by name, moth order by qici) = 1 then moth_goal
        else cast(0 as decimal(18, 2))
    end as moth_goal,
    H_promit,
    n_H_promit,
    income,
    refund,
    promit,
    re_payer,
    in_payer_4,
    j_sub,
    podan,
    Y_promit_4,
    H_promit_4,
    Y_income_4,
    H_income_4,
    Y_refund_4,
    H_refund_4,
    n_H_promit_4
from final_base

union all

select
    'moth' as data_level,
    cast(null as varchar) as qici,
    moth,
    name,
    leader_employee_email_name,
    max(dazu) as dazu,
    max(jingli) as jingli,
    max(xuebu) as xuebu,
    cast(null as decimal(18, 2)) as qici_goal,
    max(moth_goal) as moth_goal,
    sum(H_promit) as H_promit,
    sum(n_H_promit) as n_H_promit,
    sum(income) as income,
    sum(refund) as refund,
    sum(promit) as promit,
    sum(re_payer) as re_payer,
    sum(in_payer_4) as in_payer_4,
    sum(j_sub) as j_sub,
    max(podan) as podan,
    sum(Y_promit_4) as Y_promit_4,
    sum(H_promit_4) as H_promit_4,
    sum(Y_income_4) as Y_income_4,
    sum(H_income_4) as H_income_4,
    sum(Y_refund_4) as Y_refund_4,
    sum(H_refund_4) as H_refund_4,
    sum(n_H_promit_4) as n_H_promit_4
from final_base
group by moth, name, leader_employee_email_name
