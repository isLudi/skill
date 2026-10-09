-- Labels only. Never use this source to replace finance cash amounts.
SELECT cast(order_number AS varchar) AS order_number,
       cast(trade_timestamp AS varchar) AS trade_timestamp,
       cast(performance_employee_id AS varchar) AS performance_employee_id,
       stat_judge_type
FROM service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf
WHERE dt='{{snapshot_dt}}' AND hour='{{snapshot_hour}}'
 AND course_first_level_department_name IN ({{course_first_scope_sql}})
 AND course_second_level_department_name IN ({{course_second_scope_sql}})
 AND performance_second_level_department_name='青橙项目部'
 AND trade_timestamp >= timestamp '{{start_date}} 00:00:00'
 AND trade_timestamp < timestamp '{{end_exclusive}} 00:00:00'
 AND coalesce(income_amount,0)+coalesce(refund_amount,0)<>0
LIMIT {{verified_export_limit}}
