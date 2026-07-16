with
-- 青橙昆仑山战役期次日种子。后续只需追加新的期次日期；业务窗口自动取期次日前后各 2 天。
-- 例如 20260722期对应 2026-07-20 至 2026-07-24。
biz_qici_seed as (
    select date '2026-07-16' as qici_date
    union all select date '2026-07-22'
    union all select date '2026-07-28'
    union all select date '2026-08-03'
    union all select date '2026-08-09'
    union all select date '2026-08-15'
    union all select date '2026-08-21'
),
biz_qici_calendar as (
    select
        qici_date - interval '2' day as start_date,
        qici_date + interval '2' day as end_date,
        concat(date_format(cast(qici_date as timestamp), '%Y%m%d'), '期') as qici
    from biz_qici_seed
),
d_ap as (
    select distinct
        user_latest.user_number,
        case
            when user_latest.event_timestamp >= current_timestamp - interval '7' day
             and user_latest.appliction_name in ('PC客户端', 'APP', 'PC')
            then 1 else 0
        end as is_app_denglu_d
    from (
        select
            ul.user_number,
            ul.appliction_name,
            try(date_parse(ul.last_event_time, '%Y-%m-%d %H:%i:%s:%f')) as event_timestamp
        from (
            select
                user_number,
                appliction_name,
                last_event_time,
                row_number() over (
                    partition by user_number
                    order by try(date_parse(last_event_time, '%Y-%m-%d %H:%i:%s:%f')) desc
                ) as login_rn
            from dw.dim_cstm_active_user_c_appliction_mb_df
            where dt = format_datetime(current_timestamp - interval '24' hour, 'YYYYMMdd')
              and product_name in ('高途', '规划精品')
        ) ul
        where login_rn = 1
    ) user_latest
),
h_ap as (
    select
        user_number,
        max(case when application_name in ('PC客户端', 'APP', 'PC') then 1 else 0 end) as is_app_denglu_h
    from dw.dws_user_active_user_c_appliction_hf
    where dt = format_datetime(current_timestamp - interval '2' hour, 'YYYYMMdd')
      and hour = format_datetime(current_timestamp - interval '2' hour, 'HH')
      and product_name in ('高途', '规划精品')
    group by user_number
),
denglu_app as (
    select
        coalesce(d.user_number, h.user_number) as user_number,
        case
            when coalesce(h.is_app_denglu_h, 0) = 1
              or coalesce(d.is_app_denglu_d, 0) = 1
            then 1 else 0
        end as is_app_denglu
    from d_ap d
    full outer join h_ap h on d.user_number = h.user_number
),

-- TMK / 规划系统潜客 -> 正常线索。潜客只计一次，转移后的线索 ID 保留作链路证明。
dwd_prelead as (
    select distinct
        cast(crm_leads_id as bigint) as prelead_id,
        cast(user_id as bigint) as prelead_user_id,
        purchase_intention_name as prelead_purchase_intention_name
    from data_lake_fuwu.dwd_crm_leads_rt
    where model_type = 1
      and purchase_intention_name in (
          '高中预科青橙TMK',
          '高一青橙TMK',
          '高二青橙TMK',
          '高三青橙TMK',
          '规划系统高一',
          '规划系统高二',
          '规划系统高三'
      )
),
dwd_transfer_raw as (
    select
        p.prelead_id,
        p.prelead_user_id,
        p.prelead_purchase_intention_name,
        cast(l.crm_leads_id as bigint) as transfer_lead_id,
        row_number() over (
            partition by p.prelead_id
            order by cast(l.crm_leads_id as bigint) desc
        ) as transfer_rn
    from dwd_prelead p
    join data_lake_fuwu.dwd_crm_leads_rt l
      on cast(l.previous_model_id as bigint) = p.prelead_id
    where l.model_type = 0
      and l.previous_model_id > 0
),
dwd_transfer as (
    select
        prelead_id,
        prelead_user_id,
        prelead_purchase_intention_name,
        transfer_lead_id
    from dwd_transfer_raw
    where transfer_rn = 1
),

