with dd as (select *
from (
    select
        id, order_number, 
        substring(biz_number, 1, 10) AS sub_biz_number,
        pre_biz_number, clazz_name, user_id AS user_id1,
        pre_employee_id, type, trade_status, trade_type,
        order_paid_time as paid_time, trade_time,
        case 
            when trade_status in ('全部退款','部分退款') then -real_price 
            else real_price 
        end as real_price_0,
        transfer_price, price, email_prefix,
        employee_email_name as name,
        talent_type_name, city_name as city, department,
        biz_number, course_grade as grade_list,
        course_subject as subject,
	 case
    when cast(trade_time as date)
        between date '2026-07-14' and date '2026-07-19'
    then '20260716期'
    when cast(trade_time as date)
        between date '2026-07-20' and date '2026-07-25'
    then '20260722期'
    when cast(trade_time as date)
        between date '2026-07-26' and date '2026-07-31'
    then '20260728期'
    when cast(trade_time as date)
        between date '2026-08-01' and date '2026-08-06'
    then '20260803期'
    when cast(trade_time as date)
        between date '2026-08-07' and date '2026-08-12'
    then '20260808期'
    when cast(trade_time as date)
        between date '2026-08-13' and date '2026-08-18'
    then '20260815期'
    else concat(
        date_format(
            date_trunc('week', cast(trade_time as date)) + interval '4' day,
            '%Y%m%d'
        ),
        '期'
    )
end as qici,
        leader_employee_email_name, teacher_name,
        case course_term_id 
            when 'C' then '春季' 
            when 'X' then '夏季' 
            when 'Q' then '秋季' 
            when 'D' then '冬季' 
            else '其他'
        end as school_term_id,
        note, course_first_level_department_name,
        course_second_level_department_name,
        course_top_level_department_name
    from finance_dw.app_finance_performance_extend_details_hf 
    where dt = FORMAT_DATETIME(NOW() - INTERVAL '2' HOUR, 'YYYYMMdd')
        and hour = FORMAT_DATETIME(NOW() - INTERVAL '2' HOUR, 'HH')
        and employee_first_level_department_name = 'H业务线'
	    and employee_second_level_department_name = '市场部'
        and employee_third_level_department_name = '市场顾问部')
		where qici > '20260424期'
)
-- 调课调班（按name和user_id1去重，每个用户保留一条记录）
,gmv_t as (
    select 
        id, order_number, clazz_name, user_id1, trade_status, trade_time,  -- 这里加了逗号
        trade_type, email_prefix, name, grade_list, subject, 
        qici, school_term_id, teacher_name,
        course_first_level_department_name,
        course_second_level_department_name,
        name_total_price
    from (
        select 
            *,row_number() over (partition by name, user_id1 order by id) as dup_rn
        from (
            select 
                *,round(sum(price) over (partition by name, user_id1), 3) as name_total_price
            from dd 
            where trade_type = '调课调班'
        ) t1
        where name_total_price != 0
    ) t2
    where dup_rn = 1
)
-- 正常订单
,gmv_z as (
    select 
        id, order_number, clazz_name, user_id1, trade_status, trade_time,  -- 这里加了逗号
        trade_type, email_prefix, name, grade_list, subject,
        qici, school_term_id, teacher_name,
        course_first_level_department_name,
        course_second_level_department_name,
        sum(price) as name_total_price
    from dd
    where trade_type = '正常订单'
    group by id, order_number, clazz_name, user_id1, trade_status, trade_time,  -- 这里加了逗号
             trade_type, email_prefix, name, grade_list, subject,
             qici, school_term_id, teacher_name,
             course_first_level_department_name,
             course_second_level_department_name
)
-- --------------------------------------------整合流水结果
,rd as (
    select 
        id, order_number, clazz_name, user_id1, trade_status, trade_time,
        trade_type, email_prefix, name, grade_list, subject, 
        qici, school_term_id, teacher_name,
        course_first_level_department_name,
        course_second_level_department_name,
        name_total_price
    from gmv_z
    union all
    select 
        id, order_number, clazz_name, user_id1, trade_status, trade_time,
        trade_type, email_prefix, name, grade_list, subject, 
        qici, school_term_id, teacher_name,
        course_first_level_department_name,
        course_second_level_department_name,
        name_total_price
    from gmv_t
)
------依据期次获取最新uid
,n_uid as (
select aa.*,row_number() over (partition by original_order_user_number, performance_employee_email_name order by qici desc nulls last, lead_id desc nulls last) as rn
from (select lead_id,original_order_user_number,performance_employee_email_name,case
    when cast(date_parse(replace(concat(trade_group_period_year,trade_group_period_term),'期',''),'%Y%m%d') as date)
        between date '2026-07-14' and date '2026-07-19'
    then '20260716期'
    when cast(date_parse(replace(concat(trade_group_period_year,trade_group_period_term),'期',''),'%Y%m%d') as date)
        between date '2026-07-20' and date '2026-07-25'
    then '20260722期'
    when cast(date_parse(replace(concat(trade_group_period_year,trade_group_period_term),'期',''),'%Y%m%d') as date)
        between date '2026-07-26' and date '2026-07-31'
    then '20260728期'
    when cast(date_parse(replace(concat(trade_group_period_year,trade_group_period_term),'期',''),'%Y%m%d') as date)
        between date '2026-08-01' and date '2026-08-06'
    then '20260803期'
    when cast(date_parse(replace(concat(trade_group_period_year,trade_group_period_term),'期',''),'%Y%m%d') as date)
        between date '2026-08-07' and date '2026-08-12'
    then '20260808期'
    when cast(date_parse(replace(concat(trade_group_period_year,trade_group_period_term),'期',''),'%Y%m%d') as date)
        between date '2026-08-13' and date '2026-08-18'
    then '20260815期'
    else concat(
        date_format(
            date_trunc('week', cast(date_parse(replace(concat(trade_group_period_year,trade_group_period_term),'期',''),'%Y%m%d') as date)) + interval '4' day,
            '%Y%m%d'
        ),
        '期'
    )
end qici
from service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf 
where dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
        and hour = format_datetime(now() - interval '2' hour, 'HH')
and course_first_level_department_name in ('H业务线','A业务线','EM业务线','LL业务线','TT','TUTU','TT业务线')
and course_second_level_department_name in ('V项目部','本地化部','私域营销组','青少成长学部','创新技术组','成长中心供应链组','APP运营组','英语产品部','职场服务部','用户平台部','微师产品部','上海中心综合部','CAL技术组','财务核算部','财经项目部','人才发展部','财务信息化部','图书项目部（关闭）','运营部','基础架构组','数学产品部','营销产品部','雅思学部','商品部','磨课组','升学规划部','郑州中心','组织部','留学申请学部','质检部','架构平台部','师训组','投放商务组','系统班部','编程素养学部','市场运营组','项目运营组','KM技术组','二讲老师部','成都中心综合部','业务设计部','专题课部','微师职教产品部','高校学部','教学服务部','平台产品部','数字化学部','品牌运营组','校长办公室','运营中心财务','视效部','数据与商业分析中心','X项目','教学产品部','XA学部','语言学部','图书产品部','主播部','业务支持部','HL技术组','武汉中心综合部','成人供应链组','途途课堂','信息平台部','HL经营分析组','大数据部','直播运营组','市场部','金刚产品部','教学产品运营中心','平台电商组','企业效能部','品牌与内容部','产品研发部','小学部','技术质量部','财务报告部','税务部','用户产品部','直播二部','招聘部','HR共享中心','清北','增长策略部','督察部','商品运营部','资金管理部','美好家庭学部','设计支持中心','初中部','AIGC创新部','财务部','人力资源部','人才保障部一部','CAL经营分析组','基础技术部','综合素养学部','热线呼入部','品牌部','语文产品部','供应链部','题库','GZ学部','政府关系部','HRBP部','招生运营部','督检组','耀师项目部','产品运营部','营运部','多媒体技术部','跟谁学郑州中心(失效）','人工智能部','体验设计部','狮王项目部','资产服务部','专升本项目部','基础技术部(失效)','郑州中心综合部','考研学部','内容营销组','公关部','公职学部','客服部','运营平台部','CS学部','财务FP&A部','商学院学部','行政部','直播三部','营销技术部','私域运营组','飞花产品部','星火产品部','客户端技术部','薪酬绩效部','图书项目部','NJ学部','直播一部','法务部','在线服务部','履约部','KML经营分析组','社会保障部','精品班部','教学教研部','医疗项目部','菁英班部','菁英班学部','精品班学部','一对一学部','北京学部','图书学部','河南学部','清北班学部','湖广学部','山西学部','K学部','M学部','大学生学习学部','合肥学校','太原学校','苏州学校','郑州学校','北京学校','上海学校','运营中心','广州学校','市场中心','南京学校','深圳学校','成都学校','财务中心','武汉学校','济南学校','天津学校','学校办公室','重庆学校','西安学校','长沙学校','市场二部','留学学部','国际考试学部','出国语培线下项目','广州学校（IE）','国际竞赛项目','剑桥英语项目','上海学校（IE）','心理学部','创新项目部','素质成长学部','国际考试在线学部','毛豆学部','青少学部','市场三部','市场四部','青橙项目部','文旅学部','本地化大班学部','市场营销部','直播市场部','创新增长部','学习规划中心','素养初中学部','素养青藤学部','素养小学学部','用户运营部','经营策略部','校园招聘','直播创新部','战略创新部','产研部','业务研发部','教学质量部','Theta项目部','AI素养学部','文旅项目','Theta智学项目部','Theta产研部','V学部','TT初中学部','TT小学学部','产研部','T学部','专题课部（失效）','初中组','文旅项目（失效）')
        and performance_third_level_department_name = '市场顾问部'
	    )aa)
