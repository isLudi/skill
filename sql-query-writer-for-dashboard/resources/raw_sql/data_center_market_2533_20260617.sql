-------------------APP天级+小时级
with d_ap as (
select distinct 
        user_latest.user_number,
        user_latest.last_event_time,
        user_latest.product_name,
        user_latest.appliction_name,
        case when user_latest.event_timestamp >= now() - interval '7' day and user_latest.appliction_name in ('PC客户端','APP','PC') then 1 else 0 end as is_app_denglu_d,
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
            select *,
                row_number() over (partition by user_number order by try(date_parse(last_event_time, '%Y-%m-%d %H:%i:%s:%f')) desc) as rn
            from dw.dim_cstm_active_user_c_appliction_mb_df
            where dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd') 
                and product_name in ('高途','规划精品')
        ) ul
        where rn = 1
    ) user_latest)
,h_ap as (
select distinct 
user_number,
case when application_name in ('PC客户端','APP','PC') then 1 else 0 end as is_app_denglu_h
from dw.dws_user_active_user_c_appliction_hf			
where dt=format_datetime(now()-interval '2' hour,'YYYYMMdd') 
	and hour=format_datetime(now()-interval '2' hour,'HH')    
    and product_name in ('高途','规划精品'))
,denglu_app as (
select d_ap.user_number,
case when (coalesce(is_app_denglu_h,0) = '1' or coalesce(is_app_denglu_d,0) = '1') then 1 else 0 end as is_app_denglu
from d_ap left join h_ap on d_ap.user_number = h_ap.user_number),