-- 只排除确实会进入 TMK 输出的转后正常线索，避免正常线索与潜客行跨来源重复。
tmk_output_transfer_ids as (
    select distinct
        tr.transfer_lead_id
    from dwd_transfer_raw tr
    join bdg_ba.app_crm_prelead_cost_gmv_full_link_data_hf f
      on cast(f.lead_id as bigint) = tr.prelead_id
    where f.dt = format_datetime(current_timestamp - interval '2' hour, 'YYYYMMdd')
      and f.hour = format_datetime(current_timestamp - interval '2' hour, 'HH')
      and f.lead_model_type = 1
      and f.section_assign_employee_first_level_department_name = 'H业务线'
      and f.virtual_third_department_name is not null
      and f.virtual_fourth_department_name is not null
      and coalesce(try_cast(f.valid_lead_count as bigint), 0) > 0
      and f.employee_email_name is not null
      -- “规划系统高一/高二/高三”为跨部门共用意向；只允许青橙 SEC 来源进入排重链路。
      and (
          tr.prelead_purchase_intention_name not in (
              '规划系统高一',
              '规划系统高二',
              '规划系统高三'
          )
          or (
              f.virtual_third_department_name = '学习顾问部'
              and f.virtual_fourth_department_name = 'SEC创新部'
          )
      )
),

normal_first_connected as (
    select
        cast(lead_id as bigint) as lead_id,
        date_diff(
            'hour',
            cast(section_assign_time as timestamp),
            cast(section_assign_first_call_connected_time as timestamp)
        ) as first_call_connected_time_diff_hour
    from service_dw.dm_crm_lead_stats_detail_hf
    where dt = format_datetime(current_timestamp - interval '2' hour, 'YYYYMMdd')
      and hour = format_datetime(current_timestamp - interval '2' hour, 'HH')
      and mapping_first_level_department_name = 'H业务线'
      and mapping_second_level_department_name in (
          '精品班学部',
          '菁英班学部',
          '市场部',
          '本地化大班学部',
          '青橙项目部'
      )
),

-- 原青橙正常线索路径，输出到共享过程行接口。
normal_data as (
    select distinct
        'normal_lead' as record_source,
        cast(null as bigint) as prelead_id,
        cast(f.lead_id as bigint) as transfer_lead_id,
        cast(f.lead_id as bigint) as process_lead_id,
        cast(f.user_id as bigint) as user_id,
        coalesce(
            cal.qici,
            concat(
                date_format(
                    date_trunc(
                        'week',
                        date_parse(
                            replace(concat(f.group_period_year, f.group_period_term), '期', ''),
                            '%Y%m%d'
                        ) - interval '1' day
                    ) + interval '4' day,
                    '%Y%m%d'
                ),
                '期'
            )
        ) as qici,
        f.rule_name,
        substr(f.section_assign_time, 1, 10) as assign_day,
        cast(f.section_assign_time as timestamp) as section_assign_timestamp,
        cast(null as varchar) as tmk_channel_detail,
        case
            when f.rule_name like '%高一%' then '高一'
            when f.rule_name like '%高二%' then '高二'
            when f.rule_name like '%高三%' then '高三'
            when f.rule_name like '%初二%' then '初二'
            when f.rule_name like '%初三%' then '初三'
            else f.lead_purchase_intention_level2_category_name
        end as grade_1,
        f.employee_email_name,
        f.employee_email_prefix,
        cast(null as varchar) as fallback_department,
        cast(null as varchar) as fallback_dept_2,
        cast(null as varchar) as fallback_xiaozu,
        coalesce(try_cast(f.valid_lead_count as bigint), 0) as valid_lead_count,
        case when coalesce(try_cast(f.valid_lead_count as bigint), 0) > 0 then 1 else 0 end as v_lead,
        case
            when coalesce(try_cast(f.valid_lead_count as bigint), 0) > 0
            then coalesce(try_cast(f.friend_lead_count as bigint), 0)
            else 0
        end as is_friend_lead,
        date_diff(
            'hour',
            cast(f.section_assign_time as timestamp),
            cast(f.first_call_time as timestamp)
        ) as first_call_time_diff_hour,
        jt.first_call_connected_time_diff_hour as first_call_connected_time_diff_hour_1,
        cast(null as bigint) as source_call_duration_seconds,
        cast(null as bigint) as source_call_connected_count,
        cast(null as bigint) as source_call_missed_count
    from bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df f
    left join normal_first_connected jt
      on cast(f.lead_id as bigint) = jt.lead_id
    left join biz_qici_calendar cal
      on cast(
          try(date_parse(replace(concat(f.group_period_year, f.group_period_term), '期', ''), '%Y%m%d'))
          as date
      ) between cal.start_date and cal.end_date
    left join tmk_output_transfer_ids tmk_dup
      on cast(f.lead_id as bigint) = tmk_dup.transfer_lead_id
    where f.dt = format_datetime(current_timestamp - interval '2' hour, 'YYYYMMdd')
      and f.hour = format_datetime(current_timestamp - interval '3' hour, 'HH')
      and f.section_assign_employee_first_level_department_name = 'H业务线'
      and f.section_assign_employee_second_level_department_name = '青橙项目部'
      and f.period_mapping_first_level_department_name = 'H业务线'
      and f.period_mapping_second_level_department_name in ('精品班学部', '青橙项目部')
      and coalesce(try_cast(f.valid_lead_count as bigint), 0) > 0
      and f.virtual_second_department_name = '青橙项目部'
      and tmk_dup.transfer_lead_id is null
),

