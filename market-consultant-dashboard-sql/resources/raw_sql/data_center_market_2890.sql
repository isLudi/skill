WITH biz_qici_calendar AS (
    select *
    from (
        values
            ('market_consultant', 'lead_period', '20260716期', date '2026-07-14', date '2026-07-19', 1),
            ('market_consultant', 'class_period', '20260716期', date '2026-07-14', date '2026-07-19', 1),
            ('market_consultant', 'trade_period', '20260716期', date '2026-07-14', date '2026-07-19', 1),
            ('market_consultant', 'lead_period', '20260722期', date '2026-07-20', date '2026-07-25', 1),
            ('market_consultant', 'class_period', '20260722期', date '2026-07-20', date '2026-07-25', 1),
            ('market_consultant', 'trade_period', '20260722期', date '2026-07-20', date '2026-07-25', 1),
            ('market_consultant', 'lead_period', '20260728期', date '2026-07-26', date '2026-07-31', 1),
            ('market_consultant', 'class_period', '20260728期', date '2026-07-26', date '2026-07-31', 1),
            ('market_consultant', 'trade_period', '20260728期', date '2026-07-26', date '2026-07-31', 1),
            ('market_consultant', 'lead_period', '20260803期', date '2026-08-01', date '2026-08-06', 1),
            ('market_consultant', 'class_period', '20260803期', date '2026-08-01', date '2026-08-06', 1),
            ('market_consultant', 'trade_period', '20260803期', date '2026-08-01', date '2026-08-06', 1),
            ('market_consultant', 'lead_period', '20260809期', date '2026-08-07', date '2026-08-12', 1),
            ('market_consultant', 'class_period', '20260809期', date '2026-08-07', date '2026-08-12', 1),
            ('market_consultant', 'trade_period', '20260809期', date '2026-08-07', date '2026-08-12', 1)
    ) as t(business_domain, date_role, qici, period_start_date, period_end_date, enabled)
),
lead_raw AS (
    SELECT DISTINCT
        coalesce(
            lead_cal.qici,
            concat(
                date_format(
                    date_trunc(
                        'week',
                        date_parse(replace(concat(t1.group_period_year, t1.group_period_term), '期', ''), '%Y%m%d') - interval '1' day
                    ) + interval '4' day,
                    '%Y%m%d'
                ),
                '期'
            )
        ) as period_name,
        t1.lead_id, t1.user_id, t1.rule_name,
        t1.lead_purchase_intention_level2_category_name,
        t1.employee_email_name, t1.employee_email_prefix,
        t1.virtual_third_department_name,
        t1.virtual_fourth_department_name,
        t1.virtual_fifth_department_name,
        t1.virtual_second_department_name,
        t1.section_assign_employee_second_level_department_name,
        t1.virtual_leader_email_name,
        t1.virtual_direct_leader_email_name,
        t1.flow_pool_name, t1.third_department_name,
        t1.second_department_name, t1.first_department_name,
        t1.sku_id_name, t1.ad_account_name, t1.source_manager_name,
        t1.channel_name_1, t1.channel_name_2, t1.channel_name_3,
        t1.put_plan_name, t1.channel_provider_name,
        t1.channel_second_provider_name, t1.page_id_name,
        t1.source_put_plan_name, t1.get_customer_way_name,
        t1.lead_purchase_intention_name,
        t1.lead_purchase_intention_level1_category_name,
        t1.lead_create_time,
        cast(t1.flow_original_order_activity_price AS varchar) AS flow_original_order_activity_price,
        cast(t1.flow_order_price AS varchar) AS flow_order_price,
        cast(t1.flow_orders_income_amount AS varchar) AS flow_orders_income_amount,
        coalesce(t1.lead_count, 0) AS lead_count,
        coalesce(t1.valid_lead_count, 0) AS valid_lead_count,
        coalesce(t1.conversion_lead_count, 0) AS conversion_lead_count,
        coalesce(t1.subject_count, 0) AS subject_count,
        coalesce(t1.order_count, 0) AS order_count,
        coalesce(t1.income_amount, 0) AS income_amount,
        coalesce(t1.in_pay_period_refund_amount, 0) AS in_pay_period_refund_amount,
        coalesce(t1.non_pay_period_refund_amount, 0) AS non_pay_period_refund_amount,
        coalesce(t1.same_lead_period_income_amount, 0) AS same_lead_period_income_amount,
        coalesce(t1.same_lead_period_refund_amount, 0) AS same_lead_period_refund_amount,
        coalesce(t1.same_lead_period_conversion_lead_count, 0) AS same_lead_period_conversion_lead_count
    FROM bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df t1
    left join biz_qici_calendar lead_cal
      on lead_cal.business_domain = 'market_consultant'
     and lead_cal.date_role = 'lead_period'
     and cast(date_parse(replace(concat(t1.group_period_year, t1.group_period_term), '期', ''), '%Y%m%d') as date)
         between lead_cal.period_start_date and lead_cal.period_end_date
     and lead_cal.enabled = 1
    WHERE t1.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
      AND t1.hour = format_datetime(now() - interval '3' hour, 'HH')
      AND t1.section_assign_employee_first_level_department_name = 'H业务线'
      AND t1.section_assign_employee_second_level_department_name = '市场部'
      AND t1.section_assign_employee_third_level_department_name = '市场顾问部'
      AND (t1.period_mapping_first_level_department_name = 'H业务线' OR t1.period_mapping_first_level_department_name IS NULL)
      AND (t1.period_mapping_second_level_department_name IN ('市场部','精品班学部') OR t1.period_mapping_second_level_department_name IS NULL)
),
lead_base AS (
    SELECT
        period_name, lead_id, user_id,
        employee_email_name, employee_email_prefix,
        virtual_leader_email_name AS jingli,
        virtual_direct_leader_email_name AS zhuguan,
        case
  when rule_name like '%北京直播江苏%' then '北京直播江苏'
  when get_customer_way_name in ('进校直推','线下渠道商') then '河南进校'
  when get_customer_way_name in ('平台自播') and flow_pool_name in ('赢战广东中考','高途专版图书','状元帮教辅') then '广东图书'
  when get_customer_way_name in ('平台自播') and flow_pool_name in ('途铭文化专版图书','途铭文化','博慧星辰文化图书','启迪蔚来','智慧航迹图书','高途浙江初中','高途浙江高中','高途浙江新高一') then '浙江图书'
  when get_customer_way_name in ('平台自播') and flow_pool_name in ('沪上名校','沪上领航社','简学文化','魔都校友助学馆','沪上领航高中','沪上领航初中') then '上海图书'
  when get_customer_way_name in ('平台自播') and flow_pool_name in ('高途江苏中考','高途赢战中考') then '江苏图书'
  when get_customer_way_name in ('平台自播') and flow_pool_name in ('京赋-浙江科学曹忆规划','为真-浙江科学曹忆老师','为真-浙江大科学曹忆老师','京赋-江苏曹忆老师规划','博学星辰初阶规划峥峥','博学星辰-曹忆老师浙江规划','京赋-浙江曹忆老师规划') then '曹忆'
  when third_department_name in ('中价产品项目部','新媒体内容运营部') and rule_name like '%曹忆%' then '曹忆'
  when third_department_name = '直播部' and sku_id_name like '%山东专版%' then '北京直播山东'
  when third_department_name = '直播部' and sku_id_name like '%河南专版%' then '北京直播河南'
  when third_department_name like '%锋途%' and channel_name_2 = '抖音' then '锋途KOC'
  when (flow_pool_name like '%江苏预习%' or  flow_pool_name like '%江苏专版预习%') and channel_name_2 ='抖音' then '西安直播江苏-抖音'
  when flow_pool_name like '%自然流%' and rule_name like '%江苏%' and third_department_name='图书营销部' and channel_name_2 ='抖音' then '西安直播江苏-抖音'
  when (flow_pool_name like '%江苏预习%' or  flow_pool_name like '%江苏专版预习%') and channel_name_2 ='视频号' then '西安直播江苏-视频号'
  when flow_pool_name like '%自然流%' and rule_name like '%江苏%' and third_department_name='图书营销部' and channel_name_2 ='视频号' then '西安直播江苏-视频号'
  when rule_name like '%北京图书%' and third_department_name='图书营销部' then '西安直播北京'
  when flow_pool_name like '%自然流%' and rule_name like '%北京%' and third_department_name='图书营销部' then '西安直播北京'
  when flow_pool_name IN ('高途学习规划','智辉老师讲规划') then '市场私域视频号'
  when rule_name LIKE '%语数英%' AND third_department_name = '新媒体内容运营部' then '语数英'
  when flow_pool_name LIKE '%星义大大%' then '赵星义'
  when third_department_name='图书营销部' AND (sku_id_name LIKE '%孟亚飞99%' OR sku_id_name LIKE '%亚飞%') then '孟亚飞99-2组'
  when third_department_name = '投放部' AND ad_account_name LIKE '%周帅%' then '信息流-周帅'
  when source_manager_name IN ('韩正卿') then '抖音私信'
  when third_department_name = '私域运营部' AND source_manager_name IN ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研','岳一帆02','田起帆','王绍阳') then '进校私域合作'
  when channel_name_1='市场私域' AND (virtual_fourth_department_name IN ('郑州学习顾问二部','郑州学习顾问七部','郑州训练营') OR virtual_fifth_department_name IN ('罗江博团队')) then '市场私域入群'
  when put_plan_name LIKE '%周司鹏%' then '品宣组KOC'
  when put_plan_name LIKE '%公导私%' AND put_plan_name LIKE '%未购课%' then '公导私报名失败'
  when third_department_name = '图书营销部' AND rule_name LIKE '%点睛卷%' then '押题卷'
  when put_plan_name LIKE '%迪九学%' then '市场私域代运营'
  when third_department_name = '投放部' AND channel_name_2 = '小红书' AND channel_name_1 <> '搜索营销' then '信息流-小红书'
  when third_department_name = '线上商务部' AND channel_name_2 = '小红书' then '小红书'
  when (flow_pool_name LIKE '%肖晗%' OR sku_id_name LIKE '%肖晗%' OR put_plan_name LIKE '%肖晗9元%') AND third_department_name='直播部' then '肖晗'
  when (flow_pool_name LIKE '%北大汤哥%' OR flow_pool_name LIKE '%海淀名师高阶%') AND sku_id_name LIKE '%小艺%' then '郭艺'
  when third_department_name LIKE '%私域%' AND rule_name LIKE '%私域%' AND rule_name LIKE '%图书%' then '市场私域图书'
  when third_department_name LIKE '%私域%' AND rule_name LIKE '%品效%' then '市场私域品效'
  when third_department_name LIKE '%私域%' AND rule_name LIKE '%公域学霸%' then '市场私域公域组'
  when third_department_name LIKE '%私域%' AND rule_name LIKE '%IE%' then '市场私域IE'
  when third_department_name LIKE '%私域%' AND rule_name LIKE '%裂变%' then '市场私域裂变'
  when third_department_name IN ('直播部','新媒体内容运营部','市场一组','私域运营部') AND put_plan_name LIKE '%退%' AND flow_pool_name ='电商退款用户池' then '退款订单复用'
  when third_department_name IN ('直播部','新媒体内容运营部','市场一组','私域运营部') AND put_plan_name LIKE '%失败%' AND flow_pool_name ='电商退款用户池' then '赠课失败'
  when third_department_name IN ('直播部','新媒体内容运营部','市场一组') AND (flow_pool_name ='初阶化学规划' OR flow_pool_name LIKE '%启迪-初阶老师%') then '曹忆'
  when (third_department_name = '图书营销部' AND sku_id_name LIKE '%真题%') OR (third_department_name='直播部' AND sku_id_name LIKE '%真题%') then '西安图书直播间-直播'
  when (third_department_name = '图书营销部' AND sku_id_name NOT LIKE '%真题%') OR (third_department_name='直播部' AND sku_id_name LIKE '%秒懂%') OR (third_department_name='直播部' AND sku_id_name LIKE '%图书赠送%') then '西安图书直播间-挂链'
  when rule_name LIKE '%99元智学%' then 'AI直播'
  when channel_provider_name = '宿迁伯岳' then '小程序'
  when third_department_name IN ('直播部','新媒体内容运营部','市场一组') AND (flow_pool_name LIKE '%海淀高阶名师%' OR flow_pool_name LIKE '%海淀老师高阶%' OR flow_pool_name LIKE '%小艺%') then '郭艺'
  when put_plan_name LIKE '%国培教育-0元%' OR put_plan_name LIKE '%易喆教育-0元%' OR put_plan_name LIKE '%钟情-0元%' OR put_plan_name LIKE '%中望达-0元%' OR put_plan_name LIKE '%晨硕-0元%' OR put_plan_name LIKE '%彩石-0元入群%' then '创新商务入群'
  when put_plan_name LIKE '%0元入群-进校%' AND third_department_name = '线上商务部' then '创新商务入群'
  when put_plan_name LIKE '%qq0元%' AND third_department_name = '线上商务部' then '创新QQ'
  when third_department_name='KOC孵化部' AND flow_pool_name LIKE '%电商退款%' AND put_plan_name LIKE '%失败%' then '自孵化KOC-赠课失败'
  when third_department_name='KOC孵化部' AND flow_pool_name LIKE '%电商退款%' AND put_plan_name LIKE '%退%' then '自孵化KOC-退款订单复用'
  when source_manager_name = '方俊结01' AND put_plan_name LIKE '%赠课后退款%' then 'KOC-赠课后退款'
  when third_department_name = '直播部' AND (sku_id_name LIKE '%春春%' OR sku_id_name LIKE '%瑞春%' OR rule_name LIKE '%春春%' OR rule_name LIKE '%瑞春%') then '陈瑞春'
  when third_department_name = '直播部' AND (sku_id_name LIKE '%朱博士99%' OR rule_name LIKE '%朱汉祺99%') then '朱博士99'
  when (third_department_name = '直播部' AND (sku_id_name LIKE '%朱博士%' OR sku_id_name LIKE '%朱汉祺%') AND rule_name LIKE '%9%' AND rule_name NOT LIKE '%29%' AND sku_id_name NOT LIKE '%急%' AND sku_id_name NOT LIKE '%礼盒29%') OR (third_department_name = '直播部' AND sku_id_name LIKE '%朱博士9%') then '朱博士9元'
  when channel_name_1 = '商务' AND channel_name_2 = '短信' then '短信'
  when ad_account_name LIKE '%肖晗%' AND channel_name_1 = '信息流' then '信息流-肖晗'
  when channel_name_1 = '信息流' AND channel_name_2='B站' AND (page_id_name LIKE '%亚飞%' OR source_put_plan_name LIKE '%亚飞%' OR rule_name LIKE '%亚飞%' OR page_id_name LIKE '%初中-0元%') then 'B站信息流-亚飞'
  when channel_name_1 = '信息流' AND (page_id_name LIKE '%亚飞%' OR ad_account_name LIKE '%亚飞%') then '信息流-亚飞'
  when (flow_pool_name LIKE '%朱博士%' OR flow_pool_name LIKE '%双博士%' OR flow_pool_name LIKE '%教育规划%') AND third_department_name <> '线上商务部' AND period_name NOT LIKE '%多学科拓展%' AND rule_name NOT LIKE '%张杰%' AND sku_id_name NOT LIKE '%马凯鹏IP%' AND third_department_name='直播部' then '朱博士29'
  when put_plan_name LIKE '%朱博士说教育%' AND period_name NOT LIKE '%多学科拓展%' AND flow_pool_name NOT LIKE '%高分讲堂%' AND flow_pool_name NOT LIKE '%总裁%' AND third_department_name='直播部' then '朱博士29'
  when flow_pool_name LIKE '%朱博士讲英语%' AND sku_id_name LIKE '%马凯鹏IP%' AND third_department_name='直播部' then '马凯鹏29'
  when (flow_pool_name LIKE '%朱博士讲英语%' OR flow_pool_name LIKE '%朱博士英语%' OR flow_pool_name LIKE '%朱汉祺说英语%' OR flow_pool_name LIKE '%朱博士说英语%' OR flow_pool_name LIKE '%教育规划%' OR flow_pool_name LIKE '%双博士英语规划%' OR flow_pool_name LIKE '%朱博士满分英语%' OR flow_pool_name LIKE '%英语教父朱博士%' OR (flow_pool_name LIKE '%中考决胜天团%' AND lead_purchase_intention_level1_category_name = '规划系统')) AND third_department_name = '直播部' AND period_name NOT LIKE '%多学科拓展%' AND sku_id_name NOT LIKE '%马凯鹏IP%' AND third_department_name='直播部' then '朱博士29'
  when (flow_pool_name LIKE '%汤哥%' OR flow_pool_name LIKE '%汤老师%') AND period_name NOT LIKE '%多学科拓展%' AND third_department_name IN ('直播部','新媒体内容运营部') then '汤老师'
  when (flow_pool_name LIKE '%中考百日冲刺%') AND period_name NOT LIKE '%多学科拓展%' AND third_department_name='直播部' then '曹忆9.9纯课'
  when (flow_pool_name LIKE '%马总%' OR flow_pool_name = '减法化学马老师' OR flow_pool_name LIKE '%总裁讲化学%' OR flow_pool_name LIKE '%高分讲堂%') AND period_name NOT LIKE '%多学科拓展%' AND sku_id_name LIKE '%99%' AND third_department_name='直播部' then '马凯鹏99'
  when (flow_pool_name LIKE '%马总%' OR flow_pool_name = '减法化学马老师' OR flow_pool_name LIKE '%总裁讲化学%' OR flow_pool_name LIKE '%高分讲堂%') AND period_name NOT LIKE '%多学科拓展%' AND sku_id_name NOT LIKE '%99%' AND third_department_name='直播部' then '马凯鹏29'
  when (flow_pool_name LIKE '%北大杰哥%' OR flow_pool_name LIKE '%张小杰%') AND period_name NOT LIKE '%多学科拓展%' AND third_department_name='直播部' then '张杰'
  when flow_pool_name LIKE '%教育规划%' AND rule_name LIKE '%张杰%' AND third_department_name='直播部' then '张杰'
  when source_manager_name = '陈晓菁04' AND channel_provider_name NOT LIKE '%开拓%' AND put_plan_name NOT LIKE '%九学%' then '商务低价'
  when (flow_pool_name LIKE '%孟帝%' OR flow_pool_name LIKE '%孟老师%' OR flow_pool_name LIKE '%中考数学冲刺%' OR flow_pool_name LIKE '%8升9数学%' OR flow_pool_name LIKE '%孟亚飞讲数学%' OR flow_pool_name LIKE '%中考冲刺%' OR flow_pool_name LIKE '%中考满分冲刺%' OR flow_pool_name LIKE '%押题王孟亚飞%' OR flow_pool_name LIKE '%中考数学大通关%' OR flow_pool_name LIKE '%中考数学规划%' OR flow_pool_name LIKE '%亚飞数学%') AND period_name NOT LIKE '%多学科拓展%' AND channel_name_2 NOT LIKE '%KOL%' AND third_department_name='直播部' AND rule_name LIKE '%99%' then '孟亚飞99-1组'
  when (flow_pool_name LIKE '%孟帝%' OR flow_pool_name LIKE '%孟老师%' OR flow_pool_name LIKE '%中考数学冲刺%' OR flow_pool_name LIKE '%8升9数学%' OR flow_pool_name LIKE '%孟亚飞讲数学%' OR flow_pool_name LIKE '%中考冲刺%' OR flow_pool_name LIKE '%中考满分冲刺%' OR flow_pool_name LIKE '%押题王孟亚飞%' OR flow_pool_name LIKE '%中考数学大通关%' OR flow_pool_name LIKE '%中考数学规划%' OR flow_pool_name LIKE '%亚飞数学%') AND period_name NOT LIKE '%多学科拓展%' AND channel_name_2 NOT LIKE '%KOL%' AND third_department_name='直播部' AND channel_name_2 = '百度' then '孟亚飞百度数字人'
  when (flow_pool_name LIKE '%孟帝%' OR flow_pool_name LIKE '%孟老师%' OR flow_pool_name LIKE '%中考数学冲刺%' OR flow_pool_name LIKE '%8升9数学%' OR flow_pool_name LIKE '%孟亚飞讲数学%' OR flow_pool_name LIKE '%中考冲刺%' OR flow_pool_name LIKE '%中考满分冲刺%' OR flow_pool_name LIKE '%押题王孟亚飞%' OR flow_pool_name LIKE '%中考数学大通关%' OR flow_pool_name LIKE '%中考数学规划%' OR flow_pool_name LIKE '%亚飞数学%') AND period_name NOT LIKE '%多学科拓展%' AND channel_name_2 NOT LIKE '%KOL%' AND third_department_name='直播部' then '孟亚飞9元'
  when put_plan_name LIKE '%刘家晋讲图文%' OR put_plan_name LIKE '%孟帝数学%' AND third_department_name='直播部' AND rule_name LIKE '%99%' then '孟亚飞99-1组'
  when put_plan_name LIKE '%刘家晋讲图文%' OR put_plan_name LIKE '%孟帝数学%' AND third_department_name='直播部' then '孟亚飞9元'
  when (flow_pool_name LIKE '%肖晗%' OR sku_id_name LIKE '%肖晗%') AND third_department_name='直播部' then '肖晗'
  when flow_pool_name LIKE '%峥峥%' AND period_name NOT LIKE '%多学科拓展%' AND third_department_name='直播部' then '何峥峥'
  when flow_pool_name LIKE '%汐子%' AND period_name NOT LIKE '%多学科拓展%' AND sku_id_name NOT LIKE '%亚飞%' AND third_department_name='直播部' then '王汐子'
  when flow_pool_name LIKE '%汐子%' AND period_name NOT LIKE '%多学科拓展%' AND sku_id_name LIKE '%亚飞%' AND third_department_name='直播部' AND rule_name LIKE '%99%' then '孟亚飞99-1组'
  when flow_pool_name LIKE '%汐子%' AND period_name NOT LIKE '%多学科拓展%' AND sku_id_name LIKE '%亚飞%' AND third_department_name='直播部' then '孟亚飞9元'
  when (flow_pool_name LIKE '%曹忆%' OR flow_pool_name LIKE '%dudu%' OR flow_pool_name LIKE '%中考决胜天团%' OR flow_pool_name LIKE '%具象思维%' OR flow_pool_name LIKE '%在逃发面馒头%' OR flow_pool_name LIKE '%库洛米%' AND lead_purchase_intention_level1_category_name <> '规划系统') AND period_name NOT LIKE '%多学科拓展%' AND third_department_name IN ('直播部','新媒体内容运营部') then '曹忆'
  when flow_pool_name = '正价课判单补录' then '正价课判单补录'
  when channel_name_1 = '转介绍' then '转介绍'
  when first_department_name ='市场部' AND channel_name_1 <> '站内获客' AND channel_name_2 <> 'APP' then '集团私域'
  when put_plan_name LIKE '%未加好友%' then '市场私域未加好友'
  when put_plan_name LIKE '%私域-信息流%' then '市场私域待支付'
  when third_department_name = '私域运营部' AND rule_name NOT LIKE '%训练营%' AND virtual_fifth_department_name NOT IN ('罗江博团队') AND rule_name NOT LIKE '%复用%' AND rule_name NOT LIKE '%未加好友%' AND channel_name_2 <> '内部换量' then '市场私域低价单'
  when third_department_name = '私域运营部' AND rule_name NOT LIKE '%训练营%' AND rule_name NOT LIKE '%复用%' AND rule_name NOT LIKE '%未加好友%' AND channel_name_2 <> '内部换量' AND flow_original_order_activity_price = '0.0' then '市场私域低价单'
  when third_department_name = '私域运营部' AND channel_name_1 = '信息流获客' then '市场私域小红书'
  when channel_name_2 IN ('APP','M站','PC') AND flow_pool_name NOT LIKE '%途途%' then 'APP'
  when source_manager_name IN ('高文羽') AND lead_purchase_intention_name = 'AI定制' then '人工外呼-AI'
  when channel_provider_name LIKE '%唐山TMK%' then '唐山TMK'
  when source_manager_name IN ('高文羽') AND channel_provider_name NOT LIKE '%唐山TMK%' AND channel_provider_name NOT LIKE '%郑州%' then '人工外呼'
  when source_manager_name IN ('高文羽') AND channel_provider_name NOT LIKE '%唐山TMK%' AND channel_provider_name LIKE '%郑州%' then '郑州TMK-2组'
  when source_manager_name = '冯银晨' AND channel_name_2 = '小红书' then '信息流-小红书'
  when channel_name_1 = '信息流获客' AND flow_original_order_activity_price LIKE '%1990%' then '信息流19'
  when (channel_name_1 = '信息流' AND channel_name_2 <> 'B站' AND third_department_name NOT LIKE '%商务%' AND put_plan_name NOT LIKE '%初三0元%' AND put_plan_name NOT LIKE '%抖音私信%' AND put_plan_name NOT LIKE '%高中0元%' AND flow_original_order_activity_price NOT LIKE '%1990%') OR (channel_name_2 = 'B站' AND third_department_name LIKE '%投放%') then '信息流'
  when channel_name_1 = '信息流' AND channel_name_2 = 'B站' AND third_department_name NOT LIKE '%投放%' AND (page_id_name LIKE '%郭艺%') then 'B站信息流-郭艺'
  when channel_name_1 = '信息流' AND channel_name_2 = 'B站' AND third_department_name NOT LIKE '%投放%' AND (page_id_name LIKE '%朱博士%') then 'B站信息流-朱汉祺'
  when channel_name_1 = '信息流' AND channel_name_2 = 'B站' AND third_department_name NOT LIKE '%投放%' AND page_id_name LIKE '%肖晗%' then 'B站信息流-肖晗'
  when channel_name_1 = '信息流' AND channel_name_2 = 'B站' AND third_department_name NOT LIKE '%投放%' AND (page_id_name LIKE '%马凯鹏%' OR ad_account_name LIKE '%化学%') then 'B站信息流-马凯鹏'
  when channel_name_1 = '信息流' AND channel_name_2 = 'B站' AND third_department_name NOT LIKE '%投放%' AND (sku_id_name LIKE '%陈瑞春%' OR rule_name LIKE '%陈瑞春%') AND (ad_account_name LIKE '%语文%' OR source_put_plan_name LIKE '%自然流%' OR page_id_name LIKE '%春春%') then 'B站信息流-陈瑞春'
  when channel_name_1 = '信息流' AND channel_name_2 = 'B站' AND third_department_name NOT LIKE '%投放%' AND (flow_original_order_activity_price LIKE '%2990%' OR sku_id_name LIKE '%帅师%' OR sku_id_name LIKE '%周帅%') AND ad_account_name LIKE '%语文%' AND (flow_original_order_activity_price LIKE '%1980%' OR flow_original_order_activity_price LIKE '%2980%' OR flow_original_order_activity_price LIKE '%2990%') then 'B站信息流-陈瑞春'
  when channel_name_1 = '信息流' AND channel_name_2 = 'B站' AND third_department_name NOT LIKE '%投放%' AND (flow_original_order_activity_price LIKE '%2990%' OR sku_id_name LIKE '%帅师%' OR sku_id_name LIKE '%周帅%') AND ad_account_name NOT LIKE '%语文%' then 'B站信息流-周帅'
  when channel_name_1 = '信息流' AND channel_name_2 = 'B站' AND third_department_name NOT LIKE '%投放%' AND flow_order_price LIKE '%1980%' AND ad_account_name LIKE '%数学%' then 'B站信息流-周帅'
  when channel_name_1 = '短直电商' AND channel_name_2 = 'B站' AND third_department_name LIKE '%商务%' AND sku_id_name LIKE '%陈瑞春%' AND flow_pool_name LIKE '%自然流%' then 'B站信息流-陈瑞春'
  when channel_name_1 = '短直电商' AND channel_name_2 = 'B站' AND third_department_name LIKE '%商务%' AND sku_id_name LIKE '%朱博士%' AND flow_pool_name LIKE '%自然流%' then 'B站信息流-朱汉祺'
  when third_department_name = '线上商务部' AND channel_name_2 = 'B站' AND put_plan_name LIKE '%春春%' then 'B站信息流-陈瑞春'
  when third_department_name = '线上商务部' AND channel_name_2 = 'B站' AND put_plan_name LIKE '%朱博士%' then 'B站信息流-朱汉祺'
  when channel_name_1 = '信息流' AND channel_name_2 = 'B站' AND third_department_name NOT LIKE '%投放%' AND flow_original_order_activity_price NOT LIKE '%2980%' AND flow_original_order_activity_price NOT LIKE '%2990%' AND flow_original_order_activity_price NOT LIKE '%1980%' then 'B站信息流'
  when flow_pool_name = '百度搜索引擎' OR channel_name_1='搜索营销' then '信息流搜索'
  when channel_name_1 = '信息流获客' AND channel_name_2 = '小红书' AND source_manager_name IN ('王慧敏13','张琳02','王樱琦01') then '小红书投放'
  when flow_pool_name LIKE '%小红书班课%' then '小红书投放'
  when third_department_name = '投放部' AND get_customer_way_name = '短视频信息流' AND flow_original_order_activity_price LIKE '%100%' then '信息流'
  when source_manager_name IN ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') AND (sku_id_name LIKE '%原型题%') then 'KOC-书课包'
  -- 2026-08-01: 0728期退款复用误入0803期KOC渠道，按业务确认统一归入退款订单复用。
  when period_name = '20260803期'
   and third_department_name = '线上商务部'
   and source_manager_name in ('曲默晗','何木玲')
   and sku_id_name like '0728期-%'
   and (sku_id_name like '%帅师%' or sku_id_name like '%孟帝%')
  then '退款订单复用'
  when flow_pool_name = '中考加油' AND sku_id_name LIKE '%孟帝%' then 'KOC-孟亚飞数学'
  when flow_pool_name = '中考加油' AND sku_id_name LIKE '%帅师%' then 'KOC-周帅数学'
  when flow_pool_name = '中考加油' AND sku_id_name LIKE '%肖晗%' then 'KOC-肖晗'
  when source_manager_name IN ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') AND (sku_id_name LIKE '%孟帝%' OR sku_id_name LIKE '%dudu%' OR sku_id_name LIKE '%市场初二%' OR rule_name LIKE '%亚飞%' OR sku_id_name LIKE '%初二高阳%' OR sku_id_name LIKE '%高阳初二%' OR sku_id_name LIKE '%精品初二%' OR sku_id_name LIKE '%菁英初三%' OR (virtual_second_department_name = '菁英班学部' AND lead_purchase_intention_level2_category_name='初级' AND lead_create_time>= '2026-04-15 00:00:00')) then 'KOC-孟亚飞数学'
  when source_manager_name IN ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') AND (sku_id_name LIKE '%帅师%' OR rule_name LIKE '%周帅%') then 'KOC-周帅数学'
  when source_manager_name IN ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') AND (sku_id_name LIKE '%肖晗%' OR rule_name LIKE '%肖晗%') then 'KOC-肖晗'
  when source_manager_name IN ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') AND period_name NOT LIKE '%多学科拓展%' AND (flow_original_order_activity_price LIKE '%1100%' OR flow_original_order_activity_price LIKE '%500%' OR flow_orders_income_amount LIKE '%500%') AND (sku_id_name LIKE '%朱汉祺%' OR sku_id_name LIKE '%朱博士%' OR rule_name LIKE '%朱汉祺5元%' OR sku_id_name LIKE '%koc5元-朱博士%' OR rule_name LIKE '%朱汉祺%') then 'KOC-5元朱汉祺'
  when source_manager_name IN ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') AND (sku_id_name LIKE '%朱汉祺%' OR sku_id_name LIKE '%29元%' OR sku_id_name LIKE '%朱博士%' OR rule_name LIKE '%朱汉祺%' OR rule_name LIKE '%朱博士%' ) AND (flow_original_order_activity_price NOT LIKE '%1100%' OR rule_name LIKE '%29%') AND sku_id_name NOT LIKE '%周帅%' then 'KOC-5元朱汉祺'
  when source_manager_name IN ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') AND period_name NOT LIKE '%多学科拓展%' AND sku_id_name NOT LIKE '%朱汉祺%' AND sku_id_name NOT LIKE '%朱博士%' AND sku_id_name NOT LIKE '%周帅%' AND sku_id_name NOT LIKE '%29元%' then 'KOC-5元纯课'
  when source_manager_name IN ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') AND sku_id_name LIKE '%周帅%' then 'KOC-周帅'
  when third_department_name IN ('品牌效能部','KOC孵化部') AND channel_name_2 IN ('抖音','视频号','快手','KOL') then '自孵化KOC-5元纯课'
  when third_department_name IN ('品牌效能部','KOC孵化部') AND channel_name_2 IN ('抖音','视频号','快手','KOL') AND (sku_id_name LIKE '%5元%'OR sku_id_name LIKE '%11元%' OR flow_original_order_activity_price LIKE '%1100%' OR flow_original_order_activity_price LIKE '%500%' OR flow_orders_income_amount LIKE '%1100%' OR flow_orders_income_amount LIKE '%500%' ) then '自孵化KOC-5元纯课'
  when source_manager_name IN ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') AND channel_name_2 LIKE '%社群%' then '进校社群'
  when source_manager_name IN ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') AND channel_name_2 LIKE '%TMK%' AND page_id_name LIKE '%1元%' then '进校TMK1元'
  when source_manager_name IN ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') AND channel_name_2 LIKE '%TMK%' AND page_id_name LIKE '%9元%' then '进校TMK9元'
  when source_manager_name IN ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') AND channel_name_2 LIKE '%书商%' then '进校书商'
  when source_manager_name IN ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') AND channel_name_2 LIKE '%综合%' AND put_plan_name LIKE '%18%' then '进校直播'
  when source_manager_name IN ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') AND channel_name_2 LIKE '%直播%' then '进校直播'
  when source_manager_name IN ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04') AND put_plan_name NOT LIKE '%0元%' AND flow_pool_name NOT LIKE '%家校共育%' AND flow_pool_name NOT LIKE '%保持热爱%' AND flow_pool_name NOT LIKE '%青松%' AND flow_pool_name NOT LIKE '%原子初三%' AND flow_pool_name NOT LIKE '%南通欣创%' AND flow_pool_name NOT LIKE '%悟之道%' AND flow_pool_name NOT LIKE '%济南梦航%' AND channel_name_3 <> '社群' AND put_plan_name NOT LIKE '%善悟%' AND put_plan_name NOT LIKE '%人人通%' AND put_plan_name NOT LIKE '%%济南格乐' AND flow_pool_name NOT LIKE '%晨硕智学%' AND flow_pool_name NOT LIKE '%兴尧文化%' AND flow_pool_name NOT LIKE '%济南映像%' AND flow_pool_name NOT LIKE '%山东简单%' AND flow_pool_name NOT LIKE '%争鸣科技%' then '商务低价'
  when flow_pool_name LIKE '%原子初三%' OR flow_pool_name LIKE '%原子系统%' then '原子'
  when flow_pool_name LIKE '%市场部-公转私%' then '市场私域公导私'
  when flow_pool_name LIKE '%南通欣创%' OR flow_pool_name LIKE '%人人通科技%' OR flow_pool_name LIKE '%易而购%' OR flow_pool_name LIKE '%济南梦航%' OR flow_pool_name LIKE '%晨硕智学%' OR flow_pool_name LIKE '%兴尧文化%' OR flow_pool_name LIKE '%济南映像%' OR flow_pool_name LIKE '%山东简单%' OR flow_pool_name LIKE '%争鸣科技%' then '进校私域合作'
  when (flow_pool_name LIKE '%家校共育%' OR flow_pool_name LIKE '%保持热爱%' OR flow_pool_name LIKE '%青松%' OR flow_pool_name LIKE '%悟之道%') AND put_plan_name NOT LIKE '%0元%' then '进校私域合作'
  when source_manager_name = '李宁24' AND put_plan_name LIKE '%0转低%' then '进校私域合作'
  when third_department_name = '私域运营部' AND flow_original_order_activity_price IN ('100.0','900.0','300.0') then '进校私域合作'
  when third_department_name = '私域运营部' AND flow_original_order_activity_price IN ('0.0') AND source_manager_name IN ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研') then '进校私域合作'
  when third_department_name = '私域运营部' AND channel_name_1='市场私域' AND put_plan_name NOT LIKE '%公导私%' AND put_plan_name NOT LIKE '%公转私%' AND flow_original_order_activity_price = '0.0' AND rule_name NOT LIKE '%激活%' AND rule_name NOT LIKE '%咨询%' AND rule_name NOT LIKE '%训练营%' AND virtual_fifth_department_name NOT LIKE '%罗江博%' AND virtual_fifth_department_name NOT LIKE '%郑州学习顾问二部%' AND source_manager_name NOT IN ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研') then '市场私域低价单'
  when flow_pool_name LIKE '%青岛寻知%' OR flow_pool_name LIKE '%禾兴信息%' then '商务0元'
  when put_plan_name LIKE '%益企发1元%' OR put_plan_name LIKE '%腾瑞教育1元%' then '进校APP合作'
  when put_plan_name LIKE '%外部图书供量%' OR flow_pool_name='高途旗舰店—线索—yuxinru' then '外部图书慧敏'
  when source_manager_name IN ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') AND channel_name_2 LIKE '%社群%' then '创新社群'
  when source_manager_name IN ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') AND (channel_name_2 LIKE '%直推%' OR put_plan_name LIKE '%直推%') then '创新直推'
  when source_manager_name IN ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') AND (channel_name_2 LIKE '%书商%' OR put_plan_name LIKE '%书商%' OR page_id_name LIKE '%书商%') then '创新书商'
  when source_manager_name IN ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') AND channel_name_2 LIKE '%TMK%' AND page_id_name LIKE '%1元%' then '创新TMK1元'
  when source_manager_name IN ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') AND channel_name_2 LIKE '%TMK%' AND page_id_name LIKE '%9元%' then '创新TMK9元'
  when source_manager_name IN ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') AND (channel_name_2 LIKE '%直播%' OR page_id_name LIKE '%进校%') then '创新直播'
  when source_manager_name IN ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') AND channel_name_2<>'公众号' AND channel_name_1 = '商务' AND flow_pool_name <> '高途云集图书专营店-自然流' AND flow_pool_name <> '高途旗舰店—线索—yuxinru' AND put_plan_name NOT LIKE '%社群%' AND put_plan_name NOT LIKE '%小红书班课%' AND put_plan_name NOT LIKE '%外部图书供量%' AND channel_second_provider_name NOT LIKE '%沃德丰店铺线索赠课%' AND channel_second_provider_name NOT LIKE '%智慧城-图书%' AND put_plan_name NOT LIKE '%育甲%' AND flow_pool_name NOT LIKE '%周长磊%' then '创新商务'
  when flow_pool_name LIKE '%周长磊%' then '创新APP'
  when channel_provider_name LIKE '%唐成刚%' OR flow_pool_name = '高途云集图书专营店-自然流' then '图书唐成刚'
  when channel_second_provider_name LIKE '%沃德丰店铺线索赠课%' OR channel_second_provider_name LIKE '%智慧城-图书%' OR put_plan_name LIKE '%育甲%' then '外部图书慧敏'
  when flow_pool_name LIKE '%高途图书产品学部%' then '图书任炯旭'
  when source_manager_name IN ('王春宵') then '武汉图书直播间'
  when source_manager_name IN ('高曼曼01','杨思怡','宋向函') then '图书KOC达人'
  when flow_pool_name LIKE '%高中视频书%' OR flow_pool_name LIKE '%高中教辅书%' OR flow_pool_name LIKE '%朵拉老师%' then '北京图书直播间'
  when flow_pool_name LIKE '%市场部-原子合作%' then '原子'
  when flow_pool_name LIKE '%市场部-微信私域%' OR flow_pool_name LIKE '%市场部-规划报告%' OR flow_pool_name LIKE '%规划报告%' OR flow_pool_name LIKE '%市场部-小红书%' OR flow_pool_name LIKE '%孟浩宇%' then '市场私域低价单'
  when flow_pool_name LIKE '%待支付%' then '市场私域待支付'
  when flow_pool_name LIKE '%未加好友%' then '市场私域未加好友'
  when flow_pool_name LIKE '%内部换量%' then '市场私域首期掉海'
  when flow_pool_name LIKE '公导私' then '进校私域合作'
  when source_manager_name IN ('方宇02','李月林') then '菁英市场流量'
  when channel_name_2 = '公众号' then '公众号'
  when (flow_pool_name LIKE '%增长组%' OR channel_name_3 = '公众号' OR second_department_name = '微信生态部') AND channel_name_2 <> 'APP' then '集团私域'
  when put_plan_name LIKE '%济南格乐%' AND put_plan_name LIKE '%表单%' then '商务0元'
  when put_plan_name LIKE '%B类%' OR put_plan_name LIKE '%b类%' OR channel_second_provider_name LIKE '%KOC当期%' then 'KOC分层测试'
  when put_plan_name LIKE '%星耀%' OR put_plan_name LIKE '%物理展博%' OR put_plan_name LIKE '%物理谢丽荣%' OR put_plan_name LIKE '%牟恩伯%' OR put_plan_name LIKE '%王赞%' OR put_plan_name LIKE '%张磊老师高中数学%' OR put_plan_name LIKE '%雯姐高中物理大讲堂%' then '百度星耀'
  when source_manager_name = '刘福云' AND (sku_id_name LIKE '%瑞春%' OR sku_id_name LIKE '%春春%') then '陈瑞春'
  when source_manager_name = '刘福云' AND sku_id_name LIKE '%周帅%' then '周帅'
  when third_department_name = '直播部' AND sku_id_name LIKE '%周帅%' AND channel_name_2 IN ('百度','B站') then '周帅-百度数字人'
  when third_department_name = '直播部' AND sku_id_name LIKE '%孟亚飞%' AND sku_id_name LIKE '%199%' then '孟亚飞199'
  when third_department_name = '直播部' AND sku_id_name LIKE '%孟亚飞%' AND rule_name LIKE '%99%' then '孟亚飞99-1组'
  when third_department_name = '直播部' AND sku_id_name LIKE '%孟亚飞%' then '孟亚飞9元'
  when third_department_name = '直播部' AND sku_id_name LIKE '%朱汉祺%' then '朱博士29'
  when third_department_name = '直播部' AND sku_id_name LIKE '%肖晗%' then '肖晗'
  when flow_pool_name LIKE '%0转低转正%' OR channel_name_2='产研测试' then '进校私域合作'
  when source_manager_name IN ('陈甜06','梁晓敏') then '图书挂车'
  when flow_pool_name LIKE '%天津智慧双子%' then '创新社群'
  when third_department_name LIKE '%城市定制%' then '点睛卷'
  when first_department_name LIKE '%KM%' AND flow_pool_name NOT LIKE '%天津智慧双子%' then '途途商务'
  when period_name LIKE '%多学科拓展%' AND third_department_name LIKE '%私域运营%' then '市场私域入群'
  when put_plan_name LIKE '%赠课失败%' AND third_department_name = '线上商务部' then 'KOC赠课失败'
  when flow_pool_name LIKE '%自然流%' AND source_manager_name IN ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') AND sku_id_name LIKE '%周帅%' then 'KOC-周帅'
  when flow_pool_name LIKE '%自然流%' AND source_manager_name IN ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') AND sku_id_name LIKE '%肖晗%' then 'KOC-肖晗'
  when flow_pool_name LIKE '%自然流%' AND source_manager_name IN ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') AND sku_id_name LIKE '%朱汉祺%' AND flow_original_order_activity_price LIKE '%1100%' then 'KOC-5元朱汉祺'
  when flow_pool_name LIKE '%自然流%' AND source_manager_name IN ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') AND sku_id_name LIKE '%朱汉祺%' AND flow_original_order_activity_price NOT LIKE '%1100%' then 'KOC-朱汉祺29'
  when flow_pool_name LIKE '%自然流%' AND source_manager_name IN ('赵语诗','崔文轩','孙培尧') then '自孵化KOC-5元纯课'
  when flow_pool_name LIKE '%自然流%' AND (sku_id_name LIKE '%朱博士%' OR sku_id_name LIKE '%朱汉祺%') AND rule_name LIKE '%9%' AND rule_name NOT LIKE '%29%' AND third_department_name IN ('直播部','新媒体内容运营部','市场一组') then '朱博士9元'
  when flow_pool_name LIKE '%自然流%' AND sku_id_name LIKE '%朱博士%' AND third_department_name IN ('直播部','新媒体内容运营部','市场一组') then '朱博士29'
  when flow_pool_name LIKE '%自然流%' AND sku_id_name LIKE '%亚飞%' AND rule_name LIKE '%99%' AND third_department_name IN ('直播部','新媒体内容运营部','市场一组') then '孟亚飞99-1组'
  when flow_pool_name LIKE '%自然流%' AND sku_id_name LIKE '%亚飞%' AND third_department_name IN ('直播部','新媒体内容运营部','市场一组') then '孟亚飞9元'
  when flow_pool_name LIKE '%自然流%' AND sku_id_name LIKE '%曹忆%' then '曹忆'
  when flow_pool_name LIKE '%自然流%' AND rule_name LIKE '%朱博士%' AND third_department_name IN ('直播部','新媒体内容运营部','市场一组') then '朱博士29'
  when flow_pool_name LIKE '%自然流%' AND source_manager_name LIKE '%邵万昕%' AND third_department_name IN ('直播部','新媒体内容运营部','市场一组') then '朱博士29'
  when flow_pool_name LIKE '%自然流%' AND rule_name LIKE '%亚飞%' AND rule_name LIKE '%99%' then '孟亚飞99-1组'
  when flow_pool_name LIKE '%自然流%' AND rule_name LIKE '%亚飞%' then '孟亚飞9元'
  when flow_pool_name LIKE '%自然流%' AND rule_name LIKE '%曹忆%' then '曹忆'
  when flow_pool_name LIKE '%途途教室%' OR first_department_name LIKE 'TUTU' then '途途APP'
  when second_department_name = '市场二部' AND get_customer_way_name = 'KOL直播' then '市场二部KOC'
  when source_manager_name IN ('宋莹莹','辛世如') AND channel_name_2 IN ('视频号') then '信息流-虚拟号挂车'
  when put_plan_name LIKE '%高三复读%' then '市场私域高三复读'
  when put_plan_name ='美玲测试' then '途途信息流私信'
  when rule_name LIKE '%训练营%' AND rule_name LIKE '%市场私域%' then '市场私域入群'
  when flow_pool_name LIKE '%青少-私域%' then '青少私域'
  when first_department_name = 'TT业务线' AND third_department_name LIKE '%商务招生%' then '途途商务'
  when second_department_name = '战略客户部' then '文旅进校'
  when put_plan_name LIKE '%AI名师%' then 'AI直播'
  when channel_name_1= '信息流' AND (put_plan_name LIKE '%抖音私信%' OR put_plan_name LIKE '%初三0元%' OR put_plan_name LIKE '%高中0元%') then '信息流-抖音私信'
  when rule_name LIKE '%途途私域%' OR (rule_name LIKE '%私域%' AND first_department_name = 'TT') then '途途私域'
  else '其他未知流量'
end AS channel_map,
        CASE
            WHEN rule_name LIKE '%初二%' THEN '初二'
            WHEN rule_name LIKE '%初三%' THEN '初三'
            WHEN rule_name LIKE '%高一%' THEN '高一'
            WHEN rule_name LIKE '%高二%' THEN '高二'
            WHEN rule_name LIKE '%高三%' THEN '高三'
            ELSE lead_purchase_intention_level2_category_name
        END AS grade_name,
        lead_count, valid_lead_count, conversion_lead_count,
        subject_count, order_count,
        income_amount, in_pay_period_refund_amount, non_pay_period_refund_amount,
        same_lead_period_income_amount, same_lead_period_refund_amount,
        same_lead_period_conversion_lead_count
    FROM lead_raw
),
-- 用户层：先按展示粒度×用户聚合，再判断正价课出单与退费人头/人次
user_base AS (
    SELECT
        period_name,
        channel_map,
        grade_name,
        jingli,
        zhuguan,
        employee_email_name,
        user_id,
        SUM(valid_lead_count) AS valid_lead_count,
        SUM(conversion_lead_count) AS regular_course_user_count,
        SUM(subject_count) AS pay_subject_person_count,
        SUM(in_pay_period_refund_amount + non_pay_period_refund_amount) AS refund_section_amount
    FROM lead_base
    GROUP BY period_name, channel_map, grade_name, jingli, zhuguan, employee_email_name, user_id
),
user_agg AS (
    SELECT
        period_name,
        channel_map,
        grade_name,
        jingli,
        zhuguan,
        employee_email_name,
        SUM(CASE WHEN regular_course_user_count > 0 THEN 1 ELSE 0 END) AS pay_user_head_count,
        SUM(CASE WHEN regular_course_user_count > 0 AND refund_section_amount > 0 THEN 1 ELSE 0 END) AS refund_headcount_section,
        SUM(CASE WHEN regular_course_user_count > 0 AND refund_section_amount > 0 THEN pay_subject_person_count ELSE 0 END) AS refund_subject_person_count_section,
        SUM(CASE WHEN regular_course_user_count > 0 AND refund_section_amount > 0 AND pay_subject_person_count = 1 THEN 1 ELSE 0 END) AS refund_1_subject_headcount,
        SUM(CASE WHEN regular_course_user_count > 0 AND refund_section_amount > 0 AND pay_subject_person_count BETWEEN 2 AND 3 THEN 1 ELSE 0 END) AS refund_2_3_subject_headcount,
        SUM(CASE WHEN regular_course_user_count > 0 AND refund_section_amount > 0 AND pay_subject_person_count > 3 THEN 1 ELSE 0 END) AS refund_3plus_subject_headcount
    FROM user_base
    GROUP BY period_name, channel_map, grade_name, jingli, zhuguan, employee_email_name
),
-- ★ 预聚合：按期次×渠道×年级×经理×主管×顾问 汇总金额类分子/分母指标
agg AS (
    SELECT
        period_name,
        channel_map,
        grade_name,
        jingli,
        zhuguan,
        employee_email_name,
        -- === 基础指标 ===
        COUNT(DISTINCT CASE WHEN valid_lead_count > 0 THEN lead_id END) AS valid_lead_cnt,
        COUNT(DISTINCT CASE WHEN valid_lead_count > 0 THEN user_id END) AS total_headcount,
        -- === GMV退费率（当期）分子/分母 ===
        SUM(same_lead_period_refund_amount) / 100.0 AS refund_current_gmv,
        SUM(same_lead_period_income_amount - same_lead_period_refund_amount) / 100.0 AS net_income_current_gmv,
        -- === GMV退费率（截面）分子/分母 ===
        SUM(in_pay_period_refund_amount + non_pay_period_refund_amount) / 100.0 AS refund_section_gmv,
        SUM(income_amount - in_pay_period_refund_amount - non_pay_period_refund_amount) / 100.0 AS net_income_section_gmv,
        -- === 1科 GMV分子/分母（截面） ===
        SUM(CASE WHEN subject_count = 1 THEN in_pay_period_refund_amount + non_pay_period_refund_amount ELSE 0 END) / 100.0 AS refund_1_subject_gmv,
        SUM(CASE WHEN subject_count = 1 THEN income_amount - in_pay_period_refund_amount - non_pay_period_refund_amount ELSE 0 END) / 100.0 AS net_income_1_subject_gmv,
        -- === 2-3科 GMV分子/分母（截面） ===
        SUM(CASE WHEN subject_count BETWEEN 2 AND 3 THEN in_pay_period_refund_amount + non_pay_period_refund_amount ELSE 0 END) / 100.0 AS refund_2_3_subject_gmv,
        SUM(CASE WHEN subject_count BETWEEN 2 AND 3 THEN income_amount - in_pay_period_refund_amount - non_pay_period_refund_amount ELSE 0 END) / 100.0 AS net_income_2_3_subject_gmv,
        -- === 3科以上 GMV分子/分母（截面） ===
        SUM(CASE WHEN subject_count > 3 THEN in_pay_period_refund_amount + non_pay_period_refund_amount ELSE 0 END) / 100.0 AS refund_3plus_subject_gmv,
        SUM(CASE WHEN subject_count > 3 THEN income_amount - in_pay_period_refund_amount - non_pay_period_refund_amount ELSE 0 END) / 100.0 AS net_income_3plus_subject_gmv
    FROM lead_base
    GROUP BY period_name, channel_map, grade_name, jingli, zhuguan, employee_email_name
)
SELECT
    a.period_name,
    a.channel_map,
    a.grade_name,
    a.jingli,
    a.zhuguan,
    a.employee_email_name,
    -- 基础
    a.valid_lead_cnt,
    a.total_headcount,
    COALESCE(u.pay_user_head_count, 0) AS pay_user_head_count,
    -- GMV退费率（当期）= refund_current_gmv / net_income_current_gmv
    ROUND(CAST(a.refund_current_gmv AS double), 2)   AS refund_current_gmv,
    ROUND(CAST(a.net_income_current_gmv AS double), 2) AS net_income_current_gmv,
    -- GMV退费率（截面）= refund_section_gmv / net_income_section_gmv
    ROUND(CAST(a.refund_section_gmv AS double), 2)   AS refund_section_gmv,
    ROUND(CAST(a.net_income_section_gmv AS double), 2) AS net_income_section_gmv,
    -- 人头退费率（截面）= refund_headcount_section / pay_user_head_count
    COALESCE(u.refund_headcount_section, 0) AS refund_headcount_section,
    COALESCE(u.refund_subject_person_count_section, 0) AS refund_subject_person_count_section,
    -- 1科
    ROUND(CAST(a.refund_1_subject_gmv AS double), 2)   AS refund_1_subject_gmv,
    ROUND(CAST(a.net_income_1_subject_gmv AS double), 2) AS net_income_1_subject_gmv,
    COALESCE(u.refund_1_subject_headcount, 0) AS refund_1_subject_headcount,
    -- 2-3科
    ROUND(CAST(a.refund_2_3_subject_gmv AS double), 2)   AS refund_2_3_subject_gmv,
    ROUND(CAST(a.net_income_2_3_subject_gmv AS double), 2) AS net_income_2_3_subject_gmv,
    COALESCE(u.refund_2_3_subject_headcount, 0) AS refund_2_3_subject_headcount,
    -- 3科以上
    ROUND(CAST(a.refund_3plus_subject_gmv AS double), 2)   AS refund_3plus_subject_gmv,
    ROUND(CAST(a.net_income_3plus_subject_gmv AS double), 2) AS net_income_3plus_subject_gmv,
    COALESCE(u.refund_3plus_subject_headcount, 0) AS refund_3plus_subject_headcount
FROM agg a
LEFT JOIN user_agg u
  ON COALESCE(a.period_name, '#NULL#') = COALESCE(u.period_name, '#NULL#')
 AND COALESCE(a.channel_map, '#NULL#') = COALESCE(u.channel_map, '#NULL#')
 AND COALESCE(a.grade_name, '#NULL#') = COALESCE(u.grade_name, '#NULL#')
 AND COALESCE(a.jingli, '#NULL#') = COALESCE(u.jingli, '#NULL#')
 AND COALESCE(a.zhuguan, '#NULL#') = COALESCE(u.zhuguan, '#NULL#')
 AND COALESCE(a.employee_email_name, '#NULL#') = COALESCE(u.employee_email_name, '#NULL#')
WHERE a.period_name > '20260410期'
ORDER BY a.period_name, a.channel_map, a.grade_name, a.jingli, a.zhuguan, a.employee_email_name
