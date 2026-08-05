with
runtime_parameters as (
    select
        format_datetime(current_timestamp - interval '2' hour, 'YYYYMMdd') as app_snapshot_dt,
        format_datetime(current_timestamp - interval '2' hour, 'HH') as app_snapshot_hour,
        format_datetime(current_timestamp - interval '2' hour, 'YYYYMMddHH') as app_snapshot_key,
        format_datetime(current_timestamp - interval '1' day, 'YYYYMMdd') as employee_snapshot_dt,
        format_datetime(current_timestamp - interval '2' hour, 'YYYYMMdd') as private_snapshot_dt,
        format_datetime(current_timestamp - interval '2' hour, 'HH') as private_snapshot_hour,
        format_datetime(current_timestamp - interval '2' hour, 'YYYYMMddHH') as private_snapshot_key,
        format_datetime(current_timestamp - interval '3' hour, 'YYYYMMdd') as finance_snapshot_dt,
        format_datetime(current_timestamp - interval '3' hour, 'HH') as finance_snapshot_hour,
        format_datetime(current_timestamp - interval '3' hour, 'YYYYMMddHH') as finance_snapshot_key
),
biz_qici_calendar as (
    select *
    from (
        values
            ('20260710期', date '2026-07-07', date '2026-07-13'),
            ('20260716期', date '2026-07-14', date '2026-07-19'),
            ('20260722期', date '2026-07-20', date '2026-07-25'),
            ('20260728期', date '2026-07-26', date '2026-07-31'),
            ('20260803期', date '2026-08-01', date '2026-08-06'),
            ('20260808期', date '2026-08-07', date '2026-08-12'),
            ('20260815期', date '2026-08-13', date '2026-08-17'),
            ('20260821期', date '2026-08-19', date '2026-08-23')
    ) as t(qici, period_start_date, period_end_date)
),
app_partition as (
    select
        app_snapshot_dt as snapshot_dt,
        app_snapshot_hour as snapshot_hour,
        app_snapshot_key as snapshot_key
    from runtime_parameters
),
employee_org_ranked as (
    select
        nullif(trim(e.email_prefix), '') as employee_email_prefix,
        nullif(trim(e.leader_employee_email_name), '') as xiaozu,
        row_number() over (
            partition by nullif(trim(e.email_prefix), '')
            order by
                e.is_on_job desc,
                e.last_enroll_date desc nulls last,
                e.display_number desc
        ) as rn
    from finance_dw.dim_finance_employee_df e
    cross join runtime_parameters p
    where e.dt = p.employee_snapshot_dt
      and e.first_level_department_name = 'H业务线'
      and e.is_main_job = 1
      and nullif(trim(e.email_prefix), '') is not null
),
employee_org as (
    select
        employee_email_prefix,
        xiaozu
    from employee_org_ranked
    where rn = 1
),
private_partition as (
    select
        private_snapshot_dt as snapshot_dt,
        private_snapshot_hour as snapshot_hour,
        private_snapshot_key as snapshot_key
    from runtime_parameters
),
finance_partition as (
    select
        finance_snapshot_dt as snapshot_dt,
        finance_snapshot_hour as snapshot_hour,
        finance_snapshot_key as snapshot_key
    from runtime_parameters
),
dwd_chain_source as (
    select
        p.model_type,
        cast(p.crm_leads_id as bigint) as crm_leads_id,
        cast(p.user_id as bigint) as user_id,
        cast(p.previous_model_id as bigint) as previous_model_id,
        p.purchase_intention_name,
        case
            when p.model_type = 1 then cast(p.crm_leads_id as bigint)
            else cast(p.previous_model_id as bigint)
        end as chain_prelead_id
    from data_lake_fuwu.dwd_crm_leads_rt p
    where (
        p.model_type = 1
        and p.purchase_intention_name in (
            '高中预科青橙TMK',
            '高一青橙TMK',
            '高二青橙TMK',
            '高三青橙TMK',
            '规划系统高一',
            '规划系统高二',
            '规划系统高三'
        )
    )
    or (
        p.model_type = 0
        and p.previous_model_id > 0
    )
),
dwd_chain_windowed as (
    select
        s.*,
        max(case when s.model_type = 1 then 1 else 0 end) over (
            partition by s.chain_prelead_id
        ) as has_target_prelead,
        max(case when s.model_type = 1 then s.user_id end) over (
            partition by s.chain_prelead_id
        ) as prelead_user_id,
        max(case when s.model_type = 1 then s.purchase_intention_name end) over (
            partition by s.chain_prelead_id
        ) as prelead_purchase_intention_name
    from dwd_chain_source s
),
dwd_transfer as (
    select distinct
        chain_prelead_id as prelead_id,
        prelead_user_id,
        prelead_purchase_intention_name,
        crm_leads_id as transfer_lead_id,
        user_id as transfer_user_id,
        purchase_intention_name as transfer_purchase_intention_name
    from dwd_chain_windowed
    where model_type = 0
      and has_target_prelead = 1
),
app_prelead_source as (
    select
        f.lead_id,
        f.user_id,
        f.employee_email_name,
        f.employee_email_prefix,
        f.section_assign_time,
        f.rule_name,
        f.lead_purchase_intention_name,
        f.stats_grade_name,
        f.lead_purchase_intention_level2_category_name,
        f.group_period_year,
        f.group_period_term,
        f.group_period_name,
        f.section_assign_employee_first_level_department_name,
        f.section_assign_employee_second_level_department_name,
        f.valid_lead_count,
        f.dt,
        f.hour,
        coalesce(
            try(
                cast(
                    date_parse(
                        regexp_extract(
                            concat(
                                coalesce(f.group_period_year, ''),
                                coalesce(f.group_period_term, '')
                            ),
                            '([0-9]{8})',
                            1
                        ),
                        '%Y%m%d'
                    ) as date
                )
            ),
            try(
                cast(
                    date_parse(
                        concat(
                            regexp_extract(
                                f.group_period_name,
                                '([0-9]{4})年-([0-9]{4})期',
                                1
                            ),
                            regexp_extract(
                                f.group_period_name,
                                '([0-9]{4})年-([0-9]{4})期',
                                2
                            )
                        ),
                        '%Y%m%d'
                    ) as date
                )
            )
        ) as source_qici_date
    from bdg_ba.app_crm_prelead_cost_gmv_full_link_data_hf f
    cross join app_partition ap
    where f.dt = ap.snapshot_dt
      and f.hour = ap.snapshot_hour
      and f.lead_model_type = 1
      and f.section_assign_employee_first_level_department_name = 'H业务线'
      and f.section_assign_employee_second_level_department_name in (
          '精品班学部',
          '菁英班学部',
          '市场部',
          '本地化大班学部',
          '青橙项目部'
      )
),
app_prelead_base as (
    select
        cast(f.lead_id as bigint) as prelead_id,
        try_cast(f.user_id as bigint) as app_user_id,
        f.employee_email_name as tmk_consultant_name,
        f.employee_email_prefix as tmk_consultant_email_prefix,
        e.xiaozu,
        try_cast(f.section_assign_time as timestamp) as tmk_assign_time,
        f.rule_name as raw_rule_name,
        case
            when f.rule_name like '%武汉图书%' then '武汉图书'
            when f.rule_name like '%公域%' then '公域'
            when f.rule_name like '%首期掉海%' then '首期掉海'
            when f.rule_name like '%未加好友%' then '未加好友'
            when f.lead_purchase_intention_name like '规划系统%' then '未加好友'
            else coalesce(f.rule_name, '渠道未回补')
        end as lead_channel,
        coalesce(
            nullif(trim(f.stats_grade_name), ''),
            nullif(trim(f.lead_purchase_intention_level2_category_name), '')
        ) as app_lead_grade,
        coalesce(
            cal.qici,
            case
                when f.source_qici_date is not null then concat(
                    date_format(
                        date_trunc(
                            'week',
                            cast(f.source_qici_date as timestamp) - interval '1' day
                        ) + interval '4' day,
                        '%Y%m%d'
                    ),
                    '期'
                )
            end
        ) as qici,
        f.section_assign_employee_first_level_department_name as tmk_first_department,
        f.section_assign_employee_second_level_department_name as tmk_second_department,
        coalesce(try_cast(f.valid_lead_count as bigint), 0) as app_valid_lead_count,
        concat(f.dt, f.hour) as app_snapshot_key,
        concat(
            lpad(
                cast(
                    1000000000000
                    - coalesce(try_cast(f.valid_lead_count as bigint), 0)
                    as varchar
                ),
                13,
                '0'
            ),
            '|',
            cast(case when f.employee_email_name is not null then 0 else 1 end as varchar),
            '|',
            cast(case when f.rule_name is not null then 0 else 1 end as varchar),
            '|',
            lpad(
                cast(
                    10000000000000
                    - coalesce(
                        cast(to_unixtime(try_cast(f.section_assign_time as timestamp)) as bigint),
                        0
                    )
                    as varchar
                ),
                14,
                '0'
            ),
            '|',
            coalesce(f.employee_email_prefix, '~')
        ) as app_sort_key
    from app_prelead_source f
    left join biz_qici_calendar cal
      on f.source_qici_date between cal.period_start_date and cal.period_end_date
    left join employee_org e
      on nullif(trim(f.employee_email_prefix), '') = e.employee_email_prefix
),
app_prelead as (
    select
        prelead_id,
        try_cast(
            nullif(
                min_by(coalesce(cast(app_user_id as varchar), '__NULL__'), app_sort_key),
                '__NULL__'
            )
            as bigint
        ) as app_user_id,
        nullif(
            min_by(coalesce(tmk_consultant_name, '__NULL__'), app_sort_key),
            '__NULL__'
        ) as tmk_consultant_name,
        nullif(
            min_by(coalesce(xiaozu, '__NULL__'), app_sort_key),
            '__NULL__'
        ) as xiaozu,
        nullif(
            min_by(coalesce(tmk_consultant_email_prefix, '__NULL__'), app_sort_key),
            '__NULL__'
        ) as tmk_consultant_email_prefix,
        try_cast(
            nullif(
                min_by(coalesce(cast(tmk_assign_time as varchar), '__NULL__'), app_sort_key),
                '__NULL__'
            )
            as timestamp
        ) as tmk_assign_time,
        nullif(
            min_by(coalesce(raw_rule_name, '__NULL__'), app_sort_key),
            '__NULL__'
        ) as raw_rule_name,
        nullif(
            min_by(coalesce(lead_channel, '__NULL__'), app_sort_key),
            '__NULL__'
        ) as lead_channel,
        nullif(
            min_by(coalesce(app_lead_grade, '__NULL__'), app_sort_key),
            '__NULL__'
        ) as app_lead_grade,
        nullif(
            min_by(coalesce(qici, '__NULL__'), app_sort_key),
            '__NULL__'
        ) as qici,
        nullif(
            min_by(coalesce(tmk_first_department, '__NULL__'), app_sort_key),
            '__NULL__'
        ) as tmk_first_department,
        nullif(
            min_by(coalesce(tmk_second_department, '__NULL__'), app_sort_key),
            '__NULL__'
        ) as tmk_second_department,
        try_cast(
            nullif(
                min_by(
                    coalesce(cast(app_valid_lead_count as varchar), '__NULL__'),
                    app_sort_key
                ),
                '__NULL__'
            )
            as bigint
        ) as app_valid_lead_count,
        nullif(
            min_by(coalesce(app_snapshot_key, '__NULL__'), app_sort_key),
            '__NULL__'
        ) as app_snapshot_key
    from app_prelead_base
    group by prelead_id
),
private_history_base as (
    select
        cast(a.lead_id as bigint) as transfer_lead_id,
        try_cast(a.user_number as bigint) as private_user_id,
        a.employee_email_name as private_consultant_name,
        a.employee_email_prefix as private_consultant_email_prefix,
        try_cast(a.assign_time as timestamp) as private_assign_time,
        try_cast(a.private_sea_update_time as timestamp) as private_update_time,
        a.private_sea_id,
        a.assign_employee_second_level_department_name as private_second_department,
        try_cast(a.close_time as timestamp) as private_close_time,
        try_cast(a.close_reason as bigint) as private_close_reason,
        a.close_reason_desc,
        a.is_del,
        case
            when coalesce(a.is_del, 0) = 0
             and coalesce(
                     try_cast(a.close_time as timestamp),
                     timestamp '1970-01-01 08:00:00'
                 ) = timestamp '1970-01-01 08:00:00'
                then 1
            else 0
        end as is_active_private_record,
        concat(a.dt, a.hour) as private_snapshot_key
    from service_dw.dwd_crm_assign_private_detail_hf a
    cross join private_partition pp
    where a.dt = pp.snapshot_dt
      and a.hour = pp.snapshot_hour
      and a.model_type = 0
      and a.assign_employee_first_level_department_name = 'H业务线'
      and a.assign_employee_second_level_department_name in (
          '精品班学部',
          '菁英班学部',
          '市场部',
          '本地化大班学部',
           '青橙项目部'
       )
),
private_history_ordered as (
    select
        h.*,
        lead(h.private_user_id) over (
            partition by h.transfer_lead_id
            order by h.private_assign_time nulls last, h.private_sea_id nulls last
        ) as next_private_user_id,
        lead(h.private_consultant_name) over (
            partition by h.transfer_lead_id
            order by h.private_assign_time nulls last, h.private_sea_id nulls last
        ) as next_private_consultant_name,
        lead(h.private_consultant_email_prefix) over (
            partition by h.transfer_lead_id
            order by h.private_assign_time nulls last, h.private_sea_id nulls last
        ) as next_private_consultant_email_prefix,
        lead(h.private_assign_time) over (
            partition by h.transfer_lead_id
            order by h.private_assign_time nulls last, h.private_sea_id nulls last
        ) as next_private_assign_time,
        lead(h.private_sea_id) over (
            partition by h.transfer_lead_id
            order by h.private_assign_time nulls last, h.private_sea_id nulls last
        ) as next_private_sea_id,
        lead(h.private_second_department) over (
            partition by h.transfer_lead_id
            order by h.private_assign_time nulls last, h.private_sea_id nulls last
        ) as next_private_second_department,
        lead(h.is_active_private_record) over (
            partition by h.transfer_lead_id
            order by h.private_assign_time nulls last, h.private_sea_id nulls last
        ) as next_private_is_active,
        lead(h.is_del) over (
            partition by h.transfer_lead_id
            order by h.private_assign_time nulls last, h.private_sea_id nulls last
        ) as next_private_is_del,
        count(*) over (partition by h.transfer_lead_id) as private_history_count
    from private_history_base h
),
private_transfer_events_ranked as (
    select
        transfer_lead_id,
        next_private_user_id as private_user_id,
        next_private_consultant_name as first_receiver_name,
        next_private_consultant_email_prefix as first_receiver_email_prefix,
        next_private_assign_time as first_receiver_time,
        next_private_second_department as first_receiver_department,
        next_private_consultant_name as current_private_candidate,
        next_private_consultant_email_prefix as current_private_email_prefix,
        next_private_assign_time as current_private_assign_time,
        cast(next_private_is_active as bigint) as current_private_is_active,
        private_snapshot_key,
        private_history_count,
        row_number() over (
            partition by transfer_lead_id
            order by private_assign_time nulls last, private_sea_id nulls last
        ) as transfer_event_rn
    from private_history_ordered
    where private_close_reason = 2
      and next_private_sea_id is not null
      and next_private_assign_time is not null
      and coalesce(next_private_is_del, 0) = 0
      and next_private_is_active = 1
      and next_private_consultant_name is not null
),
private_roles as (
    select
        transfer_lead_id,
        private_user_id,
        first_receiver_name,
        first_receiver_email_prefix,
        first_receiver_time,
        first_receiver_department,
        current_private_candidate,
        current_private_email_prefix,
        current_private_assign_time,
        current_private_is_active,
        private_snapshot_key,
        private_history_count
    from private_transfer_events_ranked
    where transfer_event_rn = 1
),
transfer_enriched_channel_base as (
    select
        t.prelead_id,
        t.prelead_purchase_intention_name,
        t.transfer_purchase_intention_name,
        coalesce(
            a.app_user_id,
            t.prelead_user_id,
            t.transfer_user_id,
            p.private_user_id
        ) as user_id,
        t.transfer_lead_id,
        a.qici,
        case
            when a.qici is not null then 'app_prelead'
            else 'app_not_backfilled'
        end as qici_source,
        cast(p.first_receiver_time as date) as assign_day,
        a.tmk_consultant_name,
        a.xiaozu,
        a.tmk_consultant_email_prefix,
        a.tmk_assign_time,
        a.tmk_first_department,
        a.tmk_second_department,
        coalesce(
            a.app_lead_grade,
            case
                when a.raw_rule_name like '%高一%' then '高一'
                when a.raw_rule_name like '%高二%' then '高二'
                when a.raw_rule_name like '%高三%' then '高三'
                when t.transfer_purchase_intention_name like '%高一%' then '高一'
                when t.transfer_purchase_intention_name like '%高二%' then '高二'
                when t.transfer_purchase_intention_name like '%高三%' then '高三'
                when t.prelead_purchase_intention_name like '%高一%' then '高一'
                when t.prelead_purchase_intention_name like '%高二%' then '高二'
                when t.prelead_purchase_intention_name like '%高三%' then '高三'
                when t.prelead_purchase_intention_name like '%高中预科%' then '高中预科'
            end
        ) as lead_grade,
        case
            when a.app_lead_grade is not null then 'app_prelead_grade'
            when a.raw_rule_name like '%高一%'
              or a.raw_rule_name like '%高二%'
              or a.raw_rule_name like '%高三%' then 'app_rule_name'
            when t.transfer_purchase_intention_name like '%高一%'
              or t.transfer_purchase_intention_name like '%高二%'
              or t.transfer_purchase_intention_name like '%高三%' then 'transfer_intention'
            when t.prelead_purchase_intention_name like '%高一%'
              or t.prelead_purchase_intention_name like '%高二%'
              or t.prelead_purchase_intention_name like '%高三%'
              or t.prelead_purchase_intention_name like '%高中预科%' then 'prelead_intention'
            else 'grade_not_backfilled'
        end as lead_grade_source,
        a.lead_channel,
        a.raw_rule_name,
        case
            when a.raw_rule_name like '%武汉图书%' then '武汉图书'
            when a.raw_rule_name like '%西安图书%' then '西安图书'
            when a.raw_rule_name like '%公域学霸%'
              or a.raw_rule_name like '%公域%' then '公域学霸'
            when a.raw_rule_name like '%抖音正价退费%' then '抖音正价退费'
            when a.raw_rule_name like '%SEC招生退费%'
              or a.raw_rule_name like '%招生退费%' then 'SEC招生退费'
            when a.raw_rule_name like '%SEC首期掉海%'
              or a.raw_rule_name like '%首期掉海%' then 'SEC首期掉海'
            when a.raw_rule_name like '%SEC未加好友%'
              or a.raw_rule_name like '%未加好友%'
              or t.prelead_purchase_intention_name like '规划系统%'
                then 'SEC未加好友'
        end as channel_map_2,
        a.app_valid_lead_count,
        p.first_receiver_name,
        p.first_receiver_email_prefix,
        p.first_receiver_time,
        p.first_receiver_department,
        coalesce(
            p.current_private_candidate,
            p.first_receiver_name
        ) as current_consultant_name,
        case
            when p.current_private_candidate is not null
             and p.current_private_is_active = 1 then 'private_active_candidate'
            when p.current_private_candidate is not null then 'private_latest_candidate'
            when p.first_receiver_name is not null then 'first_receiver_fallback'
            else '未回补'
        end as current_consultant_source,
        p.current_private_candidate,
        p.current_private_assign_time,
        p.current_private_is_active,
        p.private_history_count,
        cast(null as timestamp) as transfer_lead_create_time,
        cast(null as varchar) as transfer_lead_period_name,
        a.app_snapshot_key,
        p.private_snapshot_key,
        cast(null as varchar) as lead_snapshot_key
    from dwd_transfer t
    left join app_prelead a
      on a.prelead_id = t.prelead_id
    inner join private_roles p
      on p.transfer_lead_id = t.transfer_lead_id
),
transfer_enriched as (
    select
        b.*,
        case
            when b.channel_map_2 = '公域学霸' then '公域'
            when b.channel_map_2 in ('武汉图书', '西安图书') then '图书'
            when b.channel_map_2 in ('SEC未加好友', 'SEC首期掉海', 'SEC招生退费')
                then '订单复用'
            when b.raw_rule_name like '%抖音正价退费%' then '抖音复用'
            when b.raw_rule_name like '%赠失-星义%'
              or b.raw_rule_name like '%赠失-朱博士%'
              or b.raw_rule_name like '%赠失-春春%'
              or b.raw_rule_name like '%赠失-郭艺%'
              or b.raw_rule_name like '%赠失-亚飞%'
              or b.raw_rule_name like '%青橙IP%'
                then concat('IP', chr(36192), chr(35838), chr(22833), chr(36133))
            when b.raw_rule_name like '%私域本地化%'
              or b.raw_rule_name like '%河南本地化%'
              or b.raw_rule_name like '%青橙本地化%' then '本地化'
            when b.raw_rule_name like '%私域会话%'
              or b.raw_rule_name like '%私域表单%'
              or b.raw_rule_name like '%私域品效%'
              or b.raw_rule_name like '%私域图书%' then '私域'
            when b.raw_rule_name like '%公域学霸%'
              or b.raw_rule_name like '%青橙公域%' then '公域'
            when b.raw_rule_name like '%武汉图书%'
              or b.raw_rule_name like '%西安图书%' then '图书'
            when b.raw_rule_name like '%亚飞IP%' then '主讲IP'
            when b.raw_rule_name like '%SEC未加好友%'
              or b.raw_rule_name like '%SEC首期掉海%'
              or b.raw_rule_name like '%SEC招生退费%'
              or b.raw_rule_name like '%招生退费%' then '订单复用'
            when b.raw_rule_name like '%顾问未加好友%'
              or b.raw_rule_name like '%青橙公海%' then '公海'
            when b.raw_rule_name like '%抖音私信%' then '抖音私信'
            when b.raw_rule_name like '%进校9元%'
              or b.raw_rule_name like '%进校%' then '进校9元'
        end as channel_map_1
    from transfer_enriched_channel_base b
),
finance_order_grouped as (
    select
        try_cast(o.original_order_user_number as bigint) as finance_user_id,
        cast(o.lead_id as bigint) as finance_lead_id,
        cast(o.order_number as varchar) as order_number,
        o.performance_employee_email_name as performance_consultant_name,
        o.performance_second_level_department_name as performance_department,
        max(o.pay_success_timestamp) as pay_success_timestamp,
        max(o.trade_timestamp) as trade_timestamp,
        array_join(
            array_sort(
                array_agg(distinct nullif(trim(cast(o.grade_name as varchar)), ''))
            ),
            ','
        ) as deal_grade,
        array_join(
            array_sort(
                array_agg(
                    distinct nullif(
                        trim(
                            cast(
                                coalesce(o.mapping_school_subject_name, o.school_subject_name)
                                as varchar
                            )
                        ),
                        ''
                    )
                )
            ),
            ','
        ) as deal_subject,
        array_join(
            array_sort(
                array_agg(
                    distinct nullif(trim(cast(o.main_teacher_nickname as varchar)), '')
                )
            ),
            ','
        ) as deal_main_teacher,
        max(coalesce(cast(o.income_amount as double), 0.0)) as income_amount_fen,
        max(coalesce(cast(o.refund_amount as double), 0.0)) as raw_refund_amount_fen,
        max(coalesce(o.is_pay_success_order, 0)) as is_pay_success_order,
        max(coalesce(o.is_full_refund_order, 0)) as is_full_refund_order,
        concat(o.dt, o.hour) as finance_snapshot_key
    from service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf o
    cross join finance_partition fp
    where o.dt = fp.snapshot_dt
      and o.hour = fp.snapshot_hour
      and o.performance_second_level_department_name in (
          '精品班学部',
          '菁英班学部',
          '市场部',
          '本地化大班学部',
          '青橙项目部'
      )
      and o.course_first_level_department_name in (
          'H业务线',
          'LL业务线',
          'TUTU',
          'TT',
          'A业务线',
          'EM业务线',
          'KA业务线',
          'TT业务线',
          '创新中心'
      )
      and o.course_second_level_department_name in (
          '精品班学部',
          '青橙项目部',
          '菁英班学部',
          '一对一学部',
          '创新学部',
          '升学规划中心',
          '线上考研学部'
      )
      and o.order_number is not null
      and coalesce(o.pay_success_timestamp, o.trade_timestamp)
          >= timestamp '2026-04-01 00:00:00'
    group by
        try_cast(o.original_order_user_number as bigint),
        cast(o.lead_id as bigint),
        cast(o.order_number as varchar),
        o.performance_employee_email_name,
        o.performance_second_level_department_name,
        concat(o.dt, o.hour)
),
finance_order as (
    select
        finance_user_id,
        finance_lead_id,
        order_number,
        performance_consultant_name,
        performance_department,
        coalesce(pay_success_timestamp, trade_timestamp) as order_event_time,
        pay_success_timestamp,
        trade_timestamp,
        deal_grade,
        deal_subject,
        deal_main_teacher,
        round(income_amount_fen / 100.0, 2) as deal_amount_yuan,
        round(
            greatest(
                raw_refund_amount_fen,
                case
                    when is_full_refund_order = 1 then income_amount_fen
                    else 0.0
                end
            ) / 100.0,
            2
        ) as refund_amount_yuan,
        round(
            (
                income_amount_fen
                - greatest(
                    raw_refund_amount_fen,
                    case
                        when is_full_refund_order = 1 then income_amount_fen
                        else 0.0
                    end
                )
            ) / 100.0,
            2
        ) as net_amount_yuan,
        case
            when is_pay_success_order = 1 or income_amount_fen > 0 then 1
            else 0
        end as is_deal_order,
        is_full_refund_order,
        finance_snapshot_key
    from finance_order_grouped
),
transfer_match_keys as (
    select
        t.*,
        k.match_type,
        case
            when k.match_type = 'transfer_lead'
                then concat('L:', cast(t.transfer_lead_id as varchar))
            when k.match_type = 'prelead'
                then concat('L:', cast(t.prelead_id as varchar))
            else concat('U:', cast(t.user_id as varchar))
        end as match_key
    from transfer_enriched t
    cross join (
        select 'transfer_lead' as match_type
        union all
        select 'prelead' as match_type
        union all
        select 'user' as match_type
    ) k
    where k.match_type <> 'user'
       or t.user_id is not null
),
finance_match_keys as (
    select
        f.*,
        case
            when k.match_type = 'lead'
                then concat('L:', cast(f.finance_lead_id as varchar))
            else concat('U:', cast(f.finance_user_id as varchar))
        end as finance_match_key
    from finance_order f
    cross join (
        select 'lead' as match_type
        union all
        select 'user' as match_type
    ) k
    where (k.match_type = 'lead' and f.finance_lead_id is not null)
       or (k.match_type = 'user' and f.finance_user_id is not null)
),
order_candidate_scored as (
    select
        t.*,
        f.*,
        case
            when f.order_number is null then 9
            when t.match_type = 'transfer_lead' then 1
            when t.match_type = 'prelead' then 2
            when f.finance_user_id = t.user_id
             and f.order_event_time >= t.first_receiver_time then 3
            else 4
        end as attribution_priority,
        case
            when f.order_number is null then cast(null as varchar)
            when t.match_type = 'transfer_lead' then '直接命中转移线索'
            when t.match_type = 'prelead' then '直接命中潜客'
            when f.finance_user_id = t.user_id
             and f.order_event_time >= t.first_receiver_time then '同用户-转移后成交'
            else '同用户-转移前已成交'
        end as deal_attribution_type,
        case
            when f.order_number is null then cast(null as varchar)
            when t.first_receiver_time is null or f.order_event_time is null then '时间关系未知'
            when f.order_event_time < t.first_receiver_time then '转移前已成交'
            else '转移后成交'
        end as deal_time_relation,
        abs(
            coalesce(
                date_diff('second', t.first_receiver_time, f.order_event_time),
                9223372036854775807
            )
        ) as transfer_order_diff_seconds
    from transfer_match_keys t
    left join finance_match_keys f
      on f.finance_match_key = t.match_key
     and (
         t.match_type <> 'user'
         or (
             t.first_receiver_time is not null
             and f.order_event_time between
                 t.first_receiver_time - interval '30' day
                 and t.first_receiver_time + interval '90' day
         )
     )
),
order_candidate_ranked as (
    select
        c.*,
        row_number() over (
            partition by
                c.finance_lead_id,
                c.order_number,
                c.performance_consultant_name,
                case
                    when c.order_number is null then c.transfer_lead_id
                end
            order by
                c.attribution_priority,
                c.transfer_order_diff_seconds,
                c.first_receiver_time desc nulls last,
                c.transfer_lead_id,
                c.match_type
        ) as transfer_chain_rn
    from order_candidate_scored c
),
order_attribution as (
    select
        transfer_lead_id,
        max(qici) as qici,
        max(assign_day) as assign_day,
        max(tmk_consultant_name) as tmk_consultant_name,
        max(xiaozu) as xiaozu,
        max(user_id) as user_id,
        max(lead_grade) as lead_grade,
        max(lead_channel) as lead_channel,
        max(channel_map_1) as channel_map_1,
        max(channel_map_2) as channel_map_2,
        max(first_receiver_name) as first_receiver_name,
        max(prelead_id) as prelead_id,
        max(qici_source) as qici_source,
        max(lead_grade_source) as lead_grade_source,
        max(prelead_purchase_intention_name) as prelead_purchase_intention_name,
        max(transfer_purchase_intention_name) as transfer_purchase_intention_name,
        max(first_receiver_time) as first_receiver_time,
        max(current_consultant_name) as current_consultant_name,
        max(current_consultant_source) as current_consultant_source,
        max(raw_rule_name) as raw_rule_name,
        max(tmk_assign_time) as tmk_assign_time,
        max(tmk_first_department) as tmk_first_department,
        max(tmk_second_department) as tmk_second_department,
        max(first_receiver_department) as first_receiver_department,
        max(current_private_candidate) as current_private_candidate,
        max(current_private_assign_time) as current_private_assign_time,
        max(current_private_is_active) as current_private_is_active,
        max(private_history_count) as private_history_count,
        max(transfer_lead_create_time) as transfer_lead_create_time,
        max(transfer_lead_period_name) as transfer_lead_period_name,
        max(app_snapshot_key) as app_snapshot_key,
        max(private_snapshot_key) as private_snapshot_key,
        max(lead_snapshot_key) as lead_snapshot_key,
        count(order_number) as matched_finance_row_count,
        count(distinct order_number) as matched_order_count,
        max(coalesce(is_deal_order, 0)) as has_deal,
        nullif(
            array_join(
                array_sort(
                    array_agg(
                        distinct nullif(
                            trim(cast(performance_consultant_name as varchar)),
                            ''
                        )
                    )
                ),
                ','
            ),
            ''
        ) as performance_consultant_names,
        nullif(
            array_join(
                array_sort(
                    array_agg(distinct nullif(trim(cast(deal_grade as varchar)), ''))
                ),
                ','
            ),
            ''
        ) as deal_grade,
        nullif(
            array_join(
                array_sort(
                    array_agg(distinct nullif(trim(cast(deal_subject as varchar)), ''))
                ),
                ','
            ),
            ''
        ) as deal_subject,
        nullif(
            array_join(
                array_sort(
                    array_agg(
                        distinct nullif(trim(cast(deal_main_teacher as varchar)), '')
                    )
                ),
                ','
            ),
            ''
        ) as deal_main_teacher,
        round(
            sum(case when is_deal_order = 1 then deal_amount_yuan else 0.0 end),
            2
        ) as deal_amount_yuan,
        round(
            sum(case when is_deal_order = 1 then refund_amount_yuan else 0.0 end),
            2
        ) as refund_amount_yuan,
        round(
            sum(case when is_deal_order = 1 then net_amount_yuan else 0.0 end),
            2
        ) as net_amount_yuan,
        nullif(
            array_join(
                array_sort(array_agg(distinct deal_attribution_type)),
                ','
            ),
            ''
        ) as deal_attribution_type,
        nullif(
            array_join(
                array_sort(array_agg(distinct deal_time_relation)),
                ','
            ),
            ''
        ) as deal_time_relation,
        max(finance_snapshot_key) as finance_snapshot_key
    from order_candidate_ranked
    where transfer_chain_rn = 1
    group by transfer_lead_id
)
select
    o.qici,
    o.assign_day,
    o.tmk_consultant_name,
    o.xiaozu,
    o.user_id,
    cast(o.transfer_lead_id as varchar) as transfer_lead_id,
    o.lead_grade,
    cast(1 as bigint) as lead_count,
    cast(
        case when coalesce(o.has_deal, 0) = 1 then 1 else 0 end
        as bigint
    ) as deal_lead_count,
    o.lead_channel,
    o.channel_map_1,
    o.channel_map_2,
    o.first_receiver_name,
    o.deal_grade,
    o.deal_subject,
    o.deal_main_teacher,
    case
        when coalesce(o.matched_order_count, 0) = 0 then cast(null as double)
        else o.deal_amount_yuan
    end as deal_amount,
    case
        when coalesce(o.matched_order_count, 0) = 0 then cast(null as double)
        else o.refund_amount_yuan
    end as refund_amount,
    case
        when coalesce(o.matched_order_count, 0) = 0 then cast(null as double)
        else o.net_amount_yuan
    end as net_amount,
    o.prelead_id,
    o.lead_grade_source,
    o.prelead_purchase_intention_name,
    o.transfer_purchase_intention_name,
    o.current_consultant_name,
    o.current_consultant_source,
    o.performance_consultant_names,
    o.matched_order_count,
    o.raw_rule_name,
    o.tmk_assign_time,
    o.tmk_first_department,
    o.tmk_second_department,
    o.first_receiver_department
from order_attribution o
