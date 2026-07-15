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
			when substr(trade_time, 1, 10) >= '2026-07-14' and substr(trade_time, 1, 10) <= '2026-07-19' then '20260716期'
			when substr(trade_time, 1, 10) >= '2026-02-25' and substr(trade_time, 1, 10) <= '2026-03-02' then '20260227期'
			when substr(trade_time, 1, 10) >= '2026-02-17' and substr(trade_time, 1, 10) <= '2026-02-24' then '20260220期'
			when substr(trade_time, 1, 10) >= '2026-02-09' and substr(trade_time, 1, 10) <= '2026-02-16' then '20260213期'
			when substr(trade_time, 1, 10) >= '2026-02-03' and substr(trade_time, 1, 10) <= '2026-02-08' then '20260206期'
			when substr(trade_time, 1, 10) >= '2026-01-27' and substr(trade_time, 1, 10) <= '2026-02-02' then '20260130期'
			when substr(trade_time, 1, 10) >= '2026-01-20' and substr(trade_time, 1, 10) <= '2026-01-26' then '20260123期'
		else concat(date_format(date_trunc('week', cast(trade_time as timestamp) - interval '1' day) + interval '4' day, '%Y%m%d'), '期') end as qici,
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
,gmv_t as (
    select
        id, order_number, clazz_name, user_id1, trade_status, trade_time,
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
,gmv_z as (
    select
        id, order_number, clazz_name, user_id1, trade_status, trade_time,
        trade_type, email_prefix, name, grade_list, subject,
        qici, school_term_id, teacher_name,
        course_first_level_department_name,
        course_second_level_department_name,
        sum(price) as name_total_price
    from dd
    where trade_type = '正常订单'
    group by id, order_number, clazz_name, user_id1, trade_status, trade_time,
             trade_type, email_prefix, name, grade_list, subject,
             qici, school_term_id, teacher_name,
             course_first_level_department_name,
             course_second_level_department_name
)
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
,n_uid as (
select aa.*,row_number() over (partition by aa.original_order_user_number order by aa.qici desc) as rn
from (select lead_id,original_order_user_number,performance_employee_email_name,case
    when cast(date_parse(replace(concat(trade_group_period_year,trade_group_period_term),'期',''),'%Y%m%d') as date) between date '2026-07-14' and date '2026-07-19' then '20260716期'
    else concat(cast(date_format(date_trunc('week',date_parse(replace(concat(trade_group_period_year,trade_group_period_term),'期',''),'%Y%m%d') - interval '1' day) + interval '4' day,'%Y%m%d')as varchar),'期')
end qici
from service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf
where dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
        and hour = format_datetime(now() - interval '2' hour, 'HH')
and course_first_level_department_name in ('H业务线','A业务线','EM业务线','LL业务线','TT','TUTU','TT业务线')
and course_second_level_department_name in ('V项目部','本地化部','私域营销组','青少成长学部','创新技术组','成长中心供应链组','APP运营组','英语产品部','职场服务部','用户平台部','微师产品部','上海中心综合部','CAL技术组','财务核算部','财经项目部','人才发展部','财务信息化部','图书项目部（关闭）','运营部','基础架构组','数学产品部','营销产品部','雅思学部','商品部','磨课组','升学规划部','郑州中心','组织部','留学申请学部','质检部','架构平台部','师训组','投放商务组','系统班部','编程素养学部','市场运营组','项目运营组','KM技术组','二讲老师部','成都中心综合部','业务设计部','专题课部','微师职教产品部','高校学部','教学服务部','平台产品部','数字化学部','品牌运营组','校长办公室','运营中心财务','视效部','数据与商业分析中心','X项目','教学产品部','XA学部','语言学部','图书产品部','主播部','业务支持部','HL技术组','武汉中心综合部','成人供应链组','途途课堂','信息平台部','HL经营分析组','大数据部','直播运营组','市场部','金刚产品部','教学产品运营中心','平台电商组','企业效能部','品牌与内容部','产品研发部','小学部','技术质量部','财务报告部','税务部','用户产品部','直播二部','招聘部','HR共享中心','清北','增长策略部','督察部','商品运营部','资金管理部','美好家庭学部','设计支持中心','初中部','AIGC创新部','财务部','人力资源部','人才保障部一部','CAL经营分析组','基础技术部','综合素养学部','热线呼入部','品牌部','语文产品部','供应链部','题库','GZ学部','政府关系部','HRBP部','招生运营部','督检组','耀师项目部','产品运营部','营运部','多媒体技术部','跟谁学郑州中心(失效）','人工智能部','体验设计部','狮王项目部','资产服务部','专升本项目部','基础技术部(失效)','郑州中心综合部','考研学部','内容营销组','公关部','公职学部','客服部','运营平台部','CS学部','财务FP&A部','商学院学部','行政部','直播三部','营销技术部','私域运营组','飞花产品部','星火产品部','客户端技术部','薪酬绩效部','图书项目部','NJ学部','直播一部','法务部','在线服务部','履约部','KML经营分析组','社会保障部','精品班部','教学教研部','医疗项目部','菁英班部','菁英班学部','精品班学部','一对一学部','北京学部','图书学部','河南学部','清北班学部','湖广学部','山西学部','K学部','M学部','大学生学习学部','合肥学校','太原学校','苏州学校','郑州学校','北京学校','上海学校','运营中心','广州学校','市场中心','南京学校','深圳学校','成都学校','财务中心','武汉学校','济南学校','天津学校','学校办公室','重庆学校','西安学校','长沙学校','市场二部','留学学部','国际考试学部','出国语培线下项目','广州学校（IE）','国际竞赛项目','剑桥英语项目','上海学校（IE）','心理学部','创新项目部','素质成长学部','国际考试在线学部','毛豆学部','青少学部','市场三部','市场四部','青橙项目部','文旅学部','本地化大班学部','市场营销部','直播市场部','创新增长部','学习规划中心','素养初中学部','素养青藤学部','素养小学学部','用户运营部','经营策略部','校园招聘','直播创新部','战略创新部','产研部','业务研发部','教学质量部','Theta项目部','AI素养学部','文旅项目','Theta智学项目部','Theta产研部','V学部','TT初中学部','TT小学学部','产研部','T学部','专题课部（失效）','初中组','文旅项目（失效）')
and performance_third_level_department_name = '市场顾问部'
	    )aa)
,lead_gmv as (
select
rd.*,
n_uid.lead_id
from rd
left join n_uid on rd.user_id1 = n_uid.original_order_user_number and rd.name = n_uid.performance_employee_email_name
where n_uid.rn =1)
-- ★ 新增：bdg_ba主表取渠道判定所需字段
,lead_info as (
    select distinct
        t.lead_id,
        t.rule_name,
        t.flow_pool_name,
        t.third_department_name,
        t.sku_id_name,
        t.ad_account_name,
        t.source_manager_name,
        t.channel_name_1,
        t.channel_name_2,
        t.channel_name_3,
        t.put_plan_name,
        t.channel_provider_name,
        t.channel_second_provider_name,
        t.page_id_name,
        t.source_put_plan_name,
        t.get_customer_way_name,
        t.first_department_name,
        t.second_department_name,
        t.virtual_second_department_name,
        t.virtual_fourth_department_name,
        t.virtual_fifth_department_name,
        t.lead_purchase_intention_name,
        t.lead_purchase_intention_level1_category_name,
        t.lead_purchase_intention_level2_category_name,
        t.lead_create_time,
        t.virtual_leader_email_name as metric_jingli,
        t.virtual_direct_leader_email_name as metric_zhuguan,
        t.employee_email_name as metric_name,
        t.lead_purchase_intention_level2_category_name as metric_grade_1,
        coalesce(t.valid_lead_count, 0) as valid_lead_count,
        coalesce(t.income_amount, 0) as income_amount,
        coalesce(t.in_pay_period_refund_amount, 0) as in_pay_period_refund_amount,
        coalesce(t.non_pay_period_refund_amount, 0) as non_pay_period_refund_amount,
        coalesce(t.same_lead_period_refund_amount, 0) as same_lead_period_refund_amount,
        cast(t.flow_original_order_activity_price as varchar) as flow_original_order_activity_price,
        cast(t.flow_order_price as varchar) as flow_order_price,
        cast(t.flow_orders_income_amount as varchar) as flow_orders_income_amount,
        case
            when cast(date_parse(replace(concat(t.group_period_year, t.group_period_term), '期', ''), '%Y%m%d') as date) between date '2026-07-14' and date '2026-07-19' then '20260716期'
            else concat(cast(date_format(date_trunc('week', date_parse(replace(concat(t.group_period_year, t.group_period_term), '期', ''), '%Y%m%d') - interval '1' day) + interval '4' day, '%Y%m%d') as varchar), '期')
        end as lf_period_name
    from bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df t
    where t.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
      and t.hour = format_datetime(now() - interval '3' hour, 'HH')
      and t.section_assign_employee_first_level_department_name = 'H业务线'
      and t.section_assign_employee_second_level_department_name = '市场部'
      and t.section_assign_employee_third_level_department_name = '市场顾问部'
      and t.period_mapping_first_level_department_name = 'H业务线'
)
,rule as (select
lead_gmv.*,
lf.virtual_fourth_department_name as depart,
-- ★ 0612渠道映射（使用 lead_info 字段）
case when lf.flow_pool_name in ('高途学习规划','智辉老师讲规划') then '市场私域视频号'
when lf.rule_name like '%语数英%' and lf.third_department_name = '新媒体内容运营部' then '语数英'
when lf.flow_pool_name like '%星义大大%' or lf.flow_pool_name like '%星义物理%' then '赵星义'
when lf.rule_name like '%途途私域%' or (lf.rule_name like '%私域%' and lf.first_department_name = 'TT' and lf.rule_name not like '%集团%') then '途途私域'
when lf.third_department_name='图书营销部' and (lf.sku_id_name like '%孟亚飞99%' or lf.sku_id_name like '%亚飞%') and lf.channel_name_2 = '百度' then '孟亚飞-2组-百度'
when lf.third_department_name='图书营销部' and (lf.sku_id_name like '%孟亚飞99%' or lf.sku_id_name like '%亚飞%') and lf.channel_name_2 = '抖音' then '孟亚飞-2组-抖音'
when lf.third_department_name = '投放部' and (lf.ad_account_name like '%周帅%' or lf.put_plan_name like '%周帅%') then '信息流-周帅'
when lf.source_manager_name in ('韩正卿') then '抖音私信'
when lf.third_department_name = '私域运营部' and lf.source_manager_name in ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研','岳一帆02','田起帆','王绍阳') then '进校私域合作'
when lf.channel_name_1='市场私域' and (lf.virtual_fourth_department_name in ('郑州学习顾问二部','郑州学习顾问七部','郑州训练营') or lf.virtual_fifth_department_name in ('罗江博团队')) then '市场私域入群'
when lf.third_department_name = '图书营销部' and (lf.rule_name like '%点睛卷%' or lf.sku_id_name like '%押题卷%')  then '押题卷'
when lf.put_plan_name like '%迪九学%' then '市场私域代运营'
when lf.third_department_name = '投放部' and lf.channel_name_2 = '小红书' and lf.channel_name_1 <> '搜索营销' then '信息流-小红书'
when lf.third_department_name = '线上商务部' and lf.channel_name_2 = '小红书' then '小红书'
when (lf.flow_pool_name like '%肖晗%' or lf.sku_id_name like '%肖晗%' or lf.put_plan_name like '%肖晗9元%') and lf.third_department_name='直播部'  then '肖晗'
when (lf.flow_pool_name like '%北大汤哥%' or lf.flow_pool_name like '%海淀名师高阶%' or lf.flow_pool_name like '%海淀高阶%') and lf.sku_id_name like '%小艺%'  then '郭艺'
when  lf.third_department_name like '%私域%' and lf.rule_name like '%私域%' and lf.rule_name like '%图书%' then '市场私域图书'
when  lf.third_department_name like '%私域%' and lf.rule_name like '%品效%'  then '市场私域品效'
when  lf.third_department_name like '%私域%' and lf.rule_name like '%公域学霸%'  then '市场私域公域组'
when  lf.third_department_name like '%私域%' and lf.rule_name like '%IE%'  then '市场私域IE'
when  lf.third_department_name like '%私域%' and lf.rule_name like '%裂变%'  then '市场私域裂变'
when lf.third_department_name in ('直播部','新媒体内容运营部','市场一组','私域运营部') and lf.put_plan_name like '%退%' and lf.flow_pool_name ='电商退款用户池'  then '退款订单复用'
when lf.third_department_name in ('直播部','新媒体内容运营部','市场一组','私域运营部') and lf.put_plan_name like '%失败%' and lf.flow_pool_name ='电商退款用户池'  then '赠课失败'
when lf.third_department_name in ('直播部','新媒体内容运营部','市场一组')  and (lf.flow_pool_name ='初阶化学规划' or lf.flow_pool_name like '%启迪-初阶老师%')  then '曹忆'
when (lf.third_department_name = '图书营销部' and lf.sku_id_name like '%真题%') or (lf.third_department_name='直播部' and lf.sku_id_name like '%真题%') then '西安图书直播间-直播'
when (lf.third_department_name = '图书营销部' and lf.sku_id_name not like '%真题%') or (lf.third_department_name='直播部' and lf.sku_id_name  like '%秒懂%') or (lf.third_department_name='直播部' and lf.sku_id_name  like '%图书赠送%') then '西安图书直播间-挂链'
when lf.third_department_name in ('直播部','新媒体内容运营部','市场一组') and (lf.flow_pool_name like '%海淀高阶名师%' or lf.flow_pool_name like '%海淀老师高阶%' or lf.flow_pool_name like '%小艺%') then '郭艺'
when lf.put_plan_name like '%国培教育-0元%' or lf.put_plan_name like '%易喆教育-0元%' or lf.put_plan_name like '%钟情-0元%' or lf.put_plan_name like '%中望达-0元%' or lf.put_plan_name like '%晨硕-0元%' or lf.put_plan_name like '%彩石-0元入群%'  then '创新商务入群'
when lf.put_plan_name like '%0元入群-进校%' and lf.third_department_name = '线上商务部' then '创新商务入群'
when lf.third_department_name='KOC孵化部' and lf.flow_pool_name like '%电商退款%' and lf.put_plan_name like '%失败%' then '自孵化KOC-赠课失败'
when lf.third_department_name='KOC孵化部' and lf.flow_pool_name like '%电商退款%' and lf.put_plan_name like '%退%' then '自孵化KOC-退款订单复用'
when lf.source_manager_name = '方俊结01' and lf.put_plan_name like '%赠课后退款%' then 'KOC-赠课后退款' 
when lf.third_department_name = '直播部' and (lf.sku_id_name like '%春春%' or lf.sku_id_name like '%瑞春%' or lf.rule_name like '%春春%' or lf.rule_name like '%瑞春%') then '陈瑞春'
when lf.third_department_name = '直播部' and (lf.sku_id_name like '%朱博士99%' or lf.rule_name like '%朱汉祺99%') then '朱博士99'
when (lf.third_department_name = '直播部' and (lf.sku_id_name like '%朱博士%' or lf.sku_id_name like '%朱汉祺%') and lf.rule_name like '%9%' and lf.rule_name not like '%29%' and lf.sku_id_name not like '%急%' and lf.sku_id_name not like '%礼盒29%') or (lf.third_department_name = '直播部' and lf.sku_id_name like '%朱博士9%') then '朱博士9元'
when lf.ad_account_name like '%春春%' and lf.channel_name_1 = '信息流' then '信息流-陈瑞春'
when lf.channel_name_1 = '信息流' and lf.channel_name_2='B站' and (lf.page_id_name like '%0元物化%') then 'B站信息流-曹忆'
when lf.third_department_name = '直播部' and lf.channel_name_1 = '信息流' and lf.channel_name_2 = 'B站'  then 'B站信息流-亚飞(1元)'
when lf.channel_name_1 = '信息流' and lf.channel_name_2='B站' and (lf.page_id_name like '%亚飞%' or lf.source_put_plan_name like '%亚飞%'  or lf.rule_name like '%亚飞%' or lf.page_id_name like '%初中-0元%') then 'B站信息流-亚飞'
when lf.channel_name_1 = '信息流' and (lf.page_id_name like '%亚飞%' or lf.ad_account_name like '%亚飞%') then '信息流-亚飞'
when (lf.flow_pool_name like '%朱博士%' or lf.flow_pool_name like '%双博士%' or lf.flow_pool_name like '%教育规划%') and lf.third_department_name <> '线上商务部' and lf.lf_period_name not like '%多学科拓展%' and lf.rule_name not like '%张杰%' and lf.sku_id_name not like '%马凯鹏IP%' and lf.third_department_name='直播部' then '朱博士29'
when lf.put_plan_name like '%朱博士说教育%' and lf.lf_period_name not like '%多学科拓展%' and lf.flow_pool_name not like '%高分讲堂%' and  lf.flow_pool_name not like '%总裁%' and lf.third_department_name='直播部' then '朱博士29'
when lf.flow_pool_name like '%朱博士讲英语%' and lf.sku_id_name like '%马凯鹏IP%' and lf.third_department_name='直播部' then '马凯鹏29'
when (lf.flow_pool_name like '%朱博士讲英语%' or lf.flow_pool_name like '%朱博士英语%' or lf.flow_pool_name like '%朱汉祺说英语%' or lf.flow_pool_name like '%朱博士说英语%' or lf.flow_pool_name like '%教育规划%' or lf.flow_pool_name like '%双博士英语规划%' or lf.flow_pool_name like '%朱博士满分英语%' or lf.flow_pool_name like '%英语教父朱博士%' or (lf.flow_pool_name like '%中考决胜天团%' and lf.lead_purchase_intention_level1_category_name = '规划系统')) and lf.third_department_name = '直播部' and lf.lf_period_name not like '%多学科拓展%' and lf.sku_id_name not like '%马凯鹏IP%' and lf.third_department_name='直播部' then '朱博士29'
when (lf.flow_pool_name like '%汤哥%' or lf.flow_pool_name like '%汤老师%') and lf.lf_period_name not like '%多学科拓展%' and lf.third_department_name in ('直播部','新媒体内容运营部')  then '汤老师'
when (lf.flow_pool_name like '%中考百日冲刺%') and lf.lf_period_name not like '%多学科拓展%' and lf.third_department_name='直播部'  then '曹忆9.9纯课'	
when lf.source_manager_name = '陈晓菁04' and lf.channel_provider_name not like '%开拓%' and lf.put_plan_name not like '%九学%' then '商务低价'	
when (lf.flow_pool_name like '%孟帝%' or lf.flow_pool_name like '%孟老师%' or lf.flow_pool_name like '%中考数学冲刺%' or lf.flow_pool_name like '%8升9数学%' or lf.flow_pool_name like '%孟亚飞讲数学%' or lf.flow_pool_name like '%中考冲刺%' or lf.flow_pool_name like '%中考满分冲刺%' or lf.flow_pool_name like '%押题王孟亚飞%' or lf.flow_pool_name like '%中考数学大通关%' or lf.flow_pool_name like '%中考数学规划%' or lf.flow_pool_name like '%亚飞数学%' or lf.flow_pool_name like '%孟帝数学%' or lf.flow_pool_name like '%亚飞秒解思维%')  and lf.lf_period_name not like '%多学科拓展%' and lf.channel_name_2 not like '%KOL%' and lf.third_department_name='直播部' and lf.channel_name_2 = '抖音'  then '孟亚飞-1组-抖音'
when (lf.flow_pool_name like '%孟帝%' or lf.flow_pool_name like '%孟老师%' or lf.flow_pool_name like '%中考数学冲刺%' or lf.flow_pool_name like '%8升9数学%' or lf.flow_pool_name like '%孟亚飞讲数学%' or lf.flow_pool_name like '%中考冲刺%' or lf.flow_pool_name like '%中考满分冲刺%' or lf.flow_pool_name like '%押题王孟亚飞%' or lf.flow_pool_name like '%中考数学大通关%' or lf.flow_pool_name like '%中考数学规划%' or lf.flow_pool_name like '%亚飞数学%' or lf.flow_pool_name like '%孟帝数学%')  and lf.lf_period_name not like '%多学科拓展%' and lf.channel_name_2 not like '%KOL%' and lf.third_department_name='直播部' and lf.channel_name_2 = '视频号'  then '孟亚飞-1组-视频号'
when (lf.flow_pool_name like '%孟帝%' or lf.flow_pool_name like '%孟老师%' or lf.flow_pool_name like '%中考数学冲刺%' or lf.flow_pool_name like '%8升9数学%' or lf.flow_pool_name like '%孟亚飞讲数学%' or lf.flow_pool_name like '%中考冲刺%' or lf.flow_pool_name like '%中考满分冲刺%' or lf.flow_pool_name like '%押题王孟亚飞%' or lf.flow_pool_name like '%中考数学大通关%' or lf.flow_pool_name like '%中考数学规划%' or lf.flow_pool_name like '%亚飞数学%' or lf.flow_pool_name like '%孟帝数学%')  and lf.lf_period_name not like '%多学科拓展%' and lf.channel_name_2 not like '%KOL%' and lf.third_department_name='直播部' and lf.channel_name_2 = 'B站'  then '孟亚飞-1组-B站'
when (lf.flow_pool_name like '%孟帝%' or lf.flow_pool_name like '%孟老师%' or lf.flow_pool_name like '%中考数学冲刺%' or lf.flow_pool_name like '%8升9数学%' or lf.flow_pool_name like '%孟亚飞讲数学%' or lf.flow_pool_name like '%中考冲刺%' or lf.flow_pool_name like '%中考满分冲刺%' or lf.flow_pool_name like '%押题王孟亚飞%' or lf.flow_pool_name like '%中考数学大通关%' or lf.flow_pool_name like '%中考数学规划%' or lf.flow_pool_name like '%亚飞数学%' or lf.flow_pool_name like '%孟帝数学%')  and lf.lf_period_name not like '%多学科拓展%' and lf.channel_name_2 not like '%KOL%' and lf.third_department_name='直播部' and lf.channel_name_2 not like '%百度%'  then '孟亚飞99-1组'
when (lf.flow_pool_name like '%孟帝%' or lf.flow_pool_name like '%孟老师%' or lf.flow_pool_name like '%中考数学冲刺%' or lf.flow_pool_name like '%8升9数学%' or lf.flow_pool_name like '%孟亚飞讲数学%' or lf.flow_pool_name like '%中考冲刺%' or lf.flow_pool_name like '%中考满分冲刺%' or lf.flow_pool_name like '%押题王孟亚飞%' or lf.flow_pool_name like '%中考数学大通关%' or lf.flow_pool_name like '%中考数学规划%' or lf.flow_pool_name like '%亚飞数学%')  and lf.lf_period_name not like '%多学科拓展%' and lf.channel_name_2 not like '%KOL%' and lf.third_department_name='直播部' and lf.channel_name_2 = '百度'  then '孟亚飞-1组-百度'
when (lf.flow_pool_name like '%孟帝%' or lf.flow_pool_name like '%孟老师%' or lf.flow_pool_name like '%中考数学冲刺%' or lf.flow_pool_name like '%8升9数学%' or lf.flow_pool_name like '%孟亚飞讲数学%' or lf.flow_pool_name like '%中考冲刺%' or lf.flow_pool_name like '%中考满分冲刺%' or lf.flow_pool_name like '%押题王孟亚飞%' or lf.flow_pool_name like '%中考数学大通关%' or lf.flow_pool_name like '%中考数学规划%' or lf.flow_pool_name like '%亚飞数学%')  and lf.lf_period_name not like '%多学科拓展%' and lf.channel_name_2 not like '%KOL%' and lf.third_department_name='直播部'  then '孟亚飞9元'
when lf.put_plan_name like '%刘家晋讲图文%' or lf.put_plan_name like '%孟帝数学%' and lf.third_department_name='直播部' and lf.rule_name like '%99%'  then '孟亚飞99-1组'	
when lf.put_plan_name like '%刘家晋讲图文%' or lf.put_plan_name like '%孟帝数学%' and lf.third_department_name='直播部' then '孟亚飞9元'	
when (lf.flow_pool_name like '%肖晗%' or lf.sku_id_name like '%肖晗%') and lf.third_department_name='直播部'  then '肖晗'
when lf.flow_pool_name like '%峥峥%' and lf.lf_period_name not like '%多学科拓展%' and lf.third_department_name='直播部'  then '何峥峥'
when lf.flow_pool_name like '%汐子%' and lf.lf_period_name not like '%多学科拓展%' and lf.sku_id_name not like '%亚飞%' and lf.third_department_name='直播部'  then '王汐子'
when lf.flow_pool_name like '%汐子%' and lf.lf_period_name not like '%多学科拓展%' and lf.sku_id_name  like '%亚飞%' and lf.third_department_name='直播部' and lf.rule_name like '%99%'  then '孟亚飞99-1组'
when lf.flow_pool_name like '%汐子%' and lf.lf_period_name not like '%多学科拓展%' and lf.sku_id_name  like '%亚飞%' and lf.third_department_name='直播部' then '孟亚飞9元'
when (lf.flow_pool_name like '%曹忆%' or lf.flow_pool_name like '%dudu%' or lf.flow_pool_name like '%中考决胜天团%' or lf.flow_pool_name like '%具象思维%' or lf.flow_pool_name like '%在逃发面馒头%' or lf.flow_pool_name like '%库洛米%' and lf.lead_purchase_intention_level1_category_name <> '规划系统') and lf.lf_period_name not like '%多学科拓展%' and lf.third_department_name in ('直播部','新媒体内容运营部') then '曹忆'
when lf.first_department_name ='市场部' and lf.channel_name_1 <> '站内获客' and lf.channel_name_2 <> 'APP' then '集团私域'
when lf.put_plan_name like '%未加好友%' then '市场私域未加好友'
when lf.put_plan_name like '%私域-信息流%' then '市场私域待支付'
when lf.third_department_name = '私域运营部' and lf.rule_name not like '%训练营%' and lf.virtual_fifth_department_name not in ('罗江博团队') and lf.rule_name not like '%复用%' and lf.rule_name not like '%未加好友%' and lf.channel_name_2 <> '内部换量' then '市场私域低价单'
when lf.third_department_name = '私域运营部' and lf.rule_name not like '%训练营%'  and lf.rule_name not like '%复用%' and lf.rule_name not like '%未加好友%' and lf.channel_name_2 <> '内部换量' and lf.flow_original_order_activity_price = '0.0' then '市场私域低价单'
when lf.channel_name_2 in ('APP','M站','PC') and lf.flow_pool_name not like '%途途%' then 'APP'
when lf.channel_provider_name like '%唐山TMK%' then '唐山TMK' 
when lf.source_manager_name in ('高文羽') and lf.channel_provider_name not like '%唐山TMK%' and lf.channel_provider_name not like '%郑州%' then '人工外呼' 
when lf.source_manager_name = '冯银晨' and lf.channel_name_2 = '小红书' then '信息流-小红书'	
when lf.channel_name_1 = '信息流' and lf.channel_name_2 = 'B站' and lf.third_department_name not like '%投放%' and lf.page_id_name like '%汤雪%'  then 'B站信息流-汤学健'
when (lf.channel_name_1 = '信息流' and lf.channel_name_2 <> 'B站' and lf.third_department_name NOT LIKE '%商务%' and lf.put_plan_name not like '%初三0元%' and lf.put_plan_name not like '%抖音私信%' and lf.put_plan_name not like '%高中0元%' and lf.flow_original_order_activity_price not like '%1990%') or (lf.channel_name_2 = 'B站' and lf.third_department_name like '%投放%') then '信息流'
when lf.channel_name_1 = '信息流' and lf.channel_name_2 = 'B站' and lf.third_department_name not like '%投放%' and (lf.page_id_name like '%郭艺%') then 'B站信息流-郭艺'
when lf.channel_name_1 = '信息流' and lf.channel_name_2 = 'B站' and lf.third_department_name not like '%投放%' and (lf.page_id_name like '%朱博士%') then 'B站信息流-朱汉祺'
when lf.channel_name_1 = '信息流' and lf.channel_name_2 = 'B站' and lf.third_department_name not like '%投放%' and lf.page_id_name like '%肖晗%' then 'B站信息流-肖晗'
when lf.channel_name_1 = '信息流' and lf.channel_name_2 = 'B站' and lf.third_department_name not like '%投放%' and (lf.page_id_name like '%马凯鹏%' or lf.ad_account_name like '%化学%') then 'B站信息流-马凯鹏'
when lf.channel_name_1 = '信息流'  and lf.channel_name_2 = 'B站' and lf.third_department_name not like '%投放%' and  (lf.sku_id_name like '%陈瑞春%' or lf.rule_name like '%陈瑞春%') and (lf.ad_account_name  like '%语文%' or lf.source_put_plan_name like '%自然流%' or lf.page_id_name like '%春春%') then 'B站信息流-陈瑞春'
when lf.channel_name_1 = '信息流' and lf.channel_name_2 = 'B站' and lf.third_department_name not like '%投放%' and (lf.flow_original_order_activity_price like '%2990%' or lf.sku_id_name like '%帅师%' or lf.sku_id_name like '%周帅%') and lf.ad_account_name like '%语文%' and  (lf.flow_original_order_activity_price like '%1980%' or lf.flow_original_order_activity_price like '%2980%' or lf.flow_original_order_activity_price like '%2990%') then 'B站信息流-陈瑞春'
when lf.channel_name_1 = '信息流' and lf.channel_name_2 = 'B站' and lf.third_department_name not like '%投放%' and (lf.flow_original_order_activity_price like '%2990%' or lf.sku_id_name like '%帅师%' or lf.sku_id_name like '%周帅%') and lf.ad_account_name not like '%语文%' then 'B站信息流-周帅'
when lf.channel_name_1 = '信息流' and lf.channel_name_2 = 'B站' and lf.third_department_name not like '%投放%' and lf.flow_order_price like '%1980%' and lf.ad_account_name like '%数学%' then 'B站信息流-周帅'
when lf.channel_name_1 = '短直电商' and lf.channel_name_2 = 'B站' and lf.third_department_name  like '%商务%' and   (lf.flow_pool_name like '%春春%' or lf.sku_id_name like '%陈瑞春%')  then 'B站信息流-陈瑞春'
when lf.channel_name_1 = '短直电商' and lf.channel_name_2 = 'B站' and lf.third_department_name  like '%商务%' and  (lf.flow_pool_name like '%朱博士%')  then 'B站信息流-朱汉祺'
--when lf.third_department_name = '线上商务部' and lf.channel_name_2 = 'B站' and lf.put_plan_name like '%春春%' then 'B站信息流-陈瑞春'
--when lf.third_department_name = '线上商务部' and lf.channel_name_2 = 'B站' and lf.put_plan_name like '%朱博士%' then 'B站信息流-朱汉祺'
when lf.channel_name_1 = '信息流' and lf.channel_name_2 = 'B站' and lf.third_department_name not like '%投放%' and lf.flow_original_order_activity_price not like '%2980%' and lf.flow_original_order_activity_price not like '%2990%' and lf.flow_original_order_activity_price not like '%1980%' then 'B站信息流'
when lf.flow_pool_name = '百度搜索引擎' or lf.channel_name_1='搜索营销' then '信息流搜索'
when lf.channel_name_1 = '信息流获客' and lf.channel_name_2 = '小红书' and lf.source_manager_name in ('王慧敏13','张琳02','王樱琦01') then '小红书投放'
when  lf.flow_pool_name like '%小红书班课%' then '小红书投放'
when lf.third_department_name = '投放部' and lf.get_customer_way_name = '短视频信息流' and lf.flow_original_order_activity_price like '%100%' then '信息流'
when lf.flow_pool_name = '中考加油' and lf.sku_id_name like '%孟帝%' then 'KOC-孟亚飞数学'
when lf.flow_pool_name = '中考加油' and lf.sku_id_name  like '%帅师%' then 'KOC-周帅数学'
when lf.flow_pool_name = '中考加油' and lf.sku_id_name  like '%肖晗%' then 'KOC-肖晗'
when  lf.source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07') and (lf.sku_id_name like '%孟帝%' or lf.sku_id_name like '%dudu%' or lf.sku_id_name like '%市场初二%' or lf.rule_name like '%亚飞%' or lf.sku_id_name like '%初二高阳%' or lf.sku_id_name like '%高阳初二%' or lf.sku_id_name like '%精品初二%' or lf.sku_id_name like '%菁英初三%' or (lf.virtual_second_department_name = '菁英班学部' and lf.lead_purchase_intention_level2_category_name='初级' and lf.lead_create_time>= '2026-04-15 00:00:00')) then 'KOC-孟亚飞数学'
when  lf.source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07') and (lf.sku_id_name like '%帅师%' or lf.rule_name like '%周帅%' or lf.sku_id_name like '%9月升高三%') then 'KOC-周帅数学'
when  lf.source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07') and (lf.sku_id_name like '%肖晗%' or lf.rule_name like '%肖晗%') then 'KOC-肖晗'
when  lf.source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07') and lf.lf_period_name not like '%多学科拓展%' and (lf.flow_original_order_activity_price like '%1100%' or lf.flow_original_order_activity_price like '%500%' or lf.flow_orders_income_amount like '%500%') and (lf.sku_id_name like '%朱汉祺%' or lf.sku_id_name like '%朱博士%' or lf.rule_name like '%朱汉祺5元%' or lf.sku_id_name like '%koc5元-朱博士%' or lf.rule_name like '%朱汉祺%') then 'KOC-5元朱汉祺'
when  lf.source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07') and (lf.sku_id_name like '%朱汉祺%' or lf.sku_id_name like '%29元%' or lf.sku_id_name like '%朱博士%' or lf.rule_name like '%朱汉祺%' or lf.rule_name like '%朱博士%' ) and (lf.flow_original_order_activity_price not like '%1100%' or lf.rule_name like '%29%') and lf.sku_id_name not like '%周帅%' then 'KOC-5元朱汉祺'
when  lf.source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07') and lf.lf_period_name not like '%多学科拓展%' and lf.sku_id_name not like '%朱汉祺%' and lf.sku_id_name not like '%朱博士%' and lf.sku_id_name not like '%周帅%' and lf.sku_id_name not like '%29元%' then 'KOC-5元纯课'
when  lf.source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07') and lf.sku_id_name like '%周帅%' then 'KOC-周帅'
--when (lf.channel_name_2 like '%KOL%' and lf.source_manager_name in ('崔文轩','孙培尧')) or (lf.channel_name_2 like '%抖音%' and lf.source_manager_name in ('徐绮鹤')) and lf.lf_period_name not like '%多学科拓展%' then '自孵化KOC'
when lf.third_department_name in ('品牌效能部','KOC孵化部') and lf.channel_name_2 in ('抖音','视频号','快手','KOL')  then '自孵化KOC-5元纯课'
when lf.third_department_name in ('品牌效能部','KOC孵化部') and lf.channel_name_2 in ('抖音','视频号','快手','KOL') and (lf.sku_id_name like '%5元%'or lf.sku_id_name like '%11元%' or lf.flow_original_order_activity_price like '%1100%' or lf.flow_original_order_activity_price like '%500%' or lf.flow_orders_income_amount  like '%1100%' or lf.flow_orders_income_amount  like '%500%' ) then '自孵化KOC-5元纯课'
when lf.source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') and lf.channel_name_2 like '%社群%' then '进校社群'
when lf.source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') and lf.channel_name_2 like '%直推%' then '进校直推'
when lf.source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') and lf.channel_name_2 like '%TMK%' and lf.page_id_name like '%1元%' then '进校TMK1元'
when lf.source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') and lf.channel_name_2 like '%TMK%' and lf.page_id_name like '%9元%' then '进校TMK9元'
when lf.source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') and lf.channel_name_2 like '%书商%' then '进校书商'
when lf.source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') and lf.channel_name_2 like '%综合%' and lf.put_plan_name like '%18%' then '进校直播'
when lf.source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') and lf.channel_name_2 like '%直播%' then '进校直播'
when lf.source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04') and lf.put_plan_name not like '%0元%' and lf.flow_pool_name not like '%家校共育%' and lf.flow_pool_name not like '%保持热爱%' and lf.flow_pool_name not like '%青松%' and lf.flow_pool_name not like '%原子初三%' and lf.flow_pool_name not like '%南通欣创%' and lf.flow_pool_name not like '%悟之道%' and lf.flow_pool_name not like '%济南梦航%' and lf.channel_name_3 <> '社群' and lf.put_plan_name not like '%善悟%' and lf.put_plan_name not like '%人人通%'  and lf.put_plan_name not like '%%济南格乐' and lf.flow_pool_name not like '%晨硕智学%' and lf.flow_pool_name not like '%兴尧文化%'  and lf.flow_pool_name not like '%济南映像%' and lf.flow_pool_name not like '%山东简单%' and lf.flow_pool_name not like '%争鸣科技%'  then '商务低价'
when lf.flow_pool_name like '%原子初三%' or lf.flow_pool_name like '%原子系统%'  then '原子'
when lf.flow_pool_name like '%市场部-公转私%' then '市场私域公导私'
when lf.flow_pool_name like '%南通欣创%' or  lf.flow_pool_name like '%人人通科技%' or lf.flow_pool_name like '%易而购%' or lf.flow_pool_name like '%济南梦航%' or lf.flow_pool_name like '%晨硕智学%' or lf.flow_pool_name like '%兴尧文化%' or lf.flow_pool_name like '%济南映像%' or lf.flow_pool_name like '%山东简单%' or lf.flow_pool_name like '%争鸣科技%'  then '进校私域合作'
when (lf.flow_pool_name like '%家校共育%' or lf.flow_pool_name like '%保持热爱%' or lf.flow_pool_name like '%青松%' or lf.flow_pool_name like '%悟之道%') and lf.put_plan_name not like '%0元%'  then '进校私域合作'
when lf.source_manager_name = '李宁24' and lf.put_plan_name like '%0转低%' then '进校私域合作'
when lf.third_department_name = '私域运营部' and  lf.flow_original_order_activity_price in ('100.0','900.0','300.0')  then '进校私域合作'
when lf.third_department_name = '私域运营部' and  lf.flow_original_order_activity_price in ('0.0') and lf.source_manager_name in ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研') then '进校私域合作'
when lf.third_department_name = '私域运营部' and lf.channel_name_1='市场私域' and lf.put_plan_name not like '%公导私%' and lf.put_plan_name not like '%公转私%' and lf.flow_original_order_activity_price = '0.0' and lf.rule_name not like '%激活%' and lf.rule_name not like '%咨询%' and lf.rule_name not like '%训练营%'  and lf.virtual_fifth_department_name not like '%罗江博%' and lf.virtual_fifth_department_name not like '%郑州学习顾问二部%' and lf.source_manager_name not in ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研') then '市场私域低价单'
when lf.source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and lf.channel_provider_name like '%格乐教育%' and lf.channel_name_2 like '%直播%' then '创新社群'
when lf.source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and lf.channel_name_2 like '%社群%' then '创新社群'
when lf.source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and (lf.channel_name_2 like '%直推%' or lf.put_plan_name like '%直推%') then '创新直推'
when lf.source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and (lf.channel_name_2 like '%书商%' or lf.put_plan_name like '%书商%' or lf.page_id_name like '%书商%') then '创新书商'
when lf.source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and lf.channel_name_2 like '%TMK%' and lf.page_id_name like '%1元%' then '创新TMK1元'
when lf.source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and lf.channel_name_2 like '%TMK%' and lf.page_id_name like '%9元%' then '创新TMK9元'
when lf.source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and (lf.channel_name_2 like '%直播%' or lf.page_id_name like '%进校%') then '创新直播'
when lf.source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and lf.channel_name_2<>'公众号' and lf.channel_name_1 = '商务' and lf.flow_pool_name <> '高途云集图书专营店-自然流' and lf.flow_pool_name <> '高途旗舰店—线索—yuxinru' and lf.put_plan_name not like '%社群%' and lf.put_plan_name not like '%小红书班课%' and lf.put_plan_name not like '%外部图书供量%' and lf.channel_second_provider_name not like '%沃德丰店铺线索赠课%' and lf.channel_second_provider_name not like '%智慧城-图书%' and lf.put_plan_name not like '%育甲%' and lf.flow_pool_name not like '%周长磊%'  then '创新商务'
when lf.flow_pool_name like '%周长磊%' then '创新APP'
when lf.source_manager_name in ('王春宵') then '武汉图书直播间'
when lf.source_manager_name in ('高曼曼01','杨思怡','宋向函') then '图书KOC达人'
when lf.flow_pool_name like '%市场部-原子合作%' then '原子'
when lf.flow_pool_name like '%市场部-微信私域%' or lf.flow_pool_name like '%市场部-规划报告%' or lf.flow_pool_name like '%规划报告%' or lf.flow_pool_name like '%市场部-小红书%' or lf.flow_pool_name like '%孟浩宇%' then '市场私域低价单'
when lf.flow_pool_name like '%待支付%' then '市场私域待支付'
when lf.flow_pool_name like '%未加好友%' then '市场私域未加好友'
when lf.flow_pool_name like '%内部换量%' then '市场私域首期掉海'
when lf.flow_pool_name like '公导私' then '进校私域合作'
when (lf.flow_pool_name like '%增长组%' or lf.channel_name_3 = '公众号' or lf.second_department_name = '微信生态部') and lf.channel_name_2 <> 'APP' then '集团私域'
when lf.put_plan_name  like '%济南格乐%' and lf.put_plan_name  like '%表单%'  then '商务0元'
when lf.put_plan_name like '%B类%' or lf.put_plan_name like '%b类%' or lf.channel_second_provider_name like '%KOC当期%' then 'KOC分层测试'
when lf.put_plan_name like '%星耀%' or lf.put_plan_name like '%物理展博%' or  lf.put_plan_name like '%物理谢丽荣%' or lf.put_plan_name like '%牟恩伯%' or  lf.put_plan_name like '%王赞%' or lf.put_plan_name like '%张磊老师高中数学%' or lf.put_plan_name like '%雯姐高中物理大讲堂%' then '百度星耀'
when lf.source_manager_name = '刘福云' and (lf.sku_id_name like '%瑞春%' or lf.sku_id_name like '%春春%') then '陈瑞春'
when lf.source_manager_name = '刘福云' and lf.sku_id_name like '%周帅%' then '周帅'
when lf.third_department_name = '直播部' and lf.sku_id_name like '%周帅%' and lf.channel_name_2 in ('百度','B站')  then '周帅'
when lf.third_department_name = '直播部' and lf.sku_id_name like '%孟亚飞%' and lf.rule_name like '%99%' then '孟亚飞99-1组'
when lf.third_department_name = '直播部' and lf.sku_id_name like '%孟亚飞%' then '孟亚飞9元'
when lf.third_department_name = '直播部' and lf.sku_id_name like '%朱汉祺%' then '朱博士29'
when lf.third_department_name = '直播部' and lf.sku_id_name like '%肖晗%' then '肖晗'
when lf.flow_pool_name like '%0转低转正%' or lf.channel_name_2='产研测试' then '进校私域合作'
when lf.flow_pool_name like '%天津智慧双子%'	then '创新社群'
when lf.third_department_name like '%城市定制%' then '点睛卷'	
when lf.lf_period_name like '%多学科拓展%' and lf.third_department_name like '%私域运营%' then '市场私域入群'
when lf.put_plan_name like '%赠课失败%' and lf.third_department_name = '线上商务部' then 'KOC赠课失败'
when lf.flow_pool_name like '%自然流%' and lf.source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07') and lf.sku_id_name like '%周帅%' then 'KOC-周帅'	
when lf.flow_pool_name like '%自然流%' and lf.source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07') and lf.sku_id_name like '%肖晗%' then 'KOC-肖晗'	
when lf.flow_pool_name like '%自然流%' and lf.source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07') and lf.sku_id_name like '%朱汉祺%'  and lf.flow_original_order_activity_price like '%1100%' then 'KOC-5元朱汉祺'
when lf.flow_pool_name like '%自然流%' and lf.source_manager_name in ('赵语诗','崔文轩','孙培尧')	then '自孵化KOC-5元纯课'
when lf.flow_pool_name like '%自然流%' and (lf.sku_id_name like '%朱博士%' or lf.sku_id_name like '%朱汉祺%') and lf.rule_name like '%9%' and lf.rule_name not like '%29%' and lf.third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '朱博士9元'
when lf.flow_pool_name like '%自然流%' and lf.sku_id_name like '%朱博士%' and lf.third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '朱博士29'
when lf.flow_pool_name like '%自然流%' and lf.sku_id_name like '%亚飞%' and lf.rule_name like '%99%' and lf.third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '孟亚飞99-1组'	
when lf.flow_pool_name like '%自然流%' and lf.sku_id_name like '%亚飞%' and lf.third_department_name  in ('直播部','新媒体内容运营部','市场一组')  then '孟亚飞9元'	
when lf.flow_pool_name like '%自然流%' and lf.sku_id_name like '%曹忆%' then '曹忆'	
when lf.flow_pool_name like '%自然流%' and lf.rule_name like '%朱博士%' and lf.third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '朱博士29'
when lf.flow_pool_name like '%自然流%' and lf.source_manager_name like '%邵万昕%' and lf.third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '朱博士29'
when lf.flow_pool_name like '%自然流%' and lf.rule_name like '%亚飞%' and lf.rule_name like '%99%' then '孟亚飞99-1组'	
when lf.flow_pool_name like '%自然流%' and lf.rule_name like '%亚飞%'  then '孟亚飞9元'	
when lf.flow_pool_name like '%自然流%' and lf.rule_name like '%郭艺%'  then '郭艺'
when lf.flow_pool_name like '%自然流%' and lf.rule_name like '%汤雪%'  then '汤老师'	
when lf.flow_pool_name like '%自然流%' and lf.rule_name like '%曹忆%' then '曹忆'		
when lf.flow_pool_name like '%途途教室%' or lf.first_department_name like 'TUTU' then '途途APP'
when lf.second_department_name = '市场四部' then '市场四部'
when lf.source_manager_name in ('宋莹莹','辛世如') and lf.channel_name_2 in ('视频号') then '信息流-虚拟号挂车'
when lf.rule_name like '%训练营%' and lf.rule_name like '%市场私域%' then '市场私域入群'
when lf.flow_pool_name like '%青少-私域%' then '青少私域'
when lf.put_plan_name like '%AI名师%' then 'AI直播'
when lf.channel_name_1= '信息流' and (lf.put_plan_name like '%抖音私信%' or lf.put_plan_name like '%初三0元%' or lf.put_plan_name like '%高中0元%') then '信息流-抖音私信'
when lf.rule_name like '%途途私域%' or (lf.rule_name like '%私域%' and lf.first_department_name = 'TT') then '途途私域'
else '其他未知流量' end as channel_1,
rr.rule_name as rr_rule_name
,coalesce(
    lf.lf_period_name,
    case
        when regexp_like(rr.group_period_term, '^[0-9]{8}期$')
             and cast(date_parse(substr(rr.group_period_term, 1, 8), '%Y%m%d') as date) between date '2026-07-14' and date '2026-07-19'
        then '20260716期'
        when regexp_like(rr.group_period_term, '^[0-9]{4}期$')
             and substr(lead_gmv.qici, 1, 4) = '2026'
             and substr(rr.group_period_term, 1, 4) between '0714' and '0719'
        then '20260716期'
        when regexp_like(rr.group_period_term, '^[0-9]{8}期$')
        then date_format(
            date_trunc('week', date_parse(substr(rr.group_period_term, 1, 8), '%Y%m%d') - interval '1' day) + interval '4' day,
            '%Y%m%d'
        ) || '期'
        when regexp_like(rr.group_period_term, '^[0-9]{4}期$')
        then date_format(
            date_trunc(
                'week',
                date_parse(
                    concat(
                        case
                            when cast(substr(rr.group_period_term, 1, 2) as integer) >= 11
                                 and cast(substr(lead_gmv.qici, 5, 2) as integer) <= 2
                            then cast(cast(substr(lead_gmv.qici, 1, 4) as integer) - 1 as varchar)
                            else substr(lead_gmv.qici, 1, 4)
                        end,
                        substr(rr.group_period_term, 1, 4)
                    ),
                    '%Y%m%d'
                ) - interval '1' day
            ) + interval '4' day,
            '%Y%m%d'
        ) || '期'
        else null
    end
) as friday_period
from lead_gmv
left join lead_info lf on lead_gmv.lead_id = lf.lead_id
left join (
	select *,case
    when instr(rule_name, '期') > 0
         and instr(rule_name, '期') >= 9
         and regexp_like(substr(rule_name, instr(rule_name, '期') - 8, 8), '^[0-9]{8}$')
    then substr(rule_name, instr(rule_name, '期') - 8, 9)
    when instr(rule_name, '期') > 0
         and instr(rule_name, '期') >= 5
         and regexp_like(substr(rule_name, instr(rule_name, '期') - 4, 4), '^[0-9]{4}$')
    then substr(rule_name, instr(rule_name, '期') - 4, 5)
    else null
end as group_period_term
	from service_dw.dim_crm_assign_rule_lead_detail_hf
	where dt = format_datetime(NOW() - interval '2' hour, 'YYYYMMdd')
    and hour = format_datetime(NOW() - interval '2' hour, 'HH')
)rr on lead_gmv.lead_id = rr.lead_id and lead_gmv.email_prefix = rr.account_domain)
,lead_metric_mapped as (
    select
        lf.*,
        case when lf.flow_pool_name in ('高途学习规划','智辉老师讲规划') then '市场私域视频号'
when lf.rule_name like '%语数英%' and lf.third_department_name = '新媒体内容运营部' then '语数英'
when lf.flow_pool_name like '%星义大大%' or lf.flow_pool_name like '%星义物理%' then '赵星义'
when lf.rule_name like '%途途私域%' or (lf.rule_name like '%私域%' and lf.first_department_name = 'TT' and lf.rule_name not like '%集团%') then '途途私域'
when lf.third_department_name='图书营销部' and (lf.sku_id_name like '%孟亚飞99%' or lf.sku_id_name like '%亚飞%') and lf.channel_name_2 = '百度' then '孟亚飞-2组-百度'
when lf.third_department_name='图书营销部' and (lf.sku_id_name like '%孟亚飞99%' or lf.sku_id_name like '%亚飞%') and lf.channel_name_2 = '抖音' then '孟亚飞-2组-抖音'
when lf.third_department_name = '投放部' and (lf.ad_account_name like '%周帅%' or lf.put_plan_name like '%周帅%') then '信息流-周帅'
when lf.source_manager_name in ('韩正卿') then '抖音私信'
when lf.third_department_name = '私域运营部' and lf.source_manager_name in ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研','岳一帆02','田起帆','王绍阳') then '进校私域合作'
when lf.channel_name_1='市场私域' and (lf.virtual_fourth_department_name in ('郑州学习顾问二部','郑州学习顾问七部','郑州训练营') or lf.virtual_fifth_department_name in ('罗江博团队')) then '市场私域入群'
when lf.third_department_name = '图书营销部' and (lf.rule_name like '%点睛卷%' or lf.sku_id_name like '%押题卷%')  then '押题卷'
when lf.put_plan_name like '%迪九学%' then '市场私域代运营'
when lf.third_department_name = '投放部' and lf.channel_name_2 = '小红书' and lf.channel_name_1 <> '搜索营销' then '信息流-小红书'
when lf.third_department_name = '线上商务部' and lf.channel_name_2 = '小红书' then '小红书'
when (lf.flow_pool_name like '%肖晗%' or lf.sku_id_name like '%肖晗%' or lf.put_plan_name like '%肖晗9元%') and lf.third_department_name='直播部'  then '肖晗'
when (lf.flow_pool_name like '%北大汤哥%' or lf.flow_pool_name like '%海淀名师高阶%' or lf.flow_pool_name like '%海淀高阶%') and lf.sku_id_name like '%小艺%'  then '郭艺'
when  lf.third_department_name like '%私域%' and lf.rule_name like '%私域%' and lf.rule_name like '%图书%' then '市场私域图书'
when  lf.third_department_name like '%私域%' and lf.rule_name like '%品效%'  then '市场私域品效'
when  lf.third_department_name like '%私域%' and lf.rule_name like '%公域学霸%'  then '市场私域公域组'
when  lf.third_department_name like '%私域%' and lf.rule_name like '%IE%'  then '市场私域IE'
when  lf.third_department_name like '%私域%' and lf.rule_name like '%裂变%'  then '市场私域裂变'
when lf.third_department_name in ('直播部','新媒体内容运营部','市场一组','私域运营部') and lf.put_plan_name like '%退%' and lf.flow_pool_name ='电商退款用户池'  then '退款订单复用'
when lf.third_department_name in ('直播部','新媒体内容运营部','市场一组','私域运营部') and lf.put_plan_name like '%失败%' and lf.flow_pool_name ='电商退款用户池'  then '赠课失败'
when lf.third_department_name in ('直播部','新媒体内容运营部','市场一组')  and (lf.flow_pool_name ='初阶化学规划' or lf.flow_pool_name like '%启迪-初阶老师%')  then '曹忆'
when (lf.third_department_name = '图书营销部' and lf.sku_id_name like '%真题%') or (lf.third_department_name='直播部' and lf.sku_id_name like '%真题%') then '西安图书直播间-直播'
when (lf.third_department_name = '图书营销部' and lf.sku_id_name not like '%真题%') or (lf.third_department_name='直播部' and lf.sku_id_name  like '%秒懂%') or (lf.third_department_name='直播部' and lf.sku_id_name  like '%图书赠送%') then '西安图书直播间-挂链'
when lf.third_department_name in ('直播部','新媒体内容运营部','市场一组') and (lf.flow_pool_name like '%海淀高阶名师%' or lf.flow_pool_name like '%海淀老师高阶%' or lf.flow_pool_name like '%小艺%') then '郭艺'
when lf.put_plan_name like '%国培教育-0元%' or lf.put_plan_name like '%易喆教育-0元%' or lf.put_plan_name like '%钟情-0元%' or lf.put_plan_name like '%中望达-0元%' or lf.put_plan_name like '%晨硕-0元%' or lf.put_plan_name like '%彩石-0元入群%'  then '创新商务入群'
when lf.put_plan_name like '%0元入群-进校%' and lf.third_department_name = '线上商务部' then '创新商务入群'
when lf.third_department_name='KOC孵化部' and lf.flow_pool_name like '%电商退款%' and lf.put_plan_name like '%失败%' then '自孵化KOC-赠课失败'
when lf.third_department_name='KOC孵化部' and lf.flow_pool_name like '%电商退款%' and lf.put_plan_name like '%退%' then '自孵化KOC-退款订单复用'
when lf.source_manager_name = '方俊结01' and lf.put_plan_name like '%赠课后退款%' then 'KOC-赠课后退款' 
when lf.third_department_name = '直播部' and (lf.sku_id_name like '%春春%' or lf.sku_id_name like '%瑞春%' or lf.rule_name like '%春春%' or lf.rule_name like '%瑞春%') then '陈瑞春'
when lf.third_department_name = '直播部' and (lf.sku_id_name like '%朱博士99%' or lf.rule_name like '%朱汉祺99%') then '朱博士99'
when (lf.third_department_name = '直播部' and (lf.sku_id_name like '%朱博士%' or lf.sku_id_name like '%朱汉祺%') and lf.rule_name like '%9%' and lf.rule_name not like '%29%' and lf.sku_id_name not like '%急%' and lf.sku_id_name not like '%礼盒29%') or (lf.third_department_name = '直播部' and lf.sku_id_name like '%朱博士9%') then '朱博士9元'
when lf.ad_account_name like '%春春%' and lf.channel_name_1 = '信息流' then '信息流-陈瑞春'
when lf.channel_name_1 = '信息流' and lf.channel_name_2='B站' and (lf.page_id_name like '%0元物化%') then 'B站信息流-曹忆'
when lf.third_department_name = '直播部' and lf.channel_name_1 = '信息流' and lf.channel_name_2 = 'B站'  then 'B站信息流-亚飞(1元)'
when lf.channel_name_1 = '信息流' and lf.channel_name_2='B站' and (lf.page_id_name like '%亚飞%' or lf.source_put_plan_name like '%亚飞%'  or lf.rule_name like '%亚飞%' or lf.page_id_name like '%初中-0元%') then 'B站信息流-亚飞'
when lf.channel_name_1 = '信息流' and (lf.page_id_name like '%亚飞%' or lf.ad_account_name like '%亚飞%') then '信息流-亚飞'
when (lf.flow_pool_name like '%朱博士%' or lf.flow_pool_name like '%双博士%' or lf.flow_pool_name like '%教育规划%') and lf.third_department_name <> '线上商务部' and lf.lf_period_name not like '%多学科拓展%' and lf.rule_name not like '%张杰%' and lf.sku_id_name not like '%马凯鹏IP%' and lf.third_department_name='直播部' then '朱博士29'
when lf.put_plan_name like '%朱博士说教育%' and lf.lf_period_name not like '%多学科拓展%' and lf.flow_pool_name not like '%高分讲堂%' and  lf.flow_pool_name not like '%总裁%' and lf.third_department_name='直播部' then '朱博士29'
when lf.flow_pool_name like '%朱博士讲英语%' and lf.sku_id_name like '%马凯鹏IP%' and lf.third_department_name='直播部' then '马凯鹏29'
when (lf.flow_pool_name like '%朱博士讲英语%' or lf.flow_pool_name like '%朱博士英语%' or lf.flow_pool_name like '%朱汉祺说英语%' or lf.flow_pool_name like '%朱博士说英语%' or lf.flow_pool_name like '%教育规划%' or lf.flow_pool_name like '%双博士英语规划%' or lf.flow_pool_name like '%朱博士满分英语%' or lf.flow_pool_name like '%英语教父朱博士%' or (lf.flow_pool_name like '%中考决胜天团%' and lf.lead_purchase_intention_level1_category_name = '规划系统')) and lf.third_department_name = '直播部' and lf.lf_period_name not like '%多学科拓展%' and lf.sku_id_name not like '%马凯鹏IP%' and lf.third_department_name='直播部' then '朱博士29'
when (lf.flow_pool_name like '%汤哥%' or lf.flow_pool_name like '%汤老师%') and lf.lf_period_name not like '%多学科拓展%' and lf.third_department_name in ('直播部','新媒体内容运营部')  then '汤老师'
when (lf.flow_pool_name like '%中考百日冲刺%') and lf.lf_period_name not like '%多学科拓展%' and lf.third_department_name='直播部'  then '曹忆9.9纯课'	
when lf.source_manager_name = '陈晓菁04' and lf.channel_provider_name not like '%开拓%' and lf.put_plan_name not like '%九学%' then '商务低价'	
when (lf.flow_pool_name like '%孟帝%' or lf.flow_pool_name like '%孟老师%' or lf.flow_pool_name like '%中考数学冲刺%' or lf.flow_pool_name like '%8升9数学%' or lf.flow_pool_name like '%孟亚飞讲数学%' or lf.flow_pool_name like '%中考冲刺%' or lf.flow_pool_name like '%中考满分冲刺%' or lf.flow_pool_name like '%押题王孟亚飞%' or lf.flow_pool_name like '%中考数学大通关%' or lf.flow_pool_name like '%中考数学规划%' or lf.flow_pool_name like '%亚飞数学%' or lf.flow_pool_name like '%孟帝数学%' or lf.flow_pool_name like '%亚飞秒解思维%')  and lf.lf_period_name not like '%多学科拓展%' and lf.channel_name_2 not like '%KOL%' and lf.third_department_name='直播部' and lf.channel_name_2 = '抖音'  then '孟亚飞-1组-抖音'
when (lf.flow_pool_name like '%孟帝%' or lf.flow_pool_name like '%孟老师%' or lf.flow_pool_name like '%中考数学冲刺%' or lf.flow_pool_name like '%8升9数学%' or lf.flow_pool_name like '%孟亚飞讲数学%' or lf.flow_pool_name like '%中考冲刺%' or lf.flow_pool_name like '%中考满分冲刺%' or lf.flow_pool_name like '%押题王孟亚飞%' or lf.flow_pool_name like '%中考数学大通关%' or lf.flow_pool_name like '%中考数学规划%' or lf.flow_pool_name like '%亚飞数学%' or lf.flow_pool_name like '%孟帝数学%')  and lf.lf_period_name not like '%多学科拓展%' and lf.channel_name_2 not like '%KOL%' and lf.third_department_name='直播部' and lf.channel_name_2 = '视频号'  then '孟亚飞-1组-视频号'
when (lf.flow_pool_name like '%孟帝%' or lf.flow_pool_name like '%孟老师%' or lf.flow_pool_name like '%中考数学冲刺%' or lf.flow_pool_name like '%8升9数学%' or lf.flow_pool_name like '%孟亚飞讲数学%' or lf.flow_pool_name like '%中考冲刺%' or lf.flow_pool_name like '%中考满分冲刺%' or lf.flow_pool_name like '%押题王孟亚飞%' or lf.flow_pool_name like '%中考数学大通关%' or lf.flow_pool_name like '%中考数学规划%' or lf.flow_pool_name like '%亚飞数学%' or lf.flow_pool_name like '%孟帝数学%')  and lf.lf_period_name not like '%多学科拓展%' and lf.channel_name_2 not like '%KOL%' and lf.third_department_name='直播部' and lf.channel_name_2 = 'B站'  then '孟亚飞-1组-B站'
when (lf.flow_pool_name like '%孟帝%' or lf.flow_pool_name like '%孟老师%' or lf.flow_pool_name like '%中考数学冲刺%' or lf.flow_pool_name like '%8升9数学%' or lf.flow_pool_name like '%孟亚飞讲数学%' or lf.flow_pool_name like '%中考冲刺%' or lf.flow_pool_name like '%中考满分冲刺%' or lf.flow_pool_name like '%押题王孟亚飞%' or lf.flow_pool_name like '%中考数学大通关%' or lf.flow_pool_name like '%中考数学规划%' or lf.flow_pool_name like '%亚飞数学%' or lf.flow_pool_name like '%孟帝数学%')  and lf.lf_period_name not like '%多学科拓展%' and lf.channel_name_2 not like '%KOL%' and lf.third_department_name='直播部' and lf.channel_name_2 not like '%百度%'  then '孟亚飞99-1组'
when (lf.flow_pool_name like '%孟帝%' or lf.flow_pool_name like '%孟老师%' or lf.flow_pool_name like '%中考数学冲刺%' or lf.flow_pool_name like '%8升9数学%' or lf.flow_pool_name like '%孟亚飞讲数学%' or lf.flow_pool_name like '%中考冲刺%' or lf.flow_pool_name like '%中考满分冲刺%' or lf.flow_pool_name like '%押题王孟亚飞%' or lf.flow_pool_name like '%中考数学大通关%' or lf.flow_pool_name like '%中考数学规划%' or lf.flow_pool_name like '%亚飞数学%')  and lf.lf_period_name not like '%多学科拓展%' and lf.channel_name_2 not like '%KOL%' and lf.third_department_name='直播部' and lf.channel_name_2 = '百度'  then '孟亚飞-1组-百度'
when (lf.flow_pool_name like '%孟帝%' or lf.flow_pool_name like '%孟老师%' or lf.flow_pool_name like '%中考数学冲刺%' or lf.flow_pool_name like '%8升9数学%' or lf.flow_pool_name like '%孟亚飞讲数学%' or lf.flow_pool_name like '%中考冲刺%' or lf.flow_pool_name like '%中考满分冲刺%' or lf.flow_pool_name like '%押题王孟亚飞%' or lf.flow_pool_name like '%中考数学大通关%' or lf.flow_pool_name like '%中考数学规划%' or lf.flow_pool_name like '%亚飞数学%')  and lf.lf_period_name not like '%多学科拓展%' and lf.channel_name_2 not like '%KOL%' and lf.third_department_name='直播部'  then '孟亚飞9元'
when lf.put_plan_name like '%刘家晋讲图文%' or lf.put_plan_name like '%孟帝数学%' and lf.third_department_name='直播部' and lf.rule_name like '%99%'  then '孟亚飞99-1组'	
when lf.put_plan_name like '%刘家晋讲图文%' or lf.put_plan_name like '%孟帝数学%' and lf.third_department_name='直播部' then '孟亚飞9元'	
when (lf.flow_pool_name like '%肖晗%' or lf.sku_id_name like '%肖晗%') and lf.third_department_name='直播部'  then '肖晗'
when lf.flow_pool_name like '%峥峥%' and lf.lf_period_name not like '%多学科拓展%' and lf.third_department_name='直播部'  then '何峥峥'
when lf.flow_pool_name like '%汐子%' and lf.lf_period_name not like '%多学科拓展%' and lf.sku_id_name not like '%亚飞%' and lf.third_department_name='直播部'  then '王汐子'
when lf.flow_pool_name like '%汐子%' and lf.lf_period_name not like '%多学科拓展%' and lf.sku_id_name  like '%亚飞%' and lf.third_department_name='直播部' and lf.rule_name like '%99%'  then '孟亚飞99-1组'
when lf.flow_pool_name like '%汐子%' and lf.lf_period_name not like '%多学科拓展%' and lf.sku_id_name  like '%亚飞%' and lf.third_department_name='直播部' then '孟亚飞9元'
when (lf.flow_pool_name like '%曹忆%' or lf.flow_pool_name like '%dudu%' or lf.flow_pool_name like '%中考决胜天团%' or lf.flow_pool_name like '%具象思维%' or lf.flow_pool_name like '%在逃发面馒头%' or lf.flow_pool_name like '%库洛米%' and lf.lead_purchase_intention_level1_category_name <> '规划系统') and lf.lf_period_name not like '%多学科拓展%' and lf.third_department_name in ('直播部','新媒体内容运营部') then '曹忆'
when lf.first_department_name ='市场部' and lf.channel_name_1 <> '站内获客' and lf.channel_name_2 <> 'APP' then '集团私域'
when lf.put_plan_name like '%未加好友%' then '市场私域未加好友'
when lf.put_plan_name like '%私域-信息流%' then '市场私域待支付'
when lf.third_department_name = '私域运营部' and lf.rule_name not like '%训练营%' and lf.virtual_fifth_department_name not in ('罗江博团队') and lf.rule_name not like '%复用%' and lf.rule_name not like '%未加好友%' and lf.channel_name_2 <> '内部换量' then '市场私域低价单'
when lf.third_department_name = '私域运营部' and lf.rule_name not like '%训练营%'  and lf.rule_name not like '%复用%' and lf.rule_name not like '%未加好友%' and lf.channel_name_2 <> '内部换量' and lf.flow_original_order_activity_price = '0.0' then '市场私域低价单'
when lf.channel_name_2 in ('APP','M站','PC') and lf.flow_pool_name not like '%途途%' then 'APP'
when lf.channel_provider_name like '%唐山TMK%' then '唐山TMK' 
when lf.source_manager_name in ('高文羽') and lf.channel_provider_name not like '%唐山TMK%' and lf.channel_provider_name not like '%郑州%' then '人工外呼' 
when lf.source_manager_name = '冯银晨' and lf.channel_name_2 = '小红书' then '信息流-小红书'	
when lf.channel_name_1 = '信息流' and lf.channel_name_2 = 'B站' and lf.third_department_name not like '%投放%' and lf.page_id_name like '%汤雪%'  then 'B站信息流-汤学健'
when (lf.channel_name_1 = '信息流' and lf.channel_name_2 <> 'B站' and lf.third_department_name NOT LIKE '%商务%' and lf.put_plan_name not like '%初三0元%' and lf.put_plan_name not like '%抖音私信%' and lf.put_plan_name not like '%高中0元%' and lf.flow_original_order_activity_price not like '%1990%') or (lf.channel_name_2 = 'B站' and lf.third_department_name like '%投放%') then '信息流'
when lf.channel_name_1 = '信息流' and lf.channel_name_2 = 'B站' and lf.third_department_name not like '%投放%' and (lf.page_id_name like '%郭艺%') then 'B站信息流-郭艺'
when lf.channel_name_1 = '信息流' and lf.channel_name_2 = 'B站' and lf.third_department_name not like '%投放%' and (lf.page_id_name like '%朱博士%') then 'B站信息流-朱汉祺'
when lf.channel_name_1 = '信息流' and lf.channel_name_2 = 'B站' and lf.third_department_name not like '%投放%' and lf.page_id_name like '%肖晗%' then 'B站信息流-肖晗'
when lf.channel_name_1 = '信息流' and lf.channel_name_2 = 'B站' and lf.third_department_name not like '%投放%' and (lf.page_id_name like '%马凯鹏%' or lf.ad_account_name like '%化学%') then 'B站信息流-马凯鹏'
when lf.channel_name_1 = '信息流'  and lf.channel_name_2 = 'B站' and lf.third_department_name not like '%投放%' and  (lf.sku_id_name like '%陈瑞春%' or lf.rule_name like '%陈瑞春%') and (lf.ad_account_name  like '%语文%' or lf.source_put_plan_name like '%自然流%' or lf.page_id_name like '%春春%') then 'B站信息流-陈瑞春'
when lf.channel_name_1 = '信息流' and lf.channel_name_2 = 'B站' and lf.third_department_name not like '%投放%' and (lf.flow_original_order_activity_price like '%2990%' or lf.sku_id_name like '%帅师%' or lf.sku_id_name like '%周帅%') and lf.ad_account_name like '%语文%' and  (lf.flow_original_order_activity_price like '%1980%' or lf.flow_original_order_activity_price like '%2980%' or lf.flow_original_order_activity_price like '%2990%') then 'B站信息流-陈瑞春'
when lf.channel_name_1 = '信息流' and lf.channel_name_2 = 'B站' and lf.third_department_name not like '%投放%' and (lf.flow_original_order_activity_price like '%2990%' or lf.sku_id_name like '%帅师%' or lf.sku_id_name like '%周帅%') and lf.ad_account_name not like '%语文%' then 'B站信息流-周帅'
when lf.channel_name_1 = '信息流' and lf.channel_name_2 = 'B站' and lf.third_department_name not like '%投放%' and lf.flow_order_price like '%1980%' and lf.ad_account_name like '%数学%' then 'B站信息流-周帅'
when lf.channel_name_1 = '短直电商' and lf.channel_name_2 = 'B站' and lf.third_department_name  like '%商务%' and   (lf.flow_pool_name like '%春春%' or lf.sku_id_name like '%陈瑞春%')  then 'B站信息流-陈瑞春'
when lf.channel_name_1 = '短直电商' and lf.channel_name_2 = 'B站' and lf.third_department_name  like '%商务%' and  (lf.flow_pool_name like '%朱博士%')  then 'B站信息流-朱汉祺'
--when lf.third_department_name = '线上商务部' and lf.channel_name_2 = 'B站' and lf.put_plan_name like '%春春%' then 'B站信息流-陈瑞春'
--when lf.third_department_name = '线上商务部' and lf.channel_name_2 = 'B站' and lf.put_plan_name like '%朱博士%' then 'B站信息流-朱汉祺'
when lf.channel_name_1 = '信息流' and lf.channel_name_2 = 'B站' and lf.third_department_name not like '%投放%' and lf.flow_original_order_activity_price not like '%2980%' and lf.flow_original_order_activity_price not like '%2990%' and lf.flow_original_order_activity_price not like '%1980%' then 'B站信息流'
when lf.flow_pool_name = '百度搜索引擎' or lf.channel_name_1='搜索营销' then '信息流搜索'
when lf.channel_name_1 = '信息流获客' and lf.channel_name_2 = '小红书' and lf.source_manager_name in ('王慧敏13','张琳02','王樱琦01') then '小红书投放'
when  lf.flow_pool_name like '%小红书班课%' then '小红书投放'
when lf.third_department_name = '投放部' and lf.get_customer_way_name = '短视频信息流' and lf.flow_original_order_activity_price like '%100%' then '信息流'
when lf.flow_pool_name = '中考加油' and lf.sku_id_name like '%孟帝%' then 'KOC-孟亚飞数学'
when lf.flow_pool_name = '中考加油' and lf.sku_id_name  like '%帅师%' then 'KOC-周帅数学'
when lf.flow_pool_name = '中考加油' and lf.sku_id_name  like '%肖晗%' then 'KOC-肖晗'
when  lf.source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07') and (lf.sku_id_name like '%孟帝%' or lf.sku_id_name like '%dudu%' or lf.sku_id_name like '%市场初二%' or lf.rule_name like '%亚飞%' or lf.sku_id_name like '%初二高阳%' or lf.sku_id_name like '%高阳初二%' or lf.sku_id_name like '%精品初二%' or lf.sku_id_name like '%菁英初三%' or (lf.virtual_second_department_name = '菁英班学部' and lf.lead_purchase_intention_level2_category_name='初级' and lf.lead_create_time>= '2026-04-15 00:00:00')) then 'KOC-孟亚飞数学'
when  lf.source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07') and (lf.sku_id_name like '%帅师%' or lf.rule_name like '%周帅%' or lf.sku_id_name like '%9月升高三%') then 'KOC-周帅数学'
when  lf.source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07') and (lf.sku_id_name like '%肖晗%' or lf.rule_name like '%肖晗%') then 'KOC-肖晗'
when  lf.source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07') and lf.lf_period_name not like '%多学科拓展%' and (lf.flow_original_order_activity_price like '%1100%' or lf.flow_original_order_activity_price like '%500%' or lf.flow_orders_income_amount like '%500%') and (lf.sku_id_name like '%朱汉祺%' or lf.sku_id_name like '%朱博士%' or lf.rule_name like '%朱汉祺5元%' or lf.sku_id_name like '%koc5元-朱博士%' or lf.rule_name like '%朱汉祺%') then 'KOC-5元朱汉祺'
when  lf.source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07') and (lf.sku_id_name like '%朱汉祺%' or lf.sku_id_name like '%29元%' or lf.sku_id_name like '%朱博士%' or lf.rule_name like '%朱汉祺%' or lf.rule_name like '%朱博士%' ) and (lf.flow_original_order_activity_price not like '%1100%' or lf.rule_name like '%29%') and lf.sku_id_name not like '%周帅%' then 'KOC-5元朱汉祺'
when  lf.source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07') and lf.lf_period_name not like '%多学科拓展%' and lf.sku_id_name not like '%朱汉祺%' and lf.sku_id_name not like '%朱博士%' and lf.sku_id_name not like '%周帅%' and lf.sku_id_name not like '%29元%' then 'KOC-5元纯课'
when  lf.source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07') and lf.sku_id_name like '%周帅%' then 'KOC-周帅'
--when (lf.channel_name_2 like '%KOL%' and lf.source_manager_name in ('崔文轩','孙培尧')) or (lf.channel_name_2 like '%抖音%' and lf.source_manager_name in ('徐绮鹤')) and lf.lf_period_name not like '%多学科拓展%' then '自孵化KOC'
when lf.third_department_name in ('品牌效能部','KOC孵化部') and lf.channel_name_2 in ('抖音','视频号','快手','KOL')  then '自孵化KOC-5元纯课'
when lf.third_department_name in ('品牌效能部','KOC孵化部') and lf.channel_name_2 in ('抖音','视频号','快手','KOL') and (lf.sku_id_name like '%5元%'or lf.sku_id_name like '%11元%' or lf.flow_original_order_activity_price like '%1100%' or lf.flow_original_order_activity_price like '%500%' or lf.flow_orders_income_amount  like '%1100%' or lf.flow_orders_income_amount  like '%500%' ) then '自孵化KOC-5元纯课'
when lf.source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') and lf.channel_name_2 like '%社群%' then '进校社群'
when lf.source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') and lf.channel_name_2 like '%直推%' then '进校直推'
when lf.source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') and lf.channel_name_2 like '%TMK%' and lf.page_id_name like '%1元%' then '进校TMK1元'
when lf.source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') and lf.channel_name_2 like '%TMK%' and lf.page_id_name like '%9元%' then '进校TMK9元'
when lf.source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') and lf.channel_name_2 like '%书商%' then '进校书商'
when lf.source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') and lf.channel_name_2 like '%综合%' and lf.put_plan_name like '%18%' then '进校直播'
when lf.source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') and lf.channel_name_2 like '%直播%' then '进校直播'
when lf.source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04') and lf.put_plan_name not like '%0元%' and lf.flow_pool_name not like '%家校共育%' and lf.flow_pool_name not like '%保持热爱%' and lf.flow_pool_name not like '%青松%' and lf.flow_pool_name not like '%原子初三%' and lf.flow_pool_name not like '%南通欣创%' and lf.flow_pool_name not like '%悟之道%' and lf.flow_pool_name not like '%济南梦航%' and lf.channel_name_3 <> '社群' and lf.put_plan_name not like '%善悟%' and lf.put_plan_name not like '%人人通%'  and lf.put_plan_name not like '%%济南格乐' and lf.flow_pool_name not like '%晨硕智学%' and lf.flow_pool_name not like '%兴尧文化%'  and lf.flow_pool_name not like '%济南映像%' and lf.flow_pool_name not like '%山东简单%' and lf.flow_pool_name not like '%争鸣科技%'  then '商务低价'
when lf.flow_pool_name like '%原子初三%' or lf.flow_pool_name like '%原子系统%'  then '原子'
when lf.flow_pool_name like '%市场部-公转私%' then '市场私域公导私'
when lf.flow_pool_name like '%南通欣创%' or  lf.flow_pool_name like '%人人通科技%' or lf.flow_pool_name like '%易而购%' or lf.flow_pool_name like '%济南梦航%' or lf.flow_pool_name like '%晨硕智学%' or lf.flow_pool_name like '%兴尧文化%' or lf.flow_pool_name like '%济南映像%' or lf.flow_pool_name like '%山东简单%' or lf.flow_pool_name like '%争鸣科技%'  then '进校私域合作'
when (lf.flow_pool_name like '%家校共育%' or lf.flow_pool_name like '%保持热爱%' or lf.flow_pool_name like '%青松%' or lf.flow_pool_name like '%悟之道%') and lf.put_plan_name not like '%0元%'  then '进校私域合作'
when lf.source_manager_name = '李宁24' and lf.put_plan_name like '%0转低%' then '进校私域合作'
when lf.third_department_name = '私域运营部' and  lf.flow_original_order_activity_price in ('100.0','900.0','300.0')  then '进校私域合作'
when lf.third_department_name = '私域运营部' and  lf.flow_original_order_activity_price in ('0.0') and lf.source_manager_name in ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研') then '进校私域合作'
when lf.third_department_name = '私域运营部' and lf.channel_name_1='市场私域' and lf.put_plan_name not like '%公导私%' and lf.put_plan_name not like '%公转私%' and lf.flow_original_order_activity_price = '0.0' and lf.rule_name not like '%激活%' and lf.rule_name not like '%咨询%' and lf.rule_name not like '%训练营%'  and lf.virtual_fifth_department_name not like '%罗江博%' and lf.virtual_fifth_department_name not like '%郑州学习顾问二部%' and lf.source_manager_name not in ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研') then '市场私域低价单'
when lf.source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and lf.channel_provider_name like '%格乐教育%' and lf.channel_name_2 like '%直播%' then '创新社群'
when lf.source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and lf.channel_name_2 like '%社群%' then '创新社群'
when lf.source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and (lf.channel_name_2 like '%直推%' or lf.put_plan_name like '%直推%') then '创新直推'
when lf.source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and (lf.channel_name_2 like '%书商%' or lf.put_plan_name like '%书商%' or lf.page_id_name like '%书商%') then '创新书商'
when lf.source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and lf.channel_name_2 like '%TMK%' and lf.page_id_name like '%1元%' then '创新TMK1元'
when lf.source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and lf.channel_name_2 like '%TMK%' and lf.page_id_name like '%9元%' then '创新TMK9元'
when lf.source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and (lf.channel_name_2 like '%直播%' or lf.page_id_name like '%进校%') then '创新直播'
when lf.source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and lf.channel_name_2<>'公众号' and lf.channel_name_1 = '商务' and lf.flow_pool_name <> '高途云集图书专营店-自然流' and lf.flow_pool_name <> '高途旗舰店—线索—yuxinru' and lf.put_plan_name not like '%社群%' and lf.put_plan_name not like '%小红书班课%' and lf.put_plan_name not like '%外部图书供量%' and lf.channel_second_provider_name not like '%沃德丰店铺线索赠课%' and lf.channel_second_provider_name not like '%智慧城-图书%' and lf.put_plan_name not like '%育甲%' and lf.flow_pool_name not like '%周长磊%'  then '创新商务'
when lf.flow_pool_name like '%周长磊%' then '创新APP'
when lf.source_manager_name in ('王春宵') then '武汉图书直播间'
when lf.source_manager_name in ('高曼曼01','杨思怡','宋向函') then '图书KOC达人'
when lf.flow_pool_name like '%市场部-原子合作%' then '原子'
when lf.flow_pool_name like '%市场部-微信私域%' or lf.flow_pool_name like '%市场部-规划报告%' or lf.flow_pool_name like '%规划报告%' or lf.flow_pool_name like '%市场部-小红书%' or lf.flow_pool_name like '%孟浩宇%' then '市场私域低价单'
when lf.flow_pool_name like '%待支付%' then '市场私域待支付'
when lf.flow_pool_name like '%未加好友%' then '市场私域未加好友'
when lf.flow_pool_name like '%内部换量%' then '市场私域首期掉海'
when lf.flow_pool_name like '公导私' then '进校私域合作'
when (lf.flow_pool_name like '%增长组%' or lf.channel_name_3 = '公众号' or lf.second_department_name = '微信生态部') and lf.channel_name_2 <> 'APP' then '集团私域'
when lf.put_plan_name  like '%济南格乐%' and lf.put_plan_name  like '%表单%'  then '商务0元'
when lf.put_plan_name like '%B类%' or lf.put_plan_name like '%b类%' or lf.channel_second_provider_name like '%KOC当期%' then 'KOC分层测试'
when lf.put_plan_name like '%星耀%' or lf.put_plan_name like '%物理展博%' or  lf.put_plan_name like '%物理谢丽荣%' or lf.put_plan_name like '%牟恩伯%' or  lf.put_plan_name like '%王赞%' or lf.put_plan_name like '%张磊老师高中数学%' or lf.put_plan_name like '%雯姐高中物理大讲堂%' then '百度星耀'
when lf.source_manager_name = '刘福云' and (lf.sku_id_name like '%瑞春%' or lf.sku_id_name like '%春春%') then '陈瑞春'
when lf.source_manager_name = '刘福云' and lf.sku_id_name like '%周帅%' then '周帅'
when lf.third_department_name = '直播部' and lf.sku_id_name like '%周帅%' and lf.channel_name_2 in ('百度','B站')  then '周帅'
when lf.third_department_name = '直播部' and lf.sku_id_name like '%孟亚飞%' and lf.rule_name like '%99%' then '孟亚飞99-1组'
when lf.third_department_name = '直播部' and lf.sku_id_name like '%孟亚飞%' then '孟亚飞9元'
when lf.third_department_name = '直播部' and lf.sku_id_name like '%朱汉祺%' then '朱博士29'
when lf.third_department_name = '直播部' and lf.sku_id_name like '%肖晗%' then '肖晗'
when lf.flow_pool_name like '%0转低转正%' or lf.channel_name_2='产研测试' then '进校私域合作'
when lf.flow_pool_name like '%天津智慧双子%'	then '创新社群'
when lf.third_department_name like '%城市定制%' then '点睛卷'	
when lf.lf_period_name like '%多学科拓展%' and lf.third_department_name like '%私域运营%' then '市场私域入群'
when lf.put_plan_name like '%赠课失败%' and lf.third_department_name = '线上商务部' then 'KOC赠课失败'
when lf.flow_pool_name like '%自然流%' and lf.source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07') and lf.sku_id_name like '%周帅%' then 'KOC-周帅'	
when lf.flow_pool_name like '%自然流%' and lf.source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07') and lf.sku_id_name like '%肖晗%' then 'KOC-肖晗'	
when lf.flow_pool_name like '%自然流%' and lf.source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07') and lf.sku_id_name like '%朱汉祺%'  and lf.flow_original_order_activity_price like '%1100%' then 'KOC-5元朱汉祺'
when lf.flow_pool_name like '%自然流%' and lf.source_manager_name in ('赵语诗','崔文轩','孙培尧')	then '自孵化KOC-5元纯课'
when lf.flow_pool_name like '%自然流%' and (lf.sku_id_name like '%朱博士%' or lf.sku_id_name like '%朱汉祺%') and lf.rule_name like '%9%' and lf.rule_name not like '%29%' and lf.third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '朱博士9元'
when lf.flow_pool_name like '%自然流%' and lf.sku_id_name like '%朱博士%' and lf.third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '朱博士29'
when lf.flow_pool_name like '%自然流%' and lf.sku_id_name like '%亚飞%' and lf.rule_name like '%99%' and lf.third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '孟亚飞99-1组'	
when lf.flow_pool_name like '%自然流%' and lf.sku_id_name like '%亚飞%' and lf.third_department_name  in ('直播部','新媒体内容运营部','市场一组')  then '孟亚飞9元'	
when lf.flow_pool_name like '%自然流%' and lf.sku_id_name like '%曹忆%' then '曹忆'	
when lf.flow_pool_name like '%自然流%' and lf.rule_name like '%朱博士%' and lf.third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '朱博士29'
when lf.flow_pool_name like '%自然流%' and lf.source_manager_name like '%邵万昕%' and lf.third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '朱博士29'
when lf.flow_pool_name like '%自然流%' and lf.rule_name like '%亚飞%' and lf.rule_name like '%99%' then '孟亚飞99-1组'	
when lf.flow_pool_name like '%自然流%' and lf.rule_name like '%亚飞%'  then '孟亚飞9元'	
when lf.flow_pool_name like '%自然流%' and lf.rule_name like '%郭艺%'  then '郭艺'
when lf.flow_pool_name like '%自然流%' and lf.rule_name like '%汤雪%'  then '汤老师'	
when lf.flow_pool_name like '%自然流%' and lf.rule_name like '%曹忆%' then '曹忆'		
when lf.flow_pool_name like '%途途教室%' or lf.first_department_name like 'TUTU' then '途途APP'
when lf.second_department_name = '市场四部' then '市场四部'
when lf.source_manager_name in ('宋莹莹','辛世如') and lf.channel_name_2 in ('视频号') then '信息流-虚拟号挂车'
when lf.rule_name like '%训练营%' and lf.rule_name like '%市场私域%' then '市场私域入群'
when lf.flow_pool_name like '%青少-私域%' then '青少私域'
when lf.put_plan_name like '%AI名师%' then 'AI直播'
when lf.channel_name_1= '信息流' and (lf.put_plan_name like '%抖音私信%' or lf.put_plan_name like '%初三0元%' or lf.put_plan_name like '%高中0元%') then '信息流-抖音私信'
when lf.rule_name like '%途途私域%' or (lf.rule_name like '%私域%' and lf.first_department_name = 'TT') then '途途私域'
else '其他未知流量' end as channel_1,
        case
            when lf.rule_name like '%高一%' then '高一'
            when lf.rule_name like '%高二%' then '高二'
            when lf.rule_name like '%高三%' then '高三'
            when lf.rule_name like '%初二%' then '初二'
            when lf.rule_name like '%初三%' then '初三'
            when lf.rule_name like '%初一%' then '初一'
            else lf.metric_grade_1
        end as grade_1
    from lead_info lf
)
,zx_active as (
    select
        employee_email_name,
        xiaozu,
        jingli
    from (
        select
            zx.*,
            row_number() over (
                partition by zx.employee_email_name
                order by
                    case
                        when zx.department = '郑州顾问部' then 1
                        when zx.department = '西安一部' then 2
                        when zx.department = '西安二部' then 3
                        else 9
                    end,
                    zx.employee_email_prefix,
                    zx.xiaozu,
                    zx.jingli
            ) as rn
        from temp_table.dingxi01_jiagou_zx zx
        where cast(zx.zaizhi as varchar) = '1'
          and zx.department in ('郑州顾问部', '西安一部', '西安二部')
    ) t
    where rn = 1
)
,jiagou_period as (
    select
        qici,
        department,
        employee_email_name,
        xiaozu,
        jingli
    from (
        select
            nullif(trim(cast(jg.qici as varchar)), '') as qici,
            nullif(trim(cast(jg.department as varchar)), '') as department,
            nullif(trim(cast(jg.employee_email_name as varchar)), '') as employee_email_name,
            nullif(trim(cast(jg.xiaozu as varchar)), '') as xiaozu,
            nullif(trim(cast(jg.jingli as varchar)), '') as jingli,
            row_number() over (
                partition by
                    nullif(trim(cast(jg.qici as varchar)), ''),
                    nullif(trim(cast(jg.department as varchar)), ''),
                    nullif(trim(cast(jg.employee_email_name as varchar)), '')
                order by
                    case when nullif(trim(cast(jg.xiaozu as varchar)), '') is not null then 0 else 1 end,
                    nullif(trim(cast(jg.xiaozu as varchar)), ''),
                    nullif(trim(cast(jg.jingli as varchar)), '')
            ) as rn
        from temp_table.dingxi01_jiagou_db jg
    ) t
    where rn = 1
)
,lead_metric_distinct as (
    select distinct
        lead_id,
        lf_period_name,
        channel_1,
        virtual_fourth_department_name,
        metric_jingli,
        metric_zhuguan,
        grade_1,
        metric_name,
        valid_lead_count,
        income_amount,
        in_pay_period_refund_amount,
        non_pay_period_refund_amount,
        same_lead_period_refund_amount
    from lead_metric_mapped
)


,metric_agg as (
    select
        m.period_name as qici,
        m.channel_map as channel_1,
        m.jingli,
        m.xiaozu,
        m.grade_1 as grade_list,
        m.employee_email_name as name,
        sum(m.can_renew_ds_count_a) as can_renew_ds_count_a,
        sum(m.trade_profit) as metric_gmv_total,
        sum(m.trade_refund) as metric_refund_total,
        sum(m.xb_trade_income - m.xb_trade_profit) as metric_refund_7
    from (
with m2253_data as
(select distinct
case
    when cast(date_parse(replace(concat(group_period_year, group_period_term), '期', ''), '%Y%m%d') as date) between date '2026-07-14' and date '2026-07-19' then '20260716期'
    else concat(cast(date_format(date_trunc('week', date_parse(replace(concat(group_period_year, group_period_term), '期', ''), '%Y%m%d') - interval '1' day) + interval '4' day, '%Y%m%d') as varchar), '期')
end period_name,
 virtual_third_department_name  depart_1,
virtual_fourth_department_name  depart,
    virtual_leader_email_name  jingli,
    virtual_direct_leader_email_name  zhuguan,
    employee_email_name,
    rule_name,
    t1.lead_id,
    user_id,
case 
when (assign_lead_count = 1 or valid_lead_count = 1) and third_department_name  in ('直播部','新媒体内容运营部','市场一组') THEN '当期'
when (assign_lead_count = 1 or valid_lead_count = 1) and third_department_name  in ('图书营销部') and rule_name like '%亚飞%' THEN '当期'
when third_department_name is null and valid_lead_count = 1 then '当期'
when source_manager_name in ('韩正卿') and merge_valid_lead_count = 1 and channel_name_1='市场私域' then '当期'
when third_department_name  not in ('直播部','新媒体内容运营部','市场一组') and valid_lead_count = 1 then '当期'
 else '非当期' end as d_w,
case when (assign_lead_count = 1 or valid_lead_count = 1) and third_department_name  in ('直播部','新媒体内容运营部','市场一组') THEN 1
when third_department_name is null and valid_lead_count = 1 then 1
when third_department_name  not in ('直播部','新媒体内容运营部','市场一组') and valid_lead_count = 1 then 1
when third_department_name  in ('图书营销部') and rule_name like '%亚飞%' and (assign_lead_count = 1 or valid_lead_count = 1)  then 1
 else 0 end as xiansuo,
case when flow_pool_name in ('高途学习规划','智辉老师讲规划') then '市场私域视频号'
when rule_name like '%语数英%' and third_department_name = '新媒体内容运营部' then '语数英'
when flow_pool_name like '%星义大大%' or flow_pool_name like '%星义物理%' then '赵星义'
when rule_name like '%途途私域%' or (rule_name like '%私域%' and first_department_name = 'TT' and rule_name not like '%集团%') then '途途私域'
when third_department_name='图书营销部' and (sku_id_name like '%孟亚飞99%' or sku_id_name like '%亚飞%') and channel_name_2 = '百度' then '孟亚飞-2组-百度'
when third_department_name='图书营销部' and (sku_id_name like '%孟亚飞99%' or sku_id_name like '%亚飞%') and channel_name_2 = '抖音' then '孟亚飞-2组-抖音'
when third_department_name = '投放部' and (ad_account_name like '%周帅%' or put_plan_name like '%周帅%') then '信息流-周帅'
when source_manager_name in ('韩正卿') then '抖音私信'
when third_department_name = '私域运营部' and source_manager_name in ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研','岳一帆02','田起帆','王绍阳') then '进校私域合作'
when channel_name_1='市场私域' and (virtual_fourth_department_name in ('郑州学习顾问二部','郑州学习顾问七部','郑州训练营') or virtual_fifth_department_name in ('罗江博团队')) then '市场私域入群'
when third_department_name = '图书营销部' and (rule_name like '%点睛卷%' or sku_id_name like '%押题卷%')  then '押题卷'
when put_plan_name like '%迪九学%' then '市场私域代运营'
when third_department_name = '投放部' and channel_name_2 = '小红书' and channel_name_1 <> '搜索营销' then '信息流-小红书'
when third_department_name = '线上商务部' and channel_name_2 = '小红书' then '小红书'
when (flow_pool_name like '%肖晗%' or sku_id_name like '%肖晗%' or put_plan_name like '%肖晗9元%') and third_department_name='直播部'  then '肖晗'
when (flow_pool_name like '%北大汤哥%' or flow_pool_name like '%海淀名师高阶%' or flow_pool_name like '%海淀高阶%') and sku_id_name like '%小艺%'  then '郭艺'
when  third_department_name like '%私域%' and rule_name like '%私域%' and rule_name like '%图书%' then '市场私域图书'
when  third_department_name like '%私域%' and rule_name like '%品效%'  then '市场私域品效'
when  third_department_name like '%私域%' and rule_name like '%公域学霸%'  then '市场私域公域组'
when  third_department_name like '%私域%' and rule_name like '%IE%'  then '市场私域IE'
when  third_department_name like '%私域%' and rule_name like '%裂变%'  then '市场私域裂变'
when third_department_name in ('直播部','新媒体内容运营部','市场一组','私域运营部') and put_plan_name like '%退%' and flow_pool_name ='电商退款用户池'  then '退款订单复用'
when third_department_name in ('直播部','新媒体内容运营部','市场一组','私域运营部') and put_plan_name like '%失败%' and flow_pool_name ='电商退款用户池'  then '赠课失败'
when third_department_name in ('直播部','新媒体内容运营部','市场一组')  and (flow_pool_name ='初阶化学规划' or flow_pool_name like '%启迪-初阶老师%')  then '曹忆'
when (third_department_name = '图书营销部' and sku_id_name like '%真题%') or (third_department_name='直播部' and sku_id_name like '%真题%') then '西安图书直播间-直播'
when (third_department_name = '图书营销部' and sku_id_name not like '%真题%') or (third_department_name='直播部' and sku_id_name  like '%秒懂%') or (third_department_name='直播部' and sku_id_name  like '%图书赠送%') then '西安图书直播间-挂链'
when third_department_name in ('直播部','新媒体内容运营部','市场一组') and (flow_pool_name like '%海淀高阶名师%' or flow_pool_name like '%海淀老师高阶%' or flow_pool_name like '%小艺%') then '郭艺'
when put_plan_name like '%国培教育-0元%' or put_plan_name like '%易喆教育-0元%' or put_plan_name like '%钟情-0元%' or put_plan_name like '%中望达-0元%' or put_plan_name like '%晨硕-0元%' or put_plan_name like '%彩石-0元入群%'  then '创新商务入群'
when put_plan_name like '%0元入群-进校%' and third_department_name = '线上商务部' then '创新商务入群'
when third_department_name='KOC孵化部' and flow_pool_name like '%电商退款%' and put_plan_name like '%失败%' then '自孵化KOC-赠课失败'
when third_department_name='KOC孵化部' and flow_pool_name like '%电商退款%' and put_plan_name like '%退%' then '自孵化KOC-退款订单复用'
when source_manager_name = '方俊结01' and put_plan_name like '%赠课后退款%' then 'KOC-赠课后退款' 
when third_department_name = '直播部' and (sku_id_name like '%春春%' or sku_id_name like '%瑞春%' or rule_name like '%春春%' or rule_name like '%瑞春%') then '陈瑞春'
when third_department_name = '直播部' and (sku_id_name like '%朱博士99%' or rule_name like '%朱汉祺99%') then '朱博士99'
when (third_department_name = '直播部' and (sku_id_name like '%朱博士%' or sku_id_name like '%朱汉祺%') and rule_name like '%9%' and rule_name not like '%29%' and sku_id_name not like '%急%' and sku_id_name not like '%礼盒29%') or (third_department_name = '直播部' and sku_id_name like '%朱博士9%') then '朱博士9元'
when ad_account_name like '%春春%' and channel_name_1 = '信息流' then '信息流-陈瑞春'
when channel_name_1 = '信息流' and channel_name_2='B站' and (page_id_name like '%0元物化%') then 'B站信息流-曹忆'
when third_department_name = '直播部' and channel_name_1 = '信息流' and channel_name_2 = 'B站'  then 'B站信息流-亚飞(1元)'
when channel_name_1 = '信息流' and channel_name_2='B站' and (page_id_name like '%亚飞%' or source_put_plan_name like '%亚飞%'  or rule_name like '%亚飞%' or page_id_name like '%初中-0元%') then 'B站信息流-亚飞'
when channel_name_1 = '信息流' and (page_id_name like '%亚飞%' or ad_account_name like '%亚飞%') then '信息流-亚飞'
when (flow_pool_name like '%朱博士%' or flow_pool_name like '%双博士%' or flow_pool_name like '%教育规划%') and third_department_name <> '线上商务部' and period_name not like '%多学科拓展%' and rule_name not like '%张杰%' and sku_id_name not like '%马凯鹏IP%' and third_department_name='直播部' then '朱博士29'
when put_plan_name like '%朱博士说教育%' and period_name not like '%多学科拓展%' and flow_pool_name not like '%高分讲堂%' and  flow_pool_name not like '%总裁%' and third_department_name='直播部' then '朱博士29'
when flow_pool_name like '%朱博士讲英语%' and sku_id_name like '%马凯鹏IP%' and third_department_name='直播部' then '马凯鹏29'
when (flow_pool_name like '%朱博士讲英语%' or flow_pool_name like '%朱博士英语%' or flow_pool_name like '%朱汉祺说英语%' or flow_pool_name like '%朱博士说英语%' or flow_pool_name like '%教育规划%' or flow_pool_name like '%双博士英语规划%' or flow_pool_name like '%朱博士满分英语%' or flow_pool_name like '%英语教父朱博士%' or (flow_pool_name like '%中考决胜天团%' and lead_purchase_intention_level1_category_name = '规划系统')) and third_department_name = '直播部' and period_name not like '%多学科拓展%' and sku_id_name not like '%马凯鹏IP%' and third_department_name='直播部' then '朱博士29'
when (flow_pool_name like '%汤哥%' or flow_pool_name like '%汤老师%') and period_name not like '%多学科拓展%' and third_department_name in ('直播部','新媒体内容运营部')  then '汤老师'
when (flow_pool_name like '%中考百日冲刺%') and period_name not like '%多学科拓展%' and third_department_name='直播部'  then '曹忆9.9纯课'	
when source_manager_name = '陈晓菁04' and channel_provider_name not like '%开拓%' and put_plan_name not like '%九学%' then '商务低价'	
when (flow_pool_name like '%孟帝%' or flow_pool_name like '%孟老师%' or flow_pool_name like '%中考数学冲刺%' or flow_pool_name like '%8升9数学%' or flow_pool_name like '%孟亚飞讲数学%' or flow_pool_name like '%中考冲刺%' or flow_pool_name like '%中考满分冲刺%' or flow_pool_name like '%押题王孟亚飞%' or flow_pool_name like '%中考数学大通关%' or flow_pool_name like '%中考数学规划%' or flow_pool_name like '%亚飞数学%' or flow_pool_name like '%孟帝数学%' or flow_pool_name like '%亚飞秒解思维%')  and period_name not like '%多学科拓展%' and channel_name_2 not like '%KOL%' and third_department_name='直播部' and channel_name_2 = '抖音'  then '孟亚飞-1组-抖音'
when (flow_pool_name like '%孟帝%' or flow_pool_name like '%孟老师%' or flow_pool_name like '%中考数学冲刺%' or flow_pool_name like '%8升9数学%' or flow_pool_name like '%孟亚飞讲数学%' or flow_pool_name like '%中考冲刺%' or flow_pool_name like '%中考满分冲刺%' or flow_pool_name like '%押题王孟亚飞%' or flow_pool_name like '%中考数学大通关%' or flow_pool_name like '%中考数学规划%' or flow_pool_name like '%亚飞数学%' or flow_pool_name like '%孟帝数学%')  and period_name not like '%多学科拓展%' and channel_name_2 not like '%KOL%' and third_department_name='直播部' and channel_name_2 = '视频号'  then '孟亚飞9元'
when (flow_pool_name like '%孟帝%' or flow_pool_name like '%孟老师%' or flow_pool_name like '%中考数学冲刺%' or flow_pool_name like '%8升9数学%' or flow_pool_name like '%孟亚飞讲数学%' or flow_pool_name like '%中考冲刺%' or flow_pool_name like '%中考满分冲刺%' or flow_pool_name like '%押题王孟亚飞%' or flow_pool_name like '%中考数学大通关%' or flow_pool_name like '%中考数学规划%' or flow_pool_name like '%亚飞数学%' or flow_pool_name like '%孟帝数学%')  and period_name not like '%多学科拓展%' and channel_name_2 not like '%KOL%' and third_department_name='直播部' and channel_name_2 = 'B站'  then '孟亚飞-1组-B站'
when (flow_pool_name like '%孟帝%' or flow_pool_name like '%孟老师%' or flow_pool_name like '%中考数学冲刺%' or flow_pool_name like '%8升9数学%' or flow_pool_name like '%孟亚飞讲数学%' or flow_pool_name like '%中考冲刺%' or flow_pool_name like '%中考满分冲刺%' or flow_pool_name like '%押题王孟亚飞%' or flow_pool_name like '%中考数学大通关%' or flow_pool_name like '%中考数学规划%' or flow_pool_name like '%亚飞数学%' or flow_pool_name like '%孟帝数学%')  and period_name not like '%多学科拓展%' and channel_name_2 not like '%KOL%' and third_department_name='直播部' and channel_name_2 not like '%百度%'  then '孟亚飞99-1组'
when (flow_pool_name like '%孟帝%' or flow_pool_name like '%孟老师%' or flow_pool_name like '%中考数学冲刺%' or flow_pool_name like '%8升9数学%' or flow_pool_name like '%孟亚飞讲数学%' or flow_pool_name like '%中考冲刺%' or flow_pool_name like '%中考满分冲刺%' or flow_pool_name like '%押题王孟亚飞%' or flow_pool_name like '%中考数学大通关%' or flow_pool_name like '%中考数学规划%' or flow_pool_name like '%亚飞数学%')  and period_name not like '%多学科拓展%' and channel_name_2 not like '%KOL%' and third_department_name='直播部' and channel_name_2 = '百度'  then '孟亚飞-1组-百度'
when (flow_pool_name like '%孟帝%' or flow_pool_name like '%孟老师%' or flow_pool_name like '%中考数学冲刺%' or flow_pool_name like '%8升9数学%' or flow_pool_name like '%孟亚飞讲数学%' or flow_pool_name like '%中考冲刺%' or flow_pool_name like '%中考满分冲刺%' or flow_pool_name like '%押题王孟亚飞%' or flow_pool_name like '%中考数学大通关%' or flow_pool_name like '%中考数学规划%' or flow_pool_name like '%亚飞数学%')  and period_name not like '%多学科拓展%' and channel_name_2 not like '%KOL%' and third_department_name='直播部'  then '孟亚飞9元'
when put_plan_name like '%刘家晋讲图文%' or put_plan_name like '%孟帝数学%' and third_department_name='直播部' and rule_name like '%99%'  then '孟亚飞99-1组'	
when put_plan_name like '%刘家晋讲图文%' or put_plan_name like '%孟帝数学%' and third_department_name='直播部' then '孟亚飞9元'	
when (flow_pool_name like '%肖晗%' or sku_id_name like '%肖晗%') and third_department_name='直播部'  then '肖晗'
when flow_pool_name like '%峥峥%' and period_name not like '%多学科拓展%' and third_department_name='直播部'  then '何峥峥'
when flow_pool_name like '%汐子%' and period_name not like '%多学科拓展%' and sku_id_name not like '%亚飞%' and third_department_name='直播部'  then '王汐子'
when flow_pool_name like '%汐子%' and period_name not like '%多学科拓展%' and sku_id_name  like '%亚飞%' and third_department_name='直播部' and rule_name like '%99%'  then '孟亚飞99-1组'
when flow_pool_name like '%汐子%' and period_name not like '%多学科拓展%' and sku_id_name  like '%亚飞%' and third_department_name='直播部' then '孟亚飞9元'
when (flow_pool_name like '%曹忆%' or flow_pool_name like '%dudu%' or flow_pool_name like '%中考决胜天团%' or flow_pool_name like '%具象思维%' or flow_pool_name like '%在逃发面馒头%' or flow_pool_name like '%库洛米%' and lead_purchase_intention_level1_category_name <> '规划系统') and period_name not like '%多学科拓展%' and third_department_name in ('直播部','新媒体内容运营部') then '曹忆'
when first_department_name ='市场部' and channel_name_1 <> '站内获客' and channel_name_2 <> 'APP' then '集团私域'
when put_plan_name like '%未加好友%' then '市场私域未加好友'
when put_plan_name like '%私域-信息流%' then '市场私域待支付'
when third_department_name = '私域运营部' and rule_name not like '%训练营%' and virtual_fifth_department_name not in ('罗江博团队') and rule_name not like '%复用%' and rule_name not like '%未加好友%' and channel_name_2 <> '内部换量' then '市场私域低价单'
when third_department_name = '私域运营部' and rule_name not like '%训练营%'  and rule_name not like '%复用%' and rule_name not like '%未加好友%' and channel_name_2 <> '内部换量' and flow_original_order_activity_price = '0.0' then '市场私域低价单'
when channel_name_2 in ('APP','M站','PC') and flow_pool_name not like '%途途%' then 'APP'
when channel_provider_name like '%唐山TMK%' then '唐山TMK' 
when source_manager_name in ('高文羽') and channel_provider_name not like '%唐山TMK%' and channel_provider_name not like '%郑州%' then '人工外呼' 
when source_manager_name = '冯银晨' and channel_name_2 = '小红书' then '信息流-小红书'	
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and page_id_name like '%汤雪%'  then 'B站信息流-汤学健'
when (channel_name_1 = '信息流' and channel_name_2 <> 'B站' and third_department_name NOT LIKE '%商务%' and put_plan_name not like '%初三0元%' and put_plan_name not like '%抖音私信%' and put_plan_name not like '%高中0元%' and flow_original_order_activity_price not like '%1990%') or (channel_name_2 = 'B站' and third_department_name like '%投放%') then '信息流'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and (page_id_name like '%郭艺%') then 'B站信息流-郭艺'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and (page_id_name like '%朱博士%') then 'B站信息流-朱汉祺'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and page_id_name like '%肖晗%' then 'B站信息流-肖晗'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and (page_id_name like '%马凯鹏%' or ad_account_name like '%化学%') then 'B站信息流-马凯鹏'
when channel_name_1 = '信息流'  and channel_name_2 = 'B站' and third_department_name not like '%投放%' and  (sku_id_name like '%陈瑞春%' or rule_name like '%陈瑞春%') and (ad_account_name  like '%语文%' or source_put_plan_name like '%自然流%' or page_id_name like '%春春%') then 'B站信息流-陈瑞春'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and (flow_original_order_activity_price like '%2990%' or sku_id_name like '%帅师%' or sku_id_name like '%周帅%') and ad_account_name like '%语文%' and  (flow_original_order_activity_price like '%1980%' or flow_original_order_activity_price like '%2980%' or flow_original_order_activity_price like '%2990%') then 'B站信息流-陈瑞春'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and (flow_original_order_activity_price like '%2990%' or sku_id_name like '%帅师%' or sku_id_name like '%周帅%') and ad_account_name not like '%语文%' then 'B站信息流-周帅'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and flow_order_price like '%1980%' and ad_account_name like '%数学%' then 'B站信息流-周帅'
when channel_name_1 = '短直电商' and channel_name_2 = 'B站' and third_department_name  like '%商务%' and   (flow_pool_name like '%春春%' or sku_id_name like '%陈瑞春%')  then 'B站信息流-陈瑞春'
when channel_name_1 = '短直电商' and channel_name_2 = 'B站' and third_department_name  like '%商务%' and  (flow_pool_name like '%朱博士%')  then 'B站信息流-朱汉祺'
--when third_department_name = '线上商务部' and channel_name_2 = 'B站' and put_plan_name like '%春春%' then 'B站信息流-陈瑞春'
--when third_department_name = '线上商务部' and channel_name_2 = 'B站' and put_plan_name like '%朱博士%' then 'B站信息流-朱汉祺'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and flow_original_order_activity_price not like '%2980%' and flow_original_order_activity_price not like '%2990%' and flow_original_order_activity_price not like '%1980%' then 'B站信息流'
when flow_pool_name = '百度搜索引擎' or channel_name_1='搜索营销' then '信息流搜索'
when channel_name_1 = '信息流获客' and channel_name_2 = '小红书' and source_manager_name in ('王慧敏13','张琳02','王樱琦01') then '小红书投放'
when  flow_pool_name like '%小红书班课%' then '小红书投放'
when third_department_name = '投放部' and get_customer_way_name = '短视频信息流' and flow_original_order_activity_price like '%100%' then '信息流'
when flow_pool_name = '中考加油' and sku_id_name like '%孟帝%' then 'KOC-孟亚飞数学'
when flow_pool_name = '中考加油' and sku_id_name  like '%帅师%' then 'KOC-周帅数学'
when flow_pool_name = '中考加油' and sku_id_name  like '%肖晗%' then 'KOC-肖晗'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07') and (sku_id_name like '%孟帝%' or sku_id_name like '%dudu%' or sku_id_name like '%市场初二%' or rule_name like '%亚飞%' or sku_id_name like '%初二高阳%' or sku_id_name like '%高阳初二%' or sku_id_name like '%精品初二%' or sku_id_name like '%菁英初三%' or (virtual_second_department_name = '菁英班学部' and lead_purchase_intention_level2_category_name='初级' and lead_create_time>= '2026-04-15 00:00:00')) then 'KOC-孟亚飞数学'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07') and (sku_id_name like '%帅师%' or rule_name like '%周帅%' or sku_id_name like '%9月升高三%') then 'KOC-周帅数学'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07') and (sku_id_name like '%肖晗%' or rule_name like '%肖晗%') then 'KOC-肖晗'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07') and period_name not like '%多学科拓展%' and (flow_original_order_activity_price like '%1100%' or flow_original_order_activity_price like '%500%' or flow_orders_income_amount like '%500%') and (sku_id_name like '%朱汉祺%' or sku_id_name like '%朱博士%' or rule_name like '%朱汉祺5元%' or sku_id_name like '%koc5元-朱博士%' or rule_name like '%朱汉祺%') then 'KOC-5元朱汉祺'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07') and (sku_id_name like '%朱汉祺%' or sku_id_name like '%29元%' or sku_id_name like '%朱博士%' or rule_name like '%朱汉祺%' or rule_name like '%朱博士%' ) and (flow_original_order_activity_price not like '%1100%' or rule_name like '%29%') and sku_id_name not like '%周帅%' then 'KOC-5元朱汉祺'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07') and period_name not like '%多学科拓展%' and sku_id_name not like '%朱汉祺%' and sku_id_name not like '%朱博士%' and sku_id_name not like '%周帅%' and sku_id_name not like '%29元%' then 'KOC-5元纯课'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07') and sku_id_name like '%周帅%' then 'KOC-周帅'
--when (channel_name_2 like '%KOL%' and source_manager_name in ('崔文轩','孙培尧')) or (channel_name_2 like '%抖音%' and source_manager_name in ('徐绮鹤')) and period_name not like '%多学科拓展%' then '自孵化KOC'
when third_department_name in ('品牌效能部','KOC孵化部') and channel_name_2 in ('抖音','视频号','快手','KOL')  then '自孵化KOC-5元纯课'
when third_department_name in ('品牌效能部','KOC孵化部') and channel_name_2 in ('抖音','视频号','快手','KOL') and (sku_id_name like '%5元%'or sku_id_name like '%11元%' or flow_original_order_activity_price like '%1100%' or flow_original_order_activity_price like '%500%' or flow_orders_income_amount  like '%1100%' or flow_orders_income_amount  like '%500%' ) then '自孵化KOC-5元纯课'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') and channel_name_2 like '%社群%' then '进校社群'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') and channel_name_2 like '%直推%' then '进校直推'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') and channel_name_2 like '%TMK%' and page_id_name like '%1元%' then '进校TMK1元'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') and channel_name_2 like '%TMK%' and page_id_name like '%9元%' then '进校TMK9元'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') and channel_name_2 like '%书商%' then '进校书商'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') and channel_name_2 like '%综合%' and put_plan_name like '%18%' then '进校直播'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04') and channel_name_2 like '%直播%' then '进校直播'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04') and put_plan_name not like '%0元%' and flow_pool_name not like '%家校共育%' and flow_pool_name not like '%保持热爱%' and flow_pool_name not like '%青松%' and flow_pool_name not like '%原子初三%' and flow_pool_name not like '%南通欣创%' and flow_pool_name not like '%悟之道%' and flow_pool_name not like '%济南梦航%' and channel_name_3 <> '社群' and put_plan_name not like '%善悟%' and put_plan_name not like '%人人通%'  and put_plan_name not like '%%济南格乐' and flow_pool_name not like '%晨硕智学%' and flow_pool_name not like '%兴尧文化%'  and flow_pool_name not like '%济南映像%' and flow_pool_name not like '%山东简单%' and flow_pool_name not like '%争鸣科技%'  then '商务低价'
when flow_pool_name like '%原子初三%' or flow_pool_name like '%原子系统%'  then '原子'
when flow_pool_name like '%市场部-公转私%' then '市场私域公导私'
when flow_pool_name like '%南通欣创%' or  flow_pool_name like '%人人通科技%' or flow_pool_name like '%易而购%' or flow_pool_name like '%济南梦航%' or flow_pool_name like '%晨硕智学%' or flow_pool_name like '%兴尧文化%' or flow_pool_name like '%济南映像%' or flow_pool_name like '%山东简单%' or flow_pool_name like '%争鸣科技%'  then '进校私域合作'
when (flow_pool_name like '%家校共育%' or flow_pool_name like '%保持热爱%' or flow_pool_name like '%青松%' or flow_pool_name like '%悟之道%') and put_plan_name not like '%0元%'  then '进校私域合作'
when source_manager_name = '李宁24' and put_plan_name like '%0转低%' then '进校私域合作'
when third_department_name = '私域运营部' and  flow_original_order_activity_price in ('100.0','900.0','300.0')  then '进校私域合作'
when third_department_name = '私域运营部' and  flow_original_order_activity_price in ('0.0') and source_manager_name in ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研') then '进校私域合作'
when third_department_name = '私域运营部' and channel_name_1='市场私域' and put_plan_name not like '%公导私%' and put_plan_name not like '%公转私%' and flow_original_order_activity_price = '0.0' and rule_name not like '%激活%' and rule_name not like '%咨询%' and rule_name not like '%训练营%'  and virtual_fifth_department_name not like '%罗江博%' and virtual_fifth_department_name not like '%郑州学习顾问二部%' and source_manager_name not in ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研') then '市场私域低价单'
when source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and channel_provider_name like '%格乐教育%' and channel_name_2 like '%直播%' then '创新社群'
when source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and channel_name_2 like '%社群%' then '创新社群'
when source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and (channel_name_2 like '%直推%' or put_plan_name like '%直推%') then '创新直推'
when source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and (channel_name_2 like '%书商%' or put_plan_name like '%书商%' or page_id_name like '%书商%') then '创新书商'
when source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and channel_name_2 like '%TMK%' and page_id_name like '%1元%' then '创新TMK1元'
when source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and channel_name_2 like '%TMK%' and page_id_name like '%9元%' then '创新TMK9元'
when source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and (channel_name_2 like '%直播%' or page_id_name like '%进校%') then '创新直播'
when source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and channel_name_2<>'公众号' and channel_name_1 = '商务' and flow_pool_name <> '高途云集图书专营店-自然流' and flow_pool_name <> '高途旗舰店—线索—yuxinru' and put_plan_name not like '%社群%' and put_plan_name not like '%小红书班课%' and put_plan_name not like '%外部图书供量%' and channel_second_provider_name not like '%沃德丰店铺线索赠课%' and channel_second_provider_name not like '%智慧城-图书%' and put_plan_name not like '%育甲%' and flow_pool_name not like '%周长磊%'  then '创新商务'
when flow_pool_name like '%周长磊%' then '创新APP'
when source_manager_name in ('王春宵') then '武汉图书直播间'
when source_manager_name in ('高曼曼01','杨思怡','宋向函') then '图书KOC达人'
when flow_pool_name like '%市场部-原子合作%' then '原子'
when flow_pool_name like '%市场部-微信私域%' or flow_pool_name like '%市场部-规划报告%' or flow_pool_name like '%规划报告%' or flow_pool_name like '%市场部-小红书%' or flow_pool_name like '%孟浩宇%' then '市场私域低价单'
when flow_pool_name like '%待支付%' then '市场私域待支付'
when flow_pool_name like '%未加好友%' then '市场私域未加好友'
when flow_pool_name like '%内部换量%' then '市场私域首期掉海'
when flow_pool_name like '公导私' then '进校私域合作'
when (flow_pool_name like '%增长组%' or channel_name_3 = '公众号' or second_department_name = '微信生态部') and channel_name_2 <> 'APP' then '集团私域'
when put_plan_name  like '%济南格乐%' and put_plan_name  like '%表单%'  then '商务0元'
when put_plan_name like '%B类%' or put_plan_name like '%b类%' or channel_second_provider_name like '%KOC当期%' then 'KOC分层测试'
when put_plan_name like '%星耀%' or put_plan_name like '%物理展博%' or  put_plan_name like '%物理谢丽荣%' or put_plan_name like '%牟恩伯%' or  put_plan_name like '%王赞%' or put_plan_name like '%张磊老师高中数学%' or put_plan_name like '%雯姐高中物理大讲堂%' then '百度星耀'
when source_manager_name = '刘福云' and (sku_id_name like '%瑞春%' or sku_id_name like '%春春%') then '陈瑞春'
when source_manager_name = '刘福云' and sku_id_name like '%周帅%' then '周帅'
when third_department_name = '直播部' and sku_id_name like '%周帅%' and channel_name_2 in ('百度','B站')  then '周帅'
when third_department_name = '直播部' and sku_id_name like '%孟亚飞%' and rule_name like '%99%' then '孟亚飞99-1组'
when third_department_name = '直播部' and sku_id_name like '%孟亚飞%' then '孟亚飞9元'
when third_department_name = '直播部' and sku_id_name like '%朱汉祺%' then '朱博士29'
when third_department_name = '直播部' and sku_id_name like '%肖晗%' then '肖晗'
when flow_pool_name like '%0转低转正%' or channel_name_2='产研测试' then '进校私域合作'
when flow_pool_name like '%天津智慧双子%'	then '创新社群'
when third_department_name like '%城市定制%' then '点睛卷'	
when period_name like '%多学科拓展%' and third_department_name like '%私域运营%' then '市场私域入群'
when put_plan_name like '%赠课失败%' and third_department_name = '线上商务部' then 'KOC赠课失败'
when flow_pool_name like '%自然流%' and source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07') and sku_id_name like '%周帅%' then 'KOC-周帅'	
when flow_pool_name like '%自然流%' and source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07') and sku_id_name like '%肖晗%' then 'KOC-肖晗'	
when flow_pool_name like '%自然流%' and source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07') and sku_id_name like '%朱汉祺%'  and flow_original_order_activity_price like '%1100%' then 'KOC-5元朱汉祺'
when flow_pool_name like '%自然流%' and source_manager_name in ('赵语诗','崔文轩','孙培尧')	then '自孵化KOC-5元纯课'
when flow_pool_name like '%自然流%' and (sku_id_name like '%朱博士%' or sku_id_name like '%朱汉祺%') and rule_name like '%9%' and rule_name not like '%29%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '朱博士9元'
when flow_pool_name like '%自然流%' and sku_id_name like '%朱博士%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '朱博士29'
when flow_pool_name like '%自然流%' and sku_id_name like '%亚飞%' and rule_name like '%99%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '孟亚飞99-1组'	
when flow_pool_name like '%自然流%' and sku_id_name like '%亚飞%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组')  then '孟亚飞9元'	
when flow_pool_name like '%自然流%' and sku_id_name like '%曹忆%' then '曹忆'	
when flow_pool_name like '%自然流%' and rule_name like '%朱博士%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '朱博士29'
when flow_pool_name like '%自然流%' and source_manager_name like '%邵万昕%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '朱博士29'
when flow_pool_name like '%自然流%' and rule_name like '%亚飞%' and rule_name like '%99%' then '孟亚飞99-1组'	
when flow_pool_name like '%自然流%' and rule_name like '%亚飞%'  then '孟亚飞9元'	
when flow_pool_name like '%自然流%' and rule_name like '%郭艺%'  then '郭艺'
when flow_pool_name like '%自然流%' and rule_name like '%汤雪%'  then '汤老师'	
when flow_pool_name like '%自然流%' and rule_name like '%曹忆%' then '曹忆'		
when flow_pool_name like '%途途教室%' or first_department_name like 'TUTU' then '途途APP'
when second_department_name = '市场四部' then '市场四部'
when source_manager_name in ('宋莹莹','辛世如') and channel_name_2 in ('视频号') then '信息流-虚拟号挂车'
when rule_name like '%训练营%' and rule_name like '%市场私域%' then '市场私域入群'
when flow_pool_name like '%青少-私域%' then '青少私域'
when put_plan_name like '%AI名师%' then 'AI直播'
when channel_name_1= '信息流' and (put_plan_name like '%抖音私信%' or put_plan_name like '%初三0元%' or put_plan_name like '%高中0元%') then '信息流-抖音私信'
when rule_name like '%途途私域%' or (rule_name like '%私域%' and first_department_name = 'TT') then '途途私域'
else '其他未知流量' end as channel_map,
case 
    when rule_name like '%高一%' then '高一'
    when rule_name like '%高二%' then '高二'
    when rule_name like '%高三%' then '高三'
    when rule_name like '%初二%' then '初二'
    when rule_name like '%初三%' then '初三'
    when rule_name like '%初一%' then '初一'
    else lead_purchase_intention_level2_category_name
