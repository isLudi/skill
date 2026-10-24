WITH
finance_raw AS (
SELECT id, order_number, top_order_number, pre_order_number,
 pre_top_order_number, pre_biz_number, cast(user_id AS varchar) AS user_id1,
 email_prefix, employee_email_name AS name, trade_status, trade_type, trade_time,
 course_grade AS grade_list, price AS name_total_price,
 CASE WHEN trade_status IN ('全部退款','部分退款') THEN price ELSE 0 END AS refund_price,
 CASE WHEN SUBSTR(trade_time, 1, 10) >= '2026-07-14' AND SUBSTR(trade_time, 1, 10) <= '2026-07-19' THEN '20260716期' WHEN SUBSTR(trade_time, 1, 10) >= '2026-07-20' AND SUBSTR(trade_time, 1, 10) <= '2026-07-25' THEN '20260722期' WHEN SUBSTR(trade_time, 1, 10) >= '2026-07-26' AND SUBSTR(trade_time, 1, 10) <= '2026-07-31' THEN '20260728期' WHEN SUBSTR(trade_time, 1, 10) >= '2026-08-01' AND SUBSTR(trade_time, 1, 10) <= '2026-08-06' THEN '20260803期' WHEN SUBSTR(trade_time, 1, 10) >= '2026-08-07' AND SUBSTR(trade_time, 1, 10) <= '2026-08-12' THEN '20260808期' WHEN SUBSTR(trade_time, 1, 10) >= '2026-08-13' AND SUBSTR(trade_time, 1, 10) <= '2026-08-18' THEN '20260815期' WHEN SUBSTR(trade_time, 1, 10) >= '2026-02-25' AND SUBSTR(trade_time, 1, 10) <= '2026-03-02' THEN '20260227期' WHEN SUBSTR(trade_time, 1, 10) >= '2026-02-17' AND SUBSTR(trade_time, 1, 10) <= '2026-02-24' THEN '20260220期' WHEN SUBSTR(trade_time, 1, 10) >= '2026-02-09' AND SUBSTR(trade_time, 1, 10) <= '2026-02-16' THEN '20260213期' WHEN SUBSTR(trade_time, 1, 10) >= '2026-02-03' AND SUBSTR(trade_time, 1, 10) <= '2026-02-08' THEN '20260206期' WHEN SUBSTR(trade_time, 1, 10) >= '2026-01-27' AND SUBSTR(trade_time, 1, 10) <= '2026-02-02' THEN '20260130期' WHEN SUBSTR(trade_time, 1, 10) >= '2026-01-20' AND SUBSTR(trade_time, 1, 10) <= '2026-01-26' THEN '20260123期' ELSE CONCAT(DATE_FORMAT(DATE_TRUNC('WEEK', CAST(trade_time AS TIMESTAMP)) + INTERVAL '4' DAY, '%Y%m%d'), '期') END AS qici
FROM finance_dw.app_finance_performance_extend_details_hf
WHERE dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
 AND hour = format_datetime(now() - interval '2' hour, 'HH')
 AND employee_first_level_department_name = 'H业务线'
 AND employee_second_level_department_name = '市场部'
 AND employee_third_level_department_name = '市场顾问部'
 AND trade_type IN ('正常订单','调课调班')
 AND trade_time >= '2026-04-27'
),
attribute_raw AS (
SELECT order_number, original_order_number,
 original_order_user_number AS user_id1,
 performance_employee_email_prefix AS email_prefix, lead_id,
 lead_period_name AS attribute_period
FROM service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf
WHERE dt = FORMAT_DATETIME(CURRENT_TIMESTAMP - INTERVAL '2' HOUR, 'YYYYMMdd') AND hour = FORMAT_DATETIME(CURRENT_TIMESTAMP - INTERVAL '2' HOUR, 'HH') AND course_first_level_department_name IN ('H业务线', 'A业务线', 'EM业务线', 'LL业务线', 'TT', 'TUTU', 'TT业务线') AND course_second_level_department_name IN ('V项目部', '本地化部', '私域营销组', '青少成长学部', '创新技术组', '成长中心供应链组', 'APP运营组', '英语产品部', '职场服务部', '用户平台部', '微师产品部', '上海中心综合部', 'CAL技术组', '财务核算部', '财经项目部', '人才发展部', '财务信息化部', '图书项目部（关闭）', '运营部', '基础架构组', '数学产品部', '营销产品部', '雅思学部', '商品部', '磨课组', '升学规划部', '郑州中心', '组织部', '留学申请学部', '质检部', '架构平台部', '师训组', '投放商务组', '系统班部', '编程素养学部', '市场运营组', '项目运营组', 'KM技术组', '二讲老师部', '成都中心综合部', '业务设计部', '专题课部', '微师职教产品部', '高校学部', '教学服务部', '平台产品部', '数字化学部', '品牌运营组', '校长办公室', '运营中心财务', '视效部', '数据与商业分析中心', 'X项目', '教学产品部', 'XA学部', '语言学部', '图书产品部', '主播部', '业务支持部', 'HL技术组', '武汉中心综合部', '成人供应链组', '途途课堂', '信息平台部', 'HL经营分析组', '大数据部', '直播运营组', '市场部', '金刚产品部', '教学产品运营中心', '平台电商组', '企业效能部', '品牌与内容部', '产品研发部', '小学部', '技术质量部', '财务报告部', '税务部', '用户产品部', '直播二部', '招聘部', 'HR共享中心', '清北', '增长策略部', '督察部', '商品运营部', '资金管理部', '美好家庭学部', '设计支持中心', '初中部', 'AIGC创新部', '财务部', '人力资源部', '人才保障部一部', 'CAL经营分析组', '基础技术部', '综合素养学部', '热线呼入部', '品牌部', '语文产品部', '供应链部', '题库', 'GZ学部', '政府关系部', 'HRBP部', '招生运营部', '督检组', '耀师项目部', '产品运营部', '营运部', '多媒体技术部', '跟谁学郑州中心(失效）', '人工智能部', '体验设计部', '狮王项目部', '资产服务部', '专升本项目部', '基础技术部(失效)', '郑州中心综合部', '考研学部', '内容营销组', '公关部', '公职学部', '客服部', '运营平台部', 'CS学部', '财务FP&A部', '商学院学部', '行政部', '直播三部', '营销技术部', '私域运营组', '飞花产品部', '星火产品部', '客户端技术部', '薪酬绩效部', '图书项目部', 'NJ学部', '直播一部', '法务部', '在线服务部', '履约部', 'KML经营分析组', '社会保障部', '精品班部', '教学教研部', '医疗项目部', '菁英班部', '菁英班学部', '精品班学部', '一对一学部', '北京学部', '图书学部', '河南学部', '清北班学部', '湖广学部', '山西学部', 'K学部', 'M学部', '大学生学习学部', '合肥学校', '太原学校', '苏州学校', '郑州学校', '北京学校', '上海学校', '运营中心', '广州学校', '市场中心', '南京学校', '深圳学校', '成都学校', '财务中心', '武汉学校', '济南学校', '天津学校', '学校办公室', '重庆学校', '西安学校', '长沙学校', '市场二部', '留学学部', '国际考试学部', '出国语培线下项目', '广州学校（IE）', '国际竞赛项目', '剑桥英语项目', '上海学校（IE）', '心理学部', '创新项目部', '素质成长学部', '国际考试在线学部', '毛豆学部', '青少学部', '市场三部', '市场四部', '青橙项目部', '文旅学部', '本地化大班学部', '市场营销部', '直播市场部', '创新增长部', '学习规划中心', '素养初中学部', '素养青藤学部', '素养小学学部', '用户运营部', '经营策略部', '校园招聘', '直播创新部', '战略创新部', '产研部', '业务研发部', '教学质量部', 'Theta项目部', 'AI素养学部', '文旅项目', 'Theta智学项目部', 'Theta产研部', 'V学部', 'TT初中学部', 'TT小学学部', '产研部', 'T学部', '专题课部（失效）', '初中组', '文旅项目（失效）') AND performance_third_level_department_name = '市场顾问部'
 AND performance_first_level_department_name = 'H业务线'
 AND performance_second_level_department_name = '市场部'
 AND lead_id > 0
),
lead_info AS (
SELECT
  t.lead_id,
  t.rule_name,
  t.flow_pool_name,
  t.third_department_name,
  t.sku_id_name,
  t.ad_account_name,
  t.source_manager_name,
  t.channel_name_1,
  t.channel_name_2,
  t.channel_name_3,
  t.put_plan_name,
  t.channel_provider_name,
  t.channel_second_provider_name,
  t.page_id_name,
  t.source_put_plan_name,
  t.get_customer_way_name,
  t.first_department_name,
  t.second_department_name,
  t.virtual_second_department_name,
  t.virtual_fourth_department_name,
  t.virtual_fifth_department_name,
  t.lead_purchase_intention_name,
  t.lead_purchase_intention_level1_category_name,
  t.lead_purchase_intention_level2_category_name,
  t.lead_create_time,
  t.trace_type_name,
  t.period_name,
  t.virtual_leader_email_name AS metric_jingli,
  t.virtual_direct_leader_email_name AS metric_zhuguan,
  t.employee_email_name AS metric_name,
  t.lead_purchase_intention_level2_category_name AS metric_grade_1,
  COALESCE(t.valid_lead_count, 0) AS valid_lead_count,
  COALESCE(t.income_amount, 0) AS income_amount,
  COALESCE(t.in_pay_period_refund_amount, 0) AS in_pay_period_refund_amount,
  COALESCE(t.non_pay_period_refund_amount, 0) AS non_pay_period_refund_amount,
  COALESCE(t.same_lead_period_refund_amount, 0) AS same_lead_period_refund_amount,
  CAST(t.flow_original_order_activity_price AS VARCHAR) AS flow_original_order_activity_price,
  CAST(t.flow_order_price AS VARCHAR) AS flow_order_price,
  CAST(t.flow_orders_income_amount AS VARCHAR) AS flow_orders_income_amount,
  CASE
    WHEN CAST(DATE_PARSE(REPLACE(CONCAT(t.group_period_year, t.group_period_term), '期', ''), '%Y%m%d') AS DATE) BETWEEN CAST('2026-07-14' AS DATE) AND CAST('2026-07-19' AS DATE)
    THEN '20260716期'
    WHEN CAST(DATE_PARSE(REPLACE(CONCAT(t.group_period_year, t.group_period_term), '期', ''), '%Y%m%d') AS DATE) BETWEEN CAST('2026-07-20' AS DATE) AND CAST('2026-07-25' AS DATE)
    THEN '20260722期'
    WHEN CAST(DATE_PARSE(REPLACE(CONCAT(t.group_period_year, t.group_period_term), '期', ''), '%Y%m%d') AS DATE) BETWEEN CAST('2026-07-26' AS DATE) AND CAST('2026-07-31' AS DATE)
    THEN '20260728期'
    WHEN CAST(DATE_PARSE(REPLACE(CONCAT(t.group_period_year, t.group_period_term), '期', ''), '%Y%m%d') AS DATE) BETWEEN CAST('2026-08-01' AS DATE) AND CAST('2026-08-06' AS DATE)
    THEN '20260803期'
    WHEN CAST(DATE_PARSE(REPLACE(CONCAT(t.group_period_year, t.group_period_term), '期', ''), '%Y%m%d') AS DATE) BETWEEN CAST('2026-08-07' AS DATE) AND CAST('2026-08-12' AS DATE)
    THEN '20260808期'
    WHEN CAST(DATE_PARSE(REPLACE(CONCAT(t.group_period_year, t.group_period_term), '期', ''), '%Y%m%d') AS DATE) BETWEEN CAST('2026-08-13' AS DATE) AND CAST('2026-08-18' AS DATE)
    THEN '20260815期'
    ELSE CONCAT(
      CAST(DATE_FORMAT(
        DATE_TRUNC(
          'WEEK',
          DATE_PARSE(REPLACE(CONCAT(t.group_period_year, t.group_period_term), '期', ''), '%Y%m%d')
        ) + INTERVAL '4' DAY,
        '%Y%m%d'
      ) AS VARCHAR),
      '期'
    )
  END AS lf_period_name,
  t.employee_email_prefix AS context_email,
  CAST(t.user_id AS VARCHAR) AS context_user_id,
  t.section_assign_time,
  t.flow_order_number,
  t.flow_order_clazz_biz_number
FROM bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df AS t
WHERE
  t.dt = FORMAT_DATETIME(CURRENT_TIMESTAMP - INTERVAL '2' HOUR, 'YYYYMMdd')
  AND t.hour = FORMAT_DATETIME(CURRENT_TIMESTAMP - INTERVAL '3' HOUR, 'HH')
  AND t.section_assign_employee_first_level_department_name = 'H业务线'
  AND t.section_assign_employee_second_level_department_name = '市场部'
  AND t.section_assign_employee_third_level_department_name = '市场顾问部'
  AND t.period_mapping_first_level_department_name = 'H业务线'
  AND t.period_mapping_second_level_department_name IN ('精品班学部', '市场部', '菁英班学部', '本地化大班学部', '一对一学部')
),
attribute_keys AS (
SELECT k.kind, k.lookup_key, a.email_prefix, a.lead_id, a.attribute_period
FROM attribute_raw a
CROSS JOIN UNNEST(ARRAY['AO','AO','AU'], ARRAY[
 cast(a.order_number AS varchar), cast(a.original_order_number AS varchar), a.user_id1
]) AS k(kind, lookup_key)
),
lead_keys AS (
SELECT k.kind, k.lookup_key, l.context_email AS email_prefix,
 l.lead_id, l.lf_period_name AS attribute_period
FROM lead_info l
CROSS JOIN UNNEST(ARRAY['BO','BB','BU'], ARRAY[
 l.flow_order_number, l.flow_order_clazz_biz_number, l.context_user_id
]) AS k(kind, lookup_key)
),
lead_lookup AS (
SELECT kind, lookup_key, email_prefix,
 CASE WHEN count(DISTINCT lead_id)=1 THEN min(lead_id) END AS lead_id,
 CASE WHEN count(DISTINCT attribute_period)=1 THEN min(attribute_period) END AS attribute_period,
 count(DISTINCT lead_id) AS lead_candidates
FROM (
 SELECT kind, lookup_key, email_prefix, lead_id, attribute_period FROM attribute_keys
 UNION ALL
 SELECT kind, lookup_key, email_prefix, lead_id, attribute_period FROM lead_keys
) k
WHERE lookup_key IS NOT NULL AND lookup_key NOT IN ('','0')
 AND email_prefix IS NOT NULL AND lead_id > 0
GROUP BY kind, lookup_key, email_prefix
),
finance_keys AS (
SELECT f.*, k.kind AS match_kind,
 k.priority AS match_priority, k.lookup_key
FROM finance_raw f
CROSS JOIN UNNEST(ARRAY[1,2,3,4,5,6,7], ARRAY['AO','AO','BO','BO','BB','AU','BU'], ARRAY[
 cast(f.order_number AS varchar), cast(f.top_order_number AS varchar),
 cast(f.pre_order_number AS varchar), cast(f.pre_top_order_number AS varchar),
 f.pre_biz_number, f.user_id1, f.user_id1
]) AS k(priority, kind, lookup_key)
WHERE f.qici > '20260424期'
),
finance_match_ranked AS (
SELECT f.*, l.lead_id, l.attribute_period,
 row_number() OVER (PARTITION BY f.id ORDER BY
  CASE WHEN l.lead_id IS NOT NULL THEN 0 ELSE 1 END, f.match_priority) AS match_rn
FROM finance_keys f
LEFT JOIN lead_lookup l ON l.kind=f.match_kind AND l.lookup_key=f.lookup_key
 AND l.email_prefix=f.email_prefix
),
finance_matched AS (
SELECT * FROM finance_match_ranked WHERE match_rn=1
),
context_ranked AS (
SELECT f.*, lf.lead_id AS context_lead_id,
 lf.rule_name, lf.flow_pool_name, lf.third_department_name, lf.sku_id_name, lf.ad_account_name, lf.source_manager_name, lf.channel_name_1, lf.channel_name_2, lf.channel_name_3, lf.put_plan_name, lf.channel_provider_name, lf.channel_second_provider_name, lf.page_id_name, lf.source_put_plan_name, lf.get_customer_way_name, lf.first_department_name, lf.second_department_name, lf.virtual_second_department_name, lf.virtual_fourth_department_name, lf.virtual_fifth_department_name, lf.lead_purchase_intention_name, lf.lead_purchase_intention_level1_category_name, lf.lead_purchase_intention_level2_category_name, lf.lead_create_time, lf.trace_type_name, lf.period_name, lf.metric_jingli, lf.metric_zhuguan, lf.metric_name, lf.metric_grade_1, lf.valid_lead_count, lf.income_amount, lf.in_pay_period_refund_amount, lf.non_pay_period_refund_amount, lf.same_lead_period_refund_amount, lf.flow_original_order_activity_price, lf.flow_order_price, lf.flow_orders_income_amount, lf.lf_period_name, lf.context_email, lf.context_user_id, lf.section_assign_time, lf.flow_order_number, lf.flow_order_clazz_biz_number,
 row_number() OVER (PARTITION BY f.id ORDER BY
  CASE WHEN lf.lf_period_name=f.attribute_period THEN 0 ELSE 1 END,
  CASE WHEN lf.context_email=f.email_prefix THEN 0 ELSE 1 END,
  CASE WHEN lf.valid_lead_count>0 THEN 0 ELSE 1 END,
  lf.section_assign_time DESC, lf.lf_period_name DESC, lf.rule_name,
  lf.flow_pool_name, lf.sku_id_name, lf.put_plan_name, lf.channel_name_1,
  lf.channel_name_2, lf.channel_name_3, lf.ad_account_name, lf.source_manager_name,
  lf.context_email) AS context_rn
FROM finance_matched f
LEFT JOIN lead_info lf ON lf.lead_id=f.lead_id
),
financial_context AS (
SELECT * FROM context_ranked WHERE context_rn=1
),
rule_ranked AS (
SELECT
  lead_id,
  account_domain,
  rule_name,
  create_time,
  CASE
    WHEN STRPOS(rule_name, '期') > 0
    AND STRPOS(rule_name, '期') >= 9
    AND REGEXP_LIKE(SUBSTR(rule_name, STRPOS(rule_name, '期') - 8, 8), '^[0-9]{8}$')
    THEN SUBSTR(rule_name, STRPOS(rule_name, '期') - 8, 9)
    WHEN STRPOS(rule_name, '期') > 0
    AND STRPOS(rule_name, '期') >= 5
    AND REGEXP_LIKE(SUBSTR(rule_name, STRPOS(rule_name, '期') - 4, 4), '^[0-9]{4}$')
    THEN SUBSTR(rule_name, STRPOS(rule_name, '期') - 4, 5)
    ELSE NULL
  END AS group_period_term,
  ROW_NUMBER() OVER (PARTITION BY lead_id, account_domain ORDER BY create_time DESC, rule_name) AS rr_rn
FROM service_dw.dim_crm_assign_rule_lead_detail_hf
WHERE
  dt = FORMAT_DATETIME(CURRENT_TIMESTAMP - INTERVAL '2' HOUR, 'YYYYMMdd')
  AND hour = FORMAT_DATETIME(CURRENT_TIMESTAMP - INTERVAL '2' HOUR, 'HH')
),
rule_once AS (
SELECT lead_id, account_domain, rule_name, group_period_term FROM rule_ranked WHERE rr_rn=1
),
rule AS (
SELECT lf.*, lf.virtual_fourth_department_name AS depart,
 CASE
  WHEN lf_period_name = '20260728期'
  AND lf.third_department_name = '线上商务部'
  AND lf.flow_pool_name = '电商退款用户池'
  AND lf.put_plan_name = '0728期退款用户计划'
  AND lf.channel_name_1 = '内部'
  AND lf.channel_name_2 = '流量复用'
  AND lf.source_manager_name = '曲默晗'
  AND lf.sku_id_name LIKE '0728期-%帅师%'
  THEN '退款订单复用'
  WHEN lf_period_name = '20260803期'
  AND lf.third_department_name = '线上商务部'
  AND lf.source_manager_name IN ('曲默晗', '何木玲')
  AND lf.sku_id_name LIKE '0728期-%'
  AND (
    lf.sku_id_name LIKE '%帅师%' OR lf.sku_id_name LIKE '%孟帝%'
  )
  THEN '退款订单复用'
  WHEN lf.get_customer_way_name IN ('平台自播')
  AND lf.flow_pool_name IN ('赢战广东中考', '高途专版图书', '状元帮教辅', '高途专版视频书', '本地化专版图书', '广东专版图书')
  THEN '广东图书'
  WHEN lf.get_customer_way_name IN ('平台自播')
  AND lf.flow_pool_name IN (
    '途铭文化专版图书',
    '途铭文化',
    '博慧星辰文化图书',
    '启迪蔚来',
    '智慧航迹图书',
    '高途浙江初中',
    '高途浙江高中',
    '高途浙江新高一',
    '浙江专版图书教辅'
  )
  THEN '浙江图书'
  WHEN lf.get_customer_way_name IN ('平台自播')
  AND lf.flow_pool_name IN ('沪上名校', '沪上领航社', '简学文化', '魔都校友助学馆', '沪上领航高中', '沪上领航初中')
  THEN '上海图书'
  WHEN lf.get_customer_way_name IN ('平台自播')
  AND lf.flow_pool_name IN ('高途江苏中考', '高途赢战中考')
  THEN '江苏图书'
  WHEN lf.flow_pool_name = '电商退款用户池'
  AND lf.rule_name LIKE '%赠失%'
  AND lf.rule_name LIKE '%朱博士%'
  THEN '赠课失败-朱汉祺'
  WHEN lf.flow_pool_name = '电商退款用户池'
  AND lf.rule_name LIKE '%赠失%'
  AND lf.rule_name LIKE '%春春%'
  THEN '赠课失败-陈瑞春'
  WHEN lf.flow_pool_name = '电商退款用户池'
  AND lf.rule_name LIKE '%赠失%'
  AND lf.rule_name LIKE '%亚飞%'
  THEN '赠课失败-孟亚飞'
  WHEN lf.flow_pool_name = '电商退款用户池'
  AND lf.rule_name LIKE '%赠失%'
  AND lf.rule_name LIKE '%星义%'
  THEN '赠课失败-赵星义'
  WHEN lf.flow_pool_name = '电商退款用户池'
  AND lf.rule_name LIKE '%赠失%'
  AND lf.rule_name LIKE '%郭艺%'
  THEN '赠课失败-郭艺'
  WHEN lf.second_department_name = '本地化大班学部'
  OR lf.source_manager_name IN ('鲍大海', '杨文卓', '喻新桥')
  THEN '本地化市场流量'
  WHEN lf.third_department_name IN ('中价产品项目部', '新媒体内容运营部') AND lf.rule_name LIKE '%曹忆%'
  THEN '曹忆'
  WHEN lf.rule_name LIKE '%语数英%' AND lf.third_department_name = '新媒体内容运营部'
  THEN '语数英'
  WHEN lf.third_department_name = '直播部' AND lf.sku_id_name LIKE '%山东专版%'
  THEN '北京直播山东'
  WHEN lf.third_department_name = '直播部' AND lf.sku_id_name LIKE '%河南专版%'
  THEN '北京直播河南'
  WHEN lf.sku_id_name LIKE '%江苏%' AND lf.third_department_name = '直播部'
  THEN '北京直播江苏'
  WHEN lf.third_department_name LIKE '%锋途%' AND lf.channel_name_2 = '抖音'
  THEN '锋途KOC'
  WHEN lf.third_department_name = '线上商务部' AND lf.flow_pool_name LIKE '%图书订单%'
  THEN '图书解密'
  WHEN lf.put_plan_name LIKE '%小红书打粉%'
  THEN 'EM-小红书合作'
  WHEN lf.third_department_name IN ('投放部', '线上商务部', '小红书攻坚组')
  AND lf.channel_name_2 = '小红书'
  THEN '小红书-闯闯组'
  WHEN lf.third_department_name IN ('新媒体内容运营部') AND lf.channel_name_2 = '小红书'
  THEN '小红书直投-绍孜组'
  WHEN lf.page_id_name LIKE '%0元领课%' AND lf.third_department_name = '投放部'
  THEN '信息流0元'
  WHEN lf.page_id_name LIKE '%周帅0元腾讯%' AND lf.third_department_name = '投放部'
  THEN '信息流0转低'
  WHEN lf.page_id_name LIKE '%信息流下引%' AND lf.third_department_name = '私域运营部'
  THEN '信息流0转低'
  WHEN lf.sku_id_name LIKE '%数理系统%'
  AND lf.third_department_name IN ('快乐成长组', '直播部', '市场效能部', '运营部')
  THEN '物理系统'
  WHEN lf.trace_type_name LIKE '%转介绍%'
  THEN '转介绍'
  WHEN lf.ad_account_name IN (
    '高途-高中-DYD搜索-QZ49',
    '高途-高中-DYD搜索-XLHD49',
    '高途-高中-DYD搜索-XLHD50',
    '高途-高中-DYD搜索-QZ50'
  )
  OR lf.ad_account_name LIKE '%DYD1元搜索%'
  THEN '搜索1元'
  WHEN (
    lf.flow_pool_name LIKE '%江苏预习%' OR lf.flow_pool_name LIKE '%江苏专版预习%'
  )
  AND lf.channel_name_2 = '抖音'
  THEN '西安直播江苏-抖音'
  WHEN lf.flow_pool_name LIKE '%自然流%'
  AND lf.rule_name LIKE '%江苏%'
  AND lf.third_department_name = '图书营销部'
  AND lf.channel_name_2 = '抖音'
  THEN '西安直播江苏-抖音'
  WHEN (
    lf.flow_pool_name LIKE '%江苏预习%' OR lf.flow_pool_name LIKE '%江苏专版预习%'
  )
  AND lf.channel_name_2 = '视频号'
  THEN '西安直播江苏-视频号'
  WHEN lf.flow_pool_name LIKE '%退款%' AND lf.third_department_name = '图书营销部'
  THEN '西安直播-退款订单复用'
  WHEN lf.flow_pool_name LIKE '%自然流%'
  AND lf.rule_name LIKE '%江苏%'
  AND lf.third_department_name = '图书营销部'
  AND lf.channel_name_2 = '视频号'
  THEN '西安直播江苏-视频号'
  WHEN lf.sku_id_name LIKE '%2000题%' AND lf.third_department_name = '图书营销部'
  THEN '西安直播2000题'
  WHEN lf.sku_id_name LIKE '%五年高考%' AND lf.third_department_name = '图书营销部'
  THEN '西安直播五年真题'
  WHEN (
    lf.rule_name LIKE '%北京图书%' OR lf.sku_id_name LIKE '%北京专版%'
  )
  AND lf.third_department_name = '图书营销部'
  THEN '西安直播北京'
  WHEN lf.sku_id_name LIKE '%安徽%' AND lf.third_department_name = '图书营销部'
  THEN '西安直播安徽'
  WHEN lf.put_plan_name LIKE '%全国教考%' AND lf.third_department_name = '图书营销部'
  THEN '西安直播全国'
  WHEN lf.flow_pool_name LIKE '%自然流%'
  AND lf.rule_name LIKE '%北京%'
  AND lf.third_department_name = '图书营销部'
  THEN '西安直播北京'
  WHEN lf.sku_id_name LIKE '%2000题%' AND lf.third_department_name = '直播部'
  THEN 'IP直播-2000题'
  WHEN lf.flow_pool_name LIKE '%星义大大%' OR lf.flow_pool_name LIKE '%星义物理%'
  THEN '赵星义'
  WHEN (
    lf.source_manager_name IN ('马思雨02', '袁银') AND lf.rule_name LIKE '%集团%'
  )
  AND NOT COALESCE(
    (
      (
        lf.third_department_name = '私域运营部'
        AND lf.source_manager_name IN (
          '陈雷19',
          '崔慧敏01',
          '侯佳林01',
          '郑天琪02',
          '杨彬屹',
          '曹义鹏',
          '王硕阳',
          '于超研',
          '岳一帆02',
          '田起帆',
          '王绍阳',
          '肖佳兴',
          '姚佳03',
          '秦金萍',
          '李冞萤'
        )
      )
      OR (
        lf.flow_pool_name LIKE '%南通欣创%'
        OR lf.flow_pool_name LIKE '%人人通科技%'
        OR lf.flow_pool_name LIKE '%易而购%'
        OR lf.flow_pool_name LIKE '%济南梦航%'
        OR lf.flow_pool_name LIKE '%晨硕智学%'
        OR lf.flow_pool_name LIKE '%兴尧文化%'
        OR lf.flow_pool_name LIKE '%济南映像%'
        OR lf.flow_pool_name LIKE '%山东简单%'
        OR lf.flow_pool_name LIKE '%争鸣科技%'
      )
      OR (
        (
          lf.flow_pool_name LIKE '%家校共育%'
          OR lf.flow_pool_name LIKE '%保持热爱%'
          OR lf.flow_pool_name LIKE '%青松%'
          OR lf.flow_pool_name LIKE '%悟之道%'
        )
        AND lf.put_plan_name NOT LIKE '%0元%'
      )
      OR (
        lf.source_manager_name = '李宁24' AND lf.put_plan_name LIKE '%0转低%'
      )
      OR (
        lf.third_department_name = '私域运营部'
        AND lf.flow_original_order_activity_price IN ('100.0', '900.0', '300.0')
      )
      OR (
        lf.third_department_name = '私域运营部'
        AND lf.flow_original_order_activity_price IN ('0.0')
        AND lf.source_manager_name IN ('陈雷19', '崔慧敏01', '侯佳林01', '郑天琪02', '杨彬屹', '曹义鹏', '王硕阳', '于超研')
      )
      OR (
        lf.flow_pool_name LIKE '公导私'
      )
      OR (
        lf.flow_pool_name LIKE '%0转低转正%' OR lf.channel_name_2 = '产研测试'
      )
    ),
    FALSE
  )
  THEN '集团私域'
  WHEN lf.rule_name LIKE '%途途私域%'
  OR (
    lf.rule_name LIKE '%私域%' AND lf.first_department_name = 'TT'
  )
  OR lf.rule_name LIKE '%私域1元%'
  OR (
    lf.third_department_name = '私域招生中心' AND lf.flow_pool_name LIKE '%APP%'
  )
  THEN '途途私域'
  WHEN lf.third_department_name = '图书营销部'
  AND (
    lf.sku_id_name LIKE '%孟亚飞99%' OR lf.sku_id_name LIKE '%亚飞%'
  )
  AND lf.channel_name_2 = '百度'
  THEN '孟亚飞-2组-百度'
  WHEN lf.third_department_name = '图书营销部'
  AND (
    lf.sku_id_name LIKE '%孟亚飞99%' OR lf.sku_id_name LIKE '%亚飞%'
  )
  AND lf.channel_name_2 = '抖音'
  THEN '孟亚飞-2组-抖音'
  WHEN lf.third_department_name = '投放部' AND (
    lf.ad_account_name LIKE '%周帅%'
  )
  THEN '信息流-周帅'
  WHEN lf.source_manager_name IN ('韩正卿')
  THEN '抖音私信'
  WHEN lf.channel_name_1 = '市场私域' AND lf.put_plan_name LIKE '%孟亚飞汇总%'
  THEN '小红书自然流-绍孜组'
  WHEN lf.channel_name_1 = '市场私域'
  AND (
    lf.virtual_fourth_department_name IN ('郑州学习顾问二部', '郑州学习顾问七部', '郑州训练营')
    AND (
      lf.rule_name LIKE '%表单%' OR lf.trace_type_name LIKE '%引流课%'
    )
  )
  THEN '市场私域低价单'
  WHEN lf.third_department_name = '私域运营部'
  AND lf.source_manager_name IN (
    '陈雷19',
    '崔慧敏01',
    '侯佳林01',
    '郑天琪02',
    '杨彬屹',
    '曹义鹏',
    '王硕阳',
    '于超研',
    '岳一帆02',
    '田起帆',
    '王绍阳',
    '肖佳兴',
    '姚佳03',
    '秦金萍',
    '李冞萤'
  )
  AND (
    lf.rule_name LIKE '%koc自孵化下引%'
    OR lf.rule_name LIKE '%koc下引%'
    OR lf.page_id_name LIKE '%自营%'
  )
  THEN '自孵化KOC下引'
  WHEN lf.third_department_name = '私域运营部'
  AND lf.source_manager_name IN (
    '陈雷19',
    '崔慧敏01',
    '侯佳林01',
    '郑天琪02',
    '杨彬屹',
    '曹义鹏',
    '王硕阳',
    '于超研',
    '岳一帆02',
    '田起帆',
    '王绍阳',
    '肖佳兴',
    '姚佳03',
    '秦金萍',
    '李冞萤'
  )
  THEN '进校私域合作'
  WHEN lf.channel_name_1 = '市场私域'
  AND (
    lf.virtual_fourth_department_name IN ('郑州学习顾问二部', '郑州学习顾问七部', '郑州训练营')
    OR lf.virtual_fifth_department_name IN ('罗江博团队')
  )
  THEN '市场私域入群'
  WHEN lf.third_department_name = '图书营销部'
  AND (
    lf.rule_name LIKE '%点睛卷%' OR lf.sku_id_name LIKE '%押题卷%'
  )
  THEN '押题卷'
  WHEN lf.third_department_name = '投放部'
  AND lf.channel_name_2 = '小红书'
  AND lf.channel_name_1 <> '搜索营销'
  THEN '信息流-小红书'
  WHEN lf.third_department_name = '线上商务部' AND lf.channel_name_2 = '小红书'
  THEN '小红书'
  WHEN (
    lf.flow_pool_name LIKE '%北大汤哥%'
    OR lf.flow_pool_name LIKE '%海淀名师高阶%'
    OR lf.flow_pool_name LIKE '%海淀高阶%'
    OR lf.flow_pool_name LIKE '%高阶英语887%'
  )
  AND lf.sku_id_name LIKE '%小艺%'
  THEN '郭艺'
  WHEN lf.third_department_name LIKE '%私域%'
  AND lf.rule_name LIKE '%私域%'
  AND lf.rule_name LIKE '%图书%'
  THEN '市场私域图书'
  WHEN lf.third_department_name LIKE '%私域%' AND lf.rule_name LIKE '%公域自然流%'
  THEN '小红书自然流-绍孜组'
  WHEN lf.third_department_name LIKE '%私域%' AND lf.rule_name LIKE '%品效%'
  THEN '市场私域品效'
  WHEN lf.third_department_name LIKE '%私域%' AND lf.put_plan_name LIKE '%会话%'
  THEN '市场私域会话'
  WHEN lf.third_department_name LIKE '%私域%' AND lf.rule_name LIKE '%公域学霸%'
  THEN '市场私域公域组'
  WHEN lf.third_department_name IN ('线上商务部')
  AND lf.source_manager_name IN ('孙晗01', '方俊结01', '刘亦鹏02', '何木玲', '杨梓月', '张可意03', '任颖迪', '曹蕊07', '曲默晗')
  AND lf.flow_pool_name LIKE '%退款%'
  THEN 'KOC-退款订单复用'
  WHEN lf.third_department_name IN ('直播部', '新媒体内容运营部', '市场一组', '私域运营部')
  AND lf.flow_pool_name = '电商退款用户池'
  THEN 'IP退款订单复用'
  WHEN lf.third_department_name IN ('直播部', '新媒体内容运营部', '市场一组', '私域运营部')
  AND lf.put_plan_name LIKE '%失败%'
  AND lf.flow_pool_name = '电商退款用户池'
  THEN '赠课失败'
  WHEN lf.third_department_name IN ('直播部', '新媒体内容运营部', '市场一组')
  AND (
    lf.flow_pool_name = '初阶化学规划' OR lf.flow_pool_name LIKE '%启迪-初阶老师%'
  )
  THEN '曹忆'
  WHEN (
    lf.third_department_name = '图书营销部' AND lf.sku_id_name LIKE '%真题%'
  )
  OR (
    lf.third_department_name = '直播部' AND lf.sku_id_name LIKE '%真题%'
  )
  THEN '西安图书直播间-直播'
  WHEN (
    lf.third_department_name = '图书营销部' AND lf.sku_id_name NOT LIKE '%真题%'
  )
  OR (
    lf.third_department_name = '直播部' AND lf.sku_id_name LIKE '%秒懂%'
  )
  OR (
    lf.third_department_name = '直播部' AND lf.sku_id_name LIKE '%图书赠送%'
  )
  THEN '西安图书直播间-挂链'
  WHEN lf.third_department_name IN ('直播部', '新媒体内容运营部', '市场一组')
  AND (
    lf.flow_pool_name LIKE '%海淀高阶名师%'
    OR lf.flow_pool_name LIKE '%海淀老师高阶%'
    OR lf.flow_pool_name LIKE '%小艺%'
    OR lf.flow_pool_name LIKE '%老蒋文化%'
  )
  THEN '郭艺'
  WHEN lf.third_department_name IN ('直播部', '新媒体内容运营部', '市场一组')
  AND lf.flow_pool_name LIKE '%电商退款%'
  AND lf.rule_name LIKE '%郭艺99%'
  THEN '郭艺'
  WHEN lf.put_plan_name LIKE '%国培教育-0元%'
  OR lf.put_plan_name LIKE '%易喆教育-0元%'
  OR lf.put_plan_name LIKE '%钟情-0元%'
  OR lf.put_plan_name LIKE '%中望达-0元%'
  OR lf.put_plan_name LIKE '%晨硕-0元%'
  OR lf.put_plan_name LIKE '%彩石-0元入群%'
  THEN '创新商务入群'
  WHEN lf.third_department_name = 'KOC孵化部'
  AND lf.flow_pool_name LIKE '%电商退款%'
  AND lf.put_plan_name LIKE '%失败%'
  THEN '自孵化KOC-赠课失败'
  WHEN lf.third_department_name = 'KOC孵化部'
  AND lf.flow_pool_name LIKE '%电商退款%'
  AND lf.put_plan_name LIKE '%退%'
  THEN '自孵化KOC-退款订单复用'
  WHEN lf.source_manager_name = '方俊结01' AND lf.put_plan_name LIKE '%赠课后退款%'
  THEN 'KOC-赠课后退款'
  WHEN lf.third_department_name = '直播部'
  AND (
    lf.sku_id_name LIKE '%春春%'
    OR lf.sku_id_name LIKE '%瑞春%'
    OR lf.rule_name LIKE '%春春%'
    OR lf.rule_name LIKE '%瑞春%'
  )
  AND lf.channel_name_2 = '百度'
  THEN '陈瑞春-百度'
  WHEN lf.third_department_name = '直播部'
  AND (
    lf.sku_id_name LIKE '%春春%'
    OR lf.sku_id_name LIKE '%瑞春%'
    OR lf.rule_name LIKE '%春春%'
    OR lf.rule_name LIKE '%瑞春%'
  )
  AND lf.channel_name_2 = 'B站'
  THEN '陈瑞春-B站'
  WHEN lf.third_department_name = '直播部'
  AND (
    lf.sku_id_name LIKE '%春春%'
    OR lf.sku_id_name LIKE '%瑞春%'
    OR lf.rule_name LIKE '%春春%'
    OR lf.rule_name LIKE '%瑞春%'
  )
  AND lf.channel_name_2 = '抖音'
  THEN '陈瑞春-抖音199'
  WHEN lf.third_department_name IN ('直播部', '新媒体内容运营部')
  AND (
    lf.sku_id_name LIKE '%春春%'
    OR lf.sku_id_name LIKE '%瑞春%'
    OR lf.rule_name LIKE '%春春%'
    OR lf.rule_name LIKE '%瑞春%'
  )
  AND lf.channel_name_2 = '视频号'
  THEN '陈瑞春-视频号49'
  WHEN lf.third_department_name = '直播部'
  AND (
    lf.sku_id_name LIKE '%朱博士99%'
    OR lf.rule_name LIKE '%朱汉祺99%'
    OR lf.rule_name LIKE '%朱博士%'
    OR lf.flow_pool_name LIKE '%朱博士%'
    OR lf.sku_id_name LIKE '%朱博士%'
  )
  AND lf.channel_name_2 = 'B站'
  THEN '朱博士-B站'
  WHEN lf.third_department_name = '直播部'
  AND (
    lf.sku_id_name LIKE '%朱博士99%'
    OR lf.rule_name LIKE '%朱汉祺99%'
    OR lf.rule_name LIKE '%朱博士%'
    OR lf.flow_pool_name LIKE '%朱博士%'
    OR lf.sku_id_name LIKE '%朱博士%'
  )
  AND lf.channel_name_2 = '百度'
  THEN '朱博士-百度'
  WHEN lf.third_department_name = '直播部'
  AND (
    lf.sku_id_name LIKE '%抖音99%' AND lf.sku_id_name LIKE '%朱博士%'
  )
  AND lf.channel_name_2 = '抖音'
  THEN '朱博士-抖音99'
  WHEN lf.third_department_name = '直播部'
  AND (
    lf.sku_id_name LIKE '%朱博士99%'
  )
  AND lf.channel_name_2 = '抖音'
  THEN '朱博士-抖音99'
  WHEN lf.third_department_name = '直播部'
  AND (
    lf.sku_id_name LIKE '%朱博士99%'
    OR lf.rule_name LIKE '%朱汉祺99%'
    OR lf.rule_name LIKE '%朱博士%'
    OR lf.flow_pool_name LIKE '%朱博士%'
    OR lf.sku_id_name LIKE '%朱博士%'
    OR lf.rule_name LIKE '%朱汉祺199%'
  )
  AND lf.channel_name_2 = '抖音'
  THEN '朱博士-抖音199'
  WHEN lf.third_department_name = '直播部'
  AND (
    lf.sku_id_name LIKE '%朱博士99%'
    OR lf.rule_name LIKE '%朱汉祺99%'
    OR lf.rule_name LIKE '%朱博士%'
    OR lf.flow_pool_name LIKE '%朱博士%'
    OR lf.sku_id_name LIKE '%朱博士%'
    OR lf.rule_name LIKE '%朱汉祺49%'
  )
  AND lf.channel_name_2 = '视频号'
  THEN '朱博士-视频号49'
  WHEN (
    lf.third_department_name = '直播部'
    AND (
      lf.sku_id_name LIKE '%朱博士%' OR lf.sku_id_name LIKE '%朱汉祺%'
    )
    AND lf.rule_name LIKE '%9%'
    AND lf.rule_name NOT LIKE '%29%'
    AND lf.sku_id_name NOT LIKE '%急%'
    AND lf.sku_id_name NOT LIKE '%礼盒29%'
  )
  OR (
    lf.third_department_name = '直播部' AND lf.sku_id_name LIKE '%朱博士9%'
  )
  THEN '朱博士9元'
  WHEN lf.ad_account_name LIKE '%春春%' AND lf.channel_name_1 = '信息流'
  THEN '信息流-陈瑞春'
  WHEN lf.channel_name_1 = '信息流'
  AND lf.channel_name_2 = 'B站'
  AND (
    lf.page_id_name LIKE '%0元物化%'
  )
  THEN 'B站信息流-曹忆'
  WHEN lf.channel_name_1 = '信息流'
  AND lf.channel_name_2 = 'B站'
  AND (
    lf.page_id_name LIKE '%赵星义%'
  )
  THEN 'B站信息流-赵星义'
  WHEN lf.channel_name_1 = '信息流'
  AND lf.channel_name_2 = 'B站'
  AND (
    lf.page_id_name LIKE '%亚飞%'
    OR lf.source_put_plan_name LIKE '%亚飞%'
    OR lf.page_id_name LIKE '%初中-0元%'
  )
  THEN 'B站信息流-亚飞'
  WHEN (
    lf.flow_pool_name LIKE '%朱博士%'
    OR lf.flow_pool_name LIKE '%双博士%'
    OR lf.flow_pool_name LIKE '%教育规划%'
  )
  AND lf.third_department_name <> '线上商务部'
  AND lf.period_name NOT LIKE '%多学科拓展%'
  AND lf.rule_name NOT LIKE '%张杰%'
  AND lf.sku_id_name NOT LIKE '%马凯鹏IP%'
  AND lf.third_department_name = '直播部'
  THEN '朱博士29'
  WHEN lf.put_plan_name LIKE '%朱博士说教育%'
  AND lf.period_name NOT LIKE '%多学科拓展%'
  AND lf.flow_pool_name NOT LIKE '%高分讲堂%'
  AND lf.flow_pool_name NOT LIKE '%总裁%'
  AND lf.third_department_name = '直播部'
  THEN '朱博士29'
  WHEN (
    lf.flow_pool_name LIKE '%朱博士讲英语%'
    OR lf.flow_pool_name LIKE '%朱博士英语%'
    OR lf.flow_pool_name LIKE '%朱汉祺说英语%'
    OR lf.flow_pool_name LIKE '%朱博士说英语%'
    OR lf.flow_pool_name LIKE '%教育规划%'
    OR lf.flow_pool_name LIKE '%双博士英语规划%'
    OR lf.flow_pool_name LIKE '%朱博士满分英语%'
    OR lf.flow_pool_name LIKE '%英语教父朱博士%'
    OR (
      lf.flow_pool_name LIKE '%中考决胜天团%'
      AND lf.lead_purchase_intention_level1_category_name = '规划系统'
    )
  )
  AND lf.third_department_name = '直播部'
  AND lf.period_name NOT LIKE '%多学科拓展%'
  AND lf.sku_id_name NOT LIKE '%马凯鹏IP%'
  AND lf.third_department_name = '直播部'
  THEN '朱博士29'
  WHEN (
    lf.flow_pool_name LIKE '%汤哥%' OR lf.flow_pool_name LIKE '%汤老师%'
  )
  AND lf.period_name NOT LIKE '%多学科拓展%'
  AND lf.third_department_name IN ('直播部', '新媒体内容运营部')
  THEN '汤老师'
  WHEN lf.source_manager_name = '陈晓菁04'
  AND lf.channel_provider_name NOT LIKE '%开拓%'
  AND lf.put_plan_name NOT LIKE '%九学%'
  THEN '商务低价'
  WHEN (
    lf.flow_pool_name LIKE '%孟帝%'
    OR lf.flow_pool_name LIKE '%孟老师%'
    OR lf.flow_pool_name LIKE '%中考数学冲刺%'
    OR lf.flow_pool_name LIKE '%8升9数学%'
    OR lf.flow_pool_name LIKE '%孟亚飞讲数学%'
    OR lf.flow_pool_name LIKE '%中考冲刺%'
    OR lf.flow_pool_name LIKE '%中考满分冲刺%'
    OR lf.flow_pool_name LIKE '%押题王孟亚飞%'
    OR lf.flow_pool_name LIKE '%中考数学大通关%'
    OR lf.flow_pool_name LIKE '%中考数学规划%'
    OR lf.flow_pool_name LIKE '%亚飞数学%'
    OR lf.flow_pool_name LIKE '%孟帝数学%'
    OR lf.flow_pool_name LIKE '%亚飞秒解思维%'
    OR lf.flow_pool_name LIKE '%亚飞解题%'
  )
  AND lf.period_name NOT LIKE '%多学科拓展%'
  AND lf.channel_name_2 NOT LIKE '%KOL%'
  AND lf.third_department_name = '直播部'
  AND lf.channel_name_2 = '抖音'
  THEN '孟亚飞-1组-抖音'
  WHEN (
    lf.flow_pool_name LIKE '%孟帝%'
    OR lf.flow_pool_name LIKE '%孟老师%'
    OR lf.flow_pool_name LIKE '%中考数学冲刺%'
    OR lf.flow_pool_name LIKE '%8升9数学%'
    OR lf.flow_pool_name LIKE '%孟亚飞讲数学%'
    OR lf.flow_pool_name LIKE '%中考冲刺%'
    OR lf.flow_pool_name LIKE '%中考满分冲刺%'
    OR lf.flow_pool_name LIKE '%押题王孟亚飞%'
    OR lf.flow_pool_name LIKE '%中考数学大通关%'
    OR lf.flow_pool_name LIKE '%中考数学规划%'
    OR lf.flow_pool_name LIKE '%亚飞数学%'
    OR lf.flow_pool_name LIKE '%孟帝数学%'
  )
  AND lf.period_name NOT LIKE '%多学科拓展%'
  AND lf.channel_name_2 NOT LIKE '%KOL%'
  AND lf.third_department_name = '直播部'
  AND lf.channel_name_2 = '视频号'
  THEN '孟亚飞-1组-视频号'
  WHEN (
    lf.flow_pool_name LIKE '%孟帝%'
    OR lf.flow_pool_name LIKE '%孟老师%'
    OR lf.flow_pool_name LIKE '%中考数学冲刺%'
    OR lf.flow_pool_name LIKE '%8升9数学%'
    OR lf.flow_pool_name LIKE '%孟亚飞讲数学%'
    OR lf.flow_pool_name LIKE '%中考冲刺%'
    OR lf.flow_pool_name LIKE '%中考满分冲刺%'
    OR lf.flow_pool_name LIKE '%押题王孟亚飞%'
    OR lf.flow_pool_name LIKE '%中考数学大通关%'
    OR lf.flow_pool_name LIKE '%中考数学规划%'
    OR lf.flow_pool_name LIKE '%亚飞数学%'
    OR lf.flow_pool_name LIKE '%孟帝数学%'
  )
  AND lf.period_name NOT LIKE '%多学科拓展%'
  AND lf.channel_name_2 NOT LIKE '%KOL%'
  AND lf.third_department_name = '直播部'
  AND lf.channel_name_2 = 'B站'
  THEN '孟亚飞-1组-B站'
  WHEN (
    lf.flow_pool_name LIKE '%孟帝%'
    OR lf.flow_pool_name LIKE '%孟老师%'
    OR lf.flow_pool_name LIKE '%中考数学冲刺%'
    OR lf.flow_pool_name LIKE '%8升9数学%'
    OR lf.flow_pool_name LIKE '%孟亚飞讲数学%'
    OR lf.flow_pool_name LIKE '%中考冲刺%'
    OR lf.flow_pool_name LIKE '%中考满分冲刺%'
    OR lf.flow_pool_name LIKE '%押题王孟亚飞%'
    OR lf.flow_pool_name LIKE '%中考数学大通关%'
    OR lf.flow_pool_name LIKE '%中考数学规划%'
    OR lf.flow_pool_name LIKE '%亚飞数学%'
    OR lf.flow_pool_name LIKE '%孟帝数学%'
  )
  AND lf.period_name NOT LIKE '%多学科拓展%'
  AND lf.channel_name_2 NOT LIKE '%KOL%'
  AND lf.third_department_name = '直播部'
  AND lf.channel_name_2 NOT LIKE '%百度%'
  THEN '孟亚飞99-1组'
  WHEN (
    lf.flow_pool_name LIKE '%孟帝%'
    OR lf.flow_pool_name LIKE '%孟老师%'
    OR lf.flow_pool_name LIKE '%中考数学冲刺%'
    OR lf.flow_pool_name LIKE '%8升9数学%'
    OR lf.flow_pool_name LIKE '%孟亚飞讲数学%'
    OR lf.flow_pool_name LIKE '%中考冲刺%'
    OR lf.flow_pool_name LIKE '%中考满分冲刺%'
    OR lf.flow_pool_name LIKE '%押题王孟亚飞%'
    OR lf.flow_pool_name LIKE '%中考数学大通关%'
    OR lf.flow_pool_name LIKE '%中考数学规划%'
    OR lf.flow_pool_name LIKE '%亚飞数学%'
  )
  AND lf.period_name NOT LIKE '%多学科拓展%'
  AND lf.channel_name_2 NOT LIKE '%KOL%'
  AND lf.third_department_name = '直播部'
  AND lf.channel_name_2 = '百度'
  THEN '孟亚飞-1组-百度'
  WHEN lf.put_plan_name LIKE '%刘家晋讲图文%'
  OR lf.put_plan_name LIKE '%孟帝数学%'
  AND lf.third_department_name = '直播部'
  THEN '孟亚飞9元'
  WHEN lf.flow_pool_name LIKE '%汐子%'
  AND lf.period_name NOT LIKE '%多学科拓展%'
  AND lf.sku_id_name LIKE '%亚飞%'
  AND lf.third_department_name = '直播部'
  AND lf.rule_name LIKE '%99%'
  THEN '孟亚飞99-1组'
  WHEN (
    lf.flow_pool_name LIKE '%曹忆%'
    OR lf.flow_pool_name LIKE '%dudu%'
    OR lf.flow_pool_name LIKE '%中考决胜天团%'
    OR lf.flow_pool_name LIKE '%具象思维%'
    OR lf.flow_pool_name LIKE '%在逃发面馒头%'
    OR lf.flow_pool_name LIKE '%库洛米%'
    AND lf.lead_purchase_intention_level1_category_name <> '规划系统'
  )
  AND lf.period_name NOT LIKE '%多学科拓展%'
  AND lf.third_department_name IN ('直播部', '新媒体内容运营部')
  THEN '曹忆'
  WHEN (
    lf.first_department_name = '市场部'
    AND lf.channel_name_1 <> '站内获客'
    AND lf.channel_name_2 <> 'APP'
  )
  AND NOT COALESCE(
    (
      (
        lf.third_department_name = '私域运营部'
        AND lf.source_manager_name IN (
          '陈雷19',
          '崔慧敏01',
          '侯佳林01',
          '郑天琪02',
          '杨彬屹',
          '曹义鹏',
          '王硕阳',
          '于超研',
          '岳一帆02',
          '田起帆',
          '王绍阳',
          '肖佳兴',
          '姚佳03',
          '秦金萍',
          '李冞萤'
        )
      )
      OR (
        lf.flow_pool_name LIKE '%南通欣创%'
        OR lf.flow_pool_name LIKE '%人人通科技%'
        OR lf.flow_pool_name LIKE '%易而购%'
        OR lf.flow_pool_name LIKE '%济南梦航%'
        OR lf.flow_pool_name LIKE '%晨硕智学%'
        OR lf.flow_pool_name LIKE '%兴尧文化%'
        OR lf.flow_pool_name LIKE '%济南映像%'
        OR lf.flow_pool_name LIKE '%山东简单%'
        OR lf.flow_pool_name LIKE '%争鸣科技%'
      )
      OR (
        (
          lf.flow_pool_name LIKE '%家校共育%'
          OR lf.flow_pool_name LIKE '%保持热爱%'
          OR lf.flow_pool_name LIKE '%青松%'
          OR lf.flow_pool_name LIKE '%悟之道%'
        )
        AND lf.put_plan_name NOT LIKE '%0元%'
      )
      OR (
        lf.source_manager_name = '李宁24' AND lf.put_plan_name LIKE '%0转低%'
      )
      OR (
        lf.third_department_name = '私域运营部'
        AND lf.flow_original_order_activity_price IN ('100.0', '900.0', '300.0')
      )
      OR (
        lf.third_department_name = '私域运营部'
        AND lf.flow_original_order_activity_price IN ('0.0')
        AND lf.source_manager_name IN ('陈雷19', '崔慧敏01', '侯佳林01', '郑天琪02', '杨彬屹', '曹义鹏', '王硕阳', '于超研')
      )
      OR (
        lf.flow_pool_name LIKE '公导私'
      )
      OR (
        lf.flow_pool_name LIKE '%0转低转正%' OR lf.channel_name_2 = '产研测试'
      )
    ),
    FALSE
  )
  THEN '集团私域'
  WHEN lf.flow_pool_name LIKE '%未加好友%'
  THEN '市场私域未加好友'
  WHEN lf.third_department_name = '私域运营部'
  AND lf.rule_name NOT LIKE '%训练营%'
  AND NOT lf.virtual_fifth_department_name IN ('罗江博团队')
  AND lf.rule_name NOT LIKE '%复用%'
  AND lf.rule_name NOT LIKE '%未加好友%'
  AND lf.channel_name_2 <> '内部换量'
  THEN '市场私域低价单'
  WHEN lf.third_department_name = '私域运营部'
  AND lf.rule_name NOT LIKE '%训练营%'
  AND lf.rule_name NOT LIKE '%复用%'
  AND lf.rule_name NOT LIKE '%未加好友%'
  AND lf.channel_name_2 <> '内部换量'
  AND lf.flow_original_order_activity_price = '0.0'
  THEN '市场私域低价单'
  WHEN lf.channel_name_2 IN ('APP', 'M站', 'PC') AND lf.flow_pool_name NOT LIKE '%途途%'
  THEN 'APP'
  WHEN lf.channel_name_2 IN ('小程序') AND lf.flow_pool_name LIKE '%高途体验课%'
  THEN 'APP'
  WHEN lf.channel_provider_name LIKE '%唐山TMK%'
  THEN '唐山TMK'
  WHEN lf.source_manager_name IN ('高文羽')
  AND lf.channel_provider_name NOT LIKE '%唐山TMK%'
  AND lf.channel_provider_name NOT LIKE '%郑州%'
  THEN '人工外呼'
  WHEN lf.source_manager_name = '冯银晨' AND lf.channel_name_2 = '小红书'
  THEN '信息流-小红书'
  WHEN lf.channel_name_1 = '信息流'
  AND lf.channel_name_2 = 'B站'
  AND lf.third_department_name NOT LIKE '%投放%'
  AND (
    lf.rule_name LIKE '%0904期-短期班-新高二-市场私域低价单%'
    OR lf.flow_original_order_activity_price = '100'
    OR lf.page_id_name LIKE '%1元%'
  )
  THEN 'B站信息流-朱汉祺-1元'
  WHEN lf.channel_name_1 = '信息流'
  AND lf.channel_name_2 = 'B站'
  AND lf.third_department_name NOT LIKE '%投放%'
  AND lf.page_id_name LIKE '%汤雪%'
  THEN 'B站信息流-汤学健'
  WHEN (
    lf.channel_name_1 = '信息流'
    AND lf.channel_name_2 <> 'B站'
    AND lf.third_department_name NOT LIKE '%商务%'
    AND lf.put_plan_name NOT LIKE '%初三0元%'
    AND lf.put_plan_name NOT LIKE '%抖音私信%'
    AND lf.put_plan_name NOT LIKE '%高中0元%'
    AND lf.flow_original_order_activity_price NOT LIKE '%1990%'
  )
  OR (
    lf.channel_name_2 = 'B站' AND lf.third_department_name LIKE '%投放%'
  )
  THEN '信息流'
  WHEN lf.channel_name_1 = '信息流'
  AND lf.channel_name_2 = 'B站'
  AND lf.third_department_name NOT LIKE '%投放%'
  AND (
    lf.page_id_name LIKE '%郭艺%'
  )
  THEN 'B站信息流-郭艺'
  WHEN lf.channel_name_1 = '信息流'
  AND lf.channel_name_2 = 'B站'
  AND lf.third_department_name NOT LIKE '%投放%'
  AND (
    lf.page_id_name LIKE '%朱博士%'
  )
  THEN 'B站信息流-朱汉祺'
  WHEN lf.channel_name_1 = '信息流'
  AND lf.channel_name_2 = 'B站'
  AND lf.third_department_name NOT LIKE '%投放%'
  AND lf.page_id_name LIKE '%肖晗%'
  THEN 'B站信息流'
  WHEN lf.channel_name_1 = '信息流'
  AND lf.channel_name_2 = 'B站'
  AND lf.third_department_name NOT LIKE '%投放%'
  AND (
    lf.page_id_name LIKE '%马凯鹏%' OR lf.ad_account_name LIKE '%化学%'
  )
  THEN 'B站信息流-马凯鹏'
  WHEN lf.channel_name_1 = '信息流'
  AND lf.channel_name_2 = 'B站'
  AND lf.third_department_name NOT LIKE '%投放%'
  AND (
    lf.sku_id_name LIKE '%陈瑞春%' OR lf.rule_name LIKE '%陈瑞春%'
  )
  AND (
    lf.ad_account_name LIKE '%语文%'
    OR lf.source_put_plan_name LIKE '%自然流%'
    OR lf.page_id_name LIKE '%春春%'
  )
  THEN 'B站信息流-陈瑞春'
  WHEN lf.channel_name_1 = '信息流'
  AND lf.channel_name_2 = 'B站'
  AND lf.third_department_name NOT LIKE '%投放%'
  AND (
    lf.flow_original_order_activity_price LIKE '%2990%'
    OR lf.sku_id_name LIKE '%帅师%'
    OR lf.sku_id_name LIKE '%周帅%'
  )
  AND lf.ad_account_name LIKE '%语文%'
  AND (
    lf.flow_original_order_activity_price LIKE '%1980%'
    OR lf.flow_original_order_activity_price LIKE '%2980%'
    OR lf.flow_original_order_activity_price LIKE '%2990%'
  )
  THEN 'B站信息流-陈瑞春'
  WHEN lf.channel_name_1 = '信息流'
  AND lf.channel_name_2 = 'B站'
  AND lf.third_department_name NOT LIKE '%投放%'
  AND (
    lf.flow_original_order_activity_price LIKE '%2990%'
    OR lf.sku_id_name LIKE '%帅师%'
    OR lf.sku_id_name LIKE '%周帅%'
  )
  AND lf.ad_account_name NOT LIKE '%语文%'
  THEN 'B站信息流-周帅'
  WHEN lf.channel_name_1 = '信息流'
  AND lf.channel_name_2 = 'B站'
  AND lf.third_department_name NOT LIKE '%投放%'
  AND lf.flow_order_price LIKE '%1980%'
  AND lf.ad_account_name LIKE '%数学%'
  THEN 'B站信息流-周帅'
  WHEN lf.channel_name_1 = '短直电商'
  AND lf.channel_name_2 = 'B站'
  AND lf.third_department_name LIKE '%商务%'
  AND (
    lf.flow_pool_name LIKE '%春春%' OR lf.sku_id_name LIKE '%陈瑞春%'
  )
  THEN 'B站信息流-陈瑞春'
  WHEN lf.channel_name_1 = '短直电商'
  AND lf.channel_name_2 = 'B站'
  AND lf.third_department_name LIKE '%商务%'
  AND (
    lf.flow_pool_name LIKE '%朱博士%'
  )
  THEN 'B站信息流-朱汉祺'
  WHEN lf.channel_name_1 = '信息流'
  AND lf.channel_name_2 = 'B站'
  AND lf.third_department_name NOT LIKE '%投放%'
  AND lf.flow_original_order_activity_price NOT LIKE '%2980%'
  AND lf.flow_original_order_activity_price NOT LIKE '%2990%'
  AND lf.flow_original_order_activity_price NOT LIKE '%1980%'
  THEN 'B站信息流'
  WHEN lf.flow_pool_name = '百度搜索引擎' OR lf.channel_name_1 = '搜索营销'
  THEN '信息流搜索'
  WHEN lf.flow_pool_name LIKE '%小红书班课%'
  THEN '小红书投放'
  WHEN lf.third_department_name = '投放部'
  AND lf.get_customer_way_name = '短视频信息流'
  AND lf.flow_original_order_activity_price LIKE '%100%'
  THEN '信息流'
  WHEN lf.put_plan_name LIKE '%福哥私域0元%'
  THEN 'KOC-下引'
  WHEN lf.put_plan_name LIKE '%福哥私域5元%'
  THEN 'KOC-下引5元'
  WHEN lf.flow_pool_name = '中考加油' AND lf.sku_id_name LIKE '%孟帝%'
  THEN 'KOC-孟亚飞数学'
  WHEN lf.flow_pool_name = '中考加油' AND lf.sku_id_name LIKE '%帅师%'
  THEN 'KOC-周帅数学'
  WHEN lf.source_manager_name IN ('孙晗01', '方俊结01', '刘亦鹏02', '何木玲', '杨梓月', '张可意03', '任颖迪', '曹蕊07', '曲默晗')
  AND (
    lf.sku_id_name LIKE '%孟帝%'
    OR lf.sku_id_name LIKE '%dudu%'
    OR lf.sku_id_name LIKE '%市场初二%'
    OR lf.rule_name LIKE '%亚飞%'
    OR lf.sku_id_name LIKE '%初二高阳%'
    OR lf.sku_id_name LIKE '%高阳初二%'
    OR lf.sku_id_name LIKE '%精品初二%'
    OR lf.rule_name LIKE '%初二%'
    OR lf.sku_id_name LIKE '%菁英初三%'
    OR (
      lf.virtual_second_department_name = '菁英班学部'
      AND lf.lead_purchase_intention_level2_category_name = '初级'
      AND lf.lead_create_time >= '2026-04-15 00:00:00'
    )
  )
  THEN 'KOC-孟亚飞数学'
  WHEN lf.source_manager_name IN ('孙晗01', '方俊结01', '刘亦鹏02', '何木玲', '杨梓月', '张可意03', '任颖迪', '曹蕊07', '曲默晗')
  AND (
    lf.sku_id_name LIKE '%帅师%'
    OR lf.rule_name LIKE '%周帅%'
    OR lf.sku_id_name LIKE '%9月升高三%'
    OR lf.sku_id_name LIKE '%新高二%'
  )
  THEN 'KOC-周帅数学'
  WHEN lf.source_manager_name IN ('孙晗01', '方俊结01', '刘亦鹏02', '何木玲', '杨梓月', '张可意03', '任颖迪', '曹蕊07', '曲默晗')
  AND (
    lf.sku_id_name LIKE '%肖晗%' OR lf.rule_name LIKE '%肖晗%'
  )
  THEN 'KOC-肖晗'
  WHEN lf.source_manager_name IN ('孙晗01', '方俊结01', '刘亦鹏02', '何木玲', '杨梓月', '张可意03', '任颖迪', '曹蕊07', '曲默晗')
  AND lf.period_name NOT LIKE '%多学科拓展%'
  AND lf.sku_id_name NOT LIKE '%朱汉祺%'
  AND lf.sku_id_name NOT LIKE '%朱博士%'
  AND lf.sku_id_name NOT LIKE '%周帅%'
  AND lf.sku_id_name NOT LIKE '%29元%'
  THEN 'KOC-5元纯课'
  WHEN lf.source_manager_name IN ('孙晗01', '方俊结01', '刘亦鹏02', '何木玲', '杨梓月', '张可意03', '任颖迪', '曹蕊07', '曲默晗')
  AND lf.sku_id_name LIKE '%周帅%'
  THEN 'KOC-周帅'
  WHEN lf.third_department_name IN ('品牌效能部', 'KOC孵化部')
  AND lf.channel_name_2 IN ('抖音', '视频号', '快手', 'KOL')
  THEN '自孵化KOC-5元纯课'
  WHEN lf.third_department_name IN ('品牌效能部', 'KOC孵化部')
  AND lf.channel_name_2 IN ('抖音', '视频号', '快手', 'KOL')
  AND (
    lf.sku_id_name LIKE '%5元%'
    OR lf.sku_id_name LIKE '%11元%'
    OR lf.flow_original_order_activity_price LIKE '%1100%'
    OR lf.flow_original_order_activity_price LIKE '%500%'
    OR lf.flow_orders_income_amount LIKE '%1100%'
    OR lf.flow_orders_income_amount LIKE '%500%'
  )
  THEN '自孵化KOC-5元纯课'
  WHEN lf.source_manager_name IN (
    '包青青',
    '蔡瑞涵',
    '李文迁',
    '李佳馨44',
    '孙昊17',
    '王洁雅01',
    '王硕北',
    '朱文',
    '贾铭锐',
    '李壮壮04',
    '陈晓菁04',
    '赵艺雅'
  )
  AND lf.channel_name_2 LIKE '%社群%'
  THEN '进校社群'
  WHEN lf.source_manager_name IN (
    '包青青',
    '蔡瑞涵',
    '李文迁',
    '李佳馨44',
    '孙昊17',
    '王洁雅01',
    '王硕北',
    '朱文',
    '贾铭锐',
    '李壮壮04',
    '陈晓菁04',
    '赵艺雅'
  )
  AND (
    lf.channel_name_2 LIKE '%直推%'
    OR (
      lf.put_plan_name LIKE '%良师益友%' OR lf.put_plan_name LIKE '%弘诚1元%'
    )
  )
  THEN '进校直推'
  WHEN lf.source_manager_name IN (
    '包青青',
    '蔡瑞涵',
    '李文迁',
    '李佳馨44',
    '孙昊17',
    '王洁雅01',
    '王硕北',
    '朱文',
    '贾铭锐',
    '李壮壮04',
    '陈晓菁04',
    '赵艺雅'
  )
  AND lf.channel_name_2 LIKE '%TMK%'
  AND (
    lf.page_id_name LIKE '%1元%' OR lf.channel_provider_name LIKE '%禾顺云%'
  )
  THEN '进校TMK1元'
  WHEN lf.source_manager_name IN (
    '包青青',
    '蔡瑞涵',
    '李文迁',
    '李佳馨44',
    '孙昊17',
    '王洁雅01',
    '王硕北',
    '朱文',
    '贾铭锐',
    '李壮壮04',
    '陈晓菁04',
    '赵艺雅'
  )
  AND lf.channel_name_2 LIKE '%TMK%'
  AND lf.page_id_name LIKE '%9元%'
  THEN '进校TMK9元'
  WHEN lf.source_manager_name IN (
    '包青青',
    '蔡瑞涵',
    '李文迁',
    '李佳馨44',
    '孙昊17',
    '王洁雅01',
    '王硕北',
    '朱文',
    '贾铭锐',
    '李壮壮04',
    '陈晓菁04',
    '赵艺雅'
  )
  AND lf.channel_name_2 LIKE '%书商%'
  THEN '进校书商'
  WHEN lf.source_manager_name IN (
    '包青青',
    '蔡瑞涵',
    '李文迁',
    '李佳馨44',
    '孙昊17',
    '王洁雅01',
    '王硕北',
    '朱文',
    '贾铭锐',
    '李壮壮04',
    '陈晓菁04',
    '赵艺雅'
  )
  AND lf.channel_name_2 LIKE '%综合%'
  AND lf.put_plan_name LIKE '%18%'
  THEN '进校直播'
  WHEN lf.source_manager_name IN (
    '包青青',
    '蔡瑞涵',
    '李文迁',
    '李佳馨44',
    '孙昊17',
    '王洁雅01',
    '王硕北',
    '朱文',
    '贾铭锐',
    '李壮壮04',
    '陈晓菁04',
    '赵艺雅'
  )
  AND lf.channel_name_2 LIKE '%直播%'
  THEN '进校直播'
  WHEN lf.source_manager_name IN (
    '包青青',
    '蔡瑞涵',
    '李文迁',
    '李佳馨44',
    '孙昊17',
    '王洁雅01',
    '王硕北',
    '朱文',
    '贾铭锐',
    '李壮壮04',
    '赵艺雅'
  )
  AND lf.put_plan_name NOT LIKE '%0元%'
  AND lf.flow_pool_name NOT LIKE '%家校共育%'
  AND lf.flow_pool_name NOT LIKE '%保持热爱%'
  AND lf.flow_pool_name NOT LIKE '%青松%'
  AND lf.flow_pool_name NOT LIKE '%原子初三%'
  AND lf.flow_pool_name NOT LIKE '%南通欣创%'
  AND lf.flow_pool_name NOT LIKE '%悟之道%'
  AND lf.flow_pool_name NOT LIKE '%济南梦航%'
  AND lf.channel_name_3 <> '社群'
  AND lf.put_plan_name NOT LIKE '%善悟%'
  AND lf.put_plan_name NOT LIKE '%人人通%'
  AND lf.put_plan_name NOT LIKE '%%济南格乐'
  AND lf.flow_pool_name NOT LIKE '%晨硕智学%'
  AND lf.flow_pool_name NOT LIKE '%兴尧文化%'
  AND lf.flow_pool_name NOT LIKE '%济南映像%'
  AND lf.flow_pool_name NOT LIKE '%山东简单%'
  AND lf.flow_pool_name NOT LIKE '%争鸣科技%'
  THEN '商务低价'
  WHEN lf.flow_pool_name LIKE '%南通欣创%'
  OR lf.flow_pool_name LIKE '%人人通科技%'
  OR lf.flow_pool_name LIKE '%易而购%'
  OR lf.flow_pool_name LIKE '%济南梦航%'
  OR lf.flow_pool_name LIKE '%晨硕智学%'
  OR lf.flow_pool_name LIKE '%兴尧文化%'
  OR lf.flow_pool_name LIKE '%济南映像%'
  OR lf.flow_pool_name LIKE '%山东简单%'
  OR lf.flow_pool_name LIKE '%争鸣科技%'
  THEN '进校私域合作'
  WHEN (
    lf.flow_pool_name LIKE '%家校共育%'
    OR lf.flow_pool_name LIKE '%保持热爱%'
    OR lf.flow_pool_name LIKE '%青松%'
    OR lf.flow_pool_name LIKE '%悟之道%'
  )
  AND lf.put_plan_name NOT LIKE '%0元%'
  THEN '进校私域合作'
  WHEN lf.source_manager_name = '李宁24' AND lf.put_plan_name LIKE '%0转低%'
  THEN '进校私域合作'
  WHEN lf.third_department_name = '私域运营部'
  AND lf.flow_original_order_activity_price IN ('100.0', '900.0', '300.0')
  THEN '进校私域合作'
  WHEN lf.third_department_name = '私域运营部'
  AND lf.flow_original_order_activity_price IN ('0.0')
  AND lf.source_manager_name IN ('陈雷19', '崔慧敏01', '侯佳林01', '郑天琪02', '杨彬屹', '曹义鹏', '王硕阳', '于超研')
  THEN '进校私域合作'
  WHEN lf.third_department_name = '私域运营部'
  AND lf.channel_name_1 = '市场私域'
  AND lf.put_plan_name NOT LIKE '%公导私%'
  AND lf.put_plan_name NOT LIKE '%公转私%'
  AND lf.flow_original_order_activity_price = '0.0'
  AND lf.rule_name NOT LIKE '%激活%'
  AND lf.rule_name NOT LIKE '%咨询%'
  AND lf.rule_name NOT LIKE '%训练营%'
  AND lf.virtual_fifth_department_name NOT LIKE '%罗江博%'
  AND lf.virtual_fifth_department_name NOT LIKE '%郑州学习顾问二部%'
  AND NOT lf.source_manager_name IN ('陈雷19', '崔慧敏01', '侯佳林01', '郑天琪02', '杨彬屹', '曹义鹏', '王硕阳', '于超研')
  THEN '市场私域低价单'
  WHEN lf.source_manager_name IN ('耿文超', '晋翠翠', '赵语诗', '王慧敏13', '于新茹', '梁超01', '刘晓20', '王玉120', '吕佳乐01')
  AND lf.channel_provider_name LIKE '%格乐教育%'
  AND lf.channel_name_2 LIKE '%直播%'
  THEN '创新社群'
  WHEN lf.source_manager_name IN ('耿文超', '晋翠翠', '赵语诗', '王慧敏13', '于新茹', '梁超01', '刘晓20', '王玉120', '吕佳乐01')
  AND lf.channel_name_2 LIKE '%社群%'
  THEN '创新社群'
  WHEN lf.source_manager_name IN ('耿文超', '晋翠翠', '赵语诗', '王慧敏13', '于新茹', '梁超01', '刘晓20', '王玉120', '吕佳乐01')
  AND (
    lf.channel_name_2 LIKE '%直推%' OR lf.put_plan_name LIKE '%直推%'
  )
  THEN '创新直推'
  WHEN lf.source_manager_name IN ('耿文超', '晋翠翠', '赵语诗', '王慧敏13', '于新茹', '梁超01', '刘晓20', '王玉120', '吕佳乐01')
  AND (
    lf.channel_name_2 LIKE '%书商%'
    OR lf.put_plan_name LIKE '%书商%'
    OR lf.page_id_name LIKE '%书商%'
  )
  THEN '创新书商'
  WHEN lf.source_manager_name IN ('耿文超', '晋翠翠', '赵语诗', '王慧敏13', '于新茹', '梁超01', '刘晓20', '王玉120', '吕佳乐01')
  AND lf.channel_name_2 LIKE '%TMK%'
  AND lf.page_id_name LIKE '%1元%'
  THEN '创新TMK1元'
  WHEN lf.source_manager_name IN ('耿文超', '晋翠翠', '赵语诗', '王慧敏13', '于新茹', '梁超01', '刘晓20', '王玉120', '吕佳乐01')
  AND lf.channel_name_2 LIKE '%TMK%'
  AND lf.page_id_name LIKE '%9元%'
  THEN '创新TMK9元'
  WHEN lf.source_manager_name IN ('耿文超', '晋翠翠', '赵语诗', '王慧敏13', '于新茹', '梁超01', '刘晓20', '王玉120', '吕佳乐01')
  AND (
    lf.channel_name_2 LIKE '%直播%' OR lf.page_id_name LIKE '%进校%'
  )
  THEN '创新直播'
  WHEN lf.source_manager_name IN ('耿文超', '晋翠翠', '赵语诗', '王慧敏13', '于新茹', '梁超01', '刘晓20', '王玉120', '吕佳乐01')
  AND lf.channel_name_2 <> '公众号'
  AND lf.channel_name_1 = '商务'
  AND lf.flow_pool_name <> '高途云集图书专营店-自然流'
  AND lf.flow_pool_name <> '高途旗舰店—线索—yuxinru'
  AND lf.put_plan_name NOT LIKE '%社群%'
  AND lf.put_plan_name NOT LIKE '%小红书班课%'
  AND lf.put_plan_name NOT LIKE '%外部图书供量%'
  AND lf.channel_second_provider_name NOT LIKE '%沃德丰店铺线索赠课%'
  AND lf.channel_second_provider_name NOT LIKE '%智慧城-图书%'
  AND lf.put_plan_name NOT LIKE '%育甲%'
  AND lf.flow_pool_name NOT LIKE '%周长磊%'
  THEN '创新商务'
  WHEN lf.source_manager_name IN ('高曼曼01', '杨思怡', '宋向函')
  THEN '图书KOC达人'
  WHEN lf.flow_pool_name LIKE '%市场部-微信私域%'
  OR lf.flow_pool_name LIKE '%市场部-规划报告%'
  OR lf.flow_pool_name LIKE '%规划报告%'
  OR lf.flow_pool_name LIKE '%市场部-小红书%'
  OR lf.flow_pool_name LIKE '%孟浩宇%'
  THEN '市场私域低价单'
  WHEN lf.flow_pool_name LIKE '公导私'
  THEN '进校私域合作'
  WHEN (
    (
      lf.flow_pool_name LIKE '%增长组%'
      OR lf.channel_name_3 = '公众号'
      OR lf.second_department_name = '微信生态部'
    )
    AND lf.channel_name_2 <> 'APP'
  )
  AND NOT COALESCE(
    (
      (
        lf.third_department_name = '私域运营部'
        AND lf.source_manager_name IN (
          '陈雷19',
          '崔慧敏01',
          '侯佳林01',
          '郑天琪02',
          '杨彬屹',
          '曹义鹏',
          '王硕阳',
          '于超研',
          '岳一帆02',
          '田起帆',
          '王绍阳',
          '肖佳兴',
          '姚佳03',
          '秦金萍',
          '李冞萤'
        )
      )
      OR (
        lf.flow_pool_name LIKE '%南通欣创%'
        OR lf.flow_pool_name LIKE '%人人通科技%'
        OR lf.flow_pool_name LIKE '%易而购%'
        OR lf.flow_pool_name LIKE '%济南梦航%'
        OR lf.flow_pool_name LIKE '%晨硕智学%'
        OR lf.flow_pool_name LIKE '%兴尧文化%'
        OR lf.flow_pool_name LIKE '%济南映像%'
        OR lf.flow_pool_name LIKE '%山东简单%'
        OR lf.flow_pool_name LIKE '%争鸣科技%'
      )
      OR (
        (
          lf.flow_pool_name LIKE '%家校共育%'
          OR lf.flow_pool_name LIKE '%保持热爱%'
          OR lf.flow_pool_name LIKE '%青松%'
          OR lf.flow_pool_name LIKE '%悟之道%'
        )
        AND lf.put_plan_name NOT LIKE '%0元%'
      )
      OR (
        lf.source_manager_name = '李宁24' AND lf.put_plan_name LIKE '%0转低%'
      )
      OR (
        lf.third_department_name = '私域运营部'
        AND lf.flow_original_order_activity_price IN ('100.0', '900.0', '300.0')
      )
      OR (
        lf.third_department_name = '私域运营部'
        AND lf.flow_original_order_activity_price IN ('0.0')
        AND lf.source_manager_name IN ('陈雷19', '崔慧敏01', '侯佳林01', '郑天琪02', '杨彬屹', '曹义鹏', '王硕阳', '于超研')
      )
      OR (
        lf.flow_pool_name LIKE '公导私'
      )
      OR (
        lf.flow_pool_name LIKE '%0转低转正%' OR lf.channel_name_2 = '产研测试'
      )
    ),
    FALSE
  )
  THEN '集团私域'
  WHEN lf.put_plan_name LIKE '%星耀%'
  OR lf.put_plan_name LIKE '%物理展博%'
  OR lf.put_plan_name LIKE '%物理谢丽荣%'
  OR lf.put_plan_name LIKE '%牟恩伯%'
  OR lf.put_plan_name LIKE '%王赞%'
  OR lf.put_plan_name LIKE '%张磊老师高中数学%'
  OR lf.put_plan_name LIKE '%雯姐高中物理大讲堂%'
  THEN '百度星耀'
  WHEN lf.source_manager_name = '刘福云'
  AND (
    lf.sku_id_name LIKE '%瑞春%' OR lf.sku_id_name LIKE '%春春%'
  )
  THEN '陈瑞春'
  WHEN lf.third_department_name = '直播部'
  AND lf.sku_id_name LIKE '%周帅%'
  AND lf.channel_name_2 IN ('百度', 'B站')
  THEN '周帅'
  WHEN lf.third_department_name = '直播部'
  AND lf.sku_id_name LIKE '%孟亚飞%'
  AND lf.rule_name LIKE '%99%'
  THEN '孟亚飞99-1组'
  WHEN lf.third_department_name = '直播部' AND lf.sku_id_name LIKE '%朱汉祺%'
  THEN '朱博士99'
  WHEN lf.flow_pool_name LIKE '%0转低转正%' OR lf.channel_name_2 = '产研测试'
  THEN '进校私域合作'
  WHEN lf.flow_pool_name LIKE '%天津智慧双子%'
  THEN '创新社群'
  WHEN lf.third_department_name LIKE '%城市定制%'
  THEN '点睛卷'
  WHEN lf.period_name LIKE '%多学科拓展%' AND lf.third_department_name LIKE '%私域运营%'
  THEN '市场私域入群'
  WHEN lf.put_plan_name LIKE '%赠课失败%' AND lf.third_department_name = '线上商务部'
  THEN 'KOC赠课失败'
  WHEN lf.flow_pool_name LIKE '%自然流%'
  AND lf.source_manager_name IN ('孙晗01', '方俊结01', '刘亦鹏02', '何木玲', '杨梓月', '张可意03', '任颖迪', '曹蕊07', '曲默晗')
  AND lf.sku_id_name LIKE '%周帅%'
  THEN 'KOC-周帅'
  WHEN lf.flow_pool_name LIKE '%自然流%'
  AND lf.source_manager_name IN ('孙晗01', '方俊结01', '刘亦鹏02', '何木玲', '杨梓月', '张可意03', '任颖迪', '曹蕊07', '曲默晗')
  AND lf.sku_id_name LIKE '%肖晗%'
  THEN 'KOC-肖晗'
  WHEN lf.flow_pool_name LIKE '%自然流%'
  AND lf.source_manager_name IN ('孙晗01', '方俊结01', '刘亦鹏02', '何木玲', '杨梓月', '张可意03', '任颖迪', '曹蕊07', '曲默晗')
  AND lf.sku_id_name LIKE '%朱汉祺%'
  AND lf.flow_original_order_activity_price LIKE '%1100%'
  THEN 'KOC-5元朱汉祺'
  WHEN lf.flow_pool_name LIKE '%自然流%'
  AND lf.source_manager_name IN ('赵语诗', '崔文轩', '孙培尧')
  THEN '自孵化KOC-5元纯课'
  WHEN lf.flow_pool_name LIKE '%自然流%'
  AND (
    lf.sku_id_name LIKE '%朱博士%' OR lf.sku_id_name LIKE '%朱汉祺%'
  )
  AND lf.rule_name LIKE '%9%'
  AND lf.rule_name NOT LIKE '%29%'
  AND lf.third_department_name IN ('直播部', '新媒体内容运营部', '市场一组')
  THEN '朱博士99'
  WHEN lf.flow_pool_name LIKE '%自然流%'
  AND lf.sku_id_name LIKE '%朱博士%'
  AND lf.third_department_name IN ('直播部', '新媒体内容运营部', '市场一组')
  THEN '朱博士99'
  WHEN lf.flow_pool_name LIKE '%自然流%'
  AND lf.sku_id_name LIKE '%亚飞%'
  AND lf.rule_name LIKE '%99%'
  AND lf.third_department_name IN ('直播部', '新媒体内容运营部', '市场一组')
  THEN '孟亚飞99-1组'
  WHEN lf.flow_pool_name LIKE '%自然流%'
  AND lf.sku_id_name LIKE '%亚飞%'
  AND lf.third_department_name IN ('直播部', '新媒体内容运营部', '市场一组')
  THEN '孟亚飞9元'
  WHEN lf.flow_pool_name LIKE '%自然流%' AND lf.sku_id_name LIKE '%曹忆%'
  THEN '曹忆'
  WHEN lf.flow_pool_name LIKE '%自然流%'
  AND lf.rule_name LIKE '%朱博士%'
  AND lf.third_department_name IN ('直播部', '新媒体内容运营部', '市场一组')
  THEN '朱博士99'
  WHEN lf.flow_pool_name LIKE '%自然流%'
  AND lf.source_manager_name LIKE '%邵万昕%'
  AND lf.third_department_name IN ('直播部', '新媒体内容运营部', '市场一组')
  THEN '朱博士99'
  WHEN lf.flow_pool_name LIKE '%自然流%'
  AND lf.rule_name LIKE '%亚飞%'
  AND lf.rule_name LIKE '%99%'
  THEN '孟亚飞99-1组'
  WHEN lf.flow_pool_name LIKE '%自然流%' AND lf.rule_name LIKE '%亚飞%'
  THEN '孟亚飞9元'
  WHEN lf.flow_pool_name LIKE '%自然流%' AND lf.rule_name LIKE '%郭艺%'
  THEN '郭艺'
  WHEN lf.flow_pool_name LIKE '%自然流%' AND lf.rule_name LIKE '%汤雪%'
  THEN '汤老师'
  WHEN lf.flow_pool_name LIKE '%自然流%' AND lf.rule_name LIKE '%曹忆%'
  THEN '曹忆'
  WHEN lf.flow_pool_name LIKE '%途途教室%' OR lf.first_department_name LIKE 'TUTU'
  THEN '途途APP'
  WHEN lf.source_manager_name IN ('宋莹莹', '辛世如') AND lf.channel_name_2 IN ('视频号')
  THEN '信息流-虚拟号挂车'
  WHEN lf.rule_name LIKE '%训练营%' AND lf.rule_name LIKE '%市场私域%'
  THEN '市场私域入群'
  WHEN lf.channel_name_1 = '信息流'
  AND (
    lf.put_plan_name LIKE '%抖音私信%'
    OR lf.put_plan_name LIKE '%初三0元%'
    OR lf.put_plan_name LIKE '%高中0元%'
  )
  THEN '信息流-抖音私信'
  WHEN lf.rule_name LIKE '%途途私域%'
  OR (
    lf.rule_name LIKE '%私域%' AND lf.first_department_name = 'TT'
  )
  THEN '途途私域'
  ELSE '其他未知流量'
END AS channel_1 /* ★ 0723渠道映射（使用 lead_info 字段） */,
 COALESCE(
  lf.lf_period_name,
  lf.attribute_period,
  CASE
    WHEN REGEXP_LIKE(rr.group_period_term, '^[0-9]{8}期$')
    AND CAST(DATE_PARSE(SUBSTR(rr.group_period_term, 1, 8), '%Y%m%d') AS DATE) BETWEEN CAST('2026-07-14' AS DATE) AND CAST('2026-07-19' AS DATE)
    THEN '20260716期'
    WHEN REGEXP_LIKE(rr.group_period_term, '^[0-9]{8}期$')
    AND CAST(DATE_PARSE(SUBSTR(rr.group_period_term, 1, 8), '%Y%m%d') AS DATE) BETWEEN CAST('2026-07-20' AS DATE) AND CAST('2026-07-25' AS DATE)
    THEN '20260722期'
    WHEN REGEXP_LIKE(rr.group_period_term, '^[0-9]{8}期$')
    AND CAST(DATE_PARSE(SUBSTR(rr.group_period_term, 1, 8), '%Y%m%d') AS DATE) BETWEEN CAST('2026-07-26' AS DATE) AND CAST('2026-07-31' AS DATE)
    THEN '20260728期'
    WHEN REGEXP_LIKE(rr.group_period_term, '^[0-9]{8}期$')
    AND CAST(DATE_PARSE(SUBSTR(rr.group_period_term, 1, 8), '%Y%m%d') AS DATE) BETWEEN CAST('2026-08-01' AS DATE) AND CAST('2026-08-06' AS DATE)
    THEN '20260803期'
    WHEN REGEXP_LIKE(rr.group_period_term, '^[0-9]{8}期$')
    AND CAST(DATE_PARSE(SUBSTR(rr.group_period_term, 1, 8), '%Y%m%d') AS DATE) BETWEEN CAST('2026-08-07' AS DATE) AND CAST('2026-08-12' AS DATE)
    THEN '20260808期'
    WHEN REGEXP_LIKE(rr.group_period_term, '^[0-9]{8}期$')
    AND CAST(DATE_PARSE(SUBSTR(rr.group_period_term, 1, 8), '%Y%m%d') AS DATE) BETWEEN CAST('2026-08-13' AS DATE) AND CAST('2026-08-18' AS DATE)
    THEN '20260815期'
    WHEN REGEXP_LIKE(rr.group_period_term, '^[0-9]{4}期$')
    AND SUBSTR(lf.qici, 1, 4) = '2026'
    AND SUBSTR(rr.group_period_term, 1, 4) BETWEEN '0714' AND '0719'
    THEN '20260716期'
    WHEN REGEXP_LIKE(rr.group_period_term, '^[0-9]{4}期$')
    AND SUBSTR(lf.qici, 1, 4) = '2026'
    AND SUBSTR(rr.group_period_term, 1, 4) BETWEEN '0720' AND '0725'
    THEN '20260722期'
    WHEN REGEXP_LIKE(rr.group_period_term, '^[0-9]{4}期$')
    AND SUBSTR(lf.qici, 1, 4) = '2026'
    AND SUBSTR(rr.group_period_term, 1, 4) BETWEEN '0726' AND '0731'
    THEN '20260728期'
    WHEN REGEXP_LIKE(rr.group_period_term, '^[0-9]{4}期$')
    AND SUBSTR(lf.qici, 1, 4) = '2026'
    AND SUBSTR(rr.group_period_term, 1, 4) BETWEEN '0801' AND '0806'
    THEN '20260803期'
    WHEN REGEXP_LIKE(rr.group_period_term, '^[0-9]{4}期$')
    AND SUBSTR(lf.qici, 1, 4) = '2026'
    AND SUBSTR(rr.group_period_term, 1, 4) BETWEEN '0807' AND '0812'
    THEN '20260808期'
    WHEN REGEXP_LIKE(rr.group_period_term, '^[0-9]{4}期$')
    AND SUBSTR(lf.qici, 1, 4) = '2026'
    AND SUBSTR(rr.group_period_term, 1, 4) BETWEEN '0813' AND '0818'
    THEN '20260815期'
    WHEN REGEXP_LIKE(rr.group_period_term, '^[0-9]{8}期$')
    THEN DATE_FORMAT(
      DATE_TRUNC('WEEK', DATE_PARSE(SUBSTR(rr.group_period_term, 1, 8), '%Y%m%d')) + INTERVAL '4' DAY,
      '%Y%m%d'
    ) || '期'
    WHEN REGEXP_LIKE(rr.group_period_term, '^[0-9]{4}期$')
    THEN DATE_FORMAT(
      DATE_TRUNC(
        'WEEK',
        DATE_PARSE(
          CONCAT(
            CASE
              WHEN CAST(SUBSTR(rr.group_period_term, 1, 2) AS INTEGER) >= 11
              AND CAST(SUBSTR(lf.qici, 5, 2) AS INTEGER) <= 2
              THEN CAST(CAST(SUBSTR(lf.qici, 1, 4) AS INTEGER) - 1 AS VARCHAR)
              ELSE SUBSTR(lf.qici, 1, 4)
            END,
            SUBSTR(rr.group_period_term, 1, 4)
          ),
          '%Y%m%d'
        )
      ) + INTERVAL '4' DAY,
      '%Y%m%d'
    ) || '期'
    ELSE NULL
  END
) AS friday_period
FROM financial_context lf
LEFT JOIN rule_once rr ON rr.lead_id=lf.lead_id AND rr.account_domain=lf.email_prefix
),
zx_active AS (
SELECT
  employee_email_name,
  xiaozu,
  jingli
FROM (
  SELECT
    zx.*,
    ROW_NUMBER() OVER (
      PARTITION BY zx.employee_email_name
      ORDER BY CASE
        WHEN zx.department = '郑州顾问部'
        THEN 1
        WHEN zx.department = '西安一部'
        THEN 2
        WHEN zx.department = '西安二部'
        THEN 3
        ELSE 9
      END, zx.employee_email_prefix, zx.xiaozu, zx.jingli
    ) AS rn
  FROM temp_table.dingxi01_jiagou_zx AS zx
  WHERE
    CAST(zx.zaizhi AS VARCHAR) = '1' AND zx.department IN ('郑州顾问部', '西安一部', '西安二部')
) AS t
WHERE
  rn = 1
),
jiagou_period AS (
SELECT
  qici,
  department,
  employee_email_name,
  xiaozu,
  jingli
FROM (
  SELECT
    NULLIF(TRIM(CAST(jg.qici AS VARCHAR)), '') AS qici,
    NULLIF(TRIM(CAST(jg.department AS VARCHAR)), '') AS department,
    NULLIF(TRIM(CAST(jg.employee_email_name AS VARCHAR)), '') AS employee_email_name,
    NULLIF(TRIM(CAST(jg.xiaozu AS VARCHAR)), '') AS xiaozu,
    NULLIF(TRIM(CAST(jg.jingli AS VARCHAR)), '') AS jingli,
    ROW_NUMBER() OVER (
      PARTITION BY NULLIF(TRIM(CAST(jg.qici AS VARCHAR)), ''), NULLIF(TRIM(CAST(jg.department AS VARCHAR)), ''), NULLIF(TRIM(CAST(jg.employee_email_name AS VARCHAR)), '')
      ORDER BY CASE WHEN NOT NULLIF(TRIM(CAST(jg.xiaozu AS VARCHAR)), '') IS NULL THEN 0 ELSE 1 END, NULLIF(TRIM(CAST(jg.xiaozu AS VARCHAR)), ''), NULLIF(TRIM(CAST(jg.jingli AS VARCHAR)), '')
    ) AS rn
  FROM temp_table.dingxi01_jiagou_db AS jg
) AS t
WHERE
  rn = 1
),
base AS (
SELECT
  b.*,
  CASE
    WHEN b.qici = b.friday_period
    THEN 0
    WHEN b.period_gap = 7
    THEN 1
    WHEN b.period_gap BETWEEN 14 AND 21
    THEN 2
    WHEN b.period_gap = -7
    THEN 4
    WHEN (
      b.friday_period = '20260716期' AND b.qici = '20260722期'
    )
    OR (
      b.friday_period = '20260722期' AND b.qici = '20260728期'
    )
    OR (
      b.friday_period = '20260728期' AND b.qici = '20260803期'
    )
    OR (
      b.friday_period = '20260803期' AND b.qici = '20260808期'
    )
    OR (
      b.friday_period = '20260808期' AND b.qici = '20260815期'
    )
    OR (
      b.friday_period = '20260815期' AND b.qici = '20260821期'
    )
    THEN 1
    WHEN (
      b.friday_period = '20260716期' AND b.qici = '20260728期'
    )
    OR (
      b.friday_period = '20260722期' AND b.qici = '20260803期'
    )
    OR (
      b.friday_period = '20260728期' AND b.qici = '20260808期'
    )
    OR (
      b.friday_period = '20260803期' AND b.qici = '20260815期'
    )
    OR (
      b.friday_period = '20260808期' AND b.qici = '20260821期'
    )
    THEN 2
    WHEN (
      b.friday_period = '20260722期' AND b.qici = '20260716期'
    )
    OR (
      b.friday_period = '20260728期' AND b.qici = '20260722期'
    )
    OR (
      b.friday_period = '20260803期' AND b.qici = '20260728期'
    )
    OR (
      b.friday_period = '20260808期' AND b.qici = '20260803期'
    )
    OR (
      b.friday_period = '20260815期' AND b.qici = '20260808期'
    )
    OR (
      b.friday_period = '20260821期' AND b.qici = '20260815期'
    )
    THEN 4
    ELSE 3
  END AS week_diff
FROM (
  SELECT
    rule.*,
    COALESCE(jg.xiaozu, zx.xiaozu) AS xiaozu,
    COALESCE(jg.jingli, zx.jingli) AS jingli,
    TRY(
      DATE_DIFF(
        'DAY',
        TRY(DATE_PARSE(SUBSTR(rule.friday_period, 1, 8), '%Y%m%d')),
        TRY(DATE_PARSE(SUBSTR(rule.qici, 1, 8), '%Y%m%d'))
      )
    ) AS period_gap
  FROM rule
  LEFT JOIN zx_active AS zx
    ON zx.employee_email_name = rule.name
  LEFT JOIN jiagou_period AS jg
    ON jg.qici = rule.friday_period
    AND jg.department = rule.depart
    AND jg.employee_email_name = rule.name
) AS b
),
bucket_agg AS (
SELECT
  b.qici,
  b.channel_1,
  b.jingli,
  b.xiaozu,
  b.grade_list,
  b.name,
  SUM(CASE WHEN b.week_diff = 0 THEN b.name_total_price ELSE 0 END) AS gmv_7,
  SUM(CASE WHEN b.week_diff = 1 THEN b.name_total_price ELSE 0 END) AS gmv_14,
  SUM(CASE WHEN b.week_diff = 2 THEN b.name_total_price ELSE 0 END) AS gmv_30,
  SUM(CASE WHEN b.week_diff = 3 THEN b.name_total_price ELSE 0 END) AS gmv_n30,
  SUM(CASE WHEN b.week_diff = 4 THEN b.name_total_price ELSE 0 END) AS gmv_7_h,
  SUM(CASE WHEN b.week_diff = 0 AND TRUE THEN b.refund_price ELSE 0 END) AS refund_7,
  SUM(CASE WHEN b.week_diff = 1 AND TRUE THEN b.refund_price ELSE 0 END) AS refund_14,
  SUM(CASE WHEN b.week_diff = 2 AND TRUE THEN b.refund_price ELSE 0 END) AS refund_30,
  SUM(CASE WHEN b.week_diff = 3 AND TRUE THEN b.refund_price ELSE 0 END) AS refund_n30,
  SUM(CASE WHEN b.week_diff = 4 AND TRUE THEN b.refund_price ELSE 0 END) AS refund_7_p,
  SUM(CASE WHEN TRUE THEN b.refund_price ELSE 0 END) AS refund_total,
  SUM(b.name_total_price) AS gmv_finance_total
FROM base AS b
GROUP BY
  b.qici,
  b.channel_1,
  b.jingli,
  b.xiaozu,
  b.grade_list,
  b.name
),
metric_agg AS (
SELECT
  m.period_name AS qici,
  m.channel_map AS channel_1,
  m.jingli,
  m.xiaozu,
  m.grade_1 AS grade_list,
  m.employee_email_name AS name,
  SUM(m.can_renew_ds_count_a) AS can_renew_ds_count_a
FROM (
  WITH m2253_data AS (
    SELECT DISTINCT
      CASE
        WHEN CAST(DATE_PARSE(REPLACE(CONCAT(group_period_year, group_period_term), '期', ''), '%Y%m%d') AS DATE) BETWEEN CAST('2026-07-14' AS DATE) AND CAST('2026-07-19' AS DATE)
        THEN '20260716期'
        WHEN CAST(DATE_PARSE(REPLACE(CONCAT(group_period_year, group_period_term), '期', ''), '%Y%m%d') AS DATE) BETWEEN CAST('2026-07-20' AS DATE) AND CAST('2026-07-25' AS DATE)
        THEN '20260722期'
        WHEN CAST(DATE_PARSE(REPLACE(CONCAT(group_period_year, group_period_term), '期', ''), '%Y%m%d') AS DATE) BETWEEN CAST('2026-07-26' AS DATE) AND CAST('2026-07-31' AS DATE)
        THEN '20260728期'
        WHEN CAST(DATE_PARSE(REPLACE(CONCAT(group_period_year, group_period_term), '期', ''), '%Y%m%d') AS DATE) BETWEEN CAST('2026-08-01' AS DATE) AND CAST('2026-08-06' AS DATE)
        THEN '20260803期'
        WHEN CAST(DATE_PARSE(REPLACE(CONCAT(group_period_year, group_period_term), '期', ''), '%Y%m%d') AS DATE) BETWEEN CAST('2026-08-07' AS DATE) AND CAST('2026-08-12' AS DATE)
        THEN '20260808期'
        WHEN CAST(DATE_PARSE(REPLACE(CONCAT(group_period_year, group_period_term), '期', ''), '%Y%m%d') AS DATE) BETWEEN CAST('2026-08-13' AS DATE) AND CAST('2026-08-18' AS DATE)
        THEN '20260815期'
        ELSE CONCAT(
          CAST(DATE_FORMAT(
            DATE_TRUNC(
              'WEEK',
              DATE_PARSE(REPLACE(CONCAT(group_period_year, group_period_term), '期', ''), '%Y%m%d')
            ) + INTERVAL '4' DAY,
            '%Y%m%d'
          ) AS VARCHAR),
          '期'
        )
      END AS period_name,
      virtual_third_department_name AS depart_1,
      virtual_fourth_department_name AS depart,
      virtual_leader_email_name AS jingli,
      virtual_direct_leader_email_name AS zhuguan,
      employee_email_name,
      rule_name,
      t1.lead_id,
      user_id,
      trace_type_name,
      CASE
        WHEN (
          assign_lead_count = 1 OR valid_lead_count = 1
        )
        AND third_department_name IN ('直播部', '新媒体内容运营部', '市场一组')
        THEN '当期'
        WHEN (
          assign_lead_count = 1 OR valid_lead_count = 1
        )
        AND third_department_name IN ('图书营销部')
        AND rule_name LIKE '%亚飞%'
        THEN '当期'
        WHEN third_department_name IS NULL AND valid_lead_count = 1
        THEN '当期'
        WHEN NOT third_department_name IN ('直播部', '新媒体内容运营部', '市场一组') AND valid_lead_count = 1
        THEN '当期'
        ELSE '非当期'
      END AS d_w,
      CASE
        WHEN (
          assign_lead_count = 1 OR valid_lead_count = 1
        )
        AND third_department_name IN ('直播部', '新媒体内容运营部', '市场一组')
        THEN 1
        WHEN third_department_name IS NULL AND valid_lead_count = 1
        THEN 1
        WHEN NOT third_department_name IN ('直播部', '新媒体内容运营部', '市场一组') AND valid_lead_count = 1
        THEN 1
        WHEN third_department_name IN ('图书营销部')
        AND rule_name LIKE '%亚飞%'
        AND (
          assign_lead_count = 1 OR valid_lead_count = 1
        )
        THEN 1
        ELSE 0
      END AS xiansuo,
      CASE
        WHEN CAST(DATE_PARSE(REPLACE(CONCAT(group_period_year, group_period_term), '期', ''), '%Y%m%d') AS DATE) BETWEEN CAST('2026-07-26' AS DATE) AND CAST('2026-07-31' AS DATE)
        AND third_department_name = '线上商务部'
        AND flow_pool_name = '电商退款用户池'
        AND put_plan_name = '0728期退款用户计划'
        AND channel_name_1 = '内部'
        AND channel_name_2 = '流量复用'
        AND source_manager_name = '曲默晗'
        AND sku_id_name LIKE '0728期-%帅师%'
        THEN '退款订单复用'
        WHEN CAST(DATE_PARSE(REPLACE(CONCAT(group_period_year, group_period_term), '期', ''), '%Y%m%d') AS DATE) BETWEEN CAST('2026-08-01' AS DATE) AND CAST('2026-08-06' AS DATE)
        AND third_department_name = '线上商务部'
        AND source_manager_name IN ('曲默晗', '何木玲')
        AND sku_id_name LIKE '0728期-%'
        AND (
          sku_id_name LIKE '%帅师%' OR sku_id_name LIKE '%孟帝%'
        )
        THEN '退款订单复用'
        WHEN get_customer_way_name IN ('平台自播')
        AND flow_pool_name IN ('赢战广东中考', '高途专版图书', '状元帮教辅', '高途专版视频书', '本地化专版图书', '广东专版图书')
        THEN '广东图书'
        WHEN get_customer_way_name IN ('平台自播')
        AND flow_pool_name IN (
          '途铭文化专版图书',
          '途铭文化',
          '博慧星辰文化图书',
          '启迪蔚来',
          '智慧航迹图书',
          '高途浙江初中',
          '高途浙江高中',
          '高途浙江新高一',
          '浙江专版图书教辅'
        )
        THEN '浙江图书'
        WHEN get_customer_way_name IN ('平台自播')
        AND flow_pool_name IN ('沪上名校', '沪上领航社', '简学文化', '魔都校友助学馆', '沪上领航高中', '沪上领航初中')
        THEN '上海图书'
        WHEN get_customer_way_name IN ('平台自播') AND flow_pool_name IN ('高途江苏中考', '高途赢战中考')
        THEN '江苏图书'
        WHEN flow_pool_name = '电商退款用户池' AND rule_name LIKE '%赠失%' AND rule_name LIKE '%朱博士%'
        THEN '赠课失败-朱汉祺'
        WHEN flow_pool_name = '电商退款用户池' AND rule_name LIKE '%赠失%' AND rule_name LIKE '%春春%'
        THEN '赠课失败-陈瑞春'
        WHEN flow_pool_name = '电商退款用户池' AND rule_name LIKE '%赠失%' AND rule_name LIKE '%亚飞%'
        THEN '赠课失败-孟亚飞'
        WHEN flow_pool_name = '电商退款用户池' AND rule_name LIKE '%赠失%' AND rule_name LIKE '%星义%'
        THEN '赠课失败-赵星义'
        WHEN flow_pool_name = '电商退款用户池' AND rule_name LIKE '%赠失%' AND rule_name LIKE '%郭艺%'
        THEN '赠课失败-郭艺'
        WHEN second_department_name = '本地化大班学部'
        OR source_manager_name IN ('鲍大海', '杨文卓', '喻新桥')
        THEN '本地化市场流量'
        WHEN third_department_name IN ('中价产品项目部', '新媒体内容运营部') AND rule_name LIKE '%曹忆%'
        THEN '曹忆'
        WHEN rule_name LIKE '%语数英%' AND third_department_name = '新媒体内容运营部'
        THEN '语数英'
        WHEN third_department_name = '直播部' AND sku_id_name LIKE '%山东专版%'
        THEN '北京直播山东'
        WHEN third_department_name = '直播部' AND sku_id_name LIKE '%河南专版%'
        THEN '北京直播河南'
        WHEN sku_id_name LIKE '%江苏%' AND third_department_name = '直播部'
        THEN '北京直播江苏'
        WHEN third_department_name LIKE '%锋途%' AND channel_name_2 = '抖音'
        THEN '锋途KOC'
        WHEN third_department_name = '线上商务部' AND flow_pool_name LIKE '%图书订单%'
        THEN '图书解密'
        WHEN put_plan_name LIKE '%小红书打粉%'
        THEN 'EM-小红书合作'
        WHEN third_department_name IN ('投放部', '线上商务部', '小红书攻坚组') AND channel_name_2 = '小红书'
        THEN '小红书-闯闯组'
        WHEN third_department_name IN ('新媒体内容运营部') AND channel_name_2 = '小红书'
        THEN '小红书直投-绍孜组'
        WHEN page_id_name LIKE '%0元领课%' AND third_department_name = '投放部'
        THEN '信息流0元'
        WHEN page_id_name LIKE '%周帅0元腾讯%' AND third_department_name = '投放部'
        THEN '信息流0转低'
        WHEN page_id_name LIKE '%信息流下引%' AND third_department_name = '私域运营部'
        THEN '信息流0转低'
        WHEN sku_id_name LIKE '%数理系统%'
        AND third_department_name IN ('快乐成长组', '直播部', '市场效能部', '运营部')
        THEN '物理系统'
        WHEN trace_type_name LIKE '%转介绍%'
        THEN '转介绍'
        WHEN ad_account_name IN (
          '高途-高中-DYD搜索-QZ49',
          '高途-高中-DYD搜索-XLHD49',
          '高途-高中-DYD搜索-XLHD50',
          '高途-高中-DYD搜索-QZ50'
        )
        OR ad_account_name LIKE '%DYD1元搜索%'
        THEN '搜索1元'
        WHEN (
          flow_pool_name LIKE '%江苏预习%' OR flow_pool_name LIKE '%江苏专版预习%'
        )
        AND channel_name_2 = '抖音'
        THEN '西安直播江苏-抖音'
        WHEN flow_pool_name LIKE '%自然流%'
        AND rule_name LIKE '%江苏%'
        AND third_department_name = '图书营销部'
        AND channel_name_2 = '抖音'
        THEN '西安直播江苏-抖音'
        WHEN (
          flow_pool_name LIKE '%江苏预习%' OR flow_pool_name LIKE '%江苏专版预习%'
        )
        AND channel_name_2 = '视频号'
        THEN '西安直播江苏-视频号'
        WHEN flow_pool_name LIKE '%退款%' AND third_department_name = '图书营销部'
        THEN '西安直播-退款订单复用'
        WHEN flow_pool_name LIKE '%自然流%'
        AND rule_name LIKE '%江苏%'
        AND third_department_name = '图书营销部'
        AND channel_name_2 = '视频号'
        THEN '西安直播江苏-视频号'
        WHEN sku_id_name LIKE '%2000题%' AND third_department_name = '图书营销部'
        THEN '西安直播2000题'
        WHEN sku_id_name LIKE '%五年高考%' AND third_department_name = '图书营销部'
        THEN '西安直播五年真题'
        WHEN (
          rule_name LIKE '%北京图书%' OR sku_id_name LIKE '%北京专版%'
        )
        AND third_department_name = '图书营销部'
        THEN '西安直播北京'
        WHEN sku_id_name LIKE '%安徽%' AND third_department_name = '图书营销部'
        THEN '西安直播安徽'
        WHEN put_plan_name LIKE '%全国教考%' AND third_department_name = '图书营销部'
        THEN '西安直播全国'
        WHEN flow_pool_name LIKE '%自然流%'
        AND rule_name LIKE '%北京%'
        AND third_department_name = '图书营销部'
        THEN '西安直播北京'
        WHEN sku_id_name LIKE '%2000题%' AND third_department_name = '直播部'
        THEN 'IP直播-2000题'
        WHEN flow_pool_name LIKE '%星义大大%' OR flow_pool_name LIKE '%星义物理%'
        THEN '赵星义'
        WHEN (
          source_manager_name IN ('马思雨02', '袁银') AND rule_name LIKE '%集团%'
        )
        AND NOT COALESCE(
          (
            (
              third_department_name = '私域运营部'
              AND source_manager_name IN (
                '陈雷19',
                '崔慧敏01',
                '侯佳林01',
                '郑天琪02',
                '杨彬屹',
                '曹义鹏',
                '王硕阳',
                '于超研',
                '岳一帆02',
                '田起帆',
                '王绍阳',
                '肖佳兴',
                '姚佳03',
                '秦金萍',
                '李冞萤'
              )
            )
            OR (
              flow_pool_name LIKE '%南通欣创%'
              OR flow_pool_name LIKE '%人人通科技%'
              OR flow_pool_name LIKE '%易而购%'
              OR flow_pool_name LIKE '%济南梦航%'
              OR flow_pool_name LIKE '%晨硕智学%'
              OR flow_pool_name LIKE '%兴尧文化%'
              OR flow_pool_name LIKE '%济南映像%'
              OR flow_pool_name LIKE '%山东简单%'
              OR flow_pool_name LIKE '%争鸣科技%'
            )
            OR (
              (
                flow_pool_name LIKE '%家校共育%'
                OR flow_pool_name LIKE '%保持热爱%'
                OR flow_pool_name LIKE '%青松%'
                OR flow_pool_name LIKE '%悟之道%'
              )
              AND put_plan_name NOT LIKE '%0元%'
            )
            OR (
              source_manager_name = '李宁24' AND put_plan_name LIKE '%0转低%'
            )
            OR (
              third_department_name = '私域运营部'
              AND flow_original_order_activity_price IN ('100.0', '900.0', '300.0')
            )
            OR (
              third_department_name = '私域运营部'
              AND flow_original_order_activity_price IN ('0.0')
              AND source_manager_name IN ('陈雷19', '崔慧敏01', '侯佳林01', '郑天琪02', '杨彬屹', '曹义鹏', '王硕阳', '于超研')
            )
            OR (
              flow_pool_name LIKE '公导私'
            )
            OR (
              flow_pool_name LIKE '%0转低转正%' OR channel_name_2 = '产研测试'
            )
          ),
          FALSE
        )
        THEN '集团私域'
        WHEN rule_name LIKE '%途途私域%'
        OR (
          rule_name LIKE '%私域%' AND first_department_name = 'TT'
        )
        OR rule_name LIKE '%私域1元%'
        OR (
          third_department_name = '私域招生中心' AND flow_pool_name LIKE '%APP%'
        )
        THEN '途途私域'
        WHEN third_department_name = '图书营销部'
        AND (
          sku_id_name LIKE '%孟亚飞99%' OR sku_id_name LIKE '%亚飞%'
        )
        AND channel_name_2 = '百度'
        THEN '孟亚飞-2组-百度'
        WHEN third_department_name = '图书营销部'
        AND (
          sku_id_name LIKE '%孟亚飞99%' OR sku_id_name LIKE '%亚飞%'
        )
        AND channel_name_2 = '抖音'
        THEN '孟亚飞-2组-抖音'
        WHEN third_department_name = '投放部' AND (
          ad_account_name LIKE '%周帅%'
        )
        THEN '信息流-周帅'
        WHEN source_manager_name IN ('韩正卿')
        THEN '抖音私信'
        WHEN channel_name_1 = '市场私域' AND put_plan_name LIKE '%孟亚飞汇总%'
        THEN '小红书自然流-绍孜组'
        WHEN channel_name_1 = '市场私域'
        AND (
          virtual_fourth_department_name IN ('郑州学习顾问二部', '郑州学习顾问七部', '郑州训练营')
          AND (
            rule_name LIKE '%表单%' OR trace_type_name LIKE '%引流课%'
          )
        )
        THEN '市场私域低价单'
        WHEN third_department_name = '私域运营部'
        AND source_manager_name IN (
          '陈雷19',
          '崔慧敏01',
          '侯佳林01',
          '郑天琪02',
          '杨彬屹',
          '曹义鹏',
          '王硕阳',
          '于超研',
          '岳一帆02',
          '田起帆',
          '王绍阳',
          '肖佳兴',
          '姚佳03',
          '秦金萍',
          '李冞萤'
        )
        AND (
          rule_name LIKE '%koc自孵化下引%'
          OR rule_name LIKE '%koc下引%'
          OR page_id_name LIKE '%自营%'
        )
        THEN '自孵化KOC下引'
        WHEN third_department_name = '私域运营部'
        AND source_manager_name IN (
          '陈雷19',
          '崔慧敏01',
          '侯佳林01',
          '郑天琪02',
          '杨彬屹',
          '曹义鹏',
          '王硕阳',
          '于超研',
          '岳一帆02',
          '田起帆',
          '王绍阳',
          '肖佳兴',
          '姚佳03',
          '秦金萍',
          '李冞萤'
        )
        THEN '进校私域合作'
        WHEN channel_name_1 = '市场私域'
        AND (
          virtual_fourth_department_name IN ('郑州学习顾问二部', '郑州学习顾问七部', '郑州训练营')
          OR virtual_fifth_department_name IN ('罗江博团队')
        )
        THEN '市场私域入群'
        WHEN third_department_name = '图书营销部'
        AND (
          rule_name LIKE '%点睛卷%' OR sku_id_name LIKE '%押题卷%'
        )
        THEN '押题卷'
        WHEN third_department_name = '投放部'
        AND channel_name_2 = '小红书'
        AND channel_name_1 <> '搜索营销'
        THEN '信息流-小红书'
        WHEN third_department_name = '线上商务部' AND channel_name_2 = '小红书'
        THEN '小红书'
        WHEN (
          flow_pool_name LIKE '%北大汤哥%'
          OR flow_pool_name LIKE '%海淀名师高阶%'
          OR flow_pool_name LIKE '%海淀高阶%'
          OR flow_pool_name LIKE '%高阶英语887%'
        )
        AND sku_id_name LIKE '%小艺%'
        THEN '郭艺'
        WHEN third_department_name LIKE '%私域%'
        AND rule_name LIKE '%私域%'
        AND rule_name LIKE '%图书%'
        THEN '市场私域图书'
        WHEN third_department_name LIKE '%私域%' AND rule_name LIKE '%公域自然流%'
        THEN '小红书自然流-绍孜组'
        WHEN third_department_name LIKE '%私域%' AND rule_name LIKE '%品效%'
        THEN '市场私域品效'
        WHEN third_department_name LIKE '%私域%' AND put_plan_name LIKE '%会话%'
        THEN '市场私域会话'
        WHEN third_department_name LIKE '%私域%' AND rule_name LIKE '%公域学霸%'
        THEN '市场私域公域组'
        WHEN third_department_name IN ('线上商务部')
        AND source_manager_name IN ('孙晗01', '方俊结01', '刘亦鹏02', '何木玲', '杨梓月', '张可意03', '任颖迪', '曹蕊07', '曲默晗')
        AND flow_pool_name LIKE '%退款%'
        THEN 'KOC-退款订单复用'
        WHEN third_department_name IN ('直播部', '新媒体内容运营部', '市场一组', '私域运营部')
        AND flow_pool_name = '电商退款用户池'
        THEN 'IP退款订单复用'
        WHEN third_department_name IN ('直播部', '新媒体内容运营部', '市场一组', '私域运营部')
        AND put_plan_name LIKE '%失败%'
        AND flow_pool_name = '电商退款用户池'
        THEN '赠课失败'
        WHEN third_department_name IN ('直播部', '新媒体内容运营部', '市场一组')
        AND (
          flow_pool_name = '初阶化学规划' OR flow_pool_name LIKE '%启迪-初阶老师%'
        )
        THEN '曹忆'
        WHEN (
          third_department_name = '图书营销部' AND sku_id_name LIKE '%真题%'
        )
        OR (
          third_department_name = '直播部' AND sku_id_name LIKE '%真题%'
        )
        THEN '西安图书直播间-直播'
        WHEN (
          third_department_name = '图书营销部' AND sku_id_name NOT LIKE '%真题%'
        )
        OR (
          third_department_name = '直播部' AND sku_id_name LIKE '%秒懂%'
        )
        OR (
          third_department_name = '直播部' AND sku_id_name LIKE '%图书赠送%'
        )
        THEN '西安图书直播间-挂链'
        WHEN third_department_name IN ('直播部', '新媒体内容运营部', '市场一组')
        AND (
          flow_pool_name LIKE '%海淀高阶名师%'
          OR flow_pool_name LIKE '%海淀老师高阶%'
          OR flow_pool_name LIKE '%小艺%'
          OR flow_pool_name LIKE '%老蒋文化%'
        )
        THEN '郭艺'
        WHEN third_department_name IN ('直播部', '新媒体内容运营部', '市场一组')
        AND flow_pool_name LIKE '%电商退款%'
        AND rule_name LIKE '%郭艺99%'
        THEN '郭艺'
        WHEN put_plan_name LIKE '%国培教育-0元%'
        OR put_plan_name LIKE '%易喆教育-0元%'
        OR put_plan_name LIKE '%钟情-0元%'
        OR put_plan_name LIKE '%中望达-0元%'
        OR put_plan_name LIKE '%晨硕-0元%'
        OR put_plan_name LIKE '%彩石-0元入群%'
        THEN '创新商务入群'
        WHEN third_department_name = 'KOC孵化部'
        AND flow_pool_name LIKE '%电商退款%'
        AND put_plan_name LIKE '%失败%'
        THEN '自孵化KOC-赠课失败'
        WHEN third_department_name = 'KOC孵化部'
        AND flow_pool_name LIKE '%电商退款%'
        AND put_plan_name LIKE '%退%'
        THEN '自孵化KOC-退款订单复用'
        WHEN source_manager_name = '方俊结01' AND put_plan_name LIKE '%赠课后退款%'
        THEN 'KOC-赠课后退款'
        WHEN third_department_name = '直播部'
        AND (
          sku_id_name LIKE '%春春%'
          OR sku_id_name LIKE '%瑞春%'
          OR rule_name LIKE '%春春%'
          OR rule_name LIKE '%瑞春%'
        )
        AND channel_name_2 = '百度'
        THEN '陈瑞春-百度'
        WHEN third_department_name = '直播部'
        AND (
          sku_id_name LIKE '%春春%'
          OR sku_id_name LIKE '%瑞春%'
          OR rule_name LIKE '%春春%'
          OR rule_name LIKE '%瑞春%'
        )
        AND channel_name_2 = 'B站'
        THEN '陈瑞春-B站'
        WHEN third_department_name = '直播部'
        AND (
          sku_id_name LIKE '%春春%'
          OR sku_id_name LIKE '%瑞春%'
          OR rule_name LIKE '%春春%'
          OR rule_name LIKE '%瑞春%'
        )
        AND channel_name_2 = '抖音'
        THEN '陈瑞春-抖音199'
        WHEN third_department_name IN ('直播部', '新媒体内容运营部')
        AND (
          sku_id_name LIKE '%春春%'
          OR sku_id_name LIKE '%瑞春%'
          OR rule_name LIKE '%春春%'
          OR rule_name LIKE '%瑞春%'
        )
        AND channel_name_2 = '视频号'
        THEN '陈瑞春-视频号49'
        WHEN third_department_name = '直播部'
        AND (
          sku_id_name LIKE '%朱博士99%'
          OR rule_name LIKE '%朱汉祺99%'
          OR rule_name LIKE '%朱博士%'
          OR flow_pool_name LIKE '%朱博士%'
          OR sku_id_name LIKE '%朱博士%'
        )
        AND channel_name_2 = 'B站'
        THEN '朱博士-B站'
        WHEN third_department_name = '直播部'
        AND (
          sku_id_name LIKE '%朱博士99%'
          OR rule_name LIKE '%朱汉祺99%'
          OR rule_name LIKE '%朱博士%'
          OR flow_pool_name LIKE '%朱博士%'
          OR sku_id_name LIKE '%朱博士%'
        )
        AND channel_name_2 = '百度'
        THEN '朱博士-百度'
        WHEN third_department_name = '直播部'
        AND (
          sku_id_name LIKE '%抖音99%' AND sku_id_name LIKE '%朱博士%'
        )
        AND channel_name_2 = '抖音'
        THEN '朱博士-抖音99'
        WHEN third_department_name = '直播部'
        AND (
          sku_id_name LIKE '%朱博士99%'
        )
        AND channel_name_2 = '抖音'
        THEN '朱博士-抖音99'
        WHEN third_department_name = '直播部'
        AND (
          sku_id_name LIKE '%朱博士99%'
          OR rule_name LIKE '%朱汉祺99%'
          OR rule_name LIKE '%朱博士%'
          OR flow_pool_name LIKE '%朱博士%'
          OR sku_id_name LIKE '%朱博士%'
          OR rule_name LIKE '%朱汉祺199%'
        )
        AND channel_name_2 = '抖音'
        THEN '朱博士-抖音199'
        WHEN third_department_name = '直播部'
        AND (
          sku_id_name LIKE '%朱博士99%'
          OR rule_name LIKE '%朱汉祺99%'
          OR rule_name LIKE '%朱博士%'
          OR flow_pool_name LIKE '%朱博士%'
          OR sku_id_name LIKE '%朱博士%'
          OR rule_name LIKE '%朱汉祺49%'
        )
        AND channel_name_2 = '视频号'
        THEN '朱博士-视频号49'
        WHEN (
          third_department_name = '直播部'
          AND (
            sku_id_name LIKE '%朱博士%' OR sku_id_name LIKE '%朱汉祺%'
          )
          AND rule_name LIKE '%9%'
          AND rule_name NOT LIKE '%29%'
          AND sku_id_name NOT LIKE '%急%'
          AND sku_id_name NOT LIKE '%礼盒29%'
        )
        OR (
          third_department_name = '直播部' AND sku_id_name LIKE '%朱博士9%'
        )
        THEN '朱博士9元'
        WHEN ad_account_name LIKE '%春春%' AND channel_name_1 = '信息流'
        THEN '信息流-陈瑞春'
        WHEN channel_name_1 = '信息流'
        AND channel_name_2 = 'B站'
        AND (
          page_id_name LIKE '%0元物化%'
        )
        THEN 'B站信息流-曹忆'
        WHEN channel_name_1 = '信息流'
        AND channel_name_2 = 'B站'
        AND (
          page_id_name LIKE '%赵星义%'
        )
        THEN 'B站信息流-赵星义'
        WHEN channel_name_1 = '信息流'
        AND channel_name_2 = 'B站'
        AND (
          page_id_name LIKE '%亚飞%'
          OR source_put_plan_name LIKE '%亚飞%'
          OR page_id_name LIKE '%初中-0元%'
        )
        THEN 'B站信息流-亚飞'
        WHEN (
          flow_pool_name LIKE '%朱博士%'
          OR flow_pool_name LIKE '%双博士%'
          OR flow_pool_name LIKE '%教育规划%'
        )
        AND third_department_name <> '线上商务部'
        AND period_name NOT LIKE '%多学科拓展%'
        AND rule_name NOT LIKE '%张杰%'
        AND sku_id_name NOT LIKE '%马凯鹏IP%'
        AND third_department_name = '直播部'
        THEN '朱博士29'
        WHEN put_plan_name LIKE '%朱博士说教育%'
        AND period_name NOT LIKE '%多学科拓展%'
        AND flow_pool_name NOT LIKE '%高分讲堂%'
        AND flow_pool_name NOT LIKE '%总裁%'
        AND third_department_name = '直播部'
        THEN '朱博士29'
        WHEN (
          flow_pool_name LIKE '%朱博士讲英语%'
          OR flow_pool_name LIKE '%朱博士英语%'
          OR flow_pool_name LIKE '%朱汉祺说英语%'
          OR flow_pool_name LIKE '%朱博士说英语%'
          OR flow_pool_name LIKE '%教育规划%'
          OR flow_pool_name LIKE '%双博士英语规划%'
          OR flow_pool_name LIKE '%朱博士满分英语%'
          OR flow_pool_name LIKE '%英语教父朱博士%'
          OR (
            flow_pool_name LIKE '%中考决胜天团%'
            AND lead_purchase_intention_level1_category_name = '规划系统'
          )
        )
        AND third_department_name = '直播部'
        AND period_name NOT LIKE '%多学科拓展%'
        AND sku_id_name NOT LIKE '%马凯鹏IP%'
        AND third_department_name = '直播部'
        THEN '朱博士29'
        WHEN (
          flow_pool_name LIKE '%汤哥%' OR flow_pool_name LIKE '%汤老师%'
        )
        AND period_name NOT LIKE '%多学科拓展%'
        AND third_department_name IN ('直播部', '新媒体内容运营部')
        THEN '汤老师'
        WHEN source_manager_name = '陈晓菁04'
        AND channel_provider_name NOT LIKE '%开拓%'
        AND put_plan_name NOT LIKE '%九学%'
        THEN '商务低价'
        WHEN (
          flow_pool_name LIKE '%孟帝%'
          OR flow_pool_name LIKE '%孟老师%'
          OR flow_pool_name LIKE '%中考数学冲刺%'
          OR flow_pool_name LIKE '%8升9数学%'
          OR flow_pool_name LIKE '%孟亚飞讲数学%'
          OR flow_pool_name LIKE '%中考冲刺%'
          OR flow_pool_name LIKE '%中考满分冲刺%'
          OR flow_pool_name LIKE '%押题王孟亚飞%'
          OR flow_pool_name LIKE '%中考数学大通关%'
          OR flow_pool_name LIKE '%中考数学规划%'
          OR flow_pool_name LIKE '%亚飞数学%'
          OR flow_pool_name LIKE '%孟帝数学%'
          OR flow_pool_name LIKE '%亚飞秒解思维%'
          OR flow_pool_name LIKE '%亚飞解题%'
        )
        AND period_name NOT LIKE '%多学科拓展%'
        AND channel_name_2 NOT LIKE '%KOL%'
        AND third_department_name = '直播部'
        AND channel_name_2 = '抖音'
        THEN '孟亚飞-1组-抖音'
        WHEN (
          flow_pool_name LIKE '%孟帝%'
          OR flow_pool_name LIKE '%孟老师%'
          OR flow_pool_name LIKE '%中考数学冲刺%'
          OR flow_pool_name LIKE '%8升9数学%'
          OR flow_pool_name LIKE '%孟亚飞讲数学%'
          OR flow_pool_name LIKE '%中考冲刺%'
          OR flow_pool_name LIKE '%中考满分冲刺%'
          OR flow_pool_name LIKE '%押题王孟亚飞%'
          OR flow_pool_name LIKE '%中考数学大通关%'
          OR flow_pool_name LIKE '%中考数学规划%'
          OR flow_pool_name LIKE '%亚飞数学%'
          OR flow_pool_name LIKE '%孟帝数学%'
        )
        AND period_name NOT LIKE '%多学科拓展%'
        AND channel_name_2 NOT LIKE '%KOL%'
        AND third_department_name = '直播部'
        AND channel_name_2 = '视频号'
        THEN '孟亚飞-1组-视频号'
        WHEN (
          flow_pool_name LIKE '%孟帝%'
          OR flow_pool_name LIKE '%孟老师%'
          OR flow_pool_name LIKE '%中考数学冲刺%'
          OR flow_pool_name LIKE '%8升9数学%'
          OR flow_pool_name LIKE '%孟亚飞讲数学%'
          OR flow_pool_name LIKE '%中考冲刺%'
          OR flow_pool_name LIKE '%中考满分冲刺%'
          OR flow_pool_name LIKE '%押题王孟亚飞%'
          OR flow_pool_name LIKE '%中考数学大通关%'
          OR flow_pool_name LIKE '%中考数学规划%'
          OR flow_pool_name LIKE '%亚飞数学%'
          OR flow_pool_name LIKE '%孟帝数学%'
        )
        AND period_name NOT LIKE '%多学科拓展%'
        AND channel_name_2 NOT LIKE '%KOL%'
        AND third_department_name = '直播部'
        AND channel_name_2 = 'B站'
        THEN '孟亚飞-1组-B站'
        WHEN (
          flow_pool_name LIKE '%孟帝%'
          OR flow_pool_name LIKE '%孟老师%'
          OR flow_pool_name LIKE '%中考数学冲刺%'
          OR flow_pool_name LIKE '%8升9数学%'
          OR flow_pool_name LIKE '%孟亚飞讲数学%'
          OR flow_pool_name LIKE '%中考冲刺%'
          OR flow_pool_name LIKE '%中考满分冲刺%'
          OR flow_pool_name LIKE '%押题王孟亚飞%'
          OR flow_pool_name LIKE '%中考数学大通关%'
          OR flow_pool_name LIKE '%中考数学规划%'
          OR flow_pool_name LIKE '%亚飞数学%'
          OR flow_pool_name LIKE '%孟帝数学%'
        )
        AND period_name NOT LIKE '%多学科拓展%'
        AND channel_name_2 NOT LIKE '%KOL%'
        AND third_department_name = '直播部'
        AND channel_name_2 NOT LIKE '%百度%'
        THEN '孟亚飞99-1组'
        WHEN (
          flow_pool_name LIKE '%孟帝%'
          OR flow_pool_name LIKE '%孟老师%'
          OR flow_pool_name LIKE '%中考数学冲刺%'
          OR flow_pool_name LIKE '%8升9数学%'
          OR flow_pool_name LIKE '%孟亚飞讲数学%'
          OR flow_pool_name LIKE '%中考冲刺%'
          OR flow_pool_name LIKE '%中考满分冲刺%'
          OR flow_pool_name LIKE '%押题王孟亚飞%'
          OR flow_pool_name LIKE '%中考数学大通关%'
          OR flow_pool_name LIKE '%中考数学规划%'
          OR flow_pool_name LIKE '%亚飞数学%'
        )
        AND period_name NOT LIKE '%多学科拓展%'
        AND channel_name_2 NOT LIKE '%KOL%'
        AND third_department_name = '直播部'
        AND channel_name_2 = '百度'
        THEN '孟亚飞-1组-百度'
        WHEN put_plan_name LIKE '%刘家晋讲图文%'
        OR put_plan_name LIKE '%孟帝数学%'
        AND third_department_name = '直播部'
        THEN '孟亚飞9元'
        WHEN flow_pool_name LIKE '%汐子%'
        AND period_name NOT LIKE '%多学科拓展%'
        AND sku_id_name LIKE '%亚飞%'
        AND third_department_name = '直播部'
        AND rule_name LIKE '%99%'
        THEN '孟亚飞99-1组'
        WHEN (
          flow_pool_name LIKE '%曹忆%'
          OR flow_pool_name LIKE '%dudu%'
          OR flow_pool_name LIKE '%中考决胜天团%'
          OR flow_pool_name LIKE '%具象思维%'
          OR flow_pool_name LIKE '%在逃发面馒头%'
          OR flow_pool_name LIKE '%库洛米%'
          AND lead_purchase_intention_level1_category_name <> '规划系统'
        )
        AND period_name NOT LIKE '%多学科拓展%'
        AND third_department_name IN ('直播部', '新媒体内容运营部')
        THEN '曹忆'
        WHEN (
          first_department_name = '市场部'
          AND channel_name_1 <> '站内获客'
          AND channel_name_2 <> 'APP'
        )
        AND NOT COALESCE(
          (
            (
              third_department_name = '私域运营部'
              AND source_manager_name IN (
                '陈雷19',
                '崔慧敏01',
                '侯佳林01',
                '郑天琪02',
                '杨彬屹',
                '曹义鹏',
                '王硕阳',
                '于超研',
                '岳一帆02',
                '田起帆',
                '王绍阳',
                '肖佳兴',
                '姚佳03',
                '秦金萍',
                '李冞萤'
              )
            )
            OR (
              flow_pool_name LIKE '%南通欣创%'
              OR flow_pool_name LIKE '%人人通科技%'
              OR flow_pool_name LIKE '%易而购%'
              OR flow_pool_name LIKE '%济南梦航%'
              OR flow_pool_name LIKE '%晨硕智学%'
              OR flow_pool_name LIKE '%兴尧文化%'
              OR flow_pool_name LIKE '%济南映像%'
              OR flow_pool_name LIKE '%山东简单%'
              OR flow_pool_name LIKE '%争鸣科技%'
            )
            OR (
              (
                flow_pool_name LIKE '%家校共育%'
                OR flow_pool_name LIKE '%保持热爱%'
                OR flow_pool_name LIKE '%青松%'
                OR flow_pool_name LIKE '%悟之道%'
              )
              AND put_plan_name NOT LIKE '%0元%'
            )
            OR (
              source_manager_name = '李宁24' AND put_plan_name LIKE '%0转低%'
            )
            OR (
              third_department_name = '私域运营部'
              AND flow_original_order_activity_price IN ('100.0', '900.0', '300.0')
            )
            OR (
              third_department_name = '私域运营部'
              AND flow_original_order_activity_price IN ('0.0')
              AND source_manager_name IN ('陈雷19', '崔慧敏01', '侯佳林01', '郑天琪02', '杨彬屹', '曹义鹏', '王硕阳', '于超研')
            )
            OR (
              flow_pool_name LIKE '公导私'
            )
            OR (
              flow_pool_name LIKE '%0转低转正%' OR channel_name_2 = '产研测试'
            )
          ),
          FALSE
        )
        THEN '集团私域'
        WHEN flow_pool_name LIKE '%未加好友%'
        THEN '市场私域未加好友'
        WHEN third_department_name = '私域运营部'
        AND rule_name NOT LIKE '%训练营%'
        AND NOT virtual_fifth_department_name IN ('罗江博团队')
        AND rule_name NOT LIKE '%复用%'
        AND rule_name NOT LIKE '%未加好友%'
        AND channel_name_2 <> '内部换量'
        THEN '市场私域低价单'
        WHEN third_department_name = '私域运营部'
        AND rule_name NOT LIKE '%训练营%'
        AND rule_name NOT LIKE '%复用%'
        AND rule_name NOT LIKE '%未加好友%'
        AND channel_name_2 <> '内部换量'
        AND flow_original_order_activity_price = '0.0'
        THEN '市场私域低价单'
        WHEN channel_name_2 IN ('APP', 'M站', 'PC') AND flow_pool_name NOT LIKE '%途途%'
        THEN 'APP'
        WHEN channel_name_2 IN ('小程序') AND flow_pool_name LIKE '%高途体验课%'
        THEN 'APP'
        WHEN channel_provider_name LIKE '%唐山TMK%'
        THEN '唐山TMK'
        WHEN source_manager_name IN ('高文羽')
        AND channel_provider_name NOT LIKE '%唐山TMK%'
        AND channel_provider_name NOT LIKE '%郑州%'
        THEN '人工外呼'
        WHEN source_manager_name = '冯银晨' AND channel_name_2 = '小红书'
        THEN '信息流-小红书'
        WHEN channel_name_1 = '信息流'
        AND channel_name_2 = 'B站'
        AND third_department_name NOT LIKE '%投放%'
        AND (
          rule_name LIKE '%0904期-短期班-新高二-市场私域低价单%'
          OR flow_original_order_activity_price = '100'
          OR page_id_name LIKE '%1元%'
        )
        THEN 'B站信息流-朱汉祺-1元'
        WHEN channel_name_1 = '信息流'
        AND channel_name_2 = 'B站'
        AND third_department_name NOT LIKE '%投放%'
        AND page_id_name LIKE '%汤雪%'
        THEN 'B站信息流-汤学健'
        WHEN (
          channel_name_1 = '信息流'
          AND channel_name_2 <> 'B站'
          AND third_department_name NOT LIKE '%商务%'
          AND put_plan_name NOT LIKE '%初三0元%'
          AND put_plan_name NOT LIKE '%抖音私信%'
          AND put_plan_name NOT LIKE '%高中0元%'
          AND flow_original_order_activity_price NOT LIKE '%1990%'
        )
        OR (
          channel_name_2 = 'B站' AND third_department_name LIKE '%投放%'
        )
        THEN '信息流'
        WHEN channel_name_1 = '信息流'
        AND channel_name_2 = 'B站'
        AND third_department_name NOT LIKE '%投放%'
        AND (
          page_id_name LIKE '%郭艺%'
        )
        THEN 'B站信息流-郭艺'
        WHEN channel_name_1 = '信息流'
        AND channel_name_2 = 'B站'
        AND third_department_name NOT LIKE '%投放%'
        AND (
          page_id_name LIKE '%朱博士%'
        )
        THEN 'B站信息流-朱汉祺'
        WHEN channel_name_1 = '信息流'
        AND channel_name_2 = 'B站'
        AND third_department_name NOT LIKE '%投放%'
        AND page_id_name LIKE '%肖晗%'
        THEN 'B站信息流'
        WHEN channel_name_1 = '信息流'
        AND channel_name_2 = 'B站'
        AND third_department_name NOT LIKE '%投放%'
        AND (
          page_id_name LIKE '%马凯鹏%' OR ad_account_name LIKE '%化学%'
        )
        THEN 'B站信息流-马凯鹏'
        WHEN channel_name_1 = '信息流'
        AND channel_name_2 = 'B站'
        AND third_department_name NOT LIKE '%投放%'
        AND (
          sku_id_name LIKE '%陈瑞春%' OR rule_name LIKE '%陈瑞春%'
        )
        AND (
          ad_account_name LIKE '%语文%'
          OR source_put_plan_name LIKE '%自然流%'
          OR page_id_name LIKE '%春春%'
        )
        THEN 'B站信息流-陈瑞春'
        WHEN channel_name_1 = '信息流'
        AND channel_name_2 = 'B站'
        AND third_department_name NOT LIKE '%投放%'
        AND (
          flow_original_order_activity_price LIKE '%2990%'
          OR sku_id_name LIKE '%帅师%'
          OR sku_id_name LIKE '%周帅%'
        )
        AND ad_account_name LIKE '%语文%'
        AND (
          flow_original_order_activity_price LIKE '%1980%'
          OR flow_original_order_activity_price LIKE '%2980%'
          OR flow_original_order_activity_price LIKE '%2990%'
        )
        THEN 'B站信息流-陈瑞春'
        WHEN channel_name_1 = '信息流'
        AND channel_name_2 = 'B站'
        AND third_department_name NOT LIKE '%投放%'
        AND (
          flow_original_order_activity_price LIKE '%2990%'
          OR sku_id_name LIKE '%帅师%'
          OR sku_id_name LIKE '%周帅%'
        )
        AND ad_account_name NOT LIKE '%语文%'
        THEN 'B站信息流-周帅'
        WHEN channel_name_1 = '信息流'
        AND channel_name_2 = 'B站'
        AND third_department_name NOT LIKE '%投放%'
        AND flow_order_price LIKE '%1980%'
        AND ad_account_name LIKE '%数学%'
        THEN 'B站信息流-周帅'
        WHEN channel_name_1 = '短直电商'
        AND channel_name_2 = 'B站'
        AND third_department_name LIKE '%商务%'
        AND (
          flow_pool_name LIKE '%春春%' OR sku_id_name LIKE '%陈瑞春%'
        )
        THEN 'B站信息流-陈瑞春'
        WHEN channel_name_1 = '短直电商'
        AND channel_name_2 = 'B站'
        AND third_department_name LIKE '%商务%'
        AND (
          flow_pool_name LIKE '%朱博士%'
        )
        THEN 'B站信息流-朱汉祺'
        WHEN channel_name_1 = '信息流'
        AND channel_name_2 = 'B站'
        AND third_department_name NOT LIKE '%投放%'
        AND flow_original_order_activity_price NOT LIKE '%2980%'
        AND flow_original_order_activity_price NOT LIKE '%2990%'
        AND flow_original_order_activity_price NOT LIKE '%1980%'
        THEN 'B站信息流'
        WHEN flow_pool_name = '百度搜索引擎' OR channel_name_1 = '搜索营销'
        THEN '信息流搜索'
        WHEN flow_pool_name LIKE '%小红书班课%'
        THEN '小红书投放'
        WHEN third_department_name = '投放部'
        AND get_customer_way_name = '短视频信息流'
        AND flow_original_order_activity_price LIKE '%100%'
        THEN '信息流'
        WHEN put_plan_name LIKE '%福哥私域0元%'
        THEN 'KOC-下引'
        WHEN put_plan_name LIKE '%福哥私域5元%'
        THEN 'KOC-下引5元'
        WHEN flow_pool_name = '中考加油' AND sku_id_name LIKE '%孟帝%'
        THEN 'KOC-孟亚飞数学'
        WHEN flow_pool_name = '中考加油' AND sku_id_name LIKE '%帅师%'
        THEN 'KOC-周帅数学'
        WHEN source_manager_name IN ('孙晗01', '方俊结01', '刘亦鹏02', '何木玲', '杨梓月', '张可意03', '任颖迪', '曹蕊07', '曲默晗')
        AND (
          sku_id_name LIKE '%孟帝%'
          OR sku_id_name LIKE '%dudu%'
          OR sku_id_name LIKE '%市场初二%'
          OR rule_name LIKE '%亚飞%'
          OR sku_id_name LIKE '%初二高阳%'
          OR sku_id_name LIKE '%高阳初二%'
          OR sku_id_name LIKE '%精品初二%'
          OR rule_name LIKE '%初二%'
          OR sku_id_name LIKE '%菁英初三%'
          OR (
            virtual_second_department_name = '菁英班学部'
            AND lead_purchase_intention_level2_category_name = '初级'
            AND lead_create_time >= '2026-04-15 00:00:00'
          )
        )
        THEN 'KOC-孟亚飞数学'
        WHEN source_manager_name IN ('孙晗01', '方俊结01', '刘亦鹏02', '何木玲', '杨梓月', '张可意03', '任颖迪', '曹蕊07', '曲默晗')
        AND (
          sku_id_name LIKE '%帅师%'
          OR rule_name LIKE '%周帅%'
          OR sku_id_name LIKE '%9月升高三%'
          OR sku_id_name LIKE '%新高二%'
        )
        THEN 'KOC-周帅数学'
        WHEN source_manager_name IN ('孙晗01', '方俊结01', '刘亦鹏02', '何木玲', '杨梓月', '张可意03', '任颖迪', '曹蕊07', '曲默晗')
        AND (
          sku_id_name LIKE '%肖晗%' OR rule_name LIKE '%肖晗%'
        )
        THEN 'KOC-肖晗'
        WHEN source_manager_name IN ('孙晗01', '方俊结01', '刘亦鹏02', '何木玲', '杨梓月', '张可意03', '任颖迪', '曹蕊07', '曲默晗')
        AND period_name NOT LIKE '%多学科拓展%'
        AND sku_id_name NOT LIKE '%朱汉祺%'
        AND sku_id_name NOT LIKE '%朱博士%'
        AND sku_id_name NOT LIKE '%周帅%'
        AND sku_id_name NOT LIKE '%29元%'
        THEN 'KOC-5元纯课'
        WHEN source_manager_name IN ('孙晗01', '方俊结01', '刘亦鹏02', '何木玲', '杨梓月', '张可意03', '任颖迪', '曹蕊07', '曲默晗')
        AND sku_id_name LIKE '%周帅%'
        THEN 'KOC-周帅'
        WHEN third_department_name IN ('品牌效能部', 'KOC孵化部')
        AND channel_name_2 IN ('抖音', '视频号', '快手', 'KOL')
        THEN '自孵化KOC-5元纯课'
        WHEN third_department_name IN ('品牌效能部', 'KOC孵化部')
        AND channel_name_2 IN ('抖音', '视频号', '快手', 'KOL')
        AND (
          sku_id_name LIKE '%5元%'
          OR sku_id_name LIKE '%11元%'
          OR flow_original_order_activity_price LIKE '%1100%'
          OR flow_original_order_activity_price LIKE '%500%'
          OR flow_orders_income_amount LIKE '%1100%'
          OR flow_orders_income_amount LIKE '%500%'
        )
        THEN '自孵化KOC-5元纯课'
        WHEN source_manager_name IN (
          '包青青',
          '蔡瑞涵',
          '李文迁',
          '李佳馨44',
          '孙昊17',
          '王洁雅01',
          '王硕北',
          '朱文',
          '贾铭锐',
          '李壮壮04',
          '陈晓菁04',
          '赵艺雅'
        )
        AND channel_name_2 LIKE '%社群%'
        THEN '进校社群'
        WHEN source_manager_name IN (
          '包青青',
          '蔡瑞涵',
          '李文迁',
          '李佳馨44',
          '孙昊17',
          '王洁雅01',
          '王硕北',
          '朱文',
          '贾铭锐',
          '李壮壮04',
          '陈晓菁04',
          '赵艺雅'
        )
        AND (
          channel_name_2 LIKE '%直推%'
          OR (
            put_plan_name LIKE '%良师益友%' OR put_plan_name LIKE '%弘诚1元%'
          )
        )
        THEN '进校直推'
        WHEN source_manager_name IN (
          '包青青',
          '蔡瑞涵',
          '李文迁',
          '李佳馨44',
          '孙昊17',
          '王洁雅01',
          '王硕北',
          '朱文',
          '贾铭锐',
          '李壮壮04',
          '陈晓菁04',
          '赵艺雅'
        )
        AND channel_name_2 LIKE '%TMK%'
        AND (
          page_id_name LIKE '%1元%' OR channel_provider_name LIKE '%禾顺云%'
        )
        THEN '进校TMK1元'
        WHEN source_manager_name IN (
          '包青青',
          '蔡瑞涵',
          '李文迁',
          '李佳馨44',
          '孙昊17',
          '王洁雅01',
          '王硕北',
          '朱文',
          '贾铭锐',
          '李壮壮04',
          '陈晓菁04',
          '赵艺雅'
        )
        AND channel_name_2 LIKE '%TMK%'
        AND page_id_name LIKE '%9元%'
        THEN '进校TMK9元'
        WHEN source_manager_name IN (
          '包青青',
          '蔡瑞涵',
          '李文迁',
          '李佳馨44',
          '孙昊17',
          '王洁雅01',
          '王硕北',
          '朱文',
          '贾铭锐',
          '李壮壮04',
          '陈晓菁04',
          '赵艺雅'
        )
        AND channel_name_2 LIKE '%书商%'
        THEN '进校书商'
        WHEN source_manager_name IN (
          '包青青',
          '蔡瑞涵',
          '李文迁',
          '李佳馨44',
          '孙昊17',
          '王洁雅01',
          '王硕北',
          '朱文',
          '贾铭锐',
          '李壮壮04',
          '陈晓菁04',
          '赵艺雅'
        )
        AND channel_name_2 LIKE '%综合%'
        AND put_plan_name LIKE '%18%'
        THEN '进校直播'
        WHEN source_manager_name IN (
          '包青青',
          '蔡瑞涵',
          '李文迁',
          '李佳馨44',
          '孙昊17',
          '王洁雅01',
          '王硕北',
          '朱文',
          '贾铭锐',
          '李壮壮04',
          '陈晓菁04',
          '赵艺雅'
        )
        AND channel_name_2 LIKE '%直播%'
        THEN '进校直播'
        WHEN source_manager_name IN (
          '包青青',
          '蔡瑞涵',
          '李文迁',
          '李佳馨44',
          '孙昊17',
          '王洁雅01',
          '王硕北',
          '朱文',
          '贾铭锐',
          '李壮壮04',
          '赵艺雅'
        )
        AND put_plan_name NOT LIKE '%0元%'
        AND flow_pool_name NOT LIKE '%家校共育%'
        AND flow_pool_name NOT LIKE '%保持热爱%'
        AND flow_pool_name NOT LIKE '%青松%'
        AND flow_pool_name NOT LIKE '%原子初三%'
        AND flow_pool_name NOT LIKE '%南通欣创%'
        AND flow_pool_name NOT LIKE '%悟之道%'
        AND flow_pool_name NOT LIKE '%济南梦航%'
        AND channel_name_3 <> '社群'
        AND put_plan_name NOT LIKE '%善悟%'
        AND put_plan_name NOT LIKE '%人人通%'
        AND put_plan_name NOT LIKE '%%济南格乐'
        AND flow_pool_name NOT LIKE '%晨硕智学%'
        AND flow_pool_name NOT LIKE '%兴尧文化%'
        AND flow_pool_name NOT LIKE '%济南映像%'
        AND flow_pool_name NOT LIKE '%山东简单%'
        AND flow_pool_name NOT LIKE '%争鸣科技%'
        THEN '商务低价'
        WHEN flow_pool_name LIKE '%南通欣创%'
        OR flow_pool_name LIKE '%人人通科技%'
        OR flow_pool_name LIKE '%易而购%'
        OR flow_pool_name LIKE '%济南梦航%'
        OR flow_pool_name LIKE '%晨硕智学%'
        OR flow_pool_name LIKE '%兴尧文化%'
        OR flow_pool_name LIKE '%济南映像%'
        OR flow_pool_name LIKE '%山东简单%'
        OR flow_pool_name LIKE '%争鸣科技%'
        THEN '进校私域合作'
        WHEN (
          flow_pool_name LIKE '%家校共育%'
          OR flow_pool_name LIKE '%保持热爱%'
          OR flow_pool_name LIKE '%青松%'
          OR flow_pool_name LIKE '%悟之道%'
        )
        AND put_plan_name NOT LIKE '%0元%'
        THEN '进校私域合作'
        WHEN source_manager_name = '李宁24' AND put_plan_name LIKE '%0转低%'
        THEN '进校私域合作'
        WHEN third_department_name = '私域运营部'
        AND flow_original_order_activity_price IN ('100.0', '900.0', '300.0')
        THEN '进校私域合作'
        WHEN third_department_name = '私域运营部'
        AND flow_original_order_activity_price IN ('0.0')
        AND source_manager_name IN ('陈雷19', '崔慧敏01', '侯佳林01', '郑天琪02', '杨彬屹', '曹义鹏', '王硕阳', '于超研')
        THEN '进校私域合作'
        WHEN third_department_name = '私域运营部'
        AND channel_name_1 = '市场私域'
        AND put_plan_name NOT LIKE '%公导私%'
        AND put_plan_name NOT LIKE '%公转私%'
        AND flow_original_order_activity_price = '0.0'
        AND rule_name NOT LIKE '%激活%'
        AND rule_name NOT LIKE '%咨询%'
        AND rule_name NOT LIKE '%训练营%'
        AND virtual_fifth_department_name NOT LIKE '%罗江博%'
        AND virtual_fifth_department_name NOT LIKE '%郑州学习顾问二部%'
        AND NOT source_manager_name IN ('陈雷19', '崔慧敏01', '侯佳林01', '郑天琪02', '杨彬屹', '曹义鹏', '王硕阳', '于超研')
        THEN '市场私域低价单'
        WHEN source_manager_name IN ('耿文超', '晋翠翠', '赵语诗', '王慧敏13', '于新茹', '梁超01', '刘晓20', '王玉120', '吕佳乐01')
        AND channel_provider_name LIKE '%格乐教育%'
        AND channel_name_2 LIKE '%直播%'
        THEN '创新社群'
        WHEN source_manager_name IN ('耿文超', '晋翠翠', '赵语诗', '王慧敏13', '于新茹', '梁超01', '刘晓20', '王玉120', '吕佳乐01')
        AND channel_name_2 LIKE '%社群%'
        THEN '创新社群'
        WHEN source_manager_name IN ('耿文超', '晋翠翠', '赵语诗', '王慧敏13', '于新茹', '梁超01', '刘晓20', '王玉120', '吕佳乐01')
        AND (
          channel_name_2 LIKE '%直推%' OR put_plan_name LIKE '%直推%'
        )
        THEN '创新直推'
        WHEN source_manager_name IN ('耿文超', '晋翠翠', '赵语诗', '王慧敏13', '于新茹', '梁超01', '刘晓20', '王玉120', '吕佳乐01')
        AND (
          channel_name_2 LIKE '%书商%'
          OR put_plan_name LIKE '%书商%'
          OR page_id_name LIKE '%书商%'
        )
        THEN '创新书商'
        WHEN source_manager_name IN ('耿文超', '晋翠翠', '赵语诗', '王慧敏13', '于新茹', '梁超01', '刘晓20', '王玉120', '吕佳乐01')
        AND channel_name_2 LIKE '%TMK%'
        AND page_id_name LIKE '%1元%'
        THEN '创新TMK1元'
        WHEN source_manager_name IN ('耿文超', '晋翠翠', '赵语诗', '王慧敏13', '于新茹', '梁超01', '刘晓20', '王玉120', '吕佳乐01')
        AND channel_name_2 LIKE '%TMK%'
        AND page_id_name LIKE '%9元%'
        THEN '创新TMK9元'
        WHEN source_manager_name IN ('耿文超', '晋翠翠', '赵语诗', '王慧敏13', '于新茹', '梁超01', '刘晓20', '王玉120', '吕佳乐01')
        AND (
          channel_name_2 LIKE '%直播%' OR page_id_name LIKE '%进校%'
        )
        THEN '创新直播'
        WHEN source_manager_name IN ('耿文超', '晋翠翠', '赵语诗', '王慧敏13', '于新茹', '梁超01', '刘晓20', '王玉120', '吕佳乐01')
        AND channel_name_2 <> '公众号'
        AND channel_name_1 = '商务'
        AND flow_pool_name <> '高途云集图书专营店-自然流'
        AND flow_pool_name <> '高途旗舰店—线索—yuxinru'
        AND put_plan_name NOT LIKE '%社群%'
        AND put_plan_name NOT LIKE '%小红书班课%'
        AND put_plan_name NOT LIKE '%外部图书供量%'
        AND channel_second_provider_name NOT LIKE '%沃德丰店铺线索赠课%'
        AND channel_second_provider_name NOT LIKE '%智慧城-图书%'
        AND put_plan_name NOT LIKE '%育甲%'
        AND flow_pool_name NOT LIKE '%周长磊%'
        THEN '创新商务'
        WHEN source_manager_name IN ('高曼曼01', '杨思怡', '宋向函')
        THEN '图书KOC达人'
        WHEN flow_pool_name LIKE '%市场部-微信私域%'
        OR flow_pool_name LIKE '%市场部-规划报告%'
        OR flow_pool_name LIKE '%规划报告%'
        OR flow_pool_name LIKE '%市场部-小红书%'
        OR flow_pool_name LIKE '%孟浩宇%'
        THEN '市场私域低价单'
        WHEN flow_pool_name LIKE '公导私'
        THEN '进校私域合作'
        WHEN (
          (
            flow_pool_name LIKE '%增长组%'
            OR channel_name_3 = '公众号'
            OR second_department_name = '微信生态部'
          )
          AND channel_name_2 <> 'APP'
        )
        AND NOT COALESCE(
          (
            (
              third_department_name = '私域运营部'
              AND source_manager_name IN (
                '陈雷19',
                '崔慧敏01',
                '侯佳林01',
                '郑天琪02',
                '杨彬屹',
                '曹义鹏',
                '王硕阳',
                '于超研',
                '岳一帆02',
                '田起帆',
                '王绍阳',
                '肖佳兴',
                '姚佳03',
                '秦金萍',
                '李冞萤'
              )
            )
            OR (
              flow_pool_name LIKE '%南通欣创%'
              OR flow_pool_name LIKE '%人人通科技%'
              OR flow_pool_name LIKE '%易而购%'
              OR flow_pool_name LIKE '%济南梦航%'
              OR flow_pool_name LIKE '%晨硕智学%'
              OR flow_pool_name LIKE '%兴尧文化%'
              OR flow_pool_name LIKE '%济南映像%'
              OR flow_pool_name LIKE '%山东简单%'
              OR flow_pool_name LIKE '%争鸣科技%'
            )
            OR (
              (
                flow_pool_name LIKE '%家校共育%'
                OR flow_pool_name LIKE '%保持热爱%'
                OR flow_pool_name LIKE '%青松%'
                OR flow_pool_name LIKE '%悟之道%'
              )
              AND put_plan_name NOT LIKE '%0元%'
            )
            OR (
              source_manager_name = '李宁24' AND put_plan_name LIKE '%0转低%'
            )
            OR (
              third_department_name = '私域运营部'
              AND flow_original_order_activity_price IN ('100.0', '900.0', '300.0')
            )
            OR (
              third_department_name = '私域运营部'
              AND flow_original_order_activity_price IN ('0.0')
              AND source_manager_name IN ('陈雷19', '崔慧敏01', '侯佳林01', '郑天琪02', '杨彬屹', '曹义鹏', '王硕阳', '于超研')
            )
            OR (
              flow_pool_name LIKE '公导私'
            )
            OR (
              flow_pool_name LIKE '%0转低转正%' OR channel_name_2 = '产研测试'
            )
          ),
          FALSE
        )
        THEN '集团私域'
        WHEN put_plan_name LIKE '%星耀%'
        OR put_plan_name LIKE '%物理展博%'
        OR put_plan_name LIKE '%物理谢丽荣%'
        OR put_plan_name LIKE '%牟恩伯%'
        OR put_plan_name LIKE '%王赞%'
        OR put_plan_name LIKE '%张磊老师高中数学%'
        OR put_plan_name LIKE '%雯姐高中物理大讲堂%'
        THEN '百度星耀'
        WHEN source_manager_name = '刘福云'
        AND (
          sku_id_name LIKE '%瑞春%' OR sku_id_name LIKE '%春春%'
        )
        THEN '陈瑞春'
        WHEN third_department_name = '直播部'
        AND sku_id_name LIKE '%周帅%'
        AND channel_name_2 IN ('百度', 'B站')
        THEN '周帅'
        WHEN third_department_name = '直播部'
        AND sku_id_name LIKE '%孟亚飞%'
        AND rule_name LIKE '%99%'
        THEN '孟亚飞99-1组'
        WHEN third_department_name = '直播部' AND sku_id_name LIKE '%朱汉祺%'
        THEN '朱博士99'
        WHEN flow_pool_name LIKE '%0转低转正%' OR channel_name_2 = '产研测试'
        THEN '进校私域合作'
        WHEN flow_pool_name LIKE '%天津智慧双子%'
        THEN '创新社群'
        WHEN third_department_name LIKE '%城市定制%'
        THEN '点睛卷'
        WHEN period_name LIKE '%多学科拓展%' AND third_department_name LIKE '%私域运营%'
        THEN '市场私域入群'
        WHEN put_plan_name LIKE '%赠课失败%' AND third_department_name = '线上商务部'
        THEN 'KOC赠课失败'
        WHEN flow_pool_name LIKE '%自然流%'
        AND source_manager_name IN ('孙晗01', '方俊结01', '刘亦鹏02', '何木玲', '杨梓月', '张可意03', '任颖迪', '曹蕊07', '曲默晗')
        AND sku_id_name LIKE '%周帅%'
        THEN 'KOC-周帅'
        WHEN flow_pool_name LIKE '%自然流%'
        AND source_manager_name IN ('孙晗01', '方俊结01', '刘亦鹏02', '何木玲', '杨梓月', '张可意03', '任颖迪', '曹蕊07', '曲默晗')
        AND sku_id_name LIKE '%肖晗%'
        THEN 'KOC-肖晗'
        WHEN flow_pool_name LIKE '%自然流%'
        AND source_manager_name IN ('孙晗01', '方俊结01', '刘亦鹏02', '何木玲', '杨梓月', '张可意03', '任颖迪', '曹蕊07', '曲默晗')
        AND sku_id_name LIKE '%朱汉祺%'
        AND flow_original_order_activity_price LIKE '%1100%'
        THEN 'KOC-5元朱汉祺'
        WHEN flow_pool_name LIKE '%自然流%' AND source_manager_name IN ('赵语诗', '崔文轩', '孙培尧')
        THEN '自孵化KOC-5元纯课'
        WHEN flow_pool_name LIKE '%自然流%'
        AND (
          sku_id_name LIKE '%朱博士%' OR sku_id_name LIKE '%朱汉祺%'
        )
        AND rule_name LIKE '%9%'
        AND rule_name NOT LIKE '%29%'
        AND third_department_name IN ('直播部', '新媒体内容运营部', '市场一组')
        THEN '朱博士99'
        WHEN flow_pool_name LIKE '%自然流%'
        AND sku_id_name LIKE '%朱博士%'
        AND third_department_name IN ('直播部', '新媒体内容运营部', '市场一组')
        THEN '朱博士99'
        WHEN flow_pool_name LIKE '%自然流%'
        AND sku_id_name LIKE '%亚飞%'
        AND rule_name LIKE '%99%'
        AND third_department_name IN ('直播部', '新媒体内容运营部', '市场一组')
        THEN '孟亚飞99-1组'
        WHEN flow_pool_name LIKE '%自然流%'
        AND sku_id_name LIKE '%亚飞%'
        AND third_department_name IN ('直播部', '新媒体内容运营部', '市场一组')
        THEN '孟亚飞9元'
        WHEN flow_pool_name LIKE '%自然流%' AND sku_id_name LIKE '%曹忆%'
        THEN '曹忆'
        WHEN flow_pool_name LIKE '%自然流%'
        AND rule_name LIKE '%朱博士%'
        AND third_department_name IN ('直播部', '新媒体内容运营部', '市场一组')
        THEN '朱博士99'
        WHEN flow_pool_name LIKE '%自然流%'
        AND source_manager_name LIKE '%邵万昕%'
        AND third_department_name IN ('直播部', '新媒体内容运营部', '市场一组')
        THEN '朱博士99'
        WHEN flow_pool_name LIKE '%自然流%' AND rule_name LIKE '%亚飞%' AND rule_name LIKE '%99%'
        THEN '孟亚飞99-1组'
        WHEN flow_pool_name LIKE '%自然流%' AND rule_name LIKE '%亚飞%'
        THEN '孟亚飞9元'
        WHEN flow_pool_name LIKE '%自然流%' AND rule_name LIKE '%郭艺%'
        THEN '郭艺'
        WHEN flow_pool_name LIKE '%自然流%' AND rule_name LIKE '%汤雪%'
        THEN '汤老师'
        WHEN flow_pool_name LIKE '%自然流%' AND rule_name LIKE '%曹忆%'
        THEN '曹忆'
        WHEN flow_pool_name LIKE '%途途教室%' OR first_department_name LIKE 'TUTU'
        THEN '途途APP'
        WHEN source_manager_name IN ('宋莹莹', '辛世如') AND channel_name_2 IN ('视频号')
        THEN '信息流-虚拟号挂车'
        WHEN rule_name LIKE '%训练营%' AND rule_name LIKE '%市场私域%'
        THEN '市场私域入群'
        WHEN channel_name_1 = '信息流'
        AND (
          put_plan_name LIKE '%抖音私信%'
          OR put_plan_name LIKE '%初三0元%'
          OR put_plan_name LIKE '%高中0元%'
        )
        THEN '信息流-抖音私信'
        WHEN rule_name LIKE '%途途私域%'
        OR (
          rule_name LIKE '%私域%' AND first_department_name = 'TT'
        )
        THEN '途途私域'
        ELSE '其他未知流量'
      END AS channel_map,
      CASE
        WHEN rule_name LIKE '%高一%'
        THEN '高一'
        WHEN rule_name LIKE '%高二%'
        THEN '高二'
        WHEN rule_name LIKE '%高三%'
        THEN '高三'
        WHEN rule_name LIKE '%初二%'
        THEN '初二'
        WHEN rule_name LIKE '%初三%'
        THEN '初三'
        WHEN rule_name LIKE '%初一%'
        THEN '初一'
        ELSE lead_purchase_intention_level2_category_name
      END AS grade_1,
      COALESCE(lead_count, 0) AS lead_count,
      COALESCE(valid_lead_count, 0) AS valid_lead_count,
      COALESCE(merge_assign_lead_count, 0) AS merge_assign_lead_count,
      COALESCE(merge_valid_lead_count, 0) AS merge_valid_lead_count,
      COALESCE(conversion_lead_count, 0) AS conversion_lead_count,
      COALESCE(subject_count, 0) AS subject_count,
      COALESCE(same_lead_period_subject_count, 0) AS same_lead_period_subject_count,
      COALESCE(lb_subject_count, 0) AS lb_subject_count,
      COALESCE(same_lead_period_lb_subject_count, 0) AS same_lead_period_lb_subject_count,
      COALESCE(order_count, 0) AS order_count,
      COALESCE(income_amount, 0) AS income_amount,
      COALESCE(in_pay_period_refund_amount, 0) AS in_pay_period_refund_amount,
      COALESCE(non_pay_period_refund_amount, 0) AS non_pay_period_refund_amount,
      COALESCE(jp_cross_department_refund_amount, 0) AS jp_cross_department_refund_amount,
      COALESCE(lead_period_income_amount, 0) AS lead_period_income_amount,
      COALESCE(lead_period_refund_amount, 0) AS lead_period_refund_amount,
      COALESCE(same_lead_period_order_count, 0) AS same_lead_period_order_count,
      COALESCE(same_lead_period_conversion_lead_count, 0) AS same_lead_period_conversion_lead_count,
      COALESCE(same_lead_period_income_amount, 0) AS same_lead_period_income_amount,
      COALESCE(same_lead_period_refund_amount, 0) AS same_lead_period_refund_amount
    FROM bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df AS t1
    WHERE
      dt = FORMAT_DATETIME(CURRENT_TIMESTAMP - INTERVAL '2' HOUR, 'YYYYMMdd')
      AND hour = FORMAT_DATETIME(CURRENT_TIMESTAMP - INTERVAL '3' HOUR, 'HH')
      AND section_assign_employee_first_level_department_name = 'H业务线'
      AND section_assign_employee_second_level_department_name = '市场部'
      AND section_assign_employee_third_level_department_name = '市场顾问部'
      AND period_mapping_first_level_department_name = 'H业务线'
      AND period_mapping_second_level_department_name IN ('精品班学部', '市场部', '菁英班学部', '本地化大班学部', '一对一学部')
  ), m2253_zhuanhua AS (
    SELECT
      period_name,
      channel_map,
      rule_name,
      grade_1,
      depart_1,
      depart,
      jingli,
      zhuguan,
      employee_email_name,
      SUM(valid_lead_count) AS can_renew_ds_count_a
    FROM m2253_data
    GROUP BY
      period_name,
      channel_map,
      rule_name,
      grade_1,
      depart_1,
      depart,
      jingli,
      zhuguan,
      employee_email_name
  ), m2253_zx_active AS (
    SELECT
      employee_email_name,
      xiaozu,
      jingli,
      department
    FROM (
      SELECT
        zx.*,
        ROW_NUMBER() OVER (
          PARTITION BY zx.employee_email_name
          ORDER BY CASE
            WHEN zx.department = '郑州顾问部'
            THEN 1
            WHEN zx.department = '西安一部'
            THEN 2
            WHEN zx.department = '西安二部'
            THEN 3
            ELSE 9
          END, zx.employee_email_prefix, zx.xiaozu, zx.jingli
        ) AS rn
      FROM temp_table.dingxi01_jiagou_zx AS zx
      WHERE
        CAST(zx.zaizhi AS VARCHAR) = '1' AND zx.department IN ('郑州顾问部', '西安一部', '西安二部')
    ) AS t
    WHERE
      rn = 1
  ), m2253_jiagou_period AS (
    SELECT
      qici,
      department,
      employee_email_name,
      xiaozu,
      jingli
    FROM (
      SELECT
        NULLIF(TRIM(CAST(jg.qici AS VARCHAR)), '') AS qici,
        NULLIF(TRIM(CAST(jg.department AS VARCHAR)), '') AS department,
        NULLIF(TRIM(CAST(jg.employee_email_name AS VARCHAR)), '') AS employee_email_name,
        NULLIF(TRIM(CAST(jg.xiaozu AS VARCHAR)), '') AS xiaozu,
        NULLIF(TRIM(CAST(jg.jingli AS VARCHAR)), '') AS jingli,
        ROW_NUMBER() OVER (
          PARTITION BY NULLIF(TRIM(CAST(jg.qici AS VARCHAR)), ''), NULLIF(TRIM(CAST(jg.department AS VARCHAR)), ''), NULLIF(TRIM(CAST(jg.employee_email_name AS VARCHAR)), '')
          ORDER BY CASE WHEN NOT NULLIF(TRIM(CAST(jg.xiaozu AS VARCHAR)), '') IS NULL THEN 0 ELSE 1 END, NULLIF(TRIM(CAST(jg.xiaozu AS VARCHAR)), ''), NULLIF(TRIM(CAST(jg.jingli AS VARCHAR)), '')
        ) AS rn
      FROM temp_table.dingxi01_jiagou_db AS jg
    ) AS t
    WHERE
      rn = 1
  )
  SELECT
    zz.period_name,
    zz.channel_map,
    zz.grade_1,
    COALESCE(
      jg.jingli,
      NULLIF(TRIM(CAST(zx.jingli AS VARCHAR)), ''),
      NULLIF(TRIM(CAST(zz.jingli AS VARCHAR)), ''),
      '未知经理'
    ) AS jingli,
    zz.employee_email_name,
    zz.can_renew_ds_count_a,
    COALESCE(
      jg.xiaozu,
      NULLIF(TRIM(CAST(zx.xiaozu AS VARCHAR)), ''),
      NULLIF(TRIM(CAST(zz.zhuguan AS VARCHAR)), ''),
      '未知主管'
    ) AS xiaozu
  FROM m2253_zhuanhua AS zz
  LEFT JOIN m2253_jiagou_period AS jg
    ON jg.qici = zz.period_name
    AND jg.department = zz.depart
    AND zz.employee_email_name = jg.employee_email_name
  LEFT JOIN m2253_zx_active AS zx
    ON zx.employee_email_name = zz.employee_email_name
  WHERE
    zz.period_name > '20260424期'
) AS m
GROUP BY
  m.period_name,
  m.channel_map,
  m.jingli,
  m.xiaozu,
  m.grade_1,
  m.employee_email_name
)
SELECT
  qici,
  channel_1,
  jingli,
  xiaozu,
  grade_list,
  name,
  gmv_7,
  gmv_14,
  gmv_30,
  gmv_n30,
  gmv_7_h,
  gmv_total,
  refund_7,
  refund_14,
  refund_30,
  refund_n30,
  refund_7_p,
  refund_total,
  can_renew_ds_count_a
