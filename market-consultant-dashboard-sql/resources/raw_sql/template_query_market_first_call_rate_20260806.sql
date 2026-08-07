--分母-线索表 service_dw.dm_crm_lead_stats_detail_hf --废弃
--王杰流水表  service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf
--王杰线索天级表  service_dw.app_h_crm_lead_income_refund_full_link_data_df --废弃
--渠道映射逻辑 顾问侧 顾问的 业务类型 年级 统一映射
with call AS
(
with temp_call AS
(
select 
call.*,em.employee_email_name,em.first_level_department_name,em.second_level_department_name,em.third_level_department_name,period.period_name,
regexp_replace(regexp_extract(period_name, '(\d{4}年-\d{4})期', 1),'-|年','')  group_period,
concat(cast(date_format(date_add('day',4,date_trunc('week',date_add('day',-1,date_parse(regexp_replace(regexp_extract(period_name, '(\d{4}年-\d{4})期', 1),'-|年',''),'%Y%m%d')))),'%Y%m%d')as varchar),'期') group_period_name
from 
    (select * from gaotu_crm_offline_statistics.app_mcrm_first_call_task_hf  --顾问首call数据分析表
     where dt=format_datetime(NOW()-interval '2' hour,'YYYYMMdd') and hour=format_datetime(NOW()-interval '2' hour,'HH')
     and is_del='0') call
left join 
    (select * from finance_dw.dim_finance_employee_df --员工维度表
    where dt=format_datetime(NOW()-interval '23' hour,'YYYYMMdd') 
    and first_level_department_name='H业务线' and second_level_department_name in ('精品班学部','菁英班学部')
    ) em on em.account_id=call.account_id
left join 
	(select * from service_dw.dim_service_period_df --期维度表
     where dt=format_datetime(NOW()-interval '23' hour,'YYYYMMdd')  and is_del='0'
    ) period on cast(period.period_code as varchar)=cast(call.biz_number as varchar)
)

select 
group_period_name,user_id,
employee_email_name,first_level_department_name,second_level_department_name,third_level_department_name,
sum(1) task_cnt,--每个顾问在每个周期内分配到的首call任务总数
sum(case when  first_call_status='3' then 1 else 0 end) "是否首CALL",--首call状态“已完成”
sum(case when  first_call_status='3'  and task_tag='1' then 1 else 0 end) "是否有效首CALL"--状态“已完成”+任务标签为“有效”
from temp_call
where employee_email_name is not null
group by 1,2,3,4,5,6
),
t AS
(
select 
--期信息
substr(period_conversion_end_time,1,7) as period_month                                   -- 期结束时间所在月份          -- 期分组
,group_period_name2 group_period_name
,dm.period_name                                                                                             --期完成名称
,period_conversion_begin_time as conversion_begin_timestamp
, period_conversion_end_time as conversion_end_timestamp 
--期对应课程部门
,period_mapping_first_level_department_name
,period_mapping_second_level_department_name
--年级
,lead_purchase_intention_level2_category_name -- 订单年级
,CASE 
            -- 【区域定向】
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
  when rule_name like '%北京直播江苏%' then '北京直播江苏'
when third_department_name like '%锋途%' and channel_name_2 = '抖音' then '锋途KOC'
when put_plan_name like '%小红书打粉%' then 'EM-小红书合作'
when trace_type_name like '%转介绍%' then '转介绍'
when flow_pool_name like '%星义大大%' or flow_pool_name like '%星义物理%' then '赵星义'
when ad_account_name in ('高途-高中-DYD搜索-QZ49','高途-高中-DYD搜索-XLHD49','高途-高中-DYD搜索-XLHD50','高途-高中-DYD搜索-QZ50') then '搜索1元'
when (flow_pool_name like '%江苏预习%' or  flow_pool_name like '%江苏专版预习%') and channel_name_2 ='抖音' then '西安直播江苏-抖音'
when flow_pool_name like '%自然流%' and rule_name like '%江苏%' and third_department_name='图书营销部' and channel_name_2 ='抖音' then '西安直播江苏-抖音'
when (flow_pool_name like '%江苏预习%' or  flow_pool_name like '%江苏专版预习%') and channel_name_2 ='视频号' then '西安直播江苏-视频号'
when flow_pool_name like '%自然流%' and rule_name like '%江苏%' and third_department_name='图书营销部' and channel_name_2 ='视频号' then '西安直播江苏-视频号'
when rule_name like '%北京图书%' and third_department_name='图书营销部' then '西安直播北京'
when flow_pool_name like '%自然流%' and rule_name like '%北京%' and third_department_name='图书营销部' then '西安直播北京'
when source_manager_name in ('马思雨02','袁银') and rule_name like '%集团%' then '集团私域'
when rule_name like '%途途私域%' or (rule_name like '%私域%' and first_department_name = 'TT') or rule_name like '%私域1元%' or (third_department_name='私域招生中心' and flow_pool_name like '%APP%') then '途途私域'
when third_department_name='图书营销部' and (sku_id_name like '%孟亚飞99%' or sku_id_name like '%亚飞%') and channel_name_2 = '百度' then '孟亚飞-2组-百度'
when third_department_name='图书营销部' and (sku_id_name like '%孟亚飞99%' or sku_id_name like '%亚飞%') and channel_name_2 = '抖音' then '孟亚飞-2组-抖音'
when third_department_name = '投放部' and (ad_account_name like '%周帅%') then '信息流-周帅'
when source_manager_name in ('韩正卿') then '抖音私信'
when third_department_name = '私域运营部' and source_manager_name in ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研','岳一帆02','田起帆','王绍阳','肖佳兴','姚佳03') then '进校私域合作'
when channel_name_1='市场私域' and (virtual_fourth_department_name in ('郑州学习顾问二部','郑州学习顾问七部','郑州训练营') or virtual_fifth_department_name in ('罗江博团队')) then '市场私域入群'
when third_department_name = '图书营销部' and (rule_name like '%点睛卷%' or sku_id_name like '%押题卷%')  then '押题卷'
when third_department_name = '投放部' and channel_name_2 = '小红书' and channel_name_1 <> '搜索营销' then '信息流-小红书'
when third_department_name = '线上商务部' and channel_name_2 = '小红书' then '小红书'
when (flow_pool_name like '%北大汤哥%' or flow_pool_name like '%海淀名师高阶%' or flow_pool_name like '%海淀高阶%' or flow_pool_name like '%高阶英语887%') and sku_id_name like '%小艺%'  then '郭艺'
when  third_department_name like '%私域%' and rule_name like '%私域%' and rule_name like '%图书%' then '市场私域图书'
when  third_department_name like '%私域%' and rule_name like '%品效%'  then '市场私域品效'
when  third_department_name like '%私域%' and rule_name like '%公域学霸%'  then '市场私域公域组'
when third_department_name in ('线上商务部') and source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07','曲默晗') and flow_pool_name like '%退款%' then 'KOC-退款订单复用'
when third_department_name in ('直播部','新媒体内容运营部','市场一组','私域运营部') and put_plan_name like '%退%' and flow_pool_name ='电商退款用户池'  then '退款订单复用'
when third_department_name in ('直播部','新媒体内容运营部','市场一组','私域运营部') and put_plan_name like '%失败%' and flow_pool_name ='电商退款用户池'  then '赠课失败'
when third_department_name in ('直播部','新媒体内容运营部','市场一组')  and (flow_pool_name ='初阶化学规划' or flow_pool_name like '%启迪-初阶老师%')  then '曹忆'
when (third_department_name = '图书营销部' and sku_id_name like '%真题%') or (third_department_name='直播部' and sku_id_name like '%真题%') then '西安图书直播间-直播'
when (third_department_name = '图书营销部' and sku_id_name not like '%真题%') or (third_department_name='直播部' and sku_id_name  like '%秒懂%') or (third_department_name='直播部' and sku_id_name  like '%图书赠送%') then '西安图书直播间-挂链'
when third_department_name in ('直播部','新媒体内容运营部','市场一组') and (flow_pool_name like '%海淀高阶名师%' or flow_pool_name like '%海淀老师高阶%' or flow_pool_name like '%小艺%' or flow_pool_name like '%老蒋文化%') then '郭艺'
when third_department_name in ('直播部','新媒体内容运营部','市场一组') and flow_pool_name like '%电商退款%' and rule_name like '%郭艺99%' then '郭艺'
when put_plan_name like '%国培教育-0元%' or put_plan_name like '%易喆教育-0元%' or put_plan_name like '%钟情-0元%' or put_plan_name like '%中望达-0元%' or put_plan_name like '%晨硕-0元%' or put_plan_name like '%彩石-0元入群%'  then '创新商务入群'
when third_department_name='KOC孵化部' and flow_pool_name like '%电商退款%' and put_plan_name like '%失败%' then '自孵化KOC-赠课失败'
when third_department_name='KOC孵化部' and flow_pool_name like '%电商退款%' and put_plan_name like '%退%' then '自孵化KOC-退款订单复用'
when source_manager_name = '方俊结01' and put_plan_name like '%赠课后退款%' then 'KOC-赠课后退款' 
when third_department_name = '直播部' and (sku_id_name like '%春春%' or sku_id_name like '%瑞春%' or rule_name like '%春春%' or rule_name like '%瑞春%') then '陈瑞春'
when third_department_name = '直播部' and (sku_id_name like '%朱博士99%' or rule_name like '%朱汉祺99%' or rule_name like '%朱博士%' or flow_pool_name like '%朱博士%' or sku_id_name like '%朱博士%') then '朱博士99'
when (third_department_name = '直播部' and (sku_id_name like '%朱博士%' or sku_id_name like '%朱汉祺%') and rule_name like '%9%' and rule_name not like '%29%' and sku_id_name not like '%急%' and sku_id_name not like '%礼盒29%') or (third_department_name = '直播部' and sku_id_name like '%朱博士9%') then '朱博士9元'
when ad_account_name like '%春春%' and channel_name_1 = '信息流' then '信息流-陈瑞春'
when channel_name_1 = '信息流' and channel_name_2='B站' and (page_id_name like '%0元物化%') then 'B站信息流-曹忆'
when channel_name_1 = '信息流' and channel_name_2='B站' and (page_id_name like '%赵星义%') then 'B站信息流-赵星义'
when third_department_name = '直播部' and channel_name_1 = '信息流' and channel_name_2 = 'B站'  then 'B站信息流-亚飞(1元)'
when channel_name_1 = '信息流' and channel_name_2='B站' and (page_id_name like '%亚飞%' or source_put_plan_name like '%亚飞%'   or page_id_name like '%初中-0元%') then 'B站信息流-亚飞'
when channel_name_1 = '信息流' and (page_id_name like '%亚飞%' or ad_account_name like '%亚飞%') then '信息流-亚飞'
when (flow_pool_name like '%朱博士%' or flow_pool_name like '%双博士%' or flow_pool_name like '%教育规划%') and third_department_name <> '线上商务部' and period_name not like '%多学科拓展%' and rule_name not like '%张杰%' and sku_id_name not like '%马凯鹏IP%' and third_department_name='直播部' then '朱博士29'
when put_plan_name like '%朱博士说教育%' and period_name not like '%多学科拓展%' and flow_pool_name not like '%高分讲堂%' and  flow_pool_name not like '%总裁%' and third_department_name='直播部' then '朱博士29'
when (flow_pool_name like '%朱博士讲英语%' or flow_pool_name like '%朱博士英语%' or flow_pool_name like '%朱汉祺说英语%' or flow_pool_name like '%朱博士说英语%' or flow_pool_name like '%教育规划%' or flow_pool_name like '%双博士英语规划%' or flow_pool_name like '%朱博士满分英语%' or flow_pool_name like '%英语教父朱博士%' or (flow_pool_name like '%中考决胜天团%' and lead_purchase_intention_level1_category_name = '规划系统')) and third_department_name = '直播部' and period_name not like '%多学科拓展%' and sku_id_name not like '%马凯鹏IP%' and third_department_name='直播部' then '朱博士29'
when (flow_pool_name like '%汤哥%' or flow_pool_name like '%汤老师%') and period_name not like '%多学科拓展%' and third_department_name in ('直播部','新媒体内容运营部')  then '汤老师'
when source_manager_name = '陈晓菁04' and channel_provider_name not like '%开拓%' and put_plan_name not like '%九学%' then '商务低价'  
when (flow_pool_name like '%孟帝%' or flow_pool_name like '%孟老师%' or flow_pool_name like '%中考数学冲刺%' or flow_pool_name like '%8升9数学%' or flow_pool_name like '%孟亚飞讲数学%' or flow_pool_name like '%中考冲刺%' or flow_pool_name like '%中考满分冲刺%' or flow_pool_name like '%押题王孟亚飞%' or flow_pool_name like '%中考数学大通关%' or flow_pool_name like '%中考数学规划%' or flow_pool_name like '%亚飞数学%' or flow_pool_name like '%孟帝数学%' or flow_pool_name like '%亚飞秒解思维%' or flow_pool_name like '%亚飞解题%')  and period_name not like '%多学科拓展%' and channel_name_2 not like '%KOL%' and third_department_name='直播部' and channel_name_2 = '抖音'  then '孟亚飞-1组-抖音'
when (flow_pool_name like '%孟帝%' or flow_pool_name like '%孟老师%' or flow_pool_name like '%中考数学冲刺%' or flow_pool_name like '%8升9数学%' or flow_pool_name like '%孟亚飞讲数学%' or flow_pool_name like '%中考冲刺%' or flow_pool_name like '%中考满分冲刺%' or flow_pool_name like '%押题王孟亚飞%' or flow_pool_name like '%中考数学大通关%' or flow_pool_name like '%中考数学规划%' or flow_pool_name like '%亚飞数学%' or flow_pool_name like '%孟帝数学%')  and period_name not like '%多学科拓展%' and channel_name_2 not like '%KOL%' and third_department_name='直播部' and channel_name_2 = '视频号'  then '孟亚飞-1组-视频号'
when (flow_pool_name like '%孟帝%' or flow_pool_name like '%孟老师%' or flow_pool_name like '%中考数学冲刺%' or flow_pool_name like '%8升9数学%' or flow_pool_name like '%孟亚飞讲数学%' or flow_pool_name like '%中考冲刺%' or flow_pool_name like '%中考满分冲刺%' or flow_pool_name like '%押题王孟亚飞%' or flow_pool_name like '%中考数学大通关%' or flow_pool_name like '%中考数学规划%' or flow_pool_name like '%亚飞数学%' or flow_pool_name like '%孟帝数学%')  and period_name not like '%多学科拓展%' and channel_name_2 not like '%KOL%' and third_department_name='直播部' and channel_name_2 = 'B站'  then '孟亚飞-1组-B站'
when (flow_pool_name like '%孟帝%' or flow_pool_name like '%孟老师%' or flow_pool_name like '%中考数学冲刺%' or flow_pool_name like '%8升9数学%' or flow_pool_name like '%孟亚飞讲数学%' or flow_pool_name like '%中考冲刺%' or flow_pool_name like '%中考满分冲刺%' or flow_pool_name like '%押题王孟亚飞%' or flow_pool_name like '%中考数学大通关%' or flow_pool_name like '%中考数学规划%' or flow_pool_name like '%亚飞数学%' or flow_pool_name like '%孟帝数学%')  and period_name not like '%多学科拓展%' and channel_name_2 not like '%KOL%' and third_department_name='直播部' and channel_name_2 not like '%百度%'  then '孟亚飞99-1组'
when (flow_pool_name like '%孟帝%' or flow_pool_name like '%孟老师%' or flow_pool_name like '%中考数学冲刺%' or flow_pool_name like '%8升9数学%' or flow_pool_name like '%孟亚飞讲数学%' or flow_pool_name like '%中考冲刺%' or flow_pool_name like '%中考满分冲刺%' or flow_pool_name like '%押题王孟亚飞%' or flow_pool_name like '%中考数学大通关%' or flow_pool_name like '%中考数学规划%' or flow_pool_name like '%亚飞数学%')  and period_name not like '%多学科拓展%' and channel_name_2 not like '%KOL%' and third_department_name='直播部' and channel_name_2 = '百度'  then '孟亚飞-1组-百度'
when (flow_pool_name like '%孟帝%' or flow_pool_name like '%孟老师%' or flow_pool_name like '%中考数学冲刺%' or flow_pool_name like '%8升9数学%' or flow_pool_name like '%孟亚飞讲数学%' or flow_pool_name like '%中考冲刺%' or flow_pool_name like '%中考满分冲刺%' or flow_pool_name like '%押题王孟亚飞%' or flow_pool_name like '%中考数学大通关%' or flow_pool_name like '%中考数学规划%' or flow_pool_name like '%亚飞数学%')  and period_name not like '%多学科拓展%' and channel_name_2 not like '%KOL%' and third_department_name='直播部'  then '孟亚飞9元'
when put_plan_name like '%刘家晋讲图文%' or put_plan_name like '%孟帝数学%' and third_department_name='直播部' and rule_name like '%99%'  then '孟亚飞99-1组'  
when put_plan_name like '%刘家晋讲图文%' or put_plan_name like '%孟帝数学%' and third_department_name='直播部' then '孟亚飞9元'  
when flow_pool_name like '%汐子%' and period_name not like '%多学科拓展%' and sku_id_name  like '%亚飞%' and third_department_name='直播部' and rule_name like '%99%'  then '孟亚飞99-1组'
when (flow_pool_name like '%曹忆%' or flow_pool_name like '%dudu%' or flow_pool_name like '%中考决胜天团%' or flow_pool_name like '%具象思维%' or flow_pool_name like '%在逃发面馒头%' or flow_pool_name like '%库洛米%' and lead_purchase_intention_level1_category_name <> '规划系统') and period_name not like '%多学科拓展%' and third_department_name in ('直播部','新媒体内容运营部') then '曹忆'
when first_department_name ='市场部' and channel_name_1 <> '站内获客' and channel_name_2 <> 'APP' then '集团私域'
when third_department_name = '私域运营部' and rule_name not like '%训练营%' and virtual_fifth_department_name not in ('罗江博团队') and rule_name not like '%复用%' and rule_name not like '%未加好友%' and channel_name_2 <> '内部换量' then '市场私域低价单'
when third_department_name = '私域运营部' and rule_name not like '%训练营%'  and rule_name not like '%复用%' and rule_name not like '%未加好友%' and channel_name_2 <> '内部换量' and flow_original_order_activity_price = '0.0' then '市场私域低价单'
when channel_name_2 in ('APP','M站','PC') and flow_pool_name not like '%途途%' then 'APP'
when channel_name_2 in ('小程序') and flow_pool_name  like '%高途体验课%' then 'APP'
when channel_provider_name like '%唐山TMK%' then '唐山TMK' 
when source_manager_name in ('高文羽') and channel_provider_name not like '%唐山TMK%' and channel_provider_name not like '%郑州%' then '人工外呼' 
when source_manager_name = '冯银晨' and channel_name_2 = '小红书' then '信息流-小红书'  
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and page_id_name like '%汤雪%'  then 'B站信息流-汤学健'
when (channel_name_1 = '信息流' and channel_name_2 <> 'B站' and third_department_name NOT LIKE '%商务%' and put_plan_name not like '%初三0元%' and put_plan_name not like '%抖音私信%' and put_plan_name not like '%高中0元%' and flow_original_order_activity_price not like '%1990%') or (channel_name_2 = 'B站' and third_department_name like '%投放%') then '信息流'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and (page_id_name like '%郭艺%') then 'B站信息流-郭艺'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and (page_id_name like '%朱博士%') then 'B站信息流-朱汉祺'
when channel_name_1 = '信息流' and channel_name_2 = 'B站' and third_department_name not like '%投放%' and page_id_name like '%肖晗%' then 'B站信息流'
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
when  flow_pool_name like '%小红书班课%' then '小红书投放'
when third_department_name = '投放部' and get_customer_way_name = '短视频信息流' and flow_original_order_activity_price like '%100%' then '信息流'
when flow_pool_name = '中考加油' and sku_id_name like '%孟帝%' then 'KOC-孟亚飞数学'
when flow_pool_name = '中考加油' and sku_id_name  like '%帅师%' then 'KOC-周帅数学'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07','曲默晗') and (sku_id_name like '%孟帝%' or sku_id_name like '%dudu%' or sku_id_name like '%市场初二%' or rule_name like '%亚飞%' or sku_id_name like '%初二高阳%' or sku_id_name like '%高阳初二%' or sku_id_name like '%精品初二%' or rule_name like '%初二%' or sku_id_name like '%菁英初三%' or (virtual_second_department_name = '菁英班学部' and lead_purchase_intention_level2_category_name='初级' and lead_create_time>= '2026-04-15 00:00:00')) then 'KOC-孟亚飞数学'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07','曲默晗') and (sku_id_name like '%帅师%' or rule_name like '%周帅%' or sku_id_name like '%9月升高三%' or sku_id_name like '%新高二%') then 'KOC-周帅数学'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07','曲默晗') and (sku_id_name like '%肖晗%' or rule_name like '%肖晗%') then 'KOC-肖晗'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07','曲默晗') and period_name not like '%多学科拓展%' and sku_id_name not like '%朱汉祺%' and sku_id_name not like '%朱博士%' and sku_id_name not like '%周帅%' and sku_id_name not like '%29元%' then 'KOC-5元纯课'
when  source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07','曲默晗') and sku_id_name like '%周帅%' then 'KOC-周帅'
--when (channel_name_2 like '%KOL%' and source_manager_name in ('崔文轩','孙培尧')) or (channel_name_2 like '%抖音%' and source_manager_name in ('徐绮鹤')) and period_name not like '%多学科拓展%' then '自孵化KOC'
when third_department_name in ('品牌效能部','KOC孵化部') and channel_name_2 in ('抖音','视频号','快手','KOL')  then '自孵化KOC-5元纯课'
when third_department_name in ('品牌效能部','KOC孵化部') and channel_name_2 in ('抖音','视频号','快手','KOL') and (sku_id_name like '%5元%'or sku_id_name like '%11元%' or flow_original_order_activity_price like '%1100%' or flow_original_order_activity_price like '%500%' or flow_orders_income_amount  like '%1100%' or flow_orders_income_amount  like '%500%' ) then '自孵化KOC-5元纯课'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04','赵艺雅') and channel_name_2 like '%社群%' then '进校社群'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04','赵艺雅') and (channel_name_2 like '%直推%' or (put_plan_name like '%良师益友%' or put_plan_name like '%弘诚1元%')) then '进校直推'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04','赵艺雅') and channel_name_2 like '%TMK%' and (page_id_name like '%1元%' or channel_provider_name like '%禾顺云%') then '进校TMK1元'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04','赵艺雅') and channel_name_2 like '%TMK%' and page_id_name like '%9元%' then '进校TMK9元'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04','赵艺雅') and channel_name_2 like '%书商%' then '进校书商'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04','赵艺雅') and channel_name_2 like '%综合%' and put_plan_name like '%18%' then '进校直播'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04','赵艺雅') and channel_name_2 like '%直播%' then '进校直播'
when source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','赵艺雅') and put_plan_name not like '%0元%' and flow_pool_name not like '%家校共育%' and flow_pool_name not like '%保持热爱%' and flow_pool_name not like '%青松%' and flow_pool_name not like '%原子初三%' and flow_pool_name not like '%南通欣创%' and flow_pool_name not like '%悟之道%' and flow_pool_name not like '%济南梦航%' and channel_name_3 <> '社群' and put_plan_name not like '%善悟%' and put_plan_name not like '%人人通%'  and put_plan_name not like '%%济南格乐' and flow_pool_name not like '%晨硕智学%' and flow_pool_name not like '%兴尧文化%'  and flow_pool_name not like '%济南映像%' and flow_pool_name not like '%山东简单%' and flow_pool_name not like '%争鸣科技%'  then '商务低价'
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
when source_manager_name in ('高曼曼01','杨思怡','宋向函') then '图书KOC达人'
--when flow_pool_name like '%市场部-原子合作%' then '原子'
when flow_pool_name like '%市场部-微信私域%' or flow_pool_name like '%市场部-规划报告%' or flow_pool_name like '%规划报告%' or flow_pool_name like '%市场部-小红书%' or flow_pool_name like '%孟浩宇%' then '市场私域低价单'
when flow_pool_name like '%未加好友%' then '市场私域未加好友'
when flow_pool_name like '公导私' then '进校私域合作'
when (flow_pool_name like '%增长组%' or channel_name_3 = '公众号' or second_department_name = '微信生态部') and channel_name_2 <> 'APP' then '集团私域'
when put_plan_name like '%星耀%' or put_plan_name like '%物理展博%' or  put_plan_name like '%物理谢丽荣%' or put_plan_name like '%牟恩伯%' or  put_plan_name like '%王赞%' or put_plan_name like '%张磊老师高中数学%' or put_plan_name like '%雯姐高中物理大讲堂%' then '百度星耀'
when source_manager_name = '刘福云' and (sku_id_name like '%瑞春%' or sku_id_name like '%春春%') then '陈瑞春'
when third_department_name = '直播部' and sku_id_name like '%周帅%' and channel_name_2 in ('百度','B站')  then '周帅'
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
when flow_pool_name like '%自然流%' and sku_id_name like '%亚飞%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组')  then '孟亚飞9元'  
when flow_pool_name like '%自然流%' and sku_id_name like '%曹忆%' then '曹忆'  
when flow_pool_name like '%自然流%' and rule_name like '%朱博士%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '朱博士99'
when flow_pool_name like '%自然流%' and source_manager_name like '%邵万昕%' and third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '朱博士99'
when flow_pool_name like '%自然流%' and rule_name like '%亚飞%' and rule_name like '%99%' then '孟亚飞99-1组'  
when flow_pool_name like '%自然流%' and rule_name like '%亚飞%'  then '孟亚飞9元'  
when flow_pool_name like '%自然流%' and rule_name like '%郭艺%'  then '郭艺'
when flow_pool_name like '%自然流%' and rule_name like '%汤雪%'  then '汤老师'  
when flow_pool_name like '%自然流%' and rule_name like '%曹忆%' then '曹忆'    
when flow_pool_name like '%途途教室%' or first_department_name like 'TUTU' then '途途APP'
when source_manager_name in ('宋莹莹','辛世如') and channel_name_2 in ('视频号') then '信息流-虚拟号挂车'
when rule_name like '%训练营%' and rule_name like '%市场私域%' then '市场私域入群'
when channel_name_1= '信息流' and (put_plan_name like '%抖音私信%' or put_plan_name like '%初三0元%' or put_plan_name like '%高中0元%') then '信息流-抖音私信'
when rule_name like '%途途私域%' or (rule_name like '%私域%' and first_department_name = 'TT') then '途途私域'
when get_customer_way_name in ('进校直推','线下渠道商') then '河南进校'
else '其他未知流量' end channel_map
,flow_original_order_activity_price/100 activity_price
--城市信息
-- ,c_city_level
-- ,c_province
-- ,c_city
--业务类型 弃用该逻辑，用人员虚拟架构拆分
--,case period_course_category_code when '10' then '训练营' when '20' then '短期班' else '其他' end as business_type
--顾问部门信息
, dm.employee_email_name -- 顾问
, section_assign_employee_first_level_department_name
, section_assign_employee_second_level_department_name
, section_assign_employee_third_level_department_name
,virtual_first_department_name
,virtual_second_department_name
,virtual_third_department_name
,virtual_fourth_department_name
-- ,virtual_fifth_department_name
, virtual_leader_email_name  -- 大组长
, virtual_direct_leader_email_name  -- 小组长
, virtual_mini_leader_email_name -- 战队长
,period_main_teacher_nicknames
,call.employee_email_name call_em_name
--,dm.lead_id
--,user_id
---指标域
, coalesce(sum(lead_cost),0) as cost --线索成本
-- , sum(a.lead_count) as lead_count -- 线索数
--, sum(assign_lead_count) as assign_lead_count -- 分配线索数
, sum(valid_lead_count) as valid_lead_count -- 有效线索数，开课前未退费为有效
, sum(conversion_lead_count) as convert_lead_cnt --转化线索数
, sum(subject_count) as convert_rc_cnt --转化人次数
, sum(order_count) as convert_order_cnt --转化订单数
, sum(same_lead_period_conversion_lead_count) as convert_current_lead_cnt --当期转化线索数
, sum(same_lead_period_subject_count) as convert_current_rc_cnt --当期转化人次数
, sum(same_lead_period_order_count) as convert_current_order_cnt --当期转化订单数
, sum(conversion_lead_count-same_lead_period_conversion_lead_count) as convert_no_current_lead_cnt --往期转化线索数
, sum(subject_count-same_lead_period_subject_count) as convert_no_current_rc_cnt --往期转化人次数
, sum(order_count-same_lead_period_order_count) as convert_no_current_order_cnt --往期转化订单数
--3个退款 当期例本期支付退款  往期例子本期支付退款 历史支付历史支付退款
, sum(coalesce(income_amount,0))/100.00 as income_amount -- 收款金额
, sum(coalesce(in_pay_period_refund_amount,0))/100.00 as refund_amount_pay_onp -- 本期支付本期退款金额  r1
, sum(coalesce(non_pay_period_refund_amount,0))/100.00 as refund_amount_pay_nonp -- 历史支付本期退款退款金额 r2
, sum(coalesce(income_amount,0)-coalesce(in_pay_period_refund_amount,0)-coalesce(non_pay_period_refund_amount,0))/100.00 as promit_amount -- 转化净额