-- 潜客宽表可能一潜客多行；优先保留有效、规则/顾问完整且分配时间最新的一行。
tmk_prelead_raw as (
    select
        p.prelead_id,
        t.transfer_lead_id,
        coalesce(cast(f.user_id as bigint), p.prelead_user_id) as user_id,
        p.prelead_purchase_intention_name,
        coalesce(f.rule_name, concat('TMK-', p.prelead_purchase_intention_name)) as rule_name,
        coalesce(
            cal.qici,
            concat(
                date_format(
                    date_trunc(
                        'week',
                        date_parse(
                            replace(concat(f.group_period_year, f.group_period_term), '期', ''),
                            '%Y%m%d'
                        ) - interval '1' day
                    ) + interval '4' day,
                    '%Y%m%d'
                ),
                '期'
            )
        ) as qici,
        f.group_period_year,
        f.group_period_term,
        f.stats_grade_name,
        f.lead_purchase_intention_level2_category_name,
        f.employee_email_name,
        f.employee_email_prefix,
        f.virtual_third_department_name,
        f.virtual_fourth_department_name,
        f.virtual_leader_email_name,
        f.virtual_direct_leader_email_name,
        f.section_assign_time,
        f.first_call_time,
        f.section_assign_first_call_connected_time,
        coalesce(try_cast(f.valid_lead_count as bigint), 0) as valid_lead_count,
        coalesce(try_cast(f.friend_lead_count as bigint), 0) as friend_lead_count,
        coalesce(try_cast(f.section_assign_call_connected_count as bigint), 0) as source_call_connected_count,
        coalesce(try_cast(f.section_assign_call_missed_count as bigint), 0) as source_call_missed_count,
        coalesce(try_cast(f.section_assign_all_call_duration as bigint), 0) as source_call_duration_seconds,
        row_number() over (
            partition by p.prelead_id
            order by
                coalesce(try_cast(f.valid_lead_count as bigint), 0) desc,
                case when f.rule_name is not null then 0 else 1 end,
                case when f.employee_email_name is not null then 0 else 1 end,
                f.section_assign_time desc,
                f.employee_email_prefix,
                t.transfer_lead_id
        ) as prelead_rn
    from bdg_ba.app_crm_prelead_cost_gmv_full_link_data_hf f
    join dwd_prelead p
      on cast(f.lead_id as bigint) = p.prelead_id
    left join dwd_transfer t
      on p.prelead_id = t.prelead_id
    left join biz_qici_calendar cal
      on cast(
          try(date_parse(replace(concat(f.group_period_year, f.group_period_term), '期', ''), '%Y%m%d'))
          as date
      ) between cal.start_date and cal.end_date
    where f.dt = format_datetime(current_timestamp - interval '2' hour, 'YYYYMMdd')
      and f.hour = format_datetime(current_timestamp - interval '2' hour, 'HH')
      and f.lead_model_type = 1
      and f.section_assign_employee_first_level_department_name = 'H业务线'
      and f.virtual_third_department_name is not null
      and f.virtual_fourth_department_name is not null
      -- 来源限域：共用的规划系统意向仅接收学习顾问部 / SEC创新部。
      -- 输出阶段仍需命中同一期次组织架构 dept_2='SEC'，形成双重限域。
      and (
          p.prelead_purchase_intention_name not in (
              '规划系统高一',
              '规划系统高二',
              '规划系统高三'
          )
          or (
              f.virtual_third_department_name = '学习顾问部'
              and f.virtual_fourth_department_name = 'SEC创新部'
          )
      )
),
tmk_data as (
    select
        'tmk_prelead' as record_source,
        prelead_id,
        transfer_lead_id,
        prelead_id as process_lead_id,
        user_id,
        qici,
        rule_name,
        substr(section_assign_time, 1, 10) as assign_day,
        cast(section_assign_time as timestamp) as section_assign_timestamp,
        case
            when rule_name like '%武汉图书%' then '武汉图书'
            when rule_name like '%公域%' then '公域'
            when rule_name like '%首期掉海%' then '首期掉海'
            when rule_name like '%未加好友%'
              or prelead_purchase_intention_name like '规划系统%'
            then '未加好友'
            else '其他'
        end as tmk_channel_detail,
        coalesce(
            stats_grade_name,
            lead_purchase_intention_level2_category_name,
            case
                when prelead_purchase_intention_name like '%高一%' then '高一'
                when prelead_purchase_intention_name like '%高二%' then '高二'
                when prelead_purchase_intention_name like '%高三%' then '高三'
                when prelead_purchase_intention_name like '%高中预科%' then '高中预科'
            end
        ) as grade_1,
        employee_email_name,
        employee_email_prefix,
        coalesce(virtual_third_department_name, '青橙TMK') as fallback_department,
        coalesce(virtual_fourth_department_name, 'TMK') as fallback_dept_2,
        coalesce(
            virtual_direct_leader_email_name,
            virtual_leader_email_name,
            'TMK待映射'
        ) as fallback_xiaozu,
        valid_lead_count,
        case when valid_lead_count > 0 then 1 else 0 end as v_lead,
        case when valid_lead_count > 0 then friend_lead_count else 0 end as is_friend_lead,
        date_diff(
            'hour',
            cast(section_assign_time as timestamp),
            cast(first_call_time as timestamp)
        ) as first_call_time_diff_hour,
        date_diff(
            'hour',
            cast(section_assign_time as timestamp),
            cast(section_assign_first_call_connected_time as timestamp)
        ) as first_call_connected_time_diff_hour_1,
        source_call_duration_seconds,
        source_call_connected_count,
        source_call_missed_count
    from tmk_prelead_raw
    where prelead_rn = 1
      and valid_lead_count > 0
      and employee_email_name is not null
),