-------获取lead_id
,lead_gmv as (
select 
rd.*,
n_uid.lead_id
from rd
left join n_uid on rd.user_id1 = n_uid.original_order_user_number and rd.name = n_uid.performance_employee_email_name 
where n_uid.rn =1)
-----关联分配规则表
,lead_channel_dim as (
    select lead_id, channel_map
    from gaotu_hl.dim_mkt_h_lead_channel_df
    where dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
)
,rule as (select 
lead_gmv.*,
rr.rule_name
,coalesce(lc.channel_map, '未知') as channel_1,
case 
    when cast(substr(rr.group_period_term, 1, 2) as integer) >= 6 
    then date_format(date_add('day', 4, date_trunc('week', date_parse(concat('2025', substr(rr.group_period_term, 1, 4)), '%Y%m%d'))),'%Y%m%d') || '期'
    else date_format(date_add('day', 4, date_trunc('week', date_parse(concat('2026', substr(rr.group_period_term, 1, 4)), '%Y%m%d'))),'%Y%m%d') || '期'
end as friday_period
from lead_gmv
left join (
	select *,case 
    when instr(rule_name, '期') > 0 
         and instr(rule_name, '期') >= 5
         and regexp_like(substr(rule_name, instr(rule_name, '期') - 4, 4), '^[0-9]{4}$')
    then substr(rule_name, instr(rule_name, '期') - 4, 5)
    else null
end as group_period_term
	from service_dw.dim_crm_assign_rule_lead_detail_hf
	where dt = format_datetime(NOW() - interval '2' hour, 'YYYYMMdd') 
    and hour = format_datetime(NOW() - interval '2' hour, 'HH') 
)rr on lead_gmv.lead_id = rr.lead_id and lead_gmv.email_prefix = rr.account_domain
left join lead_channel_dim lc on cast(lead_gmv.lead_id as varchar) = lc.lead_id)
-------------14天内、30天内出单打标签	
,base as (
select 
    rule.*,
    zx.xiaozu,
    zx.jingli,
case 
    when date_parse(substr(friday_period, 1, 8), '%Y%m%d') = date_parse(substr(qici, 1, 8), '%Y%m%d') 
    then 0 
    when date_diff('day', 
        date_parse(substr(friday_period, 1, 8), '%Y%m%d'),
        date_parse(substr(qici, 1, 8), '%Y%m%d')
    ) = 7 
    then 1
    when date_diff('day', 
        date_parse(substr(friday_period, 1, 8), '%Y%m%d'),
        date_parse(substr(qici, 1, 8), '%Y%m%d')
    ) between 14 and 21 
    then 2
    when date_diff('day', 
        date_parse(substr(friday_period, 1, 8), '%Y%m%d'),
        date_parse(substr(qici, 1, 8), '%Y%m%d')
    ) = -7 
    then 4
    else 3 
end as week_diff
from rule
left join temp_table.lvshuai01_jiagou_zx zx on zx.employee_email_name = rule.name
)
----------------聚合到人
select 
qici,
channel_1,
jingli,
xiaozu,
grade_list,
name,
-- 净gmv分期汇总
    sum(case when week_diff = 0 then name_total_price else 0 end) as gmv_7,
    sum(case when week_diff = 1 then name_total_price else 0 end) as gmv_14,
    sum(case when week_diff = 2 then name_total_price else 0 end) as gmv_30,
    sum(case when week_diff = 3 then name_total_price else 0 end) as gmv_n30,
	sum(case when week_diff = 4 then name_total_price else 0 end) as gmv_7_h,
    sum(name_total_price) as gmv_total,
 -- 退款分期汇总
    sum(case when week_diff = 0 and name_total_price < 0 then name_total_price else 0 end) as refund_7,
    sum(case when week_diff = 1 and name_total_price < 0 then name_total_price else 0 end) as refund_14,
    sum(case when week_diff = 2 and name_total_price < 0 then name_total_price else 0 end) as refund_30,
    sum(case when week_diff = 3 and name_total_price < 0 then name_total_price else 0 end) as refund_n30,
	sum(case when week_diff = 4 and name_total_price < 0 then name_total_price else 0 end) as refund_7_p,
    sum(case when name_total_price < 0 then name_total_price else 0 end) as refund_total
from base
where name_total_price <> 0  
group by qici, channel_1, jingli, xiaozu, grade_list, name
order by qici desc, jingli, xiaozu, name
