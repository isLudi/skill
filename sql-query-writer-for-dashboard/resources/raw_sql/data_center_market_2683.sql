-----------------------------------APP登录
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
            ('market_consultant', 'lead_period', '20260809期', date '2026-08-07', date '2026-08-12', 1),
            ('market_consultant', 'class_period', '20260809期', date '2026-08-07', date '2026-08-12', 1),
            ('market_consultant', 'trade_period', '20260809期', date '2026-08-07', date '2026-08-12', 1)
    ) as t(business_domain, date_role, qici, period_start_date, period_end_date, enabled)
),
denglu_app as
(
    select distinct
        user_latest.user_number,
        user_latest.last_event_time,
        user_latest.product_name,
        user_latest.appliction_name,
        case when user_latest.event_timestamp >= now() - interval '7' day and user_latest.appliction_name in ('PC客户端','APP','PC') then 1 else 0 end as is_app_denglu,
        user_latest.event_timestamp,
        now() - interval '7' day as seven_days_ago,
        date_diff('day', cast(user_latest.event_timestamp as date), current_date) as days_diff_simple
    from
    (
        select
            ul.user_number,
            ul.last_event_time,
            ul.product_name,
            ul.appliction_name,
            try(date_parse(ul.last_event_time, '%Y-%m-%d %H:%i:%s:%f')) as event_timestamp
        from (
            select *,
                row_number() over (partition by user_number order by try(date_parse(last_event_time, '%Y-%m-%d %H:%i:%s:%f')) desc) as rn
            from dw.dim_cstm_active_user_c_appliction_mb_df
            where dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
                and product_name in ('高途','规划精品')
        ) ul
        where rn = 1
    ) user_latest
)
------------------------用户最新登录设备
,app_ph as
(
    select distinct
        user_latest.user_number,
        user_latest.last_event_time,
        user_latest.last_app_channel
    from
    (
        select
            ul.user_number,
            ul.last_event_time,
            ul.last_app_channel,
            try(date_parse(ul.last_event_time, '%Y-%m-%d %H:%i:%s:%f')) as event_timestamp
        from (
            select *,
                row_number() over (partition by user_number order by try(date_parse(last_event_time, '%Y-%m-%d %H:%i:%s:%f')) desc) as rn
            from dw.dim_cstm_active_user_c_appliction_mb_df
            where dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
                and appliction_name = 'APP'
        ) ul
        where rn = 1
    ) user_latest
)
------------------------基础数据
,data as
(select distinct
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
 virtual_third_department_name  depart_1,
virtual_fourth_department_name  depart,
    virtual_leader_email_name  jingli,-- 大组长
    virtual_direct_leader_email_name  zhuguan, -- 小组长
    employee_email_name,
     employee_email_prefix,
    t1.lead_id,
    user_id,
    substr(section_assign_time, 1, 10) as assign_day,
case when rule_name like '%北京直播江苏%' then '北京直播江苏'
when flow_pool_name in ('高途学习规划','智辉老师讲规划') then '市场私域视频号'
when rule_name like '%语数英%' and third_department_name = '新媒体内容运营部' then '语数英'
when third_department_name='图书营销部' and sku_id_name like '%孟亚飞99%' then '孟亚飞99'
when third_department_name = '投放部' and ad_account_name like '%周帅%' then '信息流-周帅'
when source_manager_name in ('韩正卿') then '抖音私信'
when third_department_name = '私域运营部' and source_manager_name in ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研','岳一帆02','田起帆') then '进校私域合作'
when channel_name_1='市场私域' and (virtual_fourth_department_name in ('郑州学习顾问二部','郑州学习顾问七部','郑州训练营') or virtual_fifth_department_name in ('罗江博团队')) then '市场私域入群'
when put_plan_name like '%周司鹏%' then '品宣组KOC'
when put_plan_name like '%公导私%' and put_plan_name like '%未购课%' then '公导私报名失败'
when third_department_name = '图书营销部' and rule_name like '%点睛卷%' then '押题卷'
when put_plan_name like '%迪九学%' then '市场私域代运营'
when third_department_name = '投放部' and channel_name_2 = '小红书' and channel_name_1 <> '搜索营销' then '信息流-小红书'
when third_department_name = '线上商务部' and channel_name_2 = '小红书' then '小红书'
when (flow_pool_name like '%肖晗%' or sku_id_name like '%肖晗%' or put_plan_name like '%肖晗9元%') and third_department_name='直播部'  then '肖晗'
when (flow_pool_name like '%北大汤哥%' or flow_pool_name like '%海淀名师高阶%') and sku_id_name like '%小艺%'  then '郭艺'
when  third_department_name like '%私域%' and rule_name like '%私域%' and rule_name like '%图书%' then '市场私域图书'
when  third_department_name like '%私域%' and rule_name like '%品效%'  then '市场私域品效'
when  third_department_name like '%私域%' and rule_name like '%公域学霸%'  then '市场私域公域组'
when  third_department_name like '%私域%' and rule_name like '%IE%'  then '市场私域IE'
when  third_department_name like '%私域%' and rule_name like '%裂变%'  then '市场私域裂变'
when third_department_name in ('直播部','新媒体内容运营部','市场一组','私域运营部') and put_plan_name like '%退%' and flow_pool_name ='电商退款用户池'  then '退款订单复用'
when third_department_name in ('直播部','新媒体内容运营部','市场一组','私域运营部') and put_plan_name like '%失败%' and flow_pool_name ='电商退款用户池'  then '赠课失败'
when third_department_name in ('直播部','新媒体内容运营部','市场一组')  and flow_pool_name ='初阶化学规划'  then '曹忆'
when (third_department_name = '图书营销部' and sku_id_name like '%真题%') or (third_department_name='直播部' and sku_id_name like '%真题%') then '西安图书直播间-直播'
when (third_department_name = '图书营销部' and sku_id_name not like '%真题%') or (third_department_name='直播部' and sku_id_name  like '%秒懂%') or (third_department_name='直播部' and sku_id_name  like '%图书赠送%') then '西安图书直播间-挂链'
when rule_name like '%99元智学%' then 'AI直播'
when channel_provider_name = '宿迁伯岳' then '小程序'
when third_department_name in ('直播部','新媒体内容运营部','市场一组') and (flow_pool_name like '%海淀高阶名师%' or flow_pool_name like '%海淀老师高阶%' or flow_pool_name like '%小艺%') then '郭艺'
when put_plan_name like '%国培教育-0元%' or put_plan_name like '%易喆教育-0元%' or put_plan_name like '%钟情-0元%' or put_plan_name like '%中望达-0元%' or put_plan_name like '%晨硕-0元%' or put_plan_name like '%彩石-0元入群%'  then '创新商务入群'
when put_plan_name like '%0元入群-进校%' and third_department_name = '线上商务部' then '创新商务入群'
when put_plan_name like '%qq0元%' and third_department_name = '线上商务部' then '创新QQ'
when third_department_name='KOC孵化部' and flow_pool_name like '%电商退款%' and put_plan_name like '%失败%' then '自孵化KOC-赠课失败'
when third_department_name='KOC孵化部' and flow_pool_name like '%电商退款%' and put_plan_name like '%退%' then '自孵化KOC-退款订单复用'
when source_manager_name = '方俊结01' and put_plan_name like '%赠课后退款%' then 'KOC-赠课后退款'
when third_department_name = '直播部' and (sku_id_name like '%春春%' or sku_id_name like '%瑞春%' or rule_name like '%春春%' or rule_name like '%瑞春%') then '陈瑞春'
when third_department_name = '直播部' and (sku_id_name like '%朱博士99%' or rule_name like '%朱汉祺99%') then '朱博士99'
when (third_department_name = '直播部' and (sku_id_name like '%朱博士%' or sku_id_name like '%朱汉祺%') and rule_name like '%9%' and rule_name not like '%29%' and sku_id_name not like '%急%' and sku_id_name not like '%礼盒29%') or (third_department_name = '直播部' and sku_id_name like '%朱博士9%') then '朱博士9元'
when channel_name_1 = '商务' and channel_name_2 = '短信' then '短信'
when ad_account_name like '%肖晗%' and channel_name_1 = '信息流' then '信息流-肖晗'
when channel_name_1 = '信息流' and channel_name_2='B站' and (page_id_name like '%亚飞%' or ad_account_name like '%亚飞%') then 'B站信息流-亚飞'
when channel_name_1 = '信息流' and (page_id_name like '%亚飞%' or ad_account_name like '%亚飞%') then '信息流-亚飞'
when (flow_pool_name like '%朱博士%' or flow_pool_name like '%双博士%' or flow_pool_name like '%教育规划%') and third_department_name <> '线上商务部' and period_name not like '%多学科拓展%' and rule_name not like '%张杰%' and sku_id_name not like '%马凯鹏IP%' and third_department_name='直播部' then '朱博士29'
when put_plan_name like '%朱博士说教育%' and period_name not like '%多学科拓展%' and flow_pool_name not like '%高分讲堂%' and  flow_pool_name not like '%总裁%' and third_department_name='直播部' then '朱博士29'
when flow_pool_name like '%朱博士讲英语%' and sku_id_name like '%马凯鹏IP%' and third_department_name='直播部' then '马凯鹏29'
when (flow_pool_name like '%朱博士讲英语%' or flow_pool_name like '%朱博士英语%' or flow_pool_name like '%朱汉祺说英语%' or flow_pool_name like '%朱博士说英语%' or flow_pool_name like '%教育规划%' or flow_pool_name like '%双博士英语规划%' or flow_pool_name like '%朱博士满分英语%' or flow_pool_name like '%英语教父朱博士%' or (flow_pool_name like '%中考决胜天团%' and lead_purchase_intention_level1_category_name = '规划系统')) and third_department_name = '直播部' and period_name not like '%多学科拓展%' and sku_id_name not like '%马凯鹏IP%' and third_department_name='直播部' then '朱博士29'
when (flow_pool_name like '%汤哥%' or flow_pool_name like '%汤老师%') and period_name not like '%多学科拓展%' and third_department_name in ('直播部','新媒体内容运营部')  then '汤老师'
when (flow_pool_name like '%中考百日冲刺%') and period_name not like '%多学科拓展%' and third_department_name='直播部'  then '曹忆9.9纯课'
when (flow_pool_name like '%马总%' or  flow_pool_name = '减法化学马老师' or flow_pool_name like '%总裁讲化学%' or flow_pool_name like '%高分讲堂%') and period_name not like '%多学科拓展%' and sku_id_name  like '%99%' and third_department_name='直播部'  then '马凯鹏99'
when (flow_pool_name like '%马总%' or  flow_pool_name = '减法化学马老师' or flow_pool_name like '%总裁讲化学%' or flow_pool_name like '%高分讲堂%') and period_name not like '%多学科拓展%' and sku_id_name not like '%99%' and third_department_name='直播部'  then '马凯鹏29'
when (flow_pool_name like '%北大杰哥%' or flow_pool_name like '%张小杰%') and period_name not like '%多学科拓展%' and third_department_name='直播部' then '张杰'
when flow_pool_name like '%教育规划%' and rule_name like '%张杰%' and third_department_name='直播部' then '张杰'
when source_manager_name = '陈晓菁04' and channel_provider_name not like '%开拓%' and put_plan_name not like '%九学%' then '商务低价'
when (flow_pool_name like '%孟帝%' or flow_pool_name like '%孟老师%' or flow_pool_name like '%中考数学冲刺%' or flow_pool_name like '%8升9数学%' or flow_pool_name like '%孟亚飞讲数学%' or flow_pool_name like '%中考冲刺%' or flow_pool_name like '%中考满分冲刺%' or flow_pool_name like '%押题王孟亚飞%' or flow_pool_name like '%中考数学大通关%' or flow_pool_name like '%中考数学规划%' or flow_pool_name like '%亚飞数学%')  and period_name not like '%多学科拓展%' and channel_name_2 not like '%KOL%' and third_department_name='直播部' and rule_name like '%99%'  then '孟亚飞99'
when (flow_pool_name like '%孟帝%' or flow_pool_name like '%孟老师%' or flow_pool_name like '%中考数学冲刺%' or flow_pool_name like '%8升9数学%' or flow_pool_name like '%孟亚飞讲数学%' or flow_pool_name like '%中考冲刺%' or flow_pool_name like '%中考满分冲刺%' or flow_pool_name like '%押题王孟亚飞%' or flow_pool_name like '%中考数学大通关%' or flow_pool_name like '%中考数学规划%' or flow_pool_name like '%亚飞数学%')  and period_name not like '%多学科拓展%' and channel_name_2 not like '%KOL%' and third_department_name='直播部'  then '孟亚飞9元'
when put_plan_name like '%刘家晋讲图文%' or put_plan_name like '%孟帝数学%' and third_department_name='直播部' and rule_name like '%99%'  then '孟亚飞99'
when put_plan_name like '%刘家晋讲图文%' or put_plan_name like '%孟帝数学%' and third_department_name='直播部' then '孟亚飞9元'
when (flow_pool_name like '%肖晗%' or sku_id_name like '%肖晗%') and third_department_name='直播部'  then '肖晗'
when flow_pool_name like '%峥峥%' and period_name not like '%多学科拓展%' and third_department_name='直播部'  then '何峥峥'
when flow_pool_name like '%汐子%' and period_name not like '%多学科拓展%' and sku_id_name not like '%亚飞%' and third_department_name='直播部'  then '王汐子'
when flow_pool_name like '%汐子%' and period_name not like '%多学科拓展%' and sku_id_name  like '%亚飞%' and third_department_name='直播部' and rule_name like '%99%'  then '孟亚飞99'
when flow_pool_name like '%汐子%' and period_name not like '%多学科拓展%' and sku_id_name  like '%亚飞%' and third_department_name='直播部' then '孟亚飞9元'
when (flow_pool_name like '%曹忆%' or flow_pool_name like '%dudu%' or flow_pool_name like '%中考决胜天团%' or flow_pool_name like '%具象思维%' or flow_pool_name like '%在逃发面馒头%' or flow_pool_name like '%库洛米%' and lead_purchase_intention_level1_category_name <> '规划系统') and period_name not like '%多学科拓展%' and third_department_name in ('直播部','新媒体内容运营部') then '曹忆'
when flow_pool_name = '正价课判单补录' then '正价课判单补录'
when channel_name_1 = '转介绍' then '转介绍'
when first_department_name ='市场部' and channel_name_1 <> '站内获客' and channel_name_2 <> 'APP' then '集团私域'
when put_plan_name like '%未加好友%' then '市场私域未加好友'
when put_plan_name like '%私域-信息流%' then '市场私域待支付'
when third_department_name = '私域运营部' and rule_name not like '%训练营%' and virtual_fifth_department_name not in ('罗江博团队') and rule_name not like '%复用%' and rule_name not like '%未加好友%' and channel_name_2 <> '内部换量' then '市场私域低价单'
when third_department_name = '私域运营部' and channel_name_1 = '信息流获客' then '市场私域小红书'
when channel_name_1= '信息流' and (put_plan_name like '%抖音私信%' or put_plan_name like '%初三0元%' or put_plan_name like '%高中0元%') then '信息流-抖音私信'
when channel_name_2 in ('APP','M站','PC') and flow_pool_name not like '%途途%' then 'APP'
when source_manager_name in ('高文羽') and lead_purchase_intention_name = 'AI定制' then '人工外呼-AI'
when channel_provider_name like '%唐山TMK%' then '唐山TMK'
when source_manager_name in ('高文羽') and channel_provider_name not like '%唐山TMK%' and channel_provider_name not like '%郑州%' then '人工外呼'
when source_manager_name in ('高文羽') and channel_provider_name not like '%唐山TMK%' and channel_provider_name  like '%郑州%' then '郑州TMK-2组'
when source_manager_name = '冯银晨' and channel_name_2 = '小红书' then '信息流-小红书'
when channel_name_1 = '信息流获客' and flow_original_order_activity_price like '%1990%' then '信息流19'
when (channel_name_1 = '信息流' and channel_name_2 <> 'B站' and third_department_name NOT LIKE '%商务%' and put_plan_name not like '%初三0元%' and put_plan_name not like '%抖音私信%' and put_plan_name not like '%高中0元%' and flow_original_order_activity_price not like '%1990%') or (channel_name_2 = 'B站' and third_department_name like '%投放%') then '信息流'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and (page_id_name like '%郭艺%') then 'B站信息流-郭艺'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and (page_id_name like '%朱博士%') then 'B站信息流-朱汉祺'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and page_id_name like '%肖晗%' then 'B站信息流-肖晗'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and (page_id_name like '%马凯鹏%' or ad_account_name like '%化学%') then 'B站信息流-马凯鹏'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and  (sku_id_name like '%陈瑞春%' or rule_name like '%陈瑞春%') and (ad_account_name  like '%语文%' or source_put_plan_name like '%自然流%' or page_id_name like '%春春%') then 'B站信息流-陈瑞春'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and (flow_original_order_activity_price like '%2990%' or sku_id_name like '%帅师%' or sku_id_name like '%周帅%') and ad_account_name like '%语文%' and  (flow_original_order_activity_price like '%1980%' or flow_original_order_activity_price like '%2980%' or flow_original_order_activity_price like '%2990%') then 'B站信息流-陈瑞春'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and (flow_original_order_activity_price like '%2990%' or sku_id_name like '%帅师%' or sku_id_name like '%周帅%') and ad_account_name not like '%语文%' then 'B站信息流-周帅'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and flow_order_price like '%1980%' and ad_account_name like '%数学%' then 'B站信息流-周帅'
when channel_name_1 = '短直电商' and channel_name_2 = 'B站' and third_department_name  like '%商务%' and  sku_id_name like '%陈瑞春%' and flow_pool_name like '%自然流%'  then 'B站信息流-陈瑞春'
when channel_name_1 = '短直电商' and channel_name_2 = 'B站' and third_department_name  like '%商务%' and  sku_id_name like '%朱博士%' and flow_pool_name like '%自然流%'  then 'B站信息流-朱汉祺'
when third_department_name = '线上商务部' and channel_name_2 = 'B站' and put_plan_name like '%春春%' then 'B站信息流-陈瑞春'
when third_department_name = '线上商务部' and channel_name_2 = 'B站' and put_plan_name like '%朱博士%' then 'B站信息流-朱汉祺'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and flow_original_order_activity_price not like '%2980%' and flow_original_order_activity_price not like '%2990%' and flow_original_order_activity_price not like '%1980%' then 'B站信息流'
when flow_pool_name = '百度搜索引擎' or channel_name_1='搜索营销' then '信息流搜索'
when channel_name_1 = '信息流获客' and channel_name_2 = '小红书' and source_manager_name in ('王慧敏13','张琳02','王樱琦01') then '小红书投放'
when  flow_pool_name like '%小红书班课%' then '小红书投放'
when third_department_name = '投放部' and get_customer_way_name = '短视频信息流' and flow_original_order_activity_price like '%100%' then '信息流'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') and (sku_id_name like '%原型题%') then 'KOC-书课包'
when flow_pool_name = '中考加油' then 'KOC-5元纯课'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') and (sku_id_name like '%肖晗%' or rule_name like '%肖晗%') then 'KOC-肖晗'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') and period_name not like '%多学科拓展%' and (flow_original_order_activity_price like '%1100%' or flow_original_order_activity_price like '%500%' or flow_orders_income_amount like '%500%') and (sku_id_name like '%朱汉祺%' or sku_id_name like '%朱博士%' or rule_name like '%朱汉祺5元%' or sku_id_name like '%koc5元-朱博士%' or rule_name like '%朱汉祺%') then 'KOC-5元朱汉祺'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') and (sku_id_name like '%朱汉祺%' or sku_id_name like '%29元%' or sku_id_name like '%朱博士%' or rule_name like '%朱汉祺%' or rule_name like '%朱博士%' ) and (flow_original_order_activity_price not like '%1100%' or rule_name like '%29%') and sku_id_name not like '%周帅%' then 'KOC-5元朱汉祺'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') and period_name not like '%多学科拓展%' and sku_id_name not like '%朱汉祺%' and sku_id_name not like '%朱博士%' and sku_id_name not like '%周帅%' and sku_id_name not like '%29元%' then 'KOC-5元纯课'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') and sku_id_name like '%周帅%' then 'KOC-周帅'
--when (channel_name_2 like '%KOL%' and source_manager_name in ('崔文轩','孙培尧')) or (channel_name_2 like '%抖音%' and source_manager_name in ('徐绮鹤')) and period_name not like '%多学科拓展%' then '自孵化KOC'
when third_department_name in ('品牌效能部','KOC孵化部') and channel_name_2 in ('抖音','视频号','快手','KOL')  then '自孵化KOC-5元纯课'
when third_department_name in ('品牌效能部','KOC孵化部') and channel_name_2 in ('抖音','视频号','快手','KOL') and (sku_id_name like '%5元%'or sku_id_name like '%11元%' or flow_original_order_activity_price like '%1100%' or flow_original_order_activity_price like '%500%' or flow_orders_income_amount  like '%1100%' or flow_orders_income_amount  like '%500%' ) then '自孵化KOC-5元纯课'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') and channel_name_2 like '%社群%' then '进校社群'
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
when flow_pool_name like '%青岛寻知%' or flow_pool_name like '%禾兴信息%' then '商务0元'
when put_plan_name like '%益企发1元%' or put_plan_name like '%腾瑞教育1元%' then '进校APP合作'
when put_plan_name like '%外部图书供量%' or  flow_pool_name='高途旗舰店—线索—yuxinru' then  '外部图书慧敏'
when source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and channel_name_2 like '%社群%' then '创新社群'
when source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and (channel_name_2 like '%直推%' or put_plan_name like '%直推%') then '创新直推'
when source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and (channel_name_2 like '%书商%' or put_plan_name like '%书商%' or page_id_name like '%书商%') then '创新书商'
when source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and channel_name_2 like '%TMK%' and page_id_name like '%1元%' then '创新TMK1元'
when source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and channel_name_2 like '%TMK%' and page_id_name like '%9元%' then '创新TMK9元'
when source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and (channel_name_2 like '%直播%' or page_id_name like '%进校%') then '创新直播'
when source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and channel_name_2<>'公众号' and channel_name_1 = '商务' and flow_pool_name <> '高途云集图书专营店-自然流' and flow_pool_name <> '高途旗舰店—线索—yuxinru' and put_plan_name not like '%社群%' and put_plan_name not like '%小红书班课%' and put_plan_name not like '%外部图书供量%' and channel_second_provider_name not like '%沃德丰店铺线索赠课%' and channel_second_provider_name not like '%智慧城-图书%' and put_plan_name not like '%育甲%' and flow_pool_name not like '%周长磊%'  then '创新商务'
when flow_pool_name like '%周长磊%' then '创新APP'
when channel_provider_name like '%唐成刚%' or flow_pool_name = '高途云集图书专营店-自然流' then '图书唐成刚'
when channel_second_provider_name like '%沃德丰店铺线索赠课%' or channel_second_provider_name like '%智慧城-图书%' or put_plan_name like '%育甲%' then '外部图书慧敏'
when flow_pool_name like '%高途图书产品学部%' then '图书任炯旭'
when source_manager_name in ('王春宵') then '武汉图书直播间'
when source_manager_name in ('高曼曼01','杨思怡','宋向函') then '图书KOC达人'
when flow_pool_name like '%高中视频书%' or flow_pool_name like '%高中教辅书%' or flow_pool_name like '%朵拉老师%' then '北京图书直播间'
when flow_pool_name like '%市场部-原子合作%' then '原子'
when flow_pool_name like '%市场部-微信私域%' or flow_pool_name like '%市场部-规划报告%' or flow_pool_name like '%规划报告%' or flow_pool_name like '%市场部-小红书%' or flow_pool_name like '%孟浩宇%' then '市场私域低价单'
when flow_pool_name like '%待支付%' then '市场私域待支付'
when flow_pool_name like '%未加好友%' then '市场私域未加好友'
when flow_pool_name like '%内部换量%' then '市场私域首期掉海'
when flow_pool_name like '公导私' then '进校私域合作'
when source_manager_name in ('方宇02','李月林') then '菁英市场流量'
when channel_name_2 = '公众号' then '公众号'
when (flow_pool_name like '%增长组%' or channel_name_3 = '公众号' or second_department_name = '微信生态部') and channel_name_2 <> 'APP' then '集团私域'
when put_plan_name  like '%济南格乐%' and put_plan_name  like '%表单%'  then '商务0元'
when put_plan_name like '%B类%' or put_plan_name like '%b类%' or channel_second_provider_name like '%KOC当期%' then 'KOC分层测试'
when put_plan_name like '%星耀%' or put_plan_name like '%物理展博%' or  put_plan_name like '%物理谢丽荣%' or put_plan_name like '%牟恩伯%' or  put_plan_name like '%王赞%' or put_plan_name like '%张磊老师高中数学%' or put_plan_name like '%雯姐高中物理大讲堂%' then '百度星耀'
when source_manager_name = '刘福云' and (sku_id_name like '%瑞春%' or sku_id_name like '%春春%') then '陈瑞春'
when source_manager_name = '刘福云' and sku_id_name like '%周帅%' then '周帅'
when third_department_name = '直播部' and sku_id_name like '%周帅%' then '周帅'
when third_department_name = '直播部' and sku_id_name like '%孟亚飞%' and sku_id_name like '%199%' then '孟亚飞199'
when third_department_name = '直播部' and sku_id_name like '%孟亚飞%' and rule_name like '%99%' then '孟亚飞99'
when third_department_name = '直播部' and sku_id_name like '%孟亚飞%' then '孟亚飞9元'
when third_department_name = '直播部' and sku_id_name like '%朱汉祺%' then '朱博士29'
when third_department_name = '直播部' and sku_id_name like '%肖晗%' then '肖晗'
when flow_pool_name like '%0转低转正%' or channel_name_2='产研测试' then '进校私域合作'
when  source_manager_name in ('陈甜06','梁晓敏') then '图书挂车'
when flow_pool_name like '%天津智慧双子%'	then '创新社群'
when third_department_name like '%城市定制%' then '点睛卷'
when first_department_name like '%KM%' and flow_pool_name not like '%天津智慧双子%' then '途途商务'
when period_name like '%多学科拓展%' and third_department_name like '%私域运营%' then '市场私域入群'
when put_plan_name like '%赠课失败%' and third_department_name = '线上商务部' then 'KOC赠课失败'
when flow_pool_name like '%自然流%' and source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') and sku_id_name like '%周帅%' then 'KOC-周帅'
when flow_pool_name like '%自然流%' and source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') and sku_id_name like '%肖晗%' then 'KOC-肖晗'
when flow_pool_name like '%自然流%' and source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') and sku_id_name like '%朱汉祺%'  and flow_original_order_activity_price like '%1100%' then 'KOC-5元朱汉祺'
when flow_pool_name like '%自然流%' and source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') and sku_id_name like '%朱汉祺%'  and flow_original_order_activity_price not like '%1100%' then 'KOC-朱汉祺29'
when flow_pool_name like '%自然流%' and source_manager_name in ('赵语诗','崔文轩','孙培尧')	then '自孵化KOC-5元纯课'
when flow_pool_name like '%自然流%' and (sku_id_name like '%朱博士%' or sku_id_name like '%朱汉祺%') and rule_name like '%9%' and rule_name not like '%29%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '朱博士9元'
when flow_pool_name like '%自然流%' and sku_id_name like '%朱博士%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '朱博士29'
when flow_pool_name like '%自然流%' and sku_id_name like '%亚飞%' and rule_name like '%99%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '孟亚飞99'
when flow_pool_name like '%自然流%' and sku_id_name like '%亚飞%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组')  then '孟亚飞9元'
when flow_pool_name like '%自然流%' and sku_id_name like '%曹忆%' then '曹忆'
when flow_pool_name like '%自然流%' and rule_name like '%朱博士%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '朱博士29'
when flow_pool_name like '%自然流%' and source_manager_name like '%邵万昕%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '朱博士29'
when flow_pool_name like '%自然流%' and rule_name like '%亚飞%' and rule_name like '%99%' then '孟亚飞99'
when flow_pool_name like '%自然流%' and rule_name like '%亚飞%'  then '孟亚飞9元'
when flow_pool_name like '%自然流%' and rule_name like '%曹忆%' then '曹忆'
when flow_pool_name like '%途途教室%' or first_department_name like 'TUTU' then '途途APP'
when second_department_name = '市场二部' and get_customer_way_name = 'KOL直播' then '市场二部KOC'
when second_department_name = '市场四部' then '市场四部'
when source_manager_name in ('宋莹莹','辛世如') and channel_name_2 in ('视频号') then '信息流-虚拟号挂车'
when put_plan_name like '%高三复读%' then '市场私域高三复读'
when put_plan_name ='美玲测试' then '途途信息流私信'
when rule_name like '%训练营%' and rule_name like '%市场私域%' then '市场私域入群'
when flow_pool_name like '%青少-私域%' then '青少私域'
when first_department_name = 'TT业务线' and third_department_name like '%商务招生%' then '途途商务'
when second_department_name = '战略客户部' then '文旅进校'
when put_plan_name like '%AI名师%' then 'AI直播'
else '其他未知流量' end as channel_map,
case
            when rule_name like '%高一%' then '高一'
            when rule_name like '%高二%' then '高二'
            when rule_name like '%高三%' then '高三'
            when rule_name like '%初二%' then '初二'
            when rule_name like '%初三%' then '初三'
            else '未知'
        end as grade_1,
 city_level_name,
  coalesce(lead_count, 0) as lead_count,
    coalesce(valid_lead_count, 0) as valid_lead_count,
    coalesce(conversion_lead_count, 0) as conversion_lead_count,
    coalesce(subject_count, 0) as subject_count,
    coalesce(same_lead_period_subject_count, 0) as same_lead_period_subject_count,
    coalesce(lb_subject_count, 0) as lb_subject_count,
    coalesce(same_lead_period_lb_subject_count, 0) as same_lead_period_lb_subject_count,
    coalesce(order_count, 0) as order_count,
    coalesce(income_amount, 0) as income_amount,
    coalesce(in_pay_period_refund_amount, 0) as in_pay_period_refund_amount,
    coalesce(non_pay_period_refund_amount, 0) as non_pay_period_refund_amount,
    coalesce(jp_cross_department_refund_amount, 0) as jp_cross_department_refund_amount,
    coalesce(same_lead_period_order_count, 0) as same_lead_period_order_count,
    coalesce(same_lead_period_conversion_lead_count, 0) as same_lead_period_conversion_lead_count,
    coalesce(same_lead_period_income_amount, 0) as same_lead_period_income_amount,
    coalesce(same_lead_period_refund_amount, 0) as same_lead_period_refund_amount,
 -- 这三个特殊字段
