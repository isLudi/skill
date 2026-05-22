-------------------业绩订单明细
with dd as (
select
id,order_number,substring(biz_number, 1, 10) AS sub_biz_number,pre_biz_number,clazz_name,user_id AS user_id1,pre_employee_id,
type,trade_status,trade_type,order_paid_time as paid_time,trade_time,real_price,transfer_price,price,email_prefix,
employee_email_name as name,talent_type_name ,city_name as city,department,biz_number,course_grade as grade_list,course_subject as subject,qici,leader_employee_email_name,
case course_term_id when 'C' then '春季' when 'X' then '夏季' when 'Q' then '秋季' when 'D' then '冬季' else '其他'
end as school_term_id,
note,course_first_level_department_name,course_second_level_department_name,course_top_level_department_name,
 case when trade_type = '正常订单' then
sum(case when trade_type = '正常订单' then price else 0 end) over (partition by employee_email_name, user_id, clazz_name, trade_status)
        when trade_type = '调课调班' then
sum(case when trade_type = '调课调班' then price else 0 end) over (partition by employee_email_name, user_id)
            else 0 end as zong_price 
 from 
	(select *,
        case 
			when substr(trade_time, 1, 10) >= '2026-02-25' and substr(trade_time, 1, 10) <= '2026-03-02' then '20260227期'
			when substr(trade_time, 1, 10) >= '2026-02-17' and substr(trade_time, 1, 10) <= '2026-02-24' then '20260220期'
			when substr(trade_time, 1, 10) >= '2026-02-09' and substr(trade_time, 1, 10) <= '2026-02-16' then '20260213期'
			when substr(trade_time, 1, 10) >= '2026-02-03' and substr(trade_time, 1, 10) <= '2026-02-08' then '20260206期'
			when substr(trade_time, 1, 10) >= '2026-01-27' and substr(trade_time, 1, 10) <= '2026-02-02' then '20260130期'
			when substr(trade_time, 1, 10) >= '2026-01-20' and substr(trade_time, 1, 10) <= '2026-01-26' then '20260123期'
		else case when day_of_week(cast(trade_time as timestamp)) = 1 
           then concat(date_format(date_add('day', -3, date_trunc('week', cast(trade_time as timestamp))),'%Y%m%d'),'期')
           else concat(date_format(date_add('day', 4, date_trunc('week', cast(trade_time as timestamp))), '%Y%m%d'),'期')
        end 
end as qici
    from finance_dw.app_finance_performance_extend_details_hf 
    where dt = FORMAT_DATETIME(NOW() - INTERVAL '2' HOUR,'YYYYMMdd')
        and hour = FORMAT_DATETIME(NOW() - INTERVAL '2' HOUR,'HH')
        and employee_first_level_department_name = 'H业务线'
	    and employee_second_level_department_name = '市场部'
        and employee_third_level_department_name = '市场顾问部'
        and price <> 0) d
    where d.qici > '20260206期'
)
,ranked_dd as (select distinct
id, order_number, sub_biz_number, pre_biz_number, clazz_name, user_id1, pre_employee_id, type, trade_status, trade_type, paid_time,          trade_time, real_price, transfer_price, price, email_prefix, name, talent_type_name, city, biz_number, grade_list, subject, school_term_id,  
case when course_second_level_department_name like '%精品班学部%' then '大班'
when course_second_level_department_name like '%菁英班学部%' then '小班'
when course_second_level_department_name like '%一对一学部%' then '一对一'
when course_second_level_department_name like '%本地化学部%' then '本地化'
when course_second_level_department_name like '%清北班学部%' then '清北'
else '其他'  end as course_name,
leader_employee_email_name,
round(zong_price, 2) as zong_price,qici,
round(case when trade_type = '调课调班' then sum(case when trade_type = '调课调班' then zong_price else 0 end) over (partition by name)
else zong_price end,2) as zong_price0,
row_number() over (partition by case when trade_type = '正常订单' then clazz_name end, user_id1 ,case when trade_type = '正常订单' then trade_status end order by clazz_name desc ) as dup_rn
from dd
where  (zong_price > 5 or zong_price < 0) and  zong_price <> 0)
-----汇总订单明细
,rd as (select *
from ranked_dd
where dup_rn = 1 and zong_price <> 0 and zong_price0 <>0)
------依据期次获取最新uid
,n_uid as (
select aa.*,row_number() over (partition by original_order_user_number order by qici desc) as rn
from (select lead_id,original_order_user_number,performance_employee_email_name,concat(cast(date_format(date_add('day',4,date_trunc('week',date_add('day',-1,date_parse(replace(concat(trade_group_period_year,trade_group_period_term),'期',''),'%Y%m%d')))),'%Y%m%d')as varchar),'期') qici
from service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf 
where dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
        and hour = format_datetime(now() - interval '2' hour, 'HH')
        and course_first_level_department_name = 'H业务线'
        and course_second_level_department_name IN ('精品班学部','菁英班学部','市场部','本地化大班学部','一对一学部','青橙项目部')
        and performance_third_level_department_name = '市场顾问部'
	    )aa)