-- 正常线索和 TMK 潜客共用同一过程行接口，后续指标只维护一套表达式。
raw_data as (
    select * from normal_data
    union all
    select * from tmk_data
),
data as (
    select
        r.*,
        case
            when r.record_source = 'tmk_prelead' then '订单复用'
            when r.rule_name like '%抖音正价退费%' then '抖音复用'
            when r.rule_name like '%私域%' then '青橙私域'
            when r.rule_name like '%青橙IP%' then '青橙IP'
            when r.rule_name like '%青橙公海%' then '青橙公海'
            when r.rule_name like '%青橙公域%' then '青橙公域'
            when r.rule_name like '%青橙图书%' then '青橙图书'
            when r.rule_name like '%青橙本地化%' then '青橙本地化'
            when r.rule_name like '%抖音私信%' then '抖音私信'
            when r.rule_name like '%进校%' then '进校'
            when r.rule_name like '%训练营%' then '青橙训练营'
        end as channel_map_1,
        case
            when r.record_source = 'tmk_prelead'
            then coalesce(r.tmk_channel_detail, '其他')
            when r.rule_name like '%赠失-星义%' then 'IP星义'
            when r.rule_name like '%赠失-朱博士%' then 'IP朱博士'
            when r.rule_name like '%赠失-春春%' then 'IP春春'
            when r.rule_name like '%赠失-郭艺%' then 'IP郭艺'
            when r.rule_name like '%赠失-亚飞%' then 'IP亚飞'
            when r.rule_name like '%私域会话%' then '私域会话'
            when r.rule_name like '%私域表单%' then '私域表单'
            when r.rule_name like '%私域图书%' then '私域图书'
            when r.rule_name like '%私域裂变%' then '私域裂变'
            when r.rule_name like '%私域品效%' then '私域品效'
            when r.rule_name like '%私域IE%' then '私域IE'
            when r.rule_name like '%私域本地化%' then '私域本地化'
            when r.rule_name like '%亚飞IP%' then '亚飞IP'
            when r.rule_name like '%SEC未加好友%' then 'SEC未加好友'
            when r.rule_name like '%SEC首期掉海%' then 'SEC首期掉海'
            when r.rule_name like '%顾问未加好友%' then '顾问未加好友'
            when r.rule_name like '%郑州图书%' then '郑州图书'
            when r.rule_name like '%武汉图书%' then '武汉图书'
            when r.rule_name like '%西安图书%' then '西安图书'
            when r.rule_name like '%图书咨询%' then '图书咨询'
            when r.rule_name like '%公域学霸%' then '公域学霸'
            when r.rule_name like '%南京%' then '南京'
            when r.rule_name like '%抖音私信%' then '抖音私信'
            when r.rule_name like '%进校9元%' then '进校9元'
            when r.rule_name like '%训练营%' then '青橙训练营'
            when r.rule_name like '%抖音正价退费%' then '抖音复用'
        end as channel_map_2
    from raw_data r
),

