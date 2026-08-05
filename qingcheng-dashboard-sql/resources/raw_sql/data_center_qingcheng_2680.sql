with biz_qici_calendar as (
select *
from (
    values
        ('20260716期', '0716期', '20260717期', '0717期', date '2026-07-14', date '2026-07-19'),
        ('20260722期', '0722期', '20260724期', '0724期', date '2026-07-20', date '2026-07-25'),
        ('20260728期', '0728期', '20260731期', '0731期', date '2026-07-26', date '2026-07-31'),
        ('20260803期', '0803期', '20260807期', '0807期', date '2026-08-01', date '2026-08-06'),
        ('20260808期', '0808期', '20260814期', '0814期', date '2026-08-07', date '2026-08-12')
) as t(qici, short_qici, legacy_qici, legacy_short_qici, period_start_date, period_end_date)
)
,org_t as (
    select
        email_prefix,
        name,
        min(begin_time) as begin_time,
        max(end_time) as end_time
    from dw.dim_employee_chain
    where dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
      and path_name like '高途-H业务线-青橙项目部%'
    group by email_prefix, name
)
,order_attr as (
    select
        order_number,
        performance_employee_email_name,
        min(cast(coalesce(original_order_pay_success_timestamp, pay_success_timestamp, trade_timestamp) as timestamp)) as original_paid_time,
        max(cast(coalesce(transfer_in_amount, 0) as double) / 100.0) as service_transfer_in_amount_yuan,
        max(cast(coalesce(transfer_out_amount, 0) as double) / 100.0) as service_transfer_out_amount_yuan
    from service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf
    where dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
      and hour = format_datetime(now() - interval '2' hour, 'HH')
      and performance_second_level_department_name = '青橙项目部'
      and course_first_level_department_name in ('H业务线', 'LL业务线', 'TUTU', 'TT', 'A业务线', 'EM业务线', 'KA业务线', 'TT业务线', '创新中心')
and course_second_level_department_name in ('V项目部', '本地化部', '私域营销组', '青少成长学部', '创新技术组', '成长中心供应链组', 'APP运营组', '英语产品部', '职场服务部', '用户平台部', '微师产品部', '上海中心综合部', 'CAL技术组', '财务核算部', '财经项目部', '人才发展部', '财务信息化部', '图书项目部（关闭）', '运营部', '基础架构组', '数学产品部', '营销产品部', '雅思学部', '商品部', '磨课组', '升学规划部', '升学规划中心', '郑州中心', '组织部', '留学申请学部', '质检部', '架构平台部', '师训组', '投放商务组', '系统班部', '编程素养学部', '市场运营组', '项目运营组', 'KM技术组', '二讲老师部', '成都中心综合部', '业务设计部', '专题课部', '微师职教产品部', '高校学部', '教学服务部', '平台产品部', '数字化学部', '品牌运营组', '校长办公室', '运营中心财务', '视效部', '数据与商业分析中心', 'X项目', '教学产品部', 'XA学部', '语言学部', '图书产品部', '主播部', '业务支持部', 'HL技术组', '武汉中心综合部', '成人供应链组', '途途课堂', '信息平台部', 'HL经营分析组', '大数据部', '直播运营组', '市场部', '金刚产品部', '教学产品运营中心', '平台电商组', '企业效能部', '品牌与内容部', '产品研发部', '小学部', '技术质量部', '财务报告部', '税务部', '用户产品部', '直播二部', '招聘部', 'HR共享中心', '清北', '增长策略部', '督察部', '商品运营部', '资金管理部', '美好家庭学部', '设计支持中心', '初中部', 'AIGC创新部', '财务部', '人力资源部', '人才保障部一部', 'CAL经营分析组', '基础技术部', '综合素养学部', '热线呼入部', '品牌部', '语文产品部', '供应链部', '题库', 'GZ学部', '政府关系部', 'HRBP部', '招生运营部', '督检组', '耀师项目部', '产品运营部', '营运部', '多媒体技术部', '跟谁学郑州中心(失效）', '人工智能部', '体验设计部', '狮王项目部', '资产服务部', '专升本项目部', '基础技术部(失效)', '郑州中心综合部', '考研学部', '线上考研学部', '内容营销组', '公关部', '公职学部', '客服部', '运营平台部', 'CS学部', '财务FP&A部', '商学院学部', '行政部', '直播三部', '营销技术部', '私域运营组', '飞花产品部', '星火产品部', '客户端技术部', '薪酬绩效部', '图书项目部', 'NJ学部', '直播一部', '法务部', '在线服务部', '履约部', 'KML经营分析组', '社会保障部', '精品班部', '教学教研部', '医疗项目部', '菁英班部', '菁英班学部', '精品班学部', '一对一学部', '北京学部', '图书学部', '河南学部', '清北班学部', '湖广学部', '山西学部', 'K学部', 'M学部', '大学生学习学部', '合肥学校', '太原学校', '苏州学校', '郑州学校', '北京学校', '上海学校', '运营中心', '广州学校', '市场中心', '南京学校', '深圳学校', '成都学校', '财务中心', '武汉学校', '济南学校', '天津学校', '学校办公室', '重庆学校', '西安学校', '长沙学校', '市场二部', '留学学部', '国际考试学部', '出国语培线下项目', '广州学校（IE）', '国际竞赛项目', '剑桥英语项目', '上海学校（IE）', '心理学部', '创新项目部', '创新学部', '素质成长学部', '国际考试在线学部', '毛豆学部', '青少学部', '市场三部', '市场四部', '青橙项目部', '文旅学部', '本地化大班学部', '市场营销部', '直播市场部', '创新增长部', '学习规划中心', '素养初中学部', '素养青藤学部', '素养小学学部', '用户运营部', '经营策略部', '校园招聘', '直播创新部', '战略创新部', '产研部', '业务研发部', '教学质量部', 'Theta项目部', 'AI素养学部', '文旅项目', 'Theta智学项目部', 'Theta产研部', 'V学部', 'TT初中学部', 'TT小学学部', '产研部', 'T学部', '专题课部（失效）', '初中组', '文旅项目（失效）')
    group by order_number, performance_employee_email_name
)
,team_hist as (
    select distinct
        qici,
        employee_email_name
    from temp_table.dingxi01_qing_team_jg
)
-- 金额主表切换：service 负责收入/退款金额；finance 仅补交易类型识别，组织和退款链路继续沿用原逻辑
,service_base0 as (
    select
        s.order_number,
        s.clazz_name,
        cast(s.original_order_user_number as varchar) as user_id1,
        coalesce(s.pay_refund_type, '未知') as trade_status,
        case
            when coalesce(oa.service_transfer_in_amount_yuan, 0) > 0
              or coalesce(oa.service_transfer_out_amount_yuan, 0) > 0
            then '调课调班'
            else ''
        end as trade_type,
        cast(s.trade_timestamp as timestamp) as trade_time,
        s.performance_employee_email_prefix as email_prefix,
        s.performance_employee_email_name as name,
        s.grade_name as grade_list,
        case
            when coalesce(s.mapping_school_subject_name, s.school_subject_name) like '%英语%'
              or coalesce(s.mapping_school_subject_name, s.school_subject_name) like '%英文%' then '英语'
            when coalesce(s.mapping_school_subject_name, s.school_subject_name) like '%语文%' then '语文'
            when coalesce(s.mapping_school_subject_name, s.school_subject_name) like '%数学%' then '数学'
            when coalesce(s.mapping_school_subject_name, s.school_subject_name) like '%物理%' then '物理'
            when coalesce(s.mapping_school_subject_name, s.school_subject_name) like '%化学%' then '化学'
            when coalesce(s.mapping_school_subject_name, s.school_subject_name) like '%历史%' then '历史'
            when coalesce(s.mapping_school_subject_name, s.school_subject_name) like '%政治%' then '政治'
            when coalesce(s.mapping_school_subject_name, s.school_subject_name) like '%生物%' then '生物'
            when coalesce(s.mapping_school_subject_name, s.school_subject_name) like '%地理%' then '地理'
            when coalesce(s.mapping_school_subject_name, s.school_subject_name) like '%日语%' then '日语'
            else coalesce(s.mapping_school_subject_name, s.school_subject_name)
        end as subject,
        coalesce(
            trade_cal.qici,
            concat(
                date_format(
                    date_trunc('week', cast(s.trade_timestamp as timestamp) - interval '1' day) + interval '4' day,
                    '%Y%m%d'
                ),
                '期'
            )
        ) as qici,
        coalesce(s.school_term_name, cast(s.school_term_code as varchar)) as school_term_id,
        s.main_teacher_email_name as teacher_name,
        case
            when s.course_first_level_department_name is not null then s.course_first_level_department_name
            when s.grade_name like '%小学%' or s.grade_name like '%初%' then '小初业务线'
            else 'H业务线'
        end as course_first_level_department_name,
        case
            when s.course_second_level_department_name is not null then s.course_second_level_department_name
            when s.course_first_level_department_name = 'H业务线' then '精品班学部'
            when s.course_first_level_department_name is null
             and not (s.grade_name like '%小学%' or s.grade_name like '%初%') then '精品班学部'
            else s.course_second_level_department_name
        end as course_second_level_department_name,
        coalesce(cast(s.income_amount as double), 0.0) / 100.0 as income_amount_yuan,
        coalesce(cast(s.refund_amount as double), 0.0) / 100.0 as refund_amount_yuan,
        coalesce(oa.service_transfer_in_amount_yuan, 0) as service_transfer_in_amount_yuan,
        coalesce(oa.service_transfer_out_amount_yuan, 0) as service_transfer_out_amount_yuan,
        coalesce(
            oa.original_paid_time,
            cast(coalesce(s.original_order_pay_success_timestamp, s.pay_success_timestamp, s.trade_timestamp) as timestamp)
        ) as original_paid_time
    from service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf s
    left join order_attr oa
      on oa.order_number = s.order_number
     and oa.performance_employee_email_name = s.performance_employee_email_name
    left join biz_qici_calendar trade_cal
      on cast(s.trade_timestamp as date) between trade_cal.period_start_date and trade_cal.period_end_date
    where s.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
      and s.hour = format_datetime(now() - interval '2' hour, 'HH')
      and s.performance_first_level_department_name = 'H业务线'
      and s.performance_second_level_department_name = '青橙项目部'
      and s.course_first_level_department_name in (
          'H业务线', 'LL业务线', 'TUTU', 'TT', 'A业务线',
          'EM业务线', 'KA业务线', 'TT业务线', '创新中心'
      )
      and s.course_second_level_department_name in ('V项目部', '本地化部', '私域营销组', '青少成长学部', '创新技术组', '成长中心供应链组', 'APP运营组', '英语产品部', '职场服务部', '用户平台部', '微师产品部', '上海中心综合部', 'CAL技术组', '财务核算部', '财经项目部', '人才发展部', '财务信息化部', '图书项目部（关闭）', '运营部', '基础架构组', '数学产品部', '营销产品部', '雅思学部', '商品部', '磨课组', '升学规划部', '升学规划中心', '郑州中心', '组织部', '留学申请学部', '质检部', '架构平台部', '师训组', '投放商务组', '系统班部', '编程素养学部', '市场运营组', '项目运营组', 'KM技术组', '二讲老师部', '成都中心综合部', '业务设计部', '专题课部', '微师职教产品部', '高校学部', '教学服务部', '平台产品部', '数字化学部', '品牌运营组', '校长办公室', '运营中心财务', '视效部', '数据与商业分析中心', 'X项目', '教学产品部', 'XA学部', '语言学部', '图书产品部', '主播部', '业务支持部', 'HL技术组', '武汉中心综合部', '成人供应链组', '途途课堂', '信息平台部', 'HL经营分析组', '大数据部', '直播运营组', '市场部', '金刚产品部', '教学产品运营中心', '平台电商组', '企业效能部', '品牌与内容部', '产品研发部', '小学部', '技术质量部', '财务报告部', '税务部', '用户产品部', '直播二部', '招聘部', 'HR共享中心', '清北', '增长策略部', '督察部', '商品运营部', '资金管理部', '美好家庭学部', '设计支持中心', '初中部', 'AIGC创新部', '财务部', '人力资源部', '人才保障部一部', 'CAL经营分析组', '基础技术部', '综合素养学部', '热线呼入部', '品牌部', '语文产品部', '供应链部', '题库', 'GZ学部', '政府关系部', 'HRBP部', '招生运营部', '督检组', '耀师项目部', '产品运营部', '营运部', '多媒体技术部', '跟谁学郑州中心(失效）', '人工智能部', '体验设计部', '狮王项目部', '资产服务部', '专升本项目部', '基础技术部(失效)', '郑州中心综合部', '考研学部', '线上考研学部', '内容营销组', '公关部', '公职学部', '客服部', '运营平台部', 'CS学部', '财务FP&A部', '商学院学部', '行政部', '直播三部', '营销技术部', '私域运营组', '飞花产品部', '星火产品部', '客户端技术部', '薪酬绩效部', '图书项目部', 'NJ学部', '直播一部', '法务部', '在线服务部', '履约部', 'KML经营分析组', '社会保障部', '精品班部', '教学教研部', '医疗项目部', '菁英班部', '菁英班学部', '精品班学部', '一对一学部', '北京学部', '图书学部', '河南学部', '清北班学部', '湖广学部', '山西学部', 'K学部', 'M学部', '大学生学习学部', '合肥学校', '太原学校', '苏州学校', '郑州学校', '北京学校', '上海学校', '运营中心', '广州学校', '市场中心', '南京学校', '深圳学校', '成都学校', '财务中心', '武汉学校', '济南学校', '天津学校', '学校办公室', '重庆学校', '西安学校', '长沙学校', '市场二部', '留学学部', '国际考试学部', '出国语培线下项目', '广州学校（IE）', '国际竞赛项目', '剑桥英语项目', '上海学校（IE）', '心理学部', '创新项目部', '创新学部', '素质成长学部', '国际考试在线学部', '毛豆学部', '青少学部', '市场三部', '市场四部', '青橙项目部', '文旅学部', '本地化大班学部', '市场营销部', '直播市场部', '创新增长部', '学习规划中心', '素养初中学部', '素养青藤学部', '素养小学学部', '用户运营部', '经营策略部', '校园招聘', '直播创新部', '战略创新部', '产研部', '业务研发部', '教学质量部', 'Theta项目部', 'AI素养学部', '文旅项目', 'Theta智学项目部', 'Theta产研部', 'V学部', 'TT初中学部', 'TT小学学部', '产研部', 'T学部', '专题课部（失效）', '初中组', '文旅项目（失效）')
      and cast(s.trade_timestamp as date) >= date '2026-04-28'
      and coalesce(s.clazz_name, '') not like '%试听%'
)
,service_scope as (
    select a.*
    from service_base0 a
    left join team_hist th
      on th.employee_email_name = a.name
     and th.qici = a.qici
    where exists (
        select 1
        from org_t ot
        where ot.name = a.name
          and a.original_paid_time >= cast(ot.begin_time as timestamp)
          and (ot.end_time is null or a.original_paid_time <= cast(ot.end_time as timestamp))
    )
    or th.employee_email_name is not null
)

