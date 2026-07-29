with  guiyin as (
select order_number,performance_employee_email_name,lead_id,pay_success_timestamp,original_order_user_number
from service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf
where dt = FORMAT_DATETIME (NOW() - INTERVAL '2' HOUR, 'YYYYMMdd')
and hour = FORMAT_DATETIME (NOW() - INTERVAL '2' HOUR, 'HH')
and course_first_level_department_name in ('H业务线','A业务线','EM业务线','LL业务线','TT','TUTU','TT业务线')
and course_second_level_department_name in ('V项目部','本地化部','私域营销组','青少成长学部','创新技术组','成长中心供应链组','APP运营组','英语产品部','职场服务部','用户平台部','微师产品部','上海中心综合部','CAL技术组','财务核算部','财经项目部','人才发展部','财务信息化部','图书项目部（关闭）','运营部','基础架构组','数学产品部','营销产品部','雅思学部','商品部','磨课组','升学规划部','郑州中心','组织部','留学申请学部','质检部','架构平台部','师训组','投放商务组','系统班部','编程素养学部','市场运营组','项目运营组','KM技术组','二讲老师部','成都中心综合部','业务设计部','专题课部','微师职教产品部','高校学部','教学服务部','平台产品部','数字化学部','品牌运营组','校长办公室','运营中心财务','视效部','数据与商业分析中心','X项目','教学产品部','XA学部','语言学部','图书产品部','主播部','业务支持部','HL技术组','武汉中心综合部','成人供应链组','途途课堂','信息平台部','HL经营分析组','大数据部','直播运营组','市场部','金刚产品部','教学产品运营中心','平台电商组','企业效能部','品牌与内容部','产品研发部','小学部','技术质量部','财务报告部','税务部','用户产品部','直播二部','招聘部','HR共享中心','清北','增长策略部','督察部','商品运营部','资金管理部','美好家庭学部','设计支持中心','初中部','AIGC创新部','财务部','人力资源部','人才保障部一部','CAL经营分析组','基础技术部','综合素养学部','热线呼入部','品牌部','语文产品部','供应链部','题库','GZ学部','政府关系部','HRBP部','招生运营部','督检组','耀师项目部','产品运营部','营运部','多媒体技术部','跟谁学郑州中心(失效）','人工智能部','体验设计部','狮王项目部','资产服务部','专升本项目部','基础技术部(失效)','郑州中心综合部','考研学部','内容营销组','公关部','公职学部','客服部','运营平台部','CS学部','财务FP&A部','商学院学部','行政部','直播三部','营销技术部','私域运营组','飞花产品部','星火产品部','客户端技术部','薪酬绩效部','图书项目部','NJ学部','直播一部','法务部','在线服务部','履约部','KML经营分析组','社会保障部','精品班部','教学教研部','医疗项目部','菁英班部','菁英班学部','精品班学部','一对一学部','北京学部','图书学部','河南学部','清北班学部','湖广学部','山西学部','K学部','M学部','大学生学习学部','合肥学校','太原学校','苏州学校','郑州学校','北京学校','上海学校','运营中心','广州学校','市场中心','南京学校','深圳学校','成都学校','财务中心','武汉学校','济南学校','天津学校','学校办公室','重庆学校','西安学校','长沙学校','市场二部','留学学部','国际考试学部','出国语培线下项目','广州学校（IE）','国际竞赛项目','剑桥英语项目','上海学校（IE）','心理学部','创新项目部','素质成长学部','国际考试在线学部','毛豆学部','青少学部','市场三部','市场四部','青橙项目部','文旅学部','本地化大班学部','市场营销部','直播市场部','创新增长部','学习规划中心','素养初中学部','素养青藤学部','素养小学学部','用户运营部','经营策略部','校园招聘','直播创新部','战略创新部','产研部','业务研发部','教学质量部','Theta项目部','AI素养学部','文旅项目','Theta智学项目部','Theta产研部','V学部','TT初中学部','TT小学学部','产研部','T学部','专题课部（失效）','初中组','文旅项目（失效）')
and performance_third_level_department_name = '市场顾问部')
------------------------业绩流水
,rd as (select distinct
dt, top_period, top_order_number, top_paid_time, order_number,lead_id, trade_time, user_id, type, trade_type, trade_status, course_grade, course_subject, course_department1, course_department2, clazz_biz_number, clazz_name, teacher_name, employee_email_name,leader_employee_email_name, cast(real_price_0 as decimal(38, 9)) as price
from (
select  dt,
concat(date_format(date_trunc('week', cast(top_paid_time as timestamp) - interval '1' day) + interval '4' day, '%Y%m%d'), '期') as top_period, top_order_number, top_paid_time, ls.order_number, guiyin.lead_id,trade_time, user_id, type, trade_type, trade_status, course_grade, course_subject, clazz_biz_number, clazz_name, teacher_name,leader_employee_email_name, course_first_level_department_name as course_department1, course_second_level_department_name as course_department2, employee_email_name, employee_first_level_department_name as department1, employee_second_level_department_name as department2, employee_third_level_department_name as department3,
case when trade_status in ('全部退款', '部分退款') then -real_price
when trade_type in ('调课调班') and trade_status in ('调出退款', '全部退款') then -transfer_price
when trade_type in ('调课调班') and trade_status in ('支付') then transfer_price
else real_price end as real_price_0
    from finance_dw.app_finance_performance_extend_details_hf ls
	left join guiyin------获取lead_id
on guiyin.order_number = ls.order_number
    where dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
      and hour = format_datetime(now() - interval '2' hour, 'HH')
      and employee_first_level_department_name = 'H业务线'
      and employee_second_level_department_name = '市场部'
      and employee_third_level_department_name = '市场顾问部'
      and course_first_level_department_name = 'H业务线'
      and course_second_level_department_name = '精品班学部'
      and course_grade = '初三')
)
--------------转介绍
,zjs as (
select distinct order_number,case when introduce_type in ('1',1) then 1 else 0 end as introduce_type ,invitee_user_number,introduce_activity_code
from finance_dw.dws_finance_introduce_detail_hf
where  dt =format_datetime(now() - interval '2' hour, 'YYYYMMdd')
      and hour = format_datetime(now() - interval '2' hour, 'HH')
and introduce_type=1
and course_first_level_department_name='H业务线'
and course_second_level_department_name in ('精品班学部')
)
-----------------退费行课节数
,ord as (
	SELECT
          order_number,user_number,final_paid_timestamp,full_refund_timestamp,total_refund_amount,talent_type_name,
          employee_email_name,email_prefix,
		  full_refund_finish_lesson_count,-----完全退款时已完课课节数(直播课，不包含类直播赠课)
          full_refund_chain_finish_lesson_count,---完全退款时调课链路总完课课节数
		  original_order_pay_success_clazz_remain_lesson_count,-----原始父订单下单时剩余课节数
          clazz_number,clazz_biz_number,clazz_name,school_year,school_term_name,school_department_name,school_subject_name,
		concat(date_format(date_trunc('week', cast(full_refund_timestamp as timestamp) - interval '1' day) + interval '4' day, '%Y%m%d'), '期') as qici_re,
          CASE
            WHEN course_category_code = 10 THEN '公开课'
            WHEN course_category_code = 20 THEN '体验课'
            WHEN course_category_code = 30 THEN '专题课'
            WHEN course_category_code = 40 THEN '系列课'
            ELSE cast(course_category_code as varchar)
          END AS course_category,
          course_first_level_department_name,course_second_level_department_name,course_third_level_department_name
        FROM
          finance_dw.dm_finance_order_refund_detail_df
        WHERE dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
          AND course_first_level_department_name = 'H业务线'
		  and course_second_level_department_name in ( '精品班学部','菁英班学部','一对一学部')
          AND is_full_refund_order = 1------------------是否全部退款
          AND total_refund_amount IS NOT NULL
          AND total_refund_amount <> 0)