call_detail as (
    select distinct
        wf.user_number,
        cast(wf.lead_id as bigint) as lead_id,
        wf.section_assign_employee_email_prefix,
        wf.call_duration,
        wf.call_status,
        wf.call_time,
        wf.call_type_name,
        wf.data_source,
        wf.msg_type_name
    from service_dw.app_h_crm_lead_employee_workload_detail_hf wf
    where wf.dt = format_datetime(current_timestamp - interval '2' hour, 'YYYYMMdd')
      and wf.hour = format_datetime(current_timestamp - interval '2' hour, 'HH')
),
call_c as (
    select
        user_number,
        lead_id,
        section_assign_employee_email_prefix,
        max(case when call_duration > 480 then 1 else 0 end) as is_long_call,
        sum(call_duration) as call_duration_seconds,
        sum(case when call_status in ('1', '0') then 1 else 0 end) as total_call_count,
        sum(case when call_status = '1' then 1 else 0 end) as connected_call_count
    from call_detail
    group by user_number, lead_id, section_assign_employee_email_prefix
),
-- 14 天外呼过程按精确线索键聚合，只统计分配后 0-336 小时内的事件。
-- 不复用正常线索历史指标的用户级宽关联，避免同一用户/顾问下多条线索串数。
data_call_keys as (
    select distinct
        record_source,
        process_lead_id,
        user_id,
        employee_email_prefix,
        section_assign_timestamp
    from data
),
call_14d as (
    select
        d.record_source,
        d.process_lead_id,
        d.user_id,
        d.employee_email_prefix,
        max(
            case
                when date_diff(
                    'hour',
                    d.section_assign_timestamp,
                    try_cast(cd.call_time as timestamp)
                ) between 0 and 336
                 and try_cast(cd.call_duration as bigint) > 480
                then 1 else 0
            end
        ) as is_long_call_14d,
        sum(
            case
                when date_diff(
                    'hour',
                    d.section_assign_timestamp,
                    try_cast(cd.call_time as timestamp)
                ) between 0 and 336
                then coalesce(try_cast(cd.call_duration as bigint), 0)
                else 0
            end
        ) as call_duration_seconds_14d,
        sum(
            case
                when date_diff(
                    'hour',
                    d.section_assign_timestamp,
                    try_cast(cd.call_time as timestamp)
                ) between 0 and 336
                 and cd.call_status in ('1', '0')
                then 1 else 0
            end
        ) as total_call_count_14d
    from data_call_keys d
    join call_detail cd
      on cd.user_number = d.user_id
     and cd.lead_id = d.process_lead_id
     and cd.section_assign_employee_email_prefix = d.employee_email_prefix
    group by
        d.record_source,
        d.process_lead_id,
        d.user_id,
        d.employee_email_prefix
),

