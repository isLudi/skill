-- TT/V/T scoped alternative: 26 source-backed columns; biz_type/goods_type unavailable.
SELECT format_datetime(trade_timestamp,'yyyyMMdd') AS dt,
       trade_timestamp AS trade_timestamp,
       pay_success_timestamp AS order_timestamp,
       cast(order_number AS varchar) AS order_number,
       cast(original_order_number AS varchar) AS original_order_number,
       cast(original_order_user_number AS varchar) AS user_number,
       cast(course_number AS varchar) AS course_number,
       course_name AS course_name,
       course_first_level_subject_name AS course_first_level_subject_name,
       course_second_level_subject_name AS course_second_level_subject_name,
       course_third_level_subject_name AS course_third_level_subject_name,
       course_top_level_department_name AS course_top_level_department_name,
       course_first_level_department_name AS course_first_level_department_name,
       course_second_level_department_name AS course_second_level_department_name,
       course_third_level_department_name AS course_third_level_department_name,
       cast(performance_employee_id AS varchar) AS performance_employee_id,
       performance_employee_email_name AS performance_employee_email_name,
       performance_top_level_department_name AS performance_top_level_department_name,
       performance_first_level_department_name AS performance_first_level_department_name,
       performance_second_level_department_name AS performance_second_level_department_name,
       performance_third_level_department_name AS performance_third_level_department_name,
       cast(coalesce(income_amount,0)/100 AS decimal(24,2)) AS income_yuan,
       cast(coalesce(refund_amount,0)/100 AS decimal(24,2)) AS refund_yuan,
       cast((coalesce(income_amount,0)-coalesce(refund_amount,0))/100 AS decimal(24,2)) AS gross_profit_yuan,
       stat_judge_type AS stat_judge_type,
       fund_supervision_name AS fund_supervision_name
FROM service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf
WHERE dt='{{snapshot_dt}}'
  AND trade_timestamp >= timestamp '{{start_date}} 00:00:00'
  AND trade_timestamp < timestamp '{{end_exclusive}} 00:00:00'
  AND hour='{{snapshot_hour}}'
  AND course_first_level_department_name IN ('TT业务线','TT')
  AND course_second_level_department_name IN ('V学部','T学部','TT小学学部')
  AND performance_second_level_department_name='青橙项目部'
  AND coalesce(income_amount,0)+coalesce(refund_amount,0)<>0
LIMIT {{verified_export_limit}}