--------------调课调班
,order_change as (
	SELECT
      parent_order_number,------父订单编号
      CASE WHEN order_change_type = 0 THEN '调课调班' WHEN order_change_type = 1 THEN '课程转移' ELSE cast(order_change_type as varchar)
      END AS refund_type ---------调课调班类型
    FROM finance_dw.dim_finance_order_change_df
    WHERE dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
      AND latest_child_order_status IN (2, 6, 7)
      AND biz_type = 2)
---------------合并退费行课节数
,re_ke as (select
  ord.qici_re,
  ord.order_number,
  ord.user_number,
  ord.final_paid_timestamp,
  ord.full_refund_timestamp,
  ord.total_refund_amount,
  ord.talent_type_name,
  ord.employee_email_name,
  ord.full_refund_finish_lesson_count,-----完全退款时已完课课节数(直播课，不包含类直播赠课)
  ord.full_refund_chain_finish_lesson_count,---完全退款时调课链路总完课课节数
  ord.original_order_pay_success_clazz_remain_lesson_count,-----原始父订单下单时剩余课节数
  ord.clazz_number,
  ord.clazz_name,
  COALESCE(order_change.refund_type, '非调课调班') AS refund_type
  from ord
  left join order_change on ord.order_number = order_change.parent_order_number)
