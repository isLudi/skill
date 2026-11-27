with biz_qici_calendar as (
select *
from (
    values
        ('20260710期', '0710期', '20260710期', '0710期', date '2026-07-06', date '2026-07-12'),
        ('20260716期', '0716期', '20260717期', '0717期', date '2026-07-13', date '2026-07-19'),
        ('20260722期', '0722期', '20260724期', '0724期', date '2026-07-20', date '2026-07-26'),
        ('20260728期', '0728期', '20260731期', '0731期', date '2026-07-27', date '2026-08-02'),
        ('20260803期', '0803期', '20260807期', '0807期', date '2026-08-03', date '2026-08-09'),
        ('20260808期', '0808期', '20260814期', '0814期', date '2026-08-10', date '2026-08-16'),
        ('20260815期', '0815期', '20260814期', '0814期', date '2026-08-17', date '2026-08-23'),
        ('20260821期', '0821期', '20260821期', '0821期', date '2026-08-24', date '2026-08-30')
) as t(qici, short_qici, legacy_qici, legacy_short_qici, period_start_date, period_end_date)
)
,douyin_refund_prelead_raw as (
select
    cast(f.lead_id as bigint) as prelead_id,
    f.rule_name as prelead_rule_name,
    f.employee_email_name,
    f.virtual_direct_leader_email_name,
    coalesce(
        f.stats_grade_name,
        f.lead_purchase_intention_level2_category_name,
        case
            when f.rule_name like '%高一%' then '高一'
            when f.rule_name like '%高二%' then '高二'
            when f.rule_name like '%高三%' then '高三'
            when f.rule_name like '%高中预科%' then '高中预科'
        end
    ) as grade_1,
    coalesce(
        lead_cal.qici,
        concat(
            cast(
                date_format(
                    date_trunc('week',
                        date_parse(
                            replace(concat(f.group_period_year, f.group_period_term), '期', ''),
                            '%Y%m%d'
                        )) + interval '4' day,
                    '%Y%m%d'
                ) as varchar
            ),
            '期'
        )
    ) as qici,
    coalesce(try_cast(f.valid_lead_count as bigint), 0) as valid_lead_count,
    row_number() over (
        partition by cast(f.lead_id as bigint)
        order by
            coalesce(try_cast(f.valid_lead_count as bigint), 0) desc,
            case when f.rule_name is not null then 0 else 1 end,
            case when f.employee_email_name is not null then 0 else 1 end,
            f.section_assign_time desc,
            f.employee_email_prefix
    ) as prelead_rn
from bdg_ba.app_crm_prelead_cost_gmv_full_link_data_hf f
left join biz_qici_calendar lead_cal
  on cast(
      try(
          date_parse(
              replace(concat(f.group_period_year, f.group_period_term), '期', ''),
              '%Y%m%d'
          )
      ) as date
  ) between lead_cal.period_start_date and lead_cal.period_end_date
where f.dt = format_datetime(NOW() - interval '2' hour, 'YYYYMMdd')
  and f.hour = format_datetime(NOW() - interval '3' hour, 'HH')
  and f.lead_model_type = 1
  and f.section_assign_employee_first_level_department_name = 'H业务线'
  and f.virtual_third_department_name = '学习顾问部'
  and f.virtual_fourth_department_name = 'SEC创新部'
  and f.rule_name like '%抖音正价退费%'
)
,douyin_refund_prelead as (
select
    p.prelead_id,
    p.prelead_rule_name,
    p.employee_email_name,
    p.virtual_direct_leader_email_name,
    p.grade_1,
    p.qici
from douyin_refund_prelead_raw p
join (
    select distinct qici, employee_email_name
    from temp_table.lvshuai01_jiagou_db
    where dept_2 = 'SEC'
      and qici is not null
      and employee_email_name is not null
) jg
  on p.qici = jg.qici
 and p.employee_email_name = jg.employee_email_name
where p.prelead_rn = 1
  and valid_lead_count > 0
  and p.employee_email_name is not null
)
,douyin_refund_transfer as (
select distinct
    p.prelead_id,
    cast(l.crm_leads_id as bigint) as transfer_lead_id,
    p.prelead_rule_name
from douyin_refund_prelead p
join data_lake_fuwu.dwd_crm_leads_rt l
  on cast(l.previous_model_id as bigint) = p.prelead_id
where l.model_type = 0
  and l.previous_model_id > 0
)
,lead_map as (
select lead_id,put_plan_name,employee_email_name,channel_name_1,channel_name_2,channel_name_3,flow_pool_name,get_customer_way_name
  ,rule_name,case
    WHEN LOWER(REPLACE(COALESCE(rule_name, ''), ' ', '')) LIKE '%app%' THEN '本地化'
    WHEN LOWER(REPLACE(COALESCE(rule_name, ''), ' ', '')) LIKE '%青橙付费-山东直播间-%' THEN '付费'
    WHEN LOWER(REPLACE(COALESCE(rule_name, ''), ' ', '')) LIKE '%青橙本地化-安徽app-%' THEN '本地化'
    WHEN (rule_name LIKE '%SEC内部未加好友%' OR rule_name LIKE '%SEC内部复用%') THEN '公海'
    WHEN LOWER(REPLACE(COALESCE(rule_name, ''), ' ', '')) LIKE '%青橙公海-0元信息流-%' THEN '公海'
    WHEN LOWER(REPLACE(COALESCE(rule_name, ''), ' ', '')) LIKE '%青橙公海-顾问未加好友-%' THEN '公海'
    WHEN LOWER(REPLACE(COALESCE(rule_name, ''), ' ', '')) LIKE '%青橙本地化-河南未加好友-%' THEN '本地化'
    WHEN LOWER(REPLACE(COALESCE(rule_name, ''), ' ', '')) LIKE '%青橙本地化-河南私域-%' THEN '本地化'
    WHEN LOWER(REPLACE(COALESCE(rule_name, ''), ' ', '')) LIKE '%青橙本地化-河南app-%' THEN '本地化'
    WHEN rule_name LIKE '%青橙私域-表单浙江-%' OR rule_name = '表单浙江' THEN '私域'
    WHEN rule_name LIKE '%青橙私域-表单江苏-%' OR rule_name = '表单江苏' THEN '私域'
    when rule_name like '%私域裂变%' then '私域'
    when rule_name like '%公域自然流%' then '公域'
    when rule_name like '%公域-自然流%' then '公域'
    when rule_name like '%内部图书%' then '图书'
    when rule_name like '%SEC内部未加好友%' then '公海'
when (
    replace(coalesce(rule_name, ''), ' ', '') like '%青橙IP-招生退费-春春%'
    or replace(coalesce(rule_name, ''), ' ', '') like '%青橙IP-招生退费-朱博士%'
    or replace(coalesce(rule_name, ''), ' ', '') like '%青橙IP-招生退费-郭艺%'
) then 'IP退费'
when rule_name like '%抖音正价退费%' then '抖音复用'
when (rule_name like '%赠失-星义%'
  or rule_name like '%赠失-朱博士%'
  or rule_name like '%赠失-春春%'
  or rule_name like '%赠失-郭艺%'
  or rule_name like '%赠失-亚飞%'
  or rule_name like '%青橙IP%') then concat('IP', chr(36192), chr(35838), chr(22833), chr(36133))
when (rule_name like '%私域本地化%'
  or rule_name like '%河南本地化%'
  or rule_name like '%青橙本地化%') then '本地化'
when (rule_name like '%私域会话%'
  or rule_name like '%私域表单%'
  or rule_name like '%私域品效%'
  or rule_name like '%私域图书%') then '私域'
when rule_name like '%公域-自然流%' then '公域'
when (rule_name like '%公域学霸%'
  or rule_name like '%青橙公域%') then '公域'
when (rule_name like '%武汉图书%'
  or rule_name like '%西安图书%') then '图书'
when rule_name like '%亚飞IP%' then '主讲IP'
when (rule_name like '%SEC未加好友%'
  or rule_name like '%SEC首期掉海%'
  or rule_name like '%SEC招生退费%'
  or rule_name like '%招生退费%') then '公海'
when (rule_name like '%顾问未加好友%'
  or rule_name like '%公海%') then '公海'
when rule_name like '%抖音私信%' then '抖音私信'
when (rule_name like '%进校9元%'
  or rule_name like '%进校%') then '进校9元'
else '未知' end as channel_map_1
,case
    WHEN LOWER(REPLACE(COALESCE(rule_name, ''), ' ', '')) LIKE '%青橙公海-sec一对一复用-%' THEN 'SEC一对一复用'
    WHEN LOWER(REPLACE(COALESCE(rule_name, ''), ' ', '')) LIKE '%青橙公海-secai提效复用-%' THEN 'SECAI提效复用'
    WHEN LOWER(REPLACE(COALESCE(rule_name, ''), ' ', '')) LIKE '%青橙公海-sec进校复用-%' THEN 'SEC进校复用'
    WHEN LOWER(REPLACE(COALESCE(rule_name, ''), ' ', '')) LIKE '%app%' THEN 'APP'
    WHEN LOWER(REPLACE(COALESCE(rule_name, ''), ' ', '')) LIKE '%青橙付费-山东直播间-%' THEN '山东直播间'
    WHEN LOWER(REPLACE(COALESCE(rule_name, ''), ' ', '')) LIKE '%青橙本地化-安徽app-%' THEN 'APP'
    WHEN (rule_name LIKE '%SEC内部未加好友%' OR rule_name LIKE '%SEC内部复用%') THEN 'SEC内部复用'
    WHEN LOWER(REPLACE(COALESCE(rule_name, ''), ' ', '')) LIKE '%青橙公海-0元信息流-%' THEN '0元信息流'
    WHEN LOWER(REPLACE(COALESCE(rule_name, ''), ' ', '')) LIKE '%青橙公海-顾问未加好友-%' THEN '顾问未加好友'
    WHEN LOWER(REPLACE(COALESCE(rule_name, ''), ' ', '')) LIKE '%青橙本地化-河南未加好友-%' THEN '河南未加好友'
    WHEN LOWER(REPLACE(COALESCE(rule_name, ''), ' ', '')) LIKE '%青橙本地化-河南私域-%' THEN '河南私域'
    WHEN LOWER(REPLACE(COALESCE(rule_name, ''), ' ', '')) LIKE '%青橙本地化-河南app-%' THEN 'APP'
    WHEN rule_name LIKE '%青橙私域-表单浙江-%' OR rule_name = '表单浙江' THEN '表单浙江'
    WHEN rule_name LIKE '%青橙私域-表单江苏-%' OR rule_name = '表单江苏' THEN '表单江苏'
    when rule_name like '%私域裂变%' then '私域裂变'
    when rule_name like '%公域自然流%' then '公域自然流'
    when rule_name like '%公域-自然流%' then '公域自然流'
    when rule_name like '%内部图书%' then '内部图书'
    when rule_name like '%SEC内部未加好友%' then 'SEC内部复用'
when replace(coalesce(rule_name, ''), ' ', '') like '%青橙IP-招生退费-春春%' then '春春'
when replace(coalesce(rule_name, ''), ' ', '') like '%青橙IP-招生退费-朱博士%' then '朱博士'
when replace(coalesce(rule_name, ''), ' ', '') like '%青橙IP-招生退费-郭艺%' then '郭艺'
when rule_name like '%抖音正价退费%' then '抖音正价退费'
when rule_name like '%赠失-星义%' then '星义IP'
when rule_name like '%赠失-朱博士%' then '朱博士IP'
when rule_name like '%赠失-春春%' then '春春IP'
when rule_name like '%赠失-郭艺%' then '郭艺IP'
when rule_name like '%赠失-亚飞%' then '亚飞IP'
when rule_name like '%青橙IP%' then '亚飞IP'
when rule_name like '%私域会话%' then '私域会话'
when rule_name like '%私域表单%' then '私域表单'
when rule_name like '%私域图书%' then '私域图书'
when rule_name like '%私域品效%' then '私域品效'
when rule_name like '%私域本地化%' then '河南私域'
when (rule_name like '%河南本地化%'
  or rule_name like '%青橙本地化%') then 'APP'
when rule_name like '%亚飞IP%' then '亚飞IP'
when rule_name like '%SEC未加好友%' then 'SEC未加好友'
when rule_name like '%SEC首期掉海%' then 'SEC首期掉海'
when (rule_name like '%SEC招生退费%'
  or rule_name like '%招生退费%') then 'SEC招生退费'
when (rule_name like '%顾问未加好友%'
  or rule_name like '%公海%') then '顾问未加好友'
when rule_name like '%武汉图书%' then '武汉图书'
when rule_name like '%西安图书%' then '西安图书'
when rule_name like '%公域-自然流%' then '自然流'
when (rule_name like '%公域学霸%'
  or rule_name like '%青橙公域%') then '公域学霸'
when rule_name like '%抖音私信%' then '抖音私信'
when (rule_name like '%进校9元%'
  or rule_name like '%进校%') then '进校9元'
else '未知' end as rule_name0
,case
when rule_name like '%高一%' then '高一'
when rule_name like '%高二%' then '高二'
when rule_name like '%高三%' then '高三'
when rule_name like '%初二%' then '初二'
when rule_name like '%初三%' then '初三'
else lead_purchase_intention_level2_category_name end as grade_0,
virtual_direct_leader_email_name,
section_assign_time
from (
    select
           f.lead_id,
           f.put_plan_name,
           f.employee_email_name,
           f.channel_name_1,
           f.channel_name_2,
           f.channel_name_3,
           f.flow_pool_name,
           f.get_customer_way_name,
           coalesce(t.prelead_rule_name, f.rule_name) as rule_name,
           f.lead_purchase_intention_level2_category_name,
           f.virtual_direct_leader_email_name,
           f.section_assign_time,
           row_number() over (
               partition by f.lead_id, f.employee_email_name
               order by f.section_assign_time desc,
                        regexp_extract(coalesce(t.prelead_rule_name, f.rule_name), '(\d{4}期)', 1) desc
           ) as rn
    from bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df f
    left join douyin_refund_transfer t
      on cast(f.lead_id as bigint) = t.transfer_lead_id
    where f.dt=format_datetime(NOW()-interval '2' hour,'YYYYMMdd') and f.hour=format_datetime(NOW()-interval '3' hour,'HH')
      and f.section_assign_employee_first_level_department_name = 'H业务线'
      and f.section_assign_employee_second_level_department_name = '青橙项目部'
      and f.period_mapping_first_level_department_name = 'H业务线'
      and f.period_mapping_second_level_department_name in ('精品班学部', '菁英班学部', '市场部', '青橙项目部')
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
base.channel_map_1,
base.rule_name0,
base.rule_name,
coalesce(
    period_cal.short_qici,
    regexp_extract(base.rule_name, '(\d{4}期)', 1)
) as qici0,
base.grade_0,
base.qici,
regexp_extract(base.qici, '\d{4}(\d{4}期)', 1) as period,
base.virtual_direct_leader_email_name,
base.cycle_section_assign_time
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
ld.channel_map_1,
ld.rule_name0,
ld.rule_name,
ld.grade_0,
ld.virtual_direct_leader_email_name,
ld.section_assign_time as cycle_section_assign_time,
coalesce(
    trade_cal.qici,
    concat(date_format(date_trunc('week', cast(gmv.trade_timestamp as timestamp)) + interval '4' day, '%Y%m%d'), '期')
) as qici
from service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf gmv
left join biz_qici_calendar trade_cal
  on cast(gmv.trade_timestamp as date) between trade_cal.period_start_date and trade_cal.period_end_date
left join lead_map ld
  on gmv.lead_id = ld.lead_id
 and ld.employee_email_name = gmv.performance_employee_email_name
where gmv.dt=format_datetime(NOW()-interval '2' hour,'YYYYMMdd')
  and gmv.hour=format_datetime(NOW()-interval '3' hour,'HH')
  and gmv.performance_second_level_department_name='青橙项目部'
  and gmv.course_first_level_department_name in ('H业务线','LL业务线','TUTU','TT','A业务线','EM业务线','TT业务线','创新中心')
  and gmv.course_second_level_department_name in ('V项目部','本地化部','私域营销组','青少成长学部','创新技术组','成长中心供应链组','APP运营组','英语产品部','职场服务部','用户平台部','微师产品部','上海中心综合部','CAL技术组','财务核算部','财经项目部','人才发展部','财务信息化部','图书项目部（关闭）','运营部','基础架构组','数学产品部','营销产品部','雅思学部','商品部','磨课组','升学规划部','升学规划中心','郑州中心','组织部','留学申请学部','质检部','架构平台部','师训组','投放商务组','系统班部','编程素养学部','市场运营组','项目运营组','KM技术组','二讲老师部','成都中心综合部','业务设计部','专题课部','微师职教产品部','高校学部','教学服务部','平台产品部','数字化学部','品牌运营组','校长办公室','运营中心财务','视效部','数据与商业分析中心','X项目','教学产品部','XA学部','语言学部','图书产品部','主播部','业务支持部','HL技术组','武汉中心综合部','成人供应链组','途途课堂','信息平台部','HL经营分析组','大数据部','直播运营组','市场部','金刚产品部','教学产品运营中心','平台电商组','企业效能部','品牌与内容部','产品研发部','小学部','技术质量部','财务报告部','税务部','用户产品部','直播二部','招聘部','HR共享中心','清北','增长策略部','督察部','商品运营部','资金管理部','美好家庭学部','设计支持中心','初中部','AIGC创新部','财务部','人力资源部','人才保障部一部','CAL经营分析组','基础技术部','综合素养学部','热线呼入部','品牌部','语文产品部','供应链部','题库','GZ学部','政府关系部','HRBP部','招生运营部','督检组','耀师项目部','产品运营部','营运部','多媒体技术部','跟谁学郑州中心(失效）','人工智能部','体验设计部','狮王项目部','资产服务部','专升本项目部','基础技术部(失效)','郑州中心综合部','考研学部','线上考研学部','内容营销组','公关部','公职学部','客服部','运营平台部','CS学部','财务FP&A部','商学院学部','行政部','直播三部','营销技术部','私域运营组','飞花产品部','星火产品部','客户端技术部','薪酬绩效部','图书项目部','NJ学部','直播一部','法务部','在线服务部','履约部','KML经营分析组','社会保障部','精品班部','教学教研部','医疗项目部','菁英班部','菁英班学部','精品班学部','一对一学部','北京学部','图书学部','河南学部','清北班学部','湖广学部','山西学部','K学部','M学部','大学生学习学部','合肥学校','太原学校','苏州学校','郑州学校','北京学校','上海学校','运营中心','广州学校','市场中心','南京学校','深圳学校','成都学校','财务中心','武汉学校','济南学校','天津学校','学校办公室','重庆学校','西安学校','长沙学校','市场二部','留学学部','国际考试学部','出国语培线下项目','广州学校（IE）','国际竞赛项目','剑桥英语项目','上海学校（IE）','心理学部','创新项目部','创新学部','素质成长学部','国际考试在线学部','毛豆学部','青少学部','市场三部','市场四部','青橙项目部','文旅学部','本地化大班学部','市场营销部','直播市场部','创新增长部','学习规划中心','素养初中学部','素养青藤学部','素养小学学部','用户运营部','经营策略部','校园招聘','直播创新部','战略创新部','产研部','业务研发部','教学质量部','Theta项目部','AI素养学部','文旅项目','Theta智学项目部','Theta产研部','V学部','TT初中学部','TT小学学部','产研部','T学部','专题课部（失效）','初中组','文旅项目（失效）', '语言一对一学部')
  and (gmv.income_amount <>0 or gmv.refund_amount <> 0)
) base
left join biz_qici_calendar period_cal
  on base.qici = period_cal.qici
 and regexp_extract(base.rule_name, '(\d{4}期)', 1) = period_cal.legacy_short_qici
where base.qici >= '20260925期'
)
,course_transfer_order_rows as (
select
    latest_child_order_number as order_number,
    parent_order_number,
    original_order_number,
    cast(coalesce(transfer_in_amount, 0) as double) / 100.0 as transfer_in_amount_yuan,
    cast(coalesce(transfer_out_amount, 0) as double) / 100.0 as transfer_out_amount_yuan
from finance_dw.dim_finance_order_change_df
where dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
  and latest_child_order_status in (2, 6, 7)
  and biz_type in (2, 7)
  and order_change_type = 1
  and latest_child_order_number is not null
)
,course_transfer_order as (
select
    order_number,
    max(parent_order_number) as parent_order_number,
    max(original_order_number) as original_order_number,
    max(transfer_in_amount_yuan) as transfer_in_amount_yuan,
    max(transfer_out_amount_yuan) as transfer_out_amount_yuan
from course_transfer_order_rows
group by order_number
)
,course_transfer_finance_detail as (
select
    f.order_number,
    f.user_id as target_user_number,
    f.employee_email_name,
    cast(f.trade_time as timestamp) as trade_time,
    f.clazz_name,
    f.course_grade,
    case
        when f.course_subject like '%英语%' or f.course_subject like '%英文%' then '英语'
        when f.course_subject like '%语文%' then '语文'
        when f.course_subject like '%数学%' then '数学'
        when f.course_subject like '%物理%' then '物理'
        when f.course_subject like '%化学%' then '化学'
        when f.course_subject like '%历史%' then '历史'
        when f.course_subject like '%政治%' then '政治'
        when f.course_subject like '%生物%' then '生物'
        when f.course_subject like '%地理%' then '地理'
        when f.course_subject like '%日语%' then '日语'
        else f.course_subject
    end as mapping_school_subject_name,
    f.course_first_level_department_name,
    f.course_second_level_department_name,
    cast(coalesce(f.price, 0) as double) as income_amount,
    o.transfer_in_amount_yuan,
    o.transfer_out_amount_yuan
from finance_dw.app_finance_performance_extend_details_hf f
inner join course_transfer_order o
  on f.order_number = o.order_number
where f.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
  and f.hour = format_datetime(now() - interval '3' hour, 'HH')
  and f.employee_first_level_department_name = 'H业务线'
  and f.employee_second_level_department_name = '青橙项目部'
  and f.course_first_level_department_name in (
      'H业务线', 'LL业务线', 'TUTU', 'TT', 'A业务线',
      'EM业务线', 'TT业务线'
  )
  and f.course_second_level_department_name in (
      '精品班学部', '菁英班学部', '一对一学部', '图书学部', '本地化大班学部', '语言一对一学部'
  )
  and cast(f.trade_time as date) >= date '2026-07-20'
  and f.trade_type = '调课调班'
  and f.trade_status like '%支付%'
  and f.price > 0
)
,course_transfer_finance as (
select
    order_number,
    target_user_number,
    employee_email_name,
    min(trade_time) as trade_time,
    max(clazz_name) as clazz_name,
    max(course_grade) as course_grade,
    mapping_school_subject_name,
    max(course_first_level_department_name) as course_first_level_department_name,
    max(course_second_level_department_name) as course_second_level_department_name,
    sum(income_amount) as income_amount,
    max(transfer_in_amount_yuan) as transfer_in_amount_yuan,
    max(transfer_out_amount_yuan) as transfer_out_amount_yuan
from course_transfer_finance_detail
group by
    order_number,
    target_user_number,
    employee_email_name,
    mapping_school_subject_name
)
,course_transfer_protected_finance as (
select
    f.*,
    p.lead_id,
    cast(p.assign_time as timestamp) as section_assign_time,
    row_number() over (
        partition by f.order_number, f.mapping_school_subject_name
        order by
            cast(p.assign_time as timestamp) desc,
            p.private_sea_update_time desc,
            p.private_sea_id desc
    ) as protection_rank
from course_transfer_finance f
inner join service_dw.dwd_crm_assign_private_detail_hf p
  on cast(p.user_number as varchar) = cast(f.target_user_number as varchar)
 and p.employee_email_name = f.employee_email_name
where p.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
  and p.hour = format_datetime(now() - interval '3' hour, 'HH')
  and p.model_type = 0
  and p.is_del = 0
  and p.assign_employee_first_level_department_name = 'H业务线'
  and p.assign_employee_second_level_department_name = '青橙项目部'
  and cast(p.assign_time as timestamp) <= f.trade_time
  and (
      try_cast(p.close_time as timestamp) is null
      or try_cast(p.close_time as timestamp) = timestamp '1970-01-01 08:00:00'
      or try_cast(p.close_time as timestamp) > f.trade_time
  )
  and coalesce(
      try_cast(p.fall_sea_time as timestamp),
      timestamp '9999-12-31 23:59:59'
  ) > f.trade_time
)
,course_transfer_base as (
select
    f.lead_id,
    f.target_user_number as original_order_user_number,
    f.order_number,
    f.employee_email_name as performance_employee_email_name,
    f.mapping_school_subject_name,
    f.trade_time as trade_timestamp,
    cast(null as varchar) as trade_group_period_name,
    cast(null as varchar) as pay_group_period_name,
    f.clazz_name,
    f.income_amount,
    cast(0 as double) as refund_amount,
    f.income_amount as promit_amount,
    case
        when f.course_first_level_department_name is not null then f.course_first_level_department_name
        when f.course_grade like '%小学%' or f.course_grade like '%初%' then '小初业务线'
        else 'H业务线'
    end as filled_course_first_level_department_name,
    case
        when f.course_second_level_department_name is not null then f.course_second_level_department_name
        when f.course_first_level_department_name = 'H业务线' then '精品班学部'
        when f.course_first_level_department_name is null
         and not (f.course_grade like '%小学%' or f.course_grade like '%初%') then '精品班学部'
        else f.course_second_level_department_name
    end as filled_course_second_level_department_name,
    f.transfer_in_amount_yuan as service_transfer_in_amount_yuan,
    f.transfer_out_amount_yuan as service_transfer_out_amount_yuan,
    ld.channel_map_1,
    ld.rule_name0,
    ld.rule_name,
    ld.grade_0,
    ld.virtual_direct_leader_email_name,
    f.section_assign_time as protected_section_assign_time,
    coalesce(
        trade_cal.qici,
        concat(date_format(date_trunc('week', f.trade_time) + interval '4' day, '%Y%m%d'), '期')
    ) as qici
from course_transfer_protected_finance f
inner join lead_map ld
  on f.lead_id = ld.lead_id
 and f.employee_email_name = ld.employee_email_name
left join biz_qici_calendar trade_cal
  on cast(f.trade_time as date) between trade_cal.period_start_date and trade_cal.period_end_date
where f.protection_rank = 1
)
,course_transfer_dd as (
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
    base.channel_map_1,
    base.rule_name0,
    base.rule_name,
    coalesce(
        period_cal.short_qici,
        regexp_extract(base.rule_name, '(\d{4}期)', 1)
    ) as qici0,
    base.grade_0,
    base.qici,
    regexp_extract(base.qici, '\d{4}(\d{4}期)', 1) as period,
    base.virtual_direct_leader_email_name,
    base.protected_section_assign_time
from course_transfer_base base
left join biz_qici_calendar period_cal
  on base.qici = period_cal.qici
 and regexp_extract(base.rule_name, '(\d{4}期)', 1) = period_cal.legacy_short_qici
where base.qici >= '20260925期'
)
-- lead期次+分配时间
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
    max(1) as has_order_change,
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
  and a.course_second_level_department_name in ('V项目部','本地化部','私域营销组','青少成长学部','创新技术组','成长中心供应链组','APP运营组','英语产品部','职场服务部','用户平台部','微师产品部','上海中心综合部','CAL技术组','财务核算部','财经项目部','人才发展部','财务信息化部','图书项目部（关闭）','运营部','基础架构组','数学产品部','营销产品部','雅思学部','商品部','磨课组','升学规划部','升学规划中心','郑州中心','组织部','留学申请学部','质检部','架构平台部','师训组','投放商务组','系统班部','编程素养学部','市场运营组','项目运营组','KM技术组','二讲老师部','成都中心综合部','业务设计部','专题课部','微师职教产品部','高校学部','教学服务部','平台产品部','数字化学部','品牌运营组','校长办公室','运营中心财务','视效部','数据与商业分析中心','X项目','教学产品部','XA学部','语言学部','图书产品部','主播部','业务支持部','HL技术组','武汉中心综合部','成人供应链组','途途课堂','信息平台部','HL经营分析组','大数据部','直播运营组','市场部','金刚产品部','教学产品运营中心','平台电商组','企业效能部','品牌与内容部','产品研发部','小学部','技术质量部','财务报告部','税务部','用户产品部','直播二部','招聘部','HR共享中心','清北','增长策略部','督察部','商品运营部','资金管理部','美好家庭学部','设计支持中心','初中部','AIGC创新部','财务部','人力资源部','人才保障部一部','CAL经营分析组','基础技术部','综合素养学部','热线呼入部','品牌部','语文产品部','供应链部','题库','GZ学部','政府关系部','HRBP部','招生运营部','督检组','耀师项目部','产品运营部','营运部','多媒体技术部','跟谁学郑州中心(失效）','人工智能部','体验设计部','狮王项目部','资产服务部','专升本项目部','基础技术部(失效)','郑州中心综合部','考研学部','线上考研学部','内容营销组','公关部','公职学部','客服部','运营平台部','CS学部','财务FP&A部','商学院学部','行政部','直播三部','营销技术部','私域运营组','飞花产品部','星火产品部','客户端技术部','薪酬绩效部','图书项目部','NJ学部','直播一部','法务部','在线服务部','履约部','KML经营分析组','社会保障部','精品班部','教学教研部','医疗项目部','菁英班部','菁英班学部','精品班学部','一对一学部','北京学部','图书学部','河南学部','清北班学部','湖广学部','山西学部','K学部','M学部','大学生学习学部','合肥学校','太原学校','苏州学校','郑州学校','北京学校','上海学校','运营中心','广州学校','市场中心','南京学校','深圳学校','成都学校','财务中心','武汉学校','济南学校','天津学校','学校办公室','重庆学校','西安学校','长沙学校','市场二部','留学学部','国际考试学部','出国语培线下项目','广州学校（IE）','国际竞赛项目','剑桥英语项目','上海学校（IE）','心理学部','创新项目部','创新学部','素质成长学部','国际考试在线学部','毛豆学部','青少学部','市场三部','市场四部','青橙项目部','文旅学部','本地化大班学部','市场营销部','直播市场部','创新增长部','学习规划中心','素养初中学部','素养青藤学部','素养小学学部','用户运营部','经营策略部','校园招聘','直播创新部','战略创新部','产研部','业务研发部','教学质量部','Theta项目部','AI素养学部','文旅项目','Theta智学项目部','Theta产研部','V学部','TT初中学部','TT小学学部','产研部','T学部','专题课部（失效）','初中组','文旅项目（失效）', '语言一对一学部')
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
,service_gmv as (
select
dd.qici,dd.channel_map_1,dd.rule_name0 as qudao,dd.qici0,
case when dd.qici0 = dd.period then 1 else 0 end as is_on_period,
dd.grade_0,dd.lead_id,dd.original_order_user_number as uid,
dd.performance_employee_email_name as name,dd.virtual_direct_leader_email_name as zhuguan,
dd.mapping_school_subject_name as sub,
dd.trade_timestamp,
dd.trade_group_period_name,
dd.pay_group_period_name,
dd.cycle_section_assign_time as section_assign_time,
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
end as refund_4,
case when nullif(trim(dd.rule_name), '') is not null then dd.rule_name end as rule_name
from dd
left join re_ke
  on re_ke.order_number = dd.order_number
left join order_change
  on dd.order_number = order_change.order_number
)
,course_transfer_gmv as (
select
    c.qici,
    c.channel_map_1,
    c.rule_name0 as qudao,
    c.qici0,
    case when c.qici0 = c.period then 1 else 0 end as is_on_period,
    c.grade_0,
    c.lead_id,
    c.original_order_user_number as uid,
    c.performance_employee_email_name as name,
    c.virtual_direct_leader_email_name as zhuguan,
    c.mapping_school_subject_name as sub,
    c.trade_timestamp,
    c.trade_group_period_name,
    c.pay_group_period_name,
    c.protected_section_assign_time as section_assign_time,
    c.filled_course_first_level_department_name as course_first_level_department_name,
    c.filled_course_second_level_department_name as course_second_level_department_name,
    c.clazz_name,
    cast(0 as bigint) as re_lc,
    cast(1 as bigint) as main_has_order_change,
    c.service_transfer_in_amount_yuan as main_transfer_in_amount_yuan,
    c.service_transfer_out_amount_yuan as main_transfer_out_amount_yuan,
    c.service_transfer_in_amount_yuan,
    c.service_transfer_out_amount_yuan,
    cast(0 as bigint) as is_internal_order_change_amount,
    c.income_amount,
    c.refund_amount,
    c.promit_amount,
    cast(0 as double) as refund_4,
    case when nullif(trim(c.rule_name), '') is not null then c.rule_name end as rule_name
from course_transfer_dd c
)
,gmv as (
select * from service_gmv
union all
select * from course_transfer_gmv
)
,legacy_udd as (
select
qici,channel_map_1,qudao,grade_0,zhuguan,name,uid,
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
group by qici,channel_map_1,qudao,grade_0,zhuguan,name,uid
)
-- Cohort totals use the established adviser and uid keys.
-- Put each qualifying count on its first contributing rule. Equal times sort by rule.
,order_rule_rank as (
    select gmv.*,
        row_number() over (
            partition by qici, channel_map_1, qudao, grade_0, zhuguan, name, uid, sub
            order by case when income_amount > 0 then 0 else 1 end,
                trade_timestamp,
                case when rule_name is null then 1 else 0 end, rule_name
        ) as paid_subject_rn,
        row_number() over (
            partition by qici, channel_map_1, qudao, grade_0, zhuguan, name, uid, sub
            order by case when income_amount > 0 and is_on_period = 1 then 0 else 1 end,
                trade_timestamp,
                case when rule_name is null then 1 else 0 end, rule_name
        ) as period_subject_rn
    from gmv
)
,udd as (
    select
        qici, channel_map_1, qudao, grade_0, zhuguan, name, uid, rule_name,
        min(case when income_amount > 0 then trade_timestamp end) as first_payment,
        min(case when income_amount > 0 and is_on_period = 1 then trade_timestamp end) as first_period_payment,
        min(case when refund_amount > 0 then trade_timestamp end) as first_refund,
        sum(case when income_amount > 0 and sub <> '定制方案' and paid_subject_rn = 1 then 1 else 0 end) as pay_sub,
        sum(case when income_amount > 0 and is_on_period = 1 and sub <> '定制方案'
              and period_subject_rn = 1 then 1 else 0 end) as p_pay_sub,
        sum(income_amount) as income,
        sum(refund_amount) as refund,
        sum(promit_amount) as promit,
        sum(case when is_on_period = 1 then income_amount else 0 end) as p_income
    from order_rule_rank
    group by qici, channel_map_1, qudao, grade_0, zhuguan, name, uid, rule_name
)
,udd_legacy as (
    select udd.*,
        original.income as old_income,
        original.p_income as old_p_income,
        original.refund as old_refund,
        (original.h_promit_4 - original.y_promit_4) + original.n_h_promit_4 * 0.5 as old_podan_amount,
        original.sc as old_sc,
        row_number() over (
            partition by udd.qici, udd.channel_map_1, udd.qudao, udd.grade_0, udd.zhuguan, udd.name, udd.uid
            order by case when udd.first_payment is null then 1 else 0 end, udd.first_payment,
                case when udd.rule_name is null then 1 else 0 end, udd.rule_name
        ) as paid_rule_rn,
        row_number() over (
            partition by udd.qici, udd.channel_map_1, udd.qudao, udd.grade_0, udd.zhuguan, udd.name, udd.uid
            order by case when udd.first_period_payment is null then 1 else 0 end, udd.first_period_payment,
                case when udd.rule_name is null then 1 else 0 end, udd.rule_name
        ) as paid_period_rule_rn,
        row_number() over (
            partition by udd.qici, udd.channel_map_1, udd.qudao, udd.grade_0, udd.zhuguan, udd.name, udd.uid
            order by case when udd.first_refund is null then 1 else 0 end, udd.first_refund,
                case when udd.rule_name is null then 1 else 0 end, udd.rule_name
        ) as refund_rule_rn
    from udd
    left join legacy_udd original
      on udd.qici is not distinct from original.qici
     and udd.channel_map_1 is not distinct from original.channel_map_1
     and udd.qudao is not distinct from original.qudao
     and udd.grade_0 is not distinct from original.grade_0
     and udd.zhuguan is not distinct from original.zhuguan
     and udd.name is not distinct from original.name
     and udd.uid is not distinct from original.uid
)
,ud as (
    select
        qici, channel_map_1, qudao, grade_0, zhuguan, name, rule_name,
        count(distinct case when old_income > 0 and paid_rule_rn = 1 then uid end) as pay_user,
        count(distinct case when old_income > 0 and old_p_income > 0 and paid_period_rule_rn = 1 then uid end) as p_pay_user,
        sum(pay_sub) as pay_sub,
        sum(p_pay_sub) as p_pay_sub,
        sum(income) as income,
        sum(refund) as refund,
        sum(promit) as promit,
        sum(p_income) as p_income,
        count(distinct case when old_refund > 500 and refund_rule_rn = 1 then uid end) as refund_user,
        count(distinct case when old_podan_amount > 0 and paid_rule_rn = 1 then uid end) as podan,
        sum(case when paid_rule_rn = 1 then old_sc end) as sc
    from udd_legacy
    group by qici, channel_map_1, qudao, grade_0, zhuguan, name, rule_name
)
-- 合并链路主键：统计明细中的 lead_core_id 是跨小时稳定的根线索键。
-- lead_derivative_dependence_leads_id 仅作为衍生依赖字段，
-- 不将其猜测成 merged_to_lead_id。
,normal_lead_merge_keys_raw as (
    select
        cast(s.lead_id as bigint) as lead_id,
        nullif(try_cast(s.lead_core_id as bigint), 0) as merge_root_lead_id,
        row_number() over (
            partition by cast(s.lead_id as bigint)
            order by
                coalesce(try_cast(s.trace_update_time as timestamp), timestamp '1970-01-01 00:00:00') desc,
                coalesce(try_cast(s.latest_trace_id as bigint), 0) desc,
                coalesce(try_cast(s.lead_core_id as bigint), 0) desc
        ) as stats_rn
    from service_dw.dm_crm_lead_stats_detail_hf s
    where s.dt = format_datetime(NOW() - interval '3' hour, 'YYYYMMdd')
      and s.hour = format_datetime(NOW() - interval '3' hour, 'HH')
      and s.mapping_first_level_department_name = 'H业务线'
      and s.mapping_second_level_department_name in (
          '精品班学部',
          '菁英班学部',
          '市场部',
          '本地化大班学部',
          '青橙项目部'
      )
),
normal_lead_merge_keys as (
    select
        lead_id,
        merge_root_lead_id
    from normal_lead_merge_keys_raw
    where stats_rn = 1
),