,course_transfer_finance_raw as (
    select
        f.id,
        f.order_number,
        cast(f.user_id as varchar) as target_user_number,
        f.email_prefix,
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
        end as subject,
        f.course_first_level_department_name,
        f.course_second_level_department_name,
        case f.course_term_id
            when 'C' then '春季'
            when 'X' then '夏季'
            when 'Q' then '秋季'
            when 'D' then '冬季'
            else '其他'
        end as school_term_id,
        f.teacher_name,
        cast(coalesce(f.price, 0) as double) as income_amount_yuan,
        row_number() over (
            partition by
                f.order_number,
                f.clazz_name,
                f.user_id,
                f.trade_status,
                f.trade_type,
                f.trade_time,
                f.email_prefix,
                f.employee_email_name,
                f.course_grade,
                f.course_subject,
                f.course_term_id,
                f.teacher_name,
                f.course_first_level_department_name,
                f.course_second_level_department_name
            order by f.id
        ) as rn
    from finance_dw.app_finance_performance_extend_details_hf f
    where f.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
      and f.hour = format_datetime(now() - interval '2' hour, 'HH')
      and f.employee_first_level_department_name = 'H业务线'
      and f.employee_second_level_department_name = '青橙项目部'
      and f.course_first_level_department_name in (
          'H业务线', 'LL业务线', 'TUTU', 'TT', 'A业务线',
          'EM业务线', 'KA业务线', 'TT业务线', '创新中心'
      )
      and f.course_second_level_department_name in ('V项目部', '本地化部', '私域营销组', '青少成长学部', '创新技术组', '成长中心供应链组', 'APP运营组', '英语产品部', '职场服务部', '用户平台部', '微师产品部', '上海中心综合部', 'CAL技术组', '财务核算部', '财经项目部', '人才发展部', '财务信息化部', '图书项目部（关闭）', '运营部', '基础架构组', '数学产品部', '营销产品部', '雅思学部', '商品部', '磨课组', '升学规划部', '升学规划中心', '郑州中心', '组织部', '留学申请学部', '质检部', '架构平台部', '师训组', '投放商务组', '系统班部', '编程素养学部', '市场运营组', '项目运营组', 'KM技术组', '二讲老师部', '成都中心综合部', '业务设计部', '专题课部', '微师职教产品部', '高校学部', '教学服务部', '平台产品部', '数字化学部', '品牌运营组', '校长办公室', '运营中心财务', '视效部', '数据与商业分析中心', 'X项目', '教学产品部', 'XA学部', '语言学部', '图书产品部', '主播部', '业务支持部', 'HL技术组', '武汉中心综合部', '成人供应链组', '途途课堂', '信息平台部', 'HL经营分析组', '大数据部', '直播运营组', '市场部', '金刚产品部', '教学产品运营中心', '平台电商组', '企业效能部', '品牌与内容部', '产品研发部', '小学部', '技术质量部', '财务报告部', '税务部', '用户产品部', '直播二部', '招聘部', 'HR共享中心', '清北', '增长策略部', '督察部', '商品运营部', '资金管理部', '美好家庭学部', '设计支持中心', '初中部', 'AIGC创新部', '财务部', '人力资源部', '人才保障部一部', 'CAL经营分析组', '基础技术部', '综合素养学部', '热线呼入部', '品牌部', '语文产品部', '供应链部', '题库', 'GZ学部', '政府关系部', 'HRBP部', '招生运营部', '督检组', '耀师项目部', '产品运营部', '营运部', '多媒体技术部', '跟谁学郑州中心(失效）', '人工智能部', '体验设计部', '狮王项目部', '资产服务部', '专升本项目部', '基础技术部(失效)', '郑州中心综合部', '考研学部', '线上考研学部', '内容营销组', '公关部', '公职学部', '客服部', '运营平台部', 'CS学部', '财务FP&A部', '商学院学部', '行政部', '直播三部', '营销技术部', '私域运营组', '飞花产品部', '星火产品部', '客户端技术部', '薪酬绩效部', '图书项目部', 'NJ学部', '直播一部', '法务部', '在线服务部', '履约部', 'KML经营分析组', '社会保障部', '精品班部', '教学教研部', '医疗项目部', '菁英班部', '菁英班学部', '精品班学部', '一对一学部', '北京学部', '图书学部', '河南学部', '清北班学部', '湖广学部', '山西学部', 'K学部', 'M学部', '大学生学习学部', '合肥学校', '太原学校', '苏州学校', '郑州学校', '北京学校', '上海学校', '运营中心', '广州学校', '市场中心', '南京学校', '深圳学校', '成都学校', '财务中心', '武汉学校', '济南学校', '天津学校', '学校办公室', '重庆学校', '西安学校', '长沙学校', '市场二部', '留学学部', '国际考试学部', '出国语培线下项目', '广州学校（IE）', '国际竞赛项目', '剑桥英语项目', '上海学校（IE）', '心理学部', '创新项目部', '创新学部', '素质成长学部', '国际考试在线学部', '毛豆学部', '青少学部', '市场三部', '市场四部', '青橙项目部', '文旅学部', '本地化大班学部', '市场营销部', '直播市场部', '创新增长部', '学习规划中心', '素养初中学部', '素养青藤学部', '素养小学学部', '用户运营部', '经营策略部', '校园招聘', '直播创新部', '战略创新部', '产研部', '业务研发部', '教学质量部', 'Theta项目部', 'AI素养学部', '文旅项目', 'Theta智学项目部', 'Theta产研部', 'V学部', 'TT初中学部', 'TT小学学部', '产研部', 'T学部', '专题课部（失效）', '初中组', '文旅项目（失效）')
      and cast(f.trade_time as date) >= date '2026-07-20'
      and f.trade_type = '调课调班'
      and f.trade_status like '%支付%'
      and f.price > 0
      and exists (
          select 1
          from finance_dw.dim_finance_order_change_df o
          where o.dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
            and o.latest_child_order_number = f.order_number
            and o.latest_child_order_status in (2, 6, 7)
            and o.biz_type in (2, 7)
            and o.order_change_type = 1
      )
)
,course_transfer_finance as (
    select
        order_number,
        target_user_number,
        max(email_prefix) as email_prefix,
        employee_email_name,
        min(trade_time) as trade_time,
        max(clazz_name) as clazz_name,
        max(course_grade) as course_grade,
        subject,
        max(course_first_level_department_name) as course_first_level_department_name,
        max(course_second_level_department_name) as course_second_level_department_name,
        max(school_term_id) as school_term_id,
        max(teacher_name) as teacher_name,
        sum(income_amount_yuan) as income_amount_yuan
    from course_transfer_finance_raw
    where rn = 1
    group by order_number, target_user_number, employee_email_name, subject
)
,course_transfer_scope as (
    select
        f.order_number,
        f.clazz_name,
        f.target_user_number as user_id1,
        '支付' as trade_status,
        '' as trade_type,
        f.trade_time,
        f.email_prefix,
        f.employee_email_name as name,
        f.course_grade as grade_list,
        f.subject,
        coalesce(
            trade_cal.qici,
            concat(
                date_format(
                    date_trunc('week', f.trade_time - interval '1' day) + interval '4' day,
                    '%Y%m%d'
                ),
                '期'
            )
        ) as qici,
        f.school_term_id,
        f.teacher_name,
        case
            when f.course_first_level_department_name is not null then f.course_first_level_department_name
            when f.course_grade like '%小学%' or f.course_grade like '%初%' then '小初业务线'
            else 'H业务线'
        end as course_first_level_department_name,
        case
            when f.course_second_level_department_name is not null then f.course_second_level_department_name
            when f.course_first_level_department_name = 'H业务线' then '精品班学部'
            when f.course_first_level_department_name is null
             and not (f.course_grade like '%小学%' or f.course_grade like '%初%') then '精品班学部'
            else f.course_second_level_department_name
        end as course_second_level_department_name,
        f.income_amount_yuan,
        cast(0 as double) as refund_amount_yuan,
        cast(0 as double) as service_transfer_in_amount_yuan,
        cast(0 as double) as service_transfer_out_amount_yuan
    from course_transfer_finance f
    left join biz_qici_calendar trade_cal
      on cast(f.trade_time as date) between trade_cal.period_start_date and trade_cal.period_end_date
    where exists (
          select 1
          from service_dw.dwd_crm_assign_private_detail_hf p
          where cast(p.user_number as varchar) = f.target_user_number
            and p.employee_email_name = f.employee_email_name
            and p.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
            and p.hour = format_datetime(now() - interval '2' hour, 'HH')
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
      and coalesce(
          trade_cal.qici,
          concat(
              date_format(
                  date_trunc('week', f.trade_time - interval '1' day) + interval '4' day,
                  '%Y%m%d'
              ),
              '期'
          )
      ) > '20260424期'
      and not exists (
          select 1
          from service_scope s
          where s.order_number = f.order_number
            and s.name = f.employee_email_name
            and s.user_id1 = f.target_user_number
      )
)
,rd as (
    select
        order_number,
        clazz_name,
        user_id1,
        trade_status,
        trade_type,
        trade_time,
        email_prefix,
        name,
        grade_list,
        subject,
        qici,
        school_term_id,
        teacher_name,
        course_first_level_department_name,
        course_second_level_department_name,
        income_amount_yuan,
        refund_amount_yuan,
        service_transfer_in_amount_yuan,
        service_transfer_out_amount_yuan,
        'service' as source_type
    from service_scope
    where qici > '20260424期'

    union all

    select
        order_number,
        clazz_name,
        user_id1,
        trade_status,
        trade_type,
        trade_time,
        email_prefix,
        name,
        grade_list,
        subject,
        qici,
        school_term_id,
        teacher_name,
        course_first_level_department_name,
        course_second_level_department_name,
        income_amount_yuan,
        refund_amount_yuan,
        service_transfer_in_amount_yuan,
        service_transfer_out_amount_yuan,
        'course_transfer_supplement' as source_type
    from course_transfer_scope
    where qici > '20260424期'
)
-----------------退费行课节数
,ord as (
    select
        order_number,
        coalesce(
            refund_cal.qici,
            concat(
                date_format(
                    date_trunc('week', cast(full_refund_timestamp as timestamp) - interval '1' day) + interval '4' day,
                    '%Y%m%d'
                ),
                '期'
            )
        ) as qici_re,
        full_refund_chain_finish_lesson_count
    from finance_dw.dm_finance_order_refund_detail_df
    left join biz_qici_calendar refund_cal
      on cast(cast(full_refund_timestamp as timestamp) as date) between refund_cal.period_start_date and refund_cal.period_end_date
    where dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
      and cast(full_refund_timestamp as date) >= date '2026-04-28'
      and course_first_level_department_name = 'H业务线'
      and course_second_level_department_name in ('精品班学部', '菁英班学部', '一对一学部')
      and is_full_refund_order = 1
      and total_refund_amount is not null
      and total_refund_amount <> 0
)

--------------调课调班/课程转移主链路
,order_change_raw as (
    select
        order_number,
        parent_order_number,
        original_order_number,
        latest_child_order_number,
        cast(coalesce(transfer_in_amount, 0) as double) / 100.0 as transfer_in_amount_yuan,
        cast(coalesce(transfer_out_amount, 0) as double) / 100.0 as transfer_out_amount_yuan
    from finance_dw.dim_finance_order_change_df
    where dt = format_datetime(now() - interval '24' hour, 'YYYYMMdd')
      and latest_child_order_status in (2, 6, 7)
      and biz_type in (2, 7)
)

,order_change_order_map as (
    select
        u.join_order_number,
        r.transfer_in_amount_yuan,
        r.transfer_out_amount_yuan
    from order_change_raw r
    cross join unnest(array[
        r.order_number,
        r.parent_order_number,
        r.original_order_number,
        r.latest_child_order_number
    ]) as u(join_order_number)
    where u.join_order_number is not null
)

,order_change as (
    select
        join_order_number as order_number,
        1 as has_order_change,
        max(transfer_in_amount_yuan) as transfer_in_amount_yuan,
        max(transfer_out_amount_yuan) as transfer_out_amount_yuan
    from order_change_order_map
    group by join_order_number
)

---------------合并退费行课节数
,re_ke as (
    select
        qici_re,
        order_number,
        max(full_refund_chain_finish_lesson_count) as full_refund_chain_finish_lesson_count
    from ord
    group by qici_re, order_number
)

------------------------连接各订单退费行课节数和主交易调课调班链路
,t4 as (
    select
        rd.*,
        coalesce(re_ke.full_refund_chain_finish_lesson_count, 0) as re_lc,
        case
            -- 只剔除调课调班流水本身；命中课程转移链路的正常订单仍然保留绩效。
            -- service 订单明细侧有 transfer_in/transfer_out 但 dim_finance_order_change_df 漏链路时，也按内部调课调班剔除。
            when coalesce(rd.service_transfer_in_amount_yuan, 0) > 0
              or coalesce(rd.service_transfer_out_amount_yuan, 0) > 0
            then 1
            when rd.trade_type = '调课调班'
             and (
                    (
                        coalesce(order_change.has_order_change, 0) = 1
                        and (
                            coalesce(order_change.transfer_in_amount_yuan, 0) > 0
                            or coalesce(order_change.transfer_out_amount_yuan, 0) > 0
                        )
                    )
                    or coalesce(rd.refund_amount_yuan, 0) > 0
                 )
            then 1
            else 0
        end as is_internal_order_change
    from rd
    left join re_ke
        on re_ke.qici_re = rd.qici
       and re_ke.order_number = rd.order_number
    left join order_change
        on rd.order_number = order_change.order_number
)

--------------------
,rd_0 as (
    select
        qici,
        course_first_level_department_name,
        course_second_level_department_name,
        name,
        user_id1,
        case
            when trade_status like '%退款%' then '退款'
            when trade_status like '%支付%' then '支付'
            else '未知'
        end as trade_status,
        grade_list,
        sum(
            case
                when is_internal_order_change = 1
                then 0
                when income_amount_yuan >= 0 then income_amount_yuan
                else 0
            end
        ) as income,
        sum(case when source_type = 'service' then income_amount_yuan else 0 end) as income_all,
        sum(
            case
                when is_internal_order_change = 1
                then 0
                when course_second_level_department_name = '一对一学部'
                 and course_first_level_department_name = 'H业务线'
                then case when refund_amount_yuan > 0 then refund_amount_yuan else 0 end
                else case
                    when clazz_name like '%点睛%' and refund_amount_yuan > 0 and re_lc < 2 then refund_amount_yuan
                    when (clazz_name not like '%点睛%' or clazz_name is null) and refund_amount_yuan > 0 and re_lc < 4 then refund_amount_yuan
                    else 0
                end
            end
        ) as refund_4,
        sum(
            case
                when is_internal_order_change = 1
                then 0
                when refund_amount_yuan > 0 then refund_amount_yuan
                else 0
            end
        ) as refund,
        sum(case when source_type = 'service' then refund_amount_yuan else 0 end) as refund_all,
        count(distinct case
            when is_internal_order_change = 1
            then null
            when subject not in ('选科志愿', '定制方案') and income_amount_yuan > 0 then subject
        end) as p_sub,
        count(distinct case
            when is_internal_order_change = 1
            then null
            when subject not in ('选科志愿', '定制方案') and refund_amount_yuan > 0 then subject
        end) as r_sub
    from t4
    group by
        qici,
        course_first_level_department_name,
        course_second_level_department_name,
        name,
        user_id1,
        case
            when trade_status like '%退款%' then '退款'
            when trade_status like '%支付%' then '支付'
            else '未知'
        end,
        grade_list
)
------------
,wa as (
    select
        qici,
        course_first_level_department_name,
        course_second_level_department_name,
        name,
        user_id1,
        trade_status,
        grade_list,
        income,
        income_all,
        refund_4,
	    refund,
        refund_all,
        (income - refund_4) as promit_4,
        (income - refund) as promit,
        p_sub as jing_sub
    from rd_0
)
-- 聚合人维度
,renchan as (
    select
        qtg.qici,
        qm.moth,
        qtg.employee_email_name,
        qtg.leader_employee_email_name,
        qtg.dazu,
        qtg.jingli,
        qtg.xuebu,
        sum(case when course_first_level_department_name = 'H业务线' then promit else 0 end) as H_promit,
        sum(case when course_first_level_department_name = 'H业务线' then 0 else promit end) as n_H_promit,
        sum(income) as income,
        sum(refund) as refund,
        sum(promit) as promit,
        sum(income_all) as income_all,
        sum(refund_all) as refund_all,
        count(distinct case when refund > 500 then user_id1 end) as re_payer,
        sum(case when course_first_level_department_name = 'H业务线' and course_second_level_department_name = '一对一学部' then promit_4 else 0 end) as Y_promit_4,
        sum(case when course_first_level_department_name = 'H业务线' and course_second_level_department_name = '一对一学部' then income else 0 end) as Y_income_4,
        sum(case when course_first_level_department_name = 'H业务线' and course_second_level_department_name = '一对一学部' then refund_4 else 0 end) as Y_refund_4,
        sum(case when course_first_level_department_name = 'H业务线' then promit_4 else 0 end) as H_promit_4,
        sum(case when course_first_level_department_name = 'H业务线' then income else 0 end) as H_income_4,
        sum(case when course_first_level_department_name = 'H业务线' then refund_4 else 0 end) as H_refund_4,
        sum(case when course_first_level_department_name = 'H业务线' and course_second_level_department_name = '一对一学部' then 0 else refund_4 end) as class_refund_4,
        sum(case when course_first_level_department_name = 'H业务线' then 0 else promit_4 end) as n_H_promit_4,
        count(distinct case when refund_4 > 0 then user_id1 end) as re_payer_4,
        count(distinct case when promit > 0 then user_id1 end) as in_payer_4,
        sum(jing_sub) as j_sub
    from (
        select qici, employee_email_name, leader_employee_email_name, dazu, jingli, xuebu,
            row_number() over (partition by qici, employee_email_name order by leader_employee_email_name) as rn
        from temp_table.dingxi01_qing_team_jg
        where leader_employee_email_name is not null
    ) qtg
    left join wa
        on qtg.employee_email_name = wa.name
       and qtg.qici = wa.qici
    left join temp_table.dingxi01_qing_qi_moth qm
        on qm.qici = qtg.qici
    where qtg.rn = 1
    group by
        qtg.qici,
        qm.moth,
        qtg.employee_email_name,
        qtg.leader_employee_email_name,
        qtg.dazu,
        qtg.jingli,
        qtg.xuebu
)
-- 目标字段
,goal_qici as (
    select
        name as employee_email_name,
        qici,
        max(cast(goal as decimal(18, 2))) as qici_goal
    from temp_table.dingxi01_qing_goal
    group by name, qici
)
,goal_moth as (
    select
        month as moth,
        name as employee_email_name,
        sum(cast(goal as decimal(18, 2))) as moth_goal
    from temp_table.dingxi01_qing_goal
    group by month, name
)
,final_base as (
    select
        r.qici,
        r.moth,
        r.employee_email_name as name,
        r.leader_employee_email_name,
        r.dazu,
        r.jingli,
        r.xuebu,
        max(gq.qici_goal) as qici_goal,
        max(gm.moth_goal) as moth_goal,
        coalesce(sum(r.H_promit), 0) as H_promit,
        coalesce(sum(r.n_H_promit), 0) as n_H_promit,
        coalesce(sum(r.income), 0) as income,
        coalesce(sum(r.refund), 0) as refund,
        coalesce(sum(r.promit), 0) as promit,
        coalesce(sum(r.income_all), 0) as income_all,
        coalesce(sum(r.refund_all), 0) as refund_all,
        coalesce(sum(r.re_payer), 0) as re_payer,
        coalesce(sum(r.in_payer_4), 0) as in_payer_4,
        coalesce(sum(r.j_sub), 0) as j_sub,
        count(distinct case when r.promit > 0 then r.employee_email_name end) as podan,
        coalesce(sum(r.Y_promit_4), 0) as Y_promit_4,
        coalesce(sum(r.H_promit_4), 0) as H_promit_4,
        coalesce(sum(r.Y_income_4), 0) as Y_income_4,
        coalesce(sum(r.H_income_4), 0) as H_income_4,
        coalesce(sum(r.Y_refund_4), 0) as Y_refund_4,
        coalesce(sum(r.H_refund_4), 0) as H_refund_4,
        coalesce(sum(r.n_H_promit_4), 0) as n_H_promit_4,
        coalesce(sum(r.re_payer_4), 0) as re_payer_4,
        coalesce(sum(r.class_refund_4), 0) as class_refund_4
    from renchan r
    left join goal_qici gq
        on gq.qici = r.qici
       and gq.employee_email_name = r.employee_email_name
    left join goal_moth gm
        on gm.moth = r.moth
       and gm.employee_email_name = r.employee_email_name
    group by
        r.qici,
        r.moth,
        r.employee_email_name,
        r.leader_employee_email_name,
        r.dazu,
        r.jingli,
        r.xuebu
)
-- 团队期粒度输出。
-- 收入/退款新增 income_all/refund_all，但折算仍使用原退4/点睛2字段。
select
    qg.qici,
    qg.xuebu,
    qg.xiaozu as xiaozu1,
    qg.dazu,
    cast(qg.emye_c as decimal) as emye_c,
    cast(qg.goal as decimal) as goal,
    coalesce(sum(r.H_promit), 0) as H_promit,
    coalesce(sum(r.n_H_promit), 0) as n_H_promit,
    coalesce(sum(r.income), 0) as income,
    coalesce(sum(r.refund), 0) as refund,
    coalesce(sum(r.promit), 0) as promit,
    coalesce(sum(r.income_all), 0) as income_all,
    coalesce(sum(r.refund_all), 0) as refund_all,
    coalesce(sum(r.re_payer), 0) as re_payer,
    count(distinct case when r.promit > 0 then r.name end) as podan,
    coalesce(sum(r.Y_promit_4), 0) as Y_promit_4,
    coalesce(sum(r.Y_income_4), 0) as Y_income_4,
    coalesce(sum(r.H_promit_4), 0) as H_promit_4,
    coalesce(sum(r.n_H_promit_4), 0) as n_H_promit_4,
    coalesce(sum(r.Y_refund_4), 0) + coalesce(sum(r.class_refund_4), 0) as refund_4,
    coalesce(sum(r.class_refund_4), 0) as class_refund_4,
    coalesce(sum(r.H_promit_4), 0) + coalesce(sum(r.n_H_promit_4), 0) as promit_4,
    coalesce(sum(r.re_payer_4), 0) as re_payer_4,
    count(distinct case when coalesce(r.H_promit_4, 0) + coalesce(r.n_H_promit_4, 0) > 0 then r.name end) as podan_4,
    case when qg.xiaozu != '-' then qg.xiaozu else '-' end as xiaozu
from temp_table.dingxi01_qing_team_g_qi qg
left join final_base r
  on r.qici = qg.qici
 and r.leader_employee_email_name = qg.xiaozu
group by qg.qici, qg.xuebu, qg.xiaozu, qg.dazu, qg.emye_c, qg.goal
