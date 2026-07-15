with biz_qici_calendar as (
select *
from (
    values
        ('20260716期', '0716期', '20260717期', '0717期', date '2026-07-14', date '2026-07-20'),
        ('20260722期', '0722期', '20260724期', '0724期', date '2026-07-21', date '2026-07-27'),
        ('20260728期', '0728期', '20260731期', '0731期', date '2026-07-28', date '2026-08-03'),
        ('20260803期', '0803期', '20260807期', '0807期', date '2026-08-04', date '2026-08-06'),
        ('20260809期', '0809期', '20260807期', '0807期', date '2026-08-07', date '2026-08-10'),
        ('20260815期', '0815期', '20260814期', '0814期', date '2026-08-11', date '2026-08-17'),
        ('20260821期', '0821期', '20260821期', '0821期', date '2026-08-18', date '2026-08-24')
) as t(qici, short_qici, legacy_qici, legacy_short_qici, period_start_date, period_end_date)
)
,lead_map as (
select lead_id,put_plan_name,employee_email_name,channel_name_1,channel_name_2,channel_name_3,flow_pool_name,get_customer_way_name
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
from (
    select
           lead_id,
           put_plan_name,
           employee_email_name,
           channel_name_1,
           channel_name_2,
           channel_name_3,
           flow_pool_name,
           get_customer_way_name,
           rule_name,
           lead_purchase_intention_level2_category_name,
           virtual_direct_leader_email_name,
           section_assign_time,
           row_number() over (
               partition by lead_id, employee_email_name
               order by section_assign_time desc,
                        regexp_extract(rule_name, '(\d{4}期)', 1) desc
           ) as rn
    from bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df
    where dt=format_datetime(NOW()-interval '2' hour,'YYYYMMdd') and hour=format_datetime(NOW()-interval '2' hour,'HH')
      and section_assign_employee_first_level_department_name = 'H业务线'
      and section_assign_employee_second_level_department_name = '青橙项目部'
      and period_mapping_first_level_department_name = 'H业务线'
) lm
where lm.rn = 1
)
,dd as (
select
base.lead_id,
base.original_order_user_number,
base.order_number,
base.performance_employee_email_name,
base.mapping_school_subject_name,
base.trade_timestamp,
base.trade_group_period_name,
base.pay_group_period_name,
base.clazz_name,
base.income_amount,
base.refund_amount,
base.promit_amount,
base.filled_course_first_level_department_name,
base.filled_course_second_level_department_name,
base.service_transfer_in_amount_yuan,
base.service_transfer_out_amount_yuan,
base.rule_name0,
base.rule_name,
coalesce(
    period_cal.short_qici,
    regexp_extract(base.rule_name, '(\d{4}期)', 1)
) as qici0,
base.grade_0,
base.qici,
regexp_extract(base.qici, '\d{4}(\d{4}期)', 1) as period,
base.virtual_direct_leader_email_name
from (
select
gmv.lead_id,
gmv.original_order_user_number,
gmv.order_number,
gmv.performance_employee_email_name,
gmv.mapping_school_subject_name,
gmv.trade_timestamp,
gmv.trade_group_period_name,
gmv.pay_group_period_name,
gmv.clazz_name,
coalesce(gmv.income_amount / 100, 0) as income_amount,
coalesce(gmv.refund_amount / 100, 0) as refund_amount,
coalesce(gmv.income_amount / 100, 0) - coalesce(gmv.refund_amount / 100, 0) as promit_amount,
cast(coalesce(gmv.transfer_in_amount, 0) as double) / 100.0 as service_transfer_in_amount_yuan,
cast(coalesce(gmv.transfer_out_amount, 0) as double) / 100.0 as service_transfer_out_amount_yuan,
case
    when gmv.course_first_level_department_name is not null then gmv.course_first_level_department_name
    when gmv.grade_name like '%小学%' or gmv.grade_name like '%初%' then '小初业务线'
    else 'H业务线'
end as filled_course_first_level_department_name,
case
    when gmv.course_second_level_department_name is not null then gmv.course_second_level_department_name
    when gmv.course_first_level_department_name = 'H业务线' then '精品班学部'
    when gmv.course_first_level_department_name is null
     and not (gmv.grade_name like '%小学%' or gmv.grade_name like '%初%') then '精品班学部'
    else gmv.course_second_level_department_name
end as filled_course_second_level_department_name,
ld.rule_name0,
ld.rule_name,
ld.grade_0,
ld.virtual_direct_leader_email_name,
coalesce(
    trade_cal.qici,
    case
        when day_of_week(cast(gmv.trade_timestamp as timestamp)) = 1 then
            concat(
                date_format(
                    date_trunc('week', cast(gmv.trade_timestamp as timestamp)) - interval '3' day,
                    '%Y%m%d'
                ),
                '期'
            )
        else
            concat(
                date_format(
                    date_trunc('week', cast(gmv.trade_timestamp as timestamp)) + interval '4' day,
                    '%Y%m%d'
                ),
                '期'
            )
    end
) as qici
from service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf gmv
left join biz_qici_calendar trade_cal
  on cast(gmv.trade_timestamp as date) between trade_cal.period_start_date and trade_cal.period_end_date
left join lead_map ld
  on gmv.lead_id = ld.lead_id
 and ld.employee_email_name = gmv.performance_employee_email_name
where gmv.dt=format_datetime(NOW()-interval '2' hour,'YYYYMMdd')
  and gmv.hour=format_datetime(NOW()-interval '2' hour,'HH')
  and gmv.performance_second_level_department_name='青橙项目部'
  and gmv.course_first_level_department_name in ('H业务线','LL业务线','TUTU','TT','A业务线','EM业务线','KA业务线','TT业务线','创新中心')
  and gmv.course_second_level_department_name in ('V项目部','本地化部','私域营销组','青少成长学部','创新技术组','成长中心供应链组','APP运营组','英语产品部','职场服务部','用户平台部','微师产品部','上海中心综合部','CAL技术组','财务核算部','财经项目部','人才发展部','财务信息化部','图书项目部（关闭）','运营部','基础架构组','数学产品部','营销产品部','雅思学部','商品部','磨课组','升学规划部','升学规划中心','郑州中心','组织部','留学申请学部','质检部','架构平台部','师训组','投放商务组','系统班部','编程素养学部','市场运营组','项目运营组','KM技术组','二讲老师部','成都中心综合部','业务设计部','专题课部','微师职教产品部','高校学部','教学服务部','平台产品部','数字化学部','品牌运营组','校长办公室','运营中心财务','视效部','数据与商业分析中心','X项目','教学产品部','XA学部','语言学部','图书产品部','主播部','业务支持部','HL技术组','武汉中心综合部','成人供应链组','途途课堂','信息平台部','HL经营分析组','大数据部','直播运营组','市场部','金刚产品部','教学产品运营中心','平台电商组','企业效能部','品牌与内容部','产品研发部','小学部','技术质量部','财务报告部','税务部','用户产品部','直播二部','招聘部','HR共享中心','清北','增长策略部','督察部','商品运营部','资金管理部','美好家庭学部','设计支持中心','初中部','AIGC创新部','财务部','人力资源部','人才保障部一部','CAL经营分析组','基础技术部','综合素养学部','热线呼入部','品牌部','语文产品部','供应链部','题库','GZ学部','政府关系部','HRBP部','招生运营部','督检组','耀师项目部','产品运营部','营运部','多媒体技术部','跟谁学郑州中心(失效）','人工智能部','体验设计部','狮王项目部','资产服务部','专升本项目部','基础技术部(失效)','郑州中心综合部','考研学部','线上考研学部','内容营销组','公关部','公职学部','客服部','运营平台部','CS学部','财务FP&A部','商学院学部','行政部','直播三部','营销技术部','私域运营组','飞花产品部','星火产品部','客户端技术部','薪酬绩效部','图书项目部','NJ学部','直播一部','法务部','在线服务部','履约部','KML经营分析组','社会保障部','精品班部','教学教研部','医疗项目部','菁英班部','菁英班学部','精品班学部','一对一学部','北京学部','图书学部','河南学部','清北班学部','湖广学部','山西学部','K学部','M学部','大学生学习学部','合肥学校','太原学校','苏州学校','郑州学校','北京学校','上海学校','运营中心','广州学校','市场中心','南京学校','深圳学校','成都学校','财务中心','武汉学校','济南学校','天津学校','学校办公室','重庆学校','西安学校','长沙学校','市场二部','留学学部','国际考试学部','出国语培线下项目','广州学校（IE）','国际竞赛项目','剑桥英语项目','上海学校（IE）','心理学部','创新项目部','创新学部','素质成长学部','国际考试在线学部','毛豆学部','青少学部','市场三部','市场四部','青橙项目部','文旅学部','本地化大班学部','市场营销部','直播市场部','创新增长部','学习规划中心','素养初中学部','素养青藤学部','素养小学学部','用户运营部','经营策略部','校园招聘','直播创新部','战略创新部','产研部','业务研发部','教学质量部','Theta项目部','AI素养学部','文旅项目','Theta智学项目部','Theta产研部','V学部','TT初中学部','TT小学学部','产研部','T学部','专题课部（失效）','初中组','文旅项目（失效）')
  and (gmv.income_amount <>0 or gmv.refund_amount <> 0)
) base
left join biz_qici_calendar period_cal
  on base.qici = period_cal.qici
 and regexp_extract(base.rule_name, '(\d{4}期)', 1) = period_cal.legacy_short_qici
where base.qici >= '20260424期'
)
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
,dd_order_scope as (
select distinct qici, order_number
from dd
where order_number is not null
)
,order_change_raw as (
select
    order_number,
    parent_order_number,
    original_order_number,
    latest_child_order_number,
    case
        when order_change_type = 0 then '调课调班'
        when order_change_type = 1 then '课程转移'
        else cast(order_change_type as varchar)
    end as refund_type,
    case when cast(is_orginal_order as varchar) = '1' then 1 else 0 end as is_original_order,
    case when cast(is_orginal_order as varchar) = '0' then 1 else 0 end as is_child_order,
    cast(coalesce(transfer_in_amount, 0) as double) / 100.0 as transfer_in_amount_yuan,
    cast(coalesce(transfer_out_amount, 0) as double) / 100.0 as transfer_out_amount_yuan
from finance_dw.dim_finance_order_change_df
where dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
  and latest_child_order_status in (2, 6, 7)
  and biz_type in (2, 7)
)
,order_change_order_map as (
select order_number as join_order_number, refund_type, is_original_order, is_child_order, transfer_in_amount_yuan, transfer_out_amount_yuan
from order_change_raw
where order_number is not null
union all
select parent_order_number as join_order_number, refund_type, is_original_order, is_child_order, transfer_in_amount_yuan, transfer_out_amount_yuan
from order_change_raw
where parent_order_number is not null
union all
select original_order_number as join_order_number, refund_type, is_original_order, is_child_order, transfer_in_amount_yuan, transfer_out_amount_yuan
from order_change_raw
where original_order_number is not null
union all
select latest_child_order_number as join_order_number, refund_type, is_original_order, is_child_order, transfer_in_amount_yuan, transfer_out_amount_yuan
from order_change_raw
where latest_child_order_number is not null
)
,order_change as (
select
    join_order_number as order_number,
    1 as has_order_change,
    max(is_original_order) as is_original_order,
    max(is_child_order) as is_child_order,
    max(transfer_in_amount_yuan) as transfer_in_amount_yuan,
    max(transfer_out_amount_yuan) as transfer_out_amount_yuan,
    array_join(array_distinct(array_agg(coalesce(refund_type, '未知'))), ',') as refund_type
from order_change_order_map
group by join_order_number
)
,ord as (
select
    a.order_number,
    a.full_refund_chain_finish_lesson_count
from finance_dw.dm_finance_order_refund_detail_df a
inner join (
    select distinct order_number
    from dd_order_scope
) scope_ord
    on a.order_number = scope_ord.order_number
where a.dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
  and a.course_first_level_department_name in ('H业务线','TT')
  and a.course_second_level_department_name in ('V项目部','本地化部','私域营销组','青少成长学部','创新技术组','成长中心供应链组','APP运营组','英语产品部','职场服务部','用户平台部','微师产品部','上海中心综合部','CAL技术组','财务核算部','财经项目部','人才发展部','财务信息化部','图书项目部（关闭）','运营部','基础架构组','数学产品部','营销产品部','雅思学部','商品部','磨课组','升学规划部','升学规划中心','郑州中心','组织部','留学申请学部','质检部','架构平台部','师训组','投放商务组','系统班部','编程素养学部','市场运营组','项目运营组','KM技术组','二讲老师部','成都中心综合部','业务设计部','专题课部','微师职教产品部','高校学部','教学服务部','平台产品部','数字化学部','品牌运营组','校长办公室','运营中心财务','视效部','数据与商业分析中心','X项目','教学产品部','XA学部','语言学部','图书产品部','主播部','业务支持部','HL技术组','武汉中心综合部','成人供应链组','途途课堂','信息平台部','HL经营分析组','大数据部','直播运营组','市场部','金刚产品部','教学产品运营中心','平台电商组','企业效能部','品牌与内容部','产品研发部','小学部','技术质量部','财务报告部','税务部','用户产品部','直播二部','招聘部','HR共享中心','清北','增长策略部','督察部','商品运营部','资金管理部','美好家庭学部','设计支持中心','初中部','AIGC创新部','财务部','人力资源部','人才保障部一部','CAL经营分析组','基础技术部','综合素养学部','热线呼入部','品牌部','语文产品部','供应链部','题库','GZ学部','政府关系部','HRBP部','招生运营部','督检组','耀师项目部','产品运营部','营运部','多媒体技术部','跟谁学郑州中心(失效）','人工智能部','体验设计部','狮王项目部','资产服务部','专升本项目部','基础技术部(失效)','郑州中心综合部','考研学部','线上考研学部','内容营销组','公关部','公职学部','客服部','运营平台部','CS学部','财务FP&A部','商学院学部','行政部','直播三部','营销技术部','私域运营组','飞花产品部','星火产品部','客户端技术部','薪酬绩效部','图书项目部','NJ学部','直播一部','法务部','在线服务部','履约部','KML经营分析组','社会保障部','精品班部','教学教研部','医疗项目部','菁英班部','菁英班学部','精品班学部','一对一学部','北京学部','图书学部','河南学部','清北班学部','湖广学部','山西学部','K学部','M学部','大学生学习学部','合肥学校','太原学校','苏州学校','郑州学校','北京学校','上海学校','运营中心','广州学校','市场中心','南京学校','深圳学校','成都学校','财务中心','武汉学校','济南学校','天津学校','学校办公室','重庆学校','西安学校','长沙学校','市场二部','留学学部','国际考试学部','出国语培线下项目','广州学校（IE）','国际竞赛项目','剑桥英语项目','上海学校（IE）','心理学部','创新项目部','创新学部','素质成长学部','国际考试在线学部','毛豆学部','青少学部','市场三部','市场四部','青橙项目部','文旅学部','本地化大班学部','市场营销部','直播市场部','创新增长部','学习规划中心','素养初中学部','素养青藤学部','素养小学学部','用户运营部','经营策略部','校园招聘','直播创新部','战略创新部','产研部','业务研发部','教学质量部','Theta项目部','AI素养学部','文旅项目','Theta智学项目部','Theta产研部','V学部','TT初中学部','TT小学学部','产研部','T学部','专题课部（失效）','初中组','文旅项目（失效）')
  and a.is_full_refund_order = 1
  and a.total_refund_amount is not null
  and a.total_refund_amount <> 0
)
,re_ke as (
select
    order_number,
    max(full_refund_chain_finish_lesson_count) as full_refund_chain_finish_lesson_count
from ord
group by order_number
)
-- 成单周期 + 调课调班剔除 + 退4/点睛2
,gmv as (
select
dd.qici,dd.rule_name0 as qudao,dd.qici0,
case when dd.qici0 = dd.period then 1 else 0 end as is_on_period,
dd.grade_0,dd.lead_id,dd.original_order_user_number as uid,
dd.performance_employee_email_name as name,dd.virtual_direct_leader_email_name as zhuguan,
dd.mapping_school_subject_name as sub,
dd.trade_timestamp,
dd.trade_group_period_name,
dd.pay_group_period_name,
prc.section_assign_time,
dd.filled_course_first_level_department_name as course_first_level_department_name,
dd.filled_course_second_level_department_name as course_second_level_department_name,
dd.clazz_name,
coalesce(re_ke.full_refund_chain_finish_lesson_count, 0) as re_lc,
coalesce(order_change.has_order_change, 0) as main_has_order_change,
coalesce(order_change.transfer_in_amount_yuan, 0) as main_transfer_in_amount_yuan,
coalesce(order_change.transfer_out_amount_yuan, 0) as main_transfer_out_amount_yuan,
dd.service_transfer_in_amount_yuan,
dd.service_transfer_out_amount_yuan,
case
    when dd.service_transfer_in_amount_yuan > 0 or dd.service_transfer_out_amount_yuan > 0 then 1
    else 0
end as is_internal_order_change_amount,
case
    when dd.service_transfer_in_amount_yuan > 0 or dd.service_transfer_out_amount_yuan > 0 then 0
    else dd.income_amount
end as income_amount,
case
    when dd.service_transfer_in_amount_yuan > 0 or dd.service_transfer_out_amount_yuan > 0 then 0
    else dd.refund_amount
end as refund_amount,
case
    when dd.service_transfer_in_amount_yuan > 0 or dd.service_transfer_out_amount_yuan > 0 then 0
    else dd.promit_amount
end as promit_amount,
case
    when dd.service_transfer_in_amount_yuan > 0 or dd.service_transfer_out_amount_yuan > 0 then 0
    when dd.refund_amount <= 0 then 0
    when dd.filled_course_first_level_department_name = 'H业务线'
     and dd.filled_course_second_level_department_name = '一对一学部' then dd.refund_amount
    when dd.clazz_name like '%点睛%'
     and coalesce(re_ke.full_refund_chain_finish_lesson_count, 0) < 2 then dd.refund_amount
    when (dd.clazz_name not like '%点睛%' or dd.clazz_name is null)
     and coalesce(re_ke.full_refund_chain_finish_lesson_count, 0) < 4 then dd.refund_amount
    else 0
end as refund_4
from dd
left join prc
  on prc.lead_id = dd.lead_id
 and prc.employee_email_name = dd.performance_employee_email_name
 and prc.rn = 1
left join re_ke
  on re_ke.order_number = dd.order_number
left join order_change
  on dd.order_number = order_change.order_number
)
-- 先汇总 uid 订单，并按完成度折算逻辑计算用户级破蛋口径
,udd as (
select
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
sum(case when is_on_period = 1 then income_amount else 0 end) as p_income,
sum(case when course_first_level_department_name = 'H业务线' then income_amount - refund_4 else 0 end) as H_promit_4,
sum(case when course_first_level_department_name != 'H业务线' then income_amount - refund_4 else 0 end) as n_H_promit_4,
sum(case when course_first_level_department_name = 'H业务线' and course_second_level_department_name = '一对一学部' then income_amount - refund_4 else 0 end) as Y_promit_4
from gmv
group by qici,qudao,grade_0,zhuguan,name,uid
)
-- 汇总订单至顾问
,ud as (
select
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
count(distinct case when ((H_promit_4 - Y_promit_4) + n_H_promit_4 * 0.5) > 0 then uid end) as podan,
sum(sc) as sc
from udd
group by qici,qudao,grade_0,zhuguan,name
)
-- 线索量
,bb as (
select qici,channel_map_1,channel_map_2,grade_1,virtual_direct_leader_email_name,employee_email_name,sum(v_lead) as v_lead
from(
select distinct f.*
,coalesce(
    lead_cal.qici,
    concat(cast(date_format(date_trunc('week', date_parse(replace(concat(group_period_year, group_period_term), '期', ''), '%Y%m%d') - interval '1' day) + interval '4' day, '%Y%m%d') as varchar), '期')
) qici
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
left join biz_qici_calendar lead_cal
  on cast(date_parse(replace(concat(group_period_year, group_period_term), '期', ''), '%Y%m%d') as date)
     between lead_cal.period_start_date and lead_cal.period_end_date
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
    qici,
    employee_email_name,
    xuebu,
    leader_employee_email_name,
    dazu,
    jingli
from temp_table.dingxi01_qing_team_jg
) jg on mm.employee_email_name = jg.employee_email_name and mm.qici = jg.qici)
