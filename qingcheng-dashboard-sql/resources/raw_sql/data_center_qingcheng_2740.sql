WITH biz_qici_calendar AS (
  SELECT
    *
  FROM (VALUES
    ('20260605期', '0605期', CAST('2026-06-02' AS DATE), CAST('2026-06-08' AS DATE), 0),
    ('20260612期', '0612期', CAST('2026-06-09' AS DATE), CAST('2026-06-15' AS DATE), 1),
    ('20260619期', '0619期', CAST('2026-06-16' AS DATE), CAST('2026-06-22' AS DATE), 2),
    ('20260626期', '0626期', CAST('2026-06-23' AS DATE), CAST('2026-06-29' AS DATE), 3),
    ('20260703期', '0703期', CAST('2026-06-30' AS DATE), CAST('2026-07-06' AS DATE), 4),
    ('20260710期', '0710期', CAST('2026-07-07' AS DATE), CAST('2026-07-13' AS DATE), 5),
    ('20260716期', '0716期', CAST('2026-07-14' AS DATE), CAST('2026-07-19' AS DATE), 6),
    ('20260722期', '0722期', CAST('2026-07-20' AS DATE), CAST('2026-07-25' AS DATE), 7),
    ('20260728期', '0728期', CAST('2026-07-26' AS DATE), CAST('2026-07-31' AS DATE), 8),
    ('20260803期', '0803期', CAST('2026-08-01' AS DATE), CAST('2026-08-06' AS DATE), 9),
    ('20260808期', '0808期', CAST('2026-08-07' AS DATE), CAST('2026-08-11' AS DATE), 10),
    ('20260815期', '0815期', CAST('2026-08-12' AS DATE), CAST('2026-08-18' AS DATE), 11),
    ('20260821期', '0821期', CAST('2026-08-19' AS DATE), CAST('2026-08-24' AS DATE), 12),
    ('20260828期', '0828期', CAST('2026-08-25' AS DATE), CAST('2026-08-31' AS DATE), 13),
    ('20260904期', '0904期', CAST('2026-09-01' AS DATE), CAST('2026-09-06' AS DATE), 14)) AS c(qici, short_qici, period_start_date, period_end_date, period_index)
), period_aliases AS (
  SELECT
    *
  FROM (VALUES
    ('20260605期', '20260605期', 0),
    ('20260612期', '20260612期', 1),
    ('20260618期', '20260619期', 2),
    ('20260619期', '20260619期', 2),
    ('20260625期', '20260626期', 3),
    ('20260626期', '20260626期', 3),
    ('20260702期', '20260703期', 4),
    ('20260703期', '20260703期', 4),
    ('20260710期', '20260710期', 5),
    ('20260716期', '20260716期', 6),
    ('20260722期', '20260722期', 7),
    ('20260728期', '20260728期', 8),
    ('20260803期', '20260803期', 9),
    ('20260808期', '20260808期', 10),
    ('20260815期', '20260815期', 11),
    ('20260821期', '20260821期', 12),
    ('20260828期', '20260828期', 13),
    ('20260903期', '20260904期', 14),
    ('20260904期', '20260904期', 14),
    ('20260717期', '20260716期', 6),
    ('20260724期', '20260722期', 7),
    ('20260731期', '20260728期', 8),
    ('20260807期', '20260803期', 9)) AS a(alias_qici, canonical_qici, period_index)
), douyin_refund_prelead_raw AS (
  SELECT
    CAST(f.lead_id AS BIGINT) AS prelead_id,
    f.rule_name AS prelead_rule_name,
    f.employee_email_name,
    f.virtual_direct_leader_email_name,
    COALESCE(
      f.stats_grade_name,
      f.lead_purchase_intention_level2_category_name,
      CASE
        WHEN f.rule_name LIKE '%高一%'
        THEN '高一'
        WHEN f.rule_name LIKE '%高二%'
        THEN '高二'
        WHEN f.rule_name LIKE '%高三%'
        THEN '高三'
        WHEN f.rule_name LIKE '%高中预科%'
        THEN '高中预科'
      END
    ) AS grade_1,
    COALESCE(
      lead_cal.canonical_qici,
      CONCAT(CAST(f.group_period_year AS VARCHAR), f.group_period_term)
    ) AS qici,
    COALESCE(TRY_CAST(f.valid_lead_count AS BIGINT), 0) AS valid_lead_count,
    ROW_NUMBER() OVER (
      PARTITION BY CAST(f.lead_id AS BIGINT)
      ORDER BY COALESCE(TRY_CAST(f.valid_lead_count AS BIGINT), 0) DESC, CASE WHEN NOT f.rule_name IS NULL THEN 0 ELSE 1 END, CASE WHEN NOT f.employee_email_name IS NULL THEN 0 ELSE 1 END, f.section_assign_time DESC, f.employee_email_prefix
    ) AS prelead_rn
  FROM bdg_ba.app_crm_prelead_cost_gmv_full_link_data_hf AS f
  LEFT JOIN period_aliases AS lead_cal
    ON CONCAT(CAST(f.group_period_year AS VARCHAR), f.group_period_term) = lead_cal.alias_qici
  WHERE
    f.dt = FORMAT_DATETIME(CURRENT_TIMESTAMP - INTERVAL '2' HOUR, 'YYYYMMdd')
    AND f.hour = FORMAT_DATETIME(CURRENT_TIMESTAMP - INTERVAL '2' HOUR, 'HH')
    AND f.lead_model_type = 1
    AND f.section_assign_employee_first_level_department_name = 'H业务线'
    AND f.virtual_third_department_name = '学习顾问部'
    AND f.virtual_fourth_department_name = 'SEC创新部'
    AND f.rule_name LIKE '%抖音正价退费%'
), douyin_refund_prelead AS (
  SELECT
    p.prelead_id,
    p.prelead_rule_name,
    p.employee_email_name,
    p.virtual_direct_leader_email_name,
    p.grade_1,
    p.qici
  FROM douyin_refund_prelead_raw AS p
  JOIN (
    SELECT DISTINCT
      qici,
      employee_email_name
    FROM temp_table.dingxi01_jiagou_db
    WHERE
      dept_2 = 'SEC' AND NOT qici IS NULL AND NOT employee_email_name IS NULL
  ) AS jg
    ON p.qici = jg.qici AND p.employee_email_name = jg.employee_email_name
  WHERE
    p.prelead_rn = 1 AND valid_lead_count > 0 AND NOT p.employee_email_name IS NULL
), douyin_refund_transfer AS (
  SELECT DISTINCT
    p.prelead_id,
    CAST(l.crm_leads_id AS BIGINT) AS transfer_lead_id,
    p.prelead_rule_name,
    p.qici AS prelead_qici
  FROM douyin_refund_prelead AS p
  JOIN data_lake_fuwu.dwd_crm_leads_rt AS l
    ON CAST(l.previous_model_id AS BIGINT) = p.prelead_id
  WHERE
    l.model_type = 0 AND l.previous_model_id > 0
), lead_map AS (
  SELECT
    lead_id,
    put_plan_name,
    employee_email_name,
    channel_name_1,
    channel_name_2,
    channel_name_3,
    flow_pool_name,
    get_customer_way_name,
    rule_name,
    CASE
      WHEN LOWER(REPLACE(COALESCE(rule_name, ''), ' ', '')) LIKE '%青橙本地化-河南私域-%'
      THEN '本地化'
      WHEN LOWER(REPLACE(COALESCE(rule_name, ''), ' ', '')) LIKE '%青橙本地化-河南app-%'
      THEN '本地化'
      WHEN rule_name LIKE '%青橙私域-表单浙江-%' OR rule_name = '表单浙江'
      THEN '私域'
      WHEN rule_name LIKE '%青橙私域-表单江苏-%' OR rule_name = '表单江苏'
      THEN '私域'
      WHEN rule_name LIKE '%私域裂变%'
      THEN '私域'
      WHEN rule_name LIKE '%公域自然流%'
      THEN '公域'
      WHEN rule_name LIKE '%公域-自然流%'
      THEN '公域'
      WHEN rule_name LIKE '%内部图书%'
      THEN '图书'
      WHEN rule_name LIKE '%SEC内部未加好友%'
      THEN '订单复用'
      WHEN (
        REPLACE(COALESCE(rule_name, ''), ' ', '') LIKE '%青橙IP-招生退费-春春%'
        OR REPLACE(COALESCE(rule_name, ''), ' ', '') LIKE '%青橙IP-招生退费-朱博士%'
        OR REPLACE(COALESCE(rule_name, ''), ' ', '') LIKE '%青橙IP-招生退费-郭艺%'
      )
      THEN 'IP退费'
      WHEN rule_name LIKE '%抖音正价退费%'
      THEN '抖音复用'
      WHEN (
        rule_name LIKE '%赠失-星义%'
        OR rule_name LIKE '%赠失-朱博士%'
        OR rule_name LIKE '%赠失-春春%'
        OR rule_name LIKE '%赠失-郭艺%'
        OR rule_name LIKE '%赠失-亚飞%'
        OR rule_name LIKE '%青橙IP%'
      )
      THEN CONCAT('IP', CHR(  36192), CHR(  35838), CHR(  22833), CHR(  36133))
      WHEN (
        rule_name LIKE '%私域本地化%' OR rule_name LIKE '%河南本地化%' OR rule_name LIKE '%青橙本地化%'
      )
      THEN '本地化'
      WHEN (
        rule_name LIKE '%私域会话%'
        OR rule_name LIKE '%私域表单%'
        OR rule_name LIKE '%私域品效%'
        OR rule_name LIKE '%私域图书%'
      )
      THEN '私域'
      WHEN (
        rule_name LIKE '%公域学霸%' OR rule_name LIKE '%青橙公域%'
      )
      THEN '公域'
      WHEN (
        rule_name LIKE '%武汉图书%' OR rule_name LIKE '%西安图书%'
      )
      THEN '图书'
      WHEN rule_name LIKE '%亚飞IP%'
      THEN '主讲IP'
      WHEN (
        rule_name LIKE '%SEC未加好友%'
        OR rule_name LIKE '%SEC首期掉海%'
        OR rule_name LIKE '%SEC招生退费%'
        OR rule_name LIKE '%招生退费%'
      )
      THEN '订单复用'
      WHEN (
        rule_name LIKE '%顾问未加好友%' OR rule_name LIKE '%公海%'
      )
      THEN '公海'
      WHEN rule_name LIKE '%抖音私信%'
      THEN '抖音私信'
      WHEN (
        rule_name LIKE '%进校9元%' OR rule_name LIKE '%进校%'
      )
      THEN '进校9元'
      ELSE COALESCE(NULLIF(TRIM(channel_name_1), ''), '未知')
    END AS channel_map_1,
    CASE
      WHEN LOWER(REPLACE(COALESCE(rule_name, ''), ' ', '')) LIKE '%青橙本地化-河南私域-%'
      THEN '河南私域'
      WHEN LOWER(REPLACE(COALESCE(rule_name, ''), ' ', '')) LIKE '%青橙本地化-河南app-%'
      THEN '河南APP'
      WHEN rule_name LIKE '%青橙私域-表单浙江-%' OR rule_name = '表单浙江'
      THEN '表单浙江'
      WHEN rule_name LIKE '%青橙私域-表单江苏-%' OR rule_name = '表单江苏'
      THEN '表单江苏'
      WHEN rule_name LIKE '%私域裂变%'
      THEN '私域裂变'
      WHEN rule_name LIKE '%公域自然流%'
      THEN '公域自然流'
      WHEN rule_name LIKE '%公域-自然流%'
      THEN '公域自然流'
      WHEN rule_name LIKE '%内部图书%'
      THEN '内部图书'
      WHEN rule_name LIKE '%SEC内部未加好友%'
      THEN 'SEC内部未加好友'
      WHEN REPLACE(COALESCE(rule_name, ''), ' ', '') LIKE '%青橙IP-招生退费-春春%'
      THEN '春春'
      WHEN REPLACE(COALESCE(rule_name, ''), ' ', '') LIKE '%青橙IP-招生退费-朱博士%'
      THEN '朱博士'
      WHEN REPLACE(COALESCE(rule_name, ''), ' ', '') LIKE '%青橙IP-招生退费-郭艺%'
      THEN '郭艺'
      WHEN rule_name LIKE '%抖音正价退费%'
      THEN '抖音正价退费'
      WHEN rule_name LIKE '%赠失-星义%'
      THEN '星义IP'
      WHEN rule_name LIKE '%赠失-朱博士%'
      THEN '朱博士IP'
      WHEN rule_name LIKE '%赠失-春春%'
      THEN '春春IP'
      WHEN rule_name LIKE '%赠失-郭艺%'
      THEN '郭艺IP'
      WHEN rule_name LIKE '%赠失-亚飞%'
      THEN '亚飞IP'
      WHEN rule_name LIKE '%青橙IP%'
      THEN '亚飞IP'
      WHEN rule_name LIKE '%私域会话%'
      THEN '私域会话'
      WHEN rule_name LIKE '%私域表单%'
      THEN '私域表单'
      WHEN rule_name LIKE '%私域图书%'
      THEN '私域图书'
      WHEN rule_name LIKE '%私域品效%'
      THEN '私域品效'
      WHEN rule_name LIKE '%私域本地化%'
      THEN '河南私域'
      WHEN (
        rule_name LIKE '%河南本地化%' OR rule_name LIKE '%青橙本地化%'
      )
      THEN '河南APP'
      WHEN rule_name LIKE '%亚飞IP%'
      THEN '亚飞IP'
      WHEN rule_name LIKE '%SEC未加好友%'
      THEN 'SEC未加好友'
      WHEN rule_name LIKE '%SEC首期掉海%'
      THEN 'SEC首期掉海'
      WHEN (
        rule_name LIKE '%SEC招生退费%' OR rule_name LIKE '%招生退费%'
      )
      THEN 'SEC招生退费'
      WHEN (
        rule_name LIKE '%顾问未加好友%' OR rule_name LIKE '%公海%'
      )
      THEN '顾问未加好友'
      WHEN rule_name LIKE '%武汉图书%'
      THEN '武汉图书'
      WHEN rule_name LIKE '%西安图书%'
      THEN '西安图书'
      WHEN (
        rule_name LIKE '%公域学霸%' OR rule_name LIKE '%青橙公域%'
      )
      THEN '公域学霸'
      WHEN rule_name LIKE '%抖音私信%'
      THEN '抖音私信'
      WHEN (
        rule_name LIKE '%进校9元%' OR rule_name LIKE '%进校%'
      )
      THEN '进校9元'
      ELSE COALESCE(
        NULLIF(TRIM(channel_name_3), ''),
        NULLIF(TRIM(channel_name_2), ''),
        NULLIF(TRIM(channel_name_1), ''),
        '未知'
      )
    END AS rule_name0,
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
      ELSE lead_purchase_intention_level2_category_name
    END AS grade_0,
    virtual_direct_leader_email_name,
    full_link_period_year,
    full_link_period_term,
    full_link_valid_lead_count,
    prelead_qici
  FROM (
    SELECT
      f.lead_id,
      f.put_plan_name,
      f.employee_email_name,
      f.channel_name_1,
      f.channel_name_2,
      f.channel_name_3,
      f.flow_pool_name,
      f.get_customer_way_name,
      COALESCE(t.prelead_rule_name, f.rule_name) AS rule_name,
      f.lead_purchase_intention_level2_category_name,
      f.virtual_direct_leader_email_name,
      f.section_assign_time,
      ROW_NUMBER() OVER (
        PARTITION BY f.lead_id, f.employee_email_name
        ORDER BY f.section_assign_time DESC, REGEXP_EXTRACT(COALESCE(t.prelead_rule_name, f.rule_name), '(\d{4}期)', 1) DESC, f.group_period_year DESC, f.group_period_term DESC
      ) AS rn,
      f.group_period_year AS full_link_period_year,
      f.group_period_term AS full_link_period_term,
      f.valid_lead_count AS full_link_valid_lead_count,
      t.prelead_qici AS prelead_qici
    FROM bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df AS f
    LEFT JOIN douyin_refund_transfer AS t
      ON CAST(f.lead_id AS BIGINT) = t.transfer_lead_id
    WHERE
      (
        f.dt = FORMAT_DATETIME(CURRENT_TIMESTAMP - INTERVAL '2' HOUR, 'YYYYMMdd')
        AND f.hour = FORMAT_DATETIME(CURRENT_TIMESTAMP - INTERVAL '2' HOUR, 'HH')
        AND f.section_assign_employee_first_level_department_name = 'H业务线'
        AND f.section_assign_employee_second_level_department_name = '青橙项目部'
        AND f.period_mapping_first_level_department_name = 'H业务线'
      )
      AND f.period_mapping_second_level_department_name IN ('精品班学部', '菁英班学部', '市场部', '青橙项目部')
  ) AS lm
  WHERE
    lm.rn = 1
), dd AS (
  SELECT
    base.lead_id,
    base.original_order_user_number,
    base.order_number,
    base.performance_employee_email_name,
    base.mapping_school_subject_name,
    base.trade_timestamp,
    base.trade_group_period_name,
    base.pay_group_period_name,
    base.clazz_name,
    base.income_amount,
    base.refund_amount,
    base.promit_amount,
    base.filled_course_first_level_department_name,
    base.filled_course_second_level_department_name,
    base.service_transfer_in_amount_yuan,
    base.service_transfer_out_amount_yuan,
    base.channel_map_1,
    base.rule_name0,
    base.rule_name,
    base.grade_0,
    base.qici,
    base.virtual_direct_leader_email_name,
    base.source_lead_period_name,
    base.trade_period_index,
    base.full_link_period_year,
    base.full_link_period_term,
    base.full_link_valid_lead_count,
    base.prelead_qici
  FROM (
    SELECT
      gmv.lead_id,
      gmv.original_order_user_number,
      gmv.order_number,
      gmv.performance_employee_email_name,
      gmv.mapping_school_subject_name,
      gmv.trade_timestamp,
      gmv.trade_group_period_name,
      gmv.pay_group_period_name,
      gmv.clazz_name,
      COALESCE(gmv.income_amount / 100, 0) AS income_amount,
      COALESCE(gmv.refund_amount / 100, 0) AS refund_amount,
      COALESCE(gmv.income_amount / 100, 0) - COALESCE(gmv.refund_amount / 100, 0) AS promit_amount,
      CAST(COALESCE(gmv.transfer_in_amount, 0) AS DOUBLE) / 100.0 AS service_transfer_in_amount_yuan,
      CAST(COALESCE(gmv.transfer_out_amount, 0) AS DOUBLE) / 100.0 AS service_transfer_out_amount_yuan,
      CASE
        WHEN NOT gmv.course_first_level_department_name IS NULL
        THEN gmv.course_first_level_department_name
        WHEN gmv.grade_name LIKE '%小学%' OR gmv.grade_name LIKE '%初%'
        THEN '小初业务线'
        ELSE 'H业务线'
      END AS filled_course_first_level_department_name,
      CASE
        WHEN NOT gmv.course_second_level_department_name IS NULL
        THEN gmv.course_second_level_department_name
        WHEN gmv.course_first_level_department_name = 'H业务线'
        THEN '精品班学部'
        WHEN gmv.course_first_level_department_name IS NULL
        AND NOT (
          gmv.grade_name LIKE '%小学%' OR gmv.grade_name LIKE '%初%'
        )
        THEN '精品班学部'
        ELSE gmv.course_second_level_department_name
      END AS filled_course_second_level_department_name,
      ld.channel_map_1,
      ld.rule_name0,
      ld.rule_name,
      ld.grade_0,
      ld.virtual_direct_leader_email_name,
      COALESCE(
        trade_cal.qici,
        CONCAT(
          DATE_FORMAT(
            CASE
              WHEN CAST(gmv.trade_timestamp AS DATE) < CAST('2026-09-07' AS DATE)
              THEN DATE_TRUNC('WEEK', CAST(gmv.trade_timestamp AS TIMESTAMP) - INTERVAL '1' DAY) + INTERVAL '4' DAY
              ELSE DATE_TRUNC('WEEK', CAST(gmv.trade_timestamp AS TIMESTAMP)) + INTERVAL '4' DAY
            END,
            '%Y%m%d'
          ),
          '期'
        )
      ) AS qici,
      gmv.lead_period_name AS source_lead_period_name,
      COALESCE(
        trade_cal.period_index,
        CASE
          WHEN CAST(gmv.trade_timestamp AS DATE) >= CAST('2026-09-07' AS DATE)
          THEN 15 + CAST(FLOOR(
            DATE_DIFF(
              'DAY',
              CAST('2026-09-07' AS DATE),
              CAST(DATE_TRUNC('WEEK', CAST(gmv.trade_timestamp AS TIMESTAMP)) AS DATE)
            ) / 7.0
          ) AS BIGINT)
          ELSE CAST(FLOOR(
            DATE_DIFF(
              'DAY',
              CAST('2026-06-02' AS DATE),
              CAST(DATE_TRUNC('WEEK', CAST(gmv.trade_timestamp AS TIMESTAMP) - INTERVAL '1' DAY) AS DATE) + INTERVAL '1' DAY
            ) / 7.0
          ) AS BIGINT)
        END
      ) AS trade_period_index,
      ld.full_link_period_year,
      ld.full_link_period_term,
      ld.full_link_valid_lead_count,
      ld.prelead_qici
    FROM service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf AS gmv
    LEFT JOIN biz_qici_calendar AS trade_cal
      ON CAST(gmv.trade_timestamp AS DATE) BETWEEN trade_cal.period_start_date AND trade_cal.period_end_date
    LEFT JOIN lead_map AS ld
      ON gmv.lead_id = ld.lead_id
      AND ld.employee_email_name = gmv.performance_employee_email_name
    WHERE
      (
        gmv.dt = FORMAT_DATETIME(CURRENT_TIMESTAMP - INTERVAL '2' HOUR, 'YYYYMMdd')
        AND gmv.hour = FORMAT_DATETIME(CURRENT_TIMESTAMP - INTERVAL '2' HOUR, 'HH')
        AND gmv.performance_second_level_department_name = '青橙项目部'
        AND gmv.course_first_level_department_name IN ('H业务线', 'LL业务线', 'TUTU', 'TT', 'A业务线', 'EM业务线', 'KA业务线', 'TT业务线', '创新中心')
        AND gmv.course_second_level_department_name IN (
          'V项目部',
          '本地化部',
          '私域营销组',
          '青少成长学部',
          '创新技术组',
          '成长中心供应链组',
          'APP运营组',
          '英语产品部',
          '职场服务部',
          '用户平台部',
          '微师产品部',
          '上海中心综合部',
          'CAL技术组',
          '财务核算部',
          '财经项目部',
          '人才发展部',
          '财务信息化部',
          '图书项目部（关闭）',
          '运营部',
          '基础架构组',
          '数学产品部',
          '营销产品部',
          '雅思学部',
          '商品部',
          '磨课组',
          '升学规划部',
          '升学规划中心',
          '郑州中心',
          '组织部',
          '留学申请学部',
          '质检部',
          '架构平台部',
          '师训组',
          '投放商务组',
          '系统班部',
          '编程素养学部',
          '市场运营组',
          '项目运营组',
          'KM技术组',
          '二讲老师部',
          '成都中心综合部',
          '业务设计部',
          '专题课部',
          '微师职教产品部',
          '高校学部',
          '教学服务部',
          '平台产品部',
          '数字化学部',
          '品牌运营组',
          '校长办公室',
          '运营中心财务',
          '视效部',
          '数据与商业分析中心',
          'X项目',
          '教学产品部',
          'XA学部',
          '语言学部',
          '图书产品部',
          '主播部',
          '业务支持部',
          'HL技术组',
          '武汉中心综合部',
          '成人供应链组',
          '途途课堂',
          '信息平台部',
          'HL经营分析组',
          '大数据部',
          '直播运营组',
          '市场部',
          '金刚产品部',
          '教学产品运营中心',
          '平台电商组',
          '企业效能部',
          '品牌与内容部',
          '产品研发部',
          '小学部',
          '技术质量部',
          '财务报告部',
          '税务部',
          '用户产品部',
          '直播二部',
          '招聘部',
          'HR共享中心',
          '清北',
          '增长策略部',
          '督察部',
          '商品运营部',
          '资金管理部',
          '美好家庭学部',
          '设计支持中心',
          '初中部',
          'AIGC创新部',
          '财务部',
          '人力资源部',
          '人才保障部一部',
          'CAL经营分析组',
          '基础技术部',
          '综合素养学部',
          '热线呼入部',
          '品牌部',
          '语文产品部',
          '供应链部',
          '题库',
          'GZ学部',
          '政府关系部',
          'HRBP部',
          '招生运营部',
          '督检组',
          '耀师项目部',
          '产品运营部',
          '营运部',
          '多媒体技术部',
          '跟谁学郑州中心(失效）',
          '人工智能部',
          '体验设计部',
          '狮王项目部',
          '资产服务部',
          '专升本项目部',
          '基础技术部(失效)',
          '郑州中心综合部',
          '考研学部',
          '线上考研学部',
          '内容营销组',
          '公关部',
          '公职学部',
          '客服部',
          '运营平台部',
          'CS学部',
          '财务FP&A部',
          '商学院学部',
          '行政部',
          '直播三部',
          '营销技术部',
          '私域运营组',
          '飞花产品部',
          '星火产品部',
          '客户端技术部',
          '薪酬绩效部',
          '图书项目部',
          'NJ学部',
          '直播一部',
          '法务部',
          '在线服务部',
          '履约部',
          'KML经营分析组',
          '社会保障部',
          '精品班部',
          '教学教研部',
          '医疗项目部',
          '菁英班部',
          '菁英班学部',
          '精品班学部',
          '一对一学部',
          '北京学部',
          '图书学部',
          '河南学部',
          '清北班学部',
          '湖广学部',
          '山西学部',
          'K学部',
          'M学部',
          '大学生学习学部',
          '合肥学校',
          '太原学校',
          '苏州学校',
          '郑州学校',
          '北京学校',
          '上海学校',
          '运营中心',
          '广州学校',
          '市场中心',
          '南京学校',
          '深圳学校',
          '成都学校',
          '财务中心',
          '武汉学校',
          '济南学校',
          '天津学校',
          '学校办公室',
          '重庆学校',
          '西安学校',
          '长沙学校',
          '市场二部',
          '留学学部',
          '国际考试学部',
          '出国语培线下项目',
          '广州学校（IE）',
          '国际竞赛项目',
          '剑桥英语项目',
          '上海学校（IE）',
          '心理学部',
          '创新项目部',
          '创新学部',
          '素质成长学部',
          '国际考试在线学部',
          '毛豆学部',
          '青少学部',
          '市场三部',
          '市场四部',
          '青橙项目部',
          '文旅学部',
          '本地化大班学部',
          '市场营销部',
          '直播市场部',
          '创新增长部',
          '学习规划中心',
          '素养初中学部',
          '素养青藤学部',
          '素养小学学部',
          '用户运营部',
          '经营策略部',
          '校园招聘',
          '直播创新部',
          '战略创新部',
          '产研部',
          '业务研发部',
          '教学质量部',
          'Theta项目部',
          'AI素养学部',
          '文旅项目',
          'Theta智学项目部',
          'Theta产研部',
          'V学部',
          'TT初中学部',
          'TT小学学部',
          '产研部',
          'T学部',
          '专题课部（失效）',
          '初中组',
          '文旅项目（失效）'
        )
        AND (
          gmv.income_amount <> 0 OR gmv.refund_amount <> 0
        )
      )
      AND gmv.trade_timestamp >= CAST('2026-06-01 00:00:00' AS TIMESTAMP)
  ) AS base
  WHERE
    CAST(base.trade_timestamp AS TIMESTAMP) >= CAST('2026-06-01 00:00:00' AS TIMESTAMP)
), course_transfer_order_rows AS (
  SELECT
    latest_child_order_number AS order_number,
    parent_order_number,
    original_order_number,
    CAST(COALESCE(transfer_in_amount, 0) AS DOUBLE) / 100.0 AS transfer_in_amount_yuan,
    CAST(COALESCE(transfer_out_amount, 0) AS DOUBLE) / 100.0 AS transfer_out_amount_yuan
  FROM finance_dw.dim_finance_order_change_df
  WHERE
    dt = FORMAT_DATETIME(CURRENT_TIMESTAMP - INTERVAL '24' HOUR, 'YYYYMMdd')
    AND latest_child_order_status IN (2, 6, 7)
    AND biz_type IN (2, 7)
    AND order_change_type = 1
    AND NOT latest_child_order_number IS NULL
), course_transfer_order AS (
  SELECT
    order_number,
    MAX(parent_order_number) AS parent_order_number,
    MAX(original_order_number) AS original_order_number,
    MAX(transfer_in_amount_yuan) AS transfer_in_amount_yuan,
    MAX(transfer_out_amount_yuan) AS transfer_out_amount_yuan
  FROM course_transfer_order_rows
  GROUP BY
    order_number
), course_transfer_finance_detail AS (
  SELECT
    f.order_number,
    f.user_id AS target_user_number,
    f.employee_email_name,
    CAST(f.trade_time AS TIMESTAMP) AS trade_time,
    f.clazz_name,
    f.course_grade,
    CASE
      WHEN f.course_subject LIKE '%英语%' OR f.course_subject LIKE '%英文%'
      THEN '英语'
      WHEN f.course_subject LIKE '%语文%'
      THEN '语文'
      WHEN f.course_subject LIKE '%数学%'
      THEN '数学'
      WHEN f.course_subject LIKE '%物理%'
      THEN '物理'
      WHEN f.course_subject LIKE '%化学%'
      THEN '化学'
      WHEN f.course_subject LIKE '%历史%'
      THEN '历史'
      WHEN f.course_subject LIKE '%政治%'
      THEN '政治'
      WHEN f.course_subject LIKE '%生物%'
      THEN '生物'
      WHEN f.course_subject LIKE '%地理%'
      THEN '地理'
      WHEN f.course_subject LIKE '%日语%'
      THEN '日语'
      ELSE f.course_subject
    END AS mapping_school_subject_name,
    f.course_first_level_department_name,
    f.course_second_level_department_name,
    CAST(COALESCE(f.price, 0) AS DOUBLE) AS income_amount,
    o.transfer_in_amount_yuan,
    o.transfer_out_amount_yuan
  FROM finance_dw.app_finance_performance_extend_details_hf AS f
  INNER JOIN course_transfer_order AS o
    ON f.order_number = o.order_number
  WHERE
    f.dt = FORMAT_DATETIME(CURRENT_TIMESTAMP - INTERVAL '2' HOUR, 'YYYYMMdd')
    AND f.hour = FORMAT_DATETIME(CURRENT_TIMESTAMP - INTERVAL '2' HOUR, 'HH')
    AND f.employee_first_level_department_name = 'H业务线'
    AND f.employee_second_level_department_name = '青橙项目部'
    AND f.course_first_level_department_name IN ('H业务线', 'LL业务线', 'TUTU', 'TT', 'A业务线', 'EM业务线', 'KA业务线', 'TT业务线', '创新中心')
    AND f.course_second_level_department_name IN ('精品班学部', '菁英班学部', '一对一学部', '图书学部', '本地化大班学部')
    AND CAST(f.trade_time AS DATE) >= CAST('2026-07-20' AS DATE)
    AND f.trade_type = '调课调班'
    AND f.trade_status LIKE '%支付%'
    AND f.price > 0
), course_transfer_finance AS (
  SELECT
    order_number,
    target_user_number,
    employee_email_name,
    MIN(trade_time) AS trade_time,
    MAX(clazz_name) AS clazz_name,
    MAX(course_grade) AS course_grade,
    mapping_school_subject_name,
    MAX(course_first_level_department_name) AS course_first_level_department_name,
    MAX(course_second_level_department_name) AS course_second_level_department_name,
    SUM(income_amount) AS income_amount,
    MAX(transfer_in_amount_yuan) AS transfer_in_amount_yuan,
    MAX(transfer_out_amount_yuan) AS transfer_out_amount_yuan
  FROM course_transfer_finance_detail
  GROUP BY
    order_number,
    target_user_number,
    employee_email_name,
    mapping_school_subject_name
), course_transfer_protected_finance AS (
  SELECT
    f.*,
    p.lead_id,
    CAST(p.assign_time AS TIMESTAMP) AS section_assign_time,
    ROW_NUMBER() OVER (
      PARTITION BY f.order_number, f.mapping_school_subject_name
      ORDER BY CAST(p.assign_time AS TIMESTAMP) DESC, p.private_sea_update_time DESC, p.private_sea_id DESC
    ) AS protection_rank
  FROM course_transfer_finance AS f
  INNER JOIN service_dw.dwd_crm_assign_private_detail_hf AS p
    ON CAST(p.user_number AS VARCHAR) = CAST(f.target_user_number AS VARCHAR)
    AND p.employee_email_name = f.employee_email_name
  WHERE
    p.dt = FORMAT_DATETIME(CURRENT_TIMESTAMP - INTERVAL '2' HOUR, 'YYYYMMdd')
    AND p.hour = FORMAT_DATETIME(CURRENT_TIMESTAMP - INTERVAL '2' HOUR, 'HH')
    AND p.model_type = 0
    AND p.is_del = 0
    AND p.assign_employee_first_level_department_name = 'H业务线'
    AND p.assign_employee_second_level_department_name = '青橙项目部'
    AND CAST(p.assign_time AS TIMESTAMP) <= f.trade_time
    AND (
      TRY_CAST(p.close_time AS TIMESTAMP) IS NULL
      OR TRY_CAST(p.close_time AS TIMESTAMP) = CAST('1970-01-01 08:00:00' AS TIMESTAMP)
      OR TRY_CAST(p.close_time AS TIMESTAMP) > f.trade_time
    )
    AND COALESCE(TRY_CAST(p.fall_sea_time AS TIMESTAMP), CAST('9999-12-31 23:59:59' AS TIMESTAMP)) > f.trade_time
), course_transfer_base AS (
  SELECT
    f.lead_id,
    f.target_user_number AS original_order_user_number,
    f.order_number,
    f.employee_email_name AS performance_employee_email_name,
    f.mapping_school_subject_name,
    f.trade_time AS trade_timestamp,
    CAST(NULL AS VARCHAR) AS trade_group_period_name,
    CAST(NULL AS VARCHAR) AS pay_group_period_name,
    f.clazz_name,
    f.income_amount,
    CAST(0 AS DOUBLE) AS refund_amount,
    f.income_amount AS promit_amount,
    CASE
      WHEN NOT f.course_first_level_department_name IS NULL
      THEN f.course_first_level_department_name
      WHEN f.course_grade LIKE '%小学%' OR f.course_grade LIKE '%初%'
      THEN '小初业务线'
      ELSE 'H业务线'
    END AS filled_course_first_level_department_name,
    CASE
      WHEN NOT f.course_second_level_department_name IS NULL
      THEN f.course_second_level_department_name
      WHEN f.course_first_level_department_name = 'H业务线'
      THEN '精品班学部'
      WHEN f.course_first_level_department_name IS NULL
      AND NOT (
        f.course_grade LIKE '%小学%' OR f.course_grade LIKE '%初%'
      )
      THEN '精品班学部'
      ELSE f.course_second_level_department_name
    END AS filled_course_second_level_department_name,
    f.transfer_in_amount_yuan AS service_transfer_in_amount_yuan,
    f.transfer_out_amount_yuan AS service_transfer_out_amount_yuan,
    ld.channel_map_1,
    ld.rule_name0,
    ld.rule_name,
    ld.grade_0,
    ld.virtual_direct_leader_email_name,
    f.section_assign_time AS protected_section_assign_time,
    COALESCE(
      trade_cal.qici,
      CONCAT(
        DATE_FORMAT(
          CASE
            WHEN CAST(f.trade_time AS DATE) < CAST('2026-09-07' AS DATE)
            THEN DATE_TRUNC('WEEK', CAST(f.trade_time AS TIMESTAMP) - INTERVAL '1' DAY) + INTERVAL '4' DAY
            ELSE DATE_TRUNC('WEEK', CAST(f.trade_time AS TIMESTAMP)) + INTERVAL '4' DAY
          END,
          '%Y%m%d'
        ),
        '期'
      )
    ) AS qici,
    ld.full_link_period_year,
    ld.full_link_period_term,
    ld.full_link_valid_lead_count,
    ld.prelead_qici,
    CAST(NULL AS VARCHAR) AS source_lead_period_name,
    COALESCE(
      trade_cal.period_index,
      CASE
        WHEN CAST(f.trade_time AS DATE) >= CAST('2026-09-07' AS DATE)
        THEN 15 + CAST(FLOOR(
          DATE_DIFF('DAY', CAST('2026-09-07' AS DATE), CAST(DATE_TRUNC('WEEK', f.trade_time) AS DATE)) / 7.0
        ) AS BIGINT)
        ELSE CAST(FLOOR(
          DATE_DIFF(
            'DAY',
            CAST('2026-06-02' AS DATE),
            CAST(DATE_TRUNC('WEEK', f.trade_time - INTERVAL '1' DAY) AS DATE) + INTERVAL '1' DAY
          ) / 7.0
        ) AS BIGINT)
      END
    ) AS trade_period_index
  FROM course_transfer_protected_finance AS f
  INNER JOIN lead_map AS ld
    ON f.lead_id = ld.lead_id AND f.employee_email_name = ld.employee_email_name
  LEFT JOIN biz_qici_calendar AS trade_cal
    ON CAST(f.trade_time AS DATE) BETWEEN trade_cal.period_start_date AND trade_cal.period_end_date
  WHERE
    f.protection_rank = 1
), course_transfer_dd AS (
  SELECT
    base.lead_id,
    base.original_order_user_number,
    base.order_number,
    base.performance_employee_email_name,
    base.mapping_school_subject_name,
    base.trade_timestamp,
    base.trade_group_period_name,
    base.pay_group_period_name,
    base.clazz_name,
    base.income_amount,
    base.refund_amount,
    base.promit_amount,
    base.filled_course_first_level_department_name,
    base.filled_course_second_level_department_name,
    base.service_transfer_in_amount_yuan,
    base.service_transfer_out_amount_yuan,
    base.channel_map_1,
    base.rule_name0,
    base.rule_name,
    base.grade_0,
    base.qici,
    base.virtual_direct_leader_email_name,
    base.protected_section_assign_time,
    base.full_link_period_year,
    base.full_link_period_term,
    base.full_link_valid_lead_count,
    base.prelead_qici,
    base.source_lead_period_name,
    base.trade_period_index
  FROM course_transfer_base AS base
  WHERE
    CAST(base.trade_timestamp AS TIMESTAMP) >= CAST('2026-06-01 00:00:00' AS TIMESTAMP)
), service_gmv /* 成单周期 + 调课调班剔除 + 退4/点睛2 */ AS (
  SELECT
    dd.qici,
    COALESCE(dd.channel_map_1, '未知') AS channel_map_1,
    COALESCE(dd.rule_name0, '未知') AS qudao,
    dd.grade_0,
    dd.lead_id,
    dd.original_order_user_number AS uid,
    dd.performance_employee_email_name AS name,
    dd.trade_timestamp,
    CASE
      WHEN dd.service_transfer_in_amount_yuan > 0 OR dd.service_transfer_out_amount_yuan > 0
      THEN 0
      ELSE dd.income_amount
    END AS income_amount,
    CASE
      WHEN dd.service_transfer_in_amount_yuan > 0 OR dd.service_transfer_out_amount_yuan > 0
      THEN 0
      ELSE dd.refund_amount
    END AS refund_amount,
    CASE
      WHEN dd.service_transfer_in_amount_yuan > 0 OR dd.service_transfer_out_amount_yuan > 0
      THEN 0
      ELSE dd.promit_amount
    END AS promit_amount,
    dd.order_number,
    dd.rule_name,
    dd.source_lead_period_name,
    dd.trade_period_index,
    dd.full_link_period_year,
    dd.full_link_period_term,
    dd.full_link_valid_lead_count,
    dd.prelead_qici
  FROM dd
), course_transfer_gmv AS (
  SELECT
    c.qici,
    COALESCE(c.channel_map_1, '未知') AS channel_map_1,
    COALESCE(c.rule_name0, '未知') AS qudao,
    c.grade_0,
    c.lead_id,
    c.original_order_user_number AS uid,
    c.performance_employee_email_name AS name,
    c.trade_timestamp,
    c.income_amount,
    c.refund_amount,
    c.promit_amount,
    c.order_number,
    c.rule_name,
    c.source_lead_period_name,
    c.trade_period_index,
    c.full_link_period_year,
    c.full_link_period_term,
    c.full_link_valid_lead_count,
    c.prelead_qici
  FROM course_transfer_dd AS c
), gmv AS (
  SELECT
    *
  FROM service_gmv
  UNION ALL
  SELECT
    *
  FROM course_transfer_gmv
), lead_period_keys AS (
  SELECT
    g.*,
    COALESCE(
      NULLIF(g.prelead_qici, ''),
      CASE
        WHEN REGEXP_LIKE(COALESCE(g.source_lead_period_name, ''), '20[0-9]{2}')
        AND REGEXP_LIKE(COALESCE(g.source_lead_period_name, ''), '[0-9]{4}期')
        AND CONCAT(
          REGEXP_EXTRACT(g.source_lead_period_name, '(20[0-9]{2})', 1),
          REGEXP_EXTRACT(g.source_lead_period_name, '([0-9]{4}期)', 1)
        ) <> '20260814期'
        THEN CONCAT(
          REGEXP_EXTRACT(g.source_lead_period_name, '(20[0-9]{2})', 1),
          REGEXP_EXTRACT(g.source_lead_period_name, '([0-9]{4}期)', 1)
        )
      END,
      CASE
        WHEN COALESCE(g.full_link_valid_lead_count, 0) > 0
        THEN CONCAT(g.full_link_period_year, g.full_link_period_term)
      END,
      CASE
        WHEN NULLIF(REGEXP_EXTRACT(COALESCE(g.rule_name, ''), '([0-9]{4}期)', 1), '') = g.full_link_period_term
        THEN CONCAT(g.full_link_period_year, g.full_link_period_term)
      END,
      CASE
        WHEN REGEXP_LIKE(COALESCE(g.rule_name, ''), '20[0-9]{2}')
        AND REGEXP_LIKE(COALESCE(g.rule_name, ''), '[0-9]{4}期')
        THEN CONCAT(
          REGEXP_EXTRACT(g.rule_name, '(20[0-9]{2})', 1),
          REGEXP_EXTRACT(g.rule_name, '([0-9]{4}期)', 1)
        )
      END
    ) AS lead_qici
  FROM gmv AS g
), period_keys AS (
  SELECT
    k.*,
    TRY(CAST(DATE_PARSE(SUBSTR(k.lead_qici, 1, 8), '%Y%m%d') AS DATE)) AS lead_label_date
  FROM lead_period_keys AS k
), timing_base AS (
  SELECT
    k.*,
    COALESCE(
      lc.period_index,
      CASE
        WHEN k.lead_label_date BETWEEN CAST('2026-07-14' AS DATE) AND CAST('2026-09-06' AS DATE)
        THEN CAST(NULL AS BIGINT)
        WHEN k.lead_label_date >= CAST('2026-09-07' AS DATE)
        THEN 15 + CAST(FLOOR(
          DATE_DIFF(
            'DAY',
            CAST('2026-09-07' AS DATE),
            CAST(DATE_TRUNC('WEEK', CAST(k.lead_label_date AS TIMESTAMP)) AS DATE)
          ) / 7.0
        ) AS BIGINT)
        ELSE CAST(FLOOR(
          DATE_DIFF(
            'DAY',
            CAST('2026-06-02' AS DATE),
            CAST(DATE_TRUNC('WEEK', CAST(k.lead_label_date AS TIMESTAMP)) AS DATE) + INTERVAL '1' DAY
          ) / 7.0
        ) AS BIGINT)
      END
    ) AS lead_period_index
  FROM period_keys AS k
  LEFT JOIN period_aliases AS lc
    ON k.lead_qici = lc.alias_qici
), bucketed AS (
  SELECT
    t.*,
    CASE WHEN trade_period_index = lead_period_index THEN 1 ELSE 0 END AS is_on_period,
    CASE
      WHEN trade_period_index - lead_period_index = 0
      THEN 0
      WHEN trade_period_index - lead_period_index = 1
      THEN 1
      WHEN trade_period_index - lead_period_index BETWEEN 2 AND 3
      THEN 2
      WHEN trade_period_index - lead_period_index = -1
      THEN 4
      ELSE 3
    END AS week_diff
  FROM timing_base AS t
), team_org AS (
  SELECT
    qici,
    employee_email_name,
    leader_employee_email_name,
    dazu
  FROM temp_table.dingxi01_qing_team_jg
)
SELECT
  b.qici,
  b.channel_map_1 AS channel_1,
  b.qudao AS channel_2,
  jg.dazu,
  jg.leader_employee_email_name,
  b.grade_0 AS grade_list,
  b.name,
  SUM(CASE WHEN b.week_diff = 0 THEN b.promit_amount ELSE 0 END) AS gmv_7,
  SUM(CASE WHEN b.week_diff = 1 THEN b.promit_amount ELSE 0 END) AS gmv_14,
  SUM(CASE WHEN b.week_diff = 2 THEN b.promit_amount ELSE 0 END) AS gmv_30,
  SUM(CASE WHEN b.week_diff = 3 THEN b.promit_amount ELSE 0 END) AS gmv_n30,
  SUM(CASE WHEN b.week_diff = 4 THEN b.promit_amount ELSE 0 END) AS gmv_7_h,
  SUM(b.promit_amount) AS gmv_total,
  -SUM(CASE WHEN b.week_diff = 0 THEN b.refund_amount ELSE 0 END) AS refund_7,
  -SUM(CASE WHEN b.week_diff = 1 THEN b.refund_amount ELSE 0 END) AS refund_14,
  -SUM(CASE WHEN b.week_diff = 2 THEN b.refund_amount ELSE 0 END) AS refund_30,
  -SUM(CASE WHEN b.week_diff = 3 THEN b.refund_amount ELSE 0 END) AS refund_n30,
  -SUM(CASE WHEN b.week_diff = 4 THEN b.refund_amount ELSE 0 END) AS refund_7_p,
  -SUM(b.refund_amount) AS refund_total
FROM bucketed AS b
LEFT JOIN team_org AS jg
  ON b.name = jg.employee_email_name AND b.qici = jg.qici
WHERE
  COALESCE(b.promit_amount, 0) <> 0 OR COALESCE(b.refund_amount, 0) <> 0
GROUP BY
  b.qici,
  b.channel_map_1,
  b.qudao,
  jg.dazu,
  jg.leader_employee_email_name,
  b.grade_0,
  b.name
ORDER BY
  b.qici DESC,
  jg.dazu,
  jg.leader_employee_email_name,
  b.name
