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
dt, top_period, top_order_number, top_paid_time, order_number,lead_id, trade_time, user_id, type, trade_type, trade_status, course_grade, course_subject, clazz_biz_number, clazz_name, teacher_name, employee_email_name,leader_employee_email_name, cast(real_price_0 as decimal(38, 9)) as price
from (
select  dt,
concat(date_format(date_trunc('week', cast(top_paid_time as timestamp) - interval '1' day) + interval '4' day, '%Y%m%d'), '期') as top_period, top_order_number, top_paid_time, ls.order_number, guiyin.lead_id,trade_time, user_id, type, trade_type, trade_status, course_grade, course_subject, clazz_biz_number, clazz_name, teacher_name,leader_employee_email_name, course_first_level_department_name as course_department1, course_second_level_department_name as course_department2, course_third_level_department_name as course_department3, employee_email_name, employee_first_level_department_name as department1, employee_second_level_department_name as department2, employee_third_level_department_name as department3,
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
      and employee_second_level_department_name = '市场部')
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
,lead_rules_ranked as (
    select
        lead_id,
        user_id,
        employee_email_name,
        rule_name,
            ad_account_name,
            channel_name_1,
            channel_name_2,
            channel_name_3,
            channel_provider_name,
            channel_second_provider_name,
            first_department_name,
            flow_order_price,
            flow_orders_income_amount,
            flow_original_order_activity_price,
            flow_pool_name,
            get_customer_way_name,
            lead_create_time,
            lead_purchase_intention_level1_category_name,
            lead_purchase_intention_level2_category_name,
            page_id_name,
            period_name,
            put_plan_name,
            second_department_name,
            sku_id_name,
            source_manager_name,
            source_put_plan_name,
            third_department_name,
            trace_type_name,
            virtual_fifth_department_name,
            virtual_fourth_department_name,
            virtual_second_department_name,
        row_number() over (
            partition by lead_id, employee_email_name
            order by user_id
        ) as rn
    from bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df
    where dt = FORMAT_DATETIME(NOW() - INTERVAL '2' HOUR, 'YYYYMMdd')
      and hour = FORMAT_DATETIME(NOW() - INTERVAL '2' HOUR, 'HH')
      and section_assign_employee_first_level_department_name = 'H业务线'
      and section_assign_employee_second_level_department_name = '市场部'
      and period_mapping_first_level_department_name = 'H业务线'
)
,channel_candidates as (
    select
        lead_id,
        user_id,
        employee_email_name,
        rule_name,
        case
when get_customer_way_name in ('平台自播') and flow_pool_name in ('赢战广东中考','高途专版图书','状元帮教辅','高途专版视频书','本地化专版图书') then '广东图书'
when get_customer_way_name in ('平台自播') and flow_pool_name in ('途铭文化专版图书','途铭文化','博慧星辰文化图书','启迪蔚来','智慧航迹图书','高途浙江初中','高途浙江高中','高途浙江新高一') then '浙江图书'
when get_customer_way_name in ('平台自播') and flow_pool_name in ('沪上名校','沪上领航社','简学文化','魔都校友助学馆','沪上领航高中','沪上领航初中') then '上海图书'
when get_customer_way_name in ('平台自播') and flow_pool_name in ('高途江苏中考','高途赢战中考') then '江苏图书'
when get_customer_way_name in ('平台自播') and flow_pool_name in ('京赋-浙江科学曹忆规划','为真-浙江科学曹忆老师','为真-浙江大科学曹忆老师','京赋-江苏曹忆老师规划','博学星辰初阶规划峥峥','博学星辰-曹忆老师浙江规划','京赋-浙江曹忆老师规划') then '曹忆'
when flow_pool_name='电商退款用户池' and rule_name like '%赠失%' and rule_name like '%朱博士%' then '赠课失败-朱汉祺'
when flow_pool_name='电商退款用户池' and rule_name like '%赠失%' and rule_name like '%春春%' then '赠课失败-陈瑞春'
when flow_pool_name='电商退款用户池' and rule_name like '%赠失%' and rule_name like '%亚飞%' then '赠课失败-孟亚飞'
when flow_pool_name='电商退款用户池' and rule_name like '%赠失%' and rule_name like '%星义%' then '赠课失败-赵星义'
when flow_pool_name='电商退款用户池' and rule_name like '%赠失%' and rule_name like '%郭艺%' then '赠课失败-郭艺'
when second_department_name='本地化大班学部' or source_manager_name in ('鲍大海','杨文卓') then '本地化市场流量'
when third_department_name in ('中价产品项目部','新媒体内容运营部') and rule_name like '%曹忆%' then '曹忆'
when rule_name like '%语数英%' and third_department_name = '新媒体内容运营部' then '语数英'
when third_department_name = '直播部' and sku_id_name like '%山东专版%' then '北京直播山东'
when third_department_name = '直播部' and sku_id_name like '%河南专版%' then '北京直播河南'
when sku_id_name like '%江苏%' and third_department_name = '直播部' then '北京直播江苏'
when third_department_name like '%锋途%' and channel_name_2 = '抖音' then '锋途KOC'
when put_plan_name like '%小红书打粉%' then 'EM-小红书合作'
when trace_type_name like '%转介绍%' then '转介绍'
when flow_pool_name like '%星义大大%' or flow_pool_name like '%星义物理%' then '赵星义'
when ad_account_name in ('高途-高中-DYD搜索-QZ49','高途-高中-DYD搜索-XLHD49','高途-高中-DYD搜索-XLHD50','高途-高中-DYD搜索-QZ50') or ad_account_name like '%DYD1元搜索%' then '搜索1元'
when (flow_pool_name like '%江苏预习%' or  flow_pool_name like '%江苏专版预习%') and channel_name_2 ='抖音' then '西安直播江苏-抖音'
when flow_pool_name like '%自然流%' and rule_name like '%江苏%' and third_department_name='图书营销部' and channel_name_2 ='抖音' then '西安直播江苏-抖音'
when (flow_pool_name like '%江苏预习%' or  flow_pool_name like '%江苏专版预习%') and channel_name_2 ='视频号' then '西安直播江苏-视频号'
when flow_pool_name like '%退款%' and third_department_name ='图书营销部' then '西安直播-退款订单复用'
when flow_pool_name like '%自然流%' and rule_name like '%江苏%' and third_department_name='图书营销部' and channel_name_2 ='视频号' then '西安直播江苏-视频号'
when rule_name like '%北京图书%' and third_department_name='图书营销部' then '西安直播北京'
when sku_id_name like '%安徽%' and third_department_name='图书营销部' then '西安直播安徽'
when flow_pool_name like '%自然流%' and rule_name like '%北京%' and third_department_name='图书营销部' then '西安直播北京'
when source_manager_name in ('马思雨02','袁银') and rule_name like '%集团%' then '集团私域'
when rule_name like '%途途私域%' or (rule_name like '%私域%' and first_department_name = 'TT') or rule_name like '%私域1元%' or (third_department_name='私域招生中心' and flow_pool_name like '%APP%') then '途途私域'
when third_department_name='图书营销部' and (sku_id_name like '%孟亚飞99%' or sku_id_name like '%亚飞%') and channel_name_2 = '百度' then '孟亚飞-2组-百度'
when third_department_name='图书营销部' and (sku_id_name like '%孟亚飞99%' or sku_id_name like '%亚飞%') and channel_name_2 = '抖音' then '孟亚飞-2组-抖音'
when third_department_name = '投放部' and (ad_account_name like '%周帅%') then '信息流-周帅'
when source_manager_name in ('韩正卿') then '抖音私信'
else cast(null as varchar)
end as channel,
        1 as rule_group
    from lead_rules_ranked
    where rn = 1
    union all
    select
        lead_id,
        user_id,
        employee_email_name,
        rule_name,
        case
when third_department_name = '私域运营部' and source_manager_name in ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研','岳一帆02','田起帆','王绍阳','肖佳兴','姚佳03','秦金萍') and (rule_name like '%koc自孵化下引%' or rule_name like '%koc下引%') then '自孵化KOC下引'
when third_department_name = '私域运营部' and source_manager_name in ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研','岳一帆02','田起帆','王绍阳','肖佳兴','姚佳03','秦金萍') then '进校私域合作'
when channel_name_1='市场私域' and (virtual_fourth_department_name in ('郑州学习顾问二部','郑州学习顾问七部','郑州训练营') or virtual_fifth_department_name in ('罗江博团队')) then '市场私域入群'
when third_department_name = '图书营销部' and (rule_name like '%点睛卷%' or sku_id_name like '%押题卷%') then '押题卷'
when third_department_name = '投放部' and channel_name_2 = '小红书' and channel_name_1 <> '搜索营销' then '信息流-小红书'
when third_department_name = '线上商务部' and channel_name_2 = '小红书' then '小红书'
when (flow_pool_name like '%北大汤哥%' or flow_pool_name like '%海淀名师高阶%' or flow_pool_name like '%海淀高阶%' or flow_pool_name like '%高阶英语887%') and sku_id_name like '%小艺%' then '郭艺'
when third_department_name like '%私域%' and rule_name like '%私域%' and rule_name like '%图书%' then '市场私域图书'
when third_department_name like '%私域%' and rule_name like '%品效%' then '市场私域品效'
when third_department_name like '%私域%' and rule_name like '%公域学霸%' then '市场私域公域组'
when third_department_name in ('线上商务部') and source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07','曲默晗') and flow_pool_name like '%退款%' then 'KOC-退款订单复用'
when third_department_name in ('直播部','新媒体内容运营部','市场一组','私域运营部') and flow_pool_name ='电商退款用户池' then 'IP退款订单复用'
when third_department_name in ('直播部','新媒体内容运营部','市场一组','私域运营部') and put_plan_name like '%失败%' and flow_pool_name ='电商退款用户池' then '赠课失败'
when third_department_name in ('直播部','新媒体内容运营部','市场一组')  and (flow_pool_name ='初阶化学规划' or flow_pool_name like '%启迪-初阶老师%') then '曹忆'
when (third_department_name = '图书营销部' and sku_id_name like '%真题%') or (third_department_name='直播部' and sku_id_name like '%真题%') then '西安图书直播间-直播'
when (third_department_name = '图书营销部' and sku_id_name not like '%真题%') or (third_department_name='直播部' and sku_id_name  like '%秒懂%') or (third_department_name='直播部' and sku_id_name  like '%图书赠送%') then '西安图书直播间-挂链'
when third_department_name in ('直播部','新媒体内容运营部','市场一组') and (flow_pool_name like '%海淀高阶名师%' or flow_pool_name like '%海淀老师高阶%' or flow_pool_name like '%小艺%' or flow_pool_name like '%老蒋文化%') then '郭艺'
when third_department_name in ('直播部','新媒体内容运营部','市场一组') and flow_pool_name like '%电商退款%' and rule_name like '%郭艺99%' then '郭艺'
when put_plan_name like '%国培教育-0元%' or put_plan_name like '%易喆教育-0元%' or put_plan_name like '%钟情-0元%' or put_plan_name like '%中望达-0元%' or put_plan_name like '%晨硕-0元%' or put_plan_name like '%彩石-0元入群%' then '创新商务入群'
when third_department_name='KOC孵化部' and flow_pool_name like '%电商退款%' and put_plan_name like '%失败%' then '自孵化KOC-赠课失败'
when third_department_name='KOC孵化部' and flow_pool_name like '%电商退款%' and put_plan_name like '%退%' then '自孵化KOC-退款订单复用'
when source_manager_name = '方俊结01' and put_plan_name like '%赠课后退款%' then 'KOC-赠课后退款'
when third_department_name = '直播部' and (sku_id_name like '%春春%' or sku_id_name like '%瑞春%' or rule_name like '%春春%' or rule_name like '%瑞春%') and channel_name_2='百度' then '陈瑞春-百度'
when third_department_name = '直播部' and (sku_id_name like '%春春%' or sku_id_name like '%瑞春%' or rule_name like '%春春%' or rule_name like '%瑞春%') and channel_name_2='抖音' then '陈瑞春-抖音199'
when third_department_name = '直播部' and (sku_id_name like '%春春%' or sku_id_name like '%瑞春%' or rule_name like '%春春%' or rule_name like '%瑞春%') and channel_name_2='视频号' then '陈瑞春-视频号49'
when third_department_name = '直播部' and (sku_id_name like '%朱博士99%' or rule_name like '%朱汉祺99%' or rule_name like '%朱博士%' or flow_pool_name like '%朱博士%' or sku_id_name like '%朱博士%') and channel_name_2 = 'B站' then '朱博士-B站'
when third_department_name = '直播部' and (sku_id_name like '%朱博士99%' or rule_name like '%朱汉祺99%' or rule_name like '%朱博士%' or flow_pool_name like '%朱博士%' or sku_id_name like '%朱博士%') and channel_name_2 = '百度' then '朱博士-百度'
when third_department_name = '直播部' and (sku_id_name like '%朱博士99%' or rule_name like '%朱汉祺99%' or rule_name like '%朱博士%' or flow_pool_name like '%朱博士%' or sku_id_name like '%朱博士%') and channel_name_2 = '抖音' then '朱博士-抖音199'
when third_department_name = '直播部' and (sku_id_name like '%朱博士99%' or rule_name like '%朱汉祺99%' or rule_name like '%朱博士%' or flow_pool_name like '%朱博士%' or sku_id_name like '%朱博士%') and channel_name_2 = '视频号' then '朱博士-视频号49'
when (third_department_name = '直播部' and (sku_id_name like '%朱博士%' or sku_id_name like '%朱汉祺%') and rule_name like '%9%' and rule_name not like '%29%' and sku_id_name not like '%急%' and sku_id_name not like '%礼盒29%') or (third_department_name = '直播部' and sku_id_name like '%朱博士9%') then '朱博士9元'
when ad_account_name like '%春春%' and channel_name_1 = '信息流' then '信息流-陈瑞春'
when channel_name_1 = '信息流' and channel_name_2='B站' and (page_id_name like '%0元物化%') then 'B站信息流-曹忆'
when channel_name_1 = '信息流' and channel_name_2='B站' and (page_id_name like '%赵星义%') then 'B站信息流-赵星义'
when channel_name_1 = '信息流' and channel_name_2='B站' and (page_id_name like '%亚飞%' or source_put_plan_name like '%亚飞%'   or page_id_name like '%初中-0元%') then 'B站信息流-亚飞'
when (flow_pool_name like '%朱博士%' or flow_pool_name like '%双博士%' or flow_pool_name like '%教育规划%') and third_department_name <> '线上商务部' and period_name not like '%多学科拓展%' and rule_name not like '%张杰%' and sku_id_name not like '%马凯鹏IP%' and third_department_name='直播部' then '朱博士29'
else cast(null as varchar)
end as channel,
        2 as rule_group
    from lead_rules_ranked
    where rn = 1
    union all
    select
        lead_id,
        user_id,
        employee_email_name,
        rule_name,
        case
when put_plan_name like '%朱博士说教育%' and period_name not like '%多学科拓展%' and flow_pool_name not like '%高分讲堂%' and  flow_pool_name not like '%总裁%' and third_department_name='直播部' then '朱博士29'
when (flow_pool_name like '%朱博士讲英语%' or flow_pool_name like '%朱博士英语%' or flow_pool_name like '%朱汉祺说英语%' or flow_pool_name like '%朱博士说英语%' or flow_pool_name like '%教育规划%' or flow_pool_name like '%双博士英语规划%' or flow_pool_name like '%朱博士满分英语%' or flow_pool_name like '%英语教父朱博士%' or (flow_pool_name like '%中考决胜天团%' and lead_purchase_intention_level1_category_name = '规划系统')) and third_department_name = '直播部' and period_name not like '%多学科拓展%' and sku_id_name not like '%马凯鹏IP%' and third_department_name='直播部' then '朱博士29'
when (flow_pool_name like '%汤哥%' or flow_pool_name like '%汤老师%') and period_name not like '%多学科拓展%' and third_department_name in ('直播部','新媒体内容运营部') then '汤老师'
when source_manager_name = '陈晓菁04' and channel_provider_name not like '%开拓%' and put_plan_name not like '%九学%' then '商务低价'
when (flow_pool_name like '%孟帝%' or flow_pool_name like '%孟老师%' or flow_pool_name like '%中考数学冲刺%' or flow_pool_name like '%8升9数学%' or flow_pool_name like '%孟亚飞讲数学%' or flow_pool_name like '%中考冲刺%' or flow_pool_name like '%中考满分冲刺%' or flow_pool_name like '%押题王孟亚飞%' or flow_pool_name like '%中考数学大通关%' or flow_pool_name like '%中考数学规划%' or flow_pool_name like '%亚飞数学%' or flow_pool_name like '%孟帝数学%' or flow_pool_name like '%亚飞秒解思维%' or flow_pool_name like '%亚飞解题%')  and period_name not like '%多学科拓展%' and channel_name_2 not like '%KOL%' and third_department_name='直播部' and channel_name_2 = '抖音' then '孟亚飞-1组-抖音'
when (flow_pool_name like '%孟帝%' or flow_pool_name like '%孟老师%' or flow_pool_name like '%中考数学冲刺%' or flow_pool_name like '%8升9数学%' or flow_pool_name like '%孟亚飞讲数学%' or flow_pool_name like '%中考冲刺%' or flow_pool_name like '%中考满分冲刺%' or flow_pool_name like '%押题王孟亚飞%' or flow_pool_name like '%中考数学大通关%' or flow_pool_name like '%中考数学规划%' or flow_pool_name like '%亚飞数学%' or flow_pool_name like '%孟帝数学%')  and period_name not like '%多学科拓展%' and channel_name_2 not like '%KOL%' and third_department_name='直播部' and channel_name_2 = '视频号' then '孟亚飞-1组-视频号'
when (flow_pool_name like '%孟帝%' or flow_pool_name like '%孟老师%' or flow_pool_name like '%中考数学冲刺%' or flow_pool_name like '%8升9数学%' or flow_pool_name like '%孟亚飞讲数学%' or flow_pool_name like '%中考冲刺%' or flow_pool_name like '%中考满分冲刺%' or flow_pool_name like '%押题王孟亚飞%' or flow_pool_name like '%中考数学大通关%' or flow_pool_name like '%中考数学规划%' or flow_pool_name like '%亚飞数学%' or flow_pool_name like '%孟帝数学%')  and period_name not like '%多学科拓展%' and channel_name_2 not like '%KOL%' and third_department_name='直播部' and channel_name_2 = 'B站' then '孟亚飞-1组-B站'
when (flow_pool_name like '%孟帝%' or flow_pool_name like '%孟老师%' or flow_pool_name like '%中考数学冲刺%' or flow_pool_name like '%8升9数学%' or flow_pool_name like '%孟亚飞讲数学%' or flow_pool_name like '%中考冲刺%' or flow_pool_name like '%中考满分冲刺%' or flow_pool_name like '%押题王孟亚飞%' or flow_pool_name like '%中考数学大通关%' or flow_pool_name like '%中考数学规划%' or flow_pool_name like '%亚飞数学%' or flow_pool_name like '%孟帝数学%')  and period_name not like '%多学科拓展%' and channel_name_2 not like '%KOL%' and third_department_name='直播部' and channel_name_2 not like '%百度%' then '孟亚飞99-1组'
when (flow_pool_name like '%孟帝%' or flow_pool_name like '%孟老师%' or flow_pool_name like '%中考数学冲刺%' or flow_pool_name like '%8升9数学%' or flow_pool_name like '%孟亚飞讲数学%' or flow_pool_name like '%中考冲刺%' or flow_pool_name like '%中考满分冲刺%' or flow_pool_name like '%押题王孟亚飞%' or flow_pool_name like '%中考数学大通关%' or flow_pool_name like '%中考数学规划%' or flow_pool_name like '%亚飞数学%')  and period_name not like '%多学科拓展%' and channel_name_2 not like '%KOL%' and third_department_name='直播部' and channel_name_2 = '百度' then '孟亚飞-1组-百度'
when put_plan_name like '%刘家晋讲图文%' or put_plan_name like '%孟帝数学%' and third_department_name='直播部' then '孟亚飞9元'
when flow_pool_name like '%汐子%' and period_name not like '%多学科拓展%' and sku_id_name  like '%亚飞%' and third_department_name='直播部' and rule_name like '%99%' then '孟亚飞99-1组'
when (flow_pool_name like '%曹忆%' or flow_pool_name like '%dudu%' or flow_pool_name like '%中考决胜天团%' or flow_pool_name like '%具象思维%' or flow_pool_name like '%在逃发面馒头%' or flow_pool_name like '%库洛米%' and lead_purchase_intention_level1_category_name <> '规划系统') and period_name not like '%多学科拓展%' and third_department_name in ('直播部','新媒体内容运营部') then '曹忆'
when first_department_name ='市场部' and channel_name_1 <> '站内获客' and channel_name_2 <> 'APP' then '集团私域'
when third_department_name = '私域运营部' and rule_name not like '%训练营%' and virtual_fifth_department_name not in ('罗江博团队') and rule_name not like '%复用%' and rule_name not like '%未加好友%' and channel_name_2 <> '内部换量' then '市场私域低价单'
when third_department_name = '私域运营部' and rule_name not like '%训练营%'  and rule_name not like '%复用%' and rule_name not like '%未加好友%' and channel_name_2 <> '内部换量' and flow_original_order_activity_price = '0.0' then '市场私域低价单'
when channel_name_2 in ('APP','M站','PC') and flow_pool_name not like '%途途%' then 'APP'
when channel_name_2 in ('小程序') and flow_pool_name  like '%高途体验课%' then 'APP'
when channel_provider_name like '%唐山TMK%' then '唐山TMK'
when source_manager_name in ('高文羽') and channel_provider_name not like '%唐山TMK%' and channel_provider_name not like '%郑州%' then '人工外呼'
when source_manager_name = '冯银晨' and channel_name_2 = '小红书' then '信息流-小红书'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and page_id_name like '%汤雪%' then 'B站信息流-汤学健'
when (channel_name_1 = '信息流' and channel_name_2 <> 'B站' and third_department_name NOT LIKE '%商务%' and put_plan_name not like '%初三0元%' and put_plan_name not like '%抖音私信%' and put_plan_name not like '%高中0元%' and flow_original_order_activity_price not like '%1990%') or (channel_name_2 = 'B站' and third_department_name like '%投放%') then '信息流'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and (page_id_name like '%郭艺%') then 'B站信息流-郭艺'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and (page_id_name like '%朱博士%') then 'B站信息流-朱汉祺'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and page_id_name like '%肖晗%' then 'B站信息流'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and (page_id_name like '%马凯鹏%' or ad_account_name like '%化学%') then 'B站信息流-马凯鹏'
when channel_name_1 = '信息流'  and channel_name_2 = 'B站' and third_department_name not like '%投放%' and  (sku_id_name like '%陈瑞春%' or rule_name like '%陈瑞春%') and (ad_account_name  like '%语文%' or source_put_plan_name like '%自然流%' or page_id_name like '%春春%') then 'B站信息流-陈瑞春'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and (flow_original_order_activity_price like '%2990%' or sku_id_name like '%帅师%' or sku_id_name like '%周帅%') and ad_account_name like '%语文%' and  (flow_original_order_activity_price like '%1980%' or flow_original_order_activity_price like '%2980%' or flow_original_order_activity_price like '%2990%') then 'B站信息流-陈瑞春'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and (flow_original_order_activity_price like '%2990%' or sku_id_name like '%帅师%' or sku_id_name like '%周帅%') and ad_account_name not like '%语文%' then 'B站信息流-周帅'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and flow_order_price like '%1980%' and ad_account_name like '%数学%' then 'B站信息流-周帅'
when channel_name_1 = '短直电商' and channel_name_2 = 'B站' and third_department_name  like '%商务%' and   (flow_pool_name like '%春春%' or sku_id_name like '%陈瑞春%') then 'B站信息流-陈瑞春'
when channel_name_1 = '短直电商' and channel_name_2 = 'B站' and third_department_name  like '%商务%' and  (flow_pool_name like '%朱博士%') then 'B站信息流-朱汉祺'
--when third_department_name = '线上商务部' and channel_name_2 = 'B站' and put_plan_name like '%春春%' then 'B站信息流-陈瑞春'
--when third_department_name = '线上商务部' and channel_name_2 = 'B站' and put_plan_name like '%朱博士%' then 'B站信息流-朱汉祺'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and flow_original_order_activity_price not like '%2980%' and flow_original_order_activity_price not like '%2990%' and flow_original_order_activity_price not like '%1980%' then 'B站信息流'
when flow_pool_name = '百度搜索引擎' or channel_name_1='搜索营销' then '信息流搜索'
when flow_pool_name like '%小红书班课%' then '小红书投放'
else cast(null as varchar)
end as channel,
        3 as rule_group
    from lead_rules_ranked
    where rn = 1
    union all
    select
        lead_id,
        user_id,
        employee_email_name,
        rule_name,
        case
when third_department_name = '投放部' and get_customer_way_name = '短视频信息流' and flow_original_order_activity_price like '%100%' then '信息流'
when put_plan_name like  '%福哥私域0元%' then 'KOC-下引'
when flow_pool_name = '中考加油' and sku_id_name like '%孟帝%' then 'KOC-孟亚飞数学'
when flow_pool_name = '中考加油' and sku_id_name  like '%帅师%' then 'KOC-周帅数学'
when source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07','曲默晗') and (sku_id_name like '%孟帝%' or sku_id_name like '%dudu%' or sku_id_name like '%市场初二%' or rule_name like '%亚飞%' or sku_id_name like '%初二高阳%' or sku_id_name like '%高阳初二%' or sku_id_name like '%精品初二%' or rule_name like '%初二%' or sku_id_name like '%菁英初三%' or (virtual_second_department_name = '菁英班学部' and lead_purchase_intention_level2_category_name='初级' and lead_create_time>= '2026-04-15 00:00:00')) then 'KOC-孟亚飞数学'
when source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07','曲默晗') and (sku_id_name like '%帅师%' or rule_name like '%周帅%' or sku_id_name like '%9月升高三%' or sku_id_name like '%新高二%') then 'KOC-周帅数学'
when source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07','曲默晗') and (sku_id_name like '%肖晗%' or rule_name like '%肖晗%') then 'KOC-肖晗'
when source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07','曲默晗') and period_name not like '%多学科拓展%' and sku_id_name not like '%朱汉祺%' and sku_id_name not like '%朱博士%' and sku_id_name not like '%周帅%' and sku_id_name not like '%29元%' then 'KOC-5元纯课'
when source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07','曲默晗') and sku_id_name like '%周帅%' then 'KOC-周帅'
--when (channel_name_2 like '%KOL%' and source_manager_name in ('崔文轩','孙培尧')) or (channel_name_2 like '%抖音%' and source_manager_name in ('徐绮鹤')) and period_name not like '%多学科拓展%' then '自孵化KOC'
when third_department_name in ('品牌效能部','KOC孵化部') and channel_name_2 in ('抖音','视频号','快手','KOL') then '自孵化KOC-5元纯课'
when third_department_name in ('品牌效能部','KOC孵化部') and channel_name_2 in ('抖音','视频号','快手','KOL') and (sku_id_name like '%5元%'or sku_id_name like '%11元%' or flow_original_order_activity_price like '%1100%' or flow_original_order_activity_price like '%500%' or flow_orders_income_amount  like '%1100%' or flow_orders_income_amount  like '%500%' ) then '自孵化KOC-5元纯课'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04','赵艺雅') and channel_name_2 like '%社群%' then '进校社群'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04','赵艺雅') and (channel_name_2 like '%直推%' or (put_plan_name like '%良师益友%' or put_plan_name like '%弘诚1元%')) then '进校直推'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04','赵艺雅') and channel_name_2 like '%TMK%' and (page_id_name like '%1元%' or channel_provider_name like '%禾顺云%') then '进校TMK1元'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04','赵艺雅') and channel_name_2 like '%TMK%' and page_id_name like '%9元%' then '进校TMK9元'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04','赵艺雅') and channel_name_2 like '%书商%' then '进校书商'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04','赵艺雅') and channel_name_2 like '%综合%' and put_plan_name like '%18%' then '进校直播'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04','赵艺雅') and channel_name_2 like '%直播%' then '进校直播'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','赵艺雅') and put_plan_name not like '%0元%' and flow_pool_name not like '%家校共育%' and flow_pool_name not like '%保持热爱%' and flow_pool_name not like '%青松%' and flow_pool_name not like '%原子初三%' and flow_pool_name not like '%南通欣创%' and flow_pool_name not like '%悟之道%' and flow_pool_name not like '%济南梦航%' and channel_name_3 <> '社群' and put_plan_name not like '%善悟%' and put_plan_name not like '%人人通%'  and put_plan_name not like '%%济南格乐' and flow_pool_name not like '%晨硕智学%' and flow_pool_name not like '%兴尧文化%'  and flow_pool_name not like '%济南映像%' and flow_pool_name not like '%山东简单%' and flow_pool_name not like '%争鸣科技%' then '商务低价'
when flow_pool_name like '%南通欣创%' or  flow_pool_name like '%人人通科技%' or flow_pool_name like '%易而购%' or flow_pool_name like '%济南梦航%' or flow_pool_name like '%晨硕智学%' or flow_pool_name like '%兴尧文化%' or flow_pool_name like '%济南映像%' or flow_pool_name like '%山东简单%' or flow_pool_name like '%争鸣科技%' then '进校私域合作'
when (flow_pool_name like '%家校共育%' or flow_pool_name like '%保持热爱%' or flow_pool_name like '%青松%' or flow_pool_name like '%悟之道%') and put_plan_name not like '%0元%' then '进校私域合作'
when source_manager_name = '李宁24' and put_plan_name like '%0转低%' then '进校私域合作'
when third_department_name = '私域运营部' and  flow_original_order_activity_price in ('100.0','900.0','300.0') then '进校私域合作'
when third_department_name = '私域运营部' and  flow_original_order_activity_price in ('0.0') and source_manager_name in ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研') then '进校私域合作'
when third_department_name = '私域运营部' and channel_name_1='市场私域' and put_plan_name not like '%公导私%' and put_plan_name not like '%公转私%' and flow_original_order_activity_price = '0.0' and rule_name not like '%激活%' and rule_name not like '%咨询%' and rule_name not like '%训练营%'  and virtual_fifth_department_name not like '%罗江博%' and virtual_fifth_department_name not like '%郑州学习顾问二部%' and source_manager_name not in ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研') then '市场私域低价单'
when source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and channel_provider_name like '%格乐教育%' and channel_name_2 like '%直播%' then '创新社群'
when source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and channel_name_2 like '%社群%' then '创新社群'
when source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and (channel_name_2 like '%直推%' or put_plan_name like '%直推%') then '创新直推'
when source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and (channel_name_2 like '%书商%' or put_plan_name like '%书商%' or page_id_name like '%书商%') then '创新书商'
when source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and channel_name_2 like '%TMK%' and page_id_name like '%1元%' then '创新TMK1元'
when source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and channel_name_2 like '%TMK%' and page_id_name like '%9元%' then '创新TMK9元'
when source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and (channel_name_2 like '%直播%' or page_id_name like '%进校%') then '创新直播'
when source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and channel_name_2<>'公众号' and channel_name_1 = '商务' and flow_pool_name <> '高途云集图书专营店-自然流' and flow_pool_name <> '高途旗舰店—线索—yuxinru' and put_plan_name not like '%社群%' and put_plan_name not like '%小红书班课%' and put_plan_name not like '%外部图书供量%' and channel_second_provider_name not like '%沃德丰店铺线索赠课%' and channel_second_provider_name not like '%智慧城-图书%' and put_plan_name not like '%育甲%' and flow_pool_name not like '%周长磊%' then '创新商务'
when source_manager_name in ('高曼曼01','杨思怡','宋向函') then '图书KOC达人'
--when flow_pool_name like '%市场部-原子合作%' then '原子'
when flow_pool_name like '%市场部-微信私域%' or flow_pool_name like '%市场部-规划报告%' or flow_pool_name like '%规划报告%' or flow_pool_name like '%市场部-小红书%' or flow_pool_name like '%孟浩宇%' then '市场私域低价单'
else cast(null as varchar)
end as channel,
        4 as rule_group
    from lead_rules_ranked
    where rn = 1
    union all
    select
        lead_id,
        user_id,
        employee_email_name,
        rule_name,
        case
