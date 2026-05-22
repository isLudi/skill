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
---------------------------------------------------基础数据	
,data as (
select distinct 
f.*
,concat(cast(date_format(date_add('day',4,date_trunc('week',date_add('day',-1,date_parse(replace(concat(group_period_year,group_period_term),'期',''),'%Y%m%d')))),'%Y%m%d')as varchar),'期') qici
,substr(f.section_assign_time, 1, 10) as assign_day
,case 
when f.rule_name like '%私域%' then '青橙私域'
when f.rule_name like '%青橙IP%' then '青橙IP'
when f.rule_name like '%青橙公海%' then '青橙公海'
when f.rule_name like '%青橙公域%' then '青橙公域'
when f.rule_name like '%青橙图书%' then '青橙图书'
when f.rule_name like '%青橙本地化%' then '青橙本地化'
when f.rule_name like '%抖音私信%' then '抖音私信'
when f.rule_name like '%进校%' then '进校'
when f.rule_name like '%训练营%' then '青橙训练营'
end as channel_map_1
,case 
when f.rule_name like '%私域表单%' then '私域表单'
when f.rule_name like '%私域图书%' then '私域图书'
when f.rule_name like '%私域裂变%' then '私域裂变'
when f.rule_name like '%私域品效%' then '私域品效'
when f.rule_name like '%私域IE%' then '私域IE'
when f.rule_name like '%私域本地化%' then '私域本地化'
when f.rule_name like '%亚飞IP%' then '亚飞IP'
when f.rule_name like '%SEC未加好友%' then 'SEC未加好友'
when f.rule_name like '%SEC首期掉海%' then 'SEC首期掉海'
when f.rule_name like '%顾问未加好友%' then '顾问未加好友'
when f.rule_name like '%郑州图书%' then '郑州图书'
when f.rule_name like '%武汉图书%' then '武汉图书'
when f.rule_name like '%西安图书%' then '西安图书'
when f.rule_name like '%图书咨询%' then '图书咨询'
when f.rule_name like '%公域学霸%' then '公域学霸'
when f.rule_name like '%南京%' then '南京'
when f.rule_name like '%抖音私信%' then '抖音私信'
when f.rule_name like '%进校9元%' then '进校9元'
when f.rule_name like '%训练营%' then '青橙训练营'
end as channel_map_2
,case 
when f.rule_name like '%高一%' then '高一'
when f.rule_name like '%高二%' then '高二'
when f.rule_name like '%高三%' then '高三'
when f.rule_name like '%初二%' then '初二'
when f.rule_name like '%初三%' then '初三'
else f.lead_purchase_intention_level2_category_name end as grade_1
,date_diff('hour', cast(f.section_assign_time as timestamp), cast(f.first_call_time as timestamp)) as first_call_time_diff_hour--首次触达时间差
,jt.first_call_connected_time_diff_hour as first_call_connected_time_diff_hour_1--首次接通时间差
,case when f.valid_lead_count = '1' then 1 else 0  end as v_lead
,case when f.valid_lead_count = '1' then f.friend_lead_count else 0 end as is_friend_lead
from
bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df f 
left join 
(select 
lead_id,
section_assign_time, 
section_assign_first_call_time,
section_assign_first_call_connected_time,
date_diff('hour', CAST(section_assign_time AS timestamp), CAST(section_assign_first_call_connected_time AS timestamp)) AS first_call_connected_time_diff_hour---首次外呼接通和分配时间差
from service_dw.dm_crm_lead_stats_detail_hf 
where dt=format_datetime(NOW()-interval '2' hour,'YYYYMMdd') 
and hour=format_datetime(NOW()-interval '2' hour,'HH')
and mapping_first_level_department_name='H业务线'
and mapping_second_level_department_name in ('精品班学部','菁英班学部','市场部','本地化大班学部','青橙项目部')) jt
on f.lead_id = jt.lead_id 
where f.dt=format_datetime(NOW()-interval '2' hour,'YYYYMMdd') 
	and f.hour=format_datetime(NOW()-interval '3' hour,'HH')    
	and f.section_assign_employee_first_level_department_name = 'H业务线'
    and f.section_assign_employee_second_level_department_name = '青橙项目部'
    and f.period_mapping_first_level_department_name = 'H业务线'
    and f.period_mapping_second_level_department_name in ('精品班学部','青橙项目部') 
	and f.valid_lead_count = '1' )