end as grade_1,
    coalesce(lead_count,0) lead_count,
    coalesce(valid_lead_count,0) valid_lead_count,
    coalesce(merge_assign_lead_count,0) merge_assign_lead_count,
    coalesce(merge_valid_lead_count,0) merge_valid_lead_count,
    coalesce(conversion_lead_count,0) conversion_lead_count,
    coalesce(subject_count,0) subject_count,
    coalesce(same_lead_period_subject_count,0) same_lead_period_subject_count,
    coalesce(lb_subject_count,0)  lb_subject_count,
    coalesce(same_lead_period_lb_subject_count,0) same_lead_period_lb_subject_count,
    coalesce(order_count,0) order_count,
    coalesce(income_amount,0) income_amount,
    coalesce(in_pay_period_refund_amount,0) in_pay_period_refund_amount,
    coalesce(non_pay_period_refund_amount,0) non_pay_period_refund_amount,
    coalesce(jp_cross_department_refund_amount,0) jp_cross_department_refund_amount,
    coalesce(lead_period_income_amount,0) lead_period_income_amount,
    coalesce(lead_period_refund_amount,0) lead_period_refund_amount,
    coalesce(same_lead_period_order_count,0) same_lead_period_order_count,
    coalesce(same_lead_period_conversion_lead_count,0) same_lead_period_conversion_lead_count,
    coalesce(same_lead_period_income_amount,0) same_lead_period_income_amount,
    coalesce(same_lead_period_refund_amount,0) same_lead_period_refund_amount
from bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df t1
where dt=format_datetime(NOW()-interval '2' hour,'YYYYMMdd') and hour=format_datetime(NOW()-interval '3' hour,'HH' )
and section_assign_employee_first_level_department_name = 'H业务线'
and section_assign_employee_second_level_department_name = '市场部'
and section_assign_employee_third_level_department_name = '市场顾问部'
and period_mapping_first_level_department_name = 'H业务线'),
m2253_zhuanhua as
(select
    period_name,
    channel_map,
    rule_name,
    grade_1,
    depart_1,
    depart,
    jingli,
    zhuguan,
    employee_email_name,
    sum(xiansuo) xiansuo,
    sum(lead_count) as  lead_count,
    sum(valid_lead_count)as can_renew_ds_count_a,
    sum(conversion_lead_count) pay_users,
    sum(same_lead_period_conversion_lead_count)  pay_users_on_period,
    sum(conversion_lead_count-same_lead_period_conversion_lead_count) pay_users_not_on_period,
    sum(subject_count) pay_user_subs,
    sum(same_lead_period_subject_count) pay_user_subs_on_period,
    sum(subject_count-same_lead_period_subject_count) pay_user_subs_not_on_period,
    sum(lb_subject_count) pay_user_subs_joint,
    sum(same_lead_period_lb_subject_count) pay_user_subs_joint_onp,
    sum(lb_subject_count-same_lead_period_lb_subject_count) pay_user_subs_joint_nonp,
    sum(income_amount/100) trade_income,
    sum(in_pay_period_refund_amount/100+non_pay_period_refund_amount/100) trade_refund,
    sum(income_amount/100-in_pay_period_refund_amount/100-non_pay_period_refund_amount/100) trade_profit,
    sum(same_lead_period_income_amount/100) xb_trade_income,
    sum(same_lead_period_income_amount/100-same_lead_period_refund_amount/100) xb_trade_profit,
    sum(income_amount/100-same_lead_period_income_amount/100) kk_trade_income,
    sum(non_pay_period_refund_amount/100) pre_refund,
    sum(case when d_w = '当期' then lead_period_income_amount/100-lead_period_refund_amount/100 else 0 end) as pp_pmit,
    sum(case when d_w = '非当期' then income_amount/100-in_pay_period_refund_amount/100-non_pay_period_refund_amount/100 else 0 end) as ww_pmit
from m2253_data
group by
    period_name,
    channel_map,
    rule_name,
    grade_1,
    depart_1,
    depart,
    jingli,
    zhuguan,
    employee_email_name
)
,
m2253_zx_active as (
    select
        employee_email_name,
        xiaozu,
        jingli,
        department
    from (
        select
            zx.*,
            row_number() over (
                partition by zx.employee_email_name
                order by
                    case
                        when zx.department = '郑州顾问部' then 1
                        when zx.department = '西安一部' then 2
                        when zx.department = '西安二部' then 3
                        else 9
                    end,
                    zx.employee_email_prefix,
                    zx.xiaozu,
                    zx.jingli
            ) as rn
        from temp_table.dingxi01_jiagou_zx zx
        where cast(zx.zaizhi as varchar) = '1'
          and zx.department in ('郑州顾问部', '西安一部', '西安二部')
    ) t
    where rn = 1
)
,
m2253_channel_group_dedup as (
    select
        channel,
        max(channel_group) as channel_group
    from temp_table.dingxi01_channel_group
    group by channel
),
m2253_cost_exact as (
    select
        qici,
        channel,
        grade,
        max(coalesce(cost, 0)) as cost,
        max(coalesce(goal, 0)) as goal
    from temp_table.dingxi01_cost
    where grade <> '0'
    group by
        qici,
        channel,
        grade
),
m2253_cost_zero as (
    select
        qici,
        channel,
        max(coalesce(cost, 0)) as cost,
        max(coalesce(goal, 0)) as goal
    from temp_table.dingxi01_cost
    where grade = '0'
    group by
        qici,
        channel
),
m2253_jiagou_period as (
    select
        qici,
        department,
        employee_email_name,
        xiaozu,
        jingli
    from (
        select
            nullif(trim(cast(jg.qici as varchar)), '') as qici,
            nullif(trim(cast(jg.department as varchar)), '') as department,
            nullif(trim(cast(jg.employee_email_name as varchar)), '') as employee_email_name,
            nullif(trim(cast(jg.xiaozu as varchar)), '') as xiaozu,
            nullif(trim(cast(jg.jingli as varchar)), '') as jingli,
            row_number() over (
                partition by
                    nullif(trim(cast(jg.qici as varchar)), ''),
                    nullif(trim(cast(jg.department as varchar)), ''),
                    nullif(trim(cast(jg.employee_email_name as varchar)), '')
                order by
                    case when nullif(trim(cast(jg.xiaozu as varchar)), '') is not null then 0 else 1 end,
                    nullif(trim(cast(jg.xiaozu as varchar)), ''),
                    nullif(trim(cast(jg.jingli as varchar)), '')
            ) as rn
        from temp_table.dingxi01_jiagou_db jg
    ) t
    where rn = 1
)