coalesce(date_diff('hour', cast(t1.section_assign_time as timestamp), cast(t1.first_call_time as timestamp)),0) as first_call_time_diff_hour,
    coalesce(case when cast(valid_lead_count as varchar) = '1' then friend_lead_count else 0 end, 0) as is_friend_lead,
    coalesce(case when t.jieduan in ('深沟','已双沟') then 1 else 0 end, 0) as is_shengou,
 	coalesce(case when intention_level in ('A', 'B') and t.jieduan in ('深沟','已双沟') then 1 else 0 end, 0) as AB_intention_level,
    coalesce(case when intention_level in ('A', 'B') and conversion_lead_count = '1' then 1 else 0 end, 0) as AB_zhuanhua
from bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df t1
    left join biz_qici_calendar lead_cal
      on lead_cal.business_domain = 'market_consultant'
     and lead_cal.date_role = 'lead_period'
     and cast(date_parse(replace(concat(t1.group_period_year, t1.group_period_term), '期', ''), '%Y%m%d') as date)
         between lead_cal.period_start_date and lead_cal.period_end_date
     and lead_cal.enabled = 1
left join
    (
        select
            user_number,
            sale_flow_stage_sequence,
            sale_flow_stage_name_1,
            jieduan_1 as jieduan
        from (
            select
                user_number,
                sale_flow_stage_sequence,
                CASE
                    WHEN sale_flow_stage_sequence = '50' THEN '新线索'
                    WHEN sale_flow_stage_sequence = '60' THEN '待跟进'
                    WHEN sale_flow_stage_sequence = '70' THEN '已接收'
                    WHEN sale_flow_stage_sequence = '100' THEN '未接通'
                    WHEN sale_flow_stage_sequence = '150' THEN '已建联'
                    WHEN sale_flow_stage_sequence = '200' THEN '首call'
                    WHEN sale_flow_stage_sequence = '250' THEN '商机'
                    WHEN sale_flow_stage_sequence = '300' THEN '学情沟通'
                    WHEN sale_flow_stage_sequence = '350' THEN '浅沟'
                    WHEN sale_flow_stage_sequence = '400' THEN '已约课'
                    WHEN sale_flow_stage_sequence = '450' THEN '深沟'
                    WHEN sale_flow_stage_sequence = '470' THEN '已双沟'
                    WHEN sale_flow_stage_sequence = '500' THEN '再次建联'
                    WHEN sale_flow_stage_sequence = '550' THEN '约课'
                    WHEN sale_flow_stage_sequence = '600' THEN '诺访'
                    WHEN sale_flow_stage_sequence = '650' THEN '已排课'
                    WHEN sale_flow_stage_sequence = '660' THEN '已摸底测'
                    WHEN sale_flow_stage_sequence = '680' THEN '促到课'
                    WHEN sale_flow_stage_sequence = '700' THEN '已到课'
                    WHEN sale_flow_stage_sequence = '710' THEN '中教完课'
                    WHEN sale_flow_stage_sequence = '720' THEN '外教完课'
                    WHEN sale_flow_stage_sequence = '750' THEN '已完课'
                    WHEN sale_flow_stage_sequence = '800' THEN '到访'
                    WHEN sale_flow_stage_sequence = '820' THEN '看回放'
                    WHEN sale_flow_stage_sequence = '850' THEN '铺课'
                    WHEN sale_flow_stage_sequence = '900' THEN '已推课'
                    WHEN sale_flow_stage_sequence = '920' THEN '定金'
                    WHEN sale_flow_stage_sequence = '925' THEN '已挖需'
                    WHEN sale_flow_stage_sequence = '930' THEN '已规划'
                    WHEN sale_flow_stage_sequence = '935' THEN '已报价'
                    WHEN sale_flow_stage_sequence = '950' THEN '关单'
                    WHEN sale_flow_stage_sequence = '955' THEN '追单'
                    WHEN sale_flow_stage_sequence = '960' THEN '流转成功'
                    WHEN sale_flow_stage_sequence = '1000' THEN '未成交'
                    WHEN sale_flow_stage_sequence = '1050' THEN '成单'
                    ELSE '未知状态'
                END AS sale_flow_stage_name_1,
                CASE
                    WHEN sale_flow_stage_sequence = '450' THEN '深沟'
                    WHEN sale_flow_stage_sequence = '470' THEN '已双沟'
                    ELSE '其他'
                END AS jieduan_1,
                ROW_NUMBER() OVER (PARTITION BY user_number ORDER BY private_sea_update_time DESC) as rn
            from service_dw.dwd_crm_assign_private_detail_hf
            where dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
                and hour = format_datetime(now() - interval '2' hour, 'HH')
                and assign_employee_first_level_department_name = 'H业务线'
                and assign_employee_second_level_department_name = '市场部'
                and assign_employee_third_level_department_name = '市场顾问部'
        )
        where rn = 1
    ) t on t1.user_id = t.user_number