--------------------------------------基础数据	
data as (
    select distinct 
        f.*,
concat(cast(date_format(date_add('day',4,date_trunc('week',date_add('day',-1,date_parse(replace(concat(f.group_period_year,f.group_period_term),'期',''),'%Y%m%d')))),'%Y%m%d')as varchar),'期') as qici
  ,case
when f.rule_name like '%亚飞99元西安直播%' then '亚飞99元西安直播'
when f.rule_name like '%koc测试5元%' then 'koc测试5元'
when f.rule_name like '%百度搜索%' then '百度搜索'
when f.rule_name like '%亚飞9元百度%'  then '亚飞9元百度'
when f.rule_name like '%孟亚飞ip0元B站%'  then '孟亚飞ip0元B站'
when f.rule_name like '%孟亚飞常规99元%'  then '孟亚飞常规99元'
when f.rule_name like '%tmk3元周帅%' then 'tmk3元周帅'
when f.rule_name like '%tmk9元沈阳%' then 'tmk9元沈阳'
when f.rule_name like '%tmk9元启师%' then 'tmk9元启师'
when f.rule_name like '%tmk9元伍仟里%' then 'tmk9元伍仟里'
when f.rule_name like '%抖音私域%' or f.rule_name like '%抖音私信%' then '抖音私信'
when f.rule_name like '%曹忆ip99元福建%'  then '曹忆ip99元福建'
when f.rule_name like '%曹忆ip99元江苏%'  then '曹忆ip99元江苏'
when f.rule_name like '%孟亚飞ip9元福建%'  then '孟亚飞ip9元福建'
when f.rule_name like '%孟亚飞ip9元江苏%'  then '孟亚飞ip9元江苏'
when f.rule_name like '%孟亚飞ip9元河南%'  then '孟亚飞ip9元河南'
when f.rule_name like '%孟亚飞ip9元河北%'  then '孟亚飞ip9元河北'
when f.rule_name like '%周帅ip9元%'  then '周帅ip9元'
when f.rule_name like '%朱汉祺ip9元%'  then '朱汉祺ip9元'
when f.rule_name like '%曹忆ip99元%' then '曹忆IP99元'
when f.rule_name like '%APP%' then 'APP'
when f.rule_name like '%线索复用%' then '线索复用'
when f.rule_name like '%孟亚飞ip19元%' or f.rule_name like '%孟亚飞IP19元%' then '孟亚飞IP9元'
when f.rule_name like '%孟亚飞IP99元%' or f.rule_name like '%孟亚飞ip99元%'  then '孟亚飞IP99元'
when (f.rule_name like '%孟亚飞IP9元%' or f.rule_name like '%孟亚飞ip9元%') and  rule_name not like '%孟亚飞IP99元%' then '孟亚飞IP9元'
when (f.rule_name like '%孟亚飞IP%' or rule_name  like '%孟亚飞ip9元%') and rule_name not like '%孟亚飞IP9元%' then '孟亚飞IP9元'
when f.rule_name like '%图书KOC%' then '图书KOC'
when f.rule_name like '%朱汉祺IP%' then '朱汉祺IP'
when f.rule_name like '%西安图书%' then '西安图书'
when f.rule_name like '%常规KOC%' then '常规KOC'
when f.rule_name like '%进校%' then '进校0元'
when f.rule_name like '%春春B站99元%' then '春春B站99元'
when f.rule_name like '%肖晗ip9元%' then '肖晗ip9元'
when f.rule_name like '%肖晗ip19元%' or f.rule_name like '%ip肖晗19元%' then '肖晗ip19元'
when f.rule_name like '%koc肖晗5元%' then 'koc肖晗5元' 
when f.rule_name like '%koc自孵化5元%' or f.rule_name like '%koc广州本地化5元%'then 'koc自孵化5元' 
when f.rule_name like '%koc常规5元%' then 'koc常规5元' 
when f.rule_name like '%koc朱汉祺5元%'  then 'koc朱汉祺5元'  
when f.rule_name like '%朱汉祺ip29元%' then '朱汉祺ip29元'	
when f.rule_name like '%koc朱汉祺29元%' or f.rule_name like '%koc周帅29元%' or f.rule_name like '%周帅29元%' or f.rule_name like '%朱汉祺29元%' or f.rule_name like '%朱汉祺koc29元%' then 'koc29元' 
when f.rule_name like '%B站孟亚飞%' then 'B站孟亚飞' 
when f.rule_name like '%B站朱汉祺29元%' or f.rule_name like '%B站周帅19元%' then 'B站29元' 
when f.rule_name like '%春春ip99元%' then '春春ip99元'
when f.rule_name like '%私域0元%' or f.rule_name like '%表单高中%' or f.rule_name like '%私域表单0元%' then '私域0元' 
when f.rule_name like '%私域9元%' then '私域9元' 
when f.rule_name like '%拓展koc%' or f.rule_name like '%拓展ip%' or f.rule_name like '%koc外部发货%' or f.rule_name like '%多学科拓展%' then '多学科拓展'
when f.rule_name like '%商务书商1元%' or f.rule_name like '%商务1元%' or f.rule_name like '%商务进校18元%' or f.rule_name like '%商务TMK9元%' or f.rule_name like '%商务%' then '商务'
when f.rule_name like '%训练营%' or f.rule_name like '%CRM特殊链接分配策略%' then '训练营' 
when f.flow_pool_name ='途途教室小程序' and f.get_customer_way_name = '小程序' then '训练营'
when f.flow_pool_name ='EES系统' and f.get_customer_way_name = '私域运营' then '训练营'
when f.lead_purchase_intention_name like '%多学科拓展%' and f.get_customer_way_name = '微信私域' then '训练营'
when f.rule_name like '%信息流%' then '信息流'
when f.rule_name like '%tmk未加好友%' or f.rule_name like '%tmk外呼3元%' or f.rule_name like '%外呼%' or f.rule_name like '%tmk外呼%' then 'TMK'
when f.rule_name like '%小红书%' then '小红书'
when f.rule_name like '%原子初三%' or f.rule_name like '%原子高一%' or f.rule_name like '%原子%' then '原子'
when f.rule_name like '%9KM%' then '9KM'
when f.rule_name like '%百度星耀数学%' or f.rule_name like '%数学%' or f.rule_name like '%百度星耀物理%' or f.rule_name like '%物理%' then '百度星耀'
else '未知' end as channel_map_1,
        case 
            when f.rule_name like '%高一%' then '高一'
            when f.rule_name like '%高二%' then '高二'
            when f.rule_name like '%高三%' then '高三'
            when f.rule_name like '%初二%' then '初二'
            when f.rule_name like '%初三%' then '初三'
            else f.lead_purchase_intention_level2_category_name 
        end as grade_1,
        date_diff('hour', cast(f.section_assign_time as timestamp), cast(f.first_call_time as timestamp)) as first_call_time_diff_hour,
        jt.first_call_connected_time_diff_hour as first_call_connected_time_diff_hour_1,
        case when f.valid_lead_count = '1' then f.friend_lead_count else 0 end as is_friend_lead,
        case when t.jieduan in ('深沟','已双沟') then 1 else 0 end as is_shengou,
        case when t.jieduan in ('已双沟') then 1 else 0 end as is_shuanggou,
	    case when (yc.abnormal_traffic is not null and yc.abnormal_traffic != '' and  t.sale_flow_stage_name_1 in ('新线索','已建联','未成交'))then 1 else 0 end as is_yichang
    from bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df f 
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
    ) t on f.user_id = t.user_number
    left join 
    (
        select 
            lead_id,
            section_assign_time, 
            section_assign_first_call_time,
            section_assign_first_call_connected_time,
            date_diff('hour', cast(section_assign_time as timestamp), cast(section_assign_first_call_connected_time as timestamp)) as first_call_connected_time_diff_hour
        from service_dw.dm_crm_lead_stats_detail_hf cd
        where dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd') 
            and hour = format_datetime(now() - interval '2' hour, 'HH')
            and mapping_first_level_department_name = 'H业务线'
            and mapping_second_level_department_name in ('精品班学部','菁英班学部','市场部','本地化大班学部')
    ) jt on f.lead_id = jt.lead_id
     ------------------------异常率
   left join (
	 select 
    abnormal_traffic,
    user_number
    from service_dw.app_user_attribute_label_gaia_wide_df
    where dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
    and type = 'key') yc on yc.user_number = f.user_id
    where f.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd') 
        and f.hour = format_datetime(now() - interval '3' hour, 'HH')    
        and f.section_assign_employee_first_level_department_name = 'H业务线'
        and f.section_assign_employee_second_level_department_name = '市场部'
        and f.period_mapping_first_level_department_name = 'H业务线'
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
---------------------------crm首call任务
,f_call0 as (
select 
	concat(substr(flow_order_period_name, 1, 4), substr(flow_order_period_name, 7, 4), '期') as period,
    assign_employee_email_name,
	account_id,
    user_id,
    count(distinct call_answer_lead_count) call_answer_lead_count--首call数
from service_dw.app_h_crm_lead_task_process_info_detail_hf t1
 where dt=format_datetime(NOW()-interval '2' hour,'YYYYMMdd') and hour=format_datetime(NOW()-interval '2' hour,'HH' )
 and period_create_time > '2025-12-01'
 and is_refund_before_clazz_begin = 0
 group by flow_order_period_name,assign_employee_email_name,account_id,user_id)		
