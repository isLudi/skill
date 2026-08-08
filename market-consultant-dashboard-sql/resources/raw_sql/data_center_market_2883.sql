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
            ('market_consultant', 'lead_period', '20260808期', date '2026-08-07', date '2026-08-12', 1),
            ('market_consultant', 'lead_period', '20260815期', date '2026-08-13', date '2026-08-18', 1),
            ('market_consultant', 'class_period', '20260808期', date '2026-08-07', date '2026-08-12', 1),
            ('market_consultant', 'class_period', '20260815期', date '2026-08-13', date '2026-08-18', 1),
            ('market_consultant', 'trade_period', '20260808期', date '2026-08-07', date '2026-08-12', 1),
            ('market_consultant', 'trade_period', '20260815期', date '2026-08-13', date '2026-08-18', 1)
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
        t1.trace_type_name,
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
        CASE
-- 2026-08-02/01: preserve the two confirmed Data Center-only refund-reuse overrides before shared channel rules.
when period_name = '20260728期'
 and third_department_name = '线上商务部'
 and flow_pool_name = '电商退款用户池'
 and put_plan_name = '0728期退款用户计划'
 and channel_name_1 = '内部'
 and channel_name_2 = '流量复用'
 and source_manager_name = '曲默晗'
 and sku_id_name like '0728期-%帅师%'
then '退款订单复用'
when period_name = '20260803期'
 and third_department_name = '线上商务部'
 and source_manager_name in ('曲默晗','何木玲')
 and sku_id_name like '0728期-%'
 and (sku_id_name like '%帅师%' or sku_id_name like '%孟帝%')
then '退款订单复用'
-- 【区域定向】
   when get_customer_way_name in ('平台自播') and flow_pool_name in ('赢战广东中考','高途专版图书','状元帮教辅','高途专版视频书','本地化专版图书') then '广东图书'
   when get_customer_way_name in ('平台自播') and flow_pool_name in ('途铭文化专版图书','途铭文化','博慧星辰文化图书','启迪蔚来','智慧航迹图书','高途浙江初中','高途浙江高中','高途浙江新高一') then '浙江图书'
   when get_customer_way_name in ('平台自播') and flow_pool_name in ('沪上名校','沪上领航社','简学文化','魔都校友助学馆','沪上领航高中','沪上领航初中') then '上海图书'
   when get_customer_way_name in ('平台自播') and flow_pool_name in ('高途江苏中考','高途赢战中考') then '江苏图书'
   when get_customer_way_name in ('平台自播') and flow_pool_name in ('京赋-浙江科学曹忆规划','为真-浙江科学曹忆老师','为真-浙江大科学曹忆老师','京赋-江苏曹忆老师规划','博学星辰初阶规划峥峥','博学星辰-曹忆老师浙江规划','京赋-浙江曹忆老师规划') then '曹忆'
when flow_pool_name='电商退款用户池' and rule_name like '%赠失%' and rule_name like '%朱博士%' then '赠课失败-朱汉祺'
when flow_pool_name='电商退款用户池' and rule_name like '%赠失%' and rule_name like '%春春%' then '赠课失败-陈瑞春'
when flow_pool_name='电商退款用户池' and rule_name like '%赠失%' and rule_name like '%亚飞%' then '赠课失败-孟亚飞'
when flow_pool_name='电商退款用户池' and rule_name like '%赠失%' and rule_name like '%星义%' then '赠课失败-赵星义'
when flow_pool_name='电商退款用户池' and rule_name like '%赠失%' and rule_name like '%郭艺%' then '赠课失败-郭艺'
when second_department_name='本地化大班学部' or source_manager_name in ('鲍大海','杨文卓') then '本地化市场流量'
when third_department_name in ('中价产品项目部','新媒体内容运营部') and rule_name like '%曹忆%' then '曹忆'
when rule_name like '%语数英%' and third_department_name = '新媒体内容运营部' then '语数英'
 when third_department_name = '直播部' and sku_id_name like '%山东专版%' then '北京直播山东'
  when third_department_name = '直播部' and sku_id_name like '%河南专版%' then '北京直播河南'
  when sku_id_name like '%江苏%' and third_department_name = '直播部'  then '北京直播江苏'