------------------------连接各订单退费行课节数
,t4 as (select rd.*,coalesce(re_ke.full_refund_chain_finish_lesson_count,0) as re_lc,coalesce(zjs.introduce_type,0) as introduce_type
from rd
left join re_ke on  re_ke.order_number = rd.order_number
left join zjs on zjs.order_number = rd.order_number)
------------分配规则
-- uid1规则（修复：加 row_number 去重，防止多 user_id 导致膨胀）
,uid1_rules as (
    select uid1, lead_id0, employee_email_name, rule_name0 from (
        select
            user_id as uid1,
            lead_id as lead_id0,
            employee_email_name,
            rule_name as rule_name0,
            row_number() over(partition by lead_id, employee_email_name order by user_id) as rn
        from bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df
        where dt = FORMAT_DATETIME(NOW() - INTERVAL '2' HOUR, 'YYYYMMdd')
            and hour = FORMAT_DATETIME(NOW() - INTERVAL '2' HOUR, 'HH')
            and section_assign_employee_first_level_department_name = 'H业务线'
            and section_assign_employee_second_level_department_name = '市场部'
            and period_mapping_first_level_department_name = 'H业务线'
    ) where rn = 1
)
-- uid2规则（修复：加 row_number 去重，防止换号膨胀）
,uid2_rules as (
    select uid1, lead_id_g, uid2, rule_name, employee_email_name from (
        select
            guiyin.original_order_user_number as uid1,
            guiyin.lead_id as lead_id_g,
            ld.user_id as uid2,
            ld.rule_name,
            ld.employee_email_name,
            row_number() over(partition by guiyin.lead_id, guiyin.performance_employee_email_name order by ld.user_id) as rn
        from guiyin
        left join (
            select
                lead_id,
                user_id,
                rule_name,
                employee_email_name,
                employee_email_prefix
            from bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df
            where dt = FORMAT_DATETIME(NOW() - INTERVAL '2' HOUR, 'YYYYMMdd')
                and hour = FORMAT_DATETIME(NOW() - INTERVAL '2' HOUR, 'HH')
                and section_assign_employee_first_level_department_name = 'H业务线'
                and section_assign_employee_second_level_department_name = '市场部'
                and period_mapping_first_level_department_name = 'H业务线'
        ) ld on guiyin.lead_id = ld.lead_id
            and guiyin.performance_employee_email_name = ld.employee_email_name
    ) where rn = 1
)
---------合并（修复：uid1/uid2 JOIN 去掉 user_id 条件和 CAST，换号也能匹配）
,order_z as (select *
from (
	select distinct
	t4.*,
	u1.rule_name0,
	case
            when u1.rule_name0 like '%高一%' then '高一'
            when u1.rule_name0 like '%高二%' then '高二'
            when u1.rule_name0 like '%高三%' then '高三'
            when u1.rule_name0 like '%初一%' then '初一'
            when u1.rule_name0 like '%初二%' then '初二'
            when u1.rule_name0 like '%初三%' then '初三'
            else '未知'
        end as grade_0,
	case when instr(u1.rule_name0, '期') > 0  and instr(u1.rule_name0, '期') >= 5 and regexp_like(substr(u1.rule_name0, cast(instr(u1.rule_name0, '期') - 4 as integer), cast(4 as integer)), '^[0-9]{4}$') then substr(u1.rule_name0, cast(instr(u1.rule_name0, '期') - 4 as integer), cast(5 as integer)) else null
end as period_0,
	u2.rule_name,
	case
            when u2.rule_name like '%高一%' then '高一'
            when u2.rule_name like '%高二%' then '高二'
            when u2.rule_name like '%高三%' then '高三'
            when u2.rule_name like '%初一%' then '初一'
            when u2.rule_name like '%初二%' then '初二'
            when u2.rule_name like '%初三%' then '初三'
            else t4.course_grade
        end as grade_2,
	case when instr(u2.rule_name, '期') > 0  and instr(u2.rule_name, '期') >= 5 and regexp_like(substr(u2.rule_name, cast(instr(u2.rule_name, '期') - 4 as integer), cast(4 as integer)), '^[0-9]{4}$')
    then substr(u2.rule_name, cast(instr(u2.rule_name, '期') - 4 as integer), cast(5 as integer))
    else null
end as period_2,
	u2.uid2,
	substr(top_paid_time, cast(1 as integer), cast(10 as integer))  as day
from t4
	-- 修复：uid1 只按 lead_id + employee_email_name 匹配，不再用 user_id，去掉 CAST
	left join uid1_rules u1 on t4.employee_email_name = u1.employee_email_name and t4.lead_id = u1.lead_id0
	-- 修复：uid2 只按 lead_id + employee_email_name 匹配，不再用 user_id，去掉 CAST
	left join uid2_rules u2 on t4.employee_email_name = u2.employee_email_name and t4.lead_id = u2.lead_id_g))
