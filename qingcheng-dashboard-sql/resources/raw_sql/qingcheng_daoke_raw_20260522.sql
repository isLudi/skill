with data as (
select distinct 
        f.*,
concat(cast(date_format(date_add('day',4,date_trunc('week',date_add('day',-1,date_parse(replace(concat(f.group_period_year,f.group_period_term),'期',''),'%Y%m%d')))),'%Y%m%d')as varchar),'期') as qici
,case 
when f.rule_name like '%私域%' then '青橙私域'
when f.rule_name like '%青橙IP%' then '青橙IP'
when f.rule_name like '%青橙公海%' then '青橙公海'
when f.rule_name like '%青橙图书%' then '青橙图书'
when f.rule_name like '%青橙公域%' then '青橙公域'
when f.rule_name like '%进校%' then '进校'
end as channel_map_1
  ,case 
when f.rule_name like '%私域会话%' then '私域会话'
when f.rule_name like '%私域表单%' then '私域表单'
when f.rule_name like '%私域图书%' then '私域图书'
when f.rule_name like '%私域裂变%' then '私域裂变'
when f.rule_name like '%私域品效%' then '私域品效'
when f.rule_name like '%亚飞IP%' then '亚飞IP'
when f.rule_name like '%SEC未加好友%' then 'SEC未加好友'
when f.rule_name like '%SEC首期掉海%' then 'SEC首期掉海'
when f.rule_name like '%顾问未加好友%' then '顾问未加好友'
when f.rule_name like '%武汉图书%' then '武汉图书'
when f.rule_name like '%西安图书%' then '西安图书'
when f.rule_name like '%公域学霸%' then '公域学霸'
when f.rule_name like '%进校9元%' then '进校9元'
end as channel_map_2
,case 
when f.rule_name like '%高一%' then '高一'
when f.rule_name like '%高二%' then '高二'
when f.rule_name like '%高三%' then '高三'
when f.rule_name like '%初二%' then '初二'
when f.rule_name like '%初三%' then '初三'
else '未知' end as grade_1
    from bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df f 
    where f.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd') 
        and f.hour = format_datetime(now() - interval '3' hour, 'HH')    
        and f.section_assign_employee_first_level_department_name = 'H业务线'
        and f.section_assign_employee_second_level_department_name = '青橙项目部'
        and f.period_mapping_first_level_department_name in ('H业务线')
        and f.period_mapping_second_level_department_name in ('精品班学部','青橙项目部') 
        and f.valid_lead_count = '1'
),
daoke as (
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
select distinct 
data.qici, data.channel_map_1,data.channel_map_2,data.grade_1, jg.xiaozu, jg.department, jg.dept_2,
coalesce(data.valid_lead_count,0)lead,data.employee_email_prefix,data.employee_email_name,data.user_id,
case when sum(case when daoke.ke_1 = '1' and daoke.live_learn_duration > 0 then 1 else 0 end) > 0 then 1 else 0 end as ke_1,
case when sum(case when daoke.ke_1 = '2' and daoke.live_learn_duration > 0 then 1 else 0 end) > 0 then 1 else 0 end as ke_2,
case when sum(case when daoke.ke_1 = '3' and daoke.live_learn_duration > 0 then 1 else 0 end) > 0 then 1 else 0 end as ke_3,
case when sum(case when daoke.ke_1 = '4' and daoke.live_learn_duration > 0 then 1 else 0 end) > 0 then 1 else 0 end as ke_4,
case when sum(case when daoke.ke_1 = '5' and daoke.live_learn_duration > 0 then 1 else 0 end) > 0 then 1 else 0 end as ke_5,
case when sum(case when daoke.ke_1 = '6' and daoke.live_learn_duration > 0 then 1 else 0 end) > 0 then 1 else 0 end as ke_6,
case when sum(case when daoke.ke_1 = '1' and daoke.is_valid_live_learn = '1' then 1 else 0 end) > 0 then 1 else 0 end as v_ke_1,
case when sum(case when daoke.ke_1 = '2' and daoke.is_valid_live_learn = '1' then 1 else 0 end) > 0 then 1 else 0 end as v_ke_2,
case when sum(case when daoke.ke_1 = '3' and daoke.is_valid_live_learn = '1' then 1 else 0 end) > 0 then 1 else 0 end as v_ke_3,
case when sum(case when daoke.ke_1 = '4' and daoke.is_valid_live_learn = '1' then 1 else 0 end) > 0 then 1 else 0 end as v_ke_4,
case when sum(case when daoke.ke_1 = '5' and daoke.is_valid_live_learn = '1' then 1 else 0 end) > 0 then 1 else 0 end as v_ke_5,
case when sum(case when daoke.ke_1 = '6' and daoke.is_valid_live_learn = '1' then 1 else 0 end) > 0 then 1 else 0 end as v_ke_6
from data
left join daoke on data.employee_email_prefix = daoke.employee_email_prefix and data.qici = daoke.qici and data.lead_id = daoke.lead_id
left join temp_table.dingxi01_jiagou_db jg on data.employee_email_prefix = jg.employee_email_prefix and data.qici = jg.qici
where data.qici > '20260501期'
and jg.department is not null
and data.channel_map_1 is not null
and data.channel_map_2 is not null
group by 1,2,3,4,5,6,7,8,9,10,11