where dt=format_datetime(NOW()-interval '2' hour,'YYYYMMdd') and hour=format_datetime(NOW()-interval '3' hour,'HH' )
 	and section_assign_employee_first_level_department_name = 'H业务线'
 and section_assign_employee_second_level_department_name = '市场部'
and section_assign_employee_third_level_department_name = '市场顾问部'
    and period_mapping_first_level_department_name = 'H业务线'
    and period_mapping_second_level_department_name in ('精品班学部','青橙项目部','一对一学部','本地化大班学部','市场部','菁英班学部')
)
--------------------------5min比例、外呼次数、外呼接通次数
,call_c as (
    select
        sub.user_number as user_number,
        sub.lead_id,
        sub.section_assign_employee_email_prefix,
        max(case when sub.call_duration > 300 then 1 else 0 end) as is_long_call,
        sum(sub.call_duration) as call_duration_1,
        sum(case when sub.call_status in ('1','0') then 1 else 0 end) as zong_call_ci_1,
        sum(case when sub.call_status = '1' then 1 else 0 end) as call_status_1
    from (
        select distinct
            wf.user_number,
            wf.lead_id,
            wf.section_assign_employee_email_prefix,
            wf.call_duration,
            wf.call_status,
            wf.call_time,
            wf.call_type_name,
            wf.data_source,
            wf.msg_type_name
        from service_dw.app_h_crm_lead_employee_workload_detail_hf wf
        where wf.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
            and wf.hour = format_datetime(now() - interval '2' hour, 'HH')
    ) sub
    group by 1,2,3
)
---------------------------------首节到课
,daoke as (
    select
        dk.period_name,
        dk.employee_email_prefix,
        dk.lead_id,
        dk.user_id,
        dk.channel_map,
	    dk.begin_time,
        dk.live_learn_duration,
	    dk.is_valid_live_learn,
	    ke.ke_1
    from (
        select distinct
            t1.period_name,
            t1.employee_email_prefix,
            t1.lead_id,
            t1.user_id,
            t1.channel_map,
            t1.grade_1,
            t2.live_learn_duration,
		    t2.is_valid_live_learn,
		    t2.begin_time,
		    t2.dow
        from (
            select
                lead_id,
                user_id,
                employee_email_prefix,
                period_name,
                channel_map,
                grade_1
            from data
            group by lead_id, user_id, employee_email_prefix, period_name, channel_map, grade_1
        ) t1
        left join (
            select
                user_number,
                begin_time,
                substr(begin_time, 12, 5) as ke_time,
coalesce(
    class_cal.qici,
    case
	when cast(begin_time as date) >= date '2026-02-25' and cast(begin_time as date) <= date '2026-03-02' then '20260227期'
	when cast(begin_time as date) >= date '2026-02-17' and cast(begin_time as date) <= date '2026-02-24' then '20260220期'
	when cast(begin_time as date) >= date '2026-02-09' and cast(begin_time as date) <= date '2026-02-16' then '20260213期'
	when cast(begin_time as date) >= date '2026-02-03' and cast(begin_time as date) <= date '2026-02-08' then '20260206期'
    -- 对于其他日期，使用原有的周逻辑
    else
        case
            when day_of_week(cast(begin_time as date)) = 2
                then date_format(date_trunc('week', cast(begin_time as date)) - interval '3' day, '%Y%m%d') || '期'
            else date_format(date_trunc('week', cast(begin_time as date)) + interval '4' day, '%Y%m%d') || '期'
        end
    end
) as qici,
                mod(date_diff('day', cast('2021-02-01' as date), cast(begin_time as date)), 7) as dow,
                is_need_attend,
                live_learn_duration,
                is_valid_live_learn
            from service_dw.dws_service_user_learn_detail_hf
            left join biz_qici_calendar class_cal
              on class_cal.business_domain = 'market_consultant'
             and class_cal.date_role = 'class_period'
             and cast(begin_time as date) between class_cal.period_start_date and class_cal.period_end_date
             and class_cal.enabled = 1
            where dt = date_format(now() - interval '2' hour, '%Y%m%d')
                and hour = date_format(now() - interval '2' hour, '%H')
                and course_first_level_department_name = 'H业务线'
                and course_second_level_department_name in ('精品班学部','市场部','青橙项目部')
                and is_need_attend = 1
        ) t2 on t1.period_name = t2.qici and t1.user_id = t2.user_number) dk
	left join temp_table.dingxi01_daoke_1_6_t ke on dk.period_name = ke.qici and dk.channel_map = ke.channel and dk.grade_1 = ke.grade and dk.begin_time = ke.begin_time)