daoke as (
    select
        dk.qici,
        dk.employee_email_prefix,
        dk.lead_id,
        dk.user_id,
        dk.channel_map_1,
        dk.channel_map_2,
        dk.grade_1,
        dk.begin_time,
        dk.live_learn_duration,
        dk.is_valid_live_learn,
        ke.ke_1
    from (
        select distinct
            t1.qici,
            t1.employee_email_prefix,
            t1.lead_id,
            t1.user_id,
            t1.channel_map_1,
            t1.channel_map_2,
            t1.grade_1,
            t2.live_learn_duration,
            t2.is_valid_live_learn,
            t2.begin_time
        from (
            select
                process_lead_id as lead_id,
                user_id,
                employee_email_prefix,
                qici,
                channel_map_1,
                channel_map_2,
                grade_1
            from data
            group by
                process_lead_id,
                user_id,
                employee_email_prefix,
                qici,
                channel_map_1,
                channel_map_2,
                grade_1
        ) t1
        left join (
            select
                l.user_number,
                l.begin_time,
                coalesce(
                    cal.qici,
                    case
                        when day_of_week(cast(l.begin_time as timestamp)) = 1
                        then concat(
                            date_format(
                                date_trunc('week', cast(l.begin_time as timestamp)) - interval '3' day,
                                '%Y%m%d'
                            ),
                            '期'
                        )
                        else concat(
                            date_format(
                                date_trunc('week', cast(l.begin_time as timestamp)) + interval '4' day,
                                '%Y%m%d'
                            ),
                            '期'
                        )
                    end
                ) as qici,
                l.live_learn_duration,
                l.is_valid_live_learn
            from service_dw.dws_service_user_learn_detail_hf l
            left join biz_qici_calendar cal
              on cast(l.begin_time as date) between cal.start_date and cal.end_date
            where l.dt = format_datetime(current_timestamp - interval '2' hour, 'YYYYMMdd')
              and l.hour = format_datetime(current_timestamp - interval '2' hour, 'HH')
              and l.course_first_level_department_name = 'H业务线'
              and l.course_second_level_department_name in ('精品班学部', '市场部', '青橙项目部')
              and l.is_need_attend = 1
        ) t2
          on t1.qici = t2.qici
         and t1.user_id = t2.user_number
    ) dk
    left join temp_table.dingxi01_qing_daoke ke
     on dk.qici = ke.qici
     and dk.channel_map_2 = ke.qudao
     and dk.grade_1 = ke.grade
     and dk.begin_time = ke.begin_time
),
daoke_flags as (
    select
        qici,
        employee_email_prefix,
        lead_id,
        max(
            case
                when ke_1 = '1' and live_learn_duration > 0 then 1 else 0
            end
        ) as daoke1,
        max(
            case
                when ke_1 = '1' and try_cast(is_valid_live_learn as bigint) = 1 then 1 else 0
            end
        ) as valid_daoke_1
    from daoke
    group by qici, employee_email_prefix, lead_id
),

