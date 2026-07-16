-- 2026-07-16 update: map summer business dates 2026-07-14..2026-08-12 to actual operation qici ranges.
-- Dataset: 2054 outbound process
with d_ap as (
    select distinct
        user_latest.user_number,
        user_latest.last_event_time,
        user_latest.product_name,
        user_latest.appliction_name,
        case
            when user_latest.event_timestamp >= now() - interval '7' day
             and user_latest.appliction_name in ('PC客户端', 'APP', 'PC')
            then 1 else 0
        end as is_app_denglu_d,
        user_latest.event_timestamp,
        now() - interval '7' day as seven_days_ago,
        date_diff('day', cast(user_latest.event_timestamp as date), current_date) as days_diff_simple
    from (
        select
            ul.user_number,
            ul.last_event_time,
            ul.product_name,
            ul.appliction_name,
            try(date_parse(ul.last_event_time, '%Y-%m-%d %H:%i:%s:%f')) as event_timestamp
        from (
            select
                *,
                row_number() over (
                    partition by user_number
                    order by try(date_parse(last_event_time, '%Y-%m-%d %H:%i:%s:%f')) desc
                ) as rn
            from dw.dim_cstm_active_user_c_appliction_mb_df
            where dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
              and product_name in ('高途', '规划精品')
        ) ul
        where rn = 1
    ) user_latest
),
h_ap as (
    select distinct
        user_number,
        case when application_name in ('PC客户端', 'APP', 'PC') then 1 else 0 end as is_app_denglu_h
    from dw.dws_user_active_user_c_appliction_hf
    where dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
      and hour = format_datetime(now() - interval '3' hour, 'HH')
      and product_name in ('高途', '规划精品')
),
denglu_app as (
    select
        d_ap.user_number,
        case
            when coalesce(h_ap.is_app_denglu_h, 0) = 1
              or coalesce(d_ap.is_app_denglu_d, 0) = 1
            then 1 else 0
        end as is_app_denglu
    from d_ap
    left join h_ap on d_ap.user_number = h_ap.user_number
),
jg_market as (
    select
        qici,
        employee_email_prefix,
        department,
        jingli,
        xiaozu
    from (
        select
            jg.*,
            row_number() over (
                partition by jg.qici, jg.employee_email_prefix
                order by jg.department, jg.xiaozu, jg.jingli
            ) as rn
        from temp_table.dingxi01_jiagou_db jg
        where jg.qici > '20260507期'
          and jg.dept_1 = '市场顾问部'
          and cast(jg.zaizhi as varchar) = '1'
    ) t
    where rn = 1
),
--------------------------------------基础数据
data as (
    select distinct
        f.*,
        case
            when cast(date_parse(replace(concat(f.group_period_year, f.group_period_term), '期', ''), '%Y%m%d') as date) between date '2026-07-14' and date '2026-07-19' then '20260716期'
            when cast(date_parse(replace(concat(f.group_period_year, f.group_period_term), '期', ''), '%Y%m%d') as date) between date '2026-07-20' and date '2026-07-25' then '20260722期'
            when cast(date_parse(replace(concat(f.group_period_year, f.group_period_term), '期', ''), '%Y%m%d') as date) between date '2026-07-26' and date '2026-07-31' then '20260728期'
            when cast(date_parse(replace(concat(f.group_period_year, f.group_period_term), '期', ''), '%Y%m%d') as date) between date '2026-08-01' and date '2026-08-06' then '20260803期'
            when cast(date_parse(replace(concat(f.group_period_year, f.group_period_term), '期', ''), '%Y%m%d') as date) between date '2026-08-07' and date '2026-08-12' then '20260809期'
            else concat(
            date_format(
                date_trunc(
                    'week',
                    date_parse(replace(concat(f.group_period_year, f.group_period_term), '期', ''), '%Y%m%d') - interval '1' day
                ) + interval '4' day,
                '%Y%m%d'
            ),
            '期'
        )
        end as qici,
case when flow_pool_name in ('高途学习规划','智辉老师讲规划') then '市场私域视频号'
when rule_name like '%语数英%' and third_department_name = '新媒体内容运营部' then '语数英'
when flow_pool_name like '%星义大大%' then '赵星义'
when third_department_name='图书营销部' and (sku_id_name like '%孟亚飞99%' or sku_id_name like '%亚飞%') then '孟亚飞99-2组'
when third_department_name = '投放部' and ad_account_name like '%周帅%' then '信息流-周帅'
when source_manager_name in ('韩正卿') then '抖音私信'
when third_department_name = '私域运营部' and source_manager_name in ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研','岳一帆02','田起帆','王绍阳') then '进校私域合作'
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
when third_department_name in ('直播部','新媒体内容运营部','市场一组')  and (flow_pool_name ='初阶化学规划' or flow_pool_name like '%启迪-初阶老师%')  then '曹忆'
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
when channel_name_1 = '信息流' and channel_name_2='B站' and (page_id_name like '%亚飞%' or source_put_plan_name like '%亚飞%'  or rule_name like '%亚飞%' or page_id_name like '%初中-0元%') then 'B站信息流-亚飞'
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
when (flow_pool_name like '%孟帝%' or flow_pool_name like '%孟老师%' or flow_pool_name like '%中考数学冲刺%' or flow_pool_name like '%8升9数学%' or flow_pool_name like '%孟亚飞讲数学%' or flow_pool_name like '%中考冲刺%' or flow_pool_name like '%中考满分冲刺%' or flow_pool_name like '%押题王孟亚飞%' or flow_pool_name like '%中考数学大通关%' or flow_pool_name like '%中考数学规划%' or flow_pool_name like '%亚飞数学%')  and period_name not like '%多学科拓展%' and channel_name_2 not like '%KOL%' and third_department_name='直播部' and rule_name like '%99%'  then '孟亚飞99-1组'
when (flow_pool_name like '%孟帝%' or flow_pool_name like '%孟老师%' or flow_pool_name like '%中考数学冲刺%' or flow_pool_name like '%8升9数学%' or flow_pool_name like '%孟亚飞讲数学%' or flow_pool_name like '%中考冲刺%' or flow_pool_name like '%中考满分冲刺%' or flow_pool_name like '%押题王孟亚飞%' or flow_pool_name like '%中考数学大通关%' or flow_pool_name like '%中考数学规划%' or flow_pool_name like '%亚飞数学%')  and period_name not like '%多学科拓展%' and channel_name_2 not like '%KOL%' and third_department_name='直播部' and channel_name_2 = '百度'  then '孟亚飞百度数字人'
when (flow_pool_name like '%孟帝%' or flow_pool_name like '%孟老师%' or flow_pool_name like '%中考数学冲刺%' or flow_pool_name like '%8升9数学%' or flow_pool_name like '%孟亚飞讲数学%' or flow_pool_name like '%中考冲刺%' or flow_pool_name like '%中考满分冲刺%' or flow_pool_name like '%押题王孟亚飞%' or flow_pool_name like '%中考数学大通关%' or flow_pool_name like '%中考数学规划%' or flow_pool_name like '%亚飞数学%')  and period_name not like '%多学科拓展%' and channel_name_2 not like '%KOL%' and third_department_name='直播部'  then '孟亚飞9元'
when put_plan_name like '%刘家晋讲图文%' or put_plan_name like '%孟帝数学%' and third_department_name='直播部' and rule_name like '%99%'  then '孟亚飞99-1组'
when put_plan_name like '%刘家晋讲图文%' or put_plan_name like '%孟帝数学%' and third_department_name='直播部' then '孟亚飞9元'
when (flow_pool_name like '%肖晗%' or sku_id_name like '%肖晗%') and third_department_name='直播部'  then '肖晗'
when flow_pool_name like '%峥峥%' and period_name not like '%多学科拓展%' and third_department_name='直播部'  then '何峥峥'
when flow_pool_name like '%汐子%' and period_name not like '%多学科拓展%' and sku_id_name not like '%亚飞%' and third_department_name='直播部'  then '王汐子'
when flow_pool_name like '%汐子%' and period_name not like '%多学科拓展%' and sku_id_name  like '%亚飞%' and third_department_name='直播部' and rule_name like '%99%'  then '孟亚飞99-1组'
when flow_pool_name like '%汐子%' and period_name not like '%多学科拓展%' and sku_id_name  like '%亚飞%' and third_department_name='直播部' then '孟亚飞9元'
when (flow_pool_name like '%曹忆%' or flow_pool_name like '%dudu%' or flow_pool_name like '%中考决胜天团%' or flow_pool_name like '%具象思维%' or flow_pool_name like '%在逃发面馒头%' or flow_pool_name like '%库洛米%' and lead_purchase_intention_level1_category_name <> '规划系统') and period_name not like '%多学科拓展%' and third_department_name in ('直播部','新媒体内容运营部') then '曹忆'
when flow_pool_name = '正价课判单补录' then '正价课判单补录'
when channel_name_1 = '转介绍' then '转介绍'
when first_department_name ='市场部' and channel_name_1 <> '站内获客' and channel_name_2 <> 'APP' then '集团私域'
when put_plan_name like '%未加好友%' then '市场私域未加好友'
when put_plan_name like '%私域-信息流%' then '市场私域待支付'
when third_department_name = '私域运营部' and rule_name not like '%训练营%' and virtual_fifth_department_name not in ('罗江博团队') and rule_name not like '%复用%' and rule_name not like '%未加好友%' and channel_name_2 <> '内部换量' then '市场私域低价单'
when third_department_name = '私域运营部' and rule_name not like '%训练营%'  and rule_name not like '%复用%' and rule_name not like '%未加好友%' and channel_name_2 <> '内部换量' and flow_original_order_activity_price = '0.0' then '市场私域低价单'
when third_department_name = '私域运营部' and channel_name_1 = '信息流获客' then '市场私域小红书'
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
when flow_pool_name = '中考加油' and sku_id_name like '%孟帝%' then 'KOC-孟亚飞数学'
when flow_pool_name = '中考加油' and sku_id_name  like '%帅师%' then 'KOC-周帅数学'
when flow_pool_name = '中考加油' and sku_id_name  like '%肖晗%' then 'KOC-肖晗'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') and (sku_id_name like '%孟帝%' or sku_id_name like '%dudu%' or sku_id_name like '%市场初二%' or rule_name like '%亚飞%' or sku_id_name like '%初二高阳%' or sku_id_name like '%高阳初二%' or sku_id_name like '%精品初二%' or sku_id_name like '%菁英初三%' or (virtual_second_department_name = '菁英班学部' and lead_purchase_intention_level2_category_name='初级' and lead_create_time>= '2026-04-15 00:00:00')) then 'KOC-孟亚飞数学'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') and (sku_id_name like '%帅师%' or rule_name like '%周帅%') then 'KOC-周帅数学'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') and (sku_id_name like '%肖晗%' or rule_name like '%肖晗%') then 'KOC-肖晗'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') and period_name not like '%多学科拓展%' and (flow_original_order_activity_price like '%1100%' or flow_original_order_activity_price like '%500%' or flow_orders_income_amount like '%500%') and (sku_id_name like '%朱汉祺%' or sku_id_name like '%朱博士%' or rule_name like '%朱汉祺5元%' or sku_id_name like '%koc5元-朱博士%' or rule_name like '%朱汉祺%') then 'KOC-5元朱汉祺'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') and (sku_id_name like '%朱汉祺%' or sku_id_name like '%29元%' or sku_id_name like '%朱博士%' or rule_name like '%朱汉祺%' or rule_name like '%朱博士%' ) and (flow_original_order_activity_price not like '%1100%' or rule_name like '%29%') and sku_id_name not like '%周帅%' then 'KOC-5元朱汉祺'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') and period_name not like '%多学科拓展%' and sku_id_name not like '%朱汉祺%' and sku_id_name not like '%朱博士%' and sku_id_name not like '%周帅%' and sku_id_name not like '%29元%' then 'KOC-5元纯课'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪') and sku_id_name like '%周帅%' then 'KOC-周帅'
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
when third_department_name = '直播部' and sku_id_name like '%周帅%' and channel_name_2 in ('百度','B站')  then '周帅-百度数字人'
when third_department_name = '直播部' and sku_id_name like '%孟亚飞%' and sku_id_name like '%199%' then '孟亚飞199'
when third_department_name = '直播部' and sku_id_name like '%孟亚飞%' and rule_name like '%99%' then '孟亚飞99-1组'
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
when flow_pool_name like '%自然流%' and sku_id_name like '%亚飞%' and rule_name like '%99%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '孟亚飞99-1组'
when flow_pool_name like '%自然流%' and sku_id_name like '%亚飞%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组')  then '孟亚飞9元'
when flow_pool_name like '%自然流%' and sku_id_name like '%曹忆%' then '曹忆'
when flow_pool_name like '%自然流%' and rule_name like '%朱博士%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '朱博士29'
when flow_pool_name like '%自然流%' and source_manager_name like '%邵万昕%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '朱博士29'
when flow_pool_name like '%自然流%' and rule_name like '%亚飞%' and rule_name like '%99%' then '孟亚飞99-1组'
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
when channel_name_1= '信息流' and (put_plan_name like '%抖音私信%' or put_plan_name like '%初三0元%' or put_plan_name like '%高中0元%') then '信息流-抖音私信'
when rule_name like '%途途私域%' or (rule_name like '%私域%' and first_department_name = 'TT') then '途途私域'
else '其他未知流量' end as channel_map_1,
        case
            when f.rule_name like '%高一%' then '高一'
            when f.rule_name like '%高二%' then '高二'
  				when f.rule_name like '%高三%' then '高三'
	 			when f.rule_name like '%初一%' then '初一'
            when f.rule_name like '%初二%' then '初二'
            when f.rule_name like '%初三%' then '初三'
            else f.lead_purchase_intention_level2_category_name
        end as grade_1,
        date_diff('hour', cast(f.section_assign_time as timestamp), cast(f.first_call_time as timestamp)) as first_call_time_diff_hour,
        date_diff('minute', cast(f.section_assign_time as timestamp), cast(f.first_call_time as timestamp)) as first_call_time_diff_minute,
        jt.first_call_connected_time_diff_hour as first_call_connected_time_diff_hour_1,
        case when f.valid_lead_count = 1 then f.friend_lead_count else 0 end as is_friend_lead,
        case when t.jieduan in ('深沟', '已双沟') then 1 else 0 end as is_shengou,
        case
            when cast(t.sale_flow_stage_sequence as varchar) in ('470', '700', '850', '950', '955', '1050')
            then 1 else 0
        end as is_shuanggou,
        case
            when f.deep_communicate_method is not null
             and f.deep_communicate_method != ''
             and f.valid_lead_count = 1
            then 1 else 0
        end as yi_shuanggou,
        case
            when yc.abnormal_traffic is not null
             and yc.abnormal_traffic != ''
             and t.sale_flow_stage_name_1 in ('新线索', '已建联', '未成交')
            then 1 else 0
        end as is_yichang,
        case
            when sbb.send_double_table = '是'
             and f.valid_lead_count = 1
            then 1 else 0
        end as yi_huishou
    from bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df f
    left join (
        select
            user_number,
            sale_flow_stage_sequence,
            sale_flow_stage_name_1,
            jieduan_1 as jieduan
        from (
            select
                user_number,
                sale_flow_stage_sequence,
                case
                    when sale_flow_stage_sequence = '50' then '新线索'
                    when sale_flow_stage_sequence = '60' then '待跟进'
                    when sale_flow_stage_sequence = '70' then '已接收'
                    when sale_flow_stage_sequence = '100' then '未接通'
                    when sale_flow_stage_sequence = '150' then '已建联'
                    when sale_flow_stage_sequence = '200' then '首call'
                    when sale_flow_stage_sequence = '250' then '商机'
                    when sale_flow_stage_sequence = '300' then '学情沟通'
                    when sale_flow_stage_sequence = '350' then '浅沟'
                    when sale_flow_stage_sequence = '400' then '已约课'
                    when sale_flow_stage_sequence = '450' then '深沟'
                    when sale_flow_stage_sequence = '470' then '已双沟'
                    when sale_flow_stage_sequence = '500' then '再次建联'
                    when sale_flow_stage_sequence = '550' then '约课'
                    when sale_flow_stage_sequence = '600' then '诺访'
                    when sale_flow_stage_sequence = '650' then '已排课'
                    when sale_flow_stage_sequence = '660' then '已摸底测'
                    when sale_flow_stage_sequence = '680' then '促到课'
                    when sale_flow_stage_sequence = '700' then '已到课'
                    when sale_flow_stage_sequence = '710' then '中教完课'
                    when sale_flow_stage_sequence = '720' then '外教完课'
                    when sale_flow_stage_sequence = '750' then '已完课'
                    when sale_flow_stage_sequence = '800' then '到访'
                    when sale_flow_stage_sequence = '820' then '看回放'
                    when sale_flow_stage_sequence = '850' then '铺课'
                    when sale_flow_stage_sequence = '900' then '已推课'
                    when sale_flow_stage_sequence = '920' then '定金'
                    when sale_flow_stage_sequence = '925' then '已挖需'
                    when sale_flow_stage_sequence = '930' then '已规划'
                    when sale_flow_stage_sequence = '935' then '已报价'
                    when sale_flow_stage_sequence = '950' then '关单'
                    when sale_flow_stage_sequence = '955' then '追单'
                    when sale_flow_stage_sequence = '960' then '流转成功'
                    when sale_flow_stage_sequence = '1000' then '未成交'
                    when sale_flow_stage_sequence = '1050' then '成单'
                    else '未知状态'
                end as sale_flow_stage_name_1,
                case
                    when sale_flow_stage_sequence = '450' then '深沟'
                    when sale_flow_stage_sequence = '470' then '已双沟'
                    else '其他'
                end as jieduan_1,
                row_number() over (
                    partition by user_number
                    order by private_sea_update_time desc
                ) as rn
            from service_dw.dwd_crm_assign_private_detail_hf
            where dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
              and hour = format_datetime(now() - interval '3' hour, 'HH')
              and assign_employee_first_level_department_name = 'H业务线'
              and assign_employee_second_level_department_name = '市场部'
              and assign_employee_third_level_department_name = '市场顾问部'
        )
        where rn = 1
    ) t on f.user_id = t.user_number
    left join (
        select
            lead_id,
            section_assign_time,
            section_assign_first_call_time,
            section_assign_first_call_connected_time,
            date_diff(
                'hour',
                cast(section_assign_time as timestamp),
                cast(section_assign_first_call_connected_time as timestamp)
            ) as first_call_connected_time_diff_hour
        from service_dw.dm_crm_lead_stats_detail_hf cd
        where dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
          and hour = format_datetime(now() - interval '3' hour, 'HH')
          and mapping_first_level_department_name = 'H业务线'
          and mapping_second_level_department_name in ('精品班学部', '菁英班学部', '市场部', '本地化大班学部')
    ) jt on f.lead_id = jt.lead_id
    ------------------------异常率
    left join (
        select
            abnormal_traffic,
            user_number
        from service_dw.app_user_attribute_label_gaia_wide_df
        where dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
          and type = 'key'
    ) yc on yc.user_number = f.user_id
    -------双表发送
    left join (
        select *
        from (
            select
                send_double_table,
                user_id,
                flow_order_period_name,
                lead_update_time,
                trace_update_time,
                assign_time,
                case
                    when cast(assign_time as date) between date '2026-07-14' and date '2026-07-19' then '20260716期'
                    when cast(assign_time as date) between date '2026-07-20' and date '2026-07-25' then '20260722期'
                    when cast(assign_time as date) between date '2026-07-26' and date '2026-07-31' then '20260728期'
                    when cast(assign_time as date) between date '2026-08-01' and date '2026-08-06' then '20260803期'
                    when cast(assign_time as date) between date '2026-08-07' and date '2026-08-12' then '20260809期'
                    else concat(
                    date_format(
                        date_trunc('week', cast(assign_time as timestamp) - interval '1' day) + interval '4' day,
                        '%Y%m%d'
                    ),
                    '期'
                )
                end as qici,
                assign_employee_email_name,
                virtual_department_name_2,
                virtual_department_name_3,
                employee_virtual_department_name,
                row_number() over (
                    partition by user_id, assign_employee_email_name
                    order by trace_update_time desc
                ) as rn
            from service_dw.app_h_crm_lead_task_process_info_detail_hf
            where dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
              and hour = format_datetime(now() - interval '3' hour, 'HH')
              and virtual_department_name_2 = 'H业务线'
              and virtual_department_name_3 = '市场部'
        )
        where rn = 1
    ) sbb on sbb.assign_employee_email_name = f.employee_email_name
          and sbb.user_id = f.user_id
    where f.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
      and f.hour = format_datetime(now() - interval '3' hour, 'HH')
      and f.section_assign_employee_first_level_department_name = 'H业务线'
      and f.section_assign_employee_second_level_department_name = '市场部'
      and f.section_assign_employee_third_level_department_name = '市场顾问部'
      and (f.period_mapping_first_level_department_name = 'H业务线' or f.period_mapping_first_level_department_name is null)
      and (f.period_mapping_second_level_department_name in ('精品班学部', '市场部') or f.period_mapping_second_level_department_name is null)
),
--------------------------5min比例、外呼次数、外呼接通次数
call_c as (
    select
        sub.user_number as user_number,
        sub.lead_id,
        sub.section_assign_employee_email_prefix,
        max(case when sub.call_duration > 300 then 1 else 0 end) as is_long_call,
        sum(sub.call_duration) as call_duration_1,
        sum(case when sub.call_status in ('1', '0') then 1 else 0 end) as zong_call_ci_1,
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
          and wf.hour = format_datetime(now() - interval '3' hour, 'HH')
    ) sub
    group by
        sub.user_number,
        sub.lead_id,
        sub.section_assign_employee_email_prefix
),
---------------------------crm首call任务
f_call0 as (
    select
        a.user_id,
        a.account_id,
        b.employee_email_name as assign_employee_email_name,
        case when sum(if(first_call_status = 3, 1, 0)) > 0 then 1 else 0 end as call_answer_lead_count
    from (
        select distinct
            user_id,
            first_call_status,
            expired_time,
            finished_time,
            start_time,
            task_generate_rule_type,
            task_rule_config,
            condition_relation,
            is_del,
            account_id,
            task_tag,
            biz_number,
            create_time,
            update_time
        from gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf
        where dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
          and hour = format_datetime(now() - interval '3' hour, 'HH')
          and start_time > '2026-01-01'
          and is_del = 0
    ) a
    left join (
        select
            account_id,
            employee_email_name
        from finance_dw.dim_finance_employee_df
        where dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
          and first_level_department_name = 'H业务线'
          and second_level_department_name = '市场部'
          and third_level_department_name = '市场顾问部'
    ) b on a.account_id = b.account_id
    group by
        a.user_id,
        a.account_id,
        b.employee_email_name
),
------------------------首节到课数据
daoke as (
    select
        qici,
        user_id,
        channel_map_1,
        max(
            case
                when channel_map_1 = '曹忆IP99元' then
                    case when ke_1 = '3' and live_learn_duration > 0 then 1 else 0 end
                else
                    case when ke_1 = '1' and live_learn_duration > 0 then 1 else 0 end
            end
        ) as has_daoke,
        max(
            case
                when channel_map_1 = '曹忆IP99元' then
                    case when ke_1 = '3' and is_valid_live_learn = '1' then 1 else 0 end
                else
                    case when ke_1 = '1' and is_valid_live_learn = '1' then 1 else 0 end
            end
        ) as has_v_daoke
    from (
        select
            t2.qici,
            t2.user_number as user_id,
            t1.channel_map_1,
            t2.live_learn_duration,
            t2.is_valid_live_learn,
            ke.ke_1,
            t1.grade_1
        from (
            select distinct
                lead_id,
                user_id,
                qici,
                channel_map_1,
                grade_1
            from data
        ) t1
        inner join (
            select
                user_number,
                begin_time,
                case
                    when cast(begin_time as date) between date '2026-07-14' and date '2026-07-19' then '20260716期'
                    when cast(begin_time as date) between date '2026-07-20' and date '2026-07-25' then '20260722期'
                    when cast(begin_time as date) between date '2026-07-26' and date '2026-07-31' then '20260728期'
                    when cast(begin_time as date) between date '2026-08-01' and date '2026-08-06' then '20260803期'
                    when cast(begin_time as date) between date '2026-08-07' and date '2026-08-12' then '20260809期'
                    when cast(begin_time as date) >= date '2026-02-25' and cast(begin_time as date) <= date '2026-03-02' then '20260227期'
                    when cast(begin_time as date) >= date '2026-02-17' and cast(begin_time as date) <= date '2026-02-24' then '20260220期'
                    when cast(begin_time as date) >= date '2026-02-09' and cast(begin_time as date) <= date '2026-02-16' then '20260213期'
                    when cast(begin_time as date) >= date '2026-02-03' and cast(begin_time as date) <= date '2026-02-08' then '20260206期'
                    else
                        case
                            when day_of_week(cast(begin_time as date)) = 2
                            then date_format(
                                date_trunc('week', cast(begin_time as timestamp)) - interval '3' day,
                                '%Y%m%d'
                            ) || '期'
                            else date_format(
                                date_trunc('week', cast(begin_time as timestamp)) + interval '4' day,
                                '%Y%m%d'
                            ) || '期'
                        end
                end as qici,
                is_need_attend,
                live_learn_duration,
                is_valid_live_learn
            from service_dw.dws_service_user_learn_detail_hf
            where dt = date_format(now() - interval '2' hour, '%Y%m%d')
              and hour = date_format(now() - interval '3' hour, '%H')
              and course_first_level_department_name = 'H业务线'
              and course_second_level_department_name in ('精品班学部', '市场部')
              and is_need_attend = 1
        ) t2 on t1.qici = t2.qici
             and t1.user_id = t2.user_number
        left join temp_table.dingxi01_daoke_1_6_t ke
          on t2.qici = ke.qici
         and t1.channel_map_1 = ke.qudao
         and t1.grade_1 = ke.grade
         and t2.begin_time = ke.begin_time
        where ke.ke_1 in ('1', '3')
    ) t
    group by
        qici,
        user_id,
        channel_map_1
),
----线索维度：期次，渠道，年级，架构
prc as (
    select distinct
        data.qici,
        data.rule_name,
        data.channel_map_1,
        data.grade_1,
        jg.department,
        jg.jingli,
        jg.xiaozu,
        data.employee_email_name,
        data.user_id,
        data.lead_count,
        data.valid_lead_count,
        data.first_call_time_diff_hour,
        data.first_call_time_diff_minute,
        case when data.first_call_time_diff_minute <= 5 and data.valid_lead_count > 0 then 1 else 0 end as first_call_in_5min,
        case when data.first_call_time_diff_hour <= 6 and data.valid_lead_count > 0 then 1 else 0 end as first_call_in_6h,
        case when data.first_call_time_diff_hour <= 12 and data.valid_lead_count > 0 then 1 else 0 end as first_call_in_12h,
        case when data.first_call_time_diff_hour <= 24 and data.valid_lead_count > 0 then 1 else 0 end as first_call_in_24h,
        case when data.first_call_time_diff_hour <= 48 and data.valid_lead_count > 0 then 1 else 0 end as first_call_in_48h,
        case when data.first_call_time_diff_hour <= 168 and data.valid_lead_count > 0 then 1 else 0 end as first_call_cnt,
        case when data.first_call_connected_time_diff_hour_1 <= 24 and data.valid_lead_count > 0 then 1 else 0 end as first_call_connected_in_24h,
        case when data.first_call_connected_time_diff_hour_1 <= 48 and data.valid_lead_count > 0 then 1 else 0 end as first_call_connected_in_48h,
        case when data.first_call_connected_time_diff_hour_1 <= 168 and data.valid_lead_count > 0 then 1 else 0 end as first_call_connected_cnt,
        round(coalesce(call_c.call_duration_1, 0) / 60.00, 2) as call_duration,
        coalesce(call_c.zong_call_ci_1, 0) as zong_call_ci,
        coalesce(call_c.call_status_1, 0) as call_status,
        case when data.valid_lead_count > 0 then coalesce(call_c.is_long_call, 0) else 0 end as is_long_call,
        coalesce(data.is_friend_lead, 0) as is_friend_lead,
        case when denglu_app.user_number is not null then denglu_app.is_app_denglu else 0 end as is_app_denglu,
        coalesce(data.is_shengou, 0) as is_shengou,
        coalesce(data.is_shuanggou, 0) as is_shuanggou,
        coalesce(data.yi_shuanggou, 0) as yi_shuanggou,
        coalesce(data.is_yichang, 0) as is_yichang,
        coalesce(data.yi_huishou, 0) as yi_huishou,
        case
            when coalesce(f_call0.call_answer_lead_count, 0) > 0
             and data.valid_lead_count > 0
            then 1 else 0
        end as is_f_call,
        concat(data.dt, ' ', data.hour) as datt
    from data
    left join jg_market jg
      on data.employee_email_prefix = jg.employee_email_prefix
     and data.qici = jg.qici
    left join call_c
      on call_c.user_number = data.user_id
     and call_c.section_assign_employee_email_prefix = data.employee_email_prefix
    left join denglu_app
      on denglu_app.user_number = data.user_id
    left join f_call0
      on f_call0.assign_employee_email_name = data.employee_email_name
     and f_call0.user_id = data.user_id
    where data.qici > '20260507期'
      and data.virtual_third_department_name = '市场顾问部'
      and jg.department is not null
)
----------------------汇总
select *
from (
    select
        prc.qici,
        prc.rule_name,
        prc.channel_map_1,
        prc.grade_1,
        prc.department,
        prc.jingli,
        prc.xiaozu,
        prc.employee_email_name,
        prc.datt,
        sum(lead_count) as lead_count,
        sum(valid_lead_count) as valid_lead_count,
        sum(first_call_time_diff_hour) as first_call_time_diff_hour,
        sum(first_call_in_5min) as first_call_in_5min,
        sum(first_call_in_6h) as first_call_in_6h,
        sum(first_call_in_12h) as first_call_in_12h,
        sum(first_call_in_24h) as first_call_in_24h,
        sum(first_call_in_48h) as first_call_in_48h,
        sum(first_call_cnt) as first_call_cnt,
        sum(first_call_connected_in_24h) as first_call_connected_in_24h,
        sum(first_call_connected_in_48h) as first_call_connected_in_48h,
        sum(first_call_connected_cnt) as first_call_connected_cnt,
        sum(call_duration) as call_duration,
        sum(zong_call_ci) as zong_call_ci,
        sum(call_status) as call_status,
        sum(is_long_call) as is_long_call,
        sum(is_friend_lead) as is_friend_lead,
        sum(is_app_denglu) as is_app_denglu,
        sum(is_shengou) as is_shengou,
        sum(is_shuanggou) as is_shuanggou,
        sum(yi_shuanggou) as yi_shuanggou,
        sum(yi_huishou) as yi_huishou,
        sum(is_yichang) as is_yichang,
        sum(is_f_call) as is_f_call,
        count(distinct case when duf.has_daoke = 1 then prc.user_id end) as daoke1,
        count(distinct case when duf.has_v_daoke = 1 then prc.user_id end) as v_daoke1
    from prc
    left join daoke duf
      on prc.qici = duf.qici
     and prc.user_id = duf.user_id
     and prc.channel_map_1 = duf.channel_map_1
    group by
        prc.qici,
        prc.rule_name,
        prc.channel_map_1,
        prc.grade_1,
        prc.department,
        prc.jingli,
        prc.xiaozu,
        prc.employee_email_name,
        prc.datt
)
