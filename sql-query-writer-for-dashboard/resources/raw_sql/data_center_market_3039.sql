with data_pre as (
    select distinct
        concat(
            date_format(
                date_trunc(
                    'week',
                    date_parse(replace(concat(t1.group_period_year, t1.group_period_term), '期', ''), '%Y%m%d')
                      - interval '1' day
                ) + interval '4' day,
                '%Y%m%d'
            ),
            '期'
        ) as period_name,
        t1.virtual_third_department_name as depart_1,
        t1.virtual_fourth_department_name as depart,
        t1.virtual_leader_email_name as jingli,
        t1.virtual_direct_leader_email_name as zhuguan,
        t1.employee_email_name,
        t1.employee_email_prefix,
        t1.rule_name,
        t1.lead_id,
        t1.user_id,
        t1.flow_pool_name,
        t1.third_department_name,
        t1.sku_id_name,
        t1.ad_account_name,
        t1.source_manager_name,
        t1.channel_name_1,
        t1.channel_name_2,
        t1.channel_name_3,
        t1.virtual_second_department_name,
        t1.virtual_fourth_department_name,
        t1.virtual_fifth_department_name,
        t1.put_plan_name,
        t1.channel_provider_name,
        t1.channel_second_provider_name,
        t1.page_id_name,
        t1.source_put_plan_name,
        t1.first_department_name,
        t1.second_department_name,
        t1.lead_purchase_intention_name,
        t1.lead_purchase_intention_level1_category_name,
        t1.lead_purchase_intention_level2_category_name,
        t1.flow_original_order_activity_price,
        t1.flow_order_price,
        t1.flow_orders_income_amount,
        t1.get_customer_way_name,
  t1.lead_create_time,
case 
    when rule_name like '%高一%' then '高一'
    when rule_name like '%高二%' then '高二'
    when rule_name like '%高三%' then '高三'
    when rule_name like '%初二%' then '初二'
    when rule_name like '%初三%' then '初三'
    when rule_name like '%初一%' then '初一'
    else lead_purchase_intention_level2_category_name
end as grade_1,
        coalesce(t1.lead_count, 0) as lead_count,
        coalesce(t1.valid_lead_count, 0) as valid_lead_count,
        coalesce(t1.conversion_lead_count, 0) as conversion_lead_count,
        coalesce(t1.subject_count, 0) as subject_count,
        coalesce(t1.same_lead_period_subject_count, 0) as same_lead_period_subject_count,
        coalesce(t1.lb_subject_count, 0) as lb_subject_count,
        coalesce(t1.same_lead_period_lb_subject_count, 0) as same_lead_period_lb_subject_count,
        coalesce(t1.order_count, 0) as order_count,
        coalesce(t1.income_amount, 0) as income_amount,
        coalesce(t1.in_pay_period_refund_amount, 0) as in_pay_period_refund_amount,
        coalesce(t1.non_pay_period_refund_amount, 0) as non_pay_period_refund_amount,
        coalesce(t1.jp_cross_department_refund_amount, 0) as jp_cross_department_refund_amount,
        coalesce(t1.same_lead_period_order_count, 0) as same_lead_period_order_count,
        coalesce(t1.same_lead_period_conversion_lead_count, 0) as same_lead_period_conversion_lead_count,
        coalesce(t1.same_lead_period_income_amount, 0) as same_lead_period_income_amount,
        coalesce(t1.same_lead_period_refund_amount, 0) as same_lead_period_refund_amount,

        date_diff('hour', cast(t1.section_assign_time as timestamp), cast(t1.first_call_time as timestamp)) as first_call_time_diff_hour,
        coalesce(case when cast(t1.valid_lead_count as varchar) = '1' then t1.friend_lead_count else 0 end, 0) as is_friend_lead,
        coalesce(case when t.jieduan in ('深沟','已双沟') then 1 else 0 end, 0) as is_shengou,
        coalesce(case
            when cast(t.sale_flow_stage_sequence as varchar) in ('470', '700', '850', '950', '955', '1050')
            then 1 else 0
        end, 0) as is_shuanggou,
        coalesce(case when t.jieduan in ('深沟') and t1.conversion_lead_count = 1 then 1 else 0 end, 0) as sg_payers,
        coalesce(case when t.jieduan in ('已双沟') and t1.conversion_lead_count = 1 then 1 else 0 end, 0) as ssg_payers,
        coalesce(case when t1.intention_level in ('A', 'B') and t.jieduan in ('深沟','已双沟') then 1 else 0 end, 0) as AB_intention_level,
        coalesce(case when t1.intention_level in ('A', 'B') and t1.conversion_lead_count = 1 then 1 else 0 end, 0) as AB_zhuanhua
    from bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df t1
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
                    when sale_flow_stage_sequence = 450 then '深沟'
                    when sale_flow_stage_sequence = 470 then '已双沟'
                    else '其他'
                end as jieduan_1,
                case
                    when sale_flow_stage_sequence = 50 then '新线索'
                    when sale_flow_stage_sequence = 60 then '待跟进'
                    when sale_flow_stage_sequence = 70 then '已接收'
                    when sale_flow_stage_sequence = 100 then '未接通'
                    when sale_flow_stage_sequence = 150 then '已建联'
                    when sale_flow_stage_sequence = 200 then '首call'
                    when sale_flow_stage_sequence = 250 then '商机'
                    when sale_flow_stage_sequence = 300 then '学情沟通'
                    when sale_flow_stage_sequence = 350 then '浅沟'
                    when sale_flow_stage_sequence = 400 then '已约课'
                    when sale_flow_stage_sequence = 450 then '深沟'
                    when sale_flow_stage_sequence = 470 then '已双沟'
                    else '未知状态'
                end as sale_flow_stage_name_1,
                row_number() over (partition by user_number order by private_sea_update_time desc) as rn
            from service_dw.dwd_crm_assign_private_detail_hf
            where dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
              and hour = format_datetime(now() - interval '3' hour, 'HH')
              and assign_employee_first_level_department_name = 'H业务线'
              and assign_employee_second_level_department_name = '市场部'
              and assign_employee_third_level_department_name = '市场顾问部'
        ) x
        where rn = 1
    ) t on t1.user_id = t.user_number
    where t1.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
      and t1.hour = format_datetime(now() - interval '3' hour, 'HH')
      and t1.section_assign_employee_first_level_department_name = 'H业务线'
      and t1.section_assign_employee_second_level_department_name = '市场部'
      and t1.section_assign_employee_third_level_department_name = '市场顾问部'
      and t1.period_mapping_first_level_department_name = 'H业务线' 

),
data as (
    select
        period_name,
        depart_1,
        depart,
        jingli,
        zhuguan,
        employee_email_name,
        employee_email_prefix,
        rule_name,
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
when (flow_pool_name like '%孟帝%' or flow_pool_name like '%孟老师%' or flow_pool_name like '%中考数学冲刺%' or flow_pool_name like '%8升9数学%' or flow_pool_name like '%孟亚飞讲数学%' or flow_pool_name like '%中考冲刺%' or flow_pool_name like '%中考满分冲刺%' or flow_pool_name like '%押题王孟亚飞%' or flow_pool_name like '%中考数学大通关%' or flow_pool_name like '%中考数学规划%' or flow_pool_name like '%亚飞数学%' or flow_pool_name like '%孟帝数学%')  and period_name not like '%多学科拓展%' and channel_name_2 not like '%KOL%' and third_department_name='直播部' and channel_name_2 = '视频号'  then '孟亚飞9元'
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
        first_call_time_diff_hour,
        is_friend_lead,
        is_shengou,
        is_shuanggou,
        sg_payers,
        ssg_payers,
        AB_intention_level,
        AB_zhuanhua
    from data_pre
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
            and wf.hour = format_datetime(now() - interval '3' hour, 'HH')
    ) sub
    group by 1,2,3
)
---------------------------crm首call任务
,f_call0 as (
select 
     a.user_id 
	,b.employee_email_name assign_employee_email_name
	,case when sum(if(first_call_status=3,1,0)) > 0 then 1 else 0 end as call_answer_lead_count
	from  
	    (select 
	        distinct user_id
	        ,first_call_status	--	int	首call状态 1.未开始 2.进行中 3.已完成 4.未完成
	        ,expired_time --过期时间点
	        ,finished_time --完成时间点
	        ,start_time --开始时间点
	        ,task_generate_rule_type --任务类型 2 顾问首call
	        ,task_rule_config
	        ,condition_relation --完成条件间关系：1-AND（所有条件都要满足），2-OR（任意条件满足即可）
	        ,is_del
	        ,account_id --顾问id
-- 	        ,org_number
	        ,task_tag --任务当前标签：1-有效，2-无效
	        ,biz_number --期次id
	        ,create_time
	        ,update_time
            from gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf
	        where  dt=format_datetime(NOW()-interval '2' hour,'YYYYMMdd') and hour=format_datetime(NOW()-interval '3' hour,'HH' )
	        and task_generate_rule_type = 2
	        and start_time > timestamp '2026-01-01 00:00:00'
	        and is_del = 0
		 ) a
	left join (select account_id,employee_email_name
from finance_dw.dim_finance_employee_df
where  dt=format_datetime(NOW()-interval '24' hour,'YYYYMMdd')
and first_level_department_name = 'H业务线'
and second_level_department_name  = '市场部'
and third_level_department_name = '市场顾问部') b  on a.account_id = b.account_id
	group by a.user_id,b.employee_email_name)		
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
end as qici,
                mod(date_diff('day', cast('2021-02-01' as date), cast(begin_time as date)), 7) as dow,
                is_need_attend,
                live_learn_duration,
                is_valid_live_learn
            from service_dw.dws_service_user_learn_detail_hf  
            where dt = date_format(now() - interval '2' hour, '%Y%m%d') 
                and hour = date_format(now() - interval '3' hour, '%H')
                and course_first_level_department_name = 'H业务线'
                and course_second_level_department_name in ('精品班学部','市场部','青橙项目部')
                and is_need_attend = 1
        ) t2 on t1.period_name = t2.qici and t1.user_id = t2.user_number) dk
	left join temp_table.dingxi01_daoke_1_6_t ke on dk.period_name = ke.qici and dk.channel_map = ke.channel and dk.grade_1 = ke.grade and dk.begin_time = ke.begin_time)
