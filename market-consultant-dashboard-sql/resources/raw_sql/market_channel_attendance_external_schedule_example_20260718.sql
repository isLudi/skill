with data as (
    select distinct
        cast(f.lead_id as varchar) as lead_id,
        cast(f.user_id as varchar) as user_id,
        cast(f.employee_email_prefix as varchar) as employee_email_prefix,
        cast(f.employee_email_name as varchar) as employee_email_name,
        cast(f.rule_name as varchar) as rule_name,
        concat(cast(date_format(date_trunc('week', date_parse(replace(concat(f.group_period_year, f.group_period_term), '期', ''), '%Y%m%d') - interval '1' day) + interval '4' day, '%Y%m%d') as varchar), '期') as qici,
        '陈瑞春' as channel_map_1,
        case
            when f.rule_name like '%高二%' then '高二'
            when f.rule_name like '%高三%' then '高三'
            else f.lead_purchase_intention_level2_category_name
        end as grade_1
    from bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df f
    where f.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
      and f.hour = format_datetime(now() - interval '3' hour, 'HH')
      and f.section_assign_employee_first_level_department_name = 'H业务线'
      and f.section_assign_employee_second_level_department_name = '精品班学部'
      and f.period_mapping_first_level_department_name = 'H业务线'
      and cast(f.valid_lead_count as varchar) = '1'
      and concat(cast(date_format(date_trunc('week', date_parse(replace(concat(f.group_period_year, f.group_period_term), '期', ''), '%Y%m%d') - interval '1' day) + interval '4' day, '%Y%m%d') as varchar), '期') in ('20260619期', '20260626期', '20260703期', '20260710期')
      and (
          (
              f.third_department_name = '直播部'
              and (
                  f.sku_id_name like '%春春%'
                  or f.sku_id_name like '%瑞春%'
                  or f.rule_name like '%春春%'
                  or f.rule_name like '%瑞春%'
              )
          )
          or (
              f.source_manager_name = '刘福云'
              and (
                  f.sku_id_name like '%春春%'
                  or f.sku_id_name like '%瑞春%'
              )
          )
      )
      and (
          f.rule_name like '%高二%'
          or f.rule_name like '%高三%'
          or f.lead_purchase_intention_level2_category_name in ('高二', '高三')
      )
),
schedule as (
    select '陈瑞春' as channel_map_1, timestamp '2026-06-19 18:20:00' as begin_time_slot, '20260619期' as qici, '高三' as grade_1, '1' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-06-19 19:40:00' as begin_time_slot, '20260619期' as qici, '高三' as grade_1, '2' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-06-20 18:20:00' as begin_time_slot, '20260619期' as qici, '高三' as grade_1, '3' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-06-20 19:40:00' as begin_time_slot, '20260619期' as qici, '高三' as grade_1, '4' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-06-21 15:30:00' as begin_time_slot, '20260619期' as qici, '高三' as grade_1, '5' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-06-21 18:20:00' as begin_time_slot, '20260619期' as qici, '高三' as grade_1, '6' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-06-19 18:20:00' as begin_time_slot, '20260619期' as qici, '高二' as grade_1, '1' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-06-19 19:40:00' as begin_time_slot, '20260619期' as qici, '高二' as grade_1, '2' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-06-20 18:20:00' as begin_time_slot, '20260619期' as qici, '高二' as grade_1, '3' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-06-20 19:40:00' as begin_time_slot, '20260619期' as qici, '高二' as grade_1, '4' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-06-21 15:30:00' as begin_time_slot, '20260619期' as qici, '高二' as grade_1, '5' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-06-21 18:20:00' as begin_time_slot, '20260619期' as qici, '高二' as grade_1, '6' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-06-26 18:20:00' as begin_time_slot, '20260626期' as qici, '高三' as grade_1, '1' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-06-26 19:40:00' as begin_time_slot, '20260626期' as qici, '高三' as grade_1, '2' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-06-27 18:20:00' as begin_time_slot, '20260626期' as qici, '高三' as grade_1, '3' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-06-27 19:40:00' as begin_time_slot, '20260626期' as qici, '高三' as grade_1, '4' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-06-28 15:30:00' as begin_time_slot, '20260626期' as qici, '高三' as grade_1, '5' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-06-28 18:20:00' as begin_time_slot, '20260626期' as qici, '高三' as grade_1, '6' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-06-26 18:20:00' as begin_time_slot, '20260626期' as qici, '高二' as grade_1, '1' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-06-26 19:40:00' as begin_time_slot, '20260626期' as qici, '高二' as grade_1, '2' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-06-27 18:20:00' as begin_time_slot, '20260626期' as qici, '高二' as grade_1, '3' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-06-27 19:40:00' as begin_time_slot, '20260626期' as qici, '高二' as grade_1, '4' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-06-28 15:30:00' as begin_time_slot, '20260626期' as qici, '高二' as grade_1, '5' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-06-28 18:20:00' as begin_time_slot, '20260626期' as qici, '高二' as grade_1, '6' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-07-03 18:20:00' as begin_time_slot, '20260703期' as qici, '高三' as grade_1, '1' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-07-03 19:40:00' as begin_time_slot, '20260703期' as qici, '高三' as grade_1, '2' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-07-04 18:20:00' as begin_time_slot, '20260703期' as qici, '高三' as grade_1, '3' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-07-04 19:40:00' as begin_time_slot, '20260703期' as qici, '高三' as grade_1, '4' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-07-05 15:30:00' as begin_time_slot, '20260703期' as qici, '高三' as grade_1, '5' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-07-05 18:20:00' as begin_time_slot, '20260703期' as qici, '高三' as grade_1, '6' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-07-03 18:20:00' as begin_time_slot, '20260703期' as qici, '高二' as grade_1, '1' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-07-03 19:40:00' as begin_time_slot, '20260703期' as qici, '高二' as grade_1, '2' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-07-04 18:20:00' as begin_time_slot, '20260703期' as qici, '高二' as grade_1, '3' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-07-04 19:40:00' as begin_time_slot, '20260703期' as qici, '高二' as grade_1, '4' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-07-05 15:30:00' as begin_time_slot, '20260703期' as qici, '高二' as grade_1, '5' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-07-05 18:20:00' as begin_time_slot, '20260703期' as qici, '高二' as grade_1, '6' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-07-10 18:20:00' as begin_time_slot, '20260710期' as qici, '高三' as grade_1, '1' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-07-10 19:40:00' as begin_time_slot, '20260710期' as qici, '高三' as grade_1, '2' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-07-11 18:20:00' as begin_time_slot, '20260710期' as qici, '高三' as grade_1, '3' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-07-11 19:40:00' as begin_time_slot, '20260710期' as qici, '高三' as grade_1, '4' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-07-12 15:30:00' as begin_time_slot, '20260710期' as qici, '高三' as grade_1, '5' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-07-12 18:20:00' as begin_time_slot, '20260710期' as qici, '高三' as grade_1, '6' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-07-10 18:20:00' as begin_time_slot, '20260710期' as qici, '高二' as grade_1, '1' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-07-10 19:40:00' as begin_time_slot, '20260710期' as qici, '高二' as grade_1, '2' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-07-11 18:20:00' as begin_time_slot, '20260710期' as qici, '高二' as grade_1, '3' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-07-11 19:40:00' as begin_time_slot, '20260710期' as qici, '高二' as grade_1, '4' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-07-12 15:30:00' as begin_time_slot, '20260710期' as qici, '高二' as grade_1, '5' as lesson_no
    union all
    select '陈瑞春' as channel_map_1, timestamp '2026-07-12 18:20:00' as begin_time_slot, '20260710期' as qici, '高二' as grade_1, '6' as lesson_no
),
schedule_times as (
    select distinct begin_time_slot
    from schedule
),
lead_base as (
    select
        d.qici,
        d.channel_map_1,
        d.rule_name,
        d.grade_1,
        cast(d.lead_id as varchar) as lead_id,
        cast(d.user_id as varchar) as user_id,
        cast(d.employee_email_prefix as varchar) as employee_email_prefix,
        max(cast(d.employee_email_name as varchar)) as employee_email_name
    from data d
    where d.qici in ('20260619期', '20260626期', '20260703期', '20260710期')
      and d.channel_map_1 = '陈瑞春'
      and d.grade_1 in ('高二', '高三')
    group by
        d.qici,
        d.channel_map_1,
        d.rule_name,
        d.grade_1,
        cast(d.lead_id as varchar),
        cast(d.user_id as varchar),
        cast(d.employee_email_prefix as varchar)
),
learn_raw as (
    select
        cast(t.user_number as varchar) as user_id,
        date_trunc('minute', cast(t.begin_time as timestamp)) as begin_time_slot,
        max(cast(t.live_learn_duration as bigint)) as live_learn_duration,
        cast(max(cast(t.is_valid_live_learn as integer)) as varchar) as is_valid_live_learn
    from service_dw.dws_service_user_learn_detail_hf t
    inner join schedule_times st
      on date_trunc('minute', cast(t.begin_time as timestamp)) = st.begin_time_slot
    where t.dt = date_format(now() - interval '2' hour, '%Y%m%d')
      and t.hour = date_format(now() - interval '2' hour, '%H')
      and t.course_first_level_department_name = 'H业务线'
      and t.course_second_level_department_name in ('精品班学部', '市场部', '青橙项目部')
      and t.is_need_attend = 1
      and cast(t.begin_time as timestamp) >= timestamp '2026-06-19 00:00:00'
      and cast(t.begin_time as timestamp) < timestamp '2026-07-13 00:00:00'
    group by
        cast(t.user_number as varchar),
        date_trunc('minute', cast(t.begin_time as timestamp))
),
attendance_long as (
    select
        lb.qici,
        lb.channel_map_1,
        lb.rule_name,
        lb.grade_1,
        lb.lead_id,
        lb.user_id,
        lb.employee_email_prefix,
        lb.employee_email_name,
        s.lesson_no,
        s.begin_time_slot,
        lr.live_learn_duration,
        lr.is_valid_live_learn
    from lead_base lb
    inner join schedule s
      on lb.qici = s.qici
     and lb.channel_map_1 = s.channel_map_1
     and lb.grade_1 = s.grade_1
    left join learn_raw lr
      on lb.user_id = lr.user_id
     and s.begin_time_slot = lr.begin_time_slot
),
user_flags as (
    select
        a.qici,
        a.channel_map_1,
        a.rule_name,
        a.grade_1,
        a.lead_id,
        a.user_id,
        a.employee_email_prefix,
        a.employee_email_name,
        '精品班学部' as department,
        1 as valid_lead,
        max(case when a.lesson_no = '1' then a.begin_time_slot end) as lesson_1_begin_time,
        max(case when a.lesson_no = '2' then a.begin_time_slot end) as lesson_2_begin_time,
        max(case when a.lesson_no = '3' then a.begin_time_slot end) as lesson_3_begin_time,
        max(case when a.lesson_no = '4' then a.begin_time_slot end) as lesson_4_begin_time,
        max(case when a.lesson_no = '5' then a.begin_time_slot end) as lesson_5_begin_time,
        max(case when a.lesson_no = '6' then a.begin_time_slot end) as lesson_6_begin_time,
        max(case when a.lesson_no = '1' and coalesce(a.live_learn_duration, 0) > 0 then 1 else 0 end) as lesson_1_attended,
        max(case when a.lesson_no = '1' and a.is_valid_live_learn = '1' then 1 else 0 end) as lesson_1_valid_attended,
        max(case when a.lesson_no = '2' and coalesce(a.live_learn_duration, 0) > 0 then 1 else 0 end) as lesson_2_attended,
        max(case when a.lesson_no = '2' and a.is_valid_live_learn = '1' then 1 else 0 end) as lesson_2_valid_attended,
        max(case when a.lesson_no = '3' and coalesce(a.live_learn_duration, 0) > 0 then 1 else 0 end) as lesson_3_attended,
        max(case when a.lesson_no = '3' and a.is_valid_live_learn = '1' then 1 else 0 end) as lesson_3_valid_attended,
        max(case when a.lesson_no = '4' and coalesce(a.live_learn_duration, 0) > 0 then 1 else 0 end) as lesson_4_attended,
        max(case when a.lesson_no = '4' and a.is_valid_live_learn = '1' then 1 else 0 end) as lesson_4_valid_attended,
        max(case when a.lesson_no = '5' and coalesce(a.live_learn_duration, 0) > 0 then 1 else 0 end) as lesson_5_attended,
        max(case when a.lesson_no = '5' and a.is_valid_live_learn = '1' then 1 else 0 end) as lesson_5_valid_attended,
        max(case when a.lesson_no = '6' and coalesce(a.live_learn_duration, 0) > 0 then 1 else 0 end) as lesson_6_attended,
        max(case when a.lesson_no = '6' and a.is_valid_live_learn = '1' then 1 else 0 end) as lesson_6_valid_attended
    from attendance_long a
    group by
        a.qici,
        a.channel_map_1,
        a.rule_name,
        a.grade_1,
        a.lead_id,
        a.user_id,
        a.employee_email_prefix,
        a.employee_email_name
)
select
    qici,
    channel_map_1,
    rule_name,
    grade_1,
    lead_id,
    user_id,
    employee_email_prefix,
    employee_email_name,
    department,
    valid_lead,
    lesson_1_begin_time,
    lesson_2_begin_time,
    lesson_3_begin_time,
    lesson_4_begin_time,
    lesson_5_begin_time,
    lesson_6_begin_time,
    lesson_1_attended,
    lesson_1_valid_attended,
    lesson_2_attended,
    lesson_2_valid_attended,
    lesson_3_attended,
    lesson_3_valid_attended,
    lesson_4_attended,
    lesson_4_valid_attended,
    lesson_5_attended,
    lesson_5_valid_attended,
    lesson_6_attended,
    lesson_6_valid_attended
from user_flags
order by qici, channel_map_1, grade_1, lead_id, user_id, employee_email_prefix
