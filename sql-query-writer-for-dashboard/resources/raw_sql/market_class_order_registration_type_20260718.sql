with scoped as (
    select
        cast(t.order_number as varchar) as order_number,
        cast(t.bind_main_order_number as varchar) as bind_main_order_number,
        cast(t.activity_number as varchar) as activity_number,
        cast(t.original_order_activity_number as varchar) as original_order_activity_number,
        cast(t.original_order_user_number as varchar) as original_order_user_number,
        t.bind_type,
        t.clazz_biz_number as class_id,
        t.clazz_name as class_name,
        t.school_year,
        t.school_term_code,
        t.school_term_name,
        t.pay_success_timestamp,
        t.is_pay_success_order
    from service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf t
    where t.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
      and t.hour = format_datetime(now() - interval '2' hour, 'HH')
      and t.performance_first_level_department_name = 'H业务线'
      and t.performance_second_level_department_name = '市场部'
      and t.performance_third_level_department_name = '市场顾问部'
      and t.course_first_level_department_name = 'H业务线'
      and t.course_second_level_department_name in (
          '精品班学部',
          '市场部',
          '青橙项目部',
          '菁英班学部',
          '本地化大班学部',
          '一对一学部'
      )
      and t.trade_period_mapping_first_level_department_name = 'H业务线'
      and t.pay_period_mapping_first_level_department_name = 'H业务线'
),
target_rows as (
    select
        s.order_number,
        s.class_id,
        s.class_name,
        s.original_order_user_number,
        s.bind_type,
        s.bind_main_order_number,
        s.activity_number,
        s.original_order_activity_number,
        s.school_year,
        s.school_term_code,
        s.school_term_name
    from scoped s
    where s.class_id in (
          '23HXTS26Q22E11001',
          '23SXTS26Q9CJ11001',
          '23SXTS26QSUM11001',
          '23WLTS26QZEB11001',
          '23YWTS26Q51111001',
          '23YYTS26Q0X311001'
      )
      and s.is_pay_success_order = 1
      and s.pay_success_timestamp > timestamp '2026-05-03 19:30:00'
),
order_class as (
    select
        r.order_number,
        r.class_id,
        max(r.class_name) as class_name,
        max(r.original_order_user_number) as original_order_user_number,
        max(r.school_year) as school_year,
        max(r.school_term_code) as school_term_code,
        max(r.school_term_name) as school_term_name,
        max(case when r.bind_type = 2 then 1 else 0 end) as has_bundle_child,
        max(case when r.bind_type = 1 then 1 else 0 end) as has_bundle_main,
        max(case when r.bind_type = 0 then 1 else 0 end) as has_normal_order,
        max(r.bind_main_order_number) as bind_main_order_number,
        max(r.activity_number) as activity_number,
        max(r.original_order_activity_number) as original_order_activity_number,
        count(*) as service_row_count
    from target_rows r
    group by r.order_number, r.class_id
)
select
    o.order_number,
    o.class_id,
    o.class_name,
    o.original_order_user_number,
    case
        when o.school_year = 2026
         and o.school_term_code = 'Q'
         and (o.has_bundle_child = 1 or o.has_bundle_main = 1)
            then '暑秋联报'
        when o.school_year = 2026
         and o.school_term_code = 'Q'
         and o.has_bundle_child = 0
         and o.has_bundle_main = 0
         and o.has_normal_order = 1
            then '单独秋季'
        else '待核实'
    end as registration_type,
    case
        when o.has_bundle_child = 1 then '2-联报从课'
        when o.has_bundle_main = 1 then '1-联报主课'
        when o.has_normal_order = 1 then '0-普通订单'
        else '未知'
    end as bind_type_evidence,
    o.bind_main_order_number,
    o.activity_number,
    o.original_order_activity_number,
    o.school_year,
    o.school_term_code,
    o.school_term_name,
    case
        when o.school_year = 2026
         and o.school_term_code = 'Q'
         and o.has_bundle_child = 1
            then '2026秋季班(Q)+联报从课(bind_type=2)'
        when o.school_year = 2026
         and o.school_term_code = 'Q'
         and o.has_bundle_main = 1
            then '2026秋季班(Q)+联报主课(bind_type=1)'
        when o.school_year = 2026
         and o.school_term_code = 'Q'
         and o.has_normal_order = 1
            then '2026秋季班(Q)+普通订单(bind_type=0)'
        else '订单类型或学季不足'
    end as classification_basis,
    o.service_row_count
from order_class o
order by o.class_id, o.order_number