,sum(coalesce(same_lead_period_income_amount,0))/100.00	income_amount_onp -- 当期收款金额
,sum(coalesce(same_lead_period_refund_amount,0))/100.00	 refund_amount_lead_onp  -- 当期例子本期退款金额   r1_01
,sum(coalesce(same_lead_period_income_amount,0)-coalesce(same_lead_period_refund_amount,0))/100.00	 promit_amount_onp -- 当期净收金额

,sum(coalesce(income_amount,0)-coalesce(same_lead_period_income_amount,0))/100.00	income_amount_nonp -- 往期收款金额
,sum(coalesce(in_pay_period_refund_amount,0)-coalesce(same_lead_period_refund_amount,0))/100.00	 refund_amount_lead_nonp  -- 往期例子本期支付本期退款金额 r1_02
,sum(coalesce(same_lead_period_income_amount,0)-coalesce(same_lead_period_refund_amount,0))/100.00	 promit_amount_nonp -- 往期净收金额

, sum(if(valid_lead_count>0, friend_lead_count, 0)) as friend_count --好友线索数
,sum(if(valid_lead_count>0, is_within_24h_haoyou, 0)) as friend_24h_count --24h好友线索数
, sum(if(valid_lead_count>0 and section_assign_call_connected_count + section_assign_call_missed_count > 0,1,0)) as call_lead_count -- 拨打线索数
, sum(if(valid_lead_count>0 and section_assign_call_connected_count>0,1,0)) as connected_lead_count -- 接通线索数
, sum(if(valid_lead_count>0, section_assign_all_call_duration, 0)) as call_duration -- 拨打时长s
, sum(if(valid_lead_count>0, period_is_login_app, 0)) as login_lead_count -- 登录线索数
,sum(coalesce(is_combine_need_attend,0)) is_need_attend --(应出勤数)
,sum(coalesce(is_live_learn,0)) attend_lead_count
,sum(coalesce(is_valid_live_learn,0)) valid_attend_duration
,sum(coalesce(task_cnt,0)) first_call_task_cnt
--,sum(coalesce("是否首CALL",0)) first_call_cnt
,sum(coalesce("是否有效首CALL",0)) valid_first_call_cnt
--, sum(if(valid_lead_count>0 and learn_duration>0,1,0)) as attend_lead_count -- 到课线索数
--, sum(if(valid_lead_count>0, learn_duration, 0)) as attend_duration -- 到课时长s
,sum(same_lead_period_income_amount) income_convert_amount_onp
,sum(same_lead_period_refund_amount) refund_convert_amount_onp	
,sum(same_lead_period_income_amount-same_lead_period_refund_amount) net_convert_amount_onp
,sum(case when first_call_time_diff_hour>=0 and first_call_time_diff_hour<=24 and valid_lead_count>0 then 1 else 0 end) first_call_in_24h
,sum(case when first_call_time_diff_hour>24 and first_call_time_diff_hour<=48 and valid_lead_count>0 then 1 else 0 end) first_call_in_48h
,sum(case when first_call_time_diff_hour is not null and valid_lead_count>0 then 1 else 0 end) first_call_cnt
from 
--业财线转底表
(
select *,
concat(cast(date_format(date_add('day',4,date_trunc('week',date_add('day',-1,date_parse(replace(concat(group_period_year,group_period_term),'期',''),'%Y%m%d')))),'%Y%m%d')as varchar),'期') group_period_name2, 
CASE WHEN (
COALESCE(DATE_DIFF('hour', TRY_CAST(qw_add_time AS TIMESTAMP), TRY_CAST(section_assign_time AS TIMESTAMP)), 24) < 24
 OR
COALESCE(DATE_DIFF('hour', TRY_CAST(gw_add_time AS TIMESTAMP), TRY_CAST(section_assign_time AS TIMESTAMP)), 24) < 24
) THEN 1 ELSE 0 END AS is_within_24h_haoyou,
date_diff('hour', 
    CAST(section_assign_time AS timestamp),--截面分配时间 
    CAST(first_call_time AS timestamp)--分配后首call时间
  ) AS first_call_time_diff_hour  --分配时间和首call间隔之间的小时数
from
bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df  
where  dt=format_datetime(NOW()-interval '2' hour,'YYYYMMdd') 
and hour=format_datetime(NOW()-interval '2' hour,'HH') 
and section_assign_employee_first_level_department_name = 'H业务线'
and section_assign_employee_second_level_department_name = '市场部'
and period_mapping_first_level_department_name = 'H业务线'
and period_mapping_second_level_department_name = '精品班学部'
) dm
-- left JOIN
-- (
-- select distinct lead_id,c_city_level,c_province,c_city from
-- service_dw.app_h_crm_lead_income_refund_full_link_data_df  where  dt=format_datetime(NOW()-interval '30' hour,'YYYYMMdd')
-- ) d on d.lead_id=dm.lead_id
--关联到课率
left join 
(
select
lead_id,
concat(cast(date_format(date_add('day',4,date_trunc('week',date_add('day',-1,date_parse(replace(regexp_replace(regexp_extract(period_name, '(\d{4}年-\d{4})期', 1),'-|年',''),'期',''),'%Y%m%d')))),'%Y%m%d')as varchar),'期') group_period_name, 
sum(is_combine_need_attend) is_combine_need_attend--是否应出勤
,sum(if(live_learn_duration > 0,1,0)) is_live_learn --是否直播课节
,sum(is_valid_live_learn) is_valid_live_learn --是否直播有效到课
from service_dw.dws_service_order_lead_learn_detail_hf--行课表
where dt=format_datetime(NOW()-interval '2' hour,'YYYYMMdd') and hour=format_datetime(NOW()-interval '2' hour,'HH')
and is_sole_clazz_lesson_number = 1 --是否唯一课节，避免一个线索同一班级，存在多个订单
and is_final_index = 1 --是否生效课节，排除赠课、视频、物流发货班级课节
and final_index = 1 --首节
and is_combine_need_attend = 1 --是否应出勤课节
group by 1,2
) dk on dk.group_period_name=dm.group_period_name2 and dm.lead_id=dk.lead_id
--关联首CALL率
left join call on call.user_id=dm.user_id and call.group_period_name=dm.group_period_name2
where 
period_mapping_first_level_department_name='H业务线'
and section_assign_employee_first_level_department_name='H业务线'
and section_assign_employee_third_level_department_name not like '%学习规划%'
and period_first_level_course_project_name!='美好家庭'
and concat(group_period_year,group_period_term)>'20250901期'
--and concat(group_period_year,group_period_term)<'20241129期'
group by 
1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23
),
--获取顾问带班的年级和渠道
em AS
(
select 
group_period_name,employee_email_name,lead_purchase_intention_level2_category_name,channel_map
, section_assign_employee_first_level_department_name
, section_assign_employee_second_level_department_name
, section_assign_employee_third_level_department_name
,virtual_first_department_name
,virtual_second_department_name
,virtual_third_department_name
,virtual_fourth_department_name
,virtual_leader_email_name as dazu -- 大组长
,virtual_direct_leader_email_name as xiaozu -- 小组长
,virtual_mini_leader_email_name as zhandui -- 战队长
,case when virtual_fourth_department_name in ('郑州学习顾问二部','郑州学习顾问七部','罗江博团队','郑州训练营') then '训练营' when virtual_fourth_department_name
='上海团队' then '上海团队' else '短期班' end business_type
,row_number() over(partition by group_period_name,employee_email_name order by sum(valid_lead_count) desc) n
,case when sum(valid_lead_count)>10 then 1 else 0 end is_dai_ban
,sum(valid_lead_count) lead_cnt,sum(income_amount) income_amount
,array_join(array_distinct(array_agg(period_main_teacher_nicknames)),',') teachers
from t
group by 
1,2,3,4,5,6,7,8,9,10,11,12,13,14
) 