------------------------首节到课数据		
,daoke as (
    select 
        dk.qici,
        dk.employee_email_prefix,
        dk.lead_id,
        dk.user_id,
        dk.channel_map_1,
	    dk.begin_time,
        dk.live_learn_duration,
	    dk.is_valid_live_learn,
	    ke.ke_1
    from (
        select distinct 
            t1.qici,
            t1.employee_email_prefix,
            t1.lead_id,
            t1.user_id,
            t1.channel_map_1,
            t1.grade_1,
            t2.live_learn_duration,
		    t2.is_valid_live_learn,
		    t2.begin_time
        from (
            select 
                lead_id,
                user_id,
                employee_email_prefix,
                qici,
                channel_map_1,
                grade_1
            from data 
            group by lead_id, user_id, employee_email_prefix, qici, channel_map_1, grade_1
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
                then date_format(date_add('day', -3, date_trunc('week', cast(begin_time as date))), '%Y%m%d') || '期'
            else date_format(date_add('day', 4, date_trunc('week', cast(begin_time as date))), '%Y%m%d') || '期'
        end
end as qici,
                mod(date_diff('day', cast('2021-02-01' as date), cast(begin_time as date)), 7) as dow,
                is_need_attend,
                live_learn_duration,
                is_valid_live_learn
            from service_dw.dws_service_user_learn_detail_hf  
            where dt = date_format(now() - interval '2' hour, '%Y%m%d') 
                and hour = date_format(now() - interval '2' hour, '%H')
                and course_first_level_department_name = 'H业务线'
                and course_second_level_department_name in ('精品班学部','市场部','青橙项目部')
                and is_need_attend = 1
        ) t2 on t1.qici = t2.qici and t1.user_id = t2.user_number) dk
	left join temp_table.dingxi01_daoke_1_6_t ke on dk.qici = ke.qici and dk.channel_map_1 = ke.qudao and dk.grade_1 = ke.grade  and dk.begin_time = ke.begin_time)
	