select
    zz.period_name,
    zz.channel_map,
    zz.rule_name,
    zz.grade_1,
    zz.depart_1,
    zz.depart,
    coalesce(jg.jingli, nullif(trim(cast(zx.jingli as varchar)), ''), nullif(trim(cast(zz.jingli as varchar)), ''), '未知经理') as jingli,
    coalesce(jg.xiaozu, nullif(trim(cast(zx.xiaozu as varchar)), ''), nullif(trim(cast(zz.zhuguan as varchar)), ''), '未知主管') as zhuguan,
    zz.jingli as jingli_raw,
    zz.zhuguan as zhuguan_raw,
    zz.employee_email_name,
    zz.xiansuo,
    zz.lead_count,
    zz.can_renew_ds_count_a,
    zz.pay_users,
    zz.pay_users_on_period,
    zz.pay_users_not_on_period,
    zz.pay_user_subs,
    zz.pay_user_subs_on_period,
    zz.pay_user_subs_not_on_period,
    zz.pay_user_subs_joint,
    zz.pay_user_subs_joint_onp,
    zz.pay_user_subs_joint_nonp,
    zz.trade_income,
    zz.trade_refund,
    zz.trade_profit,
    zz.xb_trade_income,
    zz.xb_trade_profit,
    zz.kk_trade_income,
    zz.pre_refund,
    zz.pp_pmit,
    zz.ww_pmit,
    case
        when zz.rule_name like '2026年-%' then split_part(zz.rule_name, '-', 2)
        else split_part(zz.rule_name, '-', 1)
    end as sx_qi,
    case
        when zz.can_renew_ds_count_a >= 5 then zz.can_renew_ds_count_a
        else 0
    end as s_lead,
    case
        when zz.can_renew_ds_count_a >= 5
         and zz.trade_profit > 0 then 1
        else 0
    end as podan,
    zz.employee_email_name as name1,
    coalesce(jg.xiaozu, nullif(trim(cast(zx.xiaozu as varchar)), ''), nullif(trim(cast(zz.zhuguan as varchar)), ''), '未知主管') as xiaozu,
    coalesce(jg.jingli, nullif(trim(cast(zx.jingli as varchar)), ''), nullif(trim(cast(zz.jingli as varchar)), ''), '未知经理') as jingli_1,
    channel_grp.channel_group,
    coalesce(ce.cost, cz.cost, 0) as cb_cb,
    coalesce(ce.goal, cz.goal, 0) as gl_gl
