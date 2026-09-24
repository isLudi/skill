WITH scoped AS (
    SELECT
        coalesce(performance_first_level_department_name, 'NULL') AS performance_l1,
        coalesce(performance_second_level_department_name, 'NULL') AS performance_l2,
        coalesce(performance_third_level_department_name, 'NULL') AS performance_l3,
        coalesce(trade_period_mapping_first_level_department_name, 'NULL') AS trade_period_l1,
        coalesce(pay_period_mapping_first_level_department_name, 'NULL') AS pay_period_l1,
        coalesce(cast(school_year AS varchar), 'NULL') AS school_year,
        coalesce(school_term_code, 'NULL') AS school_term_code,
        coalesce(cast(bind_type AS varchar), 'NULL') AS bind_type,
        coalesce(grade_name, 'NULL') AS grade_name,
        pay_refund_type,
        order_number,
        original_order_user_number AS user_number,
        stats_trade_timestamp,
        coalesce(income_amount, 0) / 100.0 AS income_yuan,
        coalesce(refund_amount, 0) / 100.0 AS refund_yuan
    FROM service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf
    WHERE dt = '20260919'
      AND hour = '20'
      AND course_first_level_department_name = 'H业务线'
      AND course_second_level_department_name = '精品班学部'
      AND pay_refund_type IN ('支付', '退款')
)
SELECT
    performance_l1, performance_l2, performance_l3,
    trade_period_l1, pay_period_l1,
    school_year, school_term_code, bind_type, grade_name,
    count(*) AS source_rows,
    count(DISTINCT order_number) AS order_count,
    count(DISTINCT user_number) AS user_count,
    min(stats_trade_timestamp) AS min_trade_time,
    max(stats_trade_timestamp) AS max_trade_time,
    sum(income_yuan) AS income_yuan,
    sum(refund_yuan) AS refund_yuan
FROM scoped
GROUP BY 1,2,3,4,5,6,7,8,9
ORDER BY income_yuan DESC, refund_yuan DESC
LIMIT 500
