with data_base as (
    select distinct
        t1.*,
        concat(
            cast(
                date_format(
                    date_trunc(
                        'week',
                        date_parse(replace(concat(t1.group_period_year, t1.group_period_term), '期', ''), '%Y%m%d') - interval '1' day
                    ) + interval '4' day,
                    '%Y%m%d'
                ) as varchar
            ),
            '期'
        ) as calc_period_name
    from bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df t1
    where t1.dt = format_datetime(now() - interval '3' hour, 'YYYYMMdd')
      and t1.hour = format_datetime(now() - interval '3' hour, 'HH')
      and t1.section_assign_employee_first_level_department_name = 'H业务线'
      and t1.section_assign_employee_second_level_department_name in ('市场部','精品班学部','青橙项目部','菁英班学部')
      and t1.virtual_third_department_name in ('学习顾问部','市场顾问部','中价产品项目部')
      and (t1.period_mapping_first_level_department_name = 'H业务线' or t1.period_mapping_first_level_department_name is null)
),
data as (
    select distinct
        calc_period_name as period_name,
        virtual_third_department_name as depart_1,
        section_assign_employee_second_level_department_name as dept_name,
        virtual_fourth_department_name as depart,
        virtual_leader_email_name as jingli,
        virtual_direct_leader_email_name as zhuguan,
        employee_email_name,
        lead_id,
        user_id,
case when flow_pool_name in ('高途学习规划','智辉老师讲规划') then '市场私域视频号'
when rule_name like '%语数英%' and third_department_name = '新媒体内容运营部' then '语数英'
when flow_pool_name like '%星义大大%' or flow_pool_name like '%星义物理%' then '赵星义'
when rule_name like '%途途私域%' or (rule_name like '%私域%' and first_department_name = 'TT' and rule_name not like '%集团%') then '途途私域'
when third_department_name='图书营销部' and (sku_id_name like '%孟亚飞99%' or sku_id_name like '%亚飞%') and channel_name_2 = '百度' then '孟亚飞-2组-百度'
when third_department_name='图书营销部' and (sku_id_name like '%孟亚飞99%' or sku_id_name like '%亚飞%') and channel_name_2 = '抖音' then '孟亚飞-2组-抖音'
when third_department_name = '投放部' and (ad_account_name like '%周帅%' or put_plan_name like '%周帅%') then '信息流-周帅'
when source_manager_name in ('韩正卿') then '抖音私信'
when third_department_name = '私域运营部' and source_manager_name in ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研','岳一帆02','田起帆','王绍阳') then '进校私域合作'
when channel_name_1='市场私域' and (virtual_fourth_department_name in ('郑州学习顾问二部','郑州学习顾问七部','郑州训练营') or virtual_fifth_department_name in ('罗江博团队')) then '市场私域入群'
when third_department_name = '图书营销部' and (rule_name like '%点睛卷%' or sku_id_name like '%押题卷%')  then '押题卷'
when put_plan_name like '%迪九学%' then '市场私域代运营'
when third_department_name = '投放部' and channel_name_2 = '小红书' and channel_name_1 <> '搜索营销' then '信息流-小红书'
when third_department_name = '线上商务部' and channel_name_2 = '小红书' then '小红书'
when (flow_pool_name like '%肖晗%' or sku_id_name like '%肖晗%' or put_plan_name like '%肖晗9元%') and third_department_name='直播部'  then '肖晗'
when (flow_pool_name like '%北大汤哥%' or flow_pool_name like '%海淀名师高阶%' or flow_pool_name like '%海淀高阶%') and sku_id_name like '%小艺%'  then '郭艺'
when  third_department_name like '%私域%' and rule_name like '%私域%' and rule_name like '%图书%' then '市场私域图书'
when  third_department_name like '%私域%' and rule_name like '%品效%'  then '市场私域品效'
when  third_department_name like '%私域%' and rule_name like '%公域学霸%'  then '市场私域公域组'
when  third_department_name like '%私域%' and rule_name like '%IE%'  then '市场私域IE'
when  third_department_name like '%私域%' and rule_name like '%裂变%'  then '市场私域裂变'
when third_department_name in ('直播部','新媒体内容运营部','市场一组','私域运营部') and put_plan_name like '%退%' and flow_pool_name ='电商退款用户池'  then '退款订单复用'
when third_department_name in ('直播部','新媒体内容运营部','市场一组','私域运营部') and put_plan_name like '%失败%' and flow_pool_name ='电商退款用户池'  then '赠课失败'
when third_department_name in ('直播部','新媒体内容运营部','市场一组')  and (flow_pool_name ='初阶化学规划' or flow_pool_name like '%启迪-初阶老师%')  then '曹忆'
when (third_department_name = '图书营销部' and sku_id_name like '%真题%') or (third_department_name='直播部' and sku_id_name like '%真题%') then '西安图书直播间-直播'
when (third_department_name = '图书营销部' and sku_id_name not like '%真题%') or (third_department_name='直播部' and sku_id_name  like '%秒懂%') or (third_department_name='直播部' and sku_id_name  like '%图书赠送%') then '西安图书直播间-挂链'
when third_department_name in ('直播部','新媒体内容运营部','市场一组') and (flow_pool_name like '%海淀高阶名师%' or flow_pool_name like '%海淀老师高阶%' or flow_pool_name like '%小艺%') then '郭艺'
when put_plan_name like '%国培教育-0元%' or put_plan_name like '%易喆教育-0元%' or put_plan_name like '%钟情-0元%' or put_plan_name like '%中望达-0元%' or put_plan_name like '%晨硕-0元%' or put_plan_name like '%彩石-0元入群%'  then '创新商务入群'
when put_plan_name like '%0元入群-进校%' and third_department_name = '线上商务部' then '创新商务入群'
when third_department_name='KOC孵化部' and flow_pool_name like '%电商退款%' and put_plan_name like '%失败%' then '自孵化KOC-赠课失败'
when third_department_name='KOC孵化部' and flow_pool_name like '%电商退款%' and put_plan_name like '%退%' then '自孵化KOC-退款订单复用'
when source_manager_name = '方俊结01' and put_plan_name like '%赠课后退款%' then 'KOC-赠课后退款'
when third_department_name = '直播部' and (sku_id_name like '%春春%' or sku_id_name like '%瑞春%' or rule_name like '%春春%' or rule_name like '%瑞春%') then '陈瑞春'
when third_department_name = '直播部' and (sku_id_name like '%朱博士99%' or rule_name like '%朱汉祺99%') then '朱博士99'
when (third_department_name = '直播部' and (sku_id_name like '%朱博士%' or sku_id_name like '%朱汉祺%') and rule_name like '%9%' and rule_name not like '%29%' and sku_id_name not like '%急%' and sku_id_name not like '%礼盒29%') or (third_department_name = '直播部' and sku_id_name like '%朱博士9%') then '朱博士9元'
when ad_account_name like '%春春%' and channel_name_1 = '信息流' then '信息流-陈瑞春'
when channel_name_1 = '信息流' and channel_name_2='B站' and (page_id_name like '%0元物化%') then 'B站信息流-曹忆'
when third_department_name = '直播部' and channel_name_1 = '信息流' and channel_name_2 = 'B站'  then 'B站信息流-亚飞(1元)'
when channel_name_1 = '信息流' and channel_name_2='B站' and (page_id_name like '%亚飞%' or source_put_plan_name like '%亚飞%'  or rule_name like '%亚飞%' or page_id_name like '%初中-0元%') then 'B站信息流-亚飞'
when channel_name_1 = '信息流' and (page_id_name like '%亚飞%' or ad_account_name like '%亚飞%') then '信息流-亚飞'
when (flow_pool_name like '%朱博士%' or flow_pool_name like '%双博士%' or flow_pool_name like '%教育规划%') and third_department_name <> '线上商务部' and period_name not like '%多学科拓展%' and rule_name not like '%张杰%' and sku_id_name not like '%马凯鹏IP%' and third_department_name='直播部' then '朱博士29'
when put_plan_name like '%朱博士说教育%' and period_name not like '%多学科拓展%' and flow_pool_name not like '%高分讲堂%' and  flow_pool_name not like '%总裁%' and third_department_name='直播部' then '朱博士29'
when flow_pool_name like '%朱博士讲英语%' and sku_id_name like '%马凯鹏IP%' and third_department_name='直播部' then '马凯鹏29'
when (flow_pool_name like '%朱博士讲英语%' or flow_pool_name like '%朱博士英语%' or flow_pool_name like '%朱汉祺说英语%' or flow_pool_name like '%朱博士说英语%' or flow_pool_name like '%教育规划%' or flow_pool_name like '%双博士英语规划%' or flow_pool_name like '%朱博士满分英语%' or flow_pool_name like '%英语教父朱博士%' or (flow_pool_name like '%中考决胜天团%' and lead_purchase_intention_level1_category_name = '规划系统')) and third_department_name = '直播部' and period_name not like '%多学科拓展%' and sku_id_name not like '%马凯鹏IP%' and third_department_name='直播部' then '朱博士29'
when (flow_pool_name like '%汤哥%' or flow_pool_name like '%汤老师%') and period_name not like '%多学科拓展%' and third_department_name in ('直播部','新媒体内容运营部')  then '汤老师'
when (flow_pool_name like '%中考百日冲刺%') and period_name not like '%多学科拓展%' and third_department_name='直播部'  then '曹忆9.9纯课'
when source_manager_name = '陈晓菁04' and channel_provider_name not like '%开拓%' and put_plan_name not like '%九学%' then '商务低价'
when (flow_pool_name like '%孟帝%' or flow_pool_name like '%孟老师%' or flow_pool_name like '%中考数学冲刺%' or flow_pool_name like '%8升9数学%' or flow_pool_name like '%孟亚飞讲数学%' or flow_pool_name like '%中考冲刺%' or flow_pool_name like '%中考满分冲刺%' or flow_pool_name like '%押题王孟亚飞%' or flow_pool_name like '%中考数学大通关%' or flow_pool_name like '%中考数学规划%' or flow_pool_name like '%亚飞数学%' or flow_pool_name like '%孟帝数学%' or flow_pool_name like '%亚飞秒解思维%')  and period_name not like '%多学科拓展%' and channel_name_2 not like '%KOL%' and third_department_name='直播部' and channel_name_2 = '抖音'  then '孟亚飞-1组-抖音'
when (flow_pool_name like '%孟帝%' or flow_pool_name like '%孟老师%' or flow_pool_name like '%中考数学冲刺%' or flow_pool_name like '%8升9数学%' or flow_pool_name like '%孟亚飞讲数学%' or flow_pool_name like '%中考冲刺%' or flow_pool_name like '%中考满分冲刺%' or flow_pool_name like '%押题王孟亚飞%' or flow_pool_name like '%中考数学大通关%' or flow_pool_name like '%中考数学规划%' or flow_pool_name like '%亚飞数学%' or flow_pool_name like '%孟帝数学%')  and period_name not like '%多学科拓展%' and channel_name_2 not like '%KOL%' and third_department_name='直播部' and channel_name_2 = '视频号'  then '孟亚飞-1组-视频号'
when (flow_pool_name like '%孟帝%' or flow_pool_name like '%孟老师%' or flow_pool_name like '%中考数学冲刺%' or flow_pool_name like '%8升9数学%' or flow_pool_name like '%孟亚飞讲数学%' or flow_pool_name like '%中考冲刺%' or flow_pool_name like '%中考满分冲刺%' or flow_pool_name like '%押题王孟亚飞%' or flow_pool_name like '%中考数学大通关%' or flow_pool_name like '%中考数学规划%' or flow_pool_name like '%亚飞数学%' or flow_pool_name like '%孟帝数学%')  and period_name not like '%多学科拓展%' and channel_name_2 not like '%KOL%' and third_department_name='直播部' and channel_name_2 = 'B站'  then '孟亚飞-1组-B站'
when (flow_pool_name like '%孟帝%' or flow_pool_name like '%孟老师%' or flow_pool_name like '%中考数学冲刺%' or flow_pool_name like '%8升9数学%' or flow_pool_name like '%孟亚飞讲数学%' or flow_pool_name like '%中考冲刺%' or flow_pool_name like '%中考满分冲刺%' or flow_pool_name like '%押题王孟亚飞%' or flow_pool_name like '%中考数学大通关%' or flow_pool_name like '%中考数学规划%' or flow_pool_name like '%亚飞数学%' or flow_pool_name like '%孟帝数学%')  and period_name not like '%多学科拓展%' and channel_name_2 not like '%KOL%' and third_department_name='直播部' and channel_name_2 not like '%百度%'  then '孟亚飞99-1组'
when (flow_pool_name like '%孟帝%' or flow_pool_name like '%孟老师%' or flow_pool_name like '%中考数学冲刺%' or flow_pool_name like '%8升9数学%' or flow_pool_name like '%孟亚飞讲数学%' or flow_pool_name like '%中考冲刺%' or flow_pool_name like '%中考满分冲刺%' or flow_pool_name like '%押题王孟亚飞%' or flow_pool_name like '%中考数学大通关%' or flow_pool_name like '%中考数学规划%' or flow_pool_name like '%亚飞数学%')  and period_name not like '%多学科拓展%' and channel_name_2 not like '%KOL%' and third_department_name='直播部' and channel_name_2 = '百度'  then '孟亚飞-1组-百度'
when (flow_pool_name like '%孟帝%' or flow_pool_name like '%孟老师%' or flow_pool_name like '%中考数学冲刺%' or flow_pool_name like '%8升9数学%' or flow_pool_name like '%孟亚飞讲数学%' or flow_pool_name like '%中考冲刺%' or flow_pool_name like '%中考满分冲刺%' or flow_pool_name like '%押题王孟亚飞%' or flow_pool_name like '%中考数学大通关%' or flow_pool_name like '%中考数学规划%' or flow_pool_name like '%亚飞数学%')  and period_name not like '%多学科拓展%' and channel_name_2 not like '%KOL%' and third_department_name='直播部'  then '孟亚飞9元'
when put_plan_name like '%刘家晋讲图文%' or put_plan_name like '%孟帝数学%' and third_department_name='直播部' and rule_name like '%99%'  then '孟亚飞99-1组'
when put_plan_name like '%刘家晋讲图文%' or put_plan_name like '%孟帝数学%' and third_department_name='直播部' then '孟亚飞9元'
when (flow_pool_name like '%肖晗%' or sku_id_name like '%肖晗%') and third_department_name='直播部'  then '肖晗'
when flow_pool_name like '%峥峥%' and period_name not like '%多学科拓展%' and third_department_name='直播部'  then '何峥峥'
when flow_pool_name like '%汐子%' and period_name not like '%多学科拓展%' and sku_id_name not like '%亚飞%' and third_department_name='直播部'  then '王汐子'
when flow_pool_name like '%汐子%' and period_name not like '%多学科拓展%' and sku_id_name  like '%亚飞%' and third_department_name='直播部' and rule_name like '%99%'  then '孟亚飞99-1组'
when flow_pool_name like '%汐子%' and period_name not like '%多学科拓展%' and sku_id_name  like '%亚飞%' and third_department_name='直播部' then '孟亚飞9元'
when (flow_pool_name like '%曹忆%' or flow_pool_name like '%dudu%' or flow_pool_name like '%中考决胜天团%' or flow_pool_name like '%具象思维%' or flow_pool_name like '%在逃发面馒头%' or flow_pool_name like '%库洛米%' and lead_purchase_intention_level1_category_name <> '规划系统') and period_name not like '%多学科拓展%' and third_department_name in ('直播部','新媒体内容运营部') then '曹忆'
when first_department_name ='市场部' and channel_name_1 <> '站内获客' and channel_name_2 <> 'APP' then '集团私域'
when put_plan_name like '%未加好友%' then '市场私域未加好友'
when put_plan_name like '%私域-信息流%' then '市场私域待支付'
when third_department_name = '私域运营部' and rule_name not like '%训练营%' and virtual_fifth_department_name not in ('罗江博团队') and rule_name not like '%复用%' and rule_name not like '%未加好友%' and channel_name_2 <> '内部换量' then '市场私域低价单'
when third_department_name = '私域运营部' and rule_name not like '%训练营%'  and rule_name not like '%复用%' and rule_name not like '%未加好友%' and channel_name_2 <> '内部换量' and flow_original_order_activity_price = '0.0' then '市场私域低价单'
when channel_name_2 in ('APP','M站','PC') and flow_pool_name not like '%途途%' then 'APP'
when channel_provider_name like '%唐山TMK%' then '唐山TMK'
when source_manager_name in ('高文羽') and channel_provider_name not like '%唐山TMK%' and channel_provider_name not like '%郑州%' then '人工外呼'
when source_manager_name = '冯银晨' and channel_name_2 = '小红书' then '信息流-小红书'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and page_id_name like '%汤雪%'  then 'B站信息流-汤学健'
when (channel_name_1 = '信息流' and channel_name_2 <> 'B站' and third_department_name NOT LIKE '%商务%' and put_plan_name not like '%初三0元%' and put_plan_name not like '%抖音私信%' and put_plan_name not like '%高中0元%' and flow_original_order_activity_price not like '%1990%') or (channel_name_2 = 'B站' and third_department_name like '%投放%') then '信息流'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and (page_id_name like '%郭艺%') then 'B站信息流-郭艺'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and (page_id_name like '%朱博士%') then 'B站信息流-朱汉祺'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and page_id_name like '%肖晗%' then 'B站信息流-肖晗'
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
when channel_name_1 = '信息流获客' and channel_name_2 = '小红书' and source_manager_name in ('王慧敏13','张琳02','王樱琦01') then '小红书投放'
when  flow_pool_name like '%小红书班课%' then '小红书投放'
when third_department_name = '投放部' and get_customer_way_name = '短视频信息流' and flow_original_order_activity_price like '%100%' then '信息流'
when flow_pool_name = '中考加油' and sku_id_name like '%孟帝%' then 'KOC-孟亚飞数学'
when flow_pool_name = '中考加油' and sku_id_name  like '%帅师%' then 'KOC-周帅数学'
when flow_pool_name = '中考加油' and sku_id_name  like '%肖晗%' then 'KOC-肖晗'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07') and (sku_id_name like '%孟帝%' or sku_id_name like '%dudu%' or sku_id_name like '%市场初二%' or rule_name like '%亚飞%' or sku_id_name like '%初二高阳%' or sku_id_name like '%高阳初二%' or sku_id_name like '%精品初二%' or sku_id_name like '%菁英初三%' or (virtual_second_department_name = '菁英班学部' and lead_purchase_intention_level2_category_name='初级' and lead_create_time>= '2026-04-15 00:00:00')) then 'KOC-孟亚飞数学'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07') and (sku_id_name like '%帅师%' or rule_name like '%周帅%' or sku_id_name like '%9月升高三%') then 'KOC-周帅数学'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07') and (sku_id_name like '%肖晗%' or rule_name like '%肖晗%') then 'KOC-肖晗'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07') and period_name not like '%多学科拓展%' and (flow_original_order_activity_price like '%1100%' or flow_original_order_activity_price like '%500%' or flow_orders_income_amount like '%500%') and (sku_id_name like '%朱汉祺%' or sku_id_name like '%朱博士%' or rule_name like '%朱汉祺5元%' or sku_id_name like '%koc5元-朱博士%' or rule_name like '%朱汉祺%') then 'KOC-5元朱汉祺'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07') and (sku_id_name like '%朱汉祺%' or sku_id_name like '%29元%' or sku_id_name like '%朱博士%' or rule_name like '%朱汉祺%' or rule_name like '%朱博士%' ) and (flow_original_order_activity_price not like '%1100%' or rule_name like '%29%') and sku_id_name not like '%周帅%' then 'KOC-5元朱汉祺'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07') and period_name not like '%多学科拓展%' and sku_id_name not like '%朱汉祺%' and sku_id_name not like '%朱博士%' and sku_id_name not like '%周帅%' and sku_id_name not like '%29元%' then 'KOC-5元纯课'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07') and sku_id_name like '%周帅%' then 'KOC-周帅'
--when (channel_name_2 like '%KOL%' and source_manager_name in ('崔文轩','孙培尧')) or (channel_name_2 like '%抖音%' and source_manager_name in ('徐绮鹤')) and period_name not like '%多学科拓展%' then '自孵化KOC'
when third_department_name in ('品牌效能部','KOC孵化部') and channel_name_2 in ('抖音','视频号','快手','KOL')  then '自孵化KOC-5元纯课'
when third_department_name in ('品牌效能部','KOC孵化部') and channel_name_2 in ('抖音','视频号','快手','KOL') and (sku_id_name like '%5元%'or sku_id_name like '%11元%' or flow_original_order_activity_price like '%1100%' or flow_original_order_activity_price like '%500%' or flow_orders_income_amount  like '%1100%' or flow_orders_income_amount  like '%500%' ) then '自孵化KOC-5元纯课'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') and channel_name_2 like '%社群%' then '进校社群'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') and channel_name_2 like '%直推%' then '进校直推'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') and channel_name_2 like '%TMK%' and page_id_name like '%1元%' then '进校TMK1元'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') and channel_name_2 like '%TMK%' and page_id_name like '%9元%' then '进校TMK9元'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') and channel_name_2 like '%书商%' then '进校书商'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') and channel_name_2 like '%综合%' and put_plan_name like '%18%' then '进校直播'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') and channel_name_2 like '%直播%' then '进校直播'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04') and put_plan_name not like '%0元%' and flow_pool_name not like '%家校共育%' and flow_pool_name not like '%保持热爱%' and flow_pool_name not like '%青松%' and flow_pool_name not like '%原子初三%' and flow_pool_name not like '%南通欣创%' and flow_pool_name not like '%悟之道%' and flow_pool_name not like '%济南梦航%' and channel_name_3 <> '社群' and put_plan_name not like '%善悟%' and put_plan_name not like '%人人通%'  and put_plan_name not like '%%济南格乐' and flow_pool_name not like '%晨硕智学%' and flow_pool_name not like '%兴尧文化%'  and flow_pool_name not like '%济南映像%' and flow_pool_name not like '%山东简单%' and flow_pool_name not like '%争鸣科技%'  then '商务低价'
when flow_pool_name like '%原子初三%' or flow_pool_name like '%原子系统%'  then '原子'
when flow_pool_name like '%市场部-公转私%' then '市场私域公导私'
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
when flow_pool_name like '%周长磊%' then '创新APP'
when source_manager_name in ('王春宵') then '武汉图书直播间'
when source_manager_name in ('高曼曼01','杨思怡','宋向函') then '图书KOC达人'
when flow_pool_name like '%市场部-原子合作%' then '原子'
when flow_pool_name like '%市场部-微信私域%' or flow_pool_name like '%市场部-规划报告%' or flow_pool_name like '%规划报告%' or flow_pool_name like '%市场部-小红书%' or flow_pool_name like '%孟浩宇%' then '市场私域低价单'
when flow_pool_name like '%待支付%' then '市场私域待支付'
when flow_pool_name like '%未加好友%' then '市场私域未加好友'
when flow_pool_name like '%内部换量%' then '市场私域首期掉海'
when flow_pool_name like '公导私' then '进校私域合作'
when (flow_pool_name like '%增长组%' or channel_name_3 = '公众号' or second_department_name = '微信生态部') and channel_name_2 <> 'APP' then '集团私域'
when put_plan_name  like '%济南格乐%' and put_plan_name  like '%表单%'  then '商务0元'
when put_plan_name like '%B类%' or put_plan_name like '%b类%' or channel_second_provider_name like '%KOC当期%' then 'KOC分层测试'
when put_plan_name like '%星耀%' or put_plan_name like '%物理展博%' or  put_plan_name like '%物理谢丽荣%' or put_plan_name like '%牟恩伯%' or  put_plan_name like '%王赞%' or put_plan_name like '%张磊老师高中数学%' or put_plan_name like '%雯姐高中物理大讲堂%' then '百度星耀'
when source_manager_name = '刘福云' and (sku_id_name like '%瑞春%' or sku_id_name like '%春春%') then '陈瑞春'
when source_manager_name = '刘福云' and sku_id_name like '%周帅%' then '周帅'
when third_department_name = '直播部' and sku_id_name like '%周帅%' and channel_name_2 in ('百度','B站')  then '周帅'
when third_department_name = '直播部' and sku_id_name like '%孟亚飞%' and rule_name like '%99%' then '孟亚飞99-1组'
when third_department_name = '直播部' and sku_id_name like '%孟亚飞%' then '孟亚飞9元'
when third_department_name = '直播部' and sku_id_name like '%朱汉祺%' then '朱博士29'
when third_department_name = '直播部' and sku_id_name like '%肖晗%' then '肖晗'
when flow_pool_name like '%0转低转正%' or channel_name_2='产研测试' then '进校私域合作'
when flow_pool_name like '%天津智慧双子%'	then '创新社群'
when third_department_name like '%城市定制%' then '点睛卷'
when period_name like '%多学科拓展%' and third_department_name like '%私域运营%' then '市场私域入群'
when put_plan_name like '%赠课失败%' and third_department_name = '线上商务部' then 'KOC赠课失败'
when flow_pool_name like '%自然流%' and source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07') and sku_id_name like '%周帅%' then 'KOC-周帅'
when flow_pool_name like '%自然流%' and source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07') and sku_id_name like '%肖晗%' then 'KOC-肖晗'
when flow_pool_name like '%自然流%' and source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07') and sku_id_name like '%朱汉祺%'  and flow_original_order_activity_price like '%1100%' then 'KOC-5元朱汉祺'
when flow_pool_name like '%自然流%' and source_manager_name in ('赵语诗','崔文轩','孙培尧')	then '自孵化KOC-5元纯课'
when flow_pool_name like '%自然流%' and (sku_id_name like '%朱博士%' or sku_id_name like '%朱汉祺%') and rule_name like '%9%' and rule_name not like '%29%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '朱博士9元'
when flow_pool_name like '%自然流%' and sku_id_name like '%朱博士%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '朱博士29'
when flow_pool_name like '%自然流%' and sku_id_name like '%亚飞%' and rule_name like '%99%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '孟亚飞99-1组'
when flow_pool_name like '%自然流%' and sku_id_name like '%亚飞%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组')  then '孟亚飞9元'
when flow_pool_name like '%自然流%' and sku_id_name like '%曹忆%' then '曹忆'
when flow_pool_name like '%自然流%' and rule_name like '%朱博士%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '朱博士29'
when flow_pool_name like '%自然流%' and source_manager_name like '%邵万昕%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '朱博士29'
when flow_pool_name like '%自然流%' and rule_name like '%亚飞%' and rule_name like '%99%' then '孟亚飞99-1组'
when flow_pool_name like '%自然流%' and rule_name like '%亚飞%'  then '孟亚飞9元'
when flow_pool_name like '%自然流%' and rule_name like '%郭艺%'  then '郭艺'
when flow_pool_name like '%自然流%' and rule_name like '%汤雪%'  then '汤老师'
when flow_pool_name like '%自然流%' and rule_name like '%曹忆%' then '曹忆'
when flow_pool_name like '%途途教室%' or first_department_name like 'TUTU' then '途途APP'
when second_department_name = '市场四部' then '市场四部'
when source_manager_name in ('宋莹莹','辛世如') and channel_name_2 in ('视频号') then '信息流-虚拟号挂车'
when rule_name like '%训练营%' and rule_name like '%市场私域%' then '市场私域入群'
when flow_pool_name like '%青少-私域%' then '青少私域'
when put_plan_name like '%AI名师%' then 'AI直播'
when channel_name_1= '信息流' and (put_plan_name like '%抖音私信%' or put_plan_name like '%初三0元%' or put_plan_name like '%高中0元%') then '信息流-抖音私信'
when rule_name like '%途途私域%' or (rule_name like '%私域%' and first_department_name = 'TT') then '途途私域'
else '其他未知流量' end as channel_map,
        rule_name,
        lead_purchase_intention_level2_category_name,
        nvl(lead_count, 0) as lead_count,
        nvl(valid_lead_count, 0) as valid_lead_count,
        nvl(conversion_lead_count, 0) as conversion_lead_count,
        nvl(subject_count, 0) as subject_count,
        nvl(same_lead_period_subject_count, 0) as same_lead_period_subject_count,
        nvl(lb_subject_count, 0) as lb_subject_count,
        nvl(same_lead_period_lb_subject_count, 0) as same_lead_period_lb_subject_count,
        nvl(order_count, 0) as order_count,
        nvl(income_amount, 0) as income_amount,
        nvl(in_pay_period_refund_amount, 0) as in_pay_period_refund_amount,
        nvl(non_pay_period_refund_amount, 0) as non_pay_period_refund_amount,
        nvl(jp_cross_department_refund_amount, 0) as jp_cross_department_refund_amount,
        nvl(same_lead_period_order_count, 0) as same_lead_period_order_count,
        nvl(same_lead_period_conversion_lead_count, 0) as same_lead_period_conversion_lead_count,
        nvl(same_lead_period_income_amount, 0) as same_lead_period_income_amount,
        nvl(same_lead_period_refund_amount, 0) as same_lead_period_refund_amount,
        case
            when date_diff('hour', cast(section_assign_time as timestamp), cast(first_call_time as timestamp)) >= 0
             and date_diff('hour', cast(section_assign_time as timestamp), cast(first_call_time as timestamp)) <= 24
             and nvl(valid_lead_count, 0) > 0 then 1
            else 0
        end as first_call_in_24h,
        nvl(
            case
                when nvl(valid_lead_count, 0) = 1 then friend_lead_count
                else 0
            end,
            0
        ) as is_friend_lead
    from data_base
)
,
order_attribute as (
    select
        cast(o.order_number as varchar) as order_number,
        o.performance_employee_email_name,
        max_by(cast(o.lead_id as varchar), coalesce(o.stats_trade_timestamp, o.pay_success_timestamp, '')) as lead_id,
        max_by(cast(o.original_order_user_number as varchar), coalesce(o.stats_trade_timestamp, o.pay_success_timestamp, '')) as order_attribute_user_id,
        max(
            case
                when o.pay_refund_type = '支付'
                 and o.is_pay_success_order = 1
                 and o.is_stats_conversion_num = 'Y'
                 and o.is_stats_conversion_amount = 'Y'
                 and coalesce(cast(o.income_amount as double), 0) > 0
                then 1 else 0
            end
        ) as is_stats_conversion_order,
        sum(
            case
                when o.pay_refund_type = '支付'
                 and o.is_pay_success_order = 1
                 and o.is_stats_conversion_amount = 'Y'
                then coalesce(cast(o.income_amount as double), 0) / 100.0
                else 0
            end
        ) as order_attribute_income_yuan,
        max_by(
            concat(
                date_format(
                    date_trunc(
                        'week',
                        date_parse(replace(concat(o.trade_group_period_year, o.trade_group_period_term), '期', ''), '%Y%m%d') - interval '1' day
                    ) + interval '4' day,
                    '%Y%m%d'
                ),
                '期'
            ),
            coalesce(o.stats_trade_timestamp, o.pay_success_timestamp, '')
        ) as order_attribute_period_name,
        max_by(o.pay_success_timestamp, coalesce(o.stats_trade_timestamp, o.pay_success_timestamp, '')) as attribute_pay_success_timestamp,
        max_by(o.stats_trade_timestamp, coalesce(o.stats_trade_timestamp, o.pay_success_timestamp, '')) as attribute_stats_trade_timestamp,
        count(*) as order_attribute_row_count
    from service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf o
    where o.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
      and o.hour = format_datetime(now() - interval '2' hour, 'HH')
      and o.course_first_level_department_name = 'H业务线'
      and o.course_second_level_department_name in ('市场部', '精品班学部', '青橙项目部', '菁英班学部', '本地化大班学部', '一对一学部')
      and o.performance_first_level_department_name = 'H业务线'
      and o.performance_second_level_department_name in ('市场部', '精品班学部', '青橙项目部', '菁英班学部', '本地化大班学部', '一对一学部')
      and o.performance_third_level_department_name in ('学习顾问部', '市场顾问部', '中价产品项目部')
    group by
        cast(o.order_number as varchar),
        o.performance_employee_email_name
),
finance_trade_raw as (
    select
        concat(
            date_format(
                date_trunc('week', cast(f.top_paid_time as timestamp) - interval '1' day) + interval '4' day,
                '%Y%m%d'
            ),
            '期'
        ) as paid_period_name,
        concat(
            date_format(
                date_trunc('week', cast(f.trade_time as timestamp) - interval '1' day) + interval '4' day,
                '%Y%m%d'
            ),
            '期'
        ) as trade_period_name,
        coalesce(cast(f.top_order_number as varchar), cast(f.order_number as varchar)) as top_order_number,
        cast(f.order_number as varchar) as order_number,
        cast(f.user_id as varchar) as user_id,
        f.type as performance_attribution_type,
        f.trade_type,
        f.trade_status,
        f.top_paid_time,
        f.trade_time,
        f.refund_order_number,
        f.employee_email_name,
        f.leader_employee_email_name,
        f.employee_first_level_department_name,
        f.employee_second_level_department_name,
        f.employee_third_level_department_name,
        cast(f.course_number as varchar) as course_number,
        f.course_biz_number,
        f.course_name,
        cast(f.clazz_number as varchar) as clazz_number,
        f.clazz_biz_number,
        f.clazz_name,
        f.clazz_type_name,
        f.course_grade,
        f.course_subject,
        f.course_term_id,
        f.course_year,
        f.teacher_name,
        f.teacher_nickname,
        cast(f.teacher_number as varchar) as teacher_number,
        f.course_first_level_department_name,
        f.course_second_level_department_name,
        f.course_third_level_department_name,
        cast(f.real_price as double) as real_price_yuan,
        cast(f.price as double) as attributed_price_yuan,
        cast(f.transfer_price as double) as transfer_price_yuan,
        cast(f.price_ratio as double) as price_ratio,
        case
            when f.trade_status in ('全部退款', '部分退款') then -cast(f.real_price as double)
            when f.trade_type = '调课调班' and f.trade_status in ('调出退款', '全部退款') then -cast(f.transfer_price as double)
            when f.trade_type = '调课调班' and f.trade_status = '支付' then cast(f.transfer_price as double)
            else cast(f.real_price as double)
        end as signed_trade_amount_yuan
    from finance_dw.app_finance_performance_extend_details_hf f
    where f.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
      and f.hour = format_datetime(now() - interval '2' hour, 'HH')
      and f.employee_first_level_department_name = 'H业务线'
      and f.employee_second_level_department_name = '市场部'
      and f.trade_type in ('正常订单', '调课调班')
      and concat(
            date_format(
                date_trunc('week', cast(f.top_paid_time as timestamp) - interval '1' day) + interval '4' day,
                '%Y%m%d'
            ),
            '期'
          ) in ('20260619期', '20260626期', '20260703期', '20260710期')
),
finance_trade_event as (
    select distinct
        paid_period_name,
        top_order_number,
        order_number,
        refund_order_number,
        trade_time,
        trade_type,
        trade_status,
        real_price_yuan,
        transfer_price_yuan,
        signed_trade_amount_yuan
    from finance_trade_raw
),
finance_net as (
    select
        paid_period_name,
        top_order_number,
        sum(coalesce(signed_trade_amount_yuan, 0)) as net_trade_amount_yuan,
        sum(case when signed_trade_amount_yuan < 0 then -signed_trade_amount_yuan else 0 end) as refund_amount_yuan,
        count(*) as all_trade_row_count
    from finance_trade_event
    group by paid_period_name, top_order_number
),
finance_positive as (
    select
        paid_period_name,
        trade_period_name,
        top_order_number,
        order_number,
        user_id,
        performance_attribution_type,
        trade_type,
        trade_status,
        top_paid_time,
        trade_time,
        employee_email_name,
        leader_employee_email_name,
        employee_first_level_department_name,
        employee_second_level_department_name,
        employee_third_level_department_name,
        course_number,
        course_biz_number,
        course_name,
        clazz_number,
        clazz_biz_number,
        clazz_name,
        clazz_type_name,
        course_grade,
        course_subject,
        course_term_id,
        course_year,
        teacher_name,
        teacher_nickname,
        teacher_number,
        course_first_level_department_name,
        course_second_level_department_name,
        course_third_level_department_name,
        max(real_price_yuan) as gross_paid_yuan,
        sum(coalesce(attributed_price_yuan, 0)) as attributed_paid_yuan,
        max(price_ratio) as price_ratio,
        count(*) as positive_payment_source_row_count
    from finance_trade_raw
    where trade_status = '支付'
      and coalesce(real_price_yuan, 0) > 0
    group by
        paid_period_name,
        trade_period_name,
        top_order_number,
        order_number,
        user_id,
        performance_attribution_type,
        trade_type,
        trade_status,
        top_paid_time,
        trade_time,
        employee_email_name,
        leader_employee_email_name,
        employee_first_level_department_name,
        employee_second_level_department_name,
        employee_third_level_department_name,
        course_number,
        course_biz_number,
        course_name,
        clazz_number,
        clazz_biz_number,
        clazz_name,
        clazz_type_name,
        course_grade,
        course_subject,
        course_term_id,
        course_year,
        teacher_name,
        teacher_nickname,
        teacher_number,
        course_first_level_department_name,
        course_second_level_department_name,
        course_third_level_department_name
),
finance_with_attribute as (
    select
        f.*,
        n.net_trade_amount_yuan,
        n.refund_amount_yuan,
        n.all_trade_row_count,
        a.lead_id,
        a.order_attribute_user_id,
        a.is_stats_conversion_order,
        a.order_attribute_income_yuan,
        a.order_attribute_period_name,
        a.attribute_pay_success_timestamp,
        a.attribute_stats_trade_timestamp,
        a.order_attribute_row_count
    from finance_positive f
    left join finance_net n
      on f.paid_period_name = n.paid_period_name
     and f.top_order_number = n.top_order_number
    left join order_attribute a
      on f.order_number = a.order_number
     and f.employee_email_name = a.performance_employee_email_name
),
lead_candidate as (
    select
        f.*,
        d.period_name as lead_period_name,
        d.dept_name as lead_section_second_department_name,
        d.depart_1 as lead_virtual_third_department_name,
        d.depart as lead_virtual_fourth_department_name,
        d.jingli,
        d.zhuguan,
        d.employee_email_name as lead_employee_email_name,
        d.channel_map,
        d.rule_name,
        d.lead_purchase_intention_level2_category_name as lead_grade_name,
        row_number() over (
            partition by
                f.paid_period_name,
                f.order_number,
                f.employee_email_name,
                coalesce(f.clazz_biz_number, ''),
                coalesce(f.course_biz_number, '')
            order by
                case when d.employee_email_name = f.employee_email_name then 0 else 1 end,
                case when d.period_name = f.paid_period_name then 0 else 1 end,
                d.period_name desc,
                d.employee_email_name
        ) as lead_match_rank
    from finance_with_attribute f
    left join data d
      on f.lead_id = cast(d.lead_id as varchar)
),
detail_base as (
    select
        l.*,
        case
            when l.lead_id is null then '订单未匹配lead_id'
            when l.lead_employee_email_name is null then 'lead_id未匹配全链路线索'
            when l.lead_employee_email_name = l.employee_email_name and l.lead_period_name = l.paid_period_name then '顾问和期次精确匹配'
            when l.lead_employee_email_name = l.employee_email_name then '顾问精确匹配_期次回退'
            else '仅lead_id回退匹配'
        end as lead_match_type,
        case when l.lead_section_second_department_name = '市场部' then 1 else 0 end as is_lead_market_scope,
        row_number() over (
            partition by l.paid_period_name, l.order_number
            order by coalesce(l.clazz_biz_number, ''), coalesce(l.course_biz_number, ''), l.employee_email_name
        ) as order_row_number,
        row_number() over (
            partition by l.paid_period_name, l.top_order_number
            order by l.order_number, coalesce(l.clazz_biz_number, ''), l.employee_email_name
        ) as parent_order_row_number,
        row_number() over (
            partition by l.paid_period_name, l.user_id
            order by l.order_number, coalesce(l.clazz_biz_number, ''), l.employee_email_name
        ) as period_user_row_number,
        row_number() over (
            partition by l.paid_period_name, coalesce(l.channel_map, '未匹配渠道'), l.user_id
            order by l.order_number, coalesce(l.clazz_biz_number, ''), l.employee_email_name
        ) as channel_user_row_number,
        row_number() over (
            partition by
                l.paid_period_name,
                coalesce(l.channel_map, '未匹配渠道'),
                coalesce(l.course_grade, l.lead_grade_name, '未知年级'),
                l.user_id
            order by l.order_number, coalesce(l.clazz_biz_number, ''), l.employee_email_name
        ) as channel_grade_user_row_number
    from lead_candidate l
    where l.lead_match_rank = 1
)
select
    paid_period_name as "支付期次",
    trade_period_name as "交易流水期次",
    lead_period_name as "线索期次",
    order_attribute_period_name as "订单归因流水期次",
    case when paid_period_name = lead_period_name then '当期线索' else '跨期线索' end as "线索跨期类型",
    coalesce(channel_map, '未匹配渠道') as "渠道",
    rule_name as "规则名称",
    lead_grade_name as "线索年级",
    employee_first_level_department_name as "财务业绩一级部门",
    employee_second_level_department_name as "财务业绩二级部门",
    employee_third_level_department_name as "财务业绩三级部门",
    lead_section_second_department_name as "线索截面二级部门",
    lead_virtual_third_department_name as "线索虚拟三级部门",
    lead_virtual_fourth_department_name as "线索虚拟四级部门",
    jingli as "经理",
    zhuguan as "主管",
    lead_employee_email_name as "线索承接顾问",
    employee_email_name as "财务业绩顾问",
    leader_employee_email_name as "财务业绩顾问上级",
    lead_match_type as "线索匹配方式",
    lead_id as "线索id",
    user_id as "用户id",
    order_attribute_user_id as "订单归因用户id",
    top_order_number as "原始父订单号",
    order_number as "订单号",
    performance_attribution_type as "业绩归属类型",
    trade_type as "交易类型",
    trade_status as "交易状态",
    top_paid_time as "原始支付时间",
    trade_time as "交易时间",
    course_number as "课程id",
    course_biz_number as "课程业务编号",
    course_name as "课程名称",
    clazz_number as "班级id",
    clazz_biz_number as "班级业务编号",
    clazz_name as "班级名称",
    clazz_type_name as "班级标签",
    course_grade as "年级",
    course_subject as "科目",
    course_term_id as "学季",
    course_year as "学年",
    teacher_number as "主讲id",
    teacher_name as "主讲名称",
    teacher_nickname as "主讲昵称",
    course_first_level_department_name as "课程一级部门",
    course_second_level_department_name as "课程二级部门",
    course_third_level_department_name as "课程三级部门",
    gross_paid_yuan as "实付金额_元",
    attributed_paid_yuan as "财务归属金额_元",
    order_attribute_income_yuan as "运营归因收款_元",
    net_trade_amount_yuan as "父订单净流水_元",
    refund_amount_yuan as "父订单退款额_元",
    price_ratio as "财务金额归属比例",
    coalesce(is_stats_conversion_order, 0) as "是否计统计转化",
    is_lead_market_scope as "线索是否属于市场部范围",
    case
        when coalesce(is_stats_conversion_order, 0) = 1
         and is_lead_market_scope = 1
         and order_attribute_period_name = paid_period_name
        then 1 else 0
    end as "是否符合运营看板转化口径",
    case when order_row_number = 1 then 1 else 0 end as "正向支付订单数_去重",
    case when period_user_row_number = 1 then 1 else 0 end as "期次正向支付用户数_去重",
    case when channel_user_row_number = 1 then 1 else 0 end as "渠道内正向支付用户数_去重",
    case when channel_grade_user_row_number = 1 then 1 else 0 end as "渠道年级内正向支付用户数_去重",
    case when order_row_number = 1 then gross_paid_yuan else 0 end as "实付金额_去重",
    case when parent_order_row_number = 1 then net_trade_amount_yuan else 0 end as "父订单净流水_去重",
    case when parent_order_row_number = 1 then refund_amount_yuan else 0 end as "父订单退款额_去重",
    case
        when order_row_number = 1
         and coalesce(is_stats_conversion_order, 0) = 1
         and is_lead_market_scope = 1
         and order_attribute_period_name = paid_period_name
        then 1 else 0
    end as "运营口径订单数_去重",
    positive_payment_source_row_count as "正向支付底层行数",
    all_trade_row_count as "父订单全部流水行数",
    order_attribute_row_count as "订单归因底层行数"
from detail_base
order by
    paid_period_name,
    coalesce(channel_map, '未匹配渠道'),
    employee_email_name,
    order_number,
    clazz_biz_number
