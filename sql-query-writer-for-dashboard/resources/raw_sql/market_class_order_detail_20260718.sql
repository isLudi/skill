with base as (
    select
        t.id,
        cast(t.order_number as varchar) as order_number,
        cast(t.user_id as varchar) as user_id,
        t.clazz_biz_number,
        t.clazz_name,
        t.biz_number,
        t.subclazz_name,
        t.course_subject,
        case
            when t.course_subject like '%语文%' then '语文'
            when t.course_subject like '%数学%' then '数学'
            when t.course_subject like '%英语%' or t.course_subject like '%英文%' then '英语'
            when t.course_subject like '%物理%' then '物理'
            when t.course_subject like '%化学%' then '化学'
            else t.course_subject
        end as subject,
        t.course_grade,
        t.course_year,
        t.course_term_id,
        t.teacher_name,
        t.order_paid_time,
        t.trade_time,
        t.order_status,
        t.trade_type,
        t.trade_status,
        t.order_price,
        t.real_price,
        t.price,
        t.employee_email_name,
        t.leader_employee_email_name,
        t.dt as source_dt,
        t.hour as source_hour
    from finance_dw.app_finance_performance_extend_details_hf t
    where t.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
      and t.hour = format_datetime(now() - interval '2' hour, 'HH')
      and t.employee_first_level_department_name = 'H业务线'
      and t.employee_second_level_department_name = '市场部'
      and t.employee_third_level_department_name = '市场顾问部'
      and t.clazz_biz_number in (
          '23HXTS26Q22E11001',
          '23SXTS26Q9CJ11001',
          '23SXTS26QSUM11001',
          '23WLTS26QZEB11001',
          '23YWTS26Q51111001',
          '23YYTS26Q0X311001'
      )
      and try_cast(t.order_paid_time as timestamp) > timestamp '2026-05-03 19:30:00'
),
order_class_detail as (
    select
        b.order_number,
        b.clazz_biz_number,
        max_by(b.user_id, b.id) as user_id,
        max_by(b.clazz_name, b.id) as clazz_name,
        max_by(b.biz_number, b.id) as biz_number,
        max_by(b.subclazz_name, b.id) as subclazz_name,
        max_by(b.subject, b.id) as subject,
        max_by(b.course_subject, b.id) as course_subject_raw,
        max_by(b.course_grade, b.id) as course_grade,
        max_by(b.course_year, b.id) as course_year,
        max_by(b.course_term_id, b.id) as course_term_id,
        max_by(b.teacher_name, b.id) as teacher_name,
        min(b.order_paid_time) as order_paid_time,
        max(b.trade_time) as latest_trade_time,
        max_by(b.order_status, b.id) as order_status,
        round(max(b.order_price), 2) as order_price,
        round(sum(case
            when b.trade_type = '正常订单' and b.trade_status = '支付' then b.price
            else 0
        end), 2) as paid_performance_amount,
        round(-sum(case
            when b.trade_type = '正常订单' and b.price < 0 then b.price
            else 0
        end), 2) as refund_performance_amount,
        round(sum(case
            when b.trade_type = '正常订单' then b.price
            else 0
        end), 2) as net_performance_amount,
        array_join(array_agg(distinct b.employee_email_name), ',') as consultant_names,
        array_join(array_agg(distinct b.leader_employee_email_name), ',') as leader_names,
        count(distinct b.id) as performance_detail_id_count,
        count(*) as raw_event_row_count,
        max(b.source_dt) as source_dt,
        max(b.source_hour) as source_hour
    from base b
    group by
        b.order_number,
        b.clazz_biz_number
    having sum(case
        when b.trade_type = '正常订单' and b.trade_status = '支付' then 1
        else 0
    end) > 0
)
select
    d.subject,
    d.clazz_biz_number as class_id,
    d.clazz_name as class_name,
    d.order_number,
    d.user_id as student_id,
    d.order_paid_time,
    d.order_status,
    d.order_price,
    d.paid_performance_amount,
    d.refund_performance_amount,
    d.net_performance_amount,
    d.course_subject_raw,
    d.course_grade,
    d.course_year,
    d.course_term_id,
    d.teacher_name,
    d.biz_number as sub_class_id,
    d.subclazz_name as sub_class_name,
    d.consultant_names,
    d.leader_names,
    d.latest_trade_time,
    d.performance_detail_id_count,
    d.raw_event_row_count,
    d.source_dt,
    d.source_hour
from order_class_detail d
order by
    d.subject,
    d.clazz_biz_number,
    d.order_paid_time,
    d.order_number