from m2253_zhuanhua zz
left join m2253_channel_group_dedup channel_grp
  on channel_grp.channel = zz.channel_map
left join m2253_cost_exact ce
  on ce.channel = zz.channel_map
 and ce.grade = zz.grade_1
 and ce.qici = zz.period_name
left join m2253_cost_zero cz
  on cz.channel = zz.channel_map
 and cz.qici = zz.period_name
 and ce.channel is null
left join m2253_jiagou_period jg
  on jg.qici = zz.period_name
 and jg.department = zz.depart
 and zz.employee_email_name = jg.employee_email_name
left join m2253_zx_active zx
  on zx.employee_email_name = zz.employee_email_name
where zz.period_name > '20260424期'
    ) m
    group by
        m.period_name,
        m.channel_map,
        m.jingli,
        m.xiaozu,
        m.grade_1,
        m.employee_email_name
)
,base as (
select
    rule.*,
    coalesce(jg.xiaozu, zx.xiaozu) as xiaozu,
    coalesce(jg.jingli, zx.jingli) as jingli,
case
    when try(date_parse(substr(rule.friday_period, 1, 8), '%Y%m%d')) = try(date_parse(substr(rule.qici, 1, 8), '%Y%m%d'))
    then 0
    when date_diff('day',
        try(date_parse(substr(rule.friday_period, 1, 8), '%Y%m%d')),
        try(date_parse(substr(rule.qici, 1, 8), '%Y%m%d'))
    ) = 7
    then 1
    when date_diff('day',
        try(date_parse(substr(rule.friday_period, 1, 8), '%Y%m%d')),
        try(date_parse(substr(rule.qici, 1, 8), '%Y%m%d'))
    ) between 14 and 21
    then 2
    when date_diff('day',
        try(date_parse(substr(rule.friday_period, 1, 8), '%Y%m%d')),
        try(date_parse(substr(rule.qici, 1, 8), '%Y%m%d'))
    ) = -7
    then 4
    else 3
end as week_diff
from rule
left join zx_active zx on zx.employee_email_name = rule.name
left join jiagou_period jg
  on jg.qici = rule.friday_period
 and jg.department = rule.depart
 and jg.employee_email_name = rule.name
)
,bucket_agg as (
select
b.qici,
b.channel_1,
b.jingli,
b.xiaozu,
b.grade_list,
b.name,
    sum(case when b.week_diff = 0 then b.name_total_price else 0 end) as gmv_7,
    sum(case when b.week_diff = 1 then b.name_total_price else 0 end) as gmv_14,
    sum(case when b.week_diff = 2 then b.name_total_price else 0 end) as gmv_30,
    sum(case when b.week_diff = 3 then b.name_total_price else 0 end) as gmv_n30,
    sum(case when b.week_diff = 4 then b.name_total_price else 0 end) as gmv_7_h,
    sum(case when b.week_diff = 0 and b.name_total_price < 0 then b.name_total_price else 0 end) as refund_7,
    sum(case when b.week_diff = 1 and b.name_total_price < 0 then b.name_total_price else 0 end) as refund_14,
    sum(case when b.week_diff = 2 and b.name_total_price < 0 then b.name_total_price else 0 end) as refund_30,
    sum(case when b.week_diff = 3 and b.name_total_price < 0 then b.name_total_price else 0 end) as refund_n30,
    sum(case when b.week_diff = 4 and b.name_total_price < 0 then b.name_total_price else 0 end) as refund_7_p,
    sum(case when b.name_total_price < 0 then b.name_total_price else 0 end) as refund_total
from base b
where b.name_total_price <> 0
group by b.qici, b.channel_1, b.jingli, b.xiaozu, b.grade_list, b.name
)
select
qici,
channel_1,
jingli,
xiaozu,
grade_list,
name,
    gmv_7,
    gmv_14,
    gmv_30,
    gmv_n30,
    gmv_7_h,
    gmv_total,
    refund_7,
    refund_14,
    refund_30,
    refund_n30,
    refund_7_p,
    refund_total,
    can_renew_ds_count_a
