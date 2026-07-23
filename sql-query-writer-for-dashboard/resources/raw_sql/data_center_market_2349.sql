with dd as (
select
id,order_number,substring(biz_number, 1, 10) AS sub_biz_number,pre_biz_number,clazz_name,user_id AS user_id1,pre_employee_id,
type,trade_status,trade_type,order_paid_time as paid_time,trade_time,case when trade_status in ('全部退款','部分退款') then - real_price else real_price end as real_price_0,transfer_price,price,email_prefix,
employee_email_name as name,talent_type_name ,city_name as city,department,biz_number,course_grade as grade_list,course_subject as subject,qici,leader_employee_email_name,
case course_term_id when 'C' then '春季' when 'X' then '夏季' when 'Q' then '秋季' when 'D' then '冬季' else '其他'
end as school_term_id,
note,course_first_level_department_name,course_second_level_department_name,course_top_level_department_name
 from 
	(select *,
		case
			when substr(trade_time, 1, 10) >= '2026-07-14' and substr(trade_time, 1, 10) <= '2026-07-19' then '20260716期'
			when substr(trade_time, 1, 10) >= '2026-07-20' and substr(trade_time, 1, 10) <= '2026-07-25' then '20260722期'
			when substr(trade_time, 1, 10) >= '2026-07-26' and substr(trade_time, 1, 10) <= '2026-07-31' then '20260728期'
			when substr(trade_time, 1, 10) >= '2026-08-01' and substr(trade_time, 1, 10) <= '2026-08-06' then '20260803期'
			when substr(trade_time, 1, 10) >= '2026-08-07' and substr(trade_time, 1, 10) <= '2026-08-12' then '20260809期'
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
end as qici
    from finance_dw.app_finance_performance_extend_details_hf 
    where dt = FORMAT_DATETIME(NOW() - INTERVAL '2' HOUR,'YYYYMMdd')
        and hour = FORMAT_DATETIME(NOW() - INTERVAL '2' HOUR,'HH')
        and employee_first_level_department_name = 'H业务线'
	    and employee_second_level_department_name = '市场部'
        and employee_third_level_department_name = '市场顾问部'
        ) d
    where d.qici > '20260220期'
)
-------------调课调班
,gmv_t as (select *
from (select 
id,order_number,clazz_name,user_id1,trade_status,trade_type, trade_time, real_price_0,transfer_price,price,email_prefix,name,talent_type_name ,city,department,grade_list,subject,qici,leader_employee_email_name,school_term_id,course_first_level_department_name,course_second_level_department_name,name_total_price,row_number() over (partition by name order by name_total_price desc) as dup_rn
from (
   select *, round(sum(price) over (partition by name),3) as name_total_price
    from dd where trade_type = '调课调班'
) t where name_total_price != 0 )
where dup_rn = 1)
--------------正常订单
,gmv_z as (select * 
from (select 
id,order_number,clazz_name,user_id1,trade_status,trade_type, trade_time,real_price_0,transfer_price,price,email_prefix,name,talent_type_name ,city,department,grade_list,subject,qici,leader_employee_email_name,school_term_id,course_first_level_department_name,course_second_level_department_name,real_price_0 as name_total_price,row_number() over (partition by clazz_name,user_id1,real_price_0,name order by user_id1 desc) as dup_rn
from dd where trade_type = '正常订单')
where dup_rn = 1)
-----整合总订单流水
,rd as (select * from gmv_z
union all
select * from gmv_t)
------依据期次获取最新uid
,n_uid as (
select aa.*,row_number() over (partition by original_order_user_number order by qici desc) as rn
from (select lead_id,original_order_user_number,performance_employee_email_name,case
    when cast(date_parse(replace(concat(trade_group_period_year,trade_group_period_term),'期',''),'%Y%m%d') as date) between date '2026-07-14' and date '2026-07-19' then '20260716期'
    when cast(date_parse(replace(concat(trade_group_period_year,trade_group_period_term),'期',''),'%Y%m%d') as date) between date '2026-07-20' and date '2026-07-25' then '20260722期'
    when cast(date_parse(replace(concat(trade_group_period_year,trade_group_period_term),'期',''),'%Y%m%d') as date) between date '2026-07-26' and date '2026-07-31' then '20260728期'
    when cast(date_parse(replace(concat(trade_group_period_year,trade_group_period_term),'期',''),'%Y%m%d') as date) between date '2026-08-01' and date '2026-08-06' then '20260803期'
    when cast(date_parse(replace(concat(trade_group_period_year,trade_group_period_term),'期',''),'%Y%m%d') as date) between date '2026-08-07' and date '2026-08-12' then '20260809期'
    else concat(cast(date_format(date_trunc('week',date_parse(replace(concat(trade_group_period_year,trade_group_period_term),'期',''),'%Y%m%d') - interval '1' day) + interval '4' day,'%Y%m%d')as varchar),'期')
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
rd.*,case when course_second_level_department_name like '%精品班学部%' then '大班'
when course_second_level_department_name like '%菁英班学部%' then '小班'
when course_second_level_department_name like '%一对一学部%' then '一对一'
when course_second_level_department_name like '%本地化学部%' then '本地化'
when course_second_level_department_name like '%清北班学部%' then '清北'
else '其他'  end as course_name,
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
when rr.rule_name like '%北京直播江苏%' then '北京直播江苏'
when rr.rule_name like '%tmk3元周帅%' then 'tmk3元周帅'
when rr.rule_name like '%tmk9元沈阳%' then 'tmk9元沈阳'
when rr.rule_name like '%tmk9元启师%' then 'tmk9元启师'
when rr.rule_name like '%抖音私域%' then '抖音私域'
when rr.rule_name like '%曹忆ip99元福建%'  then '曹忆ip99元福建'
when rr.rule_name like '%曹忆ip99元江苏%'  then '曹忆ip99元江苏'
when rr.rule_name like '%孟亚飞ip9元福建%'  then '孟亚飞ip9元福建'
when rr.rule_name like '%孟亚飞ip9元江苏%'  then '孟亚飞ip9元江苏'
when rr.rule_name like '%周帅ip9元%'  then '周帅ip9元'
when rr.rule_name like '%朱汉祺ip9元%'  then '朱汉祺ip9元'
when rr.rule_name like '%曹忆ip99元%' then '曹忆IP99元'
when rr.rule_name like '%APP%' then 'APP'
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
when rr.rule_name like '%小红书%' then '小红书'
when rr.rule_name like '%原子初三%' or rr.rule_name like '%原子高一%' or rr.rule_name like '%原子%'  then '原子'
when rr.rule_name like '%9KM%' then '9KM'
when rr.rule_name like '%百度星耀数学%' or rr.rule_name like '%数学%' or rr.rule_name like '%百度星耀物理%' or rr.rule_name like '%物理%'then '百度星耀'
else '未知' end as channel_1,
case
        when substr(lead_gmv.qici, 1, 4) = '2026' and substr(rr.group_period_term, 1, 4) between '0714' and '0719'
        then '20260716期'
        when substr(lead_gmv.qici, 1, 4) = '2026' and substr(rr.group_period_term, 1, 4) between '0720' and '0725'
        then '20260722期'
        when substr(lead_gmv.qici, 1, 4) = '2026' and substr(rr.group_period_term, 1, 4) between '0726' and '0731'
        then '20260728期'
        when substr(lead_gmv.qici, 1, 4) = '2026' and substr(rr.group_period_term, 1, 4) between '0801' and '0806'
        then '20260803期'
        when substr(lead_gmv.qici, 1, 4) = '2026' and substr(rr.group_period_term, 1, 4) between '0807' and '0812'
        then '20260809期'
        -- 如果月份 >= 6，年份为2025
        when cast(substr(rr.group_period_term, 1, 2) as int) >= 6 
        then date_format(date_parse('2025' || rr.group_period_term, '%Y%m%d') + (5 - day_of_week(date_parse('2025' || rr.group_period_term, '%Y%m%d'))) * interval '1' day, '%Y%m%d') || '期'
        -- 其他月份，年份为2026
        else date_format(date_parse('2026' || rr.group_period_term, '%Y%m%d') + (5 - day_of_week(date_parse('2026' || rr.group_period_term, '%Y%m%d'))) * interval '1' day, '%Y%m%d') || '期'
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
------------------------ 退款金额结构占比
,refund_base as (
    select
        qici,
        channel_1,
        jingli,
        xiaozu,
        grade_list,
        case
            when subject like '%数学%' then '数学'
            when subject like '%语文%' then '语文'
            when subject like '%英语%' then '英语'
            when subject like '%物理%' then '物理'
            when subject like '%生物%' then '生物'
            when subject like '%化学%' then '化学'
            when subject like '%地理%' then '地理'
            when subject like '%政治%' then '政治'
            when subject like '%历史%' then '历史'
            when subject like '%学习分享%' then '学习分享'
            when subject like '%定制方案%' then '定制方案'
            else '其他'
        end as subject,
        course_name,
        abs(name_total_price) as refund_amount
    from base
    where name_total_price < 0
)
,subject_dim as (
    select subject
    from (
        values
            ('数学'), ('语文'), ('英语'), ('物理'), ('生物'), ('化学'),
            ('地理'), ('政治'), ('历史'), ('学习分享'), ('定制方案'), ('其他')
    ) as t(subject)
    union
    select distinct subject
    from refund_base
)
,product_dim as (
    select course_name
    from (
        values ('大班'), ('小班'), ('一对一'), ('本地化'), ('清北'), ('其他')
    ) as t(course_name)
    union
    select distinct course_name
    from refund_base
)
,grade_dim as (
    select distinct grade_list
    from refund_base
)
,filter_group_with_grade as (
    select
        qici,
        channel_1,
        jingli,
        xiaozu,
        grade_list,
        sum(refund_amount) as total_refund_amount
    from refund_base
    group by qici, channel_1, jingli, xiaozu, grade_list
)
,filter_group_without_grade as (
    select
        qici,
        channel_1,
        jingli,
        xiaozu,
        sum(refund_amount) as total_refund_amount
    from refund_base
    group by qici, channel_1, jingli, xiaozu
)
,subject_refund as (
    select
        qici,
        channel_1,
        jingli,
        xiaozu,
        grade_list,
        subject,
        sum(refund_amount) as refund_amount
    from refund_base
    group by qici, channel_1, jingli, xiaozu, grade_list, subject
)
,product_refund as (
    select
        qici,
        channel_1,
        jingli,
        xiaozu,
        grade_list,
        course_name,
        sum(refund_amount) as refund_amount
    from refund_base
    group by qici, channel_1, jingli, xiaozu, grade_list, course_name
)
,grade_refund as (
    select
        qici,
        channel_1,
        jingli,
        xiaozu,
        grade_list,
        sum(refund_amount) as refund_amount
    from refund_base
    group by qici, channel_1, jingli, xiaozu, grade_list
)
select
    fg.qici,
    fg.channel_1,
    fg.jingli,
    fg.xiaozu,
    fg.grade_list,
    sd.subject,
    cast(null as varchar) as course_name,
    'subject' as analysis_type,
    sd.subject as dim_value,
    coalesce(sr.refund_amount, 0) as refund_amount,
    fg.total_refund_amount
from filter_group_with_grade fg
cross join subject_dim sd
left join subject_refund sr
    on sr.qici = fg.qici
    and sr.channel_1 = fg.channel_1
    and coalesce(sr.jingli, '') = coalesce(fg.jingli, '')
    and coalesce(sr.xiaozu, '') = coalesce(fg.xiaozu, '')
    and coalesce(sr.grade_list, '') = coalesce(fg.grade_list, '')
    and sr.subject = sd.subject
union all
select
    fg.qici,
    fg.channel_1,
    fg.jingli,
    fg.xiaozu,
    fg.grade_list,
    cast(null as varchar) as subject,
    pd.course_name,
    'product' as analysis_type,
    pd.course_name as dim_value,
    coalesce(pr.refund_amount, 0) as refund_amount,
    fg.total_refund_amount
from filter_group_with_grade fg
cross join product_dim pd
left join product_refund pr
    on pr.qici = fg.qici
    and pr.channel_1 = fg.channel_1
    and coalesce(pr.jingli, '') = coalesce(fg.jingli, '')
    and coalesce(pr.xiaozu, '') = coalesce(fg.xiaozu, '')
    and coalesce(pr.grade_list, '') = coalesce(fg.grade_list, '')
    and pr.course_name = pd.course_name
union all
select
    fg.qici,
    fg.channel_1,
    fg.jingli,
    fg.xiaozu,
    gd.grade_list,
    cast(null as varchar) as subject,
    cast(null as varchar) as course_name,
    'grade' as analysis_type,
    gd.grade_list as dim_value,
    coalesce(gr.refund_amount, 0) as refund_amount,
    fg.total_refund_amount
from filter_group_without_grade fg
cross join grade_dim gd
left join grade_refund gr
    on gr.qici = fg.qici
    and gr.channel_1 = fg.channel_1
    and coalesce(gr.jingli, '') = coalesce(fg.jingli, '')
    and coalesce(gr.xiaozu, '') = coalesce(fg.xiaozu, '')
    and coalesce(gr.grade_list, '') = coalesce(gd.grade_list, '')
