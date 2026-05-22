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
from d_ap left join h_ap on d_ap.user_number = h_ap.user_number)
--------------------------------------基础数据	
,data as (
    select distinct 
        f.*,
concat(cast(date_format(date_add('day',4,date_trunc('week',date_add('day',-1,date_parse(replace(concat(f.group_period_year,f.group_period_term),'期',''),'%Y%m%d')))),'%Y%m%d')as varchar),'期') as qici
  ,case
when f.rule_name like '%亚飞99元西安直播%' then '亚飞99元西安直播'
when f.rule_name like '%koc测试5元%' then 'koc测试5元'
when f.rule_name like '%百度搜索%' then '百度搜索'
when f.rule_name like '%亚飞9元百度%'  then '亚飞9元百度'
when f.rule_name like '%孟亚飞ip0元B站%' or f.rule_name like '%B站孟亚飞then%' then 'B站孟亚飞'
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
case when (f.deep_communicate_method is not null and f.deep_communicate_method != '' and f.valid_lead_count = '1') then 1 else 0 end as yi_shuanggou,
  case when (yc.abnormal_traffic is not null and yc.abnormal_traffic != '' and  t.sale_flow_stage_name_1 in ('新线索','已建联','未成交'))then 1 else 0 end as is_yichang,
case when (sbb.send_double_table = '是' and f.valid_lead_count = '1') then 1 else 0 end as yi_huishou
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
-------双表发送
left join (
select *
from(
select send_double_table,user_id,flow_order_period_name,lead_update_time,trace_update_time,assign_time,
concat(date_format(date_add('day', 4, date_trunc('week', date_add('day', -1, cast(assign_time as timestamp)))), '%Y%m%d'), '期') as qici,assign_employee_email_name,virtual_department_name_2,virtual_department_name_3,employee_virtual_department_name,
ROW_NUMBER() OVER (PARTITION by user_id ,assign_employee_email_name order by trace_update_time desc) as rn
from service_dw.app_h_crm_lead_task_process_info_detail_hf
where dt=format_datetime(now()-interval '2' hour,'YYYYMMdd') 
	and hour=format_datetime(now()-interval '3' hour,'HH')
	and virtual_department_name_2 = 'H业务线'
	and virtual_department_name_3 = '市场部')
where rn = 1) sbb on   sbb.assign_employee_email_name = f.employee_email_name and sbb.user_id = f.user_id
where f.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd') 
        and f.hour = format_datetime(now() - interval '3' hour, 'HH')    
        and f.section_assign_employee_first_level_department_name = 'H业务线'
        and f.section_assign_employee_second_level_department_name = '市场部'
	    and f.section_assign_employee_third_level_department_name = '市场顾问部'
        and f.period_mapping_first_level_department_name = 'H业务线'
		and f.period_mapping_second_level_department_name in ('市场部','精品班学部'))

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
 where dt=format_datetime(NOW()-interval '2' hour,'YYYYMMdd') and hour=format_datetime(NOW()-interval '3' hour,'HH' )
 and period_create_time > '2026-01-01'
 and is_refund_before_clazz_begin = 0
 group by flow_order_period_name,assign_employee_email_name,account_id,user_id)		