when flow_pool_name like '%未加好友%' then '市场私域未加好友'
when flow_pool_name like '公导私' then '进校私域合作'
when (flow_pool_name like '%增长组%' or channel_name_3 = '公众号' or second_department_name = '微信生态部') and channel_name_2 <> 'APP' then '集团私域'
when put_plan_name like '%星耀%' or put_plan_name like '%物理展博%' or  put_plan_name like '%物理谢丽荣%' or put_plan_name like '%牟恩伯%' or  put_plan_name like '%王赞%' or put_plan_name like '%张磊老师高中数学%' or put_plan_name like '%雯姐高中物理大讲堂%' then '百度星耀'
when source_manager_name = '刘福云' and (sku_id_name like '%瑞春%' or sku_id_name like '%春春%') then '陈瑞春'
when third_department_name = '直播部' and sku_id_name like '%周帅%' and channel_name_2 in ('百度','B站') then '周帅'
when third_department_name = '直播部' and sku_id_name like '%孟亚飞%' and rule_name like '%99%' then '孟亚飞99-1组'
when third_department_name = '直播部' and sku_id_name like '%朱汉祺%' then '朱博士99'
when flow_pool_name like '%0转低转正%' or channel_name_2='产研测试' then '进校私域合作'
when flow_pool_name like '%天津智慧双子%' then '创新社群'
when third_department_name like '%城市定制%' then '点睛卷'
when period_name like '%多学科拓展%' and third_department_name like '%私域运营%' then '市场私域入群'
when put_plan_name like '%赠课失败%' and third_department_name = '线上商务部' then 'KOC赠课失败'
when flow_pool_name like '%自然流%' and source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07','曲默晗') and sku_id_name like '%周帅%' then 'KOC-周帅'
when flow_pool_name like '%自然流%' and source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07','曲默晗') and sku_id_name like '%肖晗%' then 'KOC-肖晗'
when flow_pool_name like '%自然流%' and source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07','曲默晗') and sku_id_name like '%朱汉祺%'  and flow_original_order_activity_price like '%1100%' then 'KOC-5元朱汉祺'
when flow_pool_name like '%自然流%' and source_manager_name in ('赵语诗','崔文轩','孙培尧') then '自孵化KOC-5元纯课'
when flow_pool_name like '%自然流%' and (sku_id_name like '%朱博士%' or sku_id_name like '%朱汉祺%') and rule_name like '%9%' and rule_name not like '%29%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '朱博士99'
when flow_pool_name like '%自然流%' and sku_id_name like '%朱博士%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '朱博士99'
when flow_pool_name like '%自然流%' and sku_id_name like '%亚飞%' and rule_name like '%99%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '孟亚飞99-1组'
when flow_pool_name like '%自然流%' and sku_id_name like '%亚飞%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '孟亚飞9元'
when flow_pool_name like '%自然流%' and sku_id_name like '%曹忆%' then '曹忆'
when flow_pool_name like '%自然流%' and rule_name like '%朱博士%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '朱博士99'
when flow_pool_name like '%自然流%' and source_manager_name like '%邵万昕%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '朱博士99'
when flow_pool_name like '%自然流%' and rule_name like '%亚飞%' and rule_name like '%99%' then '孟亚飞99-1组'
when flow_pool_name like '%自然流%' and rule_name like '%亚飞%' then '孟亚飞9元'
when flow_pool_name like '%自然流%' and rule_name like '%郭艺%' then '郭艺'
when flow_pool_name like '%自然流%' and rule_name like '%汤雪%' then '汤老师'
when flow_pool_name like '%自然流%' and rule_name like '%曹忆%' then '曹忆'
when flow_pool_name like '%途途教室%' or first_department_name like 'TUTU' then '途途APP'
when source_manager_name in ('宋莹莹','辛世如') and channel_name_2 in ('视频号') then '信息流-虚拟号挂车'
when rule_name like '%训练营%' and rule_name like '%市场私域%' then '市场私域入群'
when channel_name_1= '信息流' and (put_plan_name like '%抖音私信%' or put_plan_name like '%初三0元%' or put_plan_name like '%高中0元%') then '信息流-抖音私信'
when rule_name like '%途途私域%' or (rule_name like '%私域%' and first_department_name = 'TT') then '途途私域'
when get_customer_way_name in ('进校直推','线下渠道商') then '河南进校'
else cast(null as varchar)
end as channel,
        5 as rule_group
    from lead_rules_ranked
    where rn = 1
)
,lead_rules as (
    select
        lead_id,
        user_id,
        employee_email_name,
        rule_name,
        coalesce(
            min_by(
                channel,
                case when channel is not null then rule_group else 999 end
            ),
            '其他未知流量'
        ) as channel_0808
    from channel_candidates
    group by lead_id, user_id, employee_email_name, rule_name
)
---------合并（修复：uid1/uid2 JOIN 去掉 user_id 条件，换号也能匹配）
,order_z as (select *
from (
	select distinct
	t4.*,
	lr.rule_name as rule_name0,
	case
            when lr.rule_name like '%高一%' then '高一'
            when lr.rule_name like '%高二%' then '高二'
            when lr.rule_name like '%高三%' then '高三'
            when lr.rule_name like '%初一%' then '初一'
            when lr.rule_name like '%初二%' then '初二'
            when lr.rule_name like '%初三%' then '初三'
            else '未知'
        end as grade_0,
	case when instr(lr.rule_name, '期') > 0  and instr(lr.rule_name, '期') >= 5 and regexp_like(substr(lr.rule_name, cast(instr(lr.rule_name, '期') - 4 as integer), cast(4 as integer)), '^[0-9]{4}$') then substr(lr.rule_name, cast(instr(lr.rule_name, '期') - 4 as integer), cast(5 as integer)) else null
end as period_0,
	lr.rule_name,
	case
            when lr.rule_name like '%高一%' then '高一'
            when lr.rule_name like '%高二%' then '高二'
            when lr.rule_name like '%高三%' then '高三'
            when lr.rule_name like '%初一%' then '初一'
            when lr.rule_name like '%初二%' then '初二'
            when lr.rule_name like '%初三%' then '初三'
            else t4.course_grade
        end as grade_2,
	case when instr(lr.rule_name, '期') > 0  and instr(lr.rule_name, '期') >= 5 and regexp_like(substr(lr.rule_name, cast(instr(lr.rule_name, '期') - 4 as integer), cast(4 as integer)), '^[0-9]{4}$')
    then substr(lr.rule_name, cast(instr(lr.rule_name, '期') - 4 as integer), cast(5 as integer))
    else null
end as period_2,
	lr.user_id as uid2,
	lr.channel_0808,
	substr(trade_time, cast(1 as integer), cast(10 as integer))  as day
from t4
	-- 0808: one deduplicated lead-rule join supplies both rule slots and latest channel.
	left join lead_rules lr
	  on t4.employee_email_name = lr.employee_email_name
	 and t4.lead_id = lr.lead_id))