FROM (
  SELECT
    COALESCE(ma.qici, ba.qici) AS qici,
    COALESCE(ma.channel_1, ba.channel_1) AS channel_1,
    COALESCE(ma.jingli, ba.jingli) AS jingli,
    COALESCE(ma.xiaozu, ba.xiaozu) AS xiaozu,
    COALESCE(ma.grade_list, ba.grade_list) AS grade_list,
    COALESCE(ma.name, ba.name) AS name,
    COALESCE(ba.gmv_7, 0) AS gmv_7,
    COALESCE(ba.gmv_14, 0) AS gmv_14,
    COALESCE(ba.gmv_30, 0) AS gmv_30,
    COALESCE(ba.gmv_n30, 0) AS gmv_n30,
    COALESCE(ba.gmv_7_h, 0) AS gmv_7_h,
    COALESCE(ba.gmv_finance_total, 0) AS gmv_total,
    COALESCE(ba.refund_7, 0) AS refund_7,
    COALESCE(ba.refund_14, 0) AS refund_14,
    COALESCE(ba.refund_30, 0) AS refund_30,
    COALESCE(ba.refund_n30, 0) AS refund_n30,
    COALESCE(ba.refund_7_p, 0) AS refund_7_p,
    COALESCE(ba.refund_total, 0) AS refund_total,
    COALESCE(ma.can_renew_ds_count_a, 0) AS can_renew_ds_count_a
  FROM metric_agg AS ma
  FULL OUTER JOIN bucket_agg AS ba
    ON ma.qici = ba.qici
    AND ma.channel_1 = ba.channel_1
    AND COALESCE(ma.jingli, '') = COALESCE(ba.jingli, '')
    AND COALESCE(ma.xiaozu, '') = COALESCE(ba.xiaozu, '')
    AND COALESCE(ma.grade_list, '') = COALESCE(ba.grade_list, '')
    AND COALESCE(ma.name, '') = COALESCE(ba.name, '')
) AS final_aligned