-------------------业绩订单明细--科目数
,dd as (select
d.qici_new as qici,d.user_id,d.employee_email_name,count(distinct d.subject ) as subject
 from
	(select user_id, employee_email_name,
        coalesce(
            trade_cal.qici,
            case
			when substr(trade_time, 1, 10) >= '2026-02-25' and substr(trade_time, 1, 10) <= '2026-03-02' then '20260227期'
			when substr(trade_time, 1, 10) >= '2026-02-17' and substr(trade_time, 1, 10) <= '2026-02-24' then '20260220期'
			when substr(trade_time, 1, 10) >= '2026-02-09' and substr(trade_time, 1, 10) <= '2026-02-16' then '20260213期'
			when substr(trade_time, 1, 10) >= '2026-02-03' and substr(trade_time, 1, 10) <= '2026-02-08' then '20260206期'
			when substr(trade_time, 1, 10) >= '2026-01-27' and substr(trade_time, 1, 10) <= '2026-02-02' then '20260130期'
			when substr(trade_time, 1, 10) >= '2026-01-20' and substr(trade_time, 1, 10) <= '2026-01-26' then '20260123期'
		else case when day_of_week(cast(trade_time as timestamp)) = 1
           then concat(date_format(date_trunc('week', cast(trade_time as timestamp)) - interval '3' day,'%Y%m%d'),'期')
           else concat(date_format(date_trunc('week', cast(trade_time as timestamp)) + interval '4' day, '%Y%m%d'),'期')
        end
        end
     ) as qici_new,
	    case when course_subject like '%英语%' or course_subject like '%英文%' then '英语'
	           when course_subject like '%语文%'  then '语文'  when course_subject like '%数学%'  then '数学'
	           when course_subject like '%物理%'  then '物理' when course_subject like '%化学%'  then '化学'
	           when course_subject like '%历史%'  then '历史' when course_subject like '%政治%'  then '政治'
	           when course_subject like '%生物%'  then '生物' when course_subject like '%地理%'  then '地理'
	           when course_subject like '%日语%'  then '日语' else course_subject end
	     as subject
    from finance_dw.app_finance_performance_extend_details_hf
    left join biz_qici_calendar trade_cal
      on trade_cal.business_domain = 'market_consultant'
     and trade_cal.date_role = 'trade_period'
     and cast(substr(trade_time, 1, 10) as date) between trade_cal.period_start_date and trade_cal.period_end_date
     and trade_cal.enabled = 1
    where dt = FORMAT_DATETIME(NOW() - INTERVAL '2' HOUR,'YYYYMMdd')
        and hour = FORMAT_DATETIME(NOW() - INTERVAL '2' HOUR,'HH')
        and employee_first_level_department_name = 'H业务线'
	    and employee_second_level_department_name = '市场部'
        and employee_third_level_department_name = '市场顾问部'
        and real_price <> 0) d
    where d.qici_new > '20260403期'
	group by d.qici_new,d.user_id,d.employee_email_name	)