------------------------------初数
,cs_case as (select *,
cast(case when price < cast(0 as decimal(38, 9)) and re_lc > 1 then cast(0 as decimal(38, 9)) else price end as decimal(38, 9)) as valid_price,
case
    when rule_name0 like '%朱汉祺koc%' then '朱汉祺koc'
    when rule_name0 like '%朱汉祺IP%' or rule_name0 like '%朱汉祺29元%' or rule_name0 like '%朱汉祺ip%' then '朱汉祺IP'
    when rule_name0 like '%周帅ip9元%' then '周帅ip9元'
    when rule_name0 like '%亚飞9元百度%' then '亚飞9元百度'
    when rule_name0 like '%亚飞99元西安直播%' then '亚飞99元西安直播'
    when rule_name0 like '%训练营%' then '训练营'
    when rule_name0 like '%信息流%' then '信息流'
    when rule_name0 like '%肖晗ip%' then '肖晗ip'
    when rule_name0 like '%线索复用%' then '线索复用'
    when rule_name0 like '%春春退费0元%' then '线索复用'
    when rule_name0 like '%朱汉祺退费0元%' then '线索复用'
    when rule_name0 like '%西安图书%' then '西安图书'
    when rule_name0 like '%文旅%' then '文旅'
    when rule_name0 like '%未加好友%' then '未加好友'
    when rule_name0 like '%图书KOC%' then '图书KOC'
    when rule_name0 like '%私域0元%' then '私域0元'
    when rule_name0 like '%商务%' then '商务'
    when rule_name0 like '%孟亚飞ip9元%' or rule_name0 like '%亚飞IP%' then '孟亚飞ip9元'
    when rule_name0 like '%孟亚飞ip99元%' or rule_name0 like '%孟亚飞常规99元%' then '孟亚飞ip99元'
    when rule_name0 like '%孟亚飞ip19元%' then '孟亚飞ip19元'
    when rule_name0 like '%公导私主动咨询%' then '公导私主动咨询'
    when rule_name0 like '%多学科拓展%' then '多学科拓展'
    when rule_name0 like '%抖音私信%' then '抖音私信'
    when rule_name0 like '%春春ip99元%' then '春春ip99元'
    when rule_name0 like '%春春B站99元%' then '春春B站99元'
    when rule_name0 like '%常规koc%' then '常规koc'
    when rule_name0 like '%曹忆IP%' or rule_name0 like '%曹忆ip99元%' then '曹忆ip99元'
    when rule_name0 like '%百度搜索%' then '百度搜索'
    when rule_name0 like '%tmk9元%' then 'tmk9元'
    when rule_name0 like '%tmk3元%' then 'tmk3元'
    when rule_name0 like '%tmk1元%' then 'tmk1元'
    when rule_name0 like '%koc5元初中%' or rule_name0 like '%koc常规5元初二%' or rule_name0 like '%koc常规5元初三%' or rule_name0 like '%koc自孵化5元初二%' or rule_name0 like '%koc自孵化5元初三%' then 'koc5元初中'
    when rule_name0 like '%koc5元%' or rule_name0 like '%koc测试5元%' or rule_name0 like '%koc常规5元%' or rule_name0 like '%koc肖晗5元%' or rule_name0 like '%koc朱汉祺5元%' or rule_name0 like '%koc自孵化5元%' then 'koc5元'
    when rule_name0 like '%koc29元%' then 'koc29元'
    when rule_name0 like '%B转A%' then 'B转A'
    when rule_name0 like '%B站孟亚飞%' then 'B站孟亚飞'
    when rule_name0 like '%B站高中%' then 'B站高中'
    when rule_name0 like '%B站%' then 'B站'
    when rule_name0 like '%APP%' then 'APP'
    when rule_name0 like '%进校%' or rule_name0 like '%0元进校%' then '0元进校'
    else null
end as qudao0_case,
CASE
    WHEN rule_name LIKE '%朱汉祺koc%' THEN '朱汉祺koc'
    WHEN rule_name LIKE '%朱汉祺IP%' OR rule_name LIKE '%朱汉祺29元%' OR rule_name LIKE '%朱汉祺ip%' THEN '朱汉祺IP'
    WHEN rule_name LIKE '%周帅ip9元%' THEN '周帅ip9元'
    WHEN rule_name LIKE '%亚飞9元百度%' THEN '亚飞9元百度'
    WHEN rule_name LIKE '%亚飞99元西安直播%' THEN '亚飞99元西安直播'
    WHEN rule_name LIKE '%训练营%' THEN '训练营'
    WHEN rule_name LIKE '%信息流%' THEN '信息流'
    WHEN rule_name LIKE '%肖晗ip%' THEN '肖晗ip'
    WHEN rule_name LIKE '%线索复用%' THEN '线索复用'
    WHEN rule_name LIKE '%春春退费0元%' THEN '线索复用'
    WHEN rule_name LIKE '%朱汉祺退费0元%' THEN '线索复用'
    WHEN rule_name LIKE '%西安图书%' THEN '西安图书'
    WHEN rule_name LIKE '%文旅%' THEN '文旅'
    WHEN rule_name LIKE '%未加好友%' THEN '未加好友'
    WHEN rule_name LIKE '%图书KOC%' THEN '图书KOC'
    WHEN rule_name LIKE '%私域0元%' THEN '私域0元'
    WHEN rule_name LIKE '%商务%' THEN '商务'
    WHEN rule_name LIKE '%孟亚飞ip9元%' OR rule_name LIKE '%亚飞IP%' THEN '孟亚飞ip9元'
    WHEN rule_name LIKE '%孟亚飞ip99元%' OR rule_name LIKE '%孟亚飞常规99元%' THEN '孟亚飞ip99元'
    WHEN rule_name LIKE '%孟亚飞ip19元%' THEN '孟亚飞ip19元'
    WHEN rule_name LIKE '%公导私主动咨询%' THEN '公导私主动咨询'
    WHEN rule_name LIKE '%多学科拓展%' THEN '多学科拓展'
    WHEN rule_name LIKE '%抖音私信%' THEN '抖音私信'
    WHEN rule_name LIKE '%春春ip99元%' THEN '春春ip99元'
    WHEN rule_name LIKE '%春春B站99元%' THEN '春春B站99元'
    WHEN rule_name LIKE '%常规koc%' THEN '常规koc'
    WHEN rule_name LIKE '%曹忆IP%' OR rule_name LIKE '%曹忆ip99元%' THEN '曹忆ip99元'
    WHEN rule_name LIKE '%百度搜索%' THEN '百度搜索'
    WHEN rule_name LIKE '%tmk9元%' THEN 'tmk9元'
    WHEN rule_name LIKE '%tmk3元%' THEN 'tmk3元'
    WHEN rule_name LIKE '%tmk1元%' THEN 'tmk1元'
    WHEN rule_name LIKE '%koc5元初中%' OR rule_name LIKE '%koc常规5元初二%' OR rule_name LIKE '%koc常规5元初三%' OR rule_name LIKE '%koc自孵化5元初二%' OR rule_name LIKE '%koc自孵化5元初三%' THEN 'koc5元初中'
    WHEN rule_name LIKE '%koc5元%' OR rule_name LIKE '%koc测试5元%' OR rule_name LIKE '%koc常规5元%' OR rule_name LIKE '%koc肖晗5元%' OR rule_name LIKE '%koc朱汉祺5元%' OR rule_name LIKE '%koc自孵化5元%' THEN 'koc5元'
    WHEN rule_name LIKE '%koc29元%' THEN 'koc29元'
    WHEN rule_name LIKE '%B转A%' THEN 'B转A'
    WHEN rule_name LIKE '%B站孟亚飞%' THEN 'B站孟亚飞'
    WHEN rule_name LIKE '%B站高中%' THEN 'B站高中'
    WHEN rule_name LIKE '%B站%' THEN 'B站'
    WHEN rule_name LIKE '%APP%' THEN 'APP'
    WHEN rule_name LIKE '%进校%' OR rule_name LIKE '%0元进校%' THEN '0元进校'
    ELSE null
END AS qudao_case
from order_z
where day >= '2025-09-01'
  and day < '2025-12-01')