------------------------------初数
,cs as (select *,
cast(case when price < cast(0 as decimal(38, 9)) and re_lc > 2 then cast(0 as decimal(38, 9)) else price end as decimal(38, 9)) as valid_price,
case
    when channel_0808 is not null and channel_0808 <> '其他未知流量' then channel_0808
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
end as qudao0,
CASE
    when channel_0808 is not null and channel_0808 <> '其他未知流量' then channel_0808
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
END AS qudao
from order_z
where day >= ${day:1}
  and day < ${day:2})
------------计算订单数（按人+科目），人头数（按人）,联报科目数
,cs_stats as (
    select
        c.*,
        sum(valid_price) over (partition by user_id) as user_t_price,
        count(*) over (partition by user_id) * 1.0 as user_count,
        sum(valid_price) over (partition by user_id, course_subject) as subject_t_price,
        count(*) over (partition by user_id, course_subject) * 1.0 as subject_count
    from cs c
)
,lianbao_stats as (
    select
        user_id,
        count(distinct course_subject) as lianbao_sub_count
    from cs
    group by user_id
)
---------------------------
select
    cs.dt,
    cs.top_period,
    cs.top_order_number,
    cs.top_paid_time,
    cs.order_number,
    cs.lead_id,
    cs.trade_time,
    cs.user_id,
    cs.type,
    cs.trade_type,
    cs.trade_status,
    cs.course_grade,
    cs.course_subject,
    cs.clazz_biz_number,
    cs.clazz_name,
    cs.teacher_name,
    cs.employee_email_name,
    cs.leader_employee_email_name,
    cast(cast(cs.price as decimal(38, 9)) as varchar) as price,
    cs.re_lc,
    cs.introduce_type,
    cs.rule_name0,
    cs.grade_0,
    cs.period_0,
    cs.rule_name,
    cs.grade_2,
    cs.period_2,
    cs.uid2,
    cs.day,
    cast(cast(cs.valid_price as decimal(38, 9)) as varchar) as valid_price,
    cs.qudao0,
    cs.qudao,
    lianbao_stats.lianbao_sub_count,
    round(case
        when round(cs.user_t_price, 2) < 900 then 0
        when round(cs.user_t_price, 2) < 0 then -1.0 / cs.user_count
        else 1.0 / cs.user_count
    end,4) as rentou_count,
    round(case
        when round(cs.subject_t_price, 2) < -140 then -1.0 / cs.subject_count
        when round(cs.subject_t_price, 2) < 1000 then 0
        else 1.0 / cs.subject_count
    end,4) as dingdan_count
from cs_stats cs
left join lianbao_stats on cs.user_id = lianbao_stats.user_id
