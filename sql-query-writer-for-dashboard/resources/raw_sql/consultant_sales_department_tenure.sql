with org_t as (
    select
        dep_path,
        email_prefix,
        name,
        min(begin_time) as begin_time,
        max(end_time) as end_time
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
          and array_join(slice(split(path_name, '-'), 1, 4), '-') = '高途-H业务线-市场部-市场顾问部'
    ) t
    group by
        dep_path,
        email_prefix,
        name
),
dd_0 as (
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
        concat(
            date_format(
                date_add(
                    'day',
                    4,
                    date_trunc(
                        'week',
                        date_add('day', -1, cast(trade_time as timestamp))
                    )
                ),
                '%Y%m%d'
            ),
            '期'
        ) as qici,
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
      and concat(
            date_format(
                date_add(
                    'day',
                    4,
                    date_trunc(
                        'week',
                        date_add('day', -1, cast(trade_time as timestamp))
                    )
                ),
                '%Y%m%d'
            ),
            '期'
          ) >= '20260403期'
),
dd as (
    select dd_0.*
    from dd_0
    inner join org_t ot
      on ot.email_prefix = dd_0.email_prefix
    where dd_0.trade_time >= ot.begin_time
      and dd_0.trade_time <= ot.end_time
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
rd_0 as (
    select
        rd.qici,
        rd.name,
        rd.user_id1,
        case
            when rd.trade_status like '%退款%' then '退款'
            when rd.trade_status like '%支付%' then '支付'
            else '未知'
        end as trade_status,
        zz.xiaozu,
        zz.jingli,
        case
            when zz.department like '%西安%' then '西安'
            when zz.department like '%郑州%' then '郑州'
            else '未知'
        end as dept,
        rd.grade_list,
        cast(cast(rd.trade_time as timestamp) as date) as trade_date,
        sum(case when rd.name_total_price >= 0 then rd.name_total_price else 0 end) as income,
        sum(case when rd.name_total_price < 0 then abs(rd.name_total_price) else 0 end) as refund,
        sum(rd.name_total_price) as promit
    from rd
    left join temp_table.dingxi01_jiagou_zx zz
      on zz.employee_email_name = rd.name
    group by
        rd.qici,
        rd.name,
        rd.user_id1,
        case
            when rd.trade_status like '%退款%' then '退款'
            when rd.trade_status like '%支付%' then '支付'
            else '未知'
        end,
        zz.xiaozu,
        zz.jingli,
        case
            when zz.department like '%西安%' then '西安'
            when zz.department like '%郑州%' then '郑州'
            else '未知'
        end,
        rd.grade_list,
        cast(cast(rd.trade_time as timestamp) as date)
),
base_result as (
    select
        qici,
        name,
        xiaozu,
        jingli,
        dept,
        trade_date,
        sum(income) as income,
        sum(refund) as refund,
        sum(promit) as pmit
    from rd_0
    group by
        qici,
        name,
        xiaozu,
        jingli,
        dept,
        trade_date
),
day_rank_raw as (
    select
        qici,
        trade_date,
        dept,
        name,
        xiaozu,
        jingli,
        income,
        refund,
        pmit,
        '天-部门-期次' as day_dept_period_rank_scope,
        row_number() over (
            partition by trade_date, dept, qici
            order by pmit desc, name
        ) as day_dept_period_rank_no,
        lag(pmit) over (
            partition by trade_date, dept, qici
            order by pmit desc, name
        ) as day_previous_pmit
    from base_result
),
day_ranked as (
    select
        qici,
        trade_date,
        dept,
        name,
        xiaozu,
        jingli,
        income,
        refund,
        pmit,
        day_dept_period_rank_scope,
        day_dept_period_rank_no,
        case
            when day_previous_pmit is null then cast(0 as double)
            else day_previous_pmit - pmit
        end as day_dept_period_need_pmit_to_previous
    from day_rank_raw
),
period_agg as (
    select
        qici,
        dept,
        name,
        xiaozu,
        jingli,
        sum(income) as period_income,
        sum(refund) as period_refund,
        sum(pmit) as period_pmit
    from base_result
    group by
        qici,
        dept,
        name,
        xiaozu,
        jingli
),
period_rank_raw as (
    select
        qici,
        dept,
        name,
        xiaozu,
        jingli,
        period_income,
        period_refund,
        period_pmit,
        '期次-部门' as period_dept_rank_scope,
        row_number() over (
            partition by qici, dept
            order by period_pmit desc, name
        ) as period_dept_rank_no,
        lag(period_pmit) over (
            partition by qici, dept
            order by period_pmit desc, name
        ) as period_previous_pmit
    from period_agg
),
period_ranked as (
    select
        qici,
        dept,
        name,
        xiaozu,
        jingli,
        period_income,
        period_refund,
        period_pmit,
        period_dept_rank_scope,
        period_dept_rank_no,
        case
            when period_previous_pmit is null then cast(0 as double)
            else period_previous_pmit - period_pmit
        end as period_dept_need_pmit_to_previous
    from period_rank_raw
)
select
    d.qici,
    d.trade_date,
    d.dept,
    d.name,
    d.xiaozu,
    d.jingli,
    d.income,
    d.refund,
    d.pmit,

    d.day_dept_period_rank_scope,
    d.day_dept_period_rank_no,
    d.day_dept_period_need_pmit_to_previous,

    p.period_dept_rank_scope,
    p.period_dept_rank_no,
    p.period_dept_need_pmit_to_previous,

    p.period_income,
    p.period_refund,
    p.period_pmit
from day_ranked d
left join period_ranked p
  on d.qici = p.qici
 and d.dept = p.dept
 and d.name = p.name
order by
    d.qici,
    d.trade_date,
    d.dept,
    d.day_dept_period_rank_no,
    d.name