--------------------------------------外呼接通比例
,call_c as (
    select 
        sub.user_number as user_number,
        sub.lead_id,
        sub.section_assign_employee_email_prefix,
        max(case when sub.call_duration > 480 then 1 else 0 end) as is_long_call,
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
------------------------首节到课数据		
,daoke as (
    select 
        dk.qici,
        dk.employee_email_prefix,
        dk.lead_id,
        dk.user_id,
        dk.channel_map_1,
	    dk.channel_map_2,
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
		    t1.channel_map_2,
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
			    channel_map_2,
                grade_1
            from data 
            group by lead_id, user_id, employee_email_prefix, qici, channel_map_1, channel_map_2,grade_1
        ) t1
        left join (
            select 
                user_number,
                begin_time,
                substr(begin_time, 12, 5) as ke_time,
			case when day_of_week(cast(begin_time as timestamp)) = 1 
                   then concat(date_format(date_add('day', -3, date_trunc('week', cast(begin_time as timestamp))),'%Y%m%d'),'期')
                   else concat(date_format(date_add('day', 4, date_trunc('week', cast(begin_time as timestamp))), '%Y%m%d'),'期')
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
	left join temp_table.dingxi01_qing_daoke ke on dk.qici = ke.qici and dk.channel_map_2= ke.qudao and dk.grade_1 = ke.grade and dk.begin_time = ke.begin_time
)
----线索维度：期次，渠道，年级，架构，
,prc as (select distinct
data.qici
,data.rule_name
,data.assign_day
,data.channel_map_1
,data.channel_map_2
,data.grade_1
,jg.department
,jg.dept_2
,jg.xiaozu
,data.employee_email_name
,data.user_id
,data.v_lead---同一用户下有不同学部顾问，则无此线索
,coalesce(data.is_friend_lead,0) is_friend_lead
,coalesce(data.first_call_time_diff_hour,0) first_call_time_diff_hour
, case when data.first_call_time_diff_hour>=0 and data.first_call_time_diff_hour<=24 and data.valid_lead_count>0 then 1 else 0 end  first_call_in_24h----24h触达
, case when data.first_call_time_diff_hour>=0 and data.first_call_time_diff_hour<=48 and data.valid_lead_count>0 then 1 else 0 end  first_call_in_48h----48h触达
, case when data.first_call_time_diff_hour>=0 and data.first_call_time_diff_hour <=168 and data.valid_lead_count>0 then 1 else 0 end first_call_cnt----触达
, case when data.first_call_connected_time_diff_hour_1>=0 and data.first_call_connected_time_diff_hour_1<=24 and data.valid_lead_count>0 then 1 else 0 end first_call_connected_in_24h----24h沟通
, case when data.first_call_connected_time_diff_hour_1>=0 and data.first_call_connected_time_diff_hour_1<=48 and data.valid_lead_count>0 then 1 else 0 end first_call_connected_in_48h----48h沟通
, case when data.first_call_connected_time_diff_hour_1>=0 and data.first_call_connected_time_diff_hour_1<=168 and data.valid_lead_count>0 then 1 else 0 end first_call_connected_cnt----沟通
, coalesce(call_c.call_duration_1,0)/60.00 as call_duration--总通时
, coalesce(call_c.is_long_call,0) as is_long_call
, coalesce(call_c.zong_call_ci_1,0) zong_call_ci--外呼次数
, coalesce(call_c.call_status_1,0) call_status--外呼接通次数
, case when denglu_app.user_number is not null then denglu_app.is_app_denglu else 0 end as is_app_denglu
,case when sum(case when daoke.ke_1 = '1' and daoke.live_learn_duration > 0 then 1 else 0 end) > 0 then 1 else 0 end as daoke1
,case when sum(case when daoke.ke_1 = '1' and daoke.is_valid_live_learn = '1' then 1 else 0 end) > 0 then 1 else 0 end as valid_daoke_1
from data
left join  temp_table.dingxi01_jiagou_db jg on  data.employee_email_name = jg.employee_email_name and data.qici = jg.qici
left join daoke on data.employee_email_prefix = daoke.employee_email_prefix and data.qici = daoke.qici and data.lead_id = daoke.lead_id
left join call_c on  call_c.user_number = data.user_id and call_c.section_assign_employee_email_prefix = data.employee_email_prefix
left join denglu_app on denglu_app.user_number = data.user_id
where data.qici >= '20260501期'
and data.virtual_second_department_name = '青橙项目部'
and jg.department is not null
and data.channel_map_1 is not null
and data.channel_map_2 is not null
group by 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25)
-----------------------剔除线索量<2
select *
from(select 
qici,rule_name,assign_day,channel_map_1,channel_map_2,grade_1,department,dept_2,xiaozu,employee_email_name
,sum(v_lead) as v_lead,sum(is_friend_lead) as is_friend_lead,sum(first_call_time_diff_hour) as first_call_time_diff_hour
,sum(first_call_in_24h) as first_call_in_24h,sum(first_call_in_48h) as first_call_in_48h
,sum(first_call_cnt) as first_call_cnt,sum(first_call_connected_in_24h) as first_call_connected_in_24h
,sum(first_call_connected_in_48h) as first_call_connected_in_48h
,sum(first_call_connected_cnt) as first_call_connected_cnt
,sum(call_duration) as call_duration,sum(is_long_call) as is_long_call ,sum(zong_call_ci) as zong_call_ci
,sum(call_status) as call_status,sum(is_app_denglu) as is_app_denglu,sum(daoke1) as daoke1,sum(valid_daoke_1) as valid_daoke_1
from prc 
group by qici,rule_name,assign_day,channel_map_1,channel_map_2,grade_1,department,dept_2,xiaozu,employee_email_name)