-------获取lead_id
,lead_gmv as (
select 
rd.*,
n_uid.lead_id
from rd
left join n_uid
on rd.user_id1 = n_uid.original_order_user_number and rd.name = n_uid.performance_employee_email_name 
where n_uid.rn =1)
-----关联分配规则表
,rule as (select 
lead_gmv.*,
rr.rule_name,
case
when rr.rule_name like '%线索复用%'  then '线索复用' 
when rr.rule_name like '%朱汉祺ip9元%'  then '朱汉祺ip9元' 
when rr.rule_name like '%APP%' then 'APP'
when rr.rule_name like '%曹忆IP%' or rr.rule_name like '%曹忆ip%'then '曹忆IP'
when rr.rule_name like '%孟亚飞IP%'or rr.rule_name like '%孟亚飞ip%' then '孟亚飞IP'
when rr.rule_name like '%图书KOC%' then '图书KOC'
when rr.rule_name like '%朱汉祺IP%' then '朱汉祺IP'
when rr.rule_name like '%西安图书%' then '西安图书'
when rr.rule_name like '%常规KOC%' then '常规KOC'
when rr.rule_name like '%进校%' then '进校0元'
when rr.rule_name like '%春春B站99元%' then '春春B站99元'
when rr.rule_name like '%肖晗ip19元%' or rr.rule_name like '%ip肖晗19元%' then '肖晗ip19元'
when rr.rule_name like '%koc肖晗5元%' then 'koc肖晗5元' 
when rr.rule_name like '%koc自孵化5元%' or rr.rule_name like '%koc广州本地化5元%' or rr.rule_name like '%koc常规5元%'  then 'koc5元' 
when rr.rule_name like '%koc朱汉祺5元%'  then 'koc朱汉祺5元' 
when rr.rule_name like '%朱汉祺ip29元%' or rr.rule_name like '%朱汉祺退费0元%' then '朱汉祺ip29元'	
when rr.rule_name like '%koc朱汉祺29元%' or rr.rule_name like '%koc周帅29元%' or rr.rule_name like '%周帅29元%' or rr.rule_name like '%朱汉祺29元%' 
or rr.rule_name like '%朱汉祺koc29元%'	then 'koc29元' 
when rr.rule_name like '%B站高中%'  then 'B站' 
when rr.rule_name like '%B站朱汉祺29元%' or rr.rule_name like '%B站周帅19元%' then 'B站29元' 
when rr.rule_name like '%春春ip99元%'  or rr.rule_name like '%春春退费0元%' then '春春ip99元'
when rr.rule_name like '%私域0元%' or rr.rule_name like '%表单高中%' or rr.rule_name like '%私域表单0元%'  then '私域0元' 
when rr.rule_name like '%私域9元%'  then '私域9元' 
when rr.rule_name like '%拓展koc%' or rr.rule_name like '%拓展ip%' or rr.rule_name like '%koc外部发货%' or rr.rule_name like '%多学科拓展%' then '多学科拓展'
when rr.rule_name like '%商务书商1元%' or rr.rule_name like '%商务1元%' or rr.rule_name like '%商务进校18元%' or rr.rule_name like '%商务TMK9元%' or rr.rule_name like '%商务%' then '商务'
when rr.rule_name like '%训练营%' or rr.rule_name like '%CRM特殊链接分配策略%' then '训练营' 
when rr.rule_name like '%信息流%' then '信息流'
when rr.rule_name like '%tmk未加好友%' or rr.rule_name like '%tmk外呼3元%' or rr.rule_name like '%外呼%' or rr.rule_name like '%tmk外呼%'  then 'TMK'
when rr.rule_name like '%小红书%' then '小红书'
when rr.rule_name like '%原子初三%' or rr.rule_name like '%原子高一%' or rr.rule_name like '%原子%'  then '原子'
when rr.rule_name like '%汐子ip%' or rr.rule_name like '%ip百度%' or rr.rule_name like '%ip抖音%' or rr.rule_name like '%ip视频号%' or rr.rule_name like '%ip小红书%' or rr.rule_name like '%ip峥峥%' or rr.rule_name like '%ip快手%' or rr.rule_name like '%汤雪健ip%' or rr.rule_name like '%峥峥ip%' or rr.rule_name like '%ip299%'  or rr.rule_name like '%百度%' or rr.rule_name like '%抖音%' or rr.rule_name like '%视频号%' then 'ip'
when rr.rule_name like '%9KM%' then '9KM'
when rr.rule_name like '%百度星耀数学%' or rr.rule_name like '%数学%' or rr.rule_name like '%百度星耀物理%' or rr.rule_name like '%物理%'then '百度星耀'
else '未知' end as channel_1,
case 
        -- 如果月份 >= 6，年份为2025
        when cast(substr(rr.group_period_term, 1, 2) as int) >= 6 
        then date_format(date_add('day', 5 - day_of_week(date_parse('2025' || rr.group_period_term, '%Y%m%d')),date_parse('2025' || rr.group_period_term, '%Y%m%d')), '%Y%m%d') || '期'
        -- 其他月份，年份为2026
        else date_format(date_add('day', 5 - day_of_week(date_parse('2026' || rr.group_period_term, '%Y%m%d')),date_parse('2026' || rr.group_period_term, '%Y%m%d')), '%Y%m%d') || '期'
    end as friday_period
from lead_gmv
left join (
	select *,case 
        when regexp_like(substr(rule_name, 1, 4), '^[0-9]{4}$')  -- 判断前4位是否都是数字
        then substr(rule_name, 1, 4)  else null 
    end as group_period_term
	from service_dw.dim_crm_assign_rule_lead_detail_hf
	where dt = format_datetime(NOW() - interval '2' hour, 'YYYYMMdd') 
    and hour = format_datetime(NOW() - interval '2' hour, 'HH') 
	)rr on lead_gmv.lead_id = rr.lead_id and lead_gmv.email_prefix = rr.account_domain )