,cs as (
    select
        c.*,
        c.qudao0_case as qudao0,
        c.qudao_case as qudao
    from cs_case c
)
------------整数口径：按 top_order_number + course_subject 去重，净金额为正计售卖科目
,subject_order as (
    select
        channel_group,
        sale_subject,
        order_subject_key,
        sum(valid_price) as subject_order_net_price
    from (
        select
            case
                when coalesce(c.qudao, c.qudao0) in ('曹忆ip99元', '曹忆IP99元') then '精品班曹忆ip99元'
                else '精品班其他渠道'
            end as channel_group,
            coalesce(nullif(trim(cast(c.course_subject as varchar)), ''), '未知') as sale_subject,
            coalesce(
                cast(c.top_order_number as varchar),
                cast(c.order_number as varchar),
                concat(cast(c.user_id as varchar), '_', coalesce(nullif(trim(cast(c.course_subject as varchar)), ''), '未知'))
            ) as order_subject_key,
            c.valid_price
        from cs c
        where c.course_department1 = 'H业务线'
          and c.course_department2 = '精品班学部'
          and c.course_grade = '初三'
    ) x
    group by channel_group, sale_subject, order_subject_key
),
channel_dim as (
    select '精品班曹忆ip99元' as channel_group
    union all
    select '精品班其他渠道' as channel_group
),
subject_dim as (
    select distinct sale_subject
    from subject_order
),
subject_agg as (
    select
        d.channel_group,
        s.sale_subject,
        cast(coalesce(sum(case when round(o.subject_order_net_price, 2) > 0 then 1 else 0 end), 0) as bigint) as subject_sale_count
    from channel_dim d
    cross join subject_dim s
    left join subject_order o
      on d.channel_group = o.channel_group
     and s.sale_subject = o.sale_subject
    group by d.channel_group, s.sale_subject
),
final_agg as (
    select
        channel_group,
        sale_subject,
        cast(sum(subject_sale_count) over (partition by channel_group) as bigint) as total_sale_subject_count,
        subject_sale_count,
        case
            when sum(subject_sale_count) over (partition by channel_group) = 0 then 0.0
            else subject_sale_count * 1.0 / sum(subject_sale_count) over (partition by channel_group)
        end as subject_share
    from subject_agg
)
select
    channel_group,
    sale_subject,
    total_sale_subject_count,
    subject_sale_count,
    cast(round(subject_share, 6) as decimal(20, 6)) as subject_share
from final_agg
order by
    case when channel_group = '精品班曹忆ip99元' then 1 else 2 end,
    subject_sale_count desc,
    sale_subject
limit 1000