-----------------------------整合
,base as
(
    select
  data.*,
case when data.first_call_time_diff_hour >= 0 and data.first_call_time_diff_hour <= 24 and data.valid_lead_count > 0 then 1 else 0 end as first_call_in_24h,
    case when data.first_call_time_diff_hour >= 0 and data.first_call_time_diff_hour <= 48 and data.valid_lead_count > 0 then 1 else 0 end as first_call_in_48h,
	coalesce(call_c.is_long_call, 0) as is_long_call,
    case when denglu_app.user_number is not null then denglu_app.is_app_denglu else 0 end as is_app_denglu,
	app_ph.last_app_channel,
	case when dd.subject = '1' then '1科'
	when dd.subject = '2' then '2科'
	when dd.subject = '3' then '3科'
	when dd.subject = '4' then '4科'
	when dd.subject = '5' then '5科'
        when dd.subject = '6' then '6科'
        when dd.subject = '7' then '7科'
	else '0科' end as sub,
        case
            when data.channel_map = '曹忆'
                then case when exists (
                    select 1
                    from daoke
                    where daoke.user_id = data.user_id and daoke.employee_email_prefix = data.employee_email_prefix and daoke.period_name = data.period_name and data.channel_map = daoke.channel_map and daoke.ke_1 = '3' and daoke.live_learn_duration > 0) then 1 else 0 end
            else case when exists (
                    select 1
                    from daoke
                    where daoke.user_id = data.user_id and daoke.employee_email_prefix = data.employee_email_prefix and daoke.period_name = data.period_name and data.channel_map = daoke.channel_map and daoke.ke_1 = '1' and daoke.live_learn_duration > 0) then 1 else 0 end
        end as daoke1,
	case
            when data.channel_map = '曹忆'
                then case when exists (
                    select 1
                    from daoke
                    where daoke.user_id = data.user_id and daoke.employee_email_prefix = data.employee_email_prefix and daoke.period_name = data.period_name and data.channel_map = daoke.channel_map and daoke.ke_1 = '3' and daoke.is_valid_live_learn = '1') then 1 else 0 end
            else case when exists (
                    select 1
                    from daoke
                    where daoke.user_id = data.user_id and daoke.employee_email_prefix = data.employee_email_prefix and daoke.period_name = data.period_name and data.channel_map = daoke.channel_map and daoke.ke_1 = '1' and daoke.is_valid_live_learn = '1') then 1 else 0 end
        end as daoke_v1
    from data
	left join call_c on call_c.user_number = data.user_id and call_c.section_assign_employee_email_prefix = data.employee_email_prefix
	left join denglu_app on denglu_app.user_number = data.user_id
	left join app_ph on app_ph.user_number = data.user_id
	left join dd on dd.qici = data.period_name and dd.user_id = data.user_id
	where period_name > '20260403期'
)