-------------14天内、30天内出单打标签	
,base as (
select rule.*,zx.xiaozu,zx.jingli,
    case when date_parse(substr(friday_period, 1, 8), '%Y%m%d') = date_parse(substr(qici, 1, 8), '%Y%m%d')then 0 
	when date_diff('week', date_parse(substr(friday_period, 1, 8), '%Y%m%d'),date_parse(substr(qici, 1, 8), '%Y%m%d')) = 1 then 1
    when date_diff('week', date_parse(substr(friday_period, 1, 8), '%Y%m%d'),date_parse(substr(qici, 1, 8), '%Y%m%d')) in (2,3) then 2
    else 3 end as week_diff
from rule
left join temp_table.dingxi01_jiagou_zx zx on zx.employee_email_name = rule.name)
------------------------ 按渠道、年级等维度统计每个用户购买的科目数量
,user_subject as (
    select 
        qici,
        name,
        channel_1,
        jingli,
        xiaozu,
        grade_list,
        user_id1,
        count(distinct subject) as subject_count,
        sum(case when zong_price < 0 then abs(zong_price) else 0 end) as refund_amount,
        sum(case when zong_price > 0 then zong_price else 0 end) as income_amount
    from base
    where zong_price <> 0
    group by qici, name, channel_1, jingli, xiaozu, grade_list, user_id1
)
----------------聚合到人
select 
        qici,
        name,
        channel_1,
        jingli,
        xiaozu,
        grade_list,
	sum(case when subject_count = 1 then refund_amount else 0 end) as refund_1,
	sum(case when subject_count between 2 and 3 then refund_amount else 0 end) as refund_2,
	sum(case when subject_count > 3 then refund_amount else 0 end) as refund_3,
        -- 用户数
     count(distinct user_id1) as user_count,
        -- 退款金额
     sum(refund_amount) as total_refund,
        -- 总收款
     sum(income_amount) as total_income
    from user_subject
    group by qici, name, channel_1, jingli, xiaozu, grade_list