from (
    select
        coalesce(ma.qici, ba.qici) as qici,
        coalesce(ma.channel_1, ba.channel_1) as channel_1,
        coalesce(ma.jingli, ba.jingli) as jingli,
        coalesce(ma.xiaozu, ba.xiaozu) as xiaozu,
        coalesce(ma.grade_list, ba.grade_list) as grade_list,
        coalesce(ma.name, ba.name) as name,
        coalesce(ba.gmv_7, 0) as gmv_7,
        coalesce(ba.gmv_14, 0) as gmv_14,
        coalesce(ba.gmv_30, 0) as gmv_30,
        coalesce(ba.gmv_n30, 0) as gmv_n30,
        coalesce(ba.gmv_7_h, 0) as gmv_7_h,
        coalesce(ma.metric_gmv_total, 0) as gmv_total,
        coalesce(ba.refund_7, 0) as refund_7,
        coalesce(ba.refund_14, 0) as refund_14,
        coalesce(ba.refund_30, 0) as refund_30,
        coalesce(ba.refund_n30, 0) as refund_n30,
        coalesce(ba.refund_7_p, 0) as refund_7_p,
        coalesce(ba.refund_total, 0) as refund_total,
        coalesce(ma.can_renew_ds_count_a, 0) as can_renew_ds_count_a
    from metric_agg ma
    full outer join bucket_agg ba
      on ma.qici = ba.qici
     and ma.channel_1 = ba.channel_1
     and coalesce(ma.jingli, '') = coalesce(ba.jingli, '')
     and coalesce(ma.xiaozu, '') = coalesce(ba.xiaozu, '')
     and coalesce(ma.grade_list, '') = coalesce(ba.grade_list, '')
     and coalesce(ma.name, '') = coalesce(ba.name, '')
) final_aligned
order by qici desc, jingli, xiaozu, name