jg_base as (
    select
        qici,
        employee_email_name,
        employee_email_prefix,
        department,
        dept_2,
        xiaozu
    from (
        select
            qici,
            employee_email_name,
            employee_email_prefix,
            department,
            dept_2,
            xiaozu,
            row_number() over (
                partition by qici, employee_email_name
                order by department, dept_2, xiaozu, employee_email_prefix
            ) as jg_rn
        from (
            select distinct
                qici,
                employee_email_name,
                employee_email_prefix,
                department,
                dept_2,
                xiaozu
            from temp_table.dingxi01_jiagou_db
            where qici >= '20260427期'
              and qici is not null
              and employee_email_name is not null
              and department is not null
              and dept_2 is not null
              and xiaozu is not null
        ) jg_distinct
    ) jg_ranked
    where jg_rn = 1
),

prc as (
    select distinct
        data.qici,
        data.rule_name,
        data.assign_day,
        data.channel_map_1,
        data.channel_map_2,
        data.grade_1,
        jg.department as department,
        jg.dept_2 as dept_2,
        jg.xiaozu as xiaozu,
        data.employee_email_name,
        data.user_id,
        data.v_lead,
        coalesce(data.is_friend_lead, 0) as is_friend_lead,
        coalesce(data.first_call_time_diff_hour, 0) as first_call_time_diff_hour,
        case
            when data.first_call_time_diff_hour between 0 and 24
             and data.valid_lead_count > 0
            then 1 else 0
        end as first_call_in_24h,
        case
            when data.first_call_time_diff_hour between 0 and 48
             and data.valid_lead_count > 0
            then 1 else 0
        end as first_call_in_48h,
        case
            when data.first_call_time_diff_hour between 0 and 168
             and data.valid_lead_count > 0
            then 1 else 0
        end as first_call_cnt,
        case
            when data.first_call_time_diff_hour between 0 and 336
             and data.valid_lead_count > 0
            then 1 else 0
        end as first_call_cnt_14d,
        case
            when data.first_call_connected_time_diff_hour_1 between 0 and 24
             and data.valid_lead_count > 0
            then 1 else 0
        end as first_call_connected_in_24h,
        case
            when data.first_call_connected_time_diff_hour_1 between 0 and 48
             and data.valid_lead_count > 0
            then 1 else 0
        end as first_call_connected_in_48h,
        case
            when data.first_call_connected_time_diff_hour_1 between 0 and 168
             and data.valid_lead_count > 0
            then 1 else 0
        end as first_call_connected_cnt,
        case
            when data.first_call_connected_time_diff_hour_1 between 0 and 336
             and data.valid_lead_count > 0
            then 1 else 0
        end as first_call_connected_cnt_14d,
        data.v_lead as v_lead_14d_denominator,
        coalesce(call_14d.is_long_call_14d, 0) as is_long_call_14d,
        coalesce(call_14d.call_duration_seconds_14d, 0) / 60.00 as call_duration_14d,
        coalesce(call_14d.total_call_count_14d, 0) as zong_call_ci_14d,
        coalesce(
            call_c.call_duration_seconds,
            data.source_call_duration_seconds,
            0
        ) / 60.00 as call_duration,
        coalesce(call_c.is_long_call, 0) as is_long_call,
        coalesce(
            call_c.total_call_count,
            data.source_call_connected_count + data.source_call_missed_count,
            0
        ) as zong_call_ci,
        coalesce(
            call_c.connected_call_count,
            data.source_call_connected_count,
            0
        ) as call_status,
        coalesce(denglu_app.is_app_denglu, 0) as is_app_denglu,
        coalesce(daoke_flags.daoke1, 0) as daoke1,
        coalesce(daoke_flags.valid_daoke_1, 0) as valid_daoke_1
    from data
    left join jg_base jg
      on data.employee_email_name = jg.employee_email_name
     and data.qici = jg.qici
    left join daoke_flags
      on data.employee_email_prefix = daoke_flags.employee_email_prefix
     and data.qici = daoke_flags.qici
     and data.process_lead_id = daoke_flags.lead_id
    left join call_c
      on call_c.user_number = data.user_id
     and call_c.section_assign_employee_email_prefix = data.employee_email_prefix
     and (
          data.record_source = 'normal_lead'
          or call_c.lead_id = data.process_lead_id
     )
    left join call_14d
      on call_14d.record_source = data.record_source
     and call_14d.process_lead_id = data.process_lead_id
     and call_14d.user_id = data.user_id
     and call_14d.employee_email_prefix = data.employee_email_prefix
    left join denglu_app
      on denglu_app.user_number = data.user_id
    where data.qici >= '20260427期'
      and jg.department is not null
      and jg.dept_2 is not null
      and jg.xiaozu is not null
      and (
          data.record_source <> 'tmk_prelead'
          or jg.dept_2 = 'SEC'
      )
      and data.channel_map_1 is not null
      and data.channel_map_2 is not null
),
final_base as (
    select
        qici,
        rule_name,
        assign_day,
        channel_map_1,
        channel_map_2,
        grade_1,
        department,
        dept_2,
        xiaozu,
        employee_email_name,
        sum(v_lead) as v_lead,
        sum(is_friend_lead) as is_friend_lead,
        sum(first_call_time_diff_hour) as first_call_time_diff_hour,
        sum(first_call_in_24h) as first_call_in_24h,
        sum(first_call_in_48h) as first_call_in_48h,
        sum(first_call_cnt) as first_call_cnt,
        sum(first_call_cnt_14d) as first_call_cnt_14d,
        sum(first_call_connected_in_24h) as first_call_connected_in_24h,
        sum(first_call_connected_in_48h) as first_call_connected_in_48h,
        sum(first_call_connected_cnt) as first_call_connected_cnt,
        sum(first_call_connected_cnt_14d) as first_call_connected_cnt_14d,
        sum(v_lead_14d_denominator) as v_lead_14d_denominator,
        sum(is_long_call_14d) as is_long_call_14d,
        sum(call_duration_14d) as call_duration_14d,
        sum(zong_call_ci_14d) as zong_call_ci_14d,
        sum(call_duration) as call_duration,
        sum(is_long_call) as is_long_call,
        sum(zong_call_ci) as zong_call_ci,
        sum(call_status) as call_status,
        sum(is_app_denglu) as is_app_denglu,
        sum(daoke1) as daoke1,
        sum(valid_daoke_1) as valid_daoke_1
    from prc
    group by
        qici,
        rule_name,
        assign_day,
        channel_map_1,
        channel_map_2,
        grade_1,
        department,
        dept_2,
        xiaozu,
        employee_email_name
),
final_with_daiban as (
    select
        marked.*,
        marked.employee_email_name as daiban_guwen_name,
        concat(
            marked.qici,
            '|', marked.department,
            '|', marked.dept_2,
            '|', marked.xiaozu,
            '|', marked.employee_email_name
        ) as daiban_guwen_key,
        case when marked.daiban_rn = 1 then 1 else 0 end as daiban_guwen_cnt
    from (
        select
            final_base.*,
            row_number() over (
                partition by
                    final_base.qici,
                    final_base.department,
                    final_base.dept_2,
                    final_base.xiaozu,
                    final_base.employee_email_name
                order by
                    final_base.v_lead desc,
                    final_base.assign_day,
                    final_base.rule_name,
                    final_base.channel_map_1,
                    final_base.channel_map_2,
                    final_base.grade_1
            ) as daiban_rn
        from final_base
    ) marked
)
select
    qici,
    rule_name,
    assign_day,
    channel_map_1,
    channel_map_2,
    grade_1,
    department,
    dept_2,
    xiaozu,
    employee_email_name,
    daiban_guwen_name,
    daiban_guwen_key,
    daiban_guwen_cnt,
    v_lead,
    is_friend_lead,
    first_call_time_diff_hour,
    first_call_in_24h,
    first_call_in_48h,
    first_call_cnt,
    first_call_cnt_14d,
    first_call_connected_in_24h,
    first_call_connected_in_48h,
    first_call_connected_cnt,
    first_call_connected_cnt_14d,
    v_lead_14d_denominator,
    is_long_call_14d,
    call_duration_14d,
    zong_call_ci_14d,
    call_duration,
    is_long_call,
    zong_call_ci,
    call_status,
    is_app_denglu,
    daoke1,
    valid_daoke_1
from final_with_daiban
