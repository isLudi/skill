with koc_channel_scope as (
    select '自孵化KOC-5元纯课' as source_channel, '自孵化KOC' as broadcast_channel, 1 as sort_order
    union all
    select 'KOC-周帅数学' as source_channel, 'KOC-周帅数学' as broadcast_channel, 2 as sort_order
    union all
    select 'KOC-孟亚飞数学' as source_channel, 'KOC-孟亚飞数学' as broadcast_channel, 3 as sort_order
),
biz_qici_calendar as (
    select *
    from (
        values
            ('20260716期', date '2026-07-14', date '2026-07-19'),
            ('20260722期', date '2026-07-20', date '2026-07-24'),
            ('20260728期', date '2026-07-26', date '2026-07-30'),
            ('20260803期', date '2026-08-01', date '2026-08-05'),
            ('20260809期', date '2026-08-07', date '2026-08-11')
    ) as t(qici, start_date, end_date)
),
lead_base as (
    select distinct
        coalesce(
            cal.qici,
            concat(
                date_format(
                    date_trunc(
                        'week',
                        date_parse(replace(concat(t1.group_period_year, t1.group_period_term), '期', ''), '%Y%m%d')
                          - interval '1' day
                    ) + interval '4' day,
                    '%Y%m%d'
                ),
                '期'
            )
        ) as period_name,
        t1.virtual_fourth_department_name as department,
        t1.virtual_leader_email_name as raw_manager_name,
        t1.virtual_direct_leader_email_name as raw_group_name,
        t1.employee_email_name,
        t1.employee_email_prefix,
        t1.lead_id,
        t1.user_id,
        t1.rule_name,
        t1.flow_pool_name,
        t1.third_department_name,
        t1.sku_id_name,
        t1.source_manager_name,
        t1.channel_name_2,
        t1.virtual_second_department_name,
        t1.lead_purchase_intention_level2_category_name,
        t1.lead_create_time,
        coalesce(t1.valid_lead_count, 0) as valid_lead_count
    from bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df t1
    left join biz_qici_calendar cal
      on cast(date_parse(replace(concat(t1.group_period_year, t1.group_period_term), '期', ''), '%Y%m%d') as date)
         between cal.start_date and cal.end_date
    where t1.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
      and t1.hour = format_datetime(now() - interval '3' hour, 'HH')
      and t1.section_assign_employee_first_level_department_name = 'H业务线'
      and t1.section_assign_employee_second_level_department_name = '市场部'
      and t1.section_assign_employee_third_level_department_name = '市场顾问部'
      and t1.period_mapping_first_level_department_name = 'H业务线'
),
lead_with_channel as (
    select
        lb.*,
        case
            when lb.flow_pool_name = '中考加油'
             and lb.sku_id_name like '%孟帝%' then 'KOC-孟亚飞数学'
            when lb.flow_pool_name = '中考加油'
             and lb.sku_id_name like '%帅师%' then 'KOC-周帅数学'
            when lb.source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07')
             and (
                    lb.sku_id_name like '%孟帝%'
                 or lb.sku_id_name like '%dudu%'
                 or lb.sku_id_name like '%市场初二%'
                 or lb.rule_name like '%亚飞%'
                 or lb.sku_id_name like '%初二高阳%'
                 or lb.sku_id_name like '%高阳初二%'
                 or lb.sku_id_name like '%精品初二%'
                 or lb.sku_id_name like '%菁英初三%'
                 or (
                        lb.virtual_second_department_name = '菁英班学部'
                    and lb.lead_purchase_intention_level2_category_name = '初级'
                    and lb.lead_create_time >= '2026-04-15 00:00:00'
                    )
                ) then 'KOC-孟亚飞数学'
            when lb.source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07')
             and (
                    lb.sku_id_name like '%帅师%'
                 or lb.rule_name like '%周帅%'
                 or lb.sku_id_name like '%9月升高三%'
                ) then 'KOC-周帅数学'
            when lb.third_department_name in ('品牌效能部','KOC孵化部')
             and lb.channel_name_2 in ('抖音','视频号','快手','KOL') then '自孵化KOC-5元纯课'
            when lb.flow_pool_name like '%自然流%'
             and lb.source_manager_name in ('赵语诗','崔文轩','孙培尧') then '自孵化KOC-5元纯课'
        end as source_channel
    from lead_base lb
),
koc_leads as (
    select
        lwc.period_name,
        lwc.department,
        lwc.raw_manager_name,
        lwc.raw_group_name,
        lwc.employee_email_name,
        lwc.employee_email_prefix,
        lwc.lead_id,
        lwc.user_id,
        lwc.valid_lead_count,
        kcs.source_channel,
        kcs.broadcast_channel,
        kcs.sort_order
    from lead_with_channel lwc
    join koc_channel_scope kcs
      on lwc.source_channel = kcs.source_channel
    where lwc.period_name > '20260424期'
),
call_c as (
    select
        wf.user_number,
        wf.lead_id,
        wf.section_assign_employee_email_prefix,
        max(case when wf.call_duration > 300 then 1 else 0 end) as is_long_call
    from service_dw.app_h_crm_lead_employee_workload_detail_hf wf
    where wf.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
      and wf.hour = format_datetime(now() - interval '3' hour, 'HH')
    group by
        wf.user_number,
        wf.lead_id,
        wf.section_assign_employee_email_prefix
),
zx_active as (
    select
        employee_email_name,
        xiaozu,
        jingli
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
),
koc_leads_with_manager as (
    select
        kl.period_name,
        kl.source_channel,
        kl.broadcast_channel,
        kl.sort_order,
        coalesce(jg.jingli, zx.jingli, kl.raw_manager_name) as manager_name,
        kl.valid_lead_count,
        case
            when kl.valid_lead_count > 0 then coalesce(cc.is_long_call, 0)
            else 0
        end as is_long_call
    from koc_leads kl
    left join call_c cc
      on cc.user_number = kl.user_id
     and cc.lead_id = kl.lead_id
     and cc.section_assign_employee_email_prefix = kl.employee_email_prefix
    left join temp_table.dingxi01_jiagou_db jg
      on jg.qici = kl.period_name
     and jg.department = kl.department
     and jg.xiaozu = kl.raw_group_name
     and jg.employee_email_name = kl.employee_email_name
    left join zx_active zx
      on zx.employee_email_name = kl.employee_email_name
),
period_rank as (
    select
        period_name,
        dense_rank() over (order by period_name desc) as period_rank
    from (
        select distinct period_name
        from lead_base
        where period_name > '20260424期'
    ) p
),
koc_manager_base as (
    select
        klwm.period_name as qici,
        klwm.source_channel,
        klwm.broadcast_channel,
        klwm.sort_order,
        nullif(trim(cast(klwm.manager_name as varchar)), '') as manager_name,
        sum(klwm.valid_lead_count) as valid_lead_count,
        sum(klwm.is_long_call) as long_call_count,
        coalesce(
            sum(klwm.is_long_call) * 1.0000 / nullif(sum(klwm.valid_lead_count), 0),
            0
        ) as rate_long_call
    from koc_leads_with_manager klwm
    join period_rank pr
      on klwm.period_name = pr.period_name
    where pr.period_rank <= 2
      and nullif(trim(cast(klwm.manager_name as varchar)), '') is not null
      and nullif(trim(cast(klwm.manager_name as varchar)), '') <> '未知'
    group by
        klwm.period_name,
        klwm.source_channel,
        klwm.broadcast_channel,
        klwm.sort_order,
        nullif(trim(cast(klwm.manager_name as varchar)), '')
    having sum(klwm.valid_lead_count) > 5
),
koc_manager_with_avg as (
    select
        *,
        coalesce(
            avg(rate_long_call) over (partition by qici, source_channel),
            0
        ) as rate_long_call_manager_avg_value,
        coalesce(
            sum(long_call_count) over (partition by qici, source_channel) * 1.0000
            / nullif(sum(valid_lead_count) over (partition by qici, source_channel), 0),
            0
        ) as rate_long_call_weighted_avg_value,
        dense_rank() over (
            partition by qici, source_channel
            order by rate_long_call asc, manager_name asc
        ) as rank_rate_long_call
    from koc_manager_base
),
koc_channel_broadcast as (
    select
        qici,
        case
            when regexp_like(qici, '^20[0-9]{6}期$') then substr(qici, 5)
            else qici
        end as qici_short,
        source_channel,
        broadcast_channel,
        sort_order,
        count(*) as manager_count,
        sum(valid_lead_count) as valid_lead_count,
        sum(long_call_count) as long_call_count,
        max(rate_long_call_manager_avg_value) as rate_long_call_manager_avg_value,
        max(rate_long_call_weighted_avg_value) as rate_long_call_weighted_avg_value,
        array_join(
            array_distinct(
                array_agg(
                    case when rank_rate_long_call = 1 then manager_name end
                    order by rate_long_call, manager_name
                )
            ),
            '、'
        ) as rate_long_call_lowest_manager_list,
        min(case when rank_rate_long_call = 1 then rate_long_call end) as rate_long_call_lowest_value,
        min(case when rank_rate_long_call = 1 then rate_long_call end)
            - max(rate_long_call_manager_avg_value) as rate_long_call_lowest_diff,
        coalesce(
            nullif(
                array_join(
                    array_distinct(
                        array_agg(
                            case
                                when rate_long_call < rate_long_call_manager_avg_value then manager_name
                            end
                            order by rate_long_call, manager_name
                        )
                    ),
                    '、'
                ),
                ''
            ),
            '无'
        ) as rate_long_call_below_avg_manager_list,
        coalesce(
            nullif(
                array_join(
                    array_distinct(
                        array_agg(
                            case
                                when rate_long_call < rate_long_call_manager_avg_value then
                                    concat(
                                        manager_name,
                                        '(',
                                        cast(round(rate_long_call * 100, 2) as varchar),
                                        '%)'
                                    )
                            end
                            order by rate_long_call, manager_name
                        )
                    ),
                    '、'
                ),
                ''
            ),
            '无'
        ) as rate_long_call_below_avg_manager_detail
    from koc_manager_with_avg
    group by
        qici,
        case
            when regexp_like(qici, '^20[0-9]{6}期$') then substr(qici, 5)
            else qici
        end,
        source_channel,
        broadcast_channel,
        sort_order
),
koc_channel_broadcast_text_detail as (
    select
        qici,
        '市场顾问部' as department,
        qici_short,
        source_channel,
        broadcast_channel,
        broadcast_channel as channel_map_1,
        sort_order,
        manager_count,
        valid_lead_count,
        long_call_count,
        cast(round(coalesce(rate_long_call_manager_avg_value, 0), 4) as decimal(12, 4)) as rate_long_call_avg_value,
        cast(round(coalesce(rate_long_call_manager_avg_value, 0) * 100, 2) as decimal(10, 2)) as rate_long_call_avg_pct,
        concat(cast(cast(round(coalesce(rate_long_call_manager_avg_value, 0) * 100, 2) as decimal(10, 2)) as varchar), '%') as rate_long_call_avg_text,
        cast(round(coalesce(rate_long_call_weighted_avg_value, 0), 4) as decimal(12, 4)) as rate_long_call_weighted_avg_value,
        cast(round(coalesce(rate_long_call_weighted_avg_value, 0) * 100, 2) as decimal(10, 2)) as rate_long_call_weighted_avg_pct,
        concat(cast(cast(round(coalesce(rate_long_call_weighted_avg_value, 0) * 100, 2) as decimal(10, 2)) as varchar), '%') as rate_long_call_weighted_avg_text,
        rate_long_call_lowest_manager_list,
        cast(round(coalesce(rate_long_call_lowest_value, 0), 4) as decimal(12, 4)) as rate_long_call_lowest_value,
        cast(round(coalesce(rate_long_call_lowest_value, 0) * 100, 2) as decimal(10, 2)) as rate_long_call_lowest_pct,
        concat(cast(cast(round(coalesce(rate_long_call_lowest_value, 0) * 100, 2) as decimal(10, 2)) as varchar), '%') as rate_long_call_lowest_text,
        cast(round(coalesce(rate_long_call_lowest_diff, 0), 4) as decimal(12, 4)) as rate_long_call_lowest_diff,
        cast(round(coalesce(rate_long_call_lowest_diff, 0) * 100, 2) as decimal(10, 2)) as rate_long_call_lowest_diff_pct,
        coalesce(rate_long_call_below_avg_manager_detail, '无') as rate_long_call_below_avg_jingli_list,
        coalesce(rate_long_call_below_avg_manager_detail, '无') as rate_long_call_below_avg_xiaozu_list,
        coalesce(rate_long_call_below_avg_manager_list, '无') as rate_long_call_below_avg_jingli_name_list,
        concat(
            broadcast_channel,
            ' 5min率均值为 ',
            concat(cast(cast(round(coalesce(rate_long_call_manager_avg_value, 0) * 100, 2) as decimal(10, 2)) as varchar), '%'),
            '，低于平均值的经理：',
            coalesce(rate_long_call_below_avg_manager_detail, '无')
        ) as broadcast_line_text
    from koc_channel_broadcast
),
koc_channel_broadcast_text_qici as (
    select
        qici,
        department,
        array_join(array_agg(broadcast_line_text order by sort_order), chr(10)) as broadcast_text_by_qici
    from koc_channel_broadcast_text_detail
    group by qici, department
)
select
    dt.qici,
    dt.department,
    dt.qici_short,
    dt.source_channel,
    dt.broadcast_channel,
    dt.channel_map_1,
    dt.sort_order,
    dt.manager_count,
    dt.valid_lead_count,
    dt.long_call_count,
    dt.rate_long_call_avg_value,
    dt.rate_long_call_avg_pct,
    dt.rate_long_call_avg_text,
    dt.rate_long_call_weighted_avg_value,
    dt.rate_long_call_weighted_avg_pct,
    dt.rate_long_call_weighted_avg_text,
    dt.rate_long_call_lowest_manager_list,
    dt.rate_long_call_lowest_value,
    dt.rate_long_call_lowest_pct,
    dt.rate_long_call_lowest_text,
    dt.rate_long_call_lowest_diff,
    dt.rate_long_call_lowest_diff_pct,
    dt.rate_long_call_below_avg_jingli_list,
    dt.rate_long_call_below_avg_xiaozu_list,
    dt.rate_long_call_below_avg_jingli_name_list,
    dt.broadcast_line_text,
    qt.broadcast_text_by_qici
from koc_channel_broadcast_text_detail dt
left join koc_channel_broadcast_text_qici qt
  on dt.qici = qt.qici
 and dt.department = qt.department
order by qici, sort_order
