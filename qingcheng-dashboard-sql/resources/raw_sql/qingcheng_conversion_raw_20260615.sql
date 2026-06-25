-- 业绩明细
with dd as (
select
GMV.lead_id,original_order_user_number,
pay_group_period_name,
trade_group_period_name,
channel_name_1,channel_name_2,channel_name_3,flow_pool_name,get_customer_way_name,
order_number,order_status,
pay_success_timestamp,
full_refund_timestamp,is_pay_success_order,is_part_refund_order,is_full_refund_order,original_order_number,original_order_pay_success_timestamp,latest_order_number,latest_order_full_refund_timestamp,latest_order_is_pay_success_order,latest_order_is_part_refund_order,latest_order_is_full_refund_order,performance_employee_email_name,performance_city_name,performance_talent_type_name,performance_first_level_department_name,performance_second_level_department_name,performance_third_level_department_name,performance_department_path_json,clazz_biz_number,clazz_type,clazz_begin_timestamp,clazz_end_timestamp,main_teacher_number,main_teacher_email_name,course_first_level_department_name,course_second_level_department_name,course_third_level_department_name,course_first_level_subject_name,course_second_level_subject_name,course_third_level_subject_name,course_name,course_category_code,school_department_name,grade_name,school_year,school_term_name,is_renew_class_amount,is_renew_class_user,school_subject_name,mapping_school_subject_name,is_blacklist_user,put_plan_name,trade_timestamp,pay_refund_type,
coalesce(income_amount/100,0) income_amount,
coalesce(refund_amount/100,0) refund_amount,
coalesce(income_amount/100,0)-coalesce(refund_amount/100,0) promit_amount,
lead_period_name,trade_period_name,trade_period_conversion_begin_time,trade_period_conversion_end_time,trade_period_mapping_first_level_department_name,trade_period_mapping_second_level_department_name,pay_period_name,pay_period_conversion_begin_time,pay_period_conversion_end_time,pay_period_mapping_first_level_department_name,pay_period_mapping_second_level_department_name,pay_period_first_level_course_project_name,pay_period_second_level_course_project_name,is_same_trade_lead_period,virtual_direct_leader_email_name,rule_name0,regexp_extract(rule_name, '(\d{4}期)', 1) AS qici0,---------gmv_qici    0612期
grade_0,qici,regexp_extract(qici, '\d{4}(\d{4}期)', 1) AS period
from(
select *,case when day_of_week(cast(trade_timestamp as timestamp)) = 1
        then concat(date_format(date_add('day', -3, date_trunc('week', cast(trade_timestamp as timestamp))),'%Y%m%d'),'期')
        else concat(date_format(date_add('day', 4, date_trunc('week', cast(trade_timestamp as timestamp))), '%Y%m%d'),'期')
end as qici
from service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf
where dt=format_datetime(NOW()-interval '2' hour,'YYYYMMdd') and hour=format_datetime(NOW()-interval '2' hour,'HH')
and course_first_level_department_name in ('H业务线','A业务线','EM业务线','LL业务线','TT','TUTU','TT业务线','CA业务线','创新中心')
and course_second_level_department_name in ('V项目部','本地化部','私域营销组','青少成长学部','创新技术组','成长中心供应链组','APP运营组','英语产品部','职场服务部','用户平台部','微师产品部','上海中心综合部','CAL技术组','财务核算部','财经项目部','人才发展部','财务信息化部','图书项目部（关闭）','运营部','基础架构组','数学产品部','营销产品部','雅思学部','商品部','磨课组','升学规划部','升学规划中心','郑州中心','组织部','留学申请学部','质检部','架构平台部','师训组','投放商务组','系统班部','编程素养学部','市场运营组','项目运营组','KM技术组','二讲老师部','成都中心综合部','业务设计部','专题课部','微师职教产品部','高校学部','教学服务部','平台产品部','数字化学部','品牌运营组','校长办公室','运营中心财务','视效部','数据与商业分析中心','X项目','教学产品部','XA学部','语言学部','图书产品部','主播部','业务支持部','HL技术组','武汉中心综合部','成人供应链组','途途课堂','信息平台部','HL经营分析组','大数据部','直播运营组','市场部','金刚产品部','教学产品运营中心','平台电商组','企业效能部','品牌与内容部','产品研发部','小学部','技术质量部','财务报告部','税务部','用户产品部','直播二部','招聘部','HR共享中心','清北','增长策略部','督察部','商品运营部','资金管理部','美好家庭学部','设计支持中心','初中部','AIGC创新部','财务部','人力资源部','人才保障部一部','CAL经营分析组','基础技术部','综合素养学部','热线呼入部','品牌部','语文产品部','供应链部','题库','GZ学部','政府关系部','HRBP部','招生运营部','督检组','耀师项目部','产品运营部','营运部','多媒体技术部','跟谁学郑州中心(失效）','人工智能部','体验设计部','狮王项目部','资产服务部','专升本项目部','基础技术部(失效)','郑州中心综合部','考研学部','线上考研学部','内容营销组','公关部','公职学部','客服部','运营平台部','CS学部','财务FP&A部','商学院学部','行政部','直播三部','营销技术部','私域运营组','飞花产品部','星火产品部','客户端技术部','薪酬绩效部','图书项目部','NJ学部','直播一部','法务部','在线服务部','履约部','KML经营分析组','社会保障部','精品班部','教学教研部','医疗项目部','菁英班部','菁英班学部','精品班学部','一对一学部','北京学部','图书学部','河南学部','清北班学部','湖广学部','山西学部','K学部','M学部','大学生学习学部','合肥学校','太原学校','苏州学校','郑州学校','北京学校','上海学校','运营中心','广州学校','市场中心','南京学校','深圳学校','成都学校','财务中心','武汉学校','济南学校','天津学校','学校办公室','重庆学校','西安学校','长沙学校','市场二部','留学学部','国际考试学部','出国语培线下项目','广州学校（IE）','国际竞赛项目','剑桥英语项目','上海学校（IE）','心理学部','创新项目部','创新学部','素质成长学部','国际考试在线学部','毛豆学部','青少学部','市场三部','市场四部','青橙项目部','文旅学部','本地化大班学部','市场营销部','直播市场部','创新增长部','学习规划中心','素养初中学部','素养青藤学部','素养小学学部','用户运营部','经营策略部','校园招聘','直播创新部','战略创新部','产研部','业务研发部','教学质量部','Theta项目部','AI素养学部','文旅项目','Theta智学项目部','Theta产研部','V学部','TT初中学部','TT小学学部','产研部','T学部','专题课部（失效）','初中组','文旅项目（失效）')) gmv
left join (
select distinct lead_id,put_plan_name,employee_email_name,channel_name_1,channel_name_2,channel_name_3,flow_pool_name,get_customer_way_name
  ,rule_name,case
  when rule_name like '%青橙IP%' then '青橙IP'
when rule_name like '%私域会话%' then '私域会话'
when rule_name like '%私域表单%' then '私域表单'
when rule_name like '%私域图书%' then '私域图书'
when rule_name like '%私域裂变%' then '私域裂变'
when rule_name like '%私域品效%' then '私域品效'
when rule_name like '%私域IE%' then '私域IE'
when rule_name like '%私域本地化%' then '私域本地化'
when rule_name like '%亚飞IP%' then '亚飞IP'
when rule_name like '%SEC未加好友%' then 'SEC未加好友'
when rule_name like '%SEC首期掉海%' then 'SEC首期掉海'
when rule_name like '%顾问未加好友%' then '顾问未加好友'
when rule_name like '%郑州图书%' then '郑州图书'
when rule_name like '%武汉图书%' then '武汉图书'
when rule_name like '%西安图书%' then '西安图书'
when rule_name like '%图书咨询%' then '图书咨询'
when rule_name like '%公域学霸%' then '公域学霸'
when rule_name like '%公海%' then '公海'
when rule_name like '%抖音私信%' then '抖音私信'
when rule_name like '%训练营%' then '青橙训练营'
when rule_name like '%进校%' then '进校'
else '未知' end as rule_name0
,case
when rule_name like '%高一%' then '高一'
when rule_name like '%高二%' then '高二'
when rule_name like '%高三%' then '高三'
when rule_name like '%初二%' then '初二'
when rule_name like '%初三%' then '初三'
else lead_purchase_intention_level2_category_name end as grade_0,
virtual_direct_leader_email_name
from bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df
where dt=format_datetime(NOW()-interval '2' hour,'YYYYMMdd') and hour=format_datetime(NOW()-interval '2' hour,'HH')
and section_assign_employee_first_level_department_name = 'H业务线'
and section_assign_employee_second_level_department_name = '青橙项目部'
and period_mapping_first_level_department_name = 'H业务线') ld on gmv.lead_id=ld.lead_id and ld.employee_email_name=gmv.performance_employee_email_name
where performance_second_level_department_name='青橙项目部'
and (income_amount <>0 or refund_amount <> 0)
and qici >= '20260424期' )
-- lead期次+分配时间
,prc as (
select *,row_number() over (partition by lead_id order by qici_lead desc) as rn
from (
select lead_id,user_id,employee_email_name,
regexp_extract(rule_name, '(\d{4}期)', 1) AS  qici_lead
,section_assign_time
from bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df
where dt=format_datetime(NOW()-interval '2' hour,'YYYYMMdd') and hour=format_datetime(NOW()-interval '3' hour,'HH')
and section_assign_employee_first_level_department_name = 'H业务线'
and section_assign_employee_second_level_department_name = '青橙项目部'
and period_mapping_first_level_department_name = 'H业务线'))
-- 成单周期
,gmv as (select
dd.qici,dd.rule_name0 as qudao,dd.qici0,
case when dd.qici0 = dd.period then 1 else 0 end as is_on_period,
dd.grade_0,dd.lead_id,dd.original_order_user_number as uid,
dd.performance_employee_email_name as name,dd.virtual_direct_leader_email_name as zhuguan,
dd.mapping_school_subject_name as sub,dd.income_amount,dd.refund_amount,dd.promit_amount,
prc.section_assign_time,dd.trade_timestamp
from dd
left join prc on prc.lead_id = dd.lead_id and prc.employee_email_name = dd.performance_employee_email_name and prc.rn = 1)
-- 先汇总uid订单
,udd as (select
qici,qudao,grade_0,zhuguan,name,uid,
date_diff('day',
        date(max(section_assign_time)),
        date(min(case when income_amount > 0 then trade_timestamp end))
    ) as sc,
count(distinct case when income_amount > 0 and sub != '定制方案' then sub end) as pay_sub,
count(distinct case when income_amount > 0 and is_on_period = 1 and sub != '定制方案' then sub end) as p_pay_sub,
sum(income_amount) as income,
sum(refund_amount) as refund,
sum(promit_amount) as promit,
sum(case when is_on_period = 1 then income_amount else 0 end) as p_income
from gmv
group by qici,qudao,grade_0,zhuguan,name,uid)
-- 汇总订单至顾问
,ud as (select
qici,qudao,grade_0,zhuguan,name,
count(distinct case when income > 0 then uid end) as pay_user,
count(distinct case when income > 0 and p_income > 0 then uid end) as p_pay_user,
sum(pay_sub) as pay_sub,
sum(p_pay_sub) as p_pay_sub,
sum(income) as income,
sum(refund) as refund,
sum(promit) as promit,
sum(p_income) as p_income,
count(distinct case when refund > 500 then uid end) as refund_user,
count(distinct case when promit > 0 then uid end) as podan,
sum(sc) as sc
from udd
group by qici,qudao,grade_0,zhuguan,name)
-- 线索量
,bb as (
select qici,channel_map_1,channel_map_2,grade_1,virtual_direct_leader_email_name,employee_email_name,sum(v_lead) as v_lead
from(
select distinct *
,concat(cast(date_format(date_add('day',4,date_trunc('week',date_add('day',-1,date_parse(replace(concat(group_period_year,group_period_term),'期',''),'%Y%m%d')))),'%Y%m%d')as varchar),'期') qici
,case
when f.rule_name like '%私域%' then '青橙私域'
  when f.rule_name like '%IP%' or f.rule_name like '%亚飞IP%' then '青橙IP'
when f.rule_name like '%青橙IP%' then '青橙IP'
when f.rule_name like '%公海%' then '青橙公海'
when f.rule_name like '%公域%' then '青橙公域'
when f.rule_name like '%武汉图书%' or f.rule_name like '%郑州图书%' or f.rule_name like '%西安图书%' then '青橙图书'
when f.rule_name like '%抖音私信%' then '抖音私信'
when f.rule_name like '%训练营%' then '青橙训练营'
when f.rule_name like '%进校%' then '进校'
else '未知'
end as channel_map_1
  ,case
when f.rule_name like '%青橙IP%' then '青橙IP'
when f.rule_name like '%私域会话%' then '私域会话'
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
when f.rule_name like '%公海%' then '公海'
when f.rule_name like '%抖音私信%' then '抖音私信'
when f.rule_name like '%训练营%' then '青橙训练营'
when f.rule_name like '%进校%' then '进校'
else '未知'
end as channel_map_2
,case
when f.rule_name like '%高一%' then '高一'
when f.rule_name like '%高二%' then '高二'
when f.rule_name like '%高三%' then '高三'
when f.rule_name like '%初一%' then '初一'
when f.rule_name like '%初二%' then '初二'
when f.rule_name like '%初三%' then '初三'
else f.lead_purchase_intention_level2_category_name end as grade_1
,case when f.valid_lead_count = '1' then 1 else 0 end as v_lead
from
bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df f
where f.dt=format_datetime(NOW()-interval '2' hour,'YYYYMMdd') and f.hour=format_datetime(NOW()-interval '2' hour,'HH')
and f.section_assign_employee_first_level_department_name = 'H业务线'
and f.section_assign_employee_second_level_department_name = '青橙项目部'
and f.period_mapping_first_level_department_name = 'H业务线'
and f.valid_lead_count = '1' )
where qici >= '20260424期'
group by qici,channel_map_1,channel_map_2,grade_1,virtual_direct_leader_email_name,employee_email_name)
-- 保留年级维度的对齐层
,bb_dedup as (
    select *,
    case when v_lead > 5 then employee_email_name else '0' end as if_jieliang,
    row_number() over(
        partition by employee_email_name, qici, channel_map_1, channel_map_2, grade_1, virtual_direct_leader_email_name
        order by v_lead desc
    ) as rn
    from bb
)
-- 合并
,mm as (select
coalesce(bb1.qici, ud.qici) as qici,
coalesce(bb1.channel_map_2, ud.qudao, '未知') as channel_map_2,
coalesce(bb1.grade_1, ud.grade_0, '未知') as grade_1,
coalesce(bb1.employee_email_name, ud.name) as employee_email_name,
coalesce(bb1.v_lead, 0) as v_lead,
coalesce(bb1.virtual_direct_leader_email_name, ud.zhuguan) as virtual_direct_leader_email_name,
coalesce(bb1.if_jieliang, '0') as jieliang,
coalesce(ud.pay_user, 0) as pay_user,
coalesce(ud.p_pay_user, 0) as p_pay_user,
coalesce(ud.pay_sub, 0) as pay_sub,
coalesce(ud.p_pay_sub, 0) as p_pay_sub,
coalesce(ud.income, 0) as income,
coalesce(ud.refund, 0) as refund,
coalesce(ud.promit, 0) as promit,
coalesce(ud.p_income, 0) as p_income,
coalesce(ud.refund_user, 0) as refund_user,
coalesce(ud.podan, 0) as podan,
coalesce(ud.sc, 0) as sc
from bb_dedup bb1
full outer join ud
    on ud.name = bb1.employee_email_name
   and ud.qici = bb1.qici
   and ud.qudao = bb1.channel_map_2
   and ud.grade_0 = bb1.grade_1
   and ud.zhuguan = bb1.virtual_direct_leader_email_name
where bb1.rn = 1 or bb1.rn is null
)
-- 例子成本
select *
from(
select distinct
mm.*,
case when channel_map_2 = '亚飞IP' then 120
when channel_map_2 = '武汉图书' then 20
when channel_map_2 = '抖音私信' then 130
when channel_map_2 = '进校' then 70
else 0
end as cost_lead,
case when channel_map_2 like '%私域%' or channel_map_2 like '%公域%' then '私域'
     when channel_map_2 like '%IP%' then 'IP'
     when channel_map_2 like '%图书%' then '图书'
     when channel_map_2 like '%SEC未加好友%' or channel_map_2 like '%SEC首期掉海%' or channel_map_2 like '%公海%' or channel_map_2 like '%顾问未加好友%' then '公海'
     when channel_map_2 like '%抖音私信%' then '抖音私信'
     when channel_map_2 like '%训练营%' then '青橙训练营'
     when channel_map_2 like '%进校%' then '进校'
     else '未知'
end as channel_1,
jg.xuebu as dept_2,
jg.leader_employee_email_name as xiaozu,
jg.dazu,jg.jingli
from mm
left join (
select
    employee_email_name,
    xuebu,
    leader_employee_email_name,
    dazu,
    jingli
from temp_table.dingxi01_qing_team_jg
where qici = (select max(qici) from temp_table.dingxi01_qing_team_jg)
) jg on mm.employee_email_name = jg.employee_email_name)