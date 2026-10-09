-- Parameterized recipe; resolve and validate scope before execution. Full replication remains pending.
SELECT format_datetime(f.trade_timestamp,'yyyyMMdd') AS dt,
       f.trade_timestamp AS trade_timestamp,
       f.final_paid_timestamp AS order_timestamp,
       cast(f.order_number AS varchar) AS order_number,
       cast(f.original_order_number AS varchar) AS original_order_number,
       cast(f.user_number AS varchar) AS user_number,
       cast(f.course_number AS varchar) AS course_number,
       f.course_name AS course_name,
       f.course_first_level_subject_name AS course_first_level_subject_name,
       f.course_second_level_subject_name AS course_second_level_subject_name,
       f.course_third_level_subject_name AS course_third_level_subject_name,
       f.course_top_level_department_name AS course_top_level_department_name,
       f.course_first_level_department_name AS course_first_level_department_name,
       f.course_second_level_department_name AS course_second_level_department_name,
       f.course_third_level_department_name AS course_third_level_department_name,
       cast(f.performance_employee_id AS varchar) AS performance_employee_id,
       f.employee_email_name AS performance_employee_email_name,
       f.performance_top_level_department_name AS performance_top_level_department_name,
       f.performance_first_level_department_name AS performance_first_level_department_name,
       f.performance_second_level_department_name AS performance_second_level_department_name,
       f.performance_third_level_department_name AS performance_third_level_department_name,
       cast(coalesce(f.income_amount,0)/100 AS decimal(24,2)) AS income_yuan,
       cast(coalesce(f.refund_amount,0)/100 AS decimal(24,2)) AS refund_yuan,
       cast((coalesce(f.income_amount,0)-coalesce(f.refund_amount,0))/100 AS decimal(24,2)) AS gross_profit_yuan,
       f.biz_type AS biz_type,
       f.goods_type AS goods_type,
       f.fund_supervision_name AS fund_supervision_name
FROM finance_dw.app_finance_order_income_refund_info_df f
WHERE f.dt = '{{snapshot_dt}}'
  AND f.goods_first_level_department_name IN ({{goods_first_scope_sql}})
  AND f.goods_second_level_department_name IN ({{goods_second_scope_sql}})
  AND CASE WHEN f.performance_second_level_department_name='青橙项目部' THEN 1
           WHEN f.course_second_level_department_name='青橙项目部' THEN 1 ELSE 0 END = 1
  AND f.trade_timestamp >= timestamp '{{start_date}} 00:00:00'
  AND f.trade_timestamp < timestamp '{{end_exclusive}} 00:00:00'
  AND coalesce(f.income_amount,0)+coalesce(f.refund_amount,0)<>0
LIMIT {{verified_export_limit}}