------------------------首节到课数据		
,daoke as (
    select 
        qici,
        user_id,
        channel_map_1,
        -- 曹忆IP99元看第3节课是否到课，其他看第1节课是否到课
        max(case when channel_map_1 = '曹忆IP99元' then
            case when ke_1 = '3' and live_learn_duration > 0 then 1 else 0 end
        else
            case when ke_1 = '1' and live_learn_duration > 0 then 1 else 0 end
        end) as has_daoke,
        max(case when channel_map_1 = '曹忆IP99元' then
            case when ke_1 = '3' and is_valid_live_learn = '1' then 1 else 0 end
        else
            case when ke_1 = '1' and is_valid_live_learn = '1' then 1 else 0 end
        end) as has_v_daoke
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
                    when cast(begin_time as date) >= date '2026-02-25' and cast(begin_time as date) <= date '2026-03-02' then '20260227期'
                    when cast(begin_time as date) >= date '2026-02-17' and cast(begin_time as date) <= date '2026-02-24' then '20260220期'		
                    when cast(begin_time as date) >= date '2026-02-09' and cast(begin_time as date) <= date '2026-02-16' then '20260213期'
                    when cast(begin_time as date) >= date '2026-02-03' and cast(begin_time as date) <= date '2026-02-08' then '20260206期'
                    else 
                        case 
                            when day_of_week(cast(begin_time as date)) = 2 
                                then date_format(date_add('day', -3, date_trunc('week', cast(begin_time as date))), '%Y%m%d') || '期'
                            else date_format(date_add('day', 4, date_trunc('week', cast(begin_time as date))), '%Y%m%d') || '期'
                        end
                end as qici,
                is_need_attend,
                live_learn_duration,
                is_valid_live_learn
            from service_dw.dws_service_user_learn_detail_hf  
            where dt = date_format(now() - interval '2' hour, '%Y%m%d') 
                and hour = date_format(now() - interval '2' hour, '%H')
                and course_first_level_department_name = 'H业务线'
                and course_second_level_department_name in ('精品班学部','市场部','青橙项目部')
                and is_need_attend = 1
        ) t2 on t1.qici = t2.qici and t1.user_id = t2.user_number
        left join temp_table.dingxi01_daoke_1_6_t ke on t2.qici = ke.qici and t1.channel_map_1 = ke.qudao and t1.grade_1 = ke.grade and t2.begin_time = ke.begin_time
        where ke.ke_1 in ('1', '3')  -- 只关注第1节和第3节
    ) t
    group by qici, user_id, channel_map_1)
	
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
coalesce(data.yi_shuanggou, 0) as yi_shuanggou,
coalesce(data.is_yichang, 0) as is_yichang,
coalesce(data.yi_huishou, 0) as yi_huishou,
coalesce(f_call0.call_answer_lead_count, 0) as is_f_call,
concat(data.dt, ' ', data.hour) AS datt
from data
left join temp_table.dingxi01_jiagou_db jg on data.employee_email_prefix = jg.employee_email_prefix and data.qici = jg.qici
left join call_c on call_c.user_number = data.user_id and call_c.section_assign_employee_email_prefix = data.employee_email_prefix
left join denglu_app on denglu_app.user_number = data.user_id
left join f_call0 on f_call0.assign_employee_email_name = data.employee_email_name and f_call0.user_id = data.user_id 
where data.qici > '20260403期'
    and data.virtual_third_department_name = '市场顾问部'
	and jg.department is not null
	and data.channel_map_1 not in ('未知','线索复用','训练营','进校0元'))
----------------------汇总
select *
from (
	select  prc.qici,prc.rule_name,prc.channel_map_1,prc.grade_1,prc.department,prc.jingli,prc.xiaozu,prc.employee_email_name,prc.datt,
	sum(lead_count) as lead_count,sum(valid_lead_count) as valid_lead_count,sum(first_call_time_diff_hour) as first_call_time_diff_hour,
	sum(first_call_in_6h) as first_call_in_6h,sum(first_call_in_12h) as first_call_in_12h,
    sum(first_call_in_24h) as first_call_in_24h,sum(first_call_in_48h) as first_call_in_48h,sum(first_call_cnt) as first_call_cnt,
     sum(first_call_connected_in_24h) as first_call_connected_in_24h,sum(first_call_connected_in_48h) as first_call_connected_in_48h,
     sum(first_call_connected_cnt) as first_call_connected_cnt,sum(call_duration) as call_duration,sum(zong_call_ci) as zong_call_ci,
     sum(call_status) as call_status,sum(is_long_call) as is_long_call,sum(is_friend_lead) as is_friend_lead,
	sum(is_app_denglu) as is_app_denglu,sum( is_shengou) as is_shengou,sum(is_shuanggou) as is_shuanggou,sum(yi_shuanggou) as yi_shuanggou,sum(yi_huishou) as yi_huishou,
	sum(is_yichang) as is_yichang,sum(is_f_call) as is_f_call,
count(distinct case when duf.has_daoke = 1 then prc.user_id end) as daoke1,
count(distinct case when duf.has_v_daoke = 1 then prc.user_id end) as v_daoke1
from prc
left join daoke duf on prc.qici = duf.qici 
    and prc.user_id = duf.user_id
    and prc.channel_map_1 = duf.channel_map_1
group by prc.qici, prc.rule_name, prc.channel_map_1, prc.grade_1, prc.department, prc.jingli, prc.xiaozu, prc.employee_email_name, prc.datt) 
