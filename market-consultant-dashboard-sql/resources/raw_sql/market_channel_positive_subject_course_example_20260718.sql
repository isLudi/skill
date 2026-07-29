with lead_raw as (
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
        t.rule_name,
        concat('2026', substr(t.rule_name, 1, 4), '期') as rule_period_name,
        case
            when concat('2026', substr(t.rule_name, 1, 4), '期') = concat(
                date_format(
                    date_trunc(
                        'week',
                        date_parse(replace(concat(t.group_period_year, t.group_period_term), '期', ''), '%Y%m%d') - interval '1' day
                    ) + interval '4' day,
                    '%Y%m%d'
                ),
                '期'
            ) then '是'
            else '否'
        end as period_match_flag,
        case
            when t.rule_name like '%高一%' then '高一'
            when t.rule_name like '%高二%' then '高二'
            when t.rule_name like '%高三%' then '高三'
            when t.rule_name like '%初一%' then '初一'
            when t.rule_name like '%初二%' then '初二'
            when t.rule_name like '%初三%' then '初三'
            else coalesce(t.lead_purchase_intention_level2_category_name, '未知')
        end as grade_name,
        coalesce(t.virtual_leader_email_name, '未知') as manager_name,
        t.user_id,
        coalesce(t.lead_count, 0) as lead_count,
        coalesce(t.conversion_lead_count, 0) as regular_course_user_count,
        coalesce(t.subject_count, 0) as pay_subject_person_count,
        coalesce(t.order_count, 0) as regular_course_order_count,
        coalesce((t.income_amount - t.in_pay_period_refund_amount - t.non_pay_period_refund_amount) / 100.0, 0) as net_income
    from bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df t
    where t.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
      and t.hour = format_datetime(now() - interval '3' hour, 'HH')
      and t.section_assign_employee_first_level_department_name = 'H业务线'
      and t.section_assign_employee_second_level_department_name = '市场部'
      and t.section_assign_employee_third_level_department_name = '市场顾问部'
      and t.virtual_third_department_name = '市场顾问部'
      and (
            t.period_mapping_first_level_department_name = 'H业务线'
         or t.period_mapping_first_level_department_name is null
      )
      and (
            t.period_mapping_second_level_department_name in ('市场部', '精品班学部')
         or t.period_mapping_second_level_department_name is null
      )
      and t.rule_name in (
          '0703期-西安直播江苏-西安直播江苏-高一',
          '0626期-西安直播江苏-西安直播江苏-高一'
      )
),
lead_user_base as (
    select
        period_name,
        rule_name,
        rule_period_name,
        period_match_flag,
        rule_name as channel_name,
        grade_name,
        manager_name,
        user_id,
        sum(lead_count) as lead_count,
        sum(regular_course_user_count) as regular_course_user_count,
        sum(pay_subject_person_count) as pay_subject_person_count,
        sum(regular_course_order_count) as regular_course_order_count,
        sum(net_income) as net_income
    from lead_raw
    group by
        period_name,
        rule_name,
        rule_period_name,
        period_match_flag,
        grade_name,
        manager_name,
        user_id
),
positive_users as (
    select
        period_name,
        rule_name,
        rule_period_name,
        period_match_flag,
        channel_name,
        grade_name,
        manager_name,
        user_id,
        lead_count,
        regular_course_user_count,
        pay_subject_person_count,
        regular_course_order_count,
        net_income
    from lead_user_base
    where regular_course_user_count > 0
      and period_match_flag = '是'
),
finance_order_raw as (
    select
        d.qici as period_name,
        d.user_id,
        d.order_course_type,
        d.course_second_level_department_name,
        d.course_third_level_department_name,
        d.course_department,
        d.jiangsu_version_flag,
        d.order_course_name,
        d.order_class_name,
        d.order_subclazz_name,
        d.subject,
        d.order_number,
        d.subject_amount
    from (
        select
            case
                when day_of_week(date_parse(substr(f.trade_time, 1, 10), '%Y-%m-%d')) = 1
                    then concat(date_format(date_trunc('week', date_parse(substr(f.trade_time, 1, 10), '%Y-%m-%d')) - interval '3' day, '%Y%m%d'), '期')
                else concat(date_format(date_trunc('week', date_parse(substr(f.trade_time, 1, 10), '%Y-%m-%d')) + interval '4' day, '%Y%m%d'), '期')
            end as qici,
            f.user_id,
            f.order_number,
            case
                when f.course_second_level_department_name = '本地化大班学部' then '本地化学部'
                when f.course_second_level_department_name = '精品班学部' then '精品班大班课'
                else coalesce(f.course_second_level_department_name, '其他')
            end as order_course_type,
            coalesce(f.course_second_level_department_name, '未知') as course_second_level_department_name,
            coalesce(f.course_third_level_department_name, '未知') as course_third_level_department_name,
            coalesce(f.course_department, '未知') as course_department,
            case
                when coalesce(f.course_name, '') like '%江苏专版%'
                  or coalesce(f.clazz_name, '') like '%江苏专版%'
                  or coalesce(f.subclazz_name, '') like '%江苏专版%'
                    then '江苏专版订单'
                else '非江苏专版订单'
            end as jiangsu_version_flag,
            coalesce(f.course_name, '未知') as order_course_name,
            coalesce(f.clazz_name, '未知') as order_class_name,
            coalesce(f.subclazz_name, '未知') as order_subclazz_name,
            case
                when f.course_subject like '%英语%' or f.course_subject like '%英文%' then '英语'
                when f.course_subject like '%语文%' then '语文'
                when f.course_subject like '%数学%' then '数学'
                when f.course_subject like '%物理%' then '物理'
                when f.course_subject like '%化学%' then '化学'
                when f.course_subject like '%历史%' then '历史'
                when f.course_subject like '%政治%' then '政治'
                when f.course_subject like '%生物%' then '生物'
                when f.course_subject like '%地理%' then '地理'
                when f.course_subject like '%日语%' then '日语'
                when f.course_subject like '%学习分享%' then '学习分享'
                when f.course_subject like '%定制方案%' then '定制方案'
                else coalesce(f.course_subject, '其他')
            end as subject,
            f.price as subject_amount
        from finance_dw.app_finance_performance_extend_details_hf f
        where f.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
          and f.hour = format_datetime(now() - interval '2' hour, 'HH')
          and f.employee_first_level_department_name = 'H业务线'
          and f.employee_second_level_department_name = '市场部'
          and f.employee_third_level_department_name = '市场顾问部'
          and f.course_first_level_department_name = 'H业务线'
          and f.course_second_level_department_name in ('精品班学部', '本地化大班学部')
          and f.real_price <> 0
          and f.trade_type in ('正常订单', '调课调班')
    ) d
    where d.qici in ('20260626期', '20260703期')
),
finance_user_subject as (
    select
        period_name,
        user_id,
        order_course_type,
        course_second_level_department_name,
        course_third_level_department_name,
        course_department,
        jiangsu_version_flag,
        order_course_name,
        order_class_name,
        order_subclazz_name,
        subject,
        count(distinct order_number) as subject_order_count,
        sum(subject_amount) as subject_amount
    from finance_order_raw
    group by
        period_name,
        user_id,
        order_course_type,
        course_second_level_department_name,
        course_third_level_department_name,
        course_department,
        jiangsu_version_flag,
        order_course_name,
        order_class_name,
        order_subclazz_name,
        subject
),
positive_user_subject as (
    select
        pu.period_name,
        pu.rule_name,
        pu.rule_period_name,
        pu.period_match_flag,
        pu.channel_name,
        pu.grade_name,
        pu.manager_name,
        pu.user_id,
        coalesce(fs.order_course_type, '未匹配到财务订单') as order_course_type,
        coalesce(fs.course_second_level_department_name, '未匹配到财务订单') as course_second_level_department_name,
        coalesce(fs.course_third_level_department_name, '未匹配到财务订单') as course_third_level_department_name,
        coalesce(fs.course_department, '未匹配到财务订单') as course_department,
        coalesce(fs.jiangsu_version_flag, '未匹配到财务订单') as jiangsu_version_flag,
        coalesce(fs.order_course_name, '未匹配到财务订单') as order_course_name,
        coalesce(fs.order_class_name, '未匹配到财务订单') as order_class_name,
        coalesce(fs.order_subclazz_name, '未匹配到财务订单') as order_subclazz_name,
        coalesce(fs.subject, '未匹配到财务科目') as subject,
        coalesce(fs.subject_order_count, 0) as subject_order_count,
        coalesce(fs.subject_amount, 0) as subject_amount,
        pu.lead_count,
        pu.regular_course_user_count,
        pu.pay_subject_person_count,
        pu.regular_course_order_count,
        pu.net_income
    from positive_users pu
    left join finance_user_subject fs
        on fs.period_name = pu.period_name
       and fs.user_id = pu.user_id
),
total_agg as (
    select
        period_name,
        rule_name,
        rule_period_name,
        period_match_flag,
        channel_name,
        grade_name,
        manager_name,
        order_course_type,
        course_second_level_department_name,
        course_third_level_department_name,
        course_department,
        jiangsu_version_flag,
        order_course_name,
        order_class_name,
        order_subclazz_name,
        count(distinct user_id) as total_positive_user_den,
        count(distinct concat(cast(user_id as varchar), '#', subject)) as total_subject_person_den,
        sum(subject_amount) as total_subject_amount_den
    from positive_user_subject
    group by
        period_name,
        rule_name,
        rule_period_name,
        period_match_flag,
        channel_name,
        grade_name,
        manager_name,
        order_course_type,
        course_second_level_department_name,
        course_third_level_department_name,
        course_department,
        jiangsu_version_flag,
        order_course_name,
        order_class_name,
        order_subclazz_name
)
select
    pus.period_name,
    pus.rule_name,
    pus.rule_period_name,
    pus.period_match_flag,
    pus.channel_name,
    pus.grade_name,
    pus.manager_name,
    pus.user_id,
    pus.order_course_type,
    pus.course_second_level_department_name,
    pus.course_third_level_department_name,
    pus.course_department,
    pus.jiangsu_version_flag,
    pus.order_course_name,
    pus.order_class_name,
    pus.order_subclazz_name,
    pus.subject,
    1 as subject_user_count_num,
    ta.total_positive_user_den,
    1 as subject_person_count_num,
    ta.total_subject_person_den,
    pus.subject_amount as subject_amount_num,
    ta.total_subject_amount_den,
    pus.subject_order_count,
    pus.lead_count,
    pus.regular_course_user_count,
    pus.pay_subject_person_count,
    pus.regular_course_order_count,
    pus.net_income
from positive_user_subject pus
left join total_agg ta
    on ta.period_name = pus.period_name
   and ta.rule_name = pus.rule_name
   and ta.rule_period_name = pus.rule_period_name
   and ta.period_match_flag = pus.period_match_flag
   and ta.channel_name = pus.channel_name
   and ta.grade_name = pus.grade_name
   and ta.manager_name = pus.manager_name
   and ta.order_course_type = pus.order_course_type
   and ta.course_second_level_department_name = pus.course_second_level_department_name
   and ta.course_third_level_department_name = pus.course_third_level_department_name
   and ta.course_department = pus.course_department
   and ta.jiangsu_version_flag = pus.jiangsu_version_flag
   and ta.order_course_name = pus.order_course_name
   and ta.order_class_name = pus.order_class_name
   and ta.order_subclazz_name = pus.order_subclazz_name
order by
    pus.period_name,
    pus.rule_name,
    pus.rule_period_name,
    pus.period_match_flag,
    pus.grade_name,
    pus.manager_name,
    pus.user_id,
    pus.order_course_type,
    pus.jiangsu_version_flag,
    pus.order_course_name,
    pus.order_class_name,
    pus.subject
