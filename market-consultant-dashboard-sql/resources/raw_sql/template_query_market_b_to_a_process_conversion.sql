SELECT
        "period_name" as "period_name",
        "depart_1" as "depart_1",
        "depart" as "depart",
        "jingli" as "jingli",
        "zhuguan" as "zhuguan",
        "employee_email_name" as "employee_email_name",
        "employee_email_prefix" as "employee_email_prefix",
        "lead_id" as "lead_id",
        "user_id" as "user_id",
        "channel_map" as "channel_map",
        "lead_purchase_intention_name" as "lead_purchase_intention_name",
        "grade_1" as "grade_1",
        "lead_count" as "lead_count",
        "valid_lead_count" as "valid_lead_count",
        "conversion_lead_count" as "conversion_lead_count",
        "subject_count" as "subject_count",
        "same_lead_period_subject_count" as "same_lead_period_subject_count",
        "lb_subject_count" as "lb_subject_count",
        "same_lead_period_lb_subject_count" as "same_lead_period_lb_subject_count",
        "order_count" as "order_count",
        "income_amount" as "income_amount",
        "in_pay_period_refund_amount" as "in_pay_period_refund_amount",
        "non_pay_period_refund_amount" as "non_pay_period_refund_amount",
        "jp_cross_department_refund_amount" as "jp_cross_department_refund_amount",
        "same_lead_period_order_count" as "same_lead_period_order_count",
        "same_lead_period_conversion_lead_count" as "same_lead_period_conversion_lead_count",
        "same_lead_period_income_amount" as "same_lead_period_income_amount",
        "same_lead_period_refund_amount" as "same_lead_period_refund_amount",
        "is_friend_lead" as "is_friend_lead",
        "non_friend_lead" as "non_friend_lead",
        "is_shengou" as "is_shengou",
        "ab_intention_level" as "ab_intention_level",
        "ab_zhuanhua" as "ab_zhuanhua",
        "b_type" as "b_type",
        "d_type" as "d_type"