-- 本地化merge-only按本次分配唯一校验；普通有效、财务及抖音私信口径保持。
local_merge_allocation_keys AS (
SELECT DISTINCT
  f.group_period_year AS source_period_year,
  f.group_period_term AS source_period_term,
  f.lead_id,
  f.employee_email_prefix,
  f.section_assign_time
FROM bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df AS f
WHERE
  f.dt = FORMAT_DATETIME(CURRENT_TIMESTAMP - INTERVAL '2' HOUR, 'YYYYMMdd')
  AND f.hour = FORMAT_DATETIME(CURRENT_TIMESTAMP - INTERVAL '3' HOUR, 'HH')
  AND f.section_assign_employee_first_level_department_name = 'H业务线'
  AND f.section_assign_employee_second_level_department_name = '青橙项目部'
  AND f.period_mapping_first_level_department_name = 'H业务线'
  AND f.period_mapping_second_level_department_name IN ('精品班学部', '菁英班学部', '市场部', '青橙项目部')
  AND (
    COALESCE(TRY_CAST(f.valid_lead_count AS BIGINT), 0) = 0
    AND COALESCE(TRY_CAST(f.merge_valid_lead_count AS BIGINT), 0) > 0
    AND (
      REPLACE(COALESCE(f.rule_name, ''), ' ', '') LIKE '%青橙本地化%'
      OR REPLACE(COALESCE(f.rule_name, ''), ' ', '') LIKE '%河南本地化%'
      OR REPLACE(COALESCE(f.rule_name, ''), ' ', '') LIKE '%私域本地化%'
    )
  )
),
local_merge_allocation_resolved AS (
SELECT
  k.source_period_year,
  k.source_period_term,
  k.lead_id,
  k.employee_email_prefix,
  k.section_assign_time,
  COUNT(r.lead_id) AS assignment_match_count,
  MAX(r.rule_name) AS actual_assignment_rule
FROM local_merge_allocation_keys AS k
LEFT JOIN service_dw.dim_crm_assign_rule_lead_detail_hf AS r
  ON r.lead_id = k.lead_id
  AND r.account_domain = k.employee_email_prefix
  AND r.create_time BETWEEN TRY_CAST(k.section_assign_time AS TIMESTAMP) - INTERVAL '1' SECOND AND TRY_CAST(k.section_assign_time AS TIMESTAMP) + INTERVAL '1' SECOND
  AND r.dt = FORMAT_DATETIME(CURRENT_TIMESTAMP - INTERVAL '2' HOUR, 'YYYYMMdd')
  AND r.hour = FORMAT_DATETIME(CURRENT_TIMESTAMP - INTERVAL '3' HOUR, 'HH')
  AND r.state IN (1, 3)
  AND r.fail_reason = 0
GROUP BY
  k.source_period_year,
  k.source_period_term,
  k.lead_id,
  k.employee_email_prefix,
  k.section_assign_time
),
normal_lead_state_raw as (
SELECT
  f.*,
  COALESCE(
    lead_cal.qici,
    CONCAT(
      CAST(DATE_FORMAT(
        DATE_TRUNC(
          'WEEK',
          DATE_PARSE(REPLACE(CONCAT(group_period_year, group_period_term), '期', ''), '%Y%m%d')
        ) + INTERVAL '4' DAY,
        '%Y%m%d'
      ) AS VARCHAR),
      '期'
    )
  ) AS derived_qici,
  COALESCE(TRY_CAST(f.valid_lead_count AS BIGINT), 0) AS source_valid_lead_count,
  COALESCE(TRY_CAST(f.merge_valid_lead_count AS BIGINT), 0) AS source_merge_valid_lead_count,
  mk.merge_root_lead_id,
  ma.assignment_match_count AS local_merge_assignment_match_count,
  ma.actual_assignment_rule AS local_merge_actual_assignment_rule
FROM bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df AS f
LEFT JOIN biz_qici_calendar AS lead_cal
  ON CAST(DATE_PARSE(REPLACE(CONCAT(group_period_year, group_period_term), '期', ''), '%Y%m%d') AS DATE) BETWEEN lead_cal.period_start_date AND lead_cal.period_end_date
LEFT JOIN douyin_refund_transfer AS t
  ON CAST(f.lead_id AS BIGINT) = t.transfer_lead_id
LEFT JOIN normal_lead_merge_keys AS mk
  ON CAST(f.lead_id AS BIGINT) = mk.lead_id
LEFT JOIN local_merge_allocation_resolved AS ma
  ON ma.source_period_year = f.group_period_year
  AND ma.source_period_term = f.group_period_term
  AND ma.lead_id = f.lead_id
  AND ma.employee_email_prefix = f.employee_email_prefix
  AND ma.section_assign_time = f.section_assign_time
WHERE
  f.dt = FORMAT_DATETIME(CURRENT_TIMESTAMP - INTERVAL '2' HOUR, 'YYYYMMdd')
  AND f.hour = FORMAT_DATETIME(CURRENT_TIMESTAMP - INTERVAL '3' HOUR, 'HH')
  AND f.section_assign_employee_first_level_department_name = 'H业务线'
  AND f.section_assign_employee_second_level_department_name = '青橙项目部'
  AND f.period_mapping_first_level_department_name = 'H业务线'
  AND f.period_mapping_second_level_department_name IN ('精品班学部', '菁英班学部', '市场部', '青橙项目部')
  AND (
    COALESCE(TRY_CAST(f.valid_lead_count AS BIGINT), 0) = 1
    OR (
      COALESCE(TRY_CAST(f.merge_valid_lead_count AS BIGINT), 0) > 0
      AND NOT mk.merge_root_lead_id IS NULL
      AND (
        REPLACE(COALESCE(f.rule_name, ''), ' ', '') LIKE '%青橙本地化%'
        OR REPLACE(COALESCE(f.rule_name, ''), ' ', '') LIKE '%河南本地化%'
        OR REPLACE(COALESCE(f.rule_name, ''), ' ', '') LIKE '%私域本地化%'
      )
    )
  )
  AND t.transfer_lead_id IS NULL
),
-- 普通有效和 merge 有效是同一 lead 的状态迁移。按期次、顾问、lead_id
-- 折叠后任一状态有效计 1，同时存在仍只计 1。
normal_lead_state_ranked as (
    select
        normal_lead_state_raw.*,
        max(source_valid_lead_count) over (
            partition by derived_qici, employee_email_name, lead_id
        ) as canonical_source_valid_lead_count,
        max(source_merge_valid_lead_count) over (
            partition by derived_qici, employee_email_name, lead_id
        ) as canonical_source_merge_valid_lead_count,
        row_number() over (
            partition by derived_qici, employee_email_name, lead_id
            order by
                case when source_valid_lead_count > 0 then 0 else 1 end,
                source_valid_lead_count desc,
                source_merge_valid_lead_count desc,
                section_assign_time desc,
                rule_name
        ) as normal_lead_rn
    from normal_lead_state_raw
)
-- 线索量
,normal_bb as (
SELECT
  qici,
  channel_map_1,
  channel_map_2,
  grade_1,
  virtual_direct_leader_email_name,
  employee_email_name,
  SUM(v_lead) AS v_lead,
  SUM(merge_valid_lead_count_effective) AS merge_valid_lead_count,
  COUNT(
    DISTINCT CASE WHEN merge_valid_lead_count_effective > 0 THEN merge_root_lead_id END
  ) AS merge_root_lead_count,
  ARRAY_JOIN(
    ARRAY_SORT(
      ARRAY_AGG(
        DISTINCT CASE
          WHEN merge_valid_lead_count_effective > 0
          THEN CAST(merge_root_lead_id AS VARCHAR)
        END
      )
    ),
    ','
  ) AS merge_root_lead_ids,
  case when nullif(trim(rule_name), '') is not null then rule_name end as rule_name
FROM (
  SELECT DISTINCT
    f.*,
    f.derived_qici AS qici,
    CASE
    WHEN LOWER(REPLACE(COALESCE(f.rule_name, ''), ' ', '')) LIKE '%app%' THEN '本地化'
    WHEN LOWER(REPLACE(COALESCE(f.rule_name, ''), ' ', '')) LIKE '%青橙付费-山东直播间-%' THEN '付费'
    WHEN LOWER(REPLACE(COALESCE(f.rule_name, ''), ' ', '')) LIKE '%青橙本地化-安徽app-%' THEN '本地化'
    WHEN (f.rule_name LIKE '%SEC内部未加好友%' OR f.rule_name LIKE '%SEC内部复用%') THEN '公海'
    WHEN LOWER(REPLACE(COALESCE(f.rule_name, ''), ' ', '')) LIKE '%青橙公海-0元信息流-%' THEN '公海'
    WHEN LOWER(REPLACE(COALESCE(f.rule_name, ''), ' ', '')) LIKE '%青橙公海-顾问未加好友-%' THEN '公海'
    WHEN LOWER(REPLACE(COALESCE(f.rule_name, ''), ' ', '')) LIKE '%青橙本地化-河南未加好友-%' THEN '本地化'
    WHEN LOWER(REPLACE(COALESCE(f.rule_name, ''), ' ', '')) LIKE '%青橙本地化-河南私域-%' THEN '本地化'
    WHEN LOWER(REPLACE(COALESCE(f.rule_name, ''), ' ', '')) LIKE '%青橙本地化-河南app-%' THEN '本地化'
      WHEN f.rule_name LIKE '%青橙私域-表单浙江-%' OR f.rule_name = '表单浙江'
      THEN '私域'
      WHEN f.rule_name LIKE '%青橙私域-表单江苏-%' OR f.rule_name = '表单江苏'
      THEN '私域'
      WHEN f.rule_name LIKE '%私域裂变%'
      THEN '私域'
      WHEN f.rule_name LIKE '%公域自然流%'
      THEN '公域'
      WHEN f.rule_name LIKE '%公域-自然流%'
      THEN '公域'
      WHEN f.rule_name LIKE '%内部图书%'
      THEN '图书'
      WHEN f.rule_name LIKE '%SEC内部未加好友%'
      THEN '公海'
      WHEN (
        REPLACE(COALESCE(f.rule_name, ''), ' ', '') LIKE '%青橙IP-招生退费-春春%'
        OR REPLACE(COALESCE(f.rule_name, ''), ' ', '') LIKE '%青橙IP-招生退费-朱博士%'
        OR REPLACE(COALESCE(f.rule_name, ''), ' ', '') LIKE '%青橙IP-招生退费-郭艺%'
      )
      THEN 'IP退费'
      WHEN f.rule_name LIKE '%抖音正价退费%'
      THEN '抖音复用'
      WHEN (
        f.rule_name LIKE '%赠失-星义%'
        OR f.rule_name LIKE '%赠失-朱博士%'
        OR f.rule_name LIKE '%赠失-春春%'
        OR f.rule_name LIKE '%赠失-郭艺%'
        OR f.rule_name LIKE '%赠失-亚飞%'
        OR f.rule_name LIKE '%青橙IP%'
      )
      THEN CONCAT('IP', CHR(  36192), CHR(  35838), CHR(  22833), CHR(  36133))
      WHEN (
        f.rule_name LIKE '%私域本地化%'
        OR f.rule_name LIKE '%河南本地化%'
        OR f.rule_name LIKE '%青橙本地化%'
      )
      THEN '本地化'
      WHEN (
        f.rule_name LIKE '%私域会话%'
        OR f.rule_name LIKE '%私域表单%'
        OR f.rule_name LIKE '%私域品效%'
        OR f.rule_name LIKE '%私域图书%'
      )
      THEN '私域'
      WHEN (
        f.rule_name LIKE '%公域学霸%' OR f.rule_name LIKE '%青橙公域%'
      )
      THEN '公域'
      WHEN (
        f.rule_name LIKE '%武汉图书%' OR f.rule_name LIKE '%西安图书%'
      )
      THEN '图书'
      WHEN f.rule_name LIKE '%亚飞IP%'
      THEN '主讲IP'
      WHEN (
        f.rule_name LIKE '%SEC未加好友%'
        OR f.rule_name LIKE '%SEC首期掉海%'
        OR f.rule_name LIKE '%SEC招生退费%'
        OR f.rule_name LIKE '%招生退费%'
      )
      THEN '公海'
      WHEN (
        f.rule_name LIKE '%顾问未加好友%' OR f.rule_name LIKE '%公海%'
      )
      THEN '公海'
      WHEN f.rule_name LIKE '%抖音私信%'
      THEN '抖音私信'
      WHEN (
        f.rule_name LIKE '%进校9元%' OR f.rule_name LIKE '%进校%'
      )
      THEN '进校9元'
      ELSE '未知'
    END AS channel_map_1,
    CASE
    WHEN LOWER(REPLACE(COALESCE(f.rule_name, ''), ' ', '')) LIKE '%青橙公海-sec一对一复用-%' THEN 'SEC一对一复用'
    WHEN LOWER(REPLACE(COALESCE(f.rule_name, ''), ' ', '')) LIKE '%青橙公海-secai提效复用-%' THEN 'SECAI提效复用'
    WHEN LOWER(REPLACE(COALESCE(f.rule_name, ''), ' ', '')) LIKE '%青橙公海-sec进校复用-%' THEN 'SEC进校复用'
    WHEN LOWER(REPLACE(COALESCE(f.rule_name, ''), ' ', '')) LIKE '%app%' THEN 'APP'
    WHEN LOWER(REPLACE(COALESCE(f.rule_name, ''), ' ', '')) LIKE '%青橙付费-山东直播间-%' THEN '山东直播间'
    WHEN LOWER(REPLACE(COALESCE(f.rule_name, ''), ' ', '')) LIKE '%青橙本地化-安徽app-%' THEN 'APP'
    WHEN (f.rule_name LIKE '%SEC内部未加好友%' OR f.rule_name LIKE '%SEC内部复用%') THEN 'SEC内部复用'
    WHEN LOWER(REPLACE(COALESCE(f.rule_name, ''), ' ', '')) LIKE '%青橙公海-0元信息流-%' THEN '0元信息流'
    WHEN LOWER(REPLACE(COALESCE(f.rule_name, ''), ' ', '')) LIKE '%青橙公海-顾问未加好友-%' THEN '顾问未加好友'
    WHEN LOWER(REPLACE(COALESCE(f.rule_name, ''), ' ', '')) LIKE '%青橙本地化-河南未加好友-%' THEN '河南未加好友'
    WHEN LOWER(REPLACE(COALESCE(f.rule_name, ''), ' ', '')) LIKE '%青橙本地化-河南私域-%' THEN '河南私域'
    WHEN LOWER(REPLACE(COALESCE(f.rule_name, ''), ' ', '')) LIKE '%青橙本地化-河南app-%' THEN 'APP'
      WHEN f.rule_name LIKE '%青橙私域-表单浙江-%' OR f.rule_name = '表单浙江'
      THEN '表单浙江'
      WHEN f.rule_name LIKE '%青橙私域-表单江苏-%' OR f.rule_name = '表单江苏'
      THEN '表单江苏'
      WHEN f.rule_name LIKE '%私域裂变%'
      THEN '私域裂变'
      WHEN f.rule_name LIKE '%公域自然流%'
      THEN '公域自然流'
      WHEN f.rule_name LIKE '%公域-自然流%'
      THEN '公域自然流'
      WHEN f.rule_name LIKE '%内部图书%'
      THEN '内部图书'
      WHEN f.rule_name LIKE '%SEC内部未加好友%'
      THEN 'SEC内部复用'
      WHEN REPLACE(COALESCE(f.rule_name, ''), ' ', '') LIKE '%青橙IP-招生退费-春春%'
      THEN '春春'
      WHEN REPLACE(COALESCE(f.rule_name, ''), ' ', '') LIKE '%青橙IP-招生退费-朱博士%'
      THEN '朱博士'
      WHEN REPLACE(COALESCE(f.rule_name, ''), ' ', '') LIKE '%青橙IP-招生退费-郭艺%'
      THEN '郭艺'
      WHEN f.rule_name LIKE '%抖音正价退费%'
      THEN '抖音正价退费'
      WHEN f.rule_name LIKE '%赠失-星义%'
      THEN '星义IP'
      WHEN f.rule_name LIKE '%赠失-朱博士%'
      THEN '朱博士IP'
      WHEN f.rule_name LIKE '%赠失-春春%'
      THEN '春春IP'
      WHEN f.rule_name LIKE '%赠失-郭艺%'
      THEN '郭艺IP'
      WHEN f.rule_name LIKE '%赠失-亚飞%'
      THEN '亚飞IP'
      WHEN f.rule_name LIKE '%青橙IP%'
      THEN '亚飞IP'
      WHEN f.rule_name LIKE '%私域会话%'
      THEN '私域会话'
      WHEN f.rule_name LIKE '%私域表单%'
      THEN '私域表单'
      WHEN f.rule_name LIKE '%私域图书%'
      THEN '私域图书'
      WHEN f.rule_name LIKE '%私域品效%'
      THEN '私域品效'
      WHEN f.rule_name LIKE '%私域本地化%'
      THEN '河南私域'
      WHEN (
        f.rule_name LIKE '%河南本地化%' OR f.rule_name LIKE '%青橙本地化%'
      )
      THEN 'APP'
      WHEN f.rule_name LIKE '%亚飞IP%'
      THEN '亚飞IP'
      WHEN f.rule_name LIKE '%SEC未加好友%'
      THEN 'SEC未加好友'
      WHEN f.rule_name LIKE '%SEC首期掉海%'
      THEN 'SEC首期掉海'
      WHEN (
        f.rule_name LIKE '%SEC招生退费%' OR f.rule_name LIKE '%招生退费%'
      )
      THEN 'SEC招生退费'
      WHEN (
        f.rule_name LIKE '%顾问未加好友%' OR f.rule_name LIKE '%公海%'
      )
      THEN '顾问未加好友'
      WHEN f.rule_name LIKE '%武汉图书%'
      THEN '武汉图书'
      WHEN f.rule_name LIKE '%西安图书%'
      THEN '西安图书'
      WHEN (
        f.rule_name LIKE '%公域学霸%' OR f.rule_name LIKE '%青橙公域%'
      )
      THEN '公域学霸'
      WHEN f.rule_name LIKE '%抖音私信%'
      THEN '抖音私信'
      WHEN (
        f.rule_name LIKE '%进校9元%' OR f.rule_name LIKE '%进校%'
      )
      THEN '进校9元'
      ELSE '未知'
    END AS channel_map_2,
    CASE
      WHEN f.rule_name LIKE '%高一%'
      THEN '高一'
      WHEN f.rule_name LIKE '%高二%'
      THEN '高二'
      WHEN f.rule_name LIKE '%高三%'
      THEN '高三'
      WHEN f.rule_name LIKE '%初一%'
      THEN '初一'
      WHEN f.rule_name LIKE '%初二%'
      THEN '初二'
      WHEN f.rule_name LIKE '%初三%'
      THEN '初三'
      ELSE f.lead_purchase_intention_level2_category_name
    END AS grade_1,
    CASE
      WHEN f.canonical_source_valid_lead_count > 0
      THEN 1
      WHEN f.canonical_source_merge_valid_lead_count > 0
      AND NOT f.merge_root_lead_id IS NULL
      AND (
        REPLACE(COALESCE(f.rule_name, ''), ' ', '') LIKE '%青橙本地化%'
        OR REPLACE(COALESCE(f.rule_name, ''), ' ', '') LIKE '%河南本地化%'
        OR REPLACE(COALESCE(f.rule_name, ''), ' ', '') LIKE '%私域本地化%'
      )
      THEN 1
      ELSE 0
    END AS v_lead,
    CASE
      WHEN f.canonical_source_valid_lead_count > 0
      THEN 0
      WHEN f.canonical_source_merge_valid_lead_count > 0
      AND NOT f.merge_root_lead_id IS NULL
      AND (
        REPLACE(COALESCE(f.rule_name, ''), ' ', '') LIKE '%青橙本地化%'
        OR REPLACE(COALESCE(f.rule_name, ''), ' ', '') LIKE '%河南本地化%'
        OR REPLACE(COALESCE(f.rule_name, ''), ' ', '') LIKE '%私域本地化%'
      )
      THEN f.canonical_source_merge_valid_lead_count
      ELSE 0
    END AS merge_valid_lead_count_effective
  FROM normal_lead_state_ranked AS f
  WHERE
    f.normal_lead_rn = 1
    AND CASE
      WHEN f.canonical_source_valid_lead_count > 0
      THEN 1
      WHEN f.canonical_source_merge_valid_lead_count > 0
      AND NOT f.merge_root_lead_id IS NULL
      AND (
        REPLACE(COALESCE(f.rule_name, ''), ' ', '') LIKE '%青橙本地化%'
        OR REPLACE(COALESCE(f.rule_name, ''), ' ', '') LIKE '%河南本地化%'
        OR REPLACE(COALESCE(f.rule_name, ''), ' ', '') LIKE '%私域本地化%'
      )
      THEN CAST(CASE
        WHEN COALESCE(f.local_merge_assignment_match_count, 0) = 1
        THEN CASE
          WHEN (
            REPLACE(COALESCE(f.local_merge_actual_assignment_rule, ''), ' ', '') LIKE '%青橙本地化%'
            OR REPLACE(COALESCE(f.local_merge_actual_assignment_rule, ''), ' ', '') LIKE '%河南本地化%'
            OR REPLACE(COALESCE(f.local_merge_actual_assignment_rule, ''), ' ', '') LIKE '%私域本地化%'
          )
          THEN '1'
          ELSE '0'
        END
        ELSE 'UNRESOLVED_LOCAL_MERGE_ALLOCATION'
      END AS INTEGER)
      ELSE 0
    END = 1
)
WHERE
  qici >= '20260925期'
GROUP BY
  qici,
  channel_map_1,
  channel_map_2,
  grade_1,
  virtual_direct_leader_email_name,
  employee_email_name,
  case when nullif(trim(rule_name), '') is not null then rule_name end
)
,prelead_bb as (
select
    p.qici,
    case
        when p.prelead_rule_name like '%抖音正价退费%' then '抖音复用'
        else '未知'
    end as channel_map_1,
    case
        when p.prelead_rule_name like '%抖音正价退费%' then '抖音正价退费'
        else '未知'
    end as channel_map_2,
    p.grade_1,
    p.virtual_direct_leader_email_name,
    p.employee_email_name,
    count(*) as v_lead,
    sum(cast(0 as bigint)) as merge_valid_lead_count,
    sum(cast(0 as bigint)) as merge_root_lead_count,
    max(cast(null as varchar)) as merge_root_lead_ids,
    case when nullif(trim(p.prelead_rule_name), '') is not null then p.prelead_rule_name end as rule_name
from douyin_refund_prelead p
where p.qici >= '20260925期'
group by
    p.qici,
    case
        when p.prelead_rule_name like '%抖音正价退费%' then '抖音复用'
        else '未知'
    end,
    case
        when p.prelead_rule_name like '%抖音正价退费%' then '抖音正价退费'
        else '未知'
    end,
    p.grade_1,
    p.virtual_direct_leader_email_name,
    p.employee_email_name,
    case when nullif(trim(p.prelead_rule_name), '') is not null then p.prelead_rule_name end
)
,bb as (
select
    qici,
    channel_map_1,
    channel_map_2,
    grade_1,
    virtual_direct_leader_email_name,
    employee_email_name,
    sum(v_lead) as v_lead,
    sum(merge_valid_lead_count) as merge_valid_lead_count,
    sum(merge_root_lead_count) as merge_root_lead_count,
    max(merge_root_lead_ids) as merge_root_lead_ids,
    rule_name
from (
    select
        qici,
        channel_map_1,
        channel_map_2,
        grade_1,
        virtual_direct_leader_email_name,
        employee_email_name,
        v_lead,
        merge_valid_lead_count,
        merge_root_lead_count,
        merge_root_lead_ids, rule_name
    from normal_bb
    union all
    select
        qici,
        channel_map_1,
        channel_map_2,
        grade_1,
        virtual_direct_leader_email_name,
        employee_email_name,
        v_lead,
        merge_valid_lead_count,
        merge_root_lead_count,
        merge_root_lead_ids, rule_name
    from prelead_bb
) lead_union
group by
    qici,
    channel_map_1,
    channel_map_2,
    grade_1,
    virtual_direct_leader_email_name,
    employee_email_name,
    rule_name
)
,legacy_lead_totals as (
    select qici, channel_map_1, channel_map_2, grade_1, virtual_direct_leader_email_name, employee_email_name, sum(v_lead) as old_v_lead
    from bb
    group by qici, channel_map_1, channel_map_2, grade_1, virtual_direct_leader_email_name, employee_email_name
)
-- 保留年级维度的对齐层
,bb_dedup as (
    select *,
    sum(v_lead) over (partition by qici, channel_map_1, channel_map_2, grade_1, virtual_direct_leader_email_name, employee_email_name) as old_v_lead,
    row_number() over(
        partition by employee_email_name, qici, channel_map_1, channel_map_2, grade_1, virtual_direct_leader_email_name, rule_name
        order by v_lead desc
    ) as rn
    from bb
)
-- 合并
,mm as (select
coalesce(bb1.qici, ud.qici) as qici,
coalesce(bb1.channel_map_1, ud.channel_map_1, '未知') as channel_1,
coalesce(bb1.channel_map_2, ud.qudao, '未知') as channel_map_2,
coalesce(bb1.grade_1, ud.grade_0, '未知') as grade_1,
coalesce(bb1.employee_email_name, ud.name) as employee_email_name,
coalesce(bb1.v_lead, 0) as v_lead,
coalesce(bb1.merge_valid_lead_count, 0) as merge_valid_lead_count,
coalesce(bb1.merge_root_lead_count, 0) as merge_root_lead_count,
coalesce(bb1.merge_root_lead_ids, '') as merge_root_lead_ids,
coalesce(bb1.virtual_direct_leader_email_name, ud.zhuguan) as virtual_direct_leader_email_name,
case when coalesce(bb1.old_v_lead, ll.old_v_lead, 0) > 5
     then coalesce(bb1.employee_email_name, ud.name) else '0' end as jieliang,
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
coalesce(ud.sc, 0) as sc,
coalesce(bb1.rule_name, ud.rule_name) as rule_name,
case when coalesce(bb1.old_v_lead, ll.old_v_lead, 0) in (0, 1, 2)
     then '0' else coalesce(bb1.employee_email_name, ud.name) end as legacy_receiving_key
from bb_dedup bb1
full outer join ud
    on ud.name = bb1.employee_email_name
   and ud.qici = bb1.qici
   and ud.channel_map_1 = bb1.channel_map_1
   and ud.qudao = bb1.channel_map_2
   and ud.grade_0 = bb1.grade_1
   and ud.zhuguan = bb1.virtual_direct_leader_email_name
   and coalesce(ud.rule_name, '') = coalesce(bb1.rule_name, '')
left join legacy_lead_totals ll
    on ud.name = ll.employee_email_name
   and ud.qici = ll.qici
   and ud.channel_map_1 = ll.channel_map_1
   and ud.qudao = ll.channel_map_2
   and ud.grade_0 = ll.grade_1
   and ud.zhuguan = ll.virtual_direct_leader_email_name
where bb1.rn = 1 or bb1.rn is null
)
-- 例子成本
select *
from(
select distinct
mm.qici,
mm.channel_map_2,
mm.grade_1,
mm.employee_email_name,
mm.v_lead,
mm.virtual_direct_leader_email_name,
mm.jieliang,
mm.pay_user,
mm.p_pay_user,
mm.pay_sub,
mm.p_pay_sub,
mm.income,
mm.refund,
mm.promit,
mm.p_income,
mm.refund_user,
mm.podan,
mm.sc,
mm.merge_valid_lead_count,
mm.merge_root_lead_count,
mm.merge_root_lead_ids,
case when channel_map_2 = '亚飞IP' then 120
when channel_map_2 = '武汉图书' then 20
when channel_map_2 = '抖音私信' then 130
when channel_map_2 = '进校9元' then 70
else 0
end as cost_lead,
mm.channel_1,
jg.xuebu as dept_2,
jg.leader_employee_email_name as xiaozu,
jg.dazu,jg.jingli,
mm.rule_name,
mm.legacy_receiving_key,
-- Advisor breakthrough inputs: gross receipt keys, never converted customer counts.
cast(case when nullif(trim(mm.employee_email_name), '') is not null and trim(mm.employee_email_name) not in ('0', '未分配账号', '未分配顾问') then trim(mm.employee_email_name) end as varchar) as advisor_identity_key,
cast(case when mm.income > 0 and nullif(trim(mm.employee_email_name), '') is not null and trim(mm.employee_email_name) not in ('0', '未分配账号', '未分配顾问') then trim(mm.employee_email_name) end as varchar) as advisor_positive_revenue_key,
case when mm.income < 0 then 1 else 0 end as advisor_negative_income_rows
from mm
left join (
    select qici, employee_email_name, xuebu, leader_employee_email_name, dazu, jingli
    from (
        select qici, employee_email_name, xuebu, leader_employee_email_name, dazu, jingli,
               count(*) over (partition by qici, employee_email_name) as key_rows
        from temp_table.lvshuai01_qing_team_jg
    ) jg_scoped
    where key_rows = 1
) jg on mm.employee_email_name = jg.employee_email_name and mm.qici = jg.qici
cross join (
    select cast(case when count(*) = 0 then '1' else 'DUPLICATE_QING_TEAM_JG_KEY' end as integer) as valid_key
    from (
        select qici, employee_email_name
        from temp_table.lvshuai01_qing_team_jg
        group by qici, employee_email_name having count(*) > 1
    ) duplicates
) jg_quality
where jg_quality.valid_key = 1)
