WITH lead_raw AS (
    SELECT DISTINCT
        concat(
            cast(date_format(date_trunc('week', date_parse(replace(concat(t1.group_period_year, t1.group_period_term), '期', ''), '%Y%m%d') - interval '1' day) + interval '4' day, '%Y%m%d') as varchar),
            '期'
        ) AS period_name,
        t1.lead_id,
        t1.user_id,
        t1.rule_name,
        t1.lead_purchase_intention_level2_category_name,
        t1.employee_email_name,
        t1.employee_email_prefix,
        t1.virtual_third_department_name,
        t1.virtual_fourth_department_name,
        t1.virtual_fifth_department_name,
        t1.virtual_second_department_name,
        t1.section_assign_employee_second_level_department_name,
        t1.virtual_leader_email_name,
        t1.virtual_direct_leader_email_name,
        t1.flow_pool_name,
        t1.third_department_name,
        t1.second_department_name,
        t1.first_department_name,
        t1.sku_id_name,
        t1.ad_account_name,
        t1.source_manager_name,
        t1.channel_name_1,
        t1.channel_name_2,
        t1.channel_name_3,
        t1.put_plan_name,
        t1.channel_provider_name,
        t1.channel_second_provider_name,
        t1.page_id_name,
        t1.source_put_plan_name,
        t1.get_customer_way_name,
        t1.lead_purchase_intention_name,
        t1.lead_purchase_intention_level1_category_name,
        cast(t1.flow_original_order_activity_price as varchar) AS flow_original_order_activity_price,
        cast(t1.flow_order_price as varchar) AS flow_order_price,
        cast(t1.flow_orders_income_amount as varchar) AS flow_orders_income_amount,
        t1.lead_create_time,
        coalesce(t1.lead_count, 0) AS lead_count,
        coalesce(t1.valid_lead_count, 0) AS valid_lead_count,
        coalesce(t1.conversion_lead_count, 0) AS conversion_lead_count,
        coalesce(t1.order_count, 0) AS order_count,
        coalesce(t1.income_amount, 0) AS income_amount,
        coalesce(t1.in_pay_period_refund_amount, 0) AS in_pay_period_refund_amount,
        coalesce(t1.non_pay_period_refund_amount, 0) AS non_pay_period_refund_amount,
        coalesce(t1.friend_lead_count, 0) AS friend_lead_count
    FROM bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df t1
    WHERE t1.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
      AND t1.hour = format_datetime(now() - interval '3' hour, 'HH')
      AND t1.section_assign_employee_first_level_department_name = 'H业务线'
      AND t1.section_assign_employee_second_level_department_name = '市场部'
      AND t1.section_assign_employee_third_level_department_name = '市场顾问部'
      AND t1.virtual_third_department_name = '市场顾问部'
      AND (t1.period_mapping_first_level_department_name = 'H业务线' OR t1.period_mapping_first_level_department_name IS NULL)
      AND (
            t1.period_mapping_second_level_department_name IN ('市场部', '精品班学部')
         OR t1.period_mapping_second_level_department_name IS NULL
      )
),
lead_base AS (
    SELECT
        period_name,
        lead_id,
        user_id,
        rule_name,
        employee_email_name,
        employee_email_prefix,
        virtual_third_department_name AS depart_1,
        section_assign_employee_second_level_department_name AS dept_name,
        virtual_fourth_department_name AS depart,
        virtual_leader_email_name AS jingli,
        virtual_direct_leader_email_name AS zhuguan,
        CASE WHEN flow_pool_name IN ('高途学习规划','智辉老师讲规划') THEN '市场私域视频号'
WHEN rule_name LIKE '%语数英%' AND third_department_name = '新媒体内容运营部' THEN '语数英'
WHEN third_department_name='图书营销部' AND (sku_id_name LIKE '%孟亚飞99%' OR sku_id_name LIKE '%亚飞%') THEN '孟亚飞99-2组'
WHEN third_department_name = '投放部' AND ad_account_name LIKE '%周帅%' THEN '信息流-周帅'
WHEN source_manager_name IN ('韩正卿') THEN '抖音私信'
WHEN third_department_name = '私域运营部' AND source_manager_name IN ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研','岳一帆02','田起帆') THEN '进校私域合作'
WHEN channel_name_1='市场私域' AND (virtual_fourth_department_name IN ('郑州学习顾问二部','郑州学习顾问七部','郑州训练营') OR virtual_fifth_department_name IN ('罗江博团队')) THEN '市场私域入群'
WHEN put_plan_name LIKE '%周司鹏%' THEN '品宣组KOC'
WHEN put_plan_name LIKE '%公导私%' AND put_plan_name LIKE '%未购课%' THEN '公导私报名失败'
WHEN third_department_name = '图书营销部' AND rule_name LIKE '%点睛卷%' THEN '押题卷'
WHEN put_plan_name LIKE '%迪九学%' THEN '市场私域代运营'
WHEN third_department_name = '投放部' AND channel_name_2 = '小红书' AND channel_name_1 <> '搜索营销' THEN '信息流-小红书'
WHEN third_department_name = '线上商务部' AND channel_name_2 = '小红书' THEN '小红书'
WHEN (flow_pool_name LIKE '%肖晗%' OR sku_id_name LIKE '%肖晗%' OR put_plan_name LIKE '%肖晗9元%') AND third_department_name='直播部' THEN '肖晗'
WHEN (flow_pool_name LIKE '%北大汤哥%' OR flow_pool_name LIKE '%海淀名师高阶%') AND sku_id_name LIKE '%小艺%' THEN '郭艺'
WHEN third_department_name LIKE '%私域%' AND rule_name LIKE '%私域%' AND rule_name LIKE '%图书%' THEN '市场私域图书'
WHEN third_department_name LIKE '%私域%' AND rule_name LIKE '%品效%' THEN '市场私域品效'
WHEN third_department_name LIKE '%私域%' AND rule_name LIKE '%公域学霸%' THEN '市场私域公域组'
WHEN third_department_name LIKE '%私域%' AND rule_name LIKE '%IE%' THEN '市场私域IE'
WHEN third_department_name LIKE '%私域%' AND rule_name LIKE '%裂变%' THEN '市场私域裂变'
WHEN third_department_name IN ('直播部','新媒体内容运营部','市场一组','私域运营部') AND put_plan_name LIKE '%退%' AND flow_pool_name ='电商退款用户池' THEN '退款订单复用'
WHEN third_department_name IN ('直播部','新媒体内容运营部','市场一组','私域运营部') AND put_plan_name LIKE '%失败%' AND flow_pool_name ='电商退款用户池' THEN '赠课失败'
WHEN third_department_name IN ('直播部','新媒体内容运营部','市场一组') AND (flow_pool_name ='初阶化学规划' OR flow_pool_name LIKE '%启迪-初阶老师%') THEN '曹忆'
WHEN (third_department_name = '图书营销部' AND sku_id_name LIKE '%真题%') OR (third_department_name='直播部' AND sku_id_name LIKE '%真题%') THEN '西安图书直播间-直播'
WHEN (third_department_name = '图书营销部' AND sku_id_name NOT LIKE '%真题%') OR (third_department_name='直播部' AND sku_id_name LIKE '%秒懂%') OR (third_department_name='直播部' AND sku_id_name LIKE '%图书赠送%') THEN '西安图书直播间-挂链'
WHEN rule_name LIKE '%99元智学%' THEN 'AI直播'
WHEN channel_provider_name = '宿迁伯岳' THEN '小程序'
WHEN third_department_name IN ('直播部','新媒体内容运营部','市场一组') AND (flow_pool_name LIKE '%海淀高阶名师%' OR flow_pool_name LIKE '%海淀老师高阶%' OR flow_pool_name LIKE '%小艺%') THEN '郭艺'
WHEN put_plan_name LIKE '%国培教育-0元%' OR put_plan_name LIKE '%易喆教育-0元%' OR put_plan_name LIKE '%钟情-0元%' OR put_plan_name LIKE '%中望达-0元%' OR put_plan_name LIKE '%晨硕-0元%' OR put_plan_name LIKE '%彩石-0元入群%' THEN '创新商务入群'
WHEN put_plan_name LIKE '%0元入群-进校%' AND third_department_name = '线上商务部' THEN '创新商务入群'
WHEN put_plan_name LIKE '%qq0元%' AND third_department_name = '线上商务部' THEN '创新QQ'
WHEN third_department_name='KOC孵化部' AND flow_pool_name LIKE '%电商退款%' AND put_plan_name LIKE '%失败%' THEN '自孵化KOC-赠课失败'
WHEN third_department_name='KOC孵化部' AND flow_pool_name LIKE '%电商退款%' AND put_plan_name LIKE '%退%' THEN '自孵化KOC-退款订单复用'
WHEN source_manager_name = '方俊结01' AND put_plan_name LIKE '%赠课后退款%' THEN 'KOC-赠课后退款'
WHEN third_department_name = '直播部' AND (sku_id_name LIKE '%春春%' OR sku_id_name LIKE '%瑞春%' OR rule_name LIKE '%春春%' OR rule_name LIKE '%瑞春%') THEN '陈瑞春'
WHEN third_department_name = '直播部' AND (sku_id_name LIKE '%朱博士99%' OR rule_name LIKE '%朱汉祺99%') THEN '朱博士99'
WHEN (third_department_name = '直播部' AND (sku_id_name LIKE '%朱博士%' OR sku_id_name LIKE '%朱汉祺%') AND rule_name LIKE '%9%' AND rule_name NOT LIKE '%29%' AND sku_id_name NOT LIKE '%急%' AND sku_id_name NOT LIKE '%礼盒29%') OR (third_department_name = '直播部' AND sku_id_name LIKE '%朱博士9%') THEN '朱博士9元'
WHEN channel_name_1 = '商务' AND channel_name_2 = '短信' THEN '短信'
WHEN ad_account_name LIKE '%肖晗%' AND channel_name_1 = '信息流' THEN '信息流-肖晗'
WHEN channel_name_1 = '信息流' AND channel_name_2='B站' AND (page_id_name LIKE '%亚飞%' OR source_put_plan_name LIKE '%亚飞%' OR rule_name LIKE '%亚飞%' OR page_id_name LIKE '%初中-0元%') THEN 'B站信息流-亚飞'
WHEN channel_name_1 = '信息流' AND (page_id_name LIKE '%亚飞%' OR ad_account_name LIKE '%亚飞%') THEN '信息流-亚飞'
WHEN (flow_pool_name LIKE '%朱博士%' OR flow_pool_name LIKE '%双博士%' OR flow_pool_name LIKE '%教育规划%') AND third_department_name <> '线上商务部' AND period_name NOT LIKE '%多学科拓展%' AND rule_name NOT LIKE '%张杰%' AND sku_id_name NOT LIKE '%马凯鹏IP%' AND third_department_name='直播部' THEN '朱博士29'
WHEN put_plan_name LIKE '%朱博士说教育%' AND period_name NOT LIKE '%多学科拓展%' AND flow_pool_name NOT LIKE '%高分讲堂%' AND flow_pool_name NOT LIKE '%总裁%' AND third_department_name='直播部' THEN '朱博士29'
WHEN flow_pool_name LIKE '%朱博士讲英语%' AND sku_id_name LIKE '%马凯鹏IP%' AND third_department_name='直播部' THEN '马凯鹏29'
WHEN (flow_pool_name LIKE '%朱博士讲英语%' OR flow_pool_name LIKE '%朱博士英语%' OR flow_pool_name LIKE '%朱汉祺说英语%' OR flow_pool_name LIKE '%朱博士说英语%' OR flow_pool_name LIKE '%教育规划%' OR flow_pool_name LIKE '%双博士英语规划%' OR flow_pool_name LIKE '%朱博士满分英语%' OR flow_pool_name LIKE '%英语教父朱博士%' OR (flow_pool_name LIKE '%中考决胜天团%' AND lead_purchase_intention_level1_category_name = '规划系统')) AND third_department_name = '直播部' AND period_name NOT LIKE '%多学科拓展%' AND sku_id_name NOT LIKE '%马凯鹏IP%' AND third_department_name='直播部' THEN '朱博士29'
WHEN (flow_pool_name LIKE '%汤哥%' OR flow_pool_name LIKE '%汤老师%') AND period_name NOT LIKE '%多学科拓展%' AND third_department_name IN ('直播部','新媒体内容运营部') THEN '汤老师'
WHEN (flow_pool_name LIKE '%中考百日冲刺%') AND period_name NOT LIKE '%多学科拓展%' AND third_department_name='直播部' THEN '曹忆9.9纯课'
WHEN (flow_pool_name LIKE '%马总%' OR flow_pool_name = '减法化学马老师' OR flow_pool_name LIKE '%总裁讲化学%' OR flow_pool_name LIKE '%高分讲堂%') AND period_name NOT LIKE '%多学科拓展%' AND sku_id_name LIKE '%99%' AND third_department_name='直播部' THEN '马凯鹏99'
WHEN (flow_pool_name LIKE '%马总%' OR flow_pool_name = '减法化学马老师' OR flow_pool_name LIKE '%总裁讲化学%' OR flow_pool_name LIKE '%高分讲堂%') AND period_name NOT LIKE '%多学科拓展%' AND sku_id_name NOT LIKE '%99%' AND third_department_name='直播部' THEN '马凯鹏29'
WHEN (flow_pool_name LIKE '%北大杰哥%' OR flow_pool_name LIKE '%张小杰%') AND period_name NOT LIKE '%多学科拓展%' AND third_department_name='直播部' THEN '张杰'
WHEN flow_pool_name LIKE '%教育规划%' AND rule_name LIKE '%张杰%' AND third_department_name='直播部' THEN '张杰'
WHEN source_manager_name = '陈晓菁04' AND channel_provider_name NOT LIKE '%开拓%' AND put_plan_name NOT LIKE '%九学%' THEN '商务低价'
WHEN (flow_pool_name LIKE '%孟帝%' OR flow_pool_name LIKE '%孟老师%' OR flow_pool_name LIKE '%中考数学冲刺%' OR flow_pool_name LIKE '%8升9数学%' OR flow_pool_name LIKE '%孟亚飞讲数学%' OR flow_pool_name LIKE '%中考冲刺%' OR flow_pool_name LIKE '%中考满分冲刺%' OR flow_pool_name LIKE '%押题王孟亚飞%' OR flow_pool_name LIKE '%中考数学大通关%' OR flow_pool_name LIKE '%中考数学规划%' OR flow_pool_name LIKE '%亚飞数学%') AND period_name NOT LIKE '%多学科拓展%' AND channel_name_2 NOT LIKE '%KOL%' AND third_department_name='直播部' AND rule_name LIKE '%99%' THEN '孟亚飞99-1组'
WHEN (flow_pool_name LIKE '%孟帝%' OR flow_pool_name LIKE '%孟老师%' OR flow_pool_name LIKE '%中考数学冲刺%' OR flow_pool_name LIKE '%8升9数学%' OR flow_pool_name LIKE '%孟亚飞讲数学%' OR flow_pool_name LIKE '%中考冲刺%' OR flow_pool_name LIKE '%中考满分冲刺%' OR flow_pool_name LIKE '%押题王孟亚飞%' OR flow_pool_name LIKE '%中考数学大通关%' OR flow_pool_name LIKE '%中考数学规划%' OR flow_pool_name LIKE '%亚飞数学%') AND period_name NOT LIKE '%多学科拓展%' AND channel_name_2 NOT LIKE '%KOL%' AND third_department_name='直播部' AND channel_name_2 = '百度' THEN '孟亚飞百度数字人'
WHEN (flow_pool_name LIKE '%孟帝%' OR flow_pool_name LIKE '%孟老师%' OR flow_pool_name LIKE '%中考数学冲刺%' OR flow_pool_name LIKE '%8升9数学%' OR flow_pool_name LIKE '%孟亚飞讲数学%' OR flow_pool_name LIKE '%中考冲刺%' OR flow_pool_name LIKE '%中考满分冲刺%' OR flow_pool_name LIKE '%押题王孟亚飞%' OR flow_pool_name LIKE '%中考数学大通关%' OR flow_pool_name LIKE '%中考数学规划%' OR flow_pool_name LIKE '%亚飞数学%') AND period_name NOT LIKE '%多学科拓展%' AND channel_name_2 NOT LIKE '%KOL%' AND third_department_name='直播部' THEN '孟亚飞9元'
WHEN put_plan_name LIKE '%刘家晋讲图文%' OR put_plan_name LIKE '%孟帝数学%' AND third_department_name='直播部' AND rule_name LIKE '%99%' THEN '孟亚飞99-1组'
WHEN put_plan_name LIKE '%刘家晋讲图文%' OR put_plan_name LIKE '%孟帝数学%' AND third_department_name='直播部' THEN '孟亚飞9元'
WHEN (flow_pool_name LIKE '%肖晗%' OR sku_id_name LIKE '%肖晗%') AND third_department_name='直播部' THEN '肖晗'
WHEN flow_pool_name LIKE '%峥峥%' AND period_name NOT LIKE '%多学科拓展%' AND third_department_name='直播部' THEN '何峥峥'
WHEN flow_pool_name LIKE '%汐子%' AND period_name NOT LIKE '%多学科拓展%' AND sku_id_name NOT LIKE '%亚飞%' AND third_department_name='直播部' THEN '王汐子'
WHEN flow_pool_name LIKE '%汐子%' AND period_name NOT LIKE '%多学科拓展%' AND sku_id_name LIKE '%亚飞%' AND third_department_name='直播部' AND rule_name LIKE '%99%' THEN '孟亚飞99-1组'
WHEN flow_pool_name LIKE '%汐子%' AND period_name NOT LIKE '%多学科拓展%' AND sku_id_name LIKE '%亚飞%' AND third_department_name='直播部' THEN '孟亚飞9元'
WHEN (flow_pool_name LIKE '%曹忆%' OR flow_pool_name LIKE '%dudu%' OR flow_pool_name LIKE '%中考决胜天团%' OR flow_pool_name LIKE '%具象思维%' OR flow_pool_name LIKE '%在逃发面馒头%' OR flow_pool_name LIKE '%库洛米%' AND lead_purchase_intention_level1_category_name <> '规划系统') AND period_name NOT LIKE '%多学科拓展%' AND third_department_name IN ('直播部','新媒体内容运营部') THEN '曹忆'
WHEN flow_pool_name = '正价课判单补录' THEN '正价课判单补录'
WHEN channel_name_1 = '转介绍' THEN '转介绍'
WHEN first_department_name ='市场部' AND channel_name_1 <> '站内获客' AND channel_name_2 <> 'APP' THEN '集团私域'
WHEN put_plan_name LIKE '%未加好友%' THEN '市场私域未加好友'
WHEN put_plan_name LIKE '%私域-信息流%' THEN '市场私域待支付'
WHEN third_department_name = '私域运营部' AND rule_name NOT LIKE '%训练营%' AND virtual_fifth_department_name NOT IN ('罗江博团队') AND rule_name NOT LIKE '%复用%' AND rule_name NOT LIKE '%未加好友%' AND channel_name_2 <> '内部换量' THEN '市场私域低价单'
WHEN third_department_name = '私域运营部' AND rule_name NOT LIKE '%训练营%' AND rule_name NOT LIKE '%复用%' AND rule_name NOT LIKE '%未加好友%' AND channel_name_2 <> '内部换量' AND flow_original_order_activity_price = '0.0' THEN '市场私域低价单'
WHEN third_department_name = '私域运营部' AND channel_name_1 = '信息流获客' THEN '市场私域小红书'
WHEN channel_name_1= '信息流' AND (put_plan_name LIKE '%抖音私信%' OR put_plan_name LIKE '%初三0元%' OR put_plan_name LIKE '%高中0元%') THEN '信息流-抖音私信'
WHEN channel_name_2 IN ('APP','M站','PC') AND flow_pool_name NOT LIKE '%途途%' THEN 'APP'
WHEN source_manager_name IN ('高文羽') AND lead_purchase_intention_name = 'AI定制' THEN '人工外呼-AI'
WHEN channel_provider_name LIKE '%唐山TMK%' THEN '唐山TMK'
WHEN source_manager_name IN ('高文羽') AND channel_provider_name NOT LIKE '%唐山TMK%' AND channel_provider_name NOT LIKE '%郑州%' THEN '人工外呼'
WHEN source_manager_name IN ('高文羽') AND channel_provider_name NOT LIKE '%唐山TMK%' AND channel_provider_name LIKE '%郑州%' THEN '郑州TMK-2组'
WHEN source_manager_name = '冯银晨' AND channel_name_2 = '小红书' THEN '信息流-小红书'
WHEN channel_name_1 = '信息流获客' AND flow_original_order_activity_price LIKE '%1990%' THEN '信息流19'
WHEN (channel_name_1 = '信息流' AND channel_name_2 <> 'B站' AND third_department_name NOT LIKE '%商务%' AND put_plan_name NOT LIKE '%初三0元%' AND put_plan_name NOT LIKE '%抖音私信%' AND put_plan_name NOT LIKE '%高中0元%' AND flow_original_order_activity_price NOT LIKE '%1990%') OR (channel_name_2 = 'B站' AND third_department_name LIKE '%投放%') THEN '信息流'
WHEN channel_name_1 = '信息流' AND channel_name_2 = 'B站' AND third_department_name NOT LIKE '%投放%' AND (page_id_name LIKE '%郭艺%') THEN 'B站信息流-郭艺'
WHEN channel_name_1 = '信息流' AND channel_name_2 = 'B站' AND third_department_name NOT LIKE '%投放%' AND (page_id_name LIKE '%朱博士%') THEN 'B站信息流-朱汉祺'
WHEN channel_name_1 = '信息流' AND channel_name_2 = 'B站' AND third_department_name NOT LIKE '%投放%' AND page_id_name LIKE '%肖晗%' THEN 'B站信息流-肖晗'
WHEN channel_name_1 = '信息流' AND channel_name_2 = 'B站' AND third_department_name NOT LIKE '%投放%' AND (page_id_name LIKE '%马凯鹏%' OR ad_account_name LIKE '%化学%') THEN 'B站信息流-马凯鹏'
WHEN channel_name_1 = '信息流' AND channel_name_2 = 'B站' AND third_department_name NOT LIKE '%投放%' AND (sku_id_name LIKE '%陈瑞春%' OR rule_name LIKE '%陈瑞春%') AND (ad_account_name LIKE '%语文%' OR source_put_plan_name LIKE '%自然流%' OR page_id_name LIKE '%春春%') THEN 'B站信息流-陈瑞春'
WHEN channel_name_1 = '信息流' AND channel_name_2 = 'B站' AND third_department_name NOT LIKE '%投放%' AND (flow_original_order_activity_price LIKE '%2990%' OR sku_id_name LIKE '%帅师%' OR sku_id_name LIKE '%周帅%') AND ad_account_name LIKE '%语文%' AND (flow_original_order_activity_price LIKE '%1980%' OR flow_original_order_activity_price LIKE '%2980%' OR flow_original_order_activity_price LIKE '%2990%') THEN 'B站信息流-陈瑞春'
WHEN channel_name_1 = '信息流' AND channel_name_2 = 'B站' AND third_department_name NOT LIKE '%投放%' AND (flow_original_order_activity_price LIKE '%2990%' OR sku_id_name LIKE '%帅师%' OR sku_id_name LIKE '%周帅%') AND ad_account_name NOT LIKE '%语文%' THEN 'B站信息流-周帅'
WHEN channel_name_1 = '信息流' AND channel_name_2 = 'B站' AND third_department_name NOT LIKE '%投放%' AND flow_order_price LIKE '%1980%' AND ad_account_name LIKE '%数学%' THEN 'B站信息流-周帅'
WHEN channel_name_1 = '短直电商' AND channel_name_2 = 'B站' AND third_department_name LIKE '%商务%' AND sku_id_name LIKE '%陈瑞春%' AND flow_pool_name LIKE '%自然流%' THEN 'B站信息流-陈瑞春'
WHEN channel_name_1 = '短直电商' AND channel_name_2 = 'B站' AND third_department_name LIKE '%商务%' AND sku_id_name LIKE '%朱博士%' AND flow_pool_name LIKE '%自然流%' THEN 'B站信息流-朱汉祺'
WHEN third_department_name = '线上商务部' AND channel_name_2 = 'B站' AND put_plan_name LIKE '%春春%' THEN 'B站信息流-陈瑞春'
WHEN third_department_name = '线上商务部' AND channel_name_2 = 'B站' AND put_plan_name LIKE '%朱博士%' THEN 'B站信息流-朱汉祺'
WHEN channel_name_1 = '信息流' AND channel_name_2 = 'B站' AND third_department_name NOT LIKE '%投放%' AND flow_original_order_activity_price NOT LIKE '%2980%' AND flow_original_order_activity_price NOT LIKE '%2990%' AND flow_original_order_activity_price NOT LIKE '%1980%' THEN 'B站信息流'
WHEN flow_pool_name = '百度搜索引擎' OR channel_name_1='搜索营销' THEN '信息流搜索'
WHEN channel_name_1 = '信息流获客' AND channel_name_2 = '小红书' AND source_manager_name IN ('王慧敏13','张琳02','王樱琦01') THEN '小红书投放'
WHEN flow_pool_name LIKE '%小红书班课%' THEN '小红书投放'
WHEN third_department_name = '投放部' AND get_customer_way_name = '短视频信息流' AND flow_original_order_activity_price LIKE '%100%' THEN '信息流'
WHEN source_manager_name IN ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') AND (sku_id_name LIKE '%原型题%') THEN 'KOC-书课包'
WHEN flow_pool_name = '中考加油' AND sku_id_name LIKE '%孟帝%' THEN 'KOC-孟亚飞数学'
WHEN flow_pool_name = '中考加油' AND sku_id_name LIKE '%帅师%' THEN 'KOC-周帅数学'
WHEN flow_pool_name = '中考加油' AND sku_id_name LIKE '%肖晗%' THEN 'KOC-肖晗'
WHEN source_manager_name IN ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') AND (sku_id_name LIKE '%孟帝%' OR sku_id_name LIKE '%dudu%' OR sku_id_name LIKE '%市场初二%' OR rule_name LIKE '%亚飞%' OR sku_id_name LIKE '%初二高阳%' OR sku_id_name LIKE '%高阳初二%' OR sku_id_name LIKE '%精品初二%' OR sku_id_name LIKE '%菁英初三%' OR (virtual_second_department_name = '菁英班学部' AND lead_purchase_intention_level2_category_name='初级' AND lead_create_time>= '2026-04-15 00:00:00')) THEN 'KOC-孟亚飞数学'
WHEN source_manager_name IN ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') AND (sku_id_name LIKE '%帅师%' OR rule_name LIKE '%周帅%') THEN 'KOC-周帅数学'
WHEN source_manager_name IN ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') AND (sku_id_name LIKE '%肖晗%' OR rule_name LIKE '%肖晗%') THEN 'KOC-肖晗'
WHEN source_manager_name IN ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') AND period_name NOT LIKE '%多学科拓展%' AND (flow_original_order_activity_price LIKE '%1100%' OR flow_original_order_activity_price LIKE '%500%' OR flow_orders_income_amount LIKE '%500%') AND (sku_id_name LIKE '%朱汉祺%' OR sku_id_name LIKE '%朱博士%' OR rule_name LIKE '%朱汉祺5元%' OR sku_id_name LIKE '%koc5元-朱博士%' OR rule_name LIKE '%朱汉祺%') THEN 'KOC-5元朱汉祺'
WHEN source_manager_name IN ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') AND (sku_id_name LIKE '%朱汉祺%' OR sku_id_name LIKE '%29元%' OR sku_id_name LIKE '%朱博士%' OR rule_name LIKE '%朱汉祺%' OR rule_name LIKE '%朱博士%' ) AND (flow_original_order_activity_price NOT LIKE '%1100%' OR rule_name LIKE '%29%') AND sku_id_name NOT LIKE '%周帅%' THEN 'KOC-5元朱汉祺'
WHEN source_manager_name IN ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') AND period_name NOT LIKE '%多学科拓展%' AND sku_id_name NOT LIKE '%朱汉祺%' AND sku_id_name NOT LIKE '%朱博士%' AND sku_id_name NOT LIKE '%周帅%' AND sku_id_name NOT LIKE '%29元%' THEN 'KOC-5元纯课'
WHEN source_manager_name IN ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') AND sku_id_name LIKE '%周帅%' THEN 'KOC-周帅'
WHEN third_department_name IN ('品牌效能部','KOC孵化部') AND channel_name_2 IN ('抖音','视频号','快手','KOL') THEN '自孵化KOC-5元纯课'
WHEN third_department_name IN ('品牌效能部','KOC孵化部') AND channel_name_2 IN ('抖音','视频号','快手','KOL') AND (sku_id_name LIKE '%5元%'OR sku_id_name LIKE '%11元%' OR flow_original_order_activity_price LIKE '%1100%' OR flow_original_order_activity_price LIKE '%500%' OR flow_orders_income_amount LIKE '%1100%' OR flow_orders_income_amount LIKE '%500%' ) THEN '自孵化KOC-5元纯课'
WHEN source_manager_name IN ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') AND channel_name_2 LIKE '%社群%' THEN '进校社群'
WHEN source_manager_name IN ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') AND channel_name_2 LIKE '%TMK%' AND page_id_name LIKE '%1元%' THEN '进校TMK1元'
WHEN source_manager_name IN ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') AND channel_name_2 LIKE '%TMK%' AND page_id_name LIKE '%9元%' THEN '进校TMK9元'
WHEN source_manager_name IN ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') AND channel_name_2 LIKE '%书商%' THEN '进校书商'
WHEN source_manager_name IN ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') AND channel_name_2 LIKE '%综合%' AND put_plan_name LIKE '%18%' THEN '进校直播'
WHEN source_manager_name IN ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') AND channel_name_2 LIKE '%直播%' THEN '进校直播'
WHEN source_manager_name IN ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04') AND put_plan_name NOT LIKE '%0元%' AND flow_pool_name NOT LIKE '%家校共育%' AND flow_pool_name NOT LIKE '%保持热爱%' AND flow_pool_name NOT LIKE '%青松%' AND flow_pool_name NOT LIKE '%原子初三%' AND flow_pool_name NOT LIKE '%南通欣创%' AND flow_pool_name NOT LIKE '%悟之道%' AND flow_pool_name NOT LIKE '%济南梦航%' AND channel_name_3 <> '社群' AND put_plan_name NOT LIKE '%善悟%' AND put_plan_name NOT LIKE '%人人通%' AND put_plan_name NOT LIKE '%%济南格乐' AND flow_pool_name NOT LIKE '%晨硕智学%' AND flow_pool_name NOT LIKE '%兴尧文化%' AND flow_pool_name NOT LIKE '%济南映像%' AND flow_pool_name NOT LIKE '%山东简单%' AND flow_pool_name NOT LIKE '%争鸣科技%' THEN '商务低价'
WHEN flow_pool_name LIKE '%原子初三%' OR flow_pool_name LIKE '%原子系统%' THEN '原子'
WHEN flow_pool_name LIKE '%市场部-公转私%' THEN '市场私域公导私'
WHEN flow_pool_name LIKE '%南通欣创%' OR flow_pool_name LIKE '%人人通科技%' OR flow_pool_name LIKE '%易而购%' OR flow_pool_name LIKE '%济南梦航%' OR flow_pool_name LIKE '%晨硕智学%' OR flow_pool_name LIKE '%兴尧文化%' OR flow_pool_name LIKE '%济南映像%' OR flow_pool_name LIKE '%山东简单%' OR flow_pool_name LIKE '%争鸣科技%' THEN '进校私域合作'
WHEN (flow_pool_name LIKE '%家校共育%' OR flow_pool_name LIKE '%保持热爱%' OR flow_pool_name LIKE '%青松%' OR flow_pool_name LIKE '%悟之道%') AND put_plan_name NOT LIKE '%0元%' THEN '进校私域合作'
WHEN source_manager_name = '李宁24' AND put_plan_name LIKE '%0转低%' THEN '进校私域合作'
WHEN third_department_name = '私域运营部' AND flow_original_order_activity_price IN ('100.0','900.0','300.0') THEN '进校私域合作'
WHEN third_department_name = '私域运营部' AND flow_original_order_activity_price IN ('0.0') AND source_manager_name IN ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研') THEN '进校私域合作'
WHEN third_department_name = '私域运营部' AND channel_name_1='市场私域' AND put_plan_name NOT LIKE '%公导私%' AND put_plan_name NOT LIKE '%公转私%' AND flow_original_order_activity_price = '0.0' AND rule_name NOT LIKE '%激活%' AND rule_name NOT LIKE '%咨询%' AND rule_name NOT LIKE '%训练营%' AND virtual_fifth_department_name NOT LIKE '%罗江博%' AND virtual_fifth_department_name NOT LIKE '%郑州学习顾问二部%' AND source_manager_name NOT IN ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研') THEN '市场私域低价单'
WHEN flow_pool_name LIKE '%青岛寻知%' OR flow_pool_name LIKE '%禾兴信息%' THEN '商务0元'
WHEN put_plan_name LIKE '%益企发1元%' OR put_plan_name LIKE '%腾瑞教育1元%' THEN '进校APP合作'
WHEN put_plan_name LIKE '%外部图书供量%' OR flow_pool_name='高途旗舰店—线索—yuxinru' THEN '外部图书慧敏'
WHEN source_manager_name IN ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') AND channel_name_2 LIKE '%社群%' THEN '创新社群'
WHEN source_manager_name IN ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') AND (channel_name_2 LIKE '%直推%' OR put_plan_name LIKE '%直推%') THEN '创新直推'
WHEN source_manager_name IN ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') AND (channel_name_2 LIKE '%书商%' OR put_plan_name LIKE '%书商%' OR page_id_name LIKE '%书商%') THEN '创新书商'
WHEN source_manager_name IN ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') AND channel_name_2 LIKE '%TMK%' AND page_id_name LIKE '%1元%' THEN '创新TMK1元'
WHEN source_manager_name IN ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') AND channel_name_2 LIKE '%TMK%' AND page_id_name LIKE '%9元%' THEN '创新TMK9元'
WHEN source_manager_name IN ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') AND (channel_name_2 LIKE '%直播%' OR page_id_name LIKE '%进校%') THEN '创新直播'
WHEN source_manager_name IN ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') AND channel_name_2<>'公众号' AND channel_name_1 = '商务' AND flow_pool_name <> '高途云集图书专营店-自然流' AND flow_pool_name <> '高途旗舰店—线索—yuxinru' AND put_plan_name NOT LIKE '%社群%' AND put_plan_name NOT LIKE '%小红书班课%' AND put_plan_name NOT LIKE '%外部图书供量%' AND channel_second_provider_name NOT LIKE '%沃德丰店铺线索赠课%' AND channel_second_provider_name NOT LIKE '%智慧城-图书%' AND put_plan_name NOT LIKE '%育甲%' AND flow_pool_name NOT LIKE '%周长磊%' THEN '创新商务'
WHEN flow_pool_name LIKE '%周长磊%' THEN '创新APP'
WHEN channel_provider_name LIKE '%唐成刚%' OR flow_pool_name = '高途云集图书专营店-自然流' THEN '图书唐成刚'
WHEN channel_second_provider_name LIKE '%沃德丰店铺线索赠课%' OR channel_second_provider_name LIKE '%智慧城-图书%' OR put_plan_name LIKE '%育甲%' THEN '外部图书慧敏'
WHEN flow_pool_name LIKE '%高途图书产品学部%' THEN '图书任炯旭'
WHEN source_manager_name IN ('王春宵') THEN '武汉图书直播间'
WHEN source_manager_name IN ('高曼曼01','杨思怡','宋向函') THEN '图书KOC达人'
WHEN flow_pool_name LIKE '%高中视频书%' OR flow_pool_name LIKE '%高中教辅书%' OR flow_pool_name LIKE '%朵拉老师%' THEN '北京图书直播间'
WHEN flow_pool_name LIKE '%市场部-原子合作%' THEN '原子'
WHEN flow_pool_name LIKE '%市场部-微信私域%' OR flow_pool_name LIKE '%市场部-规划报告%' OR flow_pool_name LIKE '%规划报告%' OR flow_pool_name LIKE '%市场部-小红书%' OR flow_pool_name LIKE '%孟浩宇%' THEN '市场私域低价单'
WHEN flow_pool_name LIKE '%待支付%' THEN '市场私域待支付'
WHEN flow_pool_name LIKE '%未加好友%' THEN '市场私域未加好友'
WHEN flow_pool_name LIKE '%内部换量%' THEN '市场私域首期掉海'
WHEN flow_pool_name LIKE '公导私' THEN '进校私域合作'
WHEN source_manager_name IN ('方宇02','李月林') THEN '菁英市场流量'
WHEN channel_name_2 = '公众号' THEN '公众号'
WHEN (flow_pool_name LIKE '%增长组%' OR channel_name_3 = '公众号' OR second_department_name = '微信生态部') AND channel_name_2 <> 'APP' THEN '集团私域'
WHEN put_plan_name LIKE '%济南格乐%' AND put_plan_name LIKE '%表单%' THEN '商务0元'
WHEN put_plan_name LIKE '%B类%' OR put_plan_name LIKE '%b类%' OR channel_second_provider_name LIKE '%KOC当期%' THEN 'KOC分层测试'
WHEN put_plan_name LIKE '%星耀%' OR put_plan_name LIKE '%物理展博%' OR put_plan_name LIKE '%物理谢丽荣%' OR put_plan_name LIKE '%牟恩伯%' OR put_plan_name LIKE '%王赞%' OR put_plan_name LIKE '%张磊老师高中数学%' OR put_plan_name LIKE '%雯姐高中物理大讲堂%' THEN '百度星耀'
WHEN source_manager_name = '刘福云' AND (sku_id_name LIKE '%瑞春%' OR sku_id_name LIKE '%春春%') THEN '陈瑞春'
WHEN source_manager_name = '刘福云' AND sku_id_name LIKE '%周帅%' THEN '周帅'
WHEN third_department_name = '直播部' AND sku_id_name LIKE '%周帅%' AND channel_name_2 IN ('百度','B站') THEN '周帅-百度数字人'
WHEN third_department_name = '直播部' AND sku_id_name LIKE '%孟亚飞%' AND sku_id_name LIKE '%199%' THEN '孟亚飞199'
WHEN third_department_name = '直播部' AND sku_id_name LIKE '%孟亚飞%' AND rule_name LIKE '%99%' THEN '孟亚飞99-1组'
WHEN third_department_name = '直播部' AND sku_id_name LIKE '%孟亚飞%' THEN '孟亚飞9元'
WHEN third_department_name = '直播部' AND sku_id_name LIKE '%朱汉祺%' THEN '朱博士29'
WHEN third_department_name = '直播部' AND sku_id_name LIKE '%肖晗%' THEN '肖晗'
WHEN flow_pool_name LIKE '%0转低转正%' OR channel_name_2='产研测试' THEN '进校私域合作'
WHEN source_manager_name IN ('陈甜06','梁晓敏') THEN '图书挂车'
WHEN flow_pool_name LIKE '%天津智慧双子%' THEN '创新社群'
WHEN third_department_name LIKE '%城市定制%' THEN '点睛卷'
WHEN first_department_name LIKE '%KM%' AND flow_pool_name NOT LIKE '%天津智慧双子%' THEN '途途商务'
WHEN period_name LIKE '%多学科拓展%' AND third_department_name LIKE '%私域运营%' THEN '市场私域入群'
WHEN put_plan_name LIKE '%赠课失败%' AND third_department_name = '线上商务部' THEN 'KOC赠课失败'
WHEN flow_pool_name LIKE '%自然流%' AND source_manager_name IN ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') AND sku_id_name LIKE '%周帅%' THEN 'KOC-周帅'
WHEN flow_pool_name LIKE '%自然流%' AND source_manager_name IN ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') AND sku_id_name LIKE '%肖晗%' THEN 'KOC-肖晗'
WHEN flow_pool_name LIKE '%自然流%' AND source_manager_name IN ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') AND sku_id_name LIKE '%朱汉祺%' AND flow_original_order_activity_price LIKE '%1100%' THEN 'KOC-5元朱汉祺'
WHEN flow_pool_name LIKE '%自然流%' AND source_manager_name IN ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') AND sku_id_name LIKE '%朱汉祺%' AND flow_original_order_activity_price NOT LIKE '%1100%' THEN 'KOC-朱汉祺29'
WHEN flow_pool_name LIKE '%自然流%' AND source_manager_name IN ('赵语诗','崔文轩','孙培尧') THEN '自孵化KOC-5元纯课'
WHEN flow_pool_name LIKE '%自然流%' AND (sku_id_name LIKE '%朱博士%' OR sku_id_name LIKE '%朱汉祺%') AND rule_name LIKE '%9%' AND rule_name NOT LIKE '%29%' AND third_department_name IN ('直播部','新媒体内容运营部','市场一组') THEN '朱博士9元'
WHEN flow_pool_name LIKE '%自然流%' AND sku_id_name LIKE '%朱博士%' AND third_department_name IN ('直播部','新媒体内容运营部','市场一组') THEN '朱博士29'
WHEN flow_pool_name LIKE '%自然流%' AND sku_id_name LIKE '%亚飞%' AND rule_name LIKE '%99%' AND third_department_name IN ('直播部','新媒体内容运营部','市场一组') THEN '孟亚飞99-1组'
WHEN flow_pool_name LIKE '%自然流%' AND sku_id_name LIKE '%亚飞%' AND third_department_name IN ('直播部','新媒体内容运营部','市场一组') THEN '孟亚飞9元'
WHEN flow_pool_name LIKE '%自然流%' AND sku_id_name LIKE '%曹忆%' THEN '曹忆'
WHEN flow_pool_name LIKE '%自然流%' AND rule_name LIKE '%朱博士%' AND third_department_name IN ('直播部','新媒体内容运营部','市场一组') THEN '朱博士29'
WHEN flow_pool_name LIKE '%自然流%' AND source_manager_name LIKE '%邵万昕%' AND third_department_name IN ('直播部','新媒体内容运营部','市场一组') THEN '朱博士29'
WHEN flow_pool_name LIKE '%自然流%' AND rule_name LIKE '%亚飞%' AND rule_name LIKE '%99%' THEN '孟亚飞99-1组'
WHEN flow_pool_name LIKE '%自然流%' AND rule_name LIKE '%亚飞%' THEN '孟亚飞9元'
WHEN flow_pool_name LIKE '%自然流%' AND rule_name LIKE '%曹忆%' THEN '曹忆'
WHEN flow_pool_name LIKE '%途途教室%' OR first_department_name LIKE 'TUTU' THEN '途途APP'
WHEN second_department_name = '市场二部' AND get_customer_way_name = 'KOL直播' THEN '市场二部KOC'
WHEN second_department_name = '市场四部' THEN '市场四部'
WHEN source_manager_name IN ('宋莹莹','辛世如') AND channel_name_2 IN ('视频号') THEN '信息流-虚拟号挂车'
WHEN put_plan_name LIKE '%高三复读%' THEN '市场私域高三复读'
WHEN put_plan_name ='美玲测试' THEN '途途信息流私信'
WHEN rule_name LIKE '%训练营%' AND rule_name LIKE '%市场私域%' THEN '市场私域入群'
WHEN flow_pool_name LIKE '%青少-私域%' THEN '青少私域'
WHEN first_department_name = 'TT业务线' AND third_department_name LIKE '%商务招生%' THEN '途途商务'
WHEN second_department_name = '战略客户部' THEN '文旅进校'
WHEN put_plan_name LIKE '%AI名师%' THEN 'AI直播'
WHEN rule_name LIKE '%途途私域%' OR (rule_name LIKE '%私域%' AND first_department_name = 'TT') THEN '途途私域'
ELSE '其他未知流量' END AS channel_map,
        CASE
            WHEN rule_name LIKE '%初二%' THEN '初二'
            WHEN rule_name LIKE '%初三%' THEN '初三'
            WHEN rule_name LIKE '%高一%' THEN '高一'
            WHEN rule_name LIKE '%高二%' THEN '高二'
            WHEN rule_name LIKE '%高三%' THEN '高三'
            ELSE lead_purchase_intention_level2_category_name
        END AS grade_name,
        lead_count,
        valid_lead_count,
        conversion_lead_count,
        order_count,
        income_amount,
        in_pay_period_refund_amount,
        non_pay_period_refund_amount,
        friend_lead_count
    FROM lead_raw
),
private_stage AS (
    SELECT
        y.user_id,
        y.lead_id,
        y.sale_flow_stage_sequence
    FROM (
        SELECT
            t.user_number AS user_id,
            t.lead_id,
            t.sale_flow_stage_sequence,
            ROW_NUMBER() OVER (
                PARTITION BY t.user_number, t.lead_id
                ORDER BY t.private_sea_update_time DESC
            ) AS rn
        FROM service_dw.dwd_crm_assign_private_detail_hf t
        WHERE t.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
          AND t.hour = format_datetime(now() - interval '2' hour, 'HH')
          AND t.assign_employee_first_level_department_name = 'H业务线'
          AND t.assign_employee_second_level_department_name = '市场部'
          AND t.assign_employee_third_level_department_name = '市场顾问部'
    ) y
    WHERE y.rn = 1
),
profile_base AS (
    SELECT
        b.period_name,
        b.channel_map,
        b.grade_name,
        b.depart_1,
        b.dept_name,
        b.depart,
        b.jingli,
        b.zhuguan,
        b.employee_email_name,
        b.lead_id,
        b.user_id,
        b.lead_count,
        b.valid_lead_count,
        b.conversion_lead_count,
        b.order_count,
        b.income_amount,
        b.in_pay_period_refund_amount,
        b.non_pay_period_refund_amount,
        CASE
            WHEN cast(ps.sale_flow_stage_sequence AS varchar) = '470' THEN '双沟'
            WHEN cast(ps.sale_flow_stage_sequence AS varchar) = '450' THEN '深沟'
            WHEN coalesce(b.friend_lead_count, 0) > 0 THEN '已建联'
            ELSE '新线索'
        END AS deep_communication_bucket,
        CASE
            WHEN cast(ps.sale_flow_stage_sequence AS varchar) = '470' THEN 4
            WHEN cast(ps.sale_flow_stage_sequence AS varchar) = '450' THEN 3
            WHEN coalesce(b.friend_lead_count, 0) > 0 THEN 2
            ELSE 1
        END AS deep_communication_bucket_sort
    FROM lead_base b
    LEFT JOIN private_stage ps
      ON cast(ps.user_id AS varchar) = cast(b.user_id AS varchar)
     AND cast(ps.lead_id AS varchar) = cast(b.lead_id AS varchar)
),
-- ============================================================
-- ★ 新增：分母 CTE —— 从 profile_base（UNION ALL 之前）独立计算
--    每个 (period, channel, grade) 的总线索 / 总有效线索
-- ============================================================
dim_totals AS (
    SELECT
        period_name,
        channel_map,
        grade_name,
        SUM(CASE WHEN lead_count > 0 THEN lead_count ELSE 0 END) AS total_leads,
        SUM(CASE WHEN valid_lead_count > 0 THEN valid_lead_count ELSE 0 END) AS total_valid_leads
    FROM profile_base
    GROUP BY period_name, channel_map, grade_name
),
-- ============================================================
-- 深沟阶段数据集只保留沟通阶段口径，不再混入通时/上课时长口径
-- ============================================================
profile_union AS (
    SELECT period_name, channel_map, grade_name,
        '是否深沟成单用户占比' AS analysis_type,
        deep_communication_bucket AS bucket_name,
        deep_communication_bucket_sort AS bucket_sort,
        user_id, lead_id, lead_count, valid_lead_count, conversion_lead_count,
        order_count, income_amount, in_pay_period_refund_amount, non_pay_period_refund_amount
    FROM profile_base
),
-- ============================================================
-- ★ 核心修改：按沟通阶段 bucket 粒度聚合
-- ============================================================
profile_agg AS (
    SELECT
        period_name,
        channel_map,
        grade_name,
        analysis_type,
        bucket_name,
        bucket_sort,
        -- 对应区间人数：使用宽表可加线索指标，避免 distinct user 预聚合后跨渠道/年级重复相加
        SUM(CASE WHEN lead_count > 0 THEN lead_count ELSE 0 END) AS bucket_user_count,
        -- 对应区间有效线索数：保留给需要用有效线索做分母的透视表公式
        SUM(CASE WHEN valid_lead_count > 0 THEN valid_lead_count ELSE 0 END) AS bucket_valid_lead_count,
        -- 转化人头：使用宽表可加转化指标，保持与 CRM 归因口径一致
        SUM(CASE WHEN conversion_lead_count > 0 THEN conversion_lead_count ELSE 0 END) AS conversion_user_count,
        -- 订单数
        SUM(CASE WHEN lead_count > 0 THEN order_count ELSE 0 END) AS positive_course_order_count,
        -- 收款（元）
        SUM(CASE WHEN lead_count > 0 THEN income_amount ELSE 0 END) / 100.0 AS trade_income,
        -- 净营收（元）
        SUM(CASE WHEN lead_count > 0 THEN income_amount - in_pay_period_refund_amount - non_pay_period_refund_amount ELSE 0 END) / 100.0 AS section_trade_profit
    FROM profile_union
    GROUP BY period_name, channel_map, grade_name, analysis_type, bucket_name, bucket_sort
),
channel_group AS (
    SELECT channel, MAX(channel_group) AS channel_group
    FROM temp_table.shenbaoxin_channel_group
    GROUP BY channel
)
SELECT
    a.period_name,
    a.channel_map,
    cg.channel_group,
    a.grade_name,
    a.analysis_type,
    a.bucket_name,
    a.bucket_sort,
    CAST(a.bucket_user_count AS bigint) AS bucket_user_cnt,
    CAST(a.bucket_valid_lead_count AS bigint) AS bucket_valid_lead_cnt,
    CAST(dt.total_leads AS bigint) AS total_lead_cnt,
    CAST(dt.total_valid_leads AS bigint) AS total_valid_lead_cnt,
    CAST(
        CASE
            WHEN a.bucket_sort = min(a.bucket_sort) OVER (PARTITION BY a.period_name, a.channel_map, a.grade_name, a.analysis_type)
            THEN dt.total_leads
            ELSE 0
        END AS bigint
    ) AS total_lead_cnt_once,
    CAST(
        CASE
            WHEN a.bucket_sort = min(a.bucket_sort) OVER (PARTITION BY a.period_name, a.channel_map, a.grade_name, a.analysis_type)
            THEN dt.total_valid_leads
            ELSE 0
        END AS bigint
    ) AS total_valid_lead_cnt_once,
    CAST(a.conversion_user_count AS bigint) AS conversion_user_cnt,
    CAST(a.positive_course_order_count AS bigint) AS order_cnt,
    CAST(a.trade_income AS double) AS trade_income_amt,
    CAST(a.section_trade_profit AS double) AS section_profit_amt,
    ROUND(CAST(a.conversion_user_count AS double) / NULLIF(a.bucket_user_count, 0), 6) AS head_conversion_rate,
    ROUND(CAST(a.positive_course_order_count AS double) / NULLIF(a.bucket_user_count, 0), 6) AS order_conversion_rate,
    ROUND(CAST(a.section_trade_profit AS double) / NULLIF(a.bucket_user_count, 0), 6) AS section_unit_efficiency
FROM profile_agg a
LEFT JOIN channel_group cg ON cg.channel = a.channel_map
LEFT JOIN dim_totals dt
    ON dt.period_name = a.period_name
   AND dt.channel_map  = a.channel_map
   AND dt.grade_name   = a.grade_name
WHERE a.period_name > '20260417期'
  AND a.analysis_type = '是否深沟成单用户占比'