---------------------------转化
,zhuanhua as
(select
    period_name,
    channel_map,
 	grade_1,
	depart_1,
    depart,
    jingli,-- 大组长
    zhuguan, -- 小组长
    employee_email_name,
    city_level_name,
    last_app_channel,
    sub,
    sum(lead_count) IP_lead_count,
    sum(valid_lead_count) can_renew_ds_count_a,
    sum(first_call_in_24h) first_call_24h,
    sum(first_call_in_48h) first_call_48h,
    sum(is_friend_lead) friend_lead,
    sum(is_shengou) shengou_lead,
 	sum(AB_intention_level) AB_lead,
	sum(AB_zhuanhua) AB_zhuan,
    sum(is_long_call) long_call_5,
    sum(is_app_denglu) app_denglu,
    sum(daoke1) daoke_1,
    sum(daoke_v1) daoke_v1,
    sum(conversion_lead_count) pay_users,
    sum(same_lead_period_conversion_lead_count)  pay_users_on_period,
    sum(conversion_lead_count-same_lead_period_conversion_lead_count) pay_users_not_on_period,
    sum(subject_count) pay_user_subs,
    sum(same_lead_period_subject_count) pay_user_subs_on_period,
    sum(subject_count-same_lead_period_subject_count) pay_user_subs_not_on_period,
    sum(lb_subject_count) pay_user_subs_joint,
    sum(same_lead_period_lb_subject_count) pay_user_subs_joint_onp,
    sum(lb_subject_count-same_lead_period_lb_subject_count) pay_user_subs_joint_nonp,
    sum(income_amount/100) trade_income,
    sum(in_pay_period_refund_amount/100+non_pay_period_refund_amount/100) trade_refund,
    sum(income_amount/100-in_pay_period_refund_amount/100-non_pay_period_refund_amount/100) trade_profit,
    sum(same_lead_period_income_amount/100) xb_trade_income,
    sum(same_lead_period_income_amount/100-same_lead_period_refund_amount/100) xb_trade_profit,
    sum(income_amount/100-same_lead_period_income_amount/100) kk_trade_income,
    sum(non_pay_period_refund_amount/100) pre_refund
from base
group by
    period_name,
    channel_map,
 	 grade_1,
	 depart_1,
    depart,
    jingli,-- 大组长
    zhuguan, -- 小组长
   employee_email_name,
   city_level_name,
  last_app_channel,
 sub
)
-------------结果指标
select  zz.*,
case when zz.can_renew_ds_count_a >=5  then zz.can_renew_ds_count_a else 0 end as s_lead,
case when zz.can_renew_ds_count_a >=5 and zz.trade_income > 0 then 1 else 0 end as podan,---线索量>10且有净营收且带班
case when zz.can_renew_ds_count_a >=5  then zz.employee_email_name else '未知' end as name1,
zx.xiaozu ,
coalesce(ct.cost,0) cb_cb,  --单例子成本
coalesce(ct.goal,0) gl_gl,--单例子标
count(*) over (partition by zz.period_name, zz.channel_map, zz.city_level_name) city_level_row
from zhuanhua zz
----渠道
left join (select * from temp_table.dingxi01_channel_group) channel_grp on channel_grp.channel=zz.channel_map
left join (select * from temp_table.dingxi01_cost) ct on ct.channel =zz.channel_map and ct.grade=zz.grade_1 and zz.period_name=ct.qici
left join temp_table.dingxi01_jiagou_db jg on jg.qici = zz.period_name and jg.department = zz.depart and zz.zhuguan = jg.xiaozu and zz.employee_email_name = jg.employee_email_name
left join temp_table.dingxi01_jiagou_zx zx on zx.employee_email_name = zz.employee_email_name
