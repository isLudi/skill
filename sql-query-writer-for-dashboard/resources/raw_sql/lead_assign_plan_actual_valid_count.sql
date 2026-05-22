-------实际有效数量
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
group by
    rule_name,
    employee_email_name
)
-------计划分配数量
,fp as (
select
    f.plan_id,
    pl.group_id,
    split_part(f.rule_name, '-', 1) as group_period_name,
    split_part(f.rule_name, '-', 3) as qudao,
    split_part(f.rule_name, '-', 4) as nianji,
    f.rule_name,
    f.purchase_intention_id,
    t.employee_email_name,
    case
        when t.employee_state = '0' then '未知'
        when t.employee_state = '1' then '可分配'
        when t.employee_state = '2' then '离职'
        when t.employee_state = '3' then '分配达到上限'
        else '兜底顾问'
    end as employee_state_1,
    t.assign_lead_count,
    t.assign_ceiling_count,
    case
        when t.employee_is_enable = '0' then '启用'
        when t.employee_is_enable = '1' then '禁用'
        else '未知'
    end as employee_is_enable
from service_dw.dim_crm_assign_rule_lead_detail_hf f
left join service_dw.dim_crm_assign_rule_plan_item_info_hf t
  on f.rule_id = t.rule_id
 and f.plan_id = t.plan_id
 and t.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
 and t.hour = format_datetime(now() - interval '2' hour, 'HH')
 and t.is_del = '0'
left join temp_table.dingxi01_plan_id pl
  on pl.group_id = f.group_id
where f.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
  and f.hour = format_datetime(now() - interval '2' hour, 'HH')
  and pl.group_id is not null
group by
    f.plan_id,
    pl.group_id,
    split_part(f.rule_name, '-', 1),
    split_part(f.rule_name, '-', 3),
    split_part(f.rule_name, '-', 4),
    f.rule_name,
    f.purchase_intention_id,
    t.employee_email_name,
    case
        when t.employee_state = '0' then '未知'
        when t.employee_state = '1' then '可分配'
        when t.employee_state = '2' then '离职'
        when t.employee_state = '3' then '分配达到上限'
        else '兜底顾问'
    end,
    t.assign_lead_count,
    t.assign_ceiling_count,
    case
        when t.employee_is_enable = '0' then '启用'
        when t.employee_is_enable = '1' then '禁用'
        else '未知'
    end
order by 1, 2, 3, 4
)
----合并数据
select
    fp.*,
    db.xiaozu,
    db.jingli,
    vd.lead,
    vd.valid_lead
from fp
left join vd
  on vd.rule_name = fp.rule_name
 and vd.employee_email_name = fp.employee_email_name
left join (
    select
        *,
        substr(qici, -5) as qici_0
    from temp_table.dingxi01_jiagou_db
) db
  on db.employee_email_name = fp.employee_email_name
 and db.qici_0 = fp.group_period_name
