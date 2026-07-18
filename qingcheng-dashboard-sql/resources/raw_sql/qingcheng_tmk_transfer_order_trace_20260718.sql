with
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
dwd_transfer_all as (
    select distinct
        p.prelead_id,
        p.prelead_user_id,
        p.prelead_purchase_intention_name,
        cast(l.crm_leads_id as bigint) as transfer_lead_id,
        cast(l.user_id as bigint) as transfer_user_id
    from dwd_prelead p
    join data_lake_fuwu.dwd_crm_leads_rt l
      on cast(l.previous_model_id as bigint) = p.prelead_id
    where l.model_type = 0
      and l.previous_model_id > 0
),
prelead_raw as (
    select
        p.prelead_id,
        coalesce(cast(f.user_id as bigint), p.prelead_user_id) as user_id,
        p.prelead_purchase_intention_name,
        f.employee_email_name as tmk_employee_name,
        f.employee_email_prefix as tmk_employee_email_prefix,
        f.rule_name as raw_rule_name,
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
        coalesce(
            f.stats_grade_name,
            f.lead_purchase_intention_level2_category_name,
            case
                when p.prelead_purchase_intention_name like '%高一%' then '高一'
                when p.prelead_purchase_intention_name like '%高二%' then '高二'
                when p.prelead_purchase_intention_name like '%高三%' then '高三'
                when p.prelead_purchase_intention_name like '%高中预科%' then '高中预科'
            end
        ) as lead_grade,
        case
            when f.rule_name like '%武汉图书%' then '武汉图书'
            when f.rule_name like '%公域%' then '公域'
            when f.rule_name like '%首期掉海%' then '首期掉海'
            when f.rule_name like '%未加好友%'
              or p.prelead_purchase_intention_name like '规划系统%'
            then '未加好友'
            else '其他'
        end as tmk_channel_detail,
        coalesce(try_cast(f.valid_lead_count as bigint), 0) as valid_lead_count,
        row_number() over (
            partition by p.prelead_id
            order by
                coalesce(try_cast(f.valid_lead_count as bigint), 0) desc,
                case when f.rule_name is not null then 0 else 1 end,
                case when f.employee_email_name is not null then 0 else 1 end,
                f.section_assign_time desc,
                f.employee_email_prefix
        ) as prelead_rn
    from bdg_ba.app_crm_prelead_cost_gmv_full_link_data_hf f
    join dwd_prelead p
      on cast(f.lead_id as bigint) = p.prelead_id
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
),
prelead as (
    select *
    from prelead_raw
    where prelead_rn = 1
      and valid_lead_count > 0
      and tmk_employee_name is not null
      and qici >= '20260427期'
),
jg_base as (
    select qici, employee_email_name, department, dept_2, xiaozu
    from (
        select
            qici,
            employee_email_name,
            department,
            dept_2,
            xiaozu,
            row_number() over (
                partition by qici, employee_email_name
                order by department, dept_2, xiaozu
            ) as jg_rn
        from (
            select distinct qici, employee_email_name, department, dept_2, xiaozu
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
sec_transfer as (
    select
        p.prelead_id,
        p.user_id,
        p.tmk_employee_name,
        p.qici,
        p.lead_grade,
        p.tmk_channel_detail,
        p.raw_rule_name,
        t.transfer_lead_id,
        t.transfer_user_id
    from prelead p
    join jg_base jg
      on p.qici = jg.qici
     and p.tmk_employee_name = jg.employee_email_name
    join dwd_transfer_all t
      on p.prelead_id = t.prelead_id
    where jg.dept_2 = 'SEC'
),
lead_owner_raw as (
    select
        cast(f.lead_id as bigint) as transfer_lead_id,
        f.employee_email_name as receiver_employee_name,
        f.lead_purchase_intention_level2_category_name as receiver_lead_grade,
        row_number() over (
            partition by cast(f.lead_id as bigint)
            order by f.section_assign_time desc
        ) as owner_rn
    from bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df f
    join sec_transfer t
      on cast(f.lead_id as bigint) = t.transfer_lead_id
    where f.dt = format_datetime(current_timestamp - interval '2' hour, 'YYYYMMdd')
      and f.hour = format_datetime(current_timestamp - interval '2' hour, 'HH')
      and f.lead_model_type = 0
      and f.section_assign_employee_first_level_department_name = 'H业务线'
      and f.section_assign_employee_second_level_department_name = '青橙项目部'
      and f.period_mapping_first_level_department_name = 'H业务线'
),
lead_owner as (
    select transfer_lead_id, receiver_employee_name, receiver_lead_grade
    from lead_owner_raw
    where owner_rn = 1
),
transfer_period_raw as (
    select
        cast(s.lead_id as bigint) as transfer_lead_id,
        s.lead_create_time,
        s.lead_period_name,
        coalesce(
            cal.qici,
            concat(
                date_format(
                    date_trunc(
                        'week',
                        date_parse(
                            concat(
                                regexp_extract(s.lead_period_name, '(\d{4})年-(\d{4})期', 1),
                                regexp_extract(s.lead_period_name, '(\d{4})年-(\d{4})期', 2)
                            ),
                            '%Y%m%d'
                        ) - interval '1' day
                    ) + interval '4' day,
                    '%Y%m%d'
                ),
                '期'
            )
        ) as transfer_qici,
        row_number() over (
            partition by cast(s.lead_id as bigint)
            order by s.section_assign_time desc, s.lead_create_time desc
        ) as period_rn
    from service_dw.dm_crm_lead_stats_detail_hf s
    join sec_transfer t
      on cast(s.lead_id as bigint) = t.transfer_lead_id
    left join biz_qici_calendar cal
      on cast(
          try(
              date_parse(
                  concat(
                      regexp_extract(s.lead_period_name, '(\d{4})年-(\d{4})期', 1),
                      regexp_extract(s.lead_period_name, '(\d{4})年-(\d{4})期', 2)
                  ),
                  '%Y%m%d'
              )
          ) as date
      ) between cal.start_date and cal.end_date
    where s.dt = format_datetime(current_timestamp - interval '2' hour, 'YYYYMMdd')
      and s.hour = format_datetime(current_timestamp - interval '2' hour, 'HH')
      and s.mapping_first_level_department_name = 'H业务线'
      and s.mapping_second_level_department_name in (
          '精品班学部',
          '菁英班学部',
          '市场部',
          '本地化大班学部',
          '青橙项目部'
      )
      and s.lead_model_type = 0
),
transfer_period as (
    select transfer_lead_id, transfer_qici, lead_create_time, lead_period_name
    from transfer_period_raw
    where period_rn = 1
),
order_agg as (
    select
        cast(o.lead_id as bigint) as transfer_lead_id,
        max(case when coalesce(o.income_amount, 0) > 0 then 1 else 0 end) as has_deal,
        array_join(array_sort(array_agg(distinct cast(o.grade_name as varchar))), ',') as deal_grade,
        array_join(
            array_sort(
                array_agg(
                    distinct cast(coalesce(o.mapping_school_subject_name, o.school_subject_name) as varchar)
                )
            ),
            ','
        ) as deal_subject,
        array_join(array_sort(array_agg(distinct cast(o.main_teacher_nickname as varchar))), ',') as deal_main_teacher,
        round(sum(coalesce(cast(o.income_amount as double), 0.0)) / 100.0, 2) as income_amount_yuan,
        round(sum(coalesce(cast(o.refund_amount as double), 0.0)) / 100.0, 2) as refund_amount_yuan,
        round(
            sum(
                coalesce(cast(o.income_amount as double), 0.0)
                - coalesce(cast(o.refund_amount as double), 0.0)
            ) / 100.0,
            2
        ) as net_amount_yuan
    from service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf o
    join sec_transfer t
      on cast(o.lead_id as bigint) = t.transfer_lead_id
    where o.dt = format_datetime(current_timestamp - interval '2' hour, 'YYYYMMdd')
      and o.hour = format_datetime(current_timestamp - interval '2' hour, 'HH')
      and o.performance_second_level_department_name = '青橙项目部'
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
      and (coalesce(o.income_amount, 0) <> 0 or coalesce(o.refund_amount, 0) <> 0)
    group by cast(o.lead_id as bigint)
)
select
    t.tmk_employee_name as "tmk顾问姓名",
    coalesce(t.user_id, t.transfer_user_id) as "用户ID",
    t.transfer_lead_id as "转移线索ID",
    tp.transfer_qici as "转移期次",
    coalesce(t.lead_grade, lo.receiver_lead_grade) as "线索年级",
    1 as "线索数量",
    concat('订单复用/', t.tmk_channel_detail) as "线索渠道",
    lo.receiver_employee_name as "线索承接顾问",
    case
        when oa.transfer_lead_id is null then '业财未回补'
        when coalesce(oa.has_deal, 0) = 1 then '是'
        else '否'
    end as "转移线索是否成交",
    oa.deal_grade as "成交年级",
    oa.deal_subject as "成交科目",
    oa.deal_main_teacher as "成交主讲",
    oa.income_amount_yuan as "成交金额",
    oa.refund_amount_yuan as "退费金额",
    oa.net_amount_yuan as "净金额"
from sec_transfer t
left join lead_owner lo
  on lo.transfer_lead_id = t.transfer_lead_id
left join transfer_period tp
  on tp.transfer_lead_id = t.transfer_lead_id
left join order_agg oa
  on oa.transfer_lead_id = t.transfer_lead_id
order by "线索渠道", "线索年级", "tmk顾问姓名", "转移线索ID"
limit 200
