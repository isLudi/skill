with biz_qici_calendar as (
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
src as (
    select
        coalesce(
            lead_cal.qici,
            concat(
                date_format(
                    date_trunc('week', date_parse(replace(concat(t.group_period_year, t.group_period_term), '期', ''), '%Y%m%d')) + interval '4' day,
                    '%Y%m%d'
                ),
                '期'
            )
        ) as period_name,
        t.lead_id,
        t.user_id,
        t.rule_name,
        t.flow_pool_name,
        t.sku_id_name,
        t.ad_account_name,
        t.source_manager_name,
        t.channel_name_1,
        t.channel_name_2,
        t.channel_name_3,
        t.put_plan_name,
        cast(t.flow_original_order_activity_price as varchar) as flow_original_order_activity_price,
        cast(t.flow_orders_income_amount as varchar) as flow_orders_income_amount,
        cast(t.flow_order_price as varchar) as flow_order_price,
        t.channel_provider_name,
        t.channel_second_provider_name,
        t.page_id_name,
        t.source_put_plan_name,
        t.get_customer_way_name,
        t.trace_type_name,
        t.first_department_name,
        t.second_department_name,
        t.third_department_name,
        t.virtual_second_department_name,
        t.virtual_third_department_name,
        t.virtual_fourth_department_name,
        t.virtual_fifth_department_name,
        t.lead_purchase_intention_name,
        t.lead_purchase_intention_level1_category_name,
        t.lead_purchase_intention_level2_category_name,
        t.lead_create_time,
        coalesce(t.virtual_leader_email_name, '未知') as manager_name,
        coalesce(t.lead_count, 0) as lead_count,
        coalesce(t.merge_assign_lead_count, 0) as merge_assign_lead_count,
        coalesce(t.valid_lead_count, 0) as valid_lead_count,
        coalesce(t.merge_valid_lead_count, 0) as merge_valid_lead_count,
        coalesce(t.conversion_lead_count, 0) as conversion_lead_count,
        coalesce(t.subject_count, 0) as subject_count,
        coalesce(t.trade_period_yw_conversion_subject_count, 0) as chinese_person_times,
        coalesce(t.trade_period_sx_conversion_subject_count, 0) as math_person_times,
        coalesce(t.trade_period_yy_conversion_subject_count, 0) as english_person_times,
        coalesce(t.trade_period_wl_conversion_subject_count, 0) as physics_person_times,
        coalesce(t.trade_period_hx_conversion_subject_count, 0) as chemistry_person_times,
        coalesce(t.order_count, 0) as order_count,
        coalesce(t.income_amount, 0) as income_amount,
        coalesce(t.in_pay_period_refund_amount, 0) as in_pay_period_refund_amount,
        coalesce(t.non_pay_period_refund_amount, 0) as non_pay_period_refund_amount
    from bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df t
    left join biz_qici_calendar lead_cal
      on lead_cal.business_domain = 'market_consultant'
     and lead_cal.date_role = 'lead_period'
     and cast(date_parse(replace(concat(t.group_period_year, t.group_period_term), '期', ''), '%Y%m%d') as date)
         between lead_cal.period_start_date and lead_cal.period_end_date
     and lead_cal.enabled = 1
    where t.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
      and t.hour = format_datetime(now() - interval '3' hour, 'HH')
      and t.section_assign_employee_first_level_department_name = 'H业务线'
      and t.section_assign_employee_second_level_department_name = '市场部'
      and t.section_assign_employee_third_level_department_name = '市场顾问部'
      and t.virtual_third_department_name = '市场顾问部'
      and t.period_mapping_first_level_department_name = 'H业务线'
      and t.period_mapping_second_level_department_name IN ('市场部', '精品班学部')
),
data as (
    select
        period_name,
case



when get_customer_way_name in ('平台自播') and flow_pool_name in ('赢战广东中考','高途专版图书','状元帮教辅','高途专版视频书','本地化专版图书','广东专版图书') then '广东图书'





when get_customer_way_name in ('平台自播') and flow_pool_name in ('途铭文化专版图书','途铭文化','博慧星辰文化图书','启迪蔚来','智慧航迹图书','高途浙江初中','高途浙江高中','高途浙江新高一','浙江专版图书教辅') then '浙江图书'





when get_customer_way_name in ('平台自播') and flow_pool_name in ('沪上名校','沪上领航社','简学文化','魔都校友助学馆','沪上领航高中','沪上领航初中') then '上海图书'





when get_customer_way_name in ('平台自播') and flow_pool_name in ('高途江苏中考','高途赢战中考') then '江苏图书'





when flow_pool_name='电商退款用户池' and rule_name like '%赠失%' and rule_name like '%朱博士%' then '赠课失败-朱汉祺'





when flow_pool_name='电商退款用户池' and rule_name like '%赠失%' and rule_name like '%春春%' then '赠课失败-陈瑞春'





when flow_pool_name='电商退款用户池' and rule_name like '%赠失%' and rule_name like '%亚飞%' then '赠课失败-孟亚飞'





when flow_pool_name='电商退款用户池' and rule_name like '%赠失%' and rule_name like '%星义%' then '赠课失败-赵星义'





when flow_pool_name='电商退款用户池' and rule_name like '%赠失%' and rule_name like '%郭艺%' then '赠课失败-郭艺'





when second_department_name='本地化大班学部' or source_manager_name in ('鲍大海','杨文卓','喻新桥') then '本地化市场流量'





when third_department_name in ('中价产品项目部','新媒体内容运营部') and rule_name like '%曹忆%' then '曹忆'





when rule_name like '%语数英%' and third_department_name = '新媒体内容运营部' then '语数英'





when third_department_name = '直播部' and sku_id_name like '%山东专版%' then '北京直播山东'





when third_department_name = '直播部' and sku_id_name like '%河南专版%' then '北京直播河南'





when third_department_name = '直播部' and sku_id_name like '%浙江首考%' then '浙江首考'



when third_department_name = '直播部' and sku_id_name like '%广东专版%' then '广东本地化'



when second_department_name = '市场二部' and put_plan_name like '%汤雪健%' then '市场二部-汤雪健'
  


when sku_id_name like '%江苏%' and third_department_name = '直播部'  then '北京直播江苏'





when third_department_name like '%锋途%' and channel_name_2 = '抖音' then '锋途KOC'





when third_department_name='线上商务部' and flow_pool_name like '%图书订单%' then '图书解密'





when put_plan_name like '%小红书打粉%' then 'EM-小红书合作'





when third_department_name in ('投放部','线上商务部','小红书攻坚组') and channel_name_2 ='小红书' then '小红书-闯闯组'






when third_department_name in ('新媒体内容运营部') and channel_name_2 ='小红书' then '小红书直投-绍孜组'






when page_id_name like '%0元领课%'  and third_department_name ='投放部'  then '信息流0元'





when page_id_name like '%周帅0元腾讯%'  and third_department_name ='投放部'  then '信息流0转低'





when page_id_name like '%信息流下引%'  and third_department_name ='私域运营部'  then '信息流0转低'





when sku_id_name like '%数理系统%' and third_department_name in ('快乐成长组','直播部','市场效能部','运营部') then '物理系统'





when trace_type_name like '%转介绍%' then '转介绍'





when ad_account_name in ('高途-高中-DYD搜索-QZ49','高途-高中-DYD搜索-XLHD49','高途-高中-DYD搜索-XLHD50','高途-高中-DYD搜索-QZ50') or ad_account_name like '%DYD1元搜索%' then '搜索1元'





when (flow_pool_name like '%江苏预习%' or  flow_pool_name like '%江苏专版预习%' or flow_pool_name like '%江苏百事%') and channel_name_2 ='抖音' then '西安直播江苏-抖音'





when flow_pool_name like '%自然流%' and rule_name like '%江苏%' and third_department_name='图书营销部' and channel_name_2 ='抖音' then '西安直播江苏-抖音'





when (flow_pool_name like '%江苏预习%' or  flow_pool_name like '%江苏专版预习%') and channel_name_2 ='视频号' then '西安直播江苏-视频号'





when flow_pool_name like '%退款%' and third_department_name ='图书营销部' then '西安直播-退款订单复用'





when flow_pool_name like '%自然流%' and rule_name like '%江苏%' and third_department_name='图书营销部' and channel_name_2 ='视频号' then '西安直播江苏-视频号'





when sku_id_name like '%2000题%' and third_department_name='图书营销部' then '西安直播2000题'





when sku_id_name like '%五年高考%' and third_department_name='图书营销部' then '西安直播五年真题'





when (rule_name like '%北京图书%' or sku_id_name like '%北京专版%') and third_department_name='图书营销部' then '西安直播北京'





when sku_id_name like '%安徽%' and third_department_name='图书营销部' then '西安直播安徽'





when put_plan_name like '%全国教考%' and third_department_name='图书营销部' then '西安直播全国'





when flow_pool_name like '%自然流%' and rule_name like '%北京%' and third_department_name='图书营销部' then '西安直播北京'





when sku_id_name like '%2000题%' and third_department_name='直播部' then 'IP直播-2000题'





when flow_pool_name like '%星义大大%' or flow_pool_name like '%星义物理%' then '赵星义'





when (source_manager_name in ('马思雨02','袁银') and rule_name like '%集团%')
 and not coalesce((
        (third_department_name = '私域运营部' and source_manager_name in ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研','岳一帆02','田起帆','王绍阳','肖佳兴','姚佳03','秦金萍','李冞萤'))
        or (flow_pool_name like '%南通欣创%' or  flow_pool_name like '%人人通科技%' or flow_pool_name like '%易而购%' or flow_pool_name like '%济南梦航%' or flow_pool_name like '%晨硕智学%' or flow_pool_name like '%兴尧文化%' or flow_pool_name like '%济南映像%' or flow_pool_name like '%山东简单%' or flow_pool_name like '%争鸣科技%')
        or ((flow_pool_name like '%家校共育%' or flow_pool_name like '%保持热爱%' or flow_pool_name like '%青松%' or flow_pool_name like '%悟之道%') and put_plan_name not like '%0元%')
        or (source_manager_name = '李宁24' and put_plan_name like '%0转低%')
        or (third_department_name = '私域运营部' and  flow_original_order_activity_price in ('100.0','900.0','300.0'))
        or (third_department_name = '私域运营部' and  flow_original_order_activity_price in ('0.0') and source_manager_name in ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研'))
        or (flow_pool_name like '公导私')
        or (flow_pool_name like '%0转低转正%' or channel_name_2='产研测试')
    ), false)
then '集团私域'





when rule_name like '%途途私域%' or (rule_name like '%私域%' and first_department_name = 'TT') or rule_name like '%私域1元%' or (third_department_name='私域招生中心' and flow_pool_name like '%APP%') then '途途私域'





when third_department_name='图书营销部' and (sku_id_name like '%孟亚飞99%' or sku_id_name like '%亚飞%') and channel_name_2 = '百度' then '孟亚飞-2组-百度'





when third_department_name='图书营销部' and (sku_id_name like '%孟亚飞99%' or sku_id_name like '%亚飞%') and channel_name_2 = '抖音' then '孟亚飞-2组-抖音'





when third_department_name = '投放部' and (ad_account_name like '%周帅%') then '信息流-周帅'





when source_manager_name in ('韩正卿') then '抖音私信'





when channel_name_1='市场私域' and put_plan_name like '%孟亚飞汇总%' then '小红书自然流-绍孜组'






when channel_name_1='市场私域' and (virtual_fourth_department_name in ('郑州学习顾问二部','郑州学习顾问七部','郑州训练营') and (rule_name like '%表单%' or trace_type_name like '%引流课%')) then '市场私域低价单'






when third_department_name = '私域运营部' and source_manager_name in ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研','岳一帆02','田起帆','王绍阳','肖佳兴','姚佳03','秦金萍','李冞萤') and (rule_name like '%koc自孵化下引%' or rule_name like '%koc下引%' or page_id_name like '%自营%') then '自孵化KOC下引'





when third_department_name = '私域运营部' and source_manager_name in ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研','岳一帆02','田起帆','王绍阳','肖佳兴','姚佳03','秦金萍','李冞萤') then '进校私域合作'





when channel_name_1='市场私域' and (virtual_fourth_department_name in ('郑州学习顾问二部','郑州学习顾问七部','郑州训练营') or virtual_fifth_department_name in ('罗江博团队')) then '市场私域入群'





when third_department_name = '图书营销部' and (rule_name like '%点睛卷%' or sku_id_name like '%押题卷%')  then '押题卷'





when third_department_name = '投放部' and channel_name_2 = '小红书' and channel_name_1 <> '搜索营销' then '信息流-小红书'





when third_department_name = '线上商务部' and channel_name_2 = '小红书' then '小红书'





when (flow_pool_name like '%北大汤哥%' or flow_pool_name like '%海淀名师高阶%' or flow_pool_name like '%海淀高阶%' or flow_pool_name like '%高阶英语887%') and sku_id_name like '%小艺%'  then '郭艺'





when  third_department_name like '%私域%' and rule_name like '%私域%' and rule_name like '%图书%' then '市场私域图书'





when  third_department_name like '%私域%' and rule_name like '%公域自然流%' then '小红书自然流-绍孜组'





when  third_department_name like '%私域%' and rule_name like '%品效%'  then '市场私域品效'





when  third_department_name like '%私域%' and put_plan_name like '%会话%'  then '市场私域会话'





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





when third_department_name = '直播部' and (sku_id_name like '%春春%' or sku_id_name like '%瑞春%' or rule_name like '%春春%' or rule_name like '%瑞春%') and channel_name_2='B站' then '陈瑞春-B站'





when third_department_name = '直播部' and (sku_id_name like '%春春%' or sku_id_name like '%瑞春%' or rule_name like '%春春%' or rule_name like '%瑞春%') and channel_name_2='抖音' then '陈瑞春-抖音199'





when third_department_name in ('直播部','新媒体内容运营部') and (sku_id_name like '%春春%' or sku_id_name like '%瑞春%' or rule_name like '%春春%' or rule_name like '%瑞春%') and channel_name_2='视频号' then '陈瑞春-视频号49'





when third_department_name = '直播部' and (sku_id_name like '%朱博士99%' or rule_name like '%朱汉祺99%' or rule_name like '%朱博士%' or flow_pool_name like '%朱博士%' or sku_id_name like '%朱博士%') and channel_name_2 = 'B站' then '朱博士-B站'





when third_department_name = '直播部' and (sku_id_name like '%朱博士99%' or rule_name like '%朱汉祺99%' or rule_name like '%朱博士%' or flow_pool_name like '%朱博士%' or sku_id_name like '%朱博士%') and channel_name_2 = '百度' then '朱博士-百度'





when third_department_name = '直播部' and (sku_id_name like '%抖音99%' and sku_id_name like '%朱博士%') and channel_name_2 = '抖音' then '朱博士-抖音99'






when third_department_name = '直播部' and (sku_id_name like '%朱博士99%') and channel_name_2 = '抖音' then '朱博士-抖音99'





when third_department_name = '直播部' and (sku_id_name like '%朱博士99%' or rule_name like '%朱汉祺99%' or rule_name like '%朱博士%' or flow_pool_name like '%朱博士%' or sku_id_name like '%朱博士%' or rule_name like '%朱汉祺199%') and channel_name_2 = '抖音' then '朱博士-抖音199'





when third_department_name = '直播部' and (sku_id_name like '%朱博士99%' or rule_name like '%朱汉祺99%' or rule_name like '%朱博士%' or flow_pool_name like '%朱博士%' or sku_id_name like '%朱博士%' or rule_name like '%朱汉祺49%') and channel_name_2 = '视频号' then '朱博士-视频号49'





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





when (first_department_name ='市场部' and channel_name_1 <> '站内获客' and channel_name_2 <> 'APP')
 and not coalesce((
        (third_department_name = '私域运营部' and source_manager_name in ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研','岳一帆02','田起帆','王绍阳','肖佳兴','姚佳03','秦金萍','李冞萤'))
        or (flow_pool_name like '%南通欣创%' or  flow_pool_name like '%人人通科技%' or flow_pool_name like '%易而购%' or flow_pool_name like '%济南梦航%' or flow_pool_name like '%晨硕智学%' or flow_pool_name like '%兴尧文化%' or flow_pool_name like '%济南映像%' or flow_pool_name like '%山东简单%' or flow_pool_name like '%争鸣科技%')
        or ((flow_pool_name like '%家校共育%' or flow_pool_name like '%保持热爱%' or flow_pool_name like '%青松%' or flow_pool_name like '%悟之道%') and put_plan_name not like '%0元%')
        or (source_manager_name = '李宁24' and put_plan_name like '%0转低%')
        or (third_department_name = '私域运营部' and  flow_original_order_activity_price in ('100.0','900.0','300.0'))
        or (third_department_name = '私域运营部' and  flow_original_order_activity_price in ('0.0') and source_manager_name in ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研'))
        or (flow_pool_name like '公导私')
        or (flow_pool_name like '%0转低转正%' or channel_name_2='产研测试')
    ), false)
then '集团私域'





when flow_pool_name like '%未加好友%' then '市场私域未加好友'





when put_plan_name like '%首期掉海%' and flow_pool_name like '%内部换量%' then '市场私域首期掉海'



when third_department_name = '私域运营部' and rule_name not like '%训练营%' and virtual_fifth_department_name not in ('罗江博团队') and rule_name not like '%复用%' and rule_name not like '%未加好友%' and channel_name_2 <> '内部换量' then '市场私域低价单'





when third_department_name = '私域运营部' and rule_name not like '%训练营%'  and rule_name not like '%复用%' and rule_name not like '%未加好友%' and channel_name_2 <> '内部换量' and flow_original_order_activity_price = '0.0' then '市场私域低价单'





when channel_name_2 in ('APP','M站','PC') and flow_pool_name not like '%途途%' then 'APP'





when channel_name_2 in ('小程序') and flow_pool_name  like '%高途体验课%' then 'APP'





when channel_provider_name like '%唐山TMK%' then '唐山TMK'





when source_manager_name in ('高文羽') and channel_provider_name not like '%唐山TMK%' and channel_provider_name not like '%郑州%' then '人工外呼'





when source_manager_name = '冯银晨' and channel_name_2 = '小红书' then '信息流-小红书'





when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and (rule_name like '%0904期-短期班-新高二-市场私域低价单%' or flow_original_order_activity_price='100' or page_id_name like '%1元%') then 'B站信息流-朱汉祺-1元'





when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and page_id_name like '%汤雪%'  then 'B站信息流-汤学健'





when (channel_name_1 = '信息流' and channel_name_2 <> 'B站' and third_department_name NOT LIKE '%商务%' and put_plan_name not like '%初三0元%' and put_plan_name not like '%抖音私信%' and put_plan_name not like '%高中0元%' and flow_original_order_activity_price not like '%1990%') or (channel_name_2 = 'B站' and third_department_name like '%投放%') then '信息流'





when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and (page_id_name like '%郭艺%') then 'B站信息流-郭艺'





when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and (page_id_name like '%朱博士%') then 'B站信息流-朱汉祺'





when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and rule_name like '%朱汉祺%' and flow_original_order_activity_price like '%1980%' then 'B站信息流-朱汉祺'


when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and page_id_name like '%肖晗%' then 'B站信息流'





when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and (page_id_name like '%马凯鹏%' or ad_account_name like '%化学%') then 'B站信息流-马凯鹏'





when channel_name_1 = '信息流'  and channel_name_2 = 'B站' and third_department_name not like '%投放%' and  (sku_id_name like '%陈瑞春%' or rule_name like '%陈瑞春%') and (ad_account_name  like '%语文%' or source_put_plan_name like '%自然流%' or page_id_name like '%春春%') then 'B站信息流-陈瑞春'





when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and (flow_original_order_activity_price like '%2990%' or sku_id_name like '%帅师%' or sku_id_name like '%周帅%') and ad_account_name like '%语文%' and  (flow_original_order_activity_price like '%1980%' or flow_original_order_activity_price like '%2980%' or flow_original_order_activity_price like '%2990%') then 'B站信息流-陈瑞春'





when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and (flow_original_order_activity_price like '%2990%' or sku_id_name like '%帅师%' or sku_id_name like '%周帅%') and ad_account_name not like '%语文%' then 'B站信息流-周帅'





when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and flow_order_price like '%1980%' and ad_account_name like '%数学%' then 'B站信息流-周帅'





when channel_name_1 = '短直电商' and channel_name_2 = 'B站' and third_department_name  like '%商务%' and   (flow_pool_name like '%春春%' or sku_id_name like '%陈瑞春%')  then 'B站信息流-陈瑞春'





when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and rule_name like '%陈瑞春%' and flow_original_order_activity_price like '%1980%' then 'B站信息流-陈瑞春'


when channel_name_1 = '短直电商' and channel_name_2 = 'B站' and third_department_name  like '%商务%' and  (flow_pool_name like '%朱博士%')  then 'B站信息流-朱汉祺'
--when third_department_name = '线上商务部' and channel_name_2 = 'B站' and put_plan_name like '%春春%' then 'B站信息流-陈瑞春'
--when third_department_name = '线上商务部' and channel_name_2 = 'B站' and put_plan_name like '%朱博士%' then 'B站信息流-朱汉祺'





when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and flow_original_order_activity_price not like '%2980%' and flow_original_order_activity_price not like '%2990%' and flow_original_order_activity_price not like '%1980%' then 'B站信息流'





when flow_pool_name = '百度搜索引擎' or channel_name_1='搜索营销' then '信息流搜索'





when  flow_pool_name like '%小红书班课%' then '小红书投放'





when third_department_name = '投放部' and get_customer_way_name = '短视频信息流' and flow_original_order_activity_price like '%100%' then '信息流'





when put_plan_name like  '%福哥私域0元%'  then 'KOC-下引'





when put_plan_name like  '%福哥私域5元%'  then 'KOC-下引5元'





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





when source_manager_name in ('高曼曼01','杨思怡','宋向函') and sku_id_name like '%帅师%' then '武汉KOC'


when source_manager_name in ('高曼曼01','杨思怡','宋向函') then '图书KOC达人'
--when flow_pool_name like '%市场部-原子合作%' then '原子'





when flow_pool_name like '%市场部-微信私域%' or flow_pool_name like '%市场部-规划报告%' or flow_pool_name like '%规划报告%' or flow_pool_name like '%市场部-小红书%' or flow_pool_name like '%孟浩宇%' then '市场私域低价单'





when flow_pool_name like '公导私' then '进校私域合作'





when ((flow_pool_name like '%增长组%' or channel_name_3 = '公众号' or second_department_name = '微信生态部') and channel_name_2 <> 'APP')
 and not coalesce((
        (third_department_name = '私域运营部' and source_manager_name in ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研','岳一帆02','田起帆','王绍阳','肖佳兴','姚佳03','秦金萍','李冞萤'))
        or (flow_pool_name like '%南通欣创%' or  flow_pool_name like '%人人通科技%' or flow_pool_name like '%易而购%' or flow_pool_name like '%济南梦航%' or flow_pool_name like '%晨硕智学%' or flow_pool_name like '%兴尧文化%' or flow_pool_name like '%济南映像%' or flow_pool_name like '%山东简单%' or flow_pool_name like '%争鸣科技%')
        or ((flow_pool_name like '%家校共育%' or flow_pool_name like '%保持热爱%' or flow_pool_name like '%青松%' or flow_pool_name like '%悟之道%') and put_plan_name not like '%0元%')
        or (source_manager_name = '李宁24' and put_plan_name like '%0转低%')
        or (third_department_name = '私域运营部' and  flow_original_order_activity_price in ('100.0','900.0','300.0'))
        or (third_department_name = '私域运营部' and  flow_original_order_activity_price in ('0.0') and source_manager_name in ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研'))
        or (flow_pool_name like '公导私')
        or (flow_pool_name like '%0转低转正%' or channel_name_2='产研测试')
    ), false)
then '集团私域'





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
else '其他未知流量' end as channel_map,
        case
            when rule_name like '%高一%' then '高一'
            when rule_name like '%高二%' then '高二'
            when rule_name like '%高三%' then '高三'
            when rule_name like '%初二%' then '初二'
            when rule_name like '%初三%' then '初三'
            else '未知'
        end as grade_name,
        manager_name,
        lead_id,
        user_id,
        lead_count,
        merge_assign_lead_count,
        valid_lead_count,
        merge_valid_lead_count,
        conversion_lead_count,
        subject_count,
        chinese_person_times,
        math_person_times,
        english_person_times,
        physics_person_times,
        chemistry_person_times,
        order_count,
        income_amount,
        in_pay_period_refund_amount,
        non_pay_period_refund_amount
    from src
    where period_name >= '20260403期'
),
user_base as (
    select
        period_name,
        channel_map,
        grade_name,
        manager_name,
        user_id,
        sum(lead_count) as lead_count,
        sum(valid_lead_count) as valid_lead_count,
        sum(conversion_lead_count) as regular_course_user_count,
        sum(order_count) as regular_course_order_count,
        sum(subject_count) as pay_subject_person_count,
        sum(chinese_person_times) as chinese_person_times,
        sum(math_person_times) as math_person_times,
        sum(english_person_times) as english_person_times,
        sum(physics_person_times) as physics_person_times,
        sum(chemistry_person_times) as chemistry_person_times,
        sum(income_amount / 100.0) as trade_income,
        sum((income_amount - in_pay_period_refund_amount - non_pay_period_refund_amount) / 100.0) as net_income
    from data
    group by
        period_name,
        channel_map,
        grade_name,
        manager_name,
        user_id
),
agg as (
    select
        period_name,
        channel_map,
        grade_name,
        manager_name,
        sum(lead_count) as lead_count,
        sum(case when regular_course_user_count > 0 then 1 else 0 end) as pay_user_head_count,
        sum(pay_subject_person_count) as pay_subject_person_count,
        sum(net_income) as net_income,
        sum(case when regular_course_user_count > 0 and pay_subject_person_count = 1 then 1 else 0 end) as subject_1_user_count,
        sum(case when regular_course_user_count > 0 and pay_subject_person_count = 1 then net_income else 0 end) as subject_1_gmv,
        sum(case when regular_course_user_count > 0 and pay_subject_person_count between 2 and 3 then 1 else 0 end) as subject_2_3_user_count,
        sum(case when regular_course_user_count > 0 and pay_subject_person_count between 2 and 3 then net_income else 0 end) as subject_2_3_gmv,
        sum(case when regular_course_user_count > 0 and pay_subject_person_count > 3 then 1 else 0 end) as subject_3_plus_user_count,
        sum(case when regular_course_user_count > 0 and pay_subject_person_count > 3 then net_income else 0 end) as subject_3_plus_gmv,
        sum(case when regular_course_user_count > 0 and pay_subject_person_count = 0 then 1 else 0 end) as subject_0_user_count,
        sum(case when regular_course_user_count > 0 and pay_subject_person_count = 0 then net_income else 0 end) as subject_0_gmv,
        sum(valid_lead_count) as valid_lead_count,
        sum(trade_income) as trade_income,
        sum(net_income) as net_trade_income,
        sum(regular_course_user_count) as regular_course_user_count,
        sum(regular_course_order_count) as regular_course_order_count
    from user_base
    group by
        period_name,
        channel_map,
        grade_name,
        manager_name
)
,residual_user_group_count as (
    select
        period_name,
        user_id,
        count(*) as residual_group_count
    from user_base
    where pay_subject_person_count - chinese_person_times - math_person_times
        - english_person_times - physics_person_times - chemistry_person_times > 0
    group by period_name, user_id
)
,finance_subject as (
    select distinct
        coalesce(
            finance_cal.qici,
            concat(
                date_format(
                    date_trunc('week', cast(f.trade_time as timestamp)) + interval '4' day,
                    '%Y%m%d'
                ),
                '期'
            )
        ) as period_name,
        f.user_id,
        case
            when f.course_subject like '%数学%' then '数学'
            when f.course_subject like '%语文%' then '语文'
            when f.course_subject like '%英语%' then '英语'
            when f.course_subject like '%物理%' then '物理'
            when f.course_subject like '%生物%' then '生物'
            when f.course_subject like '%化学%' then '化学'
            when f.course_subject like '%地理%' then '地理'
            when f.course_subject like '%政治%' then '政治'
            when f.course_subject like '%历史%' then '历史'
            when f.course_subject like '%学习分享%' then '学习分享'
            when f.course_subject like '%定制方案%' then '定制方案'
            else '其他'
        end as purchased_subject
    from finance_dw.app_finance_performance_extend_details_hf f
    left join biz_qici_calendar finance_cal
      on finance_cal.business_domain = 'market_consultant'
     and finance_cal.date_role = 'trade_period'
     and cast(f.trade_time as date)
         between finance_cal.period_start_date and finance_cal.period_end_date
     and finance_cal.enabled = 1
    where f.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
      and f.hour = format_datetime(now() - interval '2' hour, 'HH')
      and f.employee_first_level_department_name = 'H业务线'
      and f.employee_second_level_department_name = '市场部'
      and f.employee_third_level_department_name = '市场顾问部'
      and substr(f.trade_time, 1, 10) >= '2026-04-01'
      and f.real_price <> 0
      and f.trade_type in ('正常订单', '调课调班')
)
,finance_residual_subject as (
    select period_name, user_id, purchased_subject
    from finance_subject
    where purchased_subject in ('生物', '政治', '定制方案', '学习分享', '地理', '历史')
)
,finance_residual_subject_count as (
    select period_name, user_id, count(*) as mapped_subject_count
    from finance_residual_subject
    group by period_name, user_id
)
,accepted_residual_subject as (
    select
        u.period_name,
        u.channel_map,
        u.grade_name,
        u.manager_name,
        u.user_id,
        f.purchased_subject
    from user_base u
    join residual_user_group_count g
      on g.period_name = u.period_name
     and g.user_id = u.user_id
     and g.residual_group_count = 1
    join finance_residual_subject_count fc
      on fc.period_name = u.period_name
     and fc.user_id = u.user_id
     and fc.mapped_subject_count <= u.pay_subject_person_count - u.chinese_person_times
        - u.math_person_times - u.english_person_times - u.physics_person_times
        - u.chemistry_person_times
    join finance_residual_subject f
      on f.period_name = u.period_name
     and f.user_id = u.user_id
)
,residual_other_user as (
    select
        u.period_name,
        u.channel_map,
        u.grade_name,
        u.manager_name,
        u.user_id,
        u.pay_subject_person_count - u.chinese_person_times - u.math_person_times
            - u.english_person_times - u.physics_person_times - u.chemistry_person_times
            - case
                when coalesce(g.residual_group_count, 0) = 1
                 and coalesce(fc.mapped_subject_count, 0)
                    <= u.pay_subject_person_count - u.chinese_person_times - u.math_person_times
                        - u.english_person_times - u.physics_person_times - u.chemistry_person_times
                    then coalesce(fc.mapped_subject_count, 0)
                else 0
              end as other_person_times
    from user_base u
    left join residual_user_group_count g
      on g.period_name = u.period_name
     and g.user_id = u.user_id
    left join finance_residual_subject_count fc
      on fc.period_name = u.period_name
     and fc.user_id = u.user_id
)
,subject_agg_raw as (
    select period_name, channel_map, grade_name, manager_name, '语文' as purchased_subject,
        sum(case when chinese_person_times > 0 then 1 else 0 end) as subject_headcount,
        sum(chinese_person_times) as subject_person_times
    from user_base
    group by period_name, channel_map, grade_name, manager_name
    union all
    select period_name, channel_map, grade_name, manager_name, '数学' as purchased_subject,
        sum(case when math_person_times > 0 then 1 else 0 end) as subject_headcount,
        sum(math_person_times) as subject_person_times
    from user_base
    group by period_name, channel_map, grade_name, manager_name
    union all
    select period_name, channel_map, grade_name, manager_name, '英语' as purchased_subject,
        sum(case when english_person_times > 0 then 1 else 0 end) as subject_headcount,
        sum(english_person_times) as subject_person_times
    from user_base
    group by period_name, channel_map, grade_name, manager_name
    union all
    select period_name, channel_map, grade_name, manager_name, '物理' as purchased_subject,
        sum(case when physics_person_times > 0 then 1 else 0 end) as subject_headcount,
        sum(physics_person_times) as subject_person_times
    from user_base
    group by period_name, channel_map, grade_name, manager_name
    union all
    select period_name, channel_map, grade_name, manager_name, '化学' as purchased_subject,
        sum(case when chemistry_person_times > 0 then 1 else 0 end) as subject_headcount,
        sum(chemistry_person_times) as subject_person_times
    from user_base
    group by period_name, channel_map, grade_name, manager_name
    union all
    select period_name, channel_map, grade_name, manager_name, purchased_subject,
        count(distinct user_id) as subject_headcount,
        count(*) as subject_person_times
    from accepted_residual_subject
    group by period_name, channel_map, grade_name, manager_name, purchased_subject
    union all
    select period_name, channel_map, grade_name, manager_name, '其他' as purchased_subject,
        sum(case when other_person_times > 0 then 1 else 0 end) as subject_headcount,
        sum(other_person_times) as subject_person_times
    from residual_other_user
    group by period_name, channel_map, grade_name, manager_name
)
,subject_dim as (
    select purchased_subject
    from (
        values
            ('语文'), ('英语'), ('生物'), ('物理'), ('数学'), ('政治'),
            ('定制方案'), ('学习分享'), ('地理'), ('历史'), ('化学'), ('其他')
    ) as t(purchased_subject)
)
,subject_group_dim as (
    select distinct period_name, channel_map, grade_name, manager_name
    from user_base
)
,subject_agg as (
    select
        g.period_name,
        g.channel_map,
        g.grade_name,
        g.manager_name,
        d.purchased_subject,
        coalesce(r.subject_headcount, cast(0 as bigint)) as subject_headcount,
        coalesce(r.subject_person_times, cast(0 as bigint)) as subject_person_times
    from subject_group_dim g
    cross join subject_dim d
    left join subject_agg_raw r
      on r.period_name = g.period_name
     and r.channel_map = g.channel_map
     and r.grade_name = g.grade_name
     and r.manager_name = g.manager_name
     and r.purchased_subject = d.purchased_subject
)
select
    period_name,
    channel_map,
    grade_name,
    manager_name,
    lead_count,
    pay_user_head_count,
    pay_subject_person_count,
    net_income,
    subject_1_user_count,
    subject_1_gmv,
    subject_2_3_user_count,
    subject_2_3_gmv,
    subject_3_plus_user_count,
    subject_3_plus_gmv,
    subject_0_user_count,
    subject_0_gmv,
    valid_lead_count,
    trade_income,
    net_trade_income,
    regular_course_user_count,
    regular_course_order_count,
    case when regular_course_user_count = 0 then 0 else trade_income / regular_course_user_count end as avg_income_per_regular_course_user,
    'overall' as record_type,
    '全部学科' as purchased_subject,
    cast(null as bigint) as subject_headcount,
    cast(null as bigint) as subject_person_times
from agg
union all
select
    period_name,
    channel_map,
    grade_name,
    manager_name,
    cast(null as bigint) as lead_count,
    cast(null as bigint) as pay_user_head_count,
    cast(null as bigint) as pay_subject_person_count,
    cast(null as double) as net_income,
    cast(null as bigint) as subject_1_user_count,
    cast(null as double) as subject_1_gmv,
    cast(null as bigint) as subject_2_3_user_count,
    cast(null as double) as subject_2_3_gmv,
    cast(null as bigint) as subject_3_plus_user_count,
    cast(null as double) as subject_3_plus_gmv,
    cast(null as bigint) as subject_0_user_count,
    cast(null as double) as subject_0_gmv,
    cast(null as bigint) as valid_lead_count,
    cast(null as double) as trade_income,
    cast(null as double) as net_trade_income,
    cast(null as bigint) as regular_course_user_count,
    cast(null as bigint) as regular_course_order_count,
    cast(null as double) as avg_income_per_regular_course_user,
    'subject' as record_type,
    purchased_subject,
    subject_headcount,
    subject_person_times
from subject_agg
order by
    period_name,
    channel_map,
    grade_name,
    manager_name,
    record_type,
    purchased_subject