select 
--顾问架构 主带年级 是否带班等
em.section_assign_employee_first_level_department_name
,em.section_assign_employee_second_level_department_name
,em.section_assign_employee_third_level_department_name
,em.virtual_first_department_name
,em.virtual_second_department_name
,em.virtual_third_department_name
,em.virtual_fourth_department_name
,em.dazu
,em.xiaozu
,em.zhandui
,em.employee_email_name
,em.business_type
,em.lead_purchase_intention_level2_category_name
,em.is_dai_ban
-- --期信息
,t.period_month
,concat(cast(date_format(date_add('day',4,date_trunc('week',date_add('day',-1,date_parse(replace(t.group_period_name,'期',''),'%Y%m%d')))),'%Y%m%d')as varchar),'期') group_period_name
,t.period_name
,t.conversion_begin_timestamp
,t.conversion_end_timestamp
--渠道信息
,t.channel_map
--指标
,t.valid_lead_count
,t.friend_count
,t.friend_24h_count
,t.attend_lead_count
,t.first_call_task_cnt
,t.valid_first_call_cnt
,t.first_call_in_24h
,t.first_call_in_48h
,t.first_call_cnt
,t.convert_lead_cnt --转化线索数
,t.convert_rc_cnt --转化人次数
,t.convert_order_cnt --转化订单数
,t.convert_current_lead_cnt --当期转化线索数
,t.convert_current_rc_cnt --当期转化人次数
,t.convert_current_order_cnt --当期转化订单数
,t.income_amount -- 收款金额
,t.income_amount-t.promit_amount refund_amount-- 退款金额
,t.promit_amount  --净收金额
,t.income_amount_onp -- 当期收款金额
,t.refund_amount_lead_onp  -- 当期例子本期退款金额   r1_01
,t.promit_amount_onp -- 当期净收金额
,em.channel_map em_channel_map
,case 
when t.channel_map='app' then 'app'
when em.business_type='训练营' then '训练营' 
else t.channel_map  end channel_map1
,em.teachers
,format_datetime(NOW()-interval '1' hour,'YYYYMMdd HH点') dt
from t
--em顾问表
left join em on t.group_period_name=em.group_period_name and t.employee_email_name=em.employee_email_name and em.n=1
where
em.virtual_third_department_name = '市场顾问部'
and t.channel_map != 'KOC赠课失败'
and t.channel_map != 'IP赠课失败'
and t.group_period_name=${group_period_name}
