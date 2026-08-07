-- 2026-07-16 update: map summer business dates 2026-07-14..2026-08-12 to actual operation qici ranges.
-- Dataset: 2424 daily conversion table
with dd as (
    select *
    from (
        select
            id,
            order_number,
            substring(biz_number, 1, 10) as sub_biz_number,
            pre_biz_number,
            clazz_name,
            user_id as user_id1,
            pre_employee_id,
            type,
            trade_status,
            trade_type,
            order_paid_time as paid_time,
            trade_time,
            case
                when trade_status in ('全部退款', '部分退款') then -real_price
                else real_price
            end as real_price_0,
            transfer_price,
            price,
            email_prefix,
            employee_email_name as name,
            talent_type_name,
            city_name as city,
            department,
            biz_number,
            course_grade as grade_list,
            course_subject as subject,
            case day_of_week(cast(substr(trade_time, 1, 10) as date))
                when 1 then '周1'
                when 2 then '周2'
                when 3 then '周3'
                when 4 then '周4'
                when 5 then '周5'
                when 6 then '周6'
                when 7 then '周7'
            end as weekday_name,
            case
                when substr(trade_time, 1, 10) >= '2026-07-14' and substr(trade_time, 1, 10) <= '2026-07-19' then '20260716期'
                when substr(trade_time, 1, 10) >= '2026-07-20' and substr(trade_time, 1, 10) <= '2026-07-25' then '20260722期'
                when substr(trade_time, 1, 10) >= '2026-07-26' and substr(trade_time, 1, 10) <= '2026-07-31' then '20260728期'
                when substr(trade_time, 1, 10) >= '2026-08-01' and substr(trade_time, 1, 10) <= '2026-08-06' then '20260803期'
                when substr(trade_time, 1, 10) >= '2026-08-07' and substr(trade_time, 1, 10) <= '2026-08-12' then '20260808期'
                when substr(trade_time, 1, 10) >= '2026-02-25' and substr(trade_time, 1, 10) <= '2026-03-02' then '20260227期'
                when substr(trade_time, 1, 10) >= '2026-02-17' and substr(trade_time, 1, 10) <= '2026-02-24' then '20260220期'
                when substr(trade_time, 1, 10) >= '2026-02-09' and substr(trade_time, 1, 10) <= '2026-02-16' then '20260213期'
                when substr(trade_time, 1, 10) >= '2026-02-03' and substr(trade_time, 1, 10) <= '2026-02-08' then '20260206期'
                when substr(trade_time, 1, 10) >= '2026-01-27' and substr(trade_time, 1, 10) <= '2026-02-02' then '20260130期'
                when substr(trade_time, 1, 10) >= '2026-01-20' and substr(trade_time, 1, 10) <= '2026-01-26' then '20260123期'
                else concat(
                    date_format(
                        date_trunc('week', cast(trade_time as timestamp) - interval '1' day) + interval '4' day,
                        '%Y%m%d'
                    ),
                    '期'
                )
            end as qici,
            leader_employee_email_name,
            teacher_name,
            case course_term_id
                when 'C' then '春季'
                when 'X' then '夏季'
                when 'Q' then '秋季'
                when 'D' then '冬季'
                else '其他'
            end as school_term_id,
            note,
            course_first_level_department_name,
            course_second_level_department_name,
            course_top_level_department_name
        from finance_dw.app_finance_performance_extend_details_hf
        where dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
          and hour = format_datetime(now() - interval '3' hour, 'HH')
          and employee_first_level_department_name = 'H业务线'
          and employee_second_level_department_name = '市场部'
          and employee_third_level_department_name = '市场顾问部'
    )
    where qici > '20260424期'
),
gmv_t as (
    select
        id,
        order_number,
        clazz_name,
        user_id1,
        trade_status,
        trade_time,
        weekday_name,
        trade_type,
        email_prefix,
        name,
        grade_list,
        subject,
        qici,
        school_term_id,
        teacher_name,
        course_first_level_department_name,
        course_second_level_department_name,
        name_total_price
    from (
        select
            *,
            row_number() over (partition by name, user_id1 order by id) as dup_rn
        from (
            select
                *,
                round(sum(price) over (partition by name, user_id1), 3) as name_total_price
            from dd
            where trade_type = '调课调班'
        ) t1
        where name_total_price != 0
    ) t2
    where dup_rn = 1
),
gmv_z as (
    select
        id,
        order_number,
        clazz_name,
        user_id1,
        trade_status,
        trade_time,
        weekday_name,
        trade_type,
        email_prefix,
        name,
        grade_list,
        subject,
        qici,
        school_term_id,
        teacher_name,
        course_first_level_department_name,
        course_second_level_department_name,
        sum(price) as name_total_price
    from dd
    where trade_type = '正常订单'
    group by
        id,
        order_number,
        clazz_name,
        user_id1,
        trade_status,
        trade_time,
        weekday_name,
        trade_type,
        email_prefix,
        name,
        grade_list,
        subject,
        qici,
        school_term_id,
        teacher_name,
        course_first_level_department_name,
        course_second_level_department_name
),
rd as (
    select
        id,
        order_number,
        clazz_name,
        user_id1,
        trade_status,
        trade_time,
        weekday_name,
        trade_type,
        email_prefix,
        name,
        grade_list,
        subject,
        qici,
        school_term_id,
        teacher_name,
        course_first_level_department_name,
        course_second_level_department_name,
        name_total_price
    from gmv_z

    union all

    select
        id,
        order_number,
        clazz_name,
        user_id1,
        trade_status,
        trade_time,
        weekday_name,
        trade_type,
        email_prefix,
        name,
        grade_list,
        subject,
        qici,
        school_term_id,
        teacher_name,
        course_first_level_department_name,
        course_second_level_department_name,
        name_total_price
    from gmv_t
),
n_uid as (
    select
        aa.*,
        row_number() over (partition by original_order_user_number order by qici desc) as rn
    from (
        select
            lead_id,
            original_order_user_number,
            performance_employee_email_name,
            case
                when cast(date_parse(replace(concat(trade_group_period_year, trade_group_period_term), '期', ''), '%Y%m%d') as date) between date '2026-07-14' and date '2026-07-19' then '20260716期'
                when cast(date_parse(replace(concat(trade_group_period_year, trade_group_period_term), '期', ''), '%Y%m%d') as date) between date '2026-07-20' and date '2026-07-25' then '20260722期'
                when cast(date_parse(replace(concat(trade_group_period_year, trade_group_period_term), '期', ''), '%Y%m%d') as date) between date '2026-07-26' and date '2026-07-31' then '20260728期'
                when cast(date_parse(replace(concat(trade_group_period_year, trade_group_period_term), '期', ''), '%Y%m%d') as date) between date '2026-08-01' and date '2026-08-06' then '20260803期'
                when cast(date_parse(replace(concat(trade_group_period_year, trade_group_period_term), '期', ''), '%Y%m%d') as date) between date '2026-08-07' and date '2026-08-12' then '20260808期'
                else concat(
                date_format(
                    date_trunc(
                        'week',
                        date_parse(replace(concat(trade_group_period_year, trade_group_period_term), '期', ''), '%Y%m%d') - interval '1' day
                    ) + interval '4' day,
                    '%Y%m%d'
                ),
                '期'
            )
            end as qici
        from service_dw.dws_crm_order_lead_attribute_income_refund_stats_detail_hf
        where dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
          and hour = format_datetime(now() - interval '3' hour, 'HH')
          and course_first_level_department_name in ('H业务线','A业务线','EM业务线','LL业务线','TT','TUTU','TT业务线')
          and course_second_level_department_name in ('V项目部','本地化部','私域营销组','青少成长学部','创新技术组','成长中心供应链组','APP运营组','英语产品部','职场服务部','用户平台部','微师产品部','上海中心综合部','CAL技术组','财务核算部','财经项目部','人才发展部','财务信息化部','图书项目部（关闭）','运营部','基础架构组','数学产品部','营销产品部','雅思学部','商品部','磨课组','升学规划部','郑州中心','组织部','留学申请学部','质检部','架构平台部','师训组','投放商务组','系统班部','编程素养学部','市场运营组','项目运营组','KM技术组','二讲老师部','成都中心综合部','业务设计部','专题课部','微师职教产品部','高校学部','教学服务部','平台产品部','数字化学部','品牌运营组','校长办公室','运营中心财务','视效部','数据与商业分析中心','X项目','教学产品部','XA学部','语言学部','图书产品部','主播部','业务支持部','HL技术组','武汉中心综合部','成人供应链组','途途课堂','信息平台部','HL经营分析组','大数据部','直播运营组','市场部','金刚产品部','教学产品运营中心','平台电商组','企业效能部','品牌与内容部','产品研发部','小学部','技术质量部','财务报告部','税务部','用户产品部','直播二部','招聘部','HR共享中心','清北','增长策略部','督察部','商品运营部','资金管理部','美好家庭学部','设计支持中心','初中部','AIGC创新部','财务部','人力资源部','人才保障部一部','CAL经营分析组','基础技术部','综合素养学部','热线呼入部','品牌部','语文产品部','供应链部','题库','GZ学部','政府关系部','HRBP部','招生运营部','督检组','耀师项目部','产品运营部','营运部','多媒体技术部','跟谁学郑州中心(失效）','人工智能部','体验设计部','狮王项目部','资产服务部','专升本项目部','基础技术部(失效)','郑州中心综合部','考研学部','内容营销组','公关部','公职学部','客服部','运营平台部','CS学部','财务FP&A部','商学院学部','行政部','直播三部','营销技术部','私域运营组','飞花产品部','星火产品部','客户端技术部','薪酬绩效部','图书项目部','NJ学部','直播一部','法务部','在线服务部','履约部','KML经营分析组','社会保障部','精品班部','教学教研部','医疗项目部','菁英班部','菁英班学部','精品班学部','一对一学部','北京学部','图书学部','河南学部','清北班学部','湖广学部','山西学部','K学部','M学部','大学生学习学部','合肥学校','太原学校','苏州学校','郑州学校','北京学校','上海学校','运营中心','广州学校','市场中心','南京学校','深圳学校','成都学校','财务中心','武汉学校','济南学校','天津学校','学校办公室','重庆学校','西安学校','长沙学校','市场二部','留学学部','国际考试学部','出国语培线下项目','广州学校（IE）','国际竞赛项目','剑桥英语项目','上海学校（IE）','心理学部','创新项目部','素质成长学部','国际考试在线学部','毛豆学部','青少学部','市场三部','市场四部','青橙项目部','文旅学部','本地化大班学部','市场营销部','直播市场部','创新增长部','学习规划中心','素养初中学部','素养青藤学部','素养小学学部','用户运营部','经营策略部','校园招聘','直播创新部','战略创新部','产研部','业务研发部','教学质量部','Theta项目部','AI素养学部','文旅项目','Theta智学项目部','Theta产研部','V学部','TT初中学部','TT小学学部','产研部','T学部','专题课部（失效）','初中组','文旅项目（失效）')
          and performance_third_level_department_name = '市场顾问部'
    ) aa
),
lead_gmv as (
    select
        rd.*,
        n_uid.lead_id
    from rd
    left join n_uid
      on rd.user_id1 = n_uid.original_order_user_number
     and rd.name = n_uid.performance_employee_email_name
    where n_uid.rn = 1
),
rule as (
    select
        lead_gmv.*,
        rr.rule_name,
        case
            when rr.rule_name like '%北京直播江苏%' then '北京直播江苏'
            when rr.rule_name like '%koc测试5元%' then 'koc测试5元'
            when rr.rule_name like '%百度搜索%' then '百度搜索'
            when rr.rule_name like '%孟亚飞ip0元B站%' or rr.rule_name like '%B站孟亚飞%' then 'B站孟亚飞'
            when rr.rule_name like '%孟亚飞常规99元%' then '孟亚飞常规99元'
            when rr.rule_name like '%亚飞9元百度%' then '亚飞9元百度'
            when rr.rule_name like '%tmk3元周帅%' then 'tmk3元周帅'
            when rr.rule_name like '%tmk9元沈阳%' then 'tmk9元沈阳'
            when rr.rule_name like '%tmk9元启师%' then 'tmk9元启师'
            when rr.rule_name like '%tmk9元伍仟里%' then 'tmk9元伍仟里'
            when rr.rule_name like '%抖音私域%' or rr.rule_name like '%抖音私信%' then '抖音私信'
            when rr.rule_name like '%曹忆ip99元福建%' then '曹忆ip99元福建'
            when rr.rule_name like '%曹忆ip99元江苏%' then '曹忆ip99元江苏'
            when rr.rule_name like '%孟亚飞ip9元福建%' then '孟亚飞ip9元福建'
            when rr.rule_name like '%孟亚飞ip9元江苏%' then '孟亚飞ip9元江苏'
            when rr.rule_name like '%孟亚飞ip9元河南%' then '孟亚飞ip9元河南'
            when rr.rule_name like '%孟亚飞ip9元河北%' then '孟亚飞ip9元河北'
            when rr.rule_name like '%周帅ip9元%' then '周帅ip9元'
            when rr.rule_name like '%朱汉祺ip9元%' then '朱汉祺ip9元'
            when rr.rule_name like '%曹忆ip99元%' then '曹忆IP99元'
            when rr.rule_name like '%APP%' then 'APP'
            when rr.rule_name like '%线索复用%' then '线索复用'
            when rr.rule_name like '%孟亚飞ip19元%' or rr.rule_name like '%孟亚飞IP19元%' then '孟亚飞IP9元'
            when rr.rule_name like '%孟亚飞IP99元%' or rr.rule_name like '%孟亚飞ip99元%' then '孟亚飞IP99元'
            when (rr.rule_name like '%孟亚飞IP9元%' or rr.rule_name like '%孟亚飞ip9元%') and rr.rule_name not like '%孟亚飞IP99元%' then '孟亚飞IP9元'
            when (rr.rule_name like '%孟亚飞IP%' or rr.rule_name like '%孟亚飞ip9元%') and rr.rule_name not like '%孟亚飞IP9元%' then '孟亚飞IP9元'
            when rr.rule_name like '%图书KOC%' then '图书KOC'
            when rr.rule_name like '%朱汉祺IP%' then '朱汉祺IP'
            when rr.rule_name like '%西安图书%' then '西安图书'
            when rr.rule_name like '%常规KOC%' then '常规KOC'
            when rr.rule_name like '%进校%' then '进校0元'
            when rr.rule_name like '%春春B站99元%' then '春春B站99元'
            when rr.rule_name like '%肖晗ip9元%' then '肖晗ip9元'
            when rr.rule_name like '%肖晗ip19元%' or rr.rule_name like '%ip肖晗19元%' then '肖晗ip19元'
            when rr.rule_name like '%koc肖晗5元%' then 'koc肖晗5元'
            when rr.rule_name like '%koc自孵化5元%' or rr.rule_name like '%koc广州本地化5元%' then 'koc自孵化5元'
            when rr.rule_name like '%koc常规5元%' then 'koc常规5元'
            when rr.rule_name like '%koc朱汉祺5元%' then 'koc朱汉祺5元'
            when rr.rule_name like '%朱汉祺ip29元%' then '朱汉祺ip29元'
            when rr.rule_name like '%koc朱汉祺29元%' or rr.rule_name like '%koc周帅29元%' or rr.rule_name like '%周帅29元%' or rr.rule_name like '%朱汉祺29元%' or rr.rule_name like '%朱汉祺koc29元%' then 'koc29元'
            when rr.rule_name like '%B站朱汉祺29元%' or rr.rule_name like '%B站周帅19元%' then 'B站29元'
            when rr.rule_name like '%春春ip99元%' then '春春ip99元'
            when rr.rule_name like '%私域0元%' or rr.rule_name like '%表单高中%' or rr.rule_name like '%私域表单0元%' then '私域0元'
            when rr.rule_name like '%私域9元%' then '私域9元'
            when rr.rule_name like '%拓展koc%' or rr.rule_name like '%拓展ip%' or rr.rule_name like '%koc外部发货%' or rr.rule_name like '%多学科拓展%' then '多学科拓展'
            when rr.rule_name like '%商务书商1元%' or rr.rule_name like '%商务1元%' or rr.rule_name like '%商务进校18元%' or rr.rule_name like '%商务TMK9元%' or rr.rule_name like '%商务%' then '商务'
            when rr.rule_name like '%训练营%' or rr.rule_name like '%CRM特殊链接分配策略%' then '训练营'
            when rr.rule_name like '%信息流%' then '信息流'
            when rr.rule_name like '%小红书%' then '小红书'
            when rr.rule_name like '%原子初三%' or rr.rule_name like '%原子高一%' or rr.rule_name like '%原子%' then '原子'
            when rr.rule_name like '%9KM%' then '9KM'
            when rr.rule_name like '%百度星耀数学%' or rr.rule_name like '%数学%' or rr.rule_name like '%百度星耀物理%' or rr.rule_name like '%物理%' then '百度星耀'
            else '未知'
        end as channel_1,
        case
            when rr.rule_name like '%高一%' then '高一'
            when rr.rule_name like '%高二%' then '高二'
            when rr.rule_name like '%高三%' then '高三'
            when rr.rule_name like '%初二%' then '初二'
            when rr.rule_name like '%初三%' then '初三'
            else '未知'
        end as grade_1
    from lead_gmv
    left join (
        select
            *,
            case
                when instr(rule_name, '期') > 0
                 and instr(rule_name, '期') >= 5
                 and regexp_like(substr(rule_name, instr(rule_name, '期') - 4, 4), '^[0-9]{4}$')
                then substr(rule_name, instr(rule_name, '期') - 4, 5)
                else null
            end as group_period_term
        from service_dw.dim_crm_assign_rule_lead_detail_hf
        where dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
          and hour = format_datetime(now() - interval '3' hour, 'HH')
    ) rr
      on lead_gmv.lead_id = rr.lead_id
     and lead_gmv.email_prefix = rr.account_domain
),
base as (
    select
        rule.*,
        zx.xiaozu,
        zx.jingli
    from rule
    left join temp_table.dingxi01_jiagou_zx zx
      on zx.employee_email_name = rule.name
),
geren as (
    select
        qici,
        channel_1,
        jingli,
        grade_1,
        sum(case when weekday_name = '周1' then name_total_price else 0 end) as gmv_1,
        sum(case when weekday_name = '周2' then name_total_price else 0 end) as gmv_2,
        sum(case when weekday_name = '周3' then name_total_price else 0 end) as gmv_3,
        sum(case when weekday_name = '周4' then name_total_price else 0 end) as gmv_4,
        sum(case when weekday_name = '周5' then name_total_price else 0 end) as gmv_5,
        sum(case when weekday_name = '周6' then name_total_price else 0 end) as gmv_6,
        sum(case when weekday_name = '周7' then name_total_price else 0 end) as gmv_7,
        sum(name_total_price) as gmv_t
    from base
    group by
        qici,
        channel_1,
        jingli,
        grade_1
),
data as (
    select distinct
        f.*,
        case
            when cast(date_parse(replace(concat(f.group_period_year, f.group_period_term), '期', ''), '%Y%m%d') as date) between date '2026-07-14' and date '2026-07-19' then '20260716期'
            when cast(date_parse(replace(concat(f.group_period_year, f.group_period_term), '期', ''), '%Y%m%d') as date) between date '2026-07-20' and date '2026-07-25' then '20260722期'
            when cast(date_parse(replace(concat(f.group_period_year, f.group_period_term), '期', ''), '%Y%m%d') as date) between date '2026-07-26' and date '2026-07-31' then '20260728期'
            when cast(date_parse(replace(concat(f.group_period_year, f.group_period_term), '期', ''), '%Y%m%d') as date) between date '2026-08-01' and date '2026-08-06' then '20260803期'
            when cast(date_parse(replace(concat(f.group_period_year, f.group_period_term), '期', ''), '%Y%m%d') as date) between date '2026-08-07' and date '2026-08-12' then '20260808期'
            else concat(
            date_format(
                date_trunc(
                    'week',
                    date_parse(replace(concat(f.group_period_year, f.group_period_term), '期', ''), '%Y%m%d') - interval '1' day
                ) + interval '4' day,
                '%Y%m%d'
            ),
            '期'
        )
        end as qici,
        CASE 
            -- 【区域定向】
   when f.get_customer_way_name in ('平台自播') and f.flow_pool_name in ('赢战广东中考','高途专版图书','状元帮教辅','高途专版视频书','本地化专版图书') then '广东图书'
   when f.get_customer_way_name in ('平台自播') and f.flow_pool_name in ('途铭文化专版图书','途铭文化','博慧星辰文化图书','启迪蔚来','智慧航迹图书','高途浙江初中','高途浙江高中','高途浙江新高一') then '浙江图书'
   when f.get_customer_way_name in ('平台自播') and f.flow_pool_name in ('沪上名校','沪上领航社','简学文化','魔都校友助学馆','沪上领航高中','沪上领航初中') then '上海图书'
   when f.get_customer_way_name in ('平台自播') and f.flow_pool_name in ('高途江苏中考','高途赢战中考') then '江苏图书'
   when f.get_customer_way_name in ('平台自播') and f.flow_pool_name in ('京赋-浙江科学曹忆规划','为真-浙江科学曹忆老师','为真-浙江大科学曹忆老师','京赋-江苏曹忆老师规划','博学星辰初阶规划峥峥','博学星辰-曹忆老师浙江规划','京赋-浙江曹忆老师规划') then '曹忆'
when f.flow_pool_name='电商退款用户池' and f.rule_name like '%赠失%' and f.rule_name like '%朱博士%' then '赠课失败-朱汉祺'
when f.flow_pool_name='电商退款用户池' and f.rule_name like '%赠失%' and f.rule_name like '%春春%' then '赠课失败-陈瑞春'
when f.flow_pool_name='电商退款用户池' and f.rule_name like '%赠失%' and f.rule_name like '%亚飞%' then '赠课失败-孟亚飞'
when f.flow_pool_name='电商退款用户池' and f.rule_name like '%赠失%' and f.rule_name like '%星义%' then '赠课失败-赵星义'
when f.flow_pool_name='电商退款用户池' and f.rule_name like '%赠失%' and f.rule_name like '%郭艺%' then '赠课失败-郭艺'
when f.second_department_name='本地化大班学部' or f.source_manager_name in ('鲍大海','杨文卓') then '本地化市场流量'
when f.third_department_name in ('中价产品项目部','新媒体内容运营部') and f.rule_name like '%曹忆%' then '曹忆'
when f.rule_name like '%语数英%' and f.third_department_name = '新媒体内容运营部' then '语数英'
 when f.third_department_name = '直播部' and f.sku_id_name like '%山东专版%' then '北京直播山东'
  when f.third_department_name = '直播部' and f.sku_id_name like '%河南专版%' then '北京直播河南'
  when f.rule_name like '%北京直播江苏%' then '北京直播江苏'
when f.third_department_name like '%锋途%' and f.channel_name_2 = '抖音' then '锋途KOC'
when f.put_plan_name like '%小红书打粉%' then 'EM-小红书合作'
when f.trace_type_name like '%转介绍%' then '转介绍'
when f.flow_pool_name like '%星义大大%' or f.flow_pool_name like '%星义物理%' then '赵星义'
when f.ad_account_name in ('高途-高中-DYD搜索-QZ49','高途-高中-DYD搜索-XLHD49','高途-高中-DYD搜索-XLHD50','高途-高中-DYD搜索-QZ50') then '搜索1元'
when (f.flow_pool_name like '%江苏预习%' or  f.flow_pool_name like '%江苏专版预习%') and f.channel_name_2 ='抖音' then '西安直播江苏-抖音'
when f.flow_pool_name like '%自然流%' and f.rule_name like '%江苏%' and f.third_department_name='图书营销部' and f.channel_name_2 ='抖音' then '西安直播江苏-抖音'
when (f.flow_pool_name like '%江苏预习%' or  f.flow_pool_name like '%江苏专版预习%') and f.channel_name_2 ='视频号' then '西安直播江苏-视频号'
when f.flow_pool_name like '%自然流%' and f.rule_name like '%江苏%' and f.third_department_name='图书营销部' and f.channel_name_2 ='视频号' then '西安直播江苏-视频号'
when f.rule_name like '%北京图书%' and f.third_department_name='图书营销部' then '西安直播北京'
when f.flow_pool_name like '%自然流%' and f.rule_name like '%北京%' and f.third_department_name='图书营销部' then '西安直播北京'
when f.source_manager_name in ('马思雨02','袁银') and f.rule_name like '%集团%' then '集团私域'
when f.rule_name like '%途途私域%' or (f.rule_name like '%私域%' and f.first_department_name = 'TT') or f.rule_name like '%私域1元%' or (f.third_department_name='私域招生中心' and f.flow_pool_name like '%APP%') then '途途私域'
when f.third_department_name='图书营销部' and (f.sku_id_name like '%孟亚飞99%' or f.sku_id_name like '%亚飞%') and f.channel_name_2 = '百度' then '孟亚飞-2组-百度'
when f.third_department_name='图书营销部' and (f.sku_id_name like '%孟亚飞99%' or f.sku_id_name like '%亚飞%') and f.channel_name_2 = '抖音' then '孟亚飞-2组-抖音'
when f.third_department_name = '投放部' and (f.ad_account_name like '%周帅%') then '信息流-周帅'
when f.source_manager_name in ('韩正卿') then '抖音私信'
when f.third_department_name = '私域运营部' and f.source_manager_name in ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研','岳一帆02','田起帆','王绍阳','肖佳兴','姚佳03') then '进校私域合作'
when f.channel_name_1='市场私域' and (f.virtual_fourth_department_name in ('郑州学习顾问二部','郑州学习顾问七部','郑州训练营') or f.virtual_fifth_department_name in ('罗江博团队')) then '市场私域入群'
when f.third_department_name = '图书营销部' and (f.rule_name like '%点睛卷%' or f.sku_id_name like '%押题卷%')  then '押题卷'
when f.third_department_name = '投放部' and f.channel_name_2 = '小红书' and f.channel_name_1 <> '搜索营销' then '信息流-小红书'
when f.third_department_name = '线上商务部' and f.channel_name_2 = '小红书' then '小红书'
when (f.flow_pool_name like '%北大汤哥%' or f.flow_pool_name like '%海淀名师高阶%' or f.flow_pool_name like '%海淀高阶%' or f.flow_pool_name like '%高阶英语887%') and f.sku_id_name like '%小艺%'  then '郭艺'
when  f.third_department_name like '%私域%' and f.rule_name like '%私域%' and f.rule_name like '%图书%' then '市场私域图书'
when  f.third_department_name like '%私域%' and f.rule_name like '%品效%'  then '市场私域品效'
when  f.third_department_name like '%私域%' and f.rule_name like '%公域学霸%'  then '市场私域公域组'
when f.third_department_name in ('线上商务部') and f.source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07','曲默晗') and f.flow_pool_name like '%退款%' then 'KOC-退款订单复用'
when f.third_department_name in ('直播部','新媒体内容运营部','市场一组','私域运营部') and f.put_plan_name like '%退%' and f.flow_pool_name ='电商退款用户池'  then '退款订单复用'
when f.third_department_name in ('直播部','新媒体内容运营部','市场一组','私域运营部') and f.put_plan_name like '%失败%' and f.flow_pool_name ='电商退款用户池'  then '赠课失败'
when f.third_department_name in ('直播部','新媒体内容运营部','市场一组')  and (f.flow_pool_name ='初阶化学规划' or f.flow_pool_name like '%启迪-初阶老师%')  then '曹忆'
when (f.third_department_name = '图书营销部' and f.sku_id_name like '%真题%') or (f.third_department_name='直播部' and f.sku_id_name like '%真题%') then '西安图书直播间-直播'
when (f.third_department_name = '图书营销部' and f.sku_id_name not like '%真题%') or (f.third_department_name='直播部' and f.sku_id_name  like '%秒懂%') or (f.third_department_name='直播部' and f.sku_id_name  like '%图书赠送%') then '西安图书直播间-挂链'
when f.third_department_name in ('直播部','新媒体内容运营部','市场一组') and (f.flow_pool_name like '%海淀高阶名师%' or f.flow_pool_name like '%海淀老师高阶%' or f.flow_pool_name like '%小艺%' or f.flow_pool_name like '%老蒋文化%') then '郭艺'
when f.third_department_name in ('直播部','新媒体内容运营部','市场一组') and f.flow_pool_name like '%电商退款%' and f.rule_name like '%郭艺99%' then '郭艺'
when f.put_plan_name like '%国培教育-0元%' or f.put_plan_name like '%易喆教育-0元%' or f.put_plan_name like '%钟情-0元%' or f.put_plan_name like '%中望达-0元%' or f.put_plan_name like '%晨硕-0元%' or f.put_plan_name like '%彩石-0元入群%'  then '创新商务入群'
when f.third_department_name='KOC孵化部' and f.flow_pool_name like '%电商退款%' and f.put_plan_name like '%失败%' then '自孵化KOC-赠课失败'
when f.third_department_name='KOC孵化部' and f.flow_pool_name like '%电商退款%' and f.put_plan_name like '%退%' then '自孵化KOC-退款订单复用'
when f.source_manager_name = '方俊结01' and f.put_plan_name like '%赠课后退款%' then 'KOC-赠课后退款' 
when f.third_department_name = '直播部' and (f.sku_id_name like '%春春%' or f.sku_id_name like '%瑞春%' or f.rule_name like '%春春%' or f.rule_name like '%瑞春%') then '陈瑞春'
when f.third_department_name = '直播部' and (f.sku_id_name like '%朱博士99%' or f.rule_name like '%朱汉祺99%' or f.rule_name like '%朱博士%' or f.flow_pool_name like '%朱博士%' or f.sku_id_name like '%朱博士%') then '朱博士99'
when (f.third_department_name = '直播部' and (f.sku_id_name like '%朱博士%' or f.sku_id_name like '%朱汉祺%') and f.rule_name like '%9%' and f.rule_name not like '%29%' and f.sku_id_name not like '%急%' and f.sku_id_name not like '%礼盒29%') or (f.third_department_name = '直播部' and f.sku_id_name like '%朱博士9%') then '朱博士9元'
when f.ad_account_name like '%春春%' and f.channel_name_1 = '信息流' then '信息流-陈瑞春'
when f.channel_name_1 = '信息流' and f.channel_name_2='B站' and (f.page_id_name like '%0元物化%') then 'B站信息流-曹忆'
when f.channel_name_1 = '信息流' and f.channel_name_2='B站' and (f.page_id_name like '%赵星义%') then 'B站信息流-赵星义'
when f.third_department_name = '直播部' and f.channel_name_1 = '信息流' and f.channel_name_2 = 'B站'  then 'B站信息流-亚飞(1元)'
when f.channel_name_1 = '信息流' and f.channel_name_2='B站' and (f.page_id_name like '%亚飞%' or f.source_put_plan_name like '%亚飞%'   or f.page_id_name like '%初中-0元%') then 'B站信息流-亚飞'
when f.channel_name_1 = '信息流' and (f.page_id_name like '%亚飞%' or f.ad_account_name like '%亚飞%') then '信息流-亚飞'
when (f.flow_pool_name like '%朱博士%' or f.flow_pool_name like '%双博士%' or f.flow_pool_name like '%教育规划%') and f.third_department_name <> '线上商务部' and f.period_name not like '%多学科拓展%' and f.rule_name not like '%张杰%' and f.sku_id_name not like '%马凯鹏IP%' and f.third_department_name='直播部' then '朱博士29'
when f.put_plan_name like '%朱博士说教育%' and f.period_name not like '%多学科拓展%' and f.flow_pool_name not like '%高分讲堂%' and  f.flow_pool_name not like '%总裁%' and f.third_department_name='直播部' then '朱博士29'
when (f.flow_pool_name like '%朱博士讲英语%' or f.flow_pool_name like '%朱博士英语%' or f.flow_pool_name like '%朱汉祺说英语%' or f.flow_pool_name like '%朱博士说英语%' or f.flow_pool_name like '%教育规划%' or f.flow_pool_name like '%双博士英语规划%' or f.flow_pool_name like '%朱博士满分英语%' or f.flow_pool_name like '%英语教父朱博士%' or (f.flow_pool_name like '%中考决胜天团%' and f.lead_purchase_intention_level1_category_name = '规划系统')) and f.third_department_name = '直播部' and f.period_name not like '%多学科拓展%' and f.sku_id_name not like '%马凯鹏IP%' and f.third_department_name='直播部' then '朱博士29'
when (f.flow_pool_name like '%汤哥%' or f.flow_pool_name like '%汤老师%') and f.period_name not like '%多学科拓展%' and f.third_department_name in ('直播部','新媒体内容运营部')  then '汤老师'
when f.source_manager_name = '陈晓菁04' and f.channel_provider_name not like '%开拓%' and f.put_plan_name not like '%九学%' then '商务低价'  
when (f.flow_pool_name like '%孟帝%' or f.flow_pool_name like '%孟老师%' or f.flow_pool_name like '%中考数学冲刺%' or f.flow_pool_name like '%8升9数学%' or f.flow_pool_name like '%孟亚飞讲数学%' or f.flow_pool_name like '%中考冲刺%' or f.flow_pool_name like '%中考满分冲刺%' or f.flow_pool_name like '%押题王孟亚飞%' or f.flow_pool_name like '%中考数学大通关%' or f.flow_pool_name like '%中考数学规划%' or f.flow_pool_name like '%亚飞数学%' or f.flow_pool_name like '%孟帝数学%' or f.flow_pool_name like '%亚飞秒解思维%' or f.flow_pool_name like '%亚飞解题%')  and f.period_name not like '%多学科拓展%' and f.channel_name_2 not like '%KOL%' and f.third_department_name='直播部' and f.channel_name_2 = '抖音'  then '孟亚飞-1组-抖音'
when (f.flow_pool_name like '%孟帝%' or f.flow_pool_name like '%孟老师%' or f.flow_pool_name like '%中考数学冲刺%' or f.flow_pool_name like '%8升9数学%' or f.flow_pool_name like '%孟亚飞讲数学%' or f.flow_pool_name like '%中考冲刺%' or f.flow_pool_name like '%中考满分冲刺%' or f.flow_pool_name like '%押题王孟亚飞%' or f.flow_pool_name like '%中考数学大通关%' or f.flow_pool_name like '%中考数学规划%' or f.flow_pool_name like '%亚飞数学%' or f.flow_pool_name like '%孟帝数学%')  and f.period_name not like '%多学科拓展%' and f.channel_name_2 not like '%KOL%' and f.third_department_name='直播部' and f.channel_name_2 = '视频号'  then '孟亚飞-1组-视频号'
when (f.flow_pool_name like '%孟帝%' or f.flow_pool_name like '%孟老师%' or f.flow_pool_name like '%中考数学冲刺%' or f.flow_pool_name like '%8升9数学%' or f.flow_pool_name like '%孟亚飞讲数学%' or f.flow_pool_name like '%中考冲刺%' or f.flow_pool_name like '%中考满分冲刺%' or f.flow_pool_name like '%押题王孟亚飞%' or f.flow_pool_name like '%中考数学大通关%' or f.flow_pool_name like '%中考数学规划%' or f.flow_pool_name like '%亚飞数学%' or f.flow_pool_name like '%孟帝数学%')  and f.period_name not like '%多学科拓展%' and f.channel_name_2 not like '%KOL%' and f.third_department_name='直播部' and f.channel_name_2 = 'B站'  then '孟亚飞-1组-B站'
when (f.flow_pool_name like '%孟帝%' or f.flow_pool_name like '%孟老师%' or f.flow_pool_name like '%中考数学冲刺%' or f.flow_pool_name like '%8升9数学%' or f.flow_pool_name like '%孟亚飞讲数学%' or f.flow_pool_name like '%中考冲刺%' or f.flow_pool_name like '%中考满分冲刺%' or f.flow_pool_name like '%押题王孟亚飞%' or f.flow_pool_name like '%中考数学大通关%' or f.flow_pool_name like '%中考数学规划%' or f.flow_pool_name like '%亚飞数学%' or f.flow_pool_name like '%孟帝数学%')  and f.period_name not like '%多学科拓展%' and f.channel_name_2 not like '%KOL%' and f.third_department_name='直播部' and f.channel_name_2 not like '%百度%'  then '孟亚飞99-1组'
when (f.flow_pool_name like '%孟帝%' or f.flow_pool_name like '%孟老师%' or f.flow_pool_name like '%中考数学冲刺%' or f.flow_pool_name like '%8升9数学%' or f.flow_pool_name like '%孟亚飞讲数学%' or f.flow_pool_name like '%中考冲刺%' or f.flow_pool_name like '%中考满分冲刺%' or f.flow_pool_name like '%押题王孟亚飞%' or f.flow_pool_name like '%中考数学大通关%' or f.flow_pool_name like '%中考数学规划%' or f.flow_pool_name like '%亚飞数学%')  and f.period_name not like '%多学科拓展%' and f.channel_name_2 not like '%KOL%' and f.third_department_name='直播部' and f.channel_name_2 = '百度'  then '孟亚飞-1组-百度'
when (f.flow_pool_name like '%孟帝%' or f.flow_pool_name like '%孟老师%' or f.flow_pool_name like '%中考数学冲刺%' or f.flow_pool_name like '%8升9数学%' or f.flow_pool_name like '%孟亚飞讲数学%' or f.flow_pool_name like '%中考冲刺%' or f.flow_pool_name like '%中考满分冲刺%' or f.flow_pool_name like '%押题王孟亚飞%' or f.flow_pool_name like '%中考数学大通关%' or f.flow_pool_name like '%中考数学规划%' or f.flow_pool_name like '%亚飞数学%')  and f.period_name not like '%多学科拓展%' and f.channel_name_2 not like '%KOL%' and f.third_department_name='直播部'  then '孟亚飞9元'
when f.put_plan_name like '%刘家晋讲图文%' or f.put_plan_name like '%孟帝数学%' and f.third_department_name='直播部' and f.rule_name like '%99%'  then '孟亚飞99-1组'  
when f.put_plan_name like '%刘家晋讲图文%' or f.put_plan_name like '%孟帝数学%' and f.third_department_name='直播部' then '孟亚飞9元'  
when f.flow_pool_name like '%汐子%' and f.period_name not like '%多学科拓展%' and f.sku_id_name  like '%亚飞%' and f.third_department_name='直播部' and f.rule_name like '%99%'  then '孟亚飞99-1组'
when (f.flow_pool_name like '%曹忆%' or f.flow_pool_name like '%dudu%' or f.flow_pool_name like '%中考决胜天团%' or f.flow_pool_name like '%具象思维%' or f.flow_pool_name like '%在逃发面馒头%' or f.flow_pool_name like '%库洛米%' and f.lead_purchase_intention_level1_category_name <> '规划系统') and f.period_name not like '%多学科拓展%' and f.third_department_name in ('直播部','新媒体内容运营部') then '曹忆'
when f.first_department_name ='市场部' and f.channel_name_1 <> '站内获客' and f.channel_name_2 <> 'APP' then '集团私域'
when f.third_department_name = '私域运营部' and f.rule_name not like '%训练营%' and f.virtual_fifth_department_name not in ('罗江博团队') and f.rule_name not like '%复用%' and f.rule_name not like '%未加好友%' and f.channel_name_2 <> '内部换量' then '市场私域低价单'
when f.third_department_name = '私域运营部' and f.rule_name not like '%训练营%'  and f.rule_name not like '%复用%' and f.rule_name not like '%未加好友%' and f.channel_name_2 <> '内部换量' and f.flow_original_order_activity_price = '0.0' then '市场私域低价单'
when f.channel_name_2 in ('APP','M站','PC') and f.flow_pool_name not like '%途途%' then 'APP'
when f.channel_name_2 in ('小程序') and f.flow_pool_name  like '%高途体验课%' then 'APP'
when f.channel_provider_name like '%唐山TMK%' then '唐山TMK' 
when f.source_manager_name in ('高文羽') and f.channel_provider_name not like '%唐山TMK%' and f.channel_provider_name not like '%郑州%' then '人工外呼' 
when f.source_manager_name = '冯银晨' and f.channel_name_2 = '小红书' then '信息流-小红书'  
when f.channel_name_1 = '信息流' and f.channel_name_2 = 'B站' and f.third_department_name not like '%投放%' and f.page_id_name like '%汤雪%'  then 'B站信息流-汤学健'
when (f.channel_name_1 = '信息流' and f.channel_name_2 <> 'B站' and f.third_department_name NOT LIKE '%商务%' and f.put_plan_name not like '%初三0元%' and f.put_plan_name not like '%抖音私信%' and f.put_plan_name not like '%高中0元%' and f.flow_original_order_activity_price not like '%1990%') or (f.channel_name_2 = 'B站' and f.third_department_name like '%投放%') then '信息流'
when f.channel_name_1 = '信息流' and f.channel_name_2 = 'B站' and f.third_department_name not like '%投放%' and (f.page_id_name like '%郭艺%') then 'B站信息流-郭艺'
when f.channel_name_1 = '信息流' and f.channel_name_2 = 'B站' and f.third_department_name not like '%投放%' and (f.page_id_name like '%朱博士%') then 'B站信息流-朱汉祺'
when f.channel_name_1 = '信息流' and f.channel_name_2 = 'B站' and f.third_department_name not like '%投放%' and f.page_id_name like '%肖晗%' then 'B站信息流'
when f.channel_name_1 = '信息流' and f.channel_name_2 = 'B站' and f.third_department_name not like '%投放%' and (f.page_id_name like '%马凯鹏%' or f.ad_account_name like '%化学%') then 'B站信息流-马凯鹏'
when f.channel_name_1 = '信息流'  and f.channel_name_2 = 'B站' and f.third_department_name not like '%投放%' and  (f.sku_id_name like '%陈瑞春%' or f.rule_name like '%陈瑞春%') and (f.ad_account_name  like '%语文%' or f.source_put_plan_name like '%自然流%' or f.page_id_name like '%春春%') then 'B站信息流-陈瑞春'
when f.channel_name_1 = '信息流' and f.channel_name_2 = 'B站' and f.third_department_name not like '%投放%' and (f.flow_original_order_activity_price like '%2990%' or f.sku_id_name like '%帅师%' or f.sku_id_name like '%周帅%') and f.ad_account_name like '%语文%' and  (f.flow_original_order_activity_price like '%1980%' or f.flow_original_order_activity_price like '%2980%' or f.flow_original_order_activity_price like '%2990%') then 'B站信息流-陈瑞春'
when f.channel_name_1 = '信息流' and f.channel_name_2 = 'B站' and f.third_department_name not like '%投放%' and (f.flow_original_order_activity_price like '%2990%' or f.sku_id_name like '%帅师%' or f.sku_id_name like '%周帅%') and f.ad_account_name not like '%语文%' then 'B站信息流-周帅'
when f.channel_name_1 = '信息流' and f.channel_name_2 = 'B站' and f.third_department_name not like '%投放%' and f.flow_order_price like '%1980%' and f.ad_account_name like '%数学%' then 'B站信息流-周帅'
when f.channel_name_1 = '短直电商' and f.channel_name_2 = 'B站' and f.third_department_name  like '%商务%' and   (f.flow_pool_name like '%春春%' or f.sku_id_name like '%陈瑞春%')  then 'B站信息流-陈瑞春'
when f.channel_name_1 = '短直电商' and f.channel_name_2 = 'B站' and f.third_department_name  like '%商务%' and  (f.flow_pool_name like '%朱博士%')  then 'B站信息流-朱汉祺'
--when third_department_name = '线上商务部' and channel_name_2 = 'B站' and put_plan_name like '%春春%' then 'B站信息流-陈瑞春'
--when third_department_name = '线上商务部' and channel_name_2 = 'B站' and put_plan_name like '%朱博士%' then 'B站信息流-朱汉祺'
when f.channel_name_1 = '信息流' and f.channel_name_2 = 'B站' and f.third_department_name not like '%投放%' and f.flow_original_order_activity_price not like '%2980%' and f.flow_original_order_activity_price not like '%2990%' and f.flow_original_order_activity_price not like '%1980%' then 'B站信息流'
when f.flow_pool_name = '百度搜索引擎' or f.channel_name_1='搜索营销' then '信息流搜索'
when  f.flow_pool_name like '%小红书班课%' then '小红书投放'
when f.third_department_name = '投放部' and f.get_customer_way_name = '短视频信息流' and f.flow_original_order_activity_price like '%100%' then '信息流'
when f.flow_pool_name = '中考加油' and f.sku_id_name like '%孟帝%' then 'KOC-孟亚飞数学'
when f.flow_pool_name = '中考加油' and f.sku_id_name  like '%帅师%' then 'KOC-周帅数学'
when  f.source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07','曲默晗') and (f.sku_id_name like '%孟帝%' or f.sku_id_name like '%dudu%' or f.sku_id_name like '%市场初二%' or f.rule_name like '%亚飞%' or f.sku_id_name like '%初二高阳%' or f.sku_id_name like '%高阳初二%' or f.sku_id_name like '%精品初二%' or f.rule_name like '%初二%' or f.sku_id_name like '%菁英初三%' or (f.virtual_second_department_name = '菁英班学部' and f.lead_purchase_intention_level2_category_name='初级' and f.lead_create_time>= '2026-04-15 00:00:00')) then 'KOC-孟亚飞数学'
when  f.source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07','曲默晗') and (f.sku_id_name like '%帅师%' or f.rule_name like '%周帅%' or f.sku_id_name like '%9月升高三%' or f.sku_id_name like '%新高二%') then 'KOC-周帅数学'
when  f.source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07','曲默晗') and (f.sku_id_name like '%肖晗%' or f.rule_name like '%肖晗%') then 'KOC-肖晗'
when  f.source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07','曲默晗') and f.period_name not like '%多学科拓展%' and f.sku_id_name not like '%朱汉祺%' and f.sku_id_name not like '%朱博士%' and f.sku_id_name not like '%周帅%' and f.sku_id_name not like '%29元%' then 'KOC-5元纯课'
when  f.source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07','曲默晗') and f.sku_id_name like '%周帅%' then 'KOC-周帅'
--when (channel_name_2 like '%KOL%' and source_manager_name in ('崔文轩','孙培尧')) or (channel_name_2 like '%抖音%' and source_manager_name in ('徐绮鹤')) and period_name not like '%多学科拓展%' then '自孵化KOC'
when f.third_department_name in ('品牌效能部','KOC孵化部') and f.channel_name_2 in ('抖音','视频号','快手','KOL')  then '自孵化KOC-5元纯课'
when f.third_department_name in ('品牌效能部','KOC孵化部') and f.channel_name_2 in ('抖音','视频号','快手','KOL') and (f.sku_id_name like '%5元%'or f.sku_id_name like '%11元%' or f.flow_original_order_activity_price like '%1100%' or f.flow_original_order_activity_price like '%500%' or f.flow_orders_income_amount  like '%1100%' or f.flow_orders_income_amount  like '%500%' ) then '自孵化KOC-5元纯课'
when f.source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04','赵艺雅') and f.channel_name_2 like '%社群%' then '进校社群'
when f.source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04','赵艺雅') and (f.channel_name_2 like '%直推%' or (f.put_plan_name like '%良师益友%' or f.put_plan_name like '%弘诚1元%')) then '进校直推'
when f.source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04','赵艺雅') and f.channel_name_2 like '%TMK%' and (f.page_id_name like '%1元%' or f.channel_provider_name like '%禾顺云%') then '进校TMK1元'
when f.source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04','赵艺雅') and f.channel_name_2 like '%TMK%' and f.page_id_name like '%9元%' then '进校TMK9元'
when f.source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04','赵艺雅') and f.channel_name_2 like '%书商%' then '进校书商'
when f.source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04','赵艺雅') and f.channel_name_2 like '%综合%' and f.put_plan_name like '%18%' then '进校直播'
when f.source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','陈晓菁04','赵艺雅') and f.channel_name_2 like '%直播%' then '进校直播'
when f.source_manager_name in ('包青青','蔡瑞涵','李文迁','李佳馨44','孙昊17','王洁雅01','王硕北','朱文','贾铭锐','李壮壮04','赵艺雅') and f.put_plan_name not like '%0元%' and f.flow_pool_name not like '%家校共育%' and f.flow_pool_name not like '%保持热爱%' and f.flow_pool_name not like '%青松%' and f.flow_pool_name not like '%原子初三%' and f.flow_pool_name not like '%南通欣创%' and f.flow_pool_name not like '%悟之道%' and f.flow_pool_name not like '%济南梦航%' and f.channel_name_3 <> '社群' and f.put_plan_name not like '%善悟%' and f.put_plan_name not like '%人人通%'  and f.put_plan_name not like '%%济南格乐' and f.flow_pool_name not like '%晨硕智学%' and f.flow_pool_name not like '%兴尧文化%'  and f.flow_pool_name not like '%济南映像%' and f.flow_pool_name not like '%山东简单%' and f.flow_pool_name not like '%争鸣科技%'  then '商务低价'
when f.flow_pool_name like '%南通欣创%' or  f.flow_pool_name like '%人人通科技%' or f.flow_pool_name like '%易而购%' or f.flow_pool_name like '%济南梦航%' or f.flow_pool_name like '%晨硕智学%' or f.flow_pool_name like '%兴尧文化%' or f.flow_pool_name like '%济南映像%' or f.flow_pool_name like '%山东简单%' or f.flow_pool_name like '%争鸣科技%'  then '进校私域合作'
when (f.flow_pool_name like '%家校共育%' or f.flow_pool_name like '%保持热爱%' or f.flow_pool_name like '%青松%' or f.flow_pool_name like '%悟之道%') and f.put_plan_name not like '%0元%'  then '进校私域合作'
when f.source_manager_name = '李宁24' and f.put_plan_name like '%0转低%' then '进校私域合作'
when f.third_department_name = '私域运营部' and  f.flow_original_order_activity_price in ('100.0','900.0','300.0')  then '进校私域合作'
when f.third_department_name = '私域运营部' and  f.flow_original_order_activity_price in ('0.0') and f.source_manager_name in ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研') then '进校私域合作'
when f.third_department_name = '私域运营部' and f.channel_name_1='市场私域' and f.put_plan_name not like '%公导私%' and f.put_plan_name not like '%公转私%' and f.flow_original_order_activity_price = '0.0' and f.rule_name not like '%激活%' and f.rule_name not like '%咨询%' and f.rule_name not like '%训练营%'  and f.virtual_fifth_department_name not like '%罗江博%' and f.virtual_fifth_department_name not like '%郑州学习顾问二部%' and f.source_manager_name not in ('陈雷19','崔慧敏01','侯佳林01','郑天琪02','杨彬屹','曹义鹏','王硕阳','于超研') then '市场私域低价单'
when f.source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and f.channel_provider_name like '%格乐教育%' and f.channel_name_2 like '%直播%' then '创新社群'
when f.source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and f.channel_name_2 like '%社群%' then '创新社群'
when f.source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and (f.channel_name_2 like '%直推%' or f.put_plan_name like '%直推%') then '创新直推'
when f.source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and (f.channel_name_2 like '%书商%' or f.put_plan_name like '%书商%' or f.page_id_name like '%书商%') then '创新书商'
when f.source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and f.channel_name_2 like '%TMK%' and f.page_id_name like '%1元%' then '创新TMK1元'
when f.source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and f.channel_name_2 like '%TMK%' and f.page_id_name like '%9元%' then '创新TMK9元'
when f.source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and (f.channel_name_2 like '%直播%' or f.page_id_name like '%进校%') then '创新直播'
when f.source_manager_name in ('耿文超','晋翠翠','赵语诗','王慧敏13','于新茹','梁超01','刘晓20','王玉120','吕佳乐01') and f.channel_name_2<>'公众号' and f.channel_name_1 = '商务' and f.flow_pool_name <> '高途云集图书专营店-自然流' and f.flow_pool_name <> '高途旗舰店—线索—yuxinru' and f.put_plan_name not like '%社群%' and f.put_plan_name not like '%小红书班课%' and f.put_plan_name not like '%外部图书供量%' and f.channel_second_provider_name not like '%沃德丰店铺线索赠课%' and f.channel_second_provider_name not like '%智慧城-图书%' and f.put_plan_name not like '%育甲%' and f.flow_pool_name not like '%周长磊%'  then '创新商务'
when f.source_manager_name in ('高曼曼01','杨思怡','宋向函') then '图书KOC达人'
--when flow_pool_name like '%市场部-原子合作%' then '原子'
when f.flow_pool_name like '%市场部-微信私域%' or f.flow_pool_name like '%市场部-规划报告%' or f.flow_pool_name like '%规划报告%' or f.flow_pool_name like '%市场部-小红书%' or f.flow_pool_name like '%孟浩宇%' then '市场私域低价单'
when f.flow_pool_name like '%未加好友%' then '市场私域未加好友'
when f.flow_pool_name like '公导私' then '进校私域合作'
when (f.flow_pool_name like '%增长组%' or f.channel_name_3 = '公众号' or f.second_department_name = '微信生态部') and f.channel_name_2 <> 'APP' then '集团私域'
when f.put_plan_name like '%星耀%' or f.put_plan_name like '%物理展博%' or  f.put_plan_name like '%物理谢丽荣%' or f.put_plan_name like '%牟恩伯%' or  f.put_plan_name like '%王赞%' or f.put_plan_name like '%张磊老师高中数学%' or f.put_plan_name like '%雯姐高中物理大讲堂%' then '百度星耀'
when f.source_manager_name = '刘福云' and (f.sku_id_name like '%瑞春%' or f.sku_id_name like '%春春%') then '陈瑞春'
when f.third_department_name = '直播部' and f.sku_id_name like '%周帅%' and f.channel_name_2 in ('百度','B站')  then '周帅'
when f.third_department_name = '直播部' and f.sku_id_name like '%孟亚飞%' and f.rule_name like '%99%' then '孟亚飞99-1组'
when f.third_department_name = '直播部' and f.sku_id_name like '%朱汉祺%' then '朱博士99'
when f.flow_pool_name like '%0转低转正%' or f.channel_name_2='产研测试' then '进校私域合作'
when f.flow_pool_name like '%天津智慧双子%' then '创新社群'
when f.third_department_name like '%城市定制%' then '点睛卷' 
when f.period_name like '%多学科拓展%' and f.third_department_name like '%私域运营%' then '市场私域入群'
when f.put_plan_name like '%赠课失败%' and f.third_department_name = '线上商务部' then 'KOC赠课失败'
when f.flow_pool_name like '%自然流%' and f.source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07','曲默晗') and f.sku_id_name like '%周帅%' then 'KOC-周帅' 
when f.flow_pool_name like '%自然流%' and f.source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07','曲默晗') and f.sku_id_name like '%肖晗%' then 'KOC-肖晗' 
when f.flow_pool_name like '%自然流%' and f.source_manager_name in ('孙晗01','方俊结01','刘亦鹏02','何木玲','杨梓月','张可意03','任颖迪','曹蕊07','曲默晗') and f.sku_id_name like '%朱汉祺%'  and f.flow_original_order_activity_price like '%1100%' then 'KOC-5元朱汉祺'
when f.flow_pool_name like '%自然流%' and f.source_manager_name in ('赵语诗','崔文轩','孙培尧') then '自孵化KOC-5元纯课'
when f.flow_pool_name like '%自然流%' and (f.sku_id_name like '%朱博士%' or f.sku_id_name like '%朱汉祺%') and f.rule_name like '%9%' and f.rule_name not like '%29%' and f.third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '朱博士99'
when f.flow_pool_name like '%自然流%' and f.sku_id_name like '%朱博士%' and f.third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '朱博士99'
when f.flow_pool_name like '%自然流%' and f.sku_id_name like '%亚飞%' and f.rule_name like '%99%' and f.third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '孟亚飞99-1组'  
when f.flow_pool_name like '%自然流%' and f.sku_id_name like '%亚飞%' and f.third_department_name  in ('直播部','新媒体内容运营部','市场一组')  then '孟亚飞9元'  
when f.flow_pool_name like '%自然流%' and f.sku_id_name like '%曹忆%' then '曹忆'  
when f.flow_pool_name like '%自然流%' and f.rule_name like '%朱博士%' and f.third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '朱博士99'
when f.flow_pool_name like '%自然流%' and f.source_manager_name like '%邵万昕%' and f.third_department_name  in ('直播部','新媒体内容运营部','市场一组') then '朱博士99'
when f.flow_pool_name like '%自然流%' and f.rule_name like '%亚飞%' and f.rule_name like '%99%' then '孟亚飞99-1组'  
when f.flow_pool_name like '%自然流%' and f.rule_name like '%亚飞%'  then '孟亚飞9元'  
when f.flow_pool_name like '%自然流%' and f.rule_name like '%郭艺%'  then '郭艺'
when f.flow_pool_name like '%自然流%' and f.rule_name like '%汤雪%'  then '汤老师'  
when f.flow_pool_name like '%自然流%' and f.rule_name like '%曹忆%' then '曹忆'    
when f.flow_pool_name like '%途途教室%' or f.first_department_name like 'TUTU' then '途途APP'
when f.source_manager_name in ('宋莹莹','辛世如') and f.channel_name_2 in ('视频号') then '信息流-虚拟号挂车'
when f.rule_name like '%训练营%' and f.rule_name like '%市场私域%' then '市场私域入群'
when f.channel_name_1= '信息流' and (f.put_plan_name like '%抖音私信%' or f.put_plan_name like '%初三0元%' or f.put_plan_name like '%高中0元%') then '信息流-抖音私信'
when f.rule_name like '%途途私域%' or (f.rule_name like '%私域%' and f.first_department_name = 'TT') then '途途私域'
when f.get_customer_way_name in ('进校直推','线下渠道商') then '河南进校'
else '其他未知流量' end as channel_map_1,
        case
            when f.rule_name like '%高一%' then '高一'
            when f.rule_name like '%高二%' then '高二'
            when f.rule_name like '%高三%' then '高三'
            when f.rule_name like '%初二%' then '初二'
            when f.rule_name like '%初三%' then '初三'
            else '未知'
        end as grade_1
    from bdg_ba.dm_crm_lead_cost_gmv_communication_learn_full_link_df f
    where f.dt = format_datetime(now() - interval '2' hour, 'YYYYMMdd')
      and f.hour = format_datetime(now() - interval '3' hour, 'HH')
      and f.section_assign_employee_first_level_department_name = 'H业务线'
      and f.section_assign_employee_second_level_department_name = '市场部'
      and f.period_mapping_first_level_department_name = 'H业务线'
      and f.valid_lead_count = 1
      and concat(
            date_format(
                date_trunc(
                    'week',
                    date_parse(replace(concat(f.group_period_year, f.group_period_term), '期', ''), '%Y%m%d') - interval '1' day
                ) + interval '4' day,
                '%Y%m%d'
            ),
            '期'
          ) > '20260424期'
),
leds as (
    select
        qici,
        channel_map_1,
        virtual_leader_email_name,
        grade_1,
        sum(valid_lead_count) as v_lead_c
    from data
    group by
        qici,
        channel_map_1,
        virtual_leader_email_name,
        grade_1
)
select
    coalesce(leds.qici, geren.qici) as qici,
    coalesce(leds.channel_map_1, geren.channel_1) as channel_1,
    coalesce(leds.virtual_leader_email_name, geren.jingli) as jingli,
    coalesce(leds.grade_1, geren.grade_1, '未知') as grade,
    coalesce(leds.v_lead_c, 0) as v_lead_c,
    sum(nvl(gmv_1, 0)) + sum(nvl(gmv_7, 0)) + sum(nvl(gmv_6, 0)) + sum(nvl(gmv_5, 0)) + sum(nvl(gmv_4, 0)) + sum(nvl(gmv_3, 0)) + sum(nvl(gmv_2, 0)) as gmv_1_z,
    sum(nvl(gmv_2, 0)) as gmv_2_z,
    sum(nvl(gmv_3, 0)) + sum(nvl(gmv_2, 0)) as gmv_3_z,
    sum(nvl(gmv_4, 0)) + sum(nvl(gmv_3, 0)) + sum(nvl(gmv_2, 0)) as gmv_4_z,
    sum(nvl(gmv_5, 0)) + sum(nvl(gmv_4, 0)) + sum(nvl(gmv_3, 0)) + sum(nvl(gmv_2, 0)) as gmv_5_z,
    sum(nvl(gmv_6, 0)) + sum(nvl(gmv_5, 0)) + sum(nvl(gmv_4, 0)) + sum(nvl(gmv_3, 0)) + sum(nvl(gmv_2, 0)) as gmv_6_z,
    sum(nvl(gmv_7, 0)) + sum(nvl(gmv_6, 0)) + sum(nvl(gmv_5, 0)) + sum(nvl(gmv_4, 0)) + sum(nvl(gmv_3, 0)) + sum(nvl(gmv_2, 0)) as gmv_7_z,
    sum(nvl(gmv_t, 0)) as gmv_t,
    sum(gmv_1) as gmv_1,
    sum(gmv_2) as gmv_2,
    sum(gmv_3) as gmv_3,
    sum(gmv_4) as gmv_4,
    sum(gmv_5) as gmv_5,
    sum(gmv_6) as gmv_6,
    sum(gmv_7) as gmv_7
from leds
full outer join geren
  on leds.qici = geren.qici
 and leds.channel_map_1 = geren.channel_1
 and leds.virtual_leader_email_name = geren.jingli
 and leds.grade_1 = geren.grade_1
group by
    coalesce(leds.qici, geren.qici),
    coalesce(leds.channel_map_1, geren.channel_1),
    coalesce(leds.virtual_leader_email_name, geren.jingli),
    coalesce(leds.grade_1, geren.grade_1, '未知'),
    coalesce(leds.v_lead_c, 0)
