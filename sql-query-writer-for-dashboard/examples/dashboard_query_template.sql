-- 看板型查询模板：按期次、渠道、员工聚合
with base_data as (
    select
        t.lead_id,
        t.user_id,
        t.lead_period_name,
        t.channel_name_1,
        t.employee_id,
        t.first_department_name
    from service_dw.dm_crm_lead_stats_detail_hf t
    where t.dt = 'YYYYMMDD'
      and t.hour = 'HH'
      and t.first_department_name = '<一级部门名称>'
),
final_agg as (
    select
        b.lead_period_name,
        b.channel_name_1,
        b.employee_id,
        count(distinct b.lead_id) as lead_cnt,
        count(distinct case when 待确认有效线索条件 then b.lead_id end) as valid_lead_cnt
    from base_data b
    group by
        b.lead_period_name,
        b.channel_name_1,
        b.employee_id
)
select *
from final_agg
limit 1000;