-----------------------整合 
,base as 
(select distinct
data.*,
case when data.first_call_time_diff_hour >= 0 and data.first_call_time_diff_hour <= 48 and data.valid_lead_count > 0 then 1 else 0 end as first_call_in_48h,
case when data.valid_lead_count = 1 then coalesce(call_c.is_long_call, 0) else 0 end as is_long_call,
case when data.valid_lead_count = 1 then coalesce(f_call0.call_answer_lead_count, 0) else 0 end as is_f_call,
case when call_c.call_duration_1 >= 30 and call_c.call_duration_1 < 1200 then 1 else 0 end  as is_5m_call,
case when call_c.call_duration_1 >= 1200 and call_c.call_duration_1 < 2400 then 1 else 0 end  as is_20m_call,
case when call_c.call_duration_1 >= 2400 then 1 else 0 end as is_40m_call,
case when data.valid_lead_count = 1 and conversion_lead_count = 1 then coalesce(call_c.is_long_call, 0) else 0 end as long_call_z,
case when conversion_lead_count = 1 and call_c.call_duration_1 >= 30 and call_c.call_duration_1 < 1200 then 1 else 0 end as call_5m_z,
case when conversion_lead_count = 1 and call_c.call_duration_1 >= 1200 and call_c.call_duration_1 < 2400 then 1 else 0 end as call_20m_z,
case when conversion_lead_count = 1 and call_c.call_duration_1 >= 2400 then 1 else 0 end as call_40m_z,
	---------------到课用的渠道！！
	case 
            when data.channel_map = '曹忆' 
                then case when exists (
                    select 1 
                    from daoke 
                    where daoke.user_id = data.user_id 
                        and daoke.employee_email_prefix = data.employee_email_prefix 
                        and daoke.period_name = data.period_name 
                        and data.channel_map = daoke.channel_map
                        and daoke.ke_1 = '3' 
                        and daoke.live_learn_duration > 0
                ) then 1 else 0 end
            else case when exists (
                    select 1 
                    from daoke 
                    where daoke.user_id = data.user_id 
                        and daoke.employee_email_prefix = data.employee_email_prefix 
                        and daoke.period_name = data.period_name 
                        and data.channel_map = daoke.channel_map
                        and daoke.ke_1 = '1' 
                        and daoke.live_learn_duration > 0
                ) then 1 else 0 end
        end as daoke1
    from data 
left join call_c on call_c.user_number = data.user_id and call_c.section_assign_employee_email_prefix = data.employee_email_prefix and call_c.lead_id = data.lead_id
left join f_call0 on f_call0.assign_employee_email_name = data.employee_email_name and f_call0.user_id = data.user_id 
)
---------------------------转化
,zhuanhua as
(select
    period_name,
 	channel_map,
	rule_name,
 	grade_1,
	depart_1,
    depart,
    jingli,-- 大组长
    zhuguan, -- 小组长
    employee_email_name,
    sum(lead_count) lead_count,
    sum(valid_lead_count) can_renew_ds_count_a,
    sum(is_friend_lead) friend_lead,
 	sum(is_shengou) shengou_lead,
 	sum(is_shuanggou) shuanggou_lead,
	sum(sg_payers) sg_payers,
	sum(ssg_payers) ssg_payers,
 	 sum(AB_intention_level) AB_lead,
	 sum(AB_zhuanhua) AB_zhuan,
    sum(first_call_in_48h) first_call_in_48h,
   sum(is_long_call) is_long_call,
   sum(is_f_call) is_f_call,
	sum(is_5m_call) is_5m_call,sum(is_20m_call) is_20m_call,sum(is_40m_call) is_40m_call,
 	sum(long_call_z) long_call_z,sum(call_20m_z) call_20m_z,sum(call_40m_z) call_40m_z,
	sum(call_5m_z) call_5m_z,
    sum(daoke1) daoke_1,
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
	rule_name,
 	 grade_1,
	 depart_1,
    depart,
    jingli,-- 大组长
    zhuguan, -- 小组长
    employee_email_name
)
,zx_active as (
    select
        employee_email_name,
        xiaozu,
        jingli
    from (
        select
            zx.*,
            row_number() over (
                partition by zx.employee_email_name
                order by
                    case
                        when zx.department = '郑州顾问部' then 1
                        when zx.department = '西安一部' then 2
                        when zx.department = '西安二部' then 3
                        else 9
                    end,
                    zx.employee_email_prefix,
                    zx.xiaozu,
                    zx.jingli
            ) as rn
        from temp_table.dingxi01_jiagou_zx zx
        where cast(zx.zaizhi as varchar) = '1'
          and zx.department in ('郑州顾问部', '西安一部', '西安二部')
    ) t
    where rn = 1
)
,cost_exact as (
    select
        qici,
        channel,
        grade,
        max(coalesce(cost, 0)) as cost,
        max(coalesce(goal, 0)) as goal
    from temp_table.dingxi01_cost
    where grade <> '0'
    group by qici, channel, grade
)
,cost_zero as (
    select
        qici,
        channel,
        max(coalesce(cost, 0)) as cost,
        max(coalesce(goal, 0)) as goal
    from temp_table.dingxi01_cost
    where grade = '0'
    group by qici, channel
)
,jiagou_period as (
    select
        qici,
        department,
        employee_email_name,
        xiaozu,
        jingli
    from (
        select
            nullif(trim(cast(jg.qici as varchar)), '') as qici,
            nullif(trim(cast(jg.department as varchar)), '') as department,
            nullif(trim(cast(jg.employee_email_name as varchar)), '') as employee_email_name,
            nullif(trim(cast(jg.xiaozu as varchar)), '') as xiaozu,
            nullif(trim(cast(jg.jingli as varchar)), '') as jingli,
            row_number() over (
                partition by
                    nullif(trim(cast(jg.qici as varchar)), ''),
                    nullif(trim(cast(jg.department as varchar)), ''),
                    nullif(trim(cast(jg.employee_email_name as varchar)), '')
                order by
                    case when nullif(trim(cast(jg.xiaozu as varchar)), '') is not null then 0 else 1 end,
                    nullif(trim(cast(jg.xiaozu as varchar)), ''),
                    nullif(trim(cast(jg.jingli as varchar)), '')
            ) as rn
        from temp_table.dingxi01_jiagou_db jg
    ) t
    where rn = 1
)
-------------结果指标
,final_result as (
select
    zz.period_name,
    zz.channel_map,
    zz.rule_name,
    zz.grade_1,
    zz.depart_1,
    zz.depart,
    coalesce(jg.jingli, zx.jingli, zz.jingli) as jingli,
    coalesce(jg.xiaozu, zx.xiaozu, zz.zhuguan) as zhuguan,
    zz.employee_email_name,
    zz.lead_count,
    zz.can_renew_ds_count_a,
    zz.friend_lead,
    zz.shengou_lead,
    zz.shuanggou_lead,
    zz.sg_payers,
    zz.ssg_payers,
    zz.AB_lead,
    zz.AB_zhuan,
    zz.first_call_in_48h,
    zz.is_long_call,
    zz.is_f_call,
    zz.is_5m_call,
    zz.is_20m_call,
    zz.is_40m_call,
    zz.long_call_z,
    zz.call_20m_z,
    zz.call_40m_z,
    zz.call_5m_z,
    zz.daoke_1,
    zz.pay_users,
    zz.pay_users_on_period,
    zz.pay_users_not_on_period,
    zz.pay_user_subs,
    zz.pay_user_subs_on_period,
    zz.pay_user_subs_not_on_period,
    zz.pay_user_subs_joint,
    zz.pay_user_subs_joint_onp,
    zz.pay_user_subs_joint_nonp,
    zz.trade_income,
    zz.trade_refund,
    zz.trade_profit,
    zz.xb_trade_income,
    zz.xb_trade_profit,
    zz.kk_trade_income,
    zz.pre_refund,
    case
        when zz.can_renew_ds_count_a >= 5 then zz.can_renew_ds_count_a
        else 0
    end as s_lead,
    case
        when zz.can_renew_ds_count_a >= 5 and zz.trade_income > 0 then 1
        else 0
    end as podan,
    case
        when zz.can_renew_ds_count_a >= 5 then zz.employee_email_name
        else '未知'
    end as name1,
    coalesce(jg.xiaozu, zx.xiaozu, zz.zhuguan) as xiaozu,
    coalesce(jg.jingli, zx.jingli, zz.jingli) as jingli_11,
    coalesce(ce.cost, cz.cost, 0) as cb_cb,
    coalesce(ce.goal, cz.goal, 0) as gl_gl
from zhuanhua zz
left join cost_exact ce
  on ce.channel = zz.channel_map
 and ce.grade = zz.grade_1
 and ce.qici = zz.period_name
left join cost_zero cz
  on cz.channel = zz.channel_map
 and cz.qici = zz.period_name
 and ce.channel is null
left join jiagou_period jg
  on jg.qici = zz.period_name
 and jg.department = zz.depart
 and zz.employee_email_name = jg.employee_email_name
left join zx_active zx
  on zx.employee_email_name = zz.employee_email_name
where zz.period_name > '20250704期'
)
,employee_channel_agg as (
    select
        period_name,
        depart,
        employee_email_name,
        channel_map,
        sum(lead_count) as channel_lead_count
    from final_result
    group by
        period_name,
        depart,
        employee_email_name,
        channel_map
),
employee_headcount_agg as (
    select
        period_name,
        depart,
        employee_email_name,
        count(distinct case when channel_lead_count > 0 then channel_map end) as channel_mix_cnt_all,
        sum(channel_lead_count) as employee_total_lead_count_all
    from employee_channel_agg
    group by
        period_name,
        depart,
        employee_email_name
),
final_result_headcount_base as (
    select
        fr.*,
        eh.channel_mix_cnt_all,
        eh.employee_total_lead_count_all,
        row_number() over (
            partition by fr.period_name, fr.depart, fr.employee_email_name, fr.channel_map
            order by fr.rule_name, fr.grade_1, fr.employee_email_name
        ) as rn_employee_channel_all,
        row_number() over (
            partition by fr.period_name, fr.depart, fr.employee_email_name
            order by fr.channel_map, fr.rule_name, fr.grade_1
        ) as rn_employee_all
    from final_result fr
    left join employee_headcount_agg eh
      on eh.period_name = fr.period_name
     and eh.depart = fr.depart
     and eh.employee_email_name = fr.employee_email_name
),
final_result_enriched as (
    select
        frh.period_name,
        frh.channel_map,
        frh.rule_name,
        frh.grade_1,
        frh.depart_1,
        frh.depart,
        frh.jingli,
        frh.zhuguan,
        frh.employee_email_name,
        frh.lead_count,
        frh.can_renew_ds_count_a,
        frh.friend_lead,
        frh.shengou_lead,
        frh.shuanggou_lead,
        frh.sg_payers,
        frh.ssg_payers,
        frh.AB_lead,
        frh.AB_zhuan,
        frh.first_call_in_48h,
        frh.is_long_call,
        frh.is_f_call,
        frh.is_5m_call,
        frh.is_20m_call,
        frh.is_40m_call,
        frh.long_call_z,
        frh.call_20m_z,
        frh.call_40m_z,
        frh.call_5m_z,
        frh.daoke_1,
        frh.pay_users,
        frh.pay_users_on_period,
        frh.pay_users_not_on_period,
        frh.pay_user_subs,
        frh.pay_user_subs_on_period,
        frh.pay_user_subs_not_on_period,
        frh.pay_user_subs_joint,
        frh.pay_user_subs_joint_onp,
        frh.pay_user_subs_joint_nonp,
        frh.trade_income,
        frh.trade_refund,
        frh.trade_profit,
        frh.xb_trade_income,
        frh.xb_trade_profit,
        frh.kk_trade_income,
        frh.pre_refund,
        frh.s_lead,
        frh.podan,
        frh.name1,
        frh.xiaozu,
        frh.jingli_11,
        frh.cb_cb,
        frh.gl_gl,
        frh.channel_mix_cnt_all,
        frh.employee_total_lead_count_all,
        case
            when frh.employee_total_lead_count_all > 0
             and frh.rn_employee_channel_all = 1 then 1
            else 0
        end as jieliang_channel_row_all,
        case
            when frh.employee_total_lead_count_all > 0
             and frh.channel_mix_cnt_all >= 2
             and frh.rn_employee_channel_all = 1 then 1
            else 0
        end as mix_channel_row_all,
        case
            when frh.employee_total_lead_count_all > 0
             and frh.rn_employee_all = 1 then 1
            else 0
        end as jieliang_true_once_all,
        case
            when frh.employee_total_lead_count_all > 0
             and frh.channel_mix_cnt_all >= 2
             and frh.rn_employee_all = 1 then 1
            else 0
        end as mix_employee_once_all,
        case
            when frh.employee_total_lead_count_all > 0
             and frh.rn_employee_all = 1 then frh.channel_mix_cnt_all - 1
            else 0
        end as mix_extra_once_all,
        case
            when frh.employee_total_lead_count_all > 0
             and frh.rn_employee_channel_all = 1
            then cast(1.0 / frh.channel_mix_cnt_all as decimal(18, 6))
            else cast(0 as decimal(18, 6))
        end as jieliang_weight_row_all
    from final_result_headcount_base frh
),
employee_tenure_src as (
    select
        e.employee_email_name,
        e.email_prefix,
        try_cast(
            substr(
                coalesce(nullif(e.last_enroll_date, ''), nullif(e.first_enroll_date, '')),
                1,
                10
            ) as date
        ) as enroll_date,
        row_number() over (
            partition by e.employee_email_name
            order by
                case when e.is_on_job = 1 then 0 else 1 end,
                coalesce(nullif(e.last_enroll_date, ''), nullif(e.first_enroll_date, '')) desc,
                e.email_prefix
        ) as rn
    from finance_dw.dim_finance_employee_df e
    where e.dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
      and e.is_main_job = 1
      and e.is_on_job = 1
      and e.first_level_department_name = 'H业务线'
      and e.second_level_department_name = '市场部'
      and e.third_level_department_name = '市场顾问部'
),
employee_tenure as (
    select
        employee_email_name,
        email_prefix,
        enroll_date,
        date_diff('month', enroll_date, current_date) as on_job_months,
        case
            when enroll_date is null then '待确认'
            when date_diff('month', enroll_date, current_date) < 1 then '1个月以内'
            when date_diff('month', enroll_date, current_date) < 4 then '2-3个月'
            when date_diff('month', enroll_date, current_date) < 7 then '4-6个月'
            when date_diff('month', enroll_date, current_date) < 12 then '7-12个月'
            when date_diff('month', enroll_date, current_date) < 24 then '一年以上'
            else '2年以上'
        end as on_job_time_bucket
    from employee_tenure_src
    where rn = 1
),
period_rank as (
    select
        period_name,
        dense_rank() over (order by period_name desc) as period_rank
    from (
        select distinct period_name
        from final_result_enriched
    ) t
),
final_dataset as (
    select
        fre.period_name,
        fre.channel_map,
        fre.grade_1,
        fre.jingli as manager_name,
        fre.zhuguan as supervisor_name,
        fre.employee_email_name as consultant_name,
        et.enroll_date,
        et.on_job_months,
        coalesce(et.on_job_time_bucket, '待确认') as on_job_time_bucket,
        fre.lead_count as before_refund_lead_cnt,
        fre.can_renew_ds_count_a as after_refund_lead_cnt,
        fre.is_f_call as first_call_num,
        fre.can_renew_ds_count_a as first_call_den,
        fre.first_call_in_48h as call_48h_num,
        fre.can_renew_ds_count_a as call_48h_den,
        fre.friend_lead as friend_num,
        fre.can_renew_ds_count_a as friend_den,
        fre.is_long_call as call_5min_num,
        fre.can_renew_ds_count_a as call_5min_den,
        fre.shengou_lead as deep_communication_num,
        fre.can_renew_ds_count_a as deep_communication_den,
        fre.shuanggou_lead as double_communication_num,
        fre.can_renew_ds_count_a as double_communication_den,
        fre.pay_users_on_period as current_head_conversion_num,
        fre.can_renew_ds_count_a as current_head_conversion_den,
        fre.xb_trade_income as current_income_amt,
        fre.xb_trade_profit as current_net_income_amt,
        fre.xb_trade_profit as current_unit_efficiency_num,
        fre.can_renew_ds_count_a as current_unit_efficiency_den,
        fre.pay_users as head_conversion_num,
        fre.can_renew_ds_count_a as head_conversion_den,
        fre.trade_income as income_amt,
        fre.trade_profit as net_income_amt,
        fre.trade_profit as unit_efficiency_num,
        fre.can_renew_ds_count_a as unit_efficiency_den,
        fre.pay_user_subs as avg_subject_num,
        fre.pay_users as avg_subject_den,
        fre.trade_refund as section_refund_rate_num,
        fre.trade_income as section_refund_rate_den,
        pr.period_rank
    from final_result_enriched fre
    left join period_rank pr
      on fre.period_name = pr.period_name
    left join employee_tenure et
      on et.employee_email_name = fre.employee_email_name
)
select
    period_name,
    channel_map,
    grade_1,
    manager_name,
    supervisor_name,
    consultant_name,
    enroll_date,
    on_job_months,
    on_job_time_bucket,
    before_refund_lead_cnt,
    after_refund_lead_cnt,
    first_call_num,
    first_call_den,
    call_48h_num,
    call_48h_den,
    friend_num,
    friend_den,
    call_5min_num,
    call_5min_den,
    deep_communication_num,
    deep_communication_den,
    double_communication_num,
    double_communication_den,
    current_head_conversion_num,
    current_head_conversion_den,
    current_income_amt,
    current_net_income_amt,
    current_unit_efficiency_num,
    current_unit_efficiency_den,
    head_conversion_num,
    head_conversion_den,
    income_amt,
    net_income_amt,
    unit_efficiency_num,
    unit_efficiency_den,
    avg_subject_num,
    avg_subject_den,
    section_refund_rate_num,
    section_refund_rate_den,
    period_rank
from final_dataset