when third_department_name like '%锋途%' and channel_name_2 = '抖音' then '锋途KOC'
when put_plan_name like '%小红书打粉%' then 'EM-小红书合作'
when trace_type_name like '%转介绍%' then '转介绍'
when flow_pool_name like '%星义大大%' or flow_pool_name like '%星义物理%' then '赵星义'
when ad_account_name in ('高途-高中-DYD搜索-QZ49','高途-高中-DYD搜索-XLHD49','高途-高中-DYD搜索-XLHD50','高途-高中-DYD搜索-QZ50') or ad_account_name like '%DYD1元搜索%' then '搜索1元'
when (flow_pool_name like '%江苏预习%' or  flow_pool_name like '%江苏专版预习%') and channel_name_2 ='抖音' then '西安直播江苏-抖音'
when flow_pool_name like '%自然流%' and rule_name like '%江苏%' and third_department_name='图书营销部' and channel_name_2 ='抖音' then '西安直播江苏-抖音'
when (flow_pool_name like '%江苏预习%' or  flow_pool_name like '%江苏专版预习%') and channel_name_2 ='视频号' then '西安直播江苏-视频号'
when flow_pool_name like '%退款%' and third_department_name ='图书营销部' then '西安直播-退款订单复用'
when flow_pool_name like '%自然流%' and rule_name like '%江苏%' and third_department_name='图书营销部' and channel_name_2 ='视频号' then '西安直播江苏-视频号'
when rule_name like '%北京图书%' and third_department_name='图书营销部' then '西安直播北京'
when sku_id_name like '%安徽%' and third_department_name='图书营销部' then '西安直播安徽'
when flow_pool_name like '%自然流%' and rule_name like '%北京%' and third_department_name='图书营销部' then '西安直播北京'
when source_manager_name in ('马思雨02','袁银') and rule_name like '%集团%' then '集团私域'
when rule_name like '%途途私域%' or (rule_name like '%私域%' and first_department_name = 'TT') or rule_name like '%私域1元%' or (third_department_name='私域招生中心' and flow_pool_name like '%APP%') then '途途私域'
when third_department_name='图书营销部' and (sku_id_name like '%孟亚飞99%' or sku_id_name like '%亚飞%') and channel_name_2 = '百度' then '孟亚飞-2组-百度'
when third_department_name='图书营销部' and (sku_id_name like '%孟亚飞99%' or sku_id_name like '%亚飞%') and channel_name_2 = '抖音' then '孟亚飞-2组-抖音'
when third_department_name = '投放部' and (ad_account_name like '%周帅%') then '信息流-周帅'
when source_manager_name in ('韩正卿') then '抖音私信'
when third_department_name = '私域运营部' and source_manager_name in ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研','岳一帆02','田起帆','王绍阳','肖佳兴','姚佳03','秦金萍') and (rule_name like '%koc自孵化下引%' or rule_name like '%koc下引%') then '自孵化KOC下引'
when third_department_name = '私域运营部' and source_manager_name in ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研','岳一帆02','田起帆','王绍阳','肖佳兴','姚佳03','秦金萍') then '进校私域合作'
when channel_name_1='市场私域' and (virtual_fourth_department_name in ('郑州学习顾问二部','郑州学习顾问七部','郑州训练营') or virtual_fifth_department_name in ('罗江博团队')) then '市场私域入群'
when third_department_name = '图书营销部' and (rule_name like '%点睛卷%' or sku_id_name like '%押题卷%')  then '押题卷'
when third_department_name = '投放部' and channel_name_2 = '小红书' and channel_name_1 <> '搜索营销' then '信息流-小红书'
when third_department_name = '线上商务部' and channel_name_2 = '小红书' then '小红书'
when (flow_pool_name like '%北大汤哥%' or flow_pool_name like '%海淀名师高阶%' or flow_pool_name like '%海淀高阶%' or flow_pool_name like '%高阶英语887%') and sku_id_name like '%小艺%'  then '郭艺'
when  third_department_name like '%私域%' and rule_name like '%私域%' and rule_name like '%图书%' then '市场私域图书'
when  third_department_name like '%私域%' and rule_name like '%品效%'  then '市场私域品效'
when  third_department_name like '%私域%' and rule_name like '%公域学霸%'  then '市场私域公域组'
when third_department_name in ('线上商务部') and source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07','曲默晗') and flow_pool_name like '%退款%' then 'KOC-退款订单复用'
when third_department_name in ('直播部','新媒体内容运营部','市场一组','私域运营部') and flow_pool_name ='电商退款用户池'  then 'IP退款订单复用'
when third_department_name in ('直播部','新媒体内容运营部','市场一组','私域运营部') and put_plan_name like '%失败%' and flow_pool_name ='电商退款用户池'  then '赠课失败'
when third_department_name in ('直播部','新媒体内容运营部','市场一组')  and (flow_pool_name ='初阶化学规划' or flow_pool_name like '%启迪-初阶老师%')  then '曹忆'
when (third_department_name = '图书营销部' and sku_id_name like '%真题%') or (third_department_name='直播部' and sku_id_name like '%真题%') then '西安图书直播间-直播'
when (third_department_name = '图书营销部' and sku_id_name not like '%真题%') or (third_department_name='直播部' and sku_id_name  like '%秒懂%') or (third_department_name='直播部' and sku_id_name  like '%图书赠送%') then '西安图书直播间-挂链'
when third_department_name in ('直播部','新媒体内容运营部','市场一组') and (flow_pool_name like '%海淀高阶名师%' or flow_pool_name like '%海淀老师高阶%' or flow_pool_name like '%小艺%' or flow_pool_name like '%老蒋文化%') then '郭艺'
when third_department_name in ('直播部','新媒体内容运营部','市场一组') and flow_pool_name like '%电商退款%' and rule_name like '%郭艺99%' then '郭艺'
when put_plan_name like '%国培教育-0元%' or put_plan_name like '%易喆教育-0元%' or put_plan_name like '%钟情-0元%' or put_plan_name like '%中望达-0元%' or put_plan_name like '%晨硕-0元%' or put_plan_name like '%彩石-0元入群%'  then '创新商务入群'
when third_department_name='KOC孵化部' and flow_pool_name like '%电商退款%' and put_plan_name like '%失败%' then '自孵化KOC-赠课失败'
when third_department_name='KOC孵化部' and flow_pool_name like '%电商退款%' and put_plan_name like '%退%' then '自孵化KOC-退款订单复用'
when source_manager_name = '方俊结01' and put_plan_name like '%赠课后退款%' then 'KOC-赠课后退款' 
when third_department_name = '直播部' and (sku_id_name like '%春春%' or sku_id_name like '%瑞春%' or rule_name like '%春春%' or rule_name like '%瑞春%') and channel_name_2='百度' then '陈瑞春-百度'
when third_department_name = '直播部' and (sku_id_name like '%春春%' or sku_id_name like '%瑞春%' or rule_name like '%春春%' or rule_name like '%瑞春%') and channel_name_2='抖音' then '陈瑞春-抖音199'
when third_department_name = '直播部' and (sku_id_name like '%春春%' or sku_id_name like '%瑞春%' or rule_name like '%春春%' or rule_name like '%瑞春%') and channel_name_2='视频号' then '陈瑞春-视频号49'
when third_department_name = '直播部' and (sku_id_name like '%朱博士99%' or rule_name like '%朱汉祺99%' or rule_name like '%朱博士%' or flow_pool_name like '%朱博士%' or sku_id_name like '%朱博士%') and channel_name_2 = 'B站' then '朱博士-B站'
when third_department_name = '直播部' and (sku_id_name like '%朱博士99%' or rule_name like '%朱汉祺99%' or rule_name like '%朱博士%' or flow_pool_name like '%朱博士%' or sku_id_name like '%朱博士%') and channel_name_2 = '百度' then '朱博士-百度'
when third_department_name = '直播部' and (sku_id_name like '%朱博士99%' or rule_name like '%朱汉祺99%' or rule_name like '%朱博士%' or flow_pool_name like '%朱博士%' or sku_id_name like '%朱博士%') and channel_name_2 = '抖音' then '朱博士-抖音199'
when third_department_name = '直播部' and (sku_id_name like '%朱博士99%' or rule_name like '%朱汉祺99%' or rule_name like '%朱博士%' or flow_pool_name like '%朱博士%' or sku_id_name like '%朱博士%') and channel_name_2 = '视频号' then '朱博士-视频号49'
when (third_department_name = '直播部' and (sku_id_name like '%朱博士%' or sku_id_name like '%朱汉祺%') and rule_name like '%9%' and rule_name not like '%29%' and sku_id_name not like '%急%' and sku_id_name not like '%礼盒29%') or (third_department_name = '直播部' and sku_id_name like '%朱博士9%') then '朱博士9元'
when ad_account_name like '%春春%' and channel_name_1 = '信息流' then '信息流-陈瑞春'
when channel_name_1 = '信息流' and channel_name_2='B站' and (page_id_name like '%0元物化%') then 'B站信息流-曹忆'
when channel_name_1 = '信息流' and channel_name_2='B站' and (page_id_name like '%赵星义%') then 'B站信息流-赵星义'
when channel_name_1 = '信息流' and channel_name_2='B站' and (page_id_name like '%亚飞%' or source_put_plan_name like '%亚飞%'   or page_id_name like '%初中-0元%') then 'B站信息流-亚飞'
when (flow_pool_name like '%朱博士%' or flow_pool_name like '%双博士%' or flow_pool_name like '%教育规划%') and third_department_name <> '线上商务部' and period_name not like '%多学科拓展%' and rule_name not like '%张杰%' and sku_id_name not like '%马凯鹏IP%' and third_department_name='直播部' then '朱博士29'
when put_plan_name like '%朱博士说教育%' and period_name not like '%多学科拓展%' and flow_pool_name not like '%高分讲堂%' and  flow_pool_name not like '%总裁%' and third_department_name='直播部' then '朱博士29'
when (flow_pool_name like '%朱博士讲英语%' or flow_pool_name like '%朱博士英语%' or flow_pool_name like '%朱汉祺说英语%' or flow_pool_name like '%朱博士说英语%' or flow_pool_name like '%教育规划%' or flow_pool_name like '%双博士英语规划%' or flow_pool_name like '%朱博士满分英语%' or flow_pool_name like '%英语教父朱博士%' or (flow_pool_name like '%中考决胜天团%' and lead_purchase_intention_level1_category_name = '规划系统')) and third_department_name = '直播部' and period_name not like '%多学科拓展%' and sku_id_name not like '%马凯鹏IP%' and third_department_name='直播部' then '朱博士29'
when (flow_pool_name like '%汤哥%' or flow_pool_name like '%汤老师%') and period_name not like '%多学科拓展%' and third_department_name in ('直播部','新媒体内容运营部')  then '汤老师'
when source_manager_name = '陈晓菁04' and channel_provider_name not like '%开拓%' and put_plan_name not like '%九学%' then '商务低价'        
when (flow_pool_name like '%孟帝%' or flow_pool_name like '%孟老师%' or flow_pool_name like '%中考数学冲刺%' or flow_pool_name like '%8升9数学%' or flow_pool_name like '%孟亚飞讲数学%' or flow_pool_name like '%中考冲刺%' or flow_pool_name like '%中考满分冲刺%' or flow_pool_name like '%押题王孟亚飞%' or flow_pool_name like '%中考数学大通关%' or flow_pool_name like '%中考数学规划%' or flow_pool_name like '%亚飞数学%' or flow_pool_name like '%孟帝数学%' or flow_pool_name like '%亚飞秒解思维%' or flow_pool_name like '%亚飞解题%')  and period_name not like '%多学科拓展%' and channel_name_2 not like '%KOL%' and third_department_name='直播部' and channel_name_2 = '抖音'  then '孟亚飞-1组-抖音'
when (flow_pool_name like '%孟帝%' or flow_pool_name like '%孟老师%' or flow_pool_name like '%中考数学冲刺%' or flow_pool_name like '%8升9数学%' or flow_pool_name like '%孟亚飞讲数学%' or flow_pool_name like '%中考冲刺%' or flow_pool_name like '%中考满分冲刺%' or flow_pool_name like '%押题王孟亚飞%' or flow_pool_name like '%中考数学大通关%' or flow_pool_name like '%中考数学规划%' or flow_pool_name like '%亚飞数学%' or flow_pool_name like '%孟帝数学%')  and period_name not like '%多学科拓展%' and channel_name_2 not like '%KOL%' and third_department_name='直播部' and channel_name_2 = '视频号'  then '孟亚飞-1组-视频号'
when (flow_pool_name like '%孟帝%' or flow_pool_name like '%孟老师%' or flow_pool_name like '%中考数学冲刺%' or flow_pool_name like '%8升9数学%' or flow_pool_name like '%孟亚飞讲数学%' or flow_pool_name like '%中考冲刺%' or flow_pool_name like '%中考满分冲刺%' or flow_pool_name like '%押题王孟亚飞%' or flow_pool_name like '%中考数学大通关%' or flow_pool_name like '%中考数学规划%' or flow_pool_name like '%亚飞数学%' or flow_pool_name like '%孟帝数学%')  and period_name not like '%多学科拓展%' and channel_name_2 not like '%KOL%' and third_department_name='直播部' and channel_name_2 = 'B站'  then '孟亚飞-1组-B站'
when (flow_pool_name like '%孟帝%' or flow_pool_name like '%孟老师%' or flow_pool_name like '%中考数学冲刺%' or flow_pool_name like '%8升9数学%' or flow_pool_name like '%孟亚飞讲数学%' or flow_pool_name like '%中考冲刺%' or flow_pool_name like '%中考满分冲刺%' or flow_pool_name like '%押题王孟亚飞%' or flow_pool_name like '%中考数学大通关%' or flow_pool_name like '%中考数学规划%' or flow_pool_name like '%亚飞数学%' or flow_pool_name like '%孟帝数学%')  and period_name not like '%多学科拓展%' and channel_name_2 not like '%KOL%' and third_department_name='直播部' and channel_name_2 not like '%百度%'  then '孟亚飞99-1组'
when (flow_pool_name like '%孟帝%' or flow_pool_name like '%孟老师%' or flow_pool_name like '%中考数学冲刺%' or flow_pool_name like '%8升9数学%' or flow_pool_name like '%孟亚飞讲数学%' or flow_pool_name like '%中考冲刺%' or flow_pool_name like '%中考满分冲刺%' or flow_pool_name like '%押题王孟亚飞%' or flow_pool_name like '%中考数学大通关%' or flow_pool_name like '%中考数学规划%' or flow_pool_name like '%亚飞数学%')  and period_name not like '%多学科拓展%' and channel_name_2 not like '%KOL%' and third_department_name='直播部' and channel_name_2 = '百度'  then '孟亚飞-1组-百度'
when put_plan_name like '%刘家晋讲图文%' or put_plan_name like '%孟帝数学%' and third_department_name='直播部' then '孟亚飞9元'        
when flow_pool_name like '%汐子%' and period_name not like '%多学科拓展%' and sku_id_name  like '%亚飞%' and third_department_name='直播部' and rule_name like '%99%'  then '孟亚飞99-1组'
when (flow_pool_name like '%曹忆%' or flow_pool_name like '%dudu%' or flow_pool_name like '%中考决胜天团%' or flow_pool_name like '%具象思维%' or flow_pool_name like '%在逃发面馒头%' or flow_pool_name like '%库洛米%' and lead_purchase_intention_level1_category_name <> '规划系统') and period_name not like '%多学科拓展%' and third_department_name in ('直播部','新媒体内容运营部') then '曹忆'
when first_department_name ='市场部' and channel_name_1 <> '站内获客' and channel_name_2 <> 'APP' then '集团私域'
when third_department_name = '私域运营部' and rule_name not like '%训练营%' and virtual_fifth_department_name not in ('罗江博团队') and rule_name not like '%复用%' and rule_name not like '%未加好友%' and channel_name_2 <> '内部换量' then '市场私域低价单'
when third_department_name = '私域运营部' and rule_name not like '%训练营%'  and rule_name not like '%复用%' and rule_name not like '%未加好友%' and channel_name_2 <> '内部换量' and flow_original_order_activity_price = '0.0' then '市场私域低价单'
when channel_name_2 in ('APP','M站','PC') and flow_pool_name not like '%途途%' then 'APP'
when channel_name_2 in ('小程序') and flow_pool_name  like '%高途体验课%' then 'APP'
when channel_provider_name like '%唐山TMK%' then '唐山TMK' 
when source_manager_name in ('高文羽') and channel_provider_name not like '%唐山TMK%' and channel_provider_name not like '%郑州%' then '人工外呼' 
when source_manager_name = '冯银晨' and channel_name_2 = '小红书' then '信息流-小红书'        
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and page_id_name like '%汤雪%'  then 'B站信息流-汤学健'
when (channel_name_1 = '信息流' and channel_name_2 <> 'B站' and third_department_name NOT LIKE '%商务%' and put_plan_name not like '%初三0元%' and put_plan_name not like '%抖音私信%' and put_plan_name not like '%高中0元%' and flow_original_order_activity_price not like '%1990%') or (channel_name_2 = 'B站' and third_department_name like '%投放%') then '信息流'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and (page_id_name like '%郭艺%') then 'B站信息流-郭艺'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and (page_id_name like '%朱博士%') then 'B站信息流-朱汉祺'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and page_id_name like '%肖晗%' then 'B站信息流'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and (page_id_name like '%马凯鹏%' or ad_account_name like '%化学%') then 'B站信息流-马凯鹏'
when channel_name_1 = '信息流'  and channel_name_2 = 'B站' and third_department_name not like '%投放%' and  (sku_id_name like '%陈瑞春%' or rule_name like '%陈瑞春%') and (ad_account_name  like '%语文%' or source_put_plan_name like '%自然流%' or page_id_name like '%春春%') then 'B站信息流-陈瑞春'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and (flow_original_order_activity_price like '%2990%' or sku_id_name like '%帅师%' or sku_id_name like '%周帅%') and ad_account_name like '%语文%' and  (flow_original_order_activity_price like '%1980%' or flow_original_order_activity_price like '%2980%' or flow_original_order_activity_price like '%2990%') then 'B站信息流-陈瑞春'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and (flow_original_order_activity_price like '%2990%' or sku_id_name like '%帅师%' or sku_id_name like '%周帅%') and ad_account_name not like '%语文%' then 'B站信息流-周帅'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and flow_order_price like '%1980%' and ad_account_name like '%数学%' then 'B站信息流-周帅'
when channel_name_1 = '短直电商' and channel_name_2 = 'B站' and third_department_name  like '%商务%' and   (flow_pool_name like '%春春%' or sku_id_name like '%陈瑞春%')  then 'B站信息流-陈瑞春'
when channel_name_1 = '短直电商' and channel_name_2 = 'B站' and third_department_name  like '%商务%' and  (flow_pool_name like '%朱博士%')  then 'B站信息流-朱汉祺'
--when third_department_name = '线上商务部' and channel_name_2 = 'B站' and put_plan_name like '%春春%' then 'B站信息流-陈瑞春'
--when third_department_name = '线上商务部' and channel_name_2 = 'B站' and put_plan_name like '%朱博士%' then 'B站信息流-朱汉祺'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and flow_original_order_activity_price not like '%2980%' and flow_original_order_activity_price not like '%2990%' and flow_original_order_activity_price not like '%1980%' then 'B站信息流'
when flow_pool_name = '百度搜索引擎' or channel_name_1='搜索营销' then '信息流搜索'
when  flow_pool_name like '%小红书班课%' then '小红书投放'
when third_department_name = '投放部' and get_customer_way_name = '短视频信息流' and flow_original_order_activity_price like '%100%' then '信息流'
when put_plan_name like  '%福哥私域0元%'  then 'KOC-下引'
when flow_pool_name = '中考加油' and sku_id_name like '%孟帝%' then 'KOC-孟亚飞数学'
when flow_pool_name = '中考加油' and sku_id_name  like '%帅师%' then 'KOC-周帅数学'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07','曲默晗') and (sku_id_name like '%孟帝%' or sku_id_name like '%dudu%' or sku_id_name like '%市场初二%' or rule_name like '%亚飞%' or sku_id_name like '%初二高阳%' or sku_id_name like '%高阳初二%' or sku_id_name like '%精品初二%' or rule_name like '%初二%' or sku_id_name like '%菁英初三%' or (virtual_second_department_name = '菁英班学部' and lead_purchase_intention_level2_category_name='初级' and lead_create_time>= '2026-04-15 00:00:00')) then 'KOC-孟亚飞数学'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07','曲默晗') and (sku_id_name like '%帅师%' or rule_name like '%周帅%' or sku_id_name like '%9月升高三%' or sku_id_name like '%新高二%') then 'KOC-周帅数学'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07','曲默晗') and (sku_id_name like '%肖晗%' or rule_name like '%肖晗%') then 'KOC-肖晗'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07','曲默晗') and period_name not like '%多学科拓展%' and sku_id_name not like '%朱汉祺%' and sku_id_name not like '%朱博士%' and sku_id_name not like '%周帅%' and sku_id_name not like '%29元%' then 'KOC-5元纯课'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07','曲默晗') and sku_id_name like '%周帅%' then 'KOC-周帅'
--when (channel_name_2 like '%KOL%' and source_manager_name in ('崔文轩','孙培尧')) or (channel_name_2 like '%抖音%' and source_manager_name in ('徐绮鹤')) and period_name not like '%多学科拓展%' then '自孵化KOC'
when third_department_name in ('品牌效能部','KOC孵化部') and channel_name_2 in ('抖音','视频号','快手','KOL')  then '自孵化KOC-5元纯课'
when third_department_name in ('品牌效能部','KOC孵化部') and channel_name_2 in ('抖音','视频号','快手','KOL') and (sku_id_name like '%5元%'or sku_id_name like '%11元%' or flow_original_order_activity_price like '%1100%' or flow_original_order_activity_price like '%500%' or flow_orders_income_amount  like '%1100%' or flow_orders_income_amount  like '%500%' ) then '自孵化KOC-5元纯课'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04','赵艺雅') and channel_name_2 like '%社群%' then '进校社群'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04','赵艺雅') and (channel_name_2 like '%直推%' or (put_plan_name like '%良师益友%' or put_plan_name like '%弘诚1元%')) then '进校直推'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04','赵艺雅') and channel_name_2 like '%TMK%' and (page_id_name like '%1元%' or channel_provider_name like '%禾顺云%') then '进校TMK1元'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04','赵艺雅') and channel_name_2 like '%TMK%' and page_id_name like '%9元%' then '进校TMK9元'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04','赵艺雅') and channel_name_2 like '%书商%' then '进校书商'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04','赵艺雅') and channel_name_2 like '%综合%' and put_plan_name like '%18%' then '进校直播'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04','赵艺雅') and channel_name_2 like '%直播%' then '进校直播'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','赵艺雅') and put_plan_name not like '%0元%' and flow_pool_name not like '%家校共育%' and flow_pool_name not like '%保持热爱%' and flow_pool_name not like '%青松%' and flow_pool_name not like '%原子初三%' and flow_pool_name not like '%南通欣创%' and flow_pool_name not like '%悟之道%' and flow_pool_name not like '%济南梦航%' and channel_name_3 <> '社群' and put_plan_name not like '%善悟%' and put_plan_name not like '%人人通%'  and put_plan_name not like '%%济南格乐' and flow_pool_name not like '%晨硕智学%' and flow_pool_name not like '%兴尧文化%'  and flow_pool_name not like '%济南映像%' and flow_pool_name not like '%山东简单%' and flow_pool_name not like '%争鸣科技%'  then '商务低价'
when flow_pool_name like '%南通欣创%' or  flow_pool_name like '%人人通科技%' or flow_pool_name like '%易而购%' or flow_pool_name like '%济南梦航%' or flow_pool_name like '%晨硕智学%' or flow_pool_name like '%兴尧文化%' or flow_pool_name like '%济南映像%' or flow_pool_name like '%山东简单%' or flow_pool_name like '%争鸣科技%'  then '进校私域合作'
when (flow_pool_name like '%家校共育%' or flow_pool_name like '%保持热爱%' or flow_pool_name like '%青松%' or flow_pool_name like '%悟之道%') and put_plan_name not like '%0元%'  then '进校私域合作'
when source_manager_name = '李宁24' and put_plan_name like '%0转低%' then '进校私域合作'
when third_department_name = '私域运营部' and  flow_original_order_activity_price in ('100.0','900.0','300.0')  then '进校私域合作'
when third_department_name = '私域运营部' and  flow_original_order_activity_price in ('0.0') and source_manager_name in ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研') then '进校私域合作'
when third_department_name = '私域运营部' and channel_name_1='市场私域' and put_plan_name not like '%公导私%' and put_plan_name not like '%公转私%' and flow_original_order_activity_price = '0.0' and rule_name not like '%激活%' and rule_name not like '%咨询%' and rule_name not like '%训练营%'  and virtual_fifth_department_name not like '%罗江博%' and virtual_fifth_department_name not like '%郑州学习顾问二部%' and source_manager_name not in ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研') then '市场私域低价单'
when source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and channel_provider_name like '%格乐教育%' and channel_name_2 like '%直播%' then '创新社群'
when source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and channel_name_2 like '%社群%' then '创新社群'
when source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and (channel_name_2 like '%直推%' or put_plan_name like '%直推%') then '创新直推'
when source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and (channel_name_2 like '%书商%' or put_plan_name like '%书商%' or page_id_name like '%书商%') then '创新书商'
when source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and channel_name_2 like '%TMK%' and page_id_name like '%1元%' then '创新TMK1元'
when source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and channel_name_2 like '%TMK%' and page_id_name like '%9元%' then '创新TMK9元'
when source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and (channel_name_2 like '%直播%' or page_id_name like '%进校%') then '创新直播'
when source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and channel_name_2<>'公众号' and channel_name_1 = '商务' and flow_pool_name <> '高途云集图书专营店-自然流' and flow_pool_name <> '高途旗舰店—线索—yuxinru' and put_plan_name not like '%社群%' and put_plan_name not like '%小红书班课%' and put_plan_name not like '%外部图书供量%' and channel_second_provider_name not like '%沃德丰店铺线索赠课%' and channel_second_provider_name not like '%智慧城-图书%' and put_plan_name not like '%育甲%' and flow_pool_name not like '%周长磊%'  then '创新商务'
when source_manager_name in ('高曼曼01','杨思怡','宋向函') then '图书KOC达人'
--when flow_pool_name like '%市场部-原子合作%' then '原子'
when flow_pool_name like '%市场部-微信私域%' or flow_pool_name like '%市场部-规划报告%' or flow_pool_name like '%规划报告%' or flow_pool_name like '%市场部-小红书%' or flow_pool_name like '%孟浩宇%' then '市场私域低价单'
when flow_pool_name like '%未加好友%' then '市场私域未加好友'
when flow_pool_name like '公导私' then '进校私域合作'
when (flow_pool_name like '%增长组%' or channel_name_3 = '公众号' or second_department_name = '微信生态部') and channel_name_2 <> 'APP' then '集团私域'
when put_plan_name like '%星耀%' or put_plan_name like '%物理展博%' or  put_plan_name like '%物理谢丽荣%' or put_plan_name like '%牟恩伯%' or  put_plan_name like '%王赞%' or put_plan_name like '%张磊老师高中数学%' or put_plan_name like '%雯姐高中物理大讲堂%' then '百度星耀'
when source_manager_name = '刘福云' and (sku_id_name like '%瑞春%' or sku_id_name like '%春春%') then '陈瑞春'
when third_department_name = '直播部' and sku_id_name like '%周帅%' and channel_name_2 in ('百度','B站')  then '周帅'
when third_department_name = '直播部' and sku_id_name like '%孟亚飞%' and rule_name like '%99%' then '孟亚飞99-1组'
when third_department_name = '直播部' and sku_id_name like '%朱汉祺%' then '朱博士99'
when flow_pool_name like '%0转低转正%' or channel_name_2='产研测试' then '进校私域合作'
when flow_pool_name like '%天津智慧双子%'        then '创新社群'
when third_department_name like '%城市定制%' then '点睛卷'        
when period_name like '%多学科拓展%' and third_department_name like '%私域运营%' then '市场私域入群'
when put_plan_name like '%赠课失败%' and third_department_name = '线上商务部' then 'KOC赠课失败'
when flow_pool_name like '%自然流%' and source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07','曲默晗') and sku_id_name like '%周帅%' then 'KOC-周帅'        
when flow_pool_name like '%自然流%' and source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07','曲默晗') and sku_id_name like '%肖晗%' then 'KOC-肖晗'        
when flow_pool_name like '%自然流%' and source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07','曲默晗') and sku_id_name like '%朱汉祺%'  and flow_original_order_activity_price like '%1100%' then 'KOC-5元朱汉祺'
when flow_pool_name like '%自然流%' and source_manager_name in ('赵语诗','崔文轩','孙培尧')        then '自孵化KOC-5元纯课'
when flow_pool_name like '%自然流%' and (sku_id_name like '%朱博士%' or sku_id_name like '%朱汉祺%') and rule_name like '%9%' and rule_name not like '%29%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '朱博士99'
when flow_pool_name like '%自然流%' and sku_id_name like '%朱博士%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '朱博士99'
when flow_pool_name like '%自然流%' and sku_id_name like '%亚飞%' and rule_name like '%99%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '孟亚飞99-1组'        
when flow_pool_name like '%自然流%' and sku_id_name like '%亚飞%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组')  then '孟亚飞9元'        
when flow_pool_name like '%自然流%' and sku_id_name like '%曹忆%' then '曹忆'        
when flow_pool_name like '%自然流%' and rule_name like '%朱博士%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '朱博士99'
when flow_pool_name like '%自然流%' and source_manager_name like '%邵万昕%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '朱博士99'
when flow_pool_name like '%自然流%' and rule_name like '%亚飞%' and rule_name like '%99%' then '孟亚飞99-1组'        
when flow_pool_name like '%自然流%' and rule_name like '%亚飞%'  then '孟亚飞9元'        
when flow_pool_name like '%自然流%' and rule_name like '%郭艺%'  then '郭艺'
when flow_pool_name like '%自然流%' and rule_name like '%汤雪%'  then '汤老师'        
when flow_pool_name like '%自然流%' and rule_name like '%曹忆%' then '曹忆'                
when flow_pool_name like '%途途教室%' or first_department_name like 'TUTU' then '途途APP'
when source_manager_name in ('宋莹莹','辛世如') and channel_name_2 in ('视频号') then '信息流-虚拟号挂车'
when rule_name like '%训练营%' and rule_name like '%市场私域%' then '市场私域入群'
when channel_name_1= '信息流' and (put_plan_name like '%抖音私信%' or put_plan_name like '%初三0元%' or put_plan_name like '%高中0元%') then '信息流-抖音私信'
when rule_name like '%途途私域%' or (rule_name like '%私域%' and first_department_name = 'TT') then '途途私域'
when get_customer_way_name in ('进校直推','线下渠道商') then '河南进校'
else '其他未知流量' end AS channel_map,
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