FROM
        (
                ------------------------基础数据        
                with
                        data_raw AS (
                            SELECT
                                CONCAT(
                                  DATE_FORMAT(
                                    DATE_ADD(
                                      'DAY',
                                      4,
                                      DATE_TRUNC(
                                        'WEEK',
                                        DATE_PARSE(REPLACE(CONCAT(group_period_year, group_period_term), '期', ''), '%Y%m%d')
                                      )
                                    ),
                                    '%Y%m%d'
                                  ),
                                  '期'
                                ) AS period_name,
                                virtual_third_department_name AS depart_1,
                                virtual_fourth_department_name AS depart,
                                virtual_leader_email_name AS jingli /* 大组长 */,
                                virtual_direct_leader_email_name AS zhuguan /* 小组长 */,
                                employee_email_name,
                                employee_email_prefix,
                                t1.lead_id,
                                user_id,
                                lead_purchase_intention_name,
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
                                  ELSE '未知'
                                END AS grade_1,
                                COALESCE(lead_count, 0) AS lead_count,
                                COALESCE(valid_lead_count, 0) AS valid_lead_count,
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
                                COALESCE(same_lead_period_order_count, 0) AS same_lead_period_order_count,
                                COALESCE(same_lead_period_conversion_lead_count, 0) AS same_lead_period_conversion_lead_count,
                                COALESCE(same_lead_period_income_amount, 0) AS same_lead_period_income_amount,
                                COALESCE(same_lead_period_refund_amount, 0) AS same_lead_period_refund_amount,
                                COALESCE(
                                  CASE WHEN CAST(valid_lead_count AS VARCHAR) = '1' THEN friend_lead_count ELSE 0 END,
                                  0
                                ) AS is_friend_lead,
                                COALESCE(
                                  CASE
                                    WHEN CAST(valid_lead_count AS VARCHAR) = '1' AND friend_lead_count = '0'
                                    THEN 1
                                    ELSE 0
                                  END,
                                  0
                                ) AS non_friend_lead,
                                COALESCE(CASE WHEN t.jieduan IN ('深沟', '已双沟') THEN 1 ELSE 0 END, 0) AS is_shengou,
                                COALESCE(
                                  CASE
                                    WHEN intention_level IN ('A', 'B') AND t.jieduan IN ('深沟', '已双沟')
                                    THEN 1
                                    ELSE 0
                                  END,
                                  0
                                ) AS AB_intention_level,
                                COALESCE(
                                  CASE
                                    WHEN intention_level IN ('A', 'B')
                                    AND t.jieduan IN ('深沟', '已双沟')
                                    AND conversion_lead_count = '1'
                                    THEN 1
                                    ELSE 0
                                  END,
                                  0
                                ) AS AB_zhuanhua,
                                t1.ad_account_name AS _map_ad_account_name,
                                t1.channel_name_1 AS _map_channel_name_1,
                                t1.channel_name_2 AS _map_channel_name_2,
                                t1.channel_name_3 AS _map_channel_name_3,
                                t1.channel_provider_name AS _map_channel_provider_name,
                                t1.channel_second_provider_name AS _map_channel_second_provider_name,
                                t1.first_department_name AS _map_first_department_name,
                                t1.flow_order_price AS _map_flow_order_price,
                                t1.flow_orders_income_amount AS _map_flow_orders_income_amount,
                                t1.flow_original_order_activity_price AS _map_flow_original_order_activity_price,
                                t1.flow_pool_name AS _map_flow_pool_name,
                                t1.get_customer_way_name AS _map_get_customer_way_name,
                                t1.lead_create_time AS _map_lead_create_time,
                                t1.lead_purchase_intention_level1_category_name AS _map_lead_purchase_intention_level1_category_name,
                                t1.lead_purchase_intention_level2_category_name AS _map_lead_purchase_intention_level2_category_name,
                                t1.page_id_name AS _map_page_id_name,
                                t1.period_name AS _map_period_name,
                                t1.put_plan_name AS _map_put_plan_name,
                                t1.rule_name AS _map_rule_name,
                                t1.second_department_name AS _map_second_department_name,
                                t1.sku_id_name AS _map_sku_id_name,
                                t1.source_manager_name AS _map_source_manager_name,
                                t1.source_put_plan_name AS _map_source_put_plan_name,
                                t1.third_department_name AS _map_third_department_name,
                                t1.trace_type_name AS _map_trace_type_name,
                                t1.virtual_fifth_department_name AS _map_virtual_fifth_department_name,
                                t1.virtual_fourth_department_name AS _map_virtual_fourth_department_name,
                                t1.virtual_second_department_name AS _map_virtual_second_department_name,
                                row_number() OVER () AS _mapping_row_id
                            FROM bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df AS t1
                            LEFT JOIN (
                              SELECT
                                user_number,
                                sale_flow_stage_sequence,
                                sale_flow_stage_name_1,
                                jieduan_1 AS jieduan
                              FROM (
                                SELECT
                                  user_number,
                                  sale_flow_stage_sequence,
                                  CASE
                                    WHEN sale_flow_stage_sequence = '50'
                                    THEN '新线索'
                                    WHEN sale_flow_stage_sequence = '60'
                                    THEN '待跟进'
                                    WHEN sale_flow_stage_sequence = '70'
                                    THEN '已接收'
                                    WHEN sale_flow_stage_sequence = '100'
                                    THEN '未接通'
                                    WHEN sale_flow_stage_sequence = '150'
                                    THEN '已建联'
                                    WHEN sale_flow_stage_sequence = '200'
                                    THEN '首call'
                                    WHEN sale_flow_stage_sequence = '250'
                                    THEN '商机'
                                    WHEN sale_flow_stage_sequence = '300'
                                    THEN '学情沟通'
                                    WHEN sale_flow_stage_sequence = '350'
                                    THEN '浅沟'
                                    WHEN sale_flow_stage_sequence = '400'
                                    THEN '已约课'
                                    WHEN sale_flow_stage_sequence = '450'
                                    THEN '深沟'
                                    WHEN sale_flow_stage_sequence = '470'
                                    THEN '已双沟'
                                    WHEN sale_flow_stage_sequence = '500'
                                    THEN '再次建联'
                                    WHEN sale_flow_stage_sequence = '550'
                                    THEN '约课'
                                    WHEN sale_flow_stage_sequence = '600'
                                    THEN '诺访'
                                    WHEN sale_flow_stage_sequence = '650'
                                    THEN '已排课'
                                    WHEN sale_flow_stage_sequence = '660'
                                    THEN '已摸底测'
                                    WHEN sale_flow_stage_sequence = '680'
                                    THEN '促到课'
                                    WHEN sale_flow_stage_sequence = '700'
                                    THEN '已到课'
                                    WHEN sale_flow_stage_sequence = '710'
                                    THEN '中教完课'
                                    WHEN sale_flow_stage_sequence = '720'
                                    THEN '外教完课'
                                    WHEN sale_flow_stage_sequence = '750'
                                    THEN '已完课'
                                    WHEN sale_flow_stage_sequence = '800'
                                    THEN '到访'
                                    WHEN sale_flow_stage_sequence = '820'
                                    THEN '看回放'
                                    WHEN sale_flow_stage_sequence = '850'
                                    THEN '铺课'
                                    WHEN sale_flow_stage_sequence = '900'
                                    THEN '已推课'
                                    WHEN sale_flow_stage_sequence = '920'
                                    THEN '定金'
                                    WHEN sale_flow_stage_sequence = '925'
                                    THEN '已挖需'
                                    WHEN sale_flow_stage_sequence = '930'
                                    THEN '已规划'
                                    WHEN sale_flow_stage_sequence = '935'
                                    THEN '已报价'
                                    WHEN sale_flow_stage_sequence = '950'
                                    THEN '关单'
                                    WHEN sale_flow_stage_sequence = '955'
                                    THEN '追单'
                                    WHEN sale_flow_stage_sequence = '960'
                                    THEN '流转成功'
                                    WHEN sale_flow_stage_sequence = '1000'
                                    THEN '未成交'
                                    WHEN sale_flow_stage_sequence = '1050'
                                    THEN '成单'
                                    ELSE '未知状态'
                                  END AS sale_flow_stage_name_1,
                                  CASE
                                    WHEN sale_flow_stage_sequence = '450'
                                    THEN '深沟'
                                    WHEN sale_flow_stage_sequence = '470'
                                    THEN '已双沟'
                                    ELSE '其他'
                                  END AS jieduan_1,
                                  ROW_NUMBER() OVER (PARTITION BY user_number ORDER BY private_sea_update_time DESC) AS rn
                                FROM service_dw.dwd_crm_assign_private_detail_hf
                                WHERE
                                  dt = FORMAT_DATETIME(CURRENT_TIMESTAMP - INTERVAL '2' HOUR, 'YYYYMMdd')
                                  AND hour = FORMAT_DATETIME(CURRENT_TIMESTAMP - INTERVAL '2' HOUR, 'HH')
                                  AND assign_employee_first_level_department_name = 'H业务线'
                                  AND assign_employee_second_level_department_name = '市场部'
                                  AND assign_employee_third_level_department_name = '市场顾问部'
                              )
                              WHERE
                                rn = 1
                            ) AS t
                              ON t1.user_id = t.user_number
                            WHERE
                              dt = FORMAT_DATETIME(CURRENT_TIMESTAMP - INTERVAL '2' HOUR, 'YYYYMMdd')
                              AND hour = FORMAT_DATETIME(CURRENT_TIMESTAMP - INTERVAL '2' HOUR, 'HH')
                              AND section_assign_employee_first_level_department_name = 'H业务线'
                              AND section_assign_employee_second_level_department_name = '市场部'
                              AND period_mapping_first_level_department_name = 'H业务线'
                              AND period_mapping_second_level_department_name = '市场部'
                        ),
                        channel_union AS (
                            SELECT
                                data_raw.*,
                                CASE
                                  WHEN _map_get_customer_way_name in ('平台自播') and _map_flow_pool_name in ('赢战广东中考','高途专版图书','状元帮教辅','高途专版视频书','本地化专版图书','广东专版图书') THEN '广东图书'
                                  WHEN _map_get_customer_way_name IN ('平台自播')
                                  AND _map_flow_pool_name IN (
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
                                  WHEN _map_get_customer_way_name IN ('平台自播')
                                  AND _map_flow_pool_name IN ('沪上名校', '沪上领航社', '简学文化', '魔都校友助学馆', '沪上领航高中', '沪上领航初中')
                                  THEN '上海图书'
                                  WHEN _map_get_customer_way_name IN ('平台自播')
                                  AND _map_flow_pool_name IN ('高途江苏中考', '高途赢战中考')
                                  THEN '江苏图书'
                                  WHEN _map_flow_pool_name = '电商退款用户池'
                                  AND _map_rule_name LIKE '%赠失%'
                                  AND _map_rule_name LIKE '%朱博士%'
                                  THEN '赠课失败-朱汉祺'
                                  WHEN _map_flow_pool_name = '电商退款用户池'
                                  AND _map_rule_name LIKE '%赠失%'
                                  AND _map_rule_name LIKE '%春春%'
                                  THEN '赠课失败-陈瑞春'
                                  WHEN _map_flow_pool_name = '电商退款用户池'
                                  AND _map_rule_name LIKE '%赠失%'
                                  AND _map_rule_name LIKE '%亚飞%'
                                  THEN '赠课失败-孟亚飞'
                                  WHEN _map_flow_pool_name = '电商退款用户池'
                                  AND _map_rule_name LIKE '%赠失%'
                                  AND _map_rule_name LIKE '%星义%'
                                  THEN '赠课失败-赵星义'
                                  WHEN _map_flow_pool_name = '电商退款用户池'
                                  AND _map_rule_name LIKE '%赠失%'
                                  AND _map_rule_name LIKE '%郭艺%'
                                  THEN '赠课失败-郭艺'
                                  WHEN _map_second_department_name = '本地化大班学部'
                                  OR _map_source_manager_name IN ('鲍大海', '杨文卓', '喻新桥')
                                  THEN '本地化市场流量'
                                  WHEN _map_third_department_name IN ('中价产品项目部', '新媒体内容运营部')
                                  AND _map_rule_name LIKE '%曹忆%'
                                  THEN '曹忆'
                                  WHEN _map_rule_name LIKE '%语数英%' AND _map_third_department_name = '新媒体内容运营部'
                                  THEN '语数英'
                                  WHEN _map_third_department_name = '直播部' AND _map_sku_id_name LIKE '%山东专版%'
                                  THEN '北京直播山东'
                                  WHEN _map_third_department_name = '直播部' AND _map_sku_id_name LIKE '%河南专版%'
                                  THEN '北京直播河南'
                                  WHEN _map_sku_id_name LIKE '%江苏%' AND _map_third_department_name = '直播部'
                                  THEN '北京直播江苏'
                                  WHEN _map_third_department_name LIKE '%锋途%' AND _map_channel_name_2 = '抖音'
                                  THEN '锋途KOC'
                                  WHEN _map_third_department_name = '线上商务部' AND _map_flow_pool_name LIKE '%图书订单%'
                                  THEN '图书解密'
                                  WHEN _map_put_plan_name LIKE '%小红书打粉%'
                                  THEN 'EM-小红书合作'
                                  WHEN _map_third_department_name IN ('投放部', '线上商务部', '小红书攻坚组')
                                  AND _map_channel_name_2 = '小红书'
                                  THEN '小红书-闯闯组'
                                  WHEN _map_third_department_name IN ('新媒体内容运营部') AND _map_channel_name_2 = '小红书'
                                  THEN '小红书直投-绍孜组'
                                  WHEN _map_page_id_name LIKE '%0元领课%' AND _map_third_department_name = '投放部'
                                  THEN '信息流0元'
                                  WHEN _map_page_id_name LIKE '%周帅0元腾讯%' AND _map_third_department_name = '投放部'
                                  THEN '信息流0转低'
                                  WHEN _map_page_id_name LIKE '%信息流下引%' AND _map_third_department_name = '私域运营部'
                                  THEN '信息流0转低'
                                  WHEN _map_sku_id_name like '%数理系统%' and _map_third_department_name in ('快乐成长组','直播部','市场效能部','运营部') THEN '物理系统'
                                  WHEN _map_trace_type_name LIKE '%转介绍%'
                                  THEN '转介绍'
                                  WHEN _map_ad_account_name IN (
                                    '高途-高中-DYD搜索-QZ49',
                                    '高途-高中-DYD搜索-XLHD49',
                                    '高途-高中-DYD搜索-XLHD50',
                                    '高途-高中-DYD搜索-QZ50'
                                  )
                                  OR _map_ad_account_name LIKE '%DYD1元搜索%'
                                  THEN '搜索1元'
                                  WHEN (
                                    _map_flow_pool_name LIKE '%江苏预习%' OR _map_flow_pool_name LIKE '%江苏专版预习%'
                                  )
                                  AND _map_channel_name_2 = '抖音'
                                  THEN '西安直播江苏-抖音'
                                  WHEN _map_flow_pool_name LIKE '%自然流%'
                                  AND _map_rule_name LIKE '%江苏%'
                                  AND _map_third_department_name = '图书营销部'
                                  AND _map_channel_name_2 = '抖音'
                                  THEN '西安直播江苏-抖音'
                                  WHEN (
                                    _map_flow_pool_name LIKE '%江苏预习%' OR _map_flow_pool_name LIKE '%江苏专版预习%'
                                  )
                                  AND _map_channel_name_2 = '视频号'
                                  THEN '西安直播江苏-视频号'
                                  WHEN _map_flow_pool_name LIKE '%退款%' AND _map_third_department_name = '图书营销部'
                                  THEN '西安直播-退款订单复用'
                                  WHEN _map_flow_pool_name LIKE '%自然流%'
                                  AND _map_rule_name LIKE '%江苏%'
                                  AND _map_third_department_name = '图书营销部'
                                  AND _map_channel_name_2 = '视频号'
                                  THEN '西安直播江苏-视频号'
                                  WHEN _map_sku_id_name LIKE '%2000题%' AND _map_third_department_name = '图书营销部'
                                  THEN '西安直播2000题'
                                  WHEN _map_sku_id_name LIKE '%五年高考%' AND _map_third_department_name = '图书营销部'
                                  THEN '西安直播五年真题'
                                  WHEN (
                                    _map_rule_name LIKE '%北京图书%' OR _map_sku_id_name LIKE '%北京专版%'
                                  )
                                  AND _map_third_department_name = '图书营销部'
                                  THEN '西安直播北京'
                                  WHEN _map_sku_id_name LIKE '%安徽%' AND _map_third_department_name = '图书营销部'
                                  THEN '西安直播安徽'
                                  WHEN _map_put_plan_name LIKE '%全国教考%' AND _map_third_department_name = '图书营销部'
                                  THEN '西安直播全国'
                                  WHEN _map_flow_pool_name LIKE '%自然流%'
                                  AND _map_rule_name LIKE '%北京%'
                                  AND _map_third_department_name = '图书营销部'
                                  THEN '西安直播北京'
                                  WHEN _map_sku_id_name LIKE '%2000题%' AND _map_third_department_name = '直播部'
                                  THEN 'IP直播-2000题'
                                  WHEN _map_flow_pool_name LIKE '%星义大大%' OR _map_flow_pool_name LIKE '%星义物理%'
                                  THEN '赵星义'
                                  WHEN (
                                    _map_source_manager_name IN ('马思雨02', '袁银') AND _map_rule_name LIKE '%集团%'
                                  )
                                  AND NOT COALESCE(
                                    (
                                      (
                                        _map_third_department_name = '私域运营部'
                                        AND _map_source_manager_name IN (
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
                                        _map_flow_pool_name LIKE '%南通欣创%'
                                        OR _map_flow_pool_name LIKE '%人人通科技%'
                                        OR _map_flow_pool_name LIKE '%易而购%'
                                        OR _map_flow_pool_name LIKE '%济南梦航%'
                                        OR _map_flow_pool_name LIKE '%晨硕智学%'
                                        OR _map_flow_pool_name LIKE '%兴尧文化%'
                                        OR _map_flow_pool_name LIKE '%济南映像%'
                                        OR _map_flow_pool_name LIKE '%山东简单%'
                                        OR _map_flow_pool_name LIKE '%争鸣科技%'
                                      )
                                      OR (
                                        (
                                          _map_flow_pool_name LIKE '%家校共育%'
                                          OR _map_flow_pool_name LIKE '%保持热爱%'
                                          OR _map_flow_pool_name LIKE '%青松%'
                                          OR _map_flow_pool_name LIKE '%悟之道%'
                                        )
                                        AND _map_put_plan_name NOT LIKE '%0元%'
                                      )
                                      OR (
                                        _map_source_manager_name = '李宁24' AND _map_put_plan_name LIKE '%0转低%'
                                      )
                                      OR (
                                        _map_third_department_name = '私域运营部'
                                        AND _map_flow_original_order_activity_price IN ('100.0', '900.0', '300.0')
                                      )
                                      OR (
                                        _map_third_department_name = '私域运营部'
                                        AND _map_flow_original_order_activity_price IN ('0.0')
                                        AND _map_source_manager_name IN ('陈雷19', '崔慧敏01', '侯佳林01', '郑天琪02', '杨彬屹', '曹义鹏', '王硕阳', '于超研')
                                      )
                                      OR (
                                        _map_flow_pool_name LIKE '公导私'
                                      )
                                      OR (
                                        _map_flow_pool_name LIKE '%0转低转正%' OR _map_channel_name_2 = '产研测试'
                                      )
                                    ),
                                    FALSE
                                  )
                                  THEN '集团私域'
                                END AS channel_map,
                                1 AS _mapping_priority
                            FROM data_raw
                            UNION ALL
                            SELECT
                                data_raw.*,
                                CASE
                                  WHEN _map_rule_name LIKE '%途途私域%'
                                  OR (
                                    _map_rule_name LIKE '%私域%' AND _map_first_department_name = 'TT'
                                  )
                                  OR _map_rule_name LIKE '%私域1元%'
                                  OR (
                                    _map_third_department_name = '私域招生中心' AND _map_flow_pool_name LIKE '%APP%'
                                  )
                                  THEN '途途私域'
                                  WHEN _map_third_department_name = '图书营销部'
                                  AND (
                                    _map_sku_id_name LIKE '%孟亚飞99%' OR _map_sku_id_name LIKE '%亚飞%'
                                  )
                                  AND _map_channel_name_2 = '百度'
                                  THEN '孟亚飞-2组-百度'
                                  WHEN _map_third_department_name = '图书营销部'
                                  AND (
                                    _map_sku_id_name LIKE '%孟亚飞99%' OR _map_sku_id_name LIKE '%亚飞%'
                                  )
                                  AND _map_channel_name_2 = '抖音'
                                  THEN '孟亚飞-2组-抖音'
                                  WHEN _map_third_department_name = '投放部' AND (
                                    _map_ad_account_name LIKE '%周帅%'
                                  )
                                  THEN '信息流-周帅'
                                  WHEN _map_source_manager_name IN ('韩正卿')
                                  THEN '抖音私信'
                                  WHEN _map_channel_name_1 = '市场私域' AND _map_put_plan_name LIKE '%孟亚飞汇总%'
                                  THEN '小红书自然流-绍孜组'
                                  WHEN _map_channel_name_1 = '市场私域'
                                  AND (
                                    _map_virtual_fourth_department_name IN ('郑州学习顾问二部', '郑州学习顾问七部', '郑州训练营')
                                    AND (
                                      _map_rule_name LIKE '%表单%' OR _map_trace_type_name LIKE '%引流课%'
                                    )
                                  )
                                  THEN '市场私域低价单'
                                  WHEN _map_third_department_name = '私域运营部'
                                  AND _map_source_manager_name IN (
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
                                    _map_rule_name LIKE '%koc自孵化下引%'
                                    OR _map_rule_name LIKE '%koc下引%'
                                    OR _map_page_id_name LIKE '%自营%'
                                  )
                                  THEN '自孵化KOC下引'
                                  WHEN _map_third_department_name = '私域运营部'
                                  AND _map_source_manager_name IN (
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
                                  WHEN _map_channel_name_1 = '市场私域'
                                  AND (
                                    _map_virtual_fourth_department_name IN ('郑州学习顾问二部', '郑州学习顾问七部', '郑州训练营')
                                    OR _map_virtual_fifth_department_name IN ('罗江博团队')
                                  )
                                  THEN '市场私域入群'
                                  WHEN _map_third_department_name = '图书营销部'
                                  AND (
                                    _map_rule_name LIKE '%点睛卷%' OR _map_sku_id_name LIKE '%押题卷%'
                                  )
                                  THEN '押题卷'
                                  WHEN _map_third_department_name = '投放部'
                                  AND _map_channel_name_2 = '小红书'
                                  AND _map_channel_name_1 <> '搜索营销'
                                  THEN '信息流-小红书'
                                  WHEN _map_third_department_name = '线上商务部' AND _map_channel_name_2 = '小红书'
                                  THEN '小红书'
                                  WHEN (
                                    _map_flow_pool_name LIKE '%北大汤哥%'
                                    OR _map_flow_pool_name LIKE '%海淀名师高阶%'
                                    OR _map_flow_pool_name LIKE '%海淀高阶%'
                                    OR _map_flow_pool_name LIKE '%高阶英语887%'
                                  )
                                  AND _map_sku_id_name LIKE '%小艺%'
                                  THEN '郭艺'
                                  WHEN _map_third_department_name LIKE '%私域%'
                                  AND _map_rule_name LIKE '%私域%'
                                  AND _map_rule_name LIKE '%图书%'
                                  THEN '市场私域图书'
                                  WHEN _map_third_department_name LIKE '%私域%' AND _map_rule_name LIKE '%公域自然流%'
                                  THEN '小红书自然流-绍孜组'
                                  WHEN _map_third_department_name LIKE '%私域%' AND _map_rule_name LIKE '%品效%'
                                  THEN '市场私域品效'
                                  WHEN _map_third_department_name LIKE '%私域%' AND _map_put_plan_name LIKE '%会话%'
                                  THEN '市场私域会话'
                                  WHEN _map_third_department_name LIKE '%私域%' AND _map_rule_name LIKE '%公域学霸%'
                                  THEN '市场私域公域组'
                                  WHEN _map_third_department_name IN ('线上商务部')
                                  AND _map_source_manager_name IN ('孙晗01', '方俊结01', '刘亦鹏02', '何木玲', '杨梓月', '张可意03', '任颖迪', '曹蕊07', '曲默晗')
                                  AND _map_flow_pool_name LIKE '%退款%'
                                  THEN 'KOC-退款订单复用'
                                  WHEN _map_third_department_name IN ('直播部', '新媒体内容运营部', '市场一组', '私域运营部')
                                  AND _map_flow_pool_name = '电商退款用户池'
                                  THEN 'IP退款订单复用'
                                  WHEN _map_third_department_name IN ('直播部', '新媒体内容运营部', '市场一组', '私域运营部')
                                  AND _map_put_plan_name LIKE '%失败%'
                                  AND _map_flow_pool_name = '电商退款用户池'
                                  THEN '赠课失败'
                                  WHEN _map_third_department_name IN ('直播部', '新媒体内容运营部', '市场一组')
                                  AND (
                                    _map_flow_pool_name = '初阶化学规划' OR _map_flow_pool_name LIKE '%启迪-初阶老师%'
                                  )
                                  THEN '曹忆'
                                  WHEN (
                                    _map_third_department_name = '图书营销部' AND _map_sku_id_name LIKE '%真题%'
                                  )
                                  OR (
                                    _map_third_department_name = '直播部' AND _map_sku_id_name LIKE '%真题%'
                                  )
                                  THEN '西安图书直播间-直播'
                                  WHEN (
                                    _map_third_department_name = '图书营销部' AND _map_sku_id_name NOT LIKE '%真题%'
                                  )
                                  OR (
                                    _map_third_department_name = '直播部' AND _map_sku_id_name LIKE '%秒懂%'
                                  )
                                  OR (
                                    _map_third_department_name = '直播部' AND _map_sku_id_name LIKE '%图书赠送%'
                                  )
                                  THEN '西安图书直播间-挂链'
                                  WHEN _map_third_department_name IN ('直播部', '新媒体内容运营部', '市场一组')
                                  AND (
                                    _map_flow_pool_name LIKE '%海淀高阶名师%'
                                    OR _map_flow_pool_name LIKE '%海淀老师高阶%'
                                    OR _map_flow_pool_name LIKE '%小艺%'
                                    OR _map_flow_pool_name LIKE '%老蒋文化%'
                                  )
                                  THEN '郭艺'
                                  WHEN _map_third_department_name IN ('直播部', '新媒体内容运营部', '市场一组')
                                  AND _map_flow_pool_name LIKE '%电商退款%'
                                  AND _map_rule_name LIKE '%郭艺99%'
                                  THEN '郭艺'
                                  WHEN _map_put_plan_name LIKE '%国培教育-0元%'
                                  OR _map_put_plan_name LIKE '%易喆教育-0元%'
                                  OR _map_put_plan_name LIKE '%钟情-0元%'
                                  OR _map_put_plan_name LIKE '%中望达-0元%'
                                  OR _map_put_plan_name LIKE '%晨硕-0元%'
                                  OR _map_put_plan_name LIKE '%彩石-0元入群%'
                                  THEN '创新商务入群'
                                  WHEN _map_third_department_name = 'KOC孵化部'
                                  AND _map_flow_pool_name LIKE '%电商退款%'
                                  AND _map_put_plan_name LIKE '%失败%'
                                  THEN '自孵化KOC-赠课失败'
                                  WHEN _map_third_department_name = 'KOC孵化部'
                                  AND _map_flow_pool_name LIKE '%电商退款%'
                                  AND _map_put_plan_name LIKE '%退%'
                                  THEN '自孵化KOC-退款订单复用'
                                  WHEN _map_source_manager_name = '方俊结01' AND _map_put_plan_name LIKE '%赠课后退款%'
                                  THEN 'KOC-赠课后退款'
                                  WHEN _map_third_department_name = '直播部'
                                  AND (
                                    _map_sku_id_name LIKE '%春春%'
                                    OR _map_sku_id_name LIKE '%瑞春%'
                                    OR _map_rule_name LIKE '%春春%'
                                    OR _map_rule_name LIKE '%瑞春%'
                                  )
                                  AND _map_channel_name_2 = '百度'
                                  THEN '陈瑞春-百度'
                                  WHEN _map_third_department_name = '直播部'
                                  AND (
                                    _map_sku_id_name LIKE '%春春%'
                                    OR _map_sku_id_name LIKE '%瑞春%'
                                    OR _map_rule_name LIKE '%春春%'
                                    OR _map_rule_name LIKE '%瑞春%'
                                  )
                                  AND _map_channel_name_2 = 'B站'
                                  THEN '陈瑞春-B站'
                                  WHEN _map_third_department_name = '直播部'
                                  AND (
                                    _map_sku_id_name LIKE '%春春%'
                                    OR _map_sku_id_name LIKE '%瑞春%'
                                    OR _map_rule_name LIKE '%春春%'
                                    OR _map_rule_name LIKE '%瑞春%'
                                  )
                                  AND _map_channel_name_2 = '抖音'
                                  THEN '陈瑞春-抖音199'
                                  WHEN _map_third_department_name IN ('直播部', '新媒体内容运营部')
                                  AND (
                                    _map_sku_id_name LIKE '%春春%'
                                    OR _map_sku_id_name LIKE '%瑞春%'
                                    OR _map_rule_name LIKE '%春春%'
                                    OR _map_rule_name LIKE '%瑞春%'
                                  )
                                  AND _map_channel_name_2 = '视频号'
                                  THEN '陈瑞春-视频号49'
                                  WHEN _map_third_department_name = '直播部'
                                  AND (
                                    _map_sku_id_name LIKE '%朱博士99%'
                                    OR _map_rule_name LIKE '%朱汉祺99%'
                                    OR _map_rule_name LIKE '%朱博士%'
                                    OR _map_flow_pool_name LIKE '%朱博士%'
                                    OR _map_sku_id_name LIKE '%朱博士%'
                                  )
                                  AND _map_channel_name_2 = 'B站'
                                  THEN '朱博士-B站'
                                  WHEN _map_third_department_name = '直播部'
                                  AND (
                                    _map_sku_id_name LIKE '%朱博士99%'
                                    OR _map_rule_name LIKE '%朱汉祺99%'
                                    OR _map_rule_name LIKE '%朱博士%'
                                    OR _map_flow_pool_name LIKE '%朱博士%'
                                    OR _map_sku_id_name LIKE '%朱博士%'
                                  )
                                  AND _map_channel_name_2 = '百度'
                                  THEN '朱博士-百度'
                                  WHEN _map_third_department_name = '直播部'
                                  AND (
                                    _map_sku_id_name LIKE '%抖音99%' AND _map_sku_id_name LIKE '%朱博士%'
                                  )
                                  AND _map_channel_name_2 = '抖音'
                                  THEN '朱博士-抖音99'
                                  WHEN _map_third_department_name = '直播部'
                                  AND (
                                    _map_sku_id_name LIKE '%朱博士99%'
                                  )
                                  AND _map_channel_name_2 = '抖音'
                                  THEN '朱博士-抖音99'
                                  WHEN _map_third_department_name = '直播部' and (_map_sku_id_name like '%朱博士99%' or _map_rule_name like '%朱汉祺99%' or _map_rule_name like '%朱博士%' or _map_flow_pool_name like '%朱博士%' or _map_sku_id_name like '%朱博士%' or _map_rule_name like '%朱汉祺199%') and _map_channel_name_2 = '抖音' THEN '朱博士-抖音199'
                                END AS channel_map,
                                2 AS _mapping_priority
                            FROM data_raw
                            UNION ALL
                            SELECT
                                data_raw.*,
                                CASE
                                  WHEN _map_third_department_name = '直播部' and (_map_sku_id_name like '%朱博士99%' or _map_rule_name like '%朱汉祺99%' or _map_rule_name like '%朱博士%' or _map_flow_pool_name like '%朱博士%' or _map_sku_id_name like '%朱博士%' or _map_rule_name like '%朱汉祺49%') and _map_channel_name_2 = '视频号' THEN '朱博士-视频号49'
                                  WHEN (
                                    _map_third_department_name = '直播部'
                                    AND (
                                      _map_sku_id_name LIKE '%朱博士%' OR _map_sku_id_name LIKE '%朱汉祺%'
                                    )
                                    AND _map_rule_name LIKE '%9%'
                                    AND _map_rule_name NOT LIKE '%29%'
                                    AND _map_sku_id_name NOT LIKE '%急%'
                                    AND _map_sku_id_name NOT LIKE '%礼盒29%'
                                  )
                                  OR (
                                    _map_third_department_name = '直播部' AND _map_sku_id_name LIKE '%朱博士9%'
                                  )
                                  THEN '朱博士9元'
                                  WHEN _map_ad_account_name LIKE '%春春%' AND _map_channel_name_1 = '信息流'
                                  THEN '信息流-陈瑞春'
                                  WHEN _map_channel_name_1 = '信息流'
                                  AND _map_channel_name_2 = 'B站'
                                  AND (
                                    _map_page_id_name LIKE '%0元物化%'
                                  )
                                  THEN 'B站信息流-曹忆'
                                  WHEN _map_channel_name_1 = '信息流'
                                  AND _map_channel_name_2 = 'B站'
                                  AND (
                                    _map_page_id_name LIKE '%赵星义%'
                                  )
                                  THEN 'B站信息流-赵星义'
                                  WHEN _map_channel_name_1 = '信息流'
                                  AND _map_channel_name_2 = 'B站'
                                  AND (
                                    _map_page_id_name LIKE '%亚飞%'
                                    OR _map_source_put_plan_name LIKE '%亚飞%'
                                    OR _map_page_id_name LIKE '%初中-0元%'
                                  )
                                  THEN 'B站信息流-亚飞'
                                  WHEN (
                                    _map_flow_pool_name LIKE '%朱博士%'
                                    OR _map_flow_pool_name LIKE '%双博士%'
                                    OR _map_flow_pool_name LIKE '%教育规划%'
                                  )
                                  AND _map_third_department_name <> '线上商务部'
                                  AND _map_period_name NOT LIKE '%多学科拓展%'
                                  AND _map_rule_name NOT LIKE '%张杰%'
                                  AND _map_sku_id_name NOT LIKE '%马凯鹏IP%'
                                  AND _map_third_department_name = '直播部'
                                  THEN '朱博士29'
                                  WHEN _map_put_plan_name LIKE '%朱博士说教育%'
                                  AND _map_period_name NOT LIKE '%多学科拓展%'
                                  AND _map_flow_pool_name NOT LIKE '%高分讲堂%'
                                  AND _map_flow_pool_name NOT LIKE '%总裁%'
                                  AND _map_third_department_name = '直播部'
                                  THEN '朱博士29'
                                  WHEN (
                                    _map_flow_pool_name LIKE '%朱博士讲英语%'
                                    OR _map_flow_pool_name LIKE '%朱博士英语%'
                                    OR _map_flow_pool_name LIKE '%朱汉祺说英语%'
                                    OR _map_flow_pool_name LIKE '%朱博士说英语%'
                                    OR _map_flow_pool_name LIKE '%教育规划%'
                                    OR _map_flow_pool_name LIKE '%双博士英语规划%'
                                    OR _map_flow_pool_name LIKE '%朱博士满分英语%'
                                    OR _map_flow_pool_name LIKE '%英语教父朱博士%'
                                    OR (
                                      _map_flow_pool_name LIKE '%中考决胜天团%'
                                      AND _map_lead_purchase_intention_level1_category_name = '规划系统'
                                    )
                                  )
                                  AND _map_third_department_name = '直播部'
                                  AND _map_period_name NOT LIKE '%多学科拓展%'
                                  AND _map_sku_id_name NOT LIKE '%马凯鹏IP%'
                                  AND _map_third_department_name = '直播部'
                                  THEN '朱博士29'
                                  WHEN (
                                    _map_flow_pool_name LIKE '%汤哥%' OR _map_flow_pool_name LIKE '%汤老师%'
                                  )
                                  AND _map_period_name NOT LIKE '%多学科拓展%'
                                  AND _map_third_department_name IN ('直播部', '新媒体内容运营部')
                                  THEN '汤老师'
                                  WHEN _map_source_manager_name = '陈晓菁04'
                                  AND _map_channel_provider_name NOT LIKE '%开拓%'
                                  AND _map_put_plan_name NOT LIKE '%九学%'
                                  THEN '商务低价'
                                  WHEN (
                                    _map_flow_pool_name LIKE '%孟帝%'
                                    OR _map_flow_pool_name LIKE '%孟老师%'
                                    OR _map_flow_pool_name LIKE '%中考数学冲刺%'
                                    OR _map_flow_pool_name LIKE '%8升9数学%'
                                    OR _map_flow_pool_name LIKE '%孟亚飞讲数学%'
                                    OR _map_flow_pool_name LIKE '%中考冲刺%'
                                    OR _map_flow_pool_name LIKE '%中考满分冲刺%'
                                    OR _map_flow_pool_name LIKE '%押题王孟亚飞%'
                                    OR _map_flow_pool_name LIKE '%中考数学大通关%'
                                    OR _map_flow_pool_name LIKE '%中考数学规划%'
                                    OR _map_flow_pool_name LIKE '%亚飞数学%'
                                    OR _map_flow_pool_name LIKE '%孟帝数学%'
                                    OR _map_flow_pool_name LIKE '%亚飞秒解思维%'
                                    OR _map_flow_pool_name LIKE '%亚飞解题%'
                                  )
                                  AND _map_period_name NOT LIKE '%多学科拓展%'
                                  AND _map_channel_name_2 NOT LIKE '%KOL%'
                                  AND _map_third_department_name = '直播部'
                                  AND _map_channel_name_2 = '抖音'
                                  THEN '孟亚飞-1组-抖音'
                                  WHEN (
                                    _map_flow_pool_name LIKE '%孟帝%'
                                    OR _map_flow_pool_name LIKE '%孟老师%'
                                    OR _map_flow_pool_name LIKE '%中考数学冲刺%'
                                    OR _map_flow_pool_name LIKE '%8升9数学%'
                                    OR _map_flow_pool_name LIKE '%孟亚飞讲数学%'
                                    OR _map_flow_pool_name LIKE '%中考冲刺%'
                                    OR _map_flow_pool_name LIKE '%中考满分冲刺%'
                                    OR _map_flow_pool_name LIKE '%押题王孟亚飞%'
                                    OR _map_flow_pool_name LIKE '%中考数学大通关%'
                                    OR _map_flow_pool_name LIKE '%中考数学规划%'
                                    OR _map_flow_pool_name LIKE '%亚飞数学%'
                                    OR _map_flow_pool_name LIKE '%孟帝数学%'
                                  )
                                  AND _map_period_name NOT LIKE '%多学科拓展%'
                                  AND _map_channel_name_2 NOT LIKE '%KOL%'
                                  AND _map_third_department_name = '直播部'
                                  AND _map_channel_name_2 = '视频号'
                                  THEN '孟亚飞-1组-视频号'
                                  WHEN (
                                    _map_flow_pool_name LIKE '%孟帝%'
                                    OR _map_flow_pool_name LIKE '%孟老师%'
                                    OR _map_flow_pool_name LIKE '%中考数学冲刺%'
                                    OR _map_flow_pool_name LIKE '%8升9数学%'
                                    OR _map_flow_pool_name LIKE '%孟亚飞讲数学%'
                                    OR _map_flow_pool_name LIKE '%中考冲刺%'
                                    OR _map_flow_pool_name LIKE '%中考满分冲刺%'
                                    OR _map_flow_pool_name LIKE '%押题王孟亚飞%'
                                    OR _map_flow_pool_name LIKE '%中考数学大通关%'
                                    OR _map_flow_pool_name LIKE '%中考数学规划%'
                                    OR _map_flow_pool_name LIKE '%亚飞数学%'
                                    OR _map_flow_pool_name LIKE '%孟帝数学%'
                                  )
                                  AND _map_period_name NOT LIKE '%多学科拓展%'
                                  AND _map_channel_name_2 NOT LIKE '%KOL%'
                                  AND _map_third_department_name = '直播部'
                                  AND _map_channel_name_2 = 'B站'
                                  THEN '孟亚飞-1组-B站'
                                  WHEN (
                                    _map_flow_pool_name LIKE '%孟帝%'
                                    OR _map_flow_pool_name LIKE '%孟老师%'
                                    OR _map_flow_pool_name LIKE '%中考数学冲刺%'
                                    OR _map_flow_pool_name LIKE '%8升9数学%'
                                    OR _map_flow_pool_name LIKE '%孟亚飞讲数学%'
                                    OR _map_flow_pool_name LIKE '%中考冲刺%'
                                    OR _map_flow_pool_name LIKE '%中考满分冲刺%'
                                    OR _map_flow_pool_name LIKE '%押题王孟亚飞%'
                                    OR _map_flow_pool_name LIKE '%中考数学大通关%'
                                    OR _map_flow_pool_name LIKE '%中考数学规划%'
                                    OR _map_flow_pool_name LIKE '%亚飞数学%'
                                    OR _map_flow_pool_name LIKE '%孟帝数学%'
                                  )
                                  AND _map_period_name NOT LIKE '%多学科拓展%'
                                  AND _map_channel_name_2 NOT LIKE '%KOL%'
                                  AND _map_third_department_name = '直播部'
                                  AND _map_channel_name_2 NOT LIKE '%百度%'
                                  THEN '孟亚飞99-1组'
                                  WHEN (
                                    _map_flow_pool_name LIKE '%孟帝%'
                                    OR _map_flow_pool_name LIKE '%孟老师%'
                                    OR _map_flow_pool_name LIKE '%中考数学冲刺%'
                                    OR _map_flow_pool_name LIKE '%8升9数学%'
                                    OR _map_flow_pool_name LIKE '%孟亚飞讲数学%'
                                    OR _map_flow_pool_name LIKE '%中考冲刺%'
                                    OR _map_flow_pool_name LIKE '%中考满分冲刺%'
                                    OR _map_flow_pool_name LIKE '%押题王孟亚飞%'
                                    OR _map_flow_pool_name LIKE '%中考数学大通关%'
                                    OR _map_flow_pool_name LIKE '%中考数学规划%'
                                    OR _map_flow_pool_name LIKE '%亚飞数学%'
                                  )
                                  AND _map_period_name NOT LIKE '%多学科拓展%'
                                  AND _map_channel_name_2 NOT LIKE '%KOL%'
                                  AND _map_third_department_name = '直播部'
                                  AND _map_channel_name_2 = '百度'
                                  THEN '孟亚飞-1组-百度'
                                  WHEN _map_put_plan_name LIKE '%刘家晋讲图文%'
                                  OR _map_put_plan_name LIKE '%孟帝数学%'
                                  AND _map_third_department_name = '直播部'
                                  THEN '孟亚飞9元'
                                  WHEN _map_flow_pool_name LIKE '%汐子%'
                                  AND _map_period_name NOT LIKE '%多学科拓展%'
                                  AND _map_sku_id_name LIKE '%亚飞%'
                                  AND _map_third_department_name = '直播部'
                                  AND _map_rule_name LIKE '%99%'
                                  THEN '孟亚飞99-1组'
                                  WHEN (
                                    _map_flow_pool_name LIKE '%曹忆%'
                                    OR _map_flow_pool_name LIKE '%dudu%'
                                    OR _map_flow_pool_name LIKE '%中考决胜天团%'
                                    OR _map_flow_pool_name LIKE '%具象思维%'
                                    OR _map_flow_pool_name LIKE '%在逃发面馒头%'
                                    OR _map_flow_pool_name LIKE '%库洛米%'
                                    AND _map_lead_purchase_intention_level1_category_name <> '规划系统'
                                  )
                                  AND _map_period_name NOT LIKE '%多学科拓展%'
                                  AND _map_third_department_name IN ('直播部', '新媒体内容运营部')
                                  THEN '曹忆'
                                  WHEN (
                                    _map_first_department_name = '市场部'
                                    AND _map_channel_name_1 <> '站内获客'
                                    AND _map_channel_name_2 <> 'APP'
                                  )
                                  AND NOT COALESCE(
                                    (
                                      (
                                        _map_third_department_name = '私域运营部'
                                        AND _map_source_manager_name IN (
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
                                        _map_flow_pool_name LIKE '%南通欣创%'
                                        OR _map_flow_pool_name LIKE '%人人通科技%'
                                        OR _map_flow_pool_name LIKE '%易而购%'
                                        OR _map_flow_pool_name LIKE '%济南梦航%'
                                        OR _map_flow_pool_name LIKE '%晨硕智学%'
                                        OR _map_flow_pool_name LIKE '%兴尧文化%'
                                        OR _map_flow_pool_name LIKE '%济南映像%'
                                        OR _map_flow_pool_name LIKE '%山东简单%'
                                        OR _map_flow_pool_name LIKE '%争鸣科技%'
                                      )
                                      OR (
                                        (
                                          _map_flow_pool_name LIKE '%家校共育%'
                                          OR _map_flow_pool_name LIKE '%保持热爱%'
                                          OR _map_flow_pool_name LIKE '%青松%'
                                          OR _map_flow_pool_name LIKE '%悟之道%'
                                        )
                                        AND _map_put_plan_name NOT LIKE '%0元%'
                                      )
                                      OR (
                                        _map_source_manager_name = '李宁24' AND _map_put_plan_name LIKE '%0转低%'
                                      )
                                      OR (
                                        _map_third_department_name = '私域运营部'
                                        AND _map_flow_original_order_activity_price IN ('100.0', '900.0', '300.0')
                                      )
                                      OR (
                                        _map_third_department_name = '私域运营部'
                                        AND _map_flow_original_order_activity_price IN ('0.0')
                                        AND _map_source_manager_name IN ('陈雷19', '崔慧敏01', '侯佳林01', '郑天琪02', '杨彬屹', '曹义鹏', '王硕阳', '于超研')
                                      )
                                      OR (
                                        _map_flow_pool_name LIKE '公导私'
                                      )
                                      OR (
                                        _map_flow_pool_name LIKE '%0转低转正%' OR _map_channel_name_2 = '产研测试'
                                      )
                                    ),
                                    FALSE
                                  )
                                  THEN '集团私域'
                                  WHEN _map_flow_pool_name LIKE '%未加好友%'
                                  THEN '市场私域未加好友'
                                  WHEN _map_third_department_name = '私域运营部'
                                  AND _map_rule_name NOT LIKE '%训练营%'
                                  AND NOT _map_virtual_fifth_department_name IN ('罗江博团队')
                                  AND _map_rule_name NOT LIKE '%复用%'
                                  AND _map_rule_name NOT LIKE '%未加好友%'
                                  AND _map_channel_name_2 <> '内部换量'
                                  THEN '市场私域低价单'
                                  WHEN _map_third_department_name = '私域运营部'
                                  AND _map_rule_name NOT LIKE '%训练营%'
                                  AND _map_rule_name NOT LIKE '%复用%'
                                  AND _map_rule_name NOT LIKE '%未加好友%'
                                  AND _map_channel_name_2 <> '内部换量'
                                  AND _map_flow_original_order_activity_price = '0.0'
                                  THEN '市场私域低价单'
                                  WHEN _map_channel_name_2 IN ('APP', 'M站', 'PC')
                                  AND _map_flow_pool_name NOT LIKE '%途途%'
                                  THEN 'APP'
                                  WHEN _map_channel_name_2 IN ('小程序') AND _map_flow_pool_name LIKE '%高途体验课%'
                                  THEN 'APP'
                                  WHEN _map_channel_provider_name LIKE '%唐山TMK%'
                                  THEN '唐山TMK'
                                  WHEN _map_source_manager_name IN ('高文羽')
                                  AND _map_channel_provider_name NOT LIKE '%唐山TMK%'
                                  AND _map_channel_provider_name NOT LIKE '%郑州%'
                                  THEN '人工外呼'
                                  WHEN _map_source_manager_name = '冯银晨' AND _map_channel_name_2 = '小红书'
                                  THEN '信息流-小红书'
                                  WHEN _map_channel_name_1 = '信息流'
                                  AND _map_channel_name_2 = 'B站'
                                  AND _map_third_department_name NOT LIKE '%投放%'
                                  AND (
                                    _map_rule_name LIKE '%0904期-短期班-新高二-市场私域低价单%'
                                    OR _map_flow_original_order_activity_price = '100'
                                    OR _map_page_id_name LIKE '%1元%'
                                  )
                                  THEN 'B站信息流-朱汉祺-1元'
                                  WHEN _map_channel_name_1 = '信息流'
                                  AND _map_channel_name_2 = 'B站'
                                  AND _map_third_department_name NOT LIKE '%投放%'
                                  AND _map_page_id_name LIKE '%汤雪%'
                                  THEN 'B站信息流-汤学健'
                                  WHEN (
                                    _map_channel_name_1 = '信息流'
                                    AND _map_channel_name_2 <> 'B站'
                                    AND _map_third_department_name NOT LIKE '%商务%'
                                    AND _map_put_plan_name NOT LIKE '%初三0元%'
                                    AND _map_put_plan_name NOT LIKE '%抖音私信%'
                                    AND _map_put_plan_name NOT LIKE '%高中0元%'
                                    AND _map_flow_original_order_activity_price NOT LIKE '%1990%'
                                  )
                                  OR (
                                    _map_channel_name_2 = 'B站' AND _map_third_department_name LIKE '%投放%'
                                  )
                                  THEN '信息流'
                                  WHEN _map_channel_name_1 = '信息流'
                                  AND _map_channel_name_2 = 'B站'
                                  AND _map_third_department_name NOT LIKE '%投放%'
                                  AND (
                                    _map_page_id_name LIKE '%郭艺%'
                                  )
                                  THEN 'B站信息流-郭艺'
                                  WHEN _map_channel_name_1 = '信息流'
                                  AND _map_channel_name_2 = 'B站'
                                  AND _map_third_department_name NOT LIKE '%投放%'
                                  AND (
                                    _map_page_id_name LIKE '%朱博士%'
                                  )
                                  THEN 'B站信息流-朱汉祺'
                                  WHEN _map_channel_name_1 = '信息流'
                                  AND _map_channel_name_2 = 'B站'
                                  AND _map_third_department_name NOT LIKE '%投放%'
                                  AND _map_page_id_name LIKE '%肖晗%'
                                  THEN 'B站信息流'
                                  WHEN _map_channel_name_1 = '信息流'
                                  AND _map_channel_name_2 = 'B站'
                                  AND _map_third_department_name NOT LIKE '%投放%'
                                  AND (
                                    _map_page_id_name LIKE '%马凯鹏%' OR _map_ad_account_name LIKE '%化学%'
                                  )
                                  THEN 'B站信息流-马凯鹏'
                                  WHEN _map_channel_name_1 = '信息流'
                                  AND _map_channel_name_2 = 'B站'
                                  AND _map_third_department_name NOT LIKE '%投放%'
                                  AND (
                                    _map_sku_id_name LIKE '%陈瑞春%' OR _map_rule_name LIKE '%陈瑞春%'
                                  )
                                  AND (
                                    _map_ad_account_name LIKE '%语文%'
                                    OR _map_source_put_plan_name LIKE '%自然流%'
                                    OR _map_page_id_name LIKE '%春春%'
                                  )
                                  THEN 'B站信息流-陈瑞春'
                                  WHEN _map_channel_name_1 = '信息流'
                                  AND _map_channel_name_2 = 'B站'
                                  AND _map_third_department_name NOT LIKE '%投放%'
                                  AND (
                                    _map_flow_original_order_activity_price LIKE '%2990%'
                                    OR _map_sku_id_name LIKE '%帅师%'
                                    OR _map_sku_id_name LIKE '%周帅%'
                                  )
                                  AND _map_ad_account_name LIKE '%语文%'
                                  AND (
                                    _map_flow_original_order_activity_price LIKE '%1980%'
                                    OR _map_flow_original_order_activity_price LIKE '%2980%'
                                    OR _map_flow_original_order_activity_price LIKE '%2990%'
                                  )
                                  THEN 'B站信息流-陈瑞春'
                                  WHEN _map_channel_name_1 = '信息流'
                                  AND _map_channel_name_2 = 'B站'
                                  AND _map_third_department_name NOT LIKE '%投放%'
                                  AND (
                                    _map_flow_original_order_activity_price LIKE '%2990%'
                                    OR _map_sku_id_name LIKE '%帅师%'
                                    OR _map_sku_id_name LIKE '%周帅%'
                                  )
                                  AND _map_ad_account_name NOT LIKE '%语文%'
                                  THEN 'B站信息流-周帅'
                                  WHEN _map_channel_name_1 = '信息流'
                                  AND _map_channel_name_2 = 'B站'
                                  AND _map_third_department_name NOT LIKE '%投放%'
                                  AND _map_flow_order_price LIKE '%1980%'
                                  AND _map_ad_account_name LIKE '%数学%'
                                  THEN 'B站信息流-周帅'
                                  WHEN _map_channel_name_1 = '短直电商'
                                  AND _map_channel_name_2 = 'B站'
                                  AND _map_third_department_name LIKE '%商务%'
                                  AND (
                                    _map_flow_pool_name LIKE '%春春%' OR _map_sku_id_name LIKE '%陈瑞春%'
                                  )
                                  THEN 'B站信息流-陈瑞春'
                                END AS channel_map,
                                3 AS _mapping_priority
                            FROM data_raw
                            UNION ALL
                            SELECT
                                data_raw.*,
                                CASE
                                  WHEN _map_channel_name_1 = '短直电商'
                                  AND _map_channel_name_2 = 'B站'
                                  AND _map_third_department_name LIKE '%商务%'
                                  AND (
                                    _map_flow_pool_name LIKE '%朱博士%'
                                  )
                                  THEN 'B站信息流-朱汉祺'
                                  WHEN _map_channel_name_1 = '信息流'
                                  AND _map_channel_name_2 = 'B站'
                                  AND _map_third_department_name NOT LIKE '%投放%'
                                  AND _map_flow_original_order_activity_price NOT LIKE '%2980%'
                                  AND _map_flow_original_order_activity_price NOT LIKE '%2990%'
                                  AND _map_flow_original_order_activity_price NOT LIKE '%1980%'
                                  THEN 'B站信息流'
                                  WHEN _map_flow_pool_name = '百度搜索引擎' OR _map_channel_name_1 = '搜索营销'
                                  THEN '信息流搜索'
                                  WHEN _map_flow_pool_name LIKE '%小红书班课%'
                                  THEN '小红书投放'
                                  WHEN _map_third_department_name = '投放部'
                                  AND _map_get_customer_way_name = '短视频信息流'
                                  AND _map_flow_original_order_activity_price LIKE '%100%'
                                  THEN '信息流'
                                  WHEN _map_put_plan_name LIKE '%福哥私域0元%'
                                  THEN 'KOC-下引'
                                  WHEN _map_put_plan_name LIKE '%福哥私域5元%'
                                  THEN 'KOC-下引5元'
                                  WHEN _map_flow_pool_name = '中考加油' AND _map_sku_id_name LIKE '%孟帝%'
                                  THEN 'KOC-孟亚飞数学'
                                  WHEN _map_flow_pool_name = '中考加油' AND _map_sku_id_name LIKE '%帅师%'
                                  THEN 'KOC-周帅数学'
                                  WHEN _map_source_manager_name IN ('孙晗01', '方俊结01', '刘亦鹏02', '何木玲', '杨梓月', '张可意03', '任颖迪', '曹蕊07', '曲默晗')
                                  AND (
                                    _map_sku_id_name LIKE '%孟帝%'
                                    OR _map_sku_id_name LIKE '%dudu%'
                                    OR _map_sku_id_name LIKE '%市场初二%'
                                    OR _map_rule_name LIKE '%亚飞%'
                                    OR _map_sku_id_name LIKE '%初二高阳%'
                                    OR _map_sku_id_name LIKE '%高阳初二%'
                                    OR _map_sku_id_name LIKE '%精品初二%'
                                    OR _map_rule_name LIKE '%初二%'
                                    OR _map_sku_id_name LIKE '%菁英初三%'
                                    OR (
                                      _map_virtual_second_department_name = '菁英班学部'
                                      AND _map_lead_purchase_intention_level2_category_name = '初级'
                                      AND _map_lead_create_time >= '2026-04-15 00:00:00'
                                    )
                                  )
                                  THEN 'KOC-孟亚飞数学'
                                  WHEN _map_source_manager_name IN ('孙晗01', '方俊结01', '刘亦鹏02', '何木玲', '杨梓月', '张可意03', '任颖迪', '曹蕊07', '曲默晗')
                                  AND (
                                    _map_sku_id_name LIKE '%帅师%'
                                    OR _map_rule_name LIKE '%周帅%'
                                    OR _map_sku_id_name LIKE '%9月升高三%'
                                    OR _map_sku_id_name LIKE '%新高二%'
                                  )
                                  THEN 'KOC-周帅数学'
                                  WHEN _map_source_manager_name IN ('孙晗01', '方俊结01', '刘亦鹏02', '何木玲', '杨梓月', '张可意03', '任颖迪', '曹蕊07', '曲默晗')
                                  AND (
                                    _map_sku_id_name LIKE '%肖晗%' OR _map_rule_name LIKE '%肖晗%'
                                  )
                                  THEN 'KOC-肖晗'
                                  WHEN _map_source_manager_name IN ('孙晗01', '方俊结01', '刘亦鹏02', '何木玲', '杨梓月', '张可意03', '任颖迪', '曹蕊07', '曲默晗')
                                  AND _map_period_name NOT LIKE '%多学科拓展%'
                                  AND _map_sku_id_name NOT LIKE '%朱汉祺%'
                                  AND _map_sku_id_name NOT LIKE '%朱博士%'
                                  AND _map_sku_id_name NOT LIKE '%周帅%'
                                  AND _map_sku_id_name NOT LIKE '%29元%'
                                  THEN 'KOC-5元纯课'
                                  WHEN _map_source_manager_name IN ('孙晗01', '方俊结01', '刘亦鹏02', '何木玲', '杨梓月', '张可意03', '任颖迪', '曹蕊07', '曲默晗')
                                  AND _map_sku_id_name LIKE '%周帅%'
                                  THEN 'KOC-周帅'
                                  WHEN _map_third_department_name IN ('品牌效能部', 'KOC孵化部')
                                  AND _map_channel_name_2 IN ('抖音', '视频号', '快手', 'KOL')
                                  THEN '自孵化KOC-5元纯课'
                                  WHEN _map_third_department_name IN ('品牌效能部', 'KOC孵化部')
                                  AND _map_channel_name_2 IN ('抖音', '视频号', '快手', 'KOL')
                                  AND (
                                    _map_sku_id_name LIKE '%5元%'
                                    OR _map_sku_id_name LIKE '%11元%'
                                    OR _map_flow_original_order_activity_price LIKE '%1100%'
                                    OR _map_flow_original_order_activity_price LIKE '%500%'
                                    OR _map_flow_orders_income_amount LIKE '%1100%'
                                    OR _map_flow_orders_income_amount LIKE '%500%'
                                  )
                                  THEN '自孵化KOC-5元纯课'
                                  WHEN _map_source_manager_name IN (
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
                                  AND _map_channel_name_2 LIKE '%社群%'
                                  THEN '进校社群'
                                  WHEN _map_source_manager_name IN (
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
                                    _map_channel_name_2 LIKE '%直推%'
                                    OR (
                                      _map_put_plan_name LIKE '%良师益友%' OR _map_put_plan_name LIKE '%弘诚1元%'
                                    )
                                  )
                                  THEN '进校直推'
                                  WHEN _map_source_manager_name IN (
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
                                  AND _map_channel_name_2 LIKE '%TMK%'
                                  AND (
                                    _map_page_id_name LIKE '%1元%' OR _map_channel_provider_name LIKE '%禾顺云%'
                                  )
                                  THEN '进校TMK1元'
                                  WHEN _map_source_manager_name IN (
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
                                  AND _map_channel_name_2 LIKE '%TMK%'
                                  AND _map_page_id_name LIKE '%9元%'
                                  THEN '进校TMK9元'
                                  WHEN _map_source_manager_name IN (
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
                                  AND _map_channel_name_2 LIKE '%书商%'
                                  THEN '进校书商'
                                  WHEN _map_source_manager_name IN (
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
                                  AND _map_channel_name_2 LIKE '%综合%'
                                  AND _map_put_plan_name LIKE '%18%'
                                  THEN '进校直播'
                                  WHEN _map_source_manager_name IN (
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
                                  AND _map_channel_name_2 LIKE '%直播%'
                                  THEN '进校直播'
                                  WHEN _map_source_manager_name IN (
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
                                  AND _map_put_plan_name NOT LIKE '%0元%'
                                  AND _map_flow_pool_name NOT LIKE '%家校共育%'
                                  AND _map_flow_pool_name NOT LIKE '%保持热爱%'
                                  AND _map_flow_pool_name NOT LIKE '%青松%'
                                  AND _map_flow_pool_name NOT LIKE '%原子初三%'
                                  AND _map_flow_pool_name NOT LIKE '%南通欣创%'
                                  AND _map_flow_pool_name NOT LIKE '%悟之道%'
                                  AND _map_flow_pool_name NOT LIKE '%济南梦航%'
                                  AND _map_channel_name_3 <> '社群'
                                  AND _map_put_plan_name NOT LIKE '%善悟%'
                                  AND _map_put_plan_name NOT LIKE '%人人通%'
                                  AND _map_put_plan_name NOT LIKE '%%济南格乐'
                                  AND _map_flow_pool_name NOT LIKE '%晨硕智学%'
                                  AND _map_flow_pool_name NOT LIKE '%兴尧文化%'
                                  AND _map_flow_pool_name NOT LIKE '%济南映像%'
                                  AND _map_flow_pool_name NOT LIKE '%山东简单%'
                                  AND _map_flow_pool_name NOT LIKE '%争鸣科技%'
                                  THEN '商务低价'
                                  WHEN _map_flow_pool_name LIKE '%南通欣创%'
                                  OR _map_flow_pool_name LIKE '%人人通科技%'
                                  OR _map_flow_pool_name LIKE '%易而购%'
                                  OR _map_flow_pool_name LIKE '%济南梦航%'
                                  OR _map_flow_pool_name LIKE '%晨硕智学%'
                                  OR _map_flow_pool_name LIKE '%兴尧文化%'
                                  OR _map_flow_pool_name LIKE '%济南映像%'
                                  OR _map_flow_pool_name LIKE '%山东简单%'
                                  OR _map_flow_pool_name LIKE '%争鸣科技%'
                                  THEN '进校私域合作'
                                  WHEN (
                                    _map_flow_pool_name LIKE '%家校共育%'
                                    OR _map_flow_pool_name LIKE '%保持热爱%'
                                    OR _map_flow_pool_name LIKE '%青松%'
                                    OR _map_flow_pool_name LIKE '%悟之道%'
                                  )
                                  AND _map_put_plan_name NOT LIKE '%0元%'
                                  THEN '进校私域合作'
                                  WHEN _map_source_manager_name = '李宁24' AND _map_put_plan_name LIKE '%0转低%'
                                  THEN '进校私域合作'
                                  WHEN _map_third_department_name = '私域运营部'
                                  AND _map_flow_original_order_activity_price IN ('100.0', '900.0', '300.0')
                                  THEN '进校私域合作'
                                  WHEN _map_third_department_name = '私域运营部'
                                  AND _map_flow_original_order_activity_price IN ('0.0')
                                  AND _map_source_manager_name IN ('陈雷19', '崔慧敏01', '侯佳林01', '郑天琪02', '杨彬屹', '曹义鹏', '王硕阳', '于超研')
                                  THEN '进校私域合作'
                                  WHEN _map_third_department_name = '私域运营部'
                                  AND _map_channel_name_1 = '市场私域'
                                  AND _map_put_plan_name NOT LIKE '%公导私%'
                                  AND _map_put_plan_name NOT LIKE '%公转私%'
                                  AND _map_flow_original_order_activity_price = '0.0'
                                  AND _map_rule_name NOT LIKE '%激活%'
                                  AND _map_rule_name NOT LIKE '%咨询%'
                                  AND _map_rule_name NOT LIKE '%训练营%'
                                  AND _map_virtual_fifth_department_name NOT LIKE '%罗江博%'
                                  AND _map_virtual_fifth_department_name NOT LIKE '%郑州学习顾问二部%'
                                  AND NOT _map_source_manager_name IN ('陈雷19', '崔慧敏01', '侯佳林01', '郑天琪02', '杨彬屹', '曹义鹏', '王硕阳', '于超研')
                                  THEN '市场私域低价单'
                                  WHEN _map_source_manager_name IN ('耿文超', '晋翠翠', '赵语诗', '王慧敏13', '于新茹', '梁超01', '刘晓20', '王玉120', '吕佳乐01')
                                  AND _map_channel_provider_name LIKE '%格乐教育%'
                                  AND _map_channel_name_2 LIKE '%直播%'
                                  THEN '创新社群'
                                  WHEN _map_source_manager_name IN ('耿文超', '晋翠翠', '赵语诗', '王慧敏13', '于新茹', '梁超01', '刘晓20', '王玉120', '吕佳乐01')
                                  AND _map_channel_name_2 LIKE '%社群%'
                                  THEN '创新社群'
                                  WHEN _map_source_manager_name IN ('耿文超', '晋翠翠', '赵语诗', '王慧敏13', '于新茹', '梁超01', '刘晓20', '王玉120', '吕佳乐01')
                                  AND (
                                    _map_channel_name_2 LIKE '%直推%' OR _map_put_plan_name LIKE '%直推%'
                                  )
                                  THEN '创新直推'
                                  WHEN _map_source_manager_name IN ('耿文超', '晋翠翠', '赵语诗', '王慧敏13', '于新茹', '梁超01', '刘晓20', '王玉120', '吕佳乐01')
                                  AND (
                                    _map_channel_name_2 LIKE '%书商%'
                                    OR _map_put_plan_name LIKE '%书商%'
                                    OR _map_page_id_name LIKE '%书商%'
                                  )
                                  THEN '创新书商'
                                  WHEN _map_source_manager_name IN ('耿文超', '晋翠翠', '赵语诗', '王慧敏13', '于新茹', '梁超01', '刘晓20', '王玉120', '吕佳乐01')
                                  AND _map_channel_name_2 LIKE '%TMK%'
                                  AND _map_page_id_name LIKE '%1元%'
                                  THEN '创新TMK1元'
                                  WHEN _map_source_manager_name IN ('耿文超', '晋翠翠', '赵语诗', '王慧敏13', '于新茹', '梁超01', '刘晓20', '王玉120', '吕佳乐01')
                                  AND _map_channel_name_2 LIKE '%TMK%'
                                  AND _map_page_id_name LIKE '%9元%'
                                  THEN '创新TMK9元'
                                  WHEN _map_source_manager_name IN ('耿文超', '晋翠翠', '赵语诗', '王慧敏13', '于新茹', '梁超01', '刘晓20', '王玉120', '吕佳乐01')
                                  AND (
                                    _map_channel_name_2 LIKE '%直播%' OR _map_page_id_name LIKE '%进校%'
                                  )
                                  THEN '创新直播'
                                  WHEN _map_source_manager_name IN ('耿文超', '晋翠翠', '赵语诗', '王慧敏13', '于新茹', '梁超01', '刘晓20', '王玉120', '吕佳乐01')
                                  AND _map_channel_name_2 <> '公众号'
                                  AND _map_channel_name_1 = '商务'
                                  AND _map_flow_pool_name <> '高途云集图书专营店-自然流'
                                  AND _map_flow_pool_name <> '高途旗舰店—线索—yuxinru'
                                  AND _map_put_plan_name NOT LIKE '%社群%'
                                  AND _map_put_plan_name NOT LIKE '%小红书班课%'
                                  AND _map_put_plan_name NOT LIKE '%外部图书供量%'
                                  AND _map_channel_second_provider_name NOT LIKE '%沃德丰店铺线索赠课%'
                                  AND _map_channel_second_provider_name NOT LIKE '%智慧城-图书%'
                                  AND _map_put_plan_name NOT LIKE '%育甲%'
                                  AND _map_flow_pool_name NOT LIKE '%周长磊%'
                                  THEN '创新商务'
                                  WHEN _map_source_manager_name IN ('高曼曼01', '杨思怡', '宋向函')
                                  THEN '图书KOC达人'
                                  WHEN _map_flow_pool_name LIKE '%市场部-微信私域%'
                                  OR _map_flow_pool_name LIKE '%市场部-规划报告%'
                                  OR _map_flow_pool_name LIKE '%规划报告%'
                                  OR _map_flow_pool_name LIKE '%市场部-小红书%'
                                  OR _map_flow_pool_name LIKE '%孟浩宇%'
                                  THEN '市场私域低价单'
                                END AS channel_map,
                                4 AS _mapping_priority
                            FROM data_raw
                            UNION ALL
                            SELECT
                                data_raw.*,
                                CASE
                                  WHEN _map_flow_pool_name LIKE '公导私'
                                  THEN '进校私域合作'
                                  WHEN (
                                    (
                                      _map_flow_pool_name LIKE '%增长组%'
                                      OR _map_channel_name_3 = '公众号'
                                      OR _map_second_department_name = '微信生态部'
                                    )
                                    AND _map_channel_name_2 <> 'APP'
                                  )
                                  AND NOT COALESCE(
                                    (
                                      (
                                        _map_third_department_name = '私域运营部'
                                        AND _map_source_manager_name IN (
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
                                        _map_flow_pool_name LIKE '%南通欣创%'
                                        OR _map_flow_pool_name LIKE '%人人通科技%'
                                        OR _map_flow_pool_name LIKE '%易而购%'
                                        OR _map_flow_pool_name LIKE '%济南梦航%'
                                        OR _map_flow_pool_name LIKE '%晨硕智学%'
                                        OR _map_flow_pool_name LIKE '%兴尧文化%'
                                        OR _map_flow_pool_name LIKE '%济南映像%'
                                        OR _map_flow_pool_name LIKE '%山东简单%'
                                        OR _map_flow_pool_name LIKE '%争鸣科技%'
                                      )
                                      OR (
                                        (
                                          _map_flow_pool_name LIKE '%家校共育%'
                                          OR _map_flow_pool_name LIKE '%保持热爱%'
                                          OR _map_flow_pool_name LIKE '%青松%'
                                          OR _map_flow_pool_name LIKE '%悟之道%'
                                        )
                                        AND _map_put_plan_name NOT LIKE '%0元%'
                                      )
                                      OR (
                                        _map_source_manager_name = '李宁24' AND _map_put_plan_name LIKE '%0转低%'
                                      )
                                      OR (
                                        _map_third_department_name = '私域运营部'
                                        AND _map_flow_original_order_activity_price IN ('100.0', '900.0', '300.0')
                                      )
                                      OR (
                                        _map_third_department_name = '私域运营部'
                                        AND _map_flow_original_order_activity_price IN ('0.0')
                                        AND _map_source_manager_name IN ('陈雷19', '崔慧敏01', '侯佳林01', '郑天琪02', '杨彬屹', '曹义鹏', '王硕阳', '于超研')
                                      )
                                      OR (
                                        _map_flow_pool_name LIKE '公导私'
                                      )
                                      OR (
                                        _map_flow_pool_name LIKE '%0转低转正%' OR _map_channel_name_2 = '产研测试'
                                      )
                                    ),
                                    FALSE
                                  )
                                  THEN '集团私域'
                                  WHEN _map_put_plan_name LIKE '%星耀%'
                                  OR _map_put_plan_name LIKE '%物理展博%'
                                  OR _map_put_plan_name LIKE '%物理谢丽荣%'
                                  OR _map_put_plan_name LIKE '%牟恩伯%'
                                  OR _map_put_plan_name LIKE '%王赞%'
                                  OR _map_put_plan_name LIKE '%张磊老师高中数学%'
                                  OR _map_put_plan_name LIKE '%雯姐高中物理大讲堂%'
                                  THEN '百度星耀'
                                  WHEN _map_source_manager_name = '刘福云'
                                  AND (
                                    _map_sku_id_name LIKE '%瑞春%' OR _map_sku_id_name LIKE '%春春%'
                                  )
                                  THEN '陈瑞春'
                                  WHEN _map_third_department_name = '直播部'
                                  AND _map_sku_id_name LIKE '%周帅%'
                                  AND _map_channel_name_2 IN ('百度', 'B站')
                                  THEN '周帅'
                                  WHEN _map_third_department_name = '直播部'
                                  AND _map_sku_id_name LIKE '%孟亚飞%'
                                  AND _map_rule_name LIKE '%99%'
                                  THEN '孟亚飞99-1组'
                                  WHEN _map_third_department_name = '直播部' AND _map_sku_id_name LIKE '%朱汉祺%'
                                  THEN '朱博士99'
                                  WHEN _map_flow_pool_name LIKE '%0转低转正%' OR _map_channel_name_2 = '产研测试'
                                  THEN '进校私域合作'
                                  WHEN _map_flow_pool_name LIKE '%天津智慧双子%'
                                  THEN '创新社群'
                                  WHEN _map_third_department_name LIKE '%城市定制%'
                                  THEN '点睛卷'
                                  WHEN _map_period_name LIKE '%多学科拓展%' AND _map_third_department_name LIKE '%私域运营%'
                                  THEN '市场私域入群'
                                  WHEN _map_put_plan_name LIKE '%赠课失败%' AND _map_third_department_name = '线上商务部'
                                  THEN 'KOC赠课失败'
                                  WHEN _map_flow_pool_name LIKE '%自然流%'
                                  AND _map_source_manager_name IN ('孙晗01', '方俊结01', '刘亦鹏02', '何木玲', '杨梓月', '张可意03', '任颖迪', '曹蕊07', '曲默晗')
                                  AND _map_sku_id_name LIKE '%周帅%'
                                  THEN 'KOC-周帅'
                                  WHEN _map_flow_pool_name LIKE '%自然流%'
                                  AND _map_source_manager_name IN ('孙晗01', '方俊结01', '刘亦鹏02', '何木玲', '杨梓月', '张可意03', '任颖迪', '曹蕊07', '曲默晗')
                                  AND _map_sku_id_name LIKE '%肖晗%'
                                  THEN 'KOC-肖晗'
                                  WHEN _map_flow_pool_name LIKE '%自然流%'
                                  AND _map_source_manager_name IN ('孙晗01', '方俊结01', '刘亦鹏02', '何木玲', '杨梓月', '张可意03', '任颖迪', '曹蕊07', '曲默晗')
                                  AND _map_sku_id_name LIKE '%朱汉祺%'
                                  AND _map_flow_original_order_activity_price LIKE '%1100%'
                                  THEN 'KOC-5元朱汉祺'
                                  WHEN _map_flow_pool_name LIKE '%自然流%'
                                  AND _map_source_manager_name IN ('赵语诗', '崔文轩', '孙培尧')
                                  THEN '自孵化KOC-5元纯课'
                                  WHEN _map_flow_pool_name LIKE '%自然流%'
                                  AND (
                                    _map_sku_id_name LIKE '%朱博士%' OR _map_sku_id_name LIKE '%朱汉祺%'
                                  )
                                  AND _map_rule_name LIKE '%9%'
                                  AND _map_rule_name NOT LIKE '%29%'
                                  AND _map_third_department_name IN ('直播部', '新媒体内容运营部', '市场一组')
                                  THEN '朱博士99'
                                  WHEN _map_flow_pool_name LIKE '%自然流%'
                                  AND _map_sku_id_name LIKE '%朱博士%'
                                  AND _map_third_department_name IN ('直播部', '新媒体内容运营部', '市场一组')
                                  THEN '朱博士99'
                                  WHEN _map_flow_pool_name LIKE '%自然流%'
                                  AND _map_sku_id_name LIKE '%亚飞%'
                                  AND _map_rule_name LIKE '%99%'
                                  AND _map_third_department_name IN ('直播部', '新媒体内容运营部', '市场一组')
                                  THEN '孟亚飞99-1组'
                                  WHEN _map_flow_pool_name LIKE '%自然流%'
                                  AND _map_sku_id_name LIKE '%亚飞%'
                                  AND _map_third_department_name IN ('直播部', '新媒体内容运营部', '市场一组')
                                  THEN '孟亚飞9元'
                                  WHEN _map_flow_pool_name LIKE '%自然流%' AND _map_sku_id_name LIKE '%曹忆%'
                                  THEN '曹忆'
                                  WHEN _map_flow_pool_name LIKE '%自然流%'
                                  AND _map_rule_name LIKE '%朱博士%'
                                  AND _map_third_department_name IN ('直播部', '新媒体内容运营部', '市场一组')
                                  THEN '朱博士99'
                                  WHEN _map_flow_pool_name LIKE '%自然流%'
                                  AND _map_source_manager_name LIKE '%邵万昕%'
                                  AND _map_third_department_name IN ('直播部', '新媒体内容运营部', '市场一组')
                                  THEN '朱博士99'
                                  WHEN _map_flow_pool_name LIKE '%自然流%'
                                  AND _map_rule_name LIKE '%亚飞%'
                                  AND _map_rule_name LIKE '%99%'
                                  THEN '孟亚飞99-1组'
                                  WHEN _map_flow_pool_name LIKE '%自然流%' AND _map_rule_name LIKE '%亚飞%'
                                  THEN '孟亚飞9元'
                                  WHEN _map_flow_pool_name LIKE '%自然流%' AND _map_rule_name LIKE '%郭艺%'
                                  THEN '郭艺'
                                  WHEN _map_flow_pool_name LIKE '%自然流%' AND _map_rule_name LIKE '%汤雪%'
                                  THEN '汤老师'
                                  WHEN _map_flow_pool_name LIKE '%自然流%' AND _map_rule_name LIKE '%曹忆%'
                                  THEN '曹忆'
                                  WHEN _map_flow_pool_name LIKE '%途途教室%' OR _map_first_department_name LIKE 'TUTU'
                                  THEN '途途APP'
                                  WHEN _map_source_manager_name IN ('宋莹莹', '辛世如') AND _map_channel_name_2 IN ('视频号')
                                  THEN '信息流-虚拟号挂车'
                                  WHEN _map_rule_name LIKE '%训练营%' AND _map_rule_name LIKE '%市场私域%'
                                  THEN '市场私域入群'
                                  WHEN _map_channel_name_1 = '信息流'
                                  AND (
                                    _map_put_plan_name LIKE '%抖音私信%'
                                    OR _map_put_plan_name LIKE '%初三0元%'
                                    OR _map_put_plan_name LIKE '%高中0元%'
                                  )
                                  THEN '信息流-抖音私信'
                                  WHEN _map_rule_name LIKE '%途途私域%'
                                  OR (
                                    _map_rule_name LIKE '%私域%' AND _map_first_department_name = 'TT'
                                  )
                                  THEN '途途私域'
                                  ELSE '其他未知流量'
                                END AS channel_map,
                                5 AS _mapping_priority
                            FROM data_raw
                        ),
                        channel_ranked AS (
                            SELECT
                                channel_union.*,
                                row_number() OVER (
                                    PARTITION BY _mapping_row_id
                                    ORDER BY _mapping_priority
                                ) AS _mapping_rank
                            FROM channel_union
                            WHERE channel_map IS NOT NULL
                        ),
                        data AS (
                            SELECT DISTINCT
                                period_name,
                                depart_1,
                                depart,
                                jingli,
                                zhuguan,
                                employee_email_name,
                                employee_email_prefix,
                                lead_id,
                                user_id,
                                channel_map,
                                lead_purchase_intention_name,
                                grade_1,
                                lead_count,
                                valid_lead_count,
                                conversion_lead_count,
                                subject_count,
                                same_lead_period_subject_count,
                                lb_subject_count,
                                same_lead_period_lb_subject_count,
                                order_count,
                                income_amount,
                                in_pay_period_refund_amount,
                                non_pay_period_refund_amount,
                                jp_cross_department_refund_amount,
                                same_lead_period_order_count,
                                same_lead_period_conversion_lead_count,
                                same_lead_period_income_amount,
                                same_lead_period_refund_amount,
                                is_friend_lead,
                                non_friend_lead,
                                is_shengou,
                                AB_intention_level,
                                AB_zhuanhua
                            FROM channel_ranked
                            WHERE _mapping_rank = 1
                        )
                        ---------------------------------首节到课
,
                        daoke as (
                                select
                                        date_format(date_add('day', 4, date_trunc('week', cast(begin_time as date))), '%Y%m%d') || '期' as period_name,
                                        user_number as user_id,
                                        case
                                                when max(
                                                        case
                                                                when coalesce(learn_duration, 0) / 60 > 60 then 1
                                                                else 0
                                                        end
                                                ) > 0 then 1
                                                else 0
                                        end as daoke
                                from
                                        service_dw.dws_service_user_learn_detail_hf
                                where
                                        dt = date_format(now() - interval '2' hour, '%Y%m%d')
                                        and hour = date_format(now() - interval '2' hour, '%H')
                                        and course_first_level_department_name = 'H业务线'
                                        and course_second_level_department_name in ('精品班学部', '市场部', '青橙项目部')
                                        and is_need_attend = 1
                                group by
                                        date_format(date_add('day', 4, date_trunc('week', cast(begin_time as date))), '%Y%m%d') || '期',
                                        user_number
                        )
                        -----------------------整合 
,
                        base as (
                                select
                                        data.*,
                                        case
                                                when is_friend_lead = '1'
                                                and conversion_lead_count = '0'
                                                and coalesce(daoke, 0) = 1 then 1
                                                else 0
                                        end as B_type,
                                        case
                                                when non_friend_lead = '1'
                                                and conversion_lead_count = '0'
                                                and coalesce(daoke, 0) = 0 then 1
                                                else 0
                                        end as D_type
                                from
                                        data
                                        left join daoke on daoke.period_name = data.period_name
                                        and daoke.user_id = data.user_id
                        )
                select
                        *
                from
                        base
                where
                        period_name >= ${period_name1}
                        and B_type = '1'
        ) as templateTable
