with vd as (
    select
        rule_name,
        employee_email_name,
        sum(lead_count) as lead,
        sum(valid_lead_count) as valid_lead
    from bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df
    where dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
      and hour = format_datetime(now() - interval '3' hour, 'HH')
      and section_assign_employee_first_level_department_name = 'H业务线'
      and section_assign_employee_second_level_department_name = '市场部'
      and period_mapping_first_level_department_name = 'H业务线'
    group by 1, 2
),
rule_base as (
    select
        f.plan_id,
        f.group_id,
        case
            when regexp_like(f.rule_name, '^[0-9]{4}期-') then split_part(f.rule_name, '-', 1)
            when regexp_like(f.rule_name, '^[0-9]{4}年-[0-9]{4}期-') then split_part(f.rule_name, '-', 2)
            else split_part(f.rule_name, '-', 1)
        end as group_period_name,
        split_part(f.rule_name, '-', 3) as qudao,
        split_part(f.rule_name, '-', 4) as nianji,
        f.rule_name,
        f.rule_id,
        f.purchase_intention_id
    from service_dw.dim_crm_assign_rule_lead_detail_hf f
    where f.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
      and f.hour = format_datetime(now() - interval '3' hour, 'HH')
),
fp_base as (
    select
        rb.plan_id,
        pl.group_id,
        rb.group_period_name,
        rb.qudao,
        rb.nianji,
        rb.rule_name,
        rb.purchase_intention_id,
        t.employee_email_name,
        max(
            case
                when t.employee_state = '0' then '未知'
                when t.employee_state = '1' then '可分配'
                when t.employee_state = '2' then '离职'
                when t.employee_state = '3' then '分配达到上限'
                else '兜底顾问'
            end
        ) as employee_state_1,
        max(try_cast(t.assign_lead_count as double)) as raw_assign_lead_count,
        max(try_cast(jg.goal as double)) as goal_assign_lead_count,
        max(
            case
                when t.employee_is_enable = '0' then '启用'
                when t.employee_is_enable = '1' then '禁用'
                else '未知'
            end
        ) as employee_is_enable
    from rule_base rb
    left join service_dw.dim_crm_assign_rule_plan_item_info_hf t
      on rb.rule_id = t.rule_id
     and rb.plan_id = t.plan_id
     and t.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
     and t.hour = format_datetime(now() - interval '3' hour, 'HH')
     and t.is_del = '0'
    left join temp_table.dingxi01_plan_id pl
      on pl.group_id = rb.group_id
     and pl.qici = rb.group_period_name
     and pl.year = 2026
    left join temp_table.dingxi01_jinliang_goal jg
      on jg.channel_2 = rb.qudao
     and jg.grade = rb.nianji
     and jg.qici = rb.group_period_name
    where pl.group_id is not null
    group by 1, 2, 3, 4, 5, 6, 7, 8
),
merged as (
    select
        fp_base.*,
        db.xiaozu,
        db.jingli,
        vd.lead,
        vd.valid_lead,
        count(*) over (
            partition by fp_base.group_period_name, fp_base.qudao, fp_base.nianji
        ) as goal_row_cnt
    from fp_base
    left join vd
      on vd.rule_name = fp_base.rule_name
     and vd.employee_email_name = fp_base.employee_email_name
    left join (
        select
            *,
            substr(qici, -5) as qici_0
        from temp_table.dingxi01_jiagou_db
    ) db
      on db.employee_email_name = fp_base.employee_email_name
     and db.qici_0 = fp_base.group_period_name
)
select
    plan_id,
    group_id,
    group_period_name,
    qudao,
    nianji,
    rule_name,
    purchase_intention_id,
    employee_email_name,
    employee_state_1,
    case
        when substr(group_period_name, 1, 4) >= '0522'
         and goal_assign_lead_count is not null
         and goal_row_cnt > 0
        then goal_assign_lead_count / goal_row_cnt
        else raw_assign_lead_count
    end as assign_lead_count,
    employee_is_enable,
    xiaozu,
    jingli,
    lead,
    valid_lead
from merged
order by 1, 2, 3, 4