----线索维度：期次，渠道，年级，架构，
,prc as (select distinct
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
	case when data.first_call_time_diff_hour <= 6 and data.valid_lead_count > 0 then 1 else 0 end as first_call_in_6h,
	case when data.first_call_time_diff_hour <= 12 and data.valid_lead_count > 0 then 1 else 0 end as first_call_in_12h,
    case when data.first_call_time_diff_hour <= 24 and data.valid_lead_count > 0 then 1 else 0 end as first_call_in_24h,
    case when data.first_call_time_diff_hour <= 48 and data.valid_lead_count > 0 then 1 else 0 end as first_call_in_48h,
    case when data.first_call_time_diff_hour <= 168 and data.valid_lead_count > 0 then 1 else 0 end as first_call_cnt,
    case when data.first_call_connected_time_diff_hour_1 <= 24 and data.valid_lead_count > 0 then 1 else 0 end as first_call_connected_in_24h,
    case when data.first_call_connected_time_diff_hour_1 <= 48 and data.valid_lead_count > 0 then 1 else 0 end as first_call_connected_in_48h,
    case when data.first_call_connected_time_diff_hour_1 <= 168 and data.valid_lead_count > 0 then 1 else 0 end as first_call_connected_cnt,
    ROUND(COALESCE(call_c.call_duration_1, 0) / 60.00, 2) as call_duration,
    coalesce(call_c.zong_call_ci_1, 0) as zong_call_ci,
    coalesce(call_c.call_status_1, 0) as call_status,
    case when valid_lead_count >0 then coalesce(call_c.is_long_call, 0) else 0 end as is_long_call,
    coalesce(data.is_friend_lead, 0) as is_friend_lead,
    case when denglu_app.user_number is not null then denglu_app.is_app_denglu else 0 end as is_app_denglu,
    coalesce(data.is_shengou, 0) as is_shengou,
    coalesce(data.is_shuanggou, 0) as is_shuanggou,
	coalesce(data.is_yichang, 0) as is_yichang,
	coalesce(f_call0.call_answer_lead_count, 0) as is_f_call,
	case when  data.channel_map_1 = '曹忆IP99元' then 
	    case when sum(case when daoke.ke_1 = '3' and daoke.live_learn_duration > 0 then 1 else 0 end) > 0 then 1 else 0 end 
    else case when sum(case when daoke.ke_1 = '1' and daoke.live_learn_duration > 0 then 1 else 0 end) > 0 then 1 else 0 end
end as daoke1,
case when  data.channel_map_1 = '曹忆IP99元' then 
	    case when sum(case when daoke.ke_1 = '3' and daoke.is_valid_live_learn = '1' then 1 else 0 end) > 0 then 1 else 0 end 
    else case when sum(case when daoke.ke_1 = '1' and daoke.is_valid_live_learn = '1' then 1 else 0 end) > 0 then 1 else 0 end
end as v_daoke1
from data
left join temp_table.dingxi01_jiagou_db jg on data.employee_email_prefix = jg.employee_email_prefix and data.qici = jg.qici
left join call_c on call_c.user_number = data.user_id and call_c.section_assign_employee_email_prefix = data.employee_email_prefix
left join daoke on daoke.user_id = data.user_id and daoke.employee_email_prefix = data.employee_email_prefix and daoke.qici = data.qici and data.channel_map_1 = daoke.channel_map_1
left join denglu_app on denglu_app.user_number = data.user_id
left join f_call0 on f_call0.assign_employee_email_name = data.employee_email_name and f_call0.user_id = data.user_id 
where data.qici > '20260424期'
    and data.virtual_third_department_name = '市场顾问部'
	and jg.department is not null
	and data.channel_map_1 not in ('未知','线索复用','训练营','进校0元')
group by 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30)
----------------------汇总
,last_d as(
select 
    qici, channel_map_1, department, jingli, xiaozu,
  	 rate_6,
	 rate_12,
    rate_long_call,
    rate_shengou,
    rate_shuanggou,
  dense_rank() over (partition by qici, channel_map_1,department order by rate_6 asc) as rank_rate_6,
  dense_rank() over (partition by qici, channel_map_1,department order by rate_12 asc) as rank_rate_12,
  dense_rank() over (partition by qici, channel_map_1,department order by rate_long_call asc) as rank_rate_long_call,
  dense_rank() over (partition by qici, channel_map_1,department order by rate_shengou asc) as rank_rate_shengou,
  dense_rank() over (partition by qici, channel_map_1,department order by rate_shuanggou asc) as rank_rate_shuanggou
from (
    select 
        qici, channel_map_1, department, jingli, xiaozu,
        sum(lead_count) as lead_count,
        sum(valid_lead_count) as valid_lead_count,
coalesce(sum(first_call_in_6h) * 1.0000 / nullif(sum(valid_lead_count), 0), 0) as rate_6,
coalesce(sum(first_call_in_12h) * 1.0000 / nullif(sum(valid_lead_count), 0), 0) as rate_12,
coalesce(sum(is_long_call) * 1.0000 / nullif(sum(valid_lead_count), 0), 0) as rate_long_call,
coalesce(sum(is_shengou) * 1.0000 / nullif(sum(valid_lead_count), 0), 0) as rate_shengou,
coalesce(sum(is_shuanggou) * 1.0000 / nullif(sum(valid_lead_count), 0), 0) as rate_shuanggou
    from prc
    group by qici, channel_map_1, department, jingli, xiaozu
) t
order by qici, channel_map_1, rank_rate_6)
------------------排序计算
select 
     qici, 
    channel_map_1, 
    department,
    -- rate_6 最低的小组及数值
    array_join(array_agg(case when rank_rate_6 = 1 then xiaozu end), ',') as rate_6_top1_xiaozu,
    min(case when rank_rate_6 = 1 then rate_6 end) as rate_6_top1_value,
    min(case when rank_rate_6 = 1 then rate_6 end) - avg(rate_6) as rate_6_top1_diff,
    -- rate_12 最低的小组及数值
    array_join(array_agg(case when rank_rate_12 = 1 then xiaozu end), ',') as rate_12_top1_xiaozu,
    min(case when rank_rate_12 = 1 then rate_12 end) as rate_12_top1_value,
    min(case when rank_rate_12 = 1 then rate_12 end) - avg(rate_12) as rate_12_top1_diff,
    -- rate_long_call 最低的小组及数值
    array_join(array_agg(case when rank_rate_long_call = 1 then xiaozu end), ',') as rate_long_call_top1_xiaozu_list,
    min(case when rank_rate_long_call = 1 then rate_long_call end) as rate_long_call_top1_value,
    min(case when rank_rate_long_call = 1 then rate_long_call end) - avg(rate_long_call) as rate_long_call_top1_diff,
    -- rate_shengou 最低的小组及数值
    array_join(array_agg(case when rank_rate_shengou = 1 then xiaozu end), ',') as rate_shengou_top1_xiaozu_list,
    min(case when rank_rate_shengou = 1 then rate_shengou end) as rate_shengou_top1_value,
    min(case when rank_rate_shengou = 1 then rate_shengou end) - avg(rate_shengou) as rate_shengou_top1_diff,
    -- rate_shuanggou 最低的小组及数值
    array_join(array_agg(case when rank_rate_shuanggou = 1 then xiaozu end), ',') as rate_shuanggou_top1_xiaozu_list,
    min(case when rank_rate_shuanggou = 1 then rate_shuanggou end) as rate_shuanggou_top1_value,
    min(case when rank_rate_shuanggou = 1 then rate_shuanggou end) - avg(rate_shuanggou) as rate_shuanggou_top1_diff
from last_d
group by qici, channel_map_1, department
order by qici, channel_map_1, department